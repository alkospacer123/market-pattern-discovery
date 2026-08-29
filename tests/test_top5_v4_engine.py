import copy, json, math
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from market_pattern_discovery.backtest.top5_v4 import *
import market_pattern_discovery.data.finam_v4 as fv4
from market_pattern_discovery.data.finam_v4 import IngestionError, load_finam_window_many, raw_file_hash_event, assert_no_ohlcv_materialized

ROOT=Path(__file__).resolve().parents[1]

def m1(n=20, instrument='CNYRUBF', start='2026-01-05 10:00', close=None):
    tick=float(TICKS[instrument])
    t=pd.date_range(start, periods=n, freq='min', tz=TZ)
    if close is None:
        base=10.0 if instrument=='CNYRUBF' else 90.0
        c=np.array([base]*n,float)
    else:c=np.asarray(close,float)
    return pd.DataFrame({'open_time':t,'close_time':t+pd.Timedelta(minutes=1),'open':c,'high':c+tick,'low':c-tick,'close':c,'volume':1.,'trading_date':t.date,'instrument':instrument})

def m5(close, highs=None, lows=None, start='2026-01-05 10:00', instrument='CNYRUBF'):
    tick=float(TICKS[instrument]); c=np.asarray(close,float); n=len(c)
    ot=pd.date_range(start,periods=n,freq='5min',tz=TZ)
    h=np.asarray(highs if highs is not None else c+tick,float);l=np.asarray(lows if lows is not None else c-tick,float)
    return pd.DataFrame({'open_time':ot,'close_time':ot+pd.Timedelta(minutes=5),'open':c,'high':h,'low':l,'close':c,'volume':5.,'trading_date':ot.date})

def contract_registry():
    c=load_contract(ROOT/'config/top5_v4/strategy_contract.json')
    d=json.loads((ROOT/'config/top5_v4/candidate_registry.json').read_text())
    return c,build_candidate_registry(c),d

def cand(reg,fam,sub,**params):
    for c in reg:
        if c['family']==fam and c['submodel']==sub and all(c['parameters'].get(k)==v for k,v in params.items()):return c
    raise AssertionError((fam,sub,params))

def sigrow(x, *, cid='C1', direction=1, stop_ticks=9990, target_r=2., target_ticks=None, instrument='CNYRUBF'):
    row=_signal(cid,'X','Y',instrument,x.close_time.iloc[0],x.trading_date.iloc[0],direction,stop_ticks,target_r,target_ticks)
    return finalize_signal_ids(pd.DataFrame([row]))

def test_contract_and_registry_exact():
    c,r,d=contract_registry(); assert validate_contract(c,d)
    assert len(r)==142 and sum(x['selection_eligible'] for x in r)==136
    assert len({x['candidate_id'] for x in r})==142
    assert all('instrument' not in x['parameters'] for x in r)
    assert sum(x['family']=='ORB' and x['submodel']=='FAILED_BREAKOUT_DIAGNOSTIC' for x in r)==6
    assert all(not x['selection_eligible'] for x in r if x['submodel']=='FAILED_BREAKOUT_DIAGNOSTIC')

def test_complexity_is_active_axes():
    _,r,_=contract_registry()
    assert all(c['complexity']==len(c['active_grid_axes']) for c in r)
    assert {c['complexity'] for c in r if c['family']=='ORB' and c['submodel']=='DIRECT'}=={4}
    assert {c['complexity'] for c in r if c['family']=='ORB' and c['submodel']=='BREAKOUT_RETEST'}=={3}

def test_candidate_id_changes_when_semantics_change():
    c,_,_=contract_registry(); a=build_candidate_registry(c)[0]['candidate_id']; b=copy.deepcopy(c); b['round_steps']['CNYRUBF']=0.1
    assert build_candidate_registry(b)[0]['candidate_id']!=a

def test_candidate_id_does_not_have_instrument_axis():
    _,r,_=contract_registry(); assert not any('instrument' in c['active_grid_axes'] for c in r)

def test_sample_tiers_frozen():
    assert [sample_tier(x) for x in (0,19,20,49,50,99,100)]==['VERY_LOW','VERY_LOW','LOW','LOW','MODERATE','MODERATE','BETTER']

def test_round_half_up_and_tick_conversion():
    assert round_to_tick(1.2345,.001)==1.235
    assert price_to_ticks(1.2345,.001)==1235
    assert _half_up_int('2.5')==3 and _half_up_int('-2.5')==-3

def test_prepare_m1_rejects_off_minute_and_off_tick():
    x=m1(3); x.loc[1,'open_time'] += pd.Timedelta(seconds=30); x.loc[1,'close_time'] += pd.Timedelta(seconds=30)
    with pytest.raises(ValueError,match='whole-minute|exact 1-minute'):prepare_m1(x,'CNYRUBF')
    y=m1(3); y.loc[1,'close']=10.0005
    with pytest.raises(ValueError,match='off instrument tick'):prepare_m1(y,'CNYRUBF')

def test_causal_m5_exact_expected_minutes_and_stamp():
    x=m1(11); z=causal_m5(x); assert len(z)==2 and z.open_time.iloc[0].minute==0 and z.close_time.iloc[0].minute==5
    assert causal_m5(x.drop(index=2).reset_index(drop=True)).shape[0]==1

def test_m5_never_crosses_moscow_date():
    x=m1(5,start='2026-01-05 23:58'); z=causal_m5(x); assert z.empty

def test_pivot_known_at_j_plus_2_and_future_mutation():
    x=m5([1,2,3,2,1,1,1]); p=confirmed_pivots(x,'CNYRUBF'); h=p[p.side=='HIGH'].iloc[0]
    assert h.pivot_index==2 and h.known_index==4 and h.known_time==x.close_time.iloc[4]
    y=x.copy(); y.loc[5:,'high']=50.; q=confirmed_pivots(y,'CNYRUBF')
    assert p[p.known_index<5][['side','pivot_index','known_index','price_ticks']].reset_index(drop=True).equals(q[q.known_index<5][['side','pivot_index','known_index','price_ticks']].reset_index(drop=True))

def test_snapshot_activation_is_first_open_at_or_after_known_time():
    x=m5([1,2,3,2,1,2,3.001,2,1]); p=confirmed_pivots(x,'CNYRUBF'); first=p.iloc[0]
    ix=_activation_index(x,first.known_time); assert x.open_time.iloc[ix]>=first.known_time
    assert x.open_time.iloc[ix-1]<first.known_time

def test_structural_snapshot_immutable_and_grid_identity():
    x=m5([1,2,3,2,1,2,3.001,2,1,2,3.002,2,1,2,1]); z=structural_levels(x,'CNYRUBF',3,2); eh=z[z.level_type=='EH']
    assert len(eh)>=2 and eh.snapshot_version.is_monotonic_increasing
    assert eh.level_family_id.nunique()==1 and 'tol=3|touches=2' in eh.level_family_id.iloc[0]
    first=eh.iloc[0]; assert first.touch_count==2 and eh.iloc[-1].touch_count>=3

def test_structural_family_lifetime_is_five_market_dates():
    c,_,_=contract_registry(); assert c['family_rules']['STRUCTURAL']['level_family']['lifetime_market_trading_dates']==5

def test_flat_rsi_is_nan():
    x=indicators(m5(np.ones(30)*10)); assert math.isnan(x.rsi.iloc[-1])

def test_ema_and_bb_are_continuous_across_dates():
    x=m5(np.linspace(10,11,30)); x.loc[15:,'open_time']+=pd.Timedelta(days=1);x.loc[15:,'close_time']+=pd.Timedelta(days=1);x['trading_date']=x.open_time.dt.date
    z=indicators(x); assert np.isfinite(z.ema20.iloc[15]) and np.isfinite(z.bb_mid.iloc[19])

def test_orb_direct_exact_opening_range_and_midpoint():
    _,r,_=contract_registry(); c=cand(r,'ORB','DIRECT',length=5,stop_mode='STOP_MIDPOINT',target_r=2.0)
    x=m1(10); x.loc[:4,['high','low','close']]=[10.01,9.99,10.0]; x.loc[5,['high','low','close']]=[10.02,10.0,10.02]
    s=orb_signals(x,'CNYRUBF',c); assert len(s)==1 and s.direction.iloc[0]==1
    assert s.stop_ticks.iloc[0]==10000

def test_orb_missing_expected_minute_invalidates_day():
    _,r,_=contract_registry(); c=cand(r,'ORB','DIRECT',length=5,stop_mode='STOP_OPPOSITE_OR',target_r=2.0)
    x=m1(10).drop(index=2).reset_index(drop=True); assert orb_signals(x,'CNYRUBF',c).empty

def test_orb_first_breakout_only():
    _,r,_=contract_registry(); c=cand(r,'ORB','DIRECT',length=5,stop_mode='STOP_OPPOSITE_OR',target_r=2.0)
    x=m1(12);x.loc[:4,['high','low','close']]=[10.01,9.99,10.0];x.loc[5,['high','low','close']]=[10.02,10,10.02];x.loc[7,['high','low','close']]=[10,9.98,9.98]
    assert len(orb_signals(x,'CNYRUBF',c))==1

def test_orb_failed_diagnostic_both_direction_and_age():
    _,r,_=contract_registry(); c=cand(r,'ORB','FAILED_BREAKOUT_DIAGNOSTIC',length=5,target_r=2.0)
    x=m1(12);x.loc[:4,['high','low','close']]=[10.01,9.99,10];x.loc[5,['high','low','close']]=[10.02,10,10.02];x.loc[6,['high','low','close']]=[10.015,9.995,10]
    s=orb_signals(x,'CNYRUBF',c); assert len(s)==1 and s.direction.iloc[0]==-1 and s.breakout_age_valid_bars.iloc[0]==1

def test_pair_distance_matches_reference_after_one_window():
    n=30; c=np.linspace(10,12,n)+np.sin(np.arange(n))*.01; s=np.linspace(90,92,n)+np.cos(np.arange(n))*.02
    a=m1(n,close=np.round(c,3)); b=m1(n,'USDRUBF',close=np.round(s,2)); z=pair_features(a,b,10,'DISTANCE')
    i=20;carr=a.close.to_numpy();sarr=b.close.to_numpy();c0,s0=carr[i-10],sarr[i-10];hist=carr[i-10:i]/c0-sarr[i-10:i]/s0;cur=carr[i]/c0-sarr[i]/s0
    ref=(cur-hist.mean())/hist.std(ddof=1); assert np.isclose(z.z.iloc[i],ref,rtol=1e-10,atol=1e-10)

def test_pair_ols_excludes_current_and_future():
    a=m1(30,close=np.round(np.linspace(10,11,30),3));b=m1(30,'USDRUBF',close=np.round(np.linspace(90,92,30),2));before=pair_features(a,b,10,'OLS').beta.iloc[20]
    aa=a.copy();aa.loc[20:,'close']=20.;after=pair_features(aa,b,10,'OLS').beta.iloc[20];assert before==after

def test_pair_unknown_to_outside_does_not_enter(monkeypatch):
    _,r,_=contract_registry(); c=cand(r,'PAIRS','DISTANCE',window=240,z_entry=2.0)
    x=m1(4); f=pair_frame(x,m1(4,'USDRUBF')); f['z']=[2.5,2.6,1.,2.2];f['beta']=1.;f['spread']=f.z
    monkeypatch.setattr('market_pattern_discovery.backtest.top5_v4.pairs.pair_features',lambda *a,**k:f)
    s,_=pair_signals(x,m1(4,'USDRUBF'),c); assert len(s)==1 and s.feature_index.iloc[0]==3

def test_pair_nan_does_not_rearm(monkeypatch):
    _,r,_=contract_registry(); c=cand(r,'PAIRS','DISTANCE',window=240,z_entry=2.0)
    x=m1(5); f=pair_frame(x,m1(5,'USDRUBF')); f['z']=[0.,2.1,np.nan,2.2,1.];f['beta']=1.;f['spread']=f.z
    monkeypatch.setattr('market_pattern_discovery.backtest.top5_v4.pairs.pair_features',lambda *a,**k:f)
    s,_=pair_signals(x,m1(5,'USDRUBF'),c); assert len(s)==1

def test_pair_negative_beta_leg_direction(monkeypatch):
    _,r,_=contract_registry(); c=cand(r,'PAIRS','OLS',window=240,z_entry=2.0)
    x=m1(3); f=pair_frame(x,m1(3,'USDRUBF'));f['z']=[0.,2.1,2.2];f['beta']=[-2.,-2.,-2.];f['spread']=f.z
    monkeypatch.setattr('market_pattern_discovery.backtest.top5_v4.pairs.pair_features',lambda *a,**k:f)
    s,_=pair_signals(x,m1(3,'USDRUBF'),c); assert s.direction_cny.iloc[0]==-1 and s.direction_si.iloc[0]==-1
    assert np.isclose(s.w_cny.iloc[0],1/3)

def test_actual_next_open_r_target():
    x=m1(5); x.loc[1,['open','high','low','close']]=[10.01,10.02,10.00,10.01]
    s=sigrow(x,stop_ticks=9990,target_r=2.); l,k=simulate_explicit_orders(x,s,'CNYRUBF'); assert k.empty
    assert l.target_price.iloc[0]==10.05

def test_invalid_risk_is_explicit_skip():
    x=m1(4); s=sigrow(x,stop_ticks=10010,target_r=2.); l,k=simulate_explicit_orders(x,s,'CNYRUBF');assert l.empty and set(k.reason)=={'INVALID_NONPOSITIVE_RISK'}

def test_target_gap_is_conservative_not_open():
    x=m1(4); x.loc[2,['open','high','low','close']]=[10.05,10.06,10.04,10.05]
    s=sigrow(x,stop_ticks=9990,target_r=2.);l,_=simulate_explicit_orders(x,s,'CNYRUBF');g=l[l.friction=='GROSS'].iloc[0]
    assert g.exit_reason=='TARGET_GAP_CONSERVATIVE' and g.raw_exit_price==g.target_price

def test_stop_gap_uses_raw_open():
    x=m1(4);x.loc[2,['open','high','low','close']]=[9.98,10.,9.97,9.99]
    s=sigrow(x,stop_ticks=9990,target_r=2.);l,_=simulate_explicit_orders(x,s,'CNYRUBF');g=l[l.friction=='GROSS'].iloc[0]
    assert g.exit_reason=='STOP_GAP' and g.raw_exit_price==9.98

def test_stop_first_same_bar_tie():
    x=m1(4); x.loc[1,['open','high','low','close']]=[10.,10.03,9.99,10.]
    s=sigrow(x,stop_ticks=9990,target_r=2.);l,_=simulate_explicit_orders(x,s,'CNYRUBF');assert set(l.exit_reason)=={'STOP_FIRST_TIE'}

def test_friction_monotonic_and_one_trade_id():
    x=m1(4);s=sigrow(x,stop_ticks=9990,target_r=2.);l,_=simulate_explicit_orders(x,s,'CNYRUBF');assert l.trade_id.nunique()==1 and len(l)==3
    p=l.set_index('friction').pnl_bps;assert p.GROSS>=p.BASE>=p.STRESS

def test_semantic_duplicate_collapses_and_distinct_ambiguous_skips():
    x=m1(5); s=sigrow(x); dup=pd.concat([s,s],ignore_index=True); assert len(finalize_signal_ids(dup.drop(columns=['signal_id'])))==1
    a=s.iloc[0].to_dict();b=a.copy();b['stop_ticks']=9989;d=finalize_signal_ids(pd.DataFrame([a,b]).drop(columns=['signal_id']))
    l,k=simulate_explicit_orders(x,d,'CNYRUBF');assert l.empty and len(k)==2 and set(k.reason)=={'AMBIGUOUS_SIMULTANEOUS_SIGNAL'}

def test_metrics_requires_pnl_bps():
    with pytest.raises(ValueError,match='pnl_bps'):metrics(pd.DataFrame({'pnl':[1]}))

def test_profit_factor_edge_cases():
    assert _pf(np.array([0.,0.])) is None and math.isinf(_pf(np.array([1.,2.]))) and _pf(np.array([1.,-2.]))==.5

def test_realized_dd_orders_by_exit_then_trade_id():
    t=pd.to_datetime(['2026-01-05 10:02','2026-01-05 10:01','2026-01-05 10:02']).tz_localize(TZ)
    g=pd.DataFrame({'exit_time':t,'trade_id':['b','a','a'],'pnl_bps':[5.,-3.,-4.]}); assert realized_closed_trade_dd_bps(g)==7.

def test_pooled_ledger_is_union_not_average():
    z=pd.DataFrame({'instrument':['CNYRUBF','USDRUBF'],'x':[1,2]});p=pooled_single_leg_ledger(z);assert len(p)==2 and set(p.instrument)=={'POOLED'}

def metric_table_for_selection(reg, winners):
    rows=[]
    for c in reg:
        inst='CNYRUBF+USDRUBF' if c['family']=='PAIRS' else 'POOLED'
        for fr in ('BASE','STRESS'):
            win=c['candidate_id'] in winners
            rows.append({'candidate_id':c['candidate_id'],'family':c['family'],'submodel':c['submodel'],'instrument':inst,'friction':fr,'trades':25 if win else 0,'profit_factor':2. if win else None,'expectancy_bps':1. if win else None,'realized_closed_trade_dd_bps':3.,'sample_tier':'LOW'})
    return pd.DataFrame(rows)

def test_selection_status_zero_partial_complete():
    _,r,_=contract_registry(); s,status=select_primaries(r,metric_table_for_selection(r,set())); assert status=='NO_DEV_SURVIVOR' and s.empty
    first=[next(c for c in r if c['family']==f and c['selection_eligible']) for f in ('STRUCTURAL','ORB','TREND_PULLBACK','PAIRS','BOLLINGER_RSI')]
    s,status=select_primaries(r,metric_table_for_selection(r,{first[0]['candidate_id']})); assert status=='PARTIAL_DEV_SURVIVORS' and len(s)==1
    s,status=select_primaries(r,metric_table_for_selection(r,{x['candidate_id'] for x in first})); assert status=='DEV_SELECTION_COMPLETE' and len(s)==5

def test_validation_status_rules():
    b=lambda n,pf,e:{'trades':n,'profit_factor':pf,'expectancy_bps':e}
    assert validation_status(b(5,2,1),b(5,2,1),b(9,2,1),b(9,2,1))=='INSUFFICIENT'
    assert validation_status(b(10,2,1),b(10,2,1),b(20,1,1),b(20,2,1))=='REJECTED'
    assert validation_status(b(10,2,1),b(10,2,1),b(20,2,1),b(20,2,0))=='ROBUST'
    assert validation_status(b(10,2,-1),b(10,2,1),b(20,2,1),b(20,2,1))=='WEAK'

def test_semantic_hash_column_order_nan_inf_and_row_order():
    x=pd.DataFrame({'candidate_id':['a','b'],'signal_id':['x','y'],'trade_id':['1','2'],'friction':['BASE','BASE'],'v':[np.nan,np.inf]})
    y=x.iloc[::-1][list(reversed(x.columns))];assert semantic_ledger_hash(x)==semantic_ledger_hash(y)

def write_finam(path, rows):
    path.write_text(';'.join(fv4.SCHEMA)+'\n'+'\n'.join(';'.join(map(str,r)) for r in rows)+'\n')

def frow(tm,o='10.000',h='10.001',l='9.999',c='10.000',ticker='CNYRUBF',date=20260105):return [ticker,1,date,tm,o,h,l,c,1]

def test_bounded_loader_excludes_bar_closing_at_end(tmp_path):
    p=tmp_path/'x.csv';write_finam(p,[frow('100000'),frow('100100')]);r=load_finam_window_many([p],'CNYRUBF',pd.Timestamp('2026-01-05 10:00',tz=TZ),pd.Timestamp('2026-01-05 10:02',tz=TZ))
    assert list(r.frame.open_time.dt.minute)==[0]

def test_bounded_loader_does_not_parse_future_offtick_ohlcv(tmp_path):
    p=tmp_path/'x.csv';write_finam(p,[frow('100000'),frow('100200',c='10.0005')]);r=load_finam_window_many([p],'CNYRUBF',pd.Timestamp('2026-01-05 10:00',tz=TZ),pd.Timestamp('2026-01-05 10:02',tz=TZ));assert len(r.frame)==1

def test_bounded_loader_rejects_selected_offtick(tmp_path):
    p=tmp_path/'x.csv';write_finam(p,[frow('100000',c='10.0005')])
    with pytest.raises(IngestionError,match='off-tick'):load_finam_window_many([p],'CNYRUBF',pd.Timestamp('2026-01-05 10:00',tz=TZ),pd.Timestamp('2026-01-05 10:02',tz=TZ))

def test_bounded_loader_equivalent_and_conflicting_duplicates(tmp_path):
    p=tmp_path/'a.csv';q=tmp_path/'b.csv';write_finam(p,[frow('100000')]);write_finam(q,[frow('100000')]);r=load_finam_window_many([p,q],'CNYRUBF',pd.Timestamp('2026-01-05 10:00',tz=TZ),pd.Timestamp('2026-01-05 10:02',tz=TZ));assert len(r.frame)==1 and r.equivalent_duplicates==1
    write_finam(q,[frow('100000',c='10.001')])
    with pytest.raises(IngestionError,match='conflicting duplicate'):load_finam_window_many([p,q],'CNYRUBF',pd.Timestamp('2026-01-05 10:00',tz=TZ),pd.Timestamp('2026-01-05 10:02',tz=TZ))

def test_2025_path_is_locked_even_for_hash(tmp_path):
    p=tmp_path/'CNY_2025.csv';p.write_text('x')
    with pytest.raises(IngestionError,match='2025'):raw_file_hash_event(p)

def test_access_ledger_protected_interval_uses_close_time():
    events=[{'event':'OHLCV_MATERIALIZE','timestamp_min':'2026-02-28T23:58:00+03:00','timestamp_max':'2026-02-28T23:59:00+03:00','close_time_max':'2026-03-01T00:00:00+03:00'}]
    with pytest.raises(AssertionError):assert_no_ohlcv_materialized(events,DEV_END,VALIDATION_END)

def test_direct_import_all_modules():
    import market_pattern_discovery.backtest.top5_v4.common
    import market_pattern_discovery.backtest.top5_v4.market
    import market_pattern_discovery.backtest.top5_v4.registry
    import market_pattern_discovery.backtest.top5_v4.structural
    import market_pattern_discovery.backtest.top5_v4.families
    import market_pattern_discovery.backtest.top5_v4.pairs
    import market_pattern_discovery.backtest.top5_v4.execution
    import market_pattern_discovery.backtest.top5_v4.metrics
    import market_pattern_discovery.backtest.top5_v4.freeze
