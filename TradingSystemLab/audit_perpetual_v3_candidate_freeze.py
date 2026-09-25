"""Independent fail-closed audit for the v3 perpetual candidate freeze."""
from __future__ import annotations
import ast, csv, hashlib, json, math
from pathlib import Path
from typing import Any

EXPECTED = (
 ("T2_M30_candidate_v3","T2","M30","T2-M30-608dc87d09f1"),
 ("T2_H1_candidate_v3","T2","H1","T2-H1-608dc87d09f1"),
 ("T3_M30_candidate_v3","T3","M30","T3-M30-d6feb972db57"),
 ("T3_H1_candidate_v3","T3","H1","T3-H1-4e73cdb77246"),)
PARAMETERS = {
 "T2_M30_candidate_v3":{"ema_fast":20,"ema_trend":50,"ema_slow":200,"adx_threshold":20.0,"impulse_distance_atr":0.5,"confirmation_window":3,"max_initial_stop_atr":2.5,"trailing_atr":3.0},
 "T2_H1_candidate_v3":{"ema_fast":20,"ema_trend":50,"ema_slow":200,"adx_threshold":20.0,"impulse_distance_atr":0.5,"confirmation_window":3,"max_initial_stop_atr":2.5,"trailing_atr":3.0},
 "T3_M30_candidate_v3":{"ema_period":100,"adx_threshold":20.0,"breakout_period":30,"atr_average_period":20,"stop_atr":2.0,"trail_atr":3.0},
 "T3_H1_candidate_v3":{"ema_period":100,"adx_threshold":20.0,"breakout_period":20,"atr_average_period":20,"stop_atr":2.5,"trail_atr":3.0}}
HASHES={"T2_M30_candidate_v3":"608dc87d09f10aa0e03026ebb525f6b8ec865060c7890cee08fa0c7ed14cf86b","T2_H1_candidate_v3":"608dc87d09f10aa0e03026ebb525f6b8ec865060c7890cee08fa0c7ed14cf86b","T3_M30_candidate_v3":"d6feb972db575bf6e66ac901be95fe079dccc82d9e2c3e880d17faeae8d1adf9","T3_H1_candidate_v3":"4e73cdb77246cb07b5953160b9fc0ab36bfd4bd6d9a7f7faaae7e6e392ee340a"}
BASELINES={"T2":{"ema_fast":20,"ema_trend":50,"ema_slow":200,"adx_threshold":20.0,"impulse_distance_atr":0.5,"confirmation_window":3,"max_initial_stop_atr":3.0,"trailing_atr":3.0},"T3":{"ema_period":100,"adx_threshold":20.0,"breakout_period":20,"atr_average_period":20,"stop_atr":2.0,"trail_atr":3.0}}
BASE_HASH={"T2":"0f598fd08d5fee40575b8a23daaa12bdbe8ad40071f57fb8c9b8a566cda4eb4f","T3":"782a150195d69651967ac8c5284b9140a050e35e9601cdc065ae11b196d30e47"}
SOURCE={"T2":("TradingSystemLab/strategies/trend/T2_Trend_Pullback.py","376df085cfda85eefccb31343aad40ed4fbb1078f1314496472a3a4ac9507774"),"T3":("TradingSystemLab/strategies/trend/T3_MTF_Trend.py","840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c")}
MERGE="272eabd5a4261a18a763356964b82b4b5b5673ea"
ANCHORS={"T2-M30-608dc87d09f1":(324,1.7118816595,.310463258155,100.590095642,-16.3334012952,6.15855165892),"T2-H1-608dc87d09f1":(156,2.39295957746,.575052042961,89.708118702,-6.88205022139,13.0350863211),"T3-M30-d6feb972db57":(341,1.93094457407,.376193476605,128.281975522,-15.012134415,8.54521895261),"T3-H1-4e73cdb77246":(181,2.31342650378,.399304363394,72.2740897743,-5.67342240555,12.7390637622)}

def stable_hash(v:Any)->str: return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
def rows(p:Path):
 with p.open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))
def one(rs,key,value):
 found=[r for r in rs if r[key]==value]
 if len(found)!=1: raise AssertionError(f"expected one {value}, got {len(found)}")
 return found[0]
def declaration_only(root:Path):
 source=(root/"TradingSystemLab/perpetual_v3_candidate_freeze.py").read_text()
 if any(x in source for x in ("Backtester","load_development","T2TrendPullback","T3MTFTrend","four_bar_context","optimization_runner","robustness_runner")): raise AssertionError("forbidden execution reference")
 tree=ast.parse(source); literal=None
 forbidden={"sorted","sort","nlargest","nsmallest","idxmax","idxmin","argmax","argmin","rank","score"}
 for node in ast.walk(tree):
  if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="PREDECLARED_CANDIDATES" for t in node.targets): literal=ast.literal_eval(node.value)
  if isinstance(node,ast.Call):
   name=node.func.id if isinstance(node.func,ast.Name) else node.func.attr if isinstance(node.func,ast.Attribute) else ""
   if name in forbidden: raise AssertionError(f"forbidden selection primitive: {name}")
 if literal!=EXPECTED: raise AssertionError("predeclaration is not the exact literal")

def audit(project_root:Path|str=Path("."), registry_path:Path|None=None, manifest_path:Path|None=None, report_path:Path|None=None):
 root=Path(project_root); out=root/"TradingSystemLab/results/perpetual_v3/phase3_candidate_freeze"
 rp=registry_path or out/"candidate_registry.json"; mp=manifest_path or out/"manifest.json"; report=report_path or out/"Candidate_Freeze_Report.md"
 registry=json.loads(rp.read_text()); manifest=json.loads(mp.read_text())
 declaration_only(root)
 contract={"phase":"PHASE_3_CANDIDATE_FREEZE","status":"V3_PERPETUAL_PHASE_3_CANDIDATE_FREEZE_COMPLETE","phase2_reference_merge":MERGE,"candidate_count":4,"selection_locked_before_validation":True,"raw_market_data_read":False,"optimization_executed":False,"parameter_search_executed":False,"ranking_executed":False,"robustness_executed":False,"walk_forward_executed":False,"true_oos_executed":False,"true_oos_blocked":True}
 if any(manifest.get(k)!=v for k,v in contract.items()): raise AssertionError("manifest contract mismatch")
 if manifest.get("artifact_sha256",{}).get("candidate_registry.json")!=hashlib.sha256(rp.read_bytes()).hexdigest() or manifest.get("artifact_sha256",{}).get("Candidate_Freeze_Report.md")!=hashlib.sha256(report.read_bytes()).hexdigest(): raise AssertionError("artifact hash mismatch")
 recs=registry.get("candidates")
 if registry.get("immutable") is not True or not isinstance(recs,list) or len(recs)!=4: raise AssertionError("registry cardinality/immutability mismatch")
 if [(r.get("candidate_id"),r.get("strategy"),r.get("timeframe"),r.get("phase2_configuration_id")) for r in recs]!=list(EXPECTED): raise AssertionError("candidate identity/order mismatch")
 opt=root/"TradingSystemLab/results/perpetual_v3/optimization"; inventory=rows(opt/"robust_plateau_inventory.csv")
 if len(inventory)!=25: raise AssertionError("inventory must have 25 rows")
 for record in recs:
  cid,strategy,timeframe,config=next(x for x in EXPECTED if x[0]==record["candidate_id"]); study=opt/strategy/timeframe
  pr=one(rows(study/"parameters.csv"),"configuration_id",config); rr=one(rows(study/"results.csv"),"configuration_id",config); pl=one(rows(study/"plateau_report.csv"),"configuration_id",config); inv=one(inventory,"configuration_id",config)
  if pl["classification"]!="ROBUST_PLATEAU" or (inv["strategy"],inv["timeframe"])!=(strategy,timeframe) or record.get("phase2_classification")!="ROBUST_PLATEAU": raise AssertionError("plateau mismatch")
  persisted={k:float(v) for k,v in pr.items() if k not in {"configuration_id","is_baseline"}}
  expected=PARAMETERS[cid]
  if set(persisted)!=set(expected) or any(persisted[k]!=expected[k] for k in expected): raise AssertionError("persisted parameters mismatch")
  if stable_hash(expected)!=HASHES[cid] or config.rsplit("-",1)[1]!=HASHES[cid][:12] or record.get("parameters")!=expected or record.get("parameter_hash")!=HASHES[cid]: raise AssertionError("candidate hash mismatch")
  if stable_hash(BASELINES[strategy])!=BASE_HASH[strategy] or record.get("canonical_baseline_parameters")!=BASELINES[strategy] or record.get("canonical_baseline_parameter_hash")!=BASE_HASH[strategy]: raise AssertionError("baseline mismatch")
  path,expected_source=SOURCE[strategy]; actual=hashlib.sha256((root/path).read_bytes()).hexdigest()
  if actual!=expected_source or record.get("frozen_strategy_source_hash")!=actual: raise AssertionError("source hash mismatch")
  observed=(int(rr["trades"]),)+(tuple(float(rr[k]) for k in ("PF_C1","expectancy_C1","net_R_C1","max_DD_C1","recovery_factor_C1")))
  if any(not math.isclose(a,b,rel_tol=0,abs_tol=1e-12) for a,b in zip(observed,ANCHORS[config])): raise AssertionError("evidence anchor mismatch")
  balance=[f"{i}_expectancy_C1" for i in ("USDRUBF","CNYRUBF","GLDRUBF","IMOEXF")]+["Y2023_expectancy_C1","Y2024_expectancy_C1","LONG_expectancy_C1","SHORT_expectancy_C1","expectancy_C1_without_top3"]
  if any(float(rr[k])<=0 for k in balance): raise AssertionError("balance evidence mismatch")
  locks={"selection_method":"explicit_predeclared_identifier_without_metric_ranking","validation_data_used_for_selection":False,"selection_locked_before_validation":True,"robustness_executed":False,"walk_forward_executed":False,"true_oos_executed":False,"true_oos_blocked":True,"phase2_reference_merge":MERGE}
  if any(record.get(k)!=v for k,v in locks.items()): raise AssertionError("candidate lock mismatch")
 return {"status":"V3_PERPETUAL_PHASE_3_CANDIDATE_FREEZE_COMPLETE","audit":"PASS","candidate_count":4}

if __name__=="__main__": print(json.dumps(audit(Path(__file__).resolve().parents[1]),sort_keys=True))
