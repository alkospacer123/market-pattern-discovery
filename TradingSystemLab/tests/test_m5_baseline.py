from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.multitimeframe.phase73 import hash_tree
from TradingSystemLab.timeframe_validation.m5_baseline import (
    causal_four_bar_context, discover_m5_files, run, validate_m5_candles)


def _m5(periods: int = 8) -> pd.DataFrame:
    index = pd.date_range("2024-01-03 10:05", periods=periods, freq="5min",
                          tz="Europe/Moscow", name="CloseTime")
    return pd.DataFrame({"Open": range(periods), "High": [x + 2 for x in range(periods)],
                         "Low": [x - 1 for x in range(periods)],
                         "Close": [x + 1 for x in range(periods)]}, index=index)


def test_m5_discovery_and_validation() -> None:
    paths = discover_m5_files(Path("/workspace/market-pattern-data"), "Si")
    assert all("_M5_" in path.name for path in paths)
    assert all("_2023_" in path.name or "_2024_" in path.name for path in paths)
    validate_m5_candles(_m5())
    with pytest.raises(ValueError, match="CHRONOLOGICAL"):
        validate_m5_candles(_m5().iloc[::-1])
    with pytest.raises(ValueError, match="DUPLICATE"):
        validate_m5_candles(pd.concat([_m5(), _m5().iloc[:1]]).sort_index())
    bad = _m5().copy()
    bad.index = bad.index + pd.Timedelta("1min")
    with pytest.raises(ValueError, match="TIMEFRAME"):
        validate_m5_candles(bad)
    future = _m5().copy()
    future.index = future.index + pd.DateOffset(years=1)
    with pytest.raises(ValueError, match="TRUE_OOS"):
        validate_m5_candles(future)


def test_m5_context_is_causal_and_daily() -> None:
    bars = _m5()
    context = causal_four_bar_context(bars)
    assert context.index.tolist() == [bars.index[3], bars.index[7]]
    assert causal_four_bar_context(bars.drop(bars.index[1])).empty


def test_deterministic_required_artifacts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import TradingSystemLab.timeframe_validation.m5_baseline as baseline
    monkeypatch.setattr(baseline, "load_m5_development", lambda *_: (None, []))
    output = tmp_path / "M5"
    assert run(output=output)["status"] == "PHASE_M5_BASELINE_COMPLETE"
    first = hash_tree(output)
    run(output=output)
    assert first == hash_tree(output)
    required = {"trades.csv", "metrics.json", "yearly_report.csv", "instrument_report.csv",
                "direction_report.csv", "concentration_report.csv", "mae_mfe_report.csv", "final_report.md"}
    assert required == {path.name for path in (output / "T2").iterdir()}
    assert required == {path.name for path in (output / "T3").iterdir()}
    manifest = (output / "manifest.json").read_text()
    assert '"optimization": false' in manifest
    assert '"true_oos_blocked": true' in manifest
