# TradingView ports — Synap HG research

**NOT A PROMOTE.** TradingView scripts in this folder are research
visualizations and crude cousins of Engine candidates. They are not the
FinPredict Engine, not paper fills, and not a live book.

## What lives here

All `.pine` files are **v6** (`//@version=6`). Official
[v5→v6 guide](https://www.tradingview.com/pine-script-docs/migration-guides/to-pine-version-6/):
`margin_long/short=0` keeps the v5 Tester (v6 default is 100);
FRED scripts set `dynamic_requests=false` so `request.security` stays
v5-stable. z/sigmoid cousins — not sklearn.

| File | Role | Tester |
| ---- | ---- | ------ |
| `NCU_MOM_ONLY_Weekly.pine` | S1 paper-lock cousin. Same math as HG twin. | **A first** — NCU or HG1!, Fri, 0.60/0.40, hold 5 |
| `HG_MOM_ONLY_Weekly.pine` | Same as NCU S1; HG title | Same as A |
| `NCU_MOM_FRED_MedLong_Weekly.pine` | MOM + TVC:VIX + TVC:US10Y; hold 21 or 63 | **B=21 / C=63** after A. thr 0.58/0.42 |
| `NCU_MOM_FRED_Weekly.pine` | Same proxies, hold 5 | **Skip** — h5 sign_stable FAIL |
| `HG_MOM_COT_Weekly_README.md` | Why TV COT is not Engine COT. | No Pine |
| `HG_DAILY_63D_LME_README.md` | Why LME work is Engine-first; TV HG is COMEX. | No Pine |

`CU_NCU_SHORTLIST_Weekly.pine` was on the Grokbot box but **was not
pasted** — not stored here. Do not invent it.

There is no faithful Pine port of MOM_COT or LME-official features.
Those stay in the Engine.

## How to use

1. Open NCU if listed, else COMEX HG1!, Daily.
2. Paste `NCU_MOM_ONLY_Weekly.pine` (or the HG twin) as a *strategy*.
3. Treat any TV backtest as a sketch. Commission 0.04% and 100% of
   equity are research defaults, not a live risk policy.
4. Paper lock, kill criteria, vol targeting, and dd-halt live in
   `HG_WEEKLY_DECISION_LOCK.md` and the Engine — not in Pine.

## Never promote from TradingView

A green TV equity curve is not Engine evidence. Do not promote from
Pine, from this README, or from `scripts/synap_copper/` alone.
