"""Frozen R17 M5 adaptation. Only completed observations reach this module."""
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP


class ORBBreakoutRetest:
    name = 'R17_ORB_BREAKOUT_RETEST'

    def __init__(self, parameters):
        self.p = dict(parameters)
        if (self.p['or_bars'], self.p['retest_bars'], self.p['stop_mode'],
                self.p['midpoint_rounding']) != (3, 1, 'OR_MID', 'ROUND_HALF_UP'):
            raise ValueError('UNAPPROVED_R17_GRAMMAR')

    def begin_day(self, symbol, day):
        self.symbol, self.day = symbol, day
        self.used, self.pending, self.opening = set(), {}, {}
        self.bounds = self.origin = None
        self.atr_diagnosed = False

    def clock(self, clock, zone):
        return datetime.fromisoformat(f'{self.day} {clock}:00').replace(tzinfo=zone)

    def signal_window(self, ctx):
        step = timedelta(minutes=5)
        for first, last in self.p['signal_start_windows']:
            a = max(ctx.window[0], self.clock(first, ctx.start.tzinfo))
            z = min(ctx.window[1], self.clock(last, ctx.start.tzinfo)+step)
            if a <= ctx.start and ctx.start+step <= z:
                return a, z
        return None

    def on_bar(self, bar, ctx):
        step = timedelta(minutes=5)
        if self.origin is None:
            self.origin = self.clock(self.p['or_start'], ctx.start.tzinfo)
        events = []
        if self.origin <= ctx.start < self.origin+3*step:
            if bar is not None and bar.valid:
                self.opening[ctx.start] = bar
            if ctx.start == self.origin+2*step and all(self.origin+i*step in self.opening for i in range(3)):
                self.bounds = (max(b.high for b in self.opening.values()),
                               min(b.low for b in self.opening.values()))
            return events
        permitted = self.signal_window(ctx)
        for side, ep in list(self.pending.items()):
            del self.pending[side]
            rec = dict(ep['record'])
            if ctx.start != ep['next_start'] or permitted != ep['window']:
                reason = 'NO_RETEST_WINDOW'
            elif bar is None:
                reason = 'NO_RETEST_MISSING_BAR'
            elif not bar.valid:
                reason = 'NO_RETEST_INVALID_BAR'
            else:
                high, low = self.bounds
                touch = Decimal(self.p['touch_ticks'])*ctx.tick
                ok = (bar.low <= high+touch and bar.low >= low and bar.close >= high) if side == 1 else (
                    bar.high >= low-touch and bar.high <= high and bar.close <= low)
                reason = 'SIGNAL' if ok else 'NO_RETEST_CONDITION'
                if ok:
                    mid = ((high+low)/2/ctx.tick).to_integral_value(rounding=ROUND_HALF_UP)*ctx.tick
                    rec.update(signal_at=ctx.available_at, retest_start=ctx.start,
                               retest_closed_at=ctx.available_at, retest_tick=ctx.tick,
                               or_mid_rounded=mid, stop=mid-side*self.p['stop_buffer_ticks']*ctx.tick,
                               target_gross_R=self.p['target_gross_R'],
                               max_hold_calendar_minutes=self.p['max_hold_calendar_minutes'])
            events.append(dict(rec, base_reason=reason))
        if self.bounds is None or not permitted or bar is None or not bar.valid:
            return events
        atr = ctx.indicators['atr14']
        if atr is None:
            if not self.atr_diagnosed:
                events.append(dict(signal_id=f'{self.symbol}_{self.day}_NO_ATR', direction=0,
                                   signal_at=None, base_reason='ATR_UNAVAILABLE', observed_bars=ctx.indicators['observed_bars']))
                self.atr_diagnosed = True
            return events
        high, low = self.bounds
        buffer = Decimal(self.p['buffer_atr'])*atr
        for side, triggered in ((1, bar.close >= high+buffer), (-1, bar.close <= low-buffer)):
            if not triggered or side in self.used:
                continue
            self.used.add(side)
            rec = dict(signal_id=f'{self.symbol}_{self.day}_{side}_{ctx.start:%H%M}', direction=side,
                       signal_at=None, breakout_start=ctx.start, breakout_closed_at=ctx.available_at,
                       breakout_close=bar.close, breakout_atr14=atr, breakout_tick=ctx.tick,
                       breakout_threshold=high+buffer if side == 1 else low-buffer,
                       or_high=high, or_low=low, or_available_at=self.origin+3*step,
                       signal_window_start=permitted[0], signal_window_end=permitted[1])
            if ctx.start+2*step > permitted[1]:
                events.append(dict(rec, base_reason='NO_RETEST_WINDOW'))
            else:
                self.pending[side] = dict(record=rec, next_start=ctx.start+step, window=permitted)
        return events

    def end_day(self):
        events = [dict(ep['record'], base_reason='NO_RETEST_DAY_END') for ep in self.pending.values()]
        if self.bounds is None:
            events.append(dict(signal_id=f'{self.symbol}_{self.day}_NO_OR', direction=0,
                               signal_at=None, base_reason='NO_OR', or_start=self.origin,
                               valid_required_or_bars=len(self.opening)))
        return events
