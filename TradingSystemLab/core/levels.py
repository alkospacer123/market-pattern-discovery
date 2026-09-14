"""Decimal-safe helpers for regularly spaced price levels."""
from __future__ import annotations

from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR


def _decimal(value: int | float | str | Decimal) -> Decimal:
    """Convert through the printable representation, never the binary value."""
    if isinstance(value, Decimal):
        return value
    # Market inputs are floats; 15 significant digits removes their binary
    # arithmetic tail while retaining substantially more precision than quotes.
    return Decimal(format(value, ".15g")) if isinstance(value, float) else Decimal(str(value))


def nearest_lower_level(price: int | float | str | Decimal,
                        step: int | float | str | Decimal) -> Decimal:
    """Return the greatest level <= price (an exact level returns itself)."""
    price_d, step_d = _decimal(price), _decimal(step)
    if step_d <= 0:
        raise ValueError("level step must be positive")
    return (price_d / step_d).to_integral_value(rounding=ROUND_FLOOR) * step_d


def nearest_upper_level(price: int | float | str | Decimal,
                        step: int | float | str | Decimal) -> Decimal:
    """Return the least level >= price (an exact level returns itself)."""
    price_d, step_d = _decimal(price), _decimal(step)
    if step_d <= 0:
        raise ValueError("level step must be positive")
    return (price_d / step_d).to_integral_value(rounding=ROUND_CEILING) * step_d


def level_offset(level: int | float | str | Decimal,
                 step: int | float | str | Decimal, fraction: float) -> Decimal:
    """Apply a fractional level step using decimal arithmetic."""
    return _decimal(level) + _decimal(step) * _decimal(fraction)
