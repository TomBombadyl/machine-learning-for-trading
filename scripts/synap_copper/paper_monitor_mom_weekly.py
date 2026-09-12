#!/usr/bin/env python3
"""Paper-only weekly MOM_ONLY monitor (lock cousin).

**NOT A PROMOTE.** Reads ``data/synap/copper/paper_mom_weekly_lock.json``
and applies the committed kill criteria from
``data/synap/copper/docs/HG_WEEKLY_DECISION_LOCK.md``:

- paper-only MOM_ONLY weekly
- long/short thresholds 0.60 / 0.40
- risk overlay: vol_target + dd_halt
- kill: 26w DD > 15%, sum_net < -5%, lose to MR on two consecutive reads

Without ``data/synap/copper/paper/mom_weekly_fills.parquet`` the monitor
stays IDLE. It never promotes, never arms live risk, and never writes a
new lock.

Run::

    docker compose run --rm ml4t python scripts/synap_copper/paper_monitor_mom_weekly.py

Free-only. Evidence loop owned by the FinPredict Engine. Never promote
from scripts alone.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_DIR = Path(__file__).resolve().parent
if str(_DIR) not in sys.path:
    sys.path.insert(0, str(_DIR))

from contract import (  # noqa: I001
    EVIDENCE_OWNER,
    LOCK_PATH,
    NOT_A_PROMOTE,
    PAPER_CANDIDATE_ID,
    PAPER_FILLS,
    REPO_ROOT,
    banner,
    evaluate_kill_criteria,
    load_paper_lock,
    write_report,
)


def _read_monitor_snapshot(path: Path) -> dict:
    """Optional research-machine snapshot (JSON, not a committed parquet)."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        "max_drawdown_26w": float(payload["max_drawdown_26w"]),
        "sum_net": float(payload["sum_net"]),
        "lose_to_mr_consecutive_reads": int(payload["lose_to_mr_consecutive_reads"]),
    }


def build_monitor_report(snapshot: Path | None = None) -> dict:
    lock = load_paper_lock()
    fills_present = PAPER_FILLS.is_file()
    snapshot_path = snapshot
    observed = None
    kill = None
    mode = "idle"

    if snapshot_path is not None and snapshot_path.is_file():
        observed = _read_monitor_snapshot(snapshot_path)
        kill = evaluate_kill_criteria(lock=lock, **observed)
        mode = "snapshot"
    elif fills_present:
        mode = "fills_present_unparsed"
        # Parquet parsing stays on the research machine / Engine. This
        # scaffold only knows that a fills file exists.
        kill = {
            "kill": False,
            "trips": {},
            "promote": False,
            "status": "NOT_A_PROMOTE",
            "note": "Fills parquet present; Engine parses it. Scripts do not promote.",
        }

    return {
        "status": "NOT_A_PROMOTE",
        "promote": False,
        "not_a_promote": NOT_A_PROMOTE,
        "evidence_owner": EVIDENCE_OWNER,
        "free_only": True,
        "asset": lock.get("asset", "HG"),
        "candidate_id": PAPER_CANDIDATE_ID,
        "banner": banner(),
        "mode": mode,
        "lock_path": str(LOCK_PATH.relative_to(REPO_ROOT)),
        "lock": {
            "model_family": lock["model_family"],
            "horizon": lock["horizon"],
            "paper_only": lock["paper_only"],
            "thresholds": lock["thresholds"],
            "risk": lock["risk"],
            "kill_criteria": lock["kill_criteria"],
            "promote": lock["promote"],
        },
        "fills_present": fills_present,
        "observed": observed,
        "kill_evaluation": kill,
        "note": (
            "Paper monitor only. Idle without fills/snapshot. "
            "Never promote from scripts alone."
        ),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("**NOT A PROMOTE.**")[0].strip())
    parser.add_argument(
        "--snapshot",
        type=Path,
        default=None,
        help="Optional JSON snapshot with max_drawdown_26w, sum_net, "
        "lose_to_mr_consecutive_reads (research-machine only).",
    )
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
    write_report(build_monitor_report(args.snapshot), args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
