from __future__ import annotations
from decimal import Decimal
from typing import Any
import numpy as np
import pandas as pd
from .common import TZ,TICKS,_half_up_int,price_to_ticks
from .market import indicators
from .structural import _signal,finalize_signal_ids

def _exact_opening_range(day,date,length):
    start=pd.Timestamp(date).tz_localize(TZ)+pd.Timedelta(hours=10);expected=pd.date_range(start,periods=length,freq="min");keyed=day.set_index("open_time",drop=False)
    if not all(ts in keyed.index for ts in expected):return None
    out=keyed.loc[expected];return out if len(out)==length else None

def orb_signals(m1,instrument,candidate):
    p=candidate["parameters"];length=int(p["length"]);target=float(p["target_r"]);sub=candidate["submodel"];stop_mode=p.get("stop_mode")
    if sub=="DIRECT" and stop_mode not in {"STOP_OPPOSITE_OR","STOP_MIDPOINT"}:raise ValueError("DIRECT requires valid stop_mode")
    if sub!="DIRECT" and stop_mode is not None:raise ValueError("stop_mode is DIRECT-only")
    tick=TICKS[instrument];rows=[]
    for date,day in m1.groupby("trading_date",sort=False):
        opening=_exact_opening_range(day,date,length)
        if opening is None:continue
        orh=max(price_to_ticks(v,tick) for v in opening.high);orl=min(price_to_ticks(v,tick) for v in opening.low);later=day[day.open_time>=opening.close_time.iloc[-1]].reset_index(drop=True);bp=None;bd=0
        for pos,b in later.iterrows():
            c=price_to_ticks(b.close,tick)
            if c>=orh+1:bp,bd=pos,1;break
            if c<=orl-1:bp,bd=pos,-1;break
        if bp is None:continue
        b0=later.iloc[bp]
        if sub=="DIRECT":
            stop=(orl if bd==1 else orh) if stop_mode=="STOP_OPPOSITE_OR" else _half_up_int((Decimal(orh)+Decimal(orl))/Decimal(2));rows.append(_signal(candidate["candidate_id"],"ORB","DIRECT",instrument,b0.close_time,date,bd,stop,target,or_high_ticks=orh,or_low_ticks=orl,or_length=length,stop_mode=stop_mode));continue
        exc_lo=price_to_ticks(b0.low,tick);exc_hi=price_to_ticks(b0.high,tick)
        for age,(_,b) in enumerate(later.iloc[bp+1:].iterrows(),start=1):
            if age>5:break
            lo=price_to_ticks(b.low,tick);hi=price_to_ticks(b.high,tick);c=price_to_ticks(b.close,tick);exc_lo=min(exc_lo,lo);exc_hi=max(exc_hi,hi)
            if sub=="BREAKOUT_RETEST":
                hit=(lo<=orh+1 and c>orh) if bd==1 else (hi>=orl-1 and c<orl)
                if hit:
                    stop=lo-1 if bd==1 else hi+1;rows.append(_signal(candidate["candidate_id"],"ORB",sub,instrument,b.close_time,date,bd,stop,target,or_high_ticks=orh,or_low_ticks=orl,or_length=length,breakout_age_valid_bars=age));break
            else:
                inside=orl<c<orh
                if inside:
                    d=-bd;stop=exc_lo-1 if d==1 else exc_hi+1;rows.append(_signal(candidate["candidate_id"],"ORB","FAILED_BREAKOUT_DIAGNOSTIC",instrument,b.close_time,date,d,stop,target,or_high_ticks=orh,or_low_ticks=orl,or_length=length,breakout_age_valid_bars=age,failed_excursion_low_ticks=exc_lo,failed_excursion_high_ticks=exc_hi));break
    return finalize_signal_ids(pd.DataFrame(rows))

def _trend_regime(x,i):
    if i<3 or not np.isfinite(x.ema_slow.iloc[i]) or not np.isfinite(x.ema_slow.iloc[i-3]):return 0
    if x.ema20.iloc[i]>x.ema_slow.iloc[i] and x.ema_slow.iloc[i]>x.ema_slow.iloc[i-3]:return 1
    if x.ema20.iloc[i]<x.ema_slow.iloc[i] and x.ema_slow.iloc[i]<x.ema_slow.iloc[i-3]:return -1
    return 0

def trend_signals(m5,instrument,candidate):
    slow=int(candidate["parameters"]["slow_ema"]);target=float(candidate["parameters"]["target_r"]);x=indicators(m5,slow=slow);tick=TICKS[instrument];lo_t=np.array([price_to_ticks(v,tick) for v in x.low]);hi_t=np.array([price_to_ticks(v,tick) for v in x.high]);rows=[]
    for date,idx in x.groupby("trading_date",sort=False).indices.items():
        idx=list(idx);pull=None;blocked={1:False,-1:False};just={1:False,-1:False}
        for pos,i in enumerate(idx):
            regime=_trend_regime(x,i)
            for d in (1,-1):
                if blocked[d] and ((d==1 and regime==1 and x.low.iloc[i]>x.ema20.iloc[i]) or (d==-1 and regime==-1 and x.high.iloc[i]<x.ema20.iloc[i])):blocked[d]=False;just[d]=True
            if pull is not None:
                bars=pos-pull["start_pos"]+1;pull["lo"]=min(pull["lo"],lo_t[i]);pull["hi"]=max(pull["hi"],hi_t[i]);invalid=(pull["d"]==1 and x.close.iloc[i]<x.ema_slow.iloc[i]) or (pull["d"]==-1 and x.close.iloc[i]>x.ema_slow.iloc[i])
                if invalid or bars>6:blocked[pull["d"]]=True;pull=None;continue
                resume=regime==pull["d"] and ((pull["d"]==1 and x.close.iloc[i]>x.ema20.iloc[i] and x.close.iloc[i]>x.close.iloc[i-1]) or (pull["d"]==-1 and x.close.iloc[i]<x.ema20.iloc[i] and x.close.iloc[i]<x.close.iloc[i-1]))
                if resume:
                    d=pull["d"];stop=pull["lo"]-1 if d==1 else pull["hi"]+1;rows.append(_signal(candidate["candidate_id"],"TREND_PULLBACK",f"EMA20_{slow}",instrument,x.close_time.iloc[i],date,d,stop,target,pullback_start=x.close_time.iloc[pull["start_i"]],pullback_bars=bars,ema20=float(x.ema20.iloc[i]),ema_slow=float(x.ema_slow.iloc[i])));pull=None;continue
            if pull is None and regime:
                if just[regime]:just[regime]=False;continue
                if blocked[regime]:continue
                touch=(regime==1 and x.low.iloc[i]<=x.ema20.iloc[i] and x.close.iloc[i]>=x.ema_slow.iloc[i]) or (regime==-1 and x.high.iloc[i]>=x.ema20.iloc[i] and x.close.iloc[i]<=x.ema_slow.iloc[i])
                if touch:pull={"d":regime,"start_pos":pos,"start_i":i,"lo":lo_t[i],"hi":hi_t[i]}
            for d in (1,-1):
                if d!=regime and just[d]:just[d]=False
    return finalize_signal_ids(pd.DataFrame(rows))

def mean_reversion_signals(m5,instrument,candidate):
    p=candidate["parameters"];k=float(p["k"]);lower=float(p["rsi_lower"]);upper=float(p["rsi_upper"]);max_bars=int(p["reentry_max_bars"]);exit_mode=p["exit_mode"];x=indicators(m5,bb_k=k);tick=TICKS[instrument];lo_t=np.array([price_to_ticks(v,tick) for v in x.low]);hi_t=np.array([price_to_ticks(v,tick) for v in x.high]);rows=[];pending=None;blocked=None;prior_date=None
    for i,b in x.iterrows():
        if prior_date is not None and b.trading_date!=prior_date:pending=None;blocked=None
        prior_date=b.trading_date
        if not np.isfinite(b.bb_lower) or not np.isfinite(b.bb_upper):continue
        inside=b.bb_lower<=b.close<=b.bb_upper
        if blocked is not None:
            if inside:blocked=None;continue
            continue
        if pending is not None:
            age=i-pending["i"];pending["lo"]=min(pending["lo"],lo_t[i]);pending["hi"]=max(pending["hi"],hi_t[i]);reentered=b.close>b.bb_lower if pending["d"]==1 else b.close<b.bb_upper
            if 1<=age<=max_bars and reentered:
                d=pending["d"];stop=pending["lo"]-1 if d==1 else pending["hi"]+1;target_r,target_ticks=(2.0,None) if exit_mode=="REENTRY_2R" else (None,price_to_ticks(b.bb_mid,tick)) if exit_mode=="REENTRY_FIXED_MID" else (_ for _ in ()).throw(ValueError("unknown Bollinger exit mode"));rows.append(_signal(candidate["candidate_id"],"BOLLINGER_RSI",exit_mode,instrument,b.close_time,b.trading_date,d,stop,target_r,target_ticks,extreme_time=x.close_time.iloc[pending["i"]],reentry_time=b.close_time,bb_k=k,rsi_thresholds=[lower,upper],reentry_max_bars=max_bars,frozen_mid_ticks=target_ticks));pending=None;continue
            if age>=max_bars:blocked=pending["d"];pending=None;continue
        if pending is None and np.isfinite(b.rsi):
            if b.close<b.bb_lower and b.rsi<=lower:pending={"i":i,"d":1,"lo":lo_t[i],"hi":hi_t[i]}
            elif b.close>b.bb_upper and b.rsi>=upper:pending={"i":i,"d":-1,"lo":lo_t[i],"hi":hi_t[i]}
    return finalize_signal_ids(pd.DataFrame(rows))
