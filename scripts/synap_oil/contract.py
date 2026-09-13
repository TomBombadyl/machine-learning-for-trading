#!/usr/bin/env python3
"""Shared Synap oil research contracts.

**NOT A PROMOTE.** Universe IDs, optional paper-lock paths, and
kill-criteria helpers for the additive FinPredict oil scripts. The
FinPredict Engine owns the evidence loop; this module only restates
committed locks. There is no oil paper lock yet.

Kill-criteria helpers must never promote.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

NOT_A_PROMOTE = True
PROMOTE = False
EVIDENCE_OWNER = "FinPredict Engine"
ASSET = "CL_BRENT"
FREE_ONLY = True
DECISION_CUTOFF_UTC = "20:00Z"
SIGNAL_WEEKDAY = "Friday"

REPO_ROOT = Path(__file__).resolve().parents[2]
OIL_ROOT = REPO_ROOT / "data" / "synap" / "oil"
# Present only after an Engine paper lock. Do not commit until then.
LOCK_GLOB = "paper_*_weekly_lock.json"
DOCS_ROOT = OIL_ROOT / "docs"

# Optional research-machine artifacts. Large parquets must not be committed.
PANEL_WEEKLY = OIL_ROOT / "panels" / "cl_brent_weekly.parquet"
PAPER_FILLS = OIL_ROOT / "paper" / "weekly_fills.parquet"
REGIME_LABELS = OIL_ROOT / "regimes" / "regime_labels.parquet"

# Universe: BOTH CL and Brent (not choose-one), plus the spread book.
UNIVERSE: tuple[str, ...] = ("NYMEX_CL", "ICE_BRENT", "CL_BRENT_SPREAD")
FREE_PRICE_TICKERS: dict[str, str] = {
    "NYMEX_CL": "CL=F",
    "ICE_BRENT": "BZ=F",
}
HORIZONS: tuple[str, ...] = ("5d", "21d", "63d")

# Reserved until a paper lock exists. Scripts may evaluate these; they
# still must never promote.
DEFAULT_KILL_CRITERIA: dict[str, Any] = {
    "lookback_weeks": 26,
    "max_drawdown_26w": 0.15,
    "sum_net_lt": -0.05,
    "lose_to_mr_consecutive_reads": 2,
}


@dataclass(frozen=True)
class ResearchCandidate:
    """One locked long/short research candidate. Not a live book."""

    candidate_id: str
    universe: str
    horizon: str
    label: str
    paper_only: bool
    notes: str


def _candidate(universe: str, horizon: str) -> ResearchCandidate:
    book = "spread" if universe == "CL_BRENT_SPREAD" else "absolute_direction"
    return ResearchCandidate(
        candidate_id=f"{universe.lower()}_{horizon}",
        universe=universe,
        horizon=horizon,
        label=book,
        paper_only=False,
        notes=(
            "Weekly Friday decision, 20:00Z cutoff. "
            "Research skeleton until Engine locks exist. NOT A PROMOTE."
        ),
    )


# Locked research set from MULTI_HORIZON_LONG_SHORT_SCORECARD.md.
# No paper lock cousin yet — do not invent paper_MOM_ONLY for oil.
LOCKED_CANDIDATES: tuple[ResearchCandidate, ...] = tuple(
    _candidate(universe, horizon) for universe in UNIVERSE for horizon in HORIZONS
)

# No locked qualitative oil regimes yet. Stub reprints this empty map.
LOCKED_REGIME_FINDINGS: dict[str, dict[str, str]] = {}


def banner() -> str:
    return (
        "NOT A PROMOTE — Synap FinPredict oil research scaffold. "
        "Evidence loop owned by FinPredict Engine. Free-only. "
        "Never promote from scripts alone."
    )


def paper_lock_paths(root: Path | None = None) -> list[Path]:
    """Committed paper lock JSON paths, if any. Oil has none yet."""
    base = root or OIL_ROOT
    return sorted(p for p in base.glob(LOCK_GLOB) if p.is_file())


def load_paper_lock(path: Path | None = None) -> dict[str, Any] | None:
    """Load a paper lock if one exists. Missing lock is not a promote.

    When ``path`` is omitted, the first matching ``paper_*_weekly_lock.json``
    under ``data/synap/oil/`` is used. Returns ``None`` if none exist.
    """
    if path is not None:
        lock_path = path
    else:
        matches = paper_lock_paths()
        if not matches:
            return None
        lock_path = matches[0]
    payload = json.loads(lock_path.read_text(encoding="utf-8"))
    if payload.get("promote") is True or payload.get("status") == "PROMOTE":
        raise ValueError(f"{lock_path} must remain NOT-A-PROMOTE")
    return payload


def candidate_ids(*, include_paper: bool = True) -> list[str]:
    return [
        c.candidate_id for c in LOCKED_CANDIDATES if include_paper or not c.paper_only
    ]


def evaluate_kill_criteria(
    *,
    max_drawdown_26w: float,
    sum_net: float,
    lose_to_mr_consecutive_reads: int,
    lock: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Apply reserved / lock kill rules. Does not promote or halt live books.

    Never sets ``promote`` to true. A kill is a halt signal for a future
    paper book, not a promotion.

    Kill if any of:
    - 26-week drawdown > 15%
    - sum of net returns < -5%
    - lose to the MR baseline on two consecutive monitor reads
    """
    source = lock if lock is not None else load_paper_lock()
    spec = (source or {}).get("kill_criteria") or DEFAULT_KILL_CRITERIA
    trips = {
        "dd_26w": max_drawdown_26w > spec["max_drawdown_26w"],
        "sum_net": sum_net < spec["sum_net_lt"],
        "lose_to_mr": lose_to_mr_consecutive_reads >= spec["lose_to_mr_consecutive_reads"],
    }
    return {
        "kill": any(trips.values()),
        "trips": trips,
        "promote": False,
        "status": "NOT_A_PROMOTE",
        "paper_lock_present": source is not None,
        "observed": {
            "max_drawdown_26w": max_drawdown_26w,
            "sum_net": sum_net,
            "lose_to_mr_consecutive_reads": lose_to_mr_consecutive_reads,
        },
        "thresholds": spec,
    }


def write_report(payload: dict[str, Any], output: Path | None) -> None:
    """Print JSON and optionally write it. Reports are not evidence."""
    if payload.get("promote") is True:
        raise ValueError("oil research reports must never set promote:true")
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
