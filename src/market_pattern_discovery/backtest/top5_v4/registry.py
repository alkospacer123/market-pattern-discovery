from __future__ import annotations
from hashlib import sha256
from itertools import product
from pathlib import Path
import json
from .common import CONTRACT_PATH, REGISTRY_PATH, canonical_json, stable_id

def load_contract(path: str|Path=CONTRACT_PATH)->dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))

def _semantic_fingerprint(contract:dict,family:str,submodel:str)->str:
    payload={"engine_semantics_version":contract["engine_semantics_version"],"family":family,"submodel":submodel,"timeframe":contract["timeframes"][family],"ticks":contract["ticks"],"round_steps":contract.get("round_steps",{}),"execution":contract["execution"],"data_policy":contract["data_policy"],"family_rules":contract["family_rules"][family],"friction":contract["friction"]}
    return sha256(canonical_json(payload).encode()).hexdigest()

def _candidate(contract,family,submodel,params,active_grid_axes,selection_eligible=True):
    fp=_semantic_fingerprint(contract,family,submodel); spec={"family":family,"submodel":submodel,"parameters":params,"semantic_fingerprint":fp}
    return {"candidate_id":stable_id("CAND",spec,24),"family":family,"submodel":submodel,"parameters":params,"active_grid_axes":active_grid_axes,"complexity":len(active_grid_axes),"selection_eligible":bool(selection_eligible),"semantic_fingerprint":fp}

def build_candidate_registry(contract:dict)->list[dict]:
    out=[]; sg=contract["parameter_grids"]["STRUCTURAL"]
    ordinary=["REJECTION","SIMPLE_SWEEP","COMPLEX_FALSE_BREAK","BREAKOUT_RETEST"]
    for sub,tol,touches,target in product(ordinary,sg["tolerance_ticks"],sg["min_touches"],sg["target_r"]): out.append(_candidate(contract,"STRUCTURAL",sub,{"tolerance_ticks":tol,"min_touches":touches,"target_r":target},["submodel","tolerance_ticks","min_touches","target_r"]))
    for tol,touches,target in product(sg["tolerance_ticks"],sg["min_touches"],sg["target_r"]): out.append(_candidate(contract,"STRUCTURAL","GERCHIK_A_M5_PROXY",{"tolerance_ticks":tol,"min_touches":touches,"target_r":target},["submodel","tolerance_ticks","min_touches","target_r"]))
    og=contract["parameter_grids"]["ORB"]
    for length,stop,target in product(og["length"],og["direct_stop_mode"],og["target_r"]): out.append(_candidate(contract,"ORB","DIRECT",{"length":length,"stop_mode":stop,"target_r":target},["submodel","length","stop_mode","target_r"]))
    for sub in ("BREAKOUT_RETEST","FAILED_BREAKOUT_DIAGNOSTIC"):
        for length,target in product(og["length"],og["target_r"]): out.append(_candidate(contract,"ORB",sub,{"length":length,"target_r":target},["submodel","length","target_r"],sub!="FAILED_BREAKOUT_DIAGNOSTIC"))
    tg=contract["parameter_grids"]["TREND_PULLBACK"]
    for slow,target in product(tg["slow_ema"],tg["target_r"]): out.append(_candidate(contract,"TREND_PULLBACK",f"EMA20_{slow}",{"slow_ema":slow,"target_r":target},["slow_ema","target_r"]))
    pg=contract["parameter_grids"]["PAIRS"]
    for model,window,z in product(pg["model"],pg["window"],pg["z_entry"]): out.append(_candidate(contract,"PAIRS",model,{"model":model,"window":window,"z_entry":z},["model","window","z_entry"]))
    bg=contract["parameter_grids"]["BOLLINGER_RSI"]
    for k,rsi,rb,exit_mode in product(bg["k"],bg["rsi_thresholds"],bg["reentry_max_bars"],bg["exit"]):
        lo,hi=rsi; out.append(_candidate(contract,"BOLLINGER_RSI",exit_mode,{"k":k,"rsi_lower":lo,"rsi_upper":hi,"reentry_max_bars":rb,"exit_mode":exit_mode},["k","rsi_thresholds","reentry_max_bars","exit"]))
    out.sort(key=lambda r:r["candidate_id"]); ids=[r["candidate_id"] for r in out]
    if len(ids)!=len(set(ids)):raise AssertionError("candidate_id collision")
    if len(out)!=int(contract["candidate_registry"]["expected_total"]):raise AssertionError("candidate registry count mismatch")
    if sum(r["selection_eligible"] for r in out)!=int(contract["candidate_registry"]["expected_selection_eligible"]):raise AssertionError("selection-eligible registry count mismatch")
    if any("instrument" in r["parameters"] for r in out):raise AssertionError("instrument must not enter candidate identity")
    return out

def validate_contract(contract:dict,registry=None)->bool:
    required={"contract_version","engine_semantics_version","periods","instruments","ticks","round_steps","timeframes","friction","execution","data_policy","family_rules","parameter_grids","selection_policy","metrics","validation_status_policy","validation_workflow","candidate_registry","freeze_policy","testing_policy","true_oos_policy","research_protocol_compatibility","source_fidelity"}
    missing=required-set(contract)
    if missing:raise ValueError(f"missing contract keys: {sorted(missing)}")
    expected={"DEV":["2026-01-05T00:00:00+03:00","2026-03-01T00:00:00+03:00"],"VALIDATION_A":["2026-03-01T00:00:00+03:00","2026-05-01T00:00:00+03:00"],"VALIDATION_B":["2026-05-01T00:00:00+03:00","2026-05-16T00:00:00+03:00"]}
    if contract["periods"]!=expected:raise ValueError("period boundary mutation")
    if contract["true_oos_policy"]!={"year":2025,"status":"LOCKED_TRUE_OOS_DO_NOT_ACCESS"}:raise ValueError("TRUE OOS policy mutation")
    if contract["execution"]["commission_model"]!="NOT_INCLUDED" or contract["execution"]["tick_rounding"]!="ROUND_HALF_UP":raise ValueError("execution policy mutation")
    if contract["family_rules"]["BOLLINGER_RSI"]["rsi_label"]!="RSI14_EWM_ALPHA_1_OVER_N":raise ValueError("RSI formula label mutation")
    if contract["source_fidelity"]["GERCHIK_A_M5_PROXY"]["status"]!="PROXY_NOT_EXACT_SOURCE_REPLICATION":raise ValueError("Gerchik fidelity mutation")
    if set(contract["timeframes"])!={"STRUCTURAL","ORB","TREND_PULLBACK","PAIRS","BOLLINGER_RSI"}:raise ValueError("timeframe family mutation")
    if contract["selection_policy"]["status_by_survivor_count"]!={"0":"NO_DEV_SURVIVOR","1-4":"PARTIAL_DEV_SURVIVORS","5":"DEV_SELECTION_COMPLETE"}:raise ValueError("selection status mutation")
    for fam in ("STRUCTURAL","ORB","TREND_PULLBACK","PAIRS","BOLLINGER_RSI"):
        if "executable_formulas" not in contract["family_rules"][fam]:raise ValueError(f"missing executable formulas: {fam}")
    built=build_candidate_registry(contract)
    if registry is not None:
        if isinstance(registry,list):
            if canonical_json(registry)!=canonical_json(built):raise ValueError("candidate registry is not canonical")
        elif isinstance(registry,dict):
            if registry.get("candidate_ids")!=[r["candidate_id"] for r in built]:raise ValueError("candidate registry ID list mismatch")
            if registry.get("canonical_rows_sha256")!=sha256(canonical_json(built).encode()).hexdigest():raise ValueError("candidate registry rows hash mismatch")
            if registry.get("expected_total")!=len(built) or registry.get("expected_selection_eligible")!=sum(r["selection_eligible"] for r in built):raise ValueError("candidate registry declared counts mismatch")
        else:raise ValueError("unsupported candidate registry representation")
    return True

def registry_descriptor(rows:list[dict])->dict:
    return {"registry_version":"4.0.0","representation":"canonical candidate IDs + SHA256 of deterministic expanded rows; parameters/semantics are sourced from strategy_contract.json","expected_total":len(rows),"expected_selection_eligible":sum(r["selection_eligible"] for r in rows),"canonical_rows_sha256":sha256(canonical_json(rows).encode()).hexdigest(),"candidate_ids":[r["candidate_id"] for r in rows]}

def write_candidate_registry(contract_path=CONTRACT_PATH,registry_path=REGISTRY_PATH):
    c=load_contract(contract_path);rows=build_candidate_registry(c);Path(registry_path).write_text(json.dumps(registry_descriptor(rows),indent=2,sort_keys=True)+"\n",encoding="utf-8");return rows
