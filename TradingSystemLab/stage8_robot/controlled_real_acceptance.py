"""Stage 8.11's isolated, one-contract physical-acceptance boundary.

This module is intentionally absent from RuntimeConfig, runner, supervisor and
the Scheduled Task.  Its dependencies are injected; importing it cannot load a
credential, contact FINAM, arm the switch, or transmit an order.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
import time
from typing import Any, Callable

from .account_cleanliness import count_active_orders, normalize_order_status
from .broker import OrderRequest, broker_side, compact_client_order_id
from .finam_api import (CLIENT_ORDER_ID_MAX_LENGTH, MARKET_ORDER_TYPE, TIME_IN_FORCE_DAY,
                        FinamError, FinamNotFound, FinamOrderRejected, FinamUncertainSubmission)
from .instrument_resolver import load_registry
from .specification import ACTIVE_IDENTITY, INSTRUMENTS, PRODUCTION_SPECIFICATION_ID, load_frozen_specification
from .state import StateStore, initialize_stage8_11_acceptance_ledger, stage8_11_acceptance_path
from .trading_safety_gate import emergency_halt, evaluate_new_entry_gate, heartbeat_path

STAGE8_10_AUTHORITY = "STAGE_8_10_TRADING_TOKEN_LIFECYCLE_COMPLETE"
STAGE8_11_STATUS = "CODE_READY_PENDING_PHYSICAL_ACCEPTANCE"
EVIDENCE_SCHEMA = "stage8_11_physical_acceptance.v1"
STAGE8_11_ATTEMPT2_ID = "stage8.11.attempt2"
STAGE8_11_ATTEMPT3_ID = "stage8.11.attempt3"
STAGE8_11_ATTEMPT4_ID = "stage8.11.attempt4"
STAGE8_11_ATTEMPT5_ID = "stage8.11.attempt5"
STAGE8_11_ATTEMPT6_ID = "stage8.11.attempt6"
ALLOWED_ATTEMPT_IDS = frozenset({STAGE8_11_ATTEMPT2_ID, STAGE8_11_ATTEMPT3_ID, STAGE8_11_ATTEMPT4_ID, STAGE8_11_ATTEMPT5_ID, STAGE8_11_ATTEMPT6_ID})
RECONCILIATION_MAX_OBSERVATIONS = 12
RECONCILIATION_ACTIVE_GRACE_OBSERVATIONS = 3
RECONCILIATION_SLEEP_SECONDS = 0.1
POSITION_RECONCILIATION_MAX_OBSERVATIONS = 30
POSITION_RECONCILIATION_SLEEP_SECONDS = 2.0
MAX_ACCEPTANCE_QUANTITY = 1
REGISTRY = Path(__file__).with_name("production_instrument_registry.csv")
TERMINAL_FILL = frozenset({"FILLED", "EXECUTED"})
TERMINAL_NO_FILL = frozenset({
    "REJECTED", "EXPIRED", "CANCELLED", "FAILED",
    "DENIED_BY_BROKER", "REJECTED_BY_EXCHANGE",
})
ACTIVE = frozenset({
    "NEW", "PARTIAL_FILL", "DONE_FOR_DAY", "PENDING_CANCEL", "SUSPENDED",
    "PENDING_NEW", "FORWARDING", "WAIT", "WATCHING", "LINK_WAIT",
})
# Five minutes is a deliberately conservative operational budget for the one
# contract acknowledgement, read-side reconciliation, and controlled flatten.
# It is measured against FINAM's live interval end; no exchange timetable is
# inferred locally.
ENTRY_MINIMUM_REMAINING_SESSION = timedelta(minutes=5)


class AcceptanceBlocked(RuntimeError):
    """A sanitized deterministic refusal at the controlled boundary."""


class OperatorInterventionRequired(AcceptanceBlocked):
    """Safe flat state cannot be proved; an operator must inspect the account."""


class ReconciliationPending(RuntimeError):
    """A structurally valid broker read is temporarily not yet converged."""


@dataclass(frozen=True)
class AcceptanceAuthority:
    """Values derived by :func:`build_physical_context`, never operator claims."""
    production_specification_id: str
    active_identity: str
    stage8_10_status: str
    configured_account_hash: str
    observed_account_hash: str
    heartbeat_account_hash: str
    trading_token_loaded_from_current_user_dpapi: bool
    trading_session_readonly: bool
    account_reconciled: bool
    unknown_position_count: int
    active_order_count: int
    unresolved_intent_count: int
    h1_data_safety_valid: bool
    instrument_binding_valid: bool
    instrument_tradable: bool
    r15_capacity: int
    margin_capacity: int


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256(value: str) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdefABCDEF" for c in value)


def resolve_frozen_symbol(instrument: str, registry_path: Path = REGISTRY) -> str:
    """Resolve the exact authenticated registry symbol for a frozen N4 member."""
    matches = [item for item in load_registry(registry_path)
               if item.research_symbol == instrument and item.binding_status.startswith("AUTHENTICATED_")]
    if len(matches) != 1:
        raise AcceptanceBlocked("INSTRUMENT_BINDING_INVALID")
    resolved = matches[0]
    if not resolved.finam_symbol or resolved.trading_status != "TRADABLE":
        raise AcceptanceBlocked("INSTRUMENT_NOT_TRADABLE")
    return resolved.finam_symbol


def build_physical_context(*, account_id: str, credential_loader: Callable[[], dict[str, Any]],
                           session_factory: Callable[[str], object], runtime_root: Path,
                           reconciliation: Callable[[object, str], dict[str, Any]],
                           store: StateStore,
                           sizing: Callable[[str], int], margin: Callable[[object, str, str], int],
                           instrument: str, registry_path: Path = REGISTRY) -> tuple[AcceptanceAuthority, object, str]:
    """Derive physical authority from existing injectable production components.

    Raw credentials/account objects are deliberately not retained or returned.
    The credential loader is the Windows CurrentUser DPAPI boundary in physical
    use; tests inject a synthetic equivalent.
    """
    credential = credential_loader()
    if credential.get("scope") != "CurrentUser" or not credential.get("api_secret"):
        raise AcceptanceBlocked("TRADING_DPAPI_AUTHORITY_INVALID")
    if credential.get("account_id") != account_id:
        raise AcceptanceBlocked("ACCOUNT_BINDING_INVALID")
    api = session_factory(credential["api_secret"])
    details = api.session_details()
    accounts = [str(x) for x in details.get("account_ids", [])]
    if details.get("readonly") is not False or accounts.count(account_id) != 1:
        raise AcceptanceBlocked("TRADING_SESSION_AUTHORITY_INVALID")
    symbol = resolve_frozen_symbol(instrument, registry_path)
    snapshot = reconciliation(api, account_id)
    heartbeat = json.loads(heartbeat_path(runtime_root).read_text(encoding="utf-8"))
    account_hash = _digest(account_id)
    authority = AcceptanceAuthority(
        PRODUCTION_SPECIFICATION_ID, ACTIVE_IDENTITY, STAGE8_10_AUTHORITY,
        account_hash, account_hash, str(heartbeat.get("account_hash", "")), True, False,
        snapshot.get("reconciled") is True, int(snapshot.get("unknown_position_count", -1)),
        int(snapshot.get("active_order_count", -1)), store.unresolved_intent_count(),
        heartbeat.get("reconciliation_status") == "PASS", True, True,
        int(sizing(instrument)), int(margin(api, account_id, symbol)))
    credential.clear()
    return authority, api, symbol


def precheck(*, authority: AcceptanceAuthority, runtime_root: Path, now: datetime,
             execution_authorized: bool, instrument: str) -> dict[str, Any]:
    reasons: list[str] = []
    try:
        frozen = load_frozen_specification()
        if frozen.production_id != PRODUCTION_SPECIFICATION_ID or frozen.identity != ACTIVE_IDENTITY:
            reasons.append("FROZEN_STAGE7_AUTHORITY_INVALID")
    except Exception:
        reasons.append("FROZEN_STAGE7_AUTHORITY_INVALID")
    hashes = (authority.configured_account_hash, authority.observed_account_hash, authority.heartbeat_account_hash)
    exact = (
        (authority.production_specification_id == PRODUCTION_SPECIFICATION_ID, "PRODUCTION_SPECIFICATION_MISMATCH"),
        (authority.active_identity == ACTIVE_IDENTITY, "ACTIVE_IDENTITY_MISMATCH"),
        (authority.stage8_10_status == STAGE8_10_AUTHORITY, "STAGE8_10_AUTHORITY_INVALID"),
        (all(_sha256(x) for x in hashes) and len(set(h.lower() for h in hashes)) == 1, "ACCOUNT_BINDING_INVALID"),
        (authority.trading_token_loaded_from_current_user_dpapi is True, "TRADING_DPAPI_AUTHORITY_INVALID"),
        (authority.trading_session_readonly is False, "TRADING_SESSION_NOT_WRITE_CAPABLE"),
        (authority.account_reconciled is True, "RECONCILIATION_NOT_PASS"),
        (type(authority.unknown_position_count) is int and authority.unknown_position_count == 0, "UNKNOWN_POSITIONS_PRESENT"),
        (type(authority.active_order_count) is int and authority.active_order_count == 0, "ACTIVE_ORDERS_PRESENT"),
        (type(authority.unresolved_intent_count) is int and authority.unresolved_intent_count == 0, "UNRESOLVED_INTENTS_PRESENT"),
        (authority.h1_data_safety_valid is True, "H1_DATA_SAFETY_INVALID"),
        (instrument in INSTRUMENTS, "INSTRUMENT_NOT_FROZEN_N4"),
        (authority.instrument_binding_valid is True, "INSTRUMENT_BINDING_INVALID"),
        (authority.instrument_tradable is True, "INSTRUMENT_NOT_TRADABLE"),
        (type(authority.r15_capacity) is int and authority.r15_capacity >= 1, "R15_CAPACITY_ZERO"),
        (type(authority.margin_capacity) is int and authority.margin_capacity >= 1, "MARGIN_CAPACITY_ZERO"),
    )
    reasons.extend(code for valid, code in exact if not valid)
    gate = evaluate_new_entry_gate(runtime_root=runtime_root, now=now, execution_authorized=execution_authorized)
    reasons.extend(gate["reason_codes"])
    reasons = list(dict.fromkeys(reasons))
    return {"decision": "AUTHORIZED" if not reasons else "BLOCKED", "reason_codes": reasons,
            "quantity": MAX_ACCEPTANCE_QUANTITY, "gate": gate}


class ControlledAcceptanceBroker:
    """Only adapter allowed to make the two possible Stage 8.11 POSTs."""
    def __init__(self, api: object, account_id: str, accepted_account_hash: str, store: StateStore):
        if not account_id or not _sha256(accepted_account_hash) or _digest(account_id) != accepted_account_hash.lower():
            raise AcceptanceBlocked("ACCOUNT_BINDING_INVALID")
        self.api, self.account_id, self.accepted_account_hash, self.store = api, account_id, accepted_account_hash, store
        self.entry_attempted = False
        self.order_endpoint_call_count = 0

    @staticmethod
    def _payload(request: OrderRequest) -> dict[str, Any]:
        if type(request.quantity) is not int or request.quantity != MAX_ACCEPTANCE_QUANTITY:
            raise AcceptanceBlocked("STAGE8_11_QUANTITY_MUST_EQUAL_ONE")
        client_id = compact_client_order_id(request.idempotency_key)
        if len(client_id) > CLIENT_ORDER_ID_MAX_LENGTH:
            raise AssertionError("CLIENT_ORDER_ID_TOO_LONG")
        return {"symbol": request.contract_id, "quantity": {"value": "1"},
                "side": broker_side(request.direction, exit_order=request.exit_order),
                "type": MARKET_ORDER_TYPE, "time_in_force": TIME_IN_FORCE_DAY,
                "client_order_id": client_id}

    def _post_once(self, request: OrderRequest) -> dict[str, Any]:
        payload = self._payload(request)
        if not self.store.persist_intent(request.idempotency_key, payload):
            raise AcceptanceBlocked("INTENT_ALREADY_EXISTS_RECONCILIATION_REQUIRED")
        try:
            self.order_endpoint_call_count += 1  # no retry: exactly one call for this intent
            result = self.api.place_order(self.account_id, payload)
        except FinamUncertainSubmission:
            self.store.transition_intent(request.idempotency_key, "UNCERTAIN")
            raise
        except FinamOrderRejected:
            # The server conclusively rejected this one POST.  Close the durable
            # pre-POST intent; never attempt reconciliation as an accepted order.
            self.store.transition_intent(request.idempotency_key, "REJECTED")
            raise
        order_id = str(result.get("order_id", "")) if isinstance(result, dict) else ""
        if not order_id:
            self.store.transition_intent(request.idempotency_key, "UNCERTAIN")
            raise FinamUncertainSubmission("RECONCILIATION_REQUIRED")
        self.store.transition_intent(request.idempotency_key, "ACK", order_id)
        return result

    def submit_entry(self, *, key: str, finam_symbol: str, direction: str) -> dict[str, Any]:
        if self.entry_attempted:
            raise AcceptanceBlocked("SECOND_ENTRY_FORBIDDEN")
        self.entry_attempted = True
        return self._post_once(OrderRequest(key, finam_symbol, direction, 1))

    def submit_flatten(self, *, key: str, finam_symbol: str, direction: str) -> dict[str, Any]:
        if not self.entry_attempted:
            raise AcceptanceBlocked("NO_ACCEPTANCE_ENTRY_TO_FLATTEN")
        return self._post_once(OrderRequest(key, finam_symbol, direction, 1, exit_order=True))

    def snapshot(self, key: str) -> dict[str, Any]:
        intent = self.store.intent(key)
        if not intent:
            raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
        return _production_snapshot(self.api, self.account_id, intent)

    def position_snapshot(self, finam_symbol: str) -> dict[str, Any]:
        """Return only account-position facts; never query orders, order detail or trades."""
        return _production_position_snapshot(self.api, self.account_id, finam_symbol)

    def account_snapshot(self, finam_symbol: str) -> dict[str, Any]:
        """Return sanitized account + active-order facts for pre/final cleanliness checks."""
        return _production_account_snapshot(self.api, self.account_id, finam_symbol, self.store)

    def require_active_trading_session(self, finam_symbol: str, now: datetime, *,
                                       minimum_remaining: timedelta | None = None) -> None:
        """Use a fresh exact-symbol FINAM schedule as the sole session authority."""
        from .readonly_supervisor import SafetyFault, trading_h1_windows
        try:
            windows = trading_h1_windows(self.api.schedule(finam_symbol))
        except (SafetyFault, AttributeError, TypeError, ValueError):
            raise AcceptanceBlocked("STAGE8_11_TRADING_SCHEDULE_INVALID") from None
        observed = now.astimezone(timezone.utc)
        active = [(start, end) for start, end in windows if start <= observed < end]
        if not active:
            raise AcceptanceBlocked("STAGE8_11_TRADING_SESSION_NOT_OPEN")
        if minimum_remaining is not None and max(end for _, end in active) - observed < minimum_remaining:
            raise AcceptanceBlocked("STAGE8_11_ENTRY_SESSION_SAFETY_MARGIN_NOT_MET")

    def cancel(self, order_id: str) -> Any:
        if not order_id:
            raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
        return self.api.cancel_order(self.account_id, order_id)


def canonical_controlled_acceptance_broker(*, api:object, account_id:str,
                                           runtime_root:Path)->ControlledAcceptanceBroker:
    """Back up and construct the adapter only with the canonical ledger."""
    path=initialize_stage8_11_acceptance_ledger(runtime_root,account_id)
    if path.resolve()!=stage8_11_acceptance_path(runtime_root).resolve():
        raise AcceptanceBlocked("ACCEPTANCE_LEDGER_AUTHORITY_INVALID")
    # Local import avoids coupling the order-incapable PRECHECK to backup/execution code.
    from .backup_state import create_stage8_11_acceptance_backup
    create_stage8_11_acceptance_backup(runtime_root,account_id)
    return ControlledAcceptanceBroker(api,account_id,_digest(account_id),StateStore(path))


def _rows(response: Any, key: str) -> list[dict[str, Any]]:
    """Read one documented REST collection shape and reject every other shape."""
    rows = response.get(key) if isinstance(response, dict) else None
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
    return rows


def _rest_decimal(value: Any) -> Decimal:
    """Parse the exact FINAM REST Decimal ``{"value": "..."}`` representation."""
    if not isinstance(value, dict) or set(value) != {"value"} or not isinstance(value["value"], str):
        raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
    try:
        parsed = Decimal(value["value"])
    except InvalidOperation:
        raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED") from None
    if not parsed.is_finite():
        raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
    return parsed


def _decimal_contracts(value: Any) -> int:
    """Parse a FINAM REST Decimal which must represent whole contracts."""
    parsed = _rest_decimal(value)
    if parsed != parsed.to_integral_value():
        raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
    return int(parsed)


_REST_TIMESTAMP = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2})T(?P<time>\d{2}:\d{2}:\d{2})"
    r"(?:\.(?P<fraction>\d{1,9}))?(?P<zone>Z|[+-]\d{2}:\d{2})$"
)
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def _timestamp(value: Any) -> tuple[int, int]:
    """Parse a FINAM REST RFC3339 Timestamp into exact UTC seconds/nanoseconds."""
    if not isinstance(value, str) or not value:
        raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
    match = _REST_TIMESTAMP.fullmatch(value)
    if match is None:
        raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
    fraction = match.group("fraction") or ""
    zone = "+00:00" if match.group("zone") == "Z" else match.group("zone")
    try:
        parsed = datetime.fromisoformat(
            f'{match.group("date")}T{match.group("time")}{zone}'
        ).astimezone(timezone.utc)
    except ValueError:
        raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED") from None
    delta = parsed - _EPOCH
    return delta.days * 86_400 + delta.seconds, int(fraction.ljust(9, "0") or "0")


def _status(value: Any) -> str:
    try:
        return normalize_order_status(value)
    except ValueError:
        raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED") from None


def _production_account(api: object, account_id: str) -> list[dict[str, Any]]:
    account = api.account(account_id)
    if not isinstance(account, dict):
        raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
    return _rows(account, "positions")


def _position(positions: list[dict[str, Any]], symbol: str) -> int:
    matches = [row for row in positions if row.get("symbol") == symbol]
    if len(matches) > 1:
        raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
    return 0 if not matches else _decimal_contracts(matches[0].get("quantity"))


def _production_position_snapshot(api: object, account_id: str, symbol: str) -> dict[str, Any]:
    """Read only /account positions for synchronous post-submit reconciliation."""
    positions = _production_account(api, account_id)
    selected_position = _position(positions, symbol)
    unexpected_positions = 0
    for row in positions:
        row_symbol = row.get("symbol")
        if not isinstance(row_symbol, str) or not row_symbol:
            raise OperatorInterventionRequired("POSITION_RECONCILIATION_ACCOUNT_SCHEMA_INVALID")
        quantity = _decimal_contracts(row.get("quantity"))
        if row_symbol != symbol and quantity != 0:
            unexpected_positions += 1
    return {
        "acceptance_instrument": symbol,
        "position_quantity": selected_position,
        "unexpected_position_count": unexpected_positions,
    }


def _production_snapshot(api: object, account_id: str, intent: dict[str, Any]) -> dict[str, Any]:
    """Reconcile one persisted intent through FinamAPI's actual read primitives."""
    payload = intent.get("payload")
    if not isinstance(payload, dict):
        raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
    client_id, symbol, side = (payload.get("client_order_id"), payload.get("symbol"), payload.get("side"))
    if not all(isinstance(value, str) and value for value in (client_id, symbol, side)):
        raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
    persisted_id = intent.get("broker_order_id")
    if persisted_id is not None and (not isinstance(persisted_id, str) or not persisted_id):
        raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
    candidates = [row for row in _rows(api.orders(account_id), "orders")
                  if isinstance(row.get("order"), dict)
                  and row["order"].get("client_order_id") == client_id]
    candidate_ids = []
    for row in candidates:
        order_id = row.get("order_id")
        if not isinstance(order_id, str) or not order_id:
            raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
        if order_id not in candidate_ids:
            candidate_ids.append(order_id)

    if persisted_id:
        if candidate_ids and any(order_id != persisted_id for order_id in candidate_ids):
            raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
        listed_id = persisted_id
    else:
        if len(candidate_ids) > 1:
            raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
        if len(candidate_ids) == 1:
            listed_id = candidate_ids[0]
        else:
            raise ReconciliationPending("ORDER_COLLECTION_PROPAGATION_PENDING")
    positions = _production_account(api, account_id)
    position_quantity = _position(positions, symbol)
    try:
        order = api.order(account_id, listed_id)
    except FinamNotFound:
        if not persisted_id:
            raise ReconciliationPending("ORDER_DETAIL_PROPAGATION_PENDING") from None
        return {
            "order_status": "ORDER_DETAIL_PENDING",
            "order_id": listed_id,
            "client_order_id": client_id,
            "executed_quantity": 0,
            "fills": [],
            "trade_propagation_pending": True,
            "broker_acknowledged": True,
            "order_detail_pending": True,
            "acceptance_instrument": symbol,
            "position_quantity": position_quantity,
        }
    request = order.get("order") if isinstance(order, dict) else None
    if (not isinstance(order, dict) or order.get("order_id") != listed_id
            or not isinstance(request, dict) or request.get("account_id") != account_id
            or request.get("client_order_id") != client_id or request.get("symbol") != symbol
            or request.get("side") != side or _decimal_contracts(request.get("quantity")) != 1):
        raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
    initial = _decimal_contracts(order.get("initial_quantity"))
    executed = _decimal_contracts(order.get("executed_quantity"))
    remaining = _decimal_contracts(order.get("remaining_quantity"))
    if initial != 1 or executed not in (0, 1) or remaining not in (0, 1) or executed + remaining != initial:
        raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
    accepted_at = _timestamp(order.get("accept_at"))
    # /trades is supplementary evidence only. Real FINAM can return HTTP 400
    # for this account endpoint even while the exact order and account position
    # are readable. A read-side /trades failure must never block recognition of
    # an already acknowledged one-contract position or its controlled flatten.
    try:
        trades = _rows(api.trades(account_id), "trades")
    except FinamError:
        trades = []
    matching = []
    for trade in trades:
        if trade.get("order_id") != listed_id:
            continue
        if (trade.get("account_id") != account_id or trade.get("symbol") != symbol
                or trade.get("side") != side or _decimal_contracts(trade.get("size")) != 1
                or _timestamp(trade.get("timestamp")) < accepted_at):
            raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
        if not isinstance(trade.get("trade_id"), str) or not trade["trade_id"]:
            raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
        _rest_decimal(trade.get("price"))
        matching.append({"fill_id": trade["trade_id"], "trade_id": trade["trade_id"],
                         "broker_order_id": listed_id, "quantity": "1", "price": trade["price"]["value"],
                         "timestamp": json.dumps(trade["timestamp"], sort_keys=True, separators=(",", ":"))})
    # One matching trade may become visible before the order-detail
    # executed_quantity field converges. Multiple matching trades still violate
    # the fixed one-contract acceptance boundary and fail closed.
    if len(matching) > 1:
        raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
    return {"order_status": _status(order.get("status")), "order_id": listed_id,
            "client_order_id": client_id, "executed_quantity": executed, "fills": matching,
            "trade_propagation_pending": len(matching) < executed,
            "broker_acknowledged": persisted_id is not None,
            "order_detail_pending": False,
            "acceptance_instrument": symbol, "position_quantity": position_quantity}


def _production_account_snapshot(api: object, account_id: str, symbol: str, store: StateStore) -> dict[str, Any]:
    positions = _production_account(api, account_id)
    selected_position = _position(positions, symbol)
    unexpected_positions = 0
    for row in positions:
        row_symbol = row.get("symbol")
        if not isinstance(row_symbol, str) or not row_symbol:
            raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
        quantity = _decimal_contracts(row.get("quantity"))
        if row_symbol != symbol and quantity != 0:
            unexpected_positions += 1
    order_rows = _rows(api.orders(account_id), "orders")
    try:
        active = count_active_orders(order_rows)
    except ValueError:
        raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED") from None
    return {"acceptance_instrument": symbol, "position_quantity": selected_position,
            "unexpected_position_count": unexpected_positions,
            "active_order_count": active, "reconciled": True}


def _final_state(broker: ControlledAcceptanceBroker, finam_symbol: str) -> dict[str, Any]:
    """Capture only actually observed account and canonical-ledger facts."""
    final = broker.account_snapshot(finam_symbol)
    return {**final, "unresolved_intent_count": broker.store.unresolved_intent_count()}


def _account_is_clean(final: dict[str, Any]) -> bool:
    return (type(final.get("position_quantity")) is int
            and final["position_quantity"] == 0
            and type(final.get("unexpected_position_count")) is int
            and final["unexpected_position_count"] == 0
            and type(final.get("active_order_count")) is int
            and final["active_order_count"] == 0
            and type(final.get("unresolved_intent_count")) is int
            and final["unresolved_intent_count"] == 0
            and final.get("reconciled") is True)


def _reconcile_position(*, broker: ControlledAcceptanceBroker, key: str,
                        finam_symbol: str, expected_position: int,
                        pending_position: int,
                        sleeper: Callable[[float], None] = time.sleep) -> dict[str, Any]:
    """Reconcile one submitted intent using only the exact account position.

    Normal Stage 8.11 fill detection intentionally does not query /trades,
    /orders/{id}, order status, executed_quantity or remaining_quantity.
    The account position is the synchronous risk authority.
    """
    if expected_position not in (-1, 0, 1) or pending_position not in (-1, 0, 1):
        raise OperatorInterventionRequired("POSITION_RECONCILIATION_CONFIGURATION_INVALID")
    if expected_position == pending_position:
        raise OperatorInterventionRequired("POSITION_RECONCILIATION_CONFIGURATION_INVALID")

    for observation in range(POSITION_RECONCILIATION_MAX_OBSERVATIONS):
        snap = broker.position_snapshot(finam_symbol)
        position = snap.get("position_quantity")
        unexpected = snap.get("unexpected_position_count")
        if type(position) is not int or type(unexpected) is not int:
            raise OperatorInterventionRequired("POSITION_RECONCILIATION_ACCOUNT_SCHEMA_INVALID")
        if unexpected != 0:
            raise OperatorInterventionRequired("POSITION_RECONCILIATION_UNEXPECTED_OTHER_POSITION")

        if position == expected_position:
            intent = broker.store.intent(key)
            if not intent:
                raise OperatorInterventionRequired("POSITION_RECONCILIATION_INTENT_MISSING")
            broker_id = intent.get("broker_order_id")
            broker.store.transition_intent(key, "FILL", broker_id if isinstance(broker_id, str) and broker_id else None)
            broker.store.transition_intent(key, "RECONCILED", broker_id if isinstance(broker_id, str) and broker_id else None)
            return {**snap, "executed_quantity": 1, "position_authoritative": True}

        if position != pending_position:
            raise OperatorInterventionRequired("POSITION_RECONCILIATION_UNEXPECTED_QUANTITY")

        if observation + 1 >= POSITION_RECONCILIATION_MAX_OBSERVATIONS:
            raise OperatorInterventionRequired("POSITION_RECONCILIATION_TIMEOUT")
        sleeper(POSITION_RECONCILIATION_SLEEP_SECONDS)

    raise OperatorInterventionRequired("POSITION_RECONCILIATION_TIMEOUT")


def _reconcile(broker: ControlledAcceptanceBroker, key: str, *, allow_cancel: bool,
               expected_position: int | None = None,
               sleeper: Callable[[float], None] = time.sleep) -> dict[str, Any]:
    """Bounded broker-to-StateStore reconciliation for one persisted intent.

    FINAM read endpoints may become mutually consistent a few observations
    after an acknowledged POST.  Only structurally valid propagation gaps are
    retried.  Identity/schema violations remain fail-closed immediately.
    """
    cancelled = False
    for observation in range(RECONCILIATION_MAX_OBSERVATIONS):
        try:
            snap = broker.snapshot(key)
        except ReconciliationPending as exc:
            if observation + 1 >= RECONCILIATION_MAX_OBSERVATIONS:
                raise OperatorInterventionRequired("RECONCILIATION_TIMEOUT") from exc
            sleeper(RECONCILIATION_SLEEP_SECONDS)
            continue

        status = str(snap.get("order_status", "UNKNOWN")).upper()
        order_id = str(snap.get("order_id", ""))
        filled = int(snap.get("executed_quantity", 0))
        position = snap.get("position_quantity")

        # A persisted broker ACK plus the exact expected account position is
        # sufficient proof of a one-contract state transition while FINAM's
        # order-detail read model is still propagating. This applies only to
        # pending/active read-side states; terminal contradictory states remain
        # fail-closed below.
        ack_position_proven = (
            snap.get("broker_acknowledged") is True
            and expected_position is not None
            and type(position) is int
            and position == expected_position
            and (snap.get("order_detail_pending") is True
                 or status in ACTIVE
                 or status in TERMINAL_FILL)
        )
        if ack_position_proven:
            for fill in snap.get("fills", []):
                broker.store.persist_fill(fill)
            broker.store.transition_intent(key, "FILL", order_id)
            broker.store.transition_intent(key, "RECONCILED", order_id)
            return {**snap, "executed_quantity": 1}

        if status in ACTIVE:
            # A newly acknowledged market order may remain ACTIVE/PENDING for a
            # few read observations while FINAM propagates execution state.
            # Observe first; cancel at most once only after the fixed grace
            # window. This avoids manufacturing a cancel race from normal
            # read-side eventual consistency.
            if (allow_cancel and not cancelled
                    and observation + 1 >= RECONCILIATION_ACTIVE_GRACE_OBSERVATIONS):
                broker.cancel(order_id)
                cancelled = True
            if observation + 1 >= RECONCILIATION_MAX_OBSERVATIONS:
                raise OperatorInterventionRequired("RECONCILIATION_TIMEOUT")
            sleeper(RECONCILIATION_SLEEP_SECONDS)
            continue

        fills = snap.get("fills", [])
        if status in TERMINAL_FILL and filled == 1:
            if expected_position is None or type(position) is not int:
                raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
            if position != expected_position:
                if position in (-1, 0, 1) and expected_position in (-1, 0, 1):
                    if observation + 1 >= RECONCILIATION_MAX_OBSERVATIONS:
                        raise OperatorInterventionRequired("RECONCILIATION_TIMEOUT")
                    sleeper(RECONCILIATION_SLEEP_SECONDS)
                    continue
                raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
            if not fills and snap.get("trade_propagation_pending") is not True:
                raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
            for fill in fills:
                broker.store.persist_fill(fill)
            broker.store.transition_intent(key, "FILL", order_id)
            broker.store.transition_intent(key, "RECONCILED", order_id)
            return snap

        if status in TERMINAL_FILL and filled != 1:
            # FINAM can advance terminal status before both executed_quantity
            # and the account position read model converge. With a persisted
            # broker ACK, a structurally valid one-contract state is retried
            # within the same bounded reconciliation window; it is never
            # reinterpreted as a fill until the exact expected position appears.
            if (snap.get("broker_acknowledged") is True
                    and filled == 0
                    and expected_position is not None
                    and type(position) is int
                    and position in (-1, 0, 1)):
                if observation + 1 >= RECONCILIATION_MAX_OBSERVATIONS:
                    raise OperatorInterventionRequired("RECONCILIATION_TIMEOUT")
                sleeper(RECONCILIATION_SLEEP_SECONDS)
                continue
            raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")

        # A cancel can race with a complete one-contract market fill.
        # FINAM may therefore report terminal CANCELLED together with
        # executed_quantity=1.  This is an execution, not a no-fill outcome,
        # but it is accepted only when the exact expected account position is
        # independently observed.
        if status == "CANCELLED" and filled == 1:
            if expected_position is None or type(position) is not int:
                raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
            if position != expected_position:
                if position in (-1, 0, 1) and expected_position in (-1, 0, 1):
                    if observation + 1 >= RECONCILIATION_MAX_OBSERVATIONS:
                        raise OperatorInterventionRequired("RECONCILIATION_TIMEOUT")
                    sleeper(RECONCILIATION_SLEEP_SECONDS)
                    continue
                raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
            if not fills and snap.get("trade_propagation_pending") is not True:
                raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
            for fill in fills:
                broker.store.persist_fill(fill)
            broker.store.transition_intent(key, "FILL", order_id)
            broker.store.transition_intent(key, "RECONCILED", order_id)
            return snap

        if status in TERMINAL_NO_FILL and filled != 0:
            raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")

        if status in TERMINAL_NO_FILL and filled == 0:
            position = snap.get("position_quantity")
            if type(position) is not int:
                raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
            if position != 0:
                if position in (-1, 1):
                    if observation + 1 >= RECONCILIATION_MAX_OBSERVATIONS:
                        raise OperatorInterventionRequired("RECONCILIATION_TIMEOUT")
                    sleeper(RECONCILIATION_SLEEP_SECONDS)
                    continue
                raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
            broker.store.transition_intent(
                key, "CANCELLED" if status == "CANCELLED" else "REJECTED", order_id or None)
            return snap

        # A documented FINAM state outside the exchange-market-order lifecycle
        # (for example REPLACED/DISABLED/SL/TP states) is structurally real but
        # not safe to reinterpret for Stage 8.11.
        raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")

    raise OperatorInterventionRequired("RECONCILIATION_TIMEOUT")


def run_controlled_lifecycle(*, authority: AcceptanceAuthority, runtime_root: Path,
                             execution_authorized: bool, instrument: str, finam_symbol: str,
                             direction: str, broker: ControlledAcceptanceBroker,
                             now: datetime | None = None,
                             clock: Callable[[], datetime] | None = None,
                             sleeper: Callable[[float], None] = time.sleep,
                             attempt_id: str | None = None) -> dict[str, Any]:
    """Execute the bounded lifecycle with account position as fill authority."""
    time_source = clock or ((lambda: now) if now is not None else lambda: datetime.now(timezone.utc))
    observed = time_source()
    phases = ["PRECHECK"]
    result: dict[str, Any] = {"classification": "BLOCKED", "phases": phases, "order_endpoint_call_count": 0}
    if attempt_id is not None and attempt_id not in ALLOWED_ATTEMPT_IDS:
        raise AcceptanceBlocked("STAGE8_11_ATTEMPT_ID_INVALID")
    intent_prefix = attempt_id or "stage8.11"
    entry_key = f"{intent_prefix}:{instrument}:entry"
    flatten_key = f"{intent_prefix}:{instrument}:flatten"
    expected_position = 1 if direction == "LONG" else -1

    try:
        if broker.accepted_account_hash.lower() != authority.configured_account_hash.lower():
            raise AcceptanceBlocked("ACCOUNT_BINDING_INVALID")
        if finam_symbol != resolve_frozen_symbol(instrument):
            raise AcceptanceBlocked("FINAM_SYMBOL_BINDING_INVALID")

        checked = precheck(
            authority=authority, runtime_root=runtime_root, now=observed,
            execution_authorized=execution_authorized, instrument=instrument)
        result["precheck"] = checked
        if checked["decision"] != "AUTHORIZED":
            raise AcceptanceBlocked("|".join(checked["reason_codes"]))
        if direction not in ("LONG", "SHORT"):
            raise AcceptanceBlocked("DIRECTION_INVALID")
        phases.append("AUTHORIZED")

        entry_observed = time_source()
        broker.require_active_trading_session(
            finam_symbol, entry_observed, minimum_remaining=ENTRY_MINIMUM_REMAINING_SESSION)

        # Fresh immediate pre-submit authority. /orders is used here only to
        # prove that the account begins flat with zero active broker orders.
        pre_submit = _final_state(broker, finam_symbol)
        if not _account_is_clean(pre_submit):
            raise AcceptanceBlocked("STAGE8_11_PRE_SUBMIT_ACCOUNT_NOT_CLEAN")
        phases.extend(["ACTIVE_TRADING_SESSION_PROVEN", "PRE_SUBMIT_ACCOUNT_CLEAN_PROVEN"])

        try:
            broker.submit_entry(key=entry_key, finam_symbol=finam_symbol, direction=direction)
            phases.append("ENTRY_ACKNOWLEDGED")
        except FinamOrderRejected as exc:
            phases.append("ENTRY_DEFINITIVE_REJECTION")
            final = _final_state(broker, finam_symbol)
            result["final_state"] = final
            result["rejection"] = {
                "http_status": exc.status,
                "category": exc.category,
                "request_id": exc.request_id,
                "broker_acknowledgement_present": False,
            }
            if not _account_is_clean(final):
                raise OperatorInterventionRequired("DEFINITIVE_REJECTION_ACCOUNT_NOT_CLEAN")
            phases.append("FINAL_RECONCILIATION_PASS")
            result.update(
                classification="NOT_ACCEPTED_NO_EXECUTION",
                failure_code="DEFINITIVE_REJECTION",
                entry_fill_proven=False,
                one_contract_position_observed=False,
                flatten_fill_proven=False,
            )
            return result
        except FinamUncertainSubmission:
            # The POST may have reached FINAM. Position remains the risk
            # authority: if the contract appears, controlled flatten proceeds.
            phases.append("ENTRY_SUBMISSION_UNCERTAIN_POSITION_RECONCILE")

        entry = _reconcile_position(
            broker=broker, key=entry_key, finam_symbol=finam_symbol,
            expected_position=expected_position, pending_position=0, sleeper=sleeper)
        phases.extend(["ENTRY_POSITION_RECONCILED", "ONE_CONTRACT_POSITION_OBSERVED"])
        result.update(entry_fill_proven=True, one_contract_position_observed=True)

        try:
            flatten_observed = time_source()
            broker.require_active_trading_session(finam_symbol, flatten_observed)
            broker.submit_flatten(key=flatten_key, finam_symbol=finam_symbol, direction=direction)
            phases.append("FLATTEN_ACKNOWLEDGED")
        except AcceptanceBlocked as exc:
            try:
                result["final_state"] = _final_state(broker, finam_symbol)
            except Exception:
                pass
            result["flatten_fill_proven"] = False
            if str(exc) in {
                "STAGE8_11_TRADING_SESSION_NOT_OPEN",
                "STAGE8_11_TRADING_SCHEDULE_INVALID",
            }:
                raise OperatorInterventionRequired("FLATTEN_TRADING_SESSION_NOT_OPEN") from exc
            raise OperatorInterventionRequired(f"FLATTEN_BLOCKED:{exc}") from exc
        except FinamUncertainSubmission:
            phases.append("FLATTEN_SUBMISSION_UNCERTAIN_POSITION_RECONCILE")

        _reconcile_position(
            broker=broker, key=flatten_key, finam_symbol=finam_symbol,
            expected_position=0, pending_position=expected_position, sleeper=sleeper)
        phases.append("FLATTEN_POSITION_RECONCILED")

        final = _final_state(broker, finam_symbol)
        if not _account_is_clean(final):
            raise OperatorInterventionRequired("FINAL_ACCOUNT_NOT_CLEAN")
        phases.extend(["FINAL_RECONCILIATION_PASS", "HALTED"])
        result.update(
            classification="SYNTHETIC_PASS",
            entry_fill_proven=True,
            one_contract_position_observed=True,
            flatten_fill_proven=True,
            final_state=final,
        )

    except OperatorInterventionRequired as exc:
        if "final_state" not in result:
            try:
                result["final_state"] = _final_state(broker, finam_symbol)
            except Exception:
                pass
        phases.extend(["OPERATOR_INTERVENTION_REQUIRED", "HALTED"])
        result.update(classification="OPERATOR_INTERVENTION_REQUIRED", failure_code=str(exc))

    except AcceptanceBlocked as exc:
        phases.append("HALTED")
        result["failure_code"] = str(exc)

    except Exception as exc:
        # After any attempted POST, make one risk-reduction inspection using
        # /account positions only. If the exact one-contract risk exists and no
        # flatten intent was created yet, use the one allowed flatten POST.
        phases.append("POST_SUBMISSION_EXCEPTION_POSITION_RECOVERY")
        if broker.order_endpoint_call_count:
            try:
                position = broker.position_snapshot(finam_symbol)
                current = position.get("position_quantity")
                unexpected = position.get("unexpected_position_count")
                if type(current) is not int or type(unexpected) is not int or unexpected != 0:
                    raise OperatorInterventionRequired("POSITION_RECOVERY_ACCOUNT_INVALID")

                entry_intent = broker.store.intent(entry_key)
                flatten_intent = broker.store.intent(flatten_key)
                if current == expected_position and flatten_intent is None:
                    if entry_intent and entry_intent.get("status") not in ("RECONCILED", "CLOSED"):
                        broker_id = entry_intent.get("broker_order_id")
                        broker.store.transition_intent(
                            entry_key, "FILL",
                            broker_id if isinstance(broker_id, str) and broker_id else None)
                        broker.store.transition_intent(
                            entry_key, "RECONCILED",
                            broker_id if isinstance(broker_id, str) and broker_id else None)
                    recovery_observed = time_source()
                    broker.require_active_trading_session(finam_symbol, recovery_observed)
                    broker.submit_flatten(
                        key=flatten_key, finam_symbol=finam_symbol, direction=direction)
                    _reconcile_position(
                        broker=broker, key=flatten_key, finam_symbol=finam_symbol,
                        expected_position=0, pending_position=expected_position, sleeper=sleeper)
                result["final_state"] = _final_state(broker, finam_symbol)
            except Exception:
                phases.append("RECOVERY_POSITION_RECONCILIATION_INCOMPLETE")

            phases.extend(["OPERATOR_INTERVENTION_REQUIRED", "HALTED"])
            result.update(
                classification="OPERATOR_INTERVENTION_REQUIRED",
                failure_code=f"POST_SUBMISSION_EXCEPTION:{type(exc).__name__}")
        else:
            phases.append("HALTED")
            result["failure_code"] = f"PRE_SUBMISSION_EXCEPTION:{type(exc).__name__}"

    finally:
        emergency_halt(runtime_root, now=observed)
        result["order_endpoint_call_count"] = broker.order_endpoint_call_count
        result["kill_switch_final_state"] = "HALTED"

    return result


_PREFLIGHT_KEYS = frozenset({"account_binding", "credential_scope", "session_write_capable",
                             "initial_reconciliation", "instrument_binding", "instrument_tradable",
                             "r15_capacity", "margin_capacity", "h1_data_safety"})


def sanitized_evidence(**facts: Any) -> dict[str, Any]:
    """Build and validate the strictly allowlisted repository-safe evidence shape."""
    allowed = {"attempt_id", "accepted_code_commit", "sanitized_account_identity_hash", "instrument", "direction",
               "quantity", "preflight_gate_outcomes", "kill_switch_pre_state", "kill_switch_final_state",
               "execution_authorization_observed", "order_endpoint_call_count", "broker_order_present",
               "broker_fill_count", "entry_fill_proven", "one_contract_position_observed",
               "controlled_flatten_proven", "final_position_quantity", "final_active_order_count",
               "unresolved_intent_count", "reconciliation_result", "physical_result_classification",
               "external_raw_evidence_sha256"}
    if set(facts) - allowed:
        raise ValueError("EVIDENCE_FIELD_NOT_ALLOWLISTED")
    if facts.get("attempt_id") not in ALLOWED_ATTEMPT_IDS:
        raise ValueError("EVIDENCE_ATTEMPT_ID_INVALID")
    gates = facts.get("preflight_gate_outcomes", {})
    if not isinstance(gates, dict) or set(gates) - _PREFLIGHT_KEYS or any(type(v) is not bool for v in gates.values()):
        raise ValueError("PREFLIGHT_EVIDENCE_SCHEMA_INVALID")
    if facts.get("quantity") != 1:
        raise ValueError("EVIDENCE_QUANTITY_MUST_EQUAL_ONE")
    for key in ("sanitized_account_identity_hash", "external_raw_evidence_sha256"):
        if key in facts and not _sha256(facts[key]):
            raise ValueError("EVIDENCE_SHA256_INVALID")
    classification = facts.get("physical_result_classification")
    if classification == "PASS":
        required = (facts.get("instrument") in INSTRUMENTS, facts.get("direction") in ("LONG", "SHORT"),
            facts.get("kill_switch_pre_state") == "ARMED", facts.get("execution_authorization_observed") is True,
            facts.get("entry_fill_proven") is True, facts.get("one_contract_position_observed") is True,
            facts.get("controlled_flatten_proven") is True, facts.get("final_position_quantity") == 0,
            facts.get("final_active_order_count") == 0, facts.get("unresolved_intent_count") == 0,
            facts.get("reconciliation_result") == "PASS", facts.get("kill_switch_final_state") == "HALTED")
        if not all(required):
            raise ValueError("PASS_EVIDENCE_INVARIANTS_INVALID")
    if classification == "NOT_ACCEPTED_NO_EXECUTION":
        required = (facts.get("entry_fill_proven") is False,
            facts.get("one_contract_position_observed") is False,
            facts.get("controlled_flatten_proven") is False,
            facts.get("final_position_quantity") == 0,
            facts.get("final_active_order_count") == 0,
            facts.get("unresolved_intent_count") == 0,
            facts.get("reconciliation_result") == "PASS",
            facts.get("kill_switch_final_state") == "HALTED")
        if not all(required):
            raise ValueError("NOT_ACCEPTED_EVIDENCE_INVARIANTS_INVALID")
    evidence = {"schema_id": EVIDENCE_SCHEMA, "production_specification_id": PRODUCTION_SPECIFICATION_ID,
                "stage8_11_status": "PHYSICAL_RESULT_REQUIRES_INDEPENDENT_AUDIT", **facts}
    schema = json.loads(Path(__file__).with_name("stage8_11_physical_evidence.schema.json").read_text())
    try:
        import jsonschema
        jsonschema.validate(evidence, schema)
    except ImportError:  # structural checks above remain mandatory without optional dependency
        pass
    return evidence
