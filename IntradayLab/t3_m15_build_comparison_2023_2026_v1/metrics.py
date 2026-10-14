"""Primary descriptive arithmetic. Every full result precedes sensitivity."""
import numpy as np
from collections import defaultdict
def stats(rows,months):
 rows=sorted(rows,key=lambda r:(r['exit_time'],r['instrument'],r['trade_id']))
 x=np.array([r['gross_R'] for r in rows],dtype=float);w=x[x>0];l=x[x<0]
 gain=float(w.sum());loss=float(-l.sum());total=float(x.sum())
 eq=np.r_[0.,x.cumsum()];dd=float((np.maximum.accumulate(eq)-eq).max())
 monthly={m:0. for m in months};quarter=defaultdict(float)
 for r in rows:
  m=r['exit_time'][:7]
  if m in monthly:monthly[m]+=r['gross_R']
  quarter[m[:4]+'-Q'+str((int(m[5:7])-1)//3+1)]+=r['gross_R']
 def streak(xs):
  a=b=0
  for z in xs:a=a+1 if z<0 else 0;b=max(a,b)
  return b
 worst=min(monthly,key=monthly.get) if monthly else None
 best=sorted(monthly,key=lambda m:(-monthly[m],m));wins=sorted(w,reverse=True)
 res=dict(CLOSED=len(rows),gross_PF=gain/loss if loss else None,PF_status='FINITE' if loss else 'NO_LOSSES' if gain else 'NO_CLOSED_ECONOMICS',gross_R=total,
  positive_R=gain,loss_R=loss,expectancy_R=total/len(x) if len(x) else None,mean_win_R=float(w.mean()) if len(w) else None,mean_loss_R=float(l.mean()) if len(l) else None,
  win_rate=float((x>0).mean()) if len(x) else None,wins=len(w),losses=len(l),zero_trades=int((x==0).sum()),max_DD_R=dd,max_loss_streak=streak(x),
  calendar_months=len(months),positive_months=sum(z>0 for z in monthly.values()),negative_months=sum(z<0 for z in monthly.values()),zero_months=sum(z==0 for z in monthly.values()),
  worst_month=worst,worst_month_R=monthly.get(worst),max_negative_month_streak=streak(monthly.values()),
  worst_quarter=min(quarter,key=quarter.get) if quarter else None,worst_quarter_R=min(quarter.values()) if quarter else None,
  best_month=best[0] if best else None,best_month_share_R=monthly[best[0]]/total if best and total>0 else None,
  top3_month_share_R=sum(monthly[m] for m in best[:3])/total if best and total>0 else None,
  winners_ge2=int((x>=2).sum()),winners_ge5=int((x>=5).sum()))
 for n in (1,5,10):
  removed=float(sum(wins[:n]));res[f'top{n}_trades_R']=removed;res[f'top{n}_trades_share_signed_R']=removed/total if total>0 else None;res[f'top{n}_trades_share_positive_R']=removed/gain if gain>0 else None;res[f'R_without_top{n}_trades']=total-removed;res[f'PF_without_top{n}_trades']=(gain-removed)/loss if loss else None
 for n in (1,3):
  excluded=set(best[:n]);keep=[r for r in rows if r['exit_time'][:7] not in excluded]
  kg=sum(r['gross_R'] for r in keep if r['gross_R']>0);kl=-sum(r['gross_R'] for r in keep if r['gross_R']<0)
  res[f'R_without_top{n}_months']=sum(r['gross_R'] for r in keep);res[f'PF_without_top{n}_months']=kg/kl if kl else None
 contributions={s:sum(r['gross_R'] for r in rows if r['instrument']==s) for s in {r['instrument'] for r in rows}}
 res['best_instrument_share_R']=max(contributions.values())/total if contributions and total>0 else None
 return res
