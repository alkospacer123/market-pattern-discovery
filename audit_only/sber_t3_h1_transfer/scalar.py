"""Independent scalar indicators and lifecycle. No strategy/indicator/state imports.

Same frozen constants; independently groups bars and evaluates all transitions.
Pandas is used only for containers, timestamps and missing-value predicates.
"""
from __future__ import annotations
from decimal import Decimal, ROUND_FLOOR, ROUND_CEILING
import math
import numpy as np
import pandas as pd


def ewm(values, alpha, minimum):
    output, current, count = [], None, 0
    for value in values:
        if math.isfinite(value):
            current = value if current is None else (1 - alpha) * current + alpha * value
            count += 1
        output.append(current if count >= minimum else float('nan'))
    return output


def rolling(values, period, operation):
    return [operation(values[i-period+1:i+1]) if i+1 >= period and all(math.isfinite(v) for v in values[i-period+1:i+1])
            else float('nan') for i in range(len(values))]


def indicators(frame, context=False):
    rows = list(frame.itertuples())
    tr, plus, minus = [], [], []
    for i, r in enumerate(rows):
        prev = rows[i-1] if i else None
        tr.append(max(r.High-r.Low, abs(r.High-prev.Close), abs(r.Low-prev.Close)) if prev else r.High-r.Low)
        up, down = (r.High-prev.High, prev.Low-r.Low) if prev else (0, 0)
        plus.append(up if up > down and up > 0 else 0.)
        minus.append(down if down > up and down > 0 else 0.)
    out = frame.copy()
    atr = ewm(tr, 1/14, 14)
    out['ATR'] = atr
    if context:
        a, b = ewm(plus, 1/14, 14), ewm(minus, 1/14, 14)
        dx = [100*abs(x-y)/(x+y) if math.isfinite(z) and z > 0 and x+y > 0 else float('nan') for x,y,z in zip(a,b,atr)]
        out['ADX'] = ewm(dx, 1/14, 14)
        for period in (50,100,200):
            out[f'EMA{period}'] = ewm([r.Close for r in rows], 2/(period+1), period)
        out['EMA100Slope'] = [out.EMA100.iloc[i]-out.EMA100.iloc[i-5] if i >= 5 else float('nan') for i in range(len(rows))]
        out['ATRMean20'] = rolling(atr,20,lambda x:sum(x)/len(x))
    else:
        out['PriorHigh'] = [max(r.High for r in rows[i-20:i]) if i >= 20 else float('nan') for i in range(len(rows))]
        out['PriorLow'] = [min(r.Low for r in rows[i-20:i]) if i >= 20 else float('nan') for i in range(len(rows))]
    return out


def features(frame):
    groups, pending, date = [], [], None
    for r in frame.itertuples():
        if r.Index.date() != date:
            date, pending = r.Index.date(), []
        pending.append(r)
        if len(pending) == 4:
            groups.append({'time': r.Index, 'Open': pending[0].Open, 'High': max(v.High for v in pending),
                           'Low': min(v.Low for v in pending), 'Close': r.Close})
            pending = []
    high = pd.DataFrame(groups).set_index('time')
    return indicators(frame), indicators(high, True)


def run(frame, long_only=False, grid=None, cost_price=.002, prepared=None):
    low, high = prepared if prepared is not None else features(frame)
    high_rows = list(high.itertuples())
    cursor, pos = -1, None
    out, opened = [], None
    seq = 0
    def tighten(d,a,b): return max(a,b) if d == 'LONG' else min(a,b)
    def project(d,x):
        return float((Decimal(str(x))/Decimal(str(grid))).to_integral_value(rounding=ROUND_FLOOR if d=='LONG' else ROUND_CEILING)*Decimal(str(grid))) if grid else x
    for r in low.itertuples():
        t = r.Index
        while cursor + 1 < len(high_rows) and high_rows[cursor+1].Index <= t:
            cursor += 1
        if pos is not None:
            d = pos['direction']
            if pos['triggered'] and not pos['activated'] and t > pos['trigger_time']:
                pos['activated'], pos['activation_time'] = True, t
                pos['stop'] = project(d, tighten(d,pos['stop'],pos['candidate']))
            stop = pos['stop']
            if (r.Low <= stop if d == 'LONG' else r.High >= stop):
                fill = min(r.Open,stop) if d == 'LONG' else max(r.Open,stop)
                gross = (1 if d=='LONG' else -1)*(fill-pos['entry_price'])/pos['risk']
                out.append({'direction':d,'entry_time':pos['entry_time'],'entry_price':pos['entry_price'],
                            'initial_stop_price':pos['initial_stop'],'initial_risk_price':pos['risk'],
                            'exit_time':t,'exit_price':fill,'final_stop':stop,'gross_R':gross,'cost_R':cost_price/pos['risk'],
                            'net_R':gross-cost_price/pos['risk'],'trail1_triggered':pos['triggered'],
                            'trigger_bar_time':pos['trigger_time'],'trail1_activated':pos['activated'],
                            'trail1_activation_time':pos['activation_time'],'stored_trail_candidate':pos['candidate'],
                            'bars_held':pos['bars']+1})
                pos = None
            else:
                pos['bars'] += 1
                pos['extreme'] = max(pos['extreme'],r.High) if d=='LONG' else min(pos['extreme'],r.Low)
                candidate = project(d,pos['extreme']-3*r.ATR if d=='LONG' else pos['extreme']+3*r.ATR)
                if not pos['triggered'] and (r.High >= pos['entry_price']+pos['risk'] if d=='LONG' else r.Low <= pos['entry_price']-pos['risk']):
                    pos['triggered'], pos['trigger_time'], pos['candidate'] = True,t,candidate
                if pos['activated']:
                    pos['stop'] = tighten(d,stop,candidate)
        if pos is None and cursor >= 0 and math.isfinite(r.ATR):
            h = high_rows[cursor]
            values=(h.Close,h.EMA100,h.EMA100Slope,h.ADX,h.ATR,h.ATRMean20)
            if not all(math.isfinite(x) for x in values) or h.ADX <= 20 or h.ATR <= h.ATRMean20:
                continue
            d = 'LONG' if h.Close > h.EMA100 and h.EMA100Slope > 0 and r.Close > r.PriorHigh else 'SHORT' if h.Close < h.EMA100 and h.EMA100Slope < 0 and r.Close < r.PriorLow else None
            if d is None or (long_only and d == 'SHORT'):
                continue
            stop = project(d,r.Close-2.5*r.ATR if d=='LONG' else r.Close+2.5*r.ATR)
            seq += 1
            pos = {'direction':d,'entry_time':t,'entry_price':r.Close,'initial_stop':stop,'risk':abs(r.Close-stop),
                   'stop':stop,'extreme':r.Close,'bars':0,'triggered':False,'activated':False,'trigger_time':None,
                   'activation_time':None,'candidate':None}
    return pd.DataFrame(out), pos
