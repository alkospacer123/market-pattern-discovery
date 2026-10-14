"""Primary dataframe features and object position replay; all code local.

No earlier executable imports. Exact frozen H1, ATR, ADX and Donchian rules.
The independent verifier uses scalar recursion and its own position machine.
"""
from dataclasses import dataclass, field
from pathlib import Path
import math
import pandas as pd
import numpy as np
import independent as C  # Constants / integrity / serialization only.

RULES=('CONTROL','T1','S1','COMBINED')

def read_source(path):
    records=[];stamps=[]
    with Path(path).open('rb') as f:
        assert f.readline().rstrip()==b'Ticker;Datetime;Open;High;Low;Close;Volume'
        while True:
            fields=[]
            for _ in range(2):
                buf=bytearray()
                while True:
                    char=f.read(1)
                    if not char:break
                    if char==b';':break
                    buf.extend(char)
                if not char:break
                fields.append(buf.decode())
            if not fields:break
            assert len(fields)==2,'TRUNCATED_TIMESTAMP'
            opening=pd.Timestamp(fields[1],tz='Europe/Moscow')
            if opening>=C.END:break  # No future OHLC suffix is read.
            suffix=f.readline()
            if opening<C.START:continue
            close=opening+pd.Timedelta(minutes=15)
            if close>=C.END:continue
            records.append([float(x) for x in suffix.decode().strip().split(';')]);stamps.append(close)
    f=pd.DataFrame(records,index=pd.DatetimeIndex(stamps,name='CloseTime'),columns=['Open','High','Low','Close','Volume'])
    assert len(f) and f.index.is_monotonic_increasing and not f.index.has_duplicates
    assert ((f.index.minute%15==0)&(f.index.second==0)).all() and np.isfinite(f.to_numpy()).all()
    assert (f.High>=f[['Open','Close','Low']].max(axis=1)).all() and (f.Low<=f[['Open','Close','High']].min(axis=1)).all()
    return f

def features(frame):
    low=frame.copy();groups=frame.copy()
    groups['Day']=groups.index.normalize()
    groups['Ordinal']=groups.groupby('Day',sort=True).cumcount()//4
    groups['First']=groups.index;groups['Last']=groups.index;groups['Count']=1
    h=groups.groupby(['Day','Ordinal'],sort=True).agg(Open=('Open','first'),High=('High','max'),Low=('Low','min'),
        Close=('Close','last'),Volume=('Volume','sum'),First=('First','first'),Last=('Last','last'),Count=('Count','sum'))
    h=h.loc[(h.Count==4)&((h.Last-h.First)==pd.Timedelta(minutes=45))].set_index('Last')
    def tr(f):
        prev=f.Close.shift()
        return pd.concat([f.High-f.Low,(f.High-prev).abs(),(f.Low-prev).abs()],axis=1).max(axis=1)
    def average(x):return x.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    low['ATR']=average(tr(low));low['PreviousATR']=low.ATR.shift()
    low['PriorHigh']=low.High.rolling(20).max().shift();low['PriorLow']=low.Low.rolling(20).min().shift()
    h['EMA']=h.Close.ewm(span=75,adjust=False,min_periods=75).mean();h['Slope']=h.EMA-h.EMA.shift(5)
    up=h.High.diff();down=-h.Low.diff();ht=average(tr(h))
    plus=100*average(up.where((up>down)&(up>0),0.))/ht
    minus=100*average(down.where((down>up)&(down>0),0.))/ht
    h['ADX']=average(100*(plus-minus).abs()/(plus+minus).replace(0,np.nan))
    h['ATR']=average(tr(h));h['ATRRatio']=h.ATR/h.ATR.rolling(20).mean()
    h['AvailableAt']=h.index
    for name in ('ADX','Slope','ATRRatio','AvailableAt'):
        h['Previous'+name]=h[name].shift()
        low['H1'+name]=h[name].reindex(low.index,method='ffill')
        low['H1Previous'+name]=h['Previous'+name].reindex(low.index,method='ffill')
    valid=(h.ADX>20)&(h.ATRRatio>1)
    regime=pd.Series(0,index=h.index)
    regime.loc[valid&(h.Close>h.EMA)&(h.Slope>0)]=1
    regime.loc[valid&(h.Close<h.EMA)&(h.Slope<0)]=-1
    regime=regime.reindex(low.index,method='ffill').fillna(0)
    low['Signal']=np.select([(regime==1)&(low.Close>low.PriorHigh),(regime==-1)&(low.Close<low.PriorLow)],[1,-1],default=0)
    return low

@dataclass
class Position:
    id:str
    side:int
    entry:float
    initial:float
    risk:float
    time:object
    index:int
    level:float
    stop:float
    extreme:float
    lowest:float
    highest:float
    entry_features:dict=field(default_factory=dict)
    updates:int=0
    gaps:int=0
    overnight:int=0
    activated:bool=False
    activation_time:object=None
    source:str='INITIAL_STOP'

def replay(low,symbol,version,rule):
    assert rule in RULES
    delayed=rule in ('S1','COMBINED');limited=rule in ('T1','COMBINED');trail=C.VERSIONS[version]
    ids={'version':version,'rule':rule,'instrument':symbol}
    alias={'USDRUBF':'Si','CNYRUBF':'CNY'}.get(symbol,symbol)
    trades=[];stops=[];entries=[];gaps=[];snapshots=[];position=None;previous=None;last=None
    def snapshot(q,b):
        return ids|{'trade_id':q.id,'direction':'LONG' if q.side==1 else 'SHORT','entry_time':q.time,
            'entry_price':q.entry,'initial_stop':q.initial,'initial_risk':q.risk,'active_stop':q.stop,'breakout_level':q.level,
            'last_close':b.Index,'last_close_price':float(b.Close),'unrealized_gross_R_at_last_close':q.side*(b.Close-q.entry)/q.risk,
            'pending_exit_decision':None,'threshold_activated':q.activated,'activation_time':q.activation_time,
            'favorable_extreme':q.extreme,'stop_source':q.source,'stop_updates':q.updates,
            'status':'OPEN_NOT_LIQUIDATED_EXCLUDED_FROM_CLOSED_TRADE_METRICS'}
    for index,b in enumerate(low.itertuples()):
        time=b.Index;assert C.START<=time<C.END,'FUTURE_OHLC_FORBIDDEN'
        if position and time.strftime('%Y-%m')!=previous.strftime('%Y-%m'):
            snapshots.append(snapshot(position,last)|{'month':previous.strftime('%Y-%m'),'year':previous.year})
        minute=time.tz_convert('Europe/Moscow').hour*60+time.minute
        allowed=not limited or 600<=minute<1080
        reason=('CORE_HOURS' if allowed else 'OUTSIDE_CORE_HOURS') if limited else 'CONTROL'
        delta=(time-previous).total_seconds()/60 if previous is not None else None
        gap=delta is not None and delta>15
        overnight=bool(gap and (time-C.STEP).date()!=(previous-C.STEP).date())
        if previous is None or gap:
            gaps.append(ids|{'current_close':time,'previous_close':previous,'delta_minutes':delta,
                'reason':'NO_PREVIOUS_OBSERVED_CLOSE' if previous is None else 'OBSERVED_GAP_GT_15_MIN',
                'cross_date':bool(gap and time.date()!=previous.date()),'cross_observed_open_date':overnight,
                'original_signal':int(b.Signal),'entry_rule_pass':allowed,'position_before_bar':position.id if position else None})
        exited=None
        if position is not None:
            q=position;old=q.stop;s=q.side
            opening=s*(b.Open-old)<=0
            hit=bool(opening or (b.Low<=old if s>0 else b.High>=old))
            row=ids|{'trade_id':q.id,'bar_open_time':time-C.STEP,'bar_close_time':time,'active_stop':old,
                'initial_risk':q.risk,'extreme_before':q.extreme,'open':float(b.Open),'high':float(b.High),'low':float(b.Low),
                'ATR_at_close':float(b.ATR),'stop_hit':hit,'stop_gap':bool(opening and b.Open!=old),
                'observed_gap_before_bar':gap,'observed_overnight_gap_before_bar':overnight,
                'activated_before':q.activated,'activation_time_before':q.activation_time,'threshold_R':1. if delayed else None}
            q.gaps+=int(gap);q.overnight+=int(overnight)
            if hit:
                fill=float(b.Open) if opening else old
                trades.append(ids|{'trade_id':q.id,'direction':'LONG' if s>0 else 'SHORT','entry_time':q.time,
                    'entry_price':q.entry,'initial_stop':q.initial,'initial_risk':q.risk,'breakout_level':q.level,
                    'exit_time':time,'exit_bar_open_time':time-C.STEP,'exit_bar_close_time':time,'exit_price':fill,
                    'gross_R':s*(fill-q.entry)/q.risk,'exit_type':'INITIAL_STOP' if old==q.initial else 'RATCHETED_STOP',
                    'active_stop_at_exit':old,'trailing_updates':q.updates,'gap_exit':fill!=old,'exit_at_open':bool(opening),
                    'rule_decision_time':None,'rule_stop_conflict_at_open':False,'bars_held':index-q.index,
                    'holding_minutes':(time-q.time).total_seconds()/60,
                    'MAE_R':max(0.,q.entry-q.lowest if s>0 else q.highest-q.entry,s*(q.entry-fill))/q.risk,
                    'MFE_R':max(0.,q.highest-q.entry if s>0 else q.entry-q.lowest)/q.risk,
                    'cross_calendar_day':time.date()!=q.time.date(),'year':time.year,'observed_gaps_exposed':q.gaps,
                    'observed_overnight_gaps_exposed':q.overnight,'threshold_activated':q.activated,
                    'activation_time':q.activation_time,'stop_source_at_exit':q.source,**q.entry_features})
                row.update(phase='EXIT',exit_price=fill,extreme_after=None,trail_proposal=None,active_stop_next_bar=None,
                    trailing_changed=False,favorable_extreme_after=None,favorable_R_after=None,activated_after=q.activated,
                    threshold_activated_now=False,activation_time_after=q.activation_time,original_trail_proposal=None,
                    boundary_stop=None,ratchet_changed=False,stop_source_next=None)
                exited=q.id;position=None
            else:
                q.lowest=min(q.lowest,float(b.Low));q.highest=max(q.highest,float(b.High))
                q.extreme=q.highest if s>0 else q.lowest
                activated_now=delayed and not q.activated and s*(q.extreme-q.entry)>=q.risk
                if activated_now:q.activated=True;q.activation_time=time
                proposal=q.extreme-s*trail*float(b.ATR)
                if (not delayed or q.activated) and s*(proposal-old)>0:q.stop=proposal;q.source='ATR_TRAIL';q.updates+=1
                row.update(phase='SURVIVED',exit_price=None,extreme_after=q.extreme,trail_proposal=proposal,
                    active_stop_next_bar=q.stop,trailing_changed=q.stop!=old,favorable_extreme_after=q.extreme,
                    favorable_R_after=s*(q.extreme-q.entry)/q.risk,activated_after=q.activated,
                    threshold_activated_now=bool(activated_now),activation_time_after=q.activation_time,
                    original_trail_proposal=proposal,boundary_stop=None,ratchet_changed=q.stop!=old,stop_source_next=q.source)
            stops.append(row)
        if math.isfinite(b.ATR) and b.Signal:
            busy=position is not None;accept=allowed and not busy
            tid=f'T3-M15-{alias}-{len(trades)+1:06d}' if accept else None
            entries.append(ids|{'signal_time':time,'previous_observed_close':previous,'delta_minutes':delta,'moscow_hour':time.hour,
                'direction':'LONG' if b.Signal>0 else 'SHORT','original_signal':int(b.Signal),'rule_pass':allowed,'rule_reason':reason,
                'position_occupied':busy,'occupied_trade_id':position.id if busy else None,'entry_accepted':accept,
                'decision_reason':'ACCEPTED' if accept else 'POSITION_OCCUPIED' if allowed else 'RULE_AND_OCCUPIED' if busy else 'RULE_BLOCKED',
                'trade_id':tid,'same_close_exit_trade_id':exited,'entry_price':float(b.Close),
                'candidate_initial_stop':float(b.Close)-int(b.Signal)*2*float(b.ATR),'ATR':float(b.ATR),
                'H1AvailableAt':b.H1AvailableAt,'PriorHigh':float(b.PriorHigh),'PriorLow':float(b.PriorLow)})
            if accept:
                s=int(b.Signal);entry=float(b.Close);stop=entry-s*2*float(b.ATR);risk=abs(entry-stop)
                assert risk>0 and b.H1AvailableAt<=time
                fs={k:getattr(b,k) for k in ('ATR','PreviousATR','H1ADX','H1PreviousADX','H1Slope','H1PreviousSlope',
                    'H1ATRRatio','H1PreviousATRRatio','H1AvailableAt','H1PreviousAvailableAt')}
                fs.update(signal_open=float(b.Open),signal_high=float(b.High),signal_low=float(b.Low))
                position=Position(tid,s,entry,stop,risk,time,index,float(b.PriorHigh if s>0 else b.PriorLow),stop,entry,entry,entry,fs)
        previous=time;last=b
    op=snapshot(position,last) if position else None
    if op:snapshots.append(op|{'month':last.Index.strftime('%Y-%m'),'year':last.Index.year})
    return trades,op,stops,entries,gaps,snapshots
