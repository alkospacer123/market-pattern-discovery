"""Strict read-side FINAM state for Stage 8.12.4 production reconciliation."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Literal

from .account_cleanliness import ACTIVE_ORDER_STATUSES, normalize_order_status
from .broker import compact_client_order_id
from .margin import parse_rest_decimal_value_object
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


DOCUMENTED_TRANSACTION_CATEGORIES = frozenset({
    "OTHERS", "DEPOSIT", "WITHDRAW", "INCOME", "COMMISSION", "TAX",
    "INHERITANCE", "TRANSFER", "CONTRACT_TERMINATION", "OUTCOMES",
    "FINE", "LOAN",
})
EXTERNAL_CASH_FLOW_CATEGORIES = frozenset({
    "DEPOSIT", "WITHDRAW", "INHERITANCE", "TRANSFER", "LOAN",
})


def broker_realized_basis(account: Any) -> Decimal:
    if not isinstance(account, dict):
        raise ProductionBrokerStateError("STAGE8_12_4_ACCOUNT_SCHEMA_INVALID")
    try:
        equity = parse_rest_decimal_value_object(account.get("equity"), positive=True)
        unrealized = parse_rest_decimal_value_object(account.get("unrealized_profit"))
    except ValueError:
        raise ProductionBrokerStateError("STAGE8_12_4_REALIZED_EQUITY_INVALID") from None
    result = equity - unrealized
    if not result.is_finite() or result <= 0:
        raise ProductionBrokerStateError("STAGE8_12_4_REALIZED_EQUITY_INVALID")
    return result


def _transaction_category(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise ProductionBrokerStateError("STAGE8_12_4_TRANSACTION_CATEGORY_INVALID")
    category = value.upper().removeprefix("TRANSACTION_CATEGORY_")
    if category not in DOCUMENTED_TRANSACTION_CATEGORIES:
        raise ProductionBrokerStateError("STAGE8_12_4_TRANSACTION_CATEGORY_INVALID")
    return category


def require_no_external_cash_flows(response: Any, *, hard_limit: int = 1000) -> int:
    if (
        not isinstance(response, dict)
        or not isinstance(response.get("transactions"), list)
        or type(hard_limit) is not int
        or hard_limit < 1
    ):
        raise ProductionBrokerStateError("STAGE8_12_4_TRANSACTIONS_SCHEMA_INVALID")
    rows = response["transactions"]
    if len(rows) >= hard_limit:
        raise ProductionBrokerStateError("STAGE8_12_4_TRANSACTIONS_LIMIT_REACHED")
    for row in rows:
        if not isinstance(row, dict):
            raise ProductionBrokerStateError("STAGE8_12_4_TRANSACTIONS_SCHEMA_INVALID")
        if _transaction_category(row.get("transaction_category")) in EXTERNAL_CASH_FLOW_CATEGORIES:
            raise ProductionBrokerStateError("STAGE8_12_4_UNEXPLAINED_EXTERNAL_CASH_FLOW")
    return len(rows)


def require_no_unknown_active_orders(
    orders: list[BrokerOrderView],
    intents: list[dict[str, Any]],
) -> None:
    allowed_client_ids: set[str] = set()
    allowed_comments: set[str] = set()
    for intent in intents:
        key = intent.get("idempotency_key")
        if not isinstance(key, str) or not key:
            raise ProductionBrokerStateError("STAGE8_12_4_LOCAL_INTENT_INVALID")
        allowed_client_ids.add(compact_client_order_id(key))
        allowed_comments.add(key)
    for order in orders:
        if not order.active:
            continue
        if (
            order.client_order_id not in allowed_client_ids
            and order.comment not in allowed_comments
        ):
            raise ProductionBrokerStateError("STAGE8_12_4_UNEXPECTED_ACTIVE_ORDER")


def order_for_intent(
    orders: list[BrokerOrderView],
    *,
    idempotency_key: str,
) -> BrokerOrderView | None:
    client_id = compact_client_order_id(idempotency_key)
    matches = [
        order for order in orders
        if order.client_order_id == client_id or order.comment == idempotency_key
    ]
    if len(matches) > 1:
        raise ProductionBrokerStateError("STAGE8_12_4_INTENT_ORDER_AMBIGUOUS")
    return matches[0] if matches else None


def protected_stop_ids_for_position(
    orders: list[BrokerOrderView],
    *,
    position: dict[str, Any],
) -> list[str]:
    try:
        trade_id = str(position["trade_id"])
        symbol = str(position["finam_symbol"])
        direction = str(position["direction"])
        current_broker_id = str(position["protective_stop_broker_order_id"])
        current_price = Decimal(str(position["protective_stop_price"]))
    except (KeyError, ValueError):
        raise ProductionBrokerStateError("STAGE8_12_4_LOCAL_STOP_STATE_INVALID") from None
    if not trade_id or not symbol or not current_broker_id or current_price <= 0:
        raise ProductionBrokerStateError("STAGE8_12_4_LOCAL_STOP_STATE_INVALID")
    expected_side = {"LONG": "SIDE_SELL", "SHORT": "SIDE_BUY"}.get(direction)
    if expected_side is None:
        raise ProductionBrokerStateError("STAGE8_12_4_LOCAL_STOP_STATE_INVALID")

    active = active_sltp_for_trade(
        orders, trade_id=trade_id, symbol=symbol
    )
    if not active:
        raise ProductionBrokerStateError("STAGE8_12_4_PROTECTIVE_STOP_MISSING")
    current_seen = False
    ids: list[str] = []
    for order in active:
        if order.side != expected_side:
            raise ProductionBrokerStateError("STAGE8_12_4_PROTECTIVE_STOP_SIDE_INVALID")
        stop_price = _decimal_object(
            order.request.get("sl_price"), "STAGE8_12_4_SLTP_PRICE_INVALID"
        )
        if direction == "LONG" and stop_price > current_price:
            raise ProductionBrokerStateError("STAGE8_12_4_UNEXPECTED_TIGHTER_STOP")
        if direction == "SHORT" and stop_price < current_price:
            raise ProductionBrokerStateError("STAGE8_12_4_UNEXPECTED_TIGHTER_STOP")
        if order.order_id == current_broker_id:
            if stop_price != current_price:
                raise ProductionBrokerStateError("STAGE8_12_4_CURRENT_STOP_PRICE_MISMATCH")
            current_seen = True
        ids.append(order.order_id)
    if not current_seen:
        raise ProductionBrokerStateError("STAGE8_12_4_CURRENT_PROTECTIVE_STOP_MISSING")
    return sorted(ids)
