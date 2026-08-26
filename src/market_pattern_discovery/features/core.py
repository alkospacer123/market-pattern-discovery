"""Transparent causal features computed from current and earlier closed candles only."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .schema import CORE_FEATURE_BUILDER_VERSION, CoreFeatureConfig

REQUIRED = ("open", "high", "low", "close", "volume", "instrument", "timeframe", "open_time", "close_time")


class FeatureInputError(ValueError):
    """Input is not a validated, ordered causal candle frame."""


@dataclass(frozen=True)
class FeatureBuildResult:
    frame: pd.DataFrame
    metadata: dict


def _ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """Divide only by finite, non-zero denominators; undefined ratios are NaN."""
    result = numerator.div(denominator.where(denominator.ne(0)))
    return result.where(np.isfinite(result))


def _streak(values: pd.Series, wanted: int) -> pd.Series:
    out = np.zeros(len(values), dtype=np.int64)
    run = 0
    for position, value in enumerate(values.to_numpy()):
        run = run + 1 if value == wanted else 0
        out[position] = run
    return pd.Series(out, index=values.index)


def _validate(frame: pd.DataFrame, timeframe: str) -> None:
    missing = [column for column in REQUIRED if column not in frame]
    if missing:
        raise FeatureInputError(f"missing required columns: {missing}")
    if timeframe not in {"M1", "M5"} or frame.empty:
        raise FeatureInputError("timeframe must be M1 or M5 and input must be non-empty")
    if frame.instrument.nunique(dropna=False) != 1 or frame.timeframe.nunique(dropna=False) != 1:
        raise FeatureInputError("input must contain one instrument and one timeframe")
    if frame.timeframe.iloc[0] != timeframe:
        raise FeatureInputError("timeframe argument does not match input")
    if not isinstance(frame.open_time.dtype, pd.DatetimeTZDtype) or not isinstance(frame.close_time.dtype, pd.DatetimeTZDtype):
        raise FeatureInputError("open_time and close_time must be timezone-aware")
    if not frame.open_time.is_monotonic_increasing or frame.open_time.duplicated().any():
        raise FeatureInputError("candles must be uniquely and chronologically ordered")
    minutes = 1 if timeframe == "M1" else 5
    if not (frame.close_time == frame.open_time + pd.Timedelta(minutes=minutes)).all():
        raise FeatureInputError("close_time does not match candle decision-time semantics")
    numeric = frame[["open", "high", "low", "close", "volume"]]
    if not all(pd.api.types.is_numeric_dtype(dtype) for dtype in numeric.dtypes):
        raise FeatureInputError("OHLCV columns must be numeric")
    if not np.isfinite(numeric.to_numpy(dtype=float)).all():
        raise FeatureInputError("OHLCV must be finite")
    if (numeric[["open", "high", "low", "close"]] <= 0).any().any() or (numeric.volume < 0).any():
        raise FeatureInputError("prices must be positive and volume non-negative")
    if ((frame.high < frame[["open", "close", "low"]].max(axis=1)) | (frame.low > frame[["open", "close", "high"]].min(axis=1))).any():
        raise FeatureInputError("OHLC invariant violation")


def build_core_features(frame: pd.DataFrame, *, timeframe: str,
                        config: CoreFeatureConfig | None = None) -> FeatureBuildResult:
    """Build one deterministic row per closed candle, resetting all state at Moscow midnight.

    Rolling statistics use complete windows (``min_periods=window``). Ratios with
    zero denominators and logarithms of invalid ratios are represented by NaN.
    """
    cfg = config or CoreFeatureConfig()
    _validate(frame, timeframe)
    out = frame.copy(deep=True).reset_index(drop=True)
    local_open = out.open_time.dt.tz_convert("Europe/Moscow")
    out["trading_date"] = local_open.dt.date
    groups = out.groupby("trading_date", sort=False, observed=True)

    # Geometry and time are known at the candle's close/decision time.
    out["candle_range"] = out.high - out.low
    out["signed_body"] = out.close - out.open
    out["abs_body"] = out.signed_body.abs()
    out["upper_wick"] = out.high - out[["open", "close"]].max(axis=1)
    out["lower_wick"] = out[["open", "close"]].min(axis=1) - out.low
    for name, numerator in (("body_to_range", out.abs_body), ("upper_wick_to_range", out.upper_wick),
                            ("lower_wick_to_range", out.lower_wick),
                            ("close_position_in_range", out.close - out.low),
                            ("open_position_in_range", out.open - out.low)):
        out[name] = _ratio(numerator, out.candle_range)
    out["candle_direction"] = np.sign(out.signed_body).astype(np.int8)
    out["open_to_close_return"] = _ratio(out.signed_body, out.open)
    out["high_to_close_distance"] = out.high - out.close
    out["low_to_close_distance"] = out.close - out.low
    out["local_hour"] = local_open.dt.hour.astype(np.int8)
    out["local_minute"] = local_open.dt.minute.astype(np.int8)
    out["minute_of_day"] = (out.local_hour.astype(int) * 60 + out.local_minute).astype(np.int16)
    out["weekday"] = local_open.dt.dayofweek.astype(np.int8)
    first_minutes = groups["minute_of_day"].transform("first")
    out["minutes_since_first_available_candle_of_day"] = out.minute_of_day - first_minutes

    pieces: list[pd.DataFrame] = []
    for _, day in groups:
        columns: dict[str, pd.Series] = {}
        close = day.close
        one_return = close.pct_change(fill_method=None)
        abs_move = close.diff().abs()
        direction = day.candle_direction
        previous_close = close.shift(1)
        columns["true_range"] = pd.concat([
            day.candle_range, (day.high - previous_close).abs(), (day.low - previous_close).abs()
        ], axis=1).max(axis=1)
        columns["consecutive_up_candles"] = _streak(direction, 1)
        columns["consecutive_down_candles"] = _streak(direction, -1)
        for window in cfg.general_windows:
            lag = close.shift(window)
            columns[f"close_delta_{window}"] = close - lag
            columns[f"close_return_{window}"] = _ratio(close - lag, lag)
            ratio = _ratio(close, lag)
            columns[f"log_return_{window}"] = np.log(ratio.where(ratio.gt(0)))
            columns[f"net_price_movement_{window}"] = close - lag
            cumulative = abs_move.rolling(window, min_periods=window).sum()
            columns[f"cumulative_absolute_movement_{window}"] = cumulative
            columns[f"directional_efficiency_{window}"] = _ratio((close - lag).abs(), cumulative)
            rolling_direction = direction.rolling(window, min_periods=window)
            columns[f"fraction_up_bars_{window}"] = direction.eq(1).rolling(window, min_periods=window).mean()
            columns[f"fraction_down_bars_{window}"] = direction.eq(-1).rolling(window, min_periods=window).mean()
            columns[f"signed_direction_balance_{window}"] = rolling_direction.mean()
        for window in cfg.rolling_windows:
            columns[f"atr_{window}"] = columns["true_range"].rolling(window, min_periods=window).mean()
            ranges = day.candle_range.rolling(window, min_periods=window)
            columns[f"mean_range_{window}"] = ranges.mean()
            columns[f"median_range_{window}"] = ranges.median()
            columns[f"range_std_{window}"] = ranges.std()
            returns = one_return.rolling(window, min_periods=window)
            columns[f"return_std_{window}"] = returns.std()
            columns[f"mean_abs_return_{window}"] = one_return.abs().rolling(window, min_periods=window).mean()
            columns[f"candle_range_over_atr_{window}"] = _ratio(day.candle_range, columns[f"atr_{window}"])
            columns[f"abs_body_over_atr_{window}"] = _ratio(day.abs_body, columns[f"atr_{window}"])
            volume = day.volume.rolling(window, min_periods=window)
            columns[f"volume_mean_{window}"] = volume.mean()
            columns[f"volume_median_{window}"] = volume.median()
            columns[f"relative_volume_{window}"] = _ratio(day.volume, columns[f"volume_mean_{window}"])
            columns[f"volume_change_{window}"] = day.volume - day.volume.shift(window)
            if window in (20, 60):
                columns[f"volume_zscore_{window}"] = _ratio(day.volume - volume.mean(), volume.std())
        columns["atr_5_over_atr_20"] = _ratio(columns["atr_5"], columns["atr_20"])
        columns["atr_10_over_atr_60"] = _ratio(columns["atr_10"], columns["atr_60"])
        columns["mean_range_5_over_mean_range_20"] = _ratio(columns["mean_range_5"], columns["mean_range_20"])
        columns["mean_range_10_over_mean_range_60"] = _ratio(columns["mean_range_10"], columns["mean_range_60"])
        pieces.append(pd.DataFrame(columns, index=day.index))
    calculated = pd.concat(pieces).sort_index()
    out = pd.concat([out, calculated], axis=1)
    numeric = out.select_dtypes(include=[np.number])
    if np.isinf(numeric.to_numpy(dtype=float)).any():
        raise ArithmeticError("feature output contains infinity")
    feature_names = [column for column in out.columns if column not in frame.columns]
    warmup = {str(window): int(out[f"atr_{window}"].isna().sum()) for window in cfg.rolling_windows}
    metadata = {"feature_builder_version": CORE_FEATURE_BUILDER_VERSION,
                "instrument": str(out.instrument.iloc[0]), "timeframe": timeframe,
                "input_rows": len(frame), "output_rows": len(out), "feature_names": feature_names,
                "configured_windows": {"general": list(cfg.general_windows), "rolling": list(cfg.rolling_windows)},
                "warmup": {"atr_nan_rows": warmup, "rows_are_preserved": True}}
    return FeatureBuildResult(out, metadata)
