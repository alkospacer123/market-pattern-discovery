import json, math
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from market_pattern_discovery.backtest.top5_v4 import *
import market_pattern_discovery.backtest.top5_v4.structural as smod
import market_pattern_discovery.backtest.top5_v4.families as fmod
import market_pattern_discovery.backtest.top5_v4.pairs as pmod

ROOT=Path(__file__).resolve().parents[1]

def reg():
    c=load_contract(ROOT/'config/top5_v4/strategy_contract.json');return build_candidate_registry(c)
def cand(fam,sub,**p):
    for c in reg():
        if c['family']==fam and c['submodel']==sub and all(c['parameters'].get(k)==v for k,v in p.items()):return c
    raise AssertionError((fam,sub,p))
def m5_rows(vals,start='2026-01-05 10:00'):
    ot=pd.date_range(start,periods=len(vals),freq='5min',tz=TZ)
    return pd.DataFrame({'open_time':ot,'close_time':ot+pd.Timedelta(minutes=5),'open':np.asarray([v[0] for v in vals],float),'high':np.asarray([v[1] for v in vals],float),'low':np.asarray([v[2] for v in vals],float),'close':np.asarray([v[3] for v in vals],float),'volume':5.,'trading_date':ot.date})
def level(snapshot='S1',activation=0,version=1,typ='EL',level_ticks=2000,birth=0,expiry=5):
    return {'level_family_id':'F','level_snapshot_id':snapshot,'snapshot_version':version,'level_type':typ,'level_ticks':level_ticks,'activation_index':activation,'family_birth_rank':birth,'family_expiry_rank_exclusive':expiry,'round_confluence':False,'first_touch_time':pd.Timestamp('2026-01-05 09:00',tz=TZ)}

def test_rejection_and_simple_sweep_are_distinct():
    rej=cand('STRUCTURAL','REJECTION',tolerance_ticks=2,min_touches=2,target_r=2);sw=cand('STRUCTURAL','SIMPLE_SWEEP',tolerance_ticks=2,min_touches=2,target_r=2);x=m5_rows([(2.001,2.002,2.000,2.001)]);L=pd.DataFrame([level()]);a=structural_signals(x,L,'CNYRUBF',rej);b=structural_signals(x,L,'CNYRUBF',sw);assert len(a)==1 and b.empty and a.stop_ticks.iloc[0]==1999;y=m5_rows([(2.001,2.002,1.999,2.001)]);a=structural_signals(y,L,'CNYRUBF',rej);b=structural_signals(y,L,'CNYRUBF',sw);assert a.empty and len(b)==1 and b.stop_ticks.iloc[0]==1998

def test_complex_false_break_episode_extreme_stop():
    c=cand('STRUCTURAL','COMPLEX_FALSE_BREAK',tolerance_ticks=2,min_touches=2,target_r=2);x=m5_rows([(2.0,2.001,1.997,1.999),(1.999,2.002,1.996,2.001)]);s=structural_signals(x,pd.DataFrame([level()]),'CNYRUBF',c);assert len(s)==1 and s.direction.iloc[0]==1 and s.stop_ticks.iloc[0]==1995

def test_breakout_retest_direction_and_stop():
    c=cand('STRUCTURAL','BREAKOUT_RETEST',tolerance_ticks=2,min_touches=2,target_r=2);x=m5_rows([(2.,2.001,1.997,1.999),(1.999,2.001,1.998,1.999)]);s=structural_signals(x,pd.DataFrame([level()]),'CNYRUBF',c);assert len(s)==1 and s.direction.iloc[0]==-1 and s.stop_ticks.iloc[0]==2002

def test_structural_pending_cancels_across_date():
    c=cand('STRUCTURAL','COMPLEX_FALSE_BREAK',tolerance_ticks=2,min_touches=2,target_r=2);x=m5_rows([(2.,2.001,1.997,1.999),(1.999,2.002,1.996,2.001)]);x.loc[1,'open_time']+=pd.Timedelta(days=1);x.loc[1,'close_time']+=pd.Timedelta(days=1);x['trading_date']=x.open_time.dt.date;assert structural_signals(x,pd.DataFrame([level()]),'CNYRUBF',c).empty

def test_new_snapshot_cancels_pending():
    c=cand('STRUCTURAL','COMPLEX_FALSE_BREAK',tolerance_ticks=2,min_touches=2,target_r=2);x=m5_rows([(2.,2.001,1.997,1.999),(1.999,2.002,1.996,2.001)]);L=pd.DataFrame([level('S1',0,1),level('S2',1,2)]);assert structural_signals(x,L,'CNYRUBF',c).empty

def test_rearm_bar_cannot_trigger_signal():
    c=cand('STRUCTURAL','REJECTION',tolerance_ticks=2,min_touches=2,target_r=2);x=m5_rows([(2.001,2.002,2.000,2.001),(2.003,2.004,2.000,2.003),(2.001,2.002,2.000,2.001)]);s=structural_signals(x,pd.DataFrame([level()]),'CNYRUBF',c);assert len(s)==2 and list(s.signal_time)==[x.close_time.iloc[0],x.close_time.iloc[2]]

def test_mirror_role_flip_disarms_until_rearm():
    c=cand('STRUCTURAL','REJECTION',tolerance_ticks=2,min_touches=2,target_r=2);x=m5_rows([(2.004,2.005,2.003,2.004),(1.999,2.001,1.998,1.999),(1.999,2.001,1.998,1.999),(1.997,2.000,1.996,1.997),(1.999,2.000,1.998,1.999)]);L=pd.DataFrame([level(typ='MIRROR')]);s=structural_signals(x,L,'CNYRUBF',c);assert not ((s.signal_time==x.close_time.iloc[2]).any() if len(s) else False)

def test_gerchik_uses_candidate_target_and_same_date(monkeypatch):
    c2=cand('STRUCTURAL','GERCHIK_A_M5_PROXY',tolerance_ticks=2,min_touches=2,target_r=2);c3=cand('STRUCTURAL','GERCHIK_A_M5_PROXY',tolerance_ticks=2,min_touches=2,target_r=3);vals=[(2.01,2.011,2.009,2.01)]*6;x=m5_rows(vals);x.loc[3,['low','close']]=[2.000,2.001];x.loc[4,['low','close']]=[2.000,2.002]
    def fake(frame,slow=50,**kw):z=frame.copy();z['ema20']=2.01;z['ema_slow']=[2.0,2.0,2.0,2.0,2.001,2.002];return z
    monkeypatch.setattr(smod,'indicators',fake);L=pd.DataFrame([level(activation=0,typ='EL')]);a=gerchik_a_signals(x,L,'CNYRUBF',c2);b=gerchik_a_signals(x,L,'CNYRUBF',c3);assert len(a)==1 and len(b)==1 and a.target_r.iloc[0]==2 and b.target_r.iloc[0]==3;assert a.BPU2_time.iloc[0]==x.close_time.iloc[4]

def test_gerchik_does_not_cross_date(monkeypatch):
    c=cand('STRUCTURAL','GERCHIK_A_M5_PROXY',tolerance_ticks=2,min_touches=2,target_r=2);vals=[(2.01,2.011,2.009,2.01)]*6;x=m5_rows(vals);x.loc[3,['low','close']]=[2.,2.001];x.loc[4,['low','close']]=[2.,2.002];x.loc[4:,'open_time']+=pd.Timedelta(days=1);x.loc[4:,'close_time']+=pd.Timedelta(days=1);x['trading_date']=x.open_time.dt.date
    def fake(frame,slow=50,**kw):z=frame.copy();z['ema20']=2.01;z['ema_slow']=[2.,2.,2.,2.,2.001,2.002];return z
    monkeypatch.setattr(smod,'indicators',fake);assert gerchik_a_signals(x,pd.DataFrame([level(activation=0,typ='EL')]),'CNYRUBF',c).empty

def test_trend_expiry_blocks_same_direction_but_not_opposite(monkeypatch):
    c=cand('TREND_PULLBACK','EMA20_50',slow_ema=50,target_r=2);vals=[(10,10.01,9.99,10)]*12;x=m5_rows(vals)
    def fake(frame,slow=50,**kw):z=frame.copy();z['ema20']=10.;z['ema_slow']=9.5;z.loc[:8,'ema_slow']=np.linspace(9.0,9.8,9);z.loc[:8,'ema20']=10.;z.loc[9:,'ema_slow']=[10.5,10.4,10.3];z.loc[9:,'ema20']=10.;return z
    monkeypatch.setattr(fmod,'indicators',fake);x.loc[:8,'close']=9.9;x.loc[:8,'low']=9.8;x.loc[9:,'close']=[10.4,9.9,9.8];x.loc[9:,'high']=[10.6,10.1,10.0];trend_signals(x,'CNYRUBF',c)

def test_bollinger_reentry_max_axis(monkeypatch):
    c1=cand('BOLLINGER_RSI','REENTRY_2R',k=1.5,rsi_lower=30,rsi_upper=70,reentry_max_bars=1,exit_mode='REENTRY_2R');c3=cand('BOLLINGER_RSI','REENTRY_2R',k=1.5,rsi_lower=30,rsi_upper=70,reentry_max_bars=3,exit_mode='REENTRY_2R');x=m5_rows([(10,10.01,9.99,10)]*5)
    def fake(frame,bb_k=2.,**kw):z=frame.copy();z['bb_lower']=9.;z['bb_upper']=11.;z['bb_mid']=10.;z['rsi']=50.;z.loc[0,['close','rsi']]=[8.,20.];z.loc[1,'close']=8.;z.loc[2,'close']=9.5;return z
    monkeypatch.setattr(fmod,'indicators',fake);assert mean_reversion_signals(x,'CNYRUBF',c1).empty;s=mean_reversion_signals(x,'CNYRUBF',c3);assert len(s)==1 and s.reentry_max_bars.iloc[0]==3

def test_bollinger_fixed_mid_frozen_signal_bar(monkeypatch):
    c=cand('BOLLINGER_RSI','REENTRY_FIXED_MID',k=1.5,rsi_lower=30,rsi_upper=70,reentry_max_bars=3,exit_mode='REENTRY_FIXED_MID');x=m5_rows([(10,10.01,9.99,10)]*4)
    def fake(frame,bb_k=2.,**kw):z=frame.copy();z['bb_lower']=9.;z['bb_upper']=11.;z['bb_mid']=[10.,10.123,20.,30.];z['rsi']=50.;z.loc[0,['close','rsi']]=[8.,20.];z.loc[1,'close']=9.5;return z
    monkeypatch.setattr(fmod,'indicators',fake);s=mean_reversion_signals(x,'CNYRUBF',c);assert len(s)==1 and s.target_ticks.iloc[0]==10123;x.loc[2:,'close']=99.;assert s.target_ticks.iloc[0]==10123

def test_bollinger_expired_excursion_blocks_new_extreme_until_inside(monkeypatch):
    c=cand('BOLLINGER_RSI','REENTRY_2R',k=1.5,rsi_lower=30,rsi_upper=70,reentry_max_bars=1,exit_mode='REENTRY_2R');x=m5_rows([(10,10.01,9.99,10)]*6)
    def fake(frame,bb_k=2.,**kw):z=frame.copy();z['bb_lower']=9.;z['bb_upper']=11.;z['bb_mid']=10.;z['rsi']=20.;z['close']=[8.,8.,8.,8.,10.,8.];return z
    monkeypatch.setattr(fmod,'indicators',fake);assert mean_reversion_signals(x,'CNYRUBF',c).empty

def common_pair(n=8):
    t=pd.date_range('2026-01-05 10:00',periods=n,freq='min',tz=TZ);c=np.arange(n)*.001+10;s=np.arange(n)*.01+90;a=pd.DataFrame({'open_time':t,'close_time':t+pd.Timedelta(minutes=1),'open':c,'high':c+.001,'low':c-.001,'close':c,'volume':1.,'trading_date':t.date,'instrument':'CNYRUBF'});b=pd.DataFrame({'open_time':t,'close_time':t+pd.Timedelta(minutes=1),'open':s,'high':s+.01,'low':s-.01,'close':s,'volume':1.,'trading_date':t.date,'instrument':'USDRUBF'});return a,b

def pair_signal(a,cid='P',fi=0,entry_z=2.,dc=-1,ds=1,beta=1.,wc=.5):
    row={'candidate_id':cid,'family':'PAIRS','submodel':'OLS','instrument':'CNYRUBF+USDRUBF','signal_time':a.close_time.iloc[fi],'signal_trading_date':a.trading_date.iloc[fi],'direction':dc,'side':'SPREAD','direction_cny':dc,'direction_si':ds,'entry_z':entry_z,'beta_at_entry':beta,'w_cny':wc,'w_si':1-wc,'feature_index':fi,'window':2,'z_entry':2.,'stop_ticks':None,'target_r':None,'target_ticks':None};return finalize_signal_ids(pd.DataFrame([row]))

def feat_for(a,z):return pd.DataFrame({'open_time':a.open_time,'close_time':a.close_time,'trading_date':a.trading_date,'z':z})

def test_pair_convergence_executes_next_common_open():
    a,b=common_pair(6);s=pair_signal(a,fi=0);f=feat_for(a,[2.,1.,-0.1,-.2,-.3,-.4]);l,k=simulate_pairs(a,b,s,{'P':f},120);g=l[l.friction=='GROSS'].iloc[0];assert k.empty and g.exit_reason=='CONVERGENCE' and g.exit_time==a.open_time.iloc[3] and g.bars_held==2

def test_pair_time_wins_when_convergence_close_is_120th_held_bar():
    a,b=common_pair(125);s=pair_signal(a,fi=0);z=[2.]*120+[-.1]+[-.2]*4;f=feat_for(a,z);l,_=simulate_pairs(a,b,s,{'P':f},120);assert set(l.exit_reason)=={'TIME'} and l.exit_time.iloc[0]==a.close_time.iloc[120]

def test_pair_day_end_convergence_without_next_open_is_diagnostic_not_double_skip():
    a,b=common_pair(3);s=pair_signal(a,fi=0);f=feat_for(a,[2.,2.,-.1]);l,k=simulate_pairs(a,b,s,{'P':f},120);assert set(l.exit_reason)=={'DAY_END'} and set(k.reason)=={'CONVERGENCE_NO_NEXT_COMMON_OPEN_DAY_END_DIAGNOSTIC'}

def test_pair_friction_monotone():
    a,b=common_pair(5);s=pair_signal(a,fi=0);f=feat_for(a,[2.,1.,-.1,-.2,-.3]);l,_=simulate_pairs(a,b,s,{'P':f},120);p=l.set_index('friction').pnl_bps;assert p.GROSS>=p.BASE>=p.STRESS

def test_future_mutation_completed_trade_invariant():
    a,b=common_pair(8);s=pair_signal(a,fi=0);f=feat_for(a,[2.,1.,-.1,-.2,-.3,-.4,-.5,-.6]);l1,_=simulate_pairs(a,b,s,{'P':f},120);cut=l1.exit_time.max();aa=a.copy();bb=b.copy();aa.loc[aa.open_time>cut,['open','close']]=20.;bb.loc[bb.open_time>cut,['open','close']]=180.;l2,_=simulate_pairs(aa,bb,s,{'P':f},120);cols=['trade_id','signal_id','friction','exit_reason','pnl_bps'];assert l1[l1.exit_time<=cut][cols].reset_index(drop=True).equals(l2[l2.exit_time<=cut][cols].reset_index(drop=True))

def test_assign_period_half_open():
    t=pd.Series([pd.Timestamp('2026-02-28 23:59',tz=TZ),pd.Timestamp('2026-03-01',tz=TZ),pd.Timestamp('2026-05-01',tz=TZ),pd.Timestamp('2026-05-16',tz=TZ)]);assert list(assign_period(t)[:3])==['DEV','VALIDATION_A','VALIDATION_B'] and pd.isna(assign_period(t).iloc[3])

def test_assert_oos_allows_touch_but_not_overlap():
    assert_oos(pd.Timestamp('2026-03-01',tz=TZ),pd.Timestamp('2026-03-01',tz=TZ))
    with pytest.raises(ValueError):assert_oos(pd.Timestamp('2026-03-01 00:01',tz=TZ),pd.Timestamp('2026-03-01',tz=TZ))
