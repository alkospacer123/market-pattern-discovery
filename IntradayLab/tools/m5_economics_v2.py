"""Read-only economics diagnostics; never consumed by Replay decisions."""
from collections import Counter
from datetime import datetime, timedelta
from decimal import Decimal as D
from statistics import median

from m5_conditional_v2 import tick, allowed, window_at, FIVE, ZERO


def economics(replay, bars):
    by_time={b.timestamp:b for b in bars}
    rows=[]
    for s in replay.signals:
        target=datetime.fromisoformat(s['planned_execution_at'])
        at=datetime.fromisoformat(s['ready_at'])
        b=by_time.get(target)
        signal_close=s['signal_close']; direction=s['direction_sign']
        step=tick(replay.symbol,at)
        row={'run':s['run'],'signal_id':s['signal_id'],'instrument':replay.symbol,
            'strategy':replay.strategy,'direction':s['direction'],'month':s['signal_at'][:7],
            'stage':'SIGNAL','status':s['status'],'reference_at':s['ready_at'],
            'reference_price':signal_close,'historical_tick':step,
            'atr_ticks':s['atr_shifted']/step,'rounded_stop':s['stop'],
            'rounded_take':s['take'],'rounded_adverse_cap':s['cap'],
            'adverse_cap_ticks':direction*(s['cap']-signal_close)/step,
            'signal_to_scheduled_open_minutes':D(str((target-datetime.fromisoformat(s['signal_at'])).total_seconds()/60)),
            'observed_target_exists_diagnostic':bool(b),
            'signed_adverse_open_drift_ticks':direction*(b.open-signal_close)/step if b else None,
            'projected_c1_entry':tick(replay.symbol,target),
            'projected_c1_exit':tick(replay.symbol,target),
            'cost_basis':'DATED_PLANNED_ENTRY_TICK_X2_PROJECTION_NOT_REAL_EXIT_COST'}
        add_payoff(row,signal_close,direction,s['stop'],s['take'])
        rows.append(row)
    signals={s['signal_id']:s for s in replay.signals}
    for trade in replay.ledger:
        s=signals[trade['signal_id']]
        step=tick(replay.symbol,datetime.fromisoformat(trade['entry_interval_start']))
        r={'run':trade['run'],'signal_id':trade['signal_id'],'instrument':replay.symbol,
            'strategy':replay.strategy,'direction':trade['direction'],'month':trade['entry_interval_start'][:7],
            'stage':'MODEL_ENTRY','status':trade['status'],'reference_at':trade['entry_confirmed_at'],
            'reference_price':trade['entry'],'historical_tick':step,
            'atr_ticks':s['atr_shifted']/step,'rounded_stop':trade['stop'],
            'rounded_take':trade['take'],'rounded_adverse_cap':trade['entry_cap'],
            'adverse_cap_ticks':s['direction_sign']*(trade['entry_cap']-s['signal_close'])/step,
            'signal_to_scheduled_open_minutes':D(str((datetime.fromisoformat(trade['entry_interval_start'])-datetime.fromisoformat(s['signal_at'])).total_seconds()/60)),
            'observed_target_exists_diagnostic':True,
            'signed_adverse_open_drift_ticks':s['direction_sign']*(trade['entry']-s['signal_close'])/step,
            'projected_c1_entry':step,'projected_c1_exit':step,
            'cost_basis':'ENTRY_DATED_TICK_X2_PROSPECTIVE_PROJECTION',
            'actual_c1_entry':trade['c1_entry'],'actual_c1_exit':trade['c1_exit'],
            'actual_gross_price_pnl':trade['gross_price_pnl'],'actual_net_model_c1':trade['net_model_c1'],
            'actual_exit_reason':trade['exit_reason']}
        add_payoff(r,trade['entry'],s['direction_sign'],trade['stop'],trade['take'])
        rows.append(r)
    return rows


def add_payoff(row,price,direction,stop,take):
    risk=direction*(price-stop); reward=direction*(take-price)
    cost=row['projected_c1_entry']+row['projected_c1_exit']
    net_reward=reward-cost; net_risk=risk+cost
    row.update(gross_risk=risk,gross_reward=reward,net_risk=net_risk,
        net_reward=net_reward,c1_roundtrip_projected=cost,
        stop_ticks=risk/row['historical_tick'],take_ticks=reward/row['historical_tick'],
        gross_reward_risk=reward/risk if risk>0 else None,
        potential_net_reward_risk=net_reward/net_risk if net_risk>0 else None,
        min_breakeven_win_rate=net_risk/(risk+reward) if risk>=0 and reward>0 else None,
        payoff_valid=risk>0 and reward>0,
        take_cannot_pay_c1=reward<=cost,
        payoff_assumption='Binary Stop/Take projection; time exits, gaps and unknown paths can change actual breakeven')


def payoff_summary(rows):
    result=[]
    for run in sorted({r['run'] for r in rows}):
        for stage in ('SIGNAL','MODEL_ENTRY'):
            for month in ['ALL']+[f'2023-{m:02d}' for m in range(1,13)]:
                for direction in ('ALL','LONG','SHORT'):
                    subset=[r for r in rows if r['run']==run and r['stage']==stage and
                            (month=='ALL' or r['month']==month) and (direction=='ALL' or r['direction']==direction)]
                    r={'run':run,'stage':stage,'month':month,'direction':direction,'count':len(subset),
                       'take_cannot_pay_c1_count':sum(x['take_cannot_pay_c1'] for x in subset),
                       'invalid_rounded_payoff_count':sum(not x['payoff_valid'] for x in subset)}
                    for key in ('historical_tick','atr_ticks','stop_ticks','take_ticks','adverse_cap_ticks',
                                'gross_risk','gross_reward','net_risk','net_reward','c1_roundtrip_projected',
                                'potential_net_reward_risk','min_breakeven_win_rate','signed_adverse_open_drift_ticks'):
                        vals=[x[key] for x in subset if x[key] is not None]
                        r['median_'+key]=median(vals) if vals else None
                        r['mean_'+key]=sum(vals,ZERO)/len(vals) if vals else None
                    result.append(r)
    return result


def performance(rows):
    closed=[r for r in rows if r['net_model_c1'] is not None]
    out={}
    for prefix,key in (('gross','gross_price_pnl'),('net','net_model_c1')):
        vals=[r[key] for r in closed]
        wins=[v for v in vals if v>0]; losses=[v for v in vals if v<0]
        profit=sum(wins,ZERO); loss=-sum(losses,ZERO)
        avg_win=profit/len(wins) if wins else None
        avg_loss=loss/len(losses) if losses else None
        out.update({prefix+'_PF_closed_diagnostic':profit/loss if loss else None,
            prefix+'_mean_win':avg_win,prefix+'_mean_loss_magnitude':avg_loss,
            prefix+'_expectancy_closed_diagnostic':sum(vals,ZERO)/len(vals) if vals else None,
            prefix+'_breakeven_win_rate_observed_payoff':avg_loss/(avg_win+avg_loss) if avg_win is not None and avg_loss else None})
    out['exit_reasons']=dict(Counter(r['exit_reason'] for r in rows))
    return out


def vwap_comparison(data, signals, p):
    """Observed-only diagnostic; missing volume/price cannot yield full VWAP.

    Approved daytime session accumulator spans lunch. Window accumulator resets
    at each approved window, but carries observed weights over missing slots.
    Neither is exchange transaction VWAP, nor a repaired complete session.
    """
    result=[]
    for symbol,bars in data.items():
        observed={b.timestamp for b in bars if allowed(symbol,b.timestamp)}
        missing_by_window={}
        for b in bars:
            w=window_at(b.timestamp)
            if not allowed(symbol,b.timestamp) or w in missing_by_window: continue
            t=w[0]; missing=0
            while t+FIVE<=w[1]:
                missing+=t not in observed
                t+=FIVE
            missing_by_window[w]=missing
        lookup={s['signal_at']:s for s in signals if s['instrument']==symbol and s['strategy']=='VWAP_MR'}
        day=window=None; dw=dp=ww=wp=ZERO
        for b in bars:
            if not allowed(symbol,b.timestamp): continue
            w=window_at(b.timestamp)
            if b.timestamp.date()!=day:
                day=b.timestamp.date(); dw=dp=ZERO
            if w!=window:
                window=w; ww=wp=ZERO
            if b.volume<=0: continue
            weight=b.volume; price=(b.high+b.low+b.close)/3
            dw+=weight; dp+=price*weight; ww+=weight; wp+=price*weight
            s=lookup.get(str(b.timestamp))
            if not s: continue
            day_missing=sum(n for win,n in missing_by_window.items() if win[0].date()==day)
            step=tick(symbol,datetime.fromisoformat(s['ready_at']))
            result.append({'run':s['run'],'signal_id':s['signal_id'],'signal_at':s['signal_at'],
                'instrument':symbol,'direction':s['direction'],
                'baseline_reset_vwap':s['vwap_approx'],'observed_window_anchored_vwap':wp/ww,
                'observed_daytime_session_anchored_vwap':dp/dw,
                'window_minus_reset_ticks':(wp/ww-s['vwap_approx'])/step,
                'daytime_session_minus_reset_ticks':(dp/dw-s['vwap_approx'])/step,
                'window_missing_slots':missing_by_window[w],'daytime_session_missing_slots':day_missing,
                'full_window_vwap_reconstructable':missing_by_window[w]==0,
                'full_approved_daytime_vwap_reconstructable':day_missing==0,
                'true_exchange_session_vwap':'UNAVAILABLE_NOT_CLAIMED',
                'used_by_baseline_decision':False})
    return result
