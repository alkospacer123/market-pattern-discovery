"""Broker boundary: dry-run and explicitly account-bound FINAM demo only."""
from abc import ABC,abstractmethod
from dataclasses import dataclass
import hashlib
from .finam_api import (CLIENT_ORDER_ID_MAX_LENGTH, MARKET_ORDER_TYPE,
                        ORDER_SIDE_BUY, ORDER_SIDE_SELL, FinamUncertainSubmission)
from enum import Enum
class OrderStatus(str,Enum):
 SIGNAL_CREATED="SIGNAL_CREATED"; INTENT_PERSISTED="INTENT_PERSISTED"; ORDER_SUBMITTED="ORDER_SUBMITTED"; ACKNOWLEDGED="ACKNOWLEDGED"; PARTIALLY_FILLED="PARTIALLY_FILLED"; FILLED="FILLED"; POSITION_OPEN="POSITION_OPEN"; EXIT_ORDER="EXIT_ORDER"; CLOSED="CLOSED"; REJECTED="REJECTED"; CANCELLED="CANCELLED"; EXPIRED="EXPIRED"; UNKNOWN="UNKNOWN"; RECONCILIATION_REQUIRED="RECONCILIATION_REQUIRED"
def broker_side(direction:str, *, exit_order:bool=False)->str:
 side={"LONG":ORDER_SIDE_BUY,"SHORT":ORDER_SIDE_SELL}[direction]
 if exit_order: side=ORDER_SIDE_SELL if side==ORDER_SIDE_BUY else ORDER_SIDE_BUY
 return side
def compact_client_order_id(internal_id:str)->str:
 """Stable 96-bit ASCII id; the full internal identity stays in SQLite."""
 return "s8"+hashlib.sha256(internal_id.encode()).hexdigest()[:18]
@dataclass(frozen=True)
class OrderRequest:
 idempotency_key:str; contract_id:str; direction:str; quantity:int; exit_order:bool=False
class Broker(ABC):
 @abstractmethod
 def connect(self): ...
 @abstractmethod
 def positions(self): ...
 @abstractmethod
 def active_orders(self): ...
 @abstractmethod
 def submit_order(self,request): ...
class FinamDemoBroker(Broker):
 def __init__(self,api,account_id,demo_account_id,transmission_enabled=False):
  if not account_id or account_id!=demo_account_id: raise RuntimeError("DEMO_ACCOUNT_EXPLICIT_BINDING_REQUIRED")
  self.api=api; self.account_id=account_id; self.enabled=transmission_enabled; self.connected=False
 def connect(self):
  self.api.create_session(); details=self.api.session_details()
  ids={str(x) for x in details.get("account_ids",[])}
  if self.account_id not in ids: raise RuntimeError("CONFIGURED_DEMO_ACCOUNT_NOT_ENUMERATED")
  self.api.account(self.account_id); self.connected=True
 def disconnect(self): self.connected=False
 def health(self): return {"connected":self.connected,"mode":"FINAM_DEMO"}
 def account(self): return self.api.account(self.account_id)
 def positions(self): return self.account().get("positions",[])
 def active_orders(self):
  x=self.api.orders(self.account_id); return x.get("orders",x if isinstance(x,list) else [])
 def submit_order(self,r):
  if not self.enabled: raise RuntimeError("DEMO_ORDER_TRANSMISSION_DISABLED")
  # No retry: uncertain POST must be reconciled by idempotency key/order listing.
  client_id=compact_client_order_id(r.idempotency_key)
  assert len(client_id)<=CLIENT_ORDER_ID_MAX_LENGTH
  payload={"symbol":r.contract_id,"quantity":{"value":str(r.quantity)},
           "side":broker_side(r.direction,exit_order=r.exit_order),
           "type":MARKET_ORDER_TYPE,"client_order_id":client_id}
  try: return self.api.place_order(self.account_id,payload)
  except FinamUncertainSubmission:
   # Never retransmit: the durable intent must be resolved against broker state.
   orders=self.active_orders()
   found=next((x for x in orders if x.get("client_order_id")==client_id),None)
   if found:return found
   raise
 def cancel_order(self,oid): return self.api.cancel_order(self.account_id,oid)
 def query_order(self,oid): return self.api.order(self.account_id,oid)
 def fills(self,order_id=None): return self.account().get("trades",[])
 def resolve_security(self,s): return self.api.asset(s)
class FinamBroker(FinamDemoBroker):
 def __init__(self,*a,**kw):
  if kw.pop("live_enabled",False): raise RuntimeError("LIVE_TRADING_NOT_AUTHORIZED")
  super().__init__(*a,**kw)
class FinamRealReadOnlyBroker(Broker):
 """Real-account query adapter with an unconditional transmission air-gap."""
 def __init__(self,api,account_id):
  if not account_id: raise RuntimeError("REAL_ACCOUNT_EXPLICIT_BINDING_REQUIRED")
  self.api=api; self.account_id=account_id; self.connected=False; self.details=None
 def connect(self):
  self.api.create_session(); self.details=self.api.session_details()
  if self.account_id not in {str(x) for x in self.details.get("account_ids",[])}:
   raise RuntimeError("CONFIGURED_REAL_ACCOUNT_NOT_ENUMERATED")
  if self.details.get("readonly") is not True: raise RuntimeError("REAL_TOKEN_NOT_READONLY")
  self.api.account(self.account_id); self.connected=True
 def disconnect(self): self.connected=False
 def health(self): return {"connected":self.connected,"mode":"FINAM_REAL_READONLY"}
 def account(self): return self.api.account(self.account_id)
 def positions(self): return self.account().get("positions",[])
 def active_orders(self):
  x=self.api.orders(self.account_id); return x.get("orders",x if isinstance(x,list) else [])
 def fills(self,order_id=None): return self.account().get("trades",[])
 def resolve_security(self,s): return self.api.asset(s,self.account_id)
 def asset_params(self,s): return self.api.asset_params(s,self.account_id)
 def schedule(self,s): return self.api.schedule(s)
 def submit_order(self,request): raise RuntimeError("REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED")
class DryRunBroker(Broker):
 def __init__(self): self.connected=False; self.orders={}
 def connect(self): self.connected=True
 def disconnect(self): self.connected=False
 def health(self): return {"connected":self.connected,"mode":"DRY_RUN"}
 def resolve_security(self,s): return {"research_symbol":s,"binding_status":"BLOCKED_UNAUTHENTICATED"}
 def account(self): return {"mode":"DRY_RUN"}
 def positions(self): return []
 def active_orders(self): return list(self.orders.values())
 def submit_order(self,r):
  if r.idempotency_key in self.orders:return self.orders[r.idempotency_key]
  x={"order_id":"DRY-"+r.idempotency_key[:16],"status":OrderStatus.ACKNOWLEDGED.value,"transmitted":False,"quantity":r.quantity,"filled_quantity":0};self.orders[r.idempotency_key]=x;return x
 def cancel_order(self,oid): return {"order_id":oid,"status":OrderStatus.CANCELLED.value}
 def query_order(self,oid): return next((x for x in self.orders.values() if x["order_id"]==oid),{"status":"UNKNOWN"})
 def fills(self,order_id=None): return []
