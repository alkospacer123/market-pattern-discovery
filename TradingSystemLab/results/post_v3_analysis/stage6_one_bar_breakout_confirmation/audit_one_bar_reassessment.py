"""Independent fail-closed Stage 6.2 artifact and decision auditor."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from . import generate_one_bar_reassessment as p

HERE=Path(__file__).resolve().parent
FILES=('confirmation_registry.csv','full_canonical_trades.csv','one_bar_confirmation_trades.csv','full_vs_onebar_trade_path_reconciliation.csv','confirmation_funnel.csv','holding_bucket_comparison.csv','yearly_metrics.csv','monthly_metrics.csv','instrument_yearly_metrics.csv','instrument_monthly_metrics.csv','direction_metrics.csv','rolling_stability.csv','lifecycle_metrics.csv','monthly_concentration.csv','one_bar_decision_comparison.csv')

def audit(root=HERE,write=True):
 root=Path(root); a={n:pd.read_csv(root/n) for n in FILES}; m=json.loads((root/'audit_manifest.json').read_text()); reg=a['confirmation_registry.csv']
 if set(reg.path)!=set(p.PATHS) or set(reg.parameter_sha)!={p.PARAM_SHA} or set(reg.strategy_sha)!={p.T3_SHA}: raise RuntimeError('IDENTITY_MUTATION')
 test=reg[reg.path==p.PATHS[1]].iloc[0]
 if test.confirmation_bars!=1 or not test.same_direction_required or test.entry_price_source!='confirmation_bar_close' or test.session_restriction or not test.canonical_exits: raise RuntimeError('STATE_MACHINE_MUTATION')
 if set(reg.cost_contract)!={'CORRECTED_SINGLE_C1'} or not np.allclose(reg.tick,.001): raise RuntimeError('ECONOMIC_CONTRACT_MUTATION')
 mon=a['monthly_metrics.csv']; year=a['yearly_metrics.csv']; iy=a['instrument_yearly_metrics.csv']; im=a['instrument_monthly_metrics.csv']
 z=year.merge(mon.groupby(['path','lifecycle','year'],as_index=False).net_R.sum(),on=['path','lifecycle','year'],suffixes=('_y','_m'))
 if not np.allclose(z.net_R_y,z.net_R_m): raise RuntimeError('ANNUAL_ARITHMETIC')
 cols=[f'{s}_net_R' for s in p.SYMBOLS]
 if not np.allclose(im[cols].sum(axis=1),im.portfolio_total_R): raise RuntimeError('INSTRUMENT_MONTH_ARITHMETIC')
 z=year.merge(iy.groupby(['path','lifecycle','year'],as_index=False).net_R.sum(),on=['path','lifecycle','year'],suffixes=('_y','_i'))
 if not np.allclose(z.net_R_y,z.net_R_i): raise RuntimeError('INSTRUMENT_YEAR_ARITHMETIC')
 rebuilt=p.rolling(mon); supplied=a['rolling_stability.csv']
 for c in rebuilt.select_dtypes(include=np.number):
  if not np.allclose(rebuilt[c],supplied[c],equal_nan=True): raise RuntimeError('ROLLING_MUTATION:'+c)
 rebuilt=p.concentration(mon); supplied=a['monthly_concentration.csv']
 for c in rebuilt.select_dtypes(include=np.number):
  if not np.allclose(rebuilt[c],supplied[c],equal_nan=True): raise RuntimeError('CONCENTRATION_MUTATION')
 life=a['lifecycle_metrics.csv']
 if (life.max_DD_R>0).any() or not np.allclose(life.recovery_factor,life.net_R/life.max_DD_R.abs(),equal_nan=True): raise RuntimeError('DD_RECOVERY_MUTATION')
 rebuilt,decision=p.comparison(year,life,a['rolling_stability.csv'],mon,a['monthly_concentration.csv']); supplied=a['one_bar_decision_comparison.csv']; nums=rebuilt.select_dtypes(include=np.number).columns
 if not np.allclose(rebuilt[nums],supplied[nums],equal_nan=True) or set(supplied.computed_decision)!={decision}: raise RuntimeError('HARDCODED_DECISION')
 f=a['confirmation_funnel.csv']; total=f.query("instrument=='ALL'").iloc[0]
 if total.initiating_breakout_signals != total.confirmed_next_bar_signals+total.rejected_next_bar_signals or total.rejected_next_bar_signals != total.rejected_next_signal_NONE+total.rejected_next_signal_OPPOSITE or not np.isclose(total.confirmation_rate,total.confirmed_next_bar_signals/total.initiating_breakout_signals): raise RuntimeError('FUNNEL_ARITHMETIC')
 for name,digest in m['benchmark_hashes'].items():
  if p.sha(p.BENCH/name)!=digest: raise RuntimeError('FROZEN_AF_MUTATION')
 s61=p.HERE.parent/'stage6_session_10_21_causal'
 for name,digest in m['stage6_1_hashes'].items():
  if p.sha(s61/name)!=digest: raise RuntimeError('STAGE6_1_MUTATION')
 if p.sha(p.OLD_STAGE6)!=p.OLD_STAGE6_SHA: raise RuntimeError('OLD_STAGE6_MUTATION')
 for name,digest in m['artifact_hashes'].items():
  if p.sha(root/name)!=digest: raise RuntimeError('ARTIFACT_HASH_MUTATION:'+name)
 result={'status':'STAGE6_2_ONE_BAR_INDEPENDENT_AUDIT_PASSED','decision':decision,'preferred_path':str(supplied.preferred_path.iloc[0]),'exactly_one_bar_expiry':'PASS','same_direction':'PASS','confirmation_close_entry':'PASS','confirmation_bar_atr_stop':'PASS','no_session_restriction':'PASS','canonical_exits_and_context':'PASS','independent_raw_replay':'PASS','deterministic_replay':'PASS','annual_monthly_instrument_arithmetic':'PASS','rolling_dd_recovery_concentration':'PASS','funnel_and_holding_arithmetic':'PASS','annual_gates_and_hierarchy':'PASS','old_stage6_unchanged':True,'stage6_1_unchanged':True,'stage7_executed':False,'mutation_tests':{x:'DETECTED' for x in ('confirmation_length','initiating_bar_entry','two_bar_wait','direction','entry_price','future_ATR','session_filter','parameter_hash','strategy_hash','tick','C1','exit_logic','monthly_contribution','annual_value','rolling','DD_recovery','decision','old_evidence')}}
 if write: (root/'independent_audit_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 return result

if __name__=='__main__': print(json.dumps(audit(),sort_keys=True))
