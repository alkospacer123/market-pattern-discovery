"""Order-incapable recovery of the manually closed Stage 8.11 attempt2 tail.

Attempt2 reached a real one-contract position and was then manually closed by
the operator after the immutable attempt2 evidence was captured.  This recovery
never reclassifies attempt2 as PASS.  It proves the account is currently flat,
the persisted broker order is terminal, and then closes only the stale local
attempt2 intent as CLOSED so attempt3 can start from a clean ledger.
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
    TERMINAL_ORDER_STATUSES, _rest_contract_quantity, count_active_orders,
    count_nonzero_positions, normalize_order_status,
)
from .backup_state import create_stage8_11_acceptance_backup, sha256_file
from .operations import stage8_11_exclusive_lock
from .specification import ACTIVE_IDENTITY, PRODUCTION_SPECIFICATION_ID, load_frozen_specification
from .state import StateStore, initialize_stage8_11_acceptance_ledger, stage8_11_acceptance_path
from .trading_safety_gate import load_kill_switch

ATTEMPT2_EVIDENCE_NAME = "stage8_11_physical_acceptance_attempt2.json"
ATTEMPT2_EVIDENCE_SHA256 = "0954B5C3D62444BA9AE59519386B0FC454D85C987BE1BAC04B82CA6C671B15A0"
ATTEMPT2_INTENT_KEY = "stage8.11.attempt2:CNYRUBF:entry"
FINAM_SYMBOL = "CNYRUBF@RTSX"
RECOVERY_EVIDENCE_NAME = "stage8_11_attempt2_manual_recovery.json"
RECOVERY_SCHEMA = "stage8_11_attempt2_manual_recovery.v1"
PREPARED_SUFFIX = ".prepared"


class Attempt2RecoveryBlocked(RuntimeError):
    """Sanitized fail-closed refusal."""


def _account_hash(account_id: str) -> str:
    return hashlib.sha256(account_id.encode("utf-8")).hexdigest()


def _write_new(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise Attempt2RecoveryBlocked("ATTEMPT2_RECOVERY_EVIDENCE_ALREADY_EXISTS")
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
        raise Attempt2RecoveryBlocked("ATTEMPT2_RECOVERY_EVIDENCE_INVALID") from None
    if not isinstance(value, dict):
        raise Attempt2RecoveryBlocked("ATTEMPT2_RECOVERY_EVIDENCE_INVALID")
    return value


def _validate_completed_evidence(payload: dict[str, Any], *, account_id: str) -> None:
    expected = {
        "schema_id": RECOVERY_SCHEMA,
        "recovery_status": "COMMITTED",
        "attempt2_evidence_sha256": ATTEMPT2_EVIDENCE_SHA256,
        "intent_key": ATTEMPT2_INTENT_KEY,
        "account_identity_sha256": _account_hash(account_id),
        "production_specification_id": PRODUCTION_SPECIFICATION_ID,
        "active_identity": ACTIVE_IDENTITY,
        "final_local_intent_status": "CLOSED",
        "all_positions_zero": True,
        "active_broker_order_count": 0,
    }
    if any(payload.get(k) != v for k, v in expected.items()):
        raise Attempt2RecoveryBlocked("ATTEMPT2_RECOVERY_EVIDENCE_AUTHORITY_MISMATCH")


def recover_attempt2_manual_close(*, runtime_root: Path, account_id: str, readonly_api: object,
                                  recovery_code_commit: str,
                                  now: datetime | None = None) -> dict[str, Any]:
    root = Path(runtime_root)
    with stage8_11_exclusive_lock(root):
        if (len(recovery_code_commit) != 40 or recovery_code_commit.lower() != recovery_code_commit
                or any(c not in "0123456789abcdef" for c in recovery_code_commit)):
            raise Attempt2RecoveryBlocked("ATTEMPT2_RECOVERY_CODE_COMMIT_INVALID")

        previous = root / "diagnostics" / ATTEMPT2_EVIDENCE_NAME
        if (not previous.is_file()
                or sha256_file(previous).upper() != ATTEMPT2_EVIDENCE_SHA256):
            raise Attempt2RecoveryBlocked("ATTEMPT2_EVIDENCE_MISSING_OR_MISMATCH")

        frozen = load_frozen_specification()
        if frozen.production_id != PRODUCTION_SPECIFICATION_ID or frozen.identity != ACTIVE_IDENTITY:
            raise Attempt2RecoveryBlocked("ATTEMPT2_RECOVERY_FROZEN_IDENTITY_MISMATCH")

        switch, error = load_kill_switch(root)
        if (error is not None or switch is None
                or switch.get("production_specification_id") != PRODUCTION_SPECIFICATION_ID
                or switch.get("state") != "HALTED"):
            raise Attempt2RecoveryBlocked("ATTEMPT2_RECOVERY_KILL_SWITCH_NOT_HALTED")

        details = readonly_api.session_details()
        accounts = [str(x) for x in details.get("account_ids", [])] if isinstance(details, dict) else []
        if not isinstance(details, dict) or details.get("readonly") is not True or accounts.count(account_id) != 1:
            raise Attempt2RecoveryBlocked("ATTEMPT2_RECOVERY_READONLY_ACCOUNT_MISMATCH")

        ledger = initialize_stage8_11_acceptance_ledger(root, account_id)
        if ledger.resolve() != stage8_11_acceptance_path(root).resolve():
            raise Attempt2RecoveryBlocked("ATTEMPT2_RECOVERY_CANONICAL_LEDGER_MISMATCH")
        store = StateStore(ledger)
        target = root / "diagnostics" / RECOVERY_EVIDENCE_NAME
        prepared_path = target.with_name(target.name + PREPARED_SUFFIX)
        try:
            if target.exists():
                completed = _load_json(target)
                _validate_completed_evidence(completed, account_id=account_id)
                intent = store.intent(ATTEMPT2_INTENT_KEY)
                if not intent or intent.get("status") != "CLOSED":
                    raise Attempt2RecoveryBlocked("ATTEMPT2_RECOVERY_LOCAL_STATE_MISMATCH")
                return completed

            intent = store.intent(ATTEMPT2_INTENT_KEY)
            if (not intent or intent.get("status") not in {"ACK", "UNCERTAIN", "FILL", "CLOSED"}
                    or not isinstance(intent.get("broker_order_id"), str)
                    or not intent.get("broker_order_id")):
                raise Attempt2RecoveryBlocked("ATTEMPT2_RECOVERY_INTENT_STATE_INVALID")
            payload = intent.get("payload")
            if (not isinstance(payload, dict) or payload.get("symbol") != FINAM_SYMBOL
                    or payload.get("side") != "SIDE_BUY" or payload.get("quantity") != {"value": "1"}
                    or not isinstance(payload.get("client_order_id"), str)
                    or not payload.get("client_order_id")):
                raise Attempt2RecoveryBlocked("ATTEMPT2_RECOVERY_INTENT_PAYLOAD_INVALID")

            account = readonly_api.account(account_id)
            positions = account.get("positions") if isinstance(account, dict) else None
            try:
                if count_nonzero_positions(positions) != 0:
                    raise Attempt2RecoveryBlocked("ATTEMPT2_RECOVERY_ACCOUNT_NOT_FLAT")
            except ValueError:
                raise Attempt2RecoveryBlocked("ATTEMPT2_RECOVERY_ACCOUNT_SCHEMA_INVALID") from None

            response = readonly_api.orders(account_id)
            orders = response.get("orders") if isinstance(response, dict) else None
            try:
                active_count = count_active_orders(orders)
            except ValueError:
                raise Attempt2RecoveryBlocked("ATTEMPT2_RECOVERY_ORDERS_SCHEMA_INVALID") from None
            if active_count != 0:
                raise Attempt2RecoveryBlocked("ATTEMPT2_RECOVERY_ACTIVE_ORDERS_PRESENT")

            broker_id = intent["broker_order_id"]
            matches = [row for row in orders if isinstance(row, dict) and row.get("order_id") == broker_id]
            if len(matches) != 1:
                raise Attempt2RecoveryBlocked("ATTEMPT2_RECOVERY_BROKER_ORDER_NOT_UNIQUE")
            broker_row = matches[0]
            request = broker_row.get("order")
            if not isinstance(request, dict):
                raise Attempt2RecoveryBlocked("ATTEMPT2_RECOVERY_BROKER_ORDER_SHAPE_INVALID")
            try:
                broker_quantity = _rest_contract_quantity(request.get("quantity"))
            except ValueError:
                raise Attempt2RecoveryBlocked("ATTEMPT2_RECOVERY_BROKER_ORDER_SHAPE_INVALID") from None
            if (request.get("client_order_id") != payload.get("client_order_id")
                    or request.get("symbol") != FINAM_SYMBOL
                    or request.get("side") != "SIDE_BUY"
                    or broker_quantity != 1):
                raise Attempt2RecoveryBlocked("ATTEMPT2_RECOVERY_BROKER_ORDER_IDENTITY_MISMATCH")
            try:
                broker_status = normalize_order_status(broker_row.get("status"))
            except ValueError:
                raise Attempt2RecoveryBlocked("ATTEMPT2_RECOVERY_BROKER_ORDER_STATUS_INVALID") from None
            if broker_status not in TERMINAL_ORDER_STATUSES:
                raise Attempt2RecoveryBlocked("ATTEMPT2_RECOVERY_BROKER_ORDER_NOT_TERMINAL")

            observed = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
            if prepared_path.exists():
                prepared = _load_json(prepared_path)
                if (prepared.get("schema_id") != RECOVERY_SCHEMA
                        or prepared.get("recovery_status") != "PREPARED"
                        or prepared.get("attempt2_evidence_sha256") != ATTEMPT2_EVIDENCE_SHA256
                        or prepared.get("intent_key") != ATTEMPT2_INTENT_KEY
                        or prepared.get("account_identity_sha256") != _account_hash(account_id)
                        or prepared.get("recovery_code_commit") != recovery_code_commit
                        or prepared.get("broker_order_terminal_status") != broker_status):
                    raise Attempt2RecoveryBlocked("ATTEMPT2_RECOVERY_PREPARED_AUTHORITY_MISMATCH")
                backup = root / "backups" / "stage8-11-acceptance" / str(prepared.get("backup_filename", ""))
                manifest = backup.with_name(str(prepared.get("backup_manifest_filename", "")))
                if not backup.is_file() or not manifest.is_file():
                    raise Attempt2RecoveryBlocked("ATTEMPT2_RECOVERY_BACKUP_MISSING")
            else:
                backup, manifest = create_stage8_11_acceptance_backup(root, account_id, created_at=observed)
                prepared = {
                    "schema_id": RECOVERY_SCHEMA,
                    "recovery_status": "PREPARED",
                    "attempt2_evidence_sha256": ATTEMPT2_EVIDENCE_SHA256,
                    "intent_key": ATTEMPT2_INTENT_KEY,
                    "account_identity_sha256": _account_hash(account_id),
                    "production_specification_id": PRODUCTION_SPECIFICATION_ID,
                    "active_identity": ACTIVE_IDENTITY,
                    "recovery_code_commit": recovery_code_commit,
                    "broker_order_terminal_status": broker_status,
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
                        (ATTEMPT2_INTENT_KEY, broker_id))
                    if cur.rowcount != 1:
                        raise Attempt2RecoveryBlocked("ATTEMPT2_RECOVERY_SQLITE_COMPARE_AND_SET_FAILED")
                    if store.unresolved_intent_count() != 0:
                        raise Attempt2RecoveryBlocked("ATTEMPT2_RECOVERY_UNRESOLVED_INTENTS_REMAIN")
                    store.db.commit()
                except Exception:
                    store.db.rollback()
                    raise
            elif store.unresolved_intent_count() != 0:
                raise Attempt2RecoveryBlocked("ATTEMPT2_RECOVERY_UNRESOLVED_INTENTS_REMAIN")

            completed = {
                **prepared,
                "recovery_status": "COMMITTED",
                "all_positions_zero": True,
                "active_broker_order_count": 0,
                "final_local_intent_status": "CLOSED",
                "attempt2_reclassified_as_pass": False,
                "manual_close_history_preserved": True,
                "recovered_at_utc": observed.isoformat().replace("+00:00", "Z"),
            }
            _write_new(target, completed)
            prepared_path.unlink(missing_ok=True)
            return completed
        finally:
            store.close()


def main(argv: list[str] | None = None,
         *, api_factory: Callable[[str], object] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Order-incapable attempt2 manual-close recovery")
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--accepted-recovery-commit", required=True)
    args = parser.parse_args(argv)

    secret = os.environ.pop("STAGE8_11_RECOVERY_READONLY_SECRET", "")
    account_id = os.environ.pop("STAGE8_11_RECOVERY_ACCOUNT_ID", "")
    if not secret or not account_id:
        print("ATTEMPT2_RECOVERY_READONLY_CREDENTIAL_REQUIRED")
        return 2

    from .finam_api import FinamAPI
    transport = (api_factory or FinamAPI)(secret)

    class ReadonlyRecoveryClient:
        session_details = transport.session_details
        account = transport.account
        orders = transport.orders

    try:
        recover_attempt2_manual_close(
            runtime_root=args.runtime_root, account_id=account_id,
            readonly_api=ReadonlyRecoveryClient(),
            recovery_code_commit=args.accepted_recovery_commit)
    except (Attempt2RecoveryBlocked, OSError, ValueError):
        print("ATTEMPT2_MANUAL_RECOVERY_BLOCKED")
        return 1
    print("ATTEMPT2_MANUAL_RECOVERY_COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
