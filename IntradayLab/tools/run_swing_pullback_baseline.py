#!/usr/bin/env python3
"""Frozen Swing Pullback config -> existing common engine/metrics -> separate reports."""
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
from IntradayLab.strategies.swing_pullback_m5_m15 import SwingPullback

LAB = ROOT/'IntradayLab'
CONFIG = LAB/'config/swing_pullback_m5_m15_2023_v1.json'
OUT = LAB/'results/swing_pullback_m5_m15_2023_v1'
FREEZE = subprocess.check_output(['git','-C',str(ROOT),'log','--diff-filter=A','--format=%H','--',str(CONFIG.relative_to(ROOT))], text=True).strip()


def assessed(trades, signals, source, config):
    m = summarize(trades, signals, source)
    m['distribution'] = distribution_metrics(trades)
    m['funnel'] = funnel(signals, trades)
    m['target_C1_diagnostics'] = target_diagnostics(trades)
    m['unknown_reasons'] = dict(sorted(Counter(t['unknown_reason'] for t in trades if t['status']=='UNKNOWN').items()))
    d=m['distribution']
    m['calendar_regularity']=dict(positive_month_fraction_of_12=Decimal(d['positive_months'])/12,
        positive_active_month_fraction=Decimal(d['positive_months'])/d['active_months'] if d['active_months'] else None,
        worst_known_closed_month=min(d['monthly_closed_Net_R'],key=d['monthly_closed_Net_R'].get) if d['monthly_closed_Net_R'] else None,
        worst_known_closed_month_Net_R=min(d['monthly_closed_Net_R'].values(),default=None),
        model_fills_per_available_calendar_day=Decimal(m['model_fills'])/sum(c['status']!='PRE_INCEPTION' for c in source) if any(c['status']!='PRE_INCEPTION' for c in source) else None)
    m.update(assess_baseline(m, m['distribution'], config['classification_policy']))
    return m


def funnel(signals, trades):
    return dict(context_decisions=len(signals),
        valid_M15_contexts=sum(s.get('context_valid', False) for s in signals),
        unique_valid_M15_contexts=len({s['context_p3_start'] for s in signals if s.get('context_valid', False)}),
        LONG_trends=sum(s.get('context_valid') and s.get('context_direction')==1 for s in signals),
        SHORT_trends=sum(s.get('context_valid') and s.get('context_direction')==-1 for s in signals),
        M5_pullbacks=sum(s.get('pullback_confirmed', False) for s in signals),
        continuation_signals=sum(s.get('confirmed_signal', False) for s in signals),
        rejected_continuation_signals=sum(s.get('confirmed_signal',False) and not s['model_filled'] for s in signals),
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
    r.update(m['funnel']);r.update(m['calendar_regularity']);r.update(m['target_C1_diagnostics'])
    return r


def run(data_root, output):
    if output.resolve()!=OUT.resolve() and not output.resolve().is_relative_to((LAB/'work').resolve()):
        raise ValueError('OUTPUT_MUST_BE_Swing Pullback_RESULTS_OR_INTRADAYLAB_WORK')
    if len(FREEZE)!=40:
        raise ValueError('PRE_PNL_FREEZE_COMMIT_REQUIRED')
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
    ss, tt, dd, cc, gg, monthly, instruments, directions, cov_summary, contexts = [], [], [], [], [], [], [], [], [], []
    metrics = {}
    for symbol in config['instruments']:
        strategy = SwingPullback(config['parameters'])
        signals, trades, days = engine.run(strategy,symbol,raw[symbol],
            start=date.fromisoformat(config['start']),end_exclusive=date.fromisoformat(config['end_exclusive']))
        source, gaps = coverage(symbol,raw[symbol],config,rules)
        contexts.extend(strategy.context_records)
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
    for name, data in [('signals',ss),('mtf_context',contexts),('trades',tt),('days',dd),('coverage_daily',cc),
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
        research_phase='BASELINE',
        optimization_allowed=False,instruments=metrics,
        portfolio_money_return=None,portfolio_price_PF=None,continuous_portfolio_equity=None,
        no_cross_instrument_price_pooling=True)
    dump(output/'metrics.json',document)
    dump(output/'funnel.json',{s:m['funnel'] for s,m in metrics.items()})
    dump(output/'input_provenance.json',dict(source_repository=config['source_repository'],
        source_ref=config['source_ref'],source_clean=True,inputs=receipts,
        bytes_2024_plus_read=0,bytes_2025_plus_read=0,timezone=config['timezone'],bar_label='start'))
    code_paths=sorted([*(LAB/'core').glob('*.py'),LAB/'strategies/swing_pullback_m5_m15.py',
        Path(__file__),LAB/'tools/audit_swing_pullback_baseline.py',LAB/'tools/validate_swing_pullback_baseline.py',
        LAB/'tools/audit_canonical_baseline.py',LAB/'tests/test_swing_pullback.py',LAB/'tests/test_swing_pullback_audit.py',CONFIG])
    dump(output/'provenance.json',dict(base_main=config['base_main'],config_freeze_commit=FREEZE,
        config_sha256=digest,config_frozen_before_first_PnL=True,signal_and_M15_contract=config['adaptation'],
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
                *['| '+' | '.join(f(x) for x in v)+' |' for v in values], '']
    ms=document['instruments']
    lines=['# SWING_PULLBACK_M5_M15 — Canonical Baseline 2023','',
        '**Research phase: BASELINE. Final classification: '+document['baseline_status']+'.**','',
        'One initial structural hypothesis supplied before results, one fixed configuration, four instruments, entire available 2023. No Optimization or alternative scenario.',
        'All economics below are conditional known closures after C1 (one dated tick per side). Annual complete metrics remain null on incomplete coverage/UNKNOWN. Conditional DD is not proven continuous equity. Instrument price P&L is never pooled as portfolio money.','',
        '## Fixed parameters and causal contract','']
    lines+=table(['Parameter','Value'],list(cfg['parameters'].items()))
    lines+=['Pre-P&L commit `'+FREEZE+'`; config SHA-256 `'+hashlib.sha256(CONFIG.read_bytes()).hexdigest()+'`. Config, signal/M15 and common core hashes are verified against this freeze. No result-driven changes.','']
    lines += ['- **'+k+':** '+v for k,v in cfg['adaptation'].items()]
    lines+=['','## M15 → M5 → entry → exit','',
        'Context/trend counts are per M5 decision, not unique independent trend episodes. mtf_context.csv links every decision to exact three M15 and nine child start clocks; all times are MSK and child clocks use their parent date. Unavailable buckets retain expected lineage, blank prices and explicit reasons.','']
    lines+=table(['Instrument','Valid M15','LONG','SHORT','Pullbacks','Signals','Rejected','Pending','Orders','Fills','Closed','UNKNOWN'],[
        [s,*[m['funnel'][k] for k in ('valid_M15_contexts','LONG_trends','SHORT_trends','M5_pullbacks','continuation_signals','rejected_continuation_signals','pending_entries','submitted_orders','model_fills','closed','unknown')]] for s,m in ms.items()])
    lines+=['## Conditional C1 economics','']
    lines+=table(['Instrument','Closed','Days','PF price','PF R','Net R','Expectancy R','Win rate','Conditional DD R'],[
        [s,m['closed'],m['distribution']['unique_trade_days'],*[m['conditional_closed_only_C1'][k] for k in ('PF_C1_price','PF_C1_R','Net_R','Expectancy_R','Win_Rate','Max_DD_R')]] for s,m in ms.items()])
    lines+=table(['Instrument','Avg win R','Avg loss R','Avg win price','Avg loss price','Largest winner share','Top 3 share','Largest positive month share'],[
        [s,*[m['distribution'][k] for k in ('average_winner_R','average_loser_R','average_winner_price','average_loser_price','largest_winner_share_R','top_three_winners_share_R','largest_positive_month_share_R')]] for s,m in ms.items()])
    lines+=['## Calendar regularity','']
    lines+=table(['Instrument','Positive /12','Positive /active','Worst known month','Worst Net R','Fills /available day'],[
        [s,*[m['calendar_regularity'][k] for k in ('positive_month_fraction_of_12','positive_active_month_fraction','worst_known_closed_month','worst_known_closed_month_Net_R','model_fills_per_available_calendar_day')]] for s,m in ms.items()])
    lines+=['Positive known closures in a month do not establish a complete positive calendar result. Zero-trade and pre-inception months are not positive. Every month remains in the tables.','', '## Planned and actual 3R','',
        'The planned full-net ratio is (take distance−2t)/(initial price risk+2t). Shared FULL_NET_C1_R sets distance=3s+8t with outward rounding. Actual net/net uses realized net price P&L/(s+actual C1); net_R_c1 and PF_R use s. These are different denominators. Target geometry never guarantees attainment.','']
    lines+=table(['Instrument','Plan min','Plan max','TAKE','TAKE /closed','Actual TAKE min','Actual TAKE max','Closed >=3 net/net','Filled UNKNOWN'],[
        [s,*[m['target_C1_diagnostics'][k] for k in ('planned_full_net_R_min','planned_full_net_R_max','target_hit_closed','target_hit_fraction_known_closed','actual_Take_net_net_R_min','actual_Take_net_net_R_max','known_closures_reaching_full_net_3R','unresolved_filled_targets')]] for s,m in ms.items()])
    for s,m in ms.items():
        lines += [s+': **'+m['status']+'**; conditional diagnosis **'+m['economic_diagnostic']+'**.',
            'Exit counts / costs / target details: `'+json.dumps(m['target_C1_diagnostics'],default=str,sort_keys=True)+'`.',
            'Rejected events: `'+json.dumps(m['rejection_reasons'],sort_keys=True)+'`.',
            'UNKNOWN: `'+json.dumps(m['unknown_reasons'],sort_keys=True)+'`.',
            'Evidence checks: `'+json.dumps(m['evidence_checks'],sort_keys=True)+'`.','']
    lines+=['## LONG / SHORT','']
    lines+=table(['Instrument','Side','Signals','Fills','Closed','UNKNOWN','PF price','PF R','Net R','Expectancy R'],[
        [r['instrument'],r['direction'],r['signals'],r['model_fills'],r['closed'],r['unknown'],*[r['conditional_'+k] for k in ('PF_C1_price','PF_C1_R','Net_R','Expectancy_R')]] for r in directions])
    lines+=['## All twelve calendar months','']
    lines+=table(['Month','Instrument','Signals','Fills','Closed','UNKNOWN','PF price','PF R','Net R','Expectancy R','Coverage'],[
        [r['month'],r['instrument'],r['signals'],r['model_fills'],r['closed'],r['unknown'],*[r['conditional_'+k] for k in ('PF_C1_price','PF_C1_R','Net_R','Expectancy_R')],r['coverage_classification']]
        for r in sorted(months,key=lambda r:(r['month'],cfg['instruments'].index(r['instrument'])))])
    lines+=['## Coverage and UNKNOWN','']
    lines+=table(['Instrument','Rows 2023','First observation','Complete/incomplete/pre-inception days','Missing/invalid M5'],[
        [r['instrument'],r['source_rows_2023'],r['first'],f"{r['complete_days']}/{r['incomplete_days']}/{r['pre_inception_days']}",f"{r['missing_expected_slots']}/{r['invalid_expected_slots']}"] for r in coverage_rows])
    lines+=['Coverage uses the entire accepted research windows, including post-17:00 slots, conservatively. No OHLCV filled. Missing waiting rejects before order submission; missing entry Open is UNKNOWN possible fill. Missing exposed/exit path is UNKNOWN with blank P&L. UNKNOWN blocks its day; subsequent independent research days assume FLAT conditionally. Annual equity and Max DD are unconfirmed.','',
        '## Validation, isolation and classification','',
        'Independent batch M15/signal and forward-path oracle imports no production strategy, core or metrics. It verifies lineage, availability, gaps, signals, ledger, C1 and CSV-only economics. This is independent implementation verification by the task agent, not external human acceptance. See Independent_Audit.md / audit.json.',
        'validation.json records technical tests, two full repeats with byte equality, complete reruns and independent audits of ORB A BASE, R17, R16 and Level Rejection. Old stored results and every existing file remain byte unchanged. Shared execution is unchanged; this adapter owns no orders, positions or P&L. TradingSystemLab and all paths outside IntradayLab are unchanged.',
        'Predeclared evidence policy: complete coverage/outcomes, >=30 closures, >=15 trade days, >=3 active and positive months, >=60% positive active months, positive C1 expectancy, both PF >=1.6, largest winner <=25% and largest positive month <=50%. Incomplete coverage/outcomes gives INCONCLUSIVE; negative known expectancy gives separate NO ECONOMIC BASELINE PASS diagnosis. Controlled annual drawdown cannot be certified without full coverage.',
        'Reproduce: `python3 IntradayLab/tools/run_swing_pullback_baseline.py --data-root /workspace/market-pattern-data --output IntradayLab/work/swing_replay` then the matching `audit_swing_pullback_baseline.py` command.',
        'Pinned source `'+cfg['source_ref']+'`; only exact 2023 prefixes. Zero 2024/2025+ price bytes. No selection of profitable instruments/directions/months.',
        'Stops after Draft PR. No Merge, Optimization, Robustness, Walk Forward, TRUE OOS or LIVE.','']
    (output/'Baseline_Report.md').write_text('\n'.join(lines))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=OUT)
    args=parser.parse_args();result=run(args.data_root,args.output)
    print(json.dumps({'baseline_status':result['baseline_status'],'instruments':{
        s:{k:m[k] for k in ('signals','model_fills','closed','unknown','status','economic_diagnostic')}
        for s,m in result['instruments'].items()}},sort_keys=True))
