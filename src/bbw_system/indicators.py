from __future__ import annotations
import numpy as np
import pandas as pd


def bbw(close: pd.Series, period: int = 10, deviation: float = 2.0) -> pd.DataFrame:
    middle = close.rolling(period, min_periods=period).mean()
    std = close.rolling(period, min_periods=period).std(ddof=0)
    upper, lower = middle + deviation * std, middle - deviation * std
    width = (upper - lower) / middle.replace(0, np.nan)
    return pd.DataFrame({"middle": middle, "std": std, "upper": upper, "lower": lower, "bbw": width})


def ema(close: pd.Series, period: int = 50) -> pd.Series:
    return close.ewm(span=period, adjust=False, min_periods=period).mean()


def true_range(ohlc: pd.DataFrame) -> pd.Series:
    previous = ohlc.close.shift(1)
    return pd.concat([(ohlc.high - ohlc.low), (ohlc.high - previous).abs(), (ohlc.low - previous).abs()], axis=1).max(axis=1)


def atr(ohlc: pd.DataFrame, period: int = 14) -> pd.Series:
    """Wilder ATR: SMA seed at period, then (previous*(n-1)+TR)/n."""
    tr = true_range(ohlc)
    result = pd.Series(np.nan, index=tr.index, dtype=float)
    if len(tr) >= period:
        result.iloc[period - 1] = tr.iloc[:period].mean()
        for i in range(period, len(tr)):
            result.iloc[i] = (result.iloc[i - 1] * (period - 1) + tr.iloc[i]) / period
    return result
