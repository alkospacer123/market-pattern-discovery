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
