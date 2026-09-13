# CL + Brent weekly decision lock — vertical hypothesis

**NOT A PROMOTE.** First vertical lock for **both** NYMEX CL and ICE
Brent (not choose-one). This is a research-hypothesis lock, **not** a
paper lock. There is no `paper_*_weekly_lock.json` in this tree yet.
The FinPredict Engine owns the evidence loop and any later promote /
kill decision. Scripts under `scripts/synap_oil/` may restate this
document; they must not change it and must not promote.

## Scope

| Field | Locked value |
| ----- | ------------ |
| Universe | **CL + Brent continuous** — `NYMEX_CL` and `ICE_BRENT`, plus `CL_BRENT_SPREAD` |
| Free price start | yfinance `CL=F` / `BZ=F` |
| Book | research only (no paper lock yet) |
| Cadence | weekly **Friday** decisions |
| Decision cutoff | **20:00Z** |
| Labels | multi-horizon **absolute direction** on each book **plus** the CL–Brent spread |
| Horizons | **5d / 21d / 63d** |
| Feature panel join | long `decision_date` × universe (`NYMEX_CL` / `ICE_BRENT` / `CL_BRENT_SPREAD`) |
| Feature pots | OilPot = oil-market alt features only; SemanticsOilPot = sanctions / SPR / energy M&A / policy / macro PIT only |
| Evidence owner | FinPredict Engine (evidence loop, promote, kill) |
| Budget | **Free-only until budget lifted** |

This is **not** a live promote, not a paper promote, and not a
TradingView-as-Engine substitute. A TV / Pine proxy is not sklearn and
not the Engine model. See `tradingview/README.md`.

## Universe (both books)

Do not collapse CL and Brent into a single “oil” series in this lock.

- `NYMEX_CL` — NYMEX WTI continuous (free start: `CL=F`)
- `ICE_BRENT` — ICE Brent continuous (free start: `BZ=F`)
- `CL_BRENT_SPREAD` — the spread book, labeled on the same Friday
  `decision_date` grid

A candidate that scores only CL, or only Brent, is a different
hypothesis and is out of this lock.

## Cadence and cutoff

Weekly Friday decisions. Features and semantics must be available at
or before **20:00Z** on the decision Friday. Later prints do not
rewrite that row. The Engine join key is `decision_date` + 20:00Z
cutoff.

## Labels and horizons

On each Friday `decision_date`:

1. Absolute direction of `NYMEX_CL` at 5d / 21d / 63d
2. Absolute direction of `ICE_BRENT` at 5d / 21d / 63d
3. Direction of `CL_BRENT_SPREAD` at 5d / 21d / 63d

The scorecard script restates this 3 × 3 skeleton. It does not mint
Sharpe, does not paper-lock, and does not promote.

## Feature pots (do not mix)

| Pot | What it may carry | What it must not carry |
| --- | ----------------- | ---------------------- |
| OilPot (`data/synap/oil/`) | Oil-market alt features (price, spread, free positioning / inventory when Engine-mapped) | Sanctions, SPR chatter, energy M&A, policy, macro narrative |
| SemanticsOilPot (`data/synap/semantics/oil/`) | Sanctions / SPR / energy M&A / policy / macro **PIT** features only | OilPot price panels, fills, or a joined “oil + news” promote |

See `SEMANTICS_OILPOT.md`. Scripts in this fork do not join the pots.

## Kill criteria (reserved, not armed)

No paper book is armed. `scripts/synap_oil/contract.py` keeps the same
reserved kill helper as copper so a future paper lock can be evaluated
without promoting:

1. **26-week drawdown > 15%** — `max_drawdown_26w > 0.15`
2. **Sum of net returns < -5%** — `sum_net < -0.05`
3. **Lose to MR two consecutive reads** — underperforms the
   mean-reversion baseline on two consecutive monitor reads
   (`lose_to_mr_consecutive_reads >= 2`)

A kill is a halt signal, **not** a promote. The helper always returns
`promote: false`. Do not commit a paper lock JSON from this scaffold.

## Explicit non-goals

- **Never promote** this hypothesis to paper or live from docs,
  scripts, or TradingView.
- Do **not** treat a TV backtest or a sklearn fit on yfinance as
  Engine evidence.
- Do **not** choose CL *or* Brent; the lock is both plus the spread.
- Do **not** commit large parquets, secrets, or EIA API keys.
- Do **not** drop the 20:00Z cutoff or invent a paper lock in this
  fork without a new Engine lock.
