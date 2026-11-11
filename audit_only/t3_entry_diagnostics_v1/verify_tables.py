"""Fresh CSV descriptive arithmetic and clustered intervals; no analysis imports."""
import math
from collections import defaultdict
from statistics import median
import numpy as np
from support import csvin,js

def check_tables(out):
    rows=[];feature_rows=[];fields=0;maximum=0.
    for system in ('H1','M15'):
        f=csvin(out/f'ENTRY_FEATURES_{system}.csv');feature_rows.extend(f);ix={r['signal_id']:r for r in f}
        rows.extend(dict(ix[r['signal_id']],**r) for r in csvin(out/f'OUTCOME_GROUPS_{system}.csv'))
    thresholds={(r['system'],r['feature']):r for r in csvin(out/'FEATURE_THRESHOLDS.csv')}
    def num(v):return None if v=='' else float(v)
    def eq(expected,actual,ctx):
        nonlocal fields,maximum
        fields+=1
        if expected is None:assert actual=='',(ctx,expected,actual)
        else:
            error=abs(float(expected)-float(actual));maximum=max(maximum,error)
            assert error<1e-8,(ctx,expected,actual,error)
    for (system,name),r in thresholds.items():
        vals=sorted(float(t[name]) for t in rows if t['system']==system and t[name]!='')
        def q(p):
            z=(len(vals)-1)*p;i=int(z);return vals[i]+(vals[min(i+1,len(vals)-1)]-vals[i])*(z-i)
        eq(q(1/3),r['q1'],('TERCILE1',system,name));eq(q(2/3),r['q2'],('TERCILE2',system,name))
    def group(rs,g):
        if g=='ALL':return rs
        if g=='WINNERS':return [r for r in rs if r['status']=='CLOSED' and float(r['gross_R'])>0]
        if g=='LOSERS':return [r for r in rs if r['status']=='CLOSED' and float(r['gross_R'])<0]
        if g=='LARGE_WINNER_GE_2R':return [r for r in rs if r['large_winner_ge_2R']=='True']
        return [r for r in rs if r['outcome_group']==g]
    for r in csvin(out/'FEATURE_DISTRIBUTIONS.csv'):
        rs=group([t for t in rows if t['system']==r['system']],r['outcome']);v=[float(t[r['feature']]) for t in rs if t[r['feature']]!='']
        eq(len(rs),r['N'],('DIST_N',r['system'],r['feature'],r['outcome']))
        for key,p in [('p25',.25),('median',.5),('p75',.75)]:eq(float(np.quantile(v,p)) if v else None,r[key],('DIST',r['feature'],r['outcome'],key))
    months=[f'{y}-{m:02d}' for y in (2023,2024) for m in range(1,13)]
    draws=np.random.default_rng(560518).integers(0,24,size=(2000,24));weights=np.array([np.bincount(d,minlength=24) for d in draws])
    def stat(rs,actual):
        c=[r for r in rs if r['status']=='CLOSED'];n=len(c);st=sum(r['outcome_group']=='INITIAL_STOP' for r in c)
        eq(len(rs),actual['N'],('SUMMARY_N',actual));eq(n,actual['CLOSED'],('CLOSED',actual))
        eq(len(rs)-n,actual['OPEN'],('OPEN',actual));eq(st,actual['INITIAL_STOP'],('INITIAL',actual))
        eq(st/n if n else None,actual['initial_stop_share'],('STOP_SHARE',actual))
        rsr=[float(r['gross_R']) for r in c]
        eq(math.fsum(rsr)/n if n else None,actual['mean_gross_R'],('MEAN_R',actual));eq(median(rsr) if n else None,actual['median_gross_R'],('MEDIAN_R',actual))
        eq(sum(r['large_winner_ge_2R']=='True' for r in c),actual['large_winners_ge_2R'],('BIG',actual))
        for key,source in [('median_MAE_R','MAE_executable_R0'),('median_MFE_R','MFE_pre_stop_R0'),('median_first_favorable_minutes_observed','first_favorable_minutes_bound'),('median_first_half_R_minutes_observed','first_half_R_minutes_bound')]:
            vals=[float(r[source]) for r in rs if r[source]!=''];eq(median(vals) if vals else None,actual[key],('MEDIAN',key,actual))
        ns=np.array([sum(r['signal_month']==m for r in c) for m in months]);ss=np.array([sum(r['signal_month']==m and r['outcome_group']=='INITIAL_STOP' for r in c) for m in months])
        nr=np.array([math.fsum(float(r['gross_R']) for r in c if r['signal_month']==m) for m in months])
        denom=weights@ns
        for numer,lo,hi in [(weights@ss,'initial_stop_ci95_low','initial_stop_ci95_high'),(weights@nr,'mean_R_ci95_low','mean_R_ci95_high')]:
            estimates=numer[denom>0]/denom[denom>0]
            eq(float(np.quantile(estimates,.025)) if len(estimates) else None,actual[lo],('CI',lo,actual))
            eq(float(np.quantile(estimates,.975)) if len(estimates) else None,actual[hi],('CI',hi,actual))
    for r in csvin(out/'OUTCOME_SUMMARY.csv'):
        stat(group([t for t in rows if t['system']==r['system']],r['outcome']),r)
    for r in csvin(out/'FEATURE_BUCKETS.csv'):
        rs=[t for t in rows if t['system']==r['system']];name=r['feature'];bucket=r['bucket']
        if name=='breakout_05_prespecified':
            selected=[t for t in rs if (float(t['breakout_atr'])>=.5)==(bucket=='GE_0.5')]
        else:
            q1=float(thresholds[(r['system'],name)]['q1']);q2=float(thresholds[(r['system'],name)]['q2'])
            def label(t):return 'MISSING' if t[name]=='' else 'LOW' if float(t[name])<=q1 else 'MID' if float(t[name])<=q2 else 'HIGH'
            selected=[t for t in rs if label(t)==bucket]
        stat(selected,r)
    for r in csvin(out/'INSTRUMENT_DIRECTION.csv'):
        keys={'instrument':['instrument'],'direction':['direction'],'year':['signal_year'],'instrument_direction_year':['instrument','direction','signal_year']}[r['dimension']]
        stat([t for t in rows if t['system']==r['system'] and '|'.join(t[k] for k in keys)==r['key']],r)
    qdraws=np.random.default_rng(560518).integers(0,8,size=(2000,8))
    quarter=np.repeat(np.array([np.bincount(d,minlength=8) for d in qdraws]),3,axis=1)
    def delta(high,low,r):
        h=[t for t in high if t['status']=='CLOSED'];l=[t for t in low if t['status']=='CLOSED']
        hn=np.array([sum(t['signal_month']==m for t in h) for m in months]);ln=np.array([sum(t['signal_month']==m for t in l) for m in months])
        hs=np.array([sum(t['signal_month']==m and t['outcome_group']=='INITIAL_STOP' for t in h) for m in months]);ls=np.array([sum(t['signal_month']==m and t['outcome_group']=='INITIAL_STOP' for t in l) for m in months])
        for key,v in [('high_n',len(h)),('low_n',len(l)),('high_initial',sum(hs)),('low_initial',sum(ls))]:eq(v,r[key],('DIFFERENCE_COUNTS',key,r))
        eq(sum(hs)/len(h)-sum(ls)/len(l) if h and l else None,r['risk_difference'],('DIFFERENCE',r))
        for w,lop,hip in [(weights,'ci95_low','ci95_high'),(quarter,'quarter_ci95_low','quarter_ci95_high')]:
            a=w@hn;b=w@ln;valid=(a>0)&(b>0)
            d=(w@hs)[valid]/a[valid]-(w@ls)[valid]/b[valid]
            eq(float(np.quantile(d,.025)) if len(d) else None,r[lop],('DIFFERENCE_CI',lop,r))
            eq(float(np.quantile(d,.975)) if len(d) else None,r[hip],('DIFFERENCE_CI',hip,r))
    for r in csvin(out/'STABILITY.csv'):
        rs=[t for t in rows if t['system']==r['system']];dim=r['dimension']
        if dim=='leave_one_instrument_out':rs=[t for t in rs if t['instrument']!=r['value']]
        elif dim!='ALL':rs=[t for t in rs if t[dim]==r['value']]
        th=thresholds[(r['system'],r['feature'])];q1=float(th['q1']);q2=float(th['q2']);name=r['feature']
        delta([t for t in rs if t[name]!='' and float(t[name])>q2],[t for t in rs if t[name]!='' and float(t[name])<=q1],r)
    for r in csvin(out/'BREAKOUT_05_STRATA.csv'):
        rs=[t for t in rows if t['system']==r['system']]
        for t in rs:t['volatility_tercile']='LOW' if float(t['context_atr_ratio'])<=float(r['vol_q1']) else 'MID' if float(t['context_atr_ratio'])<=float(r['vol_q2']) else 'HIGH'
        keys={'ALL':[],'instrument':['instrument'],'direction':['direction'],'year':['signal_year'],'volatility':['volatility_tercile'],
              'instrument_direction_year_volatility':['instrument','direction','signal_year','volatility_tercile']}[r['dimension']]
        if keys:rs=[t for t in rs if '|'.join(t[k] for k in keys)==r['key']]
        delta([t for t in rs if float(t['breakout_atr'])>=.5],[t for t in rs if float(t['breakout_atr'])<.5],r)
    execution={r['signal_id']:r for r in csvin(out/'EXECUTION_DIAGNOSTICS.csv')}
    for r in csvin(out/'EXECUTION_DIAGNOSTIC_SUMMARY.csv'):
        selected=group([t for t in rows if t['system']==r['system']],r['outcome'])
        vs=[float(execution[t['signal_id']]['signed_next_open_gap_atr']) for t in selected]
        eq(len(vs),r['N'],('GAP_N',r))
        for key,p in [('p25',.25),('median',.5),('p75',.75)]:eq(float(np.quantile(vs,p)) if vs else None,r[key],('GAP_QUANTILE',key,r))
    receipt=dict(status='PASS',fields_checked=fields,max_abs_numeric_error=maximum,
      method='Fresh CSV counts/returns/medians/quantiles; independently reconstructed seeded month-cluster intervals for every outcome, feature bucket and instrument/direction/year summary; every stability/breakout-stratum difference with month/quarter intervals; execution-gap summaries')
    js(out/'TABLE_VERIFICATION.json',receipt);return receipt
