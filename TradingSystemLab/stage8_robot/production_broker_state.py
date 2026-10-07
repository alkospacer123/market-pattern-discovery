"""Strict FINAM broker-state normalization for Stage 8.12.4 production."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from .account_cleanliness import (
    ACTIVE_ORDER_STATUSES,
    TERMINAL_ORDER_STATUSES,
    normalize_order_status,
)

FILLED_ORDER_STATUSES = frozenset({"FILLED", "EXECUTED", "SL_EXECUTED", "TP_EXECUTED"})
REJECTED_ORDER_STATUSES = frozenset({
    "REJECTED", "FAILED", "DENIED_BY_BROKER", "REJECTED_BY_EXCHANGE", "EXPIRED"
})


class ProductionBrokerStateError(RuntimeError):
    pass


def _decimal_contract_quantity(value: Any) -> int:
    if (
        not isinstance(value, dict)
        or set(value) != {"value"}
        or not isinstance(value["value"], str)
    ):
        raise ProductionBrokerStateError("STAGE8_12_4_BROKER_QUANTITY_INVALID")
    try:
        parsed = Decimal(value["value"])
    except InvalidOperation:
        raise ProductionBrokerStateError("STAGE8_12_4_BROKER_QUANTITY_INVALID") from None
    if not parsed.is_finite() or parsed != parsed.to_integral_value():
        raise ProductionBrokerStateError("STAGE8_12_4_BROKER_QUANTITY_INVALID")
    return int(parsed)


def position_quantity_map(account: Any) -> dict[str, int]:
    if not isinstance(account, dict) or not isinstance(account.get("positions"), list):
        raise ProductionBrokerStateError("STAGE8_12_4_BROKER_POSITIONS_INVALID")
    result: dict[str, int] = {}
    for row in account["positions"]:
        if not isinstance(row, dict):
            raise ProductionBrokerStateError("STAGE8_12_4_BROKER_POSITIONS_INVALID")
        symbol = row.get("symbol")
        if not isinstance(symbol, str) or not symbol or symbol in result:
            raise ProductionBrokerStateError("STAGE8_12_4_BROKER_POSITIONS_INVALID")
        quantity = _decimal_contract_quantity(row.get("quantity"))
        if quantity:
            result[symbol] = quantity
    return result


def order_rows(response: Any) -> list[dict[str, Any]]:
    rows = response.get("orders") if isinstance(response, dict) else response
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ProductionBrokerStateError("STAGE8_12_4_BROKER_ORDERS_INVALID")
    # Validate every status now. Unknown/unspecified broker state must fail closed
    # even when that row is unrelated to an N4 instrument.
    for row in rows:
        try:
            normalize_order_status(row.get("status"))
        except ValueError:
            raise ProductionBrokerStateError("STAGE8_12_4_BROKER_ORDER_STATUS_INVALID") from None
        order_id = row.get("order_id")
        if not isinstance(order_id, str) or not order_id:
            raise ProductionBrokerStateError("STAGE8_12_4_BROKER_ORDER_ID_INVALID")
    return rows


def order_id(row: dict[str, Any]) -> str:
    value = row.get("order_id")
    if not isinstance(value, str) or not value:
        raise ProductionBrokerStateError("STAGE8_12_4_BROKER_ORDER_ID_INVALID")
    return value


def _order_payload(row: dict[str, Any]) -> dict[str, Any] | None:
    ordinary = row.get("order")
    sltp = row.get("sltp_order")
    if ordinary is not None and sltp is not None:
        raise ProductionBrokerStateError("STAGE8_12_4_BROKER_ORDER_PAYLOAD_AMBIGUOUS")
    payload = ordinary if ordinary is not None else sltp
    if payload is None:
        return None
    if not isinstance(payload, dict):
        raise ProductionBrokerStateError("STAGE8_12_4_BROKER_ORDER_PAYLOAD_INVALID")
    return payload


def client_order_id(row: dict[str, Any]) -> str | None:
    payload = _order_payload(row)
    if payload is None:
        return None
    value = payload.get("client_order_id")
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        raise ProductionBrokerStateError("STAGE8_12_4_CLIENT_ORDER_ID_INVALID")
    return value


def order_comment(row: dict[str, Any]) -> str | None:
    payload = _order_payload(row)
    if payload is None:
        return None
    value = payload.get("comment")
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        raise ProductionBrokerStateError("STAGE8_12_4_ORDER_COMMENT_INVALID")
    return value


def by_broker_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result = {}
    for row in rows:
        key = order_id(row)
        if key in result:
            raise ProductionBrokerStateError("STAGE8_12_4_DUPLICATE_BROKER_ORDER_ID")
        result[key] = row
    return result


def by_client_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result = {}
    for row in rows:
        key = client_order_id(row)
        if key is None:
            continue
        if key in result:
            raise ProductionBrokerStateError("STAGE8_12_4_DUPLICATE_CLIENT_ORDER_ID")
        result[key] = row
    return result


def normalized_status(row: dict[str, Any]) -> str:
    try:
        return normalize_order_status(row.get("status"))
    except ValueError:
        raise ProductionBrokerStateError("STAGE8_12_4_BROKER_ORDER_STATUS_INVALID") from None


def is_active(row: dict[str, Any]) -> bool:
    return normalized_status(row) in ACTIVE_ORDER_STATUSES


def is_terminal(row: dict[str, Any]) -> bool:
    return normalized_status(row) in TERMINAL_ORDER_STATUSES


def is_filled(row: dict[str, Any]) -> bool:
    return normalized_status(row) in FILLED_ORDER_STATUSES


def is_rejected(row: dict[str, Any]) -> bool:
    return normalized_status(row) in REJECTED_ORDER_STATUSES
