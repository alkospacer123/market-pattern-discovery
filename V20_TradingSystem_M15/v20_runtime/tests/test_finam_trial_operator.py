"""Only NEW offline 08.2 operator wiring tests. Broker network forbidden."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import os
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch
from types import SimpleNamespace
import unittest

from V20_TradingSystem_M15.v20_runtime import finam_trial_operator as operator
import V20_TradingSystem_M15.v20_runtime.finam_execution as execution
from V20_TradingSystem_M15.v20_runtime.finam_execution import V20FinamBlocked, V20SingleTradeTransport
from TradingSystemLab.stage8_robot.execution_grid import initial_projection
from V20_TradingSystem_M15.v20_runtime.offline_planner import FrozenSignal, ProposedEntry
from V20_TradingSystem_M15.v20_runtime.account_risk import AccountAuthority


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

    def test_actual_clock_elapsed_rejects_delayed_market_post(self):
        # The earlier M15 snapshot is fresh at 10:15:05, but several broker
        # reads may delay the irreversible POST beyond the allowed 60 seconds.
        class LateClock(datetime):
            @classmethod
            def now(cls, tz=None):
                return datetime(2026, 10, 26, 7, 17, tzinfo=timezone.utc)
        never_post = Mock(side_effect=AssertionError("market order MUST NOT POST"))
        sender = object.__new__(V20SingleTradeTransport)
        sender.journal = SimpleNamespace(instance_root=Path("/fake-v20lab/robots/shallow"))
        sender.reader = SimpleNamespace(
            account_id=ACCOUNT, api=SimpleNamespace(place_order=never_post)
        )
        with patch.object(
            sender, "_entry", return_value={"entry_at": "2026-10-26T10:15:00"}
        ), patch.object(
            execution, "datetime", LateClock
        ), patch(
            "TradingSystemLab.stage8_robot.trading_safety_gate.load_kill_switch",
            return_value=({"state": "ARMED"}, None)
        ):
            with self.assertRaisesRegex(
                V20FinamBlocked, "TRIAL_ENTRY_ACTUAL_NEXT_OPEN_EXPIRED"
            ):
                sender.submit_entry_once(
                    key="fake", snapshot=None,
                    now=datetime(2026, 10, 26, 7, 15, 5, tzinfo=timezone.utc),
                )
        never_post.assert_not_called()

    def test_advance_owner_scope_becomes_exact_h1_first_entry_only(self):
        with TemporaryDirectory() as tmp:
            safety = Path(tmp) / "safety"
            safety.mkdir()
            grant = safety / "v20-first-signal-approval.json"
            permit = safety / "v20-single-trial-approval.json"
            grant.write_text(json.dumps({
                "schema": "v20.08.2.first_signal_approval.v1",
                "scope": "ONE_FIRST_REAL_FROZEN_TRIAL_ONLY",
                "robot_id": "v20-shallow",
                "account_sha256": HASH,
                "source_commit": SHA,
                "instrument": "USDRUBF",
                "max_risk_fraction": "0.015",
                "explicit_owner_approval": True,
            }), encoding="utf-8")
            cb = operator.create_exact_permit_on_signal(
                authorized_path=grant, permit_path=permit,
                robot="v20-shallow", account_hash=HASH,
                symbol="USDRUBF", source_sha=SHA,
            )
            bar = datetime(2026, 10, 26, 10, 15)
            price, atr = Decimal("85"), Decimal("0.10")
            stop, distance = initial_projection(
                "LONG", price, price-2*atr, Decimal("0.01")
            )
            signal = FrozenSignal(
                "SHALLOW_PULLBACK", "USDRUBF", 1,
                datetime(2026, 10, 26, 10, 0), atr,
            )
            entry = ProposedEntry(
                "SHALLOW_PULLBACK", "USDRUBF", "LONG", bar,
                price, stop, distance, 3, Decimal("675"),
                Decimal("4500"), "OFFLINE_REFERENCE_NOT_ORDER",
            )
            authority = AccountAuthority(
                ACCOUNT, Decimal("45000"), Decimal("45000"),
                Decimal("0.01"), Decimal("10"), Decimal("1500"),
                1, Decimal("8.34"),
            )
            cb("v20:v20-shallow:test-specific-frozen-key", signal, entry, authority)
            exact = json.loads(permit.read_text(encoding="utf-8"))
            self.assertEqual(exact["direction"], "LONG")
            self.assertEqual(exact["instrument"], "USDRUBF")
            self.assertEqual(exact["max_risk_rub"], "675.000")
            self.assertEqual(exact["max_quantity"], 3)
            self.assertEqual(exact["entry_key"], "v20:v20-shallow:test-specific-frozen-key")
            self.assertEqual(
                exact["authorized_operations"],
                ["ENTRY", "PROTECTIVE_STOP", "FROZEN_EXIT"],
            )
            with self.assertRaisesRegex(
                V20FinamBlocked, "TRIAL_EXACT_PERMIT_ALREADY_EXISTS"
            ):
                cb("v20:v20-shallow:second-key", signal, entry, authority)
            self.assertEqual(json.loads(permit.read_text(encoding="utf-8")), exact)

    def test_advance_owner_scope_refuses_wrong_robot_or_instrument(self):
        with TemporaryDirectory() as tmp:
            grant = Path(tmp) / "approved.json"
            grant.write_text(json.dumps({
                "schema": "v20.08.2.first_signal_approval.v1",
                "scope": "ONE_FIRST_REAL_FROZEN_TRIAL_ONLY",
                "robot_id": "v20-obv",
                "account_sha256": HASH,
                "source_commit": SHA,
                "instrument": "USDRUBF",
                "max_risk_fraction": "0.015",
                "explicit_owner_approval": True,
            }), encoding="utf-8")
            with self.assertRaisesRegex(
                V20FinamBlocked, "TRIAL_ADVANCE_APPROVAL_SCOPE_INVALID"
            ):
                operator.advance_authorization(
                    grant, robot="v20-shallow", account_hash=HASH,
                    symbol="USDRUBF", source_sha=SHA,
                )

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
