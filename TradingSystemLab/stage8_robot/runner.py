"""Dry-run orchestration. Live transport cannot be selected implicitly."""
from decimal import Decimal
import hashlib
from .broker import DryRunBroker,OrderRequest
from .config import RuntimeConfig,RuntimeMode
from .margin import parse_rest_decimal_value_object
from .reconciliation import Reconciliation,reconcile
from .specification import load_frozen_specification
from .state import StateStore
class RobotRunner:
    def __init__(self,config:RuntimeConfig,broker=None):
        account_identity=("DRY_RUN" if not config.account_id else hashlib.sha256(config.account_id.encode()).hexdigest())
        environment="REAL" if config.mode is RuntimeMode.FINAM_REAL_READONLY else config.mode.value
        self.spec=load_frozen_specification(); self.config=config; self.store=StateStore(config.persistence_path,{"production_specification_id":self.spec.production_id,"broker":"FINAM" if not config.dry_run else "DRY_RUN","account_identity_sha256":account_identity,"environment":environment})
        if config.mode.value == "LIVE": raise RuntimeError("LIVE_TRADING_NOT_AUTHORIZED")
        if broker is None and not config.dry_run: raise RuntimeError("EXPLICIT_FINAM_BROKER_REQUIRED")
        self.broker=broker or DryRunBroker(); self.entries_enabled=False
        persisted=self.store.get("realized_equity")
        if config.mode is RuntimeMode.FINAM_REAL_READONLY:
            self.realized_equity=Decimal(persisted) if persisted is not None else None
        else:
            configured=Decimal(config.starting_equity); self.realized_equity=Decimal(persisted) if persisted is not None else configured
            initial=Decimal(self.store.get("starting_realized_equity",str(configured)))
            if initial!=configured: raise RuntimeError("STARTING_EQUITY_STATE_MISMATCH")
            self.store.put("starting_realized_equity",str(configured)); self.store.put("realized_equity",str(self.realized_equity))
    def startup(self):
        self.broker.connect()
        broker_positions=self.broker.positions(); broker_orders=self.broker.active_orders()
        if self.config.mode is RuntimeMode.FINAM_REAL_READONLY and self.realized_equity is None:
            if broker_positions or broker_orders or self.store.unresolved_intent_count():
                raise RuntimeError("REAL_ACCOUNT_NOT_CLEAN_FOR_INITIALIZATION")
            account=self.broker.account(); equity=account.get("equity")
            try: starting=parse_rest_decimal_value_object(equity,positive=True)
            except ValueError: raise RuntimeError("REAL_ACCOUNT_EQUITY_INVALID") from None
            self.realized_equity=starting
            self.store.put("starting_realized_equity",str(starting)); self.store.put("realized_equity",str(starting))
            self.store.put("positions",[]); self.store.put("orders",[])
        elif self.config.mode is RuntimeMode.FINAM_REAL_READONLY:
            account=self.broker.account(); equity=account.get("equity"); unrealized=account.get("unrealized_profit")
            externally_explained=Decimal(self.store.get("explained_external_cash_flows","0"))
            try:
                broker_realized_basis=(parse_rest_decimal_value_object(equity)
                    -parse_rest_decimal_value_object(unrealized)-externally_explained)
            except ValueError: raise RuntimeError("REAL_ACCOUNT_EQUITY_INVALID") from None
            if broker_realized_basis!=self.realized_equity: raise RuntimeError("UNEXPLAINED_REALIZED_EQUITY_DISCREPANCY")
        status=reconcile(self.store.get("positions",[]),broker_positions,self.store.get("orders",[]),broker_orders)
        self.store.put("reconciliation",status.value)
        self.entries_enabled=(status is Reconciliation.RECONCILED and not self.config.new_entries_disabled
                              and self.store.unresolved_intent_count()==0 and self.config.mode is not RuntimeMode.FINAM_REAL_READONLY)
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
        if self.realized_equity is None: raise RuntimeError("REALIZED_EQUITY_NOT_INITIALIZED")
        self.realized_equity += gross_pnl-commission-exchange_fee
        self.store.put("realized_equity",str(self.realized_equity))
