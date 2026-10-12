"""PROPOSED stop-grid amendment. Exact projection; no transport or strategy changes."""
from __future__ import annotations

from dataclasses import replace
from decimal import Decimal, InvalidOperation
from fractions import Fraction
import hashlib
import json

EXECUTION_REVISION = "STOP_TICK_GRID_V2_FILL_PROPOSED"
# LIVE acceptance remains blocked: Intel report bytes and growing-position
# SLTP coverage are not independently verified. The candidate stays inactive.
FINAM_FILL_AUTHORITY_VERIFIED = False


def decimal_price(value) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError("EXECUTION_PRICE_INVALID") from None
    if not result.is_finite() or result <= 0:
        raise ValueError("EXECUTION_PRICE_INVALID")
    return result


def _tick_ratio(price, step) -> tuple[int, int]:
    step = decimal_price(step)
    price = price if isinstance(price, Fraction) else decimal_price(price)
    if price <= 0:
        raise ValueError("EXECUTION_PRICE_INVALID")
    pn, pd = price.as_integer_ratio()
    sn, sd = step.as_integer_ratio()
    return pn * sd, pd * sn


def require_on_grid(price, step) -> Decimal:
    numerator, denominator = _tick_ratio(price, step)
    if numerator % denominator:
        raise ValueError("EXECUTION_PRICE_NOT_ON_TICK_GRID")
    return project_stop("LONG", price, step) if isinstance(price, Fraction) else decimal_price(price)


def project_stop(direction: str, price, step) -> Decimal:
    if direction not in {"LONG", "SHORT"}:
        raise ValueError("DIRECTION_INVALID")
    numerator, denominator = _tick_ratio(price, step)
    ticks, remainder = divmod(numerator, denominator)
    if direction == "SHORT" and remainder:
        ticks += 1
    # Construct the exact product from integer coefficient/exponent, independent
    # of the caller's Decimal precision. No division, epsilon or float rounding.
    step_tuple = decimal_price(step).as_tuple()
    coefficient = int("".join(map(str, step_tuple.digits))) * ticks
    result = Decimal((0, tuple(map(int, str(coefficient))), step_tuple.exponent))
    return decimal_price(result)


def initial_projection(direction: str, entry, raw_stop, step) -> tuple[Decimal, Decimal]:
    entry = require_on_grid(entry, step)
    raw_stop = decimal_price(raw_stop)
    if (direction == "LONG" and raw_stop >= entry
            or direction == "SHORT" and raw_stop <= entry):
        raise ValueError("INITIAL_STOP_WRONG_SIDE")
    stop = project_stop(direction, raw_stop, step)
    return stop, abs(entry - stop)


def authority_fingerprint(evidence: dict) -> str:
    return hashlib.sha256(json.dumps(evidence, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def manage_executable(core, position, bar, step) -> dict:
    """Keep frozen core event order, projecting before stop tests and after bars.

    Executable grid prices use Decimals; order-linked means use exact Fractions. The frozen Trail1State float conversion of a
    stored candidate is bypassed numerically, while its event transitions remain
    authoritative. Raw candidate calculation still comes from DecisionCore.
    """
    rational = isinstance(position.entry, Fraction)
    number = (lambda value: Fraction(str(value))) if rational else decimal_price
    for field in ("entry", "initial_stop", "current_stop", "favorable_extreme"):
        setattr(position, field, number(getattr(position, field)))
    trail = position.trail1
    trail.initial_risk_price = abs(position.entry - position.initial_stop)
    trail.trigger_price = position.entry + (trail.initial_risk_price if position.direction == "LONG" else -trail.initial_risk_price)
    previous = require_on_grid(position.current_stop, step)
    if trail.stored_candidate is not None:
        trail.stored_candidate = require_on_grid(trail.stored_candidate, step)
    if trail.triggered and not trail.activated and bar.timestamp.isoformat() != trail.trigger_bar_time:
        candidate = trail.stored_candidate
        trail.activate_before_event(bar.timestamp.isoformat(), previous)
        position.current_stop = max(previous, candidate) if position.direction == "LONG" else min(previous, candidate)
    values = {field: require_on_grid(getattr(bar, field), step) for field in ("open", "high", "low", "close")}
    values["atr"] = decimal_price(bar.atr)
    if rational:
        values = {key: Fraction(value) for key, value in values.items()}
    was_triggered = trail.triggered
    outcome = core.manage(position, replace(bar, **values))
    if outcome["event"] == "HOLD":
        raw_candidate = outcome["canonical_stop"]
        candidate = project_stop(position.direction, raw_candidate, step)
        if trail.triggered and not was_triggered:
            trail.stored_candidate = candidate
        projected = project_stop(position.direction, position.current_stop, step)
        position.current_stop = max(previous, projected) if position.direction == "LONG" else min(previous, projected)
        outcome["raw_candidate"] = str(raw_candidate)
    outcome["stop"] = position.current_stop
    return outcome
