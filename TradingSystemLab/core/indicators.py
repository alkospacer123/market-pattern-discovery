"""Causal technical indicators (all outputs use the current or older bar)."""
from __future__ import annotations

import pandas as pd


def ema(values: pd.Series, period: int) -> pd.Series:
    return values.ewm(span=period, adjust=False, min_periods=period).mean()


def true_range(frame: pd.DataFrame) -> pd.Series:
    previous = frame["Close"].shift(1)
    return pd.concat(((frame["High"] - frame["Low"]),
                      (frame["High"] - previous).abs(),
                      (frame["Low"] - previous).abs()), axis=1).max(axis=1)


def atr(frame: pd.DataFrame, period: int = 14) -> pd.Series:
    """Wilder ATR."""
    return true_range(frame).ewm(alpha=1 / period, adjust=False,
                                 min_periods=period).mean()


def adx(frame: pd.DataFrame, period: int = 14) -> pd.Series:
    """Wilder ADX."""
    up = frame["High"].diff()
    down = -frame["Low"].diff()
    plus_dm = up.where((up > down) & (up > 0), 0.0)
    minus_dm = down.where((down > up) & (down > 0), 0.0)
    average_tr = true_range(frame).ewm(alpha=1 / period, adjust=False,
                                       min_periods=period).mean()
    plus_di = 100 * plus_dm.ewm(alpha=1 / period, adjust=False,
                                min_periods=period).mean() / average_tr
    minus_di = 100 * minus_dm.ewm(alpha=1 / period, adjust=False,
                                  min_periods=period).mean() / average_tr
    denominator = (plus_di + minus_di).replace(0, float("nan"))
    dx = 100 * (plus_di - minus_di).abs() / denominator
    return dx.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()


def ema_slope(values: pd.Series, lookback: int) -> pd.Series:
    return values - values.shift(lookback)


def bollinger_bandwidth(values: pd.Series, period: int = 20,
                        deviations: float = 2.0) -> pd.Series:
    """Bollinger bandwidth using only observations available at each close."""
    middle = values.rolling(period, min_periods=period).mean()
    deviation = values.rolling(period, min_periods=period).std(ddof=0)
    return (2.0 * deviations * deviation / middle).where(middle != 0)


def rolling_percentile_rank(values: pd.Series, window: int) -> pd.Series:
    """Causal percentile rank of the current value in its trailing window.

    Ties use the deterministic weak rank (the share of values <= current).
    The window includes the current, already-closed candle and never crosses
    the beginning of the supplied series.
    """
    return values.rolling(window, min_periods=window).apply(
        lambda sample: 100.0 * (sample <= sample[-1]).sum() / len(sample), raw=True
    )
