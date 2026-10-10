#!/usr/bin/env python3
"""Frozen Level Rejection config -> existing common engine/metrics -> separate reports."""
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
from IntradayLab.strategies.level_rejection import LevelRejection

LAB = ROOT/'IntradayLab'
CONFIG = LAB/'config/level_rejection_2023_m5_v1.json'
OUT = LAB/'results/level_rejection_2023_m5_v1'
FREEZE = 'c785d0d94133a72b97143f5b9348d6e373da7fd9'


def assessed(trades, signals, source, config):
    m = summarize(trades, signals, source)
    m['distribution'] = distribution_metrics(trades)
    m['funnel'] = funnel(signals, trades)
    m['target_C1_diagnostics'] = target_diagnostics(trades)
    m['unknown_reasons'] = dict(sorted(Counter(t['unknown_reason'] for t in trades if t['status']=='UNKNOWN').items()))
    m.update(assess_baseline(m, m['distribution'], config['classification_policy']))
    return m


def funnel(signals, trades):
    return dict(raw_rejections=sum(s.get('raw_rejection', False) for s in signals),
        confirmed_signals=sum(s.get('confirmed_signal', False) for s in signals),
        dedup_30min=sum(s['base_reason']=='DEDUP_30MIN' for s in signals),
        pending_entries=sum(s.get('pending_created', False) for s in signals),
        submitted_orders=sum(s['order_admitted'] for s in signals),
        admitted_Open_entries=sum(s.get('open_admission_passed') is True for s in signals),
        position_busy=sum(s['reason']=='POSITION_BUSY' for s in signals),
        model_fills=sum(t['model_filled'] for t in trades),
        closed=sum(t['status']=='CLOSED' for t in trades),
        unknown=sum(t['status']=='UNKNOWN' for t in trades),
        unknown_possible_fills=sum(t['status']=='UNKNOWN' and not t['model_filled'] for t in trades))


def target_diagnostics(trades):
    closed=[t for t in trades if t['status']=='CLOSED']
    filled=[t for t in trades if t['model_filled']]
    take=[t for t in closed if t['exit_reason']=='TAKE']
    wins=[t for t in closed if t['net_c1']>0]
    return dict(initial_R_denominator='initial gross price risk; unchanged common metric contract',
        target_ratio_denominator='initial gross risk + round-trip C1',
        planned_full_net_R_min=min((t['planned_net_to_net_R'] for t in filled),default=None),
        planned_full_net_R_max=max((t['planned_net_to_net_R'] for t in filled),default=None),
        target_hit_closed=len(take),
        target_hit_fraction_known_closed=Decimal(len(take))/len(closed) if closed else None,
        actual_Take_net_net_R_min=min((t['realized_net_to_net_R'] for t in take),default=None),
        actual_Take_net_net_R_max=max((t['realized_net_to_net_R'] for t in take),default=None),
        known_closures_reaching_full_net_3R=sum(t['realized_net_to_net_R']>=3 for t in closed),
        gross_R_known_closed=sum((t['gross_R'] for t in closed),Decimal(0)),
        cost_R_known_closed=sum((t['cost_R'] for t in closed),Decimal(0)),
        gross_price_known_closed=sum((t['gross'] for t in closed),Decimal(0)),
        cost_price_known_closed=sum((t['cost_c1'] for t in closed),Decimal(0)),
        mean_positive_realized_net_net_R=sum((t['realized_net_to_net_R'] for t in wins),Decimal(0))/len(wins) if wins else None,
        adverse_Stop_gaps=sum(t['exit_reason']=='STOP' and t['exit_at'] is not None for t in closed),
        unresolved_filled_targets=sum(t['model_filled'] and t['status']=='UNKNOWN' for t in trades),
        exit_reasons=dict(sorted(Counter(t['exit_reason'] for t in closed).items())))


def row(symbol, trades, signals, source, config, **labels):
    r = table_row(symbol, trades, signals, source, **labels)
    m = assessed(trades, signals, source, config)
    r.update(status=m['status'], economic_diagnostic=m['economic_diagnostic'],
             evidence_checks=m['evidence_checks'])
    r.update({'conditional_'+k:v for k,v in m['distribution'].items()})
    return r


def run(data_root, output):
    if output.resolve()!=OUT.resolve() and not output.resolve().is_relative_to((LAB/'work').resolve()):
        raise ValueError('OUTPUT_MUST_BE_Level Rejection_RESULTS_OR_INTRADAYLAB_WORK')
    config = json.loads(CONFIG.read_text())
    for path, digest in config['execution_code_sha256'].items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=digest:
            raise ValueError('FROZEN_EXECUTION_CHANGED '+path)
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
        signals, trades, days = engine.run(LevelRejection(config['parameters']),symbol,raw[symbol],
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
        research_phase='BASELINE',historical_opportunity_comparison=dict(T10_upper_bound=1754,T15_upper_bound=1648,
            clocks_equivalent=False,counts_not_directly_comparable=True),
        optimization_allowed=False,instruments=metrics,
        portfolio_money_return=None,portfolio_price_PF=None,continuous_portfolio_equity=None,
        no_cross_instrument_price_pooling=True)
    dump(output/'metrics.json',document)
    dump(output/'funnel.json',{s:m['funnel'] for s,m in metrics.items()})
    dump(output/'input_provenance.json',dict(source_repository=config['source_repository'],
        source_ref=config['source_ref'],source_clean=True,inputs=receipts,
        bytes_2024_plus_read=0,bytes_2025_plus_read=0,timezone=config['timezone'],bar_label='start'))
    code_paths=sorted([*(LAB/'core').glob('*.py'),LAB/'strategies/level_rejection.py',
        Path(__file__),LAB/'tools/audit_level_rejection_baseline.py',LAB/'tools/validate_level_rejection_baseline.py',
        LAB/'tools/audit_canonical_baseline.py',LAB/'tests/test_level_rejection.py',LAB/'tests/test_level_rejection_audit.py',LAB/'tests/test_net_c1_execution.py',CONFIG])
    dump(output/'provenance.json',dict(base_main=config['base_main'],config_freeze_commit=FREEZE,
        config_sha256=digest,config_frozen_before_first_PnL=True,historical_reference=config['historical_reference'],
        historical_selection=config['historical_selection'],opportunity_to_canonical_M5_adaptation=config['adaptation'],
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
    lines=['# LEVEL_REJECTION_M5 — Canonical Economic Baseline 2023','',
        '**Research phase: BASELINE. Status: '+document['baseline_status']+'. No automatic Optimization.**','',
        'One fixed hypothesis, one common M5 Backtester, four instruments, entire available 2023. No optimizer or alternative execution scenarios.',
        'All economic tables below describe conditional known closures after C1, one dated historical tick per side. Confirmed annual PF, Net R, expectancy, win rate and DD stay null on incomplete coverage/UNKNOWN. Known-closure DD is a conditional diagnostic sequence, not continuous broker equity. No cross-instrument price-unit portfolio pooling.','']
    lines+=table(['Instrument','Raw','Confirmed','Pending','Orders submitted','Admitted Open','Fills','Closed','UNKNOWN'],[
        [s,*[m['funnel'][k] for k in ('raw_rejections','confirmed_signals','pending_entries','submitted_orders','admitted_Open_entries','model_fills','closed','unknown')]] for s,m in metrics.items()])
    lines+=['','Admitted Open means the observed scalar Open passes reclaim/risk conditions; submitted orders also include unknown possible fills and rejected Open geometry. Confirmed signals consume directional dedup even when the common engine rejects busy/time/unknown state. Raw one-sided rejection rows and DEDUP_30MIN remain in signals.csv.','']
    lines+=table(['Instrument','Closed','Trade days','PF C1 price','PF C1 R','Net R','Expectancy R','Win rate','Conditional DD R','+/- months'],[
        [s,m['closed'],m['distribution']['unique_trade_days'],*[m['conditional_closed_only_C1'][k] for k in ('PF_C1_price','PF_C1_R','Net_R','Expectancy_R','Win_Rate','Max_DD_R')],
         f"{m['distribution']['positive_months']}/{m['distribution']['negative_months']}"] for s,m in metrics.items()])
    lines+=['','## Distribution, costs and realized target attainment','']
    lines+=table(['Instrument','Average winner R','Average loser R','Average winner price','Average loser price','Largest winner share R','Top 3 winner share R','Largest positive month share'],[
        [s,*[m['distribution'][k] for k in ('average_winner_R','average_loser_R','average_winner_price','average_loser_price','largest_winner_share_R','top_three_winners_share_R','largest_positive_month_share_R')]] for s,m in metrics.items()])
    lines+=['']
    lines+=table(['Instrument','Gross R known','Cost R C1','Take closures','Take / known closed','Actual Take net/net R min','Closures >= full-net 3R','Unresolved filled targets'],[
        [s,*[m['target_C1_diagnostics'][k] for k in ('gross_R_known_closed','cost_R_known_closed','target_hit_closed','target_hit_fraction_known_closed','actual_Take_net_net_R_min','known_closures_reaching_full_net_3R','unresolved_filled_targets')]] for s,m in metrics.items()])
    lines+=['','Target 3R uses **net-win / net-Stop-loss**, unlike the unchanged common net_R_c1 metric using initial gross risk. Planned primary distance d_full=3s+8t, diagnostic-only d_legacy=3s+2t; targets round outward. Their geometry never guarantees the target will be reached. Actual Take closures, TIME/SESSION/STOP and UNKNOWN come from real forward 2023 paths under the one frozen execution contract. Adverse Stop gaps can exceed ideal Stop loss.','']
    for s,m in metrics.items():
        lines += [s+': status **'+m['status']+'**, conditional diagnosis **'+m['economic_diagnostic']+'**.',
            'Funnel / dedup / busy: `'+json.dumps(m['funnel'],sort_keys=True)+'`.',
            'Rejection reasons: `'+json.dumps(m['rejection_reasons'],sort_keys=True)+'`.',
            'UNKNOWN reasons: `'+json.dumps(m['unknown_reasons'],sort_keys=True)+'`.',
            'Exit / target / C1 diagnostics: `'+json.dumps(m['target_C1_diagnostics'],default=str,sort_keys=True)+'`.',
            'Evidence checks: `'+json.dumps(m['evidence_checks'],sort_keys=True)+'`.','']
    lines+=['## LONG / SHORT','']
    lines+=table(['Instrument','Side','Signals','Fills','Closed','UNKNOWN','PF price','PF R','Net R','Expectancy R','Win rate'],[
        [r['instrument'],r['direction'],r['signals'],r['model_fills'],r['closed'],r['unknown'],*[r['conditional_'+k] for k in ('PF_C1_price','PF_C1_R','Net_R','Expectancy_R','Win_Rate')]] for r in directions])
    lines+=['','## All twelve calendar months','',
        'Signal-month attribution; zero closures with observed data have Net R 0 and undefined PF. Before instrument inception: NO_COVERAGE and no manufactured flat returns.','']
    lines+=table(['Month','Instrument','Signals','Fills','Closed','UNKNOWN','PF price','Net R','Expectancy R','Coverage','Complete/incomplete/pre-inception days'],[
        [r['month'],r['instrument'],r['signals'],r['model_fills'],r['closed'],r['unknown'],r['conditional_PF_C1_price'],r['conditional_Net_R'],r['conditional_Expectancy_R'],r['coverage_classification'],f"{r['complete_days']}/{r['incomplete_days']}/{r['pre_inception_days']}"]
        for r in sorted(months,key=lambda r:(r['month'],cfg['instruments'].index(r['instrument'])))])
    lines+=['','## Coverage and unresolved outcomes','']
    lines+=table(['Instrument','2023 rows','First observation','Complete/incomplete/pre-inception days','Missing/invalid research slots'],[
        [r['instrument'],r['source_rows_2023'],r['first'],f"{r['complete_days']}/{r['incomplete_days']}/{r['pre_inception_days']}",f"{r['missing_expected_slots']}/{r['invalid_expected_slots']}"] for r in coverage_rows])
    lines+=['',
        'Unchanged full calendar research-window coverage is assessed conservatively, including source slots outside the trade deadline. coverage_report.csv has every instrument/month; coverage_daily.csv and coverage_events.csv preserve gaps. Missing waiting bars reject before submission; missing execution Open stays UNKNOWN possible fill; missing exposed/mandatory exit observations stay UNKNOWN with blank economics. No bar or Open replacement.',
        'UNKNOWN blocks only its research day. Later independent research days conditionally assume FLAT; this is not broker reconciliation or a confirmed continuous equity curve.','',
        '## Historical opportunity provenance and frozen adaptation','',
        'Historical freeze `1487d7e041e9e32122a5df9ae280386da8ebadb1`, six-bar Level Rejection opportunity preregistration/config, its report and runner. Historical OPPORTUNITY_FEASIBLE: 1754 T10 / 1648 T15 conditional opportunities, no Stop/Take/position/P&L. Those schedules entered at test START+20/+25. New canonical economic Baseline enters at START+10 after one full waiting M5 and simulates actual position occupancy/exits, so counts are not directly comparable.',
        'Config and actual execution/strategy source frozen before first P&L in commit `'+FREEZE+'`; config SHA-256 `'+hashlib.sha256(CONFIG.read_bytes()).hexdigest()+'`. No outcome-driven changes.','']
    lines += ['- **'+k+':** '+value for k,value in cfg['adaptation'].items()]
    lines+=['','## Computed classification, audit and regression','',
        'Existing shared assess_baseline computes the verdict. Fixed policy: complete coverage/resolved outcomes, >=30 known closures, >=15 trade days, >=3 active and positive months, >=60% positive active months, positive C1 expectancy, price and R PF >=1.6, largest winner <=25% of positive R and largest positive month <=50% of positive monthly R. Overall four-instrument assessment requires credible evidence across every declared instrument; sparse high PF is insufficient.',
        'Independent raw-source signal/admission/forward-path oracle and CSV metric reconstruction: audit.json / Independent_Audit.md. All tests, two complete repeats, three canonical economic regressions and protected-byte checks: validation.json. Implementation independence is not external human review; PR remains Draft.',
        'Only optional generic entry constraints and FULL_NET_C1_R geometry extend execution.py/backtester.py. All old default behavior and stored ORB/R17/R16 strategies/config/results remain unchanged; rerun result bytes match. Separate replay provenance records current core code hashes, the newly enumerated strategy, and previously merged base-main code where older runners enumerate all current strategies/metrics. Exact differences and their explanations are in validation.json. TradingSystemLab and market-pattern-data untouched.',
        'Reproduce: `python3 IntradayLab/tools/run_level_rejection_baseline.py --data-root /workspace/market-pattern-data --output IntradayLab/work/level_rejection_replay` then `python3 IntradayLab/tools/audit_level_rejection_baseline.py --data-root /workspace/market-pattern-data --output IntradayLab/work/level_rejection_replay`.',
        'Source commit `'+cfg['source_ref']+'`; exact pinned unbuffered 2023 prefixes only. Zero 2024/WF or 2025+/TRUE OOS price bytes read.',
        'Baseline → Optimization → Robustness → Walk Forward → TRUE OOS. Stops after this Baseline and Draft PR. No Merge, next candidate, Optimization, Robustness, WF, TRUE OOS or LIVE.','']
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
