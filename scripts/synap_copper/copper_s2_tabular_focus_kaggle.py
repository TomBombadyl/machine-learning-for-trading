#!/usr/bin/env python3
"""Fresh paste — S2 tabular FOCUS v1.1 (log-shrunk + crash-safe). No GAT.

promote=false ALWAYS. Paste this WHOLE file as ONE new cell.
Same Friday panel (sha 35f1fce22bca…).

Kaggle long-run (grounded — see docs/synap/KAGGLE_LONG_RUN.md):
  - Set notebook Persistence to **Files only** or **Variables and Files**
    *before* the session dies
    (Kaggle product note: https://www.kaggle.com/discussions/product-feedback/355440).
  - Only ``/kaggle/working`` is carried over; ``/tmp`` is not.
  - Still download Output mid-run; persistence is best-effort.
  - Optional: Save Version → Save & Run All to archive outputs.

This cell writes (atomic replace + fsync):
  copper_s2_tabular_focus_memo.json          every 25 jobs + topo end
  copper_s2_tabular_focus_heartbeat.json     every job
  copper_s2_tabular_focus_primary_gate.json  as soon as PRIMARY finishes
  copper_s2_tabular_focus_hits.jsonl         CONTINUE / primary rows
  copper_s2_tabular_focus_metrics.json       end of run
  copper_s2_tabular_focus_receipt.txt        end of run

Grid size (v1.1): 12 topologies, ~438 cells × 5 seeds (~2190 fits).
Primary topology alone is ~262 cells — that is the family gate.

Learned from stalled focus_v0 logs (2026-09-21):
  - 63 topologies timed out (~6h → topo 28). Shrink topologies.
  - Run **primary topology first** (lb52/corr0.25) so a timeout still
    leaves a family verdict.
  - h5 + rolling + graphx CONTINUED even at 12–16 bps; keep cost ladder
    on h5, prefer rolling+expanding both.
  - h10 / corr0.45 lean rows were mostly 0/5 — drop wide horizon×corr
    spam; only light h10/h21 checks on primary.
  - Extreme thr bands (0.65/0.35 etc.) mostly 0/5 — keep 0.55/0.45 and
    0.60/0.40 only.
  - Mid-job checkpoints (v0 lacked them mid-primary).

Primary family gate (unchanged):
  h5 / step26 / 4bps / lb52 / corr0.25 / thr0.60-0.40 / C=1.0 /
  expanding / shortlist_graph_cot
Family CONTINUE if ≥3/5 seeds pass PRIMARY. Never PROMOTE. No GAT.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

VERSION = "copper_s2_tabular_focus_v1_1"
PROMOTE = False
V0_SHA12 = "35f1fce22bca"
MEMO_NAME = "copper_s2_tabular_focus_memo.json"
HEARTBEAT_NAME = "copper_s2_tabular_focus_heartbeat.json"
PRIMARY_GATE_NAME = "copper_s2_tabular_focus_primary_gate.json"
HITS_NAME = "copper_s2_tabular_focus_hits.jsonl"
METRICS_NAME = "copper_s2_tabular_focus_metrics.json"
RECEIPT_NAME = "copper_s2_tabular_focus_receipt.txt"
DD_SLACK = 0.05
TRAIN_MIN = 104
TEST_SIZE = 26
SEEDS = tuple(range(42, 47))
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
    "train_mode": "expanding",
    "loo_drop": None,
    "arm": "shortlist_graph_cot",
}
# Derive extras if missing; lean grids mostly use h5.
HORIZONS = (5, 10, 21)
# Primary topology FIRST, then a short lookback×corr list (no 0.45 — log KILL).
_LOOKBACKS = (26, 52, 78, 104)
_CORR_MINS = (0.15, 0.25, 0.35)
TOPOLOGIES: list[tuple[int, float]] = [(52, 0.25)] + [
    (lb, c)
    for lb in _LOOKBACKS
    for c in _CORR_MINS
    if not (lb == 52 and abs(c - 0.25) < 1e-12)
]
STEPS = (26, 13)
COSTS = (0.0004, 0.0006, 0.0008, 0.0012, 0.0016)  # kept high costs (log CONTINUE)
THRESHOLDS = ((0.55, 0.45), (0.60, 0.40))
C_GRID = (0.25, 1.0, 4.0)
TRAIN_MODES = ("expanding", "rolling")
ROLLING_TRAIN = 156

MOM_COLS = ["mom_5d", "mom_21d", "mom_63d"]
SHORTLIST_EXTRA = ["cper_mom_21d", "fcx_mom_63d"]
GRAPH_SURVIVORS = ["graph_pagerank", "graph_betweenness", "graph_hhi"]
COT_SURVIVORS = [
    "cot_managed_money_net",
    "cot_managed_money_pct_oi",
    "cot_managed_money_z_52w",
]
EXTRA_CANDIDATES = [
    "copx_mom_21d",
    "cot_managed_money_net_chg_1w",
    "shfe_warrant_pct_chg_21d",
    "shfe_warrant_chg_21d",
    "ret_hg",
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


def ensure_horizons(df: pd.DataFrame, horizons: tuple[int, ...]) -> tuple[pd.DataFrame, list[str]]:
    """Add missing fwd_ret_{h}d from close_hg (trading-day shift on Friday grid)."""
    work = df.copy()
    derived = []
    close_col = next(
        (c for c in ("close_hg", "HG_close", "close") if c in work.columns), None
    )
    if close_col is None:
        return work, derived
    close = work[close_col].astype(float)
    for h in horizons:
        col = f"fwd_ret_{h}d"
        if col in work.columns:
            continue
        work[col] = close.shift(-h) / close - 1.0
        derived.append(col)
    return work, derived


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
        "graph_n_nodes": float(graph.number_of_nodes()),
        "graph_n_edges": float(graph.number_of_edges()),
        "graph_degree": float(graph.degree("HG") if "HG" in graph else 0),
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
                f"[focus] emit lb={lookback} corr={corr_min} "
                f"row={loc + 1}/{n} elapsed_s={time.time() - t0:.0f}",
                flush=True,
            )
    return pd.concat([work, pd.DataFrame(rows)], axis=1)


def purged_folds(n: int, embargo: int, step: int, train_mode: str):
    folds = []
    start = TRAIN_MIN
    while start + TEST_SIZE <= n:
        test_start = start
        train_end = test_start - embargo
        if train_end < 40:
            start += step
            continue
        if train_mode == "rolling":
            train_start = max(0, train_end - ROLLING_TRAIN)
            train_idx = np.arange(train_start, train_end)
        else:
            train_idx = np.arange(0, train_end)
        if len(train_idx) < 40:
            start += step
            continue
        folds.append((train_idx, np.arange(test_start, test_start + TEST_SIZE)))
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


def build_arms(featured: pd.DataFrame) -> dict[str, list[str]]:
    mom = present_cols(featured, MOM_COLS)
    shortlist = present_cols(featured, MOM_COLS + SHORTLIST_EXTRA)
    graph = present_cols(featured, GRAPH_SURVIVORS)
    cot = present_cols(featured, COT_SURVIVORS)
    extras = present_cols(featured, EXTRA_CANDIDATES)
    # expanded graph topology cols from emit
    graph_x = present_cols(
        featured, GRAPH_SURVIVORS + ["graph_n_nodes", "graph_n_edges", "graph_degree"]
    )
    return {
        "mom": mom,
        "shortlist": shortlist,
        "shortlist_graph": list(dict.fromkeys(shortlist + graph)),
        "shortlist_graph_cot": list(dict.fromkeys(shortlist + graph + cot)),
        "shortlist_graphx_cot": list(dict.fromkeys(shortlist + graph_x + cot)),
        "shortlist_graph_cot_extra": list(dict.fromkeys(shortlist + graph + cot + extras)),
    }


def cell_key(meta: dict) -> str:
    drop = meta.get("loo_drop") or "full"
    return (
        f"h{meta['horizon']}_step{meta['step']}_"
        f"cost{int(round(meta['cost_one_way'] * 1e4))}bps_"
        f"lb{meta['lookback']}_corr{meta['corr_min']}_"
        f"thr{meta['thr_long']}-{meta['thr_short']}_C{meta['C']}_"
        f"{meta['train_mode']}_arm-{meta['arm']}_drop-{drop}"
    )


def is_primary(meta: dict) -> bool:
    p = PRIMARY
    return (
        meta.get("horizon") == p["horizon"]
        and meta.get("step") == p["step"]
        and abs(float(meta.get("cost_one_way", -1)) - p["cost_one_way"]) < 1e-12
        and meta.get("lookback") == p["lookback"]
        and abs(float(meta.get("corr_min", -1)) - p["corr_min"]) < 1e-12
        and abs(float(meta.get("thr_long", -1)) - p["thr_long"]) < 1e-12
        and abs(float(meta.get("thr_short", -1)) - p["thr_short"]) < 1e-12
        and abs(float(meta.get("C", -1)) - p["C"]) < 1e-12
        and meta.get("train_mode") == p["train_mode"]
        and meta.get("loo_drop") is None
        and meta.get("arm") == p["arm"]
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
    train_mode: str,
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
    folds = purged_folds(len(work), embargo=embargo, step=step, train_mode=train_mode)
    mom_nets, chal_nets = [], []
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
        "lift_sum_net": round(chal_score["sum_net"] - mom_score["sum_net"], 6),
        "verdict": verdict,
        "reasons": reasons,
        "promote": False,
    }


def atomic_write_json(path: Path, payload: dict) -> None:
    """Write JSON via temp+replace+fsync so a kill mid-write leaves the prior file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    data = json.dumps(payload, indent=2, default=str)
    with open(tmp, "w", encoding="utf-8") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def write_partial(payload: dict) -> None:
    atomic_write_json(OUT_DIR / MEMO_NAME, payload)


def write_heartbeat(payload: dict) -> None:
    atomic_write_json(OUT_DIR / HEARTBEAT_NAME, payload)


def print_kaggle_preflight() -> None:
    print(
        "[focus] KAGGLE LONG-RUN CHECKLIST (do before / while this cell runs)\n"
        "  1. Notebook Options → Persistence → Files only OR Variables and Files\n"
        "     (must be on BEFORE the session dies; only /kaggle/working carries)\n"
        "     cite: kaggle.com/discussions/product-feedback/355440\n"
        "  2. Input attached: synap-finpredict-panels-v0 (Friday panel)\n"
        "  3. Accelerator: None / CPU (this cell is sklearn logistic)\n"
        "  4. While running, refresh Output and download if the session wobbles:\n"
        f"       {MEMO_NAME}\n"
        f"       {HEARTBEAT_NAME}\n"
        f"       {PRIMARY_GATE_NAME}\n"
        f"       {HITS_NAME}\n"
        "  5. After finish (or stall): also grab metrics + receipt if present.\n"
        "  6. Optional durable archive: Save Version → Save & Run All.\n"
        f"  version={VERSION} promote=false no_gat=True",
        flush=True,
    )


def rank_rows(rows: list[dict], key: str, top: int = 12) -> list[dict]:
    scored = [r for r in rows if isinstance(r.get(key), (int, float))]
    scored.sort(key=lambda r: r[key], reverse=True)
    return scored[:top]


def main() -> int:
    t_run = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print_kaggle_preflight()
    hits_path = OUT_DIR / HITS_NAME
    hits_path.write_text("")  # reset append log each run
    write_heartbeat(
        {
            "promote": False,
            "version": VERSION,
            "phase": "boot",
            "elapsed_run_s": 0.0,
            "out_dir": str(OUT_DIR),
        }
    )
    panel_path = resolve_panel()
    panel_sha = sha256_file(panel_path)
    df = pd.read_parquet(panel_path)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
    df, derived_labels = ensure_horizons(df, HORIZONS)
    built = datetime.now(timezone.utc).isoformat()
    panel_meta = {
        "path": str(panel_path),
        "sha256": panel_sha,
        "sha_note": "matches_v0" if panel_sha.startswith(V0_SHA12) else "sha_changed",
        "shape": list(df.shape),
        "derived_fwd_ret": derived_labels,
        "promote": False,
    }
    available_horizons = [h for h in HORIZONS if f"fwd_ret_{h}d" in df.columns]
    missing_core = [c for c in ["fwd_ret_5d", *MOM_COLS] if c not in df.columns]
    floor = family_pass_floor(len(SEEDS))
    seed_rows: list[dict] = []
    topology_rows: list[dict] = []
    diagnostic_hits: list[dict] = []

    if missing_core or 5 not in available_horizons:
        family = "SHELF"
        note = f"missing_core={missing_core} horizons={available_horizons}"
    else:
        n_topo = len(TOPOLOGIES)
        print(
            f"[focus] start version={VERSION} n={len(df)} topologies={n_topo} "
            f"(primary_first={TOPOLOGIES[0]}) horizons={available_horizons} "
            f"derived={derived_labels} seeds={list(SEEDS)} no_gat=True "
            f"expect~438 cells / ~2190 seed-fits",
            flush=True,
        )
        primary_by_seed: dict[int, dict] = {s: {} for s in SEEDS}

        for topo_i, (lookback, corr_min) in enumerate(TOPOLOGIES, start=1):
            t_topo = time.time()
            is_primary_topo = (
                lookback == PRIMARY["lookback"]
                and abs(corr_min - PRIMARY["corr_min"]) < 1e-12
            )
            print(
                f"[focus] topology {topo_i}/{n_topo} lb={lookback} corr={corr_min} "
                f"primary_topo={is_primary_topo}",
                flush=True,
            )
            featured = emit_graph_features(df, lookback=lookback, corr_min=corr_min)
            arms = build_arms(featured)
            mom_cols = arms["mom"]
            if not mom_cols or not arms["shortlist"]:
                topology_rows.append(
                    {
                        "lookback": lookback,
                        "corr_min": corr_min,
                        "error": "missing_arm_cols",
                        "promote": False,
                    }
                )
                continue

            jobs = []
            if is_primary_topo:
                jobs.append({**PRIMARY})
                for cost, thr, train_mode, arm_name, C in itertools.product(
                    COSTS,
                    THRESHOLDS,
                    TRAIN_MODES,
                    (
                        "shortlist",
                        "shortlist_graph",
                        "shortlist_graph_cot",
                        "shortlist_graphx_cot",
                    ),
                    C_GRID,
                ):
                    if arm_name not in arms or not arms[arm_name]:
                        continue
                    jobs.append(
                        {
                            "horizon": 5,
                            "step": 26,
                            "cost_one_way": cost,
                            "lookback": lookback,
                            "corr_min": corr_min,
                            "thr_long": thr[0],
                            "thr_short": thr[1],
                            "C": C,
                            "train_mode": train_mode,
                            "arm": arm_name,
                            "loo_drop": None,
                        }
                    )
                for cost, train_mode in itertools.product(COSTS, TRAIN_MODES):
                    jobs.append(
                        {
                            "horizon": 5,
                            "step": 13,
                            "cost_one_way": cost,
                            "lookback": lookback,
                            "corr_min": corr_min,
                            "thr_long": 0.60,
                            "thr_short": 0.40,
                            "C": 1.0,
                            "train_mode": train_mode,
                            "arm": "shortlist_graph_cot",
                            "loo_drop": None,
                        }
                    )
                for horizon, train_mode in itertools.product((10, 21), TRAIN_MODES):
                    if horizon not in available_horizons:
                        continue
                    jobs.append(
                        {
                            "horizon": horizon,
                            "step": 26,
                            "cost_one_way": 0.0004,
                            "lookback": lookback,
                            "corr_min": corr_min,
                            "thr_long": 0.60,
                            "thr_short": 0.40,
                            "C": 1.0,
                            "train_mode": train_mode,
                            "arm": "shortlist_graph_cot",
                            "loo_drop": None,
                        }
                    )
                for drop in list(GRAPH_SURVIVORS) + list(COT_SURVIVORS) + [
                    "drop_graph",
                    "drop_cot",
                ]:
                    jobs.append({**PRIMARY, "loo_drop": drop})
            else:
                for step, cost, train_mode, arm_name in itertools.product(
                    (26, 13),
                    (0.0004, 0.0008),
                    TRAIN_MODES,
                    ("shortlist_graph_cot", "shortlist"),
                ):
                    jobs.append(
                        {
                            "horizon": 5,
                            "step": step,
                            "cost_one_way": cost,
                            "lookback": lookback,
                            "corr_min": corr_min,
                            "thr_long": 0.60,
                            "thr_short": 0.40,
                            "C": 1.0,
                            "train_mode": train_mode,
                            "arm": arm_name,
                            "loo_drop": None,
                        }
                    )

            seen = set()
            uniq = []
            for job in jobs:
                key = cell_key(job)
                if key in seen:
                    continue
                seen.add(key)
                uniq.append(job)
            print(
                f"[focus] topo {topo_i}/{n_topo} n_jobs={len(uniq)} "
                f"first={cell_key(uniq[0]) if uniq else None}",
                flush=True,
            )

            cells_out = []
            for job_i, meta in enumerate(uniq, start=1):
                arm_cols = list(arms.get(meta["arm"], []))
                drop = meta.get("loo_drop")
                if drop == "drop_graph":
                    arm_cols = [c for c in arm_cols if c not in GRAPH_SURVIVORS]
                elif drop == "drop_cot":
                    arm_cols = [c for c in arm_cols if c not in COT_SURVIVORS]
                elif drop:
                    arm_cols = [c for c in arm_cols if c != drop]
                if not arm_cols:
                    continue

                seed_hits = []
                for seed in SEEDS:
                    result = run_pair(
                        featured,
                        mom_cols,
                        arm_cols,
                        horizon=meta["horizon"],
                        step=meta["step"],
                        cost_one_way=meta["cost_one_way"],
                        thr_long=meta["thr_long"],
                        thr_short=meta["thr_short"],
                        C=meta["C"],
                        train_mode=meta["train_mode"],
                        seed=seed,
                    )
                    hit = {"seed": seed, "cell_key": cell_key(meta), **meta, **result}
                    seed_hits.append(hit)
                    if is_primary(meta):
                        primary_by_seed[seed] = hit
                    if result.get("verdict") == "CONTINUE" and "lift_sum_net" in result:
                        diagnostic_hits.append(
                            {
                                "cell_key": hit["cell_key"],
                                "seed": seed,
                                "horizon": meta["horizon"],
                                "lookback": meta["lookback"],
                                "corr_min": meta["corr_min"],
                                "cost_one_way": meta["cost_one_way"],
                                "train_mode": meta["train_mode"],
                                "arm": meta["arm"],
                                "loo_drop": meta.get("loo_drop"),
                                "lift_sum_net": result["lift_sum_net"],
                                "sum_net": result["challenger"]["sum_net"],
                                "mom_sum_net": result["mom"]["sum_net"],
                            }
                        )

                n_cont = sum(1 for h in seed_hits if h.get("verdict") == "CONTINUE")
                compact_hits = []
                for h in seed_hits:
                    ch = dict(h)
                    for side in ("mom", "challenger"):
                        if isinstance(ch.get(side), dict):
                            ch[side] = {
                                k: v
                                for k, v in ch[side].items()
                                if k != "fold_net"
                            }
                    compact_hits.append(ch)
                cell_row = {
                    "cell_key": cell_key(meta),
                    **meta,
                    "n_seeds_continue": n_cont,
                    "n_seeds": len(SEEDS),
                    "is_primary": is_primary(meta),
                    "seed_hits": compact_hits,
                    "promote": False,
                }
                cells_out.append(cell_row)
                if n_cont > 0 or is_primary(meta):
                    with open(OUT_DIR / HITS_NAME, "a", encoding="utf-8") as hit_f:
                        hit_f.write(
                            json.dumps(
                                {
                                    "topo_i": topo_i,
                                    "job_i": job_i,
                                    "n_jobs": len(uniq),
                                    "elapsed_run_s": round(time.time() - t_run, 1),
                                    "n_seeds_continue": n_cont,
                                    "is_primary": is_primary(meta),
                                    "cell_key": cell_row["cell_key"],
                                    "horizon": meta["horizon"],
                                    "lookback": meta["lookback"],
                                    "corr_min": meta["corr_min"],
                                    "cost_one_way": meta["cost_one_way"],
                                    "thr_long": meta["thr_long"],
                                    "thr_short": meta["thr_short"],
                                    "C": meta["C"],
                                    "train_mode": meta["train_mode"],
                                    "arm": meta["arm"],
                                    "loo_drop": meta.get("loo_drop"),
                                    "mean_lift": round(
                                        float(
                                            np.mean(
                                                [
                                                    h.get("lift_sum_net")
                                                    for h in seed_hits
                                                    if isinstance(
                                                        h.get("lift_sum_net"),
                                                        (int, float),
                                                    )
                                                ]
                                                or [0.0]
                                            )
                                        ),
                                        6,
                                    ),
                                    "promote": False,
                                }
                            )
                            + "\n"
                        )
                        hit_f.flush()
                        os.fsync(hit_f.fileno())

                write_heartbeat(
                    {
                        "promote": False,
                        "version": VERSION,
                        "phase": "cell",
                        "topo_i": topo_i,
                        "topo_total": n_topo,
                        "job_i": job_i,
                        "n_jobs": len(uniq),
                        "cell_key": cell_row["cell_key"],
                        "n_seeds_continue": n_cont,
                        "is_primary": is_primary(meta),
                        "elapsed_run_s": round(time.time() - t_run, 1),
                        "panel_sha12": panel_sha[:12],
                    }
                )

                if is_primary(meta):
                    seed_verdicts = []
                    for seed in SEEDS:
                        hit = primary_by_seed.get(seed) or {}
                        seed_verdicts.append(
                            {
                                "seed": seed,
                                "verdict": hit.get("verdict", "PENDING"),
                                "primary_ok": hit.get("verdict") == "CONTINUE",
                                "lift_sum_net": hit.get("lift_sum_net"),
                                "sum_net": (hit.get("challenger") or {}).get("sum_net"),
                                "mom_sum_net": (hit.get("mom") or {}).get("sum_net"),
                            }
                        )
                    n_ok = sum(1 for r in seed_verdicts if r.get("verdict") == "CONTINUE")
                    family_so_far = "CONTINUE" if n_ok >= floor else "KILL"
                    atomic_write_json(
                        OUT_DIR / PRIMARY_GATE_NAME,
                        {
                            "promote": False,
                            "version": VERSION,
                            "partial": True,
                            "gate": "PRIMARY",
                            "family_so_far": family_so_far,
                            "n_seeds_continue": n_ok,
                            "n_seeds": len(SEEDS),
                            "family_pass_floor": floor,
                            "cell_key": cell_row["cell_key"],
                            "seed_verdicts": seed_verdicts,
                            "elapsed_run_s": round(time.time() - t_run, 1),
                            "panel_sha12": panel_sha[:12],
                            "note": (
                                "Family gate is decided by this primary cell alone. "
                                "Later grid rows are diagnostics."
                            ),
                        },
                    )
                    print(
                        f"[focus] PRIMARY GATE DONE family_so_far={family_so_far} "
                        f"seeds={n_ok}/{len(SEEDS)} floor={floor} "
                        f"wrote {PRIMARY_GATE_NAME}",
                        flush=True,
                    )

                if job_i == 1 or job_i % 25 == 0 or job_i == len(uniq):
                    print(
                        f"[focus] topo {topo_i}/{n_topo} job={job_i}/{len(uniq)} "
                        f"{cell_key(meta)[:80]}… cont={n_cont}/{len(SEEDS)} "
                        f"run_s={time.time() - t_run:.0f}",
                        flush=True,
                    )
                    seed_verdicts = []
                    for seed in SEEDS:
                        hit = primary_by_seed.get(seed) or {}
                        seed_verdicts.append(
                            {
                                "seed": seed,
                                "verdict": hit.get("verdict", "PENDING"),
                                "primary_ok": hit.get("verdict") == "CONTINUE",
                                "lift_sum_net": hit.get("lift_sum_net"),
                            }
                        )
                    write_partial(
                        {
                            "promote": False,
                            "version": VERSION,
                            "partial": True,
                            "topo_done": topo_i - 1,
                            "topo_in_progress": topo_i,
                            "topo_total": n_topo,
                            "job_i": job_i,
                            "n_jobs": len(uniq),
                            "lookback": lookback,
                            "corr_min": corr_min,
                            "elapsed_run_s": round(time.time() - t_run, 1),
                            "n_seeds_continue_primary": sum(
                                1
                                for r in seed_verdicts
                                if r.get("verdict") == "CONTINUE"
                            ),
                            "n_seeds": len(SEEDS),
                            "family_pass_floor": floor,
                            "available_horizons": available_horizons,
                            "derived_fwd_ret": derived_labels,
                            "top_lifts": rank_rows(diagnostic_hits, "lift_sum_net"),
                            "recent_continue_keys": [
                                c["cell_key"]
                                for c in cells_out
                                if c.get("n_seeds_continue", 0) > 0
                            ][-40:],
                            "seed_verdicts": seed_verdicts,
                            "panel_sha12": panel_sha[:12],
                            "hits_jsonl": str(OUT_DIR / HITS_NAME),
                            "primary_gate": str(OUT_DIR / PRIMARY_GATE_NAME),
                            "heartbeat": str(OUT_DIR / HEARTBEAT_NAME),
                        }
                    )

            topology_rows.append(
                {
                    "lookback": lookback,
                    "corr_min": corr_min,
                    "n_jobs": len(uniq),
                    "elapsed_s": round(time.time() - t_topo, 1),
                    "cells": cells_out,
                    "promote": False,
                }
            )
            seed_verdicts = []
            for seed in SEEDS:
                hit = primary_by_seed.get(seed) or {}
                seed_verdicts.append(
                    {
                        "seed": seed,
                        "verdict": hit.get("verdict", "PENDING"),
                        "primary_ok": hit.get("verdict") == "CONTINUE",
                        "lift_sum_net": hit.get("lift_sum_net"),
                    }
                )
            n_ok = sum(1 for r in seed_verdicts if r.get("verdict") == "CONTINUE")
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
                    "available_horizons": available_horizons,
                    "derived_fwd_ret": derived_labels,
                    "top_lifts": rank_rows(diagnostic_hits, "lift_sum_net"),
                    "seed_verdicts": seed_verdicts,
                    "panel_sha12": panel_sha[:12],
                }
            )

        seed_rows = []
        for seed in SEEDS:
            hit = primary_by_seed.get(seed) or {}
            primary = {k: v for k, v in hit.items()}
            if isinstance(primary.get("mom"), dict):
                primary["mom"] = {
                    k: v for k, v in primary["mom"].items() if k != "fold_net"
                }
            if isinstance(primary.get("challenger"), dict):
                primary["challenger"] = {
                    k: v
                    for k, v in primary["challenger"].items()
                    if k != "fold_net"
                }
            seed_rows.append(
                {
                    "seed": seed,
                    "verdict": hit.get("verdict", "KILL"),
                    "primary_ok": hit.get("verdict") == "CONTINUE",
                    "primary": primary,
                    "promote": False,
                }
            )

        n_ok = sum(1 for r in seed_rows if r.get("verdict") == "CONTINUE")
        family = "CONTINUE" if n_ok >= floor else "KILL"
        note = (
            f"seeds_continue_primary={n_ok}/{len(SEEDS)} floor={floor} "
            f"horizons={available_horizons} derived={derived_labels} "
            f"elapsed_s={round(time.time() - t_run, 1)}"
        )

    by_h: dict[int, list[float]] = {}
    by_lb: dict[int, list[float]] = {}
    for hit in diagnostic_hits:
        by_h.setdefault(hit["horizon"], []).append(hit["lift_sum_net"])
        by_lb.setdefault(hit["lookback"], []).append(hit["lift_sum_net"])
    horizon_summary = [
        {
            "horizon": h,
            "n_continue_hits": len(vals),
            "mean_lift": round(float(np.mean(vals)), 6) if vals else None,
            "max_lift": round(float(np.max(vals)), 6) if vals else None,
        }
        for h, vals in sorted(by_h.items())
    ]
    lookback_summary = [
        {
            "lookback": lb,
            "n_continue_hits": len(vals),
            "mean_lift": round(float(np.mean(vals)), 6) if vals else None,
            "max_lift": round(float(np.max(vals)), 6) if vals else None,
        }
        for lb, vals in sorted(by_lb.items())
    ]

    metrics = {
        "promote": False,
        "NOT_A_PROMOTE": True,
        "version": VERSION,
        "built_at_utc": built,
        "elapsed_run_s": round(time.time() - t_run, 1),
        "learned_from": {
            "survivors_v0": "CONTINUE_5/5",
            "marathon_v0": "CONTINUE_10/10",
            "s2ablate": "KILL",
            "focus_v0_stall": "timeout_topo25_mid_primary",
            "upgrades": [
                "primary_topology_first",
                "shrunk_topologies_12",
                "rolling_vs_expanding",
                "arm_ladder",
                "loo_and_group_drops",
                "mid_job_atomic_memo",
                "heartbeat_every_job",
                "primary_gate_early_file",
            ],
        },
        "gate": (
            "PRIMARY only: h5/step26/4bps/lb52/corr0.25/thr0.60-0.40/C1/"
            "expanding/shortlist_graph_cot; family CONTINUE if "
            f">={FAMILY_MIN_FRAC:.0%} of {len(SEEDS)} seeds"
        ),
        "panel": panel_meta,
        "primary": PRIMARY,
        "grids": {
            "horizons": list(HORIZONS),
            "available_horizons": available_horizons if not missing_core else [],
            "topologies": [{"lookback": lb, "corr_min": c} for lb, c in TOPOLOGIES],
            "steps": list(STEPS),
            "costs": list(COSTS),
            "thresholds": [list(t) for t in THRESHOLDS],
            "C_grid": list(C_GRID),
            "train_modes": list(TRAIN_MODES),
        },
        "seeds": list(SEEDS),
        "family_pass_floor": floor,
        "seed_rows": seed_rows,
        "topology_rows": topology_rows,
        "horizon_summary": horizon_summary,
        "lookback_summary": lookback_summary,
        "top_lifts": rank_rows(diagnostic_hits, "lift_sum_net", top=25),
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
        "partial": False,
        "panel_sha12": panel_sha[:12],
        "sha_note": panel_meta["sha_note"],
        "n_seeds_continue": metrics["n_seeds_continue"],
        "n_seeds": len(SEEDS),
        "elapsed_run_s": metrics["elapsed_run_s"],
        "available_horizons": available_horizons if not missing_core else [],
        "derived_fwd_ret": derived_labels,
        "horizon_summary": horizon_summary,
        "lookback_summary": lookback_summary,
        "top_lifts": metrics["top_lifts"][:12],
        "note": note,
        "seed_verdicts": [
            {
                "seed": r.get("seed"),
                "verdict": r.get("verdict"),
                "primary_ok": r.get("primary_ok"),
            }
            for r in seed_rows
        ],
        "paths": {
            "metrics": str(OUT_DIR / METRICS_NAME),
            "memo": str(OUT_DIR / MEMO_NAME),
            "primary_gate": str(OUT_DIR / PRIMARY_GATE_NAME),
            "heartbeat": str(OUT_DIR / HEARTBEAT_NAME),
            "hits_jsonl": str(OUT_DIR / HITS_NAME),
        },
    }
    receipt = (
        f"Verdict: {family} (promote=false) version={VERSION}\n"
        f"sha12={panel_sha[:12]} {panel_meta['sha_note']}\n"
        f"{note}\n"
        f"horizons={available_horizons} derived={derived_labels}\n"
        f"primary={PRIMARY}\n"
        f"no_gat=True\n"
        f"elapsed_run_s={metrics['elapsed_run_s']}\n"
    )
    atomic_write_json(OUT_DIR / METRICS_NAME, metrics)
    atomic_write_json(OUT_DIR / MEMO_NAME, memo)
    (OUT_DIR / RECEIPT_NAME).write_text(receipt)
    write_heartbeat(
        {
            "promote": False,
            "version": VERSION,
            "phase": "done",
            "verdict": family,
            "elapsed_run_s": metrics["elapsed_run_s"],
            "panel_sha12": panel_sha[:12],
        }
    )
    print(receipt, flush=True)
    print(json.dumps(memo, indent=2, default=str), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
