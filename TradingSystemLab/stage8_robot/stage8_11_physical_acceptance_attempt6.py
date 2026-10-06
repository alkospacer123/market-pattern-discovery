"""Manual-only Stage 8.11 attempt-6 one-contract physical acceptance entrypoint.

Merely installing this module grants no authority.  The Windows wrapper supplies
an ephemeral, exact authorization phrase and CurrentUser-DPAPI credentials after
an independent REAL_READONLY refresh.  This module is deliberately not imported
by any normal runtime owner.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .controlled_real_acceptance import (
    AcceptanceAuthority, AcceptanceBlocked, ControlledAcceptanceBroker,
    STAGE8_10_AUTHORITY, STAGE8_11_ATTEMPT6_ID, resolve_frozen_symbol,
    run_controlled_lifecycle, sanitized_evidence,
)
from .finam_api import FinamAPI
from .funding_margin_diagnostic import READY, run as collect_funding_authority
from .operations import stage8_11_exclusive_lock
from .specification import ACTIVE_IDENTITY, PRODUCTION_SPECIFICATION_ID
from .stage8_11_attempt5_manual_close_recovery import (
    RECOVERY_EVIDENCE_NAME as ATTEMPT5_RECOVERY_EVIDENCE_NAME,
    RECOVERY_SCHEMA as ATTEMPT5_RECOVERY_SCHEMA,
)
from .stage8_11_intel_acceptance import stage8_10_authority_complete
from .state import StateStore, initialize_stage8_11_acceptance_ledger
from .trading_safety_gate import (
    emergency_halt, heartbeat_path, load_kill_switch, write_kill_switch,
)
from .backup_state import create_stage8_11_acceptance_backup

AUTHORIZATION_VALUE = "STAGE_8_11_ONE_CONTRACT_ACCEPTANCE_AUTHORIZED"
INSTRUMENT = "CNYRUBF"
FINAM_SYMBOL = "CNYRUBF@RTSX"
DIRECTION = "LONG"
QUANTITY = 1
ATTEMPT_ID = STAGE8_11_ATTEMPT6_ID
REPORT_NAME = "stage8_11_physical_acceptance_attempt6.json"
HISTORICAL_REPORT_NAME = "stage8_11_physical_acceptance.json"
PREVIOUS_REPORT_NAME = "stage8_11_physical_acceptance_attempt5.json"
PREVIOUS_EVIDENCE_SHA256 = "E67127A4727C4B5505F52877A9AFDE29447551DF781E5420DD4F7695CAC92F85"
PREVIOUS_ENTRY_KEY = "stage8.11.attempt5:CNYRUBF:entry"
ATTEMPT5_RECOVERY_CODE_COMMIT = "9e42b68cc9579d8294a5bd6dc63db1b870d23000"
PRECHECK_REPORT_NAME = "stage8_11_intel_precheck.json"
PRECHECK_EVIDENCE_SHA256 = "7171B7CD0098FF51159DC05C46C0326BF7F412A2D9EA0CBB3F9BDAFBE7745455"
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


class PhysicalAcceptanceBlocked(RuntimeError):
    """A pre-submission, sanitized physical-boundary refusal."""


def verify_repository_authority(accepted_commit: str, *, repository: Path = REPOSITORY_ROOT,
                                run: Callable[..., subprocess.CompletedProcess] = subprocess.run) -> None:
    if len(accepted_commit) != 40 or any(c not in "0123456789abcdef" for c in accepted_commit):
        raise PhysicalAcceptanceBlocked("STAGE8_11_ACCEPTED_COMMIT_INVALID")
    head = run(["git", "rev-parse", "HEAD"], cwd=repository, text=True,
               capture_output=True, check=False)
    unstaged = run(["git", "diff", "--quiet"], cwd=repository, check=False)
    staged = run(["git", "diff", "--cached", "--quiet"], cwd=repository, check=False)
    if head.returncode or head.stdout.strip() != accepted_commit:
        raise PhysicalAcceptanceBlocked("STAGE8_11_ACCEPTED_COMMIT_MISMATCH")
    if unstaged.returncode or staged.returncode:
        raise PhysicalAcceptanceBlocked("STAGE8_11_WORKTREE_NOT_CLEAN")


def verify_authorization(value: str) -> None:
    if value != AUTHORIZATION_VALUE:
        raise PhysicalAcceptanceBlocked("STAGE8_11_EXPLICIT_AUTHORIZATION_REQUIRED")


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _write_new(payload: dict[str, Any], destination: Path) -> str:
    """Publish attempt-6 evidence atomically without replacing any artifact."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise PhysicalAcceptanceBlocked("STAGE8_11_ATTEMPT6_EVIDENCE_ALREADY_EXISTS")
    descriptor, name = tempfile.mkstemp(dir=destination.parent, prefix=destination.name + ".", suffix=".incomplete")
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n"); stream.flush(); os.fsync(stream.fileno())
        os.link(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return hashlib.sha256(destination.read_bytes()).hexdigest().upper()


def _physical_evidence(*, accepted_commit: str, account_hash: str, result: dict[str, Any],
                       authority: AcceptanceAuthority, external_sha256: str) -> dict[str, Any]:
    final = result.get("final_state")
    if not isinstance(final, dict):
        final = {}
    classification = result.get("classification", "BLOCKED")
    if classification == "SYNTHETIC_PASS":
        classification = "PASS"
    if classification == "BLOCKED":
        classification = "BLOCKED_PRE_SUBMISSION"
    # The schema historically called this BLOCKED.  sanitized_evidence is the
    # canonical allowlist; physical classifications are intentionally clearer.
    facts = dict(
        attempt_id=ATTEMPT_ID,
        accepted_code_commit=accepted_commit,
        sanitized_account_identity_hash=account_hash,
        instrument=INSTRUMENT, direction=DIRECTION, quantity=QUANTITY,
        preflight_gate_outcomes={
            "account_binding": len({authority.configured_account_hash, authority.observed_account_hash,
                                    authority.heartbeat_account_hash}) == 1,
            "credential_scope": authority.trading_token_loaded_from_current_user_dpapi,
            "session_write_capable": authority.trading_session_readonly is False,
            "initial_reconciliation": authority.account_reconciled,
            "instrument_binding": authority.instrument_binding_valid,
            "instrument_tradable": authority.instrument_tradable,
            "r15_capacity": authority.r15_capacity >= 1,
            "margin_capacity": authority.margin_capacity >= 1,
            "h1_data_safety": authority.h1_data_safety_valid,
        },
        kill_switch_pre_state="ARMED", kill_switch_final_state="HALTED",
        execution_authorization_observed=True,
        order_endpoint_call_count=int(result.get("order_endpoint_call_count", 0)),
        broker_order_present=(int(result.get("order_endpoint_call_count", 0)) > 0
                              and not isinstance(result.get("rejection"), dict)),
        broker_fill_count=int(bool(result.get("entry_fill_proven"))) + int(bool(result.get("flatten_fill_proven"))),
        entry_fill_proven=result.get("entry_fill_proven") is True,
        one_contract_position_observed=result.get("one_contract_position_observed") is True,
        controlled_flatten_proven=result.get("flatten_fill_proven") is True,
        final_position_quantity=final.get("position_quantity"),
        final_active_order_count=final.get("active_order_count"),
        unresolved_intent_count=final.get("unresolved_intent_count"),
        reconciliation_result="PASS" if "FINAL_RECONCILIATION_PASS" in result.get("phases", []) else "UNRESOLVED",
        physical_result_classification=classification,
        external_raw_evidence_sha256=external_sha256,
    )
    return sanitized_evidence(**facts)


def _reconcile_previous_attempt(*, runtime_root: Path, broker: ControlledAcceptanceBroker,
                                store: StateStore, accepted_commit: str) -> None:
    """Require committed manual-close recovery of attempt5; never replay its /trades history."""
    previous = runtime_root / "diagnostics" / PREVIOUS_REPORT_NAME
    if (not previous.is_file()
            or hashlib.sha256(previous.read_bytes()).hexdigest().upper() != PREVIOUS_EVIDENCE_SHA256):
        raise PhysicalAcceptanceBlocked("STAGE8_11_ATTEMPT5_EVIDENCE_MISSING_OR_MISMATCH")

    recovery_path = runtime_root / "diagnostics" / ATTEMPT5_RECOVERY_EVIDENCE_NAME
    try:
        recovery = json.loads(recovery_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        raise PhysicalAcceptanceBlocked("STAGE8_11_ATTEMPT5_MANUAL_RECOVERY_REQUIRED") from None
    if (not isinstance(recovery, dict)
            or recovery.get("schema_id") != ATTEMPT5_RECOVERY_SCHEMA
            or recovery.get("recovery_status") != "COMMITTED"
            or recovery.get("attempt5_evidence_sha256") != PREVIOUS_EVIDENCE_SHA256
            or recovery.get("intent_key") != PREVIOUS_ENTRY_KEY
            or recovery.get("account_identity_sha256") != broker.accepted_account_hash
            or recovery.get("production_specification_id") != PRODUCTION_SPECIFICATION_ID
            or recovery.get("active_identity") != ACTIVE_IDENTITY
            or recovery.get("final_local_intent_status") != "CLOSED"
            or recovery.get("attempt5_reclassified_as_pass") is not False
            or recovery.get("manual_close_history_preserved") is not True
            or recovery.get("physical_result_preserved") != "OPERATOR_INTERVENTION_REQUIRED"
            or recovery.get("recovery_code_commit") != ATTEMPT5_RECOVERY_CODE_COMMIT):
        raise PhysicalAcceptanceBlocked("STAGE8_11_ATTEMPT5_MANUAL_RECOVERY_INVALID")

    intent = store.intent(PREVIOUS_ENTRY_KEY)
    if (not intent or intent.get("status") != "CLOSED"
            or not isinstance(intent.get("broker_order_id"), str)
            or not intent.get("broker_order_id")):
        raise PhysicalAcceptanceBlocked("STAGE8_11_ATTEMPT5_ENTRY_STATE_INVALID")
    if store.unresolved_intent_count() != 0:
        raise PhysicalAcceptanceBlocked("STAGE8_11_ATTEMPT5_RECONCILIATION_INCOMPLETE")

    final = broker.account_snapshot(FINAM_SYMBOL)
    if (final.get("position_quantity") != 0
            or final.get("unexpected_position_count") != 0
            or final.get("active_order_count") != 0):
        raise PhysicalAcceptanceBlocked("STAGE8_11_ATTEMPT6_ACCOUNT_NOT_FLAT")


def execute_boundary(*, accepted_commit: str, authorization: str, account_id: str,
                     api: Any, runtime_root: Path, external_evidence_sha256: str,
                     funding_collector: Callable[..., dict[str, Any]] = collect_funding_authority,
                     now: datetime | None = None,
                     clock: Callable[[], datetime] | None = None) -> dict[str, Any]:
    """Re-prove authority, briefly arm, invoke the canonical lifecycle, halt."""
    time_source = clock or (lambda: datetime.now(timezone.utc))
    observed = now or time_source()  # boundary/preflight timestamp, never a POST timestamp
    with stage8_11_exclusive_lock(runtime_root):
        verify_authorization(authorization)
        switch, error = load_kill_switch(runtime_root)
        if error or switch is None or switch.get("state") != "HALTED":
            raise PhysicalAcceptanceBlocked("STAGE8_11_INITIAL_HALT_REQUIRED")
        if not stage8_10_authority_complete():
            raise PhysicalAcceptanceBlocked("STAGE8_11_STAGE8_10_AUTHORITY_INVALID")
        precheck_report = runtime_root / "diagnostics" / PRECHECK_REPORT_NAME
        if external_evidence_sha256.upper() != PRECHECK_EVIDENCE_SHA256:
            raise PhysicalAcceptanceBlocked("STAGE8_11_EXTERNAL_EVIDENCE_SHA256_INVALID")
        if (not precheck_report.is_file()
                or hashlib.sha256(precheck_report.read_bytes()).hexdigest().upper() != PRECHECK_EVIDENCE_SHA256):
            raise PhysicalAcceptanceBlocked("STAGE8_11_PRECHECK_EVIDENCE_MISSING_OR_MISMATCH")

        ledger = initialize_stage8_11_acceptance_ledger(runtime_root, account_id)
        store = StateStore(ledger)
        broker: ControlledAcceptanceBroker | None = None
        try:
            create_stage8_11_acceptance_backup(runtime_root, account_id)
            account_hash = _hash(account_id)
            broker = ControlledAcceptanceBroker(api, account_id, account_hash, store)
            _reconcile_previous_attempt(
                runtime_root=runtime_root, broker=broker, store=store,
                accepted_commit=accepted_commit)
            if store.unresolved_intent_count() != 0:
                raise PhysicalAcceptanceBlocked("STAGE8_11_UNRESOLVED_INTENTS_PRESENT")
            report = funding_collector(api, account_id, None, required_readonly=False)
            case = report.get("per_instrument", {}).get(f"{INSTRUMENT}:{DIRECTION}", {})
            if report.get("funding_classification") != READY:
                raise PhysicalAcceptanceBlocked("STAGE8_11_CURRENT_AUTHORITY_BLOCKED")
            symbol = resolve_frozen_symbol(INSTRUMENT)
            if symbol != FINAM_SYMBOL:
                raise PhysicalAcceptanceBlocked("STAGE8_11_FIXED_SYMBOL_MISMATCH")
            heartbeat = json.loads(heartbeat_path(runtime_root).read_text(encoding="utf-8"))
            authority = AcceptanceAuthority(
                PRODUCTION_SPECIFICATION_ID, ACTIVE_IDENTITY, STAGE8_10_AUTHORITY,
                account_hash, str(report.get("account_identity_sha256", "")), str(heartbeat.get("account_hash", "")),
                True, False, report.get("account_clean") is True, 0,
                0 if report.get("account_clean") is True else -1, store.unresolved_intent_count(),
                heartbeat.get("reconciliation_status") == "PASS", report.get("n4_binding_valid") is True,
                True, int(case.get("r15_quantity", 0)), int(case.get("margin_quantity", 0)),
            )
            # No other path in this module writes ARMED or passes execution_authorized=True.
            write_kill_switch(runtime_root, "ARMED", allow_arm=True, now=observed)
            result = run_controlled_lifecycle(authority=authority, runtime_root=runtime_root,
                execution_authorized=True, instrument=INSTRUMENT, finam_symbol=FINAM_SYMBOL,
                direction=DIRECTION, broker=broker, clock=time_source, attempt_id=ATTEMPT_ID)
            result["evidence"] = _physical_evidence(accepted_commit=accepted_commit, account_hash=account_hash,
                result=result, authority=authority, external_sha256=external_evidence_sha256)
            return result
        finally:
            emergency_halt(runtime_root, now=observed)
            store.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manual Stage 8.11 fixed one-contract acceptance")
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--accepted-commit", required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--external-evidence-sha256", required=True)
    args = parser.parse_args(argv)
    root = args.runtime_root.resolve()
    result: dict[str, Any] | None = None
    try:
        expected_evidence = root / "diagnostics" / REPORT_NAME
        if args.evidence.resolve() != expected_evidence:
            raise PhysicalAcceptanceBlocked("STAGE8_11_EVIDENCE_PATH_INVALID")
        if expected_evidence.exists():
            raise PhysicalAcceptanceBlocked("STAGE8_11_ATTEMPT6_EVIDENCE_ALREADY_EXISTS")
        verify_repository_authority(args.accepted_commit)
        authorization = os.environ.pop("STAGE8_11_PHYSICAL_AUTHORIZATION", "")
        verify_authorization(authorization)
        if os.environ.get("STAGE8_11_DPAPI_VALIDATED") != "true":
            raise PhysicalAcceptanceBlocked("STAGE8_11_DPAPI_AUTHORITY_INVALID")
        secret = os.environ.pop("STAGE8_11_TRADING_SECRET", "")
        account = os.environ.pop("STAGE8_11_ACCOUNT_ID", "")
        if not secret or not account:
            raise PhysicalAcceptanceBlocked("STAGE8_11_DPAPI_AUTHORITY_INVALID")
        result = execute_boundary(accepted_commit=args.accepted_commit, authorization=authorization,
            account_id=account, api=FinamAPI(secret), runtime_root=root,
            external_evidence_sha256=args.external_evidence_sha256)
        digest = _write_new(result["evidence"], expected_evidence)
        print(f"STAGE8_11_PHYSICAL_RESULT={result['evidence']['physical_result_classification']}")
        print(f"STAGE8_11_PHYSICAL_EVIDENCE_SHA256={digest}")
        return 0 if result["evidence"]["physical_result_classification"] in {"PASS", "NOT_ACCEPTED_NO_EXECUTION"} else 2
    except (PhysicalAcceptanceBlocked, AcceptanceBlocked, RuntimeError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc) if isinstance(exc, (PhysicalAcceptanceBlocked, AcceptanceBlocked)) else "STAGE8_11_PHYSICAL_BOUNDARY_FAILED")
        return 1
    finally:
        for key in ("STAGE8_11_PHYSICAL_AUTHORIZATION", "STAGE8_11_DPAPI_VALIDATED",
                    "STAGE8_11_TRADING_SECRET", "STAGE8_11_ACCOUNT_ID"):
            os.environ.pop(key, None)
        try: emergency_halt(root)
        except Exception: pass


if __name__ == "__main__":
    raise SystemExit(main())
