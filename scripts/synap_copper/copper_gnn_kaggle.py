#!/usr/bin/env python3
"""Copper Experiment A + graph feats + gated GAT — one Kaggle cell.

promote=false ALWAYS. Paste this WHOLE file as one cell. Same Friday
panel as S2 (sha 35f1fce22bca…). GAT trains only if graph topology
columns survive IC→purge.

Download after SystemExit 0:
  copper_gnn_memo.json
  copper_gnn_metrics.json
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

try:
    import torch
    from torch import nn
except ImportError:
    torch = None
    nn = None

VERSION = "copper_gnn_kaggle_v0"
PROMOTE = False
V0_SHA12 = "35f1fce22bca"
HORIZON = 5
IC_ABS_MIN = 0.03
T_ABS_MIN = 1.64
MOM_CORR_MAX = 0.90
MIN_OBS = 80
LOOKBACK = 52
CORR_MIN = 0.25
TRAIN_MIN = 104
TEST_SIZE = 26
STEP = 26
EPOCHS = 20
EMBED_DIM = 4
MOM_COLS = ["mom_5d", "mom_21d", "mom_63d"]
COT_COLS = [
    "cot_managed_money_net",
    "cot_managed_money_pct_oi",
    "cot_managed_money_net_chg_1w",
    "cot_managed_money_z_52w",
]
GRAPH_COLS = [
    "graph_degree",
    "graph_pagerank",
    "graph_betweenness",
    "graph_hhi",
    "graph_n_nodes",
    "graph_n_edges",
]
SERIES = {
    "HG": ["ret_hg", "mom_5d"],
    "CPER": ["ret_cper", "cper_mom_21d"],
    "COPX": ["ret_copx", "copx_mom_21d"],
    "FCX": ["ret_fcx", "fcx_mom_63d"],
    "COT_MM": ["cot_managed_money_net_chg_1w", "cot_managed_money_net"],
    "SHFE_WH": ["shfe_warrant_pct_chg_21d", "shfe_warrant_chg_21d"],
}
NODE_ORDER = list(SERIES)
PROXY_EDGES = (("CPER", "HG"), ("COPX", "HG"), ("FCX", "HG"))
PANEL_CANDIDATES = [
    Path("/kaggle/input/datasets/synapgarden/synap-finpredict-panels-v0/deep_test_friday_panel_v0.parquet"),
    Path("/kaggle/input/synap-finpredict-panels-v0/deep_test_friday_panel_v0.parquet"),
]
OUT_DIR = Path("/kaggle/working") if Path("/kaggle/working").exists() else Path("data/synap/copper/docs")


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
    raise FileNotFoundError("deep_test_friday_panel_v0.parquet not found")


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    mask = np.isfinite(x) & np.isfinite(y)
    if int(mask.sum()) < 12:
        return float("nan")
    corr, _ = spearmanr(x[mask], y[mask])
    return float(corr)


def newey_west_t(values: np.ndarray, lags: int) -> float:
    series = np.asarray(values, dtype=float)
    series = series[np.isfinite(series)]
    n = len(series)
    if n < 8:
        return float("nan")
    mean = float(np.mean(series))
    centered = series - mean
    var = float(np.dot(centered, centered) / n)
    max_lag = max(1, min(int(lags), n - 2))
    for lag in range(1, max_lag + 1):
        weight = 1.0 - lag / (max_lag + 1)
        gamma = float(np.dot(centered[lag:], centered[:-lag]) / n)
        var += 2.0 * weight * gamma
    se = np.sqrt(max(var, 1e-18) / n)
    return float(mean / se)


def expanding_ic(feature: pd.Series, label: pd.Series, embargo: int) -> np.ndarray:
    feat = feature.to_numpy(dtype=float)
    lab = label.to_numpy(dtype=float)
    start = max(MIN_OBS, 52)
    values = [
        spearman(feat[:end], lab[:end]) for end in range(start, len(feat) - embargo)
    ]
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
            mom_corr = spearman(both[col].to_numpy(), both["mom_21d"].to_numpy())
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
        "sign_stable": sign_stable,
        "survivor": not reasons,
        "kill_reasons": reasons,
        "promote": False,
    }


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
        "graph_n_nodes": int(graph.number_of_nodes()),
        "graph_n_edges": int(graph.number_of_edges()),
        "graph_degree": int(graph.degree("HG")) if "HG" in graph else 0,
        "graph_pagerank": float(pagerank.get("HG", 0.0)),
        "graph_betweenness": float(between.get("HG", 0.0)),
        "graph_hhi": hhi(hg_weights),
    }


def emit_features(df: pd.DataFrame) -> pd.DataFrame:
    work = df.reset_index(drop=True)
    feats = pd.DataFrame([snapshot_features(work, loc) for loc in range(len(work))])
    return pd.concat([work, feats], axis=1)


class TinyGAT(nn.Module if nn is not None else object):
    def __init__(self, in_dim: int = 1, embed_dim: int = EMBED_DIM):
        if nn is None:
            raise ImportError("torch required")
        super().__init__()
        self.query = nn.Linear(in_dim, embed_dim)
        self.key = nn.Linear(in_dim, embed_dim)
        self.val = nn.Linear(in_dim, embed_dim)
        self.head = nn.Linear(embed_dim, 1)

    def embed(self, nodes, adj):
        query = self.query(nodes)
        key = self.key(nodes)
        val = self.val(nodes)
        scores = query @ key.transpose(-1, -2) / np.sqrt(query.shape[-1])
        scores = scores.masked_fill(adj < 1e-8, -1e9)
        return torch.softmax(scores, dim=-1) @ val

    def forward(self, nodes, adj):
        return self.head(self.embed(nodes, adj)[:, 0, :]).squeeze(-1)


def pack_graph(row: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    feats = []
    present = []
    for node in NODE_ORDER:
        col = first_present(pd.DataFrame([row]), SERIES[node])
        ok = bool(col and pd.notna(row.get(col, np.nan)))
        feats.append([float(row[col]) if ok else 0.0])
        present.append(1.0 if ok else 0.0)
    nodes = np.asarray(feats, dtype=np.float32)
    present_arr = np.asarray(present, dtype=np.float32)
    adj = np.outer(present_arr, present_arr)
    np.fill_diagonal(adj, 1.0)
    return nodes, adj


def purged_folds(n: int, embargo: int):
    folds = []
    start = TRAIN_MIN
    while start + TEST_SIZE <= n:
        test_start = start
        train_end = test_start - embargo
        if train_end >= 40:
            folds.append((np.arange(0, train_end), np.arange(test_start, test_start + TEST_SIZE)))
        start += STEP
    return folds


def fit_logistic(x_train, y_train, x_test):
    if len(np.unique(y_train)) < 2:
        return np.full(len(x_test), 0.5)
    scaler = StandardScaler()
    model = LogisticRegression(max_iter=400, class_weight="balanced", random_state=42)
    model.fit(scaler.fit_transform(x_train), y_train)
    return model.predict_proba(scaler.transform(x_test))[:, 1]


def sum_net(proba, rets):
    pos = np.zeros(len(proba), dtype=float)
    pos[proba >= 0.60] = 1.0
    pos[proba <= 0.40] = -1.0
    prev = np.concatenate([np.zeros(1), pos[:-1]])
    return float(np.sum(pos * rets - 0.0004 * np.abs(pos - prev)))


def run_hybrid(df: pd.DataFrame, survivors: list[str]) -> dict:
    if torch is None:
        return {"verdict": "SHELF", "note": "torch missing", "trained": False}
    work = df.dropna(subset=["fwd_ret_5d", *survivors])
    work = work.loc[work["fwd_ret_5d"] != 0].reset_index(drop=True)
    if len(work) < TRAIN_MIN + TEST_SIZE:
        return {"verdict": "SHELF", "note": "insufficient rows", "trained": False}
    y = (work["fwd_ret_5d"].to_numpy() > 0).astype(int)
    rets = work["fwd_ret_5d"].to_numpy(dtype=float)
    tabular = work[survivors].to_numpy(dtype=float)
    graphs = [pack_graph(work.iloc[i]) for i in range(len(work))]
    folds = purged_folds(len(work), 2)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tab_nets, hyb_nets = [], []
    for train_idx, test_idx in folds:
        tab_nets.append(
            sum_net(fit_logistic(tabular[train_idx], y[train_idx], tabular[test_idx]), rets[test_idx])
        )
        model = TinyGAT().to(device)
        opt = torch.optim.Adam(model.parameters(), lr=0.03)
        x_nodes = torch.tensor(np.stack([graphs[i][0] for i in train_idx]), dtype=torch.float32).to(device)
        x_adj = torch.tensor(np.stack([graphs[i][1] for i in train_idx]), dtype=torch.float32).to(device)
        y_t = torch.tensor(y[train_idx], dtype=torch.float32).to(device)
        model.train()
        for _ in range(EPOCHS):
            opt.zero_grad()
            loss = nn.BCEWithLogitsLoss()(model(x_nodes, x_adj), y_t)
            loss.backward()
            opt.step()
        model.eval()
        with torch.no_grad():
            train_emb = model.embed(x_nodes, x_adj)[:, 0, :].cpu().numpy()
            test_nodes = torch.tensor(
                np.stack([graphs[i][0] for i in test_idx]), dtype=torch.float32
            ).to(device)
            test_adj = torch.tensor(
                np.stack([graphs[i][1] for i in test_idx]), dtype=torch.float32
            ).to(device)
            test_emb = model.embed(test_nodes, test_adj)[:, 0, :].cpu().numpy()
        hyb_nets.append(
            sum_net(
                fit_logistic(
                    np.concatenate([tabular[train_idx], train_emb], axis=1),
                    y[train_idx],
                    np.concatenate([tabular[test_idx], test_emb], axis=1),
                ),
                rets[test_idx],
            )
        )
    tab_sum = float(np.sum(tab_nets)) if tab_nets else 0.0
    hyb_sum = float(np.sum(hyb_nets)) if hyb_nets else 0.0
    lifted = hyb_sum > tab_sum
    return {
        "verdict": "CONTINUE" if lifted else "KILL",
        "note": "GAT hybrid beat tabular on costed sum_net."
        if lifted
        else "GAT hybrid lost to tabular survivors.",
        "trained": True,
        "n_folds": len(folds),
        "tabular_sum_net": round(tab_sum, 6),
        "hybrid_sum_net": round(hyb_sum, 6),
        "backend": str(device),
        "epochs": EPOCHS,
        "n": int(len(work)),
        "promote": False,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel_path = resolve_panel()
    panel_sha = sha256_file(panel_path)
    df = pd.read_parquet(panel_path)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    embargo = max(2, (HORIZON + 4) // 5)
    exp_a = [screen_feature(df, col, "fwd_ret_5d", embargo) for col in MOM_COLS + COT_COLS if col in df.columns]
    cot_survivors = [row["feature"] for row in exp_a if row["survivor"] and row["feature"] in COT_COLS]
    featured = emit_features(df)
    graph_rows = [
        screen_feature(featured, col, "fwd_ret_5d", embargo)
        for col in GRAPH_COLS
        if col in featured.columns
    ]
    graph_survivors = [row["feature"] for row in graph_rows if row["survivor"]]
    gnn = (
        run_hybrid(featured, graph_survivors)
        if graph_survivors
        else {
            "verdict": "SHELF",
            "note": "No graph topology survivors. GAT not trained.",
            "trained": False,
            "promote": False,
        }
    )
    built = datetime.now(timezone.utc).isoformat()
    metrics = {
        "promote": False,
        "NOT_A_PROMOTE": True,
        "version": VERSION,
        "built_at_utc": built,
        "panel": {
            "path": str(panel_path),
            "sha256": panel_sha,
            "sha_note": "matches_v0" if panel_sha.startswith(V0_SHA12) else "sha_changed",
            "shape": list(df.shape),
        },
        "experiment_a": {
            "verdict": "CONTINUE" if cot_survivors else "SHELF",
            "cot_survivors": cot_survivors,
            "rows": exp_a,
        },
        "graph_features": {
            "verdict": "CONTINUE" if graph_survivors else "SHELF",
            "survivors": graph_survivors,
            "rows": graph_rows,
        },
        "gnn": gnn,
        "verdict": gnn.get("verdict", "SHELF"),
    }
    memo = {
        "verdict": metrics["verdict"],
        "promote": False,
        "version": VERSION,
        "experiment_a": metrics["experiment_a"]["verdict"],
        "cot_survivors": cot_survivors,
        "graph_survivors": graph_survivors,
        "gnn_trained": bool(gnn.get("trained")),
        "gnn": {key: gnn[key] for key in gnn if key != "note"} | {"note": gnn.get("note")},
        "panel_sha12": panel_sha[:12],
        "paths": {
            "metrics": str(OUT_DIR / "copper_gnn_metrics.json"),
            "memo": str(OUT_DIR / "copper_gnn_memo.json"),
        },
    }
    (OUT_DIR / "copper_gnn_metrics.json").write_text(json.dumps(metrics, indent=2, default=str))
    (OUT_DIR / "copper_gnn_memo.json").write_text(json.dumps(memo, indent=2, default=str))
    receipt = (
        f"Verdict: {metrics['verdict']} (promote=false) version={VERSION}\n"
        f"A: {metrics['experiment_a']['verdict']} cot={cot_survivors}\n"
        f"Graph: {metrics['graph_features']['verdict']} survivors={graph_survivors}\n"
        f"GNN: trained={gnn.get('trained')} {gnn.get('note')}\n"
    )
    (OUT_DIR / "copper_gnn_receipt.txt").write_text(receipt)
    print(json.dumps(memo, indent=2, default=str), flush=True)
    print("RECEIPT:\n" + receipt, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
