"""Full causal portfolio replay for fixed H1_SWING_BREAK with exact global max 2 entries/day.
Portfolio case N3 excludes IMOEX based on 2023-24 development-only PF below 1.7.
All later data retrospective, not independent OOS. Tie priority lexicographic CNY,GLD,IMOEX,USD.
Validates cap=4 against independent per-symbol standalone engine, exits included.
"""
from study import prep,TICKS,ROOT,OUT,calc_pf
from numba import njit
import numpy as np,pandas as pd
SYMS=['CNYRUBF','GLDRUBF','IMOEXF','USDRUBF']
@njit
def portfolio(ts,sym,day,day_sess,op,hi,lo,cl,atr,signal,tick,cap):
 nsy=4;pos=np.zeros(nsy,np.int64);pending=np.full(nsy,-1,np.int64);used=np.full(nsy,-1,np.int64)
 sgn=np.zeros(nsy,np.int64);entry=np.zeros(nsy);stop=np.zeros(nsy);risk=np.zeros(nsy);en_idx=np.zeros(nsy,np.int64);en_day=np.zeros(nsy,np.int64);sg_idx=np.zeros(nsy,np.int64)
 global_day=-1;day_entries=0
 out=[];opens=[]
 for i in range(len(ts)):
  s=sym[i]
  if day[i]!=global_day:
   global_day=day[i];day_entries=0
  if pos[s]:
   exval=0.;reason=0
   if day_sess[i]-en_day[s]>=2:exval=op[i];reason=3
   elif (sgn[s]==1 and op[i]<=stop[s]+tick[i]*1e-7) or (sgn[s]==-1 and op[i]>=stop[s]-tick[i]*1e-7):exval=op[i];reason=2
   elif (sgn[s]==1 and lo[i]<=stop[s]+tick[i]*1e-7) or (sgn[s]==-1 and hi[i]>=stop[s]-tick[i]*1e-7):exval=stop[s];reason=1
   if reason:
    gross=sgn[s]*(exval-entry[s])/risk[s]
    out.append((sg_idx[s],en_idx[s],i,s,sgn[s],entry[s],exval,stop[s],risk[s],gross,gross-2*tick[i]/risk[s],reason));pos[s]=0
  if pending[s]>=0:
   at=pending[s]
   if ts[i]==ts[at]+900000000000 and pos[s]==0 and used[s]!=day_sess[i] and day_entries<cap:
    direction=signal[at];entrypx=op[i]; target=entrypx-direction*2*atr[at]
    initial=(np.floor(target/tick[i]+1e-9) if direction==1 else np.ceil(target/tick[i]-1e-9))*tick[i]
    dist=abs(entrypx-initial)
    if np.isfinite(dist) and dist>0:
     sg_idx[s]=at;en_idx[s]=i;sgn[s]=direction;entry[s]=entrypx;stop[s]=initial;risk[s]=dist;en_day[s]=day_sess[i];used[s]=day_sess[i];pos[s]=1;day_entries+=1
     if (direction==1 and lo[i]<=initial+tick[i]*1e-7) or (direction==-1 and hi[i]>=initial-tick[i]*1e-7):
      out.append((at,i,i,s,direction,entrypx,initial,initial,dist,-1.,-1.-2*tick[i]/dist,4));pos[s]=0
   pending[s]=-1
  if signal[i] and pos[s]==0 and used[s]!=day_sess[i] and np.isfinite(atr[i]) and atr[i]>0:pending[s]=i
 for s in range(nsy):
  opens.append((s,int(pos[s])))
 return out,opens

def prepare(instruments):
 parts=[]
 for i,sym in enumerate(SYMS):
  if sym not in instruments:continue
  d=prep(sym);d['sym']=i;d['tick']=TICKS[sym];d['day_sess']=pd.factorize(d.day)[0];d=d[['Datetime','sym','day','day_sess','Open','High','Low','Close','atr','H1_SWING_BREAK','tick']].copy();parts.append(d)
 z=pd.concat(parts,ignore_index=True).sort_values(['Datetime','sym'],kind='mergesort').reset_index(drop=True)
 z['day_num']=pd.factorize(z.day)[0]
 return z

def run(instruments,cap):
 z=prepare(instruments);times=z.Datetime.to_numpy(dtype='datetime64[ns]').astype(np.int64)
 ev,opns=portfolio(times,z.sym.to_numpy(np.int64),z.day_num.to_numpy(np.int64),z.day_sess.to_numpy(np.int64),*[z[f].to_numpy(np.float64) for f in ['Open','High','Low','Close','atr']],z.H1_SWING_BREAK.to_numpy(np.int64),z.tick.to_numpy(np.float64),cap)
 rows=[]
 for sg,en,ex,s,side,entry,exitpx,stop,risk,gross,net,reason in ev:
  rows.append(dict(symbol=SYMS[s],side=side,signal_dt=str(pd.Timestamp(times[sg])+pd.Timedelta(minutes=15)),entry_dt=str(pd.Timestamp(times[en])),exit_dt=str(pd.Timestamp(times[ex])),entry_session=str(pd.Timestamp(z.day.iloc[en]).date()),entry=entry,exit=exitpx,stop=stop,risk=risk,gross_R=gross,net_C1_R=net,reason=reason,exit_year=pd.Timestamp(times[ex]).year,exit_month=pd.Timestamp(times[ex]).strftime('%Y-%m'),session_span=int(z.day_sess.iloc[ex]-z.day_sess.iloc[en]+1)))
 return pd.DataFrame(rows),opns

def main():
 out=[];alltrades=[]
 for group,syms in [('N4',SYMS),('N3_DEV_EX_IMOEXF',[s for s in SYMS if s!='IMOEXF'])]:
  for cap in [2,4]:
   t,opened=run(syms,cap);tag=group+'_CAP'+str(cap);t['model']=tag;alltrades.append(t)
   for period,ys in [('DEV',[2023,2024]),('LATE',[2025,2026]),('2023',[2023]),('2024',[2024]),('2025',[2025]),('2026',[2026])]:
    g=t[t.exit_year.isin(ys)];r=g.net_C1_R;mo=g.groupby('exit_month').net_C1_R.sum()
    out.append(dict(model=tag,period=period,closed=len(g),pf=calc_pf(r),net_C1_R=r.sum(),negative_closed_months=(mo<0).sum(),avg_entries_day=(t[pd.to_datetime(t.entry_dt).dt.year.isin(ys)].groupby('entry_session').size().sum()/len(pd.date_range('2023-01-01','2023-12-31'))) if False else np.nan,open_count=sum(c for s,c in opened)))
   print(tag,len(t), 'OPEN',opened,flush=True)
 ss=pd.DataFrame(out);alltr=pd.concat(alltrades);alltr.to_csv(OUT/'portfolio_trades.csv',index=False);ss.to_csv(OUT/'portfolio_summary.csv',index=False)
 print(ss.query('period in ["DEV","LATE"]').to_string(index=False))
 # All standalone trades with complete output should exactly coincide when capacity is unconstrained (cap>=4) 
 raw=pd.read_csv(OUT/'trades.csv');raw=raw[raw.model=='H1_SWING_BREAK'].copy()
 for group,syms in [('N4',SYMS),('N3_DEV_EX_IMOEXF',[s for s in SYMS if s!='IMOEXF'])]:
  q=alltr[alltr.model==group+'_CAP4'];h=raw[raw.symbol.isin(syms)];keys=['symbol','signal_dt','entry_dt','exit_dt','net_C1_R']
  def keyset(f):return sorted(tuple(x) for x in f[keys].itertuples(index=False,name=None))
  assert len(q)==len(h) and all(a[:4]==b[:4] and abs(a[4]-b[4])<1e-10 for a,b in zip(keyset(q),keyset(h))),f'CAP4 not equal control {group}'
  print('PASS full CAP4 vs independent per-symbol',group,len(h),flush=True)
if __name__=='__main__':main()
