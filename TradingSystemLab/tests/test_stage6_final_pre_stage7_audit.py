import importlib.util
from pathlib import Path

import pandas as pd
import pytest

HERE = Path(__file__).resolve().parents[1] / "results/post_v3_analysis/stage6_final_pre_stage7_audit"
SPEC = importlib.util.spec_from_file_location("final_pre7", HERE / "generate_audit.py")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def frame(values, *, trail=False):
    rows=[]
    for i,value in enumerate(values):
        rows.append({"generation":"v3_perpetual","lifecycle":"historical_true_oos","fold_id":"","strategy":"T3","timeframe":"H1","instrument":"IMOEXF","direction":"LONG","entry_time":f"2025-01-{i+1:02d}T10:00:00Z","entry_price":100+i,"exit_time":f"2025-01-{i+1:02d}T12:00:00Z","net_R_C1":value,"trade_id":f"{'T' if trail else 'C'}{i}"})
    return pd.DataFrame(rows)


def test_trade_key_is_not_ordinal_and_bridge_handles_downstream_paths():
    canonical=frame([1.,-2.,3.])
    overlay=frame([1.5,-1.])
    # Replace overlay's second entry with a new downstream entry.
    overlay.loc[1,"entry_time"]="2025-01-09T10:00:00Z"; overlay.loc[1,"entry_price"]=109
    recon,decomp=mod.reconciliation(canonical,overlay)
    row=decomp.iloc[0]
    assert row.matched_count==1 and row.canonical_only_count==2 and row.trail1_only_count==1
    assert row.matched_exit_delta_R==pytest.approx(.5)
    assert row.canonical_only_R==pytest.approx(1.)
    assert row.trail1_only_R==pytest.approx(-1.)
    assert row.bridge_R==pytest.approx(row.total_delta_R)
    assert set(recon.path_class)=={"MATCHED","CANONICAL_ONLY","TRAIL1_ONLY"}


def test_metrics_dd_recovery_and_pf_are_recomputed():
    got=mod.metrics(frame([2.,-3.,1.]))
    assert got["net_R"]==0
    assert got["PF"]==pytest.approx(1.)
    assert got["max_DD_R"]==pytest.approx(-3.)
    assert got["recovery_factor"]==0


def test_mutated_bridge_is_detectable():
    _,d=mod.reconciliation(frame([1.,-2.]),frame([1.5,-2.]))
    d.loc[0,"matched_exit_delta_R"] += .01
    assert not ((d.matched_exit_delta_R-d.canonical_only_R+d.trail1_only_R-d.total_delta_R).abs()<1e-9).all()


def test_frozen_decision_sha():
    assert mod.sha(mod.STAGE6/"production_assembly_decision.csv")==mod.DECISION_SHA


def test_published_audit_contains_all_required_mutation_detections():
    result=__import__("json").loads((HERE/"independent_audit_result.json").read_text())
    required={"matched_exit_delta","removed_canonical_only_trade","instrument_net_R","DD","yearly_result","monthly_stability","CNY_USD_redundancy","stage6_decision_SHA"}
    assert result["status"]==mod.STATUS
    assert required==set(result["mutation_tests"])
    assert set(result["mutation_tests"].values())=={"DETECTED"}
