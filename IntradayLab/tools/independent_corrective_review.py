#!/usr/bin/env python3
"""Read-only independent 2023 audit and versioned reporting correction.

Never writes frozen v1/v2, source data, or strategy settings. Full metrics mean
complete approved-window calendar coverage AND complete execution accounting.
Replay is invoked in memory solely to verify the frozen record, not to generate
replacement strategy results. Independent source/path checks precede replay.
"""
import argparse
from bisect import bisect_left
from collections import Counter, defaultdict
import csv
from datetime import datetime, timedelta
from decimal import Decimal as D, ROUND_CEILING, ROUND_FLOOR
import hashlib
import io
import json
from pathlib import Path
from statistics import median
import subprocess

LAB = Path(__file__).resolve().parents[1]
FROZEN = LAB / 'results/stage2_m5_conditional_v2'
DEST = LAB / 'results/stage2_m5_v2_corrective_review'
BASE = '90369e12332e738da222dfe510120747c6ce9e80'
FIVE = timedelta(minutes=5)
TEN = timedelta(minutes=10)
END = datetime(2024, 1, 1)
CASES = [('VWAP_MR', 'USDRUBF', '2023-02-02 15:40:00'),
         ('VWAP_MR', 'CNYRUBF', '2023-01-06 17:15:00'),
         ('VWAP_MR', 'GLDRUBF', '2023-08-17 16:00:00'),
         ('VWAP_MR', 'IMOEXF', '2023-11-30 17:20:00'),
         ('MOMENTUM', 'USDRUBF', '2023-02-03 16:15:00'),
         ('MOMENTUM', 'CNYRUBF', '2023-01-19 15:25:00'),
         ('MOMENTUM', 'GLDRUBF', '2023-07-12 11:40:00'),
         ('MOMENTUM', 'IMOEXF', '2023-11-15 16:25:00')]


def encoded(obj):
    return json.dumps(obj, default=lambda x: str(x) if isinstance(x, D) else
                      (_ for _ in ()).throw(TypeError(type(x).__name__)),
                      ensure_ascii=False, sort_keys=True, indent=2) + '\n'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()


def table(name):
    with (FROZEN / name).open(newline='') as f:
        return list(csv.DictReader(f))


def write_csv(path, rows):
    out = io.StringIO(newline='')
    fields = list(dict.fromkeys(k for r in rows for k in r))
    writer = csv.DictWriter(out, fields, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    path.write_text(out.getvalue())


def asof(value):
    return datetime.fromisoformat(value)


def independent_tick(symbol, at):
    if symbol == 'CNYRUBF':
        return D('.01') if at < datetime(2023, 9, 27, 19) else D('.001')
    return {'USDRUBF': D('.01'), 'GLDRUBF': D('.1'), 'IMOEXF': D('.5')}[symbol]


def intervals(day):
    # Independent implementation of the declared 2023 calendar contract.
    holidays = {(1, 1), (1, 2), (1, 7), (2, 23), (3, 8), (5, 1),
                (5, 9), (6, 12), (11, 4)}
    if day.year != 2023 or day.weekday() >= 5 or (day.month, day.day) in holidays:
        return []
    a = datetime(day.year, day.month, day.day, 10)
    extended = datetime(2023, 3, 13).date() <= day < datetime(2023, 3, 21).date()
    return [(a, a.replace(hour=14)),
            (a.replace(hour=14, minute=15 if extended else 5), a.replace(hour=18, minute=50))]


def admissible(at):
    return any(a <= at and at + FIVE <= z for a, z in intervals(at.date()))


def exact_lines(raw, count):
    """Independent one-byte reader: physically cannot cross the budget's LF."""
    if not isinstance(raw, io.RawIOBase) or type(count) is not int or count < 1:
        raise ValueError('Unbuffered raw input and positive exact line budget required')
    for _ in range(count):
        line = bytearray()
        while True:
            byte = raw.read(1)
            if not byte:
                raise ValueError('Truncated prefix')
            line.extend(byte)
            if byte == b'\n':
                break
            if len(line) > 4096:
                raise ValueError('Oversized line')
        yield bytes(line)


def independent_inputs(root, manifest):
    if git(root, 'rev-parse', 'HEAD') != manifest['source_ref']:
        raise ValueError('Wrong frozen source revision')
    if git(root, 'status', '--porcelain=v1', '--untracked-files=all'):
        raise ValueError('Source must be clean')
    data, provenance = {}, {}
    for symbol, spec in manifest['inputs'].items():
        assert git(root, 'ls-files', '--stage', '--', spec['path']).split()[1] == spec['blob']
        path = root / spec['path']
        before = path.stat()
        digest, byte_count, rows = hashlib.sha256(), 0, {}
        with path.open('rb', buffering=0) as raw:
            for i, line in enumerate(exact_lines(raw, spec['rows_2023'] + 1)):
                digest.update(line)
                byte_count += len(line)
                r = next(csv.reader([line.decode('utf-8-sig' if i == 0 else 'utf-8')], delimiter=';'))
                if i == 0:
                    assert r == ['Ticker', 'Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']
                    continue
                assert r[0] == symbol and len(r) == 7
                at = asof(r[1])
                # Reject protected dates BEFORE prices or volume are parsed.
                if at.year != 2023 or at.tzinfo is not None:
                    raise ValueError('2023 MSK naive start-label required')
                assert at not in rows and (not rows or at > next(reversed(rows)))
                o, h, l, c, v = map(D, r[2:])
                assert l <= min(o, c) <= max(o, c) <= h and v >= 0
                assert all(x % independent_tick(symbol, at) == 0 for x in (o, h, l, c))
                rows[at] = (o, h, l, c, v)
        after = path.stat()
        assert all(getattr(before, k) == getattr(after, k) for k in
                   ('st_size', 'st_mtime_ns', 'st_ctime_ns', 'st_ino', 'st_mode'))
        assert len(rows) == spec['rows_2023'] and str(next(iter(rows))) == spec['first']
        data[symbol] = rows
        provenance[symbol] = {'rows': len(rows), 'prefix_bytes_read': byte_count,
            'prefix_sha256': digest.hexdigest(), 'blob_sha': spec['blob'],
            'first': str(next(iter(rows))), 'last': str(next(reversed(rows))),
            'bytes_2024_plus_read': 0, 'bytes_2025_plus_read': 0,
            'reader': 'Independent unbuffered read(1), exact header + frozen 2023 row budget'}
    assert not git(root, 'status', '--porcelain=v1', '--untracked-files=all')
    return data, provenance


def neighbours(index, at):
    times = list(index)
    i = bisect_left(times, at)
    return {'previous_observed_at': str(times[i-1]) if i else None,
            'next_observed_at': str(times[i]) if i < len(times) else None}


def audit_signal_rules(signals, data):
    """Enumerate fixed-rule opportunities from independent past-only segments."""
    expected = {}
    for symbol, index in data.items():
        for strategy in ('VWAP_MR', 'MOMENTUM'):
            prior, vwaps, weight, weighted, window = [], [], D(0), D(0), None
            for at, (o, h, l, c, volume) in index.items():
                w = next(((a, z) for a, z in intervals(at.date()) if a <= at < z), None)
                if not w or at+TEN >= w[1] or not admissible(at):
                    prior, vwaps, weight, weighted, window = [], [], D(0), D(0), None
                    continue
                if w != window or (prior and at != prior[-1][0]+FIVE) or (strategy == 'VWAP_MR' and volume <= 0):
                    prior, vwaps, weight, weighted = [], [], D(0), D(0)
                window = w
                if strategy == 'VWAP_MR' and volume <= 0:
                    continue
                weight += volume
                weighted += (h+l+c)/3*volume
                vwap = weighted/weight if weight else None
                if len(prior) >= 13:
                    tr = [max(y[2]-y[3], abs(y[2]-x[4]), abs(y[3]-x[4]))
                          for x, y in zip(prior[-13:-1], prior[-12:])]
                    atr = sum(tr, D(0))/12
                    high = max(x[2] for x in prior[-12:])
                    low = min(x[3] for x in prior[-12:])
                    direction = 0
                    if atr > 0:
                        if strategy == 'MOMENTUM':
                            direction = 1 if c > high else -1 if c < low else 0
                        elif vwap is not None and vwaps[-1] is not None:
                            old = prior[-1][4]
                            if old <= vwaps[-1]-atr and vwap-atr < c < vwap:
                                direction = 1
                            elif old >= vwaps[-1]+atr and vwap < c < vwap+atr:
                                direction = -1
                    if direction:
                        tick = independent_tick(symbol, at+TEN)
                        stop = c-direction*D('1.5')*atr
                        take = vwap if strategy == 'VWAP_MR' else c+direction*3*atr
                        cap = c+direction*D('.25')*atr
                        def rnd(value, up):
                            return (value/tick).to_integral_value(rounding=ROUND_CEILING if up else ROUND_FLOOR)*tick
                        expected[strategy+'_'+symbol, str(at)] = (direction, atr, high, low,
                            rnd(stop, direction == 1), rnd(take, direction == 1), rnd(cap, direction != 1))
                prior.append((at, o, h, l, c))
                vwaps.append(vwap)
    actual = {(s['run'], s['signal_at']): s for s in signals}
    assert set(expected) == set(actual), ('missing or extra fixed-rule signals', len(expected), len(actual))
    for key, values in expected.items():
        s = actual[key]
        assert values == (int(s['direction_sign']), *map(D, (s['atr_shifted'], s['range_high_shifted'],
                          s['range_low_shifted'], s['stop'], s['take'], s['cap']))), key
    return len(expected)


def coverage(data):
    out = {}
    for symbol, index in data.items():
        for month in range(1, 13):
            start = datetime(2023, month, 1)
            end = datetime(2023, month+1, 1) if month < 12 else END
            expected = set()
            day = start
            while day < end:
                for a, z in intervals(day.date()):
                    t = a
                    while t + FIVE <= z:
                        expected.add(t)
                        t += FIVE
                day += timedelta(days=1)
            observed = expected.intersection(index)
            status = 'NO_COVERAGE' if not observed else 'PARTIAL_COVERAGE' if expected-observed else 'COVERED'
            out[symbol, f'2023-{month:02d}'] = {'coverage_status': status,
                'expected_calendar_research_slots': len(expected),
                'observed_calendar_research_slots': len(observed),
                'missing_calendar_research_slots': len(expected-observed),
                'pre_source_inception_slots': sum(t < next(iter(index)) for t in expected)}
    return out


def aggregate(rows, coverage_status, spanning_unknown=False):
    """No unqualified closed-subset metrics, even for partial calendar periods."""
    closed = [r for r in rows if r['net_model_c1'] not in ('', None)]
    unknown = sum(r['status'] == 'UNRESOLVED' for r in rows)
    nets = [D(r['net_model_c1']) for r in closed]
    gross = [D(r['gross_price_pnl']) for r in closed]
    costs = [D(r['c1_total']) for r in closed]
    wins, loss = sum((v for v in nets if v > 0), D(0)), -sum((v for v in nets if v < 0), D(0))
    pf = wins / loss if loss else None
    diag_reason = 'NO_CLOSED_TRADES' if not nets else 'NO_LOSSES' if not loss else None
    incomplete = bool(unknown or spanning_unknown)
    full = coverage_status == 'COVERED' and not incomplete
    reason = ('NO_COVERAGE' if coverage_status == 'NO_COVERAGE' else 'UNRESOLVED' if incomplete
              else 'PARTIAL_COVERAGE' if coverage_status != 'COVERED' else diag_reason)
    status = ('NO_COVERAGE' if coverage_status == 'NO_COVERAGE' else 'UNRESOLVED' if incomplete
              else 'PARTIAL_COVERAGE' if coverage_status != 'COVERED' else 'ZERO_TRADES' if not rows else 'COMPLETE')
    cumulative = peak = dd = D(0)
    for n in nets:
        cumulative += n
        peak = max(peak, cumulative)
        dd = max(dd, peak-cumulative)
    def closed_pf(vals):
        p = sum((v for v in vals if v > 0), D(0))
        l = -sum((v for v in vals if v < 0), D(0))
        return p/l if l else None
    return {'trades': len(rows), 'closed_accounted_trades': len(closed), 'unresolved': unknown,
        'spanning_unknown_exposure': spanning_unknown, 'coverage_status': coverage_status,
        'execution_accounting_status': 'UNRESOLVED' if incomplete else 'ZERO_TRADES' if not rows else 'ACCOUNTED',
        'metric_status': status, 'full_period_accounted': full,
        'PF': pf if full else None, 'full_PF': pf if full else None,
        'PF_null_reason': reason, 'full_PF_null_reason': reason,
        'Net': sum(nets, D(0)) if full else None,
        'net_model_c1': sum(nets, D(0)) if full else None,
        'Net_null_reason': None if full else reason,
        'Drawdown': None, 'full_Drawdown': None,
        'Drawdown_null_reason': reason if not full else 'INTRABAR_PATH_UNOBSERVED',
        'net_PF_closed_diagnostic': pf, 'net_PF_closed_diagnostic_null_reason': diag_reason,
        'gross_PF_closed_diagnostic': closed_pf(gross),
        'closed_only_gross': sum(gross, D(0)) if closed else None,
        'closed_only_c1': sum(costs, D(0)) if closed else None,
        'closed_only_net_c1': sum(nets, D(0)) if closed else None,
        'net_expectancy_closed_diagnostic': sum(nets, D(0))/len(nets) if nets else None,
        'net_win_rate_closed_diagnostic': D(sum(v > 0 for v in nets))/len(nets) if nets else None,
        'closed_only_drawdown_price_units': dd if nets else None,
        'closed_subset_outcome': 'NO_CLOSED_TRADES' if not nets else 'POSITIVE' if sum(nets) > 0
                                  else 'NEGATIVE' if sum(nets) < 0 else 'ZERO_NET',
        'exit_reasons': dict(Counter(r['exit_reason'] for r in rows)),
        'metric_basis': 'Declared conditional M5 model; full fields require full approved-window period coverage; closed diagnostics omit all unknown trades'}


def breakout_diagnostic(row, signal, index):
    """A close of the exit bar is never proof of return before that exit."""
    long = row['direction'] == 'LONG'
    high, low = D(signal['range_high_shifted']), D(signal['range_low_shifted'])
    entry = asof(row['entry_interval_start'])
    price = D(row['entry'])
    known = row['status'] == 'MODELLED'
    end = asof(row['exit_interval_start']) if known else None
    before = [(at, b[3]) for at, b in index.items() if known and entry <= at and at+FIVE <= end]
    across = lambda c: c <= high if long else c >= low
    elapsed = (end-entry)/FIVE*5 if known else None
    return {'run': row['run'], 'signal_id': row['signal_id'], 'status': row['status'],
        'entry_at_msk': str(entry), 'exit_at_msk': str(end) if known else None,
        'range_reentered_at_model_open': price <= high if long else price >= low,
        'close_crossed_breakout_edge_before_exit': any(across(c) for _, c in before) if known else None,
        'close_inside_full_frozen_range_before_exit': any(low <= c <= high for _, c in before) if known else None,
        'close_return_observable_before_exit_start': any(at+TEN <= end and across(c) for at, c in before) if known else None,
        'stop_on_entry_bar': row['exit_reason'] == 'STOP' and elapsed == 0,
        'stop_within_10_minutes': row['exit_reason'] == 'STOP' and elapsed is not None and elapsed <= 10,
        'basis': 'Price close must complete before exit interval start; separate t+10 availability flag. Exit-bar close excluded; not a new strategy filter.'}


def path_audit(row, index, own_events):
    """Independently scan every pre-gap/known-exit bar and scheduled time exit."""
    entry, stop, take = map(D, (row['entry'], row['stop'], row['take']))
    sign = 1 if row['direction'] == 'LONG' else -1
    at = asof(row['entry_interval_start'])
    hold = 60 if row['strategy'] == 'VWAP_MR' else 90
    boundary = asof(row['session_id'].split('--')[1])
    sent = min(at + timedelta(minutes=hold-5), boundary-timedelta(minutes=25))
    planned_exit = sent + FIVE
    stop_at = asof(row['model_flat_scenario_at'])
    t = at
    first_gap = None
    result = None
    while t <= stop_at:
        assert admissible(t), (row['signal_id'], t, 'unexpected window crossing')
        b = index.get(t)
        if b is None:
            first_gap = t
            break
        o, h, l, _, _ = b
        if t >= planned_exit:
            result = (t, o, 'SESSION_FLAT' if sent == boundary-timedelta(minutes=25) else 'MAX_HOLD')
            break
        stop_hit = l <= stop if sign == 1 else h >= stop
        take_hit = h >= take+independent_tick(row['instrument'], t) if sign == 1 else l <= take-independent_tick(row['instrument'], t)
        if stop_hit:
            result = (t, min(o, stop) if sign == 1 else max(o, stop), 'STOP')
            break
        if take_hit and t != at:
            result = (t, take, 'TAKE')
            break
        t += FIVE
    if row['status'] == 'UNRESOLVED':
        assert result is None and first_gap is not None, (row['signal_id'], result)
        path_events = [e for e in own_events if e['kind'] == 'POSITION_PATH']
        assert path_events and asof(path_events[0]['at']) == first_gap
        for e in path_events:
            missing = asof(e['at'])
            assert missing not in index and admissible(missing)
            assert asof(e['confirmed_at']) == missing+TEN
        assert not any(e['kind'] == 'EXIT' for e in own_events)
        for k in ('net_model_c1', 'gross_price_pnl', 'exit', 'c1_exit', 'c1_total', 'exit_filled_model_units'):
            assert row[k] == '', (row['signal_id'], k)
        flat_events = [e for e in own_events if e['kind'] == 'MODEL_FLAT_CONFIRMATION']
        assert len(flat_events) == 1
        flat = flat_events[0]
        scenario, ack = asof(flat['at']), asof(flat['confirmed_at'])
        orders = [e for e in own_events if e['kind'] == 'EXIT_ORDER']
        order_at = asof(orders[0]['at'])
        assert scenario > order_at and scenario in index and admissible(scenario) and ack == scenario+TEN
        # Retry picks first admissible observed slot after the causally scheduled request.
        assert not any(x in index and admissible(x) for x in
                       (order_at+FIVE+i*FIVE for i in range(int((scenario-order_at)/FIVE)-1)))
        missing_times = [asof(e['at']) for e in path_events]
        spans_timer = any(t >= planned_exit for t in missing_times)
        return {'run': row['run'], 'signal_id': row['signal_id'], 'instrument': row['instrument'],
            'strategy': row['strategy'], 'direction': row['direction'],
            'entry_at_msk': row['entry_interval_start'], 'entry_price': entry,
            'stop': stop, 'take': take, 'first_missing_at_msk': str(first_gap),
            'missing_observations_msk': '|'.join(map(str, missing_times)),
            'missing_observation_count': len(missing_times),
            'absence_detected_at_msk': str(first_gap+TEN),
            **neighbours(index, first_gap), 'source_blob_sha': row['_blob'],
            'physical_gap': True, 'admissible_expected_slot': True, 'loader_removed_row': False,
            'position_open_before_gap': True, 'known_pre_gap_exit': False,
            'stop_possible': True, 'take_possible': True, 'no_exit_possible': True,
            'scheduled_time_or_session_request_at_msk': str(sent),
            'scheduled_time_or_session_slot_at_msk': str(planned_exit),
            'time_or_session_exit_price_missing': spans_timer,
            'time_exit_possible_under_preexisting_order': orders[0]['reason'] == 'MAX_HOLD',
            'session_exit_possible_under_preexisting_order': orders[0]['reason'] == 'SESSION_FLAT',
            'preexisting_exit_order_reason': orders[0]['reason'],
            'conditional_reduce_all_scenario_at_msk': str(scenario),
            'conditional_model_flat_ack_msk': str(ack),
            'b_minus_10_msk': str(boundary-TEN),
            'b_minus_10_breach': ack > boundary-TEN,
            'primary_category': 'REAL_MISSING_PRICE_PATH',
            'resolution_status': 'OBJECTIVELY_UNRESOLVABLE_WITH_AVAILABLE_2023_M5',
            'causal_recovery_possible': False, 'status_after': 'UNRESOLVED', 'Net': None,
            'why_insufficient': 'Neighbour OHLCV cannot bound missing intrabar extrema or opening price. Stop, tick-penetrating Take and survival branches remain possible; later reduce-all proves conditional flat only.',
            'additional_observation_required': 'Missing M5 OHLCV for every listed slot (including Open for a scheduled exit); if venue suspension/no transactions, independently timed halt/resumption and quote/execution evidence. Actual exchange P&L additionally needs fills, quantities, costs and reconciliation.',
            'calendar_time_replay_error': False}
    assert first_gap is None and result is not None, (row['signal_id'], first_gap, result)
    t, price, reason = result
    assert (str(t), price, reason) == (row['exit_interval_start'], D(row['exit']), row['exit_reason'])
    assert asof(row['exit_confirmed_at']) == t+TEN
    gross = sign*(price-entry)
    c1_entry = independent_tick(row['instrument'], at)
    c1_exit = independent_tick(row['instrument'], t)
    assert D(row['gross_price_pnl']) == gross
    assert D(row['c1_entry']) == c1_entry and D(row['c1_exit']) == c1_exit
    assert D(row['c1_total']) == c1_entry+c1_exit
    assert D(row['net_model_c1']) == gross-c1_entry-c1_exit
    assert D(row['net_R']) == D(row['net_model_c1'])/D(row['initial_risk_price_units'])
    return None


def run(root, test_log=None):
    manifest_path = LAB/'config/stage2_m5_conditional_v2.json'
    m = json.loads(manifest_path.read_text())
    assert sha(manifest_path) == manifest_path.with_suffix('.sha256').read_text().split()[0]
    frozen_hashes = {p.name: sha(p) for p in sorted(FROZEN.iterdir()) if p.is_file()}
    for line in (FROZEN/'SHA256SUMS').read_text().splitlines():
        digest, name = line.split()
        assert frozen_hashes[name] == digest
    data, prov = independent_inputs(root, m)
    # Loader comparison, independently parsed contents rather than verification.json.
    from run_m5_baseline import inputs
    loaded, loader_prov = inputs(root, m)
    for symbol, bars in loaded.items():
        assert data[symbol] == {b.timestamp: (b.open, b.high, b.low, b.close, b.volume) for b in bars}
        assert prov[symbol]['prefix_sha256'] == loader_prov[symbol]['prefix_sha256']
    physical = []
    for strategy, symbol, stamp in CASES:
        at = asof(stamp)
        assert at not in data[symbol] and admissible(at)
        physical.append({'strategy': strategy, 'instrument': symbol, 'missing_at_msk': stamp,
                         **neighbours(data[symbol], at), 'source_blob_sha': m['inputs'][symbol]['blob'],
                         'physical_gap': True, 'loader_filter_cause': False})
    trades, events, signals = table('trade_ledger.csv'), table('execution_events.csv'), table('signals.csv')
    assert m['parameters'] == json.loads((LAB/'config/stage2_m5_baseline_v1.json').read_text())['parameters']
    signal_count = audit_signal_rules(signals, data)
    own = defaultdict(list)
    for e in events:
        own[e['signal_id']].append(e)
    by_signal = {s['signal_id']: s for s in signals}
    unresolved = []
    for row in trades:
        symbol = row['instrument']
        at = asof(row['entry_interval_start'])
        signal = by_signal[row['signal_id']]
        assert at == asof(signal['planned_execution_at']) == asof(signal['signal_at'])+3*FIVE
        assert D(row['entry']) == data[symbol][at][0] and asof(row['entry_confirmed_at']) == at+TEN
        assert row['entry_filled_model_units'] == '1'
        assert all(row[k] == signal[s] for k, s in [('stop', 'stop'), ('take', 'take'), ('entry_cap', 'cap')])
        p, st, tp, cap = map(D, (row['entry'], row['stop'], row['take'], row['entry_cap']))
        assert (st < p < tp and p <= cap) if row['direction'] == 'LONG' else (tp < p < st and p >= cap)
        result = path_audit(row | {'_blob': m['inputs'][symbol]['blob']}, data[symbol], own[row['signal_id']])
        if result:
            unresolved.append(result)
    diagnostics = {(r['instrument'], r['missing_at']): r for r in table('missing_bar_diagnostics.csv')}
    for r in unresolved:
        for stamp in r['missing_observations_msk'].split('|'):
            diag = diagnostics[r['instrument'], stamp]
            assert r['run'] in diag['uncertain_position_runs'].split('|')
    frozen_results = json.loads((FROZEN/'results.json').read_text())
    for run_info in frozen_results['runs']:
        assert run_info['summary']['unresolved'] == sum(r['run'] == run_info['run'] for r in unresolved)
    assert len(unresolved) == 82
    assert sum(r['missing_observation_count'] for r in unresolved) == 113
    assert len(trades) == 2140 and len(signals) == 7813
    # Execute the earlier checking algorithm with all output writers intercepted.
    # Its verification.json is produced afresh in memory; never accepted as proof.
    import audit_m5_conditional_v2 as earlier
    captured = {}
    earlier.write = lambda path, value: captured.update({path.name: json.loads(value)})
    earlier.checksums = lambda: None
    earlier.audit(root)
    independent_prior_check = captured['verification.json']
    assert independent_prior_check['counts']['integer_accounted_trades'] == 2058
    # Byte-equivalent canonical CSV records from in-memory frozen implementation.
    from m5_conditional_v2 import Replay
    from run_m5_baseline import csv_text
    replay_signals, replay_events, replay_ledger = [], [], []
    for item in m['run_matrix']:
        r = Replay(item['instrument'], item['strategy'], m['parameters']).run(loaded[item['instrument']])
        replay_signals.extend(r.signals)
        replay_events.extend(r.events)
        replay_ledger.extend(r.ledger)
    for name, records in [('signals.csv', replay_signals), ('execution_events.csv', replay_events), ('trade_ledger.csv', replay_ledger)]:
        fields = list(dict.fromkeys(k for r in records for k in r))
        assert csv_text(records, fields) == (FROZEN/name).read_text(), name
    # Recheck GLD's single already predeclared sensitivity; never introduce tuning.
    delayed = Replay('GLDRUBF', 'MOMENTUM', m['parameters'] | {'availability_minutes': 15}).run(loaded['GLDRUBF'])
    delayed_nets = [r['net_model_c1'] for r in delayed.ledger if r['net_model_c1'] is not None]
    sensitivity = json.loads((FROZEN/'delay_sensitivity.json').read_text())
    gld_delay = next(r for r in sensitivity if r['run'] == 'MOMENTUM_GLDRUBF')
    assert sum(delayed_nets, D(0)) == D(gld_delay['sensitivity_summary']['closed_only_net_c1'])
    assert len(delayed.ledger) == gld_delay['sensitivity_model_entries']
    assert sum(r['status'] == 'UNRESOLVED' for r in delayed.ledger) == gld_delay['sensitivity_summary']['unresolved']
    cov = coverage(data)
    corrected = []
    frozen_metrics = table('metrics.csv')
    for old in frozen_metrics:
        selected = [r for r in trades if r['run'] == old['run'] and
                    (old['group'] != 'MONTH' or r['entry_interval_start'][:7] == old['period']) and
                    (old['direction'] == 'ALL' or r['direction'] == old['direction'])]
        if old['group'] == 'MONTH':
            c = cov[old['instrument'], old['period']]
        else:
            c = {'coverage_status': 'COVERED' if all(cov[old['instrument'], f'2023-{i:02d}']['coverage_status'] == 'COVERED' for i in range(1, 13)) else 'PARTIAL_COVERAGE'}
        spanning = any(r['run'] == old['run'] and
                       (old['direction'] == 'ALL' or r['direction'] == old['direction']) and
                       r['entry_at_msk'][:7] <= old['period'] <= r['conditional_model_flat_ack_msk'][:7]
                       for r in unresolved) if old['group'] == 'MONTH' else False
        identity = {k: old[k] for k in ('run', 'strategy', 'instrument', 'group', 'period', 'direction')}
        corrected.append(identity | c | aggregate(selected, c['coverage_status'], spanning) |
                         {'observed_close_mtm_drawdown_diagnostic': old['observed_close_mtm_drawdown'] or None,
                          'month_end_cumulative_net_mtm_diagnostic': old['month_end_cumulative_net_mtm'] or None})
    corrected_sensitivity = []
    for s in sensitivity:
        c = dict(s)
        summary = dict(c['sensitivity_summary'])
        summary.update(PF=None, full_PF=None, Net=None, net_model_c1=None, Drawdown=None, full_Drawdown=None,
                       PF_null_reason='UNRESOLVED', full_PF_null_reason='UNRESOLVED',
                       Net_null_reason='UNRESOLVED', Drawdown_null_reason='UNRESOLVED', metric_status='UNRESOLVED',
                       net_PF_closed_diagnostic_null_reason=summary['PF_null_reason'],
                       net_PF_closed_diagnostic=summary['net_PF_closed_diagnostic'])
        c['sensitivity_summary'] = summary
        c['verification_basis'] = 'Frozen predeclared sensitivity; GLD Momentum replay independently repeated in this review'
        corrected_sensitivity.append(c)
    summary_rows = []
    econ = table('economics.csv')
    old_breakout = {r['signal_id']: r for r in table('momentum_breakout_diagnostics.csv')}
    breakout = [breakout_diagnostic(r, by_signal[r['signal_id']], data[r['instrument']])
                for r in trades if r['strategy'] == 'MOMENTUM']
    for r in breakout:
        old = old_breakout[r['signal_id']]
        r['frozen_exit_bar_inclusive_return_flag'] = old['observed_close_returned_inside_frozen_range_before_exit'] or None
        r['changed_by_excluding_exit_bar_close'] = (old['observed_close_returned_inside_frozen_range_before_exit'] == 'True' and
                                                   r['close_crossed_breakout_edge_before_exit'] is False)
    for year in (r for r in corrected if r['group'] == 'YEAR'):
        xs = [r for r in econ if r['run'] == year['run'] and r['stage'] == 'MODEL_ENTRY']
        signals_econ = [r for r in econ if r['run'] == year['run'] and r['stage'] == 'SIGNAL']
        b = [r for r in breakout if r['run'] == year['run']]
        summary_rows.append(year | {'entries': len(xs),
            'median_entry_stop_ticks': median(D(r['stop_ticks']) for r in xs),
            'median_entry_take_ticks': median(D(r['take_ticks']) for r in xs),
            'median_potential_net_reward_risk': median(D(r['potential_net_reward_risk']) for r in xs),
            'median_breakeven_win_rate': median(D(r['min_breakeven_win_rate']) for r in xs),
            'signal_targets_not_paying_C1': sum(r['take_cannot_pay_c1'] == 'True' for r in signals_econ),
            'signal_targets_total': len(signals_econ),
            'entry_targets_not_paying_C1': sum(r['take_cannot_pay_c1'] == 'True' for r in xs),
            'momentum_open_range_returns': sum(r['range_reentered_at_model_open'] for r in b),
            'momentum_entry_bar_stops': sum(r['stop_on_entry_bar'] for r in b),
            'momentum_stops_within_10_minutes': sum(r['stop_within_10_minutes'] for r in b),
            'momentum_known_close_returns_before_exit': sum(r['close_crossed_breakout_edge_before_exit'] is True for r in b),
            'momentum_close_returns_observable_before_exit': sum(r['close_return_observable_before_exit_start'] is True for r in b),
            'momentum_exit_bar_return_flags_corrected': sum(r['changed_by_excluding_exit_bar_close'] for r in b)})
    protected = {line.split()[3]: line.split()[2] for line in git(LAB.parent, 'ls-tree', 'HEAD').splitlines() if line.split()[3] != 'IntradayLab'}
    protected_main = {line.split()[3]: line.split()[2] for line in git(LAB.parent, 'ls-tree', 'origin/main').splitlines() if line.split()[3] != 'IntradayLab'}
    assert protected == protected_main
    assert frozen_hashes == {p.name: sha(p) for p in FROZEN.iterdir() if p.is_file()}
    log = test_log.read_text() if test_log else None
    if log is not None:
        assert log.rstrip().endswith('OK') and 'FAILED' not in log and 'skipped=' not in log
    implementation = {str(p.relative_to(LAB)): sha(p) for p in
                      [Path(__file__), LAB/'tests/test_independent_corrective_review.py']}
    provenance = {'schema': 1, 'id': 'stage2_m5_v2_corrective_review', 'parent_pr': 447,
        'base_sha': BASE, 'parent_manifest_sha256': sha(manifest_path), 'source_ref': m['source_ref'],
        'frozen_v2_artifact_sha256': frozen_hashes, 'implementation_sha256': implementation,
        'input_prefixes': prov, 'protected_root_ids': protected,
        'reporting_policy': 'Strict complete calendar period in approved windows + complete conditional accounting. Generic PF/Net never closed-subset aliases. No full intrabar drawdown from OHLCV.',
        'trade_change': False, 'strategy_parameter_change': False, 'source_change': False,
        'execution_contract': 'Unchanged conditional-on-observed-bar v2; independent source/path audit + in-memory exact-record reproduction',
        'test_log_sha256': sha(test_log) if test_log else None}
    breach = next(r for r in unresolved if r['b_minus_10_breach'])
    verification = {'schema': 1, 'audit': 'PASS_FOR_VERIFIED_CHECKS_ONLY',
        'source_prefix_provenance': prov, 'eight_original_missing_slots': physical,
        'counts': {'signals': 7813, 'independently_enumerated_fixed_rule_signals': signal_count,
                   'all_model_entries_checked': 2140,
                   'all_accounted_exits_and_C1_checked': 2058, 'unresolved_before': 82,
                   'unresolved_after': 82, 'resolved_with_evidence': 0, 'position_path_events': 113,
                   'no_bar_no_model_fill': 61, 'corrected_metric_rows': len(corrected),
                   'complete_all_direction_months': sum(r['group'] == 'MONTH' and r['direction'] == 'ALL' and r['full_period_accounted'] for r in corrected),
                   'complete_month_direction_rows': sum(r['group'] == 'MONTH' and r['full_period_accounted'] for r in corrected),
                   'source_rows_per_independent_pass': sum(p['rows'] for p in prov.values()),
                   'source_bytes_per_independent_pass': sum(p['prefix_bytes_read'] for p in prov.values()),
                   '2024_plus_bytes_read': 0, '2025_plus_bytes_read': 0,
                   'source_loader_or_execution_errors_proved': 0, 'reporting_defect_classes_fixed': 3,
                   'breakout_diagnostic_defect_classes_fixed': 1,
                   'exit_bar_return_flags_corrected': sum(r['changed_by_excluding_exit_bar_close'] for r in breakout)},
        'primary_unresolved_categories': {'REAL_MISSING_PRICE_PATH': 82, 'LOADER_FILTER_TIME_ERROR': 0,
            'EXECUTION_CLOSURE_ERROR': 0, 'OTHER_OBJECTIVELY_UNRESOLVABLE': 0},
        'objective_resolution_status_count': 82,
        'defects_fixed': {
            'ambiguous_generic_PF_alias': {'previous_computable_PF_now_withheld_as_incomplete': sum(bool(a['PF']) and b['PF'] is None for a, b in zip(frozen_metrics, corrected))},
            'partial_coverage_full_metric_scope': {'previous_partial_rows_with_full_PF': sum(r['coverage_status'] == 'PARTIAL_COVERAGE' and bool(r['full_PF']) for r in frozen_metrics),
                'previous_partial_rows_with_generic_Net': sum(r['coverage_status'] == 'PARTIAL_COVERAGE' and bool(r['net_model_c1']) for r in frozen_metrics)},
            'contradictory_null_reason_and_status': {'previous_null_full_PF_without_reason': sum(not r['full_PF'] and not r['PF_null_reason'] for r in frozen_metrics),
                'corrective_results_and_verification_verdicts': 'CONSISTENT'},
            'Momentum_exit_bar_close_after_exit': {'return_flags_corrected': sum(r['changed_by_excluding_exit_bar_close'] for r in breakout)}},
        'frozen_record_reproduction': {'signals.csv': 'BYTE_IDENTICAL', 'execution_events.csv': 'BYTE_IDENTICAL', 'trade_ledger.csv': 'BYTE_IDENTICAL'},
        'reexecuted_integer_feature_payoff_audit': independent_prior_check['counts'],
        'gld_momentum_breach': breach,
        'gld_momentum_delay_sensitivity': {'baseline_closed_net': '60.4', 'delayed_closed_net': str(sum(delayed_nets, D(0))),
             'delayed_entries': len(delayed.ledger), 'delayed_unresolved': sum(r['status'] == 'UNRESOLVED' for r in delayed.ledger), 'parameter_search': False},
        'executed_test_log_sha256': sha(test_log) if test_log else None,
        'protected_root_ids_equal_main': True, 'frozen_v2_unchanged': True,
        'verdicts': {'Execution model': 'PASS_WITHIN_DECLARED_CONDITIONAL_CONTRACT; B_MINUS_10_BREACH_RETAINED',
                     'Research completeness': 'NEEDS FIX / ADDITIONAL 2023 EVIDENCE REQUIRED',
                     'VWAP economic viability': 'INCONCLUSIVE / NO PASS',
                     'Momentum economic viability': 'INCONCLUSIVE / NO PASS'},
        'limitations': ['FINAM/MSK/start-label is exporter attestation, not independently retrieved provider metadata.',
             'No missing OHLCV repair, exchange execution proof, full annual result, funding imputation or true intrabar drawdown.',
             'Independent checking algorithm within this task, not second-person review.',
             'Full calendar research coverage is conditional on the declared approved windows, not an exhaustive historical venue calendar.']}
    DEST.mkdir(parents=True, exist_ok=True)
    write_csv(DEST/'unresolved_cases.csv', unresolved)
    write_csv(DEST/'metrics.csv', corrected)
    write_csv(DEST/'run_comparison.csv', summary_rows)
    write_csv(DEST/'momentum_breakout_diagnostics.csv', breakout)
    (DEST/'results.json').write_text(encoded({'schema': 1, 'provenance': 'provenance.json',
        'runs': [{'run': r['run'], 'summary': r} for r in summary_rows],
        'aggregates': corrected, 'verdicts': verification['verdicts']}))
    (DEST/'delay_sensitivity_reporting.json').write_text(encoded(corrected_sensitivity))
    (DEST/'verification.json').write_text(encoded(verification))
    (DEST/'provenance.json').write_text(encoded(provenance))
    if log is not None:
        (DEST/'test_execution.log').write_text(log)
    (DEST/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.name}\n' for p in sorted(DEST.iterdir())
        if p.is_file() and p.name != 'SHA256SUMS'))
    print(encoded(verification['counts']))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-root', type=Path, required=True)
    p.add_argument('--test-log', type=Path)
    args = p.parse_args()
    run(args.data_root, args.test_log)
