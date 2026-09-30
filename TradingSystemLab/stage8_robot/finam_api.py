"""Minimal dependency-free FINAM Trade API v1 transport.

Authority: official Trade API paths under https://api.finam.ru.  Payloads are
kept as JSON dictionaries so authenticated operator diagnostics can preserve
new optional fields without weakening validation.
"""
from __future__ import annotations
import json, logging, threading, time
from dataclasses import dataclass
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

LOG=logging.getLogger(__name__)
class FinamError(RuntimeError): pass
class FinamAuthenticationError(FinamError): pass
class FinamNotFound(FinamError): pass
class FinamRateLimit(FinamError): pass
class FinamServerError(FinamError): pass
class FinamTimeout(FinamError): pass
class FinamUncertainSubmission(FinamError): pass

@dataclass(frozen=True)
class Response:
    status:int; body:Any; request_id:str|None

class RateLimiter:
    """Process-wide sliding interval limiter, deliberately below 200/min."""
    _lock=threading.Lock(); _last=0.0
    def __init__(self, requests_per_minute:int=180):
        if not 1 <= requests_per_minute < 200: raise ValueError("LIMIT_MUST_BE_BELOW_200")
        self.interval=60/requests_per_minute
    def wait(self):
        with self._lock:
            delay=max(0,self._last+self.interval-time.monotonic())
            if delay: time.sleep(delay)
            type(self)._last=time.monotonic()

class FinamAPI:
    BASE_URL="https://api.finam.ru"; API_VERSION="v1"; RATE_LIMIT_AUTHORITY="200 requests/minute"
    def __init__(self, secret:str, timeout:float=10, transport:Callable|None=None, limiter:RateLimiter|None=None):
        if not secret: raise FinamAuthenticationError("FINAM_API_SECRET_MISSING")
        self.__secret=secret; self.__jwt=None; self.timeout=timeout; self.transport=transport or urlopen; self.limiter=limiter or RateLimiter()
    def __repr__(self): return "FinamAPI(secret=<redacted>, jwt=<redacted>)"
    def create_session(self):
        response=self._request("POST","/v1/sessions",{"secret":self.__secret},auth=False,retries=1)
        token=response.body.get("token") or response.body.get("jwt") or response.body.get("accessToken")
        if not token: raise FinamAuthenticationError("SESSION_RESPONSE_TOKEN_MISSING")
        self.__jwt=str(token); return {k:v for k,v in response.body.items() if k not in ("token","jwt","accessToken")}
    def _request(self,method,path,payload=None,auth=True,retries=2)->Response:
        if auth and not self.__jwt: self.create_session()
        body=None if payload is None else json.dumps(payload,separators=(",",":"),ensure_ascii=False).encode()
        headers={"Accept":"application/json","Content-Type":"application/json"}
        if auth: headers["Authorization"]="Bearer "+self.__jwt
        for attempt in range(retries+1):
            self.limiter.wait(); req=Request(self.BASE_URL+path,data=body,headers=headers,method=method)
            try:
                raw=self.transport(req,timeout=self.timeout); data=raw.read(); parsed=json.loads(data) if data else {}
                return Response(getattr(raw,"status",200),parsed,raw.headers.get("x-request-id"))
            except HTTPError as exc:
                request_id=exc.headers.get("x-request-id") if exc.headers else None
                LOG.warning("FINAM HTTP status=%s request_id=%s path=%s",exc.code,request_id,path)
                if exc.code==401 and auth and attempt==0:
                    self.__jwt=None; self.create_session(); headers["Authorization"]="Bearer "+self.__jwt; continue
                if exc.code==404: raise FinamNotFound(path) from None
                if exc.code==429:
                    if attempt<retries: time.sleep(min(2**attempt,2)); continue
                    raise FinamRateLimit(path) from None
                if exc.code>=500 and method=="GET" and attempt<retries: time.sleep(.1*2**attempt); continue
                if exc.code>=500: raise FinamServerError(f"HTTP_{exc.code}:{path}") from None
                raise FinamError(f"HTTP_{exc.code}:{path}") from None
            except (TimeoutError,URLError) as exc:
                if method=="POST" and path.endswith("/orders"): raise FinamUncertainSubmission("RECONCILIATION_REQUIRED") from None
                if method=="GET" and attempt<retries: continue
                raise FinamTimeout(path) from None
        raise AssertionError("unreachable")
    def session_details(self): return self._request("GET","/v1/sessions").body
    def account(self,account_id): return self._request("GET",f"/v1/accounts/{account_id}").body
    def orders(self,account_id): return self._request("GET",f"/v1/accounts/{account_id}/orders").body
    def order(self,account_id,order_id): return self._request("GET",f"/v1/accounts/{account_id}/orders/{order_id}").body
    def place_order(self,account_id,payload): return self._request("POST",f"/v1/accounts/{account_id}/orders",payload,retries=0).body
    def cancel_order(self,account_id,order_id): return self._request("DELETE",f"/v1/accounts/{account_id}/orders/{order_id}").body
    def assets(self,all_assets=False): return self._request("GET","/v1/assets/all" if all_assets else "/v1/assets").body
    def asset(self,symbol): return self._request("GET",f"/v1/assets/{symbol}").body
    def asset_params(self,symbol): return self._request("GET",f"/v1/assets/{symbol}/params").body
    def schedule(self,symbol): return self._request("GET",f"/v1/assets/{symbol}/schedule").body
    def candles(self,symbol,query):
        from urllib.parse import urlencode
        return self._request("GET",f"/v1/assets/{symbol}/candles?{urlencode(query)}").body
