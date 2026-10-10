"""Adversarial v2 checks; synthetic prices, independent gates and outcomes."""
import copy
from datetime import datetime, timedelta
from decimal import Decimal as D
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import audit_orb_false_break_fade as old_oracle
import audit_orb_false_break_fade_v2 as independent
import orb_false_break_fade_replay as engine
import run_orb_false_break_fade_daywise as daily
import run_orb_false_break_fade_v2 as production
from test_orb_false_break_fade_daywise import two_day_fixture, row

FIVE = timedelta(minutes=5)


class V2IndependentAudit(unittest.TestCase):
    def test_atr_manual_tr_adjacent_gap_invalid_and_future(self):
        t = datetime(2023, 1, 3, 9)
        bars = {t+i*FIVE: row() for i in range(14)}
        self.assertEqual(independent.atr_observations(bars)[t+13*FIVE], D(2))
        # Missing 10:10: prior close 100 must not create a TR of 100.
        u = t+15*FIVE
        bars[u] = row('200', '201', '199', '200')
        self.assertEqual(production.causal_atr14(bars)[u], D(2))
        # Adjacent bar sees the real preceding close: TR=101.
        bars[u+FIVE] = row()
        self.assertEqual(independent.atr_observations(bars)[u+FIVE], D(127)/14)
        self.assertEqual(production.causal_atr14(bars), independent.atr_observations(bars))
        bars[u+2*FIVE] = (*row()[:4], D(0))
        bars[u+3*FIVE] = row('200', '201', '199', '200')
        self.assertEqual(production.causal_atr14(bars), independent.atr_observations(bars))
        prefix = dict(production.causal_atr14(bars))
        bars[u+4*FIVE] = row('900', '1000', '800', '900')
        for at, value in prefix.items():
            self.assertEqual(production.causal_atr14(bars)[at], value)

    def test_m15_veto_strict_bounds_and_neutral(self):
        t = datetime(2023, 1, 3, 10, 15)
        bars = {t+i*FIVE: row() for i in range(3)}
        base = dict(base_reason='SIGNAL', sweep_start=t, signal_at=t+3*FIVE,
                    sweep_size=D('.01'), or_high=D(101), or_low=D(99),
                    m15_start=t, m15_open=D(100), m15_high=D(101), m15_low=D(99))
        for side, close, veto in [(-1,'101',False),(-1,'101.01',True),
                                  (1,'99',False),(1,'98.99',True)]:
            high=max(D(101),D(close));low=min(D(99),D(close))
            bars[t+2*FIVE]=row('100',str(high),str(low),close)
            e=dict(base, direction=side,m15_close=D(close),m15_high=high,m15_low=low)
            got=independent.expected_gates(bars,[e],'USDRUBF',{'atr':False,'mtf':True})[0]
            self.assertEqual(got['v2_m15_breakout_accepted_veto'],veto)
        e=dict(base,direction=-1,m15_close=None)
        got=independent.expected_gates(bars,[e],'USDRUBF',{'atr':False,'mtf':True})[0]
        self.assertEqual(got['base_reason'],'SIGNAL')
        self.assertEqual(got['v2_filter_reason'],'M15_NO_CONTEXT_NEUTRAL_ALLOWED')

    def test_missing_partial_parent_and_session_never_reuse_context(self):
        t=datetime(2023,1,3,13,45)
        bars={t+i*FIVE:row() for i in range(3)}
        self.assertEqual(production.independent_m15_close(bars,{'signal_at':t+3*FIVE}),D(100))
        self.assertIsNone(production.independent_m15_close(bars,{'signal_at':t+4*FIVE}))
        self.assertIsNone(production.independent_m15_close(bars,{'signal_at':datetime(2023,1,3,14,10)}))
        del bars[t+FIVE]
        self.assertIsNone(production.independent_m15_close(bars,{'signal_at':t+3*FIVE}))

    def test_daily_unknown_inside_day_and_missing_whole_day(self):
        bars=two_day_fixture()
        # Opposite side signal after the exposed gap is still blocked today.
        bars[datetime(2023,1,3,11)]=row('99.05','99.1','98.95','99.05')
        events,_,_=engine.base_signals('USDRUBF',bars)
        ss,tt,dd,_=daily.evaluate_symbol('USDRUBF',bars,events,'A_BASE',{'atr':False,'mtf':False})
        self.assertTrue(any(s['date']=='2023-01-03' and s['reason']=='UNKNOWN_POSITION_BLOCK' for s in ss))
        self.assertEqual(tt[0]['status'],'UNKNOWN')
        self.assertTrue(all(d['initial_flat_assumed'] and not d['initial_flat_proven'] for d in dd))
        del_rows={t:b for t,b in bars.items() if t.date().isoformat()!='2023-01-04'}
        # Keep Jan 5, so the physically missing Jan 4 is within research span.
        del_rows.update({t+timedelta(days=1):b for t,b in bars.items() if t.date().isoformat()=='2023-01-04'})
        ee,_,_=engine.base_signals('USDRUBF',del_rows)
        s,tr,d,_=daily.evaluate_symbol('USDRUBF',del_rows,ee,'A_BASE',{'atr':False,'mtf':False})
        self.assertTrue(any(x['date']=='2023-01-04' and x['reason']=='NO_OR' for x in s))
        self.assertFalse(next(x for x in d if x['date']=='2023-01-04')['source_observed'])
        self.assertFalse(any(x['signal_at'].date().isoformat()=='2023-01-04' for x in tr))

    def test_audit_detects_forged_gate_and_uses_other_trade_engine(self):
        bars=two_day_fixture();ev=old_oracle.oracle_signals('USDRUBF',bars)
        enriched=production.derive_filters(ev,bars,'USDRUBF')
        spec={'atr':False,'mtf':False}
        enriched=production.select_architecture(enriched,spec)
        ss,tt,dd,_=daily.evaluate_symbol('USDRUBF',bars,enriched,'A_BASE',spec)
        oldss,oldtt,_,_=daily.evaluate_symbol('USDRUBF',bars,ev,'A_BASE',spec)
        conf={'instruments':['USDRUBF'],'architectures':{'A_BASE':spec}}
        self.assertEqual(independent.run(conf,{'USDRUBF':bars},ss,tt,dd,oldss,oldtt)['status'],'PASS')
        forged=copy.deepcopy(ss)
        next(x for x in forged if x.get('v2_atr_ready'))['v2_atr14']+=D(1)
        self.assertEqual(independent.run(conf,{'USDRUBF':bars},forged,tt,dd,oldss,oldtt)['status'],'FAIL')


if __name__=='__main__':
    unittest.main()
