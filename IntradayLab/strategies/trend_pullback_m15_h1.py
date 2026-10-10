"""One M15 correction plus a distinct M15 continuation under one available H1."""
from decimal import Decimal
from IntradayLab.core.h1_context import H1Context
from IntradayLab.core.m15_bars import FIFTEEN

FIXED_PARAMETERS = dict(signal_tf='M15',context_tf='H1',m15_children_m5=3,h1_children_m15=4,
    h1_delivery_delay_minutes=5,h1_direction='ONE_CLOSE_VS_OPEN',pullback_bars=1,
    confirmation_bars=1,confirmation_break_ticks=1,stop_mode='CORRECTION_AND_SIGNAL_EXTREME',
    stop_buffer_ticks=1,min_initial_risk_ticks=4,target_mode='FULL_NET_C1_R',target_net_R='3',
    wait_complete_m15_bars=1,min_entry_to_flat_minutes=35,max_hold_calendar_minutes=120,
    daily_trade_deadline='17:00',cost='C1')


class TrendPullback:
    name = 'TREND_PULLBACK_M15_H1'

    def __init__(self, parameters):
        if parameters != FIXED_PARAMETERS:
            raise ValueError('UNAPPROVED_TREND_PULLBACK_PARAMETERS')
        self.context_records = []

    def begin_day(self, symbol, day):
        self.symbol,self.day = symbol,day
        self.h1 = H1Context()
        self.previous = self.window = self.last_start = None

    def on_bar(self, bar, ctx):
        self.h1.observe(bar,ctx)
        if self.window != ctx.window or (self.last_start is not None and self.last_start+FIFTEEN != ctx.start):
            self.previous = None
        self.window,self.last_start = ctx.window,ctx.start
        ident = f'{self.symbol}_{self.day}_{ctx.start:%H%M}'
        context = dict(self.h1.describe(ctx),instrument=self.symbol,signal_id=ident,
            signal_start=ctx.start,window_start=ctx.window[0],window_end=ctx.window[1])
        rec = dict(signal_id=ident,direction=0,signal_at=None,test_start=ctx.start,
            pullback_confirmed=False,confirmed_signal=False,signal_tick=ctx.tick,
            context_valid=context['context_valid'],context_direction=context['context_direction'],
            context_reason=context['context_reason'],context_decision_id=ident,
            context_h1_start=context['h1_start'],context_h1_available_at=context['h1_available_at'],
            signal_child_m5_starts=','.join(str(ctx.start+i*FIFTEEN/3) for i in range(3)))
        valid = bar is not None and bar.valid and bar.start.date() == self.day and ctx.window[0] <= bar.start and bar.available_at <= ctx.window[1]
        if not valid:
            reason = 'M15_MISSING_BAR' if bar is None else 'M15_INVALID_BAR'
        elif not context['context_valid'] or not context['context_direction']:
            reason = context['context_reason']
        elif self.previous is None:
            reason = 'M15_CORRECTION_NOT_READY'
        else:
            a = self.previous;side = context['context_direction']
            rec.update(direction=side,correction_start=a.start,
                **{'correction_'+k:getattr(a,k) for k in ('open','high','low','close')},
                **{'test_'+k:getattr(bar,k) for k in ('open','high','low','close')},
                correction_child_m5_starts=','.join(str(a.start+i*FIFTEEN/3) for i in range(3)),
                test_closed_at=ctx.available_at)
            pull = side*(a.close-a.open) < 0
            continuation = side*(bar.close-bar.open) > 0 and (bar.close >= a.high+ctx.tick if side == 1 else bar.close <= a.low-ctx.tick)
            rec['pullback_confirmed'] = pull
            reason = 'NO_M15_CORRECTION' if not pull else 'NO_M15_CONTINUATION' if not continuation else 'SIGNAL'
            if reason == 'SIGNAL':
                rec.update(confirmed_signal=True,signal_at=ctx.available_at,
                    stop=min(a.low,bar.low)-ctx.tick if side == 1 else max(a.high,bar.high)+ctx.tick,
                    target_gross_R=Decimal(3),target_net_R=Decimal(3),target_mode='FULL_NET_C1_R',
                    max_hold_calendar_minutes=120,entry_constraints=dict(minimum_risk_ticks=4,
                        reserve_minutes=35,reason_labels={'RISK_BELOW_MINIMUM_TICKS':'RISK_BELOW_FOUR_TICKS'}))
        rec['base_reason'] = reason
        self.previous = bar if valid else None
        context.update(pullback_confirmed=rec['pullback_confirmed'],confirmed_signal=rec['confirmed_signal'],decision_reason=reason)
        self.context_records.append(context)
        return [rec]

    def end_day(self):
        return []
