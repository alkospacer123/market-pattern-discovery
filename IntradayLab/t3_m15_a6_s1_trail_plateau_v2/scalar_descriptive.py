"""Independent stdlib audit of preregistered holding/frequency and month-run tables."""
import math
import common as C

def compute(pools,frames,monthly):
    holding=[];runs=[]
    def percentile(values,fraction):
        if not values:return None
        ordered=sorted(values);index=(len(ordered)-1)*fraction;lo=int(index);hi=min(lo+1,len(ordered)-1)
        return ordered[lo]+(ordered[hi]-ordered[lo])*(index-lo)
    for version,trail in C.VERSIONS.items():
        pool=pools[version]
        for scope in ('ALL_FOUR',*C.SYMBOLS):
            for direction in ('ALL','LONG','SHORT'):
                for year in ('ALL',2023,2024):
                    match=lambda r:(scope=='ALL_FOUR' or r['instrument']==scope) and (direction=='ALL' or r['direction']==direction)
                    trades=[r for r in pool['trades'] if match(r) and (year=='ALL' or r['exit_time'].year==year)]
                    decisions=[r for r in pool['entry_opportunities'] if match(r) and (year=='ALL' or r['signal_time'].year==year)]
                    n=sum(1 for symbol,bars in frames.items() if scope=='ALL_FOUR' or symbol==scope for bar in bars if year=='ALL' or bar['at'].year==year);entries=len([r for r in decisions if r['entry_accepted']])
                    row={'variant':version,'trail_atr':trail,'scope':scope,'direction':direction,'year':year,'closed':len(trades),'executed_entries':entries,'observed_bar_denominator':n,'entries_per_1000_observed_bars':entries/n*1000 if n else None,'closed_per_calendar_month':len(trades)/(24 if year=='ALL' else 12)}
                    for prefix,values in [('holding_bars',[float(r['bars_held']) for r in trades]),('holding_elapsed_hours',[(r['exit_time']-r['entry_time']).total_seconds()/3600 for r in trades])]:
                        row[prefix+'_mean']=math.fsum(values)/len(values) if values else None;row[prefix+'_median']=percentile(values,.5);row[prefix+'_p90']=percentile(values,.9);row[prefix+'_max']=max(values) if values else None
                    holding.append(row)
                    sequence=sorted([r for r in monthly if r['variant']==version and r['scope']==scope and r['direction']==direction and (year=='ALL' or r['month'].startswith(str(year)))],key=lambda r:r['month'])
                    start=None;end=None;count=0;returns=[]
                    for r in sequence+[{'month':None,'gross_R':0}]:
                        if r['gross_R']<0:
                            start=start or r['month'];end=r['month'];count+=1;returns.append(r['gross_R'])
                        elif count:
                            runs.append({'variant':version,'scope':scope,'direction':direction,'year':year,'start_month':start,'end_month':end,'length':count,'gross_R':math.fsum(returns)});start=None;count=0;returns=[]
    return {'holding_frequency':holding,'negative_month_runs':runs}
