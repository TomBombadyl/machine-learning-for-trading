#!/usr/bin/env python3
"""GAT hybrid vs tabular survivors — copper Friday graph.

**NOT A PROMOTE.** Adapts Ch23 ``06_gnn_feature_engineering`` to the
copper instrument graph (not Wiki Prices). Trains only if graph
topology columns survived IC→purge. CPU is allowed: the graph is tiny.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

_DIR = Path(__file__).resolve().parent
if str(_DIR) not in sys.path:
    sys.path.insert(0, str(_DIR))

from contract import GRAPH_FEAT_PANEL, NOT_A_PROMOTE, banner, write_report
from copper_graph_tabular_features import emit_features, purge_graph_cols
from panel_io import load_or_build_panel

try:
    import torch
    from torch import nn
except ImportError:
    torch = None
    nn = None

PROMOTE = False
TRAIN_MIN = 104
TEST_SIZE = 26
STEP = 26
EPOCHS = 20
EMBED_DIM = 4
NODE_ORDER = ["HG", "CPER", "COPX", "FCX", "COT_MM", "SHFE_WH"]
NODE_SERIES = {
    "HG": ["ret_hg", "mom_5d"],
    "CPER": ["ret_cper", "cper_mom_21d"],
    "COPX": ["ret_copx", "copx_mom_21d"],
    "FCX": ["ret_fcx", "fcx_mom_63d"],
    "COT_MM": ["cot_managed_money_net_chg_1w", "cot_managed_money_net"],
    "SHFE_WH": ["shfe_warrant_pct_chg_21d", "shfe_warrant_chg_21d"],
}


class TinyGAT(nn.Module if nn is not None else object):
    """One-layer GAT on a dense tiny adjacency. HG embedding is index 0."""

    def __init__(self, n_nodes: int, in_dim: int = 1, embed_dim: int = EMBED_DIM):
        if nn is None:
            raise ImportError("torch is required for TinyGAT")
        super().__init__()
        self.query = nn.Linear(in_dim, embed_dim)
        self.key = nn.Linear(in_dim, embed_dim)
        self.val = nn.Linear(in_dim, embed_dim)
        self.head = nn.Linear(embed_dim, 1)
        self.n_nodes = n_nodes

    def embed(self, nodes: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        query = self.query(nodes)
        key = self.key(nodes)
        val = self.val(nodes)
        scores = query @ key.transpose(-1, -2) / np.sqrt(query.shape[-1])
        scores = scores.masked_fill(adj < 1e-8, -1e9)
        attn = torch.softmax(scores, dim=-1)
        return attn @ val

    def forward(self, nodes: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        hidden = self.embed(nodes, adj)
        return self.head(hidden[:, 0, :]).squeeze(-1)


def _col(df: pd.DataFrame, names: list[str]) -> str | None:
    return next((name for name in names if name in df.columns), None)


def _pack_graph(row: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    feats = []
    present = []
    for node in NODE_ORDER:
        col = _col(pd.DataFrame([row]), NODE_SERIES[node])
        value = float(row[col]) if col and pd.notna(row[col]) else 0.0
        feats.append([value])
        present.append(1.0 if col and pd.notna(row.get(col, np.nan)) else 0.0)
    nodes = np.asarray(feats, dtype=np.float32)
    present_arr = np.asarray(present, dtype=np.float32)
    adj = np.outer(present_arr, present_arr)
    np.fill_diagonal(adj, 1.0)
    return nodes, adj


def _purged_folds(n: int, embargo: int) -> list[tuple[np.ndarray, np.ndarray]]:
    folds = []
    start = TRAIN_MIN
    while start + TEST_SIZE <= n:
        test_start, test_end = start, start + TEST_SIZE
        train_end = test_start - embargo
        if train_end < 40:
            start += STEP
            continue
        folds.append((np.arange(0, train_end), np.arange(test_start, test_end)))
        start += STEP
    return folds


def _fit_logistic(x_train: np.ndarray, y_train: np.ndarray, x_test: np.ndarray) -> np.ndarray:
    if len(np.unique(y_train)) < 2:
        return np.full(len(x_test), 0.5)
    scaler = StandardScaler()
    model = LogisticRegression(max_iter=400, class_weight="balanced", random_state=42)
    model.fit(scaler.fit_transform(x_train), y_train)
    return model.predict_proba(scaler.transform(x_test))[:, 1]


def _sum_net(proba: np.ndarray, rets: np.ndarray) -> float:
    pos = np.zeros(len(proba), dtype=float)
    pos[proba >= 0.60] = 1.0
    pos[proba <= 0.40] = -1.0
    prev = np.concatenate([np.zeros(1), pos[:-1]])
    traded = np.abs(pos - prev)
    nets = pos * rets - 0.0004 * traded
    return float(np.sum(nets))


def run_hybrid(df: pd.DataFrame, survivors: list[str]) -> dict:
    if torch is None:
        return {
            "verdict": "SHELF",
            "note": "torch not importable; GAT not trained.",
            "trained": False,
        }
    label = "fwd_ret_5d"
    work = df.dropna(subset=[label, *survivors]).copy()
    work = work.loc[work[label] != 0].reset_index(drop=True)
    if len(work) < TRAIN_MIN + TEST_SIZE:
        return {"verdict": "SHELF", "note": "insufficient rows after dropna", "trained": False}
    y = (work[label].to_numpy() > 0).astype(int)
    rets = work[label].to_numpy(dtype=float)
    tabular = work[survivors].to_numpy(dtype=float)
    graphs = [_pack_graph(work.iloc[i]) for i in range(len(work))]
    embargo = 2
    folds = _purged_folds(len(work), embargo)
    tab_nets = []
    hyb_nets = []
    device = torch.device("cpu")
    for train_idx, test_idx in folds:
        tab_p = _fit_logistic(tabular[train_idx], y[train_idx], tabular[test_idx])
        tab_nets.append(_sum_net(tab_p, rets[test_idx]))
        model = TinyGAT(n_nodes=len(NODE_ORDER)).to(device)
        opt = torch.optim.Adam(model.parameters(), lr=0.03)
        x_nodes = torch.tensor(np.stack([graphs[i][0] for i in train_idx]), dtype=torch.float32)
        x_adj = torch.tensor(np.stack([graphs[i][1] for i in train_idx]), dtype=torch.float32)
        y_t = torch.tensor(y[train_idx], dtype=torch.float32)
        model.train()
        for _ in range(EPOCHS):
            opt.zero_grad()
            logit = model(x_nodes.to(device), x_adj.to(device))
            loss = nn.BCEWithLogitsLoss()(logit, y_t.to(device))
            loss.backward()
            opt.step()
        model.eval()
        with torch.no_grad():
            train_emb = model.embed(x_nodes.to(device), x_adj.to(device))[:, 0, :].cpu().numpy()
            test_nodes = torch.tensor(
                np.stack([graphs[i][0] for i in test_idx]), dtype=torch.float32
            )
            test_adj = torch.tensor(np.stack([graphs[i][1] for i in test_idx]), dtype=torch.float32)
            test_emb = model.embed(test_nodes.to(device), test_adj.to(device))[:, 0, :].cpu().numpy()
        hyb_train = np.concatenate([tabular[train_idx], train_emb], axis=1)
        hyb_test = np.concatenate([tabular[test_idx], test_emb], axis=1)
        hyb_p = _fit_logistic(hyb_train, y[train_idx], hyb_test)
        hyb_nets.append(_sum_net(hyb_p, rets[test_idx]))
    tab_sum = float(np.sum(tab_nets)) if tab_nets else 0.0
    hyb_sum = float(np.sum(hyb_nets)) if hyb_nets else 0.0
    lifted = hyb_sum > tab_sum
    return {
        "verdict": "CONTINUE" if lifted else "KILL",
        "note": (
            "GAT hybrid beat tabular survivors on costed sum_net. promote=false."
            if lifted
            else "GAT hybrid did not beat tabular survivors. Family stays tabular or SHELF."
        ),
        "trained": True,
        "n_folds": len(folds),
        "tabular_sum_net": round(tab_sum, 6),
        "hybrid_sum_net": round(hyb_sum, 6),
        "backend": "cpu",
        "epochs": EPOCHS,
        "n": int(len(work)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=banner())
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--no-yfinance", action="store_true")
    args = parser.parse_args()
    if GRAPH_FEAT_PANEL.is_file():
        featured = pd.read_parquet(GRAPH_FEAT_PANEL)
        if "date" in featured.columns:
            featured["date"] = pd.to_datetime(featured["date"])
        meta = {"source": "graph_feat_parquet", "path": str(GRAPH_FEAT_PANEL), "promote": False}
    else:
        raw, meta = load_or_build_panel(allow_yfinance=not args.no_yfinance)
        featured = emit_features(raw)
    rows = purge_graph_cols(featured)
    survivors = [row["feature"] for row in rows if row.get("survivor")]
    if not survivors:
        payload = {
            "status": "NOT_A_PROMOTE",
            "promote": False,
            "not_a_promote": NOT_A_PROMOTE,
            "experiment": "copper_gnn_hybrid",
            "verdict": "SHELF",
            "note": "No graph topology survivors. GAT not trained (plan gate).",
            "trained": False,
            "survivors": [],
            "graph_rows": rows,
            "panel": meta,
            "banner": banner(),
        }
        write_report(payload, args.output)
        return 0
    result = run_hybrid(featured, survivors)
    payload = {
        "status": "NOT_A_PROMOTE",
        "promote": False,
        "not_a_promote": NOT_A_PROMOTE,
        "experiment": "copper_gnn_hybrid",
        "survivors": survivors,
        "graph_rows": rows,
        "panel": meta,
        "banner": banner(),
        **result,
    }
    write_report(payload, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
