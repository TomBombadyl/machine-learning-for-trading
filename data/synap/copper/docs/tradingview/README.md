# TradingView ports — Synap HG research

**NOT A PROMOTE.** TradingView scripts in this folder are research
visualizations and crude cousins of Engine candidates. They are not the
FinPredict Engine, not paper fills, and not a live book.

## What lives here

| File | Role |
| ---- | ---- |
| `HG_MOM_ONLY_Weekly.pine` | Pine v5 cousin of the paper MOM_ONLY weekly lock (daily chart, Friday signal, 5-bar hold). |
| `HG_MOM_COT_Weekly_README.md` | Why TV COT is not Engine COT. |
| `HG_DAILY_63D_LME_README.md` | Why LME work is Engine-first; TV HG is COMEX. |

There is no faithful Pine port of MOM_COT or LME-official features.
Those stay in the Engine.

## How to use

1. Open a COMEX HG daily chart if you want the MOM_ONLY cousin.
2. Paste `HG_MOM_ONLY_Weekly.pine` as a *strategy* (not an indicator).
3. Treat any TV backtest as a sketch. Commission 0.04% and 100% of
   equity are research defaults, not a live risk policy.
4. Paper lock, kill criteria, vol targeting, and dd-halt live in
   `HG_WEEKLY_DECISION_LOCK.md` and the Engine — not in Pine.

## Never promote from TradingView

A green TV equity curve is not Engine evidence. Do not promote from
Pine, from this README, or from `scripts/synap_copper/` alone.
