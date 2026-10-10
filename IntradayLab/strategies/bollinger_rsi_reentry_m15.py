"""Causal standalone Bollinger20 / Wilder RSI14 re-entry on completed M15.

Indicators explicitly cross calendar sessions/days using real observations only.
Missing expected intrawindow slots clear the entire indicator history. B/C never
cross windows or days. This module has no prices after the current Close, no
orders, position management, costs, exits or P&L.
"""
from collections import deque
from decimal import Decimal as D
from IntradayLab.core.m15_bars import FIFTEEN

FIXED_PARAMETERS = dict(signal_tf='M15', m15_children_m5=3, bollinger_period=20,
    bollinger_stddev='2.0', bollinger_ddof=0, rsi_period=14, rsi_method='WILDER',
    rsi_long_threshold='35', rsi_short_threshold='65', confirmation_bars=1,
    stop_buffer_ticks=1, min_initial_risk_ticks=4, target_mode='FULL_NET_C1_R',
    target_net_R='1.5', wait_complete_m15_bars=1, min_entry_to_flat_minutes=35,
    max_hold_calendar_minutes=120, daily_trade_deadline='17:00', cost='C1',
    directions=['LONG', 'SHORT'])


class CompletedIndicators:
    """Population variance; SMA seed of 14 changes, then Wilder recurrence."""
    def __init__(self):
        self.closes = deque(maxlen=20)
        self.previous = None
        self.changes = 0
        self.gain = self.loss = D(0)

    def observe(self, close):
        if not close.is_finite() or close <= 0:
            raise ValueError('INVALID_COMPLETED_CLOSE')
        self.closes.append(close)
        if self.previous is not None:
            delta = close-self.previous
            up, down = max(delta,D(0)), max(-delta,D(0))
            self.changes += 1
            if self.changes <= 14:
                self.gain += up
                self.loss += down
                if self.changes == 14:
                    self.gain /= 14
                    self.loss /= 14
            else:
                self.gain = (13*self.gain+up)/14
                self.loss = (13*self.loss+down)/14
        self.previous = close
        rsi = None
        if self.changes >= 14:
            rsi = D(50) if not self.gain and not self.loss else D(100) if not self.loss else D(0) if not self.gain else D(100)-D(100)/(1+self.gain/self.loss)
        mean = sigma = lower = upper = None
        if len(self.closes) == 20:
            mean = sum(self.closes,D(0))/20
            sigma = (sum(((x-mean)**2 for x in self.closes),D(0))/20).sqrt()
            lower,upper = mean-2*sigma,mean+2*sigma
        return dict(close_count=len(self.closes),change_count=self.changes,
            indicators_ready=lower is not None and rsi is not None,
            sma20=mean,population_sigma=sigma,lower_band=lower,upper_band=upper,rsi14=rsi)


class BollingerRSIReentry:
    name = 'BOLLINGER_RSI_REENTRY_M15'

    def __init__(self, parameters):
        if parameters != FIXED_PARAMETERS:
            raise ValueError('UNAPPROVED_BOLLINGER_RSI_PARAMETERS')
        self.indicators = CompletedIndicators()
        self.symbol = self.day = self.window = self.last_start = self.previous = None

    def begin_day(self, symbol, day):
        if self.symbol is not None and symbol != self.symbol:
            raise ValueError('INDICATOR_INSTRUMENT_CHANGED')
        self.symbol,self.day = symbol,day
        self.previous = self.window = self.last_start = None

    def on_bar(self, bar, ctx):
        if ctx.available_at != ctx.start+FIFTEEN or (bar is not None and (bar.start != ctx.start or bar.duration != FIFTEEN or bar.available_at > ctx.available_at)):
            raise ValueError('UNCOMPLETED_OR_MISLABELLED_M15')
        boundary = self.window != ctx.window
        gap = not boundary and self.last_start is not None and self.last_start+FIFTEEN != ctx.start
        if boundary or gap:
            self.previous = None
        if gap:
            self.indicators = CompletedIndicators()
        self.window,self.last_start = ctx.window,ctx.start
        rec = dict(signal_id=f'{self.symbol}_{self.day}_{ctx.start:%H%M}', direction=0,
            signal_at=None,test_start=ctx.start,test_closed_at=ctx.available_at,
            signal_tick=ctx.tick,confirmed_signal=False,breach_candidate=False,
            signal_child_m5_starts=','.join(str(ctx.start+i*FIFTEEN/3) for i in range(3)))
        valid = bar is not None and bar.valid and bar.start.date() == self.day and ctx.window[0] <= bar.start and bar.available_at <= ctx.window[1]
        if not valid:
            self.indicators = CompletedIndicators()
            self.previous = None
            reason = 'M15_MISSING_BAR' if bar is None else 'M15_INVALID_BAR'
        else:
            snapshot = self.indicators.observe(bar.close)
            rec.update(snapshot,**{'test_'+k:getattr(bar,k) for k in ('open','high','low','close')})
            prior = self.previous
            if not snapshot['indicators_ready']:
                reason = 'INDICATORS_NOT_READY'
            elif prior is None or not prior[1]['indicators_ready']:
                reason = 'B_NOT_READY_OR_BOUNDARY'
            else:
                b,bi = prior
                side = 1 if b.close < bi['lower_band'] and bi['rsi14'] <= 35 else -1 if b.close > bi['upper_band'] and bi['rsi14'] >= 65 else 0
                rec.update(direction=side,breach_candidate=bool(side),breach_start=b.start,
                    breach_closed_at=b.available_at,
                    **{'breach_'+k:getattr(b,k) for k in ('open','high','low','close')},
                    **{'breach_'+k:bi[k] for k in ('sma20','population_sigma','lower_band','upper_band','rsi14')},
                    breach_child_m5_starts=','.join(str(b.start+i*FIFTEEN/3) for i in range(3)))
                inside = snapshot['lower_band'] <= bar.close <= snapshot['upper_band']
                improvement = side and side*(snapshot['rsi14']-bi['rsi14']) > 0
                reason = 'NO_BREACH_B' if not side else 'NO_REENTRY_C' if not inside else 'NO_RSI_IMPROVEMENT' if not improvement else 'SIGNAL'
                if reason == 'SIGNAL':
                    rec.update(confirmed_signal=True,signal_at=ctx.available_at,
                        stop=min(b.low,bar.low)-ctx.tick if side == 1 else max(b.high,bar.high)+ctx.tick,
                        target_gross_R=D('1.5'),target_net_R=D('1.5'),target_mode='FULL_NET_C1_R',
                        max_hold_calendar_minutes=120,entry_constraints=dict(minimum_risk_ticks=4,
                            reserve_minutes=35,reason_labels={'RISK_BELOW_MINIMUM_TICKS':'RISK_BELOW_FOUR_TICKS'}))
            self.previous = (bar,snapshot)
        rec['base_reason'] = reason
        return [rec]

    def end_day(self):
        return []
