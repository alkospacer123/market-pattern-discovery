"""Frozen #463 A BASE grammar. It observes completed M5 only."""
from datetime import datetime, timedelta
from decimal import Decimal


class ORBFalseBreakFade:
    name = 'ORB_FALSE_BREAK_FADE_A_BASE'

    def __init__(self, parameters):
        self.p = dict(parameters)
        if self.p['or_bars'] != 3 or self.p['reclaim_next_bars'] != 1:
            raise ValueError('Frozen M5 grammar requires three OR bars and one reclaim successor')

    def begin_day(self, symbol, day):
        self.symbol, self.day = symbol, day
        self.used, self.pending, self.or_rows = set(), {}, []
        self.bounds = self.window = self.origin = None

    def finish(self, ep, ctx=None, reason='NO_RECLAIM'):
        rec = dict(ep['record'], base_reason=reason)
        if ctx:
            rec.update(signal_at=ctx.available_at, reclaim_start=ctx.start,
                       stop=ep['extreme']-ep['direction']*ep['tick']*self.p['stop_buffer_ticks'],
                       target_gross_R=self.p['target_gross_R'],
                       max_hold_calendar_minutes=self.p['max_hold_calendar_minutes'])
        return rec

    def on_bar(self, bar, ctx):
        events = []
        if self.origin is None:
            self.origin = datetime.fromisoformat(f'{self.day} {self.p["or_start"]}:00').replace(tzinfo=ctx.start.tzinfo)
        if ctx.window != self.window:
            events.extend(self.finish(ep, reason='NO_RECLAIM_WINDOW') for ep in self.pending.values())
            self.pending.clear()
        self.window = ctx.window
        if bar is None or not bar.valid:
            events.extend(self.finish(ep, reason='NO_RECLAIM_GAP') for ep in self.pending.values())
            self.pending.clear()
            return events
        step = bar.duration
        if self.origin <= bar.start <= self.origin+2*step:
            self.or_rows.append(bar)
            if bar.start == self.origin+2*step and [b.start for b in self.or_rows] == [self.origin+i*step for i in range(3)]:
                self.bounds = max(b.high for b in self.or_rows), min(b.low for b in self.or_rows)
            return events
        if self.bounds is None:
            return events
        high, low = self.bounds
        tick = ctx.tick
        upper = bar.high >= high+self.p['sweep_ticks']*tick
        lower = bar.low <= low-self.p['sweep_ticks']*tick
        if upper and lower and (len(self.used) < 2 or self.pending):
            events.extend(self.finish(ep, reason='NO_RECLAIM_AMBIGUOUS') for ep in self.pending.values())
            self.pending.clear()
            self.used.update((-1, 1))
            events.append(dict(signal_id=f'{self.symbol}_{self.day}_AMB_{bar.start:%H%M}',
                               direction=0, sweep_start=bar.start, signal_at=None,
                               base_reason='AMBIGUOUS_BOTH_SIDES', or_high=high, or_low=low))
            return events
        def reclaims(direction):
            return low <= bar.close <= high-self.p['reclaim_inside_ticks']*tick if direction == -1 else low+self.p['reclaim_inside_ticks']*tick <= bar.close <= high
        for direction, ep in list(self.pending.items()):
            ep['extreme'] = max(ep['extreme'], bar.high) if direction == -1 else min(ep['extreme'], bar.low)
            ok = reclaims(direction)
            events.append(self.finish(ep, ctx if ok else None, 'SIGNAL' if ok else 'NO_RECLAIM'))
            del self.pending[direction]
        for direction, swept in ((-1, upper), (1, lower)):
            if not swept or direction in self.used:
                continue
            self.used.add(direction)
            rec = dict(signal_id=f'{self.symbol}_{self.day}_{direction}_{bar.start:%H%M}',
                       direction=direction, sweep_start=bar.start, sweep_closed_at=ctx.available_at,
                       signal_at=None, or_high=high, or_low=low, or_available_at=self.origin+3*step,
                       sweep_tick=tick, sweep_size=bar.high-high if direction == -1 else low-bar.low)
            ep = dict(record=rec, direction=direction, tick=tick,
                      extreme=bar.high if direction == -1 else bar.low)
            if reclaims(direction):
                events.append(self.finish(ep, ctx, 'SIGNAL'))
            elif bar.start+step < ctx.window[1]:
                self.pending[direction] = ep
            else:
                events.append(self.finish(ep, reason='NO_RECLAIM_WINDOW'))
        return events

    def end_day(self):
        events = [self.finish(ep, reason='NO_RECLAIM_DAY_END') for ep in self.pending.values()]
        if self.bounds is None:
            events.append(dict(signal_id=f'{self.symbol}_{self.day}_NO_OR', direction=0,
                               signal_at=None, sweep_start=self.origin, base_reason='NO_OR'))
        return events
