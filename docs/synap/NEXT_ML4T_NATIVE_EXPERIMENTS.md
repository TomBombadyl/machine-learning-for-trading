# Next 3 ML4T-native copper experiments

**promote=false.** Prefer these over inventing chapter-shaped notebooks.
Each reuses `case_studies/cme_futures` and/or the Friday deep-test
panel plus stock Ch4/Ch7/Ch8/Ch11/Ch12/Ch23 tools.

Engine freezes the hyp card before anyone trains. CopperPotData /
SemanticsCopperPot emit PIT columns. KaggleMLEngine runs only after
the frame is frozen. Gate is always **IC → purge** before WF.

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

## Experiment C — S2 GBM prune on the *frozen* importance frame (beat a new sweep notebook)

| | |
| --- | --- |
| **Why native** | Ledger `S2_GBM_IMPORTANCE` is already CONTINUE. CME `07_gbm` + Ch12 presets + `create_experiment` are the sweep. `S1_KAGGLE` taught that a purged `sum_net` win with worse DD is SHELF. |
| **Owners** | Engine (frozen feature list + DD hyp) · KaggleMLEngine (fit) |
| **Do** | Freeze the MOM+ETF+SHFE/COT column set from the importance receipt (drop unstable names; keep `rank_stable` 5/5). In an experiment copy, point `07_gbm` / LightGBM presets at that frame (cpu unless Engine asks GPU). **Must** include logistic/`06_linear` as the baseline (receipt: rf h5d sum_net 0.142 vs log 0.053 — re-estimate after prune). Report purge survivors, maxDD vs S1 SHELF (+8.55pp warning), and costed path vs `S2_COSTED_STUB` (RF already lost to mom_log). |
| **Do not** | New Kaggle notebook tree. TabM/LSTM/PatchTST. Re-densify semantics. Promote on h5d `sum_net` while h21 “GBM lost”. Change paper MOM thresholds. |
| **Free-data note** | Runs on the existing deep-test / Friday panel. No new paid API. |
| **Gate** | CONTINUE or SHELF. **Never PROMOTE.** DD-aware hyp required to reopen S1-style sweeps. |

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
