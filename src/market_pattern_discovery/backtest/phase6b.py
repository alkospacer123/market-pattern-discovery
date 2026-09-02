"""Corrected causal Phase 6B known-strategy benchmark."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from hashlib import sha256
from time import perf_counter
import json, math, resource
import numpy as np
import pandas as pd
from market_pattern_discovery.data.finam import stitch_finam
from market_pattern_discovery.features.core import canonical_trading_date

START=pd.Timestamp('2026-01-05',tz='Europe/Moscow'); END=pd.Timestamp('2026-05-16',tz='Europe/Moscow')
SPECS={'CNYRUBF':(.001,.05,'CNY'),'USDRUBF':(.01,.10,'Si')}
INSTRUMENT_ALIASES={'CNY':'CNYRUBF','CNYRUBF':'CNYRUBF','Si':'USDRUBF','SI':'USDRUBF','USDRUBF':'USDRUBF'}
STRATEGIES=('RL-01','RL-02','RL-03','RL-04','MOM-01','MOM-02','NR-01','RH-01','RH-02','PD-01','PD-02')
SKIPPED={'EH-01':'No authoritative causal Equal High/Equal Low reference-price primitive is exposed.',
         'EH-02':'No authoritative causal Equal High/Equal Low reference-price primitive is exposed.'}
TRADING_DATE_SOURCE='market_pattern_discovery.features.core.canonical_trading_date'
ATR_SOURCE='phase6b fallback: standard causal Wilder ATR(14)'
ATR_DEFINITION='TR=max(high-low,abs(high-prev_close),abs(low-prev_close)); seed=mean(first 14 TR); Wilder recurrence alpha=1/14'

@dataclass(frozen=True, slots=True)
class ExecutionContext:
    """The data scope selected by V3.5 metadata for one causal V3 run."""
    instrument: str | None = None
    timeframe: str = 'M1'

    def __post_init__(self):
        if self.instrument is not None and self.instrument not in INSTRUMENT_ALIASES:
            raise ValueError(f'unsupported instrument: {self.instrument}')
        if self.timeframe not in {'M1','M5'}:
            raise ValueError(f'unsupported timeframe: {self.timeframe}')

    @classmethod
    def from_metadata(cls, metadata):
        """Build a scope from ExperimentSpec metadata, retaining V3 defaults."""
        metadata=dict(metadata or {})
        instrument=metadata.get('instrument',metadata.get('instrument_scope'))
        timeframe=metadata.get('timeframe',metadata.get('timeframe_scope','M1'))
        return cls(instrument=instrument,timeframe=timeframe)

    @property
    def instruments(self):
        return tuple(SPECS) if self.instrument is None else (INSTRUMENT_ALIASES[self.instrument],)

def add_wilder_atr14(frame):
    """Continuous per-instrument Wilder ATR; deliberately never resets by day."""
    f=frame.copy(); prev=f.close.shift(1)
    tr=np.maximum.reduce([(f.high-f.low).to_numpy(float),(f.high-prev).abs().fillna(0).to_numpy(float),(f.low-prev).abs().fillna(0).to_numpy(float)])
    out=np.full(len(f),np.nan)
    if len(f)>=14:
        out[13]=tr[:14].mean()
        for i in range(14,len(f)): out[i]=(out[i-1]*13+tr[i])/14
    f['atr14']=out; return f

def load_discovery(data_root,instrument,timeframe='M1'):
    tick,_,folder=SPECS[instrument]
    paths=sorted((Path(data_root)/'2026'/folder).glob(f'*_2026_Q[12]_{timeframe}.csv'))
    result=stitch_finam(paths,instrument,timeframe); f=result.frame
    f=f.loc[(f.open_time>=START)&(f.close_time<END)].copy()
    if f.empty or f.open_time.dt.year.ne(2026).any() or f.close_time.max()>=END: raise ValueError('discovery boundary violation')
    f['trading_date']=canonical_trading_date(f.open_time); f=add_wilder_atr14(f); f['tick']=tick
    return f.reset_index(drop=True),result.provenance

def _event(strategy,i,side,atr,ref=None,**audit):
    return {'strategy_id':strategy,'bar_index':i,'side':'LONG' if side==1 else 'SHORT','direction':side,'ATR_at_signal':atr,'reference_level':ref,**audit}

def _grid_levels(lo,hi,step):
    a=math.ceil((lo-1e-10)/step); b=math.floor((hi+1e-10)/step)
    return [round(k*step,10) for k in range(a,b+1)] if a<=b else []

def generate_signals(frame,instrument,strategies=None):
    """Generate signals from closed-prefix data only, using actual involved grid levels."""
    wanted=set(strategies or STRATEGIES); tick,step,_=SPECS[instrument]; events=[]
    daily=frame.groupby('trading_date').agg(day_high=('high','max'),day_low=('low','min')); previous=daily.shift(1)
    ph=frame.trading_date.map(previous.day_high).to_numpy(float); pl=frame.trading_date.map(previous.day_low).to_numpy(float)
    op=frame.open.to_numpy(float); hi=frame.high.to_numpy(float); lo=frame.low.to_numpy(float); cl=frame.close.to_numpy(float); atr=frame.atr14.to_numpy(float)
    dates=frame.trading_date.to_numpy(); ranges=hi-lo
    for _,indices in frame.groupby('trading_date',sort=False).indices.items():
        ix=np.asarray(indices); nr=None; retests=[]
        for pos,i in enumerate(ix):
            if not np.isfinite(atr[i]) or pos==0: continue
            pi=ix[pos-1]; ppi=ix[pos-2] if pos>=2 else None
            # Actual touched/path levels, never recomputed solely from final close.
            touched=_grid_levels(lo[i]-tick,hi[i]+tick,step)
            long_cross=[L for L in _grid_levels(cl[pi],cl[i],step) if cl[pi]<=L and cl[i]>L+tick]
            short_cross=[L for L in _grid_levels(cl[i],cl[pi],step) if cl[pi]>=L and cl[i]<L-tick]
            long_L=max(long_cross) if long_cross else None; short_L=min(short_cross) if short_cross else None
            if 'RL-01' in wanted:
                q=[L for L in touched if lo[i]<=L+tick and cl[i]>L and cl[pi]>=L]
                if q: events.append(_event('RL-01',i,1,atr[i],max(q)))
                q=[L for L in touched if hi[i]>=L-tick and cl[i]<L and cl[pi]<=L]
                if q: events.append(_event('RL-01',i,-1,atr[i],min(q)))
            if long_L is not None:
                if 'RL-02' in wanted: events.append(_event('RL-02',i,1,atr[i],long_L))
                retests.append({'side':1,'level':long_L,'break_pos':pos})
            if short_L is not None:
                if 'RL-02' in wanted: events.append(_event('RL-02',i,-1,atr[i],short_L))
                retests.append({'side':-1,'level':short_L,'break_pos':pos})
            if 'RL-03' in wanted:
                long=[]; short=[]
                for L in set(touched+(_grid_levels(lo[pi]-tick,hi[pi]+tick,step) if ppi is not None else [])):
                    lp=(lo[i]<=L-tick and cl[pi]>=L) or (ppi is not None and lo[pi]<=L-tick and cl[ppi]>=L)
                    sp=(hi[i]>=L+tick and cl[pi]<=L) or (ppi is not None and hi[pi]>=L+tick and cl[ppi]<=L)
                    if lp and cl[i]>L: long.append(L)
                    if sp and cl[i]<L: short.append(L)
                if long: events.append(_event('RL-03',i,1,atr[i],max(long),return_window=2))
                if short: events.append(_event('RL-03',i,-1,atr[i],min(short),return_window=2))
            keep=[]
            for s in retests:
                age=pos-s['break_pos']; L=s['level']
                hit=1<=age<=5 and lo[i]<=L+tick and hi[i]>=L-tick and ((s['side']==1 and cl[i]>L) or (s['side']==-1 and cl[i]<L))
                if hit:
                    if 'RL-04' in wanted: events.append(_event('RL-04',i,s['side'],atr[i],L,retest_age=age))
                elif age<=5: keep.append(s)
            retests=keep
            if pos>=5 and 'MOM-01' in wanted:
                m=(cl[i]-cl[ix[pos-5]])/atr[i]
                if abs(m)>=.5: events.append(_event('MOM-01',i,1 if m>0 else -1,atr[i],momentum=m))
            if pos>=10 and 'MOM-02' in wanted:
                m=(cl[i]-cl[ix[pos-10]])/atr[i]
                if abs(m)>=.75: events.append(_event('MOM-02',i,1 if m>0 else -1,atr[i],momentum=m))
            if nr is not None and 'NR-01' in wanted:
                age=pos-nr['pos']
                if 1<=age<=10 and cl[i]>nr['high']: events.append(_event('NR-01',i,1,atr[i],nr['high'],nr_age=age)); nr=None
                elif 1<=age<=10 and cl[i]<nr['low']: events.append(_event('NR-01',i,-1,atr[i],nr['low'],nr_age=age)); nr=None
                elif age>10: nr=None
            if pos>=6 and ranges[i]<=ranges[ix[pos-6:pos+1]].min(): nr={'pos':pos,'high':hi[i],'low':lo[i]}
            if pos>=20 and ({'RH-01','RH-02'}&wanted):
                hist=ix[pos-20:pos]; prior_hi=hi[hist].max(); prior_lo=lo[hist].min()
                if 'RH-01' in wanted:
                    if cl[i]>prior_hi: events.append(_event('RH-01',i,1,atr[i],prior_hi))
                    if cl[i]<prior_lo: events.append(_event('RH-01',i,-1,atr[i],prior_lo))
                if 'RH-02' in wanted:
                    if lo[i]<prior_lo and cl[i]>prior_lo: events.append(_event('RH-02',i,1,atr[i],prior_lo))
                    if hi[i]>prior_hi and cl[i]<prior_hi: events.append(_event('RH-02',i,-1,atr[i],prior_hi))
            if np.isfinite(ph[i]):
                if 'PD-01' in wanted:
                    if cl[pi]<=ph[i] and cl[i]>ph[i]: events.append(_event('PD-01',i,1,atr[i],ph[i]))
                    if cl[pi]>=pl[i] and cl[i]<pl[i]: events.append(_event('PD-01',i,-1,atr[i],pl[i]))
                if 'PD-02' in wanted:
                    if lo[i]<pl[i] and cl[i]>pl[i]: events.append(_event('PD-02',i,1,atr[i],pl[i]))
                    if hi[i]>ph[i] and cl[i]<ph[i]: events.append(_event('PD-02',i,-1,atr[i],ph[i]))
    if not events: return pd.DataFrame(columns=['strategy_id','bar_index','side','direction','ATR_at_signal','reference_level','signal_time','instrument'])
    e=pd.DataFrame(events).drop_duplicates(['strategy_id','bar_index','side','reference_level']); e['signal_time']=e.bar_index.map(frame.close_time);e['instrument']=instrument
    return e.sort_values(['strategy_id','bar_index','side'],kind='mergesort').reset_index(drop=True)

def event_outcomes(frame,events):
    """Post-signal labels based on executable next open, restricted to its day."""
    if events.empty:return pd.DataFrame()
    op=frame.open.to_numpy(float);hi=frame.high.to_numpy(float);lo=frame.low.to_numpy(float);cl=frame.close.to_numpy(float); dates=frame.trading_date.to_numpy()
    rows=[]
    for e in events.itertuples():
        entry=e.bar_index+1
        if entry>=len(frame) or dates[entry]!=dates[e.bar_index]:continue
        base=op[entry]
        for h in (5,15,30,60):
            end=entry+h-1
            if end>=len(frame) or dates[end]!=dates[entry]:continue
            side=e.direction
            rows.append({'strategy_id':e.strategy_id,'instrument':e.instrument,'signal_time':e.signal_time,'entry_time':frame.open_time.iloc[entry],'horizon':h,
             'signed_move_atr':side*(cl[end]-base)/e.ATR_at_signal,'mfe_atr':((hi[entry:end+1].max()-base) if side==1 else (base-lo[entry:end+1].min()))/e.ATR_at_signal,
             'mae_atr':((base-lo[entry:end+1].min()) if side==1 else (hi[entry:end+1].max()-base))/e.ATR_at_signal})
    return pd.DataFrame(rows)

def default_configs():
    return [(f'STOP_{s}_TARGET_{t}',s,t,60) for s in (.5,1.) for t in (1.,1.5,2.)]+[(f'TIME_{h}',None,None,h) for h in (15,30,60)]

def simulate(frame,events,tick,configs=None,progress=False):
    """Next-open, same-day, gap-aware execution; friction expands each path threefold."""
    configs=configs or default_configs(); raw=[]; path_id=0
    op=frame.open.to_numpy(float);hi=frame.high.to_numpy(float);lo=frame.low.to_numpy(float);cl=frame.close.to_numpy(float);dates=frame.trading_date.to_numpy()
    open_times=frame.open_time.array; close_times=frame.close_time.array
    day_end=np.empty(len(frame),int)
    for _,ix in frame.groupby('trading_date',sort=False).indices.items():day_end[np.asarray(ix)]=max(ix)
    groups=list(events.groupby('strategy_id',sort=False)); total=len(groups)*len(configs); done=0; start=perf_counter()
    for strategy,es in groups:
      ordered=es.sort_values('bar_index')
      for name,stop_mult,target_mult,maxhold in configs:
        available=-1
        for e in ordered.itertuples():
            entry_i=e.bar_index+1
            if entry_i>=len(frame) or entry_i<=available or dates[entry_i]!=dates[e.bar_index]:continue
            entry=op[entry_i]; risk_price=stop_mult*e.ATR_at_signal if stop_mult is not None else np.nan; side=e.direction
            stop=entry-side*risk_price if stop_mult is not None else np.nan; target=entry+side*risk_price*target_mult if target_mult is not None else np.nan
            requested=entry_i+maxhold-1; exit_i=min(requested,day_end[entry_i]); reason='DAY_END' if exit_i<requested else 'TIME'; price=cl[exit_i]
            path=slice(entry_i,exit_i+1); path_hi=hi[path];path_lo=lo[path]
            if stop_mult is not None:
                path_op=op[path]
                gap_s=path_op<=stop if side==1 else path_op>=stop;gap_t=path_op>=target if side==1 else path_op<=target
                hit_s=path_lo<=stop if side==1 else path_hi>=stop;hit_t=path_hi>=target if side==1 else path_lo<=target
                reached=gap_s|gap_t|hit_s|hit_t
                if reached.any():
                    off=int(np.flatnonzero(reached)[0]);exit_i=entry_i+off
                    # Explicit deterministic within-bar priority.
                    if gap_s[off]:price=op[exit_i];reason='STOP_GAP'
                    elif gap_t[off]:price=target;reason='TARGET_GAP'
                    elif hit_s[off]:price=stop;reason='STOP_FIRST_TIE' if hit_t[off] else 'STOP'
                    else:price=target;reason='TARGET'
            held_hi=hi[entry_i:exit_i+1];held_lo=lo[entry_i:exit_i+1]
            mfe=max(0.,(held_hi.max()-entry) if side==1 else (entry-held_lo.min()));mae=max(0.,(entry-held_lo.min()) if side==1 else (held_hi.max()-entry))
            available=exit_i;path_id+=1
            for friction,ticks in (('GROSS',0),('BASE',1),('STRESS',2)):
                ae=entry+side*ticks*tick;ax=price-side*ticks*tick;gross=side*(price-entry);net=side*(ax-ae);pnl_atr=net/e.ATR_at_signal
                raw.append({'trade_path_id':path_id,'strategy_id':strategy,'instrument':e.instrument,'exit_configuration':name,'friction_scenario':friction,
                 'signal_time':e.signal_time,'entry_time':open_times[entry_i],'entry_price_raw':entry,'entry_price_adjusted':ae,'side':e.side,
                 'ATR_at_entry':e.ATR_at_signal,'reference_level':e.reference_level,'risk_price':risk_price,'stop_price':stop,'target_price':target,
                 'exit_time':close_times[exit_i],'exit_price_raw':price,'exit_price_adjusted':ax,'exit_reason':reason,'bars_held':exit_i-entry_i+1,
                 'gross_pnl_price':gross,'net_pnl_price':net,'pnl_atr':pnl_atr,'pnl_R':net/risk_price if np.isfinite(risk_price) else np.nan,'MFE':mfe,'MAE':mae})
        done+=1
        if progress:print(f'[{done}/{total}] {strategy} {name}: signals={len(ordered)} paths={path_id} elapsed={perf_counter()-start:.1f}s',flush=True)
    return pd.DataFrame(raw)

def _unit_metrics(x):
    v=x.dropna().to_numpy(float); wins=v[v>0];losses=v[v<0]
    if not len(v):return dict(trades=0,profit_factor=np.nan,expectancy=np.nan,max_drawdown=np.nan,net_result=np.nan)
    eq=v.cumsum();dd=eq-np.maximum.accumulate(np.r_[0,eq])[1:]
    return {'profit_factor':wins.sum()/-losses.sum() if len(losses) else np.inf,'expectancy':v.mean(),'max_drawdown':-dd.min(initial=0),'net_result':v.sum()}

def metrics(ledger):
    rows=[];keys=['strategy_id','instrument','exit_configuration','friction_scenario']
    for key,g in ledger.groupby(keys,sort=False):
        a=_unit_metrics(g.pnl_atr);r=_unit_metrics(g.pnl_R); net=g.net_pnl_price
        atr_values=g.pnl_atr.to_numpy(float); wins=net[net>0]; losses=net[net<0]
        streak=longest=current=0
        for losing in net.lt(0).to_numpy():
            current=current+1 if losing else 0;longest=max(longest,current)
        atr_sd=np.std(atr_values,ddof=1) if len(atr_values)>1 else np.nan
        downside=atr_values[atr_values<0];downside_sd=np.std(downside,ddof=1) if len(downside)>1 else np.nan
        row=dict(zip(keys,key))|{'trades':len(g),'wins':int((net>0).sum()),'losses':int((net<0).sum()),'win_rate':float((net>0).mean()),
          'gross_pnl_price':g.gross_pnl_price.sum(),'net_pnl_price':net.sum(),'average_trade_price':net.mean(),'median_trade_price':net.median(),
          'average_win_price':wins.mean() if len(wins) else np.nan,'average_loss_price':losses.mean() if len(losses) else np.nan,
          'payoff_ratio_price':wins.mean()/-losses.mean() if len(wins) and len(losses) else np.nan,
          'profit_factor_ATR':a['profit_factor'],'expectancy_ATR':a['expectancy'],'max_drawdown_ATR':a['max_drawdown'],'net_result_ATR':a['net_result'],
          'profit_factor_R':r['profit_factor'],'expectancy_R':r['expectancy'],'max_drawdown_R':r['max_drawdown'],'net_result_R':r['net_result'],
          'recovery_factor_ATR':a['net_result']/a['max_drawdown'] if a['max_drawdown'] else np.nan,
          'sharpe_ATR':a['expectancy']/atr_sd*np.sqrt(len(g)) if len(g)>=30 and atr_sd else np.nan,
          'sortino_ATR':a['expectancy']/downside_sd*np.sqrt(len(g)) if len(g)>=30 and downside_sd else np.nan,
          'max_consecutive_losses':longest,'average_holding_bars':g.bars_held.mean(),'median_holding_bars':g.bars_held.median(),'sample_flag':'VERY_LOW_SAMPLE' if len(g)<20 else 'LOW_SAMPLE' if len(g)<50 else 'MODERATE_SAMPLE' if len(g)<100 else 'BETTER_SAMPLE'}
        rows.append(row)
    return pd.DataFrame(rows)

def _hash_info(path,rows=None):
    h=sha256();
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return {'rows':rows,'bytes':path.stat().st_size,'sha256':h.hexdigest()}

def _audit_sample(ledger):
    parts=[ledger.sort_values('trade_path_id').groupby('strategy_id').head(2),ledger[ledger.friction_scenario.eq('BASE')].head(10),ledger[ledger.exit_reason.eq('DAY_END')].head(10)]
    return pd.concat(parts).drop_duplicates().sort_values(['trade_path_id','friction_scenario']).head(100)

def _report(manifest,summary):
    base=summary[summary.friction_scenario.eq('BASE')];stop=base[base.exit_configuration.str.startswith('STOP')].sort_values('expectancy_R',ascending=False).head(15)
    time=base[base.exit_configuration.str.startswith('TIME')].sort_values('expectancy_ATR',ascending=False).head(15);common=base.sort_values('expectancy_ATR',ascending=False).head(15)
    fam=[]
    for (strategy,fr),g in summary.groupby(['strategy_id','friction_scenario']):fam.append(g.sort_values('expectancy_ATR',ascending=False).head(1))
    robust=pd.concat(fam).sort_values(['strategy_id','friction_scenario'])
    return '# Phase 6B corrected real known-strategy backtest\n\n```json\n'+json.dumps(manifest,indent=2,default=str)+'\n```\n\n## Stop/target BASE leaderboard (R)\n\n```csv\n'+stop.to_csv(index=False)+'```\n\n## Time-exit BASE leaderboard (ATR)\n\n```csv\n'+time.to_csv(index=False)+'```\n\n## Common BASE leaderboard (ATR)\n\n```csv\n'+common.to_csv(index=False)+'```\n\n## Best cell by family and friction (ATR)\n\n```csv\n'+robust.to_csv(index=False)+'```\n'

def smoke(data_root='/workspace/market-pattern-data'):
    start=perf_counter();f,p=load_discovery(data_root,'CNYRUBF');days=pd.unique(f.trading_date)[:5];f=f[f.trading_date.isin(days)].reset_index(drop=True)
    e=generate_signals(f,'CNYRUBF',('RL-02','RH-02','PD-01'));configs=[('STOP_1.0_TARGET_1.5',1.,1.5,60),('TIME_15',None,None,15)]
    ledger=simulate(f,e,.001,configs);elapsed=perf_counter()-start;paths=ledger.trade_path_id.nunique() if len(ledger) else 0
    result={'rows':len(f),'date_range':[str(f.trading_date.min()),str(f.trading_date.max())],'signals':e.strategy_id.value_counts().to_dict(),'actual_trade_paths':paths,'ledger_rows':len(ledger),
      'friction_rows':ledger.friction_scenario.value_counts().to_dict(),'elapsed_seconds':elapsed,'rows_per_second':len(f)/elapsed,'projected_full_seconds':elapsed*154356/len(f),
      'peak_rss_kb':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'first_5_trades':ledger.head().to_dict('records')}
    print('REAL SMOKE TEST\n'+json.dumps(result,indent=2,default=str),flush=True);return result

def run(data_root,output,context=None):
    """Run V3, optionally restricted by a V3.5 execution context.

    Omitting ``context`` retains the historical two-argument M1 execution over
    both instruments.
    """
    context=context or ExecutionContext()
    started=perf_counter();output=Path(output);output.mkdir(parents=True,exist_ok=True);frames={};events=[];ledgers=[];provenance=[]
    for inst in context.instruments:
        f,p=load_discovery(data_root,inst,context.timeframe);frames[inst]=f;provenance+=p;print(f'Loaded {inst} {context.timeframe}: {len(f):,} rows',flush=True)
        e=generate_signals(f,inst);events.append(e);print(f'Generated {inst}: {len(e):,} signals',flush=True)
        ledgers.append(simulate(f,e,SPECS[inst][0],progress=True))
    events=pd.concat(events,ignore_index=True);ledger=pd.concat(ledgers,ignore_index=True);summary=metrics(ledger);outcomes=pd.concat([event_outcomes(frames[i],events[events.instrument.eq(i)]) for i in frames],ignore_index=True)
    monthly=ledger.assign(month=ledger.entry_time.dt.strftime('%Y-%m')).groupby(['strategy_id','instrument','exit_configuration','friction_scenario','month']).agg(trades=('net_pnl_price','size'),net_result_price=('net_pnl_price','sum'),net_result_ATR=('pnl_atr','sum'),expectancy_ATR=('pnl_atr','mean'),net_result_R=('pnl_R','sum'),expectancy_R=('pnl_R','mean')).reset_index()
    surface=summary[summary.exit_configuration.str.startswith('STOP')].copy();audit=_audit_sample(ledger)
    outputs=((summary,'strategy_summary.csv'),(surface,'strategy_parameter_surface.csv'),(monthly,'monthly_summary.csv'),(audit,'trade_audit_sample.csv'),(outcomes,'event_outcomes.csv'),(ledger,'trade_ledger.csv'))
    for df,name in outputs:df.to_csv(output/name,index=False)
    signal_counts=events.groupby(['strategy_id','instrument']).size().rename('signals').reset_index().to_dict('records');runtime=perf_counter()-started
    manifest={'status':'PARTIAL' if SKIPPED else 'PASS','timeframe':context.timeframe,'instruments':list(context.instruments),'window':{'start':START.isoformat(),'end_exclusive':END.isoformat()},'rows':{i:len(f) for i,f in frames.items()},'dates':{i:[f.open_time.min().isoformat(),f.close_time.max().isoformat()] for i,f in frames.items()},
      'strategies_executed':list(STRATEGIES),'skipped':SKIPPED,'raw_signal_counts':signal_counts,'raw_signals':len(events),'actual_trade_paths':int(ledger.groupby('instrument').trade_path_id.nunique().sum()),'ledger_rows_including_friction':len(ledger),
      'atr_source':ATR_SOURCE,'atr_definition':ATR_DEFINITION,'atr_reset_policy':'continuous per instrument; no day reset','trading_date_source':TRADING_DATE_SOURCE,
      'round_level_semantic_source':'Phase 2 Decimal grid semantics; actual touched/crossed grid level','tie_policy':'stop first when intrabar order unknown','gap_policy':'adverse stop gaps fill at open; target gaps fill at target',
      'day_boundary_policy':'entry and complete holding path restricted to signal trading_date; DAY_END close','event_outcome_reference_price':'open of t+1; complete same-day horizons only','source_modified':False,'runtime_seconds':runtime,'provenance':provenance,
      'regenerate_command':'PYTHONPATH=src python scripts/run_phase6b.py','outputs':{}}
    for df,name in outputs:manifest['outputs'][name]=_hash_info(output/name,len(df))
    (output/'run_manifest.json').write_text(json.dumps(manifest,indent=2,default=str)+'\n');(output/'phase6b_report.md').write_text(_report(manifest,summary))
    print(f'Completed in {runtime:.1f}s: signals={len(events):,} paths={manifest["actual_trade_paths"]:,} ledger={len(ledger):,}',flush=True);return manifest
