#!/usr/bin/env python3
"""Deterministic hand-readable traces from independent reconstruction + source.

No primary Replay import. Real cases explicitly separated from synthetic rules.
"""
import argparse
from datetime import datetime as DT, timedelta as TD
from decimal import Decimal as D
import gzip
import json
from pathlib import Path

from audit_squeeze import load_source, table, m30, window, intervals, FIVE


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--data-root', type=Path, required=True)
    p.add_argument('--results', type=Path, required=True)
    p.add_argument('--audit-folder', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    assert not args.output.exists()
    data, _ = load_source(args.data_root)
    oracle = json.loads(gzip.decompress((args.audit_folder/'reconstructed.json.gz').read_bytes()))
    published = {name: table(args.results/f'{name}.csv.gz') for name in ('signals', 'trade_ledger')}
    out = ['# Squeeze v1 — independent manual traces', '',
           'All times MSK UTC+3. Source `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`; source row1 is header. Oracle uses raw source, weighted closed-form EMA/ATR, its own cycles/execution; published CSV is only the comparison target. Trace selection covers rules and does not select architectures. Real trades and synthetic boundary tests are labelled separately.', '']
    def get(symbol, architecture, delay):
        return oracle[str((symbol, architecture, delay))]
    def add_case(symbol, architecture, delay, sid, title):
        nonlocal out
        r = get(symbol, architecture, delay)
        s = next(x for x in r['signals'] if x['signal_id'] == sid)
        ledger = next((x for x in r['trade_ledger'] if x['signal_id'] == sid), None)
        idx = data[symbol]
        row_ids = {t: i+2 for i, t in enumerate(idx)}
        t = DT.fromisoformat(s['signal_at'])
        out.extend([f'## {title}: {symbol} / {architecture} / T{delay} / {sid}', '',
                    f"Signal={s['signal_at']}; delivered/decision={s['available_at']}; strictly future scheduled Open={s['planned_execution_at']}. Outcome={s['status']} / {s['reason']}.", '',
                    f"Frozen range [{s['range_low']}, {s['range_high']}] from {s['range_start']} through {s['range_end']} ({s['squeeze_bars']} true candles). Signal Close={s['signal_close']}, direction={s['direction']}. Signal candle is excluded: range end < signal start.", ''])
        assert DT.fromisoformat(s['range_end']) < t
        for name in ('signals', 'trade_ledger'):
            line = next((i+2 for i, x in enumerate(published[name]) if (x['instrument'], x['architecture'], x['scenario'], x['signal_id']) == (symbol, architecture, f'T{delay}', sid)), None)
            out.append(f'Published `{name}.csv.gz` decompressed CSV line: {line if line else "no ledger row / no fill"}.')
        out += ['', '| Feature | Independently reconstructed value |', '| --- | --- |']
        for k in ('warmup', 'sma20', 'variance20', 'std20', 'ema20', 'tr', 'atr20', 'bb_upper', 'bb_lower', 'kc_upper', 'kc_lower', 'squeeze', 'stop', 'cap'):
            out.append(f'| {k} | {s[k]} |')
        out += ['', 'Last20 completed source candles (population mean/variance window); TR includes previous Close in the same contiguous segment:', '', '| Source row | Start | Open | High | Low | Close | TR |', '| --- | --- | --- | --- | --- | --- | --- |']
        start = t-(int(s['warmup'])-1)*FIVE
        for i in range(19, -1, -1):
            at = t-i*FIVE
            o, h, l, c, v = idx[at]
            previous = idx[at-FIVE][3] if at > start else c
            tr = max(h-l, abs(h-previous), abs(l-previous))
            out.append(f'| {row_ids[at]} | {at} | {o} | {h} | {l} | {c} | {tr} |')
        out += ['', 'All squeeze-range source children (off/signal candles absent):', '', '| Source row | Start | High | Low |', '| --- | --- | --- | --- |']
        at, end = DT.fromisoformat(s['range_start']), DT.fromisoformat(s['range_end'])
        highs, lows = [], []
        while at <= end:
            b = idx[at]
            highs.append(b[1]); lows.append(b[2])
            out.append(f'| {row_ids[at]} | {at} | {b[1]} | {b[2]} |')
            at += FIVE
        assert max(highs) == D(s['range_high']) and min(lows) == D(s['range_low'])
        for label, at in (('Signal', t), ('Exact scheduled entry', DT.fromisoformat(s['planned_execution_at'])), ('Exit', DT.fromisoformat(ledger['exit_at']) if ledger and ledger['exit_at'] else None)):
            if at is not None:
                out += ['', f'{label} source row {row_ids.get(at)} at {at}: OHLCV={idx.get(at)}.']
        if ledger:
            out += ['', 'Independent payoff and protection:', '', '| Item | Value |', '| --- | --- |']
            for k in ('entry', 'entry_at', 'entry_ack', 'stop', 'initial_risk', 'planned_c1', 'planned_gross_reward', 'planned_net_reward', 'planned_net_RR', 'take', 'target_atr', 'exit', 'exit_at', 'exit_ack', 'exit_reason', 'gross', 'c1_entry', 'c1_exit', 'c1', 'net', 'gross_R', 'net_R', 'mfe_R', 'hold_minutes', 'flags'):
                out.append(f'| {k} | {ledger[k]} |')
            if ledger['net'] is not None:
                assert D(ledger['net']) == D(ledger['gross'])-D(ledger['c1'])
                assert D(ledger['planned_net_RR']) >= 3
        else:
            out += ['', 'No model fill, no ledger price, no C1. The exact-slot rejection is not retried on a later favorable candle.']
        if architecture == 'SQUEEZE_M30_M5':
            out += ['', f"M30 pair={s['mtf_first']} / {s['mtf_last']}; available={s['mtf_available_at']}; direction={s['mtf_direction']}; gate reason={s['mtf_reason']}."]
            if s['mtf_last']:
                out += ['', '| M30 child start | Source row | OHLCV |', '| --- | --- | --- |']
                for parent in (s['mtf_first'], s['mtf_last']):
                    first = DT.fromisoformat(parent)
                    for i in range(6):
                        at = first+i*FIVE
                        out.append(f'| {at} | {row_ids[at]} | {idx[at]} |')
        out += ['', '| Event clock / modeled start | Kind | Reason | Price | Acknowledgement | Flags |', '| --- | --- | --- | --- | --- | --- |']
        for e in r['execution_events']:
            if e['signal_id'] == sid:
                out.append('| '+' | '.join(str(e[k]) for k in ('at', 'kind', 'reason', 'price', 'confirmed_at', 'flags'))+' |')
        out.append('')
    cases = [
        ('USDRUBF', 'SQUEEZE_M5', 10, 'SQ_USDRUBF_000050', 'Real LONG / 3R Take'),
        ('USDRUBF', 'SQUEEZE_M5', 10, 'SQ_USDRUBF_000168', 'Real SHORT / entry-bar Stop'),
        ('USDRUBF', 'SQUEEZE_M5', 10, 'SQ_USDRUBF_000133', 'Real session-flat / previous +1R excursion'),
        ('USDRUBF', 'SQUEEZE_M5', 10, 'SQ_USDRUBF_000199', 'Real later Stop'),
        ('CNYRUBF', 'SQUEEZE_M5', 10, 'SQ_CNYRUBF_000271', 'Real CNY LONG after historical tick switch'),
        ('CNYRUBF', 'SQUEEZE_M5', 10, 'SQ_CNYRUBF_000276', 'Real CNY SHORT / risk and C1'),
        ('CNYRUBF', 'SQUEEZE_M5', 10, 'SQ_CNYRUBF_000368', 'Real CNY December Stop'),
        ('USDRUBF', 'SQUEEZE_M5', 15, 'SQ_USDRUBF_000233', 'Real T15 failed-breakout exit'),
        ('USDRUBF', 'SQUEEZE_M5', 15, 'SQ_USDRUBF_000050', 'Real T15 counterpart of T10 winner / NONFILL'),
    ]
    adverse = next(s for s in get('USDRUBF', 'SQUEEZE_M30_M5', 10)['signals'] if s['reason'] == 'MTF_SUSTAINED_ADVERSE_DIRECTION')
    cases.append(('USDRUBF', 'SQUEEZE_M30_M5', 10, adverse['signal_id'], 'Real M30 adverse-context rejection'))
    cases.append(('USDRUBF', 'SQUEEZE_M30_M5', 10, 'SQ_USDRUBF_000050', 'Real M30 accepted counterpart / same M5 exit'))
    for case in cases:
        add_case(*case)
    out += ['## Real compression without a signal', '']
    episode = next(e for e in get('USDRUBF', 'SQUEEZE_M5', 10)['squeeze_cycles'] if e['bars'] >= 3 and e['terminal_reason'] != 'SIGNAL')
    out += [json.dumps(episode, ensure_ascii=False, indent=2), '', 'Confirmed squeeze alone does not create an order. The range expired without a directional expansion; it cannot be reused after reset.', '']
    out += ['## Real missing M30 child / no stale fallback', '']
    idx = data['GLDRUBF']
    found = None
    for day in sorted({t.date() for t in idx}):
        for a, z in intervals(day):
            parent = a.replace(minute=0)
            while parent < a+TD(minutes=30):
                parent += TD(minutes=30)
            while parent+TD(minutes=30) <= z:
                now = parent+TD(minutes=35)
                rec = m30(idx, now, (a, z), 10, 1)
                times = [parent+i*FIVE for i in range(6)]
                if rec['mtf_reason'] == 'MTF_INCOMPLETE_CHILD_BUCKET' and any(t not in idx for t in times) and any(t in idx for t in times):
                    found = (now, times, rec)
                    break
                parent += TD(minutes=30)
            if found:
                break
        if found:
            break
    assert found
    now, times, rec = found
    out += [f'GLDRUBF decision clock={now}; independent gate={rec}.', '', '| Expected child | Physically exists | OHLCV |', '| --- | --- | --- |']
    for at in times:
        out.append(f'| {at} | {at in idx} | {idx.get(at)} |')
    out += ['', 'A prior complete M30 pair is not substituted. Missing child remains physically missing.', '', '## Real entire missing date / reset', '']
    for symbol in ('USDRUBF', 'CNYRUBF'):
        day = DT(2023, 8, 31).date()
        slots = [a+i*FIVE for a, z in intervals(day) for i in range(int((z-a)/FIVE))]
        assert not any(t in data[symbol] for t in slots)
        out.append(f'{symbol} 2023-08-31: all {len(slots)} approved M5 slots absent; no source row, no reconstructed candle, no indicator carry through the date. No Squeeze position was open across this gap; actual UNKNOWN count is0.')
    out += ['', '## Synthetic boundary cases — these are NOT 2023 trades', '',
            'The actual 2023 candidate has no adverse Stop gap, missing-entry order, opened UNKNOWN, Stop/Take ambiguity or MAX_HOLD exit. Those paths are verified by deterministic unit fixtures, not invented historical transactions.', '',
            '- Adverse gap + both levels: LONG entry100.05, stop99.97, risk0.08, take100.31; following Open99.95/High100.40/Low99.90. Stop-first gives exit99.95, Gross−0.10, C1=0.02, Net−0.12, NetR=−1.5. High100.40 does not prove prior3R. `test_stop_first_and_adverse_gap`.',
            '- Missing entry: prescribed signal15:55, T10 ready16:05, target16:10 absent; acknowledgement16:20 gives NO_BAR_NO_MODEL_FILL, no entry price/cost. No later candle retries that entry. `test_session_reserve_t10_t15_and_missing_exact_entry`.',
            '- UNKNOWN path: entry11:15 acknowledged11:25; gap observation11:30 requests future11:35 reduce-all, acknowledged11:45. All past Gross/C1_total/Net/R stay null even if next Open is200. `test_unknown_never_reconciles_payoff`.',
            '- MAX_HOLD: PM prescribed signal15:55, model entry16:10; request18:05, future Open18:10, acknowledgement18:20; actual model holding120min. `test_max_hold_120_and_future_failed_breakout_exit`.',
            '- Failed breakout: entry16:10; completed candle16:20 closes100.08 inside [99.90,100.10], delivered16:30; request16:30 and exit16:35 Open100.11, never the earlier Close100.08.',
            '- Session: B18:50; T10 request18:25 → Open18:30 → acknowledgement18:40. T15 request18:20 → Open18:25 → acknowledgement18:40. Both reserve B−10; boundary has priority over120min.',
            '- M30: delete each of the six children of latest expected parent; all six deletions block, even if previous pair exists. Late child delivery at decision+5 also blocks. `test_each_m30_child_missing_and_no_stale_fallback`.', '',
            'Reproduction: run `audit_squeeze.py` into a fresh audit folder, then this tool against its `reconstructed.json.gz`. Every source read uses exact attested2023 byte budget; no native TF or later-year row is opened.', '']
    args.output.write_text('\n'.join(out))
    print('Written 11 real signal/trade traces, actual no-signal/missing-context/date traces, and explicit synthetic boundary cases')


if __name__ == '__main__':
    main()
