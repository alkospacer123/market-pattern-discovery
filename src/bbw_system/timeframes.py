from __future__ import annotations

from datetime import time
import pandas as pd

from .config import SessionConfig
from .market import filter_session, trading_date


def synthetic_bars(h1: pd.DataFrame, hours: int, session: SessionConfig, incomplete: str = "drop") -> pd.DataFrame:
    """Aggregate closed input bars into anchor-aligned, complete N-hour bars."""
    if incomplete not in {"drop", "mark"}:
        raise ValueError("incomplete must be 'drop' or 'mark'")
    data = filter_session(h1, session).copy()
    anchor = time.fromisoformat(session.session_anchor)
    anchor_minutes = anchor.hour * 60 + anchor.minute
    local_minutes = data.index.hour * 60 + data.index.minute
    elapsed = (local_minutes - anchor_minutes) % (24 * 60)
    data["_bucket"] = [pd.Timestamp.combine(trading_date(ts, session), anchor).tz_localize(ts.tz) + pd.Timedelta(hours=int(e // (hours * 60)) * hours) for ts, e in zip(data.index, elapsed)]
    grouped = data.groupby("_bucket", sort=True)
    result = grouped.agg(open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"), volume=("volume", "sum"))
    result["source_bars"] = grouped.size()
    result["complete"] = result.source_bars.eq(hours)
    result.index.name = "datetime"
    return result.loc[result.complete].copy() if incomplete == "drop" else result
