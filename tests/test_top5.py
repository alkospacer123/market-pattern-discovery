import json
import numpy as np
import pandas as pd
import pytest

from market_pattern_discovery.backtest.top5 import *
from market_pattern_discovery.backtest.top5 import _signal


def bars(n=40, instrument="CNYRUBF", close=None):
    t=pd.date_range("2026-01-05 10:00",periods=n,freq="min",tz="Europe/Moscow")
    c=np.asarray(close if close is not None else 10+np.arange(n)*.001,float)
    return pd.DataFrame({"open_time":t,"close_time":t+pd.Timedelta(minutes=1),"open":c,"high":c+.001,"low":c-.001,"close":c,"volume":1,"trading_date":t.date,"instrument":instrument})


def m5bars(close, highs=None, lows=None):
    n=len(close);t=pd.date_range("2026-01-05 10:05",periods=n,freq="5min",tz="Europe/Moscow");c=np.asarray(close,float)
    return pd.DataFrame({"close_time":t,"open_time":t-pd.Timedelta(minutes=5),"open":c,"high":np.asarray(highs if highs is not None else c+.01),"low":np.asarray(lows if lows is not None else c-.01),"close":c,"volume":5,"trading_date":t.date})


def test_causal_m5_complete_and_close_stamp():
    x=causal_m5(bars(11)); assert len(x)==2 and x.close_time.iloc[0].minute==5 and x.close.iloc[0]==bars(11).close.iloc[4]


def test_incomplete_m5_unavailable(): assert len(causal_m5(bars(4)))==0


def test_pivot_confirmation_cannot_appear_early():
    x=m5bars([1,2,3,2,1]); p=confirmed_pivots(x); assert p.known_index.iloc[0]==4 and p.known_time.iloc[0]==x.close_time.iloc[4]


def test_future_mutation_cannot_alter_past_pivots():
    x=m5bars([1,2,3,2,1,1,1]); a=confirmed_pivots(x);x.loc[5:,"high"]=99;b=confirmed_pivots(x);assert a[a.known_index<5].iloc[0].price==b[b.known_index<5].iloc[0].price


@pytest.mark.parametrize("side",["HIGH","LOW"])
def test_equal_high_and_equal_low(side):
    if side=="HIGH": x=m5bars([1,2,3,2,1,2,3.001,2,1])
    else:x=m5bars([3,2,1,2,3,2,1.001,2,3])
    z=structural_levels(x,"CNYRUBF",2,2);assert len(z)==1 and z.level_type.iloc[0]==("EH" if side=="HIGH" else "EL") and z.touch_count.iloc[0]==2


def test_minimum_touch_separation():
    x=m5bars([1,3,3,2,1]);assert structural_levels(x,"CNYRUBF",2,2).empty


def test_round_number_is_confluence_only():
    x=m5bars([1,2,3,2,1]);assert structural_levels(x,"CNYRUBF",2,2).empty


def test_structural_rejection_and_sweep_long_short():
    x=m5bars([2]*8); levels=pd.DataFrame([{"level_id":"L","level_type":"EL","price":2.,"known_time":x.close_time.iloc[0],"tolerance_ticks":2,"round_confluence":True},{"level_id":"H","level_type":"EH","price":2.,"known_time":x.close_time.iloc[0],"tolerance_ticks":2,"round_confluence":True}])
    x.loc[2,["low","close"]]=[1.998,2.001];x.loc[4,["high","close"]]=[2.002,1.999]
    s=structural_signals(x,levels,"CNYRUBF"); assert {1,-1}<=set(s.direction) and "SIMPLE_SWEEP" in set(s.submodel)


def test_complex_false_break_and_exact_retest_level_and_expiry():
    x=m5bars([2]*10);lev=pd.DataFrame([{"level_id":"H","level_type":"EH","price":2.,"known_time":x.close_time.iloc[0],"tolerance_ticks":2,"round_confluence":False}]);x.loc[1,"close"]=2.002;x.loc[2,["low","close"]]=[1.999,2.001]
    s=structural_signals(x,lev,"CNYRUBF");assert (s.reference_level==2).all() and "BREAKOUT_RETEST" in set(s.submodel)
    x.loc[2:7,["low","close"]]=[2.01,2.];x.loc[8,["low","close"]]=[1.999,2.001];s=structural_signals(x,lev,"CNYRUBF");assert s.empty or not ((s.submodel=="BREAKOUT_RETEST")&(s.signal_time==x.close_time.iloc[8])).any()


def test_or_unavailable_and_orb_next_open():
    assert orb_signals(bars(4),"CNYRUBF",5).empty
    x=bars(10);x.loc[5,"close"]=10.02;x.loc[5,"high"]=10.021;s=orb_signals(x,"CNYRUBF",5);assert len(s)==1
    l=simulate_explicit_orders(x,s,.001);assert (l.entry_time==x.open_time.iloc[6]).all()


def test_trend_regime_pullback_resumption():
    c=np.r_[np.linspace(10,12,70),11.8,12.1,12.2];x=m5bars(c);x.loc[70,"low"]=x.loc[70,"close"]-.2
    s=trend_signals(x,"CNYRUBF",50);assert not s.empty and (s.ema_fast>s.ema_slow).all()


def test_pair_features_past_only():
    a=bars(260,close=np.linspace(10,11,260));b=bars(260,"USDRUBF",np.linspace(90,91,260));z=pair_features(a,b,240);before=z.z.iloc[245];a.loc[250:,"close"]=100;after=pair_features(a,b,240).z.iloc[245];assert before==after


def test_pair_two_leg_pnl_and_friction():
    a=bars(5);b=bars(5,"USDRUBF",np.linspace(90,91,5));s=pd.DataFrame([{"submodel":"OLS","signal_time":a.close_time.iloc[0],"direction_cny":1,"direction_si":-1}]);l=simulate_pairs(a,b,s);assert {"pnl_cny","pnl_si"}<=set(l) and l.loc[l.friction.eq("BASE"),"pnl"].iloc[0]<l.loc[l.friction.eq("GROSS"),"pnl"].iloc[0]


def test_bollinger_and_rsi_calculation():
    x=indicators(m5bars(np.r_[np.ones(20)*10,9]));assert np.isclose(x.bb_mid.iloc[19],10) and x.rsi.iloc[-1]<30


def test_mean_reversion_requires_reentry():
    c=np.r_[np.ones(20)*10,8,9.5,10];x=m5bars(c);s=mean_reversion_signals(x,"CNYRUBF",1.5,30);assert s.empty or (s.signal_time>s.extreme_time).all()


def test_explicit_stop_stop_first_gap_day_and_friction():
    x=bars(6);x.loc[1,["open","high","low","close"]]=[10,10.01,9.99,10];x.loc[2,["open","high","low","close"]]=[9.8,10.3,9.7,10]
    s=pd.DataFrame([_signal("X","Y","CNYRUBF",x.close_time.iloc[0],1,10,9.9,2)])
    l=simulate_explicit_orders(x,s,.001);assert set(l.exit_reason)=={"STOP_GAP"};assert l[l.friction.eq("BASE")].pnl.iloc[0]<l[l.friction.eq("GROSS")].pnl.iloc[0]


def test_no_trading_date_crossing():
    x=bars(5);x.loc[2:,"trading_date"]=pd.Timestamp("2026-01-06").date();s=pd.DataFrame([_signal("X","Y","CNYRUBF",x.close_time.iloc[0],1,10,9,2)]);l=simulate_explicit_orders(x,s,.001);assert l.exit_time.max()<=x.close_time.iloc[1]


def test_dev_selection_cannot_overlap_validation():
    with pytest.raises(ValueError):assert_oos("2026-03-01","2026-03-01")
    assert_oos("2026-02-28 23:59","2026-03-01")


def test_frozen_hash_unchanged_and_detects_change(tmp_path):
    p=tmp_path/"f.json";h=freeze(p,{"x":1});assert verify_frozen(p,h);p.write_text("{}\n");assert not verify_frozen(p,h)


def test_combined_metrics_same_rows_and_not_cny_label():
    l=pd.DataFrame({"family":["X"]*6,"submodel":["S"]*6,"instrument":["COMBINED"]*6,"friction":["BASE"]*6,"pnl":[1,-1,2,-1,3,-1],"bars_held":[1]*6});m=metrics(l);assert m.trades.iloc[0]==len(l) and m.instrument.iloc[0]=="COMBINED" and np.isclose(m.profit_factor.iloc[0],2)


def test_exit_is_part_of_frozen_variant(tmp_path):
    p=tmp_path/"f";h=freeze(p,{"exit":"2R"});assert json.loads(p.read_text())["exit"]=="2R" and verify_frozen(p,h)
