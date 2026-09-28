"""Pure causal accounting primitives for H4_03_TOTAL_OPEN_RISK_CAP."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

CAP_R = 1.0
TICK_SIZE = 0.001
EPSILON = 1e-12
Direction = Literal["LONG", "SHORT"]


@dataclass
class OpenRisk:
    direction: Direction
    entry_price: float
    initial_stop: float
    active_stop: float
    assigned_risk_R: float

    @property
    def initial_risk_price(self) -> float:
        value = (self.entry_price - self.initial_stop if self.direction == "LONG"
                 else self.initial_stop - self.entry_price)
        if value <= 0:
            raise ValueError("INITIAL_RISK_NOT_POSITIVE")
        return value

    def remaining_R(self) -> float:
        distance = (self.entry_price - self.active_stop if self.direction == "LONG"
                    else self.active_stop - self.entry_price)
        return self.assigned_risk_R * max(0.0, distance / self.initial_risk_price)


def signal_priority(strategy: str, timeframe: str, instrument: str) -> tuple[int, int, str]:
    """Frozen admission order; deliberately independent of input order/performance."""
    return ({"T2": 0, "T3": 1}[strategy], {"M30": 0, "H1": 1}[timeframe], instrument)


def allocation(open_risk_R: float, enabled: bool = True) -> tuple[float, float, str]:
    if open_risk_R < -EPSILON:
        raise ValueError("NEGATIVE_OPEN_RISK")
    residual = max(0.0, CAP_R - open_risk_R) if enabled else CAP_R
    assigned = min(CAP_R, residual) if enabled else CAP_R
    # Floating-point summation can leave sub-tolerance capacity.  It is not an
    # admission: record an exact zero so status and position accounting agree.
    if assigned <= EPSILON:
        assigned = 0.0
    status = "SKIPPED_ZERO_CAPACITY" if assigned == 0.0 else ("FULL" if abs(assigned-CAP_R) <= EPSILON else "PARTIAL")
    return residual, assigned, status


def economics(direction: Direction, entry: float, exit_price: float,
              initial_risk_price: float, assigned: float) -> dict[str, float]:
    sign = 1.0 if direction == "LONG" else -1.0
    gross = sign * (exit_price-entry) / initial_risk_price
    cost = 2.0*TICK_SIZE / initial_risk_price
    return {"gross_R": gross, "cost_R": cost, "net_R_C1": gross-cost,
            "allocated_gross_R": assigned*gross, "allocated_cost_R": assigned*cost,
            "allocated_net_R": assigned*(gross-cost)}
