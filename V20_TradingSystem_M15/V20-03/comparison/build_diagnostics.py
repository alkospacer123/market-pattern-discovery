#!/usr/bin/env python3
"""V20-03 diagnostics, immutable rules, C1/C0 only. No broker/network access.

python build_diagnostics.py --market-data /workspace/market-pattern-data/forever \
  --work /workspace/work/v20_pf

Only the missing late three-strategy ledger is reproduced. Archived causality,
signal parity, full research, quarterly replay, C2/STRICT and WF are not rerun.
--existing-replay reads a previously generated diagnostic ledger in this task.
Market data and feature caches remain outside the repository.
"""
from __future__ import annotations
import argparse, ast, hashlib, json, math, sys, warnings
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pandas as pd

warnings.filterwarnings('ignore', category=FutureWarning)
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
STAGE=ROOT/'V20-03'
BASE=ROOT/'research_original_v20'
MODES=['SHALLOW_PULLBACK','OBV_PRESSURE','INSIDE_DAY_RELEASE']
ALL='ALL_INDEPENDENT_ACCOUNTS'
PAIRS={'CNY':'CNYRUBF','MIX':'IMOEXF','Si':'USDRUBF'}
SYMS=['CNYRUBF','GLDRUBF','IMOEXF','USDRUBF']

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return pd.read_csv(p)
def save(d,n):pd.DataFrame(d).to_csv(OUT/n,index=False,float_format='%.12g',lineterminator='\n')
def fn(path,name,env):
    node=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name==name)
    ns=dict(env);exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),ns)
    return ns[name]
def lit(path,name):
    return ast.literal_eval(next(n.value for n in ast.parse(path.read_text()).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets)))

def reproduce(market,work,existing):
    index=json.loads((STAGE/'publication/ARCHIVE_FILE_INDEX.json').read_text())
    hashes={r['path']:r['sha256'] for r in index['files']}
    env=dict(np=np,pd=pd,math=math,defaultdict=defaultdict)
    inputs=work/'marketdata_m15';inputs.mkdir(parents=True,exist_ok=True)
    sources=[]
    for s in SYMS:
        p=market/s/f'{s}_M15.csv';h=sha(p)
        assert h==hashes[f'research_original_v20/marketdata_m15/{s}_M15.csv']
        sources.append(dict(path=str(p),sha256=h,status='PASS',role='ORIGINAL_MARKET_BYTES'))
        link=inputs/p.name
        if not link.exists():link.symlink_to(p)
        assert sha(link)==h
    prepare=fn(BASE/'base.py','prepare',dict(env,ROOT=work,MODES=lit(BASE/'base.py','MODES')))
    sig=fn(BASE/'run.py','sig',env)
    signals=fn(BASE/'run.py','signals',dict(env,b=SimpleNamespace(prepare=prepare),M=lit(BASE/'run.py','M'),sig=sig))
    prep=fn(BASE/'legacy_v4/dependencies/study.py','prep',dict(env,ROOT=inputs))
    inside=fn(BASE/'legacy_v4/study_v4.py','add_indicators',dict(env,MODES=lit(BASE/'legacy_v4/study_v4.py','MODES')))
    frames={}
    for s in SYMS:
        # Feature caches are task-local products of these exact AST functions.
        cache=work/f'{s}.pkl'
        if existing and cache.exists():d=pd.read_pickle(cache)
        else:
            d=signals(s);d['INSIDE_DAY_RELEASE']=inside(prep(s),s).INSIDE_DAY_RELEASE
        frames[s]=d
    runner=ROOT/'V20-02_AUDIT/replay_independent.py'
    if existing:
        late=read(existing);meta=json.loads((work/'replay_meta.json').read_text())
    else:
        one=fn(runner,'run_one',dict(env,SYMS=SYMS,TICKS=lit(BASE/'base.py','TICKS'),COLS=lit(runner,'COLS')))
        tr=[];meta={}
        for n,(name,mode) in enumerate(lit(runner,'ACCOUNTS'),1):
            t,m=one(frames,n,name,mode);t['account']=mode;tr.append(t);meta[mode]=m
        late=pd.concat(tr,ignore_index=True)
    summary=read(ROOT/'V20-02_AUDIT/PARITY_SUMMARY.csv')
    checks=[]
    for mode in MODES:
        q=late[late.account.eq(mode)];r=summary[summary.model.eq(mode)].iloc[0]
        assert len(q)==r.trades
        assert math.isclose(q.net_R.sum(),r.net_R,abs_tol=1e-9)
        assert math.isclose(q.net_R[q.net_R>0].sum()/-q.net_R[q.net_R<0].sum(),r.PF,abs_tol=1e-10)
        counts=q.exit_reason.value_counts().to_dict()
        archived=json.loads((ROOT/'V20-02_AUDIT/ACCEPTANCE_V20_02.json').read_text())['meta'][mode]
        assert {str(k):v for k,v in counts.items()}==archived['exits']
        checks.append(dict(check=f'LATE_REPRODUCTION_{mode}',status='PASS',trades=len(q),basis='EXACT_INPUT_SHA256_AND_AGGREGATE_EXIT_COUNTS_NOT_ROW_PARITY_WITH_MISSING_ORIGINAL'))
    save(late,'DIAGNOSTIC_REPLAY_TRADES.csv')
    late=late.rename(columns={'net_R':'net_C1_R'});late['family']=late.symbol
    late['contract']=late.symbol
    late['tick_entry']=late.symbol.map(lit(BASE/'base.py','TICKS'));late['tick_exit']=late.tick_entry
    late['atr_at_signal']=[frames[r.symbol].set_index('Datetime').at[pd.Timestamp(r.signal_dt)-pd.Timedelta(minutes=15),'atr'] for r in late.itertuples()]
    late['exit_year']=pd.to_datetime(late.exit_dt).dt.year
    late['exit_month']=pd.to_datetime(late.exit_dt).dt.strftime('%Y-%m')
    late['period']='2023-2026';late['trade_source']='EXACT_RULE_DIAGNOSTIC_REPRODUCTION_ORIGINAL_LEDGER_MISSING'
    return late,frames,sources,checks,meta

def metrics(q):
    q=q.sort_values(['exit_dt','entry_dt','account_num','contract'],kind='stable')
    r=q.net_C1_R.to_numpy(float);w=r[r>0];l=r[r<0]
    c=np.r_[0,np.cumsum(r)];gp=float(w.sum());gl=float(-l.sum())
    g=q.gross_R.to_numpy(float);gw=g[g>0].sum();gloss=-g[g<0].sum()
    out=dict(trades=len(q),PF_C1=gp/gl if gl else np.nan,net_R=float(r.sum()),expectancy=float(r.mean()) if len(r) else np.nan,
      wins=len(w),losses=len(l),breakeven=int((r==0).sum()),win_rate=len(w)/len(r) if len(r) else np.nan,
      average_win=float(w.mean()) if len(w) else np.nan,average_loss=float(-l.mean()) if len(l) else np.nan,
      win_loss_ratio=float(w.mean()/-l.mean()) if len(w) and len(l) else np.nan,
      max_DD_closed_R=float((np.maximum.accumulate(c)-c).max()),gross_profit_R=gp,gross_loss_R=gl,
      PF_C0=float(gw/gloss) if gloss else np.nan,net_C0_R=float(g.sum()),C1_cost_R=float((g-r).sum()),
      stop_exits=int(q.exit_reason.isin([1,2,4]).sum()),time_exits=int(q.exit_reason.eq(3).sum()),
      entry_bar_stops=int(q.exit_reason.eq(4).sum()),gap_reason_exits=int(q.exit_reason.eq(2).sum()),
      adverse_gap_exits=int((q.exit_reason.isin([2,3]) & q.gross_R.lt(-1-1e-7)).sum()))
    for col in ['stop_exits','time_exits','entry_bar_stops','gap_reason_exits','adverse_gap_exits']:out[col+'_fraction']=out[col]/len(q) if len(q) else np.nan
    for k in [5,10]:
        top=np.sort(w)[-k:].sum();out[f'top{k}_winners_R']=float(top)
        out[f'top{k}_share_positive_R']=float(top/gp) if gp else np.nan
        out[f'top{k}_over_net_R']=float(top/r.sum()) if r.sum() else np.nan
        rr=r.copy();indices=np.flatnonzero(rr>0);largest=indices[np.argsort(rr[indices])[-k:]];rr=np.delete(rr,largest)
        out[f'without_top{k}_net_R']=float(rr.sum());den=-rr[rr<0].sum();out[f'without_top{k}_PF']=float(rr[rr>0].sum()/den) if den else np.nan
    return out

def groups(d):
    yield ALL,d
    for a in MODES:yield a,d[d.account.eq(a)]

def analyse(old,late):
    period=[];instrument=[];distribution=[];stability=[]
    for d in [old,late]:
        p=d.period.iloc[0];source=d.trade_source.iloc[0]
        two=['Si','MIX'] if p=='2018-2022' else ['USDRUBF','IMOEXF']
        for a,q in groups(d):
            for scope,s in [('FULL_AVAILABLE',q),('TWO_FILTERED_EXECUTED',q[q.family.isin(two)])]:
                period.append(dict(period=p,strategy=a,scope=scope,status='VERIFIED_FROM_PUBLISHED_LEDGER' if p=='2018-2022' else 'REPRODUCED_ORIGINAL_LEDGER_NOT_VERIFIED',trade_source=source,**metrics(s)))
            for symbol,s in [('ALL',q),*list(q.groupby('family'))]:
                instrument.append(dict(record_type='TRADE_METRICS',period=p,strategy=a,instrument=symbol,status='CONDITIONAL',**metrics(s)))
                for year,z in [('ALL',s),*list(s.groupby('exit_year'))]:
                    ap=100*z.atr_at_signal/z.entry
                    instrument.append(dict(record_type='TRADE_CONDITIONED_ATR_YEAR',period=p,strategy=a,instrument=symbol,year=year,
                        status='SIGNAL_ATR_DIVIDED_BY_ENTRY_PRICE_NOT_ALL_MARKET_BARS',trades=len(z),
                        ATR14_entry_price_pct_p10=ap.quantile(.1),ATR14_entry_price_pct_median=ap.median(),ATR14_entry_price_pct_p90=ap.quantile(.9)))
                for why,z in [('ALL',s),*[(str(k),s[s.exit_reason.eq(k)]) for k in [1,2,3,4]]]:
                    distribution.append(dict(record_type='EXIT_DISTRIBUTION',period=p,strategy=a,instrument=symbol,exit_reason=why,**metrics(z)))
                for y,z in s.groupby('exit_year'):
                    stability.append(dict(period=p,strategy=a,instrument=symbol,diagnostic='YEAR',excluded_period='',year=y,**metrics(z)))
                if not len(s):continue
                ys=s.groupby('exit_year').net_C1_R.sum();ms=s.groupby('exit_month').net_C1_R.sum()
                for label,n in [('WITHOUT_BEST_YEAR',1),('WITHOUT_BEST_MONTH',1),('WITHOUT_BEST_3_MONTHS',3)]:
                    best=ys.nlargest(n).index if label.endswith('YEAR') else ms.nlargest(n).index
                    z=s[~s.exit_year.isin(best)] if label.endswith('YEAR') else s[~s.exit_month.isin(best)]
                    stability.append(dict(period=p,strategy=a,instrument=symbol,diagnostic=label,excluded_period=';'.join(map(str,best)),year='',**metrics(z)))
    return period,instrument,distribution,stability

def late_market(frames,late):
    market=[];trajectories=[]
    ticks=lit(BASE/'base.py','TICKS')
    for sym,d0 in frames.items():
        d=d0.copy();d['year']=d.Datetime.dt.year
        atrpct=100*d.atr/d.Close
        pressure=(((d.Close-d.Low)-(d.High-d.Close))/(d.High-d.Low).replace(0,np.nan)).fillna(0)*d.Volume
        pressure=pressure.shift(1).rolling(12,min_periods=12).sum()/d.Volume.shift(1).rolling(12,min_periods=12).sum().replace(0,np.nan)
        relative_volume=d.Volume/d.Volume.shift(1).rolling(20,min_periods=20).mean()
        days=list(pd.unique(d.day));dayindex={x:i for i,x in enumerate(days)}
        first={k:int(z.index[0]) for k,z in d.groupby('day',sort=False)}
        horizon=[]
        for i in range(len(d)-1):
            if d.Datetime.iat[i+1]-d.Datetime.iat[i]!=pd.Timedelta(minutes=15):continue
            en=i+1;di=dayindex[d.day.iat[en]]
            if di+2>=len(days):continue
            end=first[days[di+2]]
            if end<=en:continue
            a=d.atr.iat[i]
            if not np.isfinite(a) or a<=0:continue
            horizon.append((i,en,end))
        hmap={i:(en,end) for i,en,end in horizon}
        for y,z in d.groupby('year'):
            ap=atrpct.loc[z.index].dropna();rp=relative_volume.loc[z.index].dropna();ps=pressure.loc[z.index].dropna()
            # 1 R is the original 2 ATR stop distance; these are descriptive bins.
            hr=[]
            for i,en,end in horizon:
                if d.year.iat[i]!=y:continue
                risk=2*d.atr.iat[i]
                hr.append((d.Open.iat[end]-d.Open.iat[en])/risk)
            h=np.asarray(hr)
            market.append(dict(record_type='MARKET_YEAR',period='2023-2026',strategy='ALL',instrument=sym,year=y,status='VERIFIED_LATE_ONLY',
                bars=len(z),first_timestamp=str(z.Datetime.min()),last_timestamp=str(z.Datetime.max()),observed_sessions=z.day.nunique(),
                ATR14_price_pct_p10=ap.quantile(.1),ATR14_price_pct_p25=ap.quantile(.25),ATR14_price_pct_median=ap.median(),ATR14_price_pct_p75=ap.quantile(.75),ATR14_price_pct_p90=ap.quantile(.9),
                volume_median=z.Volume.median(),volume_p90=z.Volume.quantile(.9),volume_zero_fraction=z.Volume.eq(0).mean(),
                relative_volume_median=rp.median(),pressure_abs_gt035_fraction=ps.abs().gt(.35).mean(),
                horizon_pairs=len(h),horizon_absolute_displacement_gt_1R_fraction=float((abs(h)>1).mean()) if len(h) else np.nan,
                horizon_absolute_displacement_le_1R_fraction=float((abs(h)<=1).mean()) if len(h) else np.nan))
        for mode in MODES:
            signal_rows=[];actual_rows=[]
            for i in np.flatnonzero(d[mode].to_numpy()!=0):
                if i not in hmap:continue
                en,end=hmap[i];side=int(d[mode].iat[i]);entry=d.Open.iat[en]
                target=entry-side*2*d.atr.iat[i];tick=ticks[sym]
                stop=(math.floor(target/tick+1e-9) if side==1 else math.ceil(target/tick-1e-9))*tick;risk=abs(entry-stop)
                highs=d.High.iloc[en:end].to_numpy();lows=d.Low.iloc[en:end].to_numpy()
                terminal=d.Open.iat[end]
                favorable=max(0,side*(max(highs.max(),terminal)-entry) if side==1 else side*(min(lows.min(),terminal)-entry))/risk
                adverse=max(0,(entry-min(lows.min(),terminal)) if side==1 else (max(highs.max(),terminal)-entry))/risk
                signal_rows.append(dict(year=int(d.year.iat[i]),horizon_R=side*(terminal-entry)/risk,MFE_R=favorable,MAE_R=adverse,
                  stop_touch=adverse>=1-1e-7,relative_volume=relative_volume.iat[i]))
            for r in late[late.account.eq(mode)&late.symbol.eq(sym)].itertuples():
                en=int(d.index[d.Datetime.eq(pd.Timestamp(r.entry_dt))][0]);ex=int(d.index[d.Datetime.eq(pd.Timestamp(r.exit_dt))][0])
                # Prior full bars and the exit open are observable before stop/time exit.
                # A favorable high on the stop candle has unknown ordering and is excluded.
                pre=d.iloc[en:ex]
                favorable_prices=[r.entry,d.Open.iat[ex]]
                if len(pre):favorable_prices.append(pre.High.max() if r.side==1 else pre.Low.min())
                definite=max(r.side*(x-r.entry)/r.risk for x in favorable_prices)
                actual_rows.append(dict(year=int(r.exit_year),loss=r.net_C1_R<0,definite_MFE_R=max(0,definite),
                  favorable_then_loss=(r.net_C1_R<0 and definite>1e-7),favorable_1R_then_loss=(r.net_C1_R<0 and definite>=1-1e-7)))
            for kind,rows in [('RAW_FROZEN_SIGNALS',signal_rows),('EXECUTED_TRADE_PATH_LOWER_BOUND',actual_rows)]:
                data=pd.DataFrame(rows)
                if data.empty:continue
                for y,z in [('ALL',data),*list(data.groupby('year'))]:
                    out=dict(record_type=kind,period='2023-2026',strategy=mode,instrument=sym,year=y,observations=len(z),status='VERIFIED_LATE_ONLY')
                    if kind=='RAW_FROZEN_SIGNALS':
                        out.update(mean_horizon_R=z.horizon_R.mean(),median_horizon_R=z.horizon_R.median(),
                          positive_horizon_fraction=z.horizon_R.gt(0).mean(),horizon_above_1R_fraction=z.horizon_R.gt(1).mean(),
                          MFE_R_mean=z.MFE_R.mean(),MFE_R_median=z.MFE_R.median(),MAE_R_mean=z.MAE_R.mean(),stop_touch_fraction=z.stop_touch.mean(),
                          signal_relative_volume_median=z.relative_volume.median(),signal_relative_volume_p90=z.relative_volume.quantile(.9))
                    else:
                        out.update(losses=int(z.loss.sum()),definite_favorable_then_loss=int(z.favorable_then_loss.sum()),
                          definite_favorable_then_loss_fraction=z.favorable_then_loss.mean(),
                          definite_favorable_then_loss_fraction_of_losses=z.favorable_then_loss.sum()/z.loss.sum() if z.loss.sum() else np.nan,
                          definite_1R_then_loss=int(z.favorable_1R_then_loss.sum()),definite_MFE_R_mean=z.definite_MFE_R.mean())
                    trajectories.append(out)
    for f in ['CNY','MIX','Si']:
        for y in range(2018,2023):market.append(dict(record_type='MARKET_YEAR',period='2018-2022',strategy='ALL',instrument=f,year=y,status='NOT VERIFIED: ORIGINAL QUARTERLY M15 MISSING'))
    return market,trajectories

def frequencies(period,instrument,stability,late,frames,meta):
    old_en=read(STAGE/'results/ENTRIES.csv')
    new_en=late[['account','family','entry_dt','entry_session']].copy()
    for mode,m in meta.items():
        for r in m['terminal_positions']:
            en=pd.Timestamp(r['entry_dt'])
            new_en.loc[len(new_en)]=[mode,r['symbol'],r['entry_dt'],str((en-pd.Timedelta(hours=9)).date())]
    old_sessions=read(STAGE/'results/SESSION_AUDIT.csv')[['family','day']].drop_duplicates()
    new_sessions=pd.concat([pd.DataFrame(dict(family=s,day=pd.unique(d.day))) for s,d in frames.items()],ignore_index=True)
    def values(p,a,symbol,year=None):
        en=old_en if p=='2018-2022' else new_en
        ses=old_sessions if p=='2018-2022' else new_sessions
        en=en.copy();ses=ses.copy()
        en['year']=pd.to_datetime(en.entry_session).dt.year;ses['year']=pd.to_datetime(ses.day).dt.year
        years=range(2018,2023) if p=='2018-2022' else range(2023,2027)
        en=en[en.year.isin(years)];ses=ses[ses.year.isin(years)]
        if a!=ALL:en=en[en.account.eq(a)]
        if symbol!='ALL':en=en[en.family.eq(symbol)];ses=ses[ses.family.eq(symbol)]
        if year is not None:en=en[en.year.eq(year)];ses=ses[ses.year.eq(year)]
        n=ses.day.nunique()
        return dict(entries_all_observed=len(en),observed_session_keys=int(n),entries_per100_observed_sessions=100*len(en)/n if n else np.nan)
    for r in period:
        if r['scope']=='FULL_AVAILABLE':r.update(values(r['period'],r['strategy'],'ALL'))
    for r in instrument:
        if r['record_type']=='TRADE_METRICS':r.update(values(r['period'],r['strategy'],r['instrument']))
    for r in stability:
        if r['diagnostic']=='YEAR':r.update(values(r['period'],r['strategy'],r['instrument'],int(r['year'])))

def audit(old,late):
    cv=read(STAGE/'results/EFFECTIVE_COVERAGE.csv');cv['year']=pd.to_datetime(cv.day).dt.year
    gaps=read(STAGE/'results/INVALID_INTERVALS.csv');gaps['year']=pd.to_datetime(gaps.next_bar).dt.year
    en=read(STAGE/'results/ENTRIES.csv');checks=[]
    def check(name,condition,detail):
        checks.append(dict(check=name,status='PASS' if condition else 'FAIL',detail=detail))
        assert condition,(name,detail)
    check('NEXT_OPEN',bool((pd.to_datetime(en.entry_dt)-pd.to_datetime(en.signal_bar_dt)).eq(pd.Timedelta(minutes=15)).all()),'1016 entries: +15 minutes exactly')
    check('RISK_AND_ATR',bool(((en.risk-2*en.atr_at_signal)>=-1e-7).all() and ((en.risk-2*en.atr_at_signal)<en.tick_entry+1e-7).all()),'Original 2 ATR with outward rounding, no stop optimization')
    check('STOP_GRID',bool(np.allclose(en.stop/en.tick_entry,np.round(en.stop/en.tick_entry),atol=1e-6,rtol=0)),'Executable grid at entry')
    check('C1_FORMULA',bool(np.allclose(old.net_C1_R,old.gross_R-(old.tick_entry+old.tick_exit)/old.risk,atol=1e-9,rtol=0)),'One tick per side')
    check('ENTRY_CAPS',bool(en.groupby(['account','entry_session']).size().max()<=2 and en.groupby(['account','family','entry_session']).size().max()<=1),'Separate accounts, one underlying/session, two entries/session')
    check('CHOSEN_CONTRACT',bool(en.contract.eq(en.chosen_contract).all()),'Existing entry records agree with locked selection')
    check('STOP_PRICES',bool(np.allclose(old.loc[old.exit_reason.isin([1,4]),'gross_R'],-1,atol=1e-8,rtol=0)),'Stop hits execute at original stop')
    check('THIRD_OBSERVED_SESSION',bool(old.loc[old.exit_reason.eq(3),'session_span'].eq(3).all()),'All time exits at third observed family session; first bar checked against published session audit separately')
    # Recompute locked selection from existing session summaries, no candles/replay.
    runner=STAGE/'offline/stress_v20_03.py';env=dict(pd=pd,FAMILIES=['CNY','MIX','Si'])
    maturity=fn(runner,'maturity',env);cutoff=fn(runner,'cutoff',dict(env,maturity=maturity))
    planfn=fn(runner,'roll_plan',dict(env,maturity=maturity,cutoff=cutoff))
    sessions=read(STAGE/'results/SESSION_AUDIT.csv')
    for c in ['day','first_bar','last_bar','known_after']:sessions[c]=pd.to_datetime(sessions[c])
    plan=planfn(sessions);stored=read(STAGE/'results/ROLL_DECISIONS.csv').fillna('')
    check('ROLL_FROM_EXISTING_SUMMARIES',bool(plan.chosen_contract.fillna('').tolist()==stored.chosen_contract.tolist()),'All 2805 choices reproduce from prior-session summaries; no new roll rules')
    first=sessions.groupby(['family','day']).first_bar.min()
    time=old[old.exit_reason.eq(3)]
    # Existing positions remain in their own contract, first observation may differ.
    contractfirst=sessions.set_index(['contract','day']).first_bar
    ok=True
    for r in time.itertuples():
        dt=pd.Timestamp(r.exit_dt);day=(dt-pd.Timedelta(hours=9)).normalize()
        ok &= contractfirst.loc[(r.contract,day)]==dt
    check('TIME_EXIT_FIRST_OBSERVED_CONTRACT_BAR',bool(ok),'All 267 time exits match first bar of their third session in SESSION_AUDIT')
    coverage=[]
    for (family,year),q in cv.groupby(['family','year']):
        gs=gaps[gaps.family.eq(family)&gaps.year.eq(year)]
        coverage.append(dict(family=family,year=int(year),observed_family_sessions=len(q),no_past_candidate=int(q.chosen_contract.isna().sum()),
          selected_without_bars=int(q.coverage_status.eq('CHOSEN_CONTRACT_NO_CURRENT_OBSERVATIONS').sum()),
          selected_bars=int(q.observed_selected_rows.sum()),selected_warmup_bars=int(q.warmup_bars.sum()),unknown_gaps_all_series=len(gs)))
    return checks,coverage

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--market-data',type=Path,required=True);ap.add_argument('--work',type=Path,required=True)
    ap.add_argument('--existing-replay',type=Path);args=ap.parse_args()
    assert ROOT not in args.work.resolve().parents and args.work.resolve()!=ROOT
    late,frames,sources,checks,meta=reproduce(args.market_data.resolve(),args.work.resolve(),args.existing_replay)
    old=read(STAGE/'results/CLOSED_TRADES.csv');old['period']='2018-2022';old['trade_source']='PUBLISHED_ORIGINAL_LEDGER'
    period,instrument,distribution,stability=analyse(old,late)
    frequencies(period,instrument,stability,late,frames,meta)
    market,paths=late_market(frames,late)
    save(period,'PERIOD_STRATEGY_COMPARISON.csv');save(instrument+market,'INSTRUMENT_COMPARISON.csv')
    save(distribution+paths,'TRADE_DISTRIBUTION.csv');save(stability,'YEARLY_STABILITY.csv')
    ac,coverage=audit(old,late);checks+=ac
    # Independent old-ledger validation of the published strategy totals.
    published=read(STAGE/'results/STATISTICS.csv')
    for a,q in groups(old):
        m=metrics(q);r=published[published.account.eq(a)&published.scenario.eq('C1')&published.family.eq('ALL')&published.kind.eq('ALL')].iloc[0]
        assert m['trades']==r.trades
        for key,col in [('PF_C1','PF'),('net_R','R'),('max_DD_closed_R','DD_closed_R')]:assert math.isclose(m[key],r[col],abs_tol=1e-7)
    checks.append(dict(check='OLD_LEDGER_AGGREGATES',status='PASS',detail='Independent PF/net/DD calculations agree'))
    checks.extend([
      dict(check='ORIGINAL_1589_LEDGER_AVAILABLE',status='FAIL',detail='Missing locally and in PR/main; expected SHA256 63844fac6741e21cca00c7ad0143114e743d7bb5649b18d5a8a64b76db121efb. Diagnostic reproduction is NOT an original artifact.'),
      dict(check='OLD_M15_SOURCE_AVAILABLE',status='FAIL',detail='43 quarterly source files/ZIP missing; no old price-path or market-regime comparison asserted'),
      dict(check='STRICT_PERIOD_TYPE_ATTRIBUTION',status='NOT VERIFIED',detail='No matched contemporaneous quarterly/perpetual dataset established'),
      dict(check='SUPPRESSION_COUNTERFACTUAL',status='NOT VERIFIED',detail='No signal-level rejection journal in original publication; no independent two-symbol replay performed'),
      dict(check='OLD_INTRABAR_EXECUTION',status='NOT VERIFIED',detail='Trade and session journals permit consistency checks, not independent candle replay')])
    files=[p for p in (STAGE/'results').iterdir() if p.is_file()]
    files += [ROOT/'V20-02_AUDIT/PARITY_SUMMARY.csv',ROOT/'V20-02_AUDIT/ACCEPTANCE_V20_02.json',ROOT/'V20-02_AUDIT/replay_independent.py',
      STAGE/'publication/ARCHIVE_FILE_INDEX.json',ROOT/'docs/RESEARCH_LINEAGE.json',STAGE/'ROLL_POLICY_LOCKED_V1.md',STAGE/'offline/stress_v20_03.py',
      BASE/'base.py',BASE/'run.py',BASE/'legacy_v4/study_v4.py',BASE/'legacy_v4/dependencies/study.py']
    sources += [dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size,role='PUBLISHED_ORIGINAL') for p in files]
    censored=read(STAGE/'results/CENSORED_CLOSED.csv');sensitivity=[]
    for a,q in groups(old):
        cc=censored if a==ALL else censored[censored.account.eq(a)]
        sensitivity.append(dict(strategy=a,censored_trades=len(cc),observed_censored_R=float(cc.net_C1_R.sum()),primary=metrics(q),mechanical_all_observed=metrics(pd.concat([q,cc],ignore_index=True)),true_gap_execution='UNKNOWN'))
    comparison=[];outcome=[]
    for a in [ALL,*MODES]:
        rows=[r for r in period if r['strategy']==a]
        get=lambda p,s:next(r for r in rows if r['period']==p and r['scope']==s)
        fnew=get('2023-2026','FULL_AVAILABLE')['PF_C1'];fold=get('2018-2022','FULL_AVAILABLE')['PF_C1']
        tnew=get('2023-2026','TWO_FILTERED_EXECUTED')['PF_C1'];told=get('2018-2022','TWO_FILTERED_EXECUTED')['PF_C1']
        comparison.append(dict(strategy=a,full_PF_gap=fnew-fold,two_filtered_PF_gap=tnew-told,
          descriptive_composition_contrast=(fnew-fold)-(tnew-told),fraction_of_full_gap=((fnew-fold)-(tnew-told))/(fnew-fold),causal=False))
        o=get('2018-2022','FULL_AVAILABLE');l=get('2023-2026','FULL_AVAILABLE')
        factors=dict(strategy=a,old_over_late_win_loss_count_ratio=(o['wins']/o['losses'])/(l['wins']/l['losses']),
          old_over_late_average_win=o['average_win']/l['average_win'],late_over_old_average_loss=l['average_loss']/o['average_loss'],old_over_late_PF=o['PF_C1']/l['PF_C1'],causal=False)
        assert math.isclose(factors['old_over_late_win_loss_count_ratio']*factors['old_over_late_average_win']*factors['late_over_old_average_loss'],factors['old_over_late_PF'],abs_tol=1e-10)
        outcome.append(factors)
    verification=dict(status='PARTIAL',date='2026-10-21',repository='alkospacer123/market-pattern-discovery',
      main_sha='c3695b1304aef1acdd889264b3451184f7332bf7',input_PR_sha='072c4ccc9ab22e5c8b0c3d172272ebe29932fdd3',
      original_offline_zip_expected_sha256='1ab1f85373c2bbd7a385d228ea061f0cd8259f409a73d40babbcfc0ba7f5eb50',original_offline_zip_available=False,
      original_1589_ledger_available=False,late_trade_basis='ONE_LIMITED_EXACT_RULE_REPRODUCTION',late_row_parity_with_original='NOT VERIFIED',
      late_replay_reason='Missing original trade ledger prevents requested instrument, exit and concentration diagnostics; four original M15 hashes match archive index',
      replay_scope='Only three frozen strategies, full late N4, unchanged V20-02 run_one AST; no parameter search, no quarterly replay, no causality rerun',
      replay_meta=meta,new_replay_batches=1,strategy_replays=3,C2_STRICT_runs=0,optimization_runs=0,walk_forward_runs=0,
      source_files=sources,checks=checks,coverage_by_family_year=coverage,censored_sensitivity=sensitivity,composition_contrasts=comparison,outcome_PF_identity_decomposition=outcome,
      DD_method='Closed C1 R, initial peak=0, stable sort exit_dt/entry_dt/account_num/contract; pooled independent accounts are arithmetic diagnostics, not cash/MTM equity',
      market_bins='Absolute displacement in 2 ATR initial risk to first Open of third observed session, bins >1R and <=1R; descriptive, no new trading filters',
      path_method='Raw signals: all original signals independent of execution constraints, exact NEXT_OPEN and original horizon. Actual paths: favorable excursion lower bound using prior bars and exit Open, excluding stop-candle OHLC ambiguity',
      original_checks_rerun=False,scope='V20_TradingSystem_M15 only; no production/FINAM/main mutation',
      artifact_hashes={p.name:sha(p) for p in OUT.iterdir() if p.suffix in ['.csv','.py']},
      python=sys.version.split()[0],pandas=pd.__version__,numpy=np.__version__)
    (OUT/'VERIFICATION.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(period_rows=len(period),instrument_rows=len(instrument)+len(market),distribution_rows=len(distribution)+len(paths),stability_rows=len(stability),checks={s:sum(x['status']==s for x in checks) for s in ['PASS','FAIL','NOT VERIFIED']}),ensure_ascii=False))

if __name__=='__main__':main()
