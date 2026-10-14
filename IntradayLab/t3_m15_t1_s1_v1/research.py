"""Fixed pre-registered execution; no parameter or mechanism search."""
import argparse
import csv
import io
import json
import platform
from pathlib import Path
import subprocess
import sys
import numpy as np
import pandas as pd
import independent as C
import engine as E
import reports as R

def tests():
    logs=[]
    for name in ('test_causal.py','test_combination.py'):
        r=subprocess.run([sys.executable,str(C.HERE/name)],capture_output=True,text=True)
        logs.append(r.stdout+r.stderr)
        assert r.returncode==0,logs[-1]
    return '\n'.join(logs)

def freeze_guard():
    f=json.loads((C.HERE/'FREEZE.json').read_text());ref=f['freeze_commit']
    committed=json.loads(C.historical('IntradayLab/t3_m15_t1_s1_v1/EXPERIMENT_SPECS.json',ref))
    assert committed==json.loads((C.HERE/'EXPERIMENT_SPECS.json').read_text())
    for name,digest in f['code_and_spec_SHA256'].items():
        assert C.file_sha(C.HERE/name)==digest
        assert C.sha(C.historical('IntradayLab/t3_m15_t1_s1_v1/'+name,ref))==digest,('UNFROZEN_CODE',name)
    assert not C.git('ls-tree','-r','--name-only',ref,'--','IntradayLab/t3_m15_t1_s1_v1/results').strip(),'RESULTS_AT_FREEZE'
    return f

def benchmark_gate(t,o,d,e,output):
    compare=C.Comparison();detail=[]
    refs=[('490_CONTROL','CONTROL','IntradayLab/t3_m15_forever_v1/trades.csv'),
        ('495_CONTROL','CONTROL','IntradayLab/t3_m15_entry_regime_v1/results/trades_CONTROL.csv'),
        ('499_CONTROL','CONTROL','IntradayLab/t3_m15_session_entry_v1/results/trades_CONTROL.csv'),
        ('499_T1','T1','IntradayLab/t3_m15_session_entry_v1/results/trades_T1.csv'),
        ('496_S1','S1','IntradayLab/t3_m15_stop_exit_v1/results/trades.csv')]
    excluded=('C1_R','net_R','c1_price_unit','initial_risk_ticks')
    for name,rule,path in refs:
        r=C.reference(path)
        if name=='496_S1':r=[x for x in r if x['rule']=='S1']
        a=[x for x in t if x['rule']==rule]
        compare.rows(a,r,name,['version','instrument','entry_time'],excluded)
    for name,rule,path in [('490_OPEN','CONTROL','IntradayLab/t3_m15_forever_v1/OPEN_POSITIONS.json'),
        ('495_OPEN','CONTROL','IntradayLab/t3_m15_entry_regime_v1/results/CONTROL_OPEN_POSITIONS.json'),
        ('499_OPEN','T1','IntradayLab/t3_m15_session_entry_v1/results/OPEN_POSITIONS.json'),
        ('496_OPEN','S1','IntradayLab/t3_m15_stop_exit_v1/results/OPEN_POSITIONS.json')]:
        r=json.loads(C.historical(path))
        if name in ('499_OPEN','496_OPEN'):r=[x for x in r if x['rule']==rule]
        compare.rows([x for x in o if x['rule']==rule],r,name,['version','instrument'],('exit_C1_and_funding',))
    # The S1 Stop and signal decisions are also reproduced against #496.
    for name,actual,path,keys in [('496_S1_STOPS',d,'stop_decisions.csv',['version','instrument','bar_close_time']),
        ('496_S1_ENTRIES',e,'entry_opportunities.csv',['version','instrument','signal_time'])]:
        ref=C.reference('IntradayLab/t3_m15_stop_exit_v1/results/'+path)
        compare.rows([x for x in actual if x['rule']=='S1'],[x for x in ref if x['rule']=='S1'],name,keys)
    expected={'CONTROL':(741,701),'S1':(718,689),'T1':(568,549)}
    for rule,counts in expected.items():
        for v,n in zip(C.VERSIONS,counts):
            actual=sum(x['rule']==rule and x['version']==v for x in t)
            compare.value(actual,n,'EXPECTED_'+rule,v,'closed')
            detail.append({'rule':rule,'version':v,'closed':actual,'terminal_OPEN':sum(x['rule']==rule and x['version']==v for x in o)})
    C.write_csv(output/'BENCHMARK_DIFF.csv',compare.diffs,['table','row','field','actual','expected'])
    result={'status':'PASS' if not compare.diffs else 'FAIL','labels':C.LABEL,'2023_2024':'DEVELOPMENT_EXPOSED',
        'all_common_gross_fields':True,'absolute_tolerance':1e-8,'counts':detail,'fields_compared':compare.fields,
        'differences':len(compare.diffs),'maximum_differences':compare.maxima,'tables':compare.tables}
    C.write_json(output/'BENCHMARK_REPRODUCTION.json',result)
    assert result['status']=='PASS','REFERENCE_MISMATCH_COMBINATION_BLOCKED'
    return result

def run(root,output,benchmarks=False):
    assert output.resolve().is_relative_to(C.HERE)
    output.mkdir(parents=True,exist_ok=True)
    gate=json.loads((C.HERE/'audit_499/AUDIT_RESULT.json').read_text())
    assert gate['status']=='PASS' and gate['discrepancies']==0
    specs=json.loads((C.HERE/'EXPERIMENT_SPECS.json').read_text())
    assert specs['name']=='T3_M15_T1_S1_COMBINED_V1' and specs['data_commit']==C.DATA_SHA
    for version,trail in C.VERSIONS.items():
        assert specs['configurations'][version]=={'ema_period':75,'slope_lookback':5,'adx_period':14,'adx_threshold':20,
            'atr_period':14,'atr_average_period':20,'breakout_period':20,'stop_atr':2.,'trail_atr':trail,'S1_activation_initial_R':1.}
    assert specs['entry_T1']=={'from_PR':499,'completed_Close_tz':'Europe/Moscow','inclusive_start':'10:00','exclusive_end':'18:00'}
    if not benchmarks:
        frozen=freeze_guard();pre=json.loads((C.HERE/'PRE_COMBINATION_GATE.json').read_text())
        assert pre['status']=='PASS' and pre['freeze_commit']==frozen['freeze_commit'] and pre['combination_results_absent']
    assert C.git('rev-parse','HEAD',root=root).decode().strip()==C.DATA_SHA
    assert not C.git('status','--porcelain',root=root).strip(),'DATA_DIRTY'
    frames={};source_manifest=[]
    for source in specs['sources']:
        path=root/source['path']
        assert C.file_sha(path)==source['full_sha256']
        assert C.git('hash-object','--',str(path),root=root).decode().strip()==source['git_blob_sha']
        raw=E.read_source(path);s=source['instrument']
        assert len(raw)==source['used_candles'] and raw.index[0].isoformat()==source['first_close'] and raw.index[-1].isoformat()==source['last_close']
        frames[s]=E.features(raw);source_manifest.append(source)
    t,o,d,e,g,sn=[],[],[],[],[],[]
    def replay(rule):
        for v in C.VERSIONS:
            for s in C.SYMBOLS:
                tt,op,ss,ee,gg,nn=E.replay(frames[s],s,v,rule)
                t.extend(tt);d.extend(ss);e.extend(ee);g.extend(gg);sn.extend(nn)
                if op:o.append(op)
    for rule in ('CONTROL','S1','T1'):replay(rule)
    benchmark=benchmark_gate(t,o,d,e,output)
    if not benchmarks:replay('COMBINED')
    rules=('CONTROL','S1','T1') if benchmarks else E.RULES
    for name,rows in [('trades',t),('stop_decisions',d),('entry_opportunities',e),('observed_gaps',g)]:C.write_csv(output/(name+'.csv'),rows)
    for rule in rules:C.write_csv(output/f'trades_{rule}.csv',[r for r in t if r['rule']==rule])
    C.write_json(output/'OPEN_POSITIONS.json',o);C.write_json(output/'PERIOD_END_OPEN_POSITIONS.json',sn)
    C.write_json(output/'SOURCE_MANIFEST.json',{'data_commit':C.DATA_SHA,'base_main':specs['base_main'],'sources':source_manifest,
        'future_OHLC_parsed':False,'labels':C.LABEL,'2023_2024':'DEVELOPMENT_EXPOSED',
        'runtime':{'python':platform.python_version(),'pandas':pd.__version__,'numpy':np.__version__},
        'spec_SHA256':C.file_sha(C.HERE/'EXPERIMENT_SPECS.json'),
        'code_SHA256':{p.name:C.file_sha(p) for p in sorted(C.HERE.glob('*.py'))},
        'freeze_commit':None if benchmarks else frozen['freeze_commit']})
    tables=R.build(t,o,sn,e,g,frames,rules)
    for name,rows in tables.items():C.write_csv(output/(name+'.csv'),rows)
    R.render(tables,output)
    C.write_json(output/'GENERATED_SHA256.json',{p.name:C.file_sha(p) for p in sorted(output.iterdir()) if p.is_file() and p.name!='GENERATED_SHA256.json'})
    print(json.dumps({'reference_gate':benchmark['status'],'combination_calculated':not benchmarks,'closed_total':len(t),'terminal_OPEN':len(o)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True);p.add_argument('--output',type=Path,default=C.HERE/'results');p.add_argument('--benchmarks-only',action='store_true')
    a=p.parse_args();run(a.data_root,a.output,a.benchmarks_only)
