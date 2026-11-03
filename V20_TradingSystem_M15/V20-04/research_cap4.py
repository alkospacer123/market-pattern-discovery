"""Research ONLY: frozen V20 N4 reference replay, entry quotas 1, 2, 3, 4.
Does not import/live-call FINAM. Changes only the quota constant in temporary frozen replay copies.
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
def full_r15_margin_audit(trades,bank):
 """Diagnostic: no cap by GO, risk sizing exact to 1.5% C1; constant nominal equity.
 Not an order-admission simulation. Broker account/GO charges may differ.
 """
 events=[]
 zero_qty=0
 for t in trades.itertuples():
  per_lot=abs(float(t.risk))*RUB_PER_PRICE[t.symbol]+2*TICK_RUB[t.symbol]
  qty=math.floor(0.015*bank/per_lot+1e-9)
  if qty==0:zero_qty+=1
  req=qty*(GO[t.symbol]+2*TICK_RUB[t.symbol])
  if not req:continue
  at=pd.Timestamp(t.entry_time);out=pd.Timestamp(t.exit_time)
  # Entry-bar stop: book entry before release at identical time.
  events.append((at,1,0,t.symbol,req,qty,per_lot))
  events.append((out,2 if at==out else 0,1,t.symbol,req,qty,per_lot))
 events.sort(key=lambda v:(v[0],v[1],v[2]))
 used=0;peak=0;when=None;exceeded=0;single_over=0;detail=None
 active={}
 for at,priority,ex,sym,req,qty,per_lot in events:
  if ex:
   used-=req
   del active[sym]
  else:
   if req>bank:single_over+=1
   used+=req
   active[sym]=(qty,req)
   if used>bank:exceeded+=1
   if used>peak:
    peak=used
    when=str(at)
    detail={'symbol':sym,'one_lot_risk_rub':round(per_lot,2),
            'latest_qty':qty,'active_positions':{k:v[0] for k,v in active.items()}}
 assert round(used,6)==0,(bank,used)
 return {'bank':bank,'total_peak_GO_incl_C1':round(peak,2),
         'peak_to_bank':round(peak/bank,4),
         'peak_date':when,'peak_positions':detail,
         'risk_qty_zero_trades':zero_qty,
         'entry_go_over_bank':exceeded,
         'single_position_go_over_bank':single_over}

def run(root:Path,out:Path):
 for sym,expected in DATA_SHA.items():
  p=root/sym/(sym+'_M15.csv')
  assert sha(p)==expected, 'DATA_SHA_FAIL_'+sym
 import subprocess
 for name,expected in [('base.py','b917cc9c7c99fbad38423d9f4fdfbb82767545be'),
                       ('run.py','7d9ddf0ef498f0c93a139c0104af2a72d0e79151')]:
  p=ORIGINAL/name
  actual=subprocess.check_output(['git','hash-object','--',str(p)],text=True).strip()
  assert actual==expected, f'FROZEN_GIT_BLOB_MISMATCH_{name}:{actual}'
  print('FROZEN_SHA256_'+name+'='+sha(p),flush=True)
 with TemporaryDirectory(prefix='v20-cap4-scratch-') as scratch:
  tmp=Path(scratch);quotes=tmp/'marketdata_m15';quotes.mkdir()
  for sym in DATA_SHA:shutil.copy2(root/sym/(sym+'_M15.csv'),quotes/(sym+'_M15.csv'))
  base_original=(ORIGINAL/'base.py').read_text(encoding='utf-8')
  assert base_original.count('and nent<2:')==1, 'FROZEN_QUOTA_ANCHOR_MISMATCH'
  (tmp/'base.py').write_text(base_original,encoding='utf-8')
  for k in (1,3,4):
   (tmp/f'base_cap{k}.py').write_text(base_original.replace('and nent<2:',f'and nent<{k}:'),encoding='utf-8')
  shutil.copy2(ORIGINAL/'run.py',tmp/'run.py')
  sys.path.insert(0,str(tmp))
  baseline=importlib.import_module('base')
  variants={2:baseline}
  for k in (1,3,4):
   variants[k]=importlib.import_module(f'base_cap{k}')
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
  expected4={'SHALLOW_PULLBACK':(875,1.887632,549.941377),
             'OBV_PRESSURE':(655,1.764397,381.264922),
             'INSIDE_DAY_RELEASE':(183,2.211002,164.553984)}
  for m in MODES:
   variations={}
   for k in (1,2,3,4):
    trades,open_positions=variants[k].merged(d,m)
    q=stats(trades)
    counts=trades.groupby('entry_day').size() if len(trades) else pd.Series(dtype='int64')
    events=[]
    risk_by_symbol=defaultdict(list)
    for t in trades.itertuples():
     cost=abs(float(t.risk))*RUB_PER_PRICE[t.symbol]+2*TICK_RUB[t.symbol]
     risk_by_symbol[t.symbol].append(cost)
     entry_ts=pd.Timestamp(t.entry_time)
     exit_ts=pd.Timestamp(t.exit_time)
     events.append((entry_ts,1,1,t.symbol))
     # A stop on the entry bar needs margin at entry, then closes;
     # normal old exits release before fresh same-timestamp entries.
     events.append((exit_ts,2 if exit_ts==entry_ts else 0,-1,t.symbol))
    events.sort(key=lambda x:(x[0],x[1]))
    go=0;go_max=0;slots=0;slots_max=0;active=set()
    for dt,priority,direction,sym in events:
     if direction==1:
      assert sym not in active,('REPLAY_SAME_SYMBOL_ACTIVE',m,k,sym,dt)
      active.add(sym)
     else:
      assert sym in active,('REPLAY_UNKNOWN_EXIT',m,k,sym,dt)
      active.remove(sym)
     go+=direction*GO[sym]
     slots+=direction
     assert go>=0 and slots==len(active)
     go_max=max(go_max,go)
     slots_max=max(slots_max,slots)
    max_risk_1lot=max((max(v) for v in risk_by_symbol.values()),default=0)
    max_by_symbol={sym:round(max(risk_by_symbol.get(sym,[0])),2) for sym in GO}
    common_candidate_floor_risk=math.ceil(max_risk_1lot/0.015)
    theoretical_go_any_active_combination=sum(sorted(GO.values(),reverse=True)[:slots_max])
    # GO 50% buffer is illustrative; real FINAM GO and costs are not static.
    common_candidate_floor_go=math.ceil(1.5*theoretical_go_any_active_combination)
    variations[str(k)]=dict(metrics=q,remaining_open=len(open_positions),
       session_3_entries=int((counts==3).sum()),session_4_entries=int((counts==4).sum()),
       max_simultaneously_open=slots_max,
       one_lot_observed_peak_go=go_max,
       one_lot_worst_combination_go=theoretical_go_any_active_combination,
       one_lot_risk_max_by_symbol=max_by_symbol,
       floor_bank_for_one_lot_risk=common_candidate_floor_risk,
       floor_bank_worst_go_50pct_buffer=common_candidate_floor_go,
       floor_bank_one_lot_overall=max(common_candidate_floor_risk,common_candidate_floor_go))
   r2=variations['2']['metrics'];r4=variations['4']['metrics']
   expected=EXPECTED[m];check4=expected4[m]
   parity=(r2['trades']==expected[0] and
           abs(r2['pf']-expected[1])<0.00001 and
           abs(r2['net_R']-expected[2])<0.00001 and
           r4['trades']==check4[0] and
           abs(r4['pf']-check4[1])<0.00001 and
           abs(r4['net_R']-check4[2])<0.00001)
   all_baseline_ok&=parity
   outcomes[m]=dict(baseline_parity_accepted=bool(parity),
                    quotas=variations)
   print('CAP1234_SUMMARY '+m+' '+json.dumps(outcomes[m],ensure_ascii=False,separators=(',',':')),flush=True)
  for m in MODES:
   checks={}
   for k in (2,3):
    ledger,_=variants[k].merged(d,m)
    checks[str(k)]=[full_r15_margin_audit(ledger,b) for b in (45000,68000,100000,200000,500000,1000000)]
   outcomes[m]['dynamic_full_r15_GO_diagnostic']=checks
   print('CAP23_DYNAMIC_GO '+m+' '+json.dumps(checks,ensure_ascii=False,separators=(',',':')),flush=True)
  # Research-only side-by-side cash admission on the SAME historical
  # candidate ledger. Skipped trades do not free up alternative signals:
  # these results are indicative, not full counterfactual replays.
  from research_go_reservation import compare as go_compare
  for m in MODES:
   allocation={}
   for k in (2,3):
    ledger,_=variants[k].merged(d,m)
    for bank in (45000,68000,100000,150000):
     for policy in ("half","n4"):
      observation=go_compare(ledger,bank,policy,GO,RUB_PER_PRICE,TICK_RUB)
      allocation[f"{k}:{bank}:{policy}"]=observation
      print("GO_COMPARE "+m+" "+json.dumps(
       {"quota":k,**observation},separators=(",",":")),flush=True)
   outcomes[m]['go_reservation_cash_audit']=allocation
  common={}
  for k in (1,2,3,4):
   risk=max(outcomes[m]['quotas'][str(k)]['floor_bank_for_one_lot_risk'] for m in MODES)
   slots=max(outcomes[m]['quotas'][str(k)]['max_simultaneously_open'] for m in MODES)
   go_one_lot=sum(sorted(GO.values(),reverse=True)[:slots])
   observed_peak_go=max(outcomes[m]['quotas'][str(k)]['one_lot_observed_peak_go'] for m in MODES)
   with_buffer=math.ceil(1.5*go_one_lot)
   common[str(k)]=dict(quota=k,observed_max_open_positions=slots,
     worst_any_combination_one_lot_go=go_one_lot,
     observed_peak_one_lot_go=observed_peak_go,
     indicative_go_with_50pct_buffer=with_buffer,
     one_lot_risk_min_bank=max(risk,0),
     common_one_lot_bank_floor=max(risk,with_buffer),
     not_actual_live_dynamic_sizing=True)
  print('CAP1234_COMMON_BANK '+json.dumps(common,ensure_ascii=False,separators=(',',':')),flush=True)
  report=dict(schema='v20.cap1234.offline.candidate.20261103',
    source_repo='market-pattern-data',
    source_ref='f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8',
    historical_source_sha256=DATA_SHA,
    valid_frozen_baseline=bool(all_baseline_ok),
    model='SAME_FROZEN_REPLAY_MODIFY_SESSION_NENT_ONLY_1_2_3_4',
    quote_scope=scope,
    go_snapshot_rub_per_contract=GO,
    go_scope='OWNER_PREVIOUS_READONLY_NOT_HISTORICALLY_STABLE',
    risk_note='ONE_LOT_RISK_C1_H1_TICK_VALUE_NOT_FINAM_MARGIN_CASH_REPLAY',
    common_bank=common,results=outcomes)
  out.parent.mkdir(parents=True,exist_ok=True)
  out.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
  print('CAP1234_BASELINE_PARITY='+('PASS' if all_baseline_ok else 'MISMATCH'),flush=True)
  assert all_baseline_ok,'ACCEPTED_BASELINE_PARITY_FAILED'
  print('CAP1234_JSON_PATH='+str(out),flush=True)

if __name__=='__main__':
 if len(sys.argv)!=3:raise SystemExit('usage: research_cap4.py <pinned_quotes_folder> <output.json>')
 run(Path(sys.argv[1]),Path(sys.argv[2]))
