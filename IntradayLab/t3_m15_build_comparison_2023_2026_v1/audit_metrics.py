"""Independent stdlib arithmetic audit; imports no primary reporting/metrics."""
import argparse,csv,json,math,gzip
from pathlib import Path
from collections import defaultdict

def read(p):
 with (gzip.open(p,'rt') if str(p).endswith('.gz') else open(p)) as f:return list(csv.DictReader(f))
def read_rows(p):
 with open(p) as f:yield from csv.DictReader(f)
def independent(rows,months):
 ordered=sorted(rows,key=lambda r:(r['exit_time'],r['instrument'],r['trade_id']));x=[float(r['gross_R']) for r in ordered]
 wins=[v for v in x if v>0];losses=[v for v in x if v<0];gain=math.fsum(wins);loss=-math.fsum(losses);total=math.fsum(x)
 eq=peak=dd=run=longest=0.
 for v in x:
  eq+=v;peak=max(peak,eq);dd=max(dd,peak-eq);run=run+1 if v<0 else 0;longest=max(longest,run)
 groups=defaultdict(list);qs=defaultdict(list);ins=defaultdict(list)
 for r in ordered:
  m=r['exit_time'][:7];groups[m].append(float(r['gross_R']));qs[m[:4]+'-Q'+str((int(m[-2:])-1)//3+1)].append(float(r['gross_R']));ins[r['instrument']].append(float(r['gross_R']))
 mr={m:math.fsum(groups[m]) for m in months};nr=nmax=0
 for m in months:nr=nr+1 if mr[m]<0 else 0;nmax=max(nmax,nr)
 best=sorted(months,key=lambda m:(-mr[m],m));worst=min(months,key=lambda m:mr[m]) if months else None
 res=dict(CLOSED=len(x),gross_PF=gain/loss if loss else None,gross_R=total,positive_R=gain,loss_R=loss,expectancy_R=total/len(x) if x else None,
  mean_win_R=gain/len(wins) if wins else None,mean_loss_R=-loss/len(losses) if losses else None,win_rate=len(wins)/len(x) if x else None,
  wins=len(wins),losses=len(losses),zero_trades=sum(v==0 for v in x),max_DD_R=dd,max_loss_streak=longest,
  calendar_months=len(months),positive_months=sum(mr[m]>0 for m in months),negative_months=sum(mr[m]<0 for m in months),zero_months=sum(mr[m]==0 for m in months),
  worst_month=worst,worst_month_R=mr.get(worst),max_negative_month_streak=nmax,
  worst_quarter=min(qs,key=lambda q:math.fsum(qs[q])) if qs else None,worst_quarter_R=min((math.fsum(q) for q in qs.values()),default=None),
  best_month=best[0] if best else None,best_month_share_R=mr[best[0]]/total if best and total>0 else None,top3_month_share_R=math.fsum(mr[m] for m in best[:3])/total if total>0 else None,
  best_instrument_share_R=max((math.fsum(q) for q in ins.values()),default=0)/total if ins and total>0 else None,
  winners_ge2=sum(v>=2 for v in x),winners_ge5=sum(v>=5 for v in x))
 for n in (1,5,10):
  r=math.fsum(sorted(wins,reverse=True)[:n]);res[f'top{n}_trades_R']=r;res[f'top{n}_trades_share_signed_R']=r/total if total>0 else None;res[f'top{n}_trades_share_positive_R']=r/gain if gain>0 else None;res[f'R_without_top{n}_trades']=total-r;res[f'PF_without_top{n}_trades']=(gain-r)/loss if loss else None
 for n in (1,3):
  keep=[float(r['gross_R']) for r in ordered if r['exit_time'][:7] not in set(best[:n])];kg=math.fsum(v for v in keep if v>0);kl=-math.fsum(v for v in keep if v<0)
  res[f'R_without_top{n}_months']=math.fsum(keep);res[f'PF_without_top{n}_months']=kg/kl if kl else None
 return res

def audit(folder,coverage):
 times=coverage['times'];common=set.intersection(*(set(x) for x in times.values()));assert common==set(coverage['common_set'])
 ledgers={};fields=rows=0;maxdelta=0.;tables={};coverage_months={}
 for view,w in coverage['views'].items():coverage_months[view]={s:{t[:7] for t in ts if w['start']<=t<w['end_exclusive'] and (view!='COMMON_OBSERVED' or t in common)} for s,ts in times.items()}
 for name in ('ANNUAL_COMPARISON','MONTHLY_COMPARISON','INSTRUMENT_COMPARISON','PORTFOLIO_SUBSETS'):
  local=0
  for r in read_rows(folder/(name+'.csv')):
   bid=r['build_id']
   if bid not in ledgers:ledgers[bid]=read(folder/'journals'/bid/'trades.csv.gz')
   window=coverage['views'][r['view']];start=window['start'];end=window['end_exclusive']
   if r.get('month'):months=[r['month']];year=r['month'][:4]
   else:
    year=r['year'];y,m=int(start[:4]),int(start[5:7]);months=[]
    while f'{y:04d}-{m:02d}-01T00:00:00+03:00'<end:
     stamp=f'{y:04d}-{m:02d}'
     if year=='ALL' or stamp[:4]==year:months.append(stamp)
     m+=1
     if m==13:y+=1;m=1
   syms=(r['instruments'].split(';') if r.get('instruments') else [r['instrument']]);side=r.get('direction','BOTH')
   selected=[q for q in ledgers[bid] if q['instrument'] in syms and start<=q['exit_time']<end and (year=='ALL' or q['exit_time'][:4]==year)
    and (not r.get('month') or q['exit_time'][:7]==r['month']) and (r['view']!='COMMON_OBSERVED' or q.get('exit_bar_close_time',q['exit_time']) in common) and (side=='BOTH' or q['direction']==side)]
   expected=independent(selected,months)
   for k,v in expected.items():
    assert k in r,(name,k);saved=r[k];fields+=1
    if v is None:assert saved=='',(name,bid,k,saved)
    elif isinstance(v,(int,float)):
     delta=abs(float(saved)-v);assert delta<=1e-8,(name,bid,k,saved,v,delta);maxdelta=max(maxdelta,delta)
    else:assert saved==v,(name,bid,k,saved,v)
   if r.get('covered_months'):
    covered=sum(any(mo in coverage_months[r['view']][s] for s in syms) for mo in months)
    assert int(r['covered_months'])==covered;fields+=1
   local+=1;rows+=1
  tables[name]=local
  print('ARITHMETIC_AUDIT',name,local,flush=True)
 annual={(r['build_id'],r['view'],r['year']):r for r in read(folder/'ANNUAL_COMPARISON.csv')}
 effects=0
 for r in read(folder/'FILTER_CONTRIBUTION.csv'):
  if r.get('status')=='MISSING_CAUSALLY_COMPARABLE_CONTROL':continue
  a=annual[r['build_id'],'FULL_AVAILABLE',r['year']];z=annual[r['CONTROL'],'FULL_AVAILABLE',r['year']]
  for output,key in [('delta_PF','gross_PF'),('delta_R','gross_R'),('delta_CLOSED','CLOSED'),('delta_signals','signals'),('delta_accepted_entries','accepted_entries'),('delta_positive_months','positive_months'),('delta_DD_R','max_DD_R'),('delta_worst_month_R','worst_month_R')]:
   delta=float(a[key])-float(z[key]);assert abs(float(r[output])-delta)<=1e-8,(r['build_id'],output);fields+=1
  year=r['year'];original=[q for q in ledgers[r['CONTROL']] if (year=='ALL' or q['exit_time'][:4]==year) and float(q['gross_R'])>=2]
  key=lambda q:(q['instrument'],q['direction'],q.get('signal_time') or q['entry_time'])
  available={key(q):q for q in ledgers[r['build_id']]}
  assert int(r['CONTROL_winners_ge2'])==len(original)
  assert int(r['ge2_same_signal_retained'])==sum(key(q) in available and float(available[key(q)]['gross_R'])>=2 for q in original)
  assert int(r['ge2_same_signal_lost'])==sum(key(q) not in available for q in original)
  expected=json.loads(r['instrument_R_delta'])
  for symbol,value in expected.items():
   one=math.fsum(float(q['gross_R']) for q in ledgers[r['build_id']] if q['instrument']==symbol and (year=='ALL' or q['exit_time'][:4]==year));two=math.fsum(float(q['gross_R']) for q in ledgers[r['CONTROL']] if q['instrument']==symbol and (year=='ALL' or q['exit_time'][:4]==year))
   assert abs(one-two-value)<=1e-8;fields+=1
  effects+=1
 tables['FILTER_CONTRIBUTION']=effects
 for r in read(folder/'STABILITY_RANKING.csv'):
  for year,key in [('2023','PF_2023'),('2024','PF_2024'),('2025','PF_2025'),('2026','PF_2026_YTD')]:assert abs(float(r[key])-float(annual[r['build_id'],'FULL_AVAILABLE',year]['gross_PF']))<=1e-12;fields+=1
  a=annual[r['build_id'],'FULL_AVAILABLE','ALL']
  for k in ('gross_PF','gross_R','CLOSED','positive_months','max_DD_R','max_negative_month_streak','worst_month_R'):assert abs(float(r[k])-float(a[k]))<=1e-12;fields+=1
  ys=[annual[r['build_id'],'FULL_AVAILABLE',y] for y in ('2023','2024','2025','2026')]
  assert r['annual_minimum_2023_2024']==str(float(ys[0]['gross_PF'])>=1.7 and float(ys[1]['gross_PF'])>=1.7);fields+=1
 tables['STABILITY_RANKING']=len(read(folder/'STABILITY_RANKING.csv'))
 write=(folder/'ARITHMETIC_AUDIT.json');write.write_text(json.dumps(dict(status='PASS',fields_compared=fields,rows_compared=rows,max_numeric_delta=maxdelta,tolerance=1e-8,tables=tables,independence='Stdlib/f-sum arithmetic; no primary reporting/metrics import; same author'),sort_keys=True,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--coverage',type=Path,required=True);a=p.parse_args();audit(a.output,json.loads(a.coverage.read_text()))
