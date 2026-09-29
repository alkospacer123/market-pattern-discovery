"""Deterministic Stage 6.2 exact one-bar breakout confirmation replay."""
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
STARTING_MAIN_SHA="65d79271806a434c13973c274dad11c27eb3a973"
T3_SHA=frozen.T3_SHA; PARAM_SHA=frozen.PARAM_SHA; SYMBOLS=frozen.SYMBOLS
PATHS=("FULL_CANONICAL","ONE_BAR_BREAKOUT_CONFIRMATION"); TICK=.001
OLD_STAGE6=HERE.parent/"stage6_production_assembly/production_assembly_decision.csv"
BENCH=HERE.parent/"stage6_fixed_basket_reassessment"
OLD_STAGE6_SHA=frozen.DECISION_SHA
EVENT_COLUMNS=['generation','lifecycle','fold_id','strategy','timeframe','instrument','candidate_config_identity','trade_id','direction','entry_time','entry_price','initial_stop_price','initial_risk_price','exit_time','exit_price','exit_reason','gross_R','cost_R','net_R_C1','bars_held']

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def frame_sha(f): return hashlib.sha256(f.to_csv(index=False,lineterminator='\n',float_format='%.12g').encode()).hexdigest()
def confirmation_transition(pending, signal):
    """Evaluate one completed bar. Return (confirmed, next pending, rejection)."""
    if pending is None:
        return False, signal, None
    direction=pending[0] if isinstance(pending,tuple) else pending
    if signal == direction:
        return True, None, None
    return False, signal, "NONE" if signal is None else "OPPOSITE"

def _record(meta,pos,t,price,reason):
    sign=1 if pos['direction']=='LONG' else -1; gross=sign*(price-pos['entry'])/pos['risk']; cost=2*TICK/pos['risk']
    return {**meta,'trade_id':f"T3-H1-{meta['instrument']}-{pos['seq']:06d}",'direction':pos['direction'],'entry_time':pos['entry_time'],'entry_price':pos['entry'],'initial_stop_price':pos['initial'],'initial_risk_price':pos['risk'],'exit_time':t,'exit_price':price,'exit_reason':reason,'gross_R':gross,'cost_R':cost,'net_R_C1':gross-cost,'bars_held':pos['bars']+1}

def replay_t3(frame, meta, require_confirmation=False):
    """Raw causal replay; pending state lives for exactly the immediately next bar."""
    strategy=T3MTFTrend(_parameters()); high=DataLoader.h4_from_h1(frame)
    low,high=strategy.calculate_indicators(frame,high); cursor=-1; pos=None; pending=None; out=[]; signal_events=[]
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
            if not require_confirmation and signal:
                entry=float(b.Close); stop=float(strategy.calculate_stop_loss(signal,entry,float(b.ATR)))
                pos={'direction':signal,'entry':entry,'entry_time':t,'initial':stop,'risk':abs(entry-stop),'stop':stop,'extreme':entry,'bars':0,'seq':len(out)+1}
            elif require_confirmation:
                old=pending; confirmed,pending,rejection=confirmation_transition(old,signal)
                if old is not None:
                    signal_events.append({'instrument':meta['instrument'],'lifecycle':meta['lifecycle'],'direction':old,'initiating_time':old[1] if isinstance(old,tuple) else None,'confirmation_time':t,'confirmed':confirmed,'rejection_reason':rejection})
                # Pending carries direction and initiating timestamp without changing signal semantics.
                if isinstance(pending,str): pending=(pending,t)
                if confirmed:
                    direction=old[0] if isinstance(old,tuple) else old
                    entry=float(b.Close); stop=float(strategy.calculate_stop_loss(direction,entry,float(b.ATR)))
                    pos={'direction':direction,'entry':entry,'entry_time':t,'initial':stop,'risk':abs(entry-stop),'stop':stop,'extreme':entry,'bars':0,'seq':len(out)+1}
                    signal_events[-1]['direction']=direction; signal_events[-1]['opened']=True
                elif old is not None:
                    signal_events[-1]['direction']=old[0] if isinstance(old,tuple) else old; signal_events[-1]['opened']=False
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
    return replay_t3(frame,meta,path==PATHS[1])

def replay_all(data_root,path,return_events=False):
    # Deliberately isolated by path; neither ledger is an input to the other.
    results=[_execute_row((r,str(data_root),path)) for r in registry_rows()]
    frames=[x[0] for x in results]
    trades=pd.concat(frames,ignore_index=True).sort_values(['lifecycle','fold_id','exit_time','instrument','trade_id'],kind='mergesort').reset_index(drop=True)
    events=pd.DataFrame([e for x in results for e in x[1]])
    return (trades,events) if return_events else trades

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
   key=['direction','entry_time','entry_price']; z=a.merge(b,on=key,how='outer',suffixes=('_full','_onebar'),indicator=True); both=z[z._merge=='both']; same=(pd.to_datetime(both.exit_time_full,utc=True)==pd.to_datetime(both.exit_time_onebar,utc=True))&(both.exit_price_full==both.exit_price_onebar)
   rows.append({'instrument':s,'lifecycle':life,'full_trades':len(a),'onebar_trades':len(b),'matched_entry_trades':len(both),'full_only_entries':int((z._merge=='left_only').sum()),'onebar_only_entries':int((z._merge=='right_only').sum()),'matched_entries_same_exit':int(same.sum()),'matched_entries_changed_exit':int((~same).sum()),'full_net_R':float(a.net_R_C1.sum()),'onebar_net_R':float(b.net_R_C1.sum()),'total_delta_R':float(b.net_R_C1.sum()-a.net_R_C1.sum())})
 return pd.DataFrame(rows)

def confirmation_funnel(events,trades):
 events=events.copy(); events['confirmation_time']=pd.to_datetime(events.confirmation_time,utc=True)
 trades=trades.copy(); trades['entry_time']=pd.to_datetime(trades.entry_time,utc=True)
 events=events.merge(trades[['instrument','lifecycle','direction','entry_time','net_R_C1']],left_on=['instrument','lifecycle','direction','confirmation_time'],right_on=['instrument','lifecycle','direction','entry_time'],how='left')
 rows=[]
 groups=[(k,g) for k,g in events.groupby(['instrument','lifecycle','direction'],dropna=False)] + [(('ALL','ALL','ALL'),events)]
 for (instrument,life,direction),g in groups:
  confirmed=int(g.confirmed.sum()); initiated=len(g)
  rows.append({'instrument':instrument,'lifecycle':life,'direction':direction,'initiating_breakout_signals':initiated,'confirmed_next_bar_signals':confirmed,'rejected_next_bar_signals':initiated-confirmed,'confirmation_rate':confirmed/initiated if initiated else np.nan,'rejected_next_signal_NONE':int((g.rejection_reason=='NONE').sum()),'rejected_next_signal_OPPOSITE':int((g.rejection_reason=='OPPOSITE').sum()),'trades_opened_after_confirmation':int(g.opened.fillna(False).sum()),'resulting_net_R':float(g.net_R_C1.fillna(0).sum())})
 return pd.DataFrame(rows)

def holding_buckets(paths):
 labels=['< 3h','3–6h','6–12h','12–24h','24–48h','48–96h','>96h']; rows=[]
 def bucket(h):
  return labels[0] if h<3 else labels[1] if h<6 else labels[2] if h<12 else labels[3] if h<24 else labels[4] if h<48 else labels[5] if h<=96 else labels[6]
 for path,x in paths.items():
  x=x.copy(); x['hours']=(pd.to_datetime(x.exit_time,utc=True)-pd.to_datetime(x.entry_time,utc=True)).dt.total_seconds()/3600; x['bucket']=x.hours.map(bucket)
  for life in frozen.LIFECYCLES:
   allg=x[x.lifecycle==life]; total_losses=abs(float(allg.loc[allg.net_R_C1<0,'net_R_C1'].sum()))
   for label in labels:
    g=allg[allg.bucket==label]; r=metrics(g); loss=abs(float(g.loc[g.net_R_C1<0,'net_R_C1'].sum()))
    rows.append({'path':path,'lifecycle':life,'holding_bucket':label,'trades':len(g),'net_R':r['net_R'],'PF':r['PF'],'expectancy_R':r['expectancy_R'],'win_rate':r['win_rate'],'share_of_total_trades':len(g)/len(allg) if len(allg) else 0,'share_of_total_losses':loss/total_losses if total_losses else 0})
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
 decision='ONE_BAR_CONFIRMATION_NO_MATERIAL_DIFFERENCE' if equal else ('ONE_BAR_CONFIRMATION_ADMIT_TO_STRUCTURAL_STACK' if preferred==PATHS[1] and bool(out.iloc[1].all_annual_gates_pass) else 'ONE_BAR_CONFIRMATION_REJECTED_FULL_REMAINS_BENCHMARK')
 out['preferred_path']=preferred; out['computed_decision']=decision; out['tolerance']=1e-9; return out,decision

def authenticate(data_root):
 manifest=json.loads((BENCH/'audit_manifest.json').read_text()); source=json.loads((HERE.parent/'stage5_structural_validation/trail1/manifest_trail1.json').read_text())['source_hashes']; hs={k:v for k,v in source.items() if k.endswith('_H1.csv') and any(f'/{s}/' in k for s in SYMBOLS)}
 bench_hashes={p.name:sha(p) for p in BENCH.iterdir() if p.is_file()}
 checks={'starting_main':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==STARTING_MAIN_SHA,'strategy_sha':sha(ROOT/'TradingSystemLab/strategies/trend/T3_MTF_Trend.py')==T3_SHA,'parameter_sha':set(frozen.lifecycle_registry().query("lifecycle!='baseline'").strategy_parameter_hash)=={PARAM_SHA},'four_source_hashes':len(hs)==4 and all(sha(Path(data_root)/p)==h for p,h in hs.items()),'old_stage6_sha':sha(OLD_STAGE6)==OLD_STAGE6_SHA}
 if not all(checks.values()): raise RuntimeError(f'AUTHENTICATION_FAILED:{checks}')
 return {'checks':checks,'source_hashes':hs,'benchmark_hashes':bench_hashes,'benchmark_manifest_hash':sha(BENCH/'audit_manifest.json')}

def _report(a,decision,hashes,auth):
 y=a['yearly_metrics.csv']; c=a['one_bar_decision_comparison.csv']; funnel=a['confirmation_funnel.csv']; hold=a['holding_bucket_comparison.csv']
 lines=['# Final Stage 6.2 ONE_BAR Breakout Confirmation Report','','> **RETROSPECTIVELY_SUPPORTED_STRUCTURAL_HYPOTHESIS** evidence; 2025–2026 is revealed historical evidence, not fresh OOS validation.','','## Compact summary']
 tab=c[['path','annual_floor_R','worst_12M_R','worst_6M_R','worst_DD_R','minimum_recovery_factor','positive_month_share','chronological_net_R','all_annual_gates_pass']].copy()
 for life,yr,name in views(): tab[name]=tab.path.map(lambda p:float(y[(y.path==p)&(y.lifecycle==life)&(y.year==yr)].net_R.iloc[0]))
 tab=tab.rename(columns={'path':'Path','annual_floor_R':'Annual Floor','worst_12M_R':'Worst 12M','worst_6M_R':'Worst 6M','worst_DD_R':'Worst DD','minimum_recovery_factor':'Min Recovery','positive_month_share':'Positive Months','chronological_net_R':'Chronological R','all_annual_gates_pass':'Gate'})
 tab=tab[['Path','Baseline 2023','Baseline 2024','WF 2024','OOS 2025','OOS 2026 YTD','Annual Floor','Worst 12M','Worst 6M','Worst DD','Min Recovery','Positive Months','Chronological R','Gate']]
 lines += ['',tab.to_markdown(index=False,floatfmt='.6f'),'','## Provenance and methodological authority',f'- Actual starting main: `{STARTING_MAIN_SHA}`. Frozen T3 source SHA: `{T3_SHA}`; candidate parameter SHA: `{PARAM_SHA}`.',f'- Four authenticated raw H1 hashes: `{json.dumps(auth["source_hashes"],sort_keys=True)}`.',f'- Previous Stage 6 decision SHA: `{OLD_STAGE6_SHA}`. Frozen A–F and Stage 6.1 evidence remained read-only.','- Original v1 H1 methodology applied independently to v3 perpetual research generation: Baseline → Optimization → Robustness → Walk Forward → TRUE OOS.','', '## Frozen candidate and exact causal state machine','`T3_H1_candidate_v3` / `T3-H1-4e73cdb77246`: EMA 100, slope 5, ADX 14/20, ATR 14/20, Donchian 20, stop 2.5 ATR, trail 3.0 ATR; C1, tick 0.001.','While flat, a frozen T3 signal at completed H1 bar t only arms its direction. On the immediately next completed bar t+1 the frozen signal and completed-H4 regime are recalculated. Equal direction opens at Close(t+1), with ATR(t+1) determining the initial stop. NONE or opposite rejects the old event; a signal on that failed bar may arm a fresh event. Pending state never survives beyond that bar. No session rule or other structural modification is applied. Canonical exit/trailing and context construction are unchanged.',f'- FULL hash: `{hashes[PATHS[0]][0]}`. ONE_BAR hash: `{hashes[PATHS[1]][0]}`. Each raw replay was independently executed twice with matching hashes.','']
 sections=[('FULL vs ONE_BAR yearly summary','yearly_metrics.csv'),('Complete monthly FULL and ONE_BAR results','monthly_metrics.csv'),('Complete instrument × month matrices','instrument_monthly_metrics.csv'),('Instrument × year results','instrument_yearly_metrics.csv'),('Direction results','direction_metrics.csv'),('Confirmation funnel','confirmation_funnel.csv'),('Holding-duration and quick-failure diagnostics','holding_bucket_comparison.csv'),('Causal trade-path reconciliation','full_vs_onebar_trade_path_reconciliation.csv'),('Rolling 3M/6M/12M stability','rolling_stability.csv'),('Lifecycle DD and recovery','lifecycle_metrics.csv'),('Monthly concentration','monthly_concentration.csv'),('Annual gates and frozen hierarchy','one_bar_decision_comparison.csv')]
 for title,name in sections: lines += [f'## {title}','',a[name].to_markdown(index=False,floatfmt='.6f'),'']
 lines += ['## Historical A–F monthly benchmark appendix','Read-only authenticated Stage 6 benchmark; identities were not recomputed.','',pd.read_csv(BENCH/'basket_monthly_metrics.csv').to_markdown(index=False,floatfmt='.6f'),'','## Stage 6.1 read-only reference']
 s61=pd.read_csv(HERE.parent/'stage6_session_10_21_causal/session_decision_comparison.csv'); sr=s61[s61.path!='FULL_CANONICAL'].iloc[0]
 lines += [f'- Authenticated decision: `SESSION_10_21_ADMIT_TO_STRUCTURAL_STACK`; annual floor `{sr.annual_floor_R:.6f}`, worst 12M `{sr.worst_12M_R:.6f}`, worst 6M `{sr.worst_6M_R:.6f}`, worst DD `{sr.worst_DD_R:.6f}`, chronological R `{sr.chronological_net_R:.6f}`. SESSION is not part of this comparison.','','## Direct answers and computed decision']
 total=funnel.query("instrument=='ALL'").iloc[0]; rec=a['full_vs_onebar_trade_path_reconciliation.csv']
 lines += [f'- Initial breakouts: `{int(total.initiating_breakout_signals)}`; confirmed: `{int(total.confirmed_next_bar_signals)}` (`{total.confirmation_rate:.2%}`); rejected: `{int(total.rejected_next_bar_signals)}`.',f'- LONG/SHORT confirmed: `{dict(funnel.query("instrument != 'ALL'").groupby('direction').confirmed_next_bar_signals.sum())}`. ONE_BAR-only causal entries: `{int(rec.onebar_only_entries.sum())}`; FULL-only entries: `{int(rec.full_only_entries.sum())}`.']
 quick=hold[hold.holding_bucket.isin(['< 3h','3–6h','6–12h','12–24h'])].groupby('path').agg(trades=('trades','sum'),net_R=('net_R','sum')).reset_index(); lines += [f'- Under-24h comparison: `{quick.to_dict("records")}`. This is diagnostic; no minimum-hold rule was introduced.']
 for life,yr,label in views():
  f=float(y.query('path==@PATHS[0] and lifecycle==@life and year==@yr').net_R.iloc[0]); o=float(y.query('path==@PATHS[1] and lifecycle==@life and year==@yr').net_R.iloc[0]); lines.append(f'- {label}: FULL `{f:.6f} R`, ONE_BAR `{o:.6f} R`, delta `{o-f:+.6f} R`.')
 lines += [f'- Frozen hierarchy independently selects `{c.preferred_path.iloc[0]}`. Computed decision: **`{decision}`**.',f'- ONE_BAR is {"admitted" if decision=="ONE_BAR_CONFIRMATION_ADMIT_TO_STRUCTURAL_STACK" else "not admitted"} to the later Structural Stack. No combined strategy was built.','- Stage 7 was not executed; Stage 6.3 was not started.']
 return '\n'.join(lines)+'\n'

def execute(data_root,output_dir=HERE):
 auth=authenticate(data_root); output_dir=Path(output_dir); paths={}; hashes={}; events=None
 for path in PATHS:
  a,e=replay_all(data_root,path,True); b,_=replay_all(data_root,path,True); hashes[path]=[frame_sha(a),frame_sha(b)]
  if hashes[path][0]!=hashes[path][1]: raise RuntimeError('NONDETERMINISTIC_REPLAY')
  paths[path]=a
  if path==PATHS[1]: events=e
 mon=monthly(paths); year=yearly(paths,mon); inst=instrument_yearly(paths); roll=rolling(mon); conc=concentration(mon)
 life=pd.DataFrame([{'path':p,'lifecycle':l,**metrics(g)} for p,x in paths.items() for l,g in x.groupby('lifecycle')])
 direction=pd.DataFrame([{'path':p,'lifecycle':l,'direction':d,**metrics(g)} for p,x in paths.items() for (l,d),g in x.groupby(['lifecycle','direction'])])
 rec=reconciliation(paths); funnel=confirmation_funnel(events,paths[PATHS[1]]); hold=holding_buckets(paths); comp,decision=comparison(year,life,roll,mon,conc)
 artifacts={'confirmation_registry.csv':pd.DataFrame([{'path':p,'strategy':'T3_H1_candidate_v3','configuration':'T3-H1-4e73cdb77246','parameter_sha':PARAM_SHA,'strategy_sha':T3_SHA,'instruments':'+'.join(SYMBOLS),'timeframe':'H1','cost_contract':'CORRECTED_SINGLE_C1','tick':TICK,'confirmation_bars':1 if p==PATHS[1] else 0,'same_direction_required':p==PATHS[1],'entry_price_source':'confirmation_bar_close' if p==PATHS[1] else 'signal_bar_close','session_restriction':False,'canonical_exits':True} for p in PATHS]),'full_canonical_trades.csv':paths[PATHS[0]],'one_bar_confirmation_trades.csv':paths[PATHS[1]],'full_vs_onebar_trade_path_reconciliation.csv':rec,'confirmation_funnel.csv':funnel,'holding_bucket_comparison.csv':hold,'yearly_metrics.csv':year,'monthly_metrics.csv':mon.drop(columns=[f'{s}_net_R' for s in SYMBOLS]),'instrument_yearly_metrics.csv':inst,'instrument_monthly_metrics.csv':mon[['path','lifecycle','year','month',*[f'{s}_net_R' for s in SYMBOLS],'net_R']].rename(columns={'net_R':'portfolio_total_R'}),'direction_metrics.csv':direction,'rolling_stability.csv':roll,'lifecycle_metrics.csv':life,'monthly_concentration.csv':conc,'one_bar_decision_comparison.csv':comp}
 output_dir.mkdir(parents=True,exist_ok=True)
 for n,f in artifacts.items(): f.to_csv(output_dir/n,index=False,lineterminator='\n',float_format='%.12g')
 (output_dir/'FINAL_ONE_BAR_BREAKOUT_CONFIRMATION_REPORT.md').write_text(_report(artifacts,decision,hashes,auth))
 s61=HERE.parent/'stage6_session_10_21_causal'; session_hashes={p.name:sha(p) for p in s61.iterdir() if p.is_file()}
 manifest={'starting_main_sha':STARTING_MAIN_SHA,'strategy_sha':T3_SHA,'parameter_sha':PARAM_SHA,'source_hashes':auth['source_hashes'],'old_stage6_sha':OLD_STAGE6_SHA,'benchmark_hashes':auth['benchmark_hashes'],'stage6_1_hashes':session_hashes,'deterministic_replay_hashes':hashes,'decision':decision,'historical_evidence_label':'RETROSPECTIVELY_SUPPORTED_STRUCTURAL_HYPOTHESIS','stage7_executed':False,'source_endpoint':str(max(pd.to_datetime(x.exit_time,utc=True).max() for x in paths.values()))}
 manifest['artifact_hashes']={n:sha(output_dir/n) for n in [*artifacts,'FINAL_ONE_BAR_BREAKOUT_CONFIRMATION_REPORT.md']}; (output_dir/'audit_manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
 return artifacts,manifest

if __name__=='__main__':
 from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation.run_stage5_trail1 import resolve_data_root
 root,_=resolve_data_root(); out=Path(os.environ.get('STAGE6_ONE_BAR_OUTPUT_DIR',HERE)); _,m=execute(root,out); print(json.dumps({'decision':m['decision'],'hashes':m['deterministic_replay_hashes']},sort_keys=True))
