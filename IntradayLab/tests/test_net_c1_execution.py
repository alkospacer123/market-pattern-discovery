"""Universal opt-in Open constraints and net/net target, no market-data reads."""
from decimal import Decimal as D
import unittest
from IntradayLab.core.execution import entry_admission, entry_geometry


class NetC1ExecutionTests(unittest.TestCase):
    def test_old_default_geometry_stays_gross(self):
        self.assertEqual(entry_geometry(D(100),1,D('99.96'),D('.01'),D(3)),(D('.04'),D('100.12')))

    def test_full_net_three_R_is_eight_ticks_above_three_risk(self):
        for direction,stop,take in ((1,'99.96','100.20'),(-1,'100.04','99.80')):
            risk,price=entry_geometry(D(100),direction,D(stop),D('.01'),D(3),target_mode='FULL_NET_C1_R')
            self.assertEqual(price,D(take));self.assertEqual(risk,D('.04'))
            distance=direction*(price-D(100))
            self.assertEqual((distance-D('.02'))/(risk+D('.02')),D(3))
            self.assertNotEqual((3*risk+D('.02')-D('.02'))/(risk+D('.02')),D(3))

    def test_target_outward_rounding_both_directions(self):
        for side,stop,expected in ((1,'99.97','100.10'),(-1,'100.03','99.90')):
            risk,take=entry_geometry(D(100),side,D(stop),D('.01'),D('1.5'),target_mode='FULL_NET_C1_R')
            self.assertEqual(take,D(expected))
            self.assertGreaterEqual((side*(take-D(100))-D('.02'))/(risk+D('.02')),D('1.5'))

    def test_reclaim_and_risk_boundary(self):
        c={'directional_reference':'100','minimum_reference_ticks':1,'minimum_risk_ticks':4}
        self.assertEqual(entry_admission(D(100),1,D('99.97'),D('.01'),c),'OPEN_REFERENCE_LIMIT')
        self.assertIsNone(entry_admission(D('100.01'),1,D('99.97'),D('.01'),c))
        self.assertEqual(entry_admission(D('100.01'),1,D('99.98'),D('.01'),c),'RISK_BELOW_MINIMUM_TICKS')
        self.assertEqual(entry_admission(D('100.01'),1,D('100.01'),D('.01'),c),'INVALID_RISK')
        self.assertIsNone(entry_admission(D('99.99'),-1,D('100.03'),D('.01'),c))

    def test_cny_small_tick_and_cost_scale(self):
        risk,take=entry_geometry(D(10),1,D('9.996'),D('.001'),D(3),target_mode='FULL_NET_C1_R')
        self.assertEqual(take,D('10.020'))
        self.assertEqual((take-D(10)-D('.002'))/(risk+D('.002')),D(3))

    def test_unapproved_mode_and_invalid_geometry(self):
        with self.assertRaisesRegex(ValueError,'TARGET_MODE'):
            entry_geometry(D(100),1,D(99),D('.01'),D(3),target_mode='MAGIC')
        self.assertIsNone(entry_geometry(D(100),1,D(101),D('.01'),D(3),target_mode='FULL_NET_C1_R'))


if __name__=='__main__':
    unittest.main()
