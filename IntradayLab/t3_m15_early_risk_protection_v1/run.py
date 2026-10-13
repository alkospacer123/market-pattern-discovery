"""CONTROL gate -> one full causal experiment -> fixed path comparisons."""
import argparse,json,platform,re,subprocess,sys
from pathlib import Path
import pandas as pd,numpy as np
import common as C,control as G,run_control as R,analysis as A

def guard():
    freeze=json.loads((C.HERE/'FREEZE.json').read_text())
    for name,digest in freeze['code_spec_sha256'].items():
        assert C.file_sha(C.HERE/name)==digest,('FROZEN_CHANGED',name)
        assert C.sha(C.historical('IntradayLab/t3_m15_early_risk_protection_v1/'+name,freeze['commit']))==digest
    return freeze

def run(root,output):
    frozen=guard();output.mkdir(parents=True,exist_ok=True)
    test=[]
    for n in ['test_execution.py','test_early.py']:
        p=subprocess.run([sys.executable,str(C.HERE/n)],capture_output=True,text=True)
        assert p.returncode==0,p.stdout+p.stderr
        test.append(re.sub(r'Ran (\d+) tests in [0-9.]+s',r'Ran \1 tests (elapsed time omitted)',p.stdout+p.stderr))
    frames,scalars,control,independent,sources=R.run(root,output)
    experiment=G.compute(frames,['EARLY_PROTECT_05']);G.persist(experiment,output/'experiment')
    tables=A.build(control,experiment,sources)
    for n,r in tables.items():C.write_csv(output/(n+'.csv'),r)
    C.write_json(output/'TABLES.json',tables)
    C.write_json(output/'SOURCE_MANIFEST.json',{'base_main':C.BASE,'data_commit':C.DATA_SHA,'sources':sources,'freeze_commit':frozen['commit'],'code_spec_sha256':frozen['code_spec_sha256'],'OHLC_2025_plus_read_or_parsed':False,'full_file_hashes':'opaque bytes only','raw_quotes_copied':False,'variants':['CONTROL','EARLY_PROTECT_05'],'labels':C.LABEL,'years':'DEVELOPMENT_EXPOSED','runtime':{'python':platform.python_version(),'pandas':pd.__version__,'numpy':np.__version__}})
    (output/'TEST_RESULTS.txt').write_text('\n'.join(test))
    print(json.dumps({'experiment_closed':len(experiment['trades']),'experiment_open':len(experiment['OPEN_POSITIONS']),'tables':{n:len(r) for n,r in tables.items()}}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,default=Path('/workspace/market-pattern-data'));p.add_argument('--output',type=Path,default=C.HERE/'results');a=p.parse_args();run(a.data_root,a.output)
