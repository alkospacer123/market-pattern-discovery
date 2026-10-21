"""Pre-specified structural M15 trend entries: different from ORB/Donchian.
DO NOT use reviewed 2025+ results to adjust models. Frozen rules and all output exploratory.
Position lifetime at most two *observed* 09:00 sessions, next-adjacent Open,
stop first incl entry, 1 grid-tick per side hypothetical costs.
"""
import hashlib,json,math,sys
from pathlib import Path
import pandas as pd,numpy as np
from numba import njit
ROOT=Path('/mnt/data/marketdata_m15'); OUT=Path('/mnt/data/newtrend_v3')
SYMS=['USDRUBF','CNYRUBF','GLDRUBF','IMOEXF'];TICKS={'USDRUBF':.01,'CNYRUBF':.001,'GLDRUBF':.1,'IMOEXF':.5}
MODES=['VWAP_RECLAIM','NR7_INSIDE_BREAK','BB_KC_SQUEEZE','ADX_DI_TURN','H1_SWING_BREAK','THREE_BAR_PULLBACK','REGRESSION_RECLAIM','EMA20_60_CROSS','VWAP_OPEN_DRIVE']

@njit
def execute(ts,dayidx,op,hi,lo,cl,atr,signal,tick,stopmult=2.,step_ns=900000000000):
 out=[];pending=-1;side=0;pos=False;entry=0.;initial=0.;risk=0.;startidx=0;entryday=0;sigat=0;usedday=-1
 for i in range(len(op)):
  if pos:
   exitval=0.;reason=0
   if dayidx[i]-entryday>=2:exitval=op[i];reason=3
   elif (side==1 and op[i]<=initial+tick*1e-7) or (side==-1 and op[i]>=initial-tick*1e-7):exitval=op[i];reason=2
   elif (side==1 and lo[i]<=initial+tick*1e-7) or (side==-1 and hi[i]>=initial-tick*1e-7):exitval=initial;reason=1
   if reason:
    gross=side*(exitval-entry)/risk
    out.append((sigat,startidx,i,side,entry,exitval,initial,risk,gross,gross-2*tick/risk,reason));pos=False
  if pending>=0:
   if ts[i]==ts[pending]+step_ns and not pos and usedday!=dayidx[i]:
    at=pending;entry=op[i];side=int(signal[at]);dist=stopmult*atr[at]
    if np.isfinite(dist) and dist>0:
     target=entry-side*dist
     initial=(np.floor(target/tick+1e-9) if side==1 else np.ceil(target/tick-1e-9))*tick
     risk=abs(entry-initial)
     if risk>0:
      sigat=at;startidx=i;entryday=dayidx[i];usedday=dayidx[i];pos=True
      if (side==1 and lo[i]<=initial+tick*1e-7) or (side==-1 and hi[i]>=initial-tick*1e-7):
       out.append((at,i,i,side,entry,initial,initial,risk,-1.,-1.-2*tick/risk,4));pos=False
   pending=-1
  if signal[i]!=0 and not pos and usedday!=dayidx[i] and np.isfinite(atr[i]) and atr[i]>0:pending=i
 return out,int(pos)

def prep(sym):
 d=pd.read_csv(ROOT/f'{sym}_M15.csv',sep=';',parse_dates=['Datetime']);assert d.Datetime.is_monotonic_increasing and not d.Datetime.duplicated().any()
 assert (d.High>=d[['Open','Low','Close']].max(axis=1)).all()
 d['day']=(d.Datetime-pd.Timedelta(hours=9)).dt.normalize();d['mins']=d.Datetime.dt.hour*60+d.Datetime.dt.minute
 o,h,l,c,v=[d[k].astype(float) for k in ['Open','High','Low','Close','Volume']]
 d['ema20']=c.ewm(span=20,adjust=False,min_periods=20).mean();d['ema50']=c.ewm(span=50,adjust=False,min_periods=50).mean();d['ema200']=c.ewm(span=200,adjust=False,min_periods=200).mean();d['ema60']=c.ewm(span=60,adjust=False,min_periods=60).mean()
 prev=c.shift(1);tr=pd.concat([h-l,(h-prev).abs(),(l-prev).abs()],axis=1).max(axis=1)
 d['atr']=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean();atr=d.atr
 # directional trend from EMA50/200 and completed 4-bar slope
 long=(d.ema50>d.ema200)&(d.ema50>d.ema50.shift(4));short=(d.ema50<d.ema200)&(d.ema50<d.ema50.shift(4))
 eligible=(d.mins>=600)&(d.mins<1020)
 pc=c.shift(1);ph=h.shift(1);pl=l.shift(1)
 # Session anchored VWAP with no future known: group cumulative typical*volume / volume, zero-volume session excludes
 typical=(h+l+c)/3;vol=v.clip(lower=0)
 cv=vol.groupby(d.day).cumsum();tvol=(typical*vol).groupby(d.day).cumsum()
 d['vwap']=tvol/cv.replace(0,np.nan);pvwap=d.vwap.shift(1)
 same_prev=(d.day==d.day.shift(1));gap_prev=(d.Datetime.diff()==pd.Timedelta(minutes=15))
 # VWAP_RECLAIM: crossing session VWAP after going below/above, trend direction and candle body affirm
 vl=eligible&same_prev&gap_prev&(pc<=pvwap)&(c>d.vwap)&(c>o)&long&(d.mins>=660)
 vs=eligible&same_prev&gap_prev&(pc>=pvwap)&(c<d.vwap)&(c<o)&short&(d.mins>=660)
 d['VWAP_RECLAIM']=np.select([vl,vs],[1,-1],0)
 # NR7 inside break: previous M15 is both narrowest of last 7 and inside mother; next breaks the previous mother
 candle_range=h-l
 inside=(ph<h.shift(2))&(pl>l.shift(2))
 nr7=(candle_range.shift(1)<=candle_range.shift(1).rolling(7,min_periods=7).min()+1e-12)
 nl=eligible&inside&nr7&(c>h.shift(2))&(pc<=h.shift(2))&long
 ns=eligible&inside&nr7&(c<l.shift(2))&(pc>=l.shift(2))&short
 d['NR7_INSIDE_BREAK']=np.select([nl,ns],[1,-1],0)
 # Bollinger/Keltner squeeze: previous bars BB compressed inside 1.5 ATR around EMA20, release outside BB
 mean=c.rolling(20,min_periods=20).mean();sd=c.rolling(20,min_periods=20).std(ddof=0)
 bbw=4*sd;kcw=3*atr;was=(bbw.shift(1)<=kcw.shift(1))
 squeeze_l=eligible&was&(bbw>kcw)&(c>mean+2*sd)&(c>o)&long
 squeeze_s=eligible&was&(bbw>kcw)&(c<mean-2*sd)&(c<o)&short
 d['BB_KC_SQUEEZE']=np.select([squeeze_l,squeeze_s],[1,-1],0)
 # DI/ADX Wilder14: fresh DI crossover while ADX >=20 and trend direction
 up=h.diff();dn=-l.diff();pdmp=up.where((up>dn)&(up>0),0.);mdmp=dn.where((dn>up)&(dn>0),0.)
 plus=100*pdmp.ewm(alpha=1/14,adjust=False,min_periods=14).mean()/atr.replace(0,np.nan)
 minus=100*mdmp.ewm(alpha=1/14,adjust=False,min_periods=14).mean()/atr.replace(0,np.nan)
 dx=100*(plus-minus).abs()/(plus+minus).replace(0,np.nan);adx=dx.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
 al=eligible&long&(plus>minus)&(plus.shift(1)<=minus.shift(1))&(adx>=20)&(c>o)
 ast=eligible&short&(minus>plus)&(minus.shift(1)<=plus.shift(1))&(adx>=20)&(c<o)
 d['ADX_DI_TURN']=np.select([al,ast],[1,-1],0)
 # H1 completed OHLC from full 4 adjacent M15 bars; publication end time (last open+15min). No incomplete H1 blocks.
 d['h1_limiter']=d.Datetime.dt.floor('h')
 g=d.groupby('h1_limiter',sort=True).agg(first=('Datetime','min'),last=('Datetime','max'),n=('Datetime','size'),ho=('Open','first'),hh=('High','max'),hl=('Low','min'),hc=('Close','last'))
 valid=(g.n==4)&(g['first']==g.index)&(g['last']==g.index+pd.Timedelta(minutes=45))
 g=g[valid].copy();g['hhprev']=g.hh.shift(1);g['hlprev']=g.hl.shift(1)
 g['hh2']=g.hh.shift(2);g['hl2']=g.hl.shift(2)
 g['bull_struct']=(g.hhprev>g.hh2)&(g.hlprev>g.hl2);g['bear_struct']=(g.hhprev<g.hh2)&(g.hlprev<g.hl2)
 g['pub']=g.index+pd.Timedelta(hours=1)
 # At M15 candle close we know only previously published H1 for all current H1 bars
 a=pd.merge_asof(pd.DataFrame({'available':d.Datetime+pd.Timedelta(minutes=15)}),g[['pub','hhprev','hlprev','bull_struct','bear_struct']].sort_values('pub'),left_on='available',right_on='pub',direction='backward')
 hlv=a.hhprev.to_numpy();llv=a.hlprev.to_numpy()
 brl=eligible&long&a.bull_struct.fillna(False).to_numpy()&(c>hlv)&(pc<=hlv)
 brs=eligible&short&a.bear_struct.fillna(False).to_numpy()&(c<llv)&(pc>=llv)
 d['H1_SWING_BREAK']=np.select([brl,brs],[1,-1],0)
 # Three-bar pullback: 3 completed candles with falling highs/lows counter-direction, then next close > previous high (or inverse).
 correction_l=(h.shift(1)<h.shift(2))&(h.shift(2)<h.shift(3))&(l.shift(1)<l.shift(2))&(l.shift(2)<l.shift(3))
 correction_s=(h.shift(1)>h.shift(2))&(h.shift(2)>h.shift(3))&(l.shift(1)>l.shift(2))&(l.shift(2)>l.shift(3))
 plb=eligible&long&correction_l&(c>ph)&(c>d.ema50)
 psb=eligible&short&correction_s&(c<pl)&(c<d.ema50)
 d['THREE_BAR_PULLBACK']=np.select([plb,psb],[1,-1],0)
 # Linear regression 32 bars: slope of OLS; shifted mean+regression baseline in prior window, reclaim after testing mean
 regmean=c.rolling(32,min_periods=32).mean();reg_slope=(c.rolling(32,min_periods=32).apply(lambda x:np.dot(np.arange(32)-15.5,x)/(2728.),raw=True))
 rl=eligible&long&(reg_slope>0)&(pc<=regmean.shift(1))&(c>regmean)&(c>o)
 rs=eligible&short&(reg_slope<0)&(pc>=regmean.shift(1))&(c<regmean)&(c<o)
 d['REGRESSION_RECLAIM']=np.select([rl,rs],[1,-1],0)
 # Fast/slow EMA cross, requires H1 fast direction but no simultaneous Donchian/ORB level
 clong=eligible&(d.ema20>d.ema60)&(d.ema20.shift(1)<=d.ema60.shift(1))&(d.ema50>d.ema200)&(c>d.ema200)
 cshort=eligible&(d.ema20<d.ema60)&(d.ema20.shift(1)>=d.ema60.shift(1))&(d.ema50<d.ema200)&(c<d.ema200)
 d['EMA20_60_CROSS']=np.select([clong,cshort],[1,-1],0)
 # VWAP_OPEN_DRIVE: 10:45 first-hour VWAP slope and final opening candle beyond +0.6 ATR of day's first open, bias trend
 morning=d[(d.mins>=600)&(d.mins<=645)].groupby('day').agg(mins=('mins',list),firstopen=('Open','first'))
 valid_morning=morning.mins.map(lambda a:a==[600,615,630,645]);d['open10']=d.day.map(morning.firstopen);d['openvalid']=d.day.map(valid_morning).fillna(False)
 vd_l=(d.mins==645)&d.openvalid&long&(c>d.open10+0.6*atr)&(c>d.vwap)&(d.vwap>pvwap)
 vd_s=(d.mins==645)&d.openvalid&short&(c<d.open10-0.6*atr)&(c<d.vwap)&(d.vwap<pvwap)
 d['VWAP_OPEN_DRIVE']=np.select([vd_l,vd_s],[1,-1],0)
 return d

def calc_pf(x):
 a=x[x>0].sum();b=x[x<0].sum();return a/-b if b<0 else np.nan

def main():
 allrows=[];opens=[];sourcehash={};session_universe=set();entry_total=0
 for sym in SYMS:
  path=ROOT/f'{sym}_M15.csv';sourcehash[sym]=hashlib.sha256(path.read_bytes()).hexdigest();d=prep(sym)
  session_universe.update(d.loc[(d.mins>=600)&(d.mins<1020),'day'].dt.date)
  ts=d.Datetime.to_numpy(dtype='datetime64[ns]').astype('int64'); dayidx=pd.factorize(d.day)[0].astype('int64');arr=[d[k].to_numpy(dtype='float64') for k in ['Open','High','Low','Close','atr']]
  for mode in MODES:
   ev,opened=execute(ts,dayidx,*arr,d[mode].to_numpy(dtype='int64'),TICKS[sym]);opens.append({'model':mode,'symbol':sym,'open':opened});entry_total+=len(ev)
   for x in ev:
    sig,en,ex,side,price,end,stop,risk,gross,net,reason=x
    allrows.append({'model':mode,'symbol':sym,'side':side,'signal_dt':str(pd.Timestamp(ts[sig])+pd.Timedelta(minutes=15)),'entry_dt':str(pd.Timestamp(ts[en])),'exit_dt':str(pd.Timestamp(ts[ex])),'entry':price,'exit':end,'stop':stop,'risk':risk,'gross_R':gross,'net_C1_R':net,'reason':int(reason),'entry_session':str(pd.Timestamp(d.day.iloc[en]).date()),'exit_year':pd.Timestamp(ts[ex]).year,'entry_year':pd.Timestamp(ts[en]).year,'exit_month':pd.Timestamp(ts[ex]).strftime('%Y-%m'),'held_hours':float((ts[ex]-ts[en])/3.6e12),'session_span':int(dayidx[ex]-dayidx[en]+1)})
  print('symbol',sym,len(d),'closed',len([r for r in allrows if r['symbol']==sym]),flush=True)
 trades=pd.DataFrame(allrows).sort_values(['model','entry_dt','symbol']);trades.to_csv(OUT/'trades.csv',index=False)
 universe=sorted(session_universe);rows=[];monthly=[];by_sym=[];freq=[]
 for mode in MODES:
  base=trades[trades.model==mode];byday=base.groupby('entry_session').size();
  for name,yrs in [('DEV',[2023,2024]),('LATE',[2025,2026]),('2023',[2023]),('2024',[2024]),('2025',[2025]),('2026',[2026])]:
   g=base[base.exit_year.isin(yrs)];r=g.net_C1_R
   dates=[z for z in universe if z.year in yrs];s=byday.reindex([str(z) for z in dates],fill_value=0)
   bymo=g.groupby('exit_month').net_C1_R.sum().reindex(sorted({str(z)[:7] for z in dates}),fill_value=0)
   byyr=mode+'_'+name
   rows.append({'model':mode,'period':name,'closed':len(g),'pf':calc_pf(r),'net_C1_R':r.sum(),'gross_R':g.gross_R.sum(),'win_rate':(r>0).mean() if len(r) else np.nan,'negative_closed_months':int((bymo<0).sum()),'worst_closed_month_R':bymo.min(),'avg_entries_day':s.mean(),'pct_days_1or2':((s>=1)&(s<=2)).mean()*100,'pct_days_gt2':(s>2).mean()*100,'overnight_pct':(g.session_span>=2).mean()*100,'median_hold_hours':g.held_hours.median()})
   for month,val in bymo.items():monthly.append({'model':mode,'period':name,'month':month,'closed_R':val})
   for sym,gg in g.groupby('symbol'):by_sym.append({'model':mode,'period':name,'symbol':sym,'closed':len(gg),'pf':calc_pf(gg.net_C1_R),'net_C1_R':gg.net_C1_R.sum()})
   if name in ('DEV','LATE'):
    freq+=([{'model':mode,'period':name,'date':z,'entries':int(v)} for z,v in s.items()])
  print('model',mode,[(z['period'],round(z['pf'],3),z['closed']) for z in rows[-6:-4]],flush=True)
 pd.DataFrame(rows).to_csv(OUT/'summary.csv',index=False);pd.DataFrame(monthly).to_csv(OUT/'monthly.csv',index=False);pd.DataFrame(by_sym).to_csv(OUT/'by_symbol.csv',index=False);pd.DataFrame(freq).to_csv(OUT/'daily_frequency.csv',index=False)
 (OUT/'source_sha256.json').write_text(json.dumps(sourcehash,indent=2))
 (OUT/'terminal_open.json').write_text(json.dumps(opens,indent=2))
 print(pd.DataFrame(rows).query("period in ['DEV','LATE']")[['model','period','closed','pf','net_C1_R','negative_closed_months','avg_entries_day','pct_days_gt2']].to_string(index=False))

if __name__=='__main__':main()
