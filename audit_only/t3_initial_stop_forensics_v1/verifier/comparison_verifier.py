"""Fresh-CSV independent signal joins and static-grid sensitivity checks."""
import csv,gzip,io,math
from pathlib import Path
from collections import defaultdict
from decimal import Decimal,ROUND_FLOOR,ROUND_CEILING
from .arithmetic_verifier import read
ROOT=Path(__file__).resolve().parents[3]
G=('system','lifecycle','fold_id','instrument')

def comparison_capital_audit(output):
    output=Path(output);fields=0;maximum=0.
    def equal(e,a,ctx):
        nonlocal fields,maximum
        fields+=1
        if e is None:assert a in ('',None),(ctx,e,a)
        elif isinstance(e,bool):assert str(e)==str(a),(ctx,e,a)
        elif isinstance(e,(int,float,Decimal)):
            assert a not in ('',None),(ctx,e,a);d=abs(float(e)-float(a));maximum=max(maximum,d);assert d<=1e-8,(ctx,e,a,d)
        else:assert str(e)==str(a),(ctx,e,a)
    trades=[t for s in ('H1','M15') for t in read(output/f'{s}_TRADE_FORENSICS.csv')]
    def ident(t):return '|'.join(t[k] for k in G)+'|'+t['signal_time']+'|'+t['direction']
    for t in trades:equal(ident(t),t['signal_id'],('trade_signal_identity',t['trade_id'],t['variant']))
    control={t['signal_id']:t for t in trades if t['variant']=='CONTROL'}
    comparisons=read(output/'STOP_VARIANT_TRADE_COMPARISON.csv');lookup={(r['variant'],r['signal_id']):r for r in comparisons}
    assert len(lookup)==len(comparisons)
    expected_keys=set();lostkeys=set();newmisskeys=set();largekeys=set();ranks={};profits={}
    for t in control.values():
        group=tuple(t[k] for k in ('system','lifecycle','fold_id'))
        if group not in ranks:
            wins=sorted([x for x in control.values() if tuple(x[k] for k in ('system','lifecycle','fold_id'))==group and x['status']=='CLOSED' and float(x['gross_R'])>0],key=lambda x:-float(x['gross_R']))
            ranks[group]={w['signal_id']:i+1 for i,w in enumerate(wins)};profits[group]=math.fsum(float(w['gross_R']) for w in wins)
    signals={}
    for system in ('H1','M15'):
        for s in read(output/f'{system}_SIGNALS.csv.gz'):
            key='|'.join(s[k] for k in G)+'|'+s['at']+'|'+('LONG' if s['side']=='1' else 'SHORT');signals[(s['variant'],key)]=s
    for system in ('H1','M15'):
        for variant in (('STOP_2p0','STOP_1p5') if system=='H1' else ('STOP_1p5',)):
            baseline={k:t for k,t in control.items() if t['system']==system};other={t['signal_id']:t for t in trades if t['system']==system and t['variant']==variant}
            for key in baseline.keys()|other.keys():
                a=baseline.get(key);b=other.get(key);both=a is not None and b is not None;closed=both and a['status']==b['status']=='CLOSED';t=a or b;context=(variant,key);expected_keys.add(context);actual=lookup[context]
                equal('COMMON_SIGNAL' if both else 'MISSED_CONTROL_ENTRY' if a else 'NEW_VARIANT_ENTRY',actual['match'],context+('match',))
                if not both:newmisskeys.add(context)
                sign=1 if t['direction']=='LONG' else -1
                pr=sign*(Decimal(b['exit_price'])-Decimal(a['entry_price']))/Decimal(a['initial_risk_price']) if closed else None
                delta=float(pr)-float(a['gross_R']) if closed else None
                lost=bool(closed and float(a['gross_R'])>0>float(b['gross_R']));improved=bool(closed and float(a['gross_R'])<0 and delta>1e-8)
                early=bool(both and system=='H1' and b['trail1_activation_time'] and (not a['trail1_activation_time'] or b['trail1_activation_time']<a['trail1_activation_time']))
                earlyexit=bool(closed and early and b['exit_reason']=='ATR_TRAILING_STOP' and (not a['trail1_activation_time'] or b['exit_time']<a['trail1_activation_time']))
                expected=dict(CONTROL_trade_id=a['trade_id'] if a else None,variant_trade_id=b['trade_id'] if b else None,CONTROL_status=a['status'] if a else None,variant_status=b['status'] if b else None,CONTROL_R=float(a['gross_R']) if a and a['gross_R'] else None,variant_own_R=float(b['gross_R']) if b and b['gross_R'] else None,variant_exit_in_CONTROL_R0=pr,delta_exit_in_CONTROL_R0=delta,TIGHT_STOP_LOST_WINNER=lost,original_loss_improved_price=improved,original_loss_improved_ownR=bool(closed and float(a['gross_R'])<0 and float(b['gross_R'])>float(a['gross_R'])+1e-8),original_loss_closed_earlier=bool(closed and float(a['gross_R'])<0 and b['exit_time']<a['exit_time']),original_loss_turned_positive=bool(closed and float(a['gross_R'])<0<float(b['gross_R'])),H1_earlier_activation=early,H1_trailing_exit_before_CONTROL_activation=earlyexit,H1_early_activation_delta_CONTROL_R0=delta if earlyexit else None)
                for field,value in expected.items():equal(value,actual[field],context+(field,))
                if lost:lostkeys.add(context)
                for prefix,trade in (('CONTROL',a),('variant',b)):
                    for field,source in (('entry','entry_price'),('R0','initial_risk_price'),('exit_time','exit_time'),('exit_reason','exit_reason'),('trigger_time','trigger_bar_time'),('activation_time','trail1_activation_time')):
                        expected=trade.get(source) or None if trade else None
                        equal(float(expected) if expected is not None and field in ('entry','R0') else expected,actual[prefix+'_'+field],context+(prefix,field))
                    sig=signals.get(('CONTROL' if prefix=='CONTROL' else variant,key),{})
                    state=sig.get('reason','ACCEPTED' if trade else 'OCCUPIED')
                    equal(state,actual[prefix+'_signal_state'],context+(prefix,'signal_state'));equal(sig.get('occupied_trade_id') or None,actual[prefix+'_occupied_trade'],context+(prefix,'occupied_trade'))
                group=tuple(t[k] for k in ('system','lifecycle','fold_id'));rank=ranks[group].get(key);profit=profits[group]
                equal(rank,actual['CONTROL_winner_rank'],context+('rank',));equal(profit,actual['CONTROL_positive_R_total'],context+('positive_profit',))
                lostprofit=max(0.,-delta) if rank and delta is not None else None
                equal(lostprofit,actual['positive_profit_lost_CONTROL_R0'],context+('lost_profit',));equal(lostprofit/profit if lostprofit is not None and profit else None,actual['positive_profit_lost_share'],context+('lost_share',))
                if rank and rank<=10:largekeys.add(context)
    equal(len(expected_keys),len(lookup),'comparison_count');assert expected_keys==lookup.keys()
    for file,keys in [('LOST_WINNERS.csv',lostkeys),('NEW_AND_MISSED_ENTRIES.csv',newmisskeys),('LARGE_WINNERS.csv',largekeys)]:
        observed=read(output/file);actualkeys={(r['variant'],r['signal_id']) for r in observed};assert actualkeys==keys and len(observed)==len(keys),(file,'selection_mismatch')
        for row in observed:
            original=lookup[(row['variant'],row['signal_id'])]
            for field,value in row.items():equal(original[field],value,(file,row['signal_id'],field))
    # Grid/quantity status from authenticated static registry; no money backtest.
    registry={r['research_symbol']:r for r in read(ROOT/'TradingSystemLab/stage8_robot/production_instrument_registry.csv')}
    feasibility=read(output/'CAPITAL_FEASIBILITY.csv');caps={(r['variant'],r['signal_id']):r for r in feasibility};tradekeys={(t['variant'],t['signal_id']) for t in trades};assert tradekeys==caps.keys() and len(caps)==len(feasibility)
    for t in trades:
        context=(t['variant'],t['signal_id']);c=caps[context];reg=registry[t['instrument']];step=Decimal(reg['price_step']);value=Decimal(reg['tick_value']);initial=Decimal(t['initial_stop_price']);entry=Decimal(t['entry_price']);risk=Decimal(t['initial_risk_price']);direction=1 if t['direction']=='LONG' else -1;rounded=(initial/step).to_integral_value(rounding=ROUND_FLOOR if direction==1 else ROUND_CEILING)*step;rd=abs(entry-rounded)
        expected=dict(static_tick_size=step,static_tick_value_RUB=value,static_contract_size=Decimal(reg['contract_size']),quantity_step=1,initial_on_static_grid=abs(float(initial/step)-round(float(initial/step)))<1e-8,outward_rounded_stop=rounded,outward_rounded_Risk0=rd,risk_change_fraction=rd/risk-1,static_1lot_stop_distance_RUB=rd/step*value,static_1lot_research_risk_RUB=risk/step*value,R15=.015,nominal_limit=.06,integer_qty=None,realized_equity_RUB=None,dated_GO_RUB=None,available_margin_RUB=None,documented_broker_cost_RUB=None,money_Net='NOT_VALIDATED',RUB_DD='NOT_VALIDATED',cash_return='NOT_VALIDATED',historical_grid_authority='NOT_VALIDATED_STATIC_SNAPSHOT_ONLY')
        for field,value in expected.items():equal(value,c[field],context+('capital',field))
        assert direction*(rounded-initial)<=0,(context,'stop_rounding_not_outward')
    counts=defaultdict(lambda:[0,0])
    for system in ('H1','M15'):
        for t in read(output/f'{system}_TRACE.csv.gz'):
            step=float(registry[t['instrument']]['price_step'])
            for field in ('stop_entering','stop_after'):
                if t.get(field) not in ('',None):
                    key=tuple(t[k] for k in ('system','lifecycle','fold_id','variant'))+(t['instrument'],field);counts[key][0]+=1;number=float(t[field]);counts[key][1]+=int(abs(number/step-round(number/step))>=1e-8)
    grid=read(output/'STOP_GRID_SUMMARY.csv');assert len(grid)==len(counts)
    for g in grid:
        key=tuple(g[k] for k in ('system','lifecycle','fold_id','variant','symbol','field'));equal(counts[key][0],g['observations'],('grid_count',key));equal(counts[key][1],g['off_grid'],('off_grid_count',key))
    return dict(status='PASS',fields_checked=fields,max_abs_numeric_error=maximum,comparison_rows=len(comparisons),lost_winner_rows=len(lostkeys),new_missed_rows=len(newmisskeys),large_winner_rows=len(largekeys),capital_rows=len(feasibility),stop_grid_groups=len(grid),method='Fresh CSV signal identity join; Decimal CONTROL-R0 exits; lost winners/newmissed/activation cohorts/ranks/profit shares; independent Decimal static-grid rounding/risk and unvalidated cash fields; fresh trace grid aggregation')
