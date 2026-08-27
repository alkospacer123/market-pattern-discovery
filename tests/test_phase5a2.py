import copy
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from market_pattern_discovery.discovery.execution_contract import *
from market_pattern_discovery.discovery.protocol import benjamini_hochberg
from market_pattern_discovery.discovery.records import create_candidate_from_effect, validate_effect_record
from market_pattern_discovery.validation.phase5a2 import _effect, validate


def contract(): return load_execution_contract()

def test_feature_typing_identifier_order_and_counts():
    c=contract(); frozen=json.load(open("config/feature_set_v1.json"))
    for tf,key,total in [("M1","ordered_predictive_features",241),("M5","m5_ordered_predictive_features",220)]:
        rows=c["feature_inventory"][tf]; assert len(rows)==total; assert [x["feature"] for x in rows]==frozen[key]
        date=next(x for x in rows if x["feature"]=="trading_date"); assert date["representation"]=="excluded" and "identifier" in date["exclusion_reason"]
        assert len({x["feature"] for x in rows})==total and all(x["representation"] in c["representation_types"] for x in rows)

def test_high_cardinality_audit():
    rows={x["feature"]:x["representation"] for x in contract()["feature_inventory"]["M1"]}
    assert all(rows[x]=="integer_categorical" for x in ["local_hour","local_minute","weekday"])
    assert all(rows[x]=="continuous_quantile" for x in ["minute_of_day","consecutive_up_candles","touch_count_60","cross_count_60","bars_since_last_touch","bars_since_last_cross"])

def test_states_and_train_only_cutpoints():
    c=contract(); assert c["state_order"]["continuous_quantile"]==["LE_P10","P10_P25","P25_P75","P75_P90","GE_P90","MISSING"]
    assert canonical_categories([2,1,np.nan])==[1,2,"MISSING"]
    train=pd.Series(range(100)); validation=pd.Series([10_000]); _,states,cuts=fit_train_apply_validate(train,validation)
    assert max(cuts)<100 and states.iloc[0]=="GE_P90"

def test_pair_hash_selection_deterministic_broad_not_prefix():
    rows=contract()["feature_inventory"]["M1"]; first=enumerate_pairs(rows,timeframe="M1"); second=enumerate_pairs(rows,timeframe="M1")
    assert first==second and len(first)==500 and all("trading_date" not in x for x in first)
    covered=set(sum(([a,b] for a,b in first),[])); assert len(covered)>=.85*240
    included=[x["feature"] for x in rows if x["representation"]!="excluded"]
    prefix=[(included[i],included[j]) for i in range(len(included)) for j in range(i+1,len(included))][:500]
    assert first!=prefix

def test_pair_selection_has_no_target_argument():
    import inspect
    assert "target" not in inspect.signature(enumerate_pairs).parameters

def test_subgroup_deterministic_depth_coverage_cap_no_identifier():
    features=[(f"f{i}",[0,1]) for i in range(30)]+[("trading_date",["d"])]
    first=subgroup_rules(features,400); assert first==subgroup_rules(features,400) and len(first)==400
    assert {len(x) for x in first}=={2,3}; names={n for rule in first for n,_ in rule}; assert "trading_date" not in names and len(names)>=25
    assert any("f20" in {n for n,_ in rule} for rule in first)

def unequal_frame(effect=False,binary=False):
    lengths=[3,7,4,9,5,8,6,10]; days=np.concatenate([[f"d{i}"]*n for i,n in enumerate(lengths)]); rng=np.random.default_rng(4)
    mask=np.concatenate([np.arange(n)<max(1,n//3) for n in lengths]); y=rng.normal(size=len(days))
    if effect:y[mask]+=8
    if binary:y=(y>0).astype(float)
    return pd.DataFrame({"moscow_trading_date":days,"target":y}),pd.Series(mask)

def test_null_unequal_days_deterministic_no_alignment_or_truncation():
    frame,mask=unequal_frame(); p=null_p_value(frame,mask,"target",replications=199); assert p==null_p_value(frame,mask,"target",replications=199) and 0<p<=1
    shuffled=frame.assign(mask=mask).sample(frac=1,random_state=2); p2=null_p_value(shuffled,shuffled.pop("mask").astype(bool),"target",replications=49); assert 0<p2<=1
    with pytest.raises(ValueError,match="align"): null_p_value(frame,mask.set_axis(range(1,len(mask)+1)),"target",replications=5)

def test_null_synthetic_null_and_strong_continuous_effect():
    null_frame,mask=unequal_frame(); effect_frame,_=unequal_frame(effect=True)
    assert null_p_value(null_frame,mask,"target",replications=199)>.001
    assert null_p_value(effect_frame,mask,"target",replications=199)<=.05

def test_null_binary_multiclass_contrast():
    frame,mask=unequal_frame(effect=True,binary=True); p=null_p_value(frame,mask,"target",kind="binary",replications=99); assert 0<p<=1

def test_fdr_fixture_nan_and_family_accounting():
    q=benjamini_hochberg([.01,.04,.03,np.nan]); assert np.allclose(q,[.03,.04,.04,np.nan],equal_nan=True) and np.isfinite(q).sum()==3

def test_fold_direction_and_unavailable_semantics():
    summary=same_direction_summary(1,[1,-1,0,np.nan]); assert summary["valid_fold_count"]==3 and summary["same_direction_fold_count"]==1
    assert np.isnan(same_direction_summary(1,[np.nan])["median_fold_effect"])

def test_screening_enum_and_transitions():
    for status in SCREENING_STATUSES: validate_screening_status(status)
    with pytest.raises(ValueError): validate_screening_status("arbitrary")
    validate_screening_transition("enumerated","evaluated"); validate_screening_transition("screened","promoted")
    with pytest.raises(ValueError): validate_screening_transition("promoted","screened")

def test_effect_schema_runtime_rejects_unknown_status():
    effect=_effect(); validate_effect_record(effect); effect["screening_status"]="bad"
    with pytest.raises(ValueError): validate_effect_record(effect)

def test_candidate_promoted_persistence_lineage_and_initial_status(tmp_path):
    effect=_effect(); candidate=create_candidate_from_effect(effect,code_commit="abc",signatures=contract()["upstream_signatures"],discovery_data_period=["a","b"],directory=tmp_path)
    assert candidate["status"]=="discovered" and (tmp_path/f"{candidate['candidate_id']}.json").exists()
    lineage=candidate["discovery_effect_summary"]
    for key in ["hypothesis_id","effect_id","experiment_id","method","instrument","timeframe","feature_conditions","target_family","target_role","contrast","primary_effect_signed","primary_effect_absolute","uncertainty","walk_forward_summary","replication_result","upstream_signatures","discovery_execution_signature","code_commit"]: assert key in lineage
    effect["screening_status"]="screened"
    with pytest.raises(ValueError,match="promoted"): create_candidate_from_effect(effect,code_commit="x",signatures={},discovery_data_period=[],directory=tmp_path)

def test_candidate_default_uses_canonical_registry(monkeypatch,tmp_path):
    from market_pattern_discovery.research import registry
    monkeypatch.setattr(registry,"CANDIDATES",tmp_path)
    candidate=create_candidate_from_effect(_effect(),code_commit="abc",signatures=contract()["upstream_signatures"],discovery_data_period=["a","b"])
    assert (tmp_path/f"{candidate['candidate_id']}.json").exists() and candidate["status"]=="discovered"

def test_checkpoint_and_contract_drift(tmp_path):
    assert checkpoint_id("e","b","1","2")==checkpoint_id("e","b","1","2")
    bad=copy.deepcopy(contract());bad["execution_seed"]+=1;path=tmp_path/"bad.json";path.write_text(json.dumps(bad))
    with pytest.raises(ValueError,match="signature drift"):load_execution_contract(path)

def test_validator_semantics_and_corruption(tmp_path):
    result=validate(); assert result["remaining_execution_degrees_of_freedom"]==[]
    bad=copy.deepcopy(contract());next(x for x in bad["feature_inventory"]["M1"] if x["feature"]=="trading_date")["representation"]="categorical"
    bad.pop("signature_sha256");bad["signature_sha256"]=execution_signature(bad);path=tmp_path/"bad.json";path.write_text(json.dumps(bad))
    with pytest.raises(AssertionError,match="identifier exclusions"):validate(path)

def test_json_schema_and_runtime_effect_contract_consistency(tmp_path):
    from jsonschema import Draft202012Validator
    schema=json.loads(Path("schemas/discovery_effect_record_v1.json").read_text())
    validator=Draft202012Validator(schema); canonical=_effect()
    validator.validate(canonical); validate_effect_record(canonical)
    candidate=create_candidate_from_effect(canonical,code_commit="schema-test",signatures=contract()["upstream_signatures"],discovery_data_period=["a","b"],directory=tmp_path)
    assert (tmp_path/f"{candidate['candidate_id']}.json").exists()
    corruptions=[]
    bad=copy.deepcopy(canonical);bad["screening_status"]="unknown";corruptions.append(bad)
    bad=copy.deepcopy(canonical);bad["replication_result"]["classification"]="unknown";corruptions.append(bad)
    for key in ["hypothesis_id","target_family","target_role","contrast"]:
        bad=copy.deepcopy(canonical);bad.pop(key);corruptions.append(bad)
    for key in ["primary_effect_signed","primary_effect_absolute"]:
        bad=copy.deepcopy(canonical);bad["effect_metrics"].pop(key);corruptions.append(bad)
    for bad in corruptions:
        assert not validator.is_valid(bad)
        with pytest.raises(ValueError): validate_effect_record(bad)
