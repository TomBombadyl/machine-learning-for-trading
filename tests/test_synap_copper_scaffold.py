"""Synap Garden / FinPredict copper scaffold — paths, lock, Pine, no-promote."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
COPPER = REPO / "data" / "synap" / "copper"
SCRIPTS = REPO / "scripts" / "synap_copper"
PINE = COPPER / "docs" / "tradingview" / "HG_MOM_ONLY_Weekly.pine"

REQUIRED_PATHS = (
    SCRIPTS / "README.md",
    SCRIPTS / "multi_horizon_long_short_scorecard.py",
    SCRIPTS / "regime_backtests_locked.py",
    SCRIPTS / "paper_monitor_mom_weekly.py",
    COPPER / "README.md",
    COPPER / "paper_mom_weekly_lock.json",
    COPPER / "docs" / "HG_WEEKLY_DECISION_LOCK.md",
    COPPER / "docs" / "MULTI_HORIZON_LONG_SHORT_SCORECARD.md",
    COPPER / "docs" / "REGIME_BACKTESTS_LOCKED.md",
    COPPER / "docs" / "tradingview" / "README.md",
    COPPER / "docs" / "tradingview" / "HG_MOM_COT_Weekly_README.md",
    COPPER / "docs" / "tradingview" / "HG_DAILY_63D_LME_README.md",
    PINE,
    REPO / "data" / "synap" / "semantics" / "docs" / "SEMANTICS_COLLECTOR_PLAN.md",
)

LOCKED_CANDIDATE_IDS = (
    "daily_63d_LME",
    "daily_21d_MOM_COT",
    "daily_63d_MOM_LME",
    "weekly_MOM_COT",
    "weekly_MOM_LME",
    "paper_MOM_ONLY_weekly",
)

EXPECTED_PINE = """\
//@version=5
// Synap FinPredict research port — NOT a live promote
// Candidate: weekly MOM_ONLY MR-framed threshold (paper lock cousin)
// TV approximation: daily chart, Friday signal, 5-bar hold proxy
strategy("HG MOM_ONLY Weekly MR (research)", overlay=false, initial_capital=100000,
     commission_type=strategy.commission.percent, commission_value=0.04,
     default_qty_type=strategy.percent_of_equity, default_qty_value=100,
     pyramiding=0, calc_on_every_tick=false)

thrLong  = input.float(0.60, "Long threshold (model proxy)", minval=0.5, maxval=0.9)
thrShort = input.float(0.40, "Short threshold (model proxy)", minval=0.1, maxval=0.5)
holdBars = input.int(5, "Hold bars after signal", minval=1, maxval=21)
useFriOnly = input.bool(true, "Signals only on Friday")

mom5  = close / close[5] - 1.0
mom21 = close / close[21] - 1.0
mom63 = close / close[63] - 1.0

// MR frame: negate moms (same as Engine)
s5  = -mom5
s21 = -mom21
s63 = -mom63

// Crude logistic stand-in: z-score blend → [0,1] via sigmoid
blend = (s5 + s21 + s63) / 3.0
z = blend / ta.stdev(blend, 63)
proba = 1.0 / (1.0 + math.exp(-z))

isFri = dayofweek == dayofweek.friday
canSignal = not useFriOnly or isFri

longCond  = canSignal and proba >= thrLong
shortCond = canSignal and proba <= thrShort

var int barsInTrade = 0
if strategy.position_size != 0
    barsInTrade += 1
else
    barsInTrade := 0

if longCond and strategy.position_size <= 0
    strategy.close("S")
    strategy.entry("L", strategy.long)
if shortCond and strategy.position_size >= 0
    strategy.close("L")
    strategy.entry("S", strategy.short)

if barsInTrade >= holdBars
    strategy.close_all()

plot(proba, "proba_proxy", color=color.blue)
hline(thrLong, "thrLong", color=color.green)
hline(thrShort, "thrShort", color=color.red)
"""


def _load_script(name: str):
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"synap_copper_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("path", REQUIRED_PATHS, ids=lambda p: str(p.relative_to(REPO)))
def test_required_scaffold_paths_exist(path: Path) -> None:
    assert path.is_file(), f"missing scaffold path: {path}"


def test_pine_matches_locked_source_exactly() -> None:
    assert PINE.read_text(encoding="utf-8") == EXPECTED_PINE


def test_paper_lock_matches_weekly_decision_lock() -> None:
    lock = json.loads((COPPER / "paper_mom_weekly_lock.json").read_text(encoding="utf-8"))
    assert lock["status"] == "NOT_A_PROMOTE"
    assert lock["promote"] is False
    assert lock["paper_only"] is True
    assert lock["asset"] == "HG"
    assert lock["candidate_id"] == "paper_MOM_ONLY_weekly"
    assert lock["model_family"] == "MOM_ONLY"
    assert lock["horizon"] == "weekly"
    assert lock["thresholds"] == {"long": 0.6, "short": 0.4}
    assert lock["risk"] == {"vol_target": True, "dd_halt": True}
    assert lock["kill_criteria"]["lookback_weeks"] == 26
    assert lock["kill_criteria"]["max_drawdown_26w"] == 0.15
    assert lock["kill_criteria"]["sum_net_lt"] == -0.05
    assert lock["kill_criteria"]["lose_to_mr_consecutive_reads"] == 2
    assert lock["evidence_owner"] == "FinPredict Engine"


def test_docs_carry_not_a_promote_marker() -> None:
    docs = [
        COPPER / "README.md",
        COPPER / "docs" / "HG_WEEKLY_DECISION_LOCK.md",
        COPPER / "docs" / "MULTI_HORIZON_LONG_SHORT_SCORECARD.md",
        COPPER / "docs" / "REGIME_BACKTESTS_LOCKED.md",
        COPPER / "docs" / "tradingview" / "README.md",
        COPPER / "docs" / "tradingview" / "HG_MOM_COT_Weekly_README.md",
        COPPER / "docs" / "tradingview" / "HG_DAILY_63D_LME_README.md",
        REPO / "data" / "synap" / "semantics" / "docs" / "SEMANTICS_COLLECTOR_PLAN.md",
        SCRIPTS / "README.md",
    ]
    for path in docs:
        text = path.read_text(encoding="utf-8")
        assert "NOT A PROMOTE" in text, f"{path} missing NOT A PROMOTE"
        assert "never promote" in text.lower()


def test_scorecard_docs_list_locked_candidates() -> None:
    text = (COPPER / "docs" / "MULTI_HORIZON_LONG_SHORT_SCORECARD.md").read_text(
        encoding="utf-8"
    )
    for candidate_id in LOCKED_CANDIDATE_IDS:
        assert candidate_id in text


def test_regime_docs_lock_the_qualitative_findings() -> None:
    text = (COPPER / "docs" / "REGIME_BACKTESTS_LOCKED.md").read_text(encoding="utf-8")
    assert "strong" in text.lower()
    assert "bear" in text.lower()
    assert "bear-tolerant" in text.lower()
    assert "small-n" in text.lower()


def test_semantics_plan_is_separate_pit_and_free() -> None:
    text = (REPO / "data" / "synap" / "semantics" / "docs" / "SEMANTICS_COLLECTOR_PLAN.md").read_text(
        encoding="utf-8"
    )
    assert "SemanticsPot" in text
    assert "CopperPot" in text
    assert "mega_deal" in text or "mega-deals" in text
    assert "tech_shock" in text or "tech shocks" in text
    assert "policy_hammer" in text or "policy hammers" in text
    assert "semantic_event_v0" in text
    assert "EDGAR" in text
    assert "GDELT" in text
    assert "PIT" in text or "point-in-time" in text.lower()


def test_copper_readme_forbids_committing_parquets() -> None:
    text = (COPPER / "README.md").read_text(encoding="utf-8")
    assert "must not be committed" in text.lower() or "never commit" in text.lower()
    assert "parquet" in text.lower()


def test_gitignore_whitelists_the_paper_lock() -> None:
    gitignore = (REPO / ".gitignore").read_text(encoding="utf-8")
    assert "!data/synap/copper/paper_mom_weekly_lock.json" in gitignore


def test_scorecard_script_is_skeleton_and_not_a_promote() -> None:
    mod = _load_script("multi_horizon_long_short_scorecard")
    report = mod.build_scorecard()
    assert report["promote"] is False
    assert report["status"] == "NOT_A_PROMOTE"
    assert report["mode"] == "skeleton"
    assert [row["candidate_id"] for row in report["candidates"]] == list(LOCKED_CANDIDATE_IDS)
    assert all(row["promote"] is False for row in report["candidates"])


def test_regime_script_reprints_locked_findings() -> None:
    mod = _load_script("regime_backtests_locked")
    report = mod.build_regime_report()
    assert report["promote"] is False
    assert report["locked_findings"]["MOM_ONLY"]["strong_bull"] == "strong"
    assert report["locked_findings"]["MOM_ONLY"]["bear"] == "weak"
    assert report["locked_findings"]["MOM_COT"]["bear"] == "more_bear_tolerant"
    assert "small-n" in report["locked_findings"]["MOM_ONLY"]["crisis"]


def test_paper_monitor_idle_without_fills() -> None:
    mod = _load_script("paper_monitor_mom_weekly")
    report = mod.build_monitor_report()
    assert report["promote"] is False
    assert report["mode"] == "idle"
    assert report["lock"]["thresholds"] == {"long": 0.6, "short": 0.4}
    assert report["lock"]["risk"] == {"vol_target": True, "dd_halt": True}


def test_kill_criteria_trips_on_the_locked_rules(tmp_path: Path) -> None:
    contract = _load_script("contract")
    ok = contract.evaluate_kill_criteria(
        max_drawdown_26w=0.10,
        sum_net=-0.01,
        lose_to_mr_consecutive_reads=1,
    )
    assert ok["kill"] is False
    assert ok["promote"] is False

    dead = contract.evaluate_kill_criteria(
        max_drawdown_26w=0.16,
        sum_net=-0.06,
        lose_to_mr_consecutive_reads=2,
    )
    assert dead["kill"] is True
    assert dead["trips"] == {"dd_26w": True, "sum_net": True, "lose_to_mr": True}
    assert dead["promote"] is False

    snapshot = tmp_path / "snap.json"
    snapshot.write_text(
        json.dumps(
            {
                "max_drawdown_26w": 0.20,
                "sum_net": 0.01,
                "lose_to_mr_consecutive_reads": 0,
            }
        ),
        encoding="utf-8",
    )
    monitor = _load_script("paper_monitor_mom_weekly")
    report = monitor.build_monitor_report(snapshot)
    assert report["mode"] == "snapshot"
    assert report["kill_evaluation"]["kill"] is True
    assert report["promote"] is False


def test_scripts_main_exits_zero(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    for name in (
        "multi_horizon_long_short_scorecard",
        "regime_backtests_locked",
        "paper_monitor_mom_weekly",
    ):
        mod = _load_script(name)
        out = tmp_path / f"{name}.json"
        assert mod.main(["--output", str(out)]) == 0
        payload = json.loads(out.read_text(encoding="utf-8"))
        assert payload["promote"] is False
        assert payload["status"] == "NOT_A_PROMOTE"
    captured = capsys.readouterr()
    assert "NOT A PROMOTE" in captured.err
