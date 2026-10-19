"""One complete fresh replay. Writes only to a new output directory."""
import argparse,io,json,sys,unittest
from pathlib import Path
sys.dont_write_bytecode=True
from common import *
from sources import prepare
from engines import h1_inputs,m15_inputs,replay
from reconcile import reconcile
from analyze import build
from verify import independent_audit,arithmetic_audit
from report import report
from test_synthetic import Synthetic

def run(h1data,m15data,out):
    assert not out.exists() or not any(out.iterdir()),'OUTPUT_MUST_BE_FRESH'
    out.mkdir(parents=True,exist_ok=True)
    if (HERE/'CODE_FREEZE.json').exists():
        freeze=json.loads((HERE/'CODE_FREEZE.json').read_text())
        for name,digest in freeze['files'].items():assert sha(HERE/name)==digest,('NEW_CODE_FREEZE_CHANGED',name)
    manifest=prepare(h1data,m15data)
    manifest['experiment_code_sha256']={p.name:sha(p) for p in sorted(HERE.glob('*.py'))}
    manifest['protocol_sha256']=sha(HERE/'PROTOCOL_RU.md')
    manifest['execution_correction_evidence_sha256']=sha(HERE/'EXECUTION_CORRECTION.json')
    manifest['implementation_commit']=git('log','-1','--format=%H','--','audit_only/t3_h1_m15_partial_tp_2r_50/run.py')
    js(out/'SOURCE_MANIFEST.json',manifest)
    buf=io.StringIO();test=unittest.TextTestRunner(stream=buf).run(unittest.defaultTestLoader.loadTestsFromTestCase(Synthetic))
    assert test.wasSuccessful(),buf.getvalue()
    js(out/'SYNTHETIC_TESTS.json',dict(status='PASS',tests=test.testsRun,failures=len(test.failures),errors=len(test.errors),cases=sorted(n for n in dir(Synthetic) if n.startswith('test_'))))
    streams=h1_inputs(h1data)+m15_inputs(m15data);print('Fresh inputs ready',flush=True)
    manifest['replay_coverage']=[dict(system=s['system'],instrument=s['instrument'],lifecycle=s['lifecycle'],fold_id=s['fold_id'],observed_bars=len(s['bars']),first_completed=s['bars'][0]['at'],last_completed=s['bars'][-1]['at'],months=sorted({b['at'].strftime('%Y-%m') for b in s['bars']})) for s in streams]
    js(out/'SOURCE_MANIFEST.json',manifest)
    controls=[replay(s,'CONTROL') for s in streams]
    gate=reconcile(streams,controls,out);print('CONTROL',gate['status'],flush=True)
    if gate['status']!='PASS':raise RuntimeError('STOP_CONTROL_MISMATCH: see CONTROL_RECONCILIATION.csv')
    # No historical experimental calculation is permitted above this gate.
    partials=[replay(s,'PARTIAL_TP_2R_50') for s in streams];results=controls+partials
    print('PARTIAL replay done',flush=True)
    mechanical=independent_audit(streams,results);print('Scalar mechanical audit PASS',flush=True)
    analysis=build(streams,results,out)
    for system in ('H1','M15'):
        for name in ('trace','signals','marks'):
            csvout(out/f'{system}_{name.upper()}.csv.gz',[x for r in results for x in r[name] if x['system']==system])
    arithmetic=arithmetic_audit(out)
    boundaries=[]
    for r in results:
        for t in r['trades']:
            if t['status']=='OPEN':boundaries.append({k:t.get(k) for k in ('system','lifecycle','fold_id','instrument','trade_id','variant','entry_time','last_mark_time','last_mark_price','remaining_quantity','partial_executed')})
    csvout(out/'OPEN_BOUNDARIES.csv',boundaries)
    audit=dict(status='FRACTIONAL_AUDIT_PASS_CASH_NOT_VALIDATED',control=gate,mechanical=mechanical,arithmetic=arithmetic,
        synthetic_tests=test.testsRun,source_identity='PASS',parameter_search=False,live_API_calls=0,raw_source_copied=False,
        executable_integer='CASH_MODEL_NOT_VALIDATED',h1_verdict='INCONCLUSIVE',m15_verdict='INCONCLUSIVE',
        data_checks_after={str(p):git('rev-parse','HEAD',root=p) for p in (h1data,m15data)},
        external_audit='PENDING')
    js(out/'AUDIT.json',audit)
    report(analysis,audit,manifest,out)
    print('Completed',out,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--h1-data',type=Path,required=True);p.add_argument('--m15-data',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.h1_data.resolve(),a.m15_data.resolve(),a.output.resolve())
