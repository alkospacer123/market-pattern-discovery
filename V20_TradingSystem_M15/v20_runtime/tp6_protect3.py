"""TRL-R070 TP6 / Protect3: strict OFFLINE arithmetic and timing contract.

NO orders, cancellations, broker writes, SQLite changes or LIVE hooks. This
module deliberately has no executable SLTP replacement method. Refer to
research ZIP R060 SHA256 80291246ba4692485545f58fd28c7563199bf7be28033fc16eb296efee377e31.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
from typing import Iterable
from zoneinfo import ZoneInfo


class TP6Protect3Unsafe(RuntimeError):
    """Unable to prove entry/stop, M15 completion or safe broker replacement."""


@dataclass(frozen=True)
class TP6Levels:
    direction: str
    fill_quantity: int
    fill_vwap: Decimal
    initial_stop: Decimal
    tick: Decimal
    risk: Decimal
    take_profit: Decimal
    trigger_3r: Decimal
    locked_stop_1r: Decimal


@dataclass(frozen=True)
class ProtectionReview:
    status: str
    eligible_m15_open_msk: datetime | None
    proposed_stop: Decimal | None


def _decimal(value, label: str) -> Decimal:
    try:
        x = Decimal(str(value))
    except (TypeError, ValueError, ArithmeticError) as exc:
        raise TP6Protect3Unsafe(label) from exc
    if not x.is_finite() or x <= 0:
        raise TP6Protect3Unsafe(label)
    return x


def _outward(value: Decimal, tick: Decimal, direction: str) -> Decimal:
    """Never make a winning target/locked profit less than specified R."""
    mode = ROUND_CEILING if direction == "LONG" else ROUND_FLOOR
    return (value / tick).to_integral_value(rounding=mode) * tick


def levels_from_finam_fills(*, direction: str, fills: Iterable[tuple[int, str]],
                            initial_stop, tick) -> TP6Levels:
    """Actual order-linked FINAM fills (quantity, price); never planned Open.

    Full fills must be independently validated against FINAM /trades and
    /positions by existing V20/H1 reconciliation before this pure calculation.
    """
    if direction not in {"LONG", "SHORT"}:
        raise TP6Protect3Unsafe("TP6_SIDE_INVALID")
    step = _decimal(tick, "TP6_TICK_INVALID")
    stop = _decimal(initial_stop, "TP6_STOP_INVALID")
    if stop / step != (stop / step).to_integral_value():
        raise TP6Protect3Unsafe("TP6_STOP_OFF_TICK_GRID")
    try:
        rows = tuple(fills)
    except (TypeError, ValueError) as exc:
        raise TP6Protect3Unsafe("TP6_FILLS_INVALID") from exc
    if not rows:
        raise TP6Protect3Unsafe("TP6_FILLS_UNVERIFIED")
    total, money = 0, Decimal(0)
    for quantity, price in rows:
        if type(quantity) is not int or quantity <= 0:
            raise TP6Protect3Unsafe("TP6_FILL_QUANTITY_INVALID")
        total += quantity
        money += _decimal(price, "TP6_FILL_PRICE_INVALID") * quantity
    vwap = money / total
    side = 1 if direction == "LONG" else -1
    risk = (vwap - stop) * side
    if risk <= 0:
        raise TP6Protect3Unsafe("TP6_STOP_NOT_LOSS_SIDE")
    tp = _outward(vwap + side * 6 * risk, step, direction)
    locked = _outward(vwap + side * risk, step, direction)
    if tp <= 0 or locked <= 0:
        raise TP6Protect3Unsafe("TP6_TARGET_OR_LOCK_INVALID")
    return TP6Levels(direction, total, vwap, stop, step, risk, tp,
                     vwap + side * 3 * risk, locked)


def sltp_tp6_fields(levels: TP6Levels) -> dict:
    """Additional linked TP fields for a 100%-of-position SLTP draft.

    Existing verified 100%-quantity SL fields must remain in the same
    broker SLTP order. A draft is NOT a broker submission or ACK.
    """
    if not isinstance(levels, TP6Levels):
        raise TP6Protect3Unsafe("TP6_LEVELS_REQUIRED")
    return {
        "tp_price": {"value": str(levels.take_profit)},
        "tp_qty_measure": "SLTP_QTY_MEASURE_PERCENT",
        "quantity_tp": {"value": "100"},
    }


def review_completed_m15(*, levels: TP6Levels, m15_open_msk: datetime,
                         observed_utc: datetime, high, low,
                         active_stop, broker_stop_proved: bool,
                         completed_bar_proved: bool) -> ProtectionReview:
    """Stop-first reference order. Return a decision, NEVER an API operation.

    Broker position/SLTP/trade state, not candle OHLC, determines whether an
    exit actually occurred. A candle that could have hit SL or TP needs
    broker reconciliation, not a potentially conflicting stop replacement.
    """
    if not isinstance(levels, TP6Levels):
        raise TP6Protect3Unsafe("PROTECT3_LEVELS_REQUIRED")
    if (not isinstance(m15_open_msk, datetime) or m15_open_msk.tzinfo is not None
            or m15_open_msk.second != 0 or m15_open_msk.microsecond != 0
            or m15_open_msk.minute % 15):
        raise TP6Protect3Unsafe("PROTECT3_BAR_TIME_INVALID")
    if not isinstance(observed_utc, datetime) or observed_utc.tzinfo is None:
        raise TP6Protect3Unsafe("PROTECT3_OBSERVATION_TIME_INVALID")
    next_open = m15_open_msk + timedelta(minutes=15)
    if (observed_utc.astimezone(ZoneInfo("Europe/Moscow")).replace(tzinfo=None)
            < next_open or not completed_bar_proved):
        return ProtectionReview("M15_UNCONFIRMED_NO_CHANGE", None, None)
    if not broker_stop_proved:
        return ProtectionReview("BROKER_STOP_UNVERIFIED_NO_CHANGE", None, None)
    old = _decimal(active_stop, "PROTECT3_CURRENT_STOP_INVALID")
    top = _decimal(high, "PROTECT3_HIGH_INVALID")
    bottom = _decimal(low, "PROTECT3_LOW_INVALID")
    if top < bottom:
        raise TP6Protect3Unsafe("PROTECT3_OHLC_INVALID")
    long = levels.direction == "LONG"
    if ((long and old >= levels.locked_stop_1r) or
            (not long and old <= levels.locked_stop_1r)):
        return ProtectionReview("ALREADY_LOCKED_NO_REGRESSION", None, None)
    if ((long and bottom <= old) or (not long and top >= old)
            or (long and top >= levels.take_profit)
            or (not long and bottom <= levels.take_profit)):
        return ProtectionReview("M15_COULD_HAVE_EXITED_RECONCILE_BROKER", None, None)
    reached = top >= levels.trigger_3r if long else bottom <= levels.trigger_3r
    if not reached:
        return ProtectionReview("BELOW_3R_NO_CHANGE", None, None)
    # The time of the completed bar, not an inferred intrabar tick,
    # establishes the first permitted start of the new +1R stop.
    return ProtectionReview("LOCK_1R_DUE_NEXT_M15_BROKER_REPLACE_BLOCKED",
                            next_open, levels.locked_stop_1r)


def place_or_replace_protect3_live(*_args, **_kwargs) -> None:
    """Explicit safety barrier until FINAM proves atomic/no-gap replacement."""
    raise TP6Protect3Unsafe("FINAM_SLTP_NO_GAP_REPLACEMENT_NOT_PROVEN")
