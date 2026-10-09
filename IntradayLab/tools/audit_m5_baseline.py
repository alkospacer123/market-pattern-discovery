#!/usr/bin/env python3
"""Independent artifact invariants, read-only 2023 prefixes, no strategy runs."""
import argparse
from collections import Counter,defaultdict
import csv
from datetime import datetime
from decimal import Decimal as D
import hashlib
import json
from pathlib import Path

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
    assert prepared['implementation_sha256']==implementation_hashes()
    for line in (DEST/'SHA256SUMS').read_text().splitlines():
        digest,name=line.split()
        assert sha(DEST/name)==digest, name
    def csv_rows(name):
        with (DEST/name).open(newline='') as stream:
            return list(csv.DictReader(stream))
    signals=csv_rows('signals.csv'); events=csv_rows('execution_events.csv'); ledger=csv_rows('trade_ledger.csv')
    by_signal={s['signal_id']:s for s in signals}
    assert len(by_signal)==len(signals)
    bar_times={s:{b.timestamp for b in bs} for s,bs in data.items()}
    for s in signals:
        at,av,ready,target=map(datetime.fromisoformat,(s['signal_at'],s['available_at'],s['ready_at'],s['planned_execution_at']))
        assert at.year==av.year==ready.year==target.year==2023
        assert av>=at+2*FIVE and ready>=av and target>ready
        assert target==ready+FIVE  # this manifest's exact aligned zero extra delay scenario
    for row in ledger:
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
        if r['summary']['unresolved']:
            assert r['summary']['net_model_c1'] is None
            assert r['summary']['metric_status']=='INCOMPLETE / CLOSED-ONLY DIAGNOSTIC'
    repo=LAB.parent
    protected={x.split()[3]:x.split()[2] for x in git(repo,'ls-tree','HEAD').splitlines() if x.split()[3]!='IntradayLab'}
    assert protected==m['protected_tree_ids']
    assert not git(repo,'diff',m['base_main'],'--','.',':(exclude)IntradayLab')
    assert not git(repo,'ls-files','--others','--exclude-standard','--','.',':(exclude)IntradayLab')
    assert sha(LAB/'reports/STAGE1_2_SESSION_MTF_RESULTS.json')==m['prior_artifact_sha256']
    original=prepared['implementation_correction_before_replay']
    assert prepared['causal_gap_ack_correction']['manifest_parameters_changed'] is False
    payload={'artifact_invariants':'PASS','matrix_runs':8,'signals':len(signals),'execution_events':len(events),
             'trade_status_counts':dict(totals),'open_residual_model_units':sum(int(r['residual_model_units']) for r in ledger),
             'metric_rows':{'year':8,'direction':16,'month':96},
             'manifest_sha256':msha,'read_2023_rows':sum(p['rows'] for p in provenance.values()),
             'read_2023_prefix_bytes':sum(p['prefix_bytes_read'] for p in provenance.values()),
             'bytes_2024_plus_read':0,'bytes_2025_plus_read':0,
             'zero_volume_2023_bars':{s:sum(b.volume==0 for b in bs) for s,bs in data.items()},
             'protected_root_tree_ids':protected,'historical_stage1_artifacts_unchanged':True,
             'fixed_manifest_unchanged_after_results':True,'logging_only_correction_invariance_verified_before_gap_fix':True,
             'pending_entry_gap_ack_correction_applied':True,
             'model_fill_is_actual_exchange_evidence':False}
    write_text(DEST/'verification.json',encoded(payload))
    sums={p.name:sha(p) for p in sorted(DEST.iterdir()) if p.name!='SHA256SUMS' and p.is_file()}
    write_text(DEST/'SHA256SUMS',''.join(f'{v}  {k}\n' for k,v in sums.items()))
    print(encoded(payload))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root',type=Path,required=True)
    args=parser.parse_args();audit(args.data_root)
