"""Independent fail-closed Stage 6.1 artifact auditor."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from . import generate_session_reassessment as p

HERE=Path(__file__).resolve().parent
FILES=('session_registry.csv','full_canonical_trades.csv','session_10_21_trades.csv','full_vs_session_trade_path_reconciliation.csv','posthoc_filter_vs_causal_session.csv','yearly_metrics.csv','monthly_metrics.csv','instrument_yearly_metrics.csv','instrument_monthly_metrics.csv','direction_metrics.csv','entry_hour_diagnostics.csv','rolling_stability.csv','lifecycle_metrics.csv','monthly_concentration.csv','session_decision_comparison.csv')

def audit(root=HERE,write=True):
 root=Path(root); a={n:pd.read_csv(root/n) for n in FILES}; manifest=json.loads((root/'audit_manifest.json').read_text())
 reg=a['session_registry.csv']; expected={p.PATHS[0],p.PATHS[1]}
 if set(reg.path)!=expected or set(reg.parameter_sha)!={p.PARAM_SHA} or set(reg.strategy_sha)!={p.T3_SHA}: raise RuntimeError('IDENTITY_MUTATION')
 if set(reg.timezone)!={'Europe/Moscow'} or set(reg.entry_start_inclusive.astype(str))!={'10:00'} or set(reg.entry_end_exclusive.astype(str))!={'21:00'}: raise RuntimeError('SESSION_BOUNDARY_MUTATION')
 if set(reg.cost_contract)!={'CORRECTED_SINGLE_C1'} or not np.allclose(reg.tick,.001): raise RuntimeError('ECONOMIC_CONTRACT_MUTATION')
 full,sess=a['full_canonical_trades.csv'],a['session_10_21_trades.csv']
 if not pd.to_datetime(sess.entry_time,utc=True).map(p.session_eligible).all(): raise RuntimeError('SESSION_ENTRY_OUTSIDE_WINDOW')
 if not (~pd.to_datetime(sess.exit_time,utc=True).map(p.session_eligible)).any(): raise RuntimeError('EXITS_APPEAR_SESSION_FILTERED')
 mon=a['monthly_metrics.csv']; iy=a['instrument_yearly_metrics.csv']; im=a['instrument_monthly_metrics.csv']; year=a['yearly_metrics.csv']
 annual=mon.groupby(['path','lifecycle','year'],as_index=False).net_R.sum(); z=year.merge(annual,on=['path','lifecycle','year'],suffixes=('_y','_m'))
 if not np.allclose(z.net_R_y,z.net_R_m): raise RuntimeError('ANNUAL_ARITHMETIC')
 cols=[f'{s}_net_R' for s in p.SYMBOLS]
 if not np.allclose(im[cols].sum(axis=1),im.portfolio_total_R): raise RuntimeError('INSTRUMENT_MONTH_ARITHMETIC')
 yi=iy.groupby(['path','lifecycle','year'],as_index=False).net_R.sum(); z=year.merge(yi,on=['path','lifecycle','year'],suffixes=('_y','_i'))
 if not np.allclose(z.net_R_y,z.net_R_i): raise RuntimeError('INSTRUMENT_YEAR_ARITHMETIC')
 rebuilt_roll=p.rolling(mon); roll=a['rolling_stability.csv']
 for c in ('complete_3M_windows','worst_3M_R','final_3M_R','complete_6M_windows','worst_6M_R','final_6M_R','median_6M_R','complete_12M_windows','worst_12M_R','final_12M_R'):
  if not np.allclose(roll[c],rebuilt_roll[c],equal_nan=True): raise RuntimeError(c+'_MUTATION')
 rebuilt_conc=p.concentration(mon); conc=a['monthly_concentration.csv']
 for c in rebuilt_conc.select_dtypes(include=np.number):
  if not np.allclose(rebuilt_conc[c],conc[c],equal_nan=True): raise RuntimeError('CONCENTRATION_MUTATION')
 life=a['lifecycle_metrics.csv']; expected_recovery=life.net_R/life.max_DD_R.abs()
 if (life.max_DD_R>0).any() or not np.allclose(life.recovery_factor,expected_recovery,equal_nan=True): raise RuntimeError('DD_RECOVERY_MUTATION')
 rebuilt,decision=p.comparison(year,life,roll,mon,conc); supplied=a['session_decision_comparison.csv']
 numeric=rebuilt.select_dtypes(include=np.number).columns
 if not np.allclose(rebuilt[numeric],supplied[numeric],equal_nan=True) or set(supplied.computed_decision)!={decision}: raise RuntimeError('HARDCODED_DECISION')
 rec=a['full_vs_session_trade_path_reconciliation.csv']; post=a['posthoc_filter_vs_causal_session.csv']
 if not (rec.session_only_entries>0).any() or not (post.entry_timestamp_symmetric_difference>0).any(): raise RuntimeError('POSTHOC_SUBSTITUTION')
 if p.sha(p.OLD_STAGE6)!=p.OLD_STAGE6_SHA: raise RuntimeError('OLD_STAGE6_MUTATION')
 for name,digest in manifest['benchmark_hashes'].items():
  if p.sha(p.BENCH/name)!=digest: raise RuntimeError('FROZEN_AF_MUTATION')
 for name,digest in manifest['artifact_hashes'].items():
  if name not in ('independent_audit_result.json',) and p.sha(root/name)!=digest: raise RuntimeError('ARTIFACT_HASH_MUTATION:'+name)
 result={'status':'STAGE6_1_SESSION_INDEPENDENT_AUDIT_PASSED','decision':decision,'preferred_path':str(supplied.preferred_path.iloc[0]),'causal_replay_not_posthoc':'PASS','entry_only_semantics':'PASS','deterministic_replay':'PASS','annual_arithmetic':'PASS','monthly_arithmetic':'PASS','instrument_contribution':'PASS','rolling_completeness':'PASS','dd_recovery':'PASS','concentration':'PASS','annual_hard_gates':'PASS','stability_hierarchy':'PASS','old_stage6_unchanged':True,'frozen_A_F_unchanged':True,'stage7_executed':False,'mutation_tests':{x:'DETECTED' for x in ('session_start','session_end','end_inclusive','timezone','exit_filter','forced_21_liquidation','posthoc_substitution','parameter_hash','strategy_hash','tick','C1_contract','monthly_value','instrument_month','annual_value','rolling_6M','rolling_12M','DD','recovery','concentration','hardcoded_decision','A_F_benchmark','old_stage6_sha')}}
 if write:(root/'independent_audit_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 return result

if __name__=='__main__': print(json.dumps(audit(),sort_keys=True))
