"""Independent raw-M5 batch construction/path/report oracle; standard library only.

No production strategy, Backtester, loader, calendar, execution or metrics imports.
Implementation independence by the task author, not external human signoff.
"""
import argparse
from collections import Counter
import csv
from datetime import date, datetime, timedelta
from decimal import Decimal as D, ROUND_CEILING, ROUND_FLOOR, localcontext
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
    p=cfg['parameters'];look=p['local_extreme_lookback'];tol=p['tolerance_ticks'];limit=p['maximum_construction_bars'];final=p['approaches']
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
                    k=look
                    while k<len(span):
                        start=span[k];b=raw[start];level=b['h' if side==-1 else 'l']
                        prior=[raw[t]['h' if side==-1 else 'l'] for t in span[k-look:k]]
                        local=level>max(prior) if side==-1 else level<min(prior)
                        if not local:
                            k+=1;continue
                        ident=f'C1_{symbol}_{day}_{"LONG" if side==1 else "SHORT"}_{start:%H%M}_{int(level/grid)}'
                        def receipt(kind,when,**fields):
                            events.append(dict(instrument=symbol,direction=side,construction_id=ident,
                                first_start=start,level=level,tick=grid,event=kind,observed_at=when,**fields))
                        receipt('FIRST',start+FIVE,bar_start=start,extreme=level,previous_extrema=prior,previous_starts=span[k-look:k])
                        hits=[(start,level)];retreats=[];armed=False;consumed=False
                        max_h,min_l=b['h'],b['l'];end=k+1;reset_reason=reason;when=reset_at
                        while end<len(span):
                            t=span[end];b=raw[t];x=b['h' if side==-1 else 'l']
                            if end-k>=limit or side*(x-level)<-tol*grid:
                                reset_reason=f'EXPIRED_{limit}_BARS' if end-k>=limit else 'OUTER_ZONE_BREAK'
                                when=t+FIVE;break
                            max_h,min_l=max(max_h,b['h']),min(min_l,b['l'])
                            if not consumed:
                                if armed and abs(x-level)<=tol*grid:
                                    hits.append((t,x));armed=False
                                    receipt('SECOND' if len(hits)==2 else 'THIRD',t+FIVE,bar_start=t,extreme=x)
                                    if len(hits)==final:
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
                                            approach_separation_bars=[(hits[n+1][0]-hits[n][0])//FIVE for n in range(len(hits)-1)],
                                            observed_touch_width_ticks=(max(p[1] for p in hits)-min(p[1] for p in hits))/grid,
                                            allowed_zone_width_ticks=2*tol,stop=boundary-side*p['stop_buffer_ticks']*grid,
                                            target_mode='FULL_NET_C1_R',target_net_R=p['target_net_R'],max_hold_calendar_minutes=120,
                                            base_reason='SIGNAL' if close_d>=1 else ('SECOND_CLOSE_NOT_REJECTED' if final==2 else 'THIRD_CLOSE_NOT_REJECTED'),window_end=z))
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
        blocked=False
        boundaries=[]
        for begin,end in windows(day,cfg):
            at=begin
            while at<=end: boundaries.append(at);at+=FIVE
        for at in boundaries:
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
                            take=((entry+side*(D(cfg['parameters']['target_net_R'])*(risk+2*grid)+2*grid))/grid).to_integral_value(rounding=ROUND_CEILING if side==1 else ROUND_FLOOR)*grid
                            ratio=D(cfg['parameters']['target_net_R'])
                            diagnostic=dict(planned_C1=2*grid,d_legacy=ratio*risk+2*grid,d_full=ratio*(risk+2*grid)+2*grid,rounded_take_distance=side*(take-entry),planned_net_to_net_R=(side*(take-entry)-2*grid)/(risk+2*grid),legacy_net_to_gross_R=ratio,realized_net_to_net_R=None)
                            s.update(diagnostic)
                            s.update(status='MODEL_FILLED',reason='',order_admitted=True,model_filled=True,risk=risk,take=take)
                            active=dict(signal_id=s['signal_id'],instrument=symbol,direction=side,signal_at=at,
                                entry_at=at,entry_price=entry,entry_tick=grid,stop=s['stop'],take=take,risk=risk,
                                model_filled=True,cost_entry_c1=grid,planned_C1=2*grid,target_mode='FULL_NET_C1_R',
                                target_net_R=D(cfg['parameters']['target_net_R']),rounded_take_distance=side*(take-entry),
                                planned_net_to_net_R=(side*(take-entry)-2*grid)/(risk+2*grid),
                                deadline=min(at+timedelta(minutes=120),s['window_end']-FIVE),
                                prior_exclusion_requires_flat_assumption=prior,initial_flat_assumed=True,initial_flat_proven=False)
                            active.update(diagnostic)
                        # Engine regards a known Open as an admitted order, including NONFILL.
                        s['order_admitted']=True
                ss.append(s)
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



ROOT=Path(__file__).resolve().parents[2]
STUDY=Path(__file__).resolve().parent
NA="NOT_AVAILABLE"
EPS=D(0)
MONTHS=[f"2023-{m:02d}" for m in range(1,13)]

def independent_statistics(records,precision=50):
    """Rebuild using gain/loss partitions and prefix equity, never optimizer code."""
    with localcontext() as ctx:
        ctx.prec=precision
        ts=sorted(records,key=lambda t:(t['resolved_at'],t['signal_id']))
        rs=[D(t['net_R_c1']) for t in ts];prices=[D(t['net_c1']) for t in ts]
        rw=[v for v in rs if v>0];rl=[v for v in rs if v<0]
        pw=[v for v in prices if v>0];pl=[v for v in prices if v<0]
        total=sum(rs,D(0));gain=sum(rw,D(0));loss=sum(rl,D(0))
        pgain=sum(pw,D(0));ploss=sum(pl,D(0))
        levels=[D(0)]
        for r in rs: levels.append(levels[-1]+r)
        peak=D(0);drawdown=D(0)
        for level in levels:
            peak=max(peak,level);drawdown=max(drawdown,peak-level)
        exit_totals=[]
        for month in MONTHS:
            value=sum((D(t['net_R_c1']) for t in ts if str(t['exit_at'] or t['exit_interval_start'])[:7]==month),D(0))
            exit_totals.append(D(0) if abs(value)<=EPS else value)
        positives=[v for v in exit_totals if v>0]
        average=lambda v:sum(v,D(0))/len(v) if v else NA
        return dict(CLOSED=len(ts),entry_days=len({str(t['entry_at'])[:10] for t in ts}),
            entry_months=len({str(t['entry_at'])[:7] for t in ts}),Net_R=total,
            Net_price=sum(prices,D(0)),PF_R=-gain/loss if loss else NA,
            PF_price=-pgain/ploss if ploss else NA,
            PF_unavailable_reason='NO_NEGATIVE_CLOSED_PNL' if not rl else '',
            expectancy_R=total/len(ts) if ts else NA,win_rate=D(len(rw))/len(ts) if ts else NA,
            average_winner_R=average(rw),average_loser_R=average(rl),
            average_winner_price=average(pw),average_loser_price=average(pl),
            conditional_closed_only_DD_R=drawdown if ts else NA,
            positive_exit_months=len(positives),negative_exit_months=sum(v<0 for v in exit_totals),
            zero_exit_months=sum(v==0 for v in exit_totals),ideal_12_positive_months=len(positives)==12,
            largest_winner_share_R=max(rw)/gain if gain else NA,
            largest_positive_month_share_R=max(positives)/sum(positives,D(0)) if positives else NA,
            gross_price=sum((D(t['gross']) for t in ts),D(0)),C1_price=sum((D(t['cost_c1']) for t in ts),D(0)),
            gross_R=sum((D(t['gross_R']) for t in ts),D(0)),C1_R=sum((D(t['cost_R']) for t in ts),D(0)))


def independent_checks(m):
    valid=lambda v:v!=NA
    return dict(pass_sample=m['CLOSED']>=100 and m['entry_days']>=40 and m['entry_months']>=6,
        pass_PF_R=valid(m['PF_R']) and m['PF_R']>=2,
        pass_PF_price=valid(m['PF_price']) and m['PF_price']>=2,
        pass_positive_expectancy=valid(m['expectancy_R']) and m['expectancy_R']>0,
        pass_months=m['positive_exit_months']>=9,
        pass_conditional_DD=valid(m['conditional_closed_only_DD_R']) and m['conditional_closed_only_DD_R']<=20,
        pass_trade_concentration=valid(m['largest_winner_share_R']) and m['largest_winner_share_R']<=D('.25'),
        pass_month_concentration=valid(m['largest_positive_month_share_R']) and m['largest_positive_month_share_R']<=D('.50'))




def write_json(path,obj):
    path.write_text(json.dumps(obj,indent=2,sort_keys=True,default=encode)+'\n')


def write_csv(path,rows):
    keys=sorted({k for r in rows for k in r})
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys,lineterminator='\n');w.writeheader()
        for r in rows:w.writerow({k:json.dumps(v,default=encode,sort_keys=True) if isinstance(v,(dict,list)) else v for k,v in r.items()})


def event_check(actual,expected,label):
    columns=sorted({k for e in expected for k in e})
    def normal(row,observed):
        result={}
        for k in columns:
            v=row.get(k,'')
            if not observed:
                v=json.dumps(v,default=encode,sort_keys=True) if isinstance(v,(dict,list)) else '' if v is None else str(v)
            result[k]=v
        return json.dumps(result,sort_keys=True)
    require(Counter(normal(e,True) for e in actual)==Counter(normal(e,False) for e in expected),label)
    return len(expected)*len(columns)


def independent_coverage(symbol,raw,ss,tt,sk,xx,cfg):
    result=[];day=date(2023,1,1);first=min(raw).date();prior=False
    while day.year==2023:
        slots=[]
        for a,z in windows(day,cfg):
            while a<z:slots.append(a);a+=FIVE
        if slots:
            missing=sum(t not in raw for t in slots)
            invalid=sum(t in raw and not good(raw[t],tick(symbol,t,cfg)) for t in slots)
            ds=[s for s in ss if s['signal_at'].date()==day];dt=[t for t in tt if t['entry_at'].date()==day];dx=[t for t in xx if t['entry_at'].date()==day]
            result.append(dict(instrument=symbol,date=str(day),expected_bars=len(slots),valid_bars=len(slots)-missing-invalid,
                missing_bars=missing,invalid_bars=invalid,status='PRE_INCEPTION' if day<first else 'INCOMPLETE' if missing or invalid else 'COMPLETE',
                accepted_entries=sum(s['model_filled'] for s in ds),closed=len(dt),data_gap_skips=sum(s['status']=='DATA_GAP_SKIP' for s in ds),
                data_quality_excluded=len(dx),initial_flat_assumed=True,initial_flat_proven=False,
                prior_exclusion_requires_flat_assumption=prior if day>=first else False,remainder_of_day_blocked=bool(dx)))
            prior|=bool(dx)
        day+=timedelta(days=1)
    return result


def diagnostics_expected(ss,tt,xx,ee,spec):
    rows=[]
    for kind in ('FIRST','RETREAT','SECOND','THIRD','RESET'):
        part=[e for e in ee if e['event']==kind]
        rows.append(dict(configuration_id=spec['configuration_id'],kind='EVENT',field=kind,count=len(part),reset_reasons=dict(sorted(Counter(e.get('reason') for e in part if e.get('reason')).items()))))
    values={
        'approach_count':[len(s['approach_starts']) for s in ss],
        'local_extreme_lookback':[len(e['previous_starts']) for e in ee if e['event']=='FIRST'],
        'zone_distance_ticks':[abs((v-s['level'])/s['signal_tick']) for s in ss for v in s['approach_extrema']],
        'retreat_depth_ticks':[v for s in ss for v in s['retreat_depth_ticks']],
        'approach_separation_bars':[v for s in ss for v in s['approach_separation_bars']],
        'construction_bars':[s['construction_bars'] for s in ss],
        'risk_ticks':[t['risk']/t['entry_tick'] for t in tt+xx]}
    for k,vs in values.items():
        for v,n in sorted(Counter(map(str,vs)).items()):rows.append(dict(configuration_id=spec['configuration_id'],kind='GEOMETRY',field=k,value=v,count=n))
    return rows


def source_metadata(data_root,cfg):
    import subprocess
    command=lambda *args:subprocess.check_output(['git','-C',str(data_root),*args],text=True).strip()
    require(command('rev-parse','HEAD')==cfg['source_ref'],'PINNED_SOURCE_HEAD')
    for symbol,spec in cfg['inputs'].items():
        require(command('rev-parse',cfg['source_ref']+':'+spec['path'])==spec['blob'],'PINNED_SOURCE_BLOB')
        require(command('ls-files','--stage','--',spec['path']).split()[1]==spec['blob'],'SOURCE_INDEX_BLOB')
    require(not command('status','--porcelain=v1','--untracked-files=all'),'READ_ONLY_SOURCE_CLEAN')


def audit(data_root,output,policy=None,raw=None,synthetic=False):
    import ast
    from itertools import product
    policy=policy or json.loads((STUDY/'OPTIMIZATION_C_POLICY.json').read_text())
    require(policy['instruments']==['USDRUBF'],'USDRUBF_ONLY')
    for node in ast.walk(ast.parse(Path(__file__).read_text())):
        if isinstance(node,(ast.Import,ast.ImportFrom)):
            names=[x.name for x in node.names] if isinstance(node,ast.Import) else [node.module or '']
            require(all(not m.startswith('IntradayLab') and m not in ('aggregation','runner','contract') for m in names),'STANDARD_LIBRARY_ONLY_AUDITOR')
    protected={}
    if not synthetic:
        commitments=json.loads((STUDY/'source_commitments.json').read_text())
        for p,sha in commitments['dependencies_sha256'].items():require(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==sha,'FREEZE '+p)
        protected=json.loads((STUDY/'protected_file_sha256.json').read_text())
        for p,sha in protected.items():require(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==sha,'PROTECTED '+p)
        source_metadata(data_root,policy)
    raw=raw if raw is not None else read_source(data_root,policy)
    specs=[]
    # Independent exact published lists, not optimizer grid/selector functions.
    for a,l,t,m,sb,tp in product((2,3),(3,5),(1,2),(24,36),(1,2),range(2,11)):
        specs.append(dict(policy['parameters'],approaches=a,local_extreme_lookback=l,tolerance_ticks=t,maximum_construction_bars=m,stop_buffer_ticks=sb,target_net_R=str(tp),configuration_id=f'C_OPT2023_APP{a}_LOOKBACK{l}_TOL{t}_MAXBARS{m}_SB{sb}_TP{tp}'))
    require(read_csv(STUDY/'GRID.csv')==[{k:str(v) for k,v in r.items()} for r in specs],'INDEPENDENT_288_GRID')
    require(read_csv(STUDY/'EVALUATION_MATRIX.csv')==[dict(configuration_id=r['configuration_id'],instrument='USDRUBF') for r in specs],'INDEPENDENT_288_MATRIX')
    rows=read_csv(output/'all_candidates.csv');months=read_csv(output/'monthly_results.csv');directions=read_csv(output/'direction_results.csv');funnels=read_csv(output/'execution_funnel.csv')
    require(len(rows)==288 and len(months)==3456 and len(directions)==576 and len(funnels)==288,'COMPLETE_MATRIX_ROWS')
    actual={r['configuration_id']:r for r in rows}
    require(set(actual)=={r['configuration_id'] for r in specs} and len(actual)==len(rows),'CANDIDATE_ID_SET')
    def indexed(records,field,values):
        result={(r['configuration_id'],r[field]):r for r in records}
        require(len(result)==len(records) and set(result)=={(p['configuration_id'],v) for p in specs for v in values},'EXACT_ROW_SET '+field)
        return result
    mm=indexed(months,'month',MONTHS);dd=indexed(directions,'direction',('LONG','SHORT'))
    ff={r['configuration_id']:r for r in funnels};expected={};counts=Counter();comparison=[];all_diag=[];index=[]
    for spec in specs:
        ident=spec['configuration_id'];cfg=dict(policy,parameters={k:v for k,v in spec.items() if k!='configuration_id'})
        ev,ee=constructions('USDRUBF',raw['USDRUBF'],cfg)
        ss,tt,sk,xx=replay('USDRUBF',raw['USDRUBF'],ev,cfg)
        folder=output/'evaluations'/ident/'USDRUBF'
        for name,wanted in [('signals',ss),('trades',tt),('data_gap_skips',sk),('data_quality_exclusions',xx),('rejected_nonfill',[s for s in ss if s['status'] in ('REJECTED','NONFILL')])]:
            ledger=read_csv(folder/(name+'.csv'))
            counts[name+'_fields']+=compare_ledger(ledger,wanted,ident+' '+name,ignore=('window_end',))
            require(all(r['status']!='UNKNOWN' for r in ledger),'V2_NO_UNKNOWN')
            if name=='trades':require(all(r['status']=='CLOSED' for r in ledger),'ONLY_CLOSED')
            if name=='data_quality_exclusions':require(all(not r.get(k) for r in ledger for k in ('exit_price','exit_at','resolved_at','gross','gross_R','cost_c1','cost_R','net_c1','net_R_c1','realized_net_to_net_R')),'NO_EXCLUDED_PNL')
        counts['construction_fields']+=event_check(read_csv(folder/'construction_events.csv'),ee,'ALL_CONSTRUCTION_STATES '+ident)
        require(len({s['construction_id'] for s in ss})==len(ss),'ONE_ATTEMPT_PER_CONSTRUCTION')
        fills={s['signal_id'] for s in ss if s['model_filled']}
        require(fills=={t['signal_id'] for t in tt+xx} and len(fills)==len(tt)+len(xx),'ACCEPTED_ID_RECONCILIATION')
        counts['accepted_ID_checks']+=len(fills)
        cov=independent_coverage('USDRUBF',raw['USDRUBF'],ss,tt,sk,xx,cfg)
        ac=read_csv(folder/'coverage_report.csv');require(len(ac)==len(cov),'COVERAGE_ROW_COUNT')
        for r,e in zip(ac,cov):
            for k,v in e.items():compare_value(r.get(k,''),v,'COVERAGE '+k);counts['coverage_fields']+=1
        m=independent_statistics(tt);m.update(independent_checks(m));expected[ident]=m;row=actual[ident]
        for k,v in m.items():compare_value(row[k],v,'METRIC '+ident+' '+k);counts['metric_fields']+=1
        for k,v in spec.items():compare_value(row[k],v,'CONFIG '+k)
        cfg_saved=json.loads((folder/'configuration.json').read_text())
        require(cfg_saved['parameters']==cfg['parameters'] and cfg_saved['execution']==policy['execution'],'CONFIG_EXECUTION_BYTES')
        require(cfg_saved['source_sha']==policy['source_ref'] and cfg_saved['source_blob']==policy['inputs']['USDRUBF']['blob'],'CONFIG_SOURCE_BYTES')
        expected_counts=dict(accepted_entries=len(fills),DATA_GAP_SKIP=len(sk),DATA_QUALITY_EXCLUDED=len(xx),conditional_flat_CLOSED=sum(t['prior_exclusion_requires_flat_assumption'] for t in tt),complete_coverage_days=sum(c['status']=='COMPLETE' for c in cov),incomplete_coverage_days=sum(c['status']=='INCOMPLETE' for c in cov))
        for k,v in expected_counts.items():compare_value(row[k],v,'COUNT '+k);counts['metric_fields']+=1
        with localcontext() as ctx:
            ctx.prec=50
            compare_value(row['exclusion_fraction'],D(len(xx))/len(fills) if fills else NA,'EXCLUSION_SHARE')
            compare_value(row['skip_fraction_of_fills_and_skips'],D(len(sk))/(len(fills)+len(sk)) if fills or sk else NA,'SKIP_SHARE')
        reasons='|'.join(name for name,value,limit in [('CLOSED_BELOW_100',m['CLOSED'],100),('ENTRY_DAYS_BELOW_40',m['entry_days'],40),('ENTRY_MONTHS_BELOW_6',m['entry_months'],6)] if value<limit)
        require(row['sample_failure_reasons']==reasons,'SAMPLE_REASONS')
        for month in MONTHS:
            cohort=[t for t in tt if str(t['exit_at'] or t['exit_interval_start'])[:7]==month]
            mc=[c for c in cov if c['date'][:7]==month]
            expected_month=dict(independent_statistics(cohort),complete_days=sum(c['status']=='COMPLETE' for c in mc),incomplete_days=sum(c['status']=='INCOMPLETE' for c in mc),valid_bars=sum(c['valid_bars'] for c in mc),missing_bars=sum(c['missing_bars'] for c in mc),invalid_bars=sum(c['invalid_bars'] for c in mc),accepted_entries=sum(c['accepted_entries'] for c in mc),DATA_GAP_SKIP=sum(c['data_gap_skips'] for c in mc),DATA_QUALITY_EXCLUDED=sum(c['data_quality_excluded'] for c in mc))
            for k,v in expected_month.items():compare_value(mm[(ident,month)][k],v,'MONTH '+k);counts['monthly_fields']+=1
        for side in (1,-1):
            dr=dd[(ident,'LONG' if side==1 else 'SHORT')]
            ds=dict(independent_statistics([t for t in tt if t['direction']==side]),DATA_GAP_SKIP=sum(s['direction']==side for s in sk),DATA_QUALITY_EXCLUDED=sum(t['direction']==side for t in xx))
            for k,v in ds.items():compare_value(dr[k],v,'DIRECTION '+k);counts['direction_fields']+=1
        funnel=dict(raw_directional_events=len(ss),signals=sum(s['base_reason']=='SIGNAL' for s in ss),ambiguous_directional_events=sum(s['base_reason']=='AMBIGUOUS_BOTH_SIDES' for s in ss),final_close_not_rejected_events=sum(s['base_reason'] in ('SECOND_CLOSE_NOT_REJECTED','THIRD_CLOSE_NOT_REJECTED') for s in ss),admissions=sum(s['order_admitted'] for s in ss),rejects=sum(s['base_reason']=='SIGNAL' and s['status']=='REJECTED' for s in ss),nonfills=sum(s['status']=='NONFILL' for s in ss),fills=len(fills),SKIP=len(sk),EXCLUDED=len(xx),CLOSED=len(tt),reason_counts=dict(sorted(Counter(s['reason'] for s in ss if s['reason']).items())))
        for k,v in funnel.items():compare_value(ff[ident][k],v,'FUNNEL '+k);counts['funnel_fields']+=1
        ds=diagnostics_expected(ss,tt,xx,ee,spec);all_diag.extend(ds)
        ad=read_csv(folder/'construction_diagnostics.csv');require(len(ad)==len(ds),'DIAGNOSTIC_COUNT')
        for r,e in zip(ad,ds):
            for k,v in e.items():compare_value(r[k],v,'DIAGNOSTIC '+k);counts['diagnostic_fields']+=1
        index.append(dict(configuration_id=ident,instrument='USDRUBF',detail_directory=f'evaluations/{ident}/USDRUBF',signals=len(ss),construction_events=len(ee),CLOSED=len(tt),SKIP=len(sk),EXCLUDED=len(xx)))
        if ident==policy['historical_control_id']:
            baseline=ROOT/'IntradayLab/results/return_retest_rejection_m5_2023_c_v1'
            for name in ('signals','trades','data_gap_skips','data_quality_exclusions','construction_events','days','coverage_report'):
                current=read_csv(folder/(name+'.csv'))
                old=[r for r in read_csv(baseline/(name+'.csv')) if r['instrument']=='USDRUBF'] if not synthetic else current
                require(old==current,'EXACT_C_V1_BASELINE '+name)
                fields=sum(len(r) for r in old);counts['baseline_fields']+=fields
                comparison.append(dict(configuration_id=ident,artifact=name,baseline_rows=len(old),control_rows=len(current),checked_fields=fields,status='PASS',comparison='ALL_COLUMNS_AND_ROW_ORDER_EXACT'))
            if not synthetic:require(len(tt)==102 and len(sk)==2 and len(xx)==2,'C_V1_102_2_2')
        print('independent audit '+ident,flush=True)
    edges=read_csv(output/'parameter_neighborhood.csv');edge_map={(r['configuration_id'],r['neighbor_id']):r for r in edges};wanted_edges=set();passed=[]
    lists=dict(approaches=[2,3],local_extreme_lookback=[3,5],tolerance_ticks=[1,2],maximum_construction_bars=[24,36],stop_buffer_ticks=[1,2],target_net_R=list(range(2,11)))
    for a in specs:
        ident=a['configuration_id'];m=expected[ident];n=0
        for b in specs:
            diffs=[k for k in lists if a[k]!=b[k]]
            if len(diffs)!=1:continue
            key=diffs[0]
            if abs(lists[key].index(int(a[key]))-lists[key].index(int(b[key])))!=1:continue
            other=expected[b['configuration_id']];good_neighbor=other['CLOSED']>=100 and other['PF_R']!=NA and other['PF_R']>=D('1.5') and other['expectancy_R']!=NA and other['expectancy_R']>0
            pair=(ident,b['configuration_id']);wanted_edges.add(pair);r=edge_map[pair]
            for k,v in dict(changed_parameter=key,neighbor_CLOSED=other['CLOSED'],neighbor_PF_R=other['PF_R'],neighbor_expectancy_R=other['expectancy_R'],neighbor_qualifies=good_neighbor).items():compare_value(r[k],v,'NEIGHBOR '+k);counts['neighbor_fields']+=1
            n+=good_neighbor
        m['pass_neighbors']=n>=2
        compare_value(actual[ident]['positive_neighbor_count'],n,'NEIGHBOR_COUNT');compare_value(actual[ident]['pass_neighbors'],n>=2,'NEIGHBOR_PASS')
        failed=[k.removeprefix('pass_') for k,v in m.items() if k.startswith('pass_') and not v]
        require(actual[ident]['failure_reasons']=='|'.join(failed),'ALL_FAILED_GATES')
        status='INSUFFICIENT_SAMPLE' if not m['pass_sample'] else policy['candidate_status'] if not failed else 'DOES_NOT_QUALIFY'
        require(actual[ident]['status']==status,'STATUS')
        if not failed:passed.append((ident,m))
        else:require(actual[ident]['rank']==NA,'ONLY_FULL_PASSES_RANKED')
    require(len(edge_map)==len(edges) and set(edge_map)==wanted_edges,'FULL_NEIGHBOR_MATRIX')
    ranked=sorted(passed,key=lambda x:(-x[1]['positive_exit_months'],-min(x[1]['PF_R'],x[1]['PF_price']),x[1]['conditional_closed_only_DD_R'],-x[1]['CLOSED'],x[0]))
    selection=json.loads((output/'selection_report.json').read_text());s=selection['instruments']['USDRUBF']
    require(s['ranked_ids']==[i for i,m in ranked] and selection['criteria']==policy['selection'],'FROZEN_SELECTION_RANKING')
    for rank,(ident,m) in enumerate(ranked,1):compare_value(actual[ident]['rank'],rank,'RANK')
    values=list(expected.values());checks=dict(evaluated=288,sample_pass=sum(m['pass_sample'] for m in values),both_PF_pass=sum(m['pass_PF_R'] and m['pass_PF_price'] for m in values),sample_and_both_PF_pass=sum(m['pass_sample'] and m['pass_PF_R'] and m['pass_PF_price'] for m in values),months_pass=sum(m['pass_months'] for m in values),neighbors_pass=sum(m['pass_neighbors'] for m in values),base_study_criteria_pass=sum(all(v for k,v in m.items() if k.startswith('pass_') and k!='pass_neighbors') for m in values),full_criteria_pass=len(ranked),result=policy['candidate_status'] if ranked else policy['no_candidate_status'])
    for k,v in checks.items():require(s[k]==v,'SELECTION_COUNTS '+k);counts['selection_checks']+=1
    require(selection['evaluations']==288 and selection['overall_result']==checks['result'],'SELECTION_BUDGET_AND_RESULT')
    for name,wanted in [('detailed_artifact_index',index),('construction_diagnostics',all_diag)]:
        observed=read_csv(output/(name+'.csv'));require(len(observed)==len(wanted),'TOP_LEVEL_COUNT '+name)
        for r,e in zip(observed,wanted):
            for k,v in e.items():compare_value(r[k],v,'TOP_LEVEL '+name+' '+k);counts['index_diagnostics_fields']+=1
    write_csv(output/'baseline_comparison.csv',comparison)
    result=dict(status='PASS',evaluations=288,checked_fields=dict(counts),independent_imports='STANDARD_LIBRARY_ONLY',independent_signal_method='Batch contiguous spans and greedy fixed-level lifetime walks per side',independent_execution_method='Chronological raw M5 boundary replay and Stop-first intervals',independent_economics_selection=True,protected_files_byte_verified=len(protected),exact_comparisons=True,bytes_2024_plus_read=0,external_human_signoff=False,baseline_control='PASS',selection=checks['result'],source_read_receipts={s:dict(bytes_read=p['prefix_bytes'],rows_2023=p['rows_2023'],prefix_sha256=p['prefix_sha256'],source_blob=p['blob'],bytes_2024_plus_read=0) for s,p in policy['inputs'].items()} if not synthetic else {'synthetic':True})
    write_json(output/'audit.json',result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(json.dumps(audit(a.data_root,a.output),sort_keys=True))
