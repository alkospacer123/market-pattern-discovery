from pathlib import Path

import pandas as pd
import pytest

from bbw_system.instrument_metadata import load_metadata
from bbw_system.temporal_alignment import (
    TemporalAlignmentError, aggregate_m1, assign_trading_dates, infer_timestamp_semantics,
    load_frozen_datasets, validate_daily, validate_h1, validate_sessions,
)

PASSPORT = Path("bbw_system/config/instruments/cnyrubf.yaml")


def bars(start="2024-01-03 09:00", periods=60):
    timestamp = pd.date_range(start, periods=periods, freq="min")
    value = pd.Series(range(periods), dtype=float)
    return pd.DataFrame({"timestamp": timestamp, "open": value, "high": value + 2,
        "low": value - 1, "close": value + 1, "volume": 1})


def reference(source, timeframe, semantics="START"):
    return aggregate_m1(source, timeframe, semantics).drop(columns="source_bar_count")


def test_timestamp_semantics_is_empirically_resolved_and_ties_fail_closed():
    minute = bars(periods=15)
    result = infer_timestamp_semantics(minute, {"M5": reference(minute, "M5")})
    assert result["timestamp_semantics"] == "START"
    assert result["scores"]["START"] > result["scores"]["END"]
    assert infer_timestamp_semantics(minute, {})["timestamp_semantics"] == "UNRESOLVED"


def test_m1_to_m5_aggregates_all_ohlcv_without_price_changes():
    result = aggregate_m1(bars(periods=5), "M5", "START").iloc[0]
    assert (result.open, result.high, result.low, result.close, result.volume) == (0, 6, -1, 5, 5)
    assert result.source_bar_count == 5


def test_m1_to_h1_and_h1_safety():
    minute = bars()
    hourly = reference(minute, "H1")
    result = validate_h1(minute, hourly, "START")
    assert result["H1_ALIGNMENT"] == "PASS"
    assert result["future_filled_count"] == 0
    assert validate_h1(minute.iloc[:-1], hourly, "START")["H1_ALIGNMENT"] == "FAIL"


def test_session_boundaries_and_clearing_are_diagnostic_only():
    metadata = load_metadata(PASSPORT)
    source = pd.concat([bars(periods=2), bars("2024-01-03 14:01", periods=1)], ignore_index=True)
    original = source.copy(deep=True)
    result = validate_sessions(source, metadata)
    assert result[0]["regime"] == "weekday_0900"
    assert result[0]["clearing_bar_count"] == 1
    assert result[0]["status"] == "FAIL"
    pd.testing.assert_frame_equal(source, original)


@pytest.mark.parametrize(("day", "first", "last", "regime"), [
    ("2026-03-20", "09:00", "23:49", "weekday_0850"),
    ("2026-03-23", "09:00", "23:49", "unified_0850"),
    ("2026-07-14", "07:00", "23:49", "unified_0650"),
])
def test_session_regime_transitions_and_boundaries(day, first, last, regime):
    metadata = load_metadata(PASSPORT)
    intervals = {
        "weekday_0850": [("09:00", "14:00"), ("14:05", "18:50"), ("19:05", "23:50")],
        "unified_0850": [("09:00", "14:00"), ("14:05", "23:50")],
        "unified_0650": [("07:00", "14:00"), ("14:05", "23:50")],
    }[regime]
    stamps = pd.DatetimeIndex([])
    for begin, end in intervals:
        stamps = stamps.append(pd.date_range(f"{day} {begin}", f"{day} {end}", freq="min", inclusive="left"))
    source = bars(periods=len(stamps)).assign(timestamp=stamps)
    result = validate_sessions(source, metadata)[0]
    assert (result["regime"], result["status"]) == (regime, "PASS")
    assert result["first_timestamp"].endswith(first + ":00")
    assert result["last_timestamp"].endswith(last + ":00")


def test_trading_date_evening_and_weekend_require_calendar_evidence():
    metadata = load_metadata(PASSPORT)
    source = bars("2024-01-05 19:05", periods=1)
    assert assign_trading_dates(source, metadata, None)["status"] == "UNRESOLVED"
    assigned = assign_trading_dates(source, metadata, set())
    assert assigned["trading_dates"].iloc[0].isoformat() == "2024-01-08"
    weekend = bars("2025-03-01 10:00", periods=1)
    result = assign_trading_dates(weekend, metadata, set())
    assert result["status"] == "PASS"
    assert result["trading_dates"].iloc[0].isoformat() == "2025-03-03"


def test_h1_session_edge_accepts_only_exact_observable_minutes():
    metadata = load_metadata(PASSPORT)
    minute = bars("2024-01-03 23:00", periods=50)
    hourly = reference(minute, "H1")
    assert validate_h1(minute, hourly, "START", metadata)["H1_ALIGNMENT"] == "PASS"
    assert validate_h1(minute.iloc[:-1], hourly, "START", metadata)["H1_ALIGNMENT"] == "FAIL"
    future = pd.concat([hourly, hourly.assign(timestamp=pd.Timestamp("2024-01-04 09:00"))])
    assert validate_h1(minute, future, "START", metadata)["future_filled_count"] == 1


def test_d1_calendar_and_trading_date_validation():
    minute = bars(periods=5)
    daily = pd.DataFrame({"timestamp": [pd.Timestamp("2024-01-03")], "open": [0.], "high": [6.],
        "low": [-1.], "close": [5.], "volume": [5]})
    assert validate_daily(minute, daily)["daily_bar_semantics"] == "CALENDAR_DATE"
    # Identical candidate conventions are not distinguishable and must not be guessed.
    dates = pd.Series(["2024-01-03"] * len(minute))
    assert validate_daily(minute, daily, dates)["daily_bar_semantics"] == "UNRESOLVED"


def test_frozen_loader_fails_closed_when_bundle_is_incomplete(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text('{"instruments":{"CNYRUBF":{}}}', encoding="utf-8")
    with pytest.raises(TemporalAlignmentError, match="dataset missing"):
        load_frozen_datasets(manifest, PASSPORT)


def test_invalid_or_duplicate_raw_bars_fail_closed():
    source = bars(periods=5)
    source.loc[1, "timestamp"] = source.loc[0, "timestamp"]
    with pytest.raises(TemporalAlignmentError, match="duplicate"):
        aggregate_m1(source, "M5", "START")
