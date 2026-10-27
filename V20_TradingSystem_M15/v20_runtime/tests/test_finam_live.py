"""08.4 new-only checks; never contact FINAM or enable Windows Tasks."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
import hashlib
import json
import unittest
from contextlib import ExitStack
from datetime import datetime, timezone

from TradingSystemLab.stage8_robot.finam_api import (
    FinamServerError, FinamTimeout, FinamRateLimit, FinamUncertainSubmission,
)
from V20_TradingSystem_M15.v20_runtime.finam_live import (
    AUTH_SCHEMA, SYMBOLS, _safe_auth, _ownership, run_cycle, V20FinamBlocked,
)


class StubStore:
    def __init__(self, rows=()):
        self.rows = list(rows)
        self.intents = {}
        self.values = {}

    def all_intents(self):
        return self.rows

    def intent(self, key):
        return self.intents.get(key)

    def get(self, key, default=None):
        return self.values.get(key, default)

    def put(self, key, value):
        self.values[key] = value


class LiveAdmissionTests(unittest.TestCase):
    def fake_journal(self, root: Path):
        return SimpleNamespace(
            instance_root=root, robot_id="v20-shallow",
            account_hash=hashlib.sha256(b"v20-test-account").hexdigest(),
            store=StubStore(),
        )

    def valid_auth(self, journal, source):
        return {
            "schema": AUTH_SCHEMA, "robot_id": journal.robot_id,
            "account_sha256": journal.account_hash, "source_commit": source,
            "owner_approved": True, "execution_mode": "V20_FROZEN_M15_LIVE",
            "risk_fraction": "0.015", "initial_stop_atr": "2",
            "signals": "FROZEN_COMPLETED_M15_NEXT_OPEN",
            "symbols": list(SYMBOLS),
            "roundtrip_cost_rub": {
                "USDRUBF": "8.34", "CNYRUBF": "2.02",
                "GLDRUBF": "3.64", "IMOEXF": "4.16",
            },
        }

    def test_exact_owner_account_source_and_costs_mandatory(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            safe = root / "safety"
            safe.mkdir()
            journal = self.fake_journal(root)
            path = safe / "v20-live-authorization.json"
            source = "0" * 40
            record = self.valid_auth(journal, source)
            path.write_text(json.dumps(record), encoding="utf-8")
            self.assertEqual(_safe_auth(path, journal=journal, source=source), record)
            for key, value in (("owner_approved", False),
                               ("account_sha256", "0"*64),
                               ("risk_fraction", "0.02"),
                               ("source_commit", "1"*40)):
                invalid = dict(record, **{key: value})
                path.write_text(json.dumps(invalid), encoding="utf-8")
                with self.assertRaises(V20FinamBlocked):
                    _safe_auth(path, journal=journal, source=source)
            record["roundtrip_cost_rub"]["CNYRUBF"] = "0"
            path.write_text(json.dumps(record), encoding="utf-8")
            with self.assertRaisesRegex(V20FinamBlocked, "V20_LIVE_COST_INVALID"):
                _safe_auth(path, journal=journal, source=source)

    def test_no_auth_file_means_no_live(self):
        with TemporaryDirectory() as tmp:
            journal = self.fake_journal(Path(tmp))
            with self.assertRaisesRegex(V20FinamBlocked, "V20_LIVE_AUTH_FILE_REQUIRED"):
                _safe_auth(journal.instance_root/"safety"/"v20-live-authorization.json",
                           journal=journal, source="0"*40)

    def test_foreign_position_fails_before_new_entry(self):
        with TemporaryDirectory() as tmp:
            journal = self.fake_journal(Path(tmp))
            snapshot = SimpleNamespace(positions={"FUTCNYRUBF": 1}, orders=[])
            with self.assertRaisesRegex(V20FinamBlocked, "UNOWNED_BROKER_POSITION"):
                _ownership(journal, snapshot)

    def test_account_intents_must_not_share_same_instrument(self):
        with TemporaryDirectory() as tmp:
            journal = self.fake_journal(Path(tmp))
            key0, key1 = "entry-one", "entry-two"
            payload = {"kind": "ENTRY", "mode": "PRETRADE_NOT_AUTHORIZED",
                       "robot_id": "v20-shallow",
                       "account_sha256": journal.account_hash,
                       "symbol": "CNYRUBF", "finam_symbol": "FUTCNYRUBF",
                       "direction": "LONG", "quantity": 1}
            journal.store.rows = [
                {"idempotency_key": key, "payload": payload}
                for key in (key0, key1)
            ]
            with patch("V20_TradingSystem_M15.v20_runtime.finam_live._load_registry",
                       return_value={"CNYRUBF": {"finam_symbol": "FUTCNYRUBF"}}):
                with self.assertRaisesRegex(V20FinamBlocked, "TWO_POSITIONS"):
                    _ownership(journal, SimpleNamespace(positions={}, orders=[]))

    def test_halt_means_no_entry_even_at_m15_open(self):
        with TemporaryDirectory() as tmp:
            journal = self.fake_journal(Path(tmp))
            reader = SimpleNamespace(snapshot=lambda **k: SimpleNamespace(positions={}, orders=[]))
            sender = SimpleNamespace(journal=journal, reader=reader,
                                     auth_path=Path(tmp)/"none", source="0"*40)
            now = datetime(2026, 10, 26, 7, 0, 10, tzinfo=timezone.utc)
            with ExitStack() as stack:
                stack.enter_context(patch("V20_TradingSystem_M15.v20_runtime.finam_live._safe_auth"))
                stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live._follow_existing",
                    return_value="BROKER_RECONCILED_PROTECTION_PASS"))
                stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live.load_kill_switch",
                    return_value=({"state": "HALTED"}, None)))
                propose = stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live.propose_finam_m15_next_open"))
                self.assertEqual(run_cycle(sender, now), "HALTED_NO_NEW_ENTRIES")
                propose.assert_not_called()

    def test_no_signal_claimed_once_per_bar_in_original_symbol_order(self):
        with TemporaryDirectory() as tmp:
            journal = self.fake_journal(Path(tmp))
            reader = SimpleNamespace(snapshot=lambda **k: SimpleNamespace(positions={}, orders=[]))
            auth = {"roundtrip_cost_rub": {x: "2.02" for x in SYMBOLS}}
            sender = SimpleNamespace(journal=journal, reader=reader, auth=auth,
                                     auth_path=Path(tmp)/"none", source="0"*40)
            now = datetime(2026, 10, 26, 7, 0, 10, tzinfo=timezone.utc)
            with ExitStack() as stack:
                stack.enter_context(patch("V20_TradingSystem_M15.v20_runtime.finam_live._safe_auth"))
                stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live._follow_existing",
                    return_value="BROKER_RECONCILED_PROTECTION_PASS"))
                stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live.load_kill_switch",
                    return_value=({"state": "ARMED"}, None)))
                propose = stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live.propose_finam_m15_next_open",
                    return_value=None))
                self.assertEqual(run_cycle(sender, now), "NO_FROZEN_SIGNAL")
                self.assertEqual([c.kwargs["symbol"] for c in propose.call_args_list],
                                 sorted(SYMBOLS))
                self.assertEqual(run_cycle(sender, now), "NO_FROZEN_SIGNAL")
                self.assertEqual(propose.call_count, 4)

    def test_transient_broker_get_failures_never_submit_and_do_not_halt(self):
        for error in (FinamServerError("HTTP_503:account"),
                      FinamTimeout("account"), FinamRateLimit("orders")):
            with self.subTest(type=type(error).__name__), TemporaryDirectory() as tmp:
                journal = self.fake_journal(Path(tmp))
                sender = SimpleNamespace(
                    journal=journal, reader=SimpleNamespace(snapshot=lambda **k: (_ for _ in ()).throw(error)),
                    auth_path=Path(tmp)/"none", source="0"*40)
                now = datetime(2026, 10, 27, 2, 0, 10, tzinfo=timezone.utc)
                with patch("V20_TradingSystem_M15.v20_runtime.finam_live._safe_auth"), patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live._follow_existing"
                ) as follow:
                    self.assertEqual(run_cycle(sender, now),
                                     "FINAM_READ_TEMPORARILY_UNAVAILABLE_NO_NEW_ENTRIES")
                    follow.assert_not_called()
                    self.assertEqual(journal.store.values, {})

    def test_transient_m15_signal_get_failure_skips_boundary_without_entry(self):
        with TemporaryDirectory() as tmp:
            journal = self.fake_journal(Path(tmp))
            reader = SimpleNamespace(snapshot=lambda **k: SimpleNamespace(positions={}, orders=[]))
            sender = SimpleNamespace(journal=journal, reader=reader,
                                     auth={"roundtrip_cost_rub": {x: "2.02" for x in SYMBOLS}},
                                     auth_path=Path(tmp)/"none", source="0"*40)
            now = datetime(2026, 10, 27, 2, 0, 10, tzinfo=timezone.utc)
            with ExitStack() as stack:
                stack.enter_context(patch("V20_TradingSystem_M15.v20_runtime.finam_live._safe_auth"))
                stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live._follow_existing",
                    return_value="BROKER_RECONCILED_PROTECTION_PASS"))
                stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live.load_kill_switch",
                    return_value=({"state": "ARMED"}, None)))
                proposer = stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live.propose_finam_m15_next_open",
                    side_effect=FinamServerError("HTTP_503:bars")))
                self.assertEqual(run_cycle(sender, now),
                                 "FINAM_M15_READ_UNAVAILABLE_NO_NEW_ENTRIES")
                self.assertEqual(proposer.call_count, 1)
                self.assertEqual(journal.store.values, {})

    def test_order_post_uncertainty_and_broker_invariants_are_not_swallowed(self):
        with TemporaryDirectory() as tmp:
            journal = self.fake_journal(Path(tmp))
            sender = SimpleNamespace(
                journal=journal,
                reader=SimpleNamespace(snapshot=lambda **k: (_ for _ in ()).throw(
                    FinamUncertainSubmission("RECONCILIATION_REQUIRED"))),
                auth_path=Path(tmp)/"none", source="0"*40)
            with patch("V20_TradingSystem_M15.v20_runtime.finam_live._safe_auth"):
                with self.assertRaises(FinamUncertainSubmission):
                    run_cycle(sender, datetime(2026, 10, 27, 2, 0, 10, tzinfo=timezone.utc))

    def test_foreign_active_order_is_refused(self):
        with TemporaryDirectory() as tmp:
            journal = self.fake_journal(Path(tmp))
            order = SimpleNamespace(active=True, client_order_id="unknown",
                                    symbol="FUTCNYRUBF", kind="REGULAR")
            with self.assertRaisesRegex(V20FinamBlocked, "FOREIGN_OR_DUPLICATE_ACTIVE"):
                _ownership(journal, SimpleNamespace(positions={}, orders=[order]))


if __name__ == "__main__":
    unittest.main()
