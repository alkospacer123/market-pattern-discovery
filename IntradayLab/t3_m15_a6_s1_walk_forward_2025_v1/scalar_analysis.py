"""Independent stdlib diagnostic selection and accounting. No primary imports."""
import math,json
import common as C
from scalar_metrics import stats

def evaluate(out):
    trades=out['trades'];sources=json.loads((C.HERE/'SPEC.json').read_text())['sources']
    directions=['ALL','LONG','SHORT'];years=['2023','2024','ALL'];scopes=['ALL_FOUR']+list(C.SYMBOLS)
    result={name:[] for name in ['summary','monthly','loss_runs','scenario_summary','scenario_monthly','scenario_ledger','top_winners','november2024']}
    def pick(scope,side,year):
        selected=[]
        for trade in trades:
            if scope!='ALL_FOUR' and scope!=trade['instrument']:continue
            if side!='ALL' and side!=trade['direction']:continue
            if year!='ALL' and year!=str(trade['exit_time'].year):continue
            selected.append(trade)
        return selected
    def months(year):return list(C.CALENDAR) if year=='ALL' else [month for month in C.CALENDAR if month[:4]==year]
    def cov(scope,month):
        beginning=min(s['first_close'][:7] for s in sources if scope=='ALL_FOUR' or s['instrument']==scope)
        if month<beginning:return 'NO_COVERAGE'
        if month==beginning and scope in ['GLDRUBF','IMOEXF']:return 'AVAILABLE_PARTIAL_START'
        return 'AVAILABLE'
    def measure(selected,cal,scope,deleted=()):
        v=stats(selected,cal);denom=sum(m not in deleted for m in cal)
        v.update(retained_calendar_months=denom,no_coverage_months=sum(cov(scope,m)=='NO_COVERAGE' for m in cal),
                 positive_fraction_calendar=v['positive_months']/len(cal),positive_fraction_retained=v['positive_months']/denom if denom else None)
        return v
    def month_rows(selected,cal,meta,deleted=()):
        answer=[]
        for month in cal:
            group=[t for t in selected if t['exit_time'].strftime('%Y-%m')==month];coverage=cov(meta['scope'],month)
            status='DIAGNOSTIC_MONTH_REMOVED' if month in deleted else 'NO_COVERAGE' if coverage=='NO_COVERAGE' else 'AVAILABLE_WITH_CLOSED' if len(group)>0 else 'AVAILABLE_NO_CLOSED'
            answer.append(meta|{'month':month,'coverage':coverage,'status':status}|stats(group,[month]))
        return answer
    for scope in scopes:
        for side in directions:
            for year in years:
                selected=pick(scope,side,year);cal=months(year);meta={'scope':scope,'direction':side,'year':year}
                v=measure(selected,cal,scope);portfolio=stats(pick('ALL_FOUR',side,year),cal)
                positions=out['OPEN_POSITIONS'] if year=='ALL' else [p for p in out['PERIOD_END_OPEN_POSITIONS'] if p['month']==year+'-12']
                opened=len([p for p in positions if (scope=='ALL_FOUR' or scope==p['instrument']) and (side=='ALL' or side==p['direction'])])
                result['summary'].append(meta|v|{'period_end_OPEN':opened,'share_portfolio_net_R':v['gross_R']/portfolio['gross_R'] if portfolio['gross_R']>0 else None})
                sequential=sorted(selected,key=lambda t:(t['exit_time'],t['instrument'],t['trade_id']))
                for label,pairs in [('CLOSED_TRADES',[(t['exit_time'].isoformat()+'|'+t['instrument']+'|'+t['trade_id'],t['gross_R']) for t in sequential]),
                                     ('CALENDAR_MONTHS',[(m,math.fsum(t['gross_R'] for t in selected if t['exit_time'].strftime('%Y-%m')==m)) for m in cal])]:
                    index=0
                    while index<len(pairs):
                        if pairs[index][1]>=0:index+=1;continue
                        finish=index+1
                        while finish<len(pairs) and pairs[finish][1]<0:finish+=1
                        run=pairs[index:finish]
                        result['loss_runs'].append(meta|{'series_type':label,'start':run[0][0],'end':run[-1][0],'length':finish-index,'gross_R':math.fsum(v for _,v in run),'members':';'.join(k for k,_ in run)})
                        index=finish
            result['monthly']+=month_rows(pick(scope,side,'ALL'),C.CALENDAR,{'scope':scope,'direction':side,'year':'ALL'})
            year_trades=pick(scope,side,'2024');nov=[t for t in year_trades if t['exit_time'].month==11]
            nv=stats(nov,['2024-11']);yv=stats(year_trades,months('2024'))
            result['november2024'].append({'scope':scope,'direction':side}|nv|{'share_2024_net_R':nv['gross_R']/yv['gross_R'] if yv['gross_R']>0 else None})
    def record(name,scope,side,year,original,kept,deleted=(),level=0.):
        meta={'scenario':name,'scope':scope,'direction':side,'year':year};cal=months(year);v=measure(kept,cal,scope,deleted)
        before=stats(original,cal);reduction=before['gross_R']-v['gross_R']
        result['scenario_summary'].append(meta|v|{'original_closed':len(original),'removed_closed':len(original)-len(kept),'removed_or_stressed_R':reduction,
            'removed_share_original_net_R':reduction/before['gross_R'] if before['gross_R']>0 else None,
            'removed_share_original_positive_R':reduction/before['positive_R'] if before['positive_R']>0 else None,
            'excluded_months':','.join(deleted),'R_stress_per_CLOSED':level,'original_OPEN_unchanged':True})
        result['scenario_monthly']+=month_rows(kept,cal,meta,deleted)
        retained={(t['instrument'],t['trade_id']):t['gross_R'] for t in kept}
        for t in sorted(original,key=lambda t:(t['exit_time'],t['instrument'],t['trade_id'])):
            identity=(t['instrument'],t['trade_id'])
            result['scenario_ledger'].append(meta|{'instrument':t['instrument'],'trade_id':t['trade_id'],'exit_time':t['exit_time'],'original_R':t['gross_R'],
                'diagnostic_R':retained.get(identity),'retained':identity in retained})
    for year in years:
        for side in directions:
            original=pick('ALL_FOUR',side,year);cal=months(year)
            for symbol in C.SYMBOLS:record('LEAVE_OUT_'+symbol,'ALL_FOUR',side,year,original,[t for t in original if t['instrument']!=symbol])
            amounts={m:math.fsum(t['gross_R'] for t in original if t['exit_time'].strftime('%Y-%m')==m) for m in cal}
            ranked=sorted(cal,key=lambda m:(-amounts[m],m))
            for count in [1,3]:
                removed=ranked[:count];record('EX_BEST'+str(count)+'_MONTHS','ALL_FOUR',side,year,original,[t for t in original if t['exit_time'].strftime('%Y-%m') not in removed],removed)
            deleted=['2024-11'] if '2024-11' in cal else []
            record('EX_NOV2024','ALL_FOUR',side,year,original,[t for t in original if t['exit_time'].strftime('%Y-%m') not in deleted],deleted)
            winners=sorted((t for t in original if t['gross_R']>0),key=lambda t:(-t['gross_R'],t['exit_time'],t['instrument'],t['trade_id']))
            for count in [1,3,5,10]:
                ids=set((t['instrument'],t['trade_id']) for t in winners[:count])
                record('EX_TOP'+str(count)+'_WINNERS','ALL_FOUR',side,year,original,[t for t in original if (t['instrument'],t['trade_id']) not in ids])
            for scope in scopes:
                group=pick(scope,side,year)
                for level in [0.05,0.10]:
                    kept=[]
                    for t in group:
                        changed=t.copy();changed['gross_R']=t['gross_R']-level;kept.append(changed)
                    record('R_STRESS_'+('005' if level==0.05 else '010'),scope,side,year,group,kept,[],level)
    for year in years:
        for side in directions:
            winners=sorted((t for t in pick('ALL_FOUR',side,year) if t['gross_R']>0),key=lambda t:(-t['gross_R'],t['exit_time'],t['instrument'],t['trade_id']))
            for index,t in enumerate(winners[:10]):
                result['top_winners'].append({'year':year,'direction':side,'rank':index+1}|{k:t[k] for k in ['instrument','trade_id','signal_time','entry_time','exit_time','gross_R']}|{'exit_month':t['exit_time'].strftime('%Y-%m')})
    return result
