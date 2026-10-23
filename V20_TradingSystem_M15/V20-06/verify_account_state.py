"""V20-06.3: real account money, broker state and bounded fills, GET-only.

Run on URIU-PC with the existing pinned H1 modules, READONLY token and three
account IDs already attested in 06.1/06.2. No H1/M15 runtime or tasks opened.
A physical read-side observation is NOT a live trading authorization.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_FLOOR
import hashlib
import importlib.util
import json
import logging
from pathlib import Path
import re
import sys
from urllib.parse import parse_qs, urlsplit

BASE = Path(__file__).resolve().parents[1]
SCRATCH = BASE / "readonly-06"
PREVIOUS_SCRIPT = SCRATCH / "verify_instruments.py"
BINDINGS = SCRATCH / "ACCOUNT_BINDING_REPORT.json"
N4_REPORT = SCRATCH / "N4_SPECIFICATIONS_REPORT.json"
REPORT = SCRATCH / "ACCOUNT_STATE_REPORT.json"
ROBOTS = ("v20-shallow", "v20-obv", "v20-inside")
HISTORY_LIMIT = 400


def _digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _load_v20_06_2():
    if not PREVIOUS_SCRIPT.is_file():
        raise RuntimeError("V20_06_2_LOCAL_PINNED_SCRIPT_MISSING")
    raw = PREVIOUS_SCRIPT.read_bytes()
    actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\x00" + raw).hexdigest()
    if actual != "716c2a87f1d96d91bdc1b05ffd12738c8c2f7deb":
        raise RuntimeError("V20_06_2_SOURCE_HASH_MISMATCH")
    spec = importlib.util.spec_from_file_location("v20_06_2_readonly", PREVIOUS_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("V20_06_2_IMPORT_FAILED")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod._self_test()  # Existing GET-only gate must pass before any contact.
    return mod


def _verified_reports(mod):
    receipts = mod._receipt()  # 06.1 receipt: robot -> sha256(account_id).
    data = json.loads(N4_REPORT.read_text(encoding="utf-8"))
    if (data.get("schema") != "v20.n4.readonly_specifications.v1"
            or data.get("status") != "PASS_READONLY_3_ACCOUNTS_4_N4_WITH_SLTP_EXECUTION_DEFERRED"
            or data.get("06_1_receipt_sha256") != hashlib.sha256(BINDINGS.read_bytes()).hexdigest()
            or data.get("new_orders") != 0 or data.get("cancellations") != 0
            or data.get("trading_authorized") is not False):
        raise RuntimeError("V20_06_2_RECEIPT_NOT_PASS")
    rows = data.get("accounts")
    if (not isinstance(rows, list) or len(rows) != 3
            or {x.get("robot") for x in rows if isinstance(x, dict)} != set(ROBOTS)):
        raise RuntimeError("V20_06_2_ACCOUNT_SET_MISMATCH")
    specs = {}
    for item in rows:
        robot = item["robot"]
        if item.get("status") != "PASS_4_OF_4" or item.get("account_sha256") != receipts[robot]:
            raise RuntimeError("V20_06_2_ACCOUNT_IDENTITY_MISMATCH")
        part = item.get("specifications")
        if not isinstance(part, dict) or set(part) != set(mod.SYMBOLS):
            raise RuntimeError("V20_06_2_N4_INCOMPLETE")
        for code, values in part.items():
            if (not isinstance(values, dict)
                    or values.get("identity") != mod.SYMBOLS[code][0]
                    or str(values.get("security_id")) != mod.SYMBOLS[code][1]
                    or values.get("binding") != "PASS_READONLY"
                    or values.get("tradable") is not True):
                raise RuntimeError("V20_06_2_N4_IDENTITY_INVALID")
        specs[robot] = part
    return receipts, specs


def _api_type(mod):
    from TradingSystemLab.stage8_robot.finam_api import FinamAPI
    from TradingSystemLab.stage8_robot.finam_fill_price_readonly import (
        ReadonlyFillAPI, FillDiagnosticBlocked,
    )
    Base, _ = mod._readonly_type()

    class SnapshotReadonlyAPI(Base):
        def _request(self, method, path, payload=None, auth=True, retries=0):
            # The only newly permitted resources are this *bound* account's
            # current orders and a bounded recent fills interval.
            if method == "GET" and self.bound and payload is None and auth is True:
                if path == self.account_path + "/orders":
                    self.request_shapes.append({"method": method, "resource": "ACCOUNT_ORDERS_READ"})
                    return FinamAPI._request(self, method, path, payload, auth, retries)
                if urlsplit(path).path == self.account_path + "/trades" and not urlsplit(path).fragment:
                    try:
                        q = parse_qs(urlsplit(path).query, strict_parsing=True)
                        if set(q) != {"limit", "interval.start_time", "interval.end_time"}:
                            raise ValueError
                        if any(len(v) != 1 for v in q.values()) or q["limit"] != [str(HISTORY_LIMIT)]:
                            raise ValueError
                        start, end = mod._utc(q["interval.start_time"][0]), mod._utc(q["interval.end_time"][0])
                        now = datetime.now(timezone.utc)
                        if not (now - timedelta(days=4) <= start < end <= now + timedelta(minutes=1)
                                and end - start <= timedelta(days=3, minutes=1)):
                            raise ValueError
                    except (KeyError, ValueError, TypeError):
                        raise FillDiagnosticBlocked("V20_06_3_HISTORY_REQUEST_FORBIDDEN") from None
                    # Reuse unchanged H1 bounded-history request validation.
                    return ReadonlyFillAPI._request(self, method, path, payload, auth, retries)
            return super()._request(method, path, payload, auth, retries)

    return SnapshotReadonlyAPI, FillDiagnosticBlocked


def _self_test(mod):
    API, Blocked = _api_type(mod)
    observed = []
    class FakeResponse:
        status = 200
        headers = {}
        def read(self):
            return b'{"orders":[],"trades":[]}'
    def fake_transport(request, timeout):
        observed.append((request.get_method(), request.full_url))
        return FakeResponse()
    api = API("dummy-readonly", "demo-a", transport=fake_transport)
    api.bound = True
    valid_start = (datetime.now(timezone.utc)-timedelta(days=2)).isoformat()
    valid_end = (datetime.now(timezone.utc)-timedelta(minutes=2)).isoformat()
    response = api._request("GET", api.account_path + "/orders")
    if response.status != 200:
        raise RuntimeError("V20_06_3_ORDERS_GET_FAILED")
    api.read_history(valid_start, valid_end, HISTORY_LIMIT)
    if len(observed) != 2 or any(method != "GET" for method, _ in observed):
        raise RuntimeError("V20_06_3_GET_ALLOWLIST_FAILED")
    forbidden = (
        ("POST", api.account_path + "/orders"),
        ("POST", api.account_path + "/sltp-orders"),
        ("DELETE", api.account_path + "/orders/abc"),
        ("GET", "/v1/accounts/demo-b/orders"),
        ("GET", api.account_path + "/trades"),
        ("GET", api.account_path + "/trades?limit=999999"),
    )
    for method, url in forbidden:
        try:
            api._request(method, url)
        except Blocked:
            pass
        else:
            raise RuntimeError("V20_06_3_UNAUTHORIZED_TRANSPORT")
    if len(observed) != 2:
        raise RuntimeError("V20_06_3_FORBIDDEN_REQUEST_WAS_SENT")
    print("V20_06_3_GET_ONLY_BOUNDARIES=PASS")


def _money(account):
    from TradingSystemLab.stage8_robot.margin import portfolio_authority, parse_rest_decimal_value_object
    portfolio = portfolio_authority(account)
    equity = parse_rest_decimal_value_object(account.get("equity"))
    unrealized = parse_rest_decimal_value_object(account.get("unrealized_profit"))
    realized = equity - unrealized
    if equity <= 0 or realized <= 0 or portfolio.available_cash < 0:
        raise ValueError("V20_06_3_MONEY_NOT_FUNDED_OR_INVALID")
    return portfolio, equity, unrealized, realized


def _orders_and_positions(account, orders_data):
    from TradingSystemLab.stage8_robot.production_broker_state import position_quantities, order_views
    positions = position_quantities(account)
    orders = order_views(orders_data)
    active = [row for row in orders if row.active]
    return positions, orders, active


def _history_summary(data, account, start, end):
    if not isinstance(data, dict) or not isinstance(data.get("trades"), list):
        raise ValueError("V20_06_3_HISTORY_SCHEMA_INVALID")
    rows = data["trades"]
    if (len(rows) >= HISTORY_LIMIT
            or any(data.get(k) not in (None, "", 0) for k in ("next_cursor", "next_page_token"))):
        raise ValueError("V20_06_3_HISTORY_COVERAGE_INCOMPLETE")
    seen = set()
    for row in rows:
        if (not isinstance(row, dict) or row.get("account_id") != account
                or not isinstance(row.get("trade_id"), str) or not row["trade_id"]
                or not isinstance(row.get("order_id"), str) or not row["order_id"]):
            raise ValueError("V20_06_3_HISTORY_TRADE_IDENTITY_INVALID")
        if row["trade_id"] in seen:
            raise ValueError("V20_06_3_HISTORY_DUPLICATE_TRADE_ID")
        seen.add(row["trade_id"])
        t = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
        if t.tzinfo is None or not start <= t.astimezone(timezone.utc) < end:
            raise ValueError("V20_06_3_HISTORY_TIME_INVALID")
    return {"period_days": 3, "trades": len(rows),
            "coverage": "BOUNDED_3_DAYS_COMPLETE_BY_LIMIT_AND_CURSOR",
            "v20_live_fill_reconciliation": "NOT_APPLICABLE_PRE_LIVE"}


def _observe(api, robot, account, specs):
    from TradingSystemLab.stage8_robot.margin import margin_capacity
    account_data = api.read_account()
    if not isinstance(account_data, dict) or str(account_data.get("account_id")) != account:
        raise ValueError("V20_06_3_WRONG_ACCOUNT_RESPONSE")
    orders_data = api._request("GET", api.account_path + "/orders").body
    positions, orders, active = _orders_and_positions(account_data, orders_data)
    try:
        portfolio, equity, unrealized, realized = _money(account_data)
        money = {"status": "PASS", "equity_rub": str(equity),
                 "unrealized_rub": str(unrealized), "realized_equity_rub": str(realized),
                 "available_cash_rub": str(portfolio.available_cash),
                 "portfolio_variant": portfolio.variant,
                 "risk_budget_r15_rub": str(realized * Decimal("0.015")),
                 "account_max_initial_risk_r6_rub": str(realized * Decimal("0.06"))}
    except ValueError as exc:
        money = {"status": "BLOCKED", "reason": str(exc) if str(exc).startswith("V20_") else type(exc).__name__}
        portfolio = None
    capacity = {}
    for code, fields in specs.items():
        one = {}
        for side in ("long", "short"):
            go = Decimal(str(fields["go_" + side + "_rub"]))
            lot = Decimal(str(fields["trade_lot_size"]))
            if go <= 0 or lot <= 0 or lot != lot.to_integral_value():
                raise ValueError("V20_06_3_GO_OR_LOT_INVALID")
            one[side] = (int(margin_capacity(portfolio.available_cash, go, int(lot)))
                         if portfolio is not None else 0)
        capacity[code] = one
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=3)
    response = api.read_history(start.isoformat(), now.isoformat(), HISTORY_LIMIT)
    history = _history_summary(response, account, start, now)
    clean = not positions and not active
    # It is unsafe to claim final 1.5%-risk quantity without an actual
    # completed M15 signal, verified NEXT_OPEN entry and 2*ATR executable stop.
    return {"robot": robot, "account_sha256": _digest(account),
            "account_status": str(account_data.get("status", "UNKNOWN")),
            "money": money, "positions_nonzero": len(positions),
            "active_orders": len(active), "all_order_rows": len(orders),
            "account_clean": clean, "margin_only_capacity_contracts": capacity,
            "risk_sized_entry_contracts": "BLOCKED_UNTIL_SIGNAL_ENTRY_ATR_GRID_AND_COST",
            "history": history, "broker_state_observation": "PASS",
            "entry_ready": False,
            "entry_block_reason": "06_3_READONLY_ONLY_NO_LIVE"}


def _run():
    if REPORT.exists():
        raise RuntimeError("V20_06_3_REPORT_EXISTS_NO_OVERWRITE")
    mod = _load_v20_06_2()
    api_type, _ = _api_type(mod)
    _self_test(mod)
    receipts, specs = _verified_reports(mod)
    accounts = {}
    for robot in ROBOTS:
        value = input("FINAM account_id for " + robot + " (visible; paste Enter): ").strip()
        if (not value or len(value) > 128 or any(c in value for c in "/?#\r\n")
                or _digest(value) != receipts[robot] or value in accounts.values()):
            raise RuntimeError("V20_06_3_ACCOUNT_NOT_06_1_06_2_BOUND")
        accounts[robot] = value
    token = input("FINAM shared READONLY token (visible; paste Enter): ").strip()
    if not token:
        raise RuntimeError("V20_06_3_READONLY_TOKEN_MISSING")
    result = {"schema": "v20.finam.readonly_account_state.v1",
              "observed_at_utc": datetime.now(timezone.utc).isoformat(),
              "source_06_2_report_sha256": hashlib.sha256(N4_REPORT.read_bytes()).hexdigest(),
              "mode": "READONLY", "new_orders": 0, "cancellations": 0, "live_authorized": False,
              "accounts": []}
    try:
        for robot in ROBOTS:
            api = api_type(token, accounts[robot])
            api.connect_readonly()
            observation = _observe(api, robot, accounts[robot], specs[robot])
            result["accounts"].append(observation)
            label = ("PASS" if observation["money"]["status"] == "PASS"
                     and observation["account_clean"] else "PARTIAL")
            print("V20_06_3_" + robot + "=" + label + "_READONLY")
    finally:
        token = ""
    ok = (len(result["accounts"]) == 3 and
          all(x["money"]["status"] == "PASS" and x["account_clean"] and
              x["history"]["coverage"] == "BOUNDED_3_DAYS_COMPLETE_BY_LIMIT_AND_CURSOR"
              for x in result["accounts"]))
    result["status"] = "PASS_READONLY_3_OF_3" if ok else "PARTIAL_ACCOUNT_MONEY_OR_CLEANLINESS"
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with REPORT.open("x", encoding="utf-8") as output:
        json.dump(result, output, ensure_ascii=False, indent=2)
        output.write("\n")
    print("V20_06_3_FINAM_READONLY=" + result["status"])
    print("V20_06_3_REPORT=" + str(REPORT))
    return 0 if ok else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--connect", action="store_true")
    args = parser.parse_args()
    try:
        mod = _load_v20_06_2()
        _self_test(mod)
        if args.self_test:
            return 0
        return _run()
    except Exception as exc:
        # Never expose private FINAM account IDs, URLs, tokens or raw responses.
        value = str(exc)
        code = (value if type(exc) in (RuntimeError, ValueError)
                and re.fullmatch(r"V20_[A-Z0-9_]{1,100}", value) else type(exc).__name__)
        print("V20_06_3_FAIL=" + code, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
