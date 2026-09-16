from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.multitimeframe.phase71 import reject_true_oos, verify_frozen_strategies
from TradingSystemLab.multitimeframe.phase73 import hash_tree
from TradingSystemLab.timeframe_validation.phase81 import (
    causal_four_minute_context, discover_m1_files, run, validate_candle_order)


def _m1(periods: int = 8) -> pd.DataFrame:
    index = pd.date_range("2024-01-03 10:00", periods=periods, freq="1min",
                          tz="Europe/Moscow", name="CloseTime")
    return pd.DataFrame({"Open": range(periods), "High": [x + 2 for x in range(periods)],
                         "Low": [x - 1 for x in range(periods)],
                         "Close": [x + 1 for x in range(periods)]}, index=index)


def test_development_barrier_and_frozen_provenance() -> None:
    verify_frozen_strategies()
    with pytest.raises(ValueError, match="TRUE_OOS_BARRIER_VIOLATION"):
        reject_true_oos(pd.DatetimeIndex(["2025-01-01T00:00:00Z"]))


def test_m1_discovery_isolation() -> None:
    paths = discover_m1_files(Path("/workspace/market-pattern-data"), "Si")
    assert all("_M1_" in path.name for path in paths)
    assert all("_2023_" in path.name or "_2024_" in path.name for path in paths)


def test_candle_order_and_causal_context() -> None:
    bars = _m1()
    validate_candle_order(bars)
    context = causal_four_minute_context(bars)
    # The block ending at 10:03 is observable to execution only at 10:04.
    assert context.index[0] == bars.index[3] + pd.Timedelta("1min")
    with pytest.raises(ValueError, match="M1_CANDLE_ORDER_VIOLATION"):
        validate_candle_order(bars.iloc[::-1])
    assert causal_four_minute_context(bars.drop(bars.index[1])).empty


def test_deterministic_artifacts_and_protected_results(tmp_path: Path,
                                                       monkeypatch: pytest.MonkeyPatch) -> None:
    import TradingSystemLab.timeframe_validation.phase81 as phase81
    monkeypatch.setattr(phase81, "load_m1_development", lambda *_: (None, []))
    protected = [Path("TradingSystemLab/results/true_oos_validation"),
                 Path("TradingSystemLab/results/portfolio_construction")]
    before = [hash_tree(path) for path in protected]
    output = tmp_path / "M1"
    run(output=output)
    first = hash_tree(output)
    run(output=output)
    assert first == hash_tree(output)
    assert before == [hash_tree(path) for path in protected]
    assert (output / "T2/USDRUBF/trades.csv").exists()
    assert (output / "T3/CNYRUBF/final_report.md").exists()
    assert '"optimization": false' in (output / "manifest.json").read_text()


def test_missing_data_returns_data_unavailable(tmp_path: Path,
                                               monkeypatch: pytest.MonkeyPatch) -> None:
    import TradingSystemLab.timeframe_validation.phase81 as phase81
    monkeypatch.setattr(phase81, "load_m1_development", lambda *_: (None, []))
    output = tmp_path / "missing"
    result = run(output=output)
    assert result == {"status": "PHASE_8_1_M1_BASELINE_COMPLETE", "combinations": 4}
    assert "DATA_UNAVAILABLE" in (output / "T3/USDRUBF/metrics.json").read_text()
