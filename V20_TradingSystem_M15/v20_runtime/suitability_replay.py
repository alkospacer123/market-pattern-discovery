"""Adapters around the EXISTING V20-02/03 multisymbol replay functions.

Only offline admission masks differ. No modification of frozen code or source
quotes. Feature adapters/caches stay outside the repository. No broker imports.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import timedelta
import hashlib
import importlib.util
import math
from pathlib import Path
from types import SimpleNamespace
import json
import numpy as np
import pandas as pd

from .regime_monthly_comparison import ROOT, BAD, digest
from .market_reference_descriptive import SOURCE_SHA256
from .suitability_research import METHODS, MODES, trade_row, load_sources


def module(path):
    spec=importlib.util.spec_from_file_location('v20_existing_'+path.stem,path)
    obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj)
    return obj


def masks(frames,method,tracks,modern):
    result={};removed=0
    for symbol,source in frames.items():
        d=source.copy();instrument=symbol if modern else str(d.family.iloc[0])
        for mode in MODES:
            signal=d[mode].to_numpy(copy=True)
            for i in np.flatnonzero(signal):
                t=(d.Datetime.iat[i]+pd.Timedelta(minutes=15)).to_pydatetime()
                if tracks[mode,instrument,method].at(t)==BAD:
                    signal[i]=0;removed+=1
            d[mode]=signal
        result[symbol]=d
    return result,removed


def run_replays(archive,market,work,tracks,evidence):
    assert ROOT not in work.resolve().parents and work.resolve()!=ROOT
    _,_,published,input_hashes=load_sources()
    signature=hashlib.sha256(json.dumps(dict(inputs=input_hashes,
        code={str(p):digest(p) for p in (ROOT/'V20-02_AUDIT/replay_independent.py',ROOT/'V20-03/offline/stress_v20_03.py')},
        quotes={s:digest(market/s/(s+'_M15.csv')) for s in SOURCE_SHA256},zip=digest(archive),
        masks=[(m,r['strategy'],r['instrument'],str(r['decision']),tracks[r['strategy'],r['instrument'],m].at(r['decision']))
               for m in METHODS for r in published]),sort_keys=True).encode()).hexdigest()
    cache=work/'conditional_replay.json';metadata=work/'conditional_replay_receipt.json'
    if cache.exists() and metadata.exists():
        saved=json.loads(metadata.read_text())
        code_unchanged=all(digest(ROOT/name)==want for name,want in saved['receipt']['source_hashes'].items()
                           if not name.startswith('external/'))
        if saved['signature']==signature and saved['sha256']==digest(cache) and code_unchanged:
            value=json.loads(cache.read_text())
            for rows in value.values():
                for r in rows:
                    for name in ('entry','signal','exit','available'):r[name]=pd.Timestamp(r[name]).to_pydatetime()
            print('same admission masks and source SHA: reuse conditional replay',flush=True)
            return value,saved['receipt']
    q=module(ROOT/'V20-03/comparison/quote_diagnostics.py')
    b=module(ROOT/'V20-03/comparison/build_diagnostics.py')
    # The existing adapter checks hashes, reads the same 43 sources and rebuilds
    # only frozen input features, not the previous 4431-path research.
    old,sources,env=q.prepare_quarterly(archive,work)
    plan=pd.read_csv(ROOT/'V20-03/results/ROLL_DECISIONS.csv',parse_dates=['day']).fillna('')
    frames={};inputs=work/'marketdata_m15';inputs.mkdir(exist_ok=True)
    hashes={str(p.relative_to(ROOT)):digest(p) for p in [
        ROOT/'V20-02_AUDIT/replay_independent.py',ROOT/'V20-03/offline/stress_v20_03.py',
        ROOT/'V20-03/results/ROLL_DECISIONS.csv',
        ROOT/'research_original_v20/base.py',ROOT/'research_original_v20/run.py',
        ROOT/'research_original_v20/legacy_v4/study_v4.py',ROOT/'research_original_v20/legacy_v4/dependencies/study.py']}
    common=dict(np=np,pd=pd,math=math,defaultdict=defaultdict)
    base=ROOT/'research_original_v20';runner=ROOT/'V20-02_AUDIT/replay_independent.py'
    prepare=b.fn(base/'base.py','prepare',dict(common,ROOT=work,MODES=b.lit(base/'base.py','MODES')))
    sig=b.fn(base/'run.py','sig',common)
    signals=b.fn(base/'run.py','signals',dict(common,b=SimpleNamespace(prepare=prepare),M=b.lit(base/'run.py','M'),sig=sig))
    prep=b.fn(base/'legacy_v4/dependencies/study.py','prep',dict(common,ROOT=inputs))
    inside=b.fn(base/'legacy_v4/study_v4.py','add_indicators',dict(common,MODES=b.lit(base/'legacy_v4/study_v4.py','MODES')))
    for symbol,want in SOURCE_SHA256.items():
        p=market/symbol/(symbol+'_M15.csv');assert digest(p)==want
        hashes['external/'+symbol+'_M15.csv']=want
        link=inputs/p.name
        if not link.exists():link.symlink_to(p.resolve())
        assert digest(link)==want
        # Reading the same frozen functions preserves 2025 and available 2026.
        d=signals(symbol);d['INSIDE_DAY_RELEASE']=inside(prep(symbol),symbol).INSIDE_DAY_RELEASE
        frames[symbol]=d
    hashes['external/2018-2022.zip']=digest(archive)
    old_engine=q.fn(q.RUNNER,'replay',dict(env))
    # replay uses session/tick/maturity from the unchanged source environment.
    modern_engine=b.fn(runner,'run_one',dict(common,SYMS=b.SYMS,TICKS=q.TICKS,COLS=b.lit(runner,'COLS')))
    baseline=[r for rows in evidence.groups.values() for r in rows]
    replays={'BASELINE':baseline};receipt=dict(source_hashes=hashes,old_source_files=len(sources),
        original_signal_functions='UNCHANGED_AST',original_replay_functions='UNCHANGED_AST',
        baseline='Existing verified 1004 + reproduced 1589 ledger; no new baseline batch',methods={})
    # Necessary adapter check only: input signal keys equal the unchanged published
    # raw catalog. No path/price/stop outcome audit is repeated.
    _,_,published,_=load_sources()
    wanted={(r['strategy'],r['instrument'],r['signal']) for r in published}
    actual=set();choices={(r.family,pd.Timestamp(r.day)):r.chosen_contract for r in plan.itertuples()}
    for modern,ds in ((False,old),(True,frames)):
        for symbol,d in ds.items():
            instrument=symbol if modern else str(d.family.iloc[0])
            for mode in MODES:
                for i in np.flatnonzero(d[mode].to_numpy()):
                    t=d.Datetime.iat[i]
                    if modern or (2018<=t.year<=2022 and choices.get((instrument,d.day.iat[i]))==symbol):
                        actual.add((mode,instrument,t.to_pydatetime()))
    assert actual==wanted,('FROZEN_SIGNAL_ADAPTER',len(actual),len(wanted),list(actual^wanted)[:3])
    receipt['frozen_raw_catalog_parity']=dict(status='PASS',signals=len(actual))
    for method in METHODS[1:]:
        rows=[];status={}
        for modern,ds in ((False,old),(True,frames)):
            masked,removed=masks(ds,method,tracks,modern)
            if not removed:
                rows.extend(r for r in baseline if (r['instrument'] in SOURCE_SHA256)==modern)
                status['modern' if modern else 'old']=dict(masked_signals=0,replay='SKIP_IDENTICAL_BASELINE')
                continue
            censored=opened=0
            for n,mode in enumerate(MODES,1):
                if modern:
                    trades,meta=modern_engine(masked,n,mode,mode)
                    rows.extend(trade_row(r,True) for r in trades.to_dict('records'))
                    opened+=meta['unclosed']
                else:
                    trades,op,entries,events=old_engine(masked,plan,mode,n)
                    rows.extend(trade_row(r) for r in trades if r['stat_eligible'])
                    censored+=sum(not r['stat_eligible'] for r in trades);opened+=len(op)
            status['modern' if modern else 'old']=dict(masked_signals=removed,replay='PASS',
                censored_closed=censored,open_positions=opened)
        replays[method]=rows;receipt['methods'][method]=status
        print('frozen gated replay',method,len(rows),status,flush=True)
    cache.write_text(json.dumps(replays,default=str,separators=(',',':')))
    metadata.write_text(json.dumps(dict(signature=signature,sha256=digest(cache),receipt=receipt)))
    return replays,receipt
