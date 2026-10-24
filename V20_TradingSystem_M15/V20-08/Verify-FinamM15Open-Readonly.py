"""V20-08.1 one-shot FINAM M15 Open timestamp proof against FINAM H1 bars.

GET-only N4 historical comparison from the SAME FINAM account/session.
It does not authorize trading, call order endpoints, touch Tasks or H1 state.
No credential/account identifier or raw broker payload is persisted.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import argparse
from decimal import Decimal
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse
import hashlib
import json
import os
import re
import sys

ROOT = Path("C:/V20Lab")
SOURCE = ROOT / "source-raw"
RECEIPT = ROOT / "readonly-06" / "ACCOUNT_BINDING_REPORT.json"
OUTPUT = ROOT / "pretrade-08" / "M15_TIMESTAMP_PROOF.json"
N4 = ("USDRUBF@RTSX", "CNYRUBF@RTSX", "GLDRUBF@RTSX", "IMOEXF@RTSX")
H1_BLOBS = {
    "finam_api.py": "a1126a7d2c618c19b5895f5c54da8e1ad73b339a",
    "margin.py": "80117ff6ea169305a7c22ee52a12e3e9103c9deb",
}


class Blocked(RuntimeError):
    pass


def require(ok, code):
    if not ok:
        raise Blocked("V20_08_1_M15_" + code)


def decode_report(path):
    require(path.is_file() and not path.is_symlink(), "BINDING_MISSING")
    raw = path.read_bytes()
    try:
        if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
            obj = json.loads(raw.decode("utf-16"))
        else:
            obj = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeError, ValueError):
        raise Blocked("V20_08_1_M15_BINDING_JSON_INVALID") from None
    require(isinstance(obj, dict) and obj.get("status") == "PASS_3_OF_3",
            "BINDING_NOT_ACCEPTED")
    rows = obj.get("results")
    require(isinstance(rows, list) and len(rows) == 3,
            "BINDING_THREE_ACCOUNTS_REQUIRED")
    ids = [r.get("account_sha256") for r in rows if isinstance(r, dict)]
    require(len(ids) == 3 and len(set(ids)) == 3
            and all(isinstance(x, str) and re.fullmatch(r"[0-9a-f]{64}", x) for x in ids),
            "BINDING_ACCOUNT_HASHES_INVALID")
    return ids


def prepare_h1():
    require(os.name == "nt" and os.getenv("COMPUTERNAME", "").upper() == "URIU-PC",
            "PHYSICAL_INTEL_REQUIRED")
    require(not OUTPUT.exists(), "RESULT_ALREADY_EXISTS_NO_OVERWRITE")
    for path in (ROOT, SOURCE, OUTPUT.parent):
        require(path.is_dir() and not path.is_symlink(), "V20_DIRECTORY_INVALID")
    for name, expected in H1_BLOBS.items():
        path = SOURCE / "TradingSystemLab" / "stage8_robot" / name
        require(path.is_file() and not path.is_symlink(), "PINNED_H1_SOURCE_MISSING")
        data = path.read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\x00" + data).hexdigest()
        require(actual == expected, "PINNED_H1_SOURCE_MISMATCH")
    sys.path.insert(0, str(SOURCE))
    from TradingSystemLab.stage8_robot.finam_api import FinamAPI
    from TradingSystemLab.stage8_robot.margin import parse_rest_decimal_value_object
    return FinamAPI, parse_rest_decimal_value_object


def bounds(path, now):
    parsed = urlparse(path)
    if (parsed.fragment or parsed.params or parsed.path not in
            {"/v1/instruments/" + symbol + "/bars" for symbol in N4}):
        return False
    try:
        q = parse_qs(parsed.query, strict_parsing=True)
        if set(q) != {"timeframe", "interval.start_time", "interval.end_time"}:
            return False
        if any(len(v) != 1 for v in q.values()) or q["timeframe"][0] not in (
                "TIME_FRAME_M15", "TIME_FRAME_H1"):
            return False
        start = datetime.fromisoformat(q["interval.start_time"][0])
        end = datetime.fromisoformat(q["interval.end_time"][0])
        if start.tzinfo is None or end.tzinfo is None:
            return False
        start = start.astimezone(timezone.utc)
        end = end.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return False
    return (now - timedelta(days=8) <= start < end <= now
            and end-start <= timedelta(days=8))


def reader_type(h1_class):
    class M15ReadOnly(h1_class):
        def __init__(self, token, account):
            super().__init__(token)
            self.target = account
            self.bound = False

        def _request(self, method, path, payload=None, auth=True, retries=0):
            from TradingSystemLab.stage8_robot.finam_api import SESSION_PATH, SESSION_DETAILS_PATH
            authorization = (
                method == "POST" and auth is False and isinstance(payload, dict)
                and (
                    (path == SESSION_PATH and set(payload) == {"secret"})
                    or (path == SESSION_DETAILS_PATH and set(payload) == {"token"})
                )
            )
            allowed = (method == "GET" and self.bound and auth is True
                       and payload is None and bounds(path, datetime.now(timezone.utc)))
            if not (authorization or allowed):
                raise Blocked("V20_08_1_M15_NON_READONLY_REQUEST_REFUSED")
            return super()._request(method, path, payload=payload, auth=auth, retries=retries)

        def authenticate(self):
            self.create_session()
            details = self.session_details()
            require(isinstance(details, dict)
                    and details.get("readonly") is True
                    and isinstance(details.get("account_ids"), list)
                    and details["account_ids"].count(self.target) == 1,
                    "SINGLE_READONLY_ACCOUNT_SCOPE_REQUIRED")
            self.bound = True
    return M15ReadOnly


def read_bars(client, symbol, timeframe, start, end, decimal):
    query = urlencode({"timeframe": timeframe, "interval.start_time": start.isoformat(),
                       "interval.end_time": end.isoformat()})
    body = client._request("GET", f"/v1/instruments/{symbol}/bars?" + query).body
    require(isinstance(body, dict) and isinstance(body.get("bars"), list),
            "BROKER_BAR_RESPONSE_INVALID")
    result = {}
    previous = None
    for bar in body["bars"]:
        require(isinstance(bar, dict) and isinstance(bar.get("timestamp"), str),
                "BAR_ROW_INVALID")
        try:
            at = datetime.fromisoformat(bar["timestamp"].replace("Z", "+00:00"))
            require(at.tzinfo is not None, "BAR_TIMESTAMP_ZONE_INVALID")
            at = at.astimezone(timezone.utc)
            item = {field: decimal(bar.get(field), positive=True)
                    for field in ("open", "high", "low", "close")}
            if item["high"] < max(item["open"], item["close"]) or item["low"] > min(
                    item["open"], item["close"]):
                raise Blocked("V20_08_1_M15_BAR_OHLC_INVALID")
            require(start <= at < end and (previous is None or previous < at),
                    "BAR_TIME_DUPLICATE_OR_RANGE_INVALID")
        except (ValueError, TypeError, KeyError) as exc:
            raise Blocked("V20_08_1_M15_BAR_SCHEMA_INVALID") from exc
        result[at] = item
        previous = at
    return result


def compare(m15, h1, cutoff):
    matching = 0
    different = 0
    examples = []
    for at, hour in h1.items():
        if at + timedelta(hours=1) > cutoff:
            continue
        intervals = [at + timedelta(minutes=15*k) for k in range(4)]
        if any(t not in m15 for t in intervals):
            continue
        candles = [m15[t] for t in intervals]
        expected = {"open": candles[0]["open"],
                    "high": max(v["high"] for v in candles),
                    "low": min(v["low"] for v in candles),
                    "close": candles[-1]["close"]}
        same = all(expected[k] == hour[k] for k in expected)
        matching += int(same)
        different += int(not same)
        if len(examples) < 3:
            examples.append({"timestamp_utc": at.isoformat(),
                             "m15_open_label_match_h1": same})
    return {"matched_full_hours": matching,
            "mismatched_full_hours": different,
            "examples": examples,
            "status": "PASS" if matching >= 3 and different == 0 else "HOLD"}


def connect():
    accounts = decode_report(RECEIPT)
    FinamAPI, decimal = prepare_h1()
    account = input("FINAM account id (one of the three, visible PowerShell): ").strip()
    require(bool(re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", account))
            and hashlib.sha256(account.encode()).hexdigest() in accounts,
            "ACCOUNT_NOT_IN_THREE_PREVIOUS_BINDINGS")
    token = input("FINAM READONLY token (visible PowerShell; no history logging): ").strip()
    require(bool(token), "READONLY_TOKEN_MISSING")
    client = reader_type(FinamAPI)(token, account)
    token = ""
    client.authenticate()
    now = datetime.now(timezone.utc)
    start = now-timedelta(days=7)
    # Older completed hours only. No need for live-market availability.
    end = now-timedelta(minutes=5)
    cutoff = now-timedelta(hours=2)
    results = {}
    for symbol in N4:
        m15 = read_bars(client, symbol, "TIME_FRAME_M15", start, end, decimal)
        h1 = read_bars(client, symbol, "TIME_FRAME_H1", start, end, decimal)
        results[symbol.split("@")[0]] = compare(m15, h1, cutoff)
        print("v20_08_1_" + symbol.split("@")[0].lower() + "_m15_h1=" +
              results[symbol.split("@")[0]]["status"]
              + " matched=" + str(results[symbol.split("@")[0]]["matched_full_hours"])
              + " mismatch=" + str(results[symbol.split("@")[0]]["mismatched_full_hours"]))
    all_pass = all(row["status"] == "PASS" for row in results.values())
    report = {
        "schema": "v20.08.1.finam_m15_open_label_readonly.v1",
        "status": "PASS_4_OF_4_M15_H1_OPEN_LABELS" if all_pass else "HOLD_REAL_M15_H1_MISMATCH",
        "source": "FINAM_GET_ONLY_MATCHING_ACCOUNT_AUTHORITY",
        "timestamp_utc": now.isoformat(),
        "account_sha256": hashlib.sha256(account.encode()).hexdigest(),
        "n4": results, "orders_sent": 0, "tasks_modified": False,
        "live_enabled": False,
        "scope": "HISTORICAL_OPEN_LABEL_SEMANTICS_ONLY_NOT_CURRENT_NEXT_OPEN_LATENCY",
    }
    with OUTPUT.open("x", encoding="utf-8") as out:
        json.dump(report, out, indent=2, ensure_ascii=False)
    print("v20_08_1_m15_timestamp_proof=" + report["status"])
    print("v20_08_1_report=" + str(OUTPUT))
    return 0 if all_pass else 2


def self_test():
    """Four small structural tests; no FINAM, credentials, report or Task reads."""
    now = datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)
    uri = ("/v1/instruments/USDRUBF@RTSX/bars?" + urlencode({
        "timeframe": "TIME_FRAME_M15",
        "interval.start_time": (now - timedelta(days=1)).isoformat(),
        "interval.end_time": (now - timedelta(minutes=5)).isoformat(),
    }))
    require(bounds(uri, now), "SELFTEST_N4_M15_GET")
    for bad in (
        uri.replace("TIME_FRAME_M15", "TIME_FRAME_M5"),
        uri.replace("USDRUBF@RTSX", "BR@RTSX"),
        uri + "&forbidden=1",
    ):
        require(not bounds(bad, now), "SELFTEST_READ_SCOPE")
    class FakeAPI:
        def __init__(self, secret):
            pass
        def _request(self, *args, **kwargs):
            raise AssertionError("SELFTEST_UNEXPECTED_HTTP")
    reader = reader_type(FakeAPI)("fake-token", "fake-account")
    for method, route in (
        ("POST", "/v1/accounts/fake-account/orders"),
        ("POST", "/v1/accounts/fake-account/sltp-orders"),
        ("DELETE", "/v1/accounts/fake-account/orders/1"),
        ("GET", uri),
    ):
        try:
            reader._request(method, route)
        except Blocked:
            pass
        else:
            raise AssertionError("SELFTEST_WRITE_OR_PREAUTH_READ")
    reader.bound = True
    for method, route in (
        ("POST", "/v1/accounts/fake-account/orders"),
        ("DELETE", "/v1/accounts/fake-account/orders/1"),
        ("GET", uri.replace("USDRUBF@RTSX", "BR@RTSX")),
    ):
        try:
            reader._request(method, route)
        except Blocked:
            pass
        else:
            raise AssertionError("SELFTEST_WRITE_OR_FOREIGN_SYMBOL")
    base = datetime(2026, 10, 23, 6, 0, tzinfo=timezone.utc)
    flat = {k: Decimal("85.0") for k in ("open", "high", "low", "close")}
    h1 = {base + timedelta(hours=i): flat.copy() for i in range(4)}
    m15 = {base + timedelta(minutes=15*i): flat.copy() for i in range(16)}
    require(compare(m15, h1, now)["status"] == "PASS", "SELFTEST_OPEN_LABEL")
    m15[base + timedelta(minutes=15)]["high"] = Decimal("86")
    require(compare(m15, h1, now)["status"] == "HOLD", "SELFTEST_MISMATCH_MUST_BLOCK")
    print("v20_08_1_m15_get_only_selftest=pass_4_of_4")
    print("v20_08_1_live=off")
    print("v20_08_1_orders=zero")
    return 0


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    mode = cli.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--connect", action="store_true")
    arg = cli.parse_args()
    return self_test() if arg.self_test else connect()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Blocked as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from None
