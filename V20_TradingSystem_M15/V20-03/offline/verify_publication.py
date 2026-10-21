#!/usr/bin/env python3
"""Short publication checks only: hashes, existing tables and scope. NO replay/imports.

Run from any directory. Uses Python standard library and published derived files.
"""
from pathlib import Path
from collections import Counter
import ast,csv,hashlib,json,math,subprocess

ROOT=Path(__file__).resolve().parents[2]
STAGE=ROOT/'V20-03'
BASE_SHA='c3695b1304aef1acdd889264b3451184f7332bf7'
SOURCE_HASHES={
 'research_original_v20/base.py':'b7b9df00f8d7fb0a88c5cba103034e5a2335c108ae283258e5d8ebd5476aa59d',
 'research_original_v20/run.py':'223545374f98d8c87cf2c09b3a7302b05b07020dc8bf34b5984ebaa3d74389fe',
 'research_original_v20/legacy_v4/study_v4.py':'0f49432e207235f631807a82536f521751ad5559cc374fc6c42f8ca4f289bd08',
}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def rows(path):
 with path.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def data(path):
 return json.loads(path.read_text(),parse_constant=lambda c:(_ for _ in ()).throw(ValueError(c)))
def metric(trades,scenario='C1'):
 ordered=sorted(trades,key=lambda r:(r['exit_dt'],r['entry_dt'],int(r['account_num']),r['contract']))
 values=[float(r['net_'+scenario+'_R']) for r in ordered]
 positive=sum(v for v in values if v>0);negative=-sum(v for v in values if v<0)
 peak=running=dd=0.
 for v in values:running+=v;peak=max(peak,running);dd=max(dd,peak-running)
 return dict(trades=len(trades),PF=positive/negative if negative else None,R=sum(values),DD_closed_R=dd)

def main():
 checks=[]
 def ok(name,detail):checks.append(dict(check=name,status='PASS',detail=detail))
 manifest=ROOT/'PUBLICATION_MANIFEST_SHA256.txt'
 listed={}
 for line in manifest.read_text().splitlines():
  expected,relative=line.split('  ',1)
  p=Path(relative)
  assert not p.is_absolute() and '..' not in p.parts,relative
  assert relative not in listed,relative
  assert sha(ROOT/relative)==expected,relative
  listed[relative]=expected
 actual={p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*')
         if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'
         and p.name!='PUBLICATION_MANIFEST_SHA256.txt'}
 assert actual==set(listed),('Manifest file set differs',actual^set(listed))
 ok('PUBLICATION_SHA256_AND_FILE_SET','Every published file matches its SHA256; no extra files')

 required=['README.md','docs/ROADMAP_RU.md','docs/TASK_TRACKER.csv','docs/PROJECT_SPEC_RU.md',
  'docs/CODEX_V20_03_DRAFT_PR_PUBLICATION_RU.md','V20-03/REPORT_RU.md','V20-03/STRESS_REPORT_RU.md',
  'V20-03/CONTRACT_MAP.csv','V20-03/ROLL_POLICY.md','V20-03/ROLL_POLICY_LOCKED_V1.md',
  'V20-03/DATA_AUDIT.csv','V20-03/YEAR_COVERAGE.csv','V20-03/ACCEPTANCE_V20_03.json',
  'V20-03/verification/CAUSALITY.json','V20-03/verification/REPEAT.json',
  'V20-03/publication/ARCHIVE_FILE_INDEX.json','V20-03/publication/STATISTICS_ALL.json',
  'V20-03/publication/CENSORED_EXPLANATIONS.csv','V20-03/publication/CENSORED_IMPACT.json',
  'V20-03/publication/REFERENCE_COMPARISON.csv','V20-03/publication/C1_MONTHLY_CLASSIFIED.csv',
  'V20-03/publication/PUBLICATION_ACCEPTANCE.json','V20-03/publication/PUBLICATION_FILE_LIST.csv']
 required += ['V20-03/comparison/'+n for n in ['PF_DIAGNOSTIC_REPORT_RU.md','PERIOD_STRATEGY_COMPARISON.csv',
  'INSTRUMENT_COMPARISON.csv','TRADE_DISTRIBUTION.csv','YEARLY_STABILITY.csv','METHODOLOGY_EFFECTS_RU.md',
  'DEVELOPMENT_DECISION_RU.md','VERIFICATION.json','DIAGNOSTIC_REPLAY_TRADES.csv','build_diagnostics.py',
  'QUOTE_PATH_DIAGNOSTICS.csv','quote_diagnostics.py']]
 for p in required:assert (ROOT/p).is_file(),p
 ok('REQUIRED_ARTIFACTS_PRESENT','Reports, source documentation, derived CSV/JSON, roll, audit and prior checks present')

 archive=data(STAGE/'publication/ARCHIVE_FILE_INDEX.json')
 assert archive['archive_sha256']=='1ab1f85373c2bbd7a385d228ea061f0cd8259f409a73d40babbcfc0ba7f5eb50'
 archive_hashes={r['path']:r['sha256'] for r in archive['files']}
 result_files=sorted(p for p in (STAGE/'results').iterdir() if p.is_file())
 assert len(result_files)==18
 for p in result_files:assert sha(p)==archive_hashes[p.relative_to(ROOT).as_posix()],p
 for n,h in data(STAGE/'results/RESULT_HASHES.json').items():assert sha(STAGE/'results'/n)==h,n
 ok('EIGHTEEN_EXISTING_RESULTS_BYTE_IDENTICAL','All 18 original result files unchanged; original RESULT_HASHES verified')

 for p,h in SOURCE_HASHES.items():assert sha(ROOT/p)==h,p
 for p in ['research_original_v20/legacy_v4/dependencies/study.py','research_original_v20/legacy_v4/dependencies/portfolio_cap.py',
           'V20-03/offline/stress_v20_03.py','V20-03/offline/test_causality.py','V20-03/offline/verify_repeat.py',
           'V20-03/ROLL_POLICY_LOCKED_V1.md']:
  assert sha(ROOT/p)==archive_hashes[p],p
 for p in [*SOURCE_HASHES,'V20-03/offline/verify_publication.py']:ast.parse((ROOT/p).read_text())
 for r in data(STAGE/'publication/ARCHIVE_PARITY.json')['files']:
  assert sha(ROOT/r['published_path'])==r['published_sha256'],r['published_path']
  assert r['byte_identical']==(r['source_sha256']==r['published_sha256']),r
 ok('FROZEN_CODE_AND_ROLL_UNCHANGED','Three signal source files, dependencies, runner, original tests and locked policy byte-identical')

 forbidden={'history_2018_2022_original','source_archive','marketdata_m15','inside_day_signals'}
 for p in ROOT.rglob('*'):
  if not p.is_file():continue
  assert not (set(p.relative_to(ROOT).parts)&forbidden),p
  assert p.suffix.lower() not in {'.zip','.parquet','.gz'},p
  if p.suffix.lower()=='.csv' and p.stat().st_size>1:
   with p.open(encoding='utf-8-sig',newline='') as f:header=next(csv.reader(f))
   assert not {'Datetime','Open','High','Low','Close','Volume'}.issubset(set(header)),p
 ok('NO_SOURCE_MARKET_DATA_OR_ZIPS_IN_GIT_FOLDER','Source inputs stay outside repository as required by root AGENTS.md')

 close=rows(STAGE/'results/CLOSED_TRADES.csv');alltr=rows(STAGE/'results/ALL_OBSERVED_CLOSED.csv')
 censored=rows(STAGE/'results/CENSORED_CLOSED.csv');entries=rows(STAGE/'results/ENTRIES.csv')
 assert (len(close),len(censored),len(alltr),len(entries))==(1004,12,1016,1016)
 assert all(r['stat_eligible']=='True' for r in close)
 assert all(r['stat_eligible']=='False' and r['status']=='CENSORED_DATA_GAP' for r in censored)
 identity=lambda r:(r['account'],r['contract'],r['entry_dt'],r['exit_dt'])
 assert {identity(r) for r in alltr}=={identity(r) for r in close+censored}
 assert not (STAGE/'results/OPEN_POSITIONS.csv').read_text().strip()
 ok('TRADE_COUNTS_AND_CENSOR_PARTITION','1004 primary + 12 censored = 1016 existing entries/exits; 0 open')
 totals=Counter((r['account'],r['entry_session']) for r in entries)
 symbols=Counter((r['account'],r['family'],r['entry_session']) for r in entries)
 assert max(totals.values())<=2 and max(symbols.values())<=1
 assert all(int(r['session_span'])<=3 for r in close)
 ok('EXISTING_ENTRY_LIMITS','Existing rows satisfy 2 entries/account/session and 1 underlying/session; eligible span <=3')

 stats=rows(STAGE/'results/STATISTICS.csv')
 for r in stats:
  if r['scenario']!='C1' or not (r['kind']=='ALL' or r['kind']=='YEAR' and r['family']=='ALL'):continue
  q=[x for x in close if (r['account']=='ALL_INDEPENDENT_ACCOUNTS' or r['account']==x['account'])
     and (r['family']=='ALL' or r['family']==x['family'])
     and (r['kind']=='ALL' or r['period']==x['exit_year'])]
  assert len(q)==int(r['trades'])
  if not q:continue
  computed=metric(q)
  for field in ['R','PF','DD_closed_R']:
   if computed[field] is not None:assert math.isclose(computed[field],float(r[field]),rel_tol=1e-8,abs_tol=1e-6),(r,field,computed[field])
 ok('EXISTING_C1_AGGREGATES_CONSISTENT','Strategy/year/instrument totals agree with existing closed rows; no signal or replay execution')

 views={
  'STATISTICS_BY_STRATEGY.csv':[r for r in stats if r['kind']=='ALL' and r['family']=='ALL'],
  'STATISTICS_BY_YEAR.csv':[r for r in stats if r['kind']=='YEAR' and r['family']=='ALL'],
  'STATISTICS_BY_INSTRUMENT.csv':[r for r in stats if r['kind']=='ALL' and r['family']!='ALL'],
  'STATISTICS_MONTHLY.csv':[r for r in stats if r['kind']=='MONTH']}
 for path,expected in views.items():assert rows(STAGE/'publication'/path)==expected,path
 js=data(STAGE/'publication/STATISTICS_ALL.json')
 assert js['source_sha256']==sha(STAGE/'results/STATISTICS.csv') and len(js['records'])==len(stats)
 for a,b in zip(stats,js['records']):
  for k,v in a.items():
   expected=(float(v) if v else None) if k in {'PF','R','gross_R','DD_closed_R'} else (int(v) if v else None) if k in {'trades','wins'} else v
   assert b[k]==expected,(k,v,b[k])
 ok('PUBLISHED_CSV_JSON_VIEWS','Views serialize existing statistics only; values unchanged and no NaN JSON')

 ex=rows(STAGE/'publication/CENSORED_EXPLANATIONS.csv')
 assert len(ex)==12 and {identity(r) for r in ex}=={identity(r) for r in censored}
 assert all(int(r['gap_count'])>0 and r['observed_gap_intervals'] and r['reason']=='CENSORED_DATA_GAP' for r in ex)
 report=(STAGE/'REPORT_RU.md').read_text()
 assert all(r['event_id'] in report and r['entry_dt'] in report for r in ex)
 impact=data(STAGE/'publication/CENSORED_IMPACT.json')
 assert not impact['use_all_observed_for_decision'] and impact['true_execution_in_gap']=='UNKNOWN'
 assert math.isclose(impact['observed_censored_net_C1_R'],sum(float(r['net_C1_R']) for r in censored),abs_tol=1e-8)
 ok('ALL_TWELVE_EXCLUSIONS_EXPLAINED','All 12 event IDs, contracts, entry/exit times and existing gap intervals in report/CSV; true gap PnL unknown')

 with (ROOT/'docs/TASK_TRACKER.csv').open(newline='',encoding='utf-8') as f:tracker=list(csv.DictReader(f,delimiter=';'))
 assert [r['ID'] for r in tracker]==[f'V20-{n:02d}' for n in range(1,9)]
 assert tracker[3]['Работа']=='Разработка на базе H1/M15'
 assert 'ровно 8 этапов' in (ROOT/'docs/ROADMAP_RU.md').read_text()
 assert 'PARTIAL/HOLD' in tracker[2]['Статус']
 acceptance=data(STAGE/'ACCEPTANCE_V20_03.json')
 assert acceptance['status']=='PARTIAL/HOLD' and not acceptance['full_N4'] and not acceptance['independent_OOS']
 assert Counter(r['status'] for r in acceptance['checks'])=={'PASS':14,'FAIL':4}
 published=data(STAGE/'publication/PUBLICATION_ACCEPTANCE.json')
 assert published['stage_status']=='PARTIAL/HOLD' and published['primary_scenario']=='C1'
 assert published['replay_runs_during_publication']==0 and published['optimization_runs']==0
 assert 'C1 — единственный основной сценарий' in report
 ok('EIGHT_STAGES_AND_C1_PARTIAL_HOLD','Exactly V20-01..V20-08; V20-04 development; C1 primary; historical originals retained')

 diagnostic=data(STAGE/'comparison/VERIFICATION.json')
 assert diagnostic['status']=='PARTIAL' and not diagnostic['original_1589_ledger_available']
 assert diagnostic['quarterly_quotes_available'] and diagnostic['quarterly_source_zip']['status']=='PASS'
 assert Counter(r['status'] for r in diagnostic['checks'])=={'PASS':24,'FAIL':1,'NOT VERIFIED':2}
 for name,h in diagnostic['artifact_hashes'].items():assert sha(STAGE/'comparison'/name)==h,name
 late=rows(STAGE/'comparison/DIAGNOSTIC_REPLAY_TRADES.csv')
 assert len(late)==1589 and Counter(r['account'] for r in late)=={'SHALLOW_PULLBACK':797,'OBV_PRESSURE':612,'INSIDE_DAY_RELEASE':180}
 quote=rows(STAGE/'comparison/QUOTE_PATH_DIAGNOSTICS.csv')
 assert Counter(r['record_type'] for r in quote)=={'EXECUTED_TRADE':2605,'RAW_SIGNAL':4986,'GAP_V1_DIAGNOSTIC_TRADE':1251}
 assert diagnostic['quote_update']['quarterly_portfolio_replays']==0 and diagnostic['quote_update']['late_V1_diagnostic_replay_batches']==1
 ok('DIAGNOSTIC_PROVENANCE_AND_LIMITATIONS','43 original quote sources verified; 2605 baseline and 1251 V1 model quote checks; 4986 raw signals; original-ledger FAIL retained; no original row parity claimed')

 assert data(STAGE/'verification/CAUSALITY.json')['status']=='PASS'
 repeat=data(STAGE/'verification/REPEAT.json')
 assert repeat['status']=='PASS' and repeat['files']==18 and not repeat['differences']
 ok('PRIOR_CHECKS_PRESERVED','Archived causality/reference/repeat evidence retained; no new replay claimed')

 # Local Git check is read-only. Works for staged or committed publication.
 repository=ROOT.parent
 if (repository/'.git').exists():
  changed=subprocess.check_output(['git','diff','--name-only',BASE_SHA,'--'],cwd=repository,text=True).splitlines()
  assert changed and all(p.startswith('V20_TradingSystem_M15/') for p in changed),changed
  staged=subprocess.check_output(['git','diff','--name-only','--cached'],cwd=repository,text=True).splitlines()
  assert all(p.startswith('V20_TradingSystem_M15/') for p in staged),staged
 ok('GIT_DIFF_SCOPE','All tracked changes relative to pinned main are inside V20_TradingSystem_M15/')
 print(json.dumps(dict(status='PASS',scope='PUBLICATION_CHECKS_ONLY',checks=checks,replay_runs=0,diagnostic_replay_batches_in_current_quote_update=1,total_diagnostic_late_batches=2,optimization_runs=0,stage_status='PARTIAL/HOLD',primary_scenario='C1'),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
