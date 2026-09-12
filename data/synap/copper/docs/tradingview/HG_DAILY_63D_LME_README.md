# HG daily 63d LME — Engine-first

**NOT A PROMOTE.** There is no committed Pine strategy for
`daily_63d_LME` or `weekly_MOM_LME` in this folder on purpose.

## LME is Engine-first

`daily_63d_LME` is defined on **LME official** copper (cash / 3M and
Engine-derived term-structure features), not on COMEX HG. TradingView
HG is the CME/COMEX contract:

- different venue, calendar, and roll
- no LME official cash/3M print as the Engine feature
- COMEX–LME basis is itself a research series, not a drop-in LME proxy

Running a 63-day momentum on TV HG and labeling it `daily_63d_LME`
would be a different candidate.

## What to do instead

- Pull and score LME official series in the FinPredict Engine
  (research-machine; do not commit parquets).
- Keep TV for COMEX visualization or for the MOM_ONLY weekly cousin
  (`HG_MOM_ONLY_Weekly.pine`).
- Restate the locked set with
  `scripts/synap_copper/multi_horizon_long_short_scorecard.py`.

## Never promote

Do not promote LME candidates from a COMEX TradingView chart or from
these scripts alone. Evidence loop: FinPredict Engine.
