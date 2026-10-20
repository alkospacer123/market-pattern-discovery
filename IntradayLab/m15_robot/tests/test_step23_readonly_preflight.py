"""Synthetic M15 step #23 financial GET preflight; no order client."""
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from IntradayLab.m15_robot.finam_readonly import M15FinamReadOnlyAPI
from IntradayLab.m15_robot.step23_readonly_preflight import (
    M15Step23PreflightError, inspect_m15_halted_runtime,
    verify_m15_step23_financial_preflight,
)
from IntradayLab.m15_robot.spec import INSTRUMENTS

NOW = datetime(2026, 10, 20, 15, tzinfo=timezone.utc)
ACCOUNT = {
    "account_id": "M15-SYNTH", "status": "ACCOUNT_ACTIVE",
    "type": "FORTS", "positions": [],
    "equity": {"value": "20000"},
    "unrealized_profit": {"value": "0"},
    "portfolio_forts": {
        "available_cash": {"value": "20000"},
        "money_reserved": {"value": "0"},
    }, "open_account_date": "2026-10-19T00:00:00Z",
}
TX = {"transactions": [
    {"id": "deposit-one", "timestamp": "2026-10-19T03:00:00Z",
     "transaction_category": "DEPOSIT",
     "change": {"currency_code": "RUB", "units": "20000", "nanos": 0}},
]}
STEPS = {"USDRUBF": (2, "1"), "CNYRUBF": (3, "1"),
         "GLDRUBF": (1, "1"), "IMOEXF": (1, "5")}


def asset(symbol):
    name = symbol.split("@")[0]
    decimals, minimum = STEPS[name]
    return {"ticker":name,"mic":"RTSX","decimals":decimals,"min_step":minimum}


def params(symbol):
    rub = {"currency_code": "RUB", "units": "1000", "nanos": 0}
    return {"symbol":symbol,"account_id":"M15-SYNTH",
            "trade_lot_size":"1","long_initial_margin":rub,
            "short_initial_margin":rub}


class M15Step23PreflightTests(TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.root = Path(self.temp.name)/"m15-runtime"
        (self.root/"state").mkdir(parents=True)
        (self.root/"state"/"kill-switch.json").write_text(
            '{"state":"HALTED"}', encoding="utf-8")
        self.api = object.__new__(M15FinamReadOnlyAPI)
        self.kw = dict(api=self.api, m15_account_id="M15-SYNTH",
                       h1_account_id="H1-DIFFERENT",
                       runtime_root=self.root, observed_at=NOW)

    def tearDown(self):
        self.temp.cleanup()

    def patch_broker(self, *, account=ACCOUNT, orders=None, transactions=TX):
        from contextlib import ExitStack
        stack = ExitStack()
        stack.enter_context(patch.object(
            M15FinamReadOnlyAPI,"readonly_bound",True))
        stack.enter_context(patch.object(
            M15FinamReadOnlyAPI,"account_id","M15-SYNTH"))
        stack.enter_context(patch.object(
            M15FinamReadOnlyAPI,"account",return_value=account))
        stack.enter_context(patch.object(
            M15FinamReadOnlyAPI,"orders",
            return_value={"orders": []} if orders is None else orders))
        stack.enter_context(patch.object(
            M15FinamReadOnlyAPI,"transactions",return_value=transactions))
        stack.enter_context(patch.object(
            M15FinamReadOnlyAPI,"asset_details",side_effect=asset))
        stack.enter_context(patch.object(
            M15FinamReadOnlyAPI,"asset_params",side_effect=params))
        return stack

    def test_fresh_broker_cashflow_n4_and_halted_no_order(self):
        with self.patch_broker():
            result = verify_m15_step23_financial_preflight(**self.kw)
        self.assertEqual(result["status"],"PASS_FINANCIAL_GET_ONLY")
        self.assertEqual(result["signal_next_open_atr_trade_size"],"NOT_EVALUATED")
        self.assertTrue(result["n4_broker_go_tick_proven"])
        self.assertFalse(result["entry_order_permitted"])
        self.assertFalse(result["live_authorized"])

    def test_missing_halted_file_and_production_heartbeat_are_not_created(self):
        (self.root/"state"/"kill-switch.json").unlink()
        with self.assertRaisesRegex(M15Step23PreflightError,"HALTED_FILE_MISSING"):
            inspect_m15_halted_runtime(self.root)
        self.assertFalse((self.root/"diagnostics"/"m15-production-heartbeat.json").exists())
        self.assertFalse((self.root/"safety"/"m15-trading-kill-switch.json").exists())

    def test_same_h1_account_is_rejected_before_financial_get(self):
        with patch.object(M15FinamReadOnlyAPI,"readonly_bound",True), patch.object(
                 M15FinamReadOnlyAPI,"account_id","M15-SYNTH"), patch.object(
                 M15FinamReadOnlyAPI,"account") as account:
            with self.assertRaisesRegex(M15Step23PreflightError,"SEPARATE_READONLY"):
                verify_m15_step23_financial_preflight(
                    **{**self.kw,"h1_account_id":"M15-SYNTH"})
            account.assert_not_called()

    def test_wrong_balance_and_foreign_position_fail_closed(self):
        with self.patch_broker(account={**ACCOUNT,"positions":[{
                "symbol":"CNYRUBF@RTSX", "quantity":{"value":"1"}}]}):
            with self.assertRaisesRegex(M15Step23PreflightError,"ACCOUNT_NOT_FLAT"):
                verify_m15_step23_financial_preflight(**self.kw)
        with self.patch_broker(
                account={**ACCOUNT,"equity":{"value":"20100"}}):
            with self.assertRaisesRegex(Exception,"REALIZED_EQUITY_MISMATCH"):
                verify_m15_step23_financial_preflight(**self.kw)

    def test_existing_production_artifacts_require_review_no_overwrite(self):
        (self.root/"diagnostics").mkdir()
        path=self.root/"diagnostics"/"m15-production-heartbeat.json"
        path.write_text('{"schema_id":"unexpected"}',encoding="utf-8")
        with self.patch_broker():
            with self.assertRaisesRegex(M15Step23PreflightError,
                                        "PRODUCTION_RUNTIME_REVIEW_REQUIRED"):
                verify_m15_step23_financial_preflight(**self.kw)
        self.assertEqual(path.read_text(encoding="utf-8"),
                         '{"schema_id":"unexpected"}')


if __name__ == "__main__":
    import unittest
    unittest.main()
