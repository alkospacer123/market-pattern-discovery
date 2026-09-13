from __future__ import annotations

from datetime import time
import pandas as pd

from .config import SessionConfig
from .market import filter_session, trading_date


def synthetic_bars(h1: pd.DataFrame, hours: int, session: SessionConfig,
                   completion_policy: str = "strict_source_count") -> pd.DataFrame:
    """Aggregate H1 bars into causal, anchor-aligned setup bars.

    ``session_end_valid`` accepts a short final bucket only when every H1 slot
    expected by the configured session is present.  It therefore does not turn
    a data gap or a live, unfinished bucket into a completed candle.
    """
    aliases = {"drop": "strict_source_count", "mark": "mark"}
    completion_policy = aliases.get(completion_policy, completion_policy)
    if completion_policy not in {"strict_source_count", "session_end_valid", "mark"}:
        raise ValueError("unknown setup-bar completion policy")
    data = filter_session(h1, session).copy()
    anchor = time.fromisoformat(session.session_anchor)
    anchor_minutes = anchor.hour * 60 + anchor.minute
    local_minutes = data.index.hour * 60 + data.index.minute
    elapsed = (local_minutes - anchor_minutes) % (24 * 60)
    data["_bucket"] = [pd.Timestamp.combine(trading_date(ts, session), anchor).tz_localize(ts.tz) + pd.Timedelta(hours=int(e // (hours * 60)) * hours) for ts, e in zip(data.index, elapsed)]
    grouped = data.groupby("_bucket", sort=True)
    result = grouped.agg(open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"), volume=("volume", "sum"))
    result["source_bars"] = grouped.size()
    result["trading_date"] = [trading_date(ts, session) for ts in result.index]
    strict = result.source_bars.eq(hours)
    if completion_policy == "session_end_valid":
        # Count configured hourly opens in each bucket. Missing source rows do
        # not reduce this expectation, so gaps cannot masquerade as completion.
        expected = []
        for bucket in result.index:
            candidates = pd.date_range(bucket, periods=hours, freq="h")
            expected.append(sum(filter_session(pd.DataFrame(index=candidates), session).index.map(
                lambda ts: trading_date(ts, session) == trading_date(bucket, session))))
        result["complete"] = result.source_bars.eq(expected) & pd.Series(expected, index=result.index).gt(0)
    else:
        result["complete"] = strict
    result.index.name = "datetime"
    return result if completion_policy == "mark" else result.loc[result.complete].copy()
