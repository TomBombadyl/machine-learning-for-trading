# Copper graph hyp card — frozen 2026-09-20

**promote=false.** FinPredict Engine hyp for a typed PIT copper graph
that may later feed a GNN. Not a paper lock. Not a live book. Does not
change `paper_mom_weekly_lock.json`.

Resource map: [docs/synap/GNN_RESOURCE_MAP.md](../../../docs/synap/GNN_RESOURCE_MAP.md).

---

## Contract

| Field | Locked value |
| ----- | ------------ |
| Universe | Research proxy `HG=F` / CME HG. Live intent remains Coinbase CU/NCU. |
| Panel | Prefer `deep_test_friday_panel_v0` sha `35f1fce22bca…`. Else a yfinance Friday build — **say which** on the receipt. Do not mix Databento HG and `HG=F` in one hash. |
| Cadence | Weekly Friday decisions |
| Decision cutoff | **20:00Z** |
| Primary label | `fwd_ret_5d` (trading days). 21d is a variant. 63d only if the named panel supports it. |
| Baseline | MOM_ONLY logistic (`mom_5d`, `mom_21d`, `mom_63d`), thresholds 0.60 / 0.40 |
| Costs | Turnover: 4 bps RT + 2 bps/side slip → 4 bps one-way (same as S2 v1) |
| Gate | IC → purge **before** any WF. Logistic only if purge survivors. GAT only if those survivors still exist. |
| Three timestamps | event / disclosure / extract. Features as-of `decision_date` @ 20:00Z. |

---

## Nodes (v0 schema)

| Node | Meaning | Free source |
| ---- | ------- | ----------- |
| `HG` | Research copper future | `HG=F` or Friday panel |
| `CPER` | Copper ETF | yfinance / panel `cper_mom_*` |
| `COPX` | Copper miners ETF | yfinance / panel |
| `FCX` | Name-level miner | yfinance / panel `fcx_mom_*` |
| `COT_MM` | Managed-money positioning | CFTC COT, +6 calendar-day lag |
| `SHFE_WH` | SHFE warrant / inventory | Engine extract only. Skip if sparse (`insufficient`). |

Do not add semantics `cnt_*` nodes. Those are SHELF.

Parked (not a v0 node): Thomson Reuters / CoreCommodity **CRB**
(`TRJEFFCRB` on TV). Same Ch8 bucket as CPER/FCX moms. Do not add
`CRB` here until a single Friday-panel column survives IC → purge
vs MOM_ONLY. Copper is a CRB constituent — relative strength is
not an independent graph.

---

## Edges (v0 schema)

| Edge | Rule | Leakage rule |
| ---- | ---- | ------------ |
| `corr` | Undirected. Spearman corr of Friday log-returns over a **pre-target** lookback (52 Fridays). Keep \|ρ\| ≥ 0.25. | Lookback ends at `decision_date`. No future bars. |
| `proxy` | Directed `CPER→HG`, `COPX→HG`, `FCX→HG` | Same Friday as-of |
| `positioning` | Directed `COT_MM→HG` when COT is available after +6d lag | `cot_as_of` ≤ decision Friday |
| `inventory` | Directed `SHFE_WH→HG` only if SHFE is dense | 20:00Z cutoff. Else omit. |

A correlation MST **alone** is not this hyp. `corr` is an edge type,
not the whole graph.

---

## Features emitted (tabular, Ch23.4)

At the `HG` node, each Friday:

- `graph_degree`
- `graph_pagerank`
- `graph_betweenness`
- `graph_hhi` (Herfindahl of \|edge weights\| into `HG`)
- `graph_n_nodes`, `graph_n_edges` (snapshot size)

These columns join onto the Friday grid. They are screened with the
same IC → purge as COT+MOM. They are **not** a strategy.

---

## What is allowed to train

1. Experiment A: COT+MOM vs MOM_ONLY, IC → purge.
2. If survivors: logistic / linear only (`06_linear` pattern).
3. If graph columns also survive purge: GAT hybrid
   (`06_gnn_feature_engineering` pattern) vs that tabular model.
4. **Kaggle Cell 1 (next):** paste
   `scripts/synap_copper/copper_gnn_s2gate_kaggle.py` as one new cell on
   the existing S2 notebook. Same Friday panel (`35f1fce22bca…`). S2
   gate vs MOM_ONLY, seeds 42–61, 500 epochs, step=13. Download
   `copper_gnn_s2gate_memo.json`. Do not rerun `copper_gnn_kaggle.py`.
5. **Kaggle Cell 2 (typed / 50 epochs):** blocked until Cell 1 family
   CONTINUE. Do not write or run it before that stamp.
6. Chronos / PatchTST: sealed ablation on the **same** purged frame,
   later. Not this card.

Paper MOM_ONLY weekly (0.60 / 0.40, `vol_target` + `dd_halt`) stays
PAPER.

---

## Hard do-nots

- `promote=true`
- New `case_studies/copper/`
- GAT on one HG close + MST with no other node types
- Paid LME / Databento / SHFE scrape
- Re-densify `cnt_*`
- Commit research parquets
