# ML4T evidence-loop grounding (copper)

**promote=false.** Maps Synap’s copper evidence loop onto **existing**
ML4T artifacts. Agents implement stages by configuring those artifacts,
not by inventing a second pipeline.

Loop (Engine-owned):

```text
hyp → data contract → labels/features → model vs baseline
  → purged / walk-forward → costs / risk → promote | kill | shelf | paper
```

Copper v0 gates: **PAPER / SHELF / KILL / CONTINUE / PROMOTE**.
PROMOTE is empty. Paper MOM_ONLY weekly is PAPER. Semantics counts and
GraphRAG v0 are SHELF. `S2_GBM_IMPORTANCE` is CONTINUE (importance
only). **2026-09-20:** S2 WF v0 and stretch Friday XGB are **KILL**.
S2 WF v1 `shortlist_log_h5` is **CONTINUE / `promote=false`**. See
[RECEIPT_2026-09-20_KAGGLE.md](RECEIPT_2026-09-20_KAGGLE.md).

---

## Stage 0 — Hypothesis

**Owner:** FinPredict Engine. Others propose; Engine freezes.

| Synap v0 hyp | Ledger / lock | ML4T place to ground it |
| ------------ | ------------- | ----------------------- |
| S1 MOM_ONLY weekly MR | `paper_MOM_ONLY_weekly`; Pine cousin | Ch8 price MOM; Ch6 baseline checkpoint; Ch11 logistic |
| S2 MOM_COT weekly | scorecard `weekly_MOM_COT`; regime lock | Ch4 `08_futures_positioning`; CME carry+MOM families |
| S3 inventory tilt | **frozen** until purged IC again | Ch8 state-variable role; Ch4 as-of joins |
| GraphRAG narrative | SHELF (soft IC, no purge survivors) | Ch23 Graph RAG + `09_knowledge_graph_features` |
| VectorRAG | ablation only | Ch22 hybrid retrieve + `04_rag_comparison_benchmark` |
| Raw event counts | SHELF (`SEM_COUNTS`, `HARD_EVENTS`) | Do not re-open via Ch10 bag-of-words densify |

Ch1 **evidence boundary**: exploration (feature IC, small sweeps) is
not confirmation (sealed holdout, Ch20). CME holdout 2024-01-01 →
2025-12-31 in `evaluation.holdout_*` is the pattern. Copper Friday
panel currently runs through 2026-09-11 (backfill) — **do not** tune
on the tail you will later call holdout.

Ch6 `01_where_ideas_come_from` SLOW/WRONG/RISK taxonomy is the language
for writing the next hyp card. Engine appends the ledger within one
turn of a receipt.

---

## Stage 1 — Data contract

**Owner:** Engine (lock). **CopperPotData** implements bars + alt PIT.
**SemanticsCopperPot** implements narrative PIT only.

### Synap contract (v0, locked 2026-09-18)

- Universe: Coinbase CU / NCU; research proxy `HG=F` / CME HG
- PIT key: `decision_date`; `decision_cutoff_utc=20:00Z`
- Cadence: weekly Friday primary; daily secondary only after TV weekly pack
- Labels: `fwd_ret_5d`, `fwd_ret_21d`, `fwd_ret_63d` (trading days)
- Classification vs naive MOM / MR baselines
- Costs: paper/TV first; Coinbase fees + slippage TBD before promote

### ML4T artifacts that already encode a contract

| Artifact | What it locks | Copper action |
| -------- | ------------- | ------------- |
| `case_studies/cme_futures/config/setup.yaml` | Universe (HG in metals), Friday cadence, Monday open, cost class, WF, labels | **Copy via `create_experiment`**; subset to `HG` (or metals) rather than new YAML schema |
| `case_studies/cme_futures/config/training/fwd_ret_5d.yaml` + `fwd_ret_21d.yaml` | Which presets run | Add `fwd_ret_63d` **only** if Engine opens that label; buffer `63D` |
| `case_studies/cme_futures/config/backtest/base.yaml` | Engine cash, shorts, leverage | Do not silently retune `initial_cash` for a 1-name book without a new hyp |
| `data/futures/market/futures_specs.yaml` | HG contract / margin | Read; do not invent a CU spec here |
| `data/futures/market/config.yaml` | Databento product list | Paid path |
| `data/synap/copper/paper_mom_weekly_lock.json` | Paper thresholds + kill | Engine-only edits |
| `utils/artifact_specs.py` | Label buffer units / market semantics | Import |

### Free vs paid data in this repo

```text
Free:   yfinance HG=F (research-machine)
        data/futures/positioning/cot_download.py   # CFTC
        data/download_all.py --free-only
        EDGAR (EDGAR_IDENTITY), GDELT
Paid:   data/futures/market/download.py            # Databento GLBX.MDP3
Engine: LME official, CU/NCU native history, SHFE warrants
```

CME teaching history is 2011–2025 on Databento. Backfill HG proxy is
2000-08-30 → 2026-09-18 (n=6542). Those are **different panels**. Do
not mix them in one registry hash without saying so on the hyp card.

---

## Stage 2 — Labels and features

**Owner:** CopperPotData (price + inventory + COT). SemanticsCopperPot
(narrative columns only). Engine accepts/rejects the frame.

### Labels

| Need | ML4T implementation | Gap |
| ---- | ------------------- | --- |
| `fwd_ret_5d` | CME `02_labels` + `labels.primary: fwd_ret_5d`; buffer `5D` | None |
| `fwd_ret_21d` | CME variant + `variant_buffers.fwd_ret_21d: 21D`; `rebalance_step: 3` | None |
| `fwd_ret_63d` | Ch7 `03_label_methods`; ETF also has 5d/21d | **Not in CME setup.** Add as a labeled variant in an experiment copy, or compute on the Friday panel with the same buffer rule |
| Direction vs MOM/MR | Ch7 classification labels; paper lock **negates** MOM (MR frame) | Keep the negation explicit; CME `ls_signal` is carry/MOM rank, not the paper MR lock |
| CU native labels | Ledger `CU_REMAP` n=26; `fwd_63=0` | **Do not** treat CU labels as powered. Grow history; keep HG proxy |

Purge length must match the **outcome horizon in sessions**, not
calendar days. Ch6 `02_cv_foundations` and `utils/cv_splits.py`
(`buffer_unit: sessions` on CME) are the SSOT.

### Features

| Family | Synap status | ML4T native path |
| ------ | ------------ | ---------------- |
| Momentum / vol / MA / RSI | Useful; in deep-test 62-col panel | CME `03_financial_features` + `features.windows` in setup.yaml; Ch8 `01_price_volume_features` |
| Term structure / carry | CME teaching; optional for single-name HG | CME `features.families: term structure`; needs V0/V1 (Databento or Engine curve) |
| CFTC COT | Useful (S2); TV COT is **not** faithful | `data/futures/positioning/`; Ch4 `08_futures_positioning`; +6d availability lag |
| SHFE inventory / warrants | Useful as **features**; loudest inventory IC on proxy (thin-n) | Ch4 `07_macro_data_alignment` as-of pattern; Ch8 slow/state features. No dedicated SHFE downloader in-repo |
| ETF moms (CPER, COPX, FCX) | On deep-test panel | Ch8 cross-instrument; ETF case study is the pedagogy, not the copper registry |
| Semantics raw counts | **SHELF** (thin +0.4 mirage; densify purge fail) | Do not use Ch10 TF-IDF counts as a workaround |
| Graph / hybrid v0 | **SHELF** (soft IC, no purge survivors) | Next hyp = cleaner extract via Ch23, not more counts |
| EIA L2 electrification | SHELF (purge soft; WF sum_net negative) | Ch4 FRED/macro notebooks; refresh-only |
| Model-based ARIMA/HMM | CME already scheduled in `model_based:` | Run only after simpler families survive |

PIT join for pot features: `decision_date` + 20:00Z. CME features use
settlement snapshot + declared lookback/lag in `features.families`.
Do not “fix” timestamps to rescue a backtest
(`data/synap/semantics/docs/SEMANTICS_COLLECTOR_PLAN.md`).

Friday WF-ready panel (backfill): n=1303, 2000-09-01 → 2026-09-11.
That is the copper analogue of CME’s weekly decision grid. Prefer
**attaching columns to that panel** over rebuilding bars.

Evaluation write-outs to reuse, not replace:

- `case_studies/cme_futures/05_evaluation` → `evaluation/triage_ledger.parquet`, `ic_timeseries.parquet`
- Ch7 `05_signal_evaluation`, `06_ic_inference` (HAC / block bootstrap)
- Ch7 `07_multiple_testing` (BH-FDR) before a “best IC” story
- Ch20 `02_feature_evaluation` (feature survival ≠ strategy survival)

---

## Stage 3 — Model vs baseline

**Owner:** Engine defines the baseline. **KaggleMLEngine** fits more
flexible models only against that frozen comparison.

| Baseline | Where it already lives | Copper v0 |
| -------- | ---------------------- | --------- |
| Naive MOM / MR | Paper lock (MR-framed MOM); Ch8 MOM; Ch16 non-ML baseline | **Required** on every card |
| Regularized linear / logistic | Ch11; CME `06_linear`; presets under `case_studies/config/` | Must beat this before GBM credit |
| Equal-weight / score rank | CME `13_backtest` signal stage | Cross-section toy; single-name CU uses thresholds 0.60/0.40 |
| GBM | Ch12; CME `07_gbm` (LightGBM, `device: cpu`, `max_bin: 255`) | `S2_GBM_IMPORTANCE` CONTINUE — prune features, DD-aware, **no DL** |
| Tabular DL / LSTM | CME `08_tabular_dl`, `09_dl_lstm` | Closed until Engine says otherwise |
| Latent SDF | CME `10b_*` — only family with HAC IC CI excluding 0 on the **30-name** book | Do not port SDF to one HG series |

Registry identity: training hash → prediction hash → backtest hash
(`case_studies/RUN_LOG.md`). Copper experiments that skip the registry
cannot be compared to CME teaching results and should say so.

Kaggle receipts already on the ledger (`kaggle_signal_importance_v0/`,
`kaggle_s1_purged_sweep/`) are **SHELF/CONTINUE research dumps**, not
a second official population. Next GBM work should land in an
`create_experiment` run_log or stay on the Engine host — not a new
notebook tree.

---

## Stage 4 — Purged CV and walk-forward

**Owner:** Engine (protocol). KaggleMLEngine executes folds. Nobody
writes a new splitter.

### Vocabulary (Ch6 §6.5 / `02_cv_foundations`)

| Term | Direction | What it stops | When |
| ---- | --------- | ------------- | ---- |
| **Label buffer (purge)** | Forward | Train labels whose outcome overlaps validation | Always |
| **Feature buffer (embargo)** | Backward | Train features that used later data | CPCV / k-fold (train after val) |
| **Walk-forward** | Time order | iid k-fold on returns | Default for all case studies |
| **Sealed holdout** | After all selection | Confirmation leakage | Ch20; CME 2024–2025 |
| **CPCV** | Combinatorial paths | Single-path luck | Teaching in Ch6; not copper v0 default |

López de Prado’s “embargo” in AFML ≈ this book’s **label buffer** in
the walk-forward diagrams. Use the table above; do not argue synonyms
on a receipt.

### Repo SSOT

| Piece | Path |
| ----- | ---- |
| Teaching | `06_strategy_definition/02_cv_foundations.py` |
| Case-study splits | `utils/cv_splits.py` → `WalkForwardCV` (`ml4t-diagnostic`) |
| CME protocol | `setup.yaml` `evaluation:` `n_splits: 5`, `train_size: 8Y`, `val_size: 1Y`, `calendar: CME`, `periods_per_year: 252` |
| Holdout purge of val | `_purge_holdout_touching_validation` in `cv_splits.py` |
| Label buffers | `labels.buffer` / `variant_buffers` |
| Conformal embargo | `case_studies/utils/conformal.py` (downstream; not a copper gate) |

### Copper application

1. Screen features with **purged IC** (Ch7) on the Friday panel.
2. Survivors only then get WF (CME 5×8Y/1Y **or** a declared thinner
   protocol if n cannot support 8Y — **write the protocol on the hyp**,
   do not silently drop to iid).
3. Ledger already killed “thin +0.4 mirage” and “densify purge fail”.
   Reopening counts without a new extract is a process violation.
4. `S1_KAGGLE` purged sweep: best `sum_net` but maxDD +8.55pp → SHELF.
   Reopen only with a harder DD hyp, using the **same** splitter.

---

## Stage 5 — Costs and risk

**Owner:** Engine. No promote while Coinbase fees/slippage are TBD.

### Costs

| Artifact | What it gives copper |
| -------- | -------------------- |
| CME `costs:` in setup.yaml | `material`: commission $2/contract + 1–2 ticks + roll slippage |
| CME `backtest.sweep.cost_grid_bps` | `[0,1,2,3,5,7,10,15,20,30,50]` — reuse the grid, change the **story** (Coinbase NCU vs CME HG) |
| CME `16_costs` | Carrier cost cascade; teaching breakeven ~20–30 bps/leg on the **30-name GBM+HRP** book — **not** a CU number |
| Ch18 `01_cost_taxonomy`, `12_commission_slippage_comparison` | Asset-class stacks; crypto perps 2/4 bps is Binance, not Coinbase |
| Scorecard / Pine | 0.04% commission is a **TV sketch**, not Engine TCA |
| Ledger `S2_COSTED_STUB` | SHELF: RF sum_net −0.58 vs mom_log −0.40 |

Until Engine publishes a CU/NCU fee card, cost cells are **sensitivity**,
not go-live.

### Risk

| Artifact | Copper mapping |
| -------- | -------------- |
| Paper lock `vol_target` + `dd_halt` | Required overlay on paper MOM; do not drop one |
| Kill: 26w DD over 15%; `sum_net` below -5%; lose-to-MR two consecutive reads | `paper_monitor_mom_weekly.py` + lock JSON |
| CME `15_risk_management` | stop / trailing / time-exit **grid** — research, not a silent lock change |
| Ch19 VaR/CVaR, kill switches | Language for Engine monitor, not a second monitor |
| Ch26 `01_drift_monitoring`, `04_circuit_breakers`, `03_safe_model_rollout` | Paper monitor + promotion gate pattern. Copper monitor **failed 2026-09-14** — fix the Engine job; do not replace with a notebook |
| Regime lock | MOM_ONLY = bull/high-vol sleeve; MOM_COT more bear-tolerant; crisis = small-n |

---

## Stage 6 — promote | kill | shelf | paper

**Owner:** FinPredict Engine only.

| Gate | Meaning in v0 | ML4T analogue (do not auto-fire) |
| ---- | ------------- | -------------------------------- |
| **PAPER** | Research/monitor book (MOM_ONLY weekly) | Ch25 “paper mode” is a **different** broker demo. Copper paper = lock JSON + monitor |
| **SHELF** | Keep artifacts; stop iterating family | Ch20 “holdout failure / next-iteration” without deleting the registry |
| **KILL** | Same storage as SHELF; stop the family | Ch19/26 kill switch |
| **CONTINUE** | Next evidence step (GBM importance) | Ch6 iterative module; still `promote=false` |
| **PROMOTE** | Live / TV-alert eligible | Ch26 `03_safe_model_rollout` five-criterion gate. **None yet.** |

Hard rule used in copper v0 and restated here:

> **No promote without IC → purge.**

A model that wins `sum_net` and loses maxDD (`S1_KAGGLE`) stays SHELF.
A feature with soft IC and zero purge survivors (`GRAPHRAG`,
`SEM_COUNTS`) stays SHELF. TV Strategy Tester and Pine alerts are
**user research**, not Engine confirmation.

Ch16 DSR / Rademacher / White Reality Check apply when a sweep pool
exists (CME reports `DSR_ER` on K≈550). A single paper lock is not
that pool. Do not quote CME Sharpe 1.236 as copper evidence — that
carrier is 30-name GBM+HRP on Databento, and even that holdout CI
contains zero.

---

## End-to-end path (configure, do not rewrite)

```text
docs/what-this-is.md
  → data/synap/copper/docs/* + this folder
  → scripts/create_experiment.py -- case_studies/cme_futures
  → edit experiment setup.yaml (universe HG; optional fwd_ret_63d)
  → free COT: data/futures/positioning/cot_download.py --products HG
  → 01_feasibility → 02_labels → 03_financial_features → 05_evaluation
  → Ch7 IC + purge  →  06_linear vs MOM/MR  →  (only then) 07_gbm
  → 13_backtest / 16_costs / 15_risk   [sensitivity, promote=false]
  → Engine ledger row: PAPER | SHELF | KILL | CONTINUE
```

GPU image (`ml4t-gpu`) is for KaggleMLEngine if a frozen GBM/DL hyp
says so. Default CME GBM is **cpu**. Crypto-perp notebooks that
*require* CUDA are irrelevant to CU.

---

## What this fork must not claim

- That running CME `19_strategy_analysis` “promotes” HG.
- That Databento HG is Coinbase CU.
- That Ch25 Alpaca/IB is the NCU path.
- That a local `registry.db` row is the FinPredict ledger.
- That SemanticsPot events joined on a research laptop are PIT-safe
  without the 20:00Z contract.
