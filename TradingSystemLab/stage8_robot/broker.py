"""Broker boundary: dry-run and explicitly account-bound FINAM demo only."""
from abc import ABC,abstractmethod
from dataclasses import dataclass
from enum import Enum
class OrderStatus(str,Enum):
 SIGNAL_CREATED="SIGNAL_CREATED"; INTENT_PERSISTED="INTENT_PERSISTED"; ORDER_SUBMITTED="ORDER_SUBMITTED"; ACKNOWLEDGED="ACKNOWLEDGED"; PARTIALLY_FILLED="PARTIALLY_FILLED"; FILLED="FILLED"; POSITION_OPEN="POSITION_OPEN"; EXIT_ORDER="EXIT_ORDER"; CLOSED="CLOSED"; REJECTED="REJECTED"; CANCELLED="CANCELLED"; EXPIRED="EXPIRED"; UNKNOWN="UNKNOWN"; RECONCILIATION_REQUIRED="RECONCILIATION_REQUIRED"
@dataclass(frozen=True)
class OrderRequest: idempotency_key:str; contract_id:str; direction:str; quantity:int; order_type:str="MARKET"
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
  details=self.api.create_session(); accounts=details.get("accounts",[])
  ids={str(x.get("id",x.get("accountId",x))) for x in accounts}
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
  return self.api.place_order(self.account_id,{"symbol":r.contract_id,"side":r.direction,"quantity":r.quantity,"type":r.order_type,"clientOrderId":r.idempotency_key})
 def cancel_order(self,oid): return self.api.cancel_order(self.account_id,oid)
 def query_order(self,oid): return self.api.order(self.account_id,oid)
 def fills(self,order_id=None): return self.account().get("trades",[])
 def resolve_security(self,s): return self.api.asset(s)
class FinamBroker(FinamDemoBroker):
 def __init__(self,*a,**kw):
  if kw.pop("live_enabled",False): raise RuntimeError("LIVE_TRADING_NOT_AUTHORIZED")
  super().__init__(*a,**kw)
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
