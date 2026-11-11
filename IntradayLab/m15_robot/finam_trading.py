"""Isolated M15 FINAM Trade API v1 write-capable wire, adapted from H1 FinamAPI.

No H1 import, shared global client, credentials, runtime, order or Task access.
The static M15 NOT_LIVE_AUTHORIZED freeze blocks CONSTRUCTION of this client
before even obtaining a FINAM session. Order POST is never retried.
The execution controller must separately validate durable intent and exact
broker protection; this low-level wire never authorizes business actions.
"""
from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlencode, parse_qs, urlsplit, quote
from datetime import timedelta
from typing import Any, Callable

from .spec import EXECUTION_STATUS, INSTRUMENTS
from .finam_readonly import _stamp

# Separate reviewed code-release gate. Changing spec alone NEVER releases POST.
M15_ORDER_POST_RELEASED = False


class M15FinamTradeError(RuntimeError):
    pass


class M15FinamTradeUncertain(M15FinamTradeError):
    """POST may have reached FINAM. Broker GET reconciliation is mandatory."""


class M15FinamTradeRejected(M15FinamTradeError):
    """Broker HTTP 400 rejection, never proof of a fill or a protection."""


class M15FinamTradingAPI:
    """M15-only H1-compatible order wire. CURRENT STATIC FREEZE REFUSES ALL USE."""

    BASE_URL = "https://api.finam.ru"

    def __init__(self, *, secret: str, account_id: str,
                 transport: Callable | None = None, timeout: float = 10):
        if EXECUTION_STATUS != "LIVE_AUTHORIZED":
            raise M15FinamTradeError("M15_TRADING_WIRE_STATIC_LIVE_FREEZE")
        if (not isinstance(secret, str) or not secret
                or not isinstance(account_id, str) or not account_id
                or account_id.strip() != account_id):
            raise M15FinamTradeError("M15_TRADING_WIRE_IDENTITY_INVALID")
        if type(timeout) not in (float, int) or not 0 < timeout <= 120:
            raise M15FinamTradeError("M15_TRADING_WIRE_TIMEOUT_INVALID")
        self.__secret = secret
        self.__jwt: str | None = None
        self.__account = account_id
        self.__connected = False
        self.transport = transport or urlopen
        self.timeout = float(timeout)

    def __repr__(self) -> str:
        return "M15FinamTradingAPI(secret=<redacted>, jwt=<redacted>)"

    def _request(self, method: str, path: str, payload: dict | None = None,
                 *, authenticated: bool = True) -> Any:
        if EXECUTION_STATUS != "LIVE_AUTHORIZED":
            raise M15FinamTradeError("M15_TRADING_WIRE_STATIC_LIVE_FREEZE")
        if (method == "POST" and path.endswith(("/orders", "/sltp-orders"))
                or method == "DELETE") and M15_ORDER_POST_RELEASED is not True:
            raise M15FinamTradeError("M15_TRADING_WIRE_ORDER_POST_RELEASE_NOT_APPROVED")
        symbols = tuple(name + "@RTSX" for name in INSTRUMENTS)
        query = urlencode({"account_id": self.__account})
        allowed_asset_get = {
            form for symbol in symbols for form in (
                f"/v1/assets/{symbol}?{query}",
                f"/v1/assets/{symbol}/params?{query}",
                f"/v1/assets/{symbol}/schedule",
            )
        }
        # Broker fill/cashflow history: GET-only, bounded, exact M15 account.
        # These endpoints share the SAME JWT as orders, needed for recovery.
        history_allowed = False
        if self.__connected and method == "GET":
            parsed = urlsplit(path)
            if (parsed.path in {
                    f"/v1/accounts/{self.__account}/trades",
                    f"/v1/accounts/{self.__account}/transactions"}
                    and not parsed.fragment):
                fields = parse_qs(parsed.query, keep_blank_values=True)
                if (set(fields) == {"limit", "interval.start_time",
                                   "interval.end_time"}
                        and all(len(values) == 1 for values in fields.values())):
                    try:
                        limit = int(fields["limit"][0])
                        if (str(limit) == fields["limit"][0] and 0 < limit <= 1000
                                and _stamp(fields["interval.start_time"][0])
                                < _stamp(fields["interval.end_time"][0])):
                            history_allowed = True
                    except (ValueError, TypeError, RuntimeError):
                        pass
        bars_allowed = False
        if self.__connected and method == "GET":
            parsed = urlsplit(path)
            if (not parsed.fragment and parsed.path in {
                    f"/v1/instruments/{quote(symbol, safe='@')}/bars"
                    for symbol in symbols}):
                fields = parse_qs(parsed.query, keep_blank_values=True)
                if (set(fields) == {"timeframe", "interval.start_time",
                                   "interval.end_time"}
                        and all(len(values) == 1 for values in fields.values())
                        and fields["timeframe"] == ["TIME_FRAME_M15"]):
                    try:
                        lower = _stamp(fields["interval.start_time"][0])
                        upper = _stamp(fields["interval.end_time"][0])
                        bars_allowed = lower < upper and upper - lower <= timedelta(days=30)
                    except (ValueError, TypeError, RuntimeError):
                        pass
        if not ((method == "POST" and path in
                 {"/v1/sessions", "/v1/sessions/details"})
                or (method == "GET" and self.__jwt is not None
                    and path == f"/v1/accounts/{self.__account}")
                or (self.__connected and (
                    method == "GET" and (
                        path == f"/v1/accounts/{self.__account}/orders"
                        or path in allowed_asset_get
                        or history_allowed
                        or bars_allowed)
                    or method == "POST" and path in {
                        f"/v1/accounts/{self.__account}/orders",
                        f"/v1/accounts/{self.__account}/sltp-orders"}
                    or method == "DELETE" and
                    path.startswith(f"/v1/accounts/{self.__account}/orders/")))):
            raise M15FinamTradeError("M15_TRADING_WIRE_PATH_FORBIDDEN")
        if authenticated and not self.__jwt:
            raise M15FinamTradeError("M15_TRADING_WIRE_SESSION_REQUIRED")
        if method == "GET" and payload is not None:
            raise M15FinamTradeError("M15_TRADING_WIRE_GET_BODY_INVALID")
        data = (None if payload is None else
                json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if authenticated:
            headers["Authorization"] = "Bearer " + self.__jwt
        req = Request(self.BASE_URL + path, data=data, headers=headers, method=method)
        is_order_post = method == "POST" and path.endswith(
            ("/orders", "/sltp-orders"))
        try:
            raw = self.transport(req, timeout=self.timeout)
            response = raw.read()
            status = getattr(raw, "status", 200)
            if status < 200 or status >= 300:
                if is_order_post and status == 400:
                    raise M15FinamTradeRejected("M15_TRADING_ORDER_HTTP_400")
                if is_order_post:
                    raise M15FinamTradeUncertain("M15_TRADING_POST_RECONCILIATION_REQUIRED")
                raise M15FinamTradeError("M15_TRADING_HTTP_NON_SUCCESS")
            body = json.loads(response) if response else {}
            if not isinstance(body, dict):
                raise M15FinamTradeError("M15_TRADING_RESPONSE_SCHEMA_INVALID")
            return body
        except HTTPError as exc:
            if is_order_post:
                if exc.code == 400:
                    raise M15FinamTradeRejected("M15_TRADING_ORDER_HTTP_400") from None
                raise M15FinamTradeUncertain("M15_TRADING_POST_RECONCILIATION_REQUIRED") from None
            raise M15FinamTradeError("M15_TRADING_HTTP_FAILURE") from None
        except (TimeoutError, URLError, OSError, ValueError):
            if is_order_post:
                raise M15FinamTradeUncertain("M15_TRADING_POST_RECONCILIATION_REQUIRED") from None
            raise M15FinamTradeError("M15_TRADING_TRANSPORT_FAILURE") from None

    def create_session(self) -> dict:
        result = self._request("POST", "/v1/sessions",
                               {"secret": self.__secret}, authenticated=False)
        token = result.get("token")
        if not isinstance(token, str) or not token:
            raise M15FinamTradeError("M15_TRADING_SESSION_TOKEN_MISSING")
        self.__jwt = token
        return {k: v for k, v in result.items() if k != "token"}

    def session_details(self) -> dict:
        if not self.__jwt:
            raise M15FinamTradeError("M15_TRADING_SESSION_REQUIRED")
        # Official FINAM session details POST places JWT in JSON body.
        return self._request("POST", "/v1/sessions/details",
                             {"token": self.__jwt}, authenticated=False)

    def account(self, account_id: str) -> dict:
        if account_id != self.__account:
            raise M15FinamTradeError("M15_CROSS_ACCOUNT_QUERY_FORBIDDEN")
        # Connecting may only be completed by the owning execution controller.
        return self._request("GET", f"/v1/accounts/{self.__account}")

    def _bind_exact_session(self, *, details: dict, account: dict) -> None:
        if (not isinstance(details, dict)
                or details.get("account_ids") != [self.__account]
                or details.get("readonly") is not False
                or not isinstance(account, dict)
                or account.get("account_id") != self.__account):
            raise M15FinamTradeError("M15_TRADING_EXACT_ACCOUNT_BINDING_INVALID")
        self.__connected = True

    def orders(self, account_id: str) -> dict:
        if account_id != self.__account or not self.__connected:
            raise M15FinamTradeError("M15_TRADING_ORDERS_ACCOUNT_NOT_BOUND")
        return self._request("GET", f"/v1/accounts/{self.__account}/orders")

    def _history(self, account_id: str, kind: str, *,
                 start: str, end: str, limit: int = 1000) -> dict:
        if (not self.__connected or account_id != self.__account
                or kind not in {"trades", "transactions"}
                or type(limit) is not int or not 0 < limit <= 1000):
            raise M15FinamTradeError("M15_TRADING_HISTORY_ACCOUNT_OR_LIMIT_INVALID")
        try:
            if _stamp(start) >= _stamp(end):
                raise ValueError("interval")
        except (ValueError, TypeError, RuntimeError):
            raise M15FinamTradeError("M15_TRADING_HISTORY_INTERVAL_INVALID") from None
        query = urlencode({
            "limit": limit, "interval.start_time": start, "interval.end_time": end,
        })
        result = self._request(
            "GET", f"/v1/accounts/{self.__account}/{kind}?{query}")
        if not isinstance(result, dict) or not isinstance(result.get(kind), list):
            raise M15FinamTradeError("M15_TRADING_HISTORY_SCHEMA_INVALID")
        return result

    def trades(self, account_id: str, *, start: str, end: str,
               limit: int = 1000) -> dict:
        """Bounded authenticated M15 fill evidence for restart reconciliation."""
        return self._history(account_id, "trades", start=start, end=end,
                             limit=limit)

    def transactions(self, account_id: str, *, start: str, end: str,
                     limit: int = 1000) -> dict:
        """Bounded authenticated M15 cashflow evidence for realized R15."""
        return self._history(account_id, "transactions", start=start, end=end,
                             limit=limit)

    def _asset_get(self, symbol: str, suffix: str = "", *,
                   account_bound: bool = True) -> dict:
        if not self.__connected or symbol not in {
            x + "@RTSX" for x in INSTRUMENTS}:
            raise M15FinamTradeError("M15_TRADING_ASSET_NOT_EXACT_N4_BOUND")
        query = "?" + urlencode({"account_id": self.__account}) if account_bound else ""
        return self._request("GET", f"/v1/assets/{symbol}{suffix}{query}")

    def asset_details(self, symbol: str) -> dict:
        return self._asset_get(symbol)

    def asset_params(self, symbol: str) -> dict:
        return self._asset_get(symbol, "/params")

    def schedule(self, symbol: str) -> dict:
        return self._asset_get(symbol, "/schedule", account_bound=False)

    def bars_m15(self, symbol: str, start: str, end: str) -> dict:
        """Same authenticated trading-session GET, no new JWT or order call."""
        if not self.__connected or symbol not in {
                name + "@RTSX" for name in INSTRUMENTS}:
            raise M15FinamTradeError("M15_TRADING_BARS_SYMBOL_OR_SESSION_INVALID")
        lower, upper = _stamp(start), _stamp(end)
        if not lower < upper or upper - lower > timedelta(days=30):
            raise M15FinamTradeError("M15_TRADING_BARS_INTERVAL_INVALID")
        query = urlencode({
            "timeframe": "TIME_FRAME_M15",
            "interval.start_time": start, "interval.end_time": end,
        })
        response = self._request(
            "GET", f"/v1/instruments/{quote(symbol, safe='@')}/bars?{query}")
        if (not isinstance(response, dict) or response.get("symbol") != symbol
                or not isinstance(response.get("bars"), list)):
            raise M15FinamTradeError("M15_TRADING_BARS_SCHEMA_INVALID")
        return response

    def place_order(self, account_id: str, payload: dict) -> dict:
        if account_id != self.__account or not self.__connected:
            raise M15FinamTradeError("M15_TRADING_ORDER_ACCOUNT_NOT_BOUND")
        return self._request("POST", f"/v1/accounts/{self.__account}/orders", payload)

    def place_sltp_order(self, account_id: str, payload: dict) -> dict:
        if account_id != self.__account or not self.__connected:
            raise M15FinamTradeError("M15_TRADING_STOP_ACCOUNT_NOT_BOUND")
        return self._request("POST", f"/v1/accounts/{self.__account}/sltp-orders", payload)

    def cancel_order(self, account_id: str, order_id: str) -> dict:
        if account_id != self.__account or not self.__connected:
            raise M15FinamTradeError("M15_TRADING_CANCEL_ACCOUNT_NOT_BOUND")
        if (not isinstance(order_id, str) or not order_id or "/" in order_id
                or "?" in order_id or "#" in order_id):
            raise M15FinamTradeError("M15_TRADING_CANCEL_ID_INVALID")
        return self._request(
            "DELETE", f"/v1/accounts/{self.__account}/orders/{order_id}")
