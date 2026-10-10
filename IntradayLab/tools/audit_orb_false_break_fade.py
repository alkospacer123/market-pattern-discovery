"""Independent raw-M5 oracle. No production strategy, entry or outcome imports.

Uses batch backward source slices for features and a chronological order/position
machine for outcomes, unlike production's streaming features / forward paths.
Internal independent algorithm audit; external independent acceptance is pending.
"""
import csv
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
import hashlib
import io
import json
from pathlib import Path

D=Decimal; M=timedelta(minutes=5)
HOLIDAYS={(1,1),(1,2),(1,7),(2,23),(3,8),(5,1),(5,9),(6,12),(11,4)}
SIGNAL_KEYS=('signal_id','base_reason','direction','sweep_start','signal_at','stop','or_high','or_low','or_available_at','sweep_size','atr14','atr_pass','atr_ready','m15_start','m15_open','m15_high','m15_low','m15_close','m15_direction','m15_available_at','waiting_bar_start','waiting_bar_closed_at','order_sent_at','planned_execution_at')
TRADE_KEYS=('signal_id','direction','status','model_filled','entry_at','entry_price','stop','take','risk','exit_reason','unknown_reason','exit_price','exit_interval_start','exit_interval_end','resolved_at','unknown_detected_at','gross','cost_c1','cost_c2','net_c1','net_c2','net_R_c1','net_R_c2')


def calendar(d):
    if d.weekday()>=5 or (d.month,d.day) in HOLIDAYS:return []
    a=datetime.combine(d,datetime.min.time()).replace(hour=10)
    pm=a.replace(hour=14,minute=15 if date(2023,3,13)<=d<date(2023,3,21) else 5)
    return [(a,a.replace(hour=14)),(pm,a.replace(hour=18,minute=50))]


def grid(symbol,t):
    if symbol=='CNYRUBF':return D('.01') if t<datetime(2023,9,27,19) else D('.001')
    return D({'USDRUBF':'.01','GLDRUBF':'.1','IMOEXF':'.5'}[symbol])


def source(root,cfg):
    result={}
    for symbol,s in cfg['inputs'].items():
        # Independent LF-budget reader. No read-ahead beyond the last 2023 LF.
        chunks=[]; budget=s['rows_2023']+1
        with (root/s['path']).open('rb',buffering=0) as f:
            while budget:
                chunk=f.read(min(32768,budget))
                if not chunk:raise ValueError('TRUNCATED_PREFIX')
                budget-=chunk.count(b'\n');chunks.append(chunk)
        data=b''.join(chunks)
        assert len(data)==s['prefix_bytes'] and data.endswith(b'\n')
        assert hashlib.sha256(data).hexdigest()==s['prefix_sha256']
        rows={}
        for row in csv.DictReader(io.StringIO(data.decode('utf-8-sig')),delimiter=';'):
            t=datetime.fromisoformat(row['Datetime']);assert t.year==2023 and row['Ticker']==symbol
            rows[t]=tuple(D(row[k]) for k in ('Open','High','Low','Close','Volume'))
        assert len(rows)==s['rows_2023']
        result[symbol]=rows
    return result


def good(b):return b is not None and b[4]>0


def oracle_signals(symbol,bars):
    out=[]; d=date(2023,1,1)
    while d.year==2023:
        if d<min(bars).date() or not calendar(d):d+=timedelta(days=1);continue
        morning=calendar(d)[0][0]
        opening=[bars.get(morning+i*M) for i in range(3)]
        if not all(good(b) for b in opening):
            out.append(dict(signal_id=f'{symbol}_{d}_NO_OR',instrument=symbol,date=str(d),direction=0,signal_at=None,sweep_start=morning,base_reason='NO_OR'))
            d+=timedelta(days=1);continue
        hi=max(b[1] for b in opening);lo=min(b[2] for b in opening)
        consumed=set(); episodes={}
        for start,end in calendar(d):
            t=start;segment=[]
            def close_episode(e,at=None,reason='NO_RECLAIM'):
                r=e['r'];r['base_reason']=reason
                if at is not None:
                    # Context from only the current uninterrupted raw prefix.
                    anchors=[x for x in segment if x.minute%15==0 and x+3*M<=at+M]
                    parent=None
                    if anchors:
                        a=anchors[-1]; children=[bars.get(a+i*M) for i in range(3)]
                        if a>=segment[0] and all(good(x) for x in children):
                            parent=(a,children[0][0],max(x[1] for x in children),min(x[2] for x in children),children[-1][3])
                    r.update(signal_at=at+M,reclaim_start=at,waiting_bar_start=at+M,waiting_bar_closed_at=at+2*M,order_sent_at=at+2*M,planned_execution_at=at+2*M,stop=e['extreme']-e['direction']*e['tick'],
                             m15_start=parent[0] if parent else None,m15_open=parent[1] if parent else None,m15_high=parent[2] if parent else None,m15_low=parent[3] if parent else None,m15_close=parent[4] if parent else None,m15_available_at=parent[0]+3*M if parent else None,
                             m15_direction=(1 if parent[4]>parent[1] else -1 if parent[4]<parent[1] else 0) if parent else None)
                out.append(r)
            while t<end:
                b=bars.get(t)
                if not good(b):
                    for e in episodes.values():close_episode(e,reason='NO_RECLAIM_GAP')
                    episodes={};segment=[];t+=M;continue
                segment.append(t)
                if t<morning+3*M:t+=M;continue
                step=grid(symbol,t);tests={-1:b[1]>=hi+step,1:b[2]<=lo-step}
                if all(tests.values()) and (len(consumed)<2 or episodes):
                    for e in episodes.values():close_episode(e,reason='NO_RECLAIM_AMBIGUOUS')
                    episodes={};consumed={-1,1}
                    out.append(dict(signal_id=f'{symbol}_{d}_AMB_{t:%H%M}',instrument=symbol,date=str(d),direction=0,sweep_start=t,signal_at=None,base_reason='AMBIGUOUS_BOTH_SIDES',or_high=hi,or_low=lo));t+=M;continue
                for side,e in list(episodes.items()):
                    e['extreme']=max(e['extreme'],b[1]) if side<0 else min(e['extreme'],b[2])
                    ok=(lo<=b[3]<=hi-2*step) if side<0 else (lo+2*step<=b[3]<=hi)
                    close_episode(e,t if ok else None,'SIGNAL' if ok else 'NO_RECLAIM');del episodes[side]
                for side in (-1,1):
                    if side in consumed or not tests[side]:continue
                    consumed.add(side);atr=None
                    if len(segment)>=15:
                        q=[bars[x] for x in segment[-15:]]
                        tr=[max(q[i][1]-q[i][2],abs(q[i][1]-q[i-1][3]),abs(q[i][2]-q[i-1][3])) for i in range(1,15)]
                        atr=sum(tr,D(0))/D(14)
                    sweep=b[1]-hi if side<0 else lo-b[2]
                    r=dict(signal_id=f'{symbol}_{d}_{side}_{t:%H%M}',instrument=symbol,date=str(d),direction=side,sweep_start=t,sweep_closed_at=t+M,signal_at=None,or_high=hi,or_low=lo,or_available_at=morning+3*M,sweep_size=sweep,sweep_tick=step,atr14=atr,atr_ready=atr is not None,atr_pass=atr is not None and sweep>=max(step,D('.30')*atr),window_start=start,window_end=end)
                    e={'r':r,'direction':side,'tick':step,'extreme':b[1] if side<0 else b[2]}
                    ok=(lo<=b[3]<=hi-2*step) if side<0 else (lo+2*step<=b[3]<=hi)
                    if ok:close_episode(e,t,'SIGNAL')
                    elif t+M<end:episodes[side]=e
                    else:close_episode(e,reason='NO_RECLAIM_WINDOW')
                t+=M
            for e in episodes.values():close_episode(e,reason='NO_RECLAIM_WINDOW')
            episodes={}
        d+=timedelta(days=1)
    return sorted(out,key=lambda x:(x.get('signal_at') or x['sweep_start']+M,x['signal_id']))


def oracle_trades(symbol,bars,events,arch,spec):
    signals=[dict(x,architecture=arch,status='REJECTED',reason=x['base_reason'],order_admitted=False,model_filled=False) for x in events]
    event_at={}
    for s in signals:
        if s['base_reason']=='SIGNAL':event_at.setdefault(s['signal_at'],[]).append(s)
    pending=None; position=None; blocked=False;trades=[]
    def terminate(t,price,why,point=False,unknown=None):
        nonlocal position,blocked
        p=position; q=p['trade'];q.update(status='UNKNOWN' if unknown else 'CLOSED',exit_reason=why,exit_price=price,exit_at=t if point and not unknown else None,exit_interval_start=None if unknown else t,exit_interval_end=None if unknown else t if point else t+M,resolved_at=None if unknown else t+M if not point else t)
        if unknown:q['unknown_reason']=unknown;q['unknown_detected_at']=t+M;blocked=True
        else:
            gross=q['direction']*(price-q['entry_price']);cost=grid(symbol,q['entry_at'])+grid(symbol,t)
            q.update(gross=gross,cost_c1=cost,cost_c2=cost*2,net_c1=gross-cost,net_c2=gross-2*cost,net_R_c1=(gross-cost)/q['risk'],net_R_c2=(gross-2*cost)/q['risk'])
        position=None
    first=min(bars).replace(hour=0,minute=0);last=max(bars).replace(hour=23,minute=55)
    t=first
    while t<=last:
        # Deliver previous completed M5 outcome before decisions at this boundary.
        if position and position['trade']['entry_at']<=t-M and t-M<position['deadline']:
            q=position['trade'];b=bars.get(t-M)
            if not good(b):terminate(t-M,None,'UNKNOWN',unknown='MISSING_EXPOSED_BAR' if b is None else 'INVALID_EXPOSED_BAR')
            else:
                stop_hit=b[2]<=q['stop'] if q['direction']>0 else b[1]>=q['stop']
                take_hit=b[1]>=q['take'] if q['direction']>0 else b[2]<=q['take']
                if stop_hit:terminate(t-M,q['stop'],'STOP')
                elif take_hit and t-M!=q['entry_at']:terminate(t-M,q['take'],'TAKE')
        # At Open, only gap and scheduled market exit may resolve the position.
        if position:
            q=position['trade'];b=bars.get(t)
            if t<=position['deadline']:
                if not good(b):terminate(t,None,'UNKNOWN',unknown='MISSING_EXPOSED_BAR' if b is None else 'INVALID_EXPOSED_BAR')
                elif (b[0]<=q['stop'] if q['direction']>0 else b[0]>=q['stop']):terminate(t,b[0],'STOP',True)
                elif t==position['deadline']:terminate(t,b[0],'TIME' if t==q['entry_at']+timedelta(minutes=60) else 'SESSION_FLAT',True)
        if pending and pending['planned_execution_at']==t:
            s=pending;pending=None
            if not good(bars.get(s['waiting_bar_start'])):s['reason']='NO_WAITING_BAR'
            else:
                s['order_admitted']=True;b=bars.get(t)
                q=dict(architecture=arch,instrument=symbol,signal_id=s['signal_id'],direction=s['direction'],signal_at=s['signal_at'],sweep_start=s['sweep_start'],reclaim_start=s['reclaim_start'],waiting_bar_closed_at=s['waiting_bar_closed_at'],order_sent_at=s['order_sent_at'],planned_execution_at=t,entry_at=None,entry_price=None,stop=s['stop'],take=None,risk=None,window_end=s['window_end'],gross=None,cost_c1=None,cost_c2=None,net_c1=None,net_c2=None,net_R_c1=None,net_R_c2=None)
                if b is None:
                    s.update(status='UNKNOWN',reason='MISSING_EXECUTION_BAR');q.update(status='UNKNOWN',exit_reason='UNKNOWN',unknown_reason='MISSING_EXECUTION_BAR',model_filled=False,exit_at=None,exit_interval_start=None,exit_interval_end=None,exit_price=None,resolved_at=None,unknown_detected_at=t+M);trades.append(q);blocked=True
                else:
                    r=s['direction']*(b[0]-s['stop'])
                    if r<=0:s.update(status='NONFILL',reason='INVALID_STOP_GEOMETRY')
                    else:
                        take=b[0]+D('1.5')*r*s['direction']; step=grid(symbol,t)
                        take=(take/step).to_integral_value(rounding=ROUND_CEILING if s['direction']>0 else ROUND_FLOOR)*step
                        s.update(status='MODEL_FILLED',reason='',model_filled=True,entry_open=b[0],risk=r,take=take)
                        q.update(entry_at=t,entry_price=b[0],take=take,risk=r,model_filled=True,cost_entry_c1=step,cost_entry_c2=2*step)
                        trades.append(q);position={'trade':q,'deadline':min(t+timedelta(minutes=60),s['window_end']-M)}
        for s in event_at.get(t,[]):
            if spec['atr'] and not s['atr_ready']:s['reason']='NO_ATR'
            elif spec['atr'] and not s['atr_pass']:s['reason']='ATR_SWEEP_TOO_SMALL'
            elif spec['mtf'] and s['m15_direction']!=s['direction']:s['reason']='NO_M15' if s['m15_direction'] is None else 'M15_DIRECTION'
            elif blocked:s['reason']='UNKNOWN_POSITION_BLOCK'
            elif position or pending:s['reason']='POSITION_BUSY'
            elif s['planned_execution_at']>=s['window_end']-M or s['planned_execution_at']<s['window_start']:s['reason']='SESSION_LIMIT'
            else:pending=s
        t+=M
    assert position is None and pending is None
    return signals,trades


def text_value(x):return '' if x is None else str(x)


def compare_rows(actual,expected,keys,label):
    discrepancies=[]
    aa={x['signal_id']:x for x in actual};ee={x['signal_id']:x for x in expected}
    for sid in sorted(set(aa)|set(ee)):
        if sid not in aa or sid not in ee:discrepancies.append({'table':label,'id':sid,'reason':'ROW_SET'});continue
        for k in keys:
            if text_value(aa[sid].get(k))!=text_value(ee[sid].get(k)):
                discrepancies.append({'table':label,'id':sid,'field':k,'actual':text_value(aa[sid].get(k)),'expected':text_value(ee[sid].get(k))})
    return discrepancies


def audit(config,raw,base,signal_rows,trade_rows):
    errors=[];checked=0
    for symbol in config['instruments']:
        expected=oracle_signals(symbol,raw[symbol])
        errors+=compare_rows(base[symbol],expected,SIGNAL_KEYS,'base_signals')
        checked+=len(expected)*len(SIGNAL_KEYS)
        for arch,spec in config['architectures'].items():
            ss,tt=oracle_trades(symbol,raw[symbol],expected,arch,spec)
            a=[x for x in signal_rows if x['instrument']==symbol and x['architecture']==arch]
            b=[x for x in trade_rows if x['instrument']==symbol and x['architecture']==arch]
            errors+=compare_rows(a,ss,SIGNAL_KEYS+('status','reason','order_admitted','model_filled'),'signals_'+arch)
            errors+=compare_rows(b,tt,TRADE_KEYS,'trades_'+arch)
            checked+=len(ss)*(len(SIGNAL_KEYS)+4)+len(tt)*len(TRADE_KEYS)
    return {'status':'PASS' if not errors else 'FAIL','method':'Independent source reader, backward raw slices, independent chronological order/position state machine. Imports no production trade/signal functions. Internal algorithm verification; external acceptance pending.','checked_fields':checked,'discrepancies':errors,'source_2024_plus_bytes_read':0}
