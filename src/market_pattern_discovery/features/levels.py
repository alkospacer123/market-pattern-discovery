"""Deterministic Decimal-based round-level context.

Half-step ties select the upper level. At each row, historical counts classify
the known candle prefix against that row's current reference level. State
resets each Moscow trading date.
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


def add_round_level_features(frame: pd.DataFrame, config: RoundLevelConfig) -> tuple[pd.DataFrame, list[str]]:
    out = frame.copy(); step = Decimal(str(config.round_level_step))
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
    exact = [(Decimal(str(lo)), Decimal(str(hi)), Decimal(str(cl)), Decimal(str(ref)))
             for lo, hi, cl, ref in zip(out.low, out.high, out.close, nearest, strict=True)]
    out["touches_nearest_round_level"] = np.fromiter((lo <= ref <= hi for lo, hi, _, ref in exact), dtype=np.int8)
    out["crosses_nearest_round_level"] = np.fromiter((lo < ref < hi for lo, hi, _, ref in exact), dtype=np.int8)
    out["closes_above_nearest_round_level"] = np.fromiter((cl > ref for _, _, cl, ref in exact), dtype=np.int8)
    out["closes_below_nearest_round_level"] = np.fromiter((cl < ref for _, _, cl, ref in exact), dtype=np.int8)
    out["penetration_distance"] = np.where(out.close >= nearest, (out.high-nearest).clip(lower=0), (nearest-out.low).clip(lower=0))
    out["rejection_distance"] = np.where(out.close >= nearest, (out.close-nearest).clip(lower=0), (nearest-out.close).clip(lower=0))
    base = list(out.columns[len(frame.columns):])
    history = ([f"touch_count_{n}" for n in STRUCTURE_WINDOWS]
               + [f"cross_count_{n}" for n in STRUCTURE_WINDOWS]
               + ["bars_since_last_touch", "bars_since_last_cross"])
    out[history] = np.nan
    # At each T, re-evaluate only already-closed candles against the current
    # reference L_T. Counts are bounded by 60 bars; per-level last-event maps
    # provide bars-since without quadratic history scans. Maps reset each day.
    for _, day in out.groupby("trading_date", sort=False):
        lows = [Decimal(str(x)) for x in day.low]
        highs = [Decimal(str(x)) for x in day.high]
        refs = [Decimal(str(x)) for x in day.nearest_round_level]
        last_touch: dict[Decimal, int] = {}
        last_cross: dict[Decimal, int] = {}
        values = {f"touch_count_{n}": np.full(len(day), np.nan) for n in STRUCTURE_WINDOWS}
        values.update({f"cross_count_{n}": np.full(len(day), np.nan) for n in STRUCTURE_WINDOWS})
        values["bars_since_last_touch"] = np.full(len(day), np.nan)
        values["bars_since_last_cross"] = np.full(len(day), np.nan)
        for pos, ref in enumerate(refs):
            start = int((lows[pos] / step).to_integral_value(rounding=ROUND_FLOOR))
            stop = int((highs[pos] / step).to_integral_value(rounding=ROUND_FLOOR))
            for multiple in range(start, stop + 1):
                level = multiple * step
                if lows[pos] <= level <= highs[pos]:
                    last_touch[level] = pos
                if lows[pos] < level < highs[pos]:
                    last_cross[level] = pos
            for n in STRUCTURE_WINDOWS:
                if pos + 1 >= n:
                    first = pos - n + 1
                    values[f"touch_count_{n}"][pos] = sum(lows[j] <= ref <= highs[j] for j in range(first, pos + 1))
                    values[f"cross_count_{n}"][pos] = sum(lows[j] < ref < highs[j] for j in range(first, pos + 1))
            if ref in last_touch: values["bars_since_last_touch"][pos] = pos-last_touch[ref]
            if ref in last_cross: values["bars_since_last_cross"][pos] = pos-last_cross[ref]
        out.loc[day.index, list(values)] = pd.DataFrame(values, index=day.index)
    return out, base + history
