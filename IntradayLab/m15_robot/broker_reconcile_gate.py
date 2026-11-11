"""Step14 M15-only broker evidence cross-check. READONLY, no SQLite adoption.

Combines existing strict FINAM order, position and bounded trade validators.
This is a diagnostic precondition, not a production execution state machine:
a visible 100% SLTP still does NOT prove post-fill broker protection coverage.
No broker API object, trading endpoint, credentials, H1 state or file IO.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from .broker_fill_readonly import ExpectedEntry, analyze_account_trades
from .broker_snapshot import (
    ProductionBrokerStateError, active_sltp_for_trade, order_views,
    position_quantities,
)
from .grid_risk import require_on_grid
from .spec import INSTRUMENTS


class M15ReconcileGateError(RuntimeError):
    pass


@dataclass(frozen=True)
class M15EntryEvidence:
    quantity_status: str
    matched_fill_quantity: int
    broker_position_quantity: int
    active_entry_orders: int
    active_sltp_count: int
    protection_status: str
    fill_set_sha256: str
    sqlite_adoption_authorized: bool = False
    live_authorized: bool = False


def _order_quantity(value) -> int:
    if not isinstance(value, dict) or set(value) != {"value"} or not isinstance(value["value"], str):
        raise M15ReconcileGateError("M15_RECONCILE_ORDER_QUANTITY_SCHEMA_INVALID")
    try:
        number = Decimal(value["value"])
    except InvalidOperation:
        raise M15ReconcileGateError("M15_RECONCILE_ORDER_QUANTITY_INVALID") from None
    if not number.is_finite() or number <= 0 or number != number.to_integral_value():
        raise M15ReconcileGateError("M15_RECONCILE_ORDER_QUANTITY_INVALID")
    return int(number)


def assess_entry_evidence(
    *, account: dict, orders_response: dict, trades_response: dict,
    expected: ExpectedEntry, expected_client_order_id: str,
    stop_trade_tag: str, start: str, end: str, limit: int = 1000,
) -> M15EntryEvidence:
    """Never infer a FINAM fill from a simulated ACK or a position alone.

    Stop acknowledgement timing and 100%-after-latest-fill coverage cannot
    be proved from these three GET responses: always require a separate
    broker-side protection receipt before assigning executable authority.
    """
    if not isinstance(expected, ExpectedEntry):
        raise M15ReconcileGateError("M15_RECONCILE_EXPECTED_ENTRY_REQUIRED")
    if expected.symbol not in {symbol + "@RTSX" for symbol in INSTRUMENTS}:
        raise M15ReconcileGateError("M15_RECONCILE_SYMBOL_OUTSIDE_N4")
    if (not isinstance(expected_client_order_id, str)
            or not 1 <= len(expected_client_order_id) <= 20
            or not isinstance(stop_trade_tag, str)
            or not stop_trade_tag or len(stop_trade_tag) > 100
            or ":" in stop_trade_tag):
        raise M15ReconcileGateError("M15_RECONCILE_LOCAL_IDENTITY_INVALID")
    if (not isinstance(account, dict)
            or account.get("account_id") != expected.account_id
            or account.get("status") not in {"ACCOUNT_ACTIVE", "ACCOUNT_STATUS_ACTIVE"}):
        raise M15ReconcileGateError("M15_RECONCILE_ACCOUNT_BINDING_INVALID")

    positions = position_quantities(account)
    orders = order_views(orders_response)
    owned = [order for order in orders if order.order_id == expected.order_id]
    if len(owned) != 1 or owned[0].kind != "REGULAR":
        raise M15ReconcileGateError("M15_RECONCILE_EXACT_ORDER_UNPROVEN")
    entry = owned[0]
    if (entry.symbol != expected.symbol or entry.side != expected.side
            or entry.client_order_id != expected_client_order_id
            or _order_quantity(entry.request.get("quantity")) != expected.quantity):
        raise M15ReconcileGateError("M15_RECONCILE_ORDER_IDENTITY_MISMATCH")
    if any(
        order.active and order.kind == "REGULAR" and order.symbol == expected.symbol
        and order.order_id != expected.order_id
        for order in orders
    ):
        raise M15ReconcileGateError("M15_RECONCILE_COMPETING_ENTRY_ORDER")

    receipt = analyze_account_trades(
        trades_response, expected, start=start, end=end, limit=limit,
    )
    filled = receipt["matched_quantity"]
    # Order and trade GETs are independent snapshots. If their states disagree,
    # HALT rather than infer a fill from the order status or overlook a missing
    # history page. Repeated GETs may resolve a transient race.
    if (
        (entry.status in {"FILLED", "EXECUTED"} and filled != expected.quantity)
        or (filled == expected.quantity and entry.status not in {"FILLED", "EXECUTED"})
        or (0 < filled < expected.quantity and entry.status != "PARTIAL_FILL")
        or (filled == 0 and entry.status == "PARTIAL_FILL")
    ):
        raise M15ReconcileGateError("M15_RECONCILE_ORDER_STATUS_FILL_DIVERGENCE")
    signed = filled if expected.side == "SIDE_BUY" else -filled
    current = positions.get(expected.symbol, 0)
    # A full account ledger may legitimately contain multiple instruments.
    # A *single-entry* proof cannot silently adopt earlier same-symbol positions
    # or infer a closing order not present in this bounded entry history.
    if current != signed:
        raise M15ReconcileGateError("M15_RECONCILE_POSITION_FILL_DIVERGENCE")

    stops = active_sltp_for_trade(orders, trade_id=stop_trade_tag, symbol=expected.symbol)
    all_symbol_stops = [
        order for order in orders
        if order.active and order.kind == "SLTP" and order.symbol == expected.symbol
    ]
    if len(stops) != len(all_symbol_stops):
        raise M15ReconcileGateError("M15_RECONCILE_FOREIGN_ACTIVE_SLTP")
    if len(stops) > 1:
        raise M15ReconcileGateError("M15_RECONCILE_DUPLICATE_ACTIVE_SLTP")
    if filled == 0 and stops:
        raise M15ReconcileGateError("M15_RECONCILE_ORPHAN_ACTIVE_SLTP")

    if stops:
        stop = stops[0]
        closing_side = "SIDE_SELL" if expected.side == "SIDE_BUY" else "SIDE_BUY"
        if stop.side != closing_side:
            raise M15ReconcileGateError("M15_RECONCILE_SLTP_CLOSING_SIDE_INVALID")
        try:
            require_on_grid(stop.request["sl_price"]["value"], expected.price_step)
        except (KeyError, TypeError, ValueError):
            raise M15ReconcileGateError("M15_RECONCILE_SLTP_GRID_INVALID") from None

    if filled == 0:
        protection = "NO_CONFIRMED_FILL"
    elif not stops:
        protection = "UNPROTECTED_BROKER_FILL"
    else:
        protection = "ACTIVE_SLTP_COVERAGE_TIMESTAMP_UNPROVEN"
    return M15EntryEvidence(
        quantity_status=receipt["quantity_status"],
        matched_fill_quantity=filled,
        broker_position_quantity=current,
        active_entry_orders=int(entry.active),
        active_sltp_count=len(stops),
        protection_status=protection,
        fill_set_sha256=receipt["fill_set_sha256"],
    )
