import math
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
    wins=[v for v in values if v>0];losses=[v for v in values if v<0]
    out.update(wins=len(wins),losses=len(losses),zero_trades=len(values)-len(wins)-len(losses),win_fraction=len(wins)/len(values) if values else None,mean_WIN_R=math.fsum(wins)/len(wins) if wins else None,mean_LOSS_R=math.fsum(losses)/len(losses) if losses else None)
    return out
