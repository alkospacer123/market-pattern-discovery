from __future__ import annotations
from decimal import Decimal
from typing import Any
import numpy as np
import pandas as pd
from .common import TICKS,FRICTION_TICKS,_decimal,_half_up_int,price_to_ticks,ticks_to_price,stable_id
from .pairs import pair_frame

def _ambiguous_signal_ids(signals):
    bad=set()
    if signals.empty:return bad
    for _,g in signals.groupby(["candidate_id","instrument","signal_time"],sort=False):
        if len(g)>1:bad.update(g.signal_id.astype(str))
    return bad

def _trade_id(signal_id,entry_time,exit_time,reason):return stable_id("TRADE",{"signal_id":signal_id,"entry_time":str(entry_time),"exit_time":str(exit_time),"reason":reason},24)

def simulate_explicit_orders(m1,signals,instrument,max_hold=120):
    rows=[];skips=[]
    if signals.empty:return pd.DataFrame(),pd.DataFrame()
    tick=TICKS[instrument];x=m1.sort_values("open_time",kind="mergesort").reset_index(drop=True);open_lookup={pd.Timestamp(t):i for i,t in enumerate(x.open_time)};day_end={}
    for _,idx in x.groupby("trading_date",sort=False).indices.items():
        idx=list(idx)
        for i in idx:day_end[i]=idx[-1]
    ambiguous=_ambiguous_signal_ids(signals);busy={}
    for s in signals.sort_values(["signal_time","candidate_id","signal_id"],kind="mergesort").itertuples(index=False):
        base={"signal_id":s.signal_id,"candidate_id":s.candidate_id,"instrument":instrument,"signal_time":s.signal_time}
        if s.signal_id in ambiguous:skips.append(base|{"reason":"AMBIGUOUS_SIMULTANEOUS_SIGNAL"});continue
        key=(s.candidate_id,instrument)
        if key in busy and pd.Timestamp(s.signal_time)<busy[key]:skips.append(base|{"reason":"OPEN_POSITION"});continue
        entry_i=open_lookup.get(pd.Timestamp(s.signal_time))
        if entry_i is None:skips.append(base|{"reason":"DATA_GAP_NO_NEXT_OPEN"});continue
        if x.trading_date.iloc[entry_i]!=s.signal_trading_date:skips.append(base|{"reason":"TRADING_DATE_MISMATCH"});continue
        direction=int(s.direction);entry_ticks=price_to_ticks(x.open.iloc[entry_i],tick)
        if s.stop_ticks is None or pd.isna(s.stop_ticks):skips.append(base|{"reason":"INVALID_MISSING_STOP"});continue
        stop=int(s.stop_ticks);risk=direction*(entry_ticks-stop)
        if risk<=0:skips.append(base|{"reason":"INVALID_NONPOSITIVE_RISK"});continue
        tr=None if s.target_r is None or pd.isna(s.target_r) else float(s.target_r);tt=None if s.target_ticks is None or pd.isna(s.target_ticks) else int(s.target_ticks)
        if (tr is None)==(tt is None):skips.append(base|{"reason":"INVALID_TARGET_DEFINITION"});continue
        target=entry_ticks+direction*_half_up_int(Decimal(risk)*_decimal(tr)) if tr is not None else tt
        if direction*(target-entry_ticks)<=0:skips.append(base|{"reason":"INVALID_TARGET_SIDE"});continue
        last_i=min(entry_i+int(max_hold)-1,day_end[entry_i]);exit_i=last_i;exit_ticks=price_to_ticks(x.close.iloc[last_i],tick);reason="TIME" if last_i==entry_i+int(max_hold)-1 else "DAY_END"
        for i in range(entry_i,last_i+1):
            op=price_to_ticks(x.open.iloc[i],tick);hi=price_to_ticks(x.high.iloc[i],tick);lo=price_to_ticks(x.low.iloc[i],tick);stop_gap=op<=stop if direction==1 else op>=stop;target_gap=op>=target if direction==1 else op<=target;stop_hit=lo<=stop if direction==1 else hi>=stop;target_hit=hi>=target if direction==1 else lo<=target
            if stop_gap:exit_i,exit_ticks,reason=i,op,"STOP_GAP";break
            if target_gap:exit_i,exit_ticks,reason=i,target,"TARGET_GAP_CONSERVATIVE";break
            if stop_hit:exit_i,exit_ticks=i,stop;reason="STOP_FIRST_TIE" if target_hit else "STOP";break
            if target_hit:exit_i,exit_ticks,reason=i,target,"TARGET";break
        raw_entry=ticks_to_price(entry_ticks,tick);raw_exit=ticks_to_price(exit_ticks,tick);trade_id=_trade_id(s.signal_id,x.open_time.iloc[entry_i],x.close_time.iloc[exit_i],reason)
        for scenario,fr in FRICTION_TICKS.items():
            en=entry_ticks+direction*fr;ex=exit_ticks-direction*fr;pnl_ticks=direction*(ex-en);pnl_native=ticks_to_price(pnl_ticks,tick);pnl_bps=pnl_native/raw_entry*10000
            rows.append({"trade_id":trade_id,"signal_id":s.signal_id,"candidate_id":s.candidate_id,"family":s.family,"submodel":s.submodel,"instrument":instrument,"signal_time":s.signal_time,"entry_time":x.open_time.iloc[entry_i],"exit_time":x.close_time.iloc[exit_i],"signal_trading_date":s.signal_trading_date,"side":s.side,"friction":scenario,"friction_ticks_per_side":fr,"raw_entry_price":raw_entry,"raw_exit_price":raw_exit,"entry_price":ticks_to_price(en,tick),"exit_price":ticks_to_price(ex,tick),"stop_price":ticks_to_price(stop,tick),"target_price":ticks_to_price(target,tick),"exit_reason":reason,"bars_held":exit_i-entry_i+1,"pnl_native":pnl_native,"pnl_bps":pnl_bps,"pnl_R":pnl_ticks/risk})
        busy[key]=pd.Timestamp(x.close_time.iloc[exit_i])
    ledger=pd.DataFrame(rows);skips_df=pd.DataFrame(skips)
    if not ledger.empty:
        piv=ledger.pivot(index="trade_id",columns="friction",values="pnl_bps")
        if not ((piv.GROSS>=piv.BASE)&(piv.BASE>=piv.STRESS)).all():raise AssertionError("friction monotonicity violation")
    _assert_conservation(signals,ledger,skips_df);return ledger,skips_df

def _next_pair_convergence(features):
    """Nearest strictly-future finite z crossing for each row, constrained to trading_date."""
    n=len(features);nonpos=np.full(n,-1,dtype=np.int64);nonneg=np.full(n,-1,dtype=np.int64)
    if n==0:return nonpos,nonneg
    dates=features.trading_date.to_numpy();z=features.z.to_numpy(float);start=0
    while start<n:
        end=start+1
        while end<n and dates[end]==dates[start]:end+=1
        last_nonpos=-1;last_nonneg=-1
        for i in range(end-1,start-1,-1):
            nonpos[i]=last_nonpos;nonneg[i]=last_nonneg;zi=z[i]
            if np.isfinite(zi):
                if zi<=0:last_nonpos=i
                if zi>=0:last_nonneg=i
        start=end
    return nonpos,nonneg

def simulate_pairs(cny,si,signals,features_by_candidate,max_hold=120):
    rows=[];skips=[]
    if signals.empty:return pd.DataFrame(),pd.DataFrame()
    common=pair_frame(cny,si);open_lookup={pd.Timestamp(t):i for i,t in enumerate(common.open_time)};busy={};amb=_ambiguous_signal_ids(signals);day_end=np.empty(len(common),dtype=np.int64)
    for _,idx in common.groupby("trading_date",sort=False).indices.items():
        idx=np.asarray(idx,dtype=np.int64);day_end[idx]=idx[-1]
    convergence_cache={cid:_next_pair_convergence(features) for cid,features in features_by_candidate.items()}
    for s in signals.sort_values(["signal_time","candidate_id","signal_id"],kind="mergesort").itertuples(index=False):
        base={"signal_id":s.signal_id,"candidate_id":s.candidate_id,"instrument":s.instrument,"signal_time":s.signal_time}
        if s.signal_id in amb:skips.append(base|{"reason":"AMBIGUOUS_SIMULTANEOUS_SIGNAL"});continue
        if s.candidate_id in busy and pd.Timestamp(s.signal_time)<busy[s.candidate_id]:skips.append(base|{"reason":"OPEN_POSITION"});continue
        entry_i=open_lookup.get(pd.Timestamp(s.signal_time))
        if entry_i is None:skips.append(base|{"reason":"DATA_GAP_NO_COMMON_OPEN"});continue
        day=common.trading_date.iloc[entry_i]
        if day!=s.signal_trading_date:skips.append(base|{"reason":"TRADING_DATE_MISMATCH"});continue
        day_end_i=int(day_end[entry_i]);time_i=entry_i+max_hold-1 if entry_i+max_hold-1<=day_end_i else None;features=features_by_candidate[s.candidate_id];fi=int(s.feature_index);conv=None;conv_z=np.nan
        nonpos,nonneg=convergence_cache[s.candidate_id];fj=int(nonpos[fi] if float(s.entry_z)>0 else nonneg[fi])
        if fj>=0:
            q=features.iloc[fj];close_stamp=pd.Timestamp(q.close_time);noi=open_lookup.get(close_stamp);conv="NO_NEXT_OPEN" if noi is None or common.trading_date.iloc[noi]!=day else int(noi);conv_z=float(q.z)
        if time_i is not None:
            if isinstance(conv,int) and conv<=time_i:exit_i,mode,at_open=conv,"CONVERGENCE",True
            else:exit_i,mode,at_open=time_i,"TIME",False
        else:
            if isinstance(conv,int) and conv<=day_end_i:exit_i,mode,at_open=conv,"CONVERGENCE",True
            else:
                exit_i,mode,at_open=day_end_i,"DAY_END",False
                if conv=="NO_NEXT_OPEN":skips.append(base|{"reason":"CONVERGENCE_NO_NEXT_COMMON_OPEN_DAY_END_DIAGNOSTIC"})
        oc=float(common.open_cny.iloc[entry_i]);os=float(common.open_si.iloc[entry_i])
        if at_open:ec=float(common.open_cny.iloc[exit_i]);es=float(common.open_si.iloc[exit_i]);exit_time=common.open_time.iloc[exit_i];bars=exit_i-entry_i
        else:ec=float(common.close_cny.iloc[exit_i]);es=float(common.close_si.iloc[exit_i]);exit_time=common.close_time.iloc[exit_i];bars=exit_i-entry_i+1
        tid=_trade_id(s.signal_id,common.open_time.iloc[entry_i],exit_time,mode)
        for scenario,fr in FRICTION_TICKS.items():
            pc=float(s.w_cny)*(int(s.direction_cny)*(ec-oc)/oc-2*fr*TICKS["CNYRUBF"]/oc);ps=float(s.w_si)*(int(s.direction_si)*(es-os)/os-2*fr*TICKS["USDRUBF"]/os);pnl=(pc+ps)*10000
            rows.append({"trade_id":tid,"signal_id":s.signal_id,"candidate_id":s.candidate_id,"family":"PAIRS","submodel":s.submodel,"instrument":"CNYRUBF+USDRUBF","signal_time":s.signal_time,"entry_time":common.open_time.iloc[entry_i],"exit_time":exit_time,"signal_trading_date":s.signal_trading_date,"side":"SPREAD","friction":scenario,"friction_ticks_per_side":fr,"exit_reason":mode,"bars_held":bars,"entry_z":float(s.entry_z),"exit_z":conv_z,"beta_at_entry":float(s.beta_at_entry),"w_cny":float(s.w_cny),"w_si":float(s.w_si),"entry_price_cny":oc,"entry_price_si":os,"exit_price_cny":ec,"exit_price_si":es,"pnl_cny":pc,"pnl_si":ps,"pnl_native":pc+ps,"pnl_bps":pnl})
        busy[s.candidate_id]=pd.Timestamp(exit_time)
    ledger=pd.DataFrame(rows);skips_df=pd.DataFrame(skips)
    if not ledger.empty:
        piv=ledger.pivot(index="trade_id",columns="friction",values="pnl_bps")
        if not ((piv.GROSS>=piv.BASE)&(piv.BASE>=piv.STRESS)).all():raise AssertionError("pair friction monotonicity violation")
    conservation=skips_df[~skips_df.reason.eq("CONVERGENCE_NO_NEXT_COMMON_OPEN_DAY_END_DIAGNOSTIC")] if not skips_df.empty else skips_df;_assert_conservation(signals,ledger,conservation);return ledger,skips_df

def _assert_conservation(signals,ledger,skips):
    generated=int(signals.signal_id.nunique()) if not signals.empty else 0;executed=int(ledger.signal_id.nunique()) if not ledger.empty else 0;skipped=int(skips.signal_id.nunique()) if not skips.empty else 0;overlap=set(ledger.signal_id.astype(str))&set(skips.signal_id.astype(str)) if not ledger.empty and not skips.empty else set()
    if overlap:raise AssertionError("signal accounted as both executed and skipped")
    if generated!=executed+skipped:raise AssertionError(f"signal conservation failed: generated={generated} executed={executed} skipped={skipped}")
