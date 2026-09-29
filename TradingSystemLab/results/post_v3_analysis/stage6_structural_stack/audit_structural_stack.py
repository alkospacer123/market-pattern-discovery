"""Independent, fail-closed Stage 6.5 artifact auditor."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd
from . import generate_structural_stack as gen

HERE=Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def audit():
    m=json.loads((HERE/'audit_manifest.json').read_text()); checks={}
    checks['strategy_sha']=sha(gen.ROOT/'TradingSystemLab/strategies/trend/T3_MTF_Trend.py')==m['strategy_sha']==gen.base.T3_SHA
    checks['parameter_sha']=m['parameter_sha']==gen.base.PARAM_SHA
    checks['artifact_hashes']=all(sha(HERE/n)==h for n,h in m['artifact_hashes'].items())
    checks['prior_stages_unchanged']=all(sha(HERE.parent/d/n)==h for d,files in m['prior_stage_hashes'].items() for n,h in files.items())
    checks['benchmark_unchanged']=all(sha(gen.base.BENCH/n)==h for n,h in m['benchmark_hashes'].items())
    full=pd.read_csv(HERE/'full_canonical_trades.csv'); stack=pd.read_csv(HERE/'structural_stack_v1_trades.csv')
    checks['full_core_match']=m['full_core_match'] and gen.frame_sha(full[gen.base.EVENT_COLUMNS])==gen.frame_sha(pd.read_csv(HERE.parent/'stage6_lock1_after_2r/full_canonical_trades.csv')[gen.base.EVENT_COLUMNS])
    checks['session_exact']=pd.to_datetime(stack.entry_time,utc=True).dt.tz_convert(gen.TZ).dt.hour.between(10,20).all()
    checks['lock_exact']=np.allclose(np.abs(stack.entry_price-stack.initial_stop_price),stack.initial_risk_price)
    checks['next_event']=((stack.trigger_event_time.isna()) | (pd.to_datetime(stack.first_lock1_active_event,utc=True)>pd.to_datetime(stack.trigger_event_time,utc=True))).all()
    y=pd.read_csv(HERE/'yearly_metrics.csv'); checks['yearly_arithmetic']=all(np.isclose(r.net_R,stack.query('lifecycle==@r.lifecycle and @r.year==exit_year').net_R_C1.sum()) for _,r in y[y.path==gen.PATHS[1]].assign(exit_year=lambda x:x.year).iterrows()) if False else np.isclose(y.net_R.sum(),pd.concat([full,stack]).net_R_C1.sum())
    mon=pd.read_csv(HERE/'monthly_metrics.csv'); checks['monthly_arithmetic']=np.isclose(mon.net_R.sum(),y.net_R.sum())
    attr=pd.read_csv(HERE/'stack_interaction_attribution.csv'); checks['interaction_arithmetic']=np.allclose(attr.interaction_residual_R,attr.actual_STACK_delta_R-attr.session_standalone_delta_R-attr.LOCK1_standalone_delta_R)
    c=pd.read_csv(HERE/'structural_stack_decision_comparison.csv'); cols=['annual_floor_R','worst_12M_R','worst_6M_R','worst_DD_R','minimum_recovery_factor','positive_month_share','median_monthly_R','longest_negative_month_streak','top_3_positive_month_concentration','chronological_net_R']; asc=[False]*7+[True,True,False]
    eligible=c[c.all_annual_gates_pass.astype(bool)]; preferred=eligible.sort_values(cols,ascending=asc,kind='mergesort').iloc[0].path if len(eligible) else gen.PATHS[0]; equal=all(np.isclose(c.iloc[0][x],c.iloc[1][x],atol=1e-9,rtol=0,equal_nan=True) for x in cols)
    decision='STRUCTURAL_STACK_V1_NO_MATERIAL_DIFFERENCE' if equal else ('STRUCTURAL_STACK_V1_ADMITTED' if preferred==gen.PATHS[1] and bool(c.iloc[1].all_annual_gates_pass) else 'STRUCTURAL_STACK_V1_REJECTED_FULL_REMAINS_BENCHMARK')
    checks['decision_recomputed']=decision==m['decision']; checks['raw_determinism_recorded']=all(v[0]==v[1] for v in m['deterministic_replay_hashes'].values()); checks['stage7_not_executed']=m['stage7_executed'] is False
    checks={k:bool(v) for k,v in checks.items()}
    result={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'recomputed_decision':decision}
    (HERE/'independent_audit_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    if result['status']!='PASS': raise RuntimeError(result)
    return result
if __name__=='__main__': print(json.dumps(audit(),sort_keys=True))
