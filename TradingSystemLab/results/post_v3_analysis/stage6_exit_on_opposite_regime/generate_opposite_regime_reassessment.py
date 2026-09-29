"""Deterministic Stage 6.3 opposite-regime exit replay."""
from __future__ import annotations

import hashlib, json, os, subprocess
from dataclasses import replace
from pathlib import Path
import numpy as np
import pandas as pd

from TradingSystemLab.core.data_loader import DataLoader
from TradingSystemLab.strategies.trend.T3_MTF_Trend import T3MTFTrend, T3Parameters
from TradingSystemLab.results.post_v3_analysis.stage6_fixed_basket_reassessment import generate_reassessment as frozen

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[3]
STARTING_MAIN_SHA="df69c016b3f3e46deb31f57a797d640ea5c850c0"
T3_SHA=frozen.T3_SHA; PARAM_SHA=frozen.PARAM_SHA; SYMBOLS=frozen.SYMBOLS
PATHS=("FULL_CANONICAL","EXIT_ON_OPPOSITE_REGIME"); TICK=.001
OLD_STAGE6=HERE.parent/"stage6_production_assembly/production_assembly_decision.csv"
BENCH=HERE.parent/"stage6_fixed_basket_reassessment"
OLD_STAGE6_SHA=frozen.DECISION_SHA
EVENT_COLUMNS=['generation','lifecycle','fold_id','strategy','timeframe','instrument','candidate_config_identity','trade_id','direction','entry_time','entry_price','initial_stop_price','initial_risk_price','exit_time','exit_price','exit_reason','gross_R','cost_R','net_R_C1','bars_held']

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def frame_sha(f): return hashlib.sha256(f.to_csv(index=False,lineterminator='\n',float_format='%.12g').encode()).hexdigest()
def _record(meta,pos,t,price,reason):
    sign=1 if pos['direction']=='LONG' else -1; gross=sign*(price-pos['entry'])/pos['risk']; cost=2*TICK/pos['risk']
    return {**meta,'trade_id':f"T3-H1-{meta['instrument']}-{pos['seq']:06d}",'direction':pos['direction'],'entry_time':pos['entry_time'],'entry_price':pos['entry'],'initial_stop_price':pos['initial'],'initial_risk_price':pos['risk'],'exit_time':t,'exit_price':price,'exit_reason':reason,'gross_R':gross,'cost_R':cost,'net_R_C1':gross-cost,'bars_held':pos['bars']+1}

def opposite_exit_reason(direction, regime, stop_hit=False):
    """Return the deterministic exit reason; protective stops have priority."""
    if stop_hit:
        return "PROTECTIVE_STOP"
    if (direction == "LONG" and regime == "SHORT") or (direction == "SHORT" and regime == "LONG"):
        return "OPPOSITE_REGIME_EXIT"
    return None

def replay_t3(frame, meta, exit_on_opposite=False):
    """Replay frozen T3; completed-H4 opposite regimes exit at the H1 close."""
    strategy=T3MTFTrend(_parameters()); high=DataLoader.h4_from_h1(frame)
    low,high=strategy.calculate_indicators(frame,high); cursor=-1; pos=None; out=[]; transitions=[]; exit_events=[]; previous_regime=None; skip_entry=False
    for t,b in low.iterrows():
        while cursor+1<len(high) and high.index[cursor+1]<=t: cursor+=1
        regime=strategy.regime(high.iloc[cursor]) if cursor>=0 else None
        skip_entry=False
        if pos is not None:
            transitions.append({'instrument':meta['instrument'],'lifecycle':meta['lifecycle'],'direction':pos['direction'],'time':t,'from_regime':previous_regime,'to_regime':regime,'is_opposite':opposite_exit_reason(pos['direction'],regime)=="OPPOSITE_REGIME_EXIT",'triggered_exit':False})
            stop=pos['stop']
            if strategy.exit_signal(pos['direction'],b,stop):
                price=min(float(b.Open),stop) if pos['direction']=='LONG' else max(float(b.Open),stop)
                out.append(_record(meta,pos,t,price,'INITIAL_STOP' if stop==pos['initial'] else 'ATR_TRAILING_STOP')); pos=None
            elif exit_on_opposite and opposite_exit_reason(pos['direction'],regime)=='OPPOSITE_REGIME_EXIT':
                trade=_record(meta,pos,t,float(b.Close),'OPPOSITE_REGIME_EXIT'); out.append(trade); transitions[-1]['triggered_exit']=True
                exit_events.append({**trade,'opposite_regime_detection_time':t,'current_canonical_stop':stop,'h4_regime_before_reversal':previous_regime,'h4_regime_at_exit':regime})
                pos=None; skip_entry=True
            else:
                pos['bars']+=1; pos['extreme']=max(pos['extreme'],b.High) if pos['direction']=='LONG' else min(pos['extreme'],b.Low)
                candidate=float(strategy.manage_position(pos['direction'],pos['extreme'],b.ATR))
                pos['stop']=max(stop,candidate) if pos['direction']=='LONG' else min(stop,candidate)
        if pos is None and not skip_entry and pd.notna(b.ATR):
            signal=strategy.generate_signal(b,regime)
            if signal:
                entry=float(b.Close); stop=float(strategy.calculate_stop_loss(signal,entry,float(b.ATR)))
                pos={'direction':signal,'entry':entry,'entry_time':t,'initial':stop,'risk':abs(entry-stop),'stop':stop,'extreme':entry,'bars':0,'seq':len(out)+1}
        previous_regime=regime
    return pd.DataFrame(out).reindex(columns=EVENT_COLUMNS), transitions, exit_events, high

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
    return replay_t3(frame,meta,path==PATHS[1])

def replay_all(data_root,path,return_diagnostics=False):
    results=[_execute_row((r,str(data_root),path)) for r in registry_rows()]
    trades=pd.concat([x[0] for x in results],ignore_index=True).sort_values(['lifecycle','fold_id','exit_time','instrument','trade_id'],kind='mergesort').reset_index(drop=True)
    transitions=pd.DataFrame([e for x in results for e in x[1]])
    events=pd.DataFrame([e for x in results for e in x[2]])
    return (trades,transitions,events) if return_diagnostics else trades

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
   a=paths[PATHS[0]].query('lifecycle==@life and instrument==@s').copy(); b=paths[PATHS[1]].query('lifecycle==@life and instrument==@s').copy()
   a['entry_time']=pd.to_datetime(a.entry_time,utc=True); b['entry_time']=pd.to_datetime(b.entry_time,utc=True)
   key=['direction','entry_time','entry_price']; z=a.merge(b,on=key,how='outer',suffixes=('_full','_opposite'),indicator=True); both=z[z._merge=='both']; same=(pd.to_datetime(both.exit_time_full,utc=True)==pd.to_datetime(both.exit_time_opposite,utc=True))&(both.exit_price_full==both.exit_price_opposite)
   rows.append({'instrument':s,'lifecycle':life,'full_trades':len(a),'opposite_trades':len(b),'matched_entry_trades':len(both),'full_only_entries':int((z._merge=='left_only').sum()),'opposite_only_entries':int((z._merge=='right_only').sum()),'matched_entries_same_exit':int(same.sum()),'matched_entries_changed_exit':int((~same).sum()),'full_net_R':float(a.net_R_C1.sum()),'opposite_net_R':float(b.net_R_C1.sum()),'net_R_delta':float(b.net_R_C1.sum()-a.net_R_C1.sum())})
 return pd.DataFrame(rows)

def holding_buckets(paths):
 labels=['<3h','3–6h','6–12h','12–24h','24–48h','48–96h','>96h']; rows=[]
 def bucket(h): return labels[0] if h<3 else labels[1] if h<6 else labels[2] if h<12 else labels[3] if h<24 else labels[4] if h<48 else labels[5] if h<=96 else labels[6]
 for path,x in paths.items():
  x=x.copy(); x['hours']=(pd.to_datetime(x.exit_time,utc=True)-pd.to_datetime(x.entry_time,utc=True)).dt.total_seconds()/3600; x['bucket']=x.hours.map(bucket)
  for life in frozen.LIFECYCLES:
   allg=x[x.lifecycle==life]; losses=abs(float(allg.loc[allg.net_R_C1<0,'net_R_C1'].sum()))
   for label in labels:
    g=allg[allg.bucket==label]; r=metrics(g); loss=abs(float(g.loc[g.net_R_C1<0,'net_R_C1'].sum()))
    rows.append({'path':path,'lifecycle':life,'holding_bucket':label,'trades':len(g),'net_R':r['net_R'],'PF':r['PF'],'expectancy_R':r['expectancy_R'],'win_rate':r['win_rate'],'share_of_trades':len(g)/len(allg) if len(allg) else 0,'share_of_losses':loss/losses if losses else 0})
 return pd.DataFrame(rows)

def comparison(year,life,roll,mon,conc):
 rows=[]
 for path in PATHS:
  y=year[year.path==path]; cal=y[y.lifecycle!='walk_forward']; lf=life[life.path==path]; rr=roll[roll.path==path]; mm=mon[mon.path==path]; cc=conc[conc.path==path]
  rows.append({'path':path,'all_annual_gates_pass':bool((y.net_R>0).all()),'annual_floor_R':float(cal.net_R.min()),'worst_12M_R':float(rr.worst_12M_R.min()),'worst_6M_R':float(rr.worst_6M_R.min()),'worst_DD_R':float(lf.max_DD_R.min()),'minimum_recovery_factor':float(lf.recovery_factor.min()),'positive_month_share':float((mm.net_R>0).mean()),'median_monthly_R':float(mm.net_R.median()),'longest_negative_month_streak':max(streak(g.net_R) for _,g in mm.groupby('lifecycle')),'top_3_positive_month_concentration':float(cc.top_3_share_of_positive_R.max()),'chronological_net_R':float(cal.net_R.sum())})
 out=pd.DataFrame(rows); cols=['annual_floor_R','worst_12M_R','worst_6M_R','worst_DD_R','minimum_recovery_factor','positive_month_share','median_monthly_R','longest_negative_month_streak','top_3_positive_month_concentration','chronological_net_R']; asc=[False]*7+[True,True,False]
 eligible=out[out.all_annual_gates_pass]; ranked=eligible.sort_values(cols,ascending=asc,kind='mergesort'); preferred=str(ranked.iloc[0].path) if len(ranked) else PATHS[0]
 equal=all(np.isclose(out.iloc[0][c],out.iloc[1][c],rtol=0,atol=1e-9,equal_nan=True) for c in cols)
 decision='OPPOSITE_REGIME_EXIT_NO_MATERIAL_DIFFERENCE' if equal else ('OPPOSITE_REGIME_EXIT_ADMIT_TO_STRUCTURAL_STACK' if preferred==PATHS[1] and bool(out.iloc[1].all_annual_gates_pass) else 'OPPOSITE_REGIME_EXIT_REJECTED_FULL_REMAINS_BENCHMARK')
 out['preferred_path']=preferred; out['computed_decision']=decision; out['tolerance']=1e-9; return out,decision

def enrich_events(events,full):
 if events.empty:
  return pd.DataFrame(columns=['lifecycle','instrument','direction','entry_time','entry_price','opposite_regime_detection_time','exit_time','exit_price','holding_hours','R_at_regime_exit','current_canonical_stop','h4_regime_before_reversal','h4_regime_at_exit','canonical_FULL_winner_or_loser','canonical_FULL_exit_time','canonical_FULL_net_R','opposite_regime_net_R','delta_R'])
 e=events.copy(); f=full.copy(); keys=['instrument','lifecycle','direction','entry_time','entry_price']; z=e.merge(f[keys+['exit_time','net_R_C1']],on=keys,how='left',suffixes=('_opposite','_canonical'))
 z['entry_time']=pd.to_datetime(z.entry_time,utc=True); z['exit_time_opposite']=pd.to_datetime(z.exit_time_opposite,utc=True); z['holding_hours']=(z.exit_time_opposite-z.entry_time).dt.total_seconds()/3600
 z['R_at_regime_exit']=z.net_R_C1_opposite; z['canonical_FULL_winner_or_loser']=np.where(z.net_R_C1_canonical.isna(),'UNMATCHED',np.where(z.net_R_C1_canonical>0,'WINNER','LOSER')); z['delta_R']=z.net_R_C1_opposite-z.net_R_C1_canonical
 return z.rename(columns={'exit_time_opposite':'exit_time','exit_price':'exit_price','net_R_C1_canonical':'canonical_FULL_net_R','net_R_C1_opposite':'opposite_regime_net_R','exit_time_canonical':'canonical_FULL_exit_time'})

def transition_summary(transitions):
 rows=[]
 for (instrument,life),g in transitions.groupby(['instrument','lifecycle']):
  row={'instrument':instrument,'lifecycle':life}
  for a in ('LONG','SHORT','None'):
   for b in ('LONG','SHORT','None'): row[f'{a}_to_{b}']=int(((g.from_regime.fillna('None')==a)&(g.to_regime.fillna('None')==b)).sum())
  row['genuine_opposite_reversals_while_open']=int(g.is_opposite.sum()); row['actual_opposite_exits']=int(g.triggered_exit.sum()); row['none_observations_while_open']=int(g.to_regime.isna().sum()); rows.append(row)
 return pd.DataFrame(rows)

def decomposition(events):
 e=events.dropna(subset=['canonical_FULL_net_R']).copy()
 def cls(r):
  f,o=r.canonical_FULL_net_R,r.opposite_regime_net_R
  if o>f and f<0:return 'AVOIDED_LOSS'
  if o>f and o>0 and f>0:return 'IMPROVED_WIN'
  if f>o and f>0:return 'CUT_WINNER'
  if o<f and o<0 and f<0:return 'WORSENED_LOSS'
  return 'OTHER'
 e['classification']=e.apply(cls,axis=1); rows=[]
 for dims in [[],['lifecycle'],['instrument'],['lifecycle','instrument']]:
  grouped=[((),e)] if not dims else e.groupby(dims,dropna=False)
  for key,g in grouped:
   key=(key,) if dims and not isinstance(key,tuple) else key
   base={'scope':'ALL' if not dims else '+'.join(dims),'lifecycle':'ALL','instrument':'ALL'}; base.update(dict(zip(dims,key)))
   for c in ('AVOIDED_LOSS','IMPROVED_WIN','CUT_WINNER','WORSENED_LOSS','OTHER'):
    q=g[g.classification==c]; rows.append({**base,'classification':c,'trades':len(q),'canonical_R':float(q.canonical_FULL_net_R.sum()),'opposite_exit_R':float(q.opposite_regime_net_R.sum()),'delta_R':float(q.delta_R.sum())})
 return pd.DataFrame(rows)

def giveback(events):
 x=events.copy(); x['MFE_before_exit_R']=np.nan; x['opposite_giveback_R']=np.nan; x['canonical_giveback_R']=np.nan
 return x[['lifecycle','instrument','direction','entry_time','exit_time','MFE_before_exit_R','opposite_regime_net_R','opposite_giveback_R','canonical_FULL_net_R','canonical_giveback_R']]

def authenticate(data_root):
 source=json.loads((HERE.parent/'stage5_structural_validation/trail1/manifest_trail1.json').read_text())['source_hashes']; hs={k:v for k,v in source.items() if k.endswith('_H1.csv') and any(f'/{s}/' in k for s in SYMBOLS)}
 bench_hashes={p.name:sha(p) for p in BENCH.iterdir() if p.is_file()}; s61=HERE.parent/'stage6_session_10_21_causal'; s62=HERE.parent/'stage6_one_bar_breakout_confirmation'
 checks={'starting_main':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==STARTING_MAIN_SHA,'strategy_sha':sha(ROOT/'TradingSystemLab/strategies/trend/T3_MTF_Trend.py')==T3_SHA,'parameter_sha':set(frozen.lifecycle_registry().query("lifecycle!='baseline'").strategy_parameter_hash)=={PARAM_SHA},'four_source_hashes':len(hs)==4 and all(sha(Path(data_root)/p)==h for p,h in hs.items()),'old_stage6_sha':sha(OLD_STAGE6)==OLD_STAGE6_SHA}
 if not all(checks.values()): raise RuntimeError(f'AUTHENTICATION_FAILED:{checks}')
 return {'checks':checks,'source_hashes':hs,'benchmark_hashes':bench_hashes,'stage6_1_hashes':{p.name:sha(p) for p in s61.iterdir() if p.is_file()},'stage6_2_hashes':{p.name:sha(p) for p in s62.iterdir() if p.is_file()}}

def _report(a,decision,hashes,auth):
 y=a['yearly_metrics.csv']; c=a['opposite_regime_decision_comparison.csv']; ev=a['opposite_regime_exit_events.csv']; tr=a['regime_transition_diagnostics.csv']; dec=a['opposite_exit_decomposition.csv']
 tab=c[['path','annual_floor_R','worst_12M_R','worst_6M_R','worst_DD_R','minimum_recovery_factor','positive_month_share','chronological_net_R','all_annual_gates_pass']].copy()
 for life,yr,name in views(): tab[name]=tab.path.map(lambda path, life=life, yr=yr:float(y[(y.path==path)&(y.lifecycle==life)&(y.year==yr)].net_R.iloc[0]))
 tab=tab.rename(columns={'path':'Path','annual_floor_R':'Annual Floor','worst_12M_R':'Worst 12M','worst_6M_R':'Worst 6M','worst_DD_R':'Worst DD','minimum_recovery_factor':'Min Recovery','positive_month_share':'Positive Months','chronological_net_R':'Chronological R','all_annual_gates_pass':'Gate'})
 tab=tab[['Path','Baseline 2023','Baseline 2024','WF 2024','OOS 2025','OOS 2026 YTD','Annual Floor','Worst 12M','Worst 6M','Worst DD','Min Recovery','Positive Months','Chronological R','Gate']]
 lines=['# Final Stage 6.3 EXIT_ON_OPPOSITE_REGIME Report','',tab.to_markdown(index=False,floatfmt='.6f'),'','## Provenance',f'- Starting main `{STARTING_MAIN_SHA}`; T3 `{T3_SHA}`; parameters `{PARAM_SHA}`.','- Raw hashes: `'+json.dumps(auth['source_hashes'],sort_keys=True)+'`.','', '## Methodology authority and frozen candidate','Original v1 H1 methodology applied independently to the v3 perpetual research generation. Candidate `T3_H1_candidate_v3`, configuration `T3-H1-4e73cdb77246`; EMA 100/slope 5, ADX 14/20, ATR 14/20, Donchian 20, stop 2.5 ATR, trail 3.0 ATR. C1 tick 0.001.','', '## Exact rule, priority, and causal proof','Only open LONG + completed causal H4 SHORT, or open SHORT + completed causal H4 LONG exits. `None` holds. Canonical intrabar protective stop is evaluated first. A surviving opposite condition known at completed H1 event t exits at Close(t). That event cannot reverse immediately; entries resume only on a later event. The sole `DataLoader.h4_from_h1` stream and `high.index <= t` publication cursor prevent incomplete/future H4 use. SESSION and ONE_BAR are absent; canonical entries, stops, and trailing are otherwise unchanged.',f'- FULL hash `{hashes[PATHS[0]][0]}`; OPPOSITE hash `{hashes[PATHS[1]][0]}`; isolated repeat hashes match.','']
 sections=[('FULL vs OPPOSITE yearly table','yearly_metrics.csv'),('Complete monthly tables','monthly_metrics.csv'),('Instrument × month matrices','instrument_monthly_metrics.csv'),('Instrument × year','instrument_yearly_metrics.csv'),('Direction results','direction_metrics.csv'),('Opposite-regime exit events','opposite_regime_exit_events.csv'),('Regime transition diagnostics','regime_transition_diagnostics.csv'),('Avoided-loss vs cut-winner decomposition','opposite_exit_decomposition.csv'),('Giveback comparison','opposite_exit_giveback.csv'),('Holding-time comparison','holding_bucket_comparison.csv'),('Causal path reconciliation','full_vs_opposite_regime_trade_path_reconciliation.csv'),('Rolling 3M/6M/12M','rolling_stability.csv'),('DD/recovery','lifecycle_metrics.csv'),('Monthly concentration','monthly_concentration.csv'),('Annual gates and frozen hierarchy','opposite_regime_decision_comparison.csv')]
 for title,name in sections: lines += [f'## {title}','',a[name].to_markdown(index=False,floatfmt='.6f'),'']
 lines += ['## Historical A–F monthly appendix','',pd.read_csv(BENCH/'basket_monthly_metrics.csv').to_markdown(index=False,floatfmt='.6f'),'','## Prior structural results','- Stage 6.1: `SESSION_10_21_ADMIT_TO_STRUCTURAL_STACK` (read-only; not executed here).','- Stage 6.2: `ONE_BAR_CONFIRMATION_REJECTED_FULL_REMAINS_BENCHMARK` (read-only; not executed here).','','## Direct answers and decision',f'- Genuine reversals while open: `{int(tr.genuine_opposite_reversals_while_open.sum())}`; exits: `{len(ev)}`; LONG→SHORT: `{int((ev.direction=="LONG").sum())}`; SHORT→LONG: `{int((ev.direction=="SHORT").sum())}`; `None` observations: `{int(tr.none_observations_while_open.sum())}`.']
 d=dec.query("scope=='ALL'");
 for cls in ('AVOIDED_LOSS','CUT_WINNER'):
  q=d[d.classification==cls].iloc[0]; lines.append(f'- {cls}: `{int(q.trades)}` trades; canonical `{q.canonical_R:.6f} R`, opposite `{q.opposite_exit_R:.6f} R`, delta `{q.delta_R:+.6f} R`.')
 for life,yr,label in views():
  f=float(y.query('path==@PATHS[0] and lifecycle==@life and year==@yr').net_R.iloc[0]); o=float(y.query('path==@PATHS[1] and lifecycle==@life and year==@yr').net_R.iloc[0]); lines.append(f'- {label}: FULL `{f:.6f} R`; TEST `{o:.6f} R`; delta `{o-f:+.6f} R`.')
 lines += [f'- Frozen hierarchy selects `{c.preferred_path.iloc[0]}`; independently auditable computed decision: **`{decision}`**.',f'- EXIT_ON_OPPOSITE_REGIME is {"admitted" if decision.endswith("ADMIT_TO_STRUCTURAL_STACK") else "not admitted"} to Structural Stack.','- This is retrospective evidence. 2025–2026 are already revealed historical evidence, 2026 is partial, WF remains separate from chronological R. Stage 7 was not executed; Stage 6.4 was not started.']
 return '\n'.join(lines)+'\n'

def execute(data_root,output_dir=HERE):
 auth=authenticate(data_root); output_dir=Path(output_dir); paths={}; hashes={}; transitions=events=None
 for path in PATHS:
  a,t,e=replay_all(data_root,path,True); b,_,_=replay_all(data_root,path,True); hashes[path]=[frame_sha(a),frame_sha(b)]
  if hashes[path][0]!=hashes[path][1]: raise RuntimeError('NONDETERMINISTIC_REPLAY')
  paths[path]=a
  if path==PATHS[1]: transitions=t; events=e
 mon=monthly(paths); year=yearly(paths,mon); inst=instrument_yearly(paths); roll=rolling(mon); conc=concentration(mon)
 life=pd.DataFrame([{'path':p,'lifecycle':l,**metrics(g)} for p,x in paths.items() for l,g in x.groupby('lifecycle')]); direction=pd.DataFrame([{'path':p,'lifecycle':l,'direction':d,**metrics(g)} for p,x in paths.items() for (l,d),g in x.groupby(['lifecycle','direction'])])
 rec=reconciliation(paths); events=enrich_events(events,paths[PATHS[0]]); trans=transition_summary(transitions); dec=decomposition(events); give=giveback(events); hold=holding_buckets(paths); comp,decision=comparison(year,life,roll,mon,conc)
 registry=pd.DataFrame([{'path':p,'strategy':'T3_H1_candidate_v3','configuration':'T3-H1-4e73cdb77246','parameter_sha':PARAM_SHA,'strategy_sha':T3_SHA,'instruments':'+'.join(SYMBOLS),'timeframe':'H1','cost_contract':'CORRECTED_SINGLE_C1','tick':TICK,'opposite_only':p==PATHS[1],'none_exits':False,'stop_priority':True,'exit_execution':'Close(t)','same_event_reversal':False,'session_restriction':False,'one_bar_confirmation':False} for p in PATHS])
 artifacts={'opposite_regime_registry.csv':registry,'full_canonical_trades.csv':paths[PATHS[0]],'opposite_regime_trades.csv':paths[PATHS[1]],'full_vs_opposite_regime_trade_path_reconciliation.csv':rec,'opposite_regime_exit_events.csv':events,'regime_transition_diagnostics.csv':trans,'opposite_exit_decomposition.csv':dec,'opposite_exit_giveback.csv':give,'holding_bucket_comparison.csv':hold,'yearly_metrics.csv':year,'monthly_metrics.csv':mon.drop(columns=[f'{s}_net_R' for s in SYMBOLS]),'instrument_yearly_metrics.csv':inst,'instrument_monthly_metrics.csv':mon[['path','lifecycle','year','month',*[f'{s}_net_R' for s in SYMBOLS],'net_R']].rename(columns={'net_R':'portfolio_total_R'}),'direction_metrics.csv':direction,'rolling_stability.csv':roll,'lifecycle_metrics.csv':life,'monthly_concentration.csv':conc,'opposite_regime_decision_comparison.csv':comp}
 output_dir.mkdir(parents=True,exist_ok=True)
 for n,f in artifacts.items(): f.to_csv(output_dir/n,index=False,lineterminator='\n',float_format='%.12g')
 (output_dir/'FINAL_EXIT_ON_OPPOSITE_REGIME_REPORT.md').write_text(_report(artifacts,decision,hashes,auth))
 manifest={'starting_main_sha':STARTING_MAIN_SHA,'strategy_sha':T3_SHA,'parameter_sha':PARAM_SHA,'source_hashes':auth['source_hashes'],'old_stage6_sha':OLD_STAGE6_SHA,'benchmark_hashes':auth['benchmark_hashes'],'stage6_1_hashes':auth['stage6_1_hashes'],'stage6_2_hashes':auth['stage6_2_hashes'],'deterministic_replay_hashes':hashes,'decision':decision,'stage7_executed':False}
 manifest['artifact_hashes']={n:sha(output_dir/n) for n in [*artifacts,'FINAL_EXIT_ON_OPPOSITE_REGIME_REPORT.md']}; (output_dir/'audit_manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n'); return artifacts,manifest

if __name__=='__main__':
 from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation.run_stage5_trail1 import resolve_data_root
 root,_=resolve_data_root(); out=Path(os.environ.get('STAGE6_OPPOSITE_OUTPUT_DIR',HERE)); _,m=execute(root,out); print(json.dumps({'decision':m['decision'],'hashes':m['deterministic_replay_hashes']},sort_keys=True))
