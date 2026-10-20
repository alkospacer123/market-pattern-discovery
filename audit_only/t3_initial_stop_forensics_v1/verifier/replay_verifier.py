"""Independent scalar execution verifier adapted from PR518/PR557 verifiers.

No new primary engines/accounting imports. Authenticated frozen indicator streams
are shared; scalar entry/exit/stop/occupancy/mark arithmetic is independent. The
M15 feature authority can additionally be verified with PR518's stdlib stream.
"""
import importlib.util, math
from datetime import timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
ATR={'H1':{'CONTROL':2.5,'STOP_2p0':2.,'STOP_1p5':1.5},'M15':{'CONTROL':2.,'STOP_1p5':1.5}}
META=('system','lifecycle','fold_id','instrument')


def independent_replay_audit(streams,results):
    stream_index={tuple(s[k] for k in META):s for s in streams}
    counts=dict(fields_checked=0,streams=0,positions=0,signals=0,stop_events=0,marks=0)
    maximum=0.
    def same(expected,actual,context):
        nonlocal maximum
        counts['fields_checked']+=1
        if expected is None:
            assert actual is None,(context,expected,actual)
        elif isinstance(expected,(int,float)) and not isinstance(expected,bool):
            assert actual is not None,(context,expected,actual)
            error=abs(float(expected)-float(actual));maximum=max(maximum,error)
            assert error<=1e-8,(context,expected,actual,error)
        else:assert expected==actual,(context,expected,actual)
    def table(expected,actual,name,context):
        same(len(expected),len(actual),(context,name,'length'))
        for i,(e,a) in enumerate(zip(expected,actual)):
            for k,v in e.items():same(v,a.get(k),(context,name,i,k))
    for actual in results:
        identity=actual['marks'][0]
        stream=stream_index[tuple(identity[k] for k in META)]
        bars=stream['bars'];system=stream['system'];symbol=stream['instrument'];variant=identity['variant'];multiple=ATR[system][variant]
        calculated=_scalar(stream,variant,multiple)
        for name in ('trades','signals','trace','marks'):
            table(calculated[name],actual[name],name,tuple(identity[k] for k in META)+(variant,))
        counts['streams']+=1;counts['positions']+=len(calculated['trades']);counts['signals']+=len(calculated['signals']);counts['stop_events']+=len(calculated['trace']);counts['marks']+=len(calculated['marks'])
    return dict(status='PASS',**counts,max_abs_numeric_error=maximum,provenance='Adapted causal scalar state logic from PR518 verify.py and PR557 verify.py; no primary engine/accounting imports',independence='Independent scalar position/occupancy/signal/stop/mark calculations; authenticated frozen features shared',cash_status='NOT_VALIDATED')


def _scalar(stream,variant,multiple):
    """PR518 scalar loop generalized to the two frozen execution conventions."""
    system=stream['system'];symbol=stream['instrument'];bars=stream['bars']
    result={k:[] for k in ('trades','signals','trace','marks')}
    state=None;queued=None;seq=0;closed=0;realized=paid=0.;previous=None
    def make(signal,entry,index,ident):
        sign=signal['Signal'];initial=entry-sign*multiple*signal['ATR'];risk=abs(entry-initial)
        assert risk>0
        return dict(signal=signal,entry=entry,initial=initial,risk=risk,side=sign,index=index,id=ident,stop=initial,extreme=entry,hi=entry,lo=entry,updates=0,gaps=0,triggered=False,activated=False,stored=None,trigger_at=None,activation_at=None,looser=False)
    def trade(p):
        return dict(trade_id=p['id'],direction='LONG' if p['side']==1 else 'SHORT',entry_time=p['signal']['at'],entry_price=p['entry'],initial_stop_price=p['initial'],initial_risk_price=p['risk'],status='OPEN',active_stop=p['stop'],trail1_triggered=p['triggered'],trail1_activated=p['activated'],stored_trail_candidate=p['stored'],trigger_bar_time=p['trigger_at'],trail1_activation_time=p['activation_at'],remaining_quantity=1.)
    for index,b in enumerate(bars):
        at=b['at'];exited=None
        if queued:
            signal,ix,event=queued
            assert state is None
            if at-signal['at']==timedelta(minutes=15):
                state=make(signal,b['Open'],ix,event['trade_id'])
                event.update(reason='EXECUTED_NEXT_OPEN',entry_accepted=True,entry_price=state['entry'],initial_stop=state['initial'],execution_bar_close=at)
            else:event.update(reason='MISSING_ADJACENT_OPEN',next_observed_close=at)
            queued=None
        if state:
            p=state;sign=p['side']
            if system=='H1' and p['triggered'] and not p['activated'] and at!=p['trigger_at']:
                p['activated']=True;p['activation_at']=at
                p['stop']=max(p['stop'],p['stored']) if sign==1 else min(p['stop'],p['stored'])
            stop=p['stop'];opening=b['Open']<=stop if sign==1 else b['Open']>=stop
            hit=opening or (b['Low']<=stop if sign==1 else b['High']>=stop)
            event=dict(at=at,trade_id=p['id'],stop_entering=stop,stop_hit=hit,remaining_before=1.,remaining_after=0. if hit else 1.,partial_executed=False)
            if system=='M15':p['gaps']+=int(bool(previous and at-previous['at']>timedelta(minutes=15)))
            if hit:
                fill=min(b['Open'],stop) if sign==1 else max(b['Open'],stop)
                r=sign*(fill-p['entry'])/p['risk'];realized+=r
                reason='INITIAL_STOP' if stop==p['initial'] else 'ATR_TRAILING_STOP'
                record=trade(p)
                record.update(status='CLOSED',remaining_quantity=0.,exit_time=at,exit_price=fill,exit_reason=reason,gross_R=r,active_stop_at_exit=stop,exit_at_open=bool(opening),gap_exit=fill!=stop,bars_held=index-p['index'])
                if system=='H1':
                    paid+=.001/p['risk']
                    record.update(cost_R=.002/p['risk'],net_R_C1=r-.002/p['risk'],candidate_already_looser=p['looser'],gap_through_activated_trail=bool(p['activated'] and fill!=stop))
                else:
                    record.update(signal_time=p['signal']['at'],ATR=p['signal']['ATR'],trailing_updates=p['updates'],observed_gaps_exposed=p['gaps'],holding_minutes=(at-p['signal']['at']).total_seconds()/60,MFE_R=max(0.,p['hi']-p['entry'] if sign==1 else p['entry']-p['lo'])/p['risk'],MAE_R=max(0.,p['entry']-p['lo'] if sign==1 else p['hi']-p['entry'],sign*(p['entry']-fill))/p['risk'],exit_type='INITIAL_STOP' if stop==p['initial'] else 'RATCHETED_STOP')
                result['trades'].append(record);exited=p['id'];state=None;closed+=1
            else:
                p['hi']=max(p['hi'],b['High']);p['lo']=min(p['lo'],b['Low']);p['extreme']=p['hi'] if sign==1 else p['lo']
                proposal=p['extreme']-sign*(3 if system=='H1' else 3.5)*b['ATR']
                if system=='H1':
                    if not p['triggered'] and (b['High']>=p['entry']+p['risk'] if sign==1 else b['Low']<=p['entry']-p['risk']):
                        p['triggered']=True;p['trigger_at']=at;p['stored']=proposal;p['looser']=sign*(proposal-stop)<=0
                    if p['activated']:p['stop']=max(stop,proposal) if sign==1 else min(stop,proposal)
                    event.update(triggered=p['triggered'],activated=p['activated'],stored=p['stored'])
                else:
                    p['stop']=max(stop,proposal) if sign==1 else min(stop,proposal)
                    p['updates']+=int(p['stop']!=stop)
                event.update(stop_after=p['stop'],candidate=proposal)
            result['trace'].append(event)
        if b['Signal'] and math.isfinite(b['ATR']):
            free=state is None
            if system=='H1':
                result['signals'].append(dict(at=at,side=b['Signal'],accepted=free,occupied_trade_id=state['id'] if state else None))
                if free:
                    seq+=1;state=make(b,b['Close'],index,f'T3-H1-{symbol}-{seq:06d}');paid+=.001/state['risk']
            else:
                allowed=600<=at.hour*60+at.minute<1080;take=allowed and free
                label={'USDRUBF':'Si','CNYRUBF':'CNY'}.get(symbol,symbol)
                tid=f'T3-M15-{label}-{closed+1:06d}' if take else None
                event=dict(at=at,side=b['Signal'],trade_id=tid,entry_accepted=False,occupied_trade_id=state['id'] if state else None,same_close_exit_trade_id=exited,reason='PENDING_NEXT_OPEN' if take else 'OUTSIDE_T1_AND_OCCUPIED' if state and not allowed else 'POSITION_OCCUPIED' if state else 'OUTSIDE_T1')
                result['signals'].append(event)
                if take:queued=(b,index,event)
        unrealized=state['side']*(b['Close']-state['entry'])/state['risk'] if state else 0.
        result['marks'].append(dict(at=at,gross_realized_R=realized,gross_unrealized_R=unrealized,gross_MTM_R=realized+unrealized,C1_normalized_paid_R=paid,C1_normalized_MTM_R=realized+unrealized-paid,active_trade_id=state['id'] if state else None,remaining_quantity=1. if state else 0.))
        previous=b
    if queued:queued[2]['reason']='UNRESOLVED_END_OF_DATA'
    if state:
        record=trade(state);record.update(last_mark_time=bars[-1]['at'],last_mark_price=bars[-1]['Close'],gross_R=None,cost_R=None,net_R_C1=None)
        result['trades'].append(record)
    return result


def independent_m15_feature_audit(streams,data_root):
    """Reopen M15 OHLC with archived PR518 stdlib streaming verifier."""
    path=ROOT/'IntradayLab/t3_m15_t1_entry_retest_v1/verify.py'
    spec=importlib.util.spec_from_file_location('archived_PR518_feature_verifier',path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    fields=rows=0;maxerror=0.
    for stream in streams:
        if stream['system']!='M15':continue
        symbol=stream['instrument'];fresh=list(mod.feature_stream(mod.parse(Path(data_root)/f'forever/{symbol}/{symbol}_M15.csv')))
        assert len(fresh)==len(stream['bars'])
        for e,a in zip(fresh,stream['bars']):
            rows+=1
            for k in ('at','ATR','PriorHigh','PriorLow','H1AvailableAt','Signal','H1EMA','H1Slope','H1ADX','H1ATR','H1ATRRatio','H1Close'):
                fields+=1;left=e[k];right=a[k]
                if isinstance(left,float):
                    if math.isnan(left):assert math.isnan(right),(symbol,k,left,right)
                    else:
                        d=abs(left-right);maxerror=max(maxerror,d);assert d<=1e-8,(symbol,k,left,right)
                else:assert left==right,(symbol,k,left,right)
    return dict(status='PASS',rows=rows,fields_checked=fields,max_abs_numeric_error=maxerror,provenance='Authenticated archived PR518 stdlib parser/feature_stream independently reopens source OHLC; no primary features imports')
