"""V20-08.1: one-time GET-only proof for three independent FINAM trading tokens.

Uses the pinned H1 FINAM API / account-money / broker-state parsers unchanged.
Authentication POST is allowed; order POST, SLTP POST and DELETE are impossible.
Does NOT store a token/account ID, change a Task or authorize LIVE.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import sys
from urllib.parse import quote, urlencode

ROBOTS = ("v20-shallow", "v20-obv", "v20-inside")
N4_FINAM = ("USDRUBF@RTSX", "CNYRUBF@RTSX", "GLDRUBF@RTSX", "IMOEXF@RTSX")
SOURCE_SHA = "610109b736c53a5cc1025657291e272b1136b254"
BASE = Path("C:/V20Lab")
SOURCE = BASE / "source-raw"
BINDING = BASE / "readonly-06/ACCOUNT_BINDING_REPORT.json"
FUNDED = BASE / "readonly-06/BROKER_READONLY_REPORT_FUNDED.json"
STAGING = BASE / "staging-07/INTEL_STAGING_REPORT.json"
REPORT = BASE / "pretrade-08/TRADING_TOKEN_ACCOUNT_READONLY_REPORT.json"
EXPECTED_H1_GIT_BLOBS = {
    "finam_api.py": "a1126a7d2c618c19b5895f5c54da8e1ad73b339a",
    "margin.py": "80117ff6ea169305a7c22ee52a12e3e9103c9deb",
    "production_broker_state.py": "894321fc0d3101e75eea48f45ff3a26c0c0f58eb",
    "funding_margin_diagnostic.py": "5a61adf1cb2627518c3d72aacbce62ebc19abba7",
}


class ReadonlyBlocked(RuntimeError):
    pass


def need(ok, code):
    if not ok:
        raise ReadonlyBlocked("V20_08_1_" + code)


def sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest_id(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def get_report(path):
    need(path.is_file() and not path.is_symlink(), "PRIOR_RECEIPT_MISSING")
    return json.loads(path.read_text(encoding="utf-8"))


def local_authority():
    need(os.name == "nt" and os.environ.get("COMPUTERNAME", "").upper() == "URIU-PC",
         "EXPECTED_INTEL_WINDOWS_REQUIRED")
    for path in (BASE, SOURCE, BASE / "pretrade-08"):
        if path.exists():
            need(not path.is_symlink(), "V20_PATH_LINK_FORBIDDEN")
    need(not REPORT.exists(), "REPORT_ALREADY_EXISTS_NO_OVERWRITE")
    binding, funded, staging = (get_report(x) for x in (BINDING, FUNDED, STAGING))
    need(binding.get("status") == "PASS_3_OF_3"
         and binding.get("readonly_token_scope") == "ONE_SHARED_TOKEN_THREE_DISTINCT_ACCOUNTS",
         "BINDING_NOT_PASS")
    need(funded.get("schema") == "v20.finam.broker_readonly_report.v1"
         and funded.get("status") == "PASS_READONLY_3_OF_3"
         and funded.get("stage_06_status") == "PASS"
         and funded.get("entry_authorized") is False, "FUNDED_READONLY_NOT_PASS")
    need(staging.get("schema") == "v20.intel.stage07.staging_acceptance.v1"
         and staging.get("status") == "PASS_4_OF_4_STAGING_LIVE_OFF"
         and staging.get("source_commit") == SOURCE_SHA
         and staging.get("live_enabled") is False, "STAGING_07_NOT_PASS")
    entries = binding.get("results")
    rows = funded.get("accounts")
    need(isinstance(entries, list) and len(entries) == 3
         and isinstance(rows, list) and len(rows) == 3, "ACCOUNT_REPORT_COUNT_INVALID")
    bound = {}
    for robot in ROBOTS:
        a = [x for x in entries if isinstance(x, dict) and x.get("robot") == robot]
        c = [x for x in rows if isinstance(x, dict) and x.get("robot") == robot]
        need(len(a) == len(c) == 1 and a[0].get("status") == "PASS_READONLY"
             and c[0].get("readonly_result") == "PASS_READONLY"
             and c[0].get("money_status") == "PASS"
             and c[0].get("account_clean") is True
             and re.fullmatch(r"[0-9a-f]{64}", str(a[0].get("account_sha256", "")))
             and a[0]["account_sha256"] == c[0].get("account_sha256"),
             "ACCOUNT_RECEIPT_IDENTITY_INVALID")
        bound[robot] = a[0]["account_sha256"]
    need(len(set(bound.values())) == 3, "ACCOUNTS_NOT_INDEPENDENT")
    for name, blob in EXPECTED_H1_GIT_BLOBS.items():
        f = SOURCE / "TradingSystemLab/stage8_robot" / name
        need(f.is_file() and not f.is_symlink(), "PINNED_H1_SOURCE_MISSING")
        raw = f.read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\x00" + raw).hexdigest()
        need(actual == blob, "H1_SOURCE_BLOB_MISMATCH")
    sys.path.insert(0, str(SOURCE))
    logging.getLogger("TradingSystemLab.stage8_robot.finam_api").setLevel(logging.CRITICAL)
    return bound


def get_h1():
    from TradingSystemLab.stage8_robot.finam_api import (
        FinamAPI, SESSION_PATH, SESSION_DETAILS_PATH,
    )
    from TradingSystemLab.stage8_robot.margin import (
        portfolio_authority, parse_rest_decimal_value_object, AVAILABLE_CASH_SEMANTICS,
        directional_initial_margin,
    )
    from TradingSystemLab.stage8_robot.production_broker_state import (
        order_views, position_quantities,
    )
    from TradingSystemLab.stage8_robot.funding_margin_diagnostic import ACTIVE_ACCOUNT_STATUSES

    class AccountTradingGetOnly(FinamAPI):
        """Order-inert even when initialized with a genuine trading token."""
        def __init__(self, token, account_id, **kwargs):
            super().__init__(token, **kwargs)
            self.target_account = account_id
            self.target_path = "/v1/accounts/" + quote(account_id, safe="")
            self.bound = False

        def _request(self, method, path, payload=None, auth=True, retries=0):
            allowed_auth = (
                method == "POST" and auth is False
                and (
                    (path == SESSION_PATH and isinstance(payload, dict)
                     and set(payload) == {"secret"} and isinstance(payload["secret"], str))
                    or (path == SESSION_DETAILS_PATH and isinstance(payload, dict)
                        and set(payload) == {"token"} and isinstance(payload["token"], str))
                )
            )
            allowed_read = (
                method == "GET" and self.bound is True and auth is True
                and payload is None and
                (path in (self.target_path, self.target_path + "/orders")
                 or path in {
                     "/v1/assets/" + symbol + "/params?" +
                     urlencode({"account_id": self.target_account})
                     for symbol in N4_FINAM
                 })
            )
            if not (allowed_auth or allowed_read):
                raise ReadonlyBlocked("V20_08_1_FINAM_WRITE_OR_UNBOUND_READ_FORBIDDEN")
            return super()._request(method, path, payload=payload, auth=auth, retries=retries)

        def bind_trading(self):
            self.create_session()
            details = self.session_details()
            ids = details.get("account_ids") if isinstance(details, dict) else None
            if (not isinstance(details, dict) or details.get("readonly") is not False
                    or not isinstance(ids, list)
                    or [str(value) for value in ids].count(self.target_account) != 1):
                raise ReadonlyBlocked("V20_08_1_TRADING_TOKEN_ACCOUNT_SCOPE_INVALID")
            self.bound = True

        def read_account(self):
            return self.account(self.target_account)

        def read_orders(self):
            return self.orders(self.target_account)

        def read_n4_margins(self):
            # Fresh FINAM account-scoped directional GO via unchanged H1 parser.
            margins = {}
            for symbol in N4_FINAM:
                params = self.asset_params(symbol, self.target_account)
                margins[symbol.split("@", 1)[0]] = {
                    "long_rub": str(directional_initial_margin(params, "LONG")),
                    "short_rub": str(directional_initial_margin(params, "SHORT")),
                }
            if len(margins) != 4:
                raise ReadonlyBlocked("V20_08_1_N4_MARGIN_COUNT_INVALID")
            return margins

    return (AccountTradingGetOnly, portfolio_authority,
            parse_rest_decimal_value_object, position_quantities, order_views,
            ACTIVE_ACCOUNT_STATUSES, AVAILABLE_CASH_SEMANTICS)


def self_test():
    # Offline structural proof, deliberately no credentials and no HTTP.
    # The parent _request would attempt session setup if this guard failed.
    local_authority()
    Client, *_ = get_h1()
    client = Client("FAKE_TOKEN_SELF_TEST", "account-A")
    forbidden = (
        ("POST", "/v1/accounts/account-A/orders"),
        ("POST", "/v1/accounts/account-A/sltp-orders"),
        ("DELETE", "/v1/accounts/account-A/orders/o-1"),
        ("GET", "/v1/accounts/account-A"),
        ("GET", "/v1/accounts/account-B"),
        ("GET", "/v1/assets/BR@RTSX/params?account_id=account-A"),
        ("GET", "/v1/assets/USDRUBF@RTSX/params?account_id=account-B"),
    )
    for method, path in forbidden:
        try:
            client._request(method, path)
        except ReadonlyBlocked:
            pass
        else:
            raise AssertionError("WRITE_OR_UNBOUND_READ_GATE_BROKEN")
    client.bound = True
    for method, path in forbidden[:3] + forbidden[4:]:
        try:
            client._request(method, path)
        except ReadonlyBlocked:
            pass
        else:
            raise AssertionError("WRITE_OR_FOREIGN_READ_GATE_BROKEN")
    # Allowed asset-params GET is proven against fake HTTP, never the Internet.
    class FakeHTTP:
        status = 200
        headers = {}
        def read(self):
            return b"{}"

    calls = []
    def fake_transport(req, timeout):
        calls.append((req.get_method(), req.full_url))
        return FakeHTTP()
    client.transport = fake_transport
    client._FinamAPI__jwt = "OFFLINE_FAKE_JWT"
    assert client.asset_params("USDRUBF@RTSX", "account-A") == {}
    assert len(calls) == 1 and calls[0][0] == "GET"
    assert calls[0][1].endswith("/v1/assets/USDRUBF@RTSX/params?account_id=account-A")
    # Verify exact target-account authorization with a synthetic session;
    # no HTTP, secrets or FINAM access during this test.
    class SessionStub(Client):
        def create_session(self):
            return {}
        def session_details(self):
            return self.details

    for details, permitted in (
        ({"readonly": True, "account_ids": ["account-A"]}, False),
        ({"readonly": False, "account_ids": ["account-B"]}, False),
        ({"readonly": False, "account_ids": ["account-A"]}, True),
    ):
        stub = SessionStub("FAKE_TOKEN_SELF_TEST", "account-A")
        stub.details = details
        if permitted:
            stub.bind_trading()
            assert stub.bound is True
        else:
            try:
                stub.bind_trading()
            except ReadonlyBlocked:
                pass
            else:
                raise AssertionError("WRONG_TRADE_TOKEN_SCOPE_ACCEPTED")
    print("V20_08_1_OFFLINE_GET_ONLY_GATE=PASS")
    return 0


def connect():
    expected = local_authority()
    (Client, portfolio_authority, parse_decimal, position_quantities, order_views,
     active_statuses, cash_semantics) = get_h1()
    observed = []
    tokens_seen = set()
    for robot in ROBOTS:
        print("V20_08_1_BINDING_ROBOT=" + robot)
        account_id = input("FINAM account ID for " + robot + " (VISIBLE in PowerShell): ").strip()
        # FINAM account IDs are never serialized to the receipt.
        need(bool(re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", account_id)),
             "ACCOUNT_INPUT_INVALID")
        need(digest_id(account_id) == expected[robot], "ACCOUNT_ID_NOT_MATCHING_06")
        token = input("FINAM TRADING token for " + robot + " (VISIBLE in PowerShell): ").strip()
        need(bool(token), "TRADING_TOKEN_EMPTY")
        fingerprint = hashlib.sha256(token.encode("utf-8")).digest()
        need(fingerprint not in tokens_seen, "TRADING_TOKENS_MUST_BE_DISTINCT")
        tokens_seen.add(fingerprint)
        client = Client(token, account_id)
        # Never persist token or broker account ID, even on connection failure.
        token = ""
        client.bind_trading()
        account = client.read_account()
        need(isinstance(account, dict)
             and str(account.get("account_id")) == account_id
             and account.get("status") in active_statuses, "ACCOUNT_STATE_OR_ID_INVALID")
        broker_orders = order_views(client.read_orders())
        positions = position_quantities(account)
        active = [o for o in broker_orders if o.active]
        # Fresh GO for 4 instruments, per bound account; any unknown field blocks.
        margins_n4 = client.read_n4_margins()
        funds = portfolio_authority(account)
        equity = parse_decimal(account.get("equity"))
        unrealized = parse_decimal(account.get("unrealized_profit"))
        realized = equity - unrealized
        need(realized > 0 and funds.available_cash >= 0, "BROKER_MONEY_NOT_VALID")
        # Clean account is necessary but is NOT proof of zero V20 intents, SLTP
        # validity or the executable next-open risk for the first signal.
        clean = not positions and not active
        row = {
            "robot": robot,
            "account_sha256": expected[robot],
            "token_scope": "WRITE_CAPABLE_EXACT_TARGET_ENUMERATED",
            "token_distinct_from_other_two": True,
            "source": "FINAM_GET_ONLY_ON_TRADING_TOKEN",
            "money_read": "PASS",
            "broker_derived_realized_equity_rub": str(realized),
            "available_cash_rub": str(funds.available_cash),
            "risk_budget_r15_rub": str(realized * Decimal("0.015")),
            "risk_budget_r6_rub": str(realized * Decimal("0.06")),
            "cash_semantics": cash_semantics,
            "positions_nonzero": len(positions),
            "active_orders": len(active),
            "fresh_n4_directional_go_rub": margins_n4,
            "n4_margin_status": "PASS_4_OF_4",
            "account_clean": clean,
            "eligible_for_real_order": False,
            "pending_gates": [
                "FRESH_N4_STEP_TICK_LOT_AND_TARIFF_VALIDATION",
                "ACTUAL_FROZEN_SIGNAL_AND_NEXT_OPEN",
                "EXECUTABLE_STOP_AND_R15_R6",
                "H1_REAL_BROKER_EXECUTOR_RECOVERY_SLTP",
                "V20_DURABLE_INTENT_RECONCILIATION",
                "SEPARATE_USER_AUTHORIZATION",
            ],
        }
        observed.append(row)
        print("V20_08_1_" + robot + "=GET_ONLY_" +
              ("PASS" if clean else "HOLD_ACCOUNT_NOT_CLEAN") +
              " MONEY=PASS POSITIONS=" + str(len(positions)) +
              " ACTIVE_ORDERS=" + str(len(active)) +
              " N4_GO=PASS_4_OF_4" +
              " R15_RUB=" + str(realized * Decimal("0.015")))
    need(len(observed) == 3 and len(tokens_seen) == 3, "TOKEN_OR_ACCOUNT_COUNT_INVALID")
    report = {
        "schema": "v20.finam.trading_tokens_get_only.v1",
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "binding_report_sha256": sha256(BINDING),
        "funded_report_sha256": sha256(FUNDED),
        "stage_07_report_sha256": sha256(STAGING),
        "status": "PASS_3_OF_3_GET_ONLY" if all(x["account_clean"] for x in observed)
                  else "HOLD_ACCOUNT_NOT_CLEAN",
        "stage_08_1": "IN_PROGRESS_NO_REAL_EXECUTOR_NO_ORDER_AUTHORIZATION",
        "trading_token_storage": "NOT_PERSISTED",
        "account_id_storage": "ONLY_SHA256_FROM_PREVIOUS_READONLY_BINDINGS",
        "finam_write_routes": "DISABLED_BY_GET_ONLY_REQUEST_GATE",
        "n4_margin_source": "FRESH_FINAM_ACCOUNT_ASSET_PARAMS_GET",
        "orders_sent": 0,
        "tasks_modified": False,
        "live_enabled": False,
        "accounts": observed,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with REPORT.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    print("V20_08_1_TRADING_TOKEN_GET_ONLY=" + report["status"])
    print("V20_08_1_STAGE=IN_PROGRESS_LIVE_NOT_AUTHORIZED")
    print("V20_08_1_REPORT=" + str(REPORT))
    return 0 if report["status"] == "PASS_3_OF_3_GET_ONLY" else 2


def main():
    cli = argparse.ArgumentParser(description="V20 08.1 GET-only trading token binding")
    choice = cli.add_mutually_exclusive_group(required=True)
    choice.add_argument("--self-test", action="store_true")
    choice.add_argument("--connect", action="store_true")
    args = cli.parse_args()
    try:
        return self_test() if args.self_test else connect()
    except Exception as exc:
        code = str(exc)
        if not isinstance(exc, ReadonlyBlocked) or not re.fullmatch(
            r"V20_08_1_[A-Z0-9_]{1,90}", code
        ):
            code = "V20_08_1_" + type(exc).__name__
        print("V20_08_1_BLOCKED=" + code, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
