"""Synthetic future M15 cashflow: exact signed RUB transactions, no LIVE."""
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from IntradayLab.m15_robot.broker_risk_readonly import M15RiskAuthorityError
from IntradayLab.m15_robot.cashflow_reconcile_gate import (
    CashflowWindow, M15CashflowGateError, propose_realized_capital,
)

BIRTH = datetime(2026, 10, 16, 12, 0, tzinfo=timezone.utc)
NOW = datetime(2026, 10, 18, 12, 0, tzinfo=timezone.utc)
START = BIRTH - timedelta(seconds=1)
END = NOW + timedelta(minutes=1)


def cash(value):
    sign = -1 if value < 0 else 1
    rub, kopeks = divmod(abs(int(value * 100)), 100)
    return {"currency_code": "RUB", "units": str(rub * sign),
            "nanos": kopeks * 10000000 * sign}


def event(id, amount, category, when="2026-10-17T12:00:00Z"):
    return {
        "id": id, "timestamp": when, "transaction_category": category,
        "change": cash(amount),
    }


def account(realized="50000", floating="0", **fields):
    from decimal import Decimal
    equity = Decimal(realized) + Decimal(floating)
    result = {
        "account_id": "M15-SIM", "status": "ACCOUNT_ACTIVE",
        "type": "FORTS", "open_account_date": BIRTH.isoformat(),
        "positions": [],
        "equity": {"value": str(equity)},
        "unrealized_profit": {"value": floating},
        "portfolio_forts": {
            "available_cash": {"value": str(equity)},
            "money_reserved": {"value": "0"},
        },
    }
    result.update(fields)
    return result


def interval(rows=None, start=START, end=END, limit=1000, **changes):
    response = {"transactions": [event("deposit", 50000, "DEPOSIT")] if rows is None else rows}
    response.update(changes)
    return CashflowWindow(start, end, response, limit)


def proof(windows=None, broker=None):
    return propose_realized_capital(
        account=account() if broker is None else broker,
        expected_account_id="M15-SIM",
        windows=[interval()] if windows is None else windows,
        now=NOW,
    )


class FutureCashflowChecks(unittest.TestCase):
    def test_initial_deposit_still_matches_current_realized(self):
        result = proof()
        self.assertEqual(str(result.proposed_realized_equity), "50000")
        self.assertEqual(result.transaction_count, 1)
        self.assertFalse(result.runtime_r15_authorized)
        self.assertFalse(result.live_authorized)

    def test_two_contiguous_windows_deposits_income_fees_withdrawal(self):
        midpoint = datetime(2026, 10, 17, 0, 0, tzinfo=timezone.utc)
        first = interval(
            rows=[event("deposit", 50000, 1, "2026-10-16T12:00:00Z")],
            start=START, end=midpoint,
        )
        second = interval(
            rows=[event("commission", -10, "COMMISSION"),
                  event("income", 50, 5),
                  event("withdraw", -1000, "WITHDRAW")],
            start=midpoint, end=END,
        )
        got = proof([first, second], broker=account(realized="49040"))
        self.assertEqual(str(got.proposed_realized_equity), "49040")
        self.assertEqual(got.transaction_count, 4)

    def test_floating_equity_not_counted_as_realized(self):
        got = proof(broker=account(realized="50000", floating="250"))
        self.assertEqual(str(got.proposed_realized_equity), "50000")

    def test_future_equity_mismatch_refused(self):
        with self.assertRaisesRegex(M15CashflowGateError, "EQUITY_MISMATCH"):
            proof(broker=account(realized="49999"))

    def test_foreign_account_denied(self):
        with self.assertRaisesRegex(M15RiskAuthorityError, "BINDING"):
            proof(broker=account(account_id="H1-SIM"))

    def test_history_gap_refused(self):
        a = interval(rows=[], start=START, end=BIRTH)
        b = interval(rows=[event("deposit", 50000, 1)], start=BIRTH + timedelta(seconds=1), end=END)
        with self.assertRaisesRegex(M15CashflowGateError, "GAP_OVERLAP"):
            proof([a, b])

    def test_history_overlap_refused(self):
        a = interval(rows=[], start=START, end=BIRTH + timedelta(days=1))
        b = interval(rows=[event("deposit", 50000, 1)],
                     start=BIRTH + timedelta(hours=20), end=END)
        with self.assertRaisesRegex(M15CashflowGateError, "GAP_OVERLAP"):
            proof([a, b])

    def test_missing_terminal_window_refused(self):
        with self.assertRaisesRegex(M15CashflowGateError, "FINAL_WINDOW_MISSING"):
            proof([interval(rows=[], end=NOW)])

    def test_history_saturated_refused(self):
        with self.assertRaisesRegex(M15CashflowGateError, "HISTORY_NOT_COMPLETE"):
            proof([interval(limit=1)])

    def test_next_page_pointer_refused(self):
        with self.assertRaisesRegex(M15CashflowGateError, "HISTORY_NOT_COMPLETE"):
            proof([interval(next_page_token="more")])

    def test_duplicate_id_across_windows_refused(self):
        middle = datetime(2026, 10, 17, 0, tzinfo=timezone.utc)
        a = interval(rows=[event("same", 25000, 1, "2026-10-16T13:00:00Z")],
                     start=START, end=middle)
        b = interval(rows=[event("same", 25000, 1)], start=middle, end=END)
        with self.assertRaisesRegex(M15CashflowGateError, "ID_INVALID"):
            proof([a, b])

    def test_undocumented_category_refused(self):
        with self.assertRaisesRegex(M15CashflowGateError, "CATEGORY_NOT_DOCUMENTED"):
            proof([interval(rows=[event("other", 50000, "GUESS_MARGIN_SETTLEMENT")])])

    def test_unknown_numeric_category_refused(self):
        with self.assertRaisesRegex(M15CashflowGateError, "CATEGORY_NOT_DOCUMENTED"):
            proof([interval(rows=[event("other", 50000, 99)])])

    def test_nonrub_transaction_refused(self):
        row = event("foreign", 50000, 1)
        row["change"]["currency_code"] = "USD"
        with self.assertRaisesRegex(M15RiskAuthorityError, "NONRUB"):
            proof([interval(rows=[row])])

    def test_transaction_outside_covered_interval_refused(self):
        with self.assertRaisesRegex(M15CashflowGateError, "OUTSIDE_WINDOW"):
            proof([interval(rows=[event("too-late", 50000, 1, "2026-10-19T00:00:00Z")])])

    def test_replayed_reversed_window_order_refused(self):
        middle = datetime(2026, 10, 17, 0, tzinfo=timezone.utc)
        a = interval(rows=[], start=START, end=middle)
        b = interval(rows=[event("deposit", 50000, 1)], start=middle, end=END)
        with self.assertRaisesRegex(M15CashflowGateError, "GAP_OVERLAP"):
            proof([b, a])

    def test_missing_transactions_field_refused(self):
        with self.assertRaisesRegex(M15CashflowGateError, "TRANSACTIONS_SCHEMA"):
            proof([CashflowWindow(START, END, {"wrong_key": []})])

    def test_no_history_refused(self):
        with self.assertRaisesRegex(M15CashflowGateError, "LIFETIME_INCOMPLETE"):
            proof(windows=[])

    def test_unaware_clock_refused(self):
        with self.assertRaisesRegex(M15CashflowGateError, "TIMEZONE_INVALID"):
            propose_realized_capital(account=account(), expected_account_id="M15-SIM",
                                     windows=[interval()], now=datetime(2026, 10, 18))

    def test_zero_transactions_cannot_infer_positive_equity(self):
        with self.assertRaisesRegex(M15CashflowGateError, "EQUITY_MISMATCH"):
            proof([interval(rows=[])])

    def test_ambiguous_commission_value_rejected(self):
        row = event("fee", -1, 7)
        row["change"] = {"currency_code": "RUB", "units": "-1", "nanos": 1}
        with self.assertRaisesRegex(M15RiskAuthorityError, "MONEY_INVALID"):
            proof([interval(rows=[row])])

    def test_result_contains_no_raw_transaction_ids(self):
        result = proof()
        self.assertNotIn("deposit", str(result))
        self.assertEqual(len(result.transaction_fingerprint_sha256), 64)


if __name__ == "__main__":
    unittest.main()
