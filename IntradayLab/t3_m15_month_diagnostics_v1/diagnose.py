"""Unchanged #500 replay plus fixed descriptive diagnostics; no new trading rule."""
import argparse, csv, hashlib, json, math, sys
from pathlib import Path
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
REPO=HERE.parent.parent
REF=HERE.parent/'t3_m15_t1_s1_v1'
sys.dont_write_bytecode=True
sys.path.insert(0,str(REF))
import engine as E
import independent as C

BASE='8c40950726446ebccb1ad80b8f129558470d9c11'
SYMBOLS=list(C.SYMBOLS)
MONTHS=C.CALENDAR
LABEL=C.LABEL
FEATURES=['H1ADX','dADX','H1ATRRatio','dATRRatio','signed_slope_ATR','volatility_pct','breakout_ATR','close_location','hour']

def dump(path,x):C.write_json(path,x)
def write(path,rows):C.write_csv(path,rows)
def reference(name):
    return pd.read_csv(REF/'results'/name)

def extended(raw):
    f=E.features(raw)
    g=raw.copy();g['Day']=g.index.normalize();g['Ordinal']=g.groupby('Day').cumcount()//4
    g['First']=g.index;g['Last']=g.index;g['Count']=1
    h=g.groupby(['Day','Ordinal']).agg(Open=('Open','first'),High=('High','max'),Low=('Low','min'),Close=('Close','last'),First=('First','first'),Last=('Last','last'),Count=('Count','sum'))
    h=h[(h.Count==4)&((h.Last-h.First)==pd.Timedelta(minutes=45))].set_index('Last')
    prev=h.Close.shift()
    tr=pd.concat([h.High-h.Low,(h.High-prev).abs(),(h.Low-prev).abs()],axis=1).max(axis=1)
    h['H1ATR']=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    h['H1EMA']=h.Close.ewm(span=75,adjust=False,min_periods=75).mean()
    h['H1Close']=h.Close
    h['efficiency5']=(h.Close-h.Close.shift(5)).abs()/h.Close.diff().abs().rolling(5).sum().replace(0,np.nan)
    for k in ['H1ATR','H1EMA','H1Close','efficiency5']:f[k]=h[k].reindex(f.index,method='ffill')
    f['dADX']=f.H1ADX-f.H1PreviousADX
    f['dATRRatio']=f.H1ATRRatio-f.H1PreviousATRRatio
    f['ready']=f[['ATR','PriorHigh','PriorLow','H1ADX','H1Slope','H1ATRRatio','H1EMA']].notna().all(axis=1)
    f['base_regime']=np.select([(f.H1ADX>20)&(f.H1Close>f.H1EMA)&(f.H1Slope>0),(f.H1ADX>20)&(f.H1Close<f.H1EMA)&(f.H1Slope<0)],[1,-1],default=0)
    f['regime']=np.where(f.H1ATRRatio>1,f.base_regime,0)
    f['raw_breakout']=np.select([f.Close>f.PriorHigh,f.Close<f.PriorLow],[1,-1],default=0)
    f['volatility_pct']=100*f.ATR/f.Close
    f['hour']=f.index.hour+f.index.minute/60
    f['core']=(f.hour>=10)&(f.hour<18)
    f['month']=f.index.strftime('%Y-%m');f['year']=f.index.year
    f['mmdd']=f.index.strftime('%m-%d')
    f['date']=f.index.strftime('%Y-%m-%d')
    f['abs_slope_ATR']=f.H1Slope.abs()/f.H1ATR
    f['h1_published']=f.index==f.H1AvailableAt
    p=f.loc[f.h1_published].copy()
    flips=(p.regime*p.regime.shift()<0)
    f['regime_flip']=False;f.loc[p.index,'regime_flip']=flips
    f['regime_change']=False;f.loc[p.index,'regime_change']=(p.regime!=p.regime.shift())&p.regime.shift().notna()
    core=f.ready&f.core
    f['zero_episode_start']=core&(f.regime==0)&(~core.shift(fill_value=False)|(f.regime.shift()!=0)|(f.date!=f.date.shift())|(f.index.to_series().diff()!=pd.Timedelta(minutes=15)))
    return f

def stats(t):
    t=t.sort_values(['exit_time','instrument','trade_id'])
    x=t.gross_R
    win=x[x>0];loss=x[x<0]
    pos=win.sum();neg=-loss.sum();total=x.sum()
    eq=pd.concat([pd.Series([0.]),x.reset_index(drop=True).cumsum()],ignore_index=True)
    out={'closed':len(t),'gross_PF':pos/neg if neg else None,'gross_R':total,'positive_R':pos,'negative_R':neg,
         'expectancy_R':total/len(t) if len(t) else None,'DD_closed_R':(eq.cummax()-eq).max(),
         'wins':len(win),'losses':len(loss),'win_share':len(win)/len(t) if len(t) else None,
         'mean_win_R':win.mean(),'mean_loss_R':loss.mean(),
         'holding_mean_minutes':t.holding_minutes.mean(),'holding_median_minutes':t.holding_minutes.median(),
         'bars_mean':t.bars_held.mean(),'S1_count':int(t.threshold_activated.sum()),
         'initial_without_S1':int(((t.exit_type=='INITIAL_STOP')&~t.threshold_activated).sum()),
         'failed_entries':int(((t.MFE_R<.5)&(t.gross_R<0)).sum()),
         'failed_loss_R':-t.loc[(t.MFE_R<.5)&(t.gross_R<0),'gross_R'].sum(),
         'loss_R_after_MFE1':-t.loc[(t.MFE_R>=1)&(t.gross_R<0),'gross_R'].sum(),
         'MFE2_then_loss':int(((t.MFE_R>=2)&(t.gross_R<0)).sum()),
         'gap_exits':int(t.gap_exit.sum()),'cross_day':int(t.cross_calendar_day.sum()),
         'GE2_count':int((x>=2).sum()),'GE2_R':x[x>=2].sum(),'GE5_count':int((x>=5).sum()),'GE5_R':x[x>=5].sum(),
         'MFE_mean':t.MFE_R.mean(),'MAE_mean':t.MAE_R.mean()}
    for k in ['S1_count','initial_without_S1','failed_entries']:
        out[k+'_share']=out[k]/len(t) if len(t) else None
    for v in [.5,1,2]:
        out[f'MFE_ge_{v}_share']=float((t.MFE_R>=v).mean()) if len(t) else None
    for n in [1,3,5,10]:
        top=win.nlargest(n).sum();out[f'top{n}_R']=top;out[f'top{n}_share_positive_R']=top/pos if pos else None
    for k in FEATURES:out['mean_'+k]=t[k].mean()
    return out

def select(t,basis,period,scope='ALL',direction='ALL',cut='ALL',value='ALL',outcome='ALL'):
    r=t
    col='exit_time' if basis=='EXIT' else 'entry_time'
    if period!='ALL':
        if period=='2024Q2':r=r[r[col].str[:7].isin(['2024-04','2024-05','2024-06'])]
        else:r=r[r[col].str.startswith(period)]
    if scope=='FX':r=r[r.instrument.isin(SYMBOLS[:2])]
    elif scope!='ALL':r=r[r.instrument==scope]
    if direction!='ALL':r=r[r.direction==direction]
    if cut!='ALL':r=r[r[cut].astype(str)==value]
    if outcome=='WIN':r=r[r.gross_R>0]
    if outcome=='LOSS':r=r[r.gross_R<0]
    if outcome=='GE2':r=r[r.gross_R>=2]
    if outcome=='GE5':r=r[r.gross_R>=5]
    return r

def breakout_events(f,s):
    rows=[];ix=list(f.index)
    for i in np.flatnonzero((f.raw_breakout!=0)&f.ready):
        b=f.iloc[i];sign=int(b.raw_breakout);level=b.PriorHigh if sign>0 else b.PriorLow
        window=f.iloc[i+1:i+5]
        valid=len(window)==4 and window.index[-1]==ix[i]+pd.Timedelta(minutes=60) and all(window.index.date==ix[i].date())
        out={'instrument':s,'signal_time':ix[i],'year':int(b.year),'month':b.month,'direction':'LONG' if sign>0 else 'SHORT',
             'eligible_signal':bool(b.Signal),'core':bool(b.core),'matched':bool(b.matched),'window_complete':bool(valid),
             'no_continuation':None,'return_behind_level':None,'repeat_after_failure':None,'reverse_after_failure':None}
        if valid:
            favorable=(window.High.max()-b.Close if sign>0 else b.Close-window.Low.min())/b.ATR
            fail=favorable<1
            out['no_continuation']=bool(fail)
            out['return_behind_level']=bool(((window.Close-level)*sign<=0).any())
            nxt=f.iloc[i+5:i+9]
            next_valid=len(nxt)==4 and nxt.index[-1]==ix[i]+pd.Timedelta(minutes=120) and all(nxt.index.date==ix[i].date())
            if fail and next_valid:
                signs=nxt.raw_breakout[nxt.raw_breakout!=0]
                out['repeat_after_failure']=bool(len(signs) and signs.iloc[0]==sign)
                out['reverse_after_failure']=bool(len(signs) and signs.iloc[0]==-sign)
        rows.append(out)
    return rows

def market_stats(f,events):
    a=f[f.ready&f.core];ev=events[events.core] if len(events) else events
    v=ev[ev.window_complete] if len(ev) else ev
    out={'core_ready_bars':len(a),'observed_days':a.date.nunique(),'base_directional_share':(a.base_regime!=0).mean(),
         'tradable_regime_share':(a.regime!=0).mean(),'no_tradable_share':(a.regime==0).mean(),
         'LONG_regime_share':(a.regime==1).mean(),'SHORT_regime_share':(a.regime==-1).mean(),
         'mean_ADX':a.H1ADX.mean(),'mean_dADX':a.dADX.mean(),'ADX_rising_share':(a.dADX>0).mean(),
         'mean_ATRRatio':a.H1ATRRatio.mean(),'ATRRatio_rising_share':(a.dATRRatio>0).mean(),'mean_dATRRatio':a.dATRRatio.mean(),
         'mean_abs_slope_ATR':a.abs_slope_ATR.mean(),'mean_volatility_pct':a.volatility_pct.mean(),'mean_efficiency5':a.efficiency5.mean(),
         'signals':int((a.Signal!=0).sum()),'raw_breakouts':len(ev),'complete_breakout_windows':len(v),
         'no_continuation_count':int(v.no_continuation.sum()) if len(v) else 0,
         'no_continuation_share':v.no_continuation.mean() if len(v) else None,
         'return_behind_share':v.return_behind_level.mean() if len(v) else None,
         'regime_flips_H1':int(a.regime_flip.sum()),'H1_publications':int(a.h1_published.sum()),'regime_changes_H1':int(a.regime_change.sum()),
         'no_regime_episode_starts':int(a.zero_episode_start.sum()),
         'no_regime_episodes_per_1000bars':1000*a.zero_episode_start.sum()/len(a) if len(a) else None}
    elig=v[v.eligible_signal] if len(v) else v
    out['eligible_complete_windows']=len(elig)
    out['eligible_no_continuation_share']=elig.no_continuation.mean() if len(elig) else None
    failed=v[v.no_continuation==True] if len(v) else v
    known=failed[failed.repeat_after_failure.notna()] if len(failed) else failed
    out['failure_followup_windows']=len(known)
    out['repeat_after_failure_count']=int(known.repeat_after_failure.sum()) if len(known) else 0
    out['reverse_after_failure_count']=int(known.reverse_after_failure.sum()) if len(known) else 0
    return out

def run(root,output):
    assert output.resolve().is_relative_to(HERE)
    output.mkdir(parents=True,exist_ok=True)
    assert C.git('rev-parse','HEAD',root=root).decode().strip()==C.DATA_SHA
    assert not C.git('status','--porcelain',root=root).strip()
    specs=json.loads((REF/'EXPERIMENT_SPECS.json').read_text())
    all_t=[];all_d=[];all_e=[];all_g=[];all_o=[];all_sn=[];frames={};coverage=[];matches=[];hlogs=[];events=[]
    comp=C.Comparison();sources=[]
    for src in specs['sources']:
        path=root/src['path'];s=src['instrument']
        assert C.file_sha(path)==src['full_sha256']
        assert C.git('hash-object',str(path),root=root).decode().strip()==src['git_blob_sha']
        assert C.git('rev-parse',f'{C.DATA_SHA}:{src["path"]}',root=root).decode().strip()==src['git_blob_sha']
        raw=E.read_source(path);_,prefix=C.parse_prefix(path)
        assert prefix==src['historical_prefix_sha256'] and len(raw)==src['used_candles']
        assert raw.index[0].isoformat()==src['first_close'] and raw.index[-1].isoformat()==src['last_close']
        f=extended(raw)
        dates={y:set(f.loc[(f.year==y)&f.ready&f.core,'mmdd']) for y in [2023,2024]}
        common=dates[2023]&dates[2024];f['matched']=f.mmdd.isin(common)
        matches.extend({'instrument':s,'mmdd':d} for d in sorted(common))
        frames[s]=f
        t,o,d,e,g,sn=E.replay(f,s,'OPTIMIZED','COMBINED')
        all_t+=t;all_d+=d;all_e+=e;all_g+=g;all_sn+=sn
        if o:all_o.append(o)
        for y in [2023,2024]:
            q=f[f.year==y];delta=q.index.to_series().diff().dt.total_seconds()/60
            coverage.append({'instrument':s,'year':y,'M15_bars':len(q),'first_close':q.index[0],'last_close':q.index[-1],
                'observed_Close_days':q.date.nunique(),'ready_core_days':q.loc[q.ready&q.core,'date'].nunique(),
                'H1_valid_blocks':int(q.h1_published.sum()),'H1_ready_core_bars':int((q.ready&q.core).sum()),
                'within_date_gaps_gt15':int(((delta>15)&(q.index.to_series().dt.date==q.index.to_series().shift().dt.date)).sum()),
                'cross_date_gaps':int(((delta>15)&(q.index.to_series().dt.date!=q.index.to_series().shift().dt.date)).sum()),
                'matched_MMDD_days':len(common)})
        hlogs.extend({'instrument':s,'close_time':at,**{k:b[k] for k in ['H1ADX','dADX','H1ATRRatio','dATRRatio','H1ATR','H1EMA','H1Close','H1Slope','efficiency5','base_regime','regime','regime_flip']}} for at,b in f[f.h1_published].iterrows())
        events+=breakout_events(f,s);sources.append(src)
    # All published journals, including occupancy and Stop order, not just CSV removal.
    for name,actual,keys in [('trades.csv',all_t,['instrument','entry_time']),('stop_decisions.csv',all_d,['instrument','bar_close_time']),
                             ('entry_opportunities.csv',all_e,['instrument','signal_time']),('observed_gaps.csv',all_g,['instrument','current_close'])]:
        with (REF/'results'/name).open() as p:ref=[x for x in csv.DictReader(p) if x['version']=='OPTIMIZED' and x['rule']=='COMBINED']
        comp.rows(actual,ref,name,keys)
        write(output/name,actual)
    for name,actual,keys in [('OPEN_POSITIONS.json',all_o,['instrument']),('PERIOD_END_OPEN_POSITIONS.json',all_sn,['instrument','month'])]:
        ref=[x for x in json.loads((REF/'results'/name).read_text()) if x['version']=='OPTIMIZED' and x['rule']=='COMBINED']
        comp.rows(actual,ref,name,keys);dump(output/name,actual)
    assert not comp.diffs,comp.diffs[:3]
    write(output/'REPRODUCTION_DIFF.csv',comp.diffs or [{'status':'NO_DIFFERENCES'}])
    dump(output/'REPRODUCTION.json',{'status':'PASS','closed':len(all_t),'terminal_OPEN':len(all_o),'fields_compared':comp.fields,'differences':len(comp.diffs),'tables':comp.tables,'absolute_tolerance':1e-8})
    t=pd.DataFrame(all_t)
    for k in ['entry_time','exit_time']:t[k]=t[k].map(lambda v:v.isoformat())
    enriched=[]
    for r in t.to_dict('records'):
        b=frames[r['instrument']].loc[pd.Timestamp(r['entry_time'])];sign=1 if r['direction']=='LONG' else -1
        r['activation_time']=None if pd.isna(r['activation_time']) else r['activation_time']
        r.update(dADX=b.dADX,dATRRatio=b.dATRRatio,signed_slope_ATR=sign*b.H1Slope/b.H1ATR,volatility_pct=b.volatility_pct,
                 breakout_ATR=sign*(b.Close-r['breakout_level'])/b.ATR,
                 close_location=(b.Close-b.Low if sign>0 else b.High-b.Close)/(b.High-b.Low) if b.High>b.Low else None,hour=b.hour,matched=bool(b.matched),
                 A6=bool(b.dATRRatio>0),ADX_rising=bool(b.dADX>0),slope_strengthening=bool(abs(b.H1Slope)>abs(b.H1PreviousSlope)),
                 M15_ATR_rising=bool(b.ATR>b.PreviousATR),hour_bin='10-12' if b.hour<12 else '12-15' if b.hour<15 else '15-18')
        enriched.append(r)
    t=pd.DataFrame(enriched);write(output/'trade_diagnostics.csv',enriched)
    write(output/'coverage.csv',coverage);write(output/'matched_dates.csv',matches);write(output/'h1_features.csv',hlogs);write(output/'breakout_diagnostics.csv',events)
    ev=pd.DataFrame(events)
    yearly=[];monthly=[];quality=[];cuts=[];matched=[]
    for period in ['ALL','2023','2024']+MONTHS:
        for scope in ['ALL','FX']+SYMBOLS:
            for side in ['ALL','LONG','SHORT']:
                key={'basis':'EXIT','period':period,'scope':scope,'direction':side,'cut':'ALL','value':'ALL','outcome':'ALL'}
                q=select(t,**key);row=key|stats(q)
                if len(period)==7:
                    row['coverage']='NO_COVERAGE' if scope in SYMBOLS and not (frames[scope].month==period).any() else 'AVAILABLE'
                    for s in SYMBOLS:row['R_'+s]=q.loc[q.instrument==s,'gross_R'].sum()
                    row['R_LONG']=q.loc[q.direction=='LONG','gross_R'].sum();row['R_SHORT']=q.loc[q.direction=='SHORT','gross_R'].sum()
                    monthly.append(row)
                else:
                    m=q.groupby(q.exit_time.str[:7]).gross_R.sum();n=24 if period=='ALL' else 12
                    row.update(positive_months=int((m>0).sum()),calendar_months=n,
                        best_month_R=m.max(),top3_months_R=m.nlargest(3).sum(),
                        best_month_share_GrossR=m.max()/row['gross_R'] if row['gross_R'] else None,
                        top3_months_share_GrossR=m.nlargest(3).sum()/row['gross_R'] if row['gross_R'] else None,
                        best_month_share_positive_month_R=m.max()/m[m>0].sum() if len(m[m>0]) else None,
                        top3_months_share_positive_month_R=m.nlargest(3).sum()/m[m>0].sum() if len(m[m>0]) else None)
                    yearly.append(row)
    for period in ['ALL','2023','2024','2024Q2','2024-10','2024-11']:
        for scope in ['ALL']+SYMBOLS:
            for side in ['ALL','LONG','SHORT']:
                for outcome in ['ALL','WIN','LOSS','GE2','GE5']:
                    key={'basis':'ENTRY','period':period,'scope':scope,'direction':side,'cut':'ALL','value':'ALL','outcome':outcome}
                    quality.append(key|stats(select(t,**key)))
        for cut,values in [('A6',['True','False']),('ADX_rising',['True','False']),('slope_strengthening',['True','False']),('M15_ATR_rising',['True','False']),('hour_bin',['10-12','12-15','15-18'])]:
            for value in values:
                for side in ['ALL','LONG','SHORT']:
                    key={'basis':'ENTRY','period':period,'scope':'ALL','direction':side,'cut':cut,'value':value,'outcome':'ALL'}
                    cuts.append(key|stats(select(t,**key))|{'interpretation':'FROZEN_LEDGER_DIAGNOSTIC_NOT_NEW_CAUSAL_REPLAY'})
    for y in ['2023','2024']:
        for scope in ['ALL','FX']+SYMBOLS:
            key={'basis':'ENTRY','period':y,'scope':scope,'direction':'ALL','cut':'matched','value':'True','outcome':'ALL'}
            matched.append(key|stats(select(t,**key))|{'interpretation':'MATCHED_MMDD_ENTRY_COHORT_FULL_PATH_OUTCOMES_NOT_NEW_REPLAY'})
    distributions=[]
    for key in quality:
        if key['scope']!='ALL':continue
        q=select(t,**{k:key[k] for k in ['basis','period','scope','direction','cut','value','outcome']})
        for feature in FEATURES:
            x=q[feature].dropna()
            distributions.append({k:key[k] for k in ['basis','period','scope','direction','outcome']}|{'feature':feature,'count':len(x),'min':x.min(),'p25':x.quantile(.25),'median':x.median(),'p75':x.quantile(.75),'max':x.max()})
    write(output/'entry_feature_distributions.csv',distributions)
    for name,rows in [('yearly',yearly),('monthly',monthly),('entry_quality',quality),('causal_cuts',cuts),('matched_coverage_trades',matched)]:write(output/(name+'.csv'),rows)
    markets=[]
    for period in ['2023','2024']+MONTHS:
        for scope in ['ALL','FX']+SYMBOLS:
            for coverage_mode in ['FULL','MATCHED']:
                fs=[v for s,v in frames.items() if scope=='ALL' or (scope=='FX' and s in SYMBOLS[:2]) or scope==s]
                a=pd.concat(fs);b=ev if scope=='ALL' else ev[ev.instrument.isin(SYMBOLS[:2])] if scope=='FX' else ev[ev.instrument==scope]
                a=a[a.month.str.startswith(period)];b=b[b.month.str.startswith(period)]
                if coverage_mode=='MATCHED':a=a[a.matched];b=b[b.matched]
                markets.append({'period':period,'scope':scope,'coverage_mode':coverage_mode}|market_stats(a,b))
    write(output/'market_regime.csv',markets)
    breakout_sides=[]
    for period in ['2023','2024']+MONTHS:
        for side in ['LONG','SHORT']:
            q=ev[ev.core&ev.month.str.startswith(period)&(ev.direction==side)];v=q[q.window_complete];e=v[v.eligible_signal]
            breakout_sides.append({'period':period,'direction':side,'raw_core_breakouts':len(q),'complete_windows':len(v),'raw_no_continuation_share':v.no_continuation.mean() if len(v) else None,
                'eligible_complete_windows':len(e),'eligible_no_continuation_share':e.no_continuation.mean() if len(e) else None,'eligible_return_behind_share':e.return_behind_level.mean() if len(e) else None})
    write(output/'breakout_direction.csv',breakout_sides)
    funnels=[];ep=pd.DataFrame(all_e);ep['period']=ep.signal_time.map(lambda v:v.strftime('%Y-%m'))
    for period in ['2023','2024']+MONTHS:
        for scope in ['ALL','FX']+SYMBOLS:
            for side in ['ALL','LONG','SHORT']:
                a=ep[ep.period.str.startswith(period)]
                if scope=='FX':a=a[a.instrument.isin(SYMBOLS[:2])]
                elif scope!='ALL':a=a[a.instrument==scope]
                if side!='ALL':a=a[a.direction==side]
                funnels.append({'period':period,'scope':scope,'direction':side,'signals_all_hours':len(a),
                    'signals_T1':int(a.rule_pass.sum()),'accepted_including_OPEN':int(a.entry_accepted.sum()),
                    'T1_busy':int((a.rule_pass&a.position_occupied).sum()),'outside_T1':int((~a.rule_pass).sum()),
                    'same_close_reentry':int((a.entry_accepted&a.same_close_exit_trade_id.notna()).sum())})
    write(output/'signal_funnel.csv',funnels)
    winners=t[t.gross_R>=2].sort_values('gross_R',ascending=False).to_dict('records');write(output/'large_winners.csv',winners)
    # Historical A6 results: read-only previous full replay; no new variant.
    hist=pd.read_csv(HERE.parent/'t3_m15_entry_regime_v1/results/trades.csv')
    a6=[]
    for rule in ['CONTROL','A6']:
        for period in ['2023','2024']+MONTHS:
            q=hist[(hist.version=='OPTIMIZED')&(hist.rule==rule)&hist.exit_time.str.startswith(period)]
            x=q.gross_R;pos=x[x>0].sum();neg=-x[x<0].sum()
            a6.append({'source_PR':495,'rule':rule,'period':period,'closed':len(q),'gross_R':x.sum(),'gross_PF':pos/neg if neg else None,'interpretation':'HISTORICAL_SEPARATE_REPLAY_NOT_T1_S1'})
    write(output/'historical_A6.csv',a6)
    expected={2023:(190,2.1373,98.3963,9),2024:(355,1.5199,94.4229,8)}
    for y,(n,pf,r,pm) in expected.items():
        z=next(v for v in yearly if v['period']==str(y) and v['scope']=='ALL' and v['direction']=='ALL')
        assert z['closed']==n and round(z['gross_PF'],4)==pf and round(z['gross_R'],4)==r and z['positive_months']==pm
    for month,r in {'2024-04':-.8685,'2024-05':-2.8096,'2024-06':-1.1554,'2024-10':-.3681,'2024-11':44.0619}.items():
        z=next(v for v in monthly if v['period']==month and v['scope']=='ALL' and v['direction']=='ALL');assert round(z['gross_R'],4)==r
    nonov=stats(t[t.exit_time.str.startswith('2024')&~t.exit_time.str.startswith('2024-11')]);assert round(nonov['gross_R'],4)==50.3610 and round(nonov['gross_PF'],4)==1.2958
    dump(output/'CHECKPOINTS.json',{'status':'PASS','expected':expected,'2024_without_November':nonov,'interpretation':'RETROSPECTIVE_CLOSED_LEDGER_DIAGNOSTIC_NOT_NEW_REPLAY'})
    dump(output/'SOURCE_MANIFEST.json',{'base_main':BASE,'data_commit':C.DATA_SHA,'sources':sources,'future_OHLC_parsed':False,'labels':LABEL,'data_classification':'DEVELOPMENT_EXPOSED',
        'historical_reference_tree_sha':C.git('rev-parse',f'{BASE}:IntradayLab/t3_m15_t1_s1_v1').decode().strip(),
        'references_SHA256':{str(p.relative_to(REPO)):C.file_sha(p) for p in sorted(REF.rglob('*')) if p.is_file()},
        'code_SHA256':{p.name:C.file_sha(p) for p in sorted(HERE.glob('*.py'))},'runtime':{'python':sys.version.split()[0],'pandas':pd.__version__,'numpy':np.__version__}})
    print(json.dumps({'status':'PASS','closed':len(t),'open':len(all_o),'reproduced_fields':comp.fields,'breakouts':len(events),'H1_rows':len(hlogs)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True);p.add_argument('--output',type=Path,default=HERE/'results');a=p.parse_args();run(a.data_root,a.output)
