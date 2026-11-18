"""R088 OFFLINE: two historical R060 + FINAM source checkpoints.

No FINAM API, live SQLite, token, orders or ARM. The 14 known historical
missing M15 are from the original 18-Nov official FINAM terminal exports,
SHA-pinned in r088_finam_historical_gaps; they are left ABSENT.
Uses the already-existing R070 checkpoint serializer and source SHA pins.
"""
from __future__ import annotations

import argparse
from datetime import datetime, date, timedelta
from decimal import Decimal
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile
import pandas as pd

from V20_TradingSystem_M15.v20_runtime.ext2_history_bridge import (
    EXT2HistoryBlocked, R060_SEED_SHA256, _strict_m15,
    load_finam_terminal_csv, m15_history_sha256,
)
from V20_TradingSystem_M15.v20_runtime.ext2_r060 import REQUIRED, r060_features
from V20_TradingSystem_M15.v20_runtime.r070_m15_checkpoint import (
    PINNED_TERMINAL_SHA256, save_r070_m15_checkpoint, load_r070_m15_checkpoint,
)
from V20_TradingSystem_M15.v20_runtime.r088_finam_historical_gaps import (
    accepted_historical_missing_m15,
)

R060_NAME = "TRL-R060-V20-Cash-Parity-2023-2026-Reproducible.zip"
R060_ZIP_SHA256 = "80291246ba4692485545f58fd28c7563199bf7be28033fc16eb296efee377e31"
PINNED_LAST = datetime(2026, 11, 15, 17, 45)
CLOSED = frozenset({date(2026,9,12),date(2026,9,13),
                    date(2026,10,24),date(2026,10,25)})
SUPPORTED = ("USDRUBF", "GLDRUBF")


def need(ok: bool, code: str):
    if not ok:
        raise EXT2HistoryBlocked(code)


def _pinned_terminal_source(folder: Path, symbol: str) -> Path:
    pin = PINNED_TERMINAL_SHA256[symbol]
    candidates = tuple(p for p in folder.glob(symbol + "_*.csv")
                       if p.is_file() and not p.is_symlink())
    matches = tuple(p for p in candidates if sha256(p.read_bytes()).hexdigest() == pin)
    need(len(matches) == 1, "R088_FINAM_HISTORICAL_TERMINAL_PIN_MISSING_OR_DUPLICATE")
    return matches[0]


def build(*, sources: Path, destination: Path, symbol: str) -> dict:
    need(symbol in SUPPORTED, "R088_HISTORICAL_SYMBOL_NOT_APPROVED")
    need(sources.is_dir() and not sources.is_symlink()
         and destination.parent.is_dir() and not destination.parent.is_symlink()
         and not destination.exists() and not destination.is_symlink(),
         "R088_HISTORICAL_DESTINATION_OR_SOURCE_INVALID")
    original = sources / R060_NAME
    need(original.is_file() and not original.is_symlink()
         and sha256(original.read_bytes()).hexdigest() == R060_ZIP_SHA256,
         "R088_ORIGINAL_R060_ZIP_SHA_MISMATCH")
    seed_name = "input/input/frozen/sources/ohlcv/" + symbol + "_M15.csv"
    with ZipFile(original) as z:
        raw = z.read(seed_name)
    need(sha256(raw).hexdigest() == R060_SEED_SHA256[symbol],
         "R088_R060_SYMBOL_SHA_MISMATCH")
    source = pd.read_csv(BytesIO(raw), sep=";", parse_dates=["Datetime"],
                         float_precision="round_trip")
    need("Ticker" in source and source.Ticker.eq(symbol).all(),
         "R088_R060_SYMBOL_CHANGED")
    seed = _strict_m15(source)
    terminal_file = _pinned_terminal_source(sources, symbol)
    terminal = load_finam_terminal_csv(
        terminal_file, expected_sha256=PINNED_TERMINAL_SHA256[symbol])
    need(terminal.Datetime.iloc[-1] == pd.Timestamp("2026-11-16 08:15:00"),
         "R088_PINNED_FINAM_EXPORT_LAST_CHANGED")
    terminal = _strict_m15(terminal.loc[terminal.Datetime <= PINNED_LAST])
    need(terminal.Datetime.iloc[-1] == pd.Timestamp(PINNED_LAST),
         "R088_FINAL_COMPLETED_BAR_MISSING")
    old, new = seed.set_index("Datetime"), terminal.set_index("Datetime")
    need(old.index[-1] <= pd.Timestamp(PINNED_LAST),
         "R088_SEED_HAS_FUTURE")
    overlap = old.index.intersection(new.index)
    need(len(overlap) > 0, "R088_SEED_FINAM_NO_OVERLAP")
    for ts in overlap:
        for col in REQUIRED[1:]:
            need(Decimal(str(old.loc[ts,col])) == Decimal(str(new.loc[ts,col])),
                 "R088_SEED_FINAM_OVERLAP_DISAGREEMENT")
    combined = _strict_m15(
        pd.concat([old.loc[old.index < new.index[0]], new]).reset_index())
    need(len(combined) == len(seed) + len(terminal) - len(overlap),
         "R088_STITCH_COUNT_MISMATCH")
    begin, finish = terminal.Datetime.iloc[0].date(), PINNED_LAST.date()
    need(begin == date(2026,8,30), "R088_FINAM_START_CHANGED")
    calendar = tuple(begin+timedelta(days=i)
                     for i in range((finish-begin).days+1)
                     if begin+timedelta(days=i) not in CLOSED)
    need(len(calendar) == 74 and calendar[-1] == finish,
         "R088_PUBLISHED_MOEX_CALENDAR_CHANGED")
    times = combined.Datetime
    minutes = times.dt.hour*60 + times.dt.minute
    main = times.loc[minutes.between(600,1065)]
    present = {d: pd.DatetimeIndex(v) for d,v in
               main.groupby(main.dt.date, sort=True)}
    unknown_dates = set(present).intersection(
        {begin+timedelta(days=i) for i in range((finish-begin).days+1)}
    ) - set(calendar)
    need(not unknown_dates, "R088_M15_UNAPPROVED_CALENDAR_DATES")
    missing = []
    for day in calendar:
        start = datetime.combine(day, datetime.min.time())+timedelta(hours=10)
        expected = pd.date_range(start, periods=32, freq="15min")
        observed = present.get(day, pd.DatetimeIndex([]))
        need(not len(observed.difference(expected)),
             "R088_FINAM_UNEXPECTED_M15_OPEN")
        missing.extend(ts.to_pydatetime() for ts in expected.difference(observed))
    allowed = accepted_historical_missing_m15(symbol)
    need(tuple(missing) == allowed, "R088_FINAM_HISTORICAL_ABSENCES_CHANGED")
    need(combined.Datetime.iloc[-1] == pd.Timestamp(PINNED_LAST),
         "R088_LAST_COMPLETED_M15_MISSING")
    # Do NOT alter R060 Wilder ATR or fill sparse sessions. Keep the old
    # prior-session eligibility guard at the 15-Nov archive boundary.
    history_minute = combined.Datetime.dt.hour*60+combined.Datetime.dt.minute
    eligible = combined.loc[history_minute.between(600,1065)].copy()
    eligible["day"] = (eligible.Datetime-pd.Timedelta(hours=9)).dt.normalize()
    sessions = eligible.groupby("day").agg(n=("Close","size"),
        first=("Datetime","min"), last=("Datetime","max"))
    prior = sessions[sessions.index < pd.Timestamp(PINNED_LAST.date())].iloc[-1]
    need(prior["n"] >= 12 and prior["first"].hour == 10
         and prior["first"].minute == 0
         and prior["last"].hour*60+prior["last"].minute >= 1035,
         "R088_PRIOR_R060_SESSION_NOT_VALID")
    feats = r060_features(combined)
    need(pd.notna(feats.prior_datr14.iloc[-1])
         and feats.prior_datr14.iloc[-1] > 0,
         "R088_R060_DAILY_ATR_UNAVAILABLE")
    history_sha = m15_history_sha256(combined)
    file_sha = save_r070_m15_checkpoint(
        path=destination, symbol=symbol, verified_history=combined,
        expected_history_sha256=history_sha)
    loaded, check = load_r070_m15_checkpoint(
        path=destination, symbol=symbol,
        expected_checkpoint_sha256=file_sha,
        minimum_last_m15_open_msk=PINNED_LAST)
    need(check == history_sha and
         loaded.Datetime.equals(combined.Datetime),
         "R088_CHECKPOINT_RELOAD_NOT_IDENTICAL")
    return {"symbol":symbol,"status":"PASS_OFFLINE_FROZEN_FINAM_GAPS_NOT_INSTALLED",
            "seed_rows":len(seed),"combined_rows":len(combined),
            "overlap_rows":len(overlap),"missing_m15":len(missing),
            "missing_open_msk":[stamp.isoformat() for stamp in missing],
            "calendar_days":len(calendar),"history_sha256":history_sha,
            "checkpoint_zip_sha256":file_sha,
            "checkpoint_zip":destination.name,
            "orders_sent":0,"finam_requests":0,"live_installed":False}


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args=parser.parse_args()
    for sym in SUPPORTED:
        output = args.out / ("r070-"+sym.lower()+"-20261115-offline-m15-checkpoint.zip")
        print(json.dumps(build(sources=args.sources,destination=output,symbol=sym),
                         ensure_ascii=False,sort_keys=True),flush=True)


if __name__ == "__main__":
    main()
