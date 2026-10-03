"""Manual Stage 8.10.3 identity/account-binding diagnostic.

This deliberately narrow operator tool can authenticate and inspect session
identity only.  Credentials enter through process-local environment variables;
the sole command-line value is the external, sanitized report destination.
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

GATE_ENV = "STAGE8_10_3_IDENTITY_BINDING"
SECRET_ENV = "FINAM_TRADING_API_SECRET"
ACCOUNT_ENV = "FINAM_TRADING_ACCOUNT_ID"
SCHEMA_ID = "STAGE8_10_3_IDENTITY_ACCOUNT_BINDING_REPORT_V1"


class IdentityBindingError(RuntimeError):
    """A deterministic, sanitized diagnostic failure."""


def _fail(code: str) -> None:
    raise IdentityBindingError(code)


def validate_identity_binding(secret: str, expected_account: str, *,
                              api_factory: Callable[[str], object] = FinamAPI,
                              observed_utc: datetime | None = None) -> dict:
    """Authenticate and require one exact expected-account occurrence."""
    if not secret:
        _fail("TRADING_IDENTITY_SECRET_MISSING")
    if not expected_account:
        _fail("TRADING_IDENTITY_ACCOUNT_MISSING")
    try:
        api = api_factory(secret)
        api.create_session()
    except Exception:
        _fail("TRADING_IDENTITY_SESSION_CREATE_FAILED")
    try:
        details = api.session_details()
    except Exception:
        _fail("TRADING_IDENTITY_SESSION_DETAILS_FAILED")
    if not isinstance(details, dict):
        _fail("TRADING_IDENTITY_SESSION_DETAILS_NOT_OBJECT")
    if "account_ids" not in details:
        _fail("TRADING_IDENTITY_ACCOUNT_IDS_MISSING")
    account_ids = details["account_ids"]
    if not isinstance(account_ids, list) or any(
            not isinstance(value, (str, int)) or isinstance(value, bool)
            for value in account_ids):
        _fail("TRADING_IDENTITY_ACCOUNT_IDS_MALFORMED")
    normalized = [str(value) for value in account_ids]
    occurrences = normalized.count(str(expected_account))
    if occurrences == 0:
        _fail("TRADING_IDENTITY_EXPECTED_ACCOUNT_NOT_ENUMERATED")
    if occurrences != 1:
        _fail("TRADING_IDENTITY_EXPECTED_ACCOUNT_DUPLICATED")
    now = observed_utc or datetime.now(timezone.utc)
    return {
        "schema_id": SCHEMA_ID,
        "observed_utc": now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "production_specification_id": PRODUCTION_SPECIFICATION_ID,
        "local_readonly_trading_account_match": True,
        "trading_session_created": True,
        "expected_account_enumerated": True,
        "expected_account_occurrence_count": 1,
        "enumerated_account_count": len(normalized),
        "identity_account_binding": "PASS",
        "trading_token_used": True,
        "finam_authentication_performed": True,
        "order_count": 0,
        "order_endpoint_called": False,
        "live_trading_authorized": False,
        "real_order_transmission_authorized": False,
        "stage8_10_4_status": "NOT_STARTED",
        "stage8_11_status": "NOT_STARTED_NOT_AUTHORIZED",
        "stage8_12_status": "NOT_STARTED_NOT_AUTHORIZED",
    }


def write_report(report: dict, destination: str | Path) -> None:
    """Atomically write only the already-sanitized report."""
    path = Path(destination)
    if not path.is_absolute() or not path.parent.is_dir() or path.name != "stage8_10_3_identity_account_binding.json":
        _fail("TRADING_IDENTITY_REPORT_PATH_INVALID")
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
        _fail("TRADING_IDENTITY_REPORT_WRITE_FAILED")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Stage 8.10.3 identity binding")
    parser.add_argument("--report", required=True)
    args = parser.parse_args(argv)
    try:
        if os.environ.get(GATE_ENV, "").lower() != "true":
            _fail("TRADING_IDENTITY_DIAGNOSTIC_GATE_REQUIRED")
        report = validate_identity_binding(os.environ.get(SECRET_ENV, ""), os.environ.get(ACCOUNT_ENV, ""))
        write_report(report, args.report)
    except IdentityBindingError as exc:
        print(str(exc))
        return 1
    print("STAGE_8_10_3_FINAM_SESSION_CREATED")
    print("STAGE_8_10_3_EXPECTED_ACCOUNT_ENUMERATED")
    print("STAGE_8_10_3_IDENTITY_ACCOUNT_BINDING_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
