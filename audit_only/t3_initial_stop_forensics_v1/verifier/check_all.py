"""Pre-freeze integration check, exact registered variants only; not primary runner."""
import sys,json
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;STUDY=HERE.parent
sys.path.insert(0,str(STUDY))
from common import csvout,js
from gate import controls,DATA
from engines import replay
from forensics import build_forensics
from analyze import calendar,comparisons,capital
from verifier.verify import independent_audit,forensics_audit,post_stop_audit,arithmetic_audit

def run():
    out=STUDY/'work/verifier/full';out.mkdir(parents=True,exist_ok=True)
    streams,control=controls(out)
    variants=[replay(s,v) for s in streams for v in (('STOP_2p0','STOP_1p5') if s['system']=='H1' else ('STOP_1p5',))]
    results=control+variants;execution=independent_audit(streams,results);print('Independent execution PASS',flush=True)
    rows,post=build_forensics(streams,results,DATA,out);print('Forensics primary complete',flush=True)
    forensics=forensics_audit(streams,results,rows);print('Independent excursions PASS',flush=True)
    poststop=post_stop_audit(results,post,DATA);print('Independent poststop PASS',flush=True)
    calendar(streams,results,out);comparisons(results,out);capital(results,out)
    for system in ('H1','M15'):csvout(out/f'{system}_MARKS.csv.gz',[m for r in results for m in r['marks'] if m['system']==system])
    arithmetic=arithmetic_audit(out);print('Independent arithmetic PASS',flush=True)
    receipt=dict(status='PASS',stage='PRE_FREEZE_INTEGRATION_ONLY',execution=execution,forensics=forensics,poststop=poststop,arithmetic=arithmetic)
    js(HERE/'PRE_FREEZE_ALL_VERIFIER.json',receipt);print(json.dumps(receipt,indent=2),flush=True)
if __name__=='__main__':run()
