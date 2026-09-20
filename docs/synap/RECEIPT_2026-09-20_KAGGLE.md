# Receipt — 2026-09-20 Kaggle dumps

**promote=false.** Engine ledger notes for one calendar day of
KaggleMLEngine receipts. Not a paper lock. Not a live book. Do not
commit the JSON dumps (operator-local under `C:\Users\tobin\Downloads\`).

Sources (operator files, SHA not recomputed here):

| File | Role |
| ---- | ---- |
| `deep_test_s2_metrics.json` + `deep_test_s2_memo.json` + `ML4T_RECEIPT_CARD.md` | Copper Experiment C / S2 purged WF **v0** |
| `deep_test_s2_metrics (1).json` + `deep_test_s2_memo (1).json` + fold table `(1)` | Copper S2 purged WF **v1** (turnover cost) |
| `copper_friday_mom_etf_shfe_xgb_v0.json` | Copper stretch Friday XGB (kitchen-sink) |
| `metrics_suite_v0.json` | Index: oil TCN + copper stretch |
| `oil_tcnn_tcn_suite_v0.json` | Oil EIA + TCN/TCNN on `fwd_ret_5d` |
| `oil_downtime_suite_receipt.json` | Oil P0/P1/P2 downtime suite wrapper |

GPU on every receipt: **cpu**. `torch 2.10.0+cpu`. Do not attach a GPU
to “fix” `cuda_boot`.

---

## Copper

### C — Deep Test S2 purged WF v0 → **KILL**

- Panel: `deep_test_friday_panel_v0.parquet` sha256
  `35f1fce22bca89e161075b1d7e9c9d94755eb70bb44fb5b08bc785074234212f`
  shape `[1303, 74]`, 2000-09-01 → 2026-09-11.
- Costs: RT 4 bps + 2 bps/side. Thresholds 0.60 / 0.40.
- Semantics `cnt_*` excluded (SHELF). SHFE ablation: `insufficient`.
- Success rule (notebook): CONTINUE if challenger beats MOM_ONLY on
  costed `sum_net` **and** maxDD ≤ baseline+5pp **and** sign-stable
  ≥3/5 on ≥1 horizon.
- **Passers: 0 / decisions 9.**

| Name | `sum_net` | maxDD | vs mom | sign last-5 | Gate |
| ---- | --------- | ----- | ------ | ----------- | ---- |
| shortlist_log_h5 (headline) | +0.010274 | 0.345645 | beats mom −0.225966 / DD 0.440866 | 2/5 | **KILL** (sign) |
| shortlist_xgb_h5 | −0.360117 | 0.958246 | loses sum + DD | 1/5 | KILL |
| shortlist_rf_h5 | −0.109957 | 0.567431 | DD + sign | 0/5 | KILL |
| all h=21 shortlists | worse than mom −0.372419 | — | — | ≤2/5 | KILL |
| all h=63 shortlists | −2.88 to −4.22 vs mom **+2.553559** | 6.6–8.1 vs 2.00 | — | — | KILL |

Early console `PRIMARY h=5 shortlist_xgb` / `PRIMARY h=21 mom_only_log`
were **which model was fit**, not the gate. XGB never passed.

COT ablation (`shortlist_cot_*`) ran on a short window (2022–2026,
n=208). Ablation only — not a passer. Do not promote it.

v0 charged 8 bps **every week in a position** and labeled `fwd_ret==0`
as down. That KILL is the v0-cost receipt. It is not overwritten.

### C — Deep Test S2 purged WF v1 → **CONTINUE** (`promote=false`)

Operator files 2026-09-20 13:36Z (`version=deep_test_s2_wf_v1`,
`mode=v1`, `robustness=[]`). Same panel sha `35f1fce22bca…`,
`[1303, 74]`. Cost model **turnover** (`cost_one_way=0.0004`).
`fwd_ret==0` dropped. GPU **cpu**. XGB backend `cpu_hist`.

Success rule (unchanged): CONTINUE if challenger beats MOM_ONLY on
costed `sum_net` **and** maxDD ≤ baseline+5pp **and** sign-stable
≥3/5 on ≥1 horizon. **Never PROMOTE.**

- **Passers: 1 / decisions 9** — only `shortlist_log_h5`.
- GBM/RF/XGB still **KILL** on every horizon. Stretch XGB (separate
  hyp) still **KILL**. SHFE ablation still `insufficient`.
- Paper MOM_ONLY weekly lock unchanged.

| Name | `sum_net` | maxDD | vs mom | sign last-5 | Gate |
| ---- | --------- | ----- | ------ | ----------- | ---- |
| shortlist_log_h5 (headline) | +0.161 | 0.226677 | beats mom −0.256638 / DD 0.426748 | 3/5 | **CONTINUE** |
| shortlist_rf_h5 | −0.038258 | 0.323651 | beats sum+DD | 0/5 | KILL (sign) |
| shortlist_xgb_h5 | −0.025717 | 0.727583 | DD +30pp | 1/5 | KILL |
| all h=21 shortlists | −0.25 to −0.51 vs mom −0.326306 | — | — | ≤2/5 | KILL |
| all h=63 shortlists | −2.71 to −3.98 vs mom **+2.595159** | 6.5–7.9 vs 2.00 | — | — | KILL |

Headline window: n=624, 2013-12-27 → 2026-05-22, 24 folds, AUC 0.535,
IC 0.0396, frac_flat 0.875. Last-5 fold `sum_net` (CSV): −0.016667,
+0.037128, +0.072554, +0.050346, 0.0 (flat). MOM_ONLY h5 is 96% flat
(`frac_flat` 0.9598) — the written gate still passed.

COT ablation is **not** a passer (n=208, 8 folds, 2022–2026). Note
only: `shortlist_cot_log_h5` +0.258462 / DD 0.17869 / sign 5/5 vs
shortlist_log +0.097. Use it as a hint for Experiment A, not a stamp.

v1 did **not** run `DEEP_TEST_MODE=robustness`. Do not rerun v1.
Optional extra compute on this family is robustness seeds 42–46 on
the logistic passer only. Do not raise trees.

### Stretch Friday XGB → **KILL**

`copper_friday_mom_etf_shfe_xgb_v0.json` (`stretch: true`). Different
hyp from S2 shortlist: all CPER/COPX/FCX moms + SHFE + full COT.
`n=624`, 24 folds, `cpu_hist`, cost `copper_paper_v1`.

| | `sum_net` | maxDD |
| --- | --------- | ----- |
| XGB | −0.239184 | 0.798532 |
| mom-only logistic | −0.016627 | 0.595883 |

Reason: `no_lift_vs_mom_log,sum_net_le_0,maxDD_floor` (lift −0.222557;
DD worse by ≥5pp; last-5 signs 3/5).

### Experiment A + gated TinyGAT (`copper_gnn_kaggle_v0`) → **CONTINUE** (`promote=false`)

Operator files 2026-09-20 14:32Z (`copper_gnn_memo.json` /
`copper_gnn_metrics.json` / `copper_gnn_receipt.txt`).
**Panel sha matches S2 v0/v1:**
`35f1fce22bca89e161075b1d7e9c9d94755eb70bb44fb5b08bc785074234212f`,
`sha_note=matches_v0`, path
`/kaggle/input/datasets/synapgarden/synap-finpredict-panels-v0/deep_test_friday_panel_v0.parquet`,
shape `[1303, 74]`. GAT fit n=1300 after dropna. cpu. 20 epochs.
**This gate is not the S2 gate.** CONTINUE = COT IC→purge survivors
**and** graph topology survivors **and** TinyGAT hybrid costed
`sum_net` beat **tabular graph survivors**. No MOM / maxDD / last-5
sign on this card.

| Field | Value |
| ----- | ----- |
| Experiment A | **CONTINUE** — `cot_managed_money_net` IC 0.0900, `pct_oi` 0.0903, `z_52w` 0.1334 (n=337 each) |
| COT kill | `cot_managed_money_net_chg_1w` IC 0.0298 (`abs_ic<0.03`) |
| MOM screen | only `mom_63d` survived (IC 0.0615). `mom_5d` / `mom_21d` `abs_ic<0.03` |
| Graph CONTINUE | `graph_pagerank` 0.0664, `graph_betweenness` −0.0437, `graph_hhi` 0.0634 (n=1300) |
| Graph KILL | `graph_degree`, `graph_n_nodes`, `graph_n_edges` |
| tabular `sum_net` | −0.413309 |
| hybrid `sum_net` | +0.582117 (46 folds) |
| promote | false |

Not a paper lock. Do not retune 0.60/0.40. Do not attach extra
datasets. Do not git-add the Downloads JSON. Do not rerun this cell.

### Cell 1 S2-gate deep (`copper_gnn_s2gate_v0_deep`) → **KILL**

Operator files 2026-09-20 14:59Z. Same panel sha `35f1fce22bca…`.
20 seeds (42–61), 500 epochs, step=13, cpu. Audit
`graph_not_redundant_vs_cot`. **seeds_continue=0/20** floor=12.
Every seed: hybrid beat MOM on costed `sum_net` (~0.94–1.41 vs
−0.70) and maxDD (~0.42 vs 0.94); **last-5 fold signs 0/5 for hybrid
and MOM**. Failure mode is temporal sign stability, not undertraining.
`cell2_blocked=true`. Do **not** rerun 20×500.

### S2 ablate (`copper_gnn_s2ablate_v0`) → **KILL**

Operator receipt 2026-09-20 (Kaggle `SystemExit 0`). Same panel sha
`35f1fce22bca…`, `matches_v0`, audit `graph_not_redundant_vs_cot`.
Arms MOM / graph_tabular / gat_emb / hybrid; epoch caps 50/150/250 +
early-stop; seeds 42–46; soft gate last-10 ≥4/10.

- **best_epoch_cap=50; seeds_continue=0/5 floor=3**
- `shelf_gat=False` (no arm cleared the soft gate; graph alone did not CONTINUE)
- `cell2_blocked=True`

Confirms Cell 1 deep: temporal / recent-fold sign stability kills the
family even with shorter epochs and the graph-vs-GAT split. Do **not**
rerun ablate, s2gate, or weak-gate. Do **not** write Cell 2 (typed GAT).

Next offline: treat graph topology columns as research features only
(already IC survivors) on the frozen Friday frame; prefer Experiment A
COT+MOM / S2 v1 logistic lane. GAT hybrid stays SHELF under the S2 gate.

### S2 tabular survivors (`copper_s2_tabular_survivors_v0`) → **CONTINUE** (`promote=false`)

Operator receipt + metrics 2026-09-20. Same panel sha
`35f1fce22bca…`, `matches_v0`. Logistic only; no GAT. v1 WF gate
(step=26, last-5 ≥3/5). Seeds 42–46.

- **seeds_continue=5/5** floor=3
- `arm_continue_counts`: shortlist **5**, shortlist_graph **5**,
  shortlist_graph_cot **5**
- `no_gat=True`
- Paths are **seed-invariant** on this frame (same sum_net/DD every
  seed) — logistic + frozen features; 5/5 is a re-stamp, not five
  independent draws.

| Arm | `sum_net` | maxDD | last-5 pos | vs MOM |
| --- | --------- | ----- | ---------- | ------ |
| MOM_ONLY | +0.1022 | 0.2605 | 3/5 | baseline |
| shortlist | +0.4163 | **0.2011** | 4/5 | CONTINUE |
| shortlist_graph | +0.4936 | 0.2320 | 4/5 | CONTINUE |
| shortlist_graph_cot | **+0.6815** | 0.2320 | 4/5 | CONTINUE (best each seed) |

Deltas vs shortlist: graph **+0.077** sum_net / DD **+3.1pp**; graph+COT
**+0.265** sum_net / DD **+3.1pp**. Both still beat MOM on DD. Prefer
`shortlist_graph_cot` as research headline stack; keep shortlist as the
cleaner-DD fallback. Still **not** a paper lock. Do not flip 0.60/0.40.
Do not reopen TinyGAT.

### S2 tabular marathon (`copper_s2_tabular_marathon_v0`) → **CONTINUE** (`promote=false`)

Operator receipt + memo 2026-09-20. Same panel sha `35f1fce22bca…`,
`matches_v0`. Logistic only; `no_gat=True`. Primary gate only
(h5 / step26 / 4bps / lb52 / corr0.25 / thr 0.60–0.40 / C=1.0 / full
`shortlist_graph_cot`). Seeds 42–51.

- **seeds_continue_primary=10/10** floor=6
- `elapsed_run_s=3701` (~1.0 h wall; full run `partial=false`)
- Lookback×corr×cost×thr×C×LOO grid ran as diagnostics; family gate
  did not require alts
- Seed-invariant primary paths expected (logistic + frozen feats)

Confirms survivors/deep primary stack under a wider stress emit.
Still **not** a paper lock. Do not reopen TinyGAT. Optional leftover:
upload `copper_s2_tabular_marathon_metrics.json` if Engine wants LOO /
lookback sensitivity detail.

### Paper lock (unchanged)

`data/synap/copper/paper_mom_weekly_lock.json` +
`data/synap/copper/docs/HG_WEEKLY_DECISION_LOCK.md`.
MOM_ONLY weekly, 0.60/0.40, `vol_target` + `dd_halt`. Do not retune
from these KILLs.

---

## Oil

There is **no oil paper lock**. Kill helper in
`scripts/synap_oil/contract.py` is reserved (26w DD >15%, `sum_net` <
−5%, lose-to-MR two consecutive reads). A single Kaggle card does not
arm it.

### Downtime suite `OIL_DOWNTIME_SUITE_V0` → P0/P1/P2 **CONTINUE**

Panel: `deeptest_costed_friday_panel_v0.parquet` sha256
`eea15b30fe5091c308f9f2c9b39bdd31712f219aded09925978282aa3343fa3d`
(`panel_sha_ok: true`). CPU.

| Pack | Suite headline | `sum_net` / maxDD | passers |
| ---- | -------------- | ----------------- | ------- |
| P1 `OIL_P1_WTI_DEEP_GBM_V0` | `WTIOIL-PERP__p1_base_z_chg4w__rf__conservative_futures_v1__stride5` | 5.767481 / 1.611807 | 9 |
| P0 `OIL_P0_GAS_Z_SEAS_5D_DEEP_V0` | `BRENTOIL-PERP__p0_gas_z_seas__rf__conservative_futures_v1__pathA` | 2.171059 / 1.889173 | 5 |
| P2 (wrapper) | `BRENTOIL-PERP__p2_crack_plus_dist_seas__rf__conservative_futures_v1__stride13` | 2.169615 / 0.851996 | 8 |

P2 **pack** card after `DEEP RE_RUN COMPLETE` disagrees: headline
`WTIOIL-PERP__p2_crack_plus_dist_seas__xgb__conservative_futures_v1__stride13`
`sum_net` 4.648603 / maxDD 1.423718 / **9** passers, and **mom
`sum_net` 5.940175** (XGB lost to mom). Use the pack files under
`kaggle_p2_crack_dist_63d_deep_v0/` for P2; wrapper for P0/P1.

Kaggle symbols `WTIOIL-PERP` / `BRENTOIL-PERP` are **not** the
committed lock universe (`NYMEX_CL` / `ICE_BRENT` / `CL_BRENT_SPREAD`,
free `CL=F` / `BZ=F`). Do not equate them.

### EIA + TCN suite → TCN **KILL**; Brent EIA logistic **CONTINUE**

Panel: `oil_panel_eia_v1_1.parquet`. Label `fwd_ret_5d`. Cost
`conservative_futures_v1`. No `CL_BRENT_SPREAD` row.

| Key | verdict | `sum_net` | maxDD |
| --- | ------- | --------- | ----- |
| `ICE_BRENT__eia_primary__eia_logistic` | CONTINUE | 2.150591 | 0.813448 |
| `ICE_BRENT__eia_primary_plus_mom__eia_logistic` | CONTINUE | 1.624525 | 1.294927 |
| All `tcnn` / `tcn_lite` | KILL | — | — |
| All `NYMEX_CL` models | KILL (mom is BASELINE) | — | — |

Brent-only CONTINUE is **out of** the CL+Brent+spread lock as a lock
candidate. Research stamp only.

---

## Do not (from this day)

- New Kaggle notebook tree, GPU attach, TabM/LSTM/PatchTST/TCN rerun
- Reopen S2 **GBM/XGB/RF** or stretch XGB without a new mechanism
- Treat v1 `shortlist_log_h5` CONTINUE as a paper lock or promote
- Change copper paper MOM thresholds
- Mint an oil paper lock
- Treat TV / Pine / Kaggle `sum_net` as a promote
- Commit research parquets or these JSON dumps
