"""Canonical, read-only multi-timeframe Finam CSV loader."""
from __future__ import annotations

from pathlib import Path
import pandas as pd

from .finam import ALIASES, IngestionError, SCHEMA, _read
from .timeframes import timeframe

CANONICAL_COLUMNS = ["timestamp", "symbol", "timeframe", "open", "high", "low", "close", "volume"]


class MarketDataLoader:
    """Load existing bars without resampling or touching source files."""

    def __init__(self, data_root: str | Path) -> None:
        self.data_root = Path(data_root)

    def discover(self, symbol: str, timeframe_id: str) -> tuple[Path, ...]:
        canonical = ALIASES.get(symbol.upper())
        if canonical is None:
            raise IngestionError(f"unsupported ticker/instrument: {symbol}")
        tf = timeframe(timeframe_id)
        folder = "CNY" if canonical == "CNYRUBF" else "Si"
        # Explicit timeframe token prevents M1 from accidentally matching M15.
        paths = sorted((self.data_root / "2026" / folder).glob(f"{folder}_{tf.identifier}_*.csv"))
        if tf.identifier != "D1":
            paths = [path for path in paths if "_2026_Q" in path.name]
        return tuple(path for path in paths if "2025" not in path.name)

    def load(self, symbol: str, timeframe_id: str, paths: tuple[Path, ...] | None = None) -> pd.DataFrame:
        tf = timeframe(timeframe_id)
        canonical = ALIASES.get(symbol.upper())
        if canonical is None:
            raise IngestionError(f"unsupported ticker/instrument: {symbol}")
        selected = paths if paths is not None else self.discover(symbol, tf.identifier)
        if not selected:
            raise IngestionError(f"no source files for {symbol} {tf.identifier}")
        # Canonical research ingestion exposes only the configured development
        # interval, including when a quarterly/archive file straddles its end.
        frames = [_read(Path(path), canonical, tf.identifier,
            development_rows_only=True)[0] for path in selected]
        frame = pd.concat(frames, ignore_index=True).sort_values(
            ["open_time", "source_filename", "source_row"], kind="mergesort")
        duplicate = frame.duplicated("open_time", keep=False)
        if duplicate.any() and frame.loc[duplicate].groupby("open_time")[["open", "high", "low", "close", "volume"]].nunique().gt(1).any().any():
            raise IngestionError("conflicting duplicate timestamps")
        frame = frame.drop_duplicates("open_time", keep="first")
        result = frame.rename(columns={"open_time": "timestamp", "instrument": "symbol"})[CANONICAL_COLUMNS]
        result.attrs["metadata"] = {"source": "Finam CSV", "symbol": canonical,
            "timeframe": tf.identifier, "finam_period": tf.finam_period,
            "open_semantics": tf.open_semantics, "close_semantics": tf.close_semantics,
            "files": [Path(path).name for path in selected]}
        return result.reset_index(drop=True)
