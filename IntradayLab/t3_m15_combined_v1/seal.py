"""Final presentation repeat, scope guard and complete artifact inventory."""
import json
from pathlib import Path
import subprocess
import sys
from engine import E,HERE,MAIN


def js(path,value):path.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')


def main(data_root):
    before=json.loads((HERE/'PRESENTATION_SHA256.json').read_text())
    subprocess.run([sys.executable,str(HERE/'render_report.py')],check=True)
    after=json.loads((HERE/'PRESENTATION_SHA256.json').read_text());assert before==after
    assert all(E.sha_file(HERE/n)==h for n,h in after.items())
    js(HERE/'PRESENTATION_REPEATABILITY.json',{'status':'PASS','fresh_process':True,'files_compared':len(before),'byte_sha256_identical':True})
    repo=HERE.parent.parent
    changed=E.git(repo,'diff','--name-only',MAIN).splitlines()
    status=E.git(repo,'status','--porcelain=v1','--untracked-files=all').splitlines()
    assert all(p.startswith('IntradayLab/t3_m15_combined_v1/') for p in changed)
    assert all(line[3:].startswith('IntradayLab/t3_m15_combined_v1/') for line in status)
    assert E.git(data_root,'status','--porcelain')=='' and E.git(data_root,'rev-parse','HEAD')==E.DATA_COMMIT
    prereg=json.loads((HERE/'PREREGISTRATION.json').read_text())
    for n,h in prereg['read_only_reference_sha256'].items():assert E.sha_file(repo/n)==h
    for n,h in prereg['implementation_sha256'].items():assert E.sha_file(HERE/n)==h
    js(HERE/'SCOPE_CHECK.json',{'status':'PASS','base_main':MAIN,'allowed_prefix':'IntradayLab/t3_m15_combined_v1/',
        'out_of_scope_changes':[],'data_clean_and_pinned':True,'frozen_sources_unchanged':True,'code_unchanged_since_preregistration':True,
        'merge':False,'auto_merge':False,'2025_plus_OHLC_parsed':False,'labels':['GROSS_ONLY','COSTS_DEFERRED','NOT_LIVE_READY']})
    paths=sorted(p for p in HERE.rglob('*') if p.is_file() and not p.is_relative_to(HERE/'work') and '__pycache__' not in p.parts and p.name!='ARTIFACT_SHA256.json')
    js(HERE/'ARTIFACT_SHA256.json',{str(p.relative_to(HERE)):E.sha_file(p) for p in paths})
    print(json.dumps({'sealed':True,'artifact_count':len(paths),'scope':'PASS'}))


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True);main(p.parse_args().data_root)
