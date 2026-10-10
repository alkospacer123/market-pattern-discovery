"""Frozen two-bar pullback and separate continuation; all execution is core-owned."""
from collections import deque
from decimal import Decimal
from IntradayLab.core.m15_context import M15Context, FIVE

FIXED_PARAMETERS = dict(signal_tf='M5', context_tf='M15', m15_parent_bars=3,
    m15_availability_after_close_minutes=5,
    trend_structure='HIGHER_HIGHS_AND_LOWS / LOWER_HIGHS_AND_LOWS',
    pullback_bars=2, pullback_direction='against_M15', min_pullback_close_change_ticks=1,
    confirmation_break_ticks=1, stop_mode='CORRECTION_EXTREME', stop_buffer_ticks=1,
    min_initial_risk_ticks=4, target_mode='FULL_NET_C1_R', target_net_R='3',
    wait_complete_m5_bars=1, min_entry_to_flat_minutes=35,
    max_hold_calendar_minutes=120, daily_trade_deadline='17:00', cost='C1')


class SwingPullback:
    name = 'SWING_PULLBACK_M5_M15'

    def __init__(self, parameters):
        if parameters != FIXED_PARAMETERS:
            raise ValueError('UNAPPROVED_SWING_PULLBACK_PARAMETERS')
        self.p = dict(parameters)
        self.context_records = []

    def begin_day(self, symbol, day):
        self.symbol, self.day = symbol, day
        self.m15 = M15Context()
        self.history = deque(maxlen=2)
        self.window = self.last_start = None

    def on_bar(self, bar, ctx):
        self.m15.observe(bar, ctx)
        if self.window != ctx.window or (self.last_start is not None and self.last_start+FIVE != ctx.start):
            self.history.clear()
        self.window, self.last_start = ctx.window, ctx.start
        ident = f'{self.symbol}_{self.day}_{ctx.start:%H%M}'
        rec = dict(signal_id=ident, direction=0, signal_at=None, test_start=ctx.start,
                   pullback_confirmed=False, confirmed_signal=False, signal_tick=ctx.tick)
        context = dict(self.m15.describe(ctx), instrument=self.symbol, signal_id=ident,
                       signal_start=ctx.start, window_start=ctx.window[0], window_end=ctx.window[1])
        rec.update(context_valid=context['context_valid'], context_direction=context['context_direction'],
                   context_reason=context['context_reason'], context_decision_id=ident,
                   context_p3_start=context['p3_start'], context_p3_available_at=context['p3_available_at'])
        valid = bar is not None and bar.valid and bar.start.date() == self.day and (
            ctx.window[0] <= bar.start and bar.available_at <= ctx.window[1])
        if not valid:
            self.history.clear()
            rec['base_reason'] = 'M5_MISSING_BAR' if bar is None else 'M5_INVALID_BAR'
        elif not context['context_valid'] or context['context_direction'] == 0:
            rec['base_reason'] = context['context_reason']
        elif len(self.history) != 2:
            rec['base_reason'] = 'PULLBACK_TWO_BARS_NOT_READY'
        else:
            a,b = self.history
            side = context['context_direction']
            rec.update(direction=side, correction_1_start=a.start, correction_2_start=b.start,
                correction_1_open=a.open, correction_1_high=a.high, correction_1_low=a.low, correction_1_close=a.close,
                correction_2_open=b.open, correction_2_high=b.high, correction_2_low=b.low, correction_2_close=b.close,
                test_open=bar.open, test_high=bar.high, test_low=bar.low, test_close=bar.close,
                test_closed_at=ctx.available_at)
            pullback = side*(a.close-a.open) < 0 and side*(b.close-b.open) < 0 and side*(a.close-b.close) >= ctx.tick
            continuation = side*(bar.close-bar.open) > 0 and (
                bar.close >= b.high+ctx.tick if side == 1 else bar.close <= b.low-ctx.tick)
            rec['pullback_confirmed'] = pullback
            if not pullback:
                rec['base_reason'] = 'NO_TWO_BAR_PULLBACK'
            elif not continuation:
                rec['base_reason'] = 'NO_CONTINUATION_CONFIRMATION'
            else:
                rec.update(base_reason='SIGNAL', confirmed_signal=True, signal_at=ctx.available_at,
                    stop=min(a.low,b.low,bar.low)-ctx.tick if side == 1 else max(a.high,b.high,bar.high)+ctx.tick,
                    target_gross_R=Decimal(3), target_net_R=Decimal(3), target_mode='FULL_NET_C1_R',
                    max_hold_calendar_minutes=120,
                    entry_constraints=dict(minimum_risk_ticks=4,
                        reserve_minutes=40 if ctx.window[1] <= ctx.window[1].replace(hour=17,minute=0) else 35,
                        reason_labels={'RISK_BELOW_MINIMUM_TICKS':'RISK_BELOW_FOUR_TICKS'}))
        if valid:
            self.history.append(bar)
        context.update(pullback_confirmed=rec['pullback_confirmed'], confirmed_signal=rec['confirmed_signal'],
                       decision_reason=rec['base_reason'])
        self.context_records.append(context)
        return [rec]

    def end_day(self):
        return []
