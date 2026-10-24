"""Focused V20-08.1 adapter tests: synthetic FINAM, zero network/orders."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import unittest

from TradingSystemLab.stage8_robot.finam_api import FinamAPI
from TradingSystemLab.stage8_robot.production_runtime import _load_registry

from V20_TradingSystem_M15.v20_runtime.finam_execution import (
    V20FinamBlocked, V20FinamReadAdapter,
)


ACCOUNT = "isolated-test-account-a"
ACCOUNT_HASH = hashlib.sha256(ACCOUNT.encode()).hexdigest()


def funds(value):
    return {"value": str(value)}


def margin(value):
    return {"currency_code": "RUB", "units": str(value), "nanos": 0}


class FakeFinam(FinamAPI):
    """Explicit fake implementation, intentionally never calls base HTTP."""
    def __init__(self, *, account_id=ACCOUNT, readonly=False):
        self.account_id = account_id
        self.readonly = readonly
        self.calls = []
        self.positions = []
        self.order_rows = []

    def create_session(self):
        self.calls.append("auth")

    def session_details(self):
        self.calls.append("session_details")
        return {"readonly": self.readonly, "account_ids": [self.account_id]}

    def account(self, account_id):
        self.calls.append(("account", account_id))
        return {
            "account_id": self.account_id,
            "status": "ACCOUNT_ACTIVE",
            "type": "FORTS",
            "portfolio_forts": {
                "available_cash": funds("45000"), "money_reserved": funds("0"),
            },
            "equity": funds("45000"),
            "unrealized_profit": funds("0"),
            "positions": self.positions,
        }

    def orders(self, account_id):
        self.calls.append(("orders", account_id))
        return {"orders": self.order_rows}

    def asset_params(self, symbol, account_id):
        self.calls.append(("params", symbol, account_id))
        return {"long_initial_margin": margin("1500"),
                "short_initial_margin": margin("1600")}

    def place_order(self, *_args, **_kwargs):
        raise AssertionError("ORDER_TRANSMISSION_FORBIDDEN")

    def place_sltp_order(self, *_args, **_kwargs):
        raise AssertionError("SLTP_TRANSMISSION_FORBIDDEN")

    def cancel_order(self, *_args, **_kwargs):
        raise AssertionError("DELETE_TRANSMISSION_FORBIDDEN")


class V20BrokerAdapterTests(unittest.TestCase):
    def client(self, api=None):
        api = api or FakeFinam()
        return V20FinamReadAdapter(
            api=api, robot_id="v20-shallow", account_id=ACCOUNT,
            expected_account_hash=ACCOUNT_HASH,
        )

    def test_authentication_and_money_are_real_account_scoped(self):
        api = FakeFinam()
        reader = self.client(api)
        with self.assertRaisesRegex(V20FinamBlocked, "TRADING_SESSION_NOT_BOUND"):
            reader.snapshot(now=datetime.now(timezone.utc))
        reader.authenticate()
        now = datetime.now(timezone.utc)
        snap = reader.snapshot(now=now)
        self.assertTrue(snap.clean)
        self.assertEqual(snap.realized_equity, Decimal("45000"))
        self.assertEqual(snap.available_cash, Decimal("45000"))
        authority = reader.authority(
            snap, symbol="CNYRUBF", direction="LONG",
            roundtrip_cost_per_contract=Decimal("1.8"), now=now,
        )
        self.assertEqual(authority.realized_equity, Decimal("45000"))
        self.assertEqual(authority.initial_margin, Decimal("1500"))
        self.assertEqual(authority.roundtrip_cost_per_contract, Decimal("1.8"))
        self.assertEqual(authority.price_step, Decimal(_load_registry()["CNYRUBF"]["price_step"]))
        self.assertEqual(
            api.calls[-1],
            ("params", _load_registry()["CNYRUBF"]["finam_symbol"], ACCOUNT),
        )
        self.assertFalse(hasattr(reader, "submit"))
        self.assertFalse(hasattr(reader, "place_order"))
        self.assertFalse(hasattr(reader, "cancel"))

    def test_readonly_or_foreign_token_denied(self):
        for api in (FakeFinam(readonly=True), FakeFinam(account_id="different-account")):
            with self.subTest(api=api.account_id, readonly=api.readonly):
                with self.assertRaisesRegex(V20FinamBlocked, "EXACT_TRADING_TOKEN_SCOPE_REQUIRED"):
                    self.client(api).authenticate()
                self.assertNotIn(("account", ACCOUNT), api.calls)

    def test_identity_rejected_before_broker_contact(self):
        api = FakeFinam()
        with self.assertRaisesRegex(V20FinamBlocked, "ACCOUNT_IDENTITY_MISMATCH"):
            V20FinamReadAdapter(api=api, robot_id="v20-shallow",
                                account_id=ACCOUNT, expected_account_hash="0" * 64)
        self.assertEqual(api.calls, [])

    def test_unowned_position_or_order_never_authorizes_account(self):
        api = FakeFinam()
        api.positions = [{"symbol": "UNKNOWN@RTSX", "quantity": funds("1")}]
        reader = self.client(api)
        reader.authenticate()
        with self.assertRaisesRegex(V20FinamBlocked, "FOREIGN_ACCOUNT_POSITION"):
            reader.snapshot(now=datetime.now(timezone.utc))

    def test_missing_cost_stale_data_and_cross_account_prohibited(self):
        reader = self.client()
        reader.authenticate()
        now = datetime.now(timezone.utc)
        snap = reader.snapshot(now=now)
        with self.assertRaisesRegex(V20FinamBlocked, "BROKER_TARIFF_REQUIRED"):
            reader.authority(snap, symbol="USDRUBF", direction="LONG",
                             roundtrip_cost_per_contract="0", now=now)
        with self.assertRaisesRegex(V20FinamBlocked, "STALE_FINAM_ACCOUNT_SNAPSHOT"):
            reader.authority(snap, symbol="USDRUBF", direction="LONG",
                             roundtrip_cost_per_contract="1", now=now+timedelta(minutes=2))
        with self.assertRaisesRegex(V20FinamBlocked, "ACCOUNT_AUTHORITY_SCOPE_INVALID"):
            reader.authority(snap, symbol="BR", direction="LONG",
                             roundtrip_cost_per_contract="1", now=now)


if __name__ == "__main__":
    unittest.main()
