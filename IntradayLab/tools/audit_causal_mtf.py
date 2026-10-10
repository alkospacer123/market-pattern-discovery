"""Independent aggregation/clock and artifact audit, without Replay calls.

Native prices validate composition only. The read budget ends at the final
2023 LF; later years are not read. Unknown position paths are not revisited.
"""
import argparse
from collections import Counter
import csv
from datetime import datetime, timedelta
from decimal import Decimal as D
import hashlib
import json
from pathlib import Path

from independent_corrective_review import exact_lines, git, encoded, independent_tick, intervals
from run_m5_baseline import inputs
from audit_stage2_architectures import audit as path_audit, rows, key
from stage2_architecture_analysis import LAB
from causal_mtf import DerivedContext


def independent_pair(index, minutes, now, session, delay):
    """Separate backwards clock scan; no production parent/selector helpers."""
    duration = timedelta(minutes=minutes)
    latest = now - timedelta(minutes=minutes - 5 + delay)
    latest = latest.replace(second=0, microsecond=0)
    latest -= timedelta(minutes=(latest.hour * 60 + latest.minute) % minutes)
    starts = (latest - duration, latest)
    if starts[0] < session[0] or starts[1] + duration > session[1]:
        return None
    groups = []
    releases = []
    for at in starts:
        ts = [at + timedelta(minutes=5 * i) for i in range(minutes // 5)]
        if any(t not in index for t in ts):
            return None
        children = [index[t] for t in ts]
        for b in children:
            release = max(b.timestamp + timedelta(minutes=delay), b.available_at or b.timestamp)
            if release.second or release.microsecond or release.minute % 5:
                release = release.replace(second=0, microsecond=0) - timedelta(minutes=release.minute % 5) + timedelta(minutes=5)
            releases.append(release)
        groups.append((children[0].open, max(b.high for b in children), min(b.low for b in children), children[-1].close, sum((b.volume for b in children), D(0))))
    if max(releases) > now:
        return None
    ao, _, _, ac, _ = groups[0]
    bo, _, _, bc, _ = groups[1]
    direction = 1 if ac > ao and bc > bo and bc > ac else -1 if ac < ao and bc < bo and bc < ac else 0
    return starts, max(releases), direction


def native_check(root, symbol, minutes, index, production):
    tf = {15: 'M15', 30: 'M30', 60: 'H1'}[minutes]
    historic = json.loads((LAB / 'reports/STAGE1_2_SESSION_MTF_RESULTS.json').read_text())
    spec = historic['coverage'][symbol][tf]
    rel = f'forever/{symbol}/{symbol}_{tf}.csv'
    assert git(root, 'ls-files', '--stage', '--', rel).split()[1] == spec['frozen_blob_id']
    count, skip = spec['year_rows']['2023'], spec['year_rows'].get('2022', 0)
    parents, digest, read_bytes, skipped_bytes = {}, hashlib.sha256(), 0, 0
    stat = (root / rel).stat()
    with (root / rel).open('rb', buffering=0) as raw:
        for i, line in enumerate(exact_lines(raw, 1 + skip + count)):
            if i == 0:
                assert line.decode('utf-8-sig').strip() == 'Ticker;Datetime;Open;High;Low;Close;Volume'
            elif i <= skip:
                assert line.split(b';', 2)[1].startswith(b'2022-')
                skipped_bytes += len(line)
                continue
            else:
                fields = next(csv.reader([line.decode()], delimiter=';'))
                at = datetime.fromisoformat(fields[1])
                assert at.year == 2023 and fields[0] == symbol
                assert at not in parents
                parents[at] = tuple(map(D, fields[2:]))
            digest.update(line)
            read_bytes += len(line)
    after = (root / rel).stat()
    assert (stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns) == (after.st_size, after.st_mtime_ns, after.st_ctime_ns)
    counts = Counter()
    # Independently reconstruct child lists from each native label.
    for at, native in parents.items():
        session = next((w for w in intervals(at.date()) if w[0] <= at < w[1]), None)
        if session is None or at + timedelta(minutes=minutes) > session[1]:
            counts['outside_or_crosses_window'] += 1
            continue
        times = [at + timedelta(minutes=5 * j) for j in range(minutes // 5)]
        if any(t not in index for t in times):
            counts['incomplete_children'] += 1
            continue
        children = [index[t] for t in times]
        aggregate = (children[0].open, max(b.high for b in children), min(b.low for b in children), children[-1].close, sum((b.volume for b in children), D(0)))
        counts['exact' if aggregate == native else 'mismatch'] += 1
        assert production.cells[at].ohlcv == aggregate
        assert production.cells[at].available_at == times[-1] + timedelta(minutes=10)
    for at, parent in production.cells.items():
        if parent is not None and at not in parents:
            counts['complete_without_native_parent'] += 1
    passed = counts['exact'] > 0 and counts['mismatch'] == 0 and counts['complete_without_native_parent'] == 0
    return {'status': 'PASS_DERIVED_ONLY' if passed else 'MTF_BLOCKED', 'counts': dict(counts),
            'native_rows_2023': count, 'source_blob': spec['frozen_blob_id'],
            'header_plus_2023_sha256': digest.hexdigest(), 'header_plus_2023_bytes': read_bytes,
            'skipped_2022_rows_not_parsed': skip, 'skipped_2022_bytes': skipped_bytes,
            'bytes_2024_plus_read': 0, 'bytes_2025_plus_read': 0,
            'native_delivery': 'STILL_UNPROVED_AND_BLOCKED'}


def readiness(root, manifest):
    data, provenance = inputs(root, manifest)
    result, clocks = {}, Counter()
    for symbol, bars in data.items():
        index = {b.timestamp: b for b in bars}
        result[symbol] = {}
        for minutes in (15, 30, 60):
            production = DerivedContext(bars, minutes, manifest['parameters'])
            result[symbol][str(minutes)] = native_check(root, symbol, minutes, index, production)
            for delay in (10, 15):
                contexts = production if delay == 10 else DerivedContext(bars, minutes, manifest['parameters'] | {'availability_minutes': delay})
                for day in sorted({b.timestamp.date() for b in bars}):
                    for session in intervals(day):
                        now = session[0]
                        while now < session[1]:
                            own = independent_pair(index, minutes, now, session, delay)
                            pair, reason = contexts.pair(now, session)
                            assert (pair is None) == (own is None), (symbol, minutes, delay, now, reason)
                            if own is not None:
                                starts, release, direction = own
                                assert (pair[0].start, pair[1].start) == starts
                                rec = contexts.describe(now, session, 1, 'MOMENTUM')
                                assert datetime.fromisoformat(rec['mtf_available_at']) == release <= now
                                assert rec['mtf_direction'] == direction
                            clocks['independent_M5_decision_clocks_checked'] += 1
                            now += timedelta(minutes=5)
    passed = all(v['status'] == 'PASS_DERIVED_ONLY' for tfs in result.values() for v in tfs.values())
    return {'status': 'PASS_DERIVED_M5_CONTEXT' if passed else 'MTF_BLOCKED', 'composition': result,
            'clock_checks': dict(clocks), 'inputs': provenance,
            'contract': 'M15 T+20 / M30 T+35 / H1 T+65, max actual child delivery; T15 stress adds 5m',
            'scope': 'Distinct conditional research hypothesis, NOT native FINAM delivery proof'}


def artifact_audit(root, folder, manifest):
    data, provenance = inputs(root, manifest)
    index = {s: {b.timestamp: b for b in bars} for s, bars in data.items()}
    counts = Counter()
    signals = rows(folder / 'signals.csv')
    bykey = {key(s): s for s in signals}
    for s in signals:
        if not s['mtf_minutes']:
            continue
        symbol = s['instrument']
        delay = 10 if s['scenario'] == 'C1_T10' else 15
        now = datetime.fromisoformat(s['available_at'])
        at = datetime.fromisoformat(s['signal_at'])
        session = next(w for w in intervals(at.date()) if w[0] <= at < w[1])
        own = independent_pair(index[symbol], int(s['mtf_minutes']), now, session, delay)
        if own is None:
            assert s['mtf_gate_eligible'] == 'False' and not s['mtf_available_at']
        else:
            starts, release, trend = own
            assert tuple(datetime.fromisoformat(s[k]) for k in ('mtf_first_start', 'mtf_last_start')) == starts
            assert datetime.fromisoformat(s['mtf_available_at']) == release <= now
            assert int(s['mtf_direction']) == trend
            direction = int(s['direction_sign'])
            eligible = trend == direction if s['strategy'] == 'MOMENTUM' else trend != -direction
            assert s['mtf_gate_eligible'] == str(eligible)
        counts['MTF_signal_contexts_checked'] += 1
    for r in rows(folder / 'trade_ledger.csv'):
        if r['mtf_minutes']:
            s = bykey[key(r)]
            assert s['mtf_gate_eligible'] == 'True'
            assert datetime.fromisoformat(s['mtf_available_at']) <= datetime.fromisoformat(s['available_at']) < datetime.fromisoformat(r['entry_interval_start'])
            counts['MTF_entry_admissions_checked'] += 1
    # Map variant labels to their immutable M5 parents for the established
    # independent payoff/path checker. Production strategy code is not called.
    import tempfile
    from independent_corrective_review import write_csv
    with tempfile.TemporaryDirectory(dir=LAB / 'results', prefix='.mtf_audit_') as tmp:
        auditdir = Path(tmp)
        for filename in ('signals.csv', 'execution_events.csv', 'trade_ledger.csv', 'metrics.csv', 'stop_amendments.csv'):
            records = rows(folder / filename)
            for r in records:
                r['architecture'] = r['base_architecture'] + '::' + r['context_tf']
            # Checker needs parent architecture flags as well as unique cohorts:
            # audit each TF separately below, so labels can remain immutable.
            write_csv(auditdir / filename, records)
        details = []
        for tf in ('NONE', 'M15', 'M30', 'H1'):
            dest = auditdir / tf
            dest.mkdir()
            for filename in ('signals.csv', 'execution_events.csv', 'trade_ledger.csv', 'metrics.csv', 'stop_amendments.csv'):
                records = [r for r in rows(folder / filename) if r['context_tf'] == tf]
                for r in records:
                    r['architecture'] = r['base_architecture']
                if records:
                    write_csv(dest / filename, records)
                elif filename == 'stop_amendments.csv':
                    (dest / filename).write_text('architecture,scenario,run,signal_id,effective_at,decided_at,stop,state\n')
            if (dest / 'trade_ledger.csv').exists():
                (dest / 'results.json').write_text('{}\n')
                details.append(path_audit(root, [dest]))
    return {'status': 'PASS_INDEPENDENT_CONTEXT_AND_KNOWN_PATH_AUDIT', 'counts': dict(counts),
            'path_checks': [d['counts'] for d in details], 'inputs': provenance,
            'limits': 'Independent algorithm, not external economic acceptance; unknown paths never recovered'}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('command', choices=['readiness', 'artifacts'])
    p.add_argument('--data-root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--folder', type=Path)
    args = p.parse_args()
    manifest = json.loads((LAB / 'config/stage2_causal_mtf_v1.json').read_text())
    result = readiness(args.data_root, manifest) if args.command == 'readiness' else artifact_audit(args.data_root, args.folder, manifest)
    args.output.write_text(encoded(result))
    print(result['status'], result.get('clock_checks', result.get('counts')))
