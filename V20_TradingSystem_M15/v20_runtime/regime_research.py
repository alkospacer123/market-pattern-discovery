"""Bounded V20-04.2 offline experiment. No strategy replay, card or trading hook.

See REGIME_RESEARCH_PROTOCOL_RU.md, frozen before candidate calculation.
Only retrospective evaluation functions inspect future outcomes. Source OHLCV
stays outside the repository. All timestamps are source naive Moscow time.
"""
from __future__ import annotations

import argparse
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict, deque
import csv
from datetime import datetime, timedelta
import gzip
import io
import json
from math import isclose, isfinite, sqrt
from pathlib import Path
from statistics import mean, median
import zipfile

from .market_epochs import ROOT, STAGE, day_key, unknown_gap, sha
from .market_rolling_raw import RAW_PATH, RAW_SHA, verify_sources, stamp
from .market_reference_descriptive import SOURCE_SHA256
from .market_suitability import M15Bar, STEP
from .instrument_regime import unique_events

METHODS = ('RAW20', 'RAW20_CONFIRM5', 'FP2_20', 'FP2_CONFIRM5',
           'ER20_CONFIRM5', 'ER80_CONFIRM5', 'FP2_CUSUM')
SCHEMA = 'v20.regime_research.v1'
UNKNOWN, GOOD, BAD = 'UNKNOWN', 'NORMAL', 'WARNING'
MAX_AGE = timedelta(days=90)


def published_events(as_of=None):
    """Deduplicate only fully observed paths; check all frozen price semantics."""
    if sha(RAW_PATH) != RAW_SHA:
        raise ValueError('RAW_PUBLICATION_SHA_MISMATCH')
    events = {}
    for row in csv.DictReader(io.StringIO(RAW_PATH.read_text())):
        if row['record_type'] != 'RAW_SIGNAL' or row['horizon_status'] != 'OBSERVED_V1':
            continue
        available = stamp(row['horizon_exit_dt'])
        if as_of is not None and available > as_of:
            continue  # no future numeric outcome parsed
        r = dict(instrument=row['instrument'], contract=row['contract'],
                 signal=stamp(row['signal_bar_dt']), entry_time=stamp(row['entry_dt']),
                 available=available, side=int(row['side']), entry=float(row['entry']),
                 stop=float(row['stop']), risk=float(row['risk']), raw_R=float(row['horizon_R']),
                 stop_touch=row['horizon_stop_touch'] == 'True',
                 source_mfe=float(row['horizon_MFE_R']), robots=1)
        r['stop_aware'] = -1.0 if r['stop_touch'] else r['raw_R']
        if r['side'] not in (-1, 1) or r['risk'] <= 0 or not isclose(
                r['side'] * (r['entry']-r['stop']), r['risk'], abs_tol=1e-7):
            raise ValueError('FROZEN_RISK_OR_SIDE_INVALID')
        key = (r['instrument'], r['signal'])
        if key in events:
            previous = events[key]
            for field in r.keys() - {'robots'}:
                a, b = previous[field], r[field]
                if not (isclose(a, b, rel_tol=1e-9, abs_tol=1e-8) if isinstance(a, float) else a == b):
                    raise ValueError('DUPLICATE_CONFLICT_' + field)
            previous['robots'] += 1
        else:
            events[key] = r
    result = sorted(events.values(), key=lambda r: (r['available'], r['signal'], r['instrument']))
    expected = sum(len(unique_events(result, instrument=symbol, as_of=as_of or datetime(2027, 1, 1)))
                   for symbol in {r['instrument'] for r in result})
    if expected != len(result):
        raise ValueError('EXISTING_UNIQUE_STREAM_MISMATCH')
    return result


def read_quotes(stream):
    """V20 owner permits 2025 here; legacy epochs loader intentionally differs."""
    bars = []
    for r in csv.DictReader(stream, delimiter=';'):
        dt = stamp(r['Datetime'])
        values = [float(r[k]) for k in ('Open', 'High', 'Low', 'Close', 'Volume')]
        o, h, l, c, v = values
        if (not all(isfinite(x) for x in values) or min(o, h, l, c) <= 0 or
                h < max(o, l, c) or l > min(o, h, c) or v < 0 or
                dt.minute % 15 or dt.second or dt.microsecond or
                (bars and dt <= bars[-1].open_time)):
            raise ValueError('SOURCE_OHLCV_OR_ORDER_INVALID')
        bars.append(M15Bar(dt, *values))
    return bars


def sources(archive, data_dir):
    proof = verify_sources(archive, data_dir)
    mapping = list(csv.DictReader(io.StringIO((STAGE/'results/CONTRACT_MAP.csv').read_text())))
    contracts, families = {}, {}
    with zipfile.ZipFile(archive) as zipped:
        for r in mapping:
            contracts[r['contract']] = read_quotes(io.StringIO(zipped.read(r['file']).decode('utf-8-sig')))
            families[r['contract']] = r['family']
    for symbol in SOURCE_SHA256:
        with (data_dir/symbol/(symbol+'_M15.csv')).open(encoding='utf-8-sig') as stream:
            contracts[symbol] = read_quotes(stream)
        families[symbol] = symbol
    choices = {(r['family'], r['day']): r['chosen_contract']
               for r in csv.DictReader(io.StringIO((STAGE/'results/ROLL_DECISIONS.csv').read_text()))}
    selected = defaultdict(list)
    calendars = {'old': set(), 'modern': set()}
    proof['old_quote_last_open_msk'] = {family:max(bars[-1].open_time for contract,bars in contracts.items()
        if families[contract]==family).isoformat(sep=' ') for family in ('Si','MIX','CNY')}
    proof['raw_coverage'] = dict(Counter(r['horizon_status'] for r in
        csv.DictReader(io.StringIO(RAW_PATH.read_text())) if r['record_type']=='RAW_SIGNAL'))
    for contract, bars in contracts.items():
        modern = contract in SOURCE_SHA256
        for bar in bars:
            if not 2018<=bar.open_time.year<=2026:
                continue  # 2017 source warm-up is outside this experiment
            day = day_key(bar.open_time)
            calendars['modern' if modern else 'old'].add(day)
            if modern or choices.get((families[contract], str(day))) == contract:
                selected[families[contract]].append((contract, bar))
    for group in selected.values():
        group.sort(key=lambda x: x[1].open_time)
        if any(group[i-1][1].open_time >= group[i][1].open_time for i in range(1, len(group))):
            raise ValueError('SELECTED_CONTRACT_COLLISION')
    return contracts, selected, calendars, proof


def path_quality(event, bars):
    """Exact initial-risk excursions, interval bounds for unknown M15 ordering."""
    times = [b.open_time for b in bars]
    en, end = bisect_left(times, event['entry_time']), bisect_left(times, event['available'])
    if en >= len(bars) or end >= len(bars) or times[en] != event['entry_time'] or times[end] != event['available']:
        raise ValueError('PATH_ENDPOINT_NOT_IN_VERIFIED_QUOTES')
    if not isclose(bars[en].open, event['entry'], abs_tol=1e-7):
        raise ValueError('NEXT_OPEN_MISMATCH')
    side, price, risk = event['side'], event['entry'], event['risk']
    targets = {t: dict(result='MISS', bars=None) for t in (1, 2, 3, 5)}
    low_mfe = high_mfe = 0.0
    stopped = False
    eps = 1e-7  # same touch tolerance as published V1
    for j in range(en, end+1):
        b = bars[j]
        opened = side*(b.open-price)/risk
        if opened <= -1+eps:
            stopped = True
            break
        low_mfe = high_mfe = max(low_mfe, opened)
        for target, value in targets.items():
            if value['result'] == 'MISS' and opened >= target-eps:
                value.update(result='DEFINITE', bars=j-en)
        if j == end:
            break  # horizon Open only; the new bar has not closed
        fav = ((b.high-price) if side == 1 else (price-b.low))/risk
        adv = ((price-b.low) if side == 1 else (b.high-price))/risk
        hit_stop = adv >= 1-eps
        for target, value in targets.items():
            if value['result'] == 'MISS' and fav >= target-eps:
                value.update(result='AMBIGUOUS' if hit_stop else 'DEFINITE',
                             bars=None if hit_stop else j-en+1)
        high_mfe = max(high_mfe, fav)
        if hit_stop:
            stopped = True
            break
        low_mfe = high_mfe
    if stopped != event['stop_touch']:
        raise ValueError('PUBLISHED_STOP_TOUCH_MISMATCH')
    return dict(mfe_low=low_mfe, mfe_high=high_mfe,
                **{f'fp{t}': int(v['result'] == 'DEFINITE') for t, v in targets.items()},
                **{f'amb{t}': int(v['result'] == 'AMBIGUOUS') for t, v in targets.items()},
                **{f'bars{t}': v['bars'] for t, v in targets.items()})


def er_values(selected, calendar, as_of=None):
    """Classic ER across documented observed sessions, never across contracts.

    Values at b.open_time+15 only. Prefix invariance includes continuity checks:
    calendar is consulted only for days strictly between already observed bars.
    """
    days = sorted(calendar)
    closes = deque(maxlen=81)
    previous = None
    for contract, bar in selected:
        available = bar.open_time + STEP
        if as_of is not None and available > as_of:
            break  # future OHLC must not be inspected
        reset = previous is None
        if previous is not None:
            old_contract, old_bar = previous
            old_day, day = day_key(old_bar.open_time), day_key(bar.open_time)
            missing_day = (day > old_day and
                           bisect_left(days, day)-bisect_right(days, old_day) > 0)
            reset = (old_contract != contract or unknown_gap(old_bar.open_time, bar.open_time)
                     or (day-old_day).days > 4 or missing_day)
        if reset:
            closes.clear()
        closes.append(bar.close)
        values = list(closes)
        r = dict(as_of=available, contract=contract, reset=reset)
        for n in (20, 80):
            q = values[-n-1:]
            denominator = sum(abs(y-x) for x, y in zip(q, q[1:]))
            r[f'er{n}'] = (abs(q[-1]-q[0])/denominator if denominator else 0.0) if len(q) == n+1 else None
        yield r
        previous = (contract, bar)


class ERMonitor:
    def __init__(self, scale):
        self.scale = scale
        self.training = []
        self.base = None
        self.below = self.above = 0
        self.state = UNKNOWN
        self.last = None
        self.value = None

    def update(self, row):
        value = row[f'er{self.scale}']
        self.value = value
        self.last = row['as_of']
        if row['reset'] or value is None:
            self.below = self.above = 0
            self.state = UNKNOWN
        if value is None:
            return
        if self.base is None:
            self.training.append(value)
            if len(self.training) == 40:
                self.base = median(self.training)
            return
        self.below = self.below+1 if value < self.base else 0
        self.above = self.above+1 if value >= self.base else 0
        if self.below >= 5:
            self.state = BAD
        elif self.above >= 5:
            self.state = GOOD

    def at(self, now):
        return self.state if self.last and now-self.last <= timedelta(days=4) else UNKNOWN


def rolling_metrics(known, now):
    if not known:
        return {}
    current, previous = known[-20:], known[-40:-20]
    valid = (len(known) >= 40 and now-known[-1]['available'] <= MAX_AGE and
             all(max(r['available'] for r in q)-min(r['signal'] for r in q) <= timedelta(days=365)
                 for q in (current, previous)))
    return dict(n=len(known), current_n=len(current), previous_n=len(previous), valid=valid,
                raw=mean(r['raw_R'] for r in current),
                previous_raw=mean(r['raw_R'] for r in previous) if previous else None,
                fp2=mean(r['fp2'] for r in current),
                previous_fp2=mean(r['fp2'] for r in previous) if previous else None,
                stop_aware=mean(r['stop_aware'] for r in current),
                mfe=mean(r['mfe_low'] for r in current),
                first_signal=current[0]['signal'], last_available=known[-1]['available'])


def causal_states(events, er_rows, clocks=(), as_of=None):
    """Features/states only. No future-quality columns or evaluation functions."""
    # Filter by availability before accessing any numeric fields.
    events = sorted((r for r in events if as_of is None or r['available'] <= as_of),
                    key=lambda r: (r['available'], r['signal'], r['contract']))
    er_rows = [r for r in er_rows if as_of is None or r['as_of'] <= as_of]
    batches, er_at = defaultdict(list), {}
    for r in events:
        batches[r['available']].append(r)
    for r in er_rows:
        er_at[r['as_of']] = r
    times = sorted(set(batches) | set(er_at) | {t for t in clocks if as_of is None or t <= as_of})
    monitors = [ERMonitor(n) for n in (20, 80)]
    known, output, bar_output = [], [], []
    confirmations = dict(raw=0, fp2=0)
    cusum = dict(base=None, sigma=None, down=0.0, up=0.0, state=UNKNOWN)
    last_event = None
    metrics = {}
    for now in times:
        if last_event is not None and now-last_event > MAX_AGE:
            cusum.update(down=0.0, up=0.0, state=UNKNOWN)
            confirmations = dict(raw=0, fp2=0)
        batch = batches.get(now)
        if batch:
            known.extend(batch)
            metrics = rolling_metrics(known, now)
            for field in confirmations:
                declining = metrics['valid'] and metrics[field] < metrics['previous_'+field]
                confirmations[field] = confirmations[field]+1 if declining else 0
            if cusum['base'] is None and len(known) >= 40:
                p = mean(r['fp2'] for r in known[:40])
                cusum.update(base=p, sigma=sqrt(max(p*(1-p), 1/40)), state=GOOD)
            elif cusum['base'] is not None:
                z = sum((r['fp2']-cusum['base'])/cusum['sigma'] for r in batch)
                if cusum['state']==BAD:
                    # Reverse the SAME deterioration evidence. An ordinary
                    # upper chart z-k would demand improvement above the old
                    # baseline, rather than recovery back to that baseline.
                    cusum['up'] = max(0, cusum['up']+z+.5*len(batch))
                    if cusum['up']>=5:
                        cusum.update(state=GOOD,down=0.0,up=0.0)
                else:
                    cusum['state']=GOOD
                    cusum['down'] = max(0,cusum['down']-z-.5*len(batch))
                    if cusum['down']>=5:
                        cusum.update(state=BAD,down=0.0,up=0.0)
            last_event = now
        for monitor in monitors:
            if now in er_at:
                monitor.update(er_at[now])
        if metrics and last_event is not None and now-last_event > MAX_AGE:
            metrics = dict(metrics, valid=False)
        states = {}
        for field, direct, confirmed in (('raw', 'RAW20', 'RAW20_CONFIRM5'), ('fp2', 'FP2_20', 'FP2_CONFIRM5')):
            valid = metrics.get('valid', False)
            states[direct] = (BAD if metrics[field] < metrics['previous_'+field] else GOOD) if valid else UNKNOWN
            states[confirmed] = (BAD if confirmations[field] >= 5 else GOOD) if valid else UNKNOWN
        states['FP2_CUSUM'] = cusum['state'] if metrics.get('valid') else UNKNOWN
        for monitor in monitors:
            states[f'ER{monitor.scale}_CONFIRM5'] = monitor.at(now)
        common = dict(as_of=now, n=len(known), **{k:v for k,v in metrics.items() if k != 'n'},
                      er20=monitors[0].value, er80=monitors[1].value,
                      er20_base=monitors[0].base, er80_base=monitors[1].base,
                      cusum_base=cusum['base'], cusum_down=cusum['down'], cusum_up=cusum['up'], **states)
        # M15 CSV stores all ER updates, including times between signal outcomes.
        if now in er_at:
            bar_output.append({k: common.get(k) for k in (
                'as_of','n','er20','er80','er20_base','er80_base','ER20_CONFIRM5','ER80_CONFIRM5')}
                | dict(contract=er_at[now]['contract'], reset=er_at[now]['reset']))
        # Daily clock and every atomic raw close: a small readable joint timeline.
        if now in batches or now in clocks:
            output.append(common)
    return output, bar_output


def quality(rows):
    return dict(n=len(rows), raw_R=mean(r['raw_R'] for r in rows),
                stop_aware_R=mean(r['stop_aware'] for r in rows),
                fp2=mean(r['fp2'] for r in rows), amb2=mean(r['amb2'] for r in rows),
                fp2_upper=mean(r['fp2']+r['amb2'] for r in rows),
                mfe_low=mean(r['mfe_low'] for r in rows), mfe_high=mean(r['mfe_high'] for r in rows),
                fp3=mean(r['fp3'] for r in rows), fp5=mean(r['fp5'] for r in rows),
                stop_share=mean(r['stop_touch'] for r in rows),
                bars1_median=median([r['bars1'] for r in rows if r['fp1']]) if any(r['fp1'] for r in rows) else None,
                bars2_median=median([r['bars2'] for r in rows if r['fp2']]) if any(r['fp2'] for r in rows) else None)


def truth_periods(events):
    """Evaluation labels only: fixed nonoverlapping cohorts, never a feature."""
    blocks = []
    for i in range(0, len(events)-19, 20):
        q = events[i:i+20]
        stats = quality(q)
        valid = (max(r['available'] for r in q)-min(r['signal'] for r in q) <= timedelta(days=365)
                 and all(b['available']-a['available'] <= MAX_AGE for a,b in zip(q,q[1:])))
        weak = stats['stop_aware_R'] < 0 and stats['fp2'] < 1/3
        strong = stats['stop_aware_R'] >= 0 and stats['fp2'] >= 1/3
        blocks.append(dict(block=i//20, start=min(r['entry_time'] for r in q), end=q[-1]['available'],
                           kind=('WEAK' if weak else 'STRONG' if strong else 'MIXED') if valid else UNKNOWN, **stats))
    runs, i = [], 0
    while i < len(blocks):
        j = i+1
        while (j < len(blocks) and blocks[j]['kind'] == blocks[i]['kind'] and
               blocks[j]['start']-blocks[j-1]['end'] <= MAX_AGE):
            j += 1
        if j-i >= 2 and blocks[i]['kind'] in ('WEAK','STRONG'):
            runs.append(dict(kind=blocks[i]['kind'], start=blocks[i]['start'], end=blocks[j-1]['end'],
                             label_available=blocks[i+1]['end'], blocks=j-i, first_block=i, last_block=j-1))
        i = j
    weak = [r for r in runs if r['kind'] == 'WEAK']
    recovery, pending = [], False
    for r in runs:
        if r['kind'] == 'WEAK':
            pending = True
        elif r['kind'] == 'STRONG' and pending:
            recovery.append(r)
            pending = False
    return blocks, weak, recovery


def intervals(states, method, end):
    """ER uses its M15 states, other methods use daily+event states."""
    result = []
    for row in states:
        state = row[method]
        if not result or result[-1]['state'] != state:
            if result:
                result[-1]['end'] = row['as_of']
            result.append(dict(start=row['as_of'], end=end, state=state, n=row['n']))
    return result


def overlap(a, b, start, end):
    return max(0.0, (min(b,end)-max(a,start)).total_seconds())


def union_intervals(pairs):
    """Cohort path horizons overlap; count each calendar second once per label."""
    result=[]
    for start,end in sorted(pairs):
        if result and start<=result[-1][1]:
            result[-1]=(result[-1][0],max(end,result[-1][1]))
        else:
            result.append((start,end))
    return result


def evaluate(events, states, method, start, end, weak, recovery, blocks):
    """Only here inspect future labels; no result is fed into candidate states."""
    spans = intervals(states, method, end)
    warnings = []
    for span in spans:
        if span['state'] != BAD:
            continue
        matched = [w for w in weak if w['start']-MAX_AGE <= span['start'] <= w['end']]
        future = [r for r in events if r['available'] > span['start']]
        resolvable = len(future) >= 40 and end-span['start'] >= MAX_AGE
        warnings.append(dict(method=method, **span, result='TRUE' if matched else 'FALSE' if resolvable else 'UNRESOLVED',
            next40_n=min(40,len(future)), evaluation_at=future[39]['available'] if len(future)>=40 else None,
            next40_fp2=mean(r['fp2'] for r in future[:40]) if len(future)>=40 else None,
            next40_stop_aware_R=mean(r['stop_aware'] for r in future[:40]) if len(future)>=40 else None))
    detections = []
    for kind, episodes, target in (('WEAK', weak, BAD), ('RECOVERY', recovery, GOOD)):
        for episode in episodes:
            candidates = [s for s in spans if s['state'] == target and s['start'] <= episode['end'] and s['end'] > episode['start']]
            detected = max(episode['start'],candidates[0]['start']) if candidates else None
            prior = max((w['start'] for w in weak if w['start']<episode['start']),default=None)
            actual_return = (kind=='RECOVERY' and bool(candidates) and prior is not None and
                any(s['state']==BAD and s['start']<candidates[0]['start'] and s['end']>prior for s in spans))
            detections.append(dict(method=method, kind=kind, start=episode['start'], end=episode['end'],
                label_available=episode['label_available'], detected=detected,
                warning_origin=candidates[0]['start'] if candidates else None,
                recovery_transition=actual_return,
                delay_days=(detected-episode['start']).total_seconds()/86400 if detected else None,
                warmup_miss=(not candidates and not any(s['state'] != UNKNOWN and
                    overlap(s['start'],s['end'],episode['start'],episode['end']) for s in spans))))
    # Year-specific time errors/coverage do not silently omit non-signal periods.
    years = []
    for year in range(start.year,end.year+1):
        lo, hi = max(start,datetime(year,1,1)), min(end,datetime(year+1,1,1))
        total = (hi-lo).total_seconds()
        known = sum(overlap(s['start'],s['end'],lo,hi) for s in spans if s['state'] != UNKNOWN)
        bad_time = sum(overlap(s['start'],s['end'],lo,hi) for s in spans if s['state'] == BAD)
        strong_time = missed_time = all_weak = all_strong = 0.0
        for kind in ('WEAK','STRONG'):
            for left,right in union_intervals((max(lo,b['start']),min(hi,b['end'])) for b in blocks
                    if b['kind']==kind and max(lo,b['start'])<min(hi,b['end'])):
                if kind=='WEAK':
                    all_weak += (right-left).total_seconds()
                    missed_time += sum(overlap(s['start'],s['end'],left,right) for s in spans if s['state'] != BAD)
                else:
                    all_strong += (right-left).total_seconds()
                    strong_time += sum(overlap(s['start'],s['end'],left,right) for s in spans if s['state'] == BAD)
        warn = [w for w in warnings if w['start'].year == year]
        det = [d for d in detections if d['start'].year == year]
        delays = [d['delay_days'] for d in det if d['kind']=='WEAK' and d['detected']]
        recoveries = [d['delay_days'] for d in det if d['kind']=='RECOVERY' and d['detected']]
        years.append(dict(method=method, year=year, warnings=len(warn),
            false=sum(w['result']=='FALSE' for w in warn), true=sum(w['result']=='TRUE' for w in warn),
            unresolved=sum(w['result']=='UNRESOLVED' for w in warn),
            weak=sum(d['kind']=='WEAK' for d in det), missed=sum(d['kind']=='WEAK' and not d['detected'] for d in det),
            warmup_missed=sum(d['kind']=='WEAK' and d['warmup_miss'] for d in det),
            recoveries=sum(d['kind']=='RECOVERY' for d in det), recovered=len(recoveries),
            recovery_transitions=sum(d['recovery_transition'] for d in det),
            delay_days=delays, recovery_delay_days=recoveries,
            coverage_seconds=known, total_seconds=total, warning_seconds=bad_time,
            weak_seconds=all_weak, missed_weak_seconds=missed_time,
            strong_seconds=all_strong, false_strong_seconds=strong_time))
    return years, warnings, detections


def aggregate(rows):
    sums = ('warnings','false','true','unresolved','weak','missed','warmup_missed','recoveries','recovered','recovery_transitions',
            'coverage_seconds','total_seconds','warning_seconds','weak_seconds','missed_weak_seconds',
            'strong_seconds','false_strong_seconds')
    result = {k:sum(r[k] for r in rows) for k in sums}
    for key in ('delay_days','recovery_delay_days'):
        values = [v for r in rows for v in r[key]]
        result[key] = dict(n=len(values), median=median(values) if values else None,
                           minimum=min(values) if values else None, maximum=max(values) if values else None)
    for key,numerator,denominator in (
        ('coverage','coverage_seconds','total_seconds'),('weak_time_missed','missed_weak_seconds','weak_seconds'),
        ('strong_time_warning','false_strong_seconds','strong_seconds')):
        result[key] = result[numerator]/result[denominator] if result[denominator] else None
    return result


def dump_csv(path, rows, *, compressed=False):
    if not rows:
        path.write_text('')
        return
    fields = list(dict.fromkeys(k for row in rows for k in row))
    def encode(value):
        if isinstance(value,datetime):
            return value.isoformat(sep=' ')
        if isinstance(value,float):
            return format(value,'.10g')
        if isinstance(value,list):
            return json.dumps(value,separators=(',',':'))
        return value
    def write(stream):
        writer = csv.DictWriter(stream,fieldnames=fields,lineterminator='\n')
        writer.writeheader()
        writer.writerows({k:encode(v) for k,v in row.items()} for row in rows)
    if compressed:
        with path.open('wb') as raw:
            with gzip.GzipFile(fileobj=raw,mode='wb',filename='',mtime=0) as packed:
                with io.TextIOWrapper(packed,encoding='utf-8',newline='') as stream:
                    write(stream)
    else:
        with path.open('w',encoding='utf-8',newline='') as stream:
            write(stream)


def association(events, field):
    rows = [r for r in events if r.get(field) is not None and r.get(field+'_base') is not None]
    output = {}
    for bucket,selected in (('below_base',[r for r in rows if r[field]<r[field+'_base']]),
                            ('at_or_above_base',[r for r in rows if r[field]>=r[field+'_base']])):
        output[bucket] = quality(selected) if selected else dict(n=0)
    return output


def run(archive, data_dir, output):
    contracts, selected, calendars, provenance = sources(archive,data_dir)
    events = published_events()
    for i,r in enumerate(events):
        r.update(path_quality(r,contracts[r['contract']]))
    by_symbol = defaultdict(list)
    for r in events:
        by_symbol[r['instrument']].append(r)
    all_daily, all_bars, all_blocks, all_periods = [], [], [], []
    all_metrics, all_warnings, all_detections = [], [], []
    yearly, coverage, er_monthly, associations = [], [], [], []
    for symbol,rows in sorted(by_symbol.items()):
        source = selected[symbol]
        start = source[0][1].open_time+STEP
        end = (source[-1][1].open_time if symbol in SOURCE_SHA256 else
               stamp(provenance['old_quote_last_open_msk'][symbol]))+STEP
        if rows[-1]['available']>end:
            raise ValueError('OUTCOME_AFTER_SOURCE_END')
        clock = datetime.combine(start.date(),datetime.min.time()).replace(hour=18)
        clocks = {start,end}
        while clock<=end:
            if clock>=start:
                clocks.add(clock)
            clock += timedelta(days=1)
        ers = list(er_values(source,calendars['modern' if symbol in SOURCE_SHA256 else 'old']))
        states,bars = causal_states(rows,ers,clocks)
        # ER at signal close (=entry Open) is known before the path evolves.
        at = {b['as_of']:b for b in bars}
        for r in rows:
            state = at.get(r['entry_time'])
            if state and state['contract']!=r['contract']:
                raise ValueError('ER_SIGNAL_CONTRACT_MISMATCH')
            for key in ('er20','er80','er20_base','er80_base'):
                r[key] = state[key] if state else None
        blocks,weak,recovery = truth_periods(rows)
        for container,items in ((all_daily,states),(all_bars,bars),(all_blocks,blocks),
                                (all_periods,weak+recovery)):
            container.extend(dict(instrument=symbol,**r) for r in items)
        # Future columns have evaluation_ prefix and are appended after states.
        available = [r['available'] for r in rows]
        for state in states:
            future = rows[bisect_right(available,state['as_of']):][:40]
            state['evaluation_next40_n'] = len(future)
            state['evaluation_next40_fp2'] = mean(r['fp2'] for r in future) if len(future)==40 else None
            state['evaluation_next40_stop_aware'] = mean(r['stop_aware'] for r in future) if len(future)==40 else None
            state['evaluation_available'] = future[-1]['available'] if len(future)==40 else None
        for epoch in ('2018-2022','2023-2026'):
            period_rows=[r for r in rows if (r['signal'].year<=2022)==(epoch=='2018-2022')]
            for field in ('er20','er80'):
                for bucket,stats in association(period_rows,field).items():
                    associations.append(dict(instrument=symbol,epoch=epoch,metric=field,
                        sample='SIGNAL_ENTRY',cusum_condition='ALL',bucket=bucket,**stats))
                # Only atomic outcome updates; not thousands of repeated daily labels.
                valid_states=[s for s in states if s['as_of'] in available and s.get('valid')
                    and s.get('evaluation_next40_n')==40 and s[field] is not None and s[field+'_base'] is not None
                    and (s['as_of'].year<=2022)==(epoch=='2018-2022')]
                for condition in (GOOD,BAD):
                    for bucket in ('below_base','at_or_above_base'):
                        q=[s for s in valid_states if s['FP2_CUSUM']==condition and
                            (s[field]<s[field+'_base'])==(bucket=='below_base')]
                        associations.append(dict(instrument=symbol,epoch=epoch,metric=field,
                            sample='NEXT40_EVALUATION_ONLY',cusum_condition=condition,bucket=bucket,n=len(q),
                            fp2=mean(s['evaluation_next40_fp2'] for s in q) if q else None,
                            stop_aware_R=mean(s['evaluation_next40_stop_aware'] for s in q) if q else None))
        # Replace pre-evaluation copies only for the human-readable joint timeline.
        all_daily = [r for r in all_daily if r['instrument']!=symbol] + [dict(instrument=symbol,**r) for r in states]
        for method in METHODS:
            method_states = (sorted({r['as_of']:r for r in bars+states}.values(),key=lambda r:r['as_of'])
                             if method.startswith('ER') else states)
            metrics,warnings,detections = evaluate(rows,method_states,method,start,end,weak,recovery,blocks)
            all_metrics.extend(dict(instrument=symbol,**r) for r in metrics)
            all_warnings.extend(dict(instrument=symbol,**r) for r in warnings)
            all_detections.extend(dict(instrument=symbol,**r) for r in detections)
        for year in sorted({r['signal'].year for r in rows}):
            q=[r for r in rows if r['signal'].year==year]
            yearly.append(dict(instrument=symbol,year=year,**quality(q),
                               er20=association(q,'er20'),er80=association(q,'er80')))
        for month in sorted({r['as_of'].strftime('%Y-%m') for r in bars}):
            month_rows=[r for r in bars if r['as_of'].strftime('%Y-%m')==month]
            er_monthly.append(dict(instrument=symbol,month=month,bars=len(month_rows),**{
                f'{field}_{stat}':(len(q) if stat=='n' else mean(q) if stat=='mean' and q else median(q) if q else None)
                for field in ('er20','er80') for q in [[r[field] for r in month_rows if r[field] is not None]]
                for stat in ('n','mean','median')}))
        coverage.append(dict(instrument=symbol,quote_start=start,quote_end=end,
            last_selected_m15_close=source[-1][1].open_time+STEP,
            selected_bars=len(source),known_outcomes=len(rows),first_outcome=rows[0]['available'],
            last_outcome=rows[-1]['available'],er20_valid=sum(r['er20'] is not None for r in ers),
            er80_valid=sum(r['er80'] is not None for r in ers),er_resets=sum(r['reset'] for r in ers)))
        print('regime',symbol,len(rows),'bars',len(bars),'weak',len(weak),'recovery',len(recovery),flush=True)
    totals = {m:aggregate([r for r in all_metrics if r['method']==m]) for m in METHODS}
    epochs = {epoch:{m:aggregate([r for r in all_metrics if r['method']==m and
                 (r['year']<=2022)==(epoch=='2018-2022')]) for m in METHODS}
              for epoch in ('2018-2022','2023-2026')}
    instruments = {s:{m:aggregate([r for r in all_metrics if r['method']==m and r['instrument']==s])
                      for m in METHODS} for s in sorted(by_symbol)}
    # Prespecified gate, not a search for a combination that happens to win.
    er,cusum = (epochs['2018-2022'][m] for m in ('ER80_CONFIRM5','FP2_CUSUM'))
    combo_gate = er['false']<cusum['false'] and er['missed']<=cusum['missed']
    if combo_gate:
        raise RuntimeError('COMBINATION_GATE_PASSED_IMPLEMENT_SINGLE_PRESPECIFIED_COMBINATION')
    # No candidate can pass merely by suppressing warnings/missing recoveries.
    improvements = []
    for method in METHODS[2:]:
        passes = True
        for epoch in epochs.values():
            candidate,baseline = epoch[method],epoch['RAW20_CONFIRM5']
            delay,base_delay = candidate['delay_days']['median'],baseline['delay_days']['median']
            passes &= (candidate['false']<baseline['false'] and candidate['missed']<=baseline['missed'] and
                       candidate['recovered']>=baseline['recovered'] and candidate['coverage']>=baseline['coverage'] and
                       delay is not None and base_delay is not None and delay<=base_delay)
        if passes:
            improvements.append(method)
    result = dict(schema=SCHEMA,input_pr_head='e47e786c96b28e854ac9f7d6627b9b8f2354e14b',
        main='6f352acfac7ebdfabba73e143c4dfea3a6e48507',protocol_sha256=sha(ROOT/'V20-04/REGIME_RESEARCH_PROTOCOL_RU.md'),
        provenance=provenance,unique_events=len(events),duplicate_extra=sum(r['robots']-1 for r in events),
        duplicate_groups=sum(r['robots']>1 for r in events),coverage=coverage,yearly=yearly,
        total=totals,epochs=epochs,instruments=instruments,
        combination='SKIP_PREDECLARED_ER_GATE_FAILED',historical_improvement_candidates=improvements,
        reliability='FAIL' if not improvements else 'REQUIRES_INSTRUMENT_STABILITY_REVIEW',
        independent_oos=False,card_changed=False,trading_changed=False)
    output.mkdir(parents=True,exist_ok=True)
    dump_csv(output/'REGIME_EVENTS.csv',events)
    dump_csv(output/'REGIME_TIMELINE.csv.gz',all_daily,compressed=True)
    dump_csv(output/'REGIME_ER_M15.csv.gz',all_bars,compressed=True)
    dump_csv(output/'REGIME_BLOCKS.csv',all_blocks)
    dump_csv(output/'REGIME_PERIODS.csv',all_periods)
    dump_csv(output/'REGIME_WARNINGS.csv',all_warnings)
    dump_csv(output/'REGIME_DETECTIONS.csv',all_detections)
    dump_csv(output/'REGIME_METRICS.csv',all_metrics)
    dump_csv(output/'REGIME_ER_MONTHLY.csv',er_monthly)
    dump_csv(output/'REGIME_ASSOCIATIONS.csv',associations)
    (output/'REGIME_RESULTS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str)+'\n')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,required=True)
    parser.add_argument('--data-dir',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=run(args.archive,args.data_dir,args.output)
    print(json.dumps(dict(unique_events=result['unique_events'],reliability=result['reliability'],
                          improvements=result['historical_improvement_candidates']),ensure_ascii=False))


if __name__=='__main__':
    main()
