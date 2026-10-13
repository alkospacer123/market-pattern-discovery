"""After Git freeze, before any historical combination result: strict gates."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import independent as I
from research import tests, freeze_guard

def run(root):
    frozen=freeze_guard()
    assert not (I.HERE/'results').exists(),'RESULTS_ALREADY_EXIST'
    assert not (I.HERE/'independent_results').exists(),'INDEPENDENT_COMBINATION_ALREADY_EXISTS'
    gate=json.loads((I.HERE/'audit_499/AUDIT_RESULT.json').read_text())
    assert gate['status']=='PASS' and I.file_sha(I.HERE/'audit_499/AUDIT_RESULT.json')==json.loads((I.HERE/'EXPERIMENT_SPECS.json').read_text())['first_gate_result_SHA256']
    log=tests();(I.HERE/'TEST_FREEZE.txt').write_text(log)
    target=I.HERE/'work/postfreeze_benchmarks';ind=I.HERE/'work/postfreeze_independent_benchmarks'
    for script,args,filename in [('research.py',['--output',str(target),'--benchmarks-only'],'POSTFREEZE_BENCHMARK_LOG.txt'),
        ('verify.py',['--target',str(target),'--output',str(ind),'--benchmarks-only'],'POSTFREEZE_INDEPENDENT_BENCHMARK_LOG.txt')]:
        r=subprocess.run([sys.executable,str(I.HERE/script),'--data-root',str(root),*args],capture_output=True,text=True)
        (I.HERE/filename).write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr
    b=json.loads((target/'BENCHMARK_REPRODUCTION.json').read_text());a=json.loads((ind/'AUDIT_RESULT.json').read_text())
    assert b['status']==a['status']=='PASS' and not a['combination_checked']
    I.write_json(I.HERE/'BENCHMARK_REPRODUCTION.json',b);I.write_json(I.HERE/'INDEPENDENT_BENCHMARK_REPRODUCTION.json',a)
    (I.HERE/'BENCHMARK_DIFF.csv').write_bytes((target/'BENCHMARK_DIFF.csv').read_bytes())
    (I.HERE/'INDEPENDENT_BENCHMARK_DIFF.csv').write_bytes((ind/'DISCREPANCIES.csv').read_bytes())
    I.write_json(I.HERE/'PRE_COMBINATION_GATE.json',{'status':'PASS','labels':I.LABEL,'2023_2024':'DEVELOPMENT_EXPOSED',
        'freeze_commit':frozen['freeze_commit'],'first_gate':'PASS','benchmarks':'PASS','independent_benchmarks':'PASS',
        'causal_tests':'PASS','causal_test_count':40,'combination_results_absent':True,'all_common_gross_fields_tolerance':1e-8,
        'benchmark_SHA256':I.file_sha(I.HERE/'BENCHMARK_REPRODUCTION.json'),'independent_benchmark_SHA256':I.file_sha(I.HERE/'INDEPENDENT_BENCHMARK_REPRODUCTION.json'),
        'first_gate_SHA256':I.file_sha(I.HERE/'audit_499/AUDIT_RESULT.json'),'tests_SHA256':I.file_sha(I.HERE/'TEST_FREEZE.txt')})
    print(json.dumps({'pre_combination_gate':'PASS','freeze_commit':frozen['freeze_commit'],'combination_results_absent':True}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True);a=p.parse_args();run(a.data_root)
