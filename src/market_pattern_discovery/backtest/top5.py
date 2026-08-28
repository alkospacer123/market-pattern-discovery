"""Causal implementations for the Top-5 real-strategy benchmark.

All feature rows are stamped at their closed-bar availability time.  Strategy
selection is deliberately kept separate from evaluation by :func:`assert_oos`.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import json
import numpy as np
import pandas as pd

from market_pattern_discovery.backtest.phase6b import load_discovery
from market_pattern_discovery.backtest.phase6b import add_wilder_atr14
from market_pattern_discovery.features.core import canonical_trading_date

DEV_END = pd.Timestamp("2026-03-01", tz="Europe/Moscow")
VAL_A_END = pd.Timestamp("2026-05-01", tz="Europe/Moscow")
END = pd.Timestamp("2026-05-16", tz="Europe/Moscow")
TICKS = {"CNYRUBF": .001, "USDRUBF": .01}
ROUNDS = {"CNYRUBF": .05, "USDRUBF": .10}

MANDATORY_CONTRACT = {
    "families": {
        "STRUCTURAL": ["REJECTION", "SIMPLE_SWEEP", "COMPLEX_FALSE_BREAK", "BREAKOUT_RETEST", "GERCHIK_A_M1_PROXY"],
        "ORB": ["DIRECT", "BREAKOUT_RETEST", "FAILED_BREAKOUT"],
        "TREND_PULLBACK": ["EMA20_50", "EMA20_100"],
        "PAIRS": ["DISTANCE", "OLS"],
        "BOLLINGER_RSI": ["REENTRY_2R", "REENTRY_FIXED_MID"],
    },
    "requirements": {"EH_EL": "REQUIRED", "MIRROR_LEVEL": "REQUIRED", "HISTORICAL_FLAG": "REQUIRED", "ROUND_NUMBER": "CONFLUENCE_ONLY"},
    "source_mappings": {
        "GERCHIK_SIMPLE_FALSE_BREAK": {"source_mapping": "SIMPLE_SWEEP", "source_fidelity": "ADAPTED_TO_M1_M5"},
        "GERCHIK_COMPLEX_FALSE_BREAK": {"source_mapping": "COMPLEX_FALSE_BREAK", "source_fidelity": "ADAPTED_TO_M1_M5"},
        "GERCHIK_BREAKOUT_RETEST": {"source_mapping": "BREAKOUT_RETEST", "source_fidelity": "ADAPTED_TO_M1_M5"},
        "GERCHIK_A_M1_PROXY": {"source_fidelity": "PROXY"},
    },
}

def validate_contract(contract):
    for family, required in MANDATORY_CONTRACT["families"].items():
        if not set(required).issubset(contract.get("families", {}).get(family, [])):
            raise ValueError(f"incomplete strategy contract: {family}")
    if contract.get("requirements") != MANDATORY_CONTRACT["requirements"]: raise ValueError("incomplete requirements")
    for key,value in MANDATORY_CONTRACT["source_mappings"].items():
        if contract.get("source_mappings",{}).get(key)!=value: raise ValueError(f"incomplete source mapping: {key}")
    return True

def load_dev(data_root, instrument):
    """Read only Q1 rows strictly before DEV_END; never opens Q2 or 2025."""
    folder="CNY" if instrument=="CNYRUBF" else "Si";path=Path(data_root)/"2026"/folder/f'{folder}_2026_Q1_M1.csv'
    # Determine the prefix length without materializing any post-DEV market
    # record.  FINAM files are chronological, so pd.read_csv receives nrows.
    nrows=0
    with path.open(encoding="utf-8-sig") as source:
        next(source)
        for line in source:
            fields=line.split(";",4)
            if len(fields)<3 or int(fields[2])>=20260301:break
            if int(fields[2])>=20260105:nrows+=1
    raw=pd.read_csv(path,sep=";",nrows=nrows)
    date=raw["<DATE>"].astype(int);time=raw["<TIME>"].astype(str).str.zfill(6)
    stamp=pd.to_datetime(date.astype(str)+time,format="%Y%m%d%H%M%S").dt.tz_localize("Europe/Moscow")
    mask=(stamp>=pd.Timestamp("2026-01-05",tz="Europe/Moscow"))&(stamp<DEV_END)
    r=raw.loc[mask];stamp=stamp.loc[mask]
    f=pd.DataFrame({"open":r["<OPEN>"].to_numpy(float),"high":r["<HIGH>"].to_numpy(float),"low":r["<LOW>"].to_numpy(float),"close":r["<CLOSE>"].to_numpy(float),"volume":r["<VOL>"].to_numpy(float),"instrument":instrument,"timeframe":"M1","open_time":stamp.to_numpy()})
    f["open_time"]=pd.DatetimeIndex(f.open_time);f["close_time"]=f.open_time+pd.Timedelta(minutes=1);f["trading_date"]=canonical_trading_date(f.open_time);f=add_wilder_atr14(f);f["tick"]=TICKS[instrument]
    if f.empty or f.open_time.max()>=DEV_END or f.open_time.dt.year.ne(2026).any():raise ValueError("DEV-only boundary violation")
    return f.reset_index(drop=True)

def sample_tier(n): return "VERY_LOW" if n<20 else "LOW" if n<50 else "MODERATE" if n<100 else "BETTER"
def select_variant(frame):
    rank={"VERY_LOW":0,"LOW":1,"MODERATE":2,"BETTER":3};x=frame.copy();x["positive"]=x.base_expectancy.gt(0);x["sample_tier"]=x.trades.map(sample_tier);x["tier_rank"]=x.sample_tier.map(rank)
    return x.sort_values(["positive","tier_rank","base_pf","max_dd","complexity"],ascending=[False,False,False,True,True],kind="mergesort").iloc[0]


def causal_m5(m1: pd.DataFrame) -> pd.DataFrame:
    """Aggregate complete five-minute candles; labels are their close times."""
    x = m1.set_index("open_time")
    out = x.resample("5min", label="right", closed="left", origin="start_day").agg(
        open=("open", "first"), high=("high", "max"), low=("low", "min"),
        close=("close", "last"), volume=("volume", "sum"), count=("close", "size"),
        trading_date=("trading_date", "first"))
    out = out[out["count"].eq(5)].drop(columns="count").reset_index(names="close_time")
    out["open_time"] = out.close_time - pd.Timedelta(minutes=5)
    return out


def indicators(m5: pd.DataFrame, fast=20, slow=50, bb_k=2., rsi_n=14) -> pd.DataFrame:
    x=m5.copy(); c=x.close.astype(float)
    x["ema_fast"]=c.ewm(span=fast,adjust=False).mean(); x["ema_slow"]=c.ewm(span=slow,adjust=False).mean()
    x["bb_mid"]=c.rolling(20).mean(); sd=c.rolling(20).std(ddof=0)
    x["bb_upper"]=x.bb_mid+bb_k*sd; x["bb_lower"]=x.bb_mid-bb_k*sd
    d=c.diff(); gain=d.clip(lower=0); loss=-d.clip(upper=0)
    ag=gain.ewm(alpha=1/rsi_n,adjust=False,min_periods=rsi_n).mean(); al=loss.ewm(alpha=1/rsi_n,adjust=False,min_periods=rsi_n).mean()
    x["rsi"]=100-100/(1+ag/al.replace(0,np.nan)); x.loc[(al.eq(0))&(ag.gt(0)),"rsi"]=100
    return x


def confirmed_pivots(m5: pd.DataFrame) -> pd.DataFrame:
    """Pivots are emitted at j+2, never at pivot bar j."""
    rows=[]; h=m5.high.to_numpy(); l=m5.low.to_numpy()
    for j in range(2,len(m5)-2):
        known=j+2
        if h[j]>=h[j-2:j+3].max(): rows.append({"side":"HIGH","pivot_index":j,"known_index":known,"pivot_time":m5.close_time.iloc[j],"known_time":m5.close_time.iloc[known],"price":h[j]})
        if l[j]<=l[j-2:j+3].min(): rows.append({"side":"LOW","pivot_index":j,"known_index":known,"pivot_time":m5.close_time.iloc[j],"known_time":m5.close_time.iloc[known],"price":l[j]})
    return pd.DataFrame(rows)


def structural_levels(m5: pd.DataFrame, instrument: str, tolerance_ticks=2, min_touches=2) -> pd.DataFrame:
    """Create immutable causal versions whenever a confirmed touch qualifies."""
    piv=confirmed_pivots(m5).sort_values(["known_index","side"],kind="mergesort").reset_index(drop=True)
    if piv.empty:return pd.DataFrame()
    tick=TICKS[instrument];tol=tolerance_ticks*tick;families=[];rows=[]
    for pid,p in piv.iterrows():
        candidates=[f for f in families if abs(p.price-f["price"])<=tol and p.pivot_index-f["last_index"]>=2]
        if candidates:f=min(candidates,key=lambda x:(abs(p.price-x["price"]),x["id"]))
        else:
            f={"id":len(families),"touches":[],"price":float(p.price),"last_index":-10};families.append(f)
        if p.pivot_index-f["last_index"]<2:continue
        f["touches"].append({**p.to_dict(),"pivot_id":int(pid)});f["last_index"]=int(p.pivot_index);f["price"]=float(np.mean([q["price"] for q in f["touches"]]))
        highs=[q for q in f["touches"] if q["side"]=="HIGH"];lows=[q for q in f["touches"] if q["side"]=="LOW"]
        mirror=bool(highs and lows); qualifying=mirror or len(highs)>=min_touches or len(lows)>=min_touches
        if not qualifying:continue
        version=1+sum(r["level_family_id"]==f'{instrument}-L{f["id"]}' for r in rows)
        typ="MIRROR" if mirror else "EH" if len(highs)>=min_touches else "EL";q=f["touches"];price=f["price"];valid=pd.Timestamp(p.known_time)
        rows.append({"level_family_id":f'{instrument}-L{f["id"]}',"level_snapshot_id":f'{instrument}-L{f["id"]}-V{version}',"snapshot_version":version,"instrument":instrument,"level_type":typ,"level_price":price,"valid_from":valid,"first_touch":q[0]["pivot_time"],"last_touch":q[-1]["pivot_time"],"touch_count":len(q),"touch_times":"|".join(str(z["pivot_time"]) for z in q),"tolerance_ticks":tolerance_ticks,"min_touches":min_touches,"round_confluence":abs(price-round(price/ROUNDS[instrument])*ROUNDS[instrument])<=tick+1e-12,"historical":pd.Timestamp(q[0]["pivot_time"]).date()<valid.date(),"mirror":mirror,"source_pivot_ids":"|".join(str(z["pivot_id"]) for z in q),"source_sides":"|".join(z["side"] for z in q),"known_index":int(p.known_index)})
    out=pd.DataFrame(rows)
    if not out.empty:
        # Compatibility aliases are read-only copies, never cluster state.
        out["level_id"]=out.level_snapshot_id;out["price"]=out.level_price;out["known_time"]=out.valid_from
    return out


def structural_signals(m5, levels, instrument, target_r=3.):
    rows=[]; tick=TICKS[instrument]
    levels=levels.copy()
    aliases={"level_family_id":"level_id","level_snapshot_id":"level_id","level_price":"price","valid_from":"known_time"}
    for new,old in aliases.items():
        if new not in levels and old in levels:levels[new]=levels[old]
    defaults={"snapshot_version":1,"historical":False,"mirror":False}
    for col,value in defaults.items():
        if col not in levels:levels[col]=value
    times=m5.close_time.array; time_values=list(m5.close_time); lows=m5.low.to_numpy(float); highs=m5.high.to_numpy(float); closes=m5.close.to_numpy(float)
    ordered=levels.sort_values(["level_family_id","snapshot_version"]) if len(levels) else levels
    next_valid=ordered.groupby("level_family_id").valid_from.shift(-1) if len(ordered) else pd.Series(dtype="datetime64[ns]")
    for n,L in enumerate(ordered.itertuples()):
        start=pd.Timestamp(L.valid_from); finish=min(start+pd.Timedelta(days=5),pd.Timestamp(next_valid.iloc[n])) if pd.notna(next_valid.iloc[n]) else start+pd.Timedelta(days=5)
        active=np.flatnonzero((times>=start)&(times<finish))
        pending=[]
        for i in active:
            low=lows[i];high=highs[i];close=closes[i];time=time_values[i];tol=L.tolerance_ticks*tick
            roles=(True,False) if L.level_type=="MIRROR" else (L.level_type=="EL",)
            for support in roles:
              touch=low<=L.level_price+tol if support else high>=L.level_price-tol
              reclaim=close>L.level_price if support else close<L.level_price
              sweep=low<=L.level_price-tick if support else high>=L.level_price+tick
              if touch and reclaim:
                subtype="SIMPLE_SWEEP" if sweep else "REJECTION"; direction=1 if support else -1;stop=low-tick if direction==1 else high+tick
                rows.append(_signal("STRUCTURAL",subtype,instrument,time,direction,L.level_price,stop,target_r,L.level_snapshot_id,level_type=L.level_type,round_confluence=L.round_confluence,level_family_id=L.level_family_id,snapshot_version=L.snapshot_version,historical=L.historical,mirror=L.mirror))
              beyond=close>=L.level_price+tick if not support else close<=L.level_price-tick
              if beyond: pending.append((i,1 if not support else -1,L.level_price,low,high))
            keep=[]
            for j,d,price,lo,hi in pending:
                age=i-j; lo=min(lo,low); hi=max(hi,high)
                original=(close<L.level_price if d==1 else close>L.level_price)
                retest=(low<=price+tol and close>price) if d==1 else (high>=price-tol and close<price)
                if 1<=age<=3 and original:
                    stop=lo-tick if d==-1 else hi+tick
                    rows.append(_signal("STRUCTURAL","COMPLEX_FALSE_BREAK",instrument,time,-d,price,stop,target_r,L.level_snapshot_id,level_type=L.level_type,round_confluence=L.round_confluence,level_family_id=L.level_family_id,snapshot_version=L.snapshot_version,historical=L.historical,mirror=L.mirror))
                elif 1<=age<=5 and retest:
                    stop=low-tick if d==1 else high+tick
                    rows.append(_signal("STRUCTURAL","BREAKOUT_RETEST",instrument,time,d,price,stop,target_r,L.level_snapshot_id,level_type=L.level_type,round_confluence=L.round_confluence,level_family_id=L.level_family_id,snapshot_version=L.snapshot_version,historical=L.historical,mirror=L.mirror,breakout_level_snapshot_id=L.level_snapshot_id))
                elif age<=5:keep.append((j,d,price,lo,hi))
            pending=keep
    return pd.DataFrame(rows).drop_duplicates(["submodel","signal_time","direction","reference_level"]) if rows else pd.DataFrame()

def gerchik_a_signals(m5, levels, instrument):
    """Strict M1/M5-executable proxy; never an exact Gerchik replication."""
    x=indicators(m5,20,50);tick=TICKS[instrument];rows=[]
    for L in levels.itertuples():
        if L.level_type=="MIRROR":continue
        d=1 if L.level_type=="EL" else -1;level_tick=round(L.level_price/tick)*tick
        bsu=pd.Timestamp(L.first_touch); start=max(int(L.known_index),3)
        later=levels[(levels.level_family_id==L.level_family_id)&(levels.snapshot_version>L.snapshot_version)]
        finish=int(later.known_index.iloc[0]) if len(later) else len(x)
        for i in range(start,min(finish,len(x)-1)):
            b1=x.iloc[i];b2=x.iloc[i+1]
            trend=(d==1 and b2.ema_fast>b2.ema_slow and b2.ema_slow>x.ema_slow.iloc[i-2]) or (d==-1 and b2.ema_fast<b2.ema_slow and b2.ema_slow<x.ema_slow.iloc[i-2])
            hit=np.isclose(b1.low if d==1 else b1.high,level_tick,atol=tick/10); no_pierce=b2.low>=level_tick if d==1 else b2.high<=level_tick
            stop=level_tick-d*tick;risk=abs(b2.close-stop);luft=max(tick,.2*risk);near=level_tick<=b2.low<=level_tick+luft if d==1 else level_tick-luft<=b2.high<=level_tick
            if trend and hit and no_pierce and near:
                rows.append(_signal("STRUCTURAL","GERCHIK_A_M1_PROXY",instrument,b2.close_time,d,level_tick,stop,3.,L.level_snapshot_id,BSU_time=bsu,BPU1_time=b1.close_time,BPU2_time=b2.close_time,level_tick=level_tick,luft_price=luft,local_trend="LONG" if d==1 else "SHORT",source_fidelity="PROXY"));break
    return pd.DataFrame(rows)


def _signal(family,submodel,instrument,time,direction,ref,stop,target_r=None,level_id=None,**audit):
    return {"family":family,"submodel":submodel,"instrument":instrument,"signal_time":time,"direction":direction,"side":"LONG" if direction==1 else "SHORT","reference_level":ref,"stop_price":stop,"target_r":target_r,"level_id":level_id,**audit}


def orb_signals(m1,instrument,length=15,target_r=2.,retest=False,submodel=None,stop_mode="STOP_OPPOSITE_OR"):
    submodel=submodel or ("BREAKOUT_RETEST" if retest else "DIRECT")
    rows=[]; tick=TICKS[instrument]
    for date,g in m1.groupby("trading_date",sort=False):
        start=pd.Timestamp(date,tz="Europe/Moscow")+pd.Timedelta(hours=10); end=start+pd.Timedelta(minutes=length)
        opening=g[(g.open_time>=start)&(g.open_time<end)]
        if len(opening)!=length:continue
        oh,ol=opening.high.max(),opening.low.min(); later=g[g.open_time>=end]; broke=None;exc_lo=np.inf;exc_hi=-np.inf
        for b in later.itertuples():
            d=1 if b.close>oh+tick-1e-12 else -1 if b.close<ol-tick+1e-12 else 0
            if broke is None and d:
                broke=(b,d,oh if d==1 else ol);exc_lo=b.low;exc_hi=b.high
                if submodel=="DIRECT":
                    mid=(oh+ol)/2;stop=(ol if d==1 else oh) if stop_mode=="STOP_OPPOSITE_OR" else mid
                    rows.append(_signal("ORB","DIRECT",instrument,b.close_time,d,broke[2],stop,target_r,or_high=oh,or_low=ol,or_mid=mid,or_length=length,stop_mode=stop_mode))
            elif broke is not None and submodel in ("BREAKOUT_RETEST","FAILED_BREAKOUT"):
                bb,d,lev=broke; age=int((b.open_time-bb.open_time)/pd.Timedelta(minutes=1))
                exc_lo=min(exc_lo,b.low);exc_hi=max(exc_hi,b.high)
                if submodel=="BREAKOUT_RETEST":
                    hit=(b.low<=lev+tick and b.close>lev) if d==1 else (b.high>=lev-tick and b.close<lev)
                    if 1<=age<=5 and hit:
                        stop=b.low-tick if d==1 else b.high+tick; rows.append(_signal("ORB","BREAKOUT_RETEST",instrument,b.close_time,d,lev,stop,target_r,or_high=oh,or_low=ol,or_length=length)); break
                else:
                    inside=ol<b.close<oh
                    if 1<=age<=5 and inside:
                        rd=-d;stop=exc_lo-tick if rd==1 else exc_hi+tick;rows.append(_signal("ORB","FAILED_BREAKOUT",instrument,b.close_time,rd,lev,stop,target_r,or_high=oh,or_low=ol,failed_excursion_low=exc_lo,failed_excursion_high=exc_hi,or_length=length));break
                if age>5:break
    return pd.DataFrame(rows)


def trend_signals(m5,instrument,slow=50,target_r=3.):
    x=indicators(m5,20,slow); rows=[]; tick=TICKS[instrument]
    for _,idx in x.groupby("trading_date",sort=False).indices.items():
        pull=None
        for pos,i in enumerate(idx):
            if i<slow+3:continue
            b=x.loc[i]; d=1 if b.ema_fast>b.ema_slow and b.ema_slow>x.ema_slow.iloc[i-3] else -1 if b.ema_fast<b.ema_slow and b.ema_slow<x.ema_slow.iloc[i-3] else 0
            if pull:
                age=pos-pull["pos"]; invalid=b.close<b.ema_slow if pull["d"]==1 else b.close>b.ema_slow
                if invalid or age>6:pull=None
                else:
                    pull["lo"]=min(pull["lo"],b.low);pull["hi"]=max(pull["hi"],b.high)
                    resume=(b.close>b.ema_fast and b.close>x.close.iloc[i-1]) if pull["d"]==1 else (b.close<b.ema_fast and b.close<x.close.iloc[i-1])
                    if resume:
                        dd=pull["d"]; stop=pull["lo"]-tick if dd==1 else pull["hi"]+tick
                        rows.append(_signal("TREND_PULLBACK",f"EMA20_{slow}",instrument,b.close_time,dd,b.ema_fast,stop,target_r,pullback_start=x.close_time.iloc[pull["i"]],pullback_bars=age+1,ema_fast=b.ema_fast,ema_slow=b.ema_slow));pull=None
            if pull is None and d and ((d==1 and b.low<=b.ema_fast and b.close>=b.ema_slow) or (d==-1 and b.high>=b.ema_fast and b.close<=b.ema_slow)):
                pull={"pos":pos,"i":i,"d":d,"lo":b.low,"hi":b.high}
    return pd.DataFrame(rows)


def mean_reversion_signals(m5,instrument,k=2.,lower=30,target_r=2.,exit_mode="REENTRY_2R"):
    x=indicators(m5,bb_k=k); rows=[]; tick=TICKS[instrument]; pending=None
    for i,b in x.iterrows():
        if pending:
            age=i-pending["i"]; pending["lo"]=min(pending["lo"],b.low);pending["hi"]=max(pending["hi"],b.high)
            inside=b.close>x.bb_lower.iloc[i] if pending["d"]==1 else b.close<x.bb_upper.iloc[i]
            if 1<=age<=3 and inside:
                d=pending["d"];stop=pending["lo"]-tick if d==1 else pending["hi"]+tick
                sub=exit_mode;tr=target_r if sub=="REENTRY_2R" else None;target=float(b.bb_mid) if sub=="REENTRY_FIXED_MID" else None
                rows.append(_signal("BOLLINGER_RSI",sub,instrument,b.close_time,d,b.bb_mid,stop,tr,extreme_time=x.close_time.iloc[pending["i"]],reentry_time=b.close_time,band=pending["band"],rsi=pending["rsi"],bb_k=k,rsi_threshold=lower,target_price=target));pending=None
            elif age>=3:pending=None
        if pending is None and np.isfinite(b.rsi):
            if b.close<b.bb_lower and b.rsi<=lower:pending={"i":i,"d":1,"lo":b.low,"hi":b.high,"band":b.bb_lower,"rsi":b.rsi}
            elif b.close>b.bb_upper and b.rsi>=100-lower:pending={"i":i,"d":-1,"lo":b.low,"hi":b.high,"band":b.bb_upper,"rsi":b.rsi}
    return pd.DataFrame(rows)


def pair_features(cny,si,window=480,model="DISTANCE"):
    a=cny[["close_time","open_time","close","open","trading_date"]].merge(si[["close_time","open_time","close","open"]],on="close_time",suffixes=("_cny","_si"))
    lc=np.log(a.close_cny); ls=np.log(a.close_si)
    if model=="OLS":
        # Coefficients at t use [t-window,t), implemented by shift(1).
        mx=ls.shift(1).rolling(window).mean();my=lc.shift(1).rolling(window).mean()
        cov=(ls*lc).shift(1).rolling(window).mean()-mx*my;var=(ls*ls).shift(1).rolling(window).mean()-mx*mx
        beta=cov/var;alpha=my-beta*mx;spread=lc-alpha-beta*ls
        # Historical residual standard deviation under the coefficients known at t.
        ey2=(lc*lc).shift(1).rolling(window).mean();ex2=(ls*ls).shift(1).rolling(window).mean();exy=(ls*lc).shift(1).rolling(window).mean()
        variance=(ey2 + alpha*alpha + beta*beta*ex2 - 2*alpha*my - 2*beta*exy + 2*alpha*beta*mx).clip(lower=0)
        mean=pd.Series(0.,index=a.index);sd=np.sqrt(variance*window/(window-2))
    else:
        # Exact Gatev normalized distance.  Rolling moments are divided by the
        # first observation in [t-window,t), which is shift(window).
        c=a.close_cny.astype(float);s=a.close_si.astype(float);c0=c.shift(window);s0=s.shift(window)
        mc=c.shift(1).rolling(window).mean()/c0;ms=s.shift(1).rolling(window).mean()/s0
        mean=mc-ms
        second=(c*c).shift(1).rolling(window).sum()/(c0*c0)+(s*s).shift(1).rolling(window).sum()/(s0*s0)-2*(c*s).shift(1).rolling(window).sum()/(c0*s0)
        variance=(second-window*mean*mean)/(window-1);sd=np.sqrt(variance.clip(lower=0));spread=c/c0-s/s0;beta=pd.Series(1.,index=a.index)
    a["spread"]=spread;a["z"]=(spread-mean)/sd;a["beta"]=beta;return a


def pair_signals(cny,si,window=480,z_entry=2.,model="DISTANCE"):
    x=pair_features(cny,si,window,model); rows=[];i=0
    while i<len(x):
        b=x.iloc[i]
        if not np.isfinite(b.z) or abs(b.z)<z_entry:i+=1;continue
        d=-1 if b.z>0 else 1;entry_z=float(b.z);day=b.trading_date;exit_i=i;reason="DAY_END"
        for j in range(i+1,min(i+121,len(x))):
            q=x.iloc[j]
            if q.trading_date!=day:exit_i=j-1;reason="DAY_END";break
            exit_i=j
            if np.sign(q.z)!=np.sign(entry_z) or q.z==0:reason="CONVERGENCE";break
            if j-i==120:reason="TIME";break
        q=x.iloc[exit_i]
        rows.append({"family":"PAIRS","submodel":model,"instrument":"CNYRUBF+USDRUBF","signal_time":b.close_time,"direction_cny":d,"direction_si":-d,"z":entry_z,"entry_z":entry_z,"exit_z":float(q.z),"beta":float(b.beta),"beta_at_entry":float(b.beta),"window":window,"z_entry":z_entry,"feature_index":i,"exit_feature_index":exit_i,"planned_exit_time":q.close_time,"planned_exit_reason":reason})
        i=exit_i+1
    return pd.DataFrame(rows)


def simulate_explicit_orders(m1,signals,tick,max_hold=120):
    """Explicit structural prices; next-open, same-day, stop-first, gap-aware."""
    rows=[]
    if signals.empty:return pd.DataFrame()
    open_ns=m1.open_time.astype("int64").to_numpy(); unit=m1.open_time.dtype.unit; divisor={"ns":1,"us":1_000,"ms":1_000_000,"s":1_000_000_000}[unit]
    op=m1.open.to_numpy(float);hi=m1.high.to_numpy(float);lo=m1.low.to_numpy(float);cl=m1.close.to_numpy(float);dates=m1.trading_date.to_numpy();ot=m1.open_time.array;ct=m1.close_time.array
    day_end=np.empty(len(m1),int)
    for ix in m1.groupby("trading_date",sort=False).indices.values():day_end[np.asarray(ix)]=max(ix)
    for tid,s in enumerate(signals.sort_values("signal_time").itertuples(),1):
        stamp=pd.Timestamp(s.signal_time).value//divisor; entry_i=int(np.searchsorted(open_ns,stamp,side="left"))
        if entry_i>=len(m1):continue
        signal_day=pd.Timestamp(s.signal_time).date()
        if dates[entry_i]!=signal_day:continue
        entry=op[entry_i]; d=s.direction; stop=s.stop_price; risk=d*(entry-stop)
        if risk<=0:continue
        tr=getattr(s,"target_r",None);explicit=getattr(s,"target_price",None)
        tr=None if pd.isna(tr) else tr;explicit=None if pd.isna(explicit) else explicit
        if tr is not None and explicit is not None:raise ValueError("exactly one target definition is allowed")
        if tr is None and explicit is None:raise ValueError("target_r or target_price required")
        target=entry+d*risk*tr if tr is not None else float(explicit)
        if d*(target-entry)<=0:continue
        end_i=min(entry_i+max_hold-1,day_end[entry_i]);price=cl[end_i];reason="TIME";exit_i=end_i
        po=op[entry_i:end_i+1];ph=hi[entry_i:end_i+1];pl=lo[entry_i:end_i+1]
        gs=po<=stop if d==1 else po>=stop;hs=pl<=stop if d==1 else ph>=stop;ht=ph>=target if d==1 else pl<=target;hit=gs|hs|ht
        if hit.any():
            off=int(np.flatnonzero(hit)[0]);exit_i=entry_i+off
            if gs[off]:price=op[exit_i];reason="STOP_GAP"
            elif hs[off]:price=stop;reason="STOP_FIRST_TIE" if ht[off] else "STOP"
            else:price=target;reason="TARGET"
        for fr,ticks in (("GROSS",0),("BASE",1),("STRESS",2)):
            net=d*((price-d*ticks*tick)-(entry+d*ticks*tick))
            rows.append({"trade_id":tid,"family":s.family,"submodel":s.submodel,"instrument":s.instrument,"signal_time":s.signal_time,"entry_time":ot[entry_i],"exit_time":ct[exit_i],"side":s.side,"entry_price":entry,"stop_price":stop,"target_price":target,"exit_price":price,"exit_reason":reason,"friction":fr,"pnl":net,"pnl_R":net/risk,"bars_held":exit_i-entry_i+1})
    return pd.DataFrame(rows)


def simulate_pairs(cny,si,signals,max_hold=120):
    rows=[];cu=cny.open_time.astype("int64").to_numpy();su=si.open_time.astype("int64").to_numpy();divisor={"ns":1,"us":1_000,"ms":1_000_000,"s":1_000_000_000}[cny.open_time.dtype.unit]
    for tid,s in enumerate(signals.itertuples(),1):
        stamp=pd.Timestamp(s.signal_time).value//divisor;i=int(np.searchsorted(cu,stamp));j=int(np.searchsorted(su,stamp))
        if i>=len(cny) or j>=len(si):continue
        day=cny.trading_date.iloc[i]
        if hasattr(s,"planned_exit_time"):
            exit_stamp=pd.Timestamp(s.planned_exit_time).value//divisor;end=int(np.searchsorted(cny.close_time.astype("int64").to_numpy(),exit_stamp,side="left"));end=min(end,len(cny)-1);reason=s.planned_exit_reason;exit_z=s.exit_z
        else:
            end=min(i+max_hold-1,i+int((cny.trading_date.iloc[i:].to_numpy()==day).sum())-1);reason="TIME" if end==i+max_hold-1 else "DAY_END";exit_z=np.nan
        ec,es=cny.close.iloc[end],si.close.iloc[min(j+end-i,len(si)-1)]
        beta=float(getattr(s,"beta_at_entry",getattr(s,"beta",1.)));wc=.5 if s.submodel=="DISTANCE" else 1/(1+abs(beta));ws=1-wc
        for fr,t in (("GROSS",0),("BASE",1),("STRESS",2)):
            pc=wc*(s.direction_cny*(ec-cny.open.iloc[i])/cny.open.iloc[i]-2*t*TICKS["CNYRUBF"]/cny.open.iloc[i])
            ps=ws*(s.direction_si*(es-si.open.iloc[j])/si.open.iloc[j]-2*t*TICKS["USDRUBF"]/si.open.iloc[j])
            rows.append({"trade_id":tid,"family":"PAIRS","submodel":s.submodel,"instrument":"CNYRUBF+USDRUBF","signal_time":s.signal_time,"entry_time":cny.open_time.iloc[i],"exit_time":cny.close_time.iloc[end],"exit_reason":reason,"entry_z":getattr(s,"entry_z",np.nan),"exit_z":exit_z,"side":"SPREAD","friction":fr,"w_cny":wc,"w_si":ws,"beta_at_entry":beta,"entry_price_cny":cny.open.iloc[i],"entry_price_si":si.open.iloc[j],"exit_price_cny":ec,"exit_price_si":es,"pnl_cny":pc,"pnl_si":ps,"total_pnl":pc+ps,"pnl":pc+ps,"bars_held":end-i+1})
    return pd.DataFrame(rows)


def metrics(ledger):
    rows=[]
    for key,g in ledger.groupby(["family","submodel","instrument","friction"],dropna=False):
        p=g.pnl.to_numpy(); w=p[p>0]; l=p[p<0]; eq=p.cumsum(); peak=np.maximum.accumulate(np.r_[0,eq])[1:]
        rows.append(dict(zip(["family","submodel","instrument","friction"],key))|{"trades":len(p),"profit_factor":w.sum()/-l.sum() if len(l) else np.inf,"expectancy":p.mean() if len(p) else np.nan,"max_drawdown":max(0,float(np.max(peak-eq))) if len(p) else np.nan,"win_rate":np.mean(p>0),"payoff_ratio":w.mean()/-l.mean() if len(w) and len(l) else np.nan,"average_holding_time":g.bars_held.mean()})
    return pd.DataFrame(rows)


def assert_oos(selection_end,evaluation_start):
    if pd.Timestamp(evaluation_start)<=pd.Timestamp(selection_end):raise ValueError("evaluation overlaps parameter-selection period")


def freeze(path,variants):
    data=json.dumps(variants,sort_keys=True,indent=2)+"\n";Path(path).write_text(data);return sha256(data.encode()).hexdigest()


def verify_frozen(path,digest):
    return sha256(Path(path).read_bytes()).hexdigest()==digest
