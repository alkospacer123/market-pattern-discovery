"""Semantic, contract-only Phase 5A.2 validator; opens no market rows."""
from __future__ import annotations
import json
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from market_pattern_discovery.discovery.execution_contract import (SCREENING_STATUSES, checkpoint_id, enumerate_pairs, execution_signature, load_execution_contract, null_p_value, remaining_execution_degrees, subgroup_rules, validate_screening_status)
from market_pattern_discovery.discovery.protocol import benjamini_hochberg
from market_pattern_discovery.discovery.records import create_candidate_from_effect

ROOT = Path(__file__).resolve().parents[3]

def _effect() -> dict:
    return {"hypothesis_id":"HYP-U-000000001","effect_id":"EFF-U-000000001","experiment_id":"EXP-TEST","method":"univariate_screen","pattern_definition":{"representation":"quantile_state","feature":"x","state":"GE_P90"},"feature_conditions":[{"feature":"x","state":"GE_P90"}],"target_behavior":"synthetic_target","target_family":"PATH","target_role":"HORIZON","horizon":60,"contrast":"PRIMARY","instrument":"CNY","timeframe":"M1","sample_size":40,"unique_days":12,"coverage":.02,"baseline_size":1000,"baseline_distribution":{},"candidate_distribution":{},"effect_metrics":{"primary_effect":1.0,"primary_effect_signed":1.0,"primary_effect_absolute":1.0},"uncertainty":{"lower":.2,"upper":1.8,"standard_error":.2},"raw_p":.01,"adjusted_q":.02,"fold_results":[{"fold_id":"WF-01","effect":.8}],"replication_result":{"classification":"not_tested"},"multiplicity_family":"family","rank_within_experiment":1,"screening_status":"promoted","candidate_id":None}

def validate(path: Path | None = None) -> dict:
    contract = load_execution_contract(path or ROOT / "config/discovery_execution_v1.json")
    manifest = json.loads((ROOT / "config/feature_set_v1.json").read_text())
    expected = {"M1":manifest["ordered_predictive_features"],"M5":manifest["m5_ordered_predictive_features"]}
    counts = {}; semantic = {}
    for tf, names in expected.items():
        rows=contract["feature_inventory"][tf]; actual=[x["feature"] for x in rows]
        if actual != names or len(actual) != len(set(actual)): raise AssertionError(f"{tf} inventory/order drift")
        types=Counter(x["representation"] for x in rows); excluded={x["feature"] for x in rows if x["representation"]=="excluded"}
        if excluded != {"trading_date"}: raise AssertionError(f"{tf} identifier exclusions drift")
        if any(x["representation"] not in contract["representation_types"] for x in rows): raise AssertionError("unknown representation")
        included=[x for x in rows if x["representation"]!="excluded"]
        pairs=enumerate_pairs(rows,500,timeframe=tf,seed=contract["execution_seed"])
        if pairs != enumerate_pairs(rows,500,timeframe=tf,seed=contract["execution_seed"]) or len(pairs)!=500: raise AssertionError("pair selection nondeterministic/cap drift")
        covered=set(sum(([a,b] for a,b in pairs),[]))
        prefix=[(included[i]["feature"],included[j]["feature"]) for i in range(len(included)) for j in range(i+1,len(included))][:500]
        if "trading_date" in covered or pairs==prefix or len(covered)<int(.85*len(included)): raise AssertionError("pair coverage/exclusion failure")
        sample=[(x["feature"],["A","B"]) for x in included[:30]]
        rules=subgroup_rules(sample,200,seed=contract["execution_seed"])
        if rules!=subgroup_rules(sample,200,seed=contract["execution_seed"]) or len(rules)!=200: raise AssertionError("subgroup determinism/cap failure")
        depths={len(x) for x in rules}; rule_features={name for rule in rules for name,_ in rule}
        if depths!={2,3} or "trading_date" in rule_features or len(rule_features)<20: raise AssertionError("subgroup coverage/exclusion failure")
        counts[tf]={"total":len(rows),"predictive_included":len(included),"excluded_identifiers":len(excluded),**types,"unclassified":0}
    frame=pd.DataFrame({"moscow_trading_date":["d1"]*3+["d2"]*5+["d3"]*4,"target":[0.,1.,0.,1.,0.,1.,0.,1.,0.,1.,0.,1.]})
    mask=pd.Series([1,0,0,1,0,0,0,0,1,0,0,0],dtype=bool)
    p1=null_p_value(frame,mask,"target",replications=99);p2=null_p_value(frame,mask,"target",replications=99)
    if p1!=p2 or not 0<p1<=1: raise AssertionError("unequal-day null failure")
    if not np.allclose(benjamini_hochberg([.01,.04,.03,np.nan]),[.03,.04,.04,np.nan],equal_nan=True): raise AssertionError("BH fixture failure")
    for status in SCREENING_STATUSES: validate_screening_status(status)
    try: validate_screening_status("invented")
    except ValueError: pass
    else: raise AssertionError("screening enum accepts arbitrary strings")
    with tempfile.TemporaryDirectory() as tmp:
        candidate=create_candidate_from_effect(_effect(),code_commit="synthetic",signatures=contract["upstream_signatures"],discovery_data_period=["start","end"],directory=Path(tmp))
        if candidate["status"]!="discovered" or not (Path(tmp)/f"{candidate['candidate_id']}.json").exists(): raise AssertionError("candidate persistence/lifecycle failure")
        required={"hypothesis_id","effect_id","target_family","contrast","primary_effect_signed","discovery_execution_signature"}
        if not required <= candidate["discovery_effect_summary"].keys(): raise AssertionError("candidate lineage incomplete")
    if checkpoint_id("E","B","H1","H2")!=checkpoint_id("E","B","H1","H2"): raise AssertionError("checkpoint nondeterminism")
    remaining=remaining_execution_degrees(contract)
    if remaining: raise AssertionError(f"execution degrees remain: {remaining}")
    market=subprocess.run(["git","-C","/workspace/market-pattern-data","status","--short"],check=True,capture_output=True,text=True).stdout
    if market: raise AssertionError("market data repository dirty")
    return {"phase":"5A.2","status":"PASS","discovery_execution_version":contract["discovery_execution_version"],"discovery_execution_signature":execution_signature(contract),"upstream_signatures":contract["upstream_signatures"],"feature_typing":counts,"pair_coverage_check":True,"subgroup_coverage_check":True,"unequal_day_null_check":True,"screening_schema_check":True,"candidate_persistence_check":True,"candidate_lineage_check":True,"remaining_execution_degrees_of_freedom":remaining,**contract["safety"],"market_data_repo_clean":True}

def main(): print(json.dumps(validate(),indent=2,sort_keys=True))
