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
from typing import Any

from .backup_state import create_stage8_11_acceptance_backup, sha256_file
from .controlled_real_acceptance import ACTIVE, _decimal_contracts, _rows, _status
from .specification import ACTIVE_IDENTITY, PRODUCTION_SPECIFICATION_ID, load_frozen_specification
from .state import StateStore, initialize_stage8_11_acceptance_ledger, stage8_11_acceptance_path

ACCEPTED_PHYSICAL_COMMIT = "069806355fc6931470d7f68d5ca6db20b06358fa"
FAILED_PHYSICAL_EVIDENCE_SHA256 = "9FEFC5469F2C97F1EB36A5B5C99D323FA37BB948CF53C8A8745A27A06AB3B324"
HISTORICAL_INTENT_KEY = "stage8.11:CNYRUBF:entry"
FINAM_SYMBOL = "CNYRUBF@RTSX"
RECOVERY_EVIDENCE_NAME = "stage8_11_failed_attempt_recovery.json"
RECOVERY_SCHEMA = "stage8_11_failed_attempt_recovery.v1"


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


def recover_historical_intent(*, runtime_root: Path, account_id: str, readonly_api: object,
                              accepted_commit: str, physical_evidence: Path,
                              physical_evidence_sha256: str, intent_key: str,
                              now: datetime | None = None) -> dict[str, Any]:
    """Close only the bound historical intent after a fresh clean-account proof."""
    root = Path(runtime_root)
    if accepted_commit != ACCEPTED_PHYSICAL_COMMIT:
        raise RecoveryBlocked("RECOVERY_ACCEPTED_COMMIT_MISMATCH")
    if intent_key != HISTORICAL_INTENT_KEY:
        raise RecoveryBlocked("RECOVERY_INTENT_KEY_MISMATCH")
    if physical_evidence_sha256.upper() != FAILED_PHYSICAL_EVIDENCE_SHA256:
        raise RecoveryBlocked("RECOVERY_PHYSICAL_EVIDENCE_SHA256_MISMATCH")
    if not physical_evidence.is_file() or sha256_file(physical_evidence).upper() != FAILED_PHYSICAL_EVIDENCE_SHA256:
        raise RecoveryBlocked("RECOVERY_PHYSICAL_EVIDENCE_FILE_MISMATCH")
    frozen = load_frozen_specification()
    if frozen.production_id != PRODUCTION_SPECIFICATION_ID or frozen.identity != ACTIVE_IDENTITY:
        raise RecoveryBlocked("RECOVERY_FROZEN_IDENTITY_MISMATCH")
    details = readonly_api.session_details()
    accounts = [str(value) for value in details.get("account_ids", [])] if isinstance(details, dict) else []
    if not isinstance(details, dict) or details.get("readonly") is not True or accounts.count(account_id) != 1:
        raise RecoveryBlocked("RECOVERY_READONLY_ACCOUNT_IDENTITY_MISMATCH")

    ledger = initialize_stage8_11_acceptance_ledger(root, account_id)
    if ledger.resolve() != stage8_11_acceptance_path(root).resolve():
        raise RecoveryBlocked("RECOVERY_CANONICAL_LEDGER_MISMATCH")
    store = StateStore(ledger)
    evidence_path = root / "diagnostics" / RECOVERY_EVIDENCE_NAME
    try:
        intent = store.intent(intent_key)
        if (intent is None or intent.get("status") != "INTENT_PERSISTED"
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

        backup, manifest = create_stage8_11_acceptance_backup(root, account_id, created_at=now)
        store.transition_intent(intent_key, "REJECTED")
        if store.unresolved_intent_count() != 0:
            raise RecoveryBlocked("RECOVERY_UNRESOLVED_INTENTS_REMAIN")
        observed = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        evidence = {
            "schema_id": RECOVERY_SCHEMA,
            "accepted_physical_code_commit": ACCEPTED_PHYSICAL_COMMIT,
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
        _write_new_json(evidence_path, evidence)
        return evidence
    finally:
        store.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Order-incapable Stage 8.11 failed-attempt recovery")
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--account-id", required=True)
    parser.add_argument("--accepted-commit", required=True)
    parser.add_argument("--physical-evidence", type=Path, required=True)
    parser.add_argument("--physical-evidence-sha256", required=True)
    parser.add_argument("--intent-key", required=True)
    args = parser.parse_args(argv)
    # Deliberately no credential loading here: the operator entrypoint must inject
    # an already authenticated REAL_READONLY client via recover_historical_intent.
    print("STAGE8_11_RECOVERY_REQUIRES_INJECTED_REAL_READONLY_CLIENT")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
