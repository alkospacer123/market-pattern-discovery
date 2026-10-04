import hashlib
import json
from datetime import datetime, timezone

import pytest

from TradingSystemLab.stage8_robot.broker import FinamRealReadOnlyBroker, OrderRequest
from TradingSystemLab.stage8_robot.config import RuntimeConfig
from TradingSystemLab.stage8_robot.controlled_real_acceptance import (
    AcceptanceAuthority, AcceptanceBlocked, ControlledAcceptanceBroker,
    OperatorInterventionRequired, STAGE8_10_AUTHORITY, build_physical_context,
    precheck, resolve_frozen_symbol, run_controlled_lifecycle, sanitized_evidence,
)
from TradingSystemLab.stage8_robot.finam_api import FinamUncertainSubmission
from TradingSystemLab.stage8_robot.instrument_resolver import N4
from TradingSystemLab.stage8_robot.specification import ACTIVE_IDENTITY, PRODUCTION_SPECIFICATION_ID
from TradingSystemLab.stage8_robot.state import StateStore
from TradingSystemLab.stage8_robot.trading_safety_gate import heartbeat_path, load_kill_switch, write_kill_switch

NOW = datetime(2026, 10, 4, 12, tzinfo=timezone.utc)
ACCOUNT = "synthetic-account"
HASH = hashlib.sha256(ACCOUNT.encode()).hexdigest()


def authority(**changes):
    values = dict(production_specification_id=PRODUCTION_SPECIFICATION_ID,
        active_identity=ACTIVE_IDENTITY, stage8_10_status=STAGE8_10_AUTHORITY,
        configured_account_hash=HASH, observed_account_hash=HASH, heartbeat_account_hash=HASH,
        trading_token_loaded_from_current_user_dpapi=True, trading_session_readonly=False,
        account_reconciled=True, unknown_position_count=0, active_order_count=0,
        unresolved_intent_count=0, h1_data_safety_valid=True, instrument_binding_valid=True,
        instrument_tradable=True, r15_capacity=2, margin_capacity=2)
    values.update(changes)
    return AcceptanceAuthority(**values)


def armed_runtime(tmp_path):
    root = tmp_path / "runtime"
    write_kill_switch(root, "ARMED", allow_arm=True, now=NOW)
    path = heartbeat_path(root); path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"production_id": PRODUCTION_SPECIFICATION_ID, "mode": "REAL_READONLY",
        "health_status": "HEALTHY", "reconciliation_status": "PASS", "entries_enabled": False,
        "unresolved_order_count": 0, "failure_code": None, "consecutive_failures": 0,
        "cycle_count": 1, "account_hash": HASH, "timestamp": NOW.isoformat(),
        "last_successful_finam_api_contact": NOW.isoformat()}))
    return root


@pytest.mark.parametrize("change,code", [
    ({"configured_account_hash": "b"*64}, "ACCOUNT_BINDING_INVALID"),
    ({"heartbeat_account_hash": "b"*64}, "ACCOUNT_BINDING_INVALID"),
    ({"account_reconciled": False}, "RECONCILIATION_NOT_PASS"),
    ({"active_order_count": 1}, "ACTIVE_ORDERS_PRESENT"),
    ({"unresolved_intent_count": 1}, "UNRESOLVED_INTENTS_PRESENT"),
    ({"r15_capacity": 0}, "R15_CAPACITY_ZERO"), ({"margin_capacity": 0}, "MARGIN_CAPACITY_ZERO")])
def test_authority_failures_block(tmp_path, change, code):
    result = precheck(authority=authority(**change), runtime_root=armed_runtime(tmp_path), now=NOW,
                      execution_authorized=True, instrument="USDRUBF")
    assert result["decision"] == "BLOCKED" and code in result["reason_codes"]


class API:
    def __init__(self, store, snapshots, uncertain=()):
        self.store, self.snapshots, self.uncertain = store, iter(snapshots), list(uncertain)
        self.calls=[]; self.posts=0
    def place_order(self, account, payload):
        assert self.store.unresolved_intent_count() >= 1
        self.posts += 1; self.calls.append(("post", account, payload))
        if self.uncertain and self.uncertain.pop(0):
            raise FinamUncertainSubmission("uncertain")
        return {"order_id": f"o{self.posts}"}
    def acceptance_snapshot(self, account, client_id): return next(self.snapshots)
    def acceptance_account_snapshot(self, account):
        return {"position_quantity":0, "active_order_count":0, "reconciled":True}
    def cancel_order(self, account, oid): self.calls.append(("cancel", account, oid)); return {}


def fill(order, position):
    return {"order_status":"FILLED", "order_id":order, "filled_quantity":1,
            "position_quantity":position, "fills":[{"fill_id":"f"+order,"broker_order_id":order,
            "trade_id":"t"+order,"quantity":"1","price":"1","timestamp":NOW.isoformat()}]}


def run(tmp_path, snapshots, uncertain=(), symbol="USDRUBF@RTSX", auth=None):
    root=armed_runtime(tmp_path); store=StateStore(tmp_path/"state.db")
    api=API(store,snapshots,uncertain); broker=ControlledAcceptanceBroker(api,ACCOUNT,HASH,store)
    result=run_controlled_lifecycle(authority=auth or authority(),runtime_root=root,
        execution_authorized=True,instrument="USDRUBF",finam_symbol=symbol,direction="LONG",
        broker=broker,now=NOW)
    return result,api,store,root


def test_success_requires_entry_position_flatten_and_canonical_store(tmp_path):
    result,api,store,root=run(tmp_path,[fill("o1",1),fill("o2",0)])
    assert result["classification"] == "SYNTHETIC_PASS"
    assert result["entry_fill_proven"] and result["one_contract_position_observed"] and result["flatten_fill_proven"]
    assert store.unresolved_intent_count() == 0 and api.posts == 2
    assert load_kill_switch(root)[0]["state"] == "HALTED"


@pytest.mark.parametrize("uncertain", [(True,False),(False,True),(True,True)])
def test_every_uncertain_post_is_reconciled_without_retry(tmp_path, uncertain):
    result,api,store,_=run(tmp_path,[fill("o1",1),fill("o2",0)],uncertain)
    assert result["classification"] == "SYNTHETIC_PASS"
    assert api.posts == 2 and store.unresolved_intent_count() == 0


def test_uncertain_active_order_is_cancelled_then_no_execution(tmp_path):
    active={"order_status":"ACTIVE","order_id":"o1","filled_quantity":0,"position_quantity":0,"fills":[]}
    cancelled={"order_status":"CANCELLED","order_id":"o1","filled_quantity":0,"position_quantity":0,"fills":[]}
    result,api,store,_=run(tmp_path,[active,cancelled],(True,))
    assert result["classification"] == "NOT_ACCEPTED_NO_EXECUTION"
    assert api.posts == 1 and any(x[0]=="cancel" for x in api.calls) and store.unresolved_intent_count()==0


def test_cancel_race_fill_is_flattened_not_misclassified(tmp_path):
    active={"order_status":"ACTIVE","order_id":"o1","filled_quantity":0,"position_quantity":0,"fills":[]}
    raced=fill("o1",1); raced["order_status"]="CANCELLED"
    result,api,store,_=run(tmp_path,[active,raced,fill("o2",0)],(True,False))
    assert result["classification"] == "SYNTHETIC_PASS"
    assert api.posts == 2 and store.unresolved_intent_count() == 0


@pytest.mark.parametrize("status", ["REJECTED","EXPIRED","CANCELLED"])
def test_terminal_entry_without_fill_is_never_pass(tmp_path,status):
    terminal={"order_status":status,"order_id":"o1","filled_quantity":0,"position_quantity":0,"fills":[]}
    result,api,_,_=run(tmp_path,[terminal])
    assert result["classification"] == "NOT_ACCEPTED_NO_EXECUTION" and api.posts == 1


def test_unprovable_state_requires_operator_and_halts(tmp_path):
    unknown={"order_status":"UNKNOWN","filled_quantity":0,"position_quantity":0,"fills":[]}
    result,api,store,root=run(tmp_path,[unknown],(True,))
    assert result["classification"] == "OPERATOR_INTERVENTION_REQUIRED"
    assert api.posts == 1 and store.unresolved_intent_count()==1
    assert load_kill_switch(root)[0]["state"] == "HALTED"


def test_account_a_authority_cannot_use_account_b_and_no_post(tmp_path):
    store=StateStore(tmp_path/"s.db"); api=API(store,[])
    with pytest.raises(AcceptanceBlocked,match="ACCOUNT_BINDING"):
        ControlledAcceptanceBroker(api,"account-b",HASH,store)
    assert api.posts == 0


def test_symbol_registry_all_n4_and_mutation_blocks_before_post(tmp_path):
    assert {x:resolve_frozen_symbol(x) for x in N4} == {x:f"{x}@RTSX" for x in N4}
    result,api,_,_=run(tmp_path,[],symbol="CNYRUBF@RTSX")
    assert result["classification"] == "BLOCKED" and result["failure_code"] == "FINAM_SYMBOL_BINDING_INVALID"
    assert api.posts == 0


def test_context_builder_derives_authority_from_components(tmp_path):
    root=armed_runtime(tmp_path)
    store=StateStore(tmp_path/"context.db")
    class Session:
        def session_details(self): return {"readonly":False,"account_ids":[ACCOUNT]}
    credential={"scope":"CurrentUser","api_secret":"ephemeral","account_id":ACCOUNT}
    got,api,symbol=build_physical_context(account_id=ACCOUNT,credential_loader=lambda:credential,
        session_factory=lambda secret:Session(),runtime_root=root,
        store=store,
        reconciliation=lambda api,account:{"reconciled":True,"unknown_position_count":0,
          "active_order_count":0,"unresolved_intent_count":0}, sizing=lambda instrument:1,
        margin=lambda api,account,symbol:1,instrument="USDRUBF")
    assert got.configured_account_hash == HASH == got.heartbeat_account_hash
    assert symbol == "USDRUBF@RTSX" and credential == {}


def evidence(**changes):
    values=dict(accepted_code_commit="a"*40,sanitized_account_identity_hash=HASH,
        instrument="USDRUBF",direction="LONG",quantity=1,
        preflight_gate_outcomes={"account_binding":True},kill_switch_pre_state="ARMED",
        kill_switch_final_state="HALTED",execution_authorization_observed=True,
        order_endpoint_call_count=2,broker_order_present=True,broker_fill_count=2,
        entry_fill_proven=True,one_contract_position_observed=True,controlled_flatten_proven=True,
        final_position_quantity=0,final_active_order_count=0,unresolved_intent_count=0,
        reconciliation_result="PASS",physical_result_classification="PASS",
        external_raw_evidence_sha256="b"*64)
    values.update(changes); return values


def test_evidence_schema_privacy_and_pass_invariants():
    assert sanitized_evidence(**evidence())["physical_result_classification"] == "PASS"
    with pytest.raises(ValueError,match="ALLOWLISTED"): sanitized_evidence(**evidence(account_id="private"))
    with pytest.raises(ValueError,match="PREFLIGHT"): sanitized_evidence(**evidence(preflight_gate_outcomes={"token":"secret"}))
    with pytest.raises(ValueError,match="PASS_EVIDENCE"): sanitized_evidence(**evidence(entry_fill_proven=False))


def test_existing_live_and_readonly_airgaps(monkeypatch):
    monkeypatch.setenv("FINAM_MODE","LIVE")
    with pytest.raises(RuntimeError,match="LIVE_TRADING_NOT_AUTHORIZED"): RuntimeConfig.from_environment()
    with pytest.raises(RuntimeError,match="REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED"):
        FinamRealReadOnlyBroker(object(),"opaque").submit_order(None)
