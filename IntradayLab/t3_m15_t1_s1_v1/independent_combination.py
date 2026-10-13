"""Second computation: stdlib source features plus separate delayed-trail replay.

FIRST GATE code remains immutable in independent.py. Only this new replay adds
S1 / COMBINED support; it imports no primary engine or primary metric functions.
"""
from independent import (VERSIONS, SYMBOLS, START, END, STEP, TZ, entry_gate)
import math

def simulate(bars,symbol,version,rule):
    """Independent position state machine: settle old Stop, then surviving Close."""
    assert rule in ('CONTROL','T1','S1','COMBINED')
    delayed=rule in ('S1','COMBINED')
    trail=VERSIONS[version];ids={'version':version,'rule':rule,'instrument':symbol}
    t,d,e,g,snap=[],[],[],[],[];q=None;previous=None;last=None
    alias={'USDRUBF':'Si','CNYRUBF':'CNY'}.get(symbol,symbol)
    def opened(q,b):
        return ids|{'trade_id':q['id'],'direction':'LONG' if q['sign']==1 else 'SHORT',
            'entry_time':q['at'],'entry_price':q['entry'],'initial_stop':q['initial'],
            'initial_risk':q['risk'],'active_stop':q['stop'],'breakout_level':q['level'],
            'last_close':b['at'],'last_close_price':b['c'],
            'unrealized_gross_R_at_last_close':q['sign']*(b['c']-q['entry'])/q['risk'],
            'pending_exit_decision':None,'threshold_activated':q['activated'],'activation_time':q['activation_at'],
            'favorable_extreme':q['extreme'],'stop_source':q['source'],'stop_updates':q['updates'],'status':'OPEN_NOT_LIQUIDATED_EXCLUDED_FROM_CLOSED_TRADE_METRICS'}
    for i,b in enumerate(bars):
        at=b['at'];assert START<=at<END,'FUTURE_OHLC_FORBIDDEN'
        if q and previous.strftime('%Y-%m')!=at.strftime('%Y-%m'):
            snap.append(opened(q,last)|{'month':previous.strftime('%Y-%m'),'year':previous.year})
        allowed,reason=entry_gate(at,previous,'T1' if rule in ('T1','COMBINED') else 'CONTROL')
        delta=(at-previous).total_seconds()/60 if previous else None
        gap=delta is not None and delta>15
        overnight=gap and (at-STEP).date()!=(previous-STEP).date()
        if previous is None or gap:
            g.append(ids|{'current_close':at,'previous_close':previous,'delta_minutes':delta,
                'reason':'NO_PREVIOUS_OBSERVED_CLOSE' if previous is None else 'OBSERVED_GAP_GT_15_MIN',
                'cross_date':bool(gap and at.date()!=previous.date()),'cross_observed_open_date':bool(overnight),
                'original_signal':b['signal'],'entry_rule_pass':allowed,'position_before_bar':q['id'] if q else None})
        exited=None
        if q:
            side=q['sign'];entry=q['entry'];stop=q['stop'];risk=q['risk']
            opening=side*(b['o']-stop)<=0
            hit=opening or (b['l']<=stop if side==1 else b['h']>=stop)
            r=ids|{'trade_id':q['id'],'bar_open_time':at-STEP,'bar_close_time':at,
                'active_stop':stop,'initial_risk':risk,'extreme_before':q['extreme'],
                'open':b['o'],'high':b['h'],'low':b['l'],'ATR_at_close':b['atr'],
                'stop_hit':hit,'stop_gap':opening and b['o']!=stop,
                'observed_gap_before_bar':gap,'observed_overnight_gap_before_bar':bool(overnight),
                'activated_before':q['activated'],'activation_time_before':q['activation_at'],'threshold_R':1. if delayed else None}
            q['gaps']+=int(gap);q['overnights']+=int(overnight)
            if hit:
                fill=min(b['o'],stop) if side==1 else max(b['o'],stop)
                t.append(ids|{'trade_id':q['id'],'direction':'LONG' if side==1 else 'SHORT',
                    'entry_time':q['at'],'entry_price':entry,'initial_stop':q['initial'],'initial_risk':risk,
                    'breakout_level':q['level'],'exit_time':at,'exit_bar_open_time':at-STEP,
                    'exit_bar_close_time':at,'exit_price':fill,'gross_R':side*(fill-entry)/risk,
                    'exit_type':'INITIAL_STOP' if stop==q['initial'] else 'RATCHETED_STOP',
                    'active_stop_at_exit':stop,'trailing_updates':q['updates'],'gap_exit':fill!=stop,
                    'exit_at_open':opening,'rule_decision_time':None,'rule_stop_conflict_at_open':False,
                    'bars_held':i-q['index'],'holding_minutes':(at-q['at']).total_seconds()/60,
                    'MAE_R':max(0.,entry-q['min'] if side==1 else q['max']-entry,side*(entry-fill))/risk,
                    'MFE_R':max(0.,q['max']-entry if side==1 else entry-q['min'])/risk,
                    'cross_calendar_day':at.date()!=q['at'].date(),'year':at.year,
                    'observed_gaps_exposed':q['gaps'],'observed_overnight_gaps_exposed':q['overnights'],
                    'threshold_activated':q['activated'],'activation_time':q['activation_at'],'stop_source_at_exit':q['source'],**q['features']})
                r.update(phase='EXIT',exit_price=fill,extreme_after=None,trail_proposal=None,
                    active_stop_next_bar=None,trailing_changed=False,
                    favorable_extreme_after=None,favorable_R_after=None,activated_after=q['activated'],
                    threshold_activated_now=False,activation_time_after=q['activation_at'],original_trail_proposal=None,
                    boundary_stop=None,ratchet_changed=False,stop_source_next=None)
                exited=q['id'];q=None
            else:
                q['min']=min(q['min'],b['l']);q['max']=max(q['max'],b['h'])
                q['extreme']=max(q['extreme'],b['h']) if side==1 else min(q['extreme'],b['l'])
                proposal=q['extreme']-side*trail*b['atr']
                trigger=delayed and not q['activated'] and side*(q['extreme']-entry)>=risk
                if trigger:q['activated']=True;q['activation_at']=at
                next_stop=(max(stop,proposal) if side==1 else min(stop,proposal)) if not delayed or q['activated'] else stop
                if next_stop!=stop:q['source']='ATR_TRAIL'
                q['stop']=next_stop;q['updates']+=int(next_stop!=stop)
                r.update(phase='SURVIVED',exit_price=None,extreme_after=q['extreme'],trail_proposal=proposal,
                    active_stop_next_bar=next_stop,trailing_changed=next_stop!=stop,
                    favorable_extreme_after=q['extreme'],favorable_R_after=side*(q['extreme']-entry)/risk,
                    activated_after=q['activated'],threshold_activated_now=bool(trigger),activation_time_after=q['activation_at'],
                    original_trail_proposal=proposal,boundary_stop=None,ratchet_changed=next_stop!=stop,stop_source_next=q['source'])
            d.append(r)
        if math.isfinite(b['atr']) and b['signal']:
            busy=q is not None;accept=allowed and not busy
            tid=f'T3-M15-{alias}-{len(t)+1:06d}' if accept else None
            e.append(ids|{'signal_time':at,'previous_observed_close':previous,'delta_minutes':delta,
                'moscow_hour':at.astimezone(TZ).hour,'direction':'LONG' if b['signal']==1 else 'SHORT',
                'original_signal':b['signal'],'rule_pass':allowed,'rule_reason':reason,
                'position_occupied':busy,'occupied_trade_id':q['id'] if busy else None,
                'entry_accepted':accept,'decision_reason':'ACCEPTED' if accept else 'RULE_AND_OCCUPIED' if not allowed and busy else 'RULE_BLOCKED' if not allowed else 'POSITION_OCCUPIED',
                'trade_id':tid,'same_close_exit_trade_id':exited,'entry_price':b['c'],
                'candidate_initial_stop':b['c']-b['signal']*2*b['atr'],'ATR':b['atr'],
                'H1AvailableAt':b['h1']['at'],'PriorHigh':b['upper'],'PriorLow':b['lower']})
            if accept:
                side=b['signal'];initial=b['c']-side*2*b['atr'];risk=abs(b['c']-initial)
                assert risk>0 and b['h1']['at']<=at
                h=b['h1'];ph=b['previous_h1']
                f={'ATR':b['atr'],'PreviousATR':b['previous_atr'],'signal_open':b['o'],'signal_high':b['h'],'signal_low':b['l']}
                for name,key in (('ADX','adx'),('Slope','slope'),('ATRRatio','ratio'),('AvailableAt','at')):
                    f['H1'+name]=h[key];f['H1Previous'+name]=ph[key] if ph else None
                q={'id':tid,'sign':side,'entry':b['c'],'initial':initial,'risk':risk,'stop':initial,
                    'at':at,'index':i,'level':b['upper'] if side==1 else b['lower'],'extreme':b['c'],
                    'min':b['c'],'max':b['c'],'updates':0,'gaps':0,'overnights':0,'features':f,
                    'activated':False,'activation_at':None,'source':'INITIAL_STOP'}
        previous=at;last=b
    op=opened(q,last) if q else None
    if op:snap.append(op|{'month':last['at'].strftime('%Y-%m'),'year':last['at'].year})
    return t,op,d,e,g,snap
