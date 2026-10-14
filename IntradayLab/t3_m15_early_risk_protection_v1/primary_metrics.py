import numpy as np
def metrics(rows,calendar):
    ordered=sorted(rows,key=lambda r:(r['exit_time'],r['instrument'],r['trade_id']))
    x=np.asarray([r['gross_R'] for r in ordered],dtype=float)
    positive=float(x[x>0].sum());negative=float(-x[x<0].sum());total=float(x.sum())
    monthly={m:sum(r['gross_R'] for r in rows if r['exit_time'].strftime('%Y-%m')==m) for m in calendar}
    equity=np.r_[0.,np.cumsum(x)];longest=streak=0
    for v in monthly.values():streak=streak+1 if v<0 else 0;longest=max(streak,longest)
    worst=min(monthly,key=monthly.get) if monthly else None
    losing=seq=0
    for v in x:seq=seq+1 if v<0 else 0;losing=max(losing,seq)
    result={'closed':len(x),'gross_PF':positive/negative if negative else None,'gross_R':total,
        'expectancy_R':float(x.mean()) if len(x) else None,'positive_R':positive,'negative_R':negative,
        'positive_months':sum(v>0 for v in monthly.values()),'negative_months':sum(v<0 for v in monthly.values()),
        'zero_months':sum(v==0 for v in monthly.values()),'months':len(calendar),
        'worst_month':worst,'worst_month_R':monthly.get(worst),'max_negative_month_run':longest,
        'closed_R_drawdown':float((np.maximum.accumulate(equity)-equity).max()),'max_losing_trade_run':losing}
    ranking=sorted(monthly,key=lambda m:(-monthly[m],m))
    for n in (1,3):
        top=ranking[:n];contrib=sum(monthly[m] for m in top)
        remaining=[r['gross_R'] for r in rows if r['exit_time'].strftime('%Y-%m') not in top]
        p=sum(r for r in remaining if r>0);l=-sum(r for r in remaining if r<0)
        result.update({f'top{n}_months':','.join(top),f'top{n}_months_R':contrib,
            f'top{n}_share_annual_R':contrib/total if total>0 else None,
            f'ex_top{n}_PF':p/l if l else None,f'ex_top{n}_R':sum(remaining)})
    for n in (5,10):
        wins=sorted((v for v in x if v>0),reverse=True)[:n];p=sum(wins)
        result.update({f'top{n}_winners_R':p,f'top{n}_share_positive_R':p/positive if positive else None,
            f'ex_top{n}_winners_PF':(positive-p)/negative if negative else None,f'ex_top{n}_winners_R':total-p})
    result.update(wins=int((x>0).sum()),losses=int((x<0).sum()),zero_trades=int((x==0).sum()),win_fraction=float((x>0).mean()) if len(x) else None,mean_WIN_R=float(x[x>0].mean()) if (x>0).any() else None,mean_LOSS_R=float(x[x<0].mean()) if (x<0).any() else None)
    return result
