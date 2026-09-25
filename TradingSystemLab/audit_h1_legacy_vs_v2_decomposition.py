"""Independent fail-closed audit for the retrospective H1 decomposition."""
from __future__ import annotations
import hashlib, json, subprocess
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path("TradingSystemLab/results/diagnostics/h1_legacy_vs_v2_decomposition")
PROTECTED=("baseline_v2","optimization_v2","phase3_candidate_freeze","robustness_v2","walk_forward_v2","true_oos_v2","true_oos_validation")
EXPECTED={"T2":(69,2.40553629688,.621125887693,42.8576862508,-9.46784963187),"T3":(97,2.67722820365,.590007031994,57.2306821034,-11.4999386679)}

def _sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def _unchanged(path,commit):
    result=subprocess.run(["git","diff","--quiet",commit,"--",str(path)],check=False)
    if result.returncode: raise AssertionError(f"protected path changed: {path}")
def _metric(v):
    from .core.unified_metrics import stats
    s=stats(v.astype(float)); return {"trades":s["trades"],"PF":s["PF_R"],"expectancy":s["expectancy"],"net_R":s["net_R"],"max_DD":s["max_DD_R"],"recovery_factor":s["recovery_factor"]}

def audit():
    m=json.loads((ROOT/"summary/manifest.json").read_text()); assert m["analysis_type"]=="RETROSPECTIVE_DIAGNOSTIC" and m["true_oos_status"]=="CONSUMED_PREVIOUSLY_NOT_NEW_OOS"
    assert (m["execution_count"],m["core_factorial_execution_count"],m["universe_control_execution_count"])==(12,8,4)
    assert m["timeframe"]=="H1" and m["common_cutoff"]=="2026-08-30T19:00:00+03:00" and m["common_start"]=="2025-01-01"
    assert m["cold_start"] and m["start_state"]=="FLAT" and m["no_pre_2025_warmup"] and m["C1_only"] and m["normalized_research_tick"]==.001
    assert len(m["parameter_generations"])==2 and {x["data_generation"] for x in m["execution_design"]}=={"LEGACY_CONTINUOUS","QUARTERLY_V2"}
    assert not any(m[x] for x in ("optimization","candidate_selection","ranking","portfolio_selection","current_v2_verdicts_modified","historical_h1_verdicts_modified"))
    for name in PROTECTED: _unchanged(Path("TradingSystemLab/results")/name,"45739ebb7a1c4fff2dd93134146e83bf0a2c9f51")
    for name in ("CURRENT_STATE.md","PROJECT_CONTEXT.md","ROADMAP.md"): _unchanged(Path("TradingSystemLab")/name,"45739ebb7a1c4fff2dd93134146e83bf0a2c9f51")
    paths={"T2":Path("TradingSystemLab/strategies/trend/T2_Trend_Pullback.py"),"T3":Path("TradingSystemLab/strategies/trend/T3_MTF_Trend.py")}
    assert {_s:_sha(p) for _s,p in paths.items()}==m["strategy_hashes"]
    factorial=pd.read_csv(ROOT/"summary/factorial_results.csv"); universe=pd.read_csv(ROOT/"summary/universe_results.csv")
    assert len(factorial)==8 and len(universe[universe.universe.eq("ALL6")])==4 and len(factorial)+len(universe[universe.universe.eq("ALL6")])==12
    ledgers={}
    for s in ("T2","T3"):
      for design in m["execution_design"]:
        f=pd.read_csv(ROOT/s/f"{design['run_id']}.csv"); ledgers[s,design["run_id"]]=f
        assert (pd.to_datetime(f.entry_time,utc=True)>=pd.Timestamp("2025-01-01",tz="UTC")).all()
        got=_metric(f.net_R_C1); run_id=design["run_id"]
        table=factorial if design["universe"]=="SICNY" else universe
        row=table[(table.strategy==s)&(table.diagnostic_run_id==run_id)].iloc[0]
        for k,v in got.items(): np.testing.assert_allclose(row[k],v,rtol=1e-9,atol=1e-9)
    for s,e in EXPECTED.items():
        r=factorial.query("strategy==@s and diagnostic_run_id=='LEGACY_DATA__LEGACY_PARAMS'").iloc[0]
        np.testing.assert_allclose([r[x] for x in ("trades","PF","expectancy","net_R","max_DD")],e,rtol=1e-9,atol=1e-9)
    effects=pd.read_csv(ROOT/"summary/decomposition_effects.csv")
    idx=factorial.set_index(["strategy","diagnostic_run_id"])
    for s in ("T2","T3"):
      for metric in ("trades","PF","expectancy","net_R","max_DD","recovery_factor"):
        LL,LV,QL,QV=[idx.loc[(s,x),metric] for x in ("LEGACY_DATA__LEGACY_PARAMS","LEGACY_DATA__V2_PARAMS","QUARTERLY_DATA__LEGACY_PARAMS","QUARTERLY_DATA__V2_PARAMS")]
        value=effects.query("strategy==@s and effect=='DATA_PARAMETER_INTERACTION' and metric==@metric").value.iloc[0]
        np.testing.assert_allclose(value,(QV-QL)-(LV-LL),rtol=1e-9,atol=1e-9); np.testing.assert_allclose(value,(QV-LV)-(QL-LL),rtol=1e-9,atol=1e-9)
    assert len(pd.read_csv(ROOT/"summary/monthly_results.csv"))==12*20
    assert len(pd.read_csv(ROOT/"summary/yearly_results.csv"))==24
    assert len(pd.read_csv(ROOT/"summary/trade_overlap.csv"))==6
    assert set(pd.read_csv(ROOT/"data_comparison/bar_alignment.csv").symbol)=={"Si","CNY"}
    print("H1_LEGACY_VS_V2_DECOMPOSITION_AUDIT_PASS")
    return True
if __name__=="__main__": audit()
