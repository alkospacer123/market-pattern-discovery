#!/usr/bin/env python3
"""Independent batch R17 oracle, raw paths and ledger economics.

Imports no production loader, strategy, engine, indicators or metric functions.
Reuses only the accepted independent auditor's calendar/grid/source/assertion
utilities. This is an independent implementation, not external human signoff.
"""
import argparse
import ast
from collections import Counter, deque
from datetime import date, timedelta
from decimal import Decimal as D, ROUND_HALF_UP, ROUND_CEILING, ROUND_FLOOR
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
CONFIG=LAB/'config/r17_orb_breakout_retest_2023_m5_v1.json'
FREEZE='24f92c68ecc6e4425e4da430de1fb4f73f058399'


def atr_history(symbol,raw):
    ranges=deque(maxlen=14);previous=None;out={}
    for at,b in raw.items():
        if good(b,symbol,at):
            value=b[1]-b[2]
            if previous is not None and previous+FIVE==at:
                value=max(value,abs(b[1]-raw[previous][3]),abs(b[2]-raw[previous][3]))
            ranges.append(value);previous=at
        else:
            previous=None
        out[at]=sum(ranges,D(0))/14 if len(ranges)==14 else None
    return out


def signal_windows(day):
    calendar=windows(day)
    if not calendar:
        return []
    origin=calendar[0][0]
    return [(origin+3*FIVE,origin+timedelta(hours=3)),
            (calendar[1][0],origin+timedelta(hours=6,minutes=55))]


def episodes(symbol,raw):
    output=[];day=date(2023,1,1);atr=atr_history(symbol,raw)
    while day.year==2023:
        calendar=windows(day)
        if not calendar or day<min(raw).date():
            day+=timedelta(days=1);continue
        origin=calendar[0][0]
        opening=[raw.get(origin+i*FIVE) for i in range(3)]
        if not all(good(b,symbol,origin+i*FIVE) for i,b in enumerate(opening)):
            output.append(dict(signal_id=f'{symbol}_{day}_NO_OR',instrument=symbol,date=str(day),
                               direction=0,signal_at=None,base_reason='NO_OR'))
            day+=timedelta(days=1);continue
        high=max(b[1] for b in opening);low=min(b[2] for b in opening)
        starts=[]
        for a,z in signal_windows(day):
            while a<z:
                starts.append((a,z));a+=FIVE
        diagnosed=False
        for at,z in starts:
            if good(raw.get(at),symbol,at) and atr[at] is None and not diagnosed:
                output.append(dict(signal_id=f'{symbol}_{day}_NO_ATR',instrument=symbol,date=str(day),
                    direction=0,signal_at=None,base_reason='ATR_UNAVAILABLE',recorded_at=at+FIVE))
                diagnosed=True
        for side in (-1,1):
            onset=next(((at,z) for at,z in starts if good(raw.get(at),symbol,at) and atr[at] is not None and
                       (raw[at][3]>=high+D('.30')*atr[at] if side==1 else raw[at][3]<=low-D('.30')*atr[at])),None)
            if onset is None:
                continue
            at,z=onset;b=raw[at];successor=at+FIVE
            start=next(a for a,end in signal_windows(day) if end==z)
            rec=dict(signal_id=f'{symbol}_{day}_{side}_{at:%H%M}',instrument=symbol,date=str(day),direction=side,
                signal_at=None,breakout_start=at,breakout_closed_at=at+FIVE,breakout_close=b[3],
                breakout_atr14=atr[at],breakout_tick=tick(symbol,at),
                breakout_threshold=high+D('.30')*atr[at] if side==1 else low-D('.30')*atr[at],
                or_high=high,or_low=low,or_available_at=origin+3*FIVE,
                signal_window_start=start,signal_window_end=z,recorded_at=at+FIVE)
            if successor+FIVE>z:
                reason='NO_RETEST_WINDOW'
            else:
                following=raw.get(successor);rec['recorded_at']=successor+FIVE
                if following is None:
                    reason='NO_RETEST_MISSING_BAR'
                elif not good(following,symbol,successor):
                    reason='NO_RETEST_INVALID_BAR'
                else:
                    touch=2*tick(symbol,successor)
                    valid=(low<=following[2]<=high+touch and following[3]>=high) if side==1 else (
                           low-touch<=following[1]<=high and following[3]<=low)
                    reason='SIGNAL' if valid else 'NO_RETEST_CONDITION'
                    if valid:
                        step=tick(symbol,successor)
                        mid=((high+low)/2/step).to_integral_value(rounding=ROUND_HALF_UP)*step
                        signal=successor+FIVE
                        execution=signal+FIVE
                        cal=next(w for w in calendar if w[0]<=successor<w[1])
                        rec.update(signal_at=signal,retest_start=successor,retest_closed_at=signal,
                            retest_tick=step,or_mid_rounded=mid,stop=mid-side*step,
                            max_hold_calendar_minutes=120,target_gross_R='1.5',
                            waiting_bar_start=signal,waiting_bar_closed_at=execution,
                            planned_execution_at=execution,window_start=cal[0],window_end=cal[1])
            output.append(dict(rec,base_reason=reason))
        day+=timedelta(days=1)
    return sorted(output,key=lambda e:(e.get('recorded_at') or windows(date.fromisoformat(e['date']))[-1][1],e['signal_id']))


def path(symbol,raw,q):
    entry=q['entry_at'];side=q['direction'];stop=q['stop'];target=q['take']
    deadline=q['effective_deadline_at'];at=entry
    while at<=deadline:
        b=raw.get(at)
        if b is None:
            return dict(status='UNKNOWN',exit_reason='UNKNOWN',unknown_reason='MISSING_EXPOSED_BAR',
                unknown_detected_at=at+FIVE,unknown_effective_at=at,exit_price=None,
                exit_at=None,exit_interval_start=None,exit_interval_end=None,resolved_at=None,stop_take_conflict=False)
        op=b[0]
        if not op.is_finite() or op<=0 or op%tick(symbol,at):
            return dict(status='UNKNOWN',exit_reason='UNKNOWN',unknown_reason='INVALID_EXPOSED_OPEN',
                unknown_detected_at=at+FIVE,unknown_effective_at=at,exit_price=None,
                exit_at=None,exit_interval_start=None,exit_interval_end=None,resolved_at=None,stop_take_conflict=False)
        gap=op<=stop if side==1 else op>=stop
        if gap or at==deadline:
            reason=('STOP' if gap else 'TIME' if at==entry+timedelta(minutes=120)
                    else 'TRADE_DEADLINE' if at==q['trade_deadline_at'] else 'SESSION_FLAT')
            price=op;point=True;conflict=False
        elif not good(b,symbol,at):
            return dict(status='UNKNOWN',exit_reason='UNKNOWN',unknown_reason='INVALID_EXPOSED_BAR',
                unknown_detected_at=at+FIVE,unknown_effective_at=at+FIVE,exit_price=None,
                exit_at=None,exit_interval_start=None,exit_interval_end=None,resolved_at=None,stop_take_conflict=False)
        else:
            sh=b[2]<=stop if side==1 else b[1]>=stop
            th=b[1]>=target if side==1 else b[2]<=target
            if sh or th and at!=entry:
                reason='STOP' if sh else 'TAKE';price=stop if sh else target;point=False;conflict=sh and th
            else:
                at+=FIVE;continue
        gross=side*(price-q['entry_price']);exit_tick=tick(symbol,at)
        expense=tick(symbol,entry)+exit_tick
        return dict(status='CLOSED',exit_reason=reason,exit_price=price,exit_tick=exit_tick,
            exit_at=at if point else None,exit_interval_start=at,exit_interval_end=at if point else at+FIVE,
            resolved_at=at if point else at+FIVE,gross=gross,gross_R=gross/q['risk'],
            cost_c1=expense,cost_R=expense/q['risk'],net_c1=gross-expense,
            net_R_c1=(gross-expense)/q['risk'],stop_take_conflict=conflict)
    raise AssertionError('ORACLE_DEADLINE')


def replay(symbol,raw,events):
    signals=[];trades=[];day=None;busy_until=None;unknown_at=None;prior=False;today=False
    for event in events:
        if event['date']!=day:
            prior|=today;today=False;day=event['date'];busy_until=unknown_at=None
        s=dict(event,status='REJECTED',reason=event['base_reason'],order_admitted=False,model_filled=False)
        signals.append(s)
        if s['base_reason']!='SIGNAL':
            continue
        now=s['signal_at'];entry=s['planned_execution_at']
        if unknown_at and now>=unknown_at:
            s['reason']='UNKNOWN_POSITION_BLOCK';continue
        if (busy_until and now<busy_until) or (unknown_at and now<unknown_at):
            s['reason']='POSITION_BUSY';continue
        cutoff=windows(date.fromisoformat(day))[0][0]+timedelta(hours=7)
        if entry>=cutoff:
            s['reason']='TRADE_DEADLINE';continue
        if entry>=s['window_end']-FIVE:
            s['reason']='SESSION_LIMIT';continue
        busy_until=entry
        if not good(raw.get(s['waiting_bar_start']),symbol,s['waiting_bar_start']):
            s['reason']='NO_WAITING_BAR';continue
        s.update(order_admitted=True,order_sent_at=entry)
        q={k:s[k] for k in ('signal_id','instrument','direction','signal_at','stop','window_end',
                           'waiting_bar_closed_at','order_sent_at','planned_execution_at')}
        q.update(entry_at=None,entry_price=None,take=None,risk=None,model_filled=False,
                 gross=None,gross_R=None,cost_c1=None,cost_R=None,net_c1=None,net_R_c1=None,
                 prior_unknown_requires_flat_assumption=prior)
        b=raw.get(entry)
        if b is None or not b[0].is_finite() or b[0]<=0 or b[0]%tick(symbol,entry):
            reason='MISSING_EXECUTION_BAR' if b is None else 'INVALID_EXECUTION_OPEN'
            s.update(status='UNKNOWN',reason=reason)
            q.update(status='UNKNOWN',exit_reason='UNKNOWN',unknown_reason=reason,
                unknown_detected_at=entry+FIVE,exit_price=None,exit_at=None,
                exit_interval_start=None,exit_interval_end=None,resolved_at=None)
            trades.append(q);unknown_at=entry;today=True;continue
        risk=s['direction']*(b[0]-s['stop']);step=tick(symbol,entry)
        if risk<=0:
            s.update(status='NONFILL',reason='INVALID_STOP_GEOMETRY');continue
        target=b[0]+s['direction']*D('1.5')*risk
        target=(target/step).to_integral_value(rounding=ROUND_CEILING if s['direction']==1 else ROUND_FLOOR)*step
        deadline=min(entry+timedelta(minutes=120),s['window_end']-FIVE,cutoff)
        q.update(entry_at=entry,entry_price=b[0],take=target,risk=risk,model_filled=True,entry_tick=step,
                 cost_entry_c1=step,trade_deadline_at=cutoff,effective_deadline_at=deadline)
        s.update(status='MODEL_FILLED',reason='',model_filled=True,entry_open=b[0],risk=risk,take=target)
        q.update(path(symbol,raw,q));trades.append(q)
        if q['status']=='UNKNOWN':
            unknown_at=q['unknown_effective_at'];today=True
        else:
            busy_until=q['resolved_at']
    return signals,trades


def distribution(rows):
    closed=[t for t in rows if t['status']=='CLOSED'];win=[t for t in closed if D(t['net_R_c1'])>0];loss=[t for t in closed if D(t['net_R_c1'])<0]
    def mean(items,key):
        return sum((D(x[key]) for x in items),D(0))/len(items) if items else None
    months={}
    for t in closed:
        label=t['signal_at'][:7];months[label]=months.get(label,D(0))+D(t['net_R_c1'])
    positives=[x for x in months.values() if x>0];wins=sorted((D(t['net_R_c1']) for t in win),reverse=True)
    # Preserve ledger order for Decimal(28) reductions, just as the base metric
    # oracle does; sorting before addition changes only the last decimal place.
    total_winners=sum((D(t['net_R_c1']) for t in win),D(0))
    return dict(unique_trade_days=len({t['signal_at'][:10] for t in closed}),
        average_winner_R=mean(win,'net_R_c1'),average_loser_R=mean(loss,'net_R_c1'),
        average_winner_price=mean(win,'net_c1'),average_loser_price=mean(loss,'net_c1'),
        active_months=len(months),positive_months=len(positives),negative_months=sum(x<0 for x in months.values()),
        zero_closed_economy_months=12-sum(x!=0 for x in months.values()),
        largest_winner_share_R=wins[0]/total_winners if wins else None,
        top_three_winners_share_R=sum(wins[:3],D(0))/total_winners if wins else None,
        largest_positive_month_share_R=max(positives)/sum(positives,D(0)) if positives else None,
        monthly_closed_Net_R=dict(sorted(months.items())))


def assessment(values,dist,complete,p):
    checks=dict(complete=complete,
        enough_sample=values['closed']>=p['minimum_closed_trades'] and dist['unique_trade_days']>=p['minimum_unique_trade_days'] and dist['active_months']>=p['minimum_active_months'],
        positive_expectancy=values['Expectancy_R'] is not None and values['Expectancy_R']>0,
        PF_goal_met=all(values[k] is not None and values[k]>=D(p[goal]) for k,goal in [('PF_C1_price','goal_PF_C1_price'),('PF_C1_R','goal_PF_C1_R')]),
        monthly_stability=dist['positive_months']>=p['minimum_positive_months'] and dist['positive_months']>=D(p['minimum_positive_active_month_fraction'])*dist['active_months'],
        concentration_acceptable=all(dist[k] is not None and dist[k]<=D(p[limit]) for k,limit in [('largest_winner_share_R','maximum_largest_winner_share'),('largest_positive_month_share_R','maximum_largest_positive_month_share')]))
    negative=values['Expectancy_R'] is not None and values['Expectancy_R']<=0
    status=('INCONCLUSIVE' if not complete else 'NO ECONOMIC BASELINE PASS' if negative else 'INCONCLUSIVE' if not checks['enough_sample'] or values['Expectancy_R'] is None else 'ECONOMICALLY_PROMISING_BASELINE' if all(checks.values()) else 'NO ECONOMIC BASELINE PASS')
    diagnosis=('NO ECONOMIC BASELINE PASS' if negative else 'INSUFFICIENT_EVIDENCE' if not checks['enough_sample'] else 'CONDITIONAL_CRITERIA_MET' if all(v for k,v in checks.items() if k!='complete') else 'POSITIVE_EXPECTANCY_BELOW_EVIDENCE_CRITERIA')
    return dict(status=status,economic_diagnostic=diagnosis,evidence_checks=checks)


def compare_metrics(actual,values,dist,label):
    count=0
    for key,value in values.items():
        assert_value(actual['conditional_closed_only_C1'][key],value,label+' '+key);count+=1
    for key,value in dist.items():
        if isinstance(value,dict):
            require(set(value)==set(actual['distribution'][key]),label+' MONTH_SET')
            for month,x in value.items():
                assert_value(actual['distribution'][key][month],x,label+' '+month);count+=1
        else:
            assert_value(actual['distribution'][key],value,label+' '+key);count+=1
    return count


def audit(root,output):
    cfg=json.loads(CONFIG.read_text())
    require(subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()==cfg['source_ref'],'SOURCE_HEAD')
    require(not subprocess.check_output(['git','-C',str(root),'status','--porcelain=v1','--untracked-files=all'],text=True).strip(),'SOURCE_CHANGED')
    frozen=subprocess.check_output(['git','-C',str(ROOT),'show',FREEZE+':'+str(CONFIG.relative_to(ROOT))])
    require(frozen==CONFIG.read_bytes(),'CONFIG_CHANGED_AFTER_FREEZE')
    archive=cfg['historical_selection']
    for path,digest in archive['files_sha256'].items():
        require(hashlib.sha256(subprocess.check_output(['git','-C',str(ROOT),'show',cfg['historical_reference']+':'+path])).hexdigest()==digest,'HISTORICAL_DOCUMENT '+path)
    provenance=json.loads((output/'provenance.json').read_text())
    require(provenance['config_freeze_commit']==FREEZE and provenance['config_sha256']==hashlib.sha256(frozen).hexdigest(),'FREEZE_PROVENANCE')
    for path,digest in provenance['code_sha256'].items():
        require(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,'CODE_HASH '+path)
    for path in [*(LAB/'core').glob('*.py'),LAB/'strategies/orb_breakout_retest.py']:
        text=path.read_text();tree=ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom):
                require(not (node.module or '').startswith('TradingSystemLab'),'PROTECTED_IMPORT')
        if path.parent.name=='core':
            require('R17' not in text and 'orb_breakout' not in text,'CANDIDATE_RULE_IN_CORE')
    raw,receipts=read_source(root,cfg)
    ss=read_csv(output/'signals.csv');tt=read_csv(output/'trades.csv');cc=read_csv(output/'coverage_daily.csv')
    metrics=json.loads((output/'metrics.json').read_text());details={};checked=coverage_checked=metric_checked=0
    signal_keys=('base_reason','direction','signal_at','breakout_start','breakout_closed_at','breakout_close',
        'breakout_atr14','breakout_tick','breakout_threshold','or_high','or_low','or_available_at',
        'signal_window_start','signal_window_end','retest_start','retest_closed_at','retest_tick','or_mid_rounded',
        'stop','status','reason','order_admitted','model_filled','entry_open','risk','take','recorded_at',
        'waiting_bar_start','waiting_bar_closed_at','planned_execution_at')
    trade_keys=('direction','signal_at','status','model_filled','entry_at','entry_price','entry_tick','stop','take','risk',
        'exit_reason','unknown_reason','exit_at','exit_interval_start','exit_interval_end','resolved_at',
        'unknown_detected_at','exit_price','exit_tick','gross','gross_R','cost_entry_c1','cost_c1','cost_R',
        'net_c1','net_R_c1','prior_unknown_requires_flat_assumption','order_sent_at','waiting_bar_closed_at',
        'planned_execution_at','trade_deadline_at','effective_deadline_at','stop_take_conflict')
    for symbol in cfg['instruments']:
        expected_s,expected_t=replay(symbol,raw[symbol],episodes(symbol,raw[symbol]))
        actual_s=[x for x in ss if x['instrument']==symbol];actual_t=[x for x in tt if x['instrument']==symbol]
        checked+=check_rows(actual_s,expected_s,signal_keys,'SIGNALS')
        checked+=check_rows(actual_t,expected_t,trade_keys,'TRADES')
        cov=[c for c in cc if c['instrument']==symbol];expected_dates=[];day=date(2023,1,1)
        while day.year==2023:
            ws=windows(day)
            if ws:
                expected_dates.append(str(day));actual=next(c for c in cov if c['date']==str(day));slots=[]
                if day>=min(raw[symbol]).date():
                    for a,z in ws:
                        while a<z:
                            slots.append(a);a+=FIVE
                missing=sum(at not in raw[symbol] for at in slots)
                invalid=sum(at in raw[symbol] and not good(raw[symbol][at],symbol,at) for at in slots)
                status='PRE_INCEPTION' if day<min(raw[symbol]).date() else 'INCOMPLETE' if missing or invalid else 'COMPLETE'
                or_ok=all(good(raw[symbol].get(ws[0][0]+i*FIVE),symbol,ws[0][0]+i*FIVE) for i in range(3))
                for k,v in dict(status=status,expected_bars=len(slots),valid_bars=len(slots)-missing-invalid,missing_bars=missing,invalid_bars=invalid,or_available=or_ok).items():
                    assert_value(actual[k],v,'COVERAGE '+symbol+' '+str(day)+' '+k);coverage_checked+=1
            day+=timedelta(days=1)
        require(sorted(c['date'] for c in cov)==expected_dates,'COVERAGE_DATES')
        values=metric(actual_t);dist=distribution(actual_t);m=metrics['instruments'][symbol]
        metric_checked+=compare_metrics(m,values,dist,'METRICS '+symbol)
        complete=all(c['status']=='COMPLETE' for c in cov) and not any(t['status']=='UNKNOWN' or t['prior_unknown_requires_flat_assumption']=='True' for t in actual_t)
        expected=assessment(values,dist,complete,cfg['classification_policy'])
        for k,v in expected.items():
            require(m[k]==v,'ASSESSMENT '+symbol+' '+k)
        require(m['annual_complete']==complete,'ANNUAL_COMPLETENESS')
        for k,v in m['annual'].items():
            assert_value(v,values[k] if complete else None,'ANNUAL '+symbol+' '+k)
        for k,v in dict(signals=sum(s['base_reason']=='SIGNAL' for s in actual_s),admitted_orders=sum(s['order_admitted']=='True' for s in actual_s),model_fills=sum(t['model_filled']=='True' for t in actual_t),closed=len([t for t in actual_t if t['status']=='CLOSED']),unknown=sum(t['status']=='UNKNOWN' for t in actual_t)).items():
            assert_value(m[k],v,'COUNTS '+symbol+' '+k)
        require(m['rejection_reasons']==dict(Counter(s['reason'] for s in actual_s if s['reason'])),'REJECTIONS')
        for t in actual_t:
            if t['status']=='UNKNOWN':
                require(all(t.get(k,'')=='' for k in ('exit_price','gross','gross_R','net_c1','net_R_c1','cost_c1')),'UNKNOWN_ECONOMICS_IMPUTED')
        details[symbol]=dict(signals=len(expected_s),trades=len(expected_t),metrics_from_csv=values,
                             distribution_from_csv=dist,assessment=expected)
    table_checked=0
    for filename in ('monthly_report.csv','instrument_report.csv','direction_report.csv'):
        rows=read_csv(output/filename)
        require(len(rows)==(48 if filename.startswith('monthly') else 8 if filename.startswith('direction') else 4),'REPORT_ROW_COUNT')
        if filename.startswith('monthly'):
            require({(r['instrument'],r['month']) for r in rows}=={(s,f'2023-{i:02d}') for s in cfg['instruments'] for i in range(1,13)},'ALL_TWELVE_MONTHS')
        for row in rows:
            cohort=[t for t in tt if t['instrument']==row['instrument']]
            if 'month' in row:
                cohort=[t for t in cohort if t['signal_at'].startswith(row['month'])]
            if 'direction' in row:
                cohort=[t for t in cohort if t['direction']==('1' if row['direction']=='LONG' else '-1')]
            for key,value in dict(metric(cohort),**distribution(cohort)).items():
                column='conditional_'+key
                if column not in row or isinstance(value,dict):
                    continue
                if row['coverage_classification']=='NO_COVERAGE' and key in ('PF_C1_price','PF_C1_R','Net_R','Expectancy_R','Win_Rate','Max_DD_R'):
                    value=None
                assert_value(row[column],value,filename+' '+row['instrument']+' '+column);table_checked+=1
    statuses=[v['assessment']['status'] for v in details.values()]
    expected_status='INCONCLUSIVE' if 'INCONCLUSIVE' in statuses else 'ECONOMICALLY_PROMISING_BASELINE' if all(s=='ECONOMICALLY_PROMISING_BASELINE' for s in statuses) else 'NO ECONOMIC BASELINE PASS'
    require(metrics['baseline_status']==expected_status and metrics['optimization_allowed'] is False,'OVERALL_STATUS')
    require(metrics['portfolio_money_return'] is None and metrics['portfolio_price_PF'] is None,'INVALID_PRICE_POOLING')
    result=dict(status='PASS',method=__doc__.strip(),checked_ledger_fields=checked,
        checked_coverage_fields=coverage_checked,checked_metric_fields=metric_checked,
        checked_report_metric_fields=table_checked,instruments=details,source_receipts=receipts,
        bytes_2024_plus_read=0,bytes_2025_plus_read=0,config_freeze_commit=FREEZE,
        baseline_status=expected_status,discrepancies=[],external_human_acceptance='Not claimed; independent PR review remains required')
    (output/'audit.json').write_text(json.dumps(result,default=str,sort_keys=True,indent=2)+'\n')
    (output/'Independent_Audit.md').write_text('# Independent implementation audit — R17 M5\n\n'
        'Status: **PASS**. No production engine, strategy, indicator, loader or metric imports.\n\n'
        f'Checked {checked} ledger fields, {coverage_checked} coverage fields, {metric_checked} instrument metric fields and {table_checked} report metric fields.\n\n'
        'Independent LF-budget source reading verifies exact pinned 2023 bytes. Batch first-onset/retest slices and a separate forward execution oracle verify ATR, OR, grid, waiting, Stop/Take, C1, deadlines, missing bars and UNKNOWN. CSV-only recalculation verifies economic and concentration metrics and computed classifications. All 12 months and both directions checked.\n\n'
        'The config equals the pre-P&L freeze commit. No 2024 or 2025+ price bytes read; no imputed UNKNOWN economics or pooled cross-instrument price returns.\n\n'
        'Detailed exact field checks are in audit.json; corruption guards and byte regression are in validation.json. This is implementation-independent verification by the task agent, not a second person or external reviewer signoff. Draft PR awaits independent review.\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-root',type=Path,required=True)
    p.add_argument('--output',type=Path,default=LAB/'results/r17_orb_breakout_retest_2023_m5_v1')
    a=p.parse_args();result=audit(a.data_root,a.output)
    print(json.dumps({k:result[k] for k in ('status','checked_ledger_fields','checked_coverage_fields','checked_metric_fields','checked_report_metric_fields')},sort_keys=True))
