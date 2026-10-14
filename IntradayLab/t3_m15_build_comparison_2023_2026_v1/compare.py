"""Closed-ledger descriptive subsets of complete causal replays, no new rules."""
import argparse,json,itertools,math
from datetime import datetime
from pathlib import Path
from collections import Counter
from registry import builds,SYMBOLS,CUTOFF,HERE
from io_utils import read_csv,write_csv,write_json
from metrics import stats

def calendar(start,end):
 y,m=int(start[:4]),int(start[5:7]);out=[]
 while f'{y:04d}-{m:02d}'<=end[:7]:
  out.append(f'{y:04d}-{m:02d}');m+=1
  if m==13:y+=1;m=1
 return out
def load_trades(out,b):
 rows=read_csv(out/'journals'/b['build_id']/'trades.csv.gz')
 for r in rows:r['gross_R']=float(r['gross_R'])
 return rows
def choose(rows,symbols,view,year,coverage):
 a,z=coverage['views'][view]['start'],coverage['views'][view]['end_exclusive']
 common=coverage['common_set']
 return [r for r in rows if r['instrument'] in symbols and a<=r['exit_time']<z and (year=='ALL' or r['exit_time'][:4]==year)
  and (view!='COMMON_OBSERVED' or r.get('exit_bar_close_time',r['exit_time']) in common)]
def coverage_for(coverage,symbols,months,view):
 a,z=coverage['views'][view]['start'],coverage['views'][view]['end_exclusive'];details=[]
 for m in months:
  counts={s:sum(a<=t<z and t[:7]==m and (view!='COMMON_OBSERVED' or t in coverage['common_set']) for t in coverage['times'][s]) for s in symbols}
  state='NO_COVERAGE' if not any(counts.values()) else 'PARTIAL_INSTRUMENT_COVERAGE' if not all(counts.values()) else 'AVAILABLE_SOURCE_PREFIX'
  # These flags concern source endpoints, not a certified exchange calendar.
  if state!='NO_COVERAGE' and (m=='2026-08' or m=='2026-09' or (m=='2023-07' and 'GLDRUBF' in symbols) or (m=='2023-11' and 'IMOEXF' in symbols)):state+=';INCOMPLETE_ENDPOINT_MONTH'
  details.append(dict(month=m,status=state,counts=counts))
 return details
def enrich(met,selected,allrows,terminal,entries,coverage,symbols,months,view,year):
 a,z=coverage['views'][view]['start'],coverage['views'][view]['end_exclusive']
 if year!='ALL':a=max(a,year+'-01-01T00:00:00+03:00');z=min(z,str(int(year)+1)+'-01-01T00:00:00+03:00')
 c=coverage_for(coverage,symbols,months,view);covered=sum(x['status']!='NO_COVERAGE' for x in c)
 quarter_months=[m for m in months if m[:4]+'-Q'+str((int(m[-2:])-1)//3+1)==met['worst_quarter']]
 quarter_status='PARTIAL_SOURCE_OR_WINDOW' if len(quarter_months)!=3 or any('INCOMPLETE' in x['status'] or 'NO_COVERAGE' in x['status'] for x in c if x['month'] in quarter_months) else 'AVAILABLE_SOURCE_HISTORY_NOT_CALENDAR_CERTIFICATION'
 e=[r for r in entries if r['instrument'] in symbols and a<=r['signal_time']<z]
 reasons=Counter(r.get('decision_reason') or r.get('outcome') or ('ACCEPTED' if r.get('entry_accepted')=='True' else 'FILTER_FAILED' if r.get('rule_pass')=='False' else 'POSITION_OCCUPIED') for r in e if r.get('entry_accepted')!='True')
 def open_at(t):return sum(r['instrument'] in symbols and r['entry_time']<t and r['exit_time']>=t for r in allrows)+sum(r['instrument'] in symbols and r['entry_time']<t for r in terminal)
 return met|dict(covered_months=covered,no_coverage_months=len(months)-covered,positive_share_covered=met['positive_months']/covered if covered else None,
  OPEN_at_start=open_at(a),OPEN_at_end=open_at(z),inherited_CLOSED=sum(r['entry_time']<a for r in selected),signals=len(e),accepted_entries=sum(r.get('entry_accepted')=='True' for r in e),
  rejected_signals=sum(reasons.values()),rejection_reasons=json.dumps(dict(sorted(reasons.items())),sort_keys=True),
  pending_at_end=sum(r.get('pending_at_end')=='True' for r in e),worst_quarter_coverage=quarter_status,coverage=';'.join(sorted({x['status'] for x in c})),
  descriptive_pooled_Gross_R=True,GROSS_ONLY=True,classification='POST_HOC_COMPARISON')

def run(out,coverage):
 configs=builds();subsets=[x for n in range(1,5) for x in itertools.combinations(SYMBOLS,n)]
 annual=[];monthly=[];portfolio=[];instrument=[];lookup={};loaded={};allcontrib=[]
 for b in configs:
  bid=b['build_id'];rows=load_trades(out,b);loaded[bid]=rows
  folder=out/'journals'/bid;op=read_csv(folder/'OPEN.csv.gz');entries=read_csv(folder/'entries.csv.gz')
  for view,window in coverage['views'].items():
   months=calendar(window['start'],window['end_exclusive']);months=[m for m in months if m+'-01T00:00:00+03:00'<window['end_exclusive']]
   years=sorted({m[:4] for m in months})+['ALL']
   for symbols in subsets:
    scope='N'+str(len(symbols))+':'+'+'.join(symbols)
    for year in years:
     cal=months if year=='ALL' else [m for m in months if m[:4]==year]
     selected=choose(rows,symbols,view,year,coverage)
     met=enrich(stats(selected,cal),selected,rows,op,entries,coverage,symbols,cal,view,year)
     item=dict(build_id=bid,mode=b['mode'],view=view,year=year,scope=scope,instruments=';'.join(symbols),**met);portfolio.append(item)
     if len(symbols)==4:annual.append(item);lookup[bid,view,year]=item
     if len(symbols)==1:
      instrument.append(item|dict(direction='BOTH'))
      for side in ('LONG','SHORT'):
       sr=[r for r in selected if r['direction']==side];instrument.append(dict(build_id=bid,mode=b['mode'],view=view,year=year,instrument=symbols[0],direction=side,**stats(sr,cal)))
    # Full calendar monthly ledgers of all 15 subsets in every view.
    cov=coverage_for(coverage,symbols,months,view)
    for c in cov:
     m=c['month'];sr=[r for r in choose(rows,symbols,view,'ALL',coverage) if r['exit_time'][:7]==m]
     monthly.append(dict(build_id=bid,view=view,scope=scope,instruments=';'.join(symbols),month=m,coverage=c['status'],bars=json.dumps(c['counts'],sort_keys=True),**stats(sr,[m])))
  print('METRICS',bid,flush=True)
 # Paired effects within the exact same frozen execution/initial/trail control.
 def find(rule,trail,mode,exclude_early=True):
  return next((q for q in configs if q['rule']==rule and q['trail']==trail and q['mode']==mode and (not exclude_early or q['version']!='EARLY_PROTECT_05')),None)
 for b in configs:
  controls=[]
  if b['mode']=='SIGNAL_CLOSE' and b['rule']!='CONTROL':
   controls=[('single_mechanism',find('CONTROL',b['trail'],b['mode']))]
   if b['rule'] in ('C1','C2'):controls=[('exit_S1',find('A6' if b['rule']=='C1' else 'A7',b['trail'],b['mode'])),('entry_'+b['entry'],find('S1',b['trail'],b['mode']))]
   if b['rule']=='COMBINED':controls=[('exit_S1',find('T1',b['trail'],b['mode'])),('entry_T1',find('S1',b['trail'],b['mode']))]
  if b['mode']=='NEXT_OPEN':
   if b['rule']=='COMBINED':controls=[('exit_S1',find('T1',b['trail'],'NEXT_OPEN'))]
   if b['rule']=='C1' and b['trail'] not in (3.,3.5):controls=[('trailing_only',find('C1',3.5,'NEXT_OPEN'))]
   if b['version']=='EARLY_PROTECT_05':controls=[('early_protection',find('C1',3.75,'NEXT_OPEN'))]
   controls.append(('execution_change',find(b['rule'],b['trail'],'SIGNAL_CLOSE')))
  for effect,c in controls:
   if c is None or c['build_id']==b['build_id']:continue
   for y in ('2023','2024','2025','2026','ALL'):
    a=lookup[b['build_id'],'FULL_AVAILABLE',y];z=lookup[c['build_id'],'FULL_AVAILABLE',y]
    key=lambda r:(r['instrument'],r['direction'],r.get('signal_time') or r['entry_time'])
    original=[r for r in loaded[c['build_id']] if y=='ALL' or r['exit_time'][:4]==y]
    large=[r for r in original if r['gross_R']>=2];matched={key(r):r for r in loaded[b['build_id']]}
    allcontrib.append(dict(build_id=b['build_id'],CONTROL=c['build_id'],effect=effect,year=y,delta_PF=a['gross_PF']-z['gross_PF'] if a['gross_PF'] is not None and z['gross_PF'] is not None else None,
     delta_R=a['gross_R']-z['gross_R'],delta_CLOSED=a['CLOSED']-z['CLOSED'],delta_signals=a['signals']-z['signals'],delta_accepted_entries=a['accepted_entries']-z['accepted_entries'],
     delta_positive_months=a['positive_months']-z['positive_months'],delta_DD_R=a['max_DD_R']-z['max_DD_R'],delta_worst_month_R=a['worst_month_R']-z['worst_month_R'],
     CONTROL_winners_ge2=len(large),ge2_same_signal_retained=sum(key(r) in matched and matched[key(r)]['gross_R']>=2 for r in large),ge2_same_signal_lost=sum(key(r) not in matched for r in large),
     instrument_R_delta=json.dumps({s:sum(r['gross_R'] for r in loaded[b['build_id']] if r['instrument']==s and (y=='ALL' or r['exit_time'][:4]==y))-sum(r['gross_R'] for r in original if r['instrument']==s) for s in SYMBOLS},sort_keys=True),
     interpretation='Whole replay; matched signals descriptive only, not subtraction of losing trades'))
  if b['mode']=='NEXT_OPEN' and b['rule']=='C1':
   for effect in ('entry_A6_alone','exit_S1_alone'):
    allcontrib.append(dict(build_id=b['build_id'],CONTROL='NOT_TESTED',effect=effect,year='ALL',status='MISSING_CAUSALLY_COMPARABLE_CONTROL',interpretation='No previously frozen standalone NEXT_OPEN control at this trail; do not infer isolated effect from SIGNAL_CLOSE or invent combination'))
 # No weighted score or fitted 2026 PASS. Rank reproducible NEXT_OPEN by the
 # predeclared lexicographic priorities, keeping all weaknesses visible.
 ranks=[]
 for b in configs:
  ys=[lookup[b['build_id'],'FULL_AVAILABLE',y] for y in ('2023','2024','2025','2026')];a=lookup[b['build_id'],'FULL_AVAILABLE','ALL']
  ranks.append(dict(build_id=b['build_id'],mode=b['mode'],admission=b['admission'],annual_minimum_2023_2024=ys[0]['gross_PF']>=1.7 and ys[1]['gross_PF']>=1.7,
   PF_2023=ys[0]['gross_PF'],PF_2024=ys[1]['gross_PF'],PF_2025=ys[2]['gross_PF'],PF_2026_YTD=ys[3]['gross_PF'],min_year_PF=min(y['gross_PF'] for y in ys),
   positive_years=sum(y['gross_R']>0 for y in ys),positive_months=a['positive_months'],covered_months=a['covered_months'],calendar_months=a['calendar_months'],
   min_year_positive_month_share=min(y['positive_months']/y['covered_months'] for y in ys),worst_month_R=a['worst_month_R'],max_negative_month_streak=a['max_negative_month_streak'],
   max_DD_R=a['max_DD_R'],max_loss_streak=a['max_loss_streak'],max_year_best_month_share=max((y['best_month_share_R'] for y in ys if y['best_month_share_R'] is not None),default=None),max_year_top3_month_share=max((y['top3_month_share_R'] for y in ys if y['top3_month_share_R'] is not None),default=None),
   max_year_instrument_share=max((y['best_instrument_share_R'] for y in ys if y['best_instrument_share_R'] is not None),default=None),gross_PF=a['gross_PF'],gross_R=a['gross_R'],expectancy_R=a['expectancy_R'],CLOSED=a['CLOSED'],
   R_without_top10_trades=a['R_without_top10_trades'],PF_without_top10_trades=a['PF_without_top10_trades'],classification='POST_HOC_COMPARISON'))
 def priority(r):return (-r['positive_years'],-r['min_year_positive_month_share'],-r['positive_months'],r['max_negative_month_streak'],-r['worst_month_R'],r['max_DD_R'],r['max_year_top3_month_share'] if r['max_year_top3_month_share'] is not None else math.inf,r['max_year_instrument_share'] if r['max_year_instrument_share'] is not None else math.inf,-r['CLOSED'],-r['min_year_PF'])
 causal=sorted([r for r in ranks if r['mode']=='NEXT_OPEN'],key=priority);diag=sorted([r for r in ranks if r['mode']=='SIGNAL_CLOSE'],key=priority)
 for category,rs in [('CAUSAL_NEXT_OPEN',causal),('IDEALIZED_SIGNAL_CLOSE',diag)]:
  for i,r in enumerate(rs,1):r.update(rank=i,ranking_group=category,reason='Years positive; worst annual month share; positive months; losing-month run; worst month; DD; concentration; sample; PF. No 2026 mechanical PASS.')
 for n,rs in [('ANNUAL_COMPARISON',annual),('MONTHLY_COMPARISON',monthly),('PORTFOLIO_SUBSETS',portfolio),('INSTRUMENT_COMPARISON',instrument),('FILTER_CONTRIBUTION',allcontrib),('STABILITY_RANKING',causal+diag)]:write_csv(out/(n+'.csv'),rs)
 write_json(out/'RANKING_POLICY.json',dict(classification='POST_HOC_COMPARISON',weighted_score=False,new_2026_PASS=False,ordering='positive years; minimum annual covered-month positive fraction; total positive months; negative-month run; worst month; DD; concentration; sample; minimum PF',primary_group='CAUSAL_NEXT_OPEN',diagnostics='SIGNAL_CLOSE separate; not eligible causal winners',annual_roadmap_minimum='PF>=1.70 separately 2023/2024, shown as existing research gate; not LIVE permission'))
 return causal,diag

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--coverage',type=Path,required=True);a=p.parse_args();c=json.loads(a.coverage.read_text());c['common_set']=set(c['common_set']);run(a.output,c)
