#!/usr/bin/env python3
"""Independent arithmetic/path verifier of bounded Stage 2 artifacts.

Checks known paths only. Original/candidate unknown rows remain null; this is
not another missing-bar investigation. Does not call strategy Replay or alter
rules/artifacts. Uses source read-only exact 2023 prefix budgets.
"""
import argparse
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
from datetime import datetime,timedelta
from decimal import Decimal as D, ROUND_CEILING, ROUND_FLOOR
import json
from pathlib import Path

from independent_corrective_review import encoded, sha, independent_tick
from run_m5_baseline import inputs
from stage2_architecture_analysis import LAB, BASE


def rows(path):
    opener=path.open if path.exists() else lambda **kw:gzip.open(str(path)+'.gz','rt',**kw)
    with opener(newline='') as f:return list(csv.DictReader(f))


def raw_sha(path):
    if path.exists():return sha(path)
    with gzip.open(str(path)+'.gz','rb') as f:return hashlib.sha256(f.read()).hexdigest()


def key(r):return tuple(r[x] for x in ('architecture','scenario','run','signal_id'))


def price_round(value,step,up):
    return (value/step).to_integral_value(rounding=ROUND_CEILING if up else ROUND_FLOOR)*step


def strict_future(at):
    b=at.replace(second=0,microsecond=0);b-=timedelta(minutes=b.minute%5)
    return b+timedelta(minutes=5)


def audit(root,folders):
    m=json.loads((LAB/'config/stage2_complete_architectures_v1.json').read_text())
    data,prov=inputs(root,m);index={s:{b.timestamp:b for b in bars} for s,bars in data.items()}
    counts=Counter();details=[]
    for folder in folders:
        signals={key(s):s for s in rows(folder/'signals.csv')}
        events=defaultdict(list)
        for e in rows(folder/'execution_events.csv'):events[key(e)].append(e)
        amendments=defaultdict(list)
        if ((folder/'stop_amendments.csv').exists() or (folder/'stop_amendments.csv.gz').exists()):
            for a in rows(folder/'stop_amendments.csv'):amendments[key(a)].append(a)
        ledger=rows(folder/'trade_ledger.csv')
        byrun=defaultdict(list)
        for row in ledger:
            k=key(row);s=signals[k];ev=events[k];symbol=row['instrument'];d=1 if row['direction']=='LONG' else -1
            start=datetime.fromisoformat(row['entry_interval_start']);decision=datetime.fromisoformat(s['available_at'])
            assert start==strict_future(decision),('scheduled entry',k)
            assert decision>=datetime.fromisoformat(s['signal_at'])+timedelta(minutes=10 if row['scenario']=='C1_T10' else 15)
            b=index[symbol][start];entry=D(row['entry']);stop=D(row['stop']);take=D(row['take']);step=independent_tick(symbol,start)
            assert entry==b.open and d*(entry-stop)>0 and d*(take-entry)>0
            assert d*(entry-D(s['cap']))<=0
            assert D(row['initial_risk_price_units'])==abs(entry-stop)
            assert D(row['c1_entry'])==step
            quality=row['architecture'] not in ('FROZEN_V2','MANAGEMENT','EXIT_ONLY_FROZEN_ENTRIES')
            if quality:
                assert abs(entry-stop)>=4*step
                assert d*(take-entry)-2*step>=abs(entry-stop)+2*step
                if row['strategy']=='MOMENTUM':
                    edge=D(s['range_high_shifted'] if d==1 else s['range_low_shifted'])
                    assert 0<d*(entry-edge)<=D(s['atr_shifted'])
                    assert d*(D(s['signal_close'])-edge)<=D(s['atr_shifted'])
                    assert D(s['signal_tr_atr'])<=2
            if row['architecture'].startswith('PAYABLE_CAP'):
                bound=(take+stop-d*4*step)/2
                cap=price_round(bound,step,d==-1)
                assert d*(D(s['cap'])-cap)<=0
            if row['architecture'] in ('FULL_M5','PAYABLE_CAP_FULL_M5'):
                adx,pdi,mdi=map(D,(s['adx14'],s['plus_di14'],s['minus_di14']))
                aligned=pdi>mdi if d==1 else mdi>pdi
                if row['strategy']=='MOMENTUM':assert adx>=25 and aligned
                else:assert not(adx>=25 and not aligned)
            byrun[row['architecture'],row['scenario'],row['run']].append(row)
            if row['net_model_c1']=='':
                assert row['status']=='UNRESOLVED'
                assert row['net_R']=='' and row['exit']=='' and row['gross_price_pnl']=='' and row['c1_total']==''
                counts['unknown_rows_preserved_null']+=1
                continue
            end=datetime.fromisoformat(row['exit_interval_start']);cost=step+independent_tick(symbol,end)
            gross=d*(D(row['exit'])-entry)
            assert D(row['c1_total'])==cost and D(row['gross_price_pnl'])==gross
            assert D(row['net_model_c1'])==gross-cost
            assert D(row['net_R'])==(gross-cost)/abs(entry-stop)
            counts['known_payoffs_checked']+=1
            management=row['architecture'] in ('MANAGEMENT','ENTRY_MANAGEMENT','FULL_M5','PAYABLE_CAP_FULL_M5','EXIT_ONLY_FROZEN_ENTRIES')
            runner=management and row['strategy']=='MOMENTUM'
            amendments_for_trade=sorted(amendments[k],key=lambda x:x['effective_at'])
            for a in amendments_for_trade:
                when=datetime.fromisoformat(a['decided_at']);effective=datetime.fromisoformat(a['effective_at'])
                assert effective==strict_future(when)
                assert d*(D(a['stop'])-stop)>0
                stop=D(a['stop'])
                observable=when-timedelta(minutes=10 if row['scenario']=='C1_T10' else 15)
                assert observable in index[symbol]
                observed=index[symbol][observable]
                assert d*(observed.close-entry)>=abs(entry-D(row['stop']))
                assert d*(D(a['stop'])-observed.close)<0
                counts['causal_amendment_decisions_checked']+=1
            active=D(row['stop']);t=start
            while t<=end:
                b=index[symbol][t]
                effective=[a for a in amendments_for_trade if datetime.fromisoformat(a['effective_at'])<=t]
                if effective:active=D(effective[-1]['stop'])
                market_last=t==end and row['exit_reason'] not in ('STOP','TAKE','BREAKEVEN_STOP','TRAIL_STOP')
                if market_last:
                    orders=[e for e in ev if e['kind']=='EXIT_ORDER']
                    assert orders and strict_future(datetime.fromisoformat(orders[0]['at']))<=t
                    assert D(row['exit'])==b.open
                else:
                    stop_hit=b.low<=active if d==1 else b.high>=active
                    take_hit=not runner and t>start and (b.high>=take+independent_tick(symbol,t) if d==1 else b.low<=take-independent_tick(symbol,t))
                    if stop_hit:
                        assert t==end and row['exit_reason'] in ('STOP','BREAKEVEN_STOP','TRAIL_STOP'),('missed prior Stop',k,t)
                        assert D(row['exit'])==(min(b.open,active) if d==1 else max(b.open,active))
                    elif take_hit:
                        assert t==end and row['exit_reason']=='TAKE',('missed prior Take',k,t)
                        assert D(row['exit'])==take
                    elif t==end:
                        raise AssertionError(('unproved exit',k,t,row['exit_reason']))
                counts['known_path_bars_checked']+=1;t+=timedelta(minutes=5)
        for rec in rows(folder/'metrics.csv') if ((folder/'metrics.csv').exists() or (folder/'metrics.csv.gz').exists()) else []:
            cohort=[r for r in byrun[rec['architecture'],rec['scenario'],rec['run']] if (rec['period']=='2023' or r['entry_interval_start'][:7]==rec['period']) and (rec['direction']=='ALL' or r['direction']==rec['direction'])]
            closed=[r for r in cohort if r['net_model_c1']!=''];nets=[D(r['net_model_c1']) for r in closed]
            assert int(rec['trades'])==len(cohort) and int(rec['closed_accounted_trades'])==len(closed)
            assert int(rec['unresolved'])==sum(r['status']=='UNRESOLVED' for r in cohort)
            if closed:
                assert D(rec['closed_only_net_c1'])==sum(nets,D(0))
                assert D(rec['closed_only_c1'])==sum((D(r['c1_total']) for r in closed),D(0))
                assert D(rec['net_expectancy_closed_diagnostic'])==sum(nets,D(0))/len(nets)
                gains=sum((n for n in nets if n>0),D(0));loss=-sum((n for n in nets if n<0),D(0))
                assert rec['net_PF_closed_diagnostic']=='' if not loss else D(rec['net_PF_closed_diagnostic'])==gains/loss
            if rec['full_period_accounted']=='False':
                for field in ('Net','net_model_c1','PF','full_PF','full_Drawdown'):assert rec[field]==''
                assert rec['Net_null_reason'] and rec['full_PF_null_reason']
            assert rec['group']!='YEAR' or rec['full_PF']==''
            counts['economic_metric_rows_checked']+=1
        details.append({'folder':folder.name,'ledger_sha256':raw_sha(folder/'trade_ledger.csv'),'signals_sha256':raw_sha(folder/'signals.csv'),'results_sha256':sha(folder/'results.json')})
    return {'status':'PASS_INDEPENDENT_KNOWN_PATH_AND_ARITHMETIC_CHECKS',
        'limits':'No independent real-fill certification or economic acceptance. Unknown paths NOT examined or reconciled; no exact intrabar MFE/DD claim.',
        'counts':dict(counts),'inputs':prov,'outputs_checked':details,
        'implementation_sha256':sha(Path(__file__))}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();folders=[LAB/'results/stage2_complete_architectures_v1',LAB/'results/stage2_vwap_payable_cap_v1',LAB/'results/stage2_exit_only_ablation_v1']
    result=audit(a.data_root,folders);a.output.write_text(encoded(result));print(encoded(result['counts']))
