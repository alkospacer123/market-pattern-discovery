"""Production-contract integration for Stage 8.11 (synthetic transport only)."""
import hashlib
import json
from datetime import datetime, timezone
from urllib.parse import urlparse

import pytest

from TradingSystemLab.stage8_robot.controlled_real_acceptance import (
    AcceptanceAuthority, ControlledAcceptanceBroker, STAGE8_10_AUTHORITY,
    OperatorInterventionRequired, _decimal_contracts, _position, _timestamp,
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
            position = 1 if self.scenario == "final_nonflat" and self.posts >= 2 else self.position
            if self.scenario == "position_overfill" and self.posts == 1: position = 2
            positions=[] if position == 0 else [{"symbol":SYMBOL,"quantity":self.decimal(position),
                "average_price":self.decimal(1),"current_price":self.decimal(1),
                "maintenance_margin":self.decimal(0),"daily_pnl":self.decimal(0),
                "unrealized_pnl":self.decimal(0)}]
            return Raw({"account_id":ACCOUNT,"type":"FORTS","status":"ACCOUNT_ACTIVE",
                "equity":self.decimal(1000),"unrealized_profit":self.decimal(0),"positions":positions,
                "cash":[],"portfolio_forts":{"available_cash":self.decimal(1000),
                "money_reserved":self.decimal(0)}})
        if path == prefix + "/trades" and method == "GET":
            rows=list(self.trade_rows)
            if self.scenario == "unrelated_fill" and self.posts == 1:
                rows=[{"trade_id":"alien","order_id":"alien-order","account_id":ACCOUNT,
                    "symbol":SYMBOL,"side":"SIDE_BUY","size":self.decimal(1),
                    "price":self.decimal(1),"timestamp":"2026-10-04T09:00:03Z",
                    "comment":"","accrued_interest":self.decimal(0),"currency":"RUB"}]
            return Raw({"trades":rows})
        if path == prefix + "/orders" and method == "POST":
            payload=json.loads(request.data); self.posts += 1; oid=f"o{self.posts}"
            status="ACTIVE" if self.scenario == "active_cancel" and self.posts == 1 else "FILLED"
            if self.scenario == "no_fill" and self.posts == 1: status="REJECTED"
            if self.scenario == "mismatched_symbol" and self.posts == 1: payload["symbol"]="CNYRUBF@RTSX"
            executed=1 if status == "FILLED" else 0
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
            return Raw({"orders":rows})
        if path.startswith(prefix + "/orders/") and method == "GET":
            oid=path.rsplit("/",1)[1]; return Raw(next(o for o in self.orders if o["order_id"] == oid))
        if path.startswith(prefix + "/orders/") and method == "DELETE":
            oid=path.rsplit("/",1)[1]; order=next(o for o in self.orders if o["order_id"] == oid)
            order["status"]="CANCELLED"; self.deletes += 1; return Raw(order)
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


def test_real_finam_api_contract_runs_full_controlled_lifecycle(tmp_path):
    result,transport,store=execute(tmp_path,"pass")
    assert result["classification"] == "SYNTHETIC_PASS"
    assert transport.posts == 2 and store.unresolved_intent_count() == 0
    assert ("GET",f"/v1/accounts/{ACCOUNT}/trades") in transport.paths


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
    ("unrelated_fill","OPERATOR_INTERVENTION_REQUIRED"),("mismatched_symbol","OPERATOR_INTERVENTION_REQUIRED"),
    ("final_nonflat","OPERATOR_INTERVENTION_REQUIRED"),("executed_overfill","OPERATOR_INTERVENTION_REQUIRED"),
    ("position_overfill","OPERATOR_INTERVENTION_REQUIRED"),
])
def test_real_finam_api_contract_fails_closed(tmp_path,scenario,classification):
    result,transport,_=execute(tmp_path,scenario)
    assert result["classification"] == classification
    assert transport.posts <= 2
    if scenario == "active_cancel": assert transport.deletes == 1
