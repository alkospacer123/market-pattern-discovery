"""Development-only CONTROL inputs, features and retrospective diagnostics."""
import argparse, importlib, json
from pathlib import Path
from support import *
from features import build
from outcomes import calculate

def run(out,control_path):
    assert not out.exists() or not any(out.iterdir()),'OUTPUT_MUST_BE_FRESH'
    out.mkdir(parents=True,exist_ok=True)
    gate=json.loads(Path(control_path).read_text())
    assert gate['status']=='PASS' and gate['mismatches']==0,'STOP_CONTROL_MISMATCH'
    archives();engine=frozen()
    streams,entries,coverage=build(engine)
    results=[engine.replay(s,'CONTROL') for s in streams]
    outcomes,post,execution,disposition,reconciliation=calculate(streams,results,entries)
    csvout(out/'COVERAGE.csv',coverage)
    for system in ('H1','M15'):
        csvout(out/f'ENTRY_FEATURES_{system}.csv',[r for r in entries if r['system']==system])
        csvout(out/f'OUTCOME_GROUPS_{system}.csv',[r for r in outcomes if r['system']==system])
        csvout(out/f'SIGNAL_DISPOSITION_{system}.csv',[r for r in disposition if r['system']==system])
    csvout(out/'EXECUTION_DIAGNOSTICS.csv',execution);csvout(out/'POST_STOP.csv',post)
    js(out/'DEVELOPMENT_RECONCILIATION.json',reconciliation)
    from analysis_tables import analyze
    analyze(entries,outcomes,post,execution,results,out)
    print(json.dumps(dict(signals=len(entries),trades=len(outcomes),reconciliation=reconciliation)),flush=True)
    return streams,results,entries,outcomes

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--control',type=Path,required=True);a=p.parse_args();run(a.output.resolve(),a.control)
