"""Read-only CSV loading and causal H1-to-H4 aggregation."""
from __future__ import annotations

from pathlib import Path
import csv
import re

import pandas as pd

OHLC = ["Open", "High", "Low", "Close"]


class DataLoader:
    def __init__(self, *, timezone: str = "Europe/Moscow", forbid_true_oos: bool = True) -> None:
        self.timezone = timezone
        self.forbid_true_oos = forbid_true_oos

    def load_csv(self, paths: str | Path | list[str | Path]) -> pd.DataFrame:
        selected = [Path(paths)] if isinstance(paths, (str, Path)) else [Path(p) for p in paths]
        if not selected:
            raise ValueError("at least one CSV path is required")
        frames = [self._read(path) for path in sorted(selected)]
        result = pd.concat(frames).sort_index(kind="mergesort")
        if result.index.has_duplicates:
            duplicate = result[result.index.duplicated(False)]
            if duplicate.groupby(level=0)[OHLC + (["Volume"] if "Volume" in result else [])].nunique().gt(1).any().any():
                raise ValueError("conflicting duplicate timestamps")
            result = result[~result.index.duplicated(keep="first")]
        if self.forbid_true_oos and (result.index.year >= 2025).any():
            raise ValueError("calendar year 2025+ TRUE OOS is locked and may not be loaded")
        return result

    def load_csv_prefix(self, path: str | Path, *, start: pd.Timestamp,
                        end_exclusive: pd.Timestamp) -> pd.DataFrame:
        """Load a sorted development prefix without ingesting locked later rows.

        This entry point exists for consolidated, chronologically ordered source
        files which also contain TRUE OOS observations.  It stops as soon as the
        first timestamp at ``end_exclusive`` is encountered; later fields and
        rows are never parsed into a dataframe.
        """
        source = Path(path)
        start = self._localized_bound(start)
        end_exclusive = self._localized_bound(end_exclusive)
        rows: list[dict[str, str]] = []
        with source.open("r", encoding="utf-8-sig", newline="") as stream:
            sample = stream.read(4096)
            stream.seek(0)
            header = sample.splitlines()[0] if sample else ""
            delimiter = max((",", ";", "\t"), key=header.count)
            if header.count(delimiter) == 0:
                raise ValueError(f"{source}: CSV delimiter is missing")
            reader = csv.DictReader(stream, delimiter=delimiter)
            if reader.fieldnames is None:
                raise ValueError(f"{source}: CSV header is missing")
            names = {re.sub(r"[<>]", "", name).strip().title(): name for name in reader.fieldnames}
            time_name = next((names[name] for name in ("Datetime", "Timestamp", "Date") if name in names), None)
            if time_name is None:
                raise ValueError(f"{source}: datetime column is missing")
            for raw in reader:
                stamp = pd.Timestamp(raw[time_name])
                stamp = stamp.tz_localize(self.timezone, ambiguous="raise", nonexistent="raise") if stamp.tz is None else stamp.tz_convert(self.timezone)
                if stamp >= end_exclusive:
                    break
                if stamp >= start:
                    rows.append(raw)
        if not rows:
            raise ValueError(f"{source}: no rows in requested development interval")
        frame = pd.DataFrame(rows).rename(columns=lambda c: re.sub(r"[<>]", "", str(c)).strip().title())
        stamp = pd.to_datetime(frame[next(c for c in ("Datetime", "Timestamp", "Date") if c in frame)], errors="raise")
        stamp = pd.DatetimeIndex(stamp)
        stamp = stamp.tz_localize(self.timezone, ambiguous="raise", nonexistent="raise") if stamp.tz is None else stamp.tz_convert(self.timezone)
        result = self._validated_ohlc(frame, stamp, source)
        if result.index.has_duplicates:
            raise ValueError(f"{source}: duplicate timestamps")
        if not result.index.is_monotonic_increasing:
            raise ValueError(f"{source}: timestamps are not sorted")
        return result

    def _localized_bound(self, value: pd.Timestamp) -> pd.Timestamp:
        value = pd.Timestamp(value)
        return value.tz_localize(self.timezone) if value.tz is None else value.tz_convert(self.timezone)

    def _read(self, path: Path) -> pd.DataFrame:
        # Header inspection does not modify or copy source data.
        frame = pd.read_csv(path, sep=None, engine="python")
        frame.columns = [re.sub(r"[<>]", "", str(c)).strip().title() for c in frame.columns]
        if {"Date", "Time"}.issubset(frame.columns):
            stamp = pd.to_datetime(frame["Date"].astype(str) + frame["Time"].astype(str).str.zfill(6),
                                   format="%Y%m%d%H%M%S")
        else:
            time_column = next((c for c in ("Datetime", "Timestamp", "Date") if c in frame), None)
            if time_column is None:
                raise ValueError(f"{path}: datetime column is missing")
            stamp = pd.to_datetime(frame[time_column], errors="raise")
        stamp = pd.DatetimeIndex(stamp)
        stamp = stamp.tz_localize(self.timezone, ambiguous="raise", nonexistent="raise") if stamp.tz is None else stamp.tz_convert(self.timezone)
        return self._validated_ohlc(frame, stamp, path)

    @staticmethod
    def _validated_ohlc(frame: pd.DataFrame, stamp: pd.DatetimeIndex,
                        path: Path) -> pd.DataFrame:
        missing = set(OHLC) - set(frame.columns)
        if missing:
            raise ValueError(f"{path}: missing columns {sorted(missing)}")
        columns = OHLC + (["Volume"] if "Volume" in frame else [])
        result = frame[columns].apply(pd.to_numeric, errors="raise")
        result.index = stamp
        result.index.name = "OpenTime"
        if (result["High"] < result[["Open", "Close", "Low"]].max(axis=1)).any() or (result["Low"] > result[["Open", "Close", "High"]].min(axis=1)).any():
            raise ValueError(f"{path}: invalid OHLC geometry")
        return result

    @staticmethod
    def close_index(frame: pd.DataFrame, timeframe: str = "1h") -> pd.DataFrame:
        """Convert an explicitly open-labelled input to availability timestamps."""
        result = frame.copy()
        result.index = result.index + pd.Timedelta(timeframe)
        result.index.name = "CloseTime"
        return result

    @staticmethod
    def h4_from_h1(closed_h1: pd.DataFrame) -> pd.DataFrame:
        """Aggregate consecutive blocks inside each local trading day.

        Only complete four-bar blocks are emitted and labelled at their final H1
        close, so an H4 value cannot become visible early and never crosses days.
        """
        rows = []
        for _, day in closed_h1.groupby(closed_h1.index.normalize(), sort=True):
            for offset in range(0, len(day), 4):
                block = day.iloc[offset:offset + 4]
                if len(block) != 4:
                    continue
                row = {"Open": block["Open"].iloc[0], "High": block["High"].max(),
                       "Low": block["Low"].min(), "Close": block["Close"].iloc[-1]}
                if "Volume" in block:
                    row["Volume"] = block["Volume"].sum()
                rows.append((block.index[-1], row))
        if not rows:
            return pd.DataFrame(columns=closed_h1.columns,
                                index=pd.DatetimeIndex([], name="CloseTime"))
        result = pd.DataFrame([row for _, row in rows], index=[ts for ts, _ in rows])
        result.index.name = "CloseTime"
        return result
