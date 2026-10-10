#!/usr/bin/env python3
"""Independent raw-source oracle for the preregistered M15/H1 pair.

No Lab replay, calendar, indicator, execution, or metric module is imported.
The feasibility command does not calculate a trade payoff. Published outputs
are opened only after every independent replay has finished.
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
CONFIG = LAB / 'config/stage2_squeeze_m15_v1.json'
FIVE, FIFTEEN = TD(minutes=5), TD(minutes=15)
ZERO = D(0)
HOLIDAYS = {(1, 1), (1, 2), (1, 7), (2, 23), (3, 8), (5, 1), (5, 9), (6, 12), (11, 4)}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def intervals(day):
    if day.weekday() >= 5 or (day.month, day.day) in HOLIDAYS:
        return []
    am = DT.combine(day, DT.min.time()) + TD(hours=10)
    pm = am + TD(hours=4, minutes=15 if date(2023, 3, 13) <= day <= date(2023, 3, 20) else 5)
    return [(am, am + TD(hours=4)), (pm, am + TD(hours=8, minutes=50))]


def window(t, width=FIFTEEN):
    return next((w for w in intervals(t.date()) if w[0] <= t and t + width <= w[1]), None)


def floor_clock(t, minutes):
    elapsed = t.hour * 60 + t.minute
    return t.replace(hour=0, minute=0, second=0, microsecond=0) + TD(minutes=elapsed // minutes * minutes)


def future(t):
    return floor_clock(t, 15) + FIFTEEN


def parent_slots(day, width=15):
    for a, b in intervals(day):
        t = floor_clock(a, width)
        if t < a:
            t += TD(minutes=width)
        while t + TD(minutes=width) <= b:
            yield t
            t += TD(minutes=width)


def step(symbol, at):
    if symbol == 'CNYRUBF':
        return D('.01') if at < DT(2023, 9, 27, 19) else D('.001')
    return {'USDRUBF': D('.01'), 'GLDRUBF': D('.1'), 'IMOEXF': D('.5')}[symbol]


def quant(value, delta, up):
    return (value / delta).to_integral_value(rounding=ROUND_CEILING if up else ROUND_FLOOR) * delta


def load_source(root):
    frozen = CONFIG.read_bytes()
    assert sha(frozen) == CONFIG.with_suffix('.sha256').read_text().split()[0], 'Frozen configuration changed'
    spec = json.loads(frozen)
    assert spec['parameters']['period'] == 7 and spec['parameters']['minimum_squeeze_bars'] == 2
    def git(*args):
        return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()
    assert git('rev-parse', 'HEAD') == spec['source_ref']
    assert not git('status', '--porcelain'), 'Source is not read-only clean'
    data, provenance = {}, {}
    for symbol, s in sorted(spec['inputs'].items()):
        assert git('ls-files', '--stage', '--', s['path']).split()[1] == s['blob']
        path = root / s['path']
        before = path.stat()
        with path.open('rb', buffering=0) as source:
            raw = source.read(s['prefix_bytes'])
        assert len(raw) == s['prefix_bytes'] and sha(raw) == s['prefix_sha256'] and raw.endswith(b'\n')
        lines = raw.decode('utf-8-sig').splitlines()
        assert lines[0] == 'Ticker;Datetime;Open;High;Low;Close;Volume'
        assert len(lines) == s['rows_2023'] + 1
        values = {}
        for line in lines[1:]:
            p = line.split(';')
            t = DT.fromisoformat(p[1])
            assert t.year == 2023 and p[0] == symbol and t not in values
            assert t.minute % 5 == t.second == t.microsecond == 0
            o, h, l, c, v = map(D, p[2:])
            assert l <= min(o, c) <= max(o, c) <= h and v >= 0
            assert all(x % step(symbol, t) == 0 for x in (o, h, l, c))
            values[t] = (o, h, l, c, v)
        after = path.stat()
        assert (before.st_size, before.st_mtime_ns, before.st_ino) == (after.st_size, after.st_mtime_ns, after.st_ino)
        assert list(values) == sorted(values)
        data[symbol] = values
        provenance[symbol] = dict(rows=len(values), bytes_read=len(raw), prefix_sha256=sha(raw),
                                  protected_year_bytes_read=0, first=min(values), last=max(values))
    return spec, data, provenance


def compose(idx, width):
    """Only exact existing children, positive-volume usability is separate."""
    out = {}
    day = date(2023, 1, 1)
    while day.year == 2023:
        for t in parent_slots(day, width):
            times = [t + i * FIVE for i in range(width // 5)]
            if any(x not in idx for x in times):
                continue
            kids = [idx[x] for x in times]
            b = (kids[0][0], max(x[1] for x in kids), min(x[2] for x in kids), kids[-1][3], sum((x[4] for x in kids), ZERO))
            out[t] = dict(at=t, open=b[0], high=b[1], low=b[2], close=b[3], volume=b[4],
                          child_first=times[0], child_last=times[-1], children=width // 5,
                          window_start=window(t, TD(minutes=width))[0], window_end=window(t, TD(minutes=width))[1],
                          usable=all(x[4] > 0 for x in kids), bar=b)
        day += TD(days=1)
    return out


def batch_indicators(parents):
    """Batch weighted history, independent from streaming EMA/ATR recursion."""
    out, segment, previous_window = {}, [], None
    for t, record in sorted(parents.items()):
        w = window(t)
        if not record['usable']:
            segment, previous_window = [], None
            continue
        if w != previous_window or (segment and segment[-1][0] + FIFTEEN != t):
            segment = []
        segment.append((t, record['bar']))
        previous_window = w
        n = len(segment)
        if n < 7:
            continue
        closes = [b[3] for _, b in segment]
        trs = [b[1] - b[2] if i == 0 else max(b[1] - b[2], abs(b[1] - segment[i - 1][1][3]), abs(b[2] - segment[i - 1][1][3]))
               for i, (_, b) in enumerate(segment)]
        mean = sum(closes[-7:], ZERO) / 7
        variance = sum((x * x for x in closes[-7:]), ZERO) / 7 - mean * mean
        sigma = max(variance, ZERO).sqrt()
        seed = sum(closes[:7], ZERO) / 7
        ema = (D(3) / 4) ** (n - 7) * seed + sum((D(1) / 4 * (D(3) / 4) ** (n - 1 - i) * closes[i] for i in range(7, n)), ZERO)
        atr_seed = sum(trs[:7], ZERO) / 7
        atr = (D(6) / 7) ** (n - 7) * atr_seed + sum((D(1) / 7 * (D(6) / 7) ** (n - 1 - i) * trs[i] for i in range(7, n)), ZERO)
        ub, lb, uk, lk = mean + 2 * sigma, mean - 2 * sigma, ema + D('1.5') * atr, ema - D('1.5') * atr
        out[t] = dict(at=t, warmup=n, sma7=mean, variance7=variance, std7=sigma, ema7=ema, tr=trs[-1],
                      atr7=atr, bb_upper=ub, bb_lower=lb, kc_upper=uk, kc_lower=lk, squeeze=ub < uk and lb > lk)
    return out


def cycles_and_signals(parents, symbol, frames, scenario):
    episodes, signals, active = [], {}, None
    delay = TD(minutes=10 + scenario)
    previous_window = None
    def discard(now, reason):
        nonlocal active
        if active and not active['terminal_reason']:
            active.update(terminal_at=now, terminal_reason=reason if active['bars'] >= 2 else 'UNCONFIRMED_LT2')
        active = None
    day = date(2023, 1, 1)
    while day.year == 2023:
        # The first wall-aligned slot that cannot fit wholly in a window is
        # still a clock observation. It terminates the episode rather than
        # postponing its reset annotation to the next usable session/day.
        delivered_clock = sorted(set(parent_slots(day)) | {floor_clock(b, 15) for _, b in intervals(day)})
        for t in delivered_clock:
            now, w = t + delay, window(t)
            b = parents.get(t)
            if b and not b['usable']:
                b = None
            if w != previous_window or b is None:
                discard(now, 'NO_EXPANSION_SESSION' if w != previous_window else 'NO_EXPANSION_GAP')
            previous_window = w
            f = frames.get(t) if b else None
            if not f:
                continue
            bar = b['bar']
            if f['squeeze']:
                if active and active['released_at'] is not None:
                    discard(now, 'NO_EXPANSION_NEXT_SQUEEZE')
                if active is None:
                    active = dict(cycle_id=f'SQ_{symbol}_{len(episodes) + 1:06d}', start=t, end=t, bars=0,
                                  range_high=bar[1], range_low=bar[2], confirmed_at=None, released_at=None,
                                  terminal_at=None, terminal_reason='', signal_at=None, direction=None)
                    episodes.append(active)
                active.update(end=t, bars=active['bars'] + 1, range_high=max(active['range_high'], bar[1]), range_low=min(active['range_low'], bar[2]))
                if active['bars'] == 2:
                    active['confirmed_at'] = now
            elif active and not active['terminal_reason']:
                if active['released_at'] is None:
                    active['released_at'] = now
                if active['bars'] < 2:
                    discard(now, 'UNCONFIRMED_LT2')
                else:
                    d = 1 if bar[3] > active['range_high'] else -1 if bar[3] < active['range_low'] else 0
                    if d:
                        active.update(terminal_at=now, terminal_reason='SIGNAL', signal_at=t, direction='LONG' if d > 0 else 'SHORT')
                        signals[t] = dict(signal_id=active['cycle_id'], direction_sign=d, direction=active['direction'],
                                          range_start=active['start'], range_end=active['end'], squeeze_bars=active['bars'],
                                          range_high=active['range_high'], range_low=active['range_low']) | f
        day += TD(days=1)
    discard(DT(2024, 1, 1), 'NO_EXPANSION_YEAR_END')
    return episodes, signals


def h1_context(raw, h1, now, w, scenario, direction):
    delivered_start = floor_clock(now - TD(minutes=55 + scenario), 60)
    starts = (delivered_start - TD(hours=1), delivered_start)
    rec = dict(mtf_first=None, mtf_last=None, mtf_available_at=None, mtf_direction=None, mtf_reason='MTF_TWO_PARENTS_NOT_READY')
    if starts[0] < w[0] or starts[1] + TD(hours=1) > w[1]:
        return rec
    parents = [h1.get(t) for t in starts]
    if any(p is None or not p['usable'] for p in parents):
        rec['mtf_reason'] = 'MTF_INCOMPLETE_CHILD_BUCKET'
        return rec
    latest_child = floor_clock(now - TD(minutes=scenario), 5)
    t = starts[0]
    while t <= latest_child:
        if t not in raw or raw[t][4] <= 0 or window(t, FIVE) != w:
            rec['mtf_reason'] = 'MTF_CONTINUITY_GAP'
            return rec
        t += FIVE
    a, b = [p['bar'] for p in parents]
    trend = 1 if a[3] > a[0] and b[3] > b[0] and b[3] > a[3] else -1 if a[3] < a[0] and b[3] < b[0] and b[3] < a[3] else 0
    rec.update(mtf_first=starts[0], mtf_last=starts[1], mtf_available_at=starts[1] + TD(minutes=55 + scenario),
               mtf_direction=trend, mtf_reason='MTF_SUSTAINED_ADVERSE_DIRECTION' if trend == -direction else None)
    assert rec['mtf_available_at'] <= now
    return rec


def feasibility(data, provenance):
    rows, total_signals, total_h1_ready = [], 0, 0
    for symbol, raw in data.items():
        parents, h1 = compose(raw, 15), compose(raw, 60)
        features = batch_indicators(parents)
        max_run, run, previous, wprev = 0, 0, None, None
        for t, p in parents.items():
            w = window(t)
            run = run + 1 if p['usable'] and previous is not None and t == previous + FIFTEEN and w == wprev else int(p['usable'])
            max_run = max(max_run, run)
            previous, wprev = t, w
        scenarios = {}
        for scenario in (10, 15):
            cycles, signals = cycles_and_signals(parents, symbol, features, scenario)
            ready, causal, safe = 0, 0, 0
            for t, s in signals.items():
                now = t + TD(minutes=10 + scenario)
                target = future(now)
                w = window(t)
                causal += target > now and target == t + TD(minutes=30) and s['range_end'] < t
                safe += target + TD(minutes=25) <= floor_clock(w[1] - TD(minutes=35), 15) - FIVE
                ready += h1_context(raw, h1, now, w, scenario, s['direction_sign'])['mtf_reason'] in (None, 'MTF_SUSTAINED_ADVERSE_DIRECTION')
            total_signals += len(signals)
            total_h1_ready += ready
            scenarios[f'T{scenario}'] = dict(raw_squeeze_episodes=len(cycles), confirmed_squeezes=sum(x['bars'] >= 2 for x in cycles),
                                               confirmed_breakouts=len(signals), causal_future_targets=causal,
                                               session_safe_targets=safe, ready_h1_pair_at_breakout=ready)
            assert causal == len(signals)
        rows.append(dict(instrument=symbol, complete_m15=len(parents), usable_m15=sum(p['usable'] for p in parents.values()),
                         complete_h1=len(h1), usable_h1=sum(p['usable'] for p in h1.values()),
                         ready_m15_features=len(features), longest_m15_segment=max_run, bb20_feasible=max_run >= 20,
                         bb7_feasible=max_run >= 7, scenarios=scenarios))
    passed = all(r['bb7_feasible'] and not r['bb20_feasible'] for r in rows) and total_signals > 0 and total_h1_ready > 0
    return dict(status='FEASIBILITY PASS' if passed else 'FEASIBILITY BLOCKED / INCONCLUSIVE',
                independent=True, pnl_calculated=False, config_sha256=sha(CONFIG.read_bytes()), oracle_sha256=sha(Path(__file__).read_bytes()),
                source_provenance=provenance, instruments=rows,
                causality='Exact aligned 3/12 M5 children; M15 T+20/25, H1 T+65/70; strict future M15 Open; session/gap resets; no stale H1 fallback',
                scope='Accepted restricted historical research windows, not a certified complete venue session calendar')


def admissible(symbol, s, price, at):
    delta, direction = step(symbol, at), s['direction_sign']
    risk = direction * (price - s['stop'])
    if price % delta:
        return None, 'OPEN_OFF_GRID'
    if direction * (price - s['edge']) <= 0:
        return None, 'BREAKOUT_NOT_PERSISTENT'
    if direction * (price - s['cap']) > 0:
        return None, 'EXTENSION_OVER_0_5_ATR'
    if risk < 4 * delta:
        return None, 'RISK_BELOW_FOUR_TICKS'
    take = quant(price + direction * (3 * risk + 2 * delta), delta, direction > 0)
    reward = direction * (take - price)
    if reward > 3 * s['atr7']:
        return None, 'TARGET_OVER_THREE_ATR'
    return dict(take=take, initial_risk=risk, planned_c1=2 * delta, planned_gross_reward=reward,
                planned_net_reward=reward - 2 * delta, planned_net_RR=(reward - 2 * delta) / risk,
                target_atr=reward / s['atr7']), None


def reconstruct(raw, symbol, architecture, scenario, parents, h1, features):
    """Independent event scan; no output or production code is an input."""
    cycles, opportunities = cycles_and_signals(parents, symbol, features, scenario)
    signals, ledger, events = [], [], []
    delay = TD(minutes=10 + scenario)
    position = pending = exit_request = None
    def event(at, kind, sid='', reason='', price=None, ack=None, flags=''):
        events.append(dict(at=at, kind=kind, signal_id=sid, reason=reason, price=price, confirmed_at=ack, flags=flags))
    def ask(now, why):
        nonlocal exit_request
        target = future(now)
        if exit_request is None or target < exit_request[0]:
            exit_request = target, why
            event(now, 'EXIT_ORDER', position['signal_id'], why)
    def uncertain(now, why):
        if position['status'] != 'UNKNOWN':
            position.update(status='UNKNOWN', gross=None, c1_exit=None, c1=None, net=None, net_R=None,
                            unknown_at=now, unknown_reason=why, excursion_status='LOWER_BOUND_BEFORE_UNKNOWN')
            event(now, 'UNKNOWN_PATH', position['signal_id'], why)
        ask(now, 'DATA_GAP_EMERGENCY')
    def finish(t, now, price, why, flags=''):
        nonlocal position, exit_request
        if position['status'] == 'UNKNOWN':
            position.update(exit_reason='UNKNOWN_PATH_REDUCE_ALL', model_flat_at=now, model_flat_slot=t,
                            known_reduce_cost=step(symbol, t))
            event(t, 'CONDITIONAL_FLAT', position['signal_id'], 'PAST_PAYOFF_REMAINS_UNKNOWN', ack=now)
        else:
            gross = position['direction_sign'] * (price - position['entry'])
            cost = position['c1_entry'] + step(symbol, t)
            position['mfe_R'] = max(position['mfe_R'], gross / position['initial_risk'])
            position['mae_R'] = max(position['mae_R'], -gross / position['initial_risk'])
            position.update(status='CLOSED', exit=price, exit_at=t, exit_ack=now, exit_reason=why,
                            gross=gross, c1_exit=step(symbol, t), c1=cost, net=gross - cost,
                            net_R=(gross - cost) / position['initial_risk'], gross_R=gross / position['initial_risk'],
                            hold_minutes=int((t - position['entry_at']).total_seconds() / 60), flags=flags,
                            model_flat_at=now, model_flat_slot=t)
            event(t, 'EXIT', position['signal_id'], why, price, now, flags)
        position = exit_request = None
    def protect(t, now, bar, initial=False):
        o, h, l, _, _ = bar
        direction, stop, take, delta = position['direction_sign'], position['stop'], position['take'], step(symbol, t)
        stopped = l <= stop if direction > 0 else h >= stop
        penetrated = h >= take + delta if direction > 0 else l <= take - delta
        touched = h >= take if direction > 0 else l <= take
        if stopped:
            flags = []
            if penetrated:
                flags.append('STOP_FIRST_BOTH_LEVELS')
            if initial:
                flags.append('ENTRY_BAR_STOP')
            if direction * (o - stop) <= 0:
                flags.append('ADVERSE_STOP_GAP')
            finish(t, now, min(o, stop) if direction > 0 else max(o, stop), 'STOP', '|'.join(flags))
        elif penetrated and not initial:
            position['mfe_R'] = max(position['mfe_R'], direction * (take - position['entry']) / position['initial_risk'])
            finish(t, now, take, 'TAKE')
        else:
            if not initial:
                position['mfe_R'] = max(position['mfe_R'], direction * ((h if direction > 0 else l) - position['entry']) / position['initial_risk'])
                position['mae_R'] = max(position['mae_R'], -direction * ((l if direction > 0 else h) - position['entry']) / position['initial_risk'])
            if penetrated and initial:
                event(t, 'TP_NONFILL', position['signal_id'], 'ENTRY_BAR_TP_FORBIDDEN', ack=now)
            elif touched:
                event(t, 'TP_NONFILL', position['signal_id'], 'TOUCH_WITHOUT_TICK_PENETRATION', ack=now)
    def new_position(s, t, now, bar=None, geometry=None):
        rec = {k: s[k] for k in ('signal_id', 'direction', 'direction_sign', 'signal_at', 'available_at',
                                'planned_execution_at', 'range_high', 'range_low', 'edge', 'atr7', 'stop', 'cap')}
        rec.update(geometry or dict(take=None, initial_risk=None, planned_c1=None, planned_gross_reward=None,
                                    planned_net_reward=None, planned_net_RR=None, target_atr=None))
        rec.update(status='OPEN' if bar else 'UNKNOWN', entry=bar[0] if bar else None, entry_at=t,
                   entry_ack=now if bar else None, c1_entry=step(symbol, t) if bar else None,
                   c1_exit=None, c1=None, gross=None, net=None, net_R=None, gross_R=None, exit=None,
                   exit_at=None, exit_ack=None, exit_reason='', hold_minutes=None, model_flat_at=None,
                   model_flat_slot=None, unknown_at=None if bar else now,
                   unknown_reason='' if bar else 'UNKNOWN_POSSIBLE_ENTRY_FILL', flat_target_breach=False,
                   flags='' if bar else 'UNKNOWN_ENTRY', mfe_R=ZERO, mae_R=ZERO,
                   excursion_status='CONSERVATIVE_KNOWN_PATH' if bar else 'NO_CONFIRMED_ENTRY_OR_PATH',
                   boundary=window(t)[1], known_reduce_cost=None)
        return rec
    day = date(2023, 1, 1)
    while day.year == 2023:
        if intervals(day):
            now = DT.combine(day, DT.min.time()) + TD(hours=10)
            end = now + TD(hours=9, minutes=20)
            while now <= end:
                t = now - delay
                w = window(t) if t.minute % 15 == 0 else None
                parent = parents.get(t) if w else None
                bar = parent['bar'] if parent and parent['usable'] else None
                # Resident protection and exact-target orders are acknowledged
                # before timer decisions and before the newly delivered signal.
                if bar:
                    if position and t >= position['entry_at']:
                        if exit_request and t >= exit_request[0]:
                            finish(t, now, bar[0], exit_request[1])
                        elif position['status'] != 'UNKNOWN' and t > position['entry_at']:
                            protect(t, now, bar)
                    if pending and t == pending['planned_execution_at']:
                        s, pending = pending, None
                        geometry, why = admissible(symbol, s, bar[0], t)
                        if why:
                            s.update(status='NONFILL', reason=why)
                            event(t, 'ENTRY_NONFILL', s['signal_id'], why, ack=now)
                        else:
                            s.update(status='MODELLED', reason='CONDITIONAL_EXACT_OPEN')
                            position = new_position(s, t, now, bar, geometry)
                            ledger.append(position)
                            event(t, 'ENTRY', position['signal_id'], 'CONDITIONAL_EXACT_OPEN', bar[0], now)
                            protect(t, now, bar, True)
                if w and pending and t >= pending['planned_execution_at']:
                    s, pending = pending, None
                    s.update(status='UNKNOWN_POSSIBLE_ENTRY_FILL', reason='EXACT_M15_PARENT_INCOMPLETE')
                    position = new_position(s, s['planned_execution_at'], now)
                    ledger.append(position)
                    event(now, 'UNKNOWN_ENTRY_ORDER', s['signal_id'], s['reason'])
                    ask(now, 'DATA_GAP_EMERGENCY')
                if w and bar is None and position and t >= position['entry_at']:
                    uncertain(now, 'MISSING_EXPOSED_M15_PATH')
                if position:
                    boundary = position['boundary']
                    if now >= boundary - TD(minutes=10) and not position['flat_target_breach']:
                        position['flat_target_breach'] = True
                        event(now, 'FLAT_TARGET_BREACH', position['signal_id'], 'NO_ACK_FLAT_AT_B_MINUS_10')
                    if now >= boundary:
                        uncertain(now, 'SESSION_BOUNDARY_EXPOSURE_UNRESOLVED')
                    flat = floor_clock(boundary - TD(minutes=35), 15)
                    if now >= flat - FIVE:
                        ask(now, 'SESSION_FLAT')
                    elif now >= position['entry_at'] + TD(minutes=115):
                        ask(now, 'MAX_HOLD')
                    if bar and t >= position['entry_at'] and exit_request is None and position['status'] != 'UNKNOWN' and position['range_low'] <= bar[3] <= position['range_high']:
                        ask(now, 'FAILED_BREAKOUT')
                if bar and t in opportunities:
                    s = opportunities[t].copy()
                    direction, delta = s['direction_sign'], step(symbol, now)
                    edge = s['range_high'] if direction > 0 else s['range_low']
                    s.update(signal_at=t, signal_close=bar[3], available_at=now, ready_at=now,
                             planned_execution_at=future(now), edge=edge,
                             stop=quant(edge - direction * s['atr7'] / 4, delta, direction > 0),
                             cap=quant(edge + direction * s['atr7'] / 2, delta, direction < 0),
                             status='SUBMITTED', reason='', mtf_first=None, mtf_last=None, mtf_available_at=None,
                             mtf_direction=None, mtf_reason=None)
                    if architecture == 'SQUEEZE_H1_M15':
                        s.update(h1_context(raw, h1, now, w, scenario, direction))
                    _, why = admissible(symbol, s, bar[3], now)
                    flat = floor_clock(w[1] - TD(minutes=35), 15)
                    if position or pending:
                        why = 'POSITION_OR_ORDER_BUSY'
                    elif window(s['planned_execution_at']) != w or s['planned_execution_at'] + TD(minutes=25) > flat - FIVE:
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
    if position:
        uncertain(DT(2024, 1, 1), 'UNRESOLVED_AT_DEVELOPMENT_END')
    return dict(signals=signals, trade_ledger=ledger, execution_events=events, squeeze_cycles=cycles)


def aggregate(rows, cost=1):
    closed = [r for r in rows if r['status'] == 'CLOSED']
    known = [r for r in rows if r['entry'] is not None]
    nets = [r['gross'] - cost * r['c1'] for r in closed]
    n = len(closed)
    positive = sum((x for x in nets if x > 0), ZERO)
    negative = -sum((x for x in nets if x < 0), ZERO)
    wins, losses = sum(x > 0 for x in nets), sum(x < 0 for x in nets)
    avg_win, avg_loss = positive / wins if wins else None, negative / losses if losses else None
    gw = [r['gross'] for r in closed if r['gross'] > 0]
    gl = [-r['gross'] for r in closed if r['gross'] < 0]
    cumulative = high = dd = ZERO
    high_at, recovery = min((r['entry_at'] for r in closed), default=None), 0
    for r in sorted(closed, key=lambda row: (row['exit_ack'], row['signal_id'])):
        cumulative += r['gross'] - cost * r['c1']
        if cumulative >= high:
            high, high_at = cumulative, r['exit_ack']
        elif high_at:
            recovery = max(recovery, int((r['exit_ack'] - high_at).total_seconds() / 60))
        dd = max(dd, high - cumulative)
    top = sorted((x for x in nets if x > 0), reverse=True)
    total_r = sum((net / r['initial_risk'] for net, r in zip(nets, closed)), ZERO)
    return dict(entries=len(known), closed=n, unknown=sum(r['status'] == 'UNKNOWN' for r in rows),
                unknown_entry_orders=sum(r['entry'] is None for r in rows),
                closed_gross=sum((r['gross'] for r in closed), ZERO), closed_cost=sum((cost * r['c1'] for r in closed), ZERO),
                closed_net=sum(nets, ZERO), closed_net_PF=positive / negative if negative else None,
                PF_status='DEFINED' if negative else 'NO_LOSSES' if wins else 'NO_TRADES',
                closed_expectancy=sum(nets, ZERO) / n if n else None, closed_win_rate=D(wins) / n if n else None,
                average_net_win=avg_win, average_net_loss=avg_loss,
                realized_net_win_loss_RR=avg_win / avg_loss if avg_win is not None and avg_loss else None,
                realized_gross_win_loss_RR=(sum(gw, ZERO) / len(gw)) / (sum(gl, ZERO) / len(gl)) if gw and gl else None,
                closed_net_R=total_r, mean_net_R=total_r / n if n else None, closed_realized_DD=dd if n else None,
                closed_unrecovered_minutes=recovery, largest_winner_share=top[0] / positive if top else None,
                top3_winner_share=sum(top[:3], ZERO) / positive if top else None,
                top5_winner_share=sum(top[:5], ZERO) / positive if top else None,
                closed_net_without_top1=sum(nets, ZERO) - (top[0] if top else ZERO),
                known_entry_cost_unknown=sum((cost * r['c1_entry'] for r in known if r['status'] != 'CLOSED'), ZERO))


def calendar(raw, parents):
    first = min(raw)
    coverage, days = {}, {}
    for month in range(1, 13):
        day = date(2023, month, 1)
        slots, m15 = set(), set()
        while day.year == 2023 and day.month == month:
            for a, b in intervals(day):
                expected = {a + i * FIVE for i in range(int((b - a) / FIVE))}
                slots |= expected
                if day >= first.date():
                    e, o = days.get(day, (0, 0))
                    days[day] = e + len(expected), o + sum(t in raw and raw[t][4] > 0 for t in expected)
            m15.update(parent_slots(day))
            day += TD(days=1)
        observed = {t for t in slots if t in raw and raw[t][4] > 0}
        missing = {t for t in slots - observed if t >= first}
        status = 'NO_COVERAGE' if month < first.month else 'PARTIAL_LAUNCH' if any(t < first for t in slots) else 'PARTIAL_DATA' if missing else 'COVERED'
        coverage[f'2023-{month:02d}'] = dict(coverage_status=status, expected_slots=len(slots), observed_slots=len(observed),
                                               missing_since_inception=len(missing), pre_inception_slots=sum(t < first for t in slots),
                                               expected_m15_slots=len(m15), observed_m15_slots=sum(t in parents and parents[t]['usable'] for t in m15),
                                               missing_m15_since_inception=sum(t >= first and (t not in parents or not parents[t]['usable']) for t in m15),
                                               pre_inception_m15_slots=sum(t < first for t in m15))
    return coverage, days


def read_table(path):
    raw = gzip.decompress(path.read_bytes()) if path.suffix == '.gz' else path.read_bytes()
    return list(csv.DictReader(raw.decode().splitlines()))


def equal(expected, actual):
    if expected is None:
        return actual == ''
    if isinstance(expected, D):
        return actual != '' and abs(expected - D(actual)) <= D('1e-24') * max(D(1), abs(expected))
    return str(expected) == actual


def compare(expected, actual, label, discrepancies):
    if len(expected) != len(actual):
        discrepancies.append(dict(table=label, field='row_count', expected=len(expected), actual=len(actual)))
    checked = 0
    for i, (wanted, got) in enumerate(zip(expected, actual)):
        for key, value in wanted.items():
            # This optional field exists only when a reduce-all was required.
            if key == 'known_reduce_cost' and value is None and key not in got:
                continue
            checked += 1
            if key not in got or not equal(value, got[key]):
                discrepancies.append(dict(table=label, row=i, field=key, expected=str(value), actual=got.get(key)))
    return checked


def summaries_for(result, raw, parents, cost=1):
    ledger = result['trade_ledger']
    known = [r for r in ledger if r['entry'] is not None]
    cov, days = calendar(raw, parents)
    totals = aggregate(ledger, cost)
    totals.update(raw_squeeze_episodes=len(result['squeeze_cycles']), confirmed_squeeze_episodes=sum(e['bars'] >= 2 for e in result['squeeze_cycles']),
                  confirmed_signals=len(result['signals']), model_orders=sum(e['kind'] == 'ENTRY_ORDER' for e in result['execution_events']),
                  rejected_signals=sum(s['status'] == 'FILTERED' for s in result['signals']), nonfills=sum(s['status'] == 'NONFILL' for s in result['signals']),
                  reached_1R=sum(r['mfe_R'] >= 1 for r in known), reached_2R=sum(r['mfe_R'] >= 2 for r in known), reached_3R=sum(r['mfe_R'] >= 3 for r in known),
                  takes=sum(r['exit_reason'] == 'TAKE' for r in ledger), flat_reserve_breaches=sum(r['flat_target_breach'] for r in ledger),
                  realized_net_3R=sum(r['status'] == 'CLOSED' and (r['gross'] - cost * r['c1']) / r['initial_risk'] >= 3 for r in ledger),
                  early_potential_winners=sum(r['status'] == 'CLOSED' and r['exit_reason'] != 'TAKE' and r['mfe_R'] >= 1 for r in ledger),
                  long_entries=sum(r['direction'] == 'LONG' for r in known), short_entries=sum(r['direction'] == 'SHORT' for r in known),
                  eligible_calendar_days=len(days), observed_days=sum(o > 0 for _, o in days.values()),
                  trades_per_expected_day=D(len(known)) / len(days), trades_per_observed_day=D(len(known)) / sum(o > 0 for _, o in days.values()))
    totals.update(rejection_reasons=json.dumps(dict(sorted(Counter(s['reason'] for s in result['signals'] if s['status'] != 'MODELLED').items())), sort_keys=True),
                  exit_counts=json.dumps(dict(sorted(Counter(r['exit_reason'] for r in ledger).items())), sort_keys=True),
                  planned_min_net_RR=min((r['planned_net_RR'] for r in known), default=None),
                  mean_initial_risk=sum((r['initial_risk'] for r in known), ZERO) / len(known) if known else None,
                  mean_target_atr=sum((r['target_atr'] for r in known), ZERO) / len(known) if known else None)
    counts = Counter(r['entry_at'].date() for r in known)
    totals.update(observed_no_trade_days=sum(observed > 0 and counts[day] == 0 for day, (_, observed) in days.items()),
                  trades_per_available_month=D(len(known)) / sum(c['coverage_status'] != 'NO_COVERAGE' for c in cov.values()))
    month_rows = []
    streak = longest = 0
    for period, c in cov.items():
        rows = [r for r in ledger if r['entry_at'].strftime('%Y-%m') == period]
        q = aggregate(rows, cost)
        sign = 'NO_COVERAGE' if c['coverage_status'] == 'NO_COVERAGE' else 'UNKNOWN' if q['unknown'] else 'NO_TRADES' if not rows else 'POSITIVE' if q['closed_net'] > 0 else 'NEGATIVE' if q['closed_net'] < 0 else 'ZERO_NET'
        confirmed = c['coverage_status'] == 'COVERED' and q['unknown'] == 0
        month_rows.append(dict(period=period, sign=sign, confirmed=confirmed, net=q['closed_net'], closed=q['closed'], unknown=q['unknown']))
        streak = streak + 1 if sign == 'NEGATIVE' else 0
        longest = max(longest, streak)
    nonempty = [x for x in month_rows if x['closed']]
    totals.update(positive_closed_months=sum(x['sign'] != 'NO_COVERAGE' and x['net'] > 0 for x in month_rows),
                  negative_closed_months=sum(x['sign'] != 'NO_COVERAGE' and x['net'] < 0 for x in month_rows),
                  zero_trade_months=sum(x['sign'] == 'NO_TRADES' for x in month_rows),
                  no_coverage_months=sum(x['sign'] == 'NO_COVERAGE' for x in month_rows),
                  unknown_months=sum(x['unknown'] > 0 for x in month_rows),
                  confirmed_positive_months=sum(x['sign'] == 'POSITIVE' and x['confirmed'] for x in month_rows),
                  confirmed_negative_months=sum(x['sign'] == 'NEGATIVE' and x['confirmed'] for x in month_rows),
                  best_closed_month=max(nonempty, key=lambda x: x['net'])['period'] if nonempty else None,
                  worst_closed_month=min(nonempty, key=lambda x: x['net'])['period'] if nonempty else None,
                  longest_known_negative_month_streak=longest,
                  zero_net_trade_months=sum(x['sign'] == 'ZERO_NET' for x in month_rows),
                  confirmed_zero_trade_months=sum(x['sign'] == 'NO_TRADES' and x['confirmed'] for x in month_rows),
                  partially_covered_months=sum(c['coverage_status'] in ('PARTIAL_DATA', 'PARTIAL_LAUNCH') for c in cov.values()),
                  largest_positive_month_share=max((x['net'] for x in month_rows if x['net'] > 0), default=ZERO) /
                      sum((x['net'] for x in month_rows if x['net'] > 0), ZERO) if any(x['net'] > 0 for x in month_rows) else None)
    return totals, cov, days


def parent_export(raw, parents, width):
    rows = []
    for day in sorted({t.date() for t in raw}):
        for t in parent_slots(day, width):
            p, w = parents.get(t), window(t, TD(minutes=width))
            usable = p is not None and p['usable']
            rows.append(dict(at=t, status='COMPLETE' if usable else 'INCOMPLETE_OR_NONPOSITIVE_CHILD',
                             open=p['open'] if usable else None, high=p['high'] if usable else None,
                             low=p['low'] if usable else None, close=p['close'] if usable else None,
                             volume=p['volume'] if usable else None, child_first=t,
                             child_last=t + TD(minutes=width - 5), available_T10=t + TD(minutes=width + 5),
                             available_T15=t + TD(minutes=width + 10), window_start=w[0], window_end=w[1]))
    return rows


def audit(data, provenance, results, output):
    assert (results / 'independent_feasibility.json').exists(), 'Independent feasibility must predate P&L'
    gate = json.loads((results / 'independent_feasibility.json').read_text())
    assert gate['status'] == 'FEASIBILITY PASS' and gate['pnl_calculated'] is False
    assert gate['config_sha256'] == sha(CONFIG.read_bytes())
    reconstructed, parents_by_symbol, checked, discrepancies, summaries = {}, {}, Counter(), [], []
    for symbol, raw in data.items():
        parents, h1 = compose(raw, 15), compose(raw, 60)
        features = batch_indicators(parents)
        parents_by_symbol[symbol] = parents
        reconstructed[symbol, 'FEATURES', 0] = list(features.values())
        reconstructed[symbol, 'M15', 0] = [{k: v for k, v in p.items() if k != 'bar'} for p in parents.values()]
        reconstructed[symbol, 'H1', 0] = [{k: v for k, v in p.items() if k != 'bar'} for p in h1.values()]
        for architecture in ('SQUEEZE_M15', 'SQUEEZE_H1_M15'):
            for scenario in (10, 15):
                reconstructed[symbol, architecture, scenario] = reconstruct(raw, symbol, architecture, scenario, parents, h1, features)
    # The independent reconstruction is complete before opening published data.
    output.mkdir(parents=True, exist_ok=True)
    replay_bytes = json.dumps({str(k): v for k, v in reconstructed.items()}, default=str, sort_keys=True).encode()
    (output / 'reconstructed.json.gz').write_bytes(gzip.compress(replay_bytes, mtime=0))
    published = {name: read_table(results / f'{name}.csv.gz') for name in
                 ('signals', 'trade_ledger', 'execution_events', 'squeeze_cycles', 'indicator_features')}
    metrics = read_table(results / 'metrics.csv')
    monthly = read_table(results / 'monthly_results.csv')
    directions = read_table(results / 'direction_results.csv')
    sensitivity = read_table(results / 'sensitivity.csv')
    frequencies = read_table(results / 'frequency_report.csv')
    parent_rows = read_table(results / 'derived_parents.csv.gz')
    funnel = read_table(results / 'filter_funnel.csv')
    funnel_stages = read_table(results / 'funnel_stages.csv')
    m15_coverage_rows = read_table(results / 'coverage_m15.csv')
    comparison_rows = read_table(results / 'm15_h1_comparison.csv')
    coverage_by_symbol = {}
    for symbol, raw in data.items():
        for width in (15, 60):
            checked['parent_fields'] += compare(parent_export(raw, compose(raw, width), width),
                                               [r for r in parent_rows if r['instrument'] == symbol and r['timeframe'] == f'M{width}'],
                                               symbol + f' parent M{width}', discrepancies)
        checked['indicator_fields'] += compare(reconstructed[symbol, 'FEATURES', 0], [r for r in published['indicator_features'] if r['instrument'] == symbol], symbol + ' features', discrepancies)
        for architecture in ('SQUEEZE_M15', 'SQUEEZE_H1_M15'):
            for scenario in (10, 15):
                key = symbol, architecture, scenario
                result = reconstructed[key]
                def group(rows):
                    return [r for r in rows if (r['instrument'], r['architecture'], r['scenario']) == (symbol, architecture, f'T{scenario}')]
                for name, rows in result.items():
                    checked[name + '_fields'] += compare(rows, group(published[name]), str(key) + ' ' + name, discrepancies)
                totals, cov, days = summaries_for(result, raw, parents_by_symbol[symbol])
                coverage_by_symbol[symbol] = cov
                annual_complete = all(c['coverage_status'] == 'COVERED' for c in cov.values()) and not totals['unknown']
                annual_fields = dict(full_net=totals['closed_net'] if annual_complete else None,
                                     full_PF=totals['closed_net_PF'] if annual_complete else None,
                                     full_DD=totals['closed_realized_DD'] if annual_complete else None,
                                     metric_scope='COMPLETE_RESEARCH_CALENDAR' if annual_complete else 'CLOSED_ONLY_DIAGNOSTIC')
                checked['metrics_fields'] += compare([totals | annual_fields], group(metrics), str(key) + ' metrics', discrepancies)
                for row in group(metrics):
                    if any(row.get(k) != '' for k in ('full_net', 'full_PF', 'full_DD')):
                        discrepancies.append(dict(table=str(key), field='full_annual_metrics', expected='NULL', actual={k: row.get(k) for k in ('full_net', 'full_PF', 'full_DD')}))
                ledger = result['trade_ledger']
                for cost in (1, 2):
                    cost_totals = aggregate(ledger, cost)
                    cost_annual = dict(full_net=cost_totals['closed_net'] if annual_complete else None,
                                       full_PF=cost_totals['closed_net_PF'] if annual_complete else None,
                                       full_DD=cost_totals['closed_realized_DD'] if annual_complete else None,
                                       metric_scope=annual_fields['metric_scope'])
                    checked['sensitivity_fields'] += compare([cost_totals | cost_annual], [r for r in group(sensitivity) if r['cost'] == f'C{cost}'], str(key) + f'C{cost}', discrepancies)
                    for direction in ('LONG', 'SHORT'):
                        direction_totals = aggregate([r for r in ledger if r['direction'] == direction], cost)
                        direction_annual = dict(full_net=direction_totals['closed_net'] if annual_complete else None,
                                                full_PF=direction_totals['closed_net_PF'] if annual_complete else None,
                                                full_DD=direction_totals['closed_realized_DD'] if annual_complete else None,
                                                metric_scope=annual_fields['metric_scope'])
                        checked['direction_fields'] += compare([direction_totals | direction_annual],
                                                               [r for r in group(directions) if r['direction'] == direction and r.get('cost', 'C1') == f'C{cost}'],
                                                               str(key) + direction + f'C{cost}', discrepancies)
                    for period, coverage in cov.items():
                        subset = [r for r in ledger if r['entry_at'].strftime('%Y-%m') == period]
                        csv_coverage = coverage
                        wanted = aggregate(subset, cost) | csv_coverage
                        if coverage['coverage_status'] == 'NO_COVERAGE':
                            wanted = {k: v if k in ('entries', 'closed', 'unknown', 'unknown_entry_orders', 'PF_status') or k in csv_coverage else None for k, v in wanted.items()}
                        long = aggregate([r for r in subset if r['direction'] == 'LONG'], cost)
                        short = aggregate([r for r in subset if r['direction'] == 'SHORT'], cost)
                        sign = 'NO_COVERAGE' if coverage['coverage_status'] == 'NO_COVERAGE' else 'UNKNOWN' if wanted['unknown'] else 'NO_TRADES' if not subset else 'POSITIVE' if wanted['closed_net'] > 0 else 'NEGATIVE' if wanted['closed_net'] < 0 else 'ZERO_NET'
                        month_complete = coverage['coverage_status'] == 'COVERED' and not wanted['unknown']
                        wanted.update(long_entries=long['entries'], short_entries=short['entries'], long_closed_net=long['closed_net'] if coverage['coverage_status'] != 'NO_COVERAGE' else None,
                                      short_closed_net=short['closed_net'] if coverage['coverage_status'] != 'NO_COVERAGE' else None,
                                      month_status=sign, sign_scope='CONFIRMED_CALENDAR' if month_complete else 'CLOSED_SUBSET_ONLY',
                                      full_net=wanted['closed_net'] if month_complete else None,
                                      full_PF=wanted['closed_net_PF'] if month_complete else None,
                                      full_DD=wanted['closed_realized_DD'] if month_complete else None)
                        records = [r for r in group(monthly) if r['period'] == period and r.get('cost', 'C1') == f'C{cost}']
                        checked['monthly_fields'] += compare([wanted], records, str(key) + period + f'C{cost}', discrepancies)
                        if coverage['coverage_status'] != 'COVERED' or wanted['unknown']:
                            for r in records:
                                if any(r.get(k) != '' for k in ('full_net', 'full_PF', 'full_DD')):
                                    discrepancies.append(dict(table=str(key) + period, field='incomplete_month_full_metrics', expected='NULL'))
                known = [r for r in ledger if r['entry'] is not None]
                counts = Counter(r['entry_at'].date() for r in known)
                week_entries, week_days = Counter(), Counter()
                for day, (expected, observed) in days.items():
                    checked['frequency_fields'] += compare([dict(entries=counts[day], expected_slots=expected, observed_slots=observed,
                                                               no_trade=counts[day] == 0, data_absent=observed == 0)],
                                                          [r for r in group(frequencies) if r['frequency'] == 'DAY' and r['period'] == str(day)], str(key) + str(day), discrepancies)
                    week = f'{day.isocalendar().year}-W{day.isocalendar().week:02d}'
                    week_entries[week] += counts[day]
                    week_days[week] += 1
                for week in week_days:
                    checked['weekly_frequency_fields'] += compare([dict(entries=week_entries[week], eligible_days=week_days[week])],
                                                                 [r for r in group(frequencies) if r['frequency'] == 'WEEK' and r['period'] == week], str(key) + week, discrepancies)
                for period, c in cov.items():
                    count = sum(r['entry_at'].strftime('%Y-%m') == period for r in known)
                    checked['monthly_frequency_fields'] += compare([dict(entries=count if c['coverage_status'] != 'NO_COVERAGE' else None, coverage_status=c['coverage_status'])],
                                                                  [r for r in group(frequencies) if r['frequency'] == 'MONTH' and r['period'] == period], str(key) + period + 'frequency', discrepancies)
                summaries.append(dict(instrument=symbol, architecture=architecture, scenario=f'T{scenario}') | totals)
                wanted_funnel = [dict(status=status, reason=reason, count=count)
                                 for (status, reason), count in sorted(Counter((s['status'], s['reason']) for s in result['signals']).items())]
                actual_funnel = sorted(group(funnel), key=lambda r: (r['status'], r['reason']))
                checked['funnel_fields'] += compare(wanted_funnel, actual_funnel, str(key) + ' funnel', discrepancies)
                safe = [s for s in result['signals'] if window(s['planned_execution_at']) == window(s['signal_at']) and
                        s['planned_execution_at'] + TD(minutes=25) <= floor_clock(window(s['signal_at'])[1] - TD(minutes=35), 15) - FIVE]
                context = [s for s in safe if s['mtf_reason'] is None]
                geometry = [s for s in context if admissible(symbol, s, s['signal_close'], s['available_at'])[1] is None]
                stage_values = dict(ALL_2023_SOURCE_M5=len(raw), COMPLETE_USABLE_M15=sum(p['usable'] for p in parents_by_symbol[symbol].values()),
                                    READY_BB7_EMA7_ATR7=len(reconstructed[symbol, 'FEATURES', 0]), RAW_SQUEEZE_EPISODES=len(result['squeeze_cycles']),
                                    CONFIRMED_SQUEEZES=sum(e['bars'] >= 2 for e in result['squeeze_cycles']), DIRECTIONAL_EXPANSIONS=len(result['signals']),
                                    COMMON_SESSION_SAFE_TARGETS=len(safe), ENTRY_CONTEXT_ALLOWED=len(context), SIGNAL_CLOSE_GEOMETRY_ALLOWED=len(geometry),
                                    SUBMITTED_ORDERS=totals['model_orders'], CONDITIONAL_EXACT_OPEN_FILLS=totals['entries'], NONFILL=totals['nonfills'],
                                    UNKNOWN_ORDER_OR_PATH=totals['unknown'])
                actual_stages = {r['stage']: r for r in group(funnel_stages)}
                if set(actual_stages) != set(stage_values):
                    discrepancies.append(dict(table=str(key) + ' stage funnel', field='stage_names', expected=sorted(stage_values), actual=sorted(actual_stages)))
                for stage, count in stage_values.items():
                    checked['funnel_stage_fields'] += compare([dict(count=count)], [actual_stages[stage]] if stage in actual_stages else [], str(key) + stage, discrepancies)
        cov = coverage_by_symbol[symbol]
        for period, c in cov.items():
            wanted_coverage = {k: v for k, v in c.items() if 'm15' in k}
            checked['m15_coverage_fields'] += compare([wanted_coverage], [r for r in m15_coverage_rows if r['instrument'] == symbol and r['period'] == period], symbol + period + ' M15 coverage', discrepancies)
        for scenario in (10, 15):
            a, b = (reconstructed[symbol, arch, scenario]['trade_ledger'] for arch in ('SQUEEZE_M15', 'SQUEEZE_H1_M15'))
            ai, bi = ({r['signal_id'] for r in ledger if r['entry'] is not None} for ledger in (a, b))
            ap, bp = aggregate(a), aggregate(b)
            wanted = dict(m15_entries=len(ai), h1_entries=len(bi), retained_entries=len(ai & bi), removed_entries=len(ai - bi),
                          freed_entries=len(bi - ai), m15_closed_net=ap['closed_net'], h1_closed_net=bp['closed_net'],
                          m15_closed_PF=ap['closed_net_PF'], h1_closed_PF=bp['closed_net_PF'], m15_unknown=ap['unknown'], h1_unknown=bp['unknown'])
            checked['comparison_fields'] += compare([wanted], [r for r in comparison_rows if r['instrument'] == symbol and r['scenario'] == f'T{scenario}'], symbol + f'T{scenario} comparison', discrepancies)
    artifact = dict(status='INDEPENDENT_TRADING_LOGIC_PASS' if not discrepancies else 'INDEPENDENT_TRADING_LOGIC_FAIL',
                    algorithm='Raw bounded source prefixes; exact M15/H1; independent weighted batch features/cycle scan/execution state machine/metrics; no production imports',
                    numeric_tolerance='1e-24 * max(1,abs(expected)); production precision34, oracle50',
                    runs=16, checked_fields=dict(checked), provenance=provenance, config_sha256=sha(CONFIG.read_bytes()),
                    oracle_sha256=sha(Path(__file__).read_bytes()), independent_reconstruction_sha256=sha(replay_bytes),
                    full_annual_metrics='NULL: incomplete history/gaps/UNKNOWN', discrepancies=discrepancies, summaries=summaries)
    (output / 'independent_audit.json').write_text(json.dumps(artifact, default=str, sort_keys=True, indent=2) + '\n')
    (output / 'coverage_m15.json').write_text(json.dumps(dict(scope='All 12 calendar months; M15 eligible slots in accepted restricted windows; independent raw-source reconstruction',
                                                            instruments=coverage_by_symbol), default=str, sort_keys=True, indent=2) + '\n')
    print(artifact['status'], '; checked fields:', sum(checked.values()), '; discrepancies:', len(discrepancies))
    return artifact


def standalone_reconstruction(data, provenance, results, output):
    gate = json.loads((results / 'independent_feasibility.json').read_text())
    assert gate['status'] == 'FEASIBILITY PASS' and gate['pnl_calculated'] is False
    assert gate['config_sha256'] == sha(CONFIG.read_bytes())
    output.mkdir(parents=True, exist_ok=True)
    reconstructed, summaries = {}, []
    for symbol, raw in data.items():
        parents, h1 = compose(raw, 15), compose(raw, 60)
        features = batch_indicators(parents)
        reconstructed[symbol, 'FEATURES', 0] = list(features.values())
        reconstructed[symbol, 'M15', 0] = [{k: v for k, v in p.items() if k != 'bar'} for p in parents.values()]
        reconstructed[symbol, 'H1', 0] = [{k: v for k, v in p.items() if k != 'bar'} for p in h1.values()]
        for architecture in ('SQUEEZE_M15', 'SQUEEZE_H1_M15'):
            for scenario in (10, 15):
                result = reconstruct(raw, symbol, architecture, scenario, parents, h1, features)
                reconstructed[symbol, architecture, scenario] = result
                summaries.append(dict(instrument=symbol, architecture=architecture, scenario=f'T{scenario}') |
                                 summaries_for(result, raw, parents)[0])
    raw = json.dumps({str(k): v for k, v in reconstructed.items()}, default=str, sort_keys=True).encode()
    (output / 'precomparison_reconstructed.json.gz').write_bytes(gzip.compress(raw, mtime=0))
    report = dict(status='INDEPENDENT_RECONSTRUCTION_COMPLETE_BEFORE_PUBLISHED_READ', runs=16,
                  config_sha256=sha(CONFIG.read_bytes()), oracle_sha256=sha(Path(__file__).read_bytes()),
                  independent_reconstruction_sha256=sha(raw), provenance=provenance, summaries=summaries)
    (output / 'precomparison_summary.json').write_text(json.dumps(report, default=str, sort_keys=True, indent=2) + '\n')
    print(report['status'])


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--data-root', type=Path, required=True)
    p.add_argument('--feasibility', type=Path)
    p.add_argument('--results', type=Path)
    p.add_argument('--output', type=Path)
    p.add_argument('--reconstruct-only', action='store_true')
    args = p.parse_args()
    with localcontext() as ctx:
        ctx.prec = 50
        _, data, provenance = load_source(args.data_root)
        if args.feasibility:
            assert not args.feasibility.exists(), 'Fresh feasibility output only'
            report = feasibility(data, provenance)
            args.feasibility.write_text(json.dumps(report, default=str, sort_keys=True, indent=2) + '\n')
            print(report['status'], '; P&L not calculated')
            return
        assert args.results and args.output, '--results and --output required for economic audit'
        if args.reconstruct_only:
            standalone_reconstruction(data, provenance, args.results, args.output)
            return
        report = audit(data, provenance, args.results, args.output)
        if report['discrepancies']:
            raise SystemExit(1)


if __name__ == '__main__':
    main()
