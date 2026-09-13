# SemanticsOilPot — pointer (not a collector tree)

**NOT A PROMOTE.** Short pointer only. Copper already committed a
shared SemanticsPot plan at
[`data/synap/semantics/docs/SEMANTICS_COLLECTOR_PLAN.md`](../../semantics/docs/SEMANTICS_COLLECTOR_PLAN.md).
This fork does **not** invent a parallel oil semantics tree in git.

## Where the lanes live

| Lane | Path | Role |
| ---- | ---- | ---- |
| OilPot | `data/synap/oil/` | Oil-market alt features only |
| SemanticsOilPot | `data/synap/semantics/oil/` | Narrative / PIT lane: sanctions, SPR, energy M&A, policy, macro |
| Shared plan | `data/synap/semantics/docs/SEMANTICS_COLLECTOR_PLAN.md` | v0 families, PIT rules, free sources |

`data/synap/semantics/oil/` is **research-machine** when events exist.
Do not commit event dumps, parquets, or secrets.

## Join contract (Engine, not this fork)

The FinPredict Engine joins OilPot and SemanticsOilPot on
`decision_date` with the locked **20:00Z** cutoff. Scripts under
`scripts/synap_oil/` must not join the pots and must not promote a
“oil + news” book.

## Never promote

Never promote from SemanticsOilPot docs, from a local event file, or
from these oil scripts alone.
