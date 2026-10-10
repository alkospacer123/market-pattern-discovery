#!/usr/bin/env python3
"""Freeze, then replay v2 without writing any v1 artifact or source data."""
import argparse
from collections import Counter
from datetime import datetime, timedelta
import json
from pathlib import Path

from run_m5_baseline import (LAB, inputs, load_manifest as load_v1, encoded,
    csv_text, coverage, sha)
from m5_conditional_v2 import Replay, metrics, ZERO, END, FIVE
from m5_economics_v2 import economics, payoff_summary, performance, vwap_comparison

CONFIG=LAB/'config/stage2_m5_conditional_v2.json'
DEST=LAB/'results/stage2_m5_conditional_v2'


def load_manifest():
    m=json.loads(CONFIG.read_text()); digest=sha(CONFIG)
    if digest!=CONFIG.with_suffix('.sha256').read_text().split()[0]:
        raise ValueError('v2 manifest frozen')
    parent,parent_hash=load_v1()
    if m['parameters']!=parent['parameters'] or m['parent_manifest_sha256']!=parent_hash:
        raise ValueError('Original parameters must be identical')
    if m['run_matrix']!=parent['run_matrix'] or m['inputs']!=parent['inputs']:
        raise ValueError('Original scope/data must be identical')
    return m,digest


def implementation_hashes():
    names=['tools/m5_conditional_v2.py','tools/run_m5_conditional_v2.py',
        'tools/m5_economics_v2.py','tools/audit_m5_conditional_v2.py',
        'tests/test_m5_conditional_v2.py','tools/m5_baseline.py','tools/run_m5_baseline.py',
        'tools/session_mtf.py','tools/audit_session_mtf.py','tools/audit_m5_baseline.py']
    return {name:sha(LAB/name) for name in names}


def write(path,text):
    if not path.resolve().is_relative_to(DEST.resolve()) or not DEST.resolve().is_relative_to(LAB.resolve()):
        raise ValueError('Outside isolated v2 output')
    path.write_text(text)


def write_csv(name,rows):
    fields=list(dict.fromkeys(k for r in rows for k in r))
    write(DEST/name,csv_text(rows,fields))


def checksums():
    write(DEST/'SHA256SUMS',''.join(f'{sha(p)}  {p.name}\n' for p in sorted(DEST.iterdir())
        if p.is_file() and p.name!='SHA256SUMS'))


def original_hashes():
    paths=[LAB/'config/stage2_m5_baseline_v1.json',LAB/'config/stage2_m5_baseline_v1.sha256']
    paths+=sorted((LAB/'results/stage2_m5').iterdir())
    return {str(p.relative_to(LAB)):sha(p) for p in paths if p.is_file()}


def prepare(root):
    m,digest=load_manifest()
    _,provenance=inputs(root,m)
    payload={'manifest_sha256':digest,'parent_manifest_sha256':m['parent_manifest_sha256'],
        'source_ref':m['source_ref'],'inputs':provenance,
        'implementation_sha256':implementation_hashes(),'original_artifact_sha256':original_hashes(),
        'state':'FROZEN_BEFORE_V2_RETURNS','scope':'M5 2023 physical prefixes only',
        'conditional_flatten_assumption':'Reduce all remaining exposure branches at a pre-scheduled observed admissible bar, with model availability acknowledgement; unknown past P&L is never reconciled by OHLCV'}
    DEST.mkdir(parents=True,exist_ok=True)
    path=DEST/'input_provenance.json'
    if path.exists() and json.loads(path.read_text())!=json.loads(encoded(payload)):
        raise ValueError('Frozen provenance differs; retain history before correction')
    write(path,encoded(payload))
    print('Prepared v2',digest)


def groups(replay,bars):
    base={'run':f'{replay.strategy}_{replay.symbol}','strategy':replay.strategy,'instrument':replay.symbol}
    cov=coverage(bars)
    year=metrics(replay.ledger,replay.unknown_entries)|performance(replay.ledger)
    year['calendar_year_status']='NO_FULL_CALENDAR_COVERAGE' if any(c['coverage_status']=='NO_COVERAGE' for c in cov.values()) or bars[0].timestamp.month!=1 else 'AVAILABLE_2023_HISTORY'
    year['observed_close_mtm_drawdown']=replay.mtm_drawdown if not year['total_unresolved_cases'] else None
    year['drawdown_status']='INCOMPLETE' if year['total_unresolved_cases'] else 'OBSERVED_CLOSE_CONDITIONAL_NOT_INTRABAR'
    rows=[base|{'group':'YEAR','period':'2023','direction':'ALL'}|year]
    for direction in ('LONG','SHORT'):
        selected=[r for r in replay.ledger if r['direction']==direction]
        rows.append(base|{'group':'DIRECTION','period':'2023','direction':direction}|metrics(selected)|performance(selected))
    for key,c in cov.items():
        for direction in ('ALL','LONG','SHORT'):
            selected=[r for r in replay.ledger if r['entry_interval_start'][:7]==key and
                      (direction=='ALL' or r['direction']==direction)]
            summary=metrics(selected)|performance(selected)
            uncertainty=[r for r in replay.ledger if r['status']=='UNRESOLVED' and
                r['entry_interval_start'][:7]<=key<=(r['model_flat_confirmed_at'] or '2023-12')[:7]]
            if uncertainty:
                summary.update(metric_status='INCOMPLETE / CLOSED-ONLY DIAGNOSTIC',
                    net_model_c1=None,full_PF=None)
            if c['coverage_status']=='NO_COVERAGE':
                summary.update(metric_status='NO_COVERAGE',net_model_c1=None,
                    closed_only_net_c1=None,full_PF=None,closed_only_gross=None,closed_only_c1=None)
            outcome=('NO_COVERAGE' if c['coverage_status']=='NO_COVERAGE' else 'UNRESOLVED' if uncertainty
                else 'ZERO_TRADES' if not selected else 'POSITIVE' if summary['net_model_c1']>0
                else 'NEGATIVE' if summary['net_model_c1']<0 else 'ZERO_NET')
            # Cumulative MTM after any unknown outcome is unavailable, including
            # subsequent months. Local closed-trade monthly Net is still separate.
            mark=replay.month_marks.get(key,{})
            rows.append(base|{'group':'MONTH','period':key,'direction':direction}|summary|c|
                {'month_outcome':outcome,'month_end_model_flat_confirmed':mark.get('model_flat_confirmed') if c['coverage_status']!='NO_COVERAGE' else None,
                 'month_end_cumulative_net_mtm':mark.get('net_model_c1_mtm') if c['coverage_status']!='NO_COVERAGE' else None,
                 'observed_close_mtm_drawdown':replay.month_drawdowns.get(key) if not uncertainty and mark.get('net_complete') else None})
    streak=longest=0
    for row in rows:
        if row['group']=='MONTH' and row['direction']=='ALL':
            streak=streak+1 if row['month_outcome']=='NEGATIVE' else 0
            longest=max(longest,streak)
    year['longest_known_consecutive_negative_months']=longest
    # rows[0] is an independent merged dict.
    rows[0]['longest_known_consecutive_negative_months']=longest
    year['losing_month_streak_status']='LOWER_BOUND_UNKNOWN_MONTHS_BREAK_STREAK' if year['total_unresolved_cases'] else 'AVAILABLE_COVERED_MONTHS'
    rows[0]['losing_month_streak_status']=year['losing_month_streak_status']
    return rows,cov


def frequency(replay,bars):
    rows=[]; first=bars[0].timestamp.date(); last=(END-timedelta(days=1)).date()
    for kind in ('WEEK','MONTH'):
        buckets={}
        day=first
        while day<=last:
            key=str(day-timedelta(days=day.weekday())) if kind=='WEEK' else str(day)[:7]
            buckets.setdefault(key,[])
            day+=timedelta(days=1)
        for r in replay.ledger:
            at=datetime.fromisoformat(r['entry_interval_start']).date()
            key=str(at-timedelta(days=at.weekday())) if kind=='WEEK' else str(at)[:7]
            buckets[key].append(r)
        for key,trades in buckets.items():
            rows.append({'run':f'{replay.strategy}_{replay.symbol}','period_kind':kind,'period':key,
                'model_entries':len(trades),'accounted_trades':sum(r['net_model_c1'] is not None for r in trades),
                'unresolved_trades':sum(r['status']=='UNRESOLVED' for r in trades),
                'frequency_basis':'Available-history calendar buckets; first/last week and inception month may be partial'})
    return rows


def run(root):
    m,digest=load_manifest(); prepared=json.loads((DEST/'input_provenance.json').read_text())
    if prepared['manifest_sha256']!=digest or prepared['implementation_sha256']!=implementation_hashes() or prepared['original_artifact_sha256']!=original_hashes():
        raise ValueError('Freeze exact implementation and retain v1 before run')
    data,provenance=inputs(root,m)
    if prepared['inputs']!=provenance: raise ValueError('Changed 2023 prefixes')
    all_signals=[]; all_events=[]; all_ledger=[]; all_groups=[]; econ=[]; nonbars=[]; freq=[]; runs=[]; sensitivity=[]
    old=json.loads((LAB/'results/stage2_m5/results.json').read_text())
    old_counts={r['run']:r['summary']['trades'] for r in old['runs']}
    for item in m['run_matrix']:
        symbol,strategy=item['instrument'],item['strategy']
        replay=Replay(symbol,strategy,m['parameters']).run(data[symbol])
        grouped,cov=groups(replay,data[symbol]); run_id=f'{strategy}_{symbol}'
        all_signals+=replay.signals; all_events+=replay.events; all_ledger+=replay.ledger; all_groups+=grouped
        econ+=economics(replay,data[symbol]); nonbars+=replay.no_bar_entries; freq+=frequency(replay,data[symbol])
        runs.append({'run':run_id,'summary':grouped[0],'signals':len(replay.signals),
            'signal_status_counts':dict(Counter(s['status'] for s in replay.signals)),
            'execution_counts':replay.counts,'coverage':cov,'month_end_model_marks':replay.month_marks,
            'restored_model_entries_vs_v1':len(replay.ledger)-old_counts[run_id]})
        # One predeclared delay sensitivity, never search/rank/select parameters.
        delayed=Replay(symbol,strategy,m['parameters']|{'availability_minutes':15}).run(data[symbol])
        delayed_summary=groups(delayed,data[symbol])[0][0]
        sensitivity.append({'run':run_id,'variant':'availability_t15_open_t20_DIAGNOSTIC_ONLY',
            'baseline_availability_minutes':10,'sensitivity_availability_minutes':15,
            'baseline_model_entries':len(replay.ledger),'sensitivity_model_entries':len(delayed.ledger),
            'sensitivity_summary':delayed_summary,'execution_counts':delayed.counts})
    write(DEST/'results.json',encoded({'manifest_sha256':digest,'source_ref':m['source_ref'],
        'inputs':provenance,'implementation_sha256':prepared['implementation_sha256'],'runs':runs,
        'verdicts':{'execution_model':'PENDING_INDEPENDENT_ARITHMETIC_OHLCV_AUDIT',
            'research_completeness':'NEEDS FIX' if any(r['summary']['total_unresolved_cases'] for r in runs) else 'PENDING_AUDIT',
            'vwap_economic_viability':'INCONCLUSIVE_PENDING_AUDIT',
            'momentum_economic_viability':'INCONCLUSIVE_PENDING_AUDIT'},
        'scope':'Entire available 2023 M5 history; 2024 WF and 2025+ TRUE OOS physically unread',
        'unit':'Normalized quote price exposure, no account return or real contract sizing'}))
    for name,rows in [('signals.csv',all_signals),('execution_events.csv',all_events),('trade_ledger.csv',all_ledger),
        ('metrics.csv',all_groups),('no_bar_entries.csv',nonbars),('economics.csv',econ),
        ('economics_summary.csv',payoff_summary(econ)),('trade_frequency.csv',freq),
        ('vwap_anchor_comparison.csv',vwap_comparison(data,all_signals,m['parameters']))]: write_csv(name,rows)
    reasons=Counter((e['run'],e['kind'],e['status'],e['reason']) for e in all_events)
    write_csv('execution_diagnostics.csv',[{'run':k[0],'kind':k[1],'status':k[2],'reason':k[3],'count':v} for k,v in sorted(reasons.items())])
    write(DEST/'delay_sensitivity.json',encoded(sensitivity))
    checksums()
    for r in runs:
        s=r['summary']
        print(r['run'],s['trades'],s['closed_accounted_trades'],s['unresolved'],s['closed_only_net_c1'],s['PF'])

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=('prepare','run')); p.add_argument('--data-root',type=Path,required=True)
    args=p.parse_args(); (prepare if args.command=='prepare' else run)(args.data_root)
