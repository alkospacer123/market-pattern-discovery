#!/usr/bin/env python3
"""Top-5 V4 guarded runner.

AUDIT never opens market data. SMOKE/PROFILE/DEV explicitly operate on DEV.
VALIDATE hard-fails unless frozen DEV selected ledgers reproduce before any
Validation OHLCV is materialized.
"""
from __future__ import annotations
import argparse,json,os,platform,subprocess,time
from pathlib import Path
import numpy as np
import pandas as pd
from market_pattern_discovery.backtest.top5_v4 import *
from market_pattern_discovery.data.finam_v4 import append_access_events,assert_no_ohlcv_materialized,load_finam_window_many,raw_file_hash_event

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results'/'top5_real_strategies_v4';CONTRACT_FILE=ROOT/'config'/'top5_v4'/'strategy_contract.json';REGISTRY_FILE=ROOT/'config'/'top5_v4'/'candidate_registry.json';DATA_ROOT=Path(os.environ.get('MARKET_PATTERN_DATA','/workspace/market-pattern-data'));DEV_ACCESS_FILE=OUT/'dev_access_ledger.json';VALIDATION_ACCESS_FILE=OUT/'validation_access_ledger.json';SMOKE_ACCESS_FILE=OUT/'smoke_access_ledger.json';PROFILE_ACCESS_FILE=OUT/'profile_access_ledger.json'

def write_json(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2,sort_keys=True,default=str)+'\n',encoding='utf-8')
def read_registry():return json.loads(REGISTRY_FILE.read_text(encoding='utf-8'))
def contract_registry():
    c=json.loads(CONTRACT_FILE.read_text(encoding='utf-8'));d=read_registry();validate_contract(c,d);return c,build_candidate_registry(c)
def git_head():return subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
def require_clean_tracked_tree():
    if subprocess.run(['git','diff-index','--quiet','HEAD','--'],cwd=ROOT).returncode!=0:raise SystemExit('tracked working tree is not clean; refuse research execution')
    status=subprocess.check_output(['git','status','--porcelain=v1','--untracked-files=all'],cwd=ROOT,text=True)
    for line in status.splitlines():
        if line.startswith('?? ') and not line[3:].startswith('results/top5_real_strategies_v4/'):
            raise SystemExit(f'untracked non-result file could affect execution: {line[3:]}')

def require_engine_only_commit():
    tracked=subprocess.check_output(['git','ls-files','results/top5_real_strategies_v4'],cwd=ROOT,text=True).splitlines()
    if tracked:raise SystemExit('DEV full must run at clean engine commit E before V4 result artifacts are tracked')

def require_engine_commit_compatible(engine_commit):
    head=git_head()
    if head==engine_commit:return
    if subprocess.run(['git','merge-base','--is-ancestor',engine_commit,head],cwd=ROOT).returncode!=0:
        raise SystemExit('validation refused: frozen engine commit E is not an ancestor of current HEAD')
    changed=subprocess.check_output(['git','diff','--name-only',f'{engine_commit}..{head}'],cwd=ROOT,text=True).splitlines()
    bad=[x for x in changed if x and not x.startswith('results/top5_real_strategies_v4/')]
    if bad:raise SystemExit(f'validation refused: commits after E change engine/specification paths: {bad}')

def data_paths(instrument,include_q2):
    folder='CNY' if instrument=='CNYRUBF' else 'Si';paths=[DATA_ROOT/'2026'/folder/f'{folder}_2026_Q1_M1.csv']
    if include_q2:paths.append(DATA_ROOT/'2026'/folder/f'{folder}_2026_Q2_M1.csv')
    return paths
def load_window(start,end,include_q2,access_file=None):
    frames={};events=[]
    for inst in ('CNYRUBF','USDRUBF'):
        res=load_finam_window_many(data_paths(inst,include_q2),inst,start,end);frames[inst]=prepare_m1(res.frame,inst);events.extend(res.access_events)
    if access_file is not None:append_access_events(access_file,events)
    return frames
def _clone_target_signals(base,candidate):
    if base.empty:return base.copy()
    x=base.copy();x['candidate_id']=candidate['candidate_id']
    if 'target_r' in candidate['parameters']:x['target_r']=float(candidate['parameters']['target_r'])
    return finalize_signal_ids(x.drop(columns=['signal_id'],errors='ignore'))
def run_candidates(frames,registry,candidate_ids=None):
    use=[c for c in registry if candidate_ids is None or c['candidate_id'] in candidate_ids];m5={i:causal_m5(frames[i]) for i in ('CNYRUBF','USDRUBF')};level_cache={};signal_cache={};signals_all=[];ledgers=[];skips=[];stage={'candidate_count':len(use),'signal_generation_seconds':0.,'execution_seconds':0.}
    for c in use:
        family,sub=c['family'],c['submodel']
        if family=='PAIRS':
            t=time.perf_counter();sig,feat=pair_signals(frames['CNYRUBF'],frames['USDRUBF'],c);stage['signal_generation_seconds']+=time.perf_counter()-t;t=time.perf_counter();ledger,skip=simulate_pairs(frames['CNYRUBF'],frames['USDRUBF'],sig,{c['candidate_id']:feat},120);stage['execution_seconds']+=time.perf_counter()-t
            if not sig.empty:signals_all.append(sig)
            if not ledger.empty:ledgers.append(ledger)
            if not skip.empty:skips.append(skip)
            continue
        for inst in ('CNYRUBF','USDRUBF'):
            t=time.perf_counter();p=c['parameters']
            if family=='STRUCTURAL':
                lkey=(inst,int(p['tolerance_ticks']),int(p['min_touches']))
                if lkey not in level_cache:level_cache[lkey]=structural_levels(m5[inst],inst,lkey[1],lkey[2])
                skey=(family,sub,inst,lkey[1],lkey[2])
                if skey not in signal_cache:signal_cache[skey]=gerchik_a_signals(m5[inst],level_cache[lkey],inst,c) if sub=='GERCHIK_A_M5_PROXY' else structural_signals(m5[inst],level_cache[lkey],inst,c)
                sig=_clone_target_signals(signal_cache[skey],c);max_hold=120
            elif family=='ORB':
                skey=(family,sub,inst,int(p['length']),p.get('stop_mode'))
                if skey not in signal_cache:signal_cache[skey]=orb_signals(frames[inst],inst,c)
                sig=_clone_target_signals(signal_cache[skey],c);max_hold=120
            elif family=='TREND_PULLBACK':
                skey=(family,sub,inst,int(p['slow_ema']))
                if skey not in signal_cache:signal_cache[skey]=trend_signals(m5[inst],inst,c)
                sig=_clone_target_signals(signal_cache[skey],c);max_hold=120
            elif family=='BOLLINGER_RSI':sig=mean_reversion_signals(m5[inst],inst,c);max_hold=60
            else:raise RuntimeError(f'unknown family {family}')
            stage['signal_generation_seconds']+=time.perf_counter()-t;t=time.perf_counter();ledger,skip=simulate_explicit_orders(frames[inst],sig,inst,max_hold);stage['execution_seconds']+=time.perf_counter()-t
            if not sig.empty:signals_all.append(sig)
            if not ledger.empty:ledgers.append(ledger)
            if not skip.empty:skips.append(skip)
    sig_df=pd.concat(signals_all,ignore_index=True) if signals_all else pd.DataFrame();ledger_df=pd.concat(ledgers,ignore_index=True) if ledgers else pd.DataFrame();skip_df=pd.concat(skips,ignore_index=True) if skips else pd.DataFrame();stage['signals']=int(sig_df.signal_id.nunique()) if not sig_df.empty else 0;stage['raw_trades']=int(ledger_df.trade_id.nunique()) if not ledger_df.empty else 0;return sig_df,ledger_df,skip_df,stage

def audit():
    c,r=contract_registry();checks={'contract_valid':True,'registry_total_142':len(r)==142,'registry_selection_eligible_136':sum(x['selection_eligible'] for x in r)==136,'instrument_excluded_candidate_identity':all('instrument' not in x['parameters'] for x in r),'per_family_timeframes':set(c['timeframes'])=={'STRUCTURAL','ORB','TREND_PULLBACK','PAIRS','BOLLINGER_RSI'},'exact_formulas_frozen':all('executable_formulas' in c['family_rules'][f] for f in c['family_rules']),'selection_status_frozen':c['selection_policy']['status_by_survivor_count']=={'0':'NO_DEV_SURVIVOR','1-4':'PARTIAL_DEV_SURVIVORS','5':'DEV_SELECTION_COMPLETE'},'true_oos_locked':c['true_oos_policy']=={'year':2025,'status':'LOCKED_TRUE_OOS_DO_NOT_ACCESS'},'spec_results_separate':c['freeze_policy']['specifications_separate_from_results'] is True,'runtime_gate_seconds':c['testing_policy']['full_grid_runtime_gate_seconds']==600}
    agents=ROOT/'AGENTS.md';protocol=ROOT/'config'/'research_protocol_v1.json'
    if agents.exists():checks['zero_lookahead_repository_contract']='ZERO LOOK-AHEAD' in agents.read_text(encoding='utf-8')
    if protocol.exists():
        p=json.loads(protocol.read_text(encoding='utf-8'));checks['repository_true_oos_2025']=p.get('true_oos_year')==2025;checks['validation_nested_inside_repository_discovery']=p.get('discovery_period',{}).get('end_moscow_exclusive')=='2026-05-16T00:00:00+03:00' and p.get('internal_confirmation_period',{}).get('start_moscow')=='2026-05-16T00:00:00+03:00'
    report={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'market_data_accessed':False,'engine_commit':git_head() if (ROOT/'.git').exists() else None};write_json(OUT/'audit_report.json',report);print(json.dumps(report,indent=2));
    if report['status']!='PASS':raise SystemExit(1)
def _representatives(registry):
    wanted=[('STRUCTURAL','REJECTION'),('STRUCTURAL','SIMPLE_SWEEP'),('STRUCTURAL','COMPLEX_FALSE_BREAK'),('STRUCTURAL','BREAKOUT_RETEST'),('STRUCTURAL','GERCHIK_A_M5_PROXY'),('ORB','DIRECT'),('ORB','BREAKOUT_RETEST'),('ORB','FAILED_BREAKOUT_DIAGNOSTIC'),('TREND_PULLBACK','EMA20_50'),('TREND_PULLBACK','EMA20_100'),('PAIRS','DISTANCE'),('PAIRS','OLS'),('BOLLINGER_RSI','REENTRY_2R'),('BOLLINGER_RSI','REENTRY_FIXED_MID')];return [next(c for c in registry if c['family']==f and c['submodel']==s) for f,s in wanted]
def smoke():
    require_clean_tracked_tree();_,registry=contract_registry();SMOKE_ACCESS_FILE.unlink(missing_ok=True);frames=load_window(DEV_START,DEV_END,False,SMOKE_ACCESS_FILE);small={}
    for inst,f in frames.items():dates=list(pd.unique(f.trading_date))[:10];small[inst]=f[f.trading_date.isin(dates)].reset_index(drop=True)
    reps=_representatives(registry);t=time.perf_counter();sig,ledger,skip,stage=run_candidates(small,reps);elapsed=time.perf_counter()-t;report={'status':'PASS','elapsed_seconds':elapsed,'stage':stage,'families':sorted(set(c['family'] for c in reps)),'market_data_scope':'DEV first 10 trading dates only'};write_json(OUT/'smoke_summary.json',report);sig.to_csv(OUT/'smoke_signals.csv',index=False);ledger.to_csv(OUT/'smoke_trades.csv',index=False);skip.to_csv(OUT/'smoke_skips.csv',index=False);print(json.dumps(report,indent=2,default=str))
def profile_dev():
    require_clean_tracked_tree();c,registry=contract_registry();gate=float(c['testing_policy']['full_grid_runtime_gate_seconds']);PROFILE_ACCESS_FILE.unlink(missing_ok=True);frames=load_window(DEV_START,DEV_END,False,PROFILE_ACCESS_FILE);t=time.perf_counter();_,_,_,stage=run_candidates(frames,registry);elapsed=time.perf_counter()-t;report={'full_grid_runtime_seconds':elapsed,'gate_seconds':gate,'gate_status':'PASS' if elapsed<=gate else 'FAIL','stage':stage};write_json(OUT/'performance_profile_v4.json',report);print(json.dumps(report,indent=2));
    if elapsed>gate:raise SystemExit('full-grid runtime gate failed')
def _hash_all_frozen_data():
    data_hashes={};events=[]
    for inst in ('CNYRUBF','USDRUBF'):
        for p in data_paths(inst,True):e=raw_file_hash_event(p);events.append(e);data_hashes[f'{inst}:{p.name}']=e['sha256']
    return data_hashes,events
def dev_full():
    require_clean_tracked_tree();require_engine_only_commit();c,registry=contract_registry();gate=float(c['testing_policy']['full_grid_runtime_gate_seconds']);OUT.mkdir(parents=True,exist_ok=True);DEV_ACCESS_FILE.unlink(missing_ok=True);data_hashes,hash_events=_hash_all_frozen_data();append_access_events(DEV_ACCESS_FILE,hash_events);frames=load_window(DEV_START,DEV_END,False,DEV_ACCESS_FILE);events=json.loads(DEV_ACCESS_FILE.read_text());assert_no_ohlcv_materialized(events,DEV_END,VALIDATION_END);t=time.perf_counter();signals,ledger,skips,stage=run_candidates(frames,registry);elapsed=time.perf_counter()-t
    if elapsed>gate:raise SystemExit(f'full-grid runtime {elapsed:.2f}s exceeds preregistered {gate:.0f}s gate')
    if not ledger.empty:ledger['period']='DEV'
    signals.to_csv(OUT/'dev_signals.csv',index=False);ledger.to_csv(OUT/'dev_trade_ledger.csv',index=False);skips.to_csv(OUT/'dev_skip_ledger.csv',index=False);mt=registry_metrics(registry,ledger);mt.to_csv(OUT/'dev_metrics.csv',index=False);selected,status=select_primaries(registry,mt);selected_ids=set(selected.candidate_id) if not selected.empty else set();selection={'status':status,'selected':selected.to_dict('records') if not selected.empty else []};write_json(OUT/'dev_selection.json',selection);parameter_plateau_report(mt).to_csv(OUT/'parameter_plateau_report.csv',index=False);selected_ledger=ledger[ledger.candidate_id.isin(selected_ids)].copy() if selected_ids and not ledger.empty else pd.DataFrame();selected_hash=semantic_ledger_hash(selected_ledger);(OUT/'selected_dev_semantic_ledger.sha256').write_text(selected_hash+'\n');head=git_head();code_paths=sorted((ROOT/'src/market_pattern_discovery/backtest/top5_v4').glob('*.py'))+[ROOT/'src/market_pattern_discovery/data/finam_v4.py',ROOT/'scripts/run_top5.py'];code_hashes={str(p.relative_to(ROOT)):file_sha256(p) for p in code_paths};deps={'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__};env={'platform':platform.platform(),'timezone':'Europe/Moscow','data_root':str(DATA_ROOT)};manifest=freeze_manifest(head,CONTRACT_FILE,REGISTRY_FILE,deps,OUT/'dev_selection.json',OUT/'dev_trade_ledger.csv',env,data_hashes,DEV_ACCESS_FILE,selected_hash,code_hashes);manifest.update({'runtime_seconds':elapsed,'runtime_gate_seconds':gate,'stage':stage,'selection_status':status});write_json(OUT/'freeze_manifest.json',manifest);print(json.dumps({'status':status,'runtime_seconds':elapsed,'selected':len(selected_ids),'engine_commit':head},indent=2))
def _metric_dict(g):
    if g.empty:return {'trades':0,'profit_factor':None,'expectancy_bps':None}
    p=g.pnl_bps.astype(float).to_numpy();return {'trades':len(g),'profit_factor':_pf(p),'expectancy_bps':float(np.mean(p))}
def _selected_metric_ledger(ledger,family):return ledger.copy() if family=='PAIRS' else pooled_single_leg_ledger(ledger)
def validate():
    require_clean_tracked_tree();c,registry=contract_registry();manifest_path=OUT/'freeze_manifest.json';selection_path=OUT/'dev_selection.json'
    if not manifest_path.exists() or not selection_path.exists():raise SystemExit('validation refused: frozen DEV artifacts missing')
    manifest=json.loads(manifest_path.read_text());selection=json.loads(selection_path.read_text());status=selection.get('status')
    if status not in c['validation_workflow']['validation_allowed_dev_statuses']:raise SystemExit(f'validation refused: DEV selection status {status}')
    require_engine_commit_compatible(manifest['engine_commit'])
    if file_sha256(CONTRACT_FILE)!=manifest['contract_sha256'] or file_sha256(REGISTRY_FILE)!=manifest['candidate_registry_sha256'] or file_sha256(selection_path)!=manifest['selected_sha256']:raise SystemExit('validation refused: frozen specification/selection hash mismatch')
    for rel,expected in manifest.get('code_hashes',{}).items():
        if file_sha256(ROOT/rel)!=expected:raise SystemExit(f'validation refused: frozen code hash mismatch {rel}')
    selected_ids={r['candidate_id'] for r in selection.get('selected',[])}
    if not selected_ids:raise SystemExit('validation refused: NO_DEV_SURVIVOR')
    if not DEV_ACCESS_FILE.exists() or file_sha256(DEV_ACCESS_FILE)!=manifest.get('access_ledger_sha256'):
        raise SystemExit('validation refused: frozen DEV access-ledger hash mismatch')
    VALIDATION_ACCESS_FILE.unlink(missing_ok=True);current_hashes,hash_events=_hash_all_frozen_data()
    if current_hashes!=manifest.get('data_hashes'):raise SystemExit('HARD FAIL before Validation OHLCV: frozen raw data hash mismatch')
    append_access_events(VALIDATION_ACCESS_FILE,hash_events);dev_frames=load_window(DEV_START,DEV_END,False,VALIDATION_ACCESS_FILE);events=json.loads(VALIDATION_ACCESS_FILE.read_text());assert_no_ohlcv_materialized(events,DEV_END,VALIDATION_END);_,dev_ledger,_,_=run_candidates(dev_frames,registry,selected_ids)
    if not dev_ledger.empty:dev_ledger['period']='DEV'
    if semantic_ledger_hash(dev_ledger)!=manifest['selected_dev_semantic_ledger_hash']:raise SystemExit('HARD FAIL before Validation OHLCV: selected DEV semantic ledger mismatch')
    full_frames=load_window(DEV_START,VALIDATION_END,True,VALIDATION_ACCESS_FILE);_,ledger,skips,stage=run_candidates(full_frames,registry,selected_ids)
    if ledger.empty:raise SystemExit('validation produced no trades')
    ledger['period']=assign_period(ledger.entry_time);val=ledger[ledger.period.isin(['VALIDATION_A','VALIDATION_B'])].copy();val.to_csv(OUT/'validation_trade_ledger.csv',index=False);skips.to_csv(OUT/'validation_skip_ledger.csv',index=False);results=[];by_id={q['candidate_id']:q for q in registry}
    for cid in sorted(selected_ids):
        cand=by_id[cid];q=_selected_metric_ledger(val[val.candidate_id==cid],cand['family']);a=q[q.period=='VALIDATION_A'];b=q[q.period=='VALIDATION_B'];combined=q[q.period.isin(['VALIDATION_A','VALIDATION_B'])];ab=_metric_dict(a[a.friction=='BASE']);bb=_metric_dict(b[b.friction=='BASE']);cb=_metric_dict(combined[combined.friction=='BASE']);cs=_metric_dict(combined[combined.friction=='STRESS']);results.append({'candidate_id':cid,'family':cand['family'],'submodel':cand['submodel'],'A_BASE':ab,'B_BASE':bb,'COMBINED_BASE':cb,'COMBINED_STRESS':cs,'status':validation_status(ab,bb,cb,cs)})
    report={'classification':c['validation_workflow']['classification'],'pre_read_dev_reproduction':'PASS','selection_status':status,'stage':stage,'results':results};write_json(OUT/'validation_report.json',report);print(json.dumps(report,indent=2,default=str))
def main():
    ap=argparse.ArgumentParser();g=ap.add_mutually_exclusive_group(required=True)
    for flag in ('audit','smoke','profile-dev','dev-full','validate'):g.add_argument('--'+flag,action='store_true',dest=flag.replace('-','_'))
    a=ap.parse_args();{'audit':audit,'smoke':smoke,'profile_dev':profile_dev,'dev_full':dev_full,'validate':validate}[next(k for k,v in vars(a).items() if v)]()
if __name__=='__main__':main()
