import numpy as np
import pandas as pd
from market_pattern_discovery.backtest.phase6b import add_wilder_atr14,event_outcomes,generate_signals,metrics,simulate
from market_pattern_discovery.features.core import canonical_trading_date,build_core_features

def bars(values,dates=None,lows=None,highs=None,opens=None):
    n=len(values);t=pd.date_range('2026-01-05 10:00',periods=n,freq='min',tz='Europe/Moscow');c=np.array(values,float)
    lo=np.array(lows if lows is not None else c-.001,float);hi=np.array(highs if highs is not None else c+.001,float);op=np.array(opens if opens is not None else c,float)
    d=np.array(dates if dates is not None else t.date)
    return pd.DataFrame({'open':op,'high':np.maximum.reduce([hi,op,c]),'low':np.minimum.reduce([lo,op,c]),'close':c,'volume':1,'instrument':'CNYRUBF','timeframe':'M1','open_time':t,'close_time':t+pd.Timedelta(minutes=1),'trading_date':d,'atr14':.02,'tick':.001})

def event(f,i=14,side=1,strategy='X',atr=.1):
    return pd.DataFrame([{'strategy_id':strategy,'bar_index':i,'side':'LONG' if side==1 else 'SHORT','direction':side,'ATR_at_signal':atr,'reference_level':10.,'signal_time':f.close_time[i],'instrument':'CNYRUBF'}])

def test_canonical_trading_date_agrees_with_core_builder():
    f=bars([10]*4);f.loc[2:,'open_time']=pd.date_range('2026-01-06',periods=2,freq='min',tz='Europe/Moscow');f['close_time']=f.open_time+pd.Timedelta(minutes=1)
    assert canonical_trading_date(f.open_time).tolist()==build_core_features(f.drop(columns=['trading_date','atr14','tick']),timeframe='M1').frame.trading_date.tolist()

def test_wilder_atr_exact_and_continuous_over_day_boundary():
    f=bars([10]*16);f.loc[14:,'trading_date']=pd.Timestamp('2026-01-06').date();f.loc[14,'high']=12;f.loc[14,'low']=10
    x=add_wilder_atr14(f);tr=(f.high-f.low).to_numpy();expected=(tr[:14].mean()*13+2)/14
    assert np.isclose(x.atr14.iloc[14],expected) and np.isfinite(x.atr14.iloc[14])

def test_rolling_exact_previous_20_includes_tminus1_excludes_current():
    f=bars([10]*24);f.loc[19,'high']=11;f.loc[19,'low']=9;f.loc[20,['high','low','close']]=[12,8,10]
    e=generate_signals(f,'CNYRUBF',('RH-01','RH-02'))
    # Decision t=20 references unique t-1 extremes, not current extremes and not an omitted t-1.
    refs=e[e.bar_index.eq(20)].reference_level.tolist();assert 11 in refs and 9 in refs and 12 not in refs and 8 not in refs

def test_time_has_atr_not_fake_r_and_stop_has_both():
    f=bars([10+i*.01 for i in range(40)]);out=simulate(f,event(f),.001)
    time=out[out.exit_configuration.eq('TIME_15')];stop=out[out.exit_configuration.eq('STOP_1.0_TARGET_1.0')]
    assert time.pnl_R.isna().all() and time.pnl_atr.notna().all() and time.risk_price.isna().all()
    assert stop.pnl_R.notna().all() and stop.pnl_atr.notna().all() and stop.risk_price.notna().all()

def test_day_end_blocks_next_day_extreme():
    d=[pd.Timestamp('2026-01-05').date()]*17+[pd.Timestamp('2026-01-06').date()]*3
    f=bars([10]*17+[100,100,100],dates=d);out=simulate(f,event(f,14),.001,[('TIME_15',None,None,15)])
    assert (out.exit_reason=='DAY_END').all() and (out.exit_time==f.close_time[16]).all() and np.allclose(out[out.friction_scenario=='GROSS'].net_pnl_price,0)

def test_rl02_binds_actual_crossed_11750():
    v=[11.70]*14+[11.749,11.776];f=bars(v,lows=[x-.001 for x in v],highs=[x+.001 for x in v])
    e=generate_signals(f,'CNYRUBF',('RL-02',));x=e[(e.strategy_id=='RL-02')&(e.side=='LONG')]
    x=x[x.bar_index.eq(15)];assert len(x)==1 and np.isclose(x.reference_level.iloc[0],11.75)

def test_retest_preserves_breakout_level_and_expires():
    v=[11.7]*14+[11.749,11.776,11.751];lo=[x-.001 for x in v];lo[-1]=11.749
    e=generate_signals(bars(v,lows=lo,highs=[x+.001 for x in v]),'CNYRUBF',('RL-04',));assert np.isclose(e.reference_level.iloc[0],11.75)
    v=[11.7]*14+[11.749,11.776]+[11.79]*6+[11.751];e=generate_signals(bars(v),'CNYRUBF',('RL-04',));assert e.empty

def test_long_and_short_stop_gaps():
    f=bars([10]*22);f.loc[16,['open','high','low','close']]=[9.8,9.9,9.7,9.8]
    out=simulate(f,event(f,14,1),.001,[('STOP',1.,1.,60)]);assert set(out.exit_reason)=={'STOP_GAP'} and np.allclose(out.exit_price_raw,9.8)
    f=bars([10]*22);f.loc[16,['open','high','low','close']]=[10.2,10.3,10.1,10.2]
    out=simulate(f,event(f,14,-1),.001,[('STOP',1.,1.,60)]);assert set(out.exit_reason)=={'STOP_GAP'} and np.allclose(out.exit_price_raw,10.2)

def test_tie_next_open_friction_exact_and_exclusivity():
    f=bars([10]*25);f.loc[15,['open','high','low','close']]=[10.03,10.2,9.9,10.03]
    e=pd.concat([event(f,14),event(f,14)],ignore_index=True);out=simulate(f,e,.001,[('STOP',.5,1.,60)])
    assert len(out)==3 and (out.entry_time==f.open_time[15]).all() and set(out.exit_reason)=={'STOP_FIRST_TIE'}
    g=out[out.friction_scenario=='GROSS'].net_pnl_price.iloc[0];b=out[out.friction_scenario=='BASE'].net_pnl_price.iloc[0];assert np.isclose(g-b,.002)

def test_future_mutation_and_outcomes_cannot_change_signal():
    v=[11.7]*14+[11.749,11.776]+[11.78]*10;f=bars(v);before=generate_signals(f,'CNYRUBF',('RL-02',));event_outcomes(f,before)
    f.loc[20:,['high','low','close']]=[20,1,15];after=generate_signals(f,'CNYRUBF',('RL-02',))
    assert before[before.bar_index<20][['bar_index','reference_level']].equals(after[after.bar_index<20][['bar_index','reference_level']].reset_index(drop=True))

def test_event_outcome_uses_next_open_and_never_crosses_day():
    d=[pd.Timestamp('2026-01-05').date()]*20+[pd.Timestamp('2026-01-06').date()]*10;f=bars([10]*30,dates=d);f.loc[15,'open']=11
    o=event_outcomes(f,event(f,14),);assert np.isclose(o[o.horizon==5].signed_move_atr.iloc[0],-10) and not (o.horizon>5).any()

def test_zero_signal_execution_produces_valid_empty_v3_tables():
    f=bars([10]*20);empty=generate_signals(f,'CNYRUBF',('RL-02',))
    ledger=simulate(f,empty,.001,[('TIME_15',None,None,15)])
    summary=metrics(ledger)
    assert ledger.empty and summary.empty
    assert {'entry_time','pnl_atr','friction_scenario'} <= set(ledger)
    assert {'profit_factor_ATR','expectancy_ATR','recovery_factor_ATR'} <= set(summary)
