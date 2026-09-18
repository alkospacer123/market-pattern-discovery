from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.core.data_loader import DataLoader
from TradingSystemLab.multitimeframe.phase71 import APPROVED_DATA_ROOT, STRATEGY_SHA256, reject_true_oos
from TradingSystemLab.multitimeframe.phase73 import hash_tree
from TradingSystemLab.optimization.experiment import stable_hash
from TradingSystemLab.timeframe_validation.m30_baseline import (
    DEVELOPMENT_START, EXPECTED, PROTECTED_ARTIFACTS, TRUE_OOS_START,
    causal_four_m30_context, discover_m30_files, frozen_candidates, run,
    validate_m30_candles)


def _bars(periods: int = 8, start: str = "2024-01-03 10:30") -> pd.DataFrame:
    index = pd.date_range(start, periods=periods, freq="30min", tz="Europe/Moscow", name="CloseTime")
    return pd.DataFrame({"Open": range(periods), "High": [x + 2 for x in range(periods)],
                         "Low": [x - 1 for x in range(periods)], "Close": [x + 1 for x in range(periods)],
                         "Volume": [10] * periods}, index=index)


def test_frozen_h1_candidate_contract() -> None:
    candidates = frozen_candidates()
    assert DEVELOPMENT_START == pd.Timestamp("2023-01-01", tz="Europe/Moscow")
    assert TRUE_OOS_START == pd.Timestamp("2025-01-01", tz="Europe/Moscow")
    assert STRATEGY_SHA256 == {"T2": "376df085cfda85eefccb31343aad40ed4fbb1078f1314496472a3a4ac9507774",
                               "T3": "840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c"}
    for key in ("T2", "T3"):
        assert candidates[key]["candidate_id"] == EXPECTED[key]["candidate_id"]
        assert candidates[key]["phase32_configuration_id"] == EXPECTED[key]["phase32_configuration_id"]
        assert candidates[key]["parameters"] == EXPECTED[key]["parameters"]
        assert stable_hash(deepcopy(candidates[key]["parameters"])) == EXPECTED[key]["parameter_hash"]


def test_discovery_is_actual_m30_and_explicit_development_years() -> None:
    paths = discover_m30_files(APPROVED_DATA_ROOT, "Si")
    assert paths and all("_M30_" in p.name for p in paths)
    assert all("_2023_" in p.name or "_2024_" in p.name for p in paths)
    assert not any(any(tf in p.name for tf in ("_M1_", "_M5_", "_M15_", "_H1_")) for p in paths)
    with pytest.raises(ValueError, match="UNAPPROVED"):
        discover_m30_files(Path("/tmp"), "Si")


def test_true_oos_is_rejected() -> None:
    future = _bars(start="2025-01-03 10:30")
    with pytest.raises(ValueError, match="TRUE_OOS"):
        validate_m30_candles(future)
    with pytest.raises(ValueError, match="TRUE_OOS"):
        reject_true_oos(future.index)


def test_context_is_exact_canonical_four_bar_aggregation() -> None:
    bars = _bars()
    actual = causal_four_m30_context(bars)
    expected = DataLoader.h4_from_h1(bars)
    pd.testing.assert_frame_equal(actual, expected)
    assert actual.index.tolist() == [bars.index[3], bars.index[7]]
    assert actual.iloc[0].to_dict() == {"Open": 0, "High": 5, "Low": -1, "Close": 4, "Volume": 40}
    assert causal_four_m30_context(bars.iloc[:3]).empty
    assert len(causal_four_m30_context(bars.iloc[:7])) == 1


def test_context_never_crosses_day_and_does_not_overlap() -> None:
    split = pd.concat([_bars(2), _bars(2, "2024-01-04 10:30")])
    assert causal_four_m30_context(split).empty
    bars = _bars(9)
    context = causal_four_m30_context(bars)
    assert context.index.tolist() == [bars.index[3], bars.index[7]]


def test_deterministic_unavailable_fixture_artifacts_and_protection(tmp_path: Path,
                                                                    monkeypatch: pytest.MonkeyPatch) -> None:
    import TradingSystemLab.timeframe_validation.m30_baseline as baseline
    synthetic = _bars(240)
    monkeypatch.setattr(baseline, "load_m30_development", lambda *_: (synthetic, [Path(__file__)]))
    monkeypatch.setattr(baseline, "_execute", lambda *args: pd.DataFrame(columns=baseline.TRADE_COLUMNS))
    before = {str(p): hash_tree(p) for p in PROTECTED_ARTIFACTS}
    output = tmp_path / "M30"
    assert run(output=output)["status"] == "PHASE_M30_BASELINE_COMPLETE"
    first = hash_tree(output)
    run(output=output)
    assert first == hash_tree(output)
    assert before == {str(p): hash_tree(p) for p in PROTECTED_ARTIFACTS}
    assert set(p.name for p in output.iterdir()) == {"T2", "T3", "manifest.json", "comparison.csv",
                                                     "m30_baseline_report.md"}
    required = {"trades.csv", "metrics.json", "yearly_report.csv", "instrument_report.csv",
                "direction_report.csv", "concentration_report.csv", "mae_mfe_report.csv", "final_report.md"}
    assert {p.name for p in (output / "T2").iterdir()} == required
    manifest = (output / "manifest.json").read_text(encoding="utf-8")
    for flag in ("optimization", "ranking", "selection", "walk_forward", "parameter_change", "strategy_change"):
        assert f'"{flag}": false' in manifest
    assert '"true_oos_blocked": true' in manifest
