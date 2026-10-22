"""Only offline synthetic FINAM cashflow/protobuf receipts. No real credentials."""
import unittest
from copy import deepcopy
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from IntradayLab.m15_robot.broker_risk_readonly import M15AccountSnapshot, M15RiskAuthorityError
from IntradayLab.m15_robot.initial_capital import lifetime_interval, prove_initial_basis


BIRTH = "2026-10-17T00:00:00Z"
NOW = datetime(2026, 10, 18, 10, tzinfo=timezone.utc)


def fixture():
    account = {"open_account_date": BIRTH}
    funds = M15AccountSnapshot(
        Decimal("50000"), Decimal("50000"), Decimal("0"),
        Decimal("50000"), "portfolio_mc",
    )
    row = {"id": "tx-1", "timestamp": "2026-10-18T00:00:00Z",
           "transaction_category": "DEPOSIT",
           "change": {"currency_code": "RUB", "units": "50000"}}
    _, _, begin, end = lifetime_interval(account, NOW)
    return dict(account=account, funds=funds, trades={"trades": []},
                transactions={"transactions": [row]}, begin=begin, end=end)


class InitialCashFlowOnlyProof(unittest.TestCase):
    def test_no_trades_exact_initial_cashflow_pass(self):
        f = fixture()
        result = prove_initial_basis(**f)
        self.assertEqual(result.basis, Decimal("50000"))
        self.assertEqual(result.deposit_count, 1)
        self.assertEqual(result.authority, "INITIAL_CASHFLOW_ONLY")

    def test_multiple_deposits_exact_sum_pass(self):
        f = fixture()
        x = f["transactions"]["transactions"][0]
        x["change"]["units"] = "20000"
        y = deepcopy(x)
        y["id"] = "tx-2"
        y["transaction_category"] = "TRANSFER"
        y["change"]["units"] = "30000"
        f["transactions"]["transactions"].append(y)
        self.assertEqual(prove_initial_basis(**f).deposit_count, 2)

    def test_deposit_does_not_equal_broker_realized_denied(self):
        f = fixture()
        f["transactions"]["transactions"][0]["change"]["units"] = "49999"
        with self.assertRaisesRegex(M15RiskAuthorityError, "EQUITY_MISMATCH"):
            prove_initial_basis(**f)

    def test_commission_or_other_category_denied(self):
        f = fixture()
        f["transactions"]["transactions"][0]["transaction_category"] = "COMMISSION"
        with self.assertRaisesRegex(M15RiskAuthorityError, "NONDEPOSIT_TRANSACTION"):
            prove_initial_basis(**f)

    def test_negative_deposit_denied(self):
        f = fixture()
        f["transactions"]["transactions"][0]["change"]["units"] = "-50000"
        with self.assertRaisesRegex(M15RiskAuthorityError, "NONPOSITIVE_DEPOSIT"):
            prove_initial_basis(**f)

    def test_duplicate_broker_transaction_denied(self):
        f = fixture()
        f["transactions"]["transactions"].append(deepcopy(f["transactions"]["transactions"][0]))
        with self.assertRaisesRegex(M15RiskAuthorityError, "ID_INVALID"):
            prove_initial_basis(**f)

    def test_broker_trade_history_nonempty_denied(self):
        f = fixture()
        f["trades"] = {"trades": [{"synthetic": "trade"}]}
        with self.assertRaisesRegex(M15RiskAuthorityError, "TRADES_NOT_ZERO"):
            prove_initial_basis(**f)

    def test_prior_trade_timestamp_denied(self):
        f = fixture()
        f["account"]["first_trade_date"] = "2026-10-17T17:00:00Z"
        with self.assertRaisesRegex(M15RiskAuthorityError, "PAST_TRADE"):
            prove_initial_basis(**f)

    def test_missing_or_saturated_transaction_history_denied(self):
        f = fixture()
        f["transactions"] = {"transactions": []}
        with self.assertRaisesRegex(M15RiskAuthorityError, "EMPTY_OR_SATURATED"):
            prove_initial_basis(**f)
        f = fixture()
        with self.assertRaisesRegex(M15RiskAuthorityError, "EMPTY_OR_SATURATED"):
            prove_initial_basis(**f, limit=1)

    def test_nonrub_cash_movement_denied(self):
        f = fixture()
        f["transactions"]["transactions"][0]["change"]["currency_code"] = "USD"
        with self.assertRaisesRegex(M15RiskAuthorityError, "NONRUB"):
            prove_initial_basis(**f)

    def test_floating_profit_not_initial_basis(self):
        f = fixture()
        funds = f["funds"]
        f["funds"] = M15AccountSnapshot(funds.available_cash, funds.equity,
                                        Decimal("1"), funds.broker_equity_minus_unrealized,
                                        funds.portfolio_type)
        with self.assertRaisesRegex(M15RiskAuthorityError, "NONFLAT_FINANCIAL"):
            prove_initial_basis(**f)

    def test_future_and_too_old_open_date_denied(self):
        for birth in ("2026-11-01T00:00:00Z", "2026-08-01T00:00:00Z"):
            with self.subTest(birth=birth):
                with self.assertRaisesRegex(M15RiskAuthorityError, "LIFETIME_UNSUPPORTED"):
                    lifetime_interval({"open_account_date": birth}, NOW)

    def test_foreign_or_unparseable_transaction_timestamp_denied(self):
        f = fixture()
        f["transactions"]["transactions"][0]["timestamp"] = "2026-10-19T00:00:00Z"
        with self.assertRaisesRegex(M15RiskAuthorityError, "OUT_OF_INTERVAL"):
            prove_initial_basis(**f)
        f = fixture()
        f["transactions"]["transactions"][0]["timestamp"] = "bad"
        with self.assertRaisesRegex(M15RiskAuthorityError, "TIMESTAMP_INVALID"):
            prove_initial_basis(**f)


if __name__ == "__main__":
    unittest.main()
