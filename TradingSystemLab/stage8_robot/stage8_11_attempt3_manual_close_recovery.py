"""Order-incapable recovery after manual close of Stage 8.11 attempt3 OIR.

The immutable attempt3 evidence proves one accepted CNYRUBF entry POST and a
one-contract long position at the final snapshot. This recovery never submits,
cancels, or modifies an order. After the operator manually closes the position
in FINAM, it proves the account is flat, the exact attempt3 broker entry order
is terminal/executed, creates a backup, and closes only the stale local attempt3
entry intent as CLOSED. Attempt3 is never reclassified as PASS.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Callable

from .account_cleanliness import (
    _rest_contract_quantity, count_active_orders, count_nonzero_positions,
    normalize_order_status,
)
from .backup_state import create_stage8_11_acceptance_backup, sha256_file
from .finam_api import FinamNotFound
from .operations import stage8_11_exclusive_lock
from .specification import ACTIVE_IDENTITY, PRODUCTION_SPECIFICATION_ID, load_frozen_specification
from .state import StateStore, initialize_stage8_11_acceptance_ledger, stage8_11_acceptance_path
from .trading_safety_gate import load_kill_switch

ATTEMPT3_EVIDENCE_NAME = "stage8_11_physical_acceptance_attempt3.json"
ATTEMPT3_EVIDENCE_SHA256 = "9206841E4C9E25F126AB6C7032326B4F0778F6CF65D44AF3DA3549D8E677AD65"
ATTEMPT3_ACCEPTED_CODE_COMMIT = "5b7d879acb7e8e890f39f34e153161aa5b943a46"
ATTEMPT3_INTENT_KEY = "stage8.11.attempt3:CNYRUBF:entry"
FINAM_SYMBOL = "CNYRUBF@RTSX"
RECOVERY_EVIDENCE_NAME = "stage8_11_attempt3_manual_close_recovery.json"
RECOVERY_SCHEMA = "stage8_11_attempt3_manual_close_recovery.v1"
PREPARED_SUFFIX = ".prepared"
EXECUTED_STATUSES = frozenset({"FILLED", "EXECUTED"})
HISTORICAL_DETAIL_UNAVAILABLE = "NOT_AVAILABLE_404"
RECOVERY_BASIS_ORDER_DETAIL = "BROKER_ORDER_DETAIL_EXECUTED"
RECOVERY_BASIS_IMMUTABLE_OIR = "IMMUTABLE_ATTEMPT3_OIR_PLUS_CURRENT_FLAT"


class Attempt3ManualCloseRecoveryBlocked(RuntimeError):
    """Sanitized fail-closed refusal."""


def _account_hash(account_id: str) -> str:
    return hashlib.sha256(account_id.encode("utf-8")).hexdigest()


def _write_new(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise Attempt3ManualCloseRecoveryBlocked("ATTEMPT3_RECOVERY_EVIDENCE_ALREADY_EXISTS")
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


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        raise Attempt3ManualCloseRecoveryBlocked("ATTEMPT3_RECOVERY_EVIDENCE_INVALID") from None
    if not isinstance(value, dict):
        raise Attempt3ManualCloseRecoveryBlocked("ATTEMPT3_RECOVERY_EVIDENCE_INVALID")
    return value


def _validate_attempt3_physical_evidence(payload: dict[str, Any], *, account_id: str) -> None:
    expected = {
        "schema_id": "stage8_11_physical_acceptance.v1",
        "production_specification_id": PRODUCTION_SPECIFICATION_ID,
        "stage8_11_status": "PHYSICAL_RESULT_REQUIRES_INDEPENDENT_AUDIT",
        "accepted_code_commit": ATTEMPT3_ACCEPTED_CODE_COMMIT,
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
    if any(payload.get(k) != v for k, v in expected.items()):
        raise Attempt3ManualCloseRecoveryBlocked("ATTEMPT3_PHYSICAL_EVIDENCE_CONTENT_MISMATCH")
    gates = payload.get("preflight_gate_outcomes")
    if not isinstance(gates, dict) or not gates or any(v is not True for v in gates.values()):
        raise Attempt3ManualCloseRecoveryBlocked("ATTEMPT3_PHYSICAL_PREFLIGHT_NOT_PROVEN")


def _validate_completed(payload: dict[str, Any], *, account_id: str,
                        recovery_code_commit: str) -> None:
    expected = {
        "schema_id": RECOVERY_SCHEMA,
        "recovery_status": "COMMITTED",
        "attempt3_evidence_sha256": ATTEMPT3_EVIDENCE_SHA256,
        "intent_key": ATTEMPT3_INTENT_KEY,
        "account_identity_sha256": _account_hash(account_id),
        "production_specification_id": PRODUCTION_SPECIFICATION_ID,
        "active_identity": ACTIVE_IDENTITY,
        "final_local_intent_status": "CLOSED",
        "all_positions_zero": True,
        "active_broker_order_count": 0,
        "attempt3_reclassified_as_pass": False,
        "manual_close_history_preserved": True,
        "physical_result_preserved": "OPERATOR_INTERVENTION_REQUIRED",
        "recovery_code_commit": recovery_code_commit,
    }
    if any(payload.get(k) != v for k, v in expected.items()):
        raise Attempt3ManualCloseRecoveryBlocked("ATTEMPT3_RECOVERY_EVIDENCE_AUTHORITY_MISMATCH")
    status = payload.get("broker_order_terminal_status")
    basis = payload.get("recovery_basis")
    if not (
        status in EXECUTED_STATUSES and basis == RECOVERY_BASIS_ORDER_DETAIL
        or status == HISTORICAL_DETAIL_UNAVAILABLE
        and basis == RECOVERY_BASIS_IMMUTABLE_OIR
    ):
        raise Attempt3ManualCloseRecoveryBlocked("ATTEMPT3_RECOVERY_EVIDENCE_AUTHORITY_MISMATCH")


def recover_attempt3_manual_close(*, runtime_root: Path, account_id: str, readonly_api: object,
                                  recovery_code_commit: str,
                                  now: datetime | None = None) -> dict[str, Any]:
    root = Path(runtime_root)
    with stage8_11_exclusive_lock(root):
        if (len(recovery_code_commit) != 40 or recovery_code_commit.lower() != recovery_code_commit
                or any(c not in "0123456789abcdef" for c in recovery_code_commit)):
            raise Attempt3ManualCloseRecoveryBlocked("ATTEMPT3_RECOVERY_CODE_COMMIT_INVALID")

        previous = root / "diagnostics" / ATTEMPT3_EVIDENCE_NAME
        if (not previous.is_file()
                or sha256_file(previous).upper() != ATTEMPT3_EVIDENCE_SHA256):
            raise Attempt3ManualCloseRecoveryBlocked("ATTEMPT3_EVIDENCE_MISSING_OR_MISMATCH")
        _validate_attempt3_physical_evidence(_load_json(previous), account_id=account_id)

        frozen = load_frozen_specification()
        if frozen.production_id != PRODUCTION_SPECIFICATION_ID or frozen.identity != ACTIVE_IDENTITY:
            raise Attempt3ManualCloseRecoveryBlocked("ATTEMPT3_RECOVERY_FROZEN_IDENTITY_MISMATCH")

        switch, error = load_kill_switch(root)
        if (error is not None or switch is None
                or switch.get("production_specification_id") != PRODUCTION_SPECIFICATION_ID
                or switch.get("state") != "HALTED"):
            raise Attempt3ManualCloseRecoveryBlocked("ATTEMPT3_RECOVERY_KILL_SWITCH_NOT_HALTED")

        details = readonly_api.session_details()
        accounts = [str(x) for x in details.get("account_ids", [])] if isinstance(details, dict) else []
        if not isinstance(details, dict) or details.get("readonly") is not True or accounts.count(account_id) != 1:
            raise Attempt3ManualCloseRecoveryBlocked("ATTEMPT3_RECOVERY_READONLY_ACCOUNT_MISMATCH")

        ledger = initialize_stage8_11_acceptance_ledger(root, account_id)
        if ledger.resolve() != stage8_11_acceptance_path(root).resolve():
            raise Attempt3ManualCloseRecoveryBlocked("ATTEMPT3_RECOVERY_CANONICAL_LEDGER_MISMATCH")
        store = StateStore(ledger)
        target = root / "diagnostics" / RECOVERY_EVIDENCE_NAME
        prepared_path = target.with_name(target.name + PREPARED_SUFFIX)
        try:
            if target.exists():
                completed = _load_json(target)
                _validate_completed(
                    completed, account_id=account_id,
                    recovery_code_commit=recovery_code_commit)
                intent = store.intent(ATTEMPT3_INTENT_KEY)
                if not intent or intent.get("status") != "CLOSED":
                    raise Attempt3ManualCloseRecoveryBlocked("ATTEMPT3_RECOVERY_LOCAL_STATE_MISMATCH")
                return completed

            if store.intent("stage8.11.attempt3:CNYRUBF:flatten") is not None:
                raise Attempt3ManualCloseRecoveryBlocked("ATTEMPT3_RECOVERY_FLATTEN_INTENT_PRESENT")

            intent = store.intent(ATTEMPT3_INTENT_KEY)
            if (not intent or intent.get("status") not in {"ACK", "UNCERTAIN", "FILL", "CLOSED"}
                    or not isinstance(intent.get("broker_order_id"), str)
                    or not intent.get("broker_order_id")):
                raise Attempt3ManualCloseRecoveryBlocked("ATTEMPT3_RECOVERY_INTENT_STATE_INVALID")
            payload = intent.get("payload")
            if (not isinstance(payload, dict) or payload.get("symbol") != FINAM_SYMBOL
                    or payload.get("side") != "SIDE_BUY" or payload.get("quantity") != {"value": "1"}
                    or not isinstance(payload.get("client_order_id"), str)
                    or not payload.get("client_order_id")):
                raise Attempt3ManualCloseRecoveryBlocked("ATTEMPT3_RECOVERY_INTENT_PAYLOAD_INVALID")

            account = readonly_api.account(account_id)
            positions = account.get("positions") if isinstance(account, dict) else None
            try:
                if count_nonzero_positions(positions) != 0:
                    raise Attempt3ManualCloseRecoveryBlocked("ATTEMPT3_RECOVERY_ACCOUNT_NOT_FLAT")
            except ValueError:
                raise Attempt3ManualCloseRecoveryBlocked("ATTEMPT3_RECOVERY_ACCOUNT_SCHEMA_INVALID") from None

            response = readonly_api.orders(account_id)
            orders = response.get("orders") if isinstance(response, dict) else None
            try:
                active_count = count_active_orders(orders)
            except ValueError:
                raise Attempt3ManualCloseRecoveryBlocked("ATTEMPT3_RECOVERY_ORDERS_SCHEMA_INVALID") from None
            if active_count != 0:
                raise Attempt3ManualCloseRecoveryBlocked("ATTEMPT3_RECOVERY_ACTIVE_ORDERS_PRESENT")

            broker_id = intent["broker_order_id"]

            # Historical order detail may expire at FINAM. If it is still
            # available, prove the exact execution. If FINAM returns 404, the
            # immutable attempt3 evidence already proves one accepted POST,
            # broker acknowledgement and a final +1 CNYRUBF position. Together
            # with the current flat account and zero active orders above, that
            # is sufficient to close only the stale local intent as CLOSED.
            try:
                detail = readonly_api.order(account_id, broker_id)
            except FinamNotFound:
                broker_status = HISTORICAL_DETAIL_UNAVAILABLE
                recovery_basis = RECOVERY_BASIS_IMMUTABLE_OIR
            except Exception:
                raise Attempt3ManualCloseRecoveryBlocked(
                    "ATTEMPT3_RECOVERY_BROKER_ORDER_DETAIL_UNAVAILABLE") from None
            else:
                request = detail.get("order") if isinstance(detail, dict) else None
                if (not isinstance(detail, dict) or detail.get("order_id") != broker_id
                        or not isinstance(request, dict)
                        or request.get("account_id") != account_id):
                    raise Attempt3ManualCloseRecoveryBlocked(
                        "ATTEMPT3_RECOVERY_BROKER_ORDER_DETAIL_SHAPE_INVALID")
                try:
                    broker_quantity = _rest_contract_quantity(request.get("quantity"))
                    initial_quantity = _rest_contract_quantity(detail.get("initial_quantity"))
                    executed_quantity = _rest_contract_quantity(detail.get("executed_quantity"))
                    remaining_quantity = _rest_contract_quantity(detail.get("remaining_quantity"))
                    broker_status = normalize_order_status(detail.get("status"))
                except ValueError:
                    raise Attempt3ManualCloseRecoveryBlocked(
                        "ATTEMPT3_RECOVERY_BROKER_ORDER_DETAIL_SHAPE_INVALID") from None
                if (request.get("client_order_id") != payload.get("client_order_id")
                        or request.get("symbol") != FINAM_SYMBOL
                        or request.get("side") != "SIDE_BUY"
                        or broker_quantity != 1):
                    raise Attempt3ManualCloseRecoveryBlocked(
                        "ATTEMPT3_RECOVERY_BROKER_ORDER_IDENTITY_MISMATCH")
                if (initial_quantity != 1 or executed_quantity != 1 or remaining_quantity != 0
                        or broker_status not in EXECUTED_STATUSES):
                    raise Attempt3ManualCloseRecoveryBlocked(
                        "ATTEMPT3_RECOVERY_BROKER_EXECUTION_NOT_PROVEN")
                recovery_basis = RECOVERY_BASIS_ORDER_DETAIL

            observed = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
            if prepared_path.exists():
                prepared = _load_json(prepared_path)
                if (prepared.get("schema_id") != RECOVERY_SCHEMA
                        or prepared.get("recovery_status") != "PREPARED"
                        or prepared.get("attempt3_evidence_sha256") != ATTEMPT3_EVIDENCE_SHA256
                        or prepared.get("intent_key") != ATTEMPT3_INTENT_KEY
                        or prepared.get("account_identity_sha256") != _account_hash(account_id)
                        or prepared.get("recovery_code_commit") != recovery_code_commit
                        or prepared.get("broker_order_terminal_status") != broker_status
                        or prepared.get("recovery_basis") != recovery_basis):
                    raise Attempt3ManualCloseRecoveryBlocked("ATTEMPT3_RECOVERY_PREPARED_AUTHORITY_MISMATCH")
                backup = root / "backups" / "stage8-11-acceptance" / str(prepared.get("backup_filename", ""))
                manifest = backup.with_name(str(prepared.get("backup_manifest_filename", "")))
                if not backup.is_file() or not manifest.is_file():
                    raise Attempt3ManualCloseRecoveryBlocked("ATTEMPT3_RECOVERY_BACKUP_MISSING")
            else:
                backup, manifest = create_stage8_11_acceptance_backup(root, account_id, created_at=observed)
                prepared = {
                    "schema_id": RECOVERY_SCHEMA,
                    "recovery_status": "PREPARED",
                    "attempt3_evidence_sha256": ATTEMPT3_EVIDENCE_SHA256,
                    "intent_key": ATTEMPT3_INTENT_KEY,
                    "account_identity_sha256": _account_hash(account_id),
                    "production_specification_id": PRODUCTION_SPECIFICATION_ID,
                    "active_identity": ACTIVE_IDENTITY,
                    "recovery_code_commit": recovery_code_commit,
                    "broker_order_terminal_status": broker_status,
                    "recovery_basis": recovery_basis,
                    "backup_filename": backup.name,
                    "backup_manifest_filename": manifest.name,
                    "prepared_at_utc": observed.isoformat().replace("+00:00", "Z"),
                }
                _write_new(prepared_path, prepared)

            if intent["status"] != "CLOSED":
                try:
                    store.db.execute("BEGIN IMMEDIATE")
                    cur = store.db.execute(
                        "UPDATE intents SET status='CLOSED',updated_at=CURRENT_TIMESTAMP "
                        "WHERE idempotency_key=? AND status IN ('ACK','UNCERTAIN','FILL') "
                        "AND broker_order_id=?",
                        (ATTEMPT3_INTENT_KEY, broker_id))
                    if cur.rowcount != 1:
                        raise Attempt3ManualCloseRecoveryBlocked("ATTEMPT3_RECOVERY_SQLITE_COMPARE_AND_SET_FAILED")
                    if store.unresolved_intent_count() != 0:
                        raise Attempt3ManualCloseRecoveryBlocked("ATTEMPT3_RECOVERY_UNRESOLVED_INTENTS_REMAIN")
                    store.db.commit()
                except Exception:
                    store.db.rollback()
                    raise
            elif store.unresolved_intent_count() != 0:
                raise Attempt3ManualCloseRecoveryBlocked("ATTEMPT3_RECOVERY_UNRESOLVED_INTENTS_REMAIN")

            completed = {
                **prepared,
                "recovery_status": "COMMITTED",
                "all_positions_zero": True,
                "active_broker_order_count": 0,
                "final_local_intent_status": "CLOSED",
                "attempt3_reclassified_as_pass": False,
                "manual_close_history_preserved": True,
                "physical_result_preserved": "OPERATOR_INTERVENTION_REQUIRED",
                "recovered_at_utc": observed.isoformat().replace("+00:00", "Z"),
            }
            _write_new(target, completed)
            prepared_path.unlink(missing_ok=True)
            return completed
        finally:
            store.close()


def main(argv: list[str] | None = None,
         *, api_factory: Callable[[str], object] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Order-incapable attempt3 manual-close recovery")
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--accepted-recovery-commit", required=True)
    args = parser.parse_args(argv)

    secret = os.environ.pop("STAGE8_11_RECOVERY_READONLY_SECRET", "")
    account_id = os.environ.pop("STAGE8_11_RECOVERY_ACCOUNT_ID", "")
    if not secret or not account_id:
        print("ATTEMPT3_RECOVERY_READONLY_CREDENTIAL_REQUIRED")
        return 2

    from .finam_api import FinamAPI
    transport = (api_factory or FinamAPI)(secret)

    class ReadonlyRecoveryClient:
        session_details = transport.session_details
        account = transport.account
        orders = transport.orders
        order = transport.order

    try:
        recover_attempt3_manual_close(
            runtime_root=args.runtime_root,
            account_id=account_id,
            readonly_api=ReadonlyRecoveryClient(),
            recovery_code_commit=args.accepted_recovery_commit,
        )
    except Attempt3ManualCloseRecoveryBlocked as exc:
        print(str(exc))
        return 1
    except (OSError, ValueError):
        print("STAGE8_11_ATTEMPT3_MANUAL_CLOSE_RECOVERY_BLOCKED")
        return 1
    print("STAGE8_11_ATTEMPT3_MANUAL_CLOSE_RECOVERY_COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
