"""Synthetic tests of an explicitly versioned pooled reporting-audit correction."""
from datetime import datetime,timedelta
from decimal import Decimal as D
import unittest
from IntradayLab.tools import audit_return_retest_baseline as original
from IntradayLab.tools.audit_return_retest_baseline_v1_1 import economics, audit


class AuditRevisionTests(unittest.TestCase):
    def fixture(self):
        base=datetime(2023,1,4)
        return [dict(signal_id=str(i),resolved_at=base+timedelta(minutes=order),
            net_R_c1=D(net),net_c1=D(net),gross_R=D(net),cost_R=D(0),cost_c1=D(0),exit_reason='TIME')
            for i,net,order in ((0,'1e28',1),(1,'1',2),(2,'-1e28',0))]

    def test_explicit_chronological_net_sum(self):
        rows=self.fixture();self.assertEqual(original.economics(rows,pooled=True)['Net_R'],D(0))
        self.assertEqual(economics(rows,pooled=True)['Net_R'],D(1))

    def test_gross_cost_keep_reporting_ledger_order(self):
        self.assertEqual(economics(self.fixture(),pooled=True)['Gross_R'],D(0))

    def test_no_tolerance_forged_pf_still_rejected(self):
        with self.assertRaises(AssertionError):original.compare_json({'PF_C1_R':'9'},{'PF_C1_R':D(1)},'FORGED_PF')

    def test_original_auditor_restored_after_call(self):
        before=original.economics
        with self.assertRaises(FileNotFoundError):audit('/definitely_missing_c_audit_report',None)
        self.assertIs(original.economics,before)
