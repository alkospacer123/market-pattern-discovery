"""Full run, independent audit first, then read-only published reconciliation."""
import argparse,json,re,subprocess,sys
from pathlib import Path
from io_utils import write_csv,write_json,digest
import primary,source,metrics

HERE=Path(__file__).resolve().parent

def run(data,out,published=True):
    frozen=json.loads((HERE/'FREEZE.json').read_text())
    for name,expected in frozen['files'].items():
        assert digest(HERE/name)==expected,('CODE_FREEZE_CHANGED',name)
        assert __import__('hashlib').sha256(source.git('show',frozen['code_commit']+':'+str((HERE/name).relative_to(source.ROOT)))).hexdigest()==expected
    out.mkdir(parents=True,exist_ok=True);(out/'features').mkdir(exist_ok=True)
    test=subprocess.run([sys.executable,str(HERE/'test_causal.py')],capture_output=True,text=True)
    (out/'test_results.txt').write_text(re.sub(r'Ran (\d+) tests in [\d.]+s',r'Ran \1 tests (elapsed time omitted)',test.stdout+test.stderr))
    assert test.returncode==0,test.stdout+test.stderr
    manifest=source.manifest(data,out);write_json(out/'source_manifest.json',manifest)
    models={mode:{k:[] for k in ('trades','signals','stops','snapshots','OPEN','occupancy')} for mode in primary.MODES};allbars={}
    for symbol in primary.SYMBOLS:
        bars=primary.features(primary.load(data/'forever'/symbol/(symbol+'_M15.csv')));allbars[symbol]=bars
        write_csv(out/'features'/(symbol+'.csv.gz'),bars)
        for mode in primary.MODES:
            calculated=primary.replay(bars,symbol,mode)
            for table,value in calculated.items():models[mode][table].extend([value] if table=='occupancy' else value)
        print(json.dumps(dict(stage='primary',symbol=symbol,candles=len(bars))),flush=True)
    for mode,tables in models.items():
        for table,rows in tables.items():
            fields=['model','instrument','trade_id','direction','signal_time','entry_time','entry_price','initial_stop','initial_risk','month','active_stop','last_close','last_close_price','unrealized_gross_R','status'] if not rows and table=='OPEN' else None
            write_csv(out/(mode.lower()+'_'+table+'.csv'+('.gz' if table in ('signals','stops') else '')),rows,fields)
    tables=metrics.build(models,allbars,out);diff=metrics.differences(models,out)
    subprocess.run([sys.executable,str(HERE/'verify.py'),'--data-root',str(data),'--output',str(out)],check=True)
    write_json(out/'independent_run_completed.json',dict(full_source_replay_completed=True,independent_feature_and_execution_verification_completed=True,published_journals_read_before_completion=False,stage_order=['new_primary_full_source_replay','independent_stdlib_full_source_replay','published_reference_read']))
    if published:
        import published as P
        receipt=P.reconcile(models,out)
    else:receipt=dict(status='NOT_RUN',reason='First independent development run; no published journals read')
    evidence=[('completed_m15_only','test_features_prefix_and_future_mutation'),('h1_publication_causal','full scalar streaming feature comparison; AvailableAt assertion'),('donchian_strictly_prior20','test_donchian_excludes_current; independent deque'),('signal_close_excludes_signal_extrema','test_signal_extremes_excluded; test_signal_final_bar_no_stop'),('next_open_no_future_hlc_in_entry','test_execution_hlc_not_entry_inputs'),('one_position_per_symbol','test_busy_signals_no_pyramiding; independent full state replay'),('no_retroactive_stop_trailing','test_trailing_no_retroactive_touch; stop-first; no_plus_one_R_delay'),('gaps_no_fabrication','test_gap_cancels_no_future_open; adverse_gap_fill_open; raw source gap receipts'),('same_frozen_logic_all_four','test_all_symbols_identical_logic'),('published_only_after_independent_replay','independent_run_completed.json; sequential run.py')]
    audit=dict(status='PASS' if receipt['status']=='PASS' else 'INCOMPLETE',independent=json.loads((out/'independent_verification.json').read_text()),published=receipt,causal_tests='PASS',causal_test_count=int(re.search(r'Ran (\d+) tests',test.stderr).group(1)),causality_checks=[dict(test=k,status='PASS',evidence=v) for k,v in evidence],full_source_replay=True,months_same_sign=sum(r['same_sign'] is True for r in tables['month_signs']),month_sign_mismatches=[r['month'] for r in tables['month_signs'] if r['same_sign'] is False],differences=diff,scope='Only T1 SIGNAL_CLOSE/NEXT_OPEN trail3.5 N4; no costs, optimization, live or production changes',external_human_audit='PENDING',deterministic_repeat_receipt='../repeatability.json')
    write_json(out/'audit_result.json',audit)
    if published:
        import report
        report.render(out,tables,manifest,audit,models)
    print(json.dumps(dict(stage='finished',summary=tables['summary'],audit=audit['status'])),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,default=Path('/workspace/market-pattern-data'));p.add_argument('--output',type=Path,required=True);p.add_argument('--independent-only',action='store_true');a=p.parse_args();run(a.data_root,a.output,not a.independent_only)
