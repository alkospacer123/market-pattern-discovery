"""Manual, order-incapable closeout of the first failed Stage 8.11 intent.

This utility can only read a REAL_READONLY account and terminalize the one
historical local intent after exact evidence, repository, account, database and
fresh account-wide cleanliness proofs.  It cannot arm execution or operate on
broker orders.
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

from .backup_state import create_stage8_11_acceptance_backup, sha256_file
from .controlled_real_acceptance import ACTIVE, _decimal_contracts, _rows, _status
from .specification import ACTIVE_IDENTITY, PRODUCTION_SPECIFICATION_ID, load_frozen_specification
from .state import StateStore, initialize_stage8_11_acceptance_ledger, stage8_11_acceptance_path
from .trading_safety_gate import load_kill_switch

ACCEPTED_PHYSICAL_COMMIT = "069806355fc6931470d7f68d5ca6db20b06358fa"
FAILED_PHYSICAL_EVIDENCE_SHA256 = "9FEFC5469F2C97F1EB36A5B5C99D323FA37BB948CF53C8A8745A27A06AB3B324"
HISTORICAL_INTENT_KEY = "stage8.11:CNYRUBF:entry"
FINAM_SYMBOL = "CNYRUBF@RTSX"
RECOVERY_EVIDENCE_NAME = "stage8_11_failed_attempt_recovery.json"
RECOVERY_SCHEMA = "stage8_11_failed_attempt_recovery.v1"
RECOVERY_PREPARED_SUFFIX = ".prepared"


class RecoveryBlocked(RuntimeError):
    """Sanitized fail-closed recovery refusal."""


def _account_hash(account_id: str) -> str:
    return hashlib.sha256(account_id.encode("utf-8")).hexdigest()


def _write_new_json(path: Path, payload: dict[str, Any]) -> None:
    """Create recovery evidence atomically; never replace any evidence file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise RecoveryBlocked("RECOVERY_EVIDENCE_ALREADY_EXISTS")
    descriptor, temporary_name = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".incomplete")
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True); stream.write("\n")
            stream.flush(); os.fsync(stream.fileno())
        os.link(temporary, path)  # fails rather than overwriting a concurrent artifact
    finally:
        temporary.unlink(missing_ok=True)


def _load_prepared(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        raise RecoveryBlocked("RECOVERY_PREPARED_EVIDENCE_INVALID") from None
    if not isinstance(value, dict) or value.get("recovery_status") != "PREPARED":
        raise RecoveryBlocked("RECOVERY_PREPARED_EVIDENCE_INVALID")
    return value


def recover_historical_intent(*, runtime_root: Path, account_id: str, readonly_api: object,
                              recovery_code_commit: str, physical_evidence: Path,
                              physical_evidence_sha256: str, intent_key: str,
                              now: datetime | None = None,
                              fault_injector: Callable[[str], None] | None = None) -> dict[str, Any]:
    """Close only the bound historical intent using a restartable commit protocol.

    A durable PREPARED artifact (which explicitly does *not* claim recovery)
    precedes the SQLite commit.  The success artifact is created only after that
    commit.  If interrupted in between, the rejected row plus PREPARED artifact
    is an incomplete protocol state that a later identical invocation can only
    finalize; it can never be reported as successful prematurely.
    """
    inject = fault_injector or (lambda point: None)
    root = Path(runtime_root)
    if (len(recovery_code_commit) != 40 or recovery_code_commit.lower() != recovery_code_commit
            or any(character not in "0123456789abcdef" for character in recovery_code_commit)):
        raise RecoveryBlocked("RECOVERY_CODE_COMMIT_INVALID")
    if intent_key != HISTORICAL_INTENT_KEY:
        raise RecoveryBlocked("RECOVERY_INTENT_KEY_MISMATCH")
    if physical_evidence_sha256.upper() != FAILED_PHYSICAL_EVIDENCE_SHA256:
        raise RecoveryBlocked("RECOVERY_PHYSICAL_EVIDENCE_SHA256_MISMATCH")
    if not physical_evidence.is_file() or sha256_file(physical_evidence).upper() != FAILED_PHYSICAL_EVIDENCE_SHA256:
        raise RecoveryBlocked("RECOVERY_PHYSICAL_EVIDENCE_FILE_MISMATCH")
    frozen = load_frozen_specification()
    if frozen.production_id != PRODUCTION_SPECIFICATION_ID or frozen.identity != ACTIVE_IDENTITY:
        raise RecoveryBlocked("RECOVERY_FROZEN_IDENTITY_MISMATCH")
    switch, switch_error = load_kill_switch(root)
    if (switch_error is not None or switch is None
            or switch.get("production_specification_id") != PRODUCTION_SPECIFICATION_ID
            or switch.get("state") != "HALTED"):
        raise RecoveryBlocked("RECOVERY_KILL_SWITCH_NOT_HALTED")
    details = readonly_api.session_details()
    accounts = [str(value) for value in details.get("account_ids", [])] if isinstance(details, dict) else []
    if not isinstance(details, dict) or details.get("readonly") is not True or accounts.count(account_id) != 1:
        raise RecoveryBlocked("RECOVERY_READONLY_ACCOUNT_IDENTITY_MISMATCH")

    ledger = initialize_stage8_11_acceptance_ledger(root, account_id)
    if ledger.resolve() != stage8_11_acceptance_path(root).resolve():
        raise RecoveryBlocked("RECOVERY_CANONICAL_LEDGER_MISMATCH")
    store = StateStore(ledger)
    evidence_path = root / "diagnostics" / RECOVERY_EVIDENCE_NAME
    prepared_path = evidence_path.with_name(evidence_path.name + RECOVERY_PREPARED_SUFFIX)
    try:
        # The success target is immutable and must be absent before any backup
        # or database mutation. A PREPARED file is only a resumable journal.
        if evidence_path.exists():
            raise RecoveryBlocked("RECOVERY_EVIDENCE_ALREADY_EXISTS")
        intent = store.intent(intent_key)
        if (intent is None or intent.get("status") not in {"INTENT_PERSISTED", "REJECTED"}
                or intent.get("broker_order_id") is not None):
            raise RecoveryBlocked("RECOVERY_HISTORICAL_INTENT_STATE_MISMATCH")
        payload = intent.get("payload")
        if (not isinstance(payload, dict) or payload.get("symbol") != FINAM_SYMBOL
                or payload.get("side") != "SIDE_BUY" or payload.get("quantity") != {"value": "1"}):
            raise RecoveryBlocked("RECOVERY_HISTORICAL_INTENT_PAYLOAD_MISMATCH")

        # Fresh account-wide proof. Unknown or malformed facts fail closed.
        positions = _rows(readonly_api.account(account_id), "positions")
        for position in positions:
            symbol = position.get("symbol")
            if not isinstance(symbol, str) or not symbol or _decimal_contracts(position.get("quantity")) != 0:
                raise RecoveryBlocked("RECOVERY_BROKER_ACCOUNT_NOT_CLEAN")
        orders = _rows(readonly_api.orders(account_id), "orders")
        if any(_status(order.get("status")) in ACTIVE for order in orders):
            raise RecoveryBlocked("RECOVERY_BROKER_ACCOUNT_NOT_CLEAN")

        observed = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        if prepared_path.exists():
            prepared = _load_prepared(prepared_path)
            expected_prepared = {
                "schema_id": RECOVERY_SCHEMA,
                "recovery_status": "PREPARED",
                "accepted_physical_code_commit": ACCEPTED_PHYSICAL_COMMIT,
                "recovery_code_commit": recovery_code_commit,
                "physical_evidence_sha256": FAILED_PHYSICAL_EVIDENCE_SHA256,
                "intent_key": HISTORICAL_INTENT_KEY,
                "account_identity_sha256": _account_hash(account_id),
                "production_specification_id": PRODUCTION_SPECIFICATION_ID,
                "active_identity": ACTIVE_IDENTITY,
            }
            if any(prepared.get(key) != value for key, value in expected_prepared.items()):
                raise RecoveryBlocked("RECOVERY_PREPARED_EVIDENCE_AUTHORITY_MISMATCH")
            backup = root / "backups" / "stage8-11-acceptance" / str(prepared.get("backup_filename", ""))
            manifest = backup.with_name(str(prepared.get("backup_manifest_filename", "")))
            if not backup.is_file() or not manifest.is_file():
                raise RecoveryBlocked("RECOVERY_PREPARED_BACKUP_MISSING")
            try:
                manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
            except (OSError, ValueError, TypeError):
                raise RecoveryBlocked("RECOVERY_PREPARED_BACKUP_INVALID") from None
            if (not isinstance(manifest_payload, dict)
                    or manifest_payload.get("backup_filename") != backup.name
                    or manifest_payload.get("sha256") != sha256_file(backup)):
                raise RecoveryBlocked("RECOVERY_PREPARED_BACKUP_INVALID")
        else:
            inject("before_backup")
            backup, manifest = create_stage8_11_acceptance_backup(root, account_id, created_at=now)
            prepared = {
                "schema_id": RECOVERY_SCHEMA,
                "recovery_status": "PREPARED",
                "accepted_physical_code_commit": ACCEPTED_PHYSICAL_COMMIT,
                "recovery_code_commit": recovery_code_commit,
                "physical_evidence_sha256": FAILED_PHYSICAL_EVIDENCE_SHA256,
                "intent_key": HISTORICAL_INTENT_KEY,
                "account_identity_sha256": _account_hash(account_id),
                "production_specification_id": PRODUCTION_SPECIFICATION_ID,
                "active_identity": ACTIVE_IDENTITY,
                "backup_filename": backup.name,
                "backup_manifest_filename": manifest.name,
                "prepared_at_utc": observed.isoformat().replace("+00:00", "Z"),
            }
            _write_new_json(prepared_path, prepared)
            inject("after_backup")

        if intent["status"] == "INTENT_PERSISTED":
            inject("before_sqlite_mutation")
            try:
                store.db.execute("BEGIN IMMEDIATE")
                cursor = store.db.execute(
                    "UPDATE intents SET status='REJECTED',updated_at=CURRENT_TIMESTAMP "
                    "WHERE idempotency_key=? AND status='INTENT_PERSISTED' AND broker_order_id IS NULL",
                    (intent_key,))
                if cursor.rowcount != 1:
                    raise RecoveryBlocked("RECOVERY_SQLITE_COMPARE_AND_SET_FAILED")
                marks = ",".join("?" for _ in ("CANCELLED", "REJECTED", "CLOSED", "RECONCILED"))
                unresolved = store.db.execute(
                    f"SELECT COUNT(*) FROM intents WHERE status NOT IN ({marks})",
                    ("CANCELLED", "REJECTED", "CLOSED", "RECONCILED")).fetchone()[0]
                if unresolved != 0:
                    raise RecoveryBlocked("RECOVERY_UNRESOLVED_INTENTS_REMAIN")
                store.db.commit()
            except Exception:
                store.db.rollback()
                raise
            inject("after_sqlite_mutation")
        elif not prepared_path.exists():  # defensive; REJECTED is resumable only with its journal
            raise RecoveryBlocked("RECOVERY_REJECTED_WITHOUT_PREPARED_EVIDENCE")

        evidence = {
            "schema_id": RECOVERY_SCHEMA,
            "recovery_status": "COMMITTED",
            "accepted_physical_code_commit": ACCEPTED_PHYSICAL_COMMIT,
            "recovery_code_commit": recovery_code_commit,
            "physical_evidence_sha256": FAILED_PHYSICAL_EVIDENCE_SHA256,
            "intent_key": HISTORICAL_INTENT_KEY,
            "account_identity_sha256": _account_hash(account_id),
            "production_specification_id": PRODUCTION_SPECIFICATION_ID,
            "active_identity": ACTIVE_IDENTITY,
            "readonly_session": True,
            "fresh_account_wide_reconciliation": "PASS",
            "all_positions_zero": True,
            "active_broker_order_count": 0,
            "canonical_unresolved_intent_count": 0,
            "terminal_status": "REJECTED",
            "backup_filename": backup.name,
            "backup_manifest_filename": manifest.name,
            "recovered_at_utc": observed.isoformat().replace("+00:00", "Z"),
        }
        inject("during_evidence_finalization")
        _write_new_json(evidence_path, evidence)
        prepared_path.unlink()
        return evidence
    finally:
        store.close()


def main(argv: list[str] | None = None, *,
         api_factory: Callable[[str], object] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Order-incapable Stage 8.11 failed-attempt recovery")
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--account-id", required=True)
    parser.add_argument("--accepted-recovery-commit", required=True)
    parser.add_argument("--physical-evidence", type=Path, required=True)
    parser.add_argument("--physical-evidence-sha256", required=True)
    parser.add_argument("--intent-key", required=True)
    args = parser.parse_args(argv)
    secret = os.environ.pop("STAGE8_11_READONLY_SECRET", "")
    environment_account = os.environ.pop("STAGE8_11_READONLY_ACCOUNT_ID", "")
    if not secret or environment_account != args.account_id:
        print("STAGE8_11_RECOVERY_REAL_READONLY_CREDENTIAL_REQUIRED")
        return 2
    # FinamAPI exposes read methods and also implements trading methods, so the
    # recovery receives a deliberately narrowed facade with no order mutation
    # attributes at all.
    from .finam_api import FinamAPI
    transport = (api_factory or FinamAPI)(secret)
    class ReadonlyRecoveryClient:
        session_details = transport.session_details
        account = transport.account
        orders = transport.orders
    try:
        recover_historical_intent(runtime_root=args.runtime_root, account_id=args.account_id,
            readonly_api=ReadonlyRecoveryClient(), recovery_code_commit=args.accepted_recovery_commit,
            physical_evidence=args.physical_evidence,
            physical_evidence_sha256=args.physical_evidence_sha256, intent_key=args.intent_key)
    except (RecoveryBlocked, OSError, ValueError):
        print("STAGE8_11_RECOVERY_BLOCKED")
        return 1
    print("STAGE8_11_HISTORICAL_INTENT_RECOVERY_COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
