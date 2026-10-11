"""Common serialization, source coverage and report tables."""
import csv
from datetime import date, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

from .metrics import summarize


def encoded(value):
    if isinstance(value, (Decimal, date, datetime)):
        return str(value)
    if isinstance(value, Path):
        return str(value)
    raise TypeError(type(value))


def dump(path, value):
    path.write_text(json.dumps(value, default=encoded, indent=2, sort_keys=True,
                               ensure_ascii=False, allow_nan=False)+'\n')


def csv_write(path, rows):
    columns = sorted({k for row in rows for k in row})
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, lineterminator='\n')
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, sort_keys=True, default=encoded)
                             if isinstance(v, (dict, list)) else v for k, v in row.items()})


def coverage(symbol, rows, config, rules):
    daily, gaps = [], []
    first = min(rows).date()
    step = timedelta(minutes=config['timeframe_minutes'])
    day = date.fromisoformat(config['start'])
    end = date.fromisoformat(config['end_exclusive'])
    while day < end:
        source = [b for at, b in rows.items() if at.date()==day]
        windows = rules.windows(day)
        if windows:
            expected = []
            if day >= first:
                for a, z in windows:
                    at = a
                    while at < z:
                        expected.append(at)
                        at += step
            missing = [at for at in expected if at not in rows]
            invalid = [at for at in expected if at in rows and not rows[at].valid]
            good = len(expected)-len(missing)-len(invalid)
            origin = rules.at(day, '10:00')
            or_ok = all(at in rows and rows[at].valid for at in (origin, origin+step, origin+2*step))
            daily.append(dict(instrument=symbol, date=str(day),
                              status='PRE_INCEPTION' if day < first else 'INCOMPLETE' if missing or invalid else 'COMPLETE',
                              expected_bars=len(expected), valid_bars=good,
                              missing_bars=len(missing), invalid_bars=len(invalid),
                              source_rows_all_sessions=len(source),
                              source_rows_outside_research_windows=sum(not any(a <= b.start < z for a,z in windows) for b in source),
                              or_available=or_ok,
                              source_cause='KNOWN_EXCHANGE_HALT_2023_09_13; grid unchanged' if day==date(2023,9,13) else 'UNPROVEN; absence is not a missed trade'))
            for at in missing+invalid:
                gaps.append(dict(instrument=symbol, start=at, close=at+step,
                                 reason='MISSING_EXPECTED_RESEARCH_SLOT' if at not in rows else rows[at].problem,
                                 source_cause='KNOWN_EXCHANGE_HALT' if day==date(2023,9,13) else 'NOT_ESTABLISHED',
                                 missed_trade_proven=False))
        day += timedelta(days=1)
    return daily, gaps


def table_row(symbol, cohort, signals, source, **labels):
    m = summarize(cohort, signals, source)
    d = m['conditional_closed_only_C1']
    observed = any(c['valid_bars'] > 0 for c in source)
    classification = ('NO_COVERAGE' if not observed else 'UNKNOWN' if m['unknown'] else
                      'PARTIAL_DATA' if any(c['status'] != 'COMPLETE' for c in source) else
                      'CONDITIONAL_AFTER_UNKNOWN' if any(t.get('prior_unknown_requires_flat_assumption') for t in cohort) else
                      'COMPLETE_MODEL_COHORT')
    return dict(instrument=symbol, **labels,
                signals=m['signals'], admitted_orders=m['admitted_orders'],
                model_fills=m['model_fills'], closed=m['closed'], unknown=m['unknown'],
                complete_days=sum(c['status']=='COMPLETE' for c in source),
                incomplete_days=sum(c['status']=='INCOMPLETE' for c in source),
                pre_inception_days=sum(c['status']=='PRE_INCEPTION' for c in source),
                cohort_complete=m['annual_complete'], complete_cohort_metrics=m['annual'],
                coverage_classification=classification,
                diagnostic_scope='conditional known closures; no continuous equity claim',
                **{f'conditional_{k}': d[k] if observed else None for k in ('PF_C1_price', 'PF_C1_R', 'Net_R', 'Expectancy_R', 'Win_Rate', 'Max_DD_R')},
                status=m['status'], economic_diagnostic=m['economic_diagnostic'])


def data_quality_coverage(market_data, config, rules, result):
    """Every declared research slot, including days before source inception."""
    result.validate()
    if config['timeframe_minutes'] != 5:
        raise ValueError('DATA_GAP_SKIP_V2_REQUIRES_M5')
    daily = []
    step = timedelta(minutes=5)
    day = date.fromisoformat(config['start'])
    end = date.fromisoformat(config['end_exclusive'])
    if day >= end or end > date(2024, 1, 1):
        raise ValueError('Only approved development dates through 2023')
    day_records = {(d['instrument'], d['date']):d for d in result.days}
    for symbol in config['instruments']:
        rows = market_data[symbol]
        first = min(rows).date() if rows else end
        current_day = day
        while current_day < end:
            expected = []
            for a, z in rules.windows(current_day):
                while a < z:
                    expected.append(a)
                    a += step
            if expected:
                missing = sum(at not in rows for at in expected)
                invalid = sum(at in rows and not rows[at].valid for at in expected)
                d = day_records.get((symbol, str(current_day)), {})
                daily.append(dict(instrument=symbol, date=str(current_day),
                    status='PRE_INCEPTION' if current_day < first else
                           'INCOMPLETE' if missing or invalid else 'COMPLETE',
                    expected_bars=len(expected), valid_bars=len(expected)-missing-invalid,
                    missing_bars=missing, invalid_bars=invalid,
                    accepted_entries=d.get('accepted_entries', 0), closed=d.get('closed', 0),
                    data_gap_skips=d.get('data_gap_skips', 0),
                    data_quality_excluded=d.get('data_quality_excluded', 0),
                    initial_flat_assumed=True, initial_flat_proven=False,
                    prior_exclusion_requires_flat_assumption=d.get('prior_exclusion_requires_flat_assumption', False),
                    remainder_of_day_blocked=d.get('remainder_of_day_blocked', False),
                    following_day_contract='CONDITIONAL_FLAT; not a proven real close'))
            current_day += timedelta(days=1)
    for key, ledger in (('closed', result.trades), ('data_gap_skips', result.data_gap_skips),
                        ('data_quality_excluded', result.data_quality_exclusions)):
        if sum(d[key] for d in daily) != len(ledger):
            raise ValueError('COVERAGE_LEDGER_RECONCILIATION '+key)
    if sum(d['accepted_entries'] for d in daily) != len(result.trades)+len(result.data_quality_exclusions):
        raise ValueError('COVERAGE_ACCEPTED_ENTRY_RECONCILIATION')
    return daily


def write_data_quality_reports(output, result, market_data, config, rules):
    """Write six prospective ledgers to a new directory; never rewrite history."""
    from .metrics import summarize_data_quality
    result.validate()
    lab = Path(__file__).resolve().parents[1]
    output = Path(output).resolve()
    if not any(output.is_relative_to((lab/p).resolve()) and output != (lab/p).resolve()
               for p in ('work', 'results')):
        raise ValueError('OUTPUT_OUTSIDE_INTRADAYLAB_SCOPE')
    if output.exists() and any(output.iterdir()):
        raise ValueError('IMMUTABLE_OUTPUT_EXISTS')
    source = data_quality_coverage(market_data, config, rules, result)
    metrics = summarize_data_quality(result, source)
    output.mkdir(parents=True, exist_ok=True)
    for name, rows, required in (
        ('trades', result.trades, ('signal_id','instrument','status','entry_at','entry_price','stop','take','net_c1')),
        ('signals', result.signals, ('signal_id','instrument','signal_at','status','reason','model_filled')),
        ('data_gap_skips', result.data_gap_skips, ('signal_id','instrument','signal_at','status','reason','attempted_execution_at','gap_detected_at')),
        ('data_quality_exclusions', result.data_quality_exclusions, ('signal_id','instrument','signal_at','status','entry_at','entry_price','stop','take','gap_interval_start','gap_interval_end','gap_detected_at','exclusion_reason')),
        ('coverage_report', source, ('instrument','date','status','expected_bars','valid_bars','missing_bars','invalid_bars','accepted_entries','closed','data_gap_skips','data_quality_excluded'))):
        if rows:
            csv_write(output/(name+'.csv'), rows)
        else:
            # Empty ledgers still have a readable schema, without a fake record.
            with (output/(name+'.csv')).open('w', newline='') as stream:
                csv.writer(stream, lineterminator='\n').writerow(sorted(required))
    dump(output/'metrics.json', metrics)
    return metrics
