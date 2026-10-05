"""Strict FINAM read-side account-cleanliness semantics.

This module is order-incapable. It interprets persisted zero-quantity position
rows as flat and validates FINAM order statuses against the broker's documented
OrderStatus enum. Unknown/unspecified broker state fails closed.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

# Canonical names after removing ORDER_STATUS_ and normalizing the two spelling
# variants used elsewhere in Stage 8 (PARTIALLY_FILLED -> PARTIAL_FILL,
# CANCELED -> CANCELLED).  The source authority is FINAM's orders_service.proto.
DOCUMENTED_ORDER_STATUSES = frozenset({
    "UNSPECIFIED",
    "NEW",
    "PARTIAL_FILL",
    "FILLED",
    "DONE_FOR_DAY",
    "CANCELLED",
    "REPLACED",
    "PENDING_CANCEL",
    "REJECTED",
    "SUSPENDED",
    "PENDING_NEW",
    "EXPIRED",
    "FAILED",
    "FORWARDING",
    "WAIT",
    "DENIED_BY_BROKER",
    "REJECTED_BY_EXCHANGE",
    "WATCHING",
    "EXECUTED",
    "DISABLED",
    "LINK_WAIT",
    "SL_GUARD_TIME",
    "SL_EXECUTED",
    "SL_FORWARDING",
    "TP_GUARD_TIME",
    "TP_EXECUTED",
    "TP_CORRECTION",
    "TP_FORWARDING",
    "TP_CORR_GUARD_TIME",
})

# These states no longer represent a live order in the account collection.
# REPLACED is the historical predecessor; any live replacement must appear as
# its own order row and is evaluated independently.
TERMINAL_ORDER_STATUSES = frozenset({
    "FILLED",
    "CANCELLED",
    "REPLACED",
    "REJECTED",
    "EXPIRED",
    "FAILED",
    "DENIED_BY_BROKER",
    "REJECTED_BY_EXCHANGE",
    "EXECUTED",
    "DISABLED",
    "SL_EXECUTED",
    "TP_EXECUTED",
})
ACTIVE_ORDER_STATUSES = DOCUMENTED_ORDER_STATUSES - TERMINAL_ORDER_STATUSES - {"UNSPECIFIED"}

_STATUS_ALIASES = {
    "PARTIALLY_FILLED": "PARTIAL_FILL",
    "CANCELED": "CANCELLED",
    # Legacy synthetic Stage 8 fixtures only; FINAM does not emit these names.
    "ACTIVE": "NEW",
    "PENDING": "PENDING_NEW",
}


def _rest_contract_quantity(value: Any) -> int:
    if (not isinstance(value, dict) or set(value) != {"value"}
            or not isinstance(value["value"], str)):
        raise ValueError("FINAM_POSITION_QUANTITY_INVALID")
    try:
        parsed = Decimal(value["value"])
    except InvalidOperation:
        raise ValueError("FINAM_POSITION_QUANTITY_INVALID") from None
    if not parsed.is_finite() or parsed != parsed.to_integral_value():
        raise ValueError("FINAM_POSITION_QUANTITY_INVALID")
    return int(parsed)


def count_nonzero_positions(positions: Any) -> int:
    if not isinstance(positions, list):
        raise ValueError("FINAM_POSITIONS_SCHEMA_INVALID")
    count = 0
    for row in positions:
        if not isinstance(row, dict):
            raise ValueError("FINAM_POSITIONS_SCHEMA_INVALID")
        symbol = row.get("symbol")
        if not isinstance(symbol, str) or not symbol:
            raise ValueError("FINAM_POSITIONS_SCHEMA_INVALID")
        if _rest_contract_quantity(row.get("quantity")) != 0:
            count += 1
    return count


def normalize_order_status(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("FINAM_ORDER_STATUS_INVALID")
    status = value.upper().removeprefix("ORDER_STATUS_")
    status = _STATUS_ALIASES.get(status, status)
    if status not in DOCUMENTED_ORDER_STATUSES or status == "UNSPECIFIED":
        raise ValueError("FINAM_ORDER_STATUS_INVALID")
    return status


def count_active_orders(orders: Any) -> int:
    if not isinstance(orders, list):
        raise ValueError("FINAM_ORDERS_SCHEMA_INVALID")
    active = 0
    for row in orders:
        if not isinstance(row, dict):
            raise ValueError("FINAM_ORDERS_SCHEMA_INVALID")
        if normalize_order_status(row.get("status")) in ACTIVE_ORDER_STATUSES:
            active += 1
    return active
