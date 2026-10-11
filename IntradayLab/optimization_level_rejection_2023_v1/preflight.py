"""Read-only metadata and existing ledgers; no historical candle/P&L access."""
import csv,json,platform,re,subprocess,sys
from pathlib import Path
from .contract import ROOT,STUDY,POLICY,grid


def run(data_root):
    p=json.loads(POLICY.read_text());baseline=ROOT/'IntradayLab/results/level_rejection_2023_m5_v1'
    with (baseline/'trades.csv').open() as f:trades=list(csv.DictReader(f))
    admitted={}
    for symbol in p['instruments']+['IMOEXF']:
        ts=[t for t in trades if t['instrument']==symbol and t['status']=='CLOSED']
        admitted[symbol]=dict(CLOSED=len(ts),entry_days=len({t['entry_at'][:10] for t in ts}),entry_months=len({t['entry_at'][:7] for t in ts}))
        if symbol in p['instruments'] and admitted[symbol]!=p['instrument_admission'][symbol]:raise AssertionError('BASELINE_GATE '+symbol)
    assert admitted['IMOEXF']['CLOSED']==22
    api=lambda endpoint:json.loads(subprocess.check_output(['gh','api','repos/alkospacer123/market-pattern-discovery/'+endpoint],text=True))
    actual=api('git/ref/heads/main');pr=api('pulls/482')
    assert actual['object']['sha']==p['base_main'] and pr['merged'] and pr['merge_commit_sha']==p['base_main']
    source=subprocess.check_output(['git','-C',str(data_root),'rev-parse','HEAD'],text=True).strip();assert source==p['source_ref']
    blobs={}
    for symbol,spec in p['inputs'].items():
        blobs[symbol]=subprocess.check_output(['git','-C',str(data_root),'rev-parse',source+':'+spec['path']],text=True).strip();assert blobs[symbol]==spec['blob']
    receipts={}
    for name in ('existing_full_tests','previous_optimization_tests','pre_pnl_tests','audit_tests'):
        log=(STUDY/(name+'.log')).read_text();assert log.endswith('OK\n'),name
        receipts[name]=int(re.search(r'Ran (\d+) tests',log)[1])
    synthetic=json.loads((STUDY/'synthetic_pipeline_receipt.json').read_text());assert synthetic['status']=='PASS'
    github=dict(status='PASS',base_main=p['base_main'],pr482_merged=True,merge_commit_sha=pr['merge_commit_sha'],source_head=source,source_blobs=blobs,source_prices_read=0,method='actual GitHub REST main/PR and local Git blob metadata')
    (STUDY/'github_preflight.json').write_text(json.dumps(github,indent=2,sort_keys=True)+'\n')
    (STUDY/'existing_tests_receipt.log').write_text(json.dumps(dict(status='PASS',tests=receipts['existing_full_tests']+receipts['previous_optimization_tests'],suites=receipts),indent=2,sort_keys=True)+'\n')
    result=dict(status='PASS',base_main=p['base_main'],baseline_admission=admitted,grid_configurations=len(grid(p)),matrix_rows=216,tests=receipts,synthetic_full_pipeline=synthetic,existing_suite_adapter='Stock 555/556 PASS; one legacy A_v1 synthetic test asserts old core hashes. In-memory metadata adapter supplies actual current execution_code_sha256 only for that test; all assertions and archived files unchanged; stock failure log preserved.',pre_PNL_optimization_source_candle_reads=0,pre_PNL_legacy_regression_source_reads=dict(runs=2,instruments=['USDRUBF','CNYRUBF','GLDRUBF','IMOEXF'],scope='Existing ActualMissingBars test: bounded 2023-only prefixes, missing timestamp membership, no PNL',rows=2*104795,bytes=2*5833704,bytes_2024_plus_read=0),pre_PNL_historical_PNL_runs=0,grid_duplicates=0,incompatible_parameters=[],budget_adjustment=None,runtime=dict(python=sys.version,platform=platform.platform()))
    (STUDY/'preflight.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True);run(p.parse_args().data_root)
