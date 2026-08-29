from __future__ import annotations
from decimal import Decimal
from typing import Any
import numpy as np
import pandas as pd
from .common import TICKS,ROUND_STEPS,_half_up_int,price_to_ticks,ticks_to_price,stable_id
from .market import confirmed_pivots,indicators,_activation_index,_market_dates

def structural_levels(m5,instrument,tolerance_ticks=2,min_touches=2):
    piv=confirmed_pivots(m5,instrument)
    if piv.empty:return pd.DataFrame()
    _,rank=_market_dates(m5);families=[];rows=[];round_grid_ticks=price_to_ticks(ROUND_STEPS[instrument],TICKS[instrument]);grid_tag=f"tol={int(tolerance_ticks)}|touches={int(min_touches)}"
    for pivot_id,p in piv.sort_values(["known_time","side","pivot_index"],kind="mergesort").reset_index(drop=True).iterrows():
        activation_ix=_activation_index(m5,pd.Timestamp(p.known_time))
        if activation_ix is None:continue
        activation_date=m5.trading_date.iloc[activation_ix];ar=rank[activation_date]
        compatible=[f for f in families if ar-f["birth_rank"]<5 and abs(int(p.price_ticks)-f["anchor_ticks"])<=int(tolerance_ticks)]
        if compatible:
            f=min(compatible,key=lambda z:(abs(int(p.price_ticks)-z["anchor_ticks"]),z["family_seq"]))
            if int(p.pivot_index)-f["last_pivot_index"]<2:continue
        else:
            f={"family_seq":len(families),"anchor_ticks":int(p.price_ticks),"birth_rank":ar,"birth_date":activation_date,"last_pivot_index":-10,"touches":[],"snapshot_version":0};f["family_id"]=f"{instrument}|STRUCT|{grid_tag}|F{f['family_seq']:06d}";families.append(f)
        f["touches"].append({"pivot_id":int(pivot_id),"side":p.side,"price_ticks":int(p.price_ticks),"pivot_index":int(p.pivot_index),"pivot_time":pd.Timestamp(p.pivot_time),"known_time":pd.Timestamp(p.known_time),"activation_index":activation_ix,"activation_date":activation_date});f["last_pivot_index"]=int(p.pivot_index)
        highs=[q for q in f["touches"] if q["side"]=="HIGH"];lows=[q for q in f["touches"] if q["side"]=="LOW"];mirror=bool(highs and lows and len(f["touches"])>=min_touches)
        typ="MIRROR" if mirror else "EH" if len(highs)>=min_touches else "EL" if len(lows)>=min_touches else None
        if typ is None:continue
        f["snapshot_version"]+=1;ticks_sorted=sorted(q["price_ticks"] for q in f["touches"]);n=len(ticks_sorted);level_ticks=int(ticks_sorted[n//2]) if n%2 else _half_up_int((Decimal(ticks_sorted[n//2-1])+Decimal(ticks_sorted[n//2]))/Decimal(2));nearest=_half_up_int(Decimal(level_ticks)/Decimal(round_grid_ticks))*round_grid_ticks
        rows.append({"level_family_id":f["family_id"],"level_snapshot_id":f"{f['family_id']}|V{f['snapshot_version']:03d}","snapshot_version":f["snapshot_version"],"instrument":instrument,"level_type":typ,"anchor_ticks":f["anchor_ticks"],"level_ticks":level_ticks,"level_price":ticks_to_price(level_ticks,TICKS[instrument]),"valid_from":pd.Timestamp(p.known_time),"activation_index":activation_ix,"activation_trading_date":activation_date,"family_birth_trading_date":f["birth_date"],"family_birth_rank":f["birth_rank"],"family_expiry_rank_exclusive":f["birth_rank"]+5,"first_touch_time":f["touches"][0]["pivot_time"],"last_touch_time":f["touches"][-1]["pivot_time"],"touch_count":len(f["touches"]),"tolerance_ticks":int(tolerance_ticks),"min_touches":int(min_touches),"round_confluence":abs(level_ticks-nearest)<=1,"historical":f["touches"][0]["activation_date"]!=activation_date,"mirror":mirror,"source_pivot_ids":"|".join(str(q["pivot_id"]) for q in f["touches"])})
    return pd.DataFrame(rows)

def _signal(candidate_id,family,submodel,instrument,signal_time,signal_trading_date,direction,stop_ticks=None,target_r=None,target_ticks=None,**audit):
    if direction not in (-1,1):raise ValueError("direction must be +/-1")
    row={"candidate_id":candidate_id,"family":family,"submodel":submodel,"instrument":instrument,"signal_time":pd.Timestamp(signal_time),"signal_trading_date":signal_trading_date,"direction":int(direction),"side":"LONG" if direction==1 else "SHORT","stop_ticks":None if stop_ticks is None else int(stop_ticks),"target_r":target_r,"target_ticks":None if target_ticks is None else int(target_ticks)};row.update(audit);return row

def finalize_signal_ids(signals):
    if signals.empty:return signals.copy()
    rows=[]
    for r in signals.to_dict("records"):
        semantic={"candidate_id":r["candidate_id"],"instrument":r["instrument"],"signal_time":pd.Timestamp(r["signal_time"]).isoformat(),"direction":int(r["direction"]),"stop_ticks":r.get("stop_ticks"),"target_r":r.get("target_r"),"target_ticks":r.get("target_ticks"),"level_snapshot_id":r.get("level_snapshot_id"),"direction_cny":r.get("direction_cny"),"direction_si":r.get("direction_si")};r["signal_id"]=stable_id("SIG",semantic,24);rows.append(r)
    return pd.DataFrame(rows).sort_values(["signal_time","candidate_id","signal_id"],kind="mergesort").drop_duplicates("signal_id").reset_index(drop=True)

def structural_signals(m5,levels,instrument,candidate):
    sub=candidate["submodel"]
    if sub not in {"REJECTION","SIMPLE_SWEEP","COMPLEX_FALSE_BREAK","BREAKOUT_RETEST"}:raise ValueError("ordinary structural submodel required")
    if levels.empty:return pd.DataFrame()
    tol=int(candidate["parameters"]["tolerance_ticks"]);target=float(candidate["parameters"]["target_r"]);tick=TICKS[instrument];_,date_rank=_market_dates(m5);ct=np.array([price_to_ticks(v,tick) for v in m5.close]);ht=np.array([price_to_ticks(v,tick) for v in m5.high]);lt=np.array([price_to_ticks(v,tick) for v in m5.low]);rows=[]
    for fid,fl in levels.groupby("level_family_id",sort=False):
        fl=fl.sort_values(["activation_index","snapshot_version"],kind="mergesort").reset_index(drop=True);birth=int(fl.family_birth_rank.iloc[0]);expiry=int(fl.family_expiry_rank_exclusive.iloc[0]);start=int(fl.activation_index.min());versions={int(r.activation_index):r for r in fl.itertuples()};current=None;states={"support":{"armed":True,"pending":None},"resistance":{"armed":True,"pending":None}};prev_role=None;prev_date=None
        for i in range(start,len(m5)):
            dte=m5.trading_date.iloc[i];dr=date_rank[dte]
            if dr>=expiry:break
            if dr<birth:continue
            if i in versions:
                current=versions[i]
                for st in states.values():st["pending"]=None
            if current is None:continue
            level=int(current.level_ticks);typ=current.level_type;prev_close=ct[i-1] if i>0 else None
            role="support" if typ=="EL" else "resistance" if typ=="EH" else ("support" if prev_close is not None and prev_close>level+tol else "resistance" if prev_close is not None and prev_close<level-tol else None)
            if role!=prev_role and prev_role is not None:
                states[prev_role]["pending"]=None;states[prev_role]["armed"]=False
                if role is not None:states[role]["pending"]=None;states[role]["armed"]=False
            prev_role=role
            if prev_date is not None and dte!=prev_date:
                for st in states.values():st["pending"]=None
            prev_date=dte
            if role is None:continue
            st=states[role];support=role=="support";direction=1 if support else -1;rearm=ct[i]>level+tol if support else ct[i]<level-tol
            if not st["armed"] and st["pending"] is None and rearm:st["armed"]=True;continue
            pending=st["pending"]
            if pending is not None:
                pending["age"]+=1;pending["lo"]=min(pending["lo"],lt[i]);pending["hi"]=max(pending["hi"],ht[i]);age=pending["age"];false_break=ct[i]>level if support else ct[i]<level;bd=-1 if support else 1;retest=(ht[i]>=level-tol and ct[i]<level) if bd==-1 else (lt[i]<=level+tol and ct[i]>level);em=None
                if 1<=age<=3 and false_break:stop=pending["lo"]-1 if support else pending["hi"]+1;em="COMPLEX_FALSE_BREAK";sig_dir=direction
                elif 1<=age<=5 and retest:stop=ht[i]+1 if bd==-1 else lt[i]-1;em="BREAKOUT_RETEST";sig_dir=bd
                if em:
                    if em==sub:rows.append(_signal(candidate["candidate_id"],"STRUCTURAL",em,instrument,m5.close_time.iloc[i],dte,sig_dir,stop,target,level_snapshot_id=current.level_snapshot_id,level_family_id=fid,snapshot_version=int(current.snapshot_version),level_ticks=level,round_confluence=bool(current.round_confluence)))
                    st["pending"]=None;continue
                if age>5:st["pending"]=None
                continue
            if not st["armed"]:continue
            touch=lt[i]<=level+tol if support else ht[i]>=level-tol;reclaim=ct[i]>level if support else ct[i]<level;sweep=lt[i]<=level-1 if support else ht[i]>=level+1
            if touch and reclaim:
                em="SIMPLE_SWEEP" if sweep else "REJECTION"
                if em==sub:
                    stop=lt[i]-1 if support else ht[i]+1;rows.append(_signal(candidate["candidate_id"],"STRUCTURAL",em,instrument,m5.close_time.iloc[i],dte,direction,stop,target,level_snapshot_id=current.level_snapshot_id,level_family_id=fid,snapshot_version=int(current.snapshot_version),level_ticks=level,round_confluence=bool(current.round_confluence)))
                st["armed"]=False;continue
            beyond=ct[i]<=level-1 if support else ct[i]>=level+1
            if beyond:st["pending"]={"age":0,"lo":lt[i],"hi":ht[i]};st["armed"]=False
    return finalize_signal_ids(pd.DataFrame(rows))

def gerchik_a_signals(m5,levels,instrument,candidate):
    if levels.empty:return pd.DataFrame()
    target=float(candidate["parameters"]["target_r"]);x=indicators(m5,slow=50);tick=TICKS[instrument];lt=np.array([price_to_ticks(v,tick) for v in x.low]);ht=np.array([price_to_ticks(v,tick) for v in x.high]);ct=np.array([price_to_ticks(v,tick) for v in x.close]);_,rank=_market_dates(x);rows=[]
    for fid,fam in levels.groupby("level_family_id",sort=False):
        fam=fam.sort_values(["activation_index","snapshot_version"],kind="mergesort").reset_index(drop=True);expiry=int(fam.family_expiry_rank_exclusive.iloc[0])
        for k,L in fam.iterrows():
            if L.level_type=="MIRROR":continue
            start=int(L.activation_index);next_start=int(fam.activation_index.iloc[k+1]) if k+1<len(fam) else len(x);direction=1 if L.level_type=="EL" else -1;level=int(L.level_ticks)
            for i in range(max(start,3),min(next_start-1,len(x)-1)):
                if rank[x.trading_date.iloc[i]]>=expiry:break
                j=i+1
                if x.trading_date.iloc[i]!=x.trading_date.iloc[j]:continue
                if j>=next_start:break
                if rank[x.trading_date.iloc[j]]>=expiry:break
                exact=lt[i]==level if direction==1 else ht[i]==level
                if not exact:continue
                trend=(direction==1 and x.ema20.iloc[j]>x.ema_slow.iloc[j] and x.ema_slow.iloc[j]>x.ema_slow.iloc[j-3]) or (direction==-1 and x.ema20.iloc[j]<x.ema_slow.iloc[j] and x.ema_slow.iloc[j]<x.ema_slow.iloc[j-3])
                if not trend:continue
                stop=level-direction;risk=abs(ct[j]-stop);luft=max(1,_half_up_int(Decimal(int(risk))*Decimal("0.2")));no_pierce=lt[j]>=level if direction==1 else ht[j]<=level;near=(level<=lt[j]<=level+luft) if direction==1 else (level-luft<=ht[j]<=level)
                if no_pierce and near:
                    rows.append(_signal(candidate["candidate_id"],"STRUCTURAL","GERCHIK_A_M5_PROXY",instrument,x.close_time.iloc[j],x.trading_date.iloc[j],direction,stop,target,level_snapshot_id=L.level_snapshot_id,level_family_id=fid,snapshot_version=int(L.snapshot_version),level_ticks=level,BSU_time=L.first_touch_time,BPU1_time=x.close_time.iloc[i],BPU2_time=x.close_time.iloc[j],luft_ticks=luft,source_fidelity="PROXY_NOT_EXACT_SOURCE_REPLICATION"));break
    return finalize_signal_ids(pd.DataFrame(rows))
