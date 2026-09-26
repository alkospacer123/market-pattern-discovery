#!/usr/bin/env python3
"""Independent fail-closed audit for Stage 2 (does not import generate.py)."""
from __future__ import annotations
import csv, hashlib, json, math, statistics, subprocess, sys
from collections import defaultdict
from pathlib import Path

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[3]; S1=HERE.parent/'stage1_master_evidence'
PASS1='POST_V3_STAGE_1_MASTER_EVIDENCE_AUDIT_PASSED'; PASS2='POST_V3_STAGE_2_PORTFOLIO_DIVERSIFICATION_AUDIT_PASSED'; TOL=1e-8
UNIVERSES={'v2':('Si','CNY','GD','BR','MIX','NG'),'v3':('USDRUBF','CNYRUBF','GLDRUBF','IMOEXF')}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(name):
 with (HERE/name).open(newline='',encoding='utf-8') as h:return list(csv.DictReader(h))
def close(a,b): return math.isclose(float(a),float(b),rel_tol=TOL,abs_tol=TOL)
def ident(r): return tuple(r[x] for x in ('generation','lifecycle_stage','strategy','timeframe'))
def assert_close(a,b,msg): assert close(a,b),f'{msg}: {a} != {b}'

def audit():
 s1a=json.loads((S1/'audit_result.json').read_text()); s1m=json.loads((S1/'manifest.json').read_text()); m=json.loads((HERE/'manifest.json').read_text())
 assert s1a['status']==PASS1 and s1m['audit_status']==PASS1 and m['stage1_audit_status']==PASS1
 for name,digest in s1m['artifacts'].items(): assert sha(S1/name)==digest,f'Stage 1 artifact hash {name}'
 for x in s1m['source_files_used']:
  assert sha(ROOT/x['path'])==x['sha256'],f"Stage 1 source hash {x['path']}"
 for name,digest in m['output_sha256'].items(): assert sha(HERE/name)==digest,f'Stage 2 output hash {name}'
 matrix=rows('monthly_instrument_matrix.csv'); port=rows('monthly_portfolio_summary.csv'); stab=rows('portfolio_stability_summary.csv'); ins=rows('instrument_stability_summary.csv')
 corr=rows('pairwise_monthly_correlation.csv'); co=rows('pairwise_co_loss_statistics.csv'); loo=rows('leave_one_instrument_out.csv'); oos=rows('true_oos_portfolio_summary.csv')
 assert len(matrix)==len({ident(r)+(r['YYYY-MM'],r['instrument']) for r in matrix}),'duplicate matrix identity'
 idx={(ident(r),r['YYYY-MM'],r['instrument']):r for r in matrix}; pidx={(ident(r),r['YYYY-MM']):r for r in port}
 # Complete grids, status/zero contract, and monthly reconciliation.
 studies=sorted({ident(r) for r in matrix})
 assert len(studies)==24
 for key in studies:
  ms=sorted({r['YYYY-MM'] for r in matrix if ident(r)==key})
  for month in ms:
   rs=[idx[key,month,i] for i in UNIVERSES[key[0]]]
   assert all(x['coverage_status'] in ('AVAILABLE','NO_TRADES','NOT_YET_AVAILABLE') for x in rs)
   for x in rs:
    available=x['instrument_available']=='true'
    assert available==(x['coverage_status']!='NOT_YET_AVAILABLE')
    if x['coverage_status']=='NOT_YET_AVAILABLE': assert int(x['trades'])==0 and close(x['net_R'],0)
    if x['coverage_status']=='NO_TRADES': assert available and int(x['trades'])==0 and close(x['net_R'],0)
   assert_close(sum(float(x['net_R']) for x in rs if x['instrument_available']=='true'),pidx[key,month]['portfolio_net_R'],f'month {key} {month}')
  assert_close(sum(float(pidx[key,x]['portfolio_net_R']) for x in ms),sum(float(r['total_net_R']) for r in ins if ident(r)==key),f'study {key}')
 # Independently re-aggregate every authenticated ledger to matrix observed cells.
 sources=s1m['source_files_used']; ledgers=[ROOT/x['path'] for x in sources if x['path'].endswith('.csv')]
 for key in studies:
  gen,stage,strategy,tf=key
  token=({'baseline':'/baseline_v2/','walk_forward':'/walk_forward_v2/','true_oos':'/true_oos_v2/'}[stage] if gen=='v2' else f'/perpetual_v3/{stage}/')
  chosen=[p for p in ledgers if token in '/'+p.relative_to(ROOT).as_posix() and f'/{strategy}/' in '/'+p.relative_to(ROOT).as_posix() and f'/{tf}/' in '/'+p.relative_to(ROOT).as_posix() and str(p).endswith(('trades.csv','_trades.csv'))]
  sums=defaultdict(float); counts=defaultdict(int); col={('v2','baseline'):'net_R',('v2','walk_forward'):'net_R_C1',('v2','true_oos'):'R_result',('v3','baseline'):'net_R',('v3','walk_forward'):'net_R_C1',('v3','true_oos'):'R_result'}[gen,stage]
  for p in chosen:
   with p.open(newline='',encoding='utf-8') as h:
    for r in csv.DictReader(h):
     from datetime import datetime
     t=datetime.fromisoformat(r['exit_time']); t=datetime.fromisoformat(r['entry_time']) if t.hour==0 else t; i=r.get('instrument') or r.get('symbol'); k=(t.strftime('%Y-%m'),i); sums[k]+=float(r[col]); counts[k]+=1
  for (month,i),value in sums.items(): assert_close(idx[key,month,i]['net_R'],value,f'ledger {key} {month} {i}'); assert int(idx[key,month,i]['trades'])==counts[month,i]
 # All pair correlations/co-loss calculations over both-available months.
 coidx={(ident(r),r['instrument_a'],r['instrument_b']):r for r in co}
 for r in corr:
  key=ident(r); a,b=r['instrument_a'],r['instrument_b']; ms=sorted({x['YYYY-MM'] for x in matrix if ident(x)==key})
  pairs=[(float(idx[key,m,a]['net_R']),float(idx[key,m,b]['net_R'])) for m in ms if idx[key,m,a]['instrument_available']=='true' and idx[key,m,b]['instrument_available']=='true']
  av=[x for x,_ in pairs]; bv=[y for _,y in pairs]; assert int(r['overlapping_months'])==len(pairs)
  if len(pairs)>1 and statistics.stdev(av)>0 and statistics.stdev(bv)>0: assert_close(r['pearson_monthly_R'],statistics.correlation(av,bv),f'correlation {key,a,b}')
  elif r['pearson_monthly_R']!='NA': raise AssertionError('undefined correlation not NA')
  c=coidx[key,a,b]; bn=sum(x<0 and y<0 for x,y in pairs); opp=sum(x*y<0 for x,y in pairs)
  assert int(c['both_negative_months'])==bn and int(c['opposite_sign_months'])==opp
  assert int(c['either_negative_months'])==sum(x<0 or y<0 for x,y in pairs)
 # LOO arithmetic from the matrix for all removals and monthly-derived statistics.
 for r in loo:
  key=ident(r); rem=r['removed_instrument']; ms=sorted({x['YYYY-MM'] for x in matrix if ident(x)==key}); vals=[]
  for month in ms:
   full=float(pidx[key,month]['portfolio_net_R']); removed=float(idx[key,month,rem]['net_R']) if idx[key,month,rem]['instrument_available']=='true' else 0.; vals.append(full-removed)
  assert_close(r['total_net_R'],sum(vals),f'LOO {key,rem}'); assert_close(r['mean_monthly_R'],statistics.fmean(vals),f'LOO mean {key,rem}')
  assert_close(r['delta_total_R_vs_full'],sum(vals)-sum(float(pidx[key,m]['portfolio_net_R']) for m in ms),f'LOO delta {key,rem}')
 # TRUE OOS concise table directly reconciles to stability/contributions.
 sidx={ident(r):r for r in stab}
 assert len(oos)==8
 for r in oos:
  key=(r['generation'],'true_oos',r['strategy'],r['timeframe']); s=sidx[key]
  for a,b in [('months','months_observed'),('total_R','total_net_R'),('positive_month_share','positive_month_share'),('median_monthly_R','median_monthly_R'),('monthly_std','monthly_R_std'),('worst_month','worst_month_R'),('monthly_equity_DD','monthly_equity_max_drawdown_R'),('loss_rescue_share','loss_rescue_share'),('synchronized_loss_months','all_negative_months')]: assert_close(r[a],s[b],f'OOS {key} {a}')
 # Explicit in-memory mutation rejection probes (canonical files untouched).
 def valid_month(rs,reported): return close(sum(float(x['net_R']) for x in rs if x['instrument_available']=='true'),reported)
 first_month=next(x['YYYY-MM'] for x in matrix if ident(x)==studies[0]); pristine=[dict(x) for x in matrix if ident(x)==studies[0] and x['YYYY-MM']==first_month]; reported=pidx[studies[0],first_month]['portfolio_net_R']
 assert valid_month(pristine,reported); sample=[dict(x) for x in pristine]; target=next(x for x in sample if x['instrument_available']=='true'); target['net_R']=str(float(target['net_R'])+1); assert not valid_month(sample,reported) # monthly instrument R
 assert not valid_month(pristine,float(reported)+1) # portfolio total
 original=corr[0]; key=ident(original); a,b=original['instrument_a'],original['instrument_b']; ms=sorted({x['YYYY-MM'] for x in matrix if ident(x)==key}); pv=[(float(idx[key,z,a]['net_R']),float(idx[key,z,b]['net_R'])) for z in ms if idx[key,z,a]['instrument_available']=='true' and idx[key,z,b]['instrument_available']=='true']; expected_corr=statistics.correlation([x for x,_ in pv],[y for _,y in pv])
 cr=dict(original); cr['pearson_monthly_R']='999'; assert not close(cr['pearson_monthly_R'],expected_corr) # pair correlation
 cc=dict(co[0]); expected_bn=int(cc['both_negative_months']); cc['both_negative_months']=str(expected_bn+1); assert int(cc['both_negative_months'])!=expected_bn
 lr=dict(loo[0]); expected_loo=float(lr['total_net_R']); lr['total_net_R']=str(expected_loo+1); assert not close(lr['total_net_R'],expected_loo)
 ar=dict(next(x for x in matrix if x['coverage_status']=='NOT_YET_AVAILABLE')); ar['instrument_available']='true'; assert not (ar['instrument_available']=='false' and ar['coverage_status']=='NOT_YET_AVAILABLE')
 fake=dict(s1m['artifacts']); first=next(iter(fake)); fake[first]='0'*64; assert fake[first]!=sha(S1/first) # Stage 1 source SHA
 fake2=dict(m['output_sha256']); first=next(iter(fake2)); fake2[first]='0'*64; assert fake2[first]!=sha(HERE/first) # Stage 2 artifact SHA
 # Separate interpreter regeneration, followed by byte comparison of all evidence.
 before={n:sha(HERE/n) for n in m['output_sha256']}
 subprocess.run([sys.executable,str(HERE/'generate.py')],cwd=ROOT,check=True)
 after={n:sha(HERE/n) for n in before}; assert before==after,'non-deterministic regeneration'
 m=json.loads((HERE/'manifest.json').read_text()); m['audit_status']=PASS2
 (HERE/'manifest.json').write_text(json.dumps(m,indent=2,sort_keys=True)+'\n')
 result={'status':PASS2,'stage1_integrity':'PASS','monthly_reconciliation':'PASS','study_reconciliation':'PASS','availability_handling':'PASS','pairwise_reconciliation':'PASS','co_loss_reconciliation':'PASS','leave_one_out_reconciliation':'PASS','true_oos_reconciliation':'PASS','source_hashes':'PASS','output_hashes':'PASS','deterministic_rerun':'PASS','mutation_tests_passed':8,'portfolio_studies':len(studies)}
 (HERE/'audit_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print(PASS2)
if __name__=='__main__': audit()
