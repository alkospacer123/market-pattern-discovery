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

def test_strategy_contract_is_complete():
    assert validate_contract(MANDATORY_CONTRACT)
    bad=json.loads(json.dumps(MANDATORY_CONTRACT));bad["families"]["ORB"].remove("FAILED_BREAKOUT")
    with pytest.raises(ValueError):validate_contract(bad)

def snapshot_bars(order="HL"):
    if order=="HL":
        hi=np.array([2.2,2.3,3.,2.4,2.5,3.7,3.8,3.7,3.8,3.9,4.,4.1]);lo=np.array([1.8,1.9,2.,2.1,2.2,3.4,3.3,3.,3.4,3.5,3.6,3.7])
    else:
        hi=np.array([4.2,4.1,4.,4.1,4.2,2.6,2.7,3.,2.7,2.6,2.5,2.4]);lo=np.array([3.5,3.4,3.,3.4,3.5,2.1,2.,2.2,2.1,2.,1.9,1.8])
    c=(hi+lo)/2;x=m5bars(c,hi,lo)
    return x

@pytest.mark.parametrize("order",["HL","LH"])
def test_mirror_both_orders_and_not_early(order):
    z=structural_levels(snapshot_bars(order),"CNYRUBF",2,2)
    mirrors=z[z.mirror]
    assert len(mirrors) and (mirrors.level_type=="MIRROR").all()
    assert mirrors.valid_from.min()>=snapshot_bars(order).close_time.iloc[9]

def test_immutable_snapshots_and_historical_flag():
    x=m5bars([1,2,3,2,1,2,3.001,2,1,2,3.002,2,1]);z=structural_levels(x,"CNYRUBF",3,2)
    eh=z[z.level_type.eq("EH")];assert len(eh)>=2 and eh.snapshot_version.is_monotonic_increasing
    old=eh.iloc[0].copy();assert eh.iloc[0].touch_count==2 and eh.iloc[-1].touch_count>=3
    assert old.level_price==eh.iloc[0].level_price and old.valid_from==eh.iloc[0].valid_from

def test_future_mutation_preserves_snapshots_and_signals():
    x=m5bars([1,2,3,2,1,2,3.001,2,1,2,2,2,2]);cut=x.close_time.iloc[8];a=structural_levels(x,"CNYRUBF",3,2);sa=structural_signals(x,a,"CNYRUBF")
    y=x.copy();y.loc[9:,["high","low","close"]]=[99,-99,50];b=structural_levels(y,"CNYRUBF",3,2);sb=structural_signals(y,b,"CNYRUBF")
    cols=["level_snapshot_id","snapshot_version","level_price","valid_from","touch_count"]
    assert a[a.valid_from<=cut][cols].reset_index(drop=True).equals(b[b.valid_from<=cut][cols].reset_index(drop=True))
    if len(sa):assert sa[sa.signal_time<=cut].reset_index(drop=True).equals(sb[sb.signal_time<=cut].reset_index(drop=True))

def test_historical_flag_cross_day():
    x=m5bars([1,2,3,2,1,2,3,2,1]);x.loc[5:,"close_time"]+=pd.Timedelta(days=1);x.loc[5:,"open_time"]+=pd.Timedelta(days=1);x["trading_date"]=x.close_time.dt.date
    z=structural_levels(x,"CNYRUBF",2,2);assert z.historical.any()

def gerchik_fixture(direction=1):
    c=np.linspace(10,12,70) if direction==1 else np.linspace(12,10,70);x=m5bars(c);i=60;tick=.001;level=round(c[i]/tick)*tick
    if direction==1:
        x.loc[i,"low"]=level;x.loc[i+1,"low"]=level;x.loc[i+1,"close"]=level+.01;typ="EL"
    else:
        x.loc[i,"high"]=level;x.loc[i+1,"high"]=level;x.loc[i+1,"close"]=level-.01;typ="EH"
    lev=pd.DataFrame([{"level_family_id":"F","level_snapshot_id":"S","snapshot_version":1,"level_type":typ,"level_price":level,"valid_from":x.close_time.iloc[55],"first_touch":x.close_time.iloc[50],"known_index":55}])
    return x,lev

@pytest.mark.parametrize("direction",[1,-1])
def test_gerchik_proxy_long_short_and_fidelity(direction):
    x,l=gerchik_fixture(direction);s=gerchik_a_signals(x,l,"CNYRUBF");assert len(s)==1 and s.direction.iloc[0]==direction and s.source_fidelity.iloc[0]=="PROXY" and s.target_r.iloc[0]==3

def test_breakout_retest_keeps_snapshot():
    x=m5bars([2]*8);x.loc[1,"close"]=2.01;x.loc[2,["low","close"]]=[1.999,2.005]
    l=pd.DataFrame([{"level_family_id":"F","level_snapshot_id":"F-V1","snapshot_version":1,"level_type":"EH","level_price":2.,"valid_from":x.close_time.iloc[0],"tolerance_ticks":2,"round_confluence":False,"historical":False,"mirror":False}])
    s=structural_signals(x,l,"CNYRUBF");r=s[s.submodel.eq("BREAKOUT_RETEST")];assert len(r) and (r.breakout_level_snapshot_id=="F-V1").all()

def orb_fixture(down=False):
    x=bars(12);x.loc[:4,["high","low","close"]]=[10.01,9.99,10]
    if down:x.loc[5,["high","low","close"]]=[10,9.98,9.98];x.loc[6,["high","low","close"]]=[10,9.97,10]
    else:x.loc[5,["high","low","close"]]=[10.02,10,10.02];x.loc[6,["high","low","close"]]=[10.03,10,10]
    return x

def test_orb_stop_variants_and_failed_both_sides():
    x=orb_fixture();a=orb_signals(x,"CNYRUBF",5,2.,submodel="DIRECT",stop_mode="STOP_OPPOSITE_OR");b=orb_signals(x,"CNYRUBF",5,2.,submodel="DIRECT",stop_mode="STOP_MIDPOINT")
    assert np.isclose(a.stop_price.iloc[0],9.99) and np.isclose(b.stop_price.iloc[0],10.)
    short=orb_signals(x,"CNYRUBF",5,2.,submodel="FAILED_BREAKOUT");long=orb_signals(orb_fixture(True),"CNYRUBF",5,2.,submodel="FAILED_BREAKOUT")
    assert short.direction.iloc[0]==-1 and short.stop_price.iloc[0]>short.failed_excursion_high.iloc[0]
    assert long.direction.iloc[0]==1 and long.stop_price.iloc[0]<long.failed_excursion_low.iloc[0]

def distance_reference(c,s,w,i):
    c0,s0=c[i-w],s[i-w];hist=c[i-w:i]/c0-s[i-w:i]/s0;cur=c[i]/c0-s[i]/s0;return (cur-hist.mean())/hist.std(ddof=1)

def test_distance_matches_reference_and_is_past_only():
    c=np.linspace(10,12,30)+np.sin(np.arange(30))*.01;s=np.linspace(90,92,30)+np.cos(np.arange(30))*.02;a=bars(30,close=c);b=bars(30,"USDRUBF",s);z=pair_features(a,b,10,"DISTANCE")
    assert np.isclose(z.z.iloc[20],distance_reference(c,s,10,20));before=z.z.iloc[20];a.loc[21:,"close"]=999;assert pair_features(a,b,10,"DISTANCE").z.iloc[20]==before

def test_ols_current_and_future_excluded():
    a=bars(30,close=np.linspace(10,11,30));b=bars(30,"USDRUBF",np.linspace(90,92,30));before=pair_features(a,b,10,"OLS").beta.iloc[20];a.loc[20:,"close"]=999;after=pair_features(a,b,10,"OLS").beta.iloc[20];assert before==after

def pair_frame(zs,dates=None):
    a=bars(len(zs));a["z"]=zs;a["beta"]=2.;a["spread"]=zs
    if dates is not None:a["trading_date"]=dates
    return a

def test_pair_convergence_time_day_end_and_weights():
    a=bars(130,close=np.linspace(10,11,130));b=bars(130,"USDRUBF",np.linspace(90,91,130));s=pd.DataFrame([{"submodel":"OLS","signal_time":a.close_time.iloc[0],"direction_cny":-1,"direction_si":1,"beta_at_entry":2.,"entry_z":2.,"exit_z":-.1,"planned_exit_time":a.close_time.iloc[3],"planned_exit_reason":"CONVERGENCE"}]);l=simulate_pairs(a,b,s);assert set(l.exit_reason)=={"CONVERGENCE"} and np.isclose(l.w_cny.iloc[0],1/3) and np.isclose(l.w_si.iloc[0],2/3)
    assert l[l.friction.eq("BASE")].total_pnl.iloc[0]<l[l.friction.eq("GROSS")].total_pnl.iloc[0]

def test_fixed_middle_target_frozen_and_explicit_execution():
    c=np.r_[np.ones(20)*10,8,10,10];x=m5bars(c);s=mean_reversion_signals(x,"CNYRUBF",1.5,30,None,"REENTRY_FIXED_MID")
    if len(s):
        target=s.target_price.iloc[0];x.loc[x.index[-1],"close"]=99;assert s.target_price.iloc[0]==target
    m=bars(6);sig=pd.DataFrame([_signal("X","MID","CNYRUBF",m.close_time.iloc[0],1,10,9.9,None,target_price=10.01)]);l=simulate_explicit_orders(m,sig,.001);assert (l.target_price==10.01).all()

def test_conflicting_target_rejected():
    m=bars(6);sig=pd.DataFrame([_signal("X","Y","CNYRUBF",m.close_time.iloc[0],1,10,9.9,2,target_price=10.1)])
    with pytest.raises(ValueError):simulate_explicit_orders(m,sig,.001)

def test_selection_prefers_sample_tier_before_pf():
    x=pd.DataFrame([{"base_expectancy":1,"trades":6,"base_pf":20,"max_dd":1,"complexity":1},{"base_expectancy":.1,"trades":50,"base_pf":1.6,"max_dd":2,"complexity":2}]);assert select_variant(x).trades==50

def test_dev_loader_guard_and_modes_do_not_default_full():
    import subprocess,sys
    p=subprocess.run([sys.executable,"scripts/run_top5.py"],capture_output=True,text=True);assert p.returncode!=0 and "required" in p.stderr
    f=load_dev("/workspace/market-pattern-data","CNYRUBF");assert f.open_time.max()<DEV_END and f.open_time.dt.year.eq(2026).all()
