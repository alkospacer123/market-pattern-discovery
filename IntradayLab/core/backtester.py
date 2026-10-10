"""Chronological historical engine. It contains no candidate trading rules."""
from datetime import date, datetime, timedelta
from decimal import Decimal

from .execution import at_open, cost, entry_geometry, in_bar
from .indicators import Indicators
from .models import Context


class Backtester:
    def __init__(self, rules, *, timeframe_minutes=5, cost_ticks_per_side=1,
                 allow_entry_bar_take=False, session_flat_before_end_bars=1):
        if timeframe_minutes != 5:
            raise ValueError('Only the explicitly approved M5 clock is implemented')
        if cost_ticks_per_side < 0 or session_flat_before_end_bars < 1:
            raise ValueError('EXECUTION_CONTRACT')
        self.rules = rules
        self.step = timedelta(minutes=timeframe_minutes)
        self.cost_sides = cost_ticks_per_side
        self.entry_take = allow_entry_bar_take
        self.flat_bars = session_flat_before_end_bars

    def run(self, strategy, symbol, rows, *, start, end_exclusive):
        if start >= end_exclusive or end_exclusive > date(2024, 1, 1):
            raise ValueError('Only approved development dates through 2023')
        stamps = list(rows)
        if stamps != sorted(set(stamps)) or any(at.tzinfo is None for at in stamps):
            raise ValueError('TIMEZONE_ORDER_DUPLICATES')
        if any(rows[at].start != at or rows[at].duration != self.step for at in stamps):
            raise ValueError('BAR_LABEL_OR_DURATION')
        if any(at.date() >= end_exclusive for at in stamps):
            raise ValueError('FUTURE_INPUT')
        features = Indicators()
        # Keep preceding source history available for indicator warm-up.
        for at in stamps:
            if at.date() < start:
                features.observe(rows[at], rows[at].available_at)
        signals, trades, days = [], [], []
        prior_unknown = False
        day = start
        first_day = min(rows).date() if rows else end_exclusive
        while day < end_exclusive:
            windows = self.rules.windows(day)
            strategy.begin_day(symbol, day)
            position = pending = None
            blocked = False
            ds, dt = [], []

            def terminate(at, price=None, reason='UNKNOWN', point=False, unknown=None, conflict=False):
                nonlocal position, blocked
                p = position
                q = p['trade']
                q.update(status='UNKNOWN' if unknown else 'CLOSED', exit_reason=reason,
                         exit_price=price, exit_at=at if point and not unknown else None,
                         exit_interval_start=None if unknown else at,
                         exit_interval_end=None if unknown else at if point else at+self.step,
                         resolved_at=None if unknown else at if point else at+self.step,
                         stop_take_conflict=conflict)
                if unknown:
                    q.update(unknown_reason=unknown, unknown_detected_at=at+self.step)
                    blocked = True
                else:
                    gross = q['direction']*(price-q['entry_price'])
                    exit_tick = self.rules.tick(symbol, at)
                    costs = cost(q['entry_tick'], exit_tick, self.cost_sides)
                    q.update(exit_tick=exit_tick, gross=gross, gross_R=gross/q['risk'],
                             cost_c1=costs, cost_R=costs/q['risk'], net_c1=gross-costs,
                             net_R_c1=(gross-costs)/q['risk'])
                position = None

            at = datetime.combine(day, datetime.min.time(), self.rules.zone)
            last_boundary = at + timedelta(days=1)
            while at <= last_boundary:
                previous = rows.get(at-self.step)
                if position and position['trade']['entry_at'] <= at-self.step < position['deadline']:
                    q = position['trade']
                    if previous is None or not previous.valid:
                        terminate(at-self.step, unknown='MISSING_EXPOSED_BAR' if previous is None else 'INVALID_EXPOSED_BAR')
                    else:
                        result = in_bar(previous, q['direction'], q['stop'], q['take'],
                                        self.entry_take or previous.start != q['entry_at'])
                        if result:
                            terminate(previous.start, result[0], result[1], conflict=result[2])
                if previous is not None and previous.start.date() == day:
                    features.observe(previous, at)
                current = rows.get(at)
                # Only the current Open is observable at this boundary.
                if position:
                    q = position['trade']
                    open_ok = current is not None and current.open.is_finite() and current.open > 0 and not current.open % self.rules.tick(symbol, at)
                    if not open_ok:
                        terminate(at, unknown='MISSING_EXPOSED_BAR' if current is None else 'INVALID_EXPOSED_OPEN')
                    else:
                        result = at_open(current.open, q['direction'], q['stop'], at == position['deadline'])
                        if result:
                            reason = result[1]
                            if reason == 'SCHEDULED':
                                reason = 'TIME' if at == q['entry_at']+timedelta(minutes=q['max_hold_calendar_minutes']) else 'SESSION_FLAT'
                            terminate(at, result[0], reason, point=True)
                if pending and pending['planned_execution_at'] == at:
                    s = pending
                    pending = None
                    waiting = rows.get(s['waiting_bar_start'])
                    if waiting is None or not waiting.valid:
                        s['reason'] = 'NO_WAITING_BAR'
                    else:
                        s.update(order_admitted=True, order_sent_at=at)
                        q = {k: s.get(k) for k in ('signal_id', 'instrument', 'direction', 'signal_at',
                             'sweep_start', 'reclaim_start', 'waiting_bar_closed_at', 'order_sent_at',
                             'planned_execution_at', 'stop', 'window_end', 'max_hold_calendar_minutes')}
                        q.update(strategy=strategy.name, entry_at=None, entry_price=None,
                                 risk=None, take=None, model_filled=False, gross=None, gross_R=None,
                                 cost_c1=None, cost_R=None, net_c1=None, net_R_c1=None,
                                 initial_flat_assumed=True, initial_flat_proven=False,
                                 prior_unknown_requires_flat_assumption=prior_unknown)
                        open_ok = current is not None and current.open.is_finite() and current.open > 0 and not current.open % self.rules.tick(symbol, at)
                        if not open_ok:
                            reason = 'MISSING_EXECUTION_BAR' if current is None else 'INVALID_EXECUTION_OPEN'
                            s.update(status='UNKNOWN', reason=reason)
                            q.update(status='UNKNOWN', exit_reason='UNKNOWN', unknown_reason=reason,
                                     unknown_detected_at=at+self.step, exit_price=None,
                                     exit_at=None, exit_interval_start=None, exit_interval_end=None,
                                     resolved_at=None)
                            dt.append(q)
                            blocked = True
                        else:
                            grid = self.rules.tick(symbol, at)
                            geometry = entry_geometry(current.open, s['direction'], s['stop'], grid,
                                                      Decimal(str(s['target_gross_R'])))
                            if geometry is None:
                                s.update(status='NONFILL', reason='INVALID_STOP_GEOMETRY')
                            else:
                                risk, take = geometry
                                s.update(status='MODEL_FILLED', reason='', model_filled=True,
                                         entry_open=current.open, risk=risk, take=take)
                                q.update(entry_at=at, entry_price=current.open, risk=risk, take=take,
                                         model_filled=True, entry_tick=grid,
                                         cost_entry_c1=grid*Decimal(self.cost_sides))
                                dt.append(q)
                                position = {'trade': q, 'deadline': min(
                                    at+timedelta(minutes=s['max_hold_calendar_minutes']),
                                    s['window_end']-self.flat_bars*self.step)}
                bar_start = at-self.step
                window = next((w for w in windows if w[0] <= bar_start < w[1]), None)
                if window and day >= first_day:
                    ctx = Context(symbol, bar_start, at, window,
                                  self.rules.tick(symbol, bar_start), features.snapshot())
                    # Stable candidate tie-breaking matches the frozen ledger;
                    # strategy callback emission order cannot decide admission.
                    for event in sorted(strategy.on_bar(previous, ctx), key=lambda e: e['signal_id']):
                        s = dict(event, strategy=strategy.name, instrument=symbol, date=str(day),
                                 status='REJECTED', reason=event['base_reason'],
                                 order_admitted=False, model_filled=False,
                                 initial_flat_assumed=True, initial_flat_proven=False,
                                 prior_unknown_requires_flat_assumption=prior_unknown,
                                 recorded_at=at)
                        ds.append(s)
                        if s['base_reason'] != 'SIGNAL':
                            continue
                        if s['signal_at'] != at:
                            raise ValueError('STRATEGY_SIGNAL_NOT_AT_CURRENT_CLOSE')
                        s.update(waiting_bar_start=at, waiting_bar_closed_at=at+self.step,
                                 planned_execution_at=at+self.step,
                                 window_start=window[0], window_end=window[1])
                        if blocked:
                            s['reason'] = 'UNKNOWN_POSITION_BLOCK'
                        elif position or pending:
                            s['reason'] = 'POSITION_BUSY'
                        elif s['planned_execution_at'] >= window[1]-self.flat_bars*self.step:
                            s['reason'] = 'SESSION_LIMIT'
                        else:
                            pending = s
                at += self.step
            if position or pending:
                raise AssertionError('UNRESOLVED_DAY_WITHOUT_UNKNOWN')
            if windows and day >= first_day:
                for event in strategy.end_day():
                    ds.append(dict(event, strategy=strategy.name, instrument=symbol, date=str(day),
                                   status='REJECTED', reason=event['base_reason'],
                                   order_admitted=False, model_filled=False,
                                   initial_flat_assumed=True, initial_flat_proven=False,
                                   prior_unknown_requires_flat_assumption=prior_unknown))
                days.append(dict(instrument=symbol, date=str(day),
                                 signals=sum(s['base_reason']=='SIGNAL' for s in ds),
                                 admitted_orders=sum(s['order_admitted'] for s in ds),
                                 closed=sum(t['status']=='CLOSED' for t in dt),
                                 unknown=sum(t['status']=='UNKNOWN' for t in dt),
                                 prior_unknown_requires_flat_assumption=prior_unknown,
                                 initial_flat_assumed=True, initial_flat_proven=False))
            signals.extend(ds)
            trades.extend(dt)
            prior_unknown |= blocked
            day += timedelta(days=1)
        return signals, trades, days
