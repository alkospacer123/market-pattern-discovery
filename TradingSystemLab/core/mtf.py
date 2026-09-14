"""Generic causal alignment of closed higher-timeframe data to execution bars."""
from __future__ import annotations

import pandas as pd


def align_closed_context(
    execution: pd.DataFrame,
    context: pd.DataFrame,
    execution_duration: str | pd.Timedelta,
) -> pd.DataFrame:
    """Align the last context close available before each execution-bar open.

    Both inputs must be close-labelled.  A context timestamp equal to the
    execution bar's opening timestamp is available; later closes are not.
    The returned ``context_time`` makes the provenance directly auditable.
    """
    if execution.index.tz is None or context.index.tz is None:
        raise ValueError("alignment inputs must have timezone-aware close timestamps")
    if not execution.index.is_monotonic_increasing or not context.index.is_monotonic_increasing:
        raise ValueError("alignment inputs must be sorted")
    duration = pd.Timedelta(execution_duration)
    if duration <= pd.Timedelta(0):
        raise ValueError("execution_duration must be positive")
    left = execution.copy()
    left["__bar_open"] = left.index - duration
    right = context.copy()
    right["context_time"] = right.index
    aligned = pd.merge_asof(
        left.reset_index(), right.reset_index(drop=True), left_on="__bar_open",
        right_on="context_time", direction="backward", allow_exact_matches=True,
        suffixes=("", "_context"),
    ).set_index(execution.index)
    aligned.index.name = execution.index.name
    return aligned.drop(columns=["__bar_open"])
