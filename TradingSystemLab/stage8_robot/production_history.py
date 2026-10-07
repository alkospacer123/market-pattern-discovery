"""Frozen Stage 8.12.4 H1 warm-up seed plus live FINAM splice.

FINAM documents only 30 days of H1 historical depth. Frozen T3/H1 needs a much
longer validity-based context warm-up, so production seeds from the exact N4 H1
files already recorded by the Stage 5 TRAIL1 authority, then appends current
FINAM completed H1 bars. The common interval must match exactly; production
never repairs, fills, or silently prefers one source over the other.
"""
from __future__ import annotations

import csv
import hashlib
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import pandas as pd

from .finam_api import completed_h1_bars
from .instrument_resolver import N4, parse_rest_value_object

MOSCOW = "Europe/Moscow"
STAGE5_DATA_COMMIT = "50f1fd2178c18b7ab3bd969be82ad01f47a34745"
SEED_FILES = {
    "USDRUBF": "forever/USDRUBF/USDRUBF_H1.csv",
    "CNYRUBF": "forever/CNYRUBF/CNYRUBF_H1.csv",
    "GLDRUBF": "forever/GLDRUBF/GLDRUBF_H1.csv",
    "IMOEXF": "forever/IMOEXF/IMOEXF_H1.csv",
}
SEED_SHA256 = {
    "USDRUBF": "f0ca366d816a6213742271242e87c53d1e23f5a5fc4655df0123217df418a226",
    "CNYRUBF": "a3815b88a11aa5878b8bd104140f002859349c2c8d7f6ff0476a0d4c4d9a612e",
    "GLDRUBF": "12a626ba6cc47fce2f392d4a6ce3bdb8a3c1aad074306a73ab480fcfbb83b87e",
    "IMOEXF": "119878c12f602924296ab27b5b9f3cf51fa54f1a9370793892edbea58003e110",
}
OHLC = ("Open", "High", "Low", "Close")
CONTINUATION_SCHEMA = "stage8_12_4_h1_continuation.v1"


class ProductionHistoryError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _decimal(value: Any, code: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ProductionHistoryError(code) from None
    if not result.is_finite() or result <= 0:
        raise ProductionHistoryError(code)
    return result


def _validated_frame(
    rows: list[tuple[pd.Timestamp, Decimal, Decimal, Decimal, Decimal]],
    *,
    source_code: str,
) -> pd.DataFrame:
    if not rows:
        raise ProductionHistoryError(f"{source_code}_EMPTY")
    stamps = pd.DatetimeIndex([row[0] for row in rows], name="OpenTime")
    if stamps.tz is None or str(stamps.tz) != MOSCOW:
        raise ProductionHistoryError(f"{source_code}_TIMEZONE_INVALID")
    if stamps.has_duplicates or not stamps.is_monotonic_increasing:
        raise ProductionHistoryError(f"{source_code}_TIMESTAMP_ORDER_INVALID")
    values = [row[1:] for row in rows]
    frame = pd.DataFrame(values, index=stamps, columns=OHLC, dtype=object)
    if any(
        high < max(open_, close, low) or low > min(open_, close, high)
        for open_, high, low, close in values
    ):
        raise ProductionHistoryError(f"{source_code}_OHLC_INVALID")
    return frame


def load_stage5_seed_open_h1(data_root: Path | str, instrument: str) -> pd.DataFrame:
    if instrument not in N4:
        raise ProductionHistoryError("STAGE8_12_4_SEED_INSTRUMENT_NOT_N4")
    root = Path(data_root).resolve()
    source = (root / SEED_FILES[instrument]).resolve()
    if root not in source.parents or not source.is_file() or source.is_symlink():
        raise ProductionHistoryError("STAGE8_12_4_SEED_FILE_INVALID")
    if _sha256(source) != SEED_SHA256[instrument]:
        raise ProductionHistoryError("STAGE8_12_4_SEED_SHA256_MISMATCH")
    rows: list[tuple[pd.Timestamp, Decimal, Decimal, Decimal, Decimal]] = []
    try:
        with source.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream, delimiter=";")
            if reader.fieldnames != ["Datetime", "Open", "High", "Low", "Close", "Volume"]:
                raise ProductionHistoryError("STAGE8_12_4_SEED_SCHEMA_INVALID")
            previous: pd.Timestamp | None = None
            for raw in reader:
                stamp = pd.Timestamp(raw["Datetime"])
                if stamp.tzinfo is not None:
                    stamp = stamp.tz_convert(MOSCOW)
                else:
                    stamp = stamp.tz_localize(MOSCOW, ambiguous="raise", nonexistent="raise")
                if previous is not None and stamp <= previous:
                    raise ProductionHistoryError("STAGE8_12_4_SEED_TIMESTAMP_ORDER_INVALID")
                previous = stamp
                rows.append((
                    stamp,
                    _decimal(raw["Open"], "STAGE8_12_4_SEED_OHLC_INVALID"),
                    _decimal(raw["High"], "STAGE8_12_4_SEED_OHLC_INVALID"),
                    _decimal(raw["Low"], "STAGE8_12_4_SEED_OHLC_INVALID"),
                    _decimal(raw["Close"], "STAGE8_12_4_SEED_OHLC_INVALID"),
                ))
    except (OSError, csv.Error) as exc:
        raise ProductionHistoryError("STAGE8_12_4_SEED_READ_FAILED") from exc
    return _validated_frame(rows, source_code="STAGE8_12_4_SEED")


def finam_completed_open_h1(
    response: dict[str, Any],
    observed_at,
    trading_windows,
) -> pd.DataFrame:
    """Return the full completed FINAM H1 lookback, not only today's session.

    FINAM's schedule endpoint supplies the current trading-day authority, while
    the H1 endpoint supplies up to 30 days of historical bars. Historical rows
    before the current schedule day are necessarily complete at observed_at and
    are retained for the pinned-seed overlap. Rows in the current schedule day
    are accepted only when completed_h1_bars proves them complete.
    """
    if (
        not isinstance(response, dict)
        or not isinstance(response.get("bars"), list)
        or not isinstance(trading_windows, list)
    ):
        raise ProductionHistoryError("STAGE8_12_4_FINAM_H1_INVALID")
    try:
        observed = pd.Timestamp(observed_at)
        if observed.tzinfo is None:
            raise ValueError
        observed_utc = observed.tz_convert("UTC")
        current_scope_start = observed_utc.normalize()
        if trading_windows:
            current_scope_start = pd.Timestamp(trading_windows[0][0]).tz_convert("UTC").normalize()
        current_completed = completed_h1_bars(response, observed_at, trading_windows)
    except (TypeError, ValueError) as exc:
        raise ProductionHistoryError("STAGE8_12_4_FINAM_H1_INVALID") from exc

    completed_current_by_open: dict[pd.Timestamp, dict[str, Any]] = {}
    for bar in current_completed:
        try:
            stamp = pd.Timestamp(bar["timestamp"]).tz_convert("UTC")
        except Exception:
            raise ProductionHistoryError("STAGE8_12_4_FINAM_H1_INVALID") from None
        if stamp in completed_current_by_open:
            raise ProductionHistoryError("STAGE8_12_4_FINAM_H1_INVALID")
        completed_current_by_open[stamp] = bar

    selected: list[dict[str, Any]] = []
    seen: set[pd.Timestamp] = set()
    previous: pd.Timestamp | None = None
    for raw in response["bars"]:
        if not isinstance(raw, dict) or not isinstance(raw.get("timestamp"), str):
            raise ProductionHistoryError("STAGE8_12_4_FINAM_H1_INVALID")
        try:
            stamp = pd.Timestamp(raw["timestamp"])
            if stamp.tzinfo is None:
                raise ValueError
            stamp = stamp.tz_convert("UTC")
        except Exception:
            raise ProductionHistoryError("STAGE8_12_4_FINAM_H1_INVALID") from None
        if stamp.minute or stamp.second or stamp.microsecond:
            raise ProductionHistoryError("STAGE8_12_4_FINAM_H1_INVALID")
        if stamp in seen or (previous is not None and stamp <= previous):
            raise ProductionHistoryError("STAGE8_12_4_FINAM_H1_INVALID")
        seen.add(stamp)
        previous = stamp

        if stamp < current_scope_start:
            if stamp >= observed_utc:
                raise ProductionHistoryError("STAGE8_12_4_FINAM_H1_INVALID")
            selected.append(raw)
            continue

        # Today's rows must belong to a validated current schedule window.
        in_window = any(
            pd.Timestamp(start).tz_convert("UTC") <= stamp
            < pd.Timestamp(end).tz_convert("UTC")
            for start, end in trading_windows
        )
        if not in_window:
            raise ProductionHistoryError("STAGE8_12_4_FINAM_H1_OUTSIDE_CURRENT_SCHEDULE")
        completed = completed_current_by_open.get(stamp)
        if completed is not None:
            selected.append(completed)
        # A current in-window row absent from completed_current_by_open is the
        # still-forming H1 bar and is deliberately excluded.

    rows: list[tuple[pd.Timestamp, Decimal, Decimal, Decimal, Decimal]] = []
    for bar in selected:
        try:
            stamp = pd.Timestamp(bar["timestamp"])
            if stamp.tzinfo is None:
                raise ValueError
            stamp = stamp.tz_convert(MOSCOW)
            rows.append((
                stamp,
                parse_rest_value_object(bar["open"], positive=True),
                parse_rest_value_object(bar["high"], positive=True),
                parse_rest_value_object(bar["low"], positive=True),
                parse_rest_value_object(bar["close"], positive=True),
            ))
        except (KeyError, TypeError, ValueError):
            raise ProductionHistoryError("STAGE8_12_4_FINAM_H1_INVALID") from None
    return _validated_frame(rows, source_code="STAGE8_12_4_FINAM_H1")


def _splice_authority_and_finam_open_h1(
    authority: pd.DataFrame,
    live: pd.DataFrame,
) -> pd.DataFrame:
    """Extend frozen authority while allowing FINAM to omit historical bars.

    The Stage-5/persisted authority remains canonical. FINAM may be a sparse
    historical subset inside the overlap, but it may not introduce a timestamp
    absent from authority, every common OHLC row must match exactly, and the
    most recent authority timestamp inside the overlap must be present as the
    exact splice seam.
    """
    if authority.empty or live.empty:
        raise ProductionHistoryError("STAGE8_12_4_H1_SPLICE_EMPTY")
    if authority.index.tz is None or live.index.tz is None:
        raise ProductionHistoryError("STAGE8_12_4_H1_SPLICE_TIMEZONE_INVALID")
    authority = authority.sort_index(kind="mergesort")
    live = live.sort_index(kind="mergesort")
    if authority.index.has_duplicates or live.index.has_duplicates:
        raise ProductionHistoryError("STAGE8_12_4_H1_SPLICE_DUPLICATE")
    if live.index.min() > authority.index.max():
        raise ProductionHistoryError("STAGE8_12_4_H1_SPLICE_NO_OVERLAP")

    overlap_start = live.index.min()
    overlap_end = min(authority.index.max(), live.index.max())
    authority_overlap = authority.loc[
        (authority.index >= overlap_start) & (authority.index <= overlap_end)
    ]
    live_overlap = live.loc[
        (live.index >= overlap_start) & (live.index <= overlap_end)
    ]
    if authority_overlap.empty or live_overlap.empty:
        raise ProductionHistoryError("STAGE8_12_4_H1_SPLICE_NO_OVERLAP")

    unexpected_live = live_overlap.index.difference(authority_overlap.index)
    if len(unexpected_live):
        raise ProductionHistoryError("STAGE8_12_4_H1_SPLICE_TIMESTAMP_MISMATCH")

    seam = authority_overlap.index.max()
    if seam not in live_overlap.index:
        raise ProductionHistoryError("STAGE8_12_4_H1_SPLICE_TIMESTAMP_MISMATCH")

    for stamp in live_overlap.index:
        for column in OHLC:
            if authority_overlap.at[stamp, column] != live_overlap.at[stamp, column]:
                raise ProductionHistoryError("STAGE8_12_4_H1_SPLICE_OHLC_MISMATCH")

    appended = live.loc[live.index > authority.index.max()]
    merged = pd.concat([authority, appended])
    if merged.index.has_duplicates or not merged.index.is_monotonic_increasing:
        raise ProductionHistoryError("STAGE8_12_4_H1_SPLICE_ORDER_INVALID")
    return merged


def splice_seed_and_finam_open_h1(
    seed: pd.DataFrame,
    live: pd.DataFrame,
) -> pd.DataFrame:
    """Compatibility wrapper for the original pinned-seed bootstrap contract."""
    return _splice_authority_and_finam_open_h1(seed, live)


def _bars_sha256(bars: list[dict[str, str]]) -> str:
    canonical = json.dumps(
        bars, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _continuation_bars(frame: pd.DataFrame) -> list[dict[str, str]]:
    if frame.empty:
        return []
    if frame.index.tz is None or str(frame.index.tz) != MOSCOW:
        raise ProductionHistoryError(
            "STAGE8_12_4_H1_CONTINUATION_TIMEZONE_INVALID"
        )
    if frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
        raise ProductionHistoryError(
            "STAGE8_12_4_H1_CONTINUATION_TIMESTAMP_ORDER_INVALID"
        )
    bars: list[dict[str, str]] = []
    for stamp, row in frame.iterrows():
        values = {
            name: _decimal(
                row[name], "STAGE8_12_4_H1_CONTINUATION_OHLC_INVALID"
            )
            for name in OHLC
        }
        if (
            values["High"] < max(values["Open"], values["Close"], values["Low"])
            or values["Low"] > min(
                values["Open"], values["Close"], values["High"]
            )
        ):
            raise ProductionHistoryError(
                "STAGE8_12_4_H1_CONTINUATION_OHLC_INVALID"
            )
        bars.append({
            "timestamp": stamp.isoformat(),
            "open": str(values["Open"]),
            "high": str(values["High"]),
            "low": str(values["Low"]),
            "close": str(values["Close"]),
        })
    return bars


def continuation_payload_from_frame(
    frame: pd.DataFrame,
    instrument: str,
) -> dict[str, Any]:
    if instrument not in N4:
        raise ProductionHistoryError(
            "STAGE8_12_4_H1_CONTINUATION_INSTRUMENT_NOT_N4"
        )
    bars = _continuation_bars(frame)
    return {
        "schema": CONTINUATION_SCHEMA,
        "instrument": instrument,
        "stage5_data_commit": STAGE5_DATA_COMMIT,
        "seed_sha256": SEED_SHA256[instrument],
        "bars_sha256": _bars_sha256(bars),
        "bars": bars,
    }


def load_continuation_open_h1(
    payload: Any,
    instrument: str,
    seed: pd.DataFrame,
) -> pd.DataFrame:
    empty = pd.DataFrame(
        index=pd.DatetimeIndex([], tz=MOSCOW, name="OpenTime"),
        columns=OHLC,
        dtype=object,
    )
    if payload is None:
        return empty
    expected_keys = {
        "schema",
        "instrument",
        "stage5_data_commit",
        "seed_sha256",
        "bars_sha256",
        "bars",
    }
    if (
        not isinstance(payload, dict)
        or set(payload) != expected_keys
        or payload.get("schema") != CONTINUATION_SCHEMA
        or payload.get("instrument") != instrument
        or payload.get("stage5_data_commit") != STAGE5_DATA_COMMIT
        or payload.get("seed_sha256") != SEED_SHA256.get(instrument)
        or not isinstance(payload.get("bars"), list)
        or payload.get("bars_sha256") != _bars_sha256(payload.get("bars", []))
    ):
        raise ProductionHistoryError(
            "STAGE8_12_4_H1_CONTINUATION_INTEGRITY_INVALID"
        )

    bars = payload["bars"]
    if not bars:
        return empty

    rows: list[tuple[pd.Timestamp, Decimal, Decimal, Decimal, Decimal]] = []
    for bar in bars:
        if not isinstance(bar, dict) or set(bar) != {
            "timestamp", "open", "high", "low", "close"
        }:
            raise ProductionHistoryError(
                "STAGE8_12_4_H1_CONTINUATION_INTEGRITY_INVALID"
            )
        try:
            stamp = pd.Timestamp(bar["timestamp"])
            if stamp.tzinfo is None:
                raise ValueError
            stamp = stamp.tz_convert(MOSCOW)
        except Exception:
            raise ProductionHistoryError(
                "STAGE8_12_4_H1_CONTINUATION_INTEGRITY_INVALID"
            ) from None
        rows.append((
            stamp,
            _decimal(bar["open"], "STAGE8_12_4_H1_CONTINUATION_OHLC_INVALID"),
            _decimal(bar["high"], "STAGE8_12_4_H1_CONTINUATION_OHLC_INVALID"),
            _decimal(bar["low"], "STAGE8_12_4_H1_CONTINUATION_OHLC_INVALID"),
            _decimal(bar["close"], "STAGE8_12_4_H1_CONTINUATION_OHLC_INVALID"),
        ))
    frame = _validated_frame(
        rows, source_code="STAGE8_12_4_H1_CONTINUATION"
    )
    if seed.empty or frame.index.min() <= seed.index.max():
        raise ProductionHistoryError(
            "STAGE8_12_4_H1_CONTINUATION_OVERLAPS_SEED"
        )
    return frame


def extend_rolling_open_h1(
    seed: pd.DataFrame,
    persisted_payload: Any,
    live: pd.DataFrame,
    instrument: str,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Extend Stage-5 + persisted FINAM H1 without ever rewriting prior bars."""
    continuation = load_continuation_open_h1(
        persisted_payload, instrument, seed
    )
    authority = (
        seed.copy()
        if continuation.empty
        else pd.concat([seed, continuation])
    )
    if authority.index.has_duplicates or not authority.index.is_monotonic_increasing:
        raise ProductionHistoryError(
            "STAGE8_12_4_H1_CONTINUATION_ORDER_INVALID"
        )

    merged = _splice_authority_and_finam_open_h1(authority, live)
    new_continuation = merged.loc[merged.index > seed.index.max()]
    new_payload = continuation_payload_from_frame(
        new_continuation, instrument
    )

    if persisted_payload is not None:
        old_bars = persisted_payload.get("bars")
        if (
            not isinstance(old_bars, list)
            or new_payload["bars"][: len(old_bars)] != old_bars
        ):
            raise ProductionHistoryError(
                "STAGE8_12_4_H1_CONTINUATION_APPEND_ONLY_VIOLATION"
            )
    return merged, new_payload


def close_index_for_frozen_t3(open_h1: pd.DataFrame) -> pd.DataFrame:
    if open_h1.empty or open_h1.index.tz is None:
        raise ProductionHistoryError("STAGE8_12_4_H1_CLOSE_INDEX_INVALID")
    closed = open_h1.copy()
    closed.index = closed.index + pd.Timedelta("1h")
    closed.index.name = "CloseTime"
    closed = closed.astype(float)
    if not closed.index.is_monotonic_increasing or closed.index.has_duplicates:
        raise ProductionHistoryError("STAGE8_12_4_H1_CLOSE_INDEX_INVALID")
    return closed
