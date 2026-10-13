"""Two fixed combinations and four reproductions; frozen #490/#495/#496 mechanics.

No costs. Only completed survived bars may change extrema, activation or Stop.
"""
import importlib.util
from pathlib import Path
import sys
import pandas as pd

HERE = Path(__file__).resolve().parent
FROZEN = HERE.parent/'t3_m15_forever_v1'
spec = importlib.util.spec_from_file_location('stop_exit_frozen_features',FROZEN/'engine.py')
E = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = E
spec.loader.exec_module(E)
MAIN = 'bf703671dca481d0451a9eb822de143b96a80037'
RULES = ('CONTROL','A6','A7','S1','C1','C2')
MECHANISMS = {'CONTROL':('CONTROL','CONTROL'),'A6':('A6','CONTROL'),'A7':('A7','CONTROL'),'S1':('CONTROL','S1'),'C1':('A6','S1'),'C2':('A7','S1')}
spec_a = importlib.util.spec_from_file_location('combined_frozen_entry',HERE.parent/'t3_m15_entry_regime_v1/engine.py')
A = importlib.util.module_from_spec(spec_a)
sys.modules[spec_a.name] = A
spec_a.loader.exec_module(A)


def features(frame,p):
    low, high = E.indicators(frame,p)
    high['ATRRatio'] = high.ATR/high.ATRMean
    high['PreviousADX'] = high.ADX.shift(1)
    high['PreviousSlope'] = high.Slope.shift(1)
    high['PreviousATRRatio'] = high.ATRRatio.shift(1)
    high['AvailableAt'] = high.index
    high['PreviousAvailableAt'] = pd.Series(high.index,index=high.index).shift(1)
    for col in ('ADX','Slope','ATRRatio','PreviousADX','PreviousSlope','PreviousATRRatio','AvailableAt','PreviousAvailableAt'):
        low['H1'+col] = high[col].reindex(low.index,method='ffill')
    low['PreviousATR'] = low.ATR.shift(1)
    return low,high


def execute(low,symbol,version,p,rule):
    assert rule in RULES
    records, opened, decisions, opportunities, pos = [],None,[],[],None
    ident = {'version':version,'rule':rule,'instrument':symbol}
    alias = E.ALIASES.get(symbol,symbol)
    entry_rule, stop_rule = MECHANISMS[rule]
    threshold = 1. if stop_rule == 'S1' else None
    for i,b in enumerate(low.itertuples()):
        at_open = b.Index-pd.Timedelta(minutes=15)
        if pos is not None:
            q = pos
            sign,entry,stop,risk = q['sign'],q['entry'],q['stop'],q['risk']
            open_hit = sign*(b.Open-stop) <= 0
            # Old active Stop is settled before any current-bar favorable data.
            hit = open_hit or (b.Low <= stop if sign == 1 else b.High >= stop)
            decision = ident | {'trade_id':q['id'],'bar_open_time':at_open,'bar_close_time':b.Index,
                'active_stop':stop,'initial_risk':risk,'extreme_before':q['extreme'],
                'activated_before':q['activated'],'activation_time_before':q['activation_time'],
                'open':b.Open,'stop_hit':bool(hit),'stop_gap':bool(open_hit and b.Open != stop),
                'threshold_R':threshold}
            if hit:
                fill = min(b.Open,stop) if sign == 1 else max(b.Open,stop)
                records.append(ident | {'trade_id':q['id'],'direction':'LONG' if sign == 1 else 'SHORT',
                    'entry_time':q['at'],'entry_price':entry,'initial_stop':q['initial_stop'],'initial_risk':risk,
                    'breakout_level':q['level'],'exit_time':b.Index,'exit_bar_open_time':at_open,
                    'exit_bar_close_time':b.Index,'exit_price':fill,'gross_R':sign*(fill-entry)/risk,
                    'exit_type':'INITIAL_STOP' if stop == q['initial_stop'] else 'RATCHETED_STOP',
                    'active_stop_at_exit':stop,'trailing_updates':q['updates'],'gap_exit':bool(fill != stop),
                    'exit_at_open':bool(open_hit),'rule_decision_time':None,'rule_stop_conflict_at_open':False,
                    'bars_held':i-q['index'],'holding_minutes':(b.Index-q['at']).total_seconds()/60,
                    'MAE_R':max(0.,entry-q['min'] if sign == 1 else q['max']-entry,sign*(entry-fill))/risk,
                    'MFE_R':max(0.,q['max']-entry if sign == 1 else entry-q['min'])/risk,
                    'cross_calendar_day':bool(b.Index.normalize() != q['at'].normalize()),
                    'threshold_activated':q['activated'],'activation_time':q['activation_time'],
                    'stop_source_at_exit':q['stop_source'],**q['entry_features']})
                decision.update(phase='EXIT',exit_price=fill,favorable_extreme_after=None,
                    favorable_R_after=None,activated_after=q['activated'],threshold_activated_now=False,
                    activation_time_after=q['activation_time'],original_trail_proposal=None,boundary_stop=None,
                    active_stop_next_bar=None,ratchet_changed=False,stop_source_next=None)
                pos = None
            else:
                q['min'],q['max'] = min(q['min'],b.Low),max(q['max'],b.High)
                q['extreme'] = max(q['extreme'],b.High) if sign == 1 else min(q['extreme'],b.Low)
                trigger = threshold is not None and not q['activated'] and sign*(q['extreme']-entry) >= threshold*risk
                if trigger:q['activated'],q['activation_time'] = True,b.Index
                proposal = q['extreme']-sign*p.trail_atr*b.ATR
                boundary = None
                next_stop,source = stop,q['stop_source']
                if stop_rule == 'CONTROL' or q['activated']:
                    if sign*(proposal-next_stop) > 0:next_stop,source = proposal,'ATR_TRAIL'
                changed = next_stop != stop
                q['stop'],q['stop_source'] = next_stop,source
                q['updates'] += int(changed)
                decision.update(phase='SURVIVED',exit_price=None,favorable_extreme_after=q['extreme'],
                    favorable_R_after=sign*(q['extreme']-entry)/risk,activated_after=q['activated'],
                    threshold_activated_now=bool(trigger),activation_time_after=q['activation_time'],
                    original_trail_proposal=proposal,boundary_stop=boundary,active_stop_next_bar=next_stop,
                    ratchet_changed=bool(changed),stop_source_next=source)
            decisions.append(decision)
        if pd.notna(b.ATR) and b.Signal:
            allowed = bool(A.permits(b,entry_rule))
            accepted = pos is None and allowed
            opportunities.append(ident | {'signal_time':b.Index,'direction':'LONG' if b.Signal == 1 else 'SHORT',
                'rule_pass':allowed,'position_occupied':pos is not None,'entry_accepted':accepted,
                'entry_component':entry_rule,'stop_component':stop_rule,
                'decision_reason':'ACCEPTED' if accepted else 'FILTER_AND_OCCUPIED' if not allowed and pos is not None else 'FILTER_FAILED' if not allowed else 'POSITION_OCCUPIED',
                'ATR':b.ATR,'PreviousATR':b.PreviousATR,'H1ATRRatio':b.H1ATRRatio,
                'H1PreviousATRRatio':b.H1PreviousATRRatio,'H1AvailableAt':b.H1AvailableAt,
                'H1PreviousAvailableAt':b.H1PreviousAvailableAt})
            if accepted:
                sign,entry = int(b.Signal),float(b.Close)
                initial = entry-sign*p.stop_atr*float(b.ATR)
                risk = abs(entry-initial)
                assert risk > 0
                pos = {'sign':sign,'entry':entry,'initial_stop':initial,'risk':risk,'stop':initial,
                    'at':b.Index,'index':i,'id':f'T3-M15-{alias}-{len(records)+1:06d}',
                    'level':b.PriorHigh if sign == 1 else b.PriorLow,'extreme':entry,'min':entry,'max':entry,
                    'updates':0,'activated':False,'activation_time':None,'stop_source':'INITIAL_STOP',
                    'entry_features':{c:getattr(b,c) for c in ('ATR','PreviousATR','H1ADX','H1PreviousADX',
                        'H1Slope','H1PreviousSlope','H1ATRRatio','H1PreviousATRRatio','H1AvailableAt','H1PreviousAvailableAt')} |
                        {'signal_open':b.Open,'signal_high':b.High,'signal_low':b.Low}}
    if pos:
        q = pos
        opened = ident | {'trade_id':q['id'],'direction':'LONG' if q['sign'] == 1 else 'SHORT',
            'entry_time':q['at'].isoformat(),'entry_price':q['entry'],'initial_stop':q['initial_stop'],
            'initial_risk':q['risk'],'active_stop':q['stop'],'breakout_level':q['level'],
            'last_close':low.index[-1].isoformat(),'last_close_price':float(low.Close.iloc[-1]),
            'unrealized_gross_R_at_last_close':q['sign']*(float(low.Close.iloc[-1])-q['entry'])/q['risk'],
            'pending_exit_decision':None,'threshold_activated':q['activated'],
            'activation_time':q['activation_time'].isoformat() if q['activation_time'] is not None else None,
            'favorable_extreme':q['extreme'],'stop_source':q['stop_source'],'stop_updates':q['updates'],
            'status':'OPEN_NOT_LIQUIDATED_EXCLUDED_FROM_CLOSED_TRADE_METRICS'}
    return records,opened,decisions,opportunities
