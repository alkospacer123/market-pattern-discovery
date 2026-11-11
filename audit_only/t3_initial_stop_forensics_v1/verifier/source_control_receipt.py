"""Independent read-only SHA receipts and archived CONTROL arithmetic.

No strategy/robot imports. Does not supply archived trades to any replay.
"""
import csv,hashlib,io,json,math,subprocess
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
ARCH=HERE.parent/'work/pr557'
DATA=Path('/workspace/market-pattern-data')
MAIN='38489db7e69336548a583f968f13aab49c20913b'
PR557='5836971e7ff8e472d8128c675c4f837b40a036ef'

def git(*args,root=ROOT): return subprocess.check_output(['git','-C',str(root),*args])
def sha(raw):return hashlib.sha256(raw).hexdigest()
def rows(p):return list(csv.DictReader(p.open()))
def run():
    checks=[]
    for line in (ARCH/'SHA256SUMS').read_text().splitlines():
        digest,name=line.split('  ',1);actual=sha((ARCH/name).read_bytes())
        assert digest==actual,('ARCHIVE_SHA256',name)
        original=git('show',PR557+':audit_only/t3_h1_m15_partial_tp_2r_50/'+name)
        assert (ARCH/name).read_bytes()==original,('ARCHIVE_BYTES',name)
        checks.append({'scope':'PR557','path':name,'sha256':actual,'status':'PASS'})
    archive518=ROOT/'IntradayLab/t3_m15_t1_entry_retest_v1'
    for line in (archive518/'SHA256SUMS').read_text().splitlines():
        digest,name=line.split('  ',1);raw=(archive518/name).read_bytes();assert digest==sha(raw),('PR518_SHA256',name)
        assert raw==git('show','d85cf85083d6fea047a1a960c9ead441f7b4a6ed:IntradayLab/t3_m15_t1_entry_retest_v1/'+name),('PR518_BYTES',name)
        checks.append({'scope':'PR518','path':name,'sha256':sha(raw),'status':'PASS'})
    manifest=json.loads((ARCH/'SOURCE_MANIFEST.json').read_text())
    for path,expected in manifest['source_files'].items():
        actual=sha((ROOT/path).read_bytes());assert actual==expected['sha256'],('MAIN_SHA256',path)
        assert git('show',MAIN+':'+path)==(ROOT/path).read_bytes(),('MAIN_BYTES',path)
        checks.append({'scope':'FROZEN_SOURCE','path':path,'sha256':actual,'status':'PASS'})
    for d in manifest['data']:
        raw=git('show',d['commit']+':'+d['path'],root=DATA);assert sha(raw)==d['sha256'],('PINNED_DATA',d)
        checks.append({'scope':'DATA_COMMIT','system':d['system'],'path':d['path'],'commit':d['commit'],'sha256':sha(raw),'status':'PASS'})
    expected={'H1':(355,141,172.416620,2.206747),'M15':(1114,356,390.442918,1.778435)}
    summary={}
    for system in ('H1','M15'):
        ts=[t for t in rows(ARCH/(system+'_TRADES.csv')) if t['variant']=='CONTROL' and t['status']=='CLOSED' and t['lifecycle']!='walk_forward']
        rs=[float(t['gross_R']) for t in ts];pos=math.fsum(r for r in rs if r>0);neg=-math.fsum(r for r in rs if r<0)
        got=(len(ts),sum(t['exit_reason']=='INITIAL_STOP' for t in ts),math.fsum(rs),pos/neg)
        e=expected[system];assert got[:2]==e[:2] and all(abs(a-b)<.0000005 for a,b in zip(got[2:],e[2:])),('ARCHIVE_AGGREGATES',system,got,e)
        summary[system]={'closed':got[0],'initial_stop':got[1],'gross_R':got[2],'gross_PF':got[3],'lifecycle_counts':dict(Counter(t['lifecycle'] for t in ts))}
    wf=[t for t in rows(ARCH/'H1_TRADES.csv') if t['variant']=='CONTROL' and t['status']=='CLOSED' and t['lifecycle']=='walk_forward']
    summary['H1_WF']={'closed':len(wf),'gross_R':math.fsum(float(t['gross_R']) for t in wf),'fold_counts':dict(Counter(t['fold_id'] for t in wf))}
    result={'status':'PASS_ARCHIVED_SOURCE_AND_ARITHMETIC','sha256_checks':len(checks),'checks':checks,'CONTROL_archive_arithmetic':summary,'not_yet_claimed':'Independent fresh full replay reconciliation; this receipt only authenticates archived source bytes and archived CONTROL arithmetic','source_data_copied':False,'production_imports_or_execution':False}
    (HERE/'SOURCE_CONTROL_RECEIPT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='checks'},sort_keys=True))
if __name__=='__main__':run()
