"""Deterministic Decimal-based round-level context.

Half-step ties select the upper level. Historical counts count each candle's
own contemporaneous nearest-level interaction, never today's level projected
backward. State resets each Moscow trading date.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_FLOOR
import numpy as np
import pandas as pd

from .core import _ratio
from .schema import RoundLevelConfig, STRUCTURE_WINDOWS


def _grid(price: float, step: Decimal) -> tuple[float, float, float]:
    p = Decimal(str(price)); q = (p / step).to_integral_value(rounding=ROUND_FLOOR)
    below, above = q * step, (q + 1) * step
    nearest = above if p - below >= above - p else below
    return float(below), float(above), float(nearest)


def _since(mask: pd.Series) -> pd.Series:
    last = -1; result = []
    for i, flag in enumerate(mask.to_numpy()):
        if flag: last = i
        result.append(np.nan if last < 0 else i-last)
    return pd.Series(result, index=mask.index)


def add_round_level_features(frame: pd.DataFrame, config: RoundLevelConfig) -> tuple[pd.DataFrame, list[str]]:
    out = frame.copy(); step = Decimal(config.step); tol = float(Decimal(config.touch_tolerance))
    grids = [_grid(p, step) for p in out.close]
    below = pd.Series([x[0] for x in grids], index=out.index)
    above = pd.Series([x[1] for x in grids], index=out.index)
    nearest = pd.Series([x[2] for x in grids], index=out.index)
    out["nearest_round_level"] = nearest; out["round_level_below"] = below; out["round_level_above"] = above
    out["distance_to_nearest_round_level"] = (out.close-nearest).abs()
    out["distance_to_round_level_below"] = out.close-below
    out["distance_to_round_level_above"] = above-out.close
    out["signed_distance_to_nearest_round_level"] = out.close-nearest
    out["position_between_round_levels"] = _ratio(out.close-below, above-below)
    out["distance_to_nearest_round_level_in_steps"] = out.distance_to_nearest_round_level / float(step)
    out["distance_to_nearest_round_level_over_atr_20"] = _ratio(out.distance_to_nearest_round_level, out.atr_20)
    out["touches_nearest_round_level"] = ((out.low-tol <= nearest) & (out.high+tol >= nearest)).astype(np.int8)
    out["crosses_nearest_round_level"] = ((out.low < nearest-tol) & (out.high > nearest+tol)).astype(np.int8)
    out["closes_above_nearest_round_level"] = (out.close > nearest+tol).astype(np.int8)
    out["closes_below_nearest_round_level"] = (out.close < nearest-tol).astype(np.int8)
    out["penetration_distance"] = np.where(out.close >= nearest, (out.high-nearest).clip(lower=0), (nearest-out.low).clip(lower=0))
    out["rejection_distance"] = np.where(out.close >= nearest, (out.close-nearest).clip(lower=0), (nearest-out.close).clip(lower=0))
    base = list(out.columns[len(frame.columns):])
    for _, day in out.groupby("trading_date", sort=False):
        for n in STRUCTURE_WINDOWS:
            out.loc[day.index, f"touch_count_{n}"] = day.touches_nearest_round_level.rolling(n, min_periods=n).sum()
            out.loc[day.index, f"cross_count_{n}"] = day.crosses_nearest_round_level.rolling(n, min_periods=n).sum()
        out.loc[day.index, "bars_since_last_touch"] = _since(day.touches_nearest_round_level.astype(bool))
        out.loc[day.index, "bars_since_last_cross"] = _since(day.crosses_nearest_round_level.astype(bool))
    return out, base + [f"touch_count_{n}" for n in STRUCTURE_WINDOWS] + [f"cross_count_{n}" for n in STRUCTURE_WINDOWS] + ["bars_since_last_touch", "bars_since_last_cross"]
