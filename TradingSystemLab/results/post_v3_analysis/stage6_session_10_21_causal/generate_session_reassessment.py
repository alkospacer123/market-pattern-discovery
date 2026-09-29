"""Deterministic Stage 6.1 causal 10:00--21:00 Moscow entry-session replay."""
from __future__ import annotations

import hashlib, json, os, shutil, subprocess, tempfile
from dataclasses import replace
from pathlib import Path
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd

from TradingSystemLab.core.data_loader import DataLoader
from TradingSystemLab.strategies.trend.T3_MTF_Trend import T3MTFTrend, T3Parameters
from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation.stage5_trail1_execution import Trail1State
from TradingSystemLab.results.post_v3_analysis.stage6_fixed_basket_reassessment import generate_reassessment as frozen

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[3]
STARTING_MAIN_SHA="01d4b247bf365f2b90a974bc155c07d8a1ae6bf3"
T3_SHA=frozen.T3_SHA; PARAM_SHA=frozen.PARAM_SHA; SYMBOLS=frozen.SYMBOLS
PATHS=("FULL_CANONICAL","SESSION_10_21_CAUSAL"); TZ=ZoneInfo("Europe/Moscow")
START_MINUTE=10*60; END_MINUTE=21*60; TICK=.001
OLD_STAGE6=HERE.parent/"stage6_production_assembly/production_assembly_decision.csv"
BENCH=HERE.parent/"stage6_fixed_basket_reassessment"
OLD_STAGE6_SHA=frozen.DECISION_SHA
EVENT_COLUMNS=['generation','lifecycle','fold_id','strategy','timeframe','instrument','candidate_config_identity','trade_id','direction','entry_time','entry_price','initial_stop_price','initial_risk_price','exit_time','exit_price','exit_reason','gross_R','cost_R','net_R_C1','bars_held']

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def frame_sha(f): return hashlib.sha256(f.to_csv(index=False,lineterminator='\n',float_format='%.12g').encode()).hexdigest()
def session_eligible(timestamp)->bool:
    t=pd.Timestamp(timestamp)
    if t.tzinfo is None: raise ValueError("ENTRY_TIMESTAMP_MUST_BE_TIMEZONE_AWARE")
    local=t.tz_convert(TZ); minute=local.hour*60+local.minute
    return START_MINUTE <= minute < END_MINUTE

def _record(meta,pos,t,price,reason):
    sign=1 if pos['direction']=='LONG' else -1; gross=sign*(price-pos['entry'])/pos['risk']; cost=2*TICK/pos['risk']
    return {**meta,'trade_id':f"T3-H1-{meta['instrument']}-{pos['seq']:06d}",'direction':pos['direction'],'entry_time':pos['entry_time'],'entry_price':pos['entry'],'initial_stop_price':pos['initial'],'initial_risk_price':pos['risk'],'exit_time':t,'exit_price':price,'exit_reason':reason,'gross_R':gross,'cost_R':cost,'net_R_C1':gross-cost,'bars_held':pos['bars']+1}

def replay_t3(frame, meta, restrict_entries=False):
    """Full bar-by-bar replay; the predicate is consulted only while flat."""
    strategy=T3MTFTrend(_parameters()); high=DataLoader.h4_from_h1(frame)
    low,high=strategy.calculate_indicators(frame,high); cursor=-1; pos=None; out=[]; signal_events=[]
    for t,b in low.iterrows():
        while cursor+1<len(high) and high.index[cursor+1]<=t: cursor+=1
        regime=strategy.regime(high.iloc[cursor]) if cursor>=0 else None
        if pos is not None:
            stop=pos['stop']
            if strategy.exit_signal(pos['direction'],b,stop):
                price=min(float(b.Open),stop) if pos['direction']=='LONG' else max(float(b.Open),stop)
                out.append(_record(meta,pos,t,price,'INITIAL_STOP' if stop==pos['initial'] else 'ATR_TRAILING_STOP')); pos=None
            else:
                pos['bars']+=1; pos['extreme']=max(pos['extreme'],b.High) if pos['direction']=='LONG' else min(pos['extreme'],b.Low)
                candidate=float(strategy.manage_position(pos['direction'],pos['extreme'],b.ATR))
                pos['stop']=max(stop,candidate) if pos['direction']=='LONG' else min(stop,candidate)
        if pos is None and pd.notna(b.ATR):
            signal=strategy.generate_signal(b,regime)
            if signal:
                allowed=(not restrict_entries) or session_eligible(t); signal_events.append((t,signal,allowed))
                if allowed:
                    entry=float(b.Close); stop=float(strategy.calculate_stop_loss(signal,entry,float(b.ATR)))
                    pos={'direction':signal,'entry':entry,'entry_time':t,'initial':stop,'risk':abs(entry-stop),'stop':stop,'extreme':entry,'bars':0,'seq':len(out)+1}
    return pd.DataFrame(out).reindex(columns=EVENT_COLUMNS), signal_events, high

def _parameters():
    p=ROOT/'TradingSystemLab/results/perpetual_v3/phase3_candidate_freeze/candidate_registry.json'
    x=next(x for x in json.loads(p.read_text())['candidates'] if x['strategy']=='T3' and x['timeframe']=='H1')
    return replace(T3Parameters(),**x['parameters'])

def registry_rows():
    return frozen.lifecycle_registry().to_dict('records')

def _execute_row(item):
    r,root,path=item; raw=DataLoader(forbid_true_oos=False).load_csv(Path(root)/'forever'/r['instrument']/f"{r['instrument']}_H1.csv")
    frame=DataLoader.close_index(raw,'1h').loc[r['start_timestamp']:r['end_timestamp']].copy()
    meta={k:r[k] for k in ('generation','lifecycle','fold_id','strategy','timeframe','instrument','candidate_config_identity')}
    return replay_t3(frame,meta,path==PATHS[1])[0]

def replay_all(data_root,path):
    # Deliberately isolated by path; no FULL ledger is an input to SESSION.
    frames=[_execute_row((r,str(data_root),path)) for r in registry_rows()]
    return pd.concat(frames,ignore_index=True).sort_values(['lifecycle','fold_id','exit_time','instrument','trade_id'],kind='mergesort').reset_index(drop=True)

def pf(v):
    v=pd.to_numeric(v); loss=v[v<0].sum(); return float(v[v>0].sum()/abs(loss)) if loss else np.nan
def dd(v):
    v=pd.to_numeric(v).reset_index(drop=True); curve=pd.concat([pd.Series([0.]),v.cumsum()],ignore_index=True); return float((curve-curve.cummax()).min())
def streak(v):
    best=run=0
    for x in v: run=run+1 if x<0 else 0; best=max(best,run)
    return best
def views(): return [('baseline',2023,'Baseline 2023'),('baseline',2024,'Baseline 2024'),('walk_forward',2024,'WF 2024'),('historical_true_oos',2025,'OOS 2025'),('historical_true_oos',2026,'OOS 2026 YTD')]

def monthly(paths):
    reg=frozen.lifecycle_registry(); rows=[]
    for path,src in paths.items():
      src=src.copy(); src['exit']=pd.to_datetime(src.exit_time,utc=True)
      for life in frozen.LIFECYCLES:
        lr=reg[reg.lifecycle==life]; first=pd.to_datetime(lr.start_timestamp,utc=True).min(); last=pd.to_datetime(lr.end_timestamp,utc=True).max()
        for per in pd.period_range(first.tz_localize(None).to_period('M'),last.tz_localize(None).to_period('M')):
          available=[s for s in SYMBOLS if ((x:=lr[lr.instrument==s]).shape[0] and pd.to_datetime(x.start_timestamp,utc=True).min().tz_localize(None).to_period('M')<=per<=pd.to_datetime(x.end_timestamp,utc=True).max().tz_localize(None).to_period('M'))]
          g=src[(src.lifecycle==life)&(src.exit.dt.year==per.year)&(src.exit.dt.month==per.month)&src.instrument.isin(available)]
          contrib={s:float(g.loc[g.instrument==s,'net_R_C1'].sum()) if s in available else np.nan for s in SYMBOLS}; net=float(np.nansum(list(contrib.values())))
          rows.append({'path':path,'lifecycle':life,'year':per.year,'month':per.month,'availability_status':'AVAILABLE_NO_TRADES' if not len(g) else 'AVAILABLE','available_instruments':'+'.join(available),'trades':len(g),'net_R':net,'PF':pf(g.net_R_C1),'cumulative_R':0.,'month_sign':'POSITIVE' if net>0 else 'NEGATIVE' if net<0 else 'ZERO',**{f'{s}_net_R':contrib[s] for s in SYMBOLS}})
    out=pd.DataFrame(rows); out['cumulative_R']=out.groupby(['path','lifecycle']).net_R.cumsum(); return out

def metrics(v):
    d=dd(v.net_R_C1); net=float(v.net_R_C1.sum()); hold=(pd.to_datetime(v.exit_time,utc=True)-pd.to_datetime(v.entry_time,utc=True)).dt.total_seconds().mean()/3600 if len(v) else 0
    return {'trades':len(v),'net_R':net,'PF':pf(v.net_R_C1),'expectancy_R':float(v.net_R_C1.mean()) if len(v) else 0.,'max_DD_R':d,'recovery_factor':net/abs(d) if d else np.nan,'win_rate':float((v.net_R_C1>0).mean()) if len(v) else 0.,'median_trade_R':float(v.net_R_C1.median()) if len(v) else 0.,'average_holding_hours':float(hold) if len(v) else 0.}

def yearly(paths,mon):
 rows=[]
 for path,src in paths.items():
  x=src.copy(); x['exit']=pd.to_datetime(x.exit_time,utc=True)
  for life,year,label in views():
   g=x[(x.lifecycle==life)&(x.exit.dt.year==year)]; m=mon[(mon.path==path)&(mon.lifecycle==life)&(mon.year==year)]
   rows.append({'path':path,'lifecycle':life,'year':year,'period':label,**metrics(g),'positive_months':int((m.net_R>0).sum()),'available_months':len(m),'positive_month_share':float((m.net_R>0).mean()),'median_monthly_R':float(m.net_R.median()),'monthly_std_R':float(m.net_R.std(ddof=0)),'worst_month_R':float(m.net_R.min()),'best_month_R':float(m.net_R.max()),'longest_negative_month_streak':streak(m.net_R)})
 return pd.DataFrame(rows)

def instrument_yearly(paths):
 rows=[]
 for path,src in paths.items():
  x=src.copy(); x['exit']=pd.to_datetime(x.exit_time,utc=True)
  for life,year,label in views():
   allg=x[(x.lifecycle==life)&(x.exit.dt.year==year)]; total=float(allg.net_R_C1.sum())
   for s in SYMBOLS:
    g=allg[allg.instrument==s]; r=metrics(g); rows.append({'path':path,'instrument':s,'lifecycle':life,'year':year,**r,'contribution_to_portfolio_net_R':r['net_R']/total if total else np.nan})
 return pd.DataFrame(rows)

def rolling(mon):
 rows=[]
 for (path,life),g in mon.groupby(['path','lifecycle'],sort=True):
  g=g.sort_values(['year','month']); periods=pd.PeriodIndex(g.year.astype(str)+'-'+g.month.astype(str).str.zfill(2),freq='M'); row={'path':path,'lifecycle':life}
  for w in (3,6,12):
   vals=[float(g.net_R.iloc[i-w+1:i+1].sum()) for i in range(w-1,len(g)) if periods[i].ordinal-periods[i-w+1].ordinal==w-1]
   row.update({f'complete_{w}M_windows':len(vals),f'worst_{w}M_R':min(vals) if vals else np.nan,f'final_{w}M_R':vals[-1] if vals else np.nan})
   if w==6: row['median_6M_R']=float(np.median(vals)) if vals else np.nan
  rows.append(row)
 return pd.DataFrame(rows)

def concentration(mon):
 rows=[]
 for (path,life),g in mon.groupby(['path','lifecycle']):
  pos=g.loc[g.net_R>0,'net_R'].sort_values(ascending=False); den=float(pos.sum())
  rows.append({'path':path,'lifecycle':life,'total_net_R':float(g.net_R.sum()),'best_month_R':float(g.net_R.max()),'best_month_share_of_positive_R':float(pos.head(1).sum()/den) if den else np.nan,'top_3_positive_months_R':float(pos.head(3).sum()),'top_3_share_of_positive_R':float(pos.head(3).sum()/den) if den else np.nan,'worst_month_R':float(g.net_R.min()),'bottom_3_months_R':float(g.nsmallest(3,'net_R').net_R.sum())})
 return pd.DataFrame(rows)

def reconciliation(paths):
 rows=[]
 for life in frozen.LIFECYCLES:
  for s in SYMBOLS:
   a=paths[PATHS[0]].query('lifecycle==@life and instrument==@s'); b=paths[PATHS[1]].query('lifecycle==@life and instrument==@s')
   key=['direction','entry_time','entry_price']; z=a.merge(b,on=key,how='outer',suffixes=('_full','_session'),indicator=True); both=z[z._merge=='both']; same=(pd.to_datetime(both.exit_time_full,utc=True)==pd.to_datetime(both.exit_time_session,utc=True))&(both.exit_price_full==both.exit_price_session)
   rows.append({'instrument':s,'lifecycle':life,'full_trades':len(a),'session_trades':len(b),'matched_entry_trades':len(both),'full_only_entries':int((z._merge=='left_only').sum()),'session_only_entries':int((z._merge=='right_only').sum()),'matched_entries_same_exit':int(same.sum()),'matched_entries_changed_exit':int((~same).sum()),'full_net_R':float(a.net_R_C1.sum()),'session_net_R':float(b.net_R_C1.sum()),'total_delta_R':float(b.net_R_C1.sum()-a.net_R_C1.sum())})
 return pd.DataFrame(rows)

def posthoc(paths):
 a=paths[PATHS[0]].copy(); a['inside']=pd.to_datetime(a.entry_time,utc=True).map(session_eligible); p=a[a.inside]; b=paths[PATHS[1]]; rows=[]
 for life in frozen.LIFECYCLES:
  x=p[p.lifecycle==life]; y=b[b.lifecycle==life]; xe=set(pd.to_datetime(x.entry_time,utc=True).astype(str)); ye=set(pd.to_datetime(y.entry_time,utc=True).astype(str)); xx=set(pd.to_datetime(x.exit_time,utc=True).astype(str)); yy=set(pd.to_datetime(y.exit_time,utc=True).astype(str))
  rows.append({'lifecycle':life,'posthoc_trades':len(x),'causal_trades':len(y),'trade_delta':len(y)-len(x),'posthoc_net_R':float(x.net_R_C1.sum()),'causal_net_R':float(y.net_R_C1.sum()),'net_R_delta':float(y.net_R_C1.sum()-x.net_R_C1.sum()),'entry_timestamp_symmetric_difference':len(xe^ye),'exit_timestamp_symmetric_difference':len(xx^yy)})
 return pd.DataFrame(rows)

def comparison(year,life,roll,mon,conc):
 rows=[]
 for path in PATHS:
  y=year[year.path==path]; cal=y[y.lifecycle!='walk_forward']; lf=life[life.path==path]; rr=roll[roll.path==path]; mm=mon[mon.path==path]; cc=conc[conc.path==path]
  gates=bool((y.net_R>0).all()); rows.append({'path':path,'all_annual_gates_pass':gates,'annual_floor_R':float(cal.net_R.min()),'worst_12M_R':float(rr.worst_12M_R.min()),'worst_6M_R':float(rr.worst_6M_R.min()),'worst_DD_R':float(lf.max_DD_R.min()),'minimum_recovery_factor':float(lf.recovery_factor.min()),'positive_month_share':float((mm.net_R>0).mean()),'median_monthly_R':float(mm.net_R.median()),'longest_negative_month_streak':max(streak(g.net_R) for _,g in mm.groupby('lifecycle')),'top_3_positive_month_concentration':float(cc.top_3_share_of_positive_R.max()),'chronological_net_R':float(cal.net_R.sum())})
 out=pd.DataFrame(rows); eligible=out[out.all_annual_gates_pass]
 cols=['annual_floor_R','worst_12M_R','worst_6M_R','worst_DD_R','minimum_recovery_factor','positive_month_share','median_monthly_R','longest_negative_month_streak','top_3_positive_month_concentration','chronological_net_R']; asc=[False,False,False,False,False,False,False,True,True,False]
 ranked=eligible.sort_values(cols,ascending=asc,kind='mergesort'); preferred=str(ranked.iloc[0].path) if len(ranked) else PATHS[0]
 equal=all(np.isclose(out.iloc[0][c],out.iloc[1][c],rtol=0,atol=1e-9,equal_nan=True) for c in cols)
 decision='SESSION_10_21_NO_MATERIAL_DIFFERENCE' if equal else ('SESSION_10_21_ADMIT_TO_STRUCTURAL_STACK' if preferred==PATHS[1] and bool(out.iloc[1].all_annual_gates_pass) else 'SESSION_10_21_REJECTED_FULL_REMAINS_BENCHMARK')
 out['preferred_path']=preferred; out['computed_decision']=decision; out['tolerance']=1e-9; return out,decision

def authenticate(data_root):
 manifest=json.loads((BENCH/'audit_manifest.json').read_text()); source=json.loads((HERE.parent/'stage5_structural_validation/trail1/manifest_trail1.json').read_text())['source_hashes']; hs={k:v for k,v in source.items() if k.endswith('_H1.csv') and any(f'/{s}/' in k for s in SYMBOLS)}
 bench_hashes={p.name:sha(p) for p in BENCH.iterdir() if p.is_file()}
 checks={'starting_main':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==STARTING_MAIN_SHA,'strategy_sha':sha(ROOT/'TradingSystemLab/strategies/trend/T3_MTF_Trend.py')==T3_SHA,'parameter_sha':set(frozen.lifecycle_registry().query("lifecycle!='baseline'").strategy_parameter_hash)=={PARAM_SHA},'four_source_hashes':len(hs)==4 and all(sha(Path(data_root)/p)==h for p,h in hs.items()),'old_stage6_sha':sha(OLD_STAGE6)==OLD_STAGE6_SHA}
 if not all(checks.values()): raise RuntimeError(f'AUTHENTICATION_FAILED:{checks}')
 return {'checks':checks,'source_hashes':hs,'benchmark_hashes':bench_hashes,'benchmark_manifest_hash':sha(BENCH/'audit_manifest.json')}

def _report(a,decision,hashes,auth):
 y=a['yearly_metrics.csv']; c=a['session_decision_comparison.csv']; lines=['# Final Stage 6.1 Causal Session 10:00–21:00 Report','','> Retrospectively supported structural hypothesis; **not fresh OOS validated**.','', '## Compact summary']
 tab=c[['path','annual_floor_R','worst_12M_R','worst_6M_R','worst_DD_R','minimum_recovery_factor','positive_month_share','chronological_net_R','all_annual_gates_pass']].copy()
 for life,yr,name in views(): tab[name]=tab.path.map(lambda p:float(y[(y.path==p)&(y.lifecycle==life)&(y.year==yr)].net_R.iloc[0]))
 tab=tab[['path','Baseline 2023','Baseline 2024','WF 2024','OOS 2025','OOS 2026 YTD','annual_floor_R','worst_12M_R','worst_6M_R','worst_DD_R','minimum_recovery_factor','positive_month_share','chronological_net_R','all_annual_gates_pass']]; lines += ['',tab.to_markdown(index=False,floatfmt='.6f'),'']
 lines += ['## Provenance',f'- Starting main: `{STARTING_MAIN_SHA}`.',f'- Frozen strategy SHA: `{T3_SHA}`; parameter SHA: `{PARAM_SHA}`.',f'- Raw source hashes: `{json.dumps(auth["source_hashes"],sort_keys=True)}`.',f'- Old Stage 6 SHA: `{OLD_STAGE6_SHA}`; fixed A–F artifacts remained byte-identical.','', '## Exact rule and causal proof','Only a **new entry** is eligible at `10:00 <= actual entry event < 21:00 Europe/Moscow`. Exits, stops, trailing, gaps, signals, and completed H4 context remain unrestricted and unchanged. FULL and SESSION were separately replayed bar-by-bar from raw H1. Rejected signals leave SESSION flat and later signals are processed normally.',f'- FULL hash: `{hashes[PATHS[0]][0]}`; SESSION hash: `{hashes[PATHS[1]][0]}`. Both repeated hashes matched.','']
 sections=[('FULL vs SESSION yearly','yearly_metrics.csv'),('Lifecycle DD and recovery','lifecycle_metrics.csv'),('Complete monthly paths','monthly_metrics.csv'),('Instrument × month matrices','instrument_monthly_metrics.csv'),('Instrument × year','instrument_yearly_metrics.csv'),('Direction breakdown','direction_metrics.csv'),('FULL Moscow entry-hour diagnostics','entry_hour_diagnostics.csv'),('Rolling 3M/6M/12M','rolling_stability.csv'),('Monthly concentration','monthly_concentration.csv'),('Causal path reconciliation','full_vs_session_trade_path_reconciliation.csv'),('Post-hoc filter vs causal replay','posthoc_filter_vs_causal_session.csv'),('Stability-first hierarchy and annual gates','session_decision_comparison.csv')]
 for title,name in sections: lines += [f'## {title}','',a[name].to_markdown(index=False,floatfmt='.6f'),'']
 lines += ['## Historical A–F benchmark appendix','The frozen A–F monthly artifact is embedded read-only below; identities were not recomputed or modified.','',pd.read_csv(BENCH/'basket_monthly_metrics.csv').to_markdown(index=False,floatfmt='.6f'),'','## Answers and decision']
 full=y[y.path==PATHS[0]].set_index(['lifecycle','year']); sess=y[y.path==PATHS[1]].set_index(['lifecycle','year'])
 for life,yr,label in views():
  d=float(sess.loc[(life,yr)].net_R-full.loc[(life,yr)].net_R); lines.append(f'- {label}: SESSION {"improves" if d>0 else "worsens" if d<0 else "equals"} FULL by `{d:+.6f} R`.')
 lines += [f'- Causal replay and post-hoc filtering differ: `{bool(a["posthoc_filter_vs_causal_session.csv"].trade_delta.ne(0).any() or a["posthoc_filter_vs_causal_session.csv"].net_R_delta.abs().gt(1e-9).any())}`.',f'- Computed decision: **`{decision}`**. Preferred path and all remaining hierarchy answers are shown in the table above.','- Prospective performance remains unvalidated. Stage 7 and Stage 6.2 were not executed.','']
 return '\n'.join(lines)

def execute(data_root,output_dir=HERE):
 auth=authenticate(data_root); output_dir=Path(output_dir); paths={}; hashes={}
 for path in PATHS:
  a=replay_all(data_root,path); b=replay_all(data_root,path); hashes[path]=[frame_sha(a),frame_sha(b)]
  if hashes[path][0]!=hashes[path][1]: raise RuntimeError('NONDETERMINISTIC_REPLAY')
  paths[path]=a
 mon=monthly(paths); year=yearly(paths,mon); inst=instrument_yearly(paths); roll=rolling(mon); conc=concentration(mon)
 life=pd.DataFrame([{'path':p,'lifecycle':l,**metrics(g)} for p,x in paths.items() for l,g in x.groupby('lifecycle')])
 direction=pd.DataFrame([{'path':p,'lifecycle':l,'direction':d,**metrics(g)} for p,x in paths.items() for (l,d),g in x.groupby(['lifecycle','direction'])])
 full=paths[PATHS[0]].copy(); full['moscow_hour']=pd.to_datetime(full.entry_time,utc=True).dt.tz_convert(TZ).dt.hour
 hour=pd.DataFrame([{'entry_hour_moscow':h,**metrics(g),'instrument_split':json.dumps(g.instrument.value_counts().sort_index().to_dict()),'direction_split':json.dumps(g.direction.value_counts().sort_index().to_dict())} for h,g in full.groupby('moscow_hour')])
 rec=reconciliation(paths); post=posthoc(paths); comp,decision=comparison(year,life,roll,mon,conc)
 artifacts={'session_registry.csv':pd.DataFrame([{'path':p,'strategy':'T3_H1_candidate_v3','configuration':'T3-H1-4e73cdb77246','parameter_sha':PARAM_SHA,'strategy_sha':T3_SHA,'instruments':'+'.join(SYMBOLS),'timeframe':'H1','cost_contract':'CORRECTED_SINGLE_C1','tick':TICK,'timezone':'Europe/Moscow','entry_start_inclusive':'10:00','entry_end_exclusive':'21:00','entries_only':p==PATHS[1]} for p in PATHS]),'full_canonical_trades.csv':paths[PATHS[0]],'session_10_21_trades.csv':paths[PATHS[1]],'full_vs_session_trade_path_reconciliation.csv':rec,'posthoc_filter_vs_causal_session.csv':post,'yearly_metrics.csv':year,'monthly_metrics.csv':mon.drop(columns=[f'{s}_net_R' for s in SYMBOLS]),'instrument_yearly_metrics.csv':inst,'instrument_monthly_metrics.csv':mon[['path','lifecycle','year','month',*[f'{s}_net_R' for s in SYMBOLS],'net_R']].rename(columns={'net_R':'portfolio_total_R'}),'direction_metrics.csv':direction,'entry_hour_diagnostics.csv':hour,'rolling_stability.csv':roll,'lifecycle_metrics.csv':life,'monthly_concentration.csv':conc,'session_decision_comparison.csv':comp}
 output_dir.mkdir(parents=True,exist_ok=True)
 for n,f in artifacts.items(): f.to_csv(output_dir/n,index=False,lineterminator='\n',float_format='%.12g')
 (output_dir/'FINAL_SESSION_10_21_CAUSAL_REPORT.md').write_text(_report(artifacts,decision,hashes,auth))
 manifest={'starting_main_sha':STARTING_MAIN_SHA,'strategy_sha':T3_SHA,'parameter_sha':PARAM_SHA,'source_hashes':auth['source_hashes'],'old_stage6_sha':OLD_STAGE6_SHA,'benchmark_hashes':auth['benchmark_hashes'],'deterministic_replay_hashes':hashes,'decision':decision,'historical_evidence_label':'RETROSPECTIVELY_SUPPORTED_STRUCTURAL_HYPOTHESIS','stage7_executed':False,'source_endpoint':str(max(pd.to_datetime(x.exit_time,utc=True).max() for x in paths.values()))}
 manifest['artifact_hashes']={n:sha(output_dir/n) for n in [*artifacts,'FINAL_SESSION_10_21_CAUSAL_REPORT.md']}; (output_dir/'audit_manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
 return artifacts,manifest

if __name__=='__main__':
 from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation.run_stage5_trail1 import resolve_data_root
 root,_=resolve_data_root(); out=Path(os.environ.get('STAGE6_SESSION_OUTPUT_DIR',HERE)); _,m=execute(root,out); print(json.dumps({'decision':m['decision'],'hashes':m['deterministic_replay_hashes']},sort_keys=True))
