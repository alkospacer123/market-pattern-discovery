"""Production-contract integration for Stage 8.11 (synthetic transport only)."""
import hashlib
import json
from datetime import datetime, timezone
from urllib.error import HTTPError
from urllib.parse import urlparse

import pytest

from TradingSystemLab.stage8_robot.account_cleanliness import (
    ACTIVE_ORDER_STATUSES, DOCUMENTED_ORDER_STATUSES, TERMINAL_ORDER_STATUSES,
)
from TradingSystemLab.stage8_robot.controlled_real_acceptance import (
    AcceptanceAuthority, ControlledAcceptanceBroker, STAGE8_10_AUTHORITY,
    RECONCILIATION_ACTIVE_GRACE_OBSERVATIONS,
    OperatorInterventionRequired, _decimal_contracts, _position, _status, _timestamp,
    run_controlled_lifecycle,
)
from TradingSystemLab.stage8_robot.finam_api import FinamAPI
from TradingSystemLab.stage8_robot.specification import ACTIVE_IDENTITY, PRODUCTION_SPECIFICATION_ID
from TradingSystemLab.stage8_robot.state import StateStore
from TradingSystemLab.stage8_robot.trading_safety_gate import heartbeat_path, write_kill_switch

NOW = datetime(2026, 10, 4, 12, tzinfo=timezone.utc)
ACCOUNT = "production-contract-synthetic"
HASH = hashlib.sha256(ACCOUNT.encode()).hexdigest()
SYMBOL = "USDRUBF@RTSX"


class Raw:
    status = 200
    headers = {}
    def __init__(self, value): self.value = value
    def read(self): return json.dumps(self.value).encode()


class SyntheticFinamTransport:
    """Exact documented REST shapes for the six Stage 8.11 FINAM endpoints."""
    def __init__(self, scenario="pass"):
        self.scenario, self.orders, self.trade_rows = scenario, [], []
        self.position = self.posts = self.deletes = 0
        self.trade_reads = 0
        self.account_reads = 0
        self.paths = []

    @staticmethod
    def decimal(value): return {"value": str(value)}

    def state(self, oid, payload, status, executed):
        return {"order_id":oid,"exec_id":"exec-"+oid,"status":status,
            "order":{"account_id":ACCOUNT,"symbol":payload["symbol"],
                "quantity":self.decimal(1),"side":payload["side"],"type":payload["type"],
                "time_in_force":"TIME_IN_FORCE_DAY","client_order_id":payload["client_order_id"],
                "comment":"stage8.11"},
            "transact_at":"2026-10-04T09:00:01Z","accept_at":"2026-10-04T09:00:02Z",
            "withdraw_at":"2026-10-04T09:00:04Z","initial_quantity":self.decimal(1),
            "executed_quantity":self.decimal(executed),
            "remaining_quantity":self.decimal(1-executed)}

    def __call__(self, request, timeout):
        path, method = urlparse(request.full_url).path, request.get_method()
        self.paths.append((method,path))
        if path == "/v1/sessions" and method == "POST": return Raw({"token":"jwt"})
        if path == "/v1/sessions/details": return Raw({"readonly":False,"account_ids":[ACCOUNT]})
        if path == f"/v1/assets/{SYMBOL}/schedule" and method == "GET":
            return Raw({"sessions":[{"type":"CORE_TRADING","interval":{
                "start_time":"2026-10-04T00:00:00Z","end_time":"2026-10-04T23:59:00Z"}}]})
        prefix = f"/v1/accounts/{ACCOUNT}"
        if path == prefix and method == "GET":
            self.account_reads += 1
            position = 1 if self.scenario == "final_nonflat" and self.posts >= 2 else self.position
            if self.scenario == "position_overfill" and self.posts == 1: position = 2
            if self.scenario == "delayed_position" and self.posts == 1 and self.account_reads < 3:
                position = 0
            if self.scenario == "terminal_fill_zero_executed_delayed_position" and self.posts == 1 and self.account_reads < 3:
                position = 0
            positions=[] if position == 0 else [{"symbol":SYMBOL,"quantity":self.decimal(position),
                "average_price":self.decimal(1),"current_price":self.decimal(1),
                "maintenance_margin":self.decimal(0),"daily_pnl":self.decimal(0),
                "unrealized_pnl":self.decimal(0)}]
            return Raw({"account_id":ACCOUNT,"type":"FORTS","status":"ACCOUNT_ACTIVE",
                "equity":self.decimal(1000),"unrealized_profit":self.decimal(0),"positions":positions,
                "cash":[],"portfolio_forts":{"available_cash":self.decimal(1000),
                "money_reserved":self.decimal(0)}})
        if path == prefix + "/trades" and method == "GET":
            self.trade_reads += 1
            if self.scenario == "trades_http_400":
                raise HTTPError(request.full_url,400,"bad request",{},None)
            rows=list(self.trade_rows)
            if self.scenario == "delayed_trade" and self.posts == 1 and self.trade_reads < 3:
                rows=[]
            if self.scenario == "missing_trade" and self.posts == 1:
                rows=[]
            if self.scenario == "missing_all_trades":
                rows=[]
            if self.scenario == "unrelated_fill" and self.posts == 1:
                rows=[{"trade_id":"alien","order_id":"alien-order","account_id":ACCOUNT,
                    "symbol":SYMBOL,"side":"SIDE_BUY","size":self.decimal(1),
                    "price":self.decimal(1),"timestamp":"2026-10-04T09:00:03Z",
                    "comment":"","accrued_interest":self.decimal(0),"currency":"RUB"}]
            return Raw({"trades":rows})
        if path == prefix + "/orders" and method == "POST":
            payload=json.loads(request.data); self.posts += 1; oid=f"o{self.posts}"
            status="ACTIVE" if self.scenario in {"active_cancel","cancel_race_fill"} and self.posts == 1 else "FILLED"
            if self.scenario == "executed_status": status="ORDER_STATUS_EXECUTED"
            if self.scenario == "no_fill" and self.posts == 1: status="REJECTED"
            if self.scenario == "mismatched_symbol" and self.posts == 1: payload["symbol"]="CNYRUBF@RTSX"
            executed=1 if status in {"FILLED", "ORDER_STATUS_EXECUTED"} else 0
            if self.scenario == "executed_overfill" and self.posts == 1: executed=2
            order=self.state(oid,payload,status,executed); self.orders.append(order)
            if executed:
                self.position += 1 if payload["side"] == "SIDE_BUY" else -1
                self.trade_rows.append({"trade_id":"t"+oid,"order_id":oid,"account_id":ACCOUNT,
                    "symbol":payload["symbol"],"side":payload["side"],"size":self.decimal(1),
                    "price":self.decimal(1),"timestamp":"2026-10-04T09:00:03Z",
                    "comment":"","accrued_interest":self.decimal(0),"currency":"RUB"})
            uncertain=(self.scenario == "uncertain_entry" and self.posts == 1 or
                       self.scenario == "uncertain_flatten" and self.posts == 2)
            if uncertain: raise TimeoutError("synthetic uncertain POST")
            return Raw(order)
        if path == prefix + "/orders" and method == "GET":
            if self.scenario == "malformed": return Raw({"unexpected":[]})
            rows=list(self.orders)
            if self.scenario == "duplicate" and rows:
                duplicate=dict(rows[0],order_id="duplicate"); rows.append(duplicate)
            if self.scenario == "duplicate_same_order" and rows:
                rows.append(dict(rows[0]))
            return Raw({"orders":rows})
        if path.startswith(prefix + "/orders/") and method == "GET":
            oid=path.rsplit("/",1)[1]
            if self.scenario == "order_detail_missing":
                raise HTTPError(request.full_url,404,"not found",{},None)
            order=next(o for o in self.orders if o["order_id"] == oid)
            if self.scenario == "stale_active_detail":
                stale=json.loads(json.dumps(order))
                stale["status"]="ACTIVE"
                stale["executed_quantity"]=self.decimal(0)
                stale["remaining_quantity"]=self.decimal(1)
                return Raw(stale)
            if self.scenario in {"terminal_fill_zero_executed",
                                  "terminal_fill_zero_executed_delayed_position"}:
                stale=json.loads(json.dumps(order))
                stale["status"]="FILLED"
                stale["executed_quantity"]=self.decimal(0)
                stale["remaining_quantity"]=self.decimal(1)
                return Raw(stale)
            return Raw(order)
        if path.startswith(prefix + "/orders/") and method == "DELETE":
            oid=path.rsplit("/",1)[1]; order=next(o for o in self.orders if o["order_id"] == oid)
            order["status"]="CANCELLED"; self.deletes += 1
            if self.scenario == "cancel_race_fill" and self.posts == 1:
                order["executed_quantity"]=self.decimal(1)
                order["remaining_quantity"]=self.decimal(0)
                self.position=1
                self.trade_rows.append({"trade_id":"t"+oid,"order_id":oid,"account_id":ACCOUNT,
                    "symbol":order["order"]["symbol"],"side":order["order"]["side"],"size":self.decimal(1),
                    "price":self.decimal(1),"timestamp":"2026-10-04T09:00:03Z",
                    "comment":"","accrued_interest":self.decimal(0),"currency":"RUB"})
            return Raw(order)
        raise AssertionError((method,path))


class NoWait:
    def wait(self): pass


def authority():
    return AcceptanceAuthority(PRODUCTION_SPECIFICATION_ID,ACTIVE_IDENTITY,STAGE8_10_AUTHORITY,
        HASH,HASH,HASH,True,False,True,0,0,0,True,True,True,2,2)


def execute(tmp_path, scenario):
    root=tmp_path/"runtime"
    write_kill_switch(root,"ARMED",allow_arm=True,now=NOW)
    heartbeat_path(root).parent.mkdir(parents=True,exist_ok=True)
    heartbeat_path(root).write_text(json.dumps({"production_id":PRODUCTION_SPECIFICATION_ID,
        "mode":"REAL_READONLY","health_status":"HEALTHY","reconciliation_status":"PASS",
        "entries_enabled":False,"unresolved_order_count":0,"failure_code":None,
        "consecutive_failures":0,"cycle_count":1,"account_hash":HASH,"timestamp":NOW.isoformat(),
        "last_successful_finam_api_contact":NOW.isoformat()}))
    transport=SyntheticFinamTransport(scenario)
    api=FinamAPI("synthetic-secret",transport=transport,limiter=NoWait())
    assert api.session_details() == {"readonly":False,"account_ids":[ACCOUNT]}
    store=StateStore(tmp_path/"state.db")
    broker=ControlledAcceptanceBroker(api,ACCOUNT,HASH,store)
    result=run_controlled_lifecycle(authority=authority(),runtime_root=root,execution_authorized=True,
        instrument="USDRUBF",finam_symbol=SYMBOL,direction="LONG",broker=broker,now=NOW)
    return result,transport,store



def test_real_finam_trades_http_400_does_not_block_exact_order_position_proof_or_flatten(tmp_path):
    result,transport,store=execute(tmp_path,"trades_http_400")
    assert result["classification"] == "SYNTHETIC_PASS"
    assert transport.posts == 2
    assert transport.deletes == 0
    assert transport.trade_reads >= 2
    assert store.intent("stage8.11:USDRUBF:entry")["status"] == "RECONCILED"
    assert store.intent("stage8.11:USDRUBF:flatten")["status"] == "RECONCILED"
    assert store.unresolved_intent_count() == 0


def test_real_finam_eventual_consistency_delayed_trade_does_not_gate_exact_position_proof(tmp_path):
    result,transport,store=execute(tmp_path,"delayed_trade")
    assert result["classification"] == "SYNTHETIC_PASS"
    assert transport.posts == 2
    # /trades is supplementary: ACK + exact account position may reconcile
    # before the delayed entry trade row becomes visible.
    assert transport.trade_reads == 2
    assert store.unresolved_intent_count() == 0
    intents=store.db.execute("SELECT idempotency_key,status FROM intents ORDER BY rowid").fetchall()
    assert intents == [("stage8.11:USDRUBF:entry","RECONCILED"),
                       ("stage8.11:USDRUBF:flatten","RECONCILED")]

def test_real_finam_eventual_consistency_delayed_position_converges_without_duplicate_entry(tmp_path):
    result,transport,store=execute(tmp_path,"delayed_position")
    assert result["classification"] == "SYNTHETIC_PASS"
    assert transport.posts == 2
    assert transport.account_reads >= 3
    assert store.unresolved_intent_count() == 0


def test_real_finam_missing_entry_trade_uses_exact_order_and_position_proof(tmp_path):
    result,transport,store=execute(tmp_path,"missing_trade")
    assert result["classification"] == "SYNTHETIC_PASS"
    assert transport.posts == 2
    assert store.intent("stage8.11:USDRUBF:entry")["status"] == "RECONCILED"
    assert store.intent("stage8.11:USDRUBF:flatten")["status"] == "RECONCILED"
    assert store.unresolved_intent_count() == 0


def test_real_finam_missing_all_trades_uses_exact_order_and_position_proof(tmp_path):
    result,transport,store=execute(tmp_path,"missing_all_trades")
    assert result["classification"] == "SYNTHETIC_PASS"
    assert transport.posts == 2
    assert store.intent("stage8.11:USDRUBF:entry")["status"] == "RECONCILED"
    assert store.intent("stage8.11:USDRUBF:flatten")["status"] == "RECONCILED"
    assert store.unresolved_intent_count() == 0


def test_real_finam_missing_order_detail_uses_ack_and_exact_position_for_entry_and_flatten(tmp_path):
    result,transport,store=execute(tmp_path,"order_detail_missing")
    assert result["classification"] == "SYNTHETIC_PASS"
    assert transport.posts == 2
    assert store.intent("stage8.11:USDRUBF:entry")["status"] == "RECONCILED"
    assert store.intent("stage8.11:USDRUBF:flatten")["status"] == "RECONCILED"
    assert store.unresolved_intent_count() == 0


def test_real_finam_stale_active_order_detail_does_not_cancel_proven_position(tmp_path):
    result,transport,store=execute(tmp_path,"stale_active_detail")
    assert result["classification"] == "SYNTHETIC_PASS"
    assert transport.posts == 2
    assert transport.deletes == 0
    assert store.intent("stage8.11:USDRUBF:entry")["status"] == "RECONCILED"
    assert store.intent("stage8.11:USDRUBF:flatten")["status"] == "RECONCILED"
    assert store.unresolved_intent_count() == 0


def test_real_finam_terminal_fill_status_with_stale_zero_executed_uses_ack_and_position(tmp_path):
    result,transport,store=execute(tmp_path,"terminal_fill_zero_executed")
    assert result["classification"] == "SYNTHETIC_PASS"
    assert transport.posts == 2
    assert transport.deletes == 0
    assert store.intent("stage8.11:USDRUBF:entry")["status"] == "RECONCILED"
    assert store.intent("stage8.11:USDRUBF:flatten")["status"] == "RECONCILED"
    assert store.unresolved_intent_count() == 0
    assert store.db.execute("SELECT COUNT(*) FROM fills").fetchone()[0] == 2


def test_real_finam_terminal_fill_zero_executed_waits_for_position_convergence(tmp_path):
    result,transport,store=execute(tmp_path,"terminal_fill_zero_executed_delayed_position")
    assert result["classification"] == "SYNTHETIC_PASS"
    assert transport.posts == 2
    assert transport.deletes == 0
    assert transport.account_reads >= 3
    assert store.intent("stage8.11:USDRUBF:entry")["status"] == "RECONCILED"
    assert store.intent("stage8.11:USDRUBF:flatten")["status"] == "RECONCILED"
    assert store.unresolved_intent_count() == 0
    assert store.db.execute("SELECT COUNT(*) FROM fills").fetchone()[0] == 2


def test_real_finam_duplicate_same_order_history_row_does_not_block_reconciliation(tmp_path):
    result,transport,store=execute(tmp_path,"duplicate_same_order")
    assert result["classification"] == "SYNTHETIC_PASS"
    assert transport.posts == 2
    assert store.intent("stage8.11:USDRUBF:entry")["status"] == "RECONCILED"
    assert store.intent("stage8.11:USDRUBF:flatten")["status"] == "RECONCILED"
    assert store.unresolved_intent_count() == 0


def test_real_finam_api_contract_runs_full_controlled_lifecycle(tmp_path):
    result,transport,store=execute(tmp_path,"pass")
    assert result["classification"] == "SYNTHETIC_PASS"
    assert transport.posts == 2 and store.unresolved_intent_count() == 0
    assert ("GET",f"/v1/accounts/{ACCOUNT}/trades") in transport.paths


def test_real_finam_executed_status_reconciles_as_filled(tmp_path):
    result,transport,store=execute(tmp_path,"executed_status")
    assert result["classification"] == "SYNTHETIC_PASS"
    assert transport.posts == 2
    assert store.unresolved_intent_count() == 0


def test_active_market_order_gets_grace_observations_before_single_cancel(tmp_path):
    result,transport,store=execute(tmp_path,"active_cancel")
    assert result["classification"] == "NOT_ACCEPTED_NO_EXECUTION"
    assert transport.posts == 1 and transport.deletes == 1
    delete_index=next(i for i,item in enumerate(transport.paths) if item[0]=="DELETE")
    order_collection_reads=sum(
        1 for method,path in transport.paths[:delete_index]
        if method=="GET" and path==f"/v1/accounts/{ACCOUNT}/orders")
    assert order_collection_reads >= RECONCILIATION_ACTIVE_GRACE_OBSERVATIONS
    assert store.unresolved_intent_count() == 0


def test_real_finam_cancel_race_full_fill_is_reconciled_and_flattened(tmp_path):
    result,transport,store=execute(tmp_path,"cancel_race_fill")
    assert result["classification"] == "SYNTHETIC_PASS"
    assert transport.posts == 2
    assert transport.deletes == 1
    assert store.intent("stage8.11:USDRUBF:entry")["status"] == "RECONCILED"
    assert store.intent("stage8.11:USDRUBF:flatten")["status"] == "RECONCILED"
    assert store.unresolved_intent_count() == 0


def test_pending_cancel_is_an_active_reconciliation_status():
    assert _status("ORDER_STATUS_PENDING_CANCEL") == "PENDING_CANCEL"


@pytest.mark.parametrize("raw,normalized", [
    ("ORDER_STATUS_NEW","NEW"),
    ("ORDER_STATUS_PARTIALLY_FILLED","PARTIAL_FILL"),
    ("ORDER_STATUS_FILLED","FILLED"),
    ("ORDER_STATUS_DONE_FOR_DAY","DONE_FOR_DAY"),
    ("ORDER_STATUS_CANCELED","CANCELLED"),
    ("ORDER_STATUS_REPLACED","REPLACED"),
    ("ORDER_STATUS_PENDING_CANCEL","PENDING_CANCEL"),
    ("ORDER_STATUS_REJECTED","REJECTED"),
    ("ORDER_STATUS_SUSPENDED","SUSPENDED"),
    ("ORDER_STATUS_PENDING_NEW","PENDING_NEW"),
    ("ORDER_STATUS_EXPIRED","EXPIRED"),
    ("ORDER_STATUS_FAILED","FAILED"),
    ("ORDER_STATUS_FORWARDING","FORWARDING"),
    ("ORDER_STATUS_WAIT","WAIT"),
    ("ORDER_STATUS_DENIED_BY_BROKER","DENIED_BY_BROKER"),
    ("ORDER_STATUS_REJECTED_BY_EXCHANGE","REJECTED_BY_EXCHANGE"),
    ("ORDER_STATUS_WATCHING","WATCHING"),
    ("ORDER_STATUS_EXECUTED","EXECUTED"),
    ("ORDER_STATUS_DISABLED","DISABLED"),
    ("ORDER_STATUS_LINK_WAIT","LINK_WAIT"),
    ("ORDER_STATUS_SL_GUARD_TIME","SL_GUARD_TIME"),
    ("ORDER_STATUS_SL_EXECUTED","SL_EXECUTED"),
    ("ORDER_STATUS_SL_FORWARDING","SL_FORWARDING"),
    ("ORDER_STATUS_TP_GUARD_TIME","TP_GUARD_TIME"),
    ("ORDER_STATUS_TP_EXECUTED","TP_EXECUTED"),
    ("ORDER_STATUS_TP_CORRECTION","TP_CORRECTION"),
    ("ORDER_STATUS_TP_FORWARDING","TP_FORWARDING"),
    ("ORDER_STATUS_TP_CORR_GUARD_TIME","TP_CORR_GUARD_TIME"),
])
def test_full_documented_finam_order_status_enum_is_parsed(raw, normalized):
    assert _status(raw) == normalized


def test_unspecified_order_status_fails_closed():
    with pytest.raises(OperatorInterventionRequired):
        _status("ORDER_STATUS_UNSPECIFIED")


def test_documented_finam_status_partition_is_complete_and_disjoint():
    assert len(DOCUMENTED_ORDER_STATUSES) == 29
    assert ACTIVE_ORDER_STATUSES.isdisjoint(TERMINAL_ORDER_STATUSES)
    assert ACTIVE_ORDER_STATUSES | TERMINAL_ORDER_STATUSES | {"UNSPECIFIED"} == DOCUMENTED_ORDER_STATUSES


@pytest.mark.parametrize("shape,expected", [({"value":"0"},0),({"value":"1"},1)])
def test_rest_decimal_contract_parser_accepts_documented_whole_values(shape,expected):
    assert _decimal_contracts(shape) == expected


@pytest.mark.parametrize("shape", [
    {"value":"not-decimal"}, {"value":"0.5"}, {}, None,
    {"value":"1","scale":0}, {"num":1,"scale":0}, {"value":1},
])
def test_rest_decimal_contract_parser_rejects_malformed_or_unsupported_shapes(shape):
    with pytest.raises(OperatorInterventionRequired):
        _decimal_contracts(shape)


def test_position_decimal_parser_rejects_more_than_acceptance_contract():
    assert _position([{"symbol":SYMBOL,"quantity":{"value":"1"}}],SYMBOL) == 1
    # Parsing is canonical; the lifecycle's exact-position invariant rejects 2.
    assert _position([{"symbol":SYMBOL,"quantity":{"value":"2"}}],SYMBOL) == 2


@pytest.mark.parametrize("value", [
    "2026-10-04T09:00:02Z",
    "2026-10-04T09:00:02.123456789Z",
    "2026-10-04T12:30:02.5+03:30",
    "2026-10-04T04:00:02-05:00",
])
def test_rest_timestamp_parser_accepts_timezone_aware_rfc3339(value):
    assert _timestamp(value)


@pytest.mark.parametrize("value", [
    {"seconds":1,"nanos":0}, 1, None, "", "not-a-timestamp",
    "2026-10-04T09:00:02", "2026-02-30T09:00:02Z", "2026-10-04T25:00:02Z",
])
def test_rest_timestamp_parser_rejects_unsupported_or_invalid_values(value):
    with pytest.raises(OperatorInterventionRequired):
        _timestamp(value)


@pytest.mark.parametrize(("trade","accepted","valid"), [
    ("2026-10-04T09:00:03Z", "2026-10-04T09:00:02Z", True),
    ("2026-10-04T09:00:02Z", "2026-10-04T09:00:02Z", True),
    ("2026-10-04T09:00:01.999999999Z", "2026-10-04T09:00:02Z", False),
    ("2026-10-04T12:00:02+03:00", "2026-10-04T04:00:02-05:00", True),
])
def test_rest_timestamp_chronology_is_instant_based(trade,accepted,valid):
    assert (_timestamp(trade) >= _timestamp(accepted)) is valid


@pytest.mark.parametrize("scenario,classification",[
    ("uncertain_entry","SYNTHETIC_PASS"),("uncertain_flatten","SYNTHETIC_PASS"),
    ("active_cancel","NOT_ACCEPTED_NO_EXECUTION"),("no_fill","NOT_ACCEPTED_NO_EXECUTION"),
    ("malformed","OPERATOR_INTERVENTION_REQUIRED"),("duplicate","OPERATOR_INTERVENTION_REQUIRED"),
    ("unrelated_fill","SYNTHETIC_PASS"),("mismatched_symbol","OPERATOR_INTERVENTION_REQUIRED"),
    ("final_nonflat","OPERATOR_INTERVENTION_REQUIRED"),("executed_overfill","OPERATOR_INTERVENTION_REQUIRED"),
    ("position_overfill","OPERATOR_INTERVENTION_REQUIRED"),
])
def test_real_finam_api_contract_fails_closed(tmp_path,scenario,classification):
    result,transport,_=execute(tmp_path,scenario)
    assert result["classification"] == classification
    assert transport.posts <= 2
    if scenario == "active_cancel": assert transport.deletes == 1
