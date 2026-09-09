"""Strict, non-mutating Finam CSV ingestion."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from market_pattern_discovery.validation.temporal import require_development
from .timeframes import timeframe as get_timeframe

SCHEMA = ["<TICKER>", "<PER>", "<DATE>", "<TIME>", "<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>", "<VOL>"]
OHLCV = ["open", "high", "low", "close", "volume"]
ALIASES = {"CNYRUBF": "CNYRUBF", "CNY": "CNYRUBF", "USDRUBF": "USDRUBF", "SI": "USDRUBF"}
SOURCE_FOLDERS = {"CNYRUBF": "CNY", "USDRUBF": "Si"}

class IngestionError(ValueError):
    """The source violates a strict ingestion contract."""

@dataclass(frozen=True)
class LoadResult:
    frame: pd.DataFrame
    provenance: list[dict]
    raw_rows: int
    equivalent_duplicates: int
    conflicts: int = 0

def file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def _instrument(value: str) -> str:
    try:
        return ALIASES[value.upper()]
    except KeyError as exc:
        raise IngestionError(f"unsupported ticker/instrument: {value}") from exc

def discover_finam_sources(data_root: str | Path, instrument: str, timeframe: str) -> list[Path]:
    """Resolve the repository's deterministic 2026 Finam source names for one scope.

    Historical M5 files use ``<symbol>_2026_QN.csv`` while M1 files carry the
    explicit ``_M1.csv`` suffix.  File naming is therefore resolved separately
    from the Finam ``<PER>`` timeframe validation performed by :func:`_read`.
    """
    canonical = _instrument(instrument)
    get_timeframe(timeframe)
    folder = SOURCE_FOLDERS[canonical]
    root = Path(data_root) / "2026" / folder
    suffix = "_M1.csv" if timeframe == "M1" else ".csv"
    return [root / f"{folder}_2026_Q{quarter}{suffix}" for quarter in (1, 2)
            if (root / f"{folder}_2026_Q{quarter}{suffix}").is_file()]

def _read(path: Path, expected_instrument: str, timeframe: str, *, development_rows_only: bool = False) -> tuple[pd.DataFrame, dict]:
    expected_instrument = _instrument(expected_instrument)
    definition = get_timeframe(timeframe)
    try:
        raw = pd.read_csv(path, sep=";", dtype=str, keep_default_na=False)
    except Exception as exc:
        raise IngestionError(f"cannot parse {path.name}: {exc}") from exc
    if list(raw.columns) != SCHEMA:
        raise IngestionError(f"schema mismatch in {path.name}: {list(raw.columns)!r}")
    if raw.empty:
        raise IngestionError(f"empty source: {path.name}")
    if development_rows_only:
        # Mixed archive files (currently D1) are projected to the explicit
        # development interval before any market values are parsed or exposed.
        dates = pd.to_numeric(raw["<DATE>"], errors="coerce")
        raw = raw.loc[(dates >= 20260101) & (dates <= 20260701)].copy()
        if raw.empty:
            raise IngestionError(f"source has no permitted development rows: {path.name}")
    expected_per = definition.finam_period
    per = raw["<PER>"] if isinstance(expected_per, str) else pd.to_numeric(raw["<PER>"], errors="coerce")
    if per.isna().any() or not (per == expected_per).all():
        raise IngestionError(f"wrong PER for {timeframe} in {path.name}")
    instruments = raw["<TICKER>"].map(lambda x: ALIASES.get(x.upper()))
    if instruments.isna().any() or instruments.nunique() != 1 or instruments.iloc[0] != expected_instrument:
        raise IngestionError(f"ticker mismatch or instrument mixing in {path.name}")
    numbers = raw[["<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>", "<VOL>"]].apply(pd.to_numeric, errors="coerce")
    if numbers.isna().any().any() or not np.isfinite(numbers.to_numpy()).all():
        raise IngestionError(f"non-numeric or non-finite value in {path.name}")
    numbers.columns = OHLCV
    if (numbers[["open", "high", "low", "close"]] <= 0).any().any():
        raise IngestionError(f"prices must be positive in {path.name}")
    if (numbers.volume < 0).any():
        raise IngestionError(f"volume must be non-negative in {path.name}")
    if ((numbers.high < numbers[["open", "close", "low"]].max(axis=1)) | (numbers.low > numbers[["open", "close", "high"]].min(axis=1))).any():
        raise IngestionError(f"OHLC invariant violation in {path.name}")
    local_text = raw["<DATE>"] + raw["<TIME>"].str.zfill(6)
    try:
        naive = pd.to_datetime(local_text, format="%Y%m%d%H%M%S", errors="raise")
        opened = naive.dt.tz_localize("Europe/Moscow", ambiguous="raise", nonexistent="raise")
    except Exception as exc:
        raise IngestionError(f"invalid Moscow open timestamp in {path.name}: {exc}") from exc
    try:
        require_development(opened)
    except ValueError as exc:
        raise IngestionError(str(exc)) from exc
    frame = numbers.copy()
    frame["instrument"] = expected_instrument
    frame["timeframe"] = timeframe
    frame["open_local"] = naive
    frame["open_time"] = opened
    frame["open_utc"] = opened.dt.tz_convert("UTC")
    frame["close_time"] = opened + definition.duration
    frame["source_filename"] = path.name
    frame["source_row"] = np.arange(2, len(frame) + 2)
    sorted_originally = bool(opened.is_monotonic_increasing)
    provenance = {"filename": path.name, "instrument": expected_instrument, "timeframe": timeframe,
                  "raw_rows": len(frame), "timestamp_min": opened.min().isoformat(),
                  "timestamp_max": opened.max().isoformat(), "file_size": path.stat().st_size,
                  "sha256": file_sha256(path), "originally_sorted": sorted_originally}
    return frame, provenance

def stitch_finam(paths: Iterable[str | Path], instrument: str, timeframe: str) -> LoadResult:
    """Load named sources and deterministically reconcile equivalent overlaps."""
    loaded = [_read(Path(p), instrument, timeframe) for p in paths]
    frame = pd.concat([item[0] for item in loaded], ignore_index=True)
    frame = frame.sort_values(["open_time", "source_filename", "source_row"], kind="mergesort").reset_index(drop=True)
    duplicate_mask = frame.duplicated("open_time", keep=False)
    equivalent = 0
    for timestamp, group in frame.loc[duplicate_mask].groupby("open_time", sort=False):
        first_values = group.iloc[0][OHLCV].to_numpy()
        if not (group[OHLCV].to_numpy() == first_values).all():
            details = group[["source_filename", "source_row", *OHLCV]].to_dict("records")
            raise IngestionError(f"conflicting duplicate at {timestamp.isoformat()}: {details}")
        equivalent += len(group) - 1
    # This is not blind deduplication: all duplicate groups were validated above,
    # and stable provenance ordering explicitly selects their canonical row.
    result = frame.loc[~frame.duplicated("open_time", keep="first")].reset_index(drop=True)
    result["gap_from_previous"] = result.open_time.diff() > pd.Timedelta(minutes=1 if timeframe == "M1" else 5)
    result["is_weekend"] = result.open_time.dt.dayofweek >= 5
    return LoadResult(result, [item[1] for item in loaded], len(frame), equivalent)
