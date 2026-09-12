"""Dimensionally explicit transaction-cost conversions."""
from __future__ import annotations


def tick_cost_r(entry_price: float, initial_stop: float, tick_size: float,
                cost_ticks_per_side: float) -> float:
    """Return round-trip tick-equivalent cost in initial-risk (R) units."""
    risk = abs(float(entry_price) - float(initial_stop))
    if risk <= 0:
        raise ValueError("initial_risk_points must be positive")
    if tick_size <= 0:
        raise ValueError("tick_size must be positive")
    return 2.0 * float(cost_ticks_per_side) * float(tick_size) / risk


def net_r(gross_r: float, entry_price: float, initial_stop: float,
          tick_size: float, cost_ticks_per_side: float) -> float:
    return float(gross_r) - tick_cost_r(entry_price, initial_stop, tick_size,
                                        cost_ticks_per_side)
