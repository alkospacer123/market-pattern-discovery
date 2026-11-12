"""Final offline aggregation of nine EXISTING regime implementations.

No quote replay, indicator search, new threshold, trading hook or dependency.
See REGIME_FINAL_COMPARISON_PROTOCOL_RU.md. Evaluation columns are never
passed into the state lookup or signal assignment.
"""
from __future__ import annotations

import argparse
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
import csv
from datetime import datetime, timedelta
import gzip
import hashlib
import io
import json
from pathlib import Path
from statistics import mean, median

from .regime_research import METHODS as OLD_METHODS, dump_csv
from .confirmed_market_regime import confirmed_card, load_published
from .regime_evidence import evidence_card, exact_lower_tail
from .market_epochs import ROOT, ZIP_SHA
from .market_rolling_raw import RAW_PATH, RAW_SHA

FOLDER = ROOT/'V20-04'
METHODS = (*OLD_METHODS, 'TWO_BLOCK_20', 'REGIME_EVIDENCE')
GOOD, BAD, UNKNOWN = 'FAVORABLE', 'WARNING', 'INSUFFICIENT'
DAY = 86400
MONTH_DAYS = 365.25/12
INPUT_HEAD = '93561e7a57f0623a1180810f57beb46977359c97'


def dt(value):
    return datetime.fromisoformat(value) if isinstance(value,str) else value


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path):
    opener=gzip.open if str(path).endswith('.gz') else open
    with opener(path,'rt',encoding='utf-8',newline='') as stream:
        yield from csv.DictReader(stream)


def load_inputs(archive=None):
    names=('REGIME_EVENTS.csv','REGIME_BLOCKS.csv','REGIME_PERIODS.csv','REGIME_RESULTS.json',
           'REGIME_TIMELINE.csv.gz','REGIME_ER_M15.csv.gz','REGIME_VERIFICATION.json')
    manifest=json.loads((FOLDER/'REGIME_ARTIFACT_MANIFEST.json').read_text())
    hashes={}
    for name in names:
        path=FOLDER/name
        value=digest(path)
        if value!=manifest['artifacts'][str(path.relative_to(ROOT.parent))]['sha256']:
            raise ValueError('UNCHANGED_INPUT_SHA_FAILED_'+name)
        hashes[name]=value
    if digest(RAW_PATH)!=RAW_SHA:
        raise ValueError('RAW_SOURCE_SHA_CHANGED')
    hashes['QUOTE_PATH_DIAGNOSTICS.csv']=RAW_SHA
    if archive is not None and digest(archive)!=ZIP_SHA:
        raise ValueError('ZIP_SHA_CHANGED')
    hashes['2018-2022.zip']=ZIP_SHA
    events=[]
    for source in load_published():
        row=dict(source)
        for key in ('signal','available','entry_time'):
            row[key]=dt(row[key])
        for key in ('raw_R','stop_aware'):
            row[key]=float(row[key])
        for key in ('fp2','fp5'):
            row[key]=int(row[key])
        row['stop_touch']=row['stop_touch']=='True'
        events.append(row)
    groups=defaultdict(list)
    for r in events:
        groups[r['instrument']].append(r)
    results=json.loads((FOLDER/'REGIME_RESULTS.json').read_text())
    bounds={r['instrument']:(dt(r['quote_start']),dt(r['quote_end'])) for r in results['coverage']}
    periods=[dict(r,**{key:dt(r[key]) for key in ('start','end','label_available')})
             for r in read_csv(FOLDER/'REGIME_PERIODS.csv')]
    for r in periods:
        if r['kind']=='STRONG':
            r['kind']='RECOVERY'  # label name only, unchanged stored intervals
    blocks=[dict(r,**{key:dt(r[key]) for key in ('start','end')})
            for r in read_csv(FOLDER/'REGIME_BLOCKS.csv')]
    # Only metadata of censored raw, never invent its unknown numeric result.
    by_key={(r['instrument'],r['signal']):r for r in events}
    signals={}
    for r in read_csv(RAW_PATH):
        if r['record_type']!='RAW_SIGNAL':
            continue
        key=(r['instrument'],dt(r['signal_bar_dt']))
        if key in signals:
            if signals[key]['horizon_status']!=r['horizon_status']:
                raise ValueError('CENSORED_DUPLICATE_STATUS_CONFLICT')
            continue
        outcome=by_key.get(key)
        signals[key]=dict(instrument=key[0],signal=key[1],decision=key[1]+timedelta(minutes=15),
                          horizon_status=r['horizon_status'],outcome=outcome)
        if outcome is not None and (outcome['entry_time']!=signals[key]['decision'] or
                                   outcome['available']<=signals[key]['decision']):
            raise ValueError('SIGNAL_OWN_OUTCOME_NOT_FUTURE')
    hashes.update({name:digest(Path(__file__).with_name(name)) for name in
                   ('confirmed_market_regime.py','regime_evidence.py','instrument_regime.py','regime_research.py')})
    return groups,bounds,periods,blocks,list(signals.values()),hashes


class Track:
    def __init__(self,points,start,end):
        values={start:UNKNOWN}
        values.update({t:s for t,s in points if start<=t<=end})
        self.points=[]
        for t,s in sorted(values.items()):
            if not self.points or s!=self.points[-1][1]:
                self.points.append((t,s))
        self.times=[t for t,_ in self.points]
        self.start,self.end=start,end

    def at(self,t):
        if t<self.start or t>self.end:
            return UNKNOWN
        i=bisect_right(self.times,t)-1
        return self.points[i][1] if i>=0 else UNKNOWN

    def spans(self):
        return [(t,self.points[i+1][0] if i+1<len(self.points) else self.end,s)
                for i,(t,s) in enumerate(self.points)]


def build_tracks(groups,bounds):
    points=defaultdict(list)
    mapping={'NORMAL':GOOD,'WARNING':BAD,'UNKNOWN':UNKNOWN}
    for filename in ('REGIME_TIMELINE.csv.gz','REGIME_ER_M15.csv.gz'):
        for r in read_csv(FOLDER/filename):
            t=dt(r['as_of'])
            for method in OLD_METHODS:
                if method in r:
                    points[r['instrument'],method].append((t,mapping[r[method]]))
    for symbol,rows in groups.items():
        start,end=bounds[symbol]
        times={start,end}|{r['available'] for r in rows}
        # Exact calls to the existing freshness semantics, not a new indicator.
        for r in rows:
            for offset in (timedelta(days=90,microseconds=1),timedelta(days=91)):
                t=r['available']+offset
                if start<t<end:
                    times.add(t)
        for t in sorted(times):
            card=confirmed_card(rows,symbol,as_of=t)
            value=card['historical_observation']
            state=(BAD if value=='CONFIRMED_OBSERVED_WEAK' else
                   GOOD if value=='CONFIRMED_OBSERVED_FAVORABLE' else UNKNOWN)
            points[symbol,'TWO_BLOCK_20'].append((t,state))
            card=evidence_card(rows,symbol,t)
            value=card['last_status']
            state=(BAD if value=='FP2_DROP_EVIDENCE' else
                   GOOD if value=='FP2_RECOVERY_EVIDENCE' else UNKNOWN)
            points[symbol,'REGIME_EVIDENCE'].append((t,state))
        print('existing states',symbol,len(rows),'as-of calls',len(times),flush=True)
    return {(s,m):Track(points[s,m],*bounds[s]) for s in groups for m in METHODS}


def mean_of(rows,key):
    return mean(r[key] for r in rows) if rows else None


def quality(signals):
    rows=[s['outcome'] for s in signals if s['outcome'] is not None]
    values=[r['raw_R'] for r in rows]
    return dict(total_raw=len(signals),observed=len(rows),censored=len(signals)-len(rows),
        raw_R=mean(values) if values else None,median_raw_R=median(values) if values else None,
        stop_aware_R=mean_of(rows,'stop_aware'),fp2=mean_of(rows,'fp2'),fp5=mean_of(rows,'fp5'),
        stop_share=mean_of(rows,'stop_touch'),positive=sum(v>0 for v in values),
        negative=sum(v<0 for v in values),zero=sum(v==0 for v in values),
        positive_share=sum(v>0 for v in values)/len(values) if values else None,
        negative_share=sum(v<0 for v in values)/len(values) if values else None,
        first_signal=min((s['decision'] for s in signals),default=None),
        last_signal=max((s['decision'] for s in signals),default=None))


def assign_signals(signals,track):
    """Only timestamp lookup before inspecting the outcome; own path is future."""
    return [dict(s,state=track.at(s['decision'])) for s in signals]


def episode_spans(track):
    alerts=[]
    returns=[]
    armed=None
    spans=track.spans()
    for i,(start,end,state) in enumerate(spans):
        if state==BAD:
            armed=dict(start=start,end=end,cleared_at=end if i+1<len(spans) else None,
                       cleared_to=spans[i+1][2] if i+1<len(spans) else None)
            alerts.append(armed)
        elif state==GOOD and armed is not None:
            returns.append(dict(start=start,end=end,prior_warning=armed['start']))
            armed=None
    return alerts,returns


def evaluate_episode(rows,episode,kind):
    """Common external evaluation, no FP2/cohort labels in the classification."""
    t=episode['start']
    times=[r['available'] for r in rows]
    n=bisect_right(times,t)
    current,previous=rows[max(0,n-20):n],rows[max(0,n-40):max(0,n-20)]
    baseline=len(current)==len(previous)==20
    before_raw=mean_of(previous,'raw_R') if baseline else None
    before_sa=mean_of(previous,'stop_aware') if baseline else None
    future=rows[n:n+40]
    first,second=future[:20],future[20:40]
    sa1=mean_of(first,'stop_aware') if len(first)==20 else None
    sa2=mean_of(second,'stop_aware') if len(second)==20 else None
    persistence=('WEAK' if sa1 is not None and sa2 is not None and sa1<0 and sa2<0 else
                 'RECOVERED' if sa1 is not None and sa2 is not None and sa1>=0 and sa2>=0 else 'UNRESOLVED')
    verdict=('UNRESOLVED' if persistence=='UNRESOLVED' else
             'TRUE' if (persistence=='WEAK')==(kind=='WARNING') else 'FALSE')
    raw_at,sa_at=mean_of(current,'raw_R'),mean_of(current,'stop_aware')
    minimum_raw,minimum_sa=raw_at,sa_at
    returned_at=returned_n=None
    # At a close all simultaneous paths are known; never expose a partial batch.
    for ready in sorted({r['available'] for r in future}):
        end=bisect_right(times,ready)
        q=rows[max(0,end-20):end]
        if len(q)!=20:
            continue
        raw,sa=mean_of(q,'raw_R'),mean_of(q,'stop_aware')
        minimum_raw=min(minimum_raw,raw) if minimum_raw is not None else raw
        minimum_sa=min(minimum_sa,sa) if minimum_sa is not None else sa
        if baseline and returned_at is None and raw>=before_raw and sa>=before_sa:
            returned_at,returned_n=ready,end-n
    return_known=(True if returned_at else False if baseline and len(future)==40 else None)
    outcome=('CONTINUED_WEAK' if persistence=='WEAK' else
             'FULL_RETURN' if persistence=='RECOVERED' and returned_at else
             'PARTIAL_RETURN' if persistence=='RECOVERED' and baseline else 'UNRESOLVED')
    cleared=episode.get('cleared_at')
    cleared_early=(cleared<returned_at if cleared and returned_at else
                   True if cleared and baseline and len(future)==40 and cleared<=future[-1]['available'] else None)
    return dict(kind=kind,**episode,known_n=n,current_n=len(current),previous_n=len(previous),
        raw_before=before_raw,raw_at=raw_at,stop_aware_before=before_sa,stop_aware_at=sa_at,
        minimum_subsequent_raw20=minimum_raw,minimum_subsequent_stop_aware20=minimum_sa,
        next20_n=len(first),next20_raw_R=mean_of(first,'raw_R') if len(first)==20 else None,
        next20_stop_aware_R=sa1,next21_40_n=len(second),next21_40_stop_aware_R=sa2,
        next40_n=len(future),next40_raw_R=mean_of(future,'raw_R') if len(future)==40 else None,
        next40_stop_aware_R=mean_of(future,'stop_aware') if len(future)==40 else None,
        evaluation_available=future[-1]['available'] if len(future)==40 else None,
        pending_at_warning=sum(r['entry_time']<=t for r in future),
        persistence=persistence,verdict=verdict,outcome=outcome,
        full_return_observed=return_known,full_return_at=returned_at,full_return_new_n=returned_n,
        full_return_days=(returned_at-t).total_seconds()/DAY if returned_at else None,
        cleared_before_full_return=cleared_early)


def detect_periods(track,periods,blocks):
    spans=track.spans()
    _,announced_returns=episode_spans(track)
    out=[]
    for r in periods:
        desired=BAD if r['kind']=='WEAK' else GOOD
        matching=[(a,b,s) for a,b,s in spans if s==desired and a<=r['end'] and b>r['start']]
        when=max(r['start'],matching[0][0]) if matching else None
        previous_weak=max((p['start'] for p in periods if p['kind']=='WEAK' and p['start']<r['start']),default=None)
        real_returns=[a for a in announced_returns if previous_weak is not None and
            previous_weak<=a['start']<=r['end'] and a['end']>r['start']] if r['kind']=='RECOVERY' else []
        out.append(dict(kind=r['kind'],start=r['start'],end=r['end'],label_available=r['label_available'],
            detected_at=when,missed=when is None,
            delay_days=(when-r['start']).total_seconds()/DAY if when else None,
            delay_months=(when-r['start']).total_seconds()/DAY/MONTH_DAYS if when else None,
            confirmation_at_period_end=when==r['end'] if when else False,
            actual_recovery_transition=bool(real_returns),
            recovery_transition_at=real_returns[0]['start'] if real_returns else None))
    covered=0
    for r in blocks:
        if r['kind']=='WEAK' and any(s==BAD and a<=r['end'] and b>r['start'] for a,b,s in spans):
            covered+=1
    return out,covered


def months_until(end):
    t=datetime(2018,1,1)
    while t<end:
        following=datetime(t.year+(t.month==12),t.month%12+1,1)
        yield t,min(following,end),following
        t=following


def seconds_between(track,start,end):
    seconds={GOOD:0.0,BAD:0.0,UNKNOWN:0.0}
    for a,b,s in track.spans():
        seconds[s]+=max(0.0,(min(end,b)-max(start,a)).total_seconds())
    available=max(0.0,(min(end,track.end)-max(start,track.start)).total_seconds())
    outside=(end-start).total_seconds()-available
    seconds[UNKNOWN]+=outside
    return seconds,available


def filter_result(signals,policy):
    selected=[s for s in signals if (s['state']!=BAD if policy=='NOT_BAD' else s['state']==GOOD)]
    excluded=[s for s in signals if (s['state']==BAD if policy=='NOT_BAD' else s['state']!=GOOD)]
    kept,removed=quality(selected),quality(excluded)
    all_stats=quality(signals)
    return dict(policy=policy,**kept,all_raw=all_stats['total_raw'],all_observed=all_stats['observed'],
        all_mean_raw_R=all_stats['raw_R'],excluded=removed['total_raw'],
        excluded_observed=removed['observed'],excluded_positive=removed['positive'],
        excluded_negative=removed['negative'],excluded_censored=removed['censored'],
        excluded_positive_share=removed['positive']/all_stats['positive'] if all_stats['positive'] else None)


def quantile(values,p):
    if not values:
        return None
    values=sorted(values);i=(len(values)-1)*p;lo=int(i);hi=min(lo+1,len(values)-1)
    return values[lo]+(i-lo)*(values[hi]-values[lo])


def distribution(values):
    return dict(n=len(values),mean=mean(values) if values else None,median=median(values) if values else None,
                minimum=min(values) if values else None,maximum=max(values) if values else None,p90=quantile(values,.9))


def summary(monthly,signals,alerts,returns,detections,block_checks=()):
    elapsed=sum(r['available_days'] for r in monthly)
    good=sum(r['available_favorable_days'] for r in monthly)
    bad=sum(r['warning_days'] for r in monthly)
    warnings=[a for a in alerts if a['kind']=='WARNING']
    weak=[d for d in detections if d['kind']=='WEAK']
    recovery=[d for d in detections if d['kind']=='RECOVERY']
    delays=[d['delay_days'] for d in weak if not d['missed']]
    recovery_delays=[d['delay_days'] for d in recovery if not d['missed']]
    return dict(warnings=len(warnings),true=sum(a['verdict']=='TRUE' for a in warnings),
        false=sum(a['verdict']=='FALSE' for a in warnings),unresolved=sum(a['verdict']=='UNRESOLVED' for a in warnings),
        full_returns=sum(a['full_return_observed'] is True for a in warnings),
        partial_returns=sum(a['outcome']=='PARTIAL_RETURN' for a in warnings),
        continued_weak=sum(a['persistence']=='WEAK' for a in warnings),
        cleared_early=sum(a['cleared_before_full_return'] is True for a in warnings),
        recovery_announcements=len(returns),false_recoveries=sum(a['verdict']=='FALSE' for a in returns),
        true_recoveries=sum(a['verdict']=='TRUE' for a in returns),
        unresolved_recoveries=sum(a['verdict']=='UNRESOLVED' for a in returns),
        weak_periods=len(weak),missed=sum(d['missed'] for d in weak),
        detected_at_period_end=sum(d['confirmation_at_period_end'] for d in weak),
        recovery_periods=len(recovery),missed_recoveries=sum(d['missed'] for d in recovery),
        actual_recovery_transitions=sum(d['actual_recovery_transition'] for d in recovery),
        weak_blocks=len(block_checks),missed_weak_blocks=sum(d['missed'] for d in block_checks),
        delays=distribution(delays),recovery_delays=distribution(recovery_delays),
        coverage=(good+bad)/elapsed if elapsed else None,available_days=elapsed,
        favorable_days=good,warning_days=bad,insufficient_days=elapsed-good-bad,
        status_changes=sum(r['status_changes'] for r in monthly),
        not_bad=filter_result(signals,'NOT_BAD'),only_favorable=filter_result(signals,'ONLY_FAVORABLE'))


def build(output,archive=None):
    groups,bounds,periods,blocks,signals,hashes=load_inputs(archive)
    tracks=build_tracks(groups,bounds)
    all_end=max(b for _,b in bounds.values())
    monthly,filtered,assigned,alerts,returns,detections,status_rows=[],[],[],[],[],[],[]
    block_checks=[]
    for symbol,rows in sorted(groups.items()):
        source_signals=sorted((s for s in signals if s['instrument']==symbol),key=lambda s:s['decision'])
        for method in METHODS:
            track=tracks[symbol,method]
            selected=assign_signals(source_signals,track)
            assigned.extend(dict(method=method,**s) for s in selected)
            warn,restore=episode_spans(track)
            warning_rows=[dict(instrument=symbol,method=method,**evaluate_episode(rows,a,'WARNING')) for a in warn]
            recovery_rows=[dict(instrument=symbol,method=method,**evaluate_episode(rows,a,'RECOVERY')) for a in restore]
            alerts.extend(warning_rows);returns.extend(recovery_rows)
            truth,covered=detect_periods(track,[r for r in periods if r['instrument']==symbol],
                                        [r for r in blocks if r['instrument']==symbol])
            detections.extend(dict(instrument=symbol,method=method,**r) for r in truth)
            checked,_=detect_periods(track,[dict(r,label_available=r['end']) for r in blocks
                if r['instrument']==symbol and r['kind']=='WEAK'],[])
            block_checks.extend(dict(instrument=symbol,method=method,**r) for r in checked)
            for start,end,next_month in months_until(all_end):
                q=[s for s in selected if start<=s['decision']<end]
                stats=quality(q)
                sec,available=seconds_between(track,start,end)
                new=[a for a in warning_rows if start<=a['start']<end]
                rec=[a for a in recovery_rows if start<=a['start']<end]
                det=[d for d in truth if d['kind']=='WEAK' and d['detected_at'] is not None
                     and start<=d['detected_at']<end]
                missed=[d for d in truth if d['kind']=='WEAK' and d['missed'] and start<=d['end']<end]
                recovered=[d for d in truth if d['kind']=='RECOVERY' and d['detected_at'] is not None
                           and start<=d['detected_at']<end]
                delay=[d['delay_days'] for d in det]
                recovery_delay=[d['delay_days'] for d in recovered]
                as_of=end-timedelta(microseconds=1) if end==next_month else end
                known=[s for s in q if s['outcome'] and s['outcome']['available']<=as_of]
                end_status=track.at(as_of)
                monthly.append(dict(instrument=symbol,method=method,month=start.strftime('%Y-%m'),
                    month_start=start,month_end=end,partial_month=end!=next_month,
                    start_status=track.at(start),end_status=end_status,
                    month_evidence_status=UNKNOWN if not q or end_status==UNKNOWN else 'OBSERVED_METHOD_STATE',
                    status_changes=sum(start<=t<end for t,_ in track.points[1:]),
                    new_warnings=len(new),false_warnings=sum(a['verdict']=='FALSE' for a in new),
                    unresolved_warnings=sum(a['verdict']=='UNRESOLVED' for a in new),
                    full_returns_of_new_warnings=sum(a['full_return_observed'] is True for a in new),
                    full_returns_completed_this_month=sum(a['full_return_at'] is not None and
                        start<=a['full_return_at']<end for a in warning_rows),
                    weak_periods_starting_this_month=sum(d['kind']=='WEAK' and start<=d['start']<end for d in truth),
                    detected_weak=len(det),missed_weak=len(missed),
                    weak_detection_dates=[d['detected_at'].isoformat(sep=' ') for d in det],
                    mean_delay_days=mean(delay) if delay else None,max_delay_days=max(delay) if delay else None,
                    new_recoveries=len(rec),false_recoveries=sum(a['verdict']=='FALSE' for a in rec),
                    recovery_announcement_dates=[a['start'].isoformat(sep=' ') for a in rec],
                    detected_historical_recoveries=len(recovered),
                    historical_recovery_detection_dates=[d['detected_at'].isoformat(sep=' ') for d in recovered],
                    mean_recovery_delay_days=mean(recovery_delay) if recovery_delay else None,
                    max_recovery_delay_days=max(recovery_delay) if recovery_delay else None,
                    available_days=available/DAY,available_favorable_days=sec[GOOD]/DAY,
                    warning_days=sec[BAD]/DAY,insufficient_days=sec[UNKNOWN]/DAY,
                    known_month_outcomes_n=len(known),known_month_raw_R=quality(known)['raw_R'],**stats))
                for policy in ('NOT_BAD','ONLY_FAVORABLE'):
                    filtered.append(dict(instrument=symbol,method=method,month=start.strftime('%Y-%m'),
                                         **filter_result(q,policy)))
    # All-symbol monthly means weight unique events, not averages of instrument means.
    for method in METHODS:
        for start,end,_ in months_until(all_end):
            q=[s for s in assigned if s['method']==method and start<=s['decision']<end]
            for policy in ('NOT_BAD','ONLY_FAVORABLE'):
                filtered.append(dict(instrument='ALL',method=method,month=start.strftime('%Y-%m'),**filter_result(q,policy)))
    summaries={}
    scopes=[('ALL',None,None),('2018-2022',None,(2018,2022)),('2023-2026',None,(2023,2026))]
    scopes += [(s,s,None) for s in groups]
    scopes += [(str(y),None,(y,y)) for y in range(2018,2027)]
    comparisons=[]
    for scope,symbol,years in scopes:
        summaries[scope]={}
        def included(s,t):
            return (symbol is None or s==symbol) and (years is None or years[0]<=t.year<=years[1])
        for method in METHODS:
            mm=[r for r in monthly if r['method']==method and included(r['instrument'],r['month_start'])]
            ss=[s for s in assigned if s['method']==method and included(s['instrument'],s['decision'])]
            aa=[a for a in alerts if a['method']==method and included(a['instrument'],a['start'])]
            rr=[a for a in returns if a['method']==method and included(a['instrument'],a['start'])]
            dd=[d for d in detections if d['method']==method and included(d['instrument'],d['start'])]
            bb=[d for d in block_checks if d['method']==method and included(d['instrument'],d['start'])]
            stats=summary(mm,ss,aa,rr,dd,bb)
            summaries[scope][method]=stats
            flat={k:v for k,v in stats.items() if not isinstance(v,dict)}
            for field in ('delays','recovery_delays'):
                flat.update({field+'_'+k:v for k,v in stats[field].items()})
            for field in ('not_bad','only_favorable'):
                flat.update({field+'_'+k:v for k,v in stats[field].items()})
            comparisons.append(dict(scope=scope,method=method,**flat))
            for state in (GOOD,BAD,UNKNOWN):
                q=[s for s in ss if s['state']==state]
                status_rows.append(dict(scope=scope,method=method,state=state,**quality(q)))
    serious=[a for a in alerts if a['verdict']=='FALSE' and (a['end']-a['start']).total_seconds()/DAY>=20]
    late=[d for d in detections if d['delay_days'] is not None and d['delay_days']>90]
    output.mkdir(parents=True,exist_ok=True)
    dump_csv(output/'REGIME_MONTHLY_COMPARISON.csv',monthly)
    dump_csv(output/'REGIME_METHOD_COMPARISON.csv',comparisons)
    dump_csv(output/'REGIME_ALERT_EPISODES.csv',alerts+returns)
    dump_csv(output/'REGIME_FILTERED_RAW_MONTHLY.csv',filtered)
    dump_csv(output/'REGIME_FILTERED_RAW_BY_STATUS.csv',status_rows)
    dump_csv(output/'REGIME_FINAL_DETECTIONS.csv',detections)
    dump_csv(output/'REGIME_FINAL_BLOCK_DETECTIONS.csv',block_checks)
    dump_csv(output/'REGIME_SERIOUS_FALSE_ALERTS.csv',serious)
    dump_csv(output/'REGIME_SERIOUS_DELAYS.csv',late)
    audit=[]
    for s in assigned:
        track=tracks[s['instrument'],s['method']]
        t=s['decision'];i=bisect_right(track.times,t)-1
        state_time=track.times[i] if i>=0 and track.start<=t<=track.end else None
        known=bisect_right([e['available'] for e in groups[s['instrument']]],t)
        audit.append(dict(instrument=s['instrument'],method=s['method'],signal=s['signal'],decision=t,
            state=s['state'],state_available=state_time,known_completed_n=known,
            own_outcome_available=s['outcome']['available'] if s['outcome'] else None,
            censor_reason=s['horizon_status'] if s['outcome'] is None else None))
    dump_csv(output/'REGIME_SIGNAL_ASSIGNMENTS.csv.gz',audit,compressed=True)
    dump_csv(output/'REGIME_ADDITIONAL_STATE_CHANGES.csv',[
        dict(instrument=s,method=m,as_of=t,state=state) for (s,m),track in tracks.items()
        if m in ('TWO_BLOCK_20','REGIME_EVIDENCE') for t,state in track.points])
    result=dict(schema='v20.regime_final_monthly.v1',input_head=INPUT_HEAD,
        main='6f352acfac7ebdfabba73e143c4dfea3a6e48507',source_sha256=hashes,
        protocol_sha256=digest(FOLDER/'REGIME_FINAL_COMPARISON_PROTOCOL_RU.md'),
        source_quote_reaudit='NOT_REPEATED_UNCHANGED_SHA',source_unique_observed=sum(map(len,groups.values())),
        source_unique_raw=len(signals),source_unique_censored=sum(s['outcome'] is None for s in signals),
        unique_censored_by_status=dict(Counter(s['horizon_status'] for s in signals if s['outcome'] is None)),
        original_quote_sha256=json.loads((FOLDER/'REGIME_RESULTS.json').read_text())['provenance']['source_sha256'],
        archive_bounds=bounds,monthly_rows=len(monthly),filtered_monthly_rows=len(filtered),
        summary=summaries,predictive_claim=False,independent_oos=False,card_changed=False,
        relative_choice='RAW20_CONFIRM5',unconditional_reliability='FAIL',
        recommendation_basis='No missed sustained periods, substantially less churn than RAW20, coverage and delay; NOT maximum filtered raw',
        card_action='KEEP_EXISTING_READONLY_NO_VALIDATED_REPLACEMENT',
        arithmetic_fix=dict(regime_evidence_recovery_upper_tail=
            'Fixed reversed failure groups in up_p, no parameter changes; historical evidence remains unproven',
            recovery_example_before_p=exact_lower_tail(80,20,80,60),
            recovery_example_correct_upper_p=exact_lower_tail(80,60,80,20)))
    (output/'REGIME_FINAL_COMPARISON.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str)+'\n')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',type=Path)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    result=build(args.output,args.archive)
    print(json.dumps({k:result[k] for k in ('source_unique_observed','source_unique_raw','monthly_rows')}))


if __name__=='__main__':
    main()
