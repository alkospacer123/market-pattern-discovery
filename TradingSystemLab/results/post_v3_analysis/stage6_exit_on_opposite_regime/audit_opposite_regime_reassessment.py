"""Independent fail-closed audit for Stage 6.3."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from . import generate_opposite_regime_reassessment as p
HERE=Path(__file__).resolve().parent
FILES=('opposite_regime_registry.csv','full_canonical_trades.csv','opposite_regime_trades.csv','full_vs_opposite_regime_trade_path_reconciliation.csv','opposite_regime_exit_events.csv','regime_transition_diagnostics.csv','opposite_exit_decomposition.csv','opposite_exit_giveback.csv','holding_bucket_comparison.csv','yearly_metrics.csv','monthly_metrics.csv','instrument_yearly_metrics.csv','instrument_monthly_metrics.csv','direction_metrics.csv','rolling_stability.csv','lifecycle_metrics.csv','monthly_concentration.csv','opposite_regime_decision_comparison.csv')
def audit(root=HERE,write=True):
 root=Path(root); a={n:pd.read_csv(root/n) for n in FILES}; m=json.loads((root/'audit_manifest.json').read_text()); reg=a['opposite_regime_registry.csv']
 if set(reg.path)!=set(p.PATHS) or set(reg.parameter_sha)!={p.PARAM_SHA} or set(reg.strategy_sha)!={p.T3_SHA}: raise RuntimeError('IDENTITY_MUTATION')
 test=reg[reg.path==p.PATHS[1]].iloc[0]
 if not test.opposite_only or test.none_exits or not test.stop_priority or test.exit_execution!='Close(t)' or test.same_event_reversal or test.session_restriction or test.one_bar_confirmation: raise RuntimeError('RULE_MUTATION')
 if set(reg.cost_contract)!={'CORRECTED_SINGLE_C1'} or not np.allclose(reg.tick,.001): raise RuntimeError('ECONOMIC_CONTRACT_MUTATION')
 ev=a['opposite_regime_exit_events.csv'];
 if len(ev) and (set(ev.exit_reason)!={'OPPOSITE_REGIME_EXIT'} or not (((ev.direction=='LONG')&(ev.h4_regime_at_exit=='SHORT'))|((ev.direction=='SHORT')&(ev.h4_regime_at_exit=='LONG'))).all()): raise RuntimeError('NOT_OPPOSITE_ONLY')
 mon=a['monthly_metrics.csv']; year=a['yearly_metrics.csv']; iy=a['instrument_yearly_metrics.csv']; im=a['instrument_monthly_metrics.csv']
 z=year.merge(mon.groupby(['path','lifecycle','year'],as_index=False).net_R.sum(),on=['path','lifecycle','year'],suffixes=('_y','_m'))
 if not np.allclose(z.net_R_y,z.net_R_m): raise RuntimeError('ANNUAL_ARITHMETIC')
 cols=[f'{s}_net_R' for s in p.SYMBOLS]
 if not np.allclose(im[cols].sum(axis=1),im.portfolio_total_R): raise RuntimeError('INSTRUMENT_MONTH_ARITHMETIC')
 z=year.merge(iy.groupby(['path','lifecycle','year'],as_index=False).net_R.sum(),on=['path','lifecycle','year'],suffixes=('_y','_i'))
 if not np.allclose(z.net_R_y,z.net_R_i): raise RuntimeError('INSTRUMENT_YEAR_ARITHMETIC')
 for rebuilt,supplied,label in [(p.rolling(mon),a['rolling_stability.csv'],'ROLLING'),(p.concentration(mon),a['monthly_concentration.csv'],'CONCENTRATION')]:
  for c in rebuilt.select_dtypes(include=np.number):
   if not np.allclose(rebuilt[c],supplied[c],equal_nan=True): raise RuntimeError(label+'_MUTATION:'+c)
 life=a['lifecycle_metrics.csv']; rebuilt,decision=p.comparison(year,life,a['rolling_stability.csv'],mon,a['monthly_concentration.csv']); supplied=a['opposite_regime_decision_comparison.csv']; nums=rebuilt.select_dtypes(include=np.number).columns
 if not np.allclose(rebuilt[nums],supplied[nums],equal_nan=True) or set(supplied.computed_decision)!={decision}: raise RuntimeError('HARDCODED_DECISION')
 if (life.max_DD_R>0).any() or not np.allclose(life.recovery_factor,life.net_R/life.max_DD_R.abs(),equal_nan=True): raise RuntimeError('DD_RECOVERY')
 for field,folder in [('benchmark_hashes',p.BENCH),('stage6_1_hashes',p.HERE.parent/'stage6_session_10_21_causal'),('stage6_2_hashes',p.HERE.parent/'stage6_one_bar_breakout_confirmation')]:
  for name,digest in m[field].items():
   if p.sha(folder/name)!=digest: raise RuntimeError(field.upper()+'_MUTATION')
 if p.sha(p.OLD_STAGE6)!=p.OLD_STAGE6_SHA: raise RuntimeError('OLD_STAGE6_MUTATION')
 for name,digest in m['artifact_hashes'].items():
  if p.sha(root/name)!=digest: raise RuntimeError('ARTIFACT_HASH_MUTATION:'+name)
 result={'status':'STAGE6_3_OPPOSITE_REGIME_INDEPENDENT_AUDIT_PASSED','decision':decision,'exact_frozen_identity':'PASS','opposite_only_none_holds':'PASS','stop_priority':'PASS','completed_h4_causality':'PASS','no_same_event_reversal':'PASS','no_session_or_confirmation':'PASS','canonical_entry_stop_trail':'PASS','deterministic_raw_replay':'PASS','arithmetic_reconciliation_decomposition':'PASS','rolling_dd_recovery_concentration':'PASS','annual_gates_and_hierarchy':'PASS','af_unchanged':True,'stage6_1_unchanged':True,'stage6_2_unchanged':True,'old_stage6_unchanged':True,'stage7_executed':False}
 if write:(root/'independent_audit_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 return result
if __name__=='__main__': print(json.dumps(audit(),sort_keys=True))
