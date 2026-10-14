"""Closed-R descriptive reporting, never modifies replay or parameters."""
import math
from collections import Counter
from datetime import datetime
from io_utils import write_csv,write_json

def ordered(trades):return sorted(trades,key=lambda r:(r['exit_time'],r['instrument'],r['trade_id']))

def stats(trades,opened=0):
    rs=[x['gross_R'] for x in ordered(trades)];wins=[x for x in rs if x>0];loss=[x for x in rs if x<0]
    positive=math.fsum(wins);negative=-math.fsum(loss);total=math.fsum(rs)
    peak=0.;dd=0.;streak=0;max_streak=0;acc=[]
    for r in rs:
        acc.append(r);equity=math.fsum(acc);peak=max(peak,equity);dd=max(dd,peak-equity)
        streak=streak+1 if r<0 else 0;max_streak=max(max_streak,streak)
    return dict(CLOSED=len(rs),OPEN=opened,gross_PF=positive/negative if negative else None,gross_R=total,win_rate=len(wins)/len(rs) if rs else None,mean_win_R=positive/len(wins) if wins else None,mean_loss_R=-negative/len(loss) if loss else None,expectancy_R=total/len(rs) if rs else None,max_closed_R_DD=dd,max_losing_streak=max_streak,gross_positive_R=positive,gross_negative_R=negative)

def build(models,bars,out):
    summary=[];yearly=[];monthly=[];instruments=[];concentration=[];reasons=[]
    months=[f'{y}-{m:02d}' for y in range(2023,2027) for m in range(1,13) if (y,m)<=(2026,10)]
    coverage={month:{s:sum(b['at'].strftime('%Y-%m')==month for b in bs) for s,bs in bars.items()} for month in months}
    for mode,data in models.items():
        model='T1_'+mode+'_TRAIL_3p5';trades=data['trades'];month_rows=[]
        for month in months:
            active=[s for s,n in coverage[month].items() if n];sub=[r for r in trades if r['exit_time'].strftime('%Y-%m')==month]
            metric=stats(sub)
            if not active:metric={k:None for k in metric}
            r=dict(model=model,month=month,coverage='NO_COVERAGE' if not active else 'PARTIAL_N4' if len(active)<4 else 'N4_OBSERVED',observed_symbols='|'.join(active),observed_candles=sum(coverage[month].values()),**metric)
            month_rows.append(r);monthly.append(r)
        covered=[r for r in month_rows if r['gross_R'] is not None]
        stability=dict(positive_months=sum(r['gross_R']>1e-8 for r in covered),negative_months=sum(r['gross_R']< -1e-8 for r in covered),zero_months=sum(abs(r['gross_R'])<=1e-8 for r in covered),covered_months=len(covered),calendar_months=len(months))
        summary.append(dict(model=model,classification='IDEALIZED_SIGNAL_CLOSE' if mode=='SIGNAL_CLOSE' else 'CAUSAL_NEXT_OPEN',**stats(trades,len(data['OPEN'])),**stability))
        for year in range(2023,2027):
            sub=[r for r in trades if r['exit_time'].year==year];mr=[r for r in covered if r['month'].startswith(str(year))];worst=min(mr,key=lambda r:r['gross_R'])
            # Terminal OPEN or last observed month snapshot; no annual liquidation.
            end_month=max(r['month'] for r in mr)
            boundary=[r for r in data['snapshots'] if r['month']==end_month]
            yearly.append(dict(model=model,year=year,**stats(sub,len(boundary)),positive_months=sum(r['gross_R']>1e-8 for r in mr),negative_months=sum(r['gross_R']< -1e-8 for r in mr),zero_months=sum(abs(r['gross_R'])<=1e-8 for r in mr),covered_months=len(mr),worst_month=worst['month'],worst_month_R=worst['gross_R']))
        for symbol in bars:
            for direction in ('LONG','SHORT'):
                for period in ('ALL',2023,2024,2025,2026):
                    sub=[r for r in trades if r['instrument']==symbol and r['direction']==direction and (period=='ALL' or r['exit_time'].year==period)]
                    op=sum(r['instrument']==symbol and r['direction']==direction for r in data['OPEN']) if period=='ALL' else None
                    instruments.append(dict(model=model,period=period,instrument=symbol,direction=direction,**stats(sub,op)))
        total=math.fsum(t['gross_R'] for t in trades);winner_total=math.fsum(t['gross_R'] for t in trades if t['gross_R']>0)
        for count in (1,5,10,20):
            top=sorted([r for r in trades if r['gross_R']>0],key=lambda r:-r['gross_R'])[:count]
            amount=math.fsum(r['gross_R'] for r in top)
            concentration.append(dict(model=model,unit='best_winning_trades',top=count,gross_R=amount,share_net_R=amount/total,share_positive_R=amount/winner_total,remaining_R=total-amount))
        month_positive=math.fsum(r['gross_R'] for r in covered if r['gross_R']>0)
        for count in (1,3,5):
            top=sorted(covered,key=lambda r:-r['gross_R'])[:count];amount=math.fsum(r['gross_R'] for r in top)
            concentration.append(dict(model=model,unit='best_months',top=count,gross_R=amount,share_net_R=amount/total,share_positive_R=amount/month_positive,remaining_R=total-amount))
        for symbol in bars:
            events=[r for r in data['signals'] if r['instrument']==symbol]
            for reason,n in sorted(Counter(r['reason'] for r in events).items()):reasons.append(dict(model=model,instrument=symbol,reason=reason,count=n))
    for name,rows in [('comparison_summary',summary),('yearly_comparison',yearly),('monthly_comparison',monthly),('instrument_direction_comparison',instruments),('profit_concentration',concentration),('entry_reason_counts',reasons)]:write_csv(out/(name+'.csv'),rows)
    pairs=[]
    for month in months:
        a,b=[next(r for r in monthly if r['month']==month and r['model']=='T1_'+m+'_TRAIL_3p5') for m in models]
        def sign(x):return None if x is None else 1 if x>1e-8 else -1 if x< -1e-8 else 0
        sa=sign(a['gross_R']);sb=sign(b['gross_R'])
        pairs.append(dict(month=month,signal_close_R=a['gross_R'],next_open_R=b['gross_R'],delta_R=None if sa is None else b['gross_R']-a['gross_R'],signal_close_sign=sa,next_open_sign=sb,same_sign=None if sa is None else sa==sb,coverage=a['coverage']))
    write_csv(out/'monthly_sign_comparison.csv',pairs)
    return dict(summary=summary,yearly=yearly,monthly=monthly,instruments=instruments,concentration=concentration,reasons=reasons,month_signs=pairs)

def differences(models,out):
    def index(rows):return {(r['instrument'],r['signal_time'],r['direction']):r for r in rows}
    a,b=[index(d['trades']+d['OPEN']) for d in models.values()];trade_rows=[]
    signal_indexes=[index(d['signals']) for d in models.values()]
    fields=('entry_price','initial_stop','initial_risk','exit_time','exit_price','gross_R','active_stop_at_exit','bars_held')
    for key in sorted(a.keys()|b.keys()):
        x=a.get(key);y=b.get(key);row=dict(instrument=key[0],signal_time=key[1],direction=key[2],signal_close_present=x is not None,next_open_present=y is not None)
        different=[]
        for k in fields:
            va=x.get(k) if x else None;vb=y.get(k) if y else None
            row['signal_close_'+k]=va;row['next_open_'+k]=vb
            numeric=isinstance(va,(int,float)) and isinstance(vb,(int,float))
            row['delta_'+k]=(vb-va) if numeric else None
            if (abs(vb-va)>1e-8 if numeric else va!=vb):different.append(k)
        row['changed_fields']='|'.join(different)
        row['signal_close_signal_reason']=signal_indexes[0].get(key,{}).get('reason')
        row['next_open_signal_reason']=signal_indexes[1].get(key,{}).get('reason')
        trade_rows.append(row)
    a,b=[index(d['signals']) for d in models.values()];signal_rows=[]
    for key in sorted(a.keys()|b.keys()):
        x=a.get(key);y=b.get(key)
        row=dict(instrument=key[0],signal_time=key[1],direction=key[2])
        for field in ('reason','entry_accepted','position_occupied','entry_price','initial_stop','occupied_trade_id'):
            row['signal_close_'+field]=x.get(field) if x else None;row['next_open_'+field]=y.get(field) if y else None
        row['different_signal_presence']=(x is None)!=(y is None)
        row['different_acceptance']=bool(x and y and x['entry_accepted']!=y['entry_accepted'])
        row['different_occupancy']=bool(x and y and x['position_occupied']!=y['position_occupied'])
        signal_rows.append(row)
    write_csv(out/'trade_differences.csv',trade_rows)
    write_csv(out/'signal_differences.csv.gz',signal_rows)
    receipt=dict(matched_trade_signals=sum(r['signal_close_present'] and r['next_open_present'] for r in trade_rows),signal_close_only=sum(r['signal_close_present'] and not r['next_open_present'] for r in trade_rows),next_open_only=sum(r['next_open_present'] and not r['signal_close_present'] for r in trade_rows),different_entry_price=sum('entry_price' in r['changed_fields'].split('|') for r in trade_rows),different_initial_stop=sum('initial_stop' in r['changed_fields'].split('|') for r in trade_rows),different_exit_time=sum('exit_time' in r['changed_fields'].split('|') for r in trade_rows),different_R=sum('gross_R' in r['changed_fields'].split('|') for r in trade_rows),different_signal_presence=sum(r['different_signal_presence'] for r in signal_rows),different_acceptance=sum(r['different_acceptance'] for r in signal_rows),different_occupancy=sum(r['different_occupancy'] for r in signal_rows),counts_tolerance=1e-8)
    matched=[r for r in trade_rows if r['signal_close_present'] and r['next_open_present']]
    for field in ('entry_price','initial_stop','initial_risk','exit_time','gross_R'):
        receipt['matched_different_'+field]=sum(field in r['changed_fields'].split('|') for r in matched)
    distances=[(1 if r['direction']=='LONG' else -1)*r['delta_entry_price']/r['signal_close_initial_risk'] for r in matched]
    receipt['mean_adverse_entry_distance_R']=math.fsum(distances)/len(distances)
    receipt['max_abs_entry_distance_R']=max(map(abs,distances))
    receipt['unique_entries']=[{k:r[k] for k in ('instrument','signal_time','direction','signal_close_present','next_open_present','signal_close_signal_reason','next_open_signal_reason')} for r in trade_rows if not (r['signal_close_present'] and r['next_open_present'])]
    write_json(out/'difference_summary.json',receipt);return receipt
