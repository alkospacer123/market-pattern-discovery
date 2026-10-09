#!/usr/bin/env python3
"""Independent artifact invariants, read-only 2023 prefixes, no strategy runs."""
import argparse
from collections import Counter,defaultdict
import csv
from datetime import datetime, timedelta
from decimal import Decimal as D
import hashlib
import io
import json
from pathlib import Path
import subprocess

from run_m5_baseline import (LAB,DEST,encoded,git,inputs,load_manifest,sha,write_text,
                             implementation_hashes)
from m5_baseline import allowed,tick,window_at,FIVE


def audit(root):
    m,msha=load_manifest()
    data,provenance=inputs(root,m)
    prepared=json.loads((DEST/'input_provenance.json').read_text())
    results=json.loads((DEST/'results.json').read_text())
    assert prepared['inputs']==results['inputs']==provenance
    assert prepared['manifest_sha256']==results['manifest_sha256']==msha
    assert prepared['implementation_sha256']==results['implementation_sha256']==implementation_hashes()
    for line in (DEST/'SHA256SUMS').read_text().splitlines():
        digest,name=line.split()
        assert sha(DEST/name)==digest, name
    def csv_rows(name):
        with (DEST/name).open(newline='') as stream:
            return list(csv.DictReader(stream))
    signals=csv_rows('signals.csv'); events=csv_rows('execution_events.csv'); ledger=csv_rows('trade_ledger.csv')
    unknown=csv_rows('unknown_entries.csv')
    history=json.loads((DEST/'correction_history.json').read_text())
    correction=prepared['missing_target_correction']
    assert hashlib.sha256(encoded(history['prior']).encode()).hexdigest()==correction['prior_history_sha256']
    assert correction['manifest_parameters_changed'] is False
    assert correction['saved_before_corrected_replay'] is True
    assert history['prior']['head']==correction['prior_head']
    # Validate the retained pre-fix evidence against Git, never replaying old
    # decisions or reading a protected market-data year.
    def prior_bytes(name):
        return subprocess.check_output(['git','-C',str(LAB.parent),'show',
            f"{correction['prior_head']}:IntradayLab/results/stage2_m5/{name}"])
    def prior_rows(name):
        return list(csv.DictReader(io.StringIO(prior_bytes(name).decode())))
    for name,digest in history['prior']['artifact_sha256'].items():
        assert hashlib.sha256(prior_bytes(name)).hexdigest()==digest, name
    old_results=json.loads(prior_bytes('results.json'))
    assert old_results['inputs']==provenance and old_results['manifest_sha256']==msha
    assert history['prior']['run_summaries']==[
        {k:r[k] for k in ('run','summary','execution_counts')} for r in old_results['runs']]
    old_missing=[{k:e[k] for k in ('run','signal_id','at','confirmed_at','reason')}
        for e in prior_rows('execution_events.csv') if e['kind']=='ENTRY' and
        e['status']=='NONFILL' and e['reason']=='MISSING_OR_UNAVAILABLE_TTL_BAR']
    assert len(old_missing)==61 and old_missing==history['prior']['missing_target_entry_events']
    old_signals={s['signal_id']:s for s in prior_rows('signals.csv')}
    old_ledger={r['signal_id']:r for r in prior_rows('trade_ledger.csv')}
    by_signal={s['signal_id']:s for s in signals}
    assert len(by_signal)==len(signals)
    assert set(by_signal)==set(old_signals)
    for s in signals:
        assert {k:v for k,v in s.items() if k not in ('status','reason')}=={
            k:v for k,v in old_signals[s['signal_id']].items() if k not in ('status','reason')}
    bar_times={s:{b.timestamp for b in bs} for s,bs in data.items()}
    for s in signals:
        at,av,ready,target=map(datetime.fromisoformat,(s['signal_at'],s['available_at'],s['ready_at'],s['planned_execution_at']))
        assert at.year==av.year==ready.year==target.year==2023
        assert av>=at+2*FIVE and ready>=av and target>ready
        assert target==ready+FIVE  # this manifest's exact aligned zero extra delay scenario
    for row in ledger:
        assert row==old_ledger[row['signal_id']], 'Retained trade changed beyond missing-target fix'
        s=by_signal[row['signal_id']];symbol=row['instrument']
        entry=datetime.fromisoformat(row['entry_interval_start'])
        assert entry==datetime.fromisoformat(s['planned_execution_at'])
        assert entry>datetime.fromisoformat(s['ready_at'])
        assert entry in bar_times[symbol] and allowed(symbol,entry)
        assert entry+FIVE<=window_at(entry)[1]-6*FIVE
        assert D(row['c1_entry'])==int(row['entry_filled_model_units'])*tick(symbol,entry)
        assert D(row['c1_total'])==D(row['c1_entry'])+D(row['c1_exit'])
        assert row['stop']==s['stop'] and row['take']==s['take'] and row['entry_cap']==s['cap']
        exits=[e for e in events if e['signal_id']==row['signal_id'] and e['kind']=='EXIT' and int(e['filled_model_units'])]
        expected_cost=sum((int(e['filled_model_units'])*tick(symbol,datetime.fromisoformat(e['at'])) for e in exits),D(0))
        expected_gross=sum((int(e['filled_model_units'])*(1 if row['direction']=='LONG' else -1)*(D(e['reference_price'])-D(row['entry'])) for e in exits),D(0))
        assert expected_cost==D(row['c1_exit']) and expected_gross==D(row['gross_price_pnl'])
        for e in exits:
            at=datetime.fromisoformat(e['at'])
            assert at in bar_times[symbol] and allowed(symbol,at)
            assert datetime.fromisoformat(e['confirmed_at'])>=at+2*FIVE
            assert e['reason']!='TAKE' or at!=entry
        if row['status']=='UNRESOLVED':
            assert not row['net_model_c1'] and row['unresolved_reasons']
        else:
            assert int(row['residual_model_units'])==0
            assert D(row['net_model_c1'])==expected_gross-D(row['c1_total'])
            assert D(row['net_R'])==D(row['net_model_c1'])/D(row['initial_risk_price_units'])
    for e in events:
        if e['kind'] in ('ENTRY','EXIT') and int(e['filled_model_units']):
            symbol=by_signal[e['signal_id']]['instrument'];at=datetime.fromisoformat(e['at'])
            assert at in bar_times[symbol] and allowed(symbol,at)
    # Every failed entry receives an explicit end-of-TTL cancellation.
    for s in signals:
        if s['status']=='NONFILL':
            assert any(e['signal_id']==s['signal_id'] and e['kind']=='ENTRY_CANCEL' for e in events)
    assert not any(e['reason']=='MISSING_OR_UNAVAILABLE_TTL_BAR' for e in events)
    unknown_by_run={u['run']:u for u in unknown}
    assert len(unknown_by_run)==len(unknown)  # one persistent fail-closed latch per independent run
    for u in unknown:
        s=by_signal[u['signal_id']]
        target=datetime.fromisoformat(u['planned_execution_at'])
        detected=datetime.fromisoformat(u['detected_at'])
        assert target not in bar_times[u['instrument']] and detected==target+2*FIVE
        assert s['status']==u['status']=='UNRESOLVED_POSSIBLE_ENTRY_FILL'
        assert s['reason']==u['reason']=='MISSING_OR_UNAVAILABLE_TARGET_BAR'
        assert all(u[k]==s[k] for k in ('signal_at','available_at','ready_at','planned_execution_at','direction'))
        assert not any(u[k] for k in ('filled_model_units','possible_residual_model_units','entry',
                                     'gross_price_pnl','c1_entry','net_model_c1'))
        assert u['funding_and_emergency_costs']=='UNRESOLVED'
        assert u['resolution']=='UNRESOLVED_TO_2023_END'
        assert u['flat_target_breach']==u['close_requirement_recorded']=='True'
        assert u['signal_id'] not in {r['signal_id'] for r in ledger}
        own=[e for e in events if e['signal_id']==u['signal_id']]
        assert len([e for e in own if e['kind']=='ENTRY_ORDER'])==1
        outcome=[e for e in own if e['kind']=='ENTRY_OUTCOME']
        assert len(outcome)==1 and outcome[0]['confirmed_at']==u['detected_at']
        assert not any(e['kind'] in ('ENTRY','EXIT','ENTRY_CANCEL') for e in own)
        assert any(e['kind']=='POSSIBLE_ENTRY_RESIDUAL' and e['status']=='UNRESOLVED' for e in own)
        for e in own:
            if e['kind']!='ENTRY_ORDER' and e['reason']!='POSSIBLE_FILL_AWAITING_ACK':
                assert not e['filled_model_units'] and not e['residual_model_units'] and not e['reference_price']
        assert not any(e['run']==u['run'] and e['kind'] in ('ENTRY_ORDER','ENTRY','EXIT_ORDER','EXIT')
                       and datetime.fromisoformat(e['at'])>=detected for e in events)
        for later in signals:
            if later['run']==u['run'] and datetime.fromisoformat(later['available_at'])>=detected:
                assert later['status']=='BLOCKED' and later['reason']=='UNRESOLVED_POSSIBLE_ENTRY_FILL'
    expected={(x['strategy'],x['instrument']) for x in m['run_matrix']}
    assert {(r['run'].rsplit('_',1)[0],r['run'].rsplit('_',1)[1]) for r in results['runs']}==expected
    groups=csv_rows('metrics.csv')
    assert len([g for g in groups if g['group']=='YEAR'])==8
    assert len([g for g in groups if g['group']=='DIRECTION'])==16
    assert len([g for g in groups if g['group']=='MONTH'])==96
    totals=Counter(r['status'] for r in ledger)
    assert sum(r['summary']['trades'] for r in results['runs'])==len(ledger)
    assert sum(r['summary']['unresolved'] for r in results['runs'])==totals['UNRESOLVED']
    for r in results['runs']:
        rows=[row for row in ledger if row['run']==r['run']]
        closed=[row for row in rows if row['net_model_c1']]
        nets=[D(row['net_model_c1']) for row in closed]
        gross=sum((D(row['gross_price_pnl']) for row in rows),D(0))
        costs=sum((D(row['c1_total']) for row in rows),D(0))
        positive=sum((n for n in nets if n>0),D(0));negative=-sum((n for n in nets if n<0),D(0))
        summary=r['summary']
        assert summary['trades']==len(rows) and summary['closed_accounted_trades']==len(closed)
        assert summary['unresolved']==sum(row['status']=='UNRESOLVED' for row in rows)
        assert summary['unknown_entry_orders']==int(r['run'] in unknown_by_run)
        assert summary['total_unresolved_cases']==summary['unresolved']+summary['unknown_entry_orders']
        assert D(summary['gross_known_price_pnl'])==gross and D(summary['c1_known'])==costs
        assert summary['closed_only_net_c1']==(str(sum(nets,D(0))) if nets else None)
        assert summary['PF']==(str(positive/negative) if negative else None)
        counts=Counter(s['status'] for s in signals if s['run']==r['run'])
        assert dict(counts)==r['signal_status_counts'] and sum(counts.values())==r['signals']
        blocked=[s for s in signals if s['run']==r['run'] and s['status']=='BLOCKED']
        eligible=0
        for s in blocked:
            target=datetime.fromisoformat(s['planned_execution_at'])
            w=window_at(datetime.fromisoformat(s['signal_at']))
            if (allowed(s['instrument'],target) and window_at(target)==w and
                target+FIVE<=w[1]-timedelta(minutes=m['parameters']['no_entry_before_boundary_minutes']) and
                ((D(s['stop'])<D(s['signal_close'])<D(s['take'])) if s['direction']=='LONG' else
                 (D(s['take'])<D(s['signal_close'])<D(s['stop'])))):
                eligible+=1
        assert r['execution_counts']['blocked_signals']==len(blocked)
        assert r['execution_counts']['blocked_entry_opportunities']==eligible
        assert r['execution_counts']['unknown_flat_target_breaches']==int(r['run'] in unknown_by_run)
        assert r['execution_counts']['flat_target_breaches']==sum(row['flat_target_breach']=='True' for row in rows)
        if summary['total_unresolved_cases']:
            assert r['summary']['net_model_c1'] is None
            assert r['summary']['full_PF'] is None
            assert r['summary']['metric_status']=='INCOMPLETE / CLOSED-ONLY DIAGNOSTIC'
        if r['run'] in unknown_by_run:
            assert summary['model_flat_confirmed'] is False and summary['possible_residual_model_units'] is None
            start=unknown_by_run[r['run']]['planned_execution_at'][:7]
            for key,mark in r['month_end_model_marks'].items():
                if key>=start:
                    assert mark['model_flat_confirmed'] is False and mark['net_complete'] is False
                    assert all(mark[k] is None for k in ('possible_residual_model_units','gross_open_price_pnl',
                                                        'known_mtm_after_c1_price_units','net_model_c1_mtm'))
            for g in groups:
                if g['run']==r['run'] and (g['group'] in ('YEAR','DIRECTION') or g['period']>=start):
                    assert not g['net_model_c1'] and not g['full_PF'] and not g['possible_residual_model_units']
                    assert g['model_flat_confirmed']=='False'
                    assert g['metric_status']=='INCOMPLETE / CLOSED-ONLY DIAGNOSTIC'
                    if g['group']=='MONTH':
                        assert g['month_outcome']=='UNRESOLVED' and not g['month_end_known_mtm_after_c1']
    classifications=Counter()
    assert len(history['original_61_case_dispositions'])==61
    for old,disposition in zip(old_missing,history['original_61_case_dispositions']):
        assert all(disposition[k]==v for k,v in old.items())
        s=by_signal[old['signal_id']]
        classification=('UNRESOLVED_POSSIBLE_ENTRY_FILL' if s['status']=='UNRESOLVED_POSSIBLE_ENTRY_FILL'
                        else 'BLOCKED_NOT_SUBMITTED_DUE_TO_EARLIER_UNKNOWN')
        assert s['status'] in ('UNRESOLVED_POSSIBLE_ENTRY_FILL','BLOCKED')
        assert classification==disposition['corrected_classification']
        classifications[classification]+=1
    assert history['after']==[{k:r[k] for k in ('run','summary','execution_counts')} for r in results['runs']]
    repo=LAB.parent
    protected={x.split()[3]:x.split()[2] for x in git(repo,'ls-tree','HEAD').splitlines() if x.split()[3]!='IntradayLab'}
    assert protected==m['protected_tree_ids']
    assert not git(repo,'diff',m['base_main'],'--','.',':(exclude)IntradayLab')
    assert not git(repo,'ls-files','--others','--exclude-standard','--','.',':(exclude)IntradayLab')
    assert sha(LAB/'reports/STAGE1_2_SESSION_MTF_RESULTS.json')==m['prior_artifact_sha256']
    assert prepared['causal_gap_ack_correction']['manifest_parameters_changed'] is False
    payload={'artifact_invariants':'PASS','matrix_runs':8,'signals':len(signals),'execution_events':len(events),
             'trade_status_counts':dict(totals),'open_residual_model_units':sum(int(r['residual_model_units']) for r in ledger),
             'unknown_entry_orders':len(unknown),'possible_residual_model_units':None if unknown else 0,
             'model_flat_confirmed':not unknown and not any(int(r['residual_model_units']) for r in ledger),
             'total_unresolved_cases':totals['UNRESOLVED']+len(unknown),
             'blocked_signals':sum(r['execution_counts']['blocked_signals'] for r in results['runs']),
             'blocked_entry_opportunities':sum(r['execution_counts']['blocked_entry_opportunities'] for r in results['runs']),
             'known_position_flat_target_breaches':sum(r['execution_counts']['flat_target_breaches'] for r in results['runs']),
             'unknown_order_flat_target_breaches':sum(r['execution_counts']['unknown_flat_target_breaches'] for r in results['runs']),
             'original_61_case_dispositions':dict(classifications),
             'prior_result_hashes_verified_against_git':True,'retained_trade_rows_unchanged':True,
             'signals_and_parameters_unchanged_except_execution_status':True,
             'metric_rows':{'year':8,'direction':16,'month':96},
             'manifest_sha256':msha,'read_2023_rows':sum(p['rows'] for p in provenance.values()),
             'read_2023_prefix_bytes':sum(p['prefix_bytes_read'] for p in provenance.values()),
             'bytes_2024_plus_read':0,'bytes_2025_plus_read':0,
             'zero_volume_2023_bars':{s:sum(b.volume==0 for b in bs) for s,bs in data.items()},
             'protected_root_tree_ids':protected,'historical_stage1_artifacts_unchanged':True,
             'fixed_manifest_unchanged_after_results':True,'logging_only_correction_invariance_verified_before_gap_fix':True,
             'pending_entry_gap_ack_correction_applied':True,
             'missing_target_unknown_order_correction_applied':True,
             'verdict':'STAGE2_M5_BASELINE_CORRECTED_PENDING_REAUDIT',
             'model_fill_is_actual_exchange_evidence':False}
    write_text(DEST/'verification.json',encoded(payload))
    sums={p.name:sha(p) for p in sorted(DEST.iterdir()) if p.name!='SHA256SUMS' and p.is_file()}
    write_text(DEST/'SHA256SUMS',''.join(f'{v}  {k}\n' for k,v in sums.items()))
    print(encoded(payload))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root',type=Path,required=True)
    args=parser.parse_args();audit(args.data_root)
