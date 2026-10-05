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

from .broker import OrderRequest, broker_side, compact_client_order_id
from .finam_api import (CLIENT_ORDER_ID_MAX_LENGTH, MARKET_ORDER_TYPE, TIME_IN_FORCE_DAY,
                        FinamNotFound, FinamOrderRejected, FinamUncertainSubmission)
from .instrument_resolver import load_registry
from .specification import ACTIVE_IDENTITY, INSTRUMENTS, PRODUCTION_SPECIFICATION_ID, load_frozen_specification
from .state import StateStore, initialize_stage8_11_acceptance_ledger, stage8_11_acceptance_path
from .trading_safety_gate import emergency_halt, evaluate_new_entry_gate, heartbeat_path

STAGE8_10_AUTHORITY = "STAGE_8_10_TRADING_TOKEN_LIFECYCLE_COMPLETE"
STAGE8_11_STATUS = "CODE_READY_PENDING_PHYSICAL_ACCEPTANCE"
EVIDENCE_SCHEMA = "stage8_11_physical_acceptance.v1"
STAGE8_11_ATTEMPT2_ID = "stage8.11.attempt2"
STAGE8_11_ATTEMPT3_ID = "stage8.11.attempt3"
ALLOWED_ATTEMPT_IDS = frozenset({STAGE8_11_ATTEMPT2_ID, STAGE8_11_ATTEMPT3_ID})
RECONCILIATION_MAX_OBSERVATIONS = 12
RECONCILIATION_SLEEP_SECONDS = 0.1
MAX_ACCEPTANCE_QUANTITY = 1
REGISTRY = Path(__file__).with_name("production_instrument_registry.csv")
TERMINAL_NO_FILL = frozenset({"REJECTED", "EXPIRED", "CANCELLED"})
ACTIVE = frozenset({"NEW", "PENDING", "ACTIVE", "PARTIAL_FILL"})
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

    def account_snapshot(self, finam_symbol: str) -> dict[str, Any]:
        """Return only the sanitized acceptance facts from the production API."""
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
    if not isinstance(value, str) or not value:
        raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
    status = value.upper().removeprefix("ORDER_STATUS_")
    aliases = {"PARTIALLY_FILLED": "PARTIAL_FILL", "CANCELED": "CANCELLED"}
    status = aliases.get(status, status)
    if status not in ACTIVE | TERMINAL_NO_FILL | {"FILLED"}:
        raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
    return status


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
    if len(candidates) > 1:
        raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
    if candidates:
        listed_id = candidates[0].get("order_id")
        if not isinstance(listed_id, str) or not listed_id:
            raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
        if persisted_id and persisted_id != listed_id:
            raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
    elif persisted_id:
        listed_id = persisted_id
    else:
        raise ReconciliationPending("ORDER_COLLECTION_PROPAGATION_PENDING")
    try:
        order = api.order(account_id, listed_id)
    except FinamNotFound:
        raise ReconciliationPending("ORDER_DETAIL_PROPAGATION_PENDING") from None
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
    positions = _production_account(api, account_id)
    trades = _rows(api.trades(account_id), "trades")
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
    if len(matching) > 1:
        raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
    if len(matching) != executed:
        raise ReconciliationPending("TRADE_PROPAGATION_PENDING")
    return {"order_status": _status(order.get("status")), "order_id": listed_id,
            "client_order_id": client_id, "executed_quantity": executed, "fills": matching,
            "acceptance_instrument": symbol, "position_quantity": _position(positions, symbol)}


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
    active = 0
    for row in _rows(api.orders(account_id), "orders"):
        # Account cleanliness is global.  An unrelated active order is not ours
        # to cancel, but it is proof that physical acceptance must stop.
        if _status(row.get("status")) in ACTIVE:
            active += 1
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

        if status in ACTIVE:
            if allow_cancel and not cancelled:
                broker.cancel(order_id)
                cancelled = True
            if observation + 1 >= RECONCILIATION_MAX_OBSERVATIONS:
                raise OperatorInterventionRequired("RECONCILIATION_TIMEOUT")
            sleeper(RECONCILIATION_SLEEP_SECONDS)
            continue

        fills = snap.get("fills", [])
        if status in ({"FILLED"} | TERMINAL_NO_FILL) and filled == 1 and fills:
            position = snap.get("position_quantity")
            if expected_position is not None:
                if type(position) is not int:
                    raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
                if position != expected_position:
                    if position in (-1, 0, 1) and expected_position in (-1, 0, 1):
                        if observation + 1 >= RECONCILIATION_MAX_OBSERVATIONS:
                            raise OperatorInterventionRequired("RECONCILIATION_TIMEOUT")
                        sleeper(RECONCILIATION_SLEEP_SECONDS)
                        continue
                    raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
            for fill in fills:
                broker.store.persist_fill(fill)
            broker.store.transition_intent(key, "FILL", order_id)
            broker.store.transition_intent(key, "RECONCILED", order_id)
            return snap

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
                key, status if status != "EXPIRED" else "REJECTED", order_id or None)
            return snap

        if observation + 1 >= RECONCILIATION_MAX_OBSERVATIONS:
            raise OperatorInterventionRequired("RECONCILIATION_TIMEOUT")
        sleeper(RECONCILIATION_SLEEP_SECONDS)

    raise OperatorInterventionRequired("RECONCILIATION_TIMEOUT")


def run_controlled_lifecycle(*, authority: AcceptanceAuthority, runtime_root: Path,
                             execution_authorized: bool, instrument: str, finam_symbol: str,
                             direction: str, broker: ControlledAcceptanceBroker,
                             now: datetime | None = None,
                             clock: Callable[[], datetime] | None = None,
                             attempt_id: str | None = None) -> dict[str, Any]:
    """Execute/reconcile the bounded lifecycle; PASS requires two proven fills."""
    # ``now`` remains a deterministic legacy test input. New boundary tests use
    # an injected clock whose every invocation is an independently observed UTC
    # instant. Production always calls the system clock afresh.
    time_source = clock or ((lambda: now) if now is not None else lambda: datetime.now(timezone.utc))
    observed = time_source()
    phases = ["PRECHECK"]
    result: dict[str, Any] = {"classification": "BLOCKED", "phases": phases, "order_endpoint_call_count": 0}
    if attempt_id is not None and attempt_id not in ALLOWED_ATTEMPT_IDS:
        raise AcceptanceBlocked("STAGE8_11_ATTEMPT_ID_INVALID")
    intent_prefix = attempt_id or "stage8.11"
    entry_key = f"{intent_prefix}:{instrument}:entry"
    flatten_key = f"{intent_prefix}:{instrument}:flatten"
    try:
        if broker.accepted_account_hash.lower() != authority.configured_account_hash.lower():
            raise AcceptanceBlocked("ACCOUNT_BINDING_INVALID")
        if finam_symbol != resolve_frozen_symbol(instrument):
            raise AcceptanceBlocked("FINAM_SYMBOL_BINDING_INVALID")
        checked = precheck(authority=authority, runtime_root=runtime_root, now=observed,
                           execution_authorized=execution_authorized, instrument=instrument)
        result["precheck"] = checked
        if checked["decision"] != "AUTHORIZED":
            raise AcceptanceBlocked("|".join(checked["reason_codes"]))
        if direction not in ("LONG", "SHORT"):
            raise AcceptanceBlocked("DIRECTION_INVALID")
        phases.append("AUTHORIZED")
        # This fresh schedule read is immediately before the only possible entry
        # POST.  A refusal occurs before persist_intent and therefore creates no
        # execution intent.
        entry_observed = time_source()
        broker.require_active_trading_session(
            finam_symbol, entry_observed, minimum_remaining=ENTRY_MINIMUM_REMAINING_SESSION)
        phases.append("ACTIVE_TRADING_SESSION_PROVEN")
        try:
            broker.submit_entry(key=entry_key, finam_symbol=finam_symbol, direction=direction)
        except FinamOrderRejected as exc:
            phases.append("ENTRY_DEFINITIVE_REJECTION")
            final = _final_state(broker, finam_symbol)
            result["final_state"] = final
            result["rejection"] = {"http_status": exc.status, "category": exc.category,
                                   "request_id": exc.request_id,
                                   "broker_acknowledgement_present": False}
            if not _account_is_clean(final):
                raise OperatorInterventionRequired("DEFINITIVE_REJECTION_ACCOUNT_NOT_CLEAN")
            phases.append("FINAL_RECONCILIATION_PASS")
            result.update(classification="NOT_ACCEPTED_NO_EXECUTION",
                          failure_code="DEFINITIVE_REJECTION", entry_fill_proven=False,
                          one_contract_position_observed=False, flatten_fill_proven=False)
            return result
        except FinamUncertainSubmission:
            phases.append("ENTRY_UNCERTAIN_RECONCILE")
        entry = _reconcile(broker, entry_key, allow_cancel=True,
                           expected_position=(1 if direction == "LONG" else -1))
        phases.append("ENTRY_RECONCILED")
        if int(entry.get("executed_quantity", 0)) != 1:
            final = _final_state(broker, finam_symbol)
            result["final_state"] = final
            if int(entry.get("executed_quantity", -1)) != 0 or not _account_is_clean(final):
                raise OperatorInterventionRequired("NO_FILL_FLAT_STATE_NOT_PROVEN")
            phases.append("FINAL_RECONCILIATION_PASS")
            result["classification"] = "NOT_ACCEPTED_NO_EXECUTION"
            result["failure_code"] = "ENTRY_NOT_FILLED"
            return result
        expected_position = 1 if direction == "LONG" else -1
        if int(entry.get("position_quantity", 0)) != expected_position:
            raise OperatorInterventionRequired("ONE_CONTRACT_POSITION_NOT_PROVEN")
        phases.append("ONE_CONTRACT_POSITION_OBSERVED")
        try:
            flatten_observed = time_source()
            broker.require_active_trading_session(finam_symbol, flatten_observed)
            broker.submit_flatten(key=flatten_key, finam_symbol=finam_symbol, direction=direction)
        except AcceptanceBlocked as exc:
            # Entry and the exact signed one-contract position are already
            # proved. A closed/malformed session is therefore an operator safety
            # event, never an ordinary pre-submission BLOCKED result.
            try:
                result["final_state"] = _final_state(broker, finam_symbol)
            except Exception:
                pass
            result.update(entry_fill_proven=True, one_contract_position_observed=True,
                          flatten_fill_proven=False)
            if str(exc) in {"STAGE8_11_TRADING_SESSION_NOT_OPEN",
                            "STAGE8_11_TRADING_SCHEDULE_INVALID"}:
                raise OperatorInterventionRequired("FLATTEN_TRADING_SESSION_NOT_OPEN") from exc
            raise OperatorInterventionRequired(f"FLATTEN_BLOCKED:{exc}") from exc
        except FinamUncertainSubmission:
            phases.append("FLATTEN_UNCERTAIN_RECONCILE")
        flatten = _reconcile(broker, flatten_key, allow_cancel=True, expected_position=0)
        phases.append("FLATTEN_RECONCILED")
        final = _final_state(broker, finam_symbol)
        flat = (int(flatten.get("executed_quantity", 0)) == 1
                and _account_is_clean(final))
        if not flat:
            raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
        phases.extend(["FINAL_RECONCILIATION_PASS", "HALTED"])
        result.update(classification="SYNTHETIC_PASS", entry_fill_proven=True,
                      one_contract_position_observed=True, flatten_fill_proven=True,
                      final_state=final)
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
        # Once a POST was attempted, runtime failures are safety events rather
        # than escaping exceptions.  Reconcile/cancel first and, only when the
        # exact entry fill and position are proved, use the one allowed flatten.
        phases.append("POST_SUBMISSION_EXCEPTION_RECONCILE")
        if broker.order_endpoint_call_count:
            try:
                entry_intent = broker.store.intent(entry_key)
                if entry_intent and entry_intent["status"] not in ("RECONCILED", "CANCELLED", "REJECTED"):
                    recovered_entry = _reconcile(broker, entry_key, allow_cancel=True,
                                                 expected_position=(1 if direction == "LONG" else -1))
                else:
                    recovered_entry = broker.snapshot(entry_key) if entry_intent else None
                flatten_intent = broker.store.intent(flatten_key)
                if (recovered_entry and int(recovered_entry.get("executed_quantity", 0)) == 1
                        and int(recovered_entry.get("position_quantity", 0)) == (1 if direction == "LONG" else -1)
                        and flatten_intent is None):
                    recovery_observed = time_source()
                    broker.require_active_trading_session(finam_symbol, recovery_observed)
                    broker.submit_flatten(key=flatten_key, finam_symbol=finam_symbol, direction=direction)
                    flatten_intent = broker.store.intent(flatten_key)
                if flatten_intent and flatten_intent["status"] not in ("RECONCILED", "CANCELLED", "REJECTED"):
                    _reconcile(broker, flatten_key, allow_cancel=True, expected_position=0)
                result["final_state"] = _final_state(broker, finam_symbol)
            except Exception:
                phases.append("RECOVERY_RECONCILIATION_INCOMPLETE")
            phases.extend(["OPERATOR_INTERVENTION_REQUIRED", "HALTED"])
            result.update(classification="OPERATOR_INTERVENTION_REQUIRED",
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
