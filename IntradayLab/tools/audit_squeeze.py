#!/usr/bin/env python3
"""Independent oracle: raw prefix -> batch features/cycles -> clock state scan.

No imports of Replay, indicators, execution, calendar or metrics from Lab.
Published journals are read only AFTER reconstruction as comparison targets.
"""
import argparse
from collections import Counter
import csv
from datetime import date, datetime as DT, timedelta as TD
from decimal import Decimal as D, ROUND_CEILING, ROUND_FLOOR, localcontext
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

LAB = Path(__file__).resolve().parents[1]
FIVE = TD(minutes=5)
ZERO = D(0)
HOLIDAYS = {(1, 1), (1, 2), (1, 7), (2, 23), (3, 8), (5, 1), (5, 9), (6, 12), (11, 4)}


def intervals(day):
    if day.weekday() >= 5 or (day.month, day.day) in HOLIDAYS:
        return []
    am = DT.combine(day, DT.min.time())+TD(hours=10)
    pm = am+TD(hours=4, minutes=15 if date(2023, 3, 13) <= day < date(2023, 3, 21) else 5)
    return [(am, am+TD(hours=4)), (pm, am+TD(hours=8, minutes=50))]


def window(t):
    return next((w for w in intervals(t.date()) if w[0] <= t and t+FIVE <= w[1]), None)


def step(symbol, at):
    return (D('.01') if at < DT(2023, 9, 27, 19) else D('.001')) if symbol == 'CNYRUBF' else {'USDRUBF': D('.01'), 'GLDRUBF': D('.1'), 'IMOEXF': D('.5')}[symbol]


def quant(value, delta, up):
    return (value/delta).to_integral_value(rounding=ROUND_CEILING if up else ROUND_FLOOR)*delta


def future(now):
    minutes = now.hour*60+now.minute
    return now.replace(hour=0, minute=0, second=0, microsecond=0)+TD(minutes=(minutes//5+1)*5)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load_source(root):
    manifest = json.loads((LAB/'config/stage2_squeeze_v1.json').read_text())
    def git(*args):
        return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()
    assert git('rev-parse', 'HEAD') == manifest['source_ref'] and not git('status', '--porcelain')
    data, provenance = {}, {}
    for symbol, spec in sorted(manifest['inputs'].items()):
        assert git('ls-files', '--stage', '--', spec['path']).split()[1] == spec['blob']
        path = root/spec['path']
        before = path.stat()
        with path.open('rb', buffering=0) as stream:
            raw = stream.read(spec['prefix_bytes'])
        assert len(raw) == spec['prefix_bytes'] and sha(raw) == spec['prefix_sha256'] and raw.endswith(b'\n')
        lines = raw.decode('utf-8-sig').splitlines()
        assert lines[0] == 'Ticker;Datetime;Open;High;Low;Close;Volume' and len(lines) == spec['rows_2023']+1
        values = {}
        for line in lines[1:]:
            parts = line.split(';')
            t = DT.fromisoformat(parts[1])
            assert t.year == 2023 and parts[0] == symbol and t not in values
            o, h, l, c, v = map(D, parts[2:])
            assert l <= min(o, c) <= max(o, c) <= h and v >= 0
            assert all(x % step(symbol, t) == 0 for x in (o, h, l, c))
            values[t] = (o, h, l, c, v)
        assert list(values) == sorted(values) and path.stat() == before
        data[symbol] = values
        provenance[symbol] = dict(rows=len(values), bytes_read=len(raw), prefix_sha256=sha(raw), protected_year_bytes_read=0)
    return data, provenance


def batch_indicators(idx):
    """Separate segment arrays, variance E[C²]-E[C]², EMA weighted history."""
    out, segment, prev_w = {}, [], None
    for t, bar in idx.items():
        w = window(t)
        if not w or bar[4] <= 0:
            segment, prev_w = [], None
            continue
        if w != prev_w or (segment and segment[-1][0]+FIVE != t):
            segment = []
        segment.append((t, bar))
        prev_w = w
        n = len(segment)
        if n < 20:
            continue
        # Recompute from raw segment for each frame, independent of streaming state.
        closes = [b[3] for _, b in segment]
        trs = [b[1]-b[2] if i == 0 else max(b[1]-b[2], abs(b[1]-segment[i-1][1][3]), abs(b[2]-segment[i-1][1][3])) for i, (_, b) in enumerate(segment)]
        mean = sum(closes[-20:], ZERO)/20
        variance = sum((x*x for x in closes[-20:]), ZERO)/20-mean*mean
        sigma = max(variance, ZERO).sqrt()
        seed = sum(closes[:20], ZERO)/20
        ema = (D(19)/21)**(n-20)*seed+sum((D(2)/21*(D(19)/21)**(n-1-i)*closes[i] for i in range(20, n)), ZERO)
        atr_seed = sum(trs[:20], ZERO)/20
        atr = (D(19)/20)**(n-20)*atr_seed+sum((D(1)/20*(D(19)/20)**(n-1-i)*trs[i] for i in range(20, n)), ZERO)
        ub, lb, uk, lk = mean+2*sigma, mean-2*sigma, ema+D('1.5')*atr, ema-D('1.5')*atr
        out[t] = dict(at=t, warmup=n, sma20=mean, variance20=variance, std20=sigma, ema20=ema,
                      tr=trs[-1], atr20=atr, bb_upper=ub, bb_lower=lb, kc_upper=uk, kc_lower=lk,
                      squeeze=ub < uk and lb > lk)
    return out


def cycles_and_signals(idx, symbol, frames, delay):
    episodes, signals, active = [], {}, None
    def discard(now, why):
        nonlocal active
        if active and not active['terminal_reason']:
            active.update(terminal_at=now, terminal_reason=why if active['bars'] >= 3 else 'UNCONFIRMED_LT3')
        active = None
    day, prev_w = min(idx).date(), None
    while day <= date(2023, 12, 31):
        if intervals(day):
            now = DT.combine(day, DT.min.time())+TD(hours=10)
            while now <= DT.combine(day, DT.min.time())+TD(hours=19, minutes=10):
                t, w = now-TD(minutes=delay), window(now-TD(minutes=delay))
                b = idx.get(t) if w else None
                if b and b[4] <= 0:
                    b = None
                if w != prev_w or (w and b is None):
                    discard(now, 'NO_EXPANSION_SESSION' if w != prev_w else 'NO_EXPANSION_GAP')
                prev_w = w
                f = frames.get(t) if b else None
                if f:
                    if f['squeeze']:
                        if active and active['released_at'] is not None:
                            discard(now, 'NO_EXPANSION_NEXT_SQUEEZE')
                        if active is None:
                            active = dict(cycle_id=f'SQ_{symbol}_{len(episodes)+1:06d}', start=t, end=t, bars=0,
                                          range_high=b[1], range_low=b[2], confirmed_at=None, released_at=None,
                                          terminal_at=None, terminal_reason='', signal_at=None, direction=None)
                            episodes.append(active)
                        active.update(end=t, bars=active['bars']+1, range_high=max(active['range_high'], b[1]), range_low=min(active['range_low'], b[2]))
                        if active['bars'] == 3:
                            active['confirmed_at'] = now
                    elif active and not active['terminal_reason']:
                        if active['released_at'] is None:
                            active['released_at'] = now
                        if active['bars'] < 3:
                            discard(now, 'UNCONFIRMED_LT3')
                        else:
                            d = 1 if b[3] > active['range_high'] else -1 if b[3] < active['range_low'] else 0
                            if d:
                                active.update(terminal_at=now, terminal_reason='SIGNAL', signal_at=t, direction='LONG' if d == 1 else 'SHORT')
                                signals[t] = dict(signal_id=active['cycle_id'], direction_sign=d, direction=active['direction'],
                                                  range_start=active['start'], range_end=active['end'], squeeze_bars=active['bars'],
                                                  range_high=active['range_high'], range_low=active['range_low']) | f
                now += FIVE
        day += TD(days=1)
    discard(DT(2024, 1, 1), 'NO_EXPANSION_YEAR_END')
    return episodes, signals


def m30(idx, now, w, delay, direction):
    last = now-TD(minutes=25+delay)
    total = last.hour*60+last.minute
    last = last.replace(hour=0, minute=0)+TD(minutes=(total//30)*30)
    starts = (last-TD(minutes=30), last)
    rec = dict(mtf_first=None, mtf_last=None, mtf_available_at=None, mtf_direction=None, mtf_reason='MTF_TWO_PARENTS_NOT_READY')
    if starts[0] < w[0] or last+TD(minutes=30) > w[1]:
        return rec
    parents = []
    for t in starts:
        times = [t+i*FIVE for i in range(6)]
        if any(x not in idx or idx[x][4] <= 0 or window(x) != w for x in times):
            rec['mtf_reason'] = 'MTF_INCOMPLETE_CHILD_BUCKET'
            return rec
        kids = [idx[x] for x in times]
        parents.append((kids[0][0], max(x[1] for x in kids), min(x[2] for x in kids), kids[-1][3], sum((x[4] for x in kids), ZERO)))
    a, b = parents
    trend = 1 if a[3] > a[0] and b[3] > b[0] and b[3] > a[3] else -1 if a[3] < a[0] and b[3] < b[0] and b[3] < a[3] else 0
    rec.update(mtf_first=starts[0], mtf_last=last, mtf_available_at=last+TD(minutes=25+delay), mtf_direction=trend,
               mtf_reason='MTF_SUSTAINED_ADVERSE_DIRECTION' if trend == -direction else None)
    assert rec['mtf_available_at'] <= now
    return rec


def admissible(symbol, s, price, at):
    delta, d = step(symbol, at), s['direction_sign']
    r = d*(price-s['stop'])
    if price % delta:
        return None, 'OPEN_OFF_GRID'
    if d*(price-s['edge']) <= 0:
        return None, 'BREAKOUT_NOT_PERSISTENT'
    if d*(price-s['cap']) > 0:
        return None, 'EXTENSION_OVER_0_5_ATR'
    if r < 4*delta:
        return None, 'RISK_BELOW_FOUR_TICKS'
    take = quant(price+d*(3*r+2*delta), delta, d > 0)
    reward = d*(take-price)
    if reward > 3*s['atr20']:
        return None, 'TARGET_OVER_THREE_ATR'
    return dict(take=take, initial_risk=r, planned_c1=2*delta, planned_gross_reward=reward,
                planned_net_reward=reward-2*delta, planned_net_RR=(reward-2*delta)/r, target_atr=reward/s['atr20']), None


def reconstruct(idx, symbol, architecture, delay, frames):
    episodes, opportunity = cycles_and_signals(idx, symbol, frames, delay)
    signals, ledger, events = [], [], []
    pos = pending = exit_request = None
    def event(t, kind, sid='', why='', price=None, ack=None, flags=''):
        events.append(dict(at=t, kind=kind, signal_id=sid, reason=why, price=price, confirmed_at=ack, flags=flags))
    def ask(now, why):
        nonlocal exit_request
        if exit_request is None:
            exit_request = (future(now), why)
            event(now, 'EXIT_ORDER', pos['signal_id'], why)
    def uncertain(now, why):
        if pos['status'] != 'UNKNOWN':
            pos.update(status='UNKNOWN', gross=None, c1_exit=None, c1=None, net=None, net_R=None,
                       unknown_at=now, unknown_reason=why, excursion_status='LOWER_BOUND_BEFORE_UNKNOWN')
            event(now, 'UNKNOWN_PATH', pos['signal_id'], why)
        ask(now, 'DATA_GAP_EMERGENCY')
    def finish(t, now, price, why, flags=''):
        nonlocal pos, exit_request
        if pos['status'] == 'UNKNOWN':
            pos.update(exit_reason='UNKNOWN_PATH_REDUCE_ALL', model_flat_at=now, model_flat_slot=t)
            event(t, 'CONDITIONAL_FLAT', pos['signal_id'], 'PAST_PAYOFF_REMAINS_UNKNOWN', ack=now)
        else:
            gross = pos['direction_sign']*(price-pos['entry'])
            cost = pos['c1_entry']+step(symbol, t)
            pos['mfe_R'] = max(pos['mfe_R'], gross/pos['initial_risk'])
            pos['mae_R'] = max(pos['mae_R'], -gross/pos['initial_risk'])
            pos.update(status='CLOSED', exit=price, exit_at=t, exit_ack=now, exit_reason=why,
                       gross=gross, c1_exit=step(symbol, t), c1=cost, net=gross-cost, net_R=(gross-cost)/pos['initial_risk'],
                       gross_R=gross/pos['initial_risk'], hold_minutes=int((t-pos['entry_at']).total_seconds()/60),
                       flags=flags, model_flat_at=now, model_flat_slot=t)
            event(t, 'EXIT', pos['signal_id'], why, price, now, flags)
        pos = exit_request = None
    def protect(t, now, b, initial=False):
        o, h, l, c, _ = b
        d, st, tp, delta = pos['direction_sign'], pos['stop'], pos['take'], step(symbol, t)
        stopped = l <= st if d > 0 else h >= st
        reached = h >= tp+delta if d > 0 else l <= tp-delta
        if stopped:
            flags = []
            if reached:
                flags.append('STOP_FIRST_BOTH_LEVELS')
            if initial:
                flags.append('ENTRY_BAR_STOP')
            if d*(o-st) <= 0:
                flags.append('ADVERSE_STOP_GAP')
            finish(t, now, min(o, st) if d > 0 else max(o, st), 'STOP', '|'.join(flags))
        elif reached and not initial:
            pos['mfe_R'] = max(pos['mfe_R'], d*(tp-pos['entry'])/pos['initial_risk'])
            finish(t, now, tp, 'TAKE')
        else:
            if not initial:
                pos['mfe_R'] = max(pos['mfe_R'], d*((h if d > 0 else l)-pos['entry'])/pos['initial_risk'])
                pos['mae_R'] = max(pos['mae_R'], -d*((l if d > 0 else h)-pos['entry'])/pos['initial_risk'])
            if reached and initial:
                event(t, 'TP_NONFILL', pos['signal_id'], 'ENTRY_BAR_TP_FORBIDDEN', ack=now)
            elif h >= tp if d > 0 else l <= tp:
                event(t, 'TP_NONFILL', pos['signal_id'], 'TOUCH_WITHOUT_TICK_PENETRATION', ack=now)
    day = min(idx).date()
    while day <= date(2023, 12, 31):
        if intervals(day):
            now = DT.combine(day, DT.min.time())+TD(hours=10)
            while now <= DT.combine(day, DT.min.time())+TD(hours=19, minutes=10):
                t = now-TD(minutes=delay)
                w = window(t)
                b = idx.get(t) if w else None
                if b and b[4] <= 0:
                    b = None
                if b:
                    if pos and t >= pos['entry_at']:
                        if exit_request and t >= exit_request[0]:
                            finish(t, now, b[0], exit_request[1])
                        elif pos['status'] != 'UNKNOWN' and t > pos['entry_at']:
                            protect(t, now, b)
                    if pending and t == pending['planned_execution_at']:
                        s, pending = pending, None
                        g, why = admissible(symbol, s, b[0], t)
                        if why:
                            s.update(status='NONFILL', reason=why)
                            event(t, 'ENTRY_NONFILL', s['signal_id'], why, ack=now)
                        else:
                            s.update(status='MODELLED', reason='CONDITIONAL_EXACT_OPEN')
                            pos = {k: s[k] for k in ('signal_id', 'direction', 'direction_sign', 'signal_at', 'available_at', 'planned_execution_at', 'range_high', 'range_low', 'edge', 'atr20', 'stop', 'cap')}
                            pos.update(g)
                            pos.update(status='OPEN', entry=b[0], entry_at=t, entry_ack=now, c1_entry=step(symbol, t), c1_exit=None, c1=None, gross=None, net=None,
                                       net_R=None, gross_R=None, exit=None, exit_at=None, exit_ack=None, exit_reason='', hold_minutes=None,
                                       model_flat_at=None, model_flat_slot=None, unknown_at=None, unknown_reason='', flat_target_breach=False,
                                       flags='', mfe_R=ZERO, mae_R=ZERO, excursion_status='CONSERVATIVE_KNOWN_PATH', boundary=w[1])
                            ledger.append(pos)
                            event(t, 'ENTRY', pos['signal_id'], 'CONDITIONAL_EXACT_OPEN', b[0], now)
                            protect(t, now, b, True)
                if pending and t >= pending['planned_execution_at']:
                    s, pending = pending, None
                    s.update(status='NO_BAR_NO_MODEL_FILL', reason='EXACT_TARGET_ABSENT')
                    event(s['planned_execution_at'], 'ENTRY_NONFILL', s['signal_id'], s['reason'], ack=now)
                if w and b is None:
                    if pending and pending['planned_execution_at'] > now:
                        s, pending = pending, None
                        s.update(status='NONFILL', reason='OBSERVED_GAP_BEFORE_ENTRY')
                        event(now, 'ENTRY_CANCEL', s['signal_id'], s['reason'])
                    if pos and t >= pos['entry_at']:
                        uncertain(now, 'MISSING_EXPOSED_M5_PATH')
                if pos:
                    boundary = pos['boundary']
                    if now >= boundary-TD(minutes=10) and not pos['flat_target_breach']:
                        pos['flat_target_breach'] = True
                        event(now, 'FLAT_TARGET_BREACH', pos['signal_id'], 'NO_ACK_FLAT_AT_B_MINUS_10')
                    if now >= boundary:
                        uncertain(now, 'SESSION_BOUNDARY_EXPOSURE_UNRESOLVED')
                    deadline = boundary-TD(minutes=20)
                    while future(deadline)+TD(minutes=delay) > boundary-TD(minutes=10):
                        deadline -= FIVE
                    if now >= deadline:
                        ask(now, 'SESSION_FLAT')
                    elif now >= pos['entry_at']+TD(minutes=115):
                        ask(now, 'MAX_HOLD')
                    if b and t >= pos['entry_at'] and exit_request is None and pos['status'] != 'UNKNOWN' and pos['range_low'] <= b[3] <= pos['range_high']:
                        ask(now, 'FAILED_BREAKOUT')
                if t in opportunity and b:
                    s = opportunity[t].copy()
                    d, delta = s['direction_sign'], step(symbol, now)
                    edge = s['range_high'] if d > 0 else s['range_low']
                    s.update(signal_at=t, signal_close=b[3], available_at=now, ready_at=now, planned_execution_at=future(now), edge=edge,
                             stop=quant(edge-d*s['atr20']/4, delta, d > 0), cap=quant(edge+d*s['atr20']/2, delta, d < 0),
                             status='SUBMITTED', reason='', mtf_first=None, mtf_last=None, mtf_available_at=None, mtf_direction=None, mtf_reason=None)
                    if architecture == 'SQUEEZE_M30_M5':
                        s.update(m30(idx, now, w, delay, d))
                    _, why = admissible(symbol, s, b[3], now)
                    if pos or pending:
                        why = 'POSITION_OR_ORDER_BUSY'
                    elif window(s['planned_execution_at']) != w or s['planned_execution_at']+FIVE > w[1]-TD(minutes=30):
                        why = 'KNOWN_BOUNDARY_ENTRY_CUTOFF'
                    elif s['mtf_reason']:
                        why = s['mtf_reason']
                    if why:
                        s.update(status='FILTERED', reason=why)
                    else:
                        pending = s
                        event(now, 'ENTRY_ORDER', s['signal_id'], 'FIXED_SQUEEZE_BREAKOUT')
                    signals.append(s)
                now += FIVE
        day += TD(days=1)
    if pos:
        uncertain(DT(2024, 1, 1), 'UNRESOLVED_AT_DEVELOPMENT_END')
    return dict(signals=signals, trade_ledger=ledger, execution_events=events, squeeze_cycles=episodes)


def table(path):
    raw = gzip.decompress(path.read_bytes()) if path.suffix == '.gz' else path.read_bytes()
    return list(csv.DictReader(raw.decode().splitlines()))


def equal(expected, actual):
    if expected is None:
        return actual == ''
    if isinstance(expected, D):
        return actual != '' and abs(expected-D(actual)) <= D('1e-24')*max(D(1), abs(expected))
    return str(expected) == actual


def compare(expected, actual, label):
    assert len(expected) == len(actual), (label, 'count', len(expected), len(actual))
    for i, (a, b) in enumerate(zip(expected, actual)):
        for k, value in a.items():
            assert k in b and equal(value, b[k]), (label, i, k, str(value), b.get(k))
    return sum(len(r) for r in expected)


def aggregate(rows, cost=1):
    closed = [r for r in rows if r['status'] == 'CLOSED']
    n = len(closed)
    nets = [r['gross']-cost*r['c1'] for r in closed]
    positive = sum((x for x in nets if x > 0), ZERO)
    negative = -sum((x for x in nets if x < 0), ZERO)
    w, l = sum(x > 0 for x in nets), sum(x < 0 for x in nets)
    avg_w, avg_l = positive/w if w else None, negative/l if l else None
    gw = [r['gross'] for r in closed if r['gross'] > 0]
    gl = [-r['gross'] for r in closed if r['gross'] < 0]
    cum = high = dd = ZERO
    high_at, recovery = min((r['entry_at'] for r in closed), default=None), 0
    for r in sorted(closed, key=lambda x: (x['exit_ack'], x['signal_id'])):
        cum += r['gross']-cost*r['c1']
        if cum >= high:
            high, high_at = cum, r['exit_ack']
        elif high_at:
            recovery = max(recovery, int((r['exit_ack']-high_at).total_seconds()/60))
        dd = max(dd, high-cum)
    top = sorted((x for x in nets if x > 0), reverse=True)
    return dict(entries=len(rows), closed=n, unknown=len(rows)-n, closed_gross=sum((r['gross'] for r in closed), ZERO),
                closed_cost=sum((cost*r['c1'] for r in closed), ZERO), closed_net=sum(nets, ZERO), closed_net_PF=positive/negative if negative else None,
                closed_expectancy=sum(nets, ZERO)/n if n else None, closed_win_rate=D(w)/n if n else None,
                average_net_win=avg_w, average_net_loss=avg_l, realized_net_win_loss_RR=avg_w/avg_l if avg_w is not None and avg_l else None,
                realized_gross_win_loss_RR=(sum(gw, ZERO)/len(gw))/(sum(gl, ZERO)/len(gl)) if gw and gl else None,
                closed_net_R=sum((net/r['initial_risk'] for net, r in zip(nets, closed)), ZERO), mean_net_R=sum((net/r['initial_risk'] for net, r in zip(nets, closed)), ZERO)/n if n else None,
                closed_realized_DD=dd if n else None, closed_unrecovered_minutes=recovery,
                largest_winner_share=top[0]/positive if top else None,
                top3_winner_share=sum(top[:3], ZERO)/positive if top else None,
                top5_winner_share=sum(top[:5], ZERO)/positive if top else None,
                closed_net_without_top1=sum(nets, ZERO)-(top[0] if top else ZERO),
                known_entry_cost_unknown=sum((cost*r['c1_entry'] for r in rows if r['status'] != 'CLOSED'), ZERO))


def calendar(idx):
    first = min(idx)
    coverage, days = {}, {}
    for m in range(1, 13):
        day = date(2023, m, 1)
        slots = set()
        while day.month == m and day.year == 2023:
            for a, z in intervals(day):
                times = {a+i*FIVE for i in range(int((z-a)/FIVE))}
                slots |= times
                if day >= first.date():
                    e, o = days.get(day, (0, 0))
                    days[day] = (e+len(times), o+sum(t in idx and idx[t][4] > 0 for t in times))
            day += TD(days=1)
        observed = {t for t in slots if t in idx and idx[t][4] > 0}
        missing = {t for t in slots-observed if t >= first}
        status = 'NO_COVERAGE' if m < first.month else 'PARTIAL_LAUNCH' if any(t < first for t in slots) else 'PARTIAL_DATA' if missing else 'COVERED'
        coverage[f'2023-{m:02d}'] = dict(coverage_status=status, expected_slots=len(slots), observed_slots=len(observed), missing_since_inception=len(missing), pre_inception_slots=sum(t < first for t in slots))
    return coverage, days


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--data-root', type=Path, required=True)
    p.add_argument('--results', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    assert not args.output.exists(), 'Fresh audit output only'
    args.output.mkdir(parents=True)
    reconstructed, summaries, checked = {}, [], Counter()
    with localcontext() as ctx:
        ctx.prec = 50
        data, provenance = load_source(args.data_root)
        # Reconstruct every outcome without any published result as input.
        for symbol, idx in data.items():
            features = batch_indicators(idx)
            for architecture in ('SQUEEZE_M5', 'SQUEEZE_M30_M5'):
                for delay in (10, 15):
                    reconstructed[symbol, architecture, delay] = reconstruct(idx, symbol, architecture, delay, features)
            reconstructed[symbol, 'FEATURES', 0] = list(features.values())
        published = {name: table(args.results/f'{name}.csv.gz') for name in ('signals', 'trade_ledger', 'execution_events', 'squeeze_cycles', 'indicator_features')}
        metrics = table(args.results/'metrics.csv')
        monthly = table(args.results/'monthly_results.csv')
        directions = table(args.results/'direction_results.csv')
        sensitivity = table(args.results/'sensitivity.csv')
        frequencies = table(args.results/'frequency_report.csv')
        comparisons = table(args.results/'m5_m30_comparison.csv')
        for symbol, idx in data.items():
            checked['indicator_fields'] += compare(reconstructed[symbol, 'FEATURES', 0], [r for r in published['indicator_features'] if r['instrument'] == symbol], f'{symbol} features')
            cov, days = calendar(idx)
            for architecture in ('SQUEEZE_M5', 'SQUEEZE_M30_M5'):
                for delay in (10, 15):
                    key = symbol, architecture, delay
                    results = reconstructed[key]
                    def group(rows):
                        return [r for r in rows if (r['instrument'], r['architecture'], r['scenario']) == (symbol, architecture, f'T{delay}')]
                    for name, rows in results.items():
                        checked[name+'_fields'] += compare(rows, group(published[name]), str(key)+' '+name)
                    ledger = results['trade_ledger']
                    totals = aggregate(ledger)
                    totals.update(raw_squeeze_episodes=len(results['squeeze_cycles']), confirmed_squeeze_episodes=sum(e['bars'] >= 3 for e in results['squeeze_cycles']),
                                  confirmed_signals=len(results['signals']), model_orders=sum(e['kind'] == 'ENTRY_ORDER' for e in results['execution_events']),
                                  rejected_signals=sum(s['status'] == 'FILTERED' for s in results['signals']),
                                  nonfills=sum(s['status'] in ('NONFILL', 'NO_BAR_NO_MODEL_FILL') for s in results['signals']),
                                  reached_1R=sum(r['mfe_R'] >= 1 for r in ledger), reached_2R=sum(r['mfe_R'] >= 2 for r in ledger), reached_3R=sum(r['mfe_R'] >= 3 for r in ledger),
                                  takes=sum(r['exit_reason'] == 'TAKE' for r in ledger), flat_reserve_breaches=sum(r['flat_target_breach'] for r in ledger),
                                  realized_net_3R=sum(r['status'] == 'CLOSED' and r['net_R'] >= 3 for r in ledger),
                                  early_potential_winners=sum(r['status'] == 'CLOSED' and r['exit_reason'] != 'TAKE' and r['mfe_R'] >= 1 for r in ledger),
                                  long_entries=sum(r['direction'] == 'LONG' for r in ledger), short_entries=sum(r['direction'] == 'SHORT' for r in ledger),
                                  eligible_calendar_days=len(days), observed_days=sum(o > 0 for e, o in days.values()), trades_per_expected_day=D(len(ledger))/len(days),
                                  trades_per_observed_day=D(len(ledger))/sum(o > 0 for e, o in days.values()))
                    reasons = Counter(s['reason'] for s in results['signals'] if s['status'] != 'MODELLED')
                    exits = Counter(r['exit_reason'] for r in ledger)
                    totals.update(rejection_reasons=json.dumps(dict(sorted(reasons.items())), sort_keys=True),
                                  exit_counts=json.dumps(dict(sorted(exits.items())), sort_keys=True),
                                  planned_min_net_RR=min((r['planned_net_RR'] for r in ledger), default=None),
                                  mean_initial_risk=sum((r['initial_risk'] for r in ledger), ZERO)/len(ledger) if ledger else None,
                                  mean_target_atr=sum((r['target_atr'] for r in ledger), ZERO)/len(ledger) if ledger else None)
                    checked['metrics_fields'] += compare([totals], group(metrics), str(key)+' metrics')
                    assert all(r['full_net'] == r['full_PF'] == r['full_DD'] == '' for r in group(metrics)), 'No fabricated full annual metrics'
                    for direction in ('LONG', 'SHORT'):
                        subset = [r for r in ledger if r['direction'] == direction]
                        checked['direction_fields'] += compare([aggregate(subset)], [r for r in group(directions) if r['direction'] == direction], str(key)+direction)
                    for period, c in cov.items():
                        subset = [r for r in ledger if r['entry_at'].strftime('%Y-%m') == period]
                        wanted = aggregate(subset) | c
                        if c['coverage_status'] == 'NO_COVERAGE':
                            wanted = {k: v if k in ('entries', 'closed', 'unknown') or k in c else None for k, v in wanted.items()}
                        records = [r for r in group(monthly) if r['period'] == period]
                        long = aggregate([r for r in subset if r['direction'] == 'LONG'])
                        short = aggregate([r for r in subset if r['direction'] == 'SHORT'])
                        sign = 'NO_COVERAGE' if c['coverage_status'] == 'NO_COVERAGE' else 'UNKNOWN' if wanted['unknown'] else 'NO_TRADES' if not subset else 'POSITIVE' if wanted['closed_net'] > 0 else 'NEGATIVE' if wanted['closed_net'] < 0 else 'ZERO_NET'
                        wanted.update(long_entries=long['entries'], short_entries=short['entries'],
                                      long_closed_net=long['closed_net'] if c['coverage_status'] != 'NO_COVERAGE' else None,
                                      short_closed_net=short['closed_net'] if c['coverage_status'] != 'NO_COVERAGE' else None,
                                      month_status=sign, sign_scope='CONFIRMED_CALENDAR' if c['coverage_status'] == 'COVERED' and not wanted['unknown'] else 'CLOSED_SUBSET_ONLY')
                        checked['monthly_fields'] += compare([wanted], records, str(key)+' '+period)
                        if c['coverage_status'] != 'COVERED' or wanted['unknown']:
                            assert records[0]['full_net'] == records[0]['full_PF'] == records[0]['full_DD'] == ''
                    for multiplier in (1, 2):
                        sr = [r for r in group(sensitivity) if r['cost'] == f'C{multiplier}']
                        checked['sensitivity_fields'] += compare([aggregate(ledger, multiplier)], sr, str(key)+f'C{multiplier}')
                        assert sr[0]['full_net'] == sr[0]['full_PF'] == sr[0]['full_DD'] == ''
                    counts = Counter(r['entry_at'].date() for r in ledger)
                    week_entries, week_days = Counter(), Counter()
                    for day, (expected, observed) in days.items():
                        checked['frequency_fields'] += compare([dict(entries=counts[day], expected_slots=expected, observed_slots=observed, no_trade=counts[day] == 0, data_absent=observed == 0)], [r for r in group(frequencies) if r['frequency'] == 'DAY' and r['period'] == str(day)], str(key)+' frequency')
                        week = f'{day.isocalendar().year}-W{day.isocalendar().week:02d}'
                        week_entries[week] += counts[day]
                        week_days[week] += 1
                    for week in week_days:
                        checked['weekly_frequency_fields'] += compare([dict(entries=week_entries[week], eligible_days=week_days[week])], [r for r in group(frequencies) if r['frequency'] == 'WEEK' and r['period'] == week], str(key)+week)
                    for period, c in cov.items():
                        count = sum(r['entry_at'].strftime('%Y-%m') == period for r in ledger)
                        checked['monthly_frequency_fields'] += compare([dict(entries=count if c['coverage_status'] != 'NO_COVERAGE' else None, coverage_status=c['coverage_status'])], [r for r in group(frequencies) if r['frequency'] == 'MONTH' and r['period'] == period], str(key)+period)
                    counts_summary = dict(observed_no_trade_days=sum(observed > 0 and counts[day] == 0 for day, (expected, observed) in days.items()),
                                          trades_per_available_month=D(len(ledger))/sum(c['coverage_status'] != 'NO_COVERAGE' for c in cov.values()))
                    checked['frequency_summary_fields'] += compare([counts_summary], group(metrics), str(key)+' frequency summary')
                    summaries.append(dict(instrument=symbol, architecture=architecture, scenario=f'T{delay}') | totals)
            for delay in (10, 15):
                a, b = (reconstructed[symbol, architecture, delay]['trade_ledger'] for architecture in ('SQUEEZE_M5', 'SQUEEZE_M30_M5'))
                ai, bi = {r['signal_id'] for r in a}, {r['signal_id'] for r in b}
                wanted = dict(m5_entries=len(ai), m30_entries=len(bi), retained_entries=len(ai & bi), removed_entries=len(ai-bi), freed_entries=len(bi-ai), m5_unknown=sum(r['status'] == 'UNKNOWN' for r in a), m30_unknown=sum(r['status'] == 'UNKNOWN' for r in b))
                checked['comparison_fields'] += compare([wanted], [r for r in comparisons if r['instrument'] == symbol and r['scenario'] == f'T{delay}'], symbol+' comparison')
        artifact = dict(status='INDEPENDENT_TRADING_LOGIC_PASS', algorithm='Raw segment weighted-formula features + independent compression scan + independent execution state machine; no production imports',
                        numeric_tolerance='1e-24 * max(1,abs(expected)); production precision34, oracle50', runs=16, checked_fields=dict(checked), provenance=provenance,
                        full_annual_metrics='NULL: incomplete history/gaps/UNKNOWN', oracle_sha256=sha(Path(__file__).read_bytes()), summaries=summaries)
        (args.output/'independent_audit.json').write_text(json.dumps(artifact, default=str, sort_keys=True, indent=2)+'\n')
        # Large independent reconstruction retained in work only for reproducible traces.
        (args.output/'reconstructed.json.gz').write_bytes(gzip.compress(json.dumps({str(k): v for k, v in reconstructed.items()}, default=str, sort_keys=True).encode(), mtime=0))
    print('Independent audit PASS; checked fields:', sum(checked.values()))


if __name__ == '__main__':
    main()
