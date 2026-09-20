# Copper GNN resource map

**promote=false.** Cited map of baselines, papers, Hugging Face,
Kaggle, and official free data for a copper prediction model that
*may* become a GNN. Not a paper lock. Not a train card.

Grounding: official URLs, this repo, or a file opened the same day.
Local 2026-09-20 ledger stays in
[RECEIPT_2026-09-20_KAGGLE.md](RECEIPT_2026-09-20_KAGGLE.md).
Hyp card: [data/synap/copper/docs/COPPER_GRAPH_HYP_CARD.md](../../data/synap/copper/docs/COPPER_GRAPH_HYP_CARD.md).

---

## What we already measured (do not rerun)

- Copper S2 WF **v0 = KILL** (weekly-in-position cost). **v1 = CONTINUE**
  on `shortlist_log_h5` only (`promote=false`). XGB/RF KILL. Stretch
  XGB KILL. SHFE ablation `insufficient`.
- Oil TCN/TCNN **KILL**. Brent EIA logistic CONTINUE research-only.
  No oil paper lock.
- Semantics raw counts / GraphRAG-as-counts **SHELF**.

A transformer or GAT on the **same one-name Friday HG close** is the
same family as those KILLs.

---

## Baselines that embarrassed transformers

Use these. They already live in this fork.

| Source | What it showed | ML4T home |
| ------ | -------------- | --------- |
| Zeng et al., *Are Transformers Effective for Time Series Forecasting?* ([cure-lab/LTSF-Linear](https://github.com/cure-lab/LTSF-Linear), [vivva/DLinear](https://github.com/vivva/DLinear)) | Linear / DLinear beat a generation of LTSF transformers on standard benchmarks | Ch13 `03_great_debate` |
| Nie et al., PatchTST ([PatchTST/PatchTST](https://github.com/PatchTST/PatchTST)) | A token is a patch of days | Ch13 `04_transformers` |
| Liu et al., iTransformer, ICLR 2024 ([thuml/iTransformer](https://github.com/thuml/iTransformer), [PDF](https://proceedings.iclr.cc/paper_files/paper/2024/file/2ea18fdc667e0ef2ad82b2b4d65147ad-Paper-Conference.pdf)) | A token is a whole variate | Ch13 `04_transformers` |
| Lim et al., Temporal Fusion Transformer | Attention + variable selection; covariate-heavy | later ablation only |
| LightGBM / logistic vs MOM | Hard tabular bar on *this* copper panel | CME `06_linear` / `07_gbm`; S2 v1 logistic is the local CONTINUE |

Ch13’s own read: deep learning wins in a **narrow** slice of the book’s
case studies. Our oil TCN suite already paid that tuition.

---

## When a GNN is justified

Papers that report commodity GNN lift assume a **cross-asset or
supply graph**, not one close:

- Tan, Hu, Liu, Yin. *Futures Quantitative Investment with Heterogeneous
  Continual Graph Neural Network.* ICDM 2024, pp. 851–856. DOI
  [10.1109/ICDM59182.2024.00104](https://doi.org/10.1109/ICDM59182.2024.00104).
  49-commodity futures panel. We do **not** have that dataset here.
- Multi-graph WTI work (correlation / KNN / DTW fusion, e.g. MG-STAN
  style). Correlation-only graphs are the **weak** end — Ch23.5 says so.
- Li (2026), *A Hybrid Model for Copper Futures Price Forecasting*
  ([Entropy 28(3):320](https://www.mdpi.com/1099-4300/28/3/320)).
  Copper-specific literature. Not a Kaggle recipe.
- Jin et al. survey: *A Survey on Graph Neural Networks for Time Series*
  ([arXiv:2307.03759](https://arxiv.org/abs/2307.03759)).

Canonical methods already listed in
[23_knowledge_graphs/README.md](../../23_knowledge_graphs/README.md):

- Kipf & Welling, GCN ([tutorial](https://tkipf.github.io/graph-convolutional-networks))
- Veličković et al., GAT ([repo](https://github.com/PetarV-/GAT))
- Hamilton et al., GraphSAGE
- FinKG; FinReflectKG / FinReflectKG-MultiHop

**Rule.** A GNN on a single Friday HG series plus a homemade
correlation MST is geometric-DL theater. The graph that earns overhead
is mines / smelters / warehouses / SHFE / CPER–COPX–FCX / COT agent
types / typed events, with event / disclosure / extract timestamps
(Ch23.6) and a 20:00Z cutoff.

---

## Hugging Face (zero-shot ablation, not the book)

| Artifact | URL | Use here |
| -------- | --- | -------- |
| Chronos / Chronos-Bolt | [amazon/chronos-bolt-base](https://huggingface.co/amazon/chronos-bolt-base), [collection](https://huggingface.co/collections/amazon/chronos-models-and-datasets) | Already in Ch13 `09_foundation_models`. Sealed zero-shot vs ridge only. |
| Chronos paper / code | [amazon-science/chronos-forecasting](https://github.com/amazon-science/chronos-forecasting) | Same |
| TimesFM | Hugging Face Transformers port | Same leakage warning as Chronos |
| Commodities daily prices | [paperswithbacktest/Commodities-Daily-Price](https://huggingface.co/datasets/paperswithbacktest/Commodities-Daily-Price) | **Foreign** panel check. Do not mix into the copper Friday registry hash. |

Ch13 names **pretraining contamination** as a leakage channel no
temporal split can inspect. Fine for a sealed score. Not a promote.

---

## Kaggle (machine yes, contract no)

Public CSVs are not the copper frame:

- [mattiuzc/commodity-futures-price-history](https://www.kaggle.com/datasets/mattiuzc/commodity-futures-price-history)
- [debashish311601/commodity-prices](https://www.kaggle.com/datasets/debashish311601/commodity-prices)
  (EUR quotes, no PIT, no as-of)

Do **not** replace `HG=F` / CME HG or
`deep_test_friday_panel_v0` (sha `35f1fce22bca…`) with those dumps.
Kaggle is compute. The contract stays ML4T + Engine panels.

---

## Free official data (PIT)

| Source | URL / in-repo | Lag / note |
| ------ | ------------- | ---------- |
| CFTC COT | [Commitments of Traders](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm); [data/futures/positioning/cot_download.py](../../data/futures/positioning/cot_download.py) | +6 calendar-day conservative lag (Ch4 `08_futures_positioning`) |
| EIA Weekly Petroleum Status | official EIA / `ir.eia.gov` (free API key) | Oil already used this (`oil_panel_eia_v1_1`). Do not wrap through a paid OilPriceAPI. |
| yfinance `HG=F` / `CL=F` / `BZ=F` | research proxy | Not Coinbase CU/NCU. Not Databento HG. |
| EDGAR / GDELT | ML4T free stack | Graph extract = Ch23 `08_8k_event_extraction`, not count densify |

---

## Paid / skip unless Engine lifts budget

Databento GLBX (CME teaching 2011–2025), LME official, Barchart SHFE,
Metals-API. S2 SHFE ablation was `insufficient`. Skip a paid scrape
(Experiment B rule). Do not mix Databento HG and yfinance `HG=F` in
one registry hash.

---

## ML4T factory (do not invent a parallel stack)

1. Copy `cme_futures` via [scripts/create_experiment.py](../../scripts/create_experiment.py); universe `HG`. Free fallback: Friday `HG=F` panel, named on the card.
2. Graph **features** first: [23_knowledge_graphs/09_knowledge_graph_features](../../23_knowledge_graphs/09_knowledge_graph_features.ipynb) (PageRank, betweenness, HHI, crowding as tabular columns). Local emitter: `scripts/synap_copper/copper_graph_tabular_features.py`.
3. IC → purge (Ch7 `05_signal_evaluation` / `06_ic_inference`). Local screen: `scripts/synap_copper/experiment_a_cot_mom_purge.py`.
4. Graph **embeddings** only if survivors: [23_knowledge_graphs/06_gnn_feature_engineering](../../23_knowledge_graphs/06_gnn_feature_engineering.py). Local adapter: `scripts/synap_copper/copper_gnn_hybrid.py`.
5. **Kaggle weak-gate cell (stamped):** `copper_gnn_kaggle.py` — do not rerun.
6. **Kaggle Cell 1 (next):** paste `scripts/synap_copper/copper_gnn_s2gate_kaggle.py`. S2 gate vs MOM, seeds 42–46. Cell 2 typed GAT blocked until family CONTINUE.
7. Sequence ablation later, **same** purged frame: Ch13 Linear / PatchTST / Chronos. Not a TCN reopen.

Gate: IC → purge → costed WF vs MOM. CONTINUE ≠ paper lock.
Paper MOM_ONLY weekly is unchanged.

---

## Hard do-nots

- More S2 trees, GPU-on-XGB, PatchTST/TCN rerun of killed families
- Train GAT on one HG close with a correlation MST and call it geometric DL
- Mix Kaggle EUR CSVs or HF daily dumps into the copper registry
- Flip paper MOM thresholds or mint an oil paper lock
- Re-densify `cnt_*` / GraphRAG-as-counts
