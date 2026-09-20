# API budget — Tavily (September 2026)

**promote=false.** Operator notice for all Synap / FinPredict agents on
this fork. Not a research hyp.

## Status (2026-09-20)

Tavily emailed Dylan T.: account at **~80% of September 2026 usage**.
~10 days left in the month. Hitting the credit limit needs a manual
plan upgrade or PAYGO. Dashboard:
[Tavily Dashboard](https://app.tavily.com/).

## Rules for agents (rest of September)

1. **Do not call Tavily by default.** Prefer in-repo docs, official
   free URLs, Hugging Face MCP, already-fetched cards, and Kaggle
   receipts already on disk.
2. **One justified call max** per task, and only if the answer is not
   already in `docs/synap/` or a file opened this session.
3. **No** exploratory crawls, map/crawl sweeps, parallel Tavily batches,
   or “just in case” research runs.
4. **No** re-running prior Tavily research IDs to refresh the same
   question (e.g. asset-FM inventory already in
   [ASSET_FM_RESOURCE_MAP.md](ASSET_FM_RESOURCE_MAP.md)).
5. If blocked without Tavily, write `unknown — look up <page>` / use
   free sources and stop. Do not burn credits to unblock cosmetics.
6. Reset expectation: October allotment is a new period; do not assume
   PAYGO is enabled.

## Where this binds

- Cloud / desktop agents reading this repo
- !Flash! context packs
- Any skill that wraps Tavily (`tavily_search`, `tavily_research`,
  `tavily_crawl`, `tavily_extract`, `tavily_map`)

Copper GNN / S2 tabular Kaggle work does **not** need Tavily.
