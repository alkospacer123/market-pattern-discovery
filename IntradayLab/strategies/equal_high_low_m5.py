"""A_v1: three exact completed extremes; one attempt per maximal run."""
from datetime import timedelta

FIVE = timedelta(minutes=5)


class EqualHighLowM5:
    name = 'EQUAL_HIGH_LOW_M5'

    def __init__(self, parameters):
        self.p = dict(parameters)
        expected = dict(version='A_v1', signal_tf='M5', touches=3,
                        tolerance_ticks=0, stop_buffer_ticks=1,
                        minimum_risk_ticks=3, maximum_risk_ticks=12,
                        maximum_rebound_ticks=4, target_net_R='3',
                        target_mode='FULL_NET_C1_R', max_hold_calendar_minutes=120)
        if self.p != expected:
            raise ValueError('UNAPPROVED_A_V1_PARAMETERS')

    def begin_day(self, symbol, day):
        self.symbol, self.day = symbol, day
        self.runs = {}
        self.previous = self.window = self.tick = None

    def on_bar(self, bar, ctx):
        if ctx.available_at != ctx.start+FIVE or (bar is not None and
                (bar.start != ctx.start or bar.duration != FIVE or
                 bar.available_at != ctx.available_at)):
            raise ValueError('UNCOMPLETED_OR_MISALIGNED_M5')
        if (self.window != ctx.window or self.tick != ctx.tick or
                self.previous is not None and self.previous+FIVE != ctx.start):
            self.runs.clear()
        self.window, self.tick, self.previous = ctx.window, ctx.tick, ctx.start
        if (bar is None or not bar.valid or bar.start.date() != self.day or
                not ctx.window[0] <= bar.start < bar.available_at <= ctx.window[1]):
            self.runs.clear()
            return []
        if any(p % ctx.tick for p in (bar.high, bar.low, bar.close)):
            raise ValueError('OFF_HISTORICAL_GRID')
        candidates = []
        for side, extreme in ((-1, bar.high), (1, bar.low)):
            run = self.runs.get(side)
            if run is None or run['level'] != extreme:
                run = dict(level=extreme, start=bar.start, count=0, consumed=False)
                self.runs[side] = run
            run['count'] += 1
            if (run['count'] < 3 or run['consumed'] or
                    side*(bar.close-extreme) <= 0):
                continue
            # Consumption is independent of admission, fill, or later economics.
            run['consumed'] = True
            ident = (f'{self.symbol}_{self.day}_{"LONG" if side == 1 else "SHORT"}'
                     f'_{run["start"]:%H%M}_{int(extreme/ctx.tick)}')
            event = dict(signal_id=ident, cluster_id=ident, direction=side,
                signal_at=ctx.available_at, signal_bar_start=bar.start,
                signal_bar_closed_at=bar.available_at, cluster_start=run['start'],
                cluster_level=extreme, cluster_run_bars=run['count'], signal_tick=ctx.tick,
                touch_1_start=bar.start-2*FIVE, touch_2_start=bar.start-FIVE,
                touch_3_start=bar.start, touch_1_extreme=extreme,
                touch_2_extreme=extreme, touch_3_extreme=extreme, signal_close=bar.close,
                stop=extreme-side*ctx.tick, target_gross_R='3', target_net_R='3',
                target_mode='FULL_NET_C1_R', max_hold_calendar_minutes=120,
                entry_constraints=dict(directional_reference=extreme,
                    minimum_reference_ticks=0, maximum_reference_ticks=4,
                    minimum_risk_ticks=3, maximum_risk_ticks=12,
                    reason_labels={'OPEN_REFERENCE_LIMIT':'OPEN_WRONG_SIDE_OF_CLUSTER',
                        'INVALID_RISK':'INVALID_STOP_GEOMETRY',
                        'RISK_BELOW_MINIMUM_TICKS':'STOP_BELOW_3_TICKS',
                        'RISK_ABOVE_MAXIMUM_TICKS':'STOP_ABOVE_12_TICKS',
                        'OPEN_REFERENCE_TOO_FAR':'ENTRY_MORE_THAN_4_TICKS_FROM_CLUSTER'}))
            candidates.append(event)
        reason = 'AMBIGUOUS_BOTH_SIDES' if len(candidates) == 2 else 'SIGNAL'
        return [dict(e, base_reason=reason) for e in candidates]

    def end_day(self):
        return []
