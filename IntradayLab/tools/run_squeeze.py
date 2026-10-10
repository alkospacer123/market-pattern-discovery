#!/usr/bin/env python3
"""Exact 16 preregistered replays; fresh outputs, immutable 2023 byte budgets."""
import argparse
from collections import Counter
import csv
from datetime import datetime, timedelta
from decimal import Decimal, localcontext
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess

from session_mtf import Bar
from squeeze_replay import Replay, windows, allowed, FIVE, ZERO, tick

LAB = Path(__file__).resolve().parents[1]
CONFIG = LAB/'config/stage2_squeeze_v1.json'
D = Decimal


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(obj):
    return json.dumps(obj, default=str, sort_keys=True, ensure_ascii=False, indent=2)+'\n'


def read_inputs(root, manifest):
    assert git(root, 'rev-parse', 'HEAD') == manifest['source_ref']
    assert not git(root, 'status', '--porcelain=v1', '--untracked-files=all')
    result, provenance = {}, {}
    for symbol, spec in sorted(manifest['inputs'].items()):
        assert git(root, 'ls-files', '--stage', '--', spec['path']).split()[1] == spec['blob']
        path = root/spec['path']
        before = path.stat()
        with path.open('rb', buffering=0) as f:
            raw = f.read(spec['prefix_bytes'])
        assert len(raw) == spec['prefix_bytes'] and raw.endswith(b'\n') and sha(raw) == spec['prefix_sha256']
        rows = raw.decode('utf-8-sig').splitlines()
        assert rows[0] == 'Ticker;Datetime;Open;High;Low;Close;Volume'
        assert len(rows) == spec['rows_2023']+1
        bars = []
        for line in rows[1:]:
            parts = line.split(';')
            at = datetime.fromisoformat(parts[1])
            assert at.year == 2023 and parts[0] == symbol  # before price parsing
            o, h, l, c, v = map(D, parts[2:])
            assert l <= min(o, c) <= max(o, c) <= h and v >= 0
            assert all(p % tick(symbol, at) == 0 for p in (o, h, l, c))
            bars.append(Bar(at, o, h, l, c, v, symbol=symbol))
        assert len({b.timestamp for b in bars}) == len(bars)
        assert [b.timestamp for b in bars] == sorted(b.timestamp for b in bars)
        assert path.stat() == before
        result[symbol] = bars
        provenance[symbol] = dict(rows=len(bars), first=bars[0].timestamp, last=bars[-1].timestamp,
                                  prefix_bytes_read=len(raw), prefix_sha256=sha(raw), frozen_blob=spec['blob'],
                                  bytes_2024_plus_read=0, bytes_2025_plus_read=0)
    return result, provenance


def write_csv(path, rows):
    fields = list(dict.fromkeys(k for r in rows for k in r))
    buf = io.StringIO(newline='')
    writer = csv.DictWriter(buf, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    raw = buf.getvalue().encode()
    path.write_bytes(gzip.compress(raw, mtime=0) if path.suffix == '.gz' else raw)


def coverage(bars):
    first = bars[0].timestamp
    index = {b.timestamp for b in bars if allowed(b.symbol, b.timestamp) and b.volume > 0}
    months, days = {}, {}
    for m in range(1, 13):
        day = datetime(2023, m, 1)
        expected = set()
        while day.month == m and day.year == 2023:
            for a, z in windows(day.date()):
                t = a
                slots = set()
                while t+FIVE <= z:
                    slots.add(t)
                    t += FIVE
                expected |= slots
                if day.date() >= first.date():
                    rec = days.setdefault(day.date(), dict(expected=0, observed=0))
                    rec['expected'] += len(slots)
                    rec['observed'] += len(slots & index)
            day += timedelta(days=1)
        observed = expected & index
        missing = {t for t in expected-index if t >= first}
        status = ('NO_COVERAGE' if m < first.month else 'PARTIAL_LAUNCH' if any(t < first for t in expected)
                  else 'PARTIAL_DATA' if missing else 'COVERED')
        months[f'2023-{m:02d}'] = dict(coverage_status=status, expected_slots=len(expected), observed_slots=len(observed),
                                        missing_since_inception=len(missing), pre_inception_slots=sum(t < first for t in expected))
    return months, days


def payoff(rows, multiplier=1):
    with localcontext() as ctx:
        ctx.prec = 34
        known = [r for r in rows if r['status'] == 'CLOSED']
        unknown = [r for r in rows if r['status'] != 'CLOSED']
        nets = [r['gross']-multiplier*r['c1'] for r in known]
        wins, losses = [n for n in nets if n > 0], [n for n in nets if n < 0]
        pos, neg = sum(wins, ZERO), -sum(losses, ZERO)
        gross = sum((r['gross'] for r in known), ZERO)
        cost = sum((multiplier*r['c1'] for r in known), ZERO)
        rs = [n/r['initial_risk'] for n, r in zip(nets, known)]
        avg_win = pos/len(wins) if wins else None
        avg_loss = neg/len(losses) if losses else None
        gw = [r['gross'] for r in known if r['gross'] > 0]
        gl = [-r['gross'] for r in known if r['gross'] < 0]
        running = peak = dd = ZERO
        peak_at = min((r['entry_at'] for r in known), default=None)
        recovery_minutes = 0
        ordered = sorted(known, key=lambda r: (r['exit_ack'], r['signal_id']))
        for r in ordered:
            running += r['gross']-multiplier*r['c1']
            if running >= peak:
                peak, peak_at = running, r['exit_ack']
            elif peak_at:
                recovery_minutes = max(recovery_minutes, int((r['exit_ack']-peak_at).total_seconds()/60))
            dd = max(dd, peak-running)
        top = sorted(wins, reverse=True)
        return dict(entries=len(rows), closed=len(known), unknown=len(unknown),
                    closed_gross=gross, closed_cost=cost, closed_net=gross-cost,
                    closed_net_PF=pos/neg if neg else None, PF_status='DEFINED' if neg else 'NO_LOSSES' if wins else 'NO_TRADES',
                    closed_expectancy=(gross-cost)/len(known) if known else None,
                    closed_win_rate=D(len(wins))/len(known) if known else None,
                    average_net_win=avg_win, average_net_loss=avg_loss,
                    realized_net_win_loss_RR=avg_win/avg_loss if avg_win is not None and avg_loss else None,
                    realized_gross_win_loss_RR=(sum(gw, ZERO)/len(gw))/(sum(gl, ZERO)/len(gl)) if gw and gl else None,
                    closed_net_R=sum(rs, ZERO), mean_net_R=sum(rs, ZERO)/len(rs) if rs else None,
                    closed_realized_DD=dd if known else None, closed_unrecovered_minutes=recovery_minutes,
                    largest_winner_share=top[0]/pos if top and pos else None,
                    top3_winner_share=sum(top[:3], ZERO)/pos if pos else None,
                    top5_winner_share=sum(top[:5], ZERO)/pos if pos else None,
                    closed_net_without_top1=gross-cost-(top[0] if top else ZERO),
                    known_entry_cost_unknown=sum((multiplier*r['c1_entry'] for r in unknown), ZERO),
                    full_net=None if unknown else gross-cost,
                    full_PF=None if unknown else pos/neg if neg else None,
                    full_DD=None if unknown else dd if known else None)


def summarise(replay, cov, days):
    base = dict(architecture=replay.architecture, instrument=replay.symbol, scenario=f'T{replay.delay}')
    p = payoff(replay.ledger)
    complete = all(c['coverage_status'] == 'COVERED' for c in cov.values()) and not p['unknown']
    if not complete:
        p.update(full_net=None, full_PF=None, full_DD=None)
    reason_counts = Counter(r['reason'] for r in replay.signals if r['status'] != 'MODELLED')
    exit_counts = Counter(r['exit_reason'] for r in replay.ledger)
    result = base | p | dict(metric_scope='COMPLETE_CALENDAR' if complete else 'CLOSED_ONLY_DIAGNOSTIC',
        raw_squeeze_episodes=len(replay.cycles.rows), confirmed_squeeze_episodes=sum(e['bars'] >= 3 for e in replay.cycles.rows),
        confirmed_signals=len(replay.signals), model_orders=sum(e['kind'] == 'ENTRY_ORDER' for e in replay.events),
        rejected_signals=sum(s['status'] == 'FILTERED' for s in replay.signals),
        nonfills=sum(s['status'] in ('NONFILL', 'NO_BAR_NO_MODEL_FILL') for s in replay.signals),
        rejection_reasons=json.dumps(dict(sorted(reason_counts.items())), sort_keys=True),
        exit_counts=json.dumps(dict(sorted(exit_counts.items())), sort_keys=True),
        reached_1R=sum(r['mfe_R'] >= 1 for r in replay.ledger), reached_2R=sum(r['mfe_R'] >= 2 for r in replay.ledger),
        reached_3R=sum(r['mfe_R'] >= 3 for r in replay.ledger), takes=exit_counts['TAKE'],
        realized_net_3R=sum(r['status'] == 'CLOSED' and r['net_R'] >= 3 for r in replay.ledger),
        early_potential_winners=sum(r['status'] == 'CLOSED' and r['exit_reason'] != 'TAKE' and r['mfe_R'] >= 1 for r in replay.ledger),
        flat_reserve_breaches=sum(r['flat_target_breach'] for r in replay.ledger),
        planned_min_net_RR=min((r['planned_net_RR'] for r in replay.ledger), default=None),
        mean_initial_risk=sum((r['initial_risk'] for r in replay.ledger), ZERO)/len(replay.ledger) if replay.ledger else None,
        mean_target_atr=sum((r['target_atr'] for r in replay.ledger), ZERO)/len(replay.ledger) if replay.ledger else None,
        long_entries=sum(r['direction'] == 'LONG' for r in replay.ledger), short_entries=sum(r['direction'] == 'SHORT' for r in replay.ledger),
        eligible_calendar_days=len(days), observed_days=sum(d['observed'] > 0 for d in days.values()),
        trades_per_expected_day=D(len(replay.ledger))/len(days),
        trades_per_observed_day=D(len(replay.ledger))/sum(d['observed'] > 0 for d in days.values()))
    monthly, directions = [], []
    for direction in ('LONG', 'SHORT'):
        q = payoff([r for r in replay.ledger if r['direction'] == direction])
        if not complete:
            q.update(full_net=None, full_PF=None, full_DD=None)
        directions.append(base | dict(direction=direction, metric_scope=result['metric_scope']) | q)
    streak = longest = 0
    for period, c in cov.items():
        rows = [r for r in replay.ledger if r['entry_at'].strftime('%Y-%m') == period]
        q = payoff(rows)
        sign = ('NO_COVERAGE' if c['coverage_status'] == 'NO_COVERAGE' else 'UNKNOWN' if q['unknown']
                else 'NO_TRADES' if not rows else 'POSITIVE' if q['closed_net'] > 0 else 'NEGATIVE' if q['closed_net'] < 0 else 'ZERO_NET')
        if c['coverage_status'] != 'COVERED' or q['unknown']:
            q.update(full_net=None, full_PF=None, full_DD=None)
        if c['coverage_status'] == 'NO_COVERAGE':
            q = {k: None if k not in ('entries', 'closed', 'unknown', 'PF_status') else v for k, v in q.items()}
        long = payoff([r for r in rows if r['direction'] == 'LONG'])
        short = payoff([r for r in rows if r['direction'] == 'SHORT'])
        rec = base | dict(period=period) | q | c | dict(month_status=sign, sign_scope='CONFIRMED_CALENDAR' if c['coverage_status'] == 'COVERED' and not q['unknown'] else 'CLOSED_SUBSET_ONLY',
            long_entries=long['entries'], short_entries=short['entries'], long_closed_net=long['closed_net'] if c['coverage_status'] != 'NO_COVERAGE' else None,
            short_closed_net=short['closed_net'] if c['coverage_status'] != 'NO_COVERAGE' else None)
        monthly.append(rec)
        streak = streak+1 if sign == 'NEGATIVE' else 0
        longest = max(longest, streak)
    nonempty = [x for x in monthly if x['closed']]
    result.update(positive_closed_months=sum(x['closed_net'] is not None and x['closed_net'] > 0 for x in monthly),
                  negative_closed_months=sum(x['closed_net'] is not None and x['closed_net'] < 0 for x in monthly),
                  zero_trade_months=sum(x['month_status'] == 'NO_TRADES' for x in monthly),
                  no_coverage_months=sum(x['coverage_status'] == 'NO_COVERAGE' for x in monthly),
                  unknown_months=sum(x['unknown'] > 0 for x in monthly),
                  confirmed_positive_months=sum(x['month_status'] == 'POSITIVE' and x['sign_scope'] == 'CONFIRMED_CALENDAR' for x in monthly),
                  confirmed_negative_months=sum(x['month_status'] == 'NEGATIVE' and x['sign_scope'] == 'CONFIRMED_CALENDAR' for x in monthly),
                  best_closed_month=max(nonempty, key=lambda x: x['closed_net'])['period'] if nonempty else None,
                  worst_closed_month=min(nonempty, key=lambda x: x['closed_net'])['period'] if nonempty else None,
                  longest_known_negative_month_streak=longest,
                  trades_per_available_month=D(len(replay.ledger))/sum(x['coverage_status'] != 'NO_COVERAGE' for x in monthly))
    return result, monthly, directions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), 'Fresh output only; retain prior runs'
    raw = CONFIG.read_bytes()
    assert sha(raw) == CONFIG.with_suffix('.sha256').read_text().split()[0]
    manifest = json.loads(raw)
    assert manifest['architectures'] == ['SQUEEZE_M5', 'SQUEEZE_M30_M5'] and manifest['scenarios'] == [10, 15]
    bars, provenance = read_inputs(args.data_root, manifest)
    args.output.mkdir(parents=True)
    metrics, monthly, directions, frequencies, sensitivity = [], [], [], [], []
    tables = {name: [] for name in ('signals', 'execution_events', 'trade_ledger', 'squeeze_cycles', 'indicator_features')}
    results = {}
    with localcontext() as ctx:
        ctx.prec = 34
        for symbol, b in bars.items():
            cov, days = coverage(b)
            for architecture in manifest['architectures']:
                for delay in manifest['scenarios']:
                    replay = Replay(symbol, architecture, delay).run(b)
                    base = dict(architecture=architecture, instrument=symbol, scenario=f'T{delay}')
                    summary, mr, dr = summarise(replay, cov, days)
                    metrics.append(summary)
                    monthly += mr
                    directions += dr
                    results[symbol, architecture, delay] = replay
                    for name, rows in (('signals', replay.signals), ('execution_events', replay.events), ('trade_ledger', replay.ledger), ('squeeze_cycles', replay.cycles.rows)):
                        tables[name] += [base | r for r in rows]
                    if architecture == 'SQUEEZE_M5' and delay == 10:
                        tables['indicator_features'] += [dict(instrument=symbol) | r for r in replay.features]
                    day_counts = Counter(r['entry_at'].date() for r in replay.ledger)
                    week_counts, week_days = Counter(), Counter()
                    for day, c in days.items():
                        week = f'{day.isocalendar().year}-W{day.isocalendar().week:02d}'
                        week_counts[week] += day_counts[day]
                        week_days[week] += 1
                        frequencies.append(base | dict(period=str(day), frequency='DAY', entries=day_counts[day], observed_slots=c['observed'], expected_slots=c['expected'], no_trade=day_counts[day] == 0, data_absent=c['observed'] == 0))
                    for week, count in sorted(week_counts.items()):
                        frequencies.append(base | dict(period=week, frequency='WEEK', entries=count, eligible_days=week_days[week]))
                    for m in mr:
                        frequencies.append(base | dict(period=m['period'], frequency='MONTH', entries=m['entries'] if m['coverage_status'] != 'NO_COVERAGE' else None, coverage_status=m['coverage_status']))
                    summary['observed_no_trade_days'] = sum(c['observed'] > 0 and day_counts[day] == 0 for day, c in days.items())
                    for multiplier in (1, 2):
                        q = payoff(replay.ledger, multiplier)
                        if summary['metric_scope'] != 'COMPLETE_CALENDAR':
                            q.update(full_net=None, full_PF=None, full_DD=None)
                        sensitivity.append(base | dict(cost=f'C{multiplier}', metric_scope=summary['metric_scope']) | q)
    comparisons = []
    for symbol in bars:
        for delay in manifest['scenarios']:
            a, b = (results[symbol, architecture, delay] for architecture in manifest['architectures'])
            ai, bi = {r['signal_id'] for r in a.ledger}, {r['signal_id'] for r in b.ledger}
            x, y = payoff(a.ledger), payoff(b.ledger)
            comparisons.append(dict(instrument=symbol, scenario=f'T{delay}', m5_entries=len(ai), m30_entries=len(bi), retained_entries=len(ai & bi), removed_entries=len(ai-bi), freed_entries=len(bi-ai),
                                    m5_closed_net=x['closed_net'], m30_closed_net=y['closed_net'], m5_closed_PF=x['closed_net_PF'], m30_closed_PF=y['closed_net_PF'],
                                    m5_unknown=x['unknown'], m30_unknown=y['unknown'], scope='CLOSED_ONLY_DIAGNOSTIC'))
    for name, rows in tables.items():
        write_csv(args.output/f'{name}.csv.gz', rows)
    for name, rows in (('metrics', metrics), ('monthly_results', monthly), ('direction_results', directions), ('frequency_report', frequencies), ('sensitivity', sensitivity), ('m5_m30_comparison', comparisons)):
        write_csv(args.output/f'{name}.csv', rows)
    (args.output/'input_provenance.json').write_text(encoded(dict(config_sha256=sha(raw), inputs=provenance, source_ref=manifest['source_ref'], preregistration_commit='bc47fc5', run_count=len(metrics), market_time='MSK UTC+3 / start timestamp', protected_years_bytes_read=0,
                                                               implementation_sha256={p.name: sha(p.read_bytes()) for p in (Path(__file__), LAB/'tools/squeeze_replay.py')})))
    (args.output/'SHA256SUMS').write_text(''.join(f'{sha(p.read_bytes())}  {p.name}\n' for p in sorted(args.output.iterdir()) if p.name != 'SHA256SUMS'))
    print(f'Completed {len(metrics)} predeclared runs; output {args.output}')


if __name__ == '__main__':
    main()
