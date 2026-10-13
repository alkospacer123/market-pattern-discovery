"""Preregistered holding/frequency and negative-month runs; no replay feedback."""
import numpy as np
import common as C

def build(out,frames,monthly):
    holdings=[];runs=[]
    for v,trail in C.VERSIONS.items():
        for scope in ('ALL_FOUR',*C.SYMBOLS):
            symbols=C.SYMBOLS if scope=='ALL_FOUR' else [scope]
            for side in ('ALL','LONG','SHORT'):
                for year in ('ALL',2023,2024):
                    t=[r for r in out['trades'] if r['version']==v and r['instrument'] in symbols and (side=='ALL' or r['direction']==side) and (year=='ALL' or r['exit_time'].year==year)]
                    e=[r for r in out['entry_opportunities'] if r['version']==v and r['instrument'] in symbols and (side=='ALL' or r['direction']==side) and (year=='ALL' or r['signal_time'].year==year)]
                    bars=[r['bars_held'] for r in t];hours=[(r['exit_time']-r['entry_time']).total_seconds()/3600 for r in t]
                    denominator=sum(sum(year=='ALL' or at.year==year for at in frames[s].index) for s in symbols);entries=sum(r['entry_accepted'] for r in e)
                    row={'variant':v,'trail_atr':trail,'scope':scope,'direction':side,'year':year,'closed':len(t),'executed_entries':entries,'observed_bar_denominator':denominator,'entries_per_1000_observed_bars':entries*1000/denominator if denominator else None,'closed_per_calendar_month':len(t)/(24 if year=='ALL' else 12)}
                    for label,values in [('holding_bars',bars),('holding_elapsed_hours',hours)]:
                        row.update({label+'_mean':float(np.mean(values)) if values else None,label+'_median':float(np.median(values)) if values else None,label+'_p90':float(np.percentile(values,90,method='linear')) if values else None,label+'_max':float(max(values)) if values else None})
                    holdings.append(row)
                    months=[r for r in monthly if r['variant']==v and r['scope']==scope and r['direction']==side and (year=='ALL' or r['month'].startswith(str(year)))];current=[]
                    def flush():
                        if current:runs.append({'variant':v,'scope':scope,'direction':side,'year':year,'start_month':current[0]['month'],'end_month':current[-1]['month'],'length':len(current),'gross_R':sum(r['gross_R'] for r in current)})
                    for r in months:
                        if r['gross_R']<0:current.append(r)
                        else:flush();current=[]
                    flush()
    return {'holding_frequency':holdings,'negative_month_runs':runs}
