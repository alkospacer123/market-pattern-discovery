"""Causal exact-four-M15 context only. No order, execution or economics logic.

Select latest nominally released H1 (start+65), never substitute an older
parent through a detected gap. A new complete post-gap H1 restores context.
"""
from datetime import timedelta
from decimal import Decimal
from .m15_bars import FIFTEEN

HOUR = timedelta(hours=1)
DELIVERY = timedelta(minutes=65)


class H1Context:
    def __init__(self):
        self.window = self.last_start = self.last_gap = None
        self.children, self.parents = {}, {}

    def observe(self, bar, ctx):
        if ctx.start.tzinfo is None or ctx.start.second or ctx.start.microsecond or ctx.start.minute % 15 or ctx.available_at != ctx.start+FIFTEEN:
            raise ValueError('UNALIGNED_OR_UNCOMPLETED_M15')
        if bar is not None and (bar.start != ctx.start or bar.duration != FIFTEEN):
            raise ValueError('H1_CHILD_LABEL_DURATION')
        if self.window != ctx.window:
            self.children.clear(); self.parents.clear(); self.last_gap = None
        elif self.last_start is not None and self.last_start+FIFTEEN != ctx.start:
            self.children.clear(); self.parents.clear(); self.last_gap = ctx.start-FIFTEEN
        self.window, self.last_start = ctx.window, ctx.start
        if bar is None or not bar.valid or not (ctx.window[0] <= bar.start and bar.available_at <= ctx.window[1]):
            self.children.clear(); self.parents.clear(); self.last_gap = ctx.start
            return
        self.children[bar.start] = bar
        at = bar.start.replace(minute=0, second=0, microsecond=0)
        clocks = tuple(at+i*FIFTEEN for i in range(4))
        bars = [self.children.get(t) for t in clocks]
        if at >= ctx.window[0] and at+HOUR <= ctx.window[1] and bar.start == clocks[-1] and all(b is not None and b.valid for b in bars):
            self.parents[at] = dict(open=bars[0].open,high=max(b.high for b in bars),
                low=min(b.low for b in bars),close=bars[-1].close,
                volume=sum((b.volume for b in bars),Decimal(0)))
        self.children = {t:b for t,b in self.children.items() if t >= at}
        self.parents = {t:p for t,p in self.parents.items() if t >= at-HOUR}

    def describe(self, ctx):
        at = (ctx.available_at-DELIVERY).replace(minute=0,second=0,microsecond=0)
        p = self.parents.get(at) if self.window == ctx.window else None
        rec = dict(signal_decision_at=ctx.available_at,context_direction=0,context_valid=False,
            context_reason='',last_gap_start=self.last_gap,h1_start=at,h1_closed_at=at+HOUR,
            h1_available_at=at+DELIVERY,
            child_m15_starts=','.join(str(at+i*FIFTEEN) for i in range(4)),
            child_m5_starts=','.join(str(at+timedelta(minutes=5*i)) for i in range(12)),
            **{'h1_'+k:None for k in ('open','high','low','close','volume')})
        if at < ctx.window[0]:
            rec['context_reason'] = 'H1_NOT_YET_AVAILABLE'
        elif p is None:
            rec['context_reason'] = 'H1_INCOMPLETE_OR_GAP_RESET'
        elif at+DELIVERY > ctx.available_at:
            rec['context_reason'] = 'H1_DELIVERY_NOT_READY'
        else:
            side = 1 if p['close'] > p['open'] else -1 if p['close'] < p['open'] else 0
            rec.update(context_valid=True,context_direction=side,
                context_reason='' if side else 'H1_DOJI',**{'h1_'+k:v for k,v in p.items()})
        return rec
