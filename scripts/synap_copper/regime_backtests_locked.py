#!/usr/bin/env python3
"""Locked HG regime backtest notes.

**NOT A PROMOTE.** Reprints the locked qualitative findings from
``data/synap/copper/docs/REGIME_BACKTESTS_LOCKED.md``:

- MOM_ONLY: strong in bull / high-vol; weak in bear
- MOM_COT: more bear-tolerant than MOM_ONLY
- crisis slices: ugly / small-n (do not over-read)

If ``data/synap/copper/regimes/regime_labels.parquet`` is present on a
research machine, the script records that a panel exists but still does
not treat a local recompute as Engine evidence.

Run::

    docker compose run --rm ml4t python scripts/synap_copper/regime_backtests_locked.py

Free-only. Evidence loop owned by the FinPredict Engine. Never promote
from scripts alone.
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
    LOCKED_REGIME_FINDINGS,
    NOT_A_PROMOTE,
    REGIME_LABELS,
    banner,
    write_report,
)


def build_regime_report() -> dict:
    present = REGIME_LABELS.is_file()
    return {
        "status": "NOT_A_PROMOTE",
        "promote": False,
        "not_a_promote": NOT_A_PROMOTE,
        "evidence_owner": EVIDENCE_OWNER,
        "free_only": True,
        "asset": "HG",
        "banner": banner(),
        "mode": "research_panel" if present else "skeleton",
        "regime_labels_present": present,
        "locked_findings": LOCKED_REGIME_FINDINGS,
        "crisis_caveat": "ugly/small-n — do not treat crisis slices as powered evidence",
        "note": (
            "These findings are locked research notes. A local parquet, if "
            "present, is not a re-promote and is not Engine evidence."
        ),
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
    write_report(build_regime_report(), args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
