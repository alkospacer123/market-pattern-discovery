"""Append-only, H1-pattern M15 close-labelled history guard.

The signal engine needs the full pinned historical indicator context:
FINAM REST exposes only 30 days of M15 data. Recalculating EMA75, H1 EMA75
and recursive ATR/ADX from an arbitrary last-30-day slice is NOT equivalent
to selected #518 research. Existing protected bars are never changed.

This function is OFFLINE and requires a separate authenticated seed, a raw
FINAM read-only bridge and exact overlapping terminal bar to prevent stitching
unrelated or shifted data. No network, broker or SQLite involved.
"""
from __future__ import annotations

from datetime import datetime
import math

import pandas as pd

COLS = ("Open", "High", "Low", "Close", "Volume")


class M15HistoryContinuityError(ValueError):
    pass


def _check(frame: pd.DataFrame, name: str) -> None:
    if not isinstance(frame, pd.DataFrame):
        raise M15HistoryContinuityError(f"{name}_TYPE_INVALID")
    if not isinstance(frame.index, pd.DatetimeIndex) or frame.index.tz is None:
        raise M15HistoryContinuityError(f"{name}_TIMEZONE_REQUIRED")
    if str(frame.index.tz) != "Europe/Moscow":
        raise M15HistoryContinuityError(f"{name}_MUST_HAVE_MSK_CLOSE_LABELS")
    if frame.empty or tuple(frame.columns) != COLS:
        raise M15HistoryContinuityError(f"{name}_OHLCV_SCHEMA_INVALID")
    if not frame.index.is_monotonic_increasing or frame.index.has_duplicates:
        raise M15HistoryContinuityError(f"{name}_DUPLICATE_OR_NONMONOTONIC")
    import numpy as np
    values = frame.to_numpy(dtype=float)
    if not bool(np.isfinite(values).all()):
        raise M15HistoryContinuityError(f"{name}_NONFINITE")
    if (values[:, :4] <= 0).any() or (values[:, 4] < 0).any():
        raise M15HistoryContinuityError(f"{name}_VALUES_INVALID")
    for index in frame.index:
        if index.minute % 15 or index.second or index.microsecond:
            raise M15HistoryContinuityError(f"{name}_CLOSE_GRID_INVALID")


def immutable_prefix_splice(seed: pd.DataFrame, newer: pd.DataFrame) -> pd.DataFrame:
    """Extend a pinned M15 frame only when its final candle overlaps identically.

    The read-only seed MUST already be independently authenticated against
    frozen research provenance; this function only enforces the invariant.
    It cannot bootstrap a new series or fill missing broker data gaps.
    Returns a NEW frame; no caller-provided DataFrame is mutated.
    """
    _check(seed, "SEED")
    _check(newer, "BROKER")
    if seed.index[-1] not in newer.index:
        raise M15HistoryContinuityError("M15_IMMUTABLE_TERMINAL_SEAM_MISSING")
    overlap = seed.index.intersection(newer.index)
    if overlap.empty:
        raise M15HistoryContinuityError("M15_OVERLAP_REQUIRED")
    old = seed.loc[overlap, COLS].to_numpy(dtype=float)
    current = newer.loc[overlap, COLS].to_numpy(dtype=float)
    import numpy as np
    if not bool(np.array_equal(old, current)):
        raise M15HistoryContinuityError("M15_IMMUTABLE_HISTORY_CHANGED")
    tail = newer.loc[newer.index > seed.index[-1], COLS]
    result = pd.concat([seed, tail], axis=0)
    if result.index.has_duplicates or not result.index.is_monotonic_increasing:
        raise M15HistoryContinuityError("M15_SPLICE_ORDER_INVALID")
    return result
