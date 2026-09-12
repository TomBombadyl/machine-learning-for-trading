#!/usr/bin/env python3
"""Shared Synap copper research contracts.

**NOT A PROMOTE.** Candidate IDs, paper-lock paths, and kill-criteria helpers
for the additive FinPredict scripts. The FinPredict Engine owns the evidence
loop; this module only restates committed locks.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

NOT_A_PROMOTE = True
PROMOTE = False
EVIDENCE_OWNER = "FinPredict Engine"
ASSET = "HG"
FREE_ONLY = True

REPO_ROOT = Path(__file__).resolve().parents[2]
COPPER_ROOT = REPO_ROOT / "data" / "synap" / "copper"
LOCK_PATH = COPPER_ROOT / "paper_mom_weekly_lock.json"
DOCS_ROOT = COPPER_ROOT / "docs"

# Optional research-machine artifacts. Large parquets must not be committed.
PANEL_DAILY = COPPER_ROOT / "panels" / "hg_daily.parquet"
PANEL_WEEKLY = COPPER_ROOT / "panels" / "hg_weekly.parquet"
PAPER_FILLS = COPPER_ROOT / "paper" / "mom_weekly_fills.parquet"
REGIME_LABELS = COPPER_ROOT / "regimes" / "regime_labels.parquet"


@dataclass(frozen=True)
class ResearchCandidate:
    """One locked long/short research candidate. Not a live book."""

    candidate_id: str
    horizon: str
    features: tuple[str, ...]
    lookback_days: int | None
    paper_only: bool
    notes: str


# Locked research set from MULTI_HORIZON_LONG_SHORT_SCORECARD.md.
# paper_MOM_ONLY_weekly is the paper lock cousin, not a promote.
LOCKED_CANDIDATES: tuple[ResearchCandidate, ...] = (
    ResearchCandidate(
        candidate_id="daily_63d_LME",
        horizon="daily",
        features=("LME",),
        lookback_days=63,
        paper_only=False,
        notes="LME Engine-first; TV COMEX is not a substitute.",
    ),
    ResearchCandidate(
        candidate_id="daily_21d_MOM_COT",
        horizon="daily",
        features=("MOM", "COT"),
        lookback_days=21,
        paper_only=False,
        notes="CFTC COT fidelity lives in Engine, not TradingView overlays.",
    ),
    ResearchCandidate(
        candidate_id="daily_63d_MOM_LME",
        horizon="daily",
        features=("MOM", "LME"),
        lookback_days=63,
        paper_only=False,
        notes="Blend MOM with Engine LME official series.",
    ),
    ResearchCandidate(
        candidate_id="weekly_MOM_COT",
        horizon="weekly",
        features=("MOM", "COT"),
        lookback_days=None,
        paper_only=False,
        notes="Weekly MOM+COT; TV COT gap applies.",
    ),
    ResearchCandidate(
        candidate_id="weekly_MOM_LME",
        horizon="weekly",
        features=("MOM", "LME"),
        lookback_days=None,
        paper_only=False,
        notes="Weekly MOM+LME; LME Engine-first.",
    ),
    ResearchCandidate(
        candidate_id="paper_MOM_ONLY_weekly",
        horizon="weekly",
        features=("MOM",),
        lookback_days=None,
        paper_only=True,
        notes="Paper-only MOM_ONLY weekly lock. NOT A PROMOTE.",
    ),
)

PAPER_CANDIDATE_ID = "paper_MOM_ONLY_weekly"

# Locked qualitative regime notes from REGIME_BACKTESTS_LOCKED.md.
LOCKED_REGIME_FINDINGS: dict[str, dict[str, str]] = {
    "MOM_ONLY": {
        "strong_bull": "strong",
        "high_vol": "strong",
        "bear": "weak",
        "crisis": "ugly/small-n",
    },
    "MOM_COT": {
        "strong_bull": "ok",
        "high_vol": "ok",
        "bear": "more_bear_tolerant",
        "crisis": "ugly/small-n",
    },
}


def banner() -> str:
    return (
        "NOT A PROMOTE — Synap FinPredict research scaffold. "
        "Evidence loop owned by FinPredict Engine. Free-only. "
        "Never promote from scripts alone."
    )


def load_paper_lock(path: Path | None = None) -> dict[str, Any]:
    """Load the committed paper-only weekly MOM_ONLY lock."""
    lock_path = path or LOCK_PATH
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
    """Apply the paper lock kill rules. Does not promote or halt live books.

    Kill if any of:
    - 26-week drawdown > 15%
    - sum of net returns < -5%
    - lose to the MR baseline on two consecutive monitor reads
    """
    spec = (lock or load_paper_lock())["kill_criteria"]
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
        "observed": {
            "max_drawdown_26w": max_drawdown_26w,
            "sum_net": sum_net,
            "lose_to_mr_consecutive_reads": lose_to_mr_consecutive_reads,
        },
        "thresholds": spec,
    }


def write_report(payload: dict[str, Any], output: Path | None) -> None:
    """Print JSON and optionally write it. Reports are not evidence."""
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
