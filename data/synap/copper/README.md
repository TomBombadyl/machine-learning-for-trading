# Synap copper (HG) research data

**NOT A PROMOTE.** Text contracts and docs for the FinPredict copper
research-to-paper pipeline. This directory is additive beside upstream
ML4T data loaders. It is not a chapter dataset and it is not a live book.

## What may be committed

- `README.md` (this file)
- `paper_mom_weekly_lock.json` — paper-only weekly MOM_ONLY decision lock
- `docs/` — locks, scorecard notes, regime notes, TradingView research ports

## What must not be committed

Large parquets and binaries are **research-machine only**. They stay on
the Engine / research host and must never land in git.

Typical untracked layout (all gitignored by `data/**/*.parquet`):

```
data/synap/copper/
  panels/hg_daily.parquet
  panels/hg_weekly.parquet
  paper/mom_weekly_fills.parquet
  regimes/regime_labels.parquet
```

If a parquet appears in `git status`, do not add it. The paper lock JSON
is the only data-side JSON that is whitelisted.

## Free-only

Scripts under `scripts/synap_copper/` do not call paid APIs. LME official
series and CFTC COT fidelity belong to the FinPredict Engine, not to a
TradingView port.

## Evidence / promote

The evidence loop is owned by the FinPredict Engine. Docs and scripts
here restate locks. **Never promote from this folder or from the scripts
alone.**
