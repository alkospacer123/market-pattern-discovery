"""R070 OFFLINE-ONLY source verification + initial CNY checkpoint, no FINAM API.

This stand-alone script deliberately writes NO LIVE StateStore or account-scoped
pointer. It produces a SHA-pinned checkpoint evidence ZIP equivalent in archive
schema/serialization to r070_m15_checkpoint.save_r070_m15_checkpoint.

Calendar evidence (MOEX 2026 published trading schedule):
https://www.moex.com/n96571
https://www.moex.com/n95564
From 2026-08-30 to 2026-11-15 all days traded on futures except
2026-09-12/13 and 2026-10-24/25. A trading session being open is NOT proof
that a missing per-instrument bar had any actual trades.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import tempfile
from zipfile import ZipFile, ZIP_DEFLATED
import os
import pandas as pd

R060_ZIP = 'TRL-R060-V20-Cash-Parity-2023-2026-Reproducible.zip'
R060_SHA = '80291246ba4692485545f58fd28c7563199bf7be28033fc16eb296efee377e31'
SEED_NAME = 'input/input/frozen/sources/ohlcv/CNYRUBF_M15.csv'
SEED_SHA = '259298733d1528c0d917b100118896009519a9f08bdad33d4b373d9ce86f99b4'
RECENT_NAME = 'CNYRUBF_260830_261116.csv'
RECENT_SHA = 'f6ae045a074fea9be3f7c9b5ca47dfc7dedae4481f61e8a71fc60d16b502d4f2'
REQUIRED = ['Datetime','Open','High','Low','Close','Volume']
END = datetime(2026,11,15,17,45)
CLOSED = {date(2026,9,12),date(2026,9,13),date(2026,10,24),date(2026,10,25)}
SCHEMA = 'v20.r070.m15_candidate_checkpoint.v1'


def check(raw: bytes, expected: str, label: str) -> None:
    if sha256(raw).hexdigest() != expected:
        raise ValueError(f'{label}: SHA256_MISMATCH')


def strict(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty or not set(REQUIRED) <= set(frame.columns):
        raise ValueError('M15_SCHEMA')
    d = frame[REQUIRED].copy().reset_index(drop=True)
    t = pd.to_datetime(d.Datetime, errors='raise')
    if (t.dt.tz is not None or t.isna().any() or not t.is_monotonic_increasing
            or t.duplicated().any() or (t.dt.minute % 15).any()
            or t.dt.second.any() or t.dt.microsecond.any() or t.dt.nanosecond.any()):
        raise ValueError('M15_TIME_INVALID')
    d['Datetime'] = t
    for col in REQUIRED[1:]:
        vals = pd.to_numeric(d[col], errors='raise')
        if vals.isna().any() or not vals.map(lambda v: Decimal(str(v)).is_finite()).all():
            raise ValueError('M15_NONFINITE')
        d[col] = vals
    if ((d[['Open','High','Low','Close']] <= 0).any().any()
            or (d.Volume < 0).any()
            or (d.High < d[['Open','Low','Close']].max(axis=1)).any()
            or (d.Low > d[['Open','High','Close']].min(axis=1)).any()):
        raise ValueError('M15_OHLCV_INVALID')
    return d


def build(sources: Path, outfile: Path) -> dict:
    nested_raw = (sources / R060_ZIP).read_bytes()
    terminal_raw = (sources / RECENT_NAME).read_bytes()
    check(nested_raw, R060_SHA, 'R060_ZIP')
    check(terminal_raw, RECENT_SHA, 'TERMINAL_CNY')
    with ZipFile(BytesIO(nested_raw)) as z:
        seed_raw = z.read(SEED_NAME)
    check(seed_raw, SEED_SHA, 'R060_CNY')
    seed_original = pd.read_csv(BytesIO(seed_raw), sep=';', parse_dates=['Datetime'])
    if ('Ticker' not in seed_original or not seed_original.Ticker.eq('CNYRUBF').all()):
        raise ValueError('SEED_TICKER_INVALID')
    seed = strict(seed_original)
    raw = pd.read_csv(BytesIO(terminal_raw), sep=';', dtype=str, encoding='utf-8-sig')
    if list(raw.columns) != ['<DATE>','<TIME>','<OPEN>','<HIGH>','<LOW>','<CLOSE>','<VOL>']:
        raise ValueError('FINAM_SCHEMA_INVALID')
    terminal = pd.DataFrame()
    terminal['Datetime'] = pd.to_datetime(raw['<DATE>'] + raw['<TIME>'].str.zfill(6), format='%Y%m%d%H%M%S')
    for col, source in [('Open','<OPEN>'),('High','<HIGH>'),('Low','<LOW>'),('Close','<CLOSE>'),('Volume','<VOL>')]:
        terminal[col] = pd.to_numeric(raw[source], errors='raise')
    terminal = strict(terminal)
    if terminal.Datetime.iloc[-1] != pd.Timestamp('2026-11-16 08:15:00'):
        raise ValueError('PINNED_TERMINAL_LAST_BAR_CHANGED')
    terminal = strict(terminal.loc[terminal.Datetime <= END])
    if terminal.Datetime.iloc[-1] != pd.Timestamp(END):
        raise ValueError('FINAL_VERIFIED_BAR_MISSING')
    old, new = seed.set_index('Datetime'), terminal.set_index('Datetime')
    if old.index[-1] > pd.Timestamp(END):
        raise ValueError('SEED_FUTURE')
    overlap = old.index.intersection(new.index)
    if len(overlap) < 1:
        raise ValueError('SEED_TERMINAL_OVERLAP_MISSING')
    for stamp in overlap:
        for col in REQUIRED[1:]:
            if Decimal(str(old.loc[stamp,col])) != Decimal(str(new.loc[stamp,col])):
                raise ValueError(f'OHLCV_OVERLAP_DISAGREEMENT:{stamp}:{col}')
    combined = strict(pd.concat([old.loc[old.index < new.index[0]], new]).reset_index())
    if len(combined) != len(seed) + len(terminal) - len(overlap):
        raise ValueError('STITCH_ROW_COUNT_INCONSISTENT')
    if (combined.Datetime.iloc[-1] != pd.Timestamp(END)):
        raise ValueError('STITCH_LAST_WRONG')
    start, final = terminal.Datetime.iloc[0].date(), END.date()
    days = tuple(start+timedelta(days=i) for i in range((final-start).days+1)
                 if start+timedelta(days=i) not in CLOSED)
    if len(days) != 74 or days[0] != date(2026,8,30) or days[-1] != final:
        raise ValueError('EXCHANGE_CALENDAR_MISMATCH')
    minutes = combined.Datetime.dt.hour * 60 + combined.Datetime.dt.minute
    times = combined.loc[minutes.between(600,1065),'Datetime']
    grouped = {day: pd.DatetimeIndex(t) for day,t in times.groupby(times.dt.date)}
    for day in days:
        expected = pd.date_range(datetime.combine(day,datetime.min.time())+timedelta(hours=10), periods=32, freq='15min')
        if not grouped.get(day,pd.DatetimeIndex([])).equals(expected):
            missing = expected.difference(grouped.get(day,pd.DatetimeIndex([])))
            raise ValueError(f'CNY_SESSION_GAP:{day}:{list(missing)}')
    unexpected = {d for d in grouped if start <= d <= final and d not in days}
    if unexpected:
        raise ValueError(f'CNY_UNPROVEN_SESSIONS:{unexpected}')
    # R060 previous-session validity, and independent R060 Wilder warm-up.
    date_shift=(combined.Datetime-pd.Timedelta(hours=9)).dt.normalize()
    within=combined.loc[minutes.between(600,1065)]
    daily=within.assign(day=date_shift.loc[within.index]).groupby('day').agg(
        hi=('High','max'),lo=('Low','min'),sclose=('Close','last'),
        bars=('Close','size'),first=('Datetime','min'),last=('Datetime','max'))
    prior=daily.loc[daily.index < pd.Timestamp(END.date())].iloc[-1]
    if not (prior.bars>=12 and prior['first'].hour==10 and prior['first'].minute==0
            and prior['last'].hour*60+prior['last'].minute>=1035):
        raise ValueError('PREVIOUS_SESSION_INCOMPLETE')
    previous_close=daily.sclose.shift(1)
    tr=pd.concat([daily.hi-daily.lo, (daily.hi-previous_close).abs(),(daily.lo-previous_close).abs()],axis=1).max(axis=1)
    atr=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean().shift(1)
    if pd.isna(atr.iloc[-1]) or atr.iloc[-1] <= 0:
        raise ValueError('R060_WILDER_DATR_MISSING')
    csv=combined.to_csv(index=False,date_format='%Y-%m-%dT%H:%M:%S',float_format='%.17g',lineterminator='\n').encode('utf8')
    history_sha=sha256(csv).hexdigest()
    manifest={
        'schema':SCHEMA,'symbol':'CNYRUBF','history_sha256':history_sha,
        'rows':len(combined),'latest_m15_open_msk':END.isoformat(),
        'source_r060_csv_sha256':SEED_SHA,'source_finam_terminal_csv_sha256':RECENT_SHA,
        'csv_sha256':history_sha,
    }
    outfile.parent.mkdir(parents=True, exist_ok=True)
    if outfile.exists():
        raise FileExistsError('CHECKPOINT_EXISTS_NO_OVERWRITE')
    descriptor,tmp=tempfile.mkstemp(prefix='.r070-m15-',suffix='.zip',dir=outfile.parent)
    try:
        with os.fdopen(descriptor,'wb') as output:
            with ZipFile(output,'w',compression=ZIP_DEFLATED) as z:
                z.writestr('manifest.json',json.dumps(manifest,sort_keys=True,separators=(',',':')))
                z.writestr('history.csv',csv)
            output.flush();os.fsync(output.fileno())
        os.replace(tmp,outfile)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    # Independent load checks of the exact ZIP content and historical prefix.
    with ZipFile(outfile) as z:
        assert z.namelist() == ['manifest.json','history.csv']
        test_manifest=json.loads(z.read('manifest.json'))
        test_raw=z.read('history.csv')
    assert test_manifest==manifest
    assert sha256(test_raw).hexdigest()==history_sha
    check_loaded = strict(pd.read_csv(BytesIO(test_raw),parse_dates=['Datetime'],float_precision='round_trip'))
    check_loaded_bytes = check_loaded.to_csv(index=False,date_format='%Y-%m-%dT%H:%M:%S',float_format='%.17g',lineterminator='\n').encode('utf8')
    assert sha256(check_loaded_bytes).hexdigest()==history_sha, 'LOSSY_CHECKPOINT_ROUNDTRIP'
    return {
        'status':'OFFLINE_CNY_M15_CHECKPOINT_PASS_NOT_LIVE',
        'rows':len(combined), 'overlap_bars':len(overlap),
        'exchange_open_days':len(days), 'regular_m15_missing':0,
        'last_completed_m15_open_msk':END.isoformat(),
        'checkpoint_sha256':sha256(outfile.read_bytes()).hexdigest(),
        'history_sha256':history_sha,
        'checkpoint_filename':outfile.name,
        'calendar_source':'https://www.moex.com/n96571',
        'not_live_approved':True,
        'no_account_bound_state':True,
        'no_finam_requests':True,
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--sources',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    result=build(args.sources,args.out)
    print(json.dumps(result,indent=2,ensure_ascii=False))

if __name__=='__main__':main()