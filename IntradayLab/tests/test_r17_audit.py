"""Independent R17 oracle and corruption guards on synthetic inputs."""
from decimal import Decimal as D
import unittest
from IntradayLab.tools.audit_r17_baseline import episodes, replay, check_rows, atr_history, metric, distribution, assessment


class R17AuditTests(unittest.TestCase):
    def fixture(self):
        from IntradayLab.tests.test_r17_breakout_retest import R17Tests
        f=R17Tests();f.setUp();return f

    def verify(self,rows,f):
        actual_s,actual_t,_=f.run_engine(rows)
        raw={at:(b.open,b.high,b.low,b.close,b.volume) for at,b in rows.items()}
        events=[e for e in episodes('USDRUBF',raw) if e['date']==str(f.day)]
        ss,tt=replay('USDRUBF',raw,events)
        check_rows(actual_s,ss,('base_reason','breakout_atr14','signal_at','stop','status','reason','order_admitted','model_filled'),'SYNTHETIC_SIGNALS')
        check_rows(actual_t,tt,('status','entry_at','entry_price','take','risk','exit_at','exit_reason','net_R_c1','unknown_reason','unknown_detected_at'),'SYNTHETIC_TRADES')
        return ss,tt

    def test_independent_synthetic_replay(self):
        f=self.fixture();self.verify(f.rows(),f)

    def test_independent_missing_retest(self):
        f=self.fixture();rows=f.rows();del rows[f.at('10:20')]
        self.verify(rows,f)

    def test_independent_missing_waiting_and_execution(self):
        for clock in ('10:25','10:30','11:00','12:30'):
            with self.subTest(clock=clock):
                f=self.fixture();rows=f.rows();del rows[f.at(clock)]
                self.verify(rows,f)

    def test_independent_invalid_geometry(self):
        f=self.fixture();rows=f.rows()
        rows[f.at('10:30')]=f.bar('10:30',o='100.49',h='100.6',l='100.4',c='100.5')
        self.verify(rows,f)

    def test_corrupted_atr_rejected(self):
        with self.assertRaisesRegex(AssertionError,'breakout_atr14'):
            check_rows([{'signal_id':'a','breakout_atr14':'2'}],[{'signal_id':'a','breakout_atr14':D('1')}],['breakout_atr14'],'CORRUPTION')

    def test_corrupted_retest_and_missing_trade_rejected(self):
        with self.assertRaisesRegex(AssertionError,'retest_start'):
            check_rows([{'signal_id':'a','retest_start':'10:15'}],[{'signal_id':'a','retest_start':'10:20'}],['retest_start'],'CORRUPTION')
        with self.assertRaisesRegex(AssertionError,'ROW_SET'):
            check_rows([],[{'signal_id':'a'}],[],'CORRUPTION')

    def test_independent_atr_future_causality(self):
        f=self.fixture();bars=f.rows();raw={at:(b.open,b.high,b.low,b.close,b.volume) for at,b in bars.items()}
        before=atr_history('USDRUBF',raw)
        raw[f.at('11:00')]=(D(100),D(200),D(1),D(100),D(10))
        after=atr_history('USDRUBF',raw)
        self.assertEqual({k:v for k,v in before.items() if k<f.at('11:00')},{k:v for k,v in after.items() if k<f.at('11:00')})

    def test_unknown_cannot_inflate_independent_metrics(self):
        m=metric([dict(status='UNKNOWN',net_R_c1='999')])
        self.assertEqual(m['closed'],0);self.assertIsNone(m['Expectancy_R'])
        self.assertEqual(distribution([dict(status='UNKNOWN',net_R_c1='999')])['unique_trade_days'],0)


if __name__=='__main__':
    unittest.main()
