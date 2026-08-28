import numpy as np
import pandas as pd
import pytest
from market_pattern_discovery.backtest.phase6b import prepare_frame,wilder_atr14,generate_signals,simulate,event_outcomes
from market_pattern_discovery.features.core import canonical_trading_date,build_core_features

def bars(values,day_split=None,opens=None,highs=None,lows=None,atr=.02):
    n=len(values); t=pd.date_range('2026-01-05 10:00',periods=n,freq='min',tz='Europe/Moscow')
    if day_split is not None:
        t=t.to_series().reset_index(drop=True); t.iloc[day_split:]=pd.date_range('2026-01-06 10:00',periods=n-day_split,freq='min',tz='Europe/Moscow'); t=pd.DatetimeIndex(t)
    c=np.array(values,float); o=np.array(opens if opens is not None else c,float); h=np.array(highs if highs is not None else np.maximum(o,c)+.001,float); l=np.array(lows if lows is not None else np.minimum(o,c)-.001,float)
    f=pd.DataFrame({'open':o,'high':h,'low':l,'close':c,'volume':1.,'instrument':'CNYRUBF','timeframe':'M1','open_time':t,'close_time':t+pd.Timedelta(minutes=1)})
    f['trading_date']=canonical_trading_date(f.open_time); f['atr14']=atr; return f

def event(f,i=14,side=1,strategy='X',atr=.1,ref=10):
    return pd.DataFrame([{'strategy_id':strategy,'bar_index':i,'side':'LONG' if side==1 else 'SHORT','direction':side,'ATR_at_signal':atr,'reference_level':ref,'signal_time':f.close_time.iloc[i],'instrument':'CNYRUBF'}])

def test_canonical_trading_date_agrees_with_feature_builder():
    f=bars([10]*20,day_split=10); prepared=prepare_frame(f.drop(columns=['trading_date','atr14']))
    built=build_core_features(f.drop(columns=['trading_date','atr14']),timeframe='M1').frame
    assert prepared.trading_date.tolist()==built.trading_date.tolist()==canonical_trading_date(f.open_time).tolist()

def test_wilder_atr_exact_formula_and_continuous_across_day_boundary():
    f=bars([10]*14+[12,12],day_split=14,highs=[10.1]*14+[12.1,12.1],lows=[9.9]*14+[11.9,11.9])
    a=wilder_atr14(f); assert a.iloc[13]==pytest.approx(.2)
    # overnight gap TR=2.1 and is incorporated, not reset/warmed up again
    assert a.iloc[14]==pytest.approx((.2*13+2.1)/14); assert np.isfinite(a.iloc[14])

def test_exact_prior_20_includes_t_minus_1_and_excludes_t():
    vals=[10]*21; h=[10.1]*21; l=[9.9]*21; h[19]=11; l[19]=9; h[20]=50; l[20]=1; vals[20]=10
    f=bars(vals,highs=h,lows=l); e=generate_signals(f,'CNYRUBF',('RH-02',))
    # Current extremes excluded; unique t-1 high/low are the references.
    got=e[e.bar_index.eq(20)].sort_values('side'); assert set(got.reference_level)=={9.,11.}

def test_time_has_no_fake_r_stop_has_r_and_friction_exactly_two_ticks():
    f=bars([10]*20); f.loc[15,'open']=10; f.loc[15:,'close']=10.02
    out=simulate(f,event(f),.001,configs=[('TIME_15',None,None,15),('STOP_1.0_TARGET_2.0',1.,2.,60)])
    timed=out[out.exit_configuration.eq('TIME_15')]; stopped=out[out.exit_configuration.str.startswith('STOP')]
    assert timed.pnl_R.isna().all() and timed.pnl_atr.notna().all() and timed.risk_price.isna().all()
    assert stopped.pnl_R.notna().all() and stopped.pnl_atr.notna().all()
    g=timed[timed.friction_scenario.eq('GROSS')].iloc[0]; b=timed[timed.friction_scenario.eq('BASE')].iloc[0]
    assert g.net_pnl_price-b.net_pnl_price==pytest.approx(.002)

def test_day_end_clips_path_and_next_day_extreme_is_irrelevant():
    f=bars([10]*17,day_split=16); f.loc[15,'open']=10; f.loc[16,['open','high','low','close']]=[100,101,.1,100]
    out=simulate(f,event(f,i=14),.001,configs=[('TIME_15',None,None,15)])
    assert (out.exit_reason=='DAY_END').all() and (out.exit_time==f.close_time.iloc[15]).all()
    assert (out.exit_price_raw==f.close.iloc[15]).all()

def test_round_breakout_binds_actual_crossed_level_and_future_mutation_causal():
    f=bars([11.70]*14+[11.749,11.776,12.0],highs=[11.701]*14+[11.75,11.777,12.1],lows=[11.699]*14+[11.748,11.748,11.0])
    e=generate_signals(f,'CNYRUBF',('RL-02',)); row=e[(e.strategy_id=='RL-02')&(e.bar_index==15)].iloc[0]
    assert row.reference_level==pytest.approx(11.75)
    prefix=generate_signals(f.iloc[:16].copy(),'CNYRUBF',('RL-02',)); assert e[e.bar_index<16][['bar_index','side','reference_level']].reset_index(drop=True).equals(prefix[['bar_index','side','reference_level']].reset_index(drop=True))

def test_retest_preserves_original_breakout_reference_and_expires():
    vals=[11.7]*14+[11.749,11.776,11.76,11.751]
    f=bars(vals,lows=[11.699]*14+[11.748,11.748,11.759,11.749],highs=[11.701]*14+[11.75,11.777,11.761,11.76])
    e=generate_signals(f,'CNYRUBF',('RL-04',)); row=e[e.strategy_id.eq('RL-04')].iloc[0]; assert row.reference_level==pytest.approx(11.75)
    late=bars([11.7]*14+[11.749,11.776]+[11.79]*6+[11.751]); assert generate_signals(late,'CNYRUBF',('RL-04',)).empty

@pytest.mark.parametrize('side,entry,next_open,expected',[(1,10,9.8,9.8),(-1,10,10.2,10.2)])
def test_stop_gap_long_and_short(side,entry,next_open,expected):
    vals=[10]*18; f=bars(vals); f.loc[15,'open']=entry; f.loc[16,['open','high','low','close']]=[next_open,max(next_open,10.3),min(next_open,9.7),next_open]
    out=simulate(f,event(f,side=side),.001,configs=[('STOP_1.0_TARGET_2.0',1.,2.,60)])
    g=out[out.friction_scenario.eq('GROSS')].iloc[0]; assert g.exit_reason=='STOP_GAP' and g.exit_price_raw==expected

def test_stop_target_tie_next_open_and_position_exclusivity():
    f=bars([10]*20); f.loc[15,'open']=10; f.loc[15,['high','low']]=[10.3,9.7]
    e=pd.concat([event(f),event(f)],ignore_index=True); out=simulate(f,e,.001,configs=[('STOP_1.0_TARGET_2.0',1.,2.,60)])
    assert len(out)==3 and (out.entry_time==f.open_time.iloc[15]).all() and (out.exit_reason=='STOP_FIRST_TIE').all()

def test_outcomes_use_next_open_same_day_and_do_not_feed_signals():
    f=bars([10]*22); f.loc[15,'open']=10.5; e=event(f)
    before=generate_signals(f,'CNYRUBF',('MOM-01',)); outcomes=event_outcomes(f,e); after=generate_signals(f,'CNYRUBF',('MOM-01',))
    assert outcomes.iloc[0].signed_move_atr==pytest.approx((10-10.5)/.1)
    pd.testing.assert_frame_equal(before,after)
    cross=bars([10]*18,day_split=16); assert event_outcomes(cross,event(cross)).empty
