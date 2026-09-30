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
    assert DecisionCore().signal("USDRUBF",bar(),T3Context(110,float("nan"),1,25,3,2,None,95),1) is None
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
    assert first["transmitted"] is False and runner.persist_then_submit({"signal_id":"s"},req)["status"]=="ACK"
def test_live_default_off(monkeypatch):
    monkeypatch.setenv("STARTING_REALIZED_EQUITY","1"); monkeypatch.delenv("LIVE_TRADING_ENABLED",raising=False)
    assert RuntimeConfig.from_environment().live_trading_enabled is False
def test_registry_is_explicitly_blocked():
    text=Path("TradingSystemLab/stage8_robot/production_instrument_registry.csv").read_text()
    assert text.count("BLOCKED_UNAUTHENTICATED")==4 and not any(x in text for x in ("api_key=","secret=","password="))
def test_golden_fixture_manifest_has_twelve_cases():
    data=json.loads(Path("TradingSystemLab/stage8_robot/tests/golden_fixtures.json").read_text())
    assert len(data)==12 and all(x["provenance"] for x in data)

def test_perpetual_registry_has_no_expiry():
    from TradingSystemLab.stage8_robot.instrument_resolver import load_registry,PERPETUAL_FUTURE
    rows=load_registry(Path("TradingSystemLab/stage8_robot/production_instrument_registry.csv"))
    assert len(rows)==4 and all(x.instrument_type==PERPETUAL_FUTURE and x.expiry is None and x.automatic_prolongation for x in rows)

def test_binding_mismatch_blocks():
    from TradingSystemLab.stage8_robot.instrument_resolver import validate_finam_binding
    result=validate_finam_binding("USDRUBF",{}, {}, {})
    assert result.status!="AUTHENTICATED_DEMO_TRADABLE"

def test_context_blocks_reset_at_local_day_and_incomplete_rejected():
    import pandas as pd
    from TradingSystemLab.stage8_robot.context_builder import T3ContextBuilder
    idx=pd.DatetimeIndex([datetime(2026,1,2,h,tzinfo=MSK) for h in (10,11,12,13,14)]+[datetime(2026,1,3,h,tzinfo=MSK) for h in (10,11,12,13)])
    f=pd.DataFrame({"Open":range(9),"High":range(1,10),"Low":range(9),"Close":range(1,10)},index=idx)
    execution,ctx=T3ContextBuilder().build(f,datetime(2026,1,4,tzinfo=MSK))
    assert list(ctx.index)==[idx[3],idx[8]] and ctx.iloc[0].Open==0 and ctx.iloc[1].Open==5
    assert execution.PriorHigh.isna().all()

def test_donchian_is_shifted_one():
    import pandas as pd
    from TradingSystemLab.stage8_robot.context_builder import T3ContextBuilder
    idx=pd.date_range("2026-01-01 01:00",periods=21,freq="h",tz=MSK)
    f=pd.DataFrame({"Open":range(1,22),"High":range(2,23),"Low":range(1,22),"Close":range(1,22)},index=idx)
    execution,_=T3ContextBuilder().build(f,datetime(2026,1,2,tzinfo=MSK))
    assert execution.PriorHigh.iloc[19]!=execution.PriorHigh.iloc[19] and execution.PriorHigh.iloc[20]==21

def test_state_is_bound_to_environment_and_account(tmp_path):
    p=tmp_path/"bound.db"; StateStore(p,{"environment":"DEMO","account":"hash-a"})
    with pytest.raises(RuntimeError,match="STATE_ENVIRONMENT_ACCOUNT_MISMATCH"): StateStore(p,{"environment":"LIVE","account":"hash-a"})

def test_live_mode_is_impossible(monkeypatch):
    monkeypatch.setenv("STARTING_REALIZED_EQUITY","1"); monkeypatch.setenv("FINAM_MODE","LIVE")
    with pytest.raises(RuntimeError,match="LIVE_TRADING_NOT_AUTHORIZED"): RuntimeConfig.from_environment()

def test_conformance_reports_two_exact_independent_replays():
    report=json.loads(Path("TradingSystemLab/stage8_robot/conformance_report.json").read_text())
    assert report["status"]=="STAGE_8_FINAM_DEMO_BINDING_READY_AWAITING_OPERATOR_CREDENTIALS"
    for name in ("authority_replay","production_robot_replay"):
        assert report[name]["status"]=="PASS" and report[name]["expected_trade_count"]==report[name]["reproduced_trade_count"]==report[name]["exact_matches"]==418

def test_finam_session_schema_and_secret_redaction():
    from io import BytesIO
    from TradingSystemLab.stage8_robot.finam_api import FinamAPI,RateLimiter
    seen=[]
    class R(BytesIO):
        status=200; headers={}
    def transport(req,timeout): seen.append(req); return R(b'{"token":"jwt-value"}')
    api=FinamAPI("top-secret",transport=transport,limiter=RateLimiter(199)); assert api.create_session()=={}
    assert json.loads(seen[0].data)=={"secret":"top-secret"} and "top-secret" not in repr(api) and "jwt-value" not in repr(api)

def test_finam_endpoint_and_order_schema():
    from TradingSystemLab.stage8_robot.finam_api import SESSION_DETAILS_PATH,H1_TIMEFRAME,BARS_PATH_TEMPLATE
    from TradingSystemLab.stage8_robot.broker import broker_side,compact_client_order_id
    assert SESSION_DETAILS_PATH=="/v1/sessions/details" and H1_TIMEFRAME=="TIME_FRAME_H1"
    assert BARS_PATH_TEMPLATE=="/v1/instruments/{symbol}/bars"
    assert broker_side("LONG")=="SIDE_BUY" and broker_side("SHORT",exit_order=True)=="SIDE_BUY"
    assert compact_client_order_id("x")==compact_client_order_id("x") and len(compact_client_order_id("x"))==20

def test_finam_transport_schema_uses_token_account_ids_and_interval_query():
    from io import BytesIO
    from urllib.parse import urlparse,parse_qs
    from TradingSystemLab.stage8_robot.finam_api import FinamAPI,RateLimiter
    seen=[]
    class R(BytesIO): status=200; headers={}
    replies=[b'{"token":"jwt"}',b'{"account_ids":["demo"]}',b'{"bars":[]}']
    def transport(req,timeout): seen.append(req); return R(replies.pop(0))
    api=FinamAPI("secret",transport=transport,limiter=RateLimiter(199)); api.create_session(); details=api.session_details(); api.bars("X","a","b")
    assert json.loads(seen[1].data)=={"token":"jwt"} and details["account_ids"]==["demo"]
    query=parse_qs(urlparse(seen[2].full_url).query)
    assert query=={"timeframe":["TIME_FRAME_H1"],"interval.start_time":["a"],"interval.end_time":["b"]}

def test_production_replay_has_no_research_shortcut():
    import ast
    source=Path("TradingSystemLab/stage8_robot/production_replay.py").read_text(); tree=ast.parse(source)
    prohibited={"run_t3","_dispatch","raw_replays"}
    assert not any(isinstance(n,(ast.Import,ast.ImportFrom)) and "stage5" in ast.unparse(n) for n in ast.walk(tree))
    assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in prohibited for n in ast.walk(tree))

def test_client_order_ids_have_no_collisions():
    from TradingSystemLab.stage8_robot.broker import compact_client_order_id
    ids=[compact_client_order_id(f"TRAIL1:{i}:USDRUBF:2026-01-{i%28+1:02d}") for i in range(10000)]
    assert len(ids)==len(set(ids)) and all(len(x)<=20 for x in ids)

def test_realized_equity_restored_and_mismatch_blocked(tmp_path):
    cfg=RuntimeConfig(tmp_path/"s.db",tmp_path/"a","100000","none")
    first=RobotRunner(cfg); first.book_exit(Decimal("100"),Decimal("2"),Decimal("1"))
    assert RobotRunner(cfg).realized_equity==Decimal("100097")
    with pytest.raises(RuntimeError,match="STARTING_EQUITY_STATE_MISMATCH"):
        RobotRunner(RuntimeConfig(tmp_path/"s.db",tmp_path/"a","99999","none"))

def test_fill_durability_and_unique_id(tmp_path):
    store=StateStore(tmp_path/"s.db"); fill={"fill_id":"f","broker_order_id":"o","trade_id":"t","quantity":"1","price":"2","fee":".1","timestamp":"2026-01-01T00:00:00Z"}
    assert store.persist_fill(fill) and not store.persist_fill(fill)

# Current FINAM REST binding contract: exact names, protobuf Decimal/Bool wrappers.
def binding_fixture():
    import copy
    data=json.loads(Path("TradingSystemLab/stage8_robot/tests/finam_binding_fixtures.json").read_text())
    return copy.deepcopy(data)

def validate_fixture(code, data=None):
    from TradingSystemLab.stage8_robot.instrument_resolver import validate_finam_binding
    data=data or binding_fixture(); asset=data["assets"][("USDRUBF","CNYRUBF","GLDRUBF","IMOEXF").index(code)]
    return validate_finam_binding(code,asset,data["params"],data["schedule"],data["account_assets"][code])

@pytest.mark.parametrize("value,expected",[(1,"1"),("1.25","1.25"),({"num":"125","scale":2},"1.25"),(0,"0")])
def test_finam_decimal_parser(value,expected):
    from TradingSystemLab.stage8_robot.instrument_resolver import finam_decimal
    assert str(finam_decimal(value))==expected
@pytest.mark.parametrize("value",[-1,{"num":"x","scale":2},{"num":"1"},None,1.2])
def test_finam_decimal_parser_rejects_invalid_positive(value):
    from TradingSystemLab.stage8_robot.instrument_resolver import finam_decimal
    with pytest.raises(ValueError): finam_decimal(value,positive=True)
@pytest.mark.parametrize("value,expected",[(True,True),(False,False),({"value":True},True),({"value":False},False),({},None),(None,None)])
def test_finam_bool_wrapper(value,expected):
    from TradingSystemLab.stage8_robot.instrument_resolver import finam_bool
    assert finam_bool(value) is expected
@pytest.mark.parametrize("code",["USDRUBF","CNYRUBF","GLDRUBF","IMOEXF"])
def test_all_four_sanitized_finam_bindings(code):
    x=validate_fixture(code); assert x.status=="AUTHENTICATED_DEMO_TRADABLE" and not x.validation_errors
    assert x.tick_value_source=="MOEX" and x.quantity_semantics.startswith("quantity.value is a number of futures contracts")

def test_exact_discovery_and_ambiguity():
    from TradingSystemLab.stage8_robot.instrument_resolver import discover_finam_asset
    d=binding_fixture(); assert discover_finam_asset("USDRUBF",d["assets"])[0]["id"]=="sec-usd"
    wrong=[{**d["assets"][0],"ticker":"USD"}]; assert discover_finam_asset("USDRUBF",wrong)[1]=="BLOCKED_NOT_FOUND"
    assert discover_finam_asset("USDRUBF",[d["assets"][0],{**d["assets"][0],"id":"other"}])[1]=="BLOCKED_AMBIGUOUS_FINAM_ASSET"

@pytest.mark.parametrize("mutation,expected",[
 ("wrong_ticker","BLOCKED_IDENTITY_MISMATCH"),("wrong_mic","BLOCKED_IDENTITY_MISMATCH"),("wrong_type","BLOCKED_INSTRUMENT_TYPE_MISMATCH"),
 ("archived","BLOCKED_INSTRUMENT_DISABLED"),("wrong_decimals","BLOCKED_PRICE_STEP_MISMATCH"),("wrong_min_step","BLOCKED_PRICE_STEP_MISMATCH"),
 ("wrong_lot","BLOCKED_CONTRACT_ECONOMICS_MISMATCH"),("wrong_contract","BLOCKED_CONTRACT_ECONOMICS_MISMATCH"),("missing_future","BLOCKED_CONTRACT_ECONOMICS_MISMATCH"),
 ("currency","BLOCKED_CURRENCY_MISMATCH"),("not_tradable","BLOCKED_NOT_TRADABLE"),("missing_tradable","BLOCKED_NOT_TRADABLE"),
 ("zero_trade_lot","BLOCKED_PARAMS_INVALID"),("missing_trade_lot","BLOCKED_PARAMS_INVALID"),("schedule","BLOCKED_SCHEDULE_INVALID"),
 ("missing_symbol","BLOCKED_IDENTITY_MISMATCH"),("missing_id","BLOCKED_IDENTITY_MISMATCH")])
def test_binding_negative_mutations(mutation,expected):
    d=binding_fixture(); a=d["assets"][0]; aa=d["account_assets"]["USDRUBF"]
    if mutation=="wrong_ticker": a["ticker"]="USD"
    elif mutation=="wrong_mic": a["mic"]="XXXX"
    elif mutation=="wrong_type": a["type"]="ASSET_TYPE_SHARE"
    elif mutation=="archived": a["is_archived"]=True
    elif mutation=="wrong_decimals": aa["decimals"]=3
    elif mutation=="wrong_min_step": aa["min_step"]={"num":"2","scale":0}
    elif mutation=="wrong_lot": aa["lot_size"]={"num":"2","scale":0}
    elif mutation=="wrong_contract": aa["future_details"]["contract_size"]={"num":"999","scale":0}
    elif mutation=="missing_future": aa.pop("future_details")
    elif mutation=="currency": aa["currency"]="USD"
    elif mutation=="not_tradable": d["params"]["is_tradable"]={"value":False}
    elif mutation=="missing_tradable": d["params"].pop("is_tradable")
    elif mutation=="zero_trade_lot": d["params"]["trade_lot_size"]={"num":"0","scale":0}
    elif mutation=="missing_trade_lot": d["params"].pop("trade_lot_size")
    elif mutation=="schedule": d["schedule"]={"sessions":[]}
    elif mutation=="missing_symbol": a.pop("symbol")
    elif mutation=="missing_id": a.pop("id")
    assert validate_fixture("USDRUBF",d).status==expected

def test_binding_price_derivation_exact_decimal():
    x=validate_fixture("CNYRUBF"); assert x.min_step=="1" and x.decimals==3 and x.derived_price_step=="0.001"

def test_sizing_to_finam_contract_quantity_all_four():
    from TradingSystemLab.stage8_robot.instrument_resolver import MOEX_REFERENCE
    for code in MOEX_REFERENCE:
        x=validate_fixture(code); step,tick,_=MOEX_REFERENCE[code]
        entry=Decimal("100"); stop=entry-step*10
        sized=size_position(Decimal("100000"),entry,stop,ContractEconomics(step,tick,int(Decimal(x.trade_lot_size)),True))
        expected_loss=Decimal("10")*tick
        assert sized.risk_cash==Decimal("1500.000") and sized.loss_per_contract==expected_loss
        raw=sized.risk_cash/expected_loss
        assert sized.quantity==int(raw.to_integral_value(rounding="ROUND_FLOOR")) and Decimal(sized.quantity)<=raw
        assert sized.quantity%int(Decimal(x.trade_lot_size))==0

def test_atomic_activation_rejects_three_of_four_without_change(tmp_path):
    from TradingSystemLab.stage8_robot.instrument_resolver import evidence_sha256
    from TradingSystemLab.stage8_robot.update_demo_registry import update
    records={c:validate_fixture(c).to_dict() for c in ("USDRUBF","CNYRUBF","GLDRUBF","IMOEXF")}
    records["IMOEXF"]["status"]="BLOCKED_NOT_TRADABLE"
    report={"account_verified":True,"bindings":records,"evidence_sha256":evidence_sha256(records)}
    rp=tmp_path/"e.json"; rp.write_text(json.dumps(report)); reg=tmp_path/"r.csv"
    original=Path("TradingSystemLab/stage8_robot/production_instrument_registry.csv").read_text(); reg.write_text(original)
    with pytest.raises(RuntimeError,match="ALL_FOUR"): update(rp,reg)
    assert reg.read_text()==original

def test_atomic_activation_four_of_four(tmp_path):
    from TradingSystemLab.stage8_robot.instrument_resolver import evidence_sha256
    from TradingSystemLab.stage8_robot.update_demo_registry import update
    records={c:validate_fixture(c).to_dict() for c in ("USDRUBF","CNYRUBF","GLDRUBF","IMOEXF")}
    report={"account_verified":True,"bindings":records,"evidence_sha256":evidence_sha256(records)}
    rp=tmp_path/"e.json"; rp.write_text(json.dumps(report)); reg=tmp_path/"r.csv"
    reg.write_text(Path("TradingSystemLab/stage8_robot/production_instrument_registry.csv").read_text()); update(rp,reg)
    assert reg.read_text().count("AUTHENTICATED_DEMO_TRADABLE")==4
