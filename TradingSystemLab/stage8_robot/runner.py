"""Dry-run orchestration. Live transport cannot be selected implicitly."""
from decimal import Decimal
from .broker import DryRunBroker,OrderRequest
from .config import RuntimeConfig
from .reconciliation import Reconciliation,reconcile
from .specification import load_frozen_specification
from .state import StateStore
class RobotRunner:
    def __init__(self,config:RuntimeConfig,broker=None):
        self.spec=load_frozen_specification(); self.config=config; self.store=StateStore(config.persistence_path,{"production_specification_id":self.spec.production_id,"broker":"FINAM" if not config.dry_run else "DRY_RUN","account_id":config.account_id or "DRY_RUN","environment":config.mode.value})
        if config.mode.value == "LIVE": raise RuntimeError("LIVE_TRADING_NOT_AUTHORIZED")
        if broker is None and not config.dry_run: raise RuntimeError("EXPLICIT_FINAM_DEMO_BROKER_REQUIRED")
        self.broker=broker or DryRunBroker(); self.entries_enabled=False
        self.realized_equity=Decimal(config.starting_equity)
    def startup(self):
        self.broker.connect()
        status=reconcile(self.store.get("positions",[]),self.broker.positions(),self.store.get("orders",[]),self.broker.active_orders())
        self.store.put("reconciliation",status.value)
        self.entries_enabled=status is Reconciliation.RECONCILED and not self.config.new_entries_disabled
        return status
    def persist_then_submit(self,payload:dict,request:OrderRequest):
        if not self.entries_enabled: raise RuntimeError("NEW_ENTRIES_BLOCKED")
        if not self.store.persist_intent(request.idempotency_key,payload): return self.store.intent(request.idempotency_key)
        result=self.broker.submit_order(request); self.store.put("orders",self.store.get("orders",[])+[result]); return result
    def book_exit(self,gross_pnl:Decimal,commission:Decimal,exchange_fee:Decimal):
        self.realized_equity += gross_pnl-commission-exchange_fee
        self.store.put("realized_equity",str(self.realized_equity))
