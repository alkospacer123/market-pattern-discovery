"""Strict FINAM read-side account-cleanliness semantics.

This module is order-incapable. It interprets persisted zero-quantity position
rows as flat and distinguishes active orders from terminal order history.
Malformed or unknown broker state fails closed through ValueError.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

ACTIVE_ORDER_STATUSES = frozenset({"NEW", "PENDING", "ACTIVE", "PARTIAL_FILL"})
TERMINAL_ORDER_STATUSES = frozenset({"FILLED", "REJECTED", "EXPIRED", "CANCELLED"})


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


def _normalized_order_status(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("FINAM_ORDER_STATUS_INVALID")
    status = value.upper().removeprefix("ORDER_STATUS_")
    status = {"PARTIALLY_FILLED": "PARTIAL_FILL", "CANCELED": "CANCELLED"}.get(status, status)
    if status not in ACTIVE_ORDER_STATUSES | TERMINAL_ORDER_STATUSES:
        raise ValueError("FINAM_ORDER_STATUS_INVALID")
    return status


def count_active_orders(orders: Any) -> int:
    if not isinstance(orders, list):
        raise ValueError("FINAM_ORDERS_SCHEMA_INVALID")
    active = 0
    for row in orders:
        if not isinstance(row, dict):
            raise ValueError("FINAM_ORDERS_SCHEMA_INVALID")
        if _normalized_order_status(row.get("status")) in ACTIVE_ORDER_STATUSES:
            active += 1
    return active
