#!/usr/bin/env python3
"""Read-only Stage 2 research-acceptance audit, NOT a strategy/backtest runner.

Reads only IntradayLab's frozen 2023 M5 derived artifacts. Never opens
market-pattern-data, 2024 WF or 2025+ TRUE OOS. Never emits a PASS verdict.
"""
import csv
import hashlib
import json
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

LAB = Path(__file__).resolve().parents[1]
BASE = LAB / 'results' / 'stage2_m5'
VERDICT = 'STAGE2_M5_BASELINE_NEEDS_FIX_RESEARCH_COMPLETENESS'
SYMBOLS = ('USDRUBF', 'CNYRUBF', 'GLDRUBF', 'IMOEXF')
STRATEGIES = ('VWAP_MR', 'MOMENTUM')
EXPECTED = {f'{st}_{sy}' for st in STRATEGIES for sy in SYMBOLS}
MONTHS = [f'2023-{i:02d}' for i in range(1, 13)]


def assess(result, verification, signal_rows, manifest_hash):
    """Fail closed on provenance/count/accounting inconsistencies."""
    if result['manifest_sha256'] != manifest_hash or verification['manifest_sha256'] != manifest_hash:
        raise ValueError('FROZEN_MANIFEST_HASH_MISMATCH')
    runs = result['runs']
    if len(runs) != 8 or {r['run'] for r in runs} != EXPECTED:
        raise ValueError('INVALID_FROZEN_RUN_MATRIX')
    if verification['matrix_runs'] != 8 or verification['signals'] != sum(r['signals'] for r in runs):
        raise ValueError('RUN_OR_SIGNAL_COUNT_MISMATCH')

    rows = defaultdict(list)
    for sig in signal_rows:
        run, at, status = sig['run'], sig['signal_at'], sig['status']
        if run not in EXPECTED or at[:7] not in MONTHS:
            raise ValueError('UNDECLARED_RUN_OR_PERIOD')
        rows[run].append(sig)

    details = []
    monthly = []
    total_blocked = total_unknown = total_unresolved = 0
    for r in sorted(runs, key=lambda x: x['run']):
        run, summary = r['run'], r['summary']
        observed = Counter(row['status'] for row in rows[run])
        if len(rows[run]) != r['signals'] or dict(observed) != r['signal_status_counts']:
            raise ValueError('SIGNAL_LEDGER_COUNT_MISMATCH:' + run)
        if set(r['coverage']) != set(MONTHS):
            raise ValueError('MISSING_CALENDAR_MONTHS:' + run)
        unknown = int(summary['unknown_entry_orders'])
        unresolved = int(summary['unresolved'])
        gross = summary['closed_only_gross']
        cost = summary['closed_only_c1']
        net = summary['closed_only_net_c1']
        if net is not None and Decimal(gross) - Decimal(cost) != Decimal(net):
            raise ValueError('C1_ACCOUNTING_MISMATCH:' + run)
        if unknown + unresolved != int(summary['total_unresolved_cases']):
            raise ValueError('UNRESOLVED_COUNT_MISMATCH:' + run)
        if (unknown or unresolved) and (summary['full_PF'] is not None or summary['net_model_c1'] is not None):
            raise ValueError('UNPROVEN_ANNUAL_PNL_OR_PF:' + run)
        total_blocked += observed['BLOCKED']
        total_unknown += unknown
        total_unresolved += unresolved
        details.append({
            'run': run, 'signals': len(rows[run]), 'blocked': observed['BLOCKED'],
            'closed_accounted': summary['closed_accounted_trades'],
            'unresolved_trades': unresolved, 'unknown_entry_orders': unknown,
            'closed_only_net_C1_price_units': net,
            'closed_only_PF': summary['PF'],
            'full_annual_net_C1': summary['net_model_c1'],
            'full_annual_PF': summary['full_PF'],
            'classification': 'INCOMPLETE' if unknown or unresolved else 'PENDING_RESEARCH_REVIEW',
        })
        for month in MONTHS:
            c = r['coverage'][month]
            statuses = Counter(s['status'] for s in rows[run] if s['signal_at'].startswith(month))
            mark = r.get('month_end_model_marks', {}).get(month)
            if c['coverage_status'] == 'NO_COVERAGE':
                month_pnl = 'NO_COVERAGE'
            elif mark and mark.get('net_complete') and mark.get('model_flat_confirmed'):
                month_pnl = 'PROVISIONAL_COMPLETE_MTM_REQUIRES_REVIEW'
            else:
                month_pnl = 'UNRESOLVED_OR_UNPROVEN'
            monthly.append({
                'run': run, 'month': month, 'coverage': c['coverage_status'],
                'expected_slots': c['expected_research_slots'], 'missing_slots': c['missing_slots'],
                'signals': sum(statuses.values()), 'blocked': statuses['BLOCKED'],
                'modelled_entries': statuses['MODELLED'],
                'unknown_entry_orders': statuses['UNRESOLVED_POSSIBLE_ENTRY_FILL'],
                'research_PnL_status': month_pnl,
            })
    if total_blocked != verification['blocked_signals'] or total_unknown != verification['unknown_entry_orders'] or total_unknown+total_unresolved != verification['total_unresolved_cases']:
        raise ValueError('GLOBAL_VERIFICATION_MISMATCH')
    # A complete replay would still need independent performance, cost and monthly stability review.
    return {
        'verdict': VERDICT if total_unknown or total_unresolved else 'PENDING_INDEPENDENT_RESEARCH_REVIEW',
        'economic_baseline_complete': False,
        'reason': 'UNKNOWN_EXECUTION_OR_OPEN_LIABILITY' if total_unknown or total_unresolved else 'REQUIRES_INDEPENDENT_RESEARCH_REVIEW',
        'scope': 'Derived 2023 M5 signals/results only; no market or protected-year source accessed',
        'total_signals': sum(r['signals'] for r in runs),
        'blocked_signals': total_blocked,
        'blocked_percent': str((Decimal(total_blocked)*100/Decimal(sum(r['signals'] for r in runs))).quantize(Decimal('0.01'))),
        'unknown_entry_orders': total_unknown,
        'unresolved_trades': total_unresolved,
        'runs': details, 'run_months': monthly,
        'notes': ['Closed-only PF is NOT annual performance',
                  'NO_COVERAGE is not a zero-trade month',
                  'BLOCKED signals are not executable trade fills',
                  'Do not clear unknown orders without independent execution evidence',
                  'No strategy settings are modified or ranked'],
    }


def main():
    config_bytes = (LAB / 'config' / 'stage2_m5_baseline_v1.json').read_bytes()
    manifest_hash = hashlib.sha256(config_bytes).hexdigest()
    expected_hash = (LAB / 'config' / 'stage2_m5_baseline_v1.sha256').read_text().split()[0]
    if manifest_hash != expected_hash:
        raise ValueError('MANIFEST_CHANGED_SINCE_BASELINE')
    result = json.loads((BASE / 'results.json').read_text())
    verification = json.loads((BASE / 'verification.json').read_text())
    with (BASE / 'signals.csv').open(newline='') as f:
        out = assess(result, verification, csv.DictReader(f), manifest_hash)
    print(json.dumps(out, sort_keys=True, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
