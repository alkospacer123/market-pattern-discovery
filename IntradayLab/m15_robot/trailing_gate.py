"""Pure M15 №17 trailing 3.5 ATR: proposal is NOT an active broker stop.

Only a subsequent verified FINAM broker snapshot may commit the new
stop/watermark. This module never submits orders or changes live SQLite.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from .grid_risk import TrailingState, ratchet_after_survived_completed_bar
from .protective_gate import BrokerProtection, decide_protection
from .spec import TRAILING_STOP_ATR


class M15TrailingGateError(ValueError):
    pass


@dataclass(frozen=True)
class PendingTrail:
    before: TrailingState
    candidate: TrailingState
    broker_stop_id_at_proposal: str
    broker_position_qty: int
    replace_required: bool
    live_submission_authorized: bool = False


def propose_trail(
    *, confirmed: TrailingState, observed_stop: BrokerProtection,
    broker_position_qty: int, completed_at: datetime, high: Decimal,
    low: Decimal, atr: Decimal, price_step: Decimal,
    survived_completed_bar: bool,
) -> PendingTrail:
    """Complete-bar, STOP-first, exact broker-protected entry precondition."""
    if type(survived_completed_bar) is not bool or not survived_completed_bar:
        raise M15TrailingGateError("M15_TRAIL_BAR_SURVIVAL_NOT_PROVEN")
    if not isinstance(completed_at, datetime) or completed_at.tzinfo is None or completed_at.utcoffset() is None:
        raise M15TrailingGateError("M15_TRAIL_COMPLETED_TIME_UNPROVEN")
    if not isinstance(confirmed, TrailingState):
        raise M15TrailingGateError("M15_TRAIL_STATE_UNPROVEN")
    if confirmed.direction not in {"LONG", "SHORT"}:
        raise M15TrailingGateError("M15_TRAIL_DIRECTION_INVALID")
    if confirmed.active_stop == confirmed.entry:
        raise M15TrailingGateError("M15_TRAIL_INVALID_STOP")
    if (confirmed.direction == "LONG" and confirmed.extreme < confirmed.entry
            or confirmed.direction == "SHORT" and confirmed.extreme > confirmed.entry):
        raise M15TrailingGateError("M15_TRAIL_EXTREME_INVALID")
    if not isinstance(observed_stop, BrokerProtection) or observed_stop.stop_price != confirmed.active_stop:
        raise M15TrailingGateError("M15_TRAIL_BROKER_STOP_DIVERGENCE")
    if decide_protection(
        direction=confirmed.direction, actual_entry=confirmed.entry, atr=atr,
        price_step=price_step, broker_position_qty=broker_position_qty,
        broker_stop=observed_stop, broker_stop_count=1,
    ).action != "HOLD_BROKER_CONFIRMED":
        raise M15TrailingGateError("M15_TRAIL_PROTECTION_NOT_CONFIRMED")
    try:
        candidate = ratchet_after_survived_completed_bar(
            confirmed, completed_at=completed_at, high=high, low=low,
            atr=atr, price_step=price_step,
        )
    except ValueError as exc:
        raise M15TrailingGateError("M15_TRAIL_BAR_OR_GRID_INVALID") from None
    if (confirmed.direction == "LONG" and candidate.active_stop < confirmed.active_stop
            or confirmed.direction == "SHORT" and candidate.active_stop > confirmed.active_stop):
        raise M15TrailingGateError("M15_TRAIL_STOP_WIDENING")
    return PendingTrail(
        before=confirmed, candidate=candidate,
        broker_stop_id_at_proposal=observed_stop.broker_order_id,
        broker_position_qty=broker_position_qty,
        replace_required=candidate.active_stop != confirmed.active_stop,
    )


def confirm_trail(
    pending: PendingTrail, *, observed_stop: BrokerProtection | None,
    observed_stop_count: int, broker_position_qty: int, price_step: Decimal,
) -> TrailingState:
    """Commit proposed state ONLY when FINAM proves the expected active stop."""
    if not isinstance(pending, PendingTrail) or not isinstance(pending.before, TrailingState):
        raise M15TrailingGateError("M15_TRAIL_PENDING_PROOF_REQUIRED")
    if (type(broker_position_qty) is not int or broker_position_qty != pending.broker_position_qty
            or type(observed_stop_count) is not int or observed_stop_count != 1
            or not isinstance(observed_stop, BrokerProtection)):
        raise M15TrailingGateError("M15_TRAIL_BROKER_CONFIRMATION_UNPROVEN")
    if (observed_stop.stop_price != pending.candidate.active_stop
            or (not pending.replace_required and observed_stop.broker_order_id != pending.broker_stop_id_at_proposal)):
        raise M15TrailingGateError("M15_TRAIL_BROKER_PRICE_OR_ID_MISMATCH")
    try:
        decision = decide_protection(
            direction=pending.before.direction, actual_entry=pending.before.entry,
            atr=Decimal("1"), price_step=price_step,
            broker_position_qty=broker_position_qty, broker_stop=observed_stop,
            broker_stop_count=observed_stop_count,
        )
    except ValueError:
        raise M15TrailingGateError("M15_TRAIL_BROKER_STOP_INVALID") from None
    if decision.action != "HOLD_BROKER_CONFIRMED":
        raise M15TrailingGateError("M15_TRAIL_BROKER_COVERAGE_UNPROVEN")
    return pending.candidate
