"""Past-only, Moscow-day-reset market structure descriptors.

``rolling_*`` includes the current closed candle. ``prior_*`` excludes it.
All windows are fixed research scales and use complete windows.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .core import _ratio
from .schema import STRUCTURE_WINDOWS


def _bars_since(mask: pd.Series) -> pd.Series:
    last = -1
    values = []
    for i, flag in enumerate(mask.fillna(False).to_numpy()):
        if flag:
            last = i
        values.append(np.nan if last < 0 else i - last)
    return pd.Series(values, index=mask.index)


def add_structure_features(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    out = frame.copy()
    added: list[str] = []
    pieces = []
    for _, day in out.groupby("trading_date", sort=False):
        cols = {}
        for n in STRUCTURE_WINDOWS:
            high = day.high.rolling(n, min_periods=n).max()
            low = day.low.rolling(n, min_periods=n).min()
            prior_high = day.high.shift(1).rolling(n, min_periods=n).max()
            prior_low = day.low.shift(1).rolling(n, min_periods=n).min()
            rng = high - low
            midpoint = (high + low) / 2
            values = {
                f"rolling_high_{n}": high, f"rolling_low_{n}": low, f"rolling_range_{n}": rng,
                f"distance_to_rolling_high_{n}": high-day.close,
                f"distance_to_rolling_low_{n}": day.close-low,
                f"position_in_rolling_range_{n}": _ratio(day.close-low, rng),
                f"prior_high_{n}": prior_high, f"prior_low_{n}": prior_low,
                f"distance_to_prior_high_{n}": prior_high-day.close,
                f"distance_to_prior_low_{n}": day.close-prior_low,
                f"break_above_prior_high_{n}": (day.close > prior_high).where(prior_high.notna()).astype(float),
                f"break_below_prior_low_{n}": (day.close < prior_low).where(prior_low.notna()).astype(float),
                f"new_high_{n}": day.high.eq(high).where(high.notna()).astype(float),
                f"new_low_{n}": day.low.eq(low).where(low.notna()).astype(float),
            }
            # Direction/event extras are intentionally limited to the canonical
            # 20-bar scale to control multiple-testing and feature explosion.
            if n == 20:
                values.update({
                    "bars_since_new_high_20": _bars_since(day.high.eq(high) & high.notna()),
                    "bars_since_new_low_20": _bars_since(day.low.eq(low) & low.notna()),
                    "rolling_high_change_20": high.diff(), "rolling_low_change_20": low.diff(),
                    "rolling_range_change_20": rng.diff(),
                    "distance_from_range_midpoint_20": day.close-midpoint,
                    "normalized_distance_from_midpoint_20": _ratio(day.close-midpoint, rng),
                })
            cols.update(values)
        pieces.append(pd.DataFrame(cols, index=day.index))
    calculated = pd.concat(pieces).sort_index()
    added = list(calculated.columns)
    return pd.concat([out, calculated], axis=1), added
