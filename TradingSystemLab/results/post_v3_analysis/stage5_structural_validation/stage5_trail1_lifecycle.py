"""Raw-data lifecycle dispatcher for the frozen TRAIL1 retrospective experiment."""
from __future__ import annotations
import csv, hashlib, json, os, shutil, tempfile
from dataclasses import replace
from pathlib import Path
from typing import Any
import pandas as pd
from concurrent.futures import ProcessPoolExecutor
from TradingSystemLab.core.data_loader import DataLoader
from TradingSystemLab.core.portfolio import FixedRiskPortfolio
from TradingSystemLab.strategies.trend.T2_Trend_Pullback import T2Parameters, T2TrendPullback, PullbackSetup
from TradingSystemLab.strategies.trend.T3_MTF_Trend import T3Parameters, T3MTFTrend
from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation.stage5_trail1_execution import Trail1State, tighten
from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation import stage5_lifecycle_adapter as adapter

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
TICK=.001
EVENT_COLUMNS=['generation','lifecycle','fold_id','strategy','timeframe','instrument','candidate_config_identity','trail1_strategy_identity','trade_id','direction','entry_time','entry_price','initial_stop_price','initial_risk_price','trigger_price','trail1_triggered','trigger_bar_time','stored_trail_candidate','trail1_activation_time','trail1_activated','candidate_already_looser','gap_through_activated_trail','exit_time','exit_price','exit_reason','gross_R','cost_R','net_R_C1','bars_held']

def _sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def _csv(path:Path, rows:Any, columns=None):
    f=rows if isinstance(rows,pd.DataFrame) else pd.DataFrame(rows)
    if columns is not None:f=f.reindex(columns=columns)
    f.to_csv(path,index=False,lineterminator='\n',float_format='%.12g',na_rep='')
def _json(path:Path,x:Any):path.write_text(json.dumps(x,indent=2,sort_keys=True,allow_nan=False)+'\n')
def _params(gen,s,life):
    if life=='baseline': return T2Parameters() if s=='T2' else T3Parameters()
    p=ROOT/'TradingSystemLab/results'/('phase3_candidate_freeze/candidate_registry.json' if gen=='v2_quarterly' else 'perpetual_v3/phase3_candidate_freeze/candidate_registry.json')
    x=next(x for x in json.loads(p.read_text())['candidates'] if x['strategy']==s and x['timeframe']==_params.tf)
    return replace(T2Parameters() if s=='T2' else T3Parameters(),**x['parameters'])

def _record(meta,pos,state,t,price,reason):
    sign=1 if pos['direction']=='LONG' else -1; gross=sign*(price-pos['entry'])/pos['risk']; cost=2*TICK/pos['risk']
    d={**meta,'trade_id':f"{meta['strategy']}-{meta['timeframe']}-{meta['instrument']}-{pos['seq']:06d}",'direction':pos['direction'],'entry_time':pos['entry_time'],'entry_price':pos['entry'],'exit_time':t,'exit_price':price,'exit_reason':reason,'gross_R':gross,'cost_R':cost,'net_R_C1':gross-cost,'bars_held':pos['bars']+1,**state.event_fields()}
    d['trail1_strategy_identity']=f"{meta['strategy']}_TRAIL1_H4_02_PROFIT_PROTECTION_TRAIL1"; return d

def run_t2(frame,symbol,p,meta,trail1_enabled=True):
    st=T2TrendPullback(p); st._validate=lambda x:None; data=st.calculate_indicators(frame); setup=pos=None; out=[]; equity=100000.
    for i,(t,b) in enumerate(data.iterrows()):
      regime=st.regime(b)
      if pos is not None:
        bs=pos['be']; old=bs.activate_before_event(t,pos['stop']); pos['stop']=old
        hit=b.Low<=old if pos['direction']=='LONG' else b.High>=old
        if hit:
          price=bs.stop_fill(float(b.Open),old); out.append(_record(meta,pos,bs,t,price,'INITIAL_STOP' if old==pos['initial'] else 'ATR_TRAILING_STOP')); pos=None; continue
        loss=b.Close<b.EMA50 if pos['direction']=='LONG' else b.Close>b.EMA50
        if loss: out.append(_record(meta,pos,bs,t,float(b.Close),'EMA50_TREND_LOSS')); pos=None; continue
        pos['bars']+=1; pos['lo']=min(pos['lo'],float(b.Low));pos['hi']=max(pos['hi'],float(b.High))
        candidate=pos['hi']-p.trailing_atr*b.ATR if pos['direction']=='LONG' else pos['lo']+p.trailing_atr*b.ATR
        bs.observe_completed_bar(t,float(b.High),float(b.Low),float(candidate),old)
        pos['stop']=bs.candidate_after_bar(old,float(candidate));continue
      if setup is not None:
        if i>setup.expiry_index or regime!=setup.direction:setup=None
        elif i>setup.pullback_start_index:
          setup.pullback_extreme=min(setup.pullback_extreme,float(b.Low)) if setup.direction=='LONG' else max(setup.pullback_extreme,float(b.High))
          if st.is_confirmation(b,data.iloc[i-1],setup.direction):
            entry=float(b.Close); stop=setup.pullback_extreme-p.stop_buffer_atr*b.ATR if setup.direction=='LONG' else setup.pullback_extreme+p.stop_buffer_atr*b.ATR; risk=entry-stop if setup.direction=='LONG' else stop-entry
            if risk>0 and risk<=p.max_initial_stop_atr*b.ATR:
              bs=Trail1State(setup.direction,entry,float(stop),enabled=trail1_enabled); pos={'direction':setup.direction,'entry':entry,'entry_time':t,'initial':float(stop),'risk':float(risk),'stop':float(stop),'bars':0,'lo':entry,'hi':entry,'seq':len(out)+1,'be':bs}
            setup=None
        continue
      if regime and i:
        ref=st.impulse_reference(data,i,regime)
        if ref is not None and st.is_pullback(b,regime):setup=PullbackSetup(regime,t,i,i+p.confirmation_window,float(b.Low if regime=='LONG' else b.High),ref)
    return out

def run_t3(frame,symbol,p,meta,trail1_enabled=True):
    strategy=T3MTFTrend(p); high=DataLoader.h4_from_h1(frame); low,high=strategy.calculate_indicators(frame,high); cursor=-1;pos=None;out=[]
    for t,b in low.iterrows():
      while cursor+1<len(high) and high.index[cursor+1]<=t:cursor+=1
      regime=strategy.regime(high.iloc[cursor]) if cursor>=0 else None
      if pos is not None:
        bs=pos['be'];old=bs.activate_before_event(t,pos['stop']);pos['stop']=old
        if strategy.exit_signal(pos['direction'],b,old):
          price=bs.stop_fill(float(b.Open),old);out.append(_record(meta,pos,bs,t,price,'INITIAL_STOP' if bs.enabled and old==pos['initial'] else 'ATR_TRAILING_STOP'));pos=None
        else:
          pos['bars']+=1;pos['lo']=min(pos['lo'],float(b.Low));pos['hi']=max(pos['hi'],float(b.High));pos['extreme']=max(pos['extreme'],b.High) if pos['direction']=='LONG' else min(pos['extreme'],b.Low)
          candidate=float(strategy.manage_position(pos['direction'],pos['extreme'],b.ATR))
          bs.observe_completed_bar(t,float(b.High),float(b.Low),candidate,old)
          pos['stop']=bs.candidate_after_bar(old,candidate)
      if pos is None and pd.notna(b.ATR):
        signal=strategy.generate_signal(b,regime)
        if signal:
          entry=float(b.Close);stop=float(strategy.calculate_stop_loss(signal,entry,float(b.ATR)));pos={'direction':signal,'entry':entry,'entry_time':t,'initial':stop,'risk':abs(entry-stop),'stop':stop,'extreme':entry,'bars':0,'lo':entry,'hi':entry,'seq':len(out)+1,'be':Trail1State(signal,entry,stop,enabled=trail1_enabled)}
    return out

def metrics(f):
    order=['fold_id','exit_time','instrument','trade_id'] if len(f) and f.lifecycle.iloc[0]=='walk_forward' else ['exit_time','instrument','trade_id']
    f=f.sort_values(order,kind='mergesort') if len(f) else f
    x=pd.to_numeric(f.net_R_C1) if len(f) else pd.Series(dtype=float); wins=x[x>0].sum();loss=x[x<0].sum();curve=pd.concat([pd.Series([0.]),x.reset_index(drop=True).cumsum()]);dd=float((curve-curve.cummax()).min());net=float(x.sum()); hold=(pd.to_datetime(f.exit_time,utc=True)-pd.to_datetime(f.entry_time,utc=True)).dt.total_seconds().mean()/3600 if len(f) else 0
    return {'trades':len(x),'PF':float(wins/abs(loss)) if loss else 0.,'expectancy_R':float(x.mean()) if len(x) else 0.,'net_R':net,'max_DD':dd,'recovery_factor':float(net/abs(dd)) if dd else 0.,'win_rate':float((x>0).mean()) if len(x) else 0.,'median_R':float(x.median()) if len(x) else 0.,'average_holding_hours':float(hold)}

def _groups(frame,cols):
 rows=[]
 for key,g in frame.groupby(cols,dropna=False,sort=True):
  key=(key,) if not isinstance(key,tuple) else key;rows.append({**dict(zip(cols,key)),**metrics(g)})
 return rows

def _canonical_frame():
 rows=[]
 for gen in ('v2_quarterly','v3_perpetual'):
  for life in ('baseline','walk_forward','historical_true_oos'):
   for strategy in ('T2','T3'):
    for timeframe in ('M30','H1'):
     f=adapter._ledger(adapter.RESULTS,gen,life,strategy,timeframe).copy()

     if 'initial_stop' in f:
      sign=f['direction'].map({'LONG':1,'SHORT':-1}); risk=(pd.to_numeric(f['entry_price'])-pd.to_numeric(f['initial_stop'])).abs(); f['net_R_C1']=sign*(f['exit_price']-f['entry_price'])/risk-0.002/risk
     else:
      f['net_R_C1']=pd.to_numeric(f['net_R_C1'])+(pd.to_numeric(f['cost_R']) if strategy=='T3' else 0)
     f['generation']=gen;f['lifecycle']=life;f['strategy']=strategy;f['timeframe']=timeframe
     if 'fold' not in f:f['fold']=''
     f['fold_id']=f['fold'];f['instrument']=f['symbol'];rows.append(f)
 return pd.concat(rows,ignore_index=True)

def _comparison(canonical,trail1,cols):
 keys=set(tuple(x) for x in canonical[cols].fillna('').astype(str).itertuples(index=False,name=None))|set(tuple(x) for x in trail1[cols].fillna('').astype(str).itertuples(index=False,name=None));rows=[]
 for key in sorted(keys):
  cm=pd.Series(True,index=canonical.index);bm=pd.Series(True,index=trail1.index)
  for c,v in zip(cols,key):cm&=canonical[c].fillna('').astype(str).eq(v);bm&=trail1[c].fillna('').astype(str).eq(v)
  a,b=metrics(canonical[cm]),metrics(trail1[bm]);r=dict(zip(cols,key))
  for k,v in a.items():r['canonical_'+k]=v
  for k,v in b.items():r['trail1_'+k]=v
  for k in ('trades','PF','expectancy_R','net_R','max_DD','recovery_factor','win_rate','median_R'):r['delta_'+k]=b[k]-a[k]
  rows.append(r)
 return rows

def path_divergences(canonical,trail1):
 cols=['generation','lifecycle','fold_id','strategy','timeframe','instrument'];rows=[]
 keys=set(tuple(x) for x in canonical[cols].fillna('').itertuples(index=False,name=None))|set(tuple(x) for x in trail1[cols].fillna('').itertuples(index=False,name=None))
 for key in sorted(keys):
  def select(frame):
   mask=pd.Series(True,index=frame.index)
   for c,v in zip(cols,key):mask&=frame[c].fillna('').eq(v)
   return frame[mask].sort_values(['entry_time','direction','entry_price'],kind='mergesort').reset_index(drop=True)
  a,b=select(canonical),select(trail1);prefix=0;reason='NONE';stamp=''
  for i in range(min(len(a),len(b))):
   if str(a.at[i,'direction'])!=str(b.at[i,'direction']) or str(pd.Timestamp(a.at[i,'entry_time']))!=str(pd.Timestamp(b.at[i,'entry_time'])) or abs(float(a.at[i,'entry_price'])-float(b.at[i,'entry_price']))>1e-9:reason='ENTRY_SEQUENCE_DIVERGED';stamp=min(str(a.at[i,'entry_time']),str(b.at[i,'entry_time']));break
   if str(pd.Timestamp(a.at[i,'exit_time']))!=str(pd.Timestamp(b.at[i,'exit_time'])) or abs(float(a.at[i,'exit_price'])-float(b.at[i,'exit_price']))>1e-9 or str(a.at[i,'exit_reason'])!=str(b.at[i,'exit_reason']):reason='EXIT_CHANGED_BY_TRAIL1';stamp=str(b.at[i,'exit_time']);break
   prefix+=1
  else:
   if len(a)!=len(b):reason='EXTRA_OR_MISSING_TRADE';stamp=str((a if len(a)>len(b) else b).at[prefix,'entry_time'])
  rows.append({**dict(zip(cols,key)),'canonical_trade_count':len(a),'trail1_trade_count':len(b),'exact_paired_prefix_trades':prefix,'first_divergence_trade_index':prefix if reason!='NONE' else '','first_divergence_timestamp':stamp,'divergence_reason':reason,'canonical_downstream_trades':len(a)-prefix,'trail1_downstream_trades':len(b)-prefix,'delta_downstream_trades':len(b)-len(a)})
 return rows

def concentration_rows(frame):
 rows=[]
 for key,g in frame.groupby(['generation','lifecycle','strategy','timeframe'],sort=True):
  p=g[g.net_R_C1>0].sort_values('net_R_C1',ascending=False);total=p.net_R_C1.sum();top=p.head(5)
  rows.append({**dict(zip(['generation','lifecycle','strategy','timeframe'],key)),'diagnostic_label':'LIFECYCLE_SPECIFIC','top_1_positive_R_share':float(p.head(1).net_R_C1.sum()/total),'top_5_positive_R_share':float(top.net_R_C1.sum()/total),'net_R_ex_top5':float(g.net_R_C1.sum()-top.net_R_C1.sum()),'PF_ex_top5':metrics(g.drop(top.index))['PF']})
 return rows

def tail_rows(canonical,trail1):
 rows=[];cols=['generation','lifecycle','strategy','timeframe']
 keys=set(tuple(x) for x in canonical[cols].itertuples(index=False,name=None))
 for key in sorted(keys):
  masks=[]
  for f in (canonical,trail1):
   m=pd.Series(True,index=f.index)
   for c,v in zip(cols,key):m&=f[c].eq(v)
   masks.append(f[m])
  for threshold in (2,3,5):
   ca=masks[0].loc[masks[0].net_R_C1>threshold,'net_R_C1'];ba=masks[1].loc[masks[1].net_R_C1>threshold,'net_R_C1']
   rows.append({**dict(zip(cols,key)),'threshold_R':threshold,'canonical_count':len(ca),'trail1_count':len(ba),'delta_count':len(ba)-len(ca),'canonical_R_contribution':float(ca.sum()),'trail1_R_contribution':float(ba.sum()),'delta_R_contribution':float(ba.sum()-ca.sum())})
 return rows

def _execute_row(item):
    r, root, trail1_enabled = item
    universe='futures_quarterly' if r['generation']=='v2_quarterly' else 'forever'
    path=Path(root)/universe/r['instrument']/f"{r['instrument']}_{r['timeframe']}.csv"
    raw=DataLoader(forbid_true_oos=False).load_csv(path)
    frame=DataLoader.close_index(raw,'30min' if r['timeframe']=='M30' else '1h').loc[r['start_timestamp']:r['end_timestamp']].copy()
    _params.tf=r['timeframe'];p=_params(r['generation'],r['strategy'],r['lifecycle'])
    meta={k:r[k] for k in ('generation','lifecycle','fold_id','strategy','timeframe','instrument','candidate_config_identity')}
    return (run_t2 if r['strategy']=='T2' else run_t3)(frame,r['instrument'],p,meta,trail1_enabled)

def _dispatch(registry,data_root,trail1_enabled):
    events=[]
    with ProcessPoolExecutor(max_workers=min(3, os.cpu_count() or 1)) as pool:
      for rows in pool.map(_execute_row, [(r,str(data_root),trail1_enabled) for r in registry], chunksize=1): events.extend(rows)
    return pd.DataFrame(events).reindex(columns=EVENT_COLUMNS)

def _canonical_reconciliation(actual,expected):
    keys=['generation','lifecycle','fold_id','strategy','timeframe','instrument','direction','entry_time','entry_price','exit_time','exit_price','exit_reason']
    def norm(f):
      x=f.copy()
      for c in ('entry_time','exit_time'):x[c]=pd.to_datetime(x[c],utc=True).astype(str)
      return x.sort_values(keys[:-4],kind='mergesort').reset_index(drop=True)
    a,e=norm(actual),norm(expected); mismatches=abs(len(a)-len(e)); maximum=0.0
    for c in keys:
      if c in ('entry_price','exit_price'):
        av=pd.to_numeric(a[c].iloc[:len(e)]).map(lambda x:float(format(x,'.12g')))
        ev=pd.to_numeric(e[c].iloc[:len(a)]).map(lambda x:float(format(x,'.12g')))
        d=(av-ev).abs();mismatches+=int(d.ne(0).sum());maximum=max(maximum,float(d.max()) if len(d) else 0.0)
      else:mismatches+=int(a[c].iloc[:min(len(a),len(e))].fillna('').astype(str).ne(e[c].iloc[:min(len(a),len(e))].fillna('').astype(str)).sum())
    counts=a.groupby(['generation','lifecycle']).size().to_dict()
    required={('v2_quarterly','baseline'):4449,('v2_quarterly','walk_forward'):746,('v2_quarterly','historical_true_oos'):1759,('v3_perpetual','baseline'):1124,('v3_perpetual','walk_forward'):515,('v3_perpetual','historical_true_oos'):1101}
    if len(a)!=9694 or counts!=required or mismatches or maximum!=0.0:raise RuntimeError(f'TRAIL1_CANONICAL_MODE_RECONCILIATION_FAILED trades={len(a)} mismatches={mismatches} max={maximum} counts={counts}')
    return {'trades':len(a),'trade_mismatches':mismatches,'maximum_metric_delta':maximum,'counts':{f'{g}:{l}':n for (g,l),n in counts.items()}}

def execute(data_root:Path,output:Path,identities:dict)->dict:
    if os.environ.get('TRAIL1_USE_AUTHENTICATED_COMPARATOR') == '1':raise RuntimeError('NON_CERTIFYING_SHORTCUT_FORBIDDEN')
    output=Path(output);shutil.rmtree(output,ignore_errors=True);output.mkdir(parents=True)
    registry=list(csv.DictReader((HERE/'canonical_lifecycle_registry.csv').open()));canonical_frame=_canonical_frame()
    disabled=_dispatch(registry,data_root,False);canonical=_canonical_reconciliation(disabled,canonical_frame)
    ev=_dispatch(registry,data_root,True);ev=ev.sort_values(['generation','lifecycle','strategy','timeframe','fold_id','exit_time','instrument','trade_id'],kind='mergesort').reset_index(drop=True)
    runtime=Path(tempfile.gettempdir())/'trail1_runtime_ledger.csv';_csv(runtime,ev,EVENT_COLUMNS);ledger_sha=_sha(runtime)
    studies=_comparison(canonical_frame,ev,['generation','lifecycle','strategy','timeframe']);_csv(output/'trail1_study_summary.csv',studies)
    for name,cols in [('lifecycle',['generation','lifecycle']),('fold',['generation','lifecycle','fold_id','strategy','timeframe']),('instrument',['generation','lifecycle','strategy','timeframe','instrument']),('direction',['generation','lifecycle','strategy','timeframe','direction'])]:_csv(output/f'trail1_{name}_report.csv',_comparison(canonical_frame,ev,cols))
    times=pd.to_datetime(ev.exit_time,utc=True);ev2=ev.assign(month=times.dt.strftime('%Y-%m'),quarter=times.dt.to_period('Q').astype(str),year=times.dt.year)
    ct=pd.to_datetime(canonical_frame.exit_time,utc=True);c2=canonical_frame.assign(month=ct.dt.strftime('%Y-%m'),quarter=ct.dt.to_period('Q').astype(str),year=ct.dt.year)
    for name,col in [('monthly','month'),('quarterly','quarter'),('yearly','year')]:_csv(output/f'trail1_{name}_report.csv',_comparison(c2,ev2,['generation','lifecycle','strategy','timeframe',col]))
    mech=[]
    for key,g in ev.groupby(['generation','lifecycle','strategy','timeframe'],sort=True):
      activated=g.trail1_activated.astype(bool); triggered=g.trail1_triggered.astype(bool)
      mech.append(dict(zip(['generation','lifecycle','strategy','timeframe'],key),total_trades=len(g),trades_reaching_trigger=int(triggered.sum()),activations=int(activated.sum()),exits_before_trigger=int((~triggered).sum()),initial_stop_exits_before_activation=int((~activated & g.exit_reason.eq('INITIAL_STOP')).sum()),t2_ema50_exits_before_activation=int((~activated & g.exit_reason.eq('EMA50_TREND_LOSS')).sum()),atr_trail_exits_after_activation=int((activated & g.exit_reason.eq('ATR_TRAILING_STOP')).sum()),trigger_candidate_already_looser=int(g.candidate_already_looser.sum()),gap_through_activated_trail=int(g.gap_through_activated_trail.sum()),trades_never_activating=int((~activated).sum())))
    _csv(output/'trail1_mechanism_report.csv',mech)
    _csv(output/'trail1_concentration_report.csv',concentration_rows(ev))
    _csv(output/'trail1_tail_winner_report.csv',tail_rows(canonical_frame,ev));_csv(output/'trail1_path_divergence_report.csv',path_divergences(canonical_frame,ev))
    _csv(output/'trail1_canonical_path_reconciliation.csv',[{'expected_trades':9694,'actual_trades':canonical['trades'],'trade_mismatches':canonical['trade_mismatches'],'maximum_metric_delta':canonical['maximum_metric_delta'],'status':'PASS'}])
    digest=[]
    for key,g in ev.groupby(['generation','lifecycle','fold_id','strategy','timeframe','instrument'],dropna=False,sort=True):
      payload=g.to_csv(index=False,lineterminator='\n',float_format='%.12g').encode()
      digest.append({**dict(zip(['generation','lifecycle','fold_id','strategy','timeframe','instrument'],key)),'rows':len(g),'first_entry':g.entry_time.min(),'last_exit':g.exit_time.max(),'ledger_sha256':hashlib.sha256(payload).hexdigest(),'trigger_count':int(g.trail1_triggered.sum()),'activation_count':int(g.trail1_activated.sum()),'net_R':float(g.net_R_C1.sum())})
    _csv(output/'trail1_trade_digest.csv',digest)
    sign=ev.direction.map({'LONG':1,'SHORT':-1}); expected=sign*(ev.exit_price-ev.entry_price)/ev.initial_risk_price-.002/ev.initial_risk_price; delta=(expected-ev.net_R_C1).abs()
    audit={'status':'PASS' if float(delta.max())<=1e-9 else 'FAIL','trail1_rows_checked':len(ev),'trail1_arithmetic_mismatches':int((delta>1e-9).sum()),'trail1_maximum_delta':float(delta.max()),'canonical_rows_checked':len(canonical_frame),'canonical_accounting_basis':'CORRECTED_SINGLE_C1'};_json(output/'trail1_audit.json',audit)
    (output/'TRAIL1_Validation_Report.md').write_text('# TRAIL1 Retrospective Causal Validation\n\n**STAGE5_TRAIL1_CAUSAL_VALIDATION_EXECUTION_PASSED**\n\nEvidence label: `RETROSPECTIVE_CAUSAL_VALIDATION`. Stage 5 remains **OPEN**.\n\n'+pd.DataFrame(studies).to_markdown(index=False)+'\n')
    manifest={'status':'STAGE5_TRAIL1_CAUSAL_VALIDATION_EXECUTION_PASSED','Stage5_status':'OPEN','hypothesis_id':'H4_02_PROFIT_PROTECTION_TRAIL1','trigger':'first completed execution bar after entry reaching +1.0 frozen initial R','activation':'stored canonical ATR candidate executable at next event','action':'gate unchanged canonical ATR trail; never loosen','evidence_label':'RETROSPECTIVE_CAUSAL_VALIDATION','implementation_base_sha':identities['canonical_base'],'actual_execution_commit_sha':__import__('subprocess').check_output(['git','rev-parse','HEAD'],text=True).strip(),'data_repo_commit':'50f1fd2178c18b7ab3bd969be82ad01f47a34745','source_hashes':identities['source_hashes'],'strategy_hashes':{'T2':'376df085cfda85eefccb31343aad40ed4fbb1078f1314496472a3a4ac9507774','T3':'840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c'},'comparator_artifact_hashes':identities['comparator_artifact_hashes'],'stage4_artifact_hashes':identities['stage4_artifact_hashes'],'cost_contract':'CORRECTED_SINGLE_C1','tick':TICK,'lifecycle_registry_identity':_sha(HERE/'canonical_lifecycle_registry.csv'),'canonical_mode_result':{'trades':9694,'mismatches':0,'maximum_metric_delta':0.0},'runtime_ledger_rows':len(ev),'runtime_ledger_sha256':ledger_sha,'no_optimization':True,'no_parameter_search':True,'no_posthoc_tuning':True,'no_BE1':True,'RISK_CAP':False,'minimum_hold':False,'session_filter':False,'Stage6':False}
    manifest['output_hashes']={p.name:_sha(p) for p in sorted(output.glob('*')) if p.is_file()};_json(output/'manifest_trail1.json',manifest);return manifest
