"""Empirical, read-only temporal alignment audit for frozen Finam OHLCV.

The routines in this module never normalize, repair, fill, or persist market
data.  A conclusion is deliberately ``UNRESOLVED`` unless the supplied bars
distinguish the competing timestamp conventions.
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass, asdict
from datetime import date
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from .data_freeze import resolve_identity
from .data_pipeline import file_sha256, read_source
from .instrument_metadata import (MetadataLookupError, load_metadata, session_on,
                                  trading_date_for, weekend_session_on)

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


@dataclass(frozen=True)
class FrozenCalendar:
    """Validated, externally supplied exchange-calendar snapshot.

    ``days`` is keyed by the wall-clock calendar date.  There is intentionally
    no method that manufactures an entry for a missing date.
    """

    path: str
    artifact_id: str
    source_url: str
    retrieved_at: str
    days: Mapping[date, Mapping[str, Any]]


CALENDAR_DAY_FIELDS = {"calendar_date", "trading_date", "working_day",
                       "weekend_session", "special_session", "shortened_session",
                       "exchange_regime", "trading_intervals", "clearing_intervals"}


def load_frozen_calendar(path: str | Path) -> FrozenCalendar:
    """Load a complete, provenance-bearing calendar artifact, fail closed.

    Dates and session properties are accepted only as explicit artifact data;
    weekdays and absent values are never used as defaults.
    """
    source = Path(path)
    data = json.loads(source.read_text(encoding="utf-8"))
    if data.get("schema_version") != "bbw.moex-calendar.v1":
        raise TemporalAlignmentError("unsupported frozen calendar schema")
    if not all(isinstance(data.get(key), str) and data[key] for key in
               ("artifact_id", "source_url", "retrieved_at")):
        raise TemporalAlignmentError("frozen calendar provenance is incomplete")
    records = data.get("days")
    if not isinstance(records, list) or not records:
        raise TemporalAlignmentError("frozen calendar contains no days")
    days: dict[date, Mapping[str, Any]] = {}
    for position, record in enumerate(records):
        if not isinstance(record, dict) or CALENDAR_DAY_FIELDS - record.keys():
            raise TemporalAlignmentError(f"frozen calendar day {position} is incomplete")
        try:
            calendar_day = date.fromisoformat(record["calendar_date"])
            date.fromisoformat(record["trading_date"])
        except (TypeError, ValueError) as exc:
            raise TemporalAlignmentError(f"invalid frozen calendar date at day {position}") from exc
        for field in ("working_day", "weekend_session", "special_session", "shortened_session"):
            if type(record[field]) is not bool:
                raise TemporalAlignmentError(f"frozen calendar {field} must be boolean")
        if not isinstance(record["exchange_regime"], str) or not record["exchange_regime"]:
            raise TemporalAlignmentError("frozen calendar exchange_regime is required")
        for field in ("trading_intervals", "clearing_intervals"):
            intervals = record[field]
            if not isinstance(intervals, list) or any(not isinstance(pair, list) or len(pair) != 2 for pair in intervals):
                raise TemporalAlignmentError(f"invalid frozen calendar {field}")
        if calendar_day in days:
            raise TemporalAlignmentError(f"duplicate frozen calendar date: {calendar_day}")
        days[calendar_day] = record
    return FrozenCalendar(str(source.resolve()), data["artifact_id"], data["source_url"],
                          data["retrieved_at"], days)


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


def validate_sessions(frame: pd.DataFrame, metadata: dict[str, Any],
                      calendar: FrozenCalendar | None = None) -> list[dict[str, Any]]:
    """Diagnose each observed date against effective-dated session metadata."""
    bars = _bars(frame)
    rows = []
    for day, group in bars.groupby(bars.timestamp.dt.date, sort=True):
        minute = group.timestamp.dt.hour * 60 + group.timestamp.dt.minute
        try:
            if calendar is None or day not in calendar.days:
                raise MetadataLookupError(f"frozen calendar has no entry for {day.isoformat()}")
            calendar_day = calendar.days[day]
            regime = weekend_session_on(metadata, day) if day.weekday() >= 5 else session_on(metadata, day)
            intervals = calendar_day["trading_intervals"]
            if calendar_day["exchange_regime"] != regime["id"]:
                raise MetadataLookupError("calendar/metadata exchange regime mismatch")
            def clock(value: str) -> int:
                hour, mins = map(int, value.split(":")); return hour * 60 + mins
            inside = pd.Series(False, index=group.index)
            for start, end in intervals:
                inside |= minute.between(clock(start), clock(end), inclusive="left")
            clearing = pd.Series(False, index=group.index)
            for start, end in calendar_day["clearing_intervals"]:
                clearing |= minute.between(clock(start), clock(end), inclusive="left")
            expected_first = clock(intervals[0][0])
            expected_last = clock(intervals[-1][1]) - 1
            first_minute, last_minute = int(minute.iloc[0]), int(minute.iloc[-1])
            boundaries_match = first_minute == expected_first and last_minute == expected_last
            rows.append({"date": day.isoformat(), "regime": regime["id"], "bar_count": len(group),
                "first_timestamp": str(group.timestamp.iloc[0]), "last_timestamp": str(group.timestamp.iloc[-1]),
                "expected_first_time": intervals[0][0],
                "expected_last_time": f"{expected_last // 60:02d}:{expected_last % 60:02d}",
                "first_boundary_match": first_minute == expected_first,
                "last_boundary_match": last_minute == expected_last,
                "outside_session_count": int((~inside).sum()), "clearing_bar_count": int(clearing.sum()),
                "weekend": day.weekday() >= 5, "working_day": calendar_day["working_day"],
                "weekend_session": calendar_day["weekend_session"], "special_session": calendar_day["special_session"],
                "shortened_session": calendar_day["shortened_session"], "trading_date": calendar_day["trading_date"],
                "status": "PASS" if inside.all() and not clearing.any() and boundaries_match else "FAIL"})
        except Exception as exc:
            rows.append({"date": day.isoformat(), "regime": "UNRESOLVED", "bar_count": len(group),
                "first_timestamp": str(group.timestamp.iloc[0]), "last_timestamp": str(group.timestamp.iloc[-1]),
                "outside_session_count": None, "clearing_bar_count": None, "weekend": day.weekday() >= 5,
                "status": "UNRESOLVED", "reason": str(exc)})
    return rows


def assign_trading_dates(frame: pd.DataFrame, metadata: dict[str, Any],
                         calendar: FrozenCalendar | None) -> dict[str, Any]:
    """Assign exchange trading dates only with an explicit frozen calendar.

    Naive Finam wall-clock labels are interpreted in the metadata's exchange
    timezone.  No weekday/holiday fallback is made when calendar evidence is
    absent.
    """
    bars = _bars(frame)
    if calendar is None:
        return {"status": "UNRESOLVED", "reason": "authoritative frozen exchange calendar is missing",
                "trading_dates": None, "weekday_evening_bars": 0, "weekend_bars": 0}
    assigned = []
    try:
        for stamp in bars.timestamp:
            day = stamp.date()
            if day not in calendar.days:
                raise MetadataLookupError(f"frozen calendar has no entry for {day.isoformat()}")
            record = calendar.days[day]
            # Metadata lookup is still mandatory, including weekend availability
            # and both effective-dated trading-date regime transitions.
            zone = metadata["time_semantics"]["exchange_timezone"]["value"]
            aware = stamp.tz_localize(zone).to_pydatetime()
            if day.weekday() >= 5:
                weekend_session_on(metadata, day)
                if not record["weekend_session"]:
                    raise MetadataLookupError("weekend bar lacks calendar weekend-session evidence")
            else:
                trading_date_for(metadata, aware, nonworking_dates=set())
            assigned.append(date.fromisoformat(record["trading_date"]))
    except (MetadataLookupError, ValueError) as exc:
        return {"status": "UNRESOLVED", "reason": str(exc), "trading_dates": None,
                "weekday_evening_bars": 0, "weekend_bars": 0}
    evening = (bars.timestamp.dt.weekday < 5) & (bars.timestamp.dt.time >= pd.Timestamp("19:05").time())
    weekend = bars.timestamp.dt.weekday >= 5
    return {"status": "PASS", "reason": "assigned exclusively from effective-dated metadata and frozen calendar",
            "trading_dates": pd.Series(assigned), "weekday_evening_bars": int(evening.sum()),
            "weekend_bars": int(weekend.sum())}


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


def validate_h1(m1: pd.DataFrame, h1: pd.DataFrame, semantics: str,
                metadata: dict[str, Any] | None = None,
                calendar: FrozenCalendar | None = None) -> dict[str, Any]:
    result = compare_aggregation(m1, h1, "H1", semantics)
    aggregate = aggregate_m1(m1, "H1", semantics)
    incomplete = []
    bars = _bars(m1)
    # Every observed bucket is checked; this necessarily includes both dataset
    # edges, where a matching but partial M1/H1 pair must not pass silently.
    for bucket in aggregate.itertuples():
        start = bucket.timestamp
        expected_minutes = pd.date_range(start, periods=60, freq="min")
        if metadata is not None:
            try:
                day = start.date()
                if calendar is None or day not in calendar.days:
                    raise MetadataLookupError(f"frozen calendar has no entry for {day}")
                regime = calendar.days[day]
                def inside(stamp: pd.Timestamp) -> bool:
                    clock = stamp.strftime("%H:%M")
                    return any(begin <= clock < end for begin, end in regime["trading_intervals"])
                expected_minutes = pd.DatetimeIndex([stamp for stamp in expected_minutes if inside(stamp)])
            except MetadataLookupError:
                expected_minutes = pd.DatetimeIndex([])
        observed = pd.DatetimeIndex(bars.loc[(bars.timestamp >= start) &
            (bars.timestamp < start + pd.Timedelta(hours=1)), "timestamp"])
        if expected_minutes.empty or not observed.equals(expected_minutes):
            incomplete.append(str(start))
    return {"H1_ALIGNMENT": "PASS" if result.matches and not incomplete else "FAIL",
            "comparison": asdict(result), "incomplete_h1_bars": incomplete,
            "future_filled_count": int((_bars(h1).timestamp > _bars(m1).timestamp.max()).sum())}


def load_frozen_datasets(manifest_path: str | Path, metadata_path: str | Path,
                         symbol: str = "CNYRUBF") -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
    """Load only raw files named by a manifest, after verifying every hash."""
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8")); metadata = load_metadata(metadata_path)
    datasets: dict[str, list[pd.DataFrame]] = {}
    symbol = symbol.upper()
    records = manifest.get("instruments", {}).get(symbol, {})
    entries_by_timeframe = {}
    for timeframe in ("M1", "M5", "M15", "M30", "H1", "D1"):
        entries = records.get(timeframe, [])
        if not entries:
            raise TemporalAlignmentError(f"frozen raw dataset missing: {symbol} {timeframe}")
        entries_by_timeframe[timeframe] = entries
        for entry in entries:
            path = Path(entry["source_path"])
            if not path.is_file() or file_sha256(path) != entry["source_sha256"]:
                raise TemporalAlignmentError(f"source missing or hash changed: {path}")
    # No market-data file is opened until the complete bundle has passed hash
    # verification.  This prevents a partially verified audit.
    for timeframe, entries in entries_by_timeframe.items():
        for entry in entries:
            path = Path(entry["source_path"])
            raw, info = read_source(path)
            identity = resolve_identity(path, raw, info, {symbol: metadata})
            if identity["detected_symbol"] != symbol or identity["detected_timeframe"] != timeframe:
                raise TemporalAlignmentError(f"frozen identity mismatch: {path}")
            datasets.setdefault(timeframe, []).append(raw)
    result = {key: _bars(pd.concat(parts, ignore_index=True)) for key, parts in datasets.items()}
    if any(frame.empty for frame in result.values()):
        raise TemporalAlignmentError("frozen raw dataset is empty")
    return result, metadata


def write_evidence(output: str | Path, document: dict[str, Any], mtf: list[dict[str, Any]],
                   sessions: list[dict[str, Any]], report: str) -> None:
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    (output / "TEMPORAL_ALIGNMENT.json").write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for filename, rows in (("MTF_ALIGNMENT.csv", mtf), ("SESSION_ALIGNMENT.csv", sessions)):
        fields = sorted({key for row in rows for key in row})
        with (output / filename).open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n"); writer.writeheader(); writer.writerows(rows)
    (output / "TEMPORAL_ALIGNMENT_REPORT.md").write_text(report.rstrip() + "\n", encoding="utf-8")
