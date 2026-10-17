"""Synthetic-only proof of M15 bounded AccountTrade read-side validation."""
import unittest
from decimal import Decimal

from IntradayLab.m15_robot.broker_fill_readonly import (
    ExpectedEntry, M15FillEvidenceError, analyze_account_trades,
)

BEGIN = "2026-10-16T07:00:00Z"
END = "2026-10-16T08:00:00Z"


def target(**changes):
    values = dict(account_id="m15-separate-account", order_id="broker-order-1",
                  symbol="CNYRUBF@RTSX", side="SIDE_BUY", quantity=3,
                  price_step=Decimal("0.001"))
    values.update(changes)
    return ExpectedEntry(**values)


def trade(trade_id="fill-1", **changes):
    row = dict(trade_id=trade_id, account_id="m15-separate-account",
               order_id="broker-order-1", symbol="CNYRUBF@RTSX",
               side="SIDE_BUY", currency="XXX", timestamp="2026-10-16T07:01:00.000000123Z",
               price={"value": "12.533"}, size={"value": "1"})
    row.update(changes)
    return row


def check(rows, **kwargs):
    return analyze_account_trades({"trades": rows}, target(), start=BEGIN, end=END,
                                  limit=1000, **kwargs)


class M15TradeEvidence(unittest.TestCase):
    def test_empty_history_is_not_fill_proof(self):
        r = check([])
        self.assertFalse(r["verified_fill"])
        self.assertEqual(r["quantity_status"], "NO_MATCH")
        self.assertEqual(r["commission_authority"], "NOT_VERIFIED")
        self.assertFalse(r["sqlite_reconciled"])
        self.assertFalse(r["live_authorized"])

    def test_matching_single_partial_fill(self):
        r = check([trade()])
        self.assertEqual(r["matched_quantity"], 1)
        self.assertEqual(r["quantity_status"], "PARTIAL")
        self.assertEqual(r["weighted_price_exact"], {"numerator": "12533", "denominator": "1000"})
        self.assertTrue(r["verified_fill"])
        self.assertNotIn("broker-order-1", str(r))

    def test_matching_three_fill_exact_weighted_price(self):
        rows = [trade(), trade("fill-2", price={"value": "12.534"}),
                trade("fill-3", price={"value": "12.536"})]
        r = check(rows)
        self.assertEqual(r["matched_quantity"], 3)
        self.assertEqual(r["quantity_status"], "FULL")
        self.assertEqual(r["weighted_price_exact"], {"numerator": "125343", "denominator": "10000"})

    def test_identical_repeat_trade_deduplicated(self):
        r = check([trade(), trade()])
        self.assertEqual(r["fill_count"], 1)

    def test_conflicting_trade_id_rejected(self):
        with self.assertRaisesRegex(M15FillEvidenceError, "ID_CONFLICT"):
            check([trade(), trade(price={"value": "12.535"})])

    def test_foreign_order_is_not_adopted(self):
        r = check([trade(order_id="some-other-order")])
        self.assertFalse(r["verified_fill"])

    def test_same_order_foreign_account_denied(self):
        with self.assertRaisesRegex(M15FillEvidenceError, "IDENTITY"):
            check([trade(account_id="h1-account")])

    def test_same_order_foreign_symbol_denied(self):
        with self.assertRaisesRegex(M15FillEvidenceError, "IDENTITY"):
            check([trade(symbol="USDRUBF@RTSX")])

    def test_same_order_wrong_side_denied(self):
        with self.assertRaisesRegex(M15FillEvidenceError, "IDENTITY"):
            check([trade(side="SIDE_SELL")])

    def test_exact_interval_boundary_exclusive(self):
        with self.assertRaisesRegex(M15FillEvidenceError, "OUTSIDE_HISTORY_INTERVAL"):
            check([trade(timestamp=END)])

    def test_nanosecond_timestamp_preserved(self):
        r = check([trade(timestamp="2026-10-16T07:01:00.123456789Z")])
        self.assertEqual(r["fill_count"], 1)

    def test_off_grid_price_rejected(self):
        with self.assertRaisesRegex(M15FillEvidenceError, "OFF_GRID"):
            check([trade(price={"value": "12.5335"})])

    def test_overfilled_order_rejected(self):
        with self.assertRaisesRegex(M15FillEvidenceError, "EXCEED"):
            check([trade(size={"value": "4"})])

    def test_fractional_contracts_rejected(self):
        with self.assertRaisesRegex(M15FillEvidenceError, "NOT_INTEGER"):
            check([trade(size={"value": "1.5"})])

    def test_unknown_currency_rejected(self):
        with self.assertRaisesRegex(M15FillEvidenceError, "CURRENCY"):
            check([trade(currency="USD")])

    def test_paginated_history_not_complete(self):
        with self.assertRaisesRegex(M15FillEvidenceError, "COMPLETENESS_UNPROVEN"):
            analyze_account_trades({"trades": [], "next_page_token": "more"}, target(), start=BEGIN,
                                   end=END, limit=1000)

    def test_limit_saturated_not_complete(self):
        with self.assertRaisesRegex(M15FillEvidenceError, "COMPLETENESS_UNPROVEN"):
            analyze_account_trades({"trades": [trade()]}, target(), start=BEGIN,
                                   end=END, limit=1)

    def test_invalid_interval_rejected(self):
        with self.assertRaisesRegex(M15FillEvidenceError, "INTERVAL"):
            analyze_account_trades({"trades": []}, target(), start=END,
                                   end=BEGIN, limit=1000)

    def test_does_not_infer_commissions_from_price(self):
        r = check([trade()])
        self.assertEqual(r["commission_authority"], "NOT_VERIFIED")

    def test_malformed_trade_value_rejected(self):
        with self.assertRaisesRegex(M15FillEvidenceError, "DECIMAL"):
            check([trade(price={"value": "nan"})])


if __name__ == "__main__":
    unittest.main()
