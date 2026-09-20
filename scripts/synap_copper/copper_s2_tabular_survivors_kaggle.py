#!/usr/bin/env python3
"""Fresh paste — S2 tabular survivors (no GAT). Learning from GNN KILLs.

promote=false ALWAYS. Paste this WHOLE file as one new cell on the
existing S2 notebook. Same Friday panel (sha 35f1fce22bca…).

Closed (do not rerun):
  copper_gnn_kaggle.py / copper_gnn_s2gate / copper_gnn_s2ablate
  deep_test_s2_wf_v0 / v1 / XGB-RF

What we learned:
  - TinyGAT fails the S2 temporal gate (deep 0/20, ablate 0/5).
  - Graph IC survivors still exist (pagerank / betweenness / hhi).
  - COT managed-money trio survived Experiment A.
  - S2 v1 CONTINUE is shortlist_log_h5 (logistic). Use v1 WF geometry
    (step=26, last-5 ≥3/5), not ablate step=13 / last-10 soft gate.

Arms (logistic only, fwd_ret_5d):
  A  MOM_ONLY
  B  shortlist          # v1 passer feats: mom + cper_mom_21d + fcx_mom_63d
  C  shortlist_graph    # + frozen graph survivors
  D  shortlist_graph_cot  # + COT survivors

Seeds 42–46. Family CONTINUE if ≥3/5 seeds have any of B/C/D CONTINUE
vs MOM. Never PROMOTE. No Cell 2 / no GAT.

Download after SystemExit 0:
  copper_s2_tabular_survivors_memo.json
  copper_s2_tabular_survivors_metrics.json
  copper_s2_tabular_survivors_receipt.txt
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

VERSION = "copper_s2_tabular_survivors_v0"
PROMOTE = False
V0_SHA12 = "35f1fce22bca"
COST_ONE_WAY = 0.0004
DD_SLACK = 0.05
THR_LONG = 0.60
THR_SHORT = 0.40
TRAIN_MIN = 104
TEST_SIZE = 26
STEP = 26  # v1 geometry (not ablate step=13)
LOOKBACK = 52
CORR_MIN = 0.25
SEEDS = tuple(range(42, 47))
FAMILY_MIN_FRAC = 0.60
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
    model = LogisticRegression(max_iter=800, class_weight="balanced", random_state=seed)
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


def run_seed(work: pd.DataFrame, arms: dict[str, list[str]], seed: int) -> dict:
    y = (work["fwd_ret_5d"].to_numpy() > 0).astype(int)
    rets = work["fwd_ret_5d"].to_numpy(dtype=float)
    folds = purged_folds(len(work), embargo=2)
    arm_fold_nets = {name: [] for name in arms}
    t0 = time.time()
    for fold_i, (train_idx, test_idx) in enumerate(folds):
        for name, cols in arms.items():
            x = work[cols].to_numpy(dtype=float)
            proba = fit_logistic(x[train_idx], y[train_idx], x[test_idx], seed)
            arm_fold_nets[name].append(turnover_nets(positions(proba), rets[test_idx]))
        if fold_i == 0 or (fold_i + 1) % 5 == 0 or fold_i + 1 == len(folds):
            print(
                f"[s2tab] seed={seed} fold={fold_i + 1}/{len(folds)} "
                f"elapsed_s={time.time() - t0:.0f}",
                flush=True,
            )
    scores = {name: score_path(nets) for name, nets in arm_fold_nets.items()}
    mom = scores["mom"]
    arm_verdicts = {}
    for name in arms:
        if name == "mom":
            continue
        verdict, reasons = decide_vs_mom(scores[name], mom)
        arm_verdicts[name] = {"verdict": verdict, "reasons": reasons, "promote": False}
    seed_continue = any(item["verdict"] == "CONTINUE" for item in arm_verdicts.values())
    best_arm = None
    best_sum = float("-inf")
    for name, score in scores.items():
        if name == "mom":
            continue
        if arm_verdicts[name]["verdict"] == "CONTINUE" and score["sum_net"] > best_sum:
            best_sum = score["sum_net"]
            best_arm = name
    return {
        "seed": seed,
        "verdict": "CONTINUE" if seed_continue else "KILL",
        "best_continue_arm": best_arm,
        "arm_verdicts": arm_verdicts,
        "arms": scores,
        "n": int(len(work)),
        "n_folds": len(folds),
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
    featured = emit_graph_features(df)
    mom_cols = present_cols(featured, MOM_COLS)
    shortlist = present_cols(featured, MOM_COLS + SHORTLIST_EXTRA)
    graph_cols = present_cols(featured, GRAPH_SURVIVORS)
    cot_cols = present_cols(featured, COT_SURVIVORS)
    arms = {
        "mom": mom_cols,
        "shortlist": shortlist,
        "shortlist_graph": list(dict.fromkeys(shortlist + graph_cols)),
        "shortlist_graph_cot": list(dict.fromkeys(shortlist + graph_cols + cot_cols)),
    }
    need = ["fwd_ret_5d", *set(col for cols in arms.values() for col in cols)]
    missing_core = [col for col in ["fwd_ret_5d", *MOM_COLS] if col not in featured.columns]
    built = datetime.now(timezone.utc).isoformat()
    panel_meta = {
        "path": str(panel_path),
        "sha256": panel_sha,
        "sha_note": "matches_v0" if panel_sha.startswith(V0_SHA12) else "sha_changed",
        "shape": list(df.shape),
        "promote": False,
    }
    seed_rows: list[dict] = []
    if missing_core or not mom_cols or not shortlist:
        family = "SHELF"
        note = f"missing_core={missing_core} mom={mom_cols} shortlist={shortlist}"
    else:
        work = featured.dropna(subset=need)
        work = work.loc[work["fwd_ret_5d"] != 0].reset_index(drop=True)
        print(
            f"[s2tab] n={len(work)} seeds={len(SEEDS)} step={STEP} "
            f"arm_sizes={ {key: len(val) for key, val in arms.items()} } "
            f"graph={graph_cols} cot={cot_cols}",
            flush=True,
        )
        floor = family_pass_floor(len(SEEDS))
        for seed in SEEDS:
            print(f"[s2tab] start seed={seed}", flush=True)
            row = run_seed(work, arms, seed)
            seed_rows.append(row)
            n_ok = sum(1 for item in seed_rows if item.get("verdict") == "CONTINUE")
            (OUT_DIR / "copper_s2_tabular_survivors_memo.json").write_text(
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
                                "best_continue_arm": item.get("best_continue_arm"),
                            }
                            for item in seed_rows
                        ],
                    },
                    indent=2,
                    default=str,
                )
            )
            print(
                f"[s2tab] done seed={seed} verdict={row.get('verdict')} "
                f"best={row.get('best_continue_arm')} "
                f"running={n_ok}/{len(seed_rows)} floor={floor}",
                flush=True,
            )
        n_ok = sum(1 for row in seed_rows if row.get("verdict") == "CONTINUE")
        family = "CONTINUE" if n_ok >= floor else "KILL"
        note = f"seeds_continue={n_ok}/{len(SEEDS)} floor={floor}"

    arm_continue_counts = {
        name: sum(
            1
            for row in seed_rows
            if (row.get("arm_verdicts") or {}).get(name, {}).get("verdict") == "CONTINUE"
        )
        for name in ("shortlist", "shortlist_graph", "shortlist_graph_cot")
    }
    metrics = {
        "promote": False,
        "NOT_A_PROMOTE": True,
        "version": VERSION,
        "built_at_utc": built,
        "prior_gnn": {
            "s2gate": "KILL_0/20",
            "s2ablate": "KILL_0/5",
            "note": "GAT closed; this cell is tabular survivors only",
        },
        "gate": (
            "CONTINUE if arm beats MOM_ONLY on costed sum_net AND "
            "maxDD not > baseline+5pp AND sign-stable >=3/5 last folds (v1 gate); "
            f"family CONTINUE if >={FAMILY_MIN_FRAC:.0%} of {len(SEEDS)} seeds"
        ),
        "panel": panel_meta,
        "step": STEP,
        "seeds": list(SEEDS),
        "arms_cols": {key: list(val) for key, val in arms.items()},
        "graph_survivors_frozen": GRAPH_SURVIVORS,
        "cot_survivors_frozen": COT_SURVIVORS,
        "family_pass_floor": family_pass_floor(len(SEEDS)),
        "seed_rows": seed_rows,
        "arm_continue_counts": arm_continue_counts,
        "n_seeds_continue": sum(1 for row in seed_rows if row.get("verdict") == "CONTINUE"),
        "n_seeds": len(SEEDS),
        "verdict": family,
        "note": note,
    }
    memo = {
        "verdict": family,
        "promote": False,
        "version": VERSION,
        "panel_sha12": panel_sha[:12],
        "sha_note": panel_meta["sha_note"],
        "n_seeds_continue": metrics["n_seeds_continue"],
        "n_seeds": len(SEEDS),
        "arm_continue_counts": arm_continue_counts,
        "note": note,
        "seed_verdicts": [
            {
                "seed": row.get("seed"),
                "verdict": row.get("verdict"),
                "best_continue_arm": row.get("best_continue_arm"),
                "arm_verdicts": row.get("arm_verdicts"),
            }
            for row in seed_rows
        ],
        "paths": {
            "metrics": str(OUT_DIR / "copper_s2_tabular_survivors_metrics.json"),
            "memo": str(OUT_DIR / "copper_s2_tabular_survivors_memo.json"),
        },
    }
    receipt = (
        f"Verdict: {family} (promote=false) version={VERSION}\n"
        f"sha12={panel_sha[:12]} {panel_meta['sha_note']}\n"
        f"{note}\n"
        f"arm_continue_counts={arm_continue_counts}\n"
        f"no_gat=True\n"
    )
    (OUT_DIR / "copper_s2_tabular_survivors_metrics.json").write_text(
        json.dumps(metrics, indent=2, default=str)
    )
    (OUT_DIR / "copper_s2_tabular_survivors_memo.json").write_text(
        json.dumps(memo, indent=2, default=str)
    )
    (OUT_DIR / "copper_s2_tabular_survivors_receipt.txt").write_text(receipt)
    print(json.dumps(memo, indent=2, default=str), flush=True)
    print("RECEIPT:\n" + receipt, flush=True)
    return 0


if __name__ == "__main__":
    # Notebook-safe: return code only (avoid IPython SystemExit warning).
    raise SystemExit(main()) if not hasattr(__builtins__, "__IPYTHON__") else (main() or None)

# Kaggle / Jupyter: always run.
main()
