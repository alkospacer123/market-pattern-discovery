#!/usr/bin/env python3
"""Offline V20-03. Frozen signal bodies; one locked causal roll; no network/write to sources.
Python 3.11+, pandas 2.2.3, numpy 2.3.5. Outputs are conditional research in R.
"""
from __future__ import annotations
import argparse, ast, hashlib, json, math, sys, tempfile, warnings
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pandas as pd

warnings.filterwarnings('ignore', category=FutureWarning)
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT/'V20-03'
BASE = ROOT/'research_original_v20'
MODES = ['SHALLOW_PULLBACK', 'OBV_PRESSURE', 'INSIDE_DAY_RELEASE']
FAMILIES = ['CNY', 'MIX', 'Si']  # frozen symbol tie order, GLD absent
PROXY = {'CNY':'CNYRUBF', 'MIX':'IMOEXF', 'Si':'USDRUBF'}
RAWCOLS = ['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']
FEATURES = ['atr', 'ema50', 'ema200', *MODES]
LOCKED = {
 'base.py':'b7b9df00f8d7fb0a88c5cba103034e5a2335c108ae283258e5d8ebd5476aa59d',
 'run.py':'223545374f98d8c87cf2c09b3a7302b05b07020dc8bf34b5984ebaa3d74389fe',
 'legacy_v4/study_v4.py':'0f49432e207235f631807a82536f521751ad5559cc374fc6c42f8ca4f289bd08'}

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def extract(path, name, globals_):
    """Compile the EXACT frozen AST function; omit top-level legacy side effects.
    No formula transcription, source rewriting, imports, replay or main execution.
    """
    tree = ast.parse(path.read_text())
    node = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == name)
    ns = dict(globals_, __builtins__=__builtins__)
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), 'exec'), ns)
    return ns[name]

def literal(path, name):
    tree = ast.parse(path.read_text())
    return ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign)
                              and any(isinstance(t,ast.Name) and t.id==name for t in n.targets)))

def frozen_signals(raw):
    # A disposable file is the adapter required by frozen file-reading functions.
    # Source data and frozen code are never written to. No modern market data read here.
    with tempfile.TemporaryDirectory(prefix='v20_signal_', dir=ROOT.parent) as t:
        p = Path(t); (p/'marketdata_m15').mkdir()
        raw[RAWCOLS].to_csv(p/'marketdata_m15'/'INPUT_M15.csv',sep=';',index=False)
        common = dict(np=np,pd=pd)
        prepare = extract(BASE/'base.py','prepare',dict(common,ROOT=p,MODES=literal(BASE/'base.py','MODES')))
        sig = extract(BASE/'run.py','sig',common)
        signals = extract(BASE/'run.py','signals',dict(common,b=SimpleNamespace(prepare=prepare),
                                                     M=literal(BASE/'run.py','M'),sig=sig))
        d = signals('INPUT')
        prep = extract(BASE/'legacy_v4/dependencies/study.py','prep',dict(common,ROOT=p/'marketdata_m15'))
        legacy = extract(BASE/'legacy_v4/study_v4.py','add_indicators',
                         dict(common,MODES=literal(BASE/'legacy_v4/study_v4.py','MODES')))
        inside = legacy(prep('INPUT'),'INPUT')
        for x in ['Datetime','day']:
            assert d[x].equals(inside[x]), x
        for x in ['atr','ema50','ema200']:
            assert np.allclose(d[x],inside[x],rtol=1e-12,atol=1e-12,equal_nan=True), x
        d['INSIDE_DAY_RELEASE'] = inside['INSIDE_DAY_RELEASE'].to_numpy()
        return d[RAWCOLS+['day','mins',*FEATURES]]

def session(ts):
    return (pd.Timestamp(ts)-pd.Timedelta(hours=9)).normalize()

def tick(family, ts):
    if family=='Si':return 1.0
    if family=='MIX':return 25.0
    return .01 if pd.Timestamp(ts)<pd.Timestamp('2022-10-06 19:00') else .001

def maturity(contract):
    suffix=contract.split('-')[1]; m,y=map(int,suffix.split('.'))
    first=pd.Timestamp(2000+y,m,1)
    return first+pd.Timedelta(days=(3-first.weekday())%7+14)

def cutoff(contract):
    exp=maturity(contract)
    return exp-pd.Timedelta(days=exp.weekday())

def broken(prev, now):
    """Unknown same-date/session M15 hole; observed only when next bar arrives."""
    prev,now=pd.Timestamp(prev),pd.Timestamp(now)
    if now-prev<=pd.Timedelta(minutes=15):return False
    if prev.date()!=now.date() or session(prev)!=session(now):return False
    pair=(prev.strftime('%H:%M'),now.strftime('%H:%M'))
    return pair not in {('18:30','19:00'),('18:30','19:15'),('13:45','14:15')}

def read_inputs():
    ds={};maps=[];gap_rows=[];sessions=[]
    for family in FAMILIES:
        for p in sorted((ROOT/'history_2018_2022_original'/family.lower()).glob('*.csv')):
            contract=p.stem.removesuffix('_M15')
            d=pd.read_csv(p,sep=';',parse_dates=['Datetime'])
            assert d.Datetime.is_monotonic_increasing and not d.Datetime.duplicated().any(), p
            values=d[['Open','High','Low','Close','Volume']].to_numpy(float)
            assert np.isfinite(values).all() and (d.Volume>0).all(),p
            assert ((d.High>=d[['Open','Low','Close']].max(axis=1)) &
                    (d.Low<=d[['Open','High','Close']].min(axis=1))).all(),p
            assert (d.Datetime.dt.minute%15==0).all() and (d.Datetime.dt.second==0).all(),p
            ticks=np.array([tick(family,t) for t in d.Datetime])
            prices=d[['Open','High','Low','Close']].to_numpy(float)
            error=np.abs(prices/ticks[:,None]-np.round(prices/ticks[:,None]))
            assert (error<1e-6).all(),('TICK_GRID_FAIL',p)
            d['contract']=contract;d['family']=family
            d['day']=(d.Datetime-pd.Timedelta(hours=9)).dt.normalize()
            seg=[];counter=0;prev=None
            for t in d.Datetime:
                if prev is not None and broken(prev,t):
                    counter+=1
                    gap_rows.append(dict(family=family,contract=contract,previous_bar=prev,next_bar=t,
                                         reason='UNKNOWN_M15_HOLE_RESET_AT_NEXT_OBSERVATION'))
                seg.append(counter);prev=t
            d['segment']=seg;ds[contract]=d
            for day,q in d.groupby('day',sort=True):
                mins=q.Datetime.dt.hour*60+q.Datetime.dt.minute
                dayq=q[mins.between(600,1065)]
                valid=(len(dayq)>=12 and dayq.Datetime.iloc[0].time()<=pd.Timestamp('10:15').time()
                       and dayq.Datetime.iloc[-1].time()>=pd.Timestamp('17:15').time())
                sessions.append(dict(family=family,contract=contract,day=day,rows=len(q),
                                     first_bar=q.Datetime.min(),last_bar=q.Datetime.max(),day_rows=len(dayq),
                                     prior_day_eligible=valid,known_after=q.Datetime.max()+pd.Timedelta(minutes=15)))
            mins=d.Datetime.dt.hour*60+d.Datetime.dt.minute
            identity='FAMILY_CONFIRMED_FILE_LABEL_CONDITIONAL'
            maps.append(dict(family=family,file=p.relative_to(ROOT/'history_2018_2022_original').as_posix(),
              contract=contract,contract_suffix=contract.split('-')[1],
              expected_short_code={'Si':'Si','MIX':'MX','CNY':'CR'}[family]+{3:'H',6:'M',9:'U',12:'Z'}[maturity(contract).month]+str(maturity(contract).year)[-1],
              identity_status=identity,nominal_expiry=maturity(contract).date(),entry_cutoff=cutoff(contract).date(),
              expiry_status='THIRD_THURSDAY_RULE_CONDITIONAL_HISTORICAL_EXCEPTIONS_UNVERIFIED',
              first_timestamp=d.Datetime.min(),last_timestamp=d.Datetime.max(),rows=len(d),sha256=sha(p),
              price_unit={'Si':'RUB per 1000 USD','MIX':'100 x MOEX index points','CNY':'RUB per CNY'}[family],
              proxy=PROXY[family],proxy_scale={'Si':.001,'MIX':.01,'CNY':1}[family],
              proxy_status='ECONOMIC_PROXY_NOT_IDENTICAL_CONTRACT',
              tick_schedule='1' if family=='Si' else '25' if family=='MIX' else '0.01 before 2022-10-06 19:00; 0.001 from then',
              tick_value_RUB='1' if family=='Si' else '25' if family=='MIX' else '10 before 2022-10-06 19:00; 1 from then',
              evidence='S1/S2 + all OHLC' if family=='Si' else 'S2/S3 + all OHLC (2018-2021 changes conditional)' if family=='MIX' else 'S4/S5 + all OHLC',
              grid_failures=int((error>=1e-6).sum()),min_observed_time=d.Datetime.dt.strftime('%H:%M').min(),
              max_observed_time=d.Datetime.dt.strftime('%H:%M').max(),bars_before_09=int((mins<540).sum()),
              timestamp_status='NAIVE_CSV_START_AND_MSK_ASSUMED_NOT_VENDOR_VERIFIED',unknown_holes=counter))
    assert len(ds)==43
    return ds,pd.DataFrame(maps),pd.DataFrame(sessions),pd.DataFrame(gap_rows)

def prepare_contract(raw):
    parts=[]
    for seg,q in raw.groupby('segment',sort=False):
        d=frozen_signals(q)
        d['segment']=seg
        d['segment_bars']=np.arange(1,len(d)+1)
        parts.append(d)
    d=pd.concat(parts,ignore_index=True)
    d['contract']=raw.contract.iloc[0];d['family']=raw.family.iloc[0]
    d['tick']=[tick(d.family.iloc[0],t) for t in d.Datetime]
    return d

def roll_plan(sessions):
    """Decisions use ONLY completed prior-session summaries, independent of signals."""
    rows=[]
    for family in FAMILIES:
        s=sessions[sessions.family==family]
        days=sorted(s.day.unique());previous=None;floor=pd.Timestamp.min
        for day0 in days:
            day=pd.Timestamp(day0);decision=day+pd.Timedelta(hours=9)
            hist=s[(s.day==previous)&(s.known_after<=decision)&s.prior_day_eligible] if previous is not None else s.iloc[:0]
            candidates=[c for c in hist.contract if maturity(c)>=floor and day<cutoff(c)]
            candidates=sorted(set(candidates),key=lambda c:(maturity(c),c))
            pick=candidates[0] if candidates else ''
            if pick:floor=maturity(pick)
            proof=hist[hist.contract==pick]
            known=proof.known_after.max() if len(proof) else pd.NaT
            assert pd.isna(known) or known<=decision
            rows.append(dict(family=family,day=day,decision_time=decision,previous_observed_session=previous,
                             chosen_contract=pick,proof_known_after=known,
                             candidate_count=len(candidates),reason='NEAREST_ALREADY_OBSERVED' if pick else 'NO_ELIGIBLE_PAST_CONTRACT'))
            previous=day0
    return pd.DataFrame(rows)

def replay(frames, plan, mode, account_num):
    stacks=[]
    for c,d0 in frames.items():
        if d0.empty:continue
        d=d0.copy();d['order']=FAMILIES.index(d.family.iloc[0]);d['expiry']=maturity(c)
        stacks.append(d)
    if not stacks:return [],[],[],[]
    z=pd.concat(stacks,ignore_index=True).sort_values(['Datetime','order','expiry','contract'],kind='stable')
    # Prefixes / future suffix deletion must preserve historical decisions and exits.
    choices={(r.family,pd.Timestamp(r.day)):r.chosen_contract for r in plan.itertuples()}
    dates={f:{pd.Timestamp(d):i for i,d in enumerate(sorted(z.loc[z.family==f,'day'].unique()))} for f in FAMILIES}
    state={f:None for f in FAMILIES};pending={f:None for f in FAMILIES};used={f:None for f in FAMILIES}
    current_day=None;entries_today=0;closed=[];entries=[];events=[]
    def finish(st,r,price,reason):
        gross=st['side']*(price-st['entry'])/st['risk']
        tx=tick(r.family,r.Datetime)
        cost=(st['tick_entry']+tx)/st['risk']
        span=dates[r.family][r.day]-st['entry_session_index']+1
        out=dict(st,exit_dt=str(r.Datetime),exit=price,exit_reason=reason,tick_exit=tx,
                 gross_R=gross,net_C1_R=gross-cost,net_C2_R=gross-2*cost,net_STRICT_R=gross-4*cost,
                 session_span=span,stat_eligible=not st['data_gap'],
                 status='CENSORED_DATA_GAP' if st['data_gap'] else 'CONDITIONAL_CLOSED',
                 exit_year=r.Datetime.year,exit_month=r.Datetime.strftime('%Y-%m'))
        closed.append(out)
    for r in z.itertuples(index=False):
        f=r.family;c=r.contract;t=r.Datetime;day=r.day
        if current_day!=day:current_day=day;entries_today=0
        ses=dates[f][day];chosen=choices.get((f,day),'')
        st=state[f]
        if st is not None and st['contract']==c:
            if st['last_segment']!=r.segment or ses-st['last_session_index']>1:st['data_gap']=True
            st['last_segment']=r.segment;st['last_session_index']=ses
            st['last_observed_bar']=str(t)
            direction=st['side'];sp=st['stop'];eps=r.tick*1e-7;x=None;reason=None
            if ses-st['entry_session_index']>=2:x=r.Open;reason=3
            elif (direction==1 and r.Open<=sp+eps) or (direction==-1 and r.Open>=sp-eps):x=r.Open;reason=2
            elif (direction==1 and r.Low<=sp+eps) or (direction==-1 and r.High>=sp-eps):x=sp;reason=1
            if reason is not None:finish(st,r,x,reason);state[f]=None
        pend=pending[f]
        # Pending belongs to exactly one contract and cannot be inherited at a roll.
        if pend is not None and (pend['contract']!=chosen or t>pend['entry_time']):
            events.append(dict(account=mode,family=f,at=t,reason='PENDING_EXPIRED_OR_ROLLED',contract=pend['contract']))
            pending[f]=None;pend=None
        if pend is not None and pend['contract']==c:
            if (t==pend['entry_time'] and c==chosen and state[f] is None and used[f]!=day
                    and entries_today<2 and pend['segment']==r.segment):
                direction=pend['side'];target=r.Open-direction*2*pend['atr']
                sp=(math.floor(target/r.tick+1e-9) if direction==1 else math.ceil(target/r.tick-1e-9))*r.tick
                risk=abs(r.Open-sp)
                if risk>0 and math.isfinite(risk):
                    st=dict(account=mode,account_num=account_num,family=f,proxy=PROXY[f],contract=c,
                      side=direction,signal_bar_dt=str(pend['bar_time']),signal_dt=str(pend['entry_time']),
                      entry_dt=str(t),entry_session=str(day.date()),entry_session_index=ses,entry=float(r.Open),
                      stop=sp,risk=risk,tick_entry=r.tick,atr_at_signal=pend['atr'],entry_segment=int(r.segment),
                      last_segment=int(r.segment),last_session_index=ses,last_observed_bar=str(t),data_gap=False)
                    assert t==pend['bar_time']+pd.Timedelta(minutes=15)
                    assert risk+1e-9>=2*pend['atr'] and abs(sp/r.tick-round(sp/r.tick))<1e-6
                    state[f]=st;used[f]=day;entries_today+=1
                    assert entries_today<=2
                    entries.append(dict(st,entries_account_session=entries_today,chosen_contract=chosen))
                    if (direction==1 and r.Low<=sp+r.tick*1e-7) or (direction==-1 and r.High>=sp-r.tick*1e-7):
                        finish(st,r,sp,4);state[f]=None
            pending[f]=None
        signal=int(getattr(r,mode))
        if (signal and 2018<=t.year<=2022 and c==chosen and state[f] is None and used[f]!=day and math.isfinite(r.atr) and r.atr>0):
            pending[f]=dict(contract=c,side=signal,bar_time=t,entry_time=t+pd.Timedelta(minutes=15),
                            atr=r.atr,segment=r.segment)
    opened=[dict(st,status='OPEN_UNKNOWN_RESULT_NO_SYNTHETIC_EXIT') for st in state.values() if st is not None]
    return closed,opened,entries,events

def metrics(q,col):
    q=q.sort_values(['exit_dt','entry_dt','account_num','contract'],kind='stable')
    a=q[col].to_numpy(float);pos=a[a>0].sum();neg=-a[a<0].sum()
    cum=np.r_[0,np.cumsum(a)];dd=(np.maximum.accumulate(cum)-cum).max()
    return dict(trades=len(q),PF=pos/neg if neg else np.nan,R=float(a.sum()) if len(q) else np.nan,
                gross_R=float(q.gross_R.sum()) if len(q) else np.nan,
                DD_closed_R=float(dd) if len(q) else np.nan,wins=int((a>0).sum()),
                PF_status='CONDITIONAL_AVAILABLE_PROXY_UNIVERSE' if len(q) else 'NO_CLOSED_TRADES_NO_PNL_ESTIMATE')

def statistics(closed,out):
    valid=closed[closed.stat_eligible].copy();stats=[];concentration=[]
    months=[str(x) for x in pd.period_range('2018-01','2022-12',freq='M')]
    for mode in MODES+['ALL_INDEPENDENT_ACCOUNTS']:
        t=valid if mode=='ALL_INDEPENDENT_ACCOUNTS' else valid[valid.account==mode]
        for scenario in ['C1','C2','STRICT']:
            col='net_'+scenario+'_R'
            for f in ['ALL',*FAMILIES]:
                ft=t if f=='ALL' else t[t.family==f]
                for kind,periods in [('ALL',['2018-2022']),('YEAR',[str(y) for y in range(2018,2023)]),('MONTH',months)]:
                    for period in periods:
                        q=ft if kind=='ALL' else ft[ft.exit_year==int(period)] if kind=='YEAR' else ft[ft.exit_month==period]
                        m=metrics(q,col);stats.append(dict(account=mode,scenario=scenario,family=f,kind=kind,period=period,**m))
                m=ft.groupby('exit_month')[col].sum().reindex(months,fill_value=0)
                positive=m[m>0].sort_values(ascending=False);net=float(m.sum());p=float(positive.sum())
                winner=ft[ft[col]>0][col].sort_values(ascending=False)
                concentration.append(dict(account=mode,scenario=scenario,family=f,
                  best_month=m.idxmax() if len(ft) else '',best_month_R=float(m.max()) if len(ft) else np.nan,
                  worst_month=m.idxmin() if len(ft) else '',worst_month_R=float(m.min()) if len(ft) else np.nan,
                  positive_months=len(positive),top1_positive_month_share=float(positive.head(1).sum()/p) if p else np.nan,
                  top3_positive_month_share=float(positive.head(3).sum()/p) if p else np.nan,
                  top3_month_R_over_net=float(positive.head(3).sum()/net) if net>0 else np.nan,
                  top10_winners_share=float(winner.head(10).sum()/winner.sum()) if len(winner) else np.nan))
    table=pd.DataFrame(stats)
    save(table,out/'STATISTICS.csv');save(pd.DataFrame(concentration),out/'CONCENTRATION.csv')
    best=table[(table.kind=='MONTH')&(table.trades>0)].sort_values(
        ['account','scenario','family','R','period'],ascending=[True,True,True,False,True],kind='stable')
    best=best.groupby(['account','scenario','family'],sort=False).head(10).copy()
    best['rank']=best.groupby(['account','scenario','family'],sort=False).cumcount()+1
    save(best,out/'BEST_MONTHS.csv')

def save(df,path):
    df.to_csv(path,index=False,float_format='%.12g',lineterminator='\n')

def verify_originals():
    import zipfile
    for rel,h in LOCKED.items():assert sha(BASE/rel)==h,rel
    assert sha(ROOT/'source_archive/2018-2022.zip')=='df1aaf4d23757d18689dfdf61d6fc1ec77f0b26ae7d8af1193322d460707888a'
    with zipfile.ZipFile(ROOT/'source_archive/2018-2022.zip') as z:
        for p in (ROOT/'history_2018_2022_original').glob('*/*.csv'):
            assert z.read(p.relative_to(ROOT/'history_2018_2022_original').as_posix())==p.read_bytes(),p
    # All received files except explicitly updated V20-03 deliverables stay byte-identical.
    changed={'V20-03/CONTRACT_MAP.csv','V20-03/ROLL_POLICY.md','V20-03/STRESS_REPORT_RU.md'}
    count=0
    for line in (STAGE/'original_received/MANIFEST_SHA256.received.txt').read_text().splitlines():
        h,rel=line.split(maxsplit=1)
        if rel not in changed:assert sha(ROOT/rel)==h,rel;count+=1
    return count

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=STAGE/'results');args=ap.parse_args()
    out=args.out.resolve()
    assert out!=ROOT and out!=BASE and BASE not in out.parents
    out.mkdir(parents=True,exist_ok=True)
    preserved=verify_originals()
    raw,maps,sessions,gaps=read_inputs();plan=roll_plan(sessions)
    frames={}
    for c,d in raw.items():
        frames[c]=prepare_contract(d)
        print('features',c,len(d),'segments',d.segment.nunique(),flush=True)
    closed=[];opened=[];entries=[];events=[]
    for n,mode in enumerate(MODES,1):
        cl,op,en,ev=replay(frames,plan,mode,n)
        closed+=cl;opened+=op;entries+=en;events+=ev
        print(mode,'closed observed',len(cl),'eligible',sum(x['stat_eligible'] for x in cl),'open',len(op),flush=True)
    alltr=pd.DataFrame(closed).sort_values(['exit_dt','entry_dt','account_num','contract'],kind='stable')
    ens=pd.DataFrame(entries).sort_values(['entry_dt','account_num','family'],kind='stable')
    assert ens.groupby(['account','entry_session']).size().max()<=2
    assert ens.groupby(['account','family','entry_session']).size().max()<=1
    assert ens.contract.eq(ens.chosen_contract).all()
    assert (pd.to_datetime(ens.signal_dt)==pd.to_datetime(ens.entry_dt)).all()
    assert (pd.to_datetime(ens.entry_dt)-pd.to_datetime(ens.signal_bar_dt)==pd.Timedelta(minutes=15)).all()
    save(maps,out/'CONTRACT_MAP.csv');save(sessions,out/'SESSION_AUDIT.csv');save(gaps,out/'INVALID_INTERVALS.csv')
    save(plan,out/'ROLL_DECISIONS.csv');save(alltr,out/'ALL_OBSERVED_CLOSED.csv')
    save(alltr[alltr.stat_eligible],out/'CLOSED_TRADES.csv');save(alltr[~alltr.stat_eligible],out/'CENSORED_CLOSED.csv')
    save(ens,out/'ENTRIES.csv');save(pd.DataFrame(opened),out/'OPEN_POSITIONS.csv')
    save(pd.DataFrame(events),out/'EXECUTION_EVENTS.csv')
    audit=[]
    for c,d in frames.items():
        for day,q in d.groupby('day',sort=True):
            chosen=plan[(plan.family==q.family.iloc[0])&(plan.day==day)].chosen_contract
            audit.append(dict(family=q.family.iloc[0],contract=c,day=day,rows=len(q),
              selected=bool(len(chosen) and chosen.iloc[0]==c),warmup_bars=int(q.ema200.isna().sum()),
              segments=q.segment.nunique(),**{x+'_signals':int(q[x].ne(0).sum()) for x in MODES}))
    audit=pd.DataFrame(audit)
    save(audit,out/'SIGNAL_AND_COVERAGE_AUDIT.csv')
    selected=audit[audit.selected].drop(columns=['selected']).rename(columns={'contract':'chosen_contract'})
    coverage=plan.merge(selected,on=['family','day','chosen_contract'],how='left',validate='one_to_one')
    coverage['observed_selected_rows']=coverage.rows.fillna(0).astype(int)
    coverage['coverage_status']=np.where(coverage.chosen_contract.eq(''),'NO_ELIGIBLE_PAST_CONTRACT',
        np.where(coverage.observed_selected_rows.eq(0),'CHOSEN_CONTRACT_NO_CURRENT_OBSERVATIONS',
                 'OBSERVED_CONDITIONAL_WITH_WARMUP_AND_GAP_RESETS'))
    save(coverage,out/'EFFECTIVE_COVERAGE.csv')
    frequency=[]
    universe=sorted({pd.Timestamp(x).strftime('%Y-%m-%d') for x in plan.day if 2018<=pd.Timestamp(x).year<=2022})
    for mode in MODES:
        counts=ens[ens.account==mode].groupby('entry_session').size()
        for date in universe:frequency.append(dict(account=mode,session=date,entries=int(counts.get(date,0))))
    save(pd.DataFrame(frequency),out/'ENTRY_FREQUENCY.csv')
    statistics(alltr,out)
    meta=dict(stage='V20-03',status='PARTIAL/HOLD',independent_OOS=False,full_N4=False,
              policy_sha256=sha(STAGE/'ROLL_POLICY_LOCKED_V1.md'),original_preserved_files=preserved,
              input_contracts=len(raw),input_rows=sum(map(len,raw.values())),
              observed_closed=len(alltr),stat_eligible_closed=int(alltr.stat_eligible.sum()),
              censored_closed=int((~alltr.stat_eligible).sum()),open_positions=len(opened),entries=len(ens),
              source_hashes={str(p.relative_to(ROOT)):sha(p) for p in [*sorted((ROOT/'history_2018_2022_original').glob('*/*.csv')),
                      ROOT/'source_archive/2018-2022.zip',*[BASE/p for p in LOCKED],
                      BASE/'legacy_v4/dependencies/study.py',STAGE/'offline/stress_v20_03.py',STAGE/'ROLL_POLICY_LOCKED_V1.md']},
              versions=dict(python=sys.version.split()[0],numpy=np.__version__,pandas=pd.__version__))
    (out/'RUN_METADATA.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    hashes={p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file() and p.name!='RESULT_HASHES.json'}
    (out/'RESULT_HASHES.json').write_text(json.dumps(hashes,indent=2)+'\n')
    print(json.dumps({k:v for k,v in meta.items() if k not in ['source_hashes','versions']},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
