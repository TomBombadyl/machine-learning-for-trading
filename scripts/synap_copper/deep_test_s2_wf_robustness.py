#!/usr/bin/env python3
"""Deep purged WF robustness — S2 shortlist vs MOM_ONLY (seeds 42-46).

KaggleMLEngine / Synap copper FinPredict.
promote=false ALWAYS. Fail closed. HG proxy labels.

Paste this whole file as one Kaggle cell. Do not set env vars.
Do not raise n_estimators.

v0 (2026-09-20) is KILL (weekly-in-position cost).
v1 (2026-09-20) is CONTINUE on shortlist_log_h5 only (promote=false).
This file re-stamps that CONTINUE across seeds 42-46. Same turnover
cost, same drop-zero labels, same gate. Extra seeds are primary-only
(no SHFE/COT ablation redo).

Kaggle: paste this file as one cell, then run the cell.
Local: ``python scripts/synap_copper/deep_test_s2_wf_robustness.py``.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

try:
    import torch
except ImportError:  # pragma: no cover
    torch = None

# ---------------------------------------------------------------------------
# Paths / constants
# ---------------------------------------------------------------------------
VERSION = "deep_test_s2_wf_robustness"
V0_KILL_SHA12 = "35f1fce22bca"
PROMOTE = False

ROOT = Path(os.environ.get("SYNAP_CU_ROOT", "/workspace/synap_copper/data/synap/copper"))
PANEL_CANDIDATES = [
    Path(os.environ["DEEP_TEST_PANEL"]) if os.environ.get("DEEP_TEST_PANEL") else None,
    Path(
        "/kaggle/input/datasets/synapgarden/synap-finpredict-panels-v0/"
        "deep_test_friday_panel_v0.parquet"
    ),
    Path("/kaggle/input/synap-finpredict-panels-v0/deep_test_friday_panel_v0.parquet"),
    ROOT / "deep_test_friday_panel_v0.parquet",
]
OUT_DIR = Path(
    os.environ.get("DEEP_TEST_OUT", str(ROOT / "docs" / "kaggle_deep_test_s2_wf_robustness"))
)
if Path("/kaggle/working").exists() and not os.environ.get("DEEP_TEST_OUT"):
    OUT_DIR = Path("/kaggle/working")

CORE_MOM = ["mom_5d", "mom_21d", "mom_63d"]
SHORTLIST_EXTRA = ["cper_mom_21d", "fcx_mom_63d"]
SHFE_ABLATION = ["shfe_warrant_chg_21d", "shfe_warrant_pct_chg_21d"]
COT_ABLATION = [
    "cot_managed_money_net",
    "cot_managed_money_pct_oi",
    "cot_managed_money_net_chg_1w",
    "cot_managed_money_z_52w",
]

RT_BPS = 4.0
SLIP_BPS = 2.0
COST_RT = (RT_BPS + 2 * SLIP_BPS) / 1e4  # 8 bps round-trip
COST_ONE_WAY = COST_RT / 2.0  # 4 bps per |Δpos| unit
THR_LONG = 0.60
THR_SHORT = 0.40
TRAIN_MIN = 104
TEST_SIZE = 26
STEP = 26
DD_SLACK = 0.05
HORIZONS = [5, 21, 63]
XGB_TREES = 160
RF_TREES = 160
LOG_MAX_ITER = 800

MODE = "robustness"
PRIMARY_SEED = 42
ROBUSTNESS_SEEDS = (42, 43, 44, 45, 46)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_panel() -> Path:
    for candidate in PANEL_CANDIDATES:
        if candidate is not None and candidate.exists():
            return candidate
    kaggle_in = Path("/kaggle/input")
    if kaggle_in.exists():
        hits = sorted(kaggle_in.rglob("deep_test_friday_panel_v0.parquet"))
        if hits:
            return hits[0]
    raise FileNotFoundError("deep_test_friday_panel_v0.parquet not found")


def spearman_ic(x: np.ndarray, y: np.ndarray) -> float:
    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]
    if len(x) < 10:
        return float("nan")
    rx = x.argsort().argsort().astype(float)
    ry = y.argsort().argsort().astype(float)
    rx = (rx - rx.mean()) / (rx.std() + 1e-12)
    ry = (ry - ry.mean()) / (ry.std() + 1e-12)
    return float(np.mean(rx * ry))


def purged_folds(n: int, train_min: int, test_size: int, step: int, embargo: int):
    folds = []
    start = train_min
    while start + test_size <= n:
        test_start, test_end = start, start + test_size
        train_end = test_start - embargo
        if train_end < max(40, train_min // 2):
            start += step
            continue
        folds.append((np.arange(0, train_end), np.arange(test_start, test_end)))
        start += step
    return folds


def positions_from_proba(proba, thr_long=THR_LONG, thr_short=THR_SHORT):
    pos = np.zeros(len(proba), dtype=float)
    pos[proba >= thr_long] = 1.0
    pos[proba <= thr_short] = -1.0
    return pos


def turnover_nets(pos: np.ndarray, rets: np.ndarray) -> np.ndarray:
    """Cost on |Δposition|. Fold starts flat (prev=0)."""
    prev = np.concatenate([np.zeros(1, dtype=float), pos[:-1]])
    traded = np.abs(pos - prev)
    return pos * rets - COST_ONE_WAY * traded


def max_dd(nets: np.ndarray) -> float:
    if len(nets) == 0:
        return 0.0
    equity = np.cumsum(nets)
    peak = np.maximum.accumulate(equity)
    return float(np.max(peak - equity))


def summarize(nets, pos, dates):
    return {
        "n": int(len(nets)),
        "date_min": dates[0] if dates else None,
        "date_max": dates[-1] if dates else None,
        "sum_net": round(float(np.sum(nets)), 6),
        "mean_net": round(float(np.mean(nets)), 6) if len(nets) else 0.0,
        "hit_net": round(float(np.mean(nets > 0)), 4) if len(nets) else 0.0,
        "ann_net_approx": round(float(np.mean(nets) * 52), 6) if len(nets) else 0.0,
        "max_dd": round(max_dd(nets), 6),
        "frac_long": round(float(np.mean(pos > 0)), 4) if len(pos) else 0.0,
        "frac_short": round(float(np.mean(pos < 0)), 4) if len(pos) else 0.0,
        "frac_flat": round(float(np.mean(np.abs(pos) < 1e-12)), 4) if len(pos) else 1.0,
        "always_flat": bool(len(pos) > 0 and np.all(np.abs(pos) < 1e-12)),
    }


def detect_gpu() -> dict:
    info: dict[str, Any] = {
        "nvidia_smi": False,
        "torch_cuda": False,
        "xgb_gpu": False,
        "backend": "cpu",
    }
    try:
        result = subprocess.run(
            ["nvidia-smi"], capture_output=True, text=True, timeout=10, check=False
        )
        info["nvidia_smi"] = result.returncode == 0
        if result.returncode == 0:
            info["nvidia_smi_head"] = "\n".join(result.stdout.splitlines()[:8])
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as exc:
        info["nvidia_smi_err"] = str(exc)
    if torch is not None:
        info["torch_cuda"] = bool(torch.cuda.is_available())
        info["torch_version"] = getattr(torch, "__version__", None)
    else:
        info["torch_err"] = "torch_not_imported"
    # Copper v0 default is cpu. Only claim GPU if the driver is actually there.
    info["xgb_gpu"] = bool(info["nvidia_smi"] and info["torch_cuda"])
    info["backend"] = "gpu" if info["xgb_gpu"] else "cpu"
    return info


def make_xgb(seed: int, use_gpu: bool, scale_pos_weight: float):
    params = dict(
        n_estimators=XGB_TREES,
        max_depth=3,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_lambda=1.0,
        min_child_weight=5,
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=seed,
        scale_pos_weight=scale_pos_weight,
        verbosity=0,
    )
    if use_gpu:
        return XGBClassifier(**params, device="cuda", tree_method="hist"), "cuda_hist"
    return XGBClassifier(**params, tree_method="hist", n_jobs=2), "cpu_hist"


def fit_predict(kind: str, x_train, y_train, x_test, use_gpu: bool, seed: int = 42):
    if len(np.unique(y_train)) < 2:
        return None, None, None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if kind == "logistic":
            scaler = StandardScaler()
            clf = LogisticRegression(
                max_iter=LOG_MAX_ITER, class_weight="balanced", random_state=seed
            )
            clf.fit(scaler.fit_transform(x_train), y_train)
            proba = clf.predict_proba(scaler.transform(x_test))[:, 1]
            return proba, "logistic_cpu", clf
        if kind == "rf":
            clf = RandomForestClassifier(
                n_estimators=RF_TREES,
                max_depth=4,
                min_samples_leaf=8,
                class_weight="balanced_subsample",
                random_state=seed,
                n_jobs=-1,
            )
            clf.fit(x_train, y_train)
            return clf.predict_proba(x_test)[:, 1], "rf_cpu", clf
        if kind == "xgb":
            pos = float(np.sum(y_train == 1))
            neg = float(np.sum(y_train == 0))
            scale_pos_weight = neg / max(pos, 1.0)
            if use_gpu:
                try:
                    clf, backend = make_xgb(seed, True, scale_pos_weight)
                    clf.fit(x_train, y_train)
                    return clf.predict_proba(x_test)[:, 1], backend, clf
                except (ValueError, RuntimeError, TypeError) as exc:
                    warnings.warn(f"xgb gpu fit failed ({exc}); cpu_hist fallback")
            clf, backend = make_xgb(seed, False, scale_pos_weight)
            clf.fit(x_train, y_train)
            return clf.predict_proba(x_test)[:, 1], backend, clf
    raise ValueError(f"unknown kind: {kind}")


def run_model_horizon(
    df: pd.DataFrame,
    feats: list[str],
    horizon: int,
    kind: str,
    use_gpu: bool,
    name: str,
    seed: int,
):
    ret_col = f"fwd_ret_{horizon}d"
    need = list(dict.fromkeys(feats + [ret_col, "date"]))
    missing = [col for col in need if col not in df.columns]
    if missing:
        return None
    sub = df[need].dropna().copy()
    sub = sub.loc[sub[ret_col] != 0].copy()
    if len(sub) < TRAIN_MIN + TEST_SIZE:
        return None

    features = sub[feats].to_numpy(dtype=float)
    features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)
    rets = sub[ret_col].to_numpy(dtype=float)
    labels = (rets > 0).astype(int)
    dates = [str(day)[:10] for day in sub["date"].tolist()]

    embargo = max(2, (horizon + 4) // 5)
    folds = purged_folds(len(labels), TRAIN_MIN, TEST_SIZE, STEP, embargo)
    if len(folds) < 3:
        folds = purged_folds(len(labels), max(52, TRAIN_MIN // 2), TEST_SIZE, STEP, embargo)
    if not folds:
        return None

    all_nets, all_pos, all_dates = [], [], []
    all_proba, all_y = [], []
    fold_stats = []
    backends = []

    for fold_i, (train_idx, test_idx) in enumerate(folds):
        proba, backend, _ = fit_predict(
            kind,
            features[train_idx],
            labels[train_idx],
            features[test_idx],
            use_gpu=use_gpu,
            seed=seed + fold_i,
        )
        if proba is None:
            continue
        backends.append(backend)
        pos = positions_from_proba(proba)
        nets = turnover_nets(pos, rets[test_idx])
        test_dates = [dates[i] for i in test_idx]
        stats = summarize(nets, pos, test_dates)
        stats.update(
            {
                "fold": fold_i,
                "n_train": int(len(train_idx)),
                "n_test": int(len(test_idx)),
                "sign_positive": bool(stats["sum_net"] > 0),
                "backend": backend,
            }
        )
        try:
            stats["auc"] = round(float(roc_auc_score(labels[test_idx], proba)), 4)
        except ValueError:
            stats["auc"] = None
        stats["ic"] = round(spearman_ic(proba, labels[test_idx].astype(float)), 4)
        fold_stats.append(stats)
        all_nets.append(nets)
        all_pos.append(pos)
        all_dates.extend(test_dates)
        all_proba.append(proba)
        all_y.append(labels[test_idx])

    if not all_nets:
        return None

    nets_c = np.concatenate(all_nets)
    pos_c = np.concatenate(all_pos)
    overall = summarize(nets_c, pos_c, all_dates)
    proba_c = np.concatenate(all_proba)
    y_c = np.concatenate(all_y)
    try:
        auc = float(roc_auc_score(y_c, proba_c))
    except ValueError:
        auc = float("nan")
    ic = spearman_ic(proba_c, y_c.astype(float))

    n_folds = len(fold_stats)
    eval_folds = fold_stats[-5:] if n_folds >= 5 else fold_stats
    n_pos = sum(1 for fold in eval_folds if fold["sign_positive"])
    if len(eval_folds) >= 5:
        sign_stable = n_pos >= 3
    else:
        sign_stable = n_pos >= 3 and n_pos / max(len(eval_folds), 1) >= 0.6

    overall.update(
        {
            "name": name,
            "kind": kind,
            "feats": feats,
            "horizon": horizon,
            "embargo_fridays": embargo,
            "n_folds": n_folds,
            "n_sign_pos_last5": n_pos,
            "n_eval_folds": len(eval_folds),
            "sign_stable_3of5": bool(sign_stable),
            "frac_folds_pos": round(
                float(np.mean([fold["sign_positive"] for fold in fold_stats])), 4
            ),
            "auc_oos": round(auc, 4) if np.isfinite(auc) else None,
            "ic_proba_dir": round(ic, 4) if np.isfinite(ic) else None,
            "costs_bps": {
                "rt": RT_BPS,
                "slip_per_side": SLIP_BPS,
                "cost_frac_rt": COST_RT,
                "cost_one_way": COST_ONE_WAY,
                "cost_model": "turnover",
            },
            "thr_long": THR_LONG,
            "thr_short": THR_SHORT,
            "panel_n": int(len(sub)),
            "panel_date_min": dates[0],
            "panel_date_max": dates[-1],
            "xgb_backends": sorted(set(backends)),
            "seed": seed,
            "promote": False,
        }
    )
    return {"overall": overall, "folds": fold_stats}


def decide_vs_baseline(challenger: dict, baseline: dict) -> tuple[str, list[str]]:
    reasons = []
    if challenger.get("always_flat"):
        reasons.append("always_flat_capability_floor")
    if challenger["sum_net"] <= baseline["sum_net"]:
        reasons.append(
            f"sum_net={challenger['sum_net']:.4f}<=baseline={baseline['sum_net']:.4f}"
        )
    dd_slack = challenger["max_dd"] - baseline["max_dd"]
    if dd_slack > DD_SLACK + 1e-12:
        reasons.append(f"max_dd worse by {dd_slack:.2%} >5pp vs baseline")
    if not challenger.get("sign_stable_3of5"):
        reasons.append(
            "sign_stable fail: "
            f"{challenger.get('n_sign_pos_last5')}/{challenger.get('n_eval_folds')} pos folds"
        )
    verdict = "CONTINUE" if not reasons else "KILL"
    return verdict, reasons


def feature_sets(df: pd.DataFrame) -> dict:
    shortlist = [col for col in dict.fromkeys(CORE_MOM + SHORTLIST_EXTRA) if col in df.columns]
    mom_only = [col for col in CORE_MOM if col in df.columns]
    shfe = [col for col in SHFE_ABLATION if col in df.columns]
    cot = [col for col in COT_ABLATION if col in df.columns]
    return {
        "MOM_ONLY": mom_only,
        "S2_SHORTLIST": shortlist,
        "S2_SHORTLIST_PLUS_SHFE": list(dict.fromkeys(shortlist + shfe)),
        "S2_SHORTLIST_PLUS_COT": list(dict.fromkeys(shortlist + cot)),
    }


def run_suite(df, fsets, use_gpu, seed: int, include_ablation: bool):
    primary_specs = [
        ("MOM_ONLY", "logistic", "mom_only_log"),
        ("S2_SHORTLIST", "logistic", "shortlist_log"),
        ("S2_SHORTLIST", "rf", "shortlist_rf"),
        ("S2_SHORTLIST", "xgb", "shortlist_xgb"),
    ]
    ablation_specs = [
        ("S2_SHORTLIST_PLUS_SHFE", "logistic", "shortlist_shfe_log"),
        ("S2_SHORTLIST_PLUS_SHFE", "rf", "shortlist_shfe_rf"),
        ("S2_SHORTLIST_PLUS_SHFE", "xgb", "shortlist_shfe_xgb"),
        ("S2_SHORTLIST_PLUS_COT", "logistic", "shortlist_cot_log"),
        ("S2_SHORTLIST_PLUS_COT", "rf", "shortlist_cot_rf"),
        ("S2_SHORTLIST_PLUS_COT", "xgb", "shortlist_cot_xgb"),
    ]

    primary_results = []
    fold_tables = []
    for horizon in HORIZONS:
        for fset_name, kind, run_name in primary_specs:
            feats = fsets[fset_name]
            print(f"  PRIMARY h={horizon} {run_name} seed={seed} feats={feats}", flush=True)
            result = run_model_horizon(
                df, feats, horizon, kind, use_gpu, f"{run_name}_h{horizon}", seed
            )
            if result is None:
                primary_results.append({"name": f"{run_name}_h{horizon}", "error": "insufficient"})
                continue
            overall = result["overall"]
            overall["feature_set"] = fset_name
            overall["suite"] = "primary"
            primary_results.append(overall)
            fold_tables.append(
                {
                    "name": overall["name"],
                    "suite": "primary",
                    "seed": seed,
                    "folds": result["folds"],
                    "overall": overall,
                }
            )

    ablation_results = []
    if include_ablation:
        for horizon in HORIZONS:
            for fset_name, kind, run_name in ablation_specs:
                feats = fsets[fset_name]
                base = fsets["S2_SHORTLIST"]
                if feats == base:
                    ablation_results.append(
                        {
                            "name": f"{run_name}_h{horizon}",
                            "skipped": True,
                            "reason": "no_extra_feats",
                        }
                    )
                    continue
                print(
                    f"  ABLATION h={horizon} {run_name} seed={seed} feats={feats}",
                    flush=True,
                )
                result = run_model_horizon(
                    df, feats, horizon, kind, use_gpu, f"{run_name}_h{horizon}", seed
                )
                if result is None:
                    ablation_results.append(
                        {"name": f"{run_name}_h{horizon}", "error": "insufficient"}
                    )
                    continue
                overall = result["overall"]
                overall["feature_set"] = fset_name
                overall["suite"] = "ablation"
                ablation_results.append(overall)
                fold_tables.append(
                    {
                        "name": overall["name"],
                        "suite": "ablation",
                        "seed": seed,
                        "folds": result["folds"],
                        "overall": overall,
                    }
                )
    return primary_results, ablation_results, fold_tables


def decisions_from_primary(primary_results):
    decisions = []
    for horizon in HORIZONS:
        base = next(
            (
                row
                for row in primary_results
                if isinstance(row, dict)
                and row.get("name") == f"mom_only_log_h{horizon}"
                and "sum_net" in row
            ),
            None,
        )
        if base is None:
            decisions.append({"horizon": horizon, "verdict": "KILL", "reasons": ["no_baseline"]})
            continue
        challengers = [
            row
            for row in primary_results
            if isinstance(row, dict)
            and row.get("horizon") == horizon
            and row.get("feature_set") == "S2_SHORTLIST"
            and "sum_net" in row
        ]
        for challenger in challengers:
            verdict, reasons = decide_vs_baseline(challenger, base)
            decisions.append(
                {
                    "horizon": horizon,
                    "name": challenger["name"],
                    "verdict": verdict,
                    "reasons": reasons,
                    "sum_net": challenger["sum_net"],
                    "max_dd": challenger["max_dd"],
                    "baseline_sum_net": base["sum_net"],
                    "baseline_max_dd": base["max_dd"],
                    "sign_stable_3of5": challenger.get("sign_stable_3of5"),
                    "auc_oos": challenger.get("auc_oos"),
                    "ic_proba_dir": challenger.get("ic_proba_dir"),
                }
            )
    return decisions


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel_path = resolve_panel()
    panel_sha = sha256_file(panel_path)
    mtime = datetime.fromtimestamp(panel_path.stat().st_mtime, tz=timezone.utc).isoformat()
    df = pd.read_parquet(panel_path)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    shelf = [col for col in df.columns if col.startswith("cnt_")]
    gpu_info = detect_gpu()
    use_gpu = bool(gpu_info.get("xgb_gpu"))
    fsets = feature_sets(df)
    sha_note = (
        "matches_v0"
        if panel_sha.startswith(V0_KILL_SHA12)
        else f"sha_changed_from_v0_{V0_KILL_SHA12}"
    )

    print(
        f"[{VERSION}] panel={panel_path} shape={df.shape} sha={panel_sha[:12]} "
        f"sha_note={sha_note} mode={MODE} gpu={use_gpu} backend={gpu_info['backend']}",
        flush=True,
    )
    print(f"[{VERSION}] feature_sets={[(key, val) for key, val in fsets.items()]}", flush=True)
    print(
        f"[{VERSION}] cost_model=turnover one_way={COST_ONE_WAY} "
        f"v0_was=in_position_weekly cost={COST_RT}",
        flush=True,
    )

    primary_results, ablation_results, fold_tables = run_suite(
        df, fsets, use_gpu, PRIMARY_SEED, include_ablation=True
    )
    decisions = decisions_from_primary(primary_results)
    passers = [row for row in decisions if row.get("verdict") == "CONTINUE"]
    if passers:
        headline = max(passers, key=lambda row: row["sum_net"])
        verdict = "CONTINUE"
    else:
        scored = [row for row in decisions if "sum_net" in row]
        headline = (
            max(scored, key=lambda row: row["sum_net"])
            if scored
            else {"name": None, "sum_net": None}
        )
        verdict = "KILL"

    robustness = []
    if MODE == "robustness":
        for seed in ROBUSTNESS_SEEDS:
            if seed == PRIMARY_SEED:
                robustness.append(
                    {
                        "seed": seed,
                        "primary_results": primary_results,
                        "decisions": decisions,
                        "verdict": verdict,
                        "n_passers": len(passers),
                    }
                )
                continue
            print(f"[{VERSION}] robustness seed={seed}", flush=True)
            seed_primary, _, _ = run_suite(
                df, fsets, use_gpu, seed, include_ablation=False
            )
            seed_decisions = decisions_from_primary(seed_primary)
            seed_passers = [row for row in seed_decisions if row.get("verdict") == "CONTINUE"]
            robustness.append(
                {
                    "seed": seed,
                    "verdict": "CONTINUE" if seed_passers else "KILL",
                    "n_passers": len(seed_passers),
                    "decisions": seed_decisions,
                }
            )

    n_seeds_continue = sum(1 for row in robustness if row.get("verdict") == "CONTINUE")
    family_verdict = "CONTINUE" if n_seeds_continue >= 3 else "KILL"

    ablation_notes = []
    for horizon in HORIZONS:
        base = next(
            (
                row
                for row in primary_results
                if isinstance(row, dict)
                and row.get("name") == f"mom_only_log_h{horizon}"
                and "sum_net" in row
            ),
            None,
        )
        short = next(
            (
                row
                for row in primary_results
                if isinstance(row, dict)
                and row.get("name") == f"shortlist_log_h{horizon}"
                and "sum_net" in row
            ),
            None,
        )
        for prefix in ("shortlist_shfe", "shortlist_cot"):
            for kind in ("log", "rf", "xgb"):
                name = f"{prefix}_{kind}_h{horizon}"
                row = next(
                    (
                        item
                        for item in ablation_results
                        if isinstance(item, dict) and item.get("name") == name and "sum_net" in item
                    ),
                    None,
                )
                if row and base and short:
                    ablation_notes.append(
                        {
                            "name": name,
                            "sum_net": row["sum_net"],
                            "max_dd": row["max_dd"],
                            "vs_mom": round(row["sum_net"] - base["sum_net"], 6),
                            "vs_shortlist_log": round(row["sum_net"] - short["sum_net"], 6),
                            "sign_stable_3of5": row.get("sign_stable_3of5"),
                        }
                    )

    built = datetime.now(timezone.utc).isoformat()
    metrics = {
        "promote": False,
        "NOT_A_PROMOTE": True,
        "version": VERSION,
        "mode": MODE,
        "v0_verdict": "KILL",
        "v1_seed42_verdict": "CONTINUE",
        "v1_passer": "shortlist_log_h5",
        "robustness_seeds": list(ROBUSTNESS_SEEDS),
        "v1_changes": [
            "same turnover cost and drop-zero labels as v1",
            "primary suite on seeds 42-46; ablation only on seed 42",
            "do not raise n_estimators",
        ],
        "verdict": family_verdict,
        "seed42_verdict": verdict,
        "n_seeds_continue": n_seeds_continue,
        "n_seeds": len(ROBUSTNESS_SEEDS),
        "built_at_utc": built,
        "panel": {
            "path": str(panel_path),
            "sha256": panel_sha,
            "sha_note": sha_note,
            "mtime_utc": mtime,
            "shape": list(df.shape),
            "n_cols": int(df.shape[1]),
            "date_min": str(df["date"].min())[:10],
            "date_max": str(df["date"].max())[:10],
            "shelf_cnt_cols_excluded": shelf,
            "cot_cols_present": [col for col in df.columns if col.startswith("cot_")],
        },
        "gpu": gpu_info,
        "costs": {
            "rt_bps": RT_BPS,
            "slip_bps_per_side": SLIP_BPS,
            "cost_frac_rt": COST_RT,
            "cost_one_way": COST_ONE_WAY,
            "cost_model": "turnover",
        },
        "thresholds": {"long": THR_LONG, "short": THR_SHORT},
        "folds": {"train_min": TRAIN_MIN, "test_size": TEST_SIZE, "step": STEP},
        "feature_sets": fsets,
        "primary_results": primary_results,
        "ablation_results": ablation_results,
        "ablation_notes": ablation_notes,
        "decisions": decisions,
        "headline": headline,
        "robustness": robustness,
        "success_rule": (
            "CONTINUE if challenger beats MOM_ONLY on costed sum_net AND "
            "maxDD not > baseline+5pp AND sign-stable >=3/5 folds on >=1 horizon"
        ),
    }

    (OUT_DIR / "deep_test_s2_robustness_metrics.json").write_text(
        json.dumps(metrics, indent=2, default=str)
    )
    (OUT_DIR / "deep_test_s2_robustness_fold_table.json").write_text(
        json.dumps(fold_tables, indent=2, default=str)
    )

    rows = []
    for table in fold_tables:
        for fold in table["folds"]:
            rows.append(
                {
                    "run": table["name"],
                    "suite": table["suite"],
                    "seed": table.get("seed"),
                    **{key: fold[key] for key in fold if key != "dates"},
                }
            )
    pd.DataFrame(rows).to_csv(OUT_DIR / "deep_test_s2_robustness_fold_table.csv", index=False)

    sig_bits = []
    for horizon in HORIZONS:
        for name in (
            f"mom_only_log_h{horizon}",
            f"shortlist_log_h{horizon}",
            f"shortlist_rf_h{horizon}",
            f"shortlist_xgb_h{horizon}",
        ):
            row = next(
                (item for item in primary_results if isinstance(item, dict) and item.get("name") == name),
                None,
            )
            if row and "sum_net" in row:
                sig_bits.append(
                    f"{name}: sum={row['sum_net']:+.4f} dd={row['max_dd']:.3f} "
                    f"auc={row.get('auc_oos')} ic={row.get('ic_proba_dir')} "
                    f"sign={row.get('n_sign_pos_last5')}/{row.get('n_eval_folds')}"
                )

    best_name = headline.get("name") if isinstance(headline, dict) else None
    best_sum = headline.get("sum_net") if isinstance(headline, dict) else None
    best_dd = headline.get("max_dd") if isinstance(headline, dict) else None
    base5 = next(
        (
            row
            for row in primary_results
            if isinstance(row, dict) and row.get("name") == "mom_only_log_h5" and "sum_net" in row
        ),
        None,
    )

    receipt_lines = [
        f"Verdict: {family_verdict} (promote=false) version={VERSION} mode={MODE} "
        f"seeds_continue={n_seeds_continue}/{len(ROBUSTNESS_SEEDS)} seed42={verdict}",
        "Hyp: CU/NCU Friday · HG proxy fwd_ret · S2 shortlist vs MOM_ONLY · purged WF · v1 turnover+nonzero labels",
        "Signal: "
        + " · ".join(
            [
                f"h{horizon} shortlist_xgb auc="
                + str(
                    next(
                        (
                            row.get("auc_oos")
                            for row in primary_results
                            if isinstance(row, dict) and row.get("name") == f"shortlist_xgb_h{horizon}"
                        ),
                        None,
                    )
                )
                for horizon in HORIZONS
            ]
        ),
        f"Strategy: best={best_name} sum_net={best_sum} maxDD={best_dd} vs mom_h5 sum="
        f"{None if not base5 else base5['sum_net']} · cost=turnover {COST_ONE_WAY} one-way · GPU={gpu_info['backend']}",
        "Boundary: purged WF · embargo≥horizon Fridays · semantics cnt_* SHELF · cot/SHFE ablation only · sealed promote=false",
        f"Path: {OUT_DIR / 'deep_test_s2_robustness_metrics.json'}",
    ]
    receipt = "\n".join(receipt_lines) + "\n"
    (OUT_DIR / "ML4T_RECEIPT_CARD.md").write_text(
        f"# ML4T Receipt Card — {VERSION}\n\n"
        f"**promote: false** · built {built}\n\n"
        "```\n" + receipt + "```\n\n"
        f"- Panel sha256: `{panel_sha}` ({sha_note})\n"
        f"- Panel mtime UTC: `{mtime}`\n"
        f"- Shape: {list(df.shape)}\n"
        f"- GPU: `{json.dumps(gpu_info)}`\n"
        f"- Primary feature sets: `{json.dumps(fsets)}`\n"
        f"- Passers: {len(passers)} / decisions {len(decisions)}\n"
        f"- Ablation notes (n={len(ablation_notes)}): see metrics JSON\n\n"
        "## Primary scoreboard\n\n"
        + "\n".join(f"- {line}" for line in sig_bits)
        + "\n"
    )
    (OUT_DIR / "ML4T_RECEIPT_CARD.txt").write_text(receipt)

    memo = {
        "verdict": family_verdict,
        "seed42_verdict": verdict,
        "n_seeds_continue": n_seeds_continue,
        "n_seeds": len(ROBUSTNESS_SEEDS),
        "promote": False,
        "version": VERSION,
        "mode": MODE,
        "gpu": gpu_info["backend"],
        "panel_sha12": panel_sha[:12],
        "sha_note": sha_note,
        "n_cols": int(df.shape[1]),
        "passers": [row["name"] for row in passers],
        "headline": headline,
        "robustness_seeds": [
            {
                "seed": row.get("seed"),
                "verdict": row.get("verdict"),
                "n_passers": row.get("n_passers"),
            }
            for row in robustness
        ],
        "paths": {
            "metrics": str(OUT_DIR / "deep_test_s2_robustness_metrics.json"),
            "folds": str(OUT_DIR / "deep_test_s2_robustness_fold_table.csv"),
            "receipt": str(OUT_DIR / "ML4T_RECEIPT_CARD.md"),
        },
    }
    (OUT_DIR / "deep_test_s2_robustness_memo.json").write_text(
        json.dumps(memo, indent=2, default=str)
    )
    print(json.dumps(memo, indent=2, default=str), flush=True)
    print("RECEIPT:\n" + receipt, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
