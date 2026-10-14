"""New dataframe computation and object state machine for exactly two entries.

Specification transcribed from pinned execution_sensitivity_v1, without importing
its engine or journals. All stops are settled before completed-bar updates.
"""
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
import math
import numpy as np
import pandas as pd

STEP=timedelta(minutes=15)
SYMBOLS=('USDRUBF','CNYRUBF','GLDRUBF','IMOEXF')
MODES=('SIGNAL_CLOSE','NEXT_OPEN')

def load(path):
    frame=pd.read_csv(path,sep=';',float_precision='round_trip')
    assert list(frame)==['Ticker','Datetime','Open','High','Low','Close','Volume']
    frame.index=pd.DatetimeIndex(pd.to_datetime(frame.pop('Datetime'))).tz_localize('Europe/Moscow')+STEP
    assert frame.index.is_monotonic_increasing and not frame.index.has_duplicates
    assert (frame.Ticker==Path(path).parent.name).all()
    frame=frame.drop(columns='Ticker')
    assert np.isfinite(frame.to_numpy()).all()
    assert (frame.High>=frame[['Open','Low','Close']].max(axis=1)).all()
    assert (frame.Low<=frame[['Open','High','Close']].min(axis=1)).all()
    assert ((frame.index.minute%15==0)&(frame.index.second==0)).all()
    assert frame.index[0]>=pd.Timestamp('2023-01-01',tz='Europe/Moscow')
    assert frame.index[-1]<pd.Timestamp('2026-10-14',tz='Europe/Moscow')
    return frame

def features(raw):
    f=raw.copy(); work=raw.copy()
    work['day']=work.index.normalize();work['ordinal']=work.groupby('day').cumcount()//4
    work['first']=work.index;work['last']=work.index
    h=work.groupby(['day','ordinal'],sort=True).agg(Open=('Open','first'),High=('High','max'),Low=('Low','min'),Close=('Close','last'),first=('first','first'),last=('last','last'),count=('Close','size'))
    h=h.loc[(h['count']==4)&(h['last']-h['first']==3*STEP)].set_index('last')
    def tr(x):
        pc=x.Close.shift(1)
        return pd.concat([x.High-x.Low,abs(x.High-pc),abs(x.Low-pc)],axis=1).max(axis=1)
    def wilder(x): return x.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    f['ATR']=wilder(tr(f));f['PriorHigh']=f.High.rolling(20).max().shift(1);f['PriorLow']=f.Low.rolling(20).min().shift(1)
    h['EMA']=h.Close.ewm(span=75,adjust=False,min_periods=75).mean();h['Slope']=h.EMA-h.EMA.shift(5)
    ht=wilder(tr(h));u=h.High.diff();d=-h.Low.diff()
    p=100*wilder(u.where((u>d)&(u>0),0.))/ht;m=100*wilder(d.where((d>u)&(d>0),0.))/ht
    h['ADX']=wilder(100*abs(p-m)/(p+m).replace(0,np.nan))
    h['ATR']=ht;h['ATRRatio']=ht/ht.rolling(20).mean();h['AvailableAt']=h.index
    for key in ('EMA','Slope','ADX','ATR','ATRRatio','Close','AvailableAt'):
        f['H1'+key]=h[key].reindex(f.index,method='ffill')
    valid=(f.H1ADX>20)&(f.H1ATRRatio>1)
    long=valid&(f.H1Close>f.H1EMA)&(f.H1Slope>0)&(f.Close>f.PriorHigh)
    short=valid&(f.H1Close<f.H1EMA)&(f.H1Slope<0)&(f.Close<f.PriorLow)
    f['Signal']=np.select([long,short],[1,-1],default=0)
    result=[]
    for at,row in f.iterrows():
        b=row.to_dict();b['at']=at.to_pydatetime()
        b['H1AvailableAt']=None if pd.isna(b['H1AvailableAt']) else b['H1AvailableAt'].to_pydatetime()
        b['Signal']=int(b['Signal']);result.append(b)
    return result

@dataclass
class Position:
    signal:dict
    trade_id:str
    side:int
    entry:float
    initial:float
    risk:float
    stop:float
    extreme:float
    lowest:float
    highest:float
    index:int
    updates:int=0
    gaps:int=0

def replay(bars,symbol,mode):
    assert mode in MODES
    trades=[];signals=[];stops=[];snapshots=[];q=None;pending=None;prev=None;seq=0;busy_bars=0
    model=f'T1_{mode}_TRAIL_3p5'
    def enter(b,price,index,tid):
        initial=price-b['Signal']*2*b['ATR'];risk=abs(price-initial)
        assert risk>0 and b['H1AvailableAt']<=b['at']
        return Position(b,tid,b['Signal'],price,initial,risk,initial,price,price,price,index)
    def base(p):
        s=p.signal
        return dict(model=model,instrument=symbol,trade_id=p.trade_id,direction='LONG' if p.side>0 else 'SHORT',signal_time=s['at'],entry_time=s['at'],signal_close=s['Close'],entry_price=p.entry,initial_stop=p.initial,initial_risk=p.risk,ATR=s['ATR'],H1AvailableAt=s['H1AvailableAt'],breakout_level=s['PriorHigh'] if p.side>0 else s['PriorLow'])
    def snapshot(p,b):
        return base(p)|dict(month=b['at'].strftime('%Y-%m'),last_close=b['at'],last_close_price=b['Close'],active_stop=p.stop,unrealized_gross_R=p.side*(b['Close']-p.entry)/p.risk,status='OPEN_NOT_LIQUIDATED')
    for i,b in enumerate(bars):
        at=b['at'];exited=None
        if q and prev['at'].strftime('%Y-%m')!=at.strftime('%Y-%m'): snapshots.append(snapshot(q,prev))
        if pending is not None:
            s,ix,row=pending
            assert q is None
            if at==s['at']+STEP:
                q=enter(s,b['Open'],ix,row['trade_id'])
                row.update(entry_accepted=True,reason='EXECUTED_NEXT_OPEN',entry_price=q.entry,initial_stop=q.initial,execution_bar_close=at)
            else: row.update(reason='MISSING_ADJACENT_OPEN',next_observed_close=at)
            pending=None
        if q:
            busy_bars+=1;old=q.stop;side=q.side
            gap=bool(prev and at-prev['at']>STEP);q.gaps+=int(gap)
            opening=side*(b['Open']-old)<=0
            hit=opening or (b['Low']<=old if side>0 else b['High']>=old)
            r=dict(model=model,instrument=symbol,trade_id=q.trade_id,bar_close=at,active_stop=old,extreme_before=q.extreme,ATR=b['ATR'],stop_hit=hit,observed_gap=gap,exit_price=None,next_stop=None,extreme_after=None,proposal=None)
            if hit:
                fill=b['Open'] if opening else old
                trades.append(base(q)|dict(exit_time=at,exit_bar_open_time=at-STEP,exit_price=fill,gross_R=side*(fill-q.entry)/q.risk,active_stop_at_exit=old,exit_at_open=bool(opening),gap_exit=fill!=old,exit_type='INITIAL_STOP' if old==q.initial else 'RATCHETED_STOP',trailing_updates=q.updates,bars_held=i-q.index,holding_minutes=(at-q.signal['at']).total_seconds()/60,observed_gaps_exposed=q.gaps,MFE_R=max(0.,q.highest-q.entry if side>0 else q.entry-q.lowest)/q.risk,MAE_R=max(0.,q.entry-q.lowest if side>0 else q.highest-q.entry,side*(q.entry-fill))/q.risk))
                r['exit_price']=fill;exited=q.trade_id;q=None
            else:
                q.highest=max(q.highest,b['High']);q.lowest=min(q.lowest,b['Low'])
                q.extreme=q.highest if side>0 else q.lowest
                proposal=q.extreme-side*3.5*b['ATR']
                if side*(proposal-old)>0:q.stop=proposal;q.updates+=1
                r.update(next_stop=q.stop,extreme_after=q.extreme,proposal=proposal)
            stops.append(r)
        if b['Signal'] and math.isfinite(b['ATR']):
            allowed=600<=at.hour*60+at.minute<1080;busy=q is not None;accepted=allowed and not busy
            if accepted:seq=len(trades)+1  # Frozen journal numbering reuses a cancelled pending ID.
            tid=f'T3-M15-{dict(USDRUBF="Si",CNYRUBF="CNY").get(symbol,symbol)}-{seq:06d}' if accepted else None
            reason='ACCEPTED' if accepted else 'OUTSIDE_T1_AND_OCCUPIED' if busy and not allowed else 'POSITION_OCCUPIED' if busy else 'OUTSIDE_T1'
            row=dict(model=model,instrument=symbol,signal_time=at,direction='LONG' if b['Signal']>0 else 'SHORT',signal_close=b['Close'],ATR=b['ATR'],H1AvailableAt=b['H1AvailableAt'],PriorHigh=b['PriorHigh'],PriorLow=b['PriorLow'],rule_pass=allowed,position_occupied=busy,occupied_trade_id=q.trade_id if busy else None,same_close_exit_trade_id=exited,entry_accepted=accepted,reason=reason,trade_id=tid,entry_price=b['Close'] if accepted else None,initial_stop=b['Close']-b['Signal']*2*b['ATR'] if accepted else None,execution_bar_close=None,next_observed_close=None)
            signals.append(row)
            if accepted:
                if mode=='SIGNAL_CLOSE':q=enter(b,b['Close'],i,tid)
                else:
                    row.update(reason='PENDING_NEXT_OPEN',entry_accepted=False,entry_price=None,initial_stop=None)
                    pending=(b,i,row)
        prev=b
    if pending:pending[2]['reason']='UNRESOLVED_END_OF_DATA'
    opened=[snapshot(q,bars[-1])] if q else []
    if q:snapshots.extend(opened)
    return dict(trades=trades,signals=signals,stops=stops,snapshots=snapshots,OPEN=opened,occupancy=dict(instrument=symbol,model=model,observed_bars=len(bars),stop_checked_bars=busy_bars,denominator=len(bars)-1,occupancy=busy_bars/(len(bars)-1) if len(bars)>1 else None))
