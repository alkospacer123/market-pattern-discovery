"""Bounded, offline 20/60 C1 suitability experiment; no trading integration.

Protocol: V20-04/V20_SUITABILITY_PROTOCOL_RU.md. Shadow observations come
from existing executable baseline ledgers, not raw-path proxies. Future path
diagnostics are joined only after their own horizon. No quote-path audit here.
"""
from __future__ import annotations
import argparse
from bisect import bisect_right
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import json
from pathlib import Path
from statistics import mean, stdev, median

from .regime_monthly_comparison import (ROOT, FOLDER, dt, digest, read_csv,
    Track, GOOD, BAD, UNKNOWN, months_until, seconds_between)
from .regime_research import dump_csv
from .market_rolling_raw import RAW_PATH, RAW_SHA

MODES=('SHALLOW_PULLBACK','OBV_PRESSURE','INSIDE_DAY_RELEASE')
METHODS=('BASELINE','RAW20_CONFIRM5','TWO_BLOCK_20','EDGE_20_60','EDGE_20_60_ROTATION')
OLD=('CNY','MIX','Si')
NEW=('CNYRUBF','GLDRUBF','IMOEXF','USDRUBF')
STEP=timedelta(minutes=15)
AGE=timedelta(days=90)
INPUT_HEAD='18ac9f466a8a67b33fa3983cf45cb18736970077'


def result_available(exit_time, reason):
    """High/Low are known at CLOSE; Open exits are known at their timestamp."""
    return dt(exit_time)+(STEP if int(reason) in (1,4) else timedelta())


def trade_row(r, modern=False):
    instrument=r['symbol'] if modern else r['family']
    return dict(strategy=r['account'],instrument=instrument,
        contract=instrument if modern else r['contract'],entry=dt(r['entry_dt']),
        signal=dt(r['entry_dt'])-STEP,exit=dt(r['exit_dt']),
        available=result_available(r['exit_dt'],r['exit_reason']),
        gross=float(r['gross_R']),net=float(r['net_R'] if modern else r['net_C1_R']),
        stop=int(r['exit_reason']) in (1,2,4),reason=int(r['exit_reason']))


def load_sources():
    hashes={}
    old=ROOT/'V20-03/results/CLOSED_TRADES.csv'
    late=ROOT/'V20-03/comparison/DIAGNOSTIC_REPLAY_TRADES.csv'
    expected=json.loads((old.parent/'RESULT_HASHES.json').read_text())
    verify=json.loads((late.parent/'VERIFICATION.json').read_text())
    for p,want in ((old,expected[old.name]),(late,verify['artifact_hashes'][late.name]),(RAW_PATH,RAW_SHA)):
        assert digest(p)==want, p
        hashes[str(p.relative_to(ROOT))]=want
    manifest=json.loads((FOLDER/'REGIME_FINAL_ARTIFACT_MANIFEST.json').read_text())['artifacts']
    for name in ('REGIME_EVENTS.csv','REGIME_TIMELINE.csv.gz','REGIME_ADDITIONAL_STATE_CHANGES.csv',
                 'REGIME_SIGNAL_ASSIGNMENTS.csv.gz','REGIME_FINAL_COMPARISON.json'):
        p=FOLDER/name
        # Original event/timeline receipts live in the earlier manifest.
        record=manifest.get(str(p.relative_to(ROOT.parent)))
        if record is None:
            record=json.loads((FOLDER/'REGIME_ARTIFACT_MANIFEST.json').read_text())['artifacts'][str(p.relative_to(ROOT.parent))]
        assert digest(p)==record['sha256'],p
        hashes[str(p.relative_to(ROOT))]=record['sha256']
    rows=[trade_row(r) for r in read_csv(old)]+[trade_row(r,True) for r in read_csv(late)]
    assert len(rows)==2593 and len({(r['strategy'],r['instrument'],r['entry']) for r in rows})==2593
    groups=defaultdict(list)
    for r in rows: groups[r['strategy'],r['instrument']].append(r)
    for key in groups: groups[key].sort(key=lambda r:(r['available'],r['signal'],r['contract']))
    result=json.loads((FOLDER/'REGIME_RESULTS.json').read_text())
    bounds={r['instrument']:(dt(r['quote_start']),dt(r['quote_end'])) for r in result['coverage']}
    events={(r['instrument'],dt(r['signal'])):r for r in read_csv(FOLDER/'REGIME_EVENTS.csv')}
    for row in rows:
        row['path']=events.get((row['instrument'],row['signal']))
    raw=[]
    for r in read_csv(RAW_PATH):
        if r['record_type']!='RAW_SIGNAL':continue
        signal=dt(r['signal_bar_dt']);event=events.get((r['instrument'],signal))
        raw.append(dict(strategy=r['strategy'],instrument=r['instrument'],signal=signal,
                        decision=signal+STEP,horizon_status=r['horizon_status'],outcome=event,
                        risk=float(r['risk']) if r['risk'] else None,
                        initial_stop=float(r['stop']) if r['stop'] else None,
                        entry_price=float(r['entry']) if r['entry'] else None,side=int(r['side'])))
    assert len(raw)==4986
    return groups,bounds,raw,hashes


def performance(rows,as_of=None):
    a=[r['net'] for r in rows];w=[x for x in a if x>0];l=[x for x in a if x<0]
    avg=mean(a) if a else None
    se=stdev(a)/len(a)**.5 if len(a)>1 else None
    paths=[r['path'] for r in rows if r.get('path') is not None and
           (as_of is None or dt(r['path']['available'])<=as_of)]
    return dict(n=len(a),net_mean=avg,gross_mean=mean(r['gross'] for r in rows) if a else None,
        net_sum=sum(a),PF_C1=sum(w)/-sum(l) if l else None,
        PF_status='FINITE' if l else 'NO_LOSSES_UNDEFINED' if a else 'NO_TRADES',
        win_mean=mean(w) if w else None,loss_mean=mean(l) if l else None,
        win_rate=len(w)/len(a) if a else None,positive=len(w),negative=len(l),
        initial_stop_share=mean(r['stop'] for r in rows) if rows else None,
        ci95_low=avg-1.96*se if se is not None else None,
        ci95_high=avg+1.96*se if se is not None else None,
        first_entry=min((r['entry'] for r in rows),default=None),
        last_result=max((r['available'] for r in rows),default=None),
        span_days=(max(r['available'] for r in rows)-min(r['entry'] for r in rows)).total_seconds()/86400 if rows else None,
        horizon_known_n=len(paths),FP2=mean(int(p['fp2']) for p in paths) if paths else None,
        FP5=mean(int(p['fp5']) for p in paths) if paths else None,
        raw_R=mean(float(p['raw_R']) for p in paths) if paths else None,
        stop_aware_R=mean(float(p['stop_aware']) for p in paths) if paths else None)


class Evidence:
    def __init__(self,groups,bounds):
        self.groups=groups;self.bounds=bounds
        self.times={k:[r['available'] for r in v] for k,v in groups.items()}

    def at(self,strategy,instrument,t):
        key=(strategy,instrument);source=self.groups.get(key,[])
        n=bisect_right(self.times.get(key,[]),t)
        # Numeric future values are never read; take only a completed prefix.
        rows=source[max(0,n-60):n]
        short=performance(rows[-20:],t);long=performance(rows,t)
        state='INSUFFICIENT'
        if (n>=60 and self.bounds[instrument][0]<=t<=self.bounds[instrument][1]
                and t-long['last_result']<=AGE):
            if short['net_mean']>0 and long['ci95_low']>0:state='EDGE_CONFIRMED'
            elif short['net_mean']<=0 and long['ci95_high']<0:state='NO_EDGE_CONFIRMED'
            elif short['net_mean']<=0 and long['net_mean']>0:state='DETERIORATING'
            else:state='UNCONFIRMED'
        return dict(state=state,known=n,short=short,long=long)

    def alternative(self,strategy,instrument,t):
        candidates=[]
        for other in OLD if instrument in OLD else NEW:
            if other==instrument:continue
            card=self.at(strategy,other,t)
            if card['state']=='EDGE_CONFIRMED':
                candidates.append((other,card))
        return min(candidates,key=lambda q:(-q[1]['long']['ci95_low'],q[0])) if candidates else (None,None)


def known_flat(card):
    return dict(status=card['state'],known=card['known'],
        **{f'{label}_{k}':v for label,window in (('w20',card['short']),('w60',card['long'])) for k,v in window.items()})


def baseline_tracks(bounds):
    points=defaultdict(list)
    for r in read_csv(FOLDER/'REGIME_TIMELINE.csv.gz'):
        points[r['instrument'],'RAW20_CONFIRM5'].append((dt(r['as_of']),{'WARNING':BAD,'NORMAL':GOOD,'UNKNOWN':UNKNOWN}[r['RAW20_CONFIRM5']]))
    for r in read_csv(FOLDER/'REGIME_ADDITIONAL_STATE_CHANGES.csv'):
        if r['method']=='TWO_BLOCK_20':points[r['instrument'],r['method']].append((dt(r['as_of']),r['state']))
    return {(s,m):Track(points[s,m],*bounds[s]) for s in bounds for m in ('RAW20_CONFIRM5','TWO_BLOCK_20')}


def make_tracks(evidence,oldtracks):
    tracks={};decisions=[]
    for strategy in MODES:
        epoch_times={epoch:sorted({t for (m,s),rows in evidence.groups.items() if m==strategy and s in epoch
            for r in rows for t in (r['available'],r['available']+AGE+timedelta(microseconds=1))}) for epoch in (OLD,NEW)}
        for instrument,bounds in evidence.bounds.items():
            start,end=bounds
            times=sorted({start,end}|{t for t in epoch_times[OLD if instrument in OLD else NEW] if start<=t<=end})
            points={m:[] for m in METHODS}
            last=None
            for t in times:
                card=evidence.at(strategy,instrument,t);candidate,alt=evidence.alternative(strategy,instrument,t)
                state=card['state'];bad=state=='NO_EDGE_CONFIRMED'
                points['BASELINE'].append((t,GOOD))
                points['EDGE_20_60'].append((t,BAD if bad else GOOD if state=='EDGE_CONFIRMED' else UNKNOWN))
                points['EDGE_20_60_ROTATION'].append((t,BAD if bad and candidate else GOOD if state=='EDGE_CONFIRMED' else UNKNOWN))
                signature=(state,candidate if bad else None)
                if signature!=last:
                    row=dict(strategy=strategy,instrument=instrument,as_of=t,**known_flat(card),
                        decision='CONSIDER_REPLACEMENT' if bad else 'KEEP_WITH_CAUTION' if state!='EDGE_CONFIRMED' else 'KEEP',
                        alternative=candidate if bad else None,
                        alternative_status=alt['state'] if bad and alt else 'NO_CONFIRMED_ALTERNATIVE',
                        alternative_w20=alt['short']['net_mean'] if bad and alt else None,
                        alternative_w60=alt['long']['net_mean'] if bad and alt else None,
                        alternative_w60_low=alt['long']['ci95_low'] if bad and alt else None)
                    decisions.append(row);last=signature
            for method in METHODS:
                tracks[strategy,instrument,method]=(oldtracks[instrument,method] if method in ('RAW20_CONFIRM5','TWO_BLOCK_20')
                                                    else Track(points[method],start,end))
    return tracks,decisions


def weak_periods(groups):
    periods=[]
    for (strategy,instrument),rows in groups.items():
        blocks=[rows[i:i+20] for i in range(0,len(rows)-19,20)]
        i=0
        while i<len(blocks):
            weak=mean(r['net'] for r in blocks[i])<0;j=i+1
            while j<len(blocks) and (mean(r['net'] for r in blocks[j])<0)==weak:j+=1
            if j-i>=2:
                periods.append(dict(strategy=strategy,instrument=instrument,kind='WEAK' if weak else 'FAVORABLE',
                    start=min(r['entry'] for r in blocks[i]),end=max(r['available'] for r in blocks[j-1]),
                    label_available=max(r['available'] for r in blocks[i+1]),blocks=j-i))
            i=j
    return periods


def period_detections(periods,tracks):
    result=[]
    for p in periods:
        if p['kind']=='FAVORABLE' and not any(q['kind']=='WEAK' and
            (q['strategy'],q['instrument'])==(p['strategy'],p['instrument']) and q['end']<=p['start'] for q in periods):
            continue  # Initial good history is not a recovery.
        target=BAD if p['kind']=='WEAK' else GOOD
        for method in METHODS:
            track=tracks[p['strategy'],p['instrument'],method]
            found=p['start'] if track.at(p['start'])==target else next(
                (t for t,s in track.points if p['start']<=t<=p['end'] and s==target),None)
            result.append(dict(method=method,**p,detected_at=found,
                delay_days=(found-p['start']).total_seconds()/86400 if found else None,
                detected=found is not None))
    return result


def n4_states(evidence):
    rows=[]
    start=max(evidence.bounds[s][0] for s in NEW);end=min(evidence.bounds[s][1] for s in NEW)
    for strategy in MODES:
        times=sorted({start,end}|{t for (m,s),history in evidence.groups.items() if m==strategy and s in NEW
            for r in history for t in (r['available'],r['available']+AGE+timedelta(microseconds=1)) if start<t<end})
        for a,b in zip(times,times[1:]):
            states={s:evidence.at(strategy,s,a) for s in NEW}
            rows.append(dict(strategy=strategy,start=a,end=b,days=(b-a).total_seconds()/86400,
                **{s:v['state'] for s,v in states.items()},
                full60=sum(v['known']>=60 for v in states.values()),
                confirmed_edge=sum(v['state']=='EDGE_CONFIRMED' for v in states.values()),
                confirmed_no_edge=sum(v['state']=='NO_EDGE_CONFIRMED' for v in states.values())))
    return rows


def evaluate_future(rows,t,pre_mean):
    future=sorted((r for r in rows if r['entry']>t),key=lambda r:(r['available'],r['signal']))[:40]
    p20=performance(future[:20]);p40=performance(future[20:40])
    verdict='UNRESOLVED'
    if len(future)==40:
        if p20['net_mean']<0 and p40['net_mean']<0:verdict='TRUE'
        elif p20['net_mean']>=0 and p40['net_mean']>=0:verdict='FALSE'
    recovery=None
    if pre_mean is not None:
        for i in range(20,len(future)+1):
            if mean(r['net'] for r in future[i-20:i])>=pre_mean:
                recovery=future[i-1]['available'];break
    return dict(future_verdict=verdict,future20_n=p20['n'],future20_net=p20['net_mean'],
        future21_40_n=p40['n'],future21_40_net=p40['net_mean'],
        future_end=future[-1]['available'] if len(future)==40 else None,
        full_return_at=recovery,full_return_days=(recovery-t).total_seconds()/86400 if recovery else None)


def warning_episodes(tracks,evidence):
    episodes=[]
    for (strategy,instrument,method),track in tracks.items():
        for start,end,state in track.spans():
            if state!=BAD:continue
            card=evidence.at(strategy,instrument,start)
            candidate,alt=evidence.alternative(strategy,instrument,start)
            rows=evidence.groups.get((strategy,instrument),[])
            future=evaluate_future(rows,start,card['long']['net_mean'])
            recovery=next((t for t,s in track.points if t>=end and s==GOOD),None)
            episodes.append(dict(method=method,strategy=strategy,instrument=instrument,as_of=start,
                ended_at=end,duration_days=(end-start).total_seconds()/86400,
                **known_flat(card),alternative=candidate,
                alternative_w20=alt['short']['net_mean'] if alt else None,
                alternative_w60=alt['long']['net_mean'] if alt else None,
                next_favorable_at=recovery,**future))
    return episodes


def rotation_evaluation(decisions,evidence):
    result=[]
    for d in decisions:
        if d['status']!='NO_EDGE_CONFIRMED':continue
        row=dict(d);t=d['as_of'];key=(d['strategy'],d['instrument'])
        rows=evidence.groups.get(key,[])
        future=evaluate_future(rows,t,d['w60_net_mean']);row.update(future)
        old=[r for r in rows if r['entry']>t and future['future_end'] and r['available']<=future['future_end']]
        alt=[r for r in evidence.groups.get((d['strategy'],d['alternative']),[]) if r['entry']>t and future['future_end'] and r['available']<=future['future_end']]
        a,b=performance(old),performance(alt)
        row.update(old_future_n=a['n'],old_future_net=a['net_mean'],alternative_future_n=b['n'],alternative_future_net=b['net_mean'],
            lost_positive=a['positive'],avoided_negative=a['negative'],
            replacement_verdict='NO_CANDIDATE' if not d['alternative'] else
                'UNRESOLVED' if not future['future_end'] or len(alt)<20 else
                'USEFUL' if b['net_mean']>0 and b['net_mean']>a['net_mean'] else 'WRONG',
            original_edge_returns=next((v['as_of'] for v in decisions if v['strategy']==d['strategy'] and v['instrument']==d['instrument'] and v['as_of']>t and v['status']=='EDGE_CONFIRMED'),None))
        result.append(row)
    return result


def path_quality(raw):
    seen=[r['outcome'] for r in raw if r['outcome'] is not None]
    return dict(raw_signals=len(raw),raw_observed=len(seen),raw_censored=len(raw)-len(seen),
        raw_R=mean(float(r['raw_R']) for r in seen) if seen else None,
        stop_aware_R=mean(float(r['stop_aware']) for r in seen) if seen else None,
        FP2=mean(int(r['fp2']) for r in seen) if seen else None,
        FP5=mean(int(r['fp5']) for r in seen) if seen else None)


def integrate_weak(track,periods,start,end):
    # Periods for one strategy/instrument are disjoint.
    all_days=kept=0.
    for p in periods:
        if p['kind']!='WEAK':continue
        a,b=max(start,p['start']),min(end,p['end'])
        if b<=a:continue
        days=(b-a).total_seconds()/86400;all_days+=days
        kept+=days-seconds_between(track,a,b)[0][BAD]/86400
    return all_days,kept


def compare_scopes(evidence,tracks,episodes,periods,raw,replays):
    result=[]
    # Integrate each track/month once, then reuse for the requested scopes.
    time_rows=[]
    for (m,s,met),track in tracks.items():
        for a,b,_ in months_until(track.end):
            lo,hi=max(a,track.start),min(b,track.end)
            if hi<=lo:continue
            days=(hi-lo).total_seconds()/86400
            w,k=integrate_weak(track,[p for p in periods if p['strategy']==m and p['instrument']==s],lo,hi)
            time_rows.append((m,s,met,lo,days,days-seconds_between(track,lo,hi)[0][UNKNOWN]/86400,w,k))
    scopes=[('ALL',lambda m,s,t:True),('2018-2022',lambda m,s,t:s in OLD),('2023-2026',lambda m,s,t:s in NEW)]
    scopes += [(s,lambda m,i,t,s=s:i==s) for s in (*OLD,*NEW)]
    scopes += [(m,lambda a,s,t,m=m:a==m) for m in MODES]
    scopes += [(m+'/'+s,lambda a,i,t,m=m,s=s:a==m and i==s) for m in MODES for s in (*OLD,*NEW)]
    scopes += [(str(y),lambda m,s,t,y=y:t.year==y) for y in range(2018,2027)]
    for scope,select in scopes:
        for method in METHODS:
            baseline=[r for (m,s),rows in evidence.groups.items() for r in rows if select(m,s,r['entry'])]
            replay=[r for r in replays[method] if select(r['strategy'],r['instrument'],r['entry'])]
            removed=[r for r in baseline if tracks[r['strategy'],r['instrument'],method].at(r['entry'])==BAD]
            replay_keys={(r['strategy'],r['instrument'],r['entry']) for r in replay}
            absent=[r for r in baseline if (r['strategy'],r['instrument'],r['entry']) not in replay_keys]
            pp=[p for p in periods if p['kind']=='WEAK' and select(p['strategy'],p['instrument'],p['start'])]
            alerts=[r for r in episodes if r['method']==method and select(r['strategy'],r['instrument'],r['as_of'])]
            delays=[];misses=0;weak_days=kept_days=coverage=available=0.
            for p in pp:
                track=tracks[p['strategy'],p['instrument'],method]
                found=p['start'] if track.at(p['start'])==BAD else next((t for t,s in track.points if p['start']<=t<=p['end'] and s==BAD),None)
                if found is None:misses+=1
                else:delays.append((found-p['start']).total_seconds()/86400)
            for m,s,met,t,total,c,w,k in time_rows:
                if met==method and select(m,s,t):
                    available+=total;coverage+=c;weak_days+=w;kept_days+=k
            result.append(dict(scope=scope,method=method,alerts=len(alerts),
                false_recommendations=sum(r['future_verdict']=='FALSE' for r in alerts),
                true_recommendations=sum(r['future_verdict']=='TRUE' for r in alerts),
                unresolved_recommendations=sum(r['future_verdict']=='UNRESOLVED' for r in alerts),
                sustained_weak_periods=len(pp),missed_sustained=len(pp)-len(delays),
                delay_median_days=median(delays) if delays else None,
                delay_max_days=max(delays) if delays else None,
                weak_strategy_instrument_days=weak_days,remaining_weak_days=kept_days,
                justified_status_time_share=coverage/available if available and method!='BASELINE' else None,
                baseline_positive_excluded=sum(r['net']>0 for r in removed),
                baseline_negative_excluded=sum(r['net']<0 for r in removed),
                baseline_excluded=len(removed),baseline_n=len(baseline),
                replay_baseline_positive_lost=sum(r['net']>0 for r in absent),
                replay_baseline_negative_avoided=sum(r['net']<0 for r in absent),
                replay_baseline_absent=len(absent),
                replay_new_entries=len({(r['strategy'],r['instrument'],r['entry']) for r in replay}-
                                       {(r['strategy'],r['instrument'],r['entry']) for r in baseline}),
                excluded_positive_share=sum(r['net']>0 for r in removed)/sum(r['net']>0 for r in baseline) if any(r['net']>0 for r in baseline) else None,
                replay_lost_positive_share=sum(r['net']>0 for r in absent)/sum(r['net']>0 for r in baseline) if any(r['net']>0 for r in baseline) else None,
                **{'replay_'+k:v for k,v in performance(replay).items()}))
    return result


def monthly_rows(evidence,tracks,decisions,episodes,rotations,periods,raw,replays):
    result=[];end=max(b for a,b in evidence.bounds.values())
    for a,b,_ in months_until(end):
        month=a.strftime('%Y-%m')
        for strategy in MODES:
            for instrument,(source_start,source_end) in evidence.bounds.items():
                lo,hi=max(a,source_start),min(b,source_end)
                active=hi>lo
                c0=evidence.at(strategy,instrument,a);c1=evidence.at(strategy,instrument,min(b,source_end))
                baseline=[r for r in evidence.groups.get((strategy,instrument),[]) if a<=r['entry']<b]
                rr=[r for r in raw if r['strategy']==strategy and r['instrument']==instrument and a<=r['decision']<b]
                ds=[r for r in decisions if r['strategy']==strategy and r['instrument']==instrument and a<=r['as_of']<b and r['status']=='NO_EDGE_CONFIRMED']
                rs=[r for r in rotations if r['strategy']==strategy and r['instrument']==instrument and a<=r['as_of']<b]
                for method in METHODS:
                    track=tracks[strategy,instrument,method]
                    allowed=[r for r in rr if track.at(r['decision'])!=BAD]
                    p=[r for r in replays[method] if r['strategy']==strategy and r['instrument']==instrument and a<=r['entry']<b]
                    w,k=integrate_weak(track,[p for p in periods if p['strategy']==strategy and p['instrument']==instrument],lo,hi) if active else (0,0)
                    ep=[r for r in episodes if r['method']==method and r['strategy']==strategy and r['instrument']==instrument and a<=r['as_of']<b]
                    result.append(dict(month=month,strategy=strategy,instrument=instrument,method=method,
                        status_start=track.at(a),status_end=track.at(min(b,source_end)) if active else UNKNOWN,
                        edge_status_start=c0['state'],edge_status_end=c1['state'] if active else 'INSUFFICIENT',
                        start_w20= c0['short']['net_mean'],start_w60=c0['long']['net_mean'],start_known=c0['known'],
                        end_w20=c1['short']['net_mean'],end_w60=c1['long']['net_mean'],end_known=c1['known'],
                        last_result_start=c0['long']['last_result'],last_result_end=c1['long']['last_result'],
                        end_w60_span_days=c1['long']['span_days'],
                        available_days=(hi-lo).total_seconds()/86400 if active else 0,
                        **path_quality(rr),allowed_raw=len(allowed),excluded_raw=len(rr)-len(allowed),
                        **{'allowed_'+key:value for key,value in path_quality(allowed).items()},
                        **{'baseline_'+key:value for key,value in performance(baseline).items()},
                        **{'replay_'+key:value for key,value in performance(p).items()},
                        alerts=len(ep),false_alerts=sum(r['future_verdict']=='FALSE' for r in ep),
                        replacement_recommendations=len(ds),confirmed_alternatives=sum(bool(r['alternative']) for r in ds),
                        useful_replacements=sum(r['replacement_verdict']=='USEFUL' for r in rs),
                        wrong_replacements=sum(r['replacement_verdict']=='WRONG' for r in rs),
                        weak_days=w,remaining_weak_days=k,
                        unknown_days=seconds_between(track,lo,hi)[0][UNKNOWN]/86400 if active else 0))
    return result


def build(output,archive,market,work):
    from .suitability_replay import run_replays
    output.mkdir(parents=True,exist_ok=True);work.mkdir(parents=True,exist_ok=True)
    groups,bounds,raw,hashes=load_sources();evidence=Evidence(groups,bounds)
    tracks,decisions=make_tracks(evidence,baseline_tracks(bounds))
    print('20/60 states',len(decisions),Counter(r['status'] for r in decisions),flush=True)
    episodes=warning_episodes(tracks,evidence);rotations=rotation_evaluation(decisions,evidence)
    periods=weak_periods(groups)
    detections=period_detections(periods,tracks)
    replays,receipt=run_replays(archive,market,work,tracks,evidence)
    # Diagnostic joins for conditional entries, with independent horizon timing.
    path_map={(r['instrument'],r['signal']):r['outcome'] for r in raw}
    signal_map={(r['strategy'],r['instrument'],r['signal']):r for r in raw}
    for rows in replays.values():
        for r in rows:
            r['path']=path_map.get((r['instrument'],r['signal']))
            signal=signal_map[r['strategy'],r['instrument'],r['signal']]
            for name in ('risk','initial_stop','entry_price','side'):r[name]=signal[name]
    comparison=compare_scopes(evidence,tracks,episodes,periods,raw,replays)
    monthly=monthly_rows(evidence,tracks,decisions,episodes,rotations,periods,raw,replays)
    snapshots=[]
    for strategy in MODES:
        for instrument,(a,b) in bounds.items():
            card=evidence.at(strategy,instrument,b);alternative,alt=evidence.alternative(strategy,instrument,b)
            snapshots.append(dict(strategy=strategy,instrument=instrument,as_of=b,**known_flat(card),
                alternative=alternative if card['state']=='NO_EDGE_CONFIRMED' else None,
                decision='CONSIDER_REPLACEMENT' if card['state']=='NO_EDGE_CONFIRMED' else 'KEEP_WITH_LIMITATIONS',
                reliability='NOT_VALIDATED',readonly=True,live_feed=False))
    dump_csv(output/'V20_SUITABILITY_MONTHLY.csv',monthly)
    signal_decisions=[]
    for r in raw:
        t=r['decision'];card=evidence.at(r['strategy'],r['instrument'],t)
        alternative,alt=evidence.alternative(r['strategy'],r['instrument'],t)
        signal_decisions.append(dict(row_type='SIGNAL_DECISION',strategy=r['strategy'],instrument=r['instrument'],
            as_of=t,signal=r['signal'],**known_flat(card),
            alternative=alternative if card['state']=='NO_EDGE_CONFIRMED' else None,
            **{m+'_allowed':tracks[r['strategy'],r['instrument'],m].at(t)!=BAD for m in METHODS},
            own_horizon_available=r['outcome']['available'] if r['outcome'] else None,
            own_horizon_status=r['horizon_status']))
    dump_csv(output/'V20_SUITABILITY_DECISIONS.csv',
             [dict(row_type='STATE_CHANGE',**r) for r in decisions]+signal_decisions)
    dump_csv(output/'V20_ROTATION_COMPARISON.csv',rotations)
    dump_csv(output/'V20_SUITABILITY_METHODS.csv',comparison)
    dump_csv(output/'V20_SUITABILITY_ALERTS.csv',episodes)
    dump_csv(output/'V20_SUITABILITY_PERIODS.csv',periods)
    dump_csv(output/'V20_SUITABILITY_DETECTIONS.csv',detections)
    dump_csv(output/'V20_SUITABILITY_N4_STATES.csv',n4_states(evidence))
    dump_csv(output/'V20_SUITABILITY_SNAPSHOTS.csv',snapshots)
    annual=[];coverage=[]
    for strategy in MODES:
        for instrument,(start,end) in bounds.items():
            history=groups.get((strategy,instrument),[])
            coverage.append(dict(strategy=strategy,instrument=instrument,quote_start=start,quote_end=end,
                completed_trades=len(history),first20_available=history[19]['available'] if len(history)>=20 else None,
                first60_available=history[59]['available'] if len(history)>=60 else None,
                first_confirmed_edge=next((d['as_of'] for d in decisions if d['strategy']==strategy and d['instrument']==instrument and d['status']=='EDGE_CONFIRMED'),None),
                first_confirmed_no_edge=next((d['as_of'] for d in decisions if d['strategy']==strategy and d['instrument']==instrument and d['status']=='NO_EDGE_CONFIRMED'),None)))
            for year in range(2018,2027):
                for method in METHODS:
                    history_year=[r for r in replays[method] if r['strategy']==strategy and r['instrument']==instrument and r['entry'].year==year]
                    annual.append(dict(strategy=strategy,instrument=instrument,year=year,method=method,**performance(history_year)))
    dump_csv(output/'V20_SUITABILITY_SAMPLE_COVERAGE.csv',coverage)
    dump_csv(output/'V20_SUITABILITY_ANNUAL.csv',annual)
    all_trades=[dict(method=m,**{k:v for k,v in r.items() if k!='path'}) for m,rows in replays.items() for r in rows]
    dump_csv(output/'V20_SUITABILITY_REPLAY_TRADES.csv.gz',all_trades,compressed=True)
    hashes.update(receipt.pop('source_hashes'))
    hashes['V20-04/V20_SUITABILITY_PROTOCOL_RU.md']=digest(FOLDER/'V20_SUITABILITY_PROTOCOL_RU.md')
    summary=dict(schema='v20.suitability.rotation.research.v1',input_head=INPUT_HEAD,
        source_hashes=hashes,bounds=bounds,baseline_trades=2593,old_trades=1004,late_trades=1589,
        published_raw=4986,observed_raw=4431,unique_observed_events=3990,
        comparison=comparison,rotation_outcomes=dict(Counter(r['replacement_verdict'] for r in rotations)),
        replay=receipt,snapshots=snapshots,sample_coverage=coverage,verdict='FAIL',
        card_action='KEEP_EXISTING_NO_VALIDATED_REPLACEMENT',
        limitations=['Late original 1589 ledger absent; existing exact-rule reproduction only.',
            'Normal CI is descriptive, repeated looks/serial dependence are not controlled.',
            'Shadow baseline continues independently of conditional admission.',
            'Counterfactual replay is a frozen C1 model, not real FINAM PnL.',
            'No untouched OOS; calendar/source gaps and old contract identity remain conditional.'])
    (output/'V20_SUITABILITY_COMPARISON.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,default=str)+'\n')
    print('artifacts',len(monthly),'monthly',len(episodes),'episodes',len(rotations),'replacement states',flush=True)
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--archive',type=Path,required=True)
    parser.add_argument('--market-data',type=Path,default=Path('/workspace/market-pattern-data/forever'))
    parser.add_argument('--work',type=Path,required=True);parser.add_argument('--output',type=Path,default=FOLDER)
    args=parser.parse_args();build(args.output,args.archive,args.market_data,args.work)
