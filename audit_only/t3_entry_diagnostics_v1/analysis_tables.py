"""Predeclared descriptive summaries. No strategy selection or filtered backtests."""
from collections import defaultdict
import math
import numpy as np
from support import *
from features import FEATURES_COMMON,FEATURES_H1,FEATURES_M15

MONTHS=[f'{y}-{m:02d}' for y in (2023,2024) for m in range(1,13)]
RNG_SEED=560518
REPS=2000

def weights(k):
    draws=np.random.default_rng(RNG_SEED).integers(0,k,size=(REPS,k))
    w=np.zeros((REPS,k),dtype=float)
    for i in range(REPS):w[i]=np.bincount(draws[i],minlength=k)
    return w
WM=weights(24);WQ=weights(8)
def finite(v):return v is not None and math.isfinite(float(v))
def quant(v,q):
    a=[float(x) for x in v if finite(x)]
    return float(np.quantile(a,q)) if a else None
def median(v):return quant(v,.5)
def monthly(rows,value=lambda r:1.):
    arr=np.zeros(24)
    for r in rows:arr[MONTHS.index(r['signal_month'])]+=value(r)
    return arr
def interval(values):
    v=np.asarray(values);v=v[np.isfinite(v)]
    return (float(np.quantile(v,.025)),float(np.quantile(v,.975)),len(v)) if len(v) else (None,None,0)
def ratio_ci(num,den,quarter=False):
    if quarter:
        num=num.reshape(8,3).sum(axis=1);den=den.reshape(8,3).sum(axis=1);w=WQ
    else:w=WM
    a=w@num;b=w@den
    return np.divide(a,b,out=np.full(REPS,np.nan),where=b>0)
def closed(rows):return [r for r in rows if r['status']=='CLOSED']
def stats(rows,total_winners=None):
    c=closed(rows);n=len(c);rs=[r['gross_R'] for r in c];initial=sum(r['outcome_group']=='INITIAL_STOP' for r in c)
    big=sum(r['large_winner_ge_2R'] for r in c)
    den=monthly(c);stop=monthly(c,lambda r:float(r['outcome_group']=='INITIAL_STOP'))
    ci=interval(ratio_ci(stop,den));rci=interval(ratio_ci(monthly(c,lambda r:r['gross_R']),den))
    months=len({r['signal_month'] for r in c})
    return dict(N=len(rows),CLOSED=n,OPEN=len(rows)-n,INITIAL_STOP=initial,initial_stop_share=initial/n if n else None,
      initial_stop_ci95_low=ci[0],initial_stop_ci95_high=ci[1],bootstrap_valid=ci[2],
      mean_gross_R=math.fsum(rs)/n if n else None,median_gross_R=median(rs),mean_R_ci95_low=rci[0],mean_R_ci95_high=rci[1],
      large_winners_ge_2R=big,large_winner_share=big/n if n else None,
      share_of_all_large_winners=big/total_winners if total_winners else None,
      median_MAE_R=median(r['MAE_executable_R0'] for r in rows),median_MFE_R=median(r['MFE_pre_stop_R0'] for r in rows),
      median_MFE_upper_R=median(r['MFE_observed_upper_R0'] for r in rows),
      MFE_guaranteed_ge_1R=sum(r['MFE_pre_stop_R0']>=1 for r in rows),
      MFE_guaranteed_ge_2R=sum(r['MFE_pre_stop_R0']>=2 for r in rows),
      median_giveback_R=median(r['giveback_R0'] for r in rows),
      first_favorable_observed=sum(r['first_favorable_observed'] for r in rows),
      first_favorable_not_observed=sum(r['first_favorable_status']=='NOT_OBSERVED' for r in rows),
      first_favorable_ambiguous=sum(r['first_favorable_status']=='AMBIGUOUS_EXIT_BAR' for r in rows),
      first_favorable_censored=sum(r['first_favorable_status']=='CENSORED' for r in rows),
      median_first_favorable_minutes_observed=median(r['first_favorable_minutes_bound'] for r in rows),
      median_first_favorable_execution_bar_observed=median(r['first_favorable_bar'] for r in rows),
      half_R_observed=sum(r['half_R_status']=='OBSERVED' for r in rows),
      half_R_not_observed=sum(r['half_R_status']=='NOT_OBSERVED' for r in rows),
      half_R_ambiguous=sum(r['half_R_status']=='AMBIGUOUS_EXIT_BAR' for r in rows),
      half_R_censored=sum(r['half_R_status']=='CENSORED' for r in rows),
      median_first_half_R_minutes_observed=median(r['first_half_R_minutes_bound'] for r in rows),
      median_first_half_R_execution_bar_observed=median(r['first_half_R_bar'] for r in rows),
      signal_months=months,evidence='SMALL' if n<20 or months<6 else 'DESCRIPTIVE')

def difference(high,low):
    h=closed(high);l=closed(low)
    hn=monthly(h);ln=monthly(l)
    hs=monthly(h,lambda r:float(r['outcome_group']=='INITIAL_STOP'));ls=monthly(l,lambda r:float(r['outcome_group']=='INITIAL_STOP'))
    effect=sum(hs)/len(h)-sum(ls)/len(l) if h and l else None
    ci=interval(ratio_ci(hs,hn)-ratio_ci(ls,ln));qci=interval(ratio_ci(hs,hn,True)-ratio_ci(ls,ln,True))
    return dict(high_n=len(h),low_n=len(l),high_initial=int(sum(hs)),low_initial=int(sum(ls)),risk_difference=effect,
      ci95_low=ci[0],ci95_high=ci[1],bootstrap_valid=ci[2],quarter_ci95_low=qci[0],quarter_ci95_high=qci[1],
      evidence='SMALL' if min(len(h),len(l))<20 or min(len({r['signal_month'] for r in h}),len({r['signal_month'] for r in l}))<6 else 'DESCRIPTIVE')

def standardized(rows,keys):
    strata=defaultdict(list)
    for r in closed(rows):strata[tuple(r[k] for k in keys)].append(r)
    common=[]
    for key,rs in sorted(strata.items()):
        h=[r for r in rs if r['breakout_atr']>=.5];l=[r for r in rs if r['breakout_atr']<.5]
        if h and l:common.append((key,h,l))
    if not common:return dict(strata=0,covered_n=0)
    hs=np.array([monthly(h,lambda r:float(r['outcome_group']=='INITIAL_STOP')) for _,h,l in common]);hn=np.array([monthly(h) for _,h,l in common])
    ls=np.array([monthly(l,lambda r:float(r['outcome_group']=='INITIAL_STOP')) for _,h,l in common]);ln=np.array([monthly(l) for _,h,l in common])
    def calc(w):
        a=w@hn.T;b=w@ln.T;x=w@hs.T;y=w@ls.T
        with np.errstate(divide='ignore',invalid='ignore'):
            v=np.divide(a*b,a+b,out=np.zeros_like(a),where=(a+b)>0)
            delta=np.divide(x,a,out=np.zeros_like(x),where=a>0)-np.divide(y,b,out=np.zeros_like(y),where=b>0)
            return np.divide((v*delta).sum(axis=1),v.sum(axis=1),out=np.full(len(w),np.nan),where=v.sum(axis=1)>0)
    ci=interval(calc(WM));qci=interval(calc(np.repeat(WQ,3,axis=1)))
    covered=sum(len(h)+len(l) for _,h,l in common);n=len(closed(rows))
    return dict(adjust_for='|'.join(keys),strata=len(common),all_strata=len(strata),covered_n=covered,all_closed=n,
      coverage_share=covered/n if n else None,risk_difference=float(calc(np.ones((1,24)))[0]),
      ci95_low=ci[0],ci95_high=ci[1],bootstrap_valid=ci[2],quarter_ci95_low=qci[0],quarter_ci95_high=qci[1],
      weighting='n_high*n_low/(n_high+n_low); overlapping strata only')

def analyze(entries,outcomes,post,execution,results,out):
    features={r['signal_id']:r for r in entries};data=[dict(features[r['signal_id']],**r) for r in outcomes]
    distributions=[];buckets=[];thresholds=[];breakdown=[];stability=[];examples=[];outsum=[];mechanics=[];strata=[];adjusted=[]
    for system in ('H1','M15'):
        rows=[r for r in data if r['system']==system];total=sum(r['large_winner_ge_2R'] for r in rows)
        groups={g:[r for r in rows if r['outcome_group']==g] for g in ('INITIAL_STOP','TRAILING_NEGATIVE','TRAILING_POSITIVE','TRAILING_ZERO','OPEN')}
        groups.update(ALL=rows,WINNERS=[r for r in closed(rows) if r['gross_R']>0],LOSERS=[r for r in closed(rows) if r['gross_R']<0],LARGE_WINNER_GE_2R=[r for r in rows if r['large_winner_ge_2R']])
        for g,rs in groups.items():outsum.append(dict(system=system,outcome=g,**stats(rs,total)))
        feature_names=FEATURES_COMMON+(FEATURES_H1 if system=='H1' else FEATURES_M15)
        for name in feature_names:
            vals=[r[name] for r in rows if finite(r[name])];q1=quant(vals,1/3);q2=quant(vals,2/3)
            thresholds.append(dict(system=system,feature=name,q1=q1,q2=q2,N=len(vals),method='Unsupervised development executed-entry terciles; no outcome used'))
            for g,rs in groups.items():
                values=[r[name] for r in rs if finite(r[name])]
                distributions.append(dict(system=system,feature=name,outcome=g,N=len(rs),nonmissing=len(values),missing=len(rs)-len(values),
                  p25=quant(values,.25),median=median(values),p75=quant(values,.75)))
            def label(r):
                if not finite(r[name]):return 'MISSING'
                return 'LOW' if r[name]<=q1 else 'MID' if r[name]<=q2 else 'HIGH'
            for bucket in ('LOW','MID','HIGH','MISSING'):
                rs=[r for r in rows if label(r)==bucket]
                buckets.append(dict(system=system,feature=name,bucket=bucket,q1=q1,q2=q2,**stats(rs,total)))
                fail=sorted((r for r in rs if r['outcome_group']=='INITIAL_STOP'),key=lambda r:(r['signal_time'],r['signal_id']))
                win=sorted((r for r in rs if r['large_winner_ge_2R']),key=lambda r:(r['signal_time'],r['signal_id']))
                if fail and win:
                    for kind,r in [('INITIAL_STOP',fail[0]),('LARGE_WINNER_GE_2R',win[0])]:
                        examples.append(dict(system=system,feature=name,bucket=bucket,kind=kind,signal_id=r['signal_id'],
                          value=r[name],gross_R=r['gross_R'],instrument=r['instrument'],direction=r['direction']))
            subsets=[('ALL','ALL',rows)]
            for key in ('instrument','direction','signal_year'):
                subsets.extend((key,str(v),[r for r in rows if r[key]==v]) for v in sorted({r[key] for r in rows}))
            subsets.extend(('leave_one_instrument_out',s,[r for r in rows if r['instrument']!=s]) for s in SYMBOLS)
            for dim,value,rs in subsets:
                high=[r for r in rs if label(r)=='HIGH'];low=[r for r in rs if label(r)=='LOW']
                stability.append(dict(system=system,feature=name,dimension=dim,value=value,**difference(high,low)))
        for dim,keys in [('instrument',('instrument',)),('direction',('direction',)),('year',('signal_year',)),('instrument_direction_year',('instrument','direction','signal_year'))]:
            partitions=defaultdict(list)
            for r in rows:partitions[tuple(r[k] for k in keys)].append(r)
            for values,rs in sorted(partitions.items()):breakdown.append(dict(system=system,dimension=dim,key='|'.join(map(str,values)),**stats(rs,total)))
        q1=quant([r['context_atr_ratio'] for r in rows],1/3);q2=quant([r['context_atr_ratio'] for r in rows],2/3)
        for r in rows:r['volatility_tercile']='LOW' if r['context_atr_ratio']<=q1 else 'MID' if r['context_atr_ratio']<=q2 else 'HIGH'
        for bucket in ('LT_0.5','GE_0.5'):
            rs=[r for r in rows if (r['breakout_atr']>=.5)==(bucket=='GE_0.5')]
            buckets.append(dict(system=system,feature='breakout_05_prespecified',bucket=bucket,q1=.5,q2=None,**stats(rs,total)))
        for dim,keys in [('ALL',()),('instrument',('instrument',)),('direction',('direction',)),('year',('signal_year',)),('volatility',('volatility_tercile',)),('instrument_direction_year_volatility',('instrument','direction','signal_year','volatility_tercile'))]:
            partitions=defaultdict(list)
            for r in rows:partitions[tuple(r[k] for k in keys)].append(r)
            for values,rs in sorted(partitions.items()):
                strata.append(dict(system=system,dimension=dim,key='|'.join(map(str,values)),vol_q1=q1,vol_q2=q2,
                  **difference([r for r in rs if r['breakout_atr']>=.5],[r for r in rs if r['breakout_atr']<.5])))
        for keys in [('instrument',),('direction',),('signal_year',),('volatility_tercile',),('instrument','direction','signal_year','volatility_tercile')]:
            adjusted.append(dict(system=system,**standardized(rows,keys)))
        for code,desc,pred in [
          ('A','INITIAL_STOP, guaranteed MFE<0.5R (includes ambiguous exit bars)',lambda r:r['A_low_follow_through']),
          ('A_STRICT','INITIAL_STOP, upper MFE<0.5R',lambda r:r['A_low_follow_through'] and r['MFE_observed_upper_R0']<.5),
          ('EARLY_ADVERSE','first Open/first survived Close adverse OR first4 adverse>=0.5R',lambda r:r['immediate_adverse_open'] or r['immediate_adverse_survived_close'] or r['adverse_half_R_first4']),
          ('E','negative trailing with positive guaranteed MFE',lambda r:r['E_negative_trailing_giveback'])]:
            rs=[r for r in rows if pred(r)];mechanics.append(dict(system=system,code=code,definition=desc,**stats(rs,total)))
    for filename,table in [('FEATURE_DISTRIBUTIONS.csv',distributions),('FEATURE_BUCKETS.csv',buckets),('FEATURE_THRESHOLDS.csv',thresholds),
      ('INSTRUMENT_DIRECTION.csv',breakdown),('STABILITY.csv',stability),('CONFLICT_EXAMPLES.csv',examples),('OUTCOME_SUMMARY.csv',outsum),
      ('MECHANICS.csv',mechanics),('BREAKOUT_05_STRATA.csv',strata),('BREAKOUT_05_STANDARDIZED.csv',adjusted)]:csvout(out/filename,table)
    post_groups=defaultdict(list)
    for r in post:post_groups[(r['system'],r['window_full_next_trading_days'])].append(r)
    postsummary=[]
    outcome_index={r['signal_id']:r for r in outcomes}
    for (system,days),rs in sorted(post_groups.items()):
        complete=[r for r in rs if r['status']=='COMPLETE_OBSERVED_DATE_WINDOW']
        den=monthly([outcome_index[r['signal_id']] for r in complete])
        numerator=monthly([outcome_index[r['signal_id']] for r in complete if r['RECOVERY_ENTRY_status']=='OBSERVED'])
        ci=interval(ratio_ci(numerator,den))
        first_num=monthly([outcome_index[r['signal_id']] for r in complete if r['recovery_vs_adverse_1p5R_order'] in ('RECOVERY_FIRST','RECOVERY_ONLY_OBSERVED')])
        fci=interval(ratio_ci(first_num,den))
        postsummary.append(dict(system=system,days=days,N=len(rs),complete=len(complete),censored=len(rs)-len(complete),
          recovery_observed=sum(r['RECOVERY_ENTRY_status']=='OBSERVED' for r in complete),
          recovery_share=sum(numerator)/sum(den) if sum(den) else None,recovery_ci95_low=ci[0],recovery_ci95_high=ci[1],
          recovery_before_or_without_adverse_share=sum(first_num)/sum(den) if sum(den) else None,
          recovery_before_ci95_low=fci[0],recovery_before_ci95_high=fci[1],
          recovery_first=sum(r['recovery_vs_adverse_1p5R_order']=='RECOVERY_FIRST' for r in complete),
          recovery_only=sum(r['recovery_vs_adverse_1p5R_order']=='RECOVERY_ONLY_OBSERVED' for r in complete),
          adverse_first=sum(r['recovery_vs_adverse_1p5R_order']=='ADVERSE_FIRST' for r in complete),
          ambiguous=sum(r['recovery_vs_adverse_1p5R_order']=='AMBIGUOUS_SAME_BAR' for r in complete)))
    csvout(out/'POST_STOP_SUMMARY.csv',postsummary)
    execution_index={r['signal_id']:r for r in execution}
    execution_summary=[]
    for system in ('H1','M15'):
        rs=[r for r in outcomes if r['system']==system]
        for group in ('ALL','INITIAL_STOP','TRAILING_NEGATIVE','TRAILING_POSITIVE','OPEN','LARGE_WINNER_GE_2R'):
            selected=rs if group=='ALL' else [r for r in rs if r['large_winner_ge_2R']] if group=='LARGE_WINNER_GE_2R' else [r for r in rs if r['outcome_group']==group]
            values=[execution_index[r['signal_id']]['signed_next_open_gap_atr'] for r in selected]
            execution_summary.append(dict(system=system,outcome=group,N=len(values),p25=quant(values,.25),median=median(values),p75=quant(values,.75),
              positive=sum(v>0 for v in values),negative=sum(v<0 for v in values),zero=sum(v==0 for v in values),
              availability='EXECUTION_OPEN_AFTER_SIGNAL' if system=='M15' else 'SIGNAL_CLOSE',signal_time_predictor=False))
    csvout(out/'EXECUTION_DIAGNOSTIC_SUMMARY.csv',execution_summary)
    # Original realized calendar only. No hypothetical removal or alternative occupancy.
    calendar=[]
    for system in ('H1','M15'):
        for month in MONTHS:
            ts=[r for r in outcomes if r['system']==system and r['status']=='CLOSED' and r['exit_time'].strftime('%Y-%m')==month]
            calendar.append(dict(system=system,month_msk=month,closed=len(ts),gross_R=math.fsum(r['gross_R'] for r in ts),
              initial_stop=sum(r['outcome_group']=='INITIAL_STOP' for r in ts),negative_trailing=sum(r['outcome_group']=='TRAILING_NEGATIVE' for r in ts),
              initial_stop_R=math.fsum(r['gross_R'] for r in ts if r['outcome_group']=='INITIAL_STOP'),
              negative_trailing_R=math.fsum(r['gross_R'] for r in ts if r['outcome_group']=='TRAILING_NEGATIVE'),
              positive_R=math.fsum(r['gross_R'] for r in ts if r['gross_R']>0),
              large_winners_ge_2R=sum(r['large_winner_ge_2R'] for r in ts),
              status='OBSERVED_REALIZED_ONLY_NO_FILTER_SIMULATION'))
    csvout(out/'MONTHLY_BASELINE.csv',calendar)
    js(out/'UNCERTAINTY.json',dict(method='Paired calendar-month cluster percentile bootstrap, all instruments together',
      repetitions=REPS,seed=RNG_SEED,months=MONTHS,quarter_sensitivity='8 calendar quarters, same seed',
      intervals='95% descriptive, no multiplicity adjustment, no causality or future stability claim',
      small_rule='Each compared group <20 closed OR <6 entry months => SMALL',
      thresholds='Unsupervised executed-entry development quantiles, not optimized; 0.5 ATR predeclared'))
