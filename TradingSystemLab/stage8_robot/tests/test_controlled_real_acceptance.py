import hashlib
import json
from datetime import datetime, timezone

import pytest

from TradingSystemLab.stage8_robot.broker import FinamRealReadOnlyBroker, OrderRequest
from TradingSystemLab.stage8_robot.config import RuntimeConfig
from TradingSystemLab.stage8_robot.controlled_real_acceptance import (
    AcceptanceAuthority, AcceptanceBlocked, ControlledAcceptanceBroker,
    OperatorInterventionRequired, STAGE8_10_AUTHORITY, STAGE8_11_ATTEMPT2_ID,
    build_physical_context,
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
    """Position-authoritative synthetic broker.

    Normal reconciliation can read only account positions after a POST.
    The optional snapshot list supplies successive position observations; order
    status/fill fields are retained only for backward-compatible fixtures.
    """
    def __init__(self, store, snapshots, uncertain=(), unrelated_positions=(), unrelated_active=False):
        self.store = store
        self.snapshots = list(snapshots)
        self.uncertain = list(uncertain)
        self.unrelated_positions = list(unrelated_positions)
        self.unrelated_active = unrelated_active
        self.calls = []
        self.posts = 0
        self.current_position = 0
        self.symbol = "USDRUBF@RTSX"

    def schedule(self, symbol):
        return {"sessions":[{"type":"CORE_TRADING","interval":{
            "start_time":"2026-10-04T00:00:00Z","end_time":"2026-10-04T23:59:00Z"}}]}

    def place_order(self, account, payload):
        assert self.store.unresolved_intent_count() >= 1
        self.posts += 1
        self.symbol = payload["symbol"]
        self.calls.append(("post", account, payload))
        if self.uncertain and self.uncertain.pop(0):
            raise FinamUncertainSubmission("uncertain")
        return {"order_id": f"o{self.posts}"}

    def account(self, account):
        self.calls.append(("account", account))
        if self.posts > 0 and self.snapshots:
            self.current_position = int(self.snapshots.pop(0).get("position_quantity", 0))
        positions = [] if self.current_position == 0 else [
            {"symbol": self.symbol, "quantity": {"value": str(self.current_position)}}
        ]
        positions.extend(
            {"symbol": symbol, "quantity": {"value": str(quantity)}}
            for symbol, quantity in self.unrelated_positions
        )
        return {"account_id": account, "positions": positions}

    def orders(self, account):
        self.calls.append(("orders", account))
        rows = []
        if self.unrelated_active:
            rows.append({"order_id":"unrelated","order":{"client_order_id":"unrelated"},
                         "status":"ORDER_STATUS_NEW"})
        return {"orders": rows}

    def order(self, account, order_id):
        raise AssertionError("NORMAL_RECONCILIATION_MUST_NOT_CALL_ORDER_DETAIL")

    def trades(self, account):
        raise AssertionError("NORMAL_RECONCILIATION_MUST_NOT_CALL_TRADES")

    def cancel_order(self, account, oid):
        raise AssertionError("NORMAL_RECONCILIATION_MUST_NOT_CANCEL")


def fill(order, position):
    return {"order_status":"FILLED", "order_id":order, "executed_quantity":1,
            "position_quantity":position, "fills":[{"fill_id":"f"+order,"broker_order_id":order,
            "trade_id":"t"+order,"quantity":"1","price":"1","timestamp":NOW.isoformat()}]}


def run(tmp_path, snapshots, uncertain=(), symbol="USDRUBF@RTSX", auth=None, **api_options):
    root=armed_runtime(tmp_path); store=StateStore(tmp_path/"state.db")
    api=API(store,snapshots,uncertain,**api_options); broker=ControlledAcceptanceBroker(api,ACCOUNT,HASH,store)
    result=run_controlled_lifecycle(authority=auth or authority(),runtime_root=root,
        execution_authorized=True,instrument="USDRUBF",finam_symbol=symbol,direction="LONG",
        broker=broker,now=NOW,sleeper=lambda _:None)
    return result,api,store,root


def test_success_requires_entry_position_flatten_and_canonical_store(tmp_path):
    result,api,store,root=run(tmp_path,[fill("o1",1),fill("o2",0)])
    assert result["classification"] == "SYNTHETIC_PASS"
    assert result["entry_fill_proven"] and result["one_contract_position_observed"] and result["flatten_fill_proven"]
    assert store.unresolved_intent_count() == 0 and api.posts == 2
    assert load_kill_switch(root)[0]["state"] == "HALTED"


def test_each_post_uses_fresh_clock_and_closed_flatten_requires_operator(tmp_path):
    root=armed_runtime(tmp_path); store=StateStore(tmp_path/"state.db")
    api=API(store,[fill("o1",1)])
    api.schedule=lambda symbol:{"sessions":[{"type":"CORE_TRADING","interval":{
        "start_time":"2026-10-04T11:00:00Z","end_time":"2026-10-04T12:10:00Z"}}]}
    broker=ControlledAcceptanceBroker(api,ACCOUNT,HASH,store)
    observations=iter([NOW, NOW, datetime(2026,10,4,12,10,tzinfo=timezone.utc)])
    result=run_controlled_lifecycle(authority=authority(),runtime_root=root,
        execution_authorized=True,instrument="USDRUBF",finam_symbol="USDRUBF@RTSX",
        direction="LONG",broker=broker,clock=lambda:next(observations))
    assert result["classification"] == "OPERATOR_INTERVENTION_REQUIRED"
    assert result["failure_code"] == "FLATTEN_TRADING_SESSION_NOT_OPEN"
    assert result["entry_fill_proven"] and result["one_contract_position_observed"]
    assert result["flatten_fill_proven"] is False
    assert result["final_state"]["position_quantity"] == 1
    assert api.posts == 1 and load_kill_switch(root)[0]["state"] == "HALTED"


def test_entry_session_safety_margin_blocks_before_intent(tmp_path):
    root=armed_runtime(tmp_path); store=StateStore(tmp_path/"state.db"); api=API(store,[])
    api.schedule=lambda symbol:{"sessions":[{"type":"CORE_TRADING","interval":{
        "start_time":"2026-10-04T11:00:00Z","end_time":"2026-10-04T12:04:00Z"}}]}
    broker=ControlledAcceptanceBroker(api,ACCOUNT,HASH,store)
    result=run_controlled_lifecycle(authority=authority(),runtime_root=root,
        execution_authorized=True,instrument="USDRUBF",finam_symbol="USDRUBF@RTSX",
        direction="LONG",broker=broker,clock=lambda:NOW)
    assert result["classification"] == "BLOCKED"
    assert result["failure_code"] == "STAGE8_11_ENTRY_SESSION_SAFETY_MARGIN_NOT_MET"
    assert api.posts == 0 and store.intent("stage8.11:USDRUBF:entry") is None


@pytest.mark.parametrize("uncertain", [(True,False),(False,True),(True,True)])
def test_every_uncertain_post_is_reconciled_without_retry(tmp_path, uncertain):
    result,api,store,_=run(tmp_path,[fill("o1",1),fill("o2",0)],uncertain)
    assert result["classification"] == "SYNTHETIC_PASS"
    assert api.posts == 2 and store.unresolved_intent_count() == 0


def test_entry_position_timeout_requires_operator_and_never_cancels(tmp_path):
    waiting={"position_quantity":0}
    result,api,store,root=run(
        tmp_path,[waiting] * 30, uncertain=(True,))
    assert result["classification"] == "OPERATOR_INTERVENTION_REQUIRED"
    assert result["failure_code"] == "POSITION_RECONCILIATION_TIMEOUT"
    assert api.posts == 1
    assert store.unresolved_intent_count() == 1
    assert load_kill_switch(root)[0]["state"] == "HALTED"


def test_delayed_entry_position_then_flatten_passes(tmp_path):
    result,api,store,_=run(
        tmp_path,
        [{"position_quantity":0},{"position_quantity":0},{"position_quantity":1},
         {"position_quantity":1},{"position_quantity":0}],
    )
    assert result["classification"] == "SYNTHETIC_PASS"
    assert api.posts == 2
    assert store.unresolved_intent_count() == 0


@pytest.mark.parametrize("bad_position", [-1, 2, -2])
def test_entry_unexpected_position_fails_closed_immediately(tmp_path,bad_position):
    result,api,store,_=run(tmp_path,[{"position_quantity":bad_position}])
    assert result["classification"] == "OPERATOR_INTERVENTION_REQUIRED"
    assert result["failure_code"] == "POSITION_RECONCILIATION_UNEXPECTED_QUANTITY"
    assert api.posts == 1
    assert store.unresolved_intent_count() == 1


def test_entry_rejects_unrelated_account_position(tmp_path):
    result,api,_,_=run(
        tmp_path,[{"position_quantity":1}],
        unrelated_positions=(("GLDRUBF@RTSX",1),))
    assert result["classification"] == "OPERATOR_INTERVENTION_REQUIRED"
    assert result["failure_code"] == "POSITION_RECONCILIATION_UNEXPECTED_OTHER_POSITION"
    assert api.posts == 1


def test_pre_submit_active_order_blocks_before_entry_post(tmp_path):
    result,api,store,_=run(tmp_path,[],unrelated_active=True)
    assert result["classification"] == "BLOCKED"
    assert result["failure_code"] == "STAGE8_11_PRE_SUBMIT_ACCOUNT_NOT_CLEAN"
    assert api.posts == 0
    assert store.unresolved_intent_count() == 0


def test_flatten_delayed_position_converges_to_zero(tmp_path):
    result,api,store,_=run(
        tmp_path,
        [{"position_quantity":1},
         {"position_quantity":1},{"position_quantity":1},{"position_quantity":0}],
    )
    assert result["classification"] == "SYNTHETIC_PASS"
    assert api.posts == 2
    assert store.unresolved_intent_count() == 0


def test_flatten_position_timeout_requires_operator(tmp_path):
    result,api,store,root=run(
        tmp_path,
        [{"position_quantity":1}] + [{"position_quantity":1}] * 30,
    )
    assert result["classification"] == "OPERATOR_INTERVENTION_REQUIRED"
    assert result["failure_code"] == "POSITION_RECONCILIATION_TIMEOUT"
    assert api.posts == 2
    assert store.unresolved_intent_count() == 1
    assert result["final_state"]["position_quantity"] == 1
    assert load_kill_switch(root)[0]["state"] == "HALTED"


def test_final_cleanliness_rejects_active_order_after_flatten(tmp_path):
    root=armed_runtime(tmp_path)
    store=StateStore(tmp_path/"state.db")
    api=API(store,[{"position_quantity":1},{"position_quantity":0}])
    broker=ControlledAcceptanceBroker(api,ACCOUNT,HASH,store)
    original_orders=api.orders
    calls={"n":0}
    def orders(account):
        calls["n"] += 1
        # First call is pre-submit and must be clean. Final call is dirty.
        if calls["n"] == 1:
            return {"orders":[]}
        return {"orders":[{"order_id":"late","order":{"client_order_id":"late"},
                           "status":"ORDER_STATUS_NEW"}]}
    api.orders=orders
    result=run_controlled_lifecycle(
        authority=authority(),runtime_root=root,execution_authorized=True,
        instrument="USDRUBF",finam_symbol="USDRUBF@RTSX",direction="LONG",
        broker=broker,now=NOW,sleeper=lambda _:None)
    assert result["classification"] == "OPERATOR_INTERVENTION_REQUIRED"
    assert result["failure_code"] == "FINAL_ACCOUNT_NOT_CLEAN"
    assert api.posts == 2


def test_normal_path_never_calls_order_detail_trades_or_cancel(tmp_path):
    result,api,store,_=run(
        tmp_path,[{"position_quantity":1},{"position_quantity":0}])
    assert result["classification"] == "SYNTHETIC_PASS"
    assert api.posts == 2
    assert store.unresolved_intent_count() == 0


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
    values=dict(attempt_id=STAGE8_11_ATTEMPT2_ID,
        accepted_code_commit="a"*40,sanitized_account_identity_hash=HASH,
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


@pytest.mark.parametrize("classification", [
    "PASS", "NOT_ACCEPTED_NO_EXECUTION", "OPERATOR_INTERVENTION_REQUIRED",
])
def test_evidence_requires_attempt2_identity_for_every_physical_result(classification):
    facts = evidence(physical_result_classification=classification)
    if classification != "PASS":
        facts.update(entry_fill_proven=False, one_contract_position_observed=False,
            controlled_flatten_proven=False, broker_fill_count=0)
    if classification == "OPERATOR_INTERVENTION_REQUIRED":
        facts.update(final_position_quantity=None, final_active_order_count=None,
            unresolved_intent_count=None, reconciliation_result="UNRESOLVED")
    facts.pop("attempt_id")
    with pytest.raises(ValueError, match="EVIDENCE_ATTEMPT_ID_INVALID"):
        sanitized_evidence(**facts)


def test_evidence_rejects_wrong_attempt_identity_and_accepts_exact_attempt2():
    with pytest.raises(ValueError, match="EVIDENCE_ATTEMPT_ID_INVALID"):
        sanitized_evidence(**evidence(attempt_id="operator-choice"))
    assert sanitized_evidence(**evidence())["attempt_id"] == "stage8.11.attempt2"


def test_operator_evidence_permits_unknowns_but_never_synthesizes_zero():
    facts=evidence(physical_result_classification="OPERATOR_INTERVENTION_REQUIRED",
        final_position_quantity=None,final_active_order_count=None,unresolved_intent_count=None,
        reconciliation_result="UNRESOLVED",entry_fill_proven=False,
        one_contract_position_observed=False,controlled_flatten_proven=False)
    got=sanitized_evidence(**facts)
    assert got["final_position_quantity"] is None
    assert got["final_active_order_count"] is None
    assert got["unresolved_intent_count"] is None


def test_not_accepted_evidence_requires_explicit_clean_zero_state():
    facts=evidence(physical_result_classification="NOT_ACCEPTED_NO_EXECUTION",
        order_endpoint_call_count=1,broker_fill_count=0,entry_fill_proven=False,
        one_contract_position_observed=False,controlled_flatten_proven=False)
    assert sanitized_evidence(**facts)["final_position_quantity"] == 0
    with pytest.raises(ValueError,match="NOT_ACCEPTED_EVIDENCE"):
        sanitized_evidence(**{**facts,"final_active_order_count":None})


def test_existing_live_and_readonly_airgaps(monkeypatch):
    monkeypatch.setenv("FINAM_MODE","LIVE")
    with pytest.raises(RuntimeError,match="LIVE_TRADING_NOT_AUTHORIZED"): RuntimeConfig.from_environment()
    with pytest.raises(RuntimeError,match="REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED"):
        FinamRealReadOnlyBroker(object(),"opaque").submit_order(None)
