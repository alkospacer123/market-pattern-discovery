import numpy as np
import pandas as pd
import pytest

from TradingSystemLab.core.backtester import Backtester
from TradingSystemLab.core.indicators import atr, bollinger_bandwidth, rolling_percentile_rank
from TradingSystemLab.core.portfolio import FixedRiskPortfolio
from TradingSystemLab.strategies.trend.T1_BBW_Donchian import T1BBWDonchian


def bars(count=180):
    index = pd.date_range("2024-01-01", periods=count, freq="h", tz="UTC")
    close = pd.Series(100 + np.sin(np.arange(count) / 5), index=index)
    return pd.DataFrame({"Open": close, "High": close + 1, "Low": close - 1,
                         "Close": close}, index=index)


def test_bbw_calculation_uses_population_deviation():
    values = pd.Series([1.0, 2.0, 3.0])
    result = bollinger_bandwidth(values, 3, 2).iloc[-1]
    assert result == pytest.approx(4 * values.std(ddof=0) / values.mean())


def test_bbw_percentile_has_deterministic_weak_ties():
    assert rolling_percentile_rank(pd.Series([3., 1., 2., 2.]), 4).iloc[-1] == 75


def test_atr_expansion_regime_and_long_short_signals():
    strategy = T1BBWDonchian()
    common = {"BBW": 2., "BBWPrevious": 1., "BBWMean20": 1.5,
              "BBWPercentile": 30., "ATR": 2., "ATRMean20": 1.9,
              "PriorHigh": 10., "PriorLow": 5., "EMA50": 8.}
    assert strategy.regime(pd.Series(common)) == "LONG"
    assert strategy.generate_signal(pd.Series({**common, "Close": 11.}), "LONG") == "LONG"
    assert strategy.generate_signal(pd.Series({**common, "Close": 4.}), "LONG") == "SHORT"
    assert strategy.regime(pd.Series({**common, "ATR": 1.8})) is None


def test_donchian_shift_excludes_signal_bar():
    frame = bars(21)
    frame.iloc[-1, frame.columns.get_loc("High")] = 999
    calculated, _ = T1BBWDonchian().calculate_indicators(frame, frame)
    assert calculated.iloc[-1].PriorHigh < 999


def test_indicators_are_prefix_invariant_no_lookahead():
    frame = bars()
    before, _ = T1BBWDonchian().calculate_indicators(frame.iloc[:150], frame.iloc[:150])
    after, _ = T1BBWDonchian().calculate_indicators(frame, frame)
    pd.testing.assert_frame_equal(before, after.iloc[:150])


def test_stops_and_trailing_are_symmetric():
    strategy = T1BBWDonchian()
    assert strategy.calculate_stop_loss("LONG", 100, 2) == 96
    assert strategy.calculate_stop_loss("SHORT", 100, 2) == 104
    assert strategy.manage_position("LONG", 110, 2) == 104
    assert strategy.manage_position("SHORT", 90, 2) == 96


def test_oos_rejection_costs_and_determinism():
    frame = bars()
    tester = Backtester(FixedRiskPortfolio(), cost_ticks_per_side=1, tick_size=.5)
    first = tester.run(T1BBWDonchian(), "X", frame, frame)
    second = tester.run(T1BBWDonchian(), "X", frame, frame)
    pd.testing.assert_frame_equal(first.trades, second.trades)
    assert (first.trades.costs >= 0).all()
    oos = frame.copy()
    oos.index = pd.date_range("2025-01-01", periods=len(oos), freq="h", tz="UTC")
    with pytest.raises(ValueError, match="TRUE OOS"):
        tester.run(T1BBWDonchian(), "X", oos, oos)
