#!/usr/bin/env python3
"""Experiment A — COT+MOM IC → purge vs MOM_ONLY.

**NOT A PROMOTE.** Ch7-style time-series Spearman IC with embargo equal
to the label horizon in Friday sessions. Logistic is allowed only if
purge survivors exist. GAT is not this script.

Run::

    docker compose run --rm ml4t python scripts/synap_copper/experiment_a_cot_mom_purge.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

_DIR = Path(__file__).resolve().parent
if str(_DIR) not in sys.path:
    sys.path.insert(0, str(_DIR))

from contract import NOT_A_PROMOTE, banner, write_report
from panel_io import load_or_build_panel, newey_west_t

PROMOTE = False
HORIZON = 5
IC_ABS_MIN = 0.03
T_ABS_MIN = 1.64
MOM_CORR_MAX = 0.90
MIN_OBS = 80
MOM_COLS = ["mom_5d", "mom_21d", "mom_63d"]
COT_COLS = [
    "cot_managed_money_net",
    "cot_managed_money_pct_oi",
    "cot_managed_money_net_chg_1w",
    "cot_managed_money_z_52w",
]


def _spearman(x: np.ndarray, y: np.ndarray) -> float:
    mask = np.isfinite(x) & np.isfinite(y)
    if int(mask.sum()) < 12:
        return float("nan")
    corr, _ = spearmanr(x[mask], y[mask])
    return float(corr)


def expanding_ic(feature: pd.Series, label: pd.Series, embargo: int) -> np.ndarray:
    values = []
    feat = feature.to_numpy(dtype=float)
    lab = label.to_numpy(dtype=float)
    n = len(feat)
    start = max(MIN_OBS, 52)
    for end in range(start, n - embargo):
        train = slice(0, end)
        ic = _spearman(feat[train], lab[train])
        values.append(ic)
    return np.asarray(values, dtype=float)


def screen_feature(df: pd.DataFrame, col: str, label_col: str, embargo: int) -> dict:
    sub = df[[col, label_col]].dropna()
    sub = sub.loc[sub[label_col] != 0]
    ic_path = expanding_ic(sub[col], sub[label_col], embargo)
    ic_path = ic_path[np.isfinite(ic_path)]
    mean_ic = float(np.mean(ic_path)) if len(ic_path) else float("nan")
    t_stat = newey_west_t(ic_path, embargo)
    mid = max(1, len(ic_path) // 2)
    first = float(np.mean(ic_path[:mid])) if len(ic_path) else float("nan")
    second = float(np.mean(ic_path[mid:])) if len(ic_path) else float("nan")
    sign_stable = bool(np.isfinite(first) and np.isfinite(second) and first * second > 0)
    mom_corr = float("nan")
    if "mom_21d" in df.columns:
        both = df[[col, "mom_21d"]].dropna()
        if len(both) >= 12:
            mom_corr = _spearman(both[col].to_numpy(), both["mom_21d"].to_numpy())
    reasons = []
    if not np.isfinite(mean_ic) or abs(mean_ic) < IC_ABS_MIN:
        reasons.append(f"abs_ic<{IC_ABS_MIN}")
    if not np.isfinite(t_stat) or abs(t_stat) < T_ABS_MIN:
        reasons.append(f"abs_t<{T_ABS_MIN}")
    if not sign_stable:
        reasons.append("half_sign_flip")
    if np.isfinite(mom_corr) and abs(mom_corr) > MOM_CORR_MAX and col not in MOM_COLS:
        reasons.append(f"redundant_vs_mom21_{mom_corr:.2f}")
    if len(sub) < MIN_OBS:
        reasons.append(f"n<{MIN_OBS}")
    return {
        "feature": col,
        "n": int(len(sub)),
        "mean_ic": None if not np.isfinite(mean_ic) else round(mean_ic, 4),
        "t_hac": None if not np.isfinite(t_stat) else round(t_stat, 3),
        "ic_first_half": None if not np.isfinite(first) else round(first, 4),
        "ic_second_half": None if not np.isfinite(second) else round(second, 4),
        "sign_stable": sign_stable,
        "corr_mom_21d": None if not np.isfinite(mom_corr) else round(mom_corr, 4),
        "survivor": not reasons,
        "kill_reasons": reasons,
        "promote": False,
    }


def run_screen(df: pd.DataFrame) -> dict:
    label = f"fwd_ret_{HORIZON}d"
    if label not in df.columns:
        raise KeyError(f"{label} missing from panel")
    embargo = max(2, (HORIZON + 4) // 5)
    present_mom = [col for col in MOM_COLS if col in df.columns]
    present_cot = [col for col in COT_COLS if col in df.columns]
    rows = [screen_feature(df, col, label, embargo) for col in present_mom + present_cot]
    survivors = [row["feature"] for row in rows if row["survivor"]]
    cot_survivors = [name for name in survivors if name in present_cot]
    mom_survivors = [name for name in survivors if name in present_mom]
    if cot_survivors:
        verdict = "CONTINUE"
        note = "COT column(s) survived IC→purge vs fwd_ret_5d. Logistic allowed. Not a paper lock."
    elif mom_survivors:
        verdict = "SHELF"
        note = "Only MOM columns survived. COT added no incremental purged IC. Do not fit a new book."
    else:
        verdict = "SHELF"
        note = "No COT or MOM column cleared IC→purge."
    return {
        "status": "NOT_A_PROMOTE",
        "promote": False,
        "not_a_promote": NOT_A_PROMOTE,
        "experiment": "A_cot_mom_ic_purge",
        "verdict": verdict,
        "note": note,
        "label": label,
        "embargo_fridays": embargo,
        "thresholds": {
            "abs_ic_min": IC_ABS_MIN,
            "abs_t_min": T_ABS_MIN,
            "mom_corr_max": MOM_CORR_MAX,
        },
        "mom_cols_present": present_mom,
        "cot_cols_present": present_cot,
        "survivors": survivors,
        "cot_survivors": cot_survivors,
        "rows": rows,
        "allow_logistic": bool(cot_survivors),
        "allow_gnn": False,
        "gnn_note": "GAT is blocked until graph columns also survive a later purge.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=banner())
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--no-yfinance", action="store_true")
    args = parser.parse_args()
    df, meta = load_or_build_panel(allow_yfinance=not args.no_yfinance)
    payload = run_screen(df)
    payload["panel"] = meta
    payload["banner"] = banner()
    write_report(payload, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
