#!/usr/bin/env python3
"""Supplementary forensic diagnostics; no replay, optimizer or decision inputs.

Core provenance is frozen by prepare. This post-replay review separately records
its implementation hash. Missing-slot and breakout checks read ONLY the same
bounded 2023 prefixes. No raw source rows are copied into the repository.
"""
import argparse
from bisect import bisect_left
from collections import Counter
from datetime import datetime, timedelta
from decimal import Decimal as D
import json
from pathlib import Path
from statistics import median

from run_m5_baseline import inputs, encoded, sha, LAB, csv_text, git
from run_m5_conditional_v2 import DEST, load_manifest, write, checksums
from audit_m5_conditional_v2 import table
from m5_conditional_v2 import allowed, windows, FIVE, END


def run(root,test_log):
    m,digest=load_manifest(); data,prov=inputs(root,m)
    results=json.loads((DEST/'results.json').read_text())
    verification=json.loads((DEST/'verification.json').read_text())
    assert verification['audit']=='PASS' and verification['source_prefix_provenance']==prov
    test_text=test_log.read_text()
    assert 'Ran 100 tests' in test_text and test_text.rstrip().endswith('OK')
    signals=table('signals.csv'); events=table('execution_events.csv'); ledger=table('trade_ledger.csv')
    by_signal={s['signal_id']:s for s in signals}
    no_bars=table('no_bar_entries.csv'); missing=[]; nonfill=[]; breakout=[]
    for symbol,bars in data.items():
        observed=sorted(b.timestamp for b in bars); index={b.timestamp:b for b in bars}; observed_set=set(observed)
        day=bars[0].timestamp.replace(hour=0,minute=0,second=0,microsecond=0)
        while day<END:
            for a,z in windows(day.date()):
                t=a
                while t+FIVE<=z:
                    if allowed(symbol,t) and t not in observed_set:
                        at=bisect_left(observed,t)
                        related=[r for r in no_bars if r['instrument']==symbol and r['planned_execution_at']==str(t)]
                        path=[e for e in events if e['kind']=='POSITION_PATH' and e['at']==str(t) and e['run'].endswith('_'+symbol)]
                        missing.append({'instrument':symbol,'missing_at':str(t),'month':str(t)[:7],
                            'previous_observed_at':str(observed[at-1]) if at else None,
                            'next_observed_at':str(observed[at]) if at<len(observed) else None,
                            'no_model_entry_runs':'|'.join(r['run'] for r in related),
                            'uncertain_position_runs':'|'.join(e['run'] for e in path),
                            'classification':'ABSENT_FROM_CSV_EXPECTED_RESEARCH_SLOT',
                            'exchange_nonfill_or_halt':'NOT_INFERRED'})
                    t+=FIVE
            day+=timedelta(days=1)
        for s in signals:
            if s['instrument']!=symbol or s['status'] not in ('NONFILL','NO_BAR_NO_MODEL_FILL'): continue
            at=datetime.fromisoformat(s['planned_execution_at']); b=index.get(at)
            reasons=[]
            if s['status']=='NO_BAR_NO_MODEL_FILL': reasons=['NO_BAR_NO_MODEL_FILL']
            elif s['reason']!='OPEN_CAP_OR_FROZEN_PROTECTION': reasons=[s['reason']]
            elif b:
                long=s['direction']=='LONG'; stop=D(s['stop']); take=D(s['take']); cap=D(s['cap'])
                if (b.open>cap if long else b.open<cap): reasons.append('ADVERSE_CAP_EXCEEDED')
                if (b.open<=stop if long else b.open>=stop): reasons.append('OPEN_AT_OR_BEYOND_STOP')
                if (b.open>=take if long else b.open<=take): reasons.append('OPEN_AT_OR_BEYOND_TAKE')
            assert reasons
            nonfill.append({'run':s['run'],'signal_id':s['signal_id'],'status':s['status'],
                'planned_at':s['planned_execution_at'],'replay_reason':s['reason'],
                'detailed_reason':'|'.join(reasons),'exchange_outcome':'NOT_INFERRED'})
        for r in ledger:
            if r['instrument']!=symbol or r['strategy']!='MOMENTUM': continue
            s=by_signal[r['signal_id']]; long=r['direction']=='LONG'
            high=D(s['range_high_shifted']); low=D(s['range_low_shifted'])
            entry=D(r['entry']); entered_inside=entry<=high if long else entry>=low
            known=bool(r['exit_interval_start']) and r['status']=='MODELLED'
            closes_inside=None; elapsed=None
            if known:
                start=datetime.fromisoformat(r['entry_interval_start']); end=datetime.fromisoformat(r['exit_interval_start'])
                closes_inside=any((b.close<=high if long else b.close>=low) for b in bars if start<=b.timestamp<=end)
                elapsed=D(str((end-start).total_seconds()/60))
            breakout.append({'run':r['run'],'signal_id':r['signal_id'],'direction':r['direction'],
                'status':r['status'],'entry_at':r['entry_interval_start'],'exit_reason':r['exit_reason'],
                'range_reentered_at_model_open':entered_inside,
                'observed_close_returned_inside_frozen_range_before_exit':closes_inside,
                'stop_on_entry_bar':r['exit_reason']=='STOP' and elapsed==0,
                'stop_within_10_minutes':r['exit_reason']=='STOP' and elapsed is not None and elapsed<=10,
                'proxy_only_not_new_strategy_filter':True})
    for name,rows in [('missing_bar_diagnostics.csv',missing),('entry_nonfill_diagnostics.csv',nonfill),
                     ('momentum_breakout_diagnostics.csv',breakout)]:
        fields=list(dict.fromkeys(k for r in rows for k in r)); write(DEST/name,csv_text(rows,fields))
    econ=table('economics.csv'); anchors=table('vwap_anchor_comparison.csv'); groups=table('metrics.csv')
    special={}
    for symbol in ('USDRUBF','CNYRUBF'):
        all_rows=[r for r in econ if r['run']=='VWAP_MR_'+symbol and r['stage']=='SIGNAL']
        old=[r for r in all_rows if r['reference_at']<'2023-09-27 19:00:00']
        for key,rows in [('all_signals',all_rows),('before_cny_tick_switch',old)]:
            special[symbol+'_'+key]={'count':len(rows),'median_take_ticks':median(D(r['take_ticks']) for r in rows),
                'median_stop_ticks':median(D(r['stop_ticks']) for r in rows),
                'nonpositive_net_take_count':sum(r['take_cannot_pay_c1']=='True' for r in rows),
                'zero_adverse_cap_count':sum(D(r['adverse_cap_ticks'])==0 for r in rows)}
    anchor_summary={}
    for symbol in data:
        xs=[r for r in anchors if r['instrument']==symbol]
        anchor_summary[symbol]={'signals':len(xs),
            'signals_in_incomplete_windows':sum(r['full_window_vwap_reconstructable']=='False' for r in xs),
            'gap_carry_window_diff_count':sum(abs(D(r['window_minus_reset_ticks']))>D('.0001') for r in xs),
            'median_abs_daytime_session_minus_reset_ticks':median(abs(D(r['daytime_session_minus_reset_ticks'])) for r in xs),
            'true_full_exchange_session_vwap':'UNAVAILABLE'}
    momentum={}
    for run_id in sorted({r['run'] for r in breakout}):
        rows=[r for r in breakout if r['run']==run_id]
        momentum[run_id]={'entries':len(rows),'known_stop_count':sum(r['exit_reason']=='STOP' for r in rows),
            'range_reentered_at_model_open_count':sum(r['range_reentered_at_model_open'] for r in rows),
            'stop_on_entry_bar_count':sum(r['stop_on_entry_bar'] for r in rows),
            'stop_within_10_minutes_count':sum(r['stop_within_10_minutes'] for r in rows)}
    protected_main={line.split()[3]:line.split()[2] for line in git(LAB.parent,'ls-tree','origin/main').splitlines() if line.split()[3]!='IntradayLab'}
    protected_head={line.split()[3]:line.split()[2] for line in git(LAB.parent,'ls-tree','HEAD').splitlines() if line.split()[3]!='IntradayLab'}
    assert protected_main==protected_head
    summary={'manifest_sha256':digest,'review_implementation_sha256':sha(Path(__file__)),
        'test_count':100,'tests':'PASS_EXECUTED','independent_audit':'PASS',
        'source_prefix_rows_per_pass':sum(p['rows'] for p in prov.values()),
        'source_prefix_bytes_per_pass':sum(p['prefix_bytes_read'] for p in prov.values()),
        'source_2024_plus_bytes_read':0,'source_2025_plus_bytes_read':0,
        'restored_model_entries':sum(r['restored_model_entries_vs_v1'] for r in results['runs']),
        'missing_slots_by_instrument':dict(Counter(r['instrument'] for r in missing)),
        'detailed_nonfill_reasons':dict(Counter(r['detailed_reason'] for r in nonfill)),
        'covered_run_month_outcomes':dict(Counter(r['month_outcome'] for r in groups if r['group']=='MONTH' and r['direction']=='ALL')),
        'special_tick_economics':special,'anchor_comparison':anchor_summary,'momentum':momentum,
        'flat_target_breach_events':[e for e in events if e['kind']=='FLAT_TARGET'],
        'protected_root_ids_equal_main':True,'protected_root_ids':protected_head,
        'research_completeness_reason':'82 unknown position paths prevent full annual Net/PF/DD; no full calendar coverage for GLD/IMO',
        'verdicts':verification['verdicts'],
        'economic_conclusion':'Six negative closed-only net diagnostics; positive GLD Momentum / IMO VWAP are incomplete. Both strategy-level annual viability verdicts INCONCLUSIVE; neither accepted.',
        'candidate_policy':'Separate predeclared cost/tick-aware VWAP and one bounded breakout-quality Momentum hypothesis only; no runs/tuning here. If neither earns acceptance in separate valid research, roadmap Volatility Squeeze Breakout next.'}
    write(DEST/'review_summary.json',encoded(summary)); write(DEST/'test_execution.log',test_text)
    checksums(); print(encoded({k:summary[k] for k in ('restored_model_entries','covered_run_month_outcomes','missing_slots_by_instrument','momentum','flat_target_breach_events')}))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--data-root',type=Path,required=True)
    p.add_argument('--test-log',type=Path,required=True); args=p.parse_args(); run(args.data_root,args.test_log)
