# HG weekly decision lock — paper MOM_ONLY

**NOT A PROMOTE.** Paper-only weekly MOM_ONLY lock for COMEX HG. This
file is the prose twin of `data/synap/copper/paper_mom_weekly_lock.json`.
The FinPredict Engine owns the evidence loop. Scripts under
`scripts/synap_copper/` may monitor the lock; they must not change it and
must not promote.

## Scope

| Field | Locked value |
| ----- | ------------ |
| Asset | HG (copper) |
| Book | paper only |
| Model family | `MOM_ONLY` |
| Frame | mean-reversion (MOM signs negated, same as Engine) |
| Horizon / cadence | weekly |
| Candidate id | `paper_MOM_ONLY_weekly` |

This is **not** a live promote, not a research-candidate promote, and not
a TradingView-as-Engine substitute. The Pine port
`tradingview/HG_MOM_ONLY_Weekly.pine` is a cousin approximation (daily
chart, Friday signal, 5-bar hold proxy). Operator Tester file is
`tradingview/NCU_S1_MOM_ONLY.pine` (v6, same MR math; switch chart TF).

## Thresholds

| Side | Probability threshold |
| ---- | --------------------- |
| Long | **0.60** |
| Short | **0.40** |

Signal only when the model proxy is at or beyond the threshold. No
pyramiding. Flat otherwise.

## Risk overlay

Locked together; do not drop one in paper:

- **`vol_target`** — scale paper notionals to the Engine vol target.
- **`dd_halt`** — halt new risk when the Engine drawdown halt fires.

## Kill criteria

Any one trip kills the paper book (flatten and stop). Monitor cadence is
weekly, aligned with the signal.

1. **26-week drawdown > 15%** — `max_drawdown_26w > 0.15`
2. **Sum of net returns < -5%** — `sum_net < -0.05`
3. **Lose to MR two consecutive reads** — paper underperforms the
   mean-reversion baseline on two consecutive monitor reads
   (`lose_to_mr_consecutive_reads >= 2`)

`scripts/synap_copper/paper_monitor_mom_weekly.py` applies these rules to
an optional snapshot. A kill is a paper halt, not a promote decision
and not a rewrite of this lock.

## Explicit non-goals

- **Never promote** this lock to live or to a larger book from docs,
  scripts, or TradingView.
- Do **not** treat a TV backtest as Engine evidence.
- Do **not** relax thresholds, drop `vol_target` / `dd_halt`, or edit
  kill criteria in this fork without a new Engine lock.
