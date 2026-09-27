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

    def fill(self, open_: float, stop: float) -> float:
        return min(open_, stop) if self.direction == "LONG" else max(open_, stop)
