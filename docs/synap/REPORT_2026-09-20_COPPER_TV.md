# Report — 2026-09-20 copper TradingView initial tests

**NOT A PROMOTE.** First-pass Tester sketches. Learning only. Not
sklearn. Not Engine evidence. Not a paper-lock change. Oil was not
tested.

Operator rule: never promote unless it beats buy-and-hold. Engine
rule: TV cannot stamp `promote=true`.

---

## What this day was

Copper only. Two Pine cousins of the paper MOM_ONLY lock, run on
TradingView so the team could see long/short behavior. The Engine
ledger from the same calendar day (S2 v0 KILL, v1 `shortlist_log_h5`
CONTINUE / `promote=false`) is unchanged:
[RECEIPT_2026-09-20_KAGGLE.md](RECEIPT_2026-09-20_KAGGLE.md).

These Tester cards do **not** overwrite that ledger.

---

## Files that stay in the repo

One Pine per **strategy**. Chart timeframe is a Tester filter
(1D / 5D / 12h / 21D / 63D / 1M). Lookbacks 5/21/63 are chart bars,
not calendar days.

| File | Role |
| ---- | ---- |
| `data/synap/copper/docs/tradingview/NCU_S1_MOM_ONLY.pine` | Test A. Paper MOM_ONLY MR cousin. Pine v6. 0.60/0.40, hold 5. |
| `data/synap/copper/docs/tradingview/NCU_MOM_FRED.pine` | Test B/C. Same MR + VIX/US10Y sketch weights. Hold input 5/21/63. |
| `data/synap/copper/docs/tradingview/HG_MOM_ONLY_Weekly.pine` | Lock twin. Pine v5. Scaffold test pins this file. Do not “upgrade” it. |

Operator saved both v6 scripts in the TradingView account. Future
edits: change the repo file, copy-paste into TV.

Deleted on purpose: per-TF copies (`*_1D` / `*_5D` / `*_1M`) and the
old `NCU_*_Weekly.pine` names. COT/LME stay README-only.

---

## Math that was checked

Both operator scripts are **long and short** mean-reversion, matching
the paper lock frame:

- Negate 5/21/63 momentum → z → sigmoid.
- Rally → proba drops → **short** at ≤0.40 (A) or ≤0.42 (FRED).
- Dip → proba rises → **long** at ≥0.60 (A) or ≥0.58 (FRED).
- Flat in between. No pyramid.

Not Engine: z/sigmoid ≠ sklearn logistic. FRED VIX/US10Y weights are
a sketch (`TVC:VIX`, `TVC:US10Y`), not the Kaggle fit.

Hold timer resets on a new long or short so a flip does not inherit
the old bar count.

Friday gate (v6): `dayofweek == friday` **or** NY `time_close` is
Friday. Copper daily bars often **open Thursday night**; gating on
bar-open NY Friday produced an empty Daily Tester. That was not a
capital/qty problem. Uncheck Friday on non-daily charts.

---

## Measured Tester cards (operator)

Symbol on the exports/screens was **FX:COPPER** (TV CFD). Related
metal, not a proof that `COMEX:HG1!` is identical. Date windows are
Tester windows, not the Engine Friday panel.

| Card | Script | Chart | Sides | Net | Max DD | Trades / win | PF | Read |
| ---- | ------ | ----- | ----- | --- | ------ | ------------ | -- | ---- |
| A | MOM_ONLY | 1D | both | **+12.2%** | **45.4%** | 338/651 | **1.019** | 2012-02-24 → 2026-09-18. CSV. Fails B&H. |
| A2 | MOM_ONLY | 1D | both | **~+12.74%** | **~28.6%** | **191/343 (~56%)** | unread | 2011-08-24 → 2026-09-17. Screenshot after Friday/`time_close` + side toggles. PF not readable. |
| FRED neighbors | MOM_FRED | 1D, 5D, 7D, 1M, 63D, ≤4h | both | operator: **not good** | — | — | — | No five-number cards. |
| FRED 12h both | MOM_FRED | **12h** | both | decent vs A | **~46%** | — | **~1.29** | 2011-08-24 → 2026-09-18. Dead years, then 2021–26. |
| FRED 12h long | MOM_FRED | **12h** | **long only** | **+$59,664 / +59.66%** | **37.76%** | **62/108 (57.4%)** | **1.35** | CSV: 108 `L` only, hold 21 every trade, 2014-07-18 → 2026-08-03. Shorts were the drag vs two-sided. Tester B&H near flat. |
| FRED 2h long | MOM_FRED | **2h** | **long only** | **+$12,459 / +12.46%** | **31.38%** | **101/176 (57.4%)** | **1.11** | Tester 2020-01-02 → 2026-09-18. Two bursts (~2020–early 2022, ~2025–now). Dead 2022–24. 2022 is a **giveback**, not a conflict payday. |

CSVs operator-local (do not git-add):

- `C:\Users\tobin\Downloads\NCU_S1_MOM_ONLY_Weekly_(interim_PAPER)_FX_COPPER_2026-09-20_9c4fa.csv`
- `C:\Users\tobin\Downloads\NCU_MOM_FRED_(PAPER)_FX_COPPER_2026-09-20_2c086.csv` (12h long-only)

**How to read this.** A is “not terrible, not a promote.” FRED 12h
long-only is the nicest **sketch** so far; shorts were eating the
two-sided book. 12h and 2h lookbacks are chart bars, not the weekly
paper lock. Neighbor TFs failed = **search overfitting**, not a
found edge. Do not mint a 12h or 2h file. 2h “nice periods” are two
copper bulls, not a dated conflict feature. Short-only 12h CSV is
still missing.

**Unvalidated operator note (stop-for-now).** A later “weekly
interim” Daily both-sides run *looked* like it killed it. **No CSV,
no Properties, no five numbers.** Do not store a kill card. Fear of
accuracy is correct. TV can print a monster equity from 100%-of-equity
compounding, missing `vol_target`/`dd_halt`, FX:COPPER ≠ HG, z/sigmoid
≠ sklearn, or a qty/commission setting. First measured A is still
+12% / PF 1.02. Re-open only with export + Properties.

---

## Why a TV “kill” is not Engine truth

- Pine is a cousin: z/sigmoid, not the locked logistic.
- Sizing is 100% of equity. No paper `vol_target` or `dd_halt`.
- `FX:COPPER` ≠ `COMEX:HG1!` ≠ Coinbase CU/NCU.
- Lookbacks are **chart bars**. 12h/2h are different strategies.
- Isolated TF or isolated side with dead neighbors is search overfit.
- Tester B&H is a pane overlay, not the Engine baseline.

---

## Process upgrades (keep)

1. **One Pine per distinct strategy.** Chart TF is a filter. FRED
   hold 5/21/63 is an input, not three files.
2. **TV is intake, not a gate.** Log the five numbers. Do not write
   a ledger CONTINUE/PROMOTE from Tester equity.
3. **Operator B&H rule + Engine `promote=false`.** Both must fail
   closed. A +12% / 45% DD / PF 1.02 card is a sketch.
4. **Empty Daily first:** Friday timestamp, then symbol on the
   *chart header*, then qty. Not “add symbol” in the picker.
5. **Copy-paste path.** Repo is source. TV cloud copies are the
   runtime. Do not fork a third filename in the folder.
6. **Oil is a later sit-down.** `data/synap/oil/docs/tradingview/`
   has no Pine. Do not port these copper scripts onto CL/Brent.

---

## What we did *not* do

- Flip paper MOM_ONLY 0.60/0.40, `vol_target`, or `dd_halt`.
- Mint an oil paper lock or oil Pine.
- Treat 12h FRED as a candidate.
- New Kaggle tree. Cell 2 GAT still blocked.
- Promote.

---

## Next (when we come back)

Copper Engine work is still the book, not another TF sweep.

| Priority | Do | Do not |
| -------- | -- | ------ |
| 1 | Experiment **A** — HG + free COT, IC → purge, logistic only if survivors. | New copper case study. Paid LME. GBM reopen. |
| 2 | If Kaggle time: paste `scripts/synap_copper/copper_gnn_s2gate_kaggle.py` as Cell 1 on the **existing** S2 notebook. | Cell 2 until that memo is family CONTINUE. New notebook tree. |
| 3 | Optional leftover: `DEEP_TEST_MODE=robustness` on v1 logistic only. | Rerun v0/v1. Raise trees. |
| 4 | Oil: own session. Read `CL_BRENT_WEEKLY_DECISION_LOCK.md`. Brent EIA logistic is CONTINUE research-only. | Port NCU pines onto CL/BRN. Invent `OIL_P3`. Mint `paper_*_lock.json`. |
| 5 | TV only if we need another **cousin of a locked family**. Re-paste the two saved scripts. | Per-TF copies. 12h special file. |

Pickup order for the next agent:
[RESEARCH_HANDOFF_PROMPT.md](RESEARCH_HANDOFF_PROMPT.md).
