from __future__ import annotations

import pandas as pd
import pytest

from bbw_system.baseline import BaselineConfig
from bbw_system.trade_management_audit import reconstruct_trade_management


def _h1() -> pd.DataFrame:
    timestamps = pd.date_range("2024-01-02", periods=7, freq="h")
    return pd.DataFrame({
        "timestamp": timestamps, "high": [10] * 6 + [12], "low": [0] * 6 + [9],
        "close": [5] * 6 + [11], "bbw_squeeze": [True] + [False] * 6,
        "trend_direction": ["LONG"] * 7, "atr14": [10] * 7,
    })


def _m15() -> pd.DataFrame:
    timestamps = pd.date_range("2024-01-02 07:00", periods=7, freq="15min")
    return pd.DataFrame({"timestamp": timestamps, "open": [12, 12, 12, 12, 11, 13, 13],
                         "high": [13] * 7, "low": [11, 11, 11, 11, 9, 12, 12],
                         "close": [12, 12, 12, 12, 11, 13, 13]})


def test_reconstructs_range_retest_and_entry_mismatch_without_mutation() -> None:
    h1, m15 = _h1(), _m15()
    h1_before, m15_before = h1.copy(deep=True), m15.copy(deep=True)
    result = reconstruct_trade_management(h1, m15, BaselineConfig())

    assert result.summary["breakouts_accepted"] == 1
    assert result.summary["retests_passed"] == 1
    assert result.summary["entries"] == 1
    assert result.ranges.iloc[-1].range_bars == 6
    assert result.ranges.iloc[-1].max_width_atr_applied
    assert not result.ranges.iloc[-1].max_width_instrument_pct_applied
    entry = result.entries.iloc[0]
    assert entry.current_entry_price == 11  # confirmation close: current FACT
    assert entry.expected_entry_price_before_slippage == 13  # next M15 open: EXPECTED
    assert not entry.entry_matches_core_v1
    pd.testing.assert_frame_equal(h1, h1_before)
    pd.testing.assert_frame_equal(m15, m15_before)


def test_reports_terminal_retest_rejection_reason() -> None:
    m15 = _m15()
    m15.loc[4, "low"] = 7
    result = reconstruct_trade_management(_h1(), m15, BaselineConfig())
    assert result.summary["retests_passed"] == 0
    assert result.summary["rejection_reasons"] == {"RETEST_TOO_DEEP": 1}


def test_locked_true_oos_is_never_read_for_reconstruction() -> None:
    h1 = _h1()
    h1["timestamp"] = pd.date_range("2025-01-02", periods=7, freq="h")
    with pytest.raises(ValueError, match="TRUE OOS"):
        reconstruct_trade_management(h1, _m15(), BaselineConfig())
