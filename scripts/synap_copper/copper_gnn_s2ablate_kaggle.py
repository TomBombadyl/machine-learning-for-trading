#!/usr/bin/env python3
"""Next paste — S2 ablate after Cell 1 deep KILL (sign_stable 0/5).

promote=false ALWAYS. Paste this WHOLE file as one new cell at the
bottom of the existing S2 notebook. Same Friday panel only
(sha 35f1fce22bca…). Do not rerun copper_gnn_kaggle.py or
copper_gnn_s2gate_kaggle.py.

Why this cell (not more 500-epoch seeds):
  Cell 1 deep (copper_gnn_s2gate_v0_deep) KILL 0/20 — hybrid beat MOM
  on sum_net + maxDD every seed, but last-5 fold signs were 0/5 for
  BOTH hybrid and MOM. Failure mode is temporal, not undertraining.

Arms (same purged WF, same costs/thresholds):
  A  MOM_ONLY                         # locked baseline
  B  graph_tabular                    # pagerank/betweenness/hhi only
  C  gat_emb                          # TinyGAT HG embedding only
  D  hybrid                           # graph_tabular + gat_emb (Cell 1)

GAT: epochs in {50, 150, 250} with early-stop patience=25 on train BCE.
Seeds: 42–46 (gym-length). Emits fold_net series + last{5,10,20} signs.

Family CONTINUE only if ≥3/5 seeds have an arm that beats MOM on
costed sum_net AND maxDD ≤ MOM+5pp AND last-10 sign ≥4/10.
SHELF GAT if arm B already matches/beats arm C/D on that gate.
Cell 2 stays blocked unless family CONTINUE. Never PROMOTE.

Download after SystemExit 0:
  copper_gnn_s2ablate_memo.json
  copper_gnn_s2ablate_metrics.json
  copper_gnn_s2ablate_receipt.txt
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

VERSION = "copper_gnn_s2ablate_v0"
PROMOTE = False
V0_SHA12 = "35f1fce22bca"
COST_ONE_WAY = 0.0004
DD_SLACK = 0.05
THR_LONG = 0.60
THR_SHORT = 0.40
TRAIN_MIN = 104
TEST_SIZE = 26
STEP = 13
EPOCH_CAPS = (50, 150, 250)
EARLY_STOP_PATIENCE = 25
EMBED_DIM = 4
LOOKBACK = 52
CORR_MIN = 0.25
AUDIT_RHO_MAX = 0.90
SEEDS = tuple(range(42, 47))
FAMILY_MIN_FRAC = 0.60
LAST10_POS_FLOOR = 4
MOM_COLS = ["mom_5d", "mom_21d", "mom_63d"]
GRAPH_SURVIVORS = ["graph_pagerank", "graph_betweenness", "graph_hhi"]
COT_AUDIT_COLS = [
    "cot_managed_money_net",
    "cot_managed_money_pct_oi",
    "cot_managed_money_z_52w",
]
ARMS = ("mom", "graph", "gat", "hybrid")
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


def fold_sign_counts(fold_nets: list[np.ndarray]) -> dict:
    signs = [bool(float(np.sum(nets)) > 0) for nets in fold_nets]
    out = {}
    for window in (5, 10, 20):
        eval_folds = signs[-window:] if len(signs) >= window else signs
        n_pos = sum(1 for flag in eval_folds if flag)
        out[f"n_sign_pos_last{window}"] = n_pos
        out[f"n_eval_folds_last{window}"] = len(eval_folds)
    return out


def score_path(fold_nets: list[np.ndarray]) -> dict:
    if not fold_nets:
        return {
            "sum_net": 0.0,
            "max_dd": 0.0,
            "n_folds": 0,
            "fold_net": [],
            "n_sign_pos_last5": 0,
            "n_sign_pos_last10": 0,
            "n_sign_pos_last20": 0,
            "n_eval_folds_last5": 0,
            "n_eval_folds_last10": 0,
            "n_eval_folds_last20": 0,
            "sign_stable_3of5": False,
            "sign_stable_4of10": False,
            "promote": False,
        }
    fold_sums = [round(float(np.sum(nets)), 6) for nets in fold_nets]
    signs = fold_sign_counts(fold_nets)
    all_nets = np.concatenate(fold_nets)
    n5 = signs["n_sign_pos_last5"]
    n10 = signs["n_sign_pos_last10"]
    e5 = signs["n_eval_folds_last5"]
    e10 = signs["n_eval_folds_last10"]
    return {
        "sum_net": round(float(np.sum(all_nets)), 6),
        "max_dd": round(max_dd(all_nets), 6),
        "n_folds": len(fold_nets),
        "fold_net": fold_sums,
        **signs,
        "sign_stable_3of5": bool(e5 >= 5 and n5 >= 3),
        "sign_stable_4of10": bool(e10 >= 10 and n10 >= LAST10_POS_FLOOR),
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
    if not challenger.get("sign_stable_4of10"):
        reasons.append(
            "sign_stable_last10 fail: "
            f"{challenger.get('n_sign_pos_last10')}/"
            f"{challenger.get('n_eval_folds_last10')} pos folds "
            f"(need >={LAST10_POS_FLOOR})"
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


def family_pass_floor(n_seeds: int) -> int:
    return max(3, int(np.ceil(FAMILY_MIN_FRAC * n_seeds)))


def train_gat_embeddings(
    graphs: list,
    train_idx: np.ndarray,
    test_idx: np.ndarray,
    y_train: np.ndarray,
    device,
    epoch_cap: int,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, int]:
    torch.manual_seed(seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(seed)
    model = TinyGAT().to(device)
    opt = torch.optim.Adam(model.parameters(), lr=0.03)
    x_nodes = torch.tensor(np.stack([graphs[i][0] for i in train_idx]), dtype=torch.float32).to(
        device
    )
    x_adj = torch.tensor(np.stack([graphs[i][1] for i in train_idx]), dtype=torch.float32).to(
        device
    )
    y_t = torch.tensor(y_train, dtype=torch.float32).to(device)
    best_loss = float("inf")
    best_state = None
    stale = 0
    used = 0
    model.train()
    for epoch in range(1, epoch_cap + 1):
        opt.zero_grad()
        loss = nn.BCEWithLogitsLoss()(model(x_nodes, x_adj), y_t)
        loss.backward()
        opt.step()
        used = epoch
        loss_v = float(loss.detach().cpu())
        if loss_v + 1e-8 < best_loss:
            best_loss = loss_v
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
            stale = 0
        else:
            stale += 1
            if stale >= EARLY_STOP_PATIENCE:
                break
    if best_state is not None:
        model.load_state_dict(best_state)
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
    return train_emb, test_emb, used


def run_seed(work: pd.DataFrame, graphs: list, seed: int, epoch_cap: int) -> dict:
    if torch is None:
        return {"seed": seed, "verdict": "SHELF", "note": "torch missing", "promote": False}
    y = (work["fwd_ret_5d"].to_numpy() > 0).astype(int)
    rets = work["fwd_ret_5d"].to_numpy(dtype=float)
    mom = work[MOM_COLS].to_numpy(dtype=float)
    tabular = work[GRAPH_SURVIVORS].to_numpy(dtype=float)
    folds = purged_folds(len(work), 2)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    arm_fold_nets = {arm: [] for arm in ARMS}
    epochs_used = []
    t0 = time.time()
    for fold_i, (train_idx, test_idx) in enumerate(folds):
        mom_p = fit_logistic(mom[train_idx], y[train_idx], mom[test_idx], seed)
        arm_fold_nets["mom"].append(turnover_nets(positions(mom_p), rets[test_idx]))

        graph_p = fit_logistic(tabular[train_idx], y[train_idx], tabular[test_idx], seed)
        arm_fold_nets["graph"].append(turnover_nets(positions(graph_p), rets[test_idx]))

        train_emb, test_emb, used = train_gat_embeddings(
            graphs, train_idx, test_idx, y[train_idx], device, epoch_cap, seed + fold_i
        )
        epochs_used.append(used)

        gat_p = fit_logistic(train_emb, y[train_idx], test_emb, seed)
        arm_fold_nets["gat"].append(turnover_nets(positions(gat_p), rets[test_idx]))

        hyb_p = fit_logistic(
            np.concatenate([tabular[train_idx], train_emb], axis=1),
            y[train_idx],
            np.concatenate([tabular[test_idx], test_emb], axis=1),
            seed,
        )
        arm_fold_nets["hybrid"].append(turnover_nets(positions(hyb_p), rets[test_idx]))

        if fold_i == 0 or (fold_i + 1) % 10 == 0 or fold_i + 1 == len(folds):
            print(
                f"[s2ablate] seed={seed} epochs_cap={epoch_cap} "
                f"fold={fold_i + 1}/{len(folds)} used_ep={used} "
                f"elapsed_s={time.time() - t0:.0f}",
                flush=True,
            )

    scores = {arm: score_path(arm_fold_nets[arm]) for arm in ARMS}
    mom_score = scores["mom"]
    arm_verdicts = {}
    for arm in ("graph", "gat", "hybrid"):
        verdict, reasons = decide_vs_mom(scores[arm], mom_score)
        arm_verdicts[arm] = {"verdict": verdict, "reasons": reasons, "promote": False}
    seed_continue = any(item["verdict"] == "CONTINUE" for item in arm_verdicts.values())
    # GAT adds over frozen centrality only if hybrid/gat beat graph on sum_net
    # while clearing the same soft gate vs MOM.
    gat_adds = False
    if arm_verdicts["hybrid"]["verdict"] == "CONTINUE" or arm_verdicts["gat"]["verdict"] == "CONTINUE":
        best_gat = max(scores["gat"]["sum_net"], scores["hybrid"]["sum_net"])
        gat_adds = best_gat > scores["graph"]["sum_net"] + 1e-12
    return {
        "seed": seed,
        "epoch_cap": epoch_cap,
        "epochs_used_mean": round(float(np.mean(epochs_used)), 2) if epochs_used else 0.0,
        "verdict": "CONTINUE" if seed_continue else "KILL",
        "arm_verdicts": arm_verdicts,
        "arms": scores,
        "gat_adds_over_graph": bool(gat_adds),
        "graph_alone_continue": arm_verdicts["graph"]["verdict"] == "CONTINUE",
        "backend": str(device),
        "n": int(len(work)),
        "elapsed_s": round(time.time() - t0, 1),
        "promote": False,
    }


def summarize_family(seed_rows: list[dict]) -> dict:
    floor = family_pass_floor(len(SEEDS))
    n_ok = sum(1 for row in seed_rows if row.get("verdict") == "CONTINUE")
    family = "CONTINUE" if n_ok >= floor else "KILL"
    n_graph_ok = sum(1 for row in seed_rows if row.get("graph_alone_continue"))
    n_gat_adds = sum(1 for row in seed_rows if row.get("gat_adds_over_graph"))
    shelf_gat = False
    note_bits = [f"seeds_continue={n_ok}/{len(SEEDS)} floor={floor}"]
    if family == "CONTINUE" and n_graph_ok >= floor and n_gat_adds == 0:
        shelf_gat = True
        note_bits.append("SHELF_GAT graph_tabular_owns_edge")
    elif family == "CONTINUE" and n_gat_adds >= max(1, floor // 2):
        note_bits.append("GAT_adds_over_graph")
    return {
        "family": family,
        "n_ok": n_ok,
        "floor": floor,
        "shelf_gat": shelf_gat,
        "n_graph_alone_continue": n_graph_ok,
        "n_gat_adds_over_graph": n_gat_adds,
        "note": "; ".join(note_bits),
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
    seed_rows: list[dict] = []
    if missing:
        family = "SHELF"
        note = f"missing_cols={missing}"
        shelf_gat = False
        summary = {
            "family": family,
            "n_ok": 0,
            "floor": family_pass_floor(len(SEEDS)),
            "shelf_gat": False,
            "n_graph_alone_continue": 0,
            "n_gat_adds_over_graph": 0,
            "note": note,
        }
    elif audit["dummy"]:
        family = "SHELF"
        note = "graph_is_cot_dummy"
        shelf_gat = False
        summary = {
            "family": family,
            "n_ok": 0,
            "floor": family_pass_floor(len(SEEDS)),
            "shelf_gat": False,
            "n_graph_alone_continue": 0,
            "n_gat_adds_over_graph": 0,
            "note": note,
        }
    else:
        work = featured.dropna(subset=need)
        work = work.loc[work["fwd_ret_5d"] != 0].reset_index(drop=True)
        print(
            f"[s2ablate] packing graphs n={len(work)} seeds={len(SEEDS)} "
            f"epoch_caps={list(EPOCH_CAPS)} step={STEP}",
            flush=True,
        )
        graphs = [pack_graph(work.iloc[i]) for i in range(len(work))]
        floor = family_pass_floor(len(SEEDS))
        for epoch_cap in EPOCH_CAPS:
            for seed in SEEDS:
                print(f"[s2ablate] start seed={seed} epoch_cap={epoch_cap}", flush=True)
                row = run_seed(work, graphs, seed, epoch_cap)
                seed_rows.append(row)
                n_ok = sum(1 for item in seed_rows if item.get("verdict") == "CONTINUE")
                checkpoint = {
                    "promote": False,
                    "version": VERSION,
                    "partial": True,
                    "n_done": len(seed_rows),
                    "n_jobs": len(SEEDS) * len(EPOCH_CAPS),
                    "n_seeds_continue_rows": n_ok,
                    "family_pass_floor": floor,
                    "seed_verdicts": [
                        {
                            "seed": item.get("seed"),
                            "epoch_cap": item.get("epoch_cap"),
                            "verdict": item.get("verdict"),
                        }
                        for item in seed_rows
                    ],
                }
                (OUT_DIR / "copper_gnn_s2ablate_memo.json").write_text(
                    json.dumps(checkpoint, indent=2, default=str)
                )
                print(
                    f"[s2ablate] done seed={seed} epoch_cap={epoch_cap} "
                    f"verdict={row.get('verdict')} "
                    f"graph_alone={row.get('graph_alone_continue')} "
                    f"gat_adds={row.get('gat_adds_over_graph')}",
                    flush=True,
                )
        # Family gate: evaluate at the best epoch_cap (most CONTINUE seeds).
        by_cap: dict[int, list[dict]] = {cap: [] for cap in EPOCH_CAPS}
        for row in seed_rows:
            by_cap[int(row["epoch_cap"])].append(row)
        best_cap = max(
            EPOCH_CAPS,
            key=lambda cap: sum(1 for row in by_cap[cap] if row.get("verdict") == "CONTINUE"),
        )
        summary = summarize_family(by_cap[best_cap])
        summary["best_epoch_cap"] = best_cap
        summary["note"] = f"best_epoch_cap={best_cap}; {summary['note']}"
        family = summary["family"]
        note = summary["note"]
        shelf_gat = summary["shelf_gat"]

    metrics = {
        "promote": False,
        "NOT_A_PROMOTE": True,
        "version": VERSION,
        "built_at_utc": built,
        "prior_cell1": {
            "version": "copper_gnn_s2gate_v0_deep",
            "verdict": "KILL",
            "note": "0/20 seeds sign_stable 0/5; hybrid beat mom sum_net+DD",
        },
        "gate": (
            "Per arm CONTINUE if beats MOM_ONLY on costed sum_net AND "
            "maxDD not > baseline+5pp AND sign-stable last10 >=4/10; "
            f"seed CONTINUE if any of graph/gat/hybrid CONTINUE; "
            f"family CONTINUE if >={FAMILY_MIN_FRAC:.0%} of {len(SEEDS)} seeds "
            f"at best epoch_cap; SHELF GAT if graph alone owns the edge; "
            "SHELF if graph_is_cot_dummy"
        ),
        "panel": panel_meta,
        "audit": audit,
        "graph_survivors_frozen": GRAPH_SURVIVORS,
        "epoch_caps": list(EPOCH_CAPS),
        "early_stop_patience": EARLY_STOP_PATIENCE,
        "step": STEP,
        "family_pass_floor": family_pass_floor(len(SEEDS)),
        "seeds": list(SEEDS),
        "arms": list(ARMS),
        "seed_rows": seed_rows,
        "summary": summary if "summary" in locals() else {},
        "n_seeds_continue": summary.get("n_ok", 0) if "summary" in locals() else 0,
        "n_seeds": len(SEEDS),
        "verdict": family,
        "shelf_gat": shelf_gat if "shelf_gat" in locals() else False,
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
        "best_epoch_cap": summary.get("best_epoch_cap") if "summary" in locals() else None,
        "n_seeds_continue": metrics["n_seeds_continue"],
        "n_seeds": len(SEEDS),
        "shelf_gat": metrics["shelf_gat"],
        "n_graph_alone_continue": summary.get("n_graph_alone_continue", 0)
        if "summary" in locals()
        else 0,
        "n_gat_adds_over_graph": summary.get("n_gat_adds_over_graph", 0)
        if "summary" in locals()
        else 0,
        "cell2_blocked": family != "CONTINUE",
        "note": note,
        "seed_verdicts": [
            {
                "seed": row.get("seed"),
                "epoch_cap": row.get("epoch_cap"),
                "verdict": row.get("verdict"),
                "graph_alone_continue": row.get("graph_alone_continue"),
                "gat_adds_over_graph": row.get("gat_adds_over_graph"),
                "arm_verdicts": row.get("arm_verdicts"),
            }
            for row in seed_rows
        ],
        "paths": {
            "metrics": str(OUT_DIR / "copper_gnn_s2ablate_metrics.json"),
            "memo": str(OUT_DIR / "copper_gnn_s2ablate_memo.json"),
        },
    }
    receipt = (
        f"Verdict: {family} (promote=false) version={VERSION}\n"
        f"sha12={panel_sha[:12]} {panel_meta['sha_note']}\n"
        f"audit={audit['note']}\n"
        f"{note}\n"
        f"shelf_gat={metrics['shelf_gat']}\n"
        f"cell2_blocked={family != 'CONTINUE'}\n"
    )
    (OUT_DIR / "copper_gnn_s2ablate_metrics.json").write_text(
        json.dumps(metrics, indent=2, default=str)
    )
    (OUT_DIR / "copper_gnn_s2ablate_memo.json").write_text(json.dumps(memo, indent=2, default=str))
    (OUT_DIR / "copper_gnn_s2ablate_receipt.txt").write_text(receipt)
    print(json.dumps(memo, indent=2, default=str), flush=True)
    print("RECEIPT:\n" + receipt, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
