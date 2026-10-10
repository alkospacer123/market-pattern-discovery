"""The independent auditor must detect drift and ledger corruption."""
from decimal import Decimal as D
import unittest
from IntradayLab.tools.audit_canonical_baseline import check_rows, metric, assert_value


class AuditTests(unittest.TestCase):
    def test_wrong_trade_price_rejected(self):
        with self.assertRaisesRegex(AssertionError,'exit_price'):
            check_rows([{'signal_id':'x','exit_price':'100'}],
                       [{'signal_id':'x','exit_price':D('101')}],['exit_price'],'LEDGER')
    def test_missing_trade_rejected(self):
        with self.assertRaisesRegex(AssertionError,'ROW_SET'):
            check_rows([], [{'signal_id':'x'}], [], 'LEDGER')
    def test_independent_r_and_price_pf_and_initial_zero_dd(self):
        rows=[dict(signal_id=str(i),status='CLOSED',resolved_at=str(i),net_R_c1=r,
                   net_c1=p,cost_c1='.02') for i,(r,p) in enumerate([('-2','-.1'),('1','.2'),('-.5','-.1')])]
        actual=metric(rows)
        self.assertEqual(actual['PF_C1_price'],D(1))
        self.assertEqual(actual['PF_C1_R'],D('.4'))
        self.assertEqual(actual['Max_DD_R'],D(2))
        self.assertEqual(actual['Net_R'],D('-1.5'))
        with self.assertRaises(AssertionError):
            assert_value('0',actual['Net_R'],'CORRUPTED_METRIC')
    def test_unknown_not_given_pnl(self):
        actual=metric([dict(status='UNKNOWN',signal_id='x',net_R_c1='100')])
        self.assertEqual(actual['closed'],0)
        self.assertIsNone(actual['Expectancy_R'])


if __name__=='__main__':
    unittest.main()
