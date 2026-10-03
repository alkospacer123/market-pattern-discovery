"""Completely offline Stage 8.10.6 synthetic safety validation."""
from __future__ import annotations
import argparse, json, tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from .specification import PRODUCTION_SPECIFICATION_ID
from .trading_safety_gate import emergency_halt, evaluate_new_entry_gate, write_kill_switch, load_kill_switch, REPOSITORY_ROOT

REPORT_NAME = "stage8_10_6_safety_gate_validation.json"
PRODUCTION_HALT_INVALID = "STAGE8_10_6_PRODUCTION_KILL_SWITCH_NOT_HALTED"

def _heartbeat(now):
    return {"production_id":PRODUCTION_SPECIFICATION_ID,"mode":"REAL_READONLY","health_status":"HEALTHY",
            "reconciliation_status":"PASS","entries_enabled":False,"unresolved_order_count":0,"failure_code":None,
            "consecutive_failures":0,"cycle_count":1,"timestamp":now.isoformat(),
            "last_successful_finam_api_contact":now.isoformat(),"account_hash":"a"*64}
def _write(path, value):
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value),encoding="utf-8")

def validate(*, workspace: Path | None = None) -> dict:
    now=datetime(2030,1,2,tzinfo=timezone.utc)
    owner=tempfile.TemporaryDirectory() if workspace is None else None
    root=Path(owner.name if owner else workspace).resolve(); cases=[]
    def run(name, switch="ARMED", auth=True, heartbeat=None, raw_switch=None, raw_heartbeat=None):
        case=root/name
        if switch is not None: write_kill_switch(case,switch,allow_arm=True,now=now)
        if raw_switch is not None: p=case/"safety"/"stage8-trading-kill-switch.json"; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(raw_switch)
        hb=_heartbeat(now) if heartbeat is None else heartbeat
        if raw_heartbeat is not None: p=case/"diagnostics"/"stage8-heartbeat.json"; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(raw_heartbeat)
        elif hb is not False: _write(case/"diagnostics"/"stage8-heartbeat.json",hb)
        decision=evaluate_new_entry_gate(runtime_root=case,now=now,execution_authorized=auth)["decision"]
        cases.append((name,decision)); return decision
    run("missing_switch",switch=None); run("malformed_switch",switch=None,raw_switch="{")
    for name, mutation in [("wrong_schema",{"schema_id":"wrong"}),("wrong_switch_production",{"production_specification_id":"wrong"}),("unknown_state",{"state":"UNKNOWN"})]:
        run(name,raw_switch=json.dumps({"schema_id":"stage8_trading_kill_switch.v1","production_specification_id":PRODUCTION_SPECIFICATION_ID,"state":"ARMED","generation":1,"updated_utc":now.isoformat(),**mutation}))
    run("halted",switch="HALTED"); run("authorization_required",auth=False); run("positive",auth=True)
    mutations=[("heartbeat_missing",False),("heartbeat_malformed","RAW"),("heartbeat_wrong_production",{"production_id":"wrong"}),
      ("heartbeat_wrong_mode",{"mode":"LIVE"}),("unhealthy",{"health_status":"FAULT"}),("reconciliation",{"reconciliation_status":"FAIL"}),
      ("entries_enabled",{"entries_enabled":True}),("unresolved",{"unresolved_order_count":1}),("failure_latch",{"failure_code":"FAULT"}),
      ("consecutive_failures",{"consecutive_failures":1}),("cycle_count",{"cycle_count":0}),
      ("heartbeat_stale",{"timestamp":(now-timedelta(seconds=901)).isoformat()}),("heartbeat_future",{"timestamp":(now+timedelta(seconds=61)).isoformat()}),
      ("contact_stale",{"last_successful_finam_api_contact":(now-timedelta(seconds=901)).isoformat()}),
      ("contact_future",{"last_successful_finam_api_contact":(now+timedelta(seconds=61)).isoformat()}),("account_hash",{"account_hash":"bad"})]
    for name, mutation in mutations:
        if mutation is False: run(name,heartbeat=False)
        elif mutation == "RAW": run(name,heartbeat=False,raw_heartbeat="{")
        else: hb=_heartbeat(now); hb.update(mutation); run(name,heartbeat=hb)
    bad_time=_heartbeat(now); bad_time["timestamp"]="not-a-timestamp"; run("heartbeat_timestamp_invalid",heartbeat=bad_time)
    if len(cases)!=25 or sum(d=="OPEN" for _,d in cases)!=1:
        raise AssertionError("SYNTHETIC_MATRIX_INVALID")
    emergency=root/"emergency"; emergency_halt(emergency,now=now); (emergency/"safety"/"stage8-trading-kill-switch.json").write_text("{")
    emergency_halt(emergency,now=now); write_kill_switch(emergency,"ARMED",allow_arm=True,now=now); emergency_halt(emergency,now=now)
    state,error=load_kill_switch(emergency)
    if error or state["state"]!="HALTED": raise AssertionError("EMERGENCY_HALT_INVALID")
    if owner: owner.cleanup()
    return {"schema_id":"stage8_10_6_safety_gate_validation.v1","production_specification_id":PRODUCTION_SPECIFICATION_ID,
      "mode":"OFFLINE_LOCAL_SAFETY_VALIDATION","synthetic_case_count":25,"synthetic_open_case_count":1,"synthetic_blocked_case_count":24,
      "synthetic_matrix_validation":"PASS","emergency_halt_validation":"PASS","missing_switch_fail_closed":True,"malformed_switch_fail_closed":True,
      "execution_authorization_required":True,"heartbeat_health_gate_validated":True,"reconciliation_gate_validated":True,"unresolved_order_gate_validated":True,
      "heartbeat_freshness_gate_validated":True,"api_contact_freshness_gate_validated":True,"account_hash_shape_gate_validated":True,
      "real_account_id_used":False,"readonly_token_used":False,"trading_token_used":False,"finam_authentication_performed":False,"external_network_calls":0,
      "real_order_endpoint_called":False,"real_order_count":0,"live_trading_authorized":False,"real_order_transmission_authorized":False,"execution_authorized":False,
      "stage8_10_7_status":"NOT_STARTED","stage8_11_status":"NOT_STARTED_NOT_AUTHORIZED","stage8_12_status":"NOT_STARTED_NOT_AUTHORIZED"}

def add_production_halt_observation(result: dict, *, production_runtime_root: Path) -> dict:
    """Read an external switch without mutating it and add only sanitized facts."""
    root = production_runtime_root.resolve()
    if root == REPOSITORY_ROOT or REPOSITORY_ROOT in root.parents:
        raise ValueError("STAGE8_10_6_PRODUCTION_RUNTIME_IN_REPOSITORY_FORBIDDEN")
    state, error = load_kill_switch(root)
    if error or state is None or state["state"] != "HALTED":
        raise ValueError(PRODUCTION_HALT_INVALID)
    return {
        **result,
        "production_kill_switch_initialized": True,
        "production_kill_switch_final_state": "HALTED",
        "production_kill_switch_valid": True,
    }

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--runtime-root",type=Path,required=True); parser.add_argument("--production-runtime-root",type=Path,required=True); parser.add_argument("--report",type=Path,required=True); args=parser.parse_args()
    report=args.report.resolve()
    if report==REPOSITORY_ROOT or REPOSITORY_ROOT in report.parents: parser.error("STAGE8_10_6_REPOSITORY_OUTPUT_FORBIDDEN")
    try:
        result=add_production_halt_observation(validate(workspace=args.runtime_root),production_runtime_root=args.production_runtime_root)
    except ValueError as error:
        parser.error(str(error))
    report.parent.mkdir(parents=True,exist_ok=True); report.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n"); print(json.dumps(result,sort_keys=True))
if __name__=="__main__": main()
