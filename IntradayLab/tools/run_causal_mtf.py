"""Predeclared bounded 2023 M5/derived-MTF replays; separate frozen outputs."""
import argparse
from collections import Counter
import csv
from datetime import datetime, timedelta
from decimal import Decimal as D
import gzip
import hashlib
import io
import json
from pathlib import Path

from causal_mtf import DerivedContext, MTFGate
from m5_conditional_v2 import Replay, window_at, next_slot, ZERO
from stage2_architecture_replay import ArchitectureReplay
from stage2_vwap_payable_cap import PayableCapReplay
from stage2_architecture_analysis import LAB, indicator_maps, attribution, diagnostics
from run_stage2_architectures import metric_groups, frequency, pairs, checksums
from run_m5_baseline import inputs, csv_text
from independent_corrective_review import coverage, encoded, sha, write_csv

CONFIG = LAB / 'config/stage2_causal_mtf_v1.json'
DEST = LAB / 'results/stage2_causal_mtf_v1'
CODE = ('tools/causal_mtf.py', 'tools/audit_causal_mtf.py', 'tools/run_causal_mtf.py',
        'tests/test_causal_mtf.py')


class MTFFrozen(MTFGate, Replay):
    pass


class MTFArchitecture(MTFGate, ArchitectureReplay):
    pass


class MTFPayable(MTFGate, PayableCapReplay):
    pass


def load():
    manifest = json.loads(CONFIG.read_text())
    assert sha(CONFIG) == CONFIG.with_suffix('.sha256').read_text().split()[0]
    parent = json.loads((LAB / 'config/stage2_complete_architectures_v1.json').read_text())
    for field in ('inputs', 'parameters', 'defaults', 'source_ref', 'run_matrix'):
        assert manifest[field] == parent[field], field
    return manifest


def preserved():
    preflight = json.loads((DEST / 'preflight.json').read_text())
    for path, digest in preflight['retained_files_sha256'].items():
        if path in ('IntradayLab/ROADMAP.md', 'IntradayLab/PROJECT_CONTEXT.md'):
            continue
        assert sha(LAB.parent / path) == digest, path
    return preflight['retained_files_sha256']


def freeze(root):
    manifest = load()
    assert not (DEST / 'results.json').exists(), 'Cannot freeze after returns'
    readiness = json.loads((DEST / 'readiness.json').read_text())
    assert readiness['status'] == 'PASS_DERIVED_M5_CONTEXT', 'Stop MTF, failed contract'
    _, provenance = inputs(root, manifest)
    payload = {'state': 'FROZEN_BEFORE_MTF_RETURNS', 'manifest_sha256': sha(CONFIG),
               'implementation_sha256': {name: sha(LAB / name) for name in CODE},
               'readiness_sha256': sha(DEST / 'readiness.json'), 'inputs': provenance,
               'retained_files_sha256': preserved()}
    path = DEST / 'input_provenance.json'
    if path.exists():
        assert json.loads(path.read_text()) == json.loads(encoded(payload))
    path.write_text(encoded(payload))
    print('FROZEN', payload['manifest_sha256'])


def make_replay(symbol, strategy, params, base, defaults, context):
    if base == 'FROZEN_V2':
        replay = (MTFFrozen if context else Replay)(symbol, strategy, params)
    elif strategy == 'VWAP_MR':
        replay = (MTFPayable if context else PayableCapReplay)(symbol, params, base, defaults)
    else:
        replay = (MTFArchitecture if context else ArchitectureReplay)(symbol, strategy, params, base, defaults)
    if context:
        replay.mtf_context = context
    return replay


def serialize(rows):
    fields = list(dict.fromkeys(k for row in rows for k in row))
    return list(csv.DictReader(io.StringIO(csv_text(rows, fields))))


def verify_comparator(replay, base, scenario):
    from audit_stage2_architectures import rows
    folder = LAB / 'results' / ('stage2_vwap_payable_cap_v1' if base.startswith('PAYABLE') else 'stage2_complete_architectures_v1')
    for filename, attr in (('signals.csv', 'signals'), ('execution_events.csv', 'events'), ('trade_ledger.csv', 'ledger')):
        frozen = [r for r in rows(folder / filename) if r['architecture'] == base and r['scenario'] == scenario and r['run'] == f'{replay.strategy}_{replay.symbol}']
        current = serialize(getattr(replay, attr))
        assert len(current) == len(frozen), (base, scenario, filename)
        for a, b in zip(current, frozen):
            # Frozen multi-architecture CSVs have a union schema: fields absent
            # from this parent replay are represented by empty CSV cells.
            assert all(a.get(k, '') == v for k, v in b.items() if k not in ('architecture', 'scenario')), (base, scenario, filename)
    return 'EXACT_FROZEN_SIGNAL_EVENT_LEDGER_FIELDS'


def excursions(row, index, delay):
    # Supersede inherited nominal t+10 observable diagnostic with actual clock.
    row['mfe_observable_before_exit_lower_bound_R'] = None
    row['mfe_actionable_before_exit_lower_bound_R'] = None
    row['observable_clock_basis'] = 'actual scenario delivery < exit; next strict future protection slot < exit; terminal excluded'
    if row['net_model_c1'] is None:
        return row
    start, end = map(datetime.fromisoformat, (row['entry_interval_start'], row['exit_interval_start']))
    d = row['direction_sign'] if 'direction_sign' in row else (1 if row['direction'] == 'LONG' else -1)
    observable = actionable = ZERO
    while start < end:
        b = index[start]
        value = d * ((b.high if d == 1 else b.low) - row['entry']) / row['initial_risk_price_units']
        release = start + timedelta(minutes=delay)
        if release < end:
            observable = max(observable, value)
        if next_slot(release) < end:
            actionable = max(actionable, value)
        start += timedelta(minutes=5)
    row.update(mfe_observable_before_exit_lower_bound_R=observable,
               mfe_actionable_before_exit_lower_bound_R=actionable)
    return row


def run(root, output):
    m = load()
    frozen = json.loads((DEST / 'input_provenance.json').read_text())
    assert frozen['manifest_sha256'] == sha(CONFIG)
    assert frozen['implementation_sha256'] == {name: sha(LAB / name) for name in CODE}
    assert frozen['readiness_sha256'] == sha(DEST / 'readiness.json')
    preserved()
    data, provenance = inputs(root, m)
    assert provenance == frozen['inputs']
    indexes = {s: {b.timestamp: b for b in bars} for s, bars in data.items()}
    cov = coverage({s: {at: b.ohlcv for at, b in idx.items()} for s, idx in indexes.items()})
    indicators = indicator_maps(data)
    output.mkdir(parents=True, exist_ok=True)
    tables = {name: [] for name in ('signals', 'execution_events', 'trade_ledger', 'metrics',
              'trade_attribution', 'stop_amendments', 'paired_contribution', 'daily_frequency')}
    summaries, verification = [], []
    for item in m['run_matrix']:
        symbol, strategy = item['instrument'], item['strategy']
        for scenario, delay in (('C1_T10', 10), ('C1_T15_DELAY', 15)):
            params = m['parameters'] | {'availability_minutes': delay}
            contexts = {minutes: DerivedContext(data[symbol], minutes, params) for minutes in (15, 30, 60)}
            references = {}
            for variant in m['variants'][strategy]:
                base, tf, minutes = variant['base'], variant['tf'], variant['minutes']
                name = base + '__' + tf
                replay = make_replay(symbol, strategy, params, base, m['defaults'], contexts.get(minutes)).run(data[symbol])
                if tf == 'NONE':
                    verification.append({'run': f'{strategy}_{symbol}', 'variant': name, 'scenario': scenario,
                                         'status': verify_comparator(replay, base, scenario)})
                    references[base] = replay
                meta = {'architecture': name, 'base_architecture': base, 'context_tf': tf,
                        'mtf_minutes': minutes, 'scenario': scenario}
                for table, attr in (('signals', 'signals'), ('execution_events', 'events'), ('trade_ledger', 'ledger')):
                    tables[table] += [r | meta for r in getattr(replay, attr)]
                metrics = metric_groups(replay, {k: v for k, v in cov.items() if k[0] == symbol}, name, scenario)
                for r in metrics:
                    r.update(meta, full_economic_verdict='PENDING_FINAL_JOINT_ASSESSMENT')
                tables['metrics'] += metrics
                summaries.append(metrics[0] | {'signal_counts': dict(Counter(s['status'] for s in replay.signals)),
                       'signals': len(replay.signals), 'filter_reasons': dict(Counter(s['reason'] for s in replay.signals if s['status'] == 'FILTERED')),
                       'execution_counts': replay.counts})
                smap = {s['signal_id']: s for s in replay.signals}
                tables['trade_attribution'] += [excursions(attribution(r, smap[r['signal_id']], indexes[symbol], indicators[symbol]), indexes[symbol], delay) | meta for r in replay.ledger]
                tables['stop_amendments'] += [r | meta | {'run': f'{strategy}_{symbol}'} for r in getattr(replay, 'amendments', [])]
                tables['daily_frequency'] += [r | meta for r in frequency(replay, name, scenario, data[symbol])]
                if tf != 'NONE':
                    tables['paired_contribution'] += [r | meta for r in pairs(references[base], replay, base + '__NONE', name)]
                print(symbol, strategy, scenario, name, len(replay.ledger), metrics[0]['unresolved'], metrics[0]['closed_only_net_c1'], flush=True)
    for name, records in tables.items():
        write_csv(output / (name + '.csv'), records)
    write_csv(output / 'pnl_segments.csv', [r | {'architecture': name, 'scenario': scenario} for name, scenario in sorted({(r['architecture'], r['scenario']) for r in tables['trade_attribution']})
               for r in diagnostics([a for a in tables['trade_attribution'] if a['architecture'] == name and a['scenario'] == scenario])])
    (output / 'results.json').write_text(encoded({'manifest_sha256': sha(CONFIG), 'runs': summaries,
        'comparators': verification, 'MTF': 'DERIVED_M5_ONLY; NATIVE_DELIVERY_STILL_BLOCKED',
        'original_unknowns': '82 unchanged frozen outcomes; candidates have separate cohorts, no recovery',
        'unit': 'Per-instrument normalized quote units; never aggregate unlike instruments as capital P&L',
        'scope': 'All available 2023, 128 fixed runs incl. 64 T15; Stage 3 and next strategy unstarted'}))
    checksums(output)
    preserved()


def pack(output):
    files = {}
    for path in sorted(output.glob('*.csv')):
        if path.stat().st_size < 200000:
            continue
        raw = path.read_bytes()
        dest = Path(str(path) + '.gz')
        with dest.open('wb') as f:
            with gzip.GzipFile(filename='', mode='wb', compresslevel=9, fileobj=f, mtime=0) as zipped:
                zipped.write(raw)
        files[path.name] = {'sha256_uncompressed': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
        path.unlink()
    (output / 'packaging.json').write_text(encoded(files))
    checksums(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('command', choices=['freeze', 'run', 'pack'])
    p.add_argument('--data-root', type=Path)
    p.add_argument('--output', type=Path, default=DEST)
    a = p.parse_args()
    if a.command == 'freeze':
        freeze(a.data_root)
    elif a.command == 'run':
        run(a.data_root, a.output)
    else:
        pack(a.output)
