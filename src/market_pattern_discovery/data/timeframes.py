"""Canonical Finam timeframe definitions.

``timestamp`` in market data is always the candle open.  A candle is
observable only at ``timestamp + duration``; D1 uses a fixed 24-hour Finam
bar duration rather than guessing an exchange session close.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True, slots=True)
class Timeframe:
    identifier: str
    duration: timedelta
    finam_period: int | str
    open_semantics: str = "timestamp is inclusive candle open (Europe/Moscow)"
    close_semantics: str = "open + duration; observable at or after close"


TIMEFRAMES = {
    name: Timeframe(name, timedelta(minutes=minutes), period)
    for name, minutes, period in (
        ("M1", 1, 1), ("M5", 5, 5), ("M15", 15, 15),
        ("M30", 30, 30), ("H1", 60, 60), ("D1", 1440, "D"),
    )
}


def timeframe(identifier: str) -> Timeframe:
    try:
        return TIMEFRAMES[identifier.upper()]
    except KeyError as exc:
        raise ValueError(f"unsupported timeframe: {identifier}") from exc
