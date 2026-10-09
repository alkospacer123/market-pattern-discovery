"""Fixed causal M5 research replay. No capital sizing or actual fill claims.

Only the execution adapter receives the bar being modelled. Strategy features
receive it at t+10m; orders know only a scheduled slot, never its existence.
Execution acknowledgements also wait until the OHLCV availability event.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
from statistics import median

from audit_session_mtf import is_trading_date
from session_mtf import Bar, FIVE, KNOWN_QUARANTINES, _validate

D = Decimal
ZERO = D(0)
END = datetime(2024, 1, 1)
CNY_SWITCH = datetime(2023, 9, 27, 19)
STRATEGIES = ("VWAP_MR", "MOMENTUM")
SYMBOLS = ("USDRUBF", "CNYRUBF", "GLDRUBF", "IMOEXF")


def available(b, p):
    return max(b.timestamp + timedelta(minutes=p['availability_minutes']),
               b.available_at or b.timestamp)


def next_slot(ready):
    """Strict inequality even if ready is aligned with an M5 open."""
    base = ready.replace(second=0, microsecond=0)
    base -= timedelta(minutes=base.minute % 5)
    return base + FIVE


def tick(symbol, at):
    if symbol == 'CNYRUBF':
        return D('0.01') if at < CNY_SWITCH else D('0.001')
    return {'USDRUBF': D('0.01'), 'GLDRUBF': D('0.1'), 'IMOEXF': D('0.5')}[symbol]


def rounded(value, step, up):
    return (value / step).to_integral_value(rounding=ROUND_CEILING if up else ROUND_FLOOR) * step


def windows(day):
    """Approved research intervals; not a certified complete session calendar.

    No retrospective September halt/restart B: missing slots are observed in
    replay. March's announced longer lunch break only postpones observations.
    Future 2024 quarantine is retained in allowed(), never accessed in replay.
    """
    if not is_trading_date(day):
        return []
    def at(h, m=0):
        return datetime(day.year, day.month, day.day, h, m)
    extended = datetime(2023, 3, 13).date() <= day < datetime(2023, 3, 21).date()
    return [(at(10), at(14)), (at(14, 15 if extended else 5), at(18, 50))]


def window_at(at):
    return next(((a, z) for a, z in windows(at.date()) if a <= at < z), None)


def allowed(symbol, at):
    w = window_at(at)
    return bool(w and at + FIVE <= w[1] and not any(
        q.start < at + FIVE and at < q.end for q in KNOWN_QUARANTINES.get(symbol, ())))


class Features:
    """Past observations only; ATR/range exclude the supplied signal bar."""
    def __init__(self, params, price_only=False):
        self.p = params
        self.price_only = price_only
        self.reset()

    def reset(self):
        self.bars = []
        self.vwaps = []
        self.weight = ZERO
        self.weighted_price = ZERO
        self.window = None

    def observe(self, b, asof):
        if asof < available(b, self.p):
            raise ValueError('OHLCV not available')
        w = window_at(b.timestamp)
        if not w or not allowed(b.symbol, b.timestamp):
            self.reset()
            return None
        if (w != self.window or (self.bars and b.timestamp != self.bars[-1].timestamp + FIVE)
                or (b.volume <= 0 and not self.price_only)):
            self.reset()
        if b.volume <= 0 and not self.price_only:
            return None
        self.window = w
        prior = self.bars
        atr = None
        if len(prior) >= self.p['warmup_prior_bars']:
            pairs = list(zip(prior[:-1], prior[1:]))[-self.p['atr_period']:]
            atr = sum((max(c.high-c.low, abs(c.high-a.close), abs(c.low-a.close))
                       for a, c in pairs), ZERO) / D(self.p['atr_period'])
        self.weight += b.volume
        self.weighted_price += (b.high + b.low + b.close) / 3 * b.volume
        vwap = self.weighted_price / self.weight if self.weight > 0 else None
        result = None
        if atr is not None and atr > 0:
            old = prior[-1]
            band = D(self.p['vwap_deviation_atr']) * atr
            prev_vwap = self.vwaps[-1]
            mr = 0
            if vwap is not None and prev_vwap is not None and old.close <= prev_vwap-band and vwap-band < b.close < vwap:
                mr = 1
            elif vwap is not None and prev_vwap is not None and old.close >= prev_vwap+band and vwap < b.close < vwap+band:
                mr = -1
            past_range = prior[-self.p['range_period']:]
            high, low = max(x.high for x in past_range), min(x.low for x in past_range)
            momentum = 1 if b.close > high else -1 if b.close < low else 0
            result = {'atr': atr, 'vwap': vwap, 'range_high': high, 'range_low': low,
                      'VWAP_MR': mr, 'MOMENTUM': momentum, 'prior_bars': len(prior)}
        self.bars.append(b)
        self.vwaps.append(vwap)
        return result


def protection(direction, close, atr, vwap, strategy, step, p):
    long = direction == 1
    stop = close - direction * D(p['stop_atr']) * atr
    take = vwap if strategy == 'VWAP_MR' else close + direction * D(p['momentum_take_atr']) * atr
    cap = close + direction * D(p['adverse_entry_cap_atr']) * atr
    return (rounded(stop, step, long), rounded(take, step, long), rounded(cap, step, not long))


def level_exit(b, direction, stop, take, step, entry_bar=False):
    """Resident protection scenario, all intrabar outcomes flagged as modelled."""
    stop_hit = b.low <= stop if direction == 1 else b.high >= stop
    tp_hit = b.high >= take+step if direction == 1 else b.low <= take-step
    flags = []
    if stop_hit:
        if tp_hit:
            flags.append('AMBIGUOUS_STOP_TP')
        if entry_bar:
            flags.append('AMBIGUOUS_ENTRY_EXIT')
        gap = b.open <= stop if direction == 1 else b.open >= stop
        price = min(b.open, stop) if direction == 1 else max(b.open, stop)
        if gap:
            flags.append('ADVERSE_STOP_GAP')
        return price, 'STOP', flags
    if tp_hit and not entry_bar:
        return take, 'TAKE', flags
    return None


def fill_units(requested, capacity=None):
    """Deterministic integer abstract-unit adapter, NOT OHLCV contract capacity.

    Real baseline capacity=None: explicitly conditional full-unit scenario.
    Synthetic tests supply capacity=0/1 to exercise nonfill and partial states.
    """
    if type(requested) is not int or requested < 1:
        raise ValueError('Positive integer abstract units required')
    if capacity is not None and (type(capacity) is not int or capacity < 0):
        raise ValueError('Invalid abstract-unit capacity')
    filled = requested if capacity is None else min(requested, capacity)
    return filled, requested-filled, 'NONFILL' if filled == 0 else 'PARTIAL' if filled < requested else 'MODELLED'


@dataclass
class Position:
    row: dict
    direction: int
    remaining: int
    stop: Decimal
    take: Decimal
    entry: Decimal
    entry_at: datetime
    boundary: datetime
    deadline: datetime
    reasons: list
    flags: set


class Replay:
    def __init__(self, symbol, strategy, params, abstract_units=1, capacities=None):
        if symbol not in SYMBOLS or strategy not in STRATEGIES:
            raise ValueError('Not in declared 8-run matrix')
        self.symbol, self.strategy, self.p = symbol, strategy, params
        self.units, self.capacities = abstract_units, capacities or {}
        fill_units(abstract_units)
        self.features = Features(params, price_only=strategy == "MOMENTUM")
        self.signals, self.events, self.ledger = [], [], []
        self.entry_order = self.close_order = self.position = None
        self.unknown_entry = None  # No order acknowledgement: never infer flat.
        self.unknown_entries = []
        self.counts = {'flat_target_breaches': 0, 'missing_observations': 0,
                       'gap_resets': 0, 'partial_events': 0, 'tp_touch_nonfills': 0,
                       'blocked_signals': 0, 'blocked_entry_opportunities': 0,
                       'unknown_flat_target_breaches': 0}
        self.last_mark = None
        self.last_window = None
        self.breached = set()
        self.month_marks = {}
        self.mtm_peak = self.mtm_drawdown = ZERO
        self.known_cash = ZERO
        self.unknown_liability = False
        self.month_peaks, self.month_drawdowns = {}, {}

    def event(self, at, kind, status, reason, signal_id='', requested=0, filled=0,
              residual=0, price=None, confirmed=None, flags=()):
        row = {'run': f'{self.strategy}_{self.symbol}', 'signal_id': signal_id,
               'kind': kind, 'status': status, 'reason': reason, 'at': str(at),
               'confirmed_at': str(confirmed) if confirmed else None,
               'requested_model_units': requested, 'filled_model_units': filled,
               'residual_model_units': residual, 'reference_price': price,
               'flags': '|'.join(sorted(flags))}
        self.events.append(row)
        if status == 'PARTIAL':
            self.counts['partial_events'] += 1
        return row

    def close_request(self, now, reason):
        if self.close_order or not self.position:
            return
        ready = now + timedelta(minutes=self.p['decision_delay_minutes'] + self.p['order_delay_minutes'])
        self.close_order = {'sent': now, 'ready': ready, 'target': next_slot(ready), 'reason': reason}
        p = self.position
        self.event(now, 'EXIT_ORDER', 'SUBMITTED', reason, p.row['signal_id'],
                   requested=p.remaining, residual=p.remaining)

    def missing_entry_target(self, now):
        """Absent OHLCV cannot prove rejection/expiry of an earlier order."""
        order = self.entry_order
        s = order['signal']
        status = 'UNRESOLVED_POSSIBLE_ENTRY_FILL'
        s['status'], s['reason'] = status, 'MISSING_OR_UNAVAILABLE_TARGET_BAR'
        boundary = window_at(order['target'])[1]
        row = {'run': s['run'], 'signal_id': s['signal_id'],
               'strategy': self.strategy, 'instrument': self.symbol,
               'direction': s['direction'], 'session_id': s['session_id'],
               'signal_at': s['signal_at'], 'available_at': s['available_at'],
               'ready_at': s['ready_at'], 'planned_execution_at': str(order['target']),
               'detected_at': str(now), 'status': status, 'reason': s['reason'],
               'requested_model_units': self.units, 'filled_model_units': None,
               'possible_residual_model_units': None, 'entry': None,
               'gross_price_pnl': None, 'c1_entry': None, 'net_model_c1': None,
               'funding_and_emergency_costs': 'UNRESOLVED',
               'prior_gap_notice_at': str(order['gap_notice']) if order.get('gap_notice') else None,
               'session_end': str(boundary), 'close_requirement_recorded': False,
               'flat_target_breach': False, 'resolution': 'UNRESOLVED_TO_2023_END'}
        self.unknown_entries.append(row)
        self.unknown_entry = row
        self.unknown_liability = True
        self.event(order['target'], 'ENTRY_OUTCOME', status, s['reason'],
                   s['signal_id'], self.units, None, None, confirmed=now)
        self.event(now, 'ENTRY_CANCEL_REQUEST', 'UNRESOLVED',
                   'LATE_TTL_CANCEL_DOES_NOT_PROVE_NONFILL', s['signal_id'],
                   self.units, None, None)
        self.entry_order = None  # Unknown intent persists separately, blocking entries.

    def unresolved(self, reason):
        if self.position and reason not in self.position.reasons:
            self.position.reasons.append(reason)
            self.unknown_liability = True

    def exit_fill(self, b, now, price, reason, flags=()):
        p = self.position
        q, left, status = fill_units(p.remaining, self.capacities.get(('EXIT', b.timestamp)))
        self.event(b.timestamp, 'EXIT', status, reason, p.row['signal_id'], p.remaining,
                   q, left, price if q else None, now, flags)
        p.flags.update(flags)
        if q:
            gross = q * p.direction * (price-p.entry)
            p.row['gross_price_pnl'] += gross
            self.known_cash += gross-q*tick(self.symbol,b.timestamp)
            p.row['c1_exit'] += q * tick(self.symbol, b.timestamp)
            p.row['exit'] = price
            p.row['exit_interval_start'] = str(b.timestamp)
            p.row['exit_interval_end'] = str(b.timestamp+FIVE)
            p.row['exit_confirmed_at'] = str(now)
            p.row['exit_reason'] = reason
            p.row['exit_filled_model_units'] += q
        p.remaining = left
        p.row['residual_model_units'] = left
        if left:
            # Retry at a strictly later bar; no filled quantity charged twice.
            self.close_order = None
            self.close_request(now, 'RESIDUAL_'+reason)
            return
        p.row['status'] = 'UNRESOLVED' if p.reasons else 'MODELLED'
        p.row['unresolved_reasons'] = '|'.join(p.reasons)
        p.row['ambiguity_flags'] = '|'.join(sorted(p.flags))
        p.row['c1_total'] = p.row['c1_entry']+p.row['c1_exit']
        p.row['net_model_c1'] = None if p.reasons else p.row['gross_price_pnl']-p.row['c1_total']
        risk = p.row['initial_risk_price_units']
        p.row['net_R'] = p.row['net_model_c1']/risk if p.row['net_model_c1'] is not None else None
        p.row['holding_minutes_bar_starts'] = D(str((b.timestamp-p.entry_at).total_seconds()/60))
        p.row['funding_and_emergency_costs'] = 'UNRESOLVED' if p.reasons else 'NO_SNAPSHOT_CROSSED'
        self.position = self.close_order = None

    def execute(self, b, now):
        """Environment side only. b is never passed to a decision before now."""
        t = b.timestamp
        if not allowed(self.symbol, t):
            return
        self.last_mark = b.close
        if self.position:
            p = self.position
            if t >= p.boundary:
                self.unresolved('BOUNDARY_EXPOSURE_FUNDING_OR_EMERGENCY_UNRESOLVED')
            if self.close_order and t >= self.close_order['target']:
                # Market exit at Open predates intrabar protection; adverse
                # opening stop gap remains priced at worse Open, never Stop.
                self.exit_fill(b, now, b.open, self.close_order['reason'])
            elif p.entry_at < t:
                ex = level_exit(b, p.direction, p.stop, p.take, tick(self.symbol,t))
                if ex:
                    self.exit_fill(b, now, *ex)
                elif (b.high >= p.take if p.direction == 1 else b.low <= p.take):
                    self.counts['tp_touch_nonfills'] += 1
                    self.event(t, 'TP', 'NONFILL', 'TOUCH_WITHOUT_TICK_PENETRATION',
                               p.row['signal_id'], p.remaining, 0, p.remaining, confirmed=now)
        order = self.entry_order
        if not order or t != order['target']:
            return
        self.entry_order = None  # TTL never picks a later bar.
        s = order['signal']
        direction, stop, take, cap = s['direction_sign'], s['stop'], s['take'], s['cap']
        good = (stop < b.open < take and b.open <= cap) if direction == 1 else (take < b.open < stop and b.open >= cap)
        if not good:
            s['status'] = 'NONFILL'
            s['reason'] = 'OPEN_CAP_OR_FROZEN_PROTECTION'
            self.event(t, 'ENTRY', 'NONFILL', s['reason'], s['signal_id'], self.units, 0, self.units, confirmed=now)
            self.event(now, 'ENTRY_CANCEL', 'CANCELLED', 'ONE_BAR_TTL', s['signal_id'], self.units, 0, self.units)
            return
        q, left, status = fill_units(self.units, self.capacities.get(('ENTRY',t)))
        self.event(t, 'ENTRY', status, 'CONDITIONAL_OPEN_SCENARIO', s['signal_id'], self.units, q, left, b.open if q else None, now)
        if left:
            self.event(now, 'ENTRY_CANCEL', 'CANCELLED', 'TTL_UNFILLED_REMAINDER',
                       s['signal_id'], left, 0, left)
        s['status'] = status
        s['reason'] = 'CONDITIONAL_OPEN_SCENARIO'
        if not q:
            return
        hold = self.p['vwap_max_hold_minutes' if self.strategy == 'VWAP_MR' else 'momentum_max_hold_minutes']
        row = {'run': s['run'], 'signal_id': s['signal_id'], 'strategy': self.strategy,
               'instrument': self.symbol, 'direction': s['direction'], 'session_id': s['session_id'],
               'signal_at': s['signal_at'], 'available_at': s['available_at'], 'ready_at': s['ready_at'],
               'planned_execution_at': s['planned_execution_at'], 'entry_interval_start': str(t),
               'entry_interval_end': str(t+FIVE), 'entry_confirmed_at': str(now),
               'entry': b.open, 'stop': stop, 'take': take, 'entry_cap': cap,
               'requested_model_units': self.units, 'entry_filled_model_units': q,
               'entry_cancelled_model_units': left, 'exit_filled_model_units': 0, 'residual_model_units': q,
               'status': 'OPEN_MODELLED', 'exit': None, 'exit_reason': None,
               'exit_interval_start': None, 'exit_interval_end': None, 'exit_confirmed_at': None,
               'gross_price_pnl': ZERO, 'c1_entry': q*tick(self.symbol,t), 'c1_exit': ZERO,
               'c1_total': q*tick(self.symbol,t), 'net_model_c1': None, 'net_R': None,
               'initial_risk_price_units': q*abs(b.open-stop), 'holding_minutes_bar_starts': None,
               'unresolved_reasons': '', 'ambiguity_flags': '', 'flat_target_breach': False,
               'funding_and_emergency_costs': 'PENDING', 'model_only': True}
        self.ledger.append(row)
        self.known_cash -= row['c1_entry']
        self.position = Position(row, direction, q, stop, take, b.open, t, window_at(t)[1],
                                 t+timedelta(minutes=hold), [], set())
        if order.get('gap_notice'):
            self.unresolved('PENDING_ENTRY_GAP_POSSIBLE_FILL_UNRESOLVED')
            self.close_request(now,'PENDING_ENTRY_GAP_EMERGENCY')
        ex = level_exit(b,direction,stop,take,tick(self.symbol,t),entry_bar=True)
        if ex:
            self.exit_fill(b, now, *ex)

    def decision(self, b, now, f):
        if not f or not f[self.strategy]:
            return
        direction = f[self.strategy]
        ready = now + timedelta(minutes=self.p['decision_delay_minutes']+self.p['order_delay_minutes'])
        target = next_slot(ready)
        w = window_at(b.timestamp)
        stop, take, cap = protection(direction,b.close,f['atr'],f['vwap'],self.strategy,tick(self.symbol,ready),self.p)
        signal_id = f'{self.strategy}_{self.symbol}_{len(self.signals)+1:06d}'
        s = {'run': f'{self.strategy}_{self.symbol}', 'signal_id': signal_id,
             'strategy': self.strategy, 'instrument': self.symbol,
             'signal_at': str(b.timestamp), 'available_at': str(now), 'ready_at': str(ready),
             'planned_execution_at': str(target), 'session_id': f'{w[0]}--{w[1]}',
             'direction': 'LONG' if direction == 1 else 'SHORT', 'direction_sign': direction,
             'signal_close': b.close, 'atr_shifted': f['atr'], 'vwap_approx': f['vwap'],
             'range_high_shifted': f['range_high'], 'range_low_shifted': f['range_low'],
             'stop': stop, 'take': take, 'cap': cap, 'status': 'SUBMITTED', 'reason': ''}
        self.signals.append(s)
        if self.unknown_entry:
            s['status'], s['reason'] = 'BLOCKED', 'UNRESOLVED_POSSIBLE_ENTRY_FILL'
            self.counts['blocked_signals'] += 1
            # Count otherwise-valid entry opportunities separately from all
            # blocked signals; schedule/levels use only known information.
            valid_slot = (allowed(self.symbol,target) and window_at(target) == w and
                          target+FIVE <= w[1]-timedelta(minutes=self.p['no_entry_before_boundary_minutes']))
            valid_levels = (stop < b.close < take) if direction == 1 else (take < b.close < stop)
            if valid_slot and valid_levels:
                self.counts['blocked_entry_opportunities'] += 1
        elif self.position or self.entry_order:
            s['status'], s['reason'] = 'SKIPPED', 'POSITION_OR_ORDER_BUSY'
        elif (not allowed(self.symbol,target) or window_at(target) != w or
              target+FIVE > w[1]-timedelta(minutes=self.p['no_entry_before_boundary_minutes'])):
            s['status'], s['reason'] = 'SKIPPED', 'KNOWN_BOUNDARY_ENTRY_CUTOFF'
        elif not ((stop < b.close < take) if direction == 1 else (take < b.close < stop)):
            s['status'], s['reason'] = 'SKIPPED', 'INVALID_ROUNDED_LEVELS'
        else:
            self.entry_order = {'target': target, 'ready': ready, 'signal': s}
            self.event(now,'ENTRY_ORDER','SUBMITTED','FIXED_SIGNAL',signal_id,self.units,0,self.units)

    def run(self, bars):
        # This guard runs BEFORE validation/features; even a future sentinel
        # object's OHLCV must never be inspected.
        if not bars or any(b.timestamp.year != 2023 for b in bars):
            raise ValueError('Stage 2 accepts only physical 2023 prefix')
        if any(b.symbol != self.symbol for b in bars):
            raise ValueError('Wrong instrument')
        _validate(bars,5)
        # Real FINAM inputs have no measured delivery stamps. Later synthetic
        # deliveries are allowed, still chronological and fail-closed on gaps.
        deliveries = {}
        for b in bars:
            at = available(b,self.p)
            at = at if at.second == 0 and at.microsecond == 0 and at.minute % 5 == 0 else next_slot(at)
            if at < END:
                deliveries.setdefault(at,[]).append(b)
        day = bars[0].timestamp.replace(hour=0,minute=0,second=0,microsecond=0)
        last_day = END - timedelta(days=1)  # calendar cutoff, never future-bar existence
        while day <= last_day:
            if windows(day.date()):
                now, end = day+timedelta(hours=10), day+timedelta(hours=19)
                while now <= end:
                    expected = now-timedelta(minutes=self.p['availability_minutes'])
                    delivered = deliveries.get(now,[])
                    observations = [b for b in delivered if allowed(self.symbol,b.timestamp)]
                    for b in sorted(observations,key=lambda b:b.timestamp):
                        self.execute(b,now)
                    if self.entry_order and self.entry_order['target'] <= expected:
                        self.missing_entry_target(now)
                    current = next((b for b in observations if b.timestamp == expected),None)
                    if allowed(self.symbol,expected) and current is None:
                        self.counts['missing_observations'] += 1
                        if self.features.bars:
                            self.counts['gap_resets'] += 1
                        self.features.reset()
                        if self.entry_order and not self.entry_order.get('gap_notice'):
                            order = self.entry_order
                            s = order['signal']
                            if order['target'] > now:
                                s['status'], s['reason'] = 'NONFILL', 'GAP_CANCEL_BEFORE_POSSIBLE_ENTRY'
                                self.event(now, 'ENTRY_CANCEL', 'CANCELLED', s['reason'], s['signal_id'], self.units, 0, self.units)
                                self.entry_order = None
                            else:
                                # Scheduled entry may already have happened:
                                # a cancellation cannot manufacture a flat.
                                order['gap_notice'] = now
                                self.event(now, 'ENTRY_CANCEL_REQUEST', 'UNRESOLVED',
                                           'POSSIBLE_FILL_AWAITING_ACK',s['signal_id'],self.units,0,self.units)
                        if self.position:
                            if self.close_order and self.close_order['target'] <= expected:
                                self.event(expected, 'EXIT', 'NONFILL', 'MISSING_EXIT_BAR',
                                           self.position.row['signal_id'], self.position.remaining,
                                           0, self.position.remaining, confirmed=now)
                            self.unresolved('MISSING_PATH_EMERGENCY_OBLIGATIONS_UNRESOLVED')
                            self.close_request(now,'DATA_GAP_EMERGENCY')
                    w_now = window_at(now)
                    if w_now != self.last_window:
                        self.features.reset()
                        self.last_window = w_now
                    p = self.position
                    unknown = self.unknown_entry
                    if unknown:
                        boundary = datetime.fromisoformat(unknown['session_end'])
                        if not unknown['close_requirement_recorded'] and now >= boundary-timedelta(minutes=self.p['close_before_boundary_minutes']):
                            unknown['close_requirement_recorded'] = True
                            self.event(now, 'EMERGENCY_CLOSE_REQUIREMENT', 'UNRESOLVED',
                                       'FILL_RECONCILIATION_REQUIRED_NO_KNOWN_CLOSE_QUANTITY',
                                       unknown['signal_id'], None, None, None)
                        if not unknown['flat_target_breach'] and now >= boundary-timedelta(minutes=self.p['flat_confirm_before_boundary_minutes']):
                            unknown['flat_target_breach'] = True
                            self.counts['unknown_flat_target_breaches'] += 1
                            self.event(now, 'FLAT_TARGET', 'UNRESOLVED',
                                       'POSSIBLE_ENTRY_FILL_NOT_RECONCILED',
                                       unknown['signal_id'], None, None, None)
                    if p:
                        if now >= p.boundary-timedelta(minutes=self.p['close_before_boundary_minutes']):
                            self.close_request(now,'SESSION_FLAT')
                        elif now >= p.deadline-FIVE:
                            self.close_request(now,'MAX_HOLD')
                        if now >= p.boundary-timedelta(minutes=self.p['flat_confirm_before_boundary_minutes']):
                            key = (p.row['signal_id'],p.boundary)
                            if key not in self.breached:
                                self.breached.add(key)
                                self.counts['flat_target_breaches'] += 1
                                p.row['flat_target_breach'] = True
                                self.event(now,'FLAT_TARGET','UNCONFIRMED','NO_CONFIRMED_FLAT_AT_B_MINUS_10',p.row['signal_id'],p.remaining,0,p.remaining)
                        # An exit continues across windows without new signals.
                    if current and w_now == window_at(current.timestamp):
                        f = self.features.observe(current,now)
                        self.decision(current,now,f)
                    elif current:
                        self.features.reset()
                    # Accounting diagnostic after observable closes, never an
                    # input to signals/sizing. Unknown liabilities stay null.
                    cash = self.known_cash
                    open_pnl = ZERO
                    remaining = 0
                    if self.position and self.last_mark is not None:
                        p = self.position
                        remaining = p.remaining
                        open_pnl = remaining*p.direction*(self.last_mark-p.entry)
                    marked = None if unknown else cash+open_pnl
                    key = str(now)[:7]
                    if marked is not None:
                        self.mtm_peak = max(self.mtm_peak,marked)
                        self.mtm_drawdown = max(self.mtm_drawdown,self.mtm_peak-marked)
                        self.month_peaks[key] = max(self.month_peaks.get(key,marked),marked)
                        self.month_drawdowns[key] = max(self.month_drawdowns.get(key,ZERO),self.month_peaks[key]-marked)
                    complete = not self.position and not self.unknown_liability
                    self.month_marks[key] = {'at':str(now),'residual_model_units':remaining,
                        'possible_residual_model_units':None if unknown else 0,
                        'model_flat_confirmed':not self.position and not unknown,
                        'mark':self.last_mark,'gross_open_price_pnl':None if unknown else open_pnl,
                        'known_cash_after_c1_price_units':cash,'known_mtm_after_c1_price_units':marked,
                        'net_complete':complete,'net_model_c1_mtm':marked if complete else None}
                    now += FIVE
            day += timedelta(days=1)
        if self.entry_order:
            s = self.entry_order['signal']
            s['status'],s['reason'] = 'NONFILL','DEVELOPMENT_END_TTL_CANCEL'
            self.event(END-FIVE,'ENTRY_CANCEL','CANCELLED',s['reason'],s['signal_id'],self.units,0,self.units)
        if self.position:
            p = self.position
            self.unresolved('OPEN_RESIDUAL_AT_2023_END_EXIT_UNRESOLVED')
            p.row.update(status='UNRESOLVED',unresolved_reasons='|'.join(p.reasons),
                         ambiguity_flags='|'.join(sorted(p.flags)),c1_total=p.row['c1_entry']+p.row['c1_exit'],
                         funding_and_emergency_costs='UNRESOLVED')
            self.event(END-FIVE,'RESIDUAL','UNRESOLVED','NO_2024_ACCESS_FOR_EXIT',p.row['signal_id'],p.remaining,0,p.remaining)
        if self.unknown_entry:
            self.event(END-FIVE, 'POSSIBLE_ENTRY_RESIDUAL', 'UNRESOLVED',
                       'NO_ORDER_ACK_NO_2024_ACCESS_FOR_RECONCILIATION',
                       self.unknown_entry['signal_id'], self.units, None, None)
        return self


def metrics(rows, unknown_entries=()):
    unresolved = [r for r in rows if r['status']=='UNRESOLVED']
    closed = [r for r in rows if r['net_model_c1'] is not None]
    nets = [r['net_model_c1'] for r in closed]
    positive = sum((n for n in nets if n > 0),ZERO)
    negative = -sum((n for n in nets if n < 0),ZERO)
    incomplete = bool(unresolved or unknown_entries)
    pf = positive/negative if negative else None
    cumulative = peak = dd = ZERO
    for n in nets:
        cumulative += n
        peak = max(peak,cumulative)
        dd = max(dd,peak-cumulative)
    return {'trades':len(rows),'closed_accounted_trades':len(closed),'unresolved':len(unresolved),
            'unknown_entry_orders':len(unknown_entries),
            'total_unresolved_cases':len(unresolved)+len(unknown_entries),
            'open_residual_model_units':sum(r['residual_model_units'] for r in rows),
            'possible_residual_model_units':None if unknown_entries else 0,
            'model_flat_confirmed':not unknown_entries and not any(r['residual_model_units'] for r in rows),
            'metric_status':'INCOMPLETE / CLOSED-ONLY DIAGNOSTIC' if incomplete else 'CONDITIONAL_MODEL_COMPLETE',
            'gross_known_price_pnl':sum((r['gross_price_pnl'] for r in rows),ZERO),
            'c1_known':sum((r['c1_entry']+r['c1_exit'] for r in rows),ZERO),
            'net_model_c1':None if incomplete else sum(nets,ZERO),
            'closed_only_net_c1':None if incomplete and not nets else sum(nets,ZERO),
            'closed_only_gross':sum((r['gross_price_pnl'] for r in closed),ZERO),
            'closed_only_c1':sum((r['c1_entry']+r['c1_exit'] for r in closed),ZERO),
            'win_rate':D(sum(n>0 for n in nets))/len(nets) if nets else None,
            'PF':pf,  # Closed-only diagnostic, retained for historical comparison.
            'full_PF':None if incomplete else pf,
            'PF_null_reason':'NO_CLOSED_TRADES' if not nets else 'NO_LOSSES' if not negative else None,
            'expectancy_price_units':sum(nets,ZERO)/len(nets) if nets else None,
            'net_R':sum((r['net_R'] for r in closed),ZERO) if closed else None,
            'mean_net_R':sum((r['net_R'] for r in closed),ZERO)/len(closed) if closed else None,
            'median_hold_minutes_bar_starts':median([r['holding_minutes_bar_starts'] for r in closed]) if closed else None,
            'closed_only_drawdown_price_units':dd if nets else None}
