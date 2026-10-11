"""Independent raw-M5 batch construction/path/report oracle; standard library only.

No production strategy, Backtester, loader, calendar, execution or metrics imports.
Implementation independence by the task author, not external human signoff.
"""
import argparse
from collections import Counter
import csv
from datetime import date, datetime, timedelta
from decimal import Decimal as D, ROUND_CEILING, ROUND_FLOOR
import hashlib
import json
from pathlib import Path
from zoneinfo import ZoneInfo

FIVE=timedelta(minutes=5)
ZERO=D(0)


def require(ok, label):
    if not ok:
        raise AssertionError(label)


def stamp(day, clock, cfg):
    return datetime.fromisoformat(str(day)+' '+clock).replace(tzinfo=ZoneInfo(cfg['timezone']))


def windows(day,cfg):
    if day.weekday()>=5 or day.strftime('%m-%d') in cfg['calendar']['holidays']:
        return []
    ws=[list(w) for w in cfg['calendar']['windows']]
    ext=cfg['calendar']['extended_lunch']
    if ext['start']<=str(day)<ext['end_exclusive']:
        ws[1][0]=ext['pm_start']
    return [(stamp(day,a,cfg),stamp(day,z,cfg)) for a,z in ws]


def tick(symbol,at,cfg):
    return D([v for t,v in cfg['tick_schedule'][symbol] if stamp(t[:10],t[11:],cfg)<=at][-1])


def good_open(b,t):
    return b is not None and b['o'].is_finite() and b['o']>0 and b['o']%t==0


def good(b,t):
    if not b or not all(b[k].is_finite() for k in ('o','h','l','c','v')):
        return False
    return b['v']>0 and 0<b['l']<=min(b['o'],b['c'])<=max(b['o'],b['c'])<=b['h'] and all(b[k]%t==0 for k in ('o','h','l','c'))


def read_source(root,cfg):
    result={}
    for symbol in cfg['instruments']:
        spec=cfg['inputs'][symbol]
        with (root/spec['path']).open('rb',buffering=0) as f:
            raw=f.read(spec['prefix_bytes'])
        require(len(raw)==spec['prefix_bytes'] and hashlib.sha256(raw).hexdigest()==spec['prefix_sha256'],'PREFIX_HASH')
        lines=raw.decode('utf-8-sig').splitlines()
        require(lines[0]=='Ticker;Datetime;Open;High;Low;Close;Volume','HEADER')
        require(len(lines)-1==spec['rows_2023'],'ROW_BUDGET')
        rows={}
        for line in lines[1:]:
            sym,ts,*values=line.split(';')
            at=datetime.fromisoformat(ts).replace(tzinfo=ZoneInfo(cfg['timezone']))
            require(sym==symbol and at.year==2023 and at not in rows,'SOURCE_SCOPE')
            rows[at]=dict(zip(('o','h','l','c','v'),map(D,values)))
        require(list(rows)==sorted(rows),'SOURCE_ORDER')
        result[symbol]=rows
    return result


def constructions(symbol,raw,cfg):
    """Batch contiguous spans; each side walks a first-level lifetime independently."""
    events=[];candidates=[];day=date(2023,1,1);first=min(raw).date()
    while day.year==2023:
        ws=windows(day,cfg) if day>=first else []
        for wi,(a,z) in enumerate(ws):
            slots=[];at=a
            while at<z:
                slots.append(at);at+=FIVE
            i=0
            while i<len(slots):
                at=slots[i];grid=tick(symbol,at,cfg)
                if not good(raw.get(at),grid):
                    i+=1;continue
                j=i+1
                while j<len(slots) and tick(symbol,slots[j],cfg)==grid and good(raw.get(slots[j]),grid):
                    j+=1
                span=slots[i:j]
                if j<len(slots):
                    reset_at=slots[j]+FIVE
                    reason='TICK_CHANGE' if tick(symbol,slots[j],cfg)!=grid else 'MISSING_OR_INVALID_BAR'
                elif wi+1<len(ws):
                    reset_at=ws[wi+1][0]+FIVE;reason='SESSION_CHANGE'
                else:
                    reset_at=z;reason='DAY_END'
                for side in (-1,1):
                    k=5
                    while k<len(span):
                        start=span[k];b=raw[start];level=b['h' if side==-1 else 'l']
                        prior=[raw[t]['h' if side==-1 else 'l'] for t in span[k-5:k]]
                        local=level>max(prior) if side==-1 else level<min(prior)
                        if not local:
                            k+=1;continue
                        ident=f'C1_{symbol}_{day}_{"LONG" if side==1 else "SHORT"}_{start:%H%M}_{int(level/grid)}'
                        def receipt(kind,when,**fields):
                            events.append(dict(instrument=symbol,direction=side,construction_id=ident,
                                first_start=start,level=level,tick=grid,event=kind,observed_at=when,**fields))
                        receipt('FIRST',start+FIVE,bar_start=start,extreme=level,previous_extrema=prior,previous_starts=span[k-5:k])
                        hits=[(start,level)];retreats=[];armed=False;consumed=False
                        max_h,min_l=b['h'],b['l'];end=k+1;reset_reason=reason;when=reset_at
                        while end<len(span):
                            t=span[end];b=raw[t];x=b['h' if side==-1 else 'l']
                            if end-k>=24 or side*(x-level)<-2*grid:
                                reset_reason='EXPIRED_24_BARS' if end-k>=24 else 'OUTER_ZONE_BREAK'
                                when=t+FIVE;break
                            max_h,min_l=max(max_h,b['h']),min(min_l,b['l'])
                            if not consumed:
                                if armed and abs(x-level)<=2*grid:
                                    hits.append((t,x));armed=False
                                    receipt('SECOND' if len(hits)==2 else 'THIRD',t+FIVE,bar_start=t,extreme=x)
                                    if len(hits)==3:
                                        consumed=True;boundary=max_h if side==-1 else min_l
                                        close_d=side*(b['c']-level)/grid
                                        candidates.append(dict(signal_id=ident,cluster_id=ident,construction_id=ident,
                                            instrument=symbol,direction=side,signal_at=t+FIVE,signal_bar_start=t,
                                            signal_bar_closed_at=t+FIVE,construction_start=start,construction_bars=end-k+1,
                                            level=level,signal_tick=grid,signal_close=b['c'],close_distance_ticks=close_d,
                                            construction_max_high=max_h,construction_min_low=min_l,boundary=boundary,
                                            approach_starts=[p[0] for p in hits],approach_extrema=[p[1] for p in hits],
                                            retreat_starts=[p[0] for p in retreats],retreat_extrema=[p[1] for p in retreats],
                                            retreat_depth_ticks=[p[2] for p in retreats],
                                            approach_separation_bars=[(hits[n+1][0]-hits[n][0])//FIVE for n in (0,1)],
                                            observed_touch_width_ticks=(max(p[1] for p in hits)-min(p[1] for p in hits))/grid,
                                            allowed_zone_width_ticks=4,stop=boundary-side*grid,
                                            target_mode='FULL_NET_C1_R',target_net_R='3',max_hold_calendar_minutes=120,
                                            base_reason='SIGNAL' if close_d>=1 else 'THIRD_CLOSE_NOT_REJECTED',window_end=z))
                                elif not armed and side*(x-level)>=3*grid:
                                    depth=side*(x-level)/grid;armed=True;retreats.append((t,x,depth))
                                    receipt('RETREAT',t+FIVE,bar_start=t,extreme=x,depth_ticks=depth,after_approach=len(hits))
                            end+=1
                        receipt('RESET',when,reason=reset_reason,approaches=len(hits),consumed=consumed)
                        k=end
                i=j
        day+=timedelta(days=1)
    pairs=Counter(s['signal_at'] for s in candidates if s['base_reason']=='SIGNAL')
    for s in candidates:
        if s['base_reason']=='SIGNAL' and pairs[s['signal_at']]==2:
            s['base_reason']='AMBIGUOUS_BOTH_SIDES'
    return sorted(candidates,key=lambda s:(s['signal_at'],s['signal_id'])),events


def replay(symbol,raw,candidates,cfg):
    ss=[];tt=[];xx=[];skips=[];active=None;prior=False
    by_time={}
    for s in candidates:by_time.setdefault(s['signal_at'],[]).append(s)
    day=date(2023,1,1)
    while day.year==2023:
        blocked=False;at=stamp(day,'00:00:00',cfg);last=at+timedelta(days=1)
        while at<=last:
            current=raw.get(at);previous=raw.get(at-FIVE)
            def finish(price,reason,point=False,conflict=False):
                nonlocal active
                q=active.copy();q.pop('deadline');q.update(status='CLOSED',exit_reason=reason,
                    exit_price=price,exit_at=at if point else None,
                    exit_interval_start=at if point else at-FIVE,exit_interval_end=at,resolved_at=at,
                    stop_take_conflict=conflict)
                gross=q['direction']*(price-q['entry_price']);cost=q['entry_tick']+tick(symbol,q['exit_interval_start'],cfg)
                q.update(exit_tick=tick(symbol,q['exit_interval_start'],cfg),gross=gross,gross_R=gross/q['risk'],
                    cost_c1=cost,cost_R=cost/q['risk'],net_c1=gross-cost,net_R_c1=(gross-cost)/q['risk'],
                    realized_net_to_net_R=(gross-cost)/(q['risk']+cost))
                tt.append(q);active=None
            def exclude(reason,slot):
                nonlocal active,blocked
                q=active.copy();q.pop('deadline');q.update(status='DATA_QUALITY_EXCLUDED',
                    exclusion_reason=reason,gap_interval_start=slot,gap_interval_end=slot+FIVE,gap_detected_at=at,
                    remainder_of_day_blocked=True,exit_price=None,exit_at=None,resolved_at=None,
                    exit_interval_start=None,exit_interval_end=None,exit_reason=None)
                xx.append(q);active=None;blocked=True
            if active and active['entry_at']<=at-FIVE<active['deadline']:
                q=active;side=q['direction']
                if not good(previous,tick(symbol,at-FIVE,cfg)):
                    exclude('MISSING_EXPOSED_BAR' if previous is None else 'INVALID_EXPOSED_BAR',at-FIVE)
                else:
                    stop_hit=previous['l']<=q['stop'] if side==1 else previous['h']>=q['stop']
                    take_hit=previous['h']>=q['take'] if side==1 else previous['l']<=q['take']
                    if stop_hit:finish(q['stop'],'STOP',conflict=take_hit)
                    elif take_hit and at-FIVE!=q['entry_at']:finish(q['take'],'TAKE')
            if active:
                q=active;side=q['direction']
                if not good_open(current,tick(symbol,at,cfg)):
                    exclude('MISSING_EXPOSED_BAR' if current is None else 'INVALID_EXPOSED_OPEN',at)
                elif side*(current['o']-q['stop'])<=0:
                    finish(current['o'],'STOP',point=True)
                elif at==q['deadline']:
                    finish(current['o'],'TIME' if at==q['entry_at']+timedelta(minutes=120) else 'SESSION_FLAT',point=True)
            for candidate in by_time.get(at,[]):
                s=dict(candidate,status='REJECTED',reason=candidate['base_reason'],model_filled=False,
                    order_admitted=False,prior_exclusion_requires_flat_assumption=prior,
                    initial_flat_assumed=True,initial_flat_proven=False)
                if s['base_reason']=='SIGNAL':
                    s.update(planned_execution_at=at,entry_mode='ENTRY_NEXT_OPEN')
                    if blocked:s['reason']='DATA_QUALITY_POSITION_BLOCK'
                    elif active:s['reason']='POSITION_BUSY'
                    elif at>=s['window_end']-FIVE:s['reason']='SESSION_LIMIT'
                    elif not good_open(current,tick(symbol,at,cfg)):
                        s.update(status='DATA_GAP_SKIP',reason='MISSING_EXECUTION_BAR' if current is None else 'INVALID_EXECUTION_OPEN',
                            attempted_execution_at=at,gap_detected_at=at)
                        skips.append(s.copy())
                    else:
                        entry=current['o'];grid=tick(symbol,at,cfg);side=s['direction'];risk=side*(entry-s['stop']);distance=side*(entry-s['boundary'])
                        s.update(entry_open=entry,entry_tick=grid)
                        reason=('OPEN_WRONG_SIDE_OF_CONSTRUCTION' if distance<0 else
                            'INVALID_STOP_GEOMETRY' if risk<=0 else 'STOP_ABOVE_12_TICKS' if risk>12*grid else
                            'STOP_BELOW_3_TICKS' if risk<3*grid else 'ENTRY_MORE_THAN_4_TICKS_FROM_CONSTRUCTION' if distance>4*grid else None)
                        if reason:s.update(status='NONFILL',reason=reason)
                        else:
                            take=((entry+side*(3*risk+8*grid))/grid).to_integral_value(rounding=ROUND_CEILING if side==1 else ROUND_FLOOR)*grid
                            s.update(status='MODEL_FILLED',reason='',order_admitted=True,model_filled=True,risk=risk,take=take)
                            active=dict(signal_id=s['signal_id'],instrument=symbol,direction=side,signal_at=at,
                                entry_at=at,entry_price=entry,entry_tick=grid,stop=s['stop'],take=take,risk=risk,
                                model_filled=True,cost_entry_c1=grid,planned_C1=2*grid,target_mode='FULL_NET_C1_R',
                                target_net_R=D(3),rounded_take_distance=side*(take-entry),
                                planned_net_to_net_R=(side*(take-entry)-2*grid)/(risk+2*grid),
                                deadline=min(at+timedelta(minutes=120),s['window_end']-FIVE),
                                prior_exclusion_requires_flat_assumption=prior,initial_flat_assumed=True,initial_flat_proven=False)
                        # Engine regards a known Open as an admitted order, including NONFILL.
                        s['order_admitted']=True
                ss.append(s)
            at+=FIVE
        require(active is None,'UNRESOLVED_DAY')
        prior|=blocked;day+=timedelta(days=1)
    return ss,tt,skips,xx


def read_csv(path):
    with path.open(newline='') as stream:return list(csv.DictReader(stream))


def encode(v):
    if isinstance(v,(D,datetime,date)):return str(v)
    raise TypeError(type(v))


def compare_value(actual,expected,label):
    if isinstance(expected,(dict,list)):
        require(json.loads(actual)==json.loads(json.dumps(expected,default=encode,sort_keys=True)),label)
    elif isinstance(expected,D):
        require(actual!='' and D(actual)==expected,label)
    else:
        require(actual==('' if expected is None else str(expected)),label)


def compare_ledger(actual,expected,label,ignore=()):
    require(len(actual)==len(expected),label+'_COUNT')
    require(len({r['signal_id'] for r in actual})==len(actual),label+'_DUPLICATE')
    by_id={r['signal_id']:r for r in actual};checked=0
    require(set(by_id)=={r['signal_id'] for r in expected},label+'_ID_SET')
    for r in expected:
        for k,v in r.items():
            if k in ignore:continue
            compare_value(by_id[r['signal_id']].get(k,''),v,label+' '+r['signal_id']+' '+k);checked+=1
    return checked


def economics(tt,pooled=False):
    values=[t['net_R_c1'] for t in tt];prices=[t['net_c1'] for t in tt]
    def pf(vs):
        losses=-sum((v for v in vs if v<0),ZERO)
        return sum((v for v in vs if v>0),ZERO)/losses if losses else None
    curve=peak=dd=ZERO
    for t in sorted(tt,key=lambda t:(t['resolved_at'],t['signal_id'])):
        curve+=t['net_R_c1'];peak=max(peak,curve);dd=max(dd,peak-curve)
    return dict(closed=len(tt),Net_R=sum(values,ZERO),Net_price=None if pooled else sum(prices,ZERO),
        Gross_R=sum((t['gross_R'] for t in tt),ZERO),Cost_R=sum((t['cost_R'] for t in tt),ZERO),
        PF_C1_R=pf(values),PF_C1_price=None if pooled else pf(prices),
        Expectancy_R=sum(values,ZERO)/len(tt) if tt else None,
        Win_Rate=D(sum(v>0 for v in values))/len(tt) if tt else None,
        Max_DD_R=dd if tt else None,cost_C1=None if pooled else sum((t['cost_c1'] for t in tt),ZERO),
        PF_no_losses=bool(tt) and not any(v<0 for v in prices),
        exit_reasons=dict(sorted(Counter(t['exit_reason'] for t in tt).items())))


def distribution(tt):
    winners=[t for t in tt if t['net_R_c1']>0];losers=[t for t in tt if t['net_R_c1']<0]
    def mean(rows,key):return sum((t[key] for t in rows),ZERO)/len(rows) if rows else None
    monthly={}
    for t in tt:
        m=str(t['signal_at'])[:7];monthly[m]=monthly.get(m,ZERO)+t['net_R_c1']
    gain=sum((t['net_R_c1'] for t in winners),ZERO);monthgain=sum((v for v in monthly.values() if v>0),ZERO)
    return dict(unique_trade_days=len({t['signal_at'].date() for t in tt}),active_months=len(monthly),
        average_winner_R=mean(winners,'net_R_c1'),average_loser_R=mean(losers,'net_R_c1'),
        average_winner_price=mean(winners,'net_c1'),average_loser_price=mean(losers,'net_c1'),
        positive_months=sum(v>0 for v in monthly.values()),negative_months=sum(v<0 for v in monthly.values()),
        zero_closed_economy_months=12-sum(v!=0 for v in monthly.values()),
        largest_winner_share_R=max((t['net_R_c1'] for t in winners),default=ZERO)/gain if gain else None,
        largest_positive_month_share_R=max(monthly.values(),default=ZERO)/monthgain if monthgain else None,
        top_three_winners_share_R=sum(sorted((t['net_R_c1'] for t in winners),reverse=True)[:3],ZERO)/gain if gain else None,
        monthly_closed_Net_R=dict(sorted(monthly.items())))


def geometry_stats(values):
    return dict(count=len(values),minimum=min(values) if values else None,maximum=max(values) if values else None,
        mean=sum(values,ZERO)/len(values) if values else None,histogram=dict(sorted(Counter(str(v) for v in values).items())))


def compare_json(actual,expected,label):
    for k,v in expected.items():
        require(k in actual,label+' MISSING '+k)
        require(actual[k]==json.loads(json.dumps(v,default=encode,sort_keys=True)),label+' '+k)


def counts(ss,tt,xx,ee):
    return dict(first_approaches=sum(e['event']=='FIRST' for e in ee),second_approaches=sum(e['event']=='SECOND' for e in ee),
        third_approaches=sum(e['event']=='THIRD' for e in ee),signals=sum(s['base_reason']=='SIGNAL' for s in ss),
        signals_LONG=sum(s['base_reason']=='SIGNAL' and s['direction']==1 for s in ss),signals_SHORT=sum(s['base_reason']=='SIGNAL' and s['direction']==-1 for s in ss),
        detected_candidates=len(ss),refusals=sum(s['status'] in ('REJECTED','NONFILL') for s in ss),
        skips=sum(s['status']=='DATA_GAP_SKIP' for s in ss),accepted_entries=sum(s['model_filled'] for s in ss),closed=len(tt),excluded=len(xx))


def audit(output,data_root,cfg=None,raw=None):
    output=Path(output)
    cfg=cfg or json.loads((output/'config.json').read_text())
    raw=raw or read_source(Path(data_root),cfg)
    actual={n:read_csv(output/(n+'.csv')) for n in ('signals','trades','data_gap_skips','data_quality_exclusions','construction_events','coverage_report','monthly_report','direction_report')}
    research=json.loads((output/'research_metrics.json').read_text());metrics=json.loads((output/'metrics.json').read_text())
    all_ss=[];all_tt=[];all_xx=[];all_ee=[];checked=0
    for symbol in cfg['instruments']:
        candidates,events=constructions(symbol,raw[symbol],cfg)
        ss,tt,sk,xx=replay(symbol,raw[symbol],candidates,cfg)
        for name,expected in (('signals',ss),('trades',tt),('data_gap_skips',sk),('data_quality_exclusions',xx)):
            ledger=[r for r in actual[name] if r['instrument']==symbol]
            checked+=compare_ledger(ledger,expected,symbol+' '+name,ignore=('window_end',))
        # Event ordering is operational; compare full record multiset independently.
        observed=[e for e in actual['construction_events'] if e['instrument']==symbol]
        columns=sorted({k for e in events for k in e})
        def normal(e,production):
            values={}
            for k in columns:
                v=e.get(k,'')
                if not production:
                    if isinstance(v,(list,dict)):v=json.dumps(v,default=encode,sort_keys=True)
                    elif v is None:v=''
                    else:v=str(v)
                values[k]=v
            return json.dumps(values,sort_keys=True)
        require(Counter(normal(e,True) for e in observed)==Counter(normal(e,False) for e in events),symbol+' EVENT_RECEIPTS')
        checked+=len(events)*len(columns)
        m=research['instruments'][symbol]
        compare_json(m['counts'],counts(ss,tt,xx,events),symbol+' COUNTS')
        compare_json(m['economics'],economics(tt),symbol+' ECON')
        compare_json(m['distribution'],distribution(tt),symbol+' DISTRIBUTION')
        compare_json(m['refusal_reasons'],dict(sorted(Counter(s['reason'] for s in ss if s['reason']).items())),symbol+' REFUSALS')
        compare_json(m['reset_reasons'],dict(sorted(Counter(e['reason'] for e in events if e['event']=='RESET').items())),symbol+' RESETS')
        compare_json(m['geometry'],dict(retreat_depth_ticks=geometry_stats([v for s in ss for v in s['retreat_depth_ticks']]),
            approach_separation_bars=geometry_stats([v for s in ss for v in s['approach_separation_bars']]),
            observed_touch_width_ticks=geometry_stats([s['observed_touch_width_ticks'] for s in ss]),allowed_zone_width_ticks=4,
            stop_ticks=geometry_stats([t['risk']/t['entry_tick'] for t in tt+xx])),symbol+' GEOMETRY')
        for reason in ('STOP','TAKE','TIME','SESSION_FLAT'):
            rows=[t for t in tt if t['exit_reason']==reason]
            compare_json(m['exit_attribution'][reason],dict(count=len(rows),Gross_R=sum((t['gross_R'] for t in rows),ZERO),
                Cost_R=sum((t['cost_R'] for t in rows),ZERO),Net_R=sum((t['net_R_c1'] for t in rows),ZERO)),symbol+' EXIT '+reason)
            losses=[t for t in rows if t['net_R_c1']<0]
            compare_json(m['loss_attribution'][reason],dict(count=len(losses),Net_R=sum((t['net_R_c1'] for t in losses),ZERO)),symbol+' LOSSES '+reason)
        compare_json(metrics['instruments'][symbol]['conditional_closed_only_C1'],{k:v for k,v in economics(tt).items() if k not in ('Gross_R','Cost_R')},symbol+' V2_ECON')
        fills={s['signal_id'] for s in ss if s['model_filled']}
        require(fills=={t['signal_id'] for t in tt+xx} and len(fills)==len(tt)+len(xx),symbol+' FILL_IDENTITY')
        require(m['exclusion_fraction']==(str(D(len(xx))/len(fills)) if fills else None),symbol+' EXCLUSION_FRACTION')
        require(all(t['status']=='CLOSED' for t in actual['trades']),'ONLY_CLOSED')
        for t in actual['data_quality_exclusions']:
            require(all(not t.get(k) for k in ('exit_price','exit_at','resolved_at','gross','gross_R','net_c1','net_R_c1','cost_c1','cost_R')), 'EXCLUDED_NO_PNL')
        cc=[c for c in actual['coverage_report'] if c['instrument']==symbol]
        by_date={c['date']:c for c in cc};day=date(2023,1,1);first=min(raw[symbol]).date();prior=False
        while day.year==2023:
            ws=windows(day,cfg);slots=[]
            for a,z in ws:
                while a<z:slots.append(a);a+=FIVE
            if slots:
                require(str(day) in by_date,symbol+' COVERAGE_DATE')
                missing=sum(t not in raw[symbol] for t in slots)
                invalid=sum(t in raw[symbol] and not good(raw[symbol][t],tick(symbol,t,cfg)) for t in slots)
                ds=[s for s in ss if s['signal_at'].date()==day];dt=[t for t in tt if t['entry_at'].date()==day];dx=[t for t in xx if t['entry_at'].date()==day]
                expected=dict(expected_bars=len(slots),valid_bars=len(slots)-missing-invalid,missing_bars=missing,invalid_bars=invalid,
                    status='PRE_INCEPTION' if day<first else 'INCOMPLETE' if missing or invalid else 'COMPLETE',
                    accepted_entries=sum(s['model_filled'] for s in ds),closed=len(dt),data_gap_skips=sum(s['status']=='DATA_GAP_SKIP' for s in ds),
                    data_quality_excluded=len(dx),initial_flat_assumed=True,initial_flat_proven=False,
                    prior_exclusion_requires_flat_assumption=prior if day>=first else False,remainder_of_day_blocked=bool(dx))
                for k,v in expected.items():compare_value(by_date[str(day)][k],v,symbol+' COVERAGE '+str(day)+' '+k);checked+=1
                prior|=bool(dx)
            day+=timedelta(days=1)
        require(len(by_date)==sum(bool(windows(date(2023,1,1)+timedelta(days=i),cfg)) for i in range(365)),symbol+' COVERAGE_DAY_SET')
        all_ss+=ss;all_tt+=tt;all_xx+=xx;all_ee+=events
    compare_json(research['totals'],counts(all_ss,all_tt,all_xx,all_ee),'TOTAL_COUNTS')
    compare_json(research['pooled_normalized_R'],economics(all_tt,pooled=True),'POOLED_R')
    require(research['pooled_price_PF'] is None and research['continuous_equity'] is None and metrics['annual_economics'] is None,'NO_PORTFOLIO_CLAIM')
    require(len(actual['monthly_report'])==12*(len(cfg['instruments'])+1),'TWELVE_MONTHS_ALL_SYMBOLS')
    for r in actual['monthly_report']:
        symbol,label=r['instrument'],r['month'];match=lambda t:symbol=='ALL_R_DIAGNOSTIC' or t['instrument']==symbol
        ss=[s for s in all_ss if match(s) and str(s['signal_at'])[:7]==label];tt=[t for t in all_tt if match(t) and str(t['signal_at'])[:7]==label]
        xx=[t for t in all_xx if match(t) and str(t['signal_at'])[:7]==label];ee=[e for e in all_ee if match(e) and str(e['observed_at'])[:7]==label]
        cc=[c for c in actual['coverage_report'] if match(c) and c['date'][:7]==label]
        observed=any(int(c['valid_bars'])>0 for c in cc)
        econ=economics(tt,pooled=symbol=='ALL_R_DIAGNOSTIC')
        econ.pop('closed')
        if not observed:econ={k:None for k in econ}
        expected=dict(**counts(ss,tt,xx,ee),**econ,coverage_status='NO_COVERAGE' if not observed else 'PARTIAL_DATA' if xx or any(c['status']!='COMPLETE' for c in cc) else 'COMPLETE')
        for k,v in expected.items():compare_value(r.get(k,''),v,'MONTH '+symbol+' '+label+' '+k);checked+=1
    for r in actual['direction_report']:
        tt=[t for t in all_tt if t['instrument']==r['instrument'] and t['direction']==int(r['direction'])]
        for k,v in economics(tt).items():compare_value(r.get(k,''),v,'DIRECTION '+k);checked+=1
    return dict(status='PASS',checked_fields=checked,counts=research['totals'],
        algorithm='Independent batch contiguous-span reconstruction and raw chronological execution',
        independent_imports='Python standard library only',external_human_signoff=False,
        reconstructed_all_constructions=True,accepted_entries_reconciled_by_id=True,
        calendar_and_coverage_audited=True,bytes_2024_plus_read=0)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--data-root',type=Path,required=True)
    a=p.parse_args();print(json.dumps(audit(a.output,a.data_root),sort_keys=True))
