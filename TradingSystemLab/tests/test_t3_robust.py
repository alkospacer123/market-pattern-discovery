import pandas as pd
import pytest

from TradingSystemLab.core.backtester import Backtester


class ScriptedStrategy:
    name = "test"

    def __init__(self, direction="LONG"):
        self.direction = direction

    def calculate_indicators(self, h1, h4):
        low = h1.copy()
        low["ATR"] = 1.0
        return low, h4

    def regime(self, _bar):
        return self.direction

    def generate_signal(self, bar, _regime):
        return self.direction if bool(bar.get("signal", False)) else None

    def calculate_stop_loss(self, direction, entry, _atr):
        return entry - 2 if direction == "LONG" else entry + 2

    def manage_position(self, direction, extreme, _atr):
        return extreme - 3 if direction == "LONG" else extreme + 3

    def exit_signal(self, direction, bar, stop):
        return bar.Low <= stop if direction == "LONG" else bar.High >= stop


def bars(direction="LONG", stop_on_last=True):
    index = pd.date_range("2024-01-02", periods=4, freq="h", tz="UTC")
    frame = pd.DataFrame({"Open": [10, 10, 10, 10], "High": [99, 12, 14, 50],
                          "Low": [-99, 9, 10, 7], "Close": [10] * 4,
                          "signal": [True, False, False, False]}, index=index)
    if direction == "SHORT":
        frame.loc[:, ["High", "Low"]] = [[99, -99], [11, 8], [10, 6], [13, -50]]
    if not stop_on_last:
        frame.iloc[-1, frame.columns.get_loc("Low")] = 9
        frame.iloc[-1, frame.columns.get_loc("High")] = 11
    return frame


def execute(direction="LONG", costs=0):
    h1 = bars(direction)
    h4 = h1.iloc[[0]].drop(columns="signal")
    return Backtester(cost_ticks_per_side=costs, tick_size=.5).run(
        ScriptedStrategy(direction), "X", h1, h4).trades


def test_long_mae_mfe_excludes_entry_and_post_stop_extremes():
    trade = execute().iloc[0]
    assert trade.MAE_points == pytest.approx(1)
    assert trade.MFE_points == pytest.approx(4)
    assert trade.MAE_R == pytest.approx(.5)
    assert trade.MFE_R == pytest.approx(2)
    assert trade.bars_held == 3


def test_short_mae_mfe_is_directionally_correct():
    trade = execute("SHORT").iloc[0]
    assert trade.MAE_points == pytest.approx(1)
    assert trade.MFE_points == pytest.approx(4)


def test_costs_preserve_trade_identity_and_reduce_result():
    free, costly = execute(costs=0), execute(costs=1)
    identity = ["trade_id", "symbol", "direction", "entry_time", "exit_time", "exit_reason"]
    pd.testing.assert_frame_equal(free[identity], costly[identity])
    assert costly.profit_R.sum() < free.profit_R.sum()
    assert costly.net_profit.sum() < free.net_profit.sum()


def test_true_oos_is_rejected():
    h1 = bars()
    h1.index = pd.date_range("2025-01-02", periods=4, freq="h", tz="UTC")
    with pytest.raises(ValueError, match="TRUE OOS"):
        Backtester().run(ScriptedStrategy(), "X", h1, h1.iloc[[0]])


def test_repeated_runs_are_deterministic():
    pd.testing.assert_frame_equal(execute(), execute())
