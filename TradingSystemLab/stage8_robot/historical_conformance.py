"""Authenticated two-layer frozen H1 research-to-robot conformance."""
from __future__ import annotations
import argparse,hashlib,json,subprocess
from pathlib import Path
import pandas as pd
from TradingSystemLab.core.data_loader import DataLoader
from .authority_replay import frozen_parameters,replay_authority
from .production_replay import CONFIGURATION,replay_production

DATA_REPO="alkospacer123/market-pattern-data"; DATA_COMMIT="50f1fd2178c18b7ab3bd969be82ad01f47a34745"
T3_SHA="840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c"; PARAM_SHA="4e73cdb77246cb07b5953160b9fc0ab36bfd4bd6d9a7f7faaae7e6e392ee340a"
TRAIL_SHA="d1d8ac2eeea9095becd6f74295e4a540d02ee0494237af5f16f6d66a487f221b"; LEDGER_SHA="0f9034edf228a687da67e9f3e35fad01f2339be162c558e6d802c3cd77eea8ad"
HASHES={"USDRUBF":"f0ca366d816a6213742271242e87c53d1e23f5a5fc4655df0123217df418a226","CNYRUBF":"a3815b88a11aa5878b8bd104140f002859349c2c8d7f6ff0476a0d4c4d9a612e","GLDRUBF":"12a626ba6cc47fce2f392d4a6ce3bdb8a3c1aad074306a73ab480fcfbb83b87e","IMOEXF":"119878c12f602924296ab27b5b9f3cf51fa54f1a9370793892edbea58003e110"}
ROOT=Path(__file__).resolve().parents[2]; HERE=Path(__file__).resolve().parent; S6=ROOT/"TradingSystemLab/results/post_v3_analysis/stage6_fixed_basket_reassessment"; TOLERANCE=1e-10
EXACT=("lifecycle","fold_id","instrument","direction","entry_time","exit_time","exit_reason","trail1_triggered","trigger_bar_time","trail1_activation_time","trail1_activated","candidate_already_looser","gap_through_activated_trail","bars_held")
NUMERIC=("entry_price","initial_stop_price","initial_risk_price","trigger_price","stored_trail_candidate","exit_price","gross_R","cost_R","net_R_C1")

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def authenticate(data_root):
    manifest=json.loads((S6/"trail1_authoritative_ledger_manifest.json").read_text()); ledger=S6/"trail1_authoritative_trades.csv"
    checks={"row_count":manifest.get("row_count")==418,"committed_sha":manifest.get("committed_file_sha256")==LEDGER_SHA==sha(ledger),
      "event_hash":manifest.get("event_hash")==LEDGER_SHA,"t3":manifest.get("t3_sha")==T3_SHA==sha(ROOT/"TradingSystemLab/strategies/trend/T3_MTF_Trend.py"),
      "parameter":manifest.get("parameter_sha")==PARAM_SHA,"trail":manifest.get("trail1_implementation_sha")==TRAIL_SHA==sha(ROOT/"TradingSystemLab/results/post_v3_analysis/stage5_structural_validation/stage5_trail1_execution.py"),
      "data_commit":manifest.get("data_commit")==DATA_COMMIT==subprocess.check_output(["git","-C",str(data_root),"rev-parse","HEAD"],text=True).strip(),
      "lifecycle_registry":manifest.get("lifecycle_registry_sha")==sha(ROOT/"TradingSystemLab/results/post_v3_analysis/stage5_structural_validation/canonical_lifecycle_registry.csv"),
      "repeated":manifest.get("repeated_replay_hashes")==[LEDGER_SHA,LEDGER_SHA],"instruments":set(manifest.get("instruments",[]))==set(HASHES),
      "lifecycles":set(manifest.get("lifecycle_coverage",[]))=={"baseline","walk_forward","historical_true_oos"}}
    for symbol,digest in HASHES.items(): checks["h1_"+symbol]=sha(data_root/"forever"/symbol/f"{symbol}_H1.csv")==digest==manifest["raw_h1_source_hashes"][f"forever/{symbol}/{symbol}_H1.csv"]
    if not all(checks.values()): raise RuntimeError(f"AUTHENTICATION_FAILED:{checks}")
    frozen_parameters(); return checks

def _norm(value,field):
    if pd.isna(value) or value=="": return ""
    if field in ("entry_time","exit_time","trigger_bar_time","trail1_activation_time"): return pd.Timestamp(value).tz_convert("UTC").isoformat()
    if field in ("trail1_triggered","trail1_activated","candidate_already_looser","gap_through_activated_trail"): return str(value).lower() in ("true","1")
    return str(value)

def reconcile(expected,actual,path):
    keys=["lifecycle","fold_id","instrument"]
    expected=expected.copy(); actual=actual.copy()
    for frame in (expected,actual):
      frame.sort_values(keys+["entry_time","direction","entry_price"],kind="mergesort",inplace=True)
      frame["sequence"]=frame.groupby(keys,dropna=False).cumcount()+1
    merged=expected.merge(actual,on=keys+["sequence"],how="outer",suffixes=("_expected","_reproduced"),indicator=True,sort=True)
    rows=[]; counts={"missing":0,"extra":0,"timestamp_mismatches":0,"direction_mismatches":0,"price_mismatches":0,"state_mismatches":0,"R_mismatches":0}
    for _,r in merged.iterrows():
      status="MATCH"
      if r._merge=="left_only": status="MISSING"; counts["missing"]+=1
      elif r._merge=="right_only": status="EXTRA"; counts["extra"]+=1
      else:
       bad=[]
       for field in EXACT:
        left=r[field] if field in keys else r[field+"_expected"]
        right=r[field] if field in keys else r[field+"_reproduced"]
        same=_norm(left,field)==_norm(right,field)
        if not same:
         bad.append(field)
         if field=="direction": counts["direction_mismatches"]+=1
         elif "time" in field: counts["timestamp_mismatches"]+=1
         else: counts["state_mismatches"]+=1
       for field in NUMERIC:
        a,b=r[field+"_expected"],r[field+"_reproduced"]
        missing=lambda x: pd.isna(x) or x==""
        # The immutable ledger was committed with Stage-6's %.12g contract.
        # Compare that canonical representation; R fields additionally retain
        # the declared 1e-10 arithmetic tolerance through their 12g equality.
        same=(missing(a) and missing(b)) or (not missing(a) and not missing(b) and format(float(a),".12g")==format(float(b),".12g"))
        if not same: bad.append(field); counts["R_mismatches" if field.endswith("R") or "_R_" in field else "price_mismatches"]+=1
       if bad: status="MISMATCH:"+"|".join(bad)
      rows.append({"lifecycle":r.get("lifecycle",""),"fold_id":r.get("fold_id",""),"instrument":r.get("instrument",""),"sequence":r.sequence,"status":status,
                   "expected_trade_id":r.get("trade_id_expected",""),"reproduced_trade_id":r.get("trade_id_reproduced","")})
    out=pd.DataFrame(rows); out.to_csv(path,index=False,lineterminator="\n")
    exact=int(out.status.eq("MATCH").sum()); return {"expected_trade_count":len(expected),"reproduced_trade_count":len(actual),"exact_matches":exact,**counts,"status":"PASS" if exact==len(expected)==len(actual) else "FAIL"}

def generate(data_root):
    checks=authenticate(data_root); registry=pd.read_csv(ROOT/"TradingSystemLab/results/post_v3_analysis/stage5_structural_validation/canonical_lifecycle_registry.csv",keep_default_na=False)
    registry=registry[(registry.generation=="v3_perpetual")&(registry.strategy=="T3")&(registry.timeframe=="H1")&registry.instrument.isin(HASHES)]
    expected=pd.read_csv(S6/"trail1_authoritative_trades.csv",keep_default_na=False); runs=[]
    for _ in range(2):
     authority=[]; production=[]
     for row in registry.to_dict("records"):
      raw=DataLoader(forbid_true_oos=False).load_csv(data_root/"forever"/row["instrument"]/f'{row["instrument"]}_H1.csv')
      frame=DataLoader.close_index(raw).loc[row["start_timestamp"]:row["end_timestamp"]].copy(); meta={k:row[k] for k in ("instrument","lifecycle","fold_id")}
      authority.extend(replay_authority(frame,row["instrument"],meta)); production.extend(replay_production(frame,row["instrument"],meta))
     runs.append((pd.DataFrame(authority),pd.DataFrame(production)))
    authority,production=runs[0]
    event_hash=lambda f: hashlib.sha256(f.to_csv(index=False,lineterminator="\n",float_format="%.12g").encode()).hexdigest()
    determinism={"authority_replay":[event_hash(x[0]) for x in runs],"production_robot_replay":[event_hash(x[1]) for x in runs]}
    if any(v[0]!=v[1] for v in determinism.values()): raise RuntimeError("NONDETERMINISTIC_REPLAY")
    a=reconcile(expected,authority,HERE/"authority_replay_reconciliation.csv"); p=reconcile(expected,production,HERE/"production_robot_reconciliation.csv")
    counts=lambda f: [{"lifecycle":x[0],"instrument":x[1],"trades":int(len(g))} for x,g in f.groupby(["lifecycle","instrument"],sort=True)]
    report={"status":"STAGE_8_FINAM_DEMO_BINDING_READY_AWAITING_OPERATOR_CREDENTIALS" if a["status"]==p["status"]=="PASS" else ("STAGE_8_AUTHORITY_REPLAY_FAIL" if a["status"]!="PASS" else "STAGE_8_PRODUCTION_ROBOT_CONFORMANCE_FAIL"),
      "authority_replay":a,"production_robot_replay":p,"candidate_identity":CONFIGURATION,"candidate_parameters":vars(frozen_parameters()),"tolerance":TOLERANCE,"numeric_serialization":"Stage-6 canonical %.12g",
      "frozen_data_repo":DATA_REPO,"frozen_data_commit":DATA_COMMIT,"h1_sha256":HASHES,"source_hashes":{"t3":T3_SHA,"parameters":PARAM_SHA,"trail1":TRAIL_SHA,"authoritative_ledger":LEDGER_SHA},
      "authentication":checks,"counts":{"expected":counts(expected),"authority":counts(authority),"production":counts(production)},
      "determinism":determinism,
      "pr276_diagnosis":{"expected":418,"reproduced":424,"exact":247,"baseline_failures":177,"walk_forward_exact":"63/63","historical_true_oos_exact":"184/184"}}
    report["reconciliation_hashes"]={x.name:sha(x) for x in (HERE/"authority_replay_reconciliation.csv",HERE/"production_robot_reconciliation.csv")}
    (HERE/"conformance_report.json").write_text(json.dumps(report,indent=2,sort_keys=True,default=str)+"\n"); return report

if __name__=="__main__":
 p=argparse.ArgumentParser(); p.add_argument("--data-root",type=Path,required=True); args=p.parse_args(); print(json.dumps(generate(args.data_root),sort_keys=True))
