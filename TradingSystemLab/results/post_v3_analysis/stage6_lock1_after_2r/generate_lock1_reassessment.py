"""Deterministic Stage 6.4 LOCK1_AFTER_2R replay."""
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
STARTING_MAIN_SHA="a7745798f65cc9a514eb01aad3ae6804017e699e"
T3_SHA=frozen.T3_SHA; PARAM_SHA=frozen.PARAM_SHA; SYMBOLS=frozen.SYMBOLS
PATHS=("FULL_CANONICAL","LOCK1_AFTER_2R"); TICK=.001
OLD_STAGE6=HERE.parent/"stage6_production_assembly/production_assembly_decision.csv"
BENCH=HERE.parent/"stage6_fixed_basket_reassessment"
OLD_STAGE6_SHA=frozen.DECISION_SHA
EVENT_COLUMNS=['generation','lifecycle','fold_id','strategy','timeframe','instrument','candidate_config_identity','trade_id','direction','entry_time','entry_price','initial_stop_price','initial_risk_price','exit_time','exit_price','exit_reason','gross_R','cost_R','net_R_C1','bars_held']

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def frame_sha(f): return hashlib.sha256(f.to_csv(index=False,lineterminator='\n',float_format='%.12g').encode()).hexdigest()
def _record(meta,pos,t,price,reason):
    sign=1 if pos['direction']=='LONG' else -1; gross=sign*(price-pos['entry'])/pos['risk']; cost=2*TICK/pos['risk']
    return {**meta,'trade_id':f"T3-H1-{meta['instrument']}-{pos['seq']:06d}",'direction':pos['direction'],'entry_time':pos['entry_time'],'entry_price':pos['entry'],'initial_stop_price':pos['initial'],'initial_risk_price':pos['risk'],'exit_time':t,'exit_price':price,'exit_reason':reason,'gross_R':gross,'cost_R':cost,'net_R_C1':gross-cost,'bars_held':pos['bars']+1}

def lock_levels(direction, entry, risk, canonical_stop, active):
    """Return effective stop and whether LOCK1 is strictly binding."""
    lock = entry + risk if direction == "LONG" else entry - risk
    if not active:
        return canonical_stop, False
    effective = max(canonical_stop, lock) if direction == "LONG" else min(canonical_stop, lock)
    return effective, effective != canonical_stop

def replay_t3(frame, meta, lock1=False):
    """Replay T3 causally; a +2R event arms LOCK1 only for the next event."""
    strategy=T3MTFTrend(_parameters()); high=DataLoader.h4_from_h1(frame)
    low,high=strategy.calculate_indicators(frame,high); cursor=-1; pos=None; out=[]; activations=[]
    for t,b in low.iterrows():
        while cursor+1<len(high) and high.index[cursor+1]<=t: cursor+=1
        regime=strategy.regime(high.iloc[cursor]) if cursor>=0 else None
        if pos is not None:
            # active_at_start is deliberately snapshotted before inspecting this bar.
            active_at_start=bool(pos['armed']); canonical=pos['stop']
            effective,binding=lock_levels(pos['direction'],pos['entry'],pos['risk'],canonical,lock1 and active_at_start)
            if active_at_start and pos.get('activation_time') is None:
                pos['activation_time']=t; pos['canonical_at_activation']=canonical; pos['effective_at_activation']=effective; pos['binding_at_activation']=binding
            if strategy.exit_signal(pos['direction'],b,effective):
                price=min(float(b.Open),effective) if pos['direction']=='LONG' else max(float(b.Open),effective)
                reason='LOCK1_STOP' if binding else ('INITIAL_STOP' if effective==pos['initial'] else 'ATR_TRAILING_STOP')
                trade=_record(meta,pos,t,price,reason); trade.update({'causal_mfe_R':pos['mfe_R'],'reached_2r':pos['trigger_time'] is not None,'lock1_became_binding':pos['ever_binding'] or binding})
                out.append(trade)
                if pos['trigger_time'] is not None:
                    activations.append({**{k:trade[k] for k in ('lifecycle','instrument','direction','entry_time','entry_price','initial_stop_price','initial_risk_price')},'plus2r_trigger_price':pos['trigger_price'],'trigger_event_time':pos['trigger_time'],'first_lock1_active_event':pos.get('activation_time'),'lock1_price':pos['lock_price'],'canonical_stop_at_activation':pos.get('canonical_at_activation'),'effective_stop_at_activation':pos.get('effective_at_activation'),'lock1_tighter_at_activation':pos.get('binding_at_activation',False),'lock1_ever_binding':pos['ever_binding'] or binding,'eventual_exit_reason':reason,'final_net_R':trade['net_R_C1'],'causal_mfe_R':pos['mfe_R']})
                pos=None
            else:
                pos['ever_binding'] |= binding; pos['bars']+=1
                pos['extreme']=max(pos['extreme'],float(b.High)) if pos['direction']=='LONG' else min(pos['extreme'],float(b.Low))
                pos['mfe_R']=max(pos['mfe_R'], ((pos['extreme']-pos['entry'])/pos['risk'] if pos['direction']=='LONG' else (pos['entry']-pos['extreme'])/pos['risk']))
                candidate=float(strategy.manage_position(pos['direction'],pos['extreme'],b.ATR))
                pos['stop']=max(canonical,candidate) if pos['direction']=='LONG' else min(canonical,candidate)
                reached=(pos['extreme']>=pos['trigger_price']) if pos['direction']=='LONG' else (pos['extreme']<=pos['trigger_price'])
                if reached and not pos['armed']:
                    pos['armed']=True; pos['trigger_time']=t
        if pos is None and pd.notna(b.ATR):
            signal=strategy.generate_signal(b,regime)
            if signal:
                entry=float(b.Close); stop=float(strategy.calculate_stop_loss(signal,entry,float(b.ATR))); risk=abs(entry-stop)
                pos={'direction':signal,'entry':entry,'entry_time':t,'initial':stop,'risk':risk,'stop':stop,'extreme':entry,'bars':0,'seq':len(out)+1,'armed':False,'trigger_time':None,'activation_time':None,'trigger_price':entry+(2*risk if signal=='LONG' else -2*risk),'lock_price':entry+(risk if signal=='LONG' else -risk),'mfe_R':0.,'ever_binding':False}
    cols=EVENT_COLUMNS+['causal_mfe_R','reached_2r','lock1_became_binding']
    return pd.DataFrame(out).reindex(columns=cols), activations, high

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
    events=pd.DataFrame([e for x in results for e in x[1]])
    return (trades,events) if return_diagnostics else trades

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
 decision='LOCK1_AFTER_2R_NO_MATERIAL_DIFFERENCE' if equal else ('LOCK1_AFTER_2R_ADMIT_TO_STRUCTURAL_STACK' if preferred==PATHS[1] and bool(out.iloc[1].all_annual_gates_pass) else 'LOCK1_AFTER_2R_REJECTED_FULL_REMAINS_BENCHMARK')
 out['preferred_path']=preferred; out['computed_decision']=decision; out['tolerance']=1e-9; return out,decision

def match(paths):
 a=paths[PATHS[0]].copy(); b=paths[PATHS[1]].copy(); keys=['instrument','lifecycle','direction','entry_time','entry_price']
 return a.merge(b,on=keys,how='inner',suffixes=('_full','_lock1'))

def reconciliation(paths):
 rows=[]
 for life in frozen.LIFECYCLES:
  for sym in SYMBOLS:
   a=paths[PATHS[0]].query('lifecycle==@life and instrument==@sym'); b=paths[PATHS[1]].query('lifecycle==@life and instrument==@sym'); keys=['direction','entry_time','entry_price']
   z=a.merge(b,on=keys,how='outer',suffixes=('_full','_lock1'),indicator=True); both=z[z._merge=='both']; same=(both.exit_time_full==both.exit_time_lock1)&np.isclose(both.exit_price_full,both.exit_price_lock1)
   rows.append({'instrument':sym,'lifecycle':life,'full_trades':len(a),'lock1_trades':len(b),'matched_entries':len(both),'full_only_entries':int((z._merge=='left_only').sum()),'lock1_only_entries':int((z._merge=='right_only').sum()),'same_exits':int(same.sum()),'changed_exits':int((~same).sum()),'full_net_R':a.net_R_C1.sum(),'lock1_net_R':b.net_R_C1.sum(),'delta_R':b.net_R_C1.sum()-a.net_R_C1.sum()})
 return pd.DataFrame(rows)

def decomposition(paths):
 z=match(paths); z['delta_R']=z.net_R_C1_lock1-z.net_R_C1_full
 def cls(r):
  if np.isclose(r.delta_R,0,atol=1e-9): return 'UNCHANGED'
  if r.net_R_C1_full>0 and r.net_R_C1_lock1>r.net_R_C1_full:return 'PROTECTED_WIN'
  if r.net_R_C1_full>0 and r.net_R_C1_lock1<r.net_R_C1_full:return 'CUT_WINNER'
  if r.net_R_C1_full<=0 and r.net_R_C1_lock1>r.net_R_C1_full and r.reached_2r_full:return 'AVOIDED_GIVEBACK_TO_LOSS'
  if r.net_R_C1_full<=0 and r.net_R_C1_lock1<=0 and r.net_R_C1_lock1>r.net_R_C1_full:return 'IMPROVED_NONPOSITIVE'
  return 'OTHER'
 z['classification']=z.apply(cls,axis=1); rows=[]
 for dims in [[],['lifecycle'],['instrument'],['direction'],['lifecycle','instrument','direction']]:
  groups=[((),z)] if not dims else z.groupby(dims,dropna=False)
  for key,g in groups:
   key=(key,) if dims and not isinstance(key,tuple) else key; base={'scope':'ALL' if not dims else '+'.join(dims),'lifecycle':'ALL','instrument':'ALL','direction':'ALL'}; base.update(dict(zip(dims,key)))
   for c in ['PROTECTED_WIN','CUT_WINNER','AVOIDED_GIVEBACK_TO_LOSS','IMPROVED_NONPOSITIVE','UNCHANGED','OTHER']:
    q=g[g.classification==c]; rows.append({**base,'classification':c,'count':len(q),'canonical_R':q.net_R_C1_full.sum(),'lock1_R':q.net_R_C1_lock1.sum(),'delta_R':q.delta_R.sum()})
 return pd.DataFrame(rows)

def anatomy(full):
 rows=[]
 for (sym,life),g in full[full.reached_2r].groupby(['instrument','lifecycle']):
  v=g.net_R_C1; give=g.causal_mfe_R-v
  rows.append({'instrument':sym,'lifecycle':life,'trades_reaching_2r':len(g),'final_positive_trades':int((v>0).sum()),'final_nonpositive_trades':int((v<=0).sum()),'final_below_1r':int((v<1).sum()),'final_1r_to_2r':int(((v>=1)&(v<2)).sum()),'final_at_least_2r':int((v>=2).sum()),'mean_final_R':v.mean(),'median_final_R':v.median(),'total_R':v.sum(),'mean_giveback_R':give.mean(),'maximum_giveback_R':give.max()})
 return pd.DataFrame(rows)

def giveback(paths):
 z=match(paths); z=z[z.reached_2r_full].copy(); z['full_giveback_R']=z.causal_mfe_R_full-z.net_R_C1_full; z['lock1_giveback_R']=z.causal_mfe_R_full-z.net_R_C1_lock1; z['delta_giveback_R']=z.full_giveback_R-z.lock1_giveback_R
 return z[['lifecycle','instrument','direction','entry_time','causal_mfe_R_full','net_R_C1_full','net_R_C1_lock1','full_giveback_R','lock1_giveback_R','delta_giveback_R']].rename(columns={'causal_mfe_R_full':'causal_MFE_R','net_R_C1_full':'FULL_final_R','net_R_C1_lock1':'LOCK1_final_R'})

def funnel(test):
 rows=[]
 for dims in [['instrument','lifecycle','direction'],[]]:
  groups=test.groupby(dims) if dims else [((),test)]
  for key,g in groups:
   key=(key,) if dims and not isinstance(key,tuple) else key; base={'instrument':'ALL','lifecycle':'ALL','direction':'ALL'}; base.update(dict(zip(dims,key))); reached=g.reached_2r.astype(bool); binding=g.lock1_became_binding.astype(bool)
   rows.append({**base,'total_trades':len(g),'trades_reaching_2r':int(reached.sum()),'plus2r_reach_rate':reached.mean(),'trades_lock1_became_binding':int(binding.sum()),'binding_rate_among_plus2r':binding.sum()/reached.sum() if reached.sum() else 0,'trades_exiting_LOCK1_STOP':int((g.exit_reason=='LOCK1_STOP').sum()),'resulting_net_R':g.net_R_C1.sum()})
 return pd.DataFrame(rows)

def exit_reasons(paths):
 return pd.DataFrame([{'path':p,'lifecycle':life,'exit_reason':reason,'trades':len(g),'net_R':g.net_R_C1.sum(),'expectancy_R':g.net_R_C1.mean(),'average_holding_hours':(pd.to_datetime(g.exit_time,utc=True)-pd.to_datetime(g.entry_time,utc=True)).dt.total_seconds().mean()/3600} for p,x in paths.items() for (life,reason),g in x.groupby(['lifecycle','exit_reason'])])

def authenticate(data_root):
 source=json.loads((HERE.parent/'stage5_structural_validation/trail1/manifest_trail1.json').read_text())['source_hashes']; hs={k:v for k,v in source.items() if k.endswith('_H1.csv') and any(f'/{sym}/' in k for sym in SYMBOLS)}
 dirs={f'stage6_{n}_hashes':{p.name:sha(p) for p in (HERE.parent/d).iterdir() if p.is_file()} for n,d in [('1','stage6_session_10_21_causal'),('2','stage6_one_bar_breakout_confirmation'),('3','stage6_exit_on_opposite_regime')]}
 checks={'starting_main':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==STARTING_MAIN_SHA,'strategy_sha':sha(ROOT/'TradingSystemLab/strategies/trend/T3_MTF_Trend.py')==T3_SHA,'parameter_sha':set(frozen.lifecycle_registry().query("lifecycle!='baseline'").strategy_parameter_hash)=={PARAM_SHA},'four_source_hashes':len(hs)==4 and all(sha(Path(data_root)/p)==h for p,h in hs.items()),'old_stage6_sha':sha(OLD_STAGE6)==OLD_STAGE6_SHA}
 if not all(checks.values()): raise RuntimeError(f'AUTHENTICATION_FAILED:{checks}')
 return {'checks':checks,'source_hashes':hs,'benchmark_hashes':{p.name:sha(p) for p in BENCH.iterdir() if p.is_file()},**dirs}

def _report(a,decision,hashes,auth):
 y=a['yearly_metrics.csv']; c=a['lock1_decision_comparison.csv']; act=a['lock1_activation_events.csv']; fun=a['lock1_funnel.csv']; anat=a['plus2r_trade_anatomy.csv']; dec=a['lock1_trade_decomposition.csv']; give=a['lock1_giveback_comparison.csv']
 tab=c[['path','annual_floor_R','worst_12M_R','worst_6M_R','worst_DD_R','minimum_recovery_factor','positive_month_share','chronological_net_R','all_annual_gates_pass']].copy()
 for life,yr,name in views(): tab[name]=tab.path.map(lambda path,life=life,yr=yr:float(y.query('path==@path and lifecycle==@life and year==@yr').net_R.iloc[0]))
 tab=tab.rename(columns={'path':'Path','annual_floor_R':'Annual Floor','worst_12M_R':'Worst 12M','worst_6M_R':'Worst 6M','worst_DD_R':'Worst DD','minimum_recovery_factor':'Min Recovery','positive_month_share':'Positive Months','chronological_net_R':'Chronological R','all_annual_gates_pass':'Gate'})[['Path','Baseline 2023','Baseline 2024','WF 2024','OOS 2025','OOS 2026 YTD','Annual Floor','Worst 12M','Worst 6M','Worst DD','Min Recovery','Positive Months','Chronological R','Gate']]
 lines=['# Final Stage 6.4 LOCK1_AFTER_2R Report','',tab.to_markdown(index=False,floatfmt='.6f'),'','## Provenance',f'- Starting main `{STARTING_MAIN_SHA}`; frozen T3 `{T3_SHA}`; parameters `{PARAM_SHA}`.',f'- FULL hash `{hashes[PATHS[0]][0]}`; LOCK1 hash `{hashes[PATHS[1]][0]}`; both isolated replay pairs match.','', '## Methodology authority and frozen candidate','Original v1 H1 methodology applied independently to the v3 perpetual research generation. Frozen `T3_H1_candidate_v3` / `T3-H1-4e73cdb77246`; C1 tick 0.001. No search.','', '## Exact LOCK1 rule and next-event proof','At entry, original risk is frozen as `abs(entry - initial_stop)`. A surviving completed event whose causal high/low reaches entry ±2R arms the lock. The current event used its pre-event stop; only the next event snapshots armed=true and applies LONG `max(canonical, entry+1R)` or SHORT `min(canonical, entry-1R)`. Canonical trailing and gap fills remain intact, and activation is persistent. This is neither a TP nor a same-event exit. SESSION, ONE_BAR, and opposite-regime rules are absent.','']
 sections=[('FULL vs LOCK1 yearly summary','yearly_metrics.csv'),('Complete monthly FULL and LOCK1 tables','monthly_metrics.csv'),('Instrument × month matrices','instrument_monthly_metrics.csv'),('Instrument × year','instrument_yearly_metrics.csv'),('Direction results','direction_metrics.csv'),('LOCK1 funnel','lock1_funnel.csv'),('Activation events and next-event proof','lock1_activation_events.csv'),('+2R trade anatomy','plus2r_trade_anatomy.csv'),('Protected-win / cut-winner decomposition','lock1_trade_decomposition.csv'),('Giveback comparison','lock1_giveback_comparison.csv'),('Exit-reason comparison','exit_reason_comparison.csv'),('Holding-duration comparison','holding_bucket_comparison.csv'),('Trade-path reconciliation','full_vs_lock1_trade_path_reconciliation.csv'),('Rolling 3/6/12M','rolling_stability.csv'),('DD/recovery','lifecycle_metrics.csv'),('Monthly concentration','monthly_concentration.csv'),('Annual hard gates and frozen hierarchy','lock1_decision_comparison.csv')]
 for title,name in sections: lines += [f'## {title}','',a[name].to_markdown(index=False,floatfmt='.6f'),'']
 allfun=fun.query("instrument=='ALL'").iloc[0]; allanat=anat[['final_nonpositive_trades','final_below_1r']].sum(); alldec=dec.query("scope=='ALL'")
 lines += ['## Historical A–F monthly appendix','',pd.read_csv(BENCH/'basket_monthly_metrics.csv').to_markdown(index=False,floatfmt='.6f'),'','## Prior structural status','- Stage 6.1 `SESSION_10_21` → ADMITTED (unchanged).','- Stage 6.2 `ONE_BAR_BREAKOUT_CONFIRMATION` → REJECTED (unchanged).','- Stage 6.3 `EXIT_ON_OPPOSITE_REGIME` → NO MATERIAL DIFFERENCE / NOT ADMITTED (unchanged).','','## Direct answers and computed decision',f'- +2R trades `{int(allfun.trades_reaching_2r)}`; binding `{int(allfun.trades_lock1_became_binding)}`; LOCK1_STOP `{int(allfun.trades_exiting_LOCK1_STOP)}`.',f'- FULL +2R ending <=0 `{int(allanat.final_nonpositive_trades)}`; below +1R `{int(allanat.final_below_1r)}`.',f'- Matched +2R giveback reduction `{give.delta_giveback_R.sum():.6f} R`.']
 for cls in ['PROTECTED_WIN','CUT_WINNER']:
  q=alldec[alldec.classification==cls].iloc[0]; lines.append(f'- {cls}: `{int(q["count"])}`; delta `{q.delta_R:+.6f} R`.')
 for life,yr,label in views():
  f=float(y.query('path==@PATHS[0] and lifecycle==@life and year==@yr').net_R.iloc[0]); t=float(y.query('path==@PATHS[1] and lifecycle==@life and year==@yr').net_R.iloc[0]); lines.append(f'- {label}: FULL `{f:.6f}`, LOCK1 `{t:.6f}`, delta `{t-f:+.6f} R`.')
 lines += [f'- Frozen hierarchy selects `{c.preferred_path.iloc[0]}`. Independent decision: **`{decision}`**.',f'- LOCK1 is {"admitted" if decision.endswith("ADMIT_TO_STRUCTURAL_STACK") else "not admitted"} to Structural Stack.','- Retrospective evidence only: 2025–2026 are revealed, 2026 is partial, and WF remains separate. Stage 7 was not executed.']
 return '\n'.join(lines)+'\n'

def execute(data_root,output_dir=HERE):
 auth=authenticate(data_root); output_dir=Path(output_dir); paths={}; hashes={}; activations=None
 for path in PATHS:
  a,e=replay_all(data_root,path,True); b,_=replay_all(data_root,path,True); hashes[path]=[frame_sha(a),frame_sha(b)]
  if hashes[path][0]!=hashes[path][1]: raise RuntimeError('NONDETERMINISTIC_REPLAY')
  paths[path]=a
  if path==PATHS[1]: activations=e
 mon=monthly(paths); year=yearly(paths,mon); inst=instrument_yearly(paths); roll=rolling(mon); conc=concentration(mon); life=pd.DataFrame([{'path':p,'lifecycle':l,**metrics(g)} for p,x in paths.items() for l,g in x.groupby('lifecycle')]); direction=pd.DataFrame([{'path':p,'lifecycle':l,'direction':d,**metrics(g)} for p,x in paths.items() for (l,d),g in x.groupby(['lifecycle','direction'])]); comp,decision=comparison(year,life,roll,mon,conc)
 registry=pd.DataFrame([{'path':p,'strategy':'T3_H1_candidate_v3','configuration':'T3-H1-4e73cdb77246','parameter_sha':PARAM_SHA,'strategy_sha':T3_SHA,'instruments':'+'.join(SYMBOLS),'timeframe':'H1','cost_contract':'CORRECTED_SINGLE_C1','tick':TICK,'lock1_enabled':p==PATHS[1],'trigger_R':2,'floor_R':1,'next_event_only':True,'session_restriction':False,'one_bar_confirmation':False,'opposite_regime_exit':False} for p in PATHS])
 artifacts={'lock1_registry.csv':registry,'full_canonical_trades.csv':paths[PATHS[0]],'lock1_after_2r_trades.csv':paths[PATHS[1]],'full_vs_lock1_trade_path_reconciliation.csv':reconciliation(paths),'lock1_activation_events.csv':activations,'lock1_funnel.csv':funnel(paths[PATHS[1]]),'lock1_trade_decomposition.csv':decomposition(paths),'plus2r_trade_anatomy.csv':anatomy(paths[PATHS[0]]),'lock1_giveback_comparison.csv':giveback(paths),'exit_reason_comparison.csv':exit_reasons(paths),'holding_bucket_comparison.csv':holding_buckets(paths),'yearly_metrics.csv':year,'monthly_metrics.csv':mon.drop(columns=[f'{sym}_net_R' for sym in SYMBOLS]),'instrument_yearly_metrics.csv':inst,'instrument_monthly_metrics.csv':mon[['path','lifecycle','year','month',*[f'{sym}_net_R' for sym in SYMBOLS],'net_R']].rename(columns={'net_R':'portfolio_total_R'}),'direction_metrics.csv':direction,'rolling_stability.csv':roll,'lifecycle_metrics.csv':life,'monthly_concentration.csv':conc,'lock1_decision_comparison.csv':comp}
 output_dir.mkdir(parents=True,exist_ok=True)
 for n,f in artifacts.items(): f.to_csv(output_dir/n,index=False,lineterminator='\n',float_format='%.12g')
 (output_dir/'FINAL_LOCK1_AFTER_2R_REPORT.md').write_text(_report(artifacts,decision,hashes,auth))
 manifest={'starting_main_sha':STARTING_MAIN_SHA,'strategy_sha':T3_SHA,'parameter_sha':PARAM_SHA,'source_hashes':auth['source_hashes'],'old_stage6_sha':OLD_STAGE6_SHA,'benchmark_hashes':auth['benchmark_hashes'],'stage6_1_hashes':auth['stage6_1_hashes'],'stage6_2_hashes':auth['stage6_2_hashes'],'stage6_3_hashes':auth['stage6_3_hashes'],'deterministic_replay_hashes':hashes,'decision':decision,'stage7_executed':False}; manifest['artifact_hashes']={n:sha(output_dir/n) for n in [*artifacts,'FINAL_LOCK1_AFTER_2R_REPORT.md']}; (output_dir/'audit_manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n'); return artifacts,manifest

if __name__=='__main__':
 from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation.run_stage5_trail1 import resolve_data_root
 root,_=resolve_data_root(); out=Path(os.environ.get('STAGE6_LOCK1_OUTPUT_DIR',HERE)); _,m=execute(root,out); print(json.dumps({'decision':m['decision'],'hashes':m['deterministic_replay_hashes']},sort_keys=True))
