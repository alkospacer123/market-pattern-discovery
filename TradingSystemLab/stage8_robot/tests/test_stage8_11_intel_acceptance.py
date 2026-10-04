import hashlib, json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from TradingSystemLab.stage8_robot.stage8_11_intel_acceptance import MODE, PrecheckBlocked, precheck_only, select_candidate
from TradingSystemLab.stage8_robot.specification import PRODUCTION_SPECIFICATION_ID
from TradingSystemLab.stage8_robot.state import StateStore
from TradingSystemLab.stage8_robot.trading_safety_gate import heartbeat_path, load_kill_switch, write_kill_switch

ACCOUNT="private-account"; HASH=hashlib.sha256(ACCOUNT.encode()).hexdigest(); NOW=datetime(2026,1,2,tzinfo=timezone.utc)

class ReadOnlyAPI:
    def place_order(self,*_): pytest.fail("place_order physically unreachable")
    def cancel_order(self,*_): pytest.fail("cancel_order physically unreachable")

def runtime(tmp_path, **changes):
    root=tmp_path/"runtime"; write_kill_switch(root,"HALTED",now=NOW)
    payload={"production_id":PRODUCTION_SPECIFICATION_ID,"mode":"REAL_READONLY","health_status":"HEALTHY",
      "account_hash":HASH,"reconciliation_status":"PASS","entries_enabled":False,"unresolved_order_count":0,
      "failure_code":None,"consecutive_failures":0,"cycle_count":1,"timestamp":NOW.isoformat(),
      "last_successful_finam_api_contact":NOW.isoformat()}
    payload.update(changes); path=heartbeat_path(root); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(payload))
    (root/"state").mkdir(parents=True,exist_ok=True)
    store=StateStore(root/"state/readonly-supervisor.sqlite3"); store.close()
    return root

def funding(**changes):
    report={"funding_classification":"STAGE_8_9_FUNDING_MARGIN_VALIDATED","reason_code":"ALL_AUTHORITIES_VALID",
      "per_instrument":{"USDRUBF:LONG":{"r15_quantity":1,"margin_quantity":1,"final_quantity":1}}}
    report.update(changes); return report

def run(tmp_path, report=None, **heartbeat):
    calls=[]
    def collector(*args,**kwargs): calls.append((args,kwargs)); return report or funding()
    result=precheck_only(api=ReadOnlyAPI(),account_id=ACCOUNT,runtime_root=runtime(tmp_path,**heartbeat),direction="LONG",
      external_evidence_sha256="a"*64,accepted_commit="c"*40,funding_collector=collector,now=NOW)
    return result,calls

def test_default_boundary_is_precheck_only_and_order_incapable(tmp_path):
    result,calls=run(tmp_path)
    assert result["mode"]==MODE and result["order_endpoint_call_count"]==result["real_order_count"]==0
    assert result["kill_switch_observed"]=="HALTED" and result["execution_authorization_observed"] is False
    assert load_kill_switch(tmp_path/"runtime")[0]["state"]=="HALTED"
    assert calls[0][1]["required_readonly"] is False
    assert result["safety_gate_reason_codes"]==["KILL_SWITCH_HALTED","EXECUTION_NOT_AUTHORIZED"]
    assert result["canonical_unresolved_intents"]==0

@pytest.mark.parametrize("report, heartbeat, code",[
    (None,{"account_hash":"b"*64},"ACCOUNT_MISMATCH"),
    (None,{"reconciliation_status":"FAIL"},"SAFETY_GATE_BLOCKED"),
    (None,{"unresolved_order_count":1},"SAFETY_GATE_BLOCKED"),
    (funding(funding_classification="BLOCKED",reason_code="TOKEN_NOT_WRITE_CAPABLE"),{},"TRADING_TOKEN_READONLY"),
    (funding(funding_classification="BLOCKED",reason_code="ACTIVE_ORDERS_PRESENT"),{},"ACTIVE_ORDERS"),
    (funding(funding_classification="BLOCKED",reason_code="PRODUCTION_REGISTRY_BINDING_MISMATCH"),{},"FUNDING_AUTHORITY"),
])
def test_authority_failures_block(tmp_path,report,heartbeat,code):
    with pytest.raises(PrecheckBlocked,match=code): run(tmp_path,report,**heartbeat)

@pytest.mark.parametrize("case",[
    {"r15_quantity":0,"margin_quantity":1,"final_quantity":0},
    {"r15_quantity":1,"margin_quantity":0,"final_quantity":0},
])
def test_zero_capacity_blocks(case):
    with pytest.raises(PrecheckBlocked,match="INSUFFICIENT_CAPACITY"):
        select_candidate({"per_instrument":{"USDRUBF:LONG":case}},"LONG")

def test_frozen_order_not_performance_and_report_is_sanitized(tmp_path):
    cases={f"{x}:LONG":{"r15_quantity":2,"margin_quantity":2,"final_quantity":2,"pf":999} for x in ("CNYRUBF","USDRUBF")}
    result,_=run(tmp_path,funding(per_instrument=cases))
    assert result["selected_n4_instrument"]=="USDRUBF" and result["stage8_11_acceptance_quantity"]==1
    encoded=json.dumps(result)
    assert ACCOUNT not in encoded and "api_secret" not in encoded and "jwt" not in encoded and "pf" not in encoded

def test_dpapi_failure_is_required_by_cli_source():
    from TradingSystemLab.stage8_robot import stage8_11_intel_acceptance as module
    assert "STAGE8_11_DPAPI_AUTHORITY_INVALID" in open(module.__file__,encoding="utf-8").read()

def test_routine_entrypoints_remain_unaffected():
    from pathlib import Path
    root=Path(__file__).parents[1]
    for name in ("runner.py","readonly_supervisor.py","deploy/windows/run-readonly.ps1","deploy/windows/install-task.ps1"):
        assert "stage8_11_intel_acceptance" not in (root/name).read_text(encoding="utf-8")

@pytest.mark.parametrize("change",[
    {"health_status":"UNHEALTHY"},{"timestamp":(NOW-timedelta(seconds=901)).isoformat()},
    {"last_successful_finam_api_contact":(NOW-timedelta(seconds=901)).isoformat()},
    {"production_id":"wrong"},{"mode":"wrong"},{"entries_enabled":True},{"failure_code":"LATCH"},
    {"consecutive_failures":1},{"cycle_count":0},{"timestamp":(NOW+timedelta(seconds=61)).isoformat()},
    {"last_successful_finam_api_contact":(NOW+timedelta(seconds=61)).isoformat()},
])
def test_complete_existing_safety_gate_blocks(tmp_path,change):
    with pytest.raises(PrecheckBlocked,match="SAFETY_GATE_BLOCKED"): run(tmp_path,**change)

@pytest.mark.parametrize("status,passes",[("INTENT_PERSISTED",False),("UNCERTAIN",False),("ACK",False),
                                            ("FILL",False),("RECONCILED",True)])
def test_canonical_intent_terminal_semantics(tmp_path,status,passes):
    root=runtime(tmp_path); store=StateStore(root/"state/readonly-supervisor.sqlite3")
    store.persist_intent("intent",{}); store.transition_intent("intent",status); store.close()
    kwargs=dict(api=ReadOnlyAPI(),account_id=ACCOUNT,runtime_root=root,direction="LONG",
                external_evidence_sha256="a"*64,accepted_commit="c"*40,funding_collector=lambda *_a,**_k:funding(),now=NOW)
    if passes: assert precheck_only(**kwargs)["canonical_unresolved_intents"]==0
    else:
        with pytest.raises(PrecheckBlocked,match="CANONICAL_UNRESOLVED"): precheck_only(**kwargs)

@pytest.mark.parametrize("kind",["missing","malformed","schema"])
def test_canonical_database_failure_blocks(tmp_path,kind):
    root=runtime(tmp_path); db=root/"state/readonly-supervisor.sqlite3"; db.unlink()
    if kind=="malformed": db.write_text("not sqlite")
    elif kind=="schema":
        import sqlite3
        connection=sqlite3.connect(db); connection.execute("CREATE TABLE other(value TEXT)"); connection.close()
    with pytest.raises(PrecheckBlocked,match="CANONICAL_INTENTS_INVALID"):
        precheck_only(api=ReadOnlyAPI(),account_id=ACCOUNT,runtime_root=root,direction="LONG",
          external_evidence_sha256="a"*64,accepted_commit="c"*40,funding_collector=lambda *_a,**_k:funding(),now=NOW)

@pytest.mark.parametrize("mutation",["missing","mismatch","nontradable"])
def test_frozen_registry_binding_failure_blocks(tmp_path,mutation):
    registry=tmp_path/"registry.csv"; source=Path("TradingSystemLab/stage8_robot/production_instrument_registry.csv").read_text()
    if mutation=="missing": source="\n".join(line for line in source.splitlines() if not line.startswith("USDRUBF,"))+"\n"
    elif mutation=="mismatch": source=source.replace("AUTHENTICATED_REAL_READONLY","BLOCKED_UNAUTHENTICATED",1)
    else: source=source.replace(",TRADABLE,",",BLOCKED,",1)
    registry.write_text(source)
    root=runtime(tmp_path)
    with pytest.raises(PrecheckBlocked,match="FROZEN_REGISTRY_BINDING_INVALID"):
        precheck_only(api=ReadOnlyAPI(),account_id=ACCOUNT,runtime_root=root,direction="LONG",
          external_evidence_sha256="a"*64,accepted_commit="c"*40,funding_collector=lambda *_a,**_k:funding(),now=NOW,registry_path=registry)

def test_windows_clock_validation_is_read_only_and_fail_closed():
    wrapper=Path("TradingSystemLab/stage8_robot/deploy/windows/run-stage8-11-intel-precheck.ps1").read_text()
    assert "Get-Service -Name W32Time" in wrapper and "w32tm /query /status" in wrapper and "w32tm /query /source" in wrapper
    assert "Local CMOS Clock|Free-running System Clock" in wrapper and "$clock = (Get-Date)" not in wrapper
