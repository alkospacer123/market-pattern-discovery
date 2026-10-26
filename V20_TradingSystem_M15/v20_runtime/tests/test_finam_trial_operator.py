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
from TradingSystemLab.stage8_robot.broker import compact_client_order_id
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

    def test_technical_trial_reuses_one_entry_then_follow_only(self):
        states = iter((
            "ENTRY_ACK_NEEDS_FILL_AND_STOP",
            "STOP_NOW_BROKER_PROVEN",
            "TECHNICAL_SLTP_CONFIRMED_AWAIT_MANUAL_CLOSE",
            "MANUAL_EXIT_BROKER_FLAT_UNDER_ACCEPTANCE",
        ))
        flags = []
        def fake_cycle(sender, **kw):
            flags.append((kw["allow_new_entry"], kw["technical_acceptance"]))
            return {"state": next(states), "orders": 0}
        with patch.object(operator, "run_v20_single_trial_cycle", fake_cycle):
            outcome = operator.supervised_cycle(
                object(), symbol="CNYRUBF", cost=Decimal("2.02"),
                mode="technical", sleep=lambda _: None, now_utc=lambda: UTC,
            )
        self.assertEqual(outcome, "MANUAL_EXIT_BROKER_FLAT_UNDER_ACCEPTANCE")
        self.assertEqual(flags, [(True, True), (False, True), (False, True), (False, True)])

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

    def test_owner_approved_first_signal_waits_for_next_real_bar_without_reentry(self):
        # Existing no-signal result is not a synthetic trade or a reason
        # to consume the owner-approved one-time entry.
        from datetime import timedelta
        base = datetime(2026, 10, 26, 7, 15, 8, tzinfo=timezone.utc)
        stamps = iter((base, base, base+timedelta(minutes=15),
                       base+timedelta(minutes=15, seconds=1)))
        outcomes = iter((
            {"state":"NO_FROZEN_SIGNAL", "orders":0},
            {"state":"ENTRY_ACK_NEEDS_FILL_AND_STOP", "orders":1},
            {"state":"BROKER_FLAT_NO_ACTIVE_STOP", "orders":0},
        ))
        flags=[]
        waits=[]
        def fake(sender,**kw):
            flags.append((kw["allow_new_entry"],kw["permit_on_signal"]))
            return next(outcomes)
        token=lambda *a: None
        with patch.object(operator,"run_v20_single_trial_cycle",fake):
            final=operator.supervised_cycle(
                object(),symbol="USDRUBF",cost=Decimal("8.34"),
                mode="trial",sleep=waits.append,
                now_utc=lambda: next(stamps),
                permit_on_signal=token,wait_for_signal=True,
            )
        self.assertEqual(final,"BROKER_FLAT_NO_ACTIVE_STOP")
        self.assertEqual(flags,[(True,token),(True,token),(False,None)])
        self.assertEqual(waits,[900,5])

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

    def test_technical_grant_creates_one_contract_stop_only_permit(self):
        with TemporaryDirectory() as tmp:
            safety = Path(tmp) / "safety"
            safety.mkdir()
            grant = safety / "v20-first-signal-approval.json"
            permit = safety / "v20-single-trial-approval.json"
            grant.write_text(json.dumps({
                "schema": "v20.08.2.first_signal_approval.v1",
                "scope": "ONE_FIRST_REAL_FROZEN_TRIAL_ONLY",
                "robot_id": "v20-shallow", "account_sha256": HASH,
                "source_commit": SHA, "instrument": "CNYRUBF",
                "max_risk_fraction": "0.015", "explicit_owner_approval": True,
            }), encoding="utf-8")
            cb = operator.create_exact_permit_on_signal(
                authorized_path=grant, permit_path=permit,
                robot="v20-shallow", account_hash=HASH,
                symbol="CNYRUBF", source_sha=SHA, technical_acceptance=True,
            )
            at = datetime(2026, 10, 26, 10, 15)
            signal = FrozenSignal("SHALLOW_PULLBACK", "CNYRUBF", 1,
                                  datetime(2026, 10, 26, 10, 0), Decimal("0.01"))
            entry = ProposedEntry("SHALLOW_PULLBACK", "CNYRUBF", "LONG", at,
                                  Decimal("12.50"), Decimal("12.48"), Decimal("0.02"),
                                  1, Decimal("675"), Decimal("1500"),
                                  "TECHNICAL_NOT_STRATEGY_SIGNAL")
            authority = AccountAuthority(ACCOUNT, Decimal("45000"), Decimal("45000"),
                                         Decimal("0.01"), Decimal("10"),
                                         Decimal("1500"), 1, Decimal("2.02"))
            cb("v20:v20-shallow:technical-one-contract", signal, entry, authority)
            exact = json.loads(permit.read_text(encoding="utf-8"))
            self.assertEqual(exact["trial_kind"], "TECHNICAL_ACCEPTANCE_NOT_STRATEGY_SIGNAL")
            self.assertEqual(exact["max_quantity"], 1)
            self.assertEqual(exact["authorized_operations"], ["ENTRY", "PROTECTIVE_STOP"])
            with self.assertRaisesRegex(V20FinamBlocked, "TRIAL_EXACT_PERMIT_ALREADY_EXISTS"):
                cb("v20:v20-shallow:another", signal, entry, authority)

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


    def _create_real_ack_shallow_fixture(self, root, *, checkpoint=True):
        """H1-owned first technical SQLite: ACKed POST, no SLTP, no fake broker POST."""
        with operator.TechnicalTrialJournal(root, "v20-shallow", ACCOUNT) as old:
            key = "v20:v20-shallow:" + HASH[:16] + ":first-real-broker-ack"
            payload = {
                "kind": "ENTRY", "robot_id": "v20-shallow",
                "account_sha256": HASH, "symbol": "CNYRUBF",
                "direction": "LONG", "quantity": 1,
            }
            self.assertTrue(old.store.persist_intent(key, payload))
            old.store.transition_intent(key, "ACK", "old-broker-entry-1")
            old.store.put("trial_authority_consumed", key)
            old.store.put("execution_halt", "BROKER_ORDER_MISMATCH")
            if checkpoint:
                old.store.put("entry_submission:" + key, {
                    "account_sha256": HASH,
                    "submitted_at": UTC.isoformat(),
                })
            safety = old.instance_root / "safety"
            safety.mkdir(parents=True, exist_ok=True)
            (safety / "v20-single-trial-approval.json").write_text(
                json.dumps({
                    "schema": "v20.08.2.single_trial.v1",
                    "scope": "ONE_SPECIFIC_APPROVED_TRIAL",
                    "source_commit": SHA,
                    "robot_id": "v20-shallow",
                    "account_sha256": HASH,
                    "entry_key": key,
                    "instrument": "CNYRUBF",
                    "direction": "LONG",
                    "max_quantity": 1,
                    "trial_kind": "TECHNICAL_ACCEPTANCE_NOT_STRATEGY_SIGNAL",
                }), encoding="utf-8",
            )
            return key, old.state_path

    def test_shallow_retest_proves_original_real_post_without_modifying_it(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "v20lab"
            root.mkdir()
            key, original_path = self._create_real_ack_shallow_fixture(root)
            before = original_path.read_bytes()
            broker = SimpleNamespace(
                authenticate=Mock(),
                snapshot=Mock(return_value=SimpleNamespace(clean=True, orders=())),
            )
            with operator.ShallowStopRetestJournal(root, "v20-shallow", ACCOUNT) as retest:
                with patch.object(operator, "load_kill_switch",
                                  return_value=({"state": "HALTED"}, None)):
                    outcome = operator.prove_shallow_prior_post_and_flat(
                        journal=retest, reader=broker,
                        source_sha=SHA, symbol="CNYRUBF",
                    )
                self.assertEqual(outcome, "PASS_PRIOR_REAL_POST_PRESERVED_BROKER_FLAT")
                self.assertEqual(
                    retest.store.get("shallow_previous_client_order_id"),
                    compact_client_order_id(key),
                )
                self.assertEqual(retest.store.all_intents(), [])
                broker.authenticate.assert_called_once()
                broker.snapshot.assert_called_once()
            self.assertEqual(original_path.read_bytes(), before)
            with operator.TechnicalTrialJournal(root, "v20-shallow", ACCOUNT) as original:
                self.assertEqual(original.store.intent(key)["status"], "ACK")
                self.assertEqual(original.store.get("trial_authority_consumed"), key)

    def test_shallow_retest_rejects_missing_original_post_proof(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "v20lab"
            root.mkdir()
            key, old = self._create_real_ack_shallow_fixture(root, checkpoint=False)
            broker = SimpleNamespace(authenticate=Mock(), snapshot=Mock())
            with operator.ShallowStopRetestJournal(root, "v20-shallow", ACCOUNT) as retest:
                with patch.object(operator, "load_kill_switch",
                                  return_value=({"state": "HALTED"}, None)):
                    with self.assertRaisesRegex(
                        V20FinamBlocked, "SHALLOW_RETEST_PRIOR_BROKER_POST_INVALID",
                    ):
                        operator.prove_shallow_prior_post_and_flat(
                            journal=retest, reader=broker,
                            source_sha=SHA, symbol="CNYRUBF",
                        )
                self.assertIsNone(retest.store.get("shallow_previous_client_order_id"))
                self.assertEqual(retest.store.all_intents(), [])
            broker.authenticate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
