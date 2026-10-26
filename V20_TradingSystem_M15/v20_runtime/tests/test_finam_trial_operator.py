"""Only NEW offline 08.2 operator wiring tests. Broker network forbidden."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

from V20_TradingSystem_M15.v20_runtime import finam_trial_operator as operator
from V20_TradingSystem_M15.v20_runtime.finam_execution import V20FinamBlocked


UTC = datetime(2026, 10, 26, 7, 15, 5, tzinfo=timezone.utc)
ACCOUNT = "fake-unique-v20-trial"
HASH = hashlib.sha256(ACCOUNT.encode()).hexdigest()
SHA = "a" * 40


class TrialOperatorTests(unittest.TestCase):
    def test_no_signal_is_terminal_without_any_order_loop(self):
        hits = []
        def fake_cycle(sender, **kw):
            hits.append(kw["allow_new_entry"])
            return {"state": "NO_FROZEN_SIGNAL", "orders": 0}
        with patch.object(operator, "run_v20_single_trial_cycle", fake_cycle):
            state = operator.supervised_cycle(
                object(), symbol="USDRUBF", cost=Decimal("8.34"),
                mode="trial", sleep=lambda _: self.fail("unexpected wait"),
                now_utc=lambda: UTC,
            )
        self.assertEqual(state, "NO_FROZEN_SIGNAL")
        self.assertEqual(hits, [True])

    def test_entry_follow_stop_exit_never_rearms_new_entry(self):
        sequence = iter((
            "ENTRY_ACK_NEEDS_FILL_AND_STOP",
            "STOP_ACK_NEEDS_BROKER_PROOF",
            "STOP_NOW_BROKER_PROVEN",
            "BROKER_FLAT_NO_ACTIVE_STOP",
        ))
        flags = []
        waits = []
        def fake_cycle(sender, **kw):
            flags.append(kw["allow_new_entry"])
            return {"state": next(sequence), "orders": 0}
        with patch.object(operator, "run_v20_single_trial_cycle", fake_cycle):
            state = operator.supervised_cycle(
                object(), symbol="USDRUBF", cost=Decimal("8.34"),
                mode="trial", sleep=waits.append, now_utc=lambda: UTC,
            )
        self.assertEqual(state, "BROKER_FLAT_NO_ACTIVE_STOP")
        self.assertEqual(flags, [True, False, False, False])
        self.assertEqual(waits, [5, 5, 5])

    def test_restart_follow_must_never_allow_entry(self):
        flags = []
        def fake_cycle(sender, **kw):
            flags.append(kw["allow_new_entry"])
            return {"state": "STOP_EXIT_BROKER_FLAT_UNDER_ACCEPTANCE"}
        with patch.object(operator, "run_v20_single_trial_cycle", fake_cycle):
            state = operator.supervised_cycle(
                object(), symbol="USDRUBF", cost=Decimal("8.34"),
                mode="follow", sleep=lambda _: self.fail("unexpected wait"),
                now_utc=lambda: UTC,
            )
        self.assertEqual(state, "STOP_EXIT_BROKER_FLAT_UNDER_ACCEPTANCE")
        self.assertEqual(flags, [False])

    def test_missing_precise_permit_refuses_without_finam_network(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "v20lab"
            root.mkdir()
            env = {
                "V20_FINAM_ACCOUNT": ACCOUNT,
                "V20_FINAM_TOKEN": "test-opaque-only",
                "V20_FINAM_ACCOUNT_SHA256": HASH,
            }
            with patch.dict(os.environ, env), patch.object(
                operator.V20FinamReadAdapter, "authenticate",
                side_effect=AssertionError("broker must not be contacted"),
            ), patch.object(
                operator.V20FinamReadAdapter, "snapshot",
                side_effect=AssertionError("broker must not be contacted"),
            ):
                with self.assertRaisesRegex(
                    V20FinamBlocked, "TRIAL_OPERATOR_PERMIT_MISSING"
                ):
                    operator.run(
                        root=root, robot="v20-shallow", symbol="USDRUBF",
                        fee="8.34", source_sha=SHA, mode="trial",
                    )
            from TradingSystemLab.stage8_robot.trading_safety_gate import load_kill_switch
            switch, err = load_kill_switch(root / "robots" / "shallow")
            self.assertIsNone(err)
            self.assertEqual(switch["state"], "HALTED")


if __name__ == "__main__":
    unittest.main()
