# Synap copper research scripts

**NOT A PROMOTE.** Additive FinPredict / Synap Garden research helpers
beside upstream ML4T. They do not rewrite chapter notebooks, they do not
own the evidence loop, and they must never be treated as a live or paper
promotion path on their own.

## How to run

From the repository root, inside the ML4T image:

```bash
docker compose run --rm ml4t python scripts/synap_copper/<script>.py
```

Examples:

```bash
docker compose run --rm ml4t python scripts/synap_copper/multi_horizon_long_short_scorecard.py
docker compose run --rm ml4t python scripts/synap_copper/regime_backtests_locked.py
docker compose run --rm ml4t python scripts/synap_copper/paper_monitor_mom_weekly.py
```

Each script accepts `--help`. Outputs default to stdout; pass `--output`
to write a JSON report under a path you choose. Do not commit generated
reports or research parquets.

## Data

Research inputs and generated artifacts live under `data/synap/copper/`.

- **Committed:** lock JSON, docs, TradingView research ports (text only).
- **Research-machine only (never commit):** large parquets, fills, panels,
  COT/LME extracts. See `data/synap/copper/README.md`.

## Constraints

- **Free-only.** No paid API keys, no Databento/LME paid pulls from these
  scripts. CFTC COT (public) and Engine-exported free panels are the
  intended inputs.
- **Evidence loop is owned by the FinPredict Engine.** These scripts
  score, reprint locked findings, or monitor a paper lock. They do not
  mint evidence, do not change the lock, and do not promote.
- **Never promote from scripts alone.** A green local scorecard is not a
  promote. Promotion, if it ever happens, is an Engine evidence-loop
  decision recorded outside this fork.

## Scripts

| Script | Contract |
| ------ | -------- |
| `multi_horizon_long_short_scorecard.py` | Locked research candidates in `data/synap/copper/docs/MULTI_HORIZON_LONG_SHORT_SCORECARD.md` |
| `regime_backtests_locked.py` | Locked regime notes in `data/synap/copper/docs/REGIME_BACKTESTS_LOCKED.md` |
| `paper_monitor_mom_weekly.py` | Paper-only weekly MOM_ONLY lock in `data/synap/copper/docs/HG_WEEKLY_DECISION_LOCK.md` and `paper_mom_weekly_lock.json` |

Shared candidate IDs and kill-criteria helpers live in `contract.py`.
That module is also **not a promote**.
