"""V20-04.2 SHA-pinned historical M15 descriptive reference, READONLY.

Data: market-pattern-data/forever/<symbol>/<symbol>_M15.csv.
Only 32 fully observed bars 10:00..17:45, 20 consecutive observed sessions.
NO broker, NO strategy parameter fitting, NO three-state suitability labels.
"""
from __future__ import annotations
import argparse
import collections
import csv
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np

SOURCE_SHA256 = {
    'USDRUBF': 'fef80630080a4e2a5e968d620b663f51acd1b7ab9d5d326a42c68cf2b80c67b8',
    'CNYRUBF': '259298733d1528c0d917b100118896009519a9f08bdad33d4b373d9ce86f99b4',
    'GLDRUBF': '7381d672485b5687ca2c4d92aa5960c24bb132f527589bae3c622b2dfa20a83d',
    'IMOEXF': 'a1b9fa6102a955103d61b28e81533ed19de68117e30fd84ceb53e8e617559773',
}
METRICS = ('atr14_pct_close', 'session_efficiency_ratio',
           'continuation_rate', 'signed_volume_pressure_abs',
           'inside_session_share')


def load_sessions(directory, sym):
    path = directory / (sym + '_M15.csv')
    if hashlib.sha256(path.read_bytes()).hexdigest() != SOURCE_SHA256[sym]:
        raise ValueError('FROZEN_INPUT_SHA_MISMATCH: ' + sym)
    daily = collections.defaultdict(list)
    with path.open(encoding='utf-8', newline='') as stream:
        for row in csv.DictReader(stream, delimiter=';'):
            dt = datetime.strptime(row['Datetime'], '%Y-%m-%d %H:%M:%S')
            if 10 <= dt.hour < 18 and dt.minute % 15 == 0:
                daily[dt.date()].append((dt, *[float(row[k]) for k in
                                               ('Open', 'High', 'Low', 'Close', 'Volume')]))
    full, missing = [], []
    for day in sorted(daily):
        bars = daily[day]
        expected = [datetime(day.year, day.month, day.day, 10)
                    + timedelta(minutes=15*i) for i in range(32)]
        if [b[0] for b in bars] == expected:
            full.append((day, bars))
        else:
            missing.append((str(day), len(bars)))
    return full, missing


def regime(window):
    bars = [bar for _, session_bars in window for bar in session_bars]
    prev = None
    trs = []
    for t, o, h, l, c, v in bars:
        trs.append(h-l if prev is None else max(h-l, abs(h-prev), abs(l-prev)))
        prev = c
    atr = sum(trs[:14]) / 14
    for value in trs[14:]:
        atr = (13*atr+value)/14
    closes = [session_bars[-1][4] for _, session_bars in window]
    traveled = sum(abs(b-a) for a,b in zip(closes,closes[1:]))
    eff = abs(closes[-1]-closes[0])/traveled if traveled else 0
    history = []
    events = continued = 0
    for _, session_bars in window:
        for i, bar in enumerate(session_bars):
            if len(history) >= 20 and i+1 < len(session_bars):
                side = (1 if bar[4] > max(x[2] for x in history[-20:])
                        else -1 if bar[4] < min(x[3] for x in history[-20:])
                        else 0)
                if side:
                    events += 1
                    if (session_bars[i+1][4] - bar[4])*side > 0:
                        continued += 1
            history.append(bar)
    up = sum(b[5] for b in bars if b[4] > b[1])
    down = sum(b[5] for b in bars if b[4] < b[1])
    inside = sum(
        max(x[2] for x in newer) <= max(x[2] for x in older)
        and min(x[3] for x in newer) >= min(x[3] for x in older)
        for (_, older), (_, newer) in zip(window, window[1:]))
    return {
        'atr14_pct_close': atr/bars[-1][4],
        'session_efficiency_ratio': eff,
        'continuation_rate': continued/events if events else None,
        'signed_volume_pressure_abs': abs(up-down)/(up+down) if up+down else None,
        'inside_session_share': inside/19,
    }


def quantiles(numbers):
    if not numbers:
        return None
    return [round(float(x),7) for x in np.quantile(numbers, (.1,.25,.5,.75,.9))]


def build(directory):
    report = {'schema':'v20.market_reference.descriptive.v1',
              'status':'DESCRIPTIVE_ONLY_NO_SUITABILITY_LABEL',
              'years':'2023-2026_YTD', 'session_window':20,
              'research_open_labels':'10:00-17:45 MSK (32 M15)',
              'source_sha256':SOURCE_SHA256, 'not_a_trading_gate':True,
              'outcome_association':'NOT_VALIDATED', 'instrument':{}}
    for sym in SOURCE_SHA256:
        sessions, incomplete = load_sessions(directory,sym)
        windows = [{'year':str(sessions[i][0].year),
                    **regime(sessions[i-19:i+1])}
                   for i in range(19,len(sessions))]
        by_year = {}
        for year in ('2023','2024','2025','2026'):
            rows = [r for r in windows if r['year']==year]
            if rows:
                by_year[year] = {'windows':len(rows),
                    'metric_quantiles':{metric:quantiles([r[metric] for r in rows
                                                         if r[metric] is not None])
                                        for metric in METRICS}}
        report['instrument'][sym] = {
            'first':str(sessions[0][0]),'last':str(sessions[-1][0]),
            'complete_sessions':len(sessions),
            'excluded_incomplete_sessions':len(incomplete),
            'complete_20_session_windows':len(windows),
            'by_year':by_year}
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description='Offline V20 descriptive market baseline')
    parser.add_argument('--data-dir',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args(argv)
    args.output.write_text(json.dumps(build(args.data_dir),ensure_ascii=False,indent=2),
                           encoding='utf-8')
    print('DESCRIPTIVE_ONLY_NO_SUITABILITY_LABEL',args.output)


if __name__=='__main__':
    main()
