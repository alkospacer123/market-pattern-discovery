"""M15 FINAM REST GET-only port, adapted from audited H1 FinamAPI.

H1 source: TradingSystemLab/stage8_robot/finam_api.py (read-only reference).
Authentication uses the two official /v1/sessions POST endpoints only; after
that, exclusively GET account/orders/assets/schedule/bars endpoints.
There is deliberately NO place_order, place_sltp_order, cancel, submit,
trading capability, Windows token loader, or live M15 authorization.
No HTTP request is sent by constructing this object.
"""
from __future__ import annotations

import json
import re
import time
from datetime import datetime
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

TIMEFRAME_M15 = "TIME_FRAME_M15"
_FINAM_SYMBOL = re.compile(r"^[A-Za-z0-9._-]+@[A-Za-z0-9._-]+$")
_ACCOUNT_ID = re.compile(r"^[A-Za-z0-9._-]+$")


class M15FinamReadOnlyError(RuntimeError):
    pass


def _stamp(value: str) -> datetime:
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        raise M15FinamReadOnlyError("FINAM_INTERVAL_INVALID") from None
    if result.tzinfo is None or result.utcoffset() is None:
        raise M15FinamReadOnlyError("FINAM_INTERVAL_INVALID")
    return result


def _symbol(value: str) -> str:
    if not isinstance(value, str) or _FINAM_SYMBOL.fullmatch(value) is None:
        raise M15FinamReadOnlyError("FINAM_SYMBOL_INVALID")
    return value


def _account(value: str) -> str:
    if not isinstance(value, str) or _ACCOUNT_ID.fullmatch(value) is None:
        raise M15FinamReadOnlyError("FINAM_ACCOUNT_FORMAT_INVALID")
    return value


class M15FinamReadOnlyAPI:
    BASE_URL = "https://api.finam.ru"
    def __init__(
        self, *, secret: str, account_id: str, transport: Callable | None = None,
        timeout: float = 10.0, sleeper: Callable[[float], None] = time.sleep,
    ):
        if not isinstance(secret, str) or not secret:
            raise M15FinamReadOnlyError("M15_READONLY_TOKEN_REQUIRED")
        _account(account_id)
        if not 0 < timeout <= 120:
            raise M15FinamReadOnlyError("FINAM_TIMEOUT_INVALID")
        self.__secret = secret
        self.__jwt: str | None = None
        self.__account = account_id
        self.__bound = False
        self._transport = transport or urlopen
        self._timeout = float(timeout)
        self._sleeper = sleeper

    def __repr__(self) -> str:
        return "M15FinamReadOnlyAPI(secret=<redacted>, jwt=<redacted>)"

    @property
    def account_id(self) -> str:
        return self.__account

    @property
    def readonly_bound(self) -> bool:
        return self.__bound

    def _request(self, method: str, path: str, payload: dict | None = None) -> Any:
        allowed_auth = method == "POST" and path in ("/v1/sessions", "/v1/sessions/details")
        allowed_get = (
            method == "GET"
            and (
                path == f"/v1/accounts/{self.__account}"
                or path == f"/v1/accounts/{self.__account}/orders"
                or path.startswith(f"/v1/accounts/{self.__account}/trades?")
                or path.startswith("/v1/assets/")
                or path.startswith("/v1/instruments/")
            )
            and "/orders/" not in path
            and "/sltp-orders" not in path
        )
        if not allowed_auth and not allowed_get:
            raise M15FinamReadOnlyError("M15_FORBIDDEN_HTTP_OPERATION")
        if allowed_get and payload is not None:
            raise M15FinamReadOnlyError("M15_READONLY_GET_WITH_BODY_FORBIDDEN")
        if allowed_get and not self.__bound:
            raise M15FinamReadOnlyError("M15_READONLY_ACCOUNT_BINDING_REQUIRED")
        data = json.dumps(payload, separators=(",", ":")).encode() if payload is not None else None
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if allowed_get:
            if not self.__jwt:
                raise M15FinamReadOnlyError("M15_SESSION_REQUIRED")
            headers["Authorization"] = "Bearer " + self.__jwt
        req = Request(self.BASE_URL + path, headers=headers, data=data, method=method)
        # Read-only semantics are structural. Do not log URLs that contain account IDs.
        for attempt in range(2 if allowed_get else 1):
            try:
                response = self._transport(req, timeout=self._timeout)
                raw = response.read()
                if getattr(response, "status", 200) != 200:
                    raise M15FinamReadOnlyError("M15_FINAM_HTTP_NON200")
                return json.loads(raw) if raw else {}
            except HTTPError as exc:
                if allowed_get and exc.code in (429, 500, 502, 503, 504) and attempt == 0:
                    self._sleeper(1.0)
                    continue
                raise M15FinamReadOnlyError("M15_FINAM_HTTP_FAIL_CLOSED") from None
            except (TimeoutError, URLError, OSError, ValueError):
                if allowed_get and attempt == 0:
                    self._sleeper(1.0)
                    continue
                raise M15FinamReadOnlyError("M15_FINAM_TRANSPORT_OR_JSON_INVALID") from None
        raise AssertionError("unreachable")

    def connect_readonly(self) -> None:
        """Official session auth; refuse trading-capable or multi-account binding."""
        if self.__bound:
            raise M15FinamReadOnlyError("M15_SESSION_ALREADY_BOUND")
        auth = self._request("POST", "/v1/sessions", {"secret": self.__secret})
        if not isinstance(auth, dict) or not isinstance(auth.get("token"), str) or not auth["token"]:
            raise M15FinamReadOnlyError("M15_SESSION_TOKEN_INVALID")
        self.__jwt = auth["token"]
        # FINAM's SessionDetails requires JWT in JSON body, H1 confirmed.
        details = self._request("POST", "/v1/sessions/details", {"token": self.__jwt})
        if (
            not isinstance(details, dict)
            or details.get("readonly") is not True
            or details.get("account_ids") != [self.__account]
        ):
            self.__jwt = None
            raise M15FinamReadOnlyError("M15_READONLY_EXACT_ACCOUNT_NOT_PROVED")
        self.__bound = True

    def account(self, account_id: str) -> dict:
        if _account(account_id) != self.__account:
            raise M15FinamReadOnlyError("M15_CROSS_ACCOUNT_READ_FORBIDDEN")
        response = self._request("GET", f"/v1/accounts/{self.__account}")
        if not isinstance(response, dict):
            raise M15FinamReadOnlyError("M15_FINAM_ACCOUNT_SCHEMA_INVALID")
        return response

    def orders(self, account_id: str) -> dict:
        if _account(account_id) != self.__account:
            raise M15FinamReadOnlyError("M15_CROSS_ACCOUNT_READ_FORBIDDEN")
        response = self._request("GET", f"/v1/accounts/{self.__account}/orders")
        if not isinstance(response, dict):
            raise M15FinamReadOnlyError("M15_FINAM_ORDERS_SCHEMA_INVALID")
        return response

    def trades(self, account_id: str, *, start: str, end: str, limit: int = 1000) -> dict:
        """Exact-account FINAM GET-only trade history, no order/cancel capability.

        Unlike raw account/orders, trades require an explicit bounded interval.
        Missing broker fill evidence must never be replaced by guessed prices.
        """
        if _account(account_id) != self.__account:
            raise M15FinamReadOnlyError("M15_CROSS_ACCOUNT_READ_FORBIDDEN")
        begin = _stamp(start)
        finish = _stamp(end)
        if begin >= finish or type(limit) is not int or not 0 < limit <= 1000:
            raise M15FinamReadOnlyError("M15_TRADES_INTERVAL_OR_LIMIT_INVALID")
        query = urlencode({
            "limit": limit,
            "interval.start_time": start,
            "interval.end_time": end,
        })
        result = self._request("GET", f"/v1/accounts/{self.__account}/trades?{query}")
        if not isinstance(result, dict) or not isinstance(result.get("trades"), list):
            raise M15FinamReadOnlyError("M15_TRADES_SCHEMA_INVALID")
        return result

    def asset_params(self, symbol: str) -> dict:
        asset = quote(_symbol(symbol), safe="@")
        query = urlencode({"account_id": self.__account})
        result = self._request("GET", f"/v1/assets/{asset}/params?{query}")
        if not isinstance(result, dict):
            raise M15FinamReadOnlyError("M15_ASSET_PARAMS_SCHEMA_INVALID")
        return result

    def schedule(self, symbol: str) -> dict:
        asset = quote(_symbol(symbol), safe="@")
        result = self._request("GET", f"/v1/assets/{asset}/schedule")
        if not isinstance(result, dict):
            raise M15FinamReadOnlyError("M15_SCHEDULE_SCHEMA_INVALID")
        return result

    def bars_m15(self, symbol: str, start: str, end: str) -> dict:
        """Raw broker M15 Open-labelled bars: not yet converted to completed M15.

        Keep FINAM timestamps unchanged. Trading calendar and finalization must
        be independently proved before live feature evaluation.
        """
        asset = quote(_symbol(symbol), safe="@")
        if _stamp(start) >= _stamp(end):
            raise M15FinamReadOnlyError("FINAM_INTERVAL_INVALID")
        query = urlencode({
            "timeframe": TIMEFRAME_M15,
            "interval.start_time": start,
            "interval.end_time": end,
        })
        result = self._request("GET", f"/v1/instruments/{asset}/bars?{query}")
        if (not isinstance(result, dict) or result.get("symbol") != symbol
                or not isinstance(result.get("bars"), list)):
            raise M15FinamReadOnlyError("M15_BARS_SYMBOL_OR_SCHEMA_INVALID")
        return result
