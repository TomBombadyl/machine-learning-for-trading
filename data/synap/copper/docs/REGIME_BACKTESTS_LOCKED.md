# Regime backtests — locked qualitative findings

**NOT A PROMOTE.** Locked HG regime notes. Reprinted by
`scripts/synap_copper/regime_backtests_locked.py`. These are research
memory, not a live book and not a re-optimize invitation.

Crisis slices are **ugly / small-n**. Do not treat them as powered
evidence. The FinPredict Engine owns the evidence loop.

## MOM_ONLY

| Regime | Locked reading |
| ------ | -------------- |
| Strong bull | **Strong** |
| High vol | **Strong** |
| Bear | **Weak** |
| Crisis | Ugly / small-n |

MOM_ONLY (including the paper weekly lock cousin) is a bull / high-vol
sleeve. It is not a bear-market workhorse.

## MOM_COT

| Regime | Locked reading |
| ------ | -------------- |
| Strong bull | OK |
| High vol | OK |
| Bear | **More bear-tolerant** than MOM_ONLY |
| Crisis | Ugly / small-n |

COT positioning adds bear tolerance relative to MOM_ONLY. That does
**not** make MOM_COT a crisis strategy and does not promote it.

## Crisis / small-n

Crisis windows in the HG sample are short. Pathwise results swing on a
handful of weeks. Locked stance: report them as ugly / small-n, do not
rank candidates on crisis Sharpe, do not promote from a crisis anecdote.

## How to use this lock

- Scripts may reprint these labels and, on a research machine, note that
  a `regimes/regime_labels.parquet` file exists.
- Scripts must not overwrite this document from a local recompute.
- **Never promote from these notes or from the regime script alone.**
