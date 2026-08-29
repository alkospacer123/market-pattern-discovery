from __future__ import annotations
import numpy as np
import pandas as pd
from .structural import finalize_signal_ids

def pair_frame(cny,si):
    cols=["open_time","close_time","open","close","trading_date"];a=cny[cols].merge(si[cols],on=["open_time","close_time"],how="inner",suffixes=("_cny","_si"))
    if a.empty:return a
    if not (a.trading_date_cny==a.trading_date_si).all():raise ValueError("pair trading_date mismatch")
    a["trading_date"]=a.trading_date_cny;return a.sort_values("open_time",kind="mergesort").reset_index(drop=True)

def pair_features(cny,si,window=480,model="DISTANCE"):
    if model not in {"DISTANCE","OLS"}:raise ValueError(f"unknown pair model: {model}")
    a=pair_frame(cny,si)
    if a.empty:return a
    lc=np.log(a.close_cny.astype(float));ls=np.log(a.close_si.astype(float))
    if model=="OLS":
        mx=ls.shift(1).rolling(window,min_periods=window).mean();my=lc.shift(1).rolling(window,min_periods=window).mean();exy=(ls*lc).shift(1).rolling(window,min_periods=window).mean();ex2=(ls*ls).shift(1).rolling(window,min_periods=window).mean();ey2=(lc*lc).shift(1).rolling(window,min_periods=window).mean();cov=exy-mx*my;varx=ex2-mx*mx;beta=cov/varx;alpha=my-beta*mx;spread=lc-alpha-beta*ls;variance=(ey2+alpha*alpha+beta*beta*ex2-2*alpha*my-2*beta*exy+2*alpha*beta*mx).clip(lower=0);sd=np.sqrt(variance*window/(window-2));mean=pd.Series(0.,index=a.index);a["alpha"]=alpha
    else:
        c=a.close_cny.astype(float);s=a.close_si.astype(float);c0=c.shift(window);s0=s.shift(window);mc=c.shift(1).rolling(window,min_periods=window).mean()/c0;ms=s.shift(1).rolling(window,min_periods=window).mean()/s0;mean=mc-ms;second=(c*c).shift(1).rolling(window,min_periods=window).sum()/(c0*c0)+(s*s).shift(1).rolling(window,min_periods=window).sum()/(s0*s0)-2*(c*s).shift(1).rolling(window,min_periods=window).sum()/(c0*s0);variance=(second-window*mean*mean)/(window-1);sd=np.sqrt(variance.clip(lower=0));spread=c/c0-s/s0;beta=pd.Series(1.,index=a.index);a["alpha"]=0.
    a["spread"]=spread;a["z"]=(spread-mean)/sd;a["beta"]=beta;return a

def pair_signals(cny,si,candidate):
    p=candidate["parameters"];model=p["model"];window=int(p["window"]);z_entry=float(p["z_entry"]);features=pair_features(cny,si,window,model);rows=[];state="UNKNOWN"
    for i,b in features.iterrows():
        z=float(b.z) if np.isfinite(b.z) else np.nan
        if not np.isfinite(z):continue
        inside=abs(z)<z_entry
        if state=="UNKNOWN":state="INSIDE" if inside else "OUTSIDE";continue
        if state=="OUTSIDE":
            if inside:state="INSIDE"
            continue
        if inside:continue
        beta=float(b.beta)
        if model=="OLS" and (not np.isfinite(beta) or beta==0):state="OUTSIDE";continue
        d_cny=-1 if z>0 else 1;d_si=-d_cny if model=="DISTANCE" else -d_cny*(1 if beta>0 else -1);wc=.5 if model=="DISTANCE" else 1/(1+abs(beta));ws=1-wc
        rows.append({"candidate_id":candidate["candidate_id"],"family":"PAIRS","submodel":model,"instrument":"CNYRUBF+USDRUBF","signal_time":b.close_time,"signal_trading_date":b.trading_date,"direction":d_cny,"side":"SPREAD","direction_cny":d_cny,"direction_si":d_si,"entry_z":z,"beta_at_entry":beta,"w_cny":wc,"w_si":ws,"feature_index":i,"window":window,"z_entry":z_entry,"stop_ticks":None,"target_r":None,"target_ticks":None});state="OUTSIDE"
    return finalize_signal_ids(pd.DataFrame(rows)),features
