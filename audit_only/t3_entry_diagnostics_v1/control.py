"""Isolated full-period CONTROL gate. No diagnostic feature discovery or variants."""
import argparse, json, shutil, sys
from pathlib import Path
from support import *

def run(out):
    assert not out.exists() or not any(out.iterdir()), 'OUTPUT_MUST_BE_FRESH'
    out.mkdir(parents=True, exist_ok=True)
    receipts = archives(); engines = frozen()
    import gate
    streams, results = gate.controls(out)
    from verifier.replay_verifier import independent_replay_audit
    independent = independent_replay_audit(streams, results)
    # Authenticate PR560 CONTROL trade bytes, not just the earlier PR557 lineage.
    fields = 0
    for system in ('H1', 'M15'):
        archived = [t for t in csvin(HERE/f'work/archives/pr560/{system}_TRADES.csv') if t['variant']=='CONTROL']
        actual = [t for r in results for t in r['trades'] if t['system']==system]
        assert len(archived)==len(actual)
        for a, e in zip(actual, archived):
            for k, v in e.items():
                av=a.get(k); observed='' if av is None else av.isoformat() if hasattr(av,'isoformat') else str(av)
                assert observed == v, ('PR560_CONTROL_MISMATCH',system,k,observed,v)
                fields += 1
    receipt=json.loads((out/'SOURCE_MANIFEST.json').read_text())
    receipt.update(main_verified=MAIN, protocol_commit=PROTOCOL, archive_checks=receipts,
                   pr560_head=PINS['pr560'][0], independence='Separate scalar algorithm; same author, no external human signoff',
                   full_period_use='CONTROL reconciliation only; no discovery tables or candidate comparisons',
                   source_data_copied=False)
    js(out/'SOURCE_MANIFEST.json', receipt)
    gate_result=json.loads((out/'CONTROL_RECONCILIATION.json').read_text())
    wf=[t for r in results for t in r['trades'] if t['system']=='H1' and t['lifecycle']=='walk_forward' and t['status']=='CLOSED']
    gate_result.update(PR560_trade_fields=fields,independent_scalar_control=independent,
                       H1_WF_separate=dict(CLOSED=len(wf),INITIAL_STOP=sum(t['exit_reason']=='INITIAL_STOP' for t in wf)),
                       no_alternative_replay=True)
    js(out/'CONTROL_RECONCILIATION.json',gate_result)
    print('CONTROL_FINAL',json.dumps(gate_result['headline']),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.output.resolve())
