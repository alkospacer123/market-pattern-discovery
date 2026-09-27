"""Stage 5 BE1 chronological execution primitives.

This module is deliberately separate from the frozen strategies.  ``BE1State``
is the small, auditable state transition inserted into copies of the canonical
execution loops by the Stage 5 runner.  A trigger is observed only after a bar
has survived canonical exits; activation is deferred until the next bar.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

Direction = Literal["LONG", "SHORT"]
EVIDENCE_LABEL = "RETROSPECTIVE_CAUSAL_VALIDATION"
HYPOTHESIS_ID = "H4_01_PROFIT_PROTECTION_BE1"
TRIGGER_R = 1.0
TICK = 0.001


@dataclass
class BE1State:
    """Per-position state; construct a new instance for every entry/fold."""

    direction: Direction
    entry_price: float
    initial_stop_price: float
    enabled: bool = True
    triggered: bool = False
    activated: bool = False
    trigger_bar_time: Any = None
    trigger_bar_high: float | None = None
    trigger_bar_low: float | None = None
    activation_time: Any = None
    stop_before_activation: float | None = None
    stop_after_activation: float | None = None
    canonical_stop_already_tighter: bool = False
    be_stop_touched: bool = False
    gap_through_be: bool = False

    def __post_init__(self) -> None:
        risk = (self.entry_price - self.initial_stop_price if self.direction == "LONG"
                else self.initial_stop_price - self.entry_price)
        if self.direction not in ("LONG", "SHORT"):
            raise ValueError("BE1_DIRECTION_INVALID")
        if risk <= 0:
            raise ValueError("BE1_INITIAL_RISK_NOT_POSITIVE")
        self.initial_risk_price = float(risk)
        self.trigger_price = float(self.entry_price + risk if self.direction == "LONG"
                                   else self.entry_price - risk)

    def activate_before_event(self, event_time: Any, current_stop: float) -> float:
        """Activate at the first event *after* the completed trigger bar."""
        if not self.enabled or not self.triggered or self.activated:
            return current_stop
        if event_time == self.trigger_bar_time:
            return current_stop
        self.activation_time = event_time
        self.stop_before_activation = float(current_stop)
        if self.direction == "LONG":
            self.canonical_stop_already_tighter = current_stop >= self.entry_price
            result = max(float(current_stop), self.entry_price)
        else:
            self.canonical_stop_already_tighter = current_stop <= self.entry_price
            result = min(float(current_stop), self.entry_price)
        self.stop_after_activation = result
        self.activated = True
        return result

    def observe_completed_bar(self, time: Any, high: float, low: float) -> bool:
        """Observe a bar only after canonical processing completed without exit."""
        if not self.enabled or self.triggered:
            return False
        reached = high >= self.trigger_price if self.direction == "LONG" else low <= self.trigger_price
        if reached:
            self.triggered = True
            self.trigger_bar_time = time
            self.trigger_bar_high = float(high)
            self.trigger_bar_low = float(low)
        return reached

    def stop_fill(self, bar_open: float, stop: float) -> float:
        """Canonical gap-aware stop fill, while recording BE diagnostics."""
        fill = min(float(bar_open), stop) if self.direction == "LONG" else max(float(bar_open), stop)
        if self.activated:
            self.be_stop_touched = True
            self.gap_through_be = (fill < stop if self.direction == "LONG" else fill > stop)
        return fill

    def event_fields(self) -> dict[str, Any]:
        return {
            "initial_stop_price": self.initial_stop_price,
            "initial_risk_price": self.initial_risk_price,
            "trigger_price": self.trigger_price,
            "be_triggered": self.triggered,
            "trigger_bar_time": self.trigger_bar_time,
            "trigger_bar_high": self.trigger_bar_high,
            "trigger_bar_low": self.trigger_bar_low,
            "trigger_observed_after_bar_close": self.triggered,
            "be_activation_time": self.activation_time,
            "protective_stop_before_activation": self.stop_before_activation,
            "protective_stop_after_activation": self.stop_after_activation,
            "canonical_stop_already_tighter": self.canonical_stop_already_tighter,
            "be_activated": self.activated,
            "be_stop_touched": self.be_stop_touched,
            "gap_through_be": self.gap_through_be,
        }


def apply_canonical_trail(direction: Direction, protected_stop: float, candidate: float) -> float:
    """Canonical trail may tighten BE protection and can never loosen it."""
    return max(protected_stop, candidate) if direction == "LONG" else min(protected_stop, candidate)
