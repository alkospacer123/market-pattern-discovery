"""08.1 only: three fake FINAM checks for the existing GET-only candidate hook."""
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
import os
import unittest
from unittest.mock import patch
from TradingSystemLab.stage8_robot.finam_api import FinamAPI
from V20_TradingSystem_M15.v20_runtime import finam_worker as worker
from V20_TradingSystem_M15.v20_runtime.offline_planner import FrozenSignal, OfflinePlanner
from V20_TradingSystem_M15.v20_runtime.account_risk import AccountAuthority
from V20_TradingSystem_M15.v20_runtime.finam_execution import V20FinamBlocked
from test_finam_next_open_bridge import ACCOUNT, HASH, FakeBroker


class CandidateReadOnlyTests(unittest.TestCase):
    def setUp(self):
        self.api = FakeBroker()
        self.env = patch.dict(os.environ, {
            "V20_FINAM_ACCOUNT": ACCOUNT,
            "V20_FINAM_TOKEN": "SYNTHETIC_NOT_REAL",
            "V20_FINAM_ACCOUNT_SHA256": HASH,
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        self.conn = patch.object(worker, "AuthorityReadOnlyAPI", return_value=self.api)
        self.conn.start()
        self.addCleanup(self.conn.stop)

    def test_actual_frozen_candidate_uses_h1_cost_stop_go_no_post(self):
        signal = FrozenSignal("SHALLOW_PULLBACK", "USDRUBF", 1,
                              datetime(2026, 10, 24, 10, 15), Decimal("0.1"))
        fee = Decimal("8.34")
        auth = AccountAuthority(
            ACCOUNT, Decimal("45000"), Decimal("45000"), Decimal("0.01"),
            Decimal("10"), Decimal("1500"), 1, fee,
        )
        entry = OfflinePlanner(signal.strategy).reference_next_open(
            signal, at=datetime(2026, 10, 24, 10, 30),
            entry_open=Decimal("85.00"), realized_equity=Decimal("45000"),
            price_step=auth.price_step, tick_value=auth.tick_value,
            initial_margin=auth.initial_margin,
            available_cash=auth.available_cash, trade_lot_size=1,
            cost_buffer_per_contract=fee,
        )
        def proposal(reader, *, symbol, from_utc, now, cost_per_contract):
            self.assertEqual(symbol, "USDRUBF")
            self.assertEqual(cost_per_contract, fee)
            return signal, entry, auth, reader.snapshot(now=now)
        with patch.object(worker, "propose_finam_m15_next_open", side_effect=proposal) as bridge:
            outcome = worker.run_candidate("v20-shallow", symbol="USDRUBF",
                                           cost_per_contract=fee)
        self.assertEqual(outcome["status"], "PASS_REFERENCE_CANDIDATE_ONLY_NO_ORDER")
        self.assertEqual(outcome["executable_stop"], "84.80")
        self.assertEqual(outcome["full_roundtrip_cost_per_contract_rub"], "8.34")
        self.assertGreater(outcome["quantity"], 0)
        self.assertLessEqual(Decimal(outcome["reserved_risk_rub"]), Decimal("675"))
        self.assertEqual(self.api.order_posts, 0)
        self.assertEqual(bridge.call_count, 1)

    def test_no_frozen_signal_is_normal_and_no_order(self):
        with patch.object(worker, "propose_finam_m15_next_open", return_value=None):
            outcome = worker.run_candidate("v20-shallow", symbol="USDRUBF",
                                           cost_per_contract=Decimal("8.34"))
        self.assertEqual(outcome["status"], "PASS_NO_FROZEN_SIGNAL_NO_ORDER")
        self.assertEqual(self.api.order_posts, 0)
        self.assertEqual(self.api.money_reads, 0)

    def test_bad_fee_or_symbol_is_rejected_before_broker(self):
        for symbol, fee in (("USDRUBF", "0"), ("USDRUBF", "NaN"),
                            ("BR", "8.34"), ("USDRUBF", "-1")):
            with self.subTest(symbol=symbol, fee=fee):
                with self.assertRaises(V20FinamBlocked):
                    worker.run_candidate("v20-shallow", symbol=symbol,
                                         cost_per_contract=fee)
        self.assertEqual(self.api.order_posts, 0)


if __name__ == "__main__":
    unittest.main()
