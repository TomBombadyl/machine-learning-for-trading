#!/usr/bin/env python3
"""Cell 1 — TinyGAT hybrid vs MOM_ONLY under the S2 gate.

promote=false ALWAYS.

STAMPED 2026-09-20: copper_gnn_s2gate_v0_deep = KILL (0/20 seeds,
sign_stable 0/5 for hybrid AND MOM; hybrid still beat MOM sum_net+DD).
Do NOT rerun this file. Next paste is copper_gnn_s2ablate_kaggle.py.

Historical deep Cell 1 contract (already executed):
  20 seeds (42–61), 500 epochs/fold, step=13. Family CONTINUE if ≥60%
  of seeds beat MOM on costed sum_net AND maxDD ≤ MOM+5pp AND last-5
  fold sign ≥3/5. SHELF if graph topology is a COT dummy (|ρ|>0.90).
  Never PROMOTE. Cell 2 stays blocked unless this family is CONTINUE.

Download after SystemExit 0 (legacy):
  copper_gnn_s2gate_memo.json
  copper_gnn_s2gate_metrics.json
  copper_gnn_s2gate_receipt.txt
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

try:
    import torch
    from torch import nn
except ImportError:
    torch = None
    nn = None

VERSION = "copper_gnn_s2gate_v0_deep"
PROMOTE = False
V0_SHA12 = "35f1fce22bca"
COST_ONE_WAY = 0.0004
DD_SLACK = 0.05
THR_LONG = 0.60
THR_SHORT = 0.40
TRAIN_MIN = 104
TEST_SIZE = 26
STEP = 13
EPOCHS = 500
EMBED_DIM = 4
LOOKBACK = 52
CORR_MIN = 0.25
AUDIT_RHO_MAX = 0.90
SEEDS = tuple(range(42, 62))
FAMILY_MIN_FRAC = 0.60
MOM_COLS = ["mom_5d", "mom_21d", "mom_63d"]
GRAPH_SURVIVORS = ["graph_pagerank", "graph_betweenness", "graph_hhi"]
COT_AUDIT_COLS = [
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
NODE_ORDER = list(SERIES)
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


def fit_logistic(x_train, y_train, x_test, seed: int):
    if len(np.unique(y_train)) < 2:
        return np.full(len(x_test), 0.5)
    scaler = StandardScaler()
    model = LogisticRegression(max_iter=400, class_weight="balanced", random_state=seed)
    model.fit(scaler.fit_transform(x_train), y_train)
    return model.predict_proba(scaler.transform(x_test))[:, 1]


def positions(proba: np.ndarray) -> np.ndarray:
    pos = np.zeros(len(proba), dtype=float)
    pos[proba >= THR_LONG] = 1.0
    pos[proba <= THR_SHORT] = -1.0
    return pos


def turnover_nets(pos: np.ndarray, rets: np.ndarray) -> np.ndarray:
    prev = np.concatenate([np.zeros(1, dtype=float), pos[:-1]])
    return pos * rets - COST_ONE_WAY * np.abs(pos - prev)


def max_dd(nets: np.ndarray) -> float:
    if len(nets) == 0:
        return 0.0
    equity = np.cumsum(nets)
    peak = np.maximum.accumulate(equity)
    return float(np.max(peak - equity))


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


def audit_graph_vs_cot(df: pd.DataFrame) -> dict:
    rows = []
    dummy = False
    for graph_col in GRAPH_SURVIVORS:
        if graph_col not in df.columns:
            continue
        for cot_col in COT_AUDIT_COLS:
            if cot_col not in df.columns:
                continue
            both = df[[graph_col, cot_col]].dropna()
            rho = (
                spearman(both[graph_col].to_numpy(), both[cot_col].to_numpy())
                if len(both) >= 12
                else float("nan")
            )
            hit = bool(np.isfinite(rho) and abs(rho) > AUDIT_RHO_MAX)
            dummy = dummy or hit
            rows.append(
                {
                    "graph": graph_col,
                    "cot": cot_col,
                    "n": int(len(both)),
                    "spearman": None if not np.isfinite(rho) else round(float(rho), 4),
                    "dummy": hit,
                    "promote": False,
                }
            )
    return {
        "dummy": dummy,
        "abs_rho_max": AUDIT_RHO_MAX,
        "rows": rows,
        "note": "graph_is_cot_dummy" if dummy else "graph_not_redundant_vs_cot",
    }


def score_path(fold_nets: list[np.ndarray]) -> dict:
    if not fold_nets:
        return {
            "sum_net": 0.0,
            "max_dd": 0.0,
            "n_folds": 0,
            "n_sign_pos_last5": 0,
            "n_eval_folds": 0,
            "sign_stable_3of5": False,
        }
    signs = [bool(float(np.sum(nets)) > 0) for nets in fold_nets]
    eval_folds = signs[-5:] if len(signs) >= 5 else signs
    n_pos = sum(1 for flag in eval_folds if flag)
    if len(eval_folds) >= 5:
        sign_stable = n_pos >= 3
    else:
        sign_stable = n_pos >= 3 and n_pos / max(len(eval_folds), 1) >= 0.6
    all_nets = np.concatenate(fold_nets)
    return {
        "sum_net": round(float(np.sum(all_nets)), 6),
        "max_dd": round(max_dd(all_nets), 6),
        "n_folds": len(fold_nets),
        "n_sign_pos_last5": n_pos,
        "n_eval_folds": len(eval_folds),
        "sign_stable_3of5": bool(sign_stable),
        "promote": False,
    }


def family_pass_floor(n_seeds: int) -> int:
    return max(3, int(np.ceil(FAMILY_MIN_FRAC * n_seeds)))


def run_seed(work: pd.DataFrame, graphs: list, seed: int) -> dict:
    if torch is None:
        return {"seed": seed, "verdict": "SHELF", "note": "torch missing", "promote": False}
    y = (work["fwd_ret_5d"].to_numpy() > 0).astype(int)
    rets = work["fwd_ret_5d"].to_numpy(dtype=float)
    mom = work[MOM_COLS].to_numpy(dtype=float)
    tabular = work[GRAPH_SURVIVORS].to_numpy(dtype=float)
    folds = purged_folds(len(work), 2)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    torch.manual_seed(seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(seed)
    mom_fold_nets = []
    hyb_fold_nets = []
    t0 = time.time()
    for fold_i, (train_idx, test_idx) in enumerate(folds):
        mom_p = fit_logistic(mom[train_idx], y[train_idx], mom[test_idx], seed)
        mom_fold_nets.append(turnover_nets(positions(mom_p), rets[test_idx]))
        model = TinyGAT().to(device)
        opt = torch.optim.Adam(model.parameters(), lr=0.03)
        x_nodes = torch.tensor(np.stack([graphs[i][0] for i in train_idx]), dtype=torch.float32).to(
            device
        )
        x_adj = torch.tensor(np.stack([graphs[i][1] for i in train_idx]), dtype=torch.float32).to(
            device
        )
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
        hyb_p = fit_logistic(
            np.concatenate([tabular[train_idx], train_emb], axis=1),
            y[train_idx],
            np.concatenate([tabular[test_idx], test_emb], axis=1),
            seed,
        )
        hyb_fold_nets.append(turnover_nets(positions(hyb_p), rets[test_idx]))
        if fold_i == 0 or (fold_i + 1) % 10 == 0 or fold_i + 1 == len(folds):
            print(
                f"[s2gate] seed={seed} fold={fold_i + 1}/{len(folds)} "
                f"elapsed_s={time.time() - t0:.0f}",
                flush=True,
            )
    mom_score = score_path(mom_fold_nets)
    hyb_score = score_path(hyb_fold_nets)
    verdict, reasons = decide_vs_mom(hyb_score, mom_score)
    return {
        "seed": seed,
        "verdict": verdict,
        "reasons": reasons,
        "mom": mom_score,
        "hybrid": hyb_score,
        "backend": str(device),
        "epochs": EPOCHS,
        "n": int(len(work)),
        "elapsed_s": round(time.time() - t0, 1),
        "promote": False,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel_path = resolve_panel()
    panel_sha = sha256_file(panel_path)
    df = pd.read_parquet(panel_path)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
    featured = emit_features(df)
    audit = audit_graph_vs_cot(featured)
    need = ["fwd_ret_5d", *MOM_COLS, *GRAPH_SURVIVORS]
    missing = [col for col in need if col not in featured.columns]
    built = datetime.now(timezone.utc).isoformat()
    panel_meta = {
        "path": str(panel_path),
        "sha256": panel_sha,
        "sha_note": "matches_v0" if panel_sha.startswith(V0_SHA12) else "sha_changed",
        "shape": list(df.shape),
        "promote": False,
    }
    if missing:
        family = "SHELF"
        note = f"missing_cols={missing}"
        seed_rows = []
    elif audit["dummy"]:
        family = "SHELF"
        note = "graph_is_cot_dummy"
        seed_rows = []
    else:
        work = featured.dropna(subset=need)
        work = work.loc[work["fwd_ret_5d"] != 0].reset_index(drop=True)
        print(
            f"[s2gate] packing graphs n={len(work)} seeds={len(SEEDS)} "
            f"epochs={EPOCHS} step={STEP}",
            flush=True,
        )
        graphs = [pack_graph(work.iloc[i]) for i in range(len(work))]
        seed_rows = []
        floor = family_pass_floor(len(SEEDS))
        for seed in SEEDS:
            print(f"[s2gate] start seed={seed}", flush=True)
            row = run_seed(work, graphs, seed)
            seed_rows.append(row)
            n_ok = sum(1 for item in seed_rows if item.get("verdict") == "CONTINUE")
            checkpoint = {
                "promote": False,
                "version": VERSION,
                "partial": True,
                "n_done": len(seed_rows),
                "n_seeds": len(SEEDS),
                "n_seeds_continue": n_ok,
                "family_pass_floor": floor,
                "seed_verdicts": [
                    {"seed": item.get("seed"), "verdict": item.get("verdict")}
                    for item in seed_rows
                ],
            }
            (OUT_DIR / "copper_gnn_s2gate_memo.json").write_text(
                json.dumps(checkpoint, indent=2, default=str)
            )
            print(
                f"[s2gate] done seed={seed} verdict={row.get('verdict')} "
                f"running={n_ok}/{len(seed_rows)} floor={floor}",
                flush=True,
            )
        n_ok = sum(1 for row in seed_rows if row.get("verdict") == "CONTINUE")
        family = "CONTINUE" if n_ok >= floor else "KILL"
        note = f"seeds_continue={n_ok}/{len(SEEDS)} floor={floor}"
    metrics = {
        "promote": False,
        "NOT_A_PROMOTE": True,
        "version": VERSION,
        "built_at_utc": built,
        "gate": (
            "CONTINUE if hybrid beats MOM_ONLY on costed sum_net AND "
            "maxDD not > baseline+5pp AND sign-stable >=3/5 last folds; "
            f"family CONTINUE if >={FAMILY_MIN_FRAC:.0%} of {len(SEEDS)} seeds; "
            "SHELF if graph_is_cot_dummy"
        ),
        "panel": panel_meta,
        "audit": audit,
        "graph_survivors_frozen": GRAPH_SURVIVORS,
        "epochs": EPOCHS,
        "step": STEP,
        "family_pass_floor": family_pass_floor(len(SEEDS)),
        "seeds": list(SEEDS),
        "seed_rows": seed_rows,
        "n_seeds_continue": sum(1 for row in seed_rows if row.get("verdict") == "CONTINUE"),
        "n_seeds": len(SEEDS),
        "verdict": family,
        "cell2_blocked": family != "CONTINUE",
        "note": note,
    }
    memo = {
        "verdict": family,
        "promote": False,
        "version": VERSION,
        "panel_sha12": panel_sha[:12],
        "sha_note": panel_meta["sha_note"],
        "audit_note": audit["note"],
        "n_seeds_continue": metrics["n_seeds_continue"],
        "n_seeds": len(SEEDS),
        "cell2_blocked": family != "CONTINUE",
        "note": note,
        "seed_verdicts": [
            {"seed": row.get("seed"), "verdict": row.get("verdict"), "reasons": row.get("reasons")}
            for row in seed_rows
        ],
        "paths": {
            "metrics": str(OUT_DIR / "copper_gnn_s2gate_metrics.json"),
            "memo": str(OUT_DIR / "copper_gnn_s2gate_memo.json"),
        },
    }
    receipt = (
        f"Verdict: {family} (promote=false) version={VERSION}\n"
        f"sha12={panel_sha[:12]} {panel_meta['sha_note']}\n"
        f"audit={audit['note']}\n"
        f"{note}\n"
        f"cell2_blocked={family != 'CONTINUE'}\n"
    )
    (OUT_DIR / "copper_gnn_s2gate_metrics.json").write_text(
        json.dumps(metrics, indent=2, default=str)
    )
    (OUT_DIR / "copper_gnn_s2gate_memo.json").write_text(json.dumps(memo, indent=2, default=str))
    (OUT_DIR / "copper_gnn_s2gate_receipt.txt").write_text(receipt)
    print(json.dumps(memo, indent=2, default=str), flush=True)
    print("RECEIPT:\n" + receipt, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
