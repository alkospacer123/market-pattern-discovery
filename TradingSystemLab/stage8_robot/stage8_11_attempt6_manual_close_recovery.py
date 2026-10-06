"""Order-incapable recovery after manual close of Stage 8.11 attempt6 OIR.

Attempt6 is immutable and remains OPERATOR_INTERVENTION_REQUIRED forever.
This recovery uses only the readonly session, current account positions and the
active-order collection. It never reads /trades or exact /orders/{id}, and it
never submits, cancels or modifies an order.
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

from .account_cleanliness import count_active_orders, count_nonzero_positions
from .backup_state import create_stage8_11_acceptance_backup, sha256_file
from .operations import stage8_11_exclusive_lock
from .specification import ACTIVE_IDENTITY, PRODUCTION_SPECIFICATION_ID, load_frozen_specification
from .state import StateStore, initialize_stage8_11_acceptance_ledger, stage8_11_acceptance_path
from .trading_safety_gate import load_kill_switch

ATTEMPT6_EVIDENCE_NAME = "stage8_11_physical_acceptance_attempt6.json"
ATTEMPT6_EVIDENCE_SHA256 = "8921A4A9FC1A44DD0407D405B32B54B03A87F6949AFBCC6DA446F1FDC58BDE3B"
ATTEMPT6_ACCEPTED_CODE_COMMIT = "4de08900ab9e4c437264003e945c084fe1789847"
ATTEMPT6_INTENT_KEY = "stage8.11.attempt6:CNYRUBF:entry"
FINAM_SYMBOL = "CNYRUBF@RTSX"
RECOVERY_EVIDENCE_NAME = "stage8_11_attempt6_manual_close_recovery.json"
RECOVERY_SCHEMA = "stage8_11_attempt6_manual_close_recovery.v1"
RECOVERY_BASIS = "IMMUTABLE_ATTEMPT6_OIR_PLUS_CURRENT_FLAT_ZERO_ACTIVE_ORDERS"
PREPARED_SUFFIX = ".prepared"


class Attempt6ManualCloseRecoveryBlocked(RuntimeError):
    """Sanitized fail-closed refusal."""


def _account_hash(account_id: str) -> str:
    return hashlib.sha256(account_id.encode("utf-8")).hexdigest()


def _write_new(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise Attempt6ManualCloseRecoveryBlocked("ATTEMPT6_RECOVERY_EVIDENCE_ALREADY_EXISTS")
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
        raise Attempt6ManualCloseRecoveryBlocked("ATTEMPT6_RECOVERY_EVIDENCE_INVALID") from None
    if not isinstance(value, dict):
        raise Attempt6ManualCloseRecoveryBlocked("ATTEMPT6_RECOVERY_EVIDENCE_INVALID")
    return value


def _validate_attempt6_physical_evidence(payload: dict[str, Any], *, account_id: str) -> None:
    expected = {
        "schema_id": "stage8_11_physical_acceptance.v1",
        "production_specification_id": PRODUCTION_SPECIFICATION_ID,
        "stage8_11_status": "PHYSICAL_RESULT_REQUIRES_INDEPENDENT_AUDIT",
        "accepted_code_commit": ATTEMPT6_ACCEPTED_CODE_COMMIT,
        "attempt_id": "stage8.11.attempt6",
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
        raise Attempt6ManualCloseRecoveryBlocked("ATTEMPT6_PHYSICAL_EVIDENCE_CONTENT_MISMATCH")
    gates = payload.get("preflight_gate_outcomes")
    if not isinstance(gates, dict) or not gates or any(v is not True for v in gates.values()):
        raise Attempt6ManualCloseRecoveryBlocked("ATTEMPT6_PHYSICAL_PREFLIGHT_NOT_PROVEN")


def _validate_completed(payload: dict[str, Any], *, account_id: str,
                        recovery_code_commit: str) -> None:
    expected = {
        "schema_id": RECOVERY_SCHEMA,
        "recovery_status": "COMMITTED",
        "attempt6_evidence_sha256": ATTEMPT6_EVIDENCE_SHA256,
        "intent_key": ATTEMPT6_INTENT_KEY,
        "account_identity_sha256": _account_hash(account_id),
        "production_specification_id": PRODUCTION_SPECIFICATION_ID,
        "active_identity": ACTIVE_IDENTITY,
        "recovery_code_commit": recovery_code_commit,
        "recovery_basis": RECOVERY_BASIS,
        "all_positions_zero": True,
        "active_broker_order_count": 0,
        "final_local_intent_status": "CLOSED",
        "attempt6_reclassified_as_pass": False,
        "manual_close_history_preserved": True,
        "physical_result_preserved": "OPERATOR_INTERVENTION_REQUIRED",
    }
    if any(payload.get(k) != v for k, v in expected.items()):
        raise Attempt6ManualCloseRecoveryBlocked("ATTEMPT6_RECOVERY_EVIDENCE_AUTHORITY_MISMATCH")


def recover_attempt6_manual_close(*, runtime_root: Path, account_id: str, readonly_api: object,
                                  recovery_code_commit: str,
                                  now: datetime | None = None) -> dict[str, Any]:
    root = Path(runtime_root)
    with stage8_11_exclusive_lock(root):
        if (len(recovery_code_commit) != 40 or recovery_code_commit.lower() != recovery_code_commit
                or any(c not in "0123456789abcdef" for c in recovery_code_commit)):
            raise Attempt6ManualCloseRecoveryBlocked("ATTEMPT6_RECOVERY_CODE_COMMIT_INVALID")

        previous = root / "diagnostics" / ATTEMPT6_EVIDENCE_NAME
        if (not previous.is_file()
                or sha256_file(previous).upper() != ATTEMPT6_EVIDENCE_SHA256):
            raise Attempt6ManualCloseRecoveryBlocked("ATTEMPT6_EVIDENCE_MISSING_OR_MISMATCH")
        _validate_attempt6_physical_evidence(_load_json(previous), account_id=account_id)

        frozen = load_frozen_specification()
        if frozen.production_id != PRODUCTION_SPECIFICATION_ID or frozen.identity != ACTIVE_IDENTITY:
            raise Attempt6ManualCloseRecoveryBlocked("ATTEMPT6_RECOVERY_FROZEN_IDENTITY_MISMATCH")

        switch, error = load_kill_switch(root)
        if (error is not None or switch is None
                or switch.get("production_specification_id") != PRODUCTION_SPECIFICATION_ID
                or switch.get("state") != "HALTED"):
            raise Attempt6ManualCloseRecoveryBlocked("ATTEMPT6_RECOVERY_KILL_SWITCH_NOT_HALTED")

        details = readonly_api.session_details()
        accounts = [str(x) for x in details.get("account_ids", [])] if isinstance(details, dict) else []
        if not isinstance(details, dict) or details.get("readonly") is not True or accounts.count(account_id) != 1:
            raise Attempt6ManualCloseRecoveryBlocked("ATTEMPT6_RECOVERY_READONLY_ACCOUNT_MISMATCH")

        ledger = initialize_stage8_11_acceptance_ledger(root, account_id)
        if ledger.resolve() != stage8_11_acceptance_path(root).resolve():
            raise Attempt6ManualCloseRecoveryBlocked("ATTEMPT6_RECOVERY_CANONICAL_LEDGER_MISMATCH")
        store = StateStore(ledger)
        target = root / "diagnostics" / RECOVERY_EVIDENCE_NAME
        prepared_path = target.with_name(target.name + PREPARED_SUFFIX)
        try:
            if target.exists():
                completed = _load_json(target)
                _validate_completed(completed, account_id=account_id,
                                    recovery_code_commit=recovery_code_commit)
                intent = store.intent(ATTEMPT6_INTENT_KEY)
                if not intent or intent.get("status") != "CLOSED":
                    raise Attempt6ManualCloseRecoveryBlocked("ATTEMPT6_RECOVERY_LOCAL_STATE_MISMATCH")
                return completed

            if store.intent("stage8.11.attempt6:CNYRUBF:flatten") is not None:
                raise Attempt6ManualCloseRecoveryBlocked("ATTEMPT6_RECOVERY_FLATTEN_INTENT_PRESENT")

            intent = store.intent(ATTEMPT6_INTENT_KEY)
            if (not intent or intent.get("status") not in {"ACK", "UNCERTAIN", "FILL", "CLOSED"}
                    or not isinstance(intent.get("broker_order_id"), str)
                    or not intent.get("broker_order_id")):
                raise Attempt6ManualCloseRecoveryBlocked("ATTEMPT6_RECOVERY_INTENT_STATE_INVALID")
            payload = intent.get("payload")
            if (not isinstance(payload, dict) or payload.get("symbol") != FINAM_SYMBOL
                    or payload.get("side") != "SIDE_BUY" or payload.get("quantity") != {"value": "1"}
                    or not isinstance(payload.get("client_order_id"), str)
                    or not payload.get("client_order_id")):
                raise Attempt6ManualCloseRecoveryBlocked("ATTEMPT6_RECOVERY_INTENT_PAYLOAD_INVALID")

            account = readonly_api.account(account_id)
            positions = account.get("positions") if isinstance(account, dict) else None
            try:
                if count_nonzero_positions(positions) != 0:
                    raise Attempt6ManualCloseRecoveryBlocked("ATTEMPT6_RECOVERY_ACCOUNT_NOT_FLAT")
            except ValueError:
                raise Attempt6ManualCloseRecoveryBlocked("ATTEMPT6_RECOVERY_ACCOUNT_SCHEMA_INVALID") from None

            response = readonly_api.orders(account_id)
            orders = response.get("orders") if isinstance(response, dict) else None
            try:
                active_count = count_active_orders(orders)
            except ValueError:
                raise Attempt6ManualCloseRecoveryBlocked("ATTEMPT6_RECOVERY_ORDERS_SCHEMA_INVALID") from None
            if active_count != 0:
                raise Attempt6ManualCloseRecoveryBlocked("ATTEMPT6_RECOVERY_ACTIVE_ORDERS_PRESENT")

            observed = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
            if prepared_path.exists():
                prepared = _load_json(prepared_path)
                if (prepared.get("schema_id") != RECOVERY_SCHEMA
                        or prepared.get("recovery_status") != "PREPARED"
                        or prepared.get("attempt6_evidence_sha256") != ATTEMPT6_EVIDENCE_SHA256
                        or prepared.get("intent_key") != ATTEMPT6_INTENT_KEY
                        or prepared.get("account_identity_sha256") != _account_hash(account_id)
                        or prepared.get("recovery_code_commit") != recovery_code_commit
                        or prepared.get("recovery_basis") != RECOVERY_BASIS):
                    raise Attempt6ManualCloseRecoveryBlocked("ATTEMPT6_RECOVERY_PREPARED_AUTHORITY_MISMATCH")
                backup = root / "backups" / "stage8-11-acceptance" / str(prepared.get("backup_filename", ""))
                manifest = backup.with_name(str(prepared.get("backup_manifest_filename", "")))
                if not backup.is_file() or not manifest.is_file():
                    raise Attempt6ManualCloseRecoveryBlocked("ATTEMPT6_RECOVERY_BACKUP_MISSING")
            else:
                backup, manifest = create_stage8_11_acceptance_backup(root, account_id, created_at=observed)
                prepared = {
                    "schema_id": RECOVERY_SCHEMA,
                    "recovery_status": "PREPARED",
                    "attempt6_evidence_sha256": ATTEMPT6_EVIDENCE_SHA256,
                    "intent_key": ATTEMPT6_INTENT_KEY,
                    "account_identity_sha256": _account_hash(account_id),
                    "production_specification_id": PRODUCTION_SPECIFICATION_ID,
                    "active_identity": ACTIVE_IDENTITY,
                    "recovery_code_commit": recovery_code_commit,
                    "recovery_basis": RECOVERY_BASIS,
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
                        (ATTEMPT6_INTENT_KEY, intent["broker_order_id"]))
                    if cur.rowcount != 1:
                        raise Attempt6ManualCloseRecoveryBlocked("ATTEMPT6_RECOVERY_SQLITE_COMPARE_AND_SET_FAILED")
                    if store.unresolved_intent_count() != 0:
                        raise Attempt6ManualCloseRecoveryBlocked("ATTEMPT6_RECOVERY_UNRESOLVED_INTENTS_REMAIN")
                    store.db.commit()
                except Exception:
                    store.db.rollback()
                    raise
            elif store.unresolved_intent_count() != 0:
                raise Attempt6ManualCloseRecoveryBlocked("ATTEMPT6_RECOVERY_UNRESOLVED_INTENTS_REMAIN")

            completed = {
                **prepared,
                "recovery_status": "COMMITTED",
                "all_positions_zero": True,
                "active_broker_order_count": 0,
                "final_local_intent_status": "CLOSED",
                "attempt6_reclassified_as_pass": False,
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
    parser = argparse.ArgumentParser(description="Order-incapable attempt6 manual-close recovery")
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--accepted-recovery-commit", required=True)
    args = parser.parse_args(argv)

    secret = os.environ.pop("STAGE8_11_RECOVERY_READONLY_SECRET", "")
    account_id = os.environ.pop("STAGE8_11_RECOVERY_ACCOUNT_ID", "")
    if not secret or not account_id:
        print("ATTEMPT6_RECOVERY_READONLY_CREDENTIAL_REQUIRED")
        return 2

    from .finam_api import FinamAPI
    transport = (api_factory or FinamAPI)(secret)

    class ReadonlyRecoveryClient:
        session_details = transport.session_details
        account = transport.account
        orders = transport.orders

    try:
        recover_attempt6_manual_close(
            runtime_root=args.runtime_root,
            account_id=account_id,
            readonly_api=ReadonlyRecoveryClient(),
            recovery_code_commit=args.accepted_recovery_commit,
        )
    except Attempt6ManualCloseRecoveryBlocked as exc:
        print(str(exc))
        return 1
    except (OSError, ValueError):
        print("STAGE8_11_ATTEMPT6_MANUAL_CLOSE_RECOVERY_BLOCKED")
        return 1
    print("STAGE8_11_ATTEMPT6_MANUAL_CLOSE_RECOVERY_COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
