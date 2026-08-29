from __future__ import annotations
from typing import Any
import numpy as np
import pandas as pd
from .common import TZ, TICKS, price_to_ticks, validate_tick_grid

def canonical_trading_date(open_time: pd.Series) -> pd.Series:
    return open_time.dt.tz_convert(TZ).dt.date

def _require_times(frame: pd.DataFrame, minutes: int) -> None:
    if frame.empty: return
    if not isinstance(frame.open_time.dtype, pd.DatetimeTZDtype) or not isinstance(frame.close_time.dtype, pd.DatetimeTZDtype):
        raise ValueError("timezone-aware open_time/close_time required")
    if frame.open_time.duplicated().any() or not frame.open_time.is_monotonic_increasing:
        raise ValueError("unique ordered open_time required")
    aligned = frame.open_time.dt.floor("min" if minutes == 1 else f"{minutes}min") == frame.open_time
    if not aligned.all():
        raise ValueError(f"open_time must lie on exact {minutes}-minute grid")
    if not (frame.close_time == frame.open_time + pd.Timedelta(minutes=minutes)).all():
        raise ValueError("close_time duration invariant violation")

def prepare_m1(frame: pd.DataFrame, instrument: str) -> pd.DataFrame:
    x = frame.copy().sort_values("open_time", kind="mergesort").reset_index(drop=True)
    _require_times(x, 1); validate_tick_grid(x, instrument)
    expected = canonical_trading_date(x.open_time)
    if "trading_date" in x and not pd.Series(x.trading_date).reset_index(drop=True).equals(expected.reset_index(drop=True)):
        raise ValueError("trading_date must be Moscow calendar date by OPEN_TIME")
    x["trading_date"] = expected; x["instrument"] = instrument
    return x

def causal_m5(m1: pd.DataFrame) -> pd.DataFrame:
    if m1.empty:
        return pd.DataFrame(columns=["open_time","close_time","open","high","low","close","volume","trading_date"])
    _require_times(m1, 1)
    x = m1.sort_values("open_time", kind="mergesort").reset_index(drop=True).copy()
    if "trading_date" not in x: x["trading_date"] = canonical_trading_date(x.open_time)
    pieces=[]
    for date, day in x.groupby("trading_date", sort=False):
        day = day.set_index("open_time", drop=False)
        for start in day.open_time.dt.floor("5min").drop_duplicates():
            expected = pd.date_range(start, periods=5, freq="min")
            if not all(ts in day.index for ts in expected): continue
            g = day.loc[expected]
            if len(g) != 5: continue
            pieces.append({"open_time":start,"close_time":start+pd.Timedelta(minutes=5),"open":float(g.open.iloc[0]),"high":float(g.high.max()),"low":float(g.low.min()),"close":float(g.close.iloc[-1]),"volume":float(g.volume.sum()),"trading_date":date})
    return pd.DataFrame(pieces).sort_values("open_time",kind="mergesort").reset_index(drop=True) if pieces else pd.DataFrame(columns=["open_time","close_time","open","high","low","close","volume","trading_date"])

def indicators(m5: pd.DataFrame, slow: int = 50, bb_k: float = 2.0, rsi_n: int = 14) -> pd.DataFrame:
    x=m5.copy().reset_index(drop=True); c=x.close.astype(float)
    x["ema20"]=c.ewm(span=20,adjust=False).mean(); x["ema_slow"]=c.ewm(span=slow,adjust=False).mean()
    x["bb_mid"]=c.rolling(20,min_periods=20).mean(); sd=c.rolling(20,min_periods=20).std(ddof=0)
    x["bb_upper"]=x.bb_mid+float(bb_k)*sd; x["bb_lower"]=x.bb_mid-float(bb_k)*sd
    delta=c.diff(); gain=delta.clip(lower=0); loss=-delta.clip(upper=0)
    ag=gain.ewm(alpha=1/rsi_n,adjust=False,min_periods=rsi_n).mean(); al=loss.ewm(alpha=1/rsi_n,adjust=False,min_periods=rsi_n).mean()
    rsi=pd.Series(np.nan,index=x.index,dtype=float); both=ag.gt(0)&al.gt(0); rs=ag[both]/al[both]
    rsi.loc[both]=100-100/(1+rs); rsi.loc[ag.gt(0)&al.eq(0)]=100.; rsi.loc[ag.eq(0)&al.gt(0)]=0.; x["rsi"]=rsi
    return x

def confirmed_pivots(m5: pd.DataFrame, instrument: str) -> pd.DataFrame:
    if len(m5)<5:return pd.DataFrame()
    tick=TICKS[instrument]; h=np.array([price_to_ticks(v,tick) for v in m5.high]); l=np.array([price_to_ticks(v,tick) for v in m5.low]); rows=[]
    for j in range(2,len(m5)-2):
        known=j+2
        if h[j]>max(h[j-2:j]) and h[j]>=max(h[j+1:j+3]): rows.append({"side":"HIGH","pivot_index":j,"known_index":known,"pivot_time":m5.close_time.iloc[j],"known_time":m5.close_time.iloc[known],"price_ticks":int(h[j])})
        if l[j]<min(l[j-2:j]) and l[j]<=min(l[j+1:j+3]): rows.append({"side":"LOW","pivot_index":j,"known_index":known,"pivot_time":m5.close_time.iloc[j],"known_time":m5.close_time.iloc[known],"price_ticks":int(l[j])})
    return pd.DataFrame(rows)

def _activation_index(m5: pd.DataFrame, known_time: pd.Timestamp) -> int|None:
    ix=int(m5.open_time.searchsorted(pd.Timestamp(known_time),side="left")); return None if ix>=len(m5) else ix

def _market_dates(m5: pd.DataFrame) -> tuple[list[Any],dict[Any,int]]:
    dates=list(pd.unique(m5.trading_date)); return dates,{d:i for i,d in enumerate(dates)}
