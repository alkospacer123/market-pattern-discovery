"""Bounded provenance-first Finam M1 loader for Top-5 V4."""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from decimal import Decimal,ROUND_HALF_UP
from typing import Iterable
import csv,json
import numpy as np
import pandas as pd
TZ="Europe/Moscow";SCHEMA=["<TICKER>","<PER>","<DATE>","<TIME>","<OPEN>","<HIGH>","<LOW>","<CLOSE>","<VOL>"];ALIASES={"CNYRUBF":"CNYRUBF","CNY":"CNYRUBF","USDRUBF":"USDRUBF","SI":"USDRUBF"};TICKS={"CNYRUBF":Decimal("0.001"),"USDRUBF":Decimal("0.01")}
class IngestionError(ValueError):pass
@dataclass(frozen=True)
class BoundedLoadResult:
    frame:pd.DataFrame;access_events:list[dict];raw_selected_rows:int;equivalent_duplicates:int
def _guard(path):
    if "2025" in str(path):raise IngestionError("2025 TRUE OOS path access is locked")
def _sha(path):
    h=sha256();
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
    return h.hexdigest()
def raw_file_hash_event(path):
    path=Path(path);_guard(path);return {"event":"FILE_HASH_BYTES","path":str(path),"sha256":_sha(path),"file_size":path.stat().st_size,"ohlcv_materialized":False}
def _canon_instrument(value):
    try:return ALIASES[value.upper()]
    except KeyError as e:raise IngestionError(f"unsupported ticker {value}") from e
def _tick_valid(text,tick):
    try:d=Decimal(text)
    except Exception:return False
    if not d.is_finite():return False
    return (d/tick).quantize(Decimal("1"),rounding=ROUND_HALF_UP)*tick==d
def load_finam_window_many(paths:Iterable[str|Path],instrument,start,end,timeframe="M1"):
    instrument=_canon_instrument(instrument)
    if timeframe!="M1":raise IngestionError("Top-5 V4 bounded loader accepts M1 only")
    start=pd.Timestamp(start);end=pd.Timestamp(end)
    if start.tzinfo is None or end.tzinfo is None or start>=end:raise IngestionError("ordered timezone-aware window required")
    start=start.tz_convert(TZ);end=end.tz_convert(TZ);selected=[];events=[]
    for raw_path in paths:
        path=Path(raw_path);_guard(path);events.append(raw_file_hash_event(path));scanned=0;chosen=0
        with path.open("r",encoding="utf-8-sig",newline="") as f:
            reader=csv.reader(f,delimiter=";")
            try:header=next(reader)
            except StopIteration:raise IngestionError(f"empty source {path.name}")
            if header!=SCHEMA:raise IngestionError(f"schema mismatch {path.name}")
            for source_row,fields in enumerate(reader,2):
                scanned+=1
                if len(fields)!=len(SCHEMA):raise IngestionError(f"malformed row {path.name}:{source_row}")
                try:stamp=pd.to_datetime(fields[2]+fields[3].zfill(6),format="%Y%m%d%H%M%S",errors="raise").tz_localize(TZ)
                except Exception as e:raise IngestionError(f"invalid timestamp {path.name}:{source_row}") from e
                close_stamp=stamp+pd.Timedelta(minutes=1)
                if start<=stamp and close_stamp<end:selected.append((stamp,path.name,source_row,fields));chosen+=1
        events.append({"event":"TIMESTAMP_SCAN","path":str(path),"rows_scanned":scanned,"rows_selected":chosen,"window_start":start.isoformat(),"window_end":end.isoformat(),"ohlcv_materialized":False})
    if not selected:raise IngestionError("no rows in requested multi-file window")
    rows=[];tick=TICKS[instrument]
    for stamp,filename,source_row,f in selected:
        if _canon_instrument(f[0])!=instrument:raise IngestionError(f"ticker mismatch {filename}:{source_row}")
        if f[1]!="1":raise IngestionError(f"wrong PER {filename}:{source_row}")
        for v in f[4:8]:
            if not _tick_valid(v,tick):raise IngestionError(f"off-tick OHLC {filename}:{source_row}")
        try:o,h,l,c=[float(Decimal(v)) for v in f[4:8]];vol=float(Decimal(f[8]))
        except Exception as e:raise IngestionError(f"non-numeric OHLCV {filename}:{source_row}") from e
        if not np.isfinite([o,h,l,c,vol]).all() or min(o,h,l,c)<=0 or vol<0:raise IngestionError(f"invalid OHLCV {filename}:{source_row}")
        if h<max(o,c,l) or l>min(o,c,h):raise IngestionError(f"OHLC invariant {filename}:{source_row}")
        rows.append({"open_time":stamp,"close_time":stamp+pd.Timedelta(minutes=1),"open":o,"high":h,"low":l,"close":c,"volume":vol,"instrument":instrument,"timeframe":"M1","trading_date":stamp.date(),"source_filename":filename,"source_row":source_row})
    frame=pd.DataFrame(rows).sort_values(["open_time","source_filename","source_row"],kind="mergesort").reset_index(drop=True);dup=frame.duplicated("open_time",keep=False);equiv=0
    for stamp,g in frame.loc[dup].groupby("open_time",sort=False):
        vals=g[["open","high","low","close","volume"]].to_numpy()
        if not (vals==vals[0]).all():raise IngestionError(f"conflicting duplicate at {stamp.isoformat()}")
        equiv+=len(g)-1
    frame=frame.drop_duplicates("open_time",keep="first").reset_index(drop=True)
    events.append({"event":"OHLCV_MATERIALIZE","instrument":instrument,"rows":len(frame),"window_start":start.isoformat(),"window_end":end.isoformat(),"timestamp_min":frame.open_time.min().isoformat(),"timestamp_max":frame.open_time.max().isoformat(),"close_time_min":frame.close_time.min().isoformat(),"close_time_max":frame.close_time.max().isoformat(),"ohlcv_materialized":True})
    return BoundedLoadResult(frame,events,len(selected),equiv)
def append_access_events(path,events):
    p=Path(path);existing=json.loads(p.read_text(encoding="utf-8")) if p.exists() else [];existing.extend(events);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(existing,indent=2,sort_keys=True)+"\n",encoding="utf-8")
def assert_no_ohlcv_materialized(events,start,end):
    start=pd.Timestamp(start);end=pd.Timestamp(end)
    for e in events:
        if e.get("event")=="OHLCV_MATERIALIZE":
            open_lo=pd.Timestamp(e["timestamp_min"]);close_hi=pd.Timestamp(e.get("close_time_max",e["timestamp_max"]))
            if open_lo<end and close_hi>=start:raise AssertionError("forbidden OHLCV materialization recorded in protected interval")
