"""Manual Stage 8.10.4 token permission-boundary diagnostic.

This operator-only tool authenticates two independent sessions and inspects
only FINAM session details.  It establishes the token-level ``readonly``
boundary; it neither exercises nor predicts acceptance by any execution path.
Credentials enter only through Stage-8.10.4-specific process environment
variables.  The sole command-line value is the sanitized report destination.
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

GATE_ENV = "STAGE8_10_4_PERMISSION_BOUNDARY"
READONLY_SECRET_ENV = "FINAM_PERMISSION_READONLY_API_SECRET"
TRADING_SECRET_ENV = "FINAM_PERMISSION_TRADING_API_SECRET"
ACCOUNT_ENV = "FINAM_PERMISSION_ACCOUNT_ID"
SCHEMA_ID = "STAGE8_10_4_TOKEN_PERMISSION_BOUNDARY_REPORT_V1"
REPORT_NAME = "stage8_10_4_permission_boundary.json"


class PermissionBoundaryError(RuntimeError):
    """A deterministic, sanitized diagnostic failure."""


def _fail(code: str) -> None:
    raise PermissionBoundaryError(code)


def _details(api: object, expected_account: str, role: str) -> dict:
    try:
        api.create_session()
    except Exception:
        _fail(f"PERMISSION_BOUNDARY_{role}_SESSION_CREATE_FAILED")
    try:
        details = api.session_details()
    except Exception:
        _fail(f"PERMISSION_BOUNDARY_{role}_SESSION_DETAILS_FAILED")
    if not isinstance(details, dict):
        _fail(f"PERMISSION_BOUNDARY_{role}_SESSION_DETAILS_NOT_OBJECT")
    if "account_ids" not in details:
        _fail(f"PERMISSION_BOUNDARY_{role}_ACCOUNT_IDS_MISSING")
    account_ids = details["account_ids"]
    if not isinstance(account_ids, list) or any(
        not isinstance(value, (str, int)) or isinstance(value, bool)
        for value in account_ids
    ):
        _fail(f"PERMISSION_BOUNDARY_{role}_ACCOUNT_IDS_MALFORMED")
    occurrences = [str(value) for value in account_ids].count(str(expected_account))
    if occurrences == 0:
        _fail(f"PERMISSION_BOUNDARY_{role}_EXPECTED_ACCOUNT_NOT_ENUMERATED")
    if occurrences != 1:
        _fail(f"PERMISSION_BOUNDARY_{role}_EXPECTED_ACCOUNT_DUPLICATED")
    if "readonly" not in details:
        _fail(f"PERMISSION_BOUNDARY_{role}_READONLY_MISSING")
    if type(details["readonly"]) is not bool:
        _fail(f"PERMISSION_BOUNDARY_{role}_READONLY_NOT_EXACT_BOOL")
    return details


def validate_permission_boundary(
    readonly_secret: str,
    trading_secret: str,
    expected_account: str,
    *,
    api_factory: Callable[[str], object] = FinamAPI,
    observed_utc: datetime | None = None,
) -> dict:
    """Validate exact, separate read-only and write-boundary session flags."""
    if not readonly_secret:
        _fail("PERMISSION_BOUNDARY_READONLY_SECRET_MISSING")
    if not trading_secret:
        _fail("PERMISSION_BOUNDARY_TRADING_SECRET_MISSING")
    if not expected_account:
        _fail("PERMISSION_BOUNDARY_EXPECTED_ACCOUNT_MISSING")

    readonly_details = _details(api_factory(readonly_secret), expected_account, "READONLY")
    trading_details = _details(api_factory(trading_secret), expected_account, "TRADING")
    if readonly_details["readonly"] is not True:
        _fail("PERMISSION_BOUNDARY_READONLY_TOKEN_NOT_READONLY")
    if trading_details["readonly"] is not False:
        _fail("PERMISSION_BOUNDARY_TRADING_TOKEN_IS_READONLY")

    now = observed_utc or datetime.now(timezone.utc)
    return {
        "schema_id": SCHEMA_ID,
        "observed_utc": now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "production_specification_id": PRODUCTION_SPECIFICATION_ID,
        "local_readonly_trading_account_match": True,
        "readonly_session_created": True,
        "trading_session_created": True,
        "readonly_expected_account_enumerated": True,
        "trading_expected_account_enumerated": True,
        "readonly_expected_account_occurrence_count": 1,
        "trading_expected_account_occurrence_count": 1,
        "readonly_token_readonly": True,
        "trading_token_readonly": False,
        "token_permission_boundary": "PASS",
        "readonly_token_used": True,
        "trading_token_used": True,
        "finam_authentication_performed": True,
        "order_count": 0,
        "order_endpoint_called": False,
        "order_path_validation_performed": False,
        "live_trading_authorized": False,
        "real_order_transmission_authorized": False,
        "stage8_10_5_status": "NOT_STARTED",
        "stage8_11_status": "NOT_STARTED_NOT_AUTHORIZED",
        "stage8_12_status": "NOT_STARTED_NOT_AUTHORIZED",
    }


def write_report(report: dict, destination: str | Path) -> None:
    """Atomically write the already-sanitized report to its reserved filename."""
    path = Path(destination)
    if not path.is_absolute() or not path.parent.is_dir() or path.name != REPORT_NAME:
        _fail("PERMISSION_BOUNDARY_REPORT_PATH_INVALID")
    temporary = None
    try:
        fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except Exception:
        if temporary:
            try:
                os.unlink(temporary)
            except OSError:
                pass
        _fail("PERMISSION_BOUNDARY_REPORT_WRITE_FAILED")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Stage 8.10.4 token permission boundary")
    parser.add_argument("--report", required=True)
    args = parser.parse_args(argv)
    try:
        if os.environ.get(GATE_ENV, "").lower() != "true":
            _fail("PERMISSION_BOUNDARY_DIAGNOSTIC_GATE_REQUIRED")
        report = validate_permission_boundary(
            os.environ.get(READONLY_SECRET_ENV, ""),
            os.environ.get(TRADING_SECRET_ENV, ""),
            os.environ.get(ACCOUNT_ENV, ""),
        )
        write_report(report, args.report)
    except PermissionBoundaryError as exc:
        print(str(exc))
        return 1
    print("STAGE_8_10_4_READONLY_SESSION_CREATED")
    print("STAGE_8_10_4_TRADING_SESSION_CREATED")
    print("STAGE_8_10_4_READONLY_TOKEN_CONFIRMED")
    print("STAGE_8_10_4_TRADING_TOKEN_WRITE_BOUNDARY_CONFIRMED")
    print("STAGE_8_10_4_TOKEN_PERMISSION_BOUNDARY_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
