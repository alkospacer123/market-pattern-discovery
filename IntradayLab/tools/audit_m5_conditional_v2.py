#!/usr/bin/env python3
"""Independent integer-price arithmetic and source OHLCV audit. No strategy run.

Uses the common physically bounded input reader, but no Replay, metrics,
protection, payoff or tick implementation to calculate expected outcomes.
"""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timedelta
from decimal import Decimal as D
import json
from pathlib import Path

from run_m5_baseline import inputs, encoded, sha, LAB
from run_m5_conditional_v2 import (DEST, load_manifest, implementation_hashes,
    original_hashes, write, checksums)

SCALE=D(1000)

def millis(value):
    x=D(value)*SCALE
    assert x==x.to_integral_value(), ('off independent integer grid',value)
    return int(x)

def dated_tick_millis(symbol,at):
    if symbol=='CNYRUBF': return 10 if at<datetime(2023,9,27,19) else 1
    return {'USDRUBF':10,'GLDRUBF':100,'IMOEXF':500}[symbol]

def table(name):
    with (DEST/name).open(newline='') as f: return list(csv.DictReader(f))

def ratio(a,b): return D(a)/D(b) if b else None

def numeric(value): return D(value) if value else None

def audit(root):
    m,digest=load_manifest(); data,prov=inputs(root,m)
    prepared=json.loads((DEST/'input_provenance.json').read_text())
    results=json.loads((DEST/'results.json').read_text())
    assert prepared['inputs']==results['inputs']==prov
    assert prepared['manifest_sha256']==results['manifest_sha256']==digest
    assert prepared['implementation_sha256']==results['implementation_sha256']==implementation_hashes()
    assert prepared['original_artifact_sha256']==original_hashes()
    for line in (DEST/'SHA256SUMS').read_text().splitlines():
        expected,name=line.split(); assert sha(DEST/name)==expected,name
    index={symbol:{b.timestamp:b for b in bars} for symbol,bars in data.items()}
    missing_cases=[('VWAP_MR','USDRUBF','2023-02-02 15:40:00'),
        ('VWAP_MR','CNYRUBF','2023-01-06 17:15:00'),('VWAP_MR','GLDRUBF','2023-08-17 16:00:00'),
        ('VWAP_MR','IMOEXF','2023-11-30 17:20:00'),('MOMENTUM','USDRUBF','2023-02-03 16:15:00'),
        ('MOMENTUM','CNYRUBF','2023-01-19 15:25:00'),('MOMENTUM','GLDRUBF','2023-07-12 11:40:00'),
        ('MOMENTUM','IMOEXF','2023-11-15 16:25:00')]
    physical=[]
    for strategy,symbol,t in missing_cases:
        at=datetime.fromisoformat(t); assert at not in index[symbol],(symbol,t)
        before=max(x for x in index[symbol] if x<at); after=min(x for x in index[symbol] if x>at)
        physical.append({'run':strategy+'_'+symbol,'missing_at':t,
            'previous_observed':str(before),'next_observed':str(after),'confirmed_absent':True})
    signals=table('signals.csv'); events=table('execution_events.csv'); trades=table('trade_ledger.csv')
    no_bars=table('no_bar_entries.csv'); econ=table('economics.csv'); grouped=table('metrics.csv')
    by_signal={s['signal_id']:s for s in signals}; assert len(by_signal)==len(signals)
    by_trade={r['signal_id']:r for r in trades}; assert len(by_trade)==len(trades)
    event_map=defaultdict(list)
    for e in events: event_map[e['signal_id']].append(e)
    # All original signal features/levels must remain unchanged. Execution busy
    # state and status can differ; trading rule and its opportunities cannot.
    with (LAB/'results/stage2_m5/signals.csv').open(newline='') as f:
        original=list(csv.DictReader(f))
    assert len(signals)==len(original)
    for new,old in zip(signals,original):
        assert {k:v for k,v in new.items() if k not in ('status','reason')}=={k:v for k,v in old.items() if k not in ('status','reason')},new['signal_id']
    for s in signals:
        at,av,ready,target=map(datetime.fromisoformat,[s[k] for k in ('signal_at','available_at','ready_at','planned_execution_at')])
        assert at.year==av.year==ready.year==target.year==2023
        assert av>=at+timedelta(minutes=10) and ready>=av and target>ready
        assert target==at+timedelta(minutes=15)
        b=index[s['instrument']][at]
        assert D(s['signal_close'])==b.close
        start=datetime.fromisoformat(s['session_id'].split('--')[0])
        prior_times=[at-timedelta(minutes=5*i) for i in range(13,0,-1)]
        assert all(t>=start and t in index[s['instrument']] for t in prior_times), 'Causal contiguous warm-up'
        prior=[index[s['instrument']][t] for t in prior_times]
        tr=[max(y.high-y.low,abs(y.high-x.close),abs(y.low-x.close)) for x,y in zip(prior[:-1],prior[1:])]
        assert D(s['atr_shifted'])==sum(tr,D(0))/12
        assert D(s['range_high_shifted'])==max(x.high for x in prior[-12:])
        assert D(s['range_low_shifted'])==min(x.low for x in prior[-12:])
        if s['strategy']=='VWAP_MR':
            segment=[]; t=at
            while t>=start and t in index[s['instrument']] and index[s['instrument']][t].volume>0:
                segment.append(index[s['instrument']][t]); t-=timedelta(minutes=5)
            # Preserve chronological Decimal accumulation, independently of Features.
            segment.reverse(); weight=sum((x.volume for x in segment),D(0))
            weighted=sum(((x.high+x.low+x.close)/3*x.volume for x in segment),D(0))
            assert len(segment)>=14 and D(s['vwap_approx'])==weighted/weight
    for row in no_bars:
        s=by_signal[row['signal_id']]; at=datetime.fromisoformat(row['planned_execution_at'])
        assert at not in index[row['instrument']]
        assert s['status']==row['classification']=='NO_BAR_NO_MODEL_FILL'
        assert datetime.fromisoformat(row['detected_at'])==at+timedelta(minutes=10)
        assert row['signal_id'] not in by_trade
        assert not any(e['kind']=='ENTRY' for e in event_map[row['signal_id']])
        assert row['exchange_outcome']=='NOT_INFERRED'
    assert len(no_bars)==sum(s['status']=='NO_BAR_NO_MODEL_FILL' for s in signals)
    for strategy,symbol,t in missing_cases:
        own=[n for n in no_bars if n['run']==strategy+'_'+symbol and n['planned_execution_at']==t]
        assert len(own)==1
        assert any(r['run']==strategy+'_'+symbol and r['entry_interval_start']>t for r in trades), 'Independent later entries restored'
    samples=[]; totals=Counter(); audited_exits=0
    for row in trades:
        s=by_signal[row['signal_id']]; symbol=row['instrument']
        entry_at=datetime.fromisoformat(row['entry_interval_start']); b=index[symbol][entry_at]
        direction=1 if row['direction']=='LONG' else -1
        entry=millis(row['entry']); stop=millis(row['stop']); take=millis(row['take']); cap=millis(row['entry_cap'])
        assert entry==millis(str(b.open))
        assert row['stop']==s['stop'] and row['take']==s['take'] and row['entry_cap']==s['cap']
        assert entry_at==datetime.fromisoformat(s['planned_execution_at'])
        assert entry_at>datetime.fromisoformat(s['ready_at'])
        assert datetime.fromisoformat(row['entry_confirmed_at'])>=entry_at+timedelta(minutes=10)
        assert (stop<entry<take and entry<=cap) if direction==1 else (take<entry<stop and entry>=cap)
        q=int(row['entry_filled_model_units']); assert q==1
        c1_entry=q*dated_tick_millis(symbol,entry_at)
        assert millis(row['c1_entry'])==c1_entry
        own=event_map[row['signal_id']]
        unknown_path='MISSING_PATH' in row['unresolved_reasons']
        if unknown_path:
            assert row['status']=='UNRESOLVED'
            assert not any(row[k] for k in ('exit','exit_interval_start','exit_interval_end','exit_confirmed_at',
                'gross_price_pnl','c1_exit','c1_total','net_model_c1','net_R','exit_filled_model_units'))
            assert row['funding_and_emergency_costs']=='UNRESOLVED'
            path=[e for e in own if e['kind']=='POSITION_PATH']; assert path
            for e in path:
                assert datetime.fromisoformat(e['at']) not in index[symbol]
                assert not e['reference_price'] and not e['filled_model_units']
            if row['model_flat_confirmed_at']:
                flat=[e for e in own if e['status']=='CONDITIONAL_MODEL_FLAT']; assert len(flat)==1
                e=flat[0]; t=datetime.fromisoformat(e['at'])
                assert t in index[symbol]
                assert not e['reference_price'] and not e['filled_model_units']
                assert row['model_flat_confirmed_at']==e['confirmed_at']
                assert datetime.fromisoformat(e['confirmed_at'])>=t+timedelta(minutes=10)
                orders=[e for e in own if e['kind']=='EXIT_ORDER' and datetime.fromisoformat(e['at'])<t]
                assert orders, 'Conditional reduction must have been scheduled in advance'
                assert row['residual_model_units']=='0'
            totals['unresolved_paths']+=1
            continue
        gross=cost=0
        exits=[e for e in own if e['kind']=='EXIT' and e['filled_model_units'] and int(e['filled_model_units'])>0]
        for e in exits:
            t=datetime.fromisoformat(e['at']); eb=index[symbol][t]; price=millis(e['reference_price'])
            assert datetime.fromisoformat(e['confirmed_at'])>=t+timedelta(minutes=10)
            qty=int(e['filled_model_units']); gross+=qty*direction*(price-entry)
            cost+=qty*dated_tick_millis(symbol,t); audited_exits+=1
            st_hit=eb.low<=D(row['stop']) if direction==1 else eb.high>=D(row['stop'])
            step=D(dated_tick_millis(symbol,t))/SCALE
            if e['reason']=='STOP':
                assert st_hit
                expected=min(eb.open,D(row['stop'])) if direction==1 else max(eb.open,D(row['stop']))
                assert price==millis(str(expected))
            elif e['reason']=='TAKE':
                assert t>entry_at and not st_hit
                assert eb.high>=D(row['take'])+step if direction==1 else eb.low<=D(row['take'])-step
                assert price==take
            else:
                assert price==millis(str(eb.open))
                orders=[o for o in own if o['kind']=='EXIT_ORDER' and datetime.fromisoformat(o['at'])<t]
                assert orders
                if e['reason']=='SESSION_FLAT':
                    boundary=datetime.fromisoformat(row['session_id'].split('--')[1])
                    sent=datetime.fromisoformat(orders[-1]['at'])
                    assert sent<=boundary-timedelta(minutes=25)
                    assert datetime.fromisoformat(e['confirmed_at'])<=boundary-timedelta(minutes=10)
            assert e['reason']!='TAKE' or t!=entry_at
        assert millis(row['gross_price_pnl'])==gross and millis(row['c1_exit'])==cost
        assert millis(row['c1_total'])==c1_entry+cost
        if row['net_model_c1']:
            assert millis(row['net_model_c1'])==gross-c1_entry-cost
            assert D(row['net_R'])==D(row['net_model_c1'])/D(row['initial_risk_price_units'])
        totals['integer_accounted_trades']+=1
        # Source-verified examples stratified by run/direction/exit reason.
        sample_key=(row['run'],row['direction'],row['exit_reason'])
        if not any(x['sample_key']==list(sample_key) for x in samples):
            samples.append({'sample_key':list(sample_key),'signal_id':row['signal_id'],
                'source_entry_at':str(entry_at),'source_entry_open':str(b.open),
                'stop':row['stop'],'take':row['take'],'exit_at':row['exit_interval_start'],
                'source_ohlcv_exit_rule_verified':True,
                'source_blob':m['inputs'][symbol]['blob'],
                'gross':row['gross_price_pnl'],'c1':row['c1_total'],'net':row['net_model_c1']})
    # Independent economics: exact price distances in integer milli-quote units,
    # projecting both costs using the dated planned/actual entry tick.
    for r in econ:
        s=by_signal[r['signal_id']]; direction=int(s['direction_sign'])
        step=dated_tick_millis(r['instrument'],datetime.fromisoformat(s['planned_execution_at']))
        ref=millis(r['reference_price']); reward=direction*(millis(s['take'])-ref)
        risk=direction*(ref-millis(s['stop'])); cost=2*step
        for key,value in [('gross_reward',reward),('gross_risk',risk),('net_reward',reward-cost),
                          ('net_risk',risk+cost),('c1_roundtrip_projected',cost)]:
            assert millis(r[key])==value,(r['signal_id'],key)
        assert D(r['take_ticks'])==ratio(reward,step)
        assert D(r['stop_ticks'])==ratio(risk,step)
        expected=ratio(risk+cost,risk+reward) if risk>=0 and reward>0 else None
        assert numeric(r['min_breakeven_win_rate'])==expected
        assert numeric(r['potential_net_reward_risk'])==ratio(reward-cost,risk+cost) if risk+cost>0 else not r['potential_net_reward_risk']
        if r['stage']=='MODEL_ENTRY': assert r['signal_id'] in by_trade
    # Independent aggregate PF, expectancy, gross/cost/net, no full PF on unknowns.
    for g in grouped:
        rows=[r for r in trades if r['run']==g['run'] and
            (g['group']!='MONTH' or r['entry_interval_start'][:7]==g['period']) and
            (g['direction']=='ALL' or r['direction']==g['direction'])]
        closed=[r for r in rows if r['net_model_c1']]
        vals=[millis(r['net_model_c1']) for r in closed]
        wins=sum(v for v in vals if v>0); losses=-sum(v for v in vals if v<0)
        assert int(g['trades'])==len(rows)
        assert int(g['closed_accounted_trades'])==len(closed)
        assert numeric(g['PF'])==ratio(wins,losses)
        if vals: assert numeric(g['expectancy_price_units'])==D(sum(vals))/SCALE/len(vals)
        if g['metric_status'] in ('NO_COVERAGE','INCOMPLETE / CLOSED-ONLY DIAGNOSTIC'):
            assert not g['net_model_c1'] and not g['full_PF']
        else: assert millis(g['net_model_c1'])==sum(vals)
        if g['metric_status']=='NO_COVERAGE': assert not rows and not g['closed_only_net_c1']
    assert len(grouped)==312
    assert all(r['summary']['full_PF'] is None for r in results['runs'] if r['summary']['total_unresolved_cases'])
    assert not any(s['status']=='BLOCKED' for s in signals)
    assert sum(r['summary']['trades'] for r in results['runs'])==len(trades)
    assert sum(r['execution_counts']['no_bar_no_model_fill'] for r in results['runs'])==len(no_bars)
    report={'audit':'PASS','method':'Independent integer milli-price arithmetic; all entry/exit bars checked against original bounded 2023 M5 source; stratified samples retained',
        'manifest_sha256':digest,'implementation_sha256':implementation_hashes(),
        'physically_verified_missing_cases':physical,'source_prefix_provenance':prov,
        'counts':{'signals':len(signals),'events':len(events),'model_entries':len(trades),
            'economics_rows':len(econ),'no_bar_entries':len(no_bars),'source_verified_exit_events':audited_exits,
            'source_verified_stratified_samples':len(samples),'arithmetic_linkage_mismatches':0}|dict(totals),
        'samples':samples,'limits':['Independent algorithm in same task, not a second human/agent review',
            'Full trade outcomes through missing position bars remain unknown',
            'Conditional reduce-all acknowledgement is a model assumption, not exchange proof'],
        'verdicts':{'Execution model':'PASS','Research completeness':'NEEDS FIX',
            'VWAP economic viability':'INCONCLUSIVE','Momentum economic viability':'INCONCLUSIVE'}}
    write(DEST/'verification.json',encoded(report)); checksums()
    print(encoded({k:report[k] for k in ('audit','counts','verdicts')}))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--data-root',type=Path,required=True)
    audit(p.parse_args().data_root)
