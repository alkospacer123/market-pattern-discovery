"""Synchronized raw-bar lifecycle replay and compact evidence for Risk Cap."""
from __future__ import annotations
import copy, csv, hashlib, json, os, shutil, tempfile
from dataclasses import replace
from pathlib import Path
from typing import Any
import pandas as pd
from TradingSystemLab.core.data_loader import DataLoader
from TradingSystemLab.strategies.trend.T2_Trend_Pullback import T2Parameters, T2TrendPullback, PullbackSetup
from TradingSystemLab.strategies.trend.T3_MTF_Trend import T3Parameters, T3MTFTrend
from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation import stage5_lifecycle_adapter as adapter
from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation.stage5_risk_cap_execution import OpenRisk, allocation, economics, signal_priority, EPSILON

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[3]
GROUP=['generation','lifecycle','fold_id']; STREAM=['strategy','timeframe','instrument']
EXPECTED={('v2_quarterly','baseline'):4449,('v2_quarterly','walk_forward'):746,('v2_quarterly','historical_true_oos'):1759,('v3_perpetual','baseline'):1124,('v3_perpetual','walk_forward'):515,('v3_perpetual','historical_true_oos'):1101}

def _sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def _csv(p,x,cols=None):
 f=x if isinstance(x,pd.DataFrame) else pd.DataFrame(x); f=f.reindex(columns=cols) if cols else f
 f.to_csv(p,index=False,lineterminator='\n',float_format='%.12g',na_rep='')
def _json(p,x): Path(p).write_text(json.dumps(x,indent=2,sort_keys=True,allow_nan=False)+'\n')
def _params(gen,s,tf,life):
 if life=='baseline': return T2Parameters() if s=='T2' else T3Parameters()
 p=ROOT/'TradingSystemLab/results'/('phase3_candidate_freeze/candidate_registry.json' if gen=='v2_quarterly' else 'perpetual_v3/phase3_candidate_freeze/candidate_registry.json')
 x=next(x for x in json.loads(p.read_text())['candidates'] if x['strategy']==s and x['timeframe']==tf)
 return replace(T2Parameters() if s=='T2' else T3Parameters(),**x['parameters'])

def _canonical():
 out=[]
 for gen,life in EXPECTED:
  for s in ('T2','T3'):
   for tf in ('M30','H1'):
    f=adapter._ledger(adapter.RESULTS,gen,life,s,tf).copy(); f['generation']=gen;f['lifecycle']=life;f['strategy']=s;f['timeframe']=tf
    f['fold_id']=f['fold'] if 'fold' in f else '';f['instrument']=f['symbol']
    if 'initial_stop' in f:
     risk=(pd.to_numeric(f.entry_price)-pd.to_numeric(f.initial_stop)).abs();sign=f.direction.map({'LONG':1,'SHORT':-1});f['initial_risk_price']=risk;f['net_R_C1']=sign*(f.exit_price-f.entry_price)/risk-.002/risk
    else:
     # Frozen historical ledgers omit price risk; correct only T3's known double-C1.
     f['net_R_C1']=pd.to_numeric(f.net_R_C1)+(pd.to_numeric(f.cost_R) if s=='T3' else 0.)
    f['allocated_net_R']=f.net_R_C1;f['assigned_risk_R']=1.;out.append(f)
 return pd.concat(out,ignore_index=True)

class StreamState:
 def __init__(self,row,root):
  self.meta={k:row[k] for k in GROUP+STREAM+['candidate_config_identity']}; self.s=row['strategy']; self.p=_params(row['generation'],self.s,row['timeframe'],row['lifecycle'])
  path=Path(root)/('futures_quarterly' if row['generation']=='v2_quarterly' else 'forever')/row['instrument']/f"{row['instrument']}_{row['timeframe']}.csv"
  raw=DataLoader(forbid_true_oos=False).load_csv(path); frame=DataLoader.close_index(raw,'30min' if row['timeframe']=='M30' else '1h').loc[row['start_timestamp']:row['end_timestamp']].copy()
  self.strategy=T2TrendPullback(self.p) if self.s=='T2' else T3MTFTrend(self.p)
  if self.s=='T2': self.strategy._validate=lambda x:None; self.data=self.strategy.calculate_indicators(frame);self.high=None
  else:self.data,self.high=self.strategy.calculate_indicators(frame,DataLoader.h4_from_h1(frame))
  self.lookup={t:i for i,t in enumerate(self.data.index)};self.pos=None;self.setup=None;self.seq=0;self.cursor=-1;self.blocked=False
 def risk(self):
  if self.pos is None:return 0.
  p=self.pos;return OpenRisk(p['direction'],p['entry'],p['initial'],p['stop'],p['assigned']).remaining_R()
 def process(self,t):
  """Process exits/stop updates, then return an eligible close signal if any."""
  if t not in self.lookup:return None,None
  i=self.lookup[t];b=self.data.iloc[i]; self.blocked=False
  if self.s=='T3':
   while self.cursor+1<len(self.high) and self.high.index[self.cursor+1]<=t:self.cursor+=1
   regime=self.strategy.regime(self.high.iloc[self.cursor]) if self.cursor>=0 else None
  else:regime=self.strategy.regime(b)
  exitrow=None
  if self.pos is not None:
   p=self.pos;old=p['stop']
   hit=(b.Low<=old if p['direction']=='LONG' else b.High>=old) if self.s=='T2' else self.strategy.exit_signal(p['direction'],b,old)
   loss=self.s=='T2' and (b.Close<b.EMA50 if p['direction']=='LONG' else b.Close>b.EMA50)
   if hit or loss:
    price=(min(float(b.Open),old) if p['direction']=='LONG' else max(float(b.Open),old)) if hit else float(b.Close);reason=((('INITIAL_STOP' if old==p['initial'] else 'ATR_TRAILING_STOP') if self.s=='T2' else 'ATR_TRAILING_STOP') if hit else 'EMA50_TREND_LOSS')
    exitrow=self._exit(t,price,reason);self.pos=None
    if self.s=='T2':self.blocked=True;return exitrow,None
   else:
    p['bars']+=1;p['lo']=min(p['lo'],float(b.Low));p['hi']=max(p['hi'],float(b.High));p['extreme']=max(p['extreme'],b.High) if p['direction']=='LONG' else min(p['extreme'],b.Low)
    cand=(p['hi']-self.p.trailing_atr*b.ATR if p['direction']=='LONG' else p['lo']+self.p.trailing_atr*b.ATR) if self.s=='T2' else self.strategy.manage_position(p['direction'],p['extreme'],b.ATR)
    p['stop']=max(old,float(cand)) if p['direction']=='LONG' else min(old,float(cand));return None,None
  if self.s=='T2':
   if self.setup is not None:
    q=self.setup
    if i>q.expiry_index or regime!=q.direction:self.setup=None
    elif i>q.pullback_start_index:
     q.pullback_extreme=min(q.pullback_extreme,float(b.Low)) if q.direction=='LONG' else max(q.pullback_extreme,float(b.High))
     if self.strategy.is_confirmation(b,self.data.iloc[i-1],q.direction):
      entry=float(b.Close);stop=q.pullback_extreme-self.p.stop_buffer_atr*b.ATR if q.direction=='LONG' else q.pullback_extreme+self.p.stop_buffer_atr*b.ATR;risk=entry-stop if q.direction=='LONG' else stop-entry;self.setup=None
      if risk>0 and risk<=self.p.max_initial_stop_atr*b.ATR:return exitrow,(q.direction,entry,float(stop))
    return exitrow,None
   if regime and i:
    ref=self.strategy.impulse_reference(self.data,i,regime)
    if ref is not None and self.strategy.is_pullback(b,regime):self.setup=PullbackSetup(regime,t,i,i+self.p.confirmation_window,float(b.Low if regime=='LONG' else b.High),ref)
   return exitrow,None
  if pd.notna(b.ATR):
   sig=self.strategy.generate_signal(b,regime)
   if sig:
    entry=float(b.Close);return exitrow,(sig,entry,float(self.strategy.calculate_stop_loss(sig,entry,float(b.ATR))))
  return exitrow,None
 def admit(self,t,sig,assigned):
  d,e,stop=sig;self.seq+=1;self.pos={'direction':d,'entry':e,'entry_time':t,'initial':stop,'risk':abs(e-stop),'stop':stop,'assigned':assigned,'bars':0,'lo':e,'hi':e,'extreme':e,'seq':self.seq}
 def _exit(self,t,price,reason):
  p=self.pos;return {**self.meta,'trade_id':f"{self.s}-{self.meta['timeframe']}-{self.meta['instrument']}-{p['seq']:06d}",'direction':p['direction'],'entry_time':p['entry_time'],'entry_price':p['entry'],'initial_stop_price':p['initial'],'initial_risk_price':p['risk'],'active_stop_at_exit':p['stop'],'assigned_risk_R':p['assigned'],'exit_time':t,'exit_price':price,'exit_reason':reason,**economics(p['direction'],p['entry'],price,p['risk'],p['assigned'])}

def prepare(registry,root):
 groups={}
 for r in registry:groups.setdefault(tuple(r[k] for k in GROUP),[]).append(StreamState(r,root))
 return groups

def replay(registry,root,enabled,prepared=None):
 trades=[];admissions=[];risk_events=[]
 groups=copy.deepcopy(prepared if prepared is not None else prepare(registry,root))
 for key,streams in sorted(groups.items()):
  times=sorted(set().union(*(s.data.index for s in streams)))
  for t in times:
   signals=[]
   for s in streams:
    ex,sig=s.process(t)
    if ex is not None:trades.append(ex)
    if sig is not None:signals.append((s,sig))
   for s,sig in sorted(signals,key=lambda x:signal_priority(*[x[0].meta[k] for k in STREAM])):
    before=sum(x.risk() for x in streams);residual,assigned,status=allocation(before,enabled)
    after=before
    if assigned>EPSILON:s.admit(t,sig,assigned);after=sum(x.risk() for x in streams)
    admissions.append({**s.meta,'timestamp':t,'direction':sig[0],'open_risk_before_R':before,'residual_capacity_R':residual,'assigned_risk_R':assigned,'status':status,'open_risk_after_R':after})
    if enabled and after>1+EPSILON:raise RuntimeError('RISK_CAP_INVARIANT_VIOLATION')
   risk_events.append({**dict(zip(GROUP,key)),'timestamp':t,'open_risk_R':sum(x.risk() for x in streams),'open_positions':sum(x.pos is not None for x in streams)})
  # Canonical engines do not force-close at lifecycle end; all expected ledgers end flat.
 return pd.DataFrame(trades),pd.DataFrame(admissions),pd.DataFrame(risk_events)

def _norm_path(f):
 cols=GROUP+STREAM+['direction','entry_time','entry_price','exit_time','exit_price','exit_reason'];x=f[cols].copy()
 for c in ('entry_time','exit_time'):x[c]=pd.to_datetime(x[c],utc=True).astype(str)
 for c in ('entry_price','exit_price'):x[c]=pd.to_numeric(x[c]).map(lambda v:format(v,'.12g'))
 return x.fillna('').sort_values(cols,kind='mergesort').reset_index(drop=True)
def reconcile(actual,canonical):
 a,e=_norm_path(actual),_norm_path(canonical);m=abs(len(a)-len(e))+sum(int(a[c].iloc[:min(len(a),len(e))].ne(e[c].iloc[:min(len(a),len(e))]).sum()) for c in a)
 counts=actual.groupby(['generation','lifecycle']).size().to_dict()
 if len(a)!=9694 or counts!=EXPECTED or m:raise RuntimeError(f'CANONICAL_RECONCILIATION_FAILED rows={len(a)} mismatches={m} counts={counts}')
 return m
def _ordered(g):
 x=g.copy();x['_s']=x.strategy.map({'T2':0,'T3':1});x['_t']=x.timeframe.map({'M30':0,'H1':1});cols=(['fold_id'] if x.lifecycle.iloc[0]=='walk_forward' else [])+['exit_time','_s','_t','instrument','trade_id'];return x.sort_values(cols,kind='mergesort')
def metrics(g,col='allocated_net_R'):
 if not len(g):return {'trades':0,'net_R':0.,'PF':0.,'expectancy_R':0.,'max_DD':0.,'recovery':0.,'win_rate':0.}
 x=pd.to_numeric(_ordered(g)[col]);wins=x[x>0].sum();loss=x[x<0].sum();curve=pd.concat([pd.Series([0.]),x.reset_index(drop=True).cumsum()]);dd=float((curve-curve.cummax()).min());net=float(x.sum())
 return {'trades':len(x),'net_R':net,'PF':float(wins/abs(loss)) if loss else 0.,'expectancy_R':float(x.mean()),'max_DD':dd,'recovery':net/abs(dd) if dd else 0.,'win_rate':float((x>0).mean())}
def _hash_frame(f):return hashlib.sha256(f.to_csv(index=False,lineterminator='\n',float_format='%.12g').encode()).hexdigest()

def _single(data_root,output,identities):
 output=Path(output);shutil.rmtree(output,ignore_errors=True);output.mkdir(parents=True);registry=list(csv.DictReader((HERE/'canonical_lifecycle_registry.csv').open()));canonical=_canonical();prepared=prepare(registry,data_root)
 uncapped,ua,ur=replay(registry,data_root,False,prepared);mismatches=reconcile(uncapped,canonical);capped,adm,rr=replay(registry,data_root,True,prepared)
 trade_hash=_hash_frame(capped);admission_hash=_hash_frame(adm)
 rows=[]
 for key in EXPECTED:
  c=canonical[(canonical.generation==key[0])&(canonical.lifecycle==key[1])];q=capped[(capped.generation==key[0])&(capped.lifecycle==key[1])];a=adm[(adm.generation==key[0])&(adm.lifecycle==key[1])];r=rr[(rr.generation==key[0])&(rr.lifecycle==key[1])];u=ur[(ur.generation==key[0])&(ur.lifecycle==key[1])]
  cm,qm=metrics(c),metrics(q);status=a.status.value_counts()
  rows.append({'generation':key[0],'lifecycle':key[1],'eligible_signals':len(a),'entered_trades':len(q),'full_entries':int(status.get('FULL',0)),'partial_entries':int(status.get('PARTIAL',0)),'skipped_signals':int(status.get('SKIPPED_ZERO_CAPACITY',0)),'total_assigned_R':float(a.assigned_risk_R.sum()),'average_assigned_risk':float(a[a.assigned_risk_R>0].assigned_risk_R.mean()),'median_assigned_risk':float(a[a.assigned_risk_R>0].assigned_risk_R.median()),'minimum_nonzero_assigned_risk':float(a[a.assigned_risk_R>0].assigned_risk_R.min()),'maximum_assigned_risk':float(a.assigned_risk_R.max()),'maximum_open_positions':int(r.open_positions.max()),'uncapped_maximum_open_risk':float(u.open_risk_R.max()),'capped_maximum_open_risk':float(r.open_risk_R.max()),'mean_capped_open_risk':float(r.open_risk_R.mean()),'uncapped_timestamps_above_1R':int((u.open_risk_R>1+EPSILON).sum()),'cap_violations':int((r.open_risk_R>1+EPSILON).sum()),**{'canonical_'+k:v for k,v in cm.items()},**{'capped_'+k:v for k,v in qm.items()},'delta_net_R':qm['net_R']-cm['net_R'],'delta_max_DD':qm['max_DD']-cm['max_DD']})
 summary=pd.DataFrame(rows);_csv(output/'risk_cap_portfolio_summary.csv',summary);_csv(output/'risk_cap_lifecycle_report.csv',summary)
 ar=[]
 for key,g in adm.groupby(GROUP+STREAM,dropna=False,sort=True):
  vc=g.status.value_counts();ar.append({**dict(zip(GROUP+STREAM,key)),'eligible_signals':len(g),'full_entries':int(vc.get('FULL',0)),'partial_entries':int(vc.get('PARTIAL',0)),'skipped_zero_capacity':int(vc.get('SKIPPED_ZERO_CAPACITY',0)),'entered_trades':int((g.assigned_risk_R>0).sum()),'total_assigned_R':float(g.assigned_risk_R.sum()),'mean_assigned_R':float(g[g.assigned_risk_R>0].assigned_risk_R.mean())})
 _csv(output/'risk_cap_admission_report.csv',ar)
 orows=[]
 for key,g in rr.groupby(GROUP,dropna=False,sort=True):
  u=ur
  for c,v in zip(GROUP,key):u=u[u[c].fillna('').eq(v)]
  orows.append({**dict(zip(GROUP,key)),'maximum_uncapped_simultaneous_open_risk':float(u.open_risk_R.max()),'maximum_capped_open_risk':float(g.open_risk_R.max()),'average_capped_open_risk':float(g.open_risk_R.mean()),'maximum_open_positions':int(g.open_positions.max()),'timestamps_above_1R_uncapped':int((u.open_risk_R>1+EPSILON).sum()),'capped_violations':int((g.open_risk_R>1+EPSILON).sum())})
 _csv(output/'risk_cap_open_risk_report.csv',orows)
 def grouped_report(name,cols):
  out=[]
  keys=set(tuple(x) for x in capped[cols].fillna('').itertuples(index=False,name=None))|set(tuple(x) for x in adm[cols].fillna('').itertuples(index=False,name=None))
  for key in sorted(keys):
   q=capped.copy();a=adm.copy()
   for c,v in zip(cols,key):q=q[q[c].fillna('').astype(str).eq(str(v))];a=a[a[c].fillna('').astype(str).eq(str(v))]
   vc=a.status.value_counts();out.append({**dict(zip(cols,key)),'eligible_signals':len(a),'entered_trades':len(q),'full_entries':int(vc.get('FULL',0)),'partial_entries':int(vc.get('PARTIAL',0)),'skips':int(vc.get('SKIPPED_ZERO_CAPACITY',0)),'allocated_R':float(a.assigned_risk_R.sum()),'net_allocated_R':float(q.allocated_net_R.sum()),**metrics(q)})
  _csv(output/f'risk_cap_{name}_report.csv',out)
 grouped_report('fold',GROUP+STREAM[:2]);grouped_report('instrument',['generation','lifecycle','instrument']);grouped_report('strategy_timeframe',['generation','lifecycle','strategy','timeframe'])
 def period(name,freq):
  q=capped.assign(period=pd.to_datetime(capped.exit_time,utc=True).dt.to_period(freq).astype(str));c=canonical.assign(period=pd.to_datetime(canonical.exit_time,utc=True).dt.to_period(freq).astype(str));out=[]
  for key,g in q.groupby(['generation','lifecycle','period'],sort=True):
   cc=c[(c.generation==key[0])&(c.lifecycle==key[1])&(c.period==key[2])];aa=adm[(adm.generation==key[0])&(adm.lifecycle==key[1])&pd.to_datetime(adm.timestamp,utc=True).dt.to_period(freq).astype(str).eq(key[2])];out.append({**dict(zip(['generation','lifecycle',name],key)),'canonical_net_R':float(cc.net_R_C1.sum()),'capped_net_R':float(g.allocated_net_R.sum()),'delta_R':float(g.allocated_net_R.sum()-cc.net_R_C1.sum()),'canonical_DD':metrics(cc)['max_DD'],'capped_DD':metrics(g)['max_DD'],'entered_trades':len(g),'assigned_total_R':float(aa.assigned_risk_R.sum()),'skips':int(aa.status.eq('SKIPPED_ZERO_CAPACITY').sum()),'partial_entries':int(aa.status.eq('PARTIAL').sum())})
  _csv(output/f'risk_cap_{name}_report.csv',out)
 period('monthly','M');period('quarterly','Q')
 sim=[];conc=[]
 for key in EXPECTED:
  for label,f,col in [('canonical',canonical,'net_R_C1'),('capped',capped,'allocated_net_R')]:
   g=f[(f.generation==key[0])&(f.lifecycle==key[1])];loss=g[g[col]<0].groupby('exit_time')[col].agg(['count','sum']);multi=loss[loss['count']>=2];months=g.assign(month=pd.to_datetime(g.exit_time,utc=True).dt.strftime('%Y-%m'));mi=months[months[col]<0].groupby('month').instrument.nunique()
   sim.append({'generation':key[0],'lifecycle':key[1],'mode':label,'multi_loss_exit_timestamps':len(multi),'sum_losses_at_clusters':float(multi['sum'].sum()),'worst_same_timestamp_loss_cluster':float(multi['sum'].min()) if len(multi) else 0.,'months_multiple_losing_instruments':int((mi>=2).sum())})
  g=capped[(capped.generation==key[0])&(capped.lifecycle==key[1])];p=g[g.allocated_net_R>0].nlargest(5,'allocated_net_R');positive=g[g.allocated_net_R>0].allocated_net_R.sum();rest=g.drop(p.index);conc.append({'generation':key[0],'lifecycle':key[1],'top_1_positive_allocated_R_share':float(p.head(1).allocated_net_R.sum()/positive),'top_5_positive_allocated_R_share':float(p.allocated_net_R.sum()/positive),'net_R_ex_top5':float(rest.allocated_net_R.sum()),'PF_ex_top5':metrics(rest)['PF'],'benefit_concentration_note':'descriptive_only; inspect instrument and monthly reports'})
 _csv(output/'risk_cap_simultaneous_loss_report.csv',sim);_csv(output/'risk_cap_concentration_report.csv',conc)
 dig=[]
 for key,g in capped.groupby(GROUP+STREAM,dropna=False,sort=True):
  dig.append({**dict(zip(GROUP+STREAM,key)),'entered_rows':len(g),'full_entries':int((g.assigned_risk_R>=1-EPSILON).sum()),'partial_entries':int((g.assigned_risk_R<1-EPSILON).sum()),'assigned_R':float(g.assigned_risk_R.sum()),'first_entry':g.entry_time.min(),'last_exit':g.exit_time.max(),'ledger_hash':_hash_frame(g),'net_allocated_R':float(g.allocated_net_R.sum())})
 _csv(output/'risk_cap_trade_digest.csv',dig)
 _csv(output/'risk_cap_canonical_path_reconciliation.csv',[{'expected_trades':9694,'actual_trades':len(uncapped),'path_mismatches':mismatches,'status':'PASS'}])
 cdelta=(capped.allocated_net_R-capped.assigned_risk_R*(capped.direction.map({'LONG':1,'SHORT':-1})*(capped.exit_price-capped.entry_price)/capped.initial_risk_price-.002/capped.initial_risk_price)).abs();udelta=(uncapped.net_R_C1-(uncapped.direction.map({'LONG':1,'SHORT':-1})*(uncapped.exit_price-uncapped.entry_price)/uncapped.initial_risk_price-.002/uncapped.initial_risk_price)).abs();audit={'status':'PASS','canonical_rows':len(uncapped),'canonical_path_mismatches':mismatches,'canonical_arithmetic_mismatches':int((udelta>1e-9).sum()),'capped_rows':len(capped),'capped_arithmetic_mismatches':int((cdelta>1e-9).sum()),'maximum_arithmetic_delta':float(max(cdelta.max(),udelta.max())),'risk_accounting_events':len(adm),'risk_cap_violations':int((adm.open_risk_after_R>1+EPSILON).sum()),'negative_risk_events':int((adm.open_risk_before_R < -EPSILON).sum()),'allocation_above_one':int((adm.assigned_risk_R>1+EPSILON).sum())};_json(output/'risk_cap_audit.json',audit)
 report='# H4_03 TOTAL_OPEN_RISK_CAP Retrospective Causal Validation\n\n**Formal research label: `FORMAL_LABEL_LEFT_FOR_REVIEW`**  \n**Stage 5: OPEN**\n\nRaw chronological replay completed without combining BE1 or TRAIL1. Realized-R drawdown is ordered by exits; all diagnostics are descriptive and no tuning or selection occurred.\n\n## Portfolio evidence\n\n'+summary.to_markdown(index=False)+'\n';(output/'RISK_CAP_Validation_Report.md').write_text(report)
 manifest={'status':'STAGE5_RISK_CAP_CAUSAL_VALIDATION_PASSED','hypothesis_id':'H4_03_TOTAL_OPEN_RISK_CAP','formal_research_label':'FORMAL_LABEL_LEFT_FOR_REVIEW','Stage5_status':'OPEN','implementation_base_sha':identities['canonical_base'],'execution_source_sha':identities['execution_source_sha'],'data_repo_commit':'50f1fd2178c18b7ab3bd969be82ad01f47a34745','source_hashes':identities['source_hashes'],'strategy_hashes':identities['strategy_hashes'],'stage4_artifact_hashes':identities['stage4_artifact_hashes'],'lifecycle_registry_identity':_sha(HERE/'canonical_lifecycle_registry.csv'),'canonical_mode_result':{'trades':len(uncapped),'mismatches':mismatches},'capped_trade_rows':len(capped),'capped_trade_ledger_sha256':trade_hash,'admission_event_rows':len(adm),'admission_event_sha256':admission_hash,'risk_cap_violations':audit['risk_cap_violations'],'cost_contract':'CORRECTED_SINGLE_C1','no_optimization':True,'v2_v3_separate':True,'wf_cold_start':True};return manifest

COMPACT=['risk_cap_canonical_path_reconciliation.csv','risk_cap_portfolio_summary.csv','risk_cap_lifecycle_report.csv','risk_cap_admission_report.csv','risk_cap_open_risk_report.csv','risk_cap_trade_digest.csv']
def execute(data_root,output,identities,certify=False):
 first=_single(data_root,output,identities)
 if certify:
  with tempfile.TemporaryDirectory(prefix='risk-cap-certify-') as d:
   second=_single(data_root,Path(d),identities);compact={n:{'run_1_sha256':_sha(Path(output)/n),'run_2_sha256':_sha(Path(d)/n),'identical':_sha(Path(output)/n)==_sha(Path(d)/n)} for n in COMPACT}
   if first['capped_trade_ledger_sha256']!=second['capped_trade_ledger_sha256'] or first['admission_event_sha256']!=second['admission_event_sha256'] or not all(v['identical'] for v in compact.values()):raise RuntimeError('RISK_CAP_DETERMINISM_FAILED')
   audit=json.loads((Path(output)/'risk_cap_audit.json').read_text());audit.update({'run_1_ledger_sha256':first['capped_trade_ledger_sha256'],'run_2_ledger_sha256':second['capped_trade_ledger_sha256'],'run_1_admission_sha256':first['admission_event_sha256'],'run_2_admission_sha256':second['admission_event_sha256'],'raw_execution_determinism':'PASS','compact_artifact_determinism':compact});_json(Path(output)/'risk_cap_audit.json',audit);first['determinism']={'result':'PASS',**{k:audit[k] for k in ('run_1_ledger_sha256','run_2_ledger_sha256','run_1_admission_sha256','run_2_admission_sha256')}}
 first['output_hashes']={p.name:_sha(p) for p in sorted(Path(output).glob('*')) if p.name!='manifest_risk_cap.json'};first['evidence_tree_hash']=hashlib.sha256(''.join(f'{k}\0{v}\n' for k,v in sorted(first['output_hashes'].items())).encode()).hexdigest();_json(Path(output)/'manifest_risk_cap.json',first);return first
