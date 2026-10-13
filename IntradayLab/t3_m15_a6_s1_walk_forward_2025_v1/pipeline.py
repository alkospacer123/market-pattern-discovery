"""Sequential CONTROL then W1..W4, each seal committed before next read.

Expanding replay reconstructs exact canonical state from original history. It
preserves positions, recursion, pending, IDs and occupancy, without fitted state
or boundary flat resets. Both implementations always see the same past only.
"""
import argparse,csv,io,json,re,subprocess,sys
from datetime import datetime
from pathlib import Path
import pandas as pd
import common as C,engine as E,scalar as S,control as G,integrity as F
import safe_source as B,accounting as A,render

PREFIX='IntradayLab/t3_m15_a6_s1_walk_forward_2025_v1/'
CANON='IntradayLab/t3_m15_a6_s1_robustness_v1/results/'
SPEC=json.loads((C.HERE/'SPEC.json').read_text())
KEYS={'trades':['instrument','trade_id'],'OPEN_POSITIONS':['instrument','trade_id'],
 'stop_decisions':['instrument','bar_close_time','trade_id'],'entry_opportunities':['instrument','signal_time'],
 'observed_gaps':['instrument','current_close'],'PERIOD_END_OPEN_POSITIONS':['instrument','month','trade_id']}

def compare_outputs(a,b,label,d):
    cmp=C.Comparison()
    for name in G.NAMES:
        fields=sorted(set(k for r in a[name]+b[name] for k in r))
        cmp.rows([{k:r.get(k) for k in fields} for r in a[name]],C.plain([{k:r.get(k) for k in fields} for r in b[name]]),label+'_'+name,KEYS[name])
    result={'status':'PASS' if not cmp.diffs else 'FAIL','fields_compared':cmp.fields,'differences':len(cmp.diffs),'max_numeric_delta':max(cmp.maxima.values(),default=0),'tolerance':1e-8,'tables':cmp.tables}
    C.write_json(d/(label+'.json'),result);C.write_csv(d/(label+'_DIFF.csv'),cmp.diffs,['table','row','field','actual','expected'])
    assert not cmp.diffs,label+'_STOP'
    return result

def canonical_output(which):
    result={}
    for name in G.NAMES:
        raw=C.historical(CANON+which+'/'+name+('.json' if 'POSITIONS' in name else '.csv'))
        rows=json.loads(raw) if 'POSITIONS' in name else list(csv.DictReader(io.StringIO(raw.decode())))
        result[name]=rows
    return result

def direct_canonical(out,which,label,d):
    ref=canonical_output(which);cmp=C.Comparison()
    for name in G.NAMES:
        fields=sorted(set(k for r in ref[name] for k in r))
        cmp.rows([{k:r.get(k) for k in fields} for r in out[name]],ref[name],label+'_'+name,KEYS[name])
    result={'status':'PASS' if not cmp.diffs else 'FAIL','fields_compared':cmp.fields,'differences':len(cmp.diffs),'max_numeric_delta':max(cmp.maxima.values(),default=0),'tables':cmp.tables}
    C.write_json(d/(label+'.json'),result);assert not cmp.diffs,'PR510_CONTROL_STOP'
    return result

def published_tables(out,d):
    import analysis as P,scalar_analysis as Q
    primary=P.build(out);independent=Q.evaluate(out);cmp=C.Comparison()
    keys={'summary':['scope','direction','year'],'monthly':['scope','direction','year','month'],'loss_runs':['scope','direction','year','series_type','start','end'],
          'scenario_summary':['scenario','scope','direction','year'],'scenario_monthly':['scenario','scope','direction','year','month'],
          'scenario_ledger':['scenario','scope','direction','year','instrument','trade_id'],'top_winners':['year','direction','rank'],'november2024':['scope','direction']}
    for name,rows in primary.items():
        ref=C.reference(CANON+name+'.csv')
        cmp.rows(rows,ref,'PR510_'+name,keys[name])
        cmp.rows(independent[name],ref,'SCALAR_PR510_'+name,keys[name])
        C.write_csv(d/(name+'.csv'),rows)
    result={'status':'PASS' if not cmp.diffs else 'FAIL','fields_compared':cmp.fields,'differences':len(cmp.diffs),'max_numeric_delta':max(cmp.maxima.values(),default=0),'tables':cmp.tables}
    C.write_json(d/'PR510_TABLES.json',result);assert not cmp.diffs,'PR510_TABLES_STOP'
    return result

def sources(root,end):
    C.END=end;S.END=end
    p={};s={};receipts=[]
    assert C.git('rev-parse','HEAD',root=root).decode().strip()==C.DATA_SHA,'DATA_PIN'
    for spec in SPEC['sources']:
        symbol=spec['instrument'];path=root/spec['path']
        blob=C.git('rev-parse',C.DATA_SHA+':'+spec['path'],root=root).decode().strip()
        assert blob==spec['git_blob_sha'],'BLOB_PIN'
        raw,first=B.read_primary(path,end);other,second=B.read_scalar(path,end)
        assert first==second,'SOURCE_READERS_DIFFER'
        first.update(instrument=symbol,path=spec['path'],git_blob_sha=blob,data_commit=C.DATA_SHA)
        if end.year==2025 and end.month==1:
            assert first['allowed_prefix_sha256']==spec['historical_prefix_sha256'] and len(raw)==spec['used_candles'],'HISTORICAL_PREFIX_PIN'
        p[symbol]=E.features(raw);s[symbol]=C.build_features(other);receipts.append(first)
    return p,s,receipts

def continuation(old,new,old_frames,new_frames,prior_end,d):
    import copy
    cmp=C.Comparison();carried=[]
    # Every sealed trade/Stop/gap and settled signal remains unchanged. Pending
    # decision is legitimately resolved in the subsequent block, by the canon.
    for name,event in [('trades','exit_time'),('stop_decisions','bar_close_time'),('observed_gaps','current_close'),('entry_opportunities','signal_time')]:
        expected=[r for r in old[name] if not r.get('pending_at_end')]
        excluded={(r['instrument'],r['signal_time']) for r in old['entry_opportunities'] if r.get('pending_at_end')}
        actual=[r for r in new[name] if r[event]<prior_end and (name!='entry_opportunities' or (r['instrument'],r['signal_time']) not in excluded)]
        fields=sorted(set(k for r in expected+actual for k in r))
        cmp.rows([{k:r.get(k) for k in fields} for r in actual],C.plain([{k:r.get(k) for k in fields} for r in expected]),'SEALED_PREFIX_'+name,KEYS[name])
    for symbol in C.SYMBOLS:
        pd.testing.assert_frame_equal(old_frames[symbol],new_frames[symbol].loc[new_frames[symbol].index<prior_end],check_exact=True)
    for op in old['OPEN_POSITIONS']:
        future=[r for r in new['stop_decisions'] if r['instrument']==op['instrument'] and r['trade_id']==op['trade_id'] and r['bar_close_time']>=prior_end]
        if future:
            first=future[0]
            for key,field in [('active_stop','active_stop'),('initial_risk','initial_risk'),('favorable_extreme','extreme_before'),('threshold_activated','activated_before'),('activation_time','activation_time_before')]:cmp.value(first[field],C.plain(op[key]),'CARRY_FIRST_BAR',op['trade_id'],key)
            carried.append({'instrument':op['instrument'],'trade_id':op['trade_id'],'first_next_close':first['bar_close_time'],'state_checked':True})
        else:
            remain=[r for r in new['OPEN_POSITIONS'] if r['trade_id']==op['trade_id'] and r['instrument']==op['instrument']]
            assert remain,'CARRY_LOST';carried.append({'instrument':op['instrument'],'trade_id':op['trade_id'],'no_new_completed_bar':True})
    result={'status':'PASS' if not cmp.diffs else 'FAIL','fields_compared':cmp.fields,'differences':len(cmp.diffs),'max_numeric_delta':max(cmp.maxima.values(),default=0),'carry':carried,'feature_prefix_exact':True,'FLAT_reset':False,'pending_reconstructed_from_history':True}
    C.write_json(d/'CONTINUATION.json',result);assert not cmp.diffs,'CARRY_STOP';return result

def checkpoint(out,frames,receipts,end):
    instruments=[]
    for symbol in C.SYMBOLS:
        f=frames[symbol];last=f.iloc[-1];day=f.loc[f.index.normalize()==f.index[-1].normalize()]
        records=[]
        # Full recursion is preserved through deterministic original-prefix
        # reconstruction. This receipt records the indicator frontier + lookback.
        for at,row in f.tail(80).iterrows():records.append({'at':at}|{k:None if pd.isna(v) else v for k,v in row.items()})
        digest=C.sha(json.dumps(C.plain(records),sort_keys=True).encode())
        instruments.append({'instrument':symbol,'last_close':f.index[-1],'last_features':{k:None if pd.isna(v) else v for k,v in last.items()},
            'last80_features_sha256':digest,'daily_H1_ordinal_observed_bars':len(day),'source_prefix':next(x for x in receipts if x['instrument']==symbol),
            'state_resume':'canonical full original prefix reconstruction, no boundary initialization',
            'occupied_trade_ID':[r['trade_id'] for r in out['OPEN_POSITIONS'] if r['instrument']==symbol],
            'CLOSED_ID_count':sum(r['instrument']==symbol for r in out['trades'])})
    return {'end_exclusive':end,'OPEN':out['OPEN_POSITIONS'],'pending':[r for r in out['entry_opportunities'] if r.get('pending_at_end')],
        'indicator_frontiers':instruments,'state_reset':False,'forced_liquidation':False,'future_marks':False}

def persist_features(frames,d):
    # Only derived indicators/timestamps, no raw quote-source copies.
    fields=['ATR','PreviousATR','PriorHigh','PriorLow','H1ADX','H1PreviousADX','H1Slope','H1PreviousSlope','H1ATRRatio','H1PreviousATRRatio','H1AvailableAt','H1PreviousAvailableAt','Signal']
    rows=[]
    for symbol in C.SYMBOLS:
        for at,r in frames[symbol].iterrows():rows.append({'instrument':symbol,'close_time':at}|{k:None if pd.isna(r[k]) else int(r[k]) if k=='Signal' else r[k] for k in fields})
    C.write_csv(d/'indicators.csv',rows)

def commit_stage(d,label,enabled):
    files=sorted(p for p in d.rglob('*') if p.is_file())
    manifest={str(p.relative_to(d)):C.file_sha(p) for p in files}
    C.write_json(d/'SEAL.json',{'stage':label,'files_SHA256':manifest,'sealed_before_next_stage':True})
    if enabled:
        assert C.HERE in d.parents
        C.git('add','--',str(d.relative_to(C.REPO)));C.git('commit','-m',f'IntradayLab WF2025: seal {label} before next block')
        print(json.dumps({'sealed_stage':label,'commit':C.git('rev-parse','HEAD').decode().strip()}),flush=True)
    else:print(json.dumps({'sealed_stage':label,'repeat_mode':True}),flush=True)

def run(root,output,commits=False):
    frozen=F.freeze_guard();output.mkdir(parents=True,exist_ok=True)
    proc=subprocess.run([sys.executable,'-m','unittest','test_execution','test_wf','-v'],cwd=C.HERE,capture_output=True,text=True)
    log=re.sub(r'Ran (\d+) tests in [0-9.]+s',r'Ran \1 tests (elapsed omitted)',proc.stdout+proc.stderr)
    (output/'TEST_RESULTS.txt').write_text(log);assert proc.returncode==0,log
    prev=None;prev_frames=None;origin=None;previous_end=None
    stages=[('CONTROL',datetime(2025,1,1,tzinfo=C.TZ))]+[(q['id'],datetime.fromisoformat(q['end'])) for q in SPEC['quarters']]
    for label,end in stages:
        d=output/label;d.mkdir(parents=True,exist_ok=True)
        primary,scalar,receipts=sources(root,end)
        G.feature_gate(primary,scalar,d)
        p=G.compute(primary,['TRAIL_375']);s=G.compute(scalar,['TRAIL_375'],True)
        G.persist(p,d/'primary');G.persist(s,d/'scalar')
        compare_outputs(p,s,'INDEPENDENT_REPLAY',d)
        C.write_json(d/'CAUSAL_PRIMARY.json',F.causal(p));C.write_json(d/'CAUSAL_SCALAR.json',F.causal(s))
        C.write_json(d/'SOURCE_RECEIPTS.json',receipts)
        C.write_json(d/'CHECKPOINT.json',checkpoint(p,primary,receipts,end))
        persist_features(primary,d)
        if label=='CONTROL':
            G.gate(p,d/'primary');G.gate(s,d/'scalar',True);G.multi_gate(p,d/'primary');G.multi_gate(s,d/'scalar')
            direct_canonical(p,'control','PR510_PRIMARY',d);direct_canonical(s,'control_scalar','PR510_SCALAR',d)
            published_tables(p,d);origin=p
        else:
            continuation(prev,p,prev_frames,primary,previous_end,d)
            # No following quarter has been read at this point.
            tables,arithmetic=A.build(p,origin,primary,receipts)
            C.write_json(d/'INDEPENDENT_ARITHMETIC.json',arithmetic)
            for name,rows in tables.items():C.write_csv(d/(name+'.csv'),rows)
            C.write_json(d/'TABLES.json',tables);render.report(tables,p,origin,d,label)
            if label=='W4':
                decision=A.decide(tables);C.write_json(d/'DECISION.json',decision);render.final(tables,decision,d)
        commit_stage(d,label,commits)
        prev=p;prev_frames=primary;previous_end=end
    C.write_json(output/'READ_AUDIT.json',{'status':'PASS','raw_file_opens':B.OPEN_EVENTS,'OHLC_2026_read':False,'timestamp_2026_decoded':False,
        'coverage_2026_computed':False,'2026_used_for_exit':False,'full_source_hashes_computed':False,'buffered_read_ahead':False,
        'allowed_files_only':True,'all_5_stages_two_readers':True,'strict_completion_cutoff':True,'data_pin':C.DATA_SHA,
        'audit_method':'Runtime Python open allowlist + unbuffered byte counters + independent prefix SHA + boundary poison/read-spy synthetic tests',
        'external_syscall_trace':'not available; application-level receipts and source inspection','future_suffix_order':'not inspected; source sortedness checked on allowed prefix only'})
    C.write_json(output/'RUNTIME.json',{'python':sys.version.split()[0],'pandas':pd.__version__,'freeze_commit':frozen['commit'],'labels':SPEC['labels']})

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--data-root',type=Path,default=Path('/workspace/market-pattern-data'));parser.add_argument('--output',type=Path,default=C.HERE/'results');parser.add_argument('--commit-stages',action='store_true')
    a=parser.parse_args()
    try:run(a.data_root,a.output,a.commit_stages)
    except Exception as exc:
        a.output.mkdir(parents=True,exist_ok=True)
        C.write_json(a.output/'STOP.json',{'status':'WF_INVALID','reason':repr(exc),'WF_results_usable':False,'STOP':True})
        raise
