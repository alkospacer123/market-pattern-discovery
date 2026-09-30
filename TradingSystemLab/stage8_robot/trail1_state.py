"""Broker-neutral transcription of authenticated Stage 5 TRAIL1 state transitions."""
from dataclasses import dataclass
from typing import Literal

Direction = Literal["LONG", "SHORT"]
def tighten(direction: Direction, stop: float, candidate: float) -> float:
    return max(stop, candidate) if direction == "LONG" else min(stop, candidate)

@dataclass
class Trail1State:
    direction: Direction; entry_price: float; initial_stop_price: float
    enabled: bool=True; triggered: bool=False; activated: bool=False; trigger_bar_time: str|None=None
    activation_time: str|None=None; stored_candidate: float|None=None
    candidate_already_looser: bool=False; gap_through_activated_trail: bool=False
    def __post_init__(self):
        if self.direction not in ("LONG", "SHORT"): raise ValueError("TRAIL1_DIRECTION_INVALID")
        self.initial_risk_price = self.entry_price-self.initial_stop_price if self.direction=="LONG" else self.initial_stop_price-self.entry_price
        if self.initial_risk_price <= 0: raise ValueError("TRAIL1_INITIAL_RISK_NOT_POSITIVE")
        self.trigger_price = self.entry_price + (self.initial_risk_price if self.direction=="LONG" else -self.initial_risk_price)
    def activate_before_event(self, time: str, stop: float) -> float:
        if not self.enabled or not self.triggered or self.activated or time == self.trigger_bar_time: return stop
        self.activated=True; self.activation_time=time
        return tighten(self.direction, stop, float(self.stored_candidate))
    def observe_completed_bar(self, time: str, high: float, low: float, candidate: float, stop: float) -> bool:
        if not self.enabled or self.triggered: return False
        reached = high >= self.trigger_price if self.direction=="LONG" else low <= self.trigger_price
        if reached:
            self.triggered=True; self.trigger_bar_time=time; self.stored_candidate=float(candidate)
            self.candidate_already_looser = candidate <= stop if self.direction=="LONG" else candidate >= stop
        return reached
    def candidate_after_bar(self, stop: float, candidate: float) -> float:
        return tighten(self.direction, stop, candidate) if not self.enabled or self.activated else stop
    def stop_fill(self, bar_open: float, stop: float) -> float:
        fill=min(bar_open,stop) if self.direction=="LONG" else max(bar_open,stop)
        if self.activated: self.gap_through_activated_trail = fill != stop
        return fill
