import pandas as pd
import numpy as np

from market_pattern_discovery.backtest.phase6b import generate_signals, simulate


def bars(values, lows=None, highs=None):
    t=pd.date_range("2026-01-05 10:00",periods=len(values),freq="min",tz="Europe/Moscow")
    close=np.asarray(values,float); low=np.asarray(lows if lows is not None else close-.001); high=np.asarray(highs if highs is not None else close+.001)
    return pd.DataFrame({"open":close,"high":high,"low":low,"close":close,"volume":1,"instrument":"CNYRUBF","timeframe":"M1",
      "open_time":t,"close_time":t+pd.Timedelta(minutes=1),"trading_date":t.date,"atr14":.02,"tick":.001})


def test_round_breakout_rejection_false_breakout_and_momentum_are_causal():
    f=bars([10.00]*14+[10.049,10.052,10.051,10.051,10.07,10.08,10.09],
           lows=[9.999]*14+[10.048,10.049,10.048,10.049,10.069,10.079,10.089],
           highs=[10.001]*14+[10.050,10.053,10.052,10.052,10.071,10.081,10.091])
    e=generate_signals(f,"CNYRUBF")
    assert ((e.strategy_id=="RL-02") & (e.bar_index==15)).any()
    # Changing bars strictly after a decision cannot change its event set.
    prefix=generate_signals(f.iloc[:17].copy(),"CNYRUBF")
    assert set(map(tuple,e[e.bar_index<17][["strategy_id","bar_index","side"]].to_numpy())) == set(map(tuple,prefix[["strategy_id","bar_index","side"]].to_numpy()))
    assert (e.strategy_id=="MOM-01").any()


def test_next_open_tie_stop_first_friction_and_exclusivity():
    f=bars([10]*18); f.loc[15,"close"]=10.02; f.loc[16,["open","close"]]=[10.03,10.03]; f.loc[16,["low","high"]]=[9.9,10.2]
    e=pd.DataFrame([{"strategy_id":"X","bar_index":15,"side":"LONG","direction":1,"ATR_at_signal":.1,"reference_level":10.,"signal_time":f.close_time[15],"instrument":"CNYRUBF"},
                    {"strategy_id":"X","bar_index":15,"side":"LONG","direction":1,"ATR_at_signal":.1,"reference_level":10.,"signal_time":f.close_time[15],"instrument":"CNYRUBF"}])
    out=simulate(f,e,.001); cell=out[out.exit_configuration=="STOP_0.5_TARGET_1.0"]
    assert len(cell)==3  # duplicate/overlapping signal cannot pyramid, one trade x three friction cases
    assert (cell.entry_time==f.open_time[16]).all()
    assert (cell.exit_reason=="STOP_FIRST_TIE").all()
    gross=cell[cell.friction_scenario=="GROSS"].pnl_R.iloc[0]; base=cell[cell.friction_scenario=="BASE"].pnl_R.iloc[0]
    assert base < gross


def test_nr7_rolling_and_previous_day_breakouts():
    f=bars([10+(.001*i) for i in range(50)])
    # two explicit days, making previous-day levels causally available
    f.loc[30:,"trading_date"]=pd.Timestamp("2026-01-06").date()
    f.loc[30:,"open_time"]=pd.date_range("2026-01-06 10:00",periods=20,freq="min",tz="Europe/Moscow")
    f.loc[30:,"close_time"]=f.loc[30:,"open_time"]+pd.Timedelta(minutes=1)
    f.loc[31,["open","close","high"]]=[10.0,10.1,10.101]
    e=generate_signals(f,"CNYRUBF")
    assert (e.strategy_id=="RH-01").any()
    assert (e.strategy_id=="PD-01").any()
    assert (e.strategy_id=="NR-01").any()


def test_retest_state_expires_after_five_bars():
    vals=[10.0]*14+[10.049,10.052]+[10.08]*6+[10.051]
    f=bars(vals)
    e=generate_signals(f,"CNYRUBF")
    assert not ((e.strategy_id=="RL-04") & (e.bar_index==22)).any()
