from __future__ import annotations

import pandas as pd
import pytest

from bbw_system.core_execution import CoreExecutionConfig, replay_core_v1


CANDIDATE = {"range_min_bars": 3, "range_max_bars": 40, "atr_min": 1.0, "atr_max": 3.0,
             "retest_min_bars": 3, "retest_max_bars": 30, "penetration": 0.2}


def _h1() -> pd.DataFrame:
    t = pd.date_range("2024-01-02", periods=7, freq="h")
    return pd.DataFrame({"timestamp": t, "open": [5] * 6 + [9], "high": [10] * 6 + [12],
                         "low": [0] * 6 + [9], "close": [5] * 6 + [11], "volume": 1,
                         "bbw_squeeze": [True] + [False] * 6,
                         "trend_direction": ["LONG"] * 7, "atr14": [5] * 7})


def _m15() -> pd.DataFrame:
    t = pd.date_range("2024-01-02 07:00", periods=12, freq="15min")
    return pd.DataFrame({"timestamp": t, "open": [11, 11, 11, 12, 12, 24, 36, 48, 48, 48, 48, 48],
                         "high": [12, 12, 12, 13, 25, 37, 49, 49, 49, 49, 49, 49],
                         "low": [10, 10, 10, 11, 11, 23, 35, 47, 47, 47, 47, 47],
                         "close": [11, 11, 11, 12, 24, 36, 48, 48, 48, 48, 48, 48], "volume": 1})


def test_next_open_structural_stop_and_managed_partials_are_causal() -> None:
    h1, m15 = _h1(), _m15()
    before = m15.copy(deep=True)
    result = replay_core_v1(h1, m15, CANDIDATE)
    assert len(result.trades) == 1
    setup = result.setups.iloc[0]
    assert setup.confirmation_time == pd.Timestamp("2024-01-02 07:45")
    assert setup.entry_time == pd.Timestamp("2024-01-02 07:45")
    assert setup.entry_price == 12
    assert result.trades.iloc[0].initial_stop == 0
    assert list(result.fills.kind) == ["ENTRY", "TP1", "TP2", "TP3"]
    assert list(result.fills.stop_after)[-2:] == [24, 24]
    pd.testing.assert_frame_equal(m15, before)


def test_locked_oos_and_range_width_limit_fail_closed() -> None:
    h1 = _h1()
    h1["timestamp"] = pd.date_range("2025-01-02", periods=7, freq="h")
    with pytest.raises(ValueError, match="TRUE OOS"):
        replay_core_v1(h1, _m15(), CANDIDATE)
    result = replay_core_v1(_h1(), _m15(), CANDIDATE, CoreExecutionConfig(max_range_width_pct=0.1))
    assert result.ranges.empty
    assert "RANGE_WIDTH_PCT" in set(result.rejections.reason)
