"""Stage 8.11 one-contract real-execution acceptance boundary.

This module is deliberately not wired into ``RuntimeConfig``, the normal
runner, or the Scheduled Task.  It is an operator-only state machine whose
dependencies are injected so the repository suite can exercise it without
credentials or network access.
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
from .specification import ACTIVE_IDENTITY, INSTRUMENTS, PRODUCTION_SPECIFICATION_ID, load_frozen_specification
from .state import StateStore
from .trading_safety_gate import emergency_halt, evaluate_new_entry_gate

STAGE8_10_AUTHORITY = "STAGE_8_10_TRADING_TOKEN_LIFECYCLE_COMPLETE"
STAGE8_11_STATUS = "CODE_READY_PENDING_PHYSICAL_ACCEPTANCE"
EVIDENCE_SCHEMA = "stage8_11_physical_acceptance.v1"
MAX_ACCEPTANCE_QUANTITY = 1


class AcceptanceBlocked(RuntimeError):
    """A sanitized, deterministic refusal at the controlled boundary."""


@dataclass(frozen=True)
class AcceptanceAuthority:
    production_specification_id: str
    active_identity: str
    stage8_10_status: str
    configured_account_hash: str
    observed_account_hash: str
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


def _sha256(value: str) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdefABCDEF" for c in value)


def precheck(*, authority: AcceptanceAuthority, runtime_root: Path, now: datetime,
             execution_authorized: bool, instrument: str) -> dict[str, Any]:
    """Validate every authority simultaneously; no check is advisory."""
    reasons: list[str] = []
    try:
        frozen = load_frozen_specification()
        if frozen.production_id != PRODUCTION_SPECIFICATION_ID or frozen.identity != ACTIVE_IDENTITY:
            reasons.append("FROZEN_STAGE7_AUTHORITY_INVALID")
    except Exception:
        reasons.append("FROZEN_STAGE7_AUTHORITY_INVALID")
    exact = (
        (authority.production_specification_id == PRODUCTION_SPECIFICATION_ID, "PRODUCTION_SPECIFICATION_MISMATCH"),
        (authority.active_identity == ACTIVE_IDENTITY, "ACTIVE_IDENTITY_MISMATCH"),
        (authority.stage8_10_status == STAGE8_10_AUTHORITY, "STAGE8_10_AUTHORITY_INVALID"),
        (_sha256(authority.configured_account_hash) and authority.configured_account_hash == authority.observed_account_hash,
         "ACCOUNT_BINDING_INVALID"),
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
    gate = evaluate_new_entry_gate(runtime_root=runtime_root, now=now,
                                   execution_authorized=execution_authorized)
    reasons.extend(gate["reason_codes"])
    reasons = list(dict.fromkeys(reasons))
    return {"decision": "AUTHORIZED" if not reasons else "BLOCKED",
            "reason_codes": reasons, "quantity": MAX_ACCEPTANCE_QUANTITY,
            "gate": gate}


class ControlledAcceptanceBroker:
    """Narrow FINAM adapter: exactly one entry and, if needed, its one exit."""
    def __init__(self, api: object, account_id: str, store: StateStore):
        if not account_id:
            raise AcceptanceBlocked("ACCOUNT_BINDING_INVALID")
        self.api, self.account_id, self.store = api, account_id, store
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
            self.order_endpoint_call_count += 1
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
        # Flatten authority is intentionally independent of the new-entry gate.
        if not self.entry_attempted:
            raise AcceptanceBlocked("NO_ACCEPTANCE_ENTRY_TO_FLATTEN")
        return self._post_once(OrderRequest(key, finam_symbol, direction, 1, exit_order=True))

    def cancel(self, order_id: str) -> Any:
        if not order_id:
            raise AcceptanceBlocked("ORDER_ID_REQUIRED")
        return self.api.cancel_order(self.account_id, order_id)


def run_controlled_lifecycle(*, authority: AcceptanceAuthority, runtime_root: Path,
                             execution_authorized: bool, instrument: str, finam_symbol: str,
                             direction: str, broker: ControlledAcceptanceBroker,
                             reconcile: Callable[[], dict[str, Any]], now: datetime | None = None) -> dict[str, Any]:
    """Run one bounded synthetic/physical lifecycle and always restore HALTED."""
    observed = now or datetime.now(timezone.utc)
    phases = ["PRECHECK"]
    result: dict[str, Any] = {"classification": "BLOCKED", "phases": phases,
                              "order_endpoint_call_count": 0}
    try:
        checked = precheck(authority=authority, runtime_root=runtime_root, now=observed,
                           execution_authorized=execution_authorized, instrument=instrument)
        result["precheck"] = checked
        if checked["decision"] != "AUTHORIZED":
            raise AcceptanceBlocked("|".join(checked["reason_codes"]))
        phases.append("AUTHORIZED")
        ack = broker.submit_entry(key=f"stage8.11:{instrument}:entry", finam_symbol=finam_symbol,
                                  direction=direction)
        phases.extend(["SUBMIT_1_CONTRACT", "ACK_RECONCILE"])
        state = reconcile()
        if state.get("active_order_count"):
            broker.cancel(str(ack.get("order_id", ""))); state = reconcile()
            phases.append("SAFE_CANCEL")
        if abs(state.get("position_quantity", 0)) == 1:
            broker.submit_flatten(key=f"stage8.11:{instrument}:flatten", finam_symbol=finam_symbol,
                                  direction=direction)
            state = reconcile(); phases.append("SAFE_FLATTEN")
        phases.extend(["FINAL_RECONCILIATION", "HALTED"])
        flat = (state.get("position_quantity") == 0 and state.get("active_order_count") == 0
                and state.get("unresolved_intent_count") == 0 and state.get("reconciled") is True)
        if not flat:
            raise AcceptanceBlocked("FINAL_RECONCILIATION_NOT_FLAT")
        result.update(classification="SYNTHETIC_PASS", final_state=state)
    except FinamUncertainSubmission:
        phases.extend(["RECONCILIATION_REQUIRED", "HALTED"])
        result["failure_code"] = "UNCERTAIN_SUBMISSION_RECONCILIATION_REQUIRED"
    except AcceptanceBlocked as exc:
        phases.append("HALTED")
        result["failure_code"] = str(exc)
    finally:
        emergency_halt(runtime_root, now=observed)
        result["order_endpoint_call_count"] = broker.order_endpoint_call_count
        result["kill_switch_final_state"] = "HALTED"
    return result


def sanitized_evidence(**facts: Any) -> dict[str, Any]:
    """Construct the repository-safe shape; raw/account/credential fields reject."""
    forbidden = {"account_id", "api_token", "secret", "ciphertext", "raw_account", "raw_evidence"}
    if forbidden.intersection(facts):
        raise ValueError("PRIVATE_EVIDENCE_FIELD_FORBIDDEN")
    allowed = {"accepted_code_commit", "sanitized_account_identity_hash", "instrument", "direction",
               "quantity", "preflight_gate_outcomes", "kill_switch_pre_state", "kill_switch_final_state",
               "execution_authorization_observed", "order_endpoint_call_count", "broker_order_present",
               "broker_fill_count", "final_position_quantity", "final_active_order_count",
               "unresolved_intent_count", "reconciliation_result", "physical_result_classification",
               "external_raw_evidence_sha256"}
    if set(facts) - allowed:
        raise ValueError("EVIDENCE_FIELD_NOT_ALLOWLISTED")
    if facts.get("quantity") != 1:
        raise ValueError("EVIDENCE_QUANTITY_MUST_EQUAL_ONE")
    for key in ("sanitized_account_identity_hash", "external_raw_evidence_sha256"):
        if key in facts and not _sha256(facts[key]):
            raise ValueError("EVIDENCE_SHA256_INVALID")
    return {"schema_id": EVIDENCE_SCHEMA, "production_specification_id": PRODUCTION_SPECIFICATION_ID,
            "stage8_11_status": "PHYSICAL_RESULT_REQUIRES_INDEPENDENT_AUDIT", **facts}
