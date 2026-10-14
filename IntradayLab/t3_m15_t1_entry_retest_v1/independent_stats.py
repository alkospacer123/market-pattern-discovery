"""Independent closed-trade arithmetic, imported only by scalar verifier."""
import csv,json,math

def audit(models,observed_months,out):
    checks=0;max_error=0.;groups=0
    def equal(value,expected,where):
        nonlocal checks,max_error
        checks+=1
        if value is None:assert expected=='',(where,value,expected)
        else:
            error=abs(value-float(expected));max_error=max(max_error,error)
            assert error<=1e-8,(where,value,expected,error)
    def calculate(rows,opened):
        sequence=sorted(rows,key=lambda r:(r['exit_time'],r['instrument'],r['trade_id']))
        r=[x['gross_R'] for x in sequence];n=len(r)
        w=[x for x in r if x>0];l=[x for x in r if x<0];win=math.fsum(w);lose=-math.fsum(l)
        running=[];high=0.;drawdown=0.;loss_run=0;longest=0
        for x in r:
            running.append(x);now=math.fsum(running);high=max(high,now);drawdown=max(drawdown,high-now)
            if x<0:loss_run+=1
            else:loss_run=0
            longest=max(longest,loss_run)
        return dict(CLOSED=n,OPEN=opened,gross_PF=win/lose if lose else None,gross_R=math.fsum(r),win_rate=len(w)/n if n else None,mean_win_R=win/len(w) if w else None,mean_loss_R=-lose/len(l) if l else None,expectancy_R=math.fsum(r)/n if n else None,max_closed_R_DD=drawdown,max_losing_streak=longest,gross_positive_R=win,gross_negative_R=lose)
    for table in ('comparison_summary','yearly_comparison','monthly_comparison','instrument_direction_comparison'):
        with (out/(table+'.csv')).open() as f:records=list(csv.DictReader(f))
        for row in records:
            groups+=1;mode='NEXT_OPEN' if 'NEXT_OPEN' in row['model'] else 'SIGNAL_CLOSE';data=models[mode]
            trades=data['trades'];opened=len(data['OPEN'])
            if table=='yearly_comparison':
                trades=[t for t in trades if t['exit_time'].year==int(row['year'])]
                last_month=max(m for m in observed_months if m.startswith(row['year']))
                opened=sum(t['month']==last_month for t in data['snapshots'])
            elif table=='monthly_comparison':
                trades=[t for t in trades if t['exit_time'].strftime('%Y-%m')==row['month']];opened=0
            elif table=='instrument_direction_comparison':
                trades=[t for t in trades if t['instrument']==row['instrument'] and t['direction']==row['direction'] and (row['period']=='ALL' or t['exit_time'].year==int(row['period']))]
                opened=sum(t['instrument']==row['instrument'] and t['direction']==row['direction'] for t in data['OPEN']) if row['period']=='ALL' else None
            values=calculate(trades,opened)
            if table=='monthly_comparison' and row['month'] not in observed_months:values={k:None for k in values}
            for field,value in values.items():equal(value,row[field],(table,groups,field))
            if table=='comparison_summary':
                months={m:math.fsum(t['gross_R'] for t in data['trades'] if t['exit_time'].strftime('%Y-%m')==m) for m in observed_months}
                for field,value in dict(positive_months=sum(x>1e-8 for x in months.values()),negative_months=sum(x< -1e-8 for x in months.values()),zero_months=sum(abs(x)<=1e-8 for x in months.values()),covered_months=len(months)).items():equal(value,row[field],field)
    with (out/'profit_concentration.csv').open() as f:
        for row in csv.DictReader(f):
            mode='NEXT_OPEN' if 'NEXT_OPEN' in row['model'] else 'SIGNAL_CLOSE';trades=models[mode]['trades'];n=int(row['top'])
            total=math.fsum(t['gross_R'] for t in trades)
            if row['unit']=='best_winning_trades':
                candidates=[t['gross_R'] for t in trades if t['gross_R']>0]
            else:candidates=[math.fsum(t['gross_R'] for t in trades if t['exit_time'].strftime('%Y-%m')==m) for m in observed_months]
            amount=math.fsum(sorted(candidates,reverse=True)[:n]);positive=math.fsum(x for x in candidates if x>0)
            for k,v in dict(gross_R=amount,share_net_R=amount/total,share_positive_R=amount/positive,remaining_R=total-amount).items():equal(v,row[k],k)
    result=dict(status='PASS',groups=groups,checked_fields=checks,max_abs_error=max_error,order='exit_time / instrument / trade_id',source='Independent scalar replay output, own PF/R/DD/streak/concentration implementation')
    (out/'independent_statistics.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    return result
