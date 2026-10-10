"""R16 completed-bar signal adapter; all order execution belongs to core."""
from collections import deque
from datetime import datetime, timedelta
from decimal import Decimal


class CompressionBreakout:
    name = 'R16_COMPRESSION_BREAKOUT'

    def __init__(self, parameters):
        self.p = dict(parameters)
        if (self.p['W'], self.p['breakout_ticks'], self.p['stop_mode'],
                self.p['stop_buffer_ticks']) != (8, 1, 'OPPOSITE', 1):
            raise ValueError('UNAPPROVED_R16_GRAMMAR')

    def begin_day(self, symbol, day):
        self.symbol, self.day = symbol, day
        self.history = deque(maxlen=self.p['W'])
        self.window = self.last_start = None

    def permitted(self, ctx):
        step = timedelta(minutes=5)
        for first, last in self.p['signal_start_windows']:
            a = datetime.fromisoformat(f'{self.day} {first}:00').replace(tzinfo=ctx.start.tzinfo)
            z = datetime.fromisoformat(f'{self.day} {last}:00').replace(tzinfo=ctx.start.tzinfo)+step
            if max(a, ctx.window[0]) <= ctx.start and ctx.available_at <= min(z, ctx.window[1]):
                return True
        return False

    def on_bar(self, bar, ctx):
        step = timedelta(minutes=5)
        if ctx.available_at != ctx.start+step or (bar and (bar.start != ctx.start or bar.available_at > ctx.available_at)):
            raise ValueError('UNCOMPLETED_OR_MISALIGNED_BAR')
        rec = dict(signal_id=f'{self.symbol}_{self.day}_{ctx.start:%H%M}',
                   direction=0, signal_at=None, compression_at=ctx.start)
        events = []
        permitted = self.permitted(ctx)
        reset = ('SESSION_BOUNDARY' if self.window != ctx.window else
                 'NONCONSECUTIVE_CALLBACK' if self.last_start is not None and self.last_start+step != ctx.start else '')
        if reset:
            self.history.clear()
            if permitted:
                events.append(dict(rec, signal_id=rec['signal_id']+'_RESET', base_reason='COMPRESSION_UNAVAILABLE', reset_reason=reset,
                                   valid_preceding_bars=0))
        self.window, self.last_start = ctx.window, ctx.start
        valid = (bar is not None and bar.valid and bar.start.date() == self.day and
                 ctx.window[0] <= bar.start and bar.available_at <= ctx.window[1])
        if not valid:
            self.history.clear()
            if permitted:
                events.append(dict(rec, base_reason='COMPRESSION_MISSING_BAR' if bar is None else
                                   'COMPRESSION_INVALID_BAR', valid_preceding_bars=0))
            return events
        if permitted and len(self.history) == self.p['W']:
            high = max(b.high for b, _ in self.history)
            low = min(b.low for b, _ in self.history)
            prior, atr = self.history[-1]
            rec.update(compression_start=self.history[0][0].start,
                       compression_end=prior.available_at, compression_bars=len(self.history),
                       compression_high=high, compression_low=low, compression_width=high-low,
                       ATR_ref=atr, ATR_ref_bar_start=prior.start, breakout_start=bar.start,
                       breakout_closed_at=bar.available_at, breakout_open=bar.open,
                       breakout_close=bar.close, breakout_tick=ctx.tick)
            if atr is None or atr <= 0:
                events.append(dict(rec, base_reason='ATR_UNAVAILABLE' if atr is None else 'ATR_ZERO'))
            elif high % ctx.tick or low % ctx.tick:
                events.append(dict(rec, base_reason='OFF_COMPRESSION_GRID'))
            elif (high-low)/atr <= Decimal(self.p['width_atr']):
                rec['compression_width_atr'] = (high-low)/atr
                long = bar.open <= high and bar.close >= high+self.p['breakout_ticks']*ctx.tick
                short = bar.open >= low and bar.close <= low-self.p['breakout_ticks']*ctx.tick
                if long and short:
                    events.append(dict(rec, base_reason='AMBIGUOUS_BREAKOUT'))
                elif long or short:
                    side = 1 if long else -1
                    rec.update(direction=side, signal_at=ctx.available_at,
                               stop=low-ctx.tick if long else high+ctx.tick,
                               target_gross_R=self.p['target_gross_R'],
                               max_hold_calendar_minutes=self.p['max_hold_calendar_minutes'])
                    events.append(dict(rec, base_reason='SIGNAL'))
                elif bar.close >= high+ctx.tick or bar.close <= low-ctx.tick:
                    events.append(dict(rec, base_reason='ALREADY_OUTSIDE_RANGE'))
        # Save the snapshot AFTER evaluating; this bar enters only future windows.
        self.history.append((bar, ctx.indicators['atr14']))
        return events

    def end_day(self):
        return []
