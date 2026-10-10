"""Independent eight-slot R16 oracle, execution comparison and corruption guards."""
from decimal import Decimal as D
import unittest
from IntradayLab.tools.audit_r16_baseline import episodes, replay, check_rows, atr_history, metric


class R16AuditTests(unittest.TestCase):
    def fixture(self):
        from IntradayLab.tests.test_r16_compression_breakout import R16Tests
        f=R16Tests();f.setUp();return f

    def verify(self,rows,f):
        actual_s,actual_t,_=f.run_engine(rows)
        raw={at:(b.open,b.high,b.low,b.close,b.volume) for at,b in rows.items()}
        events=[e for e in episodes(f.symbol,raw) if e['date']==str(f.day)]
        ss,tt=replay(f.symbol,raw,events)
        check_rows(actual_s,ss,('base_reason','compression_start','compression_high','compression_low',
            'ATR_ref','signal_at','stop','status','reason','order_admitted','model_filled'),'SYNTHETIC_SIGNALS')
        check_rows(actual_t,tt,('status','entry_at','entry_price','take','risk','exit_at','exit_reason',
            'net_R_c1','unknown_reason','unknown_detected_at'),'SYNTHETIC_TRADES')

    def test_independent_synthetic_replay(self):
        f=self.fixture();self.verify(f.rows(),f)

    def test_missing_and_invalid_compression_wait_entry_management_and_flat(self):
        for clock in ('10:00','10:20','10:45','10:50','10:55','12:50'):
            for invalid in (False,True):
                with self.subTest(clock=clock,invalid=invalid):
                    f=self.fixture();rows=f.rows()
                    if invalid:
                        rows[f.at(clock)]=f.bar(clock,v='0')
                    else:
                        del rows[f.at(clock)]
                    self.verify(rows,f)

    def test_deadline_and_stop_gap_oracle(self):
        for missing in (False,True):
            f=self.fixture();rows=f.rows('16:00')
            if missing:
                del rows[f.at('17:00')]
            else:
                rows[f.at('17:00')]=f.bar('17:00',o='99',h='99',l='99',c='99')
            self.verify(rows,f)

    def test_busy_multiple_entries_and_invalid_geometry(self):
        f=self.fixture();rows=f.rows()
        rows[f.at('11:30')]=f.breakout('11:30');rows[f.at('12:55')]=f.breakout('12:55')
        self.verify(rows,f)
        rows[f.at('10:50')]=f.bar('10:50',o='99.99',h='100',l='99',c='99.99')
        self.verify(rows,f)

    def test_atr_and_compression_corruption_rejected(self):
        for key in ('ATR_ref','compression_high','compression_low','compression_bars','net_R_c1'):
            with self.assertRaisesRegex(AssertionError,key):
                check_rows([{'signal_id':'a',key:'999'}],[{'signal_id':'a',key:D(1)}],[key],'CORRUPTION')
        with self.assertRaisesRegex(AssertionError,'ROW_SET'):
            check_rows([],[{'signal_id':'missing'}],[],'CORRUPTION')

    def test_unknown_never_used_for_pnl(self):
        self.assertIsNone(metric([dict(status='UNKNOWN',net_R_c1='999')])['Expectancy_R'])

    def test_independent_atr_future_causality(self):
        f=self.fixture();rows=f.rows();raw={at:(b.open,b.high,b.low,b.close,b.volume) for at,b in rows.items()}
        before=atr_history(f.symbol,raw)
        raw[f.at('11:00')]=(D(100),D(200),D(1),D(100),D(10))
        after=atr_history(f.symbol,raw)
        self.assertEqual({k:v for k,v in before.items() if k<f.at('11:00')},
                         {k:v for k,v in after.items() if k<f.at('11:00')})


if __name__=='__main__':
    unittest.main()
