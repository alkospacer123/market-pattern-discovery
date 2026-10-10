"""Independent raw slices/Open/path oracle and ledger corruption guards."""
from decimal import Decimal as D
import unittest
from IntradayLab.tools.audit_level_rejection_baseline import episodes,replay,check_rows,metric


class LevelRejectionAuditTests(unittest.TestCase):
    def fixture(self):
        from IntradayLab.tests.test_level_rejection import LevelRejectionTests
        f=LevelRejectionTests();f.setUp();return f

    def verify(self,rows,f):
        actual_s,actual_t,_=f.run_engine(rows)
        raw={at:(b.open,b.high,b.low,b.close,b.volume) for at,b in rows.items()}
        events=[e for e in episodes(f.symbol,raw) if e['date']==str(f.day)]
        ss,tt=replay(f.symbol,raw,events)
        check_rows(actual_s,ss,('base_reason','range_start','range_high','range_low','raw_rejection',
            'confirmed_signal','previous_confirmed_start','signal_at','stop','status','reason',
            'pending_created','open_admission_passed','order_admitted','model_filled'),'SYNTHETIC_SIGNALS')
        check_rows(actual_t,tt,('status','entry_at','entry_price','take','risk','exit_at','exit_reason',
            'net_R_c1','unknown_reason','unknown_detected_at','d_full','d_legacy',
            'planned_net_to_net_R','realized_net_to_net_R'),'SYNTHETIC_TRADES')

    def test_synthetic_full_replay_long_and_short(self):
        for side in (1,-1):
            f=self.fixture();self.verify(f.rows(side=side),f)

    def test_missing_invalid_six_wait_entry_exposed_and_flat(self):
        for clock in ('10:00','10:20','10:35','10:40','10:45','12:40'):
            for invalid in (False,True):
                with self.subTest(clock=clock,invalid=invalid):
                    f=self.fixture();rows=f.rows()
                    if invalid:
                        rows[f.at(clock)]=f.bar(clock,v='0')
                    else:
                        del rows[f.at(clock)]
                    self.verify(rows,f)

    def test_Open_reclaim_risk_dedup_busy(self):
        for price in ('100','100.01','100.50'):
            f=self.fixture();rows=f.rows();rows[f.at('10:40')]=f.bar('10:40',o=price,c=price)
            rows[f.at('10:45')]=f.rejection('10:45',l='99.97',c='100')
            rows[f.at('11:10')]=f.rejection('11:10')
            self.verify(rows,f)

    def test_full_net_Take_and_Stop_first_gap(self):
        for bar in ({'h':'103'},{'h':'103','l':'99'},{'o':'99','h':'99','l':'99','c':'99'}):
            f=self.fixture();rows=f.rows();rows[f.at('10:45')]=f.bar('10:45',**bar)
            self.verify(rows,f)

    def test_reserve_deadline_and_unknown_Open(self):
        for clock in ('13:15','13:20','16:15','16:20'):
            f=self.fixture();rows=f.rows(clock)
            self.verify(rows,f)
        f=self.fixture();rows=f.rows('16:15');del rows[f.at('17:00')];self.verify(rows,f)

    def test_replay_levels_dedup_and_full_net_target_corruption(self):
        for key in ('range_high','range_low','range_bars','previous_confirmed_start','d_full',
                    'planned_net_to_net_R','net_R_c1'):
            with self.assertRaisesRegex(AssertionError,key):
                check_rows([{'signal_id':'a',key:'999'}],[{'signal_id':'a',key:D(1)}],[key],'CORRUPTION')
        with self.assertRaisesRegex(AssertionError,'ROW_SET'):
            check_rows([],[{'signal_id':'missing'}],[],'CORRUPTION')

    def test_future_changes_leave_prior_independent_decisions(self):
        f=self.fixture();rows=f.rows();raw={at:(b.open,b.high,b.low,b.close,b.volume) for at,b in rows.items()}
        before=replay(f.symbol,raw,[e for e in episodes(f.symbol,raw) if e['date']==str(f.day)])[0]
        raw[f.at('11:00')]=(D(100),D(200),D(1),D(100),D(10))
        after=replay(f.symbol,raw,[e for e in episodes(f.symbol,raw) if e['date']==str(f.day)])[0]
        self.assertEqual([s for s in before if s['recorded_at']<f.at('11:00')],
                         [s for s in after if s['recorded_at']<f.at('11:00')])

    def test_unknown_cannot_inflate_PnL(self):
        m=metric([dict(status='UNKNOWN',net_R_c1='999')])
        self.assertEqual(m['closed'],0);self.assertIsNone(m['Expectancy_R'])


if __name__=='__main__':
    unittest.main()
