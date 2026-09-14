"""Fail-closed lookup for BBW effective-dated instrument metadata.

This module performs metadata/calendar mapping only.  It deliberately has no
dependency on indicators, aggregation, strategy, trades, or performance code.
"""
from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo

VALID_STATUSES = {"VERIFIED", "EFFECTIVE_DATED_VERIFIED", "REQUIRES_CONFIRMATION", "REQUIRES_USER_INPUT", "UNRESOLVED"}
AUTOPROLONG_SERIES = "exchange_perpetual_daily_autoprolong"


class MetadataLookupError(ValueError):
    """Raised rather than guessing when metadata does not cover an instant."""


def load_metadata(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_metadata(data)
    return data


def _instant(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError(f"effective instant lacks offset: {value}")
    return parsed


def _date(value: str) -> date:
    return date.fromisoformat(value)


def _assert_contiguous(regimes: list[dict[str, Any]], *, instants: bool) -> None:
    previous = None
    for regime in regimes:
        start = _instant(regime["effective_from"]) if instants else _date(regime["effective_from"])
        end = _instant(regime["effective_to"]) if instants else _date(regime["effective_to"])
        if start >= end or (previous is not None and start != previous):
            raise ValueError("regimes must be ordered, nonempty, and contiguous")
        previous = end


def validate_metadata(data: dict[str, Any]) -> None:
    if data.get("schema_version") != "bbw.instrument-metadata.v2" or data.get("symbol") != "CNYRUBF":
        raise ValueError("not the CNYRUBF v2 metadata passport")
    sources = data.get("evidence", {}).get("sources", {})
    if not sources:
        raise ValueError("evidence registry is required")
    for source in sources.values():
        if not all(source.get(k) for k in ("title", "url", "evidence_type", "notes")):
            raise ValueError("incomplete evidence record")
    for section in (data["identity"], data["time_semantics"]):
        for field in section.values():
            if field["status"] not in VALID_STATUSES or not all(k in field for k in ("value", "effective_from", "effective_to", "source_id")):
                raise ValueError("incomplete frozen field")
            if field["source_id"] not in sources:
                raise ValueError("unknown evidence source")
    regimes = data["metadata_regimes"]
    _assert_contiguous(regimes["ticks"], instants=True)
    _assert_contiguous(regimes["sessions"], instants=False)
    _assert_contiguous(regimes["trading_date_assignment"], instants=True)
    if data["identity"]["series_type"]["value"] != AUTOPROLONG_SERIES:
        raise ValueError("CNYRUBF must retain explicit exchange auto-prolongation semantics")
    if data["rollover"]["synthetic_rollovers"] or data["rollover"]["source_partitions_are_rollovers"]:
        raise ValueError("source partitions cannot create CNYRUBF rollover events")


def _lookup_instant(regimes: list[dict[str, Any]], when: datetime) -> dict[str, Any]:
    if when.tzinfo is None:
        raise MetadataLookupError("timezone-aware timestamp required")
    matches = [r for r in regimes if _instant(r["effective_from"]) <= when < _instant(r["effective_to"])]
    if len(matches) != 1:
        raise MetadataLookupError(f"no unique metadata regime for {when.isoformat()}")
    return matches[0]


def tick_at(metadata: dict[str, Any], when: datetime) -> dict[str, Any]:
    return _lookup_instant(metadata["metadata_regimes"]["ticks"], when)


def session_on(metadata: dict[str, Any], day: date) -> dict[str, Any]:
    regimes = metadata["metadata_regimes"]["sessions"]
    matches = [r for r in regimes if _date(r["effective_from"]) <= day < _date(r["effective_to"])]
    if len(matches) != 1:
        raise MetadataLookupError(f"no unique weekday session regime for {day.isoformat()}")
    return matches[0]


def weekend_session_on(metadata: dict[str, Any], day: date) -> dict[str, Any]:
    matches = [r for r in metadata["metadata_regimes"]["weekend_sessions"] if _date(r["effective_from"]) <= day < _date(r["effective_to"])]
    if len(matches) != 1:
        raise MetadataLookupError(f"no unique weekend session regime for {day.isoformat()}")
    return matches[0]


def _next_working_day(day: date, nonworking_dates: set[date]) -> date:
    candidate = day + timedelta(days=1)
    while candidate.weekday() >= 5 or candidate in nonworking_dates:
        candidate += timedelta(days=1)
    return candidate


def trading_date_for(metadata: dict[str, Any], when: datetime, *, nonworking_dates: Iterable[date] | None = None) -> date:
    """Map a Moscow timestamp; callers must supply the versioned holiday set.

    An empty set is sufficient only for dates known not to encounter a holiday.
    This explicit argument prevents a silent ``timestamp.date()`` fallback.
    """
    if nonworking_dates is None:
        raise MetadataLookupError("authoritative nonworking_dates calendar is required")
    zone = ZoneInfo(metadata["time_semantics"]["exchange_timezone"]["value"])
    if when.tzinfo is None:
        raise MetadataLookupError("timezone-aware timestamp required")
    local = when.astimezone(zone)
    regime = _lookup_instant(metadata["metadata_regimes"]["trading_date_assignment"], local)
    blocked = set(nonworking_dates)
    if local.weekday() >= 5:
        weekend_session_on(metadata, local.date())
        candidate = local.date()
        while candidate.weekday() >= 5 or candidate in blocked:
            candidate += timedelta(days=1)
        return candidate
    if regime["weekday_rule"] == "evening_from_19:05_to_next_working_day" and local.timetz().replace(tzinfo=None) >= time(19, 5):
        return _next_working_day(local.date(), blocked)
    if local.date() in blocked:
        raise MetadataLookupError("timestamp falls on nonworking date without special-session evidence")
    return local.date()
