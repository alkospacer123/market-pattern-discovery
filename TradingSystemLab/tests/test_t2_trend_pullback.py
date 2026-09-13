"""Causality and execution contract tests for frozen T2."""
from __future__ import annotations
import pandas as pd
import pytest

from TradingSystemLab.core.portfolio import FixedRiskPortfolio
from TradingSystemLab.strategies.trend.T2_Trend_Pullback import T2Parameters, T2TrendPullback


def bars(rows: list[tuple[float, float, float, float]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["Open", "High", "Low", "Close"],
        index=pd.date_range("2024-01-01", periods=len(rows), freq="h", tz="UTC"))


def prepared(direction="LONG", *, confirm_at=2, stop_wide=False, invalidate=False):
    if direction == "LONG":
        raw = bars([(105, 107, 104, 106), (101, 103, 99, 101),
                    (102, 108, 98 if stop_wide else 100, 107), (107, 112, 106, 111), (111, 112, 90, 94)])
        ema20, ema50, ema200 = [100]*5, [95]*5, [90]*5
    else:
        raw = bars([(95, 96, 93, 94), (99, 101, 97, 99),
                    (98, 100 if not stop_wide else 102, 92, 93), (93, 94, 88, 89), (89, 110, 88, 106)])
        ema20, ema50, ema200 = [100]*5, [105]*5, [110]*5
    raw["EMA20"], raw["EMA50"], raw["EMA200"] = ema20, ema50, ema200
    raw["ATR"], raw["ADX"], raw["ATRMean20"] = 4.0, 25.0, 4.0
    if invalidate: raw.iloc[2, raw.columns.get_loc("ADX")] = 20
    return raw


def engine_on(frame, parameters=None):
    strategy = T2TrendPullback(parameters)
    strategy.calculate_indicators = lambda _: frame
    return strategy


def test_regimes_thresholds_and_atr():
    s = T2TrendPullback(); long = prepared().iloc[0]; short = prepared("SHORT").iloc[0]
    assert s.regime(long) == "LONG" and s.regime(short) == "SHORT"
    weak = long.copy(); weak.ADX = 20; assert s.regime(weak) is None
    quiet = long.copy(); quiet.ATR = 3.9; assert s.regime(quiet) is None


@pytest.mark.parametrize("direction", ["LONG", "SHORT"])
def test_causal_impulse_pullback_confirmation_and_stop(direction):
    frame, s = prepared(direction), None
    s = engine_on(frame)
    assert s.impulse_reference(frame, 1, direction) == frame.index[0]
    assert s.is_pullback(frame.iloc[1], direction)
    assert s.is_confirmation(frame.iloc[2], frame.iloc[1], direction)
    trades = s.run(frame, "Si")
    assert len(trades) == 1 and trades.iloc[0].direction == direction
    assert trades.iloc[0].entry_price == frame.iloc[2].Close
    expected = (min(frame.Low.iloc[1:3]) - .4 if direction == "LONG" else max(frame.High.iloc[1:3]) + .4)
    assert trades.iloc[0].initial_stop == pytest.approx(expected)
    assert trades.iloc[0].impulse_reference_time < trades.iloc[0].pullback_time


def test_no_impulse_no_trade():
    frame = prepared(); frame.iloc[0, frame.columns.get_loc("Close")] = 101
    assert engine_on(frame).run(frame, "Si").empty


def test_expiry_and_regime_invalidation():
    frame = prepared(); frame.loc[frame.index[2:5], "Close"] = 101
    frame.loc[frame.index[2:5], "High"] = 105
    late = pd.concat([frame, frame.iloc[[-1]].set_axis([frame.index[-1] + pd.Timedelta(hours=1)])])
    late.iloc[-1, late.columns.get_loc("Close")] = 108
    assert engine_on(late).run(late, "Si").empty
    assert engine_on(prepared(invalidate=True)).run(prepared(invalidate=True), "Si").empty


@pytest.mark.parametrize("direction", ["LONG", "SHORT"])
def test_max_stop_filter(direction):
    frame = prepared(direction, stop_wide=True)
    frame.loc[:, "ATR"] = 1.0; frame.loc[:, "ATRMean20"] = 1.0
    assert engine_on(frame).run(frame, "Si").empty


def test_fixed_risk_sizing_and_stop_priority():
    frame = prepared(); trade = engine_on(frame).run(frame, "Si", portfolio=FixedRiskPortfolio()).iloc[0]
    assert trade.quantity == pytest.approx(1000 / trade.initial_risk_points)
    assert trade.exit_reason == "ATR_TRAILING_STOP"  # bar also closes below EMA50


def test_ema_exit_and_trailing_next_bar_semantics():
    frame = prepared(); frame[["ATR", "ATRMean20"]] = 10.0
    frame.iloc[1, frame.columns.get_loc("Low")] = 90
    frame.iloc[4, frame.columns.get_loc("Low")] = 93
    trade = engine_on(frame).run(frame, "Si").iloc[0]
    assert trade.exit_reason == "EMA50_TREND_LOSS" and trade.exit_price == 94
    # Bar 3 raises trail to 100; it cannot hit itself, but is active on bar 4.
    frame = prepared()
    frame.iloc[4, frame.columns.get_loc("Close")] = 105
    frame.iloc[4, frame.columns.get_loc("Low")] = 99
    assert engine_on(frame).run(frame, "Si").iloc[0].exit_reason == "ATR_TRAILING_STOP"


def test_oos_and_determinism():
    frame = prepared(); strategy = engine_on(frame)
    assert strategy.run(frame, "Si").to_csv(index=False) == strategy.run(frame, "Si").to_csv(index=False)
    bad = bars([(1, 2, 0, 1)]); bad.index = pd.DatetimeIndex([pd.Timestamp("2025-01-01", tz="UTC")])
    with pytest.raises(ValueError, match="TRUE OOS"):
        T2TrendPullback().calculate_indicators(bad)
