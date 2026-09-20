# TradingView ports — one Pine per strategy

**NOT A PROMOTE.** z/sigmoid cousins. Not sklearn. Never promote unless
it beats buy-and-hold (operator rule) **and** Engine stamps promote
(it will not from TV).

Switch the **chart** timeframe yourself: **1D / 5D / 21D / 63D / 1M**.
Lookbacks 5/21/63 are chart bars, not calendar days. Uncheck Friday
on anything that is not Daily.

| Click | Strategy | Why a separate file |
| ----- | -------- | ------------------- |
| [NCU_S1_MOM_ONLY.pine](NCU_S1_MOM_ONLY.pine) | Paper MOM_ONLY MR | Test A. 0.60/0.40, hold 5. Rally→SHORT, dip→LONG. |
| [NCU_MOM_FRED.pine](NCU_MOM_FRED.pine) | MOM + VIX/US10Y | Grokbot B/C. Same MR. Set hold to 5 / 21 / 63. Needs `TVC:VIX` + `TVC:US10Y`. |
| [HG_MOM_ONLY_Weekly.pine](HG_MOM_ONLY_Weekly.pine) | Lock twin (v5) | Scaffold / paper-lock cousin. Do not “upgrade” this file. |

Both v6 scripts are **long and short**. Settings: uncheck **Allow longs**
or **Allow shorts** to isolate a side. No extra files.

Friday on Daily uses `dayofweek` or NY `time_close` (copper daily
often opens Thursday night). Uncheck Friday off Daily.

12h FRED **long-only** was the nicest sketch (+59.66% / PF 1.35);
neighbors failed. 2h long-only is weaker (+12.5% / PF 1.11) with
two bull bursts. Do not add a 12h or 2h file. See
`docs/synap/REPORT_2026-09-20_COPPER_TV.md`.

Operator has both v6 scripts saved in TradingView. Update here, then
copy-paste.

Growable search log (not a gate):
[TV_RESEARCH_ONTOLOGY.md](TV_RESEARCH_ONTOLOGY.md) ·
[tv_cards.tsv](tv_cards.tsv). Append a row per Tester card.

No per-TF copies. COT/LME still README-only. Oil TV has no Pine.

