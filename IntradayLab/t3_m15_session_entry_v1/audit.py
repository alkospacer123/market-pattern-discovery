"""Independent stdlib parser, recursive indicators, slice-based replay and reports.
Algorithmic independence, same author; external reviewer audit remains pending.
No import of engine.py/research.py or any strategy implementation.
"""
import argparse
import csv
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
import json,math,hashlib,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
RULES=('CONTROL','T1','T2')
SYMBOLS=('USDRUBF','CNYRUBF','GLDRUBF','IMOEXF')
DELTAS={}

def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1048576), b''):
            digest.update(b)
    return digest.hexdigest()


def prefix(path):
    data = []
    with path.open('rb') as f:
        assert f.readline().strip() == b'Ticker;Datetime;Open;High;Low;Close;Volume'
        while True:
            parts, separators = bytearray(), 0
            while separators < 2:
                b = f.read(1)
                if not b: break
                parts += b
                separators += b == b';'
            if not parts: break
            assert separators == 2
            stamp = parts.decode().split(';')[1]
            if stamp >= '2025-01-01': break
            tail = f.readline().decode().strip().split(';')
            if stamp < '2023-01-01': continue
            at = datetime.fromisoformat(stamp+'+03:00')+timedelta(minutes=15)
            if at.year >= 2025: continue
            data.append({'at':at, 'o':float(tail[0]),'h':float(tail[1]),'l':float(tail[2]),'c':float(tail[3])})
    assert all(a['at'] < b['at'] for a,b in zip(data,data[1:]))
    return data


def smooth(values, alpha, minimum):
    """Independent recursive adjust=False exponential average with NaN handling."""
    value, count, weight, out = None, 0, 1., []
    for x in values:
        finite = x is not None and math.isfinite(x)
        if value is None:
            if finite: value, count = x, 1
        else:
            weight *= 1-alpha
            if finite:
                value = (weight*value+alpha*x)/(weight+alpha)
                weight, count = 1., count+1
        out.append(value if count >= minimum else None)
    return out


def ranges(bars):
    return [max(b['h']-b['l'],abs(b['h']-bars[i-1]['c']) if i else 0.,abs(b['l']-bars[i-1]['c']) if i else 0.) for i,b in enumerate(bars)]


def derive(raw,p):
    days = {}
    for b in raw:days.setdefault(b['at'].date(),[]).append(b)
    high = []
    for day in days.values():
        for j in range(0,len(day),4):
            w = day[j:j+4]
            if len(w) == 4 and all(b['at']-a['at'] == timedelta(minutes=15) for a,b in zip(w,w[1:])):
                high.append({'at':w[-1]['at'],'h':max(b['h'] for b in w),'l':min(b['l'] for b in w),'c':w[-1]['c']})
    atr = smooth(ranges(raw),1/p['atr_period'],p['atr_period'])
    ha = smooth(ranges(high),1/p['atr_period'],p['atr_period'])
    ema = smooth([b['c'] for b in high],2/(p['ema_period']+1),p['ema_period'])
    plus,minus = [0.],[0.]
    for a,b in zip(high,high[1:]):
        up,down = b['h']-a['h'],a['l']-b['l']
        plus.append(up if up > down and up > 0 else 0.)
        minus.append(down if down > up and down > 0 else 0.)
    plus = smooth(plus,1/p['adx_period'],p['adx_period'])
    minus = smooth(minus,1/p['adx_period'],p['adx_period'])
    adx = smooth([100*abs(a-b)/(a+b) if a is not None and b is not None and a+b > 0 else None for a,b in zip(plus,minus)],1/p['adx_period'],p['adx_period'])
    for j,b in enumerate(high):
        slope = ema[j]-ema[j-p['slope_lookback']] if j >= p['slope_lookback'] and ema[j] is not None and ema[j-p['slope_lookback']] is not None else None
        w = ha[max(0,j-p['atr_average_period']+1):j+1]
        average = sum(w)/len(w) if len(w) == p['atr_average_period'] and all(x is not None for x in w) else None
        ratio = ha[j]/average if average else None
        regime = 0
        if slope is not None and adx[j] is not None and average is not None and adx[j] > p['adx_threshold'] and ha[j] > average:
            if b['c'] > ema[j] and slope > 0:regime = 1
            if b['c'] < ema[j] and slope < 0:regime = -1
        b.update(slope=slope,adx=adx[j],ratio=ratio,regime=regime)
    cursor = -1
    rows = []
    for i,b in enumerate(raw):
        while cursor+1 < len(high) and high[cursor+1]['at'] <= b['at']:cursor += 1
        h = high[cursor] if cursor >= 0 else None
        previous_h = high[cursor-1] if cursor > 0 else None
        prior = raw[max(0,i-p['breakout_period']):i]
        upper = max(x['h'] for x in prior) if len(prior) == p['breakout_period'] else None
        lower = min(x['l'] for x in prior) if len(prior) == p['breakout_period'] else None
        signal = 0
        if h and upper is not None:
            if h['regime'] == 1 and b['c'] > upper:signal = 1
            if h['regime'] == -1 and b['c'] < lower:signal = -1
        rows.append(b | {'atr':atr[i],'previous_atr':atr[i-1] if i else None,'signal':signal,
            'upper':upper,'lower':lower,'h1':h,'previous_h1':previous_h})
    return rows


def gate(at,previous,rule):
    if rule=='CONTROL':return True,'CONTROL'
    if rule=='T1':
        local=at.astimezone(ZoneInfo('Europe/Moscow'))
        okay=10<=local.hour<18
        return okay,'CORE_HOURS' if okay else 'OUTSIDE_CORE_HOURS'
    if previous is None:return False,'NO_PREVIOUS_OBSERVED_CLOSE'
    if (at-previous).total_seconds()>900:return False,'FIRST_BAR_AFTER_OBSERVED_GAP'
    return True,'CONTINUOUS_OBSERVED_CLOSES'


def feature_fields(b):
    h,old=b['h1'],b['previous_h1']
    return {'ATR':b['atr'],'PreviousATR':b['previous_atr'],'H1ADX':h['adx'],'H1PreviousADX':old['adx'],
        'H1Slope':h['slope'],'H1PreviousSlope':old['slope'],'H1ATRRatio':h['ratio'],
        'H1PreviousATRRatio':old['ratio'],'H1AvailableAt':h['at'],'H1PreviousAvailableAt':old['at'],
        'signal_open':b['o'],'signal_high':b['h'],'signal_low':b['l']}


def simulate(rows,p,rule,symbol,version):
    trades,stops,entries,gaps,snapshots=[],[],[],[],[]
    position=None;ids={'version':version,'rule':rule,'instrument':symbol}
    alias={'USDRUBF':'Si','CNYRUBF':'CNY'}.get(symbol,symbol)
    def snapshot(q,b):
        start,s=q['start'],q['side'];entry=rows[start]['c'];risk=q['risk']
        return ids|{'trade_id':q['id'],'direction':'LONG' if s==1 else 'SHORT',
            'entry_time':rows[start]['at'].isoformat(),'entry_price':entry,'initial_stop':q['initial'],
            'initial_risk':risk,'active_stop':q['active'],'breakout_level':rows[start]['upper'] if s==1 else rows[start]['lower'],
            'last_close':b['at'].isoformat(),'last_close_price':b['c'],
            'unrealized_gross_R_at_last_close':s*(b['c']-entry)/risk,'pending_exit_decision':None,
            'status':'OPEN_NOT_LIQUIDATED_EXCLUDED_FROM_CLOSED_TRADE_METRICS'}
    for i,b in enumerate(rows):
        at=b['at'];previous=rows[i-1]['at'] if i else None
        if i and previous.strftime('%Y-%m')!=at.strftime('%Y-%m') and position:
            snapshots.append(snapshot(position,rows[i-1])|{'month':previous.strftime('%Y-%m'),'year':previous.year})
        allowed,reason=gate(at,previous,rule)
        delta=(at-previous).total_seconds()/60 if i else None
        gap=bool(i and delta>15)
        overnight=bool(gap and (previous-timedelta(minutes=15)).date()!=(at-timedelta(minutes=15)).date())
        if not i or gap:
            gaps.append(ids|{'current_close':at,'previous_close':previous,'delta_minutes':delta,
                'reason':'OBSERVED_GAP_GT_15_MIN' if i else 'NO_PREVIOUS_OBSERVED_CLOSE',
                'cross_date':bool(gap and previous.date()!=at.date()),'cross_observed_open_date':overnight,
                'original_signal':b['signal'],'entry_rule_pass':allowed,'position_before_bar':position['id'] if position else None})
        exited=None
        if position:
            q=position;start=q['start'];s=q['side'];entry=rows[start]['c'];risk=q['risk'];active=q['active']
            survived=rows[start+1:i]
            lo=min([entry]+[r['l'] for r in survived]);hi=max([entry]+[r['h'] for r in survived])
            extreme=hi if s==1 else lo
            open_hit=b['o']<=active if s==1 else b['o']>=active
            hit=open_hit or (b['l']<=active if s==1 else b['h']>=active)
            d=ids|{'trade_id':q['id'],'bar_open_time':at-timedelta(minutes=15),'bar_close_time':at,
                'active_stop':active,'initial_risk':risk,'extreme_before':extreme,'open':b['o'],'high':b['h'],'low':b['l'],
                'ATR_at_close':b['atr'],'stop_hit':hit,'stop_gap':bool(open_hit and b['o']!=active),
                'observed_gap_before_bar':gap,'observed_overnight_gap_before_bar':overnight}
            if hit:
                fill=b['o'] if open_hit else active
                exposure=rows[start:i+1]
                deltas=[(y['at']-x['at']).total_seconds()/60 for x,y in zip(exposure,exposure[1:])]
                nights=sum((y['at']-x['at']).total_seconds()>900 and
                    (y['at']-timedelta(minutes=15)).date()!=(x['at']-timedelta(minutes=15)).date() for x,y in zip(exposure,exposure[1:]))
                trades.append(ids|{'trade_id':q['id'],'direction':'LONG' if s==1 else 'SHORT',
                    'entry_time':rows[start]['at'],'entry_price':entry,'initial_stop':q['initial'],'initial_risk':risk,
                    'breakout_level':rows[start]['upper'] if s==1 else rows[start]['lower'],
                    'exit_time':at,'exit_bar_open_time':at-timedelta(minutes=15),'exit_bar_close_time':at,
                    'exit_price':fill,'gross_R':s*(fill-entry)/risk,
                    'exit_type':'INITIAL_STOP' if active==q['initial'] else 'RATCHETED_STOP',
                    'active_stop_at_exit':active,'trailing_updates':q['updates'],'gap_exit':bool(fill!=active),
                    'exit_at_open':open_hit,'rule_decision_time':None,'rule_stop_conflict_at_open':False,
                    'bars_held':i-start,'holding_minutes':(at-rows[start]['at']).total_seconds()/60,
                    'MAE_R':max(0.,entry-lo if s==1 else hi-entry,s*(entry-fill))/risk,
                    'MFE_R':max(0.,hi-entry if s==1 else entry-lo)/risk,
                    'cross_calendar_day':at.date()!=rows[start]['at'].date(),'year':at.year,
                    'observed_gaps_exposed':sum(x>15 for x in deltas),'observed_overnight_gaps_exposed':nights,
                    **feature_fields(rows[start])})
                d.update(phase='EXIT',exit_price=fill,extreme_after=None,trail_proposal=None,active_stop_next_bar=None,trailing_changed=False)
                exited=q['id'];position=None
            else:
                extreme=max(extreme,b['h']) if s==1 else min(extreme,b['l'])
                proposal=extreme-s*p['trail_atr']*b['atr']
                new=sorted([active,proposal])[1 if s==1 else 0]
                q['active']=new;q['updates']+=int(active!=new)
                d.update(phase='SURVIVED',exit_price=None,extreme_after=extreme,trail_proposal=proposal,
                    active_stop_next_bar=new,trailing_changed=bool(new!=active))
            stops.append(d)
        if b['signal'] and b['atr'] is not None:
            s=b['signal'];occupied=position is not None;accepted=not occupied and allowed
            tid=f'T3-M15-{alias}-{len(trades)+1:06d}' if accepted else None
            initial=b['c']-s*p['stop_atr']*b['atr']
            entries.append(ids|{'signal_time':at,'previous_observed_close':previous,'delta_minutes':delta,
                'moscow_hour':at.astimezone(ZoneInfo('Europe/Moscow')).hour,
                'direction':'LONG' if s==1 else 'SHORT','original_signal':s,'rule_pass':allowed,'rule_reason':reason,
                'position_occupied':occupied,'occupied_trade_id':position['id'] if occupied else None,
                'entry_accepted':accepted,'decision_reason':'ACCEPTED' if accepted else 'RULE_AND_OCCUPIED' if occupied and not allowed else 'RULE_BLOCKED' if not allowed else 'POSITION_OCCUPIED',
                'trade_id':tid,'same_close_exit_trade_id':exited,'entry_price':b['c'],
                'candidate_initial_stop':initial,'ATR':b['atr'],'H1AvailableAt':b['h1']['at'],
                'PriorHigh':b['upper'],'PriorLow':b['lower']})
            if accepted:position={'id':tid,'start':i,'side':s,'initial':initial,'risk':abs(b['c']-initial),'active':initial,'updates':0}
    opened=snapshot(position,rows[-1]) if position else None
    if opened:snapshots.append(opened|{'month':rows[-1]['at'].strftime('%Y-%m'),'year':rows[-1]['at'].year})
    return trades,opened,stops,entries,gaps,snapshots


def read(path):
    with path.open() as f:return list(csv.DictReader(f))

def check(value,saved,label):
    if value is None:assert saved in ('',None),(label,value,saved)
    elif isinstance(value,bool):assert saved in (value,str(value)),(label,value,saved)
    elif isinstance(value,datetime):assert value==datetime.fromisoformat(saved),(label,value,saved)
    elif isinstance(value,str):assert value==saved,(label,value,saved)
    else:
        delta=abs(value-float(saved));DELTAS[label]=max(DELTAS.get(label,0.),delta)
        assert math.isfinite(delta) and delta<=1e-8,(label,value,saved,delta)

def compare(expected,actual,label):
    assert len(expected)==len(actual),(label,len(expected),len(actual))
    count=0
    for a,b in zip(expected,actual):
        assert set(a)==set(b),(label,'FIELD_SET',set(a)^set(b))
        for k,v in a.items():check(v,b[k],label+'.'+k);count+=1
    return count


def summary(rows,calendar,opened):
    rows=sorted(rows,key=lambda r:(r['exit_time'],r['instrument'],r['trade_id']))
    vals=[r['gross_R'] for r in rows];plus=sum(x for x in vals if x>0);minus=-sum(x for x in vals if x<0)
    mon={m:sum(r['gross_R'] for r in rows if r['exit_time'].strftime('%Y-%m')==m) for m in calendar}
    total=peak=dd=0.;streak=longest=0
    for x in vals:
        total+=x;peak=max(peak,total);dd=max(dd,peak-total)
        streak=streak+1 if x<0 else 0;longest=max(longest,streak)
    ms=maxms=0
    for x in mon.values():ms=ms+1 if x<0 else 0;maxms=max(maxms,ms)
    worst=min(mon,key=mon.get) if mon else None
    out={'closed_trades':len(rows),'open_positions_at_period_end':opened,'gross_PF':plus/minus if minus else None,
        'gross_R':sum(vals),'expectancy_R':sum(vals)/len(vals) if vals else None,'positive_R':plus,
        'negative_R_volume':minus,'max_drawdown_closed_R':dd,'max_consecutive_losses':longest,
        'calendar_months':len(calendar),'positive_months':sum(x>0 for x in mon.values()),
        'negative_months':sum(x<0 for x in mon.values()),'zero_months':sum(x==0 for x in mon.values()),
        'no_closed_trade_months':sum(not any(r['exit_time'].strftime('%Y-%m')==m for r in rows) for m in calendar),
        'worst_month':worst,'worst_month_R':mon.get(worst),'win_rate':sum(x>0 for x in vals)/len(vals) if vals else None,
        'max_losing_month_streak':maxms}
    for sign in ('positive','negative','zero'):out[sign+'_month_share']=out[sign+'_months']/len(calendar) if calendar else None
    wins=sorted([x for x in vals if x>0],reverse=True)
    for n in (5,10):
        top=sum(wins[:n]);out.update({f'top{n}_positive_R':top,f'top{n}_share_positive_R':top/plus if plus else None,
            f'gross_R_without_top{n}':sum(vals)-top,f'gross_PF_without_top{n}':(plus-top)/minus if minus else None})
    return out
def audit(data_root,output):
    configs=json.loads((HERE/'EXPERIMENT_SPECS.json').read_text())['configurations']
    manifest=json.loads((output/'SOURCE_MANIFEST.json').read_text())
    assert subprocess.check_output(['git','-C',str(data_root),'rev-parse','HEAD']).decode().strip()==manifest['data_commit']
    files={name:read(output/(name+'.csv')) for name in ('trades','stop_decisions','entry_opportunities','observed_gaps')}
    saved_open=json.loads((output/'OPEN_POSITIONS.json').read_text());saved_snap=json.loads((output/'PERIOD_END_OPEN_POSITIONS.json').read_text())
    alltrades,allentries,allgaps,allsnaps,allopen=[],[],[],[],[]
    raw_dates={};first_month={};counts=[];fields=0
    for source in manifest['sources']:
        symbol=source['instrument'];path=data_root/source['path'];assert sha(path)==source['full_sha256']
        blob=subprocess.check_output(['git','-C',str(data_root),'hash-object',str(path)]).decode().strip()
        assert blob==source['git_blob_sha']
        raw=prefix(path);assert len(raw)==source['used_candles']
        raw_dates[symbol]=[b['at'] for b in raw];first_month[symbol]=raw[0]['at'].strftime('%Y-%m')
        # Independent recursive indicators; trailing does not affect features.
        rows=derive(raw,configs['BASELINE'])
        for v,p in configs.items():
            for rule in RULES:
                t,o,d,e,g,y=simulate(rows,p,rule,symbol,v)
                selector=lambda r:all(r[k]==value for k,value in [('version',v),('rule',rule),('instrument',symbol)])
                for name,expected in [('trades',t),('stop_decisions',d),('entry_opportunities',e),('observed_gaps',g)]:
                    fields+=compare(expected,[r for r in files[name] if selector(r)],name)
                fields+=compare([o] if o else [],[r for r in saved_open if selector(r)],'OPEN')
                fields+=compare(y,[r for r in saved_snap if selector(r)],'period_OPEN')
                alltrades.extend(t);allentries.extend(e);allgaps.extend(g);allsnaps.extend(y)
                if o:allopen.append(o)
                counts.append({'version':v,'rule':rule,'instrument':symbol,'closed':len(t),'terminal_open':int(o is not None),'entry_decisions':len(e),'stop_decisions':len(d)})
    cal=[f'{year}-{month:02d}' for year in (2023,2024) for month in range(1,13)]
    report_fields=0
    def selected(r,collection,stamp='exit_time'):
        symbols=SYMBOLS if r['scope']=='ALL_FOUR' else (r['scope'],)
        vals=[x for x in collection if x['version']==r['version'] and x['rule']==r['rule'] and x['instrument'] in symbols]
        if r.get('year','ALL')!='ALL':vals=[x for x in vals if x[stamp].year==int(r['year'])]
        if r.get('direction'):vals=[x for x in vals if x['direction']==r['direction']]
        if r.get('month'):vals=[x for x in vals if x[stamp].strftime('%Y-%m')==r['month']]
        return vals
    for name in ('overall_report','instrument_report','yearly_report','direction_report','monthly_report'):
        for r in read(output/(name+'.csv')):
            vals=selected(r,alltrades)
            localcal=[r['month']] if r.get('month') else [m for m in cal if m.startswith(r['year'])] if r.get('year','ALL')!='ALL' else cal
            symbols=SYMBOLS if r['scope']=='ALL_FOUR' else (r['scope'],)
            os=[o for o in (allsnaps if r.get('year','ALL')!='ALL' or r.get('month') else allopen) if o['version']==r['version'] and o['rule']==r['rule'] and o['instrument'] in symbols and (not r.get('direction') or o['direction']==r['direction'])]
            if r.get('month'):os=[o for o in os if o['month']==r['month']]
            elif r.get('year','ALL')!='ALL':os=[o for o in os if o['month']==r['year']+'-12']
            expected=summary(vals,localcal,len(os))
            for k,x in expected.items():check(x,r[k],name+'.'+k);report_fields+=1
            if 'first_available_month' in r:
                first=min(first_month[s] for s in symbols);available=[m for m in cal if m>=first]
                check(first,r['first_available_month'],name+'.first')
                check(len(available),r['covered_calendar_months'],name+'.coverage')
                count=sum(sum(t['gross_R'] for t in vals if t['exit_time'].strftime('%Y-%m')==m)>0 for m in available)
                check(count/len(available),r['positive_share_covered_months'],name+'.covered_share')
            if 'coverage' in r:check('NO_COVERAGE' if r['month']<min(first_month[s] for s in symbols) else 'AVAILABLE',r['coverage'],'monthly.coverage')
    diagnostic_fields=0
    def checks(expected,row,label):
        nonlocal diagnostic_fields
        for k,x in expected.items():check(x,row[k],label+'.'+k);diagnostic_fields+=1
    for r in read(output/'signal_funnel.csv'):
        q=selected(r,allentries,'signal_time')
        checks({'original_signals':len(q),'rule_forbidden_signals':sum(not x['rule_pass'] for x in q),
            'rule_forbidden_when_flat':sum(not x['rule_pass'] and not x['position_occupied'] for x in q),
            'rule_forbidden_and_busy':sum(not x['rule_pass'] and x['position_occupied'] for x in q),
            'accepted_entries':sum(x['entry_accepted'] for x in q),'allowed_skipped_position_busy':sum(x['rule_pass'] and x['position_occupied'] for x in q),
            'all_busy_signals':sum(x['position_occupied'] for x in q),'partition_check':True},r,'funnel')
    for r in read(output/'t1_blocked_hours.csv'):
        q=[e for e in allentries if e['version']==r['version'] and e['rule']=='T1' and (r['scope']=='ALL_FOUR' or e['instrument']==r['scope']) and e['moscow_hour']==int(r['moscow_hour'])]
        checks({'original_signals':len(q),'forbidden':sum(not e['rule_pass'] for e in q),
            'forbidden_flat':sum(not e['rule_pass'] and not e['position_occupied'] for e in q),
            'forbidden_busy':sum(not e['rule_pass'] and e['position_occupied'] for e in q)},r,'T1_hours')
    for r in read(output/'t2_gap_summary.csv'):
        g=selected(r,allgaps,'current_close');e=selected(r,allentries,'signal_time')
        checks({'observed_gaps_gt_15min':sum(x['reason']=='OBSERVED_GAP_GT_15_MIN' for x in g),
            'no_previous_bars':sum(x['previous_close'] is None for x in g),
            'cross_close_date_gaps':sum(x['cross_date'] for x in g),'cross_observed_open_date_gaps':sum(x['cross_observed_open_date'] for x in g),
            'signals_on_first_bar_after_gap':sum(x['original_signal']!=0 and x['previous_close'] is not None for x in g),
            'signals_without_previous':sum(x['original_signal']!=0 and x['previous_close'] is None for x in g),
            'blocked_gap_signals':sum(x['rule_reason']=='FIRST_BAR_AFTER_OBSERVED_GAP' for x in e),
            'blocked_no_previous_signals':sum(x['rule_reason']=='NO_PREVIOUS_OBSERVED_CLOSE' for x in e)},r,'T2_gaps')
    for r in read(output/'november_dependence.csv'):
        vals=selected(r,alltrades);rest=[x for x in vals if x['exit_time'].month!=11];nov=[x for x in vals if x['exit_time'].month==11]
        a=summary(vals,cal[12:],0);b=summary(rest,[m for m in cal[12:] if m!='2024-11'],0)
        checks({'full_PF':a['gross_PF'],'full_R':a['gross_R'],'november_closed':len(nov),'november_R':sum(x['gross_R'] for x in nov),
            'ex_november_closed':len(rest),'ex_november_PF':b['gross_PF'],'ex_november_R':b['gross_R'],
            'ex_november_drawdown_R':b['max_drawdown_closed_R']},r,'november')
    def quantile(vals,fraction):
        if not vals:return None
        vals=sorted(vals);at=(len(vals)-1)*fraction;low=int(at);high=min(low+1,len(vals)-1)
        return vals[low]+(vals[high]-vals[low])*(at-low)
    for r in read(output/'holding_frequency.csv'):
        vals=selected(r,alltrades);es=selected(r,allentries,'signal_time')
        symbols=SYMBOLS if r['scope']=='ALL_FOUR' else (r['scope'],)
        bysymbol=[set(t.date() for t in raw_dates[s] if r['year']=='ALL' or t.year==int(r['year'])) for s in symbols]
        days=sum(len(x) for x in bysymbol);portfolio=len(set().union(*bysymbol));accepted=sum(x['entry_accepted'] for x in es)
        checks({'closed_count':len(vals),'terminal_open_entry_cohort_count':len(selected(r,[o|{'entry_time':datetime.fromisoformat(o['entry_time'])} for o in allopen],'entry_time')),
            'holding_minutes_mean':sum(x['holding_minutes'] for x in vals)/len(vals) if vals else None,
            'holding_minutes_median':quantile([x['holding_minutes'] for x in vals],.5),
            'holding_minutes_p90':quantile([x['holding_minutes'] for x in vals],.9),
            'bars_held_median':quantile([x['bars_held'] for x in vals],.5),'accepted_entries':accepted,
            'observed_instrument_days':days,'observed_portfolio_days':portfolio,
            'entries_per_observed_portfolio_day':accepted/portfolio if portfolio else None,
            'entries_per_observed_instrument_day':accepted/days if days else None,
            'closed_with_observed_overnight_gap':sum(x['observed_overnight_gaps_exposed']>0 for x in vals),
            'closed_with_observed_overnight_gap_share':sum(x['observed_overnight_gaps_exposed']>0 for x in vals)/len(vals) if vals else None,
            'total_observed_overnight_gap_exposures':sum(x['observed_overnight_gaps_exposed'] for x in vals)},r,'holding')
    identity=lambda t:(t['version'],t['instrument'],t['direction'],t['entry_time'])
    originals={identity(t):t for t in alltrades if t['rule']=='CONTROL'}
    for r in read(output/'trade_lineage.csv'):
        k=(r['version'],r['instrument'],r['direction'],datetime.fromisoformat(r['control_entry_time']))
        t=originals[k];match=next((a for a in alltrades if a['rule']==r['rule'] and identity(a)==k),None)
        e=next(a for a in allentries if a['version']==r['version'] and a['rule']==r['rule'] and a['instrument']==r['instrument'] and a['signal_time']==k[-1])
        checks({'control_gross_R':t['gross_R'],'control_winner_ge_2R':t['gross_R']>=2,
            'match_status':'CLOSED_MATCH' if match else 'LOST_ENTRY','variant_trade_id':match['trade_id'] if match else None,
            'variant_gross_R':match['gross_R'] if match else None,'decision_reason':e['decision_reason'],
            'rule_reason':e['rule_reason'],'occupied_trade_id':e['occupied_trade_id'],
            'outcome_preserved':bool(match and abs(match['gross_R']-t['gross_R'])<=1e-8)},r,'lineage')
        if match:assert abs(match['gross_R']-t['gross_R'])<1e-8 and match['exit_time']==t['exit_time']
    known=set(originals)|{(o['version'],o['instrument'],o['direction'],datetime.fromisoformat(o['entry_time'])) for o in allopen if o['rule']=='CONTROL'}
    news=[t for t in alltrades if t['rule']!='CONTROL' and identity(t) not in known]
    saved=read(output/'new_entries.csv');assert len(news)==len(saved)
    for r in saved:
        t=next(t for t in news if t['version']==r['version'] and t['rule']==r['rule'] and t['instrument']==r['instrument'] and t['trade_id']==r['trade_id'])
        diagnostic_fields+=compare([t],[r],'new_entry')
    for r in read(output/'winner_comparison.csv'):
        control=[t for t in alltrades if t['rule']=='CONTROL' and t['version']==r['version'] and (r['scope']=='ALL_FOUR' or t['instrument']==r['scope']) and (r['control_exit_year']=='ALL' or t['exit_time'].year==int(r['control_exit_year']))]
        variant={identity(t):t for t in alltrades if t['rule']==r['rule']}
        lost=[t for t in control if identity(t) not in variant];large=[t for t in control if t['gross_R']>=2]
        new=[t for t in news if t['version']==r['version'] and t['rule']==r['rule'] and (r['scope']=='ALL_FOUR' or t['instrument']==r['scope']) and (r['control_exit_year']=='ALL' or t['exit_time'].year==int(r['control_exit_year']))]
        reasons=[next(e['decision_reason'] for e in allentries if e['version']==r['version'] and e['rule']==r['rule'] and e['instrument']==t['instrument'] and e['signal_time']==t['entry_time']) for t in lost]
        checks({'control_large_winners_ge_2R':len(large),'large_winners_preserved':sum(identity(t) in variant for t in large),
            'large_winners_lost':sum(identity(t) not in variant for t in large),'lost_large_winner_R':sum(t['gross_R'] for t in large if identity(t) not in variant),
            'lost_positive_R':sum(t['gross_R'] for t in lost if t['gross_R']>0),'removed_negative_R_volume':-sum(t['gross_R'] for t in lost if t['gross_R']<0),
            'lost_entry_rule_blocked':sum(x in ('RULE_BLOCKED','RULE_AND_OCCUPIED') for x in reasons),'lost_entry_busy_only':sum(x=='POSITION_OCCUPIED' for x in reasons),
            'new_closed_entries':len(new),'new_closed_losses':sum(t['gross_R']<0 for t in new),
            'new_closed_gross_R':sum(t['gross_R'] for t in new),'new_losses_R_volume':-sum(t['gross_R'] for t in new if t['gross_R']<0)},r,'winners')
    cindex={(e['version'],e['instrument'],e['signal_time']):e for e in allentries if e['rule']=='CONTROL'}
    changes=[e for e in allentries if e['rule']!='CONTROL' and any(e[k]!=cindex[(e['version'],e['instrument'],e['signal_time'])][k] for k in ('entry_accepted','position_occupied'))]
    saved=read(output/'chronology_changes.csv');assert len(saved)==len(changes)
    for r in saved:
        e=next(e for e in changes if all(e[k]==r[k] for k in ('version','rule','instrument')) and e['signal_time']==datetime.fromisoformat(r['signal_time']))
        c=cindex[(e['version'],e['instrument'],e['signal_time'])]
        checks({'control_accepted':c['entry_accepted'],'variant_accepted':e['entry_accepted'],
            'control_busy':c['position_occupied'],'variant_busy':e['position_occupied'],'variant_rule_pass':e['rule_pass'],
            'variant_reason':e['decision_reason'],'control_occupied_trade_id':c['occupied_trade_id'],
            'variant_occupied_trade_id':e['occupied_trade_id']},r,'chronology')
    for r in read(output/'top_winners.csv'):
        vals=selected(r,alltrades)
        vals=sorted([t for t in vals if t['gross_R']>0],key=lambda t:(-t['gross_R'],t['instrument'],t['trade_id']))[:int(r['top_n'])]
        t=vals[int(r['rank'])-1]
        checks({k:t[k] for k in ('instrument','trade_id','entry_time','exit_time','gross_R')},r,'top_winners')
    expected_runs=[]
    for v in configs:
        for rule in RULES:
            for scope in ('ALL_FOUR',*SYMBOLS):
                vals=selected({'version':v,'rule':rule,'scope':scope},alltrades)
                totals={m:sum(t['gross_R'] for t in vals if t['exit_time'].strftime('%Y-%m')==m) for m in cal}
                run=[]
                for m,x in list(totals.items())+[('END',0)]:
                    if x<0:run.append(m)
                    elif run:
                        expected_runs.append({'version':v,'rule':rule,'scope':scope,'first_month':run[0],'last_month':run[-1],'months':len(run),'gross_R':sum(totals[x] for x in run)})
                        run=[]
    diagnostic_fields+=compare(expected_runs,read(output/'losing_month_runs.csv'),'month_runs')
    expected_equity=[]
    for v in configs:
        for rule in RULES:
            vals=sorted(selected({'version':v,'rule':rule,'scope':'ALL_FOUR'},alltrades),key=lambda t:(t['exit_time'],t['instrument'],t['trade_id']))
            total=peak=0.
            for t in vals:
                total+=t['gross_R'];peak=max(peak,total)
                expected_equity.append({'version':v,'rule':rule,'scope':'ALL_FOUR','exit_time':t['exit_time'],'instrument':t['instrument'],
                    'trade_id':t['trade_id'],'trade_R':t['gross_R'],'cumulative_closed_R':total,'drawdown_R':peak-total})
    diagnostic_fields+=compare(expected_equity,read(output/'closed_equity.csv'),'closed_equity')
    objective=json.loads((output/'OBJECTIVE_ASSESSMENT.json').read_text())
    for r in objective['rows']:
        vals=selected({'version':r['version'],'rule':r['rule'],'scope':'ALL_FOUR'},alltrades)
        control=selected({'version':r['version'],'rule':'CONTROL','scope':'ALL_FOUR'},alltrades)
        a=summary(vals,cal,0);c=summary(control,cal,0)
        checks({k:a[k] for k in ('gross_PF','gross_R','closed_trades','positive_months','negative_months','max_drawdown_closed_R')}|
            {'full_PF_ge_2':a['gross_PF']>=2,'positive_months_improved':a['positive_months']>c['positive_months'],
            'delta_gross_R':a['gross_R']-c['gross_R'],'delta_drawdown_R':a['max_drawdown_closed_R']-c['max_drawdown_closed_R'],
            'delta_closed':a['closed_trades']-c['closed_trades']},r,'objective')
    for name,value in json.loads((output/'GENERATED_SHA256.json').read_text()).items():assert sha(output/name)==value
    result={'status':'PASS','independent_implementation':'stdlib timestamp-first parser / recursive indicators / slice extrema / separate gating and summary',
        'same_author':True,'external_audit':'PENDING','journal_fields_compared':fields,'report_fields_compared':report_fields,
        'diagnostic_fields_compared':diagnostic_fields,'numeric_absolute_tolerance':1e-8,'maximum_differences':DELTAS,
        'replays':counts,'future_OHLC_parsed':False,'generated_SHA256':'PASS'}
    (HERE/'AUDIT_RESULTS.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('status','journal_fields_compared','report_fields_compared','diagnostic_fields_compared')},sort_keys=True))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True);p.add_argument('--output',type=Path,default=HERE/'results')
    a=p.parse_args();audit(a.data_root,a.output)
