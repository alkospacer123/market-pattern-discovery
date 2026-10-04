"""Stage 8.11's isolated, one-contract physical-acceptance boundary.

This module is intentionally absent from RuntimeConfig, runner, supervisor and
the Scheduled Task.  Its dependencies are injected; importing it cannot load a
credential, contact FINAM, arm the switch, or transmit an order.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

from .broker import OrderRequest, broker_side, compact_client_order_id
from .finam_api import CLIENT_ORDER_ID_MAX_LENGTH, MARKET_ORDER_TYPE, FinamUncertainSubmission
from .instrument_resolver import load_registry
from .specification import ACTIVE_IDENTITY, INSTRUMENTS, PRODUCTION_SPECIFICATION_ID, load_frozen_specification
from .state import StateStore
from .trading_safety_gate import emergency_halt, evaluate_new_entry_gate, heartbeat_path

STAGE8_10_AUTHORITY = "STAGE_8_10_TRADING_TOKEN_LIFECYCLE_COMPLETE"
STAGE8_11_STATUS = "CODE_READY_PENDING_PHYSICAL_ACCEPTANCE"
EVIDENCE_SCHEMA = "stage8_11_physical_acceptance.v1"
MAX_ACCEPTANCE_QUANTITY = 1
REGISTRY = Path(__file__).with_name("production_instrument_registry.csv")
TERMINAL_NO_FILL = frozenset({"REJECTED", "EXPIRED", "CANCELLED"})
ACTIVE = frozenset({"NEW", "PENDING", "ACTIVE", "PARTIAL_FILL"})


class AcceptanceBlocked(RuntimeError):
    """A sanitized deterministic refusal at the controlled boundary."""


class OperatorInterventionRequired(AcceptanceBlocked):
    """Safe flat state cannot be proved; an operator must inspect the account."""


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
                "type": MARKET_ORDER_TYPE, "client_order_id": client_id}

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
        client_id = intent["payload"]["client_order_id"] if intent else ""
        return self.api.acceptance_snapshot(self.account_id, client_id)

    def cancel(self, order_id: str) -> Any:
        if not order_id:
            raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
        return self.api.cancel_order(self.account_id, order_id)


def _reconcile(broker: ControlledAcceptanceBroker, key: str, *, allow_cancel: bool) -> dict[str, Any]:
    """Canonical broker-to-StateStore reconciliation for one persisted intent."""
    snap = broker.snapshot(key)
    status = str(snap.get("order_status", "UNKNOWN")).upper()
    order_id = str(snap.get("order_id", ""))
    if status in ACTIVE and allow_cancel:
        broker.cancel(order_id)
        snap = broker.snapshot(key)  # mandatory post-cancel reconciliation
        status = str(snap.get("order_status", "UNKNOWN")).upper()
        order_id = str(snap.get("order_id", order_id))
    for fill in snap.get("fills", []):
        broker.store.persist_fill(fill)
    filled = int(snap.get("filled_quantity", 0))
    # A cancel race may report CANCELLED after the single contract filled.  The
    # fill ledger, not the terminal label, is authoritative in that branch.
    if status in ({"FILLED"} | TERMINAL_NO_FILL) and filled == 1 and snap.get("fills"):
        broker.store.transition_intent(key, "FILL", order_id)
        broker.store.transition_intent(key, "RECONCILED", order_id)
    elif status in TERMINAL_NO_FILL and filled == 0:
        broker.store.transition_intent(key, status if status != "EXPIRED" else "REJECTED", order_id or None)
    else:
        raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
    return snap


def run_controlled_lifecycle(*, authority: AcceptanceAuthority, runtime_root: Path,
                             execution_authorized: bool, instrument: str, finam_symbol: str,
                             direction: str, broker: ControlledAcceptanceBroker,
                             now: datetime | None = None) -> dict[str, Any]:
    """Execute/reconcile the bounded lifecycle; PASS requires two proven fills."""
    observed = now or datetime.now(timezone.utc)
    phases = ["PRECHECK"]
    result: dict[str, Any] = {"classification": "BLOCKED", "phases": phases, "order_endpoint_call_count": 0}
    entry_key = f"stage8.11:{instrument}:entry"
    flatten_key = f"stage8.11:{instrument}:flatten"
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
        try:
            broker.submit_entry(key=entry_key, finam_symbol=finam_symbol, direction=direction)
        except FinamUncertainSubmission:
            phases.append("ENTRY_UNCERTAIN_RECONCILE")
        entry = _reconcile(broker, entry_key, allow_cancel=True)
        phases.append("ENTRY_RECONCILED")
        if int(entry.get("filled_quantity", 0)) != 1:
            result["classification"] = "NOT_ACCEPTED_NO_EXECUTION"
            result["failure_code"] = "ENTRY_NOT_FILLED"
            return result
        if abs(int(entry.get("position_quantity", 0))) != 1:
            raise OperatorInterventionRequired("ONE_CONTRACT_POSITION_NOT_PROVEN")
        phases.append("ONE_CONTRACT_POSITION_OBSERVED")
        try:
            broker.submit_flatten(key=flatten_key, finam_symbol=finam_symbol, direction=direction)
        except FinamUncertainSubmission:
            phases.append("FLATTEN_UNCERTAIN_RECONCILE")
        flatten = _reconcile(broker, flatten_key, allow_cancel=True)
        phases.append("FLATTEN_RECONCILED")
        final = broker.api.acceptance_account_snapshot(broker.account_id)
        flat = (int(flatten.get("filled_quantity", 0)) == 1
                and int(final.get("position_quantity", -999)) == 0
                and int(final.get("active_order_count", -1)) == 0
                and broker.store.unresolved_intent_count() == 0
                and final.get("reconciled") is True)
        if not flat:
            raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
        phases.extend(["FINAL_RECONCILIATION_PASS", "HALTED"])
        result.update(classification="SYNTHETIC_PASS", entry_fill_proven=True,
                      one_contract_position_observed=True, flatten_fill_proven=True,
                      final_state={**final, "unresolved_intent_count": 0})
    except OperatorInterventionRequired as exc:
        phases.extend(["OPERATOR_INTERVENTION_REQUIRED", "HALTED"])
        result.update(classification="OPERATOR_INTERVENTION_REQUIRED", failure_code=str(exc))
    except AcceptanceBlocked as exc:
        phases.append("HALTED")
        result["failure_code"] = str(exc)
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
    allowed = {"accepted_code_commit", "sanitized_account_identity_hash", "instrument", "direction",
               "quantity", "preflight_gate_outcomes", "kill_switch_pre_state", "kill_switch_final_state",
               "execution_authorization_observed", "order_endpoint_call_count", "broker_order_present",
               "broker_fill_count", "entry_fill_proven", "one_contract_position_observed",
               "controlled_flatten_proven", "final_position_quantity", "final_active_order_count",
               "unresolved_intent_count", "reconciliation_result", "physical_result_classification",
               "external_raw_evidence_sha256"}
    if set(facts) - allowed:
        raise ValueError("EVIDENCE_FIELD_NOT_ALLOWLISTED")
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
    evidence = {"schema_id": EVIDENCE_SCHEMA, "production_specification_id": PRODUCTION_SPECIFICATION_ID,
                "stage8_11_status": "PHYSICAL_RESULT_REQUIRES_INDEPENDENT_AUDIT", **facts}
    schema = json.loads(Path(__file__).with_name("stage8_11_physical_evidence.schema.json").read_text())
    try:
        import jsonschema
        jsonschema.validate(evidence, schema)
    except ImportError:  # structural checks above remain mandatory without optional dependency
        pass
    return evidence
