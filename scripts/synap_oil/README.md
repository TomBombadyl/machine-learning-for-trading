# Synap oil research scripts

**NOT A PROMOTE.** Additive FinPredict / Synap Garden research helpers
beside upstream ML4T. They do not rewrite chapter notebooks, they do not
own the evidence loop, and they must never be treated as a live or paper
promotion path on their own.

This is the oil twin of [`scripts/synap_copper/`](../synap_copper/).
There is **no oil paper lock yet**. Do not mint `promote: true` here.

## How to run

From the repository root, inside the ML4T image:

```bash
docker compose run --rm ml4t python scripts/synap_oil/<script>.py
```

Examples:

```bash
docker compose run --rm ml4t python scripts/synap_oil/multi_horizon_long_short_scorecard.py
docker compose run --rm ml4t python scripts/synap_oil/regime_backtests_locked.py
```

Each script accepts `--help`. Outputs default to stdout; pass `--output`
to write a JSON report under a path you choose. Do not commit generated
reports or research parquets.

## Data

Research inputs and generated artifacts live under `data/synap/oil/`.

- **Committed:** docs (vertical lock, scorecard, regime notes, TradingView
  caveats). No `paper_*_weekly_lock.json` until the Engine paper-locks.
- **Research-machine only (never commit):** large parquets, fills, panels,
  EIA extracts, secrets, EIA API keys. See `data/synap/oil/README.md`.

`SemanticsOilPot` (narrative / PIT event lane) lives under
`data/synap/semantics/oil/` when collected. That tree is separate from
OilPot intel. The Engine joins on `decision_date` with a **20:00Z**
cutoff. This folder does not invent a full semantics tree.

## Constraints

- **Free-only** until a budget is lifted. No paid API keys, no EIA key
  in-repo, no Databento/paid pulls from these scripts. Free price start
  is yfinance `CL=F` / `BZ=F`.
- **Evidence loop is owned by the FinPredict Engine.** These scripts
  restate the locked CL+Brent hypothesis or reprint empty regime notes.
  They do not mint evidence, do not change a lock, and do not promote.
- **Never promote from scripts alone.** A green local scorecard is not a
  promote. Promotion, if it ever happens, is an Engine evidence-loop
  decision recorded outside this fork.

## Scripts

| Script | Contract |
| ------ | -------- |
| `multi_horizon_long_short_scorecard.py` | Skeleton until Engine locks exist. Restates `data/synap/oil/docs/MULTI_HORIZON_LONG_SHORT_SCORECARD.md` |
| `regime_backtests_locked.py` | Skeleton. Restates `data/synap/oil/docs/REGIME_BACKTESTS_LOCKED.md` (no locked oil regimes yet) |

There is **no** `paper_monitor_*` here: oil is not paper-locked. A
monitor that required a lock would be the wrong cousin. Shared universe
IDs and kill-criteria helpers live in `contract.py`. That module is
also **not a promote**; the kill helper never sets `promote: true`.
