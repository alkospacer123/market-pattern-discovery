"""C audit revision 1.1: canonical pooled closure-sum order, no trading changes.

The pre-P&L auditor 1.0 is retained verbatim. Its per-instrument/path/coverage
checks pass, but it sums pooled R in instrument ledger order. The frozen
common closed_metrics sums those closure fields in (resolved_at, signal_id)
order; Decimal precision makes a last-place discrepancy. This revision uses
that explicit chronological order for closed metrics, retaining original
ledger order for Gross_R/Cost_R (the frozen C reporting contract). It removes
no comparisons and applies no tolerance, rounding or favorable adjustment.
Only the independent auditor is imported; no production trading module.
"""
from decimal import Decimal as D
from unittest.mock import patch
from IntradayLab.tools import audit_return_retest_baseline as original

VERSION='C_V1_AUDIT_1.1'
FROZEN_ECONOMICS=original.economics


def economics(trades,pooled=False):
    ordered=sorted(trades,key=lambda t:(t['resolved_at'],t['signal_id']))
    result=FROZEN_ECONOMICS(ordered,pooled=pooled)
    # Production research diagnostics sum these additional fields in ledger order.
    result['Gross_R']=sum((t['gross_R'] for t in trades),D(0))
    result['Cost_R']=sum((t['cost_R'] for t in trades),D(0))
    return result


def audit(output,data_root,cfg=None,raw=None):
    with patch.object(original,'economics',economics):
        result=original.audit(output,data_root,cfg,raw)
    result.update(auditor_version=VERSION,
        reporting_defect='Auditor 1.0 pooled closure-sum order differed at Decimal last place; all frozen trade/config/result bytes retained',
        original_auditor_preserved=True,exact_comparisons_retained=True,
        trading_logic_changed=False)
    return result
