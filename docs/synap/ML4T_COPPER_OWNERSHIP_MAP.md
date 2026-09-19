# ML4T copper ownership map

**promote=false.** Synap Garden / FinPredict copper research on this
ML4T 3e fork. This file tells agents **who owns what**, **what to
read vs run**, and **what not to invent in parallel**.

It is additive documentation. It does not rewrite chapter notebooks
as a product, does not change `data/synap/copper/` locks, and does
not authorize a live or paper promote.

Ground truth for copper v0 (outside git unless later copied):

- Experiment ledger v0 — FinPredict Copper (CU/NCU)
- Backfill receipt v0 — `deep_test_panel_v0` / Friday panel
- Data contract CU/NCU v0 (locked 2026-09-18)

In-repo lock twins (do not fork a second lock set):

- `data/synap/copper/README.md`
- `data/synap/copper/paper_mom_weekly_lock.json`
- `data/synap/copper/docs/HG_WEEKLY_DECISION_LOCK.md`
- `data/synap/copper/docs/MULTI_HORIZON_LONG_SHORT_SCORECARD.md`
- `data/synap/copper/docs/REGIME_BACKTESTS_LOCKED.md`
- `scripts/synap_copper/` (score / reprint / monitor only)

---

## 1. Trade targets vs research proxy

| Lane | Instrument | Owner use |
| ---- | ---------- | --------- |
| Live intent | Coinbase **CU** (2,000 lb) / **NCU** (500 lb) | Engine TV-alert path only after a future promote. Prefer NCU for size. |
| Research proxy | yfinance **`HG=F`** daily; CME **HG** in `cme_futures` | Labels/features until durable free CU/NCU history exists. |
| Not a book | CME Databento 30-product panel | Teaching pipeline. Configure / subset; do not trade the book. |
| Not Coinbase | `case_studies/crypto_perps_funding` (Binance perps) | Funding-arb pedagogy. Do not treat as CU/NCU. |

PIT join lock (CopperTalk, unchanged): key `decision_date`; cutoff
**20:00Z** same day. Features from CopperPotData / SemanticsCopperPot
must be available by cutoff.

Primary cadence: **weekly Friday decision** → next Coinbase derivatives
open. That already matches CME case-study `decision.cadence:
weekly_friday_close` + `execution_delay: monday_open`.

---

## 2. Bot roster

| Bot | Owns | Does not own |
| --- | ---- | ------------ |
| **FinPredict Engine** | Evidence loop; ledger rows; promote/kill/shelf/paper; TV shortlist; paper MOM monitor; cost/risk kill criteria | Inventing chapter stacks; rewriting notebooks |
| **CopperPotData** | Copper alt-data PIT features: SHFE inventory, CFTC COT, weekday/Friday hygiene, HG/CU bar growth | Narrative GraphRAG; promote decisions; GPU sweeps |
| **SemanticsCopperPot** | Cross-asset narrative features; **GraphRAG lead** / VectorRAG ablation; event extract hygiene | Raw event **counts** (SHELF); joining pots in this fork; promote |
| **KaggleMLEngine** | Frozen-hyp GPU/eval/sweeps; GBM importance; purged vs logistic | Hyp design; feature invention; DL before tabular IC→purge |
| **!Flash!** | Token-efficient context: this map, chapter READMEs, setup.yaml, lock JSON | Pasting full `.py` notebooks; unpaid Databento pulls |

**Handoff rule.** Engine freezes a hyp + data contract. CopperPotData /
SemanticsCopperPot emit PIT columns. KaggleMLEngine trains only on that
frozen frame. Engine scores IC → purge → WF → costs/risk → gate.
Nobody else writes `promote=true`.

---

## 3. Read vs run vs do-not-invent

### Read first (cheap, free, no training)

| Artifact | Why |
| -------- | --- |
| This folder + `data/synap/copper/docs/*` | Locks, scorecard IDs, regime notes |
| `docs/what-this-is.md` | What reproduces vs what is paid/GPU |
| `docs/running-notebooks.md` | Case-study pipeline + `create_experiment` |
| `case_studies/README.md` + `case_studies/RUN_LOG.md` | Shared stage order + registry |
| `case_studies/cme_futures/README.md` + `config/setup.yaml` | HG is already in `universe.product_groups.metals` |
| `06_strategy_definition/README.md` + `02_cv_foundations` | Purge vs embargo, WF, CPCV |
| `07_defining_the_learning_task/README.md` | Labels, IC, FDR, feasibility |
| `04_fundamental_alternative_data/README.md` | PIT, COT (`08_futures_positioning`) |
| `22_rag_financial_research/` + `23_knowledge_graphs/` READMEs | Vector vs Graph RAG; three-timestamp leakage |
| `data/futures/README.md` + `data/futures/positioning/README.md` | Paid Databento vs **free CFTC COT** |
| `utils/README.md` | `cv_splits.py`, `modeling.py` — import, do not fork |

### Run when Engine has a frozen hyp (configure, do not fork)

| Command / path | Owner | Notes |
| -------------- | ----- | ----- |
| `scripts/create_experiment.py` on `cme_futures` | Engine + KaggleMLEngine | Writable `setup.yaml` copy; leave release `run_log` intact |
| `data/futures/positioning/cot_download.py --products HG` | CopperPotData | **Free.** Friday publication; +6 calendar-day conservative lag |
| `data/download_all.py --free-only` | anyone | ETF / factor / crypto teaching sets; not CU bars |
| `case_studies/cme_futures/01`…`05` | CopperPotData + Engine | Feasibility → labels → features → IC triage |
| `06_linear` then `07_gbm` | KaggleMLEngine | Linear baseline first; GBM only after IC |
| `16_costs` / `15_risk_management` | Engine | Cost grid + overlays; Coinbase fees still TBD |
| `scripts/synap_copper/paper_monitor_mom_weekly.py` | Engine | Paper lock cousin; IDLE without fills snapshot |
| Ch7 `05_signal_evaluation` / `06_ic_inference` | Engine | IC + HAC before any sweep |

### Do not invent in parallel

| Temptation | Use this instead |
| ---------- | ---------------- |
| New copper case-study folder | `create_experiment` + `cme_futures` universe subset (`HG` or metals) |
| New purged-CV library | `utils/cv_splits.py` → `ml4t.diagnostic.splitters.WalkForwardCV`; Ch6 `02_cv_foundations` |
| New run log / MLflow | `case_studies/{cs}/run_log/registry.db` (Ch6.7) |
| New cost/slippage engine | `cme_futures` `costs:` + Ch18 notebooks + `16_costs` |
| New weekly Friday scheduler | `setup.yaml` `decision.cadence: weekly_friday_close` |
| New MOM/COT feature cookbook | Ch8 `01_price_volume_features` + `03_structural_cross_instrument_features`; CME `features.families` |
| New inventory PIT aligner | Ch4 `07_macro_data_alignment` + Ch8 `04_fundamentals_macro_calendar` |
| New GraphRAG product | Ch23 `03_graph_rag_qa`, `04_rag_comparison_benchmark`, `08_8k_event_extraction`, `09_knowledge_graph_features` |
| New count densify for news | **Forbidden.** `SEM_COUNTS` / `HARD_EVENTS` are SHELF |
| New Coinbase live broker in Ch25 | Ch25 is IB / Alpaca / QuantConnect **demos**. CU/NCU execution stays Engine + TV |
| Commit research parquets | `data/**/*.parquet` is gitignored; see `data/synap/copper/README.md` |
| Promote from TV / Pine / local Sharpe | Explicitly banned in every copper lock |

---

## 4. Chapters → bot (what to read vs run)

Legend: **R** = read README + one teaching notebook. **C** = configure /
reuse in a copper experiment. **X** = skip for copper v0 unless Engine
opens a new hyp.

### Introduction

| Chapter | Bot | Mode | Copper note |
| ------- | --- | ---- | ----------- |
| 1 Process is edge | Engine, !Flash! | **R** | Evidence boundary, regimes, trial logging. `factor_regimes` / `macro_regimes` are teaching, not copper labels. |

### Part I — Data

| Chapter | Bot | Mode | Copper note |
| ------- | --- | ---- | ----------- |
| 2 Data universe | CopperPotData | **R** | Storage / quality. CME EDA notebooks need Databento (paid). Free path is `HG=F` + COT. |
| 3 Microstructure | Engine | **X** | ITCH / dollar bars. Daily CU/NCU v0 does not need LOB. |
| 4 Fundamentals + alt | CopperPotData, SemanticsCopperPot | **R/C** | **Primary PIT chapter.** `08_futures_positioning` is the COT pattern. Macro as-of joins for inventory. EDGAR for GraphRAG extract, not copper prices. |
| 5 Synthetic data | KaggleMLEngine | **X** | Do not synthesize CU history to hide the n=26 CU remap gap. |

### Part II — Research design + features

| Chapter | Bot | Mode | Copper note |
| ------- | --- | ---- | ----------- |
| 6 Strategy framework | Engine | **R/C** | Universe, Friday schedule, cost class, WF protocol, run log. `02_cv_foundations` is the purge/embargo SSOT. |
| 7 Learning task | Engine | **R/C** | `fwd_ret_5d/21d/63d`, IC, BH-FDR, DSR. CME already ships 5d + 21d; **63d is a config add**, not a new label library. |
| 8 Financial features | CopperPotData | **R/C** | MOM / vol / carry / calendar. Declare windows in `setup.yaml` `features:` like CME. Inventory = **state**, not a new strategy. |
| 9 Model-based features | CopperPotData | **C** later | ARIMA/HMM on carry — CME already does this. Do not add until MOM+COT+inv clear purge. |
| 10 Text features | SemanticsCopperPot, !Flash! | **R** | Lexicon/TF-IDF/FinBERT are **ablation baselines**. Count densify already failed. Prefer Ch23 graph features over Ch10 bag counts. |

### Part III — Models

| Chapter | Bot | Mode | Copper note |
| ------- | --- | ---- | ----------- |
| 11 ML pipeline | Engine, KaggleMLEngine | **C** | Ridge / LASSO / logistic are the **baseline every later model must beat**. CME `06_linear`. |
| 12 GBM + tabular DL | KaggleMLEngine | **C** | LightGBM/XGB on frozen frame. Ledger `S2_GBM_IMPORTANCE` is CONTINUE (promote=false). TabPFN/TabM only after GBM prune. |
| 13 DL time series | KaggleMLEngine | **X** | Ledger: **no DL yet**. LSTM/PatchTST wait for tabular IC→purge + DD-aware hyp. |
| 14 Latent factors | KaggleMLEngine | **X** | CME SDF is a 30-product cross-section lesson, not an HG singleton model. |
| 15 Causal ML | Engine | **R** | CME `11_causal_dml` on `carry_pct` is the pattern if inventory/COT claim causality. Not a promote path. |

### Part IV — Strategy

| Chapter | Bot | Mode | Copper note |
| ------- | --- | ---- | ----------- |
| 16 Simulation | Engine | **C** | Backtest as falsification; DSR / Reality Check. CME `13_backtest`. TV is not this chapter. |
| 17 Portfolio | Engine | **X** v0 | Single-name CU/NCU. HRP/MVO are 30-product toys. Keep `vol_target` from the paper lock. |
| 18 Transaction costs | Engine | **R/C** | CME `16_costs` + Ch18 taxonomy. Coinbase fees + slippage **TBD before any promote**. |
| 19 Risk | Engine | **C** | `vol_target` + `dd_halt` already locked on paper MOM. CME `15_risk_management` overlays. Crisis slices = ugly / small-n. |
| 20 Synthesis | Engine | **R** | Holdout is confirmation, not a search pool. IC–Sharpe decorrelation is why we do not promote on IC alone **or** on Sharpe alone. |

### Part V — Advanced AI

| Chapter | Bot | Mode | Copper note |
| ------- | --- | ---- | ----------- |
| 21 RL execution | Engine | **X** | Inventory MM / execution RL is not the copper v0 book. |
| 22 RAG | SemanticsCopperPot, !Flash! | **R** | **VectorRAG ablation.** Hybrid retrieve + RAGAs. Do not rebuild a second RAG stack. |
| 23 Knowledge graphs | SemanticsCopperPot | **R/C** | **GraphRAG lead.** Three-timestamp model (event / disclosure / extract) = PIT. `09_knowledge_graph_features` → tabular feats for Ch11/12, not raw counts. |
| 24 Agents | Engine, !Flash! | **R** | Tool contracts / memory. This ownership map **is** the copper tool contract. Do not spawn unsupervised research agents that write notebooks. |

### Part VI — Production

| Chapter | Bot | Mode | Copper note |
| ------- | --- | ---- | ----------- |
| 25 Live trading | Engine | **R** only | IB/Alpaca/QC demos. **Not** Coinbase Derivatives. Paper ≠ Ch25 paper mode. |
| 26 MLOps | Engine | **C** conceptually | Drift, circuit breakers, **explicit promotion gates**. Paper monitor (failed 2026-09-14) is the copper instance of §26.2. |
| 27 Systematic edge | Engine | **R** | Process > model. No action. |

---

## 5. Case studies → bot

| Case study | Bot | Use for copper | Do not |
| ---------- | --- | -------------- | ------ |
| **`cme_futures`** | Engine, CopperPotData, KaggleMLEngine | **Primary native stack.** Metals includes **HG**. Friday close / Monday open. Labels 5d/21d. COT-ready. Costs + risk + holdout already wired. | Retrain all 30 products + Databento just to get HG |
| `etfs` | CopperPotData | Cross-asset MOM/MR pedagogy; CPER/COPX/FCX appear on the **research-machine** deep-test panel (backfill), not as a committed ETF universe here | Treat ETF Sharpe as CU evidence |
| `crypto_perps_funding` | Engine | Cost/cadence discipline on a derivatives book | Map Binance funding to CU |
| `fx_pairs` | — | Daily carry/MOM | Ignore for copper v0 |
| `nasdaq100_microstructure` | — | Intraday LOB (AlgoSeek) | Ignore |
| `sp500_*` / `us_*` | SemanticsCopperPot (EDGAR/13F patterns only) | Graph construction examples | Equity-factor books |

Shared machinery (all case studies) — **do not fork**:

- `case_studies/{id}/config/setup.yaml` — universe, labels, CV, costs
- `case_studies/config/{model_type}/*.yaml` — presets
- `case_studies/utils/` — folds, GBM, backtest runner, registry
- `case_studies/research/` — official population / study workflow
- `scripts/create_experiment.py` — writable experiment copy
- `scripts/download_artifacts.py` — read published registries without training

---

## 6. Libraries → bot

Book libraries (import; do not reimplement):

| Library | Stage | Copper owner | Parallel invention to avoid |
| ------- | ----- | ------------ | --------------------------- |
| `ml4t-data` | Data | CopperPotData | New yfinance/Databento wrappers beside `data/futures/loader.py` |
| `ml4t-engineer` | Features/labels | CopperPotData | Ad-hoc triple-barrier / bar builders for daily HG |
| `ml4t-models` | Models | KaggleMLEngine | One-off sklearn scripts that skip the registry |
| `ml4t-diagnostic` | Eval / **WalkForwardCV** | Engine | Homegrown purged k-fold |
| `ml4t-backtest` | Strategy | Engine | TV Strategy Tester as “the” backtest |
| `ml4t-live` | Deploy | Engine | Wiring CU live through Ch25 |

Repo-local imports:

| Module | Owner | Note |
| ------ | ----- | ---- |
| `utils/cv_splits.py` | Engine | Calendar-aware WF; CME calendar maps to `CME_Equity` |
| `utils/modeling.py` | KaggleMLEngine | Config + folds |
| `data/futures/positioning/cot_download.py` | CopperPotData | Free COT |
| `scripts/synap_copper/contract.py` | Engine | Candidate IDs + kill helpers; **not a promote** |

---

## 7. Existing Synap copper surfaces (do not duplicate)

| Path | Owner | Role |
| ---- | ----- | ---- |
| `paper_mom_weekly_lock.json` | Engine | Paper MOM_ONLY weekly; thr 0.60/0.40; `promote: false` |
| `docs/HG_WEEKLY_DECISION_LOCK.md` | Engine | Prose twin of the JSON |
| `docs/MULTI_HORIZON_LONG_SHORT_SCORECARD.md` | Engine | Locked candidate IDs (`weekly_MOM_COT`, LME rows, …) |
| `docs/REGIME_BACKTESTS_LOCKED.md` | Engine | MOM_ONLY bull/high-vol; MOM_COT more bear-tolerant; crisis small-n |
| `docs/tradingview/*` | Engine | Cousin sketches. TV ≠ Engine evidence |
| `scripts/synap_copper/paper_monitor_mom_weekly.py` | Engine | Kill criteria; IDLE without snapshot/fills |
| `data/synap/semantics/docs/SEMANTICS_COLLECTOR_PLAN.md` | SemanticsCopperPot | Separate pot; no copper join in this repo |

Research-machine only (never commit): Friday panel, deep-test parquet,
fills, COT/LME extracts. Backfill receipt names
`deep_test_panel_v0.parquet` (n=6542, 62 cols) and
`deep_test_friday_panel_v0.parquet` (n=1303).

---

## 8. Free-data notes

| Source | Cost | Who may pull | Caveat |
| ------ | ---- | ------------ | ------ |
| yfinance `HG=F` | Free | CopperPotData | Proxy, not CU/NCU native |
| CFTC COT | Free | CopperPotData | Tue snapshot, Fri 15:30 ET print; conservative +6d lag |
| SEC EDGAR | Free + `EDGAR_IDENTITY` | SemanticsCopperPot | Graph extract, not price |
| GDELT | Free | SemanticsCopperPot | Noisy; PIT via GDELT stamps |
| `data/download_all.py --free-only` | Free | anyone | Teaching datasets |
| Databento `GLBX.MDP3` CME | **Paid** | Engine budget only | Estimate first; not a Synap script default |
| LME official | Engine-side | Engine | TV HG is COMEX; see LME README |
| Coinbase CU/NCU history | Thin (ledger: n=26 remap) | CopperPotData | Grow native bars; do not fake them |

`scripts/synap_copper/` is **free-only** by contract.

---

## 9. Operating rules (all bots)

1. **promote=false** unless Engine writes a ledger row that says otherwise. None do in v0.
2. **No promote without IC → purge.** Soft IC is not a survivor.
3. Configure existing case studies (esp. CME / metals / HG) before adding files under `0x_*` chapter trees.
4. Do not join CopperPot and SemanticsPot in this fork. Engine joins on `decision_date` @ 20:00Z.
5. A green local scorecard, TV equity curve, or Kaggle `sum_net` is research output, not a promote.
6. If blocked on paid data, continue offline on `HG=F` + free COT + the Friday panel.
