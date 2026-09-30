"""Dry-run orchestration. Live transport cannot be selected implicitly."""
from decimal import Decimal
import hashlib
from .broker import DryRunBroker,OrderRequest
from .config import RuntimeConfig
from .reconciliation import Reconciliation,reconcile
from .specification import load_frozen_specification
from .state import StateStore
class RobotRunner:
    def __init__(self,config:RuntimeConfig,broker=None):
        account_identity=("DRY_RUN" if not config.account_id else hashlib.sha256(config.account_id.encode()).hexdigest())
        self.spec=load_frozen_specification(); self.config=config; self.store=StateStore(config.persistence_path,{"production_specification_id":self.spec.production_id,"broker":"FINAM" if not config.dry_run else "DRY_RUN","account_identity_sha256":account_identity,"environment":config.mode.value})
        if config.mode.value == "LIVE": raise RuntimeError("LIVE_TRADING_NOT_AUTHORIZED")
        if broker is None and not config.dry_run: raise RuntimeError("EXPLICIT_FINAM_DEMO_BROKER_REQUIRED")
        self.broker=broker or DryRunBroker(); self.entries_enabled=False
        configured=Decimal(config.starting_equity); persisted=self.store.get("realized_equity")
        if persisted is None:
            self.realized_equity=configured; self.store.put("realized_equity",str(configured))
        else:
            self.realized_equity=Decimal(persisted)
            initial=Decimal(self.store.get("starting_equity",str(configured)))
            if initial!=configured: raise RuntimeError("STARTING_EQUITY_STATE_MISMATCH")
        self.store.put("starting_equity",str(configured))
    def startup(self):
        self.broker.connect()
        status=reconcile(self.store.get("positions",[]),self.broker.positions(),self.store.get("orders",[]),self.broker.active_orders())
        self.store.put("reconciliation",status.value)
        self.entries_enabled=status is Reconciliation.RECONCILED and not self.config.new_entries_disabled
        return status
    def persist_then_submit(self,payload:dict,request:OrderRequest):
        if not self.entries_enabled: raise RuntimeError("NEW_ENTRIES_BLOCKED")
        if not self.store.persist_intent(request.idempotency_key,payload): return self.store.intent(request.idempotency_key)
        self.store.transition_intent(request.idempotency_key,"SUBMITTED")
        try: result=self.broker.submit_order(request)
        except Exception as exc:
            if exc.__class__.__name__=="FinamUncertainSubmission": self.store.transition_intent(request.idempotency_key,"UNCERTAIN")
            raise
        broker_id=result.get("order_id") or result.get("orderId")
        self.store.transition_intent(request.idempotency_key,"ACK",str(broker_id) if broker_id else None)
        self.store.put("orders",self.store.get("orders",[])+[result]); return result
    def book_exit(self,gross_pnl:Decimal,commission:Decimal,exchange_fee:Decimal):
        self.realized_equity += gross_pnl-commission-exchange_fee
        self.store.put("realized_equity",str(self.realized_equity))
