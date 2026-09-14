"""Empirical, read-only temporal alignment audit for frozen Finam OHLCV.

The routines in this module never normalize, repair, fill, or persist market
data.  A conclusion is deliberately ``UNRESOLVED`` unless the supplied bars
distinguish the competing timestamp conventions.
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from .data_freeze import resolve_identity
from .data_pipeline import file_sha256, read_source
from .instrument_metadata import load_metadata, session_on, weekend_session_on

INTRADAY = {"M5": "5min", "M15": "15min", "M30": "30min", "H1": "1h"}
OHLCV = ("open", "high", "low", "close", "volume")


class TemporalAlignmentError(ValueError):
    """Raised when immutable inputs cannot safely support an audit."""


@dataclass(frozen=True)
class AlignmentResult:
    timeframe: str
    semantics: str
    matches: bool
    checked_bars: int
    mismatch_count: int
    missing_aggregate_count: int
    missing_reference_count: int


def _bars(frame: pd.DataFrame) -> pd.DataFrame:
    missing = {"timestamp", *OHLCV} - set(frame.columns)
    if missing:
        raise TemporalAlignmentError(f"missing raw columns: {sorted(missing)}")
    out = frame[["timestamp", *OHLCV]].copy()
    out["timestamp"] = pd.to_datetime(out["timestamp"], errors="coerce")
    for column in OHLCV:
        out[column] = pd.to_numeric(out[column], errors="coerce")
    if out.isna().any().any() or out.timestamp.duplicated().any():
        raise TemporalAlignmentError("unparseable or duplicate frozen bars")
    return out.sort_values("timestamp", kind="stable").reset_index(drop=True)


def aggregate_m1(frame: pd.DataFrame, timeframe: str, semantics: str) -> pd.DataFrame:
    """Aggregate without filling gaps; labels implement the two hypotheses."""
    if timeframe not in INTRADAY or semantics not in {"START", "END"}:
        raise TemporalAlignmentError("unsupported timeframe or timestamp semantics")
    bars = _bars(frame)
    frequency = INTRADAY[timeframe]
    labels = bars.timestamp.dt.floor(frequency) if semantics == "START" else bars.timestamp.dt.ceil(frequency)
    bars = bars.assign(_label=labels)
    grouped = bars.groupby("_label", sort=True, observed=True)
    result = grouped.agg(open=("open", "first"), high=("high", "max"), low=("low", "min"),
                         close=("close", "last"), volume=("volume", "sum"), source_bar_count=("timestamp", "size"))
    return result.rename_axis("timestamp").reset_index()


def compare_aggregation(m1: pd.DataFrame, reference: pd.DataFrame, timeframe: str,
                        semantics: str) -> AlignmentResult:
    aggregate = aggregate_m1(m1, timeframe, semantics)
    target = _bars(reference)
    joined = aggregate.merge(target, on="timestamp", how="outer", suffixes=("_aggregate", "_reference"), indicator=True)
    common = joined._merge.eq("both")
    equal = common.copy()
    for column in OHLCV:
        equal &= joined[f"{column}_aggregate"].eq(joined[f"{column}_reference"])
    mismatches = int((common & ~equal).sum())
    missing_aggregate = int(joined._merge.eq("right_only").sum())
    missing_reference = int(joined._merge.eq("left_only").sum())
    checked = int(common.sum())
    return AlignmentResult(timeframe, semantics,
        bool(checked and not mismatches and not missing_aggregate and not missing_reference),
        checked, mismatches, missing_aggregate, missing_reference)


def infer_timestamp_semantics(m1: pd.DataFrame, references: Mapping[str, pd.DataFrame]) -> dict[str, Any]:
    """Score both hypotheses. A tie, zero evidence, or mixed winners fails closed."""
    evidence: dict[str, list[dict[str, Any]]] = {"START": [], "END": []}
    scores = {"START": 0, "END": 0}
    for semantics in scores:
        for timeframe in sorted(references):
            result = compare_aggregation(m1, references[timeframe], timeframe, semantics)
            evidence[semantics].append(asdict(result))
            scores[semantics] += result.checked_bars - result.mismatch_count - result.missing_aggregate_count - result.missing_reference_count
    winners = [name for name, score in scores.items() if score > 0 and score == max(scores.values())]
    resolved = winners[0] if len(winners) == 1 else "UNRESOLVED"
    return {"timestamp_semantics": resolved, "scores": scores, "evidence": evidence,
            "explanation": "unique positive empirical OHLCV/count score" if resolved != "UNRESOLVED" else "evidence is absent or does not distinguish START from END"}


def validate_sessions(frame: pd.DataFrame, metadata: dict[str, Any]) -> list[dict[str, Any]]:
    """Diagnose each observed date against effective-dated session metadata."""
    bars = _bars(frame)
    rows = []
    for day, group in bars.groupby(bars.timestamp.dt.date, sort=True):
        minute = group.timestamp.dt.hour * 60 + group.timestamp.dt.minute
        try:
            regime = weekend_session_on(metadata, day) if day.weekday() >= 5 else session_on(metadata, day)
            intervals = regime["trading_intervals"]
            def clock(value: str) -> int:
                hour, mins = map(int, value.split(":")); return hour * 60 + mins
            inside = pd.Series(False, index=group.index)
            for start, end in intervals:
                inside |= minute.between(clock(start), clock(end), inclusive="left")
            clearing = pd.Series(False, index=group.index)
            for start, end in regime.get("clearing_intervals", []):
                clearing |= minute.between(clock(start), clock(end), inclusive="left")
            rows.append({"date": day.isoformat(), "regime": regime["id"], "bar_count": len(group),
                "first_timestamp": str(group.timestamp.iloc[0]), "last_timestamp": str(group.timestamp.iloc[-1]),
                "outside_session_count": int((~inside).sum()), "clearing_bar_count": int(clearing.sum()),
                "weekend": day.weekday() >= 5, "status": "PASS" if inside.all() and not clearing.any() else "FAIL"})
        except Exception as exc:
            rows.append({"date": day.isoformat(), "regime": "UNRESOLVED", "bar_count": len(group),
                "first_timestamp": str(group.timestamp.iloc[0]), "last_timestamp": str(group.timestamp.iloc[-1]),
                "outside_session_count": None, "clearing_bar_count": None, "weekend": day.weekday() >= 5,
                "status": "UNRESOLVED", "reason": str(exc)})
    return rows


def validate_daily(intraday: pd.DataFrame, daily: pd.DataFrame,
                   trading_dates: pd.Series | None = None) -> dict[str, Any]:
    """Compare D1 to calendar-date and, when explicitly supplied, trading-date grouping."""
    minute, target = _bars(intraday), _bars(daily)
    candidates: dict[str, pd.Series] = {"CALENDAR_DATE": minute.timestamp.dt.normalize()}
    if trading_dates is not None:
        if len(trading_dates) != len(minute):
            raise TemporalAlignmentError("trading-date assignment length mismatch")
        candidates["TRADING_DATE"] = pd.to_datetime(trading_dates).dt.normalize()
    results = {}
    for name, labels in candidates.items():
        grouped = minute.assign(_label=labels).groupby("_label", sort=True).agg(
            open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"), volume=("volume", "sum"))
        ref = target.assign(timestamp=target.timestamp.dt.normalize()).set_index("timestamp")
        common = grouped.join(ref, how="inner", lsuffix="_aggregate", rsuffix="_reference")
        matches = pd.Series(True, index=common.index)
        for column in OHLCV:
            matches &= common[f"{column}_aggregate"].eq(common[f"{column}_reference"])
        results[name] = {"checked_bars": len(common), "matching_bars": int(matches.sum()),
                         "full_match": bool(len(common) and matches.all() and len(grouped) == len(ref))}
    winners = [name for name, result in results.items() if result["full_match"]]
    return {"daily_bar_semantics": winners[0] if len(winners) == 1 else "UNRESOLVED", "evidence": results}


def validate_h1(m1: pd.DataFrame, h1: pd.DataFrame, semantics: str) -> dict[str, Any]:
    result = compare_aggregation(m1, h1, "H1", semantics)
    aggregate = aggregate_m1(m1, "H1", semantics)
    expected = 60
    # Intraday clearing can make an intentional short bucket.  The dedicated
    # session audit diagnoses those intervals; this safety check is narrowly
    # about truncated coverage at the two dataset edges.
    edges = aggregate.iloc[[0, -1]].drop_duplicates("timestamp") if len(aggregate) else aggregate
    incomplete = edges.loc[edges.source_bar_count.ne(expected), "timestamp"].astype(str).tolist()
    return {"H1_ALIGNMENT": "PASS" if result.matches and not incomplete else "FAIL",
            "comparison": asdict(result), "incomplete_h1_bars": incomplete,
            "future_filled_count": int((_bars(h1).timestamp > _bars(m1).timestamp.max()).sum())}


def load_frozen_datasets(manifest_path: str | Path, metadata_path: str | Path) -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
    """Load only hash-verified raw CNYRUBF files named by a freeze manifest."""
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8")); metadata = load_metadata(metadata_path)
    datasets: dict[str, list[pd.DataFrame]] = {}
    records = manifest.get("instruments", {}).get("CNYRUBF", {})
    for timeframe in ("M1", "M5", "M15", "M30", "H1", "D1"):
        entries = records.get(timeframe, [])
        if not entries:
            raise TemporalAlignmentError(f"frozen raw dataset missing: CNYRUBF {timeframe}")
        for entry in entries:
            path = Path(entry["source_path"])
            if not path.is_file() or file_sha256(path) != entry["source_sha256"]:
                raise TemporalAlignmentError(f"source missing or hash changed: {path}")
            raw, info = read_source(path)
            identity = resolve_identity(path, raw, info, {"CNYRUBF": metadata})
            if identity["detected_symbol"] != "CNYRUBF" or identity["detected_timeframe"] != timeframe:
                raise TemporalAlignmentError(f"frozen identity mismatch: {path}")
            datasets.setdefault(timeframe, []).append(raw)
    return {key: _bars(pd.concat(parts, ignore_index=True)) for key, parts in datasets.items()}, metadata


def write_evidence(output: str | Path, document: dict[str, Any], mtf: list[dict[str, Any]],
                   sessions: list[dict[str, Any]], report: str) -> None:
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    (output / "TEMPORAL_ALIGNMENT.json").write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for filename, rows in (("MTF_ALIGNMENT.csv", mtf), ("SESSION_ALIGNMENT.csv", sessions)):
        fields = sorted({key for row in rows for key in row})
        with (output / filename).open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n"); writer.writeheader(); writer.writerows(rows)
    (output / "TEMPORAL_ALIGNMENT_REPORT.md").write_text(report.rstrip() + "\n", encoding="utf-8")
