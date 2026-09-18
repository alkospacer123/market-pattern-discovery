from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.multitimeframe.phase71 import (APPROVED_DATA_ROOT,
    DEVELOPMENT_START, STRATEGY_SHA256, TRUE_OOS_START, frozen_candidates,
    verify_frozen_strategies)
from TradingSystemLab.multitimeframe.phase73 import hash_tree
from TradingSystemLab.optimization.experiment import stable_hash
from TradingSystemLab.timeframe_validation.m15_baseline import (
    PROTECTED_ARTIFACTS, causal_h1_context, discover_m15_files, run,
    validate_m15_candles)


def _m15(periods: int = 8) -> pd.DataFrame:
    index = pd.date_range("2024-01-03 10:15", periods=periods, freq="15min",
                          tz="Europe/Moscow", name="CloseTime")
    return pd.DataFrame({"Open": range(periods), "High": [x + 2 for x in range(periods)],
                         "Low": [x - 1 for x in range(periods)],
                         "Close": [x + 1 for x in range(periods)],
                         "Volume": [10] * periods}, index=index)


def test_m15_discovery_is_approved_and_development_only() -> None:
    paths = discover_m15_files(APPROVED_DATA_ROOT, "Si")
    assert paths
    assert all("_M15_" in path.name for path in paths)
    assert all("_2023_" in path.name or "_2024_" in path.name for path in paths)
    with pytest.raises(ValueError, match="UNAPPROVED"):
        discover_m15_files(Path("/tmp"), "Si")


def test_m15_alignment_and_timezone_validation() -> None:
    validate_m15_candles(_m15())
    bad = _m15().copy()
    bad.index = bad.index + pd.Timedelta("1min")
    with pytest.raises(ValueError, match="TIMEFRAME"):
        validate_m15_candles(bad)
    naive = _m15().copy()
    naive.index = naive.index.tz_localize(None)
    with pytest.raises(ValueError, match="TIMEFRAME"):
        validate_m15_candles(naive)


def test_duplicate_and_non_monotonic_candles_are_rejected() -> None:
    with pytest.raises(ValueError, match="DUPLICATE"):
        validate_m15_candles(pd.concat([_m15(), _m15().iloc[:1]]).sort_index())
    with pytest.raises(ValueError, match="CHRONOLOGICAL"):
        validate_m15_candles(_m15().iloc[::-1])


def test_true_oos_is_rejected_and_period_is_exact() -> None:
    assert DEVELOPMENT_START == pd.Timestamp("2023-01-01", tz="Europe/Moscow")
    assert TRUE_OOS_START == pd.Timestamp("2025-01-01", tz="Europe/Moscow")
    future = _m15().copy()
    future.index = future.index + pd.DateOffset(years=1)
    with pytest.raises(ValueError, match="TRUE_OOS"):
        validate_m15_candles(future)


def test_frozen_candidate_identity_hashes_and_parameters() -> None:
    verify_frozen_strategies()
    candidates = frozen_candidates()
    assert candidates["T2"]["candidate_id"] == "T2_candidate_v1"
    assert candidates["T3"]["candidate_id"] == "T3_candidate_v1"
    assert set(STRATEGY_SHA256) == {"T2", "T3"}
    before = {key: stable_hash(deepcopy(candidates[key]["parameters"])) for key in ("T2", "T3")}
    run_parameters = deepcopy(candidates)
    assert before == {key: stable_hash(run_parameters[key]["parameters"]) for key in ("T2", "T3")}


def test_h1_context_is_exactly_four_closed_consecutive_m15_bars() -> None:
    bars = _m15()
    context = causal_h1_context(bars)
    assert context.index.tolist() == [bars.index[3], bars.index[7]]
    assert context.iloc[0].to_dict() == {"Open": 0, "High": 5, "Low": -1,
                                         "Close": 4, "Volume": 40}
    assert causal_h1_context(bars.iloc[:3]).empty
    assert causal_h1_context(bars.drop(bars.index[1])).empty


def test_h1_context_never_crosses_trading_day() -> None:
    bars = pd.concat([_m15(2), _m15(2).set_axis(
        pd.date_range("2024-01-04 10:15", periods=2, freq="15min", tz="Europe/Moscow",
                      name="CloseTime"))])
    assert causal_h1_context(bars).empty


def test_deterministic_artifacts_and_protected_research(tmp_path: Path,
                                                        monkeypatch: pytest.MonkeyPatch) -> None:
    import TradingSystemLab.timeframe_validation.m15_baseline as baseline
    monkeypatch.setattr(baseline, "load_m15_development", lambda *_: (None, []))
    protected_before = {str(path): hash_tree(path) for path in PROTECTED_ARTIFACTS}
    output = tmp_path / "M15"
    assert run(output=output)["status"] == "PHASE_M15_BASELINE_COMPLETE"
    first = hash_tree(output)
    run(output=output)
    assert first == hash_tree(output)
    assert protected_before == {str(path): hash_tree(path) for path in PROTECTED_ARTIFACTS}
    required = {"trades.csv", "metrics.json", "yearly_report.csv", "instrument_report.csv",
                "direction_report.csv", "concentration_report.csv", "mae_mfe_report.csv",
                "final_report.md"}
    assert required == {path.name for path in (output / "T2").iterdir()}
    assert required == {path.name for path in (output / "T3").iterdir()}
    manifest = (output / "manifest.json").read_text()
    for flag in ("optimization", "ranking", "selection", "walk_forward",
                 "parameter_change", "strategy_change"):
        assert f'"{flag}": false' in manifest
    assert '"true_oos_blocked": true' in manifest
