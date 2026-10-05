"""Stage 8.11 attempt3 OIR recovery: reconcile the accepted entry and flatten only.

This recovery exists only for the immutable attempt3 physical result
OPERATOR_INTERVENTION_REQUIRED. It can never submit another entry. After proving
that the existing CNYRUBF LONG 1 position came from the exact persisted attempt3
BUY, it may submit at most one SELL 1 flatten intent. Re-runs never repeat that
POST; they only reconcile the existing flatten intent.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
from typing import Any, Callable

from .account_cleanliness import (
    _rest_contract_quantity, count_active_orders, normalize_order_status,
)
from .backup_state import create_stage8_11_acceptance_backup, sha256_file
from .broker import OrderRequest
from .controlled_real_acceptance import ControlledAcceptanceBroker
from .finam_api import FinamNotFound, FinamOrderRejected, FinamUncertainSubmission
from .operations import stage8_11_exclusive_lock
from .readonly_supervisor import SafetyFault, trading_h1_windows
from .specification import ACTIVE_IDENTITY, PRODUCTION_SPECIFICATION_ID, load_frozen_specification
from .state import StateStore, initialize_stage8_11_acceptance_ledger, stage8_11_acceptance_path
from .trading_safety_gate import emergency_halt, load_kill_switch, write_kill_switch

PHYSICAL_EVIDENCE_NAME = "stage8_11_physical_acceptance_attempt3.json"
PHYSICAL_EVIDENCE_SHA256 = "9206841E4C9E25F126AB6C7032326B4F0778F6CF65D44AF3DA3549D8E677AD65"
PHYSICAL_ACCEPTED_CODE_COMMIT = "5b7d879acb7e8e890f39f34e153161aa5b943a46"
ENTRY_KEY = "stage8.11.attempt3:CNYRUBF:entry"
FLATTEN_KEY = "stage8.11.attempt3:CNYRUBF:flatten"
FINAM_SYMBOL = "CNYRUBF@RTSX"
DIRECTION = "LONG"
RECOVERY_EVIDENCE_NAME = "stage8_11_attempt3_oir_recovery.json"
RECOVERY_SCHEMA = "stage8_11_attempt3_oir_recovery.v1"
PREPARED_SUFFIX = ".prepared"
AUTHORIZATION_VALUE = "STAGE_8_11_ONE_CONTRACT_ACCEPTANCE_AUTHORIZED"
TERMINAL_FILL = frozenset({"FILLED", "EXECUTED"})
TERMINAL_NO_FILL = frozenset({
    "REJECTED", "EXPIRED", "CANCELLED", "FAILED",
    "DENIED_BY_BROKER", "REJECTED_BY_EXCHANGE",
})
ACTIVE = frozenset({
    "NEW", "PARTIAL_FILL", "DONE_FOR_DAY", "PENDING_CANCEL", "SUSPENDED",
    "PENDING_NEW", "FORWARDING", "WAIT", "WATCHING", "LINK_WAIT",
})
MAX_OBSERVATIONS = 60
SLEEP_SECONDS = 0.5


class Attempt3OIRRecoveryBlocked(RuntimeError):
    """Sanitized fail-closed recovery refusal."""


def _account_hash(account_id: str) -> str:
    return hashlib.sha256(account_id.encode("utf-8")).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_EVIDENCE_INVALID") from None
    if not isinstance(value, dict):
        raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_EVIDENCE_INVALID")
    return value


def _write_new(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_RECOVERY_EVIDENCE_ALREADY_EXISTS")
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".incomplete")
    tmp = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.link(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def _validate_physical_evidence(payload: dict[str, Any], *, account_id: str) -> None:
    gates = payload.get("preflight_gate_outcomes")
    expected = {
        "schema_id": "stage8_11_physical_acceptance.v1",
        "production_specification_id": PRODUCTION_SPECIFICATION_ID,
        "stage8_11_status": "PHYSICAL_RESULT_REQUIRES_INDEPENDENT_AUDIT",
        "accepted_code_commit": PHYSICAL_ACCEPTED_CODE_COMMIT,
        "attempt_id": "stage8.11.attempt3",
        "sanitized_account_identity_hash": _account_hash(account_id),
        "instrument": "CNYRUBF",
        "direction": "LONG",
        "quantity": 1,
        "kill_switch_final_state": "HALTED",
        "execution_authorization_observed": True,
        "order_endpoint_call_count": 1,
        "broker_order_present": True,
        "broker_fill_count": 0,
        "entry_fill_proven": False,
        "one_contract_position_observed": False,
        "controlled_flatten_proven": False,
        "final_position_quantity": 1,
        "final_active_order_count": 0,
        "unresolved_intent_count": 1,
        "reconciliation_result": "UNRESOLVED",
        "physical_result_classification": "OPERATOR_INTERVENTION_REQUIRED",
    }
    if any(payload.get(key) != value for key, value in expected.items()):
        raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_PHYSICAL_EVIDENCE_CONTENT_MISMATCH")
    required_gates = {
        "account_binding", "credential_scope", "h1_data_safety", "initial_reconciliation",
        "instrument_binding", "instrument_tradable", "margin_capacity", "r15_capacity",
        "session_write_capable",
    }
    if (not isinstance(gates, dict) or set(gates) != required_gates
            or any(value is not True for value in gates.values())):
        raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_PHYSICAL_PREFLIGHT_NOT_PROVEN")


def _validate_completed(payload: dict[str, Any], *, account_id: str,
                        recovery_code_commit: str) -> None:
    expected = {
        "schema_id": RECOVERY_SCHEMA,
        "recovery_status": "COMMITTED",
        "attempt3_evidence_sha256": PHYSICAL_EVIDENCE_SHA256,
        "attempt3_accepted_code_commit": PHYSICAL_ACCEPTED_CODE_COMMIT,
        "recovery_code_commit": recovery_code_commit,
        "account_identity_sha256": _account_hash(account_id),
        "production_specification_id": PRODUCTION_SPECIFICATION_ID,
        "active_identity": ACTIVE_IDENTITY,
        "entry_intent_key": ENTRY_KEY,
        "physical_result_preserved": "OPERATOR_INTERVENTION_REQUIRED",
        "attempt3_reclassified_as_pass": False,
        "final_position_quantity": 0,
        "final_active_order_count": 0,
        "unresolved_intent_count": 0,
        "kill_switch_final_state": "HALTED",
    }
    if any(payload.get(key) != value for key, value in expected.items()):
        raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_RECOVERY_EVIDENCE_AUTHORITY_MISMATCH")
    if payload.get("recovery_classification") not in {
        "RECOVERED_FLAT_AFTER_ONE_CONTROLLED_FLATTEN",
        "ALREADY_FLAT_NO_FLATTEN_POST",
    }:
        raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_RECOVERY_EVIDENCE_AUTHORITY_MISMATCH")
    if payload.get("flatten_order_endpoint_call_count") not in {0, 1}:
        raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_RECOVERY_EVIDENCE_AUTHORITY_MISMATCH")


def _rows(response: Any, key: str) -> list[dict[str, Any]]:
    rows = response.get(key) if isinstance(response, dict) else None
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_BROKER_COLLECTION_SCHEMA_INVALID")
    return rows


def _position_state(api: object, account_id: str) -> tuple[int, int]:
    account = api.account(account_id)
    positions = _rows(account, "positions")
    selected: int | None = None
    unexpected = 0
    for row in positions:
        symbol = row.get("symbol")
        if not isinstance(symbol, str) or not symbol:
            raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_ACCOUNT_SCHEMA_INVALID")
        try:
            quantity = _rest_contract_quantity(row.get("quantity"))
        except ValueError:
            raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_ACCOUNT_SCHEMA_INVALID") from None
        if symbol == FINAM_SYMBOL:
            if selected is not None:
                raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_DUPLICATE_POSITION_ROWS")
            selected = quantity
        elif quantity != 0:
            unexpected += 1
    return (0 if selected is None else selected), unexpected


def _order_rows(api: object, account_id: str) -> list[dict[str, Any]]:
    return _rows(api.orders(account_id), "orders")


def _active_order_count(rows: list[dict[str, Any]]) -> int:
    try:
        return count_active_orders(rows)
    except ValueError:
        raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_ORDERS_SCHEMA_INVALID") from None


def _intent_payload(intent: dict[str, Any], *, side: str) -> dict[str, Any]:
    payload = intent.get("payload")
    if (not isinstance(payload, dict) or payload.get("symbol") != FINAM_SYMBOL
            or payload.get("side") != side or payload.get("quantity") != {"value": "1"}
            or not isinstance(payload.get("client_order_id"), str)
            or not payload.get("client_order_id")):
        raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_INTENT_PAYLOAD_INVALID")
    return payload


def _matching_order_row(rows: list[dict[str, Any]], *, intent: dict[str, Any],
                        side: str) -> tuple[dict[str, Any], str]:
    payload = _intent_payload(intent, side=side)
    broker_id = intent.get("broker_order_id")
    candidates = []
    for row in rows:
        request = row.get("order")
        if not isinstance(request, dict):
            continue
        same_client = request.get("client_order_id") == payload["client_order_id"]
        same_id = isinstance(broker_id, str) and broker_id and row.get("order_id") == broker_id
        if same_client or same_id:
            candidates.append(row)
    if len(candidates) != 1:
        raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_BROKER_ORDER_NOT_UNIQUE")
    row = candidates[0]
    order_id = row.get("order_id")
    request = row.get("order")
    if not isinstance(order_id, str) or not order_id or not isinstance(request, dict):
        raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_BROKER_ORDER_SHAPE_INVALID")
    try:
        quantity = _rest_contract_quantity(request.get("quantity"))
    except ValueError:
        raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_BROKER_ORDER_SHAPE_INVALID") from None
    if (request.get("client_order_id") != payload["client_order_id"]
            or request.get("symbol") != FINAM_SYMBOL
            or request.get("side") != side or quantity != 1):
        raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_BROKER_ORDER_IDENTITY_MISMATCH")
    if isinstance(broker_id, str) and broker_id and broker_id != order_id:
        raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_BROKER_ORDER_IDENTITY_MISMATCH")
    return row, order_id


def _exact_order_detail(api: object, account_id: str, *, order_id: str,
                        payload: dict[str, Any], side: str) -> str:
    try:
        detail = api.order(account_id, order_id)
    except FinamNotFound:
        raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_ORDER_DETAIL_NOT_AVAILABLE") from None
    request = detail.get("order") if isinstance(detail, dict) else None
    if (not isinstance(detail, dict) or detail.get("order_id") != order_id
            or not isinstance(request, dict) or request.get("account_id") != account_id
            or request.get("client_order_id") != payload.get("client_order_id")
            or request.get("symbol") != FINAM_SYMBOL or request.get("side") != side):
        raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_ORDER_DETAIL_IDENTITY_MISMATCH")
    try:
        request_quantity = _rest_contract_quantity(request.get("quantity"))
        initial = _rest_contract_quantity(detail.get("initial_quantity"))
        executed = _rest_contract_quantity(detail.get("executed_quantity"))
        remaining = _rest_contract_quantity(detail.get("remaining_quantity"))
        status = normalize_order_status(detail.get("status"))
    except ValueError:
        raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_ORDER_DETAIL_SCHEMA_INVALID") from None
    if request_quantity != 1 or initial != 1 or executed not in (0, 1) or remaining not in (0, 1):
        raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_ORDER_QUANTITY_INVALID")
    if executed + remaining != initial:
        raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_ORDER_QUANTITY_INVALID")
    if executed == 1 and remaining == 0 and status in TERMINAL_FILL:
        return status
    if executed == 0 and remaining in (0, 1) and (status in TERMINAL_NO_FILL or status in ACTIVE):
        return status
    raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_ORDER_STATE_UNSUPPORTED")


def _prove_entry(api: object, account_id: str, intent: dict[str, Any]) -> tuple[str, int]:
    rows = _order_rows(api, account_id)
    if _active_order_count(rows) != 0:
        raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_ACTIVE_ORDERS_PRESENT")
    _, order_id = _matching_order_row(rows, intent=intent, side="SIDE_BUY")
    payload = _intent_payload(intent, side="SIDE_BUY")
    status = _exact_order_detail(api, account_id, order_id=order_id, payload=payload, side="SIDE_BUY")
    if status not in TERMINAL_FILL:
        raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_ENTRY_EXECUTION_NOT_PROVEN")
    position, unexpected = _position_state(api, account_id)
    if unexpected != 0:
        raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_UNEXPECTED_POSITION_PRESENT")
    if position not in (0, 1):
        raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_POSITION_NOT_EXACT_ZERO_OR_LONG_ONE")
    return status, position


def _require_open_session(api: object) -> None:
    try:
        windows = trading_h1_windows(api.schedule(FINAM_SYMBOL))
    except (SafetyFault, AttributeError, TypeError, ValueError):
        raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_TRADING_SCHEDULE_INVALID") from None
    now = datetime.now(timezone.utc)
    if not any(start <= now < end for start, end in windows):
        raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_TRADING_SESSION_NOT_OPEN")


def _terminalize_entry(store: StateStore, intent: dict[str, Any], *, flat_without_recovery_post: bool) -> None:
    current = intent.get("status")
    if current in {"CLOSED", "RECONCILED"}:
        return
    if current not in {"ACK", "UNCERTAIN", "FILL"}:
        raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_ENTRY_INTENT_STATE_INVALID")
    store.transition_intent(
        ENTRY_KEY, "CLOSED" if flat_without_recovery_post else "RECONCILED",
        str(intent.get("broker_order_id") or "") or None,
    )


def _flatten_snapshot(api: object, account_id: str, store: StateStore) -> dict[str, Any]:
    intent = store.intent(FLATTEN_KEY)
    if not intent:
        raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_FLATTEN_INTENT_MISSING")
    payload = _intent_payload(intent, side="SIDE_SELL")
    rows = _order_rows(api, account_id)
    active_count = _active_order_count(rows)
    position, unexpected = _position_state(api, account_id)
    if unexpected != 0:
        raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_UNEXPECTED_POSITION_PRESENT")

    broker_id = intent.get("broker_order_id")
    candidates = []
    for row in rows:
        request = row.get("order")
        if not isinstance(request, dict):
            continue
        if (request.get("client_order_id") == payload["client_order_id"]
                or isinstance(broker_id, str) and broker_id and row.get("order_id") == broker_id):
            candidates.append(row)
    if len(candidates) > 1:
        raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_FLATTEN_ORDER_NOT_UNIQUE")
    if not candidates:
        return {"position": position, "unexpected": unexpected, "active": active_count,
                "order_visible": False, "terminal_fill": False, "terminal_no_fill": False,
                "status": None, "order_id": broker_id}

    row, order_id = _matching_order_row(rows, intent=intent, side="SIDE_SELL")
    if not broker_id:
        store.transition_intent(FLATTEN_KEY, "ACK", order_id)
        intent = store.intent(FLATTEN_KEY) or intent
        payload = _intent_payload(intent, side="SIDE_SELL")
    status = _exact_order_detail(
        api, account_id, order_id=order_id, payload=payload, side="SIDE_SELL")
    return {"position": position, "unexpected": unexpected, "active": active_count,
            "order_visible": True, "terminal_fill": status in TERMINAL_FILL,
            "terminal_no_fill": status in TERMINAL_NO_FILL,
            "status": status, "order_id": order_id}


def _reconcile_flatten(api: object, account_id: str, store: StateStore,
                       *, sleeper: Callable[[float], None]) -> tuple[str, dict[str, Any]]:
    last: dict[str, Any] | None = None
    for observation in range(MAX_OBSERVATIONS):
        try:
            snap = _flatten_snapshot(api, account_id, store)
        except Attempt3OIRRecoveryBlocked as exc:
            if str(exc) != "ATTEMPT3_OIR_ORDER_DETAIL_NOT_AVAILABLE":
                raise
            snap = None
        if snap is not None:
            last = snap
            if snap["position"] == -1:
                raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_OVER_FLATTEN_POSITION_OBSERVED")
            if snap["terminal_fill"]:
                if snap["position"] == 0 and snap["active"] == 0:
                    store.transition_intent(FLATTEN_KEY, "RECONCILED", snap["order_id"])
                    return str(snap["status"]), snap
                if snap["position"] not in (0, 1):
                    raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_FLATTEN_POSITION_INVALID")
            if snap["terminal_no_fill"] and snap["position"] == 1 and snap["active"] == 0:
                store.transition_intent(
                    FLATTEN_KEY,
                    "CANCELLED" if snap["status"] == "CANCELLED" else "REJECTED",
                    snap["order_id"],
                )
                raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_FLATTEN_NOT_EXECUTED")
        if observation + 1 < MAX_OBSERVATIONS:
            sleeper(SLEEP_SECONDS)
    if last is not None and last.get("position") == 0 and last.get("active") == 0:
        raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_FLAT_BUT_FLATTEN_EXECUTION_NOT_YET_PROVEN")
    raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_FLATTEN_RECONCILIATION_TIMEOUT")


def recover_attempt3_oir(*, runtime_root: Path, account_id: str, trading_api: object,
                         recovery_code_commit: str, authorization: str,
                         sleeper: Callable[[float], None] = time.sleep,
                         now: datetime | None = None) -> dict[str, Any]:
    root = Path(runtime_root)
    flatten_post_count = 0
    try:
        with stage8_11_exclusive_lock(root):
            if authorization != AUTHORIZATION_VALUE:
                raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_AUTHORIZATION_INVALID")
            if (len(recovery_code_commit) != 40 or recovery_code_commit.lower() != recovery_code_commit
                    or any(c not in "0123456789abcdef" for c in recovery_code_commit)):
                raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_RECOVERY_CODE_COMMIT_INVALID")

            physical = root / "diagnostics" / PHYSICAL_EVIDENCE_NAME
            if (not physical.is_file()
                    or sha256_file(physical).upper() != PHYSICAL_EVIDENCE_SHA256):
                raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_PHYSICAL_EVIDENCE_MISSING_OR_MISMATCH")
            _validate_physical_evidence(_load_json(physical), account_id=account_id)

            frozen = load_frozen_specification()
            if frozen.production_id != PRODUCTION_SPECIFICATION_ID or frozen.identity != ACTIVE_IDENTITY:
                raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_FROZEN_IDENTITY_MISMATCH")

            switch, error = load_kill_switch(root)
            if (error is not None or switch is None
                    or switch.get("production_specification_id") != PRODUCTION_SPECIFICATION_ID
                    or switch.get("state") != "HALTED"):
                raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_KILL_SWITCH_NOT_HALTED")

            trading_api.create_session()
            details = trading_api.session_details()
            accounts = [str(x) for x in details.get("account_ids", [])] if isinstance(details, dict) else []
            if (not isinstance(details, dict) or details.get("readonly") is not False
                    or accounts.count(account_id) != 1):
                raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_TRADING_SESSION_AUTHORITY_INVALID")
            print("STAGE8_11_ATTEMPT3_OIR_TRADING_TOKEN_PASS")

            ledger = initialize_stage8_11_acceptance_ledger(root, account_id)
            if ledger.resolve() != stage8_11_acceptance_path(root).resolve():
                raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_CANONICAL_LEDGER_MISMATCH")
            store = StateStore(ledger)
            target = root / "diagnostics" / RECOVERY_EVIDENCE_NAME
            prepared_path = target.with_name(target.name + PREPARED_SUFFIX)
            try:
                if target.exists():
                    completed = _load_json(target)
                    _validate_completed(
                        completed, account_id=account_id,
                        recovery_code_commit=recovery_code_commit)
                    return completed

                entry = store.intent(ENTRY_KEY)
                if (not entry or entry.get("status") not in {
                        "ACK", "UNCERTAIN", "FILL", "RECONCILED", "CLOSED"}):
                    raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_ENTRY_INTENT_STATE_INVALID")
                if not isinstance(entry.get("broker_order_id"), str) or not entry.get("broker_order_id"):
                    raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_ENTRY_BROKER_ORDER_ID_MISSING")

                entry_status, position = _prove_entry(trading_api, account_id, entry)
                observed = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)

                if prepared_path.exists():
                    prepared = _load_json(prepared_path)
                    expected_prepared = {
                        "schema_id": RECOVERY_SCHEMA,
                        "recovery_status": "PREPARED",
                        "attempt3_evidence_sha256": PHYSICAL_EVIDENCE_SHA256,
                        "attempt3_accepted_code_commit": PHYSICAL_ACCEPTED_CODE_COMMIT,
                        "recovery_code_commit": recovery_code_commit,
                        "account_identity_sha256": _account_hash(account_id),
                        "production_specification_id": PRODUCTION_SPECIFICATION_ID,
                        "active_identity": ACTIVE_IDENTITY,
                        "entry_intent_key": ENTRY_KEY,
                        "entry_broker_order_terminal_status": entry_status,
                    }
                    if any(prepared.get(k) != v for k, v in expected_prepared.items()):
                        raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_PREPARED_EVIDENCE_AUTHORITY_MISMATCH")
                    backup = root / "backups" / "stage8-11-acceptance" / str(
                        prepared.get("backup_filename", ""))
                    manifest = backup.with_name(str(prepared.get("backup_manifest_filename", "")))
                    if not backup.is_file() or not manifest.is_file():
                        raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_RECOVERY_BACKUP_MISSING")
                else:
                    backup, manifest = create_stage8_11_acceptance_backup(
                        root, account_id, created_at=observed)
                    prepared = {
                        "schema_id": RECOVERY_SCHEMA,
                        "recovery_status": "PREPARED",
                        "attempt3_evidence_sha256": PHYSICAL_EVIDENCE_SHA256,
                        "attempt3_accepted_code_commit": PHYSICAL_ACCEPTED_CODE_COMMIT,
                        "recovery_code_commit": recovery_code_commit,
                        "account_identity_sha256": _account_hash(account_id),
                        "production_specification_id": PRODUCTION_SPECIFICATION_ID,
                        "active_identity": ACTIVE_IDENTITY,
                        "entry_intent_key": ENTRY_KEY,
                        "entry_broker_order_terminal_status": entry_status,
                        "backup_filename": backup.name,
                        "backup_manifest_filename": manifest.name,
                        "prepared_at_utc": observed.isoformat().replace("+00:00", "Z"),
                    }
                    _write_new(prepared_path, prepared)

                if position == 0:
                    if store.intent(FLATTEN_KEY) is not None:
                        flatten = store.intent(FLATTEN_KEY)
                        if flatten and flatten.get("status") not in {
                                "RECONCILED", "CANCELLED", "REJECTED", "CLOSED"}:
                            flatten_status, snap = _reconcile_flatten(
                                trading_api, account_id, store, sleeper=sleeper)
                            if snap["position"] != 0:
                                raise Attempt3OIRRecoveryBlocked(
                                    "ATTEMPT3_OIR_ALREADY_FLAT_RECONCILIATION_INVALID")
                        elif flatten and flatten.get("status") == "RECONCILED":
                            flatten_status = "EXECUTED"
                        else:
                            flatten_status = None
                        classification = "RECOVERED_FLAT_AFTER_ONE_CONTROLLED_FLATTEN"
                    else:
                        _terminalize_entry(store, entry, flat_without_recovery_post=True)
                        flatten_status = None
                        classification = "ALREADY_FLAT_NO_FLATTEN_POST"
                else:
                    _terminalize_entry(store, entry, flat_without_recovery_post=False)
                    existing_flatten = store.intent(FLATTEN_KEY)
                    if existing_flatten is None:
                        _require_open_session(trading_api)
                        payload = ControlledAcceptanceBroker._payload(
                            OrderRequest(
                                FLATTEN_KEY, FINAM_SYMBOL, DIRECTION, 1, exit_order=True))
                        if payload.get("side") != "SIDE_SELL":
                            raise Attempt3OIRRecoveryBlocked(
                                "ATTEMPT3_OIR_FLATTEN_SIDE_NOT_SELL")
                        if not store.persist_intent(FLATTEN_KEY, payload):
                            raise Attempt3OIRRecoveryBlocked(
                                "ATTEMPT3_OIR_FLATTEN_INTENT_PERSIST_FAILED")
                        write_kill_switch(root, "ARMED", allow_arm=True, now=observed)
                        try:
                            flatten_post_count = 1
                            response = trading_api.place_order(account_id, payload)
                        except FinamUncertainSubmission:
                            store.transition_intent(FLATTEN_KEY, "UNCERTAIN")
                        except FinamOrderRejected:
                            store.transition_intent(FLATTEN_KEY, "REJECTED")
                            raise Attempt3OIRRecoveryBlocked(
                                "ATTEMPT3_OIR_FLATTEN_DEFINITIVELY_REJECTED") from None
                        else:
                            order_id = str(response.get("order_id", "")) if isinstance(response, dict) else ""
                            if not order_id:
                                store.transition_intent(FLATTEN_KEY, "UNCERTAIN")
                            else:
                                store.transition_intent(FLATTEN_KEY, "ACK", order_id)
                        finally:
                            emergency_halt(root)
                    flatten_status, snap = _reconcile_flatten(
                        trading_api, account_id, store, sleeper=sleeper)
                    if snap["position"] != 0 or snap["active"] != 0:
                        raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_FINAL_ACCOUNT_NOT_FLAT")
                    classification = "RECOVERED_FLAT_AFTER_ONE_CONTROLLED_FLATTEN"

                final_position, unexpected = _position_state(trading_api, account_id)
                final_orders = _order_rows(trading_api, account_id)
                final_active = _active_order_count(final_orders)
                unresolved = store.unresolved_intent_count()
                if final_position != 0 or unexpected != 0 or final_active != 0 or unresolved != 0:
                    raise Attempt3OIRRecoveryBlocked("ATTEMPT3_OIR_FINAL_RECONCILIATION_NOT_CLEAN")

                completed = {
                    **prepared,
                    "recovery_status": "COMMITTED",
                    "recovery_classification": classification,
                    "flatten_intent_key": FLATTEN_KEY if store.intent(FLATTEN_KEY) else None,
                    "flatten_broker_order_terminal_status": flatten_status,
                    "flatten_order_endpoint_call_count": flatten_post_count,
                    "entry_final_local_status": (store.intent(ENTRY_KEY) or {}).get("status"),
                    "flatten_final_local_status": (
                        (store.intent(FLATTEN_KEY) or {}).get("status")
                        if store.intent(FLATTEN_KEY) else None),
                    "final_position_quantity": 0,
                    "final_active_order_count": 0,
                    "unresolved_intent_count": 0,
                    "physical_result_preserved": "OPERATOR_INTERVENTION_REQUIRED",
                    "attempt3_reclassified_as_pass": False,
                    "kill_switch_final_state": "HALTED",
                    "recovered_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                }
                emergency_halt(root)
                _write_new(target, completed)
                prepared_path.unlink(missing_ok=True)
                return completed
            finally:
                store.close()
    finally:
        try:
            emergency_halt(root)
        except Exception:
            pass


def main(argv: list[str] | None = None,
         *, api_factory: Callable[[str], object] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Stage 8.11 attempt3 OIR flatten recovery")
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--accepted-recovery-commit", required=True)
    args = parser.parse_args(argv)

    authorization = os.environ.pop("STAGE8_11_PHYSICAL_AUTHORIZATION", "")
    secret = os.environ.pop("STAGE8_11_TRADING_SECRET", "")
    account_id = os.environ.pop("STAGE8_11_ACCOUNT_ID", "")
    if not secret or not account_id:
        print("ATTEMPT3_OIR_TRADING_CREDENTIAL_REQUIRED")
        return 2

    from .finam_api import FinamAPI
    api = (api_factory or FinamAPI)(secret)
    try:
        evidence = recover_attempt3_oir(
            runtime_root=args.runtime_root,
            account_id=account_id,
            trading_api=api,
            recovery_code_commit=args.accepted_recovery_commit,
            authorization=authorization,
        )
    except (Attempt3OIRRecoveryBlocked, OSError, ValueError):
        print("STAGE8_11_ATTEMPT3_OIR_RECOVERY_BLOCKED")
        return 1
    print("STAGE8_11_ATTEMPT3_OIR_RECOVERY_COMPLETE")
    print("recovery_classification=" + str(evidence.get("recovery_classification")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
