"""Deterministic, read-only normalization of the frozen CNYRUBF bundle.

Normalization in this module is deliberately an identity operation on valid
START-labelled OHLCV bars.  It does not apply a calendar, sessions, timezone
conversion, aggregation, or any kind of repair.
"""
from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any

import pandas as pd

from .data_freeze import resolve_identity
from .data_pipeline import file_sha256, read_source
from .instrument_metadata import load_metadata
from .temporal_alignment import TemporalAlignmentError

TIMEFRAMES = ("M1", "M5", "M15", "M30", "H1", "D1")
FREQUENCIES = {"M1": "1min", "M5": "5min", "M15": "15min", "M30": "30min", "H1": "1h", "D1": "1D"}
OHLCV = ("open", "high", "low", "close", "volume")
OUTPUT_COLUMNS = ("timestamp", *OHLCV)
CALENDAR_LIMITATION = (
    "Authoritative MOEX trading calendar is not included. Gap counts are raw "
    "timestamp discontinuities and are not classified as holidays, special "
    "sessions, or expected closures. No calendar rule was inferred."
)


def _manifest_path(root: Path) -> Path:
    for candidate in (root / "FREEZE_MANIFEST.json", root / "evidence" / "FREEZE_MANIFEST.json"):
        if candidate.is_file():
            return candidate
    raise TemporalAlignmentError(f"FREEZE_MANIFEST.json not found under: {root}")


def _csv_bytes(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False, lineterminator="\n", date_format="%Y-%m-%d %H:%M:%S").encode("utf-8")


def _load(freeze_root: Path, metadata_path: Path) -> tuple[dict[str, pd.DataFrame], list[dict[str, Any]]]:
    """Verify the complete bundle before opening any market-data source."""
    manifest = json.loads(_manifest_path(freeze_root).read_text(encoding="utf-8"))
    metadata = load_metadata(metadata_path)
    records = manifest.get("instruments", {}).get("CNYRUBF", {})
    entries: list[tuple[str, dict[str, Any], Path]] = []
    sources: list[dict[str, Any]] = []
    for timeframe in TIMEFRAMES:
        timeframe_entries = records.get(timeframe, [])
        if not timeframe_entries:
            raise TemporalAlignmentError(f"frozen raw dataset missing: CNYRUBF {timeframe}")
        for entry in timeframe_entries:
            path = Path(entry["source_path"])
            expected = entry["source_sha256"]
            if not path.is_file() or file_sha256(path) != expected:
                raise TemporalAlignmentError(f"source missing or hash changed: {path}")
            entries.append((timeframe, entry, path))
            sources.append({"timeframe": timeframe, "path": str(path.resolve()), "sha256": expected})

    parts: dict[str, list[pd.DataFrame]] = {timeframe: [] for timeframe in TIMEFRAMES}
    for timeframe, _entry, path in entries:
        raw, info = read_source(path)
        identity = resolve_identity(path, raw, info, {"CNYRUBF": metadata})
        if identity["detected_symbol"] != "CNYRUBF" or identity["detected_timeframe"] != timeframe:
            raise TemporalAlignmentError(f"frozen identity mismatch: {path}")
        parts[timeframe].append(raw)
    return {key: pd.concat(value, ignore_index=True) for key, value in parts.items()}, sources


def normalize_frame(raw: pd.DataFrame, timeframe: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Return valid bars unchanged in value and label, plus deterministic diagnostics."""
    missing = set(OUTPUT_COLUMNS) - set(raw.columns)
    if missing:
        raise TemporalAlignmentError(f"missing raw columns: {sorted(missing)}")
    work = raw.loc[:, OUTPUT_COLUMNS].copy()
    timestamps = pd.to_datetime(work["timestamp"], errors="coerce")
    numeric = work.loc[:, OHLCV].apply(pd.to_numeric, errors="coerce")
    invalid = timestamps.isna() | numeric.isna().any(axis=1) | numeric["volume"].lt(0)
    invalid |= numeric["high"].lt(numeric[["open", "low", "close"]].max(axis=1))
    invalid |= numeric["low"].gt(numeric[["open", "high", "close"]].min(axis=1))
    duplicate = timestamps.duplicated(keep="first") & ~timestamps.isna()
    rejected = invalid | duplicate
    out = pd.concat([timestamps.rename("timestamp"), numeric], axis=1).loc[~rejected]
    out = out.sort_values("timestamp", kind="stable").reset_index(drop=True)
    # TRUE OOS may not be ingested or normalized, even when accidentally named
    # by a freeze manifest.
    if out["timestamp"].dt.year.eq(2025).any():
        raise TemporalAlignmentError("locked TRUE OOS calendar year 2025 is present")
    delta = out["timestamp"].diff()
    expected = pd.Timedelta(FREQUENCIES[timeframe])
    gaps = []
    for index in out.index[delta.gt(expected)]:
        gaps.append({"previous": out.at[index - 1, "timestamp"].isoformat(),
                     "next": out.at[index, "timestamp"].isoformat(),
                     "elapsed_seconds": int(delta.at[index].total_seconds())})
    diagnostics = {"rows_before": len(raw), "rows_after": len(out),
        "rejected_rows": int(rejected.sum()), "invalid_ohlc_rows": int(invalid.sum()),
        "duplicate_rows": int((duplicate & ~invalid).sum()), "gap_count": len(gaps), "gaps": gaps,
        "first_timestamp": out.timestamp.min().isoformat() if len(out) else None,
        "last_timestamp": out.timestamp.max().isoformat() if len(out) else None}
    return out, diagnostics


def _report(manifest: dict[str, Any]) -> str:
    lines = ["# CNYRUBF normalization report", "", "**Status:** READY", "",
        "Timestamp semantics are **START**. Normalization preserves valid source OHLCV bars and timestamp labels; it performs no filling, interpolation, forward fill, correction, or candle synthesis.", "",
        "## Timeframe coverage", "", "| Timeframe | Rows before | Rows after | Rejected | Duplicates | Gaps | First | Last | SHA-256 |",
        "|---|---:|---:|---:|---:|---:|---|---|---|"]
    for timeframe in TIMEFRAMES:
        row = manifest["timeframes"][timeframe]
        lines.append(f"| {timeframe} | {row['rows_before']} | {row['rows_after']} | {row['rejected_rows']} | {row['duplicate_rows']} | {row['gap_count']} | {row['first_timestamp'] or ''} | {row['last_timestamp'] or ''} | `{row['sha256']}` |")
    lines += ["", "## Source files", ""]
    for source in manifest["source_files"]:
        lines.append(f"- {source['timeframe']}: `{source['path']}` — `{source['sha256']}`")
    lines += ["", "## Trading-calendar limitation", "", CALENDAR_LIMITATION, ""]
    return "\n".join(lines)


def run_normalization(freeze_root: Path, output_root: Path, metadata_path: Path) -> dict[str, Any]:
    raw, sources = _load(freeze_root.resolve(), metadata_path)
    source_hashes = {item["path"]: item["sha256"] for item in sources}
    frames: dict[str, pd.DataFrame] = {}
    diagnostics: dict[str, dict[str, Any]] = {}
    for timeframe in TIMEFRAMES:
        frames[timeframe], diagnostics[timeframe] = normalize_frame(raw[timeframe], timeframe)
        if frames[timeframe].empty:
            raise TemporalAlignmentError(f"no valid rows after normalization: {timeframe}")

    output_root.mkdir(parents=True, exist_ok=True)
    for timeframe in TIMEFRAMES:
        payload = _csv_bytes(frames[timeframe])
        (output_root / f"{timeframe}.csv").write_bytes(payload)
        diagnostics[timeframe].update({"file": f"{timeframe}.csv", "sha256": sha256(payload).hexdigest()})
    if any(file_sha256(path) != expected for path, expected in source_hashes.items()):
        raise TemporalAlignmentError("raw source mutated during normalization")
    manifest = {"schema_version": "bbw.normalized-manifest.v1", "instrument": "CNYRUBF",
        "timestamp_semantics": "START", "deterministic": True, "calendar_limitation": CALENDAR_LIMITATION,
        "source_files": sources, "timeframes": diagnostics}
    (output_root / "NORMALIZED_MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_root / "NORMALIZATION_REPORT.md").write_text(_report(manifest), encoding="utf-8")
    return manifest
