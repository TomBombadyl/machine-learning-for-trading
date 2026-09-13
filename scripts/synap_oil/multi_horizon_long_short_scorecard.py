#!/usr/bin/env python3
"""Multi-horizon long/short scorecard — oil research skeleton.

**NOT A PROMOTE.** Restates the locked CL + Brent hypothesis from
``data/synap/oil/docs/MULTI_HORIZON_LONG_SHORT_SCORECARD.md``:

- Universe: NYMEX_CL, ICE_BRENT, CL_BRENT_SPREAD (both books, not choose-one)
- Labels: multi-horizon absolute direction on each book PLUS the spread
- Horizons: 5d / 21d / 63d
- Cadence: weekly Friday decisions, 20:00Z cutoff

Stub until Engine locks exist. Missing parquets stay skeleton.

Run::

    docker compose run --rm ml4t python scripts/synap_oil/multi_horizon_long_short_scorecard.py

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
    ASSET,
    EVIDENCE_OWNER,
    LOCKED_CANDIDATES,
    NOT_A_PROMOTE,
    PANEL_WEEKLY,
    UNIVERSE,
    banner,
    write_report,
)


def _panel_status() -> dict[str, bool]:
    return {
        "weekly_panel_present": PANEL_WEEKLY.is_file(),
    }


def build_scorecard() -> dict:
    """Return a skeleton-or-live scorecard. Missing parquets stay skeleton."""
    panels = _panel_status()
    have_research_panels = any(panels.values())
    rows = []
    for candidate in LOCKED_CANDIDATES:
        rows.append(
            {
                "candidate_id": candidate.candidate_id,
                "universe": candidate.universe,
                "horizon": candidate.horizon,
                "label": candidate.label,
                "paper_only": candidate.paper_only,
                "notes": candidate.notes,
                "mode": "research_panel" if panels["weekly_panel_present"] else "skeleton",
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
        "asset": ASSET,
        "universe": list(UNIVERSE),
        "banner": banner(),
        "panels": panels,
        "mode": "research_panel" if have_research_panels else "skeleton",
        "note": (
            "Research-machine parquets are optional. Without them this script "
            "only restates the locked CL+Brent hypothesis. Never promote from "
            "scripts alone. No oil paper lock yet."
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
