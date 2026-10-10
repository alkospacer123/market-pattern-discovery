"""Immutable market observations and the common strategy contract."""
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class Bar:
    start: datetime
    duration: timedelta
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    problem: str = ""

    @property
    def available_at(self):
        return self.start + self.duration

    @property
    def valid(self):
        return not self.problem and self.volume > 0


@dataclass(frozen=True)
class Context:
    symbol: str
    start: datetime
    available_at: datetime
    window: tuple[datetime, datetime]
    tick: Decimal
    indicators: dict


class Strategy(Protocol):
    """Only completed observations reach strategies; no data-source handle.

    Events with base_reason=SIGNAL must contain signal_id, direction (+1/-1),
    signal_at and stop, plus target_gross_R and max_hold_calendar_minutes.
    Other events are logged strategy rejections. All execution belongs to core.
    """
    name: str

    def begin_day(self, symbol: str, day): ...
    def on_bar(self, bar: Bar | None, context: Context) -> list[dict]: ...
    def end_day(self) -> list[dict]: ...
