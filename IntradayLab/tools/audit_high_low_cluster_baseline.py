#!/usr/bin/env python3
"""Independent batch envelope partition, raw slices, forward paths and CSV math.

Imports no production strategy, Backtester, data loader or metrics. The existing
independent A execution oracle is reused only for the identical execution contract.
This is implementation independence, not external human/second-agent signoff.
"""
import argparse
from collections import Counter
from datetime import date, timedelta
from decimal import Decimal as D, ROUND_HALF_UP
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from IntradayLab.tools.audit_canonical_baseline import FIVE, windows, tick, good, read_source, read_csv, require, assert_value, check_rows, metric
from IntradayLab.tools.audit_equal_high_low_baseline import replay, independent_distribution, write_json
from IntradayLab.tools.high_low_cluster_contract import verify_freeze,bounded_reads,protected_check,output_path


def episodes(symbol,raw,n,with_ledger=False):
    events=[];ledger=[];day=date(2023,1,1);first=min(raw).date()
    while day.year==2023:
        ws=windows(day) if day>=first else []
        for wi,(a,z) in enumerate(ws):
            slots=[];at=a
            while at<z:slots.append(at);at+=FIVE
            for side,index in ((-1,1),(1,2)):
                j=0
                while j<len(slots):
                    if not good(raw.get(slots[j]),symbol,slots[j]):j+=1;continue
                    end=j+1
                    while end<len(slots):
                        now=slots[end]
                        if not good(raw.get(now),symbol,now) or tick(symbol,now)!=tick(symbol,slots[j]):break
                        prices=[raw[t][index] for t in slots[j:end+1]]
                        if max(prices)-min(prices)>3*tick(symbol,now):break
                        end+=1
                    block=slots[j:end];step=tick(symbol,block[0]);v0=raw[block[0]][index]
                    ident=f'{symbol}_{day}_{"LONG" if side==1 else "SHORT"}_{block[0]:%H%M}_{int(v0/step)}'
                    consumed=False
                    for k in range(n-1,len(block)):
                        times=block[k-n+1:k+1];values=[raw[t][index] for t in times]
                        lower,upper=min(values),max(values);boundary=upper if side==-1 else lower
                        hits=[t for t in times if raw[t][index]==boundary];width=(upper-lower)/step
                        if not 1<=width<=3 or len(hits)<2:continue
                        consumed=True;at=block[k];prefix=[raw[t][index] for t in block[:k+1]]
                        round_step=D({'USDRUBF':'.10','CNYRUBF':'.05','GLDRUBF':'10','IMOEXF':'10'}[symbol])
                        nearest=(boundary/round_step).to_integral_value(rounding=ROUND_HALF_UP)*round_step
                        distance=abs(boundary-nearest);close=raw[at][3]
                        event=dict(signal_id=f'B{n}_{ident}',cluster_id=f'B{n}_{ident}',episode_id=ident,
                            instrument=symbol,date=str(day),direction=side,signal_at=at+FIVE,
                            signal_bar_start=at,signal_bar_closed_at=at+FIVE,episode_start=block[0],
                            episode_bars_at_formation=k+1,episode_envelope_min=min(prefix),episode_envelope_max=max(prefix),
                            cluster_start=times[0],cluster_end=at,cluster_bars=n,cluster_min=lower,cluster_max=upper,
                            cluster_level=boundary,cluster_width_ticks=width,boundary_touches=len(hits),internal_touches=n-len(hits),
                            first_touch=hits[0],last_touch=hits[-1],extrema=values,extreme_times=times,
                            signal_tick=step,signal_close=close,signal_close_distance_ticks=side*(close-boundary)/step,
                            round_step=round_step,nearest_round_level=nearest,round_distance_price=distance,
                            round_distance_ticks=distance/step,level_type='ROUND_NEAR' if distance<=step else 'ORDINARY_FAR',
                            stop=boundary-side*step,target_gross_R='3',target_net_R='3',target_mode='FULL_NET_C1_R',
                            max_hold_calendar_minutes=120,recorded_at=at+FIVE,
                            base_reason='SIGNAL' if side*(close-boundary)>0 else 'CLOSE_AT_BOUNDARY',
                            window_start=a,window_end=z)
                        events.append(event);break
                    if end<len(slots):
                        nxt=slots[end]
                        reason='MISSING_OR_INVALID_BAR' if not good(raw.get(nxt),symbol,nxt) else 'TICK_CHANGE' if tick(symbol,nxt)!=step else 'ENVELOPE_ABOVE_3_TICKS'
                        observed=nxt+FIVE
                    else:
                        reason='SESSION_CHANGE' if wi+1<len(ws) else 'DAY_END'
                        observed=ws[wi+1][0]+FIVE if wi+1<len(ws) else slots[-1]+FIVE
                    envelope=[raw[t][index] for t in block]
                    if consumed: ledger.append(dict(episode_id=ident,instrument=symbol,direction=side,episode_start=block[0],
                        episode_last=block[-1],episode_end_observed_at=observed,reset_reason=reason,episode_bars=len(block),
                        envelope_min=min(envelope),envelope_max=max(envelope),consumed=consumed))
                    j=end
        day+=timedelta(days=1)
    grouped={}
    for event in events:grouped.setdefault(event['signal_at'],[]).append(event)
    for candidates in grouped.values():
        if sum(e['base_reason']=='SIGNAL' for e in candidates)==2:
            for event in candidates:event['base_reason']='AMBIGUOUS_BOTH_SIDES'
        for event in candidates:
            if event['base_reason']!='SIGNAL':event.pop('window_start');event.pop('window_end')
    events.sort(key=lambda e:(e['signal_at'],e['signal_id']))
    return (events,ledger) if with_ledger else events


def expected_records(symbol,raw,n):
    events=episodes(symbol,raw,n);ss,tt=replay(symbol,raw,events);by={s['signal_id']:s for s in ss}
    for s in ss:
        op=s.get('entry_open')
        s['entry_distance_ticks']=s['direction']*(op-s['cluster_level'])/s['entry_tick'] if op is not None else None
        s['open_vs_close_ticks']=s['direction']*(op-s['signal_close'])/s['entry_tick'] if op is not None else None
    for t in tt:
        s=by[t['signal_id']]
        for k in ('episode_id','level_type','boundary_touches','cluster_bars','cluster_min','cluster_max','cluster_width_ticks',
                  'cluster_level','round_distance_ticks','signal_close','entry_distance_ticks','open_vs_close_ticks'):t[k]=s[k]
        t['holding_lower_minutes']=D(str((t['exit_interval_start']-t['entry_at']).total_seconds()/60)) if t['status']=='CLOSED' else None
        t['holding_upper_minutes']=D(str((t['exit_interval_end']-t['entry_at']).total_seconds()/60)) if t['status']=='CLOSED' else None
    return ss,tt


def geometry(rows,candidates):
    fills=[t for t in rows if t['model_filled']=='True'];closed=[t for t in rows if t['status']=='CLOSED']
    def avg(values):return sum(values,D(0))/len(values) if values else None
    costs=[D(t['planned_C1'])/D(t['risk']) for t in fills]
    return dict(mean_stop_ticks=avg([D(t['risk'])/D(t['entry_tick']) for t in fills]),
        mean_C1_initial_risk_R=avg(costs),min_C1_initial_risk_R=min(costs,default=None),max_C1_initial_risk_R=max(costs,default=None),
        mean_entry_distance_ticks=avg([D(t['entry_distance_ticks']) for t in fills]),
        mean_directional_open_vs_signal_close_ticks=avg([D(t['open_vs_close_ticks']) for t in fills]),
        mean_target_distance_ticks=avg([D(t['rounded_take_distance'])/D(t['entry_tick']) for t in fills]),
        mean_known_holding_lower_minutes=avg([D(t['holding_lower_minutes']) for t in closed]),
        mean_known_holding_upper_minutes=avg([D(t['holding_upper_minutes']) for t in closed]),
        stop_ticks_histogram=dict(sorted(Counter(str(D(t['risk'])/D(t['entry_tick'])) for t in fills).items())),
        boundary_touch_histogram=dict(sorted(Counter(t['boundary_touches'] for t in candidates).items())))


def audit(root,output,n):
    cfg,freeze,_=verify_freeze(n);scope=protected_check(root,cfg)
    require(json.loads((output/'config.json').read_text())==cfg,'OUTPUT_CONFIG')
    with bounded_reads(root,cfg) as reads:raw,receipts=read_source(root,cfg)
    ss=read_csv(output/'signals.csv');tt=read_csv(output/'trades.csv');cov=read_csv(output/'coverage_daily.csv')
    metrics=json.loads((output/'metrics.json').read_text());counts=Counter();details={}
    for symbol in cfg['instruments']:
        es,et=expected_records(symbol,raw[symbol],n)
        actual_s=[s for s in ss if s['instrument']==symbol];actual_t=[t for t in tt if t['instrument']==symbol]
        for actual,expected,label in ((actual_s,es,'signal_fields'),(actual_t,et,'trade_fields')):
            keys=sorted({k for r in expected for k in r if k not in ('unknown_effective_at','extrema','extreme_times')})
            counts[label]+=check_rows(actual,expected,keys,label)
        for a,e in zip(actual_s,es):
            for k in ('extrema','extreme_times'):
                require(json.loads(a[k])==[str(v) for v in e[k]],'RAW_CONSTRUCTION '+k);counts['signal_fields']+=n
        _,expected_ledger=episodes(symbol,raw[symbol],n,True)
        actual_ledger=[r for r in read_csv(output/'episodes.csv') if r['instrument']==symbol]
        aa={r['episode_id']:r for r in actual_ledger};ee={r['episode_id']:r for r in expected_ledger}
        require(len(aa)==len(actual_ledger) and set(aa)==set(ee),'EPISODE_LEDGER_SET')
        for ident,e in ee.items():
            for k,v in e.items():assert_value(aa[ident][k],v,'EPISODE '+ident+' '+k);counts['episode_fields']+=1
        require(len({s['episode_id'] for s in actual_s})==len(actual_s),'REUSED_EVENT')
        require(len({t['episode_id'] for t in actual_t})==len(actual_t),'REPEATED_ENTRY')
        day=date(2023,1,1);expected_cov=[]
        while day.year==2023:
            if windows(day):
                slots=[]
                if day>=min(raw[symbol]).date():
                    for a,z in windows(day):
                        while a<z:slots.append(a);a+=FIVE
                missing=sum(t not in raw[symbol] for t in slots)
                invalid=sum(t in raw[symbol] and not good(raw[symbol][t],symbol,t) for t in slots)
                expected_cov.append(dict(date=str(day),status='PRE_INCEPTION' if day<min(raw[symbol]).date() else 'INCOMPLETE' if missing or invalid else 'COMPLETE',missing_bars=missing,invalid_bars=invalid,expected_bars=len(slots),valid_bars=len(slots)-missing-invalid))
            day+=timedelta(days=1)
        actual_cov=[c for c in cov if c['instrument']==symbol]
        require(len(actual_cov)==len(expected_cov),'COVERAGE_SET')
        for a,e in zip(actual_cov,expected_cov):
            for k,v in e.items():assert_value(a[k],v,'COVERAGE '+k);counts['coverage_fields']+=1
        m=metrics['instruments'][symbol]
        for k,v in metric(actual_t).items():assert_value(m['conditional_closed_only_C1'][k],v,'METRIC '+k);counts['metric_fields']+=1
        for key,field in (('gross_price','gross'),('C1_price','cost_c1'),('net_price','net_c1'),('gross_R','gross_R'),('C1_R','cost_R'),('net_R','net_R_c1')):
            assert_value(m['economics'][key],sum((D(t[field]) for t in actual_t if t['status']=='CLOSED'),D(0)),'ECONOMICS '+key);counts['metric_fields']+=1
        for k,v in independent_distribution(actual_t).items():
            if isinstance(v,dict):
                require(set(m['distribution'][k])==set(v),'MONTHS')
                for month,value in v.items():assert_value(m['distribution'][k][month],value,'MONTH_NET');counts['metric_fields']+=1
            else:assert_value(m['distribution'][k],v,'DISTRIBUTION '+k);counts['metric_fields']+=1
        for key,value in dict(detected_accumulations=len(es),signals=sum(s['base_reason']=='SIGNAL' for s in es),model_fills=sum(t['model_filled'] for t in et),closed=sum(t['status']=='CLOSED' for t in et),unknown=sum(t['status']=='UNKNOWN' for t in et)).items():
            assert_value(m[key],value,'FUNNEL '+key);counts['metric_fields']+=1
        for k,v in geometry(actual_t,actual_s).items():
            if isinstance(v,dict):require(m['geometry'][k]==v,'GEOMETRY '+k)
            else:assert_value(m['geometry'][k],v,'GEOMETRY '+k)
            counts['metric_fields']+=1
        require(m['signals']==m['model_fills']+m['rejected_known_entries']+m['unknown_entry_attempts'],'FUNNEL_CONSERVATION')
        require(m['all_candidate_refusal_reasons']==dict(sorted(Counter(s['reason'] for s in es if s['reason']).items())),'REASONS')
        for t in actual_t:
            if t['status']=='UNKNOWN':require(all(not t.get(k) for k in ('exit_price','net_c1','net_R_c1','gross','cost_c1')),'UNKNOWN_FAKE_PNL')
        credible=all(c['status']=='COMPLETE' for c in expected_cov) and not m['unknown'] and not any(t.get('prior_unknown_requires_flat_assumption')=='True' for t in actual_t)
        require(m['annual_complete']==credible,'ANNUAL_COMPLETENESS')
        if not credible:require(all(v is None for v in m['annual'].values()),'ANNUAL_NULLS')
        require(not m['optimization_allowed'],'OPTIMIZATION_FORBIDDEN')
        for reason,v in m['loss_attribution'].items():
            cohort=[t for t in actual_t if t['status']=='CLOSED' and t['exit_reason']==reason]
            assert_value(v['count'],len(cohort),'EXIT_COUNT')
            for k,f in [('gross_R','gross_R'),('cost_R','cost_R'),('net_R','net_R_c1')]:
                assert_value(v[k],sum((D(t[f]) for t in cohort),D(0)),'ATTRIBUTION '+k);counts['metric_fields']+=1
        details[symbol]=dict(status='PASS',detected=len(es),trades=len(et))
    for filename,key,size in [('instrument_report.csv',None,4),('monthly_report.csv','month',48),('direction_report.csv','direction',8),('round_report.csv','level_type',12),('boundary_touch_report.csv','boundary_touches',4*(n-2))]:
        reports=read_csv(output/filename);require(len(reports)==size,'REPORT_SET '+filename)
        for r in reports:
            ts=[t for t in tt if t['instrument']==r['instrument']];candidates=[s for s in ss if s['instrument']==r['instrument']]
            if key=='month':ts=[t for t in ts if str(t['signal_at'])[:7]==r[key]];candidates=[s for s in candidates if s['date'][:7]==r[key]]
            elif key=='direction':
                side='1' if r[key]=='LONG' else '-1';ts=[t for t in ts if t['direction']==side];candidates=[s for s in candidates if s['direction']==side]
            elif key and r[key]!='ALL':ts=[t for t in ts if t[key]==r[key]];candidates=[s for s in candidates if s[key]==r[key]]
            for k,v in metric(ts).items():
                if r['coverage_classification']=='NO_COVERAGE' and k!='closed':v=None
                assert_value(r['conditional_'+k],v,'REPORT '+filename+' '+k);counts['report_fields']+=1
            for k,v in independent_distribution(ts).items():
                if isinstance(v,dict):require(json.loads(r['conditional_'+k])=={month:str(value) for month,value in v.items()},'REPORT_DISTRIBUTION '+k)
                else:assert_value(r['conditional_'+k],v,'REPORT_DISTRIBUTION '+k)
                counts['report_fields']+=1
            for k,v in geometry(ts,candidates).items():
                if isinstance(v,dict):require(json.loads(r[k])==v,'REPORT_GEOMETRY '+k)
                else:assert_value(r[k],v,'REPORT_GEOMETRY '+k)
                counts['report_fields']+=1
            for k,v in dict(detected_accumulations=len(candidates),signals=sum(s['base_reason']=='SIGNAL' for s in candidates),model_fills=sum(t['model_filled']=='True' for t in ts),closed=sum(t['status']=='CLOSED' for t in ts),unknown=sum(t['status']=='UNKNOWN' for t in ts)).items():
                assert_value(r[k],v,'REPORT_COUNT '+filename+' '+k);counts['report_fields']+=1
    for filename,expected in [('rejected_entries.csv',[s for s in ss if s['model_filled']!='True']),('unknown_report.csv',[t for t in tt if t['status']=='UNKNOWN'])]:
        actual=read_csv(output/filename)
        keys=sorted({k for r in actual+expected for k in r})
        counts['report_fields']+=check_rows(actual,expected,keys,filename)
    result=dict(status='PASS',pre_pnl_freeze_commit=freeze,method='Independent raw batch envelope partitions and N-bar slices; independent forward execution paths; CSV-only report arithmetic',independent_implementation=True,external_human_signoff=False,checked_fields=dict(counts),instruments=details,source_receipts=receipts,actual_read_guard=reads,protected_files=scope,optimization_allowed=False)
    write_json(output/'audit.json',result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data-root',type=Path,required=True);p.add_argument('--bars',type=int,choices=(4,7,10),required=True);p.add_argument('--output',type=Path)
    a=p.parse_args();r=audit(a.data_root,a.output or output_path(a.bars),a.bars);print(json.dumps(dict(status=r['status'],checked_fields=r['checked_fields']),sort_keys=True))
