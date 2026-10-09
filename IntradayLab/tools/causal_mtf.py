"""Explicit derived-from-M5 context, never native-feed delivery evidence.

Clock-aligned parents require every exact child in one approved continuous
window. A missing/latest undelivered parent invalidates context; there is no
stale fallback across it. The two-parent direction rule has no fitted period.
Only entry admission changes. Execution, protection and timers stay on M5.
"""
from bisect import bisect_right
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from m5_conditional_v2 import available, allowed, next_slot, window_at, windows

ZERO = Decimal(0)


def delivery_slot(bar, params):
    at = available(bar, params)
    return at if at.second == 0 and at.microsecond == 0 and at.minute % 5 == 0 else next_slot(at)


@dataclass(frozen=True)
class Parent:
    start: object
    session: tuple
    duration: int
    children: tuple
    ohlcv: tuple
    available_at: object


class DerivedContext:
    def __init__(self, bars, minutes, params):
        if minutes not in (15, 30, 60):
            raise ValueError('Undeclared timeframe')
        if not bars or any(b.timestamp.year != 2023 for b in bars):
            raise ValueError('2023 only, before accessing prices')
        if len({b.symbol for b in bars}) != 1:
            raise ValueError('One instrument only')
        index = {b.timestamp: b for b in bars}
        if len(index) != len(bars):
            raise ValueError('Duplicate children')
        self.minutes, self.params = minutes, params
        self.cells, self.sessions = {}, {}
        step = timedelta(minutes=minutes)
        for day in sorted({b.timestamp.date() for b in bars}):
            for session in windows(day):
                a, z = session
                # Wall-clock alignment: e.g. PM M30 starts at 14:30, not 14:05.
                at = a.replace(minute=0, second=0, microsecond=0)
                while at < a:
                    at += step
                starts = []
                while at + step <= z:
                    starts.append(at)
                    child_times = tuple(at + timedelta(minutes=i * 5) for i in range(minutes // 5))
                    children = tuple(index.get(t) for t in child_times)
                    parent = None
                    if all(b is not None and allowed(b.symbol, b.timestamp) and window_at(b.timestamp) == session for b in children):
                        ohlcv = (children[0].open, max(b.high for b in children),
                                 min(b.low for b in children), children[-1].close,
                                 sum((b.volume for b in children), ZERO))
                        parent = Parent(at, session, minutes, child_times, ohlcv,
                                        max(delivery_slot(b, params) for b in children))
                    self.cells[at] = parent
                    at += step
                nominal = [t + timedelta(minutes=minutes - 5 + params['availability_minutes']) for t in starts]
                self.sessions[session] = (starts, nominal)

    def pair(self, now, session):
        starts, nominal = self.sessions.get(session, ([], []))
        i = bisect_right(nominal, now) - 1
        if i < 1:
            return None, 'MTF_TWO_PARENTS_NOT_READY'
        parents = (self.cells[starts[i - 1]], self.cells[starts[i]])
        if any(p is None for p in parents):
            return None, 'MTF_INCOMPLETE_CHILD_BUCKET'
        if any(p.available_at > now for p in parents):
            return None, 'MTF_CHILD_DELIVERY_NOT_READY'
        return parents, None

    def describe(self, now, session, direction, strategy):
        pair, reason = self.pair(now, session)
        record = {'mtf_minutes': self.minutes, 'mtf_contract': 'DERIVED_EXACT_COMPLETED_M5_V1',
                  'mtf_first_start': None, 'mtf_last_start': None, 'mtf_available_at': None,
                  'mtf_direction': None, 'mtf_gate_eligible': False, 'mtf_reason': reason}
        if pair is None:
            return record
        a, b = pair
        ao, _, _, ac, _ = a.ohlcv
        bo, _, _, bc, _ = b.ohlcv
        trend = 1 if ac > ao and bc > bo and bc > ac else -1 if ac < ao and bc < bo and bc < ac else 0
        eligible = trend == direction if strategy == 'MOMENTUM' else trend != -direction
        reason = None if eligible else ('MTF_DIRECTION_NOT_ALIGNED' if strategy == 'MOMENTUM' else 'MTF_SUSTAINED_ADVERSE_DIRECTION')
        record.update(mtf_first_start=str(a.start), mtf_last_start=str(b.start),
                      mtf_available_at=str(max(a.available_at, b.available_at)),
                      mtf_direction=trend, mtf_gate_eligible=eligible, mtf_reason=reason)
        return record


class MTFGate:
    """Mixin: preserve parent M5 decisions/exits; cancel only a new entry."""
    def decision(self, bar, now, features):
        before = len(self.signals)
        super().decision(bar, now, features)
        if len(self.signals) == before:
            return
        signal = self.signals[-1]
        context = self.mtf_context.describe(now, window_at(bar.timestamp), signal['direction_sign'], self.strategy)
        signal.update(context)
        if signal['status'] == 'SUBMITTED' and not context['mtf_gate_eligible']:
            signal['status'], signal['reason'] = 'FILTERED', context['mtf_reason']
            self.entry_order = None
            self.event(now, 'ENTRY_CANCEL', 'CANCELLED', signal['reason'], signal['signal_id'], self.units, 0, self.units)
