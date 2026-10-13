"""Independent stdlib diagnostics. Does not import diagnostics/pandas/numpy/primary_metrics."""
import json,math
import common as C
from scalar_metrics import stats

SPEC=json.loads((C.HERE/'SPEC.json').read_text())
SCOPES={'ALL_FOUR':C.SYMBOLS,'FX':C.SYMBOLS[:2]}
for symbol in C.SYMBOLS:SCOPES[symbol]=(symbol,)
DIRECTIONS=('ALL','LONG','SHORT')
FEATURES=('H1ADX','dADX','H1ATRRatio','dATRRatio','signed_slope_M15ATR','d_signed_slope_M15ATR','ATR','ATR_pct','breakout_ATR','H1_age_minutes','signal_hour')
CUTS=tuple(SPEC['diagnostic_bins'])+('ADX_RISING','SLOPE_STRENGTHENING','M15_ATR_RISING','HOUR')
OUTCOMES=('ALL','WIN','LOSS','LOSS_MFE_LT_0_5','INITIAL_STOP_NO_S1','INITIAL_STOP_AFTER_S1','GE2','GE5')


def causal_fields(b,symbol,sign):
    h=b['h1'];previous=b['previous_h1'];at=b['at'];atr=b['atr'];level=b['upper'] if sign>0 else b['lower']
    assert h['at']<=at and previous['at']<h['at']
    slope_change=sign*(h['slope']-previous['slope'])
    hour=at.hour+at.minute/60
    result={'instrument':symbol,'signal_time':at,'signal_year':at.year,'signal_month':at.strftime('%Y-%m'),'signal_date':at.strftime('%Y-%m-%d'),'direction':'LONG' if sign>0 else 'SHORT',
        'H1AvailableAt':h['at'],'H1PreviousAvailableAt':previous['at'],'H1ADX':h['adx'],'dADX':h['adx']-previous['adx'],
        'H1Slope':h['slope'],'H1PreviousSlope':previous['slope'],'H1ATRRatio':h['ratio'],'dATRRatio':h['ratio']-previous['ratio'],
        'ATR':atr,'PreviousATR':b['previous_atr'],'ATR_pct':100*atr/b['c'],'signed_slope_M15ATR':sign*h['slope']/atr,
        'd_signed_slope_M15ATR':slope_change/atr,'breakout_level':level,'breakout_ATR':sign*(b['c']-level)/atr,
        'signal_close':b['c'],'H1_age_minutes':(at-h['at']).total_seconds()/60,'signal_hour':hour,
        'ADX_RISING':h['adx']>previous['adx'],'SLOPE_STRENGTHENING':slope_change>0,'M15_ATR_RISING':atr>b['previous_atr']}
    bounds=[(10,'BEFORE_10'),(12,'10_12'),(15,'12_15'),(18,'15_18'),(math.inf,'AFTER_18')]
    result['HOUR']=next(name for limit,name in bounds if hour<limit)
    for name,boundaries in SPEC['diagnostic_bins'].items():
        result[name+'_bin']='B'+str(sum(result[name]>=boundary for boundary in boundaries))
    return result


def market_window(bars,i,level,atr,sign):
    at=bars[i]['at'];future=bars[i+1:i+5]
    invalid=len(future)!=4
    for j,b in enumerate(future,1):invalid=invalid or b['at']!=at+j*C.STEP or b['at'].date()!=at.date()
    if invalid:return {'window_status':'CENSORED','window_recross':None,'window_no_1ATR':None,'window_favorable_ATR':None}
    distance=max((sign*((b['h'] if sign>0 else b['l'])-bars[i]['c'])/atr for b in future),default=0.)
    recross=any(sign*(b['c']-level)<=0 for b in future)
    return {'window_status':'COMPLETE','window_recross':recross,'window_no_1ATR':distance<1,'window_favorable_ATR':max(0.,distance)}


def entry_rows(out,frames):
    location={s:{b['at']:i for i,b in enumerate(frames[s])} for s in C.SYMBOLS};lookup={};signals=[]
    for decision in out['entry_opportunities']:
        symbol=decision['instrument'];at=decision['signal_time'];i=location[symbol][at];b=frames[symbol][i];sign=decision['original_signal']
        r=causal_fields(b,symbol,sign)
        for k in ('rule_pass','position_occupied','entry_accepted','decision_reason','trade_id','same_close_exit_trade_id','occupied_trade_id'):r[k]=decision.get(k)
        r.update(market_window(frames[symbol],i,r['breakout_level'],r['ATR'],sign));signals.append(r);lookup[symbol,at]=r
    closed=[];opened=[]
    for t in out['trades']:
        r=dict(lookup[t['instrument'],t['signal_time']]);r.update(t)
        r['status']='CLOSED';r['initial_no_s1']=t['exit_type']=='INITIAL_STOP' and not t['threshold_activated'];r['initial_after_s1']=t['exit_type']=='INITIAL_STOP' and t['threshold_activated']
        r['failed_lower_MFE']=t['gross_R']<0 and t['MFE_R']<.5;r['GE2']=t['gross_R']>=2;r['GE5']=t['gross_R']>=5;r['execution_bar_stop']=t['bars_held']==1
        r['exit_month']=t['exit_time'].strftime('%Y-%m');r['exit_year']=t['exit_time'].year;closed.append(r)
    for t in out['OPEN_POSITIONS']:
        r=dict(lookup[t['instrument'],t['signal_time']]);r.update(t);r['status']='OPEN';opened.append(r)
    return signals,closed,opened


def select(rows,scope,direction,year='ALL',clock='exit_year'):
    selected=[]
    for r in rows:
        if r['instrument'] not in SCOPES[scope]:continue
        if direction!='ALL' and r['direction']!=direction:continue
        if year!='ALL' and r[clock]!=year:continue
        selected.append(r)
    return selected


def quantile(values,q):
    x=sorted(values)
    if not x:return None
    index=(len(x)-1)*q;lo=int(index);hi=min(len(x)-1,lo+1)
    return x[lo]+(x[hi]-x[lo])*(index-lo)


def sample_stats(rows,calendar):
    result=stats(rows,calendar);n=len(rows)
    for k in ('initial_no_s1','initial_after_s1','failed_lower_MFE','GE2','GE5','execution_bar_stop'):result[k]=sum(1 for r in rows if r[k])
    result['initial_stops']=result['initial_no_s1']+result['initial_after_s1'];result['S1_activated']=sum(1 for r in rows if r['threshold_activated'])
    result['MFE_GE1']=sum(1 for r in rows if r['MFE_R']>=1);result['MFE_GE2']=sum(1 for r in rows if r['MFE_R']>=2)
    result['loss_after_MFE_GE1']=sum(1 for r in rows if r['gross_R']<0 and r['MFE_R']>=1)
    result['failed_lower_MFE_R']=math.fsum(r['gross_R'] for r in rows if r['failed_lower_MFE']);result['initial_no_s1_R']=math.fsum(r['gross_R'] for r in rows if r['initial_no_s1'])
    for k in ('initial_no_s1','initial_after_s1','failed_lower_MFE','GE2','GE5','execution_bar_stop','S1_activated'):result[k+'_fraction']=result[k]/n if n else None
    for k in ('MFE_R','MAE_R','bars_held'):
        values=[r[k] for r in rows];result[k+'_mean']=math.fsum(values)/n if n else None;result[k+'_median']=quantile(values,.5)
    complete=[r for r in rows if r['window_status']=='COMPLETE'];result['window_complete']=len(complete);result['window_censored']=n-len(complete)
    for k in ('window_recross','window_no_1ATR'):result[k+'_fraction']=sum(1 for r in complete if r[k])/len(complete) if complete else None
    return result


def by_outcome(rows,name):
    if name=='ALL':return rows
    selected=[]
    for r in rows:
        ok=r['gross_R']>0 if name=='WIN' else r['gross_R']<0 if name=='LOSS' else r['failed_lower_MFE'] if name=='LOSS_MFE_LT_0_5' else r['initial_no_s1'] if name=='INITIAL_STOP_NO_S1' else r['initial_after_s1'] if name=='INITIAL_STOP_AFTER_S1' else r[name]
        if ok:selected.append(r)
    return selected


def calculate(out,frames,sources):
    signals,closed,opened=entry_rows(out,frames)
    tables={'signal_features':signals,'trade_features':closed,'open_features':opened,'summary':[],'monthly':[],'entry_cohorts':[],'cuts':[],'feature_distributions':[],'funnel':[],'matched_dates':[],'matched_cohorts':[],'winner_entries':[],'outcome_anatomy':[]}
    for scope,symbols in SCOPES.items():
        first=min(s['first_close'][:7] for s in sources if s['instrument'] in symbols)
        for direction in DIRECTIONS:
            for year in ('ALL',2023,2024):
                calendar=list(C.CALENDAR) if year=='ALL' else [m for m in C.CALENDAR if m[:4]==str(year)]
                rows=select(closed,scope,direction,year);op=select(opened,scope,direction,year,'signal_year')
                base={'scope':scope,'direction':direction,'year':year}
                tables['summary'].append(base|{'terminal_OPEN':len(op)}|sample_stats(rows,calendar))
                entries=select(closed,scope,direction,year,'signal_year');tables['entry_cohorts'].append(base|sample_stats(entries,calendar))
                total2=sum(1 for r in entries if r['GE2']);total5=sum(1 for r in entries if r['GE5'])
                for name in CUTS:
                    if name in SPEC['diagnostic_bins']:labels=['B'+str(i) for i in range(len(SPEC['diagnostic_bins'][name])+1)];field=name+'_bin'
                    elif name=='HOUR':labels=SPEC['hours'];field=name
                    else:labels=['False','True'];field=name
                    for label in labels:
                        part=[r for r in entries if str(r[field])==label]
                        row=base|{'feature':name,'bin':label,'base_closed':len(entries),'base_GE2':total2,'base_GE5':total5,'OPEN_in_bin':sum(1 for r in op if str(r[field])==label),'GE2_share':sum(1 for r in part if r['GE2'])/total2 if total2 else None,'GE5_share':sum(1 for r in part if r['GE5'])/total5 if total5 else None}
                        tables['cuts'].append(row|sample_stats(part,calendar))
                if year!='ALL':
                    for name in OUTCOMES:
                        part=by_outcome(entries,name)
                        for feature in FEATURES:
                            values=[r[feature] for r in part if math.isfinite(r[feature])];n=len(values)
                            tables['feature_distributions'].append(base|{'outcome':name,'feature':feature,'n':n,'mean':math.fsum(values)/n if n else None,'min':min(values) if n else None,'q25':quantile(values,.25),'median':quantile(values,.5),'q75':quantile(values,.75),'max':max(values) if n else None})
                for fate in ('INITIAL_STOP_NO_S1','INITIAL_STOP_AFTER_S1','RATCHETED_LOSS','RATCHETED_NONLOSS'):
                    part=[]
                    for r in rows:
                        if fate=='INITIAL_STOP_NO_S1':ok=r['initial_no_s1']
                        elif fate=='INITIAL_STOP_AFTER_S1':ok=r['initial_after_s1']
                        elif fate=='RATCHETED_LOSS':ok=r['exit_type']=='RATCHETED_STOP' and r['gross_R']<0
                        else:ok=r['exit_type']=='RATCHETED_STOP' and r['gross_R']>=0
                        if ok:part.append(r)
                    tables['outcome_anatomy'].append(base|{'fate':fate}|sample_stats(part,calendar))
            for month in C.CALENDAR:
                rows=[r for r in select(closed,scope,direction) if r['exit_month']==month]
                coverage='NO_COVERAGE' if month<first else 'AVAILABLE_PARTIAL_START' if month==first and scope in ('GLDRUBF','IMOEXF') else 'AVAILABLE'
                tables['monthly'].append({'scope':scope,'direction':direction,'month':month,'coverage':coverage}|sample_stats(rows,[month]))
            for period in ('2023','2024',*C.CALENDAR):
                part=[r for r in select(signals,scope,direction) if r['signal_month'].startswith(period)]
                for reason in sorted(set(r['decision_reason'] for r in signals)):
                    tables['funnel'].append({'scope':scope,'direction':direction,'period':period,'decision_reason':reason,'signals':sum(1 for r in part if r['decision_reason']==reason),'all_signals':len(part)})
    for symbol in C.SYMBOLS:
        dates={2023:set(),2024:set()}
        for b in frames[symbol]:
            if b['previous_h1'] and math.isfinite(b['atr']) and math.isfinite(b['h1']['slope']):dates[b['at'].year].add(b['at'].strftime('%m-%d'))
        intersection=sorted(dates[2023].intersection(dates[2024]))
        for date in intersection:tables['matched_dates'].append({'instrument':symbol,'MM_DD':date,'date_2023':'2023-'+date,'date_2024':'2024-'+date})
        for year in (2023,2024):
            for direction in DIRECTIONS:
                rows=[r for r in select(closed,symbol,direction,year,'signal_year') if r['signal_date'][5:] in intersection]
                tables['matched_cohorts'].append({'scope':symbol,'direction':direction,'year':year,'matched_days':len(intersection)}|sample_stats(rows,[m for m in C.CALENDAR if m[:4]==str(year)]))
    fields=('instrument','direction','trade_id','signal_time','signal_year','signal_month','exit_time','gross_R','GE2','GE5',*FEATURES,*[k+'_bin' for k in SPEC['diagnostic_bins']],'ADX_RISING','SLOPE_STRENGTHENING','M15_ATR_RISING','HOUR')
    for r in closed:
        if r['GE2']:tables['winner_entries'].append({k:r[k] for k in fields})
    return tables
