"""R070 staged single SL+TP6 broker contract; verification only, NO API calls.

Reuses H1 protective stop payload and FINAM broker order view. Does not
replace an active SLTP, submit orders, touch SQLite or enable LIVE.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from fractions import Fraction
from hashlib import sha256
import json

from TradingSystemLab.stage8_robot.broker import compact_client_order_id
from TradingSystemLab.stage8_robot.production_broker_state import (
    BrokerOrderView, _validate_production_sltp, ProductionBrokerStateError,
)
from TradingSystemLab.stage8_robot.production_runtime import RuntimeAction
from TradingSystemLab.stage8_robot.protective_stop_contract import (
    percent_position_stop_payload, ProtectiveStopContractError,
)
from .tp6_protect3 import TP6Levels, TP6Protect3Unsafe, sltp_tp6_fields, levels_from_finam_fills


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
    # A second LIVE regular order may be a triggered SL/TP child or an
    # unsettled close. Its presence cannot be interpreted as one fully
    # protected linked position, even when one WATCHING SLTP also exists.
    active_symbol_orders = [
        o for o in orders if o.active and o.symbol == wire.get("symbol")
    ]
    if len(active_symbol_orders) != 1 or active_symbol_orders[0] != order:
        raise TP6Protect3Unsafe("R070_SLTP_ACTIVE_CHILD_OR_OTHER_ORDER_UNVERIFIED")
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


def prepare_r070_tp6_from_h1_full_fills(
    *, action: RuntimeAction, history: dict,
    entry_orders: tuple[BrokerOrderView, ...], entry_broker_order_id: str,
    observed_position: int, tick: Decimal,
) -> tuple[TP6Levels, dict]:
    """OFFLINE-only H1 GET /trades -> exact VWAP -> single linked SL/TP draft.

    Reuses H1's order-linked inspect_entry_fills() result, never a planned
    NEXT_OPEN, an order ACK alone or arbitrary fills. The historical H1
    parser labels this evidence DIAGNOSTIC_ONLY, so the returned fields are
    NOT permitted to be handed to the current live submit_protection_once().
    No broker calls, runtime state, cancel or order endpoint exist here.
    """
    if (not isinstance(action, RuntimeAction) or
            action.kind != "PROTECTIVE_STOP_INSTALL"
            or not isinstance(action.trade_id, str) or not action.trade_id
            or not isinstance(entry_broker_order_id, str) or not entry_broker_order_id
            or not isinstance(entry_orders, tuple)
            or any(not isinstance(o, BrokerOrderView) for o in entry_orders)
            or type(observed_position) is not int
            or observed_position != (action.quantity if action.direction == "LONG"
                                    else -action.quantity)):
        raise TP6Protect3Unsafe("R070_FILL_ORDER_OR_POSITION_UNVERIFIED")
    expected_entry_client = compact_client_order_id(action.trade_id)
    entry = [o for o in entry_orders
             if o.order_id == entry_broker_order_id
             or o.client_order_id == expected_entry_client]
    if (len(entry) != 1
            or entry[0].order_id != entry_broker_order_id
            or entry[0].client_order_id != expected_entry_client
            or entry[0].kind != "REGULAR"
            or entry[0].symbol != action.finam_symbol
            or entry[0].side != ("SIDE_BUY" if action.direction == "LONG" else "SIDE_SELL")
            or any(o.active and o.symbol == action.finam_symbol
                   for o in entry_orders)):
        raise TP6Protect3Unsafe("R070_ENTRY_BROKER_IDENTITY_OR_ACTIVE_ORDER_INVALID")
    try:
        qty = Decimal(str(entry[0].request["quantity"]["value"]))
        if qty != action.quantity:
            raise TP6Protect3Unsafe("R070_ENTRY_REQUEST_QUANTITY_MISMATCH")
        if (not isinstance(history, dict)
                or history.get("authority_scope") !=
                "READONLY_DIAGNOSTIC_ONLY_NO_RUNTIME_HANDOFF"
                or history.get("quantity_observation") != "FULL_REQUEST_MATCHED"
                or type(history.get("matched_quantity")) is not int
                or history["matched_quantity"] != action.quantity):
            raise TP6Protect3Unsafe("R070_H1_FILL_AUTHORITY_NOT_FULL")
        facts = history["matched_unique_fills"]
        if not isinstance(facts, list) or not facts:
            raise TP6Protect3Unsafe("R070_H1_FILLS_MISSING")
        if (any(not isinstance(f, dict)
                or not isinstance(f.get("trade_id_sha256"), str)
                or len(f["trade_id_sha256"]) != 64
                or type(f.get("quantity")) is not int
                or f["quantity"] <= 0
                or not isinstance(f.get("price"), str)
                for f in facts)
                or len({f["trade_id_sha256"] for f in facts}) != len(facts)):
            raise TP6Protect3Unsafe("R070_H1_FILL_SET_INVALID")
        digest = sha256(json.dumps(facts, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        if history.get("fill_set_sha256") != digest:
            raise TP6Protect3Unsafe("R070_H1_FILL_SET_HASH_INVALID")
        notional = sum((Fraction(f["price"]) * f["quantity"] for f in facts), Fraction(0))
        matched_qty = sum(f["quantity"] for f in facts)
        weighted = history.get("weighted_price_exact")
        if (matched_qty != action.quantity
                or not isinstance(weighted, dict)
                or notional / matched_qty !=
                Fraction(int(weighted["numerator"]), int(weighted["denominator"]))):
            raise TP6Protect3Unsafe("R070_H1_FILL_VWAP_INCONSISTENT")
        levels = levels_from_finam_fills(
            direction=action.direction,
            fills=[(f["quantity"], f["price"]) for f in facts],
            initial_stop=action.stop_price, tick=tick)
        return levels, prepare_r070_linked_sltp_draft(action=action, levels=levels)
    except (KeyError, ValueError, TypeError, ZeroDivisionError,
            InvalidOperation, OverflowError) as exc:
        raise TP6Protect3Unsafe("R070_H1_FILL_PROOF_INVALID") from exc
