"""Only two 08.1 tests of existing frozen FINAM->H1 R15 path; no POST."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from TradingSystemLab.stage8_robot.finam_api import FinamAPI, Response
from V20_TradingSystem_M15.v20_runtime.account_risk import AccountAuthority
from V20_TradingSystem_M15.v20_runtime.offline_planner import FrozenSignal
from V20_TradingSystem_M15.v20_runtime.finam_execution import (
    V20FinamReadAdapter, V20FinamBlocked, propose_finam_m15_next_open,
)
import V20_TradingSystem_M15.v20_runtime.finam_execution as execution

ACCOUNT = "isolated-fake-m15-bridge"
HASH = hashlib.sha256(ACCOUNT.encode()).hexdigest()
AT = datetime(2026, 10, 24, 7, 30, 5, tzinfo=timezone.utc)
START = AT - timedelta(hours=1)
SYMBOL = "USDRUBF@RTSX"


def val(v):
    return {"value": str(v)}


class FakeBroker(FinamAPI):
    def __init__(self):
        self.bar_reads = 0
        self.money_reads = 0
        self.order_posts = 0

    def create_session(self):
        return {}

    def session_details(self):
        return {"readonly": False, "account_ids": [ACCOUNT]}

    def _request(self, method, path, *_args, **_kw):
        if method != "GET":
            raise AssertionError("NO_FINAM_POST_PERMITTED")
        p = urlparse(path)
        if p.path != "/v1/instruments/" + SYMBOL + "/bars":
            raise AssertionError("ONLY_M15_READING_EXPECTED")
        self.bar_reads += 1
        if parse_qs(p.query).get("timeframe") != ["TIME_FRAME_M15"]:
            raise AssertionError("M15_ONLY")
        bars = []
        for minute in (0, 15, 30):
            stamp = datetime(2026, 10, 24, 7, minute, tzinfo=timezone.utc)
            row = {"timestamp": stamp.isoformat(), "open": val("85.00")}
            if minute < 30:
                row.update(high=val("85.10"), low=val("84.90"),
                           close=val("85.02"), volume=val("100"))
            bars.append(row)
        return Response(200, {"symbol": SYMBOL, "bars": bars}, None)

    def account(self, account_id):
        if account_id != ACCOUNT:
            raise AssertionError("FOREIGN_ACCOUNT")
        self.money_reads += 1
        return {"account_id": ACCOUNT, "status": "ACCOUNT_ACTIVE",
                "type": "FORTS", "equity": val("45000"),
                "unrealized_profit": val("0"),
                "portfolio_forts": {"available_cash": val("45000"),
                                    "money_reserved": val("0")}, "positions": []}

    def orders(self, account_id):
        if account_id != ACCOUNT:
            raise AssertionError("FOREIGN_ACCOUNT")
        return {"orders": []}

    def place_order(self, *_args, **_kw):
        self.order_posts += 1
        raise AssertionError("ENTRY_SENDER_MUST_NOT_BE_CALLED")


class NextOpenBridgeTests(unittest.TestCase):
    def setUp(self):
        self.api = FakeBroker()
        self.reader = V20FinamReadAdapter(
            api=self.api, robot_id="v20-shallow", account_id=ACCOUNT,
            expected_account_hash=HASH,
        )
        self.reader.authenticate()

    def test_true_frozen_signal_makes_only_unpersisted_h1_risk_candidate(self):
        signal = FrozenSignal("SHALLOW_PULLBACK", "USDRUBF", 1,
                              datetime(2026, 10, 24, 10, 15), Decimal("0.1"))
        risk = AccountAuthority(
            ACCOUNT, Decimal("45000"), Decimal("45000"), Decimal("0.01"),
            Decimal("10"), Decimal("1500"), 1, Decimal("2"),
        )
        with patch.object(execution, "completed_signal", return_value=signal) as frozen:
            with patch.object(self.reader, "authority", return_value=risk) as economics:
                result = propose_finam_m15_next_open(
                    self.reader, symbol="USDRUBF", from_utc=START,
                    now=AT, cost_per_contract=Decimal("2"),
                )
        self.assertIsNotNone(result)
        seen, candidate, authority, snapshot = result
        self.assertEqual(seen, signal)
        self.assertEqual(candidate.entry_bar_open, datetime(2026, 10, 24, 10, 30))
        self.assertEqual(candidate.reference_entry, Decimal("85.00"))
        self.assertEqual(candidate.initial_stop, Decimal("84.80"))
        self.assertGreater(candidate.quantity, 0)
        self.assertLessEqual(candidate.quantity, 3)
        self.assertEqual(candidate.mode, "OFFLINE_REFERENCE_NOT_ORDER")
        self.assertEqual(authority, risk)
        self.assertTrue(snapshot.clean)
        self.assertEqual(frozen.call_count, 1)
        self.assertEqual(economics.call_count, 1)
        self.assertEqual(self.api.bar_reads, 1)
        self.assertEqual(self.api.money_reads, 1)
        self.assertEqual(self.api.order_posts, 0)

    def test_no_signal_never_reads_money_or_sends_orders(self):
        with patch.object(execution, "completed_signal", return_value=None):
            result = propose_finam_m15_next_open(
                self.reader, symbol="USDRUBF", from_utc=START,
                now=AT, cost_per_contract=Decimal("2"),
            )
        self.assertIsNone(result)
        self.assertEqual(self.api.bar_reads, 1)
        self.assertEqual(self.api.money_reads, 0)
        self.assertEqual(self.api.order_posts, 0)


if __name__ == "__main__":
    unittest.main()
