"""Signed temporal protocol and audited access guards (no market-data reads)."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
PROTOCOL_PATH = ROOT / "config" / "research_protocol_v1.json"
DEFAULT_RESEARCH_SEED = 20260401

class AccessMode(StrEnum):
    DESCRIPTIVE_DEVELOPMENT = "DESCRIPTIVE_DEVELOPMENT"
    DISCOVERY = "DISCOVERY"
    INTERNAL_CONFIRMATION = "INTERNAL_CONFIRMATION"
    TRUE_OOS = "TRUE_OOS"

def canonical_bytes(protocol: dict[str, Any]) -> bytes:
    return json.dumps(protocol, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()

def protocol_signature(protocol: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(protocol)).hexdigest()

def load_protocol(path: Path = PROTOCOL_PATH) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if value["default_seed"] != DEFAULT_RESEARCH_SEED:
        raise ValueError("default research seed drift")
    return value

def _dt(value: str | datetime) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else value
    if parsed.tzinfo is None:
        raise ValueError("timestamps must be timezone-aware")
    return parsed.astimezone(timezone.utc)

def _period(period: tuple[str | datetime, str | datetime]) -> tuple[datetime, datetime]:
    start, end = map(_dt, period)
    if start >= end:
        raise ValueError("period must be non-empty and chronological")
    return start, end

def assert_discovery_period(period: tuple[str | datetime, str | datetime], protocol: dict | None = None) -> None:
    p = protocol or load_protocol(); start, end = _period(period); window = p["discovery_period"]
    if start < _dt(window["start_utc"]) or end > _dt(window["end_utc_exclusive"]):
        raise PermissionError("DISCOVERY access intersects non-discovery data")

def assert_confirmation_not_accessed(mode: AccessMode, period: tuple[str | datetime, str | datetime], protocol: dict | None = None) -> None:
    if mode is AccessMode.DISCOVERY:
        assert_discovery_period(period, protocol)

def assert_true_oos_not_accessed(period: tuple[str | datetime, str | datetime], protocol: dict | None = None) -> None:
    p = protocol or load_protocol(); start, end = _period(period)
    year = p["true_oos_year"]
    sealed_start = datetime(year, 1, 1, tzinfo=timezone.utc)
    sealed_end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    if start < sealed_end and end > sealed_start:
        raise PermissionError("2025 TRUE OOS is sealed")

def request_access(mode: AccessMode, period: tuple[str | datetime, str | datetime], *, candidate: dict | None = None,
                   experiment_id: str | None = None, audit_path: Path | None = None, protocol: dict | None = None) -> None:
    """Authorize an explicit mode and audit every confirmation/OOS attempt."""
    p = protocol or load_protocol(); approved = False; reason = ""
    try:
        start, end = _period(period)
        if mode is AccessMode.DISCOVERY:
            assert_discovery_period(period, p)
        elif mode is AccessMode.DESCRIPTIVE_DEVELOPMENT:
            if start < _dt(p["discovery_period"]["start_utc"]) or end > _dt(p["internal_confirmation_period"]["end_utc_exclusive"]):
                raise PermissionError("descriptive mode is limited to approved 2026 development coverage")
        elif mode is AccessMode.INTERNAL_CONFIRMATION:
            if not candidate or candidate.get("status") not in {"frozen_for_confirmation", "internally_confirmed", "internally_rejected"} or not candidate.get("frozen_definition"):
                raise PermissionError("internal confirmation requires a frozen candidate")
            window = p["internal_confirmation_period"]
            if start < _dt(window["start_utc"]) or end > _dt(window["end_utc_exclusive"]):
                raise PermissionError("internal confirmation mode is limited to its frozen period")
        else:
            if not candidate or candidate.get("status") != "frozen_for_true_oos":
                raise PermissionError("TRUE OOS requires frozen_for_true_oos candidate")
            if start.year != p["true_oos_year"] or end.year != p["true_oos_year"]:
                raise PermissionError("TRUE OOS mode is limited to calendar year 2025")
        approved = True; reason = "protocol requirements satisfied"
    except Exception as exc:
        reason = str(exc)
        raise
    finally:
        if mode in {AccessMode.INTERNAL_CONFIRMATION, AccessMode.TRUE_OOS}:
            path = audit_path or ROOT / "results" / "research_access_audit.jsonl"
            path.parent.mkdir(parents=True, exist_ok=True)
            record = {"timestamp": datetime.now(timezone.utc).isoformat(), "experiment_id": experiment_id,
                      "candidate_id": candidate.get("candidate_id") if candidate else None, "access_mode": mode.value,
                      "requested_period": [str(period[0]), str(period[1])], "approved": approved, "reason": reason}
            with path.open("a") as stream: stream.write(json.dumps(record, sort_keys=True) + "\n")

def deterministic_seed() -> int:
    return DEFAULT_RESEARCH_SEED
