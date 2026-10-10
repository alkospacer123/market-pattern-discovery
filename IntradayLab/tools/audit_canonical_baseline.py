#!/usr/bin/env python3
"""Independent raw-input/ledger oracle. Imports no engine/strategy/metrics code.

Batch episode slices and per-trade forward paths independently verify the
production streaming clock. Metrics are rebuilt exclusively from trades.csv.
This is implementation-independent verification, not a second person's signoff.
"""
import argparse
import ast
from collections import Counter
import csv
from datetime import date, datetime, timedelta
from decimal import Decimal as D, ROUND_CEILING, ROUND_FLOOR
import hashlib
import io
import json
from pathlib import Path
import subprocess
from zoneinfo import ZoneInfo

LAB=Path(__file__).resolve().parents[1]
CONFIG=LAB/'config/orb_a_base_2023_canonical_v1.json'
FIVE=timedelta(minutes=5)
ZONE=ZoneInfo('Europe/Moscow')
HOLIDAYS={(1,1),(1,2),(1,7),(2,23),(3,8),(5,1),(5,9),(6,12),(11,4)}


def require(condition,label):
    if not condition:
        raise AssertionError(label)


def windows(day):
    if day.weekday()>=5 or (day.month,day.day) in HOLIDAYS:
        return []
    def t(h,m=0):
        return datetime(day.year,day.month,day.day,h,m,tzinfo=ZONE)
    return [(t(10),t(14)),(t(14,15 if date(2023,3,13)<=day<date(2023,3,21) else 5),t(18,50))]


def tick(symbol,at):
    if symbol=='CNYRUBF':
        return D('.01') if at<datetime(2023,9,27,19,tzinfo=ZONE) else D('.001')
    return D({'USDRUBF':'.01','GLDRUBF':'.1','IMOEXF':'.5'}[symbol])


def good(row,symbol,at):
    if row is None:
        return False
    o,h,l,c,v=row
    return all(x.is_finite() for x in row) and 0<l<=min(o,c)<=max(o,c)<=h and v>0 and not any(x%tick(symbol,at) for x in row[:4])


def read_source(root,config):
    out={};receipts={}
    for symbol,spec in config['inputs'].items():
        # Independent LF-budget reader. The remaining LF count bounds every
        # unbuffered chunk, so it cannot consume even one future byte.
        chunks=[]; remaining=spec['rows_2023']+1
        with (root/spec['path']).open('rb',buffering=0) as stream:
            while remaining:
                block=stream.read(min(16384,remaining))
                require(bool(block),'TRUNCATED_SOURCE')
                remaining-=block.count(b'\n')
                chunks.append(block)
        raw=b''.join(chunks)
        require(len(raw)==spec['prefix_bytes'] and hashlib.sha256(raw).hexdigest()==spec['prefix_sha256'],'INDEPENDENT_PREFIX_HASH')
        records={};previous=None
        for row in csv.DictReader(io.StringIO(raw.decode('utf-8-sig')),delimiter=';'):
            at=datetime.fromisoformat(row['Datetime']).replace(tzinfo=ZONE)
            require(at.year==2023 and row['Ticker']==symbol,'INDEPENDENT_SCHEMA')
            require(previous is None or at>previous,'INDEPENDENT_ORDER')
            records[at]=tuple(D(row[k]) for k in ('Open','High','Low','Close','Volume'))
            previous=at
        require(len(records)==spec['rows_2023'],'INDEPENDENT_ROWS')
        out[symbol]=records
        receipts[symbol]={'bytes_read':len(raw),'bytes_2024_plus_read':0,'sha256':hashlib.sha256(raw).hexdigest()}
    return out,receipts


def episodes(symbol,raw):
    """Identify first-side candidates; verify reclaim using bounded raw slices."""
    output=[]; day=date(2023,1,1)
    while day.year==2023:
        ws=windows(day)
        if not ws or day<min(raw).date():
            day+=timedelta(days=1)
            continue
        origin=ws[0][0]
        opening=[raw.get(origin+i*FIVE) for i in range(3)]
        if not all(good(b,symbol,origin+i*FIVE) for i,b in enumerate(opening)):
            output.append(dict(signal_id=f'{symbol}_{day}_NO_OR',instrument=symbol,date=str(day),
                               base_reason='NO_OR',direction=0,signal_at=None,sweep_start=origin))
            day+=timedelta(days=1)
            continue
        high=max(b[1] for b in opening);low=min(b[2] for b in opening)
        used=set();pending_until=set()
        for a,z in ws:
            at=max(a,origin+3*FIVE)
            while at<z:
                b=raw.get(at)
                if not good(b,symbol,at):
                    pending_until.clear()
                    at+=FIVE
                    continue
                step=tick(symbol,at)
                up=b[1]>=high+step;down=b[2]<=low-step
                if up and down and (len(used)<2 or at in pending_until):
                    used={-1,1};pending_until.clear()
                    output.append(dict(signal_id=f'{symbol}_{day}_AMB_{at:%H%M}',instrument=symbol,
                        date=str(day),direction=0,sweep_start=at,signal_at=None,
                        base_reason='AMBIGUOUS_BOTH_SIDES',or_high=high,or_low=low))
                    at+=FIVE
                    continue
                pending_until.discard(at)
                for side,swept in ((-1,up),(1,down)):
                    if not swept or side in used:
                        continue
                    used.add(side)
                    rec=dict(signal_id=f'{symbol}_{day}_{side}_{at:%H%M}',instrument=symbol,date=str(day),
                        direction=side,sweep_start=at,sweep_closed_at=at+FIVE,signal_at=None,
                        or_high=high,or_low=low,or_available_at=origin+3*FIVE,
                        sweep_tick=step,sweep_size=b[1]-high if side<0 else low-b[2],
                        window_start=a,window_end=z)
                    def reclaimed(row,t):
                        return low<=row[3]<=high-2*tick(symbol,t) if side<0 else low+2*tick(symbol,t)<=row[3]<=high
                    extreme=b[1] if side<0 else b[2]
                    reclaim=at if reclaimed(b,at) else None
                    reason='SIGNAL' if reclaim else 'NO_RECLAIM'
                    if reclaim is None:
                        successor=at+FIVE
                        if successor>=z:
                            reason='NO_RECLAIM_WINDOW'
                        else:
                            following=raw.get(successor)
                            pending_until.add(successor)
                            if not good(following,symbol,successor):
                                reason='NO_RECLAIM_GAP'
                            elif following[1]>=high+tick(symbol,successor) and following[2]<=low-tick(symbol,successor):
                                reason='NO_RECLAIM_AMBIGUOUS'
                            else:
                                extreme=max(extreme,following[1]) if side<0 else min(extreme,following[2])
                                if reclaimed(following,successor):
                                    reclaim=successor;reason='SIGNAL'
                    rec['base_reason']=reason
                    if reclaim:
                        rec.update(signal_at=reclaim+FIVE,reclaim_start=reclaim,
                                   stop=extreme-side*step,target_gross_R='1.5',max_hold_calendar_minutes=60,
                                   waiting_bar_start=reclaim+FIVE,waiting_bar_closed_at=reclaim+2*FIVE,
                                   planned_execution_at=reclaim+2*FIVE)
                    output.append(rec)
                at+=FIVE
            pending_until.clear()
        day+=timedelta(days=1)
    return sorted(output,key=lambda e:(e.get('signal_at') or e['sweep_start']+FIVE,e['signal_id']))


def path(symbol,raw,q):
    """Forward trade path; precedence checked from explicit source observations."""
    entry=q['entry_at'];side=q['direction'];stop=q['stop'];target=q['take']
    deadline=min(entry+timedelta(minutes=60),q['window_end']-FIVE)
    at=entry
    while at<=deadline:
        b=raw.get(at)
        if b is None:
            return dict(status='UNKNOWN',exit_reason='UNKNOWN',unknown_reason='MISSING_EXPOSED_BAR',
                        unknown_detected_at=at+FIVE,unknown_effective_at=at,exit_price=None,
                        exit_at=None,exit_interval_start=None,exit_interval_end=None,resolved_at=None)
        op=b[0]
        open_ok=op.is_finite() and op>0 and not op%tick(symbol,at)
        if not open_ok:
            return dict(status='UNKNOWN',exit_reason='UNKNOWN',unknown_reason='INVALID_EXPOSED_OPEN',
                        unknown_detected_at=at+FIVE,unknown_effective_at=at,exit_price=None,
                        exit_at=None,exit_interval_start=None,exit_interval_end=None,resolved_at=None)
        gap=op<=stop if side>0 else op>=stop
        if gap or at==deadline:
            reason='STOP' if gap else 'TIME' if deadline==entry+timedelta(minutes=60) else 'SESSION_FLAT'
            price=op;point=True;conflict=False
        elif not good(b,symbol,at):
            return dict(status='UNKNOWN',exit_reason='UNKNOWN',unknown_reason='INVALID_EXPOSED_BAR',
                        unknown_detected_at=at+FIVE,unknown_effective_at=at+FIVE,exit_price=None,
                        exit_at=None,exit_interval_start=None,exit_interval_end=None,resolved_at=None)
        else:
            sh=b[2]<=stop if side>0 else b[1]>=stop
            th=b[1]>=target if side>0 else b[2]<=target
            if sh or (th and at!=entry):
                reason='STOP' if sh else 'TAKE';price=stop if sh else target
                point=False;conflict=sh and th
            else:
                at+=FIVE
                continue
        gross=side*(price-q['entry_price'])
        expense=tick(symbol,entry)+tick(symbol,at)
        return dict(status='CLOSED',exit_reason=reason,exit_price=price,
                    exit_at=at if point else None,exit_interval_start=at,
                    exit_interval_end=at if point else at+FIVE,resolved_at=at if point else at+FIVE,
                    gross=gross,gross_R=gross/q['risk'],cost_c1=expense,cost_R=expense/q['risk'],
                    net_c1=gross-expense,net_R_c1=(gross-expense)/q['risk'],stop_take_conflict=conflict)
    raise AssertionError('ORACLE_PATH')


def replay(symbol,raw,events):
    expected=[];trades=[];day=None;busy_until=None;unknown_at=None;prior_unknown=False;today_unknown=False
    for event in events:
        if day!=event['date']:
            prior_unknown|=today_unknown
            today_unknown=False;day=event['date'];busy_until=unknown_at=None
        s=dict(event,status='REJECTED',reason=event['base_reason'],order_admitted=False,model_filled=False)
        expected.append(s)
        if event['base_reason']!='SIGNAL':
            continue
        now=s['signal_at'];entry=s['planned_execution_at']
        if unknown_at and now>=unknown_at:
            s['reason']='UNKNOWN_POSITION_BLOCK';continue
        if (busy_until and now<busy_until) or (unknown_at and now<unknown_at):
            s['reason']='POSITION_BUSY';continue
        if entry>=s['window_end']-FIVE:
            s['reason']='SESSION_LIMIT';continue
        if not good(raw.get(s['waiting_bar_start']),symbol,s['waiting_bar_start']):
            s['reason']='NO_WAITING_BAR';continue
        s.update(order_admitted=True,order_sent_at=entry)
        q={k:s[k] for k in ('signal_id','instrument','direction','signal_at','sweep_start','reclaim_start',
                           'stop','window_end','waiting_bar_closed_at','order_sent_at','planned_execution_at')}
        q.update(entry_at=None,entry_price=None,take=None,risk=None,model_filled=False,
                 gross=None,gross_R=None,cost_c1=None,cost_R=None,net_c1=None,net_R_c1=None,
                 prior_unknown_requires_flat_assumption=prior_unknown)
        b=raw.get(entry)
        if b is None or not b[0].is_finite() or b[0]<=0 or b[0]%tick(symbol,entry):
            reason='MISSING_EXECUTION_BAR' if b is None else 'INVALID_EXECUTION_OPEN'
            s.update(status='UNKNOWN',reason=reason)
            q.update(status='UNKNOWN',exit_reason='UNKNOWN',unknown_reason=reason,
                     unknown_detected_at=entry+FIVE,exit_at=None,exit_interval_start=None,
                     exit_interval_end=None,exit_price=None,resolved_at=None)
            trades.append(q);unknown_at=entry;today_unknown=True;continue
        risk=s['direction']*(b[0]-s['stop'])
        step=tick(symbol,entry)
        if risk<=0:
            s.update(status='NONFILL',reason='INVALID_STOP_GEOMETRY')
            busy_until=entry
            continue
        take=b[0]+s['direction']*D('1.5')*risk
        take=(take/step).to_integral_value(rounding=ROUND_CEILING if s['direction']>0 else ROUND_FLOOR)*step
        q.update(entry_at=entry,entry_price=b[0],take=take,risk=risk,model_filled=True,cost_entry_c1=step)
        s.update(status='MODEL_FILLED',reason='',model_filled=True)
        result=path(symbol,raw,q)
        q.update(result);trades.append(q)
        if q['status']=='UNKNOWN':
            unknown_at=q['unknown_effective_at'];today_unknown=True
        else:
            busy_until=q['resolved_at']
    return expected,trades


def read_csv(path):
    with path.open() as stream:
        return list(csv.DictReader(stream))


def canonical(value):
    if value in ('',None):
        return None
    if isinstance(value,(datetime,date)):
        return str(value)
    if isinstance(value,(D,int,bool)):
        return str(value)
    if isinstance(value,str):
        try:
            return D(value)
        except Exception:
            return value
    return value


def assert_value(actual,expected,label):
    a,b=canonical(actual),canonical(expected)
    # Decimal numeric spellings may differ; values must be exactly equal.
    try:
        equal=D(str(a))==D(str(b)) if a is not None and b is not None else a==b
    except Exception:
        equal=a==b
    require(equal,f'{label}: actual={actual}, expected={expected}')


def check_rows(actual,expected,keys,label):
    aa={r['signal_id']:r for r in actual};bb={r['signal_id']:r for r in expected}
    require(len(aa)==len(actual) and set(aa)==set(bb),label+' ROW_SET')
    count=0
    for sid in sorted(aa):
        for key in keys:
            assert_value(aa[sid].get(key),bb[sid].get(key),f'{label} {sid} {key}')
            count+=1
    return count


def metric(rows):
    closed=sorted((r for r in rows if r['status']=='CLOSED'),key=lambda r:(r['resolved_at'],r['signal_id']))
    r=[D(x['net_R_c1']) for x in closed];p=[D(x['net_c1']) for x in closed]
    def ratio(values):
        gain=sum([v for v in values if v>0],D(0))
        loss=sum([-v for v in values if v<0],D(0))
        return gain/loss if loss else None
    levels=[D(0)]
    for value in r:
        levels.append(levels[-1]+value)
    dd=max((max(levels[:i+1])-v for i,v in enumerate(levels)),default=D(0))
    return dict(closed=len(r),PF_C1_price=ratio(p),PF_C1_R=ratio(r),
                Net_R=sum(r,D(0)),Net_price=sum(p,D(0)),
                Expectancy_R=sum(r,D(0))/len(r) if r else None,
                Win_Rate=D(sum(v>0 for v in r))/len(r) if r else None,
                Max_DD_R=dd if r else None,cost_C1=sum([D(x['cost_c1']) for x in closed],D(0)))


def audit(root,output):
    cfg=json.loads(CONFIG.read_text())
    require(subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()==cfg['source_ref'],'SOURCE_HEAD')
    require(not subprocess.check_output(['git','-C',str(root),'status','--porcelain=v1','--untracked-files=all'],text=True).strip(),'SOURCE_CHANGED')
    historical=json.loads(subprocess.check_output(['git','-C',str(LAB.parent),'show',cfg['historical_reference']+':IntradayLab/config/stage2_orb_false_break_fade_m5_v1.json']))
    for key,value in cfg['parameters'].items():
        require(value==historical['parameters'][key],'FROZEN_PARAMETERS '+key)
    require(cfg['inputs']==historical['inputs'],'FROZEN_INPUTS')
    require(cfg['execution']=={'allow_entry_bar_take':False,'cost_ticks_per_side':1,'session_flat_before_end_bars':1,'unknown_scope':'current_day; following days conditional FLAT','wait_complete_bars':1},'FROZEN_EXECUTION')
    provenance=json.loads((output/'provenance.json').read_text())
    for path,digest in provenance['code_sha256'].items():
        require(hashlib.sha256((LAB.parent/path).read_bytes()).hexdigest()==digest,'CODE_HASH '+path)
    for file in [*(LAB/'core').glob('*.py'),*(LAB/'strategies').glob('*.py')]:
        content=file.read_text();tree=ast.parse(content)
        require('TradingSystemLab' not in content,'PROTECTED_IMPORT '+str(file))
        if file.parent.name=='core':
            require('ORB' not in content and 'orb_false_break' not in content,'STRATEGY_IN_CORE '+str(file))
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom):
                require(not (node.module or '').startswith('TradingSystemLab'),'IMPORT')
    raw,receipts=read_source(root,cfg)
    signals=read_csv(output/'signals.csv');trades=read_csv(output/'trades.csv')
    coverage=read_csv(output/'coverage_daily.csv');metrics=json.loads((output/'metrics.json').read_text())
    checked=0;coverage_checked=0;instrument_details={}
    signal_keys=('base_reason','direction','sweep_start','sweep_closed_at','signal_at','stop',
                 'or_high','or_low','or_available_at','sweep_size','sweep_tick','reclaim_start',
                 'status','reason','order_admitted','model_filled')
    trade_keys=('direction','signal_at','sweep_start','reclaim_start','status','model_filled',
                'entry_at','entry_price','stop','take','risk','exit_reason','unknown_reason',
                'exit_at','exit_interval_start','exit_interval_end','resolved_at','unknown_detected_at',
                'exit_price','gross','gross_R','cost_entry_c1','cost_c1','cost_R','net_c1','net_R_c1',
                'prior_unknown_requires_flat_assumption','order_sent_at','waiting_bar_closed_at','planned_execution_at')
    for symbol in cfg['instruments']:
        events=episodes(symbol,raw[symbol]);ss,tt=replay(symbol,raw[symbol],events)
        actual_s=[s for s in signals if s['instrument']==symbol]
        actual_t=[t for t in trades if t['instrument']==symbol]
        checked+=check_rows(actual_s,ss,signal_keys,'SIGNALS')
        checked+=check_rows(actual_t,tt,trade_keys,'TRADES')
        cov=[r for r in coverage if r['instrument']==symbol]
        day=date(2023,1,1);expected_dates=[]
        while day.year==2023:
            ws=windows(day)
            if ws:
                expected_dates.append(str(day))
                actual=next(r for r in cov if r['date']==str(day))
                slots=[]
                if day>=min(raw[symbol]).date():
                    for a,z in ws:
                        while a<z:
                            slots.append(a);a+=FIVE
                absent=sum(t not in raw[symbol] for t in slots)
                invalid=sum(t in raw[symbol] and not good(raw[symbol][t],symbol,t) for t in slots)
                status='PRE_INCEPTION' if day<min(raw[symbol]).date() else 'INCOMPLETE' if absent or invalid else 'COMPLETE'
                for key,value in dict(status=status,expected_bars=len(slots),valid_bars=len(slots)-absent-invalid,missing_bars=absent,invalid_bars=invalid).items():
                    assert_value(actual[key],value,f'COVERAGE {symbol} {day} {key}');coverage_checked+=1
            day+=timedelta(days=1)
        require(sorted(r['date'] for r in cov)==expected_dates,'COVERAGE_DATES')
        recalculated=metric(actual_t)
        for key,value in recalculated.items():
            assert_value(metrics['instruments'][symbol]['conditional_closed_only_C1'][key],value,'METRICS '+symbol+' '+key)
        m=metrics['instruments'][symbol]
        require(m['signals']==sum(s['base_reason']=='SIGNAL' for s in actual_s),'SIGNAL_COUNT')
        require(m['admitted_orders']==sum(s['order_admitted']=='True' for s in actual_s),'ORDER_COUNT')
        require(m['unknown']==sum(t['status']=='UNKNOWN' for t in actual_t),'UNKNOWN_COUNT')
        require(m['rejection_reasons']==dict(Counter(s['reason'] for s in actual_s if s['reason'])),'REJECTION_COUNT')
        if any(t['status']=='UNKNOWN' for t in actual_t) or any(c['status']!='COMPLETE' for c in cov):
            require(not m['annual_complete'] and all(v is None for v in m['annual'].values()),'INVALID_ANNUAL_CLAIM')
        instrument_details[symbol]=dict(signals=len(ss),trades=len(tt),metrics_from_csv=recalculated,
                                       unknown=m['unknown'],complete_days=sum(c['status']=='COMPLETE' for c in cov))
    table_checks=0
    for filename in ('monthly_report.csv','instrument_report.csv','direction_report.csv'):
        report=read_csv(output/filename)
        require(len(report)==(48 if filename.startswith('monthly') else 8 if filename.startswith('direction') else 4),'REPORT_ROW_COUNT')
        for row in report:
            cohort=[t for t in trades if t['instrument']==row['instrument']]
            if 'month' in row:
                cohort=[t for t in cohort if t['signal_at'].startswith(row['month'])]
            if 'direction' in row:
                side='1' if row['direction']=='LONG' else '-1'
                cohort=[t for t in cohort if t['direction']==side]
            for key,value in metric(cohort).items():
                if 'conditional_'+key in row:
                    if row['coverage_classification']=='NO_COVERAGE':
                        value=None
                    assert_value(row['conditional_'+key],value,filename+' '+key)
                    table_checks+=1
    history=json.loads((output/'historical_comparison.json').read_text())
    require(history['status']=='PASS' and not history['discrepancies'],'HISTORICAL_COMPLETE_DAYS')
    result=dict(status='PASS',method='Independent LF-budget source reader, batch episode slices, forward trade paths, independent metrics from trades.csv; no production imports',
                checked_ledger_fields=checked,checked_coverage_fields=coverage_checked,
                checked_report_metric_fields=table_checks,instruments=instrument_details,
                source_receipts=receipts,bytes_2024_plus_read=0,bytes_2025_plus_read=0,
                historical_complete_days=history['complete_days'],historical_complete_day_trades=history['complete_day_trades'],
                discrepancies=[],external_human_acceptance='Not claimed; this is an independent implementation audit')
    (output/'audit.json').write_text(json.dumps(result,default=str,indent=2,sort_keys=True)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-root',type=Path,required=True)
    p.add_argument('--output',type=Path,default=LAB/'results/orb_a_base_2023_canonical_v1')
    a=p.parse_args()
    result=audit(a.data_root,a.output)
    print(json.dumps({k:result[k] for k in ('status','checked_ledger_fields','checked_coverage_fields','checked_report_metric_fields')},sort_keys=True))
