from datetime import datetime,timedelta
from decimal import Decimal
import importlib.util,json,sys
from pathlib import Path
from zoneinfo import ZoneInfo
import pytest

from TradingSystemLab.stage8_robot.broker import DryRunBroker,OrderRequest
from TradingSystemLab.stage8_robot.config import RuntimeConfig
from TradingSystemLab.stage8_robot.reconciliation import Reconciliation,reconcile
from TradingSystemLab.stage8_robot.risk import ContractEconomics,size_position
from TradingSystemLab.stage8_robot.runner import RobotRunner
from TradingSystemLab.stage8_robot.specification import ACTIVE_IDENTITY,load_frozen_specification
from TradingSystemLab.stage8_robot.state import StateStore
from TradingSystemLab.stage8_robot.strategy_core import CompletedBar,DecisionCore,PositionState,T3Context,order_events
from TradingSystemLab.stage8_robot.trail1_state import Trail1State

MSK=ZoneInfo("Europe/Moscow")
def bar(hour=10,**kw):
    values=dict(timestamp=datetime(2026,1,2,hour,tzinfo=MSK),open=100,high=106,low=99,close=105,atr=2,prior_high=104,prior_low=96)
    values.update(kw); return CompletedBar(**values)
def context(long=True): return T3Context(110 if long else 90,100,1 if long else -1,25,3,2,105,95)

def test_stage7_authentication(): assert load_frozen_specification().identity==ACTIVE_IDENTITY
@pytest.mark.parametrize("long",[True,False])
def test_t3_long_short_signal(long):
    b=bar() if long else bar(open=100,high=101,low=94,close=95,prior_low=96)
    result=DecisionCore().signal("USDRUBF",b,context(long),1)
    assert result.direction == ("LONG" if long else "SHORT") and result.initial_r==5
def test_warmup_and_no_signal():
    assert DecisionCore().signal("USDRUBF",bar(),T3Context(110,100,1,25,3,2,None,95),1) is None
    assert DecisionCore().signal("USDRUBF",bar(close=103),context(),1) is None

def authoritative_trail_class():
    p=Path("TradingSystemLab/results/post_v3_analysis/stage5_structural_validation/stage5_trail1_execution.py")
    s=importlib.util.spec_from_file_location("authenticated_trail1",p); m=importlib.util.module_from_spec(s)
    sys.modules[s.name]=m; s.loader.exec_module(m); return m.Trail1State
@pytest.mark.parametrize("direction,entry,stop,high,low,candidate",[("LONG",100,95,106,99,101),("SHORT",100,105,101,94,99)])
def test_trail1_direct_conformance(direction,entry,stop,high,low,candidate):
    frozen=authoritative_trail_class()(direction,entry,stop); prod=Trail1State(direction,entry,stop)
    for obj in (frozen,prod):
        assert obj.observe_completed_bar("t1",high,low,candidate,stop); assert obj.activate_before_event("t1",stop)==stop
        activated=obj.activate_before_event("t2",stop); assert obj.activated
        assert obj.candidate_after_bar(activated,candidate)==activated
    assert vars(frozen)==vars(prod)
def test_trail_never_triggers_candidate_looser_and_gap():
    s=Trail1State("LONG",100,95); assert not s.observe_completed_bar("t1",104,98,94,95)
    assert s.observe_completed_bar("t2",105,99,94,95) and s.candidate_already_looser
    assert s.activate_before_event("t3",95)==95
    assert s.stop_fill(90,95)==90 and s.gap_through_activated_trail
def test_position_stop_before_extreme_and_delayed_activation():
    s=Trail1State("LONG",100,95); p=PositionState("USDRUBF","LONG",100,95,95,100,s); core=DecisionCore()
    assert core.manage(p,bar(high=106,low=99,close=105))["event"]=="HOLD" and s.triggered and not s.activated
    out=core.manage(p,bar(hour=11,open=99,high=100,low=98,close=99)); assert s.activated and out["event"]=="EXIT"
def test_event_order_exit_before_entry_and_identity():
    es=[{"timestamp":"t","type":"ENTRY","identity":"A"},{"timestamp":"t","type":"EXIT","identity":"Z"},{"timestamp":"t","type":"EXIT","identity":"A"}]
    assert [(x["type"],x["identity"]) for x in order_events(es)]==[("EXIT","A"),("EXIT","Z"),("ENTRY","A")]
def test_r15_full_no_equal_split_and_conservative_rounding():
    x=size_position(Decimal("100000"),Decimal("100"),Decimal("95"),ContractEconomics(Decimal("1"),Decimal("100"),1,True))
    assert x.risk_cash==Decimal("1500.000") and x.quantity==3
def test_reconciliation_states():
    assert reconcile([],[],[],[]) is Reconciliation.RECONCILED
    assert reconcile([],[{"contract_id":"x","quantity":1}],[],[]) is Reconciliation.UNKNOWN_BROKER_POSITION
def test_state_idempotency_and_restart(tmp_path):
    s=StateStore(tmp_path/"s.db"); assert s.persist_intent("key",{"quantity":2}); assert not s.persist_intent("key",{"quantity":2})
    assert StateStore(tmp_path/"s.db").intent("key")["status"]=="INTENT_PERSISTED"
def test_dry_run_never_transmits_and_duplicate_blocked(tmp_path):
    cfg=RuntimeConfig(tmp_path/"s.db",tmp_path/"a.jsonl","100000","none")
    runner=RobotRunner(cfg); assert runner.startup() is Reconciliation.RECONCILED
    req=OrderRequest("key","contract","LONG",1); first=runner.persist_then_submit({"signal_id":"s"},req)
    assert first["transmitted"] is False and runner.persist_then_submit({"signal_id":"s"},req)["status"]=="INTENT_PERSISTED"
def test_live_default_off(monkeypatch):
    monkeypatch.setenv("STARTING_REALIZED_EQUITY","1"); monkeypatch.delenv("LIVE_TRADING_ENABLED",raising=False)
    assert RuntimeConfig.from_environment().live_trading_enabled is False
def test_registry_is_explicitly_blocked():
    text=Path("TradingSystemLab/stage8_robot/production_instrument_registry.csv").read_text()
    assert text.count("BLOCKED_UNAUTHENTICATED")==4 and not any(x in text for x in ("api_key=","secret=","password="))
def test_golden_fixture_manifest_has_twelve_cases():
    data=json.loads(Path("TradingSystemLab/stage8_robot/tests/golden_fixtures.json").read_text())
    assert len(data)==12 and all(x["provenance"] for x in data)
