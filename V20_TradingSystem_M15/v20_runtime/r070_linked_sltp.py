"""R070 linked SLTP proof and isolated Protect3 candidate-only orchestration.

Current LIVE is unchanged. OFFLINE candidate accepts a separately injected
fake broker transport only; the actual FINAM API is rejected by identity.
"""
from __future__ import annotations

from dataclasses import dataclass
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


@dataclass(frozen=True)
class R070InitialProtectionChoice:
    """Candidate decision only; never represents permission for an API POST."""
    status: str
    levels: TP6Levels | None = None
    wire: dict | None = None


def choose_r070_initial_protection(
    *, action: RuntimeAction, history: dict,
    entry_orders: tuple[BrokerOrderView, ...], entry_broker_order_id: str,
    observed_position: int, tick: Decimal,
    existing_broker_stop_id: str | None = None,
    existing_proved_stop_price: Decimal | None = None,
) -> R070InitialProtectionChoice:
    """OFFLINE admission of linked TP6 versus mandatory original protection.

    One V20 market entry can fill in parts. In that case the original
    immediate 100%-of-position SL is mandatory and takes precedence over
    waiting for TP6. If a verified SLTP already protects a position, NEVER
    submit another 100% SLTP; TP6 addition would require a broker-proven safe
    amendment, currently blocked by FINAM clarification.

    No FINAM API, SQLite, callbacks or write-side operations in this function.
    The return value may be used for diagnostics/candidate tests only.
    """
    if (not isinstance(action, RuntimeAction)
            or action.kind != "PROTECTIVE_STOP_INSTALL"
            or not isinstance(action.trade_id, str) or not action.trade_id
            or type(action.quantity) is not int or action.quantity <= 0
            or not isinstance(entry_broker_order_id, str) or not entry_broker_order_id
            or not isinstance(entry_orders, tuple)
            or any(not isinstance(o, BrokerOrderView) for o in entry_orders)
            or type(observed_position) is not int
            or observed_position != (action.quantity if action.direction == "LONG"
                                    else -action.quantity)):
        raise TP6Protect3Unsafe("R070_INITIAL_PROTECTION_POSITION_INVALID")
    entry = [o for o in entry_orders if o.order_id == entry_broker_order_id
             or o.client_order_id == compact_client_order_id(action.trade_id)]
    if (len(entry) != 1
            or entry[0].order_id != entry_broker_order_id
            or entry[0].client_order_id != compact_client_order_id(action.trade_id)
            or entry[0].kind != "REGULAR"
            or entry[0].symbol != action.finam_symbol
            or entry[0].side != ("SIDE_BUY" if action.direction == "LONG" else "SIDE_SELL")):
        raise TP6Protect3Unsafe("R070_INITIAL_PROTECTION_ENTRY_IDENTITY_INVALID")
    try:
        requested = Decimal(str(entry[0].request["quantity"]["value"]))
        if (requested <= 0 or requested != requested.to_integral_value()
                or requested < action.quantity
                or not isinstance(history, dict)
                or history.get("authority_scope") != "READONLY_DIAGNOSTIC_ONLY_NO_RUNTIME_HANDOFF"
                or type(history.get("matched_quantity")) is not int
                or history["matched_quantity"] != action.quantity
                or history.get("quantity_observation") != (
                    "FULL_REQUEST_MATCHED" if requested == action.quantity
                    else "PARTIAL_REQUEST_MATCHED")):
            raise TP6Protect3Unsafe("R070_INITIAL_PROTECTION_FILLS_UNVERIFIED")
        facts = history["matched_unique_fills"]
        if (not isinstance(facts, list) or not facts
                or any(not isinstance(f, dict)
                       or type(f.get("quantity")) is not int or f["quantity"] <= 0
                       or not isinstance(f.get("price"), str)
                       or not isinstance(f.get("trade_id_sha256"), str)
                       or len(f["trade_id_sha256"]) != 64 for f in facts)
                or sum(f["quantity"] for f in facts) != action.quantity
                or len(set(f["trade_id_sha256"] for f in facts)) != len(facts)
                or sha256(json.dumps(facts, sort_keys=True, separators=(",", ":")).encode()
                          ).hexdigest() != history.get("fill_set_sha256")):
            raise TP6Protect3Unsafe("R070_INITIAL_PROTECTION_FILL_SET_UNVERIFIED")
        # Match H1's exact VWAP numerator/denominator even for partial fills.
        n = sum((Fraction(f["price"]) * f["quantity"] for f in facts), Fraction(0))
        exact = Fraction(int(history["weighted_price_exact"]["numerator"]),
                         int(history["weighted_price_exact"]["denominator"]))
        if n / action.quantity != exact:
            raise TP6Protect3Unsafe("R070_INITIAL_PROTECTION_VWAP_UNVERIFIED")
    except (TypeError, ValueError, KeyError, ZeroDivisionError,
            InvalidOperation, OverflowError) as exc:
        raise TP6Protect3Unsafe("R070_INITIAL_PROTECTION_FILL_PROOF_INVALID") from exc

    stops = [o for o in entry_orders
             if o.active and o.kind == "SLTP" and o.symbol == action.finam_symbol]
    if existing_broker_stop_id is not None:
        if (not isinstance(existing_broker_stop_id, str)
                or not existing_broker_stop_id
                or existing_proved_stop_price is None
                or len(stops) != 1
                or stops[0].order_id != existing_broker_stop_id):
            raise TP6Protect3Unsafe("R070_EXISTING_STOP_ID_UNVERIFIED")
        stop = stops[0]
        try:
            _validate_production_sltp(stop)
            price = Decimal(str(stop.request["sl_price"]["value"]))
            original = Decimal(str(existing_proved_stop_price))
            if (price != original or not price.is_finite()
                    or stop.side != ("SIDE_SELL" if action.direction == "LONG" else "SIDE_BUY")):
                raise TP6Protect3Unsafe("R070_EXISTING_STOP_PRICE_OR_SIDE_UNVERIFIED")
        except (KeyError, TypeError, ValueError, InvalidOperation,
                ProductionBrokerStateError) as exc:
            raise TP6Protect3Unsafe("R070_EXISTING_STOP_PROOF_INVALID") from exc
        if any(o.active and o.symbol == action.finam_symbol
               and o.order_id not in {entry_broker_order_id, existing_broker_stop_id}
               for o in entry_orders):
            raise TP6Protect3Unsafe("R070_EXISTING_STOP_CONFLICTING_ORDER")
        return R070InitialProtectionChoice(
            "KEEP_VERIFIED_ORIGINAL_STOP_NO_TP6_REPLACEMENT")
    if existing_proved_stop_price is not None or stops:
        raise TP6Protect3Unsafe("R070_UNKNOWN_ACTIVE_STOP_NO_SECOND_SLTP")
    if any(o.active and o.symbol == action.finam_symbol
           and o.order_id != entry_broker_order_id for o in entry_orders):
        raise TP6Protect3Unsafe("R070_OTHER_ACTIVE_ORDER_UNVERIFIED")
    if requested > action.quantity:
        # The actual V20 LIVE handler already installs the 100% initial stop
        # on first partial fill. Do not wait, invent a TP, or create an order.
        return R070InitialProtectionChoice("ORIGINAL_V20_SL_REQUIRED_PARTIAL_FILL")
    levels, wire = prepare_r070_tp6_from_h1_full_fills(
        action=action, history=history, entry_orders=entry_orders,
        entry_broker_order_id=entry_broker_order_id,
        observed_position=observed_position, tick=tick)
    return R070InitialProtectionChoice("SINGLE_LINKED_SL_TP6_DRAFT_ONLY", levels, wire)


def stage_r070_protection_from_v20(
    *, journal, reader, snapshot, entry_key: str, now,
) -> R070InitialProtectionChoice:
    """READONLY candidate handoff from existing V20 ledger/fills to TP6 choice.

    Reuse V20's actual submission identity, H1 order-linked /trades parser,
    immutable risk reservation, and exact project_stop(2*ATR).
    This does NOT alter the installed worker or dispatch a broker write.
    A previously sent stop is never amended/replaced by this function.
    """
    from datetime import datetime
    from TradingSystemLab.stage8_robot.execution_grid import project_stop
    from TradingSystemLab.stage8_robot.production_runtime import _load_registry
    from .account_risk import RiskReservation
    from .finam_execution import (
        LiveAccountSnapshot, V20FinamReadAdapter, V20TradeJournal,
    )

    if (not isinstance(journal, V20TradeJournal)
            or not isinstance(reader, V20FinamReadAdapter)
            or not isinstance(snapshot, LiveAccountSnapshot)
            or not isinstance(entry_key, str) or not entry_key.startswith(
                "v20:" + reader.robot_id + ":" + reader.account_hash[:16] + ":")
            or journal.robot_id != reader.robot_id
            or journal.account_hash != reader.account_hash
            or snapshot.robot_id != reader.robot_id
            or snapshot.account_hash != reader.account_hash):
        raise TP6Protect3Unsafe("R070_V20_ACCOUNT_OR_ENTRY_SCOPE_INVALID")
    reader._fresh(snapshot, now)
    entry = journal.store.intent(entry_key)
    if (not isinstance(entry, dict) or entry.get("status") not in
            {"ACK", "PARTIAL_FILL", "FILL", "RECONCILED"}
            or not isinstance(entry.get("broker_order_id"), str)
            or not entry["broker_order_id"]):
        raise TP6Protect3Unsafe("R070_V20_ENTRY_BROKER_ACK_UNVERIFIED")
    payload = entry.get("payload")
    if not isinstance(payload, dict):
        raise TP6Protect3Unsafe("R070_V20_ENTRY_PAYLOAD_INVALID")
    symbol, direction = payload.get("symbol"), payload.get("direction")
    registry = _load_registry()
    if (symbol not in registry or direction not in {"LONG", "SHORT"}
            or payload.get("finam_symbol") != registry[symbol]["finam_symbol"]
            or type(payload.get("quantity")) is not int
            or payload["quantity"] < 1):
        raise TP6Protect3Unsafe("R070_V20_ENTRY_SCOPE_INVALID")
    tick = Decimal(registry[symbol]["price_step"])
    finam_symbol = registry[symbol]["finam_symbol"]
    qty = snapshot.positions.get(finam_symbol)
    if (type(qty) is not int or qty == 0
            or (qty > 0) != (direction == "LONG")
            or abs(qty) > payload["quantity"]):
        raise TP6Protect3Unsafe("R070_V20_POSITION_BROKER_UNVERIFIED")
    reservation = RiskReservation.restore(
        journal.store.get("risk_reservations", {}).get(entry_key))
    if (reservation.entry_key != entry_key
            or reservation.account_id != reader.account_id
            or reservation.symbol != symbol or reservation.direction != direction
            or reservation.quantity != payload["quantity"]
            or reservation.price_step != tick
            or Decimal(str(payload.get("atr14"))) != reservation.atr14):
        raise TP6Protect3Unsafe("R070_V20_RISK_RESERVATION_MISMATCH")

    # Protection-first rule. A previously sent stop (including an UNCERTAIN
    # POST) never authorizes a second broker order merely to add TP6.
    stop_intent = journal.store.intent(entry_key + ":stop")
    prior = journal.store.get("protected_fill:" + entry_key)
    if stop_intent is not None or prior is not None:
        if (not isinstance(stop_intent, dict)
                or stop_intent.get("status") not in {"ACK", "RECONCILED"}
                or not isinstance(prior, dict)
                or prior.get("account_sha256") != reader.account_hash
                or prior.get("broker_order_id") != entry["broker_order_id"]
                or prior.get("broker_stop_id") != stop_intent.get("broker_order_id")
                or prior.get("broker_stop_percent") != "100"):
            raise TP6Protect3Unsafe("R070_V20_EXISTING_STOP_UNCERTAIN_NO_RETRY")
        confirmed = reader.inspect_protective_stop(
            snapshot, entry_key=entry_key, symbol=symbol,
            direction=direction, stop_price=Decimal(prior["installed_stop"]),
            now=now)
        if confirmed.order_id != prior["broker_stop_id"]:
            raise TP6Protect3Unsafe("R070_V20_EXISTING_STOP_ID_MISMATCH")
        if any(o.active and o.symbol == finam_symbol
               and o.order_id not in {
                   entry["broker_order_id"], confirmed.order_id}
               for o in snapshot.orders):
            raise TP6Protect3Unsafe("R070_V20_EXISTING_STOP_OTHER_ACTIVE_ORDER")
        return R070InitialProtectionChoice(
            "KEEP_VERIFIED_ORIGINAL_STOP_NO_TP6_REPLACEMENT")

    if any(o.active and o.kind == "SLTP" and o.symbol == finam_symbol
           for o in snapshot.orders):
        raise TP6Protect3Unsafe("R070_V20_UNKNOWN_ACTIVE_STOP_NO_RETRY")
    submitted = journal.store.get("entry_submission:" + entry_key)
    if (not isinstance(submitted, dict)
            or submitted.get("account_sha256") != reader.account_hash
            or not isinstance(submitted.get("submitted_at"), str)):
        raise TP6Protect3Unsafe("R070_V20_SUBMISSION_PROOF_MISSING")
    try:
        submitted_at = datetime.fromisoformat(submitted["submitted_at"])
        if submitted_at.tzinfo is None:
            raise ValueError("naive submission timestamp")
    except ValueError as exc:
        raise TP6Protect3Unsafe("R070_V20_SUBMISSION_TIME_INVALID") from exc
    history = reader.inspect_entry_fills(
        snapshot, entry_key=entry_key, symbol=symbol,
        direction=direction, requested_quantity=reservation.quantity,
        submitted_at=submitted_at, now=now)
    if (not isinstance(history, dict)
            or history.get("matched_quantity") != abs(qty)
            or not history.get("matched_unique_fills")):
        raise TP6Protect3Unsafe("R070_V20_FILL_HISTORY_UNVERIFIED")
    try:
        facts = history["matched_unique_fills"]
        exact = sum(
            (int(f["quantity"]) * Fraction(f["price"]) for f in facts),
            Fraction(0)) / abs(qty)
        side = 1 if direction == "LONG" else -1
        original_stop = project_stop(
            direction, exact - side * 2 * Fraction(reservation.atr14), tick)
        # Use the exact V20 entry and stop keys; NEVER generate a second ID.
        action = RuntimeAction(
            "PROTECTIVE_STOP_INSTALL", entry_key + ":stop",
            symbol, finam_symbol, direction, abs(qty), entry_key,
            None, Decimal(str(payload["reference_entry"])),
            original_stop, qty, price_step=tick)
    except (KeyError, ValueError, TypeError, ZeroDivisionError,
            InvalidOperation, OverflowError) as exc:
        raise TP6Protect3Unsafe("R070_V20_STOP_PROJECTION_UNVERIFIED") from exc
    return choose_r070_initial_protection(
        action=action, history=history, entry_orders=snapshot.orders,
        entry_broker_order_id=entry["broker_order_id"],
        observed_position=qty, tick=tick)


def verify_r070_tp6_after_restart(
    *, journal, reader, snapshot, entry_key: str, now,
) -> BrokerOrderView:
    """READONLY proof of R070 linked TP6 using *existing* V20/H1 durable data.

    Rebuild the expected TP6 wire from strict H1 SQLite persisted fills, the
    original 2xATR executable stop and the original :stop intent. Compare the
    actual current FINAM order and quantity. No extra history /trades GET,
    durable write, stop replacement, duplicate order, or LIVE hook.

    This is a candidate verifier, NOT authorization to modify FINAM orders.
    """
    from fractions import Fraction
    from TradingSystemLab.stage8_robot.execution_grid import project_stop
    from TradingSystemLab.stage8_robot.production_runtime import _load_registry
    from .account_risk import RiskReservation
    from .finam_execution import (
        LiveAccountSnapshot, V20FinamReadAdapter, V20TradeJournal,
    )

    if (not isinstance(journal, V20TradeJournal)
            or not isinstance(reader, V20FinamReadAdapter)
            or not isinstance(snapshot, LiveAccountSnapshot)
            or not isinstance(entry_key, str)
            or not entry_key.startswith(
                "v20:" + reader.robot_id + ":" + reader.account_hash[:16] + ":")
            or journal.robot_id != reader.robot_id
            or journal.account_hash != reader.account_hash
            or snapshot.robot_id != reader.robot_id
            or snapshot.account_hash != reader.account_hash):
        raise TP6Protect3Unsafe("R070_RESTART_ACCOUNT_OR_ENTRY_INVALID")
    reader._fresh(snapshot, now)
    entry = journal.store.intent(entry_key)
    stop_intent = journal.store.intent(entry_key + ":stop")
    proof = journal.store.get("protected_fill:" + entry_key)
    if (not isinstance(entry, dict) or entry.get("status") != "RECONCILED"
            or not isinstance(entry.get("broker_order_id"), str)
            or not entry["broker_order_id"]
            or not isinstance(stop_intent, dict)
            or stop_intent.get("status") not in {"ACK", "RECONCILED"}
            or not isinstance(stop_intent.get("broker_order_id"), str)
            or not stop_intent["broker_order_id"]
            or not isinstance(proof, dict)
            or proof.get("account_sha256") != reader.account_hash
            or proof.get("broker_order_id") != entry["broker_order_id"]
            or proof.get("broker_stop_id") != stop_intent["broker_order_id"]
            or proof.get("broker_stop_percent") != "100"
            or not isinstance(proof.get("risk_assessment"), dict)
            or proof["risk_assessment"].get("status") != "PASS"
            or proof["risk_assessment"].get("stop_conforms") is not True):
        raise TP6Protect3Unsafe("R070_RESTART_DURABLE_SEALED_PROOF_INVALID")
    payload = entry.get("payload")
    wire_stored = stop_intent.get("payload")
    if (not isinstance(payload, dict)
            or not isinstance(wire_stored, dict)
            or wire_stored.get("kind") != "STOP"
            or wire_stored.get("entry_key") != entry_key
            or wire_stored.get("account_sha256") != reader.account_hash
            or not isinstance(wire_stored.get("wire"), dict)):
        raise TP6Protect3Unsafe("R070_RESTART_STOP_WIRE_MISSING")
    symbol, direction = payload.get("symbol"), payload.get("direction")
    registry = _load_registry()
    if (symbol not in registry or direction not in {"LONG", "SHORT"}
            or payload.get("finam_symbol") != registry[symbol]["finam_symbol"]
            or not isinstance(payload.get("quantity"), int)
            or type(payload["quantity"]) is not int or payload["quantity"] <= 0):
        raise TP6Protect3Unsafe("R070_RESTART_INSTRUMENT_INVALID")
    tick = Decimal(registry[symbol]["price_step"])
    finam_symbol = registry[symbol]["finam_symbol"]
    qty = snapshot.positions.get(finam_symbol)
    expected_qty = payload["quantity"]
    if (type(qty) is not int
            or qty != (expected_qty if direction == "LONG" else -expected_qty)
            or proof.get("filled_quantity") != expected_qty
            or wire_stored.get("observed_position_quantity") != qty):
        raise TP6Protect3Unsafe("R070_RESTART_POSITION_NOT_FULL")
    reservation = RiskReservation.restore(
        journal.store.get("risk_reservations", {}).get(entry_key))
    if (reservation.entry_key != entry_key
            or reservation.account_id != reader.account_id
            or reservation.quantity != expected_qty
            or reservation.symbol != symbol or reservation.direction != direction
            or reservation.price_step != tick
            or reservation.atr14 != Decimal(str(payload.get("atr14")))):
        raise TP6Protect3Unsafe("R070_RESTART_RISK_RESERVATION_INVALID")

    fills = journal.store.fills_for_order(entry["broker_order_id"])
    if not isinstance(fills, list) or not fills:
        raise TP6Protect3Unsafe("R070_RESTART_DURABLE_FILLS_MISSING")
    identities = set()
    total = 0
    money = Fraction(0)
    try:
        for f in fills:
            if (not isinstance(f, dict) or f.get("trade_id") != entry_key
                    or f.get("entry_key") != entry_key
                    or f.get("account_sha256") != reader.account_hash
                    or f.get("broker_order_id") != entry["broker_order_id"]
                    or not isinstance(f.get("broker_trade_id_sha256"), str)
                    or len(f["broker_trade_id_sha256"]) != 64
                    or f.get("fill_id") != (
                        "finam:" + reader.account_hash + ":" +
                        f["broker_trade_id_sha256"])
                    or f["fill_id"] in identities
                    or type(f.get("quantity")) not in {int, str}):
                raise TP6Protect3Unsafe("R070_RESTART_DURABLE_FILL_IDENTITY_INVALID")
            identities.add(f["fill_id"])
            q = int(f["quantity"])
            if q <= 0 or str(q) != str(f["quantity"]):
                raise TP6Protect3Unsafe("R070_RESTART_FILL_QUANTITY_INVALID")
            price = Fraction(f["price"])
            if price <= 0:
                raise TP6Protect3Unsafe("R070_RESTART_FILL_PRICE_INVALID")
            total += q
            money += q * price
        if total != expected_qty or money / total != Fraction(proof["average_exact"]):
            raise TP6Protect3Unsafe("R070_RESTART_FILL_VWAP_OR_QUANTITY_CHANGED")
        stop = Decimal(str(proof["installed_stop"]))
        side = 1 if direction == "LONG" else -1
        if stop != project_stop(
            direction, money / total - side * 2 * Fraction(reservation.atr14),
            tick):
            raise TP6Protect3Unsafe("R070_RESTART_STOP_NOT_FROZEN_2ATR")
        # Durable fill prices stored as decimals; calculate TP without
        # rounding an exact fractional average twice.
        levels = levels_from_finam_fills(
            direction=direction,
            fills=[(int(f["quantity"]), f["price"]) for f in fills],
            initial_stop=stop, tick=tick)
        action = RuntimeAction(
            "PROTECTIVE_STOP_INSTALL", entry_key + ":stop", symbol,
            finam_symbol, direction, expected_qty, entry_key, None,
            Decimal(str(payload["reference_entry"])), stop, qty,
            price_step=tick)
        expected_wire = prepare_r070_linked_sltp_draft(
            action=action, levels=levels)
    except (TypeError, KeyError, ValueError, InvalidOperation,
            OverflowError, ZeroDivisionError) as exc:
        raise TP6Protect3Unsafe("R070_RESTART_DURABLE_MATH_INVALID") from exc
    if wire_stored["wire"] != expected_wire:
        raise TP6Protect3Unsafe("R070_RESTART_STOP_INTENT_NOT_LINKED_TP6")
    return verify_r070_linked_sltp(
        observed_position=qty, orders=snapshot.orders,
        levels=levels, wire=expected_wire,
        expected_broker_order_id=stop_intent["broker_order_id"])



# 17.11.2026 — explicitly user-authorized CANCEL FIRST -> NEW SLTP plan.
# A plan/proof only. No API writes, LIVE hook or implicit risk acceptance.
@dataclass(frozen=True)
class R070Protect3CancelFirstPlan:
    """A deliberate unprotected interval exists between cancel and new ACK."""
    old_order_id: str
    symbol: str
    direction: str
    position_quantity: int
    old_wire: dict
    new_wire: dict
    stop_1r: Decimal
    tp_6r: Decimal


def review_r070_protect3_m15_boundary(
    *, levels: TP6Levels, boundary, entry_open_msk, broker_stop_proved: bool,
    currently_proved_stop,
):
    """Read-only R070 +3R witness from FINAM's existing CLOSED M15 boundary.

    A broker-verified stop AND the completed candle are prerequisites.
    Never use a forming M15 High/Low or a historical candle before entry.
    The witnessed next-bar Open is NOT a fresh executable quote and cannot
    alone authorize cancellation of a real SLTP. Returns a pure review only.
    """
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    from .finam_execution import V20M15Boundary
    from .tp6_protect3 import ProtectionReview, review_completed_m15

    if (not isinstance(levels, TP6Levels)
            or not isinstance(boundary, V20M15Boundary)
            or not isinstance(entry_open_msk, datetime)
            or entry_open_msk.tzinfo is not None
            or not isinstance(boundary.at_msk, datetime)
            or boundary.at_msk.tzinfo is not None
            or boundary.at_msk.second != 0
            or boundary.at_msk.microsecond != 0
            or boundary.at_msk.minute % 15
            or not isinstance(broker_stop_proved, bool)
            or boundary.observed_at_utc.tzinfo is None):
        raise TP6Protect3Unsafe("R070_PROTECT3_M15_BOUNDARY_SCOPE_INVALID")
    observed_msk = boundary.observed_at_utc.astimezone(
        ZoneInfo("Europe/Moscow")).replace(tzinfo=None)
    if not timedelta(0) <= observed_msk - boundary.at_msk <= timedelta(seconds=60):
        raise TP6Protect3Unsafe("R070_PROTECT3_M15_BOUNDARY_NOT_FRESH")
    if boundary.completed is None or boundary.completed.empty:
        raise TP6Protect3Unsafe("R070_PROTECT3_COMPLETED_M15_MISSING")
    last = boundary.completed.iloc[-1]
    bar_open = last["Datetime"]
    if (not isinstance(bar_open, datetime)
            or bar_open.tzinfo is not None
            or bar_open + timedelta(minutes=15) != boundary.at_msk):
        raise TP6Protect3Unsafe("R070_PROTECT3_COMPLETED_M15_NOT_ADJACENT")
    if (bar_open < entry_open_msk
            or entry_open_msk > boundary.at_msk):
        return ProtectionReview("BEFORE_ENTRY_NO_CHANGE", None, None)
    # OHLC from completed, already validated FINAM bars only. This does
    # not introduce an alternative timeframe/signal and cannot send orders.
    return review_completed_m15(
        levels=levels, m15_open_msk=bar_open,
        observed_utc=boundary.observed_at_utc,
        high=last["High"], low=last["Low"],
        active_stop=currently_proved_stop,
        broker_stop_proved=broker_stop_proved,
        completed_bar_proved=True,
    )


def prove_r070_protect3_fresh_quote(
    *, response: dict, symbol: str, direction: str,
    observed_utc, tick, maximum_age_seconds: int = 5,
) -> Decimal:
    """Validate a fresh FINAM LastQuote GET response, never a M15 Open.

    bid is the immediate SELL-side reference for LONG, ask the BUY-side
    reference for SHORT. Neither proves future execution or stop liquidity.
    Old/missing/crossed quotes refuse a Protect3 cancellation.
    """
    from datetime import datetime, timedelta, timezone

    if (not isinstance(response, dict)
            or not isinstance(symbol, str) or not symbol
            or direction not in {"LONG", "SHORT"}
            or not isinstance(observed_utc, datetime)
            or observed_utc.tzinfo is None
            or type(maximum_age_seconds) is not int
            or maximum_age_seconds not in range(1, 16)):
        raise TP6Protect3Unsafe("R070_PROTECT3_QUOTE_SCOPE_INVALID")
    quote = response.get("quote")
    if (response.get("symbol") != symbol
            or not isinstance(quote, dict)
            or quote.get("symbol") != symbol):
        raise TP6Protect3Unsafe("R070_PROTECT3_QUOTE_SYMBOL_INVALID")
    try:
        timestamp = datetime.fromisoformat(
            quote["timestamp"].replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            raise ValueError("naive quote time")
        age = observed_utc.astimezone(timezone.utc) - timestamp.astimezone(timezone.utc)
        if not timedelta(0) <= age <= timedelta(seconds=maximum_age_seconds):
            raise TP6Protect3Unsafe("R070_PROTECT3_QUOTE_STALE_OR_FUTURE")
        step = Decimal(str(tick))
        bid = Decimal(str(quote["bid"]["value"]))
        ask = Decimal(str(quote["ask"]["value"]))
        if (not step.is_finite() or step <= 0
                or not bid.is_finite() or not ask.is_finite()
                or bid <= 0 or ask <= 0 or bid > ask
                or bid / step != (bid / step).to_integral_value()
                or ask / step != (ask / step).to_integral_value()):
            raise TP6Protect3Unsafe("R070_PROTECT3_QUOTE_SPREAD_OR_GRID_INVALID")
    except (KeyError, AttributeError, TypeError, ValueError, InvalidOperation) as exc:
        raise TP6Protect3Unsafe("R070_PROTECT3_QUOTE_FIELDS_INVALID") from exc
    return bid if direction == "LONG" else ask


def read_r070_protect3_quote_from_finam(
    *, reader, symbol: str, direction: str, reference_utc=None,
) -> Decimal:
    """One authenticated FINAM READONLY GET LastQuote, no POST/DELETE.

    Reuses V20's existing authenticated reader._request(). The server quote
    timestamp, bid/ask side and tick grid are checked independently;
    a successful GET does not by itself authorize a stop replacement.
    """
    from datetime import datetime, timezone
    from TradingSystemLab.stage8_robot.production_runtime import _load_registry
    from .finam_execution import V20FinamReadAdapter

    if (not isinstance(reader, V20FinamReadAdapter)
            or not isinstance(symbol, str) or symbol not in _load_registry()
            or direction not in {"LONG", "SHORT"}):
        raise TP6Protect3Unsafe("R070_PROTECT3_FINAM_QUOTE_SCOPE_INVALID")
    reader._require_bound()
    symbol_wire = _load_registry()[symbol]["finam_symbol"]
    tick = _load_registry()[symbol]["price_step"]
    path = "/v1/instruments/" + symbol_wire + "/quotes/latest"
    response = reader.api._request("GET", path).body
    observed = datetime.now(timezone.utc)
    if reference_utc is not None:
        if not isinstance(reference_utc, datetime) or reference_utc.tzinfo is None:
            raise TP6Protect3Unsafe("R070_PROTECT3_QUOTE_REFERENCE_TIME_INVALID")
        if abs((observed - reference_utc.astimezone(timezone.utc)).total_seconds()) > 5:
            raise TP6Protect3Unsafe("R070_PROTECT3_QUOTE_SNAPSHOT_CLOCK_DIVERGED")
    return prove_r070_protect3_fresh_quote(
        response=response, symbol=symbol_wire,
        direction=direction, observed_utc=observed, tick=tick)


def plan_r070_protect3_cancel_first(
    *, levels: TP6Levels, review, observed_position: int,
    orders: tuple[BrokerOrderView, ...], old_wire: dict,
    old_order_id: str, m15_boundary_msk, broker_last_price,
) -> R070Protect3CancelFirstPlan:
    """Pure candidate preflight, never a permission to call FINAM write APIs.

    Requires one proved WATCHING linked 100% SLTP, completed +3R review,
    full unchanged position, next-M15 boundary and price beyond the new SL.
    If any fact is uncertain, keep the old stop; do NOT cancel.
    """
    from datetime import datetime
    from .tp6_protect3 import ProtectionReview

    if (not isinstance(review, ProtectionReview)
            or review.status != "LOCK_1R_DUE_NEXT_M15_BROKER_REPLACE_BLOCKED"
            or review.proposed_stop != levels.locked_stop_1r
            or not isinstance(m15_boundary_msk, datetime)
            or m15_boundary_msk.tzinfo is not None
            or review.eligible_m15_open_msk != m15_boundary_msk
            or not 10 <= m15_boundary_msk.hour < 18
            or not isinstance(old_wire, dict)):
        raise TP6Protect3Unsafe("R070_PROTECT3_PRECONDITIONS_UNVERIFIED")
    old = verify_r070_linked_sltp(
        observed_position=observed_position, orders=orders,
        levels=levels, wire=old_wire,
        expected_broker_order_id=old_order_id,
    )
    if old.status != "WATCHING":
        raise TP6Protect3Unsafe("R070_PROTECT3_OLD_STOP_NOT_WATCHING")
    try:
        price = Decimal(str(broker_last_price))
        if (not price.is_finite()
                or (levels.direction == "LONG"
                    and price < levels.locked_stop_1r + levels.tick)
                or (levels.direction == "SHORT"
                    and price > levels.locked_stop_1r - levels.tick)):
            raise TP6Protect3Unsafe("R070_PROTECT3_PRICE_NO_LONGER_SAFE")
    except (ValueError, TypeError, InvalidOperation) as exc:
        raise TP6Protect3Unsafe("R070_PROTECT3_PRICE_UNVERIFIED") from exc
    old_comment = old_wire.get("comment")
    if (not isinstance(old_comment, str) or not old_comment.endswith(":stop")):
        raise TP6Protect3Unsafe("R070_PROTECT3_STOP_IDENTITY_INVALID")
    new_comment = old_comment[:-5] + ":protect3:1r"
    if len(new_comment) > 128:
        raise TP6Protect3Unsafe("R070_PROTECT3_COMMENT_TOO_LONG")
    from TradingSystemLab.stage8_robot.broker import compact_client_order_id
    from copy import deepcopy
    new_wire = deepcopy(old_wire)
    new_wire["sl_price"] = {"value": str(levels.locked_stop_1r)}
    new_wire["comment"] = new_comment
    new_wire["client_order_id"] = compact_client_order_id(new_comment)
    if (new_wire["tp_price"] != old_wire["tp_price"]
            or new_wire["quantity_sl"] != {"value": "100"}
            or new_wire["quantity_tp"] != {"value": "100"}
            or new_wire["sl_qty_measure"] != "SLTP_QTY_MEASURE_PERCENT"
            or new_wire["tp_qty_measure"] != "SLTP_QTY_MEASURE_PERCENT"):
        raise TP6Protect3Unsafe("R070_PROTECT3_TP_OR_COVERAGE_CHANGED")
    return R070Protect3CancelFirstPlan(
        old_order_id=old_order_id, symbol=old_wire["symbol"],
        direction=levels.direction, position_quantity=observed_position,
        old_wire=deepcopy(old_wire), new_wire=new_wire,
        stop_1r=levels.locked_stop_1r, tp_6r=levels.take_profit,
    )


def prepare_r070_protect3_from_v20_readonly(
    *, journal, reader, snapshot, entry_key: str, now,
    boundary, quote_response: dict | None = None,
):
    """Read-only bridge: durable full fill + linked SLTP + M15 -> +3R plan.

    A caller supplies an already READONLY-verified LastQuote response, or
    this bridge makes ONE authenticated FINAM GET after +3R is detected.
    No POST/DELETE, SQLite writes or permission to cancel an SLTP.
    """
    from datetime import datetime
    from TradingSystemLab.stage8_robot.production_runtime import _load_registry
    from .finam_execution import (
        LiveAccountSnapshot, V20FinamReadAdapter, V20TradeJournal,
        V20M15Boundary,
    )

    if (not isinstance(journal, V20TradeJournal)
            or not isinstance(reader, V20FinamReadAdapter)
            or not isinstance(snapshot, LiveAccountSnapshot)
            or not isinstance(boundary, V20M15Boundary)
            or not isinstance(entry_key, str)
            or not isinstance(now, datetime) or now.tzinfo is None
            or journal.robot_id != reader.robot_id
            or journal.account_hash != reader.account_hash
            or snapshot.robot_id != reader.robot_id
            or snapshot.account_hash != reader.account_hash):
        raise TP6Protect3Unsafe("R070_PROTECT3_HANDOFF_SCOPE_INVALID")
    if (journal.store.get("r070_protect3:" + entry_key) is not None
            or journal.store.get("execution_halt") is not None
            or journal.store.get("flat_cleanup:" + entry_key) is not None
            or journal.store.intent(entry_key + ":frozen-exit") is not None):
        raise TP6Protect3Unsafe("R070_PROTECT3_HANDOFF_ALREADY_ATTEMPTED_OR_EXIT")
    entry = journal.store.intent(entry_key)
    stop = journal.store.intent(entry_key + ":stop")
    proof = journal.store.get("protected_fill:" + entry_key)
    if (not isinstance(entry, dict) or entry.get("status") != "RECONCILED"
            or not isinstance(stop, dict) or not isinstance(proof, dict)
            or not isinstance(entry.get("payload"), dict)
            or not isinstance(stop.get("payload"), dict)
            or not isinstance(stop["payload"].get("wire"), dict)):
        raise TP6Protect3Unsafe("R070_PROTECT3_HANDOFF_DURABLE_MISSING")
    symbol = entry["payload"].get("symbol")
    if boundary.symbol != symbol or symbol not in _load_registry():
        raise TP6Protect3Unsafe("R070_PROTECT3_HANDOFF_M15_SYMBOL_MISMATCH")
    old = verify_r070_tp6_after_restart(
        journal=journal, reader=reader, snapshot=snapshot,
        entry_key=entry_key, now=now)
    try:
        entry_open = datetime.fromisoformat(entry["payload"]["entry_at"])
        if entry_open.tzinfo is not None:
            raise ValueError("entry clock must be Moscow-naive")
        rows = journal.store.fills_for_order(entry["broker_order_id"])
        levels = levels_from_finam_fills(
            direction=entry["payload"]["direction"],
            fills=[(int(f["quantity"]), f["price"]) for f in rows],
            initial_stop=proof["installed_stop"],
            tick=_load_registry()[symbol]["price_step"])
    except (KeyError, ValueError, TypeError, InvalidOperation,
            OverflowError, ZeroDivisionError) as exc:
        raise TP6Protect3Unsafe("R070_PROTECT3_HANDOFF_VWAP_OR_ENTRY_INVALID") from exc
    review = review_r070_protect3_m15_boundary(
        levels=levels, boundary=boundary,
        entry_open_msk=entry_open, broker_stop_proved=True,
        currently_proved_stop=levels.initial_stop)
    if review.status != "LOCK_1R_DUE_NEXT_M15_BROKER_REPLACE_BLOCKED":
        return review, None
    price = (
        read_r070_protect3_quote_from_finam(
            reader=reader, symbol=symbol, direction=levels.direction,
            reference_utc=now)
        if quote_response is None else
        prove_r070_protect3_fresh_quote(
            response=quote_response,
            symbol=entry["payload"]["finam_symbol"],
            direction=levels.direction, observed_utc=now,
            tick=levels.tick)
    )
    plan = plan_r070_protect3_cancel_first(
        levels=levels, review=review,
        observed_position=snapshot.positions[entry["payload"]["finam_symbol"]],
        orders=snapshot.orders, old_wire=stop["payload"]["wire"],
        old_order_id=old.order_id,
        m15_boundary_msk=boundary.at_msk,
        broker_last_price=price,
    )
    return review, plan


def verify_r070_protect3_cancelled_before_post(
    *, plan: R070Protect3CancelFirstPlan, observed_position: int,
    orders: tuple[BrokerOrderView, ...],
) -> None:
    """Broker GET must show EXACT old ID CANCELLED and no active child/order.

    Cancel ACK alone or missing old order cannot prove this. No second POST
    until the uncertain cancellation has been reconciled. If the position is
    open without SLTP, operator escalation is required immediately.
    """
    if not isinstance(plan, R070Protect3CancelFirstPlan):
        raise TP6Protect3Unsafe("R070_PROTECT3_PLAN_REQUIRED")
    if type(observed_position) is not int or observed_position != plan.position_quantity:
        raise TP6Protect3Unsafe("R070_PROTECT3_POSITION_CHANGED_AFTER_CANCEL")
    if not isinstance(orders, tuple) or any(
            not isinstance(o, BrokerOrderView) for o in orders):
        raise TP6Protect3Unsafe("R070_PROTECT3_ORDERS_UNVERIFIED")
    old = [o for o in orders if o.order_id == plan.old_order_id]
    if (len(old) != 1 or old[0].symbol != plan.symbol
            or old[0].kind != "SLTP" or old[0].active
            or old[0].status not in {"CANCELLED", "CANCELED"}):
        raise TP6Protect3Unsafe("R070_PROTECT3_CANCEL_NOT_BROKER_PROVEN")
    if any(o.active and o.symbol == plan.symbol for o in orders):
        raise TP6Protect3Unsafe("R070_PROTECT3_CONFLICTING_ACTIVE_ORDER_AFTER_CANCEL")


def verify_r070_protect3_new_sltp(
    *, plan: R070Protect3CancelFirstPlan, observed_position: int,
    orders: tuple[BrokerOrderView, ...], new_order_id: str,
) -> BrokerOrderView:
    """After NEW broker POST, require exactly one WATCHING SLTP and 100% SL+TP6."""
    if (not isinstance(plan, R070Protect3CancelFirstPlan)
            or type(observed_position) is not int
            or observed_position != plan.position_quantity
            or not isinstance(orders, tuple)
            or not isinstance(new_order_id, str) or not new_order_id
            or new_order_id == plan.old_order_id):
        raise TP6Protect3Unsafe("R070_PROTECT3_NEW_PROOF_SCOPE_INVALID")
    active = [o for o in orders if o.active and o.symbol == plan.symbol]
    if len(active) != 1 or active[0].kind != "SLTP":
        raise TP6Protect3Unsafe("R070_PROTECT3_NEW_EXCLUSIVE_SLTP_REQUIRED")
    order = active[0]
    if (order.order_id != new_order_id or order.status != "WATCHING"
            or order.side != plan.new_wire.get("side")
            or order.symbol != plan.symbol
            or order.comment != plan.new_wire.get("comment")
            or not (order.client_order_id == plan.new_wire.get("client_order_id")
                    or order.client_order_id == "")
            or not isinstance(order.request, dict)):
        raise TP6Protect3Unsafe("R070_PROTECT3_NEW_BROKER_IDENTITY_INVALID")
    try:
        _validate_production_sltp(order)
        for k in ("sl_price", "tp_price", "quantity_sl", "quantity_tp"):
            if Decimal(str(order.request[k]["value"])) != Decimal(str(plan.new_wire[k]["value"])):
                raise TP6Protect3Unsafe("R070_PROTECT3_NEW_LEVEL_OR_COVERAGE_MISMATCH")
        for k in ("sl_qty_measure", "tp_qty_measure", "valid_before"):
            if order.request.get(k) != plan.new_wire.get(k):
                raise TP6Protect3Unsafe("R070_PROTECT3_NEW_MEASURE_OR_VALIDITY_MISMATCH")
        if (Decimal(str(order.request["sl_price"]["value"])) != plan.stop_1r
                or Decimal(str(order.request["tp_price"]["value"])) != plan.tp_6r):
            raise TP6Protect3Unsafe("R070_PROTECT3_NEW_TARGET_CHANGED")
    except (KeyError, TypeError, ValueError, InvalidOperation,
            ProductionBrokerStateError) as exc:
        raise TP6Protect3Unsafe("R070_PROTECT3_NEW_BROKER_FIELDS_UNVERIFIED") from exc
    return order

def stage_r070_protect3_cancel_first_once(
    *, journal, reader, entry_key: str, plan: R070Protect3CancelFirstPlan,
    broker_api, observed_at, authorized_live_sender=None,
) -> str:
    """One-shot CANCEL→broker proof→new SLTP, durable at each transition.

    Default is OFFLINE fake only. The optional actual FINAM route requires
    the real V20LiveTransport, its existing authorization, ARMED state and
    a separately pinned R070 release approval in the durable journal.
    No production worker calls this until a distinct staged patch is approved.
    """
    from datetime import datetime
    from .finam_execution import V20TradeJournal, V20FinamReadAdapter

    if (not isinstance(journal, V20TradeJournal)
            or not isinstance(reader, V20FinamReadAdapter)
            or not isinstance(plan, R070Protect3CancelFirstPlan)
            or not isinstance(entry_key, str) or not entry_key
            or not isinstance(observed_at, datetime)
            or observed_at.tzinfo is None
            or journal.robot_id != reader.robot_id
            or journal.account_hash != reader.account_hash
            or not hasattr(broker_api, "cancel_order")
            or not hasattr(broker_api, "place_sltp_order")
            or not callable(reader.snapshot)):
        raise TP6Protect3Unsafe("R070_PROTECT3_CANDIDATE_SCOPE_INVALID")
    if authorized_live_sender is None:
        # Backward-compatible isolated mock-only candidate.
        if getattr(journal, "live_runtime", False) or broker_api is reader.api:
            raise TP6Protect3Unsafe("R070_PROTECT3_CANDIDATE_REAL_API_FORBIDDEN")
    else:
        from .finam_live import (
            V20LiveTransport, V20LiveJournal, _safe_auth, load_kill_switch,
        )
        sender = authorized_live_sender
        if (not isinstance(sender, V20LiveTransport)
                or not isinstance(journal, V20LiveJournal)
                or sender.journal is not journal
                or sender.reader is not reader
                or broker_api is not reader.api
                or not journal.live_runtime):
            raise TP6Protect3Unsafe("R070_PROTECT3_LIVE_TRANSPORT_IDENTITY_INVALID")
        # A normal V20 authorization does not automatically approve R070.
        # The explicit release marker is never created by this function.
        approval = journal.store.get("r070_protect3_release_authorization")
        if approval != {
            "schema": "r070.protect3.live_approval.v1",
            "source_commit": sender.source,
            "robot": reader.robot_id,
            "account_sha256": reader.account_hash,
            "owner_approved": True,
        }:
            raise TP6Protect3Unsafe("R070_PROTECT3_LIVE_RELEASE_NOT_AUTHORIZED")
        _safe_auth(sender.auth_path, journal=journal, source=sender.source)
        switch, error = load_kill_switch(journal.instance_root)
        if error or not switch or switch.get("state") != "ARMED":
            raise TP6Protect3Unsafe("R070_PROTECT3_SWITCH_NOT_ARMED")
        sender._permit(key=entry_key, kind="PROTECTIVE_STOP")
    key = "r070_protect3:" + entry_key
    original = journal.store.intent(entry_key)
    old_intent = journal.store.intent(entry_key + ":stop")
    proof = journal.store.get("protected_fill:" + entry_key)
    if (not isinstance(original, dict)
            or original.get("status") != "RECONCILED"
            or not isinstance(old_intent, dict)
            or old_intent.get("status") not in {"ACK", "RECONCILED"}
            or old_intent.get("broker_order_id") != plan.old_order_id
            or not isinstance(proof, dict)
            or proof.get("broker_stop_id") != plan.old_order_id
            or proof.get("account_sha256") != journal.account_hash
            or proof.get("broker_stop_percent") != "100"
            or plan.old_wire.get("symbol") != original.get("payload", {}).get("finam_symbol")
            or plan.old_wire.get("comment") != entry_key + ":stop"
            or plan.new_wire.get("client_order_id") ==
                plan.old_wire.get("client_order_id")):
        raise TP6Protect3Unsafe("R070_PROTECT3_CANDIDATE_PROOF_INVALID")
    if journal.store.get(key) is not None:
        raise TP6Protect3Unsafe("R070_PROTECT3_ALREADY_ATTEMPTED_NO_REPLAY")
    if (journal.store.get("execution_halt") is not None
            or journal.store.get("flat_cleanup:" + entry_key) is not None
            or journal.store.intent(entry_key + ":frozen-exit") is not None):
        raise TP6Protect3Unsafe("R070_PROTECT3_EXIT_OR_HALT_PENDING")
    # This is an OFFLINE broker fake; still verify the broker-like observations.
    before = reader.snapshot(now=observed_at)
    if (before.positions.get(plan.symbol, 0) != plan.position_quantity
            or len([o for o in before.orders
                    if o.active and o.symbol == plan.symbol]) != 1
            or not any(o.active and o.order_id == plan.old_order_id
                       and o.kind == "SLTP" and o.status == "WATCHING"
                       for o in before.orders)):
        raise TP6Protect3Unsafe("R070_PROTECT3_BEFORE_CANCEL_CHANGED")
    from copy import deepcopy
    with journal.store.transaction():
        if journal.store.get(key) is not None:
            raise TP6Protect3Unsafe("R070_PROTECT3_ALREADY_ATTEMPTED_NO_REPLAY")
        journal.store.put(key, {
            "schema": "r070.protect3.cancel_first.candidate.v1",
            "state": "CANCEL_OUTCOME_UNKNOWN", "account_sha256": journal.account_hash,
            "robot": reader.robot_id, "symbol": plan.symbol,
            "entry_key": entry_key, "old_broker_id": plan.old_order_id,
            "position_quantity": plan.position_quantity,
            "new_client_order_id": plan.new_wire["client_order_id"],
            "new_wire": deepcopy(plan.new_wire),
            "new_broker_id": None,
        })

    def progress(state: str, new_broker_id=None):
        # Store the entire state so restart can inspect but NEVER replay POST.
        with journal.store.transaction():
            item = journal.store.get(key)
            if not isinstance(item, dict):
                raise TP6Protect3Unsafe("R070_PROTECT3_DURABLE_STATE_MISSING")
            item["state"] = state
            item["new_broker_id"] = new_broker_id
            journal.store.put(key, item)

    # Any exception beyond this point may mean there is NO active stop.
    # The durable alert survives restart; no other order is auto-issued.
    try:
        broker_api.cancel_order(reader.account_id, plan.old_order_id)
        progress("CANCEL_ACK_UNVERIFIED")
        after_cancel = reader.snapshot(now=observed_at)
        verify_r070_protect3_cancelled_before_post(
            plan=plan, observed_position=after_cancel.positions.get(plan.symbol, 0),
            orders=after_cancel.orders,
        )
        progress("CANCEL_PROVED_UNPROTECTED")
        # Persist the unique new POST key BEFORE dispatch. No second attempt.
        progress("NEW_POST_OUTCOME_UNKNOWN")
        result = broker_api.place_sltp_order(reader.account_id, deepcopy(plan.new_wire))
        oid = result.get("order_id") if isinstance(result, dict) else None
        if not isinstance(oid, str) or not oid:
            raise TP6Protect3Unsafe("R070_PROTECT3_NEW_ACK_MISSING")
        progress("NEW_ACK_UNVERIFIED", oid)
        after_new = reader.snapshot(now=observed_at)
        verify_r070_protect3_new_sltp(
            plan=plan, observed_position=after_new.positions.get(plan.symbol, 0),
            orders=after_new.orders, new_order_id=oid,
        )
        progress("PROTECTED", oid)
        return oid
    except BaseException:
        # A state without fresh proof must never be reported as protected.
        journal.store.put("execution_halt", "PROTECT3_UNPROTECTED_OR_UNKNOWN")
        raise


def examine_r070_protect3_after_restart(
    *, journal, reader, entry_key: str, observed_at,
) -> str:
    """GET-only recognition of previous attempt; NEVER resends CANCEL/POST.

    Also never declares protection from a stored ACK. Ownership/seal handoff
    to LIVE must be added and accepted separately before deployment.
    """
    from datetime import datetime
    from .finam_execution import V20TradeJournal, V20FinamReadAdapter

    if (not isinstance(journal, V20TradeJournal)
            or not isinstance(reader, V20FinamReadAdapter)
            or not isinstance(observed_at, datetime) or observed_at.tzinfo is None
            or journal.account_hash != reader.account_hash
            or journal.robot_id != reader.robot_id):
        raise TP6Protect3Unsafe("R070_PROTECT3_RESTART_SCOPE_INVALID")
    key = "r070_protect3:" + entry_key
    rec = journal.store.get(key)
    if (not isinstance(rec, dict)
            or rec.get("schema") != "r070.protect3.cancel_first.candidate.v1"
            or rec.get("entry_key") != entry_key
            or rec.get("account_sha256") != journal.account_hash
            or rec.get("robot") != reader.robot_id
            or not isinstance(rec.get("new_wire"), dict)):
        raise TP6Protect3Unsafe("R070_PROTECT3_RESTART_STATE_INVALID")
    current = reader.snapshot(now=observed_at)
    symbol = rec["symbol"]
    if current.positions.get(symbol, 0) == 0:
        return "BROKER_FLAT_RECONCILE_NO_WRITE"
    if (type(rec.get("position_quantity")) is not int
            or current.positions.get(symbol) != rec["position_quantity"]):
        return "CRITICAL_UNKNOWN_OR_UNPROTECTED_OPERATOR_REQUIRED"
    if rec["state"] != "PROTECTED":
        return "CRITICAL_UNKNOWN_OR_UNPROTECTED_OPERATOR_REQUIRED"
    new = [o for o in current.orders
           if o.order_id == rec.get("new_broker_id") and o.active
           and o.kind == "SLTP" and o.status == "WATCHING"
           and o.symbol == symbol
           and o.request == rec["new_wire"]]
    if (len(new) != 1
            or len([o for o in current.orders if o.active and o.symbol == symbol]) != 1):
        return "CRITICAL_UNKNOWN_OR_UNPROTECTED_OPERATOR_REQUIRED"
    # This is an OFFLINE diagnostic, not authority for new entries.
    return "CANDIDATE_PROTECTED_BROKER_SNAPSHOT_ONLY"


def verify_r070_protect3_effective_stop(
    *, journal, reader, snapshot, entry_key: str, now,
) -> BrokerOrderView:
    """Read-only reconciliation of an already replaced SLTP after reboot.

    The immutable original :stop intent, the durable original fill/VWAP
    proof and the R070 transition record must all agree with the CURRENT
    broker position and the single new SLTP. No HTTP, SQLite writes,
    broker cancellation or submission is performed by this function.
    An unconfirmed CANCEL/POST is NEVER interpreted as protection.
    """
    from TradingSystemLab.stage8_robot.production_runtime import _load_registry
    from .finam_execution import (
        LiveAccountSnapshot, V20FinamReadAdapter, V20TradeJournal,
    )

    if (not isinstance(journal, V20TradeJournal)
            or not isinstance(reader, V20FinamReadAdapter)
            or not isinstance(snapshot, LiveAccountSnapshot)
            or journal.robot_id != reader.robot_id
            or snapshot.robot_id != reader.robot_id
            or journal.account_hash != reader.account_hash
            or snapshot.account_hash != reader.account_hash
            or not isinstance(entry_key, str)
            or not entry_key.startswith(
                "v20:" + reader.robot_id + ":" + reader.account_hash[:16] + ":")):
        raise TP6Protect3Unsafe("R070_EFFECTIVE_STOP_ACCOUNT_OR_ENTRY_INVALID")
    reader._fresh(snapshot, now)
    entry = journal.store.intent(entry_key)
    initial = journal.store.intent(entry_key + ":stop")
    proof = journal.store.get("protected_fill:" + entry_key)
    rec = journal.store.get("r070_protect3:" + entry_key)
    if (not isinstance(entry, dict) or entry.get("status") != "RECONCILED"
            or not isinstance(entry.get("broker_order_id"), str)
            or not isinstance(initial, dict)
            or initial.get("status") not in {"ACK", "RECONCILED"}
            or not isinstance(proof, dict)
            or proof.get("account_sha256") != reader.account_hash
            or proof.get("broker_order_id") != entry["broker_order_id"]
            or proof.get("broker_stop_id") != initial.get("broker_order_id")
            or proof.get("broker_stop_percent") != "100"
            or not isinstance(proof.get("risk_assessment"), dict)
            or proof["risk_assessment"].get("status") != "PASS"
            or proof["risk_assessment"].get("stop_conforms") is not True
            or not isinstance(rec, dict)
            or rec.get("schema") != "r070.protect3.cancel_first.candidate.v1"
            or rec.get("state") != "PROTECTED"
            or rec.get("robot") != reader.robot_id
            or rec.get("account_sha256") != reader.account_hash
            or rec.get("entry_key") != entry_key
            or rec.get("old_broker_id") != initial["broker_order_id"]
            or not isinstance(rec.get("new_broker_id"), str)
            or not rec["new_broker_id"]
            or rec["new_broker_id"] == rec["old_broker_id"]
            or not isinstance(rec.get("new_wire"), dict)):
        raise TP6Protect3Unsafe("R070_EFFECTIVE_STOP_DURABLE_PROOF_INVALID")
    payload = entry.get("payload")
    initial_payload = initial.get("payload")
    if (not isinstance(payload, dict)
            or not isinstance(initial_payload, dict)
            or initial_payload.get("kind") != "STOP"
            or initial_payload.get("entry_key") != entry_key
            or initial_payload.get("account_sha256") != reader.account_hash
            or not isinstance(initial_payload.get("wire"), dict)):
        raise TP6Protect3Unsafe("R070_EFFECTIVE_STOP_ORIGINAL_WIRE_INVALID")
    old_wire = initial_payload["wire"]
    symbol, direction = payload.get("symbol"), payload.get("direction")
    registry = _load_registry()
    if (symbol not in registry or direction not in {"LONG", "SHORT"}
            or payload.get("finam_symbol") != registry[symbol]["finam_symbol"]
            or old_wire.get("symbol") != payload["finam_symbol"]
            or rec.get("symbol") != payload["finam_symbol"]
            or rec.get("new_wire", {}).get("symbol") != payload["finam_symbol"]
            or old_wire.get("comment") != entry_key + ":stop"
            or type(payload.get("quantity")) is not int
            or payload["quantity"] <= 0):
        raise TP6Protect3Unsafe("R070_EFFECTIVE_STOP_SYMBOL_OR_SIDE_INVALID")
    qty = snapshot.positions.get(payload["finam_symbol"])
    expected = payload["quantity"] if direction == "LONG" else -payload["quantity"]
    if (type(qty) is not int or qty != expected
            or rec.get("position_quantity") != qty
            or type(proof.get("filled_quantity")) is not int
            or proof["filled_quantity"] != abs(qty)
            or initial_payload.get("observed_position_quantity") != qty):
        raise TP6Protect3Unsafe("R070_EFFECTIVE_STOP_POSITION_CHANGED")
    try:
        fills = journal.store.fills_for_order(entry["broker_order_id"])
        if not isinstance(fills, list) or not fills:
            raise ValueError("no durable fills")
        ids = set()
        rows = []
        for fill in fills:
            if (not isinstance(fill, dict)
                    or fill.get("entry_key") != entry_key
                    or fill.get("trade_id") != entry_key
                    or fill.get("account_sha256") != reader.account_hash
                    or fill.get("broker_order_id") != entry["broker_order_id"]
                    or not isinstance(fill.get("fill_id"), str)
                    or not fill["fill_id"].startswith("finam:" + reader.account_hash + ":")
                    or fill["fill_id"] in ids):
                raise ValueError("unproven fill")
            ids.add(fill["fill_id"])
            rows.append((int(fill["quantity"]), fill["price"]))
        from fractions import Fraction
        if (sum(q for q, _ in rows) != abs(qty)
                or sum((q * Fraction(price) for q, price in rows), Fraction(0))
                   != abs(qty) * Fraction(proof["average_exact"])):
            raise ValueError("fill quantity or VWAP mismatch")
        levels = levels_from_finam_fills(
            direction=direction, fills=rows,
            initial_stop=proof["installed_stop"],
            tick=registry[symbol]["price_step"])
        if (Decimal(str(old_wire["sl_price"]["value"])) != levels.initial_stop
                or Decimal(str(old_wire["tp_price"]["value"])) != levels.take_profit):
            raise ValueError("original linked SLTP not TP6")
        old_comment = entry_key + ":stop"
        from copy import deepcopy
        expected_wire = deepcopy(old_wire)
        expected_wire["sl_price"] = {"value": str(levels.locked_stop_1r)}
        expected_wire["comment"] = entry_key + ":protect3:1r"
        expected_wire["client_order_id"] = compact_client_order_id(
            entry_key + ":protect3:1r")
        if (old_wire.get("client_order_id") != compact_client_order_id(old_comment)
                or rec["new_wire"] != expected_wire
                or rec.get("new_client_order_id") != expected_wire["client_order_id"]):
            raise ValueError("new wire not exactly derived from original seal")
    except (KeyError, TypeError, ValueError, InvalidOperation,
            OverflowError, ZeroDivisionError, TP6Protect3Unsafe) as exc:
        raise TP6Protect3Unsafe("R070_EFFECTIVE_STOP_LEVELS_OR_FILLS_UNVERIFIED") from exc
    plan = R070Protect3CancelFirstPlan(
        old_order_id=initial["broker_order_id"],
        symbol=payload["finam_symbol"], direction=direction,
        position_quantity=qty, old_wire=old_wire,
        new_wire=expected_wire, stop_1r=levels.locked_stop_1r,
        tp_6r=levels.take_profit,
    )
    return verify_r070_protect3_new_sltp(
        plan=plan, observed_position=qty,
        orders=snapshot.orders, new_order_id=rec["new_broker_id"],
    )


def verify_r070_protect3_flat_successor(
    *, journal, entry_key: str, broker_order: BrokerOrderView,
) -> BrokerOrderView:
    """Recognize only the successor SLTP for broker-FLAT cleanup, no writes.

    The caller must independently prove broker-flat (zero position) and no
    active closing/entry children before attempting the existing one-shot
    H1 cancel-after-flat. Original :stop identity is never rewritten.
    """
    from .finam_execution import V20TradeJournal
    if (not isinstance(journal, V20TradeJournal)
            or not isinstance(entry_key, str)
            or not entry_key.startswith(
                "v20:" + journal.robot_id + ":" + journal.account_hash[:16] + ":")
            or not isinstance(broker_order, BrokerOrderView)
            or broker_order.kind != "SLTP" or not broker_order.active
            or broker_order.status != "WATCHING"):
        raise TP6Protect3Unsafe("R070_FLAT_CLEANUP_SCOPE_INVALID")
    initial = journal.store.intent(entry_key + ":stop")
    proof = journal.store.get("protected_fill:" + entry_key)
    replacement = journal.store.get("r070_protect3:" + entry_key)
    if (not isinstance(initial, dict)
            or initial.get("status") not in {"ACK", "RECONCILED"}
            or not isinstance(proof, dict)
            or proof.get("account_sha256") != journal.account_hash
            or proof.get("broker_stop_id") != initial.get("broker_order_id")
            or proof.get("broker_stop_percent") != "100"
            or not isinstance(replacement, dict)
            or replacement.get("schema") != "r070.protect3.cancel_first.candidate.v1"
            or replacement.get("state") != "PROTECTED"
            or replacement.get("robot") != journal.robot_id
            or replacement.get("account_sha256") != journal.account_hash
            or replacement.get("entry_key") != entry_key
            or replacement.get("old_broker_id") != initial["broker_order_id"]
            or replacement.get("new_broker_id") == initial["broker_order_id"]
            or replacement.get("new_broker_id") != broker_order.order_id):
        raise TP6Protect3Unsafe("R070_FLAT_CLEANUP_DURABLE_ID_INVALID")
    original_payload = initial.get("payload")
    if (not isinstance(original_payload, dict)
            or original_payload.get("kind") != "STOP"
            or original_payload.get("account_sha256") != journal.account_hash
            or original_payload.get("entry_key") != entry_key
            or not isinstance(original_payload.get("wire"), dict)
            or not isinstance(replacement.get("new_wire"), dict)):
        raise TP6Protect3Unsafe("R070_FLAT_CLEANUP_WIRE_PROOF_MISSING")
    old = original_payload["wire"]
    new = replacement["new_wire"]
    expected_client = compact_client_order_id(entry_key + ":protect3:1r")
    if (new.get("comment") != entry_key + ":protect3:1r"
            or new.get("client_order_id") != expected_client
            or replacement.get("new_client_order_id") != expected_client
            or broker_order.comment != new["comment"]
            or not (broker_order.client_order_id == expected_client
                    or broker_order.client_order_id == "")
            or broker_order.side != new.get("side")
            or broker_order.symbol != new.get("symbol")
            or new.get("symbol") != old.get("symbol")
            or new.get("side") != old.get("side")
            or new.get("tp_price") != old.get("tp_price")
            or new.get("quantity_sl") != {"value": "100"}
            or new.get("quantity_tp") != {"value": "100"}
            or old.get("quantity_sl") != {"value": "100"}
            or old.get("quantity_tp") != {"value": "100"}
            or new.get("sl_qty_measure") != "SLTP_QTY_MEASURE_PERCENT"
            or new.get("tp_qty_measure") != "SLTP_QTY_MEASURE_PERCENT"):
        raise TP6Protect3Unsafe("R070_FLAT_CLEANUP_SUCCESSOR_CONTRACT_INVALID")
    try:
        _validate_production_sltp(broker_order)
        for name in ("sl_price", "tp_price", "quantity_sl", "quantity_tp"):
            if (Decimal(str(broker_order.request[name]["value"]))
                    != Decimal(str(new[name]["value"]))):
                raise ValueError("broker wire mismatch")
        for name in ("sl_qty_measure", "tp_qty_measure", "valid_before"):
            if broker_order.request.get(name) != new.get(name):
                raise ValueError("broker measure mismatch")
    except (KeyError, TypeError, ValueError, InvalidOperation,
            ProductionBrokerStateError) as exc:
        raise TP6Protect3Unsafe("R070_FLAT_CLEANUP_BROKER_WIRE_INVALID") from exc
    return broker_order
