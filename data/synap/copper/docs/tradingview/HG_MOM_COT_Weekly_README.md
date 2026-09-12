# HG MOM_COT weekly — TradingView fidelity gap

**NOT A PROMOTE.** There is no committed Pine strategy for
`weekly_MOM_COT` or `daily_21d_MOM_COT` in this folder on purpose.

## COT fidelity gap on TV

The Engine feature is CFTC Commitment of Traders (public, weekly,
disaggregated / TFF as mapped for HG), aligned point-in-time to the
Friday release. TradingView "COT" overlays and community scripts are
typically:

- vendor-transformed or delayed versus the CFTC release the Engine uses
- mixed across legacy / disaggregated / financial reports
- not guaranteed to match HG contract mapping or revision handling
- not exportable as the Engine's PIT feature store

A TV chart that *looks* like COT is not `MOM_COT`. Scoring
`weekly_MOM_COT` or `daily_21d_MOM_COT` on TradingView would mint a
different feature and silently break the lock.

## What to do instead

- Build and score MOM_COT in the FinPredict Engine (free CFTC source).
- Use `scripts/synap_copper/multi_horizon_long_short_scorecard.py` only
  to restate the locked candidate list.
- Use `HG_MOM_ONLY_Weekly.pine` if you need a TV sketch of the
  MOM-only paper cousin (no COT).

## Never promote

Do not promote MOM_COT from TradingView, from a community COT pane, or
from these scripts alone. Evidence loop: FinPredict Engine.
