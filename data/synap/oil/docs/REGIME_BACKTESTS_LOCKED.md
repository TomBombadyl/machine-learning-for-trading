# Regime backtests — oil (no locked findings yet)

**NOT A PROMOTE.** Placeholder for locked CL + Brent regime notes.
Reprinted by `scripts/synap_oil/regime_backtests_locked.py`.

Oil has **no locked qualitative regime findings** in this scaffold.
Do not copy copper `MOM_ONLY` / `MOM_COT` labels onto CL or Brent.
Do not treat a local yfinance slice as a locked regime map.

Crisis slices, when they exist, will be **ugly / small-n**. Do not
treat them as powered evidence. The FinPredict Engine owns the
evidence loop.

## Reserved (unlocked)

| Regime | Locked reading |
| ------ | -------------- |
| Strong bull | *not locked* |
| High vol | *not locked* |
| Bear | *not locked* |
| Crisis | *not locked* — expect ugly / small-n |

The script reprints an empty `locked_findings` map. That is the
contract until the Engine locks oil regimes.

## How to use this stub

- Scripts may reprint the empty map and, on a research machine, note
  that a `regimes/regime_labels.parquet` file exists.
- Scripts must not overwrite this document from a local recompute.
- **Never promote from these notes or from the regime script alone.**
