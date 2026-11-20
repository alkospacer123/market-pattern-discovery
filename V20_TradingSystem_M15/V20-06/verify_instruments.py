"""V20-06.2: bounded N4 FINAM REAL_READONLY verification on URIU-PC.

Use pinned, unchanged H1 FinamAPI, ReadonlyFillAPI, instrument_resolver and margin.
No account IDs or token are saved. No order/SLTP/DELETE endpoint is reachable.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import logging
import re
from pathlib import Path
import sys
from urllib.parse import parse_qs, urlencode, urlsplit

BASE = Path(__file__).resolve().parents[1]
SOURCE = BASE / "source-raw"
BINDING = BASE / "readonly-06" / "ACCOUNT_BINDING_REPORT.json"
REPORT = BASE / "readonly-06" / "N4_SPECIFICATIONS_REPORT.json"
ROBOTS = ("v20-shallow", "v20-obv", "v20-inside")
SYMBOLS = {
    "USDRUBF": ("USDRUBF@RTSX", "3447194"),
    "CNYRUBF": ("CNYRUBF@RTSX", "3447192"),
    "GLDRUBF": ("GLDRUBF@RTSX", "4454911"),
    "IMOEXF": ("IMOEXF@RTSX", "4631091"),
}


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _utc(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("M15_TIMESTAMP_WITHOUT_TIMEZONE")
    return dt.astimezone(timezone.utc)


def _h1_modules():
    # Re-verify the exact H1 Git blobs installed by the V20-05.5 pinned-RAW bundle.
    # A Git blob hash is SHA1("blob <byte_length>\\0" + file_bytes).
    expected_blobs = {
        "finam_api.py": "a1126a7d2c618c19b5895f5c54da8e1ad73b339a",
        "finam_fill_price_readonly.py": "4b6d9b533058f31e70ef9e7a8068ea1fb6b83cc4",
        "instrument_resolver.py": "a174aee3fb4f5c68f2f00ff39a84527d9cd4642c",
        "margin.py": "80117ff6ea169305a7c22ee52a12e3e9103c9deb",
        "protective_stop_contract.py": "51a7ab88d2f64f969088d8ef04927383b7abc1aa",
    }
    for name, expected in expected_blobs.items():
        source_file = SOURCE / "TradingSystemLab/stage8_robot" / name
        if not source_file.is_file():
            raise RuntimeError("PINNED_H1_SOURCE_MISSING")
        raw = source_file.read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\x00" + raw).hexdigest()
        if actual != expected:
            raise RuntimeError("PINNED_H1_SOURCE_BLOB_MISMATCH")
    logging.getLogger("TradingSystemLab.stage8_robot.finam_api").setLevel(logging.CRITICAL)
    sys.path.insert(0, str(SOURCE))
    from TradingSystemLab.stage8_robot.finam_api import FinamAPI
    from TradingSystemLab.stage8_robot.finam_fill_price_readonly import ReadonlyFillAPI, FillDiagnosticBlocked
    from TradingSystemLab.stage8_robot.instrument_resolver import (
        N4, MOEX_REFERENCE, discover_finam_asset, validate_finam_binding,
    )
    from TradingSystemLab.stage8_robot.margin import directional_initial_margin
    from TradingSystemLab.stage8_robot.protective_stop_contract import QTY_MEASURE
    if tuple(N4) != tuple(SYMBOLS) or QTY_MEASURE != "SLTP_QTY_MEASURE_PERCENT":
        raise RuntimeError("H1_N4_OR_SLTP_CONTRACT_MISMATCH")
    return FinamAPI, ReadonlyFillAPI, FillDiagnosticBlocked, MOEX_REFERENCE, discover_finam_asset, validate_finam_binding, directional_initial_margin


def _extended_get(path: str, account_id: str, now: datetime) -> str | None:
    """Minimal GET-only allowlist beyond H1's bound-account reader."""
    parsed = urlsplit(path)
    if parsed.fragment or not parsed.path.startswith("/v1/") or not parsed.path:
        return None
    query = parse_qs(parsed.query, keep_blank_values=True, strict_parsing=bool(parsed.query))
    if parsed.path == "/v1/assets/all":
        if query.get("only_active") != ["true"] or set(query) - {"only_active", "cursor"}:
            return None
        if "cursor" in query and (len(query["cursor"]) != 1 or not 0 < len(query["cursor"][0]) <= 256):
            return None
        return "ACTIVE_ASSETS_READ"
    for instrument in SYMBOLS.values():
        symbol = instrument[0]
        if parsed.path in ("/v1/assets/" + symbol, "/v1/assets/" + symbol + "/params"):
            if parsed.query == urlencode({"account_id": account_id}):
                return "ACCOUNT_ASSET_READ" if parsed.path.endswith(symbol) else "ACCOUNT_ASSET_PARAMS_READ"
        if parsed.path == "/v1/assets/" + symbol + "/schedule" and not parsed.query:
            return "TRADING_SCHEDULE_READ"
        if parsed.path == "/v1/instruments/" + symbol + "/bars":
            if set(query) != {"timeframe", "interval.start_time", "interval.end_time"} or any(len(v) != 1 for v in query.values()):
                return None
            if query["timeframe"] != ["TIME_FRAME_M15"]:
                return None
            try:
                start = _utc(query["interval.start_time"][0])
                end = _utc(query["interval.end_time"][0])
            except (TypeError, ValueError):
                return None
            if not (now - timedelta(days=30) <= start < end <= now + timedelta(minutes=1)
                    and end-start <= timedelta(days=8)):
                return None
            return "M15_BARS_READ"
    return None


def _readonly_type():
    FinamAPI, ReadonlyFillAPI, Blocked, *_ = _h1_modules()
    class V20N4ReadonlyAPI(ReadonlyFillAPI):
        def _request(self, method, path, payload=None, auth=True, retries=0):
            if method == "POST" and path in {"/v1/sessions", "/v1/sessions/details"}:
                return super()._request(method, path, payload, auth, retries)
            if method == "GET" and self.bound and path == self.account_path and payload is None:
                return super()._request(method, path, payload, auth, retries)
            label = (_extended_get(path, self.account_id, datetime.now(timezone.utc))
                     if method == "GET" and self.bound and payload is None and auth is True else None)
            if label is None:
                raise Blocked("V20_READONLY_REQUEST_FORBIDDEN")
            self.request_shapes.append({"method": method, "resource": label})
            return FinamAPI._request(self, method, path, payload, auth, retries)
    return V20N4ReadonlyAPI, Blocked


def _bar_summary(data: dict, now: datetime) -> dict:
    from TradingSystemLab.stage8_robot.margin import parse_rest_decimal_value_object
    if not isinstance(data, dict) or not isinstance(data.get("bars"), list):
        raise ValueError("M15_RESPONSE_SCHEMA_INVALID")
    observed = []
    prior = None
    for row in data["bars"]:
        if not isinstance(row, dict):
            raise ValueError("M15_ROW_INVALID")
        t = _utc(row.get("timestamp"))
        if prior is not None and t <= prior:
            raise ValueError("M15_TIMESTAMP_ORDER_INVALID")
        prior = t
        values = [parse_rest_decimal_value_object(row.get(k)) for k in ("open", "high", "low", "close")]
        if min(values) <= 0 or values[1] < max(values[0], values[3]) or values[2] > min(values[0], values[3]):
            raise ValueError("M15_OHLC_INVALID")
        volume = parse_rest_decimal_value_object(row.get("volume"))
        if volume < 0 or t > now + timedelta(minutes=1):
            raise ValueError("M15_VOLUME_OR_FUTURE_TIMESTAMP_INVALID")
        # Only a schema observation. The timestamp open/close convention is
        # NOT inferred or allowed to authorize a NEXT_OPEN trading feed.
        if t <= now - timedelta(minutes=30):
            observed.append(t)
    if len(observed) < 10:
        raise ValueError("M15_OBSERVATIONS_INSUFFICIENT")
    return {"schema": "PASS", "completed_conservative_count": len(observed),
            "first_timestamp_utc": observed[0].isoformat(),
            "last_timestamp_utc": observed[-1].isoformat(),
            "timestamp_label_semantics": "UNVERIFIED_READONLY_NO_TRADING_FEED_AUTHORIZATION"}


def _receipt() -> dict:
    data = json.loads(BINDING.read_text(encoding="utf-8"))
    results = data.get("results")
    if (data.get("status") != "PASS_3_OF_3"
            or data.get("readonly_token_scope") != "ONE_SHARED_TOKEN_THREE_DISTINCT_ACCOUNTS"
            or not isinstance(results, list) or len(results) != 3
            or {x.get("robot") for x in results if isinstance(x, dict)} != set(ROBOTS)):
        raise RuntimeError("V20_06_1_RECEIPT_INVALID")
    return {row["robot"]: row["account_sha256"] for row in results}


def _self_test() -> None:
    api_cls, Blocked = _readonly_type()
    api = api_cls("offline-fake-secret", "demo-a")
    api.bound = True
    now = datetime.now(timezone.utc)
    sample_start = (now - timedelta(days=2)).isoformat()
    sample_end = (now - timedelta(hours=1)).isoformat()
    good = [
        "/v1/assets/all?only_active=true",
        "/v1/assets/USDRUBF@RTSX?account_id=demo-a",
        "/v1/assets/USDRUBF@RTSX/params?account_id=demo-a",
        "/v1/assets/USDRUBF@RTSX/schedule",
        "/v1/instruments/USDRUBF@RTSX/bars?" + urlencode({
            "timeframe": "TIME_FRAME_M15", "interval.start_time": sample_start,
            "interval.end_time": sample_end,
        }),
    ]
    if any(_extended_get(p, "demo-a", now) is None for p in good):
        raise RuntimeError("V20_06_2_ALLOWLIST_FALSE_REJECT")
    denied = [
        "/v1/accounts/demo-b",
        "/v1/accounts/demo-a/orders",
        "/v1/accounts/demo-a/trades?limit=5",
        "/v1/assets/USDRUBF@RTSX?account_id=demo-b",
        "/v1/assets/all?only_active=false",
        "/v1/instruments/USDRUBF@RTSX/bars?timeframe=TIME_FRAME_H1",
        "/v1/assets/CNYRUBF@RTSX/sltp-orders",
    ]
    if any(_extended_get(p, "demo-a", now) is not None for p in denied):
        raise RuntimeError("V20_06_2_ALLOWLIST_FALSE_ALLOW")
    for method, path in (("POST", "/v1/accounts/demo-a/orders"),
                         ("POST", "/v1/accounts/demo-a/sltp-orders"),
                         ("DELETE", "/v1/accounts/demo-a/orders/x"),
                         ("GET", "/v1/accounts/demo-b")):
        try:
            api._request(method, path)
        except Blocked:
            continue
        raise RuntimeError("V20_06_2_ORDER_OR_CROSS_ACCOUNT_GATE_FAILED")
    print("V20_06_2_OFFLINE_GET_ONLY_GATES=PASS")


def _connect() -> int:
    _, _, _, reference, discover, validate, margin = _h1_modules()
    api_cls, _ = _readonly_type()
    if REPORT.exists():
        raise RuntimeError("V20_06_2_REPORT_ALREADY_EXISTS_NO_OVERWRITE")
    if not (BASE / ".venv-raw/Scripts/python.exe").is_file():
        raise RuntimeError("V20_05_NATIVE_PYTHON_MISSING")
    expected = _receipt()
    accounts = {}
    for robot in ROBOTS:
        account = input("FINAM account_id for " + robot + " (visible; paste, Enter): ").strip()
        if (not account or len(account) > 128 or any(c in account for c in "/?#\r\n")
                or _sha(account) != expected[robot] or account in accounts.values()):
            raise RuntimeError("V20_06_1_ACCOUNT_IDENTITY_MISMATCH")
        accounts[robot] = account
    token = input("FINAM shared READONLY token (visible; paste, Enter): ").strip()
    if not token:
        raise RuntimeError("V20_READONLY_TOKEN_MISSING")
    now = datetime.now(timezone.utc)
    begin = (now-timedelta(days=7)).isoformat()
    end = (now-timedelta(minutes=1)).isoformat()
    result = {"schema": "v20.n4.readonly_specifications.v1", "utc": now.isoformat(),
              "06_1_receipt_sha256": hashlib.sha256(BINDING.read_bytes()).hexdigest(),
              "mode": "REAL_READONLY", "new_orders": 0, "cancellations": 0,
              "trading_authorized": False, "accounts": [], "symbols": {},
              "sltp": "H1_PERCENT_STOP_CONTRACT_PRESENT; FINAM_ACCOUNT_EXECUTION_UNVERIFIED_UNTIL_V20_08"}
    try:
        # H1 catalog pagination is reused, with a strict GET-only extension.
        first = api_cls(token, accounts[ROBOTS[0]])
        first.connect_readonly()
        all_assets = first.assets_all_active()
        catalog = {}
        for code, (name, security_id) in SYMBOLS.items():
            asset, issue = discover(code, all_assets)
            if issue or not isinstance(asset, dict) or asset.get("symbol") != name or str(asset.get("id")) != security_id:
                raise RuntimeError("N4_CATALOG_BINDING_FAILED_" + code)
            catalog[code] = asset
        for robot, account in accounts.items():
            api = first if robot == ROBOTS[0] else api_cls(token, account)
            if api is not first:
                api.connect_readonly()
            found = api.read_account()
            if not isinstance(found, dict) or str(found.get("account_id")) != account:
                raise RuntimeError("READONLY_ACCOUNT_RESPONSE_MISMATCH_" + robot)
            rows = {}
            for code, (symbol, identity) in SYMBOLS.items():
                asset = api.asset(symbol, account)
                params = api.asset_params(symbol, account)
                schedule = api.schedule(symbol)
                proof = validate(code, catalog[code], params, schedule, asset)
                if not proof.status.startswith("AUTHENTICATED_") or str(proof.security_id) != identity:
                    raise RuntimeError("N4_SPECIFICATION_NOT_VERIFIED_" + code)
                long_go, short_go = margin(params, "LONG"), margin(params, "SHORT")
                step, tick, size = reference[code]
                rows[code] = {"identity": symbol, "security_id": identity,
                              "price_step": str(step), "tick_value_rub_reference": str(tick),
                              "tick_value_authority": "H1_FROZEN_MOEX_REFERENCE_NOT_FINAM_PRICE_QUOTE",
                              "contract_size": str(size), "trade_lot_size": proof.trade_lot_size,
                              "tradable": proof.is_tradable, "go_long_rub": str(long_go),
                              "go_short_rub": str(short_go), "schedule": proof.schedule,
                              "binding": "PASS_READONLY"}
                if robot == ROBOTS[0]:
                    query = urlencode({"timeframe": "TIME_FRAME_M15",
                                       "interval.start_time": begin, "interval.end_time": end})
                    bars = api._request("GET", "/v1/instruments/" + symbol + "/bars?" + query).body
                    result["symbols"][code] = _bar_summary(bars, now)
            result["accounts"].append({"robot": robot, "account_sha256": _sha(account),
                                        "specifications": rows, "status": "PASS_4_OF_4"})
            print("V20_06_2_" + robot + "=PASS_4_OF_4")
    finally:
        token = ""
    result["status"] = "PASS_READONLY_3_ACCOUNTS_4_N4_WITH_SLTP_EXECUTION_DEFERRED"
    # Entire report remains on Intel; do not upload to public GitHub.
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with REPORT.open("x", encoding="utf-8") as output:
        json.dump(result, output, ensure_ascii=False, indent=2)
        output.write("\n")
    print("V20_06_2_FINAM_READONLY=PASS_3_X_4")
    print("V20_06_2_REPORT=" + str(REPORT))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--connect", action="store_true")
    args = parser.parse_args()
    try:
        _self_test()
        if args.self_test:
            return 0
        return _connect()
    except Exception as exc:
        # Print only predefined, all-caps local failure codes. Never echo H1
        # transport exception strings (they can include private account IDs).
        code = str(exc) if type(exc) in (RuntimeError, ValueError) else ""
        known = code if (re.fullmatch(r"[A-Z0-9_]{1,120}", code)
                         and code.startswith(("V20_", "N4_", "M15_", "READONLY_",
                                              "PINNED_", "H1_"))) else type(exc).__name__
        print("V20_06_2_FAIL=" + known, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
