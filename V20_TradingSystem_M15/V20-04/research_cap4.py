"""Research ONLY: frozen V20 N4 reference replay, session quota 2 versus 4.
Does not import/live-call FINAM. Changes only one copy of frozen replay in temp.
Pin SHA of inputs; baseline must reproduce accepted 2023-2026 results to qualify.
"""
from __future__ import annotations
import ast
from collections import defaultdict
from datetime import datetime
import hashlib
import importlib
import json
import math
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
ORIGINAL=ROOT/'research_original_v20'
DATA_SHA={
'USDRUBF':'fef80630080a4e2a5e968d620b663f51acd1b7ab9d5d326a42c68cf2b80c67b8',
'CNYRUBF':'259298733d1528c0d917b100118896009519a9f08bdad33d4b373d9ce86f99b4',
'GLDRUBF':'7381d672485b5687ca2c4d92aa5960c24bb132f527589bae3c622b2dfa20a83d',
'IMOEXF':'a1b9fa6102a955103d61b28e81533ed19de68117e30fd84ceb53e8e617559773'}
GO={'USDRUBF':21204,'CNYRUBF':1139,'GLDRUBF':1782,'IMOEXF':8252}
RUB_PER_PRICE={'USDRUBF':1000,'CNYRUBF':1000,'GLDRUBF':1,'IMOEXF':10}
TICK_RUB={'USDRUBF':10,'CNYRUBF':1,'GLDRUBF':0.1,'IMOEXF':5}
EXPECTED={'SHALLOW_PULLBACK':(797,1.911027909,512.170268322),
          'OBV_PRESSURE':(612,1.718121910,337.441919035),
          'INSIDE_DAY_RELEASE':(180,2.265248963,167.808043522)}
MODES=list(EXPECTED)
CAPITAL=(45000,50000,60000,75000,80000,100000,125000,150000,200000,300000,500000)
def sha(p):
 return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def function(path,name,globals_):
 tree=ast.parse(Path(path).read_text(encoding='utf-8'))
 node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name==name)
 ns=dict(globals_,__builtins__=__builtins__)
 exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),ns)
 return ns[name]
def literal(path,name):
 tree=ast.parse(Path(path).read_text(encoding='utf-8'))
 return ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and
   any(isinstance(t,ast.Name) and t.id==name for t in n.targets)))
def stats(df):
 q=df.sort_values(['exit_time','symbol','entry_time'],kind='stable') if len(df) else df
 net=q.net_R.to_numpy(float) if len(q) else np.zeros(0)
 p=float(net[net>0].sum()); n=float(-net[net<0].sum())
 curve=np.r_[0,np.cumsum(net)]
 return dict(trades=len(df),net_R=round(float(net.sum()),6),
    pf=round(p/n,6) if n else None,
    dd_closed_R=round(float((np.maximum.accumulate(curve)-curve).max()),6),
    wins=int((net>0).sum()),
    by_year={str(y):{'trades':len(z),'net_R':round(float(z.net_R.sum()),5),
            'pf':round(float(z.loc[z.net_R>0,'net_R'].sum()/-z.loc[z.net_R<0,'net_R'].sum()),4)
                    if (z.net_R<0).any() else None}
     for y,z in df.groupby('exit_year')})
def peak_positions(df):
 events=[]
 for t in df.itertuples():
  events.append((pd.Timestamp(t.entry_time),1,t.symbol))
  events.append((pd.Timestamp(t.exit_time),-1,t.symbol))
 events.sort(key=lambda x:(x[0],x[1])) # exit before opening at same time
 count=peak=0; by_symbol=set()
 for at,d,s in events:
  count+=d;peak=max(peak,count)
 return peak
def money_stats(df,bank):
 events=[]
 missing_risk=0
 for t in df.itertuples():
  risk1=abs(float(t.risk))*RUB_PER_PRICE[t.symbol]+2*TICK_RUB[t.symbol]
  qty=math.floor(0.015*bank/risk1) if risk1>0 else 0
  if qty<=0: missing_risk+=1
  go=qty*GO[t.symbol]
  events.append((pd.Timestamp(t.entry_time),1,go))
  events.append((pd.Timestamp(t.exit_time),-1,go))
 events.sort(key=lambda x:(x[0],x[1]))
 current=maximum=0; violations=0
 for ts,d,go in events:
  current+=d*go
  maximum=max(maximum,current)
  if d==1 and current>bank:violations+=1
 return dict(bank=bank,risk_infeasible_trades=missing_risk,
             peak_risk_sized_go=maximum,go_over_cap_at_entry=violations)
def run(root:Path,out:Path):
 for sym,expected in DATA_SHA.items():
  p=root/sym/(sym+'_M15.csv')
  assert sha(p)==expected, 'DATA_SHA_FAIL_'+sym
 assert sha(ORIGINAL/'base.py')=='b7b9df00f8d7fb0a88c5cba103034e5a2335d8ebd5476aa59d'
 assert sha(ORIGINAL/'run.py')=='223545374f98d8c87cf2c09b3a7302b05b07020dc8bf34b5984ebaa3d74389fe'
 with TemporaryDirectory(prefix='v20-cap4-scratch-') as scratch:
  tmp=Path(scratch);quotes=tmp/'marketdata_m15';quotes.mkdir()
  for sym in DATA_SHA:shutil.copy2(root/sym/(sym+'_M15.csv'),quotes/(sym+'_M15.csv'))
  base_original=(ORIGINAL/'base.py').read_text(encoding='utf-8')
  assert base_original.count('and nent<2:')==1, 'FROZEN_QUOTA_ANCHOR_MISMATCH'
  (tmp/'base.py').write_text(base_original,encoding='utf-8')
  (tmp/'base_cap4.py').write_text(base_original.replace('and nent<2:','and nent<4:'),encoding='utf-8')
  shutil.copy2(ORIGINAL/'run.py',tmp/'run.py')
  sys.path.insert(0,str(tmp))
  baseline=importlib.import_module('base')
  candidate=importlib.import_module('base_cap4')
  signals=importlib.import_module('run')
  legacy=ORIGINAL/'legacy_v4'
  prep=function(legacy/'dependencies'/'study.py','prep',dict(pd=pd,np=np,ROOT=quotes))
  add=function(legacy/'study_v4.py','add_indicators',
               dict(pd=pd,np=np,MODES=literal(legacy/'study_v4.py','MODES')))
  d={}
  scope={}
  for sym in baseline.SYMS:
   f=signals.signals(sym)
   v=add(prep(sym),sym)
   assert f.Datetime.equals(v.Datetime) and f.day.equals(v.day), 'INSIDE_TIMESTAMPS_MISMATCH_'+sym
   assert np.allclose(f.atr,v.atr,equal_nan=True,atol=1e-12,rtol=1e-12), 'INSIDE_ATR_MISMATCH_'+sym
   f['INSIDE_DAY_RELEASE']=v.INSIDE_DAY_RELEASE.to_numpy()
   f['INSIDE_DAY_RELEASE_target']=np.nan
   f['INSIDE_DAY_RELEASE_tpr']=np.nan
   d[sym]=f
   scope[sym]=dict(rows=len(f),start=str(f.Datetime.iloc[0]),end=str(f.Datetime.iloc[-1]),
                   signals={m:int((f[m]!=0).sum()) for m in MODES})
  outcomes={}
  all_baseline_ok=True
  for m in MODES:
   a,open_a=baseline.merged(d,m)
   b,open_b=candidate.merged(d,m)
   old=stats(a);new=stats(b)
   expected=EXPECTED[m]
   parity=(old['trades']==expected[0] and
           abs(old['pf']-expected[1])<0.00001 and
           abs(old['net_R']-expected[2])<0.00001)
   all_baseline_ok&=parity
   basekey=set(zip(a.symbol,a.entry_time,a.side))
   newkey=set(zip(b.symbol,b.entry_time,b.side))
   extra=sorted(newkey-basekey)
   lost=sorted(basekey-newkey)
   counts=b.groupby('entry_day').size() if len(b) else pd.Series(dtype='int64')
   peaks=peak_positions(b)
   money=[money_stats(b,B) for B in CAPITAL]
   outcomes[m]=dict(baseline=old,candidate=new,
      baseline_parity_accepted=bool(parity),accepted_expected_trades=expected[0],
      delta_trades=len(b)-len(a),delta_net_R=round(new['net_R']-old['net_R'],6),
      delta_pf=round(new['pf']-old['pf'],6) if new['pf'] is not None and old['pf'] is not None else None,
      added_entry_keys=len(extra),removed_entry_keys=len(lost),
      sessions_3_new_entries=int((counts==3).sum()),sessions_4_new_entries=int((counts==4).sum()),
      peak_simultaneous_positions=peaks,remaining_open_2=len(open_a),remaining_open_4=len(open_b),
      sizing_sensitivity_go_2026_snapshot=money)
   print('CAP4_SUMMARY '+m+' '+json.dumps({k:outcomes[m][k] for k in
          ('baseline','candidate','baseline_parity_accepted','delta_trades','delta_net_R',
           'delta_pf','sessions_3_new_entries','sessions_4_new_entries','peak_simultaneous_positions')},
          ensure_ascii=False,separators=(',',':')),flush=True)
   print('CAP4_SIZING '+m+' '+json.dumps(money,ensure_ascii=False,separators=(',',':')),flush=True)
  report=dict(schema='v20.cap4.offline.candidate.20261103',source_repo='market-pattern-data',
    source_ref='f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8',
    historical_source_sha256=DATA_SHA,valid_frozen_baseline=bool(all_baseline_ok),
    model='ORIGINAL_FROZEN_REPLAY_ONLY_NENT2_VS4_NO_LIVE_NO_BROKER',
    quote_scope=scope,go_snapshot_rub_per_contract=GO,
    go_scope='INDICATIVE_OWNER_PREVIOUS_READONLY_NOT_HISTORICALLY_STABLE',
    risk_size='1.5pct_of_constant_test_equity_each_independent_trade_not_live_portfolio_sizing',
    results=outcomes)
  out.parent.mkdir(parents=True,exist_ok=True)
  out.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
  print('CAP4_BASELINE_PARITY='+('PASS' if all_baseline_ok else 'MISMATCH'),flush=True)
  print('CAP4_JSON_PATH='+str(out),flush=True)

if __name__=='__main__':
 if len(sys.argv)!=3:raise SystemExit('usage: research_cap4.py <pinned_quotes_folder> <output.json>')
 run(Path(sys.argv[1]),Path(sys.argv[2]))
