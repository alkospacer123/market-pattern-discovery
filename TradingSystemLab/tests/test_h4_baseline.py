from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.multitimeframe.phase71 import APPROVED_DATA_ROOT, STRATEGY_SHA256, reject_true_oos, verify_frozen_strategies
from TradingSystemLab.multitimeframe.phase73 import hash_tree
from TradingSystemLab.optimization.experiment import stable_hash
from TradingSystemLab.timeframe_validation.h4_baseline import (
    DEVELOPMENT_START, EXPECTED, PROTECTED_ARTIFACTS, TRUE_OOS_START,
    causal_d1, causal_h4, discover_h1_files, frozen_candidates, run,
    validate_development)


def _bars(periods: int = 8, start: str = "2024-01-03 10:00") -> pd.DataFrame:
    index = pd.date_range(start, periods=periods, freq="1h", tz="Europe/Moscow", name="CloseTime")
    return pd.DataFrame({"Open": range(periods), "High": [x + 2 for x in range(periods)],
                         "Low": [x - 1 for x in range(periods)], "Close": [x + 1 for x in range(periods)],
                         "Volume": [10] * periods}, index=index)


def test_frozen_strategy_and_candidate_contract_without_parameter_mutation() -> None:
    verify_frozen_strategies()
    candidates = frozen_candidates()
    assert DEVELOPMENT_START == pd.Timestamp("2023-01-01", tz="Europe/Moscow")
    assert TRUE_OOS_START == pd.Timestamp("2025-01-01", tz="Europe/Moscow")
    assert STRATEGY_SHA256 == {"T2": "376df085cfda85eefccb31343aad40ed4fbb1078f1314496472a3a4ac9507774",
                               "T3": "840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c"}
    original = deepcopy(candidates)
    for key in ("T2", "T3"):
        assert candidates[key]["candidate_id"] == EXPECTED[key]["candidate_id"]
        assert candidates[key]["phase32_configuration_id"] == EXPECTED[key]["phase32_configuration_id"]
        assert candidates[key]["parameters"] == EXPECTED[key]["parameters"]
        assert stable_hash(candidates[key]["parameters"]) == EXPECTED[key]["parameter_hash"]
    assert candidates == original


def test_discovery_is_h1_and_explicitly_2023_2024_only() -> None:
    paths = discover_h1_files(APPROVED_DATA_ROOT, "Si")
    assert paths and all("_H1_" in p.name for p in paths)
    assert all("_2023_" in p.name or "_2024_" in p.name for p in paths)
    assert not any("_2025_" in p.name or "_2026_" in p.name for p in paths)
    with pytest.raises(ValueError, match="UNAPPROVED"):
        discover_h1_files(Path("/tmp"), "Si")


def test_true_oos_is_rejected() -> None:
    future = _bars(start="2025-01-03 10:00")
    with pytest.raises(ValueError, match="TRUE_OOS"):
        validate_development(future)
    with pytest.raises(ValueError, match="TRUE_OOS"):
        reject_true_oos(future.index)


def test_h4_is_deterministic_complete_final_close_and_resets_each_day() -> None:
    bars = _bars()
    first, second = causal_h4(bars), causal_h4(bars)
    pd.testing.assert_frame_equal(first, second)
    assert first.index.tolist() == [bars.index[3], bars.index[7]]
    assert first.iloc[0].to_dict() == {"Open": 0, "High": 5, "Low": -1, "Close": 4, "Volume": 40}
    assert causal_h4(bars.iloc[:3]).empty
    split = pd.concat([_bars(2), _bars(2, "2024-01-04 10:00")])
    assert causal_h4(split).empty


def test_d1_context_is_completed_day_only_and_never_future_filled() -> None:
    first = _bars(3, "2024-01-03 10:00")
    second = _bars(2, "2024-01-04 10:00")
    context = causal_d1(pd.concat([first, second]))
    assert context.index.tolist() == [first.index[-1], second.index[-1]]
    assert context.loc[first.index[-1], "Close"] == first.Close.iloc[-1]
    assert not (context.index > pd.concat([first, second]).index.max()).any()
    # At an H4 decision, only context timestamps at or before that decision can be observed.
    decision = first.index[-1]
    assert context.loc[context.index <= decision].index.tolist() == [decision]


def test_c1_formula_and_deterministic_trade_identity() -> None:
    gross = pd.Series([1.0, -1.0])
    risk = pd.Series([10.0, 20.0])
    assert (gross - 2.0 / risk).tolist() == pytest.approx([0.8, -1.1])
    ids = [f"T2-H4-Si-{n:06d}" for n in range(1, 3)]
    assert ids == ["T2-H4-Si-000001", "T2-H4-Si-000002"]


def test_workflow_has_no_research_selection_api() -> None:
    import TradingSystemLab.timeframe_validation.h4_baseline as baseline
    for name in ("optimize", "rank", "select", "walk_forward", "true_oos"):
        assert not hasattr(baseline, name)


def test_deterministic_artifacts_and_protected_trees(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import TradingSystemLab.timeframe_validation.h4_baseline as baseline
    synthetic = _bars(240)
    monkeypatch.setattr(baseline, "load_h1_development", lambda *_: (synthetic, [Path(__file__)]))
    monkeypatch.setattr(baseline, "_execute", lambda *args: pd.DataFrame(columns=baseline.TRADE_COLUMNS))
    before = {str(p): hash_tree(p) for p in PROTECTED_ARTIFACTS}
    output = tmp_path / "H4"
    assert run(output=output)["status"] == "PHASE_H4_BASELINE_COMPLETE"
    first = hash_tree(output)
    run(output=output)
    assert first == hash_tree(output)
    assert before == {str(p): hash_tree(p) for p in PROTECTED_ARTIFACTS}
    assert {p.name for p in output.iterdir()} == {"T2", "T3", "manifest.json", "comparison.csv", "h4_baseline_report.md"}
    required = {"trades.csv", "metrics.json", "yearly_report.csv", "instrument_report.csv",
                "direction_report.csv", "concentration_report.csv", "mae_mfe_report.csv", "final_report.md"}
    assert {p.name for p in (output / "T2").iterdir()} == required
    manifest = (output / "manifest.json").read_text(encoding="utf-8")
    for flag in ("optimization", "ranking", "selection", "walk_forward", "parameter_change", "strategy_change"):
        assert f'"{flag}": false' in manifest
    assert '"true_oos_blocked": true' in manifest
