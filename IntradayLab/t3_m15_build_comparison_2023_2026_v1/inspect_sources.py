"""Supplemental source-origin, exact rule and frozen-test receipts."""
import argparse,hashlib,json,re,subprocess,sys,os
from pathlib import Path
from registry import HERE,ROOT,MAIN,PIN,PR513,CATALOG,builds,folder
from io_utils import write_json,write_csv,hash_file
EXIT={
 'CONTROL':'ATR trailing immediately after each survived completed post-entry bar; old Stop first; next observed bar effective',
 'A1':'First survived post-entry completed bar closes wrong side of breakout level -> queued next observed Open; protective Open-gap Stop wins ties',
 'A2':'Two consecutive wrong-side Closes within first four post-entry bars -> queued next observed Open; protective Open-gap Stop wins ties',
 'S1':'Activate only after completed survived bar favorable extreme >=1 immutable initial R; then accumulated extreme +/- fixed trail ATR; next observed bar effective',
 'S2':'Original immediate ATR trail plus BE boundary at entry after >=1 initial R, survived-bar activation, next-bar effective',
 'S3':'Original immediate ATR trail plus entry+side*1R floor after >=2 initial R, survived-bar activation, next-bar effective',
 'EARLY_PROTECT_05':'S1 trail plus entry-side*0.5R boundary after >=0.5R on survived completed bar; next observed bar effective'}
INITIAL={'2ATR':'Actual entry - side*2*completed signal ATR; immutable initial R',
 'I1':'Signal Low for LONG, High for SHORT, no buffer',
 'I2':'PriorHigh for LONG, PriorLow for SHORT, Donchian20 shift(1), no buffer',
 'I3':'Tighter of original 2ATR Stop and signal candle extreme; no widening, no buffer'}
def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args])
def inspect(out,data_root):
 dest=out/'supplemental';dest.mkdir(exist_ok=True);prs=json.loads((HERE/'PR_SOURCES.json').read_text());checks=[];origins=[];matrix=[]
 for b in builds():
  sha=prs[str(b['source_PR'])]['head_sha']
  for rel in (b['source_path']+'/engine.py',b['spec_path']):
   raw=git('show',sha+':'+rel);assert raw==(ROOT/rel).read_bytes(),('ORIGIN_SOURCE_CHANGED',rel)
   checks.append(dict(build_id=b['build_id'],source_PR=b['source_PR'],origin_commit=sha,path=rel,sha256=hashlib.sha256(raw).hexdigest(),direct_bytes_equal=True))
  for pr in b['aliases']:origins.append(dict(build_id=b['build_id'],PR=pr,commit=prs[str(pr)]['head_sha'],PR_url=prs[str(pr)]['url']))
  matrix.append(dict(build_id=b['build_id'],entry_filter=b['entry_filter'],exit_mechanism=EXIT[b['exit']],initial_stop=INITIAL[b['initial']],trailing_ATR=b['trail'],execution=b['mode'],config_identity=b['config_identity'],configuration=json.dumps(b['config'],sort_keys=True)))
 write_csv(dest/'BUILD_ORIGINS.csv',origins);write_csv(dest/'RULE_DEFINITIONS.csv',matrix)
 write_json(dest/'ORIGIN_CODE_SPEC_CHECKS.json',dict(status='PASS',checks=checks,count=len(checks)))
 archive='211085db6e884bc7625f464fb6da11452b0fd7ef';prefix='IntradayLab/t3_m15_a6_s1_robustness_v1';files=git('ls-tree','-r','--name-only',archive,prefix).decode().splitlines()
 write_json(dest/'PR509_ARCHIVED_EVIDENCE.json',dict(commit=archive,PR_state='CLOSED_NOT_MERGED',status='DIAGNOSTIC_ONLY',audit=json.loads(git('show',archive+':'+prefix+'/results/AUDIT_STATUS.json')),artifacts=[dict(path=p,sha256=hashlib.sha256(git('show',archive+':'+p)).hexdigest()) for p in files],haircuts_replayed=False,new_strategy=False))
 assert subprocess.check_output(['git','-C',str(data_root),'rev-parse','HEAD'],text=True).strip()==PIN
 assert not subprocess.check_output(['git','-C',str(data_root),'status','--porcelain'],text=True).strip()
 manifest=json.loads((out/'SOURCE_MANIFEST.json').read_text())
 for x in manifest['source_receipts']:assert hash_file(data_root/x['path'])==x['sha256']
 assert git('rev-parse','HEAD:TradingSystemLab').strip()==git('rev-parse',MAIN+':TradingSystemLab').strip()
 write_json(dest/'CODE_PROVENANCE.json',dict(status='PASS',frozen_code_origin_bytes_equal=True,comparison_core=[dict(path=str(p.relative_to(ROOT)),sha256=hash_file(p)) for p in sorted(HERE.glob('*.py'))],spec_sha256=hash_file(HERE/'COMPARISON_SPEC.json'),data_pin=PIN,PR513_source_pin=PR513,TradingSystemLab_tree_unchanged=True))
 tests=[]
 for group in CATALOG:
  p=subprocess.run([sys.executable,str(HERE/'frozen_tests.py'),'--group',group],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env=os.environ|{'PYTHONDONTWRITEBYTECODE':'1'},check=True)
  (dest/(group+'_TESTS.log')).write_text(p.stdout);n=int(re.search(r'Ran (\d+) tests?',p.stdout).group(1));tests.append(dict(group=group,tests=n,status='PASS'))
 p=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(HERE),'-p','test_source_guard.py'],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env=os.environ|{'PYTHONDONTWRITEBYTECODE':'1'},check=True)
 (dest/'SOURCE_GUARD_TESTS.log').write_text(p.stdout);tests.append(dict(group='new_exclusive_cutoff_read_spy',tests=int(re.search(r'Ran (\d+) tests?',p.stdout).group(1)),status='PASS'))
 assert sum(x['tests'] for x in tests)==263
 write_json(dest/'TESTS.json',dict(status='PASS',total_tests=263,suites=tests,temp_files='Redirected to /workspace/work; original frozen tests and artifacts unchanged'))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--data-root',type=Path,required=True);a=p.parse_args();inspect(a.output,a.data_root)
