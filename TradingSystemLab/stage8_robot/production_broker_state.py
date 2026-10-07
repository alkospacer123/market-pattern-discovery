"""Strict read-side FINAM state for Stage 8.12.4 production reconciliation."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Literal

from .account_cleanliness import ACTIVE_ORDER_STATUSES, normalize_order_status
from .protective_stop_contract import QTY_MEASURE, QTY_PERCENT


class ProductionBrokerStateError(RuntimeError):
    pass


def _decimal_object(value: Any, code: str) -> Decimal:
    if not isinstance(value, dict) or set(value) != {"value"} or not isinstance(value["value"], str):
        raise ProductionBrokerStateError(code)
    try:
        result = Decimal(value["value"])
    except InvalidOperation:
        raise ProductionBrokerStateError(code) from None
    if not result.is_finite():
        raise ProductionBrokerStateError(code)
    return result


def _contracts(value: Any, code: str) -> int:
    result = _decimal_object(value, code)
    if result != result.to_integral_value():
        raise ProductionBrokerStateError(code)
    return int(result)


def position_quantities(account: Any) -> dict[str, int]:
    if not isinstance(account, dict) or not isinstance(account.get("positions"), list):
        raise ProductionBrokerStateError("STAGE8_12_4_POSITIONS_SCHEMA_INVALID")
    result: dict[str, int] = {}
    for row in account["positions"]:
        if not isinstance(row, dict):
            raise ProductionBrokerStateError("STAGE8_12_4_POSITIONS_SCHEMA_INVALID")
        symbol = row.get("symbol")
        if not isinstance(symbol, str) or not symbol or symbol in result:
            raise ProductionBrokerStateError("STAGE8_12_4_POSITIONS_SCHEMA_INVALID")
        quantity = _contracts(row.get("quantity"), "STAGE8_12_4_POSITION_QUANTITY_INVALID")
        if quantity != 0:
            result[symbol] = quantity
    return result


OrderKind = Literal["REGULAR", "SLTP"]


@dataclass(frozen=True)
class BrokerOrderView:
    order_id: str
    status: str
    active: bool
    kind: OrderKind
    symbol: str
    client_order_id: str
    comment: str | None
    side: str
    request: dict[str, Any]


def order_views(response: Any) -> list[BrokerOrderView]:
    rows = response.get("orders") if isinstance(response, dict) else response
    if not isinstance(rows, list):
        raise ProductionBrokerStateError("STAGE8_12_4_ORDERS_SCHEMA_INVALID")
    result: list[BrokerOrderView] = []
    seen_ids: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ProductionBrokerStateError("STAGE8_12_4_ORDERS_SCHEMA_INVALID")
        order_id = row.get("order_id")
        if not isinstance(order_id, str) or not order_id or order_id in seen_ids:
            raise ProductionBrokerStateError("STAGE8_12_4_ORDER_ID_INVALID")
        seen_ids.add(order_id)
        try:
            status = normalize_order_status(row.get("status"))
        except ValueError:
            raise ProductionBrokerStateError("STAGE8_12_4_ORDER_STATUS_INVALID") from None

        regular = row.get("order")
        sltp = row.get("sltp_order")
        regular_present = isinstance(regular, dict) and bool(regular)
        sltp_present = isinstance(sltp, dict) and bool(sltp)
        if regular_present == sltp_present:
            raise ProductionBrokerStateError("STAGE8_12_4_ORDER_KIND_INVALID")
        request = regular if regular_present else sltp
        kind: OrderKind = "REGULAR" if regular_present else "SLTP"
        symbol = request.get("symbol")
        client_id = request.get("client_order_id")
        side = request.get("side")
        comment = request.get("comment")
        if (
            not isinstance(symbol, str)
            or not symbol
            or not isinstance(client_id, str)
            or not client_id
            or len(client_id) > 20
            or not isinstance(side, str)
            or side not in {"SIDE_BUY", "SIDE_SELL"}
            or (comment is not None and (not isinstance(comment, str) or len(comment) > 128))
        ):
            raise ProductionBrokerStateError("STAGE8_12_4_ORDER_REQUEST_INVALID")

        if kind == "REGULAR":
            quantity = _contracts(request.get("quantity"), "STAGE8_12_4_ORDER_QUANTITY_INVALID")
            if quantity <= 0:
                raise ProductionBrokerStateError("STAGE8_12_4_ORDER_QUANTITY_INVALID")

        result.append(BrokerOrderView(
            order_id=order_id,
            status=status,
            active=status in ACTIVE_ORDER_STATUSES,
            kind=kind,
            symbol=symbol,
            client_order_id=client_id,
            comment=comment,
            side=side,
            request=request,
        ))
    return result


def unique_order_by_client_id(
    orders: list[BrokerOrderView], client_order_id: str
) -> BrokerOrderView | None:
    matches = [order for order in orders if order.client_order_id == client_order_id]
    if len(matches) > 1:
        raise ProductionBrokerStateError("STAGE8_12_4_DUPLICATE_CLIENT_ORDER_ID")
    return matches[0] if matches else None


def _validate_production_sltp(order: BrokerOrderView) -> None:
    if order.kind != "SLTP":
        raise ProductionBrokerStateError("STAGE8_12_4_SLTP_ORDER_REQUIRED")
    request = order.request
    measure = request.get("sl_qty_measure")
    quantity_sl = _decimal_object(
        request.get("quantity_sl"), "STAGE8_12_4_SLTP_QUANTITY_INVALID"
    )
    if measure != QTY_MEASURE or quantity_sl != QTY_PERCENT:
        raise ProductionBrokerStateError(
            "STAGE8_12_4_SLTP_CLOSE_ONLY_CONTRACT_INVALID"
        )
    sl_price = _decimal_object(
        request.get("sl_price"), "STAGE8_12_4_SLTP_PRICE_INVALID"
    )
    if sl_price <= 0:
        raise ProductionBrokerStateError("STAGE8_12_4_SLTP_PRICE_INVALID")
    if request.get("valid_before") != "VALID_BEFORE_GOOD_TILL_CANCEL":
        raise ProductionBrokerStateError("STAGE8_12_4_SLTP_VALIDITY_INVALID")


def active_sltp_for_trade(
    orders: list[BrokerOrderView], *, trade_id: str, symbol: str
) -> list[BrokerOrderView]:
    prefix = f"stage8.12:{trade_id}:stop:"
    matched = [
        order
        for order in orders
        if order.active
        and order.kind == "SLTP"
        and order.symbol == symbol
        and isinstance(order.comment, str)
        and order.comment.startswith(prefix)
    ]
    for order in matched:
        _validate_production_sltp(order)
    return matched
