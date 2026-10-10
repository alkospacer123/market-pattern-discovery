"""Streaming indicators warm up from all available preceding observations.

ATR is the mean of genuine trailing true ranges. An unobserved adjacent Close
does not manufacture an overnight/gap range; that observation uses H-L.
Session/day boundaries do not discard the preceding observed warm-up history.
"""
from collections import deque
from decimal import Decimal


class Indicators:
    def __init__(self, period=14):
        if period < 1:
            raise ValueError('INDICATOR_PERIOD')
        self.ranges = deque(maxlen=period)
        self.previous = None
        self.count = 0

    def observe(self, bar, asof):
        if asof < bar.available_at:
            raise ValueError('UNCOMPLETED_BAR')
        if not bar.valid:
            self.previous = None
            return self.snapshot()
        tr = bar.high - bar.low
        prior = self.previous
        if prior and prior.available_at == bar.start:
            tr = max(tr, abs(bar.high-prior.close), abs(bar.low-prior.close))
        self.ranges.append(tr)
        self.previous = bar
        self.count += 1
        return self.snapshot()

    def snapshot(self):
        return {'observed_bars': self.count, 'atr14':
                sum(self.ranges, Decimal(0))/len(self.ranges)
                if len(self.ranges) == self.ranges.maxlen else None}
