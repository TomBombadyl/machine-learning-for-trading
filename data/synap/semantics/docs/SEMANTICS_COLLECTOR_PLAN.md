# Semantics collector plan — SemanticsPot

**NOT A PROMOTE.** Plan for a point-in-time semantics collector
(SemanticsPot) that sits **beside** CopperPot, not inside it. This is
research scaffolding in the ML4T fork. It does not rewrite chapter
notebooks, does not share copper panel paths, and does not promote a
news-driven book.

Evidence, if any is later minted, is owned by the FinPredict Engine —
never by this document alone.

## Why a separate pot

CopperPot (`data/synap/copper/`) is HG price / positioning / LME
research. SemanticsPot is event language: mega-deals, tech shocks, and
policy hammers that may later become **PIT features** for other books.

Do not join the pots in this repo. No shared parquet, no copper script
importing semantics events, no "copper + news" promote story from a
local merge.

## Event families (v0)

| Family | What it is | Example (illustrative, not a label) |
| ------ | ---------- | ----------------------------------- |
| `mega_deal` | Control-changing M&A, mega-cap takeovers | Cash deal above a stated USD threshold |
| `tech_shock` | Discrete technology or platform shocks | Model release, outage, export-control chip rule |
| `policy_hammer` | Sudden policy / regulatory hammers | Tariff, sanction, emergency rule |

v0 does **not** include generic headline sentiment. If it is not one of
the three families, it is out of pot.

## PIT only

Every feature the collector may eventually emit must be point-in-time:

- `event_time` = when the world could have known (release / filing time)
- `asof_time` = feature availability after collect + parse lag
- no restatement leakage: later EDGAR amendments do not rewrite earlier
  as-of rows; they append with a new `asof_time`
- no copper close aligned to a timestamp the Engine could not have had

Scripts in this fork must not "fix" timestamps to make a backtest look
better.

## Free sources only

No paid news APIs, no scraped broker research, no secrets.

| Source | Use | Notes |
| ------ | --- | ----- |
| SEC EDGAR | 8-K / DEFA14A / 425-style deal filings | Identity via `EDGAR_IDENTITY` (User-Agent), not a key |
| GDELT | Public event / mention stream | Free; treat as noisy; PIT via GDELT date stamps |
| IR pages | Issuer press rooms already public | Manual or robots-respecting fetch; no login walls |

If a source needs a paid key, it is out of v0.

## Schema — `semantic_event_v0`

One event row. JSON or parquet on a research machine; **do not commit
event dumps**.

| Field | Type | Required | Notes |
| ----- | ---- | -------- | ----- |
| `schema` | string | yes | Constant `semantic_event_v0` |
| `event_id` | string | yes | Stable hash of source + uri + event_time |
| `family` | string | yes | `mega_deal` \| `tech_shock` \| `policy_hammer` |
| `event_time` | datetime (UTC) | yes | World-could-have-known time |
| `asof_time` | datetime (UTC) | yes | `>= event_time`; when the feature exists |
| `source` | string | yes | `edgar` \| `gdelt` \| `ir` |
| `source_uri` | string | yes | Canonical URL or EDGAR accession |
| `entities` | list[string] | yes | Tickers / orgs; empty list if unknown |
| `headline` | string | yes | Short text; no full copyrighted body |
| `payload` | object | no | Family-specific, PIT-safe scalars only |
| `confidence` | float | no | `[0, 1]` collector confidence, not a trade signal |
| `promote` | bool | yes | Always `false` in v0 |

`payload` examples (optional, still not a promote):

- mega_deal: `consideration_usd`, `deal_type`
- tech_shock: `shock_channel` (`model` / `outage` / `export_control`)
- policy_hammer: `instrument` (`tariff` / `sanction` / `emergency_rule`)

## Suggested research-machine paths (untracked)

```
data/synap/semantics/
  docs/SEMANTICS_COLLECTOR_PLAN.md   # this file (committed)
  events/semantic_event_v0.parquet   # research-machine only
  events/semantic_event_v0.jsonl     # research-machine only
```

## Collector stance

- Implement later as an Engine job or a free-only script beside
  `scripts/synap_copper/`, not as a rewrite of ML4T chapter downloaders.
- v0 is collect-and-store. No portfolio construction, no copper join,
  no auto-promote.
- **Never promote from SemanticsPot docs or from a local event file.**
