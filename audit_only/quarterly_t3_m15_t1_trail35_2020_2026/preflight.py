"""Read-only, offline source gate. This module does not implement a replay.

The only outputs are receipts, missing-source coverage and NOT_RUN statuses.
No OHLC values or placeholder trade/statistical CSVs are written.
"""
import argparse
import csv
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MAIN = '38489db7e69336548a583f968f13aab49c20913b'
DATA = 'f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8'
H1 = 'd9a3a13cf5df69ca10d91b05f283ffaad641cb00'
MARKETS = ('Si', 'CNY', 'GD', 'MIX', 'BR', 'NG')
N4 = {
    'USDRUBF': 'fef80630080a4e2a5e968d620b663f51acd1b7ab9d5d326a42c68cf2b80c67b8',
    'CNYRUBF': '259298733d1528c0d917b100118896009519a9f08bdad33d4b373d9ce86f99b4',
    'GLDRUBF': '7381d672485b5687ca2c4d92aa5960c24bb132f527589bae3c622b2dfa20a83d',
    'IMOEXF': 'a1b9fa6102a955103d61b28e81533ed19de68117e30fd84ceb53e8e617559773',
}
STATUS = {
    'DATA_ACQUISITION': 'BLOCKED', 'SOURCE_INTEGRITY': 'INCOMPLETE',
    'FROZEN_STRATEGY_REPLICATION': 'NOT_RUN', 'COMPUTATIONAL_AUDIT': 'NOT_RUN',
    'EXPLORATORY_REPLAY': 'NOT_RUN', 'ROLL_PROVENANCE': 'UNVERIFIED',
    'TRADABLE_QUARTERLY_PERFORMANCE': 'NOT_VALIDATED',
    'ECONOMIC_CONCLUSION': 'INCONCLUSIVE',
}


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args])


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n')


def receipt(repo, relative, ref):
    p = repo / relative
    expected = git(repo, 'rev-parse', ref + ':' + relative).decode().strip()
    actual = git(repo, 'hash-object', '--no-filters', str(p)).decode().strip()
    if expected != actual:
        raise RuntimeError('SOURCE_BYTES_CHANGED: ' + relative)
    return dict(path=relative, bytes=p.stat().st_size, sha256=digest(p),
                git_blob_sha=expected, matches_pinned_git_blob=True)


def inventory_csv(repo, relative, role):
    result = receipt(repo, relative, DATA)
    result['role'] = role
    n = 0
    first = last = None
    tickers, periods = set(), set()
    with (repo / relative).open(newline='') as f:
        for row in csv.DictReader(f, delimiter=';'):
            n += 1
            at = row.get('Datetime') or (row.get('<DATE>', '') + ' ' + row.get('<TIME>', ''))
            first = first or at
            last = at
            if '<TICKER>' in row:
                tickers.add(row['<TICKER>'])
                periods.add(row['<PER>'])
    result.update(rows=n, first_timestamp_as_stored=first, last_timestamp_as_stored=last)
    if tickers:
        result.update(observed_tickers=sorted(tickers), observed_periods=sorted(periods),
                      eligible_for_quarterly_replay=False,
                      exclusion_reason='PERPETUAL_TICKER_NOT_TARGET_DATED_FUTURE')
    return result


def coverage(repo):
    rows = []
    for s in MARKETS:
        rel = f'futures_quarterly/{s}/{s}_M15.csv'
        if (repo / rel).exists():
            # New files require a new pilot and explicit provenance review;
            # presence alone must never silently clear the blocked gate.
            raise RuntimeError('NEW_M15_REQUIRES_PILOT_AND_IDENTITY_REVIEW: ' + rel)
        for year in range(2020, 2027):
            rows.append(dict(instrument=s, year=year, required_path=rel,
                             state='NO_DATA', m15_candles=None,
                             explanation='Required M15 source absent; not a zero-trade result',
                             year_is_complete=False if year == 2026 else None))
    return rows


def collect(data):
    if git(data, 'rev-parse', 'HEAD').decode().strip() != DATA:
        raise RuntimeError('DATA_HEAD_NOT_PINNED')
    if git(data, 'status', '--porcelain').strip():
        raise RuntimeError('DATA_WORKTREE_DIRTY')
    candles = []
    for s in MARKETS:
        for tf in ('H1', 'M30'):
            candles.append(inventory_csv(data, f'futures_quarterly/{s}/{s}_{tf}.csv',
                                         'REFERENCE_ONLY_NOT_M15'))
    for s, expected in N4.items():
        r = inventory_csv(data, f'forever/{s}/{s}_M15.csv', 'FROZEN_N4_CONTROL_ONLY')
        if r['sha256'] != expected:
            raise RuntimeError('FROZEN_N4_HASH_MISMATCH: ' + s)
        r['matches_frozen_518_sha256'] = True
        candles.append(r)
    legacy = git(data, 'ls-tree', '-r', '--name-only', DATA, '2026/').decode().splitlines()
    for rel in sorted(p for p in legacy if '_M15_' in p and p.endswith('.csv')):
        r = inventory_csv(data, rel, 'LEGACY_FILENAME_IDENTITY_CHECK')
        if not set(r.get('observed_tickers', [])).issubset(N4) or not r.get('observed_tickers'):
            raise RuntimeError('LEGACY_SOURCE_IDENTITY_REQUIRES_REVIEW: ' + rel)
        candles.append(r)
    frozen_paths = ['IntradayLab/SELECTED_T3_M15_SESSION_T1_R15.md']
    for folder in ('t3_m15_t1_entry_retest_v1', 't3_m15_execution_sensitivity_v1'):
        prefix = 'IntradayLab/' + folder + '/'
        paths = git(ROOT, 'ls-tree', '-r', '--name-only', MAIN, prefix).decode().splitlines()
        frozen_paths += [p for p in paths if p.endswith('.py') or
                         Path(p).name in ('SPEC.json', 'FREEZE.json', 'REPORT_RU.md', 'PROTOCOL.md')]
    frozen = [receipt(ROOT, p, MAIN) for p in sorted(set(frozen_paths))]
    published = receipt(ROOT, 'IntradayLab/t3_m15_t1_entry_retest_v1/results/comparison_summary.csv', MAIN)
    with (ROOT / published['path']).open() as f:
        control = next(r for r in csv.DictReader(f) if r['model'] == 'T1_NEXT_OPEN_TRAIL_3p5')
    h1_receipts = []
    for name in ('summary.json', 'REPORT_RU.md', 'DATA_AUDIT.md'):
        rel = 'audit_only/quarterly_t3_h1_trail1_2020_2026/' + name
        b = git(ROOT, 'show', H1 + ':' + rel)
        h1_receipts.append(dict(path=rel, ref=H1, bytes=len(b), sha256=hashlib.sha256(b).hexdigest()))
    return dict(schema_version=1, research_main=MAIN, data_commit=DATA,
                frozen_model='T1_NEXT_OPEN_TRAIL_3p5', input_files=candles,
                frozen_research_files=frozen, published_control_receipt=published,
                published_control_metrics=control, control_metrics_origin='READ_PUBLISHED_NOT_RECOMPUTED',
                h1_555_reference_receipts=h1_receipts, target_m15_source_files=[],
                alor_network_evidence=receipt_additional_evidence('ALOR_NETWORK_PROBE.json'),
                downloaded_raw_fragments=[], quarterly_m15_identity='NOT_ESTABLISHED',
                roll_provenance='UNVERIFIED', raw_ohlcv_published=False)


def receipt_additional_evidence(name):
    path = HERE / name
    return dict(path=name, sha256=digest(path),
                result=json.loads(path.read_text()).get('result')) if path.exists() else None


def run(data, out):
    data = data.resolve()
    out = out.resolve()
    if out == data or data in out.parents:
        raise RuntimeError('OUTPUT_MUST_NOT_BE_INSIDE_SOURCE_DATA')
    if out == ROOT or (ROOT in out.parents and out != HERE):
        raise RuntimeError('OUTPUT_OUTSIDE_AUTHORIZED_RESEARCH_DIRECTORY')
    manifest = collect(data)
    missing = coverage(data)
    out.mkdir(parents=True, exist_ok=True)
    write(out / 'SOURCE_MANIFEST.json', manifest)
    write(out / 'source_coverage.json', missing)
    write(out / 'summary.json', dict(STATUS, overall_status='SOURCE_DATA_BLOCKED_M15',
          model='T1_NEXT_OPEN_TRAIL_3p5', downloaded_m15_candles=0,
          quarterly_closed_trades=None, gross_R=None, gross_PF=None,
          reason='EXECUTOR_PROXY_CONNECT_403; required dated-futures M15 absent',
          alor_acquisition='PROXY_CONNECT_403_BEFORE_PROVIDER',
          alor_live_api_verified=False, windows_downloader='download_quarterly_m15_alor.py',
          clean_true_oos=False, capital_model='NOT_RUN',
          continuation='Resume same study after legal data delivery or network setup; rerun pilot first'))
    checks = [
        'Frozen source identity', 'Frozen configuration identity', 'Causal H1 publication',
        'No look-ahead', 'Donchian shift(1)', 'NEXT_OPEN adjacency', 'Pending cancellation',
        'Initial Stop from execution price', 'Immutable Initial R', 'Stop-first execution',
        'Adverse Open gaps', 'Trailing 3.5 ATR', 'No +1R TRAIL1', 'No pyramiding',
        'Cross-year continuity', 'Gross R/PF/DD arithmetic', 'Table reconciliation',
        'Missing versus zero periods', 'Perpetual comparison', 'H1 #555 comparison',
    ]
    write(out / 'independent_audit.json', dict(COMPUTATIONAL_AUDIT='NOT_RUN',
          historical_scalar_verification='NOT_RUN', full_replay_runs=0,
          source_gate_receipts='PASS', economic_interpretation_permitted=False,
          checks=[dict(check=x, status='NOT_RUN_ON_REAL_TARGET_M15',
                       reason='Source gate blocked') for x in checks],
          clarification='File/hash/status checks are not a strategy computational audit'))
    counts = Counter(r['role'] for r in manifest['input_files'])
    print(json.dumps(dict(status='SOURCE_DATA_BLOCKED_M15', source_receipts=dict(counts),
                          frozen_receipts=len(manifest['frozen_research_files']), replay_runs=0), sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--out', type=Path, default=HERE)
    args = parser.parse_args()
    run(args.data, args.out)
