"""Seven frozen single mechanisms over the read-only PR #490 indicator oracle.

No cost calculations. Stop chronology and Close-entry convention are historical.
"""
import importlib.util
from pathlib import Path
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
FROZEN = HERE.parent / 't3_m15_forever_v1'
spec = importlib.util.spec_from_file_location('entry_regime_frozen_features', FROZEN/'engine.py')
E = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = E
spec.loader.exec_module(E)

MAIN = '758a0ac1deda8bfa7aa1bc99d8a97a33a9357f02'
RULES = ('CONTROL', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7')


def features(frame, p):
    low, high = E.indicators(frame, p)
    high['ATRRatio'] = high.ATR/high.ATRMean
    high['PreviousADX'] = high.ADX.shift(1)
    high['PreviousSlope'] = high.Slope.shift(1)
    high['PreviousATRRatio'] = high.ATRRatio.shift(1)
    high['AvailableAt'] = high.index
    high['PreviousAvailableAt'] = pd.Series(high.index, index=high.index).shift(1)
    for col in ('ADX', 'Slope', 'ATRRatio', 'PreviousADX', 'PreviousSlope',
                'PreviousATRRatio', 'AvailableAt', 'PreviousAvailableAt'):
        low['H1'+col] = high[col].reindex(low.index, method='ffill')
    low['PreviousATR'] = low.ATR.shift(1)
    return low, high


def permits(b, rule):
    if rule in ('CONTROL', 'A1', 'A2'):
        return True
    if rule == 'A3':
        return b.High > b.Low and abs(b.Close-b.Open) >= .5*(b.High-b.Low) and b.Signal*(b.Close-b.Open) > 0
    if rule == 'A4':
        return b.H1ADX > b.H1PreviousADX
    if rule == 'A5':
        return b.H1Slope > b.H1PreviousSlope if b.Signal == 1 else abs(b.H1Slope) > abs(b.H1PreviousSlope)
    if rule == 'A6':
        return b.H1ATRRatio > b.H1PreviousATRRatio
    if rule == 'A7':
        return b.ATR > b.PreviousATR
    raise ValueError(rule)


def execute(low, symbol, version, p, rule):
    assert rule in RULES
    records, decisions, opportunities, pos = [], [], [], None
    alias = E.ALIASES.get(symbol, symbol)
    def identity():
        return {'version':version, 'rule':rule, 'instrument':symbol}
    for i, b in enumerate(low.itertuples()):
        at_open = b.Index-pd.Timedelta(minutes=15)
        if pos is not None:
            sign, entry, stop = pos['sign'], pos['entry'], pos['stop']
            # A pending market exit is known BEFORE this bar. No intrabar Low/High
            # may override its Open fill. A protective gap at that Open wins ties.
            open_stop = sign*(b.Open-stop) <= 0
            pending = pos['pending'] is not None
            hit = b.Low <= stop if sign == 1 else b.High >= stop
            if open_stop or pending or hit:
                protective = open_stop or not pending
                fill = (min(b.Open, stop) if sign == 1 else max(b.Open, stop)) if protective else b.Open
                exit_type = ('INITIAL_STOP' if stop == pos['initial_stop'] else 'RATCHETED_STOP') if protective else rule+'_NEXT_OPEN'
                risk = abs(entry-pos['initial_stop'])
                gross = sign*(fill-entry)/risk
                records.append(identity() | {
                    'trade_id':pos['id'], 'direction':'LONG' if sign == 1 else 'SHORT',
                    'entry_time':pos['at'], 'entry_price':entry, 'initial_stop':pos['initial_stop'],
                    'initial_risk':risk, 'breakout_level':pos['level'],
                    # Preserve the original protective-exit candle label exactly.
                    'exit_time':b.Index if protective else at_open,
                    'exit_bar_open_time':at_open, 'exit_bar_close_time':b.Index,
                    'exit_price':fill, 'gross_R':gross, 'exit_type':exit_type,
                    'active_stop_at_exit':stop, 'trailing_updates':pos['updates'],
                    'gap_exit':bool(protective and fill != stop), 'exit_at_open':bool(open_stop or pending),
                    'rule_decision_time':pos['pending'], 'rule_stop_conflict_at_open':bool(pending and open_stop),
                    'bars_held':i-pos['index'],
                    'holding_minutes':((b.Index if protective else at_open)-pos['at']).total_seconds()/60,
                    'MAE_R':max(0., entry-pos['min'] if sign == 1 else pos['max']-entry, sign*(entry-fill))/risk,
                    'MFE_R':max(0., pos['max']-entry if sign == 1 else entry-pos['min'])/risk,
                    **pos['entry_features']})
                pos = None
            else:
                pos['min'] = min(pos['min'], b.Low)
                pos['max'] = max(pos['max'], b.High)
                pos['extreme'] = max(pos['extreme'], b.High) if sign == 1 else min(pos['extreme'], b.Low)
                proposed = pos['extreme']-sign*p.trail_atr*b.ATR
                pos['stop'] = max(stop, proposed) if sign == 1 else min(stop, proposed)
                pos['updates'] += int(pos['stop'] != stop)
                wrong = sign*(b.Close-pos['level']) <= 0
                pos['wrong_run'] = pos['wrong_run']+1 if wrong else 0
                trigger = (rule == 'A1' and i == pos['index']+1 and wrong) or (rule == 'A2' and i-pos['index'] <= 4 and pos['wrong_run'] == 2)
                if trigger:
                    pos['pending'] = b.Index
                if (rule == 'A1' and i-pos['index'] == 1) or (rule == 'A2' and i-pos['index'] <= 4):
                    decisions.append(identity() | {'trade_id':pos['id'], 'decision_time':b.Index,
                        'post_entry_bar':i-pos['index'], 'close':b.Close, 'breakout_level':pos['level'],
                        'wrong_side':bool(wrong), 'consecutive_wrong':pos['wrong_run'],
                        'exit_queued':bool(trigger), 'active_stop_next_bar':pos['stop']})
        if pd.notna(b.ATR) and b.Signal:
            allowed = bool(permits(b, rule))
            accepted = pos is None and allowed
            opportunities.append(identity() | {'signal_time':b.Index, 'direction':'LONG' if b.Signal == 1 else 'SHORT',
                'rule_pass':allowed, 'position_occupied':pos is not None, 'entry_accepted':accepted})
            if accepted:
                sign, entry = int(b.Signal), float(b.Close)
                stop = entry-sign*p.stop_atr*float(b.ATR)
                assert abs(entry-stop) > 0
                pos = {'sign':sign, 'entry':entry, 'at':b.Index, 'index':i,
                    'id':f'T3-M15-{alias}-{len(records)+1:06d}',
                    'initial_stop':stop, 'stop':stop, 'level':b.PriorHigh if sign == 1 else b.PriorLow,
                    'extreme':entry, 'min':entry, 'max':entry, 'updates':0,
                    'wrong_run':0, 'pending':None,
                    'entry_features':{c:getattr(b,c) for c in ('ATR','PreviousATR','H1ADX','H1PreviousADX',
                        'H1Slope','H1PreviousSlope','H1ATRRatio','H1PreviousATRRatio','H1AvailableAt','H1PreviousAvailableAt')} |
                        {'signal_open':b.Open,'signal_high':b.High,'signal_low':b.Low}}
    opened = None
    if pos is not None:
        opened = identity() | {'trade_id':pos['id'], 'direction':'LONG' if pos['sign'] == 1 else 'SHORT',
            'entry_time':pos['at'].isoformat(), 'entry_price':pos['entry'],
            'initial_stop':pos['initial_stop'], 'initial_risk':abs(pos['entry']-pos['initial_stop']),
            'active_stop':pos['stop'], 'breakout_level':pos['level'],
            'last_close':low.index[-1].isoformat(), 'last_close_price':float(low.Close.iloc[-1]),
            'unrealized_gross_R_at_last_close':pos['sign']*(float(low.Close.iloc[-1])-pos['entry'])/abs(pos['entry']-pos['initial_stop']),
            'pending_exit_decision':None if pos['pending'] is None else pos['pending'].isoformat(),
            'status':'OPEN_NOT_LIQUIDATED_EXCLUDED_FROM_CLOSED_TRADE_METRICS'}
    return records, opened, decisions, opportunities
