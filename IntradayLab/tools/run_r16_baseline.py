#!/usr/bin/env python3
"""Frozen R16 config -> existing common engine/metrics -> separate reports."""
import argparse
from collections import Counter
from datetime import date
from decimal import Decimal
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
from IntradayLab.core.metrics import summarize, distribution_metrics, assess_baseline
from IntradayLab.core.reports import coverage, csv_write, dump, table_row
from IntradayLab.strategies.compression_breakout import CompressionBreakout

LAB = ROOT/'IntradayLab'
CONFIG = LAB/'config/r16_compression_breakout_2023_m5_v1.json'
OUT = LAB/'results/r16_compression_breakout_2023_m5_v1'
FREEZE = 'f0b908d3701c4fc140a4f66f4a689c3e3c2e5aee'


def assessed(trades, signals, source, config):
    m = summarize(trades, signals, source)
    m['distribution'] = distribution_metrics(trades)
    m['unknown_reasons'] = dict(sorted(Counter(t['unknown_reason'] for t in trades if t['status']=='UNKNOWN').items()))
    m.update(assess_baseline(m, m['distribution'], config['classification_policy']))
    return m


def row(symbol, trades, signals, source, config, **labels):
    r = table_row(symbol, trades, signals, source, **labels)
    m = assessed(trades, signals, source, config)
    r.update(status=m['status'], economic_diagnostic=m['economic_diagnostic'],
             evidence_checks=m['evidence_checks'])
    r.update({'conditional_'+k:v for k,v in m['distribution'].items()})
    return r


def run(data_root, output):
    if output.resolve()!=OUT.resolve() and not output.resolve().is_relative_to((LAB/'work').resolve()):
        raise ValueError('OUTPUT_MUST_BE_R16_RESULTS_OR_INTRADAYLAB_WORK')
    config = json.loads(CONFIG.read_text())
    digest = hashlib.sha256(CONFIG.read_bytes()).hexdigest()
    frozen = subprocess.check_output(['git','-C',str(ROOT),'show',FREEZE+':'+str(CONFIG.relative_to(ROOT))])
    if CONFIG.read_bytes() != frozen or CONFIG.with_suffix('.sha256').read_text().split()[0] != digest:
        raise ValueError('FROZEN_CONFIG_CHANGED')
    if config['execution']['wait_complete_bars'] != 1 or config['bar_label'] != 'start':
        raise ValueError('UNAPPROVED_CLOCK')
    rules = MarketRules(config)
    raw, receipts = load_market_data(data_root, config, rules)
    output.mkdir(parents=True, exist_ok=True)
    engine = Backtester(rules, timeframe_minutes=config['timeframe_minutes'],
        cost_ticks_per_side=config['execution']['cost_ticks_per_side'],
        allow_entry_bar_take=config['execution']['allow_entry_bar_take'],
        session_flat_before_end_bars=config['execution']['session_flat_before_end_bars'],
        daily_trade_deadline_clock=config['execution']['daily_trade_deadline_clock'])
    ss, tt, dd, cc, gg, monthly, instruments, directions, cov_summary = [], [], [], [], [], [], [], [], []
    metrics = {}
    for symbol in config['instruments']:
        signals, trades, days = engine.run(CompressionBreakout(config['parameters']),symbol,raw[symbol],
            start=date.fromisoformat(config['start']),end_exclusive=date.fromisoformat(config['end_exclusive']))
        source, gaps = coverage(symbol,raw[symbol],config,rules)
        ss.extend(signals); tt.extend(trades); dd.extend(days); cc.extend(source); gg.extend(gaps)
        metrics[symbol] = assessed(trades,signals,source,config)
        instruments.append(row(symbol,trades,signals,source,config))
        for month in range(1,13):
            label=f'2023-{month:02d}'
            monthly.append(row(symbol,[t for t in trades if str(t['signal_at']).startswith(label)],
                [s for s in signals if s['date'].startswith(label)],
                [c for c in source if c['date'].startswith(label)],config,month=label))
        for direction in (-1,1):
            directions.append(row(symbol,[t for t in trades if t['direction']==direction],
                [s for s in signals if s['direction']==direction],source,config,
                direction='LONG' if direction==1 else 'SHORT'))
        cov_summary.append(dict(instrument=symbol,source_rows_2023=len(raw[symbol]),
            first=str(min(raw[symbol])),last=str(max(raw[symbol])),
            complete_days=sum(c['status']=='COMPLETE' for c in source),
            incomplete_days=sum(c['status']=='INCOMPLETE' for c in source),
            pre_inception_days=sum(c['status']=='PRE_INCEPTION' for c in source),
            missing_expected_slots=sum(c['missing_bars'] for c in source),
            invalid_expected_slots=sum(c['invalid_bars'] for c in source),
            opening_slots_unavailable_days=sum(not c['or_available'] and c['status']!='PRE_INCEPTION' for c in source),
            expected_grid='approved IntradayLab calendar; conservative full research-window coverage',
            absence_proves_missed_trade=False))
    for name, data in [('signals',ss),('trades',tt),('days',dd),('coverage_daily',cc),
        ('coverage_events',gg),('monthly_report',monthly),('instrument_report',instruments),
        ('direction_report',directions),('coverage_summary',cov_summary)]:
        csv_write(output/f'{name}.csv',data)
    csv_write(output/'coverage_report.csv', [dict(instrument=s,month=f'2023-{month:02d}',
        complete_days=sum(c['status']=='COMPLETE' for c in cc if c['instrument']==s and c['date'].startswith(f'2023-{month:02d}')),
        incomplete_days=sum(c['status']=='INCOMPLETE' for c in cc if c['instrument']==s and c['date'].startswith(f'2023-{month:02d}')),
        pre_inception_days=sum(c['status']=='PRE_INCEPTION' for c in cc if c['instrument']==s and c['date'].startswith(f'2023-{month:02d}')),
        missing_bars=sum(c['missing_bars'] for c in cc if c['instrument']==s and c['date'].startswith(f'2023-{month:02d}')),
        invalid_bars=sum(c['invalid_bars'] for c in cc if c['instrument']==s and c['date'].startswith(f'2023-{month:02d}')),
        expected_bars=sum(c['expected_bars'] for c in cc if c['instrument']==s and c['date'].startswith(f'2023-{month:02d}')),
        valid_bars=sum(c['valid_bars'] for c in cc if c['instrument']==s and c['date'].startswith(f'2023-{month:02d}')),
        physical_source_rows=sum(at.strftime('%Y-%m')==f'2023-{month:02d}' for at in raw[s]),
        classification=next(r['coverage_classification'] for r in monthly if r['instrument']==s and r['month']==f'2023-{month:02d}'))
        for s in config['instruments'] for month in range(1,13)])
    csv_write(output/'unknown_report.csv',[dict(signal_id=t['signal_id'],instrument=t['instrument'],
        signal_at=t['signal_at'],entry_at=t['entry_at'],model_filled=t['model_filled'],
        unknown_reason=t['unknown_reason'],missing_interval_start=t['unknown_detected_at']-engine.step,
        missing_interval_end=t['unknown_detected_at'],known_entry_cost_C1=t.get('cost_entry_c1'),
        exit_price=t.get('exit_price'),net_R_c1=t['net_R_c1'],outcome='UNKNOWN; economics unassigned',
        following_day_contract='conditional FLAT assumption; broker FLAT unproven') for t in tt if t['status']=='UNKNOWN'])
    statuses=[m['status'] for m in metrics.values()]
    status=('INCONCLUSIVE' if 'INCONCLUSIVE' in statuses else 'ECONOMICALLY_PROMISING_BASELINE'
            if all(s=='ECONOMICALLY_PROMISING_BASELINE' for s in statuses) else 'NO ECONOMIC BASELINE PASS')
    document=dict(strategy=config['strategy'],period='2023-01-01—2023-12-31',baseline_status=status,
        overall_policy='Conservative four-instrument assessment: every declared instrument must supply sufficient complete evidence; per-instrument conditional diagnoses remain separate.',
        optimization_allowed=False,instruments=metrics,
        portfolio_money_return=None,portfolio_price_PF=None,continuous_portfolio_equity=None,
        no_cross_instrument_price_pooling=True)
    dump(output/'metrics.json',document)
    dump(output/'input_provenance.json',dict(source_repository=config['source_repository'],
        source_ref=config['source_ref'],source_clean=True,inputs=receipts,
        bytes_2024_plus_read=0,bytes_2025_plus_read=0,timezone=config['timezone'],bar_label='start'))
    code_paths=sorted([*(LAB/'core').glob('*.py'),LAB/'strategies/compression_breakout.py',
        Path(__file__),LAB/'tools/audit_r16_baseline.py',LAB/'tools/validate_r16_baseline.py',
        LAB/'tools/audit_canonical_baseline.py',LAB/'tests/test_r16_compression_breakout.py',LAB/'tests/test_r16_audit.py',CONFIG])
    dump(output/'provenance.json',dict(base_main=config['base_main'],config_freeze_commit=FREEZE,
        config_sha256=digest,config_frozen_before_first_PnL=True,historical_reference=config['historical_reference'],
        historical_selection=config['historical_selection'],M1_to_M5_adaptation=config['adaptation'],
        classification_policy=config['classification_policy'],source_ref=config['source_ref'],
        code_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in code_paths},
        protected_trees={line.split('\t')[1]:line.split()[2] for line in
            subprocess.check_output(['git','-C',str(ROOT),'ls-tree',config['base_main']],text=True).splitlines()
            if line.split('\t')[1]!='IntradayLab'},python='Python standard library; Decimal precision 28',
        independent_day_contract='Following UNKNOWN day assumes FLAT conditionally, never broker reconciliation',
        parameters_changed_after_PnL=False))
    report(output,config,document,monthly,directions,cov_summary)
    return document


def report(output,cfg,document,months,directions,coverage_rows):
    def f(value):
        return '—' if value is None or value=='' else f'{value:.6f}' if isinstance(value,Decimal) else str(value)
    def table(headers,values):
        return ['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|',
                *['| '+' | '.join(f(x) for x in v)+' |' for v in values]]
    metrics=document['instruments']
    lines=['# R16 Intraday Compression Breakout — Canonical M5 Baseline 2023','',
        '**Baseline: '+document['baseline_status']+'. No Optimization.**','',
        'One frozen candidate, four instruments, all available 2023 development M5. No parameter search.',
        'All reported economics are conditional known closures after C1 (one historical tick per side).',
        'Incomplete source coverage / UNKNOWN mean annual PF, expectancy, Net R, win rate and drawdown remain null. Known-closure drawdown is a diagnostic sequence, not continuous broker equity. Price units from different instruments are never added into a monetary portfolio.','']
    lines+=table(['Instrument','Signals','Orders','Fills','Closed','UNKNOWN','PF C1 price','PF C1 R','Net R','Expectancy R','Win rate','Known-closure DD R'],[
        [s,m['signals'],m['admitted_orders'],m['model_fills'],m['closed'],m['unknown'],*[m['conditional_closed_only_C1'][k] for k in ('PF_C1_price','PF_C1_R','Net_R','Expectancy_R','Win_Rate','Max_DD_R')]] for s,m in metrics.items()])
    lines+=['','## Evidence, averages and concentration','']
    lines+=table(['Instrument','Trade days','Positive/negative months','Average winner R','Average loser R','Largest winner share R','Top 3 winners share R','Largest positive month share R','Status / conditional diagnosis'],[
        [s,m['distribution']['unique_trade_days'],f"{m['distribution']['positive_months']}/{m['distribution']['negative_months']}",
         *[m['distribution'][k] for k in ('average_winner_R','average_loser_R','largest_winner_share_R','top_three_winners_share_R','largest_positive_month_share_R')],m['status']+' / '+m['economic_diagnostic']] for s,m in metrics.items()])
    for s,m in metrics.items():
        lines+=['',s+': evidence checks `'+json.dumps(m['evidence_checks'],sort_keys=True)+'`.',
                'Average winning/losing price-unit trade: '+f(m['distribution']['average_winner_price'])+' / '+f(m['distribution']['average_loser_price'])+'.',
                'Rejection/diagnostic reasons: `'+json.dumps(m['rejection_reasons'],sort_keys=True)+'`.',
                'UNKNOWN reasons: `'+json.dumps(m['unknown_reasons'],sort_keys=True)+'`.',
                f"Unknown possible entries: {m['unknown_possible_entry']}; conditional known closures after prior UNKNOWN: {m['post_unknown_conditional_closed']}."]
    lines+=['','## LONG / SHORT','']
    lines+=table(['Instrument','Side','Signals','Closed','UNKNOWN','PF C1 price','PF C1 R','Net R','Expectancy R','Win rate'],[
        [r['instrument'],r['direction'],r['signals'],r['closed'],r['unknown'],*[r['conditional_'+k] for k in ('PF_C1_price','PF_C1_R','Net_R','Expectancy_R','Win_Rate')]] for r in directions])
    lines+=['','## Twelve calendar months — conditional known closures','',
        'Month attribution uses signal date. Zero closures with observed data have Net R 0 and undefined PF; no source coverage is shown as —, never manufactured as a flat profitable month.','']
    lines+=table(['Month','Instrument','Closed','UNKNOWN','PF C1 price','Net R','Expectancy R','Coverage','Complete/incomplete/pre-inception days'],[
        [r['month'],r['instrument'],r['closed'],r['unknown'],r['conditional_PF_C1_price'],r['conditional_Net_R'],r['conditional_Expectancy_R'],r['coverage_classification'],f"{r['complete_days']}/{r['incomplete_days']}/{r['pre_inception_days']}"]
        for r in sorted(months,key=lambda r:(r['month'],cfg['instruments'].index(r['instrument'])))])
    lines+=['','## Source coverage and UNKNOWN','']
    lines+=table(['Instrument','Source M5 rows','First observation','Complete/incomplete/pre-inception days','Missing/invalid slots','Unavailable opening slots (coverage only)'],[
        [r['instrument'],r['source_rows_2023'],r['first'],f"{r['complete_days']}/{r['incomplete_days']}/{r['pre_inception_days']}",f"{r['missing_expected_slots']}/{r['invalid_expected_slots']}",r['opening_slots_unavailable_days']] for r in coverage_rows])
    lines+=['',
        'Coverage uses the unchanged approved full research-window grid, conservatively including slots outside R16 signal windows. All physical 2023 rows, including morning/evening observations, warm ATR. No bars/days are filled. GLD and IMOEX pre-inception periods stay unavailable.',
        'September 13 halt is diagnosed; other absence causes remain unproven. Missing waiting bars reject without submission. Missing entry Open creates UNKNOWN possible fill; missing exposed bar / mandatory exit retains UNKNOWN with blank net. See coverage_events.csv and unknown_report.csv.',
        'One UNKNOWN blocks only its own day. Following days require an explicit conditional FLAT assumption, not proof of broker FLAT. UNKNOWN economics cannot be used to form a continuous annual result.','',
        '## Frozen adaptation and historical provenance','',
        'Historical commit `'+cfg['historical_reference']+'`, candidate `C16-eda8af2caeee1259`; 72 tested parameter sets, 0 strict survivors. Historical 126 trades / 81 days / 4 positive months / BASE PF 1.498609 / STRESS PF 1.255979 are selection provenance only and are not this Baseline.',
        'Historical parameters remain W=8, width_atr=2.0, breakout_ticks=1, stop_mode=OPPOSITE, target_r=1.5; ATR14 references the previous completed bar. Previously viewed 2026-01-05 through 2026-05-15 cannot later qualify as independent R16 TRUE OOS.',
        'Config frozen in commit `'+FREEZE+'` before any R16 P&L; SHA-256 `'+hashlib.sha256(CONFIG.read_bytes()).hexdigest()+'`. No subsequent parameter changes.','']
    lines += ['- **'+k+':** '+v for k,v in cfg['adaptation'].items()]
    lines+=['','## Classification and validation','',
        'The status is computed from actual results, not copied from ORB. Frozen sufficient-evidence criteria: >=30 closures, >=15 trade days, >=3 active and positive months, >=60% positive active months, PF C1 price and R >=1.6, positive expectancy, largest winner <=25% of positive R and largest positive month <=50% of positive monthly R. Complete coverage and resolved outcomes are required for a confirmed pass. Four-instrument overall assessment requires sufficient evidence from every declared instrument.',
        'Independent source/strategy/execution oracle and independent CSV metric reconstruction: audit.json and Independent_Audit.md. Technical tests, two additional deterministic runs and canonical ORB / R17 regressions: validation.json. Independent implementation audit is not an external reviewer signoff; PR remains Draft for independent review.',
        'All common core modules remain byte-unchanged; the existing PR #466 exact daily deadline and generic computed classification are reused. Prior canonical ORB artifacts/config/strategy and all frozen studies are protected. TradingSystemLab and market-pattern-data remain unchanged.',
        'Reproduce: `python3 IntradayLab/tools/run_r16_baseline.py --data-root /workspace/market-pattern-data --output IntradayLab/work/r16_replay` then `python3 IntradayLab/tools/audit_r16_baseline.py --data-root /workspace/market-pattern-data --output IntradayLab/work/r16_replay`.',
        'Source commit `'+cfg['source_ref']+'`; exact verified 2023 byte prefixes only. No 2024 or 2025+ price bytes read. C1 is a research cost assumption, not verified broker fees or execution capacity.',
        'Baseline → Optimization → Robustness → Walk Forward → TRUE OOS. This task stops at Baseline and Draft PR: no Merge, Optimization, Robustness, Walk Forward, TRUE OOS or LIVE.','']
    (output/'Baseline_Report.md').write_text('\n'.join(lines))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=OUT)
    args=parser.parse_args()
    result=run(args.data_root,args.output)
    print(json.dumps({'baseline_status':result['baseline_status'], 'instruments':{
        s:{k:m[k] for k in ('signals','model_fills','closed','unknown','status','economic_diagnostic')}
        for s,m in result['instruments'].items()}},sort_keys=True))
