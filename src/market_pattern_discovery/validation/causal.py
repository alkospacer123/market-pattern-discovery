from __future__ import annotations
import pandas as pd
from .temporal import require_aware

def latest_closed_m5(m5: pd.DataFrame, decision_time: pd.Timestamp) -> pd.Series | None:
    require_aware(decision_time)
    if not m5["close_time"].is_monotonic_increasing:
        raise ValueError("higher-timeframe input must be ordered")
    available = m5.loc[m5.close_time <= decision_time]
    return None if available.empty else available.iloc[-1]

def causal_alignment(m1: pd.DataFrame, m5: pd.DataFrame) -> pd.DataFrame:
    if not m1.open_time.is_monotonic_increasing or not m5.close_time.is_monotonic_increasing:
        raise ValueError("inputs must be ordered")
    out = pd.merge_asof(m1, m5[["close_time"]].rename(columns={"close_time": "matched_m5_close"}),
                        left_on="open_time", right_on="matched_m5_close", direction="backward")
    out["causal_violation"] = out.matched_m5_close > out.open_time
    return out

