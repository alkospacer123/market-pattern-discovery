"""Independent raw M5 batch/path/economic oracle for the bounded 2023 study.

Uses the standard library only. Does not import the production strategy, engine,
loader, calendar, metrics, study runner or study aggregation. A separately tasked
agent implements the audit; this is not external human reviewer signoff.
"""
import argparse
import ast
from collections import Counter
import csv
from datetime import date, datetime, timedelta
from decimal import Decimal as D, ROUND_CEILING, ROUND_FLOOR, localcontext
import hashlib
import io
from itertools import product
import json
from pathlib import Path
import subprocess
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
STUDY = Path(__file__).resolve().parent
FIVE = timedelta(minutes=5)
ZONE = ZoneInfo('Europe/Moscow')
NA = 'NOT_AVAILABLE'
MONTHS = [f'2023-{m:02d}' for m in range(1, 13)]
HOLIDAYS = {(1,1),(1,2),(1,7),(2,23),(3,8),(5,1),(5,9),(6,12),(11,4)}
AXES = dict(min_close_reentry_ticks=[1,2], stop_beyond_extreme_ticks=[1,2],
            max_hold_calendar_minutes=[120,60], planned_net_to_net_R=list(range(2,11)))


def require(ok, label):
    if not ok:
        raise AssertionError(label)


def stamp(day, clock):
    return datetime.fromisoformat(str(day)+' '+clock).replace(tzinfo=ZONE)


def windows(day):
    if day.weekday() >= 5 or (day.month,day.day) in HOLIDAYS:
        return []
    lunch = '14:15' if date(2023,3,13) <= day < date(2023,3,21) else '14:05'
    return [(stamp(day,'10:00'),stamp(day,'14:00')),
            (stamp(day,lunch),stamp(day,'18:50'))]


def tick(symbol, at):
    if symbol == 'CNYRUBF':
        return D('.01') if at < stamp(date(2023,9,27),'19:00') else D('.001')
    return D({'USDRUBF':'.01','GLDRUBF':'.1','IMOEXF':'.5'}[symbol])


def good_open(row, symbol, at):
    return row is not None and row[0].is_finite() and row[0] > 0 and row[0] % tick(symbol,at) == 0


def good(row, symbol, at):
    if row is None or not all(x.is_finite() for x in row):
        return False
    o,h,l,c,v = row
    return 0 < l <= min(o,c) <= max(o,c) <= h and v > 0 and all(x % tick(symbol,at) == 0 for x in row[:4])


def read_source(root, policy):
    """LF-budget independent read: never consume a byte from a later year."""
    result = {}; receipts = {}
    for symbol in policy['instruments']:
        spec = policy['inputs'][symbol]
        chunks = []; remaining = spec['rows_2023']+1
        with (root/spec['path']).open('rb',buffering=0) as stream:
            while remaining:
                block = stream.read(min(16384,remaining))
                require(bool(block),'TRUNCATED_SOURCE')
                remaining -= block.count(b'\n'); chunks.append(block)
        raw = b''.join(chunks)
        require(len(raw)==spec['prefix_bytes'] and hashlib.sha256(raw).hexdigest()==spec['prefix_sha256'],'PREFIX_HASH')
        rows = {}; previous = None
        reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')),delimiter=';')
        require(reader.fieldnames==['Ticker','Datetime','Open','High','Low','Close','Volume'],'SOURCE_HEADER')
        for row in reader:
            at = datetime.fromisoformat(row['Datetime']).replace(tzinfo=ZONE)
            require(row['Ticker']==symbol and at.year==2023,'SOURCE_2023_SCOPE')
            require(previous is None or previous < at,'SOURCE_ORDER')
            rows[at] = tuple(D(row[k]) for k in ('Open','High','Low','Close','Volume')); previous = at
        require(len(rows)==spec['rows_2023'],'SOURCE_ROW_BUDGET')
        result[symbol] = rows
        receipts[symbol] = dict(bytes_read=len(raw),rows_2023=len(rows),prefix_sha256=hashlib.sha256(raw).hexdigest(),source_blob=spec['blob'],bytes_2024_plus_read=0)
    return result, receipts


def episodes(symbol, raw, parameters):
    """Immediate six timestamps, independent side cooldown and batch range."""
    output = []; day = date(2023,1,1); first = min(raw).date() if raw else date(2024,1,1)
    p = parameters
    while day.year == 2023:
        for a,z in windows(day) if day >= first else []:
            confirmed = {}; at = a
            while at < z:
                row = raw.get(at)
                rec = dict(signal_id=f'{symbol}_{day}_{at:%H%M}',instrument=symbol,date=str(day),
                    direction=0,signal_at=None,test_start=at,raw_rejection=False,
                    confirmed_signal=False,recorded_at=at+FIVE)
                if at == a:
                    output.append(dict(rec,signal_id=rec['signal_id']+'_RESET',base_reason='RANGE_UNAVAILABLE',
                                       reset_reason='SESSION_BOUNDARY',valid_preceding_bars=0))
                if not good(row,symbol,at):
                    confirmed.clear()
                    output.append(dict(rec,base_reason='RANGE_MISSING_BAR' if row is None else 'RANGE_INVALID_BAR'))
                    at += FIVE; continue
                before = [at-i*FIVE for i in range(6,0,-1)]
                if before[0] < a or not all(good(raw.get(t),symbol,t) for t in before):
                    at += FIVE; continue
                high = max(raw[t][1] for t in before); low = min(raw[t][2] for t in before); step = tick(symbol,at)
                rec.update(range_start=before[0],range_end=at,range_bars=6,range_high=high,range_low=low,
                    test_closed_at=at+FIVE,test_high=row[1],test_low=row[2],test_close=row[3],signal_tick=step)
                long = row[2] <= low-step and row[3] >= low+p['min_close_reentry_ticks']*step
                short = row[1] >= high+step and row[3] <= high-p['min_close_reentry_ticks']*step
                reason = None
                if long and short:
                    reason = 'AMBIGUOUS_BOTH_SIDES'
                elif long or short:
                    side = 1 if long else -1; prior = confirmed.get(side)
                    rec.update(signal_id=rec['signal_id']+f'_{side}',direction=side,raw_rejection=True,
                        previous_confirmed_start=prior,level=low if long else high,opposite_level=high if long else low,
                        stop=row[2]-p['stop_beyond_extreme_ticks']*step if long else row[1]+p['stop_beyond_extreme_ticks']*step)
                    if prior is not None and at-prior < timedelta(minutes=30):
                        reason = 'DEDUP_30MIN'
                    else:
                        confirmed[side] = at
                        rec.update(signal_at=at+FIVE,confirmed_signal=True,
                            max_hold_calendar_minutes=p['max_hold_calendar_minutes'],
                            target_gross_R=p['planned_net_to_net_R'],target_net_R=p['planned_net_to_net_R'],target_mode='FULL_NET_C1_R',
                            entry_constraints=dict(directional_reference=rec['level'],minimum_reference_ticks=p['min_close_reentry_ticks'],
                                minimum_risk_ticks=4,reserve_minutes=35,
                                reason_labels={'OPEN_REFERENCE_LIMIT':'OPEN_RECLAIM_NOT_PERSISTENT','RISK_BELOW_MINIMUM_TICKS':'RISK_BELOW_FOUR_TICKS'}),
                            waiting_bar_start=at+FIVE,waiting_bar_closed_at=at+2*FIVE,planned_execution_at=at+2*FIVE,
                            window_start=a,window_end=z)
                        reason = 'SIGNAL'
                if reason:
                    output.append(dict(rec,base_reason=reason))
                at += FIVE
        day += timedelta(days=1)
    return sorted(output,key=lambda r:(r['recorded_at'],r['signal_id']))


def path(symbol, raw, trade, legacy=False):
    """Forward raw observations, Open then interval, excluding no future data."""
    q = trade; entry = q['entry_at']; side = q['direction']; at = entry
    deadline = q['effective_deadline_at']
    while at <= deadline:
        row = raw.get(at)
        missing_open = row is None
        invalid_open = not missing_open and not good_open(row,symbol,at)
        if missing_open or invalid_open:
            reason = 'MISSING_EXPOSED_BAR' if missing_open else 'INVALID_EXPOSED_OPEN'
            detected = at
        elif side*(row[0]-q['stop']) <= 0 or at == deadline:
            price = row[0]; point = True; conflict = False
            reason = ('STOP' if side*(price-q['stop']) <= 0 else
                      'TIME' if at == entry+timedelta(minutes=q['max_hold_calendar_minutes']) else
                      'TRADE_DEADLINE' if at == q['trade_deadline_at'] else 'SESSION_FLAT')
            break
        elif not good(row,symbol,at):
            reason = 'INVALID_EXPOSED_BAR'; detected = at+FIVE
        else:
            sh = row[2] <= q['stop'] if side == 1 else row[1] >= q['stop']
            th = row[1] >= q['take'] if side == 1 else row[2] <= q['take']
            if sh or th and at != entry:
                price = q['stop'] if sh else q['take']; point = False; conflict = sh and th
                reason = 'STOP' if sh else 'TAKE'; break
            at += FIVE; continue
        blank = dict(exit_price=None,exit_at=None,exit_interval_start=None,exit_interval_end=None,resolved_at=None,stop_take_conflict=False)
        if legacy:
            return dict(blank,status='UNKNOWN',exit_reason='UNKNOWN',unknown_reason=reason,unknown_detected_at=at+FIVE,
                        _blocked_at=detected)
        return dict(blank,status='DATA_QUALITY_EXCLUDED',exit_reason=None,exclusion_reason=reason,
                    gap_interval_start=at,gap_interval_end=at+FIVE,gap_detected_at=detected,
                    remainder_of_day_blocked=True,_blocked_at=detected)
    else:
        raise AssertionError('ORACLE_DEADLINE')
    gross = side*(price-q['entry_price']); expense = q['entry_tick']+tick(symbol,at)
    return dict(status='CLOSED',exit_reason=reason,exit_price=price,exit_tick=tick(symbol,at),
        exit_at=at if point else None,exit_interval_start=at,exit_interval_end=at if point else at+FIVE,
        resolved_at=at if point else at+FIVE,stop_take_conflict=conflict,gross=gross,gross_R=gross/q['risk'],
        cost_c1=expense,cost_R=expense/q['risk'],net_c1=gross-expense,net_R_c1=(gross-expense)/q['risk'],
        realized_net_to_net_R=(gross-expense)/(q['risk']+expense))


def replay(symbol, raw, events, legacy=False):
    """Per-trade paths with observation-time busy/block state; no common engine."""
    signals = []; trades = []; skips = []; exclusions = []
    day = None; busy_until = None; blocked_at = None; prior = False; today = False
    for event in events:
        if event['date'] != day:
            prior |= today; today = False; day = event['date']; busy_until = blocked_at = None
        evidence = dict(initial_flat_assumed=True,initial_flat_proven=False)
        if legacy:
            evidence['prior_unknown_requires_flat_assumption'] = prior
        else:
            evidence.update(data_gap_policy='DATA_GAP_SKIP_V2',prior_exclusion_requires_flat_assumption=prior,
                            following_day_contract='CONDITIONAL_FLAT; not a proven real close')
        s = dict(event,strategy='LEVEL_REJECTION_M5',status='REJECTED',reason=event['base_reason'],order_admitted=False,model_filled=False,**evidence)
        signals.append(s)
        if s['base_reason'] != 'SIGNAL':
            continue
        now = s['signal_at']; entry = s['planned_execution_at']; cutoff = stamp(day,'17:00')
        s.update(pending_created=False,open_admission_passed=None)
        if blocked_at and now >= blocked_at:
            s['reason'] = 'UNKNOWN_POSITION_BLOCK' if legacy else 'DATA_QUALITY_POSITION_BLOCK'; continue
        if busy_until and now < busy_until or blocked_at and now < blocked_at:
            s['reason'] = 'POSITION_BUSY'; continue
        if entry >= cutoff:
            s['reason'] = 'TRADE_DEADLINE'; continue
        if entry >= s['window_end']-FIVE:
            s['reason'] = 'SESSION_LIMIT'; continue
        if entry+timedelta(minutes=35) > min(s['window_end'],cutoff):
            s['reason'] = 'SESSION_ENTRY_CUTOFF'; continue
        s['pending_created'] = True; busy_until = entry
        if not good(raw.get(s['waiting_bar_start']),symbol,s['waiting_bar_start']):
            s['reason'] = 'NO_WAITING_BAR'; continue
        s.update(order_admitted=True,order_sent_at=entry)
        if not good_open(raw.get(entry),symbol,entry):
            reason = 'MISSING_EXECUTION_BAR' if raw.get(entry) is None else 'INVALID_EXECUTION_OPEN'
            if legacy:
                s.update(status='UNKNOWN',reason=reason)
                q = dict(signal_id=s['signal_id'],instrument=symbol,status='UNKNOWN',model_filled=False,
                         unknown_reason=reason,unknown_detected_at=entry+FIVE,exit_reason='UNKNOWN',
                         exit_price=None,exit_at=None,exit_interval_start=None,exit_interval_end=None,resolved_at=None)
                trades.append(q); blocked_at = entry; today = True
            else:
                s.update(status='DATA_GAP_SKIP',reason=reason,order_admitted=False,order_sent_at=None,
                         attempted_execution_at=entry,gap_detected_at=entry)
                skips.append(s.copy())
            continue
        op = raw[entry][0]; step = tick(symbol,entry); side = s['direction']; risk = side*(op-s['stop'])
        s.update(entry_open=op,entry_tick=step,open_admission_passed=False)
        reason = ('OPEN_RECLAIM_NOT_PERSISTENT' if side*(op-s['level']) < s['entry_constraints']['minimum_reference_ticks']*step else
                  'INVALID_RISK' if risk <= 0 else 'RISK_BELOW_FOUR_TICKS' if risk < 4*step else None)
        if reason:
            s.update(status='NONFILL',reason=reason); continue
        s['open_admission_passed'] = True
        ratio = D(str(s['target_net_R'])); expense = 2*step
        target = ((op+side*(ratio*(risk+expense)+expense))/step).to_integral_value(rounding=ROUND_CEILING if side == 1 else ROUND_FLOOR)*step
        diagnostic = dict(target_mode='FULL_NET_C1_R',target_net_R=ratio,planned_C1=expense,
            d_legacy=ratio*risk+expense,d_full=ratio*(risk+expense)+expense,
            rounded_take_distance=side*(target-op),planned_net_to_net_R=(side*(target-op)-expense)/(risk+expense),
            legacy_net_to_gross_R=ratio,realized_net_to_net_R=None)
        s.update(status='MODEL_FILLED',reason='',model_filled=True,risk=risk,take=target,**diagnostic)
        q = {k:s.get(k) for k in ('signal_id','instrument','direction','signal_at','sweep_start','reclaim_start',
             'waiting_bar_closed_at','order_sent_at','planned_execution_at','stop','window_end','max_hold_calendar_minutes')}
        q.update(strategy='LEVEL_REJECTION_M5',entry_at=entry,entry_price=op,entry_tick=step,risk=risk,take=target,
                 model_filled=True,cost_entry_c1=step,trade_deadline_at=cutoff,
                 effective_deadline_at=min(entry+timedelta(minutes=s['max_hold_calendar_minutes']),s['window_end']-FIVE,cutoff),
                 **diagnostic,**evidence)
        outcome = path(symbol,raw,q,legacy); blocked = outcome.pop('_blocked_at',None); q.update(outcome)
        if blocked:
            blocked_at = blocked; today = True
            if legacy:
                q.update(gross=None,gross_R=None,cost_c1=None,cost_R=None,net_c1=None,net_R_c1=None); trades.append(q)
            else:
                exclusions.append(q)
        else:
            trades.append(q); busy_until = q['resolved_at']
    return signals,trades,skips,exclusions


def encode(value):
    if isinstance(value,(D,date,datetime)):
        return str(value)
    raise TypeError(type(value))


def read_csv(path):
    with path.open(newline='') as stream:
        return list(csv.DictReader(stream))


def compare_value(actual,expected,label):
    if isinstance(expected,(dict,list)):
        require(json.loads(actual)==json.loads(json.dumps(expected,default=encode,sort_keys=True)),label)
    elif isinstance(expected,D):
        require(actual!='' and D(actual)==expected,label)
    else:
        require(actual==('' if expected is None else str(expected)),label)


def compare_ledger(actual,expected,label,ignore=()):
    require(len(actual)==len(expected),label+'_COUNT')
    keyed = {r['signal_id']:r for r in actual}; require(len(keyed)==len(actual),label+'_DUPLICATE')
    require(set(keyed)=={r['signal_id'] for r in expected},label+'_ID_SET')
    checked = 0
    for row in expected:
        for key,value in row.items():
            if key in ignore:
                continue
            compare_value(keyed[row['signal_id']].get(key,''),value,label+' '+row['signal_id']+' '+key); checked += 1
    return checked


def independent_coverage(symbol,raw,ss,tt,sk,xx):
    result = []; day = date(2023,1,1); first = min(raw).date() if raw else date(2024,1,1); prior = False
    groups = [{str(r.get('signal_at') or r.get('entry_at'))[:10]:[] for r in ledger} for ledger in (ss,tt,sk,xx)]
    for group,ledger in zip(groups,(ss,tt,sk,xx)):
        for r in ledger:
            group[str(r.get('signal_at') or r.get('entry_at'))[:10]].append(r)
    while day.year == 2023:
        slots = []
        for a,z in windows(day):
            while a < z:
                slots.append(a); a += FIVE
        if slots:
            label = str(day); ds,dt,dsk,dx = (group.get(label,[]) for group in groups)
            missing = sum(t not in raw for t in slots); invalid = sum(t in raw and not good(raw[t],symbol,t) for t in slots)
            result.append(dict(instrument=symbol,date=label,expected_bars=len(slots),valid_bars=len(slots)-missing-invalid,
                missing_bars=missing,invalid_bars=invalid,status='PRE_INCEPTION' if day < first else 'INCOMPLETE' if missing or invalid else 'COMPLETE',
                accepted_entries=sum(s['model_filled'] for s in ds),closed=len(dt),data_gap_skips=len(dsk),data_quality_excluded=len(dx),
                initial_flat_assumed=True,initial_flat_proven=False,prior_exclusion_requires_flat_assumption=prior if day >= first else False,
                remainder_of_day_blocked=bool(dx),following_day_contract='CONDITIONAL_FLAT; not a proven real close'))
            prior |= bool(dx)
        day += timedelta(days=1)
    return result



def independent_days(symbol,raw,signals,trades,skips,exclusions):
    first=min(raw).date() if raw else date(2024,1,1)
    result=[];prior=False;day=date(2023,1,1)
    by_day={}
    for kind,rows in [('signals',signals),('trades',trades),('skips',skips),('exclusions',exclusions)]:
        by_day[kind]={}
        for row in rows:
            label=row.get('date') or str(row['signal_at'])[:10]
            by_day[kind].setdefault(label,[]).append(row)
    while day.year==2023:
        label=str(day)
        if windows(day) and day>=first:
            ss=by_day['signals'].get(label,[]);tt=by_day['trades'].get(label,[])
            sk=by_day['skips'].get(label,[]);xx=by_day['exclusions'].get(label,[])
            result.append(dict(instrument=symbol,date=label,signals=sum(s['base_reason']=='SIGNAL' for s in ss),
                admitted_orders=sum(s['order_admitted'] for s in ss),closed=len(tt),initial_flat_assumed=True,initial_flat_proven=False,
                data_gap_policy='DATA_GAP_SKIP_V2',prior_exclusion_requires_flat_assumption=prior,
                following_day_contract='CONDITIONAL_FLAT; not a proven real close',data_gap_skips=len(sk),data_quality_excluded=len(xx),
                accepted_entries=sum(s['model_filled'] for s in ss),remainder_of_day_blocked=bool(xx)))
            prior |= bool(xx)
        day+=timedelta(days=1)
    return result

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
            exit_totals.append(D(0) if value==0 else value)
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
            gross_R=sum((D(t['gross_R']) for t in ts),D(0)),C1_R=sum((D(t['cost_R']) for t in ts),D(0)),metric_scope='CONDITIONAL_CLOSED_ONLY; initial gross-risk R; no continuous broker equity')


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




def independent_common_metrics(tt):
    m = independent_statistics(tt,28)
    keys = dict(closed='CLOSED',PF_C1_price='PF_price',PF_C1_R='PF_R',Net_R='Net_R',Net_price='Net_price',
                Expectancy_R='expectancy_R',Win_Rate='win_rate',Max_DD_R='conditional_closed_only_DD_R',cost_C1='C1_price')
    result = {k:None if m[v]==NA else m[v] for k,v in keys.items()}
    result.update(PF_no_losses=bool(tt) and not any(t['net_c1']<0 for t in tt),
                  exit_reasons=dict(sorted(Counter(t['exit_reason'] for t in tt).items())))
    return result


def compare_json(actual,expected,label):
    if isinstance(expected,dict):
        require(set(actual)==set(expected),label+'_KEY_SET')
        return sum(compare_json(actual[k],v,label+' '+k) for k,v in expected.items())
    if isinstance(expected,D):
        require(actual is not None and D(str(actual))==expected,label)
    else:
        require(actual==expected,label)
    return 1


def write_json(path,obj):
    path.write_text(json.dumps(obj,indent=2,sort_keys=True,default=encode)+'\n')


def write_csv(path,rows):
    columns=sorted({k for r in rows for k in r})
    with path.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=columns,lineterminator='\n');writer.writeheader()
        for row in rows:
            writer.writerow({k:json.dumps(v,sort_keys=True,default=encode) if isinstance(v,(dict,list)) else v for k,v in row.items()})


def source_metadata(root,policy):
    run=lambda *args:subprocess.check_output(['git','-C',str(root),*args],text=True).strip()
    require(run('rev-parse','HEAD')==policy['source_ref'],'PINNED_SOURCE_HEAD')
    require(not run('status','--porcelain=v1','--untracked-files=all'),'READ_ONLY_SOURCE_CLEAN')
    for spec in policy['inputs'].values():
        require(run('rev-parse',policy['source_ref']+':'+spec['path'])==spec['blob'],'PINNED_SOURCE_BLOB')
        require(run('ls-files','--stage','--',spec['path']).split()[1]==spec['blob'],'SOURCE_INDEX_BLOB')


def independent_grid(policy):
    require(policy['grid']==AXES and policy['grid_order']==list(AXES),'EXACT_PUBLISHED_AXES')
    fixed={'level_lookback_completed_m5':6,'min_level_penetration_ticks':1,'min_initial_price_risk_ticks':4,
           'dedup_same_instrument_same_direction_minutes':30,'max_session_entry_slack_minutes':35,
           'cost_C1_ticks_per_side':1,'single_test_bar_per_signal':True,'planned_legacy_net_to_gross_R':'3'}
    require({k:v for k,v in policy['parameters'].items() if k not in AXES}==fixed,'UNCHANGED_FIXED_GRAMMAR')
    specs=[]
    for re,sb,hold,tp in product((1,2),(1,2),(120,60),range(2,11)):
        specs.append(dict(policy['parameters'],min_close_reentry_ticks=re,stop_beyond_extreme_ticks=sb,
            max_hold_calendar_minutes=hold,planned_net_to_net_R=str(tp),
            configuration_id=f'LR_OPT2023_REENTRY{re}_SB{sb}_HOLD{hold}_TP{tp}'))
    require(read_csv(STUDY/'GRID.csv')==[{k:str(v) for k,v in s.items()} for s in specs],'INDEPENDENT_72_GRID')
    require(read_csv(STUDY/'EVALUATION_MATRIX.csv')==[dict(configuration_id=s['configuration_id'],instrument=i) for s in specs for i in policy['instruments']],'INDEPENDENT_216_MATRIX')
    return specs


def freeze_checks(output,policy):
    commitments=json.loads((STUDY/'source_commitments.json').read_text())
    manifest=json.loads((output/'freeze_manifest.json').read_text())
    freeze=manifest['freeze_commit'];require(len(freeze)==40,'REAL_FREEZE_SHA')
    for k,v in commitments.items():require(manifest[k]==v,'OUTPUT_FREEZE_MANIFEST '+k)
    required={str(path.relative_to(ROOT)) for path in STUDY.glob('*.py')}
    required|={str(path.relative_to(ROOT)) for path in (ROOT/'IntradayLab/core').glob('*.py')}
    required|={str((STUDY/name).relative_to(ROOT)) for name in ('GRID.csv','EVALUATION_MATRIX.csv','OPTIMIZATION_LEVEL_REJECTION_POLICY.json','synthetic_pipeline_receipt.json','pre_pnl_tests.log')}
    required.add('IntradayLab/strategies/level_rejection_m5_optimization_v1.py')
    require(required.issubset(commitments['dependencies_sha256']),'COMPLETE_FREEZE_DEPENDENCIES')
    committed=subprocess.check_output(['git','-C',str(ROOT),'show',freeze+':'+str((STUDY/'source_commitments.json').relative_to(ROOT))])
    require(committed==(STUDY/'source_commitments.json').read_bytes(),'FREEZE_COMMITMENTS_BYTES')
    for path,sha in commitments['dependencies_sha256'].items():
        require(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha,'FROZEN_DEPENDENCY '+path)
        value=subprocess.check_output(['git','-C',str(ROOT),'show',freeze+':'+path])
        require(hashlib.sha256(value).hexdigest()==sha,'COMMITTED_DEPENDENCY '+path)
    protected=json.loads((STUDY/'protected_file_sha256.json').read_text())
    for path,sha in protected.items():
        require(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha,'PROTECTED_FILE '+path)
    changes=subprocess.check_output(['git','-C',str(ROOT),'diff','--name-status',policy['base_main']],text=True).splitlines()
    require(all(r.startswith('A\tIntradayLab/') for r in changes),'INTRADAYLAB_ADDITIONS_ONLY')
    return freeze,len(protected)


def baseline_checks(symbol,raw,output,policy,control,counts):
    legacy_s,legacy_t,_,_=replay(symbol,raw,episodes(symbol,raw,policy['parameters']),legacy=True)
    archive=ROOT/'IntradayLab/results/level_rejection_2023_m5_v1'
    baseline=[r for r in read_csv(archive/'trades.csv') if r['instrument']==symbol]
    oldclosed=[r for r in baseline if r['status']=='CLOSED'];newclosed=[r for r in legacy_t if r['status']=='CLOSED']
    counts['baseline_oracle_fields']+=compare_ledger(oldclosed,newclosed,'RAW_BASELINE '+symbol)
    require(len(newclosed)==policy['instrument_admission'][symbol]['CLOSED'],'BASELINE_CLOSED '+symbol)
    oracle_days=len({t['entry_at'].date() for t in newclosed});oracle_months=len({t['entry_at'].strftime('%Y-%m') for t in newclosed})
    require(oracle_days==policy['instrument_admission'][symbol]['entry_days'] and oracle_months==policy['instrument_admission'][symbol]['entry_months'],'BASELINE_SAMPLE '+symbol)
    for name in ('signals','trades','days'):
        old=[r for r in read_csv(archive/(name+'.csv')) if r['instrument']==symbol]
        saved=read_csv(output/'baseline_replay'/symbol/(name+'.csv'))
        require(old==saved,'EXACT_ORIGINAL_ENGINE_REPLAY '+symbol+' '+name)
        counts['baseline_replay_fields']+=sum(len(r) for r in old)
    counts['baseline_signal_oracle_fields']+=compare_ledger([r for r in read_csv(archive/'signals.csv') if r['instrument']==symbol],legacy_s,'RAW_BASELINE_SIGNALS '+symbol)
    known={r['signal_id']:r for r in newclosed};current={r['signal_id']:r for r in control};common=sorted(set(known)&set(current))
    for ident in common:
        for k,v in known[ident].items():
            if k in ('prior_unknown_requires_flat_assumption',):continue
            require(current[ident].get(k)==v,'COMMON_BASELINE_CLOSED '+symbol+' '+ident+' '+k);counts['common_baseline_fields']+=1
    comparison=[]
    for ident in sorted(set(known)|set(current)):
        old,new=known.get(ident),current.get(ident)
        comparison.append(dict(instrument=symbol,signal_id=ident,comparison='IDENTICAL_COMMON_CLOSED' if old and new else 'LEGACY_ONLY_CLOSED' if old else 'V2_ONLY_CLOSED',
            baseline_status=old['status'] if old else '',v2_status=new['status'] if new else '',
            baseline_net_R=old['net_R_c1'] if old else '',v2_net_R=new['net_R_c1'] if new else '',
            explanation='' if old and new else 'DATA_GAP_SKIP_V2 explicitly changes missing-entry day blocking; separate cohort, no imputed closure'))
    observed=[r for r in read_csv(output/'baseline_comparison.csv') if r['instrument']==symbol]
    require(len(observed)==len(comparison),'BASELINE_COMPARISON_COUNT')
    for row,wanted in zip(observed,comparison):
        for k,v in wanted.items():compare_value(row[k],v,'BASELINE_COMPARISON '+k);counts['baseline_comparison_fields']+=1
    summary=json.loads((output/'baseline_replay.json').read_text())
    require(summary['status']=='PASS' and summary['original_strategy_config_and_results_unchanged'] and summary['bytes_2024_plus_read']==0,'BASELINE_REPLAY_REPORT_STATUS')
    report=summary['instruments'][symbol]
    for k,v in dict(legacy_CLOSED=len(newclosed),legacy_UNKNOWN=sum(t['status']=='UNKNOWN' for t in legacy_t),v2_CLOSED=len(control),
                    v2_SKIP=len(read_csv(output/'evaluations'/policy['historical_control_id']/symbol/'data_gap_skips.csv')),
                    v2_EXCLUDED=len(read_csv(output/'evaluations'/policy['historical_control_id']/symbol/'data_quality_exclusions.csv')),
                    common_CLOSED=len(common),legacy_only_ids=sorted(set(known)-set(current)),v2_only_ids=sorted(set(current)-set(known))).items():
        require(report[k]==v,'BASELINE_REPLAY_REPORT '+k);counts['baseline_report_fields']+=1
    return dict(instrument=symbol,legacy_CLOSED=len(newclosed),v2_control_CLOSED=len(control),
                common_CLOSED=len(common),legacy_only_CLOSED=len(set(known)-set(current)),v2_only_CLOSED=len(set(current)-set(known)),
                common_CLOSED_all_fields_exact=True,differences_policy='DATA_GAP_SKIP_V2; no invented unknown/excluded economics',status='PASS')


def audit(data_root,output,policy=None,raw=None,synthetic=False):
    policy=policy or json.loads((STUDY/'OPTIMIZATION_LEVEL_REJECTION_POLICY.json').read_text())
    require(policy['instruments']==['USDRUBF','CNYRUBF','GLDRUBF'],'ONLY_APPROVED_INSTRUMENTS')
    # The AST check catches later dependence on the system under test.
    for node in ast.walk(ast.parse(Path(__file__).read_text())):
        if isinstance(node,(ast.Import,ast.ImportFrom)):
            names=[a.name for a in node.names] if isinstance(node,ast.Import) else [node.module or '']
            require(all(not m.startswith('IntradayLab') and m not in ('runner','aggregation','contract') for m in names),'STANDARD_LIBRARY_ONLY_AUDITOR')
    specs=independent_grid(policy);counts=Counter();expected={};index=[];comparisons=[]
    freeze='SYNTHETIC';protected=0
    if not synthetic:
        freeze,protected=freeze_checks(output,policy);source_metadata(data_root,policy)
    if raw is None:
        raw,receipts=read_source(data_root,policy)
        provenance=json.loads((output/'input_provenance.json').read_text())
        require(provenance['source_sha']==policy['source_ref'] and provenance['bytes_2024_plus_read']==0 and provenance['rows_2024_plus_read']==0,'SOURCE_PROVENANCE_SCOPE')
        require(provenance['candle_rows_read']==sum(r['rows_2023'] for r in receipts.values()) and provenance['candle_bytes_read']==sum(r['bytes_read'] for r in receipts.values()),'SOURCE_PROVENANCE_TOTALS')
        observed={r['path']:r for r in provenance['actual_python_read_receipts']}
        require(set(observed)=={p['path'] for p in policy['inputs'].values()},'SOURCE_READ_PATH_SET')
        for symbol,spec in policy['inputs'].items():
            row=observed[spec['path']]
            for k,v in dict(bytes_read=spec['prefix_bytes'],maximum_offset=spec['prefix_bytes'],lines_read=spec['rows_2023']+1,
                            candle_rows_read=spec['rows_2023'],sha256=spec['prefix_sha256'],source_blob=spec['blob'],bytes_2024_plus_read=0,rows_2024_plus_read=0).items():
                require(row[k]==v,'SOURCE_READ_RECEIPT '+symbol+' '+k);counts['provenance_fields']+=1
    else:
        require(synthetic,'REAL_AUDIT_MUST_READ_RAW_SOURCE_INDEPENDENTLY');receipts={'synthetic':True}
    rows=read_csv(output/'all_candidates.csv');months=read_csv(output/'monthly_results.csv');dirs=read_csv(output/'direction_results.csv');funnels=read_csv(output/'execution_funnel.csv')
    wanted={(s['configuration_id'],i) for s in specs for i in policy['instruments']}
    def keyed(records,label,extra=()):
        mapping={(r['configuration_id'],r['instrument'],*(r[k] for k in extra)):r for r in records}
        need={(*pair,*extras) for pair in wanted for extras in product(*extra_values)} if extra else wanted
        require(len(mapping)==len(records) and set(mapping)==need,'EXACT_ROW_SET '+label)
        return mapping
    actual=keyed(rows,'CANDIDATES');ff=keyed(funnels,'FUNNELS')
    extra_values=[MONTHS];mm=keyed(months,'MONTHS',('month',))
    extra_values=[['LONG','SHORT']];dd=keyed(dirs,'DIRECTIONS',('direction',))
    for spec in specs:
        ident=spec['configuration_id'];parameters={k:v for k,v in spec.items() if k!='configuration_id'}
        for symbol in policy['instruments']:
            key=(ident,symbol);folder=output/'evaluations'/ident/symbol
            ss,tt,sk,xx=replay(symbol,raw[symbol],episodes(symbol,raw[symbol],parameters))
            for name,wanted_rows in [('signals',ss),('trades',tt),('data_gap_skips',sk),('data_quality_exclusions',xx),('rejected_nonfill',[s for s in ss if s['status'] in ('REJECTED','NONFILL')])]:
                observed=read_csv(folder/(name+'.csv'));counts[name+'_fields']+=compare_ledger(observed,wanted_rows,ident+' '+symbol+' '+name)
                require(all(r['status']!='UNKNOWN' for r in observed),'V2_NO_UNKNOWN')
                if name=='trades':require(all(r['status']=='CLOSED' for r in observed),'CLOSED_LEDGER_ONLY')
                if name=='data_quality_exclusions':require(all(not r.get(k) for r in observed for k in ('exit_price','exit_at','resolved_at','gross','gross_R','cost_c1','cost_R','net_c1','net_R_c1','realized_net_to_net_R')),'NO_EXCLUSION_PNL')
            daily=independent_days(symbol,raw[symbol],ss,tt,sk,xx);observed_days=read_csv(folder/'days.csv')
            require(len(observed_days)==len(daily),'DAY_LEDGER_COUNT')
            for observed_day,wanted_day in zip(observed_days,daily):
                for field,value in wanted_day.items():compare_value(observed_day.get(field,''),value,'DAY '+field);counts['day_fields']+=1
            fills={s['signal_id'] for s in ss if s['model_filled']}
            require(fills=={r['signal_id'] for r in tt+xx} and len(fills)==len(tt)+len(xx),'ACCEPTED_ENTRY_RECONCILIATION');counts['accepted_ID_checks']+=len(fills)
            cov=independent_coverage(symbol,raw[symbol],ss,tt,sk,xx);observed=read_csv(folder/'coverage_report.csv')
            require(len(observed)==len(cov),'COVERAGE_COUNT')
            for a,b in zip(observed,cov):
                for k,v in b.items():compare_value(a.get(k,''),v,'COVERAGE '+symbol+' '+k);counts['coverage_fields']+=1
            m=independent_statistics(tt);m.update(independent_checks(m));expected[key]=m;row=actual[key]
            for k,v in m.items():compare_value(row[k],v,'METRIC '+ident+' '+symbol+' '+k);counts['metric_fields']+=1
            for k,v in spec.items():compare_value(row[k],v,'CONFIG '+k)
            saved=json.loads((folder/'configuration.json').read_text())
            require(saved['parameters']==parameters and saved['execution']==policy['execution'],'CONFIG_PARAMETERS_EXECUTION')
            require(saved['source_sha']==policy['source_ref'] and saved['source_blob']==policy['inputs'][symbol]['blob'],'CONFIG_SOURCE')
            code_sha=hashlib.sha256((ROOT/'IntradayLab/strategies/level_rejection_m5_optimization_v1.py').read_bytes()).hexdigest()
            require(saved['strategy_sha256']==code_sha and row['strategy_sha256']==code_sha,'STRATEGY_SHA_PROVENANCE')
            require(row['source_sha']==policy['source_ref'],'ROW_SOURCE_SHA')
            if not synthetic:
                require(saved['freeze_commit']==freeze and row['freeze_commit']==freeze,'CONFIG_FREEZE')
            extra=dict(accepted_entries=len(fills),DATA_GAP_SKIP=len(sk),DATA_QUALITY_EXCLUDED=len(xx),
                conditional_flat_CLOSED=sum(t['prior_exclusion_requires_flat_assumption'] for t in tt),
                complete_coverage_days=sum(c['status']=='COMPLETE' for c in cov),incomplete_coverage_days=sum(c['status']=='INCOMPLETE' for c in cov),
                signals=sum(s['base_reason']=='SIGNAL' for s in ss),attempted_entries=sum(bool(s.get('pending_created')) for s in ss),
                raw_rejections=sum(s['raw_rejection'] for s in ss),dedup_30min=sum(s['base_reason']=='DEDUP_30MIN' for s in ss),
                calendar_trading_days=len(cov),observed_trading_days=sum(c['valid_bars']>0 for c in cov),months_without_closed=12-m['entry_months'],
                closed_per_calendar_trading_day=D(len(tt))/len(cov),closed_per_observed_trading_day=D(len(tt))/sum(c['valid_bars']>0 for c in cov),
                closed_per_active_entry_day=D(len(tt))/m['entry_days'] if m['entry_days'] else NA)
            with localcontext() as ctx:
                ctx.prec=50
                extra.update(exclusion_fraction=D(len(xx))/len(fills) if fills else NA,
                    skip_fraction_of_fills_and_skips=D(len(sk))/(len(fills)+len(sk)) if fills or sk else NA)
            for k,v in extra.items():compare_value(row[k],v,'COUNT_FREQUENCY '+k);counts['metric_fields']+=1
            reasons='|'.join(name for name,value,limit in [('CLOSED_BELOW_100',m['CLOSED'],100),('ENTRY_DAYS_BELOW_40',m['entry_days'],40),('ENTRY_MONTHS_BELOW_6',m['entry_months'],6)] if value<limit)
            require(row['sample_failure_reasons']==reasons,'SAMPLE_FAILURE_REASONS')
            for month in MONTHS:
                cohort=[t for t in tt if str(t['exit_at'] or t['exit_interval_start'])[:7]==month];mc=[c for c in cov if c['date'][:7]==month]
                values=dict(independent_statistics(cohort),complete_days=sum(c['status']=='COMPLETE' for c in mc),incomplete_days=sum(c['status']=='INCOMPLETE' for c in mc),
                    valid_bars=sum(c['valid_bars'] for c in mc),missing_bars=sum(c['missing_bars'] for c in mc),invalid_bars=sum(c['invalid_bars'] for c in mc),
                    accepted_entries=sum(c['accepted_entries'] for c in mc),DATA_GAP_SKIP=sum(c['data_gap_skips'] for c in mc),DATA_QUALITY_EXCLUDED=sum(c['data_quality_excluded'] for c in mc),
                    coverage_scope='ENTRY_DATE counts; CLOSED economics by EXIT_DATE')
                for k,v in values.items():compare_value(mm[(*key,month)][k],v,'MONTH '+k);counts['monthly_fields']+=1
            for side in (1,-1):
                values=dict(independent_statistics([t for t in tt if t['direction']==side]),DATA_GAP_SKIP=sum(s['direction']==side for s in sk),DATA_QUALITY_EXCLUDED=sum(t['direction']==side for t in xx))
                for k,v in values.items():compare_value(dd[(*key,'LONG' if side==1 else 'SHORT')][k],v,'DIRECTION '+k);counts['direction_fields']+=1
            funnel=dict(raw_directional_events=len(ss),signals=extra['signals'],ambiguous_directional_events=sum(s['base_reason']=='AMBIGUOUS_BOTH_SIDES' for s in ss),
                final_close_not_rejected_events=0,admissions=sum(s['order_admitted'] for s in ss),rejects=sum(s['base_reason']=='SIGNAL' and s['status']=='REJECTED' for s in ss),
                nonfills=sum(s['status']=='NONFILL' for s in ss),fills=len(fills),SKIP=len(sk),EXCLUDED=len(xx),CLOSED=len(tt),reason_counts=dict(sorted(Counter(s['reason'] for s in ss if s['reason']).items())))
            for k,v in funnel.items():compare_value(ff[key][k],v,'FUNNEL '+k);counts['funnel_fields']+=1
            # Independently rebuild the engine's lower precision conditional report.
            common=dict(accepted_entries=len(fills),closed=len(tt),data_gap_skips=len(sk),data_quality_excluded=len(xx),entry_reconciliation_passed=True,
                exclusion_fraction=D(len(xx))/len(fills) if fills else None,conditional_closed_only_C1=independent_common_metrics(tt),
                coverage_complete=bool(cov) and all(c['status']=='COMPLETE' for c in cov),conditional_flat_closed=extra['conditional_flat_CLOSED'],
                exclusion_reasons=dict(sorted(Counter(t['exclusion_reason'] for t in xx).items())),skip_reasons=dict(sorted(Counter(s['reason'] for s in sk).items())))
            common_json=json.loads((folder/'metrics.json').read_text());require(set(common_json['instruments'])=={symbol},'NO_CROSS_INSTRUMENT_METRIC_POOL')
            counts['common_metric_fields']+=compare_json(common_json['instruments'][symbol],common,'COMMON_METRICS')
            totals={k:common[k] for k in ('accepted_entries','closed','data_gap_skips','data_quality_excluded','exclusion_fraction')}
            counts['common_metric_fields']+=compare_json(common_json['totals_counts_only'],totals,'COMMON_TOTALS_COUNTS_ONLY')
            require(common_json['data_gap_policy']=='DATA_GAP_SKIP_V2','COMMON_DATA_POLICY')
            require(all(common_json[k] is None for k in ('annual_account_returns','annual_economics','pooled_price_portfolio')),'NO_FULL_ANNUAL_CLAIM')
            index.append(dict(configuration_id=ident,instrument=symbol,detail_directory=f'evaluations/{ident}/{symbol}',signals=len(ss),CLOSED=len(tt),SKIP=len(sk),EXCLUDED=len(xx)))
            if ident==policy['historical_control_id'] and not synthetic:
                comparisons.append(baseline_checks(symbol,raw[symbol],output,policy,tt,counts))
        print('independent audit '+ident,flush=True)
    edges=read_csv(output/'parameter_neighborhood.csv');edge_map={(r['configuration_id'],r['instrument'],r['neighbor_id']):r for r in edges};wanted_edges=set();selection=json.loads((output/'selection_report.json').read_text());results={}
    for symbol in policy['instruments']:
        passed=[]
        for spec in specs:
            ident=spec['configuration_id'];m=expected[(ident,symbol)];positive=0
            for other in specs:
                diffs=[k for k in AXES if spec[k]!=other[k]]
                if len(diffs)!=1:continue
                axis=diffs[0]
                if abs(AXES[axis].index(int(spec[axis]))-AXES[axis].index(int(other[axis])))!=1:continue
                n=expected[(other['configuration_id'],symbol)];qualifies=n['CLOSED']>=100 and n['PF_R']!=NA and n['PF_R']>=D('1.5') and n['expectancy_R']!=NA and n['expectancy_R']>0
                pair=(ident,symbol,other['configuration_id']);wanted_edges.add(pair);observed=edge_map[pair]
                for k,v in dict(changed_parameter=axis,neighbor_CLOSED=n['CLOSED'],neighbor_PF_R=n['PF_R'],neighbor_expectancy_R=n['expectancy_R'],neighbor_qualifies=qualifies).items():compare_value(observed[k],v,'NEIGHBOR '+k);counts['neighbor_fields']+=1
                positive+=qualifies
            m['pass_neighbors']=positive>=2;row=actual[(ident,symbol)]
            compare_value(row['positive_neighbor_count'],positive,'NEIGHBOR_COUNT');compare_value(row['pass_neighbors'],positive>=2,'NEIGHBOR_PASS')
            failed=[k.removeprefix('pass_') for k,v in m.items() if k.startswith('pass_') and not v]
            require(row['failure_reasons']=='|'.join(failed),'ALL_FAILED_GATES')
            status='INSUFFICIENT_SAMPLE' if not m['pass_sample'] else policy['candidate_status'] if not failed else 'DOES_NOT_QUALIFY'
            require(row['status']==status,'STATUS')
            if not failed:passed.append((ident,m))
            else:require(row['rank']==NA,'ONLY_FULL_PASSES_RANKED')
        ranked=sorted(passed,key=lambda x:(-x[1]['positive_exit_months'],-min(x[1]['PF_R'],x[1]['PF_price']),x[1]['conditional_closed_only_DD_R'],-x[1]['CLOSED'],x[0]))
        values=[expected[(p['configuration_id'],symbol)] for p in specs]
        result=dict(evaluated=72,sample_pass=sum(m['pass_sample'] for m in values),both_PF_pass=sum(m['pass_PF_R'] and m['pass_PF_price'] for m in values),
            sample_and_both_PF_pass=sum(m['pass_sample'] and m['pass_PF_R'] and m['pass_PF_price'] for m in values),months_pass=sum(m['pass_months'] for m in values),neighbors_pass=sum(m['pass_neighbors'] for m in values),
            base_study_criteria_pass=sum(all(v for k,v in m.items() if k.startswith('pass_') and k!='pass_neighbors') for m in values),full_criteria_pass=len(ranked),ranked_ids=[ident for ident,m in ranked],
            result=policy['candidate_status'] if ranked else policy['no_candidate_status'])
        require(selection['instruments'][symbol]==result,'SELECTION_COUNTS_RANKING '+symbol);counts['selection_checks']+=len(result)
        for rank,(ident,m) in enumerate(ranked,1):compare_value(actual[(ident,symbol)]['rank'],rank,'RANK')
        results[symbol]=result
    require(len(edge_map)==len(edges) and set(edge_map)==wanted_edges,'COMPLETE_NEIGHBOR_MATRIX')
    result_status=policy['candidate_status'] if any(r['full_criteria_pass'] for r in results.values()) else policy['no_candidate_status']
    require(selection['criteria']==policy['selection'] and selection['evaluations']==216 and selection['overall_result']==result_status,'SELECTION_BUDGET_CRITERIA_STATUS')
    observed=read_csv(output/'detailed_artifact_index.csv');require(len(observed)==len(index),'DETAIL_INDEX_COUNT')
    for a,b in zip(observed,index):
        for k,v in b.items():compare_value(a[k],v,'DETAIL_INDEX '+k);counts['index_fields']+=1
    result=dict(status='PASS',evaluations=216,checked_fields=dict(counts),independent_imports='STANDARD_LIBRARY_ONLY',
        independent_signal_method='Batch immediate-six timestamps with independent directional cooldown',
        independent_execution_method='Per-trade forward raw-M5 Open and interval oracle; observation-time busy/block replay',
        independent_economics_selection=True,protected_files_byte_verified=protected,exact_comparisons=True,
        bytes_2024_plus_read=0,external_human_signoff=False,separately_tasked_auditor=True,baseline_control='SYNTHETIC_NOT_APPLICABLE' if synthetic else 'PASS',
        baseline_comparison=comparisons,selection=result_status,source_read_receipts=receipts,freeze_commit=freeze)
    write_json(output/'audit.json',result)
    (output/'Independent_Audit.md').write_text('# Independent audit — Optimization Level Rejection M5 2023\n\n'
        'Status: **PASS**. A separately tasked auditor implemented a standard-library-only raw-M5 oracle.\n\n'
        'The oracle independently rebuilds all 72 configurations × 3 instruments, immediate six-bar levels, directional cooldown, confirmed signals, waiting, scalar-Open admission, structural Stop, full-net C1 Take, Stop-first, no entry-bar Take, deadlines, SKIP and EXCLUDED paths. Exact CLOSED-only metrics, all 12 months, both directions, coverage, parameter neighbors, every failed gate and fixed ranking are checked.\n\n'
        f'Checked field counts: {json.dumps(dict(counts),sort_keys=True)}.\n\n'
        'Protected prior files and committed freeze dependencies are byte checked. Original Baseline engine replay matches its frozen ledgers; independent raw paths verify original confirmed CLOSED and common V2 closures. Policy differences remain explicit. Zero 2024+ candle bytes read; annual account returns are unavailable. No external human reviewer signoff is claimed.\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(audit(args.data_root,args.output),sort_keys=True))
