#!/usr/bin/env python3
"""Independent batch SWING_PULLBACK_M5_M15 oracle, raw paths and ledger economics.

Imports no production loader, strategy, engine, indicators or metric functions.
Reuses only the accepted independent auditor's calendar/grid/source/assertion
utilities. This is an independent implementation, not external human signoff.
"""
import argparse
import ast
from collections import Counter
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
CONFIG=LAB/'config/swing_pullback_m5_m15_2023_v1.json'
FREEZE=subprocess.check_output(['git','-C',str(ROOT),'log','--diff-filter=A','--format=%H','--',str(CONFIG.relative_to(ROOT))],text=True).strip()


def batch_context(symbol, raw, at, window, last_gap):
    """Direct exact timestamp slices, independent of streaming adapter."""
    now=at+FIVE;latest=now-timedelta(minutes=20)
    latest=latest.replace(minute=(latest.minute//15)*15,second=0,microsecond=0)
    starts=[latest-timedelta(minutes=i) for i in (30,15,0)]
    rec=dict(signal_decision_at=now,context_direction=0,context_valid=False,
        context_reason='',last_gap_start=last_gap)
    parents=[]
    for i,start in enumerate(starts,1):
        times=[start+j*FIVE for j in range(3)]
        valid=(start>=window[0] and start+3*FIVE<=window[1] and
            (last_gap is None or start>last_gap) and
            all(t+FIVE<=now and good(raw.get(t),symbol,t) for t in times))
        fields=dict(start=start,closed_at=start+3*FIVE,available_at=start+4*FIVE,
            child_m5_starts=','.join(t.strftime('%H:%M') for t in times),
            high=max(raw[t][1] for t in times) if valid else None,
            low=min(raw[t][2] for t in times) if valid else None,
            close=raw[times[-1]][3] if valid else None,valid=valid)
        rec.update({f'p{i}_{k}':v for k,v in fields.items()});parents.append(fields)
    if starts[0]<window[0]:
        rec['context_reason']='MTF_THREE_PARENTS_NOT_READY'
    elif not all(p['valid'] for p in parents):
        rec['context_reason']='MTF_INCOMPLETE_OR_GAP_RESET'
    else:
        p1,p2,p3=parents
        long=p1['high']<p2['high']<p3['high'] and p1['low']<p2['low']<p3['low'] and p3['close']>p1['close']
        short=p1['high']>p2['high']>p3['high'] and p1['low']>p2['low']>p3['low'] and p3['close']<p1['close']
        rec.update(context_valid=True,context_direction=1 if long else -1 if short else 0,
            context_reason='' if long or short else 'MTF_NO_TREND')
    return rec


def episodes(symbol,raw,include_context=False):
    output=[];contexts=[];day=date(2023,1,1);first=min(raw).date()
    while day.year==2023:
        for a,z in windows(day) if day>=first else []:
            at=a;last_gap=None
            while at<z:
                b=raw.get(at)
                if not good(b,symbol,at):
                    last_gap=at
                context=batch_context(symbol,raw,at,(a,z),last_gap)
                ident=f'{symbol}_{day}_{at:%H%M}';step=tick(symbol,at)
                rec=dict(signal_id=ident,instrument=symbol,date=str(day),direction=0,
                    signal_at=None,test_start=at,pullback_confirmed=False,confirmed_signal=False,
                    signal_tick=step,recorded_at=at+FIVE,
                    context_valid=context['context_valid'],context_direction=context['context_direction'],
                    context_reason=context['context_reason'],context_decision_id=ident,
                    context_p3_start=context['p3_start'],context_p3_available_at=context['p3_available_at'])
                preceding=[at-2*FIVE,at-FIVE]
                if not good(b,symbol,at):
                    reason='M5_MISSING_BAR' if b is None else 'M5_INVALID_BAR'
                elif not context['context_valid'] or context['context_direction']==0:
                    reason=context['context_reason']
                elif preceding[0]<a or not all(good(raw.get(t),symbol,t) for t in preceding):
                    reason='PULLBACK_TWO_BARS_NOT_READY'
                else:
                    x,y=[raw[t] for t in preceding];side=context['context_direction']
                    rec.update(direction=side,correction_1_start=preceding[0],correction_2_start=preceding[1],
                        test_open=b[0],test_high=b[1],test_low=b[2],test_close=b[3],test_closed_at=at+FIVE)
                    for i,c in enumerate((x,y),1):
                        rec.update({f'correction_{i}_{k}':v for k,v in zip(('open','high','low','close'),c[:4])})
                    pull=side*(x[3]-x[0])<0 and side*(y[3]-y[0])<0 and side*(x[3]-y[3])>=step
                    confirm=side*(b[3]-b[0])>0 and (b[3]>=y[1]+step if side==1 else b[3]<=y[2]-step)
                    rec['pullback_confirmed']=pull
                    reason='NO_TWO_BAR_PULLBACK' if not pull else 'NO_CONTINUATION_CONFIRMATION' if not confirm else 'SIGNAL'
                    if reason=='SIGNAL':
                        signal=at+FIVE;entry=signal+FIVE
                        rec.update(signal_at=signal,confirmed_signal=True,
                            stop=min(x[2],y[2],b[2])-step if side==1 else max(x[1],y[1],b[1])+step,
                            target_gross_R=D(3),target_net_R=D(3),target_mode='FULL_NET_C1_R',
                            max_hold_calendar_minutes=120,waiting_bar_start=signal,
                            waiting_bar_closed_at=entry,planned_execution_at=entry,window_start=a,window_end=z)
                rec['base_reason']=reason;output.append(rec)
                contexts.append(dict(context,instrument=symbol,signal_id=ident,signal_start=at,
                    window_start=a,window_end=z,pullback_confirmed=rec['pullback_confirmed'],
                    confirmed_signal=rec['confirmed_signal'],decision_reason=reason))
                at+=FIVE
        day+=timedelta(days=1)
    return (output,contexts) if include_context else output


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
            net_R_c1=(gross-expense)/q['risk'],realized_net_to_net_R=(gross-expense)/(q['risk']+expense),stop_take_conflict=conflict)
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
        s.update(pending_created=False,open_admission_passed=None)
        if unknown_at and now>=unknown_at:
            s['reason']='UNKNOWN_POSITION_BLOCK';continue
        if (busy_until and now<busy_until) or (unknown_at and now<unknown_at):
            s['reason']='POSITION_BUSY';continue
        cutoff=windows(date.fromisoformat(day))[0][0]+timedelta(hours=7)
        if entry>=cutoff:
            s['reason']='TRADE_DEADLINE';continue
        if entry>=s['window_end']-FIVE:
            s['reason']='SESSION_LIMIT';continue
        if entry+timedelta(minutes=35)>min(s['window_end']-FIVE,cutoff):
            s['reason']='SESSION_ENTRY_CUTOFF';continue
        s['pending_created']=True
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
        s.update(entry_open=b[0],entry_tick=step,open_admission_passed=False)
        if risk<=0:
            s.update(status='NONFILL',reason='INVALID_RISK');continue
        if risk<4*step:
            s.update(status='NONFILL',reason='RISK_BELOW_FOUR_TICKS');continue
        s['open_admission_passed']=True
        target=b[0]+s['direction']*(3*risk+8*step)
        target=(target/step).to_integral_value(rounding=ROUND_CEILING if s['direction']==1 else ROUND_FLOOR)*step
        deadline=min(entry+timedelta(minutes=120),s['window_end']-FIVE,cutoff)
        q.update(entry_at=entry,entry_price=b[0],take=target,risk=risk,model_filled=True,entry_tick=step,
                 cost_entry_c1=step,trade_deadline_at=cutoff,effective_deadline_at=deadline)
        s.update(status='MODEL_FILLED',reason='',model_filled=True,entry_open=b[0],risk=risk,take=target)
        diagnostic=dict(target_mode='FULL_NET_C1_R',target_net_R=D(3),planned_C1=2*step,
            d_legacy=3*risk+2*step,d_full=3*risk+8*step,rounded_take_distance=s['direction']*(target-b[0]),
            planned_net_to_net_R=(s['direction']*(target-b[0])-2*step)/(risk+2*step),
            legacy_net_to_gross_R=D(3),realized_net_to_net_R=None)
        s.update(diagnostic);q.update(diagnostic)
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


def funnel_from_csv(signals,trades):
    return dict(context_decisions=len(signals),
        valid_M15_contexts=sum(s['context_valid']=='True' for s in signals),
        unique_valid_M15_contexts=len({s['context_p3_start'] for s in signals if s['context_valid']=='True'}),
        LONG_trends=sum(s['context_valid']=='True' and s['context_direction']=='1' for s in signals),
        SHORT_trends=sum(s['context_valid']=='True' and s['context_direction']=='-1' for s in signals),
        M5_pullbacks=sum(s['pullback_confirmed']=='True' for s in signals),
        continuation_signals=sum(s['confirmed_signal']=='True' for s in signals),
        rejected_continuation_signals=sum(s['confirmed_signal']=='True' and s['model_filled']!='True' for s in signals),
        pending_entries=sum(s.get('pending_created')=='True' for s in signals),
        submitted_orders=sum(s['order_admitted']=='True' for s in signals),
        admitted_Open_entries=sum(s.get('open_admission_passed')=='True' for s in signals),
        position_busy=sum(s['reason']=='POSITION_BUSY' for s in signals),
        model_fills=sum(t['model_filled']=='True' for t in trades),closed=sum(t['status']=='CLOSED' for t in trades),
        unknown=sum(t['status']=='UNKNOWN' for t in trades),
        unknown_possible_fills=sum(t['status']=='UNKNOWN' and t['model_filled']!='True' for t in trades))


def target_stats_from_csv(trades):
    closed=[t for t in trades if t['status']=='CLOSED'];filled=[t for t in trades if t['model_filled']=='True']
    take=[t for t in closed if t['exit_reason']=='TAKE'];wins=[t for t in closed if D(t['net_c1'])>0]
    def reduce(items,key):
        return sum((D(t[key]) for t in items),D(0))
    return dict(initial_R_denominator='initial gross price risk; unchanged common metric contract',
        target_ratio_denominator='initial gross risk + round-trip C1',
        planned_full_net_R_min=min((D(t['planned_net_to_net_R']) for t in filled),default=None),
        planned_full_net_R_max=max((D(t['planned_net_to_net_R']) for t in filled),default=None),
        target_hit_closed=len(take),target_hit_fraction_known_closed=D(len(take))/len(closed) if closed else None,
        actual_Take_net_net_R_min=min((D(t['realized_net_to_net_R']) for t in take),default=None),
        actual_Take_net_net_R_max=max((D(t['realized_net_to_net_R']) for t in take),default=None),
        known_closures_reaching_full_net_3R=sum(D(t['realized_net_to_net_R'])>=3 for t in closed),
        gross_R_known_closed=reduce(closed,'gross_R'),cost_R_known_closed=reduce(closed,'cost_R'),
        gross_price_known_closed=reduce(closed,'gross'),cost_price_known_closed=reduce(closed,'cost_c1'),
        mean_positive_realized_net_net_R=reduce(wins,'realized_net_to_net_R')/len(wins) if wins else None,
        adverse_Stop_gaps=sum(t['exit_reason']=='STOP' and bool(t['exit_at']) for t in closed),
        unresolved_filled_targets=sum(t['model_filled']=='True' and t['status']=='UNKNOWN' for t in trades),
        exit_reasons=dict(sorted(Counter(t['exit_reason'] for t in closed).items())))


def audit(root,output):
    allowed=LAB/'results/swing_pullback_m5_m15_2023_v1'
    if output.resolve()!=allowed.resolve() and not output.resolve().is_relative_to((LAB/'work').resolve()):
        raise ValueError('AUDIT_OUTPUT_MUST_BE_SWING_PULLBACK_M5_M15_RESULTS_OR_INTRADAYLAB_WORK')
    cfg=json.loads(CONFIG.read_text())
    require(subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()==cfg['source_ref'],'SOURCE_HEAD')
    require(not subprocess.check_output(['git','-C',str(root),'status','--porcelain=v1','--untracked-files=all'],text=True).strip(),'SOURCE_CHANGED')
    frozen=subprocess.check_output(['git','-C',str(ROOT),'show',FREEZE+':'+str(CONFIG.relative_to(ROOT))])
    require(frozen==CONFIG.read_bytes(),'CONFIG_CHANGED_AFTER_FREEZE')
    for path,digest in cfg['execution_code_sha256'].items():
        require(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,'FROZEN_EXECUTION '+path)
    provenance=json.loads((output/'provenance.json').read_text())
    require(provenance['config_freeze_commit']==FREEZE and provenance['config_sha256']==hashlib.sha256(frozen).hexdigest(),'FREEZE_PROVENANCE')
    for path,digest in provenance['code_sha256'].items():
        require(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,'CODE_HASH '+path)
    for path in [*(LAB/'core').glob('*.py'),LAB/'strategies/swing_pullback_m5_m15.py']:
        text=path.read_text();tree=ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom):
                require(not (node.module or '').startswith('TradingSystemLab'),'PROTECTED_IMPORT')
        if path.parent.name=='core':
            require('SWING_PULLBACK_M5_M15' not in text and 'orb_breakout' not in text,'CANDIDATE_RULE_IN_CORE')
    raw,receipts=read_source(root,cfg)
    ss=read_csv(output/'signals.csv');tt=read_csv(output/'trades.csv');cc=read_csv(output/'coverage_daily.csv')
    metrics=json.loads((output/'metrics.json').read_text());details={};checked=coverage_checked=metric_checked=0
    signal_keys=('base_reason','direction','signal_at','test_start','signal_tick','test_open','test_high','test_low','test_close','test_closed_at',
        'pullback_confirmed','confirmed_signal','context_valid','context_direction','context_reason','context_decision_id',
        'context_p3_start','context_p3_available_at',
        'correction_1_start','correction_2_start',
        *[f'correction_{i}_{k}' for i in (1,2) for k in ('open','high','low','close')],
        'pending_created','open_admission_passed','stop','status','reason','order_admitted','model_filled',
        'entry_open','entry_tick','risk','take','recorded_at','waiting_bar_start','waiting_bar_closed_at','planned_execution_at',
        'target_mode','target_net_R','planned_C1','d_legacy','d_full','rounded_take_distance','planned_net_to_net_R','legacy_net_to_gross_R')
    trade_keys=('direction','signal_at','status','model_filled','entry_at','entry_price','entry_tick','stop','take','risk',
        'exit_reason','unknown_reason','exit_at','exit_interval_start','exit_interval_end','resolved_at',
        'unknown_detected_at','exit_price','exit_tick','gross','gross_R','cost_entry_c1','cost_c1','cost_R',
        'net_c1','net_R_c1','prior_unknown_requires_flat_assumption','order_sent_at','waiting_bar_closed_at',
        'planned_execution_at','trade_deadline_at','effective_deadline_at','stop_take_conflict',
        'target_mode','target_net_R','planned_C1','d_legacy','d_full','rounded_take_distance',
        'planned_net_to_net_R','legacy_net_to_gross_R','realized_net_to_net_R')
    contexts=read_csv(output/'mtf_context.csv');context_checked=0
    for symbol in cfg['instruments']:
        events,expected_contexts=episodes(symbol,raw[symbol],include_context=True)
        context_checked+=check_rows([c for c in contexts if c['instrument']==symbol],expected_contexts,tuple(expected_contexts[0]),'M15_CONTEXT')
        expected_s,expected_t=replay(symbol,raw[symbol],events)
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
        require(m['unknown_reasons']==dict(Counter(t['unknown_reason'] for t in actual_t if t['status']=='UNKNOWN')),'UNKNOWN_REASONS')
        require(m['rejection_reasons']==dict(Counter(s['reason'] for s in actual_s if s['reason'])),'REJECTIONS')
        for t in actual_t:
            if t['status']=='UNKNOWN':
                require(all(t.get(k,'')=='' for k in ('exit_price','gross','gross_R','net_c1','net_R_c1','cost_c1')),'UNKNOWN_ECONOMICS_IMPUTED')
        regularity=dict(positive_month_fraction_of_12=D(dist['positive_months'])/12,
            positive_active_month_fraction=D(dist['positive_months'])/dist['active_months'] if dist['active_months'] else None,
            worst_known_closed_month=min(dist['monthly_closed_Net_R'],key=dist['monthly_closed_Net_R'].get) if dist['monthly_closed_Net_R'] else None,
            worst_known_closed_month_Net_R=min(dist['monthly_closed_Net_R'].values(),default=None),
            model_fills_per_available_calendar_day=D(m['model_fills'])/sum(c['status']!='PRE_INCEPTION' for c in cov) if any(c['status']!='PRE_INCEPTION' for c in cov) else None)
        for key,value in regularity.items():
            assert_value(m['calendar_regularity'][key],value,'CALENDAR_REGULARITY '+symbol+' '+key);metric_checked+=1
        reconstructed_funnel=funnel_from_csv(actual_s,actual_t)
        require(m['funnel']==reconstructed_funnel,'FUNNEL '+symbol)
        td=target_stats_from_csv(actual_t)
        require(set(m['target_C1_diagnostics'])==set(td),'TARGET_STATS_SET')
        for key,value in td.items():
            assert_value(m['target_C1_diagnostics'][key],value,'TARGET_C1_DIAGNOSTICS '+key);metric_checked+=1
        details[symbol]=dict(funnel=reconstructed_funnel,signals=len(expected_s),trades=len(expected_t),metrics_from_csv=values,
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
    monthly_coverage=read_csv(output/'coverage_report.csv')
    require(len(monthly_coverage)==48,'MONTHLY_COVERAGE_COUNT')
    require({(r['instrument'],r['month']) for r in monthly_coverage}==
        {(s,f'2023-{i:02d}') for s in cfg['instruments'] for i in range(1,13)},'MONTHLY_COVERAGE_SET')
    for row in monthly_coverage:
        cohort=[c for c in cc if c['instrument']==row['instrument'] and c['date'].startswith(row['month'])]
        expected=dict(complete_days=sum(c['status']=='COMPLETE' for c in cohort),
            incomplete_days=sum(c['status']=='INCOMPLETE' for c in cohort),
            pre_inception_days=sum(c['status']=='PRE_INCEPTION' for c in cohort),
            missing_bars=sum(int(c['missing_bars']) for c in cohort),
            invalid_bars=sum(int(c['invalid_bars']) for c in cohort),
            expected_bars=sum(int(c['expected_bars']) for c in cohort),
            valid_bars=sum(int(c['valid_bars']) for c in cohort),
            physical_source_rows=sum(at.strftime('%Y-%m')==row['month'] for at in raw[row['instrument']]))
        for key,value in expected.items():
            assert_value(row[key],value,'MONTHLY_COVERAGE '+key);coverage_checked+=1
    unknown_rows=read_csv(output/'unknown_report.csv')
    unknown_trades=[t for t in tt if t['status']=='UNKNOWN']
    require({r['signal_id'] for r in unknown_rows}=={t['signal_id'] for t in unknown_trades},'UNKNOWN_REPORT_IDS')
    for row in unknown_rows:
        trade=next(t for t in unknown_trades if t['signal_id']==row['signal_id'])
        for key in ('instrument','signal_at','entry_at','model_filled','unknown_reason','exit_price','net_R_c1'):
            require(row[key]==trade[key],'UNKNOWN_REPORT '+key)
        require(row['missing_interval_end']==trade['unknown_detected_at'],'UNKNOWN_INTERVAL')
    require(not subprocess.check_output(['git','-C',str(ROOT),'diff',cfg['base_main'],'--','IntradayLab/core/backtester.py','IntradayLab/core/execution.py','TradingSystemLab'],text=True),'SHARED_EXECUTION_OR_PROTECTED_TREE_CHANGED')
    require(json.loads((output/'funnel.json').read_text())=={s:v['funnel'] for s,v in details.items()},'FUNNEL_JSON')
    statuses=[v['assessment']['status'] for v in details.values()]
    expected_status='INCONCLUSIVE' if 'INCONCLUSIVE' in statuses else 'ECONOMICALLY_PROMISING_BASELINE' if all(s=='ECONOMICALLY_PROMISING_BASELINE' for s in statuses) else 'NO ECONOMIC BASELINE PASS'
    require(metrics['baseline_status']==expected_status and metrics['optimization_allowed'] is False,'OVERALL_STATUS')
    require(metrics['portfolio_money_return'] is None and metrics['portfolio_price_PF'] is None,'INVALID_PRICE_POOLING')
    result=dict(status='PASS',method=__doc__.strip(),checked_ledger_fields=checked,
        checked_context_fields=context_checked,checked_coverage_fields=coverage_checked,checked_metric_fields=metric_checked,
        checked_report_metric_fields=table_checked,instruments=details,source_receipts=receipts,
        bytes_2024_plus_read=0,bytes_2025_plus_read=0,config_freeze_commit=FREEZE,
        baseline_status=expected_status,discrepancies=[],external_human_acceptance='Not claimed; independent PR review remains required')
    (output/'audit.json').write_text(json.dumps(result,default=str,sort_keys=True,indent=2)+'\n')
    (output/'Independent_Audit.md').write_text('# Independent implementation audit — SWING_PULLBACK_M5_M15\n\n'
        'Status: **PASS**. No production engine, strategy, indicator, loader or metric imports.\n\n'
        f'Checked {context_checked} M15 context fields, {checked} ledger fields, {coverage_checked} coverage fields, {metric_checked} instrument metric fields and {table_checked} report metric fields.\n\n'
        'Independent LF-budget source reading verifies exact pinned 2023 bytes. Batch exact 3x3 M5 slices independently verify M15 wall alignment, availability start+20, strict three-parent structure, gap/session/day reset and no stale fallback. Exactly two opposite-color corrections and a separate continuation verify structural Stop. A separate forward oracle verifies four-tick risk, full-net 3R, grid, waiting, Stop/Take, C1, deadlines, missing bars and UNKNOWN. CSV-only recalculation verifies economic and concentration metrics and computed classifications. All 12 months and both directions checked.\n\n'
        'The config equals the pre-P&L freeze commit. No 2024 or 2025+ price bytes read; no imputed UNKNOWN economics or pooled cross-instrument price returns.\n\n'
        'Detailed exact field checks are in audit.json; corruption guards and byte regression are in validation.json. This is implementation-independent verification by the task agent, not a second person or external reviewer signoff. Draft PR awaits independent review.\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-root',type=Path,required=True)
    p.add_argument('--output',type=Path,default=LAB/'results/swing_pullback_m5_m15_2023_v1')
    a=p.parse_args();result=audit(a.data_root,a.output)
    print(json.dumps({k:result[k] for k in ('status','checked_ledger_fields','checked_coverage_fields','checked_metric_fields','checked_report_metric_fields')},sort_keys=True))
