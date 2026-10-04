"""Production-contract integration for Stage 8.11 (synthetic transport only)."""
import hashlib
import json
from datetime import datetime, timezone
from urllib.parse import urlparse

import pytest

from TradingSystemLab.stage8_robot.controlled_real_acceptance import (
    AcceptanceAuthority, ControlledAcceptanceBroker, STAGE8_10_AUTHORITY,
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
    """Imitates only the real v1 endpoints consumed by FinamAPI."""
    def __init__(self, scenario="pass"):
        self.scenario = scenario
        self.orders = []
        self.trades = []
        self.position = 0
        self.posts = 0
        self.deletes = 0

    def __call__(self, request, timeout):
        path = urlparse(request.full_url).path
        method = request.get_method()
        if path == "/v1/sessions" and method == "POST": return Raw({"token":"jwt"})
        if path == "/v1/sessions/details":
            return Raw({"readonly":False,"account_ids":[ACCOUNT]})
        prefix = f"/v1/accounts/{ACCOUNT}"
        if path == prefix and method == "GET":
            position = self.position
            if self.scenario == "final_nonflat" and self.posts >= 2: position = 1
            positions = [] if position == 0 else [{"symbol":SYMBOL,"quantity":position}]
            trades = list(self.trades)
            if self.scenario == "unrelated_fill" and self.posts == 1:
                trades = [{"trade_id":"alien","order_id":"alien-order","client_order_id":"alien-client",
                    "symbol":SYMBOL,"side":"SIDE_BUY","quantity":"1","price":"1","timestamp":NOW.isoformat()}]
            return Raw({"positions":positions,"trades":trades})
        if path == prefix + "/orders" and method == "POST":
            payload=json.loads(request.data)
            self.posts += 1
            oid=f"o{self.posts}"
            side=payload["side"]
            status="ACTIVE" if self.scenario == "active_cancel" and self.posts == 1 else "FILLED"
            if self.scenario == "no_fill" and self.posts == 1: status="REJECTED"
            symbol="CNYRUBF@RTSX" if self.scenario == "mismatched_symbol" and self.posts == 1 else payload["symbol"]
            filled=1 if status == "FILLED" else 0
            order={"order_id":oid,"client_order_id":payload["client_order_id"],"symbol":symbol,
                   "side":side,"status":status,"filled_quantity":filled}
            self.orders.append(order)
            if filled:
                self.position += 1 if side == "SIDE_BUY" else -1
                self.trades.append({"trade_id":"t"+oid,"order_id":oid,"client_order_id":payload["client_order_id"],
                    "symbol":symbol,"side":side,"quantity":"1","price":"1","timestamp":NOW.isoformat()})
            uncertain=(self.scenario == "uncertain_entry" and self.posts == 1
                       or self.scenario == "uncertain_flatten" and self.posts == 2)
            if uncertain: raise TimeoutError("synthetic uncertain POST")
            return Raw({"order_id":oid})
        if path == prefix + "/orders" and method == "GET":
            if self.scenario == "malformed": return Raw({"unexpected":[]})
            rows=[{"order_id":o["order_id"],"client_order_id":o["client_order_id"],"status":o["status"]}
                  for o in self.orders]
            if self.scenario == "duplicate" and rows: rows.append(dict(rows[0],order_id="duplicate"))
            return Raw({"orders":rows})
        if path.startswith(prefix + "/orders/") and method == "GET":
            oid=path.rsplit("/",1)[1]
            return Raw(next(o for o in self.orders if o["order_id"] == oid))
        if path.startswith(prefix + "/orders/") and method == "DELETE":
            oid=path.rsplit("/",1)[1]
            next(o for o in self.orders if o["order_id"] == oid)["status"]="CANCELLED"
            self.deletes += 1
            return Raw({})
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


@pytest.mark.parametrize("scenario,classification",[
    ("uncertain_entry","SYNTHETIC_PASS"),("uncertain_flatten","SYNTHETIC_PASS"),
    ("active_cancel","NOT_ACCEPTED_NO_EXECUTION"),("no_fill","NOT_ACCEPTED_NO_EXECUTION"),
    ("malformed","OPERATOR_INTERVENTION_REQUIRED"),("duplicate","OPERATOR_INTERVENTION_REQUIRED"),
    ("unrelated_fill","OPERATOR_INTERVENTION_REQUIRED"),("mismatched_symbol","OPERATOR_INTERVENTION_REQUIRED"),
    ("final_nonflat","OPERATOR_INTERVENTION_REQUIRED"),
])
def test_real_finam_api_contract_fails_closed(tmp_path,scenario,classification):
    result,transport,_=execute(tmp_path,scenario)
    assert result["classification"] == classification
    assert transport.posts <= 2
    if scenario == "active_cancel": assert transport.deletes == 1
