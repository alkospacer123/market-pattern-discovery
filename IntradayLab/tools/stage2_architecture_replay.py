"""Bounded fixed-rule Stage 2 architectures; frozen v2 execution is reused.

All adaptive exits/stop amendments decided on a delivered bar are scheduled
strictly after the decision/order delay. A t+10 decision cannot alter protection
on the already elapsed t+5/t+10 bars, even though their acknowledgements arrive
later. Resident stop ordering and unknown-path handling remain v2's contract.
"""
from datetime import datetime, timedelta
from decimal import Decimal as D

from m5_conditional_v2 import (Replay, Features, FIVE, ZERO, available, next_slot,
    tick, rounded, protection, close_submission_deadline)
from stage2_architecture_analysis import Indicators

ARCHITECTURES = ('FROZEN_V2','ENTRY','MANAGEMENT','ENTRY_MANAGEMENT','FULL_M5')


class ArchitectureReplay(Replay):
    def __init__(self,symbol,strategy,params,architecture,defaults,**kwargs):
        if architecture not in ARCHITECTURES:
            raise ValueError('Undeclared architecture')
        super().__init__(symbol,strategy,params,**kwargs)
        self.architecture,self.defaults=architecture,defaults
        self.entry_quality=architecture in ('ENTRY','ENTRY_MANAGEMENT','FULL_M5')
        self.management=architecture in ('MANAGEMENT','ENTRY_MANAGEMENT','FULL_M5')
        self.regime=architecture=='FULL_M5'
        self.indicators=Indicators(defaults['indicator_period'],defaults['ema_period'])
        self.features=ArchitectureFeatures(params,self.indicators,strategy=='MOMENTUM')
        self.pending_amendments=[]
        self.amendments=[]
        self.current_context={}

    def gate_entry(self,s,price):
        d=s['direction_sign']; step=tick(self.symbol,datetime.fromisoformat(s['planned_execution_at']))
        risk=d*(price-s['stop']); reward=d*(s['take']-price)
        if risk<=0 or risk<D(self.defaults['minimum_risk_ticks'])*step:
            return 'RISK_BELOW_FOUR_TICKS'
        if reward-2*step < risk+2*step:
            return 'NET_TARGET_BELOW_NET_RISK'
        if self.strategy=='MOMENTUM':
            edge=s['range_high_shifted'] if d==1 else s['range_low_shifted']
            extension=d*(price-edge)/s['atr_shifted']
            if extension<=0:
                return 'BREAKOUT_NOT_PERSISTENT'
            if extension>D(self.defaults['max_breakout_extension_atr']):
                return 'BREAKOUT_ALREADY_EXTENDED'
        return None

    def decision(self,b,now,f):
        self.current_context=self.features.context
        # Management uses only delivered complete OHLCV, irrespective of a new
        # entry signal. Base timers run first and keep session-flat priority.
        if self.management and self.position and not self.close_order:
            self.manage(b,now,f)
        if not f or not f[self.strategy]: return
        before=len(self.signals)
        super().decision(b,now,f)
        if len(self.signals)==before: return
        s=self.signals[-1]; d=s['direction_sign']
        c=self.current_context
        s.update(architecture=self.architecture,**c,
            signal_tr_atr=max(b.high-b.low,abs(b.high-self.features.prior_close),abs(b.low-self.features.prior_close))/f['atr'],
            swing_low=min(x.low for x in self.features.bars[-3:]),
            swing_high=max(x.high for x in self.features.bars[-3:]))
        if s['status']!='SUBMITTED': return
        reason=None
        if self.management:
            atr=c.get('atr14')
            if atr is None or atr<=0:
                reason='ATR14_NOT_READY'
            else:
                step=tick(self.symbol,now)
                raw=b.close-d*D(self.p['stop_atr'])*atr
                if self.strategy=='MOMENTUM':
                    edge=s['range_high_shifted'] if d==1 else s['range_low_shifted']
                    structure=edge-d*D(self.defaults['breakout_stop_buffer_atr'])*atr
                else:
                    structure=(s['swing_low']-step) if d==1 else (s['swing_high']+step)
                raw=min(raw,structure) if d==1 else max(raw,structure)
                s['stop']=rounded(raw,step,d==1)
                # TP remains the decision VWAP for MR; Momentum entry still has
                # its original admissible price interval, then becomes a runner.
                s['initial_stop_basis']='MAX_ATR14_AND_FROZEN_STRUCTURE'
        if self.entry_quality and not reason:
            # Decision check at adverse cap is conservative for reward/risk;
            # actual filled Open must also pass. Favorable gaps can shrink risk.
            reason=self.gate_entry(s,s['cap'])
            if self.strategy=='MOMENTUM' and not reason:
                edge=s['range_high_shifted'] if d==1 else s['range_low_shifted']
                if d*(b.close-edge)>D(self.defaults['max_breakout_extension_atr'])*f['atr']:
                    reason='SIGNAL_ALREADY_EXTENDED'
                elif s['signal_tr_atr']>D(self.defaults['max_signal_tr_atr']):
                    reason='SIGNAL_RANGE_EXPANSION_GT_2_ATR'
        if self.regime and not reason:
            adx,pdi,mdi=c.get('adx14'),c.get('plus_di14'),c.get('minus_di14')
            aligned=(pdi>mdi if d==1 else mdi>pdi) if pdi is not None else False
            if adx is None:
                reason='ADX14_NOT_READY'
            elif self.strategy=='MOMENTUM' and (adx<D(self.defaults['trend_adx']) or not aligned):
                reason='MOMENTUM_ADX_DI_REGIME'
            elif self.strategy=='VWAP_MR' and adx>=D(self.defaults['trend_adx']) and not aligned:
                reason='VWAP_STRONG_ADVERSE_ADX_DI'
        if reason:
            # Replace only a just-created scenario, never cancel a different
            # pending order because another signal was rejected.
            s['status'],s['reason']='FILTERED',reason
            self.entry_order=None
            self.event(now,'ENTRY_CANCEL','CANCELLED',reason,s['signal_id'],self.units,0,self.units)
        elif self.entry_order:
            self.entry_order['signal']=s

    def execute(self,b,now):
        p=self.position
        while p and self.pending_amendments and b.timestamp>=self.pending_amendments[0]['effective_at']:
            amend=self.pending_amendments.pop(0)
            if amend['signal_id']!=p.row['signal_id']:
                raise ValueError('Stop amendment belongs to another trade')
            p.stop=amend['stop']
            p.row['effective_stop_state']=amend['state']
            self.event(b.timestamp,'STOP_AMENDMENT','MODELLED',amend['state'],p.row['signal_id'],
                p.remaining,0,p.remaining,price=p.stop,confirmed=now)
        if p and self.management and self.strategy=='MOMENTUM':
            p.take=D('Infinity') if p.direction==1 else D('-Infinity')
        order=self.entry_order
        if order and b.timestamp==order['target'] and self.entry_quality:
            s=order['signal']; reason=self.gate_entry(s,b.open)
            if reason:
                s['status'],s['reason']='NONFILL',reason
                self.event(b.timestamp,'ENTRY','NONFILL',reason,s['signal_id'],self.units,0,self.units,confirmed=now)
                self.entry_order=None
        before=len(self.ledger)
        super().execute(b,now)
        if len(self.ledger)>before:
            r=self.ledger[-1]
            r.update(architecture=self.architecture,effective_stop_state='INITIAL',
                runner=self.management and self.strategy=='MOMENTUM')
            if self.position and self.position.row is r:
                self.position.best_observed_price=self.position.entry
        if not self.position:
            self.pending_amendments=[]

    def exit_fill(self,b,now,price,reason,flags=()):
        if reason=='STOP' and self.position:
            state=self.position.row.get('effective_stop_state','INITIAL')
            reason={'BE':'BREAKEVEN_STOP','TRAIL':'TRAIL_STOP'}.get(state,'STOP')
        super().exit_fill(b,now,price,reason,flags)

    def manage(self,b,now,f):
        p=self.position
        if not p or 'UNKNOWN_PATH_OUTCOME' in p.flags or b.timestamp<p.entry_at:
            return
        # Frozen regime/structure data belongs to this trade's original signal.
        s=next(s for s in reversed(self.signals) if s['signal_id']==p.row['signal_id'])
        d=p.direction; r=p.row['initial_risk_price_units']; age=b.timestamp-p.entry_at
        progress=d*(b.close-p.entry)
        c=self.current_context
        if self.strategy=='VWAP_MR':
            swing=s['swing_low'] if d==1 else s['swing_high']
            if d*(b.close-swing)<0:
                self.close_request(now,'VWAP_PREMISE_FAILED')
            elif age>=timedelta(minutes=self.defaults['stagnation_minutes']) and progress<=0:
                self.close_request(now,'VWAP_NO_PROGRESS_30M')
            return
        edge=s['range_high_shifted'] if d==1 else s['range_low_shifted']
        if d*(b.close-edge)<=0:
            self.close_request(now,'FAILED_BREAKOUT')
            return
        if age>=timedelta(minutes=self.defaults['stagnation_minutes']) and progress<D(self.defaults['stagnation_progress_R'])*r:
            self.close_request(now,'MOMENTUM_NO_PROGRESS_30M')
            return
        favorable=b.high if d==1 else b.low
        best=getattr(p,'best_observed_price',p.entry)
        p.best_observed_price=max(best,favorable) if d==1 else min(best,favorable)
        candidate=None; state=None; step=tick(self.symbol,now)
        # Trigger by completed close, not by favorable High before Stop in the
        # same candle. Amendment executes at next strictly eligible future slot.
        if progress>=D(self.defaults['breakeven_trigger_R'])*r:
            candidate=p.entry+d*2*step; state='BE'
        atr=c.get('atr14')
        if progress>=D(self.defaults['trail_trigger_R'])*r and atr is not None:
            trail=p.best_observed_price-d*D(self.defaults['trail_atr'])*atr
            if candidate is None or d*(trail-candidate)>0:
                candidate,state=trail,'TRAIL'
        if candidate is None: return
        candidate=rounded(candidate,step,d==1)
        effective=next_slot(now+timedelta(minutes=self.p['decision_delay_minutes']+self.p['order_delay_minutes']))
        current=self.pending_amendments[-1]['stop'] if self.pending_amendments else p.stop
        if d*(candidate-current)<=0: return
        if d*(candidate-b.close)>=0:
            self.close_request(now,'TRAIL_ALREADY_MARKETABLE')
            return
        amendment={'signal_id':p.row['signal_id'],'decided_at':now,'effective_at':effective,'stop':candidate,'state':state}
        self.pending_amendments.append(amendment)
        self.amendments.append(amendment.copy())
        self.event(now,'STOP_AMEND_ORDER','SUBMITTED',state,p.row['signal_id'],p.remaining,0,p.remaining,price=candidate)


class ArchitectureFeatures(Features):
    def __init__(self,params,indicators,price_only):
        self.indicators=indicators
        self.context={}
        self.prior_close=None
        super().__init__(params,price_only)

    def reset(self):
        super().reset()
        self.indicators.reset()
        self.context={}; self.prior_close=None

    def observe(self,b,asof):
        if asof<available(b,self.p): raise ValueError('Unavailable bar')
        self.prior_close=self.bars[-1].close if self.bars else b.close
        result=super().observe(b,asof)
        # super may reset indicator state when an observed window/gap changes.
        self.context=self.indicators.observe(b)
        return result

    # Called after observe; avoid cached context leaking into a different bar.

