"""Optimization B v1: frozen grid; width bounds the ENTIRE greedy episode envelope."""
from datetime import timedelta
from decimal import Decimal as D, ROUND_HALF_UP

FIVE = timedelta(minutes=5)
ROUND_STEPS = {'USDRUBF': '0.10', 'CNYRUBF': '0.05', 'GLDRUBF': '10', 'IMOEXF': '10'}


def configuration_id(p):
    return (f'B_OPT2023_N{p["cluster_bars"]}_W{p["maximum_width_ticks"]}'
            f'_T{p["minimum_boundary_touches"]}_SB{p["stop_buffer_ticks"]}_TP{p["target_net_R"]}')


def parameters(n=4, width=3, touches=2, buffer=1, take=3):
    if (n not in range(4,11) or take not in range(2,11) or
            not (buffer==1 and width in (2,3) and touches in (2,3) or
                 buffer==2 and width==3 and touches==2)):
        raise ValueError('UNAPPROVED_B_OPT_GRID')
    return dict(version='B_OPT2023_v1', signal_tf='M5', cluster_bars=n,
        minimum_width_ticks=1, maximum_width_ticks=width, minimum_boundary_touches=touches,
        stop_buffer_ticks=buffer, minimum_risk_ticks=3, maximum_risk_ticks=12,
        maximum_rebound_ticks=4, target_net_R=str(take), target_mode='FULL_NET_C1_R',
        max_hold_calendar_minutes=120, tolerance_ticks=0)


class HighLowClusterM5OptimizationB:
    name = 'HIGH_LOW_CLUSTER_M5'

    def __init__(self, p):
        if p != parameters(p.get('cluster_bars'), p.get('maximum_width_ticks'),
                           p.get('minimum_boundary_touches'), p.get('stop_buffer_ticks'),
                           int(p.get('target_net_R', 0))):
            raise ValueError('UNAPPROVED_B_PARAMETERS')
        self.p = dict(p)
        self.episode_records = []

    def begin_day(self, symbol, day):
        self.symbol, self.day = symbol, day
        self.runs = {}
        self.previous = self.window = self.tick = None

    def finish(self, side, reason, at):
        run = self.runs.pop(side, None)
        if run and run['consumed']:
            self.episode_records.append(dict(episode_id=run['id'], instrument=self.symbol,
                direction=side, episode_start=run['start'], episode_last=run['last'],
                episode_end_observed_at=at, reset_reason=reason, episode_bars=run['count'],
                envelope_min=run['min'], envelope_max=run['max'], consumed=run['consumed']))

    def reset(self, reason, at):
        for side in tuple(self.runs):
            self.finish(side, reason, at)

    def on_bar(self, bar, ctx):
        if ctx.available_at != ctx.start+FIVE or (bar is not None and
                (bar.start != ctx.start or bar.duration != FIVE or bar.available_at != ctx.available_at)):
            raise ValueError('UNCOMPLETED_OR_MISALIGNED_M5')
        reason = ('SESSION_CHANGE' if self.window is not None and self.window != ctx.window else
                  'TICK_CHANGE' if self.tick is not None and self.tick != ctx.tick else
                  'BAR_GAP' if self.previous is not None and self.previous+FIVE != ctx.start else None)
        if reason:
            self.reset(reason, ctx.available_at)
        self.previous, self.window, self.tick = ctx.start, ctx.window, ctx.tick
        if bar is None or not bar.valid or bar.start.date() != self.day or not (
                ctx.window[0] <= bar.start < bar.available_at <= ctx.window[1]):
            self.reset('MISSING_OR_INVALID_BAR', ctx.available_at)
            return []
        if any(price % ctx.tick for price in (bar.high, bar.low, bar.close)):
            raise ValueError('OFF_HISTORICAL_GRID')
        candidates = []
        n = self.p['cluster_bars']
        for side, extreme in ((-1, bar.high), (1, bar.low)):
            run = self.runs.get(side)
            if run and max(run['max'], extreme)-min(run['min'], extreme) > self.p['maximum_width_ticks']*ctx.tick:
                self.finish(side, f'ENVELOPE_ABOVE_{self.p["maximum_width_ticks"]}_TICKS', ctx.available_at)
                run = None
            if run is None:
                ident = (f'{self.symbol}_{self.day}_{"LONG" if side == 1 else "SHORT"}'
                         f'_{ctx.start:%H%M}_{int(extreme/ctx.tick)}')
                run = dict(id=ident, start=ctx.start, min=extreme, max=extreme,
                           count=0, consumed=False, tail=[])
                self.runs[side] = run
            run['min'], run['max'] = min(run['min'], extreme), max(run['max'], extreme)
            run['count'] += 1
            run['last'] = ctx.start
            run['tail'] = (run['tail']+[(ctx.start, extreme)])[-n:]
            if run['consumed'] or len(run['tail']) != n:
                continue
            values = [v for _, v in run['tail']]
            lower, upper = min(values), max(values)
            width = (upper-lower)/ctx.tick
            boundary = upper if side == -1 else lower
            touches = [at for at, v in run['tail'] if v == boundary]
            if not 1 <= width <= self.p['maximum_width_ticks'] or len(touches) < self.p['minimum_boundary_touches']:
                continue
            # Formed construction is consumed even if Close/admission/ambiguity fails.
            run['consumed'] = True
            ident = f'{configuration_id(self.p)}_{run["id"]}'
            step = D(ROUND_STEPS[self.symbol])
            nearest = (boundary/step).to_integral_value(rounding=ROUND_HALF_UP)*step
            distance = abs(boundary-nearest)
            event = dict(signal_id=ident, cluster_id=ident, episode_id=run['id'],
                direction=side, signal_at=ctx.available_at, signal_bar_start=ctx.start,
                signal_bar_closed_at=ctx.available_at, episode_start=run['start'],
                episode_bars_at_formation=run['count'], episode_envelope_min=run['min'],
                episode_envelope_max=run['max'], cluster_start=run['tail'][0][0],
                cluster_end=ctx.start, cluster_bars=n, cluster_min=lower, cluster_max=upper,
                cluster_level=boundary, cluster_width_ticks=width,
                boundary_touches=len(touches), internal_touches=n-len(touches),
                first_touch=touches[0], last_touch=touches[-1],
                extrema=values, extreme_times=[at for at, _ in run['tail']],
                signal_tick=ctx.tick, signal_close=bar.close,
                signal_close_distance_ticks=side*(bar.close-boundary)/ctx.tick,
                round_step=step, nearest_round_level=nearest,
                round_distance_price=distance, round_distance_ticks=distance/ctx.tick,
                level_type='ROUND_NEAR' if distance <= ctx.tick else 'ORDINARY_FAR',
                stop=boundary-side*self.p['stop_buffer_ticks']*ctx.tick,
                target_gross_R=self.p['target_net_R'], target_net_R=self.p['target_net_R'],
                target_mode='FULL_NET_C1_R', max_hold_calendar_minutes=120,
                base_reason='SIGNAL' if side*(bar.close-boundary)>0 else 'CLOSE_AT_BOUNDARY',
                entry_constraints=dict(directional_reference=boundary, minimum_reference_ticks=0,
                    maximum_reference_ticks=4, minimum_risk_ticks=3, maximum_risk_ticks=12,
                    reason_labels={'OPEN_REFERENCE_LIMIT':'OPEN_WRONG_SIDE_OF_CLUSTER',
                        'INVALID_RISK':'INVALID_STOP_GEOMETRY',
                        'RISK_BELOW_MINIMUM_TICKS':'STOP_BELOW_3_TICKS',
                        'RISK_ABOVE_MAXIMUM_TICKS':'STOP_ABOVE_12_TICKS',
                        'OPEN_REFERENCE_TOO_FAR':'ENTRY_MORE_THAN_4_TICKS_FROM_CLUSTER'}))
            candidates.append(event)
        if sum(e['base_reason']=='SIGNAL' for e in candidates)==2:
            for event in candidates:
                event['base_reason']='AMBIGUOUS_BOTH_SIDES'
        return candidates

    def end_day(self):
        # Last completed session bar is the latest observable reset boundary.
        self.reset('DAY_END', self.previous+FIVE if self.previous else None)
        return []
