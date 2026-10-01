"""Order-incapable collector for FINAM schedule/H1 time-model evidence.

The output is an intentionally narrow, public-market-time projection.  Real
timing evidence is external operational evidence and must never be committed
or otherwise copied into this repository checkout.  Authentication material,
account identifiers, prices, quantities and every other response field are
discarded.
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from .finam_api import FinamAPI
from .readonly_supervisor import MODE, _authenticated_registry

EVIDENCE_SCHEMA = "finam-h1-market-time-evidence-v1"
ALLOWED_SESSION_KEYS = frozenset({"type", "start_time", "end_time"})
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_OUTPUT_FORBIDDEN = "H1_TIMING_EVIDENCE_REPOSITORY_OUTPUT_FORBIDDEN"


class DiagnosticSafetyFault(RuntimeError):
    pass


def validated_external_output(output: Path) -> Path:
    """Return a canonical output path, failing closed for this checkout."""
    repository = REPOSITORY_ROOT.resolve()
    destination = output.expanduser().resolve()
    if destination == repository or repository in destination.parents:
        raise DiagnosticSafetyFault(REPOSITORY_OUTPUT_FORBIDDEN)
    return destination


def _observed(clock: Callable[[], datetime]) -> str:
    value = clock()
    if value.tzinfo is None:
        raise DiagnosticSafetyFault("DIAGNOSTIC_CLOCK_MUST_BE_AWARE")
    return value.astimezone(timezone.utc).isoformat()


def _sessions(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or not isinstance(payload.get("sessions"), list):
        raise DiagnosticSafetyFault("SCHEDULE_RESPONSE_MALFORMED")
    clean=[]
    for row in payload["sessions"]:
        interval=row.get("interval") if isinstance(row, dict) else None
        if not isinstance(interval, dict):
            raise DiagnosticSafetyFault("SCHEDULE_RESPONSE_MALFORMED")
        clean.append({"type": row.get("type"), "start_time": interval.get("start_time"),
                      "end_time": interval.get("end_time")})
    return clean


def _bar_timestamps(payload: Any) -> list[Any]:
    if not isinstance(payload, dict) or not isinstance(payload.get("bars"), list):
        raise DiagnosticSafetyFault("BARS_RESPONSE_MALFORMED")
    result=[]
    for bar in payload["bars"]:
        if not isinstance(bar, dict) or "timestamp" not in bar:
            raise DiagnosticSafetyFault("BARS_RESPONSE_MALFORMED")
        result.append(bar["timestamp"])
    return result


def collect(api: Any, *, clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
            lookback_days: int = 10) -> dict[str, Any]:
    """Collect all N4 evidence using only session creation, schedule and bars."""
    if not 2 <= lookback_days <= 31:
        raise ValueError("LOOKBACK_DAYS_OUT_OF_RANGE")
    api.create_session()
    symbols=_authenticated_registry()
    rows=[]
    for research_symbol in sorted(symbols):
        symbol=symbols[research_symbol]
        schedule=api.schedule(symbol)
        schedule_observed_at=_observed(clock)
        schedule_server_timestamp=getattr(api, "last_server_timestamp", None)
        end=clock()
        if end.tzinfo is None:
            raise DiagnosticSafetyFault("DIAGNOSTIC_CLOCK_MUST_BE_AWARE")
        bars=api.bars(symbol, (end-timedelta(days=lookback_days)).isoformat(), end.isoformat())
        rows.append({
            "symbol": symbol,
            "sessions": _sessions(schedule),
            "h1_timestamps": _bar_timestamps(bars),
            "schedule_observed_at": schedule_observed_at,
            "schedule_server_timestamp": schedule_server_timestamp,
            "bars_observed_at": _observed(clock),
            "bars_server_timestamp": getattr(api, "last_server_timestamp", None),
        })
    return {"schema": EVIDENCE_SCHEMA, "mode": MODE, "instruments": rows,
            "contains_account_data": False, "contains_credentials": False,
            "order_capable_calls": False}


def main(argv: list[str] | None = None) -> int:
    parser=argparse.ArgumentParser(description="Sanitized REAL_READONLY FINAM H1 timing evidence")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--lookback-days", type=int, default=10)
    args=parser.parse_args(argv)
    try:
        output=validated_external_output(args.output)
    except (OSError, RuntimeError):
        raise SystemExit(REPOSITORY_OUTPUT_FORBIDDEN) from None
    if os.environ.get("FINAM_MODE") != MODE:
        raise SystemExit("FINAM_REAL_READONLY_MODE_REQUIRED")
    if os.environ.get("NEW_ENTRIES_DISABLED", "").lower() != "true":
        raise SystemExit("NEW_ENTRIES_DISABLED_REQUIRED")
    secret=os.environ.get("FINAM_API_SECRET", "")
    if not secret:
        raise SystemExit("FINAM_API_SECRET_MISSING")
    evidence=collect(FinamAPI(secret), lookback_days=args.lookback_days)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
