"""CONTROL-only historical replay, then fixed accounting. Both gates precede diagnostics."""
import argparse,json,platform,re,subprocess,sys
from pathlib import Path
import numpy,pandas
import common as C,control as G,integrity as F

def run(root,output):
    frozen=F.freeze_guard();output.mkdir(parents=True,exist_ok=True)
    test=subprocess.run([sys.executable,'-m','unittest','test_execution','test_diagnostics','-v'],cwd=C.HERE,capture_output=True,text=True)
    log=re.sub(r'Ran (\d+) tests in [0-9.]+s',r'Ran \1 tests (elapsed omitted)',test.stdout+test.stderr)
    (output/'TEST_RESULTS.txt').write_text(log);assert test.returncode==0,log
    primary,sources=G.load(root);scalar,_=G.load(root,True)
    feature=G.feature_gate(primary,scalar,output)
    out=G.compute(primary,['TRAIL_375']);G.persist(out,output/'control');gate=G.gate(out,output/'control');multi=G.multi_gate(out,output/'control')
    independent=G.compute(scalar,['TRAIL_375'],True);G.persist(independent,output/'control_scalar');sgate=G.gate(independent,output/'control_scalar',True);smulti=G.multi_gate(independent,output/'control_scalar')
    C.write_json(output/'CAUSAL_INVARIANTS.json',F.causal(out))
    print(json.dumps({'CONTROL':gate['status'],'scalar_CONTROL':sgate['status'],'PR506_508':multi['status'],'scalar_PR506_508':smulti['status'],'FEATURE':feature['status']}),flush=True)
    import analysis as A,report as R
    tables=A.build(out)
    for name,rows in tables.items():C.write_csv(output/(name+'.csv'),rows)
    C.write_json(output/'TABLES.json',tables);R.render(tables,output)
    origin=json.loads((C.HERE/'SOURCE_ORIGIN.json').read_text())
    for name in ['engine.py','scalar.py','primary_metrics.py','scalar_metrics.py']:
        assert C.file_sha(C.HERE/name)==origin['unchanged_files'][name]['sha256']
    C.write_json(output/'SOURCE_MANIFEST.json',{'base_main':C.BASE,'data_commit':C.DATA_SHA,'sources':sources,'freeze_commit':frozen['commit'],
        'code_spec_sha256':frozen['code_spec_sha256'],'CONTROL_primary':gate['status'],'CONTROL_scalar':sgate['status'],
        'full_frozen_journals_PR505_508':'PASS','FEATURE_CONTROL':feature['status'],'OHLC_2025_plus_read_or_parsed':False,
        'full_file_hashes':'opaque bytes only','raw_quotes_copied':False,'trading_replays':'unchanged CONTROL only, both implementations',
        'sensitivity':'arithmetic on unchanged trajectories, no new replay','period':'2023-2024 DEVELOPMENT_EXPOSED','labels':C.LABEL,
        'runtime':{'python':platform.python_version(),'numpy':numpy.__version__,'pandas':pandas.__version__}})
    print(json.dumps({'tables':{k:len(v) for k,v in tables.items()}}),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--data-root',type=Path,default=Path('/workspace/market-pattern-data'));parser.add_argument('--output',type=Path,default=C.HERE/'results')
    args=parser.parse_args();run(args.data_root,args.output)
