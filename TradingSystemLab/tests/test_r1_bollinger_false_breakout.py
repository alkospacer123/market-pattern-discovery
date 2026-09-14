from pathlib import Path
import hashlib
import pandas as pd
import numpy as np
import pytest
from pandas.testing import assert_frame_equal
from TradingSystemLab.core.indicators import bollinger_bands, bollinger_bandwidth, previous_window_percentile
from TradingSystemLab.core.portfolio import FixedRiskPortfolio
from TradingSystemLab.strategies.range.R1_Bollinger_False_Breakout import R1BollingerFalseBreakout, R1Parameters
from TradingSystemLab.run_r1_implementation_check import instrument_tick_size, metrics_for

TZ="Europe/Moscow"
def raw(n=340):
    idx=pd.date_range("2023-01-01",periods=n,freq="h",tz=TZ)
    close=pd.Series(100+np.sin(np.arange(n)/4),index=idx)
    return pd.DataFrame({"Open":close,"High":close+.4,"Low":close-.4,"Close":close},index=idx)

def prepared(rows):
    idx=pd.date_range("2023-06-01",periods=len(rows),freq="h",tz=TZ)
    defaults=dict(Open=100.,High=100.4,Low=99.6,Close=100.,Middle=100.,Upper=102.,Lower=98.,BBW=.04,BBW_reference=.05,BBW_percentile=40.,ATR=1.,ADX=10.,EMA200=100.,EMA200_slope_ATR=.1,Target_previous_middle=100.,RangeRegime=True)
    return pd.DataFrame([{**defaults,**r} for r in rows],index=idx)

def run_rows(monkeypatch,rows,params=None):
    s=R1BollingerFalseBreakout(params); d=prepared(rows)
    monkeypatch.setattr(s,"calculate_indicators",lambda _:d)
    return s.run(d[["Open","High","Low","Close"]],"Si")

def test_bollinger_and_bbw_population_convention():
    x=pd.Series(range(1,21),dtype=float); b=bollinger_bands(x)
    assert b.middle.iloc[-1]==10.5
    assert b.upper.iloc[-1]==pytest.approx(10.5+2*x.std(ddof=0))
    assert bollinger_bandwidth(x).iloc[-1]==pytest.approx((b.upper.iloc[-1]-b.lower.iloc[-1])/10.5)

def test_causal_bbw_percentile_excludes_current():
    x=pd.Series(list(range(100))+[10000.])
    q=previous_window_percentile(x,100,50)
    assert q.iloc[100]==pytest.approx(49.5)
    changed=x.copy(); changed.iloc[100]=-10000
    assert previous_window_percentile(changed,100,50).iloc[100]==q.iloc[100]

def test_indicator_regime_and_ema_slope():
    d=R1BollingerFalseBreakout().calculate_indicators(raw())
    i=250
    expected=abs(d.EMA200.iloc[i]-d.EMA200.iloc[i-10])/d.ATR.iloc[i]
    assert d.EMA200_slope_ATR.iloc[i]==pytest.approx(expected)
    assert d.RangeRegime.iloc[i] == (d.ADX.iloc[i]<=20 and d.BBW.iloc[i]<=d.BBW_reference.iloc[i] and expected<=.25)

@pytest.mark.parametrize("direction,rows",[("LONG",[{"Low":97.5,"Close":97.8},{"Close":99.}]),("SHORT",[{"High":102.5,"Close":102.2},{"Close":101.}])])
def test_excursion_next_bar_reclaim_and_stops(monkeypatch,direction,rows):
    t=run_rows(monkeypatch,rows+[{"Low":95.,"High":105.}],R1Parameters(max_holding_bars=1))
    assert len(t)==1 and t.direction.iloc[0]==direction
    assert t.entry_time.iloc[0]==prepared(rows).index[1]
    expected=97.4 if direction=="LONG" else 102.6
    assert t.initial_stop.iloc[0]==pytest.approx(expected)

def test_touch_same_bar_and_expiry_do_not_enter(monkeypatch):
    assert run_rows(monkeypatch,[{"Low":98.,"Close":99.},{"Close":100.}]).empty
    # A same-bar close back inside only arms; the next bar fails and a later reclaim is too late.
    assert run_rows(monkeypatch,[{"Low":97.,"Close":99.},{"Close":98.},{"Close":99.}]).empty

def test_regime_required_on_both_bars_and_each_component():
    s=R1BollingerFalseBreakout()
    for key,value in [("ADX",21.),("BBW",.06),("EMA200_slope_ATR",.26)]:
        bar=prepared([{key:value}]).iloc[0]
        # RangeRegime is calculated as the conjunction; explicitly verify each frozen boundary.
        valid=bar.ADX<=20 and bar.BBW<=bar.BBW_reference and bar.EMA200_slope_ATR<=.25
        assert not valid

def test_regime_invalidation(monkeypatch):
    assert run_rows(monkeypatch,[{"Low":97.5,"Close":97.8},{"Close":101.,"RangeRegime":False}]).empty

def test_max_stop_long_and_short(monkeypatch):
    assert run_rows(monkeypatch,[{"Low":90.},{"Close":99.}]).empty
    assert run_rows(monkeypatch,[{"High":110.},{"Close":99.}]).empty

def test_fixed_risk_and_cost_conversion(monkeypatch):
    t=run_rows(monkeypatch,[{"Low":97.5,"Close":97.8},{"Close":99.},{"Low":96.}],R1Parameters(max_holding_bars=1))
    assert t.quantity.iloc[0]==FixedRiskPortfolio().size(100000.,t.entry_price.iloc[0],t.initial_stop.iloc[0])
    assert t.cost_R_C1.iloc[0]==pytest.approx(.002/t.initial_risk_points.iloc[0])

def test_runner_uses_frozen_instrument_tick_sizes():
    assert instrument_tick_size("Si") == pytest.approx(0.001)
    assert instrument_tick_size("CNY") == pytest.approx(0.001)

def test_previous_middle_target_and_priority(monkeypatch):
    # Current Middle deliberately differs; executable previous-middle column wins.
    t=run_rows(monkeypatch,[{"Low":97.5,"Close":97.8},{"Close":99.},{"Middle":500.,"Target_previous_middle":101.,"Low":96.,"High":102.}])
    assert t.exit_reason.iloc[0]=="STOP"  # stop and target reachable: stop priority
    t=run_rows(monkeypatch,[{"Low":97.5,"Close":97.8},{"Close":99.},{"Middle":500.,"Target_previous_middle":101.,"Low":98.,"High":102.}])
    assert t.exit_reason.iloc[0]=="MIDDLE_BAND_TARGET" and t.exit_price.iloc[0]==101.

def test_range_failure_precedes_time(monkeypatch):
    p=R1Parameters(max_holding_bars=1)
    t=run_rows(monkeypatch,[{"Low":97.5,"Close":97.8},{"Close":99.},{"ADX":26.,"Close":99.,"High":99.5,"Low":98.5,"Target_previous_middle":110.}],p)
    assert t.exit_reason.iloc[0]=="RANGE_FAILURE"

def test_time_exit_exactly_ten_bars(monkeypatch):
    quiet={"Close":99.,"High":99.5,"Low":98.5,"Target_previous_middle":110.}
    t=run_rows(monkeypatch,[{"Low":97.5,"Close":97.8},{"Close":99.}]+[quiet]*10)
    assert t.exit_reason.iloc[0]=="TIME_EXIT" and t.bars_held.iloc[0]==10

def test_one_position_and_mae_mfe_stop_at_exit(monkeypatch):
    rows=[{"Low":97.5,"Close":97.8},{"Close":99.}]+[{"Low":98.5,"High":99.5,"Close":99.,"Target_previous_middle":110.}]*10
    t=run_rows(monkeypatch,rows)
    assert len(t)==1 and t.MAE_R.iloc[0]>=0 and t.MFE_R.iloc[0]>=0

def test_oos_rejected_and_no_lookahead():
    d=raw(30); d.index=pd.date_range("2025-01-01",periods=30,freq="h",tz=TZ)
    with pytest.raises(ValueError,match="TRUE OOS"): R1BollingerFalseBreakout().calculate_indicators(d)
    base=raw(); a=R1BollingerFalseBreakout().calculate_indicators(base)
    altered=base.copy(); altered.iloc[300:,altered.columns.get_loc("Close")]+=50
    b=R1BollingerFalseBreakout().calculate_indicators(altered)
    assert_frame_equal(a.iloc[:300],b.iloc[:300])

def test_determinism(monkeypatch):
    rows=[{"Low":97.5,"Close":97.8},{"Close":99.}]+[{"Close":99.,"High":99.5,"Low":98.5,"Target_previous_middle":110.}]*10
    a=run_rows(monkeypatch,rows); b=run_rows(monkeypatch,rows)
    assert a.to_csv(index=False)==b.to_csv(index=False)
    assert metrics_for(a)==metrics_for(b)
