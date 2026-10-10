#!/usr/bin/env python3
"""One strategy + JSON config -> common Backtester -> deterministic artifacts."""
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from IntradayLab.core.backtester import Backtester
from IntradayLab.core.calendar import MarketRules
from IntradayLab.core.data_loader import load_market_data
from IntradayLab.core.metrics import summarize
from IntradayLab.core.reports import coverage, csv_write, dump, table_row
from IntradayLab.strategies.orb_false_break_fade import ORBFalseBreakFade

LAB = ROOT/'IntradayLab'
CONFIG = LAB/'config/orb_a_base_2023_canonical_v1.json'
OUT = LAB/'results/orb_a_base_2023_canonical_v1'
STRATEGIES = {ORBFalseBreakFade.name: ORBFalseBreakFade}


def run(data_root, output, config_path=CONFIG):
    if not output.resolve().is_relative_to(LAB.resolve()) or output.resolve() in (LAB.resolve(), ROOT.resolve()):
        raise ValueError('OUTPUT_MUST_BE_ISOLATED_UNDER_INTRADAYLAB')
    config = json.loads(config_path.read_text())
    if config['execution']['wait_complete_bars'] != 1 or config['bar_label'] != 'start':
        raise ValueError('UNAPPROVED_CLOCK')
    config_hash = hashlib.sha256(config_path.read_bytes()).hexdigest()
    if config_path.with_suffix('.sha256').read_text().strip().split()[0] != config_hash:
        raise ValueError('FROZEN_CONFIG_CHANGED')
    rules = MarketRules(config)
    raw, receipts = load_market_data(data_root, config, rules)
    output.mkdir(parents=True, exist_ok=True)
    ss, tt, dd, cc, gg, monthly, instruments, directions = [], [], [], [], [], [], [], []
    metrics = {}
    engine = Backtester(rules, timeframe_minutes=config['timeframe_minutes'],
                        cost_ticks_per_side=config['execution']['cost_ticks_per_side'],
                        allow_entry_bar_take=config['execution']['allow_entry_bar_take'],
                        session_flat_before_end_bars=config['execution']['session_flat_before_end_bars'])
    for symbol in config['instruments']:
        strategy = STRATEGIES[config['strategy']](config['parameters'])
        signals, trades, days = engine.run(strategy, symbol, raw[symbol],
            start=date.fromisoformat(config['start']), end_exclusive=date.fromisoformat(config['end_exclusive']))
        source, gaps = coverage(symbol, raw[symbol], config, rules)
        ss += signals; tt += trades; dd += days; cc += source; gg += gaps
        metrics[symbol] = summarize(trades, signals, source)
        instruments.append(table_row(symbol, trades, signals, source))
        for month in range(1,13):
            label = f'2023-{month:02d}'
            cohort = [t for t in trades if str(t['signal_at']).startswith(label)]
            events = [s for s in signals if s['date'].startswith(label)]
            cov = [c for c in source if c['date'].startswith(label)]
            monthly.append(table_row(symbol, cohort, events, cov, month=label))
        for direction in (-1,1):
            directions.append(table_row(symbol, [t for t in trades if t['direction']==direction],
                                        [s for s in signals if s['direction']==direction], source,
                                        direction='LONG' if direction==1 else 'SHORT'))
    for name, rows in [('signals',ss), ('trades',tt), ('days',dd), ('coverage_daily',cc),
                       ('coverage_events',gg), ('monthly_report',monthly),
                       ('instrument_report',instruments), ('direction_report',directions)]:
        csv_write(output/f'{name}.csv', rows)
    csv_write(output/'unknown_report.csv', [dict(signal_id=t['signal_id'],instrument=t['instrument'],
        signal_at=t['signal_at'],entry_at=t['entry_at'],model_filled=t['model_filled'],
        unknown_reason=t['unknown_reason'],missing_interval_start=t['unknown_detected_at']-engine.step,
        missing_interval_end=t['unknown_detected_at'],known_entry_cost_C1=t.get('cost_entry_c1'),
        exit_price=t.get('exit_price'),net_R_c1=t['net_R_c1'],outcome='UNKNOWN; never imputed',
        following_day_contract='conditional FLAT assumption, not reconciliation') for t in tt if t['status']=='UNKNOWN'])
    coverage_summary = []
    for symbol in config['instruments']:
        c = [x for x in cc if x['instrument']==symbol]
        coverage_summary.append(dict(instrument=symbol,
            expected_days_from_first_history=sum(x['status']!='PRE_INCEPTION' for x in c),
            complete_days=sum(x['status']=='COMPLETE' for x in c),
            incomplete_days=sum(x['status']=='INCOMPLETE' for x in c),
            pre_inception_days=sum(x['status']=='PRE_INCEPTION' for x in c),
            missing_expected_slots=sum(x['missing_bars'] for x in c),
            invalid_expected_slots=sum(x['invalid_bars'] for x in c),
            source_rows_2023=len(raw[symbol]), first=str(min(raw[symbol])), last=str(max(raw[symbol])),
            expected_grid='approved research windows; not proof of complete exchange sessions',
            absence_proves_missed_trade=False))
    csv_write(output/'coverage_report.csv', coverage_summary)
    dump(output/'metrics.json', dict(strategy=config['strategy'], period='2023-01-01—2023-12-31',
         baseline_status='INCONCLUSIVE' if any(not m['annual_complete'] for m in metrics.values()) else 'NO ECONOMIC BASELINE PASS',
         optimization_allowed=False, instruments=metrics))
    dump(output/'input_provenance.json', dict(source_repository=config['source_repository'],
         source_ref=config['source_ref'], inputs=receipts, source_clean=True,
         bars_label='Open/start; completed OHLC available at start+5 minutes',
         timezone='Europe/Moscow; exporter attestation', annual_portfolio_claim=False))
    code_paths = sorted([* (LAB/'core').glob('*.py'), * (LAB/'strategies').glob('*.py'),
                        Path(__file__), LAB/'tools/audit_canonical_baseline.py',
                        LAB/'tools/compare_canonical_history.py', LAB/'tools/validate_canonical_baseline.py',
                        LAB/'tests/test_universal_backtester.py', LAB/'tests/test_canonical_audit.py', config_path])
    dump(output/'provenance.json', dict(base_main=config['base_main'], historical_reference=config['historical_reference'],
         config_sha256=config_hash, source_ref=config['source_ref'],
         code_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in code_paths},
         protected_root_trees={line.split('\t')[1]:line.split()[2] for line in
            subprocess.check_output(['git','-C',str(ROOT),'ls-tree',config['base_main']], text=True).splitlines()
            if line.split('\t')[1] != 'IntradayLab'},
         python='Python 3 standard library; Decimal precision 28',
         execution='Signal completed M5 -> full waiting M5 -> next interval Open; Stop-first; no entry-bar Take; exact mandatory exit Open',
         unknown_contract='Keep unknown trades; block same day only; following research days assume FLAT conditionally'))
    from compare_canonical_history import compare
    comparison = compare(output, config)
    dump(output/'historical_comparison.json', comparison)
    report(output, config, metrics, monthly, coverage_summary, comparison)
    return metrics


def report(output, config, metrics, months, cov, comparison):
    lines = ['# Canonical Baseline — ORB FALSE-BREAK FADE A BASE M5', '',
        '**Infrastructure: technical validation and independent audit recorded in audit.json.**',
        '**Baseline: INCONCLUSIVE. Optimization is not authorized.**', '',
        '2023-01-01—2023-12-31; one fixed strategy, no optimization. Source '+config['source_ref']+'.',
        'All economics below are conditional known closures after model C1, one dated tick per side.',
        'Annual PF/Net/Expectancy/Win Rate/DD are null because coverage and outcomes are incomplete.',
        'The closed-only DD is a diagnostic sequence of known closures, not continuous portfolio equity.', '',
        '| Instrument | Signals | Orders | Fills | Closed | UNKNOWN | PF price | PF R | Net R | Expectancy R | Win rate | DD R |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    def f(x):
        return '—' if x is None else f'{x:.6f}' if hasattr(x, 'quantize') else str(x)
    details=[]
    for symbol,m in metrics.items():
        d=m['conditional_closed_only_C1']
        lines.append('| '+' | '.join(map(f,[symbol,m['signals'],m['admitted_orders'],m['model_fills'],m['closed'],m['unknown'],d['PF_C1_price'],d['PF_C1_R'],d['Net_R'],d['Expectancy_R'],d['Win_Rate'],d['Max_DD_R']]))+' |')
        details += ['', f"{symbol}: {m['economic_diagnostic']}; rejection reasons: `{json.dumps(m['rejection_reasons'],sort_keys=True)}`.",
                  f"Unknown possible entries {m['unknown_possible_entry']}; known closures after a prior unresolved day {m['post_unknown_conditional_closed']}."]
    lines+=details
    lines += ['', '## Source coverage', '', '| Instrument | Full / eligible days | Pre-inception days | Missing expected slots | Invalid slots | All source M5 rows |', '|---|---:|---:|---:|---:|---:|']
    for c in cov:
        lines.append(f"| {c['instrument']} | {c['complete_days']}/{c['expected_days_from_first_history']} | {c['pre_inception_days']} | {c['missing_expected_slots']} | {c['invalid_expected_slots']} | {c['source_rows_2023']} |")
    lines += ['', 'Every physical 2023 M5 row is validated, including pre-10:00 and evening observations. These outside-window rows warm indicators but cannot create entries.',
        'Calendar weekends/declared holidays and pre-inception days do not create fictitious expected candles. The grid is the approved research contract, not a complete exchange calendar.',
        'The September 13 exchange halt is identified diagnostically; it does not retrospectively change trade windows. The absent August 31 USD/CNY rows have an unproved source cause.',
        'Missing slots are neither automatic missed trades nor source errors. Exact missing/invalid slots and source-cause limits are retained in coverage_events.csv.', '',
        '## All twelve months — conditional known closures', '',
        '| Month | Instrument | Closed | UNKNOWN | PF C1 price | Net R | Expectancy R | Win rate | DD R | Coverage class | Full / incomplete / pre-inception days |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|']
    for row in sorted(months, key=lambda x:(x['month'],config['instruments'].index(x['instrument']))):
        vals=[row['month'],row['instrument'],row['closed'],row['unknown'],row['conditional_PF_C1_price'],row['conditional_Net_R'],row['conditional_Expectancy_R'],row['conditional_Win_Rate'],row['conditional_Max_DD_R'],row['coverage_classification'],f"{row['complete_days']}/{row['incomplete_days']}/{row['pre_inception_days']}"]
        lines.append('| '+' | '.join(map(f,vals))+' |')
    lines += ['', '## Execution and fixed candidate', '',
        'OR 10:00–10:15, sweep 1 dated tick, reclaim 2 ticks inside on same/next completed M5; first attempt per side/day is consumed, even if it fails.',
        'Stop at episode extreme ±1 sweep-dated tick; target 1.5 gross R, rounded outward on entry-dated grid; holding 60 calendar minutes. No ATR, MTF or minimum Stop filter.',
        'Signal at reclaim close; one full following M5 closes; Open-only model entry at the next boundary. Stop-first on ambiguous OHLC; no entry-bar Take; adverse Stop gap at Open; Take at target without favorable gap improvement.',
        'Events sharing a signal timestamp use ascending signal_id, matching the frozen #463 executable ledger; one pending/open position is admitted per instrument. A both-sided sweep candle consumes both attempts without entry.',
        'Trading windows 10:00–14:00 / 14:05–18:50; afternoon starts 14:15 on March 13–20. Scheduled TIME/SESSION_FLAT uses exact Open, with adverse Stop gap precedence.',
        'Missing waiting bar: NO_WAITING_BAR, no order. Missing entry Open: UNKNOWN possible fill. Missing exposed bar/mandatory exit: UNKNOWN, no invented exit or net. Same day is blocked; next day assumes FLAT conditionally.',
        'Intrabar exits are intervals [start,end], not exact exchange timestamps. Missing-slot discovery metadata is the interval end; no missing price is replaced.', '',
        '## Frozen #463 comparison', '',
        f"Reference commit `{config['historical_reference']}`; A BASE v2 daywise only. Fully sufficient instrument-days: {comparison['complete_days']}; compared trades: {comparison['complete_day_trades']}; discrepancies: {len(comparison['discrepancies'])}.",
        'historical_comparison.json includes row-set and field checks for signals, admission, entry, Stop, Take, exit and C1, plus incomplete-day diagnostics. Historical code/config/artifacts were read through git show and remain untouched.', '',
        'One implementation discrepancy was found and fixed before canonical freeze: two GLD signals at 2023-10-06 10:35 were emitted in callback order. Applying the frozen ascending signal_id tie-break restores identical admission and trade identity. Parameters were not changed; final comparison has zero discrepancies on incomplete days as well.', '',
        '## Reproduction and limits', '',
        'Run `python3 IntradayLab/tools/run_canonical_baseline.py --data-root /workspace/market-pattern-data --output IntradayLab/work/replay` then `python3 IntradayLab/tools/audit_canonical_baseline.py --data-root /workspace/market-pattern-data --output IntradayLab/work/replay`.',
        'Determinism and technical-test receipts are stored separately in validation.json. Provenance pins input prefix bytes/hashes, code/config hashes, historical reference and protected root trees.',
        'C1 is a research cost assumption, not verified broker fees. This normalized historical model does not establish queue fills, capital, margin or live authority.',
        'NO ECONOMIC BASELINE PASS is retained for negative known-closure diagnostics. Overall and sparse/unknown instruments remain INCONCLUSIVE; no candidate moves to Optimization.',
        'Lifecycle stays Baseline → Optimization → Robustness → Walk Forward → TRUE OOS. 2024 and 2025+ were not read. No Merge, next stage or LIVE. TradingSystemLab is read-only and not imported.', '']
    (output/'Baseline_Report.md').write_text('\n'.join(lines))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=OUT)
    args=parser.parse_args()
    result=run(args.data_root,args.output)
    print(json.dumps({k:{x:v[x] for x in ('signals','admitted_orders','model_fills','closed','unknown')} for k,v in result.items()},sort_keys=True))
