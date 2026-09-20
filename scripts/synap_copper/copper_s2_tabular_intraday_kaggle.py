#!/usr/bin/env python3
"""Fresh paste — copper S2 tabular INTRADAY (2h / 4h / 12h). No GAT.

promote=false ALWAYS. Paste this WHOLE file as ONE new cell.

Why a new cell:
  The stamped Friday panel (sha 35f1fce22bca…) is weekly. It cannot
  score 2h / 4h / 12h labels. This cell builds a **separate** hourly
  research panel from yfinance ``HG=F`` (1h bars) and scores those
  horizons. Do **not** mix this hash with the Friday registry.

Closed: TinyGAT / Cell 2 / Friday-panel reopen for hourly claims.

Horizons (bars of 1h):
  2h → fwd_ret_2h
  4h → fwd_ret_4h   (PRIMARY gate)
  12h → fwd_ret_12h

Family CONTINUE if ≥3/5 seeds pass PRIMARY (4h) vs MOM on costed
sum_net + DD slack + sign-stable last-5. 2h/12h are reported.
Never PROMOTE. Sample is shorter than Friday history — read receipt.

Download:
  copper_s2_tabular_intraday_memo.json
  copper_s2_tabular_intraday_metrics.json
  copper_s2_tabular_intraday_receipt.txt
"""
from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

try:
    import yfinance as yf
except ImportError:
    yf = None

VERSION = "copper_s2_tabular_intraday_v0"
PROMOTE = False
DD_SLACK = 0.05
THR_LONG = 0.60
THR_SHORT = 0.40
COST_ONE_WAY = 0.0004
COSTS = (0.0004, 0.0008, 0.0012)
SEEDS = tuple(range(42, 47))
FAMILY_MIN_FRAC = 0.60
# Hourly WF geometry (bars)
TRAIN_MIN = 24 * 20  # ~20 trading days of hours
TEST_SIZE = 24 * 5
STEP = 24 * 2
HORIZONS = (2, 4, 12)  # hours == 1h bars
PRIMARY_H = 4
YF_PERIOD = "730d"
YF_INTERVAL = "1h"
TICKERS = {"HG": "HG=F", "CPER": "CPER", "COPX": "COPX", "FCX": "FCX"}

OUT_DIR = (
    Path("/kaggle/working")
    if Path("/kaggle/working").exists()
    else Path("data/synap/copper/panels")
)


def family_pass_floor(n_seeds: int) -> int:
    return max(3, int(np.ceil(FAMILY_MIN_FRAC * n_seeds)))


def _flat_cols(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = [str(c[0]).lower() for c in df.columns]
    else:
        df = df.copy()
        df.columns = [str(c).lower() for c in df.columns]
    return df


def download_hourly() -> tuple[pd.DataFrame, dict]:
    if yf is None:
        raise ImportError("yfinance required for intraday paste")
    frames = []
    meta = {"tickers": {}, "promote": False}
    for name, ticker in TICKERS.items():
        raw = yf.download(
            ticker,
            period=YF_PERIOD,
            interval=YF_INTERVAL,
            auto_adjust=True,
            progress=False,
        )
        if raw is None or raw.empty:
            meta["tickers"][name] = {"ok": False}
            continue
        raw = _flat_cols(raw)
        if "close" not in raw.columns:
            meta["tickers"][name] = {"ok": False, "note": "no_close"}
            continue
        piece = raw[["close"]].rename(columns={"close": f"close_{name.lower()}"})
        piece.index = pd.to_datetime(piece.index).tz_localize(None)
        frames.append(piece)
        meta["tickers"][name] = {
            "ok": True,
            "ticker": ticker,
            "n": int(len(piece)),
            "start": str(piece.index.min()),
            "end": str(piece.index.max()),
        }
    if not frames:
        raise FileNotFoundError("yfinance returned no hourly closes")
    panel = pd.concat(frames, axis=1).sort_index()
    # keep rows with HG
    panel = panel.dropna(subset=["close_hg"]).copy()
    return panel, meta


def build_features(panel: pd.DataFrame) -> pd.DataFrame:
    df = panel.copy()
    close = df["close_hg"].astype(float)
    df["ret_1h"] = close.pct_change()
    for w in (2, 4, 12, 24, 48):
        df[f"mom_{w}h"] = close / close.shift(w) - 1.0
    for h in HORIZONS:
        df[f"fwd_ret_{h}h"] = close.shift(-h) / close - 1.0
    # proxy moms if present
    for name, w in (("cper", 12), ("copx", 12), ("fcx", 24)):
        col = f"close_{name}"
        if col in df.columns:
            df[f"{name}_mom_{w}h"] = df[col] / df[col].shift(w) - 1.0
    df = df.reset_index(names="ts")
    return df


def purged_folds(n: int, embargo: int):
    folds = []
    start = TRAIN_MIN
    while start + TEST_SIZE <= n:
        test_start = start
        train_end = test_start - embargo
        if train_end >= max(40, TRAIN_MIN // 2):
            folds.append((np.arange(0, train_end), np.arange(test_start, test_start + TEST_SIZE)))
        start += STEP
    return folds


def fit_logistic(x_train, y_train, x_test, seed: int):
    if len(np.unique(y_train)) < 2:
        return np.full(len(x_test), 0.5)
    x_train = np.nan_to_num(x_train, nan=0.0, posinf=0.0, neginf=0.0)
    x_test = np.nan_to_num(x_test, nan=0.0, posinf=0.0, neginf=0.0)
    scaler = StandardScaler()
    model = LogisticRegression(max_iter=800, class_weight="balanced", random_state=seed)
    model.fit(scaler.fit_transform(x_train), y_train)
    return model.predict_proba(scaler.transform(x_test))[:, 1]


def positions(proba: np.ndarray) -> np.ndarray:
    pos = np.zeros(len(proba), dtype=float)
    pos[proba >= THR_LONG] = 1.0
    pos[proba <= THR_SHORT] = -1.0
    return pos


def turnover_nets(pos: np.ndarray, rets: np.ndarray, cost: float) -> np.ndarray:
    prev = np.concatenate([np.zeros(1, dtype=float), pos[:-1]])
    return pos * rets - cost * np.abs(pos - prev)


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
            "n_sign_pos_last5": 0,
            "n_eval_folds": 0,
            "sign_stable_3of5": False,
            "promote": False,
        }
    signs = [bool(float(np.sum(n)) > 0) for n in fold_nets]
    eval_folds = signs[-5:] if len(signs) >= 5 else signs
    n_pos = sum(1 for flag in eval_folds if flag)
    all_nets = np.concatenate(fold_nets)
    return {
        "sum_net": round(float(np.sum(all_nets)), 6),
        "max_dd": round(max_dd(all_nets), 6),
        "n_folds": len(fold_nets),
        "n_sign_pos_last5": n_pos,
        "n_eval_folds": len(eval_folds),
        "sign_stable_3of5": bool(len(eval_folds) >= 5 and n_pos >= 3),
        "promote": False,
    }


def decide_vs_mom(chal: dict, mom: dict) -> tuple[str, list[str]]:
    reasons = []
    if chal["sum_net"] <= mom["sum_net"]:
        reasons.append(f"sum_net={chal['sum_net']:.4f}<=mom={mom['sum_net']:.4f}")
    if chal["max_dd"] - mom["max_dd"] > DD_SLACK + 1e-12:
        reasons.append(f"max_dd worse by {chal['max_dd'] - mom['max_dd']:.2%} >5pp")
    if not chal.get("sign_stable_3of5"):
        reasons.append(
            f"sign_stable fail: {chal.get('n_sign_pos_last5')}/{chal.get('n_eval_folds')}"
        )
    return ("CONTINUE" if not reasons else "KILL"), reasons


def present(df: pd.DataFrame, cols: list[str]) -> list[str]:
    return [c for c in cols if c in df.columns]


def run_horizon(
    df: pd.DataFrame,
    horizon: int,
    cost: float,
    seed: int,
    arms: dict[str, list[str]],
) -> dict:
    label = f"fwd_ret_{horizon}h"
    embargo = max(2, horizon)
    need = [label, *{c for cols in arms.values() for c in cols}]
    work = df.dropna(subset=[c for c in need if c in df.columns]).copy()
    work = work.loc[np.isfinite(work[label]) & (work[label] != 0)].reset_index(drop=True)
    if len(work) < TRAIN_MIN + TEST_SIZE:
        return {"error": "insufficient_rows", "n": int(len(work)), "promote": False}
    y = (work[label].to_numpy() > 0).astype(int)
    rets = work[label].to_numpy(dtype=float)
    folds = purged_folds(len(work), embargo=embargo)
    scores = {}
    for name, cols in arms.items():
        cols = present(work, cols)
        if not cols:
            scores[name] = score_path([])
            continue
        nets = []
        x_all = work[cols].to_numpy(dtype=float)
        for train_idx, test_idx in folds:
            proba = fit_logistic(x_all[train_idx], y[train_idx], x_all[test_idx], seed)
            nets.append(turnover_nets(positions(proba), rets[test_idx], cost))
        scores[name] = score_path(nets)
    mom = scores.get("mom") or score_path([])
    verdicts = {}
    for name in arms:
        if name == "mom":
            continue
        verdict, reasons = decide_vs_mom(scores[name], mom)
        verdicts[name] = {"verdict": verdict, "reasons": reasons, "promote": False}
    best = None
    best_sum = float("-inf")
    for name, v in verdicts.items():
        if v["verdict"] == "CONTINUE" and scores[name]["sum_net"] > best_sum:
            best_sum = scores[name]["sum_net"]
            best = name
    seed_ok = any(v["verdict"] == "CONTINUE" for v in verdicts.values())
    return {
        "horizon_h": horizon,
        "cost_one_way": cost,
        "seed": seed,
        "n": int(len(work)),
        "n_folds": len(folds),
        "arms": scores,
        "arm_verdicts": verdicts,
        "best_continue_arm": best,
        "verdict": "CONTINUE" if seed_ok else "KILL",
        "promote": False,
    }


def panel_sha(df: pd.DataFrame) -> str:
    # hash of timestamps + HG close — not Friday sha
    blob = (
        df[["ts", "close_hg"]].astype(str).to_csv(index=False).encode("utf-8")
        if "ts" in df.columns
        else df.to_csv(index=False).encode("utf-8")
    )
    return hashlib.sha256(blob).hexdigest()


def main() -> int:
    t0 = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    built = datetime.now(timezone.utc).isoformat()
    print(
        f"[intraday] building HG=F {YF_INTERVAL} period={YF_PERIOD} "
        f"horizons={list(HORIZONS)}h primary={PRIMARY_H}h promote=false",
        flush=True,
    )
    raw, dl_meta = download_hourly()
    featured = build_features(raw)
    sha = panel_sha(featured)
    mom_cols = present(featured, ["mom_2h", "mom_4h", "mom_12h", "mom_24h"])
    shortlist = present(
        featured,
        mom_cols
        + ["cper_mom_12h", "copx_mom_12h", "fcx_mom_24h", "ret_1h"],
    )
    arms = {"mom": mom_cols, "shortlist": shortlist}
    floor = family_pass_floor(len(SEEDS))

    if len(mom_cols) < 2 or f"fwd_ret_{PRIMARY_H}h" not in featured.columns:
        family = "SHELF"
        note = f"missing_features mom={mom_cols}"
        seed_rows = []
        cells = []
    else:
        cells = []
        primary_by_seed = {}
        jobs = [(h, c) for h in HORIZONS for c in COSTS]
        for seed in SEEDS:
            print(f"[intraday] seed={seed}", flush=True)
            for horizon, cost in jobs:
                row = run_horizon(featured, horizon, cost, seed, arms)
                row["cell_key"] = f"h{horizon}h_cost{int(round(cost * 1e4))}bps"
                cells.append(row)
                if horizon == PRIMARY_H and abs(cost - COST_ONE_WAY) < 1e-12:
                    primary_by_seed[seed] = row
                print(
                    f"[intraday] seed={seed} {row['cell_key']} "
                    f"verdict={row.get('verdict')} n={row.get('n')} "
                    f"best={row.get('best_continue_arm')} "
                    f"elapsed_s={time.time() - t0:.0f}",
                    flush=True,
                )
            # mid memo
            (OUT_DIR / "copper_s2_tabular_intraday_memo.json").write_text(
                json.dumps(
                    {
                        "promote": False,
                        "version": VERSION,
                        "partial": True,
                        "seed_done": seed,
                        "primary_so_far": {
                            str(s): (primary_by_seed.get(s) or {}).get("verdict")
                            for s in SEEDS
                            if s in primary_by_seed
                        },
                        "elapsed_run_s": round(time.time() - t0, 1),
                    },
                    indent=2,
                    default=str,
                )
            )
        seed_rows = []
        for seed in SEEDS:
            hit = primary_by_seed.get(seed) or {}
            seed_rows.append(
                {
                    "seed": seed,
                    "verdict": hit.get("verdict", "KILL"),
                    "primary_ok": hit.get("verdict") == "CONTINUE",
                    "best_continue_arm": hit.get("best_continue_arm"),
                    "primary": hit,
                    "promote": False,
                }
            )
        n_ok = sum(1 for r in seed_rows if r.get("verdict") == "CONTINUE")
        family = "CONTINUE" if n_ok >= floor else "KILL"
        note = (
            f"seeds_continue_primary_{PRIMARY_H}h={n_ok}/{len(SEEDS)} floor={floor} "
            f"elapsed_s={round(time.time() - t0, 1)}"
        )

    # per-horizon continue counts at base cost
    horizon_counts = {}
    for h in HORIZONS:
        horizon_counts[h] = sum(
            1
            for c in cells
            if c.get("horizon_h") == h
            and abs(float(c.get("cost_one_way", -1)) - COST_ONE_WAY) < 1e-12
            and c.get("verdict") == "CONTINUE"
        )

    metrics = {
        "promote": False,
        "NOT_A_PROMOTE": True,
        "version": VERSION,
        "built_at_utc": built,
        "elapsed_run_s": round(time.time() - t0, 1),
        "note_vs_friday": (
            "Separate from Friday panel sha 35f1fce22bca. Hourly yfinance HG=F. "
            "Do not mix registry hashes."
        ),
        "panel": {
            "source": f"yfinance HG=F {YF_INTERVAL} period={YF_PERIOD}",
            "sha256": sha,
            "sha12": sha[:12],
            "n_rows": int(len(featured)),
            "ts_start": str(featured["ts"].iloc[0]) if len(featured) else None,
            "ts_end": str(featured["ts"].iloc[-1]) if len(featured) else None,
            "download": dl_meta,
            "promote": False,
        },
        "horizons_h": list(HORIZONS),
        "primary_horizon_h": PRIMARY_H,
        "costs": list(COSTS),
        "seeds": list(SEEDS),
        "arms_cols": {k: list(v) for k, v in arms.items()},
        "gate": (
            f"PRIMARY {PRIMARY_H}h @ {COST_ONE_WAY} one-way: challenger beats MOM on "
            "costed sum_net AND maxDD not >+5pp AND sign-stable >=3/5; "
            f"family CONTINUE if >={FAMILY_MIN_FRAC:.0%} of {len(SEEDS)} seeds"
        ),
        "horizon_continue_counts_at_4bps": horizon_counts,
        "seed_rows": seed_rows,
        "cells": cells,
        "n_seeds_continue": sum(1 for r in seed_rows if r.get("verdict") == "CONTINUE"),
        "n_seeds": len(SEEDS),
        "verdict": family,
        "note": note,
        "no_gat": True,
    }
    memo = {
        "verdict": family,
        "promote": False,
        "version": VERSION,
        "panel_sha12": sha[:12],
        "primary_horizon_h": PRIMARY_H,
        "horizons_h": list(HORIZONS),
        "horizon_continue_counts_at_4bps": horizon_counts,
        "n_seeds_continue": metrics["n_seeds_continue"],
        "n_seeds": len(SEEDS),
        "elapsed_run_s": metrics["elapsed_run_s"],
        "n_rows": int(len(featured)),
        "ts_start": metrics["panel"]["ts_start"],
        "ts_end": metrics["panel"]["ts_end"],
        "note": note,
        "seed_verdicts": [
            {
                "seed": r.get("seed"),
                "verdict": r.get("verdict"),
                "primary_ok": r.get("primary_ok"),
                "best_continue_arm": r.get("best_continue_arm"),
            }
            for r in seed_rows
        ],
        "paths": {
            "metrics": str(OUT_DIR / "copper_s2_tabular_intraday_metrics.json"),
            "memo": str(OUT_DIR / "copper_s2_tabular_intraday_memo.json"),
        },
    }
    receipt = (
        f"Verdict: {family} (promote=false) version={VERSION}\n"
        f"hourly_sha12={sha[:12]} source=yfinance_HG=F_1h_{YF_PERIOD}\n"
        f"NOT friday_panel_35f1fce22bca\n"
        f"horizons_h={list(HORIZONS)} primary={PRIMARY_H}h\n"
        f"horizon_continue_counts_4bps={horizon_counts}\n"
        f"{note}\n"
        f"n_rows={len(featured)} {metrics['panel']['ts_start']} → {metrics['panel']['ts_end']}\n"
        f"no_gat=True\n"
    )
    (OUT_DIR / "copper_s2_tabular_intraday_metrics.json").write_text(
        json.dumps(metrics, indent=2, default=str)
    )
    (OUT_DIR / "copper_s2_tabular_intraday_memo.json").write_text(
        json.dumps(memo, indent=2, default=str)
    )
    (OUT_DIR / "copper_s2_tabular_intraday_receipt.txt").write_text(receipt)
    print(json.dumps(memo, indent=2, default=str), flush=True)
    print("RECEIPT:\n" + receipt, flush=True)
    return 0


if __name__ == "__main__":
    main()
