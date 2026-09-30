"""Broker boundary and an inert FINAM Trade API foundation."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any

class OrderStatus(str,Enum):
    SIGNAL_CREATED="SIGNAL_CREATED"; INTENT_PERSISTED="INTENT_PERSISTED"; ORDER_SUBMITTED="ORDER_SUBMITTED"
    ACKNOWLEDGED="ACKNOWLEDGED"; PARTIALLY_FILLED="PARTIALLY_FILLED"; FILLED="FILLED"; POSITION_OPEN="POSITION_OPEN"
    EXIT_ORDER="EXIT_ORDER"; CLOSED="CLOSED"; REJECTED="REJECTED"; CANCELLED="CANCELLED"; EXPIRED="EXPIRED"
    UNKNOWN="UNKNOWN"; RECONCILIATION_REQUIRED="RECONCILIATION_REQUIRED"
@dataclass(frozen=True)
class OrderRequest:
    idempotency_key: str; contract_id: str; direction: str; quantity: int; order_type: str="MARKET"
class Broker(ABC):
    @abstractmethod
    def connect(self)->None: ...
    @abstractmethod
    def disconnect(self)->None: ...
    @abstractmethod
    def health(self)->dict: ...
    @abstractmethod
    def resolve_security(self, research_symbol:str)->dict: ...
    @abstractmethod
    def account(self)->dict: ...
    @abstractmethod
    def positions(self)->list[dict]: ...
    @abstractmethod
    def active_orders(self)->list[dict]: ...
    @abstractmethod
    def submit_order(self, request:OrderRequest)->dict: ...
    @abstractmethod
    def cancel_order(self, order_id:str)->dict: ...
    @abstractmethod
    def query_order(self, order_id:str)->dict: ...
    @abstractmethod
    def fills(self, order_id:str|None=None)->list[dict]: ...

class FinamBroker(Broker):
    """Fail-closed boundary: transport awaits verified current API schema/bindings."""
    def __init__(self, token:str|None, account_id:str|None, endpoint:str, live_enabled:bool=False):
        self._token=token; self._account_id=account_id; self.endpoint=endpoint; self.live_enabled=live_enabled; self.connected=False
    def connect(self):
        if not self._token or not self._account_id: raise RuntimeError("FINAM_CREDENTIALS_MISSING")
        raise RuntimeError("FINAM_OFFICIAL_SCHEMA_NOT_AUTHENTICATED")
    def disconnect(self): self.connected=False
    def health(self): return {"connected":self.connected,"live_enabled":self.live_enabled,"status":"BINDING_BLOCKED"}
    def _blocked(self,*_:Any,**__:Any): raise RuntimeError("FINAM_OFFICIAL_SCHEMA_NOT_AUTHENTICATED")
    resolve_security=_blocked; account=_blocked; positions=_blocked; active_orders=_blocked
    cancel_order=_blocked; query_order=_blocked; fills=_blocked
    def submit_order(self,request:OrderRequest):
        if not self.live_enabled: raise RuntimeError("LIVE_TRADING_DISABLED")
        return self._blocked(request)

class DryRunBroker(Broker):
    def __init__(self): self.connected=False; self.orders:dict[str,dict]={}
    def connect(self): self.connected=True
    def disconnect(self): self.connected=False
    def health(self): return {"connected":self.connected,"mode":"DRY_RUN"}
    def resolve_security(self,s): return {"research_symbol":s,"binding_status":"BLOCKED_UNAUTHENTICATED"}
    def account(self): return {"mode":"DRY_RUN"}
    def positions(self): return []
    def active_orders(self): return list(self.orders.values())
    def submit_order(self,r):
        if r.idempotency_key in self.orders: return self.orders[r.idempotency_key]
        result={"order_id":"DRY-"+r.idempotency_key[:16],"status":OrderStatus.ACKNOWLEDGED.value,"transmitted":False,"quantity":r.quantity,"filled_quantity":0}
        self.orders[r.idempotency_key]=result; return result
    def cancel_order(self,oid): return {"order_id":oid,"status":OrderStatus.CANCELLED.value}
    def query_order(self,oid): return next((x for x in self.orders.values() if x["order_id"]==oid),{"status":"UNKNOWN"})
    def fills(self,order_id=None): return []
