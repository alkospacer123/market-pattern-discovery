"""Fresh CSV/Decimal report audit; independent of primary analysis helpers."""
import csv,gzip,io,math,statistics
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

GROUP=('system','lifecycle','fold_id','variant')

def read(path):
    raw=Path(path).read_bytes()
    if str(path).endswith('.gz'):raw=gzip.decompress(raw)
    return list(csv.DictReader(io.StringIO(raw.decode())))
def number(x):return None if x in ('',None) else float(x)
def sign(x):return 1 if x>1e-8 else -1 if x< -1e-8 else 0

def arithmetic_audit(output):
    output=Path(output);fields=0;maxerror=0.;summary_count=monthly_count=curve_count=0
    def equal(e,a,context):
        nonlocal fields,maxerror
        fields+=1
        if e is None:assert a in ('',None),(context,e,a)
        elif isinstance(e,(float,int,Decimal)) and not isinstance(e,bool):
            assert a not in ('',None),(context,e,a);d=abs(float(e)-float(a));maxerror=max(maxerror,d);assert d<=1e-8,(context,e,a,d)
        else:assert str(e)==str(a),(context,e,a)
    trades=[r for system in ('H1','M15') for r in read(output/f'{system}_TRADE_FORENSICS.csv')]
    monthly=read(output/'STOP_VARIANT_MONTHLY.csv');summaries=read(output/'STOP_VARIANT_SUMMARY.csv');curves=read(output/'PORTFOLIO_CURVES.csv.gz')
    for t in trades:
        if t['status']!='CLOSED':continue
        gross=(Decimal(1) if t['direction']=='LONG' else Decimal(-1))*(Decimal(t['exit_price'])-Decimal(t['entry_price']))/Decimal(t['initial_risk_price'])
        equal(gross,t['gross_R'],('trade_Decimal_R',t['signal_id'],t['variant']))
        if t['system']=='H1':
            cost=Decimal('.002')/Decimal(t['initial_risk_price']);equal(cost,t['cost_R'],('trade_C1',t['signal_id']));equal(gross-cost,t['net_R_C1'],('trade_net_C1',t['signal_id']))
        else:equal(None,t['cost_R'],('M15_cost_unvalidated',t['signal_id']));equal(None,t['net_R_C1'],('M15_net_unvalidated',t['signal_id']))
    # Portfolio reconstruction from fresh per-symbol marks, using stdlib last-value state.
    reconstructed={};curve_index={tuple(r[k] for k in GROUP)+(r['at'],):r for r in curves};raw_marks_available=all((output/f'{s}_MARKS.csv.gz').exists() for s in ('H1','M15'))
    if raw_marks_available:
        marks=[m for s in ('H1','M15') for m in read(output/f'{s}_MARKS.csv.gz')];events=defaultdict(lambda:defaultdict(list))
        for m in marks:events[tuple(m[k] for k in GROUP)][m['at']].append(m)
        columns=('gross_realized_R','gross_MTM_R','C1_normalized_MTM_R','gross_unrealized_R','remaining_quantity')
        for group,times in events.items():
            state={};reconstructed[group]=[]
            for at,changes in sorted(times.items()):
                for m in changes:state[m['instrument']]=m
                expected={col:math.fsum(float(m[col]) for m in state.values()) for col in columns};actual=curve_index[group+(at,)];curve_count+=1
                for col,value in expected.items():equal(value,actual[col],('portfolio_from_marks',group,at,col))
                reconstructed[group].append(dict(at=at,**expected))
        equal(len(curves),curve_count,'portfolio_curve_rows')
    else:
        for c in curves:reconstructed.setdefault(tuple(c[k] for k in GROUP),[]).append({**c,**{k:float(c[k]) for k in ('gross_realized_R','gross_MTM_R','C1_normalized_MTM_R','gross_unrealized_R','remaining_quantity')}})
    months_by_group=defaultdict(list)
    for m in monthly:months_by_group[tuple(m[k] for k in GROUP)].append(m)
    def drawdown(values,initial=0.):
        peak=initial;worst=0.
        for value in values:peak=max(peak,value);worst=max(worst,peak-value)
        return worst
    def negstreak(months,basis):
        best=run=0;lastordinal=None
        for m in sorted(months,key=lambda r:r['month']):
            ordinal=int(m['month'][:4])*12+int(m['month'][5:]);v=number(m[basis]);negative=v is not None and v< -1e-8
            run=(run+1 if lastordinal is not None and ordinal==lastordinal+1 else 1) if negative else 0;best=max(best,run);lastordinal=ordinal
        return best
    for group,months in months_by_group.items():
        previous=previous_c1=0.;cs=reconstructed[group]
        for m in sorted(months,key=lambda r:r['month']):
            monthly_count+=1;identity=group+(m['month'],);ts=[t for t in trades if tuple(t[k] for k in GROUP)==group and t['status']=='CLOSED' and t['exit_time'][:7]==m['month']]
            if m['coverage']=='NO_DATA':
                for field in ('CLOSED_R','MTM_R','C1_normalized_CLOSED_R','C1_normalized_MTM_R','CLOSED_sign','MTM_sign','CLOSED_trades','MTM_intramonth_DD_R'):equal(None,m[field],('NO_DATA',identity,field))
                assert not ts,('NO_DATA_HAS_EXIT',identity)
                continue
            part=[c for c in cs if c['at'][:7]==m['month']];assert part,identity
            gross=math.fsum(float(t['gross_R']) for t in ts);mtm=part[-1]['gross_MTM_R']-previous
            equal(gross,m['CLOSED_R'],('month_closed',identity));equal(mtm,m['MTM_R'],('month_mtm',identity));equal(len(ts),m['CLOSED_trades'],('month_count',identity));equal(sign(gross),m['CLOSED_sign'],('month_closed_sign',identity));equal(sign(mtm),m['MTM_sign'],('month_mtm_sign',identity))
            equal(drawdown([c['gross_MTM_R'] for c in part],previous),m['MTM_intramonth_DD_R'],('intramonth_DD',identity))
            if group[0]=='H1':equal(math.fsum(float(t['net_R_C1']) for t in ts),m['C1_normalized_CLOSED_R'],('month_C1closed',identity));equal(part[-1]['C1_normalized_MTM_R']-previous_c1,m['C1_normalized_MTM_R'],('month_C1mtm',identity))
            else:equal(None,m['C1_normalized_CLOSED_R'],('M15_C1blank',identity));equal(None,m['C1_normalized_MTM_R'],('M15_C1blank',identity))
            equal(part[-1]['remaining_quantity'],m['open_positions_at_last_bar'],('month_openqty',identity));equal(part[-1]['gross_unrealized_R'],m['unrealized_R_at_last_bar'],('month_unrealized',identity))
            previous=part[-1]['gross_MTM_R'];previous_c1=part[-1]['C1_normalized_MTM_R']
    for s in summaries:
        group=tuple(s[k] for k in GROUP);union=s['lifecycle']=='DISJOINT_BASELINE_AND_HISTORICAL_OOS';summary_count+=1
        def selected(r):return r['system']==s['system'] and r['variant']==s['variant'] and (r['lifecycle']!='walk_forward' if union else r['lifecycle']==s['lifecycle'] and r['fold_id']==s['fold_id'])
        allts=[t for t in trades if selected(t)];ts=sorted([t for t in allts if t['status']=='CLOSED'],key=lambda r:(r['exit_time'],r['instrument'],r['trade_id']));ms=[m for m in monthly if selected(m) and m['coverage']!='NO_DATA'];rs=[float(t['gross_R']) for t in ts];wins=[r for r in rs if r>0];losses=[r for r in rs if r<0];net=math.fsum(rs)
        expected=dict(CLOSED=len(ts),OPEN=len(allts)-len(ts),gross_R=net,gross_PF=math.fsum(wins)/-math.fsum(losses) if losses else None,expectancy_R=net/len(rs) if rs else None,win_rate=len(wins)/len(rs) if rs else None,average_win_R=statistics.mean(wins) if wins else None,average_loss_R=statistics.mean(losses) if losses else None,gross_positive_R=math.fsum(wins),gross_negative_R=math.fsum(losses),top5_winners_R=math.fsum(sorted(wins,reverse=True)[:5]),top10_winners_R=math.fsum(sorted(wins,reverse=True)[:10]))
        for reason in ('INITIAL_STOP','ATR_TRAILING_STOP'):
            subset=[t for t in ts if t['exit_reason']==reason];expected[reason+'_count']=len(subset);expected[reason+'_R']=math.fsum(float(t['gross_R']) for t in subset)
        expected['negative_trailing_count']=sum(t['exit_reason']=='ATR_TRAILING_STOP' and float(t['gross_R'])<0 for t in ts)
        if s['system']=='H1':
            c1=[float(t['net_R_C1']) for t in ts];expected.update(C1_normalized_R=math.fsum(c1),C1_normalized_PF=math.fsum(r for r in c1 if r>0)/-math.fsum(r for r in c1 if r<0) if any(r<0 for r in c1) else None)
        else:expected.update(C1_normalized_R=None,C1_normalized_PF=None)
        basis=s['monthly_basis'];vals=[float(m[basis]) for m in ms];streak=max((negstreak([m for m in ms if m['lifecycle']==life],basis) for life in {m['lifecycle'] for m in ms}),default=0) if union else negstreak(ms,basis)
        expected.update(positive_months=sum(sign(v)>0 for v in vals),negative_months=sum(sign(v)<0 for v in vals),zero_months=sum(sign(v)==0 for v in vals),observed_months=len(vals),worst_month_R=min(vals) if vals else None,median_month_R=statistics.median(vals) if vals else None,max_negative_month_streak=streak)
        if union:expected.update(CLOSED_R_DD=None,MTM_R_DD=None)
        else:
            total=0.;closedcurve=[]
            for r in rs:total+=r;closedcurve.append(total)
            expected.update(CLOSED_R_DD=drawdown(closedcurve),MTM_R_DD=drawdown([c['gross_MTM_R'] for c in reconstructed[group]]))
        for k,v in expected.items():equal(v,s[k],('summary',group,basis,k))
    return dict(status='PASS',fields_checked=fields,max_abs_numeric_error=maxerror,summary_rows=summary_count,monthly_rows=monthly_count,portfolio_rows=curve_count,portfolio_rebuilt_from_per_symbol_marks=raw_marks_available,method='Fresh CSV/gzip reads; Decimal trade returns and C1; stdlib portfolio/MTM, monthly signs/DD, lifecycle PF/expectancy/winloss/exit contributions/top5top10, no primary analysis imports')
