"""Synap Garden / FinPredict oil scaffold — paths, no-promote, skeletons."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
OIL = REPO / "data" / "synap" / "oil"
SCRIPTS = REPO / "scripts" / "synap_oil"

REQUIRED_PATHS = (
    SCRIPTS / "README.md",
    SCRIPTS / "contract.py",
    SCRIPTS / "multi_horizon_long_short_scorecard.py",
    SCRIPTS / "regime_backtests_locked.py",
    OIL / "README.md",
    OIL / "docs" / "CL_BRENT_WEEKLY_DECISION_LOCK.md",
    OIL / "docs" / "MULTI_HORIZON_LONG_SHORT_SCORECARD.md",
    OIL / "docs" / "REGIME_BACKTESTS_LOCKED.md",
    OIL / "docs" / "SEMANTICS_OILPOT.md",
    OIL / "docs" / "tradingview" / "README.md",
)

LOCKED_CANDIDATE_IDS = (
    "nymex_cl_5d",
    "nymex_cl_21d",
    "nymex_cl_63d",
    "ice_brent_5d",
    "ice_brent_21d",
    "ice_brent_63d",
    "cl_brent_spread_5d",
    "cl_brent_spread_21d",
    "cl_brent_spread_63d",
)

LOCKED_UNIVERSE = ("NYMEX_CL", "ICE_BRENT", "CL_BRENT_SPREAD")

FORBIDDEN_SUFFIXES = (".parquet", ".pkl", ".h5", ".hdf5", ".env")
SECRET_MARKERS = ("EIA_API_KEY", "API_KEY=", "SECRET=", "BEGIN PRIVATE KEY")


def _load_script(name: str):
    path = SCRIPTS / f"{name}.py"
    mod_name = f"synap_oil_{name}"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    return module


def _oil_text_files() -> list[Path]:
    files = [p for p in REQUIRED_PATHS if p.is_file()]
    files.extend(SCRIPTS.glob("*.py"))
    return files


@pytest.mark.parametrize("path", REQUIRED_PATHS, ids=lambda p: str(p.relative_to(REPO)))
def test_required_scaffold_paths_exist(path: Path) -> None:
    assert path.is_file(), f"missing scaffold path: {path}"


def test_no_paper_monitor_or_committed_paper_lock() -> None:
    """Oil is not paper-locked; do not copy copper's monitor/lock yet."""
    assert not list(OIL.glob("paper_*_weekly_lock.json"))
    assert not list(SCRIPTS.glob("paper_monitor_*.py"))


def test_paper_lock_promote_false_if_present() -> None:
    contract = _load_script("contract")
    payload = contract.load_paper_lock()
    if payload is None:
        assert contract.paper_lock_paths() == []
        return
    assert payload.get("promote") is False
    assert payload.get("status") != "PROMOTE"


def test_docs_carry_not_a_promote_marker() -> None:
    docs = [
        OIL / "README.md",
        OIL / "docs" / "CL_BRENT_WEEKLY_DECISION_LOCK.md",
        OIL / "docs" / "MULTI_HORIZON_LONG_SHORT_SCORECARD.md",
        OIL / "docs" / "REGIME_BACKTESTS_LOCKED.md",
        OIL / "docs" / "SEMANTICS_OILPOT.md",
        OIL / "docs" / "tradingview" / "README.md",
        SCRIPTS / "README.md",
    ]
    for path in docs:
        text = path.read_text(encoding="utf-8")
        assert "NOT A PROMOTE" in text, f"{path} missing NOT A PROMOTE"
        assert "never promote" in text.lower()


def test_vertical_lock_documents_cl_and_brent_hypothesis() -> None:
    text = (OIL / "docs" / "CL_BRENT_WEEKLY_DECISION_LOCK.md").read_text(encoding="utf-8")
    assert "NYMEX_CL" in text
    assert "ICE_BRENT" in text
    assert "CL_BRENT_SPREAD" in text
    assert "CL=F" in text
    assert "BZ=F" in text
    assert "20:00Z" in text
    assert "Friday" in text
    assert "5d" in text and "21d" in text and "63d" in text
    assert "not choose-one" in text.lower() or "both" in text.lower()
    assert "OilPot" in text
    assert "SemanticsOilPot" in text
    assert "free-only" in text.lower()
    assert "promote: true" not in text.lower()


def test_scorecard_docs_list_locked_candidates() -> None:
    text = (OIL / "docs" / "MULTI_HORIZON_LONG_SHORT_SCORECARD.md").read_text(
        encoding="utf-8"
    )
    for candidate_id in LOCKED_CANDIDATE_IDS:
        assert candidate_id in text
    for universe in LOCKED_UNIVERSE:
        assert universe in text


def test_regime_docs_are_unlocked_stub() -> None:
    text = (OIL / "docs" / "REGIME_BACKTESTS_LOCKED.md").read_text(encoding="utf-8")
    assert "no locked" in text.lower()
    assert "not locked" in text.lower()
    assert "never promote" in text.lower()


def test_tradingview_readme_proxy_is_not_sklearn() -> None:
    text = (OIL / "docs" / "tradingview" / "README.md").read_text(encoding="utf-8")
    assert "sklearn" in text.lower()
    assert "proxy" in text.lower()
    assert "never promote" in text.lower()


def test_semantics_pointer_does_not_invent_a_tree() -> None:
    text = (OIL / "docs" / "SEMANTICS_OILPOT.md").read_text(encoding="utf-8")
    assert "SemanticsOilPot" in text
    assert "data/synap/semantics/oil/" in text
    assert "20:00Z" in text
    assert "decision_date" in text
    assert not (REPO / "data" / "synap" / "semantics" / "oil").exists()


def test_oil_readme_forbids_committing_parquets() -> None:
    text = (OIL / "README.md").read_text(encoding="utf-8")
    assert "must not be committed" in text.lower() or "never commit" in text.lower()
    assert "parquet" in text.lower()
    assert "SemanticsOilPot" in text


def test_gitignore_whitelists_oil_paper_lock_pattern() -> None:
    gitignore = (REPO / ".gitignore").read_text(encoding="utf-8")
    assert "!data/synap/oil/paper_*_weekly_lock.json" in gitignore


def test_scorecard_script_is_skeleton_and_not_a_promote() -> None:
    mod = _load_script("multi_horizon_long_short_scorecard")
    report = mod.build_scorecard()
    assert report["promote"] is False
    assert report["status"] == "NOT_A_PROMOTE"
    assert report["mode"] == "skeleton"
    assert report["universe"] == list(LOCKED_UNIVERSE)
    assert [row["candidate_id"] for row in report["candidates"]] == list(
        LOCKED_CANDIDATE_IDS
    )
    assert all(row["promote"] is False for row in report["candidates"])
    assert all(row["paper_only"] is False for row in report["candidates"])


def test_regime_script_is_empty_stub() -> None:
    mod = _load_script("regime_backtests_locked")
    report = mod.build_regime_report()
    assert report["promote"] is False
    assert report["mode"] == "skeleton"
    assert report["locked_findings"] == {}


def test_kill_criteria_helper_never_promotes() -> None:
    contract = _load_script("contract")
    assert contract.PROMOTE is False
    assert contract.load_paper_lock() is None

    ok = contract.evaluate_kill_criteria(
        max_drawdown_26w=0.10,
        sum_net=-0.01,
        lose_to_mr_consecutive_reads=1,
    )
    assert ok["kill"] is False
    assert ok["promote"] is False
    assert ok["status"] == "NOT_A_PROMOTE"
    assert ok["paper_lock_present"] is False

    dead = contract.evaluate_kill_criteria(
        max_drawdown_26w=0.16,
        sum_net=-0.06,
        lose_to_mr_consecutive_reads=2,
    )
    assert dead["kill"] is True
    assert dead["trips"] == {"dd_26w": True, "sum_net": True, "lose_to_mr": True}
    assert dead["promote"] is False

    forged = {"promote": True, "status": "PROMOTE", "kill_criteria": {}}
    # evaluate_kill_criteria must still refuse to promote even if handed junk
    forged_eval = contract.evaluate_kill_criteria(
        max_drawdown_26w=0.0,
        sum_net=0.0,
        lose_to_mr_consecutive_reads=0,
        lock=forged,
    )
    assert forged_eval["promote"] is False


def test_load_paper_lock_rejects_promote_true(tmp_path: Path) -> None:
    contract = _load_script("contract")
    bad = tmp_path / "paper_bad_weekly_lock.json"
    bad.write_text(
        json.dumps({"promote": True, "status": "PROMOTE", "kill_criteria": {}}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="NOT-A-PROMOTE"):
        contract.load_paper_lock(bad)


def test_scripts_main_exits_zero(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    for name in (
        "multi_horizon_long_short_scorecard",
        "regime_backtests_locked",
    ):
        mod = _load_script(name)
        out = tmp_path / f"{name}.json"
        assert mod.main(["--output", str(out)]) == 0
        payload = json.loads(out.read_text(encoding="utf-8"))
        assert payload["promote"] is False
        assert payload["status"] == "NOT_A_PROMOTE"
        assert payload["mode"] == "skeleton"
    captured = capsys.readouterr()
    assert "NOT A PROMOTE" in captured.err


def test_no_parquet_or_secrets_in_oil_scaffold() -> None:
    for path in _oil_text_files():
        assert path.suffix not in FORBIDDEN_SUFFIXES
        text = path.read_text(encoding="utf-8")
        for marker in SECRET_MARKERS:
            assert marker not in text, f"{path} looks like it embeds a secret ({marker})"
    for parquet in OIL.rglob("*.parquet"):
        pytest.fail(f"oil parquet must not be committed: {parquet}")


def test_git_diff_has_no_parquet_or_secrets() -> None:
    result = subprocess.run(
        ["git", "diff", "--name-only", "origin/main...HEAD"],
        cwd=REPO,
        check=False,
        capture_output=True,
        text=True,
    )
    names = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    # Uncommitted working tree as well (pre-commit / local).
    dirty = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    )
    for line in dirty.stdout.splitlines():
        names.append(line[3:].strip())
    for name in names:
        lowered = name.lower()
        assert not lowered.endswith(FORBIDDEN_SUFFIXES), name
        assert "id_rsa" not in lowered
        assert not lowered.endswith(".pem")
