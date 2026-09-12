#!/usr/bin/env python3
"""Multi-horizon long/short scorecard — locked research candidates.

**NOT A PROMOTE.** Scores the locked HG candidates from
``data/synap/copper/docs/MULTI_HORIZON_LONG_SHORT_SCORECARD.md``:

- daily_63d_LME
- daily_21d_MOM_COT
- daily_63d_MOM_LME
- weekly_MOM_COT
- weekly_MOM_LME
- paper_MOM_ONLY_weekly (paper lock cousin; still not a promote)

Run::

    docker compose run --rm ml4t python scripts/synap_copper/multi_horizon_long_short_scorecard.py

Free-only. Evidence loop owned by the FinPredict Engine. A completed
scorecard is research output, not a promotion.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_DIR = Path(__file__).resolve().parent
if str(_DIR) not in sys.path:
    sys.path.insert(0, str(_DIR))

from contract import (  # noqa: I001
    EVIDENCE_OWNER,
    LOCKED_CANDIDATES,
    NOT_A_PROMOTE,
    PANEL_DAILY,
    PANEL_WEEKLY,
    banner,
    write_report,
)


def _panel_status() -> dict[str, bool]:
    return {
        "daily_panel_present": PANEL_DAILY.is_file(),
        "weekly_panel_present": PANEL_WEEKLY.is_file(),
    }


def build_scorecard() -> dict:
    """Return a skeleton-or-live scorecard. Missing parquets stay skeleton."""
    panels = _panel_status()
    have_research_panels = any(panels.values())
    rows = []
    for candidate in LOCKED_CANDIDATES:
        panel_ok = (
            panels["daily_panel_present"]
            if candidate.horizon == "daily"
            else panels["weekly_panel_present"]
        )
        rows.append(
            {
                "candidate_id": candidate.candidate_id,
                "horizon": candidate.horizon,
                "features": list(candidate.features),
                "lookback_days": candidate.lookback_days,
                "paper_only": candidate.paper_only,
                "notes": candidate.notes,
                "mode": "research_panel" if panel_ok else "skeleton",
                "sharpe": None,
                "hit_rate": None,
                "sum_net": None,
                "promote": False,
            }
        )
    return {
        "status": "NOT_A_PROMOTE",
        "promote": False,
        "not_a_promote": NOT_A_PROMOTE,
        "evidence_owner": EVIDENCE_OWNER,
        "free_only": True,
        "asset": "HG",
        "banner": banner(),
        "panels": panels,
        "mode": "research_panel" if have_research_panels else "skeleton",
        "note": (
            "Research-machine parquets are optional. Without them this script "
            "only restates the locked candidate set. Never promote from scripts alone."
        ),
        "candidates": rows,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("**NOT A PROMOTE.**")[0].strip())
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional JSON report path (do not commit).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    print(banner(), file=sys.stderr)
    write_report(build_scorecard(), args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
