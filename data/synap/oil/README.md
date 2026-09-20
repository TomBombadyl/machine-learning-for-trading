# Synap oil (CL + Brent) research data

**NOT A PROMOTE.** Text contracts and docs for the FinPredict oil
research pipeline. This directory is additive beside upstream ML4T data
loaders. It is not a chapter dataset and it is not a live book.

Oil is **not paper-locked**. Do not commit `paper_*_weekly_lock.json`
until the Engine paper-locks. `.gitignore` already whitelists that
pattern so a future lock JSON can be committed without lifting the
`data/**/*.json` ignore.

## What may be committed

- `README.md` (this file)
- `docs/` — vertical lock, scorecard notes, regime notes, TradingView
  caveats, SemanticsOilPot pointer

## What must not be committed

Large parquets and binaries are **research-machine only**. They stay on
the Engine / research host and must never land in git.

Typical untracked layout (all gitignored by `data/**/*.parquet`):

```
data/synap/oil/
  panels/cl_brent_weekly.parquet
  paper/weekly_fills.parquet
  regimes/regime_labels.parquet
```

If a parquet appears in `git status`, do not add it. Do not commit EIA
API keys, `.env` secrets, or paid extracts.

## OilPot vs SemanticsOilPot

- **OilPot** (this tree) = oil-market alt features only (prices,
  term structure, inventory/positioning when free or Engine-side).
- **SemanticsOilPot** = sanctions / SPR / energy M&A / policy / macro
  PIT features only. Narrative lane lives under
  `data/synap/semantics/oil/` (research-machine; do not invent a full
  tree in this fork). See `docs/SEMANTICS_OILPOT.md`.
- The FinPredict Engine joins the two on `decision_date` with a
  **20:00Z** cutoff. Scripts here do not join the pots.

## Free-only

Scripts under `scripts/synap_oil/` do not call paid APIs. Free price
start is yfinance `CL=F` (NYMEX CL continuous) and `BZ=F` (ICE Brent
continuous). Budget-lifted sources stay Engine-side.

## Evidence / promote

The evidence loop is owned by the FinPredict Engine. Docs and scripts
here restate the locked CL+Brent hypothesis. **Never promote from this
folder or from the scripts alone.**

2026-09-20 Kaggle pointer:
[`docs/RECEIPT_2026-09-20_KAGGLE.md`](docs/RECEIPT_2026-09-20_KAGGLE.md)
(full tables in
[`docs/synap/RECEIPT_2026-09-20_KAGGLE.md`](../../../docs/synap/RECEIPT_2026-09-20_KAGGLE.md)).
