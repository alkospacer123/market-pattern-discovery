"""R070 staged single SL+TP6 broker contract; verification only, NO API calls.

Reuses H1 protective stop payload and FINAM broker order view. Does not
replace an active SLTP, submit orders, touch SQLite or enable LIVE.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from TradingSystemLab.stage8_robot.broker import compact_client_order_id
from TradingSystemLab.stage8_robot.production_broker_state import (
    BrokerOrderView, _validate_production_sltp, ProductionBrokerStateError,
)
from TradingSystemLab.stage8_robot.production_runtime import RuntimeAction
from TradingSystemLab.stage8_robot.protective_stop_contract import (
    percent_position_stop_payload, ProtectiveStopContractError,
)
from .tp6_protect3 import TP6Levels, TP6Protect3Unsafe, sltp_tp6_fields


def prepare_r070_linked_sltp_draft(
    *, action: RuntimeAction, levels: TP6Levels,
) -> dict:
    """Build the one H1 100%-SLTP with R070 TP6, *without* sending it.

    Caller must have independent FINAM /trades order-linked proof and
    broker position proof. A single linked SL+TP replaces two independent
    exit orders, not the old stop already protecting an active position.
    """
    if (not isinstance(action, RuntimeAction) or not isinstance(levels, TP6Levels)
            or action.kind != "PROTECTIVE_STOP_INSTALL"
            or action.direction != levels.direction
            or type(action.quantity) is not int or action.quantity != levels.fill_quantity
            or action.stop_price != levels.initial_stop
            or not isinstance(action.idempotency_key, str)
            or len(action.idempotency_key) > 128):
        raise TP6Protect3Unsafe("R070_SLTP_FILL_OR_STOP_SCOPE_INVALID")
    try:
        wire = percent_position_stop_payload(action)
    except (ProtectiveStopContractError, ValueError, TypeError) as exc:
        raise TP6Protect3Unsafe("R070_H1_SLTP_DRAFT_INVALID") from exc
    wire.pop("schema_id", None)
    wire["client_order_id"] = compact_client_order_id(action.idempotency_key)
    wire.update(sltp_tp6_fields(levels))
    if (wire.get("quantity_sl") != {"value": "100"}
            or wire.get("sl_qty_measure") != "SLTP_QTY_MEASURE_PERCENT"
            or wire.get("quantity_tp") != {"value": "100"}
            or wire.get("tp_qty_measure") != "SLTP_QTY_MEASURE_PERCENT"):
        raise TP6Protect3Unsafe("R070_SLTP_PERCENT_COVERAGE_INVALID")
    return wire


def verify_r070_linked_sltp(
    *, observed_position: int, orders: tuple[BrokerOrderView, ...],
    levels: TP6Levels, wire: dict, expected_broker_order_id: str,
) -> BrokerOrderView:
    """A broker ACK alone never proves SL and TP both protect the position.

    Require EXACT one active SLTP by broker ID, scope, side, prices and
    both 100%-of-position measures, with no conflicting active SLTP.
    Reuse H1 WATCHING missing-client-id fallback, never guess identity.
    """
    expected_position = levels.fill_quantity if levels.direction == "LONG" else -levels.fill_quantity
    if (type(observed_position) is not int or observed_position != expected_position
            or not isinstance(expected_broker_order_id, str)
            or not expected_broker_order_id
            or not isinstance(wire, dict)
            or not isinstance(orders, tuple)
            or any(not isinstance(order, BrokerOrderView) for order in orders)):
        raise TP6Protect3Unsafe("R070_SLTP_BROKER_STATE_UNVERIFIED")
    matching = [
        o for o in orders if o.active and o.kind == "SLTP"
        and o.symbol == wire.get("symbol")
    ]
    if len(matching) != 1:
        raise TP6Protect3Unsafe("R070_SLTP_ONE_ACTIVE_LINKED_ORDER_REQUIRED")
    order = matching[0]
    if (order.order_id != expected_broker_order_id
            or order.symbol != wire.get("symbol")
            or order.side != wire.get("side")
            or order.comment != wire.get("comment")
            or not (order.client_order_id == wire.get("client_order_id")
                    or (order.status == "WATCHING" and order.client_order_id == ""))
            or order.request.get("symbol") != wire.get("symbol")):
        raise TP6Protect3Unsafe("R070_SLTP_BROKER_IDENTITY_MISMATCH")
    try:
        _validate_production_sltp(order)
        for name in ("sl_price", "tp_price", "quantity_sl", "quantity_tp"):
            expected = Decimal(str(wire[name]["value"]))
            actual = Decimal(str(order.request[name]["value"]))
            if not expected.is_finite() or actual != expected:
                raise TP6Protect3Unsafe("R070_SLTP_PRICE_OR_COVERAGE_MISMATCH")
        for name in ("sl_qty_measure", "tp_qty_measure", "valid_before"):
            if order.request.get(name) != wire.get(name):
                raise TP6Protect3Unsafe("R070_SLTP_PERCENT_OR_VALIDITY_MISMATCH")
        if (Decimal(str(order.request["sl_price"]["value"])) != levels.initial_stop
                or Decimal(str(order.request["tp_price"]["value"])) != levels.take_profit):
            raise TP6Protect3Unsafe("R070_SLTP_6R_LEVELS_CHANGED")
    except (KeyError, TypeError, ValueError, InvalidOperation,
            ProductionBrokerStateError) as exc:
        raise TP6Protect3Unsafe("R070_SLTP_BROKER_PRICE_FIELDS_UNVERIFIED") from exc
    return order
