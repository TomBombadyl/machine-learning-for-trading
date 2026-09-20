#!/usr/bin/env python3
"""Fresh paste — S2 tabular deep stress (no GAT). Longer/better than v0 stamp.

promote=false ALWAYS. Paste this WHOLE file as one new cell on the
existing S2 notebook. Same Friday panel (sha 35f1fce22bca…).

Prior stamp (do not rerun for novelty):
  copper_s2_tabular_survivors_kaggle.py → CONTINUE 5/5, seed-invariant
  on this frame (logistic + frozen feats). Headline = shortlist_graph_cot.

Closed (do not reopen):
  copper_gnn_kaggle / s2gate / s2ablate / TinyGAT / Cell 2 typed GAT

What this cell adds (stress grid, still logistic only):
  - Horizons: fwd_ret_5d always; 21d / 63d if columns exist
  - Steps: 26 (v1) and 13 (ablate geometry as sensitivity)
  - Costs: 4 bps and 8 bps one-way turnover
  - Per-arm row masks (no joint dropna across unused columns)
  - NaN → 0 after per-arm finite mask (scaler-safe)
  - Headline gate on shortlist_graph_cot vs MOM (not any-arm)

Seeds 42–46 still run (re-stamp + receipt shape). Expect near-identical
paths under fixed C / frozen features — diversity comes from the grid,
not from seed noise.

Family CONTINUE if ≥3/5 seeds have shortlist_graph_cot CONTINUE on the
primary cell (h=5, step=26, cost=4bps) AND that same arm also CONTINUES
on ≥1 alternate grid cell (other horizon/step/cost). Never PROMOTE.

Download after success:
  copper_s2_tabular_deep_memo.json
  copper_s2_tabular_deep_metrics.json
  copper_s2_tabular_deep_receipt.txt
"""
from __future__ import annotations

import hashlib
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

VERSION = "copper_s2_tabular_deep_v0"
PROMOTE = False
V0_SHA12 = "35f1fce22bca"
DD_SLACK = 0.05
THR_LONG = 0.60
THR_SHORT = 0.40
TRAIN_MIN = 104
TEST_SIZE = 26
LOOKBACK = 52
CORR_MIN = 0.25
SEEDS = tuple(range(42, 47))
FAMILY_MIN_FRAC = 0.60
PRIMARY = {"horizon": 5, "step": 26, "cost_one_way": 0.0004}
HORIZONS = (5, 21, 63)
STEPS = (26, 13)
COSTS = (0.0004, 0.0008)
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


def snapshot_features(df: pd.DataFrame, loc: int) -> dict:
    start = max(0, loc - LOOKBACK + 1)
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
            if np.isfinite(rho) and abs(rho) >= CORR_MIN:
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


def emit_graph_features(df: pd.DataFrame) -> pd.DataFrame:
    work = df.reset_index(drop=True)
    feats = pd.DataFrame([snapshot_features(work, loc) for loc in range(len(work))])
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
    """Rows usable for one arm: finite label ≠ 0 and finite arm features."""
    label_ok = np.isfinite(df[label].to_numpy(dtype=float)) & (df[label].to_numpy(dtype=float) != 0)
    if not cols:
        return label_ok
    feat = df[cols].to_numpy(dtype=float)
    feat_ok = np.isfinite(feat).all(axis=1)
    return label_ok & feat_ok


def run_cell(
    featured: pd.DataFrame,
    arms: dict[str, list[str]],
    *,
    horizon: int,
    step: int,
    cost_one_way: float,
    seed: int,
) -> dict | None:
    label = f"fwd_ret_{horizon}d"
    if label not in featured.columns:
        return None
    embargo = max(2, (horizon + 4) // 5)
    mom_cols = arms["mom"]
    scores: dict[str, dict] = {}
    arm_verdicts: dict[str, dict] = {}
    arm_n: dict[str, int] = {}
    t0 = time.time()

    for name, cols in arms.items():
        if name == "mom":
            continue
        pair_cols = list(dict.fromkeys([*mom_cols, *cols]))
        mask = arm_row_mask(featured, label, pair_cols)
        work = featured.loc[mask].reset_index(drop=True)
        arm_n[name] = int(len(work))
        if len(work) < TRAIN_MIN + TEST_SIZE or not mom_cols:
            scores[name] = score_path([])
            arm_verdicts[name] = {
                "verdict": "KILL",
                "reasons": ["insufficient_rows"],
                "promote": False,
            }
            continue
        y = (work[label].to_numpy() > 0).astype(int)
        rets = work[label].to_numpy(dtype=float)
        folds = purged_folds(len(work), embargo=embargo, step=step)
        mom_nets = []
        chal_nets = []
        for train_idx, test_idx in folds:
            x_mom = work[mom_cols].to_numpy(dtype=float)
            x_chal = work[cols].to_numpy(dtype=float)
            mom_proba = fit_logistic(x_mom[train_idx], y[train_idx], x_mom[test_idx], seed)
            chal_proba = fit_logistic(x_chal[train_idx], y[train_idx], x_chal[test_idx], seed)
            mom_nets.append(turnover_nets(positions(mom_proba), rets[test_idx], cost_one_way))
            chal_nets.append(turnover_nets(positions(chal_proba), rets[test_idx], cost_one_way))
        mom_score = score_path(mom_nets)
        chal_score = score_path(chal_nets)
        if "mom" not in scores or mom_score["n_folds"] >= scores["mom"]["n_folds"]:
            scores["mom"] = mom_score
            arm_n["mom"] = int(len(work))
        scores[name] = chal_score
        verdict, reasons = decide_vs_mom(chal_score, mom_score)
        arm_verdicts[name] = {"verdict": verdict, "reasons": reasons, "promote": False}

    if "mom" not in scores or scores["mom"]["n_folds"] == 0:
        return {
            "horizon": horizon,
            "step": step,
            "cost_one_way": cost_one_way,
            "seed": seed,
            "error": "insufficient_mom_folds",
            "arm_n": arm_n,
            "promote": False,
        }
    headline = arm_verdicts.get("shortlist_graph_cot", {})
    return {
        "horizon": horizon,
        "step": step,
        "cost_one_way": cost_one_way,
        "seed": seed,
        "embargo": embargo,
        "arm_n": arm_n,
        "arms": scores,
        "arm_verdicts": arm_verdicts,
        "headline_verdict": headline.get("verdict", "KILL"),
        "elapsed_s": round(time.time() - t0, 1),
        "promote": False,
        "compare_note": "each challenger vs MOM on shared finite mask for that pair",
    }


def cell_key(horizon: int, step: int, cost_one_way: float) -> str:
    return f"h{horizon}_step{step}_cost{int(round(cost_one_way * 1e4))}bps"


def is_primary(cell: dict) -> bool:
    return (
        cell.get("horizon") == PRIMARY["horizon"]
        and cell.get("step") == PRIMARY["step"]
        and abs(float(cell.get("cost_one_way", -1)) - PRIMARY["cost_one_way"]) < 1e-12
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel_path = resolve_panel()
    panel_sha = sha256_file(panel_path)
    df = pd.read_parquet(panel_path)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
    featured = emit_graph_features(df)
    mom_cols = present_cols(featured, MOM_COLS)
    shortlist = present_cols(featured, MOM_COLS + SHORTLIST_EXTRA)
    graph_cols = present_cols(featured, GRAPH_SURVIVORS)
    cot_cols = present_cols(featured, COT_SURVIVORS)
    arms = {
        "mom": mom_cols,
        "shortlist": shortlist,
        "shortlist_graph_cot": list(dict.fromkeys(shortlist + graph_cols + cot_cols)),
    }
    available_horizons = [h for h in HORIZONS if f"fwd_ret_{h}d" in featured.columns]
    built = datetime.now(timezone.utc).isoformat()
    panel_meta = {
        "path": str(panel_path),
        "sha256": panel_sha,
        "sha_note": "matches_v0" if panel_sha.startswith(V0_SHA12) else "sha_changed",
        "shape": list(df.shape),
        "promote": False,
    }
    seed_rows: list[dict] = []
    missing_core = [col for col in ["fwd_ret_5d", *MOM_COLS] if col not in featured.columns]
    if missing_core or not mom_cols or not shortlist or 5 not in available_horizons:
        family = "SHELF"
        note = (
            f"missing_core={missing_core} mom={mom_cols} shortlist={shortlist} "
            f"horizons={available_horizons}"
        )
    else:
        grid = [
            (h, step, cost)
            for h in available_horizons
            for step in STEPS
            for cost in COSTS
        ]
        print(
            f"[s2deep] n_panel={len(featured)} seeds={len(SEEDS)} "
            f"grid={len(grid)} arms={ {k: len(v) for k, v in arms.items()} } "
            f"graph={graph_cols} cot={cot_cols} horizons={available_horizons}",
            flush=True,
        )
        floor = family_pass_floor(len(SEEDS))
        for seed in SEEDS:
            print(f"[s2deep] start seed={seed}", flush=True)
            cells = []
            for horizon, step, cost in grid:
                cell = run_cell(
                    featured,
                    arms,
                    horizon=horizon,
                    step=step,
                    cost_one_way=cost,
                    seed=seed,
                )
                if cell is None:
                    continue
                cell["cell_key"] = cell_key(horizon, step, cost)
                cells.append(cell)
                print(
                    f"[s2deep] seed={seed} {cell['cell_key']} "
                    f"headline={cell.get('headline_verdict')} "
                    f"elapsed_s={cell.get('elapsed_s')}",
                    flush=True,
                )
            primary = next((c for c in cells if is_primary(c)), None)
            alt_ok = [
                c
                for c in cells
                if not is_primary(c) and c.get("headline_verdict") == "CONTINUE"
            ]
            primary_ok = bool(primary and primary.get("headline_verdict") == "CONTINUE")
            seed_continue = primary_ok and len(alt_ok) >= 1
            row = {
                "seed": seed,
                "verdict": "CONTINUE" if seed_continue else "KILL",
                "primary_ok": primary_ok,
                "n_alt_continue": len(alt_ok),
                "alt_continue_keys": [c["cell_key"] for c in alt_ok],
                "primary": primary,
                "cells": cells,
                "promote": False,
            }
            seed_rows.append(row)
            n_ok = sum(1 for item in seed_rows if item.get("verdict") == "CONTINUE")
            (OUT_DIR / "copper_s2_tabular_deep_memo.json").write_text(
                json.dumps(
                    {
                        "promote": False,
                        "version": VERSION,
                        "partial": True,
                        "n_done": len(seed_rows),
                        "n_seeds": len(SEEDS),
                        "n_seeds_continue": n_ok,
                        "family_pass_floor": floor,
                        "seed_verdicts": [
                            {
                                "seed": item.get("seed"),
                                "verdict": item.get("verdict"),
                                "primary_ok": item.get("primary_ok"),
                                "n_alt_continue": item.get("n_alt_continue"),
                            }
                            for item in seed_rows
                        ],
                    },
                    indent=2,
                    default=str,
                )
            )
            print(
                f"[s2deep] done seed={seed} verdict={row['verdict']} "
                f"primary_ok={primary_ok} alt={len(alt_ok)} "
                f"running={n_ok}/{len(seed_rows)} floor={floor}",
                flush=True,
            )
        n_ok = sum(1 for row in seed_rows if row.get("verdict") == "CONTINUE")
        family = "CONTINUE" if n_ok >= floor else "KILL"
        note = f"seeds_continue={n_ok}/{len(SEEDS)} floor={floor} headline=shortlist_graph_cot"

    metrics = {
        "promote": False,
        "NOT_A_PROMOTE": True,
        "version": VERSION,
        "built_at_utc": built,
        "prior": {
            "survivors_v0": "CONTINUE_5/5",
            "s2gate": "KILL_0/20",
            "s2ablate": "KILL_0/5",
            "note": "GAT closed; deep stress is tabular only",
        },
        "gate": (
            "PRIMARY (h5/step26/4bps): shortlist_graph_cot beats MOM on costed "
            "sum_net AND maxDD not > baseline+5pp AND sign-stable >=3/5; "
            "AND same arm CONTINUES on >=1 alternate (horizon|step|cost) cell; "
            f"family CONTINUE if >={FAMILY_MIN_FRAC:.0%} of {len(SEEDS)} seeds"
        ),
        "panel": panel_meta,
        "primary": PRIMARY,
        "horizons": available_horizons if not missing_core else [],
        "steps": list(STEPS),
        "costs": list(COSTS),
        "seeds": list(SEEDS),
        "arms_cols": {key: list(val) for key, val in arms.items()},
        "graph_survivors_frozen": GRAPH_SURVIVORS,
        "cot_survivors_frozen": COT_SURVIVORS,
        "family_pass_floor": family_pass_floor(len(SEEDS)),
        "seed_rows": seed_rows,
        "n_seeds_continue": sum(1 for row in seed_rows if row.get("verdict") == "CONTINUE"),
        "n_seeds": len(SEEDS),
        "verdict": family,
        "note": note,
        "code_notes": [
            "per-arm finite masks (no joint dropna across unused cols)",
            "nan_to_num before StandardScaler",
            "seed-invariant logistic expected; grid is the stress",
        ],
    }
    memo = {
        "verdict": family,
        "promote": False,
        "version": VERSION,
        "panel_sha12": panel_sha[:12],
        "sha_note": panel_meta["sha_note"],
        "n_seeds_continue": metrics["n_seeds_continue"],
        "n_seeds": len(SEEDS),
        "note": note,
        "seed_verdicts": [
            {
                "seed": row.get("seed"),
                "verdict": row.get("verdict"),
                "primary_ok": row.get("primary_ok"),
                "n_alt_continue": row.get("n_alt_continue"),
                "alt_continue_keys": row.get("alt_continue_keys"),
            }
            for row in seed_rows
        ],
        "paths": {
            "metrics": str(OUT_DIR / "copper_s2_tabular_deep_metrics.json"),
            "memo": str(OUT_DIR / "copper_s2_tabular_deep_memo.json"),
        },
    }
    receipt = (
        f"Verdict: {family} (promote=false) version={VERSION}\n"
        f"sha12={panel_sha[:12]} {panel_meta['sha_note']}\n"
        f"{note}\n"
        f"primary={PRIMARY}\n"
        f"no_gat=True\n"
    )
    (OUT_DIR / "copper_s2_tabular_deep_metrics.json").write_text(
        json.dumps(metrics, indent=2, default=str)
    )
    (OUT_DIR / "copper_s2_tabular_deep_memo.json").write_text(
        json.dumps(memo, indent=2, default=str)
    )
    (OUT_DIR / "copper_s2_tabular_deep_receipt.txt").write_text(receipt)
    print(json.dumps(memo, indent=2, default=str), flush=True)
    print("RECEIPT:\n" + receipt, flush=True)
    return 0


if __name__ == "__main__":
    main()
