"""Bounded 2012 extension using the existing LOCKED_V1 functions, not a new tester.

Quotes and feature caches are external. Only date/manifest admission assertions
are adapted; frozen signal, roll and execution expressions are retained exactly.
Early MIX off-grid prices are retained and explicitly fail source certification.
"""
from __future__ import annotations
import argparse
import ast
from collections import Counter
from datetime import datetime, timedelta
import hashlib
import io
import json
import math
from pathlib import Path
from types import SimpleNamespace
import zipfile

import numpy as np
import pandas as pd

from .suitability_replay import module
from .suitability_research import trade_row, MODES
from .regime_monthly_comparison import ROOT, FOLDER, digest, read_csv, dt
from .regime_research import dump_csv, path_quality
from .market_suitability import M15Bar

ZIP_SHA='9b253772c6533235b1db0893b6b42472be86dff0862b6af390089608ac561fa2'
RUNNER=ROOT/'V20-03/offline/stress_v20_03.py'
PREFIX='V20_2012_2026_'


def adapted_function(name, env, *, start_year=2018, manifest_count=88):
    node=next(n for n in ast.parse(RUNNER.read_text()).body if isinstance(n,ast.FunctionDef) and n.name==name)
    changes=[]
    if name=='replay':
        matches=[n for n in ast.walk(node) if isinstance(n,ast.Compare) and ast.unparse(n)=='2018 <= t.year <= 2022']
        assert len(matches)==1
        matches[0].left=ast.Constant(start_year)
        changes.append('SIGNAL_YEAR_LOWER_BOUND')
    if name=='read_inputs':
        for n in ast.walk(node):
            if isinstance(n,ast.Assert) and ast.unparse(n.test)=='len(ds) == 43':
                n.test.comparators[0]=ast.Constant(manifest_count);changes.append('MANIFEST_COUNT')
            if isinstance(n,ast.Assert) and isinstance(n.msg,ast.Tuple) and ast.unparse(n.msg).startswith("('TICK_GRID_FAIL'"):
                # Never infer a replacement tick or round/repair source prices.
                # The exact failing cells remain in maps.grid_failures.
                n.test=ast.Constant(True);changes.append('GRID_CERTIFICATION_REPORTED_NOT_SILENCED')
        assert len(changes)==2
    ns=dict(env)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),str(RUNNER),'exec'),ns)
    return ns[name]


def ingest(archive, old_archive, work, output):
    assert digest(archive)==ZIP_SHA
    assert digest(old_archive)=='df1aaf4d23757d18689dfdf61d6fc1ec77f0b26ae7d8af1193322d460707888a'
    work=work.resolve()
    assert ROOT not in work.parents and work!=ROOT
    qd=module(ROOT/'V20-03/comparison/quote_diagnostics.py')
    env=qd.source_environment(work/'validated');env['FAMILIES']=['MIX','Si']
    root=work/'history_2018_2022_original';root.mkdir(parents=True,exist_ok=True)
    overlap=[];members=[];quarantine=[]
    with zipfile.ZipFile(archive) as z, zipfile.ZipFile(old_archive) as old:
        for name in sorted(n for n in z.namelist() if n.endswith('.csv')):
            rel=Path(name)
            assert not rel.is_absolute() and '..' not in rel.parts and rel.parts[0] in ('si','mix')
            b=z.read(name);p=root/rel;p.parent.mkdir(parents=True,exist_ok=True)
            if p.exists():assert p.read_bytes()==b
            else:p.write_bytes(b)
            members.append(dict(file=name,sha256=hashlib.sha256(b).hexdigest(),bytes=len(b)))
            if name in old.namelist():
                assert b==old.read(name),('OVERLAP_DIFF',name)
                overlap.append(name)
            d=pd.read_csv(io.BytesIO(b),sep=';',parse_dates=['Datetime'])
            bad=(d.High<d[['Open','Low','Close']].max(axis=1)) | (d.Low>d[['Open','High','Close']].min(axis=1))
            assert (d[['Open','High','Low','Close']]>0).all().all() and (d.Volume>0).all()
            assert d.Datetime.is_monotonic_increasing and not d.Datetime.duplicated().any()
            for r in d[bad].to_dict('records'):
                quarantine.append(dict(file=name,**{k:str(v) for k,v in r.items()},reason='OHLC_INCONSISTENT_SOURCE_UNCHANGED'))
            dest=work/'validated/history_2018_2022_original'/rel;dest.parent.mkdir(parents=True,exist_ok=True)
            if bad.any():d[~bad].to_csv(dest,sep=';',index=False,lineterminator='\n')
            elif not dest.exists():dest.write_bytes(b)
    raw,maps,sessions,gaps=adapted_function('read_inputs',env)()
    assert sum(map(len,raw.values()))==299998-len(quarantine) and len(overlap)==40
    for bad in quarantine:
        c=Path(bad['file']).stem.removesuffix('_M15');d=raw[c]
        d['segment']+=np.asarray(d.Datetime>pd.Timestamp(bad['Datetime']),dtype=int)
    roll=qd.fn(RUNNER,'roll_plan',env);plan=roll(sessions)
    frozen={str(p.relative_to(ROOT)):digest(p) for p in (ROOT/'research_original_v20').rglob('*.py')}
    sig=digest(RUNNER)+''.join(frozen.values())
    cache=work/'features';cache.mkdir(exist_ok=True)
    frames={}
    oldcache=Path('/workspace/work/v20-suitability/quarterly_features')
    for c,d in raw.items():
        h=digest(root/maps.loc[maps.contract.eq(c),'file'].iloc[0]);h+=str([r for r in quarantine if Path(r['file']).stem.removesuffix('_M15')==c]);p=cache/(c+'.pkl');rp=cache/(c+'.json')
        if p.exists() and rp.exists() and json.loads(rp.read_text())==dict(source=h,code=sig,cache=digest(p)):
            frames[c]=pd.read_pickle(p)
        elif (oldcache/(c+'.pkl')).exists() and (oldcache/(c+'.json')).exists():
            receipt=json.loads((oldcache/(c+'.json')).read_text())
            # Validate both source and exact feature-generation code receipt.
            signature=hashlib.sha256(''.join(digest(p0) for p0 in [RUNNER,qd.BASE/'base.py',qd.BASE/'run.py',qd.BASE/'legacy_v4/study_v4.py',qd.BASE/'legacy_v4/dependencies/study.py']).encode()).hexdigest()
            assert receipt['source_sha256']+'[]'==h and receipt['code_signature']==signature and receipt['cache_sha256']==digest(oldcache/(c+'.pkl'))
            frames[c]=pd.read_pickle(oldcache/(c+'.pkl'))
        else:
            frames[c]=env['prepare_contract'](d)
        if not p.exists():
            frames[c].to_pickle(p);rp.write_text(json.dumps(dict(source=h,code=sig,cache=digest(p))))
    audit=dict(input_head='089e6b5d12b773e09029f0db94df8857014015fa',zip_sha256=ZIP_SHA,
        old_zip_sha256=digest(old_archive),members=members,contracts=len(raw),bars=299998,validated_bars=sum(map(len,raw.values())),quarantined=quarantine,
        overlap_files=len(overlap),overlap_byte_identical=overlap,overlap_OHLCV_timestamps_series='PASS EXACT BYTES',
        source_timestamp='NAIVE_MSK_OPEN_ASSUMED_NOT_VENDOR_VERIFIED',roll='UNCHANGED_LOCKED_V1',
        changes=['DATE_GUARD_2018_TO_2012','MANIFEST_COUNT_43_TO_88','OFFGRID_REPORTED_WITH_UNCERTIFIED_EARLY_MIX','TWO_INVALID_OHLC_QUARANTINED_SEGMENT_RESET'],
        grid_certification='FAIL EARLY_MIX',tick='UNCHANGED Si=1 MIX=25; early MIX actual exchange C1 NOT AVAILABLE',
        frozen_hashes=frozen,runner_sha256=digest(RUNNER),unknown_holes=len(gaps),sessions=len(sessions),
        incomplete_sessions=int((~sessions.prior_day_eligible).sum()),
        inventory=json.loads(maps.to_json(orient='records',date_format='iso')))
    audit['annual_bars']={f:dict(Counter(str(t.year) for d in raw.values() if d.family.iat[0]==f for t in d.Datetime)) for f in ('Si','MIX')}
    audit['grid_failures']=int(maps.grid_failures.sum())
    (output/'V20_2012_2022_SOURCE_AUDIT.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
    dump_csv(output/(PREFIX+'ROLL_DECISIONS.csv'),plan.to_dict('records'))
    print('SOURCE AUDIT',len(raw),audit['bars'],'grid cells',audit['grid_failures'],flush=True)
    return raw,frames,plan,env,audit,qd


def run(archive, old_archive, work, output=FOLDER):
    output.mkdir(parents=True,exist_ok=True)
    raw,frames,plan,env,audit,qd=ingest(archive,old_archive,work,output)
    early=[];censored=[];opens=[];entries=[];continuous_overlap=[]
    fn=adapted_function('replay',env,start_year=2012)
    for i,m in enumerate(MODES,1):
        cl,op,en,_=fn(frames,plan,m,i)
        early.extend(r for r in cl if r['stat_eligible'] and dt(r['entry_dt']).year<2018)
        censored.extend(r for r in cl if not r['stat_eligible'] and dt(r['entry_dt']).year<2018)
        opens.extend(op);entries.extend(r for r in en if dt(r['entry_dt']).year<2018)
        cont=[r for r in cl if r['stat_eligible'] and dt(r['entry_dt']).year>=2018]
        continuous_overlap.append(dict(strategy=m,trades=len(cont),net_C1_R=sum(r['net_C1_R'] for r in cont),
            universe='Si+MIX',start_state='CONTINUOUS_FROM_2012; UNKNOWN_POSITION_NOT_CLOSED'))
        print('REPLAY',m,'early',sum(r['account']==m for r in early),'censored',sum(r['account']==m for r in censored),flush=True)
    # Matched-universe overlap: retain CNY neither in candidates nor in cap usage.
    origplan=pd.read_csv(ROOT/'V20-03/results/ROLL_DECISIONS.csv').fillna('')
    origplan.day=pd.to_datetime(origplan.day)
    previous={c:d for c,d in frames.items() if c in {Path(x).stem.removesuffix('_M15') for x in audit['overlap_byte_identical']}}
    overlap=[]
    fixed=qd.fn(RUNNER,'replay',env)
    for i,m in enumerate(MODES,1):
        a,_,_,_=fixed(previous,origplan,m,i)
        b,_,_,_=adapted_function('replay',env)(previous,plan,m,i)
        assert a==b,('OVERLAP_REPLAY_MISMATCH',m)
        overlap.append(dict(strategy=m,universe='Si+MIX',trades=sum(x['stat_eligible'] for x in a),
            net_C1_R=sum(x['net_C1_R'] for x in a if x['stat_eligible']),parity='PASS EXACT RECORDS'))
    dump_csv(output/'V20_2012_2022_REPLAY_TRADES.csv',early)
    dump_csv(output/(PREFIX+'CENSORED_TRADES.csv'),censored)
    dump_csv(output/(PREFIX+'ENTRIES.csv'),entries)
    audit['overlap_replay']=overlap
    audit['continuous_replay_overlap']=continuous_overlap
    audit['early_open_positions']=opens
    # Raw trajectories only for NEW years; old 4431 outcomes are not rescanned.
    choices={(r.family,int(pd.Timestamp(r.day).value)):r.chosen_contract for r in plan.itertuples()}
    days={f:np.unique(np.concatenate([d.day.to_numpy('datetime64[ns]').astype('int64') for d in frames.values() if d.family.iat[0]==f])) for f in ('Si','MIX')}
    for position in audit['early_open_positions']:
        f=position['family'];index=position['entry_session_index']+2
        due=pd.Timestamp(days[f][index]) if index<len(days[f]) else None
        stamps=[d.loc[d.day.eq(due),'Datetime'].min() for d in frames.values() if d.family.iat[0]==f and d.day.eq(due).any()]
        position['unknown_after']=str(min(stamps)) if stamps else None
        position['scope_end']='2018-01-01 00:00:00'
        position['scope_note']='Published 2018 reference restarts independently; no invented closure/cash continuity.'
    events=[];verified=0
    for c,d in frames.items():
        if d.Datetime.min().year>=2018:continue
        family=d.family.iat[0]
        q=qd.QuoteFrame(d,c,family,'2018-2022',days[family],env,choices,{})
        for trade in [r for r in early+censored if r['contract']==c]:
            # Reuse the existing detailed quote/ATR/first-stop/exit checker on
            # ONLY the new observations. No second audit of old 4431 outcomes.
            qd.verify_and_measure_trade(SimpleNamespace(**trade,period='2018-2022'),q)
            verified+=1
        bars=[M15Bar(t.to_pydatetime(),float(o),float(h),float(l),float(cl),float(v)) for t,o,h,l,cl,v in d[env['RAWCOLS']].itertuples(index=False,name=None)]
        for m in MODES:
            for j in np.flatnonzero((d[m].to_numpy()!=0)&q.selected&(q.y>=2012)&(q.y<2018)):
                t=d.Datetime.iat[j];side=int(d[m].iat[j]);en=j+1
                rec=dict(strategy=m,instrument=family,contract=c,signal=t,decision=t+pd.Timedelta(minutes=15),outcome=None,horizon_status='NO_NEXT_OPEN')
                if en<len(q.t) and q.t[en]-q.t[j]==900000000000 and q.feature_segment[j]==q.feature_segment[en] and choices.get((family,int(q.day[en])))==c:
                    target=q.o[en]-side*2*q.a[j];tick=q.tick[en]
                    stop=(math.floor(target/tick+1e-9) if side==1 else math.ceil(target/tick-1e-9))*tick
                    risk=abs(q.o[en]-stop);h=q.horizon(en,side,q.o[en],risk);rec['horizon_status']=h['horizon_status']
                    if h['horizon_status']=='OBSERVED_V1':
                        e=dict(instrument=family,signal=t.to_pydatetime(),entry_time=d.Datetime.iat[en].to_pydatetime(),
                            available=dt(h['horizon_exit_dt']),side=side,entry=q.o[en],stop=stop,risk=risk,
                            raw_R=h['horizon_R'],stop_touch=h['horizon_stop_touch'])
                        e.update(path_quality(e,bars));e['stop_touch']=str(e['stop_touch']);rec['outcome']=e
                events.append(rec)
    dump_csv(output/(PREFIX+'NEW_RAW_PATHS.csv'),[dict(r,outcome=json.dumps(r['outcome'],default=str,sort_keys=True)) for r in events])
    audit['early_raw']=dict(Counter(r['horizon_status'] for r in events))
    assert verified==len(early)+len(censored)
    audit['new_trade_quote_ATR_NEXT_OPEN_first_exit_checks']=dict(status='PASS',checked=verified)
    audit['early_trades']=len(early);audit['early_censored']=len(censored)
    audit['full_early_replay']='FAIL_PARTIAL_MISSING_CONTRACT_EXIT' if audit['early_open_positions'] else 'PASS_CONDITIONAL_LOCKED_V1'
    (output/'V20_2012_2022_SOURCE_AUDIT.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2,default=str)+'\n')
    print('DONE',audit['early_trades'],audit['early_raw'],flush=True)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--archive',type=Path,required=True);ap.add_argument('--old-archive',type=Path,required=True)
    ap.add_argument('--work',type=Path,required=True);args=ap.parse_args()
    run(args.archive,args.old_archive,args.work)


if __name__=='__main__':main()
