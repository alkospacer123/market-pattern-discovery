"""C_v1: one causal level per side, three approaches separated by whole-bar retreats."""
from datetime import timedelta

FIVE = timedelta(minutes=5)


def parameters():
    return dict(version='C_v1', signal_tf='M5', approaches=3, local_extreme_lookback=5,
        local_extreme_strict=True, tolerance_ticks=2, retreat_ticks=3,
        maximum_construction_bars=24, rejection_close_ticks=1, stop_buffer_ticks=1,
        minimum_risk_ticks=3, maximum_risk_ticks=12, maximum_rebound_ticks=4,
        target_mode='FULL_NET_C1_R', target_net_R='3', max_hold_calendar_minutes=120)


class ReturnRetestRejectionM5:
    name = 'RETURN_RETEST_REJECTION_M5'

    def __init__(self, p):
        if p != parameters():
            raise ValueError('UNAPPROVED_C_V1_PARAMETERS')
        self.p = dict(p)
        self.construction_events = []

    def record(self, run, kind, at, **fields):
        self.construction_events.append(dict(instrument=self.symbol, direction=run['side'],
            construction_id=run['id'], first_start=run['start'], level=run['level'],
            tick=run['tick'], event=kind, observed_at=at, **fields))

    def finish(self, side, reason, at):
        run = self.runs.pop(side, None)
        if run:
            self.record(run, 'RESET', at, reason=reason, approaches=len(run['touches']),
                consumed=run['consumed'])

    def clear(self, reason, at):
        for side in (-1, 1):
            self.finish(side, reason, at)
        self.history.clear()

    def begin_day(self, symbol, day):
        self.symbol, self.day = symbol, day
        self.runs, self.history = {}, []
        self.previous = self.window = self.tick = None

    def on_bar(self, bar, ctx):
        if ctx.available_at != ctx.start + FIVE or bar is not None and (
            bar.start != ctx.start or bar.duration != FIVE or bar.available_at != ctx.available_at):
            raise ValueError('UNCOMPLETED_OR_MISALIGNED_M5')
        reason = ('SESSION_CHANGE' if self.window is not None and self.window != ctx.window else
                  'TICK_CHANGE' if self.tick is not None and self.tick != ctx.tick else
                  'BAR_GAP' if self.previous is not None and self.previous + FIVE != ctx.start else None)
        if reason:
            self.clear(reason, ctx.available_at)
        self.previous, self.window, self.tick = ctx.start, ctx.window, ctx.tick
        if bar is None or not bar.valid or bar.start.date() != self.day or not (
            ctx.window[0] <= bar.start < bar.available_at <= ctx.window[1]):
            self.clear('MISSING_OR_INVALID_BAR', ctx.available_at)
            return []
        if any(p % ctx.tick for p in (bar.open, bar.high, bar.low, bar.close)):
            raise ValueError('OFF_HISTORICAL_GRID')
        candidates = []
        for side in (-1, 1):
            extreme = bar.high if side == -1 else bar.low
            run = self.runs.get(side)
            if run and (ctx.start-run['start']) // FIVE >= 24:
                self.finish(side, 'EXPIRED_24_BARS', ctx.available_at)
                run = None
            if run and side * (extreme-run['level']) < -2 * ctx.tick:
                self.finish(side, 'OUTER_ZONE_BREAK', ctx.available_at)
                run = None
            if run is None:
                preceding = [b.high if side == -1 else b.low for b in self.history]
                local = len(preceding) == 5 and (extreme > max(preceding) if side == -1 else extreme < min(preceding))
                if not local:
                    continue
                ident = f'C1_{self.symbol}_{self.day}_{"LONG" if side == 1 else "SHORT"}_{ctx.start:%H%M}_{int(extreme/ctx.tick)}'
                run = dict(id=ident, side=side, start=ctx.start, level=extreme, tick=ctx.tick,
                    max_high=bar.high, min_low=bar.low, touches=[(ctx.start, extreme)],
                    retreats=[], armed=False, consumed=False)
                self.runs[side] = run
                self.record(run, 'FIRST', ctx.available_at, bar_start=ctx.start, extreme=extreme,
                    previous_extrema=preceding, previous_starts=[b.start for b in self.history])
                continue
            run['max_high'] = max(run['max_high'], bar.high)
            run['min_low'] = min(run['min_low'], bar.low)
            if run['consumed']:
                continue
            distance = side * (extreme-run['level']) / ctx.tick
            if not run['armed'] and distance >= 3:
                run['armed'] = True
                run['retreats'].append((ctx.start, extreme, distance))
                self.record(run, 'RETREAT', ctx.available_at, bar_start=ctx.start,
                    extreme=extreme, depth_ticks=distance, after_approach=len(run['touches']))
            elif run['armed'] and abs(extreme-run['level']) <= 2*ctx.tick:
                run['armed'] = False
                run['touches'].append((ctx.start, extreme))
                count = len(run['touches'])
                self.record(run, 'SECOND' if count == 2 else 'THIRD', ctx.available_at,
                    bar_start=ctx.start, extreme=extreme)
                if count != 3:
                    continue
                # One attempt at the first bar of approach three, regardless of Close or fill.
                run['consumed'] = True
                boundary = run['max_high'] if side == -1 else run['min_low']
                touches, retreats = run['touches'], run['retreats']
                close_distance = side * (bar.close-run['level']) / ctx.tick
                event = dict(signal_id=run['id'], cluster_id=run['id'], construction_id=run['id'],
                    direction=side, signal_at=ctx.available_at, signal_bar_start=ctx.start,
                    signal_bar_closed_at=ctx.available_at, construction_start=run['start'],
                    construction_bars=(ctx.start-run['start']) // FIVE + 1,
                    level=run['level'], signal_tick=ctx.tick, signal_close=bar.close,
                    close_distance_ticks=close_distance, construction_max_high=run['max_high'],
                    construction_min_low=run['min_low'], boundary=boundary,
                    approach_starts=[t[0] for t in touches], approach_extrema=[t[1] for t in touches],
                    retreat_starts=[r[0] for r in retreats], retreat_extrema=[r[1] for r in retreats],
                    retreat_depth_ticks=[r[2] for r in retreats],
                    approach_separation_bars=[(touches[i+1][0]-touches[i][0]) // FIVE for i in (0, 1)],
                    observed_touch_width_ticks=(max(t[1] for t in touches)-min(t[1] for t in touches))/ctx.tick,
                    allowed_zone_width_ticks=4, stop=boundary-side*ctx.tick,
                    target_mode='FULL_NET_C1_R', target_net_R='3', target_gross_R='3',
                    max_hold_calendar_minutes=120,
                    base_reason='SIGNAL' if close_distance >= 1 else 'THIRD_CLOSE_NOT_REJECTED',
                    entry_constraints=dict(directional_reference=boundary, minimum_reference_ticks=0,
                        maximum_reference_ticks=4, minimum_risk_ticks=3, maximum_risk_ticks=12,
                        reason_labels={'OPEN_REFERENCE_LIMIT': 'OPEN_WRONG_SIDE_OF_CONSTRUCTION',
                            'INVALID_RISK': 'INVALID_STOP_GEOMETRY',
                            'RISK_BELOW_MINIMUM_TICKS': 'STOP_BELOW_3_TICKS',
                            'RISK_ABOVE_MAXIMUM_TICKS': 'STOP_ABOVE_12_TICKS',
                            'OPEN_REFERENCE_TOO_FAR': 'ENTRY_MORE_THAN_4_TICKS_FROM_CONSTRUCTION'}))
                candidates.append(event)
        if sum(e['base_reason'] == 'SIGNAL' for e in candidates) == 2:
            for e in candidates:
                if e['base_reason'] == 'SIGNAL':
                    e['base_reason'] = 'AMBIGUOUS_BOTH_SIDES'
        self.history = (self.history + [bar])[-5:]
        return candidates

    def end_day(self):
        self.clear('DAY_END', self.previous + FIVE if self.previous else None)
        return []
