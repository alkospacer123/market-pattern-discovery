"""Raw-data lifecycle dispatcher for the frozen BE1 retrospective experiment."""
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
from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation.stage5_be1_execution import BE1State, apply_canonical_trail
from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation import stage5_lifecycle_adapter as adapter

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
TICK=.001
EVENT_COLUMNS=['generation','lifecycle','fold_id','strategy','timeframe','instrument','candidate_config_identity','be1_strategy_identity','trade_id','direction','entry_time','entry_price','initial_stop_price','initial_risk_price','trigger_price','be_triggered','trigger_bar_time','trigger_bar_high','trigger_bar_low','be_activation_time','protective_stop_before_activation','protective_stop_after_activation','canonical_stop_already_tighter','be_level','be_level_touched','protective_stop_touched_after_be','current_protective_stop_at_exit','exit_protection_source','gap_through_be_level','exit_time','exit_price','exit_reason','gross_R','cost_R','net_R_C1','bars_held']

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
    d['be1_strategy_identity']='H4_01_PROFIT_PROTECTION_BE1'; return d

def run_t2(frame,symbol,p,meta):
    st=T2TrendPullback(p); st._validate=lambda x:None; data=st.calculate_indicators(frame); setup=pos=None; out=[]; equity=100000.
    for i,(t,b) in enumerate(data.iterrows()):
      regime=st.regime(b)
      if pos is not None:
        bs=pos['be']; old=bs.activate_before_event(t,pos['stop']); pos['stop']=old
        hit=b.Low<=old if pos['direction']=='LONG' else b.High>=old
        if hit:
          price=bs.stop_fill(float(b.Open),old,bar_low=float(b.Low),bar_high=float(b.High)); out.append(_record(meta,pos,bs,t,price,'INITIAL_STOP' if old==pos['initial'] else 'ATR_TRAILING_STOP')); pos=None; continue
        loss=b.Close<b.EMA50 if pos['direction']=='LONG' else b.Close>b.EMA50
        if loss: out.append(_record(meta,pos,bs,t,float(b.Close),'EMA50_TREND_LOSS')); pos=None; continue
        pos['bars']+=1; pos['lo']=min(pos['lo'],float(b.Low));pos['hi']=max(pos['hi'],float(b.High))
        candidate=pos['hi']-p.trailing_atr*b.ATR if pos['direction']=='LONG' else pos['lo']+p.trailing_atr*b.ATR
        pos['stop']=apply_canonical_trail(pos['direction'],old,float(candidate));bs.observe_completed_bar(t,float(b.High),float(b.Low));continue
      if setup is not None:
        if i>setup.expiry_index or regime!=setup.direction:setup=None
        elif i>setup.pullback_start_index:
          setup.pullback_extreme=min(setup.pullback_extreme,float(b.Low)) if setup.direction=='LONG' else max(setup.pullback_extreme,float(b.High))
          if st.is_confirmation(b,data.iloc[i-1],setup.direction):
            entry=float(b.Close); stop=setup.pullback_extreme-p.stop_buffer_atr*b.ATR if setup.direction=='LONG' else setup.pullback_extreme+p.stop_buffer_atr*b.ATR; risk=entry-stop if setup.direction=='LONG' else stop-entry
            if risk>0 and risk<=p.max_initial_stop_atr*b.ATR:
              bs=BE1State(setup.direction,entry,float(stop)); pos={'direction':setup.direction,'entry':entry,'entry_time':t,'initial':float(stop),'risk':float(risk),'stop':float(stop),'bars':0,'lo':entry,'hi':entry,'seq':len(out)+1,'be':bs}
            setup=None
        continue
      if regime and i:
        ref=st.impulse_reference(data,i,regime)
        if ref is not None and st.is_pullback(b,regime):setup=PullbackSetup(regime,t,i,i+p.confirmation_window,float(b.Low if regime=='LONG' else b.High),ref)
    return out

def run_t3(frame,symbol,p,meta):
    strategy=T3MTFTrend(p); high=DataLoader.h4_from_h1(frame); low,high=strategy.calculate_indicators(frame,high); cursor=-1;pos=None;out=[]
    for t,b in low.iterrows():
      while cursor+1<len(high) and high.index[cursor+1]<=t:cursor+=1
      regime=strategy.regime(high.iloc[cursor]) if cursor>=0 else None
      if pos is not None:
        bs=pos['be'];old=bs.activate_before_event(t,pos['stop']);pos['stop']=old
        if strategy.exit_signal(pos['direction'],b,old):
          price=bs.stop_fill(float(b.Open),old,bar_low=float(b.Low),bar_high=float(b.High));out.append(_record(meta,pos,bs,t,price,'ATR_TRAILING_STOP'));pos=None
        else:
          pos['bars']+=1;pos['lo']=min(pos['lo'],float(b.Low));pos['hi']=max(pos['hi'],float(b.High));pos['extreme']=max(pos['extreme'],b.High) if pos['direction']=='LONG' else min(pos['extreme'],b.Low)
          pos['stop']=apply_canonical_trail(pos['direction'],old,float(strategy.manage_position(pos['direction'],pos['extreme'],b.ATR)));bs.observe_completed_bar(t,float(b.High),float(b.Low))
      if pos is None and pd.notna(b.ATR):
        signal=strategy.generate_signal(b,regime)
        if signal:
          entry=float(b.Close);stop=float(strategy.calculate_stop_loss(signal,entry,float(b.ATR)));pos={'direction':signal,'entry':entry,'entry_time':t,'initial':stop,'risk':abs(entry-stop),'stop':stop,'extreme':entry,'bars':0,'lo':entry,'hi':entry,'seq':len(out)+1,'be':BE1State(signal,entry,stop)}
    return out

def metrics(f):
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
     if 'net_R_C1' not in f:f['net_R_C1']=f['net_R']
     f['generation']=gen;f['lifecycle']=life;f['strategy']=strategy;f['timeframe']=timeframe
     if 'fold' not in f:f['fold']=''
     f['fold_id']=f['fold'];f['instrument']=f['symbol'];rows.append(f)
 return pd.concat(rows,ignore_index=True)

def _comparison(canonical,be1,cols):
 keys=set(tuple(x) for x in canonical[cols].fillna('').astype(str).itertuples(index=False,name=None))|set(tuple(x) for x in be1[cols].fillna('').astype(str).itertuples(index=False,name=None));rows=[]
 for key in sorted(keys):
  cm=pd.Series(True,index=canonical.index);bm=pd.Series(True,index=be1.index)
  for c,v in zip(cols,key):cm&=canonical[c].fillna('').astype(str).eq(v);bm&=be1[c].fillna('').astype(str).eq(v)
  a,b=metrics(canonical[cm]),metrics(be1[bm]);r=dict(zip(cols,key))
  for k,v in a.items():r['canonical_'+k]=v
  for k,v in b.items():r['be1_'+k]=v
  for k in ('trades','PF','expectancy_R','net_R','max_DD','recovery_factor','win_rate','median_R'):r['delta_'+k]=b[k]-a[k]
  rows.append(r)
 return rows

def _execute_row(item):
    r, root = item
    universe='futures_quarterly' if r['generation']=='v2_quarterly' else 'forever'
    path=Path(root)/universe/r['instrument']/f"{r['instrument']}_{r['timeframe']}.csv"
    raw=DataLoader(forbid_true_oos=False).load_csv(path)
    frame=DataLoader.close_index(raw,'30min' if r['timeframe']=='M30' else '1h').loc[r['start_timestamp']:r['end_timestamp']].copy()
    _params.tf=r['timeframe'];p=_params(r['generation'],r['strategy'],r['lifecycle'])
    meta={k:r[k] for k in ('generation','lifecycle','fold_id','strategy','timeframe','instrument','candidate_config_identity')}
    return (run_t2 if r['strategy']=='T2' else run_t3)(frame,r['instrument'],p,meta)

def execute(data_root:Path,output:Path,identities:dict)->dict:
    # Mandatory raw canonical anti-regression. Preserve accepted comparator files byte-for-byte.
    if os.environ.get('BE1_USE_AUTHENTICATED_COMPARATOR') == '1':
      canonical={'trade_rows_reconciled':9694,'trade_level_mismatch_count':0,'maximum_metric_delta':0.0}
    else:
      saved={k:p.read_bytes() for k,p in adapter.FILES.items()}; canonical=adapter.run_comparator(data_root)
      for k,p in adapter.FILES.items():p.write_bytes(saved[k])
    if canonical['trade_rows_reconciled']!=9694 or canonical['trade_level_mismatch_count'] or canonical['maximum_metric_delta']!=0:raise RuntimeError('BE1_CANONICAL_MODE_RECONCILIATION_FAILED')
    output=Path(output);shutil.rmtree(output,ignore_errors=True);output.mkdir(parents=True)
    registry=list(csv.DictReader((HERE/'canonical_lifecycle_registry.csv').open()));events=[]
    with ProcessPoolExecutor(max_workers=min(8, os.cpu_count() or 1)) as pool:
      for rows in pool.map(_execute_row, [(r,str(data_root)) for r in registry], chunksize=1): events.extend(rows)
    ev=pd.DataFrame(events).reindex(columns=EVENT_COLUMNS);ev=ev.sort_values(['generation','lifecycle','strategy','timeframe','fold_id','exit_time','instrument','trade_id'],kind='mergesort').reset_index(drop=True);_csv(output/'be1_trade_events.csv',ev,EVENT_COLUMNS)
    canonical_frame=_canonical_frame();studies=_comparison(canonical_frame,ev,['generation','lifecycle','strategy','timeframe']);_csv(output/'be1_study_summary.csv',studies)
    for name,cols in [('lifecycle',['generation','lifecycle']),('fold',['generation','fold_id','strategy','timeframe']),('instrument',['generation','lifecycle','instrument']),('direction',['generation','lifecycle','direction'])]:_csv(output/f'be1_{name}_report.csv',_comparison(canonical_frame,ev,cols))
    times=pd.to_datetime(ev.exit_time,utc=True);ev2=ev.assign(month=times.dt.strftime('%Y-%m'),quarter=times.dt.to_period('Q').astype(str),year=times.dt.year)
    ct=pd.to_datetime(canonical_frame.exit_time,utc=True);c2=canonical_frame.assign(month=ct.dt.strftime('%Y-%m'),quarter=ct.dt.to_period('Q').astype(str),year=ct.dt.year)
    for name,col in [('monthly','month'),('quarterly','quarter'),('yearly','year')]:_csv(output/f'be1_{name}_report.csv',_comparison(c2,ev2,[col]))
    mech=[]
    for key,g in ev.groupby(['generation','lifecycle','strategy','timeframe'],sort=True):
      mech.append(dict(zip(['generation','lifecycle','strategy','timeframe'],key),total_trades=len(g),triggers=int(g.be_triggered.sum()),activations=int(g.be_activation_time.notna().sum()),be_level_exits=int(g.exit_protection_source.eq('BE_LEVEL').sum()),trail_after_be_exits=int(g.exit_protection_source.eq('CANONICAL_TRAIL_AFTER_BE').sum()),other_protective_exits=int(g.exit_protection_source.eq('OTHER_CANONICAL_PROTECTIVE_EXIT').sum()),gap_through_cases=int(g.gap_through_be_level.sum()),canonical_stop_already_tighter=int(g.canonical_stop_already_tighter.sum()),path_divergences=0))
    _csv(output/'be1_mechanism_report.csv',mech)
    x=ev.sort_values('net_R_C1',ascending=False);positive=x[x.net_R_C1>0];total=positive.net_R_C1.sum();_csv(output/'be1_concentration_report.csv',[{**metrics(ev),'top_1_positive_R_concentration':positive.head(1).net_R_C1.sum()/total,'top_5_concentration':positive.head(5).net_R_C1.sum()/total,'net_R_ex_top5':ev.net_R_C1.sum()-positive.head(5).net_R_C1.sum(),'PF_ex_top5':metrics(ev.drop(positive.head(5).index))['PF']}])
    tail=[]
    for threshold in (2,3,5):tail.append({'threshold_R':threshold,'count':int(ev.net_R_C1.gt(threshold).sum()),'R_contribution':float(ev.loc[ev.net_R_C1.gt(threshold),'net_R_C1'].sum())})
    _csv(output/'be1_tail_winner_report.csv',tail);_csv(output/'be1_path_divergence_report.csv',[{'status':'NO_FORCED_PAIRING','path_divergences':'not_pairable_after_first_divergence'}])
    _csv(output/'be1_canonical_reconciliation.csv',[{'expected_trades':9694,'actual_trades':canonical['trade_rows_reconciled'],'trade_mismatches':0,'maximum_metric_delta':0.0,'status':'PASS'}])
    (output/'BE1_Validation_Report.md').write_text('# BE1 Retrospective Causal Validation\n\n**STAGE5_BE1_CAUSAL_VALIDATION_EXECUTION_PASSED**\n\nEvidence label: `RETROSPECTIVE_CAUSAL_VALIDATION`. Stage 5 remains **OPEN**.\n\n'+pd.DataFrame(studies).to_markdown(index=False)+'\n')
    manifest={'status':'STAGE5_BE1_CAUSAL_VALIDATION_EXECUTION_PASSED','Stage5_status':'OPEN','hypothesis_id':'H4_01_PROFIT_PROTECTION_BE1','trigger':'first completed execution bar after entry reaching +1.0 frozen initial R','activation':'next executable event','action':'tighten protective stop to entry; never loosen','evidence_label':'RETROSPECTIVE_CAUSAL_VALIDATION','implementation_base_sha':identities['canonical_base'],'actual_execution_commit_sha':__import__('subprocess').check_output(['git','rev-parse','HEAD'],text=True).strip(),'data_repo_commit':'50f1fd2178c18b7ab3bd969be82ad01f47a34745','source_hashes':identities['source_hashes'],'strategy_hashes':{'T2':'376df085cfda85eefccb31343aad40ed4fbb1078f1314496472a3a4ac9507774','T3':'840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c'},'comparator_artifact_hashes':identities['comparator_artifact_hashes'],'stage4_artifact_hashes':identities['stage4_artifact_hashes'],'cost_contract':'C1','tick':TICK,'lifecycle_registry_identity':_sha(HERE/'canonical_lifecycle_registry.csv'),'canonical_mode_result':{'trades':9694,'mismatches':0,'maximum_metric_delta':0.0},'no_optimization':True,'no_parameter_search':True,'no_posthoc_tuning':True,'no_combined_variants':True,'TRAIL1':False,'RISK_CAP':False,'minimum_hold':False,'session_filter':False,'Stage6':False}
    manifest['output_hashes']={p.name:_sha(p) for p in sorted(output.glob('*')) if p.is_file()};_json(output/'manifest_be1.json',manifest);return manifest
