"""Four standalone initial stops; immutable #490 indicators, original ATR trailing."""
import importlib.util
from pathlib import Path
import sys
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
FROZEN = HERE.parent/'t3_m15_forever_v1'
spec = importlib.util.spec_from_file_location('initial_stop_frozen_indicators', FROZEN/'engine.py')
E = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = E
spec.loader.exec_module(E)
MAIN = '8513203e6e6d9f6995d9464ecd29bb75775400d3'
RULES = ('CONTROL','I1','I2','I3')


def tick(symbol, at):
    if symbol == 'CNYRUBF':
        return .01 if at < pd.Timestamp('2023-09-27 19:00',tz=E.TZ) else .001
    return {'USDRUBF':.01,'GLDRUBF':.1,'IMOEXF':.5}[symbol]


def features(frame, p):
    low, high = E.indicators(frame, p)
    high['ATRRatio'] = high.ATR/high.ATRMean
    high['PreviousADX'] = high.ADX.shift(1)
    high['PreviousSlope'] = high.Slope.shift(1)
    high['PreviousATRRatio'] = high.ATRRatio.shift(1)
    high['AvailableAt'] = high.index
    high['PreviousAvailableAt'] = pd.Series(high.index,index=high.index).shift(1)
    for c in ('ADX','Slope','ATRRatio','PreviousADX','PreviousSlope','PreviousATRRatio','AvailableAt','PreviousAvailableAt'):
        low['H1'+c] = high[c].reindex(low.index,method='ffill')
    low['PreviousATR'] = low.ATR.shift(1)
    return low, high


def initial(b, rule):
    s = int(b.Signal)
    control = float(b.Close)-s*2.*float(b.ATR)
    extreme = float(b.Low if s == 1 else b.High)
    if rule == 'CONTROL':return control
    if rule == 'I1':return extreme
    if rule == 'I2':return float(b.PriorHigh if s == 1 else b.PriorLow)
    if rule == 'I3':return max(control,extreme) if s == 1 else min(control,extreme)
    raise ValueError(rule)


def execute(low, symbol, version, p, rule):
    assert rule in RULES and p.stop_atr == 2.
    assert not (low.index >= E.END).any(), 'FUTURE_OHLC_FORBIDDEN'
    ident = {'version':version,'rule':rule,'instrument':symbol}
    records, decisions, opportunities, snapshots, pos = [],[],[],[],None
    alias = E.ALIASES.get(symbol,symbol)
    def state(q, b):
        if q is None:return None
        return ident | {'trade_id':q['id'],'direction':'LONG' if q['sign']==1 else 'SHORT',
            'entry_time':q['at'].isoformat(),'entry_price':q['entry'],'initial_stop':q['initial_stop'],
            'initial_risk':q['risk'],'active_stop':q['stop'],'breakout_level':q['level'],
            'ATR':q['entry_features']['ATR'],'reference_2ATR_risk':q['reference'],
            'entry_exchange_tick':q['tick'],'initial_risk_exchange_ticks':q['risk']/q['tick'],
            'last_close':b.Index.isoformat(),'last_close_price':float(b.Close),
            'unrealized_gross_R_at_last_close':q['sign']*(float(b.Close)-q['entry'])/q['risk'],
            'unrealized_reference_2ATR_R':q['sign']*(float(b.Close)-q['entry'])/q['reference'],
            'status':'OPEN_NOT_LIQUIDATED_EXCLUDED_FROM_CLOSED_TRADE_METRICS'}
    previous = None
    for i,b in enumerate(low.itertuples()):
        if previous is not None and previous.Index.year != b.Index.year and pos:
            snapshots.append(state(pos,previous) | {'year':previous.Index.year})
        at_open = b.Index-pd.Timedelta(minutes=15)
        if pos is not None:
            q = pos
            s,entry,stop,risk = q['sign'],q['entry'],q['stop'],q['risk']
            opening_hit = s*(b.Open-stop) <= 0
            hit = opening_hit or (b.Low <= stop if s == 1 else b.High >= stop)
            d = ident | {'trade_id':q['id'],'bar_open_time':at_open,'bar_close_time':b.Index,
                'active_stop':stop,'initial_risk':risk,'extreme_before':q['extreme'],
                'open':b.Open,'high':b.High,'low':b.Low,'ATR_at_close':b.ATR,
                'stop_hit':bool(hit),'stop_gap':bool(opening_hit and b.Open != stop)}
            if hit:
                fill = min(b.Open,stop) if s == 1 else max(b.Open,stop)
                profit = s*(fill-entry)
                records.append(ident | {'trade_id':q['id'],'direction':'LONG' if s == 1 else 'SHORT',
                    'entry_time':q['at'],'entry_price':entry,'initial_stop':q['initial_stop'],'initial_risk':risk,
                    'breakout_level':q['level'],'exit_time':b.Index,'exit_bar_open_time':at_open,
                    'exit_bar_close_time':b.Index,'exit_price':fill,'gross_R':profit/risk,
                    'gross_price_pnl':profit,'reference_2ATR_risk':q['reference'],'reference_2ATR_R':profit/q['reference'],
                    'entry_exchange_tick':q['tick'],'initial_risk_exchange_ticks':risk/q['tick'],
                    'initial_risk_ATR':risk/q['entry_features']['ATR'],
                    'exit_type':'INITIAL_STOP' if stop == q['initial_stop'] else 'RATCHETED_STOP',
                    'active_stop_at_exit':stop,'trailing_updates':q['updates'],'gap_exit':bool(fill != stop),
                    'exit_at_open':bool(opening_hit),'rule_decision_time':None,'rule_stop_conflict_at_open':False,
                    'bars_held':i-q['index'],'holding_minutes':(b.Index-q['at']).total_seconds()/60,
                    'MAE_R':max(0.,entry-q['min'] if s == 1 else q['max']-entry,s*(entry-fill))/risk,
                    'MFE_R':max(0.,q['max']-entry if s == 1 else entry-q['min'])/risk,
                    'cross_calendar_day':bool(b.Index.normalize() != q['at'].normalize()),'year':b.Index.year,
                    **q['entry_features']})
                d.update(phase='EXIT',exit_price=fill,extreme_after=None,trail_proposal=None,
                    active_stop_next_bar=None,trailing_changed=False)
                pos = None
            else:
                q['min'],q['max'] = min(q['min'],b.Low),max(q['max'],b.High)
                q['extreme'] = max(q['extreme'],b.High) if s == 1 else min(q['extreme'],b.Low)
                proposal = q['extreme']-s*p.trail_atr*b.ATR
                q['stop'] = max(stop,proposal) if s == 1 else min(stop,proposal)
                changed = q['stop'] != stop
                q['updates'] += int(changed)
                d.update(phase='SURVIVED',exit_price=None,extreme_after=q['extreme'],trail_proposal=proposal,
                    active_stop_next_bar=q['stop'],trailing_changed=bool(changed))
            decisions.append(d)
        if b.Signal:
            s,entry = int(b.Signal),float(b.Close)
            stop = initial(b,rule)
            risk = abs(entry-stop)
            valid = np.isfinite(risk) and risk > 0 and np.isfinite(entry) and np.isfinite(stop)
            reason = 'NONFINITE_INITIAL_RISK' if not np.isfinite(risk) else 'NONPOSITIVE_INITIAL_RISK' if risk <= 0 else 'VALID'
            occupied = pos is not None
            accepted = not occupied and valid
            outcome = 'POSITION_OCCUPIED' if occupied else 'ACCEPTED' if valid else reason
            etick = tick(symbol,b.Index)
            tid = f'T3-M15-{alias}-{len(records)+1:06d}' if accepted else None
            opportunities.append(ident | {'signal_time':b.Index,'direction':'LONG' if s == 1 else 'SHORT',
                'entry_price':entry,'candidate_initial_stop':stop,'candidate_initial_risk':risk,'ATR':b.ATR,
                'reference_2ATR_risk':2.*b.ATR,'entry_exchange_tick':etick,'candidate_risk_exchange_ticks':risk/etick,
                'signal_open':b.Open,'signal_high':b.High,'signal_low':b.Low,
                'PriorHigh':b.PriorHigh,'PriorLow':b.PriorLow,'H1AvailableAt':b.H1AvailableAt,
                'initial_stop_valid':bool(valid),'validity_reason':reason,
                'position_occupied':occupied,'occupied_trade_id':pos['id'] if occupied else None,
                'entry_accepted':bool(accepted),'outcome':outcome,'trade_id':tid})
            if accepted:
                pos = {'sign':s,'entry':entry,'at':b.Index,'index':i,'id':tid,'risk':risk,
                    'initial_stop':stop,'stop':stop,'reference':2.*float(b.ATR),'tick':etick,
                    'level':b.PriorHigh if s == 1 else b.PriorLow,'extreme':entry,'min':entry,'max':entry,'updates':0,
                    'entry_features':{c:getattr(b,c) for c in ('ATR','PreviousATR','H1ADX','H1PreviousADX',
                        'H1Slope','H1PreviousSlope','H1ATRRatio','H1PreviousATRRatio','H1AvailableAt','H1PreviousAvailableAt')} |
                        {'signal_open':b.Open,'signal_high':b.High,'signal_low':b.Low}}
        previous = b
    opened = state(pos,previous)
    if opened:snapshots.append(opened | {'year':previous.Index.year})
    return records,opened,decisions,opportunities,snapshots
