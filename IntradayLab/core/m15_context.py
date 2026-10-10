"""Streaming exact-three M5 adapter. Context only; no execution or source handle.

Wall-clock M15 buckets are released at start+20 minutes. A known M5 gap
invalidates the current context immediately; three new complete parents are
required after it. Selection uses the latest nominally available bucket, never
an older substitute. All timestamps in compact child-clock fields are MSK on
the associated parent's date.
"""
from datetime import timedelta
from decimal import Decimal

FIVE = timedelta(minutes=5)
FIFTEEN = timedelta(minutes=15)
TWENTY = timedelta(minutes=20)


class M15Context:
    def __init__(self):
        self.window = self.last_start = self.last_gap = None
        self.children = {}
        self.parents = {}

    def observe(self, bar, ctx):
        if ctx.available_at != ctx.start+FIVE or (bar is not None and (
                bar.start != ctx.start or bar.duration != FIVE or bar.available_at != ctx.available_at)):
            raise ValueError('UNCOMPLETED_OR_MISALIGNED_BAR')
        if ctx.start.tzinfo is None or ctx.start.second or ctx.start.microsecond or ctx.start.minute % 5:
            raise ValueError('UNALIGNED_CONTEXT_CALLBACK')
        if self.window != ctx.window:
            self.children.clear(); self.parents.clear(); self.last_gap = None
        elif self.last_start is not None and self.last_start+FIVE != ctx.start:
            self.children.clear(); self.parents.clear(); self.last_gap = ctx.start-FIVE
        self.window, self.last_start = ctx.window, ctx.start
        valid = bar is not None and bar.valid and ctx.window[0] <= bar.start and bar.available_at <= ctx.window[1]
        if not valid:
            self.children.clear(); self.parents.clear(); self.last_gap = ctx.start
            return
        self.children[bar.start] = bar
        start = bar.start.replace(minute=bar.start.minute//15*15, second=0, microsecond=0)
        times = tuple(start+i*FIVE for i in range(3))
        if start >= ctx.window[0] and start+FIFTEEN <= ctx.window[1] and bar.start == times[-1]:
            bars = [self.children.get(at) for at in times]
            if all(b is not None and b.valid for b in bars):
                self.parents[start] = dict(start=start, closed_at=start+FIFTEEN,
                    available_at=start+TWENTY, child_m5_starts=','.join(at.strftime('%H:%M') for at in times),
                    open=bars[0].open, high=max(b.high for b in bars), low=min(b.low for b in bars),
                    close=bars[-1].close, volume=sum((b.volume for b in bars), Decimal(0)))
        # Bounded storage; context uses the latest three released parents.
        self.children = {at:b for at,b in self.children.items() if at >= start}
        self.parents = {at:p for at,p in self.parents.items() if at >= start-3*FIFTEEN}

    def describe(self, ctx):
        latest = ctx.available_at-TWENTY
        latest = latest.replace(minute=latest.minute//15*15, second=0, microsecond=0)
        starts = [latest-i*FIFTEEN for i in (2,1,0)]
        rec = dict(signal_decision_at=ctx.available_at, context_direction=0,
                   context_valid=False, context_reason='', last_gap_start=self.last_gap)
        parents = []
        for i, start in enumerate(starts, 1):
            p = self.parents.get(start) if start >= ctx.window[0] else None
            fields = dict(start=start, closed_at=start+FIFTEEN, available_at=start+TWENTY,
                child_m5_starts=','.join((start+j*FIVE).strftime('%H:%M') for j in range(3)),
                high=None, low=None, close=None, valid=p is not None)
            if p is not None:
                fields.update({k:p[k] for k in ('high','low','close')})
            rec.update({f'p{i}_{k}':v for k,v in fields.items()})
            parents.append(p)
        if starts[0] < ctx.window[0]:
            rec['context_reason'] = 'MTF_THREE_PARENTS_NOT_READY'
        elif any(p is None for p in parents):
            rec['context_reason'] = 'MTF_INCOMPLETE_OR_GAP_RESET'
        elif any(p['available_at'] > ctx.available_at for p in parents):
            rec['context_reason'] = 'MTF_DELIVERY_NOT_READY'
        else:
            a,b,c = parents
            long = a['high'] < b['high'] < c['high'] and a['low'] < b['low'] < c['low'] and c['close'] > a['close']
            short = a['high'] > b['high'] > c['high'] and a['low'] > b['low'] > c['low'] and c['close'] < a['close']
            rec.update(context_valid=True, context_direction=1 if long else -1 if short else 0,
                       context_reason='' if long or short else 'MTF_NO_TREND')
        return rec
