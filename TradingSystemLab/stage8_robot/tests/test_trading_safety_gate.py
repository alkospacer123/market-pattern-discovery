import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
from TradingSystemLab.stage8_robot.specification import PRODUCTION_SPECIFICATION_ID
from TradingSystemLab.stage8_robot.trading_safety_gate import *

NOW=datetime(2030,1,1,tzinfo=timezone.utc)
def hb(**changes):
    value={"production_id":PRODUCTION_SPECIFICATION_ID,"mode":"REAL_READONLY","health_status":"HEALTHY","reconciliation_status":"PASS",
      "entries_enabled":False,"unresolved_order_count":0,"failure_code":None,"consecutive_failures":0,"cycle_count":1,"timestamp":NOW.isoformat(),
      "last_successful_finam_api_contact":NOW.isoformat(),"account_hash":"A"*64}; value.update(changes); return value
def put_hb(root,value):
    p=root/"diagnostics"/"stage8-heartbeat.json";p.parent.mkdir(parents=True);p.write_text(json.dumps(value))
def test_open_requires_both_keys_and_healthy_heartbeat(tmp_path):
    write_kill_switch(tmp_path,"ARMED",allow_arm=True,now=NOW);put_hb(tmp_path,hb())
    assert evaluate_new_entry_gate(runtime_root=tmp_path,now=NOW)["decision"]=="BLOCKED"
    assert evaluate_new_entry_gate(runtime_root=tmp_path,now=NOW,execution_authorized=True)["decision"]=="OPEN"
@pytest.mark.parametrize("change,code",[
 ({"production_id":"x"},"HEARTBEAT_PRODUCTION_ID_MISMATCH"),({"mode":"x"},"HEARTBEAT_MODE_INVALID"),({"health_status":"x"},"HEARTBEAT_NOT_HEALTHY"),
 ({"reconciliation_status":"x"},"RECONCILIATION_NOT_PASS"),({"entries_enabled":True},"OBSERVER_ENTRIES_ENABLED"),({"unresolved_order_count":1},"UNRESOLVED_ORDERS_PRESENT"),
 ({"failure_code":"x"},"FAILURE_LATCH_PRESENT"),({"consecutive_failures":1},"CONSECUTIVE_FAILURES_NONZERO"),({"cycle_count":0},"CYCLE_COUNT_INVALID"),
 ({"timestamp":(NOW-timedelta(seconds=901)).isoformat()},"HEARTBEAT_STALE"),({"timestamp":(NOW+timedelta(seconds=61)).isoformat()},"HEARTBEAT_CLOCK_SKEW"),
 ({"last_successful_finam_api_contact":(NOW-timedelta(seconds=901)).isoformat()},"FINAM_CONTACT_STALE"),
 ({"last_successful_finam_api_contact":(NOW+timedelta(seconds=61)).isoformat()},"FINAM_CONTACT_CLOCK_SKEW"),({"account_hash":"x"},"ACCOUNT_HASH_INVALID")])
def test_heartbeat_failures(tmp_path,change,code):
    write_kill_switch(tmp_path,"ARMED",allow_arm=True,now=NOW);put_hb(tmp_path,hb(**change)); result=evaluate_new_entry_gate(runtime_root=tmp_path,now=NOW,execution_authorized=True)
    assert not result["entry_gate_open"] and code in result["reason_codes"]
def test_missing_malformed_halted_and_arm_boundary(tmp_path):
    assert "KILL_SWITCH_MISSING" in evaluate_new_entry_gate(runtime_root=tmp_path,now=NOW)["reason_codes"]
    p=tmp_path/"safety"/KILL_SWITCH_FILENAME;p.parent.mkdir();p.write_text("{")
    assert "KILL_SWITCH_INVALID" in evaluate_new_entry_gate(runtime_root=tmp_path,now=NOW)["reason_codes"]
    with pytest.raises(PermissionError,match=ARM_NOT_AUTHORIZED): write_kill_switch(tmp_path,"ARMED")
    emergency_halt(tmp_path,now=NOW);put_hb(tmp_path,hb())
    assert "KILL_SWITCH_HALTED" in evaluate_new_entry_gate(runtime_root=tmp_path,now=NOW,execution_authorized=True)["reason_codes"]
def test_emergency_halt_repairs_and_is_atomic(tmp_path,monkeypatch):
    calls=[]; real=os.replace; monkeypatch.setattr(os,"replace",lambda a,b:(calls.append((a,b)),real(a,b))[1])
    emergency_halt(tmp_path,now=NOW); p=tmp_path/"safety"/KILL_SWITCH_FILENAME;p.write_text("bad");emergency_halt(tmp_path,now=NOW)
    write_kill_switch(tmp_path,"ARMED",allow_arm=True,now=NOW); emergency_halt(tmp_path,now=NOW); state,error=load_kill_switch(tmp_path)
    assert not error and state["state"]=="HALTED" and len(calls)==4
def test_repository_output_rejected():
    with pytest.raises(ValueError,match=REPOSITORY_OUTPUT_FORBIDDEN): emergency_halt(REPOSITORY_ROOT)
