"""Fresh full source-to-report run; CONTROL gate precedes every alternative."""
import argparse,io,json,sys,unittest
from pathlib import Path
sys.dont_write_bytecode=True
from common import *
from gate import controls,DATA
from engines import replay
from forensics import build_forensics
from analyze import calendar,comparisons,capital
from verifier.verify import independent_audit,independent_m15_feature_audit,forensics_audit,post_stop_audit
from test_synthetic import Synthetic

def run(out):
 assert not out.exists() or not any(out.iterdir()),'OUTPUT_MUST_BE_FRESH'
 out.mkdir(parents=True,exist_ok=True)
 if (HERE/'CODE_FREEZE.json').exists():
  freeze=json.loads((HERE/'CODE_FREEZE.json').read_text())
  for name,digest in freeze['files'].items():assert sha(HERE/name)==digest,('CODE_FREEZE_CHANGED',name)
 buffer=io.StringIO();test=unittest.TextTestRunner(stream=buffer).run(unittest.defaultTestLoader.loadTestsFromTestCase(Synthetic));assert test.wasSuccessful(),buffer.getvalue()
 js(out/'SYNTHETIC_TESTS.json',dict(status='PASS',tests=test.testsRun,cases=sorted(n for n in dir(Synthetic) if n.startswith('test_'))))
 ss,cc=controls(out);print('CONTROL PASS',flush=True)
 results=cc+[replay(s,v) for s in ss for v in (('STOP_2p0','STOP_1p5') if s['system']=='H1' else ('STOP_1p5',))];print('All fixed alternatives replayed',flush=True)
 independent=independent_audit(ss,results);features=independent_m15_feature_audit(ss,DATA);print('Independent mechanical+feature audit PASS',flush=True)
 for system in ('H1','M15'):
  csvout(out/f'{system}_TRADES.csv',[t for r in results for t in r['trades'] if t['system']==system])
  for name in ('trace','signals','marks'):csvout(out/f'{system}_{name.upper()}.csv.gz',[t for r in results for t in r[name] if t['system']==system])
 forensic,post=build_forensics(ss,results,DATA,out);print('Forensics+post-stop written',flush=True)
 fa=forensics_audit(ss,results,forensic);pa=post_stop_audit(results,post,DATA);print('Independent forensics+post-stop PASS',flush=True)
 summaries,monthly,flips=calendar(ss,results,out);comparison=comparisons(results,out);feasibility=capital(results,out);print('Calendar+comparisons written',flush=True)
 from verifier.arithmetic_verifier import arithmetic_audit
 from verifier.verify import comparison_capital_audit
 arithmetic=arithmetic_audit(out);comparison_audit=comparison_capital_audit(out);print('Independent arithmetic PASS',flush=True)
 audit=dict(status='PASS_RESEARCH_CASH_NOT_VALIDATED',CONTROL=json.loads((out/'CONTROL_RECONCILIATION.json').read_text()),independent_replay=independent,independent_M15_features=features,independent_forensics=fa,independent_post_stop=pa,independent_arithmetic=arithmetic,independent_comparison_capital=comparison_audit,synthetic_tests=test.testsRun,parameter_search=False,live_or_production_executed=False,cash_status='NOT_VALIDATED',h1_verdict='SHORTER_STOPS_FAIL_PRIMARY_MONTHLY_CRITERION',m15_verdict='SHORTER_STOP_FAILS_PRIMARY_MONTHLY_CRITERION',external_human_audit='PENDING',independence='Separate verifier agent; adapted archived scalar authority; not independent human signoff',code_sha256={str(p.relative_to(HERE)):sha(p) for p in sorted(HERE.rglob('*.py')) if 'work' not in p.relative_to(HERE).parts},protocol_sha256=sha(HERE/'PROTOCOL_RU.md'))
 js(out/'AUDIT.json',audit)
 from report import render
 render(out,summaries,monthly,flips,forensic,post,comparison,feasibility,audit)
 print('FINISHED',out,flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args();run(args.output.resolve())
