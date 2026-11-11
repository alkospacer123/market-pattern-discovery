"""PR518 execution machine: only confirmation reservation and audit marks added.
CONTROL uses the unchanged NEXT_OPEN path. See ENGINE_LINEAGE.patch.
"""
from dataclasses import dataclass
from datetime import timedelta
import math
STEP=timedelta(minutes=15)
MODES=('CONTROL','CONFIRM')

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
    trades=[];signals=[];stops=[];snapshots=[];marks=[];q=None;pending=None;confirm=None;prev=None;seq=0;busy_bars=0;realized=0.
    model='T1_NEXT_OPEN_TRAIL_3p5' if mode=='CONTROL' else 'T1_CONFIRM_ONE_BAR_TRAIL_3p5'
    def enter(b,price,index,tid):
        initial=price-b['Signal']*2*b['ATR'];risk=abs(price-initial)
        assert risk>0 and b['H1AvailableAt']<=b['at']
        return Position(b,tid,b['Signal'],price,initial,risk,initial,price,price,price,index)
    def base(p):
        s=p.signal
        return dict(model=model,instrument=symbol,trade_id=p.trade_id,direction='LONG' if p.side>0 else 'SHORT',signal_time=s['at'],entry_time=s['at'],signal_close=s['Close'],entry_price=p.entry,initial_stop=p.initial,initial_risk=p.risk,ATR=s['ATR'],H1AvailableAt=s['H1AvailableAt'],breakout_level=s['PriorHigh'] if p.side>0 else s['PriorLow'],actual_entry_time=s['actual_entry_time'],execution_bar_close=s['execution_bar_close'],confirmed=s['confirmed'])
    def snapshot(p,b):
        return base(p)|dict(month=b['at'].strftime('%Y-%m'),last_close=b['at'],last_close_price=b['Close'],active_stop=p.stop,unrealized_gross_R=p.side*(b['Close']-p.entry)/p.risk,status='OPEN_NOT_LIQUIDATED')
    for i,b in enumerate(bars):
        at=b['at'];exited=None
        if q and prev['at'].strftime('%Y-%m')!=at.strftime('%Y-%m'): snapshots.append(snapshot(q,prev))
        if pending is not None:
            s,ix,row=pending
            assert q is None
            if at==row['ready_time']+STEP:
                q=enter(s,b['Open'],ix,row['trade_id'])
                row['actual_entry_time']=at-STEP
                q.signal=q.signal|{'actual_entry_time':at-STEP,'execution_bar_close':at,'confirmed':row['stretched_delay']}
                row.update(entry_accepted=True,reason='EXECUTED_CONFIRMED_OPEN' if row['stretched_delay'] else 'EXECUTED_NEXT_OPEN',entry_price=q.entry,initial_stop=q.initial,execution_bar_close=at)
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
                realized+=trades[-1]['gross_R']
                r['exit_price']=fill;exited=q.trade_id;q=None
            else:
                q.highest=max(q.highest,b['High']);q.lowest=min(q.lowest,b['Low'])
                q.extreme=q.highest if side>0 else q.lowest
                proposal=q.extreme-side*3.5*b['ATR']
                if side*(proposal-old)>0:q.stop=proposal;q.updates+=1
                r.update(next_stop=q.stop,extreme_after=q.extreme,proposal=proposal)
            stops.append(r)
        if confirm is not None:
            original,ix,event=confirm
            event['confirmation_time']=at
            event['confirmation_close']=b['Close']
            adjacent=at==original['at']+STEP
            in_t1=600<=at.hour*60+at.minute<1080
            side=original['Signal'];level=original['PriorHigh'] if side>0 else original['PriorLow']
            passed=side*(b['Close']-original['Close'])>0 and side*(b['Close']-level)>0
            event['confirmation_adjacent']=adjacent
            event['confirmation_in_T1']=in_t1
            event['confirmation_price_pass']=passed
            if not adjacent:event['reason']='MISSING_ADJACENT_CONFIRMATION'
            elif not in_t1:event['reason']='CONFIRMATION_OUTSIDE_T1'
            elif not passed:event['reason']='CONFIRMATION_FAILED'
            else:
                event.update(reason='PENDING_CONFIRMED_OPEN',ready_time=at)
                pending=(original,ix,event)
            confirm=None
        if b['Signal'] and math.isfinite(b['ATR']):
            allowed=600<=at.hour*60+at.minute<1080;busy=q is not None;reserved=pending is not None;accepted=allowed and not busy and not reserved
            if accepted:seq=len(trades)+1  # Frozen journal numbering reuses a cancelled pending ID.
            tid=f'T3-M15-{dict(USDRUBF="Si",CNYRUBF="CNY").get(symbol,symbol)}-{seq:06d}' if accepted else None
            reason='ACCEPTED' if accepted else 'CONFIRMATION_ENTRY_RESERVED' if reserved else 'OUTSIDE_T1_AND_OCCUPIED' if busy and not allowed else 'POSITION_OCCUPIED' if busy else 'OUTSIDE_T1'
            row=dict(model=model,instrument=symbol,signal_time=at,direction='LONG' if b['Signal']>0 else 'SHORT',signal_close=b['Close'],ATR=b['ATR'],H1AvailableAt=b['H1AvailableAt'],PriorHigh=b['PriorHigh'],PriorLow=b['PriorLow'],rule_pass=allowed,position_occupied=busy,occupied_trade_id=q.trade_id if busy else None,same_close_exit_trade_id=exited,entry_accepted=accepted,reason=reason,trade_id=tid,entry_price=b['Close'] if accepted else None,initial_stop=b['Close']-b['Signal']*2*b['ATR'] if accepted else None,execution_bar_close=None,next_observed_close=None)
            level=b['PriorHigh'] if b['Signal']>0 else b['PriorLow']
            row.update(signal_id=symbol+'|'+at.isoformat()+'|'+row['direction'],breakout_ATR=b['Signal']*(b['Close']-level)/b['ATR'],pending_reserved=reserved,stretched_delay=mode=='CONFIRM' and b['Signal']*(b['Close']-level)/b['ATR']>=.5,ready_time=at,confirmation_time=None,confirmation_close=None,confirmation_adjacent=None,confirmation_in_T1=None,confirmation_price_pass=None,actual_entry_time=None)
            signals.append(row)
            if accepted:
                row.update(reason='PENDING_CONFIRMATION' if row['stretched_delay'] else 'PENDING_NEXT_OPEN',entry_accepted=False,entry_price=None,initial_stop=None)
                if row['stretched_delay']:confirm=(b,i,row)
                else:pending=(b,i,row)
        unrealized=q.side*(b['Close']-q.entry)/q.risk if q else 0.
        marks.append(dict(instrument=symbol,variant=mode,at=at,gross_realized_R=realized,gross_unrealized_R=unrealized,gross_MTM_R=realized+unrealized,position_trade_id=q.trade_id if q else None,waiting_signal_id=(pending or confirm)[2]['signal_id'] if pending or confirm else None,waiting_stage='ENTRY_OPEN' if pending else 'CONFIRMATION_CLOSE' if confirm else None))
        prev=b
    if pending:pending[2]['reason']='UNRESOLVED_END_OF_DATA'
    if confirm:confirm[2]['reason']='UNRESOLVED_CONFIRMATION_END_OF_DATA'
    opened=[snapshot(q,bars[-1])] if q else []
    if q:snapshots.extend(opened)
    return dict(marks=marks,trades=trades,signals=signals,stops=stops,snapshots=snapshots,OPEN=opened,occupancy=dict(instrument=symbol,model=model,observed_bars=len(bars),stop_checked_bars=busy_bars,denominator=len(bars)-1,occupancy=busy_bars/(len(bars)-1) if len(bars)>1 else None))
