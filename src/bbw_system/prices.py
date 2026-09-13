"""Tick-normalized price arithmetic used by signal and execution code."""
from __future__ import annotations

from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP


def price_to_ticks(price: float, tick_size: float, rounding: str = "nearest") -> int:
    if tick_size <= 0:
        raise ValueError("tick_size must be positive")
    value = Decimal(str(price)) / Decimal(str(tick_size))
    modes = {"nearest": ROUND_HALF_UP, "up": ROUND_CEILING, "down": ROUND_FLOOR}
    if rounding not in modes:
        raise ValueError("rounding must be nearest, up, or down")
    return int(value.to_integral_value(rounding=modes[rounding]))


def ticks_to_price(ticks: int, tick_size: float) -> float:
    return float(Decimal(ticks) * Decimal(str(tick_size)))


def align_price(price: float, tick_size: float, rounding: str = "nearest") -> float:
    return ticks_to_price(price_to_ticks(price, tick_size, rounding), tick_size)


def is_tick_aligned(price: float, tick_size: float) -> bool:
    value = Decimal(str(price)) / Decimal(str(tick_size))
    return value == value.to_integral_value()


def adverse_fill(price: float, side: str, slippage_ticks: float, tick_size: float) -> float:
    """Apply slippage adversely: BUY upwards and SELL downwards, then grid-align."""
    raw = price + slippage_ticks * tick_size * (1 if side == "BUY" else -1)
    return align_price(raw, tick_size, "up" if side == "BUY" else "down")
