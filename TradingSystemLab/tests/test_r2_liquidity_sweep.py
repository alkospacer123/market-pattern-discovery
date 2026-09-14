import hashlib

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from TradingSystemLab.core.mtf import align_closed_context
from TradingSystemLab.core.portfolio import FixedRiskPortfolio
from TradingSystemLab.run_r2_implementation_check import metrics_for
from TradingSystemLab.strategies.range.R2_Liquidity_Sweep import R2LiquiditySweep, R2Parameters

TZ = "Europe/Moscow"


def frames(rows, periods=40):
    hidx = pd.date_range("2023-06-01 01:00", periods=4, freq="h", tz=TZ)
    h1 = pd.DataFrame({"Open": 100., "High": 102., "Low": 98., "Close": 100.}, index=hidx)
    midx = pd.date_range("2023-06-01 01:15", periods=max(periods, len(rows)), freq="15min", tz=TZ)
    defaults = {"Open": 100., "High": 100.4, "Low": 99.6, "Close": 100., "ATR_M15": 1.,
                "context_time": hidx[0], "range_high": 102., "range_low": 98., "range_midpoint": 100.,
                "ADX_H1": 10., "EMA200_slope_ATR_H1": .1, "range_regime": True,
                "failure_context_time": hidx[0], "H1_Close_at_execution": 100.}
    prepared = pd.DataFrame([{**defaults, **(rows[i] if i < len(rows) else {})} for i in range(max(periods, len(rows)))], index=midx)
    return h1, prepared


def run_rows(monkeypatch, rows, params=None):
    h1, ready = frames(rows)
    strategy = R2LiquiditySweep(params)
    monkeypatch.setattr(strategy, "prepare", lambda _h, _m: ready)
    return strategy.run(h1, ready[["Open", "High", "Low", "Close"]], "Si")


def long_signal(**extra):
    return {"Open": 98.2, "High": 99., "Low": 97.8, "Close": 98.8, **extra}


def short_signal(**extra):
    return {"Open": 101.8, "High": 102.2, "Low": 101., "Close": 101.2, **extra}


def test_h1_range_shift_regime_and_future_mutation():
    idx = pd.date_range("2023-01-01", periods=260, freq="h", tz=TZ)
    close = pd.Series(100 + np.sin(np.arange(260) / 8), index=idx)
    raw = pd.DataFrame({"Open": close, "High": close + .5, "Low": close - .5, "Close": close})
    strategy = R2LiquiditySweep()
    result = strategy.calculate_h1_context(raw)
    i = 230
    assert result.range_high.iloc[i] == raw.High.iloc[i-20:i].max()
    assert result.range_low.iloc[i] == raw.Low.iloc[i-20:i].min()
    expected = abs(result.EMA200.iloc[i] - result.EMA200.iloc[i-10]) / result.ATR_H1.iloc[i]
    assert result.EMA200_slope_ATR_H1.iloc[i] == pytest.approx(expected)
    assert result.range_regime.iloc[i] == (result.ADX_H1.iloc[i] <= 25 and expected <= .35)
    changed = raw.copy(); changed.iloc[240:, changed.columns.get_loc("High")] += 50
    assert_frame_equal(result.iloc[:240], strategy.calculate_h1_context(changed).iloc[:240])


def test_generic_causal_alignment_uses_context_before_bar_open():
    m = pd.DataFrame(index=pd.date_range("2023-01-01 10:15", periods=5, freq="15min", tz=TZ))
    h = pd.DataFrame({"value": [10., 11.]}, index=pd.DatetimeIndex(["2023-01-01 10:00", "2023-01-01 11:00"], tz=TZ))
    out = align_closed_context(m, h, "15min")
    assert out.loc["2023-01-01 10:45", "value"] == 10
    assert out.loc["2023-01-01 11:00", "value"] == 10
    assert out.loc["2023-01-01 11:15", "value"] == 11


@pytest.mark.parametrize("signal,direction,stop", [(long_signal(), "LONG", 97.7), (short_signal(), "SHORT", 102.3)])
def test_long_short_sweep_entry_stop_target_and_entry_bar_no_exit(monkeypatch, signal, direction, stop):
    trade = run_rows(monkeypatch, [signal, {"High": 100.1, "Low": 99.5}])
    assert len(trade) == 1 and trade.direction.iloc[0] == direction
    assert trade.entry_time.iloc[0] == frames([signal])[1].index[0]
    assert trade.initial_stop.iloc[0] == pytest.approx(stop)
    assert trade.exit_reason.iloc[0] == "RANGE_MIDPOINT_TARGET"
    assert trade.target_price.iloc[0] == 100.


@pytest.mark.parametrize("signal", [long_signal(Close=97.9), short_signal(Close=102.1),
                                     long_signal(Low=98.1), short_signal(High=101.9),
                                     long_signal(Low=97.97), short_signal(High=102.03),
                                     long_signal(Low=96.9), short_signal(High=103.1),
                                     long_signal(Close=98.2, High=99.5), short_signal(Close=101.8, Low=100.5)])
def test_invalid_reclaim_sweep_depth_and_rejection(monkeypatch, signal):
    assert run_rows(monkeypatch, [signal]).empty


@pytest.mark.parametrize("field,value", [("ADX_H1", 25.1), ("EMA200_slope_ATR_H1", .351)])
def test_h1_regime_filters(monkeypatch, field, value):
    assert run_rows(monkeypatch, [long_signal(**{field: value, "range_regime": False})]).empty


def test_max_stop_and_target_side(monkeypatch):
    assert run_rows(monkeypatch, [long_signal(Close=99.4)]).empty
    assert run_rows(monkeypatch, [short_signal(Close=100.6)]).empty
    assert run_rows(monkeypatch, [long_signal(range_midpoint=98.8)]).empty
    assert run_rows(monkeypatch, [short_signal(range_midpoint=101.2)]).empty


def test_midpoint_is_frozen_after_entry(monkeypatch):
    trade = run_rows(monkeypatch, [long_signal(), {"range_midpoint": 500., "High": 100.1, "Low": 99.5}])
    assert trade.target_price.iloc[0] == 100.
    assert trade.exit_price.iloc[0] == 100.


def test_stop_target_priority_and_mae_mfe(monkeypatch):
    trade = run_rows(monkeypatch, [long_signal(), {"Open": 98.8, "Low": 97., "High": 101.}])
    assert trade.exit_reason.iloc[0] == "STOP"
    assert trade.MAE_R.iloc[0] >= 0 and trade.MFE_R.iloc[0] == 0


@pytest.mark.parametrize("signal,failure", [(long_signal(), 97.9), (short_signal(), 102.1)])
def test_range_failure_precedes_time(monkeypatch, signal, failure):
    p = R2Parameters(max_holding_bars_m15=1)
    row = {"High": 99.5 if failure < 100 else 101.5, "Low": 98.5 if failure < 100 else 100.5,
           "H1_Close_at_execution": failure, "failure_context_time": pd.Timestamp("2023-06-01 02:00", tz=TZ)}
    trade = run_rows(monkeypatch, [signal, row], p)
    assert trade.exit_reason.iloc[0] == "RANGE_FAILURE"


def test_time_exit_one_position_fixed_risk_and_cost(monkeypatch):
    quiet = {"High": 99.5, "Low": 98.5, "Close": 99.}
    trade = run_rows(monkeypatch, [long_signal()] + [quiet] * 16)
    assert len(trade) == 1 and trade.exit_reason.iloc[0] == "TIME_EXIT" and trade.bars_held.iloc[0] == 16
    assert trade.quantity.iloc[0] == FixedRiskPortfolio().size(100000., trade.entry_price.iloc[0], trade.initial_stop.iloc[0])
    assert trade.cost_R_C1.iloc[0] == pytest.approx(.002 / trade.initial_risk_points.iloc[0])


def test_true_oos_rejected():
    h1, ready = frames([])
    h1.index = pd.date_range("2025-01-01", periods=len(h1), freq="h", tz=TZ)
    with pytest.raises(ValueError, match="TRUE OOS"):
        R2LiquiditySweep().calculate_h1_context(h1)
    ready.index = pd.date_range("2025-01-01", periods=len(ready), freq="15min", tz=TZ)
    with pytest.raises(ValueError, match="TRUE OOS"):
        R2LiquiditySweep().prepare(frames([])[0], ready[["Open", "High", "Low", "Close"]])


def test_determinism(monkeypatch):
    rows = [long_signal()] + [{"High": 99.5, "Low": 98.5, "Close": 99.}] * 16
    first, second = run_rows(monkeypatch, rows), run_rows(monkeypatch, rows)
    assert hashlib.sha256(first.to_csv(index=False).encode()).digest() == hashlib.sha256(second.to_csv(index=False).encode()).digest()
    assert metrics_for(first) == metrics_for(second)
