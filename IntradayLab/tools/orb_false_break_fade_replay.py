"""Fixed 2023 ORB fade: completed-bar signal stage / Open-only entry adapter.

Historical full-unit fills are conditional model outcomes. No broker/queue proof.
The independent auditor imports none of this module's strategy/outcome functions.
"""
from collections import deque
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
import hashlib
import json
from pathlib import Path
import subprocess

from m5_baseline import windows, tick

D = Decimal
FIVE = timedelta(minutes=5)
LAB = Path(__file__).resolve().parents[1]
CONFIG = LAB / 'config/stage2_orb_false_break_fade_m5_v1.json'
FREEZE = '8291f0efb7346b0bf4f01331caffd5eee7a242cc'


def read_source(root, config):
    git = lambda *a: subprocess.check_output(['git', '-C', str(root), *a], text=True).strip()
    if git('rev-parse', 'HEAD') != config['source_ref'] or git('status', '--porcelain=v1', '--untracked-files=all'):
        raise ValueError('SOURCE_REF_OR_CLEANLINESS')
    result, receipts = {}, {}
    for symbol, spec in config['inputs'].items():
        if git('ls-files', '--stage', '--', spec['path']).split()[1] != spec['blob']:
            raise ValueError('SOURCE_BLOB')
        path = root / spec['path']
        before = path.stat()
        with path.open('rb', buffering=0) as raw:
            content = raw.read(spec['prefix_bytes'])
        after = path.stat()
        if (before.st_size, before.st_ino, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_ino, after.st_mtime_ns, after.st_ctime_ns):
            raise ValueError('SOURCE_CHANGED')
        if len(content) != spec['prefix_bytes'] or hashlib.sha256(content).hexdigest() != spec['prefix_sha256'] or not content.endswith(b'\n'):
            raise ValueError('PREFIX_HASH_OR_LENGTH')
        lines = content.decode('utf-8-sig').splitlines()
        if lines[0] != 'Ticker;Datetime;Open;High;Low;Close;Volume' or len(lines)-1 != spec['rows_2023']:
            raise ValueError('HEADER_OR_ROWS')
        rows, prior = {}, None
        for line in lines[1:]:
            s, label, *prices = line.split(';')
            at = datetime.fromisoformat(label)
            if s != symbol or at.year != 2023 or at.tzinfo or at.second or at.microsecond or at.minute % 5 or (prior is not None and at <= prior):
                raise ValueError('DATE_SCHEMA_ORDER')
            prior = at
            values = tuple(map(D, prices))
            if len(values) != 5 or not all(x.is_finite() for x in values):
                raise ValueError('FINITE_SCHEMA')
            o,h,l,c,v = values
            if not (0 < l <= min(o,c) <= max(o,c) <= h and v >= 0) or any(x % tick(symbol, at) for x in values[:4]):
                raise ValueError('OHLC_GRID')
            rows[at] = values
        if str(min(rows)) != spec['first']:
            raise ValueError('FIRST_DATE')
        result[symbol] = rows
        receipts[symbol] = dict(spec, bytes_read=len(content), bytes_2024_plus_read=0, bytes_2025_plus_read=0, last=str(max(rows)), reader='unbuffered FileIO exact byte prefix')
    return result, receipts


def valid(row):
    return row is not None and row[4] > 0


def dates():
    day = date(2023,1,1)
    while day.year == 2023:
        yield day
        day += timedelta(days=1)


def slots(day):
    for a,z in windows(day):
        t = a
        while t < z:
            yield t,(a,z)
            t += FIVE


def base_signals(symbol, rows):
    """Streaming completed M5 only. Output never depends on future entry data."""
    records, daily, coverage = [], [], []
    for day in dates():
        ws = windows(day)
        if not ws:
            continue
        origin = datetime.combine(day, datetime.min.time()).replace(hour=10)
        if day < min(rows).date():
            coverage.append(dict(instrument=symbol,date=str(day),status='PRE_INCEPTION',expected_bars=0,valid_bars=0,missing_bars=0,zero_volume_bars=0,or_available=False))
            continue
        used, pending = set(), {}
        or_rows, bounds, history, last_parent = [], None, deque(maxlen=15), None
        previous_window = None
        day_records = []
        missing = zero = count = 0
        def finish(ep, bar=None, why='NO_RECLAIM'):
            rec = ep['row']
            rec['base_reason'] = why
            if bar is not None:
                at,b,w = bar
                rec.update(signal_at=at+FIVE,reclaim_start=at,waiting_bar_start=at+FIVE,waiting_bar_closed_at=at+2*FIVE,order_sent_at=at+2*FIVE,planned_execution_at=at+2*FIVE,
                           stop=ep['extreme'] + (-ep['direction'])*ep['tick'],
                           m15_start=last_parent[0] if last_parent else None,
                           m15_open=last_parent[1] if last_parent else None,
                           m15_high=last_parent[2] if last_parent else None,
                           m15_low=last_parent[3] if last_parent else None,
                           m15_close=last_parent[4] if last_parent else None,
                           m15_available_at=last_parent[0]+3*FIVE if last_parent else None,
                           m15_direction=(1 if last_parent[4]>last_parent[1] else -1 if last_parent[4]<last_parent[1] else 0) if last_parent else None)
            day_records.append(rec)
        for at,w in slots(day):
            b = rows.get(at)
            if w != previous_window:
                for ep in pending.values():
                    finish(ep,why='NO_RECLAIM_WINDOW')
                pending.clear();history.clear();last_parent=None
            previous_window = w
            if not valid(b):
                missing += b is None
                zero += b is not None
                for ep in pending.values():
                    finish(ep,why='NO_RECLAIM_GAP')
                pending.clear();history.clear();last_parent=None
                if at == origin+2*FIVE:
                    bounds = None
                continue
            count += 1
            history.append((at,b))
            # Current completed bar can complete an aligned M15 parent.
            if (at.minute+5)%15 == 0 and len(history)>=3:
                tail=list(history)[-3:]
                if tail[0][0].minute%15==0 and tail[0][0]+2*FIVE==at and tail[0][0]>=w[0]:
                    last_parent=(tail[0][0],tail[0][1][0],max(x[1][1] for x in tail),min(x[1][2] for x in tail),b[3])
            if origin <= at <= origin+2*FIVE:
                or_rows.append((at,b))
                if at == origin+2*FIVE and [x[0] for x in or_rows] == [origin,origin+FIVE,origin+2*FIVE]:
                    bounds=(max(x[1][1] for x in or_rows),min(x[1][2] for x in or_rows))
                continue
            if bounds is None:
                continue
            high,low=bounds
            step=tick(symbol,at)
            upper=b[1]>=high+step;lower=b[2]<=low-step
            if upper and lower and (len(used)<2 or pending):
                for ep in pending.values():
                    finish(ep,why='NO_RECLAIM_AMBIGUOUS')
                pending.clear();used.update((-1,1))
                day_records.append(dict(signal_id=f'{symbol}_{day}_AMB_{at:%H%M}',instrument=symbol,date=str(day),direction=0,sweep_start=at,signal_at=None,base_reason='AMBIGUOUS_BOTH_SIDES',or_high=high,or_low=low))
                continue
            for direction,ep in list(pending.items()):
                ep['extreme']=max(ep['extreme'],b[1]) if direction==-1 else min(ep['extreme'],b[2])
                reclaim=(low<=b[3]<=high-2*step) if direction==-1 else (low+2*step<=b[3]<=high)
                finish(ep,(at,b,w) if reclaim else None,'SIGNAL' if reclaim else 'NO_RECLAIM')
                del pending[direction]
            for direction,swept in ((-1,upper),(1,lower)):
                if not swept or direction in used:
                    continue
                used.add(direction)
                atr=None
                if len(history)==15:
                    h=list(history)
                    atr=sum((max(c[1][1]-c[1][2],abs(c[1][1]-a[1][3]),abs(c[1][2]-a[1][3])) for a,c in zip(h,h[1:])),D(0))/14
                size=b[1]-high if direction==-1 else low-b[2]
                rec=dict(signal_id=f'{symbol}_{day}_{direction}_{at:%H%M}',instrument=symbol,date=str(day),direction=direction,sweep_start=at,sweep_closed_at=at+FIVE,signal_at=None,or_high=high,or_low=low,or_available_at=origin+3*FIVE,sweep_size=size,sweep_tick=step,atr14=atr,atr_ready=atr is not None,atr_pass=atr is not None and size>=max(step,D('.30')*atr),window_start=w[0],window_end=w[1])
                ep={'row':rec,'direction':direction,'tick':step,'extreme':b[1] if direction==-1 else b[2]}
                reclaim=(low<=b[3]<=high-2*step) if direction==-1 else (low+2*step<=b[3]<=high)
                if reclaim:
                    finish(ep,(at,b,w),'SIGNAL')
                elif at+FIVE < w[1]:
                    pending[direction]=ep
                else:
                    finish(ep,why='NO_RECLAIM_WINDOW')
        for ep in pending.values():
            finish(ep,why='NO_RECLAIM_DAY_END')
        if bounds is None:
            day_records.append(dict(signal_id=f'{symbol}_{day}_NO_OR',instrument=symbol,date=str(day),direction=0,signal_at=None,sweep_start=origin,base_reason='NO_OR'))
        records.extend(day_records)
        coverage.append(dict(instrument=symbol,date=str(day),status='COMPLETE' if missing+zero==0 else 'INCOMPLETE',expected_bars=count+missing+zero,valid_bars=count,missing_bars=missing,zero_volume_bars=zero,or_available=bounds is not None))
        daily.append(dict(instrument=symbol,date=str(day),observed=count>0,or_available=bounds is not None,base_signals=sum(x['base_reason']=='SIGNAL' for x in day_records)))
    records.sort(key=lambda x:(x.get('signal_at') or x['sweep_start']+FIVE,x['signal_id']))
    return records,daily,coverage


def open_adapter(openprice, direction, stop, step):
    """Receives no entry-bar High/Low/Close/Volume."""
    risk=direction*(openprice-stop)
    if risk<=0:
        return None
    target=openprice+direction*D('1.5')*risk
    target=(target/step).to_integral_value(rounding=ROUND_CEILING if direction==1 else ROUND_FLOOR)*step
    return risk,target


def trade_path(symbol, rows, trade):
    """Resident orders; scheduled market exit reads only its Open."""
    entry=trade['entry_at']; direction=trade['direction']; stop=trade['stop']; take=trade['take']
    end=min(entry+timedelta(minutes=60),trade['window_end']-FIVE)
    at=entry
    while at<=end:
        b=rows.get(at)
        if not valid(b):
            return dict(status='UNKNOWN',exit_reason='UNKNOWN',unknown_reason='MISSING_EXPOSED_BAR' if b is None else 'INVALID_EXPOSED_BAR',exit_at=None,exit_interval_start=None,exit_interval_end=None,exit_price=None,resolved_at=at+FIVE)
        o,h,l,c,v=b
        gap=o<=stop if direction==1 else o>=stop
        if gap:
            return dict(status='CLOSED',exit_reason='STOP',exit_at=at,exit_interval_start=at,exit_interval_end=at,exit_price=o,resolved_at=at,adverse_gap=True)
        if at==end:
            return dict(status='CLOSED',exit_reason='TIME' if end==entry+timedelta(minutes=60) else 'SESSION_FLAT',exit_at=at,exit_interval_start=at,exit_interval_end=at,exit_price=o,resolved_at=at)
        sh=l<=stop if direction==1 else h>=stop
        th=h>=take if direction==1 else l<=take
        if sh or (th and at!=entry):
            return dict(status='CLOSED',exit_reason='STOP' if sh else 'TAKE',exit_at=None,exit_interval_start=at,exit_interval_end=at+FIVE,exit_price=stop if sh else take,resolved_at=at+FIVE,stop_take_conflict=sh and th,entry_bar=at==entry)
        at+=FIVE
    raise AssertionError('UNREACHABLE')


def replay(symbol, rows, records, architecture, spec):
    signals,trades=[],[]
    occupied_until=None; blocked=False; last_order=None
    for original in records:
        s=dict(original,architecture=architecture,status='REJECTED',reason=original['base_reason'],order_admitted=False,model_filled=False)
        signals.append(s)
        if s['base_reason']!='SIGNAL':
            continue
        if spec['atr'] and not s['atr_ready']:
            s['reason']='NO_ATR';continue
        if spec['atr'] and not s['atr_pass']:
            s['reason']='ATR_SWEEP_TOO_SMALL';continue
        if spec['mtf'] and s['m15_direction']!=s['direction']:
            s['reason']='NO_M15' if s['m15_direction'] is None else 'M15_DIRECTION';continue
        now=s['signal_at'];target=s['planned_execution_at']
        if blocked:
            s['reason']='UNKNOWN_POSITION_BLOCK';continue
        if (occupied_until is not None and now<occupied_until) or (last_order is not None and now<last_order):
            s['reason']='POSITION_BUSY';continue
        if target>=s['window_end']-FIVE or target<s['window_start']:
            s['reason']='SESSION_LIMIT';continue
        if not valid(rows.get(s['waiting_bar_start'])):
            s['reason']='NO_WAITING_BAR';continue
        s['order_admitted']=True;last_order=target
        b=rows.get(target)
        t=dict(architecture=architecture,instrument=symbol,signal_id=s['signal_id'],direction=s['direction'],signal_at=now,sweep_start=s['sweep_start'],reclaim_start=s['reclaim_start'],waiting_bar_closed_at=s['waiting_bar_closed_at'],order_sent_at=s['order_sent_at'],planned_execution_at=target,entry_at=None,entry_price=None,stop=s['stop'],take=None,risk=None,window_end=s['window_end'],gross=None,cost_c1=None,cost_c2=None,net_c1=None,net_c2=None,net_R_c1=None,net_R_c2=None)
        if b is None:
            s.update(status='UNKNOWN',reason='MISSING_EXECUTION_BAR')
            t.update(status='UNKNOWN',exit_reason='UNKNOWN',unknown_reason='MISSING_EXECUTION_BAR',model_filled=False,exit_at=None,exit_interval_start=None,exit_interval_end=None,exit_price=None,resolved_at=target+FIVE)
            trades.append(t);blocked=True;continue
        geometry=open_adapter(b[0],s['direction'],s['stop'],tick(symbol,target))
        if geometry is None:
            s.update(status='NONFILL',reason='INVALID_STOP_GEOMETRY');continue
        risk,take=geometry
        s.update(status='MODEL_FILLED',reason='',model_filled=True,entry_open=b[0],risk=risk,take=take)
        t.update(entry_at=target,entry_price=b[0],take=take,risk=risk,model_filled=True,entry_tick=tick(symbol,target))
        t.update(trade_path(symbol,rows,t))
        t['cost_entry_c1']=tick(symbol,target);t['cost_entry_c2']=2*tick(symbol,target)
        if t['status']=='CLOSED':
            exit_time=t['exit_interval_start'];gross=s['direction']*(t['exit_price']-t['entry_price'])
            cost=tick(symbol,target)+tick(symbol,exit_time)
            t.update(gross=gross,exit_tick=tick(symbol,exit_time),cost_c1=cost,cost_c2=2*cost,net_c1=gross-cost,net_c2=gross-2*cost,net_R_c1=(gross-cost)/risk,net_R_c2=(gross-2*cost)/risk)
            occupied_until=t['resolved_at']
        else:
            blocked=True
        trades.append(t)
    return signals,trades


def encode(value):
    if isinstance(value,(Decimal,datetime,date)):
        return str(value)
    raise TypeError(type(value))


def dump(path,value):
    path.write_text(json.dumps(value,default=encode,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
