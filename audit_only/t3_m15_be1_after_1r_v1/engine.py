"""Frozen PR518 NEXT_OPEN machine plus one survived-bar BE1 floor and audit marks.
No confirmation or entry changes. ENGINE_LINEAGE.patch gives the exact diff.
"""
from dataclasses import dataclass
from datetime import timedelta
import math
STEP=timedelta(minutes=15)
MODES=('CONTROL','BE1')

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
    reached:bool=False
    raised:bool=False
    activation:object=None
    source:str="INITIAL"

def replay(bars,symbol,mode):
    assert mode in MODES
    trades=[];signals=[];stops=[];snapshots=[];q=None;pending=None;prev=None;seq=0;busy_bars=0;marks=[];realized=0.
    model='T1_NEXT_OPEN_TRAIL_3p5' if mode=='CONTROL' else 'T1_NEXT_OPEN_BE1_TRAIL_3p5'
    def enter(b,price,index,tid):
        initial=price-b['Signal']*2*b['ATR'];risk=abs(price-initial)
        assert risk>0 and b['H1AvailableAt']<=b['at']
        return Position(b,tid,b['Signal'],price,initial,risk,initial,price,price,price,index)
    def base(p):
        s=p.signal
        return dict(model=model,instrument=symbol,trade_id=p.trade_id,direction='LONG' if p.side>0 else 'SHORT',signal_time=s['at'],entry_time=s['at'],signal_close=s['Close'],entry_price=p.entry,initial_stop=p.initial,initial_risk=p.risk,ATR=s['ATR'],H1AvailableAt=s['H1AvailableAt'],breakout_level=s['PriorHigh'] if p.side>0 else s['PriorLow'],actual_entry_time=s['at'],execution_bar_close=s['at']+STEP,BE1_reached=p.reached,BE1_raised=p.raised,BE1_activation_time=p.activation,stop_source=p.source)
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
            r=dict(model=model,instrument=symbol,trade_id=q.trade_id,bar_close=at,active_stop=old,extreme_before=q.extreme,ATR=b['ATR'],stop_hit=hit,observed_gap=gap,exit_price=None,next_stop=None,extreme_after=None,proposal=None,BE1_reached_now=False,BE1_raised_now=False,BE1_eligible_next_observed=False,stop_source_before=q.source,stop_source_after=None)
            if hit:
                fill=b['Open'] if opening else old
                trades.append(base(q)|dict(exit_time=at,exit_bar_open_time=at-STEP,exit_price=fill,gross_R=side*(fill-q.entry)/q.risk,active_stop_at_exit=old,exit_at_open=bool(opening),gap_exit=fill!=old,exit_type='INITIAL_STOP' if old==q.initial else 'RATCHETED_STOP',trailing_updates=q.updates,bars_held=i-q.index,holding_minutes=(at-q.signal['at']).total_seconds()/60,observed_gaps_exposed=q.gaps,MFE_R=max(0.,q.highest-q.entry if side>0 else q.entry-q.lowest)/q.risk,MAE_R=max(0.,q.entry-q.lowest if side>0 else q.highest-q.entry,side*(q.entry-fill))/q.risk))
                realized+=trades[-1]['gross_R']
                r['exit_price']=fill;exited=q.trade_id;q=None
            else:
                q.highest=max(q.highest,b['High']);q.lowest=min(q.lowest,b['Low'])
                q.extreme=q.highest if side>0 else q.lowest
                proposal=q.extreme-side*3.5*b['ATR']
                if side*(proposal-old)>0:q.stop=proposal;q.updates+=1;q.source='TRAIL'
                reached=side*(q.extreme-q.entry)>=q.risk
                r['BE1_reached_now']=bool(reached and not q.reached)
                if reached and not q.reached:q.reached=True;q.activation=at
                if mode=='BE1' and reached and side*(q.entry-q.stop)>0:
                    q.stop=q.entry;q.raised=True;q.source='BE1';r['BE1_raised_now']=True
                r.update(BE1_eligible_next_observed=mode=='BE1' and reached,stop_source_after=q.source)
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
                row.update(reason='PENDING_NEXT_OPEN',entry_accepted=False,entry_price=None,initial_stop=None)
                pending=(b,i,row)
        marks.append(dict(instrument=symbol,variant=mode,at=at,gross_realized_R=realized,gross_unrealized_R=q.side*(b['Close']-q.entry)/q.risk if q else 0.,gross_MTM_R=realized+(q.side*(b['Close']-q.entry)/q.risk if q else 0.),position_trade_id=q.trade_id if q else None,waiting_signal_id=symbol+'|'+pending[0]['at'].isoformat()+'|'+('LONG' if pending[0]['Signal']>0 else 'SHORT') if pending else None))
        prev=b
    if pending:pending[2]['reason']='UNRESOLVED_END_OF_DATA'
    opened=[snapshot(q,bars[-1])] if q else []
    if q:snapshots.extend(opened)
    return dict(marks=marks,trades=trades,signals=signals,stops=stops,snapshots=snapshots,OPEN=opened,occupancy=dict(instrument=symbol,model=model,observed_bars=len(bars),stop_checked_bars=busy_bars,denominator=len(bars)-1,occupancy=busy_bars/(len(bars)-1) if len(bars)>1 else None))
