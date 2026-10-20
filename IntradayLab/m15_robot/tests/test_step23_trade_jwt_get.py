"""Exact M15 trading JWT read-side financial snapshot; offline-only."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from IntradayLab.m15_robot.finam_readonly import M15FinamReadOnlyAPI
from IntradayLab.m15_robot.step23_trade_jwt_get import (
    M15TradingJwtGetError, verify_m15_trade_jwt_broker_get,
)
from IntradayLab.m15_robot.tests.test_step23_readonly_preflight import (
    ACCOUNT, asset, params,
)


class TestM15TradeJWTGetOnly(TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.root = Path(self.temp.name) / "m15"
        (self.root / "state").mkdir(parents=True)
        (self.root / "state" / "kill-switch.json").write_text(
            '{"state":"HALTED"}', encoding="utf-8")
        self.api = object.__new__(M15FinamReadOnlyAPI)
        self.kw = {"api": self.api, "m15_account_id": "M15-SYNTH",
                   "runtime_root": self.root}

    def tearDown(self):
        self.temp.cleanup()

    def broker(self, *, account=ACCOUNT, orders=None, trading=True):
        from contextlib import ExitStack
        scope=ExitStack()
        scope.enter_context(patch.object(
            M15FinamReadOnlyAPI, "readonly_bound", False))
        scope.enter_context(patch.object(
            M15FinamReadOnlyAPI, "trading_get_only_bound", trading))
        scope.enter_context(patch.object(
            M15FinamReadOnlyAPI, "account_id", "M15-SYNTH"))
        get_account=scope.enter_context(patch.object(
            M15FinamReadOnlyAPI, "account", return_value=account))
        get_orders=scope.enter_context(patch.object(
            M15FinamReadOnlyAPI, "orders",
            return_value={"orders": []} if orders is None else orders))
        scope.enter_context(patch.object(
            M15FinamReadOnlyAPI, "asset_details", side_effect=asset))
        scope.enter_context(patch.object(
            M15FinamReadOnlyAPI, "asset_params", side_effect=params))
        return scope,get_account,get_orders

    def test_full_n4_snapshot_with_actual_trading_scope(self):
        scope,acc,orders=self.broker()
        with scope:
            report=verify_m15_trade_jwt_broker_get(**self.kw)
        self.assertTrue(report["exact_trading_jwt_get"])
        self.assertTrue(report["n4_go_and_tick"])
        self.assertFalse(report["order_post_permitted"])
        self.assertFalse(report["live_authorized"])
        acc.assert_called_once_with("M15-SYNTH")
        orders.assert_called_once_with("M15-SYNTH")

    def test_readonly_scope_is_not_accepted_for_trading_jwt_proof(self):
        scope,acc,orders=self.broker(trading=False)
        with scope, self.assertRaisesRegex(
            M15TradingJwtGetError, "TRADING_JWT_NOT_EXACT_BOUND"):
            verify_m15_trade_jwt_broker_get(**self.kw)
        acc.assert_not_called()
        orders.assert_not_called()

    def test_broker_active_order_and_position_fail_closed(self):
        scope,_,_=self.broker(account={**ACCOUNT, "positions":[{
                "symbol":"CNYRUBF@RTSX", "quantity":{"value":"1"}}]})
        with scope, self.assertRaisesRegex(
            M15TradingJwtGetError, "BROKER_NOT_FLAT"):
            verify_m15_trade_jwt_broker_get(**self.kw)

    def test_halted_runtime_must_exist(self):
        (self.root / "state" / "kill-switch.json").unlink()
        scope,acc,orders=self.broker()
        with scope, self.assertRaises(Exception):
            verify_m15_trade_jwt_broker_get(**self.kw)
        acc.assert_not_called()
        orders.assert_not_called()
