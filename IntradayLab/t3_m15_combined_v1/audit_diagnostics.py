"""Independent CSV arithmetic for additional predeclared diagnostics."""
import csv
from datetime import datetime
from pathlib import Path


def read(p):
    with p.open() as f:return list(csv.DictReader(f))


def verify(root,trades,opened,decisions,opportunities,manifest,check):
    counts={}; sources={s['instrument']:s for s in manifest['sources']}
    from audit import RAW_CALENDARS
    raw=RAW_CALENDARS
    freq=read(root/'frequency_occupancy.csv')
    for r in freq:
        syms=tuple(sources) if r['scope']=='ALL_FOUR' else (r['scope'],)
        match=lambda t:t['version']==r['version'] and t['rule']==r['rule'] and t['instrument'] in syms
        period=lambda stamp:r['year']=='ALL' or str(stamp)[:4]==r['year']
        e=[t for t in opportunities if match(t) and period(t['signal_time'])]
        d=[t for t in decisions if match(t) and period(t['bar_close_time'])]
        f=[t for t in trades if match(t) and period(t['exit_time'])]
        n=sum(sum(period(b['at']) for b in raw[s]) for s in syms)
        eligible=sum(sum(period(b['at']) for b in raw[s][1:]) for s in syms)
        accepted=sum(t['entry_accepted']=='True' for t in e);passed=sum(t['rule_pass']=='True' for t in e)
        vals={'observed_bars':n,'eligible_position_bars':eligible,'occupied_position_bars':len(d),
            'observed_bar_occupancy':len(d)/eligible if eligible else None,'raw_signal_opportunities':len(e),'filter_pass':passed,
            'filter_failed':len(e)-passed,'occupied_at_signal_close':sum(t['position_occupied']=='True' for t in e),
            'filter_pass_but_occupied':sum(t['rule_pass']=='True' and t['position_occupied']=='True' for t in e),
            'accepted_entries':accepted,'accepted_entries_per_1000_observed_bars':1000*accepted/n if n else None,
            'closed_trades':len(f),'mean_closed_bars_held':sum(float(t['bars_held']) for t in f)/len(f) if f else None,
            'mean_closed_holding_minutes':sum(float(t['holding_minutes']) for t in f)/len(f) if f else None}
        for k,v in vals.items():check(v,r[k],'frequency:'+k)
    counts['frequency_rows']=len(freq)
    tables={n:read(root/n) for n in ('overall_report.csv','yearly_report.csv','monthly_report.csv','direction_report.csv','monthly_direction_report.csv')}
    comparisons=read(root/'component_comparisons.csv')
    for r in comparisons:
        keys=['version','scope']+[k for k in ('year','month','direction') if r[k]]
        find=lambda rule:next(t for t in tables[r['report']] if t['rule']==rule and all(t[k]==r[k] for k in keys))
        a,b=find(r['variant']),find(r['reference']);field=r['metric']
        va=float(a[field]) if a[field] else None; vb=float(b[field]) if b[field] else None
        for k,v in {'variant_value':va,'reference_value':vb,'delta':va-vb if va is not None and vb is not None else None}.items():check(v,r[k],'component:'+k)
    counts['component_metric_rows']=len(comparisons)
    frequency_comparisons=read(root/'frequency_comparison.csv')
    for r in frequency_comparisons:
        find=lambda rule:next(t for t in freq if t['rule']==rule and all(t[k]==r[k] for k in ('version','scope','year')))
        a,b=find(r['variant']),find(r['reference'])
        for k in r:
            if k.startswith('delta_'):
                field=k[6:];va=float(a[field]) if a[field] else None;vb=float(b[field]) if b[field] else None
                check(va,r['variant_'+field],'freqcomparison:variant');check(vb,r['reference_'+field],'freqcomparison:reference')
                check(va-vb if va is not None and vb is not None else None,r[k],'freqcomparison:delta')
    counts['frequency_comparison_rows']=len(frequency_comparisons)
    key=lambda t:(t['version'],t['instrument'],t['direction'],datetime.fromisoformat(t['entry_time']))
    lookup={(t['rule'],key(t)):t for t in trades}; ol={(t['rule'],key(t)):t for t in opened}
    lineage=read(root/'component_trade_lineage.csv')
    for r in lineage:
        k=(r['version'],r['instrument'],r['direction'],datetime.fromisoformat(r['reference_entry_time']))
        old=lookup[r['reference'],k];new=lookup.get((r['variant'],k));o=ol.get((r['variant'],k))
        vals={'reference_gross_R':float(old['gross_R']),'reference_is_ge2R':float(old['gross_R'])>=2,
            'reference_trade_id':old['trade_id'],'reference_exit_time':old['exit_time'],
            'reference_exit_year':old['exit_time'][:4],
            'match_status':'CLOSED_MATCH' if new else 'OPEN_TERMINAL' if o else 'NO_MATCHING_ENTRY',
            'variant_trade_id':new['trade_id'] if new else o['trade_id'] if o else None,
            'variant_gross_R':float(new['gross_R']) if new else None,'variant_exit_time':new['exit_time'] if new else None}
        for k,v in vals.items():check(v,r[k],'component_lineage:'+k)
    counts['component_lineage_rows']=len(lineage)
    cohorts=read(root/'component_winner_retention.csv')
    for r in cohorts:
        sel=[t for t in lineage if all(t[k]==r[k] for k in ('version','variant','reference')) and t['reference_is_ge2R']=='True' and (r['scope']=='ALL_FOUR' or t['instrument']==r['scope']) and (r['year']=='ALL' or t['reference_exit_year']==r['year'])]
        closed=lambda t:t['match_status']=='CLOSED_MATCH';old=lambda t:float(t['reference_gross_R']);new=lambda t:float(t['variant_gross_R'])
        vals={'reference_ge2R_winners':len(sel),'reference_ge2R_R':sum(old(t) for t in sel),
            'fully_preserved':sum(closed(t) and new(t)>=old(t)-1e-8 for t in sel),
            'reduced':sum(closed(t) and new(t)<old(t)-1e-8 for t in sel),
            'lost_entry':sum(t['match_status']=='NO_MATCHING_ENTRY' for t in sel),
            'terminal_open':sum(t['match_status']=='OPEN_TERMINAL' for t in sel),
            'matched_below_2R':sum(closed(t) and new(t)<2 for t in sel),
            'matched_nonpositive':sum(closed(t) and new(t)<=0 for t in sel),
            'matched_variant_R':sum(new(t) for t in sel if closed(t))}
        for k,v in vals.items():check(v,r[k],'component_winners:'+k)
    counts['component_winner_rows']=len(cohorts)
    return counts
