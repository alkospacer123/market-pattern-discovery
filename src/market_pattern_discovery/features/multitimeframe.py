"""Causal native-M5 context for M1 decision rows.

M1 features describe its current closed candle, so decision time is M1
``close_time``. Only M5 rows closed by then on the same Moscow date match.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .core import _ratio

M5_CONTEXT_SOURCE_COLUMNS = (
    "candle_direction", "candle_range", "body_to_range", "close_return_5", "atr_5", "atr_20",
    "position_in_rolling_range_20", "distance_to_prior_high_20",
    "distance_to_prior_low_20", "nearest_round_level",
    "distance_to_nearest_round_level", "touches_nearest_round_level",
    "crosses_nearest_round_level", "high", "low",
)
M5_CONTEXT_FEATURES = tuple(f"m5_{name}" for name in M5_CONTEXT_SOURCE_COLUMNS)
CROSS_TIMEFRAME_FEATURES = (
    "direction_agreement_m1_m5", "m1_range_over_m5_range",
    "m1_atr5_over_m5_atr5", "m1_close_position_relative_to_m5_range",
    "distance_to_m5_high", "distance_to_m5_low",
)


def attach_m5_context(m1: pd.DataFrame, m5: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Backward as-of match without prior-day carry; unmatched rows are retained."""
    left = m1.copy(); right = m5.copy()
    left["_decision_date"] = left.open_time.dt.tz_convert("Europe/Moscow").dt.date
    right["_decision_date"] = right.open_time.dt.tz_convert("Europe/Moscow").dt.date
    payload = right[["_decision_date", "open_time", "close_time", *M5_CONTEXT_SOURCE_COLUMNS]].rename(
        columns={"open_time": "m5_source_open_time", "close_time": "m5_source_close_time",
                 **{name: f"m5_{name}" for name in M5_CONTEXT_SOURCE_COLUMNS}})
    # merge_asof requires globally ordered join keys; the date equality prevents carry.
    merged = pd.merge_asof(left.sort_values("close_time"), payload.sort_values("m5_source_close_time"),
                           left_on="close_time", right_on="m5_source_close_time",
                           by="_decision_date", direction="backward", allow_exact_matches=True)
    merged = merged.sort_values("open_time").drop(columns="_decision_date").reset_index(drop=True)
    merged["direction_agreement_m1_m5"] = (merged.candle_direction == merged.m5_candle_direction).where(merged.m5_candle_direction.notna()).astype(float)
    merged["m1_range_over_m5_range"] = _ratio(merged.candle_range, merged.m5_candle_range)
    merged["m1_atr5_over_m5_atr5"] = _ratio(merged.atr_5, merged.m5_atr_5)
    merged["m1_close_position_relative_to_m5_range"] = _ratio(merged.close-merged.m5_low, merged.m5_high-merged.m5_low)
    merged["distance_to_m5_high"] = merged.m5_high-merged.close
    merged["distance_to_m5_low"] = merged.close-merged.m5_low
    return merged, list(M5_CONTEXT_FEATURES + CROSS_TIMEFRAME_FEATURES)
