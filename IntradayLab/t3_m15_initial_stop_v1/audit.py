"""Independent standard-library initial-stop replay and report audit.

Does not import the experiment engine/research implementation. Reuses only the
frozen PR #490 independent byte parser and recursive smoother. Same author;
external audit independence remains pending.
"""
import argparse
import csv
from datetime import datetime, timedelta
import importlib.util
import json
import math
import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
FROZEN = HERE.parent/'t3_m15_forever_v1'
spec = importlib.util.spec_from_file_location('independent_frozen_parser',FROZEN/'audit.py')
A = importlib.util.module_from_spec(spec)
spec.loader.exec_module(A)
RULES = ('CONTROL','I1','I2','I3')
SYMBOLS = ('USDRUBF','CNYRUBF','GLDRUBF','IMOEXF')
DELTAS = {}
RAW_CALENDARS = {}


def read(p):
    with p.open() as f:return list(csv.DictReader(f))


def check(value,saved,label):
    if value is None:
        assert saved in ('',None),(label,value,saved)
    elif isinstance(value,bool):
        assert saved == value or saved == str(value),(label,value,saved)
    elif isinstance(value,datetime):
        assert value == datetime.fromisoformat(saved),(label,value,saved)
    elif isinstance(value,str):
        assert value == saved,(label,value,saved)
    else:
        difference = abs(value-float(saved))
        DELTAS[label] = max(DELTAS.get(label,0.),difference)
        assert math.isfinite(difference) and difference <= 1e-8,(label,value,saved,difference)


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
    atr = A.smooth(ranges(raw),1/p['atr_period'],p['atr_period'])
    ha = A.smooth(ranges(high),1/p['atr_period'],p['atr_period'])
    ema = A.smooth([b['c'] for b in high],2/(p['ema_period']+1),p['ema_period'])
    plus,minus = [0.],[0.]
    for a,b in zip(high,high[1:]):
        up,down = b['h']-a['h'],a['l']-b['l']
        plus.append(up if up > down and up > 0 else 0.)
        minus.append(down if down > up and down > 0 else 0.)
    plus = A.smooth(plus,1/p['adx_period'],p['adx_period'])
    minus = A.smooth(minus,1/p['adx_period'],p['adx_period'])
    adx = A.smooth([100*abs(a-b)/(a+b) if a is not None and b is not None and a+b > 0 else None for a,b in zip(plus,minus)],1/p['adx_period'],p['adx_period'])
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


def tick_size(symbol,at):
    if symbol=='CNYRUBF':return .01 if at.isoformat()<'2023-09-27T19:00:00+03:00' else .001
    return {'USDRUBF':.01,'GLDRUBF':.1,'IMOEXF':.5}[symbol]


def entry_features(b):
    h,old=b['h1'],b['previous_h1']
    return {'ATR':b['atr'],'PreviousATR':b['previous_atr'],'H1ADX':h['adx'],'H1PreviousADX':old['adx'],
        'H1Slope':h['slope'],'H1PreviousSlope':old['slope'],'H1ATRRatio':h['ratio'],'H1PreviousATRRatio':old['ratio'],
        'H1AvailableAt':h['at'],'H1PreviousAvailableAt':old['at'],
        'signal_open':b['o'],'signal_high':b['h'],'signal_low':b['l']}


def simulate(rows,p,rule,symbol,version):
    """Different state representation; reconstruct extrema from historical slices."""
    trades,decisions,entries,snapshots,position=[],[],[],[],None
    ids={'version':version,'rule':rule,'instrument':symbol}
    alias={'USDRUBF':'Si','CNYRUBF':'CNY'}.get(symbol,symbol)
    def opened(q,b):
        if q is None:return None
        s,entry,risk=q['side'],rows[q['start']]['c'],q['risk']
        return ids | {'trade_id':q['id'],'direction':'LONG' if s==1 else 'SHORT',
            'entry_time':rows[q['start']]['at'],'entry_price':entry,'initial_stop':q['initial'],'initial_risk':risk,
            'active_stop':q['active'],'breakout_level':q['level'],'ATR':rows[q['start']]['atr'],
            'reference_2ATR_risk':q['reference'],'entry_exchange_tick':q['tick'],'initial_risk_exchange_ticks':risk/q['tick'],
            'last_close':b['at'],'last_close_price':b['c'],'unrealized_gross_R_at_last_close':s*(b['c']-entry)/risk,
            'unrealized_reference_2ATR_R':s*(b['c']-entry)/q['reference'],
            'status':'OPEN_NOT_LIQUIDATED_EXCLUDED_FROM_CLOSED_TRADE_METRICS'}
    for i,b in enumerate(rows):
        if i and rows[i-1]['at'].year!=b['at'].year and position:
            snapshots.append(opened(position,rows[i-1]) | {'year':rows[i-1]['at'].year})
        if position:
            q=position
            start,s,active=q['start'],q['side'],q['active']
            entry=rows[start]['c'];risk=q['risk'];initial=q['initial']
            path=rows[start+1:i]
            lo=min([entry]+[x['l'] for x in path]);hi=max([entry]+[x['h'] for x in path])
            extreme=hi if s==1 else lo
            opening=b['at']-timedelta(minutes=15)
            at_open=b['o']<=active if s==1 else b['o']>=active
            hit=at_open or (b['l']<=active if s==1 else b['h']>=active)
            d=ids | {'trade_id':q['id'],'bar_open_time':opening,'bar_close_time':b['at'],
                'active_stop':active,'initial_risk':risk,'extreme_before':extreme,'open':b['o'],'high':b['h'],
                'low':b['l'],'ATR_at_close':b['atr'],'stop_hit':hit,'stop_gap':bool(at_open and b['o']!=active)}
            if hit:
                fill=b['o'] if at_open else active
                profit=s*(fill-entry)
                trades.append(ids | {'trade_id':q['id'],'direction':'LONG' if s==1 else 'SHORT',
                    'entry_time':rows[start]['at'],'entry_price':entry,'initial_stop':initial,'initial_risk':risk,
                    'breakout_level':q['level'],'exit_time':b['at'],'exit_bar_open_time':opening,'exit_bar_close_time':b['at'],
                    'exit_price':fill,'gross_R':profit/risk,'gross_price_pnl':profit,'reference_2ATR_risk':q['reference'],
                    'reference_2ATR_R':profit/q['reference'],'entry_exchange_tick':q['tick'],'initial_risk_exchange_ticks':risk/q['tick'],
                    'initial_risk_ATR':risk/rows[start]['atr'],
                    'exit_type':'INITIAL_STOP' if active==initial else 'RATCHETED_STOP',
                    'active_stop_at_exit':active,'trailing_updates':q['updates'],'gap_exit':bool(fill!=active),
                    'exit_at_open':at_open,'rule_decision_time':None,'rule_stop_conflict_at_open':False,'bars_held':i-start,
                    'holding_minutes':(b['at']-rows[start]['at']).total_seconds()/60,
                    'MAE_R':max(0.,entry-lo if s==1 else hi-entry,s*(entry-fill))/risk,
                    'MFE_R':max(0.,hi-entry if s==1 else entry-lo)/risk,
                    'cross_calendar_day':b['at'].date()!=rows[start]['at'].date(),'year':b['at'].year,
                    **entry_features(rows[start])})
                d.update(phase='EXIT',exit_price=fill,extreme_after=None,trail_proposal=None,
                    active_stop_next_bar=None,trailing_changed=False)
                position=None
            else:
                new_extreme=max(extreme,b['h']) if s==1 else min(extreme,b['l'])
                proposal=new_extreme-s*p['trail_atr']*b['atr']
                next_stop=max(active,proposal) if s==1 else min(active,proposal)
                changed=next_stop!=active
                q['updates']+=int(changed);q['active']=next_stop
                d.update(phase='SURVIVED',exit_price=None,extreme_after=new_extreme,trail_proposal=proposal,
                    active_stop_next_bar=next_stop,trailing_changed=changed)
            decisions.append(d)
        if b['signal']:
            s=b['signal'];entry=b['c'];reference=2*b['atr']
            base_stop=entry-s*reference
            extreme=b['l'] if s==1 else b['h']
            stop={'CONTROL':base_stop,'I1':extreme,'I2':b['upper'] if s==1 else b['lower'],
                'I3':sorted([base_stop,extreme])[1 if s==1 else 0]}[rule]
            risk=abs(entry-stop)
            valid=math.isfinite(risk) and risk>0 and math.isfinite(entry) and math.isfinite(stop)
            reason='NONFINITE_INITIAL_RISK' if not math.isfinite(risk) else 'NONPOSITIVE_INITIAL_RISK' if risk<=0 else 'VALID'
            occupied=position is not None;accepted=valid and not occupied
            outcome='POSITION_OCCUPIED' if occupied else 'ACCEPTED' if valid else reason
            etick=tick_size(symbol,b['at'])
            tid=f'T3-M15-{alias}-{len(trades)+1:06d}' if accepted else None
            entries.append(ids | {'signal_time':b['at'],'direction':'LONG' if s==1 else 'SHORT',
                'entry_price':entry,'candidate_initial_stop':stop,'candidate_initial_risk':risk,'ATR':b['atr'],
                'reference_2ATR_risk':reference,'entry_exchange_tick':etick,'candidate_risk_exchange_ticks':risk/etick,
                'signal_open':b['o'],'signal_high':b['h'],'signal_low':b['l'],'PriorHigh':b['upper'],'PriorLow':b['lower'],
                'H1AvailableAt':b['h1']['at'],'initial_stop_valid':valid,'validity_reason':reason,
                'position_occupied':occupied,'occupied_trade_id':position['id'] if occupied else None,
                'entry_accepted':accepted,'outcome':outcome,'trade_id':tid})
            if accepted:position={'start':i,'side':s,'initial':stop,'active':stop,'risk':risk,'reference':reference,
                'tick':etick,'id':tid,'level':b['upper'] if s==1 else b['lower'],'updates':0}
    op=opened(position,rows[-1])
    if op:snapshots.append(op | {'year':rows[-1]['at'].year})
    return trades,op,decisions,entries,snapshots


def summary(rows,calendar,column,opened_count):
    rows=sorted(rows,key=lambda r:(r['exit_time'],r['instrument'],r['trade_id']))
    vals=[r[column] for r in rows]
    plus=sum(x for x in vals if x>0);minus=-sum(x for x in vals if x<0)
    months={m:sum(r[column] for r in rows if r['exit_time'].strftime('%Y-%m')==m) for m in calendar}
    total=peak=dd=0.;streak=longest=0
    for x in vals:
        total+=x;peak=max(peak,total);dd=max(dd,peak-total)
        streak=streak+1 if x<0 else 0;longest=max(longest,streak)
    worst=min(months,key=months.get) if months else None
    out={'closed_trades':len(rows),'open_positions_at_period_end':opened_count,
        'gross_PF':plus/minus if minus else None,'gross_R':sum(vals),'expectancy_R':sum(vals)/len(vals) if vals else None,
        'positive_R':plus,'negative_R_volume':minus,'max_drawdown_closed_R':dd,'max_consecutive_losses':longest,
        'calendar_months':len(calendar),'positive_months':sum(x>0 for x in months.values()),
        'negative_months':sum(x<0 for x in months.values()),'zero_months':sum(x==0 for x in months.values()),
        'no_closed_trade_months':sum(not any(r['exit_time'].strftime('%Y-%m')==m for r in rows) for m in calendar),
        'worst_month':worst,'worst_month_R':months.get(worst),'win_rate':sum(x>0 for x in vals)/len(vals) if vals else None}
    for sign in ('positive','negative','zero'):out[sign+'_month_share']=out[sign+'_months']/len(calendar) if calendar else None
    for n in (5,10):
        top=sum(sorted([x for x in vals if x>0],reverse=True)[:n])
        out.update({f'top{n}_positive_R':top,f'top{n}_share_positive_R':top/plus if plus else None,
            f'gross_R_without_top{n}':sum(vals)-top,f'gross_PF_without_top{n}':(plus-top)/minus if minus else None})
    return out


def compare_rows(expected,saved,label):
    assert len(expected)==len(saved),(label,len(expected),len(saved))
    count=0
    for i,(a,b) in enumerate(zip(expected,saved)):
        assert set(a)==set(b),(label,'FIELD_SET',set(a)^set(b))
        for field,value in a.items():check(value,b[field],label+'.'+field);count+=1
    return count


def main(data_root,output):
    configs=json.loads((HERE/'EXPERIMENT_SPECS.json').read_text())['configurations']
    manifest=json.loads((output/'SOURCE_MANIFEST.json').read_text())
    assert subprocess.check_output(['git','-C',str(data_root),'rev-parse','HEAD']).decode().strip()==manifest['data_commit']
    expected_trades,expected_entries,expected_decisions,expected_open,expected_year=[],[],[],[],[]
    counts=[]
    for src in manifest['sources']:
        path=data_root/src['path'];assert A.sha(path)==src['full_sha256']
        blob=subprocess.check_output(['git','-C',str(data_root),'hash-object','--',str(path)]).decode().strip()
        assert blob==src['git_blob_sha']
        digest=hashlib.sha256()
        with path.open('rb') as stream:
            digest.update(stream.readline())
            while True:
                prefix=bytearray()
                while prefix.count(b';')<2:
                    char=stream.read(1)
                    if not char:break
                    prefix+=char
                if not prefix:break
                if prefix.decode().split(';')[1]>='2025-01-01':break
                digest.update(prefix+stream.readline())
        assert digest.hexdigest()==src['historical_prefix_sha256']
        raw=A.prefix(path);assert len(raw)==src['used_candles']
        assert raw[0]['at'].isoformat()==src['first_close'] and raw[-1]['at'].isoformat()==src['last_close']
        RAW_CALENDARS[src['instrument']]=raw[0]['at'].strftime('%Y-%m')
        for v,p in configs.items():
            derived=derive(raw,p)
            for rule in RULES:
                t,o,d,e,y=simulate(derived,p,rule,src['instrument'],v)
                expected_trades.extend(t);expected_entries.extend(e);expected_decisions.extend(d);expected_year.extend(y)
                if o:expected_open.append(o)
                counts.append({'version':v,'rule':rule,'instrument':src['instrument'],'closed':len(t),'open':int(o is not None)})
    expected_trades.sort(key=lambda r:(r['version'],r['rule'],r['exit_time'],r['instrument'],r['trade_id']))
    saved_trades=read(output/'trades.csv')
    # Journals use CONTROL first, then I1/I2/I3, with version and symbol loops.
    sortkey=lambda r:(RULES.index(r['rule']),r['version'],SYMBOLS.index(r['instrument']),r['signal_time'] if 'signal_time' in r else r['bar_close_time'])
    expected_entries.sort(key=sortkey);expected_decisions.sort(key=sortkey)
    saved_entries=sorted(read(output/'entry_opportunities.csv'),key=sortkey)
    saved_decisions=sorted(read(output/'stop_decisions.csv'),key=sortkey)
    field_counts={'trades':compare_rows(expected_trades,saved_trades,'trade'),
        'entries':compare_rows(expected_entries,saved_entries,'entry'),
        'stops':compare_rows(expected_decisions,saved_decisions,'stop')}
    openkey=lambda r:(r['version'],r['rule'],r['instrument'],r.get('year',0))
    field_counts['terminal_open']=compare_rows(sorted(expected_open,key=openkey),sorted(json.loads((output/'OPEN_POSITIONS.json').read_text()),key=openkey),'open')
    field_counts['year_end_open']=compare_rows(sorted(expected_year,key=openkey),sorted(json.loads((output/'YEAR_END_OPEN_POSITIONS.json').read_text()),key=openkey),'year_open')
    calendar=[f'{y}-{m:02}' for y in (2023,2024) for m in range(1,13)]
    report_fields=0
    for file in ('overall_report.csv','yearly_report.csv','direction_report.csv','monthly_report.csv','instrument_report.csv'):
        for r in read(output/file):
            selected=[t for t in expected_trades if t['version']==r['version'] and t['rule']==r['rule'] and (r['scope']=='ALL_FOUR' or t['instrument']==r['scope'])]
            os=[o for o in expected_open if o['version']==r['version'] and o['rule']==r['rule'] and (r['scope']=='ALL_FOUR' or o['instrument']==r['scope'])]
            cal=calendar
            if r.get('year','ALL')!='ALL':
                year=int(r['year']);selected=[t for t in selected if t['exit_time'].year==year];cal=[m for m in calendar if m.startswith(str(year))]
                os=[o for o in expected_year if o['version']==r['version'] and o['rule']==r['rule'] and (r['scope']=='ALL_FOUR' or o['instrument']==r['scope']) and o['year']==year]
            if 'direction' in r:selected=[t for t in selected if t['direction']==r['direction']];os=[o for o in os if o['direction']==r['direction']]
            if 'month' in r:selected=[t for t in selected if t['exit_time'].strftime('%Y-%m')==r['month']];cal=[r['month']];os=[]
            col='gross_R' if r['normalization']=='ACTUAL_INITIAL_RISK' else 'reference_2ATR_R'
            for k,value in summary(selected,cal,col,len(os)).items():check(value,r[k],file+'.'+k);report_fields+=1
            if 'first_available_month' in r:
                first=min(RAW_CALENDARS.values()) if r['scope']=='ALL_FOUR' else RAW_CALENDARS[r['scope']]
                covered=[m for m in calendar if m>=first]
                for k,value in {'first_available_month':first,'covered_calendar_months':len(covered),
                    'positive_share_covered_months':sum(sum(t[col] for t in selected if t['exit_time'].strftime('%Y-%m')==m)>0 for m in covered)/len(covered)}.items():check(value,r[k],file+'.'+k);report_fields+=1
            if 'coverage' in r:
                first=min(RAW_CALENDARS.values()) if r['scope']=='ALL_FOUR' else RAW_CALENDARS[r['scope']]
                check('NO_COVERAGE' if r['month']<first else 'AVAILABLE',r['coverage'],file+'.coverage')
    from audit_diagnostics import audit_diagnostics
    diagnostic_fields=audit_diagnostics(expected_trades,expected_entries,expected_open,output,check,summary,calendar)
    result={'status':'PASS','method':'Second standard-library implementation from raw permitted prefixes; no experiment engine/research/diagnostics imports',
        'independence':'Algorithmic independence; same author. External audit pending.','field_counts':field_counts,
        'report_fields':report_fields,'diagnostic_fields':diagnostic_fields,'replays':counts,'maximum_numeric_deltas':DELTAS,
        'future_OHLC_parsed':False,'all_source_hashes_verified':True}
    (HERE/'AUDIT_RESULTS.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'audit':'PASS','journal_fields':sum(field_counts.values()),'report_fields':report_fields,'diagnostic_fields':diagnostic_fields}))

if __name__=='__main__':
    import subprocess
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True);p.add_argument('--output',type=Path,default=HERE/'results')
    a=p.parse_args();main(a.data_root,a.output)
