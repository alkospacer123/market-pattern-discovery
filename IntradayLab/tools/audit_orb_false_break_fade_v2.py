"""Independent v2 gates, daily state machine and economics from bounded raw M5.

Imports no production v2 feature, selection, entry or trade-outcome function.
The v1 oracle has its own raw reader, calendar and chronological outcome engine.
"""
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal
import audit_orb_false_break_fade as oracle

D=Decimal; FIVE=timedelta(minutes=5)


def atr_observations(rows):
    """Prefix-sum oracle: 14 actual TR observations, no inserted time slots."""
    out={};total=D(0);sums=[total];last=None
    for at,b in sorted(rows.items()):
        if b[4]<=0:
            last=None
            continue
        tr=b[1]-b[2]
        if last is not None and last+FIVE==at:
            tr=max(tr,abs(b[1]-rows[last][3]),abs(b[2]-rows[last][3]))
        total+=tr;sums.append(total);last=at
        if len(sums)>14:out[at]=(sums[-1]-sums[-15])/D(14)
    return out


def expected_gates(rows,events,symbol,spec):
    values=atr_observations(rows);out=[]
    for original in events:
        r=dict(original);r['v2_original_base_reason']=r['base_reason']
        r['v2_filter_reason']=r['base_reason']
        if r['base_reason']=='SIGNAL':
            assert r['sweep_start']+FIVE<=r['signal_at']
            atr=values.get(r['sweep_start']);price_step=oracle.grid(symbol,r['sweep_start'])
            parent=r.get('m15_close')
            if parent is not None:
                assert r['m15_start']+3*FIVE<=r['signal_at']
                children=[rows[r['m15_start']+i*FIVE] for i in range(3)]
                assert r['m15_open']==children[0][0] and parent==children[-1][3]
                assert r['m15_high']==max(x[1] for x in children) and r['m15_low']==min(x[2] for x in children)
            veto=parent is not None and ((r['direction']<0 and parent>r['or_high']) or (r['direction']>0 and parent<r['or_low']))
            passes=atr is not None and r['sweep_size']>=max(price_step,D('.30')*atr)
            r.update(v2_atr14=atr,v2_atr_ready=atr is not None,v2_atr_pass=passes,v2_m15_context_available=parent is not None,v2_m15_breakout_accepted_veto=veto)
            if spec['atr'] and atr is None:r['base_reason']=r['v2_filter_reason']='V2_ATR_UNAVAILABLE'
            elif spec['atr'] and not passes:r['base_reason']=r['v2_filter_reason']='V2_ATR_SWEEP_TOO_SMALL'
            elif spec['mtf'] and veto:r['base_reason']=r['v2_filter_reason']='V2_M15_ACCEPTED_BREAKOUT_VETO'
            elif spec['mtf'] and parent is None:r['v2_filter_reason']='M15_NO_CONTEXT_NEUTRAL_ALLOWED'
        out.append(r)
    return out


def daily_expected(symbol,rows,events,arch,spec):
    days=defaultdict(dict);ee=defaultdict(list)
    for t,b in rows.items():
        if oracle.calendar(t.date()):days[str(t.date())][t]=b
    for e in events:ee[e['date']].append(e)
    signals=[];trades=[];daily=[];unresolved=False
    for day in sorted(set(days)|set(ee)):
        bars=days.get(day,{})
        if bars:ss,tt=oracle.oracle_trades(symbol,bars,ee.get(day,[]),arch,spec)
        else:
            assert not any(x['base_reason']=='SIGNAL' for x in ee[day])
            ss=[dict(x,architecture=arch,status='REJECTED',reason=x['base_reason'],order_admitted=False,model_filled=False) for x in ee[day]];tt=[]
        for x in ss+tt:x.update(research_mode='DAY_ISOLATED_CONDITIONAL',initial_flat_assumed=True,initial_flat_proven=False,prior_unknown_requires_flat_assumption=unresolved)
        unknown=any(x['status']=='UNKNOWN' for x in tt)
        daily.append(dict(architecture=arch,instrument=symbol,date=day,source_observed=bool(bars),initial_flat_assumed=True,initial_flat_proven=False,signal_count=sum(x['base_reason']=='SIGNAL' for x in ss),model_fills=sum(x['model_filled'] for x in tt),closed=sum(x['status']=='CLOSED' for x in tt),unknown=sum(x['status']=='UNKNOWN' for x in tt),prior_unknown_requires_flat_assumption=unresolved,any_unknown=unknown))
        signals+=ss;trades+=tt;unresolved=unresolved or unknown
    return signals,trades,daily


def statistics(trades,scenario):
    closed=sorted((x for x in trades if x['status']=='CLOSED'),key=lambda x:(x['resolved_at'],x['signal_id']))
    amounts=[];gross=[];costs=[];r_values=[]
    for t in closed:
        pnl=t['direction']*(t['exit_price']-t['entry_price'])
        fee=(1 if scenario=='c1' else 2)*(oracle.grid(t['instrument'],t['entry_at'])+oracle.grid(t['instrument'],t['exit_interval_start']))
        gross.append(pnl);costs.append(fee);amounts.append(pnl-fee);r_values.append((pnl-fee)/t['risk'])
    wins=[x for x in amounts if x>0];losses=[x for x in amounts if x<0]
    gain=sum(wins,D(0));loss=-sum(losses,D(0));RG=sum((x for x in r_values if x>0),D(0));RL=-sum((x for x in r_values if x<0),D(0))
    curve=[D(0)];price_curve=[D(0)]
    for x in r_values:curve.append(curve[-1]+x)
    for x in amounts:price_curve.append(price_curve[-1]+x)
    n=len(closed)
    return dict(closed_trades=n,gross=sum(gross,D(0)),cost=sum(costs,D(0)),net=sum(amounts,D(0)),net_R=sum(r_values,D(0)),net_PF=gain/loss if loss else None,PF_no_losses=bool(wins and not losses),net_PF_R=RG/RL if RL else None,expectancy_price=sum(amounts,D(0))/n if n else None,expectancy_R=sum(r_values,D(0))/n if n else None,win_rate=D(len(wins))/n if n else None,average_win_price=gain/len(wins) if wins else None,average_loss_price=-loss/len(losses) if losses else None,realized_reward_risk=(gain/len(wins))/(loss/len(losses)) if wins and losses else None,max_drawdown_R=max(max(curve[:i+1])-v for i,v in enumerate(curve)) if n else None,max_drawdown_price=max(max(price_curve[:i+1])-v for i,v in enumerate(price_curve)) if n else None,worst_trade_R=min(r_values) if n else None,worst_trade_price=min(amounts) if n else None,largest_winner_share=max(wins)/gain if wins else None,top3_winners_share=sum(sorted(wins,reverse=True)[:3],D(0))/gain if wins else None)


def run(config,raw,actual_signals,actual_trades,actual_days,v1_signals,v1_trades):
    errors=[];checked=0;control_fields=0
    for symbol in config['instruments']:
        events=oracle.oracle_signals(symbol,raw[symbol])
        for arch,spec in config['architectures'].items():
            expected=expected_gates(raw[symbol],events,symbol,spec)
            ss,tt,dd=daily_expected(symbol,raw[symbol],expected,arch,{'atr':False,'mtf':False})
            a=[x for x in actual_signals if x['instrument']==symbol and x['architecture']==arch]
            b=[x for x in actual_trades if x['instrument']==symbol and x['architecture']==arch]
            signal_keys=oracle.SIGNAL_KEYS+('v2_original_base_reason','v2_atr14','v2_atr_ready','v2_atr_pass','v2_m15_context_available','v2_m15_breakout_accepted_veto','v2_filter_reason','status','reason','order_admitted','model_filled','initial_flat_assumed','initial_flat_proven','prior_unknown_requires_flat_assumption')
            trade_keys=oracle.TRADE_KEYS+('signal_at','waiting_bar_closed_at','order_sent_at','planned_execution_at','initial_flat_assumed','initial_flat_proven','prior_unknown_requires_flat_assumption')
            errors+=oracle.compare_rows(a,ss,signal_keys,'v2_signals_'+arch)
            errors+=oracle.compare_rows(b,tt,trade_keys,'v2_trades_'+arch)
            got_days={x['date']:x for x in actual_days if x['instrument']==symbol and x['architecture']==arch}
            for day in dd:
                if got_days.get(day['date'])!=day:errors.append(dict(table='days',instrument=symbol,architecture=arch,date=day['date']))
            checked+=len(ss)*len(signal_keys)+len(tt)*len(trade_keys)
            old_ss,old_tt,_=daily_expected(symbol,raw[symbol],events,arch,spec)
            va=[x for x in v1_signals if x['instrument']==symbol and x['architecture']==arch]
            vb=[x for x in v1_trades if x['instrument']==symbol and x['architecture']==arch]
            errors+=oracle.compare_rows(va,old_ss,oracle.SIGNAL_KEYS+('status','reason','order_admitted','model_filled','prior_unknown_requires_flat_assumption'),'v1_daywise_signals_'+arch)
            errors+=oracle.compare_rows(vb,old_tt,trade_keys,'v1_daywise_trades_'+arch)
            checked+=len(old_ss)*(len(oracle.SIGNAL_KEYS)+5)+len(old_tt)*len(trade_keys)
            if arch=='A_BASE':
                errors+=oracle.compare_rows(b,vb,trade_keys,'A_BASE_v2_vs_v1_daywise')
                control_fields+=len(b)*len(trade_keys)
    return dict(status='PASS' if not errors else 'FAIL',checked_fields=checked,control_fields=control_fields,discrepancies=errors,method='Independent bounded raw reader, independent ORB/M15 source oracle, prefix-sum ATR observations, independently selected gates, separate chronological per-day trade engine; no production v2 signal/outcome functions',continuous_account_claim=False)
