"""Post-fill M15 R15 and pre-entry GO review: synthetic evidence, no orders."""
from __future__ import annotations

import hashlib
import unittest
from dataclasses import replace
from decimal import Decimal
from fractions import Fraction

from IntradayLab.m15_robot.broker_risk_readonly import M15AccountSnapshot
from IntradayLab.m15_robot.cashflow_reconcile_gate import CashflowReconciliation
from IntradayLab.m15_robot.grid_risk import ContractAuthority, size_r15
from IntradayLab.m15_robot.initial_stop_from_fills import M15InitialStopProposal
from IntradayLab.m15_robot.postfill_risk_review import (
    M15PostFillRiskError, review_initial_risk_after_broker_fill,
)
from IntradayLab.m15_robot.trade_draft_contract import M15Draft


class PostFillRiskReviewTests(unittest.TestCase):
    def setUp(self):
        self.contract = ContractAuthority(
            price_step=Decimal("0.001"), tick_value=Decimal("1"),
            trade_lot_size=1, long_initial_margin=Decimal("1000"),
            short_initial_margin=Decimal("1000"),
        )
        self.account = M15AccountSnapshot(
            available_cash=Decimal("20000"), equity=Decimal("100000"),
            unrealized_profit=Decimal("0"),
            broker_equity_minus_unrealized=Decimal("100000"),
            portfolio_type="portfolio_forts",
        )
        self.capital = CashflowReconciliation(
            proposed_realized_equity=Decimal("100000"), transaction_count=1,
            transaction_fingerprint_sha256="a" * 64,
        )
        self.sized = size_r15(
            realized_equity=Decimal("100000"), entry=Decimal("12.500"),
            stop=Decimal("12.250"), contract=self.contract,
            direction="LONG", available_margin_cash=Decimal("20000"),
        )
        self.assertEqual(self.sized.final_quantity, 6)
        self.proposal = self.make_proposal()

    def make_proposal(self, *, n=6, vwap=Fraction(25, 2), stop="12.300",
                      closing_side="SIDE_SELL"):
        d = M15Draft(
            kind="PROTECTIVE_STOP_INSTALL",
            account_fingerprint=hashlib.sha256(b"M15-SYNTH").hexdigest(),
            endpoint="SLTP_ORDER_DRAFT",
            payload={
                "symbol": "CNYRUBF@RTSX",
                "side": closing_side,
                "quantity_sl": {"value": "100"},
                "sl_qty_measure": "SLTP_QTY_MEASURE_PERCENT",
                "sl_price": {"value": str(Decimal(stop))},
            },
        )
        return M15InitialStopProposal(
            draft=d, matched_quantity=n, weighted_entry_exact=vwap,
            stop_price=Decimal(stop), fill_set_sha256="b" * 64,
        )

    def review(self, **kwargs):
        arguments = dict(proposal=self.proposal, initial_order_sizing=self.sized,
                         contract=self.contract, pre_entry_account=self.account,
                         capital=self.capital,
                         pre_entry_committed_nominal_risk=Decimal("0"))
        arguments.update(kwargs)
        return review_initial_risk_after_broker_fill(**arguments)

    def test_long_six_contracts_within_nominal_budget(self):
        r = self.review()
        self.assertEqual(r.actual_initial_loss_rub, Fraction(1200))
        self.assertEqual(r.initial_risk_budget_rub, Fraction(1500))
        self.assertEqual(r.full_margin_requirement_rub, Decimal("6000"))
        self.assertEqual(r.result, "WITHIN_NOMINAL_R15_GO_OFFLINE_ONLY")
        self.assertFalse(r.live_authorized or r.new_entries_authorized
                         or r.order_submission_authorized or r.stop_broker_acknowledged)

    def test_offgrid_exact_vwap_is_not_rounded_before_risk(self):
        p = self.make_proposal(vwap=Fraction(25001, 2000))
        r = self.review(proposal=p)
        self.assertEqual(r.actual_initial_loss_rub, Fraction(1203))
        self.assertEqual(r.exact_vwap, Fraction(25001, 2000))

    def test_far_stop_breaches_r15_without_auto_trade(self):
        p = self.make_proposal(stop="12.100")
        r = self.review(proposal=p)
        self.assertEqual(r.actual_initial_loss_rub, Fraction(2400))
        self.assertEqual(r.result, "POSTFILL_RISK_OR_MARGIN_OVERRUN_REQUIRES_BROKER_REVIEW")
        self.assertFalse(r.new_entries_authorized or r.order_submission_authorized)

    def test_pre_committed_n4_cap_reduces_capacity(self):
        r = self.review(pre_entry_committed_nominal_risk=Decimal("5750"))
        self.assertEqual(r.initial_risk_budget_rub, Fraction(250))
        self.assertEqual(r.result, "POSTFILL_RISK_OR_MARGIN_OVERRUN_REQUIRES_BROKER_REVIEW")

    def test_margin_shortfall_flagged_not_silently_resized(self):
        limited = replace(self.account, available_cash=Decimal("1000"))
        r = self.review(pre_entry_account=limited)
        self.assertEqual(r.result, "POSTFILL_RISK_OR_MARGIN_OVERRUN_REQUIRES_BROKER_REVIEW")
        self.assertEqual(r.matched_broker_quantity, 6)

    def test_short_side_exact_vwap_offgrid(self):
        p = self.make_proposal(closing_side="SIDE_BUY",
                               vwap=Fraction(25001, 2000), stop="12.701")
        r = self.review(proposal=p)
        self.assertEqual(r.actual_initial_loss_rub, Fraction(1203))
        self.assertEqual(r.result, "WITHIN_NOMINAL_R15_GO_OFFLINE_ONLY")

    def test_wrong_side_stop_refused(self):
        p = self.make_proposal(stop="12.700")
        with self.assertRaisesRegex(M15PostFillRiskError, "STOP_WRONG_SIDE"):
            self.review(proposal=p)

    def test_stop_off_grid_refused(self):
        p = self.make_proposal(stop="12.3005")
        with self.assertRaisesRegex(M15PostFillRiskError, "STOP_OFF_TICK"):
            self.review(proposal=p)

    def test_unconfirmed_proposal_is_not_a_broker_stop(self):
        r = self.review()
        self.assertFalse(r.stop_broker_acknowledged)
        self.assertFalse(r.commission_verified)
        self.assertEqual(r.margin_source, "PRE_ENTRY_READONLY_M15_SNAPSHOT")

    def test_synthetic_live_escalation_denied(self):
        p = replace(self.proposal, live_authorized=True)
        with self.assertRaisesRegex(M15PostFillRiskError, "OFFLINE_ONLY"):
            self.review(proposal=p)

    def test_actual_staged_submission_flag_denied(self):
        p = replace(self.proposal,
                    draft=replace(self.proposal.draft, submitted=True))
        with self.assertRaisesRegex(M15PostFillRiskError, "OFFLINE_ONLY"):
            self.review(proposal=p)

    def test_runtime_capital_authority_escalation_denied(self):
        p = replace(self.capital, runtime_r15_authorized=True)
        with self.assertRaisesRegex(M15PostFillRiskError, "OFFLINE_ONLY"):
            self.review(capital=p)

    def test_distinct_account_equity_mismatch_denied(self):
        p = replace(self.account, broker_equity_minus_unrealized=Decimal("99999"))
        with self.assertRaisesRegex(M15PostFillRiskError, "PRE_ENTRY_CAPITAL_UNPROVEN"):
            self.review(pre_entry_account=p)

    def test_broker_fill_quantity_exceeding_planned_refused(self):
        p = self.make_proposal(n=7)
        with self.assertRaisesRegex(M15PostFillRiskError, "ORDER_QUANTITY_UNPROVEN"):
            self.review(proposal=p)

    def test_fractional_lot_fill_flagged(self):
        contract = replace(self.contract, trade_lot_size=4)
        r = self.review(contract=contract)
        self.assertEqual(r.result, "POSTFILL_RISK_OR_MARGIN_OVERRUN_REQUIRES_BROKER_REVIEW")

    def test_invalid_pre_committed_initial_risk_denied(self):
        with self.assertRaisesRegex(M15PostFillRiskError, "PRE_ENTRY_CAPITAL_UNPROVEN"):
            self.review(pre_entry_committed_nominal_risk=Decimal("-1"))

    def test_no_real_broker_or_order_transport(self):
        r = self.review()
        for name in ("place_order", "submit", "cancel", "connect"):
            self.assertFalse(hasattr(r, name))
        self.assertFalse(r.live_authorized)
        self.assertEqual(self.proposal.draft.endpoint, "SLTP_ORDER_DRAFT")


if __name__ == "__main__":
    unittest.main()
