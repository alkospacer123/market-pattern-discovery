from __future__ import annotations

import pandas as pd
import pytest

from TradingSystemLab.true_oos.m5 import OOS_START, SESSION, STATUS, _eligible, validate_true_oos_candles


def _bars(index: pd.DatetimeIndex) -> pd.DataFrame:
    return pd.DataFrame({"Open": 1.0, "High": 2.0, "Low": .5, "Close": 1.5}, index=index)


def test_frozen_contract_is_exact() -> None:
    assert STATUS == "PHASE_M5_TRUE_OOS_COMPLETE"
    assert SESSION == {"weekdays": "Monday-Friday", "entry_start_inclusive": "10:00",
                       "entry_end_exclusive": "17:00", "timezone": "Europe/Moscow"}
    assert _eligible(pd.Timestamp("2025-01-06 10:00", tz="Europe/Moscow"))
    assert _eligible(pd.Timestamp("2025-01-06 16:55", tz="Europe/Moscow"))
    assert not _eligible(pd.Timestamp("2025-01-06 17:00", tz="Europe/Moscow"))
    assert not _eligible(pd.Timestamp("2025-01-05 12:00", tz="Europe/Moscow"))


def test_candle_barrier_order_and_duplicates_fail_closed() -> None:
    validate_true_oos_candles(_bars(pd.date_range(OOS_START, periods=3, freq="5min")))
    with pytest.raises(ValueError, match="DEVELOPMENT"):
        validate_true_oos_candles(_bars(pd.date_range("2024-12-31 23:55", periods=2,
                                                       freq="5min", tz="Europe/Moscow")))
    duplicate = pd.DatetimeIndex([OOS_START, OOS_START])
    with pytest.raises(ValueError, match="ORDER_OR_DUPLICATE"):
        validate_true_oos_candles(_bars(duplicate))
    descending = pd.date_range(OOS_START, periods=2, freq="5min")[::-1]
    with pytest.raises(ValueError, match="ORDER_OR_DUPLICATE"):
        validate_true_oos_candles(_bars(descending))
