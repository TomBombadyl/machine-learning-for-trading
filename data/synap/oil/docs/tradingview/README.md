# TradingView ports — Synap CL / Brent research

**NOT A PROMOTE.** TradingView scripts, if added later, are research
visualizations and crude cousins of Engine candidates. They are not
the FinPredict Engine, not paper fills, and not a live book.

**A TradingView proxy is not sklearn.** Pine `ta.*` transforms, TV
strategy equity curves, and community “ML” overlays are not the
FinPredict Engine model, not a scikit-learn estimator, and not a
locked feature store. Do not paste a TV backtest into a scorecard
row and call it `nymex_cl_21d` or `cl_brent_spread_63d`.

## What lives here

| File | Role |
| ---- | ---- |
| `README.md` (this file) | Proxy ≠ sklearn / Engine. No committed Pine yet. |

There is **no** committed Pine strategy for oil. Oil is not
paper-locked. Do not port copper `HG_MOM_ONLY_Weekly.pine` onto CL
or Brent and treat it as this lock.

## How to use (research sketch only)

1. If you open a TV chart, keep CL and Brent as **two** books. The
   lock is both plus the spread, not choose-one.
2. Free continuous starts (`CL1!` / `BRN1!` on TV, or yfinance
   `CL=F` / `BZ=F`) are not the Engine roll calendar.
3. Treat any TV backtest as a sketch. Commission defaults and
   100%-of-equity sizing are not a live risk policy.
4. Weekly Friday decisions and the **20:00Z** cutoff live in
   `CL_BRENT_WEEKLY_DECISION_LOCK.md` and the Engine — not in Pine.

## Never promote from TradingView

A green TV equity curve is not Engine evidence. Do not promote from
Pine, from this README, or from `scripts/synap_oil/` alone.
