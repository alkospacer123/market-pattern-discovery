"""SHA-pinned offline reference using the SAME calculation as the operator card.

The 10:00..17:45 research schedule is not a FINAM calendar. Incomplete observed
sessions remain in windows. TRUE OOS 2025 is excluded BEFORE feature ingestion;
windows never cross that exclusion. Source CSVs remain read-only, outside repo.
"""
from __future__ import annotations
import argparse
import collections
import csv
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from .market_suitability import CompletedSession, M15Bar, evaluate_market_card, METRIC_SCHEMA

SOURCE_SHA256 = {
    'USDRUBF': 'fef80630080a4e2a5e968d620b663f51acd1b7ab9d5d326a42c68cf2b80c67b8',
    'CNYRUBF': '259298733d1528c0d917b100118896009519a9f08bdad33d4b373d9ce86f99b4',
    'GLDRUBF': '7381d672485b5687ca2c4d92aa5960c24bb132f527589bae3c622b2dfa20a83d',
    'IMOEXF': 'a1b9fa6102a955103d61b28e81533ed19de68117e30fd84ceb53e8e617559773',
}
METRICS = ('atr14_pct_close', 'directional_efficiency', 'continuation_rate',
           'pressure_direction_alignment', 'range_compression_ratio',
           'inside_release_continuation_rate')


def load_sessions(directory, sym):
    path = directory / sym / (sym + '_M15.csv')
    if not path.exists():
        path = directory / (sym + '_M15.csv')
    if hashlib.sha256(path.read_bytes()).hexdigest() != SOURCE_SHA256[sym]:
        raise ValueError('FROZEN_INPUT_SHA_MISMATCH: ' + sym)
    daily = collections.defaultdict(list)
    with path.open(encoding='utf-8', newline='') as stream:
        for row in csv.DictReader(stream, delimiter=';'):
            # Do not parse locked year's prices, volumes or features.
            if row['Datetime'].startswith('2025-'):
                continue
            dt = datetime.strptime(row['Datetime'], '%Y-%m-%d %H:%M:%S')
            if 10 <= dt.hour < 18:
                daily[dt.date()].append(M15Bar(dt, *[float(row[k]) for k in
                                                   ('Open', 'High', 'Low', 'Close', 'Volume')]))
    sessions = []
    for day, bars in sorted(daily.items()):
        expected = tuple(datetime.combine(day, datetime.min.time()).replace(hour=10)
                         + timedelta(minutes=15*i) for i in range(32))
        sessions.append(CompletedSession(day, expected, tuple(bars), expected[-1]+timedelta(minutes=15)))
    return sessions


def card_windows(sessions, symbol):
    for i in range(19, len(sessions)):
        window = sessions[i-19:i+1]
        if window[0].day.year < 2025 < window[-1].day.year:
            continue
        card = evaluate_market_card(symbol, window, as_of=window[-1].closed_at,
                                    expected_session_days=[s.day for s in window])
        yield window[-1].day, card


def regime(window):
    """Public adapter: no independent proxy formulas or implicit missing-day drop."""
    card = evaluate_market_card('REFERENCE', window, as_of=window[-1].closed_at,
                                expected_session_days=[s.day for s in window])
    if card['strategies']['SHALLOW_PULLBACK']['suitability'] == 'НЕДОСТАТОЧНО ДАННЫХ':
        return {metric: None for metric in METRICS}
    values = dict(card['strategies']['SHALLOW_PULLBACK']['diagnostics'])
    values.update(card['strategies']['INSIDE_DAY_RELEASE']['diagnostics'])
    return {metric: values[metric] for metric in METRICS}


def quantiles(numbers):
    if not numbers:
        return None
    numbers = sorted(numbers)
    result = []
    for q in (.1, .25, .5, .75, .9):
        pos = (len(numbers)-1)*q
        lo = int(pos)
        result.append(round(numbers[lo]+(numbers[min(lo+1,len(numbers)-1)]-numbers[lo])*(pos-lo), 7))
    return result


def build(directory):
    report = {'schema': 'v20.market_reference.descriptive.v2', 'metric_schema': METRIC_SCHEMA,
              'status': 'DESCRIPTIVE_ONLY_NO_SUITABILITY_LABEL',
              'locked_year_excluded': 2025, 'session_window': 20,
              'research_open_labels': '10:00-17:45 MSK (32 M15); observed dates only',
              'source_sha256': SOURCE_SHA256, 'not_a_trading_gate': True,
              'outcome_association': 'NOT_VALIDATED', 'instrument': {}}
    for sym in SOURCE_SHA256:
        sessions = load_sessions(directory, sym)
        windows = list(card_windows(sessions, sym))
        by_year = {}
        for year in (2023, 2024, 2026):
            cards = [c for d,c in windows if d.year == year]
            complete = [c for c in cards if c['strategies']['SHALLOW_PULLBACK']['diagnostics']]
            if cards:
                by_year[str(year)] = {'candidate_windows': len(cards), 'complete_windows': len(complete),
                    'metric_quantiles': {m: quantiles([c['strategies']['INSIDE_DAY_RELEASE']['diagnostics'][m]
                        for c in complete if c['strategies']['INSIDE_DAY_RELEASE']['diagnostics'][m] is not None])
                        for m in METRICS}}
        report['instrument'][sym] = {'observed_sessions_excluding_2025': len(sessions), 'by_year': by_year}
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description='Offline V20 descriptive market baseline')
    parser.add_argument('--data-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    args.output.write_text(json.dumps(build(args.data_dir), ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    print('DESCRIPTIVE_ONLY_NO_SUITABILITY_LABEL', args.output)


if __name__ == '__main__':
    main()
