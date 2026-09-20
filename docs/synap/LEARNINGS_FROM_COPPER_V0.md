# Learnings from copper v0 — implied ML4T upgrades

**promote=false.** What copper work through 2026-09-18 changes about
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
| GBM importance is CONTINUE, not a model launch | Prune features on the frozen S2 frame; still beat logistic; no DL |
| Costed stub can lose to MOM | `S2_COSTED_STUB` RF worse than mom_log. Costs/risk before any "RF won IC" story |
| Crisis slices are small-n | Regime lock: do not rank on crisis Sharpe |
| Feature survival ≠ strategy survival | Ch20 teaching; copper already saw it (inventory IC vs frozen S3) |
| Multiple pots, one join | Engine @ 20:00Z. Bots that join locally create unauditable leakage |
| Token waste | !Flash!: read this folder + READMEs + `setup.yaml`, not 1.2k-line `research_workflow.py` |

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
