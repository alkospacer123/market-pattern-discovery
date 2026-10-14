"""Fixed WF accounting. All scopes and stresses preregistered, no trading changes."""
from datetime import datetime,timedelta
import math,statistics
import common as C
from primary_metrics import metrics
from scalar_metrics import stats
WF_START=datetime(2025,1,1,tzinfo=C.TZ)
WF_END=datetime(2026,1,1,tzinfo=C.TZ)
MONTHS=[f'2025-{m:02d}' for m in range(1,13)]
SCOPES=('ALL_FOUR',)+C.SYMBOLS
DIRECTIONS=('ALL','LONG','SHORT')

def select(rows,scope,direction):
    return [r for r in rows if (scope=='ALL_FOUR' or r['instrument']==scope) and (direction=='ALL' or r['direction']==direction)]

def ordered(rows):return sorted(rows,key=lambda r:(r['exit_time'],r['instrument'],r['trade_id']))
def cohort(r):return WF_START<=r['signal_time']<WF_END and WF_START<=r['entry_time']<WF_END

def recovery(rows):
    """All drawdown episodes and exact CLOSED-R recovery, starting from 0 R."""
    equity=peak=0.;peak_at=None;episode=None;episodes=[]
    for r in ordered(rows):
        equity+=r['gross_R'];at=r['exit_time']
        if equity>=peak:
            if episode:
                episode.update(recovery_time=at,recovered=True,days_to_recovery=(at-episode['underwater_start']).total_seconds()/86400)
                episodes.append(episode);episode=None
            peak=equity;peak_at=at
        else:
            depth=peak-equity
            if episode is None:episode={'peak_time':peak_at,'underwater_start':at,'peak_R':peak,'max_depth_R':depth,'trough_time':at,'trough_R':equity,'recovery_time':None,'recovered':False,'days_to_recovery':None}
            if depth>episode['max_depth_R']:episode.update(max_depth_R=depth,trough_time=at,trough_R=equity)
    if episode:episodes.append(episode)
    return episodes

def extra(rows):
    t=ordered(rows);hold=[r['holding_minutes'] for r in t];draw=recovery(t)
    worst=max(draw,key=lambda x:x['max_depth_R']) if draw else None
    return {'median_holding_minutes':statistics.median(hold) if hold else None,
        'mean_holding_minutes':statistics.mean(hold) if hold else None,
        'max_DD_recovered':worst['recovered'] if worst else None,
        'max_DD_peak_time':worst['peak_time'] if worst else None,'max_DD_trough_time':worst['trough_time'] if worst else None,
        'max_DD_recovery_time':worst['recovery_time'] if worst else None,'max_DD_days_to_recovery':worst['days_to_recovery'] if worst else None,
        'terminal_underwater_R':draw[-1]['peak_R']-sum(r['gross_R'] for r in t) if draw and not draw[-1]['recovered'] else 0.}

def assess(rows,months):return metrics(rows,months)|extra(rows)

def periods(end):
    result=[('FULL_WF',MONTHS)]
    for q in range(4):
        ms=MONTHS[q*3:q*3+3]
        if ms[-1]<=end:result.append(('W'+str(q+1),ms))
    for q in range(4):
        ms=MONTHS[:q*3+3]
        if ms[-1]<=end:result.append(('CUM_W'+str(q+1),ms))
    result.extend((m,[m]) for m in MONTHS if m<=end)
    if end<'2025-12':result=[(p,[m for m in ms if m<=end]) for p,ms in result]
    return result

def snapshot_months(out,origin,months):
    snapshots={m:[r for r in out['PERIOD_END_OPEN_POSITIONS'] if r['month']==m] for m in months}
    return snapshots

def scenarios(t,months):
    yield 'BASE',t,[],0.
    for s in C.SYMBOLS:yield 'LEAVE_OUT_'+s,[r for r in t if r['instrument']!=s],[],0.
    ranking=sorted(months,key=lambda m:(-sum(r['gross_R'] for r in t if r['exit_time'].strftime('%Y-%m')==m),m))
    for n in (1,3):
        removed=ranking[:n];yield 'EX_BEST'+str(n)+'_MONTHS',[r for r in t if r['exit_time'].strftime('%Y-%m') not in removed],removed,0.
    winners=sorted([r for r in t if r['gross_R']>0],key=lambda r:(-r['gross_R'],r['exit_time'],r['instrument'],r['trade_id']))
    for n in (1,3,5,10):
        keys={(r['instrument'],r['trade_id']) for r in winners[:n]}
        yield 'EX_TOP'+str(n)+'_WINNERS',[r for r in t if (r['instrument'],r['trade_id']) not in keys],[],0.
    for cost in (.05,.1):yield 'R_STRESS_'+str(cost),[r|{'gross_R':r['gross_R']-cost} for r in t],[],cost

def loss_runs(rows,months):
    result=[]
    for kind,sequence in [('TRADE',[(str(r['exit_time'])+'|'+r['instrument']+'|'+r['trade_id'],r['gross_R']) for r in ordered(rows)]),('MONTH',[(m,sum(r['gross_R'] for r in rows if r['exit_time'].strftime('%Y-%m')==m)) for m in months])]:
        run=[]
        for label,value in sequence+[('',0.)]:
            if value<0:run.append((label,value))
            elif run:
                result.append({'type':kind,'start':run[0][0],'end':run[-1][0],'length':len(run),'gross_R':sum(v for _,v in run),'members':' ; '.join(k for k,_ in run)});run=[]
    return result

def build(out,origin,features,receipts):
    closed=[r|{'cohort':'NEW_WF' if cohort(r) else 'INHERITED_DEVELOPMENT'} for r in out['trades'] if r['exit_time']>=WF_START]
    end=(datetime.fromisoformat(receipts[0]['cutoff_end_exclusive'])-timedelta(microseconds=1)).strftime('%Y-%m')
    snapshots=snapshot_months(out,origin,MONTHS)
    tables={k:[] for k in ('summary','monthly','scenario_summary','scenario_ledger','top_winners','loss_runs','drawdown_episodes','marked_monthly','coverage','cohort_ledger','instrument_contributions','direction_contributions','open_monthly','entry_cohorts')}
    comparator=C.Comparison()
    for s in C.SYMBOLS:
        frame=features[s]
        for month in MONTHS:
            if month>end:continue
            b=frame.loc[frame.index.strftime('%Y-%m')==month]
            ready=b.loc[b.H1AvailableAt.notna() & b.ATR.notna() & b.PriorHigh.notna()]
            tables['coverage'].append({'instrument':s,'month':month,'status':'NO_COVERAGE' if b.empty else 'WARMUP_NOT_READY' if ready.empty else 'AVAILABLE','bars':len(b),'indicator_ready_bars':len(ready),'first_close':b.index[0] if len(b) else None,'last_close':b.index[-1] if len(b) else None,'observed_days':len(set(b.index.date))})
    for period,months in periods(end):
        t=[r for r in closed if r['exit_time'].strftime('%Y-%m') in months]
        for group in ('CALENDAR_CLOSED','NEW_WF_COHORT','INHERITED_DEVELOPMENT'):
            g=[r for r in t if group=='CALENDAR_CLOSED' or (cohort(r) if group=='NEW_WF_COHORT' else not cohort(r))]
            for scope in SCOPES:
                for direction in DIRECTIONS:
                    rows=select(g,scope,direction);meta={'period':period,'cohort':group,'scope':scope,'direction':direction}
                    m=assess(rows,months);sm=stats(rows,months)
                    for k,v in sm.items():comparator.value(m[k],v,'INDEPENDENT_ARITHMETIC',str(meta),k)
                    op=select(snapshots.get(months[-1],[]),scope,direction)
                    if group!='CALENDAR_CLOSED':op=[r for r in op if cohort(r)==(group=='NEW_WF_COHORT')]
                    r=meta|m|{'period_end_OPEN':len(op),'period_end_OPEN_marked_R':sum(x['unrealized_gross_R_at_last_close'] for x in op)}
                    tables['summary'].append(r)
                    if period in MONTHS:tables['monthly'].append(r)
                    if group=='CALENDAR_CLOSED':
                        tables['loss_runs'] += [meta|x for x in loss_runs(rows,months)]
                        tables['drawdown_episodes'] += [meta|x for x in recovery(rows)]
            # Full fixed diagnostics on ALL + each instrument, all directions;
            # one-month exclusions also retained, not turned into primary evidence.
            for scope in SCOPES:
                for direction in DIRECTIONS:
                    base=select(g,scope,direction)
                    for scenario,changed,removed,cost in scenarios(base,months):
                        if scenario.startswith('LEAVE_OUT_') and scope!='ALL_FOUR':continue
                        meta={'period':period,'cohort':group,'scope':scope,'direction':direction,'scenario':scenario}
                        m=assess(changed,months);sm=stats(changed,months)
                        for k,v in sm.items():comparator.value(m[k],v,'INDEPENDENT_SCENARIO_ARITHMETIC',str(meta),k)
                        tables['scenario_summary'].append(meta|m|{'excluded_months':','.join(removed),'R_stress_per_CLOSED':cost,'original_CLOSED':len(base),'removed_CLOSED':len(base)-len(changed),'original_OPEN_unchanged':True})
                        if scope=='ALL_FOUR' and period not in MONTHS:
                            changed_keys={(r['instrument'],r['trade_id']):r for r in changed}
                            for row in ordered(base):
                                adjusted=changed_keys.get((row['instrument'],row['trade_id']))
                                tables['scenario_ledger'].append(meta|{'instrument':row['instrument'],'trade_id':row['trade_id'],'exit_time':row['exit_time'],'original_R':row['gross_R'],'diagnostic_R':adjusted['gross_R'] if adjusted else None,'retained':adjusted is not None})
                    wins=sorted([r for r in base if r['gross_R']>0],key=lambda r:(-r['gross_R'],r['exit_time'],r['instrument'],r['trade_id']))
                    for rank,row in enumerate(wins[:10],1):tables['top_winners'].append({'period':period,'cohort':group,'scope':scope,'direction':direction,'rank':rank}|{k:row[k] for k in ('instrument','trade_id','signal_time','entry_time','exit_time','gross_R')})
    for month in MONTHS:
        if month>end:continue
        prev='2024-12' if month=='2025-01' else f'2025-{int(month[-2:])-1:02d}'
        start=origin['OPEN_POSITIONS'] if prev=='2024-12' else snapshots[prev]
        stop=snapshots[month]
        for scope in SCOPES:
            for direction in DIRECTIONS:
                a=select(start,scope,direction);b=select(stop,scope,direction)
                t=select([r for r in closed if r['exit_time'].strftime('%Y-%m')==month],scope,direction)
                realized=sum(r['gross_R'] for r in t);u0=sum(r['unrealized_gross_R_at_last_close'] for r in a);u1=sum(r['unrealized_gross_R_at_last_close'] for r in b)
                tables['marked_monthly'].append({'month':month,'scope':scope,'direction':direction,'CLOSED_R':realized,'U_start_R':u0,'U_end_R':u1,'marked_R':realized+u1-u0,'OPEN_start':len(a),'OPEN_end':len(b),'carried_in_IDs':','.join(r['trade_id'] for r in a),'carried_out_IDs':','.join(r['trade_id'] for r in b),'capital_return':False})
        tables['open_monthly'] += [r|{'month':month} for r in stop]
    # Signal+entry membership is defined inside each reporting interval; exit
    # outcomes are only those known by this sealed replay horizon.
    all_rows=out['trades']+out['OPEN_POSITIONS']
    for period,months in periods(end):
        first=datetime.fromisoformat(months[0]+'-01T00:00:00+03:00')
        y,m=map(int,months[-1].split('-'));last=datetime(y+int(m==12),1 if m==12 else m+1,1,tzinfo=C.TZ)
        members=[r for r in all_rows if first<=r['signal_time']<last and first<=r['entry_time']<last]
        for row in members:
            tables['entry_cohorts'].append({'entry_period':period,'horizon_end_exclusive':receipts[0]['cutoff_end_exclusive'],
                'known_status':'CLOSED' if 'exit_time' in row else 'OPEN','exit_inside_entry_period':first<=row['exit_time']<last if 'exit_time' in row else None,
                'instrument':row['instrument'],'direction':row['direction'],'trade_id':row['trade_id'],'signal_time':row['signal_time'],
                'entry_time':row['entry_time'],'exit_time':row.get('exit_time'),'gross_R':row.get('gross_R'),
                'marked_R':row.get('unrealized_gross_R_at_last_close')})
    tables['cohort_ledger']=closed
    full=[r for r in tables['summary'] if r['period']=='FULL_WF' and r['cohort']=='CALENDAR_CLOSED' and r['direction']=='ALL']
    total=next(r for r in full if r['scope']=='ALL_FOUR')['gross_R']
    for r in full:
        if r['scope']!='ALL_FOUR':tables['instrument_contributions'].append(r|{'share_portfolio_R':r['gross_R']/total if total>0 else None})
    for r in tables['summary']:
        if r['period']=='FULL_WF' and r['cohort']=='CALENDAR_CLOSED' and r['scope']=='ALL_FOUR' and r['direction']!='ALL':tables['direction_contributions'].append(r|{'share_portfolio_R':r['gross_R']/total if total>0 else None})
    assert not comparator.diffs,'ACCOUNTING_MISMATCH'
    return tables,{'status':'PASS','fields_compared':comparator.fields,'differences':len(comparator.diffs),'max_numeric_delta':max(comparator.maxima.values(),default=0),'tolerance':1e-8}

def decide(tables):
    full=[r for r in tables['summary'] if r['period']=='FULL_WF' and r['scope']=='ALL_FOUR' and r['direction']=='ALL' and r['cohort'] in ('CALENDAR_CLOSED','NEW_WF_COHORT')]
    incomplete=[r for r in tables['coverage'] if r['status']!='AVAILABLE']
    if len(tables['coverage'])!=48 or incomplete or any(not r['closed'] or r['gross_PF'] is None for r in full):return {'status':'WF_INSUFFICIENT_EVIDENCE','reason':'Assigned coverage or defined CLOSED evidence insufficient','cells':incomplete}
    if any(r['gross_R']<=0 or r['gross_PF']<=1 or r['expectancy_R']<=0 for r in full):return {'status':'WF_GROSS_EDGE_NOT_CONFIRMED','reason':'Nonpositive full calendar or new WF cohort gross edge','full':full}
    bad=[r for r in tables['summary'] if r['period'] in ('FULL_WF','W1','W2','W3','W4') and r['cohort'] in ('CALENDAR_CLOSED','NEW_WF_COHORT') and r['gross_R']<=0 and r['closed']>0]
    bad += [r for r in tables['scenario_summary'] if r['period'] in ('FULL_WF','W1','W2','W3','W4') and r['cohort'] in ('CALENDAR_CLOSED','NEW_WF_COHORT') and r['gross_R']<=0 and r['original_CLOSED']>0]
    return {'status':'WF_MIXED' if bad else 'WF_REVIEW_REQUIRED','blocking_or_limiting_cells':bad,'automatic_PASS':False,'TRUE_OOS_authorized':False,'LIVE_authorized':False,'external_human_review':'PENDING'}
