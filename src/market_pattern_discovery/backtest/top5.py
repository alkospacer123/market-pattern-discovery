"""Causal implementations for the Top-5 real-strategy benchmark.

All feature rows are stamped at their closed-bar availability time.  Strategy
selection is deliberately kept separate from evaluation by :func:`assert_oos`.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
from pathlib import Path
import json
import numpy as np
import pandas as pd

from market_pattern_discovery.backtest.phase6b import load_discovery

DEV_END = pd.Timestamp("2026-03-01", tz="Europe/Moscow")
VAL_A_END = pd.Timestamp("2026-05-01", tz="Europe/Moscow")
END = pd.Timestamp("2026-05-16", tz="Europe/Moscow")
TICKS = {"CNYRUBF": .001, "USDRUBF": .01}
ROUNDS = {"CNYRUBF": .05, "USDRUBF": .10}


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
    """Deterministically cluster same-side confirmed pivots into EH/EL levels."""
    piv=confirmed_pivots(m5); tick=TICKS[instrument]; rows=[]
    if piv.empty:return pd.DataFrame()
    for side,g in piv.groupby("side",sort=False):
        clusters=[]; buckets={}; width=max(tolerance_ticks*tick, tick)
        for p in g.sort_values("known_index").to_dict("records"):
            bucket=round(p["price"]/width)
            candidates=[c for k in (bucket-1,bucket,bucket+1) for c in buckets.get(k,[]) if abs(p["price"]-c["price"])<=tolerance_ticks*tick and p["pivot_index"]-c["last_index"]>=2]
            if candidates:
                c=min(candidates,key=lambda z:(abs(p["price"]-z["price"]),z["id"])); old=round(c["price"]/width);c["touches"].append(p); c["price"]=float(np.mean([q["price"] for q in c["touches"]])); c["last_index"]=p["pivot_index"];new=round(c["price"]/width)
                if new!=old:buckets[old].remove(c);buckets.setdefault(new,[]).append(c)
            else:
                c={"id":len(clusters),"price":p["price"],"last_index":p["pivot_index"],"touches":[p]};clusters.append(c);buckets.setdefault(bucket,[]).append(c)
        for c in clusters:
            if len(c["touches"])<min_touches:continue
            q=c["touches"]; price=c["price"]; known=q[-1]["known_time"]
            rows.append({"level_id":f'{instrument}-{side}-{c["id"]}',"instrument":instrument,"level_type":"EH" if side=="HIGH" else "EL","price":price,"touch_count":len(q),"touch_times":"|".join(str(z["pivot_time"]) for z in q),"first_touch":q[0]["pivot_time"],"last_touch":q[-1]["pivot_time"],"known_time":known,"known_index":q[-1]["known_index"],"spacing":min(np.diff([z["pivot_index"] for z in q])) if len(q)>1 else np.nan,"tolerance_ticks":tolerance_ticks,"round_confluence":abs(price-round(price/ROUNDS[instrument])*ROUNDS[instrument])<=tick+1e-12,"mirror":False})
    return pd.DataFrame(rows)


def structural_signals(m5, levels, instrument, target_r=3.):
    rows=[]; tick=TICKS[instrument]
    times=m5.close_time.array; time_values=list(m5.close_time); lows=m5.low.to_numpy(float); highs=m5.high.to_numpy(float); closes=m5.close.to_numpy(float)
    for L in levels.itertuples():
        start=pd.Timestamp(L.known_time); finish=start+pd.Timedelta(days=5)
        active=np.flatnonzero((times>=start)&(times<finish))
        pending=[]
        for i in active:
            low=lows[i];high=highs[i];close=closes[i];time=time_values[i];tol=L.tolerance_ticks*tick
            support=L.level_type=="EL"
            touch=low<=L.price+tol if support else high>=L.price-tol
            reclaim=close>L.price if support else close<L.price
            sweep=low<=L.price-tick if support else high>=L.price+tick
            if touch and reclaim:
                subtype="SIMPLE_SWEEP" if sweep else "REJECTION"; direction=1 if support else -1
                stop=low-tick if direction==1 else high+tick
                rows.append(_signal("STRUCTURAL",subtype,instrument,time,direction,L.price,stop,target_r,L.level_id,level_type=L.level_type,round_confluence=L.round_confluence))
            beyond=close>=L.price+tick if not support else close<=L.price-tick
            if beyond: pending.append((i,1 if not support else -1,L.price,low,high))
            keep=[]
            for j,d,price,lo,hi in pending:
                age=i-j; lo=min(lo,low); hi=max(hi,high)
                original=(close<L.price if d==1 else close>L.price)
                retest=(low<=price+tol and close>price) if d==1 else (high>=price-tol and close<price)
                if 1<=age<=3 and original:
                    stop=lo-tick if d==-1 else hi+tick
                    rows.append(_signal("STRUCTURAL","COMPLEX_FALSE_BREAK",instrument,time,-d,price,stop,target_r,L.level_id,level_type=L.level_type,round_confluence=L.round_confluence))
                elif 1<=age<=5 and retest:
                    stop=low-tick if d==1 else high+tick
                    rows.append(_signal("STRUCTURAL","BREAKOUT_RETEST",instrument,time,d,price,stop,target_r,L.level_id,level_type=L.level_type,round_confluence=L.round_confluence))
                elif age<=5:keep.append((j,d,price,lo,hi))
            pending=keep
    return pd.DataFrame(rows).drop_duplicates(["submodel","signal_time","direction","reference_level"]) if rows else pd.DataFrame()


def _signal(family,submodel,instrument,time,direction,ref,stop,target_r=None,level_id=None,**audit):
    return {"family":family,"submodel":submodel,"instrument":instrument,"signal_time":time,"direction":direction,"side":"LONG" if direction==1 else "SHORT","reference_level":ref,"stop_price":stop,"target_r":target_r,"level_id":level_id,**audit}


def orb_signals(m1,instrument,length=15,target_r=2.,retest=False):
    rows=[]; tick=TICKS[instrument]
    for date,g in m1.groupby("trading_date",sort=False):
        start=pd.Timestamp(date,tz="Europe/Moscow")+pd.Timedelta(hours=10); end=start+pd.Timedelta(minutes=length)
        opening=g[(g.open_time>=start)&(g.open_time<end)]
        if len(opening)!=length:continue
        oh,ol=opening.high.max(),opening.low.min(); later=g[g.open_time>=end]; broke=None
        for b in later.itertuples():
            d=1 if b.close>oh+tick-1e-12 else -1 if b.close<ol-tick+1e-12 else 0
            if broke is None and d:
                broke=(b,d,oh if d==1 else ol); 
                if not retest:
                    stop=ol if d==1 else oh; rows.append(_signal("ORB","DIRECT",instrument,b.close_time,d,broke[2],stop,target_r,or_high=oh,or_low=ol,or_length=length))
            elif broke is not None and retest:
                bb,d,lev=broke; age=int((b.open_time-bb.open_time)/pd.Timedelta(minutes=1))
                hit=(b.low<=lev+tick and b.close>lev) if d==1 else (b.high>=lev-tick and b.close<lev)
                if 1<=age<=5 and hit:
                    stop=b.low-tick if d==1 else b.high+tick; rows.append(_signal("ORB","BREAKOUT_RETEST",instrument,b.close_time,d,lev,stop,target_r,or_high=oh,or_low=ol,or_length=length)); break
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


def mean_reversion_signals(m5,instrument,k=2.,lower=30,target_r=2.):
    x=indicators(m5,bb_k=k); rows=[]; tick=TICKS[instrument]; pending=None
    for i,b in x.iterrows():
        if pending:
            age=i-pending["i"]; pending["lo"]=min(pending["lo"],b.low);pending["hi"]=max(pending["hi"],b.high)
            inside=b.close>x.bb_lower.iloc[i] if pending["d"]==1 else b.close<x.bb_upper.iloc[i]
            if 1<=age<=3 and inside:
                d=pending["d"];stop=pending["lo"]-tick if d==1 else pending["hi"]+tick
                rows.append(_signal("BOLLINGER_RSI","REENTRY_2R",instrument,b.close_time,d,b.bb_mid,stop,target_r,extreme_time=x.close_time.iloc[pending["i"]],reentry_time=b.close_time,band=pending["band"],rsi=pending["rsi"],bb_k=k,rsi_threshold=lower));pending=None
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
    else:
        beta=pd.Series(1.,index=a.index);spread=lc-ls
    mean=spread.shift(1).rolling(window).mean();sd=spread.shift(1).rolling(window).std(ddof=1)
    a["z"]=(spread-mean)/sd;a["beta"]=beta;return a


def pair_signals(cny,si,window=480,z_entry=2.,model="DISTANCE"):
    x=pair_features(cny,si,window,model); rows=[]; active=False
    for i,b in x.iterrows():
        if active:
            if np.sign(b.z)!=np.sign(entry_z) or i-entry_i>=120 or b.trading_date!=entry_day:active=False
        if not active and np.isfinite(b.z) and abs(b.z)>=z_entry:
            active=True;entry_i=i;entry_z=b.z;entry_day=b.trading_date;d=-1 if b.z>0 else 1
            rows.append({"family":"PAIRS","submodel":model,"instrument":"CNYRUBF+USDRUBF","signal_time":b.close_time,"direction_cny":d,"direction_si":-d,"z":b.z,"beta":b.beta,"window":window,"z_entry":z_entry})
    return pd.DataFrame(rows)


def simulate_explicit_orders(m1,signals,tick,max_hold=120):
    """Explicit structural prices; next-open, same-day, stop-first, gap-aware."""
    rows=[]
    if signals.empty:return pd.DataFrame()
    open_ns=m1.open_time.astype("int64").to_numpy(); unit=m1.open_time.dtype.unit; divisor={"ns":1,"us":1_000,"ms":1_000_000,"s":1_000_000_000}[unit]
    day_end=np.empty(len(m1),int)
    for ix in m1.groupby("trading_date",sort=False).indices.values():day_end[np.asarray(ix)]=max(ix)
    for tid,s in enumerate(signals.sort_values("signal_time").itertuples(),1):
        stamp=pd.Timestamp(s.signal_time).value//divisor; entry_i=int(np.searchsorted(open_ns,stamp,side="left"))
        if entry_i>=len(m1):continue
        signal_day=pd.Timestamp(s.signal_time).date()
        if m1.trading_date.iloc[entry_i]!=signal_day:continue
        entry=m1.open.iloc[entry_i]; d=s.direction; stop=s.stop_price; risk=d*(entry-stop)
        if risk<=0:continue
        target=entry+d*risk*(s.target_r or 2.); end_i=min(entry_i+max_hold-1,day_end[entry_i]); path=m1.iloc[entry_i:end_i+1]
        price=path.close.iloc[-1];reason="TIME";exit_i=path.index[-1]
        for i,b in path.iterrows():
            gs=b.open<=stop if d==1 else b.open>=stop; hs=b.low<=stop if d==1 else b.high>=stop; ht=b.high>=target if d==1 else b.low<=target
            if gs:price=b.open;reason="STOP_GAP";exit_i=i;break
            if hs:price=stop;reason="STOP_FIRST_TIE" if ht else "STOP";exit_i=i;break
            if ht:price=target;reason="TARGET";exit_i=i;break
        for fr,ticks in (("GROSS",0),("BASE",1),("STRESS",2)):
            net=d*((price-d*ticks*tick)-(entry+d*ticks*tick))
            rows.append({"trade_id":tid,"family":s.family,"submodel":s.submodel,"instrument":s.instrument,"signal_time":s.signal_time,"entry_time":m1.open_time.loc[entry_i],"exit_time":m1.close_time.loc[exit_i],"side":s.side,"entry_price":entry,"stop_price":stop,"target_price":target,"exit_price":price,"exit_reason":reason,"friction":fr,"pnl":net,"pnl_R":net/risk,"bars_held":list(path.index).index(exit_i)+1})
    return pd.DataFrame(rows)


def simulate_pairs(cny,si,signals,max_hold=120):
    rows=[];cu=cny.open_time.astype("int64").to_numpy();su=si.open_time.astype("int64").to_numpy();divisor={"ns":1,"us":1_000,"ms":1_000_000,"s":1_000_000_000}[cny.open_time.dtype.unit]
    for tid,s in enumerate(signals.itertuples(),1):
        stamp=pd.Timestamp(s.signal_time).value//divisor;i=int(np.searchsorted(cu,stamp));j=int(np.searchsorted(su,stamp))
        if i>=len(cny) or j>=len(si):continue
        day=cny.trading_date.iloc[i]; end=min(i+max_hold-1,i+int((cny.trading_date.iloc[i:].to_numpy()==day).sum())-1); ec,es=cny.close.iloc[end],si.close.iloc[min(j+end-i,len(si)-1)]
        for fr,t in (("GROSS",0),("BASE",1),("STRESS",2)):
            pc=s.direction_cny*(ec-cny.open.iloc[i])/cny.open.iloc[i]-2*t*TICKS["CNYRUBF"]/cny.open.iloc[i]
            ps=s.direction_si*(es-si.open.iloc[j])/si.open.iloc[j]-2*t*TICKS["USDRUBF"]/si.open.iloc[j]
            rows.append({"trade_id":tid,"family":"PAIRS","submodel":s.submodel,"instrument":"CNYRUBF+USDRUBF","signal_time":s.signal_time,"entry_time":cny.open_time.iloc[i],"exit_time":cny.close_time.iloc[end],"side":"SPREAD","friction":fr,"pnl_cny":pc,"pnl_si":ps,"pnl":pc+ps,"bars_held":end-i+1})
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
