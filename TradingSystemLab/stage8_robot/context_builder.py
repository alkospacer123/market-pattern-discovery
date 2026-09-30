"""Causal T3 H1 execution and four-bar Moscow-local context construction."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
from TradingSystemLab.core.indicators import adx, atr, ema, ema_slope

ABS_TOL=1e-12
_REQUIRED=("Open","High","Low","Close")

class T3ContextBuilder:
    """Production adapter using the frozen research indicator definitions."""
    def build(self, h1: pd.DataFrame, now: datetime) -> tuple[pd.DataFrame,pd.DataFrame]:
        if not isinstance(h1.index,pd.DatetimeIndex) or h1.index.tz is None: raise ValueError("H1_TIMEZONE_REQUIRED")
        frame=h1.sort_index(kind="mergesort").copy()
        if frame.index.has_duplicates or not frame.index.is_monotonic_increasing: raise ValueError("DUPLICATE_OR_NON_MONOTONIC_BAR")
        frame=frame.loc[frame.index <= pd.Timestamp(now).tz_convert(frame.index.tz),list(_REQUIRED)]
        if len(frame)!=len(h1.loc[h1.index <= pd.Timestamp(now).tz_convert(h1.index.tz)]): raise ValueError("INVALID_H1_COLUMNS")
        moscow=frame.tz_convert("Europe/Moscow")
        day=pd.Series(moscow.index.date,index=moscow.index)
        ordinal=day.groupby(day).cumcount()
        block=(ordinal//4).astype(int)
        grouped=moscow.groupby([day,block],sort=True)
        complete=grouped.filter(lambda x:len(x)==4)
        if complete.empty: context=pd.DataFrame(columns=_REQUIRED,index=pd.DatetimeIndex([],tz="Europe/Moscow"))
        else:
            d=pd.Series(complete.index.date,index=complete.index); o=d.groupby(d).cumcount()//4
            context=complete.groupby([d,o],sort=True).agg(Open=("Open","first"),High=("High","max"),Low=("Low","min"),Close=("Close","last"))
            ends=complete.groupby([d,o],sort=True).apply(lambda x:x.index[-1])
            context.index=pd.DatetimeIndex(ends.tolist(),name="timestamp")
        execution=moscow.copy()
        execution["ATR"]=atr(execution,14)
        execution["PriorHigh"]=execution.High.rolling(20,min_periods=20).max().shift(1)
        execution["PriorLow"]=execution.Low.rolling(20,min_periods=20).min().shift(1)
        context["EMA100"]=ema(context.Close,100); context["EMA50"]=ema(context.Close,50); context["EMA200"]=ema(context.Close,200)
        context["EMA100Slope"]=ema_slope(context.EMA100,5); context["ADX"]=adx(context,14); context["ATR"]=atr(context,14)
        context["ATRMean20"]=context.ATR.rolling(20,min_periods=20).mean()
        return execution,context
