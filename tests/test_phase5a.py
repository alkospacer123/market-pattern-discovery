import copy
import json

import numpy as np
import pandas as pd
import pytest

from market_pattern_discovery.discovery.protocol import *
from market_pattern_discovery.discovery.records import *
from market_pattern_discovery.research.protocol import load_protocol


def test_protocol_signatures_and_drift(tmp_path):
    protocol=load_discovery_protocol(); assert protocol["discovery_protocol_version"]=="1.0"
    changed=copy.deepcopy(protocol); changed["rule"]["maximum_depth"]=4
    path=tmp_path/"p.json"; path.write_text(json.dumps(changed))
    with pytest.raises(ValueError,match="signature drift"): load_discovery_protocol(path)


def test_quantile_bins_categorical_and_nan_state():
    state,cuts=quantile_states(pd.Series([np.nan,*range(100)]))
    assert state.iloc[0]=="MISSING" and state.iloc[1]=="LE_P10" and state.iloc[-1]=="GE_P90"
    assert apply_cutpoints(pd.Series([np.nan,0,99]),cuts).tolist()==["MISSING","LE_P10","GE_P90"]
    assert categorical_states(pd.Series([1,np.nan,"x"])).tolist()==[1,"MISSING","x"]


def test_continuous_and_binary_effects_and_synthetic_recovery():
    effect=continuous_effect(np.arange(10)+10,np.arange(20))
    assert effect["median_difference"]==5 and effect["probability_of_superiority"]>.5
    binary=binary_effect(np.ones(10),np.r_[np.zeros(10),np.ones(10)])
    assert binary["probability_difference"]==.5 and binary["relative_risk"]==2


def test_day_bootstrap_is_deterministic_and_keeps_day_unit():
    frame=pd.DataFrame({"moscow_trading_date":np.repeat(range(12),3),"y":np.tile([0.,1.,2.],12)})
    mask=pd.Series(np.tile([False,False,True],12))
    a=day_block_bootstrap(frame,mask,"y",replications=30); b=day_block_bootstrap(frame,mask,"y",replications=30)
    assert a==b and a["replications"]==30 and np.isfinite(a["standard_error"])


def test_bh_fdr_mapping_nan_monotonicity_and_validation():
    q=benjamini_hochberg([.01,.04,.03,np.nan]); assert np.allclose(q[:3],[.03,.04,.04]) and np.isnan(q[3])
    with pytest.raises(ValueError): benjamini_hochberg([1.1])


def test_walk_forward_applies_frozen_mask_without_retuning():
    frame=pd.DataFrame({"timestamp":pd.date_range("2026-02-01",periods=4,freq="20D",tz="UTC"),"moscow_trading_date":range(4),"y":[0.,2.,0.,4.]})
    folds=[{"fold_id":"a","validate":["2026-01-31T21:00:00Z","2026-02-28T21:00:00Z"]},{"fold_id":"b","validate":["2026-02-28T21:00:00Z","2026-04-30T21:00:00Z"]}]
    result=fold_effects(frame,pd.Series([True,False,True,False]),"y",folds,"EXP cutpoints")
    assert all(x["definition_source"]=="EXP cutpoints" for x in result)


def test_mask_dedupe_rule_depth_and_pairwise_cap():
    kept,dupes=exact_mask_dedupe([np.array([1,0]),np.array([1,0]),np.array([0,1])]); assert kept==[0,2] and dupes=={1:0}
    validate_rule([{"feature":"x","state":"high"}]*3)
    with pytest.raises(ValueError): validate_rule([{"feature":"x","state":"x"}]*4)
    assert len(capped_feature_pairs(["d","c","b","a"],3))==3


def test_cluster_target_isolation_and_seed_determinism():
    x=np.array([[0.,0.],[0.,1.],[9.,9.],[9.,8.]])
    first=deterministic_kmeans(x,2); second=deterministic_kmeans(x,2)
    assert np.array_equal(first,second)
    # The API accepts features only, so changing an outcome cannot influence labels.
    outcome=np.array([0,0,1,1]); outcome[:]=1; assert np.array_equal(first,deterministic_kmeans(x,2))


def _effect():
    return {"hypothesis_id":"HYP-U-000000001","target_role":"HORIZON","contrast":"PRIMARY","horizon":60,"effect_id":"EFF-1","experiment_id":"EXP-1","method":"univariate_screen","pattern_definition":{"representation":"quantile_state"},"feature_conditions":[],"target_behavior":"y","instrument":"CNY","timeframe":"M1","sample_size":100,"unique_days":12,"coverage":.1,"baseline_size":1000,"baseline_distribution":{},"candidate_distribution":{},"effect_metrics":{"primary_effect":.1,"primary_effect_signed":.1,"primary_effect_absolute":.1},"uncertainty":{"lower":.01,"upper":.2},"raw_p":.01,"adjusted_q":.02,"fold_results":[{"effect":.1},{"effect":.2}],"replication_result":{"classification":"not_tested"},"multiplicity_family":"fam","rank_within_experiment":1,"screening_status":"promoted","candidate_id":None,"target_family":"DIRECTIONAL"}


def test_candidate_screening_lineage_and_immutability(tmp_path):
    effect=_effect(); ok,reasons=screen_effect(effect,load_discovery_protocol()["candidate_screening_policy"]); assert ok and not reasons
    candidate=create_candidate_from_effect(effect,code_commit="abc",signatures={"x":"y"},discovery_data_period=["a","b"],directory=tmp_path)
    frozen=freeze_for_confirmation(candidate); changed=copy.deepcopy(frozen); changed["pattern_definition"]["state"]="other"
    with pytest.raises(ValueError,match="new Candidate ID"): assert_candidate_immutable(frozen,changed)


def test_replication_semantics():
    assert replication_semantics({"representation":"quantile_state"})=="not_tested"
    assert replication_semantics({"representation":"raw_threshold"})=="not_applicable"


def test_experiment_preregistration_confirmation_guard_and_true_oos_lock():
    p=load_discovery_protocol(); r=load_protocol(); exp={"experiment_id":"EXP-1","research_track":"unknown_discovery","experiment_type":"univariate_screen","access_mode":"DISCOVERY","feature_set_signature":p["required_signatures"]["feature_set"],"behavior_target_signature":p["required_signatures"]["behavior_target_set"],"research_protocol_signature":p["required_signatures"]["research_protocol"],"method":"univariate_screen","target_family":"DIRECTIONAL","feature_scope":["x"],"multiplicity_family":"f","seed":20260401,"period":[r["discovery_period"]["start_utc"],r["discovery_period"]["end_utc_exclusive"]]}
    authorize_experiment(exp)
    with pytest.raises(ValueError,match="unregistered"): authorize_experiment({})
    bad=copy.deepcopy(exp); bad["access_mode"]="INTERNAL_CONFIRMATION"
    with pytest.raises(PermissionError): authorize_experiment(bad)
    sealed=copy.deepcopy(exp); sealed["period"]=["2025-01-01T00:00:00Z","2025-02-01T00:00:00Z"]
    with pytest.raises(PermissionError): authorize_experiment(sealed)
