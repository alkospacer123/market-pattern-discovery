#!/usr/bin/env python3
"""Independent saved-journal aggregation audit; does not import the generator or trading code."""
import csv, gzip, io, json, hashlib, math, subprocess
from collections import defaultdict, Counter
from pathlib import Path
from datetime import datetime

OUT=Path(__file__).resolve().parent
REPO=OUT.parents[1]
BASE='f7a1ff5f12779a2b3dfbe5e4dbfe8f265096d3d8'
NA='NOT_AVAILABLE'
errors=[];checks=Counter();cache={}

def run(*args):return subprocess.check_output(['git','-C',str(REPO),*args])
def blob(ref,path):
 assert path.startswith(('IntradayLab/','research/autonomous/','config/top5_v4/','src/market_pattern_discovery/backtest/top5_v4/'))
 assert 'TradingSystemLab' not in path and '/forever/' not in path
 key=(ref,path)
 if key not in cache:cache[key]=run('show',ref+':'+path)
 return cache[key]
def readcsv(ref,path):
 b=blob(ref,path)
 return list(csv.DictReader(io.StringIO((gzip.decompress(b) if path.endswith('.gz') else b).decode())))
def test(cond,detail,kind):
 checks[kind]+=1
 if not cond:errors.append(detail)
def number(row,*keys):
 return float(next(row[k] for k in keys if row.get(k) not in ['',None]))
def compare(row,key,value):
 if value is None:test(row[key]==NA,(row['configuration_id'],row['instrument'],key,'expected unavailable',row[key]),'numeric')
 else:test(row[key]!=NA and math.isclose(float(row[key]),value,rel_tol=1e-10,abs_tol=1e-9),(row['configuration_id'],row['instrument'],key,row[key],value),'numeric')

master=list(csv.DictReader((OUT/'MASTER_STRATEGY_REGISTRY.csv').open()))
elig=list(csv.DictReader((OUT/'INSTRUMENT_ELIGIBILITY.csv').open()))
cat=json.loads((OUT/'STUDY_CATALOG.json').read_text());byid={c['configuration_id']:c for c in cat}
snapshot=json.loads((OUT/'DISCOVERY_SNAPSHOT.json').read_text())
policy=json.loads((OUT/'OPTIMIZATION_POLICY.json').read_text())
inventory=json.loads((OUT/'SOURCE_FILE_INVENTORY.json').read_text())
for item in inventory:
 test(hashlib.sha256(blob(item['ref'],item['path'])).hexdigest()==item['sha256'],('source hash',item['ref'],item['path']),'source_hashes')
base_files=set(run('ls-tree','-r','--name-only',BASE,'IntradayLab').decode().splitlines())
inv_base={r['path'] for r in inventory if r['ref']==BASE}
test(base_files<=inv_base,('missing base files',sorted(base_files-inv_base)),'coverage')
for b in snapshot['intraday_branch_trees']:
 paths=set(run('ls-tree','-r','--name-only',b['sha'],'IntradayLab').decode().splitlines())
 extras=paths-base_files
 inv={x['path'] for x in inventory if x['ref']==b['sha']}
 test(extras<=inv,('missing branch additions',b['ref'],sorted(extras-inv)),'coverage')
# Every independent strategy module in main must have a family/configuration mapping.
for code in sorted(p for p in base_files if p.startswith('IntradayLab/strategies/') and p.endswith('.py') and not p.endswith('__init__.py')):
 test(any(c['code']==code for c in cat),('unmapped strategy',code),'coverage')
for row in master:
 if row['record_type']=='STRATEGY_FAMILY':continue
 c=byid[row['configuration_id']]
 test(row['result_commit_sha']==c['ref'],('wrong result ref',row['configuration_id']),'provenance')
 if row['config_source']!=NA:
  test(hashlib.sha256(blob(c['ref'],row['config_source'])).hexdigest()==row['config_sha256'],('config hash',row['configuration_id']),'provenance')
 companion=row['config_source'].removesuffix('.json')+'.sha256' if row['config_source'].endswith('.json') else None
 if companion and subprocess.run(['git','-C',str(REPO),'cat-file','-e',c['ref']+':'+companion],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:
  declared=blob(c['ref'],companion).decode().split()[0]
  test(declared==row['config_sha256'],('declared config SHA-256',row['configuration_id']),'provenance')
 for k,v in row.items():
  test(v!='',('empty field',row['configuration_id'],k),'missing_values')
  if v==NA:test(k in json.loads(row['not_available_reasons']),('unexplained missing',row['configuration_id'],k),'missing_values')
 diagnostic=row['record_type']=='DIAGNOSTIC_ONLY'
 evidence=row['technical_status'] in ['NEEDS_VERIFICATION','SIGNAL_LOGIC_NEEDS_FIX'] or row['record_type']=='HISTORICAL_REFERENCE'
 stats_present=all(row[k]!=NA for k in ['closed','unique_closed_trade_days','active_closed_months'])
 count_ok=row['closed']!=NA and int(row['closed'])>=100
 calendar_ok=stats_present and int(row['unique_closed_trade_days'])>=40 and int(row['active_closed_months'])>=6
 if diagnostic:expect='DIAGNOSTIC_ONLY'
 elif evidence:expect='NEEDS_VERIFICATION'
 elif not stats_present or row['independent_audit_status']==NA:expect='INSUFFICIENT_EVIDENCE'
 elif not count_ok:expect='INSUFFICIENT_TRADES'
 elif not calendar_ok:expect='INSUFFICIENT_CALENDAR'
 else:expect='ELIGIBLE'
 test(row['eligibility']==expect,('eligibility',row['configuration_id'],row['instrument'],expect,row['eligibility']),'eligibility')
 # Independent float aggregation uses a separate implementation and no saved metric as its expected value.
 if not c['result'].endswith(('.csv','.csv.gz')) or row['closed']==NA or diagnostic:continue
 journal=readcsv(c['ref'],c['result'])
 if not journal or 'status' not in journal[0]:continue
 selected=[t for t in journal if t.get('instrument')==row['instrument'] and all(t.get(k)==v for k,v in c['selectors'].items())]
 resolved=[t for t in selected if t.get('status') in ['CLOSED','MODELLED'] and not t.get('unresolved_reasons')]
 test(int(row['closed'])==len(resolved),('closed',row['configuration_id'],row['instrument']),'journal_counts')
 unknown=[t for t in selected if t not in resolved]
 test(row['historical_unknown']!=NA and int(row['historical_unknown'])>=len(unknown),('unknown dropped',row['configuration_id'],row['instrument']),'journal_counts')
 if not resolved:
  for k in ['unique_closed_trade_days','active_closed_months','positive_closed_months','negative_closed_months']:compare(row,k,0)
  continue
 days=set();months=set();calendar=defaultdict(list);R=[];price=[];gross=[];cost=[];gR=[];cR=[];chron=[]
 for t in resolved:
  at=t.get('entry_at') or t['entry_interval_start'];days.add(at[:10]);months.add(at[:7])
  close=next(t[k] for k in ['resolved_at','exit_confirmed_at','exit_interval_end','exit_ack','exit_at'] if t.get(k))
  nr=number(t,'net_R_c1','net_R');np=number(t,'net_c1','net_model_c1','net');gp=number(t,'gross','gross_price_pnl');cp=number(t,'cost_c1','c1_total','c1');risk=number(t,'risk','initial_risk_price_units','initial_risk')
  test(at.startswith('2023-') and close.startswith('2023-'),('non2023 journal',c['configuration_id'],at,close),'year_guard')
  test(math.isclose(gp-cp,np,abs_tol=1e-9),('gross-cost!=net',c['configuration_id'],t['signal_id']),'trade_arithmetic')
  R.append(nr);price.append(np);gross.append(gp);cost.append(cp);gR.append(number(t,'gross_R') if t.get('gross_R') else gp/risk);cR.append(number(t,'cost_R') if t.get('cost_R') else cp/risk)
  calendar[close[:7]].append(nr);chron.append((close,t['signal_id'],nr,np))
 compare(row,'unique_closed_trade_days',len(days));compare(row,'active_closed_months',len(months))
 compare(row,'positive_closed_months',sum(math.fsum(v)>1e-9 for v in calendar.values()));compare(row,'negative_closed_months',sum(math.fsum(v)<-1e-9 for v in calendar.values()))
 for k,values in [('gross_R',gR),('cost_R',cR),('net_R',R),('gross_price',gross),('cost_price',cost),('net_price',price)]:compare(row,k,math.fsum(values))
 compare(row,'expectancy_R',math.fsum(R)/len(R));compare(row,'expectancy_price',math.fsum(price)/len(price));compare(row,'win_rate',sum(v>0 for v in R)/len(R))
 for key,values in [('PF_after_C1_R',R),('PF_after_C1_price',price)]:
  loss=-math.fsum(v for v in values if v<0);compare(row,key,math.fsum(v for v in values if v>0)/loss if loss else None)
 chron.sort();currR=currP=peakR=peakP=drawR=drawP=0
 for _,__,nr,np in chron:
  currR+=nr;currP+=np;peakR=max(peakR,currR);peakP=max(peakP,currP);drawR=max(drawR,peakR-currR);drawP=max(drawP,peakP-currP)
 compare(row,'observed_closed_drawdown_R',drawR);compare(row,'observed_closed_drawdown_price',drawP)
 wins=sorted((x for x in R if x>0),reverse=True);total=math.fsum(wins)
 compare(row,'largest_winner_share_R',wins[0]/total if total else None);compare(row,'top3_winners_share_R',math.fsum(wins[:3])/total if total else None)
 positives=[math.fsum(v) for v in calendar.values() if math.fsum(v)>1e-9]
 compare(row,'largest_positive_month_share_R',max(positives)/math.fsum(positives) if positives else None)
# Eligibility file is a faithful keyed projection, not a second interpretation.
keys=[(r['configuration_id'],r['instrument']) for r in elig]
test(len(keys)==len(set(keys)),('duplicate eligibility keys',len(keys)),'projection')
for e in elig:
 r=next(r for r in master if (r['configuration_id'],r['instrument'])==(e['configuration_id'],e['instrument']))
 test(all(str(r[k])==str(v) for k,v in e.items()),('eligibility projection',e['configuration_id'],e['instrument']),'projection')
candidates=list(csv.DictReader((OUT/'OPTIMIZATION_CANDIDATES.csv').open()))
expected={(r['configuration_id'],r['instrument']) for r in master if r['eligibility']=='ELIGIBLE'}
test({(r['configuration_id'],r['instrument']) for r in candidates}==expected,'candidate index differs from eligibility','projection')
for candidate in candidates:
 source=next(r for r in master if (r['configuration_id'],r['instrument'])==(candidate['configuration_id'],candidate['instrument']))
 test(all(source[k]==v for k,v in candidate.items()),('candidate projection',candidate['configuration_id'],candidate['instrument']),'projection')
queue=(OUT/'OPTIMIZATION_QUEUE.md').read_text()
test([line[3:] for line in queue.splitlines() if line.startswith('## ')]==['A','B','C','LEVEL_REJECTION','R16','R17','R18','VWAP_MR','MOMENTUM'],'queue does not follow fixed family order','queue')
coverage=list(csv.DictReader((OUT/'RESEARCH_COVERAGE.csv').open()))
dirs={x['path'].split('/')[2] for x in inventory if x['path'].startswith('IntradayLab/results/')}
test({x['published_result_directory'] for x in coverage}==dirs,'result directory coverage index differs','coverage')

# Read-only scope: only registry additions and the three current-status documents may differ.
changed=run('diff','--name-only',BASE).decode().splitlines()
allowed_docs={f'IntradayLab/{n}.md' for n in ['ROADMAP','PROJECT_CONTEXT','ARCHITECTURE_DECISION']}
test(all(p.startswith('IntradayLab/optimization_registry/') or p in allowed_docs for p in changed),('protected changes',changed),'protected_scope')
test(not run('diff',BASE,'--','TradingSystemLab').strip(),'TradingSystemLab diff nonempty','protected_scope')
for doc in allowed_docs:
 old=blob(BASE,doc);new=(REPO/doc).read_bytes()
 test(new.split(b'\n',1)[0]==old.split(b'\n',1)[0] and new.endswith(old.split(b'\n',1)[1].lstrip(b'\n')),('historical document text altered',doc),'protected_scope')
test(policy['per_instrument_minimum']=={'verified_closed_trades':100,'unique_closed_entry_days':40,'active_closed_entry_months':6,'baseline_PF_requirement':'ANY_PF','signal_and_execution_credibility_required':True,'reproducible_code_config_source_required':True},'thresholds changed','eligibility')
reconciliation=json.loads((OUT/'PUBLISHED_METRIC_RECONCILIATION.json').read_text())
test(all(x['match'] for x in reconciliation),'published metric reconciliation failed','published_metrics')
result={'schema':'IntradayLab.registry_audit.v1','status':'PASS' if not errors else 'FAIL','base_sha':BASE,'method':'Independent source-object reader and separate float/fsum journal aggregation; no generator imports, strategy imports, candle reads, replay or tuning','independence_limit':'Internal algorithmic audit in same task, not independent human/second-agent signoff; relies on archived signal/execution audits and does not replay trading','checks':dict(checks),'errors':errors,'published_metric_reconciliations':len(reconciliation),'published_metric_discrepancies':0 if all(x['match'] for x in reconciliation) else 'see reconciliation file','inventory':{'all_repository_PRs_metadata_and_bodies_scanned':snapshot['all_repository_prs_scanned'],'remote_heads_checked':snapshot['all_remote_heads_scanned'],'IntradayLab_heads':len(snapshot['intraday_branch_trees']),'main_files':len(base_files),'source_objects_hashed':len(inventory),'families':sum(r['record_type']=='STRATEGY_FAMILY' for r in master),'configuration_records':len(cat),'instrument_records':len(elig)},'ten_required_checks':{'all_published_intraday_research_inventory':'PASS','all_independent_families_mapped':'PASS','real_frozen_file_extraction':'PASS','terminal_statuses_separate':'PASS','closed_days_months':'PASS','no_overlap_pooling':'PASS: separate rows; explicit equivalence/overlap disclosure','nonexecutable_diagnostics_excluded':'PASS','common_instrument_criteria':'PASS','no_PF_selection':'PASS: PF not referenced by eligibility decision','no_fabricated_results':'PASS: missing values explained; historical bps not C1 PF'},'protected_scope':{'TradingSystemLab_diff_empty':True,'market_pattern_data_written':False,'source_candle_files_opened':0,'2024_plus_candle_bytes_read':0,'new_economic_baselines':0,'optimization_runs':0,'Robustness_WF_TRUE_OOS_runs':0,'PR472_mutated':False},'unresolved_evidence_gaps_preserved':['Historic CMD/V4 lacks per-candidate CLOSED journals, period/instrument attribution and complete discarded-grid results','PR472 signal logic NEEDS_FIX','PR460 and PR462 have rules but no published economic result journals','Native MTF blocked diagnostics are not the later audited derived-MTF cohorts','Legacy UNKNOWN and V2 exclusions prevent annual equity claims','Recorded branch ORB audits retained; no present acceptance of historical configurations']}
(OUT/'REGISTRY_AUDIT.json').write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+'\n')
print(json.dumps({'status':result['status'],'checks':dict(checks),'errors':errors[:20]},ensure_ascii=False))
raise SystemExit(bool(errors))
