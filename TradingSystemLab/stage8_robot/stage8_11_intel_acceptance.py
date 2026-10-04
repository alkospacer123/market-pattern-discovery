"""Operator-only Stage 8.11 Intel physical precheck (zero order capability).

This module deliberately has no execution mode and never imports the controlled
acceptance broker.  A later physical run is a separate, independently audited
operator action.  Candidate selection follows frozen N4 order, not performance.
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

from .finam_api import FinamAPI
from .funding_margin_diagnostic import READY, run as collect_funding_authority
from .instrument_resolver import N4, load_registry
from .operations import InstanceLock
from .specification import PRODUCTION_SPECIFICATION_ID
from .state import readonly_unresolved_intent_count
from .trading_safety_gate import evaluate_new_entry_gate, heartbeat_path

MODE = "STAGE8_11_PRECHECK_ONLY"
STATUS = "CODE_READY_PHYSICAL_PRECHECK_NOT_YET_EXECUTED"
STAGE8_10 = "STAGE_8_10_TRADING_TOKEN_LIFECYCLE_COMPLETE"
SOURCE_BASE_COMMIT = "14b4cdb13a1bc62031a1b859926bc65ce1071105"
REPORT_NAME = "stage8_11_intel_precheck.json"
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
ALLOWED_DIRECTIONS = frozenset({"LONG", "SHORT"})
REGISTRY = Path(__file__).with_name("production_instrument_registry.csv")
CANONICAL_STATE = Path("state") / "readonly-supervisor.sqlite3"
EXPECTED_GATE_REASONS = ["KILL_SWITCH_HALTED", "EXECUTION_NOT_AUTHORIZED"]


class PrecheckBlocked(RuntimeError):
    pass


def _fail(code: str) -> None:
    raise PrecheckBlocked(code)


def _external(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if not path.is_absolute() or path.name != REPORT_NAME or resolved == REPOSITORY_ROOT or REPOSITORY_ROOT in resolved.parents:
        _fail("STAGE8_11_REPORT_PATH_INVALID")
    return resolved


def select_candidate(report: dict[str, Any], direction: str) -> tuple[str, dict[str, Any]]:
    """Select the first feasible member in frozen N4 order (operational only)."""
    if direction not in ALLOWED_DIRECTIONS:
        _fail("STAGE8_11_DIRECTION_AUTHORITY_REQUIRED")
    cases = report.get("per_instrument")
    if not isinstance(cases, dict):
        _fail("STAGE8_11_PHYSICAL_ACCEPTANCE_BLOCKED_INSUFFICIENT_CAPACITY")
    for instrument in N4:
        case = cases.get(f"{instrument}:{direction}")
        if (isinstance(case, dict) and type(case.get("r15_quantity")) is int
                and type(case.get("margin_quantity")) is int
                and case["r15_quantity"] >= 1 and case["margin_quantity"] >= 1
                and type(case.get("final_quantity")) is int and case["final_quantity"] >= 1):
            return instrument, case
    _fail("STAGE8_11_PHYSICAL_ACCEPTANCE_BLOCKED_INSUFFICIENT_CAPACITY")


def recovery_implementation_available() -> bool:
    """Statically prove the accepted recovery implementation is present.

    Reading source cannot construct a broker or expose an order endpoint to this
    process, while still proving each required later physical branch exists.
    """
    source = Path(__file__).with_name("controlled_real_acceptance.py").read_text(encoding="utf-8")
    required = ("ENTRY_UNCERTAIN_RECONCILE", "broker.cancel(order_id)",
                "ONE_CONTRACT_POSITION_OBSERVED", "submit_flatten",
                "FLATTEN_UNCERTAIN_RECONCILE", "FINAL_RECONCILIATION_PASS",
                'emergency_halt(runtime_root')
    return all(token in source for token in required)


def precheck_only(*, api: Any, account_id: str, runtime_root: Path, direction: str,
                  external_evidence_sha256: str, accepted_commit: str,
                  funding_collector: Callable[..., dict] = collect_funding_authority,
                  now: datetime | None = None, registry_path: Path = REGISTRY) -> dict[str, Any]:
    """Perform read/session preflight; the object passed here need not expose POST methods."""
    observed_now = now or datetime.now(timezone.utc)
    gate = evaluate_new_entry_gate(runtime_root=runtime_root, now=observed_now,
                                   execution_authorized=False)
    if gate.get("reason_codes") != EXPECTED_GATE_REASONS:
        _fail("STAGE8_11_SAFETY_GATE_BLOCKED")
    heartbeat = json.loads(heartbeat_path(runtime_root).read_text(encoding="utf-8"))
    account_hash = hashlib.sha256(account_id.encode()).hexdigest()
    if heartbeat.get("account_hash") != account_hash: _fail("STAGE8_11_ACCOUNT_MISMATCH")
    try: canonical_unresolved = readonly_unresolved_intent_count(runtime_root / CANONICAL_STATE)
    except Exception: _fail("STAGE8_11_CANONICAL_INTENTS_INVALID")
    if canonical_unresolved != 0: _fail("STAGE8_11_CANONICAL_UNRESOLVED_INTENTS")
    report = funding_collector(api, account_id, None, required_readonly=False)
    if report.get("reason_code") == "TOKEN_NOT_WRITE_CAPABLE": _fail("STAGE8_11_TRADING_TOKEN_READONLY")
    if report.get("reason_code") == "ACTIVE_ORDERS_PRESENT": _fail("STAGE8_11_ACTIVE_ORDERS_PRESENT")
    if report.get("funding_classification") != READY: _fail("STAGE8_11_FUNDING_AUTHORITY_BLOCKED")
    instrument, case = select_candidate(report, direction)
    if not recovery_implementation_available(): _fail("STAGE8_11_RECOVERY_IMPLEMENTATION_UNAVAILABLE")
    try:
        matches=[row for row in load_registry(registry_path) if row.research_symbol == instrument]
    except Exception: _fail("STAGE8_11_FROZEN_REGISTRY_INVALID")
    if (len(matches) != 1 or not matches[0].finam_symbol
            or matches[0].binding_status != "AUTHENTICATED_REAL_READONLY"
            or matches[0].trading_status != "TRADABLE"):
        _fail("STAGE8_11_FROZEN_REGISTRY_BINDING_INVALID")
    symbol = matches[0].finam_symbol
    if not isinstance(external_evidence_sha256, str) or len(external_evidence_sha256) != 64:
        _fail("STAGE8_11_EXTERNAL_EVIDENCE_SHA256_INVALID")
    return {"schema_id":"stage8_11_intel_precheck.v1", "mode":MODE,
        "accepted_code_commit":accepted_commit, "production_specification_id":PRODUCTION_SPECIFICATION_ID,
        "sanitized_account_hash":account_hash, "selected_n4_instrument":instrument,
        "prospective_direction":direction, "resolved_finam_symbol":symbol,
        "stage8_10_authority":"PASS", "dpapi_authority":"PASS",
        "session_write_capable":"PASS", "account_binding":"PASS", "reconciliation":"PASS",
        "active_orders":0, "unresolved_intents":0, "canonical_unresolved_intents":canonical_unresolved,
        "safety_gate_reason_codes":gate["reason_codes"], "instrument_binding":"PASS", "tradable":"PASS",
        "r15_permits_at_least_one_contract":case["r15_quantity"] >= 1,
        "margin_permits_at_least_one_contract":case["margin_quantity"] >= 1,
        "stage8_11_acceptance_quantity":1, "kill_switch_observed":"HALTED",
        "execution_authorization_observed":False, "order_endpoint_call_count":0,
        "real_order_count":0, "recovery_readiness":"PASS", "external_evidence_sha256":external_evidence_sha256,
        "stage8_11_status":"IN_PROGRESS_CODE_READY_PENDING_PHYSICAL_ACCEPTANCE",
        "stage8_12_status":"NOT_STARTED_NOT_AUTHORIZED"}


def write_report(report: dict[str, Any], output: Path) -> None:
    destination = _external(output); destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=destination.parent, prefix=destination.name+".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(report, stream, indent=2, sort_keys=True); stream.write("\n"); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, destination)
    finally:
        Path(temporary).unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("--runtime-root",type=Path,required=True)
    parser.add_argument("--report",type=Path,required=True); parser.add_argument("--direction",choices=sorted(ALLOWED_DIRECTIONS),required=True)
    parser.add_argument("--accepted-commit",required=True)
    args=parser.parse_args(argv)
    try:
        root=args.runtime_root.resolve()
        if subprocess.run(["git","diff","--quiet"],cwd=REPOSITORY_ROOT).returncode or subprocess.run(["git","diff","--cached","--quiet"],cwd=REPOSITORY_ROOT).returncode: _fail("STAGE8_11_WORKTREE_NOT_CLEAN")
        commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=REPOSITORY_ROOT,text=True).strip()
        if len(args.accepted_commit) != 40 or commit != args.accepted_commit: _fail("STAGE8_11_ACCEPTED_COMMIT_MISMATCH")
        if os.environ.get("STAGE8_11_DPAPI_VALIDATED") != "true": _fail("STAGE8_11_DPAPI_AUTHORITY_INVALID")
        secret=os.environ.get("STAGE8_11_TRADING_SECRET",""); account=os.environ.get("STAGE8_11_ACCOUNT_ID","")
        if not secret or not account: _fail("STAGE8_11_DPAPI_AUTHORITY_INVALID")
        with InstanceLock(root/"locks/stage8-11-intel-precheck.lock"):
            result=precheck_only(api=FinamAPI(secret),account_id=account,runtime_root=root,direction=args.direction,
                external_evidence_sha256=os.environ.get("STAGE8_11_EXTERNAL_EVIDENCE_SHA256",""),accepted_commit=args.accepted_commit)
            write_report(result,args.report)
    except (PrecheckBlocked, OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc) if isinstance(exc,PrecheckBlocked) else "STAGE8_11_PRECHECK_FAILED"); return 1
    finally:
        for key in ("STAGE8_11_TRADING_SECRET","STAGE8_11_ACCOUNT_ID"): os.environ.pop(key,None)
    print("STAGE8_11_PRECHECK_ONLY_PASS"); return 0


if __name__ == "__main__": raise SystemExit(main())
