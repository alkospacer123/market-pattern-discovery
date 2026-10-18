"""M15 roadmap №16: evidence-only FINAM SLTP lifecycle inspection.

Two independently obtained, ordered FINAM GET snapshots are needed. Merely
seeing a 100%-quantity stop cannot prove later partial fills are protected.
This module has no FINAM transport, token, SQLite, H1 reference or order API.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from .broker_fill_readonly import ExpectedEntry
from .broker_snapshot import active_sltp_for_trade, order_views, position_quantities
from .grid_risk import require_on_grid
from .protective_gate import BrokerProtection, decide_protection


class M15SLTPObservationError(RuntimeError):
    pass


@dataclass(frozen=True)
class M15ObservedSLTP:
    broker_order_sha256: str
    initially_observed_quantity: int
    current_broker_quantity: int
    stop_price: Decimal
    protection_action: str
    stop_count: int
    evidence: str = "TWO_SYNTHETIC_OR_BROKER_SUPPLIED_GET_SNAPSHOTS"
    # The caller must prove authenticated exact-account FINAM source separately.
    live_authorized: bool = False
    broker_submission_authorized: bool = False


def _snapshot(
    account: dict, orders_response: dict, expected: ExpectedEntry,
    trade_tag: str, order_id: str,
) -> tuple[int, Decimal]:
    if (not isinstance(account, dict) or account.get("account_id") != expected.account_id
            or account.get("status") not in {"ACCOUNT_ACTIVE", "ACCOUNT_STATUS_ACTIVE"}):
        raise M15SLTPObservationError("M15_SLTP_EXACT_ACCOUNT_UNPROVEN")
    signed = position_quantities(account).get(expected.symbol, 0)
    multiplier = 1 if expected.side == "SIDE_BUY" else -1
    covered = signed * multiplier
    if covered <= 0 or covered > expected.quantity:
        raise M15SLTPObservationError("M15_SLTP_BROKER_POSITION_UNPROVEN")
    orders = order_views(orders_response)
    candidates = active_sltp_for_trade(orders, trade_id=trade_tag, symbol=expected.symbol)
    all_symbol = [
        o for o in orders if o.active and o.kind == "SLTP"
        and o.symbol == expected.symbol
    ]
    if len(candidates) != 1 or len(all_symbol) != 1:
        raise M15SLTPObservationError("M15_SLTP_NOT_UNIQUE_OR_INACTIVE")
    order = candidates[0]
    opposite = "SIDE_SELL" if expected.side == "SIDE_BUY" else "SIDE_BUY"
    if order.order_id != order_id or order.side != opposite:
        raise M15SLTPObservationError("M15_SLTP_ORDER_OR_CLOSING_SIDE_UNPROVEN")
    try:
        value = Decimal(order.request["sl_price"]["value"])
        price = require_on_grid(value, expected.price_step)
    except (KeyError, TypeError, ValueError, ArithmeticError):
        raise M15SLTPObservationError("M15_SLTP_PRICE_GRID_UNPROVEN") from None
    if price <= 0:
        raise M15SLTPObservationError("M15_SLTP_PRICE_UNPROVEN")
    return covered, price


def inspect_sltp_between_gets(
    *, expected: ExpectedEntry, trade_tag: str, stop_order_id: str,
    first_at: datetime, current_at: datetime,
    first_account: dict, first_orders: dict,
    current_account: dict, current_orders: dict,
) -> M15ObservedSLTP:
    """Conservative assessment of 100% SLTP vs later partial fills.

    This is a read-only consistency observation, NOT proof of actual stop
    placement, historical time-of-ACK, exchange acceptance or safe LIVE.
    """
    if not isinstance(expected, ExpectedEntry):
        raise M15SLTPObservationError("M15_SLTP_EXPECTED_IDENTITY_REQUIRED")
    if (not isinstance(trade_tag, str) or not 1 <= len(trade_tag) <= 80
            or ":" in trade_tag or not isinstance(stop_order_id, str)
            or not stop_order_id or len(stop_order_id) > 128):
        raise M15SLTPObservationError("M15_SLTP_LOCAL_IDENTITY_INVALID")
    for instant in (first_at, current_at):
        if not isinstance(instant, datetime) or instant.tzinfo is None or instant.utcoffset() is None:
            raise M15SLTPObservationError("M15_SLTP_OBSERVATION_CLOCK_UNPROVEN")
    if current_at.astimezone(timezone.utc) <= first_at.astimezone(timezone.utc):
        raise M15SLTPObservationError("M15_SLTP_OUT_OF_ORDER_OR_REPLAYED_GET")
    first_qty, first_stop = _snapshot(first_account, first_orders, expected, trade_tag, stop_order_id)
    current_qty, current_stop = _snapshot(current_account, current_orders, expected, trade_tag, stop_order_id)
    if current_stop != first_stop:
        raise M15SLTPObservationError("M15_SLTP_STOP_CHANGED_WITHOUT_SEPARATE_ACK")
    if current_qty < first_qty:
        raise M15SLTPObservationError("M15_SLTP_POSITION_REDUCTION_REQUIRES_EXIT_RECONCILIATION")
    observed = BrokerProtection(
        broker_order_id=stop_order_id, stop_price=current_stop,
        percent=100, covered_quantity_at_ack=first_qty, active=True,
    )
    # Existing stop is never cancelled here; later fills require new evidence.
    decision = decide_protection(
        direction="LONG" if expected.side == "SIDE_BUY" else "SHORT",
        actual_entry=Decimal("1"), atr=Decimal("1"),
        price_step=expected.price_step,
        broker_position_qty=current_qty, broker_stop=observed,
        broker_stop_count=1,
    )
    import hashlib
    return M15ObservedSLTP(
        broker_order_sha256=hashlib.sha256(stop_order_id.encode()).hexdigest(),
        initially_observed_quantity=first_qty,
        current_broker_quantity=current_qty,
        stop_price=current_stop,
        protection_action=decision.action,
        stop_count=1,
    )
