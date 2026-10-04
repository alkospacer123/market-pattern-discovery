import json
from datetime import datetime, timezone

import pytest

from TradingSystemLab.stage8_robot.broker import FinamRealReadOnlyBroker
from TradingSystemLab.stage8_robot.config import RuntimeConfig
from TradingSystemLab.stage8_robot.controlled_real_acceptance import (
    AcceptanceAuthority, AcceptanceBlocked, ControlledAcceptanceBroker,
    STAGE8_10_AUTHORITY, precheck, run_controlled_lifecycle, sanitized_evidence,
)
from TradingSystemLab.stage8_robot.finam_api import FinamUncertainSubmission
from TradingSystemLab.stage8_robot.specification import ACTIVE_IDENTITY, PRODUCTION_SPECIFICATION_ID
from TradingSystemLab.stage8_robot.state import StateStore
from TradingSystemLab.stage8_robot.trading_safety_gate import heartbeat_path, load_kill_switch, write_kill_switch

NOW = datetime(2026, 10, 4, 12, tzinfo=timezone.utc)
HASH = "a" * 64


def authority(**changes):
    values = dict(production_specification_id=PRODUCTION_SPECIFICATION_ID,
                  active_identity=ACTIVE_IDENTITY, stage8_10_status=STAGE8_10_AUTHORITY,
                  configured_account_hash=HASH, observed_account_hash=HASH,
                  trading_token_loaded_from_current_user_dpapi=True,
                  trading_session_readonly=False, account_reconciled=True,
                  unknown_position_count=0, active_order_count=0, unresolved_intent_count=0,
                  h1_data_safety_valid=True, instrument_binding_valid=True,
                  instrument_tradable=True, r15_capacity=2, margin_capacity=2)
    values.update(changes)
    return AcceptanceAuthority(**values)


def armed_runtime(tmp_path):
    root = tmp_path / "runtime"
    write_kill_switch(root, "ARMED", allow_arm=True, now=NOW)
    path = heartbeat_path(root); path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"production_id": PRODUCTION_SPECIFICATION_ID,
        "mode": "REAL_READONLY", "health_status": "HEALTHY", "reconciliation_status": "PASS",
        "entries_enabled": False, "unresolved_order_count": 0, "failure_code": None,
        "consecutive_failures": 0, "cycle_count": 1, "account_hash": HASH,
        "timestamp": NOW.isoformat(), "last_successful_finam_api_contact": NOW.isoformat()}))
    return root


@pytest.mark.parametrize("change,code", [
    ({"configured_account_hash": "b" * 64}, "ACCOUNT_BINDING_INVALID"),
    ({"account_reconciled": False}, "RECONCILIATION_NOT_PASS"),
    ({"active_order_count": 1}, "ACTIVE_ORDERS_PRESENT"),
    ({"unresolved_intent_count": 1}, "UNRESOLVED_INTENTS_PRESENT"),
    ({"r15_capacity": 0}, "R15_CAPACITY_ZERO"),
    ({"margin_capacity": 0}, "MARGIN_CAPACITY_ZERO"),
])
def test_authority_failures_block(tmp_path, change, code):
    result = precheck(authority=authority(**change), runtime_root=armed_runtime(tmp_path),
                      now=NOW, execution_authorized=True, instrument="USDRUBF")
    assert result["decision"] == "BLOCKED" and code in result["reason_codes"]


def test_missing_false_authorization_and_non_n4_block(tmp_path):
    root = armed_runtime(tmp_path)
    for value in (False, None, "true"):
        result = precheck(authority=authority(), runtime_root=root, now=NOW,
                          execution_authorized=value, instrument="NOT_N4")
        assert "EXECUTION_NOT_AUTHORIZED" in result["reason_codes"]
        assert "INSTRUMENT_NOT_FROZEN_N4" in result["reason_codes"]


def test_halted_missing_malformed_and_unhealthy_heartbeat_block(tmp_path):
    root = armed_runtime(tmp_path)
    write_kill_switch(root, "HALTED", now=NOW)
    assert "KILL_SWITCH_HALTED" in precheck(authority=authority(), runtime_root=root, now=NOW,
        execution_authorized=True, instrument="USDRUBF")["reason_codes"]
    root = tmp_path / "missing"
    assert "KILL_SWITCH_MISSING" in precheck(authority=authority(), runtime_root=root, now=NOW,
        execution_authorized=True, instrument="USDRUBF")["reason_codes"]
    root = armed_runtime(tmp_path / "bad")
    heartbeat_path(root).write_text("{}")
    result = precheck(authority=authority(), runtime_root=root, now=NOW,
                      execution_authorized=True, instrument="USDRUBF")
    assert result["decision"] == "BLOCKED" and "HEARTBEAT_NOT_HEALTHY" in result["reason_codes"]


class API:
    def __init__(self, store=None, uncertain=False):
        self.calls=[]; self.store=store; self.uncertain=uncertain
    def place_order(self, account, payload):
        assert self.store.unresolved_intent_count() >= 1  # durable before POST
        self.calls.append((account, payload))
        if self.uncertain: raise FinamUncertainSubmission("RECONCILIATION_REQUIRED")
        return {"order_id": f"o{len(self.calls)}"}
    def cancel_order(self, account, oid): self.calls.append(("cancel", oid)); return {"status":"CANCELLED"}


def test_quantity_one_serialization_persistence_and_second_entry_impossible(tmp_path):
    store=StateStore(tmp_path / "state.db"); api=API(store); broker=ControlledAcceptanceBroker(api,"opaque",store)
    broker.submit_entry(key="entry",finam_symbol="USDRUBF@RTSX",direction="LONG")
    assert api.calls[0][1]["quantity"] == {"value":"1"}
    assert len(api.calls[0][1]["client_order_id"]) <= 20
    with pytest.raises(AcceptanceBlocked, match="SECOND_ENTRY_FORBIDDEN"):
        broker.submit_entry(key="entry2",finam_symbol="USDRUBF@RTSX",direction="LONG")
    with pytest.raises(AcceptanceBlocked, match="QUANTITY_MUST_EQUAL_ONE"):
        broker._payload(__import__("TradingSystemLab.stage8_robot.broker",fromlist=["OrderRequest"]).OrderRequest("x","s","LONG",2))


def test_uncertain_post_has_zero_retry_and_cannot_retransmit(tmp_path):
    store=StateStore(tmp_path / "state.db"); api=API(store, uncertain=True)
    broker=ControlledAcceptanceBroker(api,"opaque",store)
    with pytest.raises(FinamUncertainSubmission): broker.submit_entry(key="entry",finam_symbol="x",direction="LONG")
    assert len(api.calls) == 1 and store.intent("entry")["status"] == "UNCERTAIN"
    with pytest.raises(AcceptanceBlocked): broker._post_once(
        __import__("TradingSystemLab.stage8_robot.broker",fromlist=["OrderRequest"]).OrderRequest("entry","x","LONG",1))
    assert len(api.calls) == 1


def test_successful_lifecycle_flattens_reconciles_and_halts(tmp_path):
    root=armed_runtime(tmp_path); store=StateStore(tmp_path / "state.db"); api=API(store)
    broker=ControlledAcceptanceBroker(api,"opaque",store); calls=iter([1,2])
    def reconcile():
        n=next(calls)
        if n == 1: return {"position_quantity":1,"active_order_count":0,"unresolved_intent_count":1,"reconciled":True}
        store.transition_intent("stage8.11:USDRUBF:entry","RECONCILED")
        store.transition_intent("stage8.11:USDRUBF:flatten","RECONCILED")
        return {"position_quantity":0,"active_order_count":0,"unresolved_intent_count":0,"reconciled":True}
    result=run_controlled_lifecycle(authority=authority(),runtime_root=root,execution_authorized=True,
        instrument="USDRUBF",finam_symbol="USDRUBF@RTSX",direction="LONG",broker=broker,reconcile=reconcile,now=NOW)
    assert result["classification"] == "SYNTHETIC_PASS"
    assert [x[1]["quantity"]["value"] for x in api.calls] == ["1","1"]
    assert load_kill_switch(root)[0]["state"] == "HALTED"


def test_active_order_cancel_and_failure_paths_halt(tmp_path):
    root=armed_runtime(tmp_path); store=StateStore(tmp_path / "state.db"); api=API(store)
    broker=ControlledAcceptanceBroker(api,"opaque",store); states=iter([
        {"position_quantity":0,"active_order_count":1,"unresolved_intent_count":1,"reconciled":False},
        {"position_quantity":0,"active_order_count":0,"unresolved_intent_count":1,"reconciled":False}])
    result=run_controlled_lifecycle(authority=authority(),runtime_root=root,execution_authorized=True,
        instrument="USDRUBF",finam_symbol="USDRUBF@RTSX",direction="SHORT",broker=broker,
        reconcile=lambda:next(states),now=NOW)
    assert ("cancel","o1") in api.calls and result["classification"] == "BLOCKED"
    assert load_kill_switch(root)[0]["state"] == "HALTED"


def test_existing_live_and_readonly_airgaps(monkeypatch):
    monkeypatch.setenv("FINAM_MODE","LIVE")
    with pytest.raises(RuntimeError,match="LIVE_TRADING_NOT_AUTHORIZED"): RuntimeConfig.from_environment()
    broker=FinamRealReadOnlyBroker(object(),"opaque")
    with pytest.raises(RuntimeError,match="REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED"): broker.submit_order(None)


def test_evidence_allowlist_rejects_secrets_and_non_one_quantity():
    with pytest.raises(ValueError,match="PRIVATE"): sanitized_evidence(quantity=1, account_id="private")
    with pytest.raises(ValueError,match="QUANTITY"): sanitized_evidence(quantity=2)
    report=sanitized_evidence(quantity=1,sanitized_account_identity_hash=HASH,
                              external_raw_evidence_sha256="b"*64,
                              physical_result_classification="PENDING_PHYSICAL_ACCEPTANCE")
    assert "account_id" not in report and "secret" not in report and "raw_evidence" not in report
