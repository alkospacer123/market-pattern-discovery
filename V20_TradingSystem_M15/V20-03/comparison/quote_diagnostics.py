#!/usr/bin/env python3
"""Quote diagnostics for frozen V20-03. No strategy/parameter/roll changes.

Source ZIP and all temporary candle adapters/caches stay OUTSIDE the repository.
This computes source features and reads existing trades; it does not replay the
quarterly portfolio or rerun historical causality/repeat checks.

Use --gap-v1 for the one required late methodology diagnostic: the pre-existing
V1 reset/censor pipeline on identical late inputs, never a rule/parameter search.
See ../README_RUN_RU.md for an external-input reproduction command.
"""
from __future__ import annotations
import argparse, ast, hashlib, json, math, sys, tempfile, warnings, zipfile
from pathlib import Path
from types import SimpleNamespace
from collections import defaultdict
import numpy as np
import pandas as pd

sys.dont_write_bytecode=True
warnings.filterwarnings('ignore',category=FutureWarning)
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
STAGE=ROOT/'V20-03'
BASE=ROOT/'research_original_v20'
RUNNER=STAGE/'offline/stress_v20_03.py'
MODES=['SHALLOW_PULLBACK','OBV_PRESSURE','INSIDE_DAY_RELEASE']
ALL='ALL_INDEPENDENT_ACCOUNTS'
EXPECTED_ZIP='df1aaf4d23757d18689dfdf61d6fc1ec77f0b26ae7d8af1193322d460707888a'
TICKS={'CNYRUBF':.001,'GLDRUBF':.1,'IMOEXF':.5,'USDRUBF':.01}
PROXY={'CNY':'CNYRUBF','MIX':'IMOEXF','Si':'USDRUBF'}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fn(path,name,env):
    node=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name==name)
    ns=dict(env);exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),ns)
    return ns[name]
def lit(path,name):
    return ast.literal_eval(next(n.value for n in ast.parse(path.read_text()).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets)))
def save(rows,name):pd.DataFrame(rows).to_csv(OUT/name,index=False,float_format='%.12g',lineterminator='\n')

def source_environment(work):
    env=dict(np=np,pd=pd,math=math,ast=ast,tempfile=tempfile,Path=Path,SimpleNamespace=SimpleNamespace,
      ROOT=work,BASE=BASE,RAWCOLS=lit(RUNNER,'RAWCOLS'),FEATURES=['atr','ema50','ema200',*MODES],
      MODES=MODES,FAMILIES=lit(RUNNER,'FAMILIES'),PROXY=PROXY,sha=sha)
    for name in ['extract','literal','session','tick','maturity','cutoff','broken','frozen_signals','prepare_contract','read_inputs']:
        env[name]=fn(RUNNER,name,env)
    return env

def prepare_quarterly(source,work):
    source=source.resolve();work=work.resolve()
    assert ROOT not in work.parents and work!=ROOT
    assert sha(source)==EXPECTED_ZIP,'Uploaded ZIP is not the original V20-03 source'
    expected=json.loads((STAGE/'results/RUN_METADATA.json').read_text())['source_hashes']
    rawroot=work/'history_2018_2022_original';rawroot.mkdir(parents=True,exist_ok=True)
    sources=[]
    with zipfile.ZipFile(source) as z:
        csvs=[n for n in z.namelist() if n.lower().endswith('.csv')]
        assert len(csvs)==43
        for name in csvs:
            rel=Path(name);assert not rel.is_absolute() and '..' not in rel.parts
            data=z.read(name);h=hashlib.sha256(data).hexdigest()
            assert h==expected['history_2018_2022_original/'+rel.as_posix()],name
            dest=rawroot/rel;dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists():assert sha(dest)==h
            else:dest.write_bytes(data)
            sources.append(dict(path=str(dest),sha256=h,bytes=len(data),role='UPLOADED_ORIGINAL_QUARTERLY_M15'))
    env=source_environment(work)
    raw,maps,sessions,gaps=env['read_inputs']()
    assert sum(map(len,raw.values()))==149028 and len(gaps)==409
    # Verify raw input segmentation and summaries against published artifacts.
    stored=pd.read_csv(STAGE/'results/INVALID_INTERVALS.csv')
    for c in stored.columns:assert gaps[c].astype(str).tolist()==stored[c].astype(str).tolist(),c
    cache=work/'quarterly_features';cache.mkdir(exist_ok=True)
    signature=hashlib.sha256(''.join(sha(p) for p in [RUNNER,BASE/'base.py',BASE/'run.py',BASE/'legacy_v4/study_v4.py',BASE/'legacy_v4/dependencies/study.py']).encode()).hexdigest()
    frames={}
    for contract,d in raw.items():
        p=cache/(contract+'.pkl');receipt=cache/(contract+'.json')
        valid=False
        if p.exists() and receipt.exists():
            r=json.loads(receipt.read_text());valid=r['source_sha256']==expected['history_2018_2022_original/'+maps.loc[maps.contract.eq(contract),'file'].iloc[0]] and r['code_signature']==signature and r['cache_sha256']==sha(p)
        if valid:features=pd.read_pickle(p)
        else:
            features=env['prepare_contract'](d);features.to_pickle(p)
            receipt.write_text(json.dumps(dict(source_sha256=expected['history_2018_2022_original/'+maps.loc[maps.contract.eq(contract),'file'].iloc[0]],code_signature=signature,cache_sha256=sha(p))))
        assert len(features)==len(d)
        frames[contract]=features
        print('quote features',contract,len(features),'segments',features.segment.nunique(),flush=True)
    return frames,sources,env

class QuoteFrame:
    def __init__(self,d,contract,family,period,days,env,choices,roll_buckets):
        self.d=d.reset_index(drop=True);d=self.d
        self.contract=contract;self.family=family;self.period=period;self.env=env
        self.t=d.Datetime.to_numpy('datetime64[ns]').astype('int64')
        self.lookup={int(t):i for i,t in enumerate(self.t)}
        self.day=d.day.to_numpy('datetime64[ns]').astype('int64')
        self.day_index={int(t):i for i,t in enumerate(days)}
        self.ses=np.array([self.day_index[int(t)] for t in self.day],dtype=int)
        self.days=days;self.first={}
        for j,k in enumerate(self.day):self.first.setdefault(int(k),j)
        self.o=d.Open.to_numpy(float);self.h=d.High.to_numpy(float);self.l=d.Low.to_numpy(float);self.c=d.Close.to_numpy(float)
        self.a=d.atr.to_numpy(float);self.vol=d.Volume.to_numpy(float)
        self.feature_segment=d.segment.to_numpy(int) if 'segment' in d else np.zeros(len(d),dtype=int)
        if 'segment' in d:self.obs_segment=self.feature_segment
        else:
            # V1 observability diagnostic only. Modern features remain the original
            # continuous features: no modern reset/replay/selection rule is added.
            bad=np.zeros(len(d),dtype=int)
            for j in range(1,len(d)):bad[j]=env['broken'](d.Datetime.iat[j-1],d.Datetime.iat[j])
            self.obs_segment=np.cumsum(bad)
        self.missing_session=np.r_[0,np.cumsum(np.diff(self.ses)>1)]
        self.tick=d.tick.to_numpy(float) if 'tick' in d else np.full(len(d),TICKS[family])
        self.selected=np.array([choices.get((family,int(day)),'')==contract for day in self.day]) if period=='2018-2022' else np.ones(len(d),dtype=bool)
        self.roll=np.array([roll_buckets.get((family,int(day),contract),'NOT_APPLICABLE') for day in self.day])
        self.y=d.Datetime.dt.year.to_numpy(int)
        volume=pd.Series(self.vol);close=pd.Series(self.c);low=pd.Series(self.l);high=pd.Series(self.h)
        clv=((close-low)-(high-close))/(high-low).replace(0,np.nan)
        self.pressure=np.full(len(d),np.nan);self.relative_volume=np.full(len(d),np.nan)
        for seg in np.unique(self.feature_segment):
            ind=np.flatnonzero(self.feature_segment==seg);v=volume.iloc[ind].reset_index(drop=True);f=(clv.iloc[ind].reset_index(drop=True).fillna(0)*v)
            self.pressure[ind]=(f.shift(1).rolling(12,min_periods=12).sum()/v.shift(1).rolling(12,min_periods=12).sum().replace(0,np.nan)).to_numpy()
            self.relative_volume[ind]=(v/v.shift(1).rolling(20,min_periods=20).mean()).to_numpy()

    def path_status(self,en,end):
        if end<en:return 'UNAVAILABLE'
        if self.obs_segment[end]!=self.obs_segment[en]:return 'UNKNOWN_INTRASESSION_GAP'
        if self.missing_session[end]!=self.missing_session[en]:return 'CONTRACT_SESSION_MISSING'
        return 'OBSERVED_V1'

    def horizon(self,en,side,entry,risk):
        target=self.ses[en]+2
        if target>=len(self.days):return dict(horizon_status='END_OF_ARCHIVE')
        end=self.first.get(int(self.days[target]),-1)
        if end<en:return dict(horizon_status='CONTRACT_THIRD_SESSION_UNAVAILABLE')
        status=self.path_status(en,end)
        if end==en:return dict(horizon_status='INVALID_ZERO_HORIZON')
        hi=max(float(self.h[en:end].max()),self.o[end]);lo=min(float(self.l[en:end].min()),self.o[end])
        mfe=max(0,(hi-entry) if side==1 else (entry-lo))/risk
        mae=max(0,(entry-lo) if side==1 else (hi-entry))/risk
        move=side*(self.o[end]-entry)/risk
        return dict(horizon_status=status,horizon_exit_dt=str(self.d.Datetime.iat[end]),horizon_R=move,
                    horizon_MFE_R=mfe,horizon_MAE_R=mae,horizon_stop_touch=bool(mae>=1-1e-7))

def frame_context(old,modern,env):
    plan=pd.read_csv(STAGE/'results/ROLL_DECISIONS.csv').fillna('')
    choices={(r.family,int(pd.Timestamp(r.day).value)):r.chosen_contract for r in plan.itertuples()}
    family_days={}
    for family in PROXY:
        family_days[family]=np.unique(np.concatenate([d.day.to_numpy('datetime64[ns]').astype('int64') for c,d in old.items() if d.family.iat[0]==family]))
    buckets={}
    for family,z in plan.groupby('family',sort=False):
        z=z.sort_values('day');last='';age=-1;days=family_days[family]
        for r in z.itertuples():
            c=r.chosen_contract;day=int(pd.Timestamp(r.day).value)
            if not c:continue
            if c!=last:age=0;last=c
            else:age+=1
            before=days[days<int(env['cutoff'](c).value)]
            last3=set(map(int,before[-3:]))
            bucket='FIRST_3_SELECTED_SESSIONS' if age<3 else 'LAST_3_BEFORE_LOCKED_CUTOFF' if day in last3 else 'INTERIOR'
            buckets[(family,day,c)]=bucket
    result={}
    for c,d in old.items():
        f=d.family.iat[0];result[('2018-2022',c)]=QuoteFrame(d,c,f,'2018-2022',family_days[f],env,choices,buckets)
    for s,d in modern.items():
        days=np.unique(d.day.to_numpy('datetime64[ns]').astype('int64'))
        result[('2023-2026',s)]=QuoteFrame(d,s,s,'2023-2026',days,env,{}, {})
    return result,choices

def existing_trades():
    old=pd.read_csv(STAGE/'results/ALL_OBSERVED_CLOSED.csv');old['period']='2018-2022';old['instrument']=old.family
    late=pd.read_csv(OUT/'DIAGNOSTIC_REPLAY_TRADES.csv').rename(columns={'net_R':'net_C1_R'})
    late['period']='2023-2026';late['contract']=late.symbol;late['family']=late.symbol;late['instrument']=late.symbol
    late['stat_eligible']=True;late['signal_bar_dt']=pd.to_datetime(late.signal_dt)-pd.Timedelta(minutes=15)
    late['tick_entry']=late.symbol.map(TICKS);late['tick_exit']=late.tick_entry
    return pd.concat([old,late],ignore_index=True)

def verify_and_measure_trade(r,q):
    en=q.lookup[int(pd.Timestamp(r.entry_dt).value)];ex=q.lookup[int(pd.Timestamp(r.exit_dt).value)]
    sg=q.lookup[int(pd.Timestamp(r.signal_bar_dt).value)]
    assert en==sg+1 and q.t[en]-q.t[sg]==900000000000
    assert int(q.d[r.account].iat[sg])==r.side
    assert abs(q.o[en]-r.entry)<=q.tick[en]*1e-7
    stop=(math.floor((r.entry-r.side*2*q.a[sg])/q.tick[en]+1e-9) if r.side==1 else math.ceil((r.entry-r.side*2*q.a[sg])/q.tick[en]-1e-9))*q.tick[en]
    assert abs(stop-r.stop)<=q.tick[en]*1e-7
    assert math.isclose(abs(r.entry-stop),r.risk,abs_tol=1e-7,rel_tol=1e-10)
    found=None
    for j in range(en,ex+1):
        tick=q.tick[j];eps=tick*1e-7
        touch=(r.side==1 and q.l[j]<=stop+eps) or (r.side==-1 and q.h[j]>=stop-eps)
        gap=(r.side==1 and q.o[j]<=stop+eps) or (r.side==-1 and q.o[j]>=stop-eps)
        if j==en:
            if touch:found=(j,4,stop)
        elif q.ses[j]-q.ses[en]>=2:found=(j,3,q.o[j])
        elif gap:found=(j,2,q.o[j])
        elif touch:found=(j,1,stop)
        if found is not None:break
    assert found is not None and found[0]==ex and found[1]==r.exit_reason,(r.account,r.contract,r.entry_dt,found,r.exit_dt,r.exit_reason)
    assert math.isclose(found[2],r.exit,abs_tol=q.tick[ex]*1e-7)
    status=q.path_status(en,ex)
    if r.period=='2018-2022':assert bool(r.stat_eligible)==(status=='OBSERVED_V1')
    prehigh=float(q.h[en:ex].max()) if ex>en else r.entry
    prelow=float(q.l[en:ex].min()) if ex>en else r.entry
    favorable=max(r.entry,prehigh,q.o[ex]) if r.side==1 else min(r.entry,prelow,q.o[ex])
    mfe=max(0,r.side*(favorable-r.entry)/r.risk)
    rec=dict(record_type='EXECUTED_TRADE',period=r.period,strategy=r.account,instrument=r.family,contract=r.contract,
      side=r.side,signal_bar_dt=str(r.signal_bar_dt),entry_dt=r.entry_dt,entry_session=r.entry_session,exit_dt=r.exit_dt,
      entry=r.entry,stop=r.stop,risk=r.risk,net_C1_R=r.net_C1_R,exit_reason=int(r.exit_reason),stat_eligible=bool(r.stat_eligible),
      actual_path_status=status,definite_MFE_before_exit_R=mfe,loss=r.net_C1_R<0,
      definite_favorable_then_loss=(r.net_C1_R<0 and mfe>1e-7),definite_1R_then_loss=(r.net_C1_R<0 and mfe>=1-1e-7),
      signal_relative_volume=q.relative_volume[sg],signal_pressure=q.pressure[sg],ATR14_price_pct=100*q.a[sg]/r.entry,roll_bucket=q.roll[en],
      **q.horizon(en,int(r.side),r.entry,r.risk))
    return rec

def admission_index(trades):
    alltr=trades[['period','account','family','contract','side','entry_dt','exit_dt','entry_session']].copy()
    meta=json.loads((OUT/'VERIFICATION.json').read_text())['replay_meta']
    for mode,m in meta.items():
        for p in m['terminal_positions']:
            en=pd.Timestamp(p['entry_dt'])
            alltr.loc[len(alltr)]=['2023-2026',mode,p['symbol'],p['symbol'],p['side'],str(en),str(pd.Timestamp.max.floor('s')),str((en-pd.Timedelta(hours=9)).date())]
    alltr['en']=pd.to_datetime(alltr.entry_dt).astype('int64');alltr['ex']=pd.to_datetime(alltr.exit_dt).astype('int64')
    alltr['dayn']=pd.to_datetime(alltr.entry_session).astype('int64')
    old_order={'CNY':0,'MIX':1,'Si':2};new_order={'CNYRUBF':0,'GLDRUBF':1,'IMOEXF':2,'USDRUBF':3}
    alltr['order']=[(old_order if p=='2018-2022' else new_order)[f] for p,f in zip(alltr.period,alltr.family)]
    return {(p,a):q for (p,a),q in alltr.groupby(['period','account'])}

def raw_signal_rows(context,choices,trades):
    by_account=admission_index(trades);result=[]
    for (period,contract),q in context.items():
        order=({'CNY':0,'MIX':1,'Si':2} if period=='2018-2022' else {'CNYRUBF':0,'GLDRUBF':1,'IMOEXF':2,'USDRUBF':3})[q.family]
        for mode in MODES:
            tr=by_account[(period,mode)];same=tr[tr.family.eq(q.family)]
            for i in np.flatnonzero((q.d[mode].to_numpy()!=0)&q.selected&(q.y>=2018 if period=='2018-2022' else q.y>=2023)):
                side=int(q.d[mode].iat[i]);rec=dict(record_type='RAW_SIGNAL',period=period,strategy=mode,instrument=q.family,contract=contract,
                  side=side,signal_bar_dt=str(q.d.Datetime.iat[i]),year=int(q.y[i]),roll_bucket=q.roll[i],
                  signal_relative_volume=q.relative_volume[i],signal_pressure=q.pressure[i],ATR14_price_pct=100*q.a[i]/q.c[i],
                  removed_instruments_direct_cap_block=False,cap_blocking_instruments='')
                en=i+1
                if en>=len(q.t) or q.t[en]-q.t[i]!=900000000000:
                    rec.update(admission='NO_NEXT_OPEN',horizon_status='NO_NEXT_OPEN');result.append(rec);continue
                rec['entry_dt']=str(q.d.Datetime.iat[en]);rec['entry_session']=str(pd.Timestamp(q.day[en]).date())
                if q.feature_segment[en]!=q.feature_segment[i] or (period=='2018-2022' and choices.get((q.family,int(q.day[en])))!=contract):
                    rec.update(admission='CONTRACT_OR_SEGMENT_ROLLED',horizon_status='INVALID_PENDING');result.append(rec);continue
                target=q.o[en]-side*2*q.a[i]
                stop=(math.floor(target/q.tick[en]+1e-9) if side==1 else math.ceil(target/q.tick[en]-1e-9))*q.tick[en]
                risk=abs(q.o[en]-stop)
                rec.update(entry=q.o[en],stop=stop,risk=risk,**q.horizon(en,side,q.o[en],risk))
                occupied=((same.en<=q.t[i])&(same.ex>q.t[i])).any()
                used=((same.dayn==q.day[i])&(same.en<=q.t[i])).any()
                earlier=tr[(tr.dayn==q.day[en])&((tr.en<q.t[en])|((tr.en==q.t[en])&(tr.order<order)))]
                hit=same[(same.en==q.t[en])&same.contract.eq(contract)&same.side.eq(side)]
                if occupied:reason='POSITION_OCCUPIED_AT_SIGNAL_CLOSE'
                elif used:reason='FAMILY_ALREADY_ENTERED_SESSION'
                elif len(earlier)>=2:
                    reason='ACCOUNT_TWO_ENTRY_CAP';rec['cap_blocking_instruments']=';'.join(earlier.family.tolist())
                    pair={'MIX','Si'} if period=='2018-2022' else {'IMOEXF','USDRUBF'}
                    rec['removed_instruments_direct_cap_block']=q.family in pair and int(earlier.family.isin(pair).sum())<2
                elif len(hit)==1:reason='EXECUTED'
                else:reason='UNEXPLAINED'
                rec['admission']=reason;result.append(rec)
    result=pd.DataFrame(result)
    assert not result.admission.eq('UNEXPLAINED').any(),result[result.admission.eq('UNEXPLAINED')].head().to_dict('records')
    expected={'2018-2022':1016,'2023-2026':1590}
    assert result[result.admission.eq('EXECUTED')].groupby('period').size().to_dict()==expected
    return result

def quote_market_rows(context):
    market=[]
    for (period,contract),q in context.items():
        for year in np.unique(q.y):
            if year<2018:continue
            ind=np.flatnonzero(q.selected&(q.y==year))
            if not len(ind):continue
            a=100*q.a[ind]/q.c[ind];a=a[np.isfinite(a)]
            horizon=[];horizon_candidates=0
            for i in ind:
                en=i+1
                if en>=len(q.t) or q.t[en]-q.t[i]!=900000000000 or not np.isfinite(q.a[i]):continue
                horizon_candidates+=1;target=q.ses[en]+2
                end=q.first.get(int(q.days[target]),-1) if target<len(q.days) else -1
                if end<en or q.path_status(en,end)!='OBSERVED_V1':continue
                horizon.append((q.o[end]-q.o[en])/(2*q.a[i]))
            rec=dict(record_type='MARKET_CONTRACT_YEAR',period=period,strategy='ALL',instrument=q.family,contract=contract,year=int(year),status='VERIFIED_ORIGINAL_QUOTES',
              bars=len(ind),warmed_bars=int(q.d.ema200.iloc[ind].notna().sum()),ATR_values=a.tolist(),volume_values=q.vol[ind].tolist(),
              relative_volume_values=q.relative_volume[ind][np.isfinite(q.relative_volume[ind])].tolist(),
              pressure_values=q.pressure[ind][np.isfinite(q.pressure[ind])].tolist(),horizon_values=horizon,horizon_candidates=horizon_candidates,
              first_timestamp=str(q.d.Datetime.iat[int(ind[0])]),last_timestamp=str(q.d.Datetime.iat[int(ind[-1])]),
              SHALLOW_PULLBACK_signals=int(np.count_nonzero(q.d.SHALLOW_PULLBACK.iloc[ind])),
              OBV_PRESSURE_signals=int(np.count_nonzero(q.d.OBV_PRESSURE.iloc[ind])),
              INSIDE_DAY_RELEASE_signals=int(np.count_nonzero(q.d.INSIDE_DAY_RELEASE.iloc[ind])))
            market.append(rec)
    output=[];df=pd.DataFrame(market)
    for (period,family,year),z in df.groupby(['period','instrument','year'],sort=False):
        a=np.asarray(sum(z.ATR_values.tolist(),[]));vol=np.asarray(sum(z.volume_values.tolist(),[]))
        rv=np.asarray(sum(z.relative_volume_values.tolist(),[]));pressure=np.asarray(sum(z.pressure_values.tolist(),[]));h=np.asarray(sum(z.horizon_values.tolist(),[]))
        rec=dict(record_type='MARKET_YEAR',period=period,strategy='ALL',instrument=family,year=year,status='VERIFIED_ORIGINAL_QUOTES_SELECTED_V1',
          bars=int(z.bars.sum()),warmed_bars=int(z.warmed_bars.sum()),first_timestamp=z.first_timestamp.min(),last_timestamp=z.last_timestamp.max(),
          ATR14_price_pct_p10=float(np.quantile(a,.1)),ATR14_price_pct_p25=float(np.quantile(a,.25)),ATR14_price_pct_median=float(np.median(a)),ATR14_price_pct_p75=float(np.quantile(a,.75)),ATR14_price_pct_p90=float(np.quantile(a,.9)),
          volume_median=float(np.median(vol)),volume_p90=float(np.quantile(vol,.9)),volume_zero_fraction=float((vol==0).mean()),
          relative_volume_median=float(np.median(rv)),relative_volume_p90=float(np.quantile(rv,.9)),pressure_abs_gt035_fraction=float((abs(pressure)>.35).mean()),
          horizon_candidates=int(z.horizon_candidates.sum()),horizon_pairs=len(h),horizon_absolute_displacement_gt_1R_fraction=float((abs(h)>1).mean()) if len(h) else np.nan,
          horizon_absolute_displacement_le_1R_fraction=float((abs(h)<=1).mean()) if len(h) else np.nan)
        for m in MODES:rec[m+'_signals']=int(z[m+'_signals'].sum())
        output.append(rec)
    return output

def roll_market_rows(context):
    rows=[]
    for (period,contract),q in context.items():
        if period!='2018-2022':continue
        for year in np.unique(q.y):
            if year<2018:continue
            for bucket in np.unique(q.roll):
                mask=q.selected&(q.y==year)&(q.roll==bucket)
                if not mask.any():continue
                r=dict(period=period,instrument=q.family,year=int(year),roll_bucket=bucket,bars=int(mask.sum()),warmup_bars=int(q.d.ema200[mask].isna().sum()))
                for mode in MODES:r[mode+'_signals']=int(np.count_nonzero(q.d.loc[mask,mode]))
                rows.append(r)
    result=pd.DataFrame(rows).groupby(['period','instrument','year','roll_bucket'],as_index=False).sum()
    result['record_type']='ROLL_WINDOW_YEAR';result['status']='DESCRIPTIVE_NO_RULE_CHANGE';result['strategy']='ALL'
    return result.to_dict('records')

def expanded_groups(df):
    for period,p in df.groupby('period',sort=False):
        for mode,q in [(ALL,p),*list(p.groupby('strategy',sort=False))]:
            for family,z in [('ALL',q),*list(q.groupby('instrument',sort=False))]:
                for year,v in [('ALL',z),*list(z.groupby('year',sort=False))]:
                    yield dict(period=period,strategy=mode,instrument=family,year=year),v

def path_aggregates(actual,raw):
    output=[]
    actual=actual[actual.stat_eligible].copy();actual['year']=pd.to_datetime(actual.exit_dt).dt.year
    for base,q in expanded_groups(actual):
        z=q[q.actual_path_status.eq('OBSERVED_V1')];loss=z[z.loss]
        h=q[q.horizon_status.eq('OBSERVED_V1')]
        stop=h[h.exit_reason.isin([1,2,4])]
        output.append(dict(record_type='EXECUTED_TRADE_PATH_LOWER_BOUND',**base,status='VERIFIED_ORIGINAL_QUOTES_WITH_DENOMINATORS',
          observations=len(q),actual_observed_paths=len(z),actual_paths_with_unknown_gaps=len(q)-len(z),losses=int(q.loss.sum()),losses_with_observed_path=len(loss),
          definite_favorable_then_loss=int(z.definite_favorable_then_loss.sum()),
          definite_favorable_then_loss_fraction_of_losses=z.definite_favorable_then_loss.sum()/len(loss) if len(loss) else np.nan,
          definite_1R_then_loss=int(z.definite_1R_then_loss.sum()),definite_1R_then_loss_fraction_of_losses=z.definite_1R_then_loss.sum()/len(loss) if len(loss) else np.nan,
          definite_MFE_R_mean=z.definite_MFE_before_exit_R.mean(),
          horizon_observed_paths=len(h),horizon_unverified_paths=len(q)-len(h),mean_horizon_R=h.horizon_R.mean(),
          median_horizon_R=h.horizon_R.median(),positive_horizon_fraction=h.horizon_R.gt(0).mean(),
          MFE_R_mean=h.horizon_MFE_R.mean(),MFE_R_median=h.horizon_MFE_R.median(),MAE_R_mean=h.horizon_MAE_R.mean(),
          stop_touch_fraction=h.horizon_stop_touch.astype(float).mean(),stopped_with_observed_horizon=len(stop),
          stopped_then_positive_horizon=int(stop.horizon_R.gt(0).sum()),
          stopped_then_positive_horizon_fraction=stop.horizon_R.gt(0).mean()))
    for base,q in expanded_groups(raw):
        h=q[q.horizon_status.eq('OBSERVED_V1')]
        output.append(dict(record_type='RAW_FROZEN_SIGNALS',**base,status='VERIFIED_SELECTED_FROZEN_SIGNALS_WITH_OBSERVABILITY',
          observations=len(q),horizon_observed_paths=len(h),horizon_unverified_paths=len(q)-len(h),
          mean_horizon_R=h.horizon_R.mean(),median_horizon_R=h.horizon_R.median(),positive_horizon_fraction=h.horizon_R.gt(0).mean(),
          horizon_above_1R_fraction=h.horizon_R.gt(1).mean(),MFE_R_mean=h.horizon_MFE_R.mean(),MFE_R_median=h.horizon_MFE_R.median(),
          MAE_R_mean=h.horizon_MAE_R.mean(),stop_touch_fraction=h.horizon_stop_touch.astype(float).mean(),
          signal_relative_volume_median=q.signal_relative_volume.median(),signal_relative_volume_p90=q.signal_relative_volume.quantile(.9)))
    return output

def admission_aggregates(raw):
    out=[]
    for base,q in expanded_groups(raw):
        cap=q[q.admission.eq('ACCOUNT_TWO_ENTRY_CAP')];removed=cap[cap.removed_instruments_direct_cap_block]
        r=dict(record_type='SIGNAL_ADMISSION_YEAR',**base,status='REALIZED_HISTORY_GATE_DIAGNOSTIC_NOT_COUNTERFACTUAL_REPLAY',raw_signals=len(q),
          quota_blocked_candidate_signals=len(cap),quota_blocked_family_sessions=len(cap[['strategy','instrument','entry_session']].drop_duplicates()),
          removed_instruments_direct_cap_block_signals=len(removed),removed_instruments_direct_cap_block_family_sessions=len(removed[['strategy','instrument','entry_session']].drop_duplicates()))
        for reason,count in q.admission.value_counts().items():r['admission_'+reason]=int(count)
        out.append(r)
    return out

def pnl(q):
    r=q.net_C1_R;win=r[r>0].sum();loss=-r[r<0].sum()
    return dict(trades=len(q),PF_C1=float(win/loss) if loss else None,net_R=float(r.sum()),expectancy=float(r.mean()) if len(q) else None)

def cache_signature():
    names={'QuoteFrame','frame_context','existing_trades','verify_and_measure_trade','admission_index','raw_signal_rows','quote_market_rows','roll_market_rows'}
    tree=ast.parse(Path(__file__).read_text())
    text=''.join(ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in names)
    return hashlib.sha256(text.encode()).hexdigest()

def verify_feature_summaries(frames):
    computed={}
    for contract,d in frames.items():
        for day,q in d.groupby('day',sort=False):
            computed[(contract,str(pd.Timestamp(day).date()))]=[len(q),int(q.ema200.isna().sum()),q.segment.nunique(),*[int(q[m].ne(0).sum()) for m in MODES]]
    stored=pd.read_csv(STAGE/'results/SIGNAL_AND_COVERAGE_AUDIT.csv')
    assert len(computed)==len(stored)==2853
    for r in stored.itertuples():
        expected=[r.rows,r.warmup_bars,r.segments,*[getattr(r,m+'_signals') for m in MODES]]
        assert computed[(r.contract,r.day)]==expected,(r.contract,r.day,computed[(r.contract,r.day)],expected)

def measure(context,choices,work):
    trades=existing_trades()
    actual=pd.DataFrame([verify_and_measure_trade(r,context[(r.period,r.contract)]) for r in trades.itertuples(index=False)])
    raw=raw_signal_rows(context,choices,trades)
    market=pd.DataFrame(quote_market_rows(context));roll=pd.DataFrame(roll_market_rows(context))
    for name,data in [('trade',actual),('raw',raw),('market',market),('roll',roll)]:data.to_pickle(work/f'quote_{name}_records.pkl')
    files={f'quote_{name}_records.pkl':sha(work/f'quote_{name}_records.pkl') for name in ['trade','raw','market','roll']}
    (work/'quote_measurement_receipt.json').write_text(json.dumps(dict(signature=cache_signature(),files=files)))
    return actual,raw,market,roll

def modern_original_features(market,work,env):
    index=json.loads((STAGE/'publication/ARCHIVE_FILE_INDEX.json').read_text())
    hashes={r['path']:r['sha256'] for r in index['files']}
    destination=work/'modern_original_features';destination.mkdir(exist_ok=True)
    signature=''.join(sha(p) for p in [RUNNER,BASE/'base.py',BASE/'run.py',BASE/'legacy_v4/study_v4.py',BASE/'legacy_v4/dependencies/study.py'])
    frames={}
    for sym in TICKS:
        source=market/sym/(sym+'_M15.csv');h=sha(source);assert h==hashes['research_original_v20/marketdata_m15/'+source.name]
        cache=destination/(sym+'.pkl');receipt=destination/(sym+'.json');valid=False
        if cache.exists() and receipt.exists():
            r=json.loads(receipt.read_text());valid=r['source_sha256']==h and r['code_signature']==signature and r['cache_sha256']==sha(cache)
        if valid:d=pd.read_pickle(cache)
        else:
            d=env['frozen_signals'](pd.read_csv(source,sep=';',parse_dates=['Datetime']));d.to_pickle(cache)
            receipt.write_text(json.dumps(dict(source_sha256=h,code_signature=signature,cache_sha256=sha(cache))))
        frames[sym]=d
    return frames

def enrich(frames,sources,env,source,work,modern=None,reuse=False,market=None):
    work=work.resolve()
    verify_feature_summaries(frames)
    if reuse:
        receipt=json.loads((work/'quote_measurement_receipt.json').read_text())
        assert receipt['signature']==cache_signature()
        for name,h in receipt['files'].items():assert sha(work/name)==h
        actual,raw,market,roll=[pd.read_pickle(work/f'quote_{n}_records.pkl') for n in ['trade','raw','market','roll']]
    else:
        if modern is None:modern=modern_original_features(market or Path('/workspace/market-pattern-data/forever'),work,env)
        context,choices=frame_context(frames,modern,env)
        actual,raw,market,roll=measure(context,choices,work)
    assert len(actual)==2605
    distribution=pd.read_csv(OUT/'TRADE_DISTRIBUTION.csv')
    distribution=distribution[distribution.record_type.eq('EXIT_DISTRIBUTION')]
    summaries=path_aggregates(actual,raw)
    sensitivities=[]
    for period,p in actual[actual.stat_eligible].groupby('period'):
        for mode,q in [(ALL,p),*list(p.groupby('strategy'))]:
            free=q[q.actual_path_status.eq('OBSERVED_V1')]
            sensitivities.append(dict(record_type='OBSERVABILITY_SENSITIVITY',period=period,strategy=mode,instrument='ALL',
              year='ALL',status='EXISTING_TRADES_ONLY_NO_SIGNAL_RESET_OR_REPLAY',flagged_existing_trades=len(q)-len(free),
              primary_PF_C1=pnl(q)['PF_C1'],primary_net_R=pnl(q)['net_R'],**pnl(free)))
    roll_trades=[]
    old=actual[actual.period.eq('2018-2022')&actual.stat_eligible]
    for (mode,family,bucket),q in old.groupby(['strategy','instrument','roll_bucket']):
        roll_trades.append(dict(record_type='ROLL_TRADE_WINDOW',period='2018-2022',strategy=mode,instrument=family,roll_bucket=bucket,**pnl(q)))
    save(distribution.to_dict('records')+summaries+sensitivities+roll_trades,'TRADE_DISTRIBUTION.csv')
    ins=pd.read_csv(OUT/'INSTRUMENT_COMPARISON.csv')
    ins=ins[~ins.record_type.isin(['MARKET_YEAR','ROLL_WINDOW_YEAR','SIGNAL_ADMISSION_YEAR'])]
    admission=admission_aggregates(raw)
    save(ins.to_dict('records')+market.to_dict('records')+roll.to_dict('records')+admission,'INSTRUMENT_COMPARISON.csv')
    save(pd.concat([actual,raw],ignore_index=True).to_dict('records'),'QUOTE_PATH_DIAGNOSTICS.csv')
    verification=json.loads((OUT/'VERIFICATION.json').read_text())
    verification['quote_update_input_PR_sha']='9beb954201ba2ee18d8c89d82b551be8b5e745c3'
    verification['quarterly_source_zip']=dict(path=str(source.resolve()),sha256=sha(source),bytes=source.stat().st_size,expected_sha256=EXPECTED_ZIP,status='PASS')
    verification['quarterly_quotes_available']=True
    verification['source_files']=[r for r in verification['source_files'] if r.get('role')!='UPLOADED_ORIGINAL_QUARTERLY_M15']+sources
    for r in verification['checks']:
        if r['check']=='OLD_M15_SOURCE_AVAILABLE':r.update(status='PASS',detail='Uploaded original ZIP and all 43 CSV hashes match prior V20-03 source metadata; 149028 bars')
        if r['check']=='OLD_INTRABAR_EXECUTION':r.update(status='PASS',detail='All 1016 observed old model exits match first frozen trigger in original quotes; true execution inside 12 gaps remains unknown')
        if r['check']=='SUPPRESSION_COUNTERFACTUAL':r.update(detail='Direct two-entry-cap refusals counted on unchanged realized history; independent two-instrument PnL remains NOT VERIFIED')
    new_checks=[
      dict(check='QUARTERLY_ZIP_SHA256',status='PASS',detail=EXPECTED_ZIP),
      dict(check='ALL_43_QUARTERLY_SOURCE_HASHES',status='PASS',detail='Each CSV byte hash matches RUN_METADATA; safe extraction outside Git'),
      dict(check='QUARTERLY_INPUT_FORMAT_AND_GAP_PARITY',status='PASS',detail='149028 bars, OHLC/volume/grid/order; exact 409 gap records match publication'),
      dict(check='QUOTE_FEATURE_SUMMARY_PARITY',status='PASS',detail='Recalculated exact frozen features match all 2853 contract/session signal and warmup summaries'),
      dict(check='ALL_CLOSED_TRADES_QUOTE_EXECUTION',status='PASS',detail='2605 observed model trades: 1016 old including 12 censored + 1589 late; signal/entry/stop/first exit checked; no quarterly portfolio replay'),
      dict(check='RAW_SIGNAL_ADMISSION_RECONCILIATION',status='PASS',detail='Executed raw signal gates reproduce 1016 old entries and 1590 late entries including one open'),
      dict(check='MATCHED_PATH_OBSERVABILITY',status='PASS',detail='Same locked V1 gap recognition applied to path diagnostics in both periods; original PnL and modern feature continuity unchanged')]
    verification['checks']=[r for r in verification['checks'] if r['check'] not in {r['check'] for r in new_checks}]+new_checks
    verification['quote_update']=dict(source_bars=149028,quarterly_source_files=43,quarterly_portfolio_replays=0,
      strategy_parameter_changes=0,roll_policy_changes=0,new_C2_STRICT_runs=0,optimization_runs=0,walk_forward_runs=0,
      trade_quote_rows=len(actual),raw_selected_signal_rows=len(raw),diagnostic_output_sha256=sha(OUT/'QUOTE_PATH_DIAGNOSTICS.csv'),
      path_status_counts=[dict(period=p,status=s,count=len(q)) for (p,s),q in actual.groupby(['period','actual_path_status'])],
      horizon_status_counts=[dict(period=p,status=s,count=len(q)) for (p,s),q in actual.groupby(['period','horizon_status'])],
      observability_sensitivity=sensitivities,
      admission_summary=[r for r in admission if r['instrument']=='ALL' and r['year']=='ALL'],
      source_feature_cache_policy='Only locally generated caches; per-CSV hash plus immutable source-code signature and cache SHA256 validated')
    verification['path_method']='Both periods: original NEXT_OPEN, initial executable stop risk, first Open of third observed family session in same contract. Unknown V1 gaps/contract-session skips censor path summaries only. Favorable-before-loss lower bound excludes exit-candle High/Low. Post-stop horizon is descriptive price potential, not PnL of another exit policy.'
    verification['artifact_hashes']={p.name:sha(p) for p in OUT.iterdir() if p.suffix in ['.csv','.py','.md']}
    (OUT/'VERIFICATION.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(status='PARTIAL',quote_trades=len(actual),raw_signals=len(raw),checks={s:sum(r['status']==s for r in verification['checks']) for s in ['PASS','FAIL','NOT VERIFIED']})),flush=True)

def prepare_modern_v1(market,work,env):
    """Exactly the existing V1 segmentation/seed applied to the late inputs.

    This is a diagnostic of the known pipeline asymmetry, not a new data filter
    chosen by PnL. Modern tick sizes stay the original frozen perpetual sizes.
    """
    index=json.loads((STAGE/'publication/ARCHIVE_FILE_INDEX.json').read_text())
    hashes={r['path']:r['sha256'] for r in index['files']}
    destination=work/'modern_v1_features';destination.mkdir(exist_ok=True)
    source_signature=''.join(sha(p) for p in [RUNNER,BASE/'base.py',BASE/'run.py',BASE/'legacy_v4/study_v4.py',BASE/'legacy_v4/dependencies/study.py'])
    frames={};input_hashes={}
    for sym in TICKS:
        source=market/sym/(sym+'_M15.csv');h=sha(source);assert h==hashes['research_original_v20/marketdata_m15/'+source.name]
        input_hashes[str(source)]=h
        cache=destination/(sym+'.pkl');receipt=destination/(sym+'.json')
        valid=False
        if cache.exists() and receipt.exists():
            r=json.loads(receipt.read_text());valid=r['source_sha256']==h and r['frozen_code_signature']==source_signature and r['cache_sha256']==sha(cache)
        if valid:d=pd.read_pickle(cache)
        else:
            raw=pd.read_csv(source,sep=';',parse_dates=['Datetime']);seg=np.zeros(len(raw),dtype=int)
            for j in range(1,len(raw)):seg[j]=seg[j-1]+int(env['broken'](raw.Datetime.iat[j-1],raw.Datetime.iat[j]))
            raw['segment']=seg;parts=[]
            for n,q in raw.groupby('segment',sort=False):
                d=env['frozen_signals'](q);d['segment']=int(n);parts.append(d)
            d=pd.concat(parts,ignore_index=True);d['tick']=TICKS[sym]
            d.to_pickle(cache);receipt.write_text(json.dumps(dict(source_sha256=h,frozen_code_signature=source_signature,cache_sha256=sha(cache))))
        frames[sym]=d
        print('late V1 features',sym,len(d),'segments',d.segment.nunique(),flush=True)
    return frames,input_hashes

def run_modern_v1(frames):
    runner=ROOT/'V20-02_AUDIT/replay_independent.py'
    env=dict(np=np,pd=pd,math=math,defaultdict=defaultdict,SYMS=lit(BASE/'base.py','SYMS'),TICKS=TICKS,COLS=lit(runner,'COLS'))
    one=fn(runner,'run_one',env);result=[];meta={}
    for n,(name,mode) in enumerate(lit(runner,'ACCOUNTS'),1):
        t,m=one(frames,n,name,mode);meta[mode]=m;t['strategy']=mode;t['record_type']='GAP_V1_DIAGNOSTIC_TRADE'
        t=t.rename(columns={'net_R':'net_C1_R'});t['period']='2023-2026';t['instrument']=t.symbol;t['contract']=t.symbol
        eligibility=[]
        for r in t.itertuples():
            d=frames[r.symbol].set_index('Datetime');en=pd.Timestamp(r.entry_dt);ex=pd.Timestamp(r.exit_dt)
            eligibility.append(int(d.at[en,'segment'])==int(d.at[ex,'segment']))
        t['stat_eligible']=eligibility;result.append(t)
        print('late V1 replay',mode,'closed',len(t),'eligible',sum(eligibility),'open',m['unclosed'],flush=True)
    return pd.concat(result,ignore_index=True),meta

def gap_v1_sensitivity(market,work,env):
    frames,input_hashes=prepare_modern_v1(market,work,env)
    tree=ast.parse(Path(__file__).read_text());names={'prepare_modern_v1','run_modern_v1'}
    signature=hashlib.sha256((''.join(ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names)+sha(ROOT/'V20-02_AUDIT/replay_independent.py')+json.dumps(input_hashes,sort_keys=True)).encode()).hexdigest()
    cache=work/'modern_v1_trade_results.pkl';receipt=work/'modern_v1_trade_receipt.json'
    if cache.exists() and receipt.exists():
        r=json.loads(receipt.read_text());assert r['signature']==signature and r['cache_sha256']==sha(cache)
        trades=pd.read_pickle(cache);meta=r['meta']
    else:
        trades,meta=run_modern_v1(frames);trades.to_pickle(cache)
        receipt.write_text(json.dumps(dict(signature=signature,cache_sha256=sha(cache),meta=meta)))
    contexts={s:QuoteFrame(d,s,s,'2023-2026',np.unique(d.day.to_numpy('datetime64[ns]').astype('int64')),env,{}, {}) for s,d in frames.items()}
    checked=trades.copy();checked['account']=checked.strategy;checked['family']=checked.symbol
    checked['signal_bar_dt']=pd.to_datetime(checked.signal_dt)-pd.Timedelta(minutes=15)
    for r in checked.itertuples(index=False):
        measurement=verify_and_measure_trade(r,contexts[r.symbol])
        assert bool(r.stat_eligible)==(measurement['actual_path_status']=='OBSERVED_V1')
        assert math.isclose(r.net_C1_R,r.side*(r.exit-r.entry)/r.risk-2*TICKS[r.symbol]/r.risk,abs_tol=1e-8)
    out=[];valid=trades[trades.stat_eligible].copy();valid['year']=pd.to_datetime(valid.exit_dt).dt.year
    for mode,q in [(ALL,valid),*list(valid.groupby('strategy'))]:
        for family,f in [('ALL',q),('TWO_FILTERED_EXECUTED',q[q.instrument.isin(['USDRUBF','IMOEXF'])]),*list(q.groupby('instrument'))]:
            for year,z in [('ALL',f),*list(f.groupby('year'))]:
                r=pnl(z);r['record_type']='GAP_V1_REPLAY_SENSITIVITY';r.update(period='2023-2026',strategy=mode,instrument=family,year=year,
                  status='ONE_LOCKED_V1_PIPELINE_DIAGNOSTIC_NOT_NEW_STRATEGY')
                a=z.sort_values(['exit_dt','entry_dt','account_num','contract']).net_C1_R.to_numpy(float);c=np.r_[0,np.cumsum(a)]
                r['max_DD_closed_R']=float((np.maximum.accumulate(c)-c).max());out.append(r)
    distribution=pd.read_csv(OUT/'TRADE_DISTRIBUTION.csv');distribution=distribution[~distribution.record_type.eq('GAP_V1_REPLAY_SENSITIVITY')]
    save(distribution.to_dict('records')+out,'TRADE_DISTRIBUTION.csv')
    paths=pd.read_csv(OUT/'QUOTE_PATH_DIAGNOSTICS.csv');paths=paths[~paths.record_type.eq('GAP_V1_DIAGNOSTIC_TRADE')]
    save(pd.concat([paths,trades],ignore_index=True).to_dict('records'),'QUOTE_PATH_DIAGNOSTICS.csv')
    coverage=[]
    for sym,d in frames.items():
        for year,z in [('ALL',d),*list(d.groupby(d.Datetime.dt.year))]:
            r=dict(record_type='GAP_V1_COVERAGE_YEAR',period='2023-2026',strategy='ALL',instrument=sym,year=year,
              bars=len(z),warmup_bars=int(z.ema200.isna().sum()),status='LOCKED_V1_DIAGNOSTIC_SAME_QUOTES')
            for mode in MODES:r[mode+'_signals']=int(z[mode].ne(0).sum())
            coverage.append(r)
    ins=pd.read_csv(OUT/'INSTRUMENT_COMPARISON.csv');ins=ins[~ins.record_type.eq('GAP_V1_COVERAGE_YEAR')]
    save(ins.to_dict('records')+coverage,'INSTRUMENT_COMPARISON.csv')
    path=OUT/'VERIFICATION.json';v=json.loads(path.read_text());v['new_replay_batches']=2;v['strategy_replays']=6
    v['replay_scope']='Previous missing-ledger baseline reproduction plus one late locked-V1 gap/reset diagnostic; no quarterly portfolio replay, parameter changes, optimization, WF or causality rerun'
    v['quote_update']['late_V1_diagnostic_replay_batches']=1;v['quote_update']['late_V1_diagnostic_strategy_replays']=3
    v['quote_update']['late_V1_diagnostic_reason']='86 original late trades cross gaps under locked historical V1; a mere closed-row filter cannot measure indicator warmup/reset selection. Exactly one existing V1 pipeline is applied to the same late quotes; no thresholds/rules are selected by results.'
    v['quote_update']['late_V1_replay_meta']=meta
    v['quote_update']['late_V1_quote_checked_closed_rows']=len(checked)
    for r in v['checks']:
        if r['check']=='ALL_CLOSED_TRADES_QUOTE_EXECUTION':r['detail']='2605 baseline observed model trades (1016 old +1589 late), plus1251 late V1 model trades: signal/entry/stop/first exit checked; true gap execution unknown'
    v['quote_update']['late_V1_replay_input_hashes']=input_hashes
    v['quote_update']['late_V1_gap_intervals_by_symbol']={s:int(d.segment.nunique()-1) for s,d in frames.items()}
    v['quote_update']['late_V1_warmup_coverage']=coverage
    v['quote_update']['late_V1_replay_summaries']=[r for r in out if r['instrument'] in ['ALL','TWO_FILTERED_EXECUTED'] and r['year']=='ALL']
    v['quote_update']['diagnostic_output_sha256']=sha(OUT/'QUOTE_PATH_DIAGNOSTICS.csv')
    v['checks']=[r for r in v['checks'] if r['check']!='LATE_EXISTING_V1_PIPELINE_DIAGNOSTIC']+[dict(check='LATE_EXISTING_V1_PIPELINE_DIAGNOSTIC',status='PASS',detail='One required methodology diagnostic: exact original V1 feature resets/censoring on unchanged late quotes and frozen run_one; no optimization or quarterly portfolio replay')]
    v['artifact_hashes']={p.name:sha(p) for p in OUT.iterdir() if p.suffix in ['.csv','.py','.md']}
    path.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print('V1 DIAGNOSTIC',json.dumps(v['quote_update']['late_V1_replay_summaries']),flush=True)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--quarterly-zip',type=Path,required=True);ap.add_argument('--work',type=Path,required=True)
    ap.add_argument('--prepare-only',action='store_true');ap.add_argument('--reuse-measurements',action='store_true')
    ap.add_argument('--gap-v1',action='store_true');ap.add_argument('--market-data',type=Path,default=Path('/workspace/market-pattern-data/forever'));args=ap.parse_args()
    frames,sources,env=prepare_quarterly(args.quarterly_zip,args.work)
    print('QUARTERLY INPUT PASS',len(frames),'files',sum(map(len,frames.values())),'bars',flush=True)
    if not args.prepare_only:enrich(frames,sources,env,args.quarterly_zip,args.work,reuse=args.reuse_measurements,market=args.market_data)
    if args.gap_v1:gap_v1_sensitivity(args.market_data,args.work,env)

if __name__=='__main__':main()
