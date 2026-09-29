"""Deterministic, additive generator/verifier for the final pre-Stage-7 audit.

The frozen CSV/report bundle was produced from raw-data TRAIL1 replay.  This
entry point authenticates the identities, independently replays all four
predeclared instruments twice, reconstructs the principal metrics and exact
entry-key bridge, and fails if they differ from the published bundle.  It never
selects, optimizes, or executes Stage 7.
"""
from __future__ import annotations
import hashlib,json,subprocess
from pathlib import Path
import numpy as np
import pandas as pd
from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation import stage5_trail1_lifecycle as trail

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[3]
STAGE5=HERE.parent/'stage5_structural_validation'; STAGE6=HERE.parent/'stage6_production_assembly'
SYMBOLS=('CNYRUBF','GLDRUBF','IMOEXF','USDRUBF'); SELECTED=SYMBOLS[:3]
LIFECYCLES=('baseline','walk_forward','historical_true_oos')
ASSEMBLY_ID='PROD_STAGE6_83C7B31BB42C'; DECISION='CURRENT_STAGE6_ASSEMBLY_SUPPORTED_FOR_STAGE7'
STATUS='FINAL_PRE_STAGE7_INDEPENDENT_AUDIT_PASSED'
DECISION_SHA='1efdaac2b689e2537b17371407a4d219dec5334c490a56c2378b065b9055431b'
TRAIL_SHA='d1d8ac2eeea9095becd6f74295e4a540d02ee0494237af5f16f6d66a487f221b'
T3_SHA='840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def registry_frame():
 r=pd.read_csv(STAGE5/'canonical_lifecycle_registry.csv',keep_default_na=False)
 return r[(r.generation=='v3_perpetual')&(r.strategy=='T3')&(r.timeframe=='H1')&r.instrument.isin(SYMBOLS)&r.lifecycle.isin(LIFECYCLES)].copy()
def replay(data_root):
 rows=registry_frame().sort_values(['lifecycle','fold_id','instrument'],kind='mergesort').to_dict('records')
 return trail._dispatch(rows,data_root,True).sort_values(['lifecycle','fold_id','exit_time','instrument','trade_id'],kind='mergesort').reset_index(drop=True)
def canonical():
 x=trail._canonical_frame(); return x[(x.generation=='v3_perpetual')&(x.strategy=='T3')&(x.timeframe=='H1')&x.instrument.isin(SYMBOLS)&x.lifecycle.isin(LIFECYCLES)].copy()
def ordered(x): return x.sort_values(['fold_id','exit_time','instrument','entry_time'],kind='mergesort')
def metrics(x,col='net_R_C1'):
 v=pd.to_numeric(ordered(x)[col]); loss=float(v[v<0].sum()); curve=pd.concat([pd.Series([0.]),v.reset_index(drop=True).cumsum()]); dd=float((curve-curve.cummax()).min()); net=float(v.sum())
 return {'trades':len(v),'net_R':net,'PF':float(v[v>0].sum())/abs(loss) if loss else None,'expectancy_R':float(v.mean()) if len(v) else 0.,'max_DD_R':dd,'recovery_factor':net/abs(dd) if dd else None,'win_rate':float((v>0).mean()) if len(v) else 0.,'median_trade_R':float(v.median()) if len(v) else 0.}
def entry_key(x):
 return x.lifecycle.astype(str)+'|'+x.fold_id.fillna('').astype(str)+'|'+x.instrument.astype(str)+'|'+x.direction.astype(str)+'|'+pd.to_datetime(x.entry_time,utc=True).astype(str)+'|'+pd.to_numeric(x.entry_price).map(lambda n:format(n,'.12g'))
def reconciliation(base,overlay):
 a,b=base.copy(),overlay.copy(); a['trade_key']=entry_key(a); b['trade_key']=entry_key(b)
 if a.trade_key.duplicated().any() or b.trade_key.duplicated().any(): raise RuntimeError('NON_UNIQUE_TRADE_KEY')
 l=a[['trade_key','lifecycle','fold_id','instrument','direction','entry_time','entry_price','exit_time','net_R_C1']].rename(columns={'exit_time':'canonical_exit_time','net_R_C1':'canonical_R'})
 rr=b[['trade_key','lifecycle','fold_id','instrument','direction','entry_time','entry_price','exit_time','net_R_C1']].rename(columns={'lifecycle':'right_lifecycle','fold_id':'right_fold_id','instrument':'right_instrument','direction':'right_direction','entry_time':'right_entry_time','entry_price':'right_entry_price','exit_time':'trail1_exit_time','net_R_C1':'trail1_R'})
 r=l.merge(rr,on='trade_key',how='outer',indicator=True)
 for c in ('lifecycle','fold_id','instrument','direction','entry_time','entry_price'): r[c]=r[c].fillna(r.pop('right_'+c))
 r['path_class']=r._merge.map({'both':'MATCHED','left_only':'CANONICAL_ONLY','right_only':'TRAIL1_ONLY'}); r['matched_exit_delta_R']=np.where(r._merge=='both',pd.to_numeric(r.trail1_R)-pd.to_numeric(r.canonical_R),np.nan)
 rows=[]
 for (s,life),g in r.groupby(['instrument','lifecycle'],sort=True):
  cm=metrics(a[(a.instrument==s)&(a.lifecycle==life)]); tm=metrics(b[(b.instrument==s)&(b.lifecycle==life)]); matched=float(g.matched_exit_delta_R.sum()); co=float(pd.to_numeric(g.loc[g._merge=='left_only','canonical_R']).sum()); to=float(pd.to_numeric(g.loc[g._merge=='right_only','trail1_R']).sum()); delta=tm['net_R']-cm['net_R']; bridge=matched-co+to
  if abs(bridge-delta)>1e-9: raise RuntimeError('BRIDGE_FAILED')
  rows.append({'instrument':s,'lifecycle':life,'canonical_trades':cm['trades'],'canonical_net_R':cm['net_R'],'trail1_trades':tm['trades'],'trail1_net_R':tm['net_R'],'total_delta_R':delta,'matched_count':int((g._merge=='both').sum()),'matched_exit_delta_R':matched,'canonical_only_count':int((g._merge=='left_only').sum()),'canonical_only_R':co,'canonical_only_bridge_contribution_R':-co,'trail1_only_count':int((g._merge=='right_only').sum()),'trail1_only_R':to,'bridge_R':bridge,'bridge_error_R':bridge-delta})
 return r.drop(columns='_merge'),pd.DataFrame(rows)
def authenticate(data_root):
 m=json.loads((STAGE5/'trail1/manifest_trail1.json').read_text()); checks={'assembly':ASSEMBLY_ID in (STAGE6/'production_assembly_decision.csv').read_text(),'decision_sha':sha(STAGE6/'production_assembly_decision.csv')==DECISION_SHA,'trail_sha':sha(STAGE5/'stage5_trail1_execution.py')==TRAIL_SHA,'t3_sha':sha(ROOT/'TradingSystemLab/strategies/trend/T3_MTF_Trend.py')==T3_SHA,'contract':m['cost_contract']=='CORRECTED_SINGLE_C1','data_commit':subprocess.check_output(['git','-C',str(data_root),'rev-parse','HEAD'],text=True).strip()==m['data_repo_commit']}
 sources={p:h for p,h in m['source_hashes'].items() if p.endswith('_H1.csv') and any('/'+s+'/' in p for s in SYMBOLS)}; checks['sources']=len(sources)==4 and all(sha(data_root/p)==h for p,h in sources.items())
 if not all(checks.values()): raise RuntimeError(f'AUTHENTICATION_FAILED {checks}')
 return checks
def _same_csv(actual,expected,keys):
 a=pd.read_csv(actual).sort_values(keys).reset_index(drop=True); e=expected.sort_values(keys).reset_index(drop=True)
 if list(a.columns)!=list(e.columns) or len(a)!=len(e): return False
 for c in a:
  if pd.api.types.is_numeric_dtype(a[c]) and pd.api.types.is_numeric_dtype(e[c]):
   if not np.allclose(a[c],e[c],atol=1e-9,equal_nan=True): return False
  elif not a[c].fillna('').astype(str).equals(e[c].fillna('').astype(str)): return False
 return True
def execute(data_root):
 auth=authenticate(data_root); base=canonical(); one=replay(data_root); two=replay(data_root)
 f=lambda x:hashlib.sha256(x.to_csv(index=False,lineterminator='\n',float_format='%.12g').encode()).hexdigest()
 if f(one)!=f(two): raise RuntimeError('NONDETERMINISTIC_RAW_REPLAY')
 recon,decomp=reconciliation(base,one); recon2,decomp2=reconciliation(base,two)
 summary=[]
 for s in SYMBOLS:
  for life in LIFECYCLES:
   cm=metrics(base[(base.instrument==s)&(base.lifecycle==life)]); tm=metrics(one[(one.instrument==s)&(one.lifecycle==life)]); row={'instrument':s,'lifecycle':life,**{'canonical_'+k:v for k,v in cm.items()},**{'trail1_'+k:v for k,v in tm.items()}}
   for k in ('net_R','PF','expectancy_R','max_DD_R','recovery_factor'): row['delta_'+k]=tm[k]-cm[k] if tm[k] is not None and cm[k] is not None else None
   summary.append(row)
 checks={'summary_rebuilt':_same_csv(HERE/'instrument_canonical_vs_trail1_summary.csv',pd.DataFrame(summary),['instrument','lifecycle']),'decomposition_rebuilt':_same_csv(HERE/'trade_path_decomposition.csv',decomp,['instrument','lifecycle']),'reconciliation_rows':len(pd.read_csv(HERE/'trade_path_reconciliation.csv'))==len(recon),'bridge_identities':np.allclose(decomp.matched_exit_delta_R-decomp.canonical_only_R+decomp.trail1_only_R,decomp.total_delta_R,atol=1e-9),'deterministic_isolated_raw_rerun':f(one)==f(two) and f(decomp)==f(decomp2),'stage6_unchanged':sha(STAGE6/'production_assembly_decision.csv')==DECISION_SHA}
 if not all(checks.values()): raise RuntimeError(f'INDEPENDENT_AUDIT_FAILED {checks}')
 return {'status':STATUS,'decision':DECISION,'authentication':auth,'checks':checks,'event_sha256_runs':[f(one),f(two)]}
if __name__=='__main__':
 from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation.run_stage5_trail1 import resolve_data_root
 root,_=resolve_data_root(); print(json.dumps(execute(root),sort_keys=True))
