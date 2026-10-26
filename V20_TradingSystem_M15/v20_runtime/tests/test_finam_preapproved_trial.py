"""V20-08.1: two synthetic no-POST tests of per-account trial intent handoff."""
from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

from TradingSystemLab.stage8_robot.execution_grid import initial_projection
from V20_TradingSystem_M15.v20_runtime.account_risk import AccountAuthority
from V20_TradingSystem_M15.v20_runtime.offline_planner import FrozenSignal, ProposedEntry
from V20_TradingSystem_M15.v20_runtime.finam_execution import (
    V20TradeJournal, V20FinamReadAdapter, V20FinamBlocked,
    V20SingleTradeTransport, prepare_finam_single_trial,
)
import V20_TradingSystem_M15.v20_runtime.finam_execution as execution
import test_finam_trial_transport as fixture


class PreapprovedIntentTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "v20lab"
        self.root.mkdir()
        self.api = fixture.FakeFinam()
        self.reader = V20FinamReadAdapter(
            api=self.api, robot_id=fixture.ROBOT, account_id=fixture.ACCOUNT,
            expected_account_hash=fixture.HASH,
        )
        self.reader.authenticate()

    def proposal(self):
        bar = datetime(2026, 10, 24, 10, 15)
        price, atr = Decimal("85.00"), Decimal("0.10")
        stop, distance = initial_projection("LONG", price, price-2*atr, Decimal("0.01"))
        signal = FrozenSignal("SHALLOW_PULLBACK", "USDRUBF", 1,
                              bar-timedelta(minutes=15), atr)
        entry = ProposedEntry("SHALLOW_PULLBACK", "USDRUBF", "LONG", bar,
                              price, stop, distance, 3, Decimal("675"),
                              Decimal("4500"), "SYNTHETIC")
        authority = AccountAuthority(
            fixture.ACCOUNT, Decimal("45000"), Decimal("45000"),
            Decimal("0.01"), Decimal("10"), Decimal("1500"), 1, Decimal("2"),
        )
        snap = self.reader.snapshot(now=fixture.OPEN_UTC)
        return signal, entry, authority, snap

    def prepare(self, journal):
        sender = V20SingleTradeTransport(
            journal=journal, reader=self.reader, accepted_commit=fixture.CODE_SHA,
            trial_permit_path=journal.instance_root/"safety"/"v20-single-trial-approval.json",
        )
        with patch.object(execution, "datetime", fixture.OfflineTestClock):
            with patch("TradingSystemLab.stage8_robot.trading_safety_gate.load_kill_switch",
                       return_value=({"state": "ARMED"}, None)):
                with patch.object(execution, "propose_finam_m15_next_open",
                                  return_value=self.proposal()):
                    return prepare_finam_single_trial(
                        sender, symbol="USDRUBF",
                        from_utc=fixture.OPEN_UTC-timedelta(hours=1),
                        now=fixture.OPEN_UTC, cost_per_contract=Decimal("2"),
                    )

    def test_no_specific_trial_approval_writes_no_h1_intent(self):
        with V20TradeJournal(self.root, fixture.ROBOT, fixture.ACCOUNT) as journal:
            with self.assertRaisesRegex(V20FinamBlocked, "SINGLE_TRIAL_EXPLICIT_AUTHORIZATION_MISSING"):
                self.prepare(journal)
            self.assertEqual(journal.store.all_intents(), [])
            self.assertEqual(self.api.order_posts, 0)
            self.assertEqual(self.api.stop_posts, 0)

    def test_specific_permit_caps_quantity_and_persists_without_fin_am_post(self):
        with V20TradeJournal(self.root, fixture.ROBOT, fixture.ACCOUNT) as journal:
            key = journal.preview_entry_key(self.proposal()[1])
            fixture.TrialBoundaryTests.approval(self, journal, key)
            result = self.prepare(journal)
            self.assertEqual(result["status"], "APPROVED_PREPARED_ONLY_NO_ORDER")
            self.assertEqual(result["entry_key"], key)
            self.assertEqual(result["quantity"], 1)
            self.assertLessEqual(Decimal(result["reserved_risk_rub"]), Decimal("675"))
            self.assertEqual(journal.store.intent(key)["status"], "INTENT_PERSISTED")
            self.assertEqual(journal.store.intent(key)["payload"]["quantity"], 1)
            self.assertEqual(self.api.order_posts, 0)
            with self.assertRaisesRegex(V20FinamBlocked, "TRIAL_PREPARER_EXISTING_INTENT_OR_HALT"):
                self.prepare(journal)
            self.assertEqual(self.api.order_posts, 0)


    def test_technical_single_contract_has_separate_h1_state_and_no_post(self):
        """One operator-approved technical entry never alters LIVE/frozen ledger."""
        from V20_TradingSystem_M15.v20_runtime.finam_trial_operator import TechnicalTrialJournal
        with TechnicalTrialJournal(self.root, fixture.ROBOT, fixture.ACCOUNT) as journal:
            key = journal.preview_entry_key(self.proposal()[1])
            fixture.TrialBoundaryTests.approval(self, journal, key)
            sender = V20SingleTradeTransport(
                journal=journal, reader=self.reader, accepted_commit=fixture.CODE_SHA,
                trial_permit_path=journal.instance_root/"safety"/"v20-single-trial-approval.json",
            )
            with patch.object(execution, "datetime", fixture.OfflineTestClock):
                with patch("TradingSystemLab.stage8_robot.trading_safety_gate.load_kill_switch",
                           return_value=({"state": "ARMED"}, None)):
                    with patch.object(execution, "propose_finam_m15_next_open",
                                      return_value=self.proposal()):
                        result = prepare_finam_single_trial(
                            sender, symbol="USDRUBF",
                            from_utc=fixture.OPEN_UTC-timedelta(hours=1),
                            now=fixture.OPEN_UTC, cost_per_contract=Decimal("2"),
                            technical_acceptance=True,
                        )
            self.assertEqual(result["quantity"], 1)
            self.assertEqual(journal.store.intent(key)["payload"]["quantity"], 1)
            marker = journal.store.get("technical_acceptance:" + key)
            self.assertEqual(marker["kind"], "TECHNICAL_ACCEPTANCE_NOT_FROZEN_SIGNAL")
            self.assertEqual(marker["max_quantity"], 1)
            self.assertLessEqual(Decimal(marker["reserved_risk_rub"]), Decimal("675"))
            self.assertEqual(self.api.order_posts, 0)
            self.assertEqual(self.api.stop_posts, 0)
        self.assertFalse((self.root/"robots"/"shallow"/"state"/"v20-real-intents.sqlite3").exists())


    def test_technical_one_shot_posts_only_on_fresh_pretrade_not_old_m15_open(self):
        """Fake FINAM: a 15-minute old M15 reference is not a delayed live signal."""
        import json
        from V20_TradingSystem_M15.v20_runtime.finam_trial_operator import TechnicalTrialJournal
        old_signal, old_entry, authority, snap = self.proposal()
        from dataclasses import replace
        old_bar = old_entry.entry_bar_open-timedelta(minutes=15)
        signal = replace(old_signal, signal_bar_open=old_bar-timedelta(minutes=15))
        entry = replace(old_entry, entry_bar_open=old_bar, quantity=1)
        with TechnicalTrialJournal(self.root, fixture.ROBOT, fixture.ACCOUNT) as journal:
            with patch.object(execution, "datetime", fixture.OfflineTestClock):
                key = journal.prepare_entry(signal=signal, entry=entry,
                                            authority=authority, snapshot=snap)
                journal.store.put("technical_acceptance:" + key, {
                    "kind": "TECHNICAL_ACCEPTANCE_NOT_FROZEN_SIGNAL",
                    "robot_id": fixture.ROBOT, "account_sha256": fixture.HASH,
                    "symbol": "USDRUBF", "direction": "LONG", "max_quantity": 1,
                    "prepared_at_utc": fixture.OPEN_UTC.isoformat(),
                })
                permit_path = fixture.TrialBoundaryTests.approval(self, journal, key)
                record = json.loads(permit_path.read_text(encoding="utf-8"))
                record["trial_kind"] = "TECHNICAL_ACCEPTANCE_NOT_STRATEGY_SIGNAL"
                record["authorized_operations"] = ["ENTRY", "PROTECTIVE_STOP"]
                permit_path.write_text(json.dumps(record), encoding="utf-8")
                sender = V20SingleTradeTransport(
                    journal=journal, reader=self.reader, accepted_commit=fixture.CODE_SHA,
                    trial_permit_path=permit_path,
                )
                with patch("TradingSystemLab.stage8_robot.trading_safety_gate.load_kill_switch",
                           return_value=({"state": "ARMED"}, None)):
                    sender.submit_entry_once(key=key, snapshot=snap, now=fixture.OPEN_UTC)
                self.assertEqual(self.api.order_posts, 1)
                with self.assertRaises(V20FinamBlocked):
                    sender.submit_entry_once(key=key, snapshot=snap, now=fixture.OPEN_UTC)
                self.assertEqual(self.api.order_posts, 1)


    def _technical_prepost(self, journal):
        """Existing FakeFinam/H1 journal, one on-grid contract, no POST."""
        import json
        from dataclasses import replace
        from V20_TradingSystem_M15.v20_runtime.finam_trial_operator import (
            TechnicalTrialJournal,
        )
        signal, entry, authority, snap = self.proposal()
        entry = replace(entry, quantity=1)
        with patch.object(execution, "datetime", fixture.OfflineTestClock):
            key = journal.prepare_entry(
                signal=signal, entry=entry, authority=authority, snapshot=snap,
            )
        permit = fixture.TrialBoundaryTests.approval(self, journal, key)
        body = json.loads(permit.read_text(encoding="utf-8"))
        body["trial_kind"] = "TECHNICAL_ACCEPTANCE_NOT_STRATEGY_SIGNAL"
        body["authorized_operations"] = ["ENTRY", "PROTECTIVE_STOP"]
        permit.write_text(json.dumps(body), encoding="utf-8")
        journal.store.put("technical_acceptance:" + key, {
            "kind": "TECHNICAL_ACCEPTANCE_NOT_FROZEN_SIGNAL",
            "account_sha256": fixture.HASH, "robot_id": fixture.ROBOT,
            "symbol": "USDRUBF", "direction": "LONG", "max_quantity": 1,
            "prepared_at_utc": fixture.OPEN_UTC.isoformat(),
        })
        sender = V20SingleTradeTransport(
            journal=journal, reader=self.reader, accepted_commit=fixture.CODE_SHA,
            trial_permit_path=permit,
        )
        return key, sender, snap, permit

    def test_technical_current_clock_not_earlier_cycle_clock(self):
        from V20_TradingSystem_M15.v20_runtime.finam_trial_operator import TechnicalTrialJournal
        with TechnicalTrialJournal(self.root, fixture.ROBOT, fixture.ACCOUNT) as journal:
            key, sender, snap, _ = self._technical_prepost(journal)
            journal.store.put("technical_acceptance:" + key, {
                **journal.store.get("technical_acceptance:" + key),
                "prepared_at_utc": (fixture.OPEN_UTC + timedelta(seconds=5)).isoformat(),
            })
            class LaterClock(datetime):
                @classmethod
                def now(cls, tz=None):
                    return fixture.OPEN_UTC + timedelta(seconds=7)
            with patch.object(execution, "datetime", LaterClock):
                with patch("TradingSystemLab.stage8_robot.trading_safety_gate.load_kill_switch",
                           return_value=({"state": "ARMED"}, None)):
                    sender.submit_entry_once(
                        key=key, snapshot=snap, now=fixture.OPEN_UTC,
                    )
            self.assertEqual(self.api.order_posts, 1)
            self.assertEqual(journal.store.intent(key)["status"], "ACK")
            record = journal.store.get("entry_submission:" + key)
            self.assertIsNotNone(record)
            self.assertEqual(record["account_sha256"], fixture.HASH)

    def test_recover_only_unsubmitted_technical_intent_after_broker_flat(self):
        from V20_TradingSystem_M15.v20_runtime.finam_trial_operator import (
            TechnicalTrialJournal, recover_unsubmitted_technical,
        )
        from TradingSystemLab.stage8_robot.trading_safety_gate import write_kill_switch
        with TechnicalTrialJournal(self.root, fixture.ROBOT, fixture.ACCOUNT) as journal:
            key, sender, snap, permit = self._technical_prepost(journal)
            write_kill_switch(journal.instance_root, "HALTED")
            done = recover_unsubmitted_technical(
                journal=journal, reader=self.reader, sender=sender, permit=permit,
                robot=fixture.ROBOT, symbol="USDRUBF",
            )
            self.assertEqual(
                done, "PASS_PREPOST_ONLY_FINAM_TWICE_FLAT_NEW_ENTRY_STILL_OFF",
            )
            self.assertEqual(journal.store.all_intents(), [])
            self.assertEqual(journal.store.get("risk_reservations"), {})
            self.assertEqual(journal.store.get("session_entries"), {})
            self.assertEqual(
                journal.store.get("technical_unposted_aborts")[0]["entry_key"], key,
            )
            self.assertFalse(permit.exists())
            self.assertEqual(self.api.order_posts, 0)
            self.assertEqual(self.api.stop_posts, 0)

    def test_recovery_refuses_if_post_checkpoint_present(self):
        from V20_TradingSystem_M15.v20_runtime.finam_trial_operator import (
            TechnicalTrialJournal, recover_unsubmitted_technical,
        )
        from TradingSystemLab.stage8_robot.trading_safety_gate import write_kill_switch
        with TechnicalTrialJournal(self.root, fixture.ROBOT, fixture.ACCOUNT) as journal:
            key, sender, snap, permit = self._technical_prepost(journal)
            write_kill_switch(journal.instance_root, "HALTED")
            journal.store.put("entry_submission:" + key, {
                "submitted_at": fixture.OPEN_UTC.isoformat(),
                "account_sha256": fixture.HASH,
            })
            with self.assertRaisesRegex(
                V20FinamBlocked, "TECHNICAL_RECOVERY_POST_OR_STATE_UNCERTAIN",
            ):
                recover_unsubmitted_technical(
                    journal=journal, reader=self.reader, sender=sender, permit=permit,
                    robot=fixture.ROBOT, symbol="USDRUBF",
                )
            self.assertTrue(permit.is_file())
            self.assertEqual(len(journal.store.all_intents()), 1)
            self.assertEqual(self.api.order_posts, 0)


if __name__ == "__main__":
    unittest.main()
