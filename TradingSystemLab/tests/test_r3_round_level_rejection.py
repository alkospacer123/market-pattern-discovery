"""Focused regression tests for the frozen R3 state machine."""
from decimal import Decimal

import pandas as pd
import pytest

from TradingSystemLab.core.levels import level_offset, nearest_lower_level, nearest_upper_level
from TradingSystemLab.core.portfolio import FixedRiskPortfolio
from TradingSystemLab.strategies.range.R3_Round_Level_Rejection import R3Parameters, R3RoundLevelRejection


def frame(rows, start="2024-01-02 10:00", freq="15min"):
    index = pd.date_range(start, periods=len(rows), freq=freq, tz="Europe/Moscow")
    return pd.DataFrame(rows, columns=["Open", "High", "Low", "Close"], index=index)


def engine(**overrides):
    return R3RoundLevelRejection(R3Parameters(atr_period_m15=1, **overrides))


@pytest.mark.parametrize("price,step,lower,upper", [
    (11.073, .05, Decimal("11.05"), Decimal("11.10")),
    (83.17, .10, Decimal("83.10"), Decimal("83.20")),
    (11.10, .05, Decimal("11.10"), Decimal("11.10")),
    (0.1 + 0.2, .05, Decimal("0.30"), Decimal("0.30")),
])
def test_decimal_safe_levels(price, step, lower, upper):
    assert nearest_lower_level(price, step) == lower
    assert nearest_upper_level(price, step) == upper


def test_midpoint_target_is_decimal_safe():
    assert level_offset("11.05", ".05", .5) == Decimal("11.075")
    assert level_offset("11.05", ".05", -.5) == Decimal("11.025")


def test_long_signal_entry_bar_does_not_exit_and_target_is_next_bar():
    data = frame([(11.02, 11.04, 10.98, 11.02), (11.02, 11.06, 11.01, 11.04)])
    trade = engine().run(data, "CNY", round_level_step=.05).iloc[0]
    assert trade.direction == "LONG" and trade.entry_time == data.index[0]
    assert trade.initial_stop == pytest.approx(10.974)
    assert trade.target_price == pytest.approx(11.025)
    assert trade.exit_time == data.index[1] and trade.exit_reason == "ROUND_LEVEL_MIDPOINT_TARGET"
    assert trade.bars_held == 1


def test_short_signal_and_stop_priority_when_stop_and_target_hit():
    data = frame([(11.03, 11.07, 11.02, 11.04), (11.04, 11.08, 11.01, 11.04)])
    trade = engine().run(data, "CNY", round_level_step=.05).iloc[0]
    assert trade.direction == "SHORT"
    assert trade.initial_stop == pytest.approx(11.075)
    assert trade.target_price == pytest.approx(11.025)
    assert trade.exit_reason == "STOP"


@pytest.mark.parametrize("row", [
    (11.02, 11.04, 11.00, 11.02),  # raw touch
    (11.02, 11.04, 10.98, 11.00),  # no reclaim
    (11.02, 11.08, 10.98, 11.01),  # below half bar
    (11.02, 11.04, 10.999, 11.02),  # insufficient penetration
    (11.02, 11.20, 10.94, 11.03),  # multiple levels/deep penetration
])
def test_invalid_long_shapes_do_not_trade(row):
    assert engine().run(frame([row]), "CNY", round_level_step=.05).empty


def test_level_failure_precedes_time_exit():
    data = frame([(11.02, 11.04, 10.98, 11.02), (11.02, 11.024, 10.991, 10.999)])
    trade = engine(max_holding_bars_m15=1).run(data, "CNY", round_level_step=.05).iloc[0]
    assert trade.exit_reason == "LEVEL_FAILURE" and trade.exit_price == 10.999


def test_time_exit_and_one_position():
    data = frame([(11.02, 11.04, 10.98, 11.02), (11.02, 11.024, 11.001, 11.02),
                  (11.02, 11.024, 11.001, 11.02)])
    trades = engine(max_holding_bars_m15=2).run(data, "CNY", round_level_step=.05)
    assert len(trades) == 1 and trades.iloc[0].exit_reason == "TIME_EXIT" and trades.iloc[0].bars_held == 2


def test_tick_size_is_separate_from_round_step_and_fixed_risk_is_used():
    data = frame([(11.02, 11.04, 10.98, 11.02), (11.02, 11.03, 11.01, 11.025)])
    trade = engine().run(data, "CNY", round_level_step=.05, tick_size=.001,
                         portfolio=FixedRiskPortfolio(initial_capital=1000, risk_fraction=.01)).iloc[0]
    assert trade.round_level_step == .05
    assert trade.initial_risk_ticks == pytest.approx(trade.initial_risk_points / .001)
    assert trade.quantity == pytest.approx(10 / trade.initial_risk_points)
    assert trade.cost_R_C1 == pytest.approx(.002 / trade.initial_risk_points)


def test_optional_h1_is_diagnostic_and_causally_aligned():
    m15 = frame([(11.02, 11.04, 10.98, 11.02), (11.02, 11.03, 11.01, 11.025)])
    h1 = frame([(11, 11.1, 10.9, 11)] * 220, start="2023-12-24", freq="1h")
    without = engine().run(m15, "CNY", round_level_step=.05)
    with_context = engine().run(m15, "CNY", round_level_step=.05, h1=h1)
    assert without[["direction", "entry_price", "round_level", "initial_stop", "target_price"]].equals(
        with_context[["direction", "entry_price", "round_level", "initial_stop", "target_price"]])
    assert with_context.iloc[0].H1_context_time <= m15.index[0] - pd.Timedelta("15min")


def test_true_oos_is_hard_rejected_for_execution_and_context():
    oos = frame([(11, 11.1, 10.9, 11)], start="2025-01-01")
    with pytest.raises(ValueError, match="TRUE OOS"):
        engine().run(oos, "CNY", round_level_step=.05)
    valid = frame([(11, 11.1, 10.9, 11)])
    with pytest.raises(ValueError, match="TRUE OOS"):
        engine().run(valid, "CNY", round_level_step=.05, h1=oos)
