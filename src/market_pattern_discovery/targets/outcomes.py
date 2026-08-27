"""Canonical Phase 3A future market-path outcomes.

This is intentionally a forward-looking *target-side* module.  A decision is
made at the current candle's close and offset one always denotes the next
candle.  Complete horizons neither cross a Moscow date nor skip an expected
timeframe candle.  The signed excursion formulas are not clipped: a negative
value preserves the fact that the complete future path stayed on the other
side of the reference close.  Directional names describe viewpoints only;
they are not trades or labels.
"""
from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

HORIZONS: dict[str, tuple[int, ...]] = {
    "M1": (1, 3, 5, 10, 15, 30, 60),
    "M5": (1, 3, 6, 12),
}
_MINUTES = {"M1": 1, "M5": 5}
_IDENTITY = ("instrument", "timeframe", "open_time", "close_time", "decision_time")
_METRICS = (
    "future_close", "future_delta", "future_return", "future_max_high",
    "future_min_low", "long_mfe", "long_mae", "long_mfe_return",
    "long_mae_return", "short_mfe", "short_mae", "short_mfe_return",
    "short_mae_return", "future_range", "future_range_return",
    "close_location_in_future_range", "bars_to_future_high",
    "bars_to_future_low", "future_high_before_low",
)


def outcome_columns(timeframe: str) -> list[str]:
    """Return the exact ordered canonical v1 target columns."""
    _require_timeframe(timeframe)
    columns = ["target_reference_close"]
    for horizon in HORIZONS[timeframe]:
        columns.extend((f"target_future_valid_{horizon}", f"target_future_invalid_reason_{horizon}"))
        columns.extend(f"target_{metric}_{horizon}" for metric in _METRICS)
    return columns


def _require_timeframe(timeframe: str) -> None:
    if timeframe not in HORIZONS:
        raise ValueError(f"unsupported timeframe {timeframe!r}; canonical v1 supports M1 and M5")


def _validate(frame: pd.DataFrame) -> str:
    required = {"instrument", "timeframe", "open_time", "close_time", "open", "high", "low", "close"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"missing required columns: {missing}")
    if frame.empty:
        raise ValueError("outcome input must not be empty")
    if frame["instrument"].nunique(dropna=False) != 1:
        raise ValueError("outcome input contains mixed instruments")
    if frame["timeframe"].nunique(dropna=False) != 1:
        raise ValueError("outcome input contains mixed timeframes")
    timeframe = str(frame["timeframe"].iloc[0])
    _require_timeframe(timeframe)
    opened = frame["open_time"]
    if not isinstance(opened.dtype, pd.DatetimeTZDtype):
        raise ValueError("open_time must be timezone-aware")
    if not opened.is_monotonic_increasing:
        raise ValueError("open_time must be strictly sorted")
    if opened.duplicated().any():
        raise ValueError("duplicate open_time values are forbidden")
    prices = frame[["open", "high", "low", "close"]].to_numpy(dtype=float)
    if not np.isfinite(prices).all():
        raise ValueError("OHLC values must be finite")
    if (prices <= 0).any():
        raise ValueError("OHLC values must be positive")
    op, hi, lo, cl = prices.T
    if (hi < np.maximum.reduce((op, lo, cl))).any() or (lo > np.minimum.reduce((op, hi, cl))).any():
        raise ValueError("invalid OHLC relationships")
    expected_close = opened + pd.Timedelta(minutes=_MINUTES[timeframe])
    if not frame["close_time"].reset_index(drop=True).equals(expected_close.reset_index(drop=True)):
        raise ValueError("close_time does not equal open_time plus timeframe duration")
    return timeframe


def _future_matrix(values: np.ndarray, horizon: int) -> np.ndarray:
    """Rows contain offsets t+1..t+h; unavailable offsets are NaN."""
    n = len(values)
    result = np.full((n, horizon), np.nan, dtype=float)
    for offset in range(1, horizon + 1):
        if offset >= n:
            break
        result[: n - offset, offset - 1] = values[offset:]
    return result


def build_outcomes(frame: pd.DataFrame) -> pd.DataFrame:
    """Build the fixed v1 outcome grid, exactly one output row per candle.

    Invalid reason precedence is ``data_end``, then ``day_end``, then ``gap``.
    Thus every invalid horizon belongs to exactly one validator count.
    """
    timeframe = _validate(frame)
    source = frame.reset_index(drop=True)
    n = len(source)
    minutes = _MINUTES[timeframe]
    opened = source["open_time"]
    dates = opened.dt.tz_convert("Europe/Moscow").dt.date.to_numpy()
    reference = source["close"].to_numpy(dtype=float)
    highs = source["high"].to_numpy(dtype=float)
    lows = source["low"].to_numpy(dtype=float)
    closes = source["close"].to_numpy(dtype=float)

    identity = source[["instrument", "timeframe", "open_time", "close_time"]].copy()
    identity["decision_time"] = identity["close_time"]
    target_data: dict[str, Sequence] = {"target_reference_close": reference}
    row = np.arange(n)
    for horizon in HORIZONS[timeframe]:
        enough = row + horizon < n
        last = np.minimum(row + horizon, n - 1)
        same_day = enough & (dates[last] == dates)
        elapsed = opened.shift(-horizon) - opened
        contiguous = enough & elapsed.eq(pd.Timedelta(minutes=horizon * minutes)).to_numpy()
        valid = same_day & contiguous
        reason = np.full(n, "", dtype=object)
        reason[~enough] = "data_end"
        reason[enough & ~same_day] = "day_end"
        reason[enough & same_day & ~contiguous] = "gap"

        high_path = _future_matrix(highs, horizon)
        low_path = _future_matrix(lows, horizon)
        future_high = np.max(high_path, axis=1)
        future_low = np.min(low_path, axis=1)
        future_close = np.full(n, np.nan)
        future_close[enough] = closes[row[enough] + horizon]
        high_bar = np.argmax(high_path, axis=1).astype(float) + 1
        low_bar = np.argmin(low_path, axis=1).astype(float) + 1
        path_range = future_high - future_low

        values: dict[str, np.ndarray] = {
            "future_close": future_close,
            "future_delta": future_close - reference,
            "future_return": future_close / reference - 1,
            "future_max_high": future_high,
            "future_min_low": future_low,
            "long_mfe": future_high - reference,
            "long_mae": reference - future_low,
            "long_mfe_return": future_high / reference - 1,
            "long_mae_return": 1 - future_low / reference,
            "short_mfe": reference - future_low,
            "short_mae": future_high - reference,
            "short_mfe_return": 1 - future_low / reference,
            "short_mae_return": future_high / reference - 1,
            "future_range": path_range,
            "future_range_return": path_range / reference,
            "close_location_in_future_range": np.divide(
                future_close - future_low, path_range,
                out=np.full(n, np.nan), where=path_range != 0,
            ),
            "bars_to_future_high": high_bar,
            "bars_to_future_low": low_bar,
            "future_high_before_low": np.where(high_bar < low_bar, 1.0, np.where(low_bar < high_bar, 0.0, np.nan)),
        }
        target_data[f"target_future_valid_{horizon}"] = valid
        target_data[f"target_future_invalid_reason_{horizon}"] = pd.array(reason, dtype="string")
        for metric in _METRICS:
            value = values[metric]
            value[~valid] = np.nan
            target_data[f"target_{metric}_{horizon}"] = value
    output = pd.concat([identity, pd.DataFrame(target_data)], axis=1)
    if np.isinf(output.select_dtypes(include=[np.number]).to_numpy()).any():
        raise RuntimeError("outcome engine produced infinity")
    return output[[*_IDENTITY, *outcome_columns(timeframe)]]
