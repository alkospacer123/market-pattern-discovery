"""Stage 8.10.7 Intel Trading Token session-only acceptance diagnostic.

The physical operator wrapper supplies an already locally-bound Trading Token.
This module observes the production kill switch before and after the two allowed
FINAM session calls.  It has no order, market-data, or account-data capability.
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .finam_api import FinamAPI
from .specification import PRODUCTION_SPECIFICATION_ID
from .trading_safety_gate import load_kill_switch

GATE_ENV = "STAGE8_10_7_INTEL_TRADING_TOKEN_ACCEPTANCE"
SECRET_ENV = "FINAM_8107_TRADING_API_SECRET"
ACCOUNT_ENV = "FINAM_8107_ACCOUNT_ID"
LOCAL_BINDING_ENV = "STAGE8_10_7_LOCAL_ACCOUNT_BINDING_CONFIRMED"
SCHEMA_ID = "stage8_10_7_intel_trading_token_acceptance.v1"
REPORT_NAME = "stage8_10_7_intel_trading_token_acceptance.json"
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


class TradingTokenAcceptanceError(RuntimeError):
    """A deterministic error that never contains credential or account data."""


def _fail(code: str) -> None:
    raise TradingTokenAcceptanceError(code)


def _halted_switch(runtime_root: str | Path, *, post: bool = False) -> None:
    invalid = "STAGE8_10_7_POST_KILL_SWITCH_INVALID" if post else "STAGE8_10_7_KILL_SWITCH_INVALID"
    not_halted = "STAGE8_10_7_POST_KILL_SWITCH_NOT_HALTED" if post else "STAGE8_10_7_KILL_SWITCH_NOT_HALTED"
    try:
        switch, error = load_kill_switch(runtime_root)
    except Exception:
        _fail(invalid)
    if error or not isinstance(switch, dict):
        _fail(invalid)
    if switch.get("production_specification_id") != PRODUCTION_SPECIFICATION_ID:
        _fail(invalid)
    if switch.get("state") != "HALTED":
        _fail(not_halted)


def validate_intel_trading_token_acceptance(
    secret: str,
    expected_account: str,
    runtime_root: str | Path,
    *,
    local_account_binding_confirmed: bool,
    api_factory: Callable[[str], object] = FinamAPI,
    observed_utc: datetime | None = None,
) -> dict:
    """Validate one Trading Token session while the production switch is HALTED."""
    if not secret:
        _fail("STAGE8_10_7_SECRET_MISSING")
    if not expected_account:
        _fail("STAGE8_10_7_ACCOUNT_MISSING")
    if local_account_binding_confirmed is not True:
        _fail("STAGE8_10_7_LOCAL_ACCOUNT_BINDING_NOT_CONFIRMED")

    # This observation must precede construction of the network-capable client.
    _halted_switch(runtime_root)
    try:
        api = api_factory(secret)
        api.create_session()
    except Exception:
        _fail("STAGE8_10_7_SESSION_CREATE_FAILED")
    try:
        details = api.session_details()
    except Exception:
        _fail("STAGE8_10_7_SESSION_DETAILS_FAILED")
    if not isinstance(details, dict):
        _fail("STAGE8_10_7_SESSION_DETAILS_NOT_OBJECT")
    if "account_ids" not in details:
        _fail("STAGE8_10_7_ACCOUNT_IDS_MISSING")
    account_ids = details["account_ids"]
    if not isinstance(account_ids, list) or any(
        not isinstance(value, (str, int)) or isinstance(value, bool) for value in account_ids
    ):
        _fail("STAGE8_10_7_ACCOUNT_IDS_MALFORMED")
    occurrences = [str(value) for value in account_ids].count(str(expected_account))
    if occurrences == 0:
        _fail("STAGE8_10_7_EXPECTED_ACCOUNT_NOT_ENUMERATED")
    if occurrences != 1:
        _fail("STAGE8_10_7_EXPECTED_ACCOUNT_DUPLICATED")
    if "readonly" not in details:
        _fail("STAGE8_10_7_READONLY_MISSING")
    if type(details["readonly"]) is not bool:
        _fail("STAGE8_10_7_READONLY_NOT_EXACT_BOOL")
    if details["readonly"] is not False:
        _fail("STAGE8_10_7_TRADING_TOKEN_IS_READONLY")

    _halted_switch(runtime_root, post=True)
    now = observed_utc or datetime.now(timezone.utc)
    return {
        "schema_id": SCHEMA_ID,
        "observed_utc": now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "production_specification_id": PRODUCTION_SPECIFICATION_ID,
        "mode": "INTEL_TRADING_TOKEN_SESSION_ACCEPTANCE_NO_ORDER",
        "local_readonly_trading_account_match": True,
        "trading_dpapi_current_user_validated": True,
        "trading_credential_production_id_validated": True,
        "production_kill_switch_pre_valid": True,
        "production_kill_switch_pre_state": "HALTED",
        "trading_session_created": True,
        "expected_account_enumerated": True,
        "expected_account_occurrence_count": 1,
        "trading_token_readonly": False,
        "trading_token_write_boundary_confirmed": True,
        "remote_call_scope": "SESSION_CREATE_AND_DETAILS_ONLY",
        "production_kill_switch_post_valid": True,
        "production_kill_switch_post_state": "HALTED",
        "trading_token_used": True,
        "readonly_token_used_for_remote_auth": False,
        "finam_authentication_performed": True,
        "order_endpoint_called": False,
        "order_count": 0,
        "execution_authorized": False,
        "live_trading_authorized": False,
        "real_order_transmission_authorized": False,
        "scheduled_task_required": False,
        "stage8_10_8_status": "NOT_STARTED",
        "stage8_11_status": "NOT_STARTED_NOT_AUTHORIZED",
        "stage8_12_status": "NOT_STARTED_NOT_AUTHORIZED",
    }


def write_report(report: dict, destination: str | Path) -> None:
    """Atomically publish sanitized evidence outside the repository."""
    path = Path(destination)
    try:
        resolved = path.resolve()
    except (OSError, RuntimeError):
        _fail("STAGE8_10_7_REPORT_PATH_INVALID")
    if resolved == REPOSITORY_ROOT or REPOSITORY_ROOT in resolved.parents:
        _fail("STAGE8_10_7_REPORT_REPOSITORY_OUTPUT_FORBIDDEN")
    if not path.is_absolute() or path.name != REPORT_NAME:
        _fail("STAGE8_10_7_REPORT_PATH_INVALID")
    parent = resolved.parent
    temporary = None
    try:
        parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=parent)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(report, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, resolved)
    except Exception:
        if temporary:
            try:
                os.unlink(temporary)
            except OSError:
                pass
        _fail("STAGE8_10_7_REPORT_WRITE_FAILED")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Stage 8.10.7 Intel Trading Token acceptance")
    parser.add_argument("--runtime-root", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args(argv)
    try:
        if os.environ.get(GATE_ENV, "").lower() != "true":
            _fail("STAGE8_10_7_GATE_REQUIRED")
        report = validate_intel_trading_token_acceptance(
            os.environ.get(SECRET_ENV, ""),
            os.environ.get(ACCOUNT_ENV, ""),
            args.runtime_root,
            local_account_binding_confirmed=os.environ.get(LOCAL_BINDING_ENV, "").lower() == "true",
        )
        write_report(report, args.report)
    except TradingTokenAcceptanceError as exc:
        print(str(exc))
        return 1
    print("STAGE_8_10_7_INTEL_TRADING_TOKEN_ACCEPTANCE_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
