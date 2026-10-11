#!/usr/bin/env python3
"""Independent batch-run signal oracle, forward execution path and CSV economics.

No production strategy, engine, loader or metrics imports. This is algorithmic
verification by the task agent, not external human or second-agent acceptance.
"""
import argparse
import ast
from collections import Counter
import csv
from datetime import date, timedelta
from decimal import Decimal as D, ROUND_CEILING, ROUND_FLOOR
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from IntradayLab.tools.audit_canonical_baseline import (
    FIVE, windows, tick, good, read_source, read_csv, require, assert_value, check_rows, metric)
LAB=ROOT/'IntradayLab'
CONFIG=LAB/'config/equal_high_low_m5_2023_a_v1.json'
OUT=LAB/'results/equal_high_low_m5_2023_a_v1'


def episodes(symbol, raw):
    """Scan exact three-bar slices and recover maximal runs backwards.

    Backward reconstruction differs from the production streaming counters.
    A consumed run stays consumed even if its admission or fill fails.
    """
    output=[];day=date(2023,1,1);first=min(raw).date()
    while day.year==2023:
        for a,z in windows(day) if day>=first else []:
            consumed=set();at=a
            while at<z:
                row=raw.get(at)
                if not good(row,symbol,at):
                    at+=FIVE;continue
                candidates=[]
                for side,index in ((-1,1),(1,2)):
                    times=[at-2*FIVE,at-FIVE,at]
                    if times[0]<a or not all(good(raw.get(t),symbol,t) and
                            tick(symbol,t)==tick(symbol,at) and raw[t][index]==row[index] for t in times):
                        continue
                    level=row[index];begin=times[0]
                    while (begin-FIVE>=a and good(raw.get(begin-FIVE),symbol,begin-FIVE) and
                            tick(symbol,begin-FIVE)==tick(symbol,at) and raw[begin-FIVE][index]==level):
                        begin-=FIVE
                    ident=f'{symbol}_{day}_{"LONG" if side==1 else "SHORT"}_{begin:%H%M}_{int(level/tick(symbol,at))}'
                    if ident in consumed or side*(row[3]-level)<=0:
                        continue
                    consumed.add(ident)
                    candidates.append(dict(signal_id=ident,cluster_id=ident,instrument=symbol,date=str(day),
                        direction=side,signal_at=at+FIVE,signal_bar_start=at,signal_bar_closed_at=at+FIVE,
                        cluster_start=begin,cluster_level=level,cluster_run_bars=int((at-begin)/FIVE)+1,
                        signal_tick=tick(symbol,at),touch_1_start=times[0],touch_2_start=times[1],
                        touch_3_start=at,touch_1_extreme=raw[times[0]][index],
                        touch_2_extreme=raw[times[1]][index],touch_3_extreme=row[index],
                        signal_close=row[3],stop=level-side*tick(symbol,at),
                        target_gross_R='3',target_net_R='3',target_mode='FULL_NET_C1_R',
                        max_hold_calendar_minutes=120,recorded_at=at+FIVE,
                        window_start=a,window_end=z))
                reason='AMBIGUOUS_BOTH_SIDES' if len(candidates)==2 else 'SIGNAL'
                # The production engine supplies windows only to SIGNAL intents.
                for c in candidates:
                    if reason!='SIGNAL':
                        c.pop('window_start');c.pop('window_end')
                    output.append(dict(c,base_reason=reason))
                at+=FIVE
        day+=timedelta(days=1)
    return sorted(output,key=lambda e:(e['signal_at'],e['signal_id']))


def path(symbol,raw,q):
    """Independent next-interval path; Open checks precede completed OHLC checks."""
    entry=q['entry_at'];side=q['direction'];stop=q['stop'];take=q['take']
    deadline=min(entry+timedelta(minutes=120),q['window_end']-FIVE)
    at=entry
    while at<=deadline:
        b=raw.get(at)
        op=b[0] if b else None
        unknown=None;effective=at
        if op is None:
            unknown='MISSING_EXPOSED_BAR'
        elif not op.is_finite() or op<=0 or op%tick(symbol,at):
            unknown='INVALID_EXPOSED_OPEN'
        else:
            gap=op<=stop if side==1 else op>=stop
            if gap or at==deadline:
                price=op;reason='STOP' if gap else 'TIME' if at==entry+timedelta(minutes=120) else 'SESSION_FLAT'
                point=True;conflict=False
                break
            if not good(b,symbol,at):
                unknown='INVALID_EXPOSED_BAR';effective=at+FIVE
            else:
                sh=b[2]<=stop if side==1 else b[1]>=stop
                th=b[1]>=take if side==1 else b[2]<=take
                if sh or th and at!=entry:
                    price=stop if sh else take;reason='STOP' if sh else 'TAKE'
                    point=False;conflict=sh and th
                    break
        if unknown:
            return dict(status='UNKNOWN',exit_reason='UNKNOWN',unknown_reason=unknown,
                unknown_detected_at=at+FIVE,unknown_effective_at=effective,
                exit_price=None,exit_at=None,exit_interval_start=None,exit_interval_end=None,
                resolved_at=None,stop_take_conflict=False)
        at+=FIVE
    else:
        raise AssertionError('UNRESOLVED_ORACLE_PATH')
    expense=tick(symbol,entry)+tick(symbol,at);gross=side*(price-q['entry_price'])
    return dict(status='CLOSED',exit_reason=reason,exit_price=price,exit_tick=tick(symbol,at),
        exit_at=at if point else None,exit_interval_start=at,exit_interval_end=at if point else at+FIVE,
        resolved_at=at if point else at+FIVE,stop_take_conflict=conflict,
        gross=gross,gross_R=gross/q['risk'],cost_c1=expense,cost_R=expense/q['risk'],
        net_c1=gross-expense,net_R_c1=(gross-expense)/q['risk'],
        realized_net_to_net_R=(gross-expense)/(q['risk']+expense))


def replay(symbol,raw,events,*,close_oracle=False):
    ss=[];tt=[];day=None;busy_until=unknown_at=None;prior=today=False
    for event in events:
        if event['date']!=day:
            prior|=today;today=False;day=event['date'];busy_until=unknown_at=None
        s=dict(event,status='REJECTED',reason=event['base_reason'],order_admitted=False,model_filled=False)
        s.update(initial_flat_assumed=True,initial_flat_proven=False,
            prior_unknown_requires_flat_assumption=prior)
        ss.append(s)
        if s['base_reason']!='SIGNAL':
            continue
        entry=s['signal_at'];side=s['direction'];level=s['cluster_level'];step=tick(symbol,entry)
        s.update(entry_mode='ENTRY_CLOSE_ORACLE' if close_oracle else 'ENTRY_NEXT_OPEN',
            waiting_bar_start=None,waiting_bar_closed_at=None,planned_execution_at=entry,
            pending_created=False,open_admission_passed=None)
        if unknown_at is not None and entry>=unknown_at:
            s['reason']='UNKNOWN_POSITION_BLOCK';continue
        if (busy_until is not None and entry<busy_until) or (unknown_at is not None and entry<unknown_at):
            s['reason']='POSITION_BUSY';continue
        if entry>=s['window_end']-FIVE:
            s['reason']='SESSION_LIMIT';continue
        s.update(pending_created=True,order_admitted=True,order_sent_at=entry)
        q={k:s[k] for k in ('signal_id','cluster_id','instrument','direction','signal_at',
            'entry_mode','stop','window_end','max_hold_calendar_minutes','planned_execution_at','order_sent_at','waiting_bar_closed_at')}
        q.update(entry_at=None,entry_price=None,risk=None,take=None,model_filled=False,
            gross=None,gross_R=None,cost_c1=None,cost_R=None,net_c1=None,net_R_c1=None,
            prior_unknown_requires_flat_assumption=prior,initial_flat_assumed=True,initial_flat_proven=False)
        op=s['signal_close'] if close_oracle else raw[entry][0] if entry in raw else None
        if op is None or not op.is_finite() or op<=0 or op%step:
            reason='MISSING_EXECUTION_BAR' if op is None else 'INVALID_EXECUTION_OPEN'
            s.update(status='UNKNOWN',reason=reason)
            q.update(status='UNKNOWN',exit_reason='UNKNOWN',unknown_reason=reason,
                unknown_detected_at=entry+FIVE,unknown_effective_at=entry,exit_price=None,
                exit_at=None,exit_interval_start=None,exit_interval_end=None,resolved_at=None)
            tt.append(q);unknown_at=entry;today=True;continue
        risk=side*(op-s['stop']);distance=side*(op-level)
        rejection=('OPEN_WRONG_SIDE_OF_CLUSTER' if distance<0 else
            'INVALID_STOP_GEOMETRY' if risk<=0 else 'STOP_ABOVE_12_TICKS' if risk>12*step else
            'STOP_BELOW_3_TICKS' if risk<3*step else
            'ENTRY_MORE_THAN_4_TICKS_FROM_CLUSTER' if distance>4*step else None)
        s.update(entry_open=op,entry_tick=step,open_admission_passed=rejection is None)
        if rejection:
            s.update(status='NONFILL',reason=rejection);continue
        target=op+side*(3*risk+8*step)
        target=(target/step).to_integral_value(rounding=ROUND_CEILING if side==1 else ROUND_FLOOR)*step
        s.update(status='MODEL_FILLED',reason='',model_filled=True,risk=risk,take=target)
        q.update(entry_at=entry,entry_price=op,entry_tick=step,cost_entry_c1=step,
            model_filled=True,risk=risk,take=target,target_mode='FULL_NET_C1_R',target_net_R=D(3),
            planned_C1=2*step,d_legacy=3*risk+2*step,d_full=3*risk+8*step,
            rounded_take_distance=side*(target-op),planned_net_to_net_R=(side*(target-op)-2*step)/(risk+2*step),
            legacy_net_to_gross_R=D(3),realized_net_to_net_R=None)
        s.update({k:q[k] for k in ('target_mode','target_net_R','planned_C1','d_legacy','d_full',
            'rounded_take_distance','planned_net_to_net_R','legacy_net_to_gross_R','realized_net_to_net_R')})
        result=path(symbol,raw,q)
        q.update(result);tt.append(q)
        if q['status']=='UNKNOWN':
            unknown_at=q['unknown_effective_at'];today=True
        else:
            busy_until=q['resolved_at']
    return ss,tt


def independent_distribution(rows):
    closed=[r for r in rows if r['status']=='CLOSED']
    win=[r for r in closed if D(r['net_R_c1'])>0];loss=[r for r in closed if D(r['net_R_c1'])<0]
    def mean(cohort,key):
        return sum((D(r[key]) for r in cohort),D(0))/len(cohort) if cohort else None
    monthly={}
    for r in closed:
        m=str(r['signal_at'])[:7];monthly[m]=monthly.get(m,D(0))+D(r['net_R_c1'])
    gains=sum((D(r['net_R_c1']) for r in win),D(0));mg=sum((v for v in monthly.values() if v>0),D(0))
    return dict(unique_trade_days=len({str(r['signal_at'])[:10] for r in closed}),
        average_winner_R=mean(win,'net_R_c1'),average_loser_R=mean(loss,'net_R_c1'),
        average_winner_price=mean(win,'net_c1'),average_loser_price=mean(loss,'net_c1'),
        active_months=len(monthly),positive_months=sum(v>0 for v in monthly.values()),
        negative_months=sum(v<0 for v in monthly.values()),zero_closed_economy_months=12-sum(v!=0 for v in monthly.values()),
        largest_winner_share_R=max((D(r['net_R_c1']) for r in win),default=D(0))/gains if gains else None,
        top_three_winners_share_R=sum(sorted((D(r['net_R_c1']) for r in win),reverse=True)[:3],D(0))/gains if gains else None,
        largest_positive_month_share_R=max(monthly.values(),default=D(0))/mg if mg else None,
        monthly_closed_Net_R=dict(sorted(monthly.items())))


def write_json(path,value):
    path.write_text(json.dumps(value,default=str,indent=2,sort_keys=True,ensure_ascii=False)+'\n')


def audit(root,output):
    from IntradayLab.tools.equal_high_low_contract import check_output,verify_freeze,bounded_reads
    check_output(output)
    verify_freeze()
    cfg=json.loads(CONFIG.read_text())
    require(subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()==cfg['source_ref'],'SOURCE_HEAD')
    require(not subprocess.check_output(['git','-C',str(root),'status','--porcelain=v1','--untracked-files=all'],text=True).strip(),'SOURCE_DIRTY')
    require(cfg['parameters']==dict(version='A_v1',signal_tf='M5',touches=3,tolerance_ticks=0,
        stop_buffer_ticks=1,minimum_risk_ticks=3,maximum_risk_ticks=12,maximum_rebound_ticks=4,
        target_net_R='3',target_mode='FULL_NET_C1_R',max_hold_calendar_minutes=120),'PARAMETERS')
    for path_name,digest in cfg['execution_code_sha256'].items():
        require(hashlib.sha256((ROOT/path_name).read_bytes()).hexdigest()==digest,'FROZEN_CODE '+path_name)
    for path_name in [* (LAB/'core').glob('*.py'),LAB/'strategies/equal_high_low_m5.py']:
        for node in ast.walk(ast.parse(path_name.read_text())):
            if isinstance(node,ast.ImportFrom):
                module=node.module or ''
                require(not module.startswith('TradingSystemLab'),'PROTECTED_IMPORT')
                if path_name.parent.name=='core':
                    require('strategies' not in module,'CANDIDATE_IMPORT_IN_CORE')
    with bounded_reads(root,cfg) as actual_read_guard:
        raw,receipts=read_source(root,cfg)
    ss=read_csv(output/'signals.csv');tt=read_csv(output/'trades.csv')
    metrics=json.loads((output/'metrics.json').read_text())
    cov=read_csv(output/'coverage_daily.csv');counts=dict(signal_fields=0,trade_fields=0,coverage_fields=0,metric_fields=0,report_fields=0)
    details={}
    for symbol in cfg['instruments']:
        expected_s,expected_t=replay(symbol,raw[symbol],episodes(symbol,raw[symbol]))
        actual_s=[s for s in ss if s['instrument']==symbol];actual_t=[t for t in tt if t['instrument']==symbol]
        for actual,expected,label in ((actual_s,expected_s,'signal_fields'),(actual_t,expected_t,'trade_fields')):
            keys=sorted({k for r in expected for k in r if k!='unknown_effective_at'})
            counts[label]+=check_rows(actual,expected,keys,label)
        # Independent reconstruction of every expected daytime observation.
        day=date(2023,1,1);expected_cov=[]
        while day.year==2023:
            if windows(day):
                slots=[]
                if day>=min(raw[symbol]).date():
                    for a,z in windows(day):
                        while a<z:
                            slots.append(a);a+=FIVE
                missing=sum(t not in raw[symbol] for t in slots)
                invalid=sum(t in raw[symbol] and not good(raw[symbol][t],symbol,t) for t in slots)
                expected_cov.append(dict(date=str(day),status='PRE_INCEPTION' if day<min(raw[symbol]).date() else
                    'INCOMPLETE' if missing or invalid else 'COMPLETE',missing_bars=missing,invalid_bars=invalid,
                    expected_bars=len(slots),valid_bars=len(slots)-missing-invalid))
            day+=timedelta(days=1)
        actual_cov=[c for c in cov if c['instrument']==symbol]
        require(len(actual_cov)==len(expected_cov),'COVERAGE_ROW_SET')
        for a,b in zip(actual_cov,expected_cov):
            for k,v in b.items():
                assert_value(a[k],v,'COVERAGE '+symbol+' '+k);counts['coverage_fields']+=1
        m=metrics['instruments'][symbol]
        for k,v in metric(actual_t).items():
            assert_value(m['conditional_closed_only_C1'][k],v,'METRIC '+symbol+' '+k);counts['metric_fields']+=1
        for key,field in (('gross_price','gross'),('C1_price','cost_c1'),('net_price','net_c1'),
                          ('gross_R','gross_R'),('C1_R','cost_R'),('net_R','net_R_c1')):
            expected=sum((D(t[field]) for t in actual_t if t['status']=='CLOSED'),D(0))
            assert_value(m['economics'][key],expected,'GROSS_C1_NET '+key);counts['metric_fields']+=1
        exits=dict(sorted(Counter(t['exit_reason'] for t in actual_t if t['status']=='CLOSED').items()))
        require(m['conditional_closed_only_C1']['exit_reasons']==exits,'EXIT_REASONS')
        refusals=dict(sorted(Counter(s['reason'] for s in expected_s if s['base_reason']=='SIGNAL' and s['reason']).items()))
        require(m['rejection_reasons']==refusals,'REFUSAL_REASONS')
        known_rejected=sum(s['base_reason']=='SIGNAL' and s['status'] in ('REJECTED','NONFILL') for s in expected_s)
        require(m['rejected_known_entries']==known_rejected,'REJECTED_COUNT')
        require(m['signals']==m['model_fills']+m['rejected_known_entries']+m['unknown_entry_attempts'],'FUNNEL_CONSERVATION')
        for k,v in independent_distribution(actual_t).items():
            if isinstance(v,dict):
                require(set(m['distribution'][k])==set(v),'MONTH_SET')
                for month,value in v.items():
                    assert_value(m['distribution'][k][month],value,'MONTH_NET');counts['metric_fields']+=1
            else:
                assert_value(m['distribution'][k],v,'DISTRIBUTION '+k);counts['metric_fields']+=1
        require(not m['optimization_allowed'],'OPTIMIZATION_FORBIDDEN')
        require(m['signals']==sum(s['base_reason']=='SIGNAL' for s in expected_s),'SIGNAL_COUNT')
        require(m['unknown']==sum(t['status']=='UNKNOWN' for t in expected_t),'UNKNOWN_COUNT')
        for t in actual_t:
            if t['status']=='UNKNOWN':
                require(all(not t.get(k) for k in ('exit_price','net_c1','net_R_c1','gross','cost_c1')),'UNKNOWN_FAKE_ECONOMICS')
        credible=all(c['status']=='COMPLETE' for c in expected_cov) and not m['unknown'] and not any(t.get('prior_unknown_requires_flat_assumption')=='True' for t in actual_t)
        require(m['annual_complete']==credible,'COMPLETE_CLASSIFICATION')
        if not credible:
            require(all(v is None for v in m['annual'].values()),'ANNUAL_NULLS')
        details[symbol]=dict(signals=m['signals'],model_fills=m['model_fills'],closed=m['closed'],unknown=m['unknown'],status='PASS')
    for filename,cohort_key in [('instrument_report.csv',None),('monthly_report.csv','month'),('direction_report.csv','direction')]:
        reports=read_csv(output/filename)
        require(len(reports)==(4 if cohort_key is None else 48 if cohort_key=='month' else 8),'REPORT_ROW_SET')
        for r in reports:
            cohort=[t for t in tt if t['instrument']==r['instrument']]
            if cohort_key=='month':
                cohort=[t for t in cohort if str(t['signal_at'])[:7]==r['month']]
            elif cohort_key=='direction':
                cohort=[t for t in cohort if t['direction']==('1' if r['direction']=='LONG' else '-1')]
            for k,v in metric(cohort).items():
                if r['coverage_classification']=='NO_COVERAGE' and k!='closed':
                    v=None
                assert_value(r['conditional_'+k],v,'REPORT '+filename+' '+k);counts['report_fields']+=1
            candidates=[s for s in ss if s['instrument']==r['instrument']]
            if cohort_key=='month':candidates=[s for s in candidates if s['date'][:7]==r['month']]
            elif cohort_key=='direction':candidates=[s for s in candidates if s['direction']==('1' if r['direction']=='LONG' else '-1')]
            for k,v in dict(signals=sum(s['base_reason']=='SIGNAL' for s in candidates),
                model_fills=sum(t['model_filled']=='True' for t in cohort),closed=sum(t['status']=='CLOSED' for t in cohort),
                unknown=sum(t['status']=='UNKNOWN' for t in cohort),raw_directional_candidates=len(candidates)).items():
                assert_value(r[k],v,'REPORT_COUNT '+k);counts['report_fields']+=1
    oracle=json.loads((output/'diagnostics/close_oracle_metrics.json').read_text())
    require(oracle['diagnostic_only'] and not oracle['economic_pass_allowed'],'ORACLE_NOT_TRADE_EVIDENCE')
    require('ENTRY_CLOSE_ORACLE' not in (output/'trades.csv').read_text(),'ORACLE_IN_TRADING_LEDGER')
    result=dict(status='PASS',method='independent backward maximal-run slices, forward paths, CSV-only economics; no production imports',
        independent_implementation=True,external_human_signoff=False,checked_fields=counts,instruments=details,
        source_receipts=receipts,actual_read_guard=actual_read_guard,oracle_separate_from_economic_classification=True,
        causal_signal_close_equals_immediate_next_M5_Open=True,optimization_allowed=False)
    write_json(output/'audit.json',result)
    (output/'Independent_Audit.md').write_text('# Independent algorithm audit — A_v1\n\n**PASS**. '+result['method']+'.\n\n'
        'All completed touches, cluster IDs/consumption, signal boundaries, actual next Opens, dated grids, structural Stops, pre-fill limits, Take/C1, Stop-first, session-flat, UNKNOWN nulls and month/instrument/direction reports checked.\n\n'
        'This is a separate algorithm implemented by the task agent; external human signoff has not been obtained. Full-year economic evidence remains limited by missing coverage/UNKNOWN. Oracle is diagnostic only.\n\n'
        'Checked fields: `'+json.dumps(counts,sort_keys=True)+'`. Source read receipts and scope in audit.json; frozen artifacts/regressions and byte determinism in validation.json.\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data-root',type=Path,required=True);p.add_argument('--output',type=Path,default=OUT)
    a=p.parse_args();print(json.dumps(audit(a.data_root,a.output),default=str,sort_keys=True))
