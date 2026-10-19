"""Independent per-position scalar execution and stdlib arithmetic audit.

Does not import the replay engines or accounting helpers; its state is rebuilt
from input candles. Feature authority is the authenticated frozen calculation.
"""
import math,statistics
from bisect import bisect_right
from decimal import Decimal,ROUND_CEILING,ROUND_FLOOR
from collections import defaultdict
import csv,gzip,io
from datetime import timedelta

def independent_audit(streams,results):
    index={(s['system'],s['lifecycle'],s['fold_id'],s['instrument']):s['bars'] for s in streams}
    fields=0;positions=0;partials=0;ambiguities=0;grid_stops=0
    def same(a,b):
        nonlocal fields
        fields+=1
        if isinstance(a,(float,int)) and not isinstance(a,bool):
            assert b is not None and abs(a-b)<=1e-8,('AUDIT_NUMERIC',a,b)
        else:assert a==b,('AUDIT_FIELD',a,b)
    for result in results:
        for t in result['trades']:
            positions+=1
            bars=index[(t['system'],t['lifecycle'],t['fold_id'],t['instrument'])]
            side=1 if t['direction']=='LONG' else -1
            risk=abs(t['entry_price']-t['initial_stop_price']);same(risk,t['initial_risk_price'])
            entry_idx=next(i for i,b in enumerate(bars) if b['at']==t['entry_time'])
            signal=bars[entry_idx]
            same(t['entry_price']-side*(2.5 if t['system']=='H1' else 2.)*signal['ATR'],t['initial_stop_price'])
            if t['system']=='M15':
                assert 600<=signal['at'].hour*60+signal['at'].minute<1080
                assert bars[entry_idx+1]['at']==signal['at']+timedelta(minutes=15)
                same(bars[entry_idx+1]['Open'],t['entry_price'])
            else:same(signal['Close'],t['entry_price'])
            tick=Decimal(str(t['price_step']));entry=Decimal(str(t['entry_price']));initial=Decimal(str(t['initial_stop_price']))
            raw=entry+Decimal(side)*2*abs(entry-initial)
            target=float((raw/tick).to_integral_value(rounding=ROUND_CEILING if side==1 else ROUND_FLOOR)*tick)
            same(target,t['target_price']);assert side*(Decimal(str(target))-raw)>=0
            if Decimal(str(t['initial_stop_price']))%tick:grid_stops+=1
            stop=t['initial_stop_price'];extreme=t['entry_price'];triggered=activated=False;stored=None;trigger_at=None
            legs={};found_end=False;amb=0
            for b in bars[entry_idx+1:]:
                at=b['at']
                if t['system']=='H1' and triggered and not activated and at!=trigger_at:
                    activated=True;stop=max(stop,stored) if side==1 else min(stop,stored)
                stop_hit=b['Low']<=stop if side==1 else b['High']>=stop
                opening=side*(b['Open']-stop)<=0
                stop_hit=stop_hit or opening
                target_hit=b['High']>=target if side==1 else b['Low']<=target
                if stop_hit and target_hit and 1 not in legs:amb+=1
                if stop_hit:
                    price=min(b['Open'],stop) if side==1 else max(b['Open'],stop)
                    for part in (1,2):
                        if part not in legs:legs[part]=(at,price,'INITIAL_STOP' if stop==t['initial_stop_price'] else 'ATR_TRAILING_STOP')
                    found_end=True;break
                if target_hit and t['variant']=='PARTIAL_TP_2R_50' and 1 not in legs:legs[1]=(at,target,'PARTIAL_TP_2R_50')
                extreme=max(extreme,b['High']) if side==1 else min(extreme,b['Low'])
                proposal=extreme-side*(3 if t['system']=='H1' else 3.5)*b['ATR']
                if t['system']=='H1':
                    if not triggered and (b['High']>=t['entry_price']+risk if side==1 else b['Low']<=t['entry_price']-risk):
                        triggered=True;trigger_at=at;stored=proposal
                    if activated:stop=max(stop,proposal) if side==1 else min(stop,proposal)
                else:stop=max(stop,proposal) if side==1 else min(stop,proposal)
            same('CLOSED' if found_end else 'OPEN',t['status']);same(amb,t['ambiguous_stop_tp_bars']);ambiguities+=amb
            same(1.,t['part1_quantity']+t['part2_quantity']);same(.5,t['part1_quantity']);same(.5,t['part2_quantity'])
            is_partial=1 in legs and legs[1][2]=='PARTIAL_TP_2R_50';same(is_partial,t['partial_executed']);partials+=is_partial
            gross=[]
            for part in (1,2):
                a=legs.get(part)
                same(a[0] if a else None,t[f'part{part}_exit_time']);same(a[1] if a else None,t[f'part{part}_exit_price']);same(a[2] if a else None,t[f'part{part}_reason'])
                if a:
                    r=.5*side*(a[1]-t['entry_price'])/risk;gross.append(r);same(r,t[f'part{part}_gross_R'])
                same(0. if a else .5*side*(bars[-1]['Close']-t['entry_price'])/risk,t[f'part{part}_unrealized_gross_R'])
                same(None,t[f'part{part}_broker_commission_RUB']);same(None,t[f'part{part}_broker_slippage_RUB'])
            if found_end:
                same(math.fsum(gross),t['gross_R']);same(0.,t['remaining_quantity'])
                if t['system']=='H1':
                    costs=math.fsum(t[f'part{p}_{leg}_C1_R'] for p in (1,2) for leg in ('entry','exit'))
                    same(.002/risk,costs);same(t['gross_R']-costs,t['net_R_C1'])
            same(stop,t['active_stop'])
    # Independently rebuild every observed mark and realized-cost event from legs.
    for result in results:
        if not result['marks']:continue
        identity=result['marks'][0]
        bars=index[tuple(identity[k] for k in ('system','lifecycle','fold_id','instrument'))]
        expected_realized=defaultdict(list);costs=defaultdict(list);entries=defaultdict(list);exits=defaultdict(list)
        for t in result['trades']:
            entry_at=t['entry_time']+(timedelta(minutes=15) if t['system']=='M15' else timedelta(0))
            entries[entry_at].append(t)
            if t['system']=='H1':costs[entry_at].append(.001/t['initial_risk_price'])
            for part in (1,2):
                at=t[f'part{part}_exit_time']
                if at is not None:
                    expected_realized[at].append(t[f'part{part}_gross_R'])
                    if t['system']=='H1':costs[at].append(.0005/t['initial_risk_price'])
            if t['status']=='CLOSED':exits[t['exit_time']].append(t['trade_id'])
        active=None;realized=paid=0.
        same(len(bars),len(result['marks']))
        for b,m in zip(bars,result['marks']):
            at=b['at'];same(at,m['at'])
            for t in entries[at]:active=t
            for tid in exits[at]:
                if active and active['trade_id']==tid:active=None
            realized+=math.fsum(expected_realized[at]);paid+=math.fsum(costs[at])
            remaining=1.-.5*sum(active[f'part{part}_exit_time'] is not None and active[f'part{part}_exit_time']<=at for part in (1,2)) if active else 0.
            unrealized=remaining*(1 if active['direction']=='LONG' else -1)*(b['Close']-active['entry_price'])/active['initial_risk_price'] if active else 0.
            same(active['trade_id'] if active else None,m['active_trade_id']);same(remaining,m['remaining_quantity'])
            same(realized,m['gross_realized_R']);same(unrealized,m['gross_unrealized_R']);same(realized+unrealized,m['gross_MTM_R'])
            same(paid,m['C1_normalized_paid_R']);same(realized+unrealized-paid,m['C1_normalized_MTM_R'])
    # Partial cannot change occupancy/end time in fractional model.
    alltrades=[t for r in results for t in r['trades']]
    def key(t):return tuple(t[k] for k in ('system','lifecycle','fold_id','instrument','trade_id'))
    a={key(t):t for t in alltrades if t['variant']=='CONTROL'};b={key(t):t for t in alltrades if t['variant']!='CONTROL'}
    assert a.keys()==b.keys()
    for k in a:
        for field in ('direction','entry_time','entry_price','initial_stop_price','initial_risk_price','exit_time','exit_price','active_stop','trail1_triggered','trigger_bar_time','trail1_activation_time','trail1_activated','stored_trail_candidate','status'):
            same(a[k].get(field),b[k].get(field))
    return dict(status='PASS',independent_scalar_positions=positions,fields_checked=fields,fractional_partial_events=partials,ambiguous_stop_tp_observations=ambiguities,
        inherited_off_grid_initial_stops=grid_stops,off_grid_status='Frozen research initial/trailing stops, unchanged; cash execution not validated',
        price_grid_new_TP='PASS',volumes='PASS .5+.5=1; no overclose; residual reserves instrument',
        chronology='PASS old stop before target, entry candle rules and no retroactive exits',
        costs='PASS normalized H1 C1 only; M15 GROSS_ONLY; no money Net claimed',
        capital='CASH_MODEL_NOT_VALIDATED',external_human_audit='PENDING',
        independence='Separate scalar position replay, no import of new engines/accounting; authenticated frozen features shared')

def arithmetic_audit(out):
    """Fresh CSV reads, Decimal leg arithmetic and monthly recomputation."""
    def read(path):
        with path.open() as f:return list(csv.DictReader(f))
    count=0;maximum=0.
    def equal(a,b):
        nonlocal count,maximum
        error=abs(float(a)-float(b));assert error<1e-8,('ARITHMETIC',a,b);maximum=max(maximum,error);count+=1
    for system in ('H1','M15'):
        trades=read(out/f'{system}_TRADES.csv');months=read(out/f'{system}_MONTHLY.csv')
        for t in trades:
            for p in (1,2):
                if not t[f'part{p}_exit_price']:continue
                d=Decimal(t[f'part{p}_quantity'])*(1 if t['direction']=='LONG' else -1)*(Decimal(t[f'part{p}_exit_price'])-Decimal(t['entry_price']))/Decimal(t['initial_risk_price'])
                equal(d,t[f'part{p}_gross_R'])
        for m in months:
            if m['model']=='EXECUTABLE_INTEGER':assert not m['capital_MTM_return_pct'] and not m['gross_closed_leg_R'];continue
            if m['coverage']=='NO_DATA':assert not m['gross_closed_leg_R'];continue
            vals=[]
            for t in trades:
                if any(t[k]!=m[k] for k in ('lifecycle','fold_id','variant')):continue
                for p in (1,2):
                    if t[f'part{p}_exit_time'].startswith(m['month']):vals.append(float(t[f'part{p}_gross_R']))
            equal(math.fsum(vals),m['gross_closed_leg_R'])
        # Rebuild portfolio marks without pandas, grouping simultaneous observations.
        raw=gzip.decompress((out/f'{system}_MARKS.csv.gz').read_bytes()).decode()
        marks=list(csv.DictReader(io.StringIO(raw)));groups=defaultdict(list)
        for r in marks:groups[(r['lifecycle'],r['fold_id'],r['variant'])].append(r)
        for group,rows in groups.items():
            events=defaultdict(list)
            for r in rows:events[r['at']].append(r)
            state={};calendar=defaultdict(list);c1calendar=defaultdict(list)
            for at in sorted(events):
                for r in events[at]:state[r['instrument']]=r
                calendar[at[:7]].append(math.fsum(float(r['gross_MTM_R']) for r in state.values()))
                c1calendar[at[:7]].append(math.fsum(float(r['C1_normalized_MTM_R']) for r in state.values()))
            previous=previous_c1=0.
            for month,curve in sorted(calendar.items()):
                m=next(r for r in months if tuple(r[k] for k in ('lifecycle','fold_id','variant'))==group and r['month']==month and r['model']=='FRACTIONAL_REFERENCE')
                equal(curve[-1]-previous,m['gross_MTM_change_R'])
                peak=previous;worst=0.
                for value in curve:peak=max(peak,value);worst=max(worst,peak-value)
                equal(worst,m['gross_MTM_intra_month_DD_R'])
                if system=='H1':equal(c1calendar[month][-1]-previous_c1,m['C1_normalized_MTM_change_R'])
                previous=curve[-1];previous_c1=c1calendar[month][-1]
        # Every headline and lifecycle summary derives from fresh trade/month CSVs.
        for s in read(out/f'{system}_SUMMARY.csv'):
            if s['model']=='EXECUTABLE_INTEGER':assert not s['positive_months'] and not s['net_money_R'];continue
            def selected(r):
                return r['variant']==s['variant'] and (r['lifecycle']!='walk_forward' if s['lifecycle']=='DISJOINT_BASELINE_AND_HISTORICAL_OOS' else r['lifecycle']==s['lifecycle'] and r['fold_id']==s['fold_id'])
            ts=[t for t in trades if selected(t) and t['status']=='CLOSED']
            ms=[m for m in months if selected(m) and m['model']=='FRACTIONAL_REFERENCE' and m['coverage']!='NO_DATA']
            ms.sort(key=lambda r:r['month']);rs=[float(t['gross_R']) for t in ts];wins=[r for r in rs if r>0];losses=[r for r in rs if r<0]
            equal(len(rs),s['closed_positions']);equal(math.fsum(rs),s['gross_R'])
            if losses:equal(math.fsum(wins)/-math.fsum(losses),s['gross_PF'])
            equal(math.fsum(rs)/len(rs),s['expectancy_gross_R']);equal(len(wins)/len(rs),s['win_rate'])
            if wins:equal(statistics.mean(wins),s['average_win_R'])
            if losses:equal(statistics.mean(losses),s['average_loss_R'])
            if wins and losses:equal(statistics.mean(wins)/abs(statistics.mean(losses)),s['average_win_abs_loss_ratio'])
            for n in (5,10):
                removed=sorted(wins,reverse=True)[:n];remaining=sorted(rs,reverse=True)[len(removed):]
                equal(math.fsum(remaining),s[f'gross_R_without_top{n}'])
                lp=-math.fsum(r for r in remaining if r<0)
                if lp:equal(math.fsum(r for r in remaining if r>0)/lp,s[f'gross_PF_without_top{n}'])
            col='gross_closed_leg_R' if s['monthly_basis']=='GROSS_CLOSED_LEG_R' else 'gross_MTM_change_R'
            values=[float(m[col]) for m in ms]
            positive=sum(v>1e-8 for v in values);negative=sum(v< -1e-8 for v in values);zero=len(values)-positive-negative
            for name,value in [('positive_months',positive),('negative_months',negative),('zero_months',zero),('covered_months',len(values)),('positive_share',positive/len(values)),('negative_share',negative/len(values)),('zero_share',zero/len(values)),('worst_month_R',min(values)),('median_month_R',statistics.median(values))]:equal(value,s[name])
            streak=best=0
            for value in values:streak=streak+1 if value< -1e-8 else 0;best=max(best,streak)
            equal(best,s['max_consecutive_negative_months']);equal(max(float(m['gross_MTM_intra_month_DD_R']) for m in ms),s['max_MTM_intramonth_DD_R'])
    return dict(status='PASS',checks=count,max_absolute_error=maximum,method='Fresh CSV/gzip reads; Decimal leg arithmetic; stdlib portfolio MTM/DD, calendar signs, PF/expectancy/win-loss and top5/top10 summary recomputation')
