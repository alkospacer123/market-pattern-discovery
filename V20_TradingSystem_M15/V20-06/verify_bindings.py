"""V20-06.1: three FINAM READONLY account↔token bindings on the user's Intel.

Reuse H1 ReadonlyFillAPI unmodified. No trading commands, H1 token reuse, broker
state import, Windows Task operations, or secret persistence.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import getpass
import hashlib
import json
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parents[1]
H1_SOURCE = BASE / "source-raw"
REPORT = BASE / "readonly-06" / "ACCOUNT_BINDING_REPORT.json"
ROBOTS = ("v20-shallow", "v20-obv", "v20-inside")


def _read_h1():
    if not (H1_SOURCE / "TradingSystemLab/stage8_robot/finam_fill_price_readonly.py").is_file():
        raise RuntimeError("V20_05_PINNED_H1_READONLY_SOURCE_NOT_INSTALLED")
    sys.path.insert(0, str(H1_SOURCE))
    from TradingSystemLab.stage8_robot.finam_fill_price_readonly import (
        ReadonlyFillAPI, FillDiagnosticBlocked,
    )
    return ReadonlyFillAPI, FillDiagnosticBlocked


def _fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _self_test() -> None:
    ReadonlyFillAPI, FillDiagnosticBlocked = _read_h1()
    class Stub(ReadonlyFillAPI):
        def create_session(self):
            return {"expires_in": 600}
        def session_details(self):
            return self.details

    api = Stub("fake-token", "demo-a")
    for method, path in (
        ("POST", "/v1/accounts/demo-a/orders"),
        ("POST", "/v1/accounts/demo-a/sltp-orders"),
        ("DELETE", "/v1/accounts/demo-a/orders/123"),
        ("GET", "/v1/accounts/demo-b"),
        ("GET", "/v1/accounts/demo-a"),
    ):
        try:
            api._request(method, path)
        except FillDiagnosticBlocked:
            pass
        else:
            raise AssertionError("READONLY_ALLOWLIST_FAILED")
    api.details = {"readonly": False, "account_ids": ["demo-a"]}
    try:
        api.connect_readonly()
    except FillDiagnosticBlocked:
        pass
    else:
        raise AssertionError("WRITE_TOKEN_WAS_ACCEPTED")
    api.details = {"readonly": True, "account_ids": ["demo-b"]}
    try:
        api.connect_readonly()
    except FillDiagnosticBlocked:
        pass
    else:
        raise AssertionError("FOREIGN_ACCOUNT_WAS_ACCEPTED")
    api.details = {"readonly": True, "account_ids": ["demo-a"]}
    api.connect_readonly()
    if not api.bound:
        raise AssertionError("EXACT_READONLY_ACCOUNT_NOT_BOUND")
    print("V20_06_1_OFFLINE_SOURCE_AND_REQUEST_GATES=PASS")


def _connect() -> int:
    ReadonlyFillAPI, _ = _read_h1()
    if not (BASE / ".venv-raw" / "Scripts" / "python.exe").is_file():
        raise RuntimeError("V20_05_PYTHON_NOT_INSTALLED")
    if not (BASE / "acceptance-raw" / "WINDOWS_ACCEPTANCE_REPORT.json").is_file():
        raise RuntimeError("V20_05_WINDOWS_REPORT_NOT_FOUND")

    seen_accounts: set[str] = set()
    seen_token_digests: set[str] = set()
    results: list[dict] = []
    for robot in ROBOTS:
        print("READONLY_BINDING_CHECK=" + robot)
        account_id = getpass.getpass("FINAM account_id for " + robot + " (hidden): ").strip()
        token = getpass.getpass("FINAM READONLY token for " + robot + " (hidden): ").strip()
        if (not account_id or not token or any(ch in account_id for ch in "/?#\r\n")
                or len(account_id) > 128):
            raise RuntimeError("ACCOUNT_OR_TOKEN_MISSING_OR_INVALID")
        digest = _fingerprint(token)
        if account_id in seen_accounts or digest in seen_token_digests:
            raise RuntimeError("V20_ACCOUNT_OR_TOKEN_NOT_UNIQUE")
        # H1's accepted ReadonlyFillAPI: two session POSTs only, no order endpoints.
        # FINAM session details must prove readonly=true and exactly this account.
        try:
            api = ReadonlyFillAPI(token, account_id)
            api.connect_readonly()
        except Exception:
            # Do not print errors with URL, account ID or token-derived values.
            raise RuntimeError("FINAM_READONLY_BINDING_FAILED_FOR_" + robot) from None
        finally:
            token = ""
        seen_accounts.add(account_id)
        seen_token_digests.add(digest)
        results.append({
            "robot": robot,
            "status": "PASS_READONLY",
            "account_sha256": _fingerprint(account_id),
            "session_readonly": True,
            "requests": [x["resource"] for x in api.request_shapes],
        })
        print("BINDING_" + robot + "=PASS_READONLY")
    if len(results) != 3 or len(seen_accounts) != 3 or len(seen_token_digests) != 3:
        raise RuntimeError("THREE_INDEPENDENT_BINDINGS_NOT_CONFIRMED")

    # Report never contains tokens, account IDs, account state or raw FINAM responses.
    receipt = {
        "schema": "v20.finam.account_bindings_readonly.v1",
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS_3_OF_3",
        "no_orders_or_cancellations": True,
        "source": "H1 ReadonlyFillAPI in V20 pinned offline source",
        "results": results,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    if REPORT.exists():
        raise RuntimeError("EXISTING_BINDING_RECEIPT_NOT_OVERWRITTEN")
    REPORT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("V20_06_1_FINAM_READONLY=PASS_3_OF_3")
    print("V20_06_1_REPORT=" + str(REPORT))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--connect", action="store_true")
    args = parser.parse_args()
    try:
        if args.self_test:
            _self_test()
            return 0
        _self_test()  # refuse broker contact if H1 readonly guard fails
        return _connect()
    except (RuntimeError, AssertionError) as exc:
        # All explicit error codes are fixed and contain no secrets.
        print("V20_06_1_FAIL=" + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
