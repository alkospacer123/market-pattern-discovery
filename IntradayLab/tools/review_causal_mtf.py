"""Reporting-only economic closeout; never changes predeclared experiments."""
import argparse
from collections import Counter, defaultdict
from decimal import Decimal as D
import json
from pathlib import Path

from audit_stage2_architectures import rows
from independent_corrective_review import encoded, write_csv
from stage2_architecture_analysis import LAB
from run_stage2_architectures import checksums

DEST = LAB / 'results/stage2_causal_mtf_v1'
ZERO = D(0)


def number(value):
    return None if value in ('', None) else D(value)


def pf(values):
    gain = sum((v for v in values if v > 0), ZERO)
    loss = -sum((v for v in values if v < 0), ZERO)
    return gain / loss if loss else None


def review(folder):
    runs = json.loads((folder / 'results.json').read_text())['runs']
    metric = rows(folder / 'metrics.csv')
    ledger = rows(folder / 'trade_ledger.csv')
    attrs = rows(folder / 'trade_attribution.csv')
    signals = rows(folder / 'signals.csv')
    byrun = defaultdict(list)
    byattr = defaultdict(list)
    bysignal = defaultdict(list)
    freq = defaultdict(list)
    for r in ledger:
        byrun[r['architecture'], r['scenario'], r['run']].append(r)
    for r in attrs:
        byattr[r['architecture'], r['scenario'], r['run']].append(r)
    for r in signals:
        bysignal[r['architecture'], r['scenario'], r['run']].append(r)
    for r in rows(folder / 'daily_frequency.csv'):
        freq[r['architecture'], r['scenario'], r['run']].append(r)
    summaries = {(r['architecture'], r['scenario'], r['run']): r for r in runs}
    comparisons, retention, exits, bins, directions, concentration = [], [], [], [], [], []
    for k, cohort in sorted(byrun.items()):
        for reason, count in sorted(Counter(r['exit_reason'] for r in cohort).items()):
            exits.append(dict(zip(('architecture', 'scenario', 'run'), k)) | {'exit_reason': reason, 'count': count})
        for ruler in ('net_R', 'gross_R'):
            counter = Counter()
            for r in cohort:
                value = number(r['net_R']) if ruler == 'net_R' else (number(r['gross_price_pnl']) / number(r['initial_risk_price_units']) if r['gross_price_pnl'] else None)
                bucket = 'UNKNOWN' if value is None else '<=-1R' if value <= -1 else '(-1,0)R' if value < 0 else '0R' if value == 0 else '(0,0.5)R' if value < D('.5') else '[0.5,1)R' if value < 1 else '[1,2)R' if value < 2 else '[2,3)R' if value < 3 else '>=3R'
                counter[bucket] += 1
            bins += [dict(zip(('architecture', 'scenario', 'run'), k)) | {'ruler': ruler, 'bucket': b, 'count': n, 'basis': 'Each parent initial price risk; no capital sizing'} for b, n in sorted(counter.items())]
    for r in runs:
        if r['scenario'] != 'C1_T10':
            continue
        k = r['architecture'], r['scenario'], r['run']
        known = [t for t in byrun[k] if t['net_model_c1']]
        nets = [D(t['net_model_c1']) for t in known]
        wins = sorted((v for v in nets if v > 0), reverse=True)
        total_wins = sum(wins, ZERO)
        net = sum(nets, ZERO) if nets else None
        without_top = list(nets)
        if wins:
            without_top.remove(wins[0])
        conc = dict(zip(('architecture', 'scenario', 'run'), k)) | {
            'closed_trades': len(known), 'positive_trades': len(wins),
            'largest_winner': wins[0] if wins else None,
            'top1_share_positive_PnL': wins[0] / total_wins if wins else None,
            'top5_share_positive_PnL': sum(wins[:5], ZERO) / total_wins if wins else None,
            'top1_over_closed_net': wins[0] / net if wins and net and net > 0 else None,
            'closed_net_without_top_winner': sum(without_top, ZERO) if wins else None,
            'closed_PF_without_top_winner': pf(without_top) if wins else None,
            'basis': 'Known subset sensitivity; excludes unknown, never full portfolio PnL'}
        concentration.append(conc)
        days = freq[k]
        dates = {t['entry_interval_start'][:10] for t in byrun[k]}
        weeks = len(days) / 5
        months = len({d['date'][:7] for d in days})
        ms = [t for t in metric if t['architecture'] == k[0] and t['scenario'] == k[1] and t['run'] == k[2] and t['group'] == 'MONTH' and t['direction'] == 'ALL']
        delayed = summaries[r['architecture'], 'C1_T15_DELAY', r['run']]
        ref = summaries[r['base_architecture'] + '__NONE', 'C1_T10', r['run']]
        reference_signals = {t['signal_id'] for t in byrun[r['base_architecture'] + '__NONE', 'C1_T10', r['run']]}
        own_signals = {t['signal_id'] for t in byrun[k]}
        fields = ('architecture', 'base_architecture', 'context_tf', 'strategy', 'instrument', 'run',
            'signals', 'trades', 'closed_accounted_trades', 'unresolved', 'closed_only_gross',
            'closed_only_c1', 'closed_only_net_c1', 'net_PF_closed_diagnostic', 'gross_PF_closed_diagnostic',
            'net_expectancy_closed_diagnostic', 'mean_net_R_closed_diagnostic', 'mean_win',
            'mean_loss_magnitude', 'closed_only_drawdown_price_units', 'Net', 'full_PF',
            'Net_null_reason', 'complete_calendar_months', 'complete_positive_calendar_months',
            'complete_negative_calendar_months', 'no_coverage_months', 'incomplete_covered_months')
        row = {f: r.get(f) for f in fields}
        row.update(reference_M5_entries=ref['trades'], entries_change=r['trades'] - ref['trades'],
            entries_retained_same_signal=len(reference_signals & own_signals),
            reference_entries_omitted=len(reference_signals - own_signals),
            newly_freed_opportunities=len(own_signals - reference_signals),
            entries_retention_ratio=D(r['trades']) / ref['trades'] if ref['trades'] else None,
            entry_days=len(dates), approved_calendar_days_since_source_inception=len(days),
            entries_per_5_approved_days=D(r['trades']) / D(str(weeks)) if weeks else None,
            entries_per_source_calendar_month=D(r['trades']) / months if months else None,
            entries_per_2023_calendar_month=D(r['trades']) / 12,
            entries_per_2023_calendar_week=D(r['trades']) * 7 / 365,
            closed_positive_months=sum(t['closed_subset_outcome'] == 'POSITIVE' for t in ms),
            closed_negative_months=sum(t['closed_subset_outcome'] == 'NEGATIVE' for t in ms),
            months_with_closed_trades=sum(int(t['closed_accounted_trades']) > 0 for t in ms),
            months_without_model_entries=sum(int(t['trades']) == 0 for t in ms),
            closed_positive_share_12_months=D(sum(t['closed_subset_outcome'] == 'POSITIVE' for t in ms)) / 12,
            closed_negative_share_12_months=D(sum(t['closed_subset_outcome'] == 'NEGATIVE' for t in ms)) / 12,
            complete_positive_share_12_months=D(r['complete_positive_calendar_months']) / 12,
            complete_negative_share_12_months=D(r['complete_negative_calendar_months']) / 12,
            no_coverage_share_12_months=D(r['no_coverage_months']) / 12,
            incomplete_covered_share_12_months=D(r['incomplete_covered_months']) / 12,
            delay_entries=delayed['trades'], delay_closed=delayed['closed_accounted_trades'],
            delay_unknown=delayed['unresolved'], delay_net=delayed['closed_only_net_c1'],
            delay_PF=delayed['net_PF_closed_diagnostic'], C2_net=r['C2_closed_net_stress'], C2_PF=r['C2_PF_closed_stress'],
            top1_share_positive_PnL=conc['top1_share_positive_PnL'],
            closed_net_without_top_winner=conc['closed_net_without_top_winner'],
            closed_PF_without_top_winner=conc['closed_PF_without_top_winner'],
            mtf_no_context_signals=sum(t.get('mtf_reason', '').startswith(('MTF_TWO', 'MTF_INCOMPLETE', 'MTF_CHILD')) for t in bysignal[k]),
            mtf_direction_rejected_signals=sum(t.get('mtf_reason', '') in ('MTF_DIRECTION_NOT_ALIGNED', 'MTF_SUSTAINED_ADVERSE_DIRECTION') for t in bysignal[k]),
            mtf_filtered_entry_attempts=sum(t['status'] == 'FILTERED' and t['reason'].startswith('MTF_') for t in bysignal[k]))
        for field in ('mfe_pre_exit_lower_bound_R', 'mae_pre_exit_lower_bound_R', 'mfe_observable_before_exit_lower_bound_R', 'mfe_actionable_before_exit_lower_bound_R'):
            values = [D(t[field]) for t in byattr[k] if t[field]]
            row['mean_' + field] = sum(values, ZERO) / len(values) if values else None
            row['denominator_' + field] = len(values)
        comparisons.append(row)
        retention.append({f: row[f] for f in ('architecture', 'run', 'reference_M5_entries', 'trades', 'closed_accounted_trades', 'unresolved', 'entries_retained_same_signal', 'reference_entries_omitted', 'newly_freed_opportunities', 'entries_retention_ratio', 'mtf_filtered_entry_attempts')})
        directions += [t for t in metric if t['architecture'] == k[0] and t['scenario'] == k[1] and t['run'] == k[2] and t['group'] == 'YEAR']
    pair_groups = defaultdict(list)
    for r in rows(folder / 'paired_contribution.csv'):
        pair_groups[r['architecture'], r['scenario'], r['run']].append(r)
    pair_summary = []
    for k, matches in sorted(pair_groups.items()):
        paired = [r for r in matches if r['paired_net_delta']]
        assert all(D(r['paired_net_delta']) == 0 for r in paired), 'Entry-only MTF changed common-entry payoff'
        pair_summary.append(dict(zip(('architecture', 'scenario', 'run'), k)) | {
            'common_signal_entries': len(matches), 'same_entry_both_known': len(paired),
            'excluded_unknown_or_changed_entry': len(matches) - len(paired), 'paired_net_delta': sum((D(r['paired_net_delta']) for r in paired), ZERO),
            'interpretation': 'MTF selects opportunities; identical entered trades retain M5 economics. Not additive profit attribution.'})
    for name, records in (('architecture_comparison.csv', comparisons), ('entry_retention.csv', retention),
        ('monthly_results.csv', [r for r in metric if r['group'] == 'MONTH']), ('direction_results.csv', directions),
        ('exit_counts.csv', exits), ('R_distribution.csv', bins), ('concentration.csv', concentration), ('paired_summary.csv', pair_summary)):
        write_csv(folder / name, records)
    verdict = {'VWAP_MR': 'NO ECONOMIC BASELINE PASS / REJECT CANDIDATE',
               'MOMENTUM': 'NO ECONOMIC BASELINE PASS / REJECT CANDIDATE',
               'scope': 'Final bounded assessed M5/MTF architectures, not proof about every conceivable strategy',
               'MTF': 'COMPLETE; derived readiness PASS, native delivery remains blocked but unused',
               'annual_metrics': 'Full annual Net/PF/DD remain null: incomplete calendar and/or unknown paths; no PASS',
               'external_acceptance': 'Pending independent user audit; internal verifier is a distinct algorithm',
               'next_candidate': 'Volatility Squeeze Breakout recommended only; unimplemented, wait separate user decision',
               'Stage3': 'NOT STARTED'}
    (folder / 'final_assessment.json').write_text(encoded(verdict))
    checksums(folder)
    print('64 primary comparisons, all monthly directions/scenarios, retention, R, exits, concentration and verdicts')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--folder', type=Path, default=DEST)
    review(p.parse_args().folder)
