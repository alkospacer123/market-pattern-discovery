from dataclasses import replace
import math
import numpy as np
import pandas as pd
import pytest

from bbw_system.config import BBWConfig, InstrumentConfig, SessionConfig, load_config
from bbw_system.data import reject_true_oos, validate_ohlcv
from bbw_system.engine import CoreEngine
from bbw_system.exits import BaselineExitManager, Position
from bbw_system.indicators import atr, bbw, ema, true_range
from bbw_system.market import filter_session, trading_date
from bbw_system.reports import DiagnosticWriter
from bbw_system.strategy import (Range, Rejection, State, StateMachine, breakout,
    compression_threshold, construct_range, entry_rejection, evaluate_retest,
    horizontality, structural_stop)
from bbw_system.timeframes import synthetic_bars


def bars(index, opens=None):
    n = len(index); values = np.arange(n, dtype=float) + 100 if opens is None else np.asarray(opens, dtype=float)
    return pd.DataFrame({"open": values, "high": values + 1, "low": values - 1,
                         "close": values + .5, "volume": np.ones(n)}, index=pd.DatetimeIndex(index))


SESSION = SessionConfig(timezone="UTC", session_start="01:00", session_end="20:00", session_anchor="01:00")
INSTRUMENT = InstrumentConfig("TEST", .1, 10, 1, 1000, 100, .2, SESSION)


def test_weekends_and_liquid_session_are_excluded():
    idx = pd.to_datetime(["2026-01-02 00:00", "2026-01-02 01:00", "2026-01-03 10:00", "2026-01-04 10:00"])
    result = filter_session(bars(idx), SESSION)
    assert list(result.index.hour) == [1]
    assert result.index.tz is not None


def test_trading_date_uses_anchor_not_calendar_date():
    assert str(trading_date(pd.Timestamp("2026-01-06 00:30", tz="UTC"), SESSION)) == "2026-01-05"


def test_synthetic_h4_anchor_and_ohlcv():
    source = bars(pd.date_range("2026-01-05 01:00", periods=8, freq="h"))
    result = synthetic_bars(source, 4, SESSION)
    assert list(result.index.hour) == [1, 5]
    assert result.iloc[0][["open", "high", "low", "close", "volume"]].tolist() == [100, 104, 99, 103.5, 4]


def test_incomplete_setup_bar_is_marked_or_dropped():
    source = bars(pd.date_range("2026-01-05 01:00", periods=5, freq="h"))
    assert len(synthetic_bars(source, 4, SESSION)) == 1
    marked = synthetic_bars(source, 4, SESSION, "mark")
    assert marked.complete.tolist() == [True, False]


def test_bbw_population_formula():
    result = bbw(pd.Series([1., 2., 3.]), 3, 2).iloc[-1]
    assert result.middle == 2
    assert result["std"] == pytest.approx(math.sqrt(2 / 3))
    assert result.bbw == pytest.approx(2 * math.sqrt(2 / 3))


def test_recursive_ema_matches_manual_and_warmup():
    values = pd.Series(np.arange(1., 52.))
    result = ema(values, 50)
    expected = values.ewm(span=50, adjust=False, min_periods=50).mean()
    pd.testing.assert_series_equal(result, expected)
    assert result.iloc[:49].isna().all()


def test_wilder_atr_manual_example():
    frame = pd.DataFrame({"high": [10, 12, 13, 15], "low": [8, 9, 11, 12], "close": [9, 11, 12, 14]})
    assert true_range(frame).tolist() == [2, 3, 2, 3]
    result = atr(frame, 3)
    assert result.iloc[2] == pytest.approx(7 / 3)
    assert result.iloc[3] == pytest.approx((7 / 3 * 2 + 3) / 3)


def test_threshold_excludes_current_bar_and_records_audit():
    idx = pd.date_range("2026-01-05", periods=8, freq="D")
    values = pd.Series([.2, .3, .4, .5, .6, .7, .001, .8], index=idx)
    dates = pd.Series(idx.date)
    result = compression_threshold(values, dates, 10, 6, 3)
    assert result.iloc[6].threshold == .45
    assert result.iloc[6].compression
    assert .001 not in result.iloc[6].minima


def test_range_construction_and_horizontal_filter():
    frame = bars(pd.date_range("2026-01-05", periods=6, freq="4h"), [10] * 6)
    value = construct_range(frame)
    assert value == Range(11, 9, 2, 6)
    assert horizontality(pd.Series([10, 10.4]), 1, .5)[0]
    assert not horizontality(pd.Series([10, 10.6]), 1, .5)[0]


def test_breakout_requires_close_not_wick():
    value = Range(11, 9, 2, 6)
    assert breakout(pd.Series({"high": 12, "low": 10, "close": 10.5}), value) is None
    assert breakout(pd.Series({"high": 12, "low": 10, "close": 11.1}), value) == "LONG"


def test_retest_acceptance_and_rejection():
    config = replace(BBWConfig(), penetration_ticks=5)
    assert evaluate_retest(pd.Series({"low": 10.8}), "LONG", 11, 2, .1, config)[0]
    accepted, reason, depth = evaluate_retest(pd.Series({"low": 10.4}), "LONG", 11, 2, .1, config)
    assert not accepted and reason == Rejection.RETEST_TOO_DEEP and depth == pytest.approx(.6)


def test_entry_extension_rejection():
    config = replace(BBWConfig(), max_entry_extension_atr=.1, max_entry_extension_range_pct=.1)
    bar = pd.Series({"open": 11, "high": 11.2, "low": 10.8, "close": 11.1})
    assert entry_rejection(12, 11, 1, 2, bar, config) == Rejection.ENTRY_TOO_EXTENDED


def test_structural_stop_and_wide_stop_is_not_replaced():
    config = replace(BBWConfig(), stop_offset_ticks=2, max_stop_atr=1)
    result = structural_stop("LONG", 12, Range(11, 9, 2, 6), 1, config, INSTRUMENT)
    assert result.stop == 8.8
    assert result.rejection == Rejection.STOP_TOO_LARGE


def test_next_bar_entry_and_stop_wide_e2e_rejection():
    config = replace(BBWConfig(), max_stop_atr=1, max_entry_extension_atr=10, max_entry_extension_range_pct=10)
    reports = DiagnosticWriter(); engine = CoreEngine(config, INSTRUMENT, 100_000, reports)
    confirmation = pd.Series({"open": 11, "high": 11.3, "low": 10.8, "close": 11.2}, name=pd.Timestamp("2026-01-06 10:00"))
    next_bar = pd.Series({"open": 11.4, "high": 12, "low": 11}, name=pd.Timestamp("2026-01-06 11:00"))
    assert engine.enter_after_confirmation("SETUP-1", "LONG", Range(11, 9, 2, 6), 1, confirmation, next_bar) is None
    assert reports.rows["rejected_setups"][0]["reason"] == "STOP_TOO_LARGE"
    assert reports.rows["rejected_setups"][0]["entry"] == 11.4


def test_tp1_tp2_tp3_and_stop_moves():
    position = Position("LONG", 10, 9, 10)
    manager = BaselineExitManager()
    assert manager.process(position, 11, 9.5)[0]["event"] == "TP1"
    assert position.stop == 10 and position.remaining_fraction == .5
    assert manager.process(position, 12, 10.5)[0]["event"] == "TP2"
    assert position.stop == 11 and position.remaining_fraction == pytest.approx(.2)
    assert manager.process(position, 13, 11.5)[0]["event"] == "TP3"
    assert position.closed and position.realized_r == pytest.approx(1.7)


def test_same_bar_stop_first_is_conservative():
    position = Position("LONG", 10, 9, 1)
    events = BaselineExitManager(policy="STOP_FIRST").process(position, 11.5, 8.5)
    assert [event["event"] for event in events] == ["STOP"]
    assert position.realized_r == -1


def test_synthetic_e2e_compression_to_three_targets():
    machine = StateMachine("SETUP-00000001")
    for state in (State.COMPRESSION, State.RANGE, State.BREAKOUT, State.RETEST, State.CONFIRMATION, State.POSITION):
        machine.transition(state)
    config = replace(BBWConfig(), max_entry_extension_atr=10, max_entry_extension_range_pct=10, max_stop_atr=10, max_stop_range_ratio=10)
    engine = CoreEngine(config, INSTRUMENT, 100_000)
    confirmation = pd.Series({"open": 11, "high": 11.2, "low": 10.8, "close": 11.1}, name=pd.Timestamp("2026-01-06 10:00"))
    nxt = pd.Series({"open": 11.1, "high": 11.2, "low": 11}, name=pd.Timestamp("2026-01-06 11:00"))
    position = engine.enter_after_confirmation(machine.setup_id, "LONG", Range(11, 10, 1, 6), 1, confirmation, nxt)
    assert position is not None
    risk = position.risk
    path = pd.DataFrame({"high": [position.entry + risk, position.entry + 2*risk, position.entry + 3*risk], "low": [position.entry, position.entry + .01, position.entry + risk + .01]}, index=pd.date_range("2026-01-06 12:00", periods=3, freq="h"))
    assert [e["event"] for e in engine.manage(position, path)] == ["TP1", "TP2", "TP3"]


def test_data_diagnostics_sort_duplicates_gaps_and_ohlc():
    idx = pd.to_datetime(["2026-01-05 02:00", "2026-01-05 00:00", "2026-01-05 00:00"])
    frame = bars(idx); frame.iloc[0, frame.columns.get_loc("high")] = 0
    clean, report = validate_ohlcv(frame, "1h")
    assert clean.index.is_monotonic_increasing and report.duplicate_timestamps and report.missing_timestamps and report.invalid_ohlc_rows


def test_true_oos_guard():
    with pytest.raises(ValueError, match="locked TRUE OOS"):
        reject_true_oos(bars(pd.to_datetime(["2025-01-01"])))


def test_config_and_reports(tmp_path):
    config, instrument = load_config("bbw_system/config/base.yaml")
    assert config.bbw_period == 10 and instrument.session.excluded_weekdays == [5, 6]
    writer = DiagnosticWriter(); writer.write(tmp_path)
    assert all((tmp_path / f"{name}.csv").exists() for name in writer.FILES)
