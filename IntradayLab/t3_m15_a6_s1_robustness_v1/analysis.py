"""Fixed arithmetic diagnostics on unchanged CLOSED trajectories. No replay imports."""
import numpy as np
import common as C
from primary_metrics import metrics

DIRECTIONS=('ALL','LONG','SHORT')
PERIODS=('2023','2024','ALL')
SCOPES=('ALL_FOUR',)+C.SYMBOLS

def calendar(year):
    return [m for m in C.CALENDAR if year=='ALL' or m.startswith(year)]

def subset(rows,scope,direction,year):
    return [r for r in rows if (scope=='ALL_FOUR' or r['instrument']==scope)
            and (direction=='ALL' or r['direction']==direction)
            and (year=='ALL' or str(r['exit_time'].year)==year)]

def ordered(rows):
    return sorted(rows,key=lambda r:(r['exit_time'],r['instrument'],r['trade_id']))

def coverage(scope,month):
    sources=__import__('json').loads((C.HERE/'SPEC.json').read_text())['sources']
    first=min(s['first_close'][:7] for s in sources if scope=='ALL_FOUR' or s['instrument']==scope)
    return 'NO_COVERAGE' if month<first else 'AVAILABLE_PARTIAL_START' if month==first and scope in ('GLDRUBF','IMOEXF') else 'AVAILABLE'

def additional(rows,months,excluded_months=()):
    m=metrics(rows,months)
    m.update(retained_calendar_months=len(months)-len(set(months)&set(excluded_months)),
             no_coverage_months=sum(coverage('ALL_FOUR',x)=='NO_COVERAGE' for x in months))
    m['positive_fraction_calendar']=m['positive_months']/len(months)
    m['positive_fraction_retained']=m['positive_months']/m['retained_calendar_months'] if m['retained_calendar_months'] else None
    return m

def monthly(rows,months,meta,excluded_months=()):
    out=[]
    for month in months:
        t=[r for r in rows if r['exit_time'].strftime('%Y-%m')==month]
        c=coverage(meta['scope'],month)
        out.append(meta|{'month':month,'coverage':c,'status':'DIAGNOSTIC_MONTH_REMOVED' if month in excluded_months else c if c=='NO_COVERAGE' else 'AVAILABLE_WITH_CLOSED' if t else 'AVAILABLE_NO_CLOSED'}|metrics(t,[month]))
    return out

def loss_runs(rows,months,meta):
    out=[]
    for kind,sequence in [('CLOSED_TRADES',[(r['exit_time'].isoformat()+'|'+r['instrument']+'|'+r['trade_id'],r['gross_R']) for r in ordered(rows)]),
                          ('CALENDAR_MONTHS',[(m,sum(r['gross_R'] for r in rows if r['exit_time'].strftime('%Y-%m')==m)) for m in months])]:
        run=[]
        for item in sequence+[('',0.)]:
            if item[1]<0:run.append(item)
            elif run:
                out.append(meta|{'series_type':kind,'start':run[0][0],'end':run[-1][0],'length':len(run),'gross_R':sum(v for _,v in run),'members':';'.join(k for k,_ in run)});run=[]
    return out

def scenarios(rows):
    """No combined scenarios. Rank frozen outcomes locally in each assessment period."""
    for year in PERIODS:
        for direction in DIRECTIONS:
            base=subset(rows,'ALL_FOUR',direction,year)
            months=calendar(year)
            for symbol in C.SYMBOLS:
                yield 'LEAVE_OUT_'+symbol,'ALL_FOUR',direction,year,base,[r for r in base if r['instrument']!=symbol],[],0.
            rank=sorted(months,key=lambda m:(-sum(r['gross_R'] for r in base if r['exit_time'].strftime('%Y-%m')==m),m))
            for n in (1,3):
                removed=rank[:n]
                yield 'EX_BEST'+str(n)+'_MONTHS','ALL_FOUR',direction,year,base,[r for r in base if r['exit_time'].strftime('%Y-%m') not in removed],removed,0.
            removed=['2024-11'] if '2024-11' in months else []
            yield 'EX_NOV2024','ALL_FOUR',direction,year,base,[r for r in base if r['exit_time'].strftime('%Y-%m') not in removed],removed,0.
            wins=sorted([r for r in base if r['gross_R']>0],key=lambda r:(-r['gross_R'],r['exit_time'],r['instrument'],r['trade_id']))
            for n in (1,3,5,10):
                keys={(r['instrument'],r['trade_id']) for r in wins[:n]}
                yield 'EX_TOP'+str(n)+'_WINNERS','ALL_FOUR',direction,year,base,[r for r in base if (r['instrument'],r['trade_id']) not in keys],[],0.
            for scope in SCOPES:
                base=subset(rows,scope,direction,year)
                for level in (0.05,0.10):
                    yield 'R_STRESS_'+('005' if level==0.05 else '010'),scope,direction,year,base,[r|{'gross_R':r['gross_R']-level} for r in base],[],level

def build(out):
    rows=out['trades'];tables={k:[] for k in ('summary','monthly','loss_runs','scenario_summary','scenario_monthly','scenario_ledger','top_winners','november2024')}
    for scope in SCOPES:
        for direction in DIRECTIONS:
            for year in PERIODS:
                t=subset(rows,scope,direction,year);months=calendar(year);meta={'scope':scope,'direction':direction,'year':year}
                op=out['OPEN_POSITIONS'] if year=='ALL' else [r for r in out['PERIOD_END_OPEN_POSITIONS'] if r['month']==year+'-12']
                count=sum((scope=='ALL_FOUR' or r['instrument']==scope) and (direction=='ALL' or r['direction']==direction) for r in op)
                m=additional(t,months);m['no_coverage_months']=sum(coverage(scope,x)=='NO_COVERAGE' for x in months)
                total=metrics(subset(rows,'ALL_FOUR',direction,year),months)['gross_R']
                tables['summary'].append(meta|m|{'period_end_OPEN':count,'share_portfolio_net_R':m['gross_R']/total if total>0 else None})
                tables['loss_runs']+=loss_runs(t,months,meta)
            tables['monthly']+=monthly(subset(rows,scope,direction,'ALL'),C.CALENDAR,{'scope':scope,'direction':direction,'year':'ALL'})
            nov=[r for r in subset(rows,scope,direction,'2024') if r['exit_time'].month==11]
            y=metrics(subset(rows,scope,direction,'2024'),C.CALENDAR[12:]);n=metrics(nov,['2024-11'])
            tables['november2024'].append({'scope':scope,'direction':direction}|n|{'share_2024_net_R':n['gross_R']/y['gross_R'] if y['gross_R']>0 else None})
    for kind,scope,direction,year,base,changed,excluded,stress in scenarios(rows):
        meta={'scenario':kind,'scope':scope,'direction':direction,'year':year};months=calendar(year)
        m=additional(changed,months,excluded);m['no_coverage_months']=sum(coverage(scope,x)=='NO_COVERAGE' for x in months)
        bm=metrics(base,months);removed_R=bm['gross_R']-m['gross_R'];removed_count=len(base)-len(changed)
        tables['scenario_summary'].append(meta|m|{'original_closed':len(base),'removed_closed':removed_count,'removed_or_stressed_R':removed_R,
            'removed_share_original_net_R':removed_R/bm['gross_R'] if bm['gross_R']>0 else None,
            'removed_share_original_positive_R':removed_R/bm['positive_R'] if bm['positive_R']>0 else None,
            'excluded_months':','.join(excluded),'R_stress_per_CLOSED':stress,'original_OPEN_unchanged':True})
        tables['scenario_monthly']+=monthly(changed,months,meta,excluded)
        changed_by_id={(r['instrument'],r['trade_id']):r for r in changed}
        for r in ordered(base):
            cr=changed_by_id.get((r['instrument'],r['trade_id']))
            tables['scenario_ledger'].append(meta|{'instrument':r['instrument'],'trade_id':r['trade_id'],'exit_time':r['exit_time'],
                'original_R':r['gross_R'],'diagnostic_R':cr['gross_R'] if cr else None,'retained':cr is not None})
    for year in PERIODS:
        for direction in DIRECTIONS:
            wins=sorted([r for r in subset(rows,'ALL_FOUR',direction,year) if r['gross_R']>0],key=lambda r:(-r['gross_R'],r['exit_time'],r['instrument'],r['trade_id']))
            for rank,r in enumerate(wins[:10],1):
                tables['top_winners'].append({'year':year,'direction':direction,'rank':rank}|{k:r[k] for k in ('instrument','trade_id','signal_time','entry_time','exit_time','gross_R')}|{'exit_month':r['exit_time'].strftime('%Y-%m')})
    return tables
