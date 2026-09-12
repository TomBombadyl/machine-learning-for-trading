# Multi-horizon long/short scorecard — oil research skeleton

**NOT A PROMOTE.** Locked CL + Brent research-hypothesis set for the
FinPredict scorecard. `scripts/synap_oil/multi_horizon_long_short_scorecard.py`
restates this list. Until Engine locks exist the script is a **stub**:
it reprints the candidate grid and exits 0 without research parquets.

A completed scorecard is research output. It is not a promotion, not a
paper book, and not Engine evidence by itself.

The evidence loop is owned by the FinPredict Engine. Free-only inputs
only from these scripts.

## Locked hypothesis (both books)

See `CL_BRENT_WEEKLY_DECISION_LOCK.md`. Weekly Friday decisions,
**20:00Z** cutoff. Labels are multi-horizon absolute direction on each
book **plus** the CL–Brent spread.

| Candidate id | Universe | Horizon | Label | Role |
| ------------ | -------- | ------- | ----- | ---- |
| `nymex_cl_5d` | `NYMEX_CL` | 5d | absolute direction | Research skeleton |
| `nymex_cl_21d` | `NYMEX_CL` | 21d | absolute direction | Research skeleton |
| `nymex_cl_63d` | `NYMEX_CL` | 63d | absolute direction | Research skeleton |
| `ice_brent_5d` | `ICE_BRENT` | 5d | absolute direction | Research skeleton |
| `ice_brent_21d` | `ICE_BRENT` | 21d | absolute direction | Research skeleton |
| `ice_brent_63d` | `ICE_BRENT` | 63d | absolute direction | Research skeleton |
| `cl_brent_spread_5d` | `CL_BRENT_SPREAD` | 5d | spread direction | Research skeleton |
| `cl_brent_spread_21d` | `CL_BRENT_SPREAD` | 21d | spread direction | Research skeleton |
| `cl_brent_spread_63d` | `CL_BRENT_SPREAD` | 63d | spread direction | Research skeleton |

There is **no** `paper_*` cousin row. Oil is not paper-locked.

## Scoring rules (research)

- Long/short, not long-only. Flat when the Engine proxy is between
  thresholds the Engine later calibrates. This fork does not invent
  thresholds.
- Missing research-machine parquets → skeleton mode (candidate list
  only). That is not a failed promote; there is nothing to promote.
- Free price start: yfinance `CL=F` / `BZ=F`. Not a substitute for the
  Engine continuous series or roll calendar.

## TradingView / sklearn caveats

- A TradingView Pine **proxy is not sklearn** and is not the Engine
  model. See `tradingview/README.md`.
- Do not score this grid on a single CL or Brent TV chart and call it
  the lock.

## Never promote from this document

Do not graduate any row to paper or live because a local scorecard
looked good. Promotion, if it ever happens, is an Engine evidence-loop
decision recorded outside this ML4T fork.
