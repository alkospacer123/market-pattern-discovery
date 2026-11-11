"""Separate scalar/stdlib verifier. Same author; no external-human audit claim.

Feature formulas are recomputed from pinned raw prefixes, without features.py,
primary indicators or primary outcome code. EWM algorithm follows PR518 verifier.
"""
import csv,io,json,math,subprocess
from collections import defaultdict,deque
from datetime import datetime,timedelta
from decimal import Decimal
from statistics import median
from zoneinfo import ZoneInfo
from support import HERE,ROOT,DATA,SYMBOLS,csvin,js

TZ=ZoneInfo('Europe/Moscow');END=datetime(2025,1,1,tzinfo=TZ);NAN=float('nan')
class EWM:
    def __init__(self,a,n):self.a=a;self.n=n;self.x=NAN;self.w=1.;self.count=0
    def update(self,v):
        valid=math.isfinite(v);self.count+=valid
        if math.isfinite(self.x):
            self.w*=1-self.a
            if valid:
                if self.x!=v:self.x=(self.w*self.x+self.a*v)/(self.w+self.a)
                self.w=1.
        elif valid:self.x=v
        return self.x if self.count>=self.n else NAN

def parse(system,symbol,baseline=True):
    commit={'H1':'50f1fd2178c18b7ab3bd969be82ad01f47a34745','M15':'f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8'}[system]
    step=timedelta(minutes=60 if system=='H1' else 15)
    bounds=None
    if system=='H1' and baseline:
        with (ROOT/'TradingSystemLab/results/post_v3_analysis/stage5_structural_validation/canonical_lifecycle_registry.csv').open() as h:
            bounds=next(r for r in csv.DictReader(h) if r['generation']=='v3_perpetual' and r['strategy']=='T3' and r['timeframe']=='H1' and r['lifecycle']=='baseline' and r['instrument']==symbol)
    p=subprocess.Popen(['git','-C',str(DATA),'show',commit+f':forever/{symbol}/{symbol}_{system}.csv'],stdout=subprocess.PIPE)
    rows=[]
    for r in csv.DictReader(io.TextIOWrapper(p.stdout),delimiter=';'):
        at=datetime.fromisoformat(r['Datetime']).replace(tzinfo=TZ)+step
        if at>=END:break
        if bounds and not datetime.fromisoformat(bounds['start_timestamp'])<=at<=datetime.fromisoformat(bounds['end_timestamp']):continue
        rows.append(dict(at=at,**{k:float(r[k]) for k in ('Open','High','Low','Close')}))
    if p.poll() is None:p.terminate()
    p.wait()
    return rows

def indicators(raw,period):
    a=EWM(1/14,14);p=EWM(1/14,14);m=EWM(1/14,14);ad=EWM(1/14,14);em=EWM(2/(period+1),period)
    last=None;eh=[];ah=deque(maxlen=20);out=[]
    for b in raw:
        tr=max(b['High']-b['Low'],abs(b['High']-last['Close']),abs(b['Low']-last['Close'])) if last else b['High']-b['Low']
        av=a.update(tr);u=b['High']-last['High'] if last else NAN;d=last['Low']-b['Low'] if last else NAN
        pv=p.update(u if u>0 and u>d else 0.);mv=m.update(d if d>0 and d>u else 0.)
        pd=100*pv/av if av else NAN;md=100*mv/av if av else NAN
        dx=100*abs(pd-md)/(pd+md) if pd+md else NAN
        ax=ad.update(dx);ev=em.update(b['Close']);slope=ev-eh[-5] if len(eh)>=5 else NAN
        eh.append(ev);ah.append(av);mean=sum(ah)/20 if len(ah)==20 else NAN
        out.append(dict(b,ATR=av,EMA=ev,Slope=slope,ADX=ax,ATRRatio=av/mean if mean else NAN))
        last=b
    return out

def independent_features(system,symbol):
    raw=parse(system,symbol);low=indicators(raw,100);groups=defaultdict(list)
    for b in raw:groups[b['at'].date()].append(b)
    high=[];step=timedelta(minutes=60 if system=='H1' else 15)
    for day,bs in sorted(groups.items()):
        for i in range(0,len(bs),4):
            q=bs[i:i+4]
            if len(q)<4:continue
            if system=='M15' and any(q[j]['at']-q[j-1]['at']!=step for j in (1,2,3)):continue
            high.append(dict(at=q[-1]['at'],Open=q[0]['Open'],Close=q[-1]['Close'],High=max(x['High'] for x in q),Low=min(x['Low'] for x in q)))
    high=indicators(high,100 if system=='H1' else 75);pointer=-1;out=[]
    for i,b in enumerate(low):
        while pointer+1<len(high) and high[pointer+1]['at']<=b['at']:pointer+=1
        if pointer<0 or i<20:continue
        h=high[pointer];prior=raw[i-20:i];ph=max(x['High'] for x in prior);pl=min(x['Low'] for x in prior)
        sign=0
        if h['ADX']>20 and h['ATRRatio']>1:
            if h['Close']>h['EMA'] and h['Slope']>0 and b['Close']>ph:sign=1
            elif h['Close']<h['EMA'] and h['Slope']<0 and b['Close']<pl:sign=-1
        if not sign:continue
        a=b['ATR'];spread=b['High']-b['Low'];location=(b['Close']-b['Low'])/spread if spread else NAN
        life='baseline' if system=='H1' else 'history_2023_2026'
        ident='|'.join((system,life,'',symbol,b['at'].isoformat(),'LONG' if sign==1 else 'SHORT'))
        r=dict(signal_id=ident,context_available_at=h['at'].isoformat(),feature_available_at=b['at'].isoformat(),
          signal_time=b['at'].isoformat(),signal_year=b['at'].year,signal_month=b['at'].strftime('%Y-%m'),
          direction='LONG' if sign==1 else 'SHORT',signal_close=b['Close'],prior_donchian=ph if sign==1 else pl,
          context_ema=h['EMA'],context_slope=h['Slope'],context_close=h['Close'],context_direction='LONG' if h['Slope']>0 else 'SHORT',
          breakout_atr=sign*(b['Close']-(ph if sign==1 else pl))/a,range_atr=spread/a,
          body_abs_atr=abs(b['Close']-b['Open'])/a,body_signed_atr=sign*(b['Close']-b['Open'])/a,
          close_location=location,directional_close_location=location if sign==1 else 1-location,
          atr=a,atr_ratio_cross_day=b['ATRRatio'],
          prior_move4_atr_cross_day=sign*(raw[i-1]['Close']-raw[i-5]['Close'])/a,
          prior_move20_atr_cross_day=sign*(raw[i-1]['Close']-raw[i-21]['Close'])/a if i>=21 else NAN,
          prior_pullback20_atr_cross_day=sign*((ph if sign==1 else pl)-raw[i-1]['Close'])/a,
          price_context_ema_atr=sign*(b['Close']-h['EMA'])/a,
          context_adx=h['ADX'],context_slope_atr=sign*h['Slope']/h['ATR'],context_atr=h['ATR'],
          context_atr_ratio=h['ATRRatio'],context_age_minutes=(b['at']-h['at']).total_seconds()/60)
        if system=='H1':r.update(price_h1_ema100_atr=sign*(b['Close']-b['EMA'])/a,h1_slope5_atr=sign*b['Slope']/a,h1_adx=b['ADX'])
        else:r.update(price_context_ema_context_atr=sign*(b['Close']-h['EMA'])/h['ATR'],session_minutes=b['at'].hour*60+b['at'].minute-600,signal_hour_msk=b['at'].hour)
        out.append(r)
    return out,raw

def verify(out):
    fields=0;maxerror=0.;bars={};fresh={}
    def equal(e,a,ctx):
        nonlocal fields,maxerror
        fields+=1
        if isinstance(e,(int,float)) and not isinstance(e,bool):
            if not math.isfinite(e):assert a=='',(ctx,e,a)
            else:
                error=abs(float(a)-e);maxerror=max(maxerror,error)
                assert error<=1e-8,(ctx,e,a,error)
        elif isinstance(e,bool):assert str(e)==a,(ctx,e,a)
        else:assert str(e)==a,(ctx,e,a)
    for system in ('H1','M15'):
        expected=[]
        for symbol in SYMBOLS:
            rows,raw=independent_features(system,symbol);expected.extend(rows);bars[(system,symbol)]=raw
        actual=csvin(out/f'ENTRY_FEATURES_{system}.csv')
        assert [r['signal_id'] for r in expected]==[r['signal_id'] for r in actual],('SIGNAL_UNIVERSE',system)
        for e,a in zip(expected,actual):
            for key,v in e.items():equal(v,a[key],(e['signal_id'],key))
            assert datetime.fromisoformat(a['context_available_at'])<=datetime.fromisoformat(a['signal_time'])<END
            fresh[e['signal_id']]=e
    feature_fields=fields
    allout=[]
    for system in ('H1','M15'):
        outcomes=csvin(out/f'OUTCOME_GROUPS_{system}.csv');allout.extend(outcomes)
        for r in outcomes:
            sgn=1 if r['direction']=='LONG' else -1;entry=float(r['entry_price']);risk=float(r['initial_risk_price'])
            if r['status']=='CLOSED':
                price=Decimal(r['exit_price']);rr=sgn*(price-Decimal(r['entry_price']))/Decimal(r['initial_risk_price'])
                equal(float(rr),r['gross_R'],('RETURN',r['signal_id']))
                group='INITIAL_STOP' if r['exit_reason']=='INITIAL_STOP' else 'TRAILING_NEGATIVE' if rr<0 else 'TRAILING_POSITIVE' if rr>0 else 'TRAILING_ZERO'
            else:group='OPEN'
            equal(group,r['outcome_group'],('OUTCOME',r['signal_id']))
            equal(r['status']=='CLOSED' and float(r['gross_R'])>=2,r['large_winner_ge_2R'],('BIG',r['signal_id']))
            raw=bars[(system,r['instrument'])];start=datetime.fromisoformat(r['entry_time']);end=datetime.fromisoformat(r['exit_time']) if r['exit_time'] else raw[-1]['at']
            after=[b for b in raw if start<b['at']<=end];mfe=mae=upper=uppermae=0.;first=half=None;early=False;advopen=advclose=False;hbar=None;hprecision=None;fbar=None;fprecision=None
            step=timedelta(minutes=60 if system=='H1' else 15)
            for n,b in enumerate(after,1):
                last=r['status']=='CLOSED' and b['at']==end
                orr=sgn*(b['Open']-entry)/risk
                good=max(0.,sgn*((b['High'] if sgn>0 else b['Low'])-entry)/risk)
                bad=max(0.,-sgn*((b['Low'] if sgn>0 else b['High'])-entry)/risk)
                mfe=max(mfe,max(0.,orr),good if not last else 0.)
                mae=max(mae,max(0.,-orr),max(0.,-float(r['gross_R'])) if last else bad)
                upper=max(upper,good);uppermae=max(uppermae,bad)
                if first is None and (orr>0 or not last and good>0):
                    first=b['at']-step if orr>0 else b['at'];fbar=n;fprecision='OPEN' if orr>0 else 'BAR_INTERVAL'
                if half is None and (orr>=.5 or not last and good>=.5):
                    half=b['at']-step if orr>=.5 else b['at'];hbar=n;hprecision='OPEN' if orr>=.5 else 'BAR_INTERVAL'
                if n==1:advopen=orr<0;advclose=not last and sgn*(b['Close']-entry)<0
                if n<=4 and (max(0.,-orr)>=.5 or not last and bad>=.5 or last and float(r['gross_R'])<=-.5):early=True
            for key,v in dict(MFE_pre_stop_R0=mfe,MAE_executable_R0=mae,MFE_observed_upper_R0=upper,MAE_observed_upper_R0=uppermae,
              first_favorable_time_bound=first.isoformat() if first else '',first_favorable_observed=first is not None,
              first_favorable_time_lower=(first-step if fprecision=='BAR_INTERVAL' else first).isoformat() if first else '',
              first_favorable_bar=fbar if fbar else '',first_favorable_precision=fprecision or '',
              first_favorable_minutes_bound=(first-start).total_seconds()/60 if first else '',
              first_favorable_status='OBSERVED' if first else 'CENSORED' if r['status']=='OPEN' else 'AMBIGUOUS_EXIT_BAR' if upper>0 else 'NOT_OBSERVED',
              first_half_R_time_bound=half.isoformat() if half else '',first_half_R_bar=hbar if hbar is not None else '',
              first_half_R_precision=hprecision or '',adverse_half_R_first4=early,immediate_adverse_open=advopen,
              first_half_R_minutes_bound=(half-start).total_seconds()/60 if half else '',
              half_R_status='OBSERVED' if half else 'CENSORED' if r['status']=='OPEN' else 'AMBIGUOUS_EXIT_BAR' if mfe<.5<=upper else 'NOT_OBSERVED',
              A_low_follow_through=r['status']=='CLOSED' and r['exit_reason']=='INITIAL_STOP' and mfe<.5,
              A_exit_bar_ambiguous=mfe<.5<=upper,E_negative_trailing_giveback=group=='TRAILING_NEGATIVE' and mfe>0,
              giveback_R0=max(0.,mfe-float(r['gross_R'])) if r['status']=='CLOSED' else '',
              immediate_adverse_survived_close=advclose).items():equal(v,r[key],('PATH',r['signal_id'],key))
    path_fields=fields-feature_fields
    # Reopen POST_STOP and raw prefixes independently. No primary forensics import.
    post=csvin(out/'POST_STOP.csv');post_checks=0
    byid={r['signal_id']:r for r in allout}
    for r in csvin(out/'EXECUTION_DIAGNOSTICS.csv'):
        t=byid[r['signal_id']];f=fresh[r['signal_id']];sign=1 if t['direction']=='LONG' else -1
        equal(sign*(float(t['entry_price'])-f['signal_close'])/f['atr'],r['signed_next_open_gap_atr'],('EXECUTION_GAP',r['signal_id']))
        if t['system']=='M15':
            equal('EXECUTION_OPEN_AFTER_SIGNAL',r['availability'],('GAP_AVAILABILITY',r['signal_id']))
            equal(False,r['signal_predictor'],('GAP_NOT_SIGNAL_PREDICTOR',r['signal_id']))
    histories={(s,sym):parse(s,sym,False) for s in ('H1','M15') for sym in SYMBOLS}
    for r in post:
        t=byid[r['signal_id']];system=t['system'];step=timedelta(minutes=60 if system=='H1' else 15)
        raw=histories[(system,t['instrument'])];stop=datetime.fromisoformat(t['exit_time']);stopday=(stop-step).date()
        dates=sorted({(b['at']-step).date() for b in raw if (b['at']-step).date()>stopday})
        k=int(r['window_full_next_trading_days']);complete=len(dates)>k;target=dates[k-1] if len(dates)>=k else None
        after=[b for b in raw if b['at']>stop and (target is None or (b['at']-step).date()<=target)]
        equal('COMPLETE_OBSERVED_DATE_WINDOW' if complete else 'CENSORED',r['status'],('POST_STATUS',r['signal_id'],k))
        equal(len(after),r['observed_bars'],('POST_BARS',r['signal_id'],k))
        sign=1 if t['direction']=='LONG' else -1;e=float(t['entry_price']);risk=float(t['initial_risk_price']);first={}
        levels={0.:'RECOVERY_ENTRY',.5:'FAVORABLE_0p5R',1.:'FAVORABLE_1R',1.5:'FAVORABLE_1p5R',2.:'FAVORABLE_2R',-1.5:'ADVERSE_1p5R',-2.:'ADVERSE_2R'}
        for i,b in enumerate(after):
            lo=min(sign*(b['Low']-e)/risk,sign*(b['High']-e)/risk);hi=max(sign*(b['Low']-e)/risk,sign*(b['High']-e)/risk);o=sign*(b['Open']-e)/risk
            for level,name in levels.items():
                if name not in first and (hi>=level if level>=0 else lo<=level):
                    opening=o>=level if level>=0 else o<=level
                    first[name]=(i,0 if opening else 1,b['at']-step if opening else b['at'])
        for name in levels.values():
            v=first.get(name);equal('OBSERVED' if v else 'NOT_OBSERVED' if complete else 'CENSORED',r[name+'_status'],('POST_LEVEL',r['signal_id'],k,name));post_checks+=1
            equal(v[2].isoformat() if v else '',r[name+'_first_time_bound'],('POST_TIME',r['signal_id'],k,name))
        a=first.get('RECOVERY_ENTRY');b=first.get('ADVERSE_1p5R')
        order=('RECOVERY_FIRST' if a[:2]<b[:2] else 'ADVERSE_FIRST' if a[:2]>b[:2] else 'AMBIGUOUS_SAME_BAR') if a and b else 'RECOVERY_ONLY_OBSERVED' if a else 'ADVERSE_ONLY_OBSERVED' if b else 'NEITHER_OBSERVED'
        equal(order,r['recovery_vs_adverse_1p5R_order'],('POST_ORDER',r['signal_id'],k))
    # Fresh CSV + Decimal calendar check, including explicit UTC-to-MSK boundary.
    assert datetime.fromisoformat('2024-12-31T21:00:00+00:00').astimezone(TZ)==END
    assert datetime.fromisoformat('2024-12-31T20:59:00+00:00').astimezone(TZ)<END
    calendar=csvin(out/'MONTHLY_BASELINE.csv')
    for r in calendar:
        ts=[t for t in allout if t['system']==r['system'] and t['status']=='CLOSED' and datetime.fromisoformat(t['exit_time']).astimezone(TZ).strftime('%Y-%m')==r['month_msk']]
        equal(len(ts),r['closed'],('MONTH',r['system'],r['month_msk']))
        equal(float(sum((Decimal(t['gross_R']) for t in ts),Decimal(0))),r['gross_R'],('MONTH_R',r['system'],r['month_msk']))
    for r in csvin(out/'BREAKOUT_05_STANDARDIZED.csv'):
        rows=[dict(fresh[t['signal_id']],**t) for t in allout if t['system']==r['system'] and t['status']=='CLOSED']
        vs=sorted(float(x['context_atr_ratio']) for x in rows+[dict(fresh[t['signal_id']],**t) for t in allout if t['system']==r['system'] and t['status']=='OPEN'])
        def q(p):
            pos=(len(vs)-1)*p;i=int(pos);return vs[i]+(vs[min(i+1,len(vs)-1)]-vs[i])*(pos-i)
        q1=q(1/3);q2=q(2/3)
        grouped=defaultdict(list);keys=r['adjust_for'].split('|')
        for t in rows:
            t['volatility_tercile']='LOW' if float(t['context_atr_ratio'])<=q1 else 'MID' if float(t['context_atr_ratio'])<=q2 else 'HIGH'
            grouped[tuple(str(t[k]) for k in keys)].append(t)
        numerator=den=0.;covered=0;ns=0
        for rs in grouped.values():
            high=[t for t in rs if float(t['breakout_atr'])>=.5];low=[t for t in rs if float(t['breakout_atr'])<.5]
            if not high or not low:continue
            n=len(high);m=len(low);w=n*m/(n+m)
            numerator+=w*(sum(t['outcome_group']=='INITIAL_STOP' for t in high)/n-sum(t['outcome_group']=='INITIAL_STOP' for t in low)/m);den+=w;covered+=n+m;ns+=1
        equal(numerator/den,r['risk_difference'],('STANDARDIZED',r['system'],r['adjust_for']))
        equal(covered,r['covered_n'],('STRATA_COVERAGE',r['system'],r['adjust_for']));equal(ns,r['strata'],('STRATA_N',r['system'],r['adjust_for']))
    receipt=dict(status='PASS',independence='Separate scalar algorithm, same author; no independent human or separate-agent review',
      feature_fields=feature_fields,outcome_path_fields=path_fields,fields_checked=fields,max_abs_numeric_error=maxerror,
      post_stop_threshold_checks=post_checks,calendar_rows=len(calendar),signal_rows=len(fresh),
      methods='Fresh stdlib pinned-prefix parser, independent EWM/aggregation/signals/features, stop-first bounds, post-stop levels/order, Decimal returns and MSK calendar, direct stratification',
      locked_numeric_rows=0)
    js(out/'INDEPENDENT_VERIFICATION.json',receipt)
    return receipt

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--output',type=__import__('pathlib').Path,required=True);a=p.parse_args();print(json.dumps(verify(a.output)))
