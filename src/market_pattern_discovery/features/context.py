"""Causal higher-timeframe context alignment."""
from __future__ import annotations

import pandas as pd

from market_pattern_discovery.data import timeframe


class CausalContextEngine:
    SUPPORTED = frozenset({"M15", "H1", "D1"})

    @staticmethod
    def close_times(frame: pd.DataFrame) -> pd.Series:
        if frame.empty:
            return pd.Series(index=frame.index, dtype="datetime64[ns, UTC]")
        ids = frame["timeframe"].unique()
        if len(ids) != 1:
            raise ValueError("one timeframe per frame is required")
        return frame["timestamp"] + timeframe(str(ids[0])).duration

    def align(self, observations: pd.DataFrame, context: pd.DataFrame) -> pd.DataFrame:
        if context.empty:
            raise ValueError("context cannot be empty")
        context_id = str(context["timeframe"].iloc[0])
        if context_id not in self.SUPPORTED:
            raise ValueError(f"unsupported context timeframe: {context_id}")
        left = observations.copy()
        left["observation_close_time"] = self.close_times(left)
        right = context.copy()
        right["context_close_time"] = self.close_times(right)
        payload = ["open", "high", "low", "close", "volume"]
        right = right[["context_close_time", *payload]].rename(
            columns={name: f"context_{context_id}_{name}" for name in payload})
        result = pd.merge_asof(left.sort_values("observation_close_time"),
            right.sort_values("context_close_time"), left_on="observation_close_time",
            right_on="context_close_time", direction="backward", allow_exact_matches=True)
        available = result["context_close_time"].notna()
        if not (result.loc[available, "context_close_time"] <=
                result.loc[available, "observation_close_time"]).all():
            raise AssertionError("ZERO LOOK-AHEAD violation: context was not closed")
        return result
