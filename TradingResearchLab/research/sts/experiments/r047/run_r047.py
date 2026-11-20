#!/usr/bin/env python3
"""TRL-R047: reproducible offline diagnosis of retrospective missed trends and two fixed causal signals.
This program cannot connect to FINAM or alter LIVE. No config optimization.
"""
from __future__ import annotations
import hashlib, json, math, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results';OUT.mkdir(exist_ok=True)
assert hashlib.sha256((ROOT/'FROZEN_PROTOCOL.md').read_bytes()).hexdigest()=="335653853db36305c3dda9f9c97d0d282f55cab872b11a3239bfea2f442d0b06"
DEPS=ROOT/'deps'
CODE=DEPS if (DEPS/'trl_fixed_engine_sts.py').exists() else Path('/mnt/data/sts_work/r038/code')
OHLC=CODE/'sources'/'ohlcv' if (CODE/'sources'/'ohlcv').exists() else Path('/mnt/data/trl_shallow_family/deps/deps/baseline_helpers/sources/ohlcv')
CATALOG=DEPS/'R031_trend_event_catalog.csv' if (DEPS/'R031_trend_event_catalog.csv').exists() else Path('/mnt/data/trl_shallow_family/research_r039/R031_trend_event_catalog.csv')
LEDGER=DEPS/'r045_trade_ledger_135k.csv' if (DEPS/'r045_trade_ledger_135k.csv').exists() else Path('/mnt/data/sts_r045/results/trade_ledger_135k.csv')
for p,h in [(CODE/'trl_fixed_engine_sts.py','b9d896f851bf8c086af7a76f0c1cfee1a8d8f80478a6353a6f07dc0a8aa5aea8'),(CODE/'sources/research_extended.py','c048f96ff9a008ffda874189be12c4176e0fe305b0c410ae74734bfd3f4f657c')]:
 assert hashlib.sha256(p.read_bytes()).hexdigest()==h, f'input hash drift: {p}'
sys.path.insert(0,str(CODE))
import trl_fixed_engine_sts as e
e.base.SRC=OHLC
SYMS=e.SYMS
CANDS=['EARLY_TREND_RESUME','TIGHT_DRIFT_BREAK']
EXITS={'BASE':(None,None),'TP6_PROTECT3':(6,3)}
GO={'OCT2026_PROXY':e.GO_OLD,'NOV2026_PROXY':e.GO_MOEX}
MONTHS=pd.period_range('2023-01','2026-09',freq='M').astype(str)

def add_signals(d):
 d=d.copy();c=d.Close.astype(float);o=d.Open.astype(float);h=d.High.astype(float);l=d.Low.astype(float)
 atr=d.atr.astype(float);e50=d.ema50.astype(float);e200=d.ema200.astype(float)
 base=(d.Datetime.dt.dayofweek<5)&d.mins.between(630,960)&atr.gt(0)&e200.notna()&e50.notna()&d.prior_atr14_d.gt(0)&d.sopen.notna()
 distance_l=c-d.sopen;distance_s=d.sopen-c
 late_l=(distance_l>=0)&(distance_l<=d.prior_atr14_d)
 late_s=(distance_s>=0)&(distance_s<=d.prior_atr14_d)
 breakout6h=h.shift(1).rolling(6,min_periods=6).max()
 breakout6l=l.shift(1).rolling(6,min_periods=6).min()
 longA=(base & (e50>e50.shift(4)) & (e50<=e200) & (c>e50) &
        ((c-c.shift(12))>=1.0*atr)&((c.shift(1)-c.shift(7))>=.45*atr)&
        (c>breakout6h)&((c-o)>=.20*atr)&late_l)
 shortA=(base & (e50<e50.shift(4)) & (e50>=e200) & (c<e50) &
         ((c.shift(12)-c)>=1.0*atr)&((c.shift(7)-c.shift(1))>=.45*atr)&
         (c<breakout6l)&((o-c)>=.20*atr)&late_s)
 d['EARLY_TREND_RESUME']=np.select([longA,shortA],[1,-1],0).astype('int8')
 # 4 immediately previous bars are same trading session as current; prior ranges use closed bars only
 hi4=h.shift(1).rolling(4,min_periods=4).max()
 lo4=l.shift(1).rolling(4,min_periods=4).min()
 prior4range=hi4-lo4
 is4same=d.day.eq(d.day.shift(4))
 drift=c.shift(1)-c.shift(4)
 prevpush=c.shift(1)-c.shift(9)
 trend_l=(e50>e200)&(e50>e50.shift(4))
 trend_s=(e50<e200)&(e50<e50.shift(4))
 longB=(base & is4same & trend_l & (prior4range<=.9*atr) &
        (drift>=.15*atr)&(drift<=.80*atr)&(prevpush>=.9*atr) &
        (c>hi4) & ((c-o)>=.20*atr)&late_l)
 shortB=(base & is4same & trend_s & (prior4range<=.9*atr) &
         (drift<=-.15*atr)&(drift>=-.80*atr)&(prevpush<=-.9*atr) &
         (c<lo4) & ((o-c)>=.20*atr)&late_s)
 d['TIGHT_DRIFT_BREAK']=np.select([longB,shortB],[1,-1],0).astype('int8')
 return d

def retstats(v):
 a=np.asarray(v,float)
 good=a[a>0].sum();bad=-a[a<0].sum();return float(good/bad) if bad>0 else None

def dd(v):
 a=np.r_[0.,np.cumsum(np.asarray(v,float))];return float(np.max(np.maximum.accumulate(a)-a))

def tab_stats(t,col,months=True):
 t=t.sort_values(['exit_dt','symbol']).copy()
 val=t[col].to_numpy(float)
 ms=t.groupby(t.exit_dt.dt.strftime('%Y-%m'))[col].sum().reindex(MONTHS,fill_value=0)
 return dict(trades=len(t),PF=retstats(val),net=float(val.sum()),closed_dd=dd(val),positive_months=int((ms>0).sum()),worst_month=float(ms.min()),PF2025=retstats(t.loc[t.exit_dt.dt.year==2025,col]),net2025=float(t.loc[t.exit_dt.dt.year==2025,col].sum()))

def write_csv(rows,name):pd.DataFrame(rows).to_csv(OUT/name,index=False)

def main():
 cat=pd.read_csv(CATALOG,parse_dates=['start_dt','end_dt','milestone_dt'])
 assert len(cat)==779 and cat.Shallow_entry.eq(0).sum()==366
 missing=cat[cat.Shallow_entry==0].copy()
 missing['year']=missing.start_dt.dt.year
 mods=['Deep','SecondImpulse','H4Break','SESSION_AUCTION_CONTINUATION']
 counts=[]
 for col,vc in [('symbol',missing.symbol),('year',missing.year),('side',missing.side),('shallow_missed_reason',missing.shallow_missed_reason)]:
  for val,num in vc.value_counts().items():counts.append(dict(dimension=col,value=val,episodes=int(num)))
 for key,ct in missing.milestone_shallow_failure_flags.str.split('|').explode().value_counts().items():
  counts.append(dict(dimension='milestone_failure_flag_overlapping',value=key,episodes=int(ct)))
 for m in mods:
  z=missing[missing[m+'_entry']==1]
  counts.append(dict(dimension='existing_alternative_accepted_events',value=m,episodes=len(z)))
  counts.append(dict(dimension='existing_alternative_positive_events',value=m,episodes=int(z[m+'_positive_entry'].sum())))
 covered=missing[[m+'_entry' for m in mods]].sum(axis=1)
 counts.extend([dict(dimension='existing_alternatives',value='no_one_has_entry',episodes=int((covered==0).sum())),dict(dimension='existing_alternatives',value='at_least_one',episodes=int((covered>0).sum()))])
 write_csv(counts,'R031_missed_breakdown.csv')
 for m in mods:
  q=missing.loc[missing[m+'_entry']==1,m+'_full_trade_R'].astype(float)
  print('PRIOR_MODULE',m,'missed episodes with entry',len(q),'sum FULL-R',round(float(q.sum()),3))
 print('BREAKDOWN no raw',missing.shallow_missed_reason.eq('NO_RAW_SHALLOW_PATTERN').sum(),'blocked raw',missing.shallow_missed_reason.eq('RAW_BUT_NOT_ACCEPTED').sum(),'missed_alternatives_none',int((covered==0).sum()),flush=True)

 hist={s:add_signals(e.base.load_one(s)) for s in SYMS}
 print('SOURCED_DATA',{s:dict(rows=len(d),start=str(d.Datetime.iloc[0]),end=str(d.Datetime.iloc[-1]),raw={m:int(d[m].ne(0).sum()) for m in CANDS}) for s,d in hist.items()},flush=True)
 # A few symbol-local time-prefix slices recomputed from all available OHLC and lagged indicators.
 prefix_checks=[]
 for s,d in hist.items():
  active=np.where(d[CANDS].ne(0).any(axis=1))[0]
  ids=set(map(int,active[::max(1,len(active)//30)]));ids.update(np.linspace(201, len(d)-1, 18,dtype=int).tolist())
  for i in sorted(ids):
   short=add_signals(d.iloc[:i+1].drop(columns=CANDS))
   for m in CANDS:
    assert int(short[m].iloc[-1])==int(d[m].iloc[i]),(s,i,m,'PREFIX_NONCAUSAL')
    prefix_checks.append(dict(symbol=s,row=i,mode=m,result='PASS'))
 write_csv(prefix_checks,'prefix_causality_audit.csv')
 # Frozen parities on the same exact original signals, without changing the research engine.
 for title,tp,protect,n,netR in [('BASE',None,None,773,505.4766203967774),('TP6_PROTECT3',6,3,808,499.2860389864027)]:
  arr=e.prepare('SHALLOW_PULLBACK',hist)
  z,meta=e.engine(arr,1,tp=tp,protection=protect)
  assert len(z)==n and math.isclose(sum(x['net_R'] for x in z),netR,rel_tol=0,abs_tol=1e-8),(title,len(z),sum(x['net_R'] for x in z))
  print('FROZEN_CLASSIC_PARITY',title,'PASS',len(z),flush=True)
 baseline=pd.read_csv(LEDGER,parse_dates=['entry_dt','exit_dt'])
 bl=baseline[baseline.scenario=='V20_45_45_45_135000_OCT2026_PROXY_TP6_PROTECT3_x']
 assert math.isclose(bl.net_rub.sum(),381607.6,abs_tol=.06),(bl.net_rub.sum(),'PARITY_FAIL')
 print('V20_CONTROL_PARITY',len(bl),round(float(bl.net_rub.sum()),2),flush=True)
 cash_rows=[];cash_ledger=[];unit_rows=[];coverage=[];corr=[];overlap=[];portfolios=[];years=[];cashstress=[]
 for m in CANDS:
  arr=e.prepare(m,hist)
  for style,(tp,protect) in EXITS.items():
   un,unmeta=e.engine(arr,1,tp=tp,protection=protect)
   q=pd.DataFrame(un)
   if len(q)==0:print('EMPTY_MODEL',m,style);continue
   q['entry_dt']=pd.to_datetime(q.entry_dt);q['exit_dt']=pd.to_datetime(q.exit_dt)
   unit_rows.append(dict(module=m,exit=style,raw=sum(int(d[m].ne(0).sum()) for d in hist.values()),**tab_stats(q,'net_R')))
   for cost in (1,2,4):
    r=q.gross_R.to_numpy(float)-2*cost*q.symbol.map(e.TICKS).to_numpy(float)/q.risk.to_numpy(float)
    unit_rows.append(dict(module=m,exit=style,case='C'+str(cost),trades=len(r),PF=retstats(r),net=float(r.sum())))
   top=q.nlargest(min(5,len(q)),'net_R').index
   u=q.drop(top);unit_rows.append(dict(module=m,exit=style,case='NO_TOP5_R',trades=len(u),PF=retstats(u.net_R),net=float(u.net_R.sum())))
   for sym,sub in q.groupby('symbol'):
    years.append(dict(module=m,exit=style,cut='instrument',value=sym,trades=len(sub),PF_R=retstats(sub.net_R),net_R=float(sub.net_R.sum())))
   for yr,sub in q.groupby(q.exit_dt.dt.year):
    years.append(dict(module=m,exit=style,cut='year',value=yr,trades=len(sub),PF_R=retstats(sub.net_R),net_R=float(sub.net_R.sum())))
   for gg,go in GO.items():
    for bank in (45000,):
     tr,meta=e.engine(arr,2,tp=tp,protection=protect,finance=dict(bank=bank,go=go,no_compound=True,risk_per_trade=.015,max_total_risk=.06))
     v=pd.DataFrame(tr)
     if not len(v):continue
     v['entry_dt']=pd.to_datetime(v.entry_dt);v['exit_dt']=pd.to_datetime(v.exit_dt)
     v['module']=m;v['exit_style']=style;v['go_proxy']=gg;v['bank']=bank;v['net_rub']=v.cash_pnl.astype(float)
     cash_rows.append(dict(module=m,exit=style,go_proxy=gg,bank=bank,raw_signals=sum(int(d[m].ne(0).sum()) for d in hist.values()),rejections=meta,**tab_stats(v,'net_rub')))
     cash_ledger.append(v)
     vv=v.nlargest(min(5,len(v)),'net_rub').index
     z=v.drop(vv);cashstress.append(dict(module=m,exit=style,go_proxy=gg,test='REMOVE_TOP5',net=float(z.net_rub.sum()),PF=retstats(z.net_rub),trades=len(z)))
     for cost in (2,4):
      extra=(cost-1)*2*v.lots.astype(float)*v.symbol.map(e.TICKS).astype(float)*v.symbol.map(e.MULT).astype(float)
      v1=v.net_rub-extra
      cashstress.append(dict(module=m,exit=style,go_proxy=gg,test='C'+str(cost),net=float(v1.sum()),PF=retstats(v1),trades=len(v)))
     # ex-post event coverage using accepted cash trades; do not use these labels as filters.
     relevant=missing
     num=0;posit=0;matches=0;sumR=0.;detail=[]
     for ev in relevant.itertuples():
      x=v[(v.symbol==ev.symbol)&(v.side==ev.side)&(v.entry_dt>=ev.start_dt)&(v.entry_dt<=ev.end_dt)]
      if len(x):
       num+=1;posit+=int((x.net_rub>0).any());matches+=len(x);sumR+=float(x.net_R.sum())
       detail.append(dict(event_id=ev.event_id,module=m,exit=style,go_proxy=gg,number_trades=len(x),event_symbol=ev.symbol,event_start=ev.start_dt,event_end=ev.end_dt,full_life_r=float(x.net_R.sum()),net_rub=float(x.net_rub.sum())))
     coverage.append(dict(module=m,exit=style,go_proxy=gg,missed_episodes=366,covered_events=num,events_with_positive_trade=posit,trades_within_events=matches,trade_full_life_sumR=sumR))
     pd.DataFrame(detail).to_csv(OUT/f'coverage_{m}_{style}_{gg}.csv',index=False)
     if gg=='OCT2026_PROXY' and style=='TP6_PROTECT3':
      sh=bl[bl.module=='SHALLOW'].copy();os=0;active=0
      for row in v.itertuples():
       w=sh[(sh.symbol==row.symbol)&(sh.side==row.side)]
       if ((w.entry_dt<row.exit_dt)&(w.exit_dt>row.entry_dt)).any():os+=1
       if ((w.entry_dt<=row.entry_dt)&(w.exit_dt>row.entry_dt)).any():active+=1
      overlap.append(dict(module=m,n=len(v),same_side_hold_overlap=os,classic_active_at_candidate_entry=active))
      daily_cal=pd.date_range('2023-01-01','2026-09-30',freq='D')
      s1=sh.groupby(sh.exit_dt.dt.normalize()).net_rub.sum().reindex(daily_cal,fill_value=0)
      s2=v.groupby(v.exit_dt.dt.normalize()).net_rub.sum().reindex(daily_cal,fill_value=0)
      bad=s1[s1<0].index
      corr.append(dict(module=m,corr_daily=float(s1.corr(s2)),classic_loss_days=int((s1<0).sum()),candidate_profit_loss_days=float(s2.loc[bad].sum()),candidate_positive_loss_days=int((s2.loc[bad]>0).sum()),classic_losing_months=[x for x in MONTHS if sh.groupby(sh.exit_dt.dt.strftime('%Y-%m')).net_rub.sum().reindex(MONTHS,fill_value=0).get(x,0)<0],candidate_profit_losing_months=None))
      cm=v.groupby(v.exit_dt.dt.strftime('%Y-%m')).net_rub.sum().reindex(MONTHS,fill_value=0)
      lm=sh.groupby(sh.exit_dt.dt.strftime('%Y-%m')).net_rub.sum().reindex(MONTHS,fill_value=0)
      corr[-1]['candidate_profit_losing_months']=round(float(cm[lm<0].sum()),2)
      corr[-1]['candidate_positive_losing_months']=int((cm[lm<0]>0).sum())
 print('UNIT',pd.DataFrame(unit_rows).head(20).to_string(index=False),flush=True)
 write_csv(unit_rows,'standalone_R.csv');write_csv(cash_rows,'standalone_cash.csv');write_csv(years,'year_symbol.csv');write_csv(coverage,'missed_event_coverage.csv');write_csv(cashstress,'cash_cost_outlier_stress.csv');write_csv(overlap,'candidate_vs_classic_overlap.csv');write_csv(corr,'candidate_vs_classic_loss_days.csv')
 cash=pd.concat(cash_ledger,ignore_index=True)
 cash.to_csv(OUT/'candidate_cash_trades.csv',index=False)
 for gg in GO:
  for style in EXITS:
   src=baseline[baseline.scenario==f'V20_45_45_45_135000_{gg}_{style}_x'].copy()
   assert len(src)>0
   for name,models in [ ('V20',['SHALLOW','OBV','INSIDE']),
      ('EARLY_REPL_OBV',['SHALLOW','INSIDE','EARLY_TREND_RESUME']),
      ('EARLY_REPL_INSIDE',['SHALLOW','OBV','EARLY_TREND_RESUME']),
      ('DRIFT_REPL_OBV',['SHALLOW','INSIDE','TIGHT_DRIFT_BREAK']),
      ('DRIFT_REPL_INSIDE',['SHALLOW','OBV','TIGHT_DRIFT_BREAK']),
      ('ALL_SHALLOW_TRIPLE',['SHALLOW','EARLY_TREND_RESUME','TIGHT_DRIFT_BREAK'])]:
    x=src[src.module.isin(models)].copy()
    plus=cash[(cash.go_proxy==gg)&(cash.exit_style==style)&(cash.bank==45000)&cash.module.isin(models)]
    if len(plus):x=pd.concat([x,plus[['module','symbol','entry_dt','exit_dt','side','lots','net_rub','exit_reason']]],ignore_index=True)
    xx=tab_stats(x,'net_rub')
    portfolios.append(dict(model=name,go_proxy=gg,exit=style,bank_total=135000,**xx))
    for yr,g in x.groupby(x.exit_dt.dt.year):
      years.append(dict(module=name,exit=style,cut='portfolio_year',value=yr,go_proxy=gg,trades=len(g),PF_R=None,net_R=None,PF_rub=retstats(g.net_rub),net_rub=float(g.net_rub.sum())))
 write_csv(portfolios,'portfolio_comparison.csv');write_csv(years,'year_symbol.csv')
 print('PORTFOLIOS OCT TP6',pd.DataFrame(portfolios).query('go_proxy=="OCT2026_PROXY" and exit=="TP6_PROTECT3"').to_string(index=False),flush=True)
 # November Oct-Nov live sample remains already seen / not OOS. Exact R046 feature loader format.
 NOV_ROOT=DEPS/'nov_user_csv' if (DEPS/'nov_user_csv').exists() else Path('/mnt/data')
 user_paths={s:next(NOV_ROOT.glob(s+'_261001_261111*.csv')) for s in SYMS}
 import tempfile
 class Eq:
  def __eq__(self,other):return True
 with tempfile.TemporaryDirectory(prefix='r047_nov_') as t:
  tt=Path(t);oldsrc=e.base.SRC
  e.base.SRC=tt
  oldhash=e.base.KNOWN_SHA.copy();oldsign=e.base.KNOWN_SIGNALS.copy()
  for s,p in user_paths.items():
   a=pd.read_csv(p,sep=';');a.columns=['DATE','TIME','Open','High','Low','Close','Volume'];a['Datetime']=pd.to_datetime(a.DATE.astype(str)+a.TIME.astype(str).str.zfill(6),format='%Y%m%d%H%M%S')
   f=tt/f'{s}_M15.csv';a[['Datetime','Open','High','Low','Close','Volume']].to_csv(f,sep=';',index=False)
   e.base.KNOWN_SHA[s]=hashlib.sha256(f.read_bytes()).hexdigest();e.base.KNOWN_SIGNALS[s]=Eq()
  fresh={s:add_signals(e.base.load_one(s)) for s in SYMS}
  e.base.SRC=oldsrc;e.base.KNOWN_SHA.update(oldhash);e.base.KNOWN_SIGNALS.update(oldsign)
 nov=[]
 for s,d in fresh.items():
  a=d[d.Datetime.between('2026-11-09','2026-11-11 08:30')]
  for m in CANDS:
   for row in a.loc[a[m]!=0,['Datetime',m,'Close']].itertuples(index=False):nov.append(dict(symbol=s,module=m,signal_time=row.Datetime,side=int(row[1]),close=float(row.Close)))
 write_csv(nov,'november_discovery_signals.csv')
 print('NOV_DISCOVERY_SIGNALS',pd.DataFrame(nov).groupby(['symbol','module']).size().to_dict() if len(nov) else {},flush=True)
 aud=dict(protocol_sha256=hashlib.sha256((ROOT/'FROZEN_PROTOCOL.md').read_bytes()).hexdigest(),catalog_rows=len(cat),missed_rows=len(missing),prefix_tests=len(prefix_checks),classic_parity='PASS_773_BASE_AND_808_TP6',v20_cash_parity='PASS_381607.6',source_input_hashes={s:e.base.KNOWN_SHA[s] for s in SYMS},analysed_history_not_independent=True,november_discovery_not_oos=True)
 (OUT/'AUDIT.json').write_text(json.dumps(aud,ensure_ascii=False,indent=2),encoding='utf-8')
 print('AUDIT',json.dumps(aud,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
