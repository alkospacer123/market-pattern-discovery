"""No-token synthetic REST account / N4 GO / tick metadata authority tests."""
import unittest
from decimal import Decimal as D

from IntradayLab.m15_robot.broker_risk_readonly import (
    M15RiskAuthorityError, check_account, check_instrument, decimal_value, rub_money,
)


def money(units="22100", nanos=900000000):
    return {"currency_code": "RUB", "units": units, "nanos": nanos}


def account():
    return {
        "account_id": "m15-only", "status": "ACCOUNT_ACTIVE", "type": "FORTS",
        "positions": [], "equity": {"value": "50000.00"},
        "unrealized_profit": {"value": "0.00"},
        "portfolio_forts": {
            "available_cash": {"value": "49500.00"}, "money_reserved": {"value": "500.00"}
        },
    }


def asset():
    return {"ticker": "USDRUBF", "mic": "RTSX", "decimals": 2,
            "min_step": "1", "lot_size": {"value": "1"}}


def params():
    return {"symbol": "USDRUBF@RTSX", "account_id": "m15-only",
            "trade_lot_size": "1", "long_initial_margin": money(),
            "short_initial_margin": money("23100", 0)}


class M15ReadOnlyRiskProof(unittest.TestCase):
    def test_forts_equity_float_and_available_cash(self):
        x = check_account(account(), "m15-only")
        self.assertEqual(x.available_cash, D("49500"))
        self.assertEqual(x.broker_equity_minus_unrealized, D("50000"))
        self.assertEqual(x.portfolio_type, "portfolio_forts")

    def test_wrong_account_denied(self):
        with self.assertRaisesRegex(M15RiskAuthorityError, "BINDING"):
            check_account(account(), "h1")

    def test_portfolio_multiple_oneofs_denied(self):
        x = account()
        x["portfolio_mc"] = {}
        with self.assertRaisesRegex(M15RiskAuthorityError, "ONEOF"):
            check_account(x, "m15-only")

    def test_missing_equity_denied(self):
        x = account()
        x.pop("equity")
        with self.assertRaisesRegex(M15RiskAuthorityError, "DECIMAL"):
            check_account(x, "m15-only")

    def test_nan_decimal_denied(self):
        with self.assertRaisesRegex(M15RiskAuthorityError, "DECIMAL"):
            decimal_value({"value": "nan"})

    def test_money_exact_rubles(self):
        self.assertEqual(rub_money(money()), D("22100.9"))

    def test_money_non_rub_denied(self):
        x = money()
        x["currency_code"] = "USD"
        with self.assertRaisesRegex(M15RiskAuthorityError, "MONEY_SCHEMA"):
            rub_money(x)

    def test_money_opposite_sign_denied(self):
        with self.assertRaisesRegex(M15RiskAuthorityError, "MONEY_INVALID"):
            rub_money(money("-1", 100000000))

    def test_account_negative_available_denied(self):
        x = account()
        x["portfolio_forts"]["available_cash"]["value"] = "-1"
        with self.assertRaisesRegex(M15RiskAuthorityError, "FINANCIAL"):
            check_account(x, "m15-only")

    def test_n4_go_exact_step_and_lot(self):
        p = check_instrument(asset(), params(), "USDRUBF@RTSX", "m15-only")
        self.assertEqual(p.price_step, D("0.01"))
        self.assertEqual(p.trade_lot_size, 1)
        self.assertEqual(p.long_initial_margin_rub, D("22100.9"))
        self.assertEqual(p.short_initial_margin_rub, D("23100"))
        self.assertEqual(p.tick_value_authority, "NOT_PROVEN")

    def test_wrong_account_params_denied(self):
        x = params()
        x["account_id"] = "h1-account"
        with self.assertRaisesRegex(M15RiskAuthorityError, "MISMATCH"):
            check_instrument(asset(), x, "USDRUBF@RTSX", "m15-only")

    def test_wrong_symbol_asset_denied(self):
        x = asset()
        x["ticker"] = "CNYRUBF"
        with self.assertRaisesRegex(M15RiskAuthorityError, "MISMATCH"):
            check_instrument(x, params(), "USDRUBF@RTSX", "m15-only")

    def test_unknown_symbol_denied(self):
        with self.assertRaisesRegex(M15RiskAuthorityError, "NOT_N4"):
            check_instrument(asset(), params(), "BR@RTSX", "m15-only")

    def test_zero_lot_denied(self):
        x = params()
        x["trade_lot_size"] = "0"
        with self.assertRaisesRegex(M15RiskAuthorityError, "TRADE_LOT"):
            check_instrument(asset(), x, "USDRUBF@RTSX", "m15-only")

    def test_negative_margin_denied(self):
        x = params()
        x["long_initial_margin"] = money("-22100", 0)
        with self.assertRaisesRegex(M15RiskAuthorityError, "MONEY_NOT_POSITIVE"):
            check_instrument(asset(), x, "USDRUBF@RTSX", "m15-only")

    def test_unsupported_portfolio_denied(self):
        x = account()
        x["type"] = "OTHER"
        with self.assertRaisesRegex(M15RiskAuthorityError, "TYPE"):
            check_account(x, "m15-only")


if __name__ == "__main__":
    unittest.main()
