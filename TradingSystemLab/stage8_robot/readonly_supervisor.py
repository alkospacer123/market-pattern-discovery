"""Continuous, order-incapable FINAM REAL_READONLY operational observer.

This module deliberately does not import the broker or runner.  It authenticates
the frozen production identity, observes account cleanliness and completed N4 H1
bars, and writes only operational continuity state.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import os
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from .account_cleanliness import count_active_orders, count_nonzero_positions
from .finam_api import FinamAPI, completed_h1_bars
from .operations import InstanceLock, configure_operational_log, write_heartbeat
from .specification import ACTIVE_IDENTITY, INSTRUMENTS, PRODUCTION_SPECIFICATION_ID, load_frozen_specification

MODE = "REAL_READONLY"
REGISTRY = Path(__file__).with_name("production_instrument_registry.csv")
POLL_MIN_SECONDS = 30
POLL_MAX_SECONDS = 3600
DEFAULT_POLL_SECONDS = 300
DEFAULT_MAX_FAILURES = 5
DEFAULT_BACKOFF_SECONDS = 30
EXPECTED_BINDINGS = {
    "USDRUBF": ("USDRUBF@RTSX", "3447194"),
    "CNYRUBF": ("CNYRUBF@RTSX", "3447192"),
    "GLDRUBF": ("GLDRUBF@RTSX", "4454911"),
    "IMOEXF": ("IMOEXF@RTSX", "4631091"),
}
STALE_DATA_CODE = "STALE_COMPLETED_H1_DATA"
WATERMARK_UNAVAILABLE_CODE = "H1_EXPECTED_COMPLETED_WATERMARK_UNAVAILABLE"
OFF_GRID_H1_OPEN_CODE = "H1_BAR_OPEN_NOT_WHOLE_HOUR_UTC"
TRADING_SESSION_TYPES = frozenset({"EARLY_TRADING", "CORE_TRADING", "LATE_TRADING"})
NON_TRADING_SESSION_TYPES = frozenset({"OPENING_AUCTION", "CLEARING", "CLOSED"})


class SafetyFault(RuntimeError):
    """A sanitized fail-closed condition safe to place in logs/heartbeats."""

    def __init__(self, code: str, *, unresolved_order_count: int = 0):
        super().__init__(code)
        self.unresolved_order_count = unresolved_order_count


class OperationalState:
    """Small transactional store containing no strategy, order, or equity state."""

    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("CREATE TABLE IF NOT EXISTS operational_state(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
        self.db.commit()

    def get(self, key: str, default: str | None = None) -> str | None:
        row = self.db.execute("SELECT value FROM operational_state WHERE key=?", (key,)).fetchone()
        return row[0] if row else default

    def put_many(self, values: dict[str, str]) -> None:
        with self.db:
            self.db.executemany(
                "INSERT INTO operational_state VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                sorted(values.items()),
            )

    def close(self) -> None:
        self.db.close()


def _required_environment(environment: dict[str, str]) -> tuple[str, str]:
    if environment.get("FINAM_MODE") != MODE:
        raise SafetyFault("FINAM_REAL_READONLY_MODE_REQUIRED")
    if environment.get("NEW_ENTRIES_DISABLED", "").lower() != "true":
        raise SafetyFault("NEW_ENTRIES_DISABLED_REQUIRED")
    secret = environment.get("FINAM_API_SECRET", "")
    account = environment.get("FINAM_REAL_ACCOUNT_ID", "")
    if not secret:
        raise SafetyFault("FINAM_API_SECRET_MISSING")
    if not account:
        raise SafetyFault("FINAM_REAL_ACCOUNT_ID_MISSING")
    return secret, account


def _authenticated_registry(path: Path = REGISTRY) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    expected = set(INSTRUMENTS)
    if (
        len(rows) != 4
        or {row.get("research_symbol") for row in rows} != expected
        or any(row.get("binding_status") != "AUTHENTICATED_REAL_READONLY" for row in rows)
        or any(row.get("trading_status") != "TRADABLE" for row in rows)
        or any(row.get("mic") != "RTSX" for row in rows)
        or any((row.get("finam_symbol"), row.get("security_id")) != EXPECTED_BINDINGS.get(row.get("research_symbol")) for row in rows)
    ):
        raise SafetyFault("REAL_REGISTRY_NOT_FOUR_AUTHENTICATED_TRADABLE_RTSX")
    return {row["research_symbol"]: row["finam_symbol"] for row in rows}


def _session_is_safe(details: dict, account: str) -> None:
    if details.get("readonly") is not True:
        raise SafetyFault("REAL_TOKEN_NOT_READONLY")
    if account not in {str(value) for value in details.get("account_ids", [])}:
        raise SafetyFault("CONFIGURED_REAL_ACCOUNT_NOT_ENUMERATED")


def _utc_timestamp(value: Any) -> datetime:
    """Parse a FINAM schedule timestamp without guessing a timezone."""
    if not isinstance(value, str):
        raise SafetyFault("H1_FRESHNESS_SCHEDULE_INVALID")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise SafetyFault("H1_FRESHNESS_SCHEDULE_INVALID") from None
    if parsed.tzinfo is None:
        raise SafetyFault("H1_FRESHNESS_SCHEDULE_INVALID")
    return parsed.astimezone(timezone.utc)


def trading_h1_windows(schedule: Any) -> list[tuple[datetime, datetime]]:
    """Validate a schedule and merge touching FINAM trading intervals."""
    if not isinstance(schedule, dict) or not isinstance(schedule.get("sessions"), list):
        raise SafetyFault("H1_FRESHNESS_SCHEDULE_INVALID")
    intervals = []
    for session in schedule["sessions"]:
        if not isinstance(session, dict) or not isinstance(session.get("interval"), dict):
            raise SafetyFault("H1_FRESHNESS_SCHEDULE_INVALID")
        session_type = session.get("type")
        if session_type not in TRADING_SESSION_TYPES | NON_TRADING_SESSION_TYPES:
            raise SafetyFault("H1_FRESHNESS_SCHEDULE_INVALID")
        interval = session["interval"]
        start = _utc_timestamp(interval.get("start_time"))
        end = _utc_timestamp(interval.get("end_time"))
        if end <= start:
            raise SafetyFault("H1_FRESHNESS_SCHEDULE_INVALID")
        if session_type in TRADING_SESSION_TYPES:
            if start.minute or start.second or start.microsecond or end.second or end.microsecond:
                raise SafetyFault("H1_FRESHNESS_SCHEDULE_INVALID")
            intervals.append((start, end))
    windows: list[tuple[datetime, datetime]] = []
    for start, end in sorted(intervals):
        if windows and start < windows[-1][1]:
            raise SafetyFault("H1_FRESHNESS_SCHEDULE_INVALID")
        if windows and start == windows[-1][1]:
            windows[-1] = (windows[-1][0], end)
        else:
            windows.append((start, end))
    return windows


def newest_expected_h1_close(schedule: Any, observed_at: datetime) -> datetime | None:
    """Return the raw open of the newest schedule-proven completed H1 bar."""
    now = observed_at.astimezone(timezone.utc)
    expected: datetime | None = None
    for start, end in trading_h1_windows(schedule):
        candidate = start
        while candidate < end and min(candidate + timedelta(hours=1), end) <= now:
            expected = candidate if expected is None or candidate > expected else expected
            candidate += timedelta(hours=1)
    return expected


class ReadonlySupervisor:
    def __init__(
        self,
        runtime_root: Path,
        api,
        account: str,
        symbols: dict[str, str],
        *,
        poll_seconds: int = DEFAULT_POLL_SECONDS,
        max_failures: int = DEFAULT_MAX_FAILURES,
        backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
        clock: Callable[[], datetime] | None = None,
        sleeper: Callable[[float], None] = time.sleep,
    ):
        if not POLL_MIN_SECONDS <= poll_seconds <= POLL_MAX_SECONDS:
            raise ValueError("POLL_SECONDS_OUT_OF_RANGE")
        if max_failures < 1 or backoff_seconds < 0:
            raise ValueError("RETRY_CONFIGURATION_INVALID")
        self.root = Path(runtime_root)
        for name in ("state", "audit", "logs", "diagnostics", "backups"):
            (self.root / name).mkdir(parents=True, exist_ok=True)
        self.api = api
        self.account = account
        self.account_hash = hashlib.sha256(account.encode()).hexdigest()
        self.symbols = symbols
        self.poll_seconds = poll_seconds
        self.max_failures = max_failures
        self.backoff_seconds = backoff_seconds
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.sleeper = sleeper
        self.logger = configure_operational_log(self.root / "logs" / "stage8-readonly.log")
        self.heartbeat_path = self.root / "diagnostics" / "stage8-heartbeat.json"
        self.state = OperationalState(self.root / "state" / "readonly-supervisor.sqlite3")
        self.cycle_count = int(self.state.get("cycle_count", "0") or "0")
        self.consecutive_failures = int(self.state.get("consecutive_failures", "0") or "0")

    def close(self) -> None:
        self.state.close()
        for handler in self.logger.handlers:
            handler.flush()
            handler.close()
        self.logger.handlers.clear()

    def authenticate(self) -> None:
        self.api.create_session()
        _session_is_safe(self.api.session_details(), self.account)

    def _heartbeat(self, *, healthy: bool, code: str | None = None, unresolved: int = 0) -> None:
        watermarks = [self.state.get(f"h1:{name}") for name in INSTRUMENTS]
        common = min(watermarks) if all(watermarks) else None
        write_heartbeat(
            self.heartbeat_path,
            mode=MODE,
            production_id=PRODUCTION_SPECIFICATION_ID,
            account_hash=self.account_hash,
            last_completed_h1=common,
            last_api_contact=self.state.get("last_api_contact"),
            reconciliation_status="PASS" if healthy else "FAULT",
            entries_enabled=False,
            unresolved_order_count=unresolved,
            health_status="HEALTHY" if healthy else "UNHEALTHY",
            failure_code=code,
            consecutive_failures=self.consecutive_failures,
            cycle_count=self.cycle_count,
        )

    def cycle(self) -> None:
        now = self.clock().astimezone(timezone.utc)
        _session_is_safe(self.api.session_details(), self.account)
        account_data = self.api.account(self.account)
        if account_data.get("status") not in {"ACCOUNT_ACTIVE", "ACCOUNT_STATUS_ACTIVE"}:
            raise SafetyFault("REAL_ACCOUNT_NOT_ACTIVE")
        positions = account_data.get("positions")
        try:
            nonzero_positions = count_nonzero_positions(positions)
        except ValueError:
            raise SafetyFault("REAL_POSITIONS_SCHEMA_INVALID") from None
        if nonzero_positions:
            raise SafetyFault("UNEXPECTED_BROKER_POSITION")
        orders_data = self.api.orders(self.account)
        orders = orders_data.get("orders", orders_data if isinstance(orders_data, list) else None)
        try:
            active_orders = count_active_orders(orders)
        except ValueError:
            raise SafetyFault("REAL_ORDERS_SCHEMA_INVALID") from None
        if active_orders:
            raise SafetyFault("UNEXPECTED_ACTIVE_ORDER", unresolved_order_count=active_orders)

        updates: dict[str, str] = {}
        # Retain the broad observation window for continuity across closures; the
        # schedule below determines whether a newer completed candle is due.
        start = (now - timedelta(days=30)).isoformat()
        for name in INSTRUMENTS:
            symbol = self.symbols.get(name)
            if symbol is None:
                raise SafetyFault("N4_MARKET_DATA_REQUIRED")
            schedule = self.api.schedule(symbol)
            windows = trading_h1_windows(schedule)
            response = self.api.bars(symbol, start, now.isoformat())
            try:
                bars = completed_h1_bars(response, now, windows)
                raw_opens = {_utc_timestamp(bar["timestamp"]) for bar in response.get("bars", [])}
            except ValueError as exc:
                if str(exc) == OFF_GRID_H1_OPEN_CODE:
                    raise SafetyFault(OFF_GRID_H1_OPEN_CODE) from None
                raise SafetyFault("H1_BARS_SCHEMA_INVALID") from None
            except TypeError:
                raise SafetyFault("H1_BARS_SCHEMA_INVALID") from None
            derived = newest_expected_h1_close(schedule, now)
            prior_expected_text = self.state.get(f"expected_h1:{name}")
            prior_expected = _utc_timestamp(prior_expected_text) if prior_expected_text else None
            expected = max(derived, prior_expected) if derived is not None and prior_expected is not None else derived or prior_expected
            if expected is None:
                raise SafetyFault(WATERMARK_UNAVAILABLE_CODE)
            if expected not in raw_opens:
                raise SafetyFault(STALE_DATA_CODE)
            completed_opens = {_utc_timestamp(bar["timestamp"]) for bar in bars}
            if derived is not None and derived not in completed_opens:
                raise SafetyFault(STALE_DATA_CODE)
            updates[f"h1:{name}"] = expected.isoformat()
            updates[f"expected_h1:{name}"] = expected.isoformat()
        contact = now.isoformat()
        self.cycle_count += 1
        self.consecutive_failures = 0
        updates.update({"cycle_count": str(self.cycle_count), "consecutive_failures": "0",
                        "last_api_contact": contact, "last_reconciliation": "PASS",
                        "last_clean_account_observation": contact})
        self.state.put_many(updates)
        self._heartbeat(healthy=True)
        self.logger.info("READONLY_CYCLE_PASS cycle=%d instruments=4", self.cycle_count)

    def run(self, *, once: bool = False) -> int:
        while True:
            try:
                self.cycle()
            except SafetyFault as exc:
                code = str(exc)
                self.consecutive_failures += 1
                self.state.put_many({"consecutive_failures": str(self.consecutive_failures),
                                     "last_reconciliation": "FAULT"})
                self._heartbeat(healthy=False, code=code, unresolved=exc.unresolved_order_count)
                self.logger.error("READONLY_SAFETY_FAULT code=%s", code)
                return 1
            except Exception:
                self.consecutive_failures += 1
                self.state.put_many({"consecutive_failures": str(self.consecutive_failures),
                                     "last_reconciliation": "FAULT"})
                code = "FINAM_OPERATIONAL_CYCLE_FAILED"
                self._heartbeat(healthy=False, code=code)
                self.logger.warning("READONLY_TRANSIENT_FAILURE code=%s consecutive=%d", code, self.consecutive_failures)
                if once or self.consecutive_failures >= self.max_failures:
                    return 1
                self.sleeper(min(self.backoff_seconds * (2 ** (self.consecutive_failures - 1)), 300))
                continue
            if once:
                return 0
            self.sleeper(self.poll_seconds)


def run_from_environment(
    runtime_root: Path,
    *,
    once: bool = False,
    poll_seconds: int = DEFAULT_POLL_SECONDS,
    api_factory=FinamAPI,
    environment: dict[str, str] | None = None,
    clock: Callable[[], datetime] | None = None,
) -> int:
    environment = dict(os.environ if environment is None else environment)
    lock = InstanceLock(Path(runtime_root) / "state" / "stage8-readonly.lock")
    lock.acquire()
    supervisor = None
    try:
        secret, account = _required_environment(environment)
        spec = load_frozen_specification()
        if spec.identity != ACTIVE_IDENTITY or spec.production_id != PRODUCTION_SPECIFICATION_ID:
            raise SafetyFault("STAGE7_PRODUCTION_IDENTITY_NOT_AUTHENTIC")
        symbols = _authenticated_registry()
        supervisor = ReadonlySupervisor(runtime_root, api_factory(secret), account, symbols,
                                        poll_seconds=poll_seconds, clock=clock)
        supervisor.authenticate()
        return supervisor.run(once=once)
    finally:
        if supervisor is not None:
            supervisor.close()
        lock.release()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Continuous FINAM REAL_READONLY operational supervisor")
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--poll-seconds", type=int, default=DEFAULT_POLL_SECONDS)
    args = parser.parse_args(argv)
    try:
        return run_from_environment(args.runtime_root, once=args.once, poll_seconds=args.poll_seconds)
    except (SafetyFault, RuntimeError, ValueError) as exc:
        code = str(exc)
        if code not in {
            "FINAM_REAL_READONLY_MODE_REQUIRED", "NEW_ENTRIES_DISABLED_REQUIRED", "FINAM_API_SECRET_MISSING",
            "FINAM_REAL_ACCOUNT_ID_MISSING", "SECOND_ROBOT_INSTANCE_BLOCKED", "POLL_SECONDS_OUT_OF_RANGE",
            "REAL_REGISTRY_NOT_FOUR_AUTHENTICATED_TRADABLE_RTSX", "STAGE7_PRODUCTION_IDENTITY_NOT_AUTHENTIC",
        }:
            code = "READONLY_SUPERVISOR_STARTUP_FAILED"
        print(code)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
