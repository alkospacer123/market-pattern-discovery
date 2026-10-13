"""Reproducible GROSS_ONLY 2026 YTD OOS, never a completed 2026 year.

Uses the frozen, unmodified PR512 primary and scalar engines. Reads strictly
completed M15 candles before the predeclared cutoff, and checks the complete
2023-2025 published journals before any 2026 performance is accepted.
No network, broker, fees, parameter search, LIVE, or TradingSystemLab imports.
"""
import argparse
import csv
from datetime import datetime, timedelta
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
FROZEN = ROOT / 'IntradayLab/t3_m15_a6_s1_walk_forward_2025_v1'
sys.path.insert(0, str(FROZEN))
import pandas as pd
import common as C
import engine as E
import scalar as S
import control as G
import integrity as F

MOSCOW = ZoneInfo('Europe/Moscow')
YEAR_START = datetime(2026, 1, 1, tzinfo=MOSCOW)
CUTOFF = datetime(2026, 10, 13, tzinfo=MOSCOW)
STEP = timedelta(minutes=15)
PIN = 'f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8'
REFERENCE = FROZEN / 'results/W4'
FIELDS = ('Open','High','Low','Close','Volume')

def frozen_json(x):
    return json.dumps(C.plain(x), sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + '\n'

def emit(path,obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(frozen_json(obj),encoding='utf-8')

def assert_source_checkout(root):
    assert root.is_dir(), 'MISSING_MARKET_DATA_CHECKOUT'
    rev = subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
    assert rev == PIN, ('WRONG_DATA_COMMIT',rev)
    spec=json.loads((FROZEN/'SPEC.json').read_text(encoding='utf-8'))
    assert tuple(x['instrument'] for x in spec['sources']) == C.SYMBOLS
    for entry in spec['sources']:
        path=entry['path']
        assert path==f"forever/{entry['instrument']}/{entry['instrument']}_M15.csv",('BAD_SOURCE',path)
        blob=subprocess.check_output(['git','-C',str(root),'rev-parse',PIN+':'+path],text=True).strip()
        assert blob==entry['git_blob_sha'],('SOURCE_BLOB_PIN_MISMATCH',path)
        assert (root/path).is_file(),('MISSING_SOURCE',path)
    return spec['sources']

def parse_file(file,cutoff,mode):
    """FileIO(unbuffered): read timestamp before OHLCV; never decode excluded OHLCV.

    Two independent timestamp parsers, with the same cutoff contract. Reading
    the first excluded timestamp is allowed only to establish the boundary.
    """
    assert mode in ('primary','scalar') and YEAR_START<cutoff<=CUTOFF
    sha=hashlib.sha256();rows=[];last=None;reason='EOF'
    with open(file,'rb',buffering=0) as f:
        header=f.readline()
        assert header==b'Ticker;Datetime;Open;High;Low;Close;Volume\n'
        sha.update(header)
        while True:
            sym=bytearray()
            while True:
                char=f.read(1)
                if not char: break
                sym.extend(char)
                if char==b';':break
                assert len(sym)<30, 'BAD_TICKER_PREFIX'
            if not sym:break
            assert sym[-1:]==b';','TRUNCATED_TICKER'
            stamp=bytearray()
            while True:
                unit=f.read(1)
                assert unit,'TRUNCATED_TIMESTAMP'
                if unit==b';':break
                stamp+=unit
                assert len(stamp)<=20,'BAD_TIMESTAMP'
            if mode=='primary':
                opening=datetime.strptime(stamp.decode('ascii'),'%Y-%m-%d %H:%M:%S').replace(tzinfo=MOSCOW)
            else:
                opening=datetime.fromisoformat(stamp.decode('ascii')).replace(tzinfo=MOSCOW)
            at=opening+STEP
            if at>=cutoff:
                reason='FIRST_COMPLETION_OUTSIDE_AUTHORIZED_CUTOFF'
                break
            assert opening>=datetime(2023,1,1,tzinfo=MOSCOW),'BEFORE_DEVELOPMENT'
            assert last is None or opening>last,'UNSORTED_OR_DUPLICATE_BAR'
            assert opening.minute%15==0 and opening.second==0,'BAD_CLOCK_GRID'
            numeric=f.readline()
            assert numeric.endswith(b'\n'), 'TRUNCATED_OHLCV'
            if mode=='primary':
                values=tuple(float(x) for x in numeric.rstrip(b'\r\n').split(b';'))
            else:
                columns=numeric.decode('ascii').rstrip('\r\n').split(';')
                values=tuple(map(float,columns))
            assert len(values)==5 and all(math.isfinite(x) for x in values),'BAD_FLOAT'
            o,h,l,c,v=values
            assert h>=max(o,l,c) and l<=min(o,h,c),'BAD_OHLC'
            rows.append((at,*values))
            sha.update(sym+stamp+b';'+numeric)
            last=opening
        receipt={'reader':mode,'source':str(file),'cutoff_end_exclusive':cutoff.isoformat(),
                 'used_candles':len(rows),'first_close':rows[0][0] if rows else None,
                 'last_close':rows[-1][0] if rows else None,'prefix_sha256':sha.hexdigest(),
                 'bytes_consumed':f.tell(),'excluded_OHLCV_decoded':False,
                 'stop_reason':reason,'buffered_read_ahead':False}
    if mode=='primary':
        frame=pd.DataFrame([v[1:] for v in rows],index=pd.DatetimeIndex([v[0] for v in rows],name='CloseTime'),columns=FIELDS)
        return frame,receipt
    bars=[dict(at=x[0],o=x[1],h=x[2],l=x[3],c=x[4],v=x[5]) for x in rows]
    return bars,receipt

def compute(root,sources,end):
    C.END=end
    S.END=end   # Scalar imports END at module load; adjust only the run horizon.
    frames={};scalars={};receipts=[]
    for entry in sources:
        symbol=entry['instrument'];path=root/entry['path']
        pf,rec=parse_file(path,end,'primary')
        sb,srec=parse_file(path,end,'scalar')
        assert len(pf)==len(sb),('READER_ROW_COUNT',symbol)
        assert rec['prefix_sha256']==srec['prefix_sha256'],('READER_PREFIX_DIFFERENCE',symbol)
        assert len(pf)>0,('EMPTY_SOURCE',symbol)
        frames[symbol]=E.features(pf)
        scalars[symbol]=C.build_features(sb)
        receipts.append(dict(rec,instrument=symbol,git_blob_sha=entry['git_blob_sha'],
                             data_commit=PIN,scalar_prefix_sha256=srec['prefix_sha256']))
    primary=G.compute(frames,['TRAIL_375'])
    independent=G.compute(scalars,['TRAIL_375'],scalar=True)
    return frames,primary,independent,receipts

def journal_subset(out,which,end,ignore=None):
    ignore=ignore or set()
    date_field={'trades':'exit_time','stop_decisions':'bar_close_time',
                'entry_opportunities':'signal_time','observed_gaps':'current_close',
                'PERIOD_END_OPEN_POSITIONS':'month'}
    if which=='OPEN_POSITIONS':return list(out[which])
    result=[]
    for row in out[which]:
        when=row[date_field[which]]
        if which=='PERIOD_END_OPEN_POSITIONS':
            if when>=end.strftime('%Y-%m'):continue
        elif when>=end:continue
        if which=='entry_opportunities' and (row['instrument'],row['signal_time']) in ignore:continue
        result.append(row)
    return result

def validate_against_wf(out,label,reference=REFERENCE):
    """Directly compare published merged #512 W4 ledgers, not just summary PF."""
    assert reference.is_dir(),'FROZEN_WF_RESULTS_NOT_MOUNTED'
    cmp=C.Comparison()
    from csv import DictReader
    dates=['trades','stop_decisions','entry_opportunities','observed_gaps','PERIOD_END_OPEN_POSITIONS','OPEN_POSITIONS']
    keys={'trades':['instrument','trade_id'],'OPEN_POSITIONS':['instrument','trade_id'],
          'stop_decisions':['instrument','bar_close_time','trade_id'],
          'entry_opportunities':['instrument','signal_time'],
          'observed_gaps':['instrument','current_close'],
          'PERIOD_END_OPEN_POSITIONS':['instrument','month','trade_id']}
    ignore=set()
    ref_entries=list(DictReader((reference/label/'entry_opportunities.csv').open(newline='')))
    for row in ref_entries:
        if row.get('pending_at_end')=='True':
            ignore.add((row['instrument'],datetime.fromisoformat(row['signal_time'])))
    for name in dates:
        ref_path=reference/label/(name+('.json' if 'POSITIONS' in name else '.csv'))
        assert ref_path.is_file(),('MISSING_WF_JOURNAL',name)
        if 'POSITIONS' in name:
            ref=json.loads(ref_path.read_text())
        else:
            with ref_path.open(newline='') as stream:ref=list(DictReader(stream))
        subset=journal_subset(out,name,YEAR_START,ignore if name=='entry_opportunities' else set())
        if name=='entry_opportunities':ref=[r for r in ref if r.get('pending_at_end')!='True']
        fields=set(k for row in ref for k in row)
        subset=[{k:r.get(k) for k in fields} for r in subset]
        cmp.rows(subset,ref,'WF2025_'+name,keys[name])
    assert not cmp.diffs,('WF_2025_PREFIX_MISMATCH',cmp.diffs[:4])
    return {'status':'PASS','fields_compared':cmp.fields,'differences':0}

def metrics(rows):
    r=[float(x['gross_R']) for x in rows]
    wins=[x for x in r if x>0];loss=[x for x in r if x<0]
    w=sum(wins);l=abs(sum(loss))
    ordered=sorted(rows,key=lambda a:(a['exit_time'],a['instrument'],a['trade_id']))
    balance=0.;peak=0.;dd=0.
    for row in ordered:
        balance+=float(row['gross_R'])
        peak=max(peak,balance);dd=max(dd,peak-balance)
    return {'closed':len(r),'wins':len(wins),'losses':len(loss),'gross_R':sum(r),
            'gross_PF':w/l if l else None,'expectancy_R':sum(r)/len(r) if r else None,
            'avg_win_R':w/len(wins) if wins else None,
            'avg_loss_R':-l/len(loss) if loss else None,'closed_R_drawdown':dd}

def present(out,frames,end):
    closed=[r for r in out['trades'] if YEAR_START<=r['exit_time']<end]
    new=[r for r in closed if YEAR_START<=r['signal_time']<end and YEAR_START<=r['entry_time']<end]
    inherited=[r for r in closed if r not in new]
    new_open=[r for r in out['OPEN_POSITIONS'] if YEAR_START<=r['signal_time']<end and YEAR_START<=r['entry_time']<end]
    inherited_open=[r for r in out['OPEN_POSITIONS'] if r not in new_open]
    months=[f'2026-{m:02d}' for m in range(1,end.month+1)]
    monthly=[]
    for month in months:
        trades=[r for r in closed if r['exit_time'].strftime('%Y-%m')==month]
        coverage=[]
        for symbol,frame in frames.items():
            n=int(sum(at.strftime('%Y-%m')==month for at in frame.index))
            coverage.append({'instrument':symbol,'bars':n,'coverage':'AVAILABLE' if n else 'NO_COVERAGE'})
        monthly.append({'month':month,**metrics(trades),'coverage':coverage})
    slices=[]
    for symbol in ('ALL_FOUR',*C.SYMBOLS):
        for side in ('ALL','LONG','SHORT'):
            t=[r for r in closed if (symbol=='ALL_FOUR' or r['instrument']==symbol) and (side=='ALL' or r['direction']==side)]
            slices.append({'scope':symbol,'direction':side,**metrics(t)})
    complete_months=sum(any(x['bars'] for x in r['coverage']) for r in monthly)
    last_close=max((f.index[-1] for f in frames.values() if len(f)),default=None)
    base=metrics(closed)
    positive=[x for x in monthly if x['gross_R']>0 and any(v['bars'] for v in x['coverage'])]
    negative=[x for x in monthly if x['gross_R']<0 and any(v['bars'] for v in x['coverage'])]
    return {'status':'OOS_2026_YTD_RESEARCH_ONLY',
            'gross_only':True,'commission_included':False,'spread_slippage_included':False,
            'candidate':'A6+S1 / T3 M15 / NEXT_OPEN / TRAIL_375',
            'data_cutoff_end_exclusive':end,'last_available_bar_close':last_close,
            'calendar_complete':False,'coverage_months_with_any_M15_bars':complete_months,
            'positive_months':len(positive),'negative_months':len(negative),
            'calendar_CLOSED':base,'new_2026_entry_CLOSED':metrics(new),
            'inherited_pre_2026_CLOSED':metrics(inherited),
            'new_2026_terminal_OPEN':new_open,'inherited_terminal_OPEN':inherited_open,
            'all_terminal_OPEN':out['OPEN_POSITIONS'],'monthly':monthly,'slices':slices,
            'full_year_OOS_claim':False,'LIVE_authorized':False}

def run(data_root,output,end):
    assert YEAR_START<end<=CUTOFF,'UNAUTHORIZED_DATE_RANGE'
    assert data_root.resolve()!=output.resolve()
    sources=assert_source_checkout(data_root)
    assert F.freeze_guard()['before_any_WF_2025_read'],'FROZEN_BASELINE_GUARD'
    output.mkdir(parents=True,exist_ok=True)
    old_frames,old_p,old_s,old_receipts=compute(data_root,sources,YEAR_START)
    # Frozen 2025 WF closes exactly at midnight 2026. No 2026 OHLC read here.
    assert validate_against_wf(old_p,'primary')['status']=='PASS'
    assert validate_against_wf(old_s,'scalar')['status']=='PASS'
    current_frames,p,s,receipts=compute(data_root,sources,end)
    for lbl,result in [('primary',p),('scalar',s)]:
        emit(output/(lbl+'_causality.json'),F.causal(result))
    cmp=C.Comparison()
    keys={'trades':['instrument','trade_id'],'OPEN_POSITIONS':['instrument','trade_id'],
          'stop_decisions':['instrument','bar_close_time','trade_id'],
          'entry_opportunities':['instrument','signal_time'],
          'observed_gaps':['instrument','current_close'],
          'PERIOD_END_OPEN_POSITIONS':['instrument','month','trade_id']}
    for name in G.NAMES:
        fields=set(k for r in p[name]+s[name] for k in r)
        cmp.rows([{k:r.get(k) for k in fields} for r in p[name]],
                 [{k:r.get(k) for k in fields} for r in s[name]],
                 'INDEPENDENT_'+name,keys[name])
    assert not cmp.diffs,('PRIMARY_SCALAR_MISMATCH',cmp.diffs[:4])
    # Prior to 2026, all completed journal entries and features must be exact.
    pending={(r['instrument'],r['signal_time']) for r in old_p['entry_opportunities'] if r.get('pending_at_end')}
    for name in ('trades','stop_decisions','observed_gaps','entry_opportunities','PERIOD_END_OPEN_POSITIONS'):
        a=journal_subset(old_p,name,YEAR_START,pending if name=='entry_opportunities' else set())
        b=journal_subset(p,name,YEAR_START,pending if name=='entry_opportunities' else set())
        fields=set(k for row in a+b for k in row)
        compare=C.Comparison()
        compare.rows([{k:r.get(k) for k in fields} for r in b],
                     [{k:r.get(k) for k in fields} for r in a],
                     'SEALED_2025_'+name,keys[name])
        assert not compare.diffs,('SEALED_2025_CHANGED',name,compare.diffs[:3])
    for symbol in C.SYMBOLS:
        pd.testing.assert_frame_equal(old_frames[symbol],current_frames[symbol].loc[current_frames[symbol].index<YEAR_START],check_exact=True)
    summary=present(p,current_frames,end)
    assert summary['last_available_bar_close']>=YEAR_START,'NO_2026_CANDLES'
    emit(output/'SOURCE_RECEIPTS.json',receipts)
    emit(output/'AUDIT.json',{'status':'PASS','compared_full_replay_fields':cmp.fields,
                              'primary_scalar_differences':0,'published_2025_WF_prefix':'PASS',
                              'unmodified_frozen_engine':'PASS','no_cost_deductions':True,
                              'read_ceiling':end,'data_commit':PIN,
                              'future_OHLCV_suffix_read':False,'TradingSystemLab_untouched':True})
    emit(output/'SUMMARY.json',summary)
    G.persist(p,output/'primary')
    G.persist(s,output/'scalar')
    report=['# TRUE OOS 2026 — YTD, GROSS ONLY','',
            'Это незавершённый календарный 2026; никаких комиссий и издержек.',
            'Замороженная T3/M15 A6+S1 NEXT_OPEN TRAIL_375; все 4 инструмента.',
            f"DATA END EXCLUSIVE: {end.isoformat()}",
            f"LAST BAR CLOSE: {summary['last_available_bar_close'].isoformat()}",
            f"CALENDAR CLOSED: {summary['calendar_CLOSED']}",
            f"NEW 2026 CLOSED: {summary['new_2026_entry_CLOSED']}",
            f"MONTHS POSITIVE/NEGATIVE: {summary['positive_months']}/{summary['negative_months']}",
            f"PRIMARY/SCALAR + FROZEN 2025 PREFIX: PASS",
            'Нет LIVE разрешения и нет утверждения о полном годе.']
    (output/'REPORT_RU.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    print(json.dumps({'status':'OOS_2026_YTD_RESEARCH_ONLY','gross_pf':summary['calendar_CLOSED']['gross_PF'],
                      'closed':summary['calendar_CLOSED']['closed'],
                      'gross_R':summary['calendar_CLOSED']['gross_R'],
                      'last_bar':str(summary['last_available_bar_close']),'output':str(output)},ensure_ascii=False))
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--data-root',type=Path,default=Path('/workspace/market-pattern-data'))
    p.add_argument('--output',type=Path,default=HERE/'results')
    p.add_argument('--end-exclusive',default=CUTOFF.isoformat())
    args=p.parse_args()
    try:run(args.data_root,args.output,datetime.fromisoformat(args.end_exclusive))
    except Exception as exc:
        args.output.mkdir(parents=True,exist_ok=True)
        emit(args.output/'STOP.json',{'status':'OOS_2026_YTD_INVALID_STOP',
                                     'exception':repr(exc),'no_valid_oos_results':True})
        raise
