"""Frozen five-configuration experiment; both control gates precede candidates."""
import argparse,json,platform,subprocess,sys,re
from pathlib import Path
import numpy as np,pandas as pd
import common as C,control as G,analysis as A

def freeze_guard():
    f=json.loads((C.HERE/'FREEZE.json').read_text())
    for name,digest in f['code_spec_sha256'].items():
        assert C.file_sha(C.HERE/name)==digest,('FROZEN_CODE_CHANGED',name)
        assert C.sha(C.historical('IntradayLab/t3_m15_a6_s1_trail_optimization_v1/'+name,f['commit']))==digest
    assert not C.git('ls-tree','-r','--name-only',f['commit'],'--','IntradayLab/t3_m15_a6_s1_trail_optimization_v1/results').strip()
    return f

def run(root,output,controls_only=False):
    frozen=freeze_guard();output.mkdir(parents=True,exist_ok=True)
    test=subprocess.run([sys.executable,str(C.HERE/'test_causal.py')],capture_output=True,text=True);assert test.returncode==0,test.stdout+test.stderr
    frames,sources=G.load(root);scalars,_=G.load(root,True)
    control=G.compute(frames,G.CONTROLS);G.persist(control,output/'control');p=G.gate(control,output/'control')
    scalar_control=G.compute(scalars,G.CONTROLS,True);G.persist(scalar_control,output/'control_scalar');s=G.gate(scalar_control,output/'control_scalar',True)
    print(json.dumps({'primary_control':p['status'],'scalar_control':s['status'],'primary_fields':p['fields_compared'],'scalar_fields':s['fields_compared']}),flush=True)
    if controls_only:return
    # No candidate calculation is reachable until both raw-journal controls PASS.
    candidates=G.compute(frames,[v for v in C.VERSIONS if v not in G.CONTROLS])
    out={k:control[k]+candidates[k] for k in G.NAMES};G.persist(out,output/'replay')
    tables=A.build(out,frames)
    for name,rows in tables.items():C.write_csv(output/(name+'.csv'),rows)
    A.render(tables,output)
    C.write_json(output/'SOURCE_MANIFEST.json',{'base_main':C.BASE,'data_commit':C.DATA_SHA,'sources':sources,'frozen_commit':frozen['commit'],'code_spec_sha256':frozen['code_spec_sha256'],'spec_sha256':C.file_sha(C.HERE/'SPEC.json'),'OHLC_2025_plus_parsed':False,'raw_quotes_copied':False,'labels':C.LABEL,'period':'2023-2024 DEVELOPMENT_EXPOSED','runtime':{'python':platform.python_version(),'pandas':pd.__version__,'numpy':np.__version__},'CONTROL_primary':p['status'],'CONTROL_scalar':s['status'],'engine_byte_identical_to_PR504':C.file_sha(C.HERE/'engine.py')==C.sha(C.historical('IntradayLab/t3_m15_execution_sensitivity_v1/engine.py')),'scalar_byte_identical_to_PR504':C.file_sha(C.HERE/'scalar.py')==C.sha(C.historical('IntradayLab/t3_m15_execution_sensitivity_v1/scalar.py'))})
    (output/'TEST_RESULTS.txt').write_text(re.sub(r'Ran (\d+) tests in [0-9.]+s',r'Ran \1 tests (elapsed time omitted)',test.stdout+test.stderr))
    print(json.dumps(tables['comparison'],indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,default=Path('/workspace/market-pattern-data'));p.add_argument('--output',type=Path,default=C.HERE/'results');p.add_argument('--controls-only',action='store_true');a=p.parse_args();run(a.data_root,a.output,a.controls_only)
