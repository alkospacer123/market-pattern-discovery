"""Independent BE1 contract auditor (does not import producer modules)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass
class IndependentBE1:
    direction: Literal["LONG", "SHORT"]
    entry: float
    initial_stop: float
    triggered: bool = False
    activated: bool = False
    trigger_time: object = None
    be_level_touched: bool = False
    protective_stop_touched_after_be: bool = False
    gap_through_be_level: bool = False
    exit_protection_source: str = "CANONICAL"

    def __post_init__(self) -> None:
        self.risk = self.entry - self.initial_stop if self.direction == "LONG" else self.initial_stop - self.entry
        if self.risk <= 0:
            raise ValueError("BE1_INITIAL_RISK_NOT_POSITIVE")
        self.level = self.entry + self.risk if self.direction == "LONG" else self.entry - self.risk

    def observe(self, time: object, high: float, low: float) -> None:
        if not self.triggered and (high >= self.level if self.direction == "LONG" else low <= self.level):
            self.triggered, self.trigger_time = True, time

    def activate(self, time: object, stop: float) -> float:
        if not self.triggered or self.activated or time == self.trigger_time:
            return stop
        self.activated = True
        return max(stop, self.entry) if self.direction == "LONG" else min(stop, self.entry)

    def fill(self, open_: float, stop: float, *, low: float | None = None,
             high: float | None = None) -> float:
        result = min(open_, stop) if self.direction == "LONG" else max(open_, stop)
        if self.activated:
            self.protective_stop_touched_after_be = True
            at_be = abs(stop - self.entry) <= 1e-12
            self.be_level_touched = (low <= self.entry if self.direction == "LONG" and low is not None
                                     else high >= self.entry if self.direction == "SHORT" and high is not None
                                     else at_be)
            self.gap_through_be_level = (result < self.entry if self.direction == "LONG"
                                         else result > self.entry)
            if at_be:
                self.exit_protection_source = "BE_LEVEL"
            elif stop > self.entry if self.direction == "LONG" else stop < self.entry:
                self.exit_protection_source = "CANONICAL_TRAIL_AFTER_BE"
            else:
                self.exit_protection_source = "OTHER_CANONICAL_PROTECTIVE_EXIT"
        return result
