# Research handoff prompt — FinPredict copper + oil (paste to the next agent)

Copy everything below the line into a new agent. Do not add the JSON
dumps to context unless the agent asks for one field.

---

You are a FinPredict Engine / CopperPotData / KaggleMLEngine agent on
the ML4T fork `TomBombadyl/machine-learning-for-trading` (default
branch as cloned).

**promote=false.** You do not write `promote=true`. You do not mint an
oil paper lock. You do not change
`data/synap/copper/paper_mom_weekly_lock.json`.

## Pickup (read in this order)

1. `docs/synap/README.md`
2. `docs/synap/API_BUDGET_TAVILY.md` — **Sept 2026 Tavily ~80% used; avoid Tavily calls**
3. `docs/synap/RECEIPT_2026-09-20_KAGGLE.md` — **Kaggle ledger**
4. `docs/synap/REPORT_2026-09-20_COPPER_TV.md` — copper TV initial tests (learning only)
5. `docs/synap/LEARNINGS_FROM_COPPER_V0.md`
6. `docs/synap/NEXT_ML4T_NATIVE_EXPERIMENTS.md` — C GBM **KILL**; v1 logistic **CONTINUE / promote=false**
7. `docs/synap/ML4T_COPPER_OWNERSHIP_MAP.md`
8. `docs/synap/ML4T_EVIDENCE_LOOP_GROUNDING.md`
9. `docs/synap/GNN_RESOURCE_MAP.md` — copper GNN path; GAT closed under current hyp
10. `docs/synap/ASSET_FM_RESOURCE_MAP.md` — HF / official TSFMs for copper/oil; sealed only. Hugging Face MCP is live (`hub_repo_search` / `hub_repo_details` as `TomBombadyl` / SynapGarden admin). Re-query the Hub; do not invent IDs. SynapGarden has zero Hub repos. **Do not re-Tavily this inventory.**
11. Copper graph hyp: `data/synap/copper/docs/COPPER_GRAPH_HYP_CARD.md`
12. Copper lock: `data/synap/copper/docs/HG_WEEKLY_DECISION_LOCK.md`
13. Oil lock: `data/synap/oil/docs/CL_BRENT_WEEKLY_DECISION_LOCK.md`
14. `scripts/synap_oil/contract.py` — no oil paper lock; kill helper reserved
15. TV cousins: `data/synap/copper/docs/tradingview/README.md` — two v6 scripts + v5 lock twin. Oil TV folder has no Pine.
16. TV search ontology: `data/synap/copper/docs/tradingview/TV_RESEARCH_ONTOLOGY.md` + `tv_cards.tsv`. Append cards. Do not join to the graph hyp.

No guessing. Ground facts in this repo, an official URL, or a file you
just opened. If unknown, write `unknown — look up <page>` and stop.

## What is already decided (2026-09-20)

### Copper

1. **Deep Test S2 purged WF v0 = KILL.** 0 passers / 9 decisions.
   Weekly-in-position 8 bps cost; `fwd_ret==0` labeled down. Panel
   `deep_test_friday_panel_v0` sha `35f1fce22bca…`. Headline
   `shortlist_log_h5` beat mom on `sum_net` (+0.010 vs −0.226) and DD,
   **sign-stable 2/5** → KILL. Keep this as the v0-cost receipt.
2. **Deep Test S2 purged WF v1 = CONTINUE / `promote=false`.** Same
   panel sha. Turnover cost (`cost_one_way=0.0004`), zeros dropped.
   **1 passer / 9 decisions:** `shortlist_log_h5` sum_net +0.161 /
   maxDD 0.226677 vs mom −0.256638 / 0.426748; sign 3/5; AUC 0.535;
   n=624 (2013–2026). XGB/RF KILL every horizon. h21/h63 KILL. SHFE
   `insufficient`. COT ablation n=208 is not a passer. `robustness=[]`.
   Do not rerun v1.
3. **Stretch Friday XGB (MOM+all ETF moms+SHFE+COT) = KILL.**
   `sum_net` −0.239 vs mom_log −0.017; maxDD worse by ≥5pp.
   Reason `no_lift_vs_mom_log,sum_net_le_0,maxDD_floor`.
4. **`copper_gnn_kaggle_v0` = CONTINUE / `promote=false`.** Experiment A
   COT survivors (net, pct_oi, z_52w). Graph survivors (pagerank,
   betweenness, hhi). TinyGAT hybrid `sum_net` +0.582 vs tabular
   −0.413; n=1300; 46 folds; cpu. **Gate ≠ S2** (no MOM / maxDD /
   sign). Memo `panel_sha12` **confirmed** `35f1fce22bca` (`matches_v0`,
   shape `[1303, 74]`).

Paper MOM_ONLY weekly stays PAPER (0.60/0.40, `vol_target` + `dd_halt`).
`S2_GBM_IMPORTANCE` was CONTINUE (importance only). GBM/XGB/RF WF
fits are KILL. v1 CONTINUE is **not** a paper lock.

5. **Copper TV initial tests = learning, not a gate.** Operator ran
   `NCU_S1_MOM_ONLY` and `NCU_MOM_FRED` on FX:COPPER and saved both
   in TradingView (`Allow longs` / `Allow shorts` isolate sides).
   Test A daily both: +12.2% / 45.4% DD / PF 1.019 — fails B&H.
   FRED 12h **long-only** (CSV `2c086`): +59.66% / 37.76% DD / PF 1.35
   / 62/108; shorts dragged the two-sided book. FRED 2h long-only
   2020–26: +12.46% / PF 1.11 — two bull bursts, 2022 giveback, not a
   conflict feature. 1D/5D/7D/1M/63D and ≤4h failed (search overfit).
   Do not mint a 12h/2h file. Oil has no Pine and was not tested.
   A later MOM_ONLY Daily “killed it” report has **no CSV** — unvalidated.
   Report: `docs/synap/REPORT_2026-09-20_COPPER_TV.md`.
   Search log: `data/synap/copper/docs/tradingview/tv_cards.tsv`.

### Oil — CONTINUE research, no paper lock

1. `OIL_DOWNTIME_SUITE_V0` P0/P1/P2 CONTINUE on
   `deeptest_costed_friday_panel_v0` sha `eea15b30fe50…`. Use wrapper
   for P0/P1. P2 pack card (WTI XGB, 9 passers, `sum_net` 4.65) **lost
   to mom 5.94** — write that on the ledger row. Wrapper P2 headline
   (Brent RF, 8 passers) is stale vs the pack.
2. EIA + TCN suite on `oil_panel_eia_v1_1.parquet` / `fwd_ret_5d`:
   **all TCN/TCNN KILL**. CONTINUE only
   `ICE_BRENT__eia_primary__eia_logistic` and
   `ICE_BRENT__eia_primary_plus_mom__eia_logistic`. All `NYMEX_CL`
   models KILL. No spread book in that suite.
3. Kaggle `WTIOIL-PERP` / `BRENTOIL-PERP` ≠ lock `NYMEX_CL` /
   `ICE_BRENT` / `CL=F` / `BZ=F`. Do not collapse them.

## Exact next action

**Do not start a new Kaggle notebook tree.** Do not rerun v0 or v1.
Do not sweep more TradingView timeframes. Oil is a later sit-down.

1. Restate Engine ledger rows if not already written:
   copper S2 v0 **KILL**; copper S2 v1 `shortlist_log_h5` **CONTINUE /
   promote=false**; copper stretch XGB **KILL**; oil TCN family
   **KILL**; oil Brent EIA logistic **CONTINUE / promote=false**;
   oil downtime P0–P2 **CONTINUE / promote=false** (P2 lost to mom on
   `sum_net`).
2. If the operator wants more compute on the v1 passer, the only
   allowed leftover is `DEEP_TEST_MODE=robustness` in
   `scripts/synap_copper/deep_test_s2_wf_v1.py` (seeds 42–46, primary
   logistic only). Not more trees. Not XGB/RF reopen.
3. **Next paste:** `scripts/synap_copper/copper_gnn_s2gate_kaggle.py`
   as a **new cell** on the existing S2 notebook (same dataset only).
   That is Cell 1 / S2-strength gate vs MOM, seeds 42–61, 500 epochs,
   step=13, COT-dummy
   audit. Do not rerun `copper_gnn_kaggle.py`. Cell 2 (typed GAT) is
   **blocked** until `copper_gnn_s2gate_memo.json` family CONTINUE.
   After SystemExit 0, download the s2gate memo/metrics/receipt and
   stamp the ledger. SHELF or KILL → do not write Cell 2.
4. Experiment B (SHFE as Ch8 state) only if SHFE is dense enough —
   S2 SHFE ablation was `insufficient`. Skip rather than paid scrape.
5. Oil: no `OIL_P3` exists in this repo. Do not invent one. Do not
   mint `paper_*_weekly_lock.json`. Do not rerun TCN.

## Hard do-nots

- New files under `0x_*` or `case_studies/copper/`
- New purge library, Friday clock, or cost engine
- Re-densify `SEM_COUNTS` / `HARD_EVENTS` / GraphRAG-as-counts
- Commit `data/**/*.parquet` or Downloads JSON
- Flip copper paper thresholds
- Treat v1 CONTINUE as a paper lock or promote
- Treat TV / Pine / Kaggle `sum_net` as a promote
- Mix Databento HG with yfinance `HG=F` in one registry hash
- Fake CU bars; CU n=26 cannot power 63d
- Join CopperPot + SemanticsPot locally; Engine joins @ 20:00Z
- GPU unless a *new* frozen hyp (not these) says so

## Bot split

- **FinPredict Engine** — ledger, gates, this handoff
- **KaggleMLEngine** — idle unless Engine freezes robustness or A
- **CopperPotData** — PIT COT/SHFE/HG only if A or B opens
- **SemanticsCopperPot / SemanticsOilPot** — idle (counts SHELF)
- **!Flash!** — this folder + READMEs only; do not paste full notebooks

## Operator-local artifacts (do not git-add)

v0: `C:\Users\tobin\Downloads\deep_test_s2_metrics.json` (+ memo, folds, `ML4T_RECEIPT_CARD.md`)
v1: `C:\Users\tobin\Downloads\deep_test_s2_metrics (1).json` (+ memo `(1)`, fold table `(1)`)
`C:\Users\tobin\Downloads\copper_friday_mom_etf_shfe_xgb_v0.json`
`C:\Users\tobin\Downloads\metrics_suite_v0.json`
`C:\Users\tobin\Downloads\oil_tcnn_tcn_suite_v0.json`
`C:\Users\tobin\Downloads\oil_downtime_suite_receipt.json`

GNN 14:32Z: `C:\Users\tobin\Downloads\copper_gnn_memo.json` (+ metrics, receipt)

When you finish, append one ledger line to
`docs/synap/RECEIPT_2026-09-20_KAGGLE.md` if you stamped something new.
Do not rewrite the KILL/CONTINUE table without a new measured file.
