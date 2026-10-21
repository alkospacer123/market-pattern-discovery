"""V11, frozen 10 mechanisms, exploratory; never route to live."""
from pathlib import Path
import hashlib,json,sys
import pandas as pd,numpy as np
from numba import njit
ROOT=Path(__file__).resolve().parent
# imported locked support module; upstream archived in V11
SYMS=['CNYRUBF','GLDRUBF','IMOEXF','USDRUBF'];TICKS={'CNYRUBF':.001,'GLDRUBF':.1,'IMOEXF':.5,'USDRUBF':.01}
MODES=['CONTINUATION_2DAY','BREAK_HIGH_VOL','MIDDAY_RETEST','TWO_UP_HOURS','FAILED_AM_BREAK','CLIMAX_WICK_FADE','EXTREME_BB_REENTRY','OPEN_GAP_FOLLOW','OPEN_GAP_REVERSE','FX_LAG_REACTION']

@njit
def replay(ts,sym,day,day_sess,op,hi,lo,cl,atr,signal,target,tpr,tick):
 nsy=4;pos=np.zeros(nsy,np.int64);pending=np.full(nsy,-1,np.int64);used=np.full(nsy,-1,np.int64)
 side=np.zeros(nsy,np.int64);entry=np.zeros(nsy);stop=np.zeros(nsy);risk=np.zeros(nsy);tp=np.full(nsy,np.nan);en_idx=np.zeros(nsy,np.int64);en_day=np.zeros(nsy,np.int64);sg_idx=np.zeros(nsy,np.int64)
 gd=-1;nent=0;out=[]
 for i in range(len(ts)):
  s=sym[i]
  if day[i]!=gd:gd=day[i];nent=0
  if pos[s]:
   x=0.;why=0
   if day_sess[i]-en_day[s]>=2: x=op[i];why=3
   elif (side[s]==1 and op[i]<=stop[s]+tick[i]*1e-7) or (side[s]==-1 and op[i]>=stop[s]-tick[i]*1e-7): x=op[i];why=2
   elif (side[s]==1 and lo[i]<=stop[s]+tick[i]*1e-7) or (side[s]==-1 and hi[i]>=stop[s]-tick[i]*1e-7):x=stop[s];why=1
   elif np.isfinite(tp[s]):
    if (side[s]==1 and op[i]>=tp[s]-tick[i]*1e-7) or (side[s]==-1 and op[i]<=tp[s]+tick[i]*1e-7):x=op[i];why=6
    elif (side[s]==1 and hi[i]>=tp[s]-tick[i]*1e-7) or (side[s]==-1 and lo[i]<=tp[s]+tick[i]*1e-7):x=tp[s];why=5
   if why:
    gross=side[s]*(x-entry[s])/risk[s]
    out.append((sg_idx[s],en_idx[s],i,s,side[s],entry[s],x,stop[s],risk[s],tp[s],gross,gross-2*tick[i]/risk[s],why))
    pos[s]=0
  if pending[s]>=0:
   at=pending[s]
   if ts[i]==ts[at]+900000000000 and pos[s]==0 and used[s]!=day_sess[i] and nent<2:
    direction=signal[at];price=op[i];raw=price-direction*2*atr[at]
    sp=(np.floor(raw/tick[i]+1e-9) if direction==1 else np.ceil(raw/tick[i]-1e-9))*tick[i];dist=abs(price-sp)
    targ=target[at]
    if not np.isfinite(targ) and np.isfinite(tpr[at]):targ=price+direction*tpr[at]*dist
    if np.isfinite(targ):targ=(np.floor(targ/tick[i]+1e-9) if direction==1 else np.ceil(targ/tick[i]-1e-9))*tick[i]
    if dist>0 and np.isfinite(dist) and (not np.isfinite(targ) or direction*(targ-price)>0):
     sg_idx[s]=at;en_idx[s]=i;side[s]=direction;entry[s]=price;stop[s]=sp;risk[s]=dist;tp[s]=targ;en_day[s]=day_sess[i];used[s]=day_sess[i];pos[s]=1;nent+=1
     # stop-first on entry bar; do not assume favorable OHLC ordering
     if (direction==1 and lo[i]<=sp+tick[i]*1e-7) or (direction==-1 and hi[i]>=sp-tick[i]*1e-7):
      out.append((at,i,i,s,direction,price,sp,sp,dist,targ,-1.,-1.-2*tick[i]/dist,4));pos[s]=0
     elif np.isfinite(targ) and ((direction==1 and hi[i]>=targ-tick[i]*1e-7) or (direction==-1 and lo[i]<=targ+tick[i]*1e-7)):
      gross=direction*(targ-price)/dist
      out.append((at,i,i,s,direction,price,targ,sp,dist,targ,gross,gross-2*tick[i]/dist,7));pos[s]=0
   pending[s]=-1
  if signal[i]!=0 and pos[s]==0 and used[s]!=day_sess[i] and np.isfinite(atr[i]) and atr[i]>0:pending[s]=i
 openings=[]
 for s in range(nsy):
  if pos[s]:openings.append((s,sg_idx[s],en_idx[s],entry[s],risk[s],side[s]))
 return out,openings

def prepare(sym):
 d=pd.read_csv(ROOT/'marketdata_m15'/f'{sym}_M15.csv',sep=';',parse_dates=['Datetime']).sort_values('Datetime').reset_index(drop=True)
 assert d.Datetime.is_monotonic_increasing and not d.Datetime.duplicated().any()
 assert ((d.High>=d[['Open','Close','Low']].max(axis=1))&(d.Low<=d[['Open','Close','High']].min(axis=1))).all()
 d['day']=(d.Datetime-pd.Timedelta(hours=9)).dt.normalize();d['mins']=d.Datetime.dt.hour*60+d.Datetime.dt.minute
 o,h,l,c,v=[d[k].astype(float) for k in ['Open','High','Low','Close','Volume']]
 p=c.shift(1);ph=h.shift(1);pl=l.shift(1)
 d['ema50']=c.ewm(span=50,adjust=False,min_periods=50).mean();d['ema200']=c.ewm(span=200,adjust=False,min_periods=200).mean()
 tr=pd.concat([h-l,(h-p).abs(),(l-p).abs()],axis=1).max(axis=1);d['atr']=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean();atr=d.atr
 up=(d.ema50>d.ema200)&(d.ema50>d.ema50.shift(4));dn=(d.ema50<d.ema200)&(d.ema50<d.ema50.shift(4))
 eligible=(d.mins>=600)&(d.mins<=1020)
 first=(d.mins>=600)&(d.mins<=645);firstdf=d[first]
 firsthour=firstdf.groupby('day').agg(fo=('Open','first'),fc=('Close','last'),fh=('High','max'),fl=('Low','min'),tm=('mins',list))
 firsthour['full']=firsthour.tm.map(lambda x:x==[600,615,630,645]);firsthour['mid']=(firsthour.fh+firsthour.fl)/2
 for x in ['fo','fc','fh','fl','full','mid']:d['m_'+x]=d.day.map(firsthour[x])
 mf=d.m_full.fillna(False).astype(bool)&(d.mins>=660)
 session=d[(d.mins>=600)&(d.mins<=1065)]
 daily=session.groupby('day').agg(do=('Open','first'),dc=('Close','last'),dh=('High','max'),dl=('Low','min'),atr=('atr','last'),tm=('mins',list))
 daily['full']=daily.tm.map(lambda x:x==list(range(600,1080,15)))
 daily['body']=(daily.dc-daily.do)/daily.atr.replace(0,np.nan)
 daily['closepos']=(daily.dc-daily.dl)/(daily.dh-daily.dl).replace(0,np.nan)
 for x in ['do','dc','dh','dl','atr','full','body','closepos']:d['y_'+x]=d.day.map(daily[x].shift(1))
 yfull=d.y_full.fillna(False).astype(bool)
 firsto=d.day.map(session[session.mins==600].set_index('day').Open);d['first_open']=firsto
 f2=session[session.mins.isin([600,615])].groupby('day').agg(hi=('High','max'),lo=('Low','min'),tm=('mins',list))
 f2['full']=f2.tm.map(lambda x:x==[600,615]);d['first2_hi']=d.day.map(f2.hi);d['first2_lo']=d.day.map(f2.lo);d['first2_full']=d.day.map(f2.full).fillna(False).astype(bool)
 # prior 20 bar true past median (we don't know bar volume until it completes, so prior only)
 medvol20=v.shift(1).rolling(20,min_periods=20).median();medvol40=v.shift(1).rolling(40,min_periods=40).median()
 # 1: yesterday directional and extreme close, continued today 10:30 M15
 m1l=(d.mins==630)&yfull&(d.y_body>=1.5)&(d.y_closepos>=.8)&(c>d.first_open)&(c>o)&up
 m1s=(d.mins==630)&yfull&(d.y_body<=-1.5)&(d.y_closepos<=.2)&(c<d.first_open)&(c<o)&dn
 d['CONTINUATION_2DAY']=np.select([m1l,m1s],[1,-1],0)
 # 2: break 32-bar previous high / low on elevated volume
 bhl=(eligible)&(d.mins>=660)&(v>=2*medvol20)&(c>h.shift(1).rolling(32,min_periods=32).max())&up&(c>o)
 bhs=(eligible)&(d.mins>=660)&(v>=2*medvol20)&(c<l.shift(1).rolling(32,min_periods=32).min())&dn&(c<o)
 d['BREAK_HIGH_VOL']=np.select([bhl,bhs],[1,-1],0)
 # 3: price retests completed first hour midpoint then closes away
 m3l=mf&(d.mins>=780)&(d.mins<=900)&((d.m_fc-d.m_fo)>=atr)&(l<=d.m_mid)&(c>d.m_mid)&(c>o)&up
 m3s=mf&(d.mins>=780)&(d.mins<=900)&((d.m_fo-d.m_fc)>=atr)&(h>=d.m_mid)&(c<d.m_mid)&(c<o)&dn
 d['MIDDAY_RETEST']=np.select([m3l,m3s],[1,-1],0)
 # 4: two most recent *fully completed/published* H1 bars have rising highs and lows + bullish body; asof public at close
 g=d.groupby(d.Datetime.dt.floor('h'),sort=True).agg(start=('Datetime','min'),end=('Datetime','max'),n=('Datetime','size'),ho=('Open','first'),hh=('High','max'),hl=('Low','min'),hc=('Close','last'))
 g=g[(g.n==4)&(g.start==g.index)&(g.end==g.index+pd.Timedelta(minutes=45))].copy()
 g['pub']=g.index+pd.Timedelta(hours=1)
 g['bull']=(g.hc>g.ho)&(g.hc.shift(1)>g.ho.shift(1))&(g.hh>g.hh.shift(1))&(g.hl>g.hl.shift(1))
 g['bear']=(g.hc<g.ho)&(g.hc.shift(1)<g.ho.shift(1))&(g.hh<g.hh.shift(1))&(g.hl<g.hl.shift(1))
 aa=pd.merge_asof(pd.DataFrame({'known':d.Datetime+pd.Timedelta(minutes=15)}),g[['pub','bull','bear']].sort_values('pub'),left_on='known',right_on='pub',direction='backward')
 m4l=eligible&(d.mins>=780)&(aa.bull.fillna(False).to_numpy())&up&(c>h.shift(1).rolling(8,min_periods=8).max())
 m4s=eligible&(d.mins>=780)&(aa.bear.fillna(False).to_numpy())&dn&(c<l.shift(1).rolling(8,min_periods=8).min())
 d['TWO_UP_HOURS']=np.select([m4l,m4s],[1,-1],0)
 # 5: current bar probes completed morning high/low then closes back, reverse to morning midpoint
 m5s=mf&(d.mins>=675)&(d.mins<=840)&(h>d.m_fh)&(c<d.m_fh)&(c> d.m_mid)&(c<o)
 m5l=mf&(d.mins>=675)&(d.mins<=840)&(l<d.m_fl)&(c>d.m_fl)&(c<d.m_mid)&(c>o)
 d['FAILED_AM_BREAK']=np.select([m5l,m5s],[1,-1],0)
 d['FAILED_AM_BREAK_target']=d.m_mid
 # 6: wick rejection with volume climax
 rng=(h-l).replace(0,np.nan);uw=h-np.maximum(c,o);lw=np.minimum(c,o)-l
 m6s=eligible&(d.mins>=630)&(uw/rng>=.65)&(rng>=1.5*atr)&(v>=2*medvol40)&(c<o)
 m6l=eligible&(d.mins>=630)&(lw/rng>=.65)&(rng>=1.5*atr)&(v>=2*medvol40)&(c>o)
 d['CLIMAX_WICK_FADE']=np.select([m6l,m6s],[1,-1],0)
 # 7: prior Close outside BB30, current Close returns inside
 mean=c.rolling(30,min_periods=30).mean();sd=c.rolling(30,min_periods=30).std(ddof=0)
 m7l=eligible&(d.mins>=630)&(p<mean.shift(1)-2.5*sd.shift(1))&(c>mean-2.5*sd)&(c>o)
 m7s=eligible&(d.mins>=630)&(p>mean.shift(1)+2.5*sd.shift(1))&(c<mean+2.5*sd)&(c<o)
 d['EXTREME_BB_REENTRY']=np.select([m7l,m7s],[1,-1],0)
 d['EXTREME_BB_REENTRY_target']=mean
 # 8: yesterday trending, today aligned opening gap + break completed 30-min range at 10:45
 gap=firsto-d.y_dc
 m8l=(d.mins==645)&d.first2_full&yfull&(d.y_body>=1)&(gap>=.4*atr)&(c>d.first2_hi)&up
 m8s=(d.mins==645)&d.first2_full&yfull&(d.y_body<=-1)&(gap<=-.4*atr)&(c<d.first2_lo)&dn
 d['OPEN_GAP_FOLLOW']=np.select([m8l,m8s],[1,-1],0)
 # 9: gap against yesterday trend, price returns toward yesterday close by 11:00
 m9l=(d.mins==660)&mf&yfull&(d.y_body>=1)&(gap<=-.6*atr)&(c>o)&(c>firsto)
 m9s=(d.mins==660)&mf&yfull&(d.y_body<=-1)&(gap>=.6*atr)&(c<o)&(c<firsto)
 d['OPEN_GAP_REVERSE']=np.select([m9l,m9s],[1,-1],0)
 d['OPEN_GAP_REVERSE_target']=d.y_dc
 # 10 cross-asset filled after all per symbol preprocessing
 d['FX_LAG_REACTION']=np.zeros(len(d),np.int8)
 d['fx_trend_long']=up;d['fx_trend_short']=dn;d['fx_mom4']=(c/c.shift(4)-1)*c/atr.replace(0,np.nan) # approximate scaled 4bar change
 d['fx_breaklong']=eligible&(d.mins>=600)&(c>h.shift(1).rolling(3,min_periods=3).max())&(v>=1.3*medvol20)
 d['fx_breakshort']=eligible&(d.mins>=600)&(c<l.shift(1).rolling(3,min_periods=3).min())&(v>=1.3*medvol20)
 # set fixed targets in initial R, no TP for modes with fixed pre-known price
 for k in MODES:
  if k+'_target' not in d:d[k+'_target']=np.nan
  d[k+'_tpr'] = np.nan
 for k in ['CONTINUATION_2DAY','MIDDAY_RETEST','OPEN_GAP_FOLLOW','FX_LAG_REACTION']:
  d[k+'_tpr']=2.5
 for k in ['BREAK_HIGH_VOL','TWO_UP_HOURS']:d[k+'_tpr']=3.
 for k in ['CLIMAX_WICK_FADE']:d[k+'_tpr']=1.5
 return d

def cross(D):
 u=D['USDRUBF'][['Datetime','fx_trend_long','fx_trend_short','fx_mom4','fx_breaklong','fx_breakshort']].rename(columns={x:'usd_'+x for x in ['fx_trend_long','fx_trend_short','fx_mom4','fx_breaklong','fx_breakshort']})
 c=D['CNYRUBF'][['Datetime','fx_trend_long','fx_trend_short','fx_mom4','fx_breaklong','fx_breakshort']].rename(columns={x:'cny_'+x for x in ['fx_trend_long','fx_trend_short','fx_mom4','fx_breaklong','fx_breakshort']})
 # strictly contemporaneous, both completed bars at same timestamp
 z=u.merge(c,on='Datetime',how='inner')
 # lagging *target* is below .25 ATR, leader >=.7 ATR. Current target breakout through last3, volume signal.
 m1=z.usd_fx_trend_long&z.cny_fx_trend_long&(z.usd_fx_mom4>=.7)&(z.cny_fx_mom4.abs()<.25)&z.cny_fx_breaklong
 m2=z.usd_fx_trend_short&z.cny_fx_trend_short&(z.usd_fx_mom4<=-.7)&(z.cny_fx_mom4.abs()<.25)&z.cny_fx_breakshort
 m3=z.usd_fx_trend_long&z.cny_fx_trend_long&(z.cny_fx_mom4>=.7)&(z.usd_fx_mom4.abs()<.25)&z.usd_fx_breaklong
 m4=z.usd_fx_trend_short&z.cny_fx_trend_short&(z.cny_fx_mom4<=-.7)&(z.usd_fx_mom4.abs()<.25)&z.usd_fx_breakshort
 # assignment by current completed exact timestamp
 for s,a,b in [('USDRUBF',m3,m4),('CNYRUBF',m1,m2)]:
  zz=z.loc[a|b,['Datetime']].copy();zz['x']=np.select([a[a|b],b[a|b]],[1,-1],0).astype('int8')
  dd=D[s];dd['FX_LAG_REACTION']=dd.Datetime.map(zz.set_index('Datetime').x).fillna(0).astype('int8')

def merged(D,mode):
 blocks=[]
 for si,s in enumerate(SYMS):
  d=D[s][['Datetime','day','Open','High','Low','Close','atr',mode,mode+'_target',mode+'_tpr']].copy()
  d['sym']=si;d['tick']=TICKS[s];d['day_sess']=pd.factorize(d.day)[0];blocks.append(d)
 z=pd.concat(blocks,ignore_index=True).sort_values(['Datetime','sym'],kind='stable').reset_index(drop=True)
 z['day_n']=pd.factorize(z.day)[0]
 ts=z.Datetime.to_numpy(dtype='datetime64[ns]').astype('int64')
 args=[z[k].to_numpy(np.float64) for k in ['Open','High','Low','Close','atr']]
 events,opened=replay(ts,z.sym.to_numpy(np.int64),z.day_n.to_numpy(np.int64),z.day_sess.to_numpy(np.int64),*args,z[mode].to_numpy(np.int64),z[mode+'_target'].to_numpy(np.float64),z[mode+'_tpr'].to_numpy(np.float64),z.tick.to_numpy(np.float64))
 rows=[]
 for sg,en,ex,s,side,entry,exprice,stop,risk,tp,gross,net,reason in events:
  rows.append({'model':mode,'symbol':SYMS[s],'side':int(side),'signal_time':str(pd.Timestamp(ts[sg])+pd.Timedelta(minutes=15)),'entry_time':str(pd.Timestamp(ts[en])),'exit_time':str(pd.Timestamp(ts[ex])),'entry_day':str(pd.Timestamp(z.day.iloc[en]).date()),'entry':entry,'exit':exprice,'stop':stop,'risk':risk,'tp':tp,'gross_R':gross,'net_R':net,'exit_reason':reason,'exit_year':pd.Timestamp(ts[ex]).year,'exit_month':pd.Timestamp(ts[ex]).strftime('%Y-%m'),'held_hours':(ts[ex]-ts[en])/3.6e12,'session_count':int(z.day_sess.iloc[ex]-z.day_sess.iloc[en]+1)})
 return pd.DataFrame(rows),opened

def pf(r):
 w=r[r>0].sum();l=-r[r<0].sum();return w/l if l>0 else np.nan

def stats(tr,universe):
 summary=[];months=[];daily=[];symbols=[]
 for mode in MODES:
  w=tr[tr.model==mode].copy()
  w['ey']=pd.to_datetime(w.entry_time).dt.year
  for name,ys in [('2023',[2023]),('2024',[2024]),('2025',[2025]),('2026',[2026]),('DEV',[2023,2024]),('LATE',[2025,2026]),('ALL',[2023,2024,2025,2026])]:
   g=w[w.exit_year.isin(ys)].copy();r=g.net_R
   dates=[dt for dt in universe if int(dt[:4]) in ys]
   n=w[w.ey.isin(ys)].groupby('entry_day').size().reindex(dates,fill_value=0)
   monthly=g.groupby('exit_month').net_R.sum().reindex(sorted({dt[:7] for dt in dates}),fill_value=0)
   ordered=g.sort_values(['exit_time','symbol','entry_time']);rr=ordered.net_R.to_numpy();cc=np.cumsum(rr);dd=(np.maximum.accumulate(np.r_[0.,cc])[1:]-cc).max() if len(cc) else np.nan
   summary.append({'model':mode,'period':name,'closed':len(g),'PF':pf(r),'net_R':r.sum(),'gross_R':g.gross_R.sum(),'max_closed_DD_R':dd,'negative_months':int((monthly<0).sum()),'min_month_R':monthly.min() if len(monthly) else np.nan,'avg_entries_day':n.mean() if len(n) else np.nan,'pct_days_zero':100*n.eq(0).mean() if len(n) else np.nan,'pct_days_1or2':100*n.between(1,2).mean() if len(n) else np.nan,'pct_days_gt2':100*n.gt(2).mean() if len(n) else np.nan,'median_hold_h':g.held_hours.median(),'pct_next_session':100*g.session_count.ge(2).mean() if len(g) else np.nan,'ge2_count':int((r>=2).sum())})
   if name in ('DEV','LATE'):
    for dt,value in n.items():daily.append({'model':mode,'period':name,'date':dt,'entries':int(value)})
    for m,value in monthly.items():months.append({'model':mode,'period':name,'month':m,'net_R':value})
   if name in ('2023','2024','2025','2026'):
    for sym,q in g.groupby('symbol'):symbols.append({'model':mode,'year':name,'symbol':sym,'closed':len(q),'PF':pf(q.net_R),'net_R':q.net_R.sum()})
 return pd.DataFrame(summary),pd.DataFrame(daily),pd.DataFrame(months),pd.DataFrame(symbols)

def main():
 D={};source={};universe=set();sigcounts=[];alltr=[];terminal={}
 for s in SYMS:
  p=ROOT/'marketdata_m15'/f'{s}_M15.csv';source[s]=hashlib.sha256(p.read_bytes()).hexdigest()
  d=prepare(s);D[s]=d
  universe.update(d.loc[(d.mins>=600)&(d.mins<=1020),'day'].dt.strftime('%Y-%m-%d').tolist())
  print('prepared',s,len(d),flush=True)
 cross(D)
 for mode in MODES:
  for s,d in D.items():sigcounts.append({'model':mode,'symbol':s,'signals':int((d[mode]!=0).sum())})
  tr,op=merged(D,mode)
  if not tr.empty:alltr.append(tr)
  terminal[mode]=op
  print('replayed',mode,len(tr),'open',len(op),flush=True)
 alltr=pd.concat(alltr,ignore_index=True)
 summary,daily,monthly,symbol=stats(alltr,sorted(universe))
 for name,df in [('trades',alltr),('summary',summary),('daily_frequency',daily),('monthly',monthly),('by_symbol',symbol),('signal_counts',pd.DataFrame(sigcounts))]:df.to_csv(ROOT/f'{name}.csv',index=False)
 (ROOT/'LINEAGE.json').write_text(json.dumps({'sha256_ohlcv':source,'protocol_sha256':hashlib.sha256((ROOT/'PROTOCOL_RU.md').read_bytes()).hexdigest(),'terminal_open':terminal,'independent_OOS':False},ensure_ascii=False,indent=2))
 print(summary[summary.period.isin(['2023','2024','2025','2026'])].pivot(index='model',columns='period',values='PF').round(3).to_string(),flush=True)
 print(summary[summary.period.eq('LATE')][['model','closed','PF','avg_entries_day','pct_days_1or2','pct_days_zero']].to_string(index=False),flush=True)

if __name__=='__main__':main()
