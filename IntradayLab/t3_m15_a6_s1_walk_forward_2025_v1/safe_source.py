"""Two unbuffered timestamp-first readers. Only permitted suffix bytes are read.

At the locked boundary only a four-byte YEAR sentinel is inspected, never a
2026 timestamp or OHLCV. No buffered read-ahead, git hash-object or full hash.
Source ordering is verified over the admitted prefix; closed suffix is untouched.
"""
from datetime import datetime
from pathlib import Path
import hashlib, math, os, sys
import pandas as pd
import common as C
HEADER=b'Ticker;Datetime;Open;High;Low;Close;Volume\n'
DATA_ROOT=Path('/workspace/market-pattern-data').resolve()
AUTHORIZED_OPEN=False
OPEN_EVENTS=[]

def open_guard(event,args):
    if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
        path=Path(os.fsdecode(args[0])).resolve()
        if path==DATA_ROOT or DATA_ROOT in path.parents:
            # Only four M15 paths; metadata access uses git commands separately.
            allowed={DATA_ROOT/f'forever/{s}/{s}_M15.csv' for s in C.SYMBOLS}
            assert AUTHORIZED_OPEN and path in allowed,'UNAUTHORIZED_MARKET_FILE_OPEN'
            OPEN_EVENTS.append(str(path.relative_to(DATA_ROOT)))
sys.addaudithook(open_guard)

def open_raw(path):
    global AUTHORIZED_OPEN
    AUTHORIZED_OPEN=True
    try:return open(path,'rb',buffering=0)
    finally:AUTHORIZED_OPEN=False

def receipt(f,end,rows,digest,read_rows,reason):
    return {'reader':'unbuffered_FileIO_timestamp_first','cutoff_end_exclusive':end.isoformat(),
        'used_candles':len(rows),'first_close':rows[0]['at'].isoformat() if rows else None,
        'last_close':rows[-1]['at'].isoformat() if rows else None,'allowed_prefix_sha256':digest.hexdigest(),
        'bytes_read':f.tell(),'OHLCV_suffix_reads':read_rows,'OHLCV_decoded_rows':len(rows),
        'stop_reason':reason,'locked_timestamp_decoded':False,'locked_price_volume_read':False,
        'full_file_hash_computed':False,'buffering':0}

def read_primary(path,end):
    assert C.START<end<=datetime(2026,1,1,tzinfo=C.TZ)
    rows=[];digest=hashlib.sha256();last=None;count=0;reason='EOF'
    with open_raw(path) as f:
        header=f.readline();assert header==HEADER;digest.update(header)
        while True:
            ticker=bytearray()
            while True:
                ch=f.read(1)
                if not ch:break
                ticker.extend(ch)
                if ch==b';':break
                assert len(ticker)<30,'BAD_TICKER_PREFIX'
            if not ticker:break
            assert ch==b';','TRUNCATED_TICKER'
            year=f.read(4);assert len(year)==4 and year.isdigit(),'BAD_YEAR'
            if int(year)>=(end.year if end.month==1 else end.year+1):
                reason='YEAR_SENTINEL_AT_OR_AFTER_CUTOFF';break
            stamp=bytearray(year)
            while True:
                ch=f.read(1);assert ch,'TRUNCATED_TIMESTAMP'
                stamp.extend(ch)
                if ch==b';':break
                assert len(stamp)<=20,'BAD_TIMESTAMP_WIDTH'
            opening=datetime.strptime(bytes(stamp[:-1]).decode('ascii'),'%Y-%m-%d %H:%M:%S').replace(tzinfo=C.TZ)
            if opening+C.STEP>=end:
                reason='COMPLETION_AT_OR_AFTER_CUTOFF';break
            assert C.START<=opening and (last is None or opening>last),'UNSORTED_OR_OUT_OF_SCOPE'
            assert opening.minute%15==0 and opening.second==0
            tail=f.readline();assert tail.endswith(b'\n'),'TRUNCATED_OHLCV'
            count+=1;digest.update(ticker+stamp+tail)
            numbers=list(map(float,tail.decode('ascii').strip().split(';')))
            assert len(numbers)==5 and all(math.isfinite(v) for v in numbers),'BAD_VALUES'
            o,h,l,c,v=numbers;assert h>=max(o,l,c) and l<=min(o,h,c),'BAD_OHLC'
            rows.append({'at':opening+C.STEP,'o':o,'h':h,'l':l,'c':c,'v':v});last=opening
        rec=receipt(f,end,rows,digest,count,reason)
    index=pd.DatetimeIndex([r['at'] for r in rows],name='CloseTime')
    frame=pd.DataFrame([{a:r[b] for a,b in [('Open','o'),('High','h'),('Low','l'),('Close','c'),('Volume','v')]} for r in rows],index=index)
    return frame,rec

def read_scalar(path,end):
    """Separate tokenization/validation; no call to read_primary or pandas features."""
    assert end<=datetime(2026,1,1,tzinfo=C.TZ)
    bars=[];hashing=hashlib.sha256();previous=None;tails=0;reason='EOF'
    with open_raw(path) as stream:
        first=stream.readline();assert first==HEADER;hashing.update(first)
        while True:
            leading=bytearray()
            while not leading or leading[-1]!=59:
                unit=stream.read(1)
                if not unit:break
                leading+=unit;assert len(leading)<30
            if not leading:break
            assert leading[-1]==59
            yyyy=stream.read(4);assert len(yyyy)==4 and yyyy.isdigit()
            if yyyy>=str(end.year if end.month==1 else end.year+1).encode():reason='YEAR_SENTINEL_AT_OR_AFTER_CUTOFF';break
            text=bytearray(yyyy)
            while text[-1]!=59:
                bit=stream.read(1);assert bit; text+=bit;assert len(text)<=20
            value=bytes(text[:-1]).decode('ascii');time=datetime.fromisoformat(value).replace(tzinfo=C.TZ)
            finish=time+C.STEP
            if finish>=end:reason='COMPLETION_AT_OR_AFTER_CUTOFF';break
            assert time>=C.START and (previous is None or time>previous)
            assert time.minute%15==0 and time.second==0
            numeric=stream.readline();assert numeric.endswith(b'\n');tails+=1
            hashing.update(leading+text+numeric)
            columns=numeric.rstrip(b'\r\n').split(b';');assert len(columns)==5
            vals=[float(col) for col in columns];assert all(math.isfinite(x) for x in vals)
            bar=dict(zip(('o','h','l','c','v'),vals));assert bar['l']<=min(bar['o'],bar['c'])<=max(bar['o'],bar['c'])<=bar['h']
            assert bar['l']<=bar['h'];bars.append({'at':finish}|bar);previous=time
        result=receipt(stream,end,bars,hashing,tails,reason)
    return bars,result
