"""One fixed p25/p75 descriptive check, and readonly annotations for the V20 card.

No strategy selection, PF, fitting alternatives or validated suitability profile.
See V20-04/MARKET_CARD_RANGES_PROTOCOL_RU.md. Do not extend this experiment.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
import csv
from datetime import date, datetime, timedelta
import json
from math import isfinite
from pathlib import Path
from statistics import mean, median
from .market_suitability import METRIC_SCHEMA

SCHEMA = 'v20.market_ranges.descriptive.v1'
DEFAULT_RANGES = Path(__file__).resolve().parents[1]/'V20-04/MARKET_CARD_TYPICAL_RANGES.json'
# One shared ATR, exactly one preselected specific metric per frozen strategy.
CHECKS = {
    'COMMON_ATR': ('ALL', 'atr14_pct_close', 'ATR/Close'),
    'SHALLOW_PULLBACK': ('SHALLOW_PULLBACK', 'continuation_rate', 'Продолжение пробоев'),
    'OBV_PRESSURE': ('OBV_PRESSURE', 'pressure_direction_alignment', 'Согласованность давления'),
    'INSIDE_DAY_RELEASE': ('INSIDE_DAY_RELEASE', 'range_compression_ratio', 'Сжатие диапазона'),
}
BUCKETS = ('НИЖЕ', 'ВНУТРИ', 'ВЫШЕ')
PERIODS = ('2023-2024', '2026_YTD')
MIN_BASE = 40
MIN_BUCKET = 10


def _number(value):
    return isinstance(value, (float,int)) and not isinstance(value,bool) and isfinite(value)


def percentile(values, q):
    values = sorted(values)
    pos = (len(values)-1)*q
    low = int(pos)
    return values[low]+(values[min(low+1,len(values)-1)]-values[low])*(pos-low)


def bucket(value, low, high):
    if not _number(value):
        return 'НЕИЗВЕСТНО'
    if not (_number(low) and _number(high) and low<high):
        raise ValueError('INVALID_DESCRIPTIVE_RANGE')
    return 'НИЖЕ' if value<low else 'ВЫШЕ' if value>high else 'ВНУТРИ'


def validate_observations(rows):
    for row in rows:
        day = date.fromisoformat(row['signal_day'])
        signal = datetime.fromisoformat(row['signal_dt'])
        cutoff = datetime.fromisoformat(row['cutoff'])
        outcome = datetime.fromisoformat(row['outcome_at'])
        if any(t.tzinfo is not None for t in (signal,cutoff,outcome)):
            raise ValueError('MOSCOW_NAIVE_REQUIRED')
        if (day.year==2025 or cutoff.year==2025 or outcome.year==2025
                or cutoff.year<2025<day.year):
            raise ValueError('LOCKED_2025_OBSERVATION')
        if day.year not in (2023,2024,2026):
            raise ValueError('OUTSIDE_PREDECLARED_PERIODS')
        expected = '2026_YTD' if day.year==2026 else '2023-2024'
        if (row['block']!=expected or (signal-timedelta(hours=9)).date()!=day
                or cutoff.date()>=day or cutoff>=signal or outcome<=signal):
            raise ValueError('NON_CAUSAL_OBSERVATION')


def _selected(rows, check, period):
    strategy, metric, _ = CHECKS[check]
    years = ('2023','2024') if period=='2023-2024' else ('2026',)
    return [r for r in rows if r['block']==period and r['signal_day'][:4] in years and
            (strategy=='ALL' or r['strategy']==strategy) and _number(r['features'].get(metric))]


def calibrate_ranges(rows):
    """Only 2023/24 feature distributions; never read an outcome or 2026 feature."""
    ranges = {}
    for check, (_,metric,label) in CHECKS.items():
        base = _selected(rows, check, '2023-2024')
        values = [r['features'][metric] for r in base]
        low, high = (percentile(values,.25),percentile(values,.75)) if values else (None,None)
        ranges[check] = dict(metric=metric,label=label,n=len(base),p25=low,p75=high,
                            base_status='ОПИСАТЕЛЬНЫЙ' if len(base)>=MIN_BASE and low<high else 'НЕ ПРОВЕРЕНО')
    return dict(schema=SCHEMA,metric_schema=METRIC_SCHEMA,
        calibration_start='2023-01-01',calibration_end='2024-12-31',
        boundaries_available_from_msk='2025-01-01T00:00:00',
        source_universe=sorted({r['symbol'] for r in rows if r['block']=='2023-2024'
                               and r['signal_day'][:4] in ('2023','2024')}),
        percentiles=[.25,.75],min_base=MIN_BASE,min_bucket=MIN_BUCKET,
        ranges=ranges,not_a_suitability_profile=True,independent_holdout=False,
        session_calendar='OBSERVED_DATES_NOT_FINAM_VERIFIED',affects_signals_or_risk=False)


def summarize(rows):
    values = [r['horizon_R'] for r in rows]
    if any(not _number(v) for v in values) or any(type(r['horizon_stop_touch']) is not bool for r in rows):
        raise ValueError('INVALID_PUBLISHED_OUTCOME')
    return dict(n=len(rows),instrument_sessions=len({(r['symbol'],r['signal_day']) for r in rows}),
        mean_horizon_R=mean(values) if values else None,median_horizon_R=median(values) if values else None,
        positive_share=mean(v>0 for v in values) if values else None,
        stop_touch_share=mean(r['horizon_stop_touch'] for r in rows) if rows else None,
        sample_status='N>=10' if len(rows)>=MIN_BUCKET else 'МАЛО ДАННЫХ')


def evaluate_ranges(rows, profile):
    """Use the already frozen bounds in both periods and every instrument."""
    table, checks = [], {}
    for check, spec in profile['ranges'].items():
        for period in PERIODS:
            selected = _selected(rows,check,period)
            for symbol in ('ALL',*profile['source_universe']):
                group = selected if symbol=='ALL' else [r for r in selected if r['symbol']==symbol]
                for position in BUCKETS:
                    members = [r for r in group if spec['base_status']=='ОПИСАТЕЛЬНЫЙ'
                               and bucket(r['features'][spec['metric']],spec['p25'],spec['p75'])==position]
                    table.append(dict(check=check,metric=spec['metric'],period=period,symbol=symbol,
                                      bucket=position,**summarize(members)))
        periods = {}
        for period in PERIODS:
            q = {r['bucket']:r for r in table if r['check']==check and r['period']==period and r['symbol']=='ALL'}
            adequate = spec['base_status']=='ОПИСАТЕЛЬНЫЙ' and all(r['n']>=MIN_BUCKET for r in q.values())
            inside = q['ВНУТРИ']
            better = adequate and all(inside[k]>max(q[b][k] for b in ('НИЖЕ','ВЫШЕ'))
                                     for k in ('mean_horizon_R','median_horizon_R'))
            periods[period] = dict(adequate=adequate,inside_better_mean_and_median=better)
        stable = all(p['inside_better_mean_and_median'] for p in periods.values())
        checks[check] = dict(periods=periods,
            interval_hypothesis='ПОДТВЕРЖДЕНО ОПИСАТЕЛЬНО' if stable else 'НЕ ПОДТВЕРЖДЕНО',
            suitability='НЕ ОЦЕНЕНО')
    return table, checks


def annotate_card(card, profile):
    """Describe typical location; NEVER set suitability or reference evidence."""
    result = deepcopy(card)
    if profile.get('schema')!=SCHEMA or profile.get('metric_schema')!=METRIC_SCHEMA:
        raise ValueError('DESCRIPTIVE_RANGE_SCHEMA_INVALID')
    as_of = datetime.fromisoformat(card['as_of_msk'])
    available = datetime.fromisoformat(profile['boundaries_available_from_msk'])
    if available.tzinfo is not None or as_of<available:
        result['typical_ranges'] = {'state':'CALIBRATION_NOT_YET_AVAILABLE'}
        return result
    summaries = {}
    for check in CHECKS:
        spec = profile['ranges'][check]
        if check=='COMMON_ATR':
            value = card['metrics']['volatility']['atr14_pct_close']
        else:
            value = card['strategies'][check]['diagnostics'].get(spec['metric'])
        position = (bucket(value,spec['p25'],spec['p75']) if spec['base_status']=='ОПИСАТЕЛЬНЫЙ' else 'НЕ ПРОВЕРЕНО')
        summaries[check] = dict(metric=spec['metric'],label=spec['label'],value=value,
                               p25=spec['p25'],p75=spec['p75'],position=position)
    result['typical_ranges'] = dict(state='DESCRIPTIVE_ONLY',calibration='2023–2024',
        source_universe=profile['source_universe'],
        symbol_in_reference=card['symbol'] in profile['source_universe'],
        evidence='Типичный диапазон не подтверждает пригодность.',values=summaries)
    # The final check result itself must also have been observable at this time.
    if as_of>=datetime.fromisoformat(profile['outcomes_observed_through_msk']):
        result['typical_ranges']['interval_check'] = {k:v['interval_hypothesis'] for k,v in profile['checks'].items()}
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--observations',type=Path,required=True)
    parser.add_argument('--ranges-output',type=Path,required=True)
    parser.add_argument('--table-output',type=Path,required=True)
    args = parser.parse_args(argv)
    data = json.loads(args.observations.read_text())
    rows = data['observations']
    validate_observations(rows)
    profile = calibrate_ranges(rows)
    # Persist the declared feature-only boundaries BEFORE evaluating outcomes.
    args.ranges_output.write_text(json.dumps(profile,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print('FROZEN_P25_P75',json.dumps(profile['ranges'],ensure_ascii=False),flush=True)
    table, checks = evaluate_ranges(rows,profile)
    profile.update(checks=checks,source_sha256=data['source_sha256'],observations=len(rows),
        outcomes_observed_through_msk=max(r['outcome_at'] for r in rows),
        research_status='ЗАВЕРШЕНО — БЕЗ ДАЛЬНЕЙШЕГО ПОДБОРА')
    args.ranges_output.write_text(json.dumps(profile,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    with args.table_output.open('w',newline='') as stream:
        writer = csv.DictWriter(stream,fieldnames=list(table[0]),lineterminator='\n')
        writer.writeheader()
        writer.writerows(table)
    print('ONE_CHECK_COMPLETE',json.dumps(checks,ensure_ascii=False),flush=True)


if __name__=='__main__':
    main()
