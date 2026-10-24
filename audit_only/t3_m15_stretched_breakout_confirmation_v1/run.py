"""Fresh full CONTROL gate, development replay, verification and report."""
import argparse,json,subprocess,sys,shutil,platform
from support import *
from io_utils import write_csv,write_json,read_csv,clean
import engine,analysis,verifier

def run(out,cost=0.,slippage=0.):
 assert cost>=0 and slippage>=0
 if (HERE/'CODE_FREEZE.json').exists():
  freeze=json.loads((HERE/'CODE_FREEZE.json').read_text())
  for name,expected in freeze['files'].items():assert digest(HERE/name)==expected,('CODE_CHANGED_AFTER_FREEZE',name)
 assert not out.exists(),'OUTPUT_MUST_BE_FRESH';out.mkdir(parents=True)
 subprocess.run([sys.executable,str(HERE/'control.py'),'--output',str(out/'control')],check=True)
 gate=json.loads((out/'control/CONTROL_RECONCILIATION.json').read_text());assert gate['status']=='PASS'
 p=frozen();bars={s:p.features(development_frame(s)) for s in SYMBOLS}
 models={}
 for mode in ('CONTROL','CONFIRM'):
  results=[engine.replay(bs,s,mode) for s,bs in bars.items()]
  r={k:[x for rr in results for x in ([rr[k]] if k=='occupancy' else rr[k])] for k in results[0]};models[mode]=r
  for table,rows in r.items():write_csv(out/(mode+'_'+table+'.csv'+('.gz' if table in ('signals','stops','marks') else '')),rows)
 # The modified machine must still reproduce every original frozen CONTROL field.
 import control
 fields=0
 for s,bs in bars.items():
  expected=p.replay(bs,s,'NEXT_OPEN')
  for table,rows in expected.items():
   rows=[rows] if table=='occupancy' else rows
   actual=[r for r in models['CONTROL'][table] if r['instrument']==s]
   encoded=[{k:('' if v is None else str(v)) for k,v in clean(r).items()} for r in rows]
   fields+=control.compare(actual,encoded)
 # PR562 development entries/exits, including OPEN censorship and original risk.
 archived=read_csv(archive('pr562','OUTCOME_GROUPS_M15.csv'))
 actual=models['CONTROL']['trades']+models['CONTROL']['OPEN']
 index={(t['instrument'],t['trade_id']):t for t in actual};assert len(actual)==len(archived)
 mapped={'initial_stop_price':'initial_stop','initial_risk_price':'initial_risk'}
 for a in archived:
  t=index[(a['instrument'],a['trade_id'])]
  for k in ('entry_time','entry_price','initial_stop_price','initial_risk_price','direction','exit_time','exit_price','gross_R'):
   fields+=control.compare([{k:t.get(mapped.get(k,k))}],[{k:a[k]}])
 write_json(out/'DEVELOPMENT_CONTROL.json',dict(status='PASS',compared_fields=fields,CLOSED=len(models['CONTROL']['trades']),OPEN=len(models['CONTROL']['OPEN']),PR562_development_equal=True))
 (out/'features').mkdir()
 for s,bs in bars.items():write_csv(out/'features'/f'{s}.csv.gz',[{k:v for k,v in b.items() if k not in ('Open','High','Low','Close','Volume','H1Close')} for b in bs])
 summary,monthly,transitions=analysis.calendar(models,bars,out,cost,slippage);comparison=analysis.comparisons(models,out)
 independent=verifier.verify(DATA,out,scalar());write_json(out/'INDEPENDENT_VERIFICATION.json',independent)
 import test_contract
 tests=test_contract.run();write_json(out/'SYNTHETIC_TESTS.json',tests)
 import report
 report.build(out,summary,monthly,transitions,comparison,independent)
 write_json(out/'CAPITAL_FEASIBILITY.json',dict(status='NOT_VALIDATED',risk_fraction=.015,nominal_risk_limit=.06,no_cash_inference_from_R=True,quantity_formula='floor(min(0.015*realized_equity_RUB/risk_per_lot_RUB,available_margin_RUB/dated_GO_RUB)); total reserved nominal initial risk <=0.06*realized_equity_RUB',missing=['starting capital and cashflows','dated historical GO/margin','dated contract size, tick size and tick value','verified fees, slippage, funding, settlement'],frozen_stops='UNROUNDED_RESEARCH_VALUES',normalized_cost_R=cost,normalized_slippage_R=slippage,production_parameters_modified=False))
 write_json(out/'AUDIT.json',dict(status='PASS',CONTROL=gate,development_CONTROL=json.loads((out/'DEVELOPMENT_CONTROL.json').read_text()),independent=independent,tests=tests,code_sha256={p.name:digest(p) for p in sorted(HERE.iterdir()) if p.suffix in ('.py','.md','.patch','.txt') and p.name not in ('REPORT_RU.md','SHA256SUMS')},code_freeze=json.loads((HERE/'CODE_FREEZE.json').read_text()) if (HERE/'CODE_FREEZE.json').exists() else None,runtime=dict(python=platform.python_version()),parameter_search=False,alternatives=1,development_only=True,production_access=False,external_audit='NOT_PERFORMED'))
 print('REPLAY PASS',json.dumps(summary),flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--output',type=Path,required=True);a.add_argument('--round-trip-cost-R',type=float,default=0);a.add_argument('--round-trip-slippage-R',type=float,default=0);r=a.parse_args();run(r.output.resolve(),r.round_trip_cost_R,r.round_trip_slippage_R)
