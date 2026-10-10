#!/usr/bin/env python3
"""Independent 2023 oracle: stdlib only; no IntradayLab production imports.

Reconstructs ALL opportunities and position states, then compares frozen CSVs.
No strategy search, source repair, unknown payoff recovery or Replay invocation.
Reads exact attested M5 byte budgets, never the next row or buffered lookahead.
"""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import date, datetime as DT, timedelta as TD
from decimal import Decimal as D, ROUND_CEILING, ROUND_FLOOR
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

LAB = Path(__file__).resolve().parents[1]
HEAD = '2cfab348011c874e5d8e98787855f86b75fb5e43'
MAIN = 'f5dec0a73bf1273f9490502fbc0b9588f9315260'
FIVE = TD(minutes=5)
ZERO = D(0)
HOLIDAYS = {(1,1),(1,2),(1,7),(2,23),(3,8),(5,1),(5,9),(6,12),(11,4)}

def git(root, *args):
    return subprocess.check_output(['git','-C',str(root),*args], text=True).strip()

def sha(data):
    return hashlib.sha256(data).hexdigest()

def encoded(x):
    return json.dumps(x, default=str, ensure_ascii=False, sort_keys=True, indent=2)+'\n'

def table(path):
    if not path.exists():
        path = path.with_suffix('.csv.gz')
    with (gzip.open(path, 'rt') if path.suffix == '.gz' else path.open()) as f:
        return list(csv.DictReader(f))

def intervals(day):
    assert day.year == 2023
    if day.weekday() >= 5 or (day.month,day.day) in HOLIDAYS:
        return []
    morning = DT.combine(day, DT.min.time())+TD(hours=10)
    extra = date(2023,3,13) <= day < date(2023,3,21)
    return [(morning,morning+TD(hours=4)),
            (morning+TD(hours=4,minutes=15 if extra else 5), morning+TD(hours=8,minutes=50))]

def window(at):
    return next((w for w in intervals(at.date()) if w[0] <= at and at+FIVE <= w[1]), None)

def clock_window(at):
    return next((w for w in intervals(at.date()) if w[0] <= at < w[1]), None)

def next_open(at):
    return at.replace(second=0,microsecond=0)-TD(minutes=at.minute%5)+FIVE

def tick(symbol, at):
    if symbol == 'CNYRUBF':
        return D('.01') if at < DT(2023,9,27,19) else D('.001')
    return {'USDRUBF':D('.01'),'GLDRUBF':D('.1'),'IMOEXF':D('.5')}[symbol]

def round_tick(value, step, up):
    return (value/step).to_integral_value(rounding=ROUND_CEILING if up else ROUND_FLOOR)*step

def source(root, manifest):
    assert git(root,'rev-parse','HEAD') == manifest['source_ref']
    assert not git(root,'status','--porcelain=v1','--untracked-files=all')
    budgets = json.loads((LAB/'results/stage2_causal_mtf_v1/input_provenance.json').read_text())['inputs']
    data, provenance = {}, {}
    for symbol,spec in sorted(manifest['inputs'].items()):
        assert git(root,'ls-files','--stage','--',spec['path']).split()[1] == spec['blob']
        path=root/spec['path']; before=path.stat(); count=budgets[symbol]['prefix_bytes_read']
        with path.open('rb',buffering=0) as f:
            raw=f.read(count)  # exact bytes; no read of following newline/EOF
        assert len(raw)==count and raw.endswith(b'\n') and sha(raw)==budgets[symbol]['prefix_sha256']
        lines=raw.decode('utf-8-sig').splitlines()
        assert lines[0]=='Ticker;Datetime;Open;High;Low;Close;Volume'
        assert len(lines)==spec['rows_2023']+1
        idx={}; zeros=0
        for line in lines[1:]:
            fields=line.split(';'); at=DT.fromisoformat(fields[1])
            assert at.year==2023 and fields[0]==symbol and at not in idx
            values=tuple(map(D,fields[2:])); o,h,l,c,v=values
            assert l<=min(o,c)<=max(o,c)<=h and v>=0
            zeros+=v==0; idx[at]=values
        assert list(idx)==sorted(idx)
        assert path.stat()==before
        data[symbol]=idx
        provenance[symbol]={'rows':len(idx),'bytes_read':count,'prefix_sha256':sha(raw),
                            'last':max(idx),'zero_volume_rows':zeros,'bytes_2024_plus_read':0}
    return data,provenance

def features(idx, strategy, delay):
    """Independent chronological arrays; shifted ATR12, Wilder14, local VWAP."""
    frames={}; history=[]; trs=[]; plus=[]; minus=[]; dxs=[]
    trsum=pdm=mdm=adx=ema=None; vw_sum=weight=ZERO; previous_vwap=None; previous_window=None
    for at,b in idx.items():
        w=window(at)
        if w is None or clock_window(at+TD(minutes=delay))!=w:
            continue
        o,h,l,c,v=b
        reset=(w!=previous_window or (history and at!=history[-1][0]+FIVE)
               or (strategy=='VWAP_MR' and v<=0))
        if reset:
            history=[];trs=[];plus=[];minus=[];dxs=[]
            trsum=pdm=mdm=adx=ema=None;vw_sum=weight=ZERO;previous_vwap=None
        previous_window=w
        prior_close=history[-1][1][3] if history else c
        atr=sum(trs[-12:],ZERO)/12 if len(history)>=13 else None
        weight+=v; vw_sum+=(h+l+c)/3*v
        vwap=vw_sum/weight if weight>0 else None
        high=max((x[1][1] for x in history[-12:]),default=None)
        low=min((x[1][2] for x in history[-12:]),default=None)
        mr=mom=0
        if atr is not None and atr>0:
            if previous_vwap is not None and prior_close<=previous_vwap-atr and vwap-atr<c<vwap:
                mr=1
            if previous_vwap is not None and prior_close>=previous_vwap+atr and vwap<c<vwap+atr:
                mr=-1
            mom=1 if c>high else -1 if c<low else 0
        old_ema=ema
        pdi=mdi=None
        if history:
            _,a=history[-1]
            tr=max(h-l,abs(h-a[3]),abs(l-a[3])); up=h-a[1]; down=a[2]-l
            pd=up if up>max(down,ZERO) else ZERO
            md=down if down>max(up,ZERO) else ZERO
            trs.append(tr);plus.append(pd);minus.append(md)
            if len(trs)==14:
                trsum=sum(trs,ZERO);pdm=sum(plus,ZERO);mdm=sum(minus,ZERO)
            elif trsum is not None:
                trsum=trsum-trsum/14+tr;pdm=pdm-pdm/14+pd;mdm=mdm-mdm/14+md
            if trsum is not None:
                pdi=100*pdm/trsum if trsum else ZERO;mdi=100*mdm/trsum if trsum else ZERO
                dx=100*abs(pdi-mdi)/(pdi+mdi) if pdi+mdi else ZERO
                dxs.append(dx)
                if len(dxs)==14: adx=sum(dxs,ZERO)/14
                elif adx is not None: adx=(13*adx+dx)/14
        history.append((at,b))
        if len(history)==50: ema=sum((x[1][3] for x in history),ZERO)/50
        elif ema is not None: ema+=D(2)/51*(c-ema)
        frames[at]={'direction':mr if strategy=='VWAP_MR' else mom,'atr_shifted':atr,
            'vwap_approx':vwap,'range_high_shifted':high,'range_low_shifted':low,
            'atr14':trsum/14 if trsum is not None else None,'adx14':adx,'plus_di14':pdi,'minus_di14':mdi,
            'ema50':ema,'ema50_slope':ema-old_ema if ema is not None and old_ema is not None else None,
            'swing_low':min(x[1][2] for x in history[-3:]),'swing_high':max(x[1][1] for x in history[-3:]),
            'signal_tr_atr':max(h-l,abs(h-prior_close),abs(l-prior_close))/atr if atr else None,
            'previous_close':prior_close,'previous_vwap':previous_vwap,'tr12_sum':atr*12 if atr is not None else None,
            'vwap_weight':weight,'vwap_weighted_sum':vw_sum,'segment_first':history[0][0],
            'prior_bars':len(history)-1}
        previous_vwap=vwap
    return frames

def mtf(idx, minutes, now, w, delay):
    latest=now-TD(minutes=minutes-5+delay)
    minute=latest.hour*60+latest.minute
    latest=latest.replace(hour=0,minute=0)+TD(minutes=minute-minute%minutes)
    starts=[latest-TD(minutes=minutes),latest]
    rec={'mtf_first_start':None,'mtf_last_start':None,'mtf_available_at':None,'mtf_direction':None,
         'mtf_reason':'MTF_TWO_PARENTS_NOT_READY','mtf_gate_eligible':False}
    if starts[0]<w[0]: return rec
    groups=[]
    for t in starts:
        times=[t+i*FIVE for i in range(minutes//5)]
        if any(x not in idx for x in times):
            rec['mtf_reason']='MTF_INCOMPLETE_CHILD_BUCKET';return rec
        kids=[idx[x] for x in times]
        groups.append((kids[0][0],max(b[1] for b in kids),min(b[2] for b in kids),kids[-1][3],sum((b[4] for b in kids),ZERO)))
    a,b=groups
    trend=1 if a[3]>a[0] and b[3]>b[0] and b[3]>a[3] else -1 if a[3]<a[0] and b[3]<b[0] and b[3]<a[3] else 0
    rec.update(mtf_first_start=starts[0],mtf_last_start=starts[1],mtf_available_at=latest+TD(minutes=minutes-5+delay),
               mtf_direction=trend,mtf_reason=None,groups=groups)
    assert rec['mtf_available_at']<=now and latest+TD(minutes=minutes)<=now
    return rec

def quality(s, price, strategy, step):
    d=s['direction_sign'];risk=d*(price-s['stop']);reward=d*(s['take']-price)
    if risk<4*step or risk<=0:return 'RISK_BELOW_FOUR_TICKS'
    if reward-2*step<risk+2*step:return 'NET_TARGET_BELOW_NET_RISK'
    if strategy=='MOMENTUM':
        extension=d*(price-s['edge'])/s['atr_shifted']
        if extension<=0:return 'BREAKOUT_NOT_PERSISTENT'
        if extension>1:return 'BREAKOUT_ALREADY_EXTENDED'
    return None

def oracle(idx,symbol,strategy,base,minutes,delay,frames):
    """Independent event state machine; journals are NOT an input."""
    management=base in ('MANAGEMENT','ENTRY_MANAGEMENT','FULL_M5','PAYABLE_CAP_FULL_M5')
    entry_quality=base in ('ENTRY','ENTRY_MANAGEMENT','FULL_M5','PAYABLE_CAP_ENTRY','PAYABLE_CAP_FULL_M5')
    regime=base in ('FULL_M5','PAYABLE_CAP_FULL_M5')
    signals=[];ledger=[];events=[];amends=[];position=None;order=None;close=None
    def event(now,kind,status,reason,sid,price=None,confirmed=None,flags=''):
        requested,filled,residual=1,0,1
        if kind in ('ENTRY','EXIT') and status=='MODELLED':filled,residual=1,0
        if kind in ('ENTRY_OUTCOME','CONTEXT_RESET'):residual=0
        if kind=='POSITION_PATH':requested=filled=residual=None
        if kind=='MODEL_FLAT_CONFIRMATION':requested=filled=None;residual=0
        events.append(dict(at=now,kind=kind,status=status,reason=reason,signal_id=sid,
                           reference_price=price,confirmed_at=confirmed,flags=flags,
                           requested_model_units=requested,filled_model_units=filled,residual_model_units=residual))
    def request(now,reason):
        nonlocal close
        if close is None:
            close=(next_open(now),reason)
            event(now,'EXIT_ORDER','SUBMITTED',reason,position['signal_id'])
    def finish(t,now,price,reason,flags=()):
        nonlocal position,close
        p=position;r=p['row'];s=p['signal'];d=s['direction_sign']
        if reason=='STOP' and management:
            reason={'BE':'BREAKEVEN_STOP','TRAIL':'TRAIL_STOP'}.get(p['state'],'STOP')
        event(t,'EXIT','MODELLED',reason,p['signal_id'],price,now,'|'.join(sorted(flags)))
        gross=d*(price-r['entry']);c1=tick(symbol,t)
        r.update(exit=price,exit_reason=reason,exit_interval_start=t,exit_interval_end=t+FIVE,exit_confirmed_at=now,
                 gross_price_pnl=gross,c1_exit=c1,c1_total=r['c1_entry']+c1,net_model_c1=gross-r['c1_entry']-c1,
                 status='MODELLED',exit_filled_model_units=1,residual_model_units=0,possible_residual_model_units=0,
                 model_flat_confirmed_at=now,model_flat_scenario_at=t,funding_and_emergency_costs='NO_SNAPSHOT_CROSSED',
                 holding_minutes_bar_starts=D((t-r['entry_interval_start']).total_seconds()/60),
                 ambiguity_flags='|'.join(sorted(flags)))
        r['net_R']=r['net_model_c1']/r['initial_risk_price_units'];position=None;close=None
    def resident(t,now,b,entry_bar=False):
        p=position;d=p['signal']['direction_sign'];step=tick(symbol,t)
        o,h,l,c,v=b;stop=p['stop'];take=p['signal']['take']
        sh=l<=stop if d==1 else h>=stop
        th=(h>=take+step if d==1 else l<=take-step) and not (management and strategy=='MOMENTUM' and not entry_bar)
        if sh:
            flags=[]
            if th:flags.append('AMBIGUOUS_STOP_TP')
            if entry_bar:flags.append('AMBIGUOUS_ENTRY_EXIT')
            if (o<=stop if d==1 else o>=stop):flags.append('ADVERSE_STOP_GAP')
            finish(t,now,min(o,stop) if d==1 else max(o,stop),'STOP',flags)
        elif th and not entry_bar:finish(t,now,take,'TAKE')
        elif not entry_bar and not (management and strategy=='MOMENTUM') and (h>=take if d==1 else l<=take):
            event(t,'TP','NONFILL','TOUCH_WITHOUT_TICK_PENETRATION',p['signal_id'],confirmed=now)
    first=min(idx).date();day=first
    while day<=date(2023,12,31):
        if intervals(day):
            now=DT.combine(day,DT.min.time())+TD(hours=10)
            end=now+TD(hours=9)
            while now<=end:
                t=now-TD(minutes=delay);b=idx.get(t);w=window(t)
                if b is not None and w:
                    if position:
                        p=position
                        if t>=p['boundary']:
                            # Every real instance is already UNKNOWN_PATH; retain liability.
                            p['reasons'].append('BOUNDARY_EXPOSURE_FUNDING_OR_EMERGENCY_UNRESOLVED')
                        while p['pending'] and t>=p['pending'][0]['effective_at']:
                            a=p['pending'].pop(0);p['stop']=a['stop'];p['state']=a['state']
                            p['row']['effective_stop_state']=p['state']
                            event(t,'STOP_AMENDMENT','MODELLED',p['state'],p['signal_id'],p['stop'],now)
                        if p['unknown']:
                            if close and t>=close[0]:
                                p['row'].update(status='UNRESOLVED',exit_reason='UNKNOWN_PATH_CONDITIONAL_REDUCE_ALL',
                                    gross_price_pnl=None,c1_exit=None,c1_total=None,net_model_c1=None,net_R=None,exit=None,
                                    exit_filled_model_units=None,residual_model_units=0,possible_residual_model_units=0,
                                    model_flat_confirmed_at=now,model_flat_scenario_at=t,
                                    unresolved_reasons='|'.join(dict.fromkeys(p['reasons'])),
                                    ambiguity_flags='UNKNOWN_PATH_OUTCOME',funding_and_emergency_costs='UNRESOLVED')
                                event(t,'MODEL_FLAT_CONFIRMATION','CONDITIONAL_MODEL_FLAT',
                                    'REDUCE_ALL_POSSIBLE_EXPOSURE_BRANCHES_NOT_A_KNOWN_TRADE_EXIT',p['signal_id'],confirmed=now)
                                position=None;close=None
                        elif close and t>=close[0]:finish(t,now,b[0],close[1])
                        elif t>p['row']['entry_interval_start']:resident(t,now,b)
                    if order and t==order['planned_execution_at']:
                        s=order;order=None;d=s['direction_sign'];step=tick(symbol,t)
                        reason=quality(s,b[0],strategy,step) if entry_quality else None
                        if reason:
                            s.update(status='NONFILL',reason=reason)
                            event(t,'ENTRY','NONFILL',reason,s['signal_id'],confirmed=now)
                        elif not (d*(b[0]-s['stop'])>0 and d*(s['take']-b[0])>0 and d*(b[0]-s['cap'])<=0):
                            s.update(status='NONFILL',reason='OPEN_CAP_OR_FROZEN_PROTECTION')
                            event(t,'ENTRY','NONFILL',s['reason'],s['signal_id'],confirmed=now)
                            event(now,'ENTRY_CANCEL','CANCELLED','ONE_BAR_TTL',s['signal_id'])
                        else:
                            s.update(status='MODELLED',reason='CONDITIONAL_OPEN_SCENARIO')
                            event(t,'ENTRY','MODELLED',s['reason'],s['signal_id'],b[0],now)
                            r={k:s[k] for k in ('signal_id','signal_at','available_at','ready_at','planned_execution_at','stop','take')}
                            r.update(entry_interval_start=t,entry_interval_end=t+FIVE,entry_confirmed_at=now,entry=b[0],
                                entry_cap=s['cap'],initial_risk_price_units=abs(b[0]-s['stop']),status='OPEN_MODELLED',
                                requested_model_units=1,entry_filled_model_units=1,entry_cancelled_model_units=0,
                                c1_entry=step,c1_exit=ZERO,c1_total=step,gross_price_pnl=ZERO,net_model_c1=None,net_R=None,
                                exit=None,exit_reason=None,exit_interval_start=None,exit_interval_end=None,exit_confirmed_at=None,
                                holding_minutes_bar_starts=None,exit_filled_model_units=0,residual_model_units=1,
                                possible_residual_model_units=0,model_flat_confirmed_at=None,model_flat_scenario_at=None,
                                flat_target_breach=False,ambiguity_flags='',unresolved_reasons='',funding_and_emergency_costs='PENDING')
                            ledger.append(r)
                            position={'signal_id':s['signal_id'],'signal':s,'row':r,'stop':s['stop'],'state':'INITIAL',
                                'pending':[],'best':b[0],'unknown':False,'reasons':[],'boundary':w[1]}
                            resident(t,now,b,True)
                            if management:r.update(effective_stop_state='INITIAL',runner=strategy=='MOMENTUM')
                if order and order['planned_execution_at']<=t:
                    s=order;s.update(status='NO_BAR_NO_MODEL_FILL',reason='NO_BAR_NO_MODEL_FILL')
                    event(s['planned_execution_at'],'ENTRY_OUTCOME',s['status'],s['reason'],s['signal_id'],confirmed=now);order=None
                if w and b is None:
                    if order:
                        s=order
                        if s['planned_execution_at']>now:
                            s.update(status='NONFILL',reason='GAP_CANCEL_BEFORE_POSSIBLE_ENTRY')
                            event(now,'ENTRY_CANCEL','CANCELLED',s['reason'],s['signal_id']);order=None
                        elif not s.get('gap_notice'):
                            s['gap_notice']=now
                            event(now,'CONTEXT_RESET','MODEL_SCENARIO_PENDING','OBSERVED_TARGET_REQUIRED_NO_LIVE_ORDER',s['signal_id'])
                    if position:
                        p=position;p['unknown']=True
                        p['row'].update(possible_residual_model_units=None,gross_price_pnl=None,c1_exit=None,c1_total=None)
                        if 'MISSING_PATH_EMERGENCY_OBLIGATIONS_UNRESOLVED' not in p['reasons']:
                            p['reasons'].append('MISSING_PATH_EMERGENCY_OBLIGATIONS_UNRESOLVED')
                        event(t,'POSITION_PATH','UNRESOLVED','MISSING_BAR_STOP_TAKE_OR_EXPOSURE_OUTCOME_UNKNOWN',p['signal_id'],confirmed=now)
                        request(now,'DATA_GAP_EMERGENCY')
                if position:
                    p=position;boundary=p['boundary'];entry=p['row']['entry_interval_start']
                    submit=boundary-TD(minutes=20)
                    while next_open(submit)+TD(minutes=delay)>boundary-TD(minutes=10):submit-=FIVE
                    if now>=submit:request(now,'SESSION_FLAT')
                    elif now>=entry+TD(minutes=55 if strategy=='VWAP_MR' else 85):request(now,'MAX_HOLD')
                    if now>=boundary-TD(minutes=10) and not p['row']['flat_target_breach']:
                        p['row']['flat_target_breach']=True
                        event(now,'FLAT_TARGET','UNCONFIRMED','NO_CONFIRMED_FLAT_AT_B_MINUS_10',p['signal_id'])
                f=frames.get(t)
                if f is not None:
                    if management and position and close is None and not position['unknown']:
                        p=position;s=p['signal'];d=s['direction_sign'];r=p['row']['initial_risk_price_units']
                        age=t-p['row']['entry_interval_start'];progress=d*(b[3]-p['row']['entry'])
                        if strategy=='VWAP_MR':
                            swing=s['swing_low'] if d==1 else s['swing_high']
                            if d*(b[3]-swing)<0:request(now,'VWAP_PREMISE_FAILED')
                            elif age>=TD(minutes=30) and progress<=0:request(now,'VWAP_NO_PROGRESS_30M')
                        else:
                            if d*(b[3]-s['edge'])<=0:request(now,'FAILED_BREAKOUT')
                            elif age>=TD(minutes=30) and progress<D('.5')*r:request(now,'MOMENTUM_NO_PROGRESS_30M')
                            else:
                                favorable=b[1] if d==1 else b[2]
                                p['best']=max(p['best'],favorable) if d==1 else min(p['best'],favorable)
                                candidate=None;state=None;step=tick(symbol,now)
                                if progress>=r:candidate=p['row']['entry']+d*2*step;state='BE'
                                if progress>=2*r and f['atr14'] is not None:
                                    trail=p['best']-d*2*f['atr14']
                                    if candidate is None or d*(trail-candidate)>0:candidate=trail;state='TRAIL'
                                if candidate is not None:
                                    candidate=round_tick(candidate,step,d==1)
                                    current=p['pending'][-1]['stop'] if p['pending'] else p['stop']
                                    if d*(candidate-current)>0:
                                        if d*(candidate-b[3])>=0:request(now,'TRAIL_ALREADY_MARKETABLE')
                                        else:
                                            a=dict(signal_id=p['signal_id'],decided_at=now,effective_at=next_open(now),stop=candidate,state=state)
                                            p['pending'].append(a);amends.append(a)
                                            event(now,'STOP_AMEND_ORDER','SUBMITTED',state,p['signal_id'],candidate)
                    if f['direction']:
                        d=f['direction'];step=tick(symbol,now);atr=f['atr_shifted'];c=b[3]
                        s={k:v for k,v in f.items() if k not in ('direction',)}
                        s.update(signal_id=f'{strategy}_{symbol}_{len(signals)+1:06d}',signal_at=t,available_at=now,ready_at=now,
                            planned_execution_at=next_open(now),signal_close=c,direction_sign=d,direction='LONG' if d==1 else 'SHORT',
                            stop=round_tick(c-d*D('1.5')*atr,step,d==1),
                            take=round_tick(f['vwap_approx'] if strategy=='VWAP_MR' else c+d*3*atr,step,d==1),
                            cap=round_tick(c+d*D('.25')*atr,step,d==-1),status='SUBMITTED',reason='')
                        s['edge']=f['range_high_shifted'] if d==1 else f['range_low_shifted']
                        signals.append(s);target=s['planned_execution_at']
                        if position or order:s.update(status='SKIPPED',reason='POSITION_OR_ORDER_BUSY')
                        elif window(target)!=w or target+FIVE>w[1]-TD(minutes=30):s.update(status='SKIPPED',reason='KNOWN_BOUNDARY_ENTRY_CUTOFF')
                        elif not (d*(c-s['stop'])>0 and d*(s['take']-c)>0):s.update(status='SKIPPED',reason='INVALID_ROUNDED_LEVELS')
                        else:
                            order=s;event(now,'ENTRY_ORDER','SUBMITTED','FIXED_SIGNAL',s['signal_id'])
                            reason=None
                            if management:
                                a=f['atr14']
                                if a is None or a<=0:reason='ATR14_NOT_READY'
                                else:
                                    structure=s['edge']-d*D('.5')*a if strategy=='MOMENTUM' else (f['swing_low']-step if d==1 else f['swing_high']+step)
                                    raw=c-d*D('1.5')*a
                                    s['stop']=round_tick(min(raw,structure) if d==1 else max(raw,structure),step,d==1)
                            if entry_quality and not reason:
                                if base.startswith('PAYABLE'):
                                    bound=round_tick((s['take']+s['stop']-d*4*step)/2,step,d==-1)
                                    s['cap']=min(s['cap'],bound) if d==1 else max(s['cap'],bound);s['payable_cap']=s['cap']
                                reason=quality(s,s['cap'],strategy,step)
                                if strategy=='MOMENTUM' and not reason:
                                    if d*(c-s['edge'])>atr:reason='SIGNAL_ALREADY_EXTENDED'
                                    elif f['signal_tr_atr']>2:reason='SIGNAL_RANGE_EXPANSION_GT_2_ATR'
                            if regime and not reason:
                                adx,pdi,mdi=f['adx14'],f['plus_di14'],f['minus_di14']
                                aligned=(pdi>mdi if d==1 else mdi>pdi) if pdi is not None else False
                                if adx is None:reason='ADX14_NOT_READY'
                                elif strategy=='MOMENTUM' and (adx<25 or not aligned):reason='MOMENTUM_ADX_DI_REGIME'
                                elif strategy=='VWAP_MR' and adx>=25 and not aligned:reason='VWAP_STRONG_ADVERSE_ADX_DI'
                            if reason:
                                s.update(status='FILTERED',reason=reason);order=None
                                event(now,'ENTRY_CANCEL','CANCELLED',reason,s['signal_id'])
                        if minutes:
                            context=mtf(idx,minutes,now,w,delay);trend=context['mtf_direction']
                            eligible=trend==d if strategy=='MOMENTUM' else trend is not None and trend!=-d
                            context['mtf_gate_eligible']=eligible
                            if trend is not None and not eligible:context['mtf_reason']='MTF_DIRECTION_NOT_ALIGNED' if strategy=='MOMENTUM' else 'MTF_SUSTAINED_ADVERSE_DIRECTION'
                            s.update(context)
                            if s['status']=='SUBMITTED' and not eligible:
                                s.update(status='FILTERED',reason=context['mtf_reason']);order=None
                                event(now,'ENTRY_CANCEL','CANCELLED',s['reason'],s['signal_id'])
                now+=FIVE
        day+=TD(days=1)
    assert position is None and order is None, 'Unexpected terminal branch: report INCONCLUSIVE before extending oracle'
    return signals,ledger,events,amends

NUMERIC={'signal_close','atr_shifted','vwap_approx','range_high_shifted','range_low_shifted','stop','take','cap',
    'atr14','adx14','plus_di14','minus_di14','ema50','ema50_slope','signal_tr_atr','swing_low','swing_high','payable_cap',
    'entry','exit','entry_cap','initial_risk_price_units','gross_price_pnl','c1_entry','c1_exit','c1_total','net_model_c1','net_R',
    'holding_minutes_bar_starts','reference_price'}

def equal(a,b,k):
    if a is None:return b==''
    if k in NUMERIC:
        return b!='' and D(str(a))==D(b)
    return str(a)==b

def compare(actual,expected,fields,label,errors,counts):
    counts[label+'_rows']+=len(actual)
    if len(actual)!=len(expected):errors.append({'table':label,'lengths':[len(actual),len(expected)]})
    for a,b in zip(actual,expected):
        for k in fields:
            if not equal(a.get(k),b.get(k,''),k):
                counts['mismatches']+=1
                if len(errors)<40:errors.append({'table':label,'signal_id':a.get('signal_id'),'field':k,'oracle':a.get(k),'journal':b.get(k)})

def metrics_audit(data,ledger,rows,errors,counts):
    """Recompute every year/month/direction diagnostic, never impute unknowns."""
    groups=defaultdict(list)
    for r in ledger:groups[r['run'],r['architecture'],r['scenario']].append(r)
    coverage={}
    for symbol,idx in data.items():
        for month in range(1,13):
            day=date(2023,month,1);expected=set()
            while day.year==2023 and day.month==month:
                for start,end in intervals(day):
                    while start+FIVE<=end:expected.add(start);start+=FIVE
                day+=TD(days=1)
            observed=expected.intersection(idx)
            cov='NO_COVERAGE' if not observed else 'PARTIAL_COVERAGE' if expected-observed else 'COVERED'
            coverage[symbol,f'2023-{month:02d}']=(cov,len(expected),len(observed),len(expected-observed),sum(t<min(idx) for t in expected))
    for old in rows:
        cohort=groups[old['run'],old['architecture'],old['scenario']]
        monthly=old['group']=='MONTH';period=old['period'];direction=old['direction']
        selected=[r for r in cohort if (not monthly or str(r['entry_interval_start']).startswith(period))
                  and (direction=='ALL' or ('LONG' if r['entry']>r['stop'] else 'SHORT')==direction)]
        known=[r for r in selected if r['net_model_c1'] is not None]
        nets=[r['net_model_c1'] for r in known];gross=[r['gross_price_pnl'] for r in known]
        c2=[r['gross_price_pnl']-2*r['c1_total'] for r in known]
        def pf(values):
            loss=-sum((v for v in values if v<0),ZERO)
            return sum((v for v in values if v>0),ZERO)/loss if loss else None
        def average(values):return sum(values,ZERO)/len(values) if values else None
        unknown=sum(r['status']=='UNRESOLVED' for r in selected)
        cov=coverage[old['instrument'],period][0] if monthly else ('COVERED' if all(coverage[old['instrument'],f'2023-{m:02d}'][0]=='COVERED' for m in range(1,13)) else 'PARTIAL_COVERAGE')
        # All source unknown reductions occur in their entry month; assert this
        # rather than borrowing the journal's spanning-exposure classification.
        assert all(r['status']!='UNRESOLVED' or str(r['entry_interval_start'])[:7]==str(r['model_flat_confirmed_at'])[:7] for r in cohort)
        # Published monthly acceptance is conservative at instrument/cohort
        # level: an unknown SHORT also blocks that cohort's LONG calendar PASS.
        spanning=monthly and any(r['status']=='UNRESOLVED' and str(r['entry_interval_start'])[:7]<=period<=str(r['model_flat_confirmed_at'])[:7] for r in cohort)
        full=cov=='COVERED' and not (unknown or spanning)
        status='NO_COVERAGE' if cov=='NO_COVERAGE' else 'UNRESOLVED' if unknown or spanning else 'PARTIAL_COVERAGE' if cov!='COVERED' else 'ZERO_TRADES' if not selected else 'COMPLETE'
        cumulative=peak=dd=ZERO
        for value in nets:cumulative+=value;peak=max(peak,cumulative);dd=max(dd,peak-cumulative)
        exit_counts=Counter(r['exit_reason'] for r in selected)
        new=dict(trades=len(selected),closed_accounted_trades=len(known),unresolved=unknown,
            spanning_unknown_exposure=spanning,coverage_status=cov,metric_status=status,full_period_accounted=full,
            Net=sum(nets,ZERO) if full else None,net_model_c1=sum(nets,ZERO) if full else None,PF=pf(nets) if full else None,
            full_PF=pf(nets) if full else None,Drawdown=None,full_Drawdown=None,
            closed_only_gross=sum(gross,ZERO) if known else None,closed_only_c1=sum((r['c1_total'] for r in known),ZERO) if known else None,
            closed_only_net_c1=sum(nets,ZERO) if known else None,net_PF_closed_diagnostic=pf(nets),gross_PF_closed_diagnostic=pf(gross),
            net_expectancy_closed_diagnostic=average(nets),net_win_rate_closed_diagnostic=D(sum(n>0 for n in nets))/len(nets) if nets else None,
            closed_only_drawdown_price_units=dd if known else None,net_R_closed_diagnostic=sum((r['net_R'] for r in known),ZERO) if known else None,
            mean_net_R_closed_diagnostic=average([r['net_R'] for r in known]),gross_R_closed_diagnostic=sum((r['gross_price_pnl']/r['initial_risk_price_units'] for r in known),ZERO) if known else None,
            mean_win=average([v for v in nets if v>0]),mean_loss_magnitude=average([-v for v in nets if v<0]),
            entry_count=len(selected),stop_count=exit_counts['STOP'],take_count=exit_counts['TAKE'],BE_count=exit_counts['BREAKEVEN_STOP'],trailing_count=exit_counts['TRAIL_STOP'],
            C2_closed_net_stress=sum(c2,ZERO) if known else None,C2_PF_closed_stress=pf(c2))
        if monthly:
            new.update(zip(('expected_calendar_research_slots','observed_calendar_research_slots','missing_calendar_research_slots','pre_source_inception_slots'),coverage[old['instrument'],period][1:]))
        numeric=set(new)-{'spanning_unknown_exposure','coverage_status','metric_status','full_period_accounted'}
        NUMERIC.update(numeric)
        compare([new],[old],list(new),'metrics',errors,counts)
    return {f'{s}/{m}':dict(zip(('status','expected','observed','missing','pre_inception'),values)) for (s,m),values in coverage.items()}

def context_checks(data,signals,counts):
    totals=Counter();clock_digest=hashlib.sha256();metadata=Counter()
    for symbol,idx in data.items():
        for minutes in (15,30,60):
            for day in sorted({at.date() for at in idx}):
                for w in intervals(day):
                    start=w[0].replace(hour=0,minute=0)+TD(minutes=((w[0].hour*60+w[0].minute+minutes-1)//minutes)*minutes)
                    while start+TD(minutes=minutes)<=w[1]:
                        children=[start+i*FIVE for i in range(minutes//5)]
                        if all(t in idx for t in children):totals[f'{minutes}_complete']+=1
                        else:totals[f'{minutes}_incomplete']+=1
                        start+=TD(minutes=minutes)
                    for delay in (10,15):
                        now=w[0]
                        while now<w[1]:
                            context=mtf(idx,minutes,now,w,delay)
                            if context['mtf_direction'] is not None:
                                assert context['mtf_available_at']<=now
                                assert context['mtf_last_start']-context['mtf_first_start']==TD(minutes=minutes)
                            clock_digest.update(encoded((symbol,minutes,delay,now,context)).encode())
                            counts['all_MTF_decision_clocks']+=1;now+=FIVE
    assert [totals[f'{m}_complete'] for m in (15,30,60)]==[20433,8986,3567]
    for s in signals:
        if s['base_architecture']!='FROZEN_V2' and s['scenario']=='C1_T15_DELAY':
            metadata['T15_indicator_label_nominal_T10']+=1
    # Real-data metamorphic check: perturb future candles; past features/MTF
    # remain identical. Remove each latest M30 child; older pair cannot survive.
    idx=data['USDRUBF'];day=min(t.date() for t in idx);cut=DT.combine(day,DT.min.time())+TD(hours=12)
    changed={t:(tuple(x+D(100) for x in b[:4])+(b[4],) if t>cut else b) for t,b in idx.items() if t.date()==day}
    original={t:b for t,b in idx.items() if t.date()==day}
    for strategy in ('VWAP_MR','MOMENTUM'):
        fa=features(original,strategy,10);fb=features(changed,strategy,10)
        assert {t:f for t,f in fa.items() if t<=cut}=={t:f for t,f in fb.items() if t<=cut}
    w=window(cut);pair=mtf(original,30,cut,w,10)
    assert pair==mtf(changed,30,cut,w,10) and pair['mtf_direction'] is not None
    for i in range(6):
        missing=dict(original);missing.pop(pair['mtf_last_start']+i*FIVE)
        assert mtf(missing,30,cut,w,10)['mtf_reason']=='MTF_INCOMPLETE_CHILD_BUCKET'
    e=[];c=Counter();compare([{'signal_id':'probe','net_R':D(1)}],[{'signal_id':'probe','net_R':'2'}],['net_R'],'mutation',e,c)
    assert c['mismatches']==1
    return dict(composition=totals,all_clock_sha256=clock_digest.hexdigest(),metamorphic_checks='PASS: future perturbation, each of six missing latest children, corrupted payoff rejected',metadata_observation=metadata)

def main():
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    assert out.is_relative_to(Path('/workspace/work')) or out.is_relative_to(LAB/'results/stage2_final_independent_audit')
    assert not out.exists(), 'Use a NEW folder; frozen outputs are never overwritten'
    manifest=json.loads((LAB/'config/stage2_causal_mtf_v1.json').read_text())
    assert sha((LAB/'config/stage2_causal_mtf_v1.json').read_bytes())=='6588f77d8fe7fc8c087f267e4ca3e76414d3ce221ecbe3ba4618b199fb09cd00'
    original={path:git(LAB.parent,'rev-parse',f'{HEAD}:{path}') for path in git(LAB.parent,'ls-tree','--name-only',HEAD).splitlines() if path!='IntradayLab'}
    assert all(git(LAB.parent,'rev-parse',f'{MAIN}:{path}')==blob for path,blob in original.items())
    frozen={path:sha((LAB.parent/path).read_bytes()) for path in git(LAB.parent,'ls-tree','-r','--name-only',HEAD,'IntradayLab').splitlines()}
    data,provenance=source(a.data_root,manifest)
    folder=LAB/'results/stage2_causal_mtf_v1'
    tables={name:table(folder/(name+'.csv')) for name in ('signals','trade_ledger','execution_events','stop_amendments')}
    grouped={name:defaultdict(list) for name in tables}
    for name,rows in tables.items():
        for r in rows:grouped[name][(r['run'],r['architecture'],r['scenario'])].append(r)
    errors=[];counts=Counter();reconstructed=[];all_signals=[];all_events=[];all_amends=[];runs=[]
    for item in manifest['run_matrix']:
        symbol,strategy=item['instrument'],item['strategy'];idx=data[symbol]
        for delay in (10,15):
            frames=features(idx,strategy,delay)
            counts['all_decision_observations']+=len(frames)
            for variant in manifest['variants'][strategy]:
                base,minutes=variant['base'],variant['minutes'];arch=base+'__'+variant['tf'];scenario='C1_T10' if delay==10 else 'C1_T15_DELAY'
                run=f'{strategy}_{symbol}';key=(run,arch,scenario)
                signals,ledger,events,amends=oracle(idx,symbol,strategy,base,minutes,delay,frames)
                sf=['signal_id','signal_at','available_at','ready_at','planned_execution_at','direction','direction_sign','signal_close',
                    'atr_shifted','vwap_approx','range_high_shifted','range_low_shifted','stop','take','cap','status','reason']
                if base!='FROZEN_V2':sf+=['atr14','adx14','plus_di14','minus_di14','ema50','ema50_slope','signal_tr_atr','swing_low','swing_high','payable_cap']
                if minutes:sf+=['mtf_first_start','mtf_last_start','mtf_available_at','mtf_direction','mtf_gate_eligible','mtf_reason']
                compare(signals,grouped['signals'][key],sf,'signals',errors,counts)
                lf=list(ledger[0]) if ledger else []
                if base=='FROZEN_V2':lf=[k for k in lf if k not in ('runner','effective_stop_state')]
                compare(ledger,grouped['trade_ledger'][key],lf,'ledger',errors,counts)
                compare(events,grouped['execution_events'][key],list(events[0]) if events else [],'events',errors,counts)
                compare(amends,grouped['stop_amendments'][key],['signal_id','decided_at','effective_at','stop','state'],'amendments',errors,counts)
                meta=dict(run=run,instrument=symbol,strategy=strategy,architecture=arch,base_architecture=base,scenario=scenario)
                reconstructed.extend(r|meta for r in ledger);all_signals.extend(s|meta for s in signals)
                all_events.extend(e|meta for e in events);all_amends.extend(r|meta for r in amends)
                known=[r for r in ledger if r['net_model_c1'] is not None]
                wins=sum((r['net_model_c1'] for r in known if r['net_model_c1']>0),ZERO)
                losses=-sum((r['net_model_c1'] for r in known if r['net_model_c1']<0),ZERO)
                runs.append(meta|dict(signals=len(signals),entries=len(ledger),known=len(known),unknown=len(ledger)-len(known),
                    gross=sum((r['gross_price_pnl'] for r in known),ZERO) if known else None,
                    c1=sum((r['c1_total'] for r in known),ZERO) if known else None,
                    net=sum((r['net_model_c1'] for r in known),ZERO) if known else None,pf=wins/losses if losses else None,
                    reasons=dict(Counter(s['reason'] for s in signals))))
                print(run,arch,scenario,'signals',len(signals),'trades',len(ledger),'mismatches',counts['mismatches'],flush=True)
    calendar=metrics_audit(data,reconstructed,table(folder/'metrics.csv'),errors,counts)
    context=context_checks(data,all_signals,counts)
    # Metadata field is hardcoded T10 in production even in T15. Confirm its
    # exact extent; this field is not consumed by the execution state machine.
    labels=[s for s in tables['signals'] if s['indicator_available_at'] and s['scenario']=='C1_T15_DELAY']
    assert all(DT.fromisoformat(s['indicator_available_at'])==DT.fromisoformat(s['signal_at'])+TD(minutes=10)
               and DT.fromisoformat(s['available_at'])==DT.fromisoformat(s['signal_at'])+TD(minutes=15) for s in labels)
    context['metadata_observation']={'T15_indicator_available_at_five_minutes_early':len(labels),
        'execution_effect':'NONE: release/decision/order/stop clocks use actual scenario availability'}
    assert all(sha((LAB.parent/path).read_bytes())==digest for path,digest in frozen.items())
    assert git(a.data_root,'rev-parse','HEAD')==manifest['source_ref'] and not git(a.data_root,'status','--porcelain=v1','--untracked-files=all')
    counts['mismatches']+=0
    out.mkdir(parents=True)
    result=dict(status='PASS' if not errors else 'MISMATCH_REQUIRES_REVIEW',counts=counts,errors=errors,runs=runs,
        inputs=provenance,context=context,calendar=calendar,source_ref=manifest['source_ref'],audited_head=HEAD,main_before=MAIN,protected_roots=original,
        frozen_files_checked=len(frozen),all_prior_files_sha256=frozen,oracle_sha256=sha(Path(__file__).read_bytes()),
        independence='stdlib only, no production imports or Replay calls; journals compared after reconstruction',
        numeric_comparison='Exact Decimal equality, including recursive indicators, prices, P&L and R; exact timestamps/statuses')
    (out/'audit.json').write_text(encoded(result))
    with (out/'run_summary.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=[k for k in runs[0] if k!='reasons'],lineterminator='\n');writer.writeheader()
        writer.writerows({k:v for k,v in r.items() if k!='reasons'} for r in runs)
    # Intermediate derivative evidence stays outside the repository.
    (out/'reconstructed.json').write_text(encoded(dict(signals=all_signals,ledger=reconstructed,events=all_events,amendments=all_amends)))
    if errors:raise SystemExit(1)

if __name__=='__main__':main()
