"""Two separate causal engines. Frozen features are reused, never trade CSV inputs."""
import importlib.util, math, sys
from datetime import timedelta
import numpy as np
import pandas as pd
from common import *

sys.path.insert(0,str(ROOT))
from TradingSystemLab.core.data_loader import DataLoader
from TradingSystemLab.strategies.trend.T3_MTF_Trend import T3Parameters,T3MTFTrend

def m15_module():
    path=ROOT/'IntradayLab/t3_m15_t1_entry_retest_v1/primary.py'
    spec=importlib.util.spec_from_file_location('frozen_t1_primary',path);mod=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=mod;spec.loader.exec_module(mod);return mod

def h1_inputs(data):
    reg=pd.read_csv(ROOT/'TradingSystemLab/results/post_v3_analysis/stage5_structural_validation/canonical_lifecycle_registry.csv',keep_default_na=False)
    reg=reg[(reg.generation=='v3_perpetual')&(reg.strategy=='T3')&(reg.timeframe=='H1')&reg.instrument.isin(SYMBOLS)]
    params=T3Parameters(stop_atr=2.5);strategy=T3MTFTrend(params);result=[]
    raw={s:DataLoader.close_index(DataLoader(forbid_true_oos=False).load_csv(data/f'forever/{s}/{s}_H1.csv'),'1h') for s in SYMBOLS}
    for r in reg.sort_values(['lifecycle','fold_id','instrument']).to_dict('records'):
        s=r['instrument'];f=raw[s].loc[r['start_timestamp']:r['end_timestamp']].copy()
        low,high=strategy.calculate_indicators(f,DataLoader.h4_from_h1(f))
        regime=pd.Series([strategy.regime(x) for _,x in high.iterrows()],index=high.index,dtype=object)
        aligned=regime.reindex(low.index,method='ffill')
        sig=np.select([(aligned=='LONG')&(low.Close>low.PriorHigh),(aligned=='SHORT')&(low.Close<low.PriorLow)],[1,-1],default=0)
        bars=[]
        for (at,row),sign in zip(low.iterrows(),sig):
            bars.append(dict(at=at,Open=float(row.Open),High=float(row.High),Low=float(row.Low),Close=float(row.Close),ATR=float(row.ATR),Signal=int(sign)))
        result.append(dict(system='H1',instrument=s,lifecycle=r['lifecycle'],fold_id=r['fold_id'],bars=bars,frame=f))
    return result

def m15_inputs(data):
    mod=m15_module();return [dict(system='M15',instrument=s,lifecycle='history_2023_2026',fold_id='',bars=mod.features(mod.load(data/f'forever/{s}/{s}_M15.csv'))) for s in SYMBOLS]

def h1_replay(stream,variant):
    s=stream['instrument'];life=stream['lifecycle'];fold=stream['fold_id'];q=None
    trades=[];marks=[];trace=[];signals=[];realized=0.;c1=0.;seq=0
    for i,b in enumerate(stream['bars']):
        at=b['at']
        if q:
            before=q['_realized'];remaining=q['_remaining']
            if q['_triggered'] and not q['_activated'] and at!=q['trigger_bar_time']:
                q['_activated']=True;q['trail1_activation_time']=at
                q['_stop']=max(q['_stop'],q['_stored']) if q['_side']==1 else min(q['_stop'],q['_stored'])
            old=q['_stop'];done=protect_and_tp(q,b)
            realized+=q['_realized']-before;c1+=(remaining-q['_remaining'])*.001/q['initial_risk_price']
            ev=dict(at=at,trade_id=q['trade_id'],stop_entering=old,stop_hit=done,
                    remaining_before=remaining,remaining_after=q['_remaining'],partial_executed=q['partial_executed'])
            if done:
                q['bars_held']=q['_held']+1;trades.append(public(q));q=None
            else:
                q['_held']+=1
                q['_extreme']=max(q['_extreme'],b['High']) if q['_side']==1 else min(q['_extreme'],b['Low'])
                candidate=q['_extreme']-q['_side']*3*b['ATR']
                reached=b['High']>=q['entry_price']+q['initial_risk_price'] if q['_side']==1 else b['Low']<=q['entry_price']-q['initial_risk_price']
                if not q['_triggered'] and reached:
                    q['_triggered']=True;q['trigger_bar_time']=at;q['_stored']=candidate
                    q['candidate_already_looser']=q['_side']*(candidate-old)<=0
                if q['_activated']:
                    q['_stop']=max(old,candidate) if q['_side']==1 else min(old,candidate)
                ev.update(stop_after=q['_stop'],candidate=candidate,triggered=q['_triggered'],activated=q['_activated'],stored=q['_stored'])
            trace.append(ev)
        if b['Signal'] and math.isfinite(b['ATR']):
            accepted=q is None
            signals.append(dict(at=at,side=b['Signal'],accepted=accepted,occupied_trade_id=q['trade_id'] if q else None))
            if accepted:
                seq+=1;entry=b['Close'];initial=entry-b['Signal']*2.5*b['ATR']
                q=new_position('H1',s,life,fold,f'T3-H1-{s}-{seq:06d}',at,entry,initial,b['Signal'],variant,i)
                c1+=.001/q['initial_risk_price']
        marks.append(mark(q,b,realized,c1))
    if q:
        q.update(last_mark_time=b['at'],last_mark_price=b['Close'],gross_R=None,cost_R=None,net_R_C1=None)
        trades.append(public(q))
    return dict(trades=trades,marks=marks,trace=trace,signals=signals)

def m15_replay(stream,variant):
    s=stream['instrument'];q=None;pending=None;prev=None;closed=0
    trades=[];marks=[];trace=[];signals=[];realized=0.
    for i,b in enumerate(stream['bars']):
        at=b['at']
        if pending:
            signal,ix,row=pending
            if at==signal['at']+timedelta(minutes=15):
                entry=b['Open'];initial=entry-signal['Signal']*2*signal['ATR']
                q=new_position('M15',s,stream['lifecycle'],'',row['trade_id'],signal['at'],entry,initial,signal['Signal'],variant,ix)
                q.update(signal_time=signal['at'],signal_close=signal['Close'],ATR=signal['ATR'],H1AvailableAt=signal['H1AvailableAt'],
                         breakout_level=signal['PriorHigh'] if q['_side']==1 else signal['PriorLow'],_lo=entry,_hi=entry,_updates=0,_gaps=0)
                row.update(entry_accepted=True,reason='EXECUTED_NEXT_OPEN',entry_price=entry,initial_stop=initial,execution_bar_close=at)
            else:row.update(reason='MISSING_ADJACENT_OPEN',next_observed_close=at)
            pending=None
        exited=None
        if q:
            old=q['_stop'];before=q['_realized'];remaining=q['_remaining']
            q['_gaps']+=int(bool(prev and at-prev['at']>timedelta(minutes=15)))
            done=protect_and_tp(q,b);realized+=q['_realized']-before
            ev=dict(at=at,trade_id=q['trade_id'],stop_entering=old,stop_hit=done,remaining_before=remaining,remaining_after=q['_remaining'],partial_executed=q['partial_executed'])
            if done:
                q.update(bars_held=i-q['_index'],trailing_updates=q['_updates'],observed_gaps_exposed=q['_gaps'],
                    holding_minutes=(at-q['signal_time']).total_seconds()/60,
                    MFE_R=max(0.,q['_hi']-q['entry_price'] if q['_side']==1 else q['entry_price']-q['_lo'])/q['initial_risk_price'],
                    MAE_R=max(0.,q['entry_price']-q['_lo'] if q['_side']==1 else q['_hi']-q['entry_price'],q['_side']*(q['entry_price']-q['exit_price']))/q['initial_risk_price'],
                    exit_type='INITIAL_STOP' if old==q['initial_stop_price'] else 'RATCHETED_STOP')
                exited=q['trade_id'];trades.append(public(q));q=None;closed+=1
            else:
                q['_hi']=max(q['_hi'],b['High']);q['_lo']=min(q['_lo'],b['Low'])
                q['_extreme']=q['_hi'] if q['_side']==1 else q['_lo']
                candidate=q['_extreme']-q['_side']*3.5*b['ATR']
                if q['_side']*(candidate-old)>0:q['_stop']=candidate;q['_updates']+=1
                ev.update(stop_after=q['_stop'],candidate=candidate)
            trace.append(ev)
        if b['Signal'] and math.isfinite(b['ATR']):
            allowed=600<=at.hour*60+at.minute<1080;busy=q is not None;accepted=allowed and not busy
            tid=f'T3-M15-{dict(USDRUBF="Si",CNYRUBF="CNY").get(s,s)}-{closed+1:06d}' if accepted else None
            row=dict(at=at,side=b['Signal'],trade_id=tid,entry_accepted=False,
                occupied_trade_id=q['trade_id'] if busy else None,same_close_exit_trade_id=exited,
                reason='PENDING_NEXT_OPEN' if accepted else 'OUTSIDE_T1_AND_OCCUPIED' if busy and not allowed else 'POSITION_OCCUPIED' if busy else 'OUTSIDE_T1')
            signals.append(row)
            if accepted:pending=(b,i,row)
        marks.append(mark(q,b,realized,0.));prev=b
    if pending:pending[2]['reason']='UNRESOLVED_END_OF_DATA'
    if q:
        q.update(last_mark_time=b['at'],last_mark_price=b['Close'],gross_R=None,cost_R=None,net_R_C1=None)
        trades.append(public(q))
    return dict(trades=trades,marks=marks,trace=trace,signals=signals)

def replay(stream,variant):
    r=(h1_replay if stream['system']=='H1' else m15_replay)(stream,variant)
    meta={k:stream[k] for k in ('system','instrument','lifecycle','fold_id')}
    for name in ('marks','trace','signals'):r[name]=[{**meta,'variant':variant,**x} for x in r[name]]
    return r
