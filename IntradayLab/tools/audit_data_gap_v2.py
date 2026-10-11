"""Independent synthetic raw-M5 path, CSV arithmetic and coverage audit.

Only standard-library imports. No production Backtester, execution, metrics,
loader, calendar or strategy supplies expected answers. Not human signoff.
"""
import csv
from datetime import datetime, timedelta
from decimal import Decimal as D, ROUND_CEILING, ROUND_FLOOR
import json
from pathlib import Path

FIVE = timedelta(minutes=5)


def read_csv(path):
    with path.open(newline='') as stream:
        return list(csv.DictReader(stream))


def require(condition, label):
    if not condition:
        raise AssertionError(label)


def audit(output):
    output = Path(output)
    spec = json.loads((output/'synthetic_contract.json').read_text())
    raw = read_csv(output/'synthetic_m5.csv')
    rows = {datetime.fromisoformat(r['start']):r for r in raw}
    require(len(rows)==len(raw), 'RAW_DUPLICATES')
    require(all(t.year==2023 for t in rows), 'RAW_PERIOD')
    tick = D(spec['tick'])
    side, stop = spec['direction'], D(spec['stop'])
    def good_open(row):
        if row is None:
            return False
        p = D(row['open'])
        return p.is_finite() and p>0 and p%tick==0
    def good(row):
        if row is None or row['problem'] or D(row['volume'])<=0:
            return False
        o,h,l,c = (D(row[k]) for k in ('open','high','low','close'))
        return all(x.is_finite() and x>0 and x%tick==0 for x in (o,h,l,c)) and l<=min(o,c)<=max(o,c)<=h
    ss = read_csv(output/'signals.csv')
    tt = read_csv(output/'trades.csv')
    skips = read_csv(output/'data_gap_skips.csv')
    excluded = read_csv(output/'data_quality_exclusions.csv')
    coverage = read_csv(output/'coverage_report.csv')
    metrics = json.loads((output/'metrics.json').read_text())
    for label, ledger in (('SIGNALS',ss),('TRADES',tt),('SKIPS',skips),('EXCLUDED',excluded)):
        require(len({r['signal_id'] for r in ledger})==len(ledger), label+'_DUPLICATES')
        require(all(r.get('status')!='UNKNOWN' for r in ledger), label+'_STATUS')
    expected_signals, expected_closed, expected_skips, expected_excluded = [], [], [], []
    prior_exclusion = False
    requests = [datetime.fromisoformat(t) for t in spec['signal_times']]
    for day_text in sorted({str(t.date()) for t in rows}):
        day = datetime.fromisoformat(day_text).replace(tzinfo=next(iter(rows)).tzinfo)
        blocked, active = False, None
        at = day
        while at <= day+timedelta(days=1):
            previous, current = rows.get(at-FIVE), rows.get(at)
            def close(price, reason, point=False, conflict=False):
                nonlocal active
                q = active
                gross = side*(price-q['entry_price'])
                costs = 2*tick
                q.update(exit_price=price, exit_reason=reason, gross=gross,
                         gross_R=gross/q['risk'], cost_c1=costs, cost_R=costs/q['risk'],
                         net_c1=gross-costs, net_R_c1=(gross-costs)/q['risk'],
                         exit_at=at if point else None,
                         exit_interval_start=at if point else at-FIVE,
                         exit_interval_end=at,
                         resolved_at=at, stop_take_conflict=conflict)
                expected_closed.append(q)
                active = None
            def exclude(reason, slot):
                nonlocal active, blocked
                active.update(exclusion_reason=reason, gap_interval_start=slot,
                              gap_interval_end=slot+FIVE, gap_detected_at=at)
                expected_excluded.append(active)
                active, blocked = None, True
            if active and active['entry_at'] <= at-FIVE < active['deadline']:
                if not good(previous):
                    exclude('MISSING_EXPOSED_BAR' if previous is None else 'INVALID_EXPOSED_BAR',at-FIVE)
                else:
                    stop_hit = D(previous['low'])<=stop if side==1 else D(previous['high'])>=stop
                    take_hit = D(previous['high'])>=active['take'] if side==1 else D(previous['low'])<=active['take']
                    if stop_hit:
                        close(stop,'STOP',conflict=take_hit)
                    elif take_hit and at-FIVE!=active['entry_at']:
                        close(active['take'],'TAKE')
            if active:
                if not good_open(current):
                    exclude('MISSING_EXPOSED_BAR' if current is None else 'INVALID_EXPOSED_OPEN',at)
                elif (D(current['open'])<=stop if side==1 else D(current['open'])>=stop):
                    close(D(current['open']),'STOP',point=True)
                elif at==active['deadline']:
                    reason = 'TIME' if at==active['entry_at']+timedelta(minutes=spec['hold_minutes']) else 'SESSION_FLAT'
                    close(D(current['open']),reason,point=True)
            if at in requests and good(previous):
                windows = [(datetime.fromisoformat(day_text+'T'+a).replace(tzinfo=at.tzinfo),
                            datetime.fromisoformat(day_text+'T'+z).replace(tzinfo=at.tzinfo)) for a,z in spec['windows']]
                window = next(((a,z) for a,z in windows if a<=at-FIVE<z),None)
                if window:
                    signal = dict(signal_id=str(at), signal_at=at, status='REJECTED',
                        reason='', model_filled=False,
                        prior_exclusion_requires_flat_assumption=prior_exclusion)
                    if blocked:
                        signal['reason']='DATA_QUALITY_POSITION_BLOCK'
                    elif active:
                        signal['reason']='POSITION_BUSY'
                    elif at>=window[1]-FIVE:
                        signal['reason']='SESSION_LIMIT'
                    elif not good_open(current):
                        signal.update(status='DATA_GAP_SKIP',reason='MISSING_EXECUTION_BAR' if current is None else 'INVALID_EXECUTION_OPEN')
                        expected_skips.append(signal)
                    else:
                        entry = D(current['open'])
                        risk = side*(entry-stop)
                        require(risk>0, 'FIXTURE_RISK')
                        take = ((entry+side*risk*D(spec['target_gross_R']))/tick).to_integral_value(
                            rounding=ROUND_CEILING if side==1 else ROUND_FLOOR)*tick
                        signal.update(status='MODEL_FILLED', model_filled=True)
                        active = dict(signal_id=str(at), entry_at=at, entry_price=entry,
                                      stop=stop, take=take, risk=risk,
                                      deadline=min(at+timedelta(minutes=spec['hold_minutes']),window[1]-FIVE),
                                      prior_exclusion_requires_flat_assumption=prior_exclusion)
                    expected_signals.append(signal)
            at += FIVE
        require(active is None,'DAY_UNRESOLVED')
        prior_exclusion |= blocked
    checked = 0
    def compare(actual, expected, label):
        nonlocal checked
        require({r['signal_id'] for r in actual}=={r['signal_id'] for r in expected},label+'_ROW_SET')
        by_id = {r['signal_id']:r for r in actual}
        for e in expected:
            for k,v in e.items():
                if k=='deadline':continue
                a = by_id[e['signal_id']].get(k,'')
                wanted = '' if v is None else str(v)
                require(a==wanted,label+' '+k+' '+e['signal_id'])
                checked += 1
    compare(ss,expected_signals,'SIGNAL')
    compare(tt,expected_closed,'CLOSED')
    compare(skips,expected_skips,'SKIP')
    compare(excluded,expected_excluded,'EXCLUDED')
    require(all(t['status']=='CLOSED' for t in tt),'TRADE_CLOSED_ONLY')
    for t in excluded:
        require(t['status']=='DATA_QUALITY_EXCLUDED' and t['model_filled']=='True','EXCLUSION_FILL')
        require(all(not t.get(k) for k in ('exit_price','exit_at','resolved_at','gross','gross_R','net_c1','net_R_c1','cost_c1')), 'EXCLUSION_NO_IMPUTATION')
    for c in coverage:
        slots = []
        for a,z in spec['windows']:
            at = datetime.fromisoformat(c['date']+'T'+a).replace(tzinfo=next(iter(rows)).tzinfo)
            end = datetime.fromisoformat(c['date']+'T'+z).replace(tzinfo=at.tzinfo)
            while at<end:
                slots.append(at);at+=FIVE
        missing = sum(t not in rows for t in slots)
        invalid = sum(t in rows and not good(rows[t]) for t in slots)
        counts = dict(expected_bars=len(slots),missing_bars=missing,invalid_bars=invalid,
            valid_bars=len(slots)-missing-invalid,
            accepted_entries=sum(s['model_filled'] for s in expected_signals if str(s['signal_at'])[:10]==c['date']),
            closed=sum(str(t['entry_at'])[:10]==c['date'] for t in expected_closed),
            data_gap_skips=sum(str(t['signal_at'])[:10]==c['date'] for t in expected_skips),
            data_quality_excluded=sum(str(t['entry_at'])[:10]==c['date'] for t in expected_excluded))
        for k,v in counts.items():
            require(int(c[k])==v,'COVERAGE '+k);checked+=1
        require(c['status']==('INCOMPLETE' if missing or invalid else 'COMPLETE'),'COVERAGE_STATUS')
        require(c['initial_flat_assumed']=='True' and c['initial_flat_proven']=='False','FLAT_ASSUMPTION')
    require({c['date'] for c in coverage}=={str(t.date()) for t in rows},'COVERAGE_DAYS')
    fills = sum(s['model_filled']=='True' for s in ss)
    require(fills==len(tt)+len(excluded),'ENTRY_IDENTITY')
    counts = dict(accepted_entries=fills,closed=len(tt),data_gap_skips=len(skips),data_quality_excluded=len(excluded))
    for k,v in counts.items():
        require(metrics['totals_counts_only'][k]==v,'TOTAL '+k)
        require(metrics['instruments'][spec['instrument']][k]==v,'INSTRUMENT '+k)
    fraction = str(D(len(excluded))/fills) if fills else None
    require(metrics['totals_counts_only']['exclusion_fraction']==fraction,'EXCLUSION_FRACTION')
    econ = metrics['instruments'][spec['instrument']]['conditional_closed_only_C1']
    for k in ('Net_R','Net_price','cost_C1'):
        field = {'Net_R':'net_R_c1','Net_price':'net_c1','cost_C1':'cost_c1'}[k]
        require(D(econ[k])==sum((D(t[field]) for t in tt),D(0)),'ECON '+k)
    for field,key in (('net_c1','PF_C1_price'),('net_R_c1','PF_C1_R')):
        values = [D(t[field]) for t in tt]
        gains = sum((v for v in values if v>0),D(0))
        losses = -sum((v for v in values if v<0),D(0))
        require(econ[key]==(str(gains/losses) if losses else None),'PF '+key)
    rs = [D(t['net_R_c1']) for t in sorted(tt,key=lambda t:(t['resolved_at'],t['signal_id']))]
    curve = peak = drawdown = D(0)
    for r in rs:
        curve += r;peak=max(peak,curve);drawdown=max(drawdown,peak-curve)
    expected_metrics = dict(closed=len(rs),
        Expectancy_R=str(sum(rs,D(0))/len(rs)) if rs else None,
        Win_Rate=str(D(sum(r>0 for r in rs))/len(rs)) if rs else None,
        Max_DD_R=str(drawdown) if rs else None,
        PF_no_losses=bool(tt) and not any(D(t['net_c1'])<0 for t in tt))
    for k,v in expected_metrics.items():
        require(econ[k]==v,'ECON '+k)
    require(metrics['instruments'][spec['instrument']]['exclusion_fraction']==fraction,'INSTRUMENT_EXCLUSION_FRACTION')
    require(metrics['annual_account_returns'] is None and metrics['annual_economics'] is None,'NO_ANNUAL_CLAIM')
    require(bool(metrics['data_quality_warning']),'SELECTION_BIAS_DISCLOSURE')
    return dict(status='PASS',checked_path_and_coverage_fields=checked,counts=counts,
                independent_imports='Python standard library only',
                scope='Synthetic M5 technical fixtures; no historical strategy evaluation',
                external_human_signoff=False)


if __name__=='__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    print(json.dumps(audit(p.parse_args().output),sort_keys=True))
