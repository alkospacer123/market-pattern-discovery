from __future__ import annotations

from dataclasses import dataclass
import pandas as pd

REQUIRED = ("open", "high", "low", "close", "volume")


@dataclass(frozen=True)
class DataDiagnostics:
    rows: int
    duplicate_timestamps: tuple[str, ...]
    missing_timestamps: tuple[str, ...]
    invalid_ohlc_rows: tuple[str, ...]


def validate_ohlcv(data: pd.DataFrame, expected_frequency: str | None = None) -> tuple[pd.DataFrame, DataDiagnostics]:
    missing = set(REQUIRED).difference(data.columns)
    if missing:
        raise ValueError(f"Missing OHLCV columns: {sorted(missing)}")
    out = data.copy()
    if "datetime" in out.columns:
        out = out.set_index(pd.to_datetime(out.pop("datetime")))
    out.index = pd.DatetimeIndex(out.index)
    duplicates = tuple(map(str, out.index[out.index.duplicated(keep=False)].unique()))
    out = out.sort_index(kind="stable")
    hi = out[["open", "close", "low"]].max(axis=1)
    lo = out[["open", "close", "high"]].min(axis=1)
    invalid = tuple(map(str, out.index[(out.high < hi) | (out.low > lo) | (out.volume < 0)]))
    gaps: tuple[str, ...] = ()
    if expected_frequency and len(out):
        expected = pd.date_range(out.index.min(), out.index.max(), freq=expected_frequency, tz=out.index.tz)
        gaps = tuple(map(str, expected.difference(out.index)))
    return out, DataDiagnostics(len(out), duplicates, gaps, invalid)
