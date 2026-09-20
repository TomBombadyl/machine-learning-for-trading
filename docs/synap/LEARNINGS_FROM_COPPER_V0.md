# Learnings from copper v0 — implied ML4T upgrades

**promote=false.** What copper work through **2026-09-20** changes about
*how* Synap agents should use this ML4T fork. Not a rewrite of
chapters. Not a new lock. Not a promote.

Sources: experiment ledger v0, backfill receipt v0, CU/NCU data
contract v0, plus in-repo copper scaffold under `data/synap/copper/`.

---

## 1. Semantics raw counts are SHELF — stop the Ch10-shaped reflex

**What happened.** Event-count densify (`SEM_COUNTS`) produced a thin
+0.4 IC mirage and **failed purge**. CopperPot hard-event counts
(`HARD_EVENTS`) never cleared IC. Graph/Vector/hybrid v0 (`GRAPHRAG`)
had soft IC and **no purge survivors**.

**Implied upgrade.**

- Do **not** reopen count densify. Ch10 bag-of-words / TF-IDF /
  “just add more headlines” is the same family with a prettier name.
- SemanticsCopperPot’s next object is **structure**, not frequency:
  Ch23 extraction + typed edges + three timestamps (event, disclosure,
  extract), then `09_knowledge_graph_features` (centrality, crowding,
  cross-graph terms) as **tabular columns**.
- VectorRAG (Ch22) stays an **ablation** against GraphRAG, matching
  `04_rag_comparison_benchmark`. Token cost is !Flash!’s problem;
  accuracy-after-purge is Engine’s.
- Keep SemanticsPot **beside** CopperPot. The collector plan already
  forbids a local copper+news join. Ledger failure modes are exactly
  why.

**Hyp shape for GraphRAG (when Engine reopens).** Cleaner extract /
more history — not denser counts. PIT via Ch23.6 cutoff rules and the
20:00Z contract. Gate remains IC → purge before any WF. `promote=false`.

---

## 2. Inventory and COT earned *feature* status, not strategy status

**What happened.** SHFE warrant-change features were the loudest
inventory IC on the HG proxy (thin-n). COT shows up in S2
(MOM_COT) as a regime-tolerant research candidate. S3 inventory-tilt
as a **strategy** is frozen until a feature clears purged IC *again*.

**Implied upgrade.**

- Treat inventory / COT as Ch8 **state or signal columns** attached to
  the existing Friday panel, using Ch4 as-of / COT-lag patterns.
- Do **not** stand up a new “inventory strategy” notebook. CME
  `features.families` already separates `role: signal` vs `role: state`.
  Inventory belongs there.
- Free path: `data/futures/positioning/cot_download.py` (CFTC). SHFE
  warrants stay Engine/CopperPotData — no paid scrape in
  `scripts/synap_copper/`.
- TV COT overlays are not Engine COT (`HG_MOM_COT_Weekly_README.md`).
  A TV sketch cannot “confirm” S2.

---

## 3. The Friday panel exists — stop rebuilding the clock

**What happened.** Backfill receipt (PAPER):

| Panel | n | Span | Note |
| ----- | -: | ---- | ---- |
| HG daily deep-test | 6542 | 2000-08-30 → 2026-09-18 | 62 cols; ETF moms + inventory join; semantics cols present but SHELF |
| Friday WF-ready | 1303 | 2000-09-01 → 2026-09-11 | Decision grid |
| CPER / COPX / FCX | 3731 / 4130 / 7851 | — | Cross-instrument moms |
| Native CU | thin | — | Labels still HG proxy |

**Implied upgrade.**

- New work **joins onto** `deep_test_friday_panel_v0` (research-machine)
  or an experiment copy of CME’s weekly Friday grid. Do not mint a
  third weekly calendar.
- CME `decision.cadence: weekly_friday_close` + Monday open is the
  same economic clock as the CU/NCU contract. Prefer configuring that
  over a custom scheduler.
- Weekday hygiene remains CopperPotData PAPER. If Friday vs other
  sessions still leak into daily models, that is a feature bug, not a
  reason for a new case study.
- Do not commit the parquets. `data/synap/copper/README.md` already
  says so.

---

## 4. CU native bars are a gap — do not paper over them with models

**What happened.** `CU_REMAP`: n=26, CU↔HG corr 0.97, `fwd_ret_63d=0`.
Contract still uses `HG=F` until durable free CU/NCU history is wired.

**Implied upgrade.**

- CopperPotData priority is **grow CU/NCU history**, not a deeper
  model on 26 rows.
- High CU↔HG correlation licenses the **proxy** for research; it does
  not license promoting an HG Sharpe as a CU book.
- Do not use Ch5 synthetic generators to elongate CU. That hides the
  gap the ledger already named.
- CME Databento HG (2011+) is a **different** series (paid, ratio
  back-adjusted continuous). If you mix it with yfinance `HG=F`
  2000–2026, say so on the hyp card and keep hashes separate.
- 63-day labels are in the Synap contract but **not** in CME
  `setup.yaml` (5d primary, 21d variant). Adding `fwd_ret_63d` is a
  **config/label variant** in an experiment copy, not a new labeling
  library — and CU cannot support 63d until history grows.

---

## 5. Paper monitor hygiene is an Engine MLOps bug, not a strategy idea

**What happened.** Paper MOM_ONLY weekly is locked (0.60/0.40,
`vol_target` + `dd_halt`, 26w DD / sum_net / lose-to-MR kills). The
**Monday paper monitor routine failed 2026-09-14** and needs a fix.
The in-repo script stays IDLE without
`data/synap/copper/paper/mom_weekly_fills.parquet` or a snapshot JSON.

**Implied upgrade.**

- Engine owns the monitor. Fix the job (fills present, snapshot
  schema, alert path). Do not replace it with Ch26 notebooks pointed
  at `us_equities_panel`.
- Ch26 is the **pattern language** (technical vs statistical failure,
  drift vs broken feed, circuit breakers, promotion gates). Use it to
  debug the 9/14 fail: was it missing fills (technical) or a kill
  trip (statistical)?
- Scripts must not rewrite the lock. `paper_monitor_mom_weekly.py`
  already encodes that.
- TV Pine is a cousin. A green Strategy Tester week is not a monitor
  pass and not a promote.

---

## 6. Process lessons that should change the next card

| Lesson | Do next time |
| ------ | ------------ |
| Soft IC is not a survivor | Ledger already: GraphRAG, EIA soft purge. Write **purge n / survivors** on every receipt |
| `sum_net` up + DD worse = SHELF | `S1_KAGGLE` (+8.55pp maxDD). KaggleMLEngine does not reopen without a DD hyp |
| GBM importance is CONTINUE, not a model launch | Importance ≠ WF. S2 GBM/XGB/RF and stretch XGB are **KILL**. v1 logistic shortlist h5 is **CONTINUE / promote=false** — do not promote it |
| Costed stub can lose to MOM | `S2_COSTED_STUB` RF worse than mom_log. Costs/risk before any "RF won IC" story |
| Crisis slices are small-n | Regime lock: do not rank on crisis Sharpe |
| Feature survival ≠ strategy survival | Ch20 teaching; copper already saw it (inventory IC vs frozen S3) |
| Multiple pots, one join | Engine @ 20:00Z. Bots that join locally create unauditable leakage |
| Token waste | !Flash!: read this folder + READMEs + `setup.yaml`, not 1.2k-line `research_workflow.py` |
| TV: one Pine per strategy | Chart TF is a Tester filter. Do not mint `_1D`/`_5D`/`_1M` copies. FRED hold 5/21/63 is an input, not three files |
| Isolated TF win = snooping | FRED 12h looked decent; 1D/5D/7D/1M/63D and ≤4h did not. Do not mint a 12h or 2h file |
| Split long vs short before judging | FRED 12h long-only +59.66% / 37.8% DD / PF 1.35 / 62/108. Two-sided was worse. Shorts were the drag |
| Burst windows ≠ a new TF | 2h long-only +12.5% / PF 1.11 over 2020–26. Paydays ~2020–early 2022 and ~2025–now; 2022 is giveback. Not a conflict feature |
| Empty Daily ≠ capital | Copper daily often opens Thursday night. Friday gate must use `dayofweek` or NY `time_close`, not bar-open NY Friday only |
| No CSV = no number | A TV “kill” without export + Properties is unvalidated. First measured A stays +12% / PF 1.02 |
| CRB is Ch8, not a new book | Overlay/crossover vs `TRJEFFCRB`. Same family as `cper_mom_*`. Copper sits inside CRB. One column + purge, not a third Pine and not a graph v0 node |

---

## 7. What “upgrade” does *not* mean

- Does not mean rewrite `0x_*` chapter notebooks as a Synap product.
- Does not mean a tenth case study named `copper_cu_ncu`.
- Does not mean promoting paper MOM_ONLY.
- Does not mean treating CME’s published GBM Sharpe as a copper result.
- Does not mean lifting `promote=false` in docs, scripts, or Pine.

The upgrade is **operating**: attach PIT columns to the Friday/CME
grid, screen with the book’s purge/WF/IC tools, and let Engine gate.
See [NEXT_ML4T_NATIVE_EXPERIMENTS.md](NEXT_ML4T_NATIVE_EXPERIMENTS.md).
Kaggle day 2026-09-20: [RECEIPT_2026-09-20_KAGGLE.md](RECEIPT_2026-09-20_KAGGLE.md).

---

## 8. 2026-09-20 — S2 GBM is KILL; v1 logistic shortlist h5 is CONTINUE

**What happened.** Deep Test S2 purged WF **v0** (panel sha
`35f1fce22bca…`) stamped **KILL**, 0 passers / 9 decisions (weekly-in-
position cost; `fwd_ret==0` labeled down). Same-day stretch Friday XGB
also **KILL**. v1 re-receipt (turnover cost, drop zeros) stamped
**CONTINUE** on `shortlist_log_h5` only: sum_net +0.161 / maxDD 0.226677
vs mom −0.256638 / 0.426748; sign 3/5; AUC 0.535; `promote=false`.
XGB/RF still KILL every horizon. SHFE ablation: `insufficient`. COT
ablation is not a passer (n=208).

**Implied upgrade.**

- Experiment C **GBM prune is closed**. Do not reopen XGB/RF or a new
  Kaggle S2 tree. Do not rerun v0 or v1.
- v1 CONTINUE is **not** a paper lock. Optional leftover is robustness
  seeds on the logistic passer. New copper hyp is Experiment A (free
  COT + logistic) then B (SHFE state) — see NEXT doc.
- Paper MOM_ONLY weekly is unchanged. Do not retune 0.60/0.40.
- Oil that day: downtime P0–P2 CONTINUE (P2 pack lost to mom on
  `sum_net`); TCN/TCNN KILL; Brent EIA logistic CONTINUE research-only.
  No oil paper lock.

---

## 9. 2026-09-20 — copper TV is learning, not a gate

**What happened.** Two v6 cousins (`NCU_S1_MOM_ONLY`, `NCU_MOM_FRED`)
ran on FX:COPPER. Paper-lock math (MR long/short) is the same frame;
z/sigmoid is not sklearn. Allow-long / allow-short inputs isolate
sides. Test A daily both-sides: +12.2% / 45.4% DD / PF 1.019 — fails
B&H. FRED 12h **long-only** (CSV `2c086`): +59.66% / 37.76% DD /
PF 1.35 / 62/108, all hold 21, 2014-07-18 → 2026-08-03. Two-sided 12h
was worse (shorts dragged). FRED 2h long-only 2020–26: +12.46% /
31.38% DD / PF 1.11 / 101/176 — two bull bursts, dead mid, 2022
giveback. Neighbors 1D/5D/7D/1M/63D and ≤4h failed. Operator saved
both scripts in TradingView.
Report: [REPORT_2026-09-20_COPPER_TV.md](REPORT_2026-09-20_COPPER_TV.md).

**Implied upgrade.**

- Intake Tester cards as notes. TV = search. Engine = held-out gate.
  Do not stamp CONTINUE/PROMOTE from Tester equity.
- Split long vs short before calling a card “nice.”
- Do not mint 12h/2h files. Do not name 2h bursts “conflict” without
  a dated PIT column.
- Keep one Pine per strategy. Do not port them onto oil.
- Next Engine work is still Experiment A, then optional Cell 1
  s2gate. Oil is a later sit-down; no oil Pine yet.
