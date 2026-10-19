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
from typing import Any, Callable

from .spec import EXECUTION_STATUS


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
        if not ((method == "POST" and path in
                 {"/v1/sessions", "/v1/sessions/details"})
                or (method == "GET" and self.__jwt is not None
                    and path == f"/v1/accounts/{self.__account}")
                or (self.__connected and (
                    method == "POST" and path in {
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
