"""Predeclared Squeeze v1. Completed observations only; no other strategy signal.

The conditional execution adapter evaluates pre-scheduled candles at their
delivery clock. It never supplies future Open/existence to signal decisions.
Calendar/tick primitives and exact M30 composition are the accepted Lab contract.
"""
from datetime import datetime, timedelta
from decimal import Decimal, localcontext

from m5_baseline import windows, window_at, allowed, next_slot, tick, rounded
from causal_mtf import DerivedContext

D = Decimal
FIVE = timedelta(minutes=5)
ZERO = D(0)


class Indicators:
    def __init__(self):
        self.reset()

    def reset(self):
        self.bars, self.trs = [], []
        self.ema = self.atr = None

    def observe(self, b):
        with localcontext() as ctx:
            ctx.prec = 34
            prev = self.bars[-1].close if self.bars else b.close
            tr = max(b.high-b.low, abs(b.high-prev), abs(b.low-prev))
            self.bars.append(b)
            self.trs.append(tr)
            n = len(self.bars)
            if n < 20:
                return None
            closes = [x.close for x in self.bars[-20:]]
            mean = sum(closes, ZERO)/20
            variance = sum(((x-mean)**2 for x in closes), ZERO)/20
            sigma = variance.sqrt()
            if n == 20:
                self.ema = mean
                self.atr = sum(self.trs, ZERO)/20
            else:
                self.ema += D(2)/21*(b.close-self.ema)
                self.atr = (19*self.atr+tr)/20
            upper, lower = mean+2*sigma, mean-2*sigma
            ku, kl = self.ema+D('1.5')*self.atr, self.ema-D('1.5')*self.atr
            return dict(at=b.timestamp, warmup=n, sma20=mean, variance20=variance,
                        std20=sigma, ema20=self.ema, tr=tr, atr20=self.atr,
                        bb_upper=upper, bb_lower=lower, kc_upper=ku, kc_lower=kl,
                        squeeze=upper < ku and lower > kl)


class Cycles:
    def __init__(self, symbol):
        self.symbol, self.rows, self.active = symbol, [], None

    def reset(self, at, reason):
        if self.active and not self.active['terminal_reason']:
            e = self.active
            e['terminal_at'] = at
            e['terminal_reason'] = reason if e['bars'] >= 3 else 'UNCONFIRMED_LT3'
        self.active = None

    def observe(self, b, f, now):
        if f is None:
            return None
        if f['squeeze']:
            if self.active and self.active['released_at'] is not None:
                self.reset(now, 'NO_EXPANSION_NEXT_SQUEEZE')
            if self.active is None:
                e = dict(cycle_id=f'SQ_{self.symbol}_{len(self.rows)+1:06d}', start=b.timestamp,
                         end=b.timestamp, bars=0, range_high=b.high, range_low=b.low,
                         confirmed_at=None, released_at=None, terminal_at=None,
                         terminal_reason='', signal_at=None, direction=None)
                self.rows.append(e)
                self.active = e
            e = self.active
            e['end'], e['bars'] = b.timestamp, e['bars']+1
            e['range_high'] = max(e['range_high'], b.high)
            e['range_low'] = min(e['range_low'], b.low)
            if e['bars'] == 3:
                e['confirmed_at'] = now
            return None
        e = self.active
        if not e or e['terminal_reason']:
            return None
        if e['released_at'] is None:
            e['released_at'] = now
            if e['bars'] < 3:
                self.reset(now, 'UNCONFIRMED_LT3')
                return None
        direction = 1 if b.close > e['range_high'] else -1 if b.close < e['range_low'] else 0
        if not direction:
            return None
        e.update(terminal_at=now, terminal_reason='SIGNAL', signal_at=b.timestamp,
                 direction='LONG' if direction == 1 else 'SHORT')
        return dict(signal_id=e['cycle_id'], direction_sign=direction, direction=e['direction'],
                    range_start=e['start'], range_end=e['end'], squeeze_bars=e['bars'],
                    range_high=e['range_high'], range_low=e['range_low'])


def geometry(symbol, signal, price, at):
    """Same frozen admissibility at decision Close and exact execution Open."""
    with localcontext() as ctx:
        ctx.prec = 34
        step = tick(symbol, at)
        d, atr, edge = signal['direction_sign'], signal['atr20'], signal['edge']
        risk = d*(price-signal['stop'])
        if price % step:
            return None, 'OPEN_OFF_GRID'
        if d*(price-edge) <= 0:
            return None, 'BREAKOUT_NOT_PERSISTENT'
        if d*(price-signal['cap']) > 0:
            return None, 'EXTENSION_OVER_0_5_ATR'
        if risk < 4*step:
            return None, 'RISK_BELOW_FOUR_TICKS'
        c1 = 2*step
        take = rounded(price+d*(3*risk+c1), step, d == 1)
        gross = d*(take-price)
        if gross > 3*atr:
            return None, 'TARGET_OVER_THREE_ATR'
        return dict(take=take, initial_risk=risk, planned_c1=c1,
                    planned_gross_reward=gross, planned_net_reward=gross-c1,
                    planned_net_RR=(gross-c1)/risk, target_atr=gross/atr), None


class Replay:
    def __init__(self, symbol, architecture, delay=10):
        if architecture not in ('SQUEEZE_M5', 'SQUEEZE_M30_M5') or delay not in (10, 15):
            raise ValueError('Undeclared experiment')
        self.symbol, self.architecture, self.delay = symbol, architecture, delay
        self.signals, self.ledger, self.events, self.features = [], [], [], []
        self.indicators, self.cycles = Indicators(), Cycles(symbol)
        self.position = self.order = self.close_order = None
        self.last_observed = self.last_window = None

    def event(self, now, kind, sid='', reason='', price=None, confirmed=None, flags=''):
        self.events.append(dict(at=now, kind=kind, signal_id=sid, reason=reason,
                                price=price, confirmed_at=confirmed, flags=flags))

    def request(self, now, reason):
        if self.close_order is None:
            self.close_order = dict(target=next_slot(now), reason=reason)
            self.event(now, 'EXIT_ORDER', self.position['signal_id'], reason)

    def unknown(self, now, reason):
        p = self.position
        if p['status'] != 'UNKNOWN':
            p.update(status='UNKNOWN', gross=None, c1_exit=None, c1=None, net=None, net_R=None,
                     unknown_at=now, unknown_reason=reason, excursion_status='LOWER_BOUND_BEFORE_UNKNOWN')
            self.event(now, 'UNKNOWN_PATH', p['signal_id'], reason)
        self.request(now, 'DATA_GAP_EMERGENCY')

    def finish(self, t, now, price, reason, flags=''):
        p = self.position
        if p['status'] == 'UNKNOWN':
            p.update(exit_reason='UNKNOWN_PATH_REDUCE_ALL', model_flat_at=now, model_flat_slot=t)
            self.event(t, 'CONDITIONAL_FLAT', p['signal_id'], 'PAST_PAYOFF_REMAINS_UNKNOWN', confirmed=now)
        else:
            gross = p['direction_sign']*(price-p['entry'])
            c1_exit = tick(self.symbol, t)
            net = gross-p['c1_entry']-c1_exit
            p['mfe_R'] = max(p['mfe_R'], gross/p['initial_risk'])
            p['mae_R'] = max(p['mae_R'], -gross/p['initial_risk'])
            p.update(status='CLOSED', exit=price, exit_at=t, exit_ack=now, exit_reason=reason,
                     gross=gross, c1_exit=c1_exit, c1=p['c1_entry']+c1_exit, net=net,
                     net_R=net/p['initial_risk'], gross_R=gross/p['initial_risk'],
                     hold_minutes=int((t-p['entry_at']).total_seconds()/60),
                     flags=flags, model_flat_at=now, model_flat_slot=t)
            self.event(t, 'EXIT', p['signal_id'], reason, price, now, flags)
        self.position = self.close_order = None

    def resident(self, b, now, entry_bar=False):
        p = self.position
        d, stop, take, step = p['direction_sign'], p['stop'], p['take'], tick(self.symbol, b.timestamp)
        sh = b.low <= stop if d == 1 else b.high >= stop
        th = b.high >= take+step if d == 1 else b.low <= take-step
        if sh:
            flags = []
            if th:
                flags.append('STOP_FIRST_BOTH_LEVELS')
            if entry_bar:
                flags.append('ENTRY_BAR_STOP')
            if d*(b.open-stop) <= 0:
                flags.append('ADVERSE_STOP_GAP')
            self.finish(b.timestamp, now, min(b.open, stop) if d == 1 else max(b.open, stop),
                        'STOP', '|'.join(flags))
        elif th and not entry_bar:
            p['mfe_R'] = max(p['mfe_R'], d*(take-p['entry'])/p['initial_risk'])
            self.finish(b.timestamp, now, take, 'TAKE')
        else:
            # Do not infer favorable sequencing in the entry candle.
            if not entry_bar:
                p['mfe_R'] = max(p['mfe_R'], d*((b.high if d == 1 else b.low)-p['entry'])/p['initial_risk'])
                p['mae_R'] = max(p['mae_R'], -d*((b.low if d == 1 else b.high)-p['entry'])/p['initial_risk'])
            if th and entry_bar:
                self.event(b.timestamp, 'TP_NONFILL', p['signal_id'], 'ENTRY_BAR_TP_FORBIDDEN', confirmed=now)
            elif (b.high >= take if d == 1 else b.low <= take):
                self.event(b.timestamp, 'TP_NONFILL', p['signal_id'], 'TOUCH_WITHOUT_TICK_PENETRATION', confirmed=now)

    def entry(self, b, now):
        s, self.order = self.order, None
        g, reason = geometry(self.symbol, s, b.open, b.timestamp)
        if reason:
            s.update(status='NONFILL', reason=reason)
            self.event(b.timestamp, 'ENTRY_NONFILL', s['signal_id'], reason, confirmed=now)
            return
        s.update(status='MODELLED', reason='CONDITIONAL_EXACT_OPEN')
        p = {k: s[k] for k in ('signal_id', 'direction', 'direction_sign', 'signal_at', 'available_at',
                              'planned_execution_at', 'range_high', 'range_low', 'edge', 'atr20', 'stop', 'cap')}
        p.update(g)
        p.update(status='OPEN', entry=b.open, entry_at=b.timestamp, entry_ack=now,
                 c1_entry=tick(self.symbol, b.timestamp), c1_exit=None, c1=None, gross=None, net=None,
                 net_R=None, gross_R=None, exit=None, exit_at=None, exit_ack=None, exit_reason='',
                 hold_minutes=None, model_flat_at=None, model_flat_slot=None, unknown_at=None,
                 unknown_reason='', flat_target_breach=False, flags='', mfe_R=ZERO, mae_R=ZERO,
                 excursion_status='CONSERVATIVE_KNOWN_PATH', boundary=window_at(b.timestamp)[1])
        self.ledger.append(p)
        self.position = p
        self.event(b.timestamp, 'ENTRY', p['signal_id'], 'CONDITIONAL_EXACT_OPEN', b.open, now)
        self.resident(b, now, True)

    def context(self, now, w, d):
        pair, reason = self.mtf.pair(now, w)
        out = dict(mtf_first=None, mtf_last=None, mtf_available_at=None, mtf_direction=None,
                   mtf_reason=reason)
        if pair is None:
            return out, reason
        a, b = pair
        ao, _, _, ac, _ = a.ohlcv
        bo, _, _, bc, _ = b.ohlcv
        trend = 1 if ac > ao and bc > bo and bc > ac else -1 if ac < ao and bc < bo and bc < ac else 0
        reason = 'MTF_SUSTAINED_ADVERSE_DIRECTION' if trend == -d else None
        out.update(mtf_first=a.start, mtf_last=b.start, mtf_available_at=max(a.available_at, b.available_at),
                   mtf_direction=trend, mtf_reason=reason)
        return out, reason

    def decision(self, b, f, now, w):
        s = self.cycles.observe(b, f, now)
        if not s:
            return
        d, atr = s['direction_sign'], f['atr20']
        step = tick(self.symbol, now)
        edge = s['range_high'] if d == 1 else s['range_low']
        s.update(f)
        s.update(signal_at=b.timestamp, signal_close=b.close, available_at=now, ready_at=now,
                 planned_execution_at=next_slot(now), edge=edge,
                 stop=rounded(edge-d*D('.25')*atr, step, d == 1),
                 cap=rounded(edge+d*D('.5')*atr, step, d == -1), status='SUBMITTED', reason='',
                 mtf_first=None, mtf_last=None, mtf_available_at=None, mtf_direction=None, mtf_reason=None)
        if self.architecture == 'SQUEEZE_M30_M5':
            record, context_reason = self.context(now, w, d)
            s.update(record)
        else:
            context_reason = None
        _, reason = geometry(self.symbol, s, b.close, now)
        if self.position or self.order:
            reason = 'POSITION_OR_ORDER_BUSY'
        elif window_at(s['planned_execution_at']) != w or s['planned_execution_at']+FIVE > w[1]-timedelta(minutes=30):
            reason = 'KNOWN_BOUNDARY_ENTRY_CUTOFF'
        elif context_reason:
            reason = context_reason
        if reason:
            s.update(status='FILTERED', reason=reason)
        else:
            self.order = s
            self.event(now, 'ENTRY_ORDER', s['signal_id'], 'FIXED_SQUEEZE_BREAKOUT')
        self.signals.append(s)

    def run(self, bars):
        if not bars or any(b.timestamp.year != 2023 for b in bars):
            raise ValueError('Only physical 2023 data')
        index = {b.timestamp: b for b in bars}
        self.mtf = DerivedContext([b for b in bars if b.volume > 0], 30, {'availability_minutes': self.delay}) if self.architecture.endswith('M30_M5') else None
        day = bars[0].timestamp.date()
        with localcontext() as ctx:
            ctx.prec = 34
            while day <= datetime(2023, 12, 31).date():
                if windows(day):
                    now = datetime.combine(day, datetime.min.time())+timedelta(hours=10)
                    end = now+timedelta(hours=9, minutes=10)
                    while now <= end:
                        t = now-timedelta(minutes=self.delay)
                        w = window_at(t)
                        b = index.get(t) if allowed(self.symbol, t) else None
                        if b and b.volume <= 0:
                            b = None
                        if w != self.last_window or (w and (not b or (self.last_observed is not None and t != self.last_observed+FIVE))):
                            self.indicators.reset()
                            self.cycles.reset(now, 'NO_EXPANSION_SESSION' if w != self.last_window else 'NO_EXPANSION_GAP')
                            self.last_observed = None
                        self.last_window = w
                        # Adapter processes only outcomes of prior commitments.
                        if b:
                            if self.position and t >= self.position['entry_at']:
                                if self.close_order and t >= self.close_order['target']:
                                    self.finish(t, now, b.open, self.close_order['reason'])
                                elif self.position['status'] != 'UNKNOWN' and t > self.position['entry_at']:
                                    self.resident(b, now)
                            if self.order and t == self.order['planned_execution_at']:
                                self.entry(b, now)
                        if self.order and t >= self.order['planned_execution_at']:
                            s, self.order = self.order, None
                            s.update(status='NO_BAR_NO_MODEL_FILL', reason='EXACT_TARGET_ABSENT')
                            self.event(s['planned_execution_at'], 'ENTRY_NONFILL', s['signal_id'], s['reason'], confirmed=now)
                        if w and not b:
                            if self.order and self.order['planned_execution_at'] > now:
                                s, self.order = self.order, None
                                s.update(status='NONFILL', reason='OBSERVED_GAP_BEFORE_ENTRY')
                                self.event(now, 'ENTRY_CANCEL', s['signal_id'], s['reason'])
                            if self.position and t >= self.position['entry_at']:
                                self.unknown(now, 'MISSING_EXPOSED_M5_PATH')
                        if self.position:
                            p = self.position
                            boundary = p['boundary']
                            if now >= boundary-timedelta(minutes=10) and not p['flat_target_breach']:
                                p['flat_target_breach'] = True
                                self.event(now, 'FLAT_TARGET_BREACH', p['signal_id'], 'NO_ACK_FLAT_AT_B_MINUS_10')
                            if now >= boundary:
                                self.unknown(now, 'SESSION_BOUNDARY_EXPOSURE_UNRESOLVED')
                            sent = boundary-timedelta(minutes=15+self.delay)
                            if now >= sent:
                                self.request(now, 'SESSION_FLAT')
                            elif now >= p['entry_at']+timedelta(minutes=115):
                                self.request(now, 'MAX_HOLD')
                            if b and t >= p['entry_at'] and self.close_order is None and p['status'] != 'UNKNOWN' and p['range_low'] <= b.close <= p['range_high']:
                                self.request(now, 'FAILED_BREAKOUT')
                        if b:
                            f = self.indicators.observe(b)
                            self.last_observed = t
                            if f:
                                self.features.append(f.copy())
                            self.decision(b, f, now, w)
                        now += FIVE
                day += timedelta(days=1)
            self.cycles.reset(datetime(2024, 1, 1), 'NO_EXPANSION_YEAR_END')
            if self.position:
                self.unknown(datetime(2024, 1, 1), 'UNRESOLVED_AT_DEVELOPMENT_END')
        return self
