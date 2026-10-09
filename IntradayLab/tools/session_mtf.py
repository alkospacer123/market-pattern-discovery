"""Minimal fail-closed MTF alignment. Standard library only, Python 3.12.

Bars have naive *feed-local* labels; TimestampEvidence must independently
confirm their IANA timezone and start/end meaning. Calendar-date boundaries
alone do not establish exchange trading days. SessionWindow is an explicitly
attested continuous interval, split at clearing, halts and day boundaries.
No inferred historical schedule is supplied as a default.

Decisions are observable at the completed M5 bar's end, never at its label.
This module aligns data; it neither generates signals nor models fills.
"""
from bisect import bisect_left
import io
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import BinaryIO, Iterator, Sequence
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

FIVE = timedelta(minutes=5)


def bounded_lines(raw: BinaryIO, count: int, max_line_bytes: int = 4096) -> Iterator[bytes]:
    """Read exactly count LF-terminated lines, without reading the next byte.

    Caller MUST open an unbuffered binary FileIO, not BufferedReader/TextIO.
    Read size is at most the remaining number of newlines. A byte cannot
    contain more than one LF, so this bound cannot cross the last allowed LF,
    even for one-byte/blank lines. No lookahead, seek, mmap or EOF probe.
    The budget comes from the trusted frozen manifest (header + row count).
    """
    if not isinstance(raw, io.RawIOBase):
        raise TypeError("Unbuffered raw binary stream required")
    if count < 0 or max_line_bytes < 1:
        raise ValueError("Invalid line budget")
    pending = b""
    while count:
        chunk = raw.read(min(65536, count))
        if not chunk:
            raise ValueError("Historical prefix truncated or missing final LF")
        parts = (pending + chunk).split(b"\n")
        pending = parts.pop()
        if len(pending) > max_line_bytes:
            raise ValueError("CSV line too long")
        for line in parts:
            if len(line) + 1 > max_line_bytes:
                raise ValueError("CSV line too long")
            count -= 1
            yield line + b"\n"
    if pending:
        raise AssertionError("Reader crossed the frozen prefix")


@dataclass(frozen=True)
class Bar:
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    # Optional known delivery time, in the same feed-local timezone.
    available_at: datetime | None = None
    symbol: str = "SYNTHETIC"

    @property
    def ohlcv(self) -> tuple[Decimal, ...]:
        return self.open, self.high, self.low, self.close, self.volume


@dataclass(frozen=True)
class TimestampEvidence:
    timezone: str | None = None
    label: str | None = None  # "start" or "end"
    sources: tuple[str, ...] = ()  # Independent provider evidence, not OHLCV fits.

    @property
    def confirmed(self) -> bool:
        if self.label not in ("start", "end") or not self.timezone or not self.sources:
            return False
        try:
            ZoneInfo(self.timezone)
        except (ZoneInfoNotFoundError, ValueError):
            return False
        return True


@dataclass(frozen=True)
class SessionWindow:
    start: datetime
    end: datetime
    session_id: str
    trading_day: date
    confirmed: bool = False
    sources: tuple[str, ...] = ()


@dataclass(frozen=True)
class BlockedInterval:
    start: datetime
    end: datetime
    reason: str


IMOEXF_QUARANTINE = BlockedInterval(
    datetime(2024, 8, 16, 18, 45), datetime(2024, 8, 17),
    "unexplained_M15_evening",
)
KNOWN_QUARANTINES = {"IMOEXF": (IMOEXF_QUARANTINE,)}


@dataclass(frozen=True)
class Decision:
    asof: datetime
    parent: Bar | None
    reason: str


def interval(bar: Bar, minutes: int, label: str) -> tuple[datetime, datetime]:
    duration = timedelta(minutes=minutes)
    if label == "start":
        return bar.timestamp, bar.timestamp + duration
    if label == "end":
        return bar.timestamp - duration, bar.timestamp
    raise ValueError("Unknown label semantics")


def aggregate(bars: Sequence[Bar], timestamp: datetime) -> Bar:
    if not bars:
        raise ValueError("Empty composition")
    return Bar(timestamp, bars[0].open, max(b.high for b in bars),
               min(b.low for b in bars), bars[-1].close,
               sum((b.volume for b in bars), Decimal(0)), symbol=bars[0].symbol)


def _validate(bars: Sequence[Bar], minutes: int) -> None:
    previous = None
    for b in bars:
        t = b.timestamp
        if (t.tzinfo is not None or t.second or t.microsecond or
                (t.hour * 60 + t.minute) % minutes):
            raise ValueError("Expected aligned naive feed-local timestamps")
        if previous is not None and t <= previous:
            raise ValueError("Bars must be strictly ordered and unique")
        if (not all(isinstance(v, Decimal) and v.is_finite() for v in b.ohlcv) or
                min(b.open, b.high, b.low, b.close) <= 0 or b.volume < 0 or
                b.high < max(b.open, b.low, b.close) or
                b.low > min(b.open, b.high, b.close)):
            raise ValueError("Invalid OHLCV")
        if b.available_at is not None and b.available_at.tzinfo is not None:
            raise ValueError("Delivery time must use the same naive feed-local clock")
        previous = t


def align_contexts(
    m5: Sequence[Bar], parents: Sequence[Bar], minutes: int,
    evidence: TimestampEvidence = TimestampEvidence(),
    sessions: Sequence[SessionWindow] = (),
    quarantine: Sequence[BlockedInterval] = (),
    observed_at: datetime | None = None,
) -> list[Decision]:
    """Last scheduled closed M15/M30/H1 at each completed M5, fail closed.

    A missing/latest-unobservable parent never falls back to an older parent.
    Every expected M5 slot from the parent start through the decision must
    exist and be closed/delivered. A gap therefore invalidates carried context
    until a fresh complete parent closes. Parent and decision must share one
    confirmed continuous session window. OHLCV uses exact Decimal equality.
    """
    if minutes not in (15, 30, 60):
        raise ValueError("Only M15/M30/H1 -> M5 supported")
    _validate(m5, 5)
    _validate(parents, minutes)
    symbols = {b.symbol for b in (*m5, *parents)}
    if len(symbols) > 1 or any(not isinstance(s, str) or not s.strip() for s in symbols):
        raise ValueError("MTF inputs must share one instrument")
    if observed_at is not None and observed_at.tzinfo is not None:
        raise ValueError("observed_at must be feed-local naive")
    quarantine = (*KNOWN_QUARANTINES.get(next(iter(symbols), ""), ()), *quarantine)
    ordered_sessions = sorted(sessions, key=lambda w: w.start)
    for i, w in enumerate(ordered_sessions):
        if (w.start.tzinfo is not None or w.end.tzinfo is not None or
                w.start >= w.end or not w.session_id or type(w.trading_day) is not date or
                w.end > datetime.combine(w.start.date() + timedelta(days=1), datetime.min.time()) or
                (i and ordered_sessions[i - 1].end > w.start)):
            raise ValueError("Invalid/overlapping session windows")
    for q in quarantine:
        if q.start.tzinfo is not None or q.end.tzinfo is not None or q.start >= q.end:
            raise ValueError("Invalid quarantine interval")
    # When semantics are unknown, even asof cannot be asserted. Use the later
    # of start/end hypotheses for diagnostics only; every decision is blocked.
    label = evidence.label if evidence.confirmed else "start"
    base = {interval(b, 5, label)[0]: b for b in m5}
    higher = {interval(b, minutes, label)[0]: b for b in parents}
    window_starts = [w.start for w in ordered_sessions]
    output = []
    for b in m5:
        bstart, asof = interval(b, 5, label)
        if observed_at is not None and asof > observed_at:
            break
        parent = None
        reason = "timestamp_unconfirmed"
        if evidence.confirmed:
            day = asof.replace(hour=0, minute=0, second=0, microsecond=0)
            elapsed = int((asof - day).total_seconds() // 60)
            pstart = day + timedelta(minutes=(elapsed // minutes - 1) * minutes)
            wi = bisect_left(window_starts, bstart + timedelta(microseconds=1)) - 1
            w = ordered_sessions[wi] if wi >= 0 else None
            if not w or not w.confirmed or not w.sources or not (w.start <= bstart < asof <= w.end):
                reason = "session_unconfirmed"
            elif pstart < w.start:
                reason = "session_boundary"
            elif any(q.start < asof and pstart < q.end for q in quarantine):
                reason = "quarantine"
            elif pstart not in higher:
                reason = "missing_parent"
            else:
                candidate = higher[pstart]
                pend = pstart + timedelta(minutes=minutes)
                delivery = candidate.available_at or pend
                if pend > asof or delivery > asof:
                    reason = "parent_not_observable"
                else:
                    slots = [pstart + i * FIVE for i in range(int((asof - pstart) / FIVE))]
                    if any(t not in base for t in slots):
                        reason = "missing_m5_or_stale_context"
                    elif any((base[t].available_at or t + FIVE) > asof for t in slots):
                        reason = "m5_not_observable"
                    else:
                        children = [base[t] for t in slots[:minutes // 5]]
                        if aggregate(children, candidate.timestamp).ohlcv != candidate.ohlcv:
                            reason = "ohlcv_mismatch"
                        else:
                            parent, reason = candidate, "admitted"
        output.append(Decision(asof, parent, reason))
    return output
