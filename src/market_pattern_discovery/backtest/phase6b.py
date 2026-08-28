"""Corrected causal Phase 6B known-strategy benchmark."""
from __future__ import annotations
from pathlib import Path
from hashlib import sha256
import json, math, time
import numpy as np
import pandas as pd
from market_pattern_discovery.data.finam import stitch_finam
from market_pattern_discovery.features.core import canonical_trading_date

START=pd.Timestamp('2026-01-05',tz='Europe/Moscow'); END=pd.Timestamp('2026-05-16',tz='Europe/Moscow')
SPECS={'CNYRUBF':(.001,.05,'CNY'),'USDRUBF':(.01,.10,'Si')}
STRATEGIES=('RL-01','RL-02','RL-03','RL-04','MOM-01','MOM-02','NR-01','RH-01','RH-02','PD-01','PD-02')
SKIPPED={'EH-01':'No authoritative causal EH/EL reference-price primitive exists.', 'EH-02':'No authoritative causal EH/EL reference-price primitive exists.'}
CONFIGS=[(f'STOP_{s}_TARGET_{t}',s,t,60) for s in(.5,1.) for t in(1.,1.5,2.)]+[(f'TIME_{h}',None,None,h) for h in(15,30,60)]

def wilder_atr14(frame):
    """Standard continuous causal Wilder ATR(14); never resets at a day boundary."""
    h=frame.high.to_numpy(float); l=frame.low.to_numpy(float); c=frame.close.to_numpy(float)
    prev=np.r_[np.nan,c[:-1]]
    tr=np.maximum(h-l,np.maximum(np.abs(h-prev),np.abs(l-prev))); tr[0]=h[0]-l[0]
    out=np.full(len(frame),np.nan)
    if len(frame)>=14:
        out[13]=tr[:14].mean()
        for i in range(14,len(frame)): out[i]=(out[i-1]*13+tr[i])/14
    return pd.Series(out,index=frame.index,name='atr14')

def prepare_frame(frame):
    f=frame.copy().reset_index(drop=True)
    f['trading_date']=canonical_trading_date(f.open_time)
    f['atr14']=wilder_atr14(f).to_numpy()
    return f

def load_discovery(data_root,instrument):
    tick,_,folder=SPECS[instrument]; paths=sorted((Path(data_root)/'2026'/folder).glob('*_2026_Q[12]_M1.csv'))
    if not paths or any('2025' in str(x) for x in paths): raise ValueError('only named 2026 discovery sources are permitted')
    result=stitch_finam(paths,instrument,'M1'); f=result.frame
    f=f.loc[(f.open_time>=START)&(f.close_time<END)].copy()
    if f.empty or f.open_time.dt.year.ne(2026).any() or f.close_time.max()>=END: raise ValueError('discovery boundary violation')
    f=prepare_frame(f); f['tick']=tick
    return f,result.provenance

def _event(strategy,i,side,atr,ref=np.nan,**audit):
    return {'strategy_id':strategy,'bar_index':i,'side':'LONG' if side==1 else 'SHORT','direction':side,'ATR_at_signal':atr,'reference_level':ref,**audit}

def _grid_between(a,b,step):
    """All exact grid levels in inclusive price interval, as ascending floats."""
    lo=math.ceil((min(a,b)-1e-10)/step); hi=math.floor((max(a,b)+1e-10)/step)
    return [round(k*step,10) for k in range(lo,hi+1)]

def generate_signals(frame,instrument,strategies=None):
    """Signals use only each closed row and its already-closed prefix."""
    wanted=set(strategies or STRATEGIES); tick,step,_=SPECS[instrument]; events=[]
    o=frame.open.to_numpy(float); h=frame.high.to_numpy(float); l=frame.low.to_numpy(float); c=frame.close.to_numpy(float); atr=frame.atr14.to_numpy(float)
    dates=frame.trading_date.to_numpy(); times=frame.close_time.to_numpy()
    daily=frame.groupby('trading_date',sort=False).agg(high=('high','max'),low=('low','min')).shift(1)
    ph=frame.trading_date.map(daily.high).to_numpy(float); pl=frame.trading_date.map(daily.low).to_numpy(float)
    for _,day in frame.groupby('trading_date',sort=False):
        ids=day.index.to_numpy(); nr=None; retests=[]
        for pos,i in enumerate(ids):
            if pos==0 or not np.isfinite(atr[i]): continue
            p=ids[pos-1]; pp=ids[pos-2] if pos>=2 else None
            # Actual path-bound level candidates, not nearest-to-final-close.
            touched=_grid_between(l[i]-tick,h[i]+tick,step)
            if 'RL-01' in wanted:
                longs=[L for L in touched if l[i]<=L+tick and c[i]>L and c[p]>=L]
                shorts=[L for L in touched if h[i]>=L-tick and c[i]<L and c[p]<=L]
                if longs: events.append(_event('RL-01',i,1,atr[i],max(longs)))
                if shorts: events.append(_event('RL-01',i,-1,atr[i],min(shorts)))
            long_cross=[L for L in _grid_between(c[p],c[i],step) if c[p]<=L and c[i]>L+tick]
            short_cross=[L for L in _grid_between(c[p],c[i],step) if c[p]>=L and c[i]<L-tick]
            if long_cross:
                L=max(long_cross)
                if 'RL-02' in wanted: events.append(_event('RL-02',i,1,atr[i],L))
                if 'RL-04' in wanted: retests.append((1,L,pos))
            if short_cross:
                L=min(short_cross)
                if 'RL-02' in wanted: events.append(_event('RL-02',i,-1,atr[i],L))
                if 'RL-04' in wanted: retests.append((-1,L,pos))
            if 'RL-03' in wanted:
                # Bind to an actually penetrated level in current/previous candle.
                lc=[L for L in _grid_between(l[i],c[p],step) if l[i]<=L-tick and c[p]>=L and c[i]>L]
                sc=[L for L in _grid_between(c[p],h[i],step) if h[i]>=L+tick and c[p]<=L and c[i]<L]
                if pp is not None:
                    lc += [L for L in _grid_between(l[p],c[pp],step) if l[p]<=L-tick and c[pp]>=L and c[i]>L]
                    sc += [L for L in _grid_between(c[pp],h[p],step) if h[p]>=L+tick and c[pp]<=L and c[i]<L]
                if lc: events.append(_event('RL-03',i,1,atr[i],max(lc),return_window=2))
                if sc: events.append(_event('RL-03',i,-1,atr[i],min(sc),return_window=2))
            keep=[]
            for side,L,bpos in retests:
                age=pos-bpos; hit=l[i]<=L+tick and h[i]>=L-tick and ((side==1 and c[i]>L) or(side==-1 and c[i]<L))
                if 1<=age<=5 and hit: events.append(_event('RL-04',i,side,atr[i],L,retest_age=age))
                elif age<=5: keep.append((side,L,bpos))
            retests=keep
            if 'MOM-01' in wanted and pos>=5:
                m=(c[i]-c[ids[pos-5]])/atr[i]
                if abs(m)>=.5: events.append(_event('MOM-01',i,1 if m>0 else -1,atr[i],momentum=m))
            if 'MOM-02' in wanted and pos>=10:
                m=(c[i]-c[ids[pos-10]])/atr[i]
                if abs(m)>=.75: events.append(_event('MOM-02',i,1 if m>0 else -1,atr[i],momentum=m))
            if 'NR-01' in wanted:
                if nr:
                    age=pos-nr[0]
                    if 1<=age<=10 and c[i]>nr[1]: events.append(_event('NR-01',i,1,atr[i],nr[1],nr_age=age)); nr=None
                    elif 1<=age<=10 and c[i]<nr[2]: events.append(_event('NR-01',i,-1,atr[i],nr[2],nr_age=age)); nr=None
                    elif age>10: nr=None
                if pos>=6 and h[i]-l[i]<=np.min(h[ids[pos-6:pos+1]]-l[ids[pos-6:pos+1]]): nr=(pos,h[i],l[i])
            if pos>=20 and ({'RH-01','RH-02'}&wanted):
                prior=ids[pos-20:pos]; hi=h[prior].max(); lo=l[prior].min()
                if 'RH-01' in wanted:
                    if c[i]>hi: events.append(_event('RH-01',i,1,atr[i],hi))
                    if c[i]<lo: events.append(_event('RH-01',i,-1,atr[i],lo))
                if 'RH-02' in wanted:
                    if l[i]<lo and c[i]>lo: events.append(_event('RH-02',i,1,atr[i],lo))
                    if h[i]>hi and c[i]<hi: events.append(_event('RH-02',i,-1,atr[i],hi))
            if np.isfinite(ph[i]):
                if 'PD-01' in wanted:
                    if c[p]<=ph[i] and c[i]>ph[i]: events.append(_event('PD-01',i,1,atr[i],ph[i]))
                    if c[p]>=pl[i] and c[i]<pl[i]: events.append(_event('PD-01',i,-1,atr[i],pl[i]))
                if 'PD-02' in wanted:
                    if l[i]<pl[i] and c[i]>pl[i]: events.append(_event('PD-02',i,1,atr[i],pl[i]))
                    if h[i]>ph[i] and c[i]<ph[i]: events.append(_event('PD-02',i,-1,atr[i],ph[i]))
    if not events: return pd.DataFrame(columns=['strategy_id','bar_index','side','direction','ATR_at_signal','reference_level','signal_time','instrument'])
    e=pd.DataFrame(events).drop_duplicates(['strategy_id','bar_index','side','reference_level'])
    e['signal_time']=pd.to_datetime(e.bar_index.map(frame.close_time)); e['instrument']=instrument
    return e.sort_values(['strategy_id','bar_index','side'],kind='mergesort').reset_index(drop=True)

def event_outcomes(frame,events):
    rows=[]; O=frame.open.to_numpy(float); H=frame.high.to_numpy(float); L=frame.low.to_numpy(float); C=frame.close.to_numpy(float); D=frame.trading_date.to_numpy()
    for e in events.itertuples():
        entry=e.bar_index+1
        if entry>=len(frame) or D[entry]!=D[e.bar_index]: continue
        base=O[entry]
        for horizon in (5,15,30,60):
            end=entry+horizon-1
            if end>=len(frame) or D[end]!=D[entry]: continue
            path=slice(entry,end+1); side=e.direction; atr=e.ATR_at_signal
            rows.append({'strategy_id':e.strategy_id,'instrument':e.instrument,'signal_time':e.signal_time,'entry_time':frame.open_time.iloc[entry],'horizon':horizon,
              'signed_move_atr':side*(C[end]-base)/atr,'mfe_atr':((H[path].max()-base) if side==1 else(base-L[path].min()))/atr,
              'mae_atr':((base-L[path].min()) if side==1 else(H[path].max()-base))/atr})
    return pd.DataFrame(rows)

def simulate(frame,events,tick,configs=None,progress=None):
    configs=configs or CONFIGS; paths=[]
    O=frame.open.to_numpy(float); H=frame.high.to_numpy(float); L=frame.low.to_numpy(float); C=frame.close.to_numpy(float); D=frame.trading_date.to_numpy()
    open_times=frame.open_time.to_numpy(); close_times=frame.close_time.to_numpy()
    day_end=np.empty(len(frame),int)
    for _,g in frame.groupby('trading_date',sort=False): day_end[g.index.to_numpy()]=g.index[-1]
    groups=list(events.groupby('strategy_id',sort=False)); total=len(groups)*len(configs); done=0
    for strategy,es in groups:
      # Tuples avoid pandas attribute/indexing work in the hot path.
      ordered=[(int(x.bar_index),int(x.direction),float(x.ATR_at_signal),float(x.reference_level),x.signal_time,x.side,x.instrument) for x in es.sort_values('bar_index').itertuples()]
      for name,stop_mult,target_mult,maxhold in configs:
        done+=1; available=-1
        for signal_i,side,atr,ref,signal_time,side_name,instrument in ordered:
            entry_i=signal_i+1
            if entry_i>=len(frame) or entry_i<=available or D[entry_i]!=D[signal_i]: continue
            entry=O[entry_i]; risk=stop_mult*atr if stop_mult is not None else np.nan
            stop=entry-side*risk if stop_mult is not None else np.nan; target=entry+side*risk*target_mult if target_mult is not None else np.nan
            requested=entry_i+maxhold-1; final=min(requested,day_end[entry_i]); exit_i=final; price=C[final]; reason='DAY_END' if final<requested else 'TIME'
            mfe=mae=0.
            for j in range(entry_i,final+1):
                mfe=max(mfe,H[j]-entry if side==1 else entry-L[j]); mae=max(mae,entry-L[j] if side==1 else H[j]-entry)
                if stop_mult is None: continue
                gap_stop=O[j]<=stop if side==1 else O[j]>=stop; gap_target=O[j]>=target if side==1 else O[j]<=target
                if gap_stop: exit_i=j; price=O[j]; reason='STOP_GAP'; break
                if gap_target: exit_i=j; price=target; reason='TARGET_GAP'; break
                hit_s=L[j]<=stop if side==1 else H[j]>=stop; hit_t=H[j]>=target if side==1 else L[j]<=target
                if hit_s: exit_i=j; price=stop; reason='STOP_FIRST_TIE' if hit_t else 'STOP'; break
                if hit_t: exit_i=j; price=target; reason='TARGET'; break
            available=exit_i; gross=side*(price-entry)
            paths.append({'trade_path_id':f'{strategy}:{name}:{instrument}:{signal_i}','strategy_id':strategy,'instrument':instrument,'exit_configuration':name,
              'signal_time':signal_time,'entry_time':open_times[entry_i],'entry_price_raw':entry,'side':side_name,'direction':side,'ATR_at_entry':atr,'reference_level':ref,
              'risk_price':risk,'stop_price':stop,'target_price':target,'exit_time':close_times[exit_i],'exit_price_raw':price,'exit_reason':reason,'bars_held':exit_i-entry_i+1,
              'gross_pnl_price':gross,'MFE':mfe,'MAE':mae})
        if progress: progress(done,total,strategy,name,len(paths)*3)
    base=pd.DataFrame(paths)
    if base.empty:return base
    # Friction scenarios share the identical path and are expanded vectorially.
    expanded=pd.concat([base.assign(friction_scenario=name,friction_ticks=ticks) for name,ticks in (('GROSS',0),('BASE',1),('STRESS',2))],ignore_index=True)
    side=expanded.direction.to_numpy(); ticks=expanded.friction_ticks.to_numpy()
    expanded['entry_price_adjusted']=expanded.entry_price_raw+side*ticks*tick
    expanded['exit_price_adjusted']=expanded.exit_price_raw-side*ticks*tick
    expanded['net_pnl_price']=side*(expanded.exit_price_adjusted-expanded.entry_price_adjusted)
    expanded['pnl_atr']=expanded.net_pnl_price/expanded.ATR_at_entry
    expanded['pnl_R']=expanded.net_pnl_price/expanded.risk_price
    return expanded.drop(columns=['direction','friction_ticks'])

def _stats(x):
    x=np.asarray(x,float); x=x[np.isfinite(x)]; n=len(x)
    if not n:return dict(pf=np.nan,exp=np.nan,total=np.nan,dd=np.nan)
    win=x[x>0].sum(); loss=-x[x<0].sum(); eq=x.cumsum(); peak=np.maximum.accumulate(np.r_[0,eq])[1:]
    return dict(pf=win/loss if loss else np.inf,exp=x.mean(),total=x.sum(),dd=float(np.max(peak-eq,initial=0)))

def metrics(ledger):
    rows=[]; keys=['strategy_id','instrument','exit_configuration','friction_scenario']
    for key,g in ledger.groupby(keys,sort=False):
        a=_stats(g.pnl_atr); r=_stats(g.pnl_R); n=len(g); net=g.net_pnl_price.to_numpy(); losses=cur=maxloss=0
        for v in net: cur=cur+1 if v<0 else 0; maxloss=max(maxloss,cur)
        rows.append(dict(zip(keys,key))|{'trades':n,'wins':int((net>0).sum()),'losses':int((net<0).sum()),'win_rate':float((net>0).mean()),
          'gross_pnl_price':g.gross_pnl_price.sum(),'net_pnl_price':net.sum(),'profit_factor_ATR':a['pf'],'expectancy_ATR':a['exp'],'max_drawdown_ATR':a['dd'],'net_result_ATR':a['total'],
          'profit_factor_R':r['pf'],'expectancy_R':r['exp'],'max_drawdown_R':r['dd'],'net_result_R':r['total'],'average_holding_bars':g.bars_held.mean(),
          'median_holding_bars':g.bars_held.median(),'max_consecutive_losses':maxloss,'sample_flag':'VERY_LOW_SAMPLE' if n<20 else 'LOW_SAMPLE' if n<50 else 'MODERATE_SAMPLE' if n<100 else 'BETTER_SAMPLE'})
    return pd.DataFrame(rows)

def _file_meta(path,rows=None):
    p=Path(path); return {'rows':rows,'bytes':p.stat().st_size,'sha256':sha256(p.read_bytes()).hexdigest()}

def _table(df,cols,n=10): return df.loc[:,cols].head(n).to_csv(index=False)

def write_report(output,manifest,summary):
    base=summary[summary.friction_scenario.eq('BASE')]
    stop=base[base.exit_configuration.str.startswith('STOP')].sort_values(['expectancy_R','profit_factor_R'],ascending=False)
    timed=base[base.exit_configuration.str.startswith('TIME')].sort_values(['expectancy_ATR','profit_factor_ATR'],ascending=False)
    common=base.sort_values(['expectancy_ATR','profit_factor_ATR'],ascending=False)
    stopcols=['strategy_id','instrument','exit_configuration','trades','win_rate','profit_factor_R','expectancy_R','max_drawdown_R','net_result_R']
    timecols=['strategy_id','instrument','exit_configuration','trades','win_rate','profit_factor_ATR','expectancy_ATR','max_drawdown_ATR','net_result_ATR']
    text='# Phase 6B corrected real known-strategy backtest\n\n```json\n'+json.dumps(manifest,indent=2)+'\n```\n\n'
    text+='## STOP/TARGET BASE leaderboard\n\n```csv\n'+_table(stop,stopcols)+'```\n\n## TIME BASE leaderboard\n\n```csv\n'+_table(timed,timecols)+'```\n\n## COMMON BASE leaderboard (ATR units)\n\n```csv\n'+_table(common,timecols)+'```\n'
    best=(summary.sort_values(['friction_scenario','strategy_id','expectancy_ATR'],ascending=[True,True,False])
          .groupby(['strategy_id','friction_scenario'],sort=True).head(1)
          [['strategy_id','friction_scenario','instrument','exit_configuration','trades','profit_factor_ATR','expectancy_ATR','max_drawdown_ATR','net_result_ATR']])
    text+='\n## Best cell per family and friction scenario (ATR units)\n\n```csv\n'+best.to_csv(index=False)+'```\n'
    (Path(output)/'phase6b_report.md').write_text(text)

def run(data_root,output,*,smoke=False):
    started=time.perf_counter(); output=Path(output); output.mkdir(parents=True,exist_ok=True); frames={}; evs=[]; ledgers=[]; provenance=[]
    instruments=('CNYRUBF',) if smoke else tuple(SPECS); wanted=('RL-02','RH-02','PD-01') if smoke else STRATEGIES
    for inst in instruments:
        f,p=load_discovery(data_root,inst)
        if smoke:
            keep=set(pd.unique(f.trading_date)[:5]); f=f[f.trading_date.isin(keep)].reset_index(drop=True)
        frames[inst]=f; provenance+=p; print(f'Loaded {inst}: {len(f):,} rows',flush=True)
        e=generate_signals(f,inst,wanted); evs.append(e); print('signals:',e.strategy_id.value_counts().to_dict(),flush=True)
        cfg=[CONFIGS[0],CONFIGS[-2]] if smoke else CONFIGS
        def progress(done,total,s,n,rows):
            if not smoke: print(f'[{done}/{total}] {s} {inst} {n}: ledger rows={rows:,}',flush=True)
        ledgers.append(simulate(f,e,SPECS[inst][0],cfg,progress))
    events=pd.concat(evs,ignore_index=True); ledger=pd.concat(ledgers,ignore_index=True); summary=metrics(ledger)
    outcomes=pd.concat([event_outcomes(frames[i],events[events.instrument==i]) for i in frames],ignore_index=True)
    monthly=(ledger.assign(month=ledger.entry_time.dt.strftime('%Y-%m')).groupby(['strategy_id','instrument','exit_configuration','friction_scenario','month']).agg(trades=('pnl_atr','size'),net_result_ATR=('pnl_atr','sum'),expectancy_ATR=('pnl_atr','mean'),net_result_R=('pnl_R','sum'),expectancy_R=('pnl_R','mean')).reset_index())
    surface=summary[summary.exit_configuration.str.startswith('STOP')].copy()
    files=((summary,'strategy_summary.csv'),(surface,'strategy_parameter_surface.csv'),(monthly,'monthly_summary.csv'),(outcomes,'event_outcomes.csv'),(ledger,'trade_ledger.csv'))
    for df,name in files: df.to_csv(output/name,index=False)
    # deterministic diverse compact sample
    sample=pd.concat([ledger.groupby(['strategy_id','exit_configuration','friction_scenario'],sort=True).head(1),ledger[ledger.exit_reason.eq('DAY_END')].head(20)]).drop_duplicates().sort_values(['strategy_id','entry_time','exit_configuration','friction_scenario']).head(250)
    sample.to_csv(output/'trade_audit_sample.csv',index=False)
    runtime=time.perf_counter()-started
    counts=events.groupby(['strategy_id','instrument']).size(); actual=ledger.trade_path_id.nunique()
    manifest={'status':'SMOKE' if smoke else('PARTIAL' if SKIPPED else 'PASS'),'window':{'start':START.isoformat(),'end_exclusive':END.isoformat()},
      'rows':{i:len(f) for i,f in frames.items()},'dates':{i:[f.open_time.min().isoformat(),f.close_time.max().isoformat()] for i,f in frames.items()},'strategies_executed':list(wanted),'skipped':SKIPPED if not smoke else {},
      'raw_signals':len(events),'raw_signal_counts':{f'{a}/{b}':int(v) for(a,b),v in counts.items()},'actual_trade_paths':actual,'ledger_rows':len(ledger),'provenance':provenance,
      'atr_source':'phase6b fallback (no authoritative ATR14 exists)','atr_definition':'Wilder ATR(14), causal TR including prior available close','atr_reset_policy':'continuous_per_instrument_no_day_reset',
      'trading_date_source':'market_pattern_discovery.features.core.canonical_trading_date','round_level_semantic_source':'Phase 2 instrument grid; actual touched/crossed grid level','tie_policy':'gap checks then stop first when intrabar order unknown',
      'gap_policy':'adverse stop gap fills at open; favorable target gap capped at target','day_boundary_policy':'entry and complete path confined to signal trading_date; DAY_END close','event_outcome_reference_price':'next M1 open; complete same-day horizons only',
      'runtime_seconds':runtime,'source_modified':False,'regenerate_command':'PYTHONPATH=src python scripts/run_phase6b.py'}
    (output/'run_manifest.json').write_text(json.dumps(manifest,indent=2,default=str)+'\n')
    write_report(output,manifest,summary)
    # hashes after report/manifest; manifest self-hash intentionally excluded
    output_meta={}
    for df,name in files: output_meta[name]=_file_meta(output/name,len(df))
    # The report embeds this manifest, so hashing it here would create a
    # circular, necessarily stale self-reference. Regenerable large outputs
    # and every compact CSV are hashed below; manifest/report are committed.
    output_meta['trade_audit_sample.csv']=_file_meta(output/'trade_audit_sample.csv',len(sample))
    manifest['output_files']=output_meta; (output/'run_manifest.json').write_text(json.dumps(manifest,indent=2,default=str)+'\n'); write_report(output,manifest,summary)
    print(f'actual paths={actual:,}; ledger rows={len(ledger):,}; elapsed={runtime:.2f}s',flush=True)
    return manifest
