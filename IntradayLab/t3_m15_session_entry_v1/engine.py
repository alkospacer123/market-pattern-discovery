"""Fixed session-entry-only replay; frozen #490 features, no exit changes."""
import importlib.util
from pathlib import Path
import sys
import pandas as pd
HERE = Path(__file__).resolve().parent
FROZEN = HERE.parent/'t3_m15_forever_v1'
spec = importlib.util.spec_from_file_location('session_frozen_features',FROZEN/'engine.py')
E = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = E
spec.loader.exec_module(E)
MAIN = '4b415f95576e00480e344a1da498c35660eef931'
RULES = ('CONTROL','T1','T2')

def features(frame, p):
    low, high = E.indicators(frame, p)
    high['ATRRatio'] = high.ATR/high.ATRMean
    high['PreviousADX'] = high.ADX.shift(1)
    high['PreviousSlope'] = high.Slope.shift(1)
    high['PreviousATRRatio'] = high.ATRRatio.shift(1)
    high['AvailableAt'] = high.index
    high['PreviousAvailableAt'] = pd.Series(high.index, index=high.index).shift(1)
    for col in ('ADX', 'Slope', 'ATRRatio', 'PreviousADX', 'PreviousSlope',
                'PreviousATRRatio', 'AvailableAt', 'PreviousAvailableAt'):
        low['H1'+col] = high[col].reindex(low.index, method='ffill')
    low['PreviousATR'] = low.ATR.shift(1)
    return low, high


def permits(current, previous, rule):
    assert rule in RULES
    if current.tzinfo is None or (previous is not None and previous.tzinfo is None):
        raise ValueError('TIMEZONE_REQUIRED')
    now = current.tz_convert(E.TZ)
    if previous is not None and current <= previous:raise ValueError('NONINCREASING_CLOSES')
    if rule == 'CONTROL':return True,'CONTROL'
    if rule == 'T1':
        allowed = 10*60 <= now.hour*60+now.minute < 18*60
        return allowed,'CORE_HOURS' if allowed else 'OUTSIDE_CORE_HOURS'
    if previous is None:return False,'NO_PREVIOUS_OBSERVED_CLOSE'
    if current-previous > pd.Timedelta(minutes=15):return False,'FIRST_BAR_AFTER_OBSERVED_GAP'
    return True,'CONTINUOUS_OBSERVED_CLOSES'


def execute(low,symbol,version,p,rule):
    assert rule in RULES and p.stop_atr == 2.0
    trades,stops,entries,gaps,snapshots = [],[],[],[],[]
    pos,previous = None,None
    ids={'version':version,'rule':rule,'instrument':symbol}
    alias=E.ALIASES.get(symbol,symbol)
    def opened(q,b):
        return ids | {'trade_id':q['id'],'direction':'LONG' if q['sign']==1 else 'SHORT',
            'entry_time':q['at'].isoformat(),'entry_price':q['entry'],'initial_stop':q['initial'],
            'initial_risk':q['risk'],'active_stop':q['stop'],'breakout_level':q['level'],
            'last_close':b.Index.isoformat(),'last_close_price':float(b.Close),
            'unrealized_gross_R_at_last_close':q['sign']*(b.Close-q['entry'])/q['risk'],
            'pending_exit_decision':None,'status':'OPEN_NOT_LIQUIDATED_EXCLUDED_FROM_CLOSED_TRADE_METRICS'}
    last=None
    for i,b in enumerate(low.itertuples()):
        assert b.Index < E.END and b.Index >= E.START,'FUTURE_OHLC_FORBIDDEN'
        if previous is not None and previous.strftime('%Y-%m') != b.Index.strftime('%Y-%m') and pos:
            snapshots.append(opened(pos,last)|{'month':previous.strftime('%Y-%m'),'year':previous.year})
        allowed,reason=permits(b.Index,previous,rule)
        delta=(b.Index-previous).total_seconds()/60 if previous is not None else None
        gap=delta is not None and delta>15
        overnight=gap and (previous-pd.Timedelta(minutes=15)).date()!=(b.Index-pd.Timedelta(minutes=15)).date()
        if previous is None or gap:
            gaps.append(ids|{'current_close':b.Index,'previous_close':previous,'delta_minutes':delta,
                'reason':'NO_PREVIOUS_OBSERVED_CLOSE' if previous is None else 'OBSERVED_GAP_GT_15_MIN',
                'cross_date':bool(gap and previous.date()!=b.Index.date()),'cross_observed_open_date':bool(overnight),'original_signal':int(b.Signal),'entry_rule_pass':allowed,
                'position_before_bar':pos['id'] if pos else None})
        exited=None
        if pos:
            q=pos;s=q['sign'];entry=q['entry'];stop=q['stop'];risk=q['risk']
            open_hit=s*(b.Open-stop)<=0
            hit=open_hit or (b.Low<=stop if s==1 else b.High>=stop)
            d=ids|{'trade_id':q['id'],'bar_open_time':b.Index-pd.Timedelta(minutes=15),
                'bar_close_time':b.Index,'active_stop':stop,'initial_risk':risk,
                'extreme_before':q['extreme'],'open':b.Open,'high':b.High,'low':b.Low,
                'ATR_at_close':b.ATR,'stop_hit':bool(hit),'stop_gap':bool(open_hit and b.Open!=stop),
                'observed_gap_before_bar':gap,'observed_overnight_gap_before_bar':bool(overnight)}
            q['gaps']+=int(gap);q['overnights']+=int(overnight)
            if hit:
                fill=min(b.Open,stop) if s==1 else max(b.Open,stop)
                trades.append(ids|{'trade_id':q['id'],'direction':'LONG' if s==1 else 'SHORT',
                    'entry_time':q['at'],'entry_price':entry,'initial_stop':q['initial'],'initial_risk':risk,
                    'breakout_level':q['level'],'exit_time':b.Index,
                    'exit_bar_open_time':b.Index-pd.Timedelta(minutes=15),'exit_bar_close_time':b.Index,
                    'exit_price':fill,'gross_R':s*(fill-entry)/risk,
                    'exit_type':'INITIAL_STOP' if stop==q['initial'] else 'RATCHETED_STOP',
                    'active_stop_at_exit':stop,'trailing_updates':q['updates'],'gap_exit':bool(fill!=stop),
                    'exit_at_open':bool(open_hit),'rule_decision_time':None,'rule_stop_conflict_at_open':False,
                    'bars_held':i-q['index'],'holding_minutes':(b.Index-q['at']).total_seconds()/60,
                    'MAE_R':max(0.,entry-q['min'] if s==1 else q['max']-entry,s*(entry-fill))/risk,
                    'MFE_R':max(0.,q['max']-entry if s==1 else entry-q['min'])/risk,
                    'cross_calendar_day':b.Index.date()!=q['at'].date(),'year':b.Index.year,
                    'observed_gaps_exposed':q['gaps'],'observed_overnight_gaps_exposed':q['overnights'],
                    **q['features']})
                d.update(phase='EXIT',exit_price=fill,extreme_after=None,trail_proposal=None,
                    active_stop_next_bar=None,trailing_changed=False)
                exited=q['id'];pos=None
            else:
                q['min']=min(q['min'],b.Low);q['max']=max(q['max'],b.High)
                q['extreme']=max(q['extreme'],b.High) if s==1 else min(q['extreme'],b.Low)
                proposal=q['extreme']-s*p.trail_atr*b.ATR
                new=max(stop,proposal) if s==1 else min(stop,proposal)
                q['updates']+=int(new!=stop);q['stop']=new
                d.update(phase='SURVIVED',exit_price=None,extreme_after=q['extreme'],trail_proposal=proposal,
                    active_stop_next_bar=new,trailing_changed=bool(new!=stop))
            stops.append(d)
        if pd.notna(b.ATR) and b.Signal:
            occupied=pos is not None;accepted=allowed and not occupied
            tid=f'T3-M15-{alias}-{len(trades)+1:06d}' if accepted else None
            entries.append(ids|{'signal_time':b.Index,'previous_observed_close':previous,
                'delta_minutes':delta,'moscow_hour':b.Index.tz_convert(E.TZ).hour,
                'direction':'LONG' if b.Signal==1 else 'SHORT','original_signal':int(b.Signal),
                'rule_pass':allowed,'rule_reason':reason,'position_occupied':occupied,
                'occupied_trade_id':pos['id'] if occupied else None,'entry_accepted':accepted,
                'decision_reason':'ACCEPTED' if accepted else 'RULE_AND_OCCUPIED' if not allowed and occupied else 'RULE_BLOCKED' if not allowed else 'POSITION_OCCUPIED',
                'trade_id':tid,'same_close_exit_trade_id':exited,'entry_price':b.Close,
                'candidate_initial_stop':b.Close-b.Signal*p.stop_atr*b.ATR,'ATR':b.ATR,
                'H1AvailableAt':b.H1AvailableAt,'PriorHigh':b.PriorHigh,'PriorLow':b.PriorLow})
            if accepted:
                s=int(b.Signal);entry=float(b.Close);initial=entry-s*p.stop_atr*float(b.ATR)
                risk=abs(entry-initial);assert risk>0
                assert b.H1AvailableAt<=b.Index
                pos={'id':tid,'sign':s,'entry':entry,'at':b.Index,'index':i,'initial':initial,
                    'risk':risk,'stop':initial,'level':b.PriorHigh if s==1 else b.PriorLow,
                    'extreme':entry,'min':entry,'max':entry,'updates':0,'gaps':0,'overnights':0,
                    'features':{c:getattr(b,c) for c in ('ATR','PreviousATR','H1ADX','H1PreviousADX',
                    'H1Slope','H1PreviousSlope','H1ATRRatio','H1PreviousATRRatio','H1AvailableAt','H1PreviousAvailableAt')}|
                    {'signal_open':b.Open,'signal_high':b.High,'signal_low':b.Low}}
        previous=b.Index;last=b
    op=opened(pos,last) if pos else None
    if op:snapshots.append(op|{'month':last.Index.strftime('%Y-%m'),'year':last.Index.year})
    return trades,op,stops,entries,gaps,snapshots
