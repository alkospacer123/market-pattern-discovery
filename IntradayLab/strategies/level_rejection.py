"""Frozen six-bar failed-level signal grammar; execution is owned by core."""
from collections import deque
from datetime import timedelta


class LevelRejection:
    name = 'LEVEL_REJECTION_M5'

    def __init__(self, parameters):
        self.p = dict(parameters)
        if (self.p['level_lookback_completed_m5'], self.p['min_level_penetration_ticks'],
                self.p['min_close_reentry_ticks'], self.p['stop_beyond_extreme_ticks'],
                self.p['min_initial_price_risk_ticks'], self.p['dedup_same_instrument_same_direction_minutes']) != (6,1,1,1,4,30):
            raise ValueError('UNAPPROVED_LEVEL_REJECTION_GRAMMAR')

    def begin_day(self, symbol, day):
        self.symbol, self.day = symbol, day
        self.history = deque(maxlen=self.p['level_lookback_completed_m5'])
        self.window = self.last_start = None
        self.last_confirmed = {}

    def on_bar(self, bar, ctx):
        step = timedelta(minutes=5)
        if ctx.available_at != ctx.start+step or (bar and (bar.start != ctx.start or bar.available_at > ctx.available_at)):
            raise ValueError('UNCOMPLETED_OR_MISALIGNED_BAR')
        rec = dict(signal_id=f'{self.symbol}_{self.day}_{ctx.start:%H%M}', direction=0,
                   signal_at=None, test_start=ctx.start, raw_rejection=False, confirmed_signal=False)
        events = []
        reset = ('SESSION_BOUNDARY' if self.window != ctx.window else
                 'NONCONSECUTIVE_CALLBACK' if self.last_start is not None and self.last_start+step != ctx.start else '')
        if reset:
            self.history.clear();self.last_confirmed.clear()
            events.append(dict(rec,signal_id=rec['signal_id']+'_RESET',base_reason='RANGE_UNAVAILABLE',
                               reset_reason=reset,valid_preceding_bars=0))
        self.window,self.last_start=ctx.window,ctx.start
        if bar is None or not bar.valid or bar.start.date()!=self.day or not (
                ctx.window[0] <= bar.start and bar.available_at <= ctx.window[1]):
            self.history.clear();self.last_confirmed.clear()
            events.append(dict(rec,base_reason='RANGE_MISSING_BAR' if bar is None else 'RANGE_INVALID_BAR'))
            return events
        if len(self.history)==self.p['level_lookback_completed_m5']:
            high=max(b.high for b in self.history);low=min(b.low for b in self.history)
            rec.update(range_high=high,range_low=low,range_start=self.history[0].start,
                range_end=self.history[-1].available_at,range_bars=len(self.history),
                test_closed_at=ctx.available_at,test_high=bar.high,test_low=bar.low,
                test_close=bar.close,signal_tick=ctx.tick)
            long=bar.low<=low-self.p['min_level_penetration_ticks']*ctx.tick and bar.close>=low+self.p['min_close_reentry_ticks']*ctx.tick
            short=bar.high>=high+self.p['min_level_penetration_ticks']*ctx.tick and bar.close<=high-self.p['min_close_reentry_ticks']*ctx.tick
            if long and short:
                events.append(dict(rec,base_reason='AMBIGUOUS_BOTH_SIDES'))
            elif long or short:
                side=1 if long else -1;previous=self.last_confirmed.get(side)
                rec.update(signal_id=rec['signal_id']+f'_{side}',direction=side,raw_rejection=True,
                           previous_confirmed_start=previous,
                           level=low if long else high,opposite_level=high if long else low,
                           stop=bar.low-ctx.tick if long else bar.high+ctx.tick)
                if previous is not None and ctx.start-previous < timedelta(
                        minutes=self.p['dedup_same_instrument_same_direction_minutes']):
                    events.append(dict(rec,base_reason='DEDUP_30MIN'))
                else:
                    self.last_confirmed[side]=ctx.start
                    rec.update(signal_at=ctx.available_at,confirmed_signal=True,
                        target_gross_R=self.p['planned_net_to_net_R'],
                        target_net_R=self.p['planned_net_to_net_R'],target_mode='FULL_NET_C1_R',
                        max_hold_calendar_minutes=self.p['max_hold_calendar_minutes'],
                        entry_constraints=dict(directional_reference=rec['level'],
                            minimum_reference_ticks=self.p['min_close_reentry_ticks'],
                            minimum_risk_ticks=self.p['min_initial_price_risk_ticks'],
                            reserve_minutes=self.p['max_session_entry_slack_minutes'],
                            reason_labels={'OPEN_REFERENCE_LIMIT':'OPEN_RECLAIM_NOT_PERSISTENT',
                                           'RISK_BELOW_MINIMUM_TICKS':'RISK_BELOW_FOUR_TICKS'}))
                    events.append(dict(rec,base_reason='SIGNAL'))
        # The current test becomes history only after its own evaluation.
        self.history.append(bar)
        return events

    def end_day(self):
        return []
