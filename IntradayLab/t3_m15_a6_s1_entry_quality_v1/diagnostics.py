"""Primary diagnostic computation. Completed features and future outcomes stay separate."""
import json, math
from collections import defaultdict
import numpy as np
import pandas as pd
import common as C
from primary_metrics import metrics

SPEC=json.loads((C.HERE/'SPEC.json').read_text())
SCOPES={'ALL_FOUR':C.SYMBOLS,'FX':C.SYMBOLS[:2]}|{s:(s,) for s in C.SYMBOLS}
DIRECTIONS=('ALL','LONG','SHORT')
FEATURES=('H1ADX','dADX','H1ATRRatio','dATRRatio','signed_slope_M15ATR','d_signed_slope_M15ATR','ATR','ATR_pct','breakout_ATR','H1_age_minutes','signal_hour')
CUTS=tuple(SPEC['diagnostic_bins'])+('ADX_RISING','SLOPE_STRENGTHENING','M15_ATR_RISING','HOUR')
OUTCOMES=('ALL','WIN','LOSS','LOSS_MFE_LT_0_5','INITIAL_STOP_NO_S1','INITIAL_STOP_AFTER_S1','GE2','GE5')


def feature(row,at,symbol,side):
    r={'instrument':symbol,'signal_time':at,'signal_year':at.year,'signal_month':at.strftime('%Y-%m'),'signal_date':at.strftime('%Y-%m-%d'),'direction':'LONG' if side==1 else 'SHORT',
       'H1AvailableAt':row.H1AvailableAt,'H1PreviousAvailableAt':row.H1PreviousAvailableAt,
       'H1ADX':float(row.H1ADX),'dADX':float(row.H1ADX-row.H1PreviousADX),'H1Slope':float(row.H1Slope),'H1PreviousSlope':float(row.H1PreviousSlope),
       'H1ATRRatio':float(row.H1ATRRatio),'dATRRatio':float(row.H1ATRRatio-row.H1PreviousATRRatio),'ATR':float(row.ATR),'PreviousATR':float(row.PreviousATR),
       'ATR_pct':100*float(row.ATR/row.Close),'signed_slope_M15ATR':side*float(row.H1Slope/row.ATR),'d_signed_slope_M15ATR':side*float((row.H1Slope-row.H1PreviousSlope)/row.ATR),
       'breakout_level':float(row.PriorHigh if side==1 else row.PriorLow),'breakout_ATR':side*float((row.Close-(row.PriorHigh if side==1 else row.PriorLow))/row.ATR),
       'signal_close':float(row.Close),'H1_age_minutes':float((at-row.H1AvailableAt).total_seconds()/60),'signal_hour':at.hour+at.minute/60,
       'ADX_RISING':bool(row.H1ADX>row.H1PreviousADX),'SLOPE_STRENGTHENING':bool(side*(row.H1Slope-row.H1PreviousSlope)>0),'M15_ATR_RISING':bool(row.ATR>row.PreviousATR)}
    assert r['H1AvailableAt']<=at and r['H1PreviousAvailableAt']<r['H1AvailableAt']
    hour=r['signal_hour'];r['HOUR']='BEFORE_10' if hour<10 else '10_12' if hour<12 else '12_15' if hour<15 else '15_18' if hour<18 else 'AFTER_18'
    for k,edges in SPEC['diagnostic_bins'].items():
        r[k+'_bin']=str(pd.cut([r[k]],[-np.inf,*edges,np.inf],labels=[f'B{i}' for i in range(len(edges)+1)],right=False)[0])
    return r


def future_window(frame,at,level,atr,side):
    following=frame.loc[frame.index>at].iloc[:4]
    expected=pd.date_range(at+C.STEP,periods=4,freq='15min')
    if len(following)!=4 or not following.index.equals(expected) or any(t.date()!=at.date() for t in following.index):
        return {'window_status':'CENSORED','window_recross':None,'window_no_1ATR':None,'window_favorable_ATR':None}
    favorable=float((following.High.max()-frame.loc[at,'Close'])/atr if side==1 else (frame.loc[at,'Close']-following.Low.min())/atr)
    return {'window_status':'COMPLETE','window_recross':bool(((following.Close-level)*side<=0).any()),'window_no_1ATR':bool(favorable<1),'window_favorable_ATR':max(0.,favorable)}


def enrich(out,frames):
    signals=[];signalmap={}
    for e in out['entry_opportunities']:
        at=e['signal_time'];s=e['instrument'];side=1 if e['direction']=='LONG' else -1
        f=feature(frames[s].loc[at],at,s,side)
        f.update({k:e.get(k) for k in ('rule_pass','position_occupied','entry_accepted','decision_reason','trade_id','same_close_exit_trade_id','occupied_trade_id')})
        f.update(future_window(frames[s],at,f['breakout_level'],f['ATR'],side))
        signals.append(f);signalmap[(s,at)]=f
    closed=[];opened=[]
    for t in out['trades']:
        f=dict(signalmap[t['instrument'],t['signal_time']]);f.update(t)
        f.update(status='CLOSED',initial_no_s1=t['exit_type']=='INITIAL_STOP' and not t['threshold_activated'],initial_after_s1=t['exit_type']=='INITIAL_STOP' and t['threshold_activated'],failed_lower_MFE=t['gross_R']<0 and t['MFE_R']<.5,
            GE2=t['gross_R']>=2,GE5=t['gross_R']>=5,execution_bar_stop=t['bars_held']==1,
            exit_month=t['exit_time'].strftime('%Y-%m'),exit_year=t['exit_time'].year)
        closed.append(f)
    for o in out['OPEN_POSITIONS']:
        f=dict(signalmap[o['instrument'],o['signal_time']]);f.update(o);f['status']='OPEN';opened.append(f)
    return signals,closed,opened


def choose(rows,scope,direction,year='ALL',clock='exit_year'):
    return [r for r in rows if r['instrument'] in SCOPES[scope] and (direction=='ALL' or r['direction']==direction) and (year=='ALL' or r[clock]==year)]


def anatomy(rows):
    n=len(rows);f=pd.DataFrame(rows)
    counts={k:int(sum(bool(r[k]) for r in rows)) for k in ('initial_no_s1','initial_after_s1','failed_lower_MFE','GE2','GE5','execution_bar_stop')}
    counts['initial_stops']=counts['initial_no_s1']+counts['initial_after_s1']
    counts['S1_activated']=sum(r['threshold_activated'] for r in rows)
    counts['MFE_GE1']=sum(r['MFE_R']>=1 for r in rows);counts['MFE_GE2']=sum(r['MFE_R']>=2 for r in rows)
    counts['loss_after_MFE_GE1']=sum(r['gross_R']<0 and r['MFE_R']>=1 for r in rows)
    counts['failed_lower_MFE_R']=float(f.loc[f.failed_lower_MFE,'gross_R'].sum()) if n else 0.
    counts['initial_no_s1_R']=float(f.loc[f.initial_no_s1,'gross_R'].sum()) if n else 0.
    for k in ('initial_no_s1','initial_after_s1','failed_lower_MFE','GE2','GE5','execution_bar_stop','S1_activated'):
        counts[k+'_fraction']=counts[k]/n if n else None
    for k in ('MFE_R','MAE_R','bars_held'):
        counts[k+'_mean']=float(f[k].mean()) if n else None;counts[k+'_median']=float(f[k].median()) if n else None
    complete=[r for r in rows if r['window_status']=='COMPLETE'];counts['window_complete']=len(complete);counts['window_censored']=n-len(complete)
    for k in ('window_recross','window_no_1ATR'):counts[k+'_fraction']=sum(r[k] for r in complete)/len(complete) if complete else None
    return counts


def group_stats(rows,calendar):return metrics(rows,calendar)|anatomy(rows)


def outcome_rows(rows,outcome):
    if outcome=='ALL':return rows
    return [r for r in rows if (r['gross_R']>0 if outcome=='WIN' else r['gross_R']<0 if outcome=='LOSS' else r['failed_lower_MFE'] if outcome=='LOSS_MFE_LT_0_5' else r['initial_no_s1'] if outcome=='INITIAL_STOP_NO_S1' else r['initial_after_s1'] if outcome=='INITIAL_STOP_AFTER_S1' else r[outcome])]


def build(out,frames,sources):
    signals,closed,opened=enrich(out,frames)
    tables={'signal_features':signals,'trade_features':closed,'open_features':opened,'summary':[],'monthly':[],'entry_cohorts':[],'cuts':[],'feature_distributions':[],'funnel':[],'matched_dates':[],'matched_cohorts':[],'winner_entries':[],'outcome_anatomy':[]}
    for scope in SCOPES:
        first=min(s['first_close'][:7] for s in sources if s['instrument'] in SCOPES[scope])
        for direction in DIRECTIONS:
            for year in ('ALL',2023,2024):
                rows=choose(closed,scope,direction,year);calendar=C.CALENDAR if year=='ALL' else [m for m in C.CALENDAR if m.startswith(str(year))]
                op=choose(opened,scope,direction,year,'signal_year') if year!='ALL' else choose(opened,scope,direction)
                tables['summary'].append({'scope':scope,'direction':direction,'year':year,'terminal_OPEN':len(op)}|group_stats(rows,calendar))
                entry=choose(closed,scope,direction,year,'signal_year');base={'scope':scope,'direction':direction,'year':year}
                tables['entry_cohorts'].append(base|group_stats(entry,calendar))
                for k in CUTS:
                    labels=[f'B{i}' for i in range(len(SPEC['diagnostic_bins'][k])+1)] if k in SPEC['diagnostic_bins'] else ['False','True'] if k!='HOUR' else SPEC['hours']
                    field=k+'_bin' if k in SPEC['diagnostic_bins'] else k
                    for label in labels:
                        part=[r for r in entry if str(r[field])==label];po=[r for r in op if str(r[field])==label]
                        tables['cuts'].append(base|{'feature':k,'bin':label,'base_closed':len(entry),'base_GE2':sum(r['GE2'] for r in entry),'base_GE5':sum(r['GE5'] for r in entry),'OPEN_in_bin':len(po),'GE2_share':sum(r['GE2'] for r in part)/sum(r['GE2'] for r in entry) if any(r['GE2'] for r in entry) else None,'GE5_share':sum(r['GE5'] for r in part)/sum(r['GE5'] for r in entry) if any(r['GE5'] for r in entry) else None}|group_stats(part,calendar))
                for outcome in OUTCOMES:
                    part=outcome_rows(entry,outcome)
                    if year!='ALL':
                        for feat in FEATURES:
                            vals=pd.Series([r[feat] for r in part],dtype=float).dropna()
                            tables['feature_distributions'].append(base|{'outcome':outcome,'feature':feat,'n':len(vals),'mean':float(vals.mean()) if len(vals) else None,'min':float(vals.min()) if len(vals) else None,'q25':float(vals.quantile(.25)) if len(vals) else None,'median':float(vals.median()) if len(vals) else None,'q75':float(vals.quantile(.75)) if len(vals) else None,'max':float(vals.max()) if len(vals) else None})
                for fate in ('INITIAL_STOP_NO_S1','INITIAL_STOP_AFTER_S1','RATCHETED_LOSS','RATCHETED_NONLOSS'):
                    part=[r for r in rows if r['initial_no_s1']] if fate=='INITIAL_STOP_NO_S1' else [r for r in rows if r['initial_after_s1']] if fate=='INITIAL_STOP_AFTER_S1' else [r for r in rows if r['exit_type']=='RATCHETED_STOP' and ((r['gross_R']<0)==(fate=='RATCHETED_LOSS'))]
                    tables['outcome_anatomy'].append(base|{'fate':fate}|group_stats(part,calendar))
            for month in C.CALENDAR:
                part=[r for r in choose(closed,scope,direction) if r['exit_month']==month]
                coverage='NO_COVERAGE' if month<first else 'AVAILABLE_PARTIAL_START' if month==first and scope in ('GLDRUBF','IMOEXF') else 'AVAILABLE'
                tables['monthly'].append({'scope':scope,'direction':direction,'month':month,'coverage':coverage}|group_stats(part,[month]))
            for period in ('2023','2024',*C.CALENDAR):
                es=[r for r in choose(signals,scope,direction) if r['signal_month'].startswith(period)]
                reasons=sorted(set(r['decision_reason'] for r in signals))
                for reason in reasons:
                    tables['funnel'].append({'scope':scope,'direction':direction,'period':period,'decision_reason':reason,'signals':sum(r['decision_reason']==reason for r in es),'all_signals':len(es)})
    for s in C.SYMBOLS:
        frame=frames[s];ready=frame.loc[frame.H1PreviousAvailableAt.notna()&frame.ATR.notna()&frame.H1Slope.notna()]
        dates={y:set(t.strftime('%m-%d') for t in ready.index if t.year==y) for y in (2023,2024)}
        matched=sorted(dates[2023]&dates[2024])
        tables['matched_dates'].extend({'instrument':s,'MM_DD':d,'date_2023':'2023-'+d,'date_2024':'2024-'+d} for d in matched)
        for y in (2023,2024):
            for direction in DIRECTIONS:
                part=[r for r in choose(closed,s,direction,y,'signal_year') if r['signal_date'][5:] in matched]
                tables['matched_cohorts'].append({'scope':s,'direction':direction,'year':y,'matched_days':len(matched)}|group_stats(part,[m for m in C.CALENDAR if m.startswith(str(y))]))
    tables['winner_entries']=[{k:r[k] for k in ('instrument','direction','trade_id','signal_time','signal_year','signal_month','exit_time','gross_R','GE2','GE5',*FEATURES,*[k+'_bin' for k in SPEC['diagnostic_bins']],'ADX_RISING','SLOPE_STRENGTHENING','M15_ATR_RISING','HOUR')} for r in closed if r['GE2']]
    return tables
