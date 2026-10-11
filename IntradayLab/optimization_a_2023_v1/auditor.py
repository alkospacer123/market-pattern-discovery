"""Independent raw-slice signal/path, metrics and selection auditor.

Standard library only. Does not import strategy, Backtester, execution, loader,
optimizer metrics, selection or any other IntradayLab module.
"""
import argparse
import ast
from collections import Counter
import csv
from datetime import date, datetime, timedelta
from decimal import Decimal as D, ROUND_CEILING, ROUND_FLOOR, localcontext
import hashlib
import io
import json
from pathlib import Path
import subprocess
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[2]
STUDY=Path(__file__).resolve().parent
FIVE=timedelta(minutes=5)
ZONE=ZoneInfo('Europe/Moscow')
HOLIDAYS={(1,1),(1,2),(1,7),(2,23),(3,8),(5,1),(5,9),(6,12),(11,4)}
NA='NOT_AVAILABLE'
EPS=D('1e-20')
MONTHS=[f'2023-{m:02d}' for m in range(1,13)]

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

def episodes(symbol, raw, parameters, start=date(2023,1,1), end=date(2024,1,1)):
    """Scan exact three-bar slices and recover maximal runs backwards.

    Backward reconstruction differs from the production streaming counters.
    A consumed run stays consumed even if its admission or fill fails.
    """
    output=[];day=start;first=min(raw).date()
    while day<end:
        for a,z in windows(day) if day>=first else []:
            consumed=set();at=a
            while at<z:
                row=raw.get(at)
                if not good(row,symbol,at):
                    at+=FIVE;continue
                candidates=[]
                for side,index in ((-1,1),(1,2)):
                    times=[at-i*FIVE for i in reversed(range(parameters['touches']))]
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
                        signal_tick=tick(symbol,at),touch_count=parameters['touches'],
                        signal_close=row[3],stop=level-side*tick(symbol,at)*parameters['stop_buffer_ticks'],
                        target_gross_R=parameters['target_net_R'],target_net_R=parameters['target_net_R'],target_mode='FULL_NET_C1_R',
                        max_hold_calendar_minutes=120,recorded_at=at+FIVE,
                        window_start=a,window_end=z))
                for c in candidates:
                    for i,t in enumerate(times,1):
                        c[f'touch_{i}_start']=t
                        c[f'touch_{i}_extreme']=c['cluster_level']
                reason='AMBIGUOUS_BOTH_SIDES' if len(candidates)==2 else 'SIGNAL'
                # The production engine supplies windows only to SIGNAL intents.
                for c in candidates:
                    if reason!='SIGNAL':
                        c.pop('window_start');c.pop('window_end')
                    output.append(dict(c,base_reason=reason))
                at+=FIVE
        day+=timedelta(days=1)
    return sorted(output,key=lambda e:(e['signal_at'],e['signal_id']))

def path(symbol,raw,q,legacy=False):
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
            if not legacy:
                return dict(status='DATA_QUALITY_EXCLUDED',exit_reason=None,exclusion_reason=unknown,
                    gap_interval_start=at,gap_interval_end=at+FIVE,gap_detected_at=effective,
                    unknown_effective_at=effective,remainder_of_day_blocked=True,
                    exit_price=None,exit_at=None,exit_interval_start=None,exit_interval_end=None,
                    resolved_at=None,stop_take_conflict=False)
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

def replay(symbol,raw,events,parameters,legacy=False):
    close_oracle=False; skips=[];exclusions=[]
    ss=[];tt=[];day=None;busy_until=unknown_at=None;prior=today=False
    for event in events:
        if event['date']!=day:
            prior|=today;today=False;day=event['date'];busy_until=unknown_at=None
        s=dict(event,status='REJECTED',reason=event['base_reason'],order_admitted=False,model_filled=False)
        s.update(initial_flat_assumed=True,initial_flat_proven=False,
            prior_unknown_requires_flat_assumption=prior)
        if not legacy:
            s.pop('prior_unknown_requires_flat_assumption');s['prior_exclusion_requires_flat_assumption']=prior
        ss.append(s)
        if s['base_reason']!='SIGNAL':
            continue
        entry=s['signal_at'];side=s['direction'];level=s['cluster_level'];step=tick(symbol,entry)
        s.update(entry_mode='ENTRY_CLOSE_ORACLE' if close_oracle else 'ENTRY_NEXT_OPEN',
            waiting_bar_start=None,waiting_bar_closed_at=None,planned_execution_at=entry,
            pending_created=False,open_admission_passed=None)
        if unknown_at is not None and entry>=unknown_at:
            s['reason']='UNKNOWN_POSITION_BLOCK' if legacy else 'DATA_QUALITY_POSITION_BLOCK';continue
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
        if not legacy:
            q.pop('prior_unknown_requires_flat_assumption');q['prior_exclusion_requires_flat_assumption']=prior
        op=s['signal_close'] if close_oracle else raw[entry][0] if entry in raw else None
        if op is None or not op.is_finite() or op<=0 or op%step:
            reason='MISSING_EXECUTION_BAR' if op is None else 'INVALID_EXECUTION_OPEN'
            if not legacy:
                s.update(status='DATA_GAP_SKIP',reason=reason,order_admitted=False,order_sent_at=None,
                    attempted_execution_at=entry,gap_detected_at=entry)
                skips.append(dict(s));continue
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
        ratio=D(parameters['target_net_R'])
        target=op+side*(ratio*(risk+2*step)+2*step)
        target=(target/step).to_integral_value(rounding=ROUND_CEILING if side==1 else ROUND_FLOOR)*step
        s.update(status='MODEL_FILLED',reason='',model_filled=True,risk=risk,take=target)
        q.update(entry_at=entry,entry_price=op,entry_tick=step,cost_entry_c1=step,
            model_filled=True,risk=risk,take=target,target_mode='FULL_NET_C1_R',target_net_R=ratio,
            planned_C1=2*step,d_legacy=ratio*risk+2*step,d_full=ratio*(risk+2*step)+2*step,
            rounded_take_distance=side*(target-op),planned_net_to_net_R=(side*(target-op)-2*step)/(risk+2*step),
            legacy_net_to_gross_R=ratio,realized_net_to_net_R=None)
        s.update({k:q[k] for k in ('target_mode','target_net_R','planned_C1','d_legacy','d_full',
            'rounded_take_distance','planned_net_to_net_R','legacy_net_to_gross_R','realized_net_to_net_R')})
        result=path(symbol,raw,q,legacy=legacy)
        q.update(result)
        if q['status']=='DATA_QUALITY_EXCLUDED':
            for k in ('gross','gross_R','cost_c1','cost_R','net_c1','net_R_c1','realized_net_to_net_R'):
                q.pop(k,None)
            exclusions.append(q);unknown_at=q['unknown_effective_at'];today=True
        else:
            tt.append(q)
        if q['status']=='UNKNOWN':
            unknown_at=q['unknown_effective_at'];today=True
        elif q['status']=='CLOSED':
            busy_until=q['resolved_at']
    return ss,tt,skips,exclusions


def independent_statistics(records):
    """Rebuild using gain/loss partitions and prefix equity, never optimizer code."""
    with localcontext() as ctx:
        ctx.prec=50
        ts=sorted(records,key=lambda t:(t['resolved_at'],t['signal_id']))
        rs=[D(t['net_R_c1']) for t in ts];prices=[D(t['net_c1']) for t in ts]
        rw=[v for v in rs if v>0];rl=[v for v in rs if v<0]
        pw=[v for v in prices if v>0];pl=[v for v in prices if v<0]
        total=sum(rs,D(0));gain=sum(rw,D(0));loss=sum(rl,D(0))
        pgain=sum(pw,D(0));ploss=sum(pl,D(0))
        levels=[D(0)]
        for r in rs: levels.append(levels[-1]+r)
        peak=D(0);drawdown=D(0)
        for level in levels:
            peak=max(peak,level);drawdown=max(drawdown,peak-level)
        exit_totals=[]
        for month in MONTHS:
            value=sum((D(t['net_R_c1']) for t in ts if str(t['exit_at'] or t['exit_interval_start'])[:7]==month),D(0))
            exit_totals.append(D(0) if abs(value)<=EPS else value)
        positives=[v for v in exit_totals if v>0]
        average=lambda v:sum(v,D(0))/len(v) if v else NA
        return dict(CLOSED=len(ts),entry_days=len({str(t['entry_at'])[:10] for t in ts}),
            entry_months=len({str(t['entry_at'])[:7] for t in ts}),Net_R=total,
            Net_price=sum(prices,D(0)),PF_R=-gain/loss if loss else NA,
            PF_price=-pgain/ploss if ploss else NA,
            PF_unavailable_reason='NO_NEGATIVE_CLOSED_PNL' if not rl else '',
            expectancy_R=total/len(ts) if ts else NA,win_rate=D(len(rw))/len(ts) if ts else NA,
            average_winner_R=average(rw),average_loser_R=average(rl),
            average_winner_price=average(pw),average_loser_price=average(pl),
            conditional_closed_only_DD_R=drawdown if ts else NA,
            positive_exit_months=len(positives),negative_exit_months=sum(v<0 for v in exit_totals),
            zero_exit_months=sum(v==0 for v in exit_totals),ideal_12_positive_months=len(positives)==12,
            largest_winner_share_R=max(rw)/gain if gain else NA,
            largest_positive_month_share_R=max(positives)/sum(positives,D(0)) if positives else NA,
            gross_price=sum((D(t['gross']) for t in ts),D(0)),C1_price=sum((D(t['cost_c1']) for t in ts),D(0)),
            gross_R=sum((D(t['gross_R']) for t in ts),D(0)),C1_R=sum((D(t['cost_R']) for t in ts),D(0)))


def independent_checks(m):
    valid=lambda v:v!=NA
    return dict(pass_sample=m['CLOSED']>=100 and m['entry_days']>=40 and m['entry_months']>=6,
        pass_PF_R=valid(m['PF_R']) and m['PF_R']>=2,
        pass_PF_price=valid(m['PF_price']) and m['PF_price']>=2,
        pass_positive_expectancy=valid(m['expectancy_R']) and m['expectancy_R']>0,
        pass_months=m['positive_exit_months']>=9,
        pass_conditional_DD=valid(m['conditional_closed_only_DD_R']) and m['conditional_closed_only_DD_R']<=20,
        pass_trade_concentration=valid(m['largest_winner_share_R']) and m['largest_winner_share_R']<=D('.25'),
        pass_month_concentration=valid(m['largest_positive_month_share_R']) and m['largest_positive_month_share_R']<=D('.50'))


def numeric_equal(actual,expected,label):
    # Exact trade/path checks use assert_value; aggregation permits registry tolerance.
    try:
        if abs(D(str(actual))-D(str(expected)))<=EPS: return
    except Exception: pass
    assert_value(actual,expected,label)


def independent_coverage(symbol,raw,signals,closed,skips,excluded):
    output=[];day=date(2023,1,1);first=min(raw).date();prior=False
    while day.year==2023:
        slots=[]
        for a,z in windows(day):
            while a<z:slots.append(a);a+=FIVE
        if slots:
            stamp=str(day)
            missing=sum(t not in raw for t in slots)
            invalid=sum(t in raw and not good(raw[t],symbol,t) for t in slots)
            dex=[e for e in excluded if str(e['entry_at'])[:10]==stamp]
            output.append(dict(instrument=symbol,date=stamp,status='PRE_INCEPTION' if day<first else
                'INCOMPLETE' if missing or invalid else 'COMPLETE',expected_bars=len(slots),
                valid_bars=len(slots)-missing-invalid,missing_bars=missing,invalid_bars=invalid,
                accepted_entries=sum(s['model_filled'] for s in signals if s['date']==stamp),
                closed=sum(str(t['entry_at'])[:10]==stamp for t in closed),
                data_gap_skips=sum(s['date']==stamp for s in skips),data_quality_excluded=len(dex),
                initial_flat_assumed=True,initial_flat_proven=False,
                prior_exclusion_requires_flat_assumption=prior,remainder_of_day_blocked=bool(dex)))
            prior|=bool(dex)
        day+=timedelta(days=1)
    return output


def write_csv(path,rows):
    with path.open('w',newline='') as f:
        columns=sorted({k for r in rows for k in r})
        w=csv.DictWriter(f,fieldnames=columns,lineterminator='\n');w.writeheader();w.writerows(rows)


def write_json(path,obj):
    path.write_text(json.dumps(obj,indent=2,sort_keys=True,default=str)+'\n')


def audit(data_root,output):
    policy=json.loads((STUDY/'OPTIMIZATION_A_POLICY.json').read_text())
    commitments=json.loads((STUDY/'source_commitments.json').read_text())
    for name,sha in commitments['dependencies_sha256'].items():
        require(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha,'AUDITOR_FREEZE '+name)
    require(policy['instruments']==['USDRUBF','CNYRUBF'],'TWO_INSTRUMENTS_ONLY')
    require(subprocess.check_output(['git','-C',str(data_root),'rev-parse','HEAD'],text=True).strip()==policy['source_ref'],'SOURCE_HEAD')
    for symbol,spec in policy['inputs'].items():
        blob=subprocess.check_output(['git','-C',str(data_root),'rev-parse',policy['source_ref']+':'+spec['path']],text=True).strip()
        require(blob==spec['blob'],'SOURCE_BLOB')
    for node in ast.walk(ast.parse(Path(__file__).read_text())):
        if isinstance(node,(ast.Import,ast.ImportFrom)):
            modules=[x.name for x in node.names] if isinstance(node,ast.Import) else [node.module or '']
            require(all(not m.startswith('IntradayLab') and m not in ('aggregation','runner','contract') for m in modules),'STANDARD_LIBRARY_ONLY_AUDITOR')
    raw,reads=read_source(data_root,policy)
    specs=[]
    for t in range(2,6):
        for sb in (1,2):
            for target in range(2,11):
                specs.append(dict(policy['parameters'],touches=t,stop_buffer_ticks=sb,target_net_R=str(target),
                    configuration_id=f'A_OPT2023_T{t}_SB{sb}_TP{target}'))
    frozen_grid=read_csv(STUDY/'GRID.csv')
    require(frozen_grid==[{k:str(v) for k,v in s.items()} for s in specs],'INDEPENDENT_72_GRID')
    actual_candidates=read_csv(output/'all_candidates.csv')
    actual_months=read_csv(output/'monthly_results.csv');actual_direction=read_csv(output/'direction_results.csv')
    actual_funnel=read_csv(output/'execution_funnel.csv')
    require(len(actual_candidates)==144 and len(actual_months)==1728 and len(actual_direction)==288 and len(actual_funnel)==144,'FULL_REPORT_ROW_COUNTS')
    candidates={(r['configuration_id'],r['instrument']):r for r in actual_candidates}
    require(len(candidates)==144,'NO_DUPLICATE_CANDIDATES')
    expected_metrics={};counts=Counter();comparator=[]
    for spec in specs:
        ident=spec['configuration_id']
        for symbol in policy['instruments']:
            folder=output/'evaluations'/ident/symbol
            expected_s,expected_t,expected_skip,expected_ex=replay(symbol,raw[symbol],episodes(symbol,raw[symbol],spec),spec)
            for filename,wanted in [('signals',expected_s),('trades',expected_t),('data_gap_skips',expected_skip),('data_quality_exclusions',expected_ex)]:
                actual=read_csv(folder/(filename+'.csv'))
                keys=sorted({k for r in wanted for k in r if k!='unknown_effective_at'})
                counts[filename+'_fields']+=check_rows(actual,wanted,keys,ident+' '+symbol+' '+filename)
                require(all(r.get('status')!='UNKNOWN' for r in actual),'V2_NO_UNKNOWN')
                if filename=='data_quality_exclusions':
                    require(all(not r.get(k) for r in actual for k in ('exit_price','exit_at','resolved_at','net_c1','net_R_c1','gross','cost_c1')),'NO_EXCLUDED_PNL')
            fills={s['signal_id'] for s in expected_s if s['model_filled']}
            require(fills=={t['signal_id'] for t in expected_t}|{t['signal_id'] for t in expected_ex},'ACCEPTED_ID_RECONCILIATION')
            counts['accepted_ID_checks']+=len(fills)
            rejected=read_csv(folder/'rejected_nonfill.csv')
            require({s['signal_id'] for s in rejected}=={s['signal_id'] for s in expected_s if s['status'] in ('REJECTED','NONFILL')},'REJECTED_NONFILL_IDS')
            cov=independent_coverage(symbol,raw[symbol],expected_s,expected_t,expected_skip,expected_ex)
            actual_cov=read_csv(folder/'coverage_report.csv')
            require(len(cov)==len(actual_cov),'COVERAGE_SIZE')
            for actual,wanted in zip(actual_cov,cov):
                for k,v in wanted.items():assert_value(actual[k],v,'COVERAGE '+k);counts['coverage_fields']+=1
            m=independent_statistics(expected_t)
            m.update(independent_checks(m));expected_metrics[(ident,symbol)]=m
            row=candidates[(ident,symbol)]
            for k,v in m.items():numeric_equal(row[k],v,'CANDIDATE '+ident+' '+symbol+' '+k);counts['metric_fields']+=1
            for k,v in spec.items():assert_value(row[k],v,'CONFIG '+k)
            require(row['source_sha']==policy['source_ref'],'CANDIDATE_SOURCE_SHA')
            require(row['strategy_sha256']==hashlib.sha256((ROOT/'IntradayLab/strategies/equal_high_low_m5_optimization_a_v1.py').read_bytes()).hexdigest(),'CANDIDATE_CODE_SHA')
            config=json.loads((folder/'configuration.json').read_text())
            require(config['parameters']=={k:v for k,v in spec.items() if k!='configuration_id'},'EVALUATION_PARAMETERS')
            require(config['source_sha']==policy['source_ref'] and config['source_blob']==policy['inputs'][symbol]['blob'] and config['execution']==policy['execution'],'EVALUATION_SOURCE_EXECUTION')
            for k,v in dict(accepted_entries=len(fills),DATA_GAP_SKIP=len(expected_skip),DATA_QUALITY_EXCLUDED=len(expected_ex),
                conditional_flat_CLOSED=sum(bool(t['prior_exclusion_requires_flat_assumption']) for t in expected_t),
                complete_coverage_days=sum(c['status']=='COMPLETE' for c in cov),incomplete_coverage_days=sum(c['status']=='INCOMPLETE' for c in cov)).items():
                assert_value(row[k],v,'CANDIDATE_COUNT '+k);counts['metric_fields']+=1
            with localcontext() as ctx:
                ctx.prec=50
                numeric_equal(row['exclusion_fraction'],D(len(expected_ex))/len(fills) if fills else NA,'EXCLUSION_FRACTION')
                attempts=len(fills)+len(expected_skip)
                numeric_equal(row['skip_fraction_of_fills_and_skips'],D(len(expected_skip))/attempts if attempts else NA,'SKIP_FRACTION')
            common=json.loads((folder/'metrics.json').read_text())
            cm=common['instruments'][symbol]
            for k,v in dict(accepted_entries=len(fills),closed=len(expected_t),data_gap_skips=len(expected_skip),data_quality_excluded=len(expected_ex),
                coverage_complete=all(c['status']=='COMPLETE' for c in cov),conditional_flat_closed=sum(bool(t['prior_exclusion_requires_flat_assumption']) for t in expected_t)).items():
                assert_value(cm[k],v,'COMMON_METRIC '+k);counts['metric_fields']+=1
            econ=cm['conditional_closed_only_C1']
            for ck,mk in [('closed','CLOSED'),('PF_C1_R','PF_R'),('PF_C1_price','PF_price'),('Net_R','Net_R'),('Net_price','Net_price'),
                ('Expectancy_R','expectancy_R'),('Win_Rate','win_rate'),('Max_DD_R','conditional_closed_only_DD_R'),('cost_C1','C1_price')]:
                numeric_equal(econ[ck],None if m[mk]==NA else m[mk],'COMMON_ECON '+ck);counts['metric_fields']+=1
            require(econ['exit_reasons']==dict(Counter(t['exit_reason'] for t in expected_t)),'COMMON_EXIT_REASONS')
            require(common['annual_account_returns'] is None and common['annual_economics'] is None and common['pooled_price_portfolio'] is None,'NO_ANNUAL_OR_PORTFOLIO_CLAIM')
            for monthly in [r for r in actual_months if r['configuration_id']==ident and r['instrument']==symbol]:
                month=monthly['month'];require(month in MONTHS,'MONTH_2023_ONLY')
                cohort=[t for t in expected_t if str(t['exit_at'] or t['exit_interval_start'])[:7]==month]
                for k,v in independent_statistics(cohort).items():numeric_equal(monthly[k],v,'MONTH '+k);counts['monthly_fields']+=1
                mc=[c for c in cov if c['date'][:7]==month]
                for k,v in dict(complete_days=sum(c['status']=='COMPLETE' for c in mc),incomplete_days=sum(c['status']=='INCOMPLETE' for c in mc),
                    valid_bars=sum(c['valid_bars'] for c in mc),missing_bars=sum(c['missing_bars'] for c in mc),invalid_bars=sum(c['invalid_bars'] for c in mc),
                    accepted_entries=sum(c['accepted_entries'] for c in mc),DATA_GAP_SKIP=sum(c['data_gap_skips'] for c in mc),DATA_QUALITY_EXCLUDED=sum(c['data_quality_excluded'] for c in mc)).items():
                    assert_value(monthly[k],v,'MONTH_COVERAGE '+k);counts['monthly_fields']+=1
            for directional in [r for r in actual_direction if r['configuration_id']==ident and r['instrument']==symbol]:
                side=1 if directional['direction']=='LONG' else -1
                for k,v in independent_statistics([t for t in expected_t if t['direction']==side]).items():numeric_equal(directional[k],v,'DIRECTION '+k);counts['direction_fields']+=1
                assert_value(directional['DATA_GAP_SKIP'],sum(s['direction']==side for s in expected_skip),'DIRECTION_SKIP')
                assert_value(directional['DATA_QUALITY_EXCLUDED'],sum(t['direction']==side for t in expected_ex),'DIRECTION_EXCLUDED')
            funnel=next(r for r in actual_funnel if r['configuration_id']==ident and r['instrument']==symbol)
            wanted=dict(raw_directional_events=len(expected_s),signals=sum(s['base_reason']=='SIGNAL' for s in expected_s),
                ambiguous_directional_events=sum(s['base_reason']!='SIGNAL' for s in expected_s),admissions=sum(s['order_admitted'] for s in expected_s),
                rejects=sum(s['base_reason']=='SIGNAL' and s['status']=='REJECTED' for s in expected_s),nonfills=sum(s['status']=='NONFILL' for s in expected_s),
                fills=len(fills),SKIP=len(expected_skip),EXCLUDED=len(expected_ex),CLOSED=len(expected_t))
            for k,v in wanted.items():assert_value(funnel[k],v,'FUNNEL '+k);counts['funnel_fields']+=1
            require(json.loads(funnel['reason_counts'])==dict(Counter(s['reason'] for s in expected_s if s['reason'])),'FUNNEL_REASON_COUNTS')
            if ident=='A_OPT2023_T3_SB1_TP3':
                legacy_s,legacy_t,_,_=replay(symbol,raw[symbol],episodes(symbol,raw[symbol],spec),spec,legacy=True)
                old=ROOT/'IntradayLab/results/equal_high_low_m5_2023_a_v1'
                old_s=[r for r in read_csv(old/'signals.csv') if r['instrument']==symbol]
                old_t=[r for r in read_csv(old/'trades.csv') if r['instrument']==symbol]
                # Extra touch_count belongs to the new version; historical fields remain exact.
                keys=sorted({k for r in legacy_s for k in r if k!='touch_count'})
                counts['legacy_signal_fields']+=check_rows(old_s,legacy_s,keys,'A_V1_LEGACY_REPLAY')
                keys=sorted({k for r in legacy_t for k in r if k!='unknown_effective_at'})
                counts['legacy_trade_fields']+=check_rows(old_t,legacy_t,keys,'A_V1_LEGACY_PATH')
                old_by={r['signal_id']:r for r in legacy_s};old_trade={t['signal_id']:t for t in legacy_t};new_trade={t['signal_id']:t for t in expected_t+expected_ex}
                for s in expected_s:
                    l=old_by[s['signal_id']];a=old_trade.get(s['signal_id'],{});b=new_trade.get(s['signal_id'],{})
                    different=l['status']!=s['status'] or l['reason']!=s['reason'] or a.get('status')!=b.get('status')
                    if a.get('status')=='CLOSED' and b.get('status')=='CLOSED':
                        for k in ('entry_at','entry_price','stop','take','risk','exit_price','net_R_c1'):assert_value(a[k],b[k],'COMMON_COMPARATOR_PATH '+k)
                    comparator.append(dict(instrument=symbol,signal_id=s['signal_id'],legacy_signal_status=l['status'],legacy_reason=l['reason'],
                        v2_signal_status=s['status'],v2_reason=s['reason'],legacy_trade_status=a.get('status'),v2_trade_status=b.get('status'),
                        legacy_net_R=a.get('net_R_c1'),v2_net_R=b.get('net_R_c1'),difference=different,
                        explanation='V2_MISSING_ENTRY_SKIP_REMOVES_LEGACY_DAY_LATCH_OR_SEPARATES_FILLED_EXCLUSION' if different else 'IDENTICAL_SIGNAL_AND_PATH'))
        print('independent audit '+ident,flush=True)
    neighbor_actual=read_csv(output/'parameter_neighborhood.csv')
    neighbor_map={(r['instrument'],r['configuration_id'],r['neighbor_id']):r for r in neighbor_actual}
    expected_edges=set();passed_by={s:[] for s in policy['instruments']}
    for (ident,symbol),m in expected_metrics.items():
        row=candidates[(ident,symbol)];count=0
        a=next(s for s in specs if s['configuration_id']==ident)
        for b in specs:
            delta=[abs(int(a[k])-int(b[k])) for k in ('touches','stop_buffer_ticks','target_net_R')]
            if sum(delta)!=1:continue
            other=expected_metrics[(b['configuration_id'],symbol)]
            good_neighbor=other['CLOSED']>=100 and other['expectancy_R']!=NA and other['expectancy_R']>0 and other['PF_R']!=NA and other['PF_R']>=D('1.5')
            key=(symbol,ident,b['configuration_id']);expected_edges.add(key)
            n=neighbor_map[key];assert_value(n['neighbor_qualifies'],good_neighbor,'NEIGHBOR')
            for k,v in dict(neighbor_CLOSED=other['CLOSED'],neighbor_expectancy_R=other['expectancy_R'],neighbor_PF_R=other['PF_R']).items():numeric_equal(n[k],v,'NEIGHBOR '+k)
            count+=good_neighbor;counts['neighborhood_fields']+=4
        m['pass_neighbors']=count>=2
        assert_value(row['positive_neighbor_count'],count,'NEIGHBOR_COUNT');assert_value(row['pass_neighbors'],count>=2,'NEIGHBOR_PASS')
        failed=[k.removeprefix('pass_') for k,v in m.items() if k.startswith('pass_') and not v]
        require(row['failure_reasons']=='|'.join(failed),'ALL_FAILURE_REASONS')
        status='INSUFFICIENT_SAMPLE' if not m['pass_sample'] else policy['candidate_status'] if not failed else 'DOES_NOT_QUALIFY'
        require(row['status']==status,'STATUS')
        if not failed:passed_by[symbol].append((ident,m))
        else:require(row['rank']==NA,'ONLY_PASSED_RANKED')
    require(set(neighbor_map)==expected_edges and len(neighbor_map)==len(neighbor_actual),'NEIGHBOR_ROW_SET')
    selection=json.loads((output/'selection_report.json').read_text())
    require(selection['criteria']==policy['selection'],'SELECTION_FROZEN_CRITERIA')
    for symbol,passed in passed_by.items():
        ordered=sorted(passed,key=lambda x:(-x[1]['positive_exit_months'],-min(x[1]['PF_R'],x[1]['PF_price']),x[1]['conditional_closed_only_DD_R'],-x[1]['CLOSED'],x[0]))
        require(selection['instruments'][symbol]['ranked_ids']==[x[0] for x in ordered],'RANK_ORDER')
        for i,(ident,_) in enumerate(ordered,1):assert_value(candidates[(ident,symbol)]['rank'],i,'RANK')
        cohort=[m for (i,s),m in expected_metrics.items() if s==symbol]
        checks=dict(evaluated=72,sample_pass=sum(m['pass_sample'] for m in cohort),both_PF_pass=sum(m['pass_PF_R'] and m['pass_PF_price'] for m in cohort),
            sample_and_both_PF_pass=sum(m['pass_sample'] and m['pass_PF_R'] and m['pass_PF_price'] for m in cohort),months_pass=sum(m['pass_months'] for m in cohort),
            base_study_criteria_pass=sum(all(v for k,v in m.items() if k.startswith('pass_') and k!='pass_neighbors') for m in cohort),full_criteria_pass=len(ordered),
            result=policy['candidate_status'] if ordered else policy['no_candidate_status'])
        for k,v in checks.items():assert_value(selection['instruments'][symbol][k],v,'SELECTION_COUNTS '+k)
    require(selection['evaluations']==144,'SELECTION_BUDGET')
    require(selection['overall_result']==(policy['candidate_status'] if any(passed_by.values()) else policy['no_candidate_status']),'OVERALL_SELECTION')
    write_csv(output/'comparator_gap_policy.csv',comparator)
    result=dict(status='PASS',evaluations=144,checked_fields=dict(counts),source_read_receipts=reads,
        independent_imports='STANDARD_LIBRARY_ONLY',independent_signal_method='Backward maximal-run slices',
        independent_execution_method='Forward raw Open/interval paths; occupancy from causal resolution/detection times',
        independent_economics_selection=True,bytes_2024_plus_read=0,external_human_signoff=False,
        comparator_legacy_A_v1_replay='PASS',comparator_signal_count=len(comparator),
        comparator_differences=sum(r['difference'] for r in comparator),selection=selection['overall_result'])
    write_json(output/'audit.json',result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(json.dumps(audit(a.data_root,a.output),sort_keys=True))

