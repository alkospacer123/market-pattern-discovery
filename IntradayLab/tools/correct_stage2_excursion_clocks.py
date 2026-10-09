#!/usr/bin/env python3
"""Reporting-only strict observable/actionable excursion clocks for T10/T15.

Frozen raw attribution has a nominal t+10 <=exit-clock diagnostic. This view
uses each actual scenario delay, strict before-exit observability and strictly
future effective protection, without changing any strategy decision or outcome.
Unknown rows are null immediately; their price paths are never inspected.
"""
import csv
from datetime import datetime,timedelta
from decimal import Decimal as D
import gzip
import json
from pathlib import Path
from run_m5_baseline import inputs
from independent_corrective_review import write_csv,encoded,sha
from stage2_architecture_analysis import LAB

DEST=LAB/'results/stage2_architecture_review'
FOLDERS=['stage2_complete_architectures_v1','stage2_vwap_payable_cap_v1','stage2_exit_only_ablation_v1']

def future(at):
    b=at.replace(second=0,microsecond=0);b-=timedelta(minutes=b.minute%5)
    return b+timedelta(minutes=5)


def table(path):
    opener=path.open if path.exists() else lambda **kw:gzip.open(str(path)+'.gz','rt',**kw)
    with opener(newline='') as f:return list(csv.DictReader(f))


def run(root):
    m=json.loads((LAB/'config/stage2_complete_architectures_v1.json').read_text())
    data,provenance=inputs(root,m);idx={s:{b.timestamp:b for b in bars} for s,bars in data.items()}
    result=[];known=unknown=0
    for folder in FOLDERS:
        for r in table(LAB/'results'/folder/'trade_ledger.csv'):
            rec={k:r[k] for k in ('architecture','scenario','run','signal_id','status')}
            delay=10 if r['scenario']=='C1_T10' else 15
            rec.update(availability_minutes=delay,mfe_pre_exit_lower_bound_R=None,
                mae_pre_exit_lower_bound_R=None,mfe_observed_strictly_before_exit_R=None,
                mfe_observed_and_future_protection_strictly_before_exit_R=None,
                basis='Terminal extrema excluded; observable availability<exit start; actionable next strict future slot<exit start',null_reason=None)
            if r['net_model_c1']=='':
                rec['null_reason']='UNKNOWN_OUTCOME_NOT_REEXAMINED';result.append(rec);unknown+=1;continue
            start=datetime.fromisoformat(r['entry_interval_start']);end=datetime.fromisoformat(r['exit_interval_start'])
            risk=D(r['initial_risk_price_units']);entry=D(r['entry']);d=1 if r['direction']=='LONG' else -1
            t=start;mf=ma=observed=actionable=D(0)
            while t<end:
                b=idx[r['instrument']][t]
                favorable=d*((b.high if d==1 else b.low)-entry)/risk
                adverse=-d*((b.low if d==1 else b.high)-entry)/risk
                mf=max(mf,favorable);ma=max(ma,adverse)
                delivery=t+timedelta(minutes=delay)
                if delivery<end:observed=max(observed,favorable)
                if future(delivery)<end:actionable=max(actionable,favorable)
                t+=timedelta(minutes=5)
            assert 0<=actionable<=observed<=mf
            rec.update(mfe_pre_exit_lower_bound_R=mf,mae_pre_exit_lower_bound_R=ma,
                mfe_observed_strictly_before_exit_R=observed,
                mfe_observed_and_future_protection_strictly_before_exit_R=actionable)
            result.append(rec);known+=1
    verified=json.loads((DEST/'independent_audit.json').read_text())['counts']
    assert known==verified['known_payoffs_checked'] and unknown==verified['unknown_rows_preserved_null']
    write_csv(DEST/'excursion_clock_correction.csv',result)
    (DEST/'excursion_clock_provenance.json').write_text(encoded({'status':'PASS_STRICT_SCENARIO_OBSERVABILITY_AND_FUTURE_EFFECTIVE_BOUND',
        'known':known,'unknown_null_without_path_scan':unknown,'inputs':provenance,
        'implementation_sha256':sha(Path(__file__)),
        'scope':'Reporting only; trading outputs/parameters/P&L unchanged; corrected view supersedes nominal raw observable-clock field'}))
    print(known,unknown,'strict excursion clocks corrected; unknown paths unexamined')

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True);run(p.parse_args().data_root)
