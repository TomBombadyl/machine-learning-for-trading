# Next 3 ML4T-native copper experiments

**promote=false.** Prefer these over inventing chapter-shaped notebooks.
Each reuses `case_studies/cme_futures` and/or the Friday deep-test
panel plus stock Ch4/Ch7/Ch8/Ch11/Ch12/Ch23 tools.

Engine freezes the hyp card before anyone trains. CopperPotData /
SemanticsCopperPot emit PIT columns. KaggleMLEngine runs only after
the frame is frozen. Gate is always **IC → purge** before WF.

**2026-09-20:** Experiment **C GBM prune is KILL / closed**. S2 WF **v0
= KILL** (wrong weekly-in-position cost). S2 WF **v1 = CONTINUE** on
`shortlist_log_h5` only (`promote=false`). Stretch Friday XGB is KILL.
Do not rerun v0 or v1. Optional leftover on this family is
`DEEP_TEST_MODE=robustness` (seeds, logistic only). New copper hyp is
**A then B**. Receipt:
[RECEIPT_2026-09-20_KAGGLE.md](RECEIPT_2026-09-20_KAGGLE.md). Handoff
prompt: [RESEARCH_HANDOFF_PROMPT.md](RESEARCH_HANDOFF_PROMPT.md).
Copper TV initial tests (learning only):
[REPORT_2026-09-20_COPPER_TV.md](REPORT_2026-09-20_COPPER_TV.md).
Do not treat Tester equity as a hyp. Oil TV is empty; do not port
copper Pines.

---

## Experiment A — HG-only CME config + free COT (beat a new case study)

| | |
| --- | --- |
| **Why native** | HG is already in `universe.product_groups.metals`. Friday/Monday clock already matches the CU contract. COT downloader already exists. |
| **Owners** | Engine (hyp) · CopperPotData (COT + universe subset) · KaggleMLEngine (linear only) |
| **Do** | `scripts/create_experiment.py` on `cme_futures`. In the **copy** of `setup.yaml`, set universe to `HG` (or metals: HG/GC/SI/PL). Pull **free** COT: `data/futures/positioning/cot_download.py --products HG --start-year 2000`. Attach COT with Ch4 `08_futures_positioning` lag (+6 calendar days). Run `01_feasibility` → `02_labels` → `03_financial_features` → `05_evaluation`. Screen COT+MOM vs MOM-only with Ch7 IC + purge. Fit `06_linear` / logistic **only if** purge survivors exist. |
| **Do not** | Full 30-product Databento refresh “to get HG”. New `case_studies/copper/`. Paid LME. GBM/DL. Commit parquets. |
| **Free-data note** | If Databento bars are missing, run the same COT+MOM screen on research-machine `HG=F` / Friday panel. Say which panel on the card. |
| **Gate** | PAPER or SHELF. `promote=false`. |
| **Local screen** | `scripts/synap_copper/experiment_a_cot_mom_purge.py` (Friday panel or yfinance `HG=F` build). Graph schema: `data/synap/copper/docs/COPPER_GRAPH_HYP_CARD.md`. Cited map: [GNN_RESOURCE_MAP.md](GNN_RESOURCE_MAP.md). |
| **Kaggle train** | Marathon CONTINUE 10/10 stamped. **Next paste:** `scripts/synap_copper/copper_s2_tabular_focus_kaggle.py` (expanded timeframes + params). `promote=false`. No GAT. |

---

## Experiment B — SHFE inventory as a Ch8 *state* column on the Friday panel

| | |
| --- | --- |
| **Why native** | Ledger already says inventory is useful **as a feature**. Ch8 role split + Ch4 as-of joins are the implementation. S3-as-strategy stays frozen. |
| **Owners** | Engine (hyp) · CopperPotData (PIT inventory) · Engine (IC/purge) |
| **Do** | Join SHFE warrant-change (Engine/CopperPot extract) onto `deep_test_friday_panel_v0` at `decision_date` with **20:00Z** cutoff. Declare the column like CME `features.families` (`role: state`, lookback, lag, failure_mode). Run the Ch7 univariate stack (`05_signal_evaluation`, `06_ic_inference`) **and** a purge that matches `fwd_ret_5d/21d` (63d only if the panel supports it — CU 63d is still dead). Compare incremental IC vs MOM+COT, not vs zero in a vacuum. |
| **Do not** | New inventory strategy notebook. Daily (non-Friday) labels without weekday-hygiene proof. “Tilt overlay” that skips purge. Semantics count columns (SHELF). |
| **Free-data note** | If SHFE is unavailable, skip the experiment — do not substitute a paid scrape in this fork. COT-only is Experiment A. |
| **Gate** | CONTINUE only if purge survivors are stable across horizons; else SHELF. No S3 strategy unlock without Engine. `promote=false`. |

---

## Experiment C — S2 GBM prune — **KILL / closed 2026-09-20**

| | |
| --- | --- |
| **Status** | **GBM/XGB/RF = KILL.** Stretch kitchen-sink XGB = KILL. **v1 logistic shortlist h5 = CONTINUE / `promote=false`** (1/9 decisions). v0 (weekly-in-position cost) = KILL, kept as the v0-cost receipt. |
| **Why native (historical)** | Ledger `S2_GBM_IMPORTANCE` was CONTINUE (importance only). CME `07_gbm` + Ch12 presets are the sweep. `S1_KAGGLE` taught that a purged `sum_net` win with worse DD is SHELF. |
| **Measured v1** | `shortlist_log_h5` sum_net +0.161 / maxDD 0.226677 vs mom −0.256638 / 0.426748; sign 3/5; AUC 0.535. Same panel sha `35f1fce22bca…`. Turnover cost. |
| **Do now** | Do not rerun v0 or v1. Next leftover is `scripts/synap_copper/deep_test_s2_wf_robustness.py` (paste whole file; seeds 42–46). Do not raise `n_estimators`. New copper hyp is Experiment A. Paper MOM_ONLY lock unchanged. |
| **Do not** | New Kaggle notebook tree. TabM/LSTM/PatchTST. Re-densify semantics. Promote on h5d `sum_net`. Change paper MOM thresholds. Treat COT ablation (n=208) as a passer. Reopen XGB/RF. |
| **Receipt** | [RECEIPT_2026-09-20_KAGGLE.md](RECEIPT_2026-09-20_KAGGLE.md) |

---

## Experiment C (original brief, closed)

Kept so agents do not re-invent the prune. **Do not execute.**

| | |
| --- | --- |
| **Owners** | Engine (frozen feature list + DD hyp) · KaggleMLEngine (fit) |
| **Was** | Freeze MOM+ETF+SHFE/COT from importance; logistic baseline mandatory; report purge / maxDD / costed vs `S2_COSTED_STUB`. |
| **Gate used** | CONTINUE if challenger beats MOM_ONLY on costed `sum_net` AND maxDD not > baseline+5pp AND sign-stable ≥3/5 on ≥1 horizon. **Never PROMOTE.** |

---

## Explicitly later (not in the next three)

| Idea | Why wait | Native home when Engine opens it |
| ---- | -------- | -------------------------------- |
| GraphRAG cleaner extract | v0 SHELF; needs extract quality + history, not another count | Ch23 `08_8k_event_extraction` + `09_knowledge_graph_features`; Ch22 as ablation |
| `fwd_ret_63d` on CME setup | CU n=26 cannot power it; add as experiment `labels.variants` only on HG panel | Ch7 + CME `02_labels` |
| Coinbase fee grid | Fees/slippage TBD | Ch18 + CME `16_costs` `cost_grid_bps` with an Engine fee card |
| Paper monitor 9/14 fail | Ops fix, not an experiment | Ch26 language; `paper_monitor_mom_weekly.py` |
| Native CU bars | Data growth, not a model | CopperPotData; remap receipt |

---

## Checklist (print on the hyp card)

- [ ] `promote=false` written on the card
- [ ] Panel named (Friday deep-test vs CME Databento vs `HG=F`)
- [ ] Baseline named (MOM/MR and linear/logistic)
- [ ] Purge horizon = label horizon (sessions)
- [ ] No SHELF family reopened without a new mechanism
- [ ] No new files under `0x_*` or `case_studies/copper/`
- [ ] Engine ledger row after the receipt (PAPER/SHELF/KILL/CONTINUE)
