"""Frozen control, causal diagnostics, then independent audit; no alternative strategy."""
import argparse,json,platform,subprocess,sys,re
from pathlib import Path
import numpy as np,pandas as pd
import common as C,run_control as R,diagnostics as D

def guard():
    f=json.loads((C.HERE/'FREEZE.json').read_text())
    for n,digest in f['code_spec_sha256'].items():
        assert C.file_sha(C.HERE/n)==digest,('FROZEN_CHANGED',n)
        assert C.sha(C.historical('IntradayLab/t3_m15_a6_s1_entry_quality_v1/'+n,f['commit']))==digest
    return f

def run(root,output):
    freeze=guard();output.mkdir(parents=True,exist_ok=True)
    test_output=[]
    for n in ('test_execution.py','test_diagnostics.py'):
        t=subprocess.run([sys.executable,str(C.HERE/n)],capture_output=True,text=True)
        assert t.returncode==0,t.stdout+t.stderr
        test_output.append(re.sub(r'Ran (\d+) tests in [0-9.]+s',r'Ran \1 tests (elapsed time omitted)',t.stdout+t.stderr))
    frames,scalars,out,independent,sources=R.run(root,output)
    # This line is unreachable before both full control implementations PASS.
    tables=D.build(out,frames,sources)
    for name,rows in tables.items():C.write_csv(output/(name+'.csv'),rows)
    C.write_json(output/'TABLES.json',tables)
    C.write_json(output/'SOURCE_MANIFEST.json',{'base_main':C.BASE,'data_commit':C.DATA_SHA,'sources':sources,'freeze_commit':freeze['commit'],'code_spec_sha256':freeze['code_spec_sha256'],'OHLC_2025_plus_read_or_parsed':False,'full_file_hashes':'opaque bytes only','raw_quotes_copied':False,'configuration':D.SPEC['configuration'],'labels':C.LABEL,'years':'DEVELOPMENT_EXPOSED','new_strategies':0,'filter_replays':0,'runtime':{'python':platform.python_version(),'pandas':pd.__version__,'numpy':np.__version__}})
    (output/'TEST_RESULTS.txt').write_text('\n'.join(test_output))
    print(json.dumps({k:len(v) for k,v in tables.items()}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,default=Path('/workspace/market-pattern-data'));p.add_argument('--output',type=Path,default=C.HERE/'results');a=p.parse_args();run(a.data_root,a.output)
