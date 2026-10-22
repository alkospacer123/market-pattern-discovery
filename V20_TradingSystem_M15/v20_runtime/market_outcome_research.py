"""V20-04.2 offline attribution; published RAW_SIGNAL rows, never trade selection.

No fitting, PF, classification thresholds, broker or strategy replay. 2025 prices
are excluded before ingestion. Published aggregates are checked without treating
an already researched period as a new OOS. Source candles are never copied.
"""
from __future__ import annotations
import argparse
from bisect import bisect_left
from collections import Counter, defaultdict
import csv
from datetime import datetime, timedelta
import hashlib
import json
from math import isclose, sqrt
from pathlib import Path
from statistics import mean, median
from .market_suitability import STRATEGIES, clv_pressure_prior12, M15Bar, METRIC_SCHEMA, _compression_stats
from .market_reference_descriptive import SOURCE_SHA256, METRICS, load_sessions, card_windows

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT/'V20-03/comparison/QUOTE_PATH_DIAGNOSTICS.csv'
RAW_SHA = '1f936dca02b9c99ed1df6ca30ef52c4c33128c9d06743175b6f5d6f59dee9c0f'
PERIODS = ('2018-2022', '2023-2026')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def raw_rows(rows):
    return [r for r in rows if r['record_type'] == 'RAW_SIGNAL']


def contrast(rows):
    summaries = []
    for period in PERIODS:
        for strategy in (*STRATEGIES, 'ALL_INDEPENDENT_ACCOUNTS'):
            group = [r for r in rows if r['period'] == period and
                     (r['strategy'] == strategy or strategy == 'ALL_INDEPENDENT_ACCOUNTS')]
            observed = [r for r in group if r['horizon_status'] == 'OBSERVED_V1']
            summaries.append(dict(period=period, strategy=strategy, raw_signals=len(group),
                observed_horizons=len(observed), unverified_horizons=len(group)-len(observed),
                mean_horizon_R=mean(float(r['horizon_R']) for r in observed),
                median_horizon_R=median(float(r['horizon_R']) for r in observed),
                positive_horizon_share=mean(float(r['horizon_R']) > 0 for r in observed),
                stop_touch_share=mean(r['horizon_stop_touch']=='True' for r in observed),
                horizon_status_counts=dict(Counter(r['horizon_status'] for r in group))))
    return summaries


def _ranks(values):
    order = sorted(range(len(values)), key=values.__getitem__)
    result = [0.0]*len(values)
    i = 0
    while i < len(order):
        j = i+1
        while j < len(order) and values[order[j]] == values[order[i]]:
            j += 1
        for k in range(i,j):
            result[order[k]] = (i+j-1)/2
        i = j
    return result


def spearman(xs, ys):
    if len(xs) < 3:
        return None
    x, y = _ranks(xs), _ranks(ys)
    mx, my = mean(x), mean(y)
    denominator = sqrt(sum((v-mx)**2 for v in x)*sum((v-my)**2 for v in y))
    return sum((a-mx)*(b-my) for a,b in zip(x,y))/denominator if denominator else None


def associations(joined):
    output = []
    for strategy in STRATEGIES:
        for block in ('2023-2024', '2026_YTD'):
            group = [r for r in joined if r['strategy']==strategy and r['block']==block]
            for metric in METRICS:
                q = [r for r in group if r['features'].get(metric) is not None]
                xs, ys = [r['features'][metric] for r in q], [r['horizon_R'] for r in q]
                pos = [r['features'][metric] for r in q if r['horizon_R']>0]
                neg = [r['features'][metric] for r in q if r['horizon_R']<=0]
                output.append(dict(strategy=strategy, block=block, metric=metric, signals=len(q),
                    instrument_sessions=len({(r['symbol'],r['signal_day']) for r in q}),
                    median_feature=median(xs) if xs else None,
                    median_positive_horizon=median(pos) if pos else None,
                    median_nonpositive_horizon=median(neg) if neg else None,
                    spearman_horizon_R=spearman(xs,ys)))
    return output


def build(data_dir):
    assert sha(RAW_PATH)==RAW_SHA, 'PUBLISHED_RAW_ARTIFACT_CHANGED'
    with RAW_PATH.open() as f:
        rows = raw_rows(csv.DictReader(f))
    summary = contrast(rows)
    distribution_path = ROOT/'V20-03/comparison/TRADE_DISTRIBUTION.csv'
    with distribution_path.open() as f:
        published = [r for r in csv.DictReader(f) if r['record_type']=='RAW_FROZEN_SIGNALS'
                     and r['instrument']=='ALL' and r['year']=='ALL']
    for rec in summary:
        match = next(r for r in published if r['period']==rec['period'] and r['strategy']==rec['strategy'])
        assert int(match['observations'])==rec['raw_signals']
        assert int(match['horizon_observed_paths'])==rec['observed_horizons']
        assert isclose(float(match['mean_horizon_R']),rec['mean_horizon_R'],abs_tol=1e-10)
    cards, quote_index, coverage, source_sessions = {}, {}, {}, {}
    for sym in SOURCE_SHA256:
        sessions = load_sessions(data_dir,sym)  # SHA verified; locked year excluded.
        source_sessions[sym] = (sessions,{s.day:i for i,s in enumerate(sessions)})
        by_day = dict(card_windows(sessions,sym))
        cards[sym] = by_day
        coverage[sym] = dict(observed_sessions_excluding_2025=len(sessions),
                            incomplete_observed_sessions=sum(len(s.bars)!=32 for s in sessions),
                            candidate_windows=len(by_day),
                            complete_windows=sum(bool(c['strategies']['SHALLOW_PULLBACK']['diagnostics']) for c in by_day.values()))
        # Independent quote checks use all source hours, never 2025 numeric fields.
        path = data_dir/sym/(sym+'_M15.csv')
        if not path.exists():
            path = data_dir/(sym+'_M15.csv')
        bars = []
        with path.open() as f:
            for r in csv.DictReader(f,delimiter=';'):
                if r['Datetime'].startswith('2025-'):
                    continue
                bars.append(M15Bar(datetime.fromisoformat(r['Datetime']),
                                   *[float(r[k]) for k in ('Open','High','Low','Close','Volume')]))
        quote_index[sym] = (bars,{b.open_time:i for i,b in enumerate(bars)})
        print('source/card',sym,coverage[sym],flush=True)
    joined, skipped, quote_checks, pressure_checks, inside_checks = [], Counter(), 0, 0, 0
    for r in rows:
        if r['period'] != '2023-2026':
            skipped['OLD_SOURCE_QUOTES_UNAVAILABLE'] += 1
            continue
        signal = datetime.fromisoformat(r['signal_bar_dt'])
        if signal.year==2025 or r['horizon_exit_dt'].startswith('2025-'):
            skipped['LOCKED_2025'] += 1
            continue
        if r['horizon_status']!='OBSERVED_V1':
            skipped['UNVERIFIED_HORIZON'] += 1
            continue
        sym = r['instrument']
        bars, lookup = quote_index[sym]
        en, ex = (lookup[datetime.fromisoformat(r[k])] for k in ('entry_dt','horizon_exit_dt'))
        assert isclose(bars[en].open,float(r['entry']),rel_tol=1e-10,abs_tol=1e-8)
        calculated = int(r['side'])*(bars[ex].open-bars[en].open)/float(r['risk'])
        assert isclose(calculated,float(r['horizon_R']),rel_tol=1e-9,abs_tol=1e-8)
        quote_checks += 1
        sg = lookup[signal]
        prior = bars[max(0,sg-12):sg+1]
        if len(prior)==13 and not (prior[0].open_time.year<2025<signal.year):
            assert isclose(clv_pressure_prior12(prior),float(r['signal_pressure']),abs_tol=1e-10)
            pressure_checks += 1
        day = (signal-timedelta(hours=9)).date()
        if r['strategy']=='INSIDE_DAY_RELEASE':
            sessions, day_lookup = source_sessions[sym]
            day_ix = day_lookup[day]
            pair = sessions[max(0,day_ix-2):day_ix]
            if len(pair)==2 and not (pair[0].day.year<2025<day.year):
                diagnostic = _compression_stats(pair)
                assert diagnostic['valid_day_pairs']==1 and diagnostic['latest_pair_strict_inside'] is True
                level = (max(b.high for b in pair[-1].bars) if int(r['side'])==1
                         else min(b.low for b in pair[-1].bars))
                assert int(r['side'])*(bars[sg].close-level)>0
                assert int(r['side'])*(bars[sg-1].close-level)<=0
                inside_checks += 1
        dates = sorted(cards[sym])
        ix = bisect_left(dates,day)-1
        if ix<0:
            skipped['NO_PRIOR_20_SESSION_WINDOW'] += 1
            continue
        end = dates[ix]
        if signal.year>2025 and end.year<2025:
            skipped['WINDOW_WOULD_CROSS_LOCKED_YEAR'] += 1
            continue
        card = cards[sym][end]
        assert datetime.fromisoformat(card['as_of_msk']) < signal
        diagnostics = card['strategies']['INSIDE_DAY_RELEASE']['diagnostics']
        if not diagnostics:
            skipped['INCOMPLETE_PRIOR_WINDOW'] += 1
            continue
        # No outcome is passed into the card calculator. Targets are added here.
        joined.append(dict(strategy=r['strategy'],symbol=sym,signal_day=str(day),
            block='2026_YTD' if signal.year==2026 else '2023-2024',
            cutoff=card['as_of_msk'],horizon_R=float(r['horizon_R']),
            features={m:diagnostics[m] for m in METRICS}))
    assert len(joined)+sum(skipped.values())==len(rows)
    assoc = associations(joined)
    # Old rows expose only source ATR and source pressure. Do not invent the
    # other three card groups from executed trades or from economic proxies.
    table = []
    for period in PERIODS:
        for strategy in STRATEGIES:
            q = [r for r in rows if r['period']==period and r['strategy']==strategy
                 and r['horizon_status']=='OBSERVED_V1'
                 and (period=='2018-2022' or (not r['signal_bar_dt'].startswith('2025-')
                                             and not r['horizon_exit_dt'].startswith('2025-')))]
            late = [r for r in joined if r['strategy']==strategy]
            for metric in METRICS:
                values = ([r['features'][metric] for r in late if r['features'][metric] is not None]
                          if period=='2023-2026' else [])
                table.append(dict(period=period,strategy=strategy,metric=metric,
                    card_feature_signals=len(values),card_feature_median=median(values) if values else None,
                    coverage='LAGGED_COMPLETE_WINDOW_EXCLUDING_2025' if period=='2023-2026' else 'NO_OLD_QUOTES_FOR_CARD',
                    published_signal_ATR_pct_median=median(float(r['ATR14_price_pct']) for r in q),
                    published_side_times_pressure_median=median(int(r['side'])*float(r['signal_pressure']) for r in q)))
    return dict(schema='v20.market_outcome.research.v2',metric_schema=METRIC_SCHEMA,
        status='EXPLORATORY_NO_VALIDATED_CLASSIFICATION',locked_feature_year=2025,
        raw_contrast=summary,five_group_table=table,associations=assoc,
        joined_signals=len(joined),skipped=dict(skipped),coverage=coverage,
        quote_horizon_checks=quote_checks,source_clv_checks=pressure_checks,
        source_inside_pair_and_cross_checks=inside_checks,
        source_sha256={str(RAW_PATH.relative_to(ROOT)):RAW_SHA,
                       str(distribution_path.relative_to(ROOT)):sha(distribution_path),**SOURCE_SHA256},
        notes=['Observed-date research schedule; FINAM calendar and wholly absent days unverified',
               'Signals/windows overlap; correlations are descriptive, no iid significance claim',
               '2026 diagnostic temporal control, already researched; not independent OOS',
               'No PF, thresholds, parameter search or original 1589 ledger parity claim'])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args(argv)
    report = build(args.data_dir)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(report['status'], 'joined',report['joined_signals'],'skipped',report['skipped'])


if __name__=='__main__':
    main()
