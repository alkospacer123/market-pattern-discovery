"""Causal fixtures, raw-data guard and LONG/SHORT protective semantics."""
from datetime import datetime, timedelta, timezone
import tempfile
from pathlib import Path
import unittest
import independent as I

def at(text):return datetime.fromisoformat(text).replace(tzinfo=I.TZ)

def fixture(times,signals,side=1):
    bars=[]
    for time,signal in zip(times,signals):
        t=at(time);h={'at':t,'adx':25.,'slope':float(side),'ratio':1.2,'ema':100.,'c':100.}
        bars.append({'at':t,'o':100.,'h':101.,'l':99.,'c':100.,'v':1.,'atr':1.,'previous_atr':1.,
            'upper':99.,'lower':101.,'signal':signal,'h1':h,'previous_h1':h|{'at':t-timedelta(hours=1)}})
    return bars

class Gates(unittest.TestCase):
    def test_t1_inclusive_exclusive_boundaries(self):
        for hour,ok in [('09:45',False),('10:00',True),('10:15',True),('17:45',True),('18:00',False),('18:15',False),('00:00',False)]:
            self.assertEqual(I.entry_gate(at('2024-04-01 '+hour),None,'T1')[0],ok)
    def test_t1_UTC_equivalent(self):
        for time in ('2024-04-01 10:00','2024-04-01 18:00'):
            t=at(time);self.assertEqual(I.entry_gate(t,None,'T1'),I.entry_gate(t.astimezone(timezone.utc),None,'T1'))
    def test_t2_absent_predecessor(self):
        self.assertEqual(I.entry_gate(at('2024-04-01 10:00'),None,'T2'),(False,'NO_PREVIOUS_OBSERVED_CLOSE'))
    def test_t2_strict_15_and_first_only(self):
        t=at('2024-04-01 10:00')
        self.assertTrue(I.entry_gate(t+I.STEP,t,'T2')[0])
        self.assertFalse(I.entry_gate(t+2*I.STEP,t,'T2')[0])
        self.assertTrue(I.entry_gate(t+3*I.STEP,t+2*I.STEP,'T2')[0])
    def test_t2_previous_actual_bar_without_signal(self):
        f=fixture(['2024-04-01 10:00','2024-04-01 10:15'],[0,1])
        self.assertTrue(I.simulate(f,'USDRUBF','BASELINE','T2')[3][0]['entry_accepted'])
    def test_t2_continuous_midnight(self):
        self.assertTrue(I.entry_gate(at('2024-04-02 00:00'),at('2024-04-01 23:45'),'T2')[0])
    def test_t2_weekend_and_year_gap(self):
        for previous,now in [('2024-04-05 23:45','2024-04-08 09:15'),('2023-12-29 23:45','2024-01-03 09:15')]:
            self.assertFalse(I.entry_gate(at(now),at(previous),'T2')[0])
    def test_timezone_and_order_required(self):
        with self.assertRaises(AssertionError):I.entry_gate(datetime(2024,1,1),None,'T1')
        with self.assertRaises(AssertionError):I.entry_gate(at('2024-01-01'),at('2024-01-02'),'T2')

class Execution(unittest.TestCase):
    def test_stop_first_both_sides(self):
        for side in (1,-1):
            f=fixture(['2024-04-01 10:00','2024-04-01 10:15'],[side,0],side);f[1].update(h=110.,l=90.)
            t,o,d,*_=I.simulate(f,'USDRUBF','BASELINE','CONTROL')
            self.assertEqual(t[0]['gross_R'],-1.);self.assertEqual(t[0]['MFE_R'],0.);self.assertEqual(t[0]['trailing_updates'],0)
    def test_adverse_open_gap_both_sides(self):
        for side,opening in ((1,90.),(-1,110.)):
            f=fixture(['2024-04-01 10:00','2024-04-02 10:00'],[side,0],side)
            f[1].update(o=opening,h=max(101.,opening),l=min(99.,opening))
            t=I.simulate(f,'USDRUBF','BASELINE','CONTROL')[0][0]
            self.assertEqual(t['exit_price'],opening);self.assertEqual(t['gross_R'],-5.);self.assertTrue(t['exit_at_open'])
    def test_next_observed_bar_trail_both_sides(self):
        for side in (1,-1):
            f=fixture(['2024-04-01 10:00','2024-04-01 10:15','2024-04-02 10:00'],[side,0,0],side)
            if side==1:f[1].update(h=110.);f[2].update(o=108.,h=109.,l=106.)
            else:f[1].update(l=90.);f[2].update(o=92.,h=94.,l=91.)
            t,o,d,*_=I.simulate(f,'USDRUBF','BASELINE','CONTROL')
            self.assertFalse(d[0]['stop_hit']);self.assertEqual(d[0]['active_stop'],100-side*2)
            self.assertEqual(d[0]['active_stop_next_bar'],100+side*7);self.assertEqual(t[0]['exit_price'],100+side*7)
    def test_same_close_reentry_allowed(self):
        f=fixture(['2024-04-01 10:00','2024-04-01 10:15'],[1,1]);f[1]['l']=97.
        for rule in ('CONTROL','T1'):
            t,o,d,e,*_=I.simulate(f,'USDRUBF','BASELINE',rule)
            self.assertEqual(len(t),1);self.assertIsNotNone(o);self.assertTrue(e[-1]['entry_accepted']);self.assertEqual(e[-1]['same_close_exit_trade_id'],t[0]['trade_id'])
    def test_same_close_reentry_forbidden(self):
        f=fixture(['2024-04-01 17:45','2024-04-01 18:00'],[1,1]);f[1]['l']=97.
        t,o,d,e,*_=I.simulate(f,'USDRUBF','BASELINE','T1')
        self.assertEqual(len(t),1);self.assertIsNone(o);self.assertFalse(e[-1]['entry_accepted'])
    def test_position_held_outside_entry_hours(self):
        f=fixture(['2024-04-01 10:00','2024-04-01 18:00','2024-04-02 09:15'],[1,1,1])
        a=I.simulate(f,'USDRUBF','BASELINE','T1');b=I.simulate(f,'USDRUBF','BASELINE','CONTROL')
        self.assertEqual(a[1]['active_stop'],b[1]['active_stop']);self.assertEqual(len(a[2]),2)
        self.assertTrue(a[3][-1]['position_occupied']);self.assertFalse(a[3][-1]['rule_pass'])
    def test_occupancy_replay_changes_next_signal(self):
        f=fixture(['2024-04-01 09:45','2024-04-01 10:00'],[1,1])
        a=I.simulate(f,'USDRUBF','BASELINE','T1');b=I.simulate(f,'USDRUBF','BASELINE','CONTROL')
        self.assertTrue(a[3][-1]['entry_accepted']);self.assertFalse(b[3][-1]['entry_accepted'])
    def test_year_boundary_terminal_open_not_liquidated(self):
        f=fixture(['2023-12-29 10:00','2024-01-03 10:00'],[1,0])
        t,o,d,e,g,s=I.simulate(f,'USDRUBF','BASELINE','T1')
        self.assertEqual(len(t),0);self.assertIsNotNone(o);self.assertEqual([r['year'] for r in s],[2023,2024])
    def test_future_bar_rejected(self):
        f=fixture(['2025-01-01 10:00'],[1])
        with self.assertRaises(AssertionError):I.simulate(f,'USDRUBF','BASELINE','CONTROL')
    def test_replay_prefix_invariant(self):
        f=fixture(['2024-04-01 09:45','2024-04-01 10:00','2024-04-01 10:15','2024-04-02 10:00'],[1,1,1,0])
        for rule in ('CONTROL','T1','T2'):
            full=I.simulate(f,'USDRUBF','BASELINE',rule);prefix=I.simulate(f[:3],'USDRUBF','BASELINE',rule)
            self.assertEqual(full[2][:len(prefix[2])],prefix[2]);self.assertEqual(full[3][:len(prefix[3])],prefix[3])

class Features(unittest.TestCase):
    def raw(self,n=600):
        begin=at('2024-01-03 10:00')
        return [{'at':begin+i*I.STEP,'o':100.+i*.01,'h':101.+i*.01,'l':99.+i*.01,'c':100.1+i*.01,'v':1.} for i in range(n)]
    def test_H1_available_only_fourth_completed_bar(self):
        f=I.build_features(self.raw(5))
        self.assertIsNone(f[2]['h1']);self.assertEqual(f[3]['h1']['at'],f[3]['at']);self.assertEqual(f[4]['h1']['at'],f[3]['at'])
    def test_H1_gap_block_skipped(self):
        raw=self.raw(8)
        for r in raw[2:]:r['at']+=I.STEP
        f=I.build_features(raw);self.assertIsNone(f[3]['h1']);self.assertEqual(f[7]['h1']['at'],f[7]['at'])
    def test_H1_daily_ordinal_reset(self):
        raw=self.raw(6)
        for i,r in enumerate(raw):r['at']=at('2024-01-03 23:15')+i*I.STEP
        f=I.build_features(raw);self.assertTrue(all(r['h1'] is None for r in f))
    def test_Donchian_excludes_current_extreme(self):
        raw=self.raw(22);raw[20]['h']=10000.
        f=I.build_features(raw)
        self.assertEqual(f[20]['upper'],max(r['h'] for r in raw[:20]));self.assertEqual(f[21]['upper'],10000.)
    def test_indicator_prefix_no_lookahead(self):
        raw=self.raw();a=I.build_features(raw);b=I.build_features(raw[:477])
        # NaNs compare via canonical serialization instead of NaN == NaN.
        self.assertEqual(I.plain(a[:477]),I.plain(b))
        self.assertTrue(all(r['h1'] is None or r['h1']['at']<=r['at'] for r in a))
    def test_timestamp_first_future_poison_unread(self):
        work=I.HERE/'work';work.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=work) as tmp:
            p=Path(tmp)/'poison.csv'
            p.write_text('Ticker;Datetime;Open;High;Low;Close;Volume\nX;2024-12-30 10:00:00;1;2;0;1;1\nX;2025-01-01 10:00:00;FORBIDDEN;OHLC;POISON\n')
            self.assertEqual(len(I.parse_prefix(p)[0]),1)
    def test_closed_R_metrics_calendar_and_top(self):
        t=[{'exit_time':at('2024-01-02')+i*I.STEP,'instrument':'X','trade_id':str(i),'gross_R':x} for i,x in enumerate([2.,-1.,-1.,3.])]
        m=I.metrics(t,I.CALENDAR)
        self.assertEqual(m['gross_PF'],2.5);self.assertEqual(m['gross_R'],3.);self.assertEqual(m['max_drawdown_closed_R'],2.)
        self.assertEqual(m['max_consecutive_losses'],2);self.assertEqual(m['calendar_months'],24);self.assertEqual(m['positive_months'],1)

if __name__=='__main__':unittest.main(verbosity=2)
