"""Separate stdlib features, dictionary position machine and scalar accounting.

Imports neither primary engine nor primary reporting/metrics. Shared common
functions supply source pins, integrity, constants, serialization/comparison.
"""
import argparse,csv,json,math,statistics
from pathlib import Path
import common as C
import scalar as S

def read(path):
    return json.loads(path.read_text()) if path.suffix=='.json' else list(csv.DictReader(path.open()))

def stats(rows,calendar):
    rows=sorted(rows,key=lambda r:(r['exit_time'],r['instrument'],r['trade_id']))
    values=[r['gross_R'] for r in rows];p=math.fsum(v for v in values if v>0);l=-math.fsum(v for v in values if v<0)
    total=math.fsum(values);month_R={m:math.fsum(r['gross_R'] for r in rows if r['exit_time'].strftime('%Y-%m')==m) for m in calendar}
    eq=peak=dd=0.;streak=maxstreak=0
    for v in values:
        eq+=v;peak=max(eq,peak);dd=max(dd,peak-eq);streak=streak+1 if v<0 else 0;maxstreak=max(maxstreak,streak)
    run=maxrun=0
    for m in calendar:run=run+1 if month_R[m]<0 else 0;maxrun=max(maxrun,run)
    worst=min(calendar,key=lambda m:month_R[m]) if calendar else None
    out={'closed':len(values),'gross_PF':p/l if l else None,'gross_R':total,'expectancy_R':total/len(values) if values else None,
        'positive_R':p,'negative_R':l,'positive_months':sum(v>0 for v in month_R.values()),'negative_months':sum(v<0 for v in month_R.values()),
        'zero_months':sum(v==0 for v in month_R.values()),'months':len(calendar),'worst_month':worst,'worst_month_R':month_R.get(worst),
        'max_negative_month_run':maxrun,'closed_R_drawdown':dd,'max_losing_trade_run':maxstreak}
    rank=sorted(calendar,key=lambda m:(-month_R[m],m))
    for n in (1,3):
        selected=set(rank[:n]);v=math.fsum(month_R[m] for m in selected)
        remaining=[r['gross_R'] for r in rows if r['exit_time'].strftime('%Y-%m') not in selected]
        plus=math.fsum(v for v in remaining if v>0);minus=-math.fsum(v for v in remaining if v<0)
        out.update({f'top{n}_months':','.join(rank[:n]),f'top{n}_months_R':v,f'top{n}_share_annual_R':v/total if total>0 else None,
            f'ex_top{n}_PF':plus/minus if minus else None,f'ex_top{n}_R':math.fsum(remaining)})
    winners=sorted((v for v in values if v>0),reverse=True)
    for n in (5,10):
        v=math.fsum(winners[:n]);out.update({f'top{n}_winners_R':v,f'top{n}_share_positive_R':v/p if p else None,
            f'ex_top{n}_winners_PF':(p-v)/l if l else None,f'ex_top{n}_winners_R':total-v})
    return out

def matches(r,target):
    return (r['rule']==target['rule'] and r['version']==target['version'] and
        ('mode' not in target or r['mode']==target['mode']) and
        ('scope' not in target or target['scope']=='ALL_FOUR' or r['instrument']==target['scope']) and
        ('direction' not in target or target['direction']=='ALL' or r['direction']==target['direction']))

def run(root,primary,output):
    output.mkdir(parents=True,exist_ok=True);cmp=C.Comparison();frames,sources=C.load_sources(root)
    allrows={name:[] for name in ('trades','OPEN_POSITIONS','stop_decisions','entry_opportunities','observed_gaps','PERIOD_END_OPEN_POSITIONS')}
    for mode,folder in [('SIGNAL_CLOSE','signal_close'),('NEXT_OPEN','next_open')]:
        out={name:[] for name in allrows}
        for version in C.VERSIONS:
            for rule in ('C1','T1','COMBINED'):
                for symbol in C.SYMBOLS:
                    result=S.simulate(frames[symbol],symbol,version,rule,mode)
                    for name,rows in zip(out,result):out[name].extend(([rows] if rows else []) if name=='OPEN_POSITIONS' else rows)
        for name,rows in out.items():
            expected=read(primary/folder/(name+('.json' if 'POSITIONS' in name else '.csv')))
            keys=['version','rule','instrument']+(['trade_id'] if name in ('trades','OPEN_POSITIONS') else ['bar_close_time'] if name=='stop_decisions' else ['signal_time'] if name=='entry_opportunities' else ['current_close'] if name=='observed_gaps' else ['month'])
            fields=set(k for r in expected for k in r)
            actual=[{k:r.get(k) for k in fields} for r in rows]
            cmp.rows(actual,expected,mode+'_'+name,keys)
            allrows[name].extend(rows)
    t=allrows['trades'];op=allrows['OPEN_POSITIONS'];sn=allrows['PERIOD_END_OPEN_POSITIONS'];entries=allrows['entry_opportunities'];stops=allrows['stop_decisions']
    for name in ('summary','monthly'):
        expected=read(primary/(name+'.csv'))
        for i,row in enumerate(expected):
            selected=[r for r in t if matches(r,row)]
            calendar=C.CALENDAR
            if name=='summary':
                if row['year']!='ALL':selected=[r for r in selected if str(r['exit_time'].year)==row['year']];calendar=[m for m in C.CALENDAR if m.startswith(row['year'])]
            else:selected=[r for r in selected if r['exit_time'].strftime('%Y-%m')==row['month']];calendar=[row['month']]
            actual=stats(selected,calendar)
            for field,value in actual.items():cmp.value(value,row[field],name,i,field)
            if name=='summary':
                openrows=op if row['year']=='ALL' else [r for r in sn if r['month']==row['year']+'-12']
                cmp.value(sum(matches(r,row) for r in openrows),row['period_end_OPEN'],name,i,'period_end_OPEN')
            else:
                symbols=C.SYMBOLS if row['scope']=='ALL_FOUR' else (row['scope'],)
                first=min(frames[s][0]['at'] for s in symbols).strftime('%Y-%m')
                coverage='NO_COVERAGE' if row['month']<first else 'AVAILABLE_PARTIAL_START' if row['month']==first and row['scope'] in ('GLDRUBF','IMOEXF') else 'AVAILABLE'
                cmp.value(coverage,row['coverage'],name,i,'coverage')
    for i,row in enumerate(read(primary/'funnel_occupancy.csv')):
        ee=[r for r in entries if matches(r,row) and (row['year']=='ALL' or str(r['signal_time'].year)==row['year'])]
        dd=[r for r in stops if matches(r,row) and (row['year']=='ALL' or str(r['bar_close_time'].year)==row['year'])]
        symbols=C.SYMBOLS if row['scope']=='ALL_FOUR' else (row['scope'],)
        denom=sum(sum(row['year']=='ALL' or str(b['at'].year)==row['year'] for b in frames[s][1:]) for s in symbols)
        actual={'signals':len(ee),'executed_entries':sum(r['entry_accepted'] for r in ee),'filtered':sum(not r['rule_pass'] for r in ee),
            'occupied_allowed_signals':sum(r['rule_pass'] and r['position_occupied'] for r in ee),'missing_adjacent_open':sum(r['decision_reason']=='SKIPPED_MISSING_ADJACENT_OPEN' for r in ee),
            'unresolved_pending':sum(r['decision_reason']=='UNRESOLVED_END_OF_DATA' for r in ee),'occupied_observed_bars':len(dd),'observed_bar_denominator':denom,'occupancy_share':len(dd)/denom if denom else None}
        actual['partition_PASS']=actual['signals']==sum(actual[k] for k in ('executed_entries','filtered','occupied_allowed_signals','missing_adjacent_open','unresolved_pending'))
        for k,v in actual.items():cmp.value(v,row[k],'funnel_occupancy',i,k)
    key=lambda r:(r['rule'],r['version'],r['instrument'],r['direction'],r['signal_time'].isoformat())
    originals={key(r):r for r in t+op if r['mode']=='SIGNAL_CLOSE'};next_t={key(r):r for r in t if r['mode']=='NEXT_OPEN'};next_o={key(r):r for r in op if r['mode']=='NEXT_OPEN'}
    actual_lineage=[]
    for row in read(primary/'lineage.csv'):
        k=(row['rule'],row['version'],row['instrument'],row['direction'],row['signal_time'])
        original=originals[k];n=next_t.get(k);o=next_o.get(k)
        status='PRESERVED_R' if n and 'gross_R' in original and n['gross_R']>=original['gross_R']-1e-8 else 'CHANGED_R' if n else 'TERMINAL_OPEN' if o else 'LOST_ENTRY'
        decision=next(r for r in entries if r['mode']=='NEXT_OPEN' and r['rule']==row['rule'] and r['version']==row['version'] and r['instrument']==row['instrument'] and r['signal_time'].isoformat()==row['signal_time'])
        actual={'status':status,'original_R':original.get('gross_R'),'next_R':n.get('gross_R') if n else None,'R_change':n['gross_R']-original['gross_R'] if n and 'gross_R' in original else None,
            'decision_reason':decision['decision_reason'],'next_entry_price':(n or o or {}).get('entry_price'),'original_entry_price':original['entry_price'],'exit_time_changed':n['exit_time']!=original.get('exit_time') if n else None,
            'original_status':'CLOSED' if 'gross_R' in original else 'OPEN','original_exit_year':original['exit_time'].year if 'exit_time' in original else None}
        for f,v in actual.items():cmp.value(v,row[f],'lineage',str(k),f)
        actual_lineage.append(row|actual)
    for i,row in enumerate(read(primary/'winner_retention.csv')):
        selected=[r for r in actual_lineage if r['version']==row['version'] and r['rule']==row['rule'] and r['original_status']=='CLOSED' and r['original_R']>=float(row['threshold_R']) and (row['year']=='ALL' or str(r['original_exit_year'])==row['year'])]
        actual={'original_winners':len(selected),'preserved_or_improved_R':sum(r['status']=='PRESERVED_R' for r in selected),'changed_R':sum(r['status']=='CHANGED_R' for r in selected),
            'lost_entry':sum(r['status']=='LOST_ENTRY' for r in selected),'terminal_OPEN':sum(r['status']=='TERMINAL_OPEN' for r in selected),
            'still_at_threshold':sum(r['next_R'] is not None and r['next_R']>=float(row['threshold_R']) for r in selected),'matched_below_threshold':sum(r['next_R'] is not None and r['next_R']<float(row['threshold_R']) for r in selected),
            'matched_nonpositive':sum(r['next_R'] is not None and r['next_R']<=0 for r in selected)}
        for f,v in actual.items():cmp.value(v,row[f],'winner_retention',i,f)
    for i,row in enumerate(read(primary/'november.csv')):
        year=[r for r in t if matches(r,row) and r['exit_time'].year==2024];nov=[r for r in year if r['exit_time'].month==11];ex=[r for r in year if r['exit_time'].month!=11]
        a=stats(year,C.CALENDAR[12:]);b=stats(ex,[m for m in C.CALENDAR[12:] if m!='2024-11']);nr=math.fsum(r['gross_R'] for r in nov)
        vals={'november_closed':len(nov),'november_R':nr,'november_share_2024_R':nr/a['gross_R'] if a['gross_R']>0 else None,'ex_november_PF':b['gross_PF'],'ex_november_R':b['gross_R'],'ex_november_DD':b['closed_R_drawdown'],'november_best_month':a['top1_months']=='2024-11'}
        for f,v in vals.items():cmp.value(v,row[f],'november',i,f)
    for i,row in enumerate(read(primary/'entry_price_sensitivity.csv')):
        selected=[r for r in t+op if matches(r,row) and r['mode']=='NEXT_OPEN' and (row['year']=='ALL' or str(r['signal_time'].year)==row['year'])]
        dev=[(1 if r['direction']=='LONG' else -1)*(r['entry_price']-r['signal_close'])/r['initial_risk'] for r in selected]
        vals={'executed_entries':len(dev),'mean_signed_entry_deviation_R':statistics.mean(dev) if dev else None,'median_signed_entry_deviation_R':statistics.median(dev) if dev else None,'mean_absolute_entry_deviation_R':statistics.mean(map(abs,dev)) if dev else None,
            'worse_price_count':sum(v>0 for v in dev),'better_price_count':sum(v<0 for v in dev),'same_price_count':sum(v==0 for v in dev),'not_a_PnL_attribution':True}
        for f,v in vals.items():cmp.value(v,row[f],'entry_price_sensitivity',i,f)
    for i,row in enumerate(read(primary/'comparison.csv')):
        lookup=lambda mode,year:stats([r for r in t if matches(r,row) and r['mode']==mode and (year=='ALL' or r['exit_time'].year==year)],C.CALENDAR if year=='ALL' else [m for m in C.CALENDAR if m.startswith(str(year))])
        c=lookup('SIGNAL_CLOSE','ALL');n=lookup('NEXT_OPEN','ALL');a=lookup('NEXT_OPEN',2023);b=lookup('NEXT_OPEN',2024)
        vals={'Close_PF':c['gross_PF'],'Next_PF':n['gross_PF'],'Close_R':c['gross_R'],'Next_R':n['gross_R'],'delta_R':n['gross_R']-c['gross_R'],
            'PF2023':a['gross_PF'],'PF2024':b['gross_PF'],'positive_Close':c['positive_months'],'positive_Next':n['positive_months'],'closed_Close':c['closed'],'closed_Next':n['closed'],
            'DD_Close':c['closed_R_drawdown'],'DD_Next':n['closed_R_drawdown'],'annual_minimum':'MET' if a['gross_PF'] and b['gross_PF'] and min(a['gross_PF'],b['gross_PF'])>=1.7 else 'NOT MET'}
        for f,v in vals.items():cmp.value(v,row[f],'comparison',i,f)
    C.write_csv(output/'DIFFERENCES.csv',cmp.diffs,['table','row','field','actual','expected'])
    C.write_json(output/'OPEN_POSITIONS.json',op);C.write_json(output/'PERIOD_END_OPEN_POSITIONS.json',sn)
    result={'status':'PASS' if not cmp.diffs else 'FAIL','fields_compared':cmp.fields,'differences':len(cmp.diffs),'max_numeric_delta':max(cmp.maxima.values(),default=0.),'absolute_tolerance':1e-8,
        'CLOSED':len(t),'terminal_OPEN':len(op),'stop_decisions':len(stops),'signal_decisions':len(entries),'tables':cmp.tables,'independence':'separate dataframe/object vs stdlib streaming/dict; same author; human review PENDING'}
    C.write_json(output/'AUDIT_RESULT.json',result)
    assert not cmp.diffs,'INDEPENDENT_AUDIT_FAILED'
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,default=Path('/workspace/market-pattern-data'));p.add_argument('--primary',type=Path,default=C.HERE/'results');p.add_argument('--output',type=Path,default=C.HERE/'audit');a=p.parse_args();run(a.data_root,a.primary,a.output)
