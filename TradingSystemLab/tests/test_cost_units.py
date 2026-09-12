import pandas as pd
import pytest

from TradingSystemLab.core.execution import net_r, tick_cost_r
from TradingSystemLab.core.portfolio import FixedRiskPortfolio
from TradingSystemLab.run_robust import IDENTITY, SCENARIOS, TICK_SIZE


@pytest.mark.parametrize("gross,expected", [(1.0, .75), (-.5, -.75)])
def test_synthetic_long_and_short_points_to_r(gross, expected):
    # The absolute risk conversion is identical for entry/stop order (long/short).
    stop = 98 if gross > 0 else 102
    assert abs(100 - stop) / .25 == 8
    assert tick_cost_r(100, stop, .25, 1) == pytest.approx(.25)
    assert net_r(gross, 100, stop, .25, 1) == pytest.approx(expected)


def test_c0_is_exact_identity_and_cost_is_applied_once():
    assert tick_cost_r(100, 98, .25, 0) == 0.0
    assert net_r(1.0, 100, 98, .25, 0) == 1.0
    # One tick each side is 0.50 points, not an entry/exit adjustment plus 0.50.
    assert net_r(1.0, 100, 98, .25, 1) == .75


def test_quantity_cancels_from_fixed_risk_normalization():
    risk_points, tick, qty, point_value = 2., .25, 37, 10.
    monetary_cost = 2 * tick * qty * point_value
    risk_money = risk_points * qty * point_value
    assert monetary_cost / risk_money == tick_cost_r(100, 98, tick, 1)


@pytest.mark.parametrize("strategy,path,baseline", [
    ("T1", "TradingSystemLab/results/T1_robust/mae_mfe.csv",
     "TradingSystemLab/results/T1_baseline/trades.csv"),
    ("T3", "TradingSystemLab/results/T3_robust/trades/trades_C0.csv",
     "TradingSystemLab/results/T3_baseline/trades.csv"),
])
def test_frozen_c0_parity(strategy, path, baseline):
    current, frozen = pd.read_csv(path), pd.read_csv(baseline)
    aliases = {"stop_loss": "initial_stop"}
    if "gross_R" not in frozen:
        aliases["profit_R"] = "gross_R"
    frozen = frozen.rename(columns=aliases)
    if "trade_id" not in frozen:
        frozen["trade_id"] = frozen.groupby("symbol", sort=False).cumcount().add(1).map(
            lambda n: f"{n:06d}")
        frozen["trade_id"] = frozen.symbol + "-" + frozen.trade_id
    current = current.sort_values(["trade_id"]).reset_index(drop=True)
    frozen = frozen.sort_values(["trade_id"]).reset_index(drop=True)
    columns = IDENTITY + ["entry_price", "initial_stop", "exit_price", "gross_R"]
    pd.testing.assert_frame_equal(current[columns].reset_index(drop=True),
                                  frozen[columns].reset_index(drop=True), check_dtype=False)


def test_committed_cost_results_are_monotonic_and_deterministic():
    diagnostics = pd.read_csv("TradingSystemLab/results/execution_units_audit/trade_unit_diagnostics.csv")
    assert (diagnostics.initial_risk_ticks > 0).all()
    assert (diagnostics.tick_size > 0).all()
    for _, row in diagnostics.iterrows():
        values = [row.gross_R - 2 * ticks / row.initial_risk_ticks
                  for ticks in SCENARIOS.values()]
        assert values == sorted(values, reverse=True)
    pd.testing.assert_frame_equal(diagnostics, pd.read_csv(
        "TradingSystemLab/results/execution_units_audit/trade_unit_diagnostics.csv"))
