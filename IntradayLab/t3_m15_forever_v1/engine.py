"""Standalone frozen T3/M15 replay. No TradingSystemLab executable imports."""
from dataclasses import dataclass, asdict
import csv
import hashlib
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd

BASE_COMMIT = "7927d3d6b465ec1bceae51ec8121def5e7c7e191"
DATA_COMMIT = "f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8"
TZ = "Europe/Moscow"
START = pd.Timestamp("2023-01-01", tz=TZ)
END = pd.Timestamp("2025-01-01", tz=TZ)
SYMBOLS = ("USDRUBF", "CNYRUBF", "GLDRUBF", "IMOEXF")
ALIASES = {"USDRUBF": "Si", "CNYRUBF": "CNY"}
# Si/CNY units deliberately reproduce the historical research model.
UNITS = {"USDRUBF": .001, "CNYRUBF": .001, "GLDRUBF": .1, "IMOEXF": .5}


@dataclass(frozen=True)
class Parameters:
    ema_period: int = 75
    slope_lookback: int = 5
    adx_period: int = 14
    adx_threshold: int = 20
    atr_period: int = 14
    atr_average_period: int = 20
    breakout_period: int = 20
    stop_atr: float = 2.0
    trail_atr: float = 3.0


CONFIGS = {"BASELINE": Parameters(), "OPTIMIZED": Parameters(trail_atr=3.5)}


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args]).decode().strip()


def sha_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_source(root, relative):
    """Verify working file bytes against pinned blob, never mutate the source."""
    blob = git(root, "rev-parse", f"{DATA_COMMIT}:{relative}")
    if git(root, "hash-object", "--", str(Path(root) / relative)) != blob:
        raise ValueError(f"PINNED_BLOB_MISMATCH: {relative}")
    return {"path": relative, "git_blob_sha": blob,
            "full_sha256": sha_file(Path(root) / relative)}


def read_prefix(path):
    """Read historical OHLC only; inspect boundary timestamp before its OHLC.

    Full-file integrity hashing is a separate opaque byte operation. This parser
    stops after the second semicolon of the first 2025+ row, without parsing or
    loading that row's OHLC. The pinned, chronological source is the contract.
    """
    rows, stamps, digest = [], [], hashlib.sha256()
    with Path(path).open("rb") as stream:
        header = stream.readline()
        if header.rstrip(b"\r\n") != b"Ticker;Datetime;Open;High;Low;Close;Volume":
            raise ValueError("UNEXPECTED_HEADER")
        digest.update(header)
        while True:
            prefix = bytearray()
            separators = 0
            while separators < 2:
                char = stream.read(1)
                if not char:
                    break
                prefix.extend(char)
                separators += char == b";"
            if not prefix:
                break
            if separators != 2:
                raise ValueError("TRUNCATED_TIMESTAMP")
            stamp = pd.Timestamp(prefix.decode().split(";")[1]).tz_localize(TZ)
            if stamp >= END:
                break
            suffix = stream.readline()
            digest.update(prefix + suffix)
            if stamp < START:
                continue
            values = suffix.decode().strip().split(";")
            rows.append([float(v) for v in values])
            stamps.append(stamp)
    frame = pd.DataFrame(rows, columns=["Open", "High", "Low", "Close", "Volume"],
                         index=pd.DatetimeIndex(stamps, name="OpenTime"))
    validate(frame)
    return frame, digest.hexdigest()


def validate(frame):
    if frame.empty or frame.index.tz is None or not frame.index.is_monotonic_increasing or frame.index.has_duplicates:
        raise ValueError("INVALID_TIME_INDEX")
    index = frame.index
    if not ((index.minute % 15 == 0) & (index.second == 0)).all():
        raise ValueError("INVALID_M15_GRID")
    if (index < START).any() or (index >= END).any():
        raise ValueError("HISTORICAL_WINDOW_VIOLATION")
    if not np.isfinite(frame.to_numpy()).all():
        raise ValueError("NONFINITE_OHLCV")
    if (frame.High < frame[["Open", "Close", "Low"]].max(axis=1)).any() or (frame.Low > frame[["Open", "Close", "High"]].min(axis=1)).any():
        raise ValueError("INVALID_OHLC")


def close_index(frame):
    out = frame.copy()
    out.index += pd.Timedelta(minutes=15)
    out.index.name = "CloseTime"
    out = out.loc[(out.index >= START) & (out.index < END)]
    validate(out)
    return out


def historical_quarters(root, alias):
    names = git(root, "ls-tree", "-r", "--name-only", DATA_COMMIT, f"2026/{alias}").splitlines()
    names = [n for n in names if any(Path(n).name.startswith(f"{alias}_M15_{y}_Q") for y in (2023, 2024))]
    pieces, sources = [], []
    for relative in sorted(names):
        sources.append(verify_source(root, relative))
        raw = pd.read_csv(Path(root) / relative, sep=";")
        stamps = pd.to_datetime(raw["<DATE>"].astype(str) + raw["<TIME>"].astype(str).str.zfill(6), format="%Y%m%d%H%M%S")
        frame = raw[["<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>", "<VOL>"]].copy()
        frame.columns = ["Open", "High", "Low", "Close", "Volume"]
        frame.index = pd.DatetimeIndex(stamps).tz_localize(TZ)
        validate(frame)
        pieces.append(frame)
    result = pd.concat(pieces)
    result.index.name = "OpenTime"
    validate(result)
    return result, sources


def context(frame):
    """Four consecutive closes per daily ordinal block; incomplete/gap blocks skipped."""
    rows, stamps = [], []
    for _, day in frame.groupby(frame.index.normalize(), sort=True):
        for offset in range(0, len(day), 4):
            block = day.iloc[offset:offset+4]
            if len(block) != 4 or not (block.index.to_series().diff().iloc[1:] == pd.Timedelta(minutes=15)).all():
                continue
            rows.append([block.Open.iloc[0], block.High.max(), block.Low.min(), block.Close.iloc[-1], block.Volume.sum()])
            stamps.append(block.index[-1])
    return pd.DataFrame(rows, columns=frame.columns, index=pd.DatetimeIndex(stamps, name="CloseTime"))


def tr(frame):
    previous = frame.Close.shift(1)
    return pd.concat([frame.High-frame.Low, (frame.High-previous).abs(), (frame.Low-previous).abs()], axis=1).max(axis=1)


def wilder(values, period):
    return values.ewm(alpha=1/period, adjust=False, min_periods=period).mean()


def indicators(frame, p):
    low, high = frame.copy(), context(frame)
    low["ATR"] = wilder(tr(low), p.atr_period)
    low["PriorHigh"] = low.High.rolling(p.breakout_period).max().shift(1)
    low["PriorLow"] = low.Low.rolling(p.breakout_period).min().shift(1)
    high["EMA"] = high.Close.ewm(span=p.ema_period, adjust=False, min_periods=p.ema_period).mean()
    high["Slope"] = high.EMA - high.EMA.shift(p.slope_lookback)
    up, down = high.High.diff(), -high.Low.diff()
    average_tr = wilder(tr(high), p.adx_period)
    plus = 100*wilder(up.where((up > down) & (up > 0), 0.0), p.adx_period)/average_tr
    minus = 100*wilder(down.where((down > up) & (down > 0), 0.0), p.adx_period)/average_tr
    high["ADX"] = wilder(100*(plus-minus).abs()/(plus+minus).replace(0, float("nan")), p.adx_period)
    high["ATR"] = wilder(tr(high), p.atr_period)
    high["ATRMean"] = high.ATR.rolling(p.atr_average_period).mean()
    valid = high[["Close", "EMA", "Slope", "ADX", "ATR", "ATRMean"]].notna().all(axis=1) & (high.ADX > p.adx_threshold) & (high.ATR > high.ATRMean)
    regimes = pd.Series(0, index=high.index)
    regimes.loc[valid & (high.Close > high.EMA) & (high.Slope > 0)] = 1
    regimes.loc[valid & (high.Close < high.EMA) & (high.Slope < 0)] = -1
    low["Regime"] = regimes.reindex(low.index, method="ffill").fillna(0)
    low["Signal"] = 0
    low.loc[(low.Regime == 1) & (low.Close > low.PriorHigh), "Signal"] = 1
    low.loc[(low.Regime == -1) & (low.Close < low.PriorLow), "Signal"] = -1
    return low, high


def execute(low, symbol, version, p, unit):
    """Historical stop-first OHLC convention; stop bar excluded from MFE."""
    if unit <= 0 or not np.isfinite(unit):
        raise ValueError("INVALID_C1_UNIT")
    records, pos = [], None
    for bar in low.itertuples():
        if pos is not None:
            sign, entry, stop = pos["sign"], pos["entry"], pos["stop"]
            hit = bar.Low <= stop if sign == 1 else bar.High >= stop
            if hit:
                exit_price = min(bar.Open, stop) if sign == 1 else max(bar.Open, stop)
                risk = abs(entry-pos["initial_stop"])
                gross = sign*(exit_price-entry)/risk
                mae = max(0., entry-pos["min"] if sign == 1 else pos["max"]-entry, sign*(entry-exit_price))
                mfe = max(0., pos["max"]-entry if sign == 1 else entry-pos["min"])
                alias = ALIASES.get(symbol, symbol)
                records.append({"version": version, "instrument": symbol,
                    "trade_id": f"T3-M15-{alias}-{len(records)+1:06d}", "direction": "LONG" if sign == 1 else "SHORT",
                    "entry_time": pos["at"], "entry_price": entry, "initial_stop": pos["initial_stop"], "initial_risk": risk,
                    "exit_time": bar.Index, "exit_price": exit_price, "gross_R": gross, "C1_R": 2*unit/risk, "net_R": gross-2*unit/risk,
                    "MAE_R": mae/risk, "MFE_R": mfe/risk, "bars_held": pos["bars"]+1,
                    "holding_minutes": (bar.Index-pos["at"]).total_seconds()/60,
                    "c1_price_unit": unit, "initial_risk_ticks": risk/unit,
                    "exit_type": "INITIAL_STOP" if stop == pos["initial_stop"] else "RATCHETED_STOP",
                    "active_stop_at_exit": stop, "trailing_updates": pos["updates"],
                    "gap_exit": bool(exit_price != stop),
                    "cross_calendar_day": bool(bar.Index.normalize() != pos["at"].normalize())})
                pos = None
            else:
                pos["bars"] += 1
                pos["min"], pos["max"] = min(pos["min"], bar.Low), max(pos["max"], bar.High)
                pos["extreme"] = max(pos["extreme"], bar.High) if sign == 1 else min(pos["extreme"], bar.Low)
                proposed = pos["extreme"]-sign*p.trail_atr*bar.ATR
                pos["stop"] = max(stop, proposed) if sign == 1 else min(stop, proposed)
                pos["updates"] += pos["stop"] != stop
        # Same-bar re-entry after a protective exit is part of the historical model.
        if pos is None and pd.notna(bar.ATR) and bar.Signal:
            sign, entry = int(bar.Signal), float(bar.Close)
            stop = entry-sign*p.stop_atr*float(bar.ATR)
            pos = {"sign": sign, "entry": entry, "at": bar.Index, "initial_stop": stop,
                   "stop": stop, "extreme": entry, "min": entry, "max": entry, "bars": 0, "updates": 0}
    return pd.DataFrame(records), (None if pos is None else {
        "version": version, "instrument": symbol, "entry_time": pos["at"].isoformat(),
        "direction": "LONG" if pos["sign"] == 1 else "SHORT",
        "entry_price": pos["entry"], "initial_stop": pos["initial_stop"],
        "initial_risk": abs(pos["entry"]-pos["initial_stop"]), "active_stop": pos["stop"],
        "last_close_price": float(low.Close.iloc[-1]),
        "unrealized_gross_R_at_last_close": pos["sign"]*(float(low.Close.iloc[-1])-pos["entry"])/abs(pos["entry"]-pos["initial_stop"]),
        "exit_C1_and_funding": "UNRESOLVED_NOT_ZERO",
        "last_close": low.index[-1].isoformat(), "status": "OPEN_NOT_LIQUIDATED_EXCLUDED_FROM_CLOSED_TRADE_METRICS"})


def replay(frame, symbol, version, unit=None):
    p = CONFIGS[version]
    low, _ = indicators(frame, p)
    return execute(low, symbol, version, p, UNITS[symbol] if unit is None else unit)
