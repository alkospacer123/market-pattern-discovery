"""Dependency-free transport for the authenticated FINAM Trade API v1 schema.

Bars carry their documented *opening* timestamp.  ``completed_h1_bars`` turns
that into the close timestamp used by Stage 7 and rejects the still-open bar.
"""
from __future__ import annotations
import json, logging, threading, time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

LOG=logging.getLogger(__name__)
SESSION_PATH="/v1/sessions"
SESSION_DETAILS_PATH="/v1/sessions/details"
BARS_PATH_TEMPLATE="/v1/instruments/{symbol}/bars"
ACTIVE_ASSETS_PATH="/v1/assets/all"
ACTIVE_ASSETS_PAGE_SAFETY_CEILING=10000
H1_TIMEFRAME="TIME_FRAME_H1"
ORDER_SIDE_BUY="SIDE_BUY"; ORDER_SIDE_SELL="SIDE_SELL"
MARKET_ORDER_TYPE="ORDER_TYPE_MARKET"
CLIENT_ORDER_ID_MAX_LENGTH=20
CLIENT_ORDER_ID_CHARACTERS="ASCII alphanumeric"

class FinamError(RuntimeError): pass
class FinamAuthenticationError(FinamError): pass
class FinamNotFound(FinamError): pass
class FinamRateLimit(FinamError): pass
class FinamServerError(FinamError): pass
class FinamTimeout(FinamError): pass
class FinamUncertainSubmission(FinamError): pass
@dataclass(frozen=True)
class Response: status:int; body:Any; request_id:str|None

class RateLimiter:
    """Process-wide 180/min limiter: a margin below FINAM's documented 200/min."""
    _lock=threading.Lock(); _last=0.0
    def __init__(self,requests_per_minute:int=180):
        if not 1<=requests_per_minute<200: raise ValueError("LIMIT_MUST_BE_BELOW_200")
        self.interval=60/requests_per_minute
    def wait(self):
        with self._lock:
            delay=max(0,self._last+self.interval-time.monotonic())
            if delay: time.sleep(delay)
            type(self)._last=time.monotonic()

class FinamAPI:
    BASE_URL="https://api.finam.ru"; RATE_LIMIT_AUTHORITY="200 requests/minute"
    def __init__(self,secret:str,timeout:float=10,transport:Callable|None=None,limiter:RateLimiter|None=None):
        if not secret: raise FinamAuthenticationError("FINAM_API_SECRET_MISSING")
        self.__secret=secret; self.__jwt=None; self.timeout=timeout
        self.transport=transport or urlopen; self.limiter=limiter or RateLimiter()
    def __repr__(self): return "FinamAPI(secret=<redacted>, jwt=<redacted>)"
    def create_session(self):
        response=self._request("POST",SESSION_PATH,{"secret":self.__secret},auth=False,retries=1)
        token=response.body.get("token")
        if not token: raise FinamAuthenticationError("SESSION_RESPONSE_TOKEN_MISSING")
        self.__jwt=str(token)
        return {k:v for k,v in response.body.items() if k!="token"}
    def _request(self,method,path,payload=None,auth=True,retries=2)->Response:
        if auth and not self.__jwt: self.create_session()
        body=None if payload is None else json.dumps(payload,separators=(",",":")).encode()
        headers={"Accept":"application/json","Content-Type":"application/json"}
        if auth: headers["Authorization"]="Bearer "+self.__jwt
        for attempt in range(retries+1):
            self.limiter.wait(); req=Request(self.BASE_URL+path,data=body,headers=headers,method=method)
            try:
                raw=self.transport(req,timeout=self.timeout); data=raw.read()
                return Response(getattr(raw,"status",200),json.loads(data) if data else {},raw.headers.get("x-request-id"))
            except HTTPError as exc:
                request_id=exc.headers.get("x-request-id") if exc.headers else None
                LOG.warning("FINAM HTTP status=%s request_id=%s path=%s",exc.code,request_id,path)
                if exc.code==401 and auth and attempt==0:
                    self.__jwt=None; self.create_session(); headers["Authorization"]="Bearer "+self.__jwt; continue
                if exc.code==404: raise FinamNotFound(path) from None
                if exc.code==429 and attempt<retries: time.sleep(min(2**attempt,2)); continue
                if exc.code==429: raise FinamRateLimit(path) from None
                if exc.code>=500 and method=="GET" and attempt<retries: continue
                if exc.code>=500: raise FinamServerError(f"HTTP_{exc.code}:{path}") from None
                raise FinamError(f"HTTP_{exc.code}:{path}") from None
            except (TimeoutError,URLError):
                if method=="POST" and path.endswith("/orders"): raise FinamUncertainSubmission("RECONCILIATION_REQUIRED") from None
                if method=="GET" and attempt<retries: continue
                raise FinamTimeout(path) from None
        raise AssertionError("unreachable")
    def session_details(self):
        if not self.__jwt: self.create_session()
        # This endpoint is exceptional: FINAM requires the JWT in the JSON body.
        return self._request("POST",SESSION_DETAILS_PATH,{"token":self.__jwt},auth=False).body
    def account(self,account_id): return self._request("GET",f"/v1/accounts/{account_id}").body
    def orders(self,account_id): return self._request("GET",f"/v1/accounts/{account_id}/orders").body
    def order(self,account_id,order_id): return self._request("GET",f"/v1/accounts/{account_id}/orders/{order_id}").body
    def place_order(self,account_id,payload): return self._request("POST",f"/v1/accounts/{account_id}/orders",payload,retries=0).body
    def cancel_order(self,account_id,order_id): return self._request("DELETE",f"/v1/accounts/{account_id}/orders/{order_id}").body
    def assets(self): return self._request("GET","/v1/assets").body
    def assets_all_active(self):
        """Return the complete active REST catalog, failing closed on pagination faults.

        The ceiling is only an abnormal-loop guard.  It must never turn a partial
        catalog into apparently successful discovery.
        """
        assets=[]; cursor=None; seen=set()
        for _ in range(ACTIVE_ASSETS_PAGE_SAFETY_CEILING):
            query={"only_active":"true"}
            if cursor is not None: query["cursor"]=cursor
            page=self._request("GET",ACTIVE_ASSETS_PATH+"?"+urlencode(query)).body
            if not isinstance(page,dict): raise FinamError("ACTIVE_ASSETS_PAGE_NOT_OBJECT")
            rows=page.get("assets")
            if not isinstance(rows,list) or any(not isinstance(row,dict) for row in rows):
                raise FinamError("ACTIVE_ASSETS_PAYLOAD_MALFORMED")
            assets.extend(rows)
            next_cursor=page.get("next_cursor")
            if next_cursor is None or next_cursor=="" or (type(next_cursor) is int and next_cursor==0):
                return assets
            if (isinstance(next_cursor,str) and next_cursor.strip()==next_cursor and next_cursor
                    or type(next_cursor) is int and next_cursor>0):
                marker=(type(next_cursor).__name__,next_cursor)
            else: raise FinamError("ACTIVE_ASSETS_CURSOR_MALFORMED")
            if marker in seen: raise FinamError("ACTIVE_ASSETS_CURSOR_REPEATED")
            seen.add(marker); cursor=next_cursor
        raise FinamError("ACTIVE_ASSETS_PAGINATION_SAFETY_CEILING")
    def asset(self,symbol,account_id):
        if not account_id: raise ValueError("ACCOUNT_ID_REQUIRED")
        return self._request("GET",f"/v1/assets/{symbol}?{urlencode({'account_id':account_id})}").body
    def asset_params(self,symbol,account_id):
        if not account_id: raise ValueError("ACCOUNT_ID_REQUIRED")
        return self._request("GET",f"/v1/assets/{symbol}/params?{urlencode({'account_id':account_id})}").body
    def schedule(self,symbol): return self._request("GET",f"/v1/assets/{symbol}/schedule").body
    def bars(self,symbol,start,end):
        query={"timeframe":H1_TIMEFRAME,"interval.start_time":start,"interval.end_time":end}
        return self._request("GET",BARS_PATH_TEMPLATE.format(symbol=symbol)+"?"+urlencode(query)).body

def completed_h1_bars(response:dict,observed_at:datetime)->list[dict]:
    """Normalize documented bar-open ``timestamp`` to a completed close time."""
    now=observed_at.astimezone(timezone.utc); result=[]
    for bar in response.get("bars",[]):
        opened=datetime.fromisoformat(bar["timestamp"].replace("Z","+00:00"))
        closed=opened+timedelta(hours=1)
        if closed<=now: result.append({**bar,"open_timestamp":opened.isoformat(),"timestamp":closed.isoformat()})
    return result
