#!/usr/bin/env python3
"""Emit Ch23.4-style topology columns onto the copper Friday grid.

**NOT A PROMOTE.** NetworkX snapshot per Friday. Lookback ends at
``decision_date``. Does not train a GNN. Does not commit parquets
unless the operator passes ``--output-parquet`` to a gitignored path.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

_DIR = Path(__file__).resolve().parent
if str(_DIR) not in sys.path:
    sys.path.insert(0, str(_DIR))

from contract import GRAPH_FEAT_PANEL, NOT_A_PROMOTE, banner, write_report
from experiment_a_cot_mom_purge import HORIZON, screen_feature
from panel_io import load_or_build_panel

PROMOTE = False
LOOKBACK = 52
CORR_MIN = 0.25
SERIES = {
    "HG": ["ret_hg", "mom_5d"],
    "CPER": ["ret_cper", "cper_mom_21d"],
    "COPX": ["ret_copx", "copx_mom_21d"],
    "FCX": ["ret_fcx", "fcx_mom_63d"],
    "COT_MM": ["cot_managed_money_net_chg_1w", "cot_managed_money_net"],
    "SHFE_WH": ["shfe_warrant_pct_chg_21d", "shfe_warrant_chg_21d"],
}
PROXY_EDGES = (("CPER", "HG"), ("COPX", "HG"), ("FCX", "HG"))


def _first_present(df: pd.DataFrame, names: list[str]) -> str | None:
    return next((name for name in names if name in df.columns), None)


def _corr(a: np.ndarray, b: np.ndarray) -> float:
    mask = np.isfinite(a) & np.isfinite(b)
    if int(mask.sum()) < 16:
        return float("nan")
    corr, _ = spearmanr(a[mask], b[mask])
    return float(corr)


def _hhi(weights: list[float]) -> float:
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
    node_cols: dict[str, str] = {}
    for node, candidates in SERIES.items():
        col = _first_present(window, candidates)
        if col is None:
            continue
        if window[col].notna().sum() < 16:
            continue
        node_cols[node] = col
    graph = nx.Graph()
    for node in node_cols:
        graph.add_node(node)
    nodes = list(node_cols)
    for i, left in enumerate(nodes):
        for right in nodes[i + 1 :]:
            rho = _corr(window[node_cols[left]].to_numpy(), window[node_cols[right]].to_numpy())
            if np.isfinite(rho) and abs(rho) >= CORR_MIN:
                graph.add_edge(left, right, weight=abs(rho), kind="corr")
    for src, dst in PROXY_EDGES:
        if src in graph and dst in graph and not graph.has_edge(src, dst):
            graph.add_edge(src, dst, weight=0.35, kind="proxy")
    if "COT_MM" in graph and "HG" in graph and not graph.has_edge("COT_MM", "HG"):
        graph.add_edge("COT_MM", "HG", weight=0.35, kind="positioning")
    if "SHFE_WH" in graph and "HG" in graph and not graph.has_edge("SHFE_WH", "HG"):
        graph.add_edge("SHFE_WH", "HG", weight=0.35, kind="inventory")
    pagerank = nx.pagerank(graph, weight="weight") if graph.number_of_nodes() else {}
    between = (
        nx.betweenness_centrality(graph, weight="weight") if graph.number_of_nodes() > 2 else {}
    )
    hg_weights = [abs(data.get("weight", 0.0)) for _, _, data in graph.edges("HG", data=True)]
    return {
        "graph_n_nodes": int(graph.number_of_nodes()),
        "graph_n_edges": int(graph.number_of_edges()),
        "graph_degree": int(graph.degree("HG")) if "HG" in graph else 0,
        "graph_pagerank": float(pagerank.get("HG", 0.0)),
        "graph_betweenness": float(between.get("HG", 0.0)),
        "graph_hhi": _hhi(hg_weights),
        "graph_nodes": ",".join(sorted(graph.nodes())),
    }


def emit_features(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    work = df.reset_index(drop=True)
    for loc in range(len(work)):
        rows.append(snapshot_features(work, loc))
    feats = pd.DataFrame(rows)
    out = pd.concat([work.reset_index(drop=True), feats], axis=1)
    return out


def purge_graph_cols(df: pd.DataFrame) -> list[dict]:
    label = f"fwd_ret_{HORIZON}d"
    if label not in df.columns:
        return []
    embargo = max(2, (HORIZON + 4) // 5)
    cols = [
        "graph_degree",
        "graph_pagerank",
        "graph_betweenness",
        "graph_hhi",
        "graph_n_nodes",
        "graph_n_edges",
    ]
    return [screen_feature(df, col, label, embargo) for col in cols if col in df.columns]


def main() -> int:
    parser = argparse.ArgumentParser(description=banner())
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--output-parquet", type=Path, default=GRAPH_FEAT_PANEL)
    parser.add_argument("--no-yfinance", action="store_true")
    args = parser.parse_args()
    df, meta = load_or_build_panel(allow_yfinance=not args.no_yfinance)
    featured = emit_features(df)
    rows = purge_graph_cols(featured)
    survivors = [row["feature"] for row in rows if row.get("survivor")]
    if args.output_parquet is not None:
        args.output_parquet.parent.mkdir(parents=True, exist_ok=True)
        featured.to_parquet(args.output_parquet, index=False)
    payload = {
        "status": "NOT_A_PROMOTE",
        "promote": False,
        "not_a_promote": NOT_A_PROMOTE,
        "experiment": "copper_graph_tabular_features",
        "verdict": "CONTINUE" if survivors else "SHELF",
        "note": (
            "Graph topology columns survived IC→purge."
            if survivors
            else "No graph topology column survived IC→purge. GAT stays blocked."
        ),
        "survivors": survivors,
        "rows": rows,
        "panel": meta,
        "parquet": str(args.output_parquet) if args.output_parquet else None,
        "allow_gnn": bool(survivors),
        "banner": banner(),
    }
    write_report(payload, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
