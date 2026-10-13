"""One preregistered primary run with compulsory CONTROL and freeze gates."""
import argparse,json,platform,subprocess,sys,re
from pathlib import Path
import pandas as pd,numpy as np
import common as C,control as G,analysis as A

def freeze_guard():
    frozen=json.loads((C.HERE/'FREEZE.json').read_text());ref=frozen['commit']
    for name,h in frozen['code_spec_sha256'].items():
        assert C.file_sha(C.HERE/name)==h,('FROZEN_CODE_CHANGED',name)
        assert C.sha(C.historical('IntradayLab/t3_m15_execution_sensitivity_v1/'+name,ref))==h
    assert not C.git('ls-tree','-r','--name-only',ref,'--','IntradayLab/t3_m15_execution_sensitivity_v1/results').strip()
    return frozen

def run(root,output):
    frozen=freeze_guard();test=subprocess.run([sys.executable,str(C.HERE/'test_causal.py')],capture_output=True,text=True)
    assert test.returncode==0,test.stdout+test.stderr
    frames,sources=G.load(root);control=G.compute(frames);G.persist(control,output/'signal_close');gate=G.gate(control,output/'signal_close')
    next_open=G.compute(frames,mode='NEXT_OPEN');G.persist(next_open,output/'next_open')
    allrows={k:control[k]+next_open[k] for k in control};tables=A.build(allrows,frames)
    for name,rows in tables.items():C.write_csv(output/(name+'.csv'),rows)
    A.render(tables,output)
    pending=[r for r in next_open['entry_opportunities'] if r['decision_reason']=='UNRESOLVED_END_OF_DATA']
    skips=[r for r in next_open['entry_opportunities'] if r['decision_reason']=='SKIPPED_MISSING_ADJACENT_OPEN']
    C.write_json(output/'PENDING_SIGNALS.json',pending);C.write_csv(output/'MISSING_ADJACENT_OPEN.csv',skips)
    C.write_json(output/'SOURCE_MANIFEST.json',{'base_main':C.BASE,'data_commit':C.DATA_SHA,'sources':sources,'spec_sha256':C.file_sha(C.HERE/'SPEC.json'),
        'frozen_commit':frozen['commit'],'code_spec_sha256':frozen['code_spec_sha256'],'OHLC_2025_plus_parsed':False,
        'labels':C.LABEL,'period':'2023-2024 DEVELOPMENT_EXPOSED','runtime':{'python':platform.python_version(),'pandas':pd.__version__,'numpy':np.__version__},
        'CONTROL_status':gate['status'],'raw_quotes_copied':False})
    (output/'TEST_RESULTS.txt').write_text(re.sub(r'Ran 22 tests in [0-9.]+s','Ran 22 tests (elapsed time omitted for byte reproducibility)',test.stdout+test.stderr))
    print(json.dumps({'CONTROL':'PASS','Next_OPEN_closed':len(next_open['trades']),'Next_OPEN_terminal_OPEN':len(next_open['OPEN_POSITIONS']),'pending':len(pending),'missing_adjacent_open':len(skips)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,default=Path('/workspace/market-pattern-data'));p.add_argument('--output',type=Path,default=C.HERE/'results');a=p.parse_args();run(a.data_root,a.output)
