#!/usr/bin/env python3
"""Fresh paste — S2 tabular MARATHON. **STAMPED CONTINUE 10/10** (2026-09-20).

promote=false ALWAYS. Do not rerun for novelty unless Engine asks for a
metrics LOO/lookback skim with a fresh card.

Closed (do not reopen):
  TinyGAT / s2gate / s2ablate / Cell 2 typed GAT

Prior stamps:
  survivors_v0 CONTINUE 5/5
  marathon_v0 CONTINUE 10/10 primary (this file) — sha 35f1fce22bca…
  elapsed_run_s=3701; floor=6; no_gat=True

Family gate = PRIMARY only (documented below). Never PROMOTE.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

VERSION = "copper_s2_tabular_marathon_v0"
PROMOTE = False
V0_SHA12 = "35f1fce22bca"
DD_SLACK = 0.05
TRAIN_MIN = 104
TEST_SIZE = 26
SEEDS = tuple(range(42, 52))  # 10
FAMILY_MIN_FRAC = 0.60
PRIMARY = {
    "horizon": 5,
    "step": 26,
    "cost_one_way": 0.0004,
    "lookback": 52,
    "corr_min": 0.25,
    "thr_long": 0.60,
    "thr_short": 0.40,
    "C": 1.0,
    "loo_drop": None,
}
LOOKBACKS = (26, 39, 52, 65, 78, 91, 104)
CORR_MINS = (0.15, 0.25, 0.35)
HORIZONS = (5, 21, 63)
STEPS = (26, 13)
COSTS = (0.0002, 0.0004, 0.0006, 0.0008, 0.0012)
THRESHOLDS = ((0.55, 0.45), (0.60, 0.40), (0.65, 0.35))
C_GRID = (0.25, 1.0, 4.0)
MOM_COLS = ["mom_5d", "mom_21d", "mom_63d"]
SHORTLIST_EXTRA = ["cper_mom_21d", "fcx_mom_63d"]
GRAPH_SURVIVORS = ["graph_pagerank", "graph_betweenness", "graph_hhi"]
COT_SURVIVORS = [
    "cot_managed_money_net",
    "cot_managed_money_pct_oi",
    "cot_managed_money_z_52w",
]
SERIES = {
    "HG": ["ret_hg", "mom_5d"],
    "CPER": ["ret_cper", "cper_mom_21d"],
    "COPX": ["ret_copx", "copx_mom_21d"],
    "FCX": ["ret_fcx", "fcx_mom_63d"],
    "COT_MM": ["cot_managed_money_net_chg_1w", "cot_managed_money_net"],
    "SHFE_WH": ["shfe_warrant_pct_chg_21d", "shfe_warrant_chg_21d"],
}
PROXY_EDGES = (("CPER", "HG"), ("COPX", "HG"), ("FCX", "HG"))
PANEL_CANDIDATES = [
    Path(
        "/kaggle/input/datasets/synapgarden/synap-finpredict-panels-v0/"
        "deep_test_friday_panel_v0.parquet"
    ),
    Path("/kaggle/input/synap-finpredict-panels-v0/deep_test_friday_panel_v0.parquet"),
]
OUT_DIR = (
    Path("/kaggle/working")
    if Path("/kaggle/working").exists()
    else Path("data/synap/copper/panels")
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_panel() -> Path:
    for candidate in PANEL_CANDIDATES:
        if candidate.is_file():
            return candidate
    kaggle_in = Path("/kaggle/input")
    if kaggle_in.exists():
        hits = sorted(kaggle_in.rglob("deep_test_friday_panel_v0.parquet"))
        if hits:
            return hits[0]
    raise FileNotFoundError(
        "deep_test_friday_panel_v0.parquet not found. "
        "Add Input synap-finpredict-panels-v0 on the existing S2 notebook."
    )


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    mask = np.isfinite(x) & np.isfinite(y)
    if int(mask.sum()) < 12:
        return float("nan")
    if np.nanstd(x[mask]) == 0 or np.nanstd(y[mask]) == 0:
        return float("nan")
    corr, _ = spearmanr(x[mask], y[mask])
    return float(corr)


def first_present(df: pd.DataFrame, names: list[str]) -> str | None:
    return next((name for name in names if name in df.columns), None)


def hhi(weights: list[float]) -> float:
    if not weights:
        return 0.0
    total = sum(weights)
    if total <= 0:
        return 0.0
    shares = [weight / total for weight in weights]
    return float(sum(share * share for share in shares))


def snapshot_features(df: pd.DataFrame, loc: int, lookback: int, corr_min: float) -> dict:
    start = max(0, loc - lookback + 1)
    window = df.iloc[start : loc + 1]
    node_cols = {}
    for node, candidates in SERIES.items():
        col = first_present(window, candidates)
        if col is None or window[col].notna().sum() < 16:
            continue
        node_cols[node] = col
    graph = nx.Graph()
    graph.add_nodes_from(node_cols)
    nodes = list(node_cols)
    for i, left in enumerate(nodes):
        for right in nodes[i + 1 :]:
            rho = spearman(window[node_cols[left]].to_numpy(), window[node_cols[right]].to_numpy())
            if np.isfinite(rho) and abs(rho) >= corr_min:
                graph.add_edge(left, right, weight=abs(rho))
    for src, dst in PROXY_EDGES:
        if src in graph and dst in graph and not graph.has_edge(src, dst):
            graph.add_edge(src, dst, weight=0.35)
    if "COT_MM" in graph and "HG" in graph and not graph.has_edge("COT_MM", "HG"):
        graph.add_edge("COT_MM", "HG", weight=0.35)
    if "SHFE_WH" in graph and "HG" in graph and not graph.has_edge("SHFE_WH", "HG"):
        graph.add_edge("SHFE_WH", "HG", weight=0.35)
    pagerank = nx.pagerank(graph, weight="weight") if graph.number_of_nodes() else {}
    between = (
        nx.betweenness_centrality(graph, weight="weight") if graph.number_of_nodes() > 2 else {}
    )
    hg_weights = [abs(data.get("weight", 0.0)) for _, _, data in graph.edges("HG", data=True)]
    return {
        "graph_pagerank": float(pagerank.get("HG", 0.0)),
        "graph_betweenness": float(between.get("HG", 0.0)),
        "graph_hhi": hhi(hg_weights),
    }


def emit_graph_features(df: pd.DataFrame, lookback: int, corr_min: float) -> pd.DataFrame:
    work = df.reset_index(drop=True)
    n = len(work)
    rows = []
    t0 = time.time()
    for loc in range(n):
        rows.append(snapshot_features(work, loc, lookback, corr_min))
        if loc == 0 or (loc + 1) % 100 == 0 or loc + 1 == n:
            print(
                f"[marathon] emit lookback={lookback} corr={corr_min} "
                f"row={loc + 1}/{n} elapsed_s={time.time() - t0:.0f}",
                flush=True,
            )
    feats = pd.DataFrame(rows)
    return pd.concat([work, feats], axis=1)


def purged_folds(n: int, embargo: int, step: int):
    folds = []
    start = TRAIN_MIN
    while start + TEST_SIZE <= n:
        test_start = start
        train_end = test_start - embargo
        if train_end >= 40:
            folds.append((np.arange(0, train_end), np.arange(test_start, test_start + TEST_SIZE)))
        start += step
    return folds


def fit_logistic(x_train, y_train, x_test, seed: int, C: float):
    if len(np.unique(y_train)) < 2:
        return np.full(len(x_test), 0.5)
    x_train = np.nan_to_num(x_train, nan=0.0, posinf=0.0, neginf=0.0)
    x_test = np.nan_to_num(x_test, nan=0.0, posinf=0.0, neginf=0.0)
    scaler = StandardScaler()
    model = LogisticRegression(
        max_iter=1200, class_weight="balanced", random_state=seed, C=C
    )
    model.fit(scaler.fit_transform(x_train), y_train)
    return model.predict_proba(scaler.transform(x_test))[:, 1]


def positions(proba: np.ndarray, thr_long: float, thr_short: float) -> np.ndarray:
    pos = np.zeros(len(proba), dtype=float)
    pos[proba >= thr_long] = 1.0
    pos[proba <= thr_short] = -1.0
    return pos


def turnover_nets(pos: np.ndarray, rets: np.ndarray, cost_one_way: float) -> np.ndarray:
    prev = np.concatenate([np.zeros(1, dtype=float), pos[:-1]])
    return pos * rets - cost_one_way * np.abs(pos - prev)


def max_dd(nets: np.ndarray) -> float:
    if len(nets) == 0:
        return 0.0
    equity = np.cumsum(nets)
    peak = np.maximum.accumulate(equity)
    return float(np.max(peak - equity))


def score_path(fold_nets: list[np.ndarray]) -> dict:
    if not fold_nets:
        return {
            "sum_net": 0.0,
            "max_dd": 0.0,
            "n_folds": 0,
            "fold_net": [],
            "n_sign_pos_last5": 0,
            "n_eval_folds": 0,
            "sign_stable_3of5": False,
            "promote": False,
        }
    fold_sums = [round(float(np.sum(nets)), 6) for nets in fold_nets]
    signs = [bool(float(np.sum(nets)) > 0) for nets in fold_nets]
    eval_folds = signs[-5:] if len(signs) >= 5 else signs
    n_pos = sum(1 for flag in eval_folds if flag)
    all_nets = np.concatenate(fold_nets)
    return {
        "sum_net": round(float(np.sum(all_nets)), 6),
        "max_dd": round(max_dd(all_nets), 6),
        "n_folds": len(fold_nets),
        "fold_net": fold_sums,
        "n_sign_pos_last5": n_pos,
        "n_eval_folds": len(eval_folds),
        "sign_stable_3of5": bool(len(eval_folds) >= 5 and n_pos >= 3),
        "promote": False,
    }


def decide_vs_mom(challenger: dict, baseline: dict) -> tuple[str, list[str]]:
    reasons = []
    if challenger["sum_net"] <= baseline["sum_net"]:
        reasons.append(
            f"sum_net={challenger['sum_net']:.4f}<=mom={baseline['sum_net']:.4f}"
        )
    dd_slack = challenger["max_dd"] - baseline["max_dd"]
    if dd_slack > DD_SLACK + 1e-12:
        reasons.append(f"max_dd worse by {dd_slack:.2%} >5pp vs mom")
    if not challenger.get("sign_stable_3of5"):
        reasons.append(
            "sign_stable fail: "
            f"{challenger.get('n_sign_pos_last5')}/{challenger.get('n_eval_folds')} pos folds"
        )
    return ("CONTINUE" if not reasons else "KILL"), reasons


def family_pass_floor(n_seeds: int) -> int:
    return max(3, int(np.ceil(FAMILY_MIN_FRAC * n_seeds)))


def present_cols(df: pd.DataFrame, names: list[str]) -> list[str]:
    return [name for name in names if name in df.columns]


def arm_row_mask(df: pd.DataFrame, label: str, cols: list[str]) -> np.ndarray:
    label_vals = df[label].to_numpy(dtype=float)
    label_ok = np.isfinite(label_vals) & (label_vals != 0)
    if not cols:
        return label_ok
    feat = df[cols].to_numpy(dtype=float)
    return label_ok & np.isfinite(feat).all(axis=1)


def cell_key(
    *,
    horizon: int,
    step: int,
    cost_one_way: float,
    lookback: int,
    corr_min: float,
    thr_long: float,
    thr_short: float,
    C: float,
    loo_drop: str | None,
) -> str:
    drop = loo_drop or "full"
    return (
        f"h{horizon}_step{step}_cost{int(round(cost_one_way * 1e4))}bps_"
        f"lb{lookback}_corr{corr_min}_thr{thr_long}-{thr_short}_C{C}_drop-{drop}"
    )


def is_primary(meta: dict) -> bool:
    return (
        meta.get("horizon") == PRIMARY["horizon"]
        and meta.get("step") == PRIMARY["step"]
        and abs(float(meta.get("cost_one_way", -1)) - PRIMARY["cost_one_way"]) < 1e-12
        and meta.get("lookback") == PRIMARY["lookback"]
        and abs(float(meta.get("corr_min", -1)) - PRIMARY["corr_min"]) < 1e-12
        and abs(float(meta.get("thr_long", -1)) - PRIMARY["thr_long"]) < 1e-12
        and abs(float(meta.get("thr_short", -1)) - PRIMARY["thr_short"]) < 1e-12
        and abs(float(meta.get("C", -1)) - PRIMARY["C"]) < 1e-12
        and meta.get("loo_drop") is None
    )


def run_pair(
    featured: pd.DataFrame,
    mom_cols: list[str],
    chal_cols: list[str],
    *,
    horizon: int,
    step: int,
    cost_one_way: float,
    thr_long: float,
    thr_short: float,
    C: float,
    seed: int,
) -> dict:
    label = f"fwd_ret_{horizon}d"
    if label not in featured.columns:
        return {"error": "missing_label", "promote": False}
    embargo = max(2, (horizon + 4) // 5)
    pair_cols = list(dict.fromkeys([*mom_cols, *chal_cols]))
    mask = arm_row_mask(featured, label, pair_cols)
    work = featured.loc[mask].reset_index(drop=True)
    if len(work) < TRAIN_MIN + TEST_SIZE or not mom_cols or not chal_cols:
        return {"error": "insufficient_rows", "n": int(len(work)), "promote": False}
    y = (work[label].to_numpy() > 0).astype(int)
    rets = work[label].to_numpy(dtype=float)
    folds = purged_folds(len(work), embargo=embargo, step=step)
    mom_nets = []
    chal_nets = []
    for train_idx, test_idx in folds:
        x_mom = work[mom_cols].to_numpy(dtype=float)
        x_chal = work[chal_cols].to_numpy(dtype=float)
        mom_proba = fit_logistic(x_mom[train_idx], y[train_idx], x_mom[test_idx], seed, C)
        chal_proba = fit_logistic(x_chal[train_idx], y[train_idx], x_chal[test_idx], seed, C)
        mom_nets.append(
            turnover_nets(positions(mom_proba, thr_long, thr_short), rets[test_idx], cost_one_way)
        )
        chal_nets.append(
            turnover_nets(positions(chal_proba, thr_long, thr_short), rets[test_idx], cost_one_way)
        )
    mom_score = score_path(mom_nets)
    chal_score = score_path(chal_nets)
    verdict, reasons = decide_vs_mom(chal_score, mom_score)
    return {
        "n": int(len(work)),
        "n_folds": len(folds),
        "embargo": embargo,
        "mom": mom_score,
        "challenger": chal_score,
        "verdict": verdict,
        "reasons": reasons,
        "promote": False,
    }


def write_partial(payload: dict) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "copper_s2_tabular_marathon_memo.json").write_text(
        json.dumps(payload, indent=2, default=str)
    )


def main() -> int:
    t_run = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel_path = resolve_panel()
    panel_sha = sha256_file(panel_path)
    df = pd.read_parquet(panel_path)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
    built = datetime.now(timezone.utc).isoformat()
    panel_meta = {
        "path": str(panel_path),
        "sha256": panel_sha,
        "sha_note": "matches_v0" if panel_sha.startswith(V0_SHA12) else "sha_changed",
        "shape": list(df.shape),
        "promote": False,
    }
    available_horizons = [h for h in HORIZONS if f"fwd_ret_{h}d" in df.columns]
    missing_core = [col for col in ["fwd_ret_5d", *MOM_COLS] if col not in df.columns]
    floor = family_pass_floor(len(SEEDS))

    if missing_core or 5 not in available_horizons:
        family = "SHELF"
        note = f"missing_core={missing_core} horizons={available_horizons}"
        seed_rows: list[dict] = []
        topology_rows: list[dict] = []
    else:
        # Spec jobs: (lookback, corr_min, cell_kind, extra)
        # cell_kind: grid | loo | C_sweep
        drop_cols = GRAPH_SURVIVORS + COT_SURVIVORS
        n_topo = len(LOOKBACKS) * len(CORR_MINS)
        print(
            f"[marathon] start n_panel={len(df)} topologies={n_topo} "
            f"seeds={len(SEEDS)} horizons={available_horizons} "
            f"target_wall_clock=4h+ promote=false",
            flush=True,
        )
        topology_rows = []
        primary_by_seed: dict[int, dict] = {seed: {} for seed in SEEDS}

        for topo_i, (lookback, corr_min) in enumerate(
            itertools.product(LOOKBACKS, CORR_MINS), start=1
        ):
            t_topo = time.time()
            print(
                f"[marathon] topology {topo_i}/{n_topo} "
                f"lookback={lookback} corr_min={corr_min}",
                flush=True,
            )
            featured = emit_graph_features(df, lookback=lookback, corr_min=corr_min)
            mom_cols = present_cols(featured, MOM_COLS)
            shortlist = present_cols(featured, MOM_COLS + SHORTLIST_EXTRA)
            graph_cols = present_cols(featured, GRAPH_SURVIVORS)
            cot_cols = present_cols(featured, COT_SURVIVORS)
            full_chal = list(dict.fromkeys(shortlist + graph_cols + cot_cols))
            if not mom_cols or not shortlist:
                topology_rows.append(
                    {
                        "lookback": lookback,
                        "corr_min": corr_min,
                        "error": "missing_arm_cols",
                        "promote": False,
                    }
                )
                continue

            cells_out = []
            # Full stress grid (diagnostic)
            grid = list(
                itertools.product(
                    available_horizons, STEPS, COSTS, THRESHOLDS, (PRIMARY["C"],)
                )
            )
            # Primary C sweep + LOO only on primary geometry
            primary_extras = []
            if lookback == PRIMARY["lookback"] and abs(corr_min - PRIMARY["corr_min"]) < 1e-12:
                for C in C_GRID:
                    primary_extras.append(
                        (
                            PRIMARY["horizon"],
                            PRIMARY["step"],
                            PRIMARY["cost_one_way"],
                            (PRIMARY["thr_long"], PRIMARY["thr_short"]),
                            C,
                            None,
                        )
                    )
                for drop in drop_cols:
                    if drop in full_chal:
                        primary_extras.append(
                            (
                                PRIMARY["horizon"],
                                PRIMARY["step"],
                                PRIMARY["cost_one_way"],
                                (PRIMARY["thr_long"], PRIMARY["thr_short"]),
                                PRIMARY["C"],
                                drop,
                            )
                        )

            jobs = []
            for horizon, step, cost, thr, C in grid:
                jobs.append((horizon, step, cost, thr, C, None))
            jobs.extend(primary_extras)
            # de-dupe
            seen = set()
            uniq_jobs = []
            for job in jobs:
                key = (job[0], job[1], job[2], job[3], job[4], job[5])
                if key in seen:
                    continue
                seen.add(key)
                uniq_jobs.append(job)

            for job_i, (horizon, step, cost, thr, C, loo_drop) in enumerate(uniq_jobs, start=1):
                thr_long, thr_short = thr
                chal_cols = [c for c in full_chal if c != loo_drop] if loo_drop else full_chal
                meta = {
                    "horizon": horizon,
                    "step": step,
                    "cost_one_way": cost,
                    "lookback": lookback,
                    "corr_min": corr_min,
                    "thr_long": thr_long,
                    "thr_short": thr_short,
                    "C": C,
                    "loo_drop": loo_drop,
                }
                key = cell_key(**meta)
                seed_hits = []
                for seed in SEEDS:
                    result = run_pair(
                        featured,
                        mom_cols,
                        chal_cols,
                        horizon=horizon,
                        step=step,
                        cost_one_way=cost,
                        thr_long=thr_long,
                        thr_short=thr_short,
                        C=C,
                        seed=seed,
                    )
                    hit = {
                        "seed": seed,
                        "cell_key": key,
                        **meta,
                        **result,
                    }
                    seed_hits.append(hit)
                    if is_primary(meta):
                        primary_by_seed[seed] = hit
                n_cont = sum(1 for h in seed_hits if h.get("verdict") == "CONTINUE")
                cells_out.append(
                    {
                        "cell_key": key,
                        **meta,
                        "n_seeds_continue": n_cont,
                        "n_seeds": len(SEEDS),
                        "is_primary": is_primary(meta),
                        "seed_hits": seed_hits,
                        "promote": False,
                    }
                )
                if job_i == 1 or job_i % 10 == 0 or job_i == len(uniq_jobs):
                    print(
                        f"[marathon] topo {topo_i}/{n_topo} job={job_i}/{len(uniq_jobs)} "
                        f"{key} cont={n_cont}/{len(SEEDS)} "
                        f"elapsed_topo_s={time.time() - t_topo:.0f} "
                        f"elapsed_run_s={time.time() - t_run:.0f}",
                        flush=True,
                    )

            topology_rows.append(
                {
                    "lookback": lookback,
                    "corr_min": corr_min,
                    "n_jobs": len(uniq_jobs),
                    "elapsed_s": round(time.time() - t_topo, 1),
                    "cells": cells_out,
                    "promote": False,
                }
            )
            # Mid-run memo (downloadable)
            seed_verdicts = []
            for seed in SEEDS:
                hit = primary_by_seed.get(seed) or {}
                seed_verdicts.append(
                    {
                        "seed": seed,
                        "verdict": hit.get("verdict", "PENDING"),
                        "primary_ok": hit.get("verdict") == "CONTINUE",
                        "sum_net": (hit.get("challenger") or {}).get("sum_net"),
                        "mom_sum_net": (hit.get("mom") or {}).get("sum_net"),
                    }
                )
            n_ok = sum(1 for row in seed_verdicts if row.get("verdict") == "CONTINUE")
            write_partial(
                {
                    "promote": False,
                    "version": VERSION,
                    "partial": True,
                    "topo_done": topo_i,
                    "topo_total": n_topo,
                    "elapsed_run_s": round(time.time() - t_run, 1),
                    "n_seeds_continue_primary": n_ok,
                    "n_seeds": len(SEEDS),
                    "family_pass_floor": floor,
                    "seed_verdicts": seed_verdicts,
                    "panel_sha12": panel_sha[:12],
                }
            )

        seed_rows = []
        for seed in SEEDS:
            hit = primary_by_seed.get(seed) or {}
            seed_rows.append(
                {
                    "seed": seed,
                    "verdict": hit.get("verdict", "KILL"),
                    "primary_ok": hit.get("verdict") == "CONTINUE",
                    "primary": hit,
                    "promote": False,
                }
            )
        n_ok = sum(1 for row in seed_rows if row.get("verdict") == "CONTINUE")
        family = "CONTINUE" if n_ok >= floor else "KILL"
        note = (
            f"seeds_continue_primary={n_ok}/{len(SEEDS)} floor={floor} "
            f"elapsed_s={round(time.time() - t_run, 1)}"
        )

    metrics = {
        "promote": False,
        "NOT_A_PROMOTE": True,
        "version": VERSION,
        "built_at_utc": built,
        "elapsed_run_s": round(time.time() - t_run, 1),
        "prior": {
            "survivors_v0": "CONTINUE_5/5",
            "s2ablate": "KILL_0/5",
            "note": "GAT closed; marathon is tabular only",
        },
        "gate": (
            "PRIMARY only: h5/step26/4bps/lb52/corr0.25/thr0.60-0.40/C1.0/full feats; "
            "shortlist_graph_cot vs MOM on costed sum_net + DD slack + sign>=3/5; "
            f"family CONTINUE if >={FAMILY_MIN_FRAC:.0%} of {len(SEEDS)} seeds"
        ),
        "panel": panel_meta,
        "primary": PRIMARY,
        "lookbacks": list(LOOKBACKS),
        "corr_mins": list(CORR_MINS),
        "horizons": available_horizons if not missing_core else [],
        "steps": list(STEPS),
        "costs": list(COSTS),
        "thresholds": [list(t) for t in THRESHOLDS],
        "C_grid": list(C_GRID),
        "seeds": list(SEEDS),
        "family_pass_floor": floor,
        "seed_rows": seed_rows,
        "topology_rows": topology_rows,
        "n_seeds_continue": sum(1 for row in seed_rows if row.get("verdict") == "CONTINUE"),
        "n_seeds": len(SEEDS),
        "verdict": family,
        "note": note,
        "no_gat": True,
    }
    memo = {
        "verdict": family,
        "promote": False,
        "version": VERSION,
        "partial": False,
        "panel_sha12": panel_sha[:12],
        "sha_note": panel_meta["sha_note"],
        "n_seeds_continue": metrics["n_seeds_continue"],
        "n_seeds": len(SEEDS),
        "elapsed_run_s": metrics["elapsed_run_s"],
        "note": note,
        "seed_verdicts": [
            {
                "seed": row.get("seed"),
                "verdict": row.get("verdict"),
                "primary_ok": row.get("primary_ok"),
            }
            for row in seed_rows
        ],
        "paths": {
            "metrics": str(OUT_DIR / "copper_s2_tabular_marathon_metrics.json"),
            "memo": str(OUT_DIR / "copper_s2_tabular_marathon_memo.json"),
        },
    }
    receipt = (
        f"Verdict: {family} (promote=false) version={VERSION}\n"
        f"sha12={panel_sha[:12]} {panel_meta['sha_note']}\n"
        f"{note}\n"
        f"primary={PRIMARY}\n"
        f"no_gat=True\n"
        f"elapsed_run_s={metrics['elapsed_run_s']}\n"
    )
    (OUT_DIR / "copper_s2_tabular_marathon_metrics.json").write_text(
        json.dumps(metrics, indent=2, default=str)
    )
    (OUT_DIR / "copper_s2_tabular_marathon_memo.json").write_text(
        json.dumps(memo, indent=2, default=str)
    )
    (OUT_DIR / "copper_s2_tabular_marathon_receipt.txt").write_text(receipt)
    print(json.dumps(memo, indent=2, default=str), flush=True)
    print("RECEIPT:\n" + receipt, flush=True)
    return 0


if __name__ == "__main__":
    main()
