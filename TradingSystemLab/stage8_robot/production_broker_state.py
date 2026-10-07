"""Strict FINAM broker-state parsing for Stage 8.12.4 production."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from .account_cleanliness import (
    ACTIVE_ORDER_STATUSES,
    TERMINAL_ORDER_STATUSES,
    normalize_order_status,
)
from .broker import compact_client_order_id
from .instrument_resolver import parse_rest_value_object
from .margin import parse_rest_decimal_value_object
from .specification import INSTRUMENTS


class ProductionBrokerStateError(RuntimeError):
    pass


DOCUMENTED_TRANSACTION_CATEGORIES = frozenset({
    "OTHERS", "DEPOSIT", "WITHDRAW", "INCOME", "COMMISSION", "TAX",
    "INHERITANCE", "TRANSFER", "CONTRACT_TERMINATION", "OUTCOMES",
    "FINE", "LOAN",
})
EXTERNAL_CASH_FLOW_CATEGORIES = frozenset({
    "DEPOSIT", "WITHDRAW", "INHERITANCE", "TRANSFER", "LOAN",
})
FILLED_ORDER_STATUSES = frozenset({"FILLED", "EXECUTED", "SL_EXECUTED", "TP_EXECUTED"})
REJECTED_ORDER_STATUSES = frozenset({
    "REJECTED", "FAILED", "DENIED_BY_BROKER", "REJECTED_BY_EXCHANGE",
    "CANCELLED", "EXPIRED", "DISABLED",
})


@dataclass(frozen=True)
class BrokerOrder:
    order_id: str
    status: str
    kind: str
    symbol: str
    side: str | None
    client_order_id: str | None
    comment: str | None
    payload: dict[str, Any]

    @property
    def active(self) -> bool:
        return self.status in ACTIVE_ORDER_STATUSES

    @property
    def terminal(self) -> bool:
        return self.status in TERMINAL_ORDER_STATUSES


def _integral_contract_quantity(value: Any) -> int:
    try:
        parsed = parse_rest_decimal_value_object(value)
    except ValueError:
        raise ProductionBrokerStateError("BROKER_POSITION_QUANTITY_INVALID") from None
    if parsed != parsed.to_integral_value():
        raise ProductionBrokerStateError("BROKER_POSITION_QUANTITY_INVALID")
    return int(parsed)


def broker_positions(
    account: Any,
    *,
    finam_to_instrument: dict[str, str],
) -> dict[str, int]:
    if not isinstance(account, dict) or not isinstance(account.get("positions"), list):
        raise ProductionBrokerStateError("BROKER_POSITIONS_SCHEMA_INVALID")
    result = {instrument: 0 for instrument in INSTRUMENTS}
    seen: set[str] = set()
    for row in account["positions"]:
        if not isinstance(row, dict):
            raise ProductionBrokerStateError("BROKER_POSITIONS_SCHEMA_INVALID")
        symbol = row.get("symbol")
        if not isinstance(symbol, str) or not symbol:
            raise ProductionBrokerStateError("BROKER_POSITIONS_SCHEMA_INVALID")
        quantity = _integral_contract_quantity(row.get("quantity"))
        if quantity == 0:
            continue
        instrument = finam_to_instrument.get(symbol)
        if instrument is None:
            raise ProductionBrokerStateError("UNEXPECTED_NON_N4_BROKER_POSITION")
        if instrument in seen:
            raise ProductionBrokerStateError("DUPLICATE_BROKER_POSITION")
        seen.add(instrument)
        result[instrument] = quantity
    return result


def broker_realized_basis(account: Any) -> Decimal:
    if not isinstance(account, dict):
        raise ProductionBrokerStateError("BROKER_ACCOUNT_SCHEMA_INVALID")
    try:
        equity = parse_rest_decimal_value_object(account.get("equity"), positive=True)
        unrealized = parse_rest_decimal_value_object(account.get("unrealized_profit"))
    except ValueError:
        raise ProductionBrokerStateError("BROKER_REALIZED_EQUITY_INVALID") from None
    basis = equity - unrealized
    if not basis.is_finite() or basis <= 0:
        raise ProductionBrokerStateError("BROKER_REALIZED_EQUITY_INVALID")
    return basis


def normalize_transaction_category(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise ProductionBrokerStateError("BROKER_TRANSACTION_CATEGORY_INVALID")
    category = value.upper().removeprefix("TRANSACTION_CATEGORY_")
    if category not in DOCUMENTED_TRANSACTION_CATEGORIES:
        raise ProductionBrokerStateError("BROKER_TRANSACTION_CATEGORY_INVALID")
    return category


def require_no_external_cash_flows(response: Any) -> int:
    if not isinstance(response, dict) or not isinstance(response.get("transactions"), list):
        raise ProductionBrokerStateError("BROKER_TRANSACTIONS_SCHEMA_INVALID")
    rows = response["transactions"]
    # FINAM exposes no pagination cursor here. Reaching the requested hard
    # limit makes completeness unknowable and therefore blocks production.
    if len(rows) >= 1000:
        raise ProductionBrokerStateError("BROKER_TRANSACTIONS_LIMIT_REACHED")
    checked = 0
    for row in rows:
        if not isinstance(row, dict):
            raise ProductionBrokerStateError("BROKER_TRANSACTIONS_SCHEMA_INVALID")
        category = normalize_transaction_category(row.get("transaction_category"))
        if category in EXTERNAL_CASH_FLOW_CATEGORIES:
            raise ProductionBrokerStateError("UNEXPLAINED_EXTERNAL_CASH_FLOW")
        checked += 1
    return checked


def parse_orders(response: Any) -> list[BrokerOrder]:
    rows = response.get("orders") if isinstance(response, dict) else response
    if not isinstance(rows, list):
        raise ProductionBrokerStateError("BROKER_ORDERS_SCHEMA_INVALID")
    parsed: list[BrokerOrder] = []
    ids: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ProductionBrokerStateError("BROKER_ORDERS_SCHEMA_INVALID")
        order_id = row.get("order_id")
        if not isinstance(order_id, str) or not order_id or order_id in ids:
            raise ProductionBrokerStateError("BROKER_ORDER_ID_INVALID")
        ids.add(order_id)
        try:
            status = normalize_order_status(row.get("status"))
        except ValueError:
            raise ProductionBrokerStateError("BROKER_ORDER_STATUS_INVALID") from None
        normal = row.get("order")
        sltp = row.get("sltp_order")
        has_normal = isinstance(normal, dict) and bool(normal)
        has_sltp = isinstance(sltp, dict) and bool(sltp)
        if has_normal == has_sltp:
            raise ProductionBrokerStateError("BROKER_ORDER_PAYLOAD_INVALID")
        payload = normal if has_normal else sltp
        kind = "ORDER" if has_normal else "SLTP"
        symbol = payload.get("symbol")
        side = payload.get("side")
        client_id = payload.get("client_order_id")
        comment = payload.get("comment")
        if not isinstance(symbol, str) or not symbol:
            raise ProductionBrokerStateError("BROKER_ORDER_PAYLOAD_INVALID")
        if side is not None and not isinstance(side, str):
            raise ProductionBrokerStateError("BROKER_ORDER_PAYLOAD_INVALID")
        if client_id in (None, ""):
            client_id = None
        elif not isinstance(client_id, str):
            raise ProductionBrokerStateError("BROKER_ORDER_PAYLOAD_INVALID")
        if comment in (None, ""):
            comment = None
        elif not isinstance(comment, str):
            raise ProductionBrokerStateError("BROKER_ORDER_PAYLOAD_INVALID")
        parsed.append(BrokerOrder(
            order_id, status, kind, symbol, side, client_id, comment, payload
        ))
    return parsed


def order_for_intent(orders: list[BrokerOrder], idempotency_key: str) -> BrokerOrder | None:
    client_id = compact_client_order_id(idempotency_key)
    matches = [
        order for order in orders
        if order.client_order_id == client_id or order.comment == idempotency_key
    ]
    if len(matches) > 1:
        # One Stage 8 intent is allowed to identify exactly one broker order.
        # Historical terminal rows with the same client id would make the
        # authority ambiguous and must be handled by an operator.
        raise ProductionBrokerStateError("BROKER_INTENT_ORDER_AMBIGUOUS")
    return matches[0] if matches else None


def _decimal_field(payload: dict[str, Any], key: str) -> Decimal:
    try:
        return parse_rest_value_object(payload.get(key))
    except ValueError:
        raise ProductionBrokerStateError("BROKER_SLTP_PAYLOAD_INVALID") from None


def active_protection_for_position(
    orders: list[BrokerOrder],
    position: dict[str, Any],
) -> list[str]:
    try:
        trade_id = str(position["trade_id"])
        symbol = str(position["finam_symbol"])
        direction = str(position["direction"])
        current_stop = Decimal(str(position["protective_stop_price"]))
        current_broker_id = str(position["protective_stop_broker_order_id"])
    except (KeyError, ValueError):
        raise ProductionBrokerStateError("LOCAL_PROTECTIVE_STOP_STATE_INVALID") from None
    if direction not in {"LONG", "SHORT"}:
        raise ProductionBrokerStateError("LOCAL_PROTECTIVE_STOP_STATE_INVALID")
    expected_side = "SIDE_SELL" if direction == "LONG" else "SIDE_BUY"
    prefix = f"stage8.12:{trade_id}:stop:"
    related = [
        order for order in orders
        if order.kind == "SLTP"
        and order.active
        and isinstance(order.comment, str)
        and order.comment.startswith(prefix)
    ]
    if not related:
        raise ProductionBrokerStateError("BROKER_PROTECTIVE_STOP_MISSING")

    active_ids: list[str] = []
    current_seen = False
    for order in related:
        payload = order.payload
        if (
            order.symbol != symbol
            or order.side != expected_side
            or payload.get("sl_qty_measure") != "SLTP_QTY_MEASURE_PERCENT"
            or _decimal_field(payload, "quantity_sl") != Decimal("100")
        ):
            raise ProductionBrokerStateError("BROKER_PROTECTIVE_STOP_INVALID")
        stop_price = _decimal_field(payload, "sl_price")
        if direction == "LONG" and stop_price > current_stop:
            raise ProductionBrokerStateError("BROKER_PROTECTIVE_STOP_UNEXPECTEDLY_TIGHTER")
        if direction == "SHORT" and stop_price < current_stop:
            raise ProductionBrokerStateError("BROKER_PROTECTIVE_STOP_UNEXPECTEDLY_TIGHTER")
        if order.order_id == current_broker_id:
            if stop_price != current_stop:
                raise ProductionBrokerStateError("BROKER_CURRENT_STOP_PRICE_MISMATCH")
            current_seen = True
        active_ids.append(order.order_id)
    if not current_seen:
        raise ProductionBrokerStateError("BROKER_CURRENT_PROTECTIVE_STOP_MISSING")
    return sorted(active_ids)


def require_no_unknown_active_orders(
    orders: list[BrokerOrder],
    known_intents: list[dict[str, Any]],
) -> None:
    allowed_client_ids: set[str] = set()
    allowed_comments: set[str] = set()
    for row in known_intents:
        key = row.get("idempotency_key")
        if not isinstance(key, str) or not key:
            raise ProductionBrokerStateError("LOCAL_INTENT_IDENTITY_INVALID")
        allowed_client_ids.add(compact_client_order_id(key))
        allowed_comments.add(key)
    for order in orders:
        if not order.active:
            continue
        if (
            order.client_order_id not in allowed_client_ids
            and order.comment not in allowed_comments
        ):
            raise ProductionBrokerStateError("UNEXPECTED_ACTIVE_BROKER_ORDER")
