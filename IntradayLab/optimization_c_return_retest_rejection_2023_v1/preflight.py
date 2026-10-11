"""Document/metadata/synthetic preflight; never opens a physical candle source."""
from collections import Counter
import csv,hashlib,json,platform,re,subprocess,sys
from pathlib import Path
from .contract import ROOT,STUDY,POLICY,grid


def run(data_root):
    policy=json.loads(POLICY.read_text());baseline=ROOT/'IntradayLab/results/return_retest_rejection_m5_2023_c_v1'
    def read(path):
        with path.open() as f:return list(csv.DictReader(f))
    instruments={}
    for symbol in ('USDRUBF','CNYRUBF','GLDRUBF','IMOEXF'):
        ts=[r for r in read(baseline/'trades.csv') if r['instrument']==symbol]
        require=lambda ok,label:None if ok else (_ for _ in ()).throw(AssertionError(label))
        require(all(t['status']=='CLOSED' for t in ts),'BASELINE_ONLY_CLOSED')
        instruments[symbol]=dict(CLOSED=len(ts),entry_days=len({t['entry_at'][:10] for t in ts}),entry_months=len({t['entry_at'][:7] for t in ts}),SKIP=sum(r['instrument']==symbol for r in read(baseline/'data_gap_skips.csv')),EXCLUDED=sum(r['instrument']==symbol for r in read(baseline/'data_quality_exclusions.csv')))
    require(instruments['USDRUBF']==dict(CLOSED=102,entry_days=82,entry_months=12,SKIP=2,EXCLUDED=2),'EXACT_USD_CONTROL_REFERENCE')
    require([instruments[s]['CLOSED'] for s in ('CNYRUBF','GLDRUBF','IMOEXF')]==[61,2,3],'SPARSE_INSTRUMENTS_EXCLUDED')
    actual=json.loads(subprocess.check_output(['gh','api','repos/alkospacer123/market-pattern-discovery/git/ref/heads/main'],text=True))
    pr=json.loads(subprocess.check_output(['gh','api','repos/alkospacer123/market-pattern-discovery/pulls/472'],text=True))
    require(actual['object']['sha']==policy['base_main'],'ACTUAL_API_MAIN')
    require(pr['head']['sha']==policy['pr_472_head'] and pr['draft'],'PR472_REFERENCE')
    source_head=subprocess.check_output(['git','-C',str(data_root),'rev-parse','HEAD'],text=True).strip()
    source_blob=subprocess.check_output(['git','-C',str(data_root),'rev-parse',source_head+':'+policy['inputs']['USDRUBF']['path']],text=True).strip()
    require(source_head==policy['source_ref'] and source_blob==policy['inputs']['USDRUBF']['blob'],'PINNED_METADATA')
    new_log=(STUDY/'pre_pnl_tests.log').read_text();old=json.loads((STUDY/'existing_tests_receipt.log').read_text());synthetic=json.loads((STUDY/'synthetic_pipeline_receipt.json').read_text())
    require(new_log.endswith('OK\n') and synthetic['status']=='PASS' and old['status']=='PASS','ALL_REAL_TESTS_PASS')
    count=int(re.search(r'Ran (\d+) tests',new_log)[1])
    github=dict(status='PASS',base_main=actual['object']['sha'],pr472_head=pr['head']['sha'],pr472_draft=pr['draft'],source_head=source_head,source_blob=source_blob,source_prices_read=0,method='Actual GitHub REST API main and PR472; local pinned source Git metadata only')
    (STUDY/'github_preflight.json').write_text(json.dumps(github,indent=2,sort_keys=True)+'\n')
    result=dict(status='PASS',remote_main=policy['base_main'],historical_C_v1_frozen_ledgers=instruments,grid_configurations=len(grid(policy)),matrix_rows=288,existing_full_tests=old['tests'],new_synthetic_tests=count,corruption_tests=len(synthetic['corruption_checks']),total_tests=old['tests']+count+len(synthetic['corruption_checks']),synthetic_full_pipeline=synthetic,pre_PNL_source_candle_reads=0,pre_PNL_historical_PNL_runs=0,source_head=source_head,source_blob=source_blob,runtime=dict(python=sys.version,platform=platform.platform()))
    (STUDY/'preflight.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True);run(p.parse_args().data_root)
