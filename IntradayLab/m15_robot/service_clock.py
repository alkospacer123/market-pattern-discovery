"""Isolated, offline-only M15 polling clock and completed-close watermark.

Adapted from inspected H1 production_service / InstanceLock, without H1
imports, broker access, credentials, order paths, tasks, or LIVE ability.
Input is an injected, already-authorized iterable of CLOSE-MSK timestamps:
this module cannot promote raw FINAM opens to verified completed bars.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import threading
from typing import Callable, Iterable
from zoneinfo import ZoneInfo

from .spec import INSTRUMENTS, TIMEFRAME_MINUTES

MSK = ZoneInfo("Europe/Moscow")
POLL_SECONDS = 30
_LOCK_GUARD = threading.Lock()
_PROCESS_LOCKS: set[str] = set()


class M15ClockError(RuntimeError):
    pass


class M15SingleInstance:
    """H1-style advisory OS lock; no deleting another process' lock file."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.stream = None

    def __enter__(self):
        if self.path.is_symlink() or self.path.parent.is_symlink():
            raise M15ClockError("M15_LOCK_SYMLINK_FORBIDDEN")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        key = str(self.path.resolve())
        with _LOCK_GUARD:
            if key in _PROCESS_LOCKS:
                raise M15ClockError("M15_SECOND_PROCESS_REFUSED")
            stream = self.path.open("a+b")
            try:
                if os.name == "nt":
                    import msvcrt
                    stream.seek(0)
                    stream.write(b"0")
                    stream.flush()
                    stream.seek(0)
                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except (OSError, IOError):
                stream.close()
                raise M15ClockError("M15_SECOND_PROCESS_REFUSED") from None
            self.stream = stream
            _PROCESS_LOCKS.add(key)
        return self

    def __exit__(self, *_):
        key = str(self.path.resolve())
        try:
            if self.stream is not None:
                if os.name == "nt":
                    import msvcrt
                    self.stream.seek(0)
                    msvcrt.locking(self.stream.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(self.stream.fileno(), fcntl.LOCK_UN)
                self.stream.close()
        finally:
            self.stream = None
            with _LOCK_GUARD:
                _PROCESS_LOCKS.discard(key)


def _stamp(dt: datetime) -> str:
    if not isinstance(dt, datetime) or dt.tzinfo is None or dt.utcoffset() is None:
        raise M15ClockError("M15_COMPLETED_CLOSE_TIMEZONE_REQUIRED")
    local = dt.astimezone(MSK)
    if local.minute % TIMEFRAME_MINUTES or local.second or local.microsecond:
        raise M15ClockError("M15_COMPLETED_CLOSE_GRID_INVALID")
    return dt.astimezone(timezone.utc).isoformat()


def _atomic_json(path: Path, payload: dict) -> None:
    if path.is_symlink():
        raise M15ClockError("M15_SERVICE_STATE_SYMLINK_FORBIDDEN")
    temp = path.with_name(path.name + ".pending")
    if temp.exists() or temp.is_symlink():
        raise M15ClockError("M15_SERVICE_PENDING_STATE_EXISTS")
    try:
        with temp.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


class M15OfflineClock:
    """No real broker, signal calculator, or trade callbacks: clocks only."""

    def __init__(self, *, root: Path, completed: Callable[[str, datetime], Iterable[datetime]],
                 clock: Callable[[], datetime], poll_seconds: int = POLL_SECONDS):
        if not callable(completed) or not callable(clock):
            raise M15ClockError("M15_INJECTED_READSIDE_REQUIRED")
        if not isinstance(poll_seconds, int) or not 1 <= poll_seconds <= 900:
            raise M15ClockError("M15_POLL_INTERVAL_INVALID")
        self.root = Path(root).resolve()
        self.state = self.root / "state"
        self.state.mkdir(parents=True, exist_ok=True)
        self._path = self.state / "m15-offline-service-clock.json"
        self._heartbeat = self.state / "m15-offline-service-heartbeat.json"
        self.lock_path = self.state / "m15-offline-service.lock"
        self.completed = completed
        self.clock = clock
        self.poll_seconds = poll_seconds

    def lock(self):
        return M15SingleInstance(self.lock_path)

    def _read_watermarks(self) -> dict[str, str]:
        if not self._path.exists():
            return {}
        if self._path.is_symlink():
            raise M15ClockError("M15_SERVICE_STATE_SYMLINK_FORBIDDEN")
        try:
            state = json.loads(self._path.read_text(encoding="utf-8"))
            if state.get("schema") != "M15_OFFLINE_CLOCK_V1" or not isinstance(state.get("watermarks"), dict):
                raise ValueError("schema")
            watermarks = state["watermarks"]
            if not set(watermarks).issubset(set(INSTRUMENTS)):
                raise ValueError("symbols")
            for value in watermarks.values():
                if not isinstance(value, str) or _stamp(datetime.fromisoformat(value)) != value:
                    raise ValueError("times")
            return watermarks
        except (ValueError, TypeError, KeyError):
            raise M15ClockError("M15_SERVICE_WATERMARK_INVALID") from None

    def _cycle(self) -> dict:
        """Internal only; caller holds the exclusive instance lock."""
        now = self.clock()
        if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
            raise M15ClockError("M15_SERVICE_CLOCK_INVALID")
        old = self._read_watermarks()
        updated = old.copy()
        advanced: list[dict] = []
        now_utc = now.astimezone(timezone.utc)
        for symbol in INSTRUMENTS:
            received = self.completed(symbol, now)
            if not isinstance(received, (list, tuple)):
                raise M15ClockError("M15_COMPLETED_SERIES_REQUIRED")
            last = datetime.fromisoformat(old[symbol]) if symbol in old else None
            previous = None
            for close in received:
                stamp = _stamp(close)
                current = datetime.fromisoformat(stamp)
                if current > now_utc:
                    raise M15ClockError("M15_FUTURE_CLOSE_REFUSED")
                if previous is not None and current <= previous:
                    raise M15ClockError("M15_UNSORTED_OR_DUPLICATE_CLOSE")
                previous = current
                if last is not None and current <= last:
                    continue
                advanced.append({"instrument": symbol, "close_utc": stamp})
                updated[symbol] = stamp
        _atomic_json(self._path, {"schema": "M15_OFFLINE_CLOCK_V1", "watermarks": updated})
        _atomic_json(self._heartbeat, {
            "status": "HEALTHY_OFFLINE_NO_TRADING", "observed_utc": now_utc.isoformat(),
            "advanced": len(advanced), "watermarks": updated,
            "live_authorized": False,
        })
        return {"status": "HEALTHY_OFFLINE_NO_TRADING", "advanced": advanced,
                "watermarks": updated, "live_authorized": False}

    def once(self) -> dict:
        with self.lock():
            return self._cycle()

    def simulate(self, polls: int, sleeper: Callable[[int], None]) -> list[dict]:
        if not isinstance(polls, int) or polls < 1 or not callable(sleeper):
            raise M15ClockError("M15_SIMULATION_ARGUMENT_INVALID")
        result = []
        with self.lock():
            for i in range(polls):
                result.append(self._cycle())
                if i != polls - 1:
                    sleeper(self.poll_seconds)
        return result
