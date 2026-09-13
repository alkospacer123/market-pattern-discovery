"""Read-only CSV loading and causal H1-to-H4 aggregation."""
from __future__ import annotations

from pathlib import Path
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
