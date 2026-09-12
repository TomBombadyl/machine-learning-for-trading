# Multi-horizon long/short scorecard — locked research candidates

**NOT A PROMOTE.** Locked HG research-candidate set for the FinPredict
scorecard. `scripts/synap_copper/multi_horizon_long_short_scorecard.py`
restates this list. A completed scorecard is research output. It is not
a promotion, not a live book, and not Engine evidence by itself.

The evidence loop is owned by the FinPredict Engine. Free-only inputs
only from these scripts.

## Locked candidates

| Candidate id | Horizon | Features | Lookback | Role |
| ------------ | ------- | -------- | -------- | ---- |
| `daily_63d_LME` | daily | LME | 63d | Research. LME official series is Engine-first. |
| `daily_21d_MOM_COT` | daily | MOM + COT | 21d | Research. CFTC COT fidelity is Engine-side. |
| `daily_63d_MOM_LME` | daily | MOM + LME | 63d | Research. |
| `weekly_MOM_COT` | weekly | MOM + COT | weekly | Research. TV COT gap applies. |
| `weekly_MOM_LME` | weekly | MOM + LME | weekly | Research. LME Engine-first. |
| `paper_MOM_ONLY_weekly` | weekly | MOM only | weekly | **Paper lock cousin.** See `HG_WEEKLY_DECISION_LOCK.md`. Still not a promote. |

## Scoring rules (research)

- Long/short, not long-only. Flat when the proxy is between thresholds.
- Paper MOM_ONLY weekly uses the locked 0.60 / 0.40 thresholds and the
  `vol_target` + `dd_halt` overlay.
- Research candidates may use Engine-calibrated thresholds; this fork
  does not invent new ones.
- Missing research-machine parquets → skeleton mode (candidate list
  only). That is not a failed promote; there is nothing to promote.

## TradingView / COMEX caveats

- `daily_63d_LME` and `weekly_MOM_LME` need Engine LME. TV HG is COMEX.
  See `tradingview/HG_DAILY_63D_LME_README.md`.
- COT features need Engine CFTC series. TV COT overlays are not
  faithful. See `tradingview/HG_MOM_COT_Weekly_README.md`.

## Never promote from this document

Do not graduate any row to live because a local scorecard looked good.
Promotion, if it ever happens, is an Engine evidence-loop decision
recorded outside this ML4T fork.
