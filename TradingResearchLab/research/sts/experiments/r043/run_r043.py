#!/usr/bin/env python3
"""TRL-R-043 STS research-only, preregistered MTF ledge and 2-session staircase.
Uses SHA-pinned R039/R038 source and frozen R040 cash baseline. No network/broker.
"""
from __future__ import annotations
import hashlib, json, math, sys, bisect, time
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
assert hashlib.sha256((HERE/'FROZEN_PROTOCOL.md').read_bytes()).hexdigest()== '370149f025542a1c1748546f7a7128cceceb6a8821bbf58a72478c2073cf1e8b'
R038=ROOT/'sts_work/r038/code'
R039=ROOT/'trl_shallow_family/research_r039'
SRC=ROOT/'trl_shallow_family/deps/deps/baseline_helpers/sources'
R041=ROOT/'sts_r041';R042=ROOT/'sts_r042'
for path,sha in [(R038/'trl_fixed_engine.py','ce7468ee72568fbae01be5784e22cd4028833fc804fe0b561ee104d9064fb855'),(SRC/'research_extended.py','c048f96ff9a008ffda874189be12c4176e0fe305b0c410ae74734bfd3f4f657c'),(R039/'run_r039.py','c2726e9b44071de311e16d50eb18ad34f717ad9cb78bc46eea7ba6162bde9c95')]:
 assert hashlib.sha256(path.read_bytes()).hexdigest()==sha, f'Dependency mismatch: {path}'
sys.path[:0]=[str(R038),str(SRC),str(R039),str(R041),str(R042)]
import trl_fixed_engine as eng
import run_r039 as r039
import run_r041 as r041
import run_r042 as r042
r039.re.SRC=SRC/'ohlcv'; eng.base.SRC=SRC/'ohlcv'
MODES=['H1_H4_LEDGE_RECLAIM','MULTI_SESSION_STAIRCASE']
NAMES={'H1_H4_LEDGE_RECLAIM':'MTF_LEDGE','MULTI_SESSION_STAIRCASE':'STAIRCASE'}
MONTHS=list(pd.period_range('2023-01','2026-09',freq='M').astype(str))


def _bars(d, width):
    """Aggregate complete and naturally aligned regular-session blocks only."""
    p=d[d.mins.between(600,1065)].copy()
    p['bucket']=((p.mins-600)//(15*width)).astype(int)
    x=p.groupby(['day','bucket'],sort=True).agg(
      n=('Open','size'),first=('Datetime','min'),last=('Datetime','max'),
      Open=('Open','first'),High=('High','max'),Low=('Low','min'),Close=('Close','last'))
    x=x.reset_index(drop=False)
    min_first=600+x.bucket*width*15
    valid=(x.n==width)&((x['first'].dt.hour*60+x['first'].dt.minute)==min_first)&\
          ((x['last'].dt.hour*60+x['last'].dt.minute)==min_first+(width-1)*15)
    x=x[valid].reset_index(drop=True)
    x['close_time']=x['last']+pd.Timedelta(minutes=15)
    return x

def _h_context(d):
    h1=_bars(d,4);h4=_bars(d,16)
    for x,prefix in [(h1,'H1'),(h4,'H4')]:
      x['ema8']=x.Close.ewm(span=8,adjust=False,min_periods=8).mean()
      x['ema21']=x.Close.ewm(span=21,adjust=False,min_periods=21).mean()
      x['ema5']=x.Close.ewm(span=5,adjust=False,min_periods=5).mean()
      x['ema13']=x.Close.ewm(span=13,adjust=False,min_periods=13).mean()
    pc=h1.Close.shift(1)
    tr=pd.concat([(h1.High-h1.Low),(h1.High-pc).abs(),(h1.Low-pc).abs()],axis=1).max(axis=1)
    h1['atr14']=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    hi3=h1.High.rolling(3,min_periods=3).max()
    lo3=h1.Low.rolling(3,min_periods=3).min()
    a=h1.atr14
    h1['ledge_l']=(h1.ema8>h1.ema21)&(h1.Close<h1.ema8)&(h1.Close>=h1.ema21-.2*a)&\
       ((hi3-h1.Low)>=.4*a)&((hi3-h1.Low)<=2.2*a)
    h1['ledge_s']=(h1.ema8<h1.ema21)&(h1.Close>h1.ema8)&(h1.Close<=h1.ema21+.2*a)&\
       ((h1.High-lo3)>=.4*a)&((h1.High-lo3)<=2.2*a)
    h4['trend_l']=(h4.ema5>h4.ema13)&(h4.ema5>h4.ema5.shift(2))
    h4['trend_s']=(h4.ema5<h4.ema13)&(h4.ema5<h4.ema5.shift(2))
    # A complete H1/H4 block is available at signal decision t+15m. No partial H1/H4.
    decision=d.Datetime+pd.Timedelta(minutes=15)
    left=pd.DataFrame({'decision':decision,'seq':np.arange(len(d))})
    m1=pd.merge_asof(left.sort_values('decision'),h1[['close_time','ledge_l','ledge_s']].sort_values('close_time'),left_on='decision',right_on='close_time',direction='backward')
    m4=pd.merge_asof(left.sort_values('decision'),h4[['close_time','trend_l','trend_s']].sort_values('close_time'),left_on='decision',right_on='close_time',direction='backward')
    return m1.sort_values('seq'), m4.sort_values('seq'), h1, h4

def _d_context(d):
    s=d[d.mins.between(600,1065)].copy()
    x=s.groupby('day',sort=True).agg(n=('Open','size'),first=('Datetime','first'),last=('Datetime','last'),High=('High','max'),Low=('Low','min'),Close=('Close','last')).reset_index()
    valid=(x.n>=24)&((x['first'].dt.hour*60+x['first'].dt.minute)==600)&((x['last'].dt.hour*60+x['last'].dt.minute)==1065)
    x=x[valid].copy().reset_index(drop=True)
    pc=x.Close.shift(1)
    tr=pd.concat([(x.High-x.Low),(x.High-pc).abs(),(x.Low-pc).abs()],axis=1).max(axis=1)
    x['atr14']=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    x['ema8']=x.Close.ewm(span=8,adjust=False,min_periods=8).mean()
    x['ema20']=x.Close.ewm(span=20,adjust=False,min_periods=20).mean()
    a=x.atr14
    impulse=x.Close.shift(2)-x.Close.shift(6)
    drop=x.Close.shift(2)-x.Close
    rise=-drop
    x['stair_l']=(x.ema8>x.ema20)&(x.ema8>x.ema8.shift(2))&\
        (impulse>=.70*a)&(x.Close.shift(1)<x.Close.shift(2))&(x.Close<x.Close.shift(1))&\
        (drop>=.25*a)&(drop<=1.60*a)&(x.Low>=x.Low.shift(1)-.25*a)&(x.Close>=x.ema20-.15*a)
    x['stair_s']=(x.ema8<x.ema20)&(x.ema8<x.ema8.shift(2))&\
        (impulse<=-.70*a)&(x.Close.shift(1)>x.Close.shift(2))&(x.Close>x.Close.shift(1))&\
        (rise>=.25*a)&(rise<=1.60*a)&(x.High<=x.High.shift(1)+.25*a)&(x.Close<=x.ema20+.15*a)
    # Strict prior-day-asof: even if today's session summary exists in the full
    # historical file it is never visible to a signal on that same date.
    left=pd.DataFrame({'day':d.day,'seq':np.arange(len(d))})
    z=pd.merge_asof(left.sort_values('day',kind='stable'),x[['day','stair_l','stair_s','Close','atr14']].rename(columns={'day':'previous_eligible_day','Close':'previous_close','atr14':'previous_atr'}).sort_values('previous_eligible_day'),left_on='day',right_on='previous_eligible_day',direction='backward',allow_exact_matches=False)
    return z.sort_values('seq'),x

def signals(d):
    h1ctx,h4ctx,h1,h4=_h_context(d)
    dailyctx,daily=_d_context(d)
    o,h,l,c,a=(d[k].astype(float) for k in ['Open','High','Low','Close','atr'])
    body=c-o
    valid=(d.Datetime.dt.weekday<5)&d.mins.between(630,960)&a.gt(0)
    same6=d.day.eq(d.day.shift(6))
    upbar=(body>=.20*a);dnbar=(body<=-.20*a)
    high6=h.shift(1).rolling(6,min_periods=6).max()
    low6=l.shift(1).rolling(6,min_periods=6).min()
    h1l=h1ctx.ledge_l.fillna(False).to_numpy(bool);h1s=h1ctx.ledge_s.fillna(False).to_numpy(bool)
    h4l=h4ctx.trend_l.fillna(False).to_numpy(bool);h4s=h4ctx.trend_s.fillna(False).to_numpy(bool)
    ml=(valid&same6&h1l&h4l&(c>high6)&upbar)
    ms=(valid&same6&h1s&h4s&(c<low6)&dnbar)
    d[MODES[0]]=np.select([ml,ms],[1,-1],default=0).astype('int8')
    dl=dailyctx.stair_l.fillna(False).to_numpy(bool);ds=dailyctx.stair_s.fillna(False).to_numpy(bool)
    pcl=dailyctx.previous_close.to_numpy(float);atr=dailyctx.previous_atr.to_numpy(float)
    sl=(valid&same6&dl&np.isfinite(atr)&(c>high6)&(c>pcl+.10*atr)&upbar)
    ss=(valid&same6&ds&np.isfinite(atr)&(c<low6)&(c<pcl-.10*atr)&dnbar)
    d[MODES[1]]=np.select([sl,ss],[1,-1],default=0).astype('int8')
    for m in MODES:
        assert set(d[m].unique()).issubset({-1,0,1})
    return d,{'h1':len(h1),'h4':len(h4),'daily':len(daily)}

def pf(vals):
  v=np.asarray(vals,float);neg=-v[v<0].sum();return float(v[v>0].sum()/neg) if neg>1e-9 else (float('nan') if len(v)==0 else None)

def stats(trades):
  if len(trades)==0:return dict(trades=0,net_rub=0.,pf_rub=None,closed_dd_rub=0.,positive_months=0,pf2025=None,worst_month=0,net2025=0)
  t=trades.copy().sort_values(['exit_dt','robot','symbol'])
  pnl=t.cash_pnl.to_numpy(float);cum=np.r_[0.,pnl.cumsum()]
  mt=t.groupby(t.exit_dt.dt.strftime('%Y-%m')).cash_pnl.sum().reindex(MONTHS,fill_value=0.)
  p25=t.loc[t.exit_dt.dt.year==2025,'cash_pnl'].to_numpy(float)
  return dict(trades=len(t),net_rub=round(float(pnl.sum()),2),pf_rub=round(pf(pnl),5) if pf(pnl) is not None else None,closed_dd_rub=round(float((np.maximum.accumulate(cum)-cum).max()),2),positive_months=int((mt>0).sum()),negative_months=int((mt<0).sum()),pf2025=round(pf(p25),5) if pf(p25) is not None else None,worst_month=round(float(mt.min()),2),net2025=round(float(p25.sum()),2))

def prep(rows,name,bank,go_name,ex):
  if not rows:return pd.DataFrame(columns=['robot','cash_pnl','entry_dt','exit_dt','symbol','side','net_R'])
  t=pd.DataFrame(rows);t['robot']=name;t['entry_dt']=pd.to_datetime(t.entry_dt);t['exit_dt']=pd.to_datetime(t.exit_dt);t['bank_per_robot']=bank;t['go_proxy']=go_name;t['exit_type']=ex
  return t

def overlap(candidate,reference):
  result=dict(same_side_overlap=0,reference_active_at_entry=0,opposite_side_overlap=0)
  for r in candidate.itertuples():
    q=reference[reference.symbol==r.symbol]
    a=q[q.side==r.side];b=q[q.side==-r.side]
    if ((a.entry_dt<r.exit_dt)&(a.exit_dt>r.entry_dt)).any():result['same_side_overlap']+=1
    if ((a.entry_dt<=r.entry_dt)&(a.exit_dt>=r.entry_dt)).any():result['reference_active_at_entry']+=1
    if ((b.entry_dt<r.exit_dt)&(b.exit_dt>r.entry_dt)).any():result['opposite_side_overlap']+=1
  return result

def gate_replay(arr,reference,bank,go,tp,protect):
  ints={}
  for (sym,side),g in reference.groupby(['symbol','side']):
    ints[(sym,side)]=(g.entry_dt.astype('int64').to_numpy(),g.exit_dt.astype('int64').to_numpy())
  def active(sym,side,ts):
    if (sym,side) not in ints:return False
    en,ex=ints[(sym,side)];return bool(np.any((en<=ts)&(ex>=ts)))
  return eng.engine(arr,2,tp=tp,protection=protect,finance={'bank':bank,'go':go,'no_compound':True},cross_gate=active)

def write(name,rows):
  pd.DataFrame(rows).to_csv(HERE/'results'/f'{name}.csv',index=False)

def main():
  t0=time.monotonic();raw={s:r039.signal_dataframe(r039.re.load_one(s).copy()) for s in eng.SYMS}
  data={};ct={}
  for s,df in raw.items():
    data[s],ct[s]=signals(df)
  print('AGGREGATE_COUNTS',json.dumps(ct),flush=True)
  print('RAW_SIGNALS',json.dumps({m:{s:int(data[s][m].ne(0).sum()) for s in eng.SYMS} for m in MODES}),flush=True)
  # Frozen parity expected for Classic Shallow, BASE and TP6 protection.
  a={m:eng.prepare(m,data) for m in MODES+['SHALLOW_PULLBACK','MICRO_SHALLOW']}
  for ex,tp,prot,n,rr in [('BASE',None,None,773,505.4766203967774),('TP6_PROTECT3',6,3,808,499.2860389864027)]:
    tr,_=eng.engine(a['SHALLOW_PULLBACK'],1,tp=tp,protection=prot)
    z=sum(x['net_R'] for x in tr)
    assert len(tr)==n and math.isclose(z,rr,abs_tol=1e-8),(ex,len(tr),z)
    print('CLASSIC_PARITY_PASS',ex,n,flush=True)
  # Deterministic causal prefix checks on all four symbols, different dates.
  for s,df in raw.items():
    for frac in (.41,.72,.89):
      n=int(len(df)*frac)
      f,_=signals(df.iloc[:n+1].copy())
      for m in MODES: assert int(f[m].iloc[-1])==int(data[s][m].iloc[n]),(s,m,n)
  print('PREFIX_INVARIANCE_PASS',flush=True)
  baseline=pd.read_csv(ROOT/'STS_R040_results/cash_trades.csv',parse_dates=['entry_dt','exit_dt'],low_memory=False)
  baseline=baseline[baseline.architecture=='V20']
  standalone=[];annual_R=[];by_symbol_R=[];stress=[];results=[];years=[];months=[];modules=[];metadata=[];diagnostics=[];gates=[]
  for m in MODES:
    for ex,tp,prot in [('BASE',None,None),('TP6_PROTECT3',6,3)]:
      tr,meta=eng.engine(a[m],2,tp=tp,protection=prot)
      v=pd.DataFrame(tr); net=v.net_R.to_numpy(float) if len(v) else np.empty(0)
      cm=np.r_[0.,np.cumsum(net)]
      standalone.append(dict(module=NAMES[m],exit_type=ex,trades=len(v),pf_R=round(pf(net),6) if pf(net) is not None else None,net_R=round(float(net.sum()),6),closed_dd_R=round(float((np.maximum.accumulate(cm)-cm).max()),3),unfinished=meta.get('unclosed',0)))
      if len(v):
        v['exit_dt']=pd.to_datetime(v.exit_dt)
        for y in (2023,2024,2025,2026):
          z=v[v.exit_dt.dt.year==y].net_R.to_numpy(float)
          annual_R.append(dict(module=NAMES[m],exit_type=ex,year=y,trades=len(z),pf_R=round(pf(z),5) if pf(z) is not None else None,net_R=round(float(z.sum()),3)))
        for s in eng.SYMS:
          z=v[v.symbol==s].net_R.to_numpy(float)
          by_symbol_R.append(dict(module=NAMES[m],exit_type=ex,symbol=s,trades=len(z),pf_R=round(pf(z),5) if pf(z) is not None else None,net_R=round(float(z.sum()),3)))
        for cost in (1,2,4):
          x=v.gross_R.to_numpy(float)-2*cost*v.symbol.map(eng.TICKS).to_numpy(float)/v.risk.to_numpy(float)
          stress.append(dict(module=NAMES[m],exit_type=ex,cost_case=f'C{cost}',trades=len(x),pf_R=round(pf(x),5),net_R=round(float(x.sum()),3)))
        if len(v)>5:
          x=np.delete(net,np.argsort(net)[-5:]);stress.append(dict(module=NAMES[m],exit_type=ex,cost_case='REMOVE_TOP5',trades=len(x),pf_R=round(pf(x),5) if pf(x) is not None else None,net_R=round(float(x.sum()),3)))
  for bank in (45000,500000,1000000):
    for goname,go in [('OCT2026_PROXY',eng.GO_OLD),('NOV2026_PROXY',eng.GO_MOEX)]:
      for ex,tp,pro in [('BASE',None,None),('TP6_PROTECT3',6,3)]:
        ref={name:baseline[(baseline.bank_per_robot==bank)&(baseline.go_proxy==goname)&(baseline.exit_type==ex)&(baseline.robot==name)].copy() for name in ('CLASSIC','OBV','INSIDE')}
        if any(len(x)==0 for x in ref.values()):raise ValueError('Baseline missing')
        new={}
        for m in MODES:
          tr,meta=eng.engine(a[m],2,tp=tp,protection=pro,finance={'bank':bank,'go':go,'no_compound':True})
          new[NAMES[m]]=prep(tr,NAMES[m],bank,goname,ex)
          metadata.append(dict(module=NAMES[m],bank_per_robot=bank,go_proxy=goname,exit_type=ex,**meta))
          modules.append(new[NAMES[m]])
        specs={'V20':['CLASSIC','OBV','INSIDE'],
               'MTF_REPL_OBV':['CLASSIC','MTF_LEDGE','INSIDE'],
               'MTF_REPL_INSIDE':['CLASSIC','OBV','MTF_LEDGE'],
               'STAIR_REPL_OBV':['CLASSIC','STAIRCASE','INSIDE'],
               'STAIR_REPL_INSIDE':['CLASSIC','OBV','STAIRCASE'],
               'STS_MTF_STAIR':['CLASSIC','MTF_LEDGE','STAIRCASE']}
        for title,names in specs.items():
          dd={**ref,**new}; z=pd.concat([dd[x] for x in names],ignore_index=True)
          s=stats(z); results.append(dict(model=title,bank_per_robot=bank,total_bank=3*bank,go_proxy=goname,exit_type=ex,**s))
          for y in (2023,2024,2025,2026):
            yr=z[z.exit_dt.dt.year==y]
            sy=stats(yr); years.append(dict(model=title,bank_per_robot=bank,total_bank=3*bank,go_proxy=goname,exit_type=ex,year=y,**sy))
          mon=z.groupby(z.exit_dt.dt.strftime('%Y-%m')).cash_pnl.sum().reindex(MONTHS,fill_value=0.)
          for month,pl in mon.items():months.append(dict(model=title,bank_per_robot=bank,total_bank=3*bank,go_proxy=goname,exit_type=ex,month=month,net_rub=round(float(pl),2)))
        if bank==45000 and goname=='OCT2026_PROXY' and ex=='TP6_PROTECT3':
          b=stats(pd.concat(list(ref.values()),ignore_index=True))
          assert math.isclose(b['net_rub'],381607.6,abs_tol=.01) and math.isclose(b['pf_rub'],1.844655,abs_tol=.00001)
          micro_tr,_=eng.engine(a['MICRO_SHALLOW'],2,tp=tp,protection=pro,finance={'bank':bank,'go':go,'no_compound':True})
          micro=prep(micro_tr,'MICRO',bank,goname,ex)
          for m in MODES:
            name=NAMES[m];t=new[name]; c=ref['CLASSIC']
            dt=t.groupby(t.exit_dt.dt.normalize()).cash_pnl.sum()
            cr=c.groupby(c.exit_dt.dt.normalize()).cash_pnl.sum()
            union=dt.index.union(cr.index)
            xd=dt.reindex(union,fill_value=0.);yd=cr.reindex(union,fill_value=0.)
            ddays=yd<0
            dmonths=t.groupby(t.exit_dt.dt.strftime('%Y-%m')).cash_pnl.sum().reindex(MONTHS,fill_value=0.)
            cmonths=c.groupby(c.exit_dt.dt.strftime('%Y-%m')).cash_pnl.sum().reindex(MONTHS,fill_value=0.)
            weak=cmonths<0
            diagnostics.append(dict(module=name,**stats(t),**{'overlap_classic_'+k:v for k,v in overlap(t,c).items()},**{'overlap_micro_'+k:v for k,v in overlap(t,micro).items()},classic_down_days=int(ddays.sum()),pnl_classic_down_days=round(float(xd[ddays].sum()),2),classic_down_months=int(weak.sum()),pnl_classic_down_months=round(float(dmonths[weak].sum()),2),daily_corr=round(float(xd.corr(yd)),5)))
            gt,gmeta=gate_replay(a[m],c,bank,go,tp,pro)
            gates.append(dict(module=name,**stats(prep(gt,name,bank,goname,ex)),blocked=gmeta.get('cross_rejected',0)))
        print('BATCH_DONE',bank,goname,ex,'secs',round(time.monotonic()-t0,2),flush=True)
  for n,rows in {'standalone_R':standalone,'years_R':annual_R,'symbols_R':by_symbol_R,'cost_stress_R':stress,'portfolio_cash':results,'portfolio_years':years,'portfolio_months':months,'candidate_cash_metadata':metadata,'candidate_diagnostics':diagnostics,'causal_gate':gates}.items():write(n,rows)
  if modules:pd.concat(modules,ignore_index=True).to_csv(HERE/'results/candidate_cash_trades.csv',index=False)
  digest={'protocol_sha256':hashlib.sha256((HERE/'FROZEN_PROTOCOL.md').read_bytes()).hexdigest(),
     'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
     'source_engine_sha256':hashlib.sha256((R038/'trl_fixed_engine.py').read_bytes()).hexdigest(),
     'source_signal_sha256':hashlib.sha256((R039/'run_r039.py').read_bytes()).hexdigest(),
     'finished_seconds':round(time.monotonic()-t0,2),'classic_parity_pass':True,'prefix_pass':True}
  (HERE/'results/AUDIT.json').write_text(json.dumps(digest,ensure_ascii=False,indent=2),encoding='utf8')
  print('R043_AUDIT_PASS',json.dumps(digest,ensure_ascii=False),flush=True)
  print('STANDALONE',pd.DataFrame(standalone).to_string(index=False),flush=True)
  print('MAIN',pd.DataFrame(results).query("total_bank==135000 and go_proxy=='OCT2026_PROXY' and exit_type=='TP6_PROTECT3'").to_string(index=False),flush=True)
  print('DIAGNOSTICS',pd.DataFrame(diagnostics).to_string(index=False),flush=True)
  print('GATES',pd.DataFrame(gates).to_string(index=False),flush=True)

if __name__=='__main__':main()