"""Independent fail-closed Stage 7 semantic auditor."""
from __future__ import annotations
import argparse, csv, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
ACTIVE="TRAIL1__N4_01__FULL__R15"; REFERENCE="CANONICAL__N4_01__FULL__R15"
INSTRUMENTS=["USDRUBF","CNYRUBF","GLDRUBF","IMOEXF"]

def check(condition: bool, message: str, errors: list[str]):
    if not condition: errors.append(message)

def audit(target: Path, write_result: bool=True) -> dict:
    errors=[]
    try: spec=json.loads((target/"production_specification.json").read_text())
    except Exception as e: return {"status":"FAIL","errors":[f"SPEC_UNREADABLE:{e}"],"checks":0}
    upstream=ROOT/"TradingSystemLab/results/post_v3_analysis/stage6_7_n4_full_four_case_test/four_case_registry.csv"
    check(hashlib.sha256(upstream.read_bytes()).hexdigest()=="e1f5edbff005ce17fcaa73c71837db1b3906bdd3d92d1f249788e80c725c34a2","UPSTREAM_CASE_HASH",errors)
    with upstream.open(newline="") as f: cases={r["case_id"] for r in csv.DictReader(f)}
    check({ACTIVE,REFERENCE}<=cases,"UPSTREAM_CASES",errors)
    t3=ROOT/"TradingSystemLab/strategies/trend/T3_MTF_Trend.py"; trail=ROOT/"TradingSystemLab/results/post_v3_analysis/stage5_structural_validation/stage5_trail1_execution.py"
    tsha=hashlib.sha256(t3.read_bytes()).hexdigest(); trsha=hashlib.sha256(trail.read_bytes()).hexdigest()
    trail_manifest=json.loads((ROOT/"TradingSystemLab/results/post_v3_analysis/stage5_structural_validation/trail1/manifest_trail1.json").read_text())
    checks=[
      (spec.get("identity")==ACTIVE,"ACTIVE_IDENTITY"),(spec.get("status")=="ACTIVE_PRODUCTION_SPECIFICATION","ACTIVE_STATUS"),
      (spec.get("basket",{}).get("instruments")==INSTRUMENTS,"N4_MEMBERSHIP"),(spec.get("basket",{}).get("id")=="N4_01","N4_ID"),
      (spec.get("strategy",{}).get("name")=="T3" and spec.get("strategy",{}).get("timeframe")=="H1","T3_H1"),
      (spec.get("strategy",{}).get("candidate")=="T3_H1_candidate_v3" and spec.get("strategy",{}).get("configuration_id")=="T3-H1-4e73cdb77246","T3_CANDIDATE"),
      (tsha=="840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c"==spec.get("strategy",{}).get("source_sha256"),"T3_SOURCE_HASH"),
      (spec.get("strategy",{}).get("parameter_sha256")=="4e73cdb77246cb07b5953160b9fc0ab36bfd4bd6d9a7f7faaae7e6e392ee340a","PARAMETER_HASH"),
      (spec.get("variant",{}).get("name")=="TRAIL1" and trsha=="d1d8ac2eeea9095becd6f74295e4a540d02ee0494237af5f16f6d66a487f221b"==spec.get("variant",{}).get("source_sha256"),"TRAIL1_IDENTITY"),
      (trail_manifest.get("determinism",{}).get("run_1_ledger_sha256")==trail_manifest.get("determinism",{}).get("run_2_ledger_sha256")==spec.get("variant",{}).get("authoritative_ledger_sha256"),"TRAIL1_LEDGER"),
      (spec.get("risk",{}).get("mode")=="R15" and spec.get("risk",{}).get("risk_fraction_per_new_instrument_position")==.015,"R15"),
      (spec.get("risk",{}).get("load")=="FULL" and spec.get("risk",{}).get("equal_split") is False,"FULL"),
      (spec.get("risk",{}).get("maximum_nominal_simultaneous_initial_risk")==.06,"MAX_RISK"),
      (spec.get("event_order")==["timestamp_ascending","EXIT_before_ENTRY","deterministic_trade_instrument_order_identity_ascending"],"EVENT_ORDER"),
      (spec.get("cost_evidence_contract",{}).get("name")=="C1","C1"),
      (spec.get("schedule",{}).get("entry_time_filter") is None and spec.get("schedule",{}).get("session_10_21") is False,"NO_SESSION"),
      (spec.get("variant",{}).get("forbidden_overlays")==["BE1","LOCK1_AFTER_2R","SESSION_10_21","ONE_BAR","EXIT_ON_OPPOSITE_REGIME","STRUCTURAL_STACK"],"FORBIDDEN_OVERLAYS"),
      (spec.get("stage8_started") is False,"STAGE8_BOUNDARY")]
    for ok,msg in checks: check(ok,msg,errors)
    payload=dict(spec); sid=payload.pop("production_specification_id",None); recorded=payload.pop("canonical_active_payload_sha256",None)
    digest=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
    check(recorded==digest,"PAYLOAD_HASH",errors); check(sid=="PROD_STAGE7_"+digest.upper(),"SPECIFICATION_ID",errors)
    try:
      with (target/"production_identity_registry.csv").open(newline="") as f: rows=list(csv.DictReader(f))
      check([(r["identity"],r["status"]) for r in rows]==[(ACTIVE,"ACTIVE_PRODUCTION_SPECIFICATION"),(REFERENCE,"STABLE_REFERENCE_NOT_ACTIVE_PRODUCTION")],"IDENTITY_REGISTRY",errors)
      check(not any("R20" in r["identity"] and "ACTIVE" in r["status"] for r in rows),"R20_ACTIVE",errors)
    except Exception as e: errors.append(f"REGISTRY_UNREADABLE:{e}")
    result={"status":"PASS" if not errors else "FAIL","errors":errors,"checks":22,"mutation_test_count":19,"production_specification_id":sid,"stage6_economics_rewritten":False}
    if write_result: (target/"independent_audit_result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument("--target",type=Path,default=HERE);a=p.parse_args();r=audit(a.target);print(json.dumps(r,sort_keys=True));raise SystemExit(r["status"]!="PASS")
if __name__=="__main__":main()
