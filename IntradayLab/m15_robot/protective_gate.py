"""M15 Step16: strict *offline* protection decision from broker evidence.

H1 contract read as reference; no H1 imports, orders, task or token access.
A 100%-position FINAM SLTP percentage does not prove coverage of contracts
filled AFTER the stop acknowledgement. Keep the former stop until broker
confirms replacement. Never enable a new entry while protection is unproven.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .grid_risk import initial_stop, require_on_grid


class M15ProtectionError(RuntimeError):
    pass


@dataclass(frozen=True)
class BrokerProtection:
    broker_order_id: str
    stop_price: Decimal
    percent: int
    covered_quantity_at_ack: int
    active: bool


@dataclass(frozen=True)
class ProtectionDecision:
    action: str
    proposed_stop: Decimal
    old_stop_must_remain: bool
    new_entries_authorized: bool = False
    live_submission_authorized: bool = False


def decide_protection(
    *, direction: str, actual_entry: Decimal, atr: Decimal,
    price_step: Decimal, broker_position_qty: int,
    broker_stop: BrokerProtection | None, broker_stop_count: int,
) -> ProtectionDecision:
    """Offline STOP-first decision; broker verification mandatory on each cycle.

    Quantity is absolute M15-account position size, independently confirmed
    by FINAM after fills. This function never submits or cancels SLTP orders.
    """
    if direction not in {"LONG", "SHORT"}:
        raise M15ProtectionError("M15_PROTECTION_DIRECTION_INVALID")
    if type(broker_position_qty) is not int or broker_position_qty <= 0:
        raise M15ProtectionError("M15_PROTECTION_POSITION_NOT_PROVEN")
    if type(broker_stop_count) is not int or broker_stop_count < 0 or broker_stop_count > 1:
        raise M15ProtectionError("M15_PROTECTION_DUPLICATE_OR_UNKNOWN_STOP")
    proposed = initial_stop(direction, actual_entry, atr, price_step)
    if broker_stop is None:
        if broker_stop_count != 0:
            raise M15ProtectionError("M15_PROTECTION_STOP_EVIDENCE_MISSING")
        return ProtectionDecision("INSTALL_REQUIRED", proposed, False)
    if broker_stop_count != 1:
        raise M15ProtectionError("M15_PROTECTION_STOP_COUNT_MISMATCH")
    if (not isinstance(broker_stop, BrokerProtection)
            or not broker_stop.active
            or not isinstance(broker_stop.broker_order_id, str)
            or not broker_stop.broker_order_id
            or type(broker_stop.percent) is not int or broker_stop.percent != 100
            or type(broker_stop.covered_quantity_at_ack) is not int
            or broker_stop.covered_quantity_at_ack <= 0):
        raise M15ProtectionError("M15_PROTECTION_BROKER_STOP_INVALID")
    current_stop = require_on_grid(broker_stop.stop_price, price_step)
    # Existing proven trailing stops may correctly cross the original entry.
    if broker_stop.covered_quantity_at_ack > broker_position_qty:
        raise M15ProtectionError("M15_PROTECTION_COVERAGE_EXCEEDS_POSITION")
    if broker_stop.covered_quantity_at_ack < broker_position_qty:
        # Later partial fills increase exposure; a past 100% SLTP acknowledgement
        # is NOT evidence that those additional contracts are now protected.
        return ProtectionDecision("REPLACE_REQUIRED_COVERAGE", current_stop, True)
    return ProtectionDecision("HOLD_BROKER_CONFIRMED", current_stop, True)
