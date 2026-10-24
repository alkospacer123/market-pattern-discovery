"""V20-08.1 common one-shot FINAM read-side worker for 3 independent robots.

No broker order route is reachable. This is an H1 FINAM API connector and a
bounded current-M15 Open witness, NOT a LIVE strategy/order service.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import os
import re
import sys
from urllib.parse import parse_qs, urlparse, urlencode
from zoneinfo import ZoneInfo

from TradingSystemLab.stage8_robot.finam_api import (
    BARS_PATH_TEMPLATE, FinamAPI, SESSION_PATH, SESSION_DETAILS_PATH,
)
from TradingSystemLab.stage8_robot.production_runtime import _load_registry

from .finam_execution import (
    V20FinamBlocked, V20FinamReadAdapter, read_finam_m15_boundary,
)
from .h1_state_journal import ROBOT_STRATEGIES
from .offline_planner import N4


class ReadonlyWorkerAPI(FinamAPI):
    """H1 wire client with 08.1 request-level POST/DELETE denial."""

    def __init__(self, token: str, account_id: str, **kwargs):
        super().__init__(token, **kwargs)
        self.account_id = account_id

    def _request(self, method, path, payload=None, auth=True, retries=2):
        session = (
            method == "POST" and auth is False and isinstance(payload, dict)
            and (
                (path == SESSION_PATH and set(payload) == {"secret"})
                or (path == SESSION_DETAILS_PATH and set(payload) == {"token"})
            )
        )
        account_get = (
            method == "GET" and auth is True and payload is None
            and path in {f"/v1/accounts/{self.account_id}",
                         f"/v1/accounts/{self.account_id}/orders"}
        )
        bars_get = False
        if method == "GET" and auth is True and payload is None:
            url = urlparse(path)
            symbols = {_load_registry()[symbol]["finam_symbol"] for symbol in N4}
            routes = {BARS_PATH_TEMPLATE.format(symbol=sym) for sym in symbols}
            if url.path in routes and not url.fragment and not url.params:
                try:
                    query = parse_qs(url.query, strict_parsing=True)
                    if (set(query) == {"timeframe", "interval.start_time",
                                      "interval.end_time"}
                            and all(len(v) == 1 for v in query.values())
                            and query["timeframe"] == ["TIME_FRAME_M15"]):
                        start = datetime.fromisoformat(query["interval.start_time"][0])
                        end = datetime.fromisoformat(query["interval.end_time"][0])
                        now = datetime.now(timezone.utc)
                        bars_get = (
                            start.tzinfo is not None and end.tzinfo is not None
                            and timedelta(0) < end-start <= timedelta(days=30, minutes=15)
                            and now-timedelta(days=31) <= start.astimezone(timezone.utc)
                            and end.astimezone(timezone.utc) <= now+timedelta(minutes=16)
                        )
                except (ValueError, TypeError, OverflowError):
                    bars_get = False
        if not (session or account_get or bars_get):
            raise V20FinamBlocked("V20_WORKER_READONLY_DENIES_BROKER_WRITE")
        return super()._request(
            method, path, payload=payload, auth=auth, retries=retries,
        )



class AuthorityReadOnlyAPI(ReadonlyWorkerAPI):
    """Only the three existing H1 FINAM asset routes for the own N4 account."""

    def _request(self, method, path, payload=None, auth=True, retries=2):
        symbols = {_load_registry()[code]["finam_symbol"] for code in N4}
        extra = {
            f"/v1/assets/{symbol}?"+urlencode({"account_id": self.account_id})
            for symbol in symbols
        } | {
            f"/v1/assets/{symbol}/params?"+urlencode({"account_id": self.account_id})
            for symbol in symbols
        } | {f"/v1/assets/{symbol}/schedule" for symbol in symbols}
        if method == "GET" and auth is True and payload is None and path in extra:
            return FinamAPI._request(
                self, method, path, payload=payload, auth=auth, retries=retries,
            )
        return super()._request(
            method, path, payload=payload, auth=auth, retries=retries,
        )


def run_n4_authority(robot_id: str) -> dict:
    """Fresh N4 FINAM asset/params/schedule and H1 directional margin proof.

    This checks the *current* broker values against the previously verified
    MOEX tick price/tick value reference, not current NEXT_OPEN/fill/fees.
    """
    from TradingSystemLab.stage8_robot.instrument_resolver import (
        AUTHENTICATED, validate_finam_binding,
    )
    from TradingSystemLab.stage8_robot.margin import directional_initial_margin

    if robot_id not in ROBOT_STRATEGIES:
        raise V20FinamBlocked("WORKER_UNKNOWN_ROBOT")
    account = os.environ.get("V20_FINAM_ACCOUNT", "")
    secret = os.environ.get("V20_FINAM_TOKEN", "")
    account_hash = os.environ.get("V20_FINAM_ACCOUNT_SHA256", "")
    if (not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", account)
            or not secret or hashlib.sha256(account.encode()).hexdigest() != account_hash):
        raise V20FinamBlocked("WORKER_ACCOUNT_BINDING_MISSING_OR_INVALID")
    api = AuthorityReadOnlyAPI(secret, account)
    reader = V20FinamReadAdapter(
        api=api, robot_id=robot_id,
        account_id=account, expected_account_hash=account_hash,
    )
    reader.authenticate()
    snap = reader.snapshot(now=datetime.now(timezone.utc))
    if not snap.clean:
        return {"status": "HOLD_BROKER_NOT_FLAT_NEEDS_RECONCILIATION",
                "robot": robot_id, "instruments": {}, "orders": 0}
    result = {}
    registry = _load_registry()
    for symbol in sorted(N4):
        remote = registry[symbol]["finam_symbol"]
        asset = api.asset(remote, account)
        params = api.asset_params(remote, account)
        schedule = api.schedule(remote)
        evidence = validate_finam_binding(symbol, asset, params, schedule,
                                          account_asset=asset)
        go_long = directional_initial_margin(params, "LONG")
        go_short = directional_initial_margin(params, "SHORT")
        # FINAM step/lot bound to the validated MOEX/H1 specification.
        if evidence.status != AUTHENTICATED or go_long <= 0 or go_short <= 0:
            result[symbol] = "HOLD_FINAM_ASSET_OR_MARGIN_AUTHORITY"
        elif (Decimal(str(registry[symbol]["price_step"])) !=
              Decimal(str(evidence.moex_price_step))
              or Decimal(str(registry[symbol]["tick_value"])) !=
              Decimal(str(evidence.moex_tick_value))):
            result[symbol] = "HOLD_H1_TICK_VALUE_REGISTRY_CONFLICT"
        else:
            result[symbol] = "PASS"
    return {
        "status": "PASS_N4_AUTHORITY_4_OF_4" if
                  len(result) == 4 and all(x == "PASS" for x in result.values())
                  else "HOLD_N4_AUTHORITY",
        "robot": robot_id, "instruments": result, "orders": 0,
        "scope": "FRESH_ASSET_PARAMS_SCHEDULE_MARGIN_NOT_NEXT_OPEN_OR_TARIFF",
    }


def run_once(robot_id: str, *, witness: bool = False) -> dict:
    """One H1-account GET and orders GET, optionally FINAM new M15 Open."""
    if robot_id not in ROBOT_STRATEGIES:
        raise V20FinamBlocked("WORKER_UNKNOWN_ROBOT")
    account = os.environ.get("V20_FINAM_ACCOUNT", "")
    secret = os.environ.get("V20_FINAM_TOKEN", "")
    account_hash = os.environ.get("V20_FINAM_ACCOUNT_SHA256", "")
    if (not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", account)
            or not secret
            or hashlib.sha256(account.encode()).hexdigest() != account_hash):
        raise V20FinamBlocked("WORKER_ACCOUNT_BINDING_MISSING_OR_INVALID")
    api = ReadonlyWorkerAPI(secret, account)
    reader = V20FinamReadAdapter(
        api=api, robot_id=robot_id,
        account_id=account, expected_account_hash=account_hash,
    )
    reader.authenticate()
    now = datetime.now(timezone.utc)
    state = reader.snapshot(now=now)
    if not state.clean:
        return {
            "status": "HOLD_BROKER_NOT_FLAT_NEEDS_RECONCILIATION",
            "robot": robot_id, "orders": 0,
        }
    if not witness:
        return {"status": "PASS_ACCOUNT_GET_ONLY", "robot": robot_id, "orders": 0}
    # These are the ONLY instants at which a real NEXT_OPEN could be sent.
    msk = now.astimezone(ZoneInfo("Europe/Moscow"))
    if msk.minute % 15 or msk.second >= 60:
        return {"status": "NEXT_OPEN_NOT_IN_CURRENT_60_SECONDS",
                "robot": robot_id, "orders": 0}
    results = {}
    for symbol in sorted(N4):
        try:
            boundary = read_finam_m15_boundary(
                reader, symbol=symbol, from_utc=now-timedelta(hours=3),
                now=datetime.now(timezone.utc),
            )
            results[symbol] = (
                "PASS" if boundary.observed_at_utc - boundary.at_msk.replace(
                    tzinfo=ZoneInfo("Europe/Moscow")
                ).astimezone(timezone.utc) <= timedelta(seconds=60)
                else "HOLD_LATE"
            )
        except V20FinamBlocked as exc:
            # Only short internal error codes, no account or token.
            results[symbol] = str(exc)[:90] if re.fullmatch(
                r"[A-Z0-9_]{1,90}", str(exc)
            ) else "HOLD_BROKER_BAR_INVALID"
    return {
        "status": "PASS_NEXT_OPEN_4_OF_4" if
                  all(x == "PASS" for x in results.values())
                  else "HOLD_NEXT_OPEN_BROKER_WITNESS",
        "robot": robot_id, "results": results, "orders": 0,
    }


def self_test() -> int:
    """No network/token: prove GET target only, H1 auth and M15 allowlist."""
    from urllib.parse import urlencode
    seen = []

    class FakeResponse:
        status = 200
        headers = {}
        def read(self):
            return b"{}"

    def fake_transport(request, timeout):
        seen.append((request.get_method(), request.full_url))
        return FakeResponse()

    api = ReadonlyWorkerAPI(
        "SYNTHETIC_SECRET", "SYNTHETIC_ACCOUNT",
        transport=fake_transport,
    )
    api._FinamAPI__jwt = "SYNTHETIC_JWT"
    forbidden = (
        ("POST", "/v1/accounts/SYNTHETIC_ACCOUNT/orders"),
        ("POST", "/v1/accounts/SYNTHETIC_ACCOUNT/sltp-orders"),
        ("DELETE", "/v1/accounts/SYNTHETIC_ACCOUNT/orders/123"),
        ("GET", "/v1/accounts/FOREIGN_ACCOUNT"),
        ("GET", "/v1/assets/USDRUBF@RTSX/params?account_id=SYNTHETIC_ACCOUNT"),
        ("GET", "/v1/instruments/BR@RTSX/bars"),
    )
    for method, path in forbidden:
        try:
            api._request(method, path)
        except V20FinamBlocked:
            pass
        else:
            raise AssertionError("V20_08_1_READONLY_WRITE_OR_FOREIGN_READ_ALLOWED")
    if seen:
        raise AssertionError("V20_08_1_FORBIDDEN_HTTP_REACHED")
    api.account("SYNTHETIC_ACCOUNT")
    api.orders("SYNTHETIC_ACCOUNT")
    if len(seen) != 2 or any(row[0] != "GET" for row in seen):
        raise AssertionError("V20_08_1_ALLOWLIST_ACCOUNT_READ_FAILED")
    now = datetime.now(timezone.utc)
    symbol = _load_registry()["USDRUBF"]["finam_symbol"]
    query = urlencode({
        "timeframe": "TIME_FRAME_M15",
        "interval.start_time": (now - timedelta(hours=2)).isoformat(),
        "interval.end_time": (now + timedelta(minutes=15)).isoformat(),
    })
    api._request("GET", BARS_PATH_TEMPLATE.format(symbol=symbol) + "?" + query)
    if len(seen) != 3 or seen[-1][0] != "GET":
        raise AssertionError("V20_08_1_ALLOWLIST_M15_READ_FAILED")
    print("v20_08_1_finam_worker_selftest=pass_readonly_no_order")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--robot", choices=tuple(ROBOT_STRATEGIES))
    parser.add_argument("--witness-current-open", action="store_true")
    parser.add_argument("--authority", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        if args.self_test:
            return self_test()
        if args.robot is None:
            raise V20FinamBlocked("V20_WORKER_ROBOT_REQUIRED")
        result = (run_n4_authority(args.robot) if args.authority else
                  run_once(args.robot, witness=args.witness_current_open))
        print("v20_08_1_" + args.robot + "=" + result["status"])
        if "results" in result:
            for symbol, status in result["results"].items():
                print("v20_08_1_open_" + symbol.lower() + "=" + status)
        if "instruments" in result:
            for symbol, status in result["instruments"].items():
                print("v20_08_1_n4_" + symbol.lower() + "=" + status)
        print("v20_08_1_orders=zero")
        print("v20_08_1_live=off")
        # A missed time window is NOT a passed real-time Open witness.
        return 0 if result["status"].startswith("PASS") else 2
    except BaseException as exc:
        name = type(exc).__name__
        if isinstance(exc, V20FinamBlocked):
            code = str(exc)
            if re.fullmatch(r"[A-Z0-9_]{1,90}", code):
                name = code
        print("v20_08_1_finam_worker=BLOCKED_" + name, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
