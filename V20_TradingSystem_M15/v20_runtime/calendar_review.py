"""Fixed quarterly/half-year review, causal C1 decisions, existing frozen replay.

No indicator search or trading hook. See V20_CALENDAR_REVIEW_PROTOCOL_RU.md.
Completion windows, entry-cohort costs and raw signal cohorts are kept separate.
"""
from __future__ import annotations
import argparse
from bisect import bisect_left
from collections import Counter,defaultdict
from datetime import datetime,timedelta
import json
from pathlib import Path
from statistics import mean,median

from .suitability_research import load_sources,MODES,OLD,NEW
from .suitability_replay import run_replays
from .regime_monthly_comparison import ROOT,FOLDER,dt,digest,read_csv,Track,GOOD,BAD,UNKNOWN,months_until,seconds_between
from .regime_research import dump_csv

METHODS=('BASELINE','QUARTER_3M','HALF_YEAR_6M','QUARTER_3M_6M')
MIN3,MIN6=10,20
INPUT_HEAD='669bad64e8633bdbbcee3b500330b7a2b6c7fdc5'


def shift_month(t,n):
    y,m=divmod(t.year*12+t.month-1+n,12)
    return datetime(y,m+1,1)


def quarter(t):
    return datetime(t.year,3*((t.month-1)//3)+1,1)


def completion_period(t):
    """Right-closed (start,end] calendar windows: midnight belongs to prior month."""
    return t-timedelta(microseconds=1)


def history_start(instrument,bounds):
    if instrument in ('Si','MIX'):return datetime(2018,1,1)
    if instrument in ('USDRUBF','CNYRUBF'):return datetime(2023,1,1)
    t=bounds[instrument][0];floor=datetime(t.year,t.month,1)
    return floor if t==floor else shift_month(floor,1)


def statistics(rows):
    # C1-only aggregation: do not even parse an unused raw path whose horizon
    # may not yet be complete when an intrabar trade has already stopped out.
    values=[r['net'] for r in rows];wins=[v for v in values if v>0];losses=[v for v in values if v<0]
    closes=defaultdict(float)
    for r in rows:closes[r['available']]+=r['net']
    equity=peak=dd=0.
    for t,value in sorted(closes.items()):
        equity+=value;peak=max(peak,equity);dd=max(dd,peak-equity)
    single=len({r['strategy'] for r in rows})<=1
    return dict(n=len(values),net_R=sum(values),mean_R=mean(values) if values else None,
        PF_C1=sum(wins)/-sum(losses) if losses else None,
        wins=len(wins),losses=len(losses),positive_R=sum(max(0,r['net']) for r in rows),
        negative_R=-sum(min(0,r['net']) for r in rows),
        DD_closed_R=dd if rows and single else None,
        DD_status='SINGLE_ACCOUNT_CLOSED_R' if single else 'NOT_PORTFOLIO_MULTIPLE_ACCOUNTS',
        first_result=min((r['available'] for r in rows),default=None),
        last_result=max((r['available'] for r in rows),default=None),
        observed_span_days=(max(r['available'] for r in rows)-min(r['available'] for r in rows)).total_seconds()/86400 if rows else None)


def completed_window(rows,t,months,start):
    lo=shift_month(t,-months)
    known=[r for r in rows if lo<r['available']<=t]
    return dict(**statistics(known),full_history=lo>=start,
        sufficient=lo>=start and len(known)>=(MIN3 if months==3 else MIN6),
        window_start=lo,window_end=t)


def rule(method,w3,w6,excluded=False):
    if method=='QUARTER_3M' or method=='HALF_YEAR_6M':
        w=w3 if method=='QUARTER_3M' else w6
        if not w['sufficient']:return 'INSUFFICIENT',False
        return ('EXCLUDE',True) if w['net_R']<0 else ('GOOD' if w['net_R']>0 else 'NEUTRAL',False)
    if excluded:
        if w3['sufficient'] and w3['net_R']>0:return 'RECOVERED',False
        if not (w3['sufficient'] and w6['sufficient']):return 'INSUFFICIENT',True
        return 'EXCLUDE_PENDING_RECOVERY',True
    if not (w3['sufficient'] and w6['sufficient']):return 'INSUFFICIENT',False
    if w3['net_R']<0 and w6['net_R']<0:return 'EXCLUDE',True
    if w3['net_R']<0:return 'WARNING',False
    return ('GOOD' if w3['net_R']>0 else 'NEUTRAL'),False


def session_opens(bounds,market):
    """Activation metadata: first OBSERVED session bar, never future OHLC values."""
    import pandas as pd
    plan={(r['family'],r['day']):r['chosen_contract'] for r in read_csv(ROOT/'V20-03/results/ROLL_DECISIONS.csv')}
    clocks=defaultdict(list)
    for r in read_csv(ROOT/'V20-03/results/SESSION_AUDIT.csv'):
        if plan.get((r['family'],r['day']))==r['contract']:
            clocks[r['family']].append(dt(r['first_bar']))
    for symbol in NEW:
        d=pd.read_csv(market/symbol/(symbol+'_M15.csv'),sep=';',usecols=['Datetime'])
        ts=pd.to_datetime(d.Datetime)
        clocks[symbol]=list(ts.groupby(ts.dt.normalize()).min().array.to_pydatetime())
    return {s:sorted(set(t for t in clocks[s] if bounds[s][0]<=t<=bounds[s][1])) for s in bounds}


def effective_at(clocks,instrument,t):
    values=clocks[instrument];i=bisect_left(values,t)
    return values[i] if i<len(values) else None


def decisions_and_tracks(groups,bounds,clocks):
    reviews=[];tracks={};end=max(b for a,b in bounds.values())
    dates=[];t=datetime(2018,1,1)
    while t<=end:dates.append(t);t=shift_month(t,3)
    for strategy in MODES:
        for instrument,(start,stop) in bounds.items():
            rows=groups.get((strategy,instrument),[])
            for method in METHODS:
                if method=='BASELINE':
                    tracks[strategy,instrument,method]=Track([(start,GOOD)],start,stop);continue
                points=[(start,UNKNOWN)];excluded=False
                for t in dates:
                    if method=='HALF_YEAR_6M' and t.month not in (1,7):continue
                    h=history_start(instrument,bounds)
                    w3,w6=(completed_window(rows,t,m,h) for m in (3,6))
                    active=(start<=t<=stop)
                    effect=effective_at(clocks,instrument,t) if active else None
                    assessment,bad=rule(method,w3,w6,excluded) if active else ('NOT_AVAILABLE',False)
                    record=dict(method=method,strategy=strategy,instrument=instrument,decision_at=t,effective_at=effect,
                        assessment=assessment,action='EXCLUDE' if bad else 'ALLOW',
                        carried_exclusion=excluded and bad,
                        newly_excluded=not excluded and bad,available_instrument=active,
                        **{'w3_'+k:v for k,v in w3.items()},**{'w6_'+k:v for k,v in w6.items()})
                    reviews.append(record)
                    if effect is not None:
                        points.append((effect,BAD if bad else UNKNOWN if assessment=='INSUFFICIENT' else GOOD))
                    excluded=bad
                tracks[strategy,instrument,method]=Track(points,start,stop)
    return reviews,tracks


def uncertain_sources():
    # Censored outcomes are metadata, never numerical input to a decision.
    old=[dict(strategy=r['account'],instrument=r['family'],entry=dt(r['entry_dt']),
        available=dt(r['exit_dt'])+timedelta(minutes=15 if int(r['exit_reason']) in (1,4) else 0))
        for r in read_csv(ROOT/'V20-03/results/CENSORED_CLOSED.csv')]
    acceptance=json.loads((ROOT/'V20-02_AUDIT/ACCEPTANCE_V20_02.json').read_text())
    modern=[dict(strategy=mode,instrument=r['symbol'],entry=dt(r['entry_dt']),available=None)
            for mode in MODES for r in acceptance['meta'][mode]['terminal_positions']]
    return old+modern


def forward_result(rows,t,months,bounds,censored,minimum):
    end=shift_month(t,months)
    sample=[r for r in rows if t<r['available']<=end]
    unknown=[r for r in censored if (r['available'] is not None and t<r['available']<=end) or
             (r['available'] is None and t<=r['entry']<end)]
    complete=end<=bounds[1]
    verdict=('UNRESOLVED' if not complete or len(sample)<minimum or unknown else
             'FALSE' if sum(r['net'] for r in sample)>0 else
             'USEFUL' if sum(r['net'] for r in sample)<0 else 'UNRESOLVED')
    return dict(**statistics(sample),complete=complete,censored=len(unknown),
        verdict=verdict,pending_at_decision=sum(r['entry']<t for r in sample),end=end)


def evaluate_reviews(reviews,groups,bounds,censored):
    for r in reviews:
        key=(r['strategy'],r['instrument']);rows=groups.get(key,[])
        unknown=[v for v in censored if (v['strategy'],v['instrument'])==key]
        t=r['decision_at']
        for label,start,m,n in (('next_q',t,3,10),('second_q',shift_month(t,3),3,10),('next_h',t,6,20)):
            r.update({label+'_'+k:v for k,v in forward_result(rows,start,m,bounds[r['instrument']],unknown,n).items()})
        lo,hi=r['w3_window_start'],r['w6_window_start']
        for label,start in (('w3',lo),('w6',hi)):
            r[label+'_censored']=sum(v['available'] is not None and start<v['available']<=t for v in unknown)


def exclusion_episodes(reviews,tracks,groups):
    episodes=[]
    for key,track in tracks.items():
        strategy,instrument,method=key
        if method=='BASELINE':continue
        local=[r for r in reviews if (r['strategy'],r['instrument'],r['method'])==key]
        for a,b,state in track.spans():
            if state!=BAD:continue
            first=next(r for r in local if r['effective_at']==a and r['action']=='EXCLUDE')
            subsequent=[r for r in local if r['effective_at'] is not None and r['effective_at']>=b]
            release=subsequent[0] if subsequent and b<track.end else None
            confirmed=next((r for r in local if r['decision_at']>first['decision_at'] and r['assessment'] in ('GOOD','RECOVERED')),None)
            lost=[r for r in groups.get((strategy,instrument),[]) if a<=r['entry']<b]
            cost=statistics(lost)
            episodes.append(dict(**first,episode_start=a,episode_end=b,
                duration_days=(b-a).total_seconds()/86400,
                returned_at=b if release else None,release_reason=release['assessment'] if release else 'END_OF_ARCHIVE',
                first_positive_review=confirmed['decision_at'] if confirmed else None,
                confirmed_return=bool(release and release['assessment'] in ('GOOD','RECOVERED')),
                lost_positive_trades=cost['wins'],avoided_negative_trades=cost['losses'],
                lost_positive_R=cost['positive_R'],avoided_negative_R=cost['negative_R'],
                baseline_net_during_exclusion=cost['net_R'],
                hypothetical_1pct_risk_lost_pp=cost['positive_R'],
                false_cost_positive_R=cost['positive_R'] if first['next_q_verdict']=='FALSE' else 0))
    for r in reviews:
        if r['action']=='EXCLUDE' and r['effective_at'] is not None:
            episode=next(e for e in episodes if (e['strategy'],e['instrument'],e['method'])==(r['strategy'],r['instrument'],r['method']) and e['episode_start']<=r['effective_at']<e['episode_end'])
            r['episode_start']=episode['episode_start'];r['episode_returned_at']=episode['returned_at']
            r['episode_first_positive_review']=episode['first_positive_review']
            until_return=[q for q in groups.get((r['strategy'],r['instrument']),[])
                if r['effective_at']<=q['entry']<episode['episode_end']]
            r.update(until_return_observed_end=episode['episode_end'],
                until_return_days=(episode['episode_end']-r['effective_at']).total_seconds()/86400,
                cost_censored_by_archive=episode['returned_at'] is None,
                lost_positive_R_until_return_or_archive=sum(max(0,q['net']) for q in until_return),
                avoided_negative_R_until_return_or_archive=-sum(min(0,q['net']) for q in until_return),
                lost_wins_until_return_or_archive=sum(q['net']>0 for q in until_return))
            following=[q['effective_at'] for q in reviews if (q['strategy'],q['instrument'],q['method'])==(r['strategy'],r['instrument'],r['method'])
                       and q['effective_at'] is not None and q['effective_at']>r['effective_at']]
            end=min(following) if following else episode['episode_end']
            end=min(end,episode['episode_end'])
            lost=[q for q in groups.get((r['strategy'],r['instrument']),[]) if r['effective_at']<=q['entry']<end]
            p=statistics(lost)
            r.update(review_interval_end=end,review_interval_days=(end-r['effective_at']).total_seconds()/86400,
                lost_positive_R=p['positive_R'],avoided_negative_R=p['negative_R'],
                lost_positive_trades=p['wins'],avoided_negative_trades=p['losses'],
                baseline_net_excluded=p['net_R'],hypothetical_1pct_risk_lost_pp=p['positive_R'])
    return episodes


def quarterly_truth(groups,bounds,censored):
    periods=[];quarters=[]
    for (strategy,instrument),rows in groups.items():
        t=datetime(2018,1,1);end=bounds[instrument][1]
        while t<end:
            value=forward_result(rows,t,3,bounds[instrument],
                [r for r in censored if (r['strategy'],r['instrument'])==(strategy,instrument)],10)
            eligible=t>=history_start(instrument,bounds) and value['complete'] and value['n']>=10 and not value['censored']
            quarters.append(dict(strategy=strategy,instrument=instrument,start=t,
                eligible=eligible,weak=eligible and value['net_R']<0,**value))
            t=shift_month(t,3)
        local=[r for r in quarters if (r['strategy'],r['instrument'])==(strategy,instrument)]
        i=0
        while i<len(local):
            if not local[i]['weak']:i+=1;continue
            j=i+1
            while j<len(local) and local[j]['weak']:j+=1
            if j-i>=2:periods.append(dict(strategy=strategy,instrument=instrument,start=local[i]['start'],
                end=local[j-1]['end'],quarters=j-i))
            i=j
    return quarters,periods


def detect_periods(periods,tracks,groups,clocks):
    result=[]
    for p in periods:
        for method in METHODS:
            track=tracks[p['strategy'],p['instrument'],method]
            actionable=effective_at(clocks,p['instrument'],p['start']) or p['end']
            found=p['start'] if track.at(actionable)==BAD else next((t for t,s in track.points if actionable<=t<p['end'] and s==BAD),None)
            stop=found or p['end']
            before=[r for r in groups.get((p['strategy'],p['instrument']),[]) if p['start']<r['available']<=stop]
            losses=[r for r in before if r['net']<0]
            result.append(dict(method=method,**p,detected_at=found,missed=found is None,
                delay_days=(found-p['start']).total_seconds()/86400 if found else None,
                negative_R_before_detection=-sum(r['net'] for r in losses),
                net_R_before_detection=sum(r['net'] for r in before)))
    return result


def overview(reviews,bounds):
    rows=[]
    for t in sorted({r['decision_at'] for r in reviews}):
        summaries=[]
        for strategy in MODES:
            local=[r for r in reviews if r['decision_at']==t and r['strategy']==strategy and r['method']=='QUARTER_3M' and r['available_instrument']]
            n=len(local)
            counts={f'{w}_{kind}':sum(r[w+'_sufficient'] and (r[w+'_net_R']<0 if kind=='negative' else r[w+'_net_R']>0) for r in local) for w in ('w3','w6') for kind in ('negative','positive')}
            counts.update({w+'_sufficient':sum(r[w+'_sufficient'] for r in local) for w in ('w3','w6')})
            state=('ALL_AVAILABLE_NEGATIVE' if n and counts['w3_negative']==n else
                'MAJORITY_AVAILABLE_NEGATIVE' if counts['w3_negative']>n/2 else
                'LOCAL_WEAKNESS' if n>1 and counts['w3_negative']==1 and counts['w3_positive']==n-1 else 'MIXED_OR_INSUFFICIENT')
            summaries.append(dict(as_of=t,strategy=strategy,available=n,classification=state,**counts))
        simultaneous=all(r['available'] and r['w3_negative']>r['available']/2 for r in summaries)
        for r in summaries:r['simultaneous_majority_all_3_robots']=simultaneous
        rows.extend(summaries)
    return rows


def scopes():
    return ['ALL','2018','2019-2022','2023-2026',*[str(y) for y in range(2019,2027)],
        *MODES,*OLD,*NEW,*[m+'/'+s for m in MODES for s in (*OLD,*NEW)]]


def matches(scope,strategy,instrument,t):
    if scope=='ALL':return True
    if scope in ('2019-2022','2023-2026'):
        return (2019<=t.year<=2022) if scope=='2019-2022' else (2023<=t.year<=2026)
    if scope.isdigit():return t.year==int(scope)
    if '/' in scope:return scope==strategy+'/'+instrument
    return scope in (strategy,instrument)


def compare(groups,replays,tracks,reviews,episodes,quarters,detections,bounds,clocks):
    rows=[];baseline=[r for v in groups.values() for r in v]
    assessment_tracks={}
    for key,track in tracks.items():
        strategy,instrument,method=key
        points=[(track.start,GOOD if method=='BASELINE' else UNKNOWN)]
        points.extend((r['effective_at'],UNKNOWN if r['assessment']=='INSUFFICIENT' else GOOD)
            for r in reviews if (r['strategy'],r['instrument'],r['method'])==key and r['effective_at'] is not None)
        assessment_tracks[key]=Track(points,track.start,track.end)
    for scope in scopes():
        choose=lambda r:matches(scope,r['strategy'],r['instrument'],completion_period(r['available']))
        for method in METHODS:
            replay=[r for r in replays[method] if choose(r)]
            direct=[r for r in baseline if choose(r) and tracks[r['strategy'],r['instrument'],method].at(r['entry'])!=BAD]
            base=[r for r in baseline if choose(r)];keys={(r['strategy'],r['instrument'],r['entry']) for r in replay}
            absent=[r for r in base if (r['strategy'],r['instrument'],r['entry']) not in keys]
            keys_base={(r['strategy'],r['instrument'],r['entry']) for r in base}
            rr=[r for r in reviews if r['method']==method and r['action']=='EXCLUDE' and matches(scope,r['strategy'],r['instrument'],r['decision_at'])]
            ep=[r for r in episodes if r['method']==method and matches(scope,r['strategy'],r['instrument'],r['decision_at'])]
            dd=[r for r in detections if r['method']==method and matches(scope,r['strategy'],r['instrument'],r['start'])]
            weak=[r for r in quarters if r['weak'] and matches(scope,r['strategy'],r['instrument'],r['start'])]
            missed_q=sum(not any(s==BAD and a<q['end'] and b>(effective_at(clocks,q['instrument'],q['start']) or q['end'])
                for a,b,s in tracks[q['strategy'],q['instrument'],method].spans()) for q in weak)
            total=unknown=bad_days=0.
            for (strategy,instrument,m),track in tracks.items():
                if m!=method:continue
                for a,b,_ in months_until(track.end):
                    lo,hi=max(a,track.start),min(b,track.end)
                    if hi<=lo or not matches(scope,strategy,instrument,a):continue
                    seconds,available=seconds_between(track,lo,hi);total+=available
                    unknown+=seconds_between(assessment_tracks[strategy,instrument,m],lo,hi)[0][UNKNOWN]
                    bad_days+=seconds[BAD]/86400
            result=dict(scope=scope,method=method,recommendations=len(rr),episodes=len(ep),
                useful=sum(r['next_q_verdict']=='USEFUL' for r in rr),false=sum(r['next_q_verdict']=='FALSE' for r in rr),
                unresolved=sum(r['next_q_verdict']=='UNRESOLVED' for r in rr),
                false_episodes=sum(r['next_q_verdict']=='FALSE' for r in ep),
                false_interval_lost_positive_R=sum(r['lost_positive_R'] for r in rr if r['next_q_verdict']=='FALSE'),
                false_interval_avoided_negative_R=sum(r['avoided_negative_R'] for r in rr if r['next_q_verdict']=='FALSE'),
                false_interval_lost_wins=sum(r['lost_positive_trades'] for r in rr if r['next_q_verdict']=='FALSE'),
                largest_missed_profitable_quarter_R=max((r['next_q_net_R'] for r in rr if r['next_q_verdict']=='FALSE'),default=None),
                sustained_periods=len(dd),missed_sustained=sum(r['missed'] for r in dd),
                weak_quarters=len(weak),missed_weak_quarters=missed_q,
                delay_median_days=median([r['delay_days'] for r in dd if not r['missed']]) if any(not r['missed'] for r in dd) else None,
                exclusion_days=bad_days,unknown_time_share=unknown/total if total else None,
                duration_mean_days=mean(r['duration_days'] for r in ep) if ep else None,
                confirmed_returns=sum(r['confirmed_return'] for r in ep),
                actual_lost_positive_R=sum(max(0,r['net']) for r in absent),actual_avoided_negative_R=-sum(min(0,r['net']) for r in absent),
                actual_lost_wins=sum(r['net']>0 for r in absent),actual_avoided_losses=sum(r['net']<0 for r in absent),
                replay_new_entries=sum((r['strategy'],r['instrument'],r['entry']) not in keys_base for r in replay),
                **{'replay_'+k:v for k,v in statistics(replay).items()},
                **{'direct_'+k:v for k,v in statistics(direct).items()})
            bymonth=defaultdict(float)
            for r in replay:bymonth[completion_period(r['available']).strftime('%Y-%m')]+=r['net']
            result.update(replay_positive_months=sum(v>0 for v in bymonth.values()),replay_negative_months=sum(v<0 for v in bymonth.values()))
            base_months=defaultdict(list);after_months=defaultdict(list)
            for r in base:base_months[r['strategy'],r['instrument'],completion_period(r['available']).strftime('%Y-%m')].append(r)
            for r in replay:after_months[r['strategy'],r['instrument'],completion_period(r['available']).strftime('%Y-%m')].append(r)
            result.update(profitable_result_months_silenced=sum(sum(r['net'] for r in vv)>0 and not after_months[k] for k,vv in base_months.items()),
                negative_result_months_made_nonnegative=sum(sum(r['net'] for r in vv)<0 and sum(r['net'] for r in after_months[k])>=0 for k,vv in base_months.items()),
                positive_result_months_made_negative=sum(sum(r['net'] for r in vv)>0 and sum(r['net'] for r in after_months[k])<0 for k,vv in base_months.items()))
            rows.append(result)
    return rows


def monthly(groups,replays,tracks,reviews,bounds):
    rows=[]
    for a,b,_ in months_until(max(v[1] for v in bounds.values())):
        for strategy in MODES:
            for instrument in bounds:
                base=groups.get((strategy,instrument),[])
                for method in METHODS:
                    track=tracks[strategy,instrument,method]
                    eligible=[r for r in replays[method] if r['strategy']==strategy and r['instrument']==instrument]
                    closed=[r for r in eligible if a<r['available']<=b]
                    entered=[r for r in eligible if a<=r['entry']<b]
                    original=[r for r in base if a<=r['entry']<b]
                    mask=[r for r in original if track.at(r['entry'])==BAD]
                    local=[r for r in reviews if (r['strategy'],r['instrument'],r['method'])==(strategy,instrument,method) and a<=r['decision_at']<b]
                    rows.append(dict(month=a.strftime('%Y-%m'),strategy=strategy,instrument=instrument,method=method,
                        status_start=track.at(a),status_end=track.at(min(b,bounds[instrument][1])) if a<bounds[instrument][1] else UNKNOWN,
                        source_partial=b>bounds[instrument][1],baseline_entries=len(original),direct_excluded_entries=len(mask),
                        replay_entries=len(entered),recommendations=sum(r['action']=='EXCLUDE' for r in local),
                        **{'closed_'+k:v for k,v in statistics(closed).items()},
                        **{'entry_cohort_'+k:v for k,v in statistics(entered).items()}))
    return rows


def annual(replays,groups,tracks):
    rows=[]
    for year in range(2018,2027):
        for strategy in (*MODES,'ALL_INDEPENDENT_ACCOUNTS'):
            for instrument in (*OLD,*NEW,'ALL'):
                for method in METHODS:
                    def selected(r):
                        return completion_period(r['available']).year==year and (strategy=='ALL_INDEPENDENT_ACCOUNTS' or r['strategy']==strategy) and (instrument=='ALL' or r['instrument']==instrument)
                    replay=[r for r in replays[method] if selected(r)]
                    baseline=[r for vv in groups.values() for r in vv if selected(r)]
                    direct=[r for r in baseline if tracks[r['strategy'],r['instrument'],method].at(r['entry'])!=BAD]
                    keys={(r['strategy'],r['instrument'],r['entry']) for r in replay}
                    absent=[r for r in baseline if (r['strategy'],r['instrument'],r['entry']) not in keys]
                    months=defaultdict(float)
                    for r in replay:months[completion_period(r['available']).month]+=r['net']
                    rows.append(dict(year=year,strategy=strategy,instrument=instrument,method=method,
                        **statistics(replay),direct_PF_C1=statistics(direct)['PF_C1'],direct_net_R=statistics(direct)['net_R'],
                        lost_positive_trades=sum(r['net']>0 for r in absent),lost_positive_R=sum(max(0,r['net']) for r in absent),
                        avoided_negative_R=-sum(min(0,r['net']) for r in absent),
                        positive_months=sum(v>0 for v in months.values()),negative_months=sum(v<0 for v in months.values())))
    return rows


def build(archive,market,work,output):
    from .calendar_tail_diagnostics import build_tail_tables
    output.mkdir(parents=True,exist_ok=True);work.mkdir(parents=True,exist_ok=True)
    groups,bounds,raw,hashes=load_sources()
    expected=json.loads((ROOT/'V20-03/results/RESULT_HASHES.json').read_text())
    for name in ('STATISTICS.csv','SESSION_AUDIT.csv','CENSORED_CLOSED.csv'):
        p=ROOT/'V20-03/results'/name
        assert digest(p)==expected[name]
        hashes['V20-03/results/'+name]=digest(p)
    receipts=json.loads((FOLDER/'V20_SUITABILITY_ARTIFACT_MANIFEST.json').read_text())['artifacts']
    for name in ('V20_SUITABILITY_REPLAY_TRADES.csv.gz','V20_SUITABILITY_FINAL_RU.md'):
        p=FOLDER/name;assert digest(p)==receipts[str(p.relative_to(ROOT.parent))]['sha256']
        hashes['V20-04/'+name]=digest(p)
    clocks=session_opens(bounds,market)
    reviews,tracks=decisions_and_tracks(groups,bounds,clocks)
    censored=uncertain_sources();evaluate_reviews(reviews,groups,bounds,censored)
    episodes=exclusion_episodes(reviews,tracks,groups)
    quarters,periods=quarterly_truth(groups,bounds,censored);detections=detect_periods(periods,tracks,groups,clocks)
    print('calendar decisions',len(reviews),'episodes',len(episodes),flush=True)
    from types import SimpleNamespace
    replays,receipt=run_replays(archive,market,work,tracks,SimpleNamespace(groups=groups,bounds=bounds),methods=METHODS,cache_tag='calendar_')
    comparison=compare(groups,replays,tracks,reviews,episodes,quarters,detections,bounds,clocks)
    mm=monthly(groups,replays,tracks,reviews,bounds)
    tails=build_tail_tables(output,groups,raw,bounds,episodes)
    for name,rows in (
        ('V20_CALENDAR_REVIEW_QUARTERLY.csv',[r for r in reviews if r['method']!='HALF_YEAR_6M']),
        ('V20_CALENDAR_REVIEW_HALFYEAR.csv',[r for r in reviews if r['method']=='HALF_YEAR_6M']),
        ('V20_CALENDAR_FALSE_EXCLUSIONS.csv',[r for r in reviews if r['action']=='EXCLUDE' and r['next_q_verdict']=='FALSE']),
        ('V20_CALENDAR_EXCLUSION_EPISODES.csv',episodes),
        ('V20_CALENDAR_REPLAY_COMPARISON.csv',comparison),('V20_CALENDAR_MONTHLY.csv',mm),
        ('V20_CALENDAR_BASELINE_QUARTERS.csv',quarters),('V20_CALENDAR_DETECTIONS.csv',detections),
        ('V20_CALENDAR_ANNUAL.csv',annual(replays,groups,tracks)),
        ('V20_CALENDAR_CROSS_MARKET.csv',overview(reviews,bounds))):dump_csv(output/name,rows)
    snapshots=[]
    for strategy in MODES:
        for instrument in bounds:
            local=[r for r in reviews if (r['strategy'],r['instrument'],r['method'])==(strategy,instrument,'QUARTER_3M_6M') and r['available_instrument']]
            if local:
                latest=max(local,key=lambda r:r['decision_at'])
                snapshots.append({k:v for k,v in dict(latest,source_data_until=bounds[instrument][1],
                    readonly=True,live_feed=False,capital_gate_validated=False,
                    operator_note='OBSERVATION_ONLY_NO_VALIDATED_EXCLUSION').items()
                    if not k.startswith(('next_','second_','episode_','review_interval','until_return','cost_censored','lost_','avoided_','baseline_net_excluded','hypothetical_'))})
    dump_csv(output/'V20_CALENDAR_READONLY_SNAPSHOT.csv',snapshots)
    dump_csv(output/'V20_CALENDAR_REPLAY_TRADES.csv.gz',
        [dict(method=m,**{k:v for k,v in r.items() if k!='path'}) for m,rows in replays.items() for r in rows],compressed=True)
    hashes.update(receipt.pop('source_hashes'))
    hashes['V20-04/V20_CALENDAR_REVIEW_PROTOCOL_RU.md']=digest(FOLDER/'V20_CALENDAR_REVIEW_PROTOCOL_RU.md')
    summary=dict(schema='v20.calendar_review.v1',input_head=INPUT_HEAD,main='6f352acfac7ebdfabba73e143c4dfea3a6e48507',
        source_hashes=hashes,bounds=bounds,baseline_old=1004,baseline_late=1589,
        minima=dict(three_months=MIN3,six_months=MIN6),comparison=comparison,tail_diagnostics=tails,
        replay=receipt,card_action='KEEP_RUNTIME_UNCHANGED',verdict='FAIL_CAPITAL_EXCLUSION',
        readonly_choice='QUARTER_3M_6M_OBSERVATION_ONLY',tail_temporal_discrimination='FAIL',
        data_caveats=['Original late 1589 ledger absent; existing exact-rule reproduction reused.',
            'Old 12 censored closed outcomes and one late terminal open outcome remain unknown.',
            '2026Q3 and old 2022Q4 partial; no future full-quarter labels.',
            'C1 frozen one tick per side, not actual FINAM charges; multiple-account sums are research only.',
            'History is already researched, not untouched OOS; no exchange-calendar completeness proof.'])
    (output/'V20_CALENDAR_REVIEW_RESULTS.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,default=str)+'\n')
    print('calendar artifacts',len(mm),'monthly',flush=True)
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--archive',required=True,type=Path)
    p.add_argument('--market-data',default=Path('/workspace/market-pattern-data/forever'),type=Path)
    p.add_argument('--work',required=True,type=Path);p.add_argument('--output',default=FOLDER,type=Path)
    args=p.parse_args();build(args.archive,args.market_data,args.work,args.output)
