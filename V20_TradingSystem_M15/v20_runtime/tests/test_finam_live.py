"""08.4 new-only checks; never contact FINAM or enable Windows Tasks."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
import hashlib
import json
import unittest
from contextlib import ExitStack, nullcontext
from datetime import datetime, timezone

from TradingSystemLab.stage8_robot.finam_api import (
    FinamError, FinamNotFound, FinamServerError, FinamTimeout, FinamRateLimit, FinamUncertainSubmission,
)
from V20_TradingSystem_M15.v20_runtime.finam_live import (
    AUTH_SCHEMA, SYMBOLS, _safe_auth, _ownership, run_cycle, run, V20FinamBlocked,
    V20FinamSnapshotReadRetry,
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
            now = datetime(2026, 10, 26, 7, 15, 10, tzinfo=timezone.utc)
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

    def test_afterhours_m15_poll_is_skipped_but_broker_reconcile_runs(self):
        # Frozen signals: bar Open 10:00..17:00, NEXT_OPEN 10:15..17:15.
        # No strategy M15 history fetch after hours; broker protection stays active.
        with TemporaryDirectory() as tmp:
            journal = self.fake_journal(Path(tmp))
            read_calls = []
            reader = SimpleNamespace(snapshot=lambda **k: read_calls.append(k) or
                                     SimpleNamespace(positions={}, orders=[]))
            sender = SimpleNamespace(journal=journal, reader=reader,
                                     auth={"roundtrip_cost_rub": {x: "2.02" for x in SYMBOLS}},
                                     auth_path=Path(tmp)/"none", source="0"*40)
            with ExitStack() as stack:
                stack.enter_context(patch("V20_TradingSystem_M15.v20_runtime.finam_live._safe_auth"))
                follow = stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live._follow_existing",
                    return_value="BROKER_RECONCILED_PROTECTION_PASS"))
                stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live.load_kill_switch",
                    return_value=({"state": "ARMED"}, None)))
                proposer = stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live.propose_finam_m15_next_open",
                    side_effect=V20FinamBlocked("M15_FINAM_TIMESTAMP_OUT_OF_RANGE")))
                # MSK: 09:45, 17:30, 19:15 — no frozen entry can be opened.
                for utc_hour, utc_minute in ((6, 45), (14, 30), (16, 15)):
                    now = datetime(2026, 10, 28, utc_hour, utc_minute, 7,
                                   tzinfo=timezone.utc)
                    self.assertEqual(run_cycle(sender, now), "WAIT_NEXT_M15_OPEN")
                self.assertEqual(follow.call_count, 3)
                self.assertEqual(len(read_calls), 3)
                proposer.assert_not_called()
                self.assertEqual(journal.store.values, {})
                # Inside the entry window the raw validation remains strict,
                # but LIVE must skip the whole unsafe entry attempt, not HALT.
                self.assertEqual(run_cycle(sender, datetime(2026, 10, 28, 14, 15, 5,
                                                           tzinfo=timezone.utc)),
                                 "M15_TIMESTAMP_UNTRUSTED_NO_ENTRY")
                self.assertEqual(proposer.call_count, 1)
                self.assertEqual(journal.store.values, {})

    def test_inside_20261029_141500_msk_timestamp_skip_retries_without_post(self):
        # Actual incident: Inside at 2026-10-29 11:15:00.263995 UTC.
        # The archive contains no individual candle timestamps; never
        # accept an invalid witness or silently consume the bar's decision.
        with TemporaryDirectory() as tmp:
            journal = self.fake_journal(Path(tmp))
            snapshots = []
            reader = SimpleNamespace(snapshot=lambda **k: snapshots.append(k) or
                                     SimpleNamespace(positions={}, orders=[]))
            sender = SimpleNamespace(journal=journal, reader=reader,
                                     auth={"roundtrip_cost_rub": {x: "2.02" for x in SYMBOLS}},
                                     auth_path=Path(tmp)/"none", source="0"*40)
            t0 = datetime(2026, 10, 29, 11, 15, 0, 263995, tzinfo=timezone.utc)
            with ExitStack() as stack:
                stack.enter_context(patch("V20_TradingSystem_M15.v20_runtime.finam_live._safe_auth"))
                follow = stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live._follow_existing",
                    return_value="BROKER_RECONCILED_PROTECTION_PASS"))
                stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live.load_kill_switch",
                    return_value=({"state": "ARMED"}, None)))
                proposer = stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live.propose_finam_m15_next_open",
                    side_effect=[V20FinamBlocked("M15_FINAM_TIMESTAMP_OUT_OF_RANGE"),
                                 None, None, None, None]))
                submit = stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live.V20LiveTransport.submit_entry_once"))
                self.assertEqual(run_cycle(sender, t0),
                                 "M15_TIMESTAMP_UNTRUSTED_NO_ENTRY")
                self.assertEqual(proposer.call_count, 1)
                self.assertEqual(journal.store.values, {})
                submit.assert_not_called()
                # At 14:15:30 MSK, the same boundary may recover, with
                # original order of all four symbols and no invented fill.
                retry = t0.replace(second=30)
                self.assertEqual(run_cycle(sender, retry), "NO_FROZEN_SIGNAL")
                self.assertEqual(proposer.call_count, 5)
                self.assertEqual(len(snapshots), 2)
                self.assertEqual(follow.call_count, 2)
                submit.assert_not_called()

    def test_timestamp_failure_in_position_followup_still_halts(self):
        with TemporaryDirectory() as tmp:
            journal = self.fake_journal(Path(tmp))
            reader = SimpleNamespace(snapshot=lambda **k:
                                     SimpleNamespace(positions={}, orders=[]))
            sender = SimpleNamespace(journal=journal, reader=reader,
                                     auth_path=Path(tmp)/"none", source="0"*40)
            with patch("V20_TradingSystem_M15.v20_runtime.finam_live._safe_auth"), patch(
                "V20_TradingSystem_M15.v20_runtime.finam_live._follow_existing",
                side_effect=V20FinamBlocked("M15_FINAM_TIMESTAMP_OUT_OF_RANGE")
            ):
                with self.assertRaisesRegex(V20FinamBlocked,
                                            "M15_FINAM_TIMESTAMP_OUT_OF_RANGE"):
                    run_cycle(sender, datetime(2026, 10, 29, 11, 15, 0,
                                               tzinfo=timezone.utc))

    def test_other_live_entry_timestamp_faults_remain_strict(self):
        with TemporaryDirectory() as tmp:
            journal = self.fake_journal(Path(tmp))
            reader = SimpleNamespace(snapshot=lambda **k:
                                     SimpleNamespace(positions={}, orders=[]))
            sender = SimpleNamespace(journal=journal, reader=reader,
                                     auth={"roundtrip_cost_rub": {x: "2.02" for x in SYMBOLS}},
                                     auth_path=Path(tmp)/"none", source="0"*40)
            with patch("V20_TradingSystem_M15.v20_runtime.finam_live._safe_auth"), patch(
                "V20_TradingSystem_M15.v20_runtime.finam_live._follow_existing",
                return_value="BROKER_RECONCILED_PROTECTION_PASS"
            ), patch("V20_TradingSystem_M15.v20_runtime.finam_live.load_kill_switch",
                     return_value=({"state": "ARMED"}, None)), patch(
                "V20_TradingSystem_M15.v20_runtime.finam_live.propose_finam_m15_next_open",
                side_effect=V20FinamBlocked("M15_FINAM_GRID_MISMATCH")
            ):
                with self.assertRaisesRegex(V20FinamBlocked, "M15_FINAM_GRID_MISMATCH"):
                    run_cycle(sender, datetime(2026, 10, 29, 11, 15, 0,
                                               tzinfo=timezone.utc))

    def test_transient_broker_get_failures_never_submit_and_do_not_halt(self):
        for error in (FinamServerError("HTTP_503:account"),
                      FinamTimeout("account"), FinamRateLimit("orders")):
            with self.subTest(type=type(error).__name__), TemporaryDirectory() as tmp:
                journal = self.fake_journal(Path(tmp))
                sender = SimpleNamespace(
                    journal=journal, reader=SimpleNamespace(snapshot=lambda **k: (_ for _ in ()).throw(error)),
                    auth_path=Path(tmp)/"none", source="0"*40)
                now = datetime(2026, 10, 27, 7, 0, 10, tzinfo=timezone.utc)
                with patch("V20_TradingSystem_M15.v20_runtime.finam_live._safe_auth"), patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live._follow_existing"
                ) as follow:
                    with self.assertRaises(type(error)):
                        run_cycle(sender, now)
                    follow.assert_not_called()
                    self.assertEqual(journal.store.values, {})

    def test_night_snapshot_generic_http_400_408_retries_without_entry(self):
        for status in (400, 408):
            with self.subTest(status=status), TemporaryDirectory() as tmp:
                journal = self.fake_journal(Path(tmp))
                reader = SimpleNamespace(snapshot=lambda **k: (_ for _ in ()).throw(
                    FinamError(f"HTTP_{status}:/v1/accounts/private/orders")))
                sender = SimpleNamespace(journal=journal, reader=reader,
                                         auth_path=Path(tmp)/"none", source="0"*40)
                with patch("V20_TradingSystem_M15.v20_runtime.finam_live._safe_auth"), patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live._follow_existing"
                ) as follow:
                    with self.assertRaisesRegex(V20FinamSnapshotReadRetry,
                                                f"FINAM_SNAPSHOT_HTTP_{status}"):
                        run_cycle(sender, datetime(2026, 10, 29, 7, 11, 48, tzinfo=timezone.utc))
                    follow.assert_not_called()
                    self.assertEqual(journal.store.values, {})

    def test_closed_moex_night_flat_skips_finam_get_until_0650_msk(self):
        # Exchange closed 23:50..06:50 MSK: no account/orders GET,
        # no new order, no switch mutation; start/finish are exact.
        with TemporaryDirectory() as tmp:
            journal = self.fake_journal(Path(tmp))
            reader = SimpleNamespace(snapshot=lambda **k: (_ for _ in ()).throw(
                AssertionError("NO_FINAM_GET_DURING_CLOSED_FLAT")))
            sender = SimpleNamespace(journal=journal, reader=reader,
                                     auth_path=Path(tmp)/"none", source="0"*40)
            with patch("V20_TradingSystem_M15.v20_runtime.finam_live._safe_auth"), patch(
                "V20_TradingSystem_M15.v20_runtime.finam_live.load_kill_switch",
                return_value=({"state": "ARMED"}, None)
            ), patch("V20_TradingSystem_M15.v20_runtime.finam_live._follow_existing") as follow:
                for stamp in (
                    datetime(2026, 10, 29, 20, 50, tzinfo=timezone.utc),
                    datetime(2026, 10, 30, 2, 11, 2, tzinfo=timezone.utc),
                    datetime(2026, 10, 30, 3, 49, 59, tzinfo=timezone.utc),
                ):
                    self.assertEqual(run_cycle(sender, stamp), "WAIT_NEXT_M15_OPEN")
                    self.assertTrue(reader._closed_night_flat_no_get)
                follow.assert_not_called()
                self.assertEqual(journal.store.values, {})
                # At 06:50 market reopening, a fresh broker snapshot is
                # MANDATORY; never treat a prior flat ledger as live proof.
                with self.assertRaisesRegex(AssertionError, "NO_FINAM_GET_DURING_CLOSED_FLAT"):
                    run_cycle(sender, datetime(2026, 10, 30, 3, 50, tzinfo=timezone.utc))
                self.assertFalse(reader._closed_night_flat_no_get)
                # At 23:49:59 Moscow the exchange has not closed.
                with self.assertRaisesRegex(AssertionError, "NO_FINAM_GET_DURING_CLOSED_FLAT"):
                    run_cycle(sender, datetime(2026, 10, 29, 20, 49, 59, tzinfo=timezone.utc))

    def test_closed_night_unsettled_entry_still_requires_broker_reconcile(self):
        with TemporaryDirectory() as tmp:
            journal = self.fake_journal(Path(tmp))
            journal.store.rows = [{"idempotency_key": "pending", "payload": {"kind": "ENTRY"}}]
            reader = SimpleNamespace(snapshot=lambda **k: (_ for _ in ()).throw(
                FinamServerError("HTTP_503:account")))
            sender = SimpleNamespace(journal=journal, reader=reader,
                                     auth_path=Path(tmp)/"none", source="0"*40)
            with patch("V20_TradingSystem_M15.v20_runtime.finam_live._safe_auth"):
                with self.assertRaises(FinamServerError):
                    run_cycle(sender, datetime(2026, 10, 30, 2, 11, tzinfo=timezone.utc))
                self.assertFalse(reader._closed_night_flat_no_get)

    def test_closed_night_orphan_stop_never_skips_broker(self):
        with TemporaryDirectory() as tmp:
            journal = self.fake_journal(Path(tmp))
            journal.store.rows = [{"idempotency_key": "orphan", "payload": {"kind": "STOP"}}]
            reader = SimpleNamespace(snapshot=lambda **k: (_ for _ in ()).throw(
                FinamTimeout("account")))
            sender = SimpleNamespace(journal=journal, reader=reader,
                                     auth_path=Path(tmp)/"none", source="0"*40)
            with patch("V20_TradingSystem_M15.v20_runtime.finam_live._safe_auth"):
                with self.assertRaises(FinamTimeout):
                    run_cycle(sender, datetime(2026, 10, 30, 2, 11, tzinfo=timezone.utc))
                self.assertFalse(reader._closed_night_flat_no_get)

    def test_closed_night_halted_flat_does_not_poll_or_rearm(self):
        with TemporaryDirectory() as tmp:
            journal = self.fake_journal(Path(tmp))
            reader = SimpleNamespace(snapshot=lambda **k: (_ for _ in ()).throw(
                AssertionError("HALTED_NO_GET")))
            sender = SimpleNamespace(journal=journal, reader=reader,
                                     auth_path=Path(tmp)/"none", source="0"*40)
            with patch("V20_TradingSystem_M15.v20_runtime.finam_live._safe_auth"), patch(
                "V20_TradingSystem_M15.v20_runtime.finam_live.load_kill_switch",
                return_value=({"state": "HALTED"}, None)
            ):
                self.assertEqual(run_cycle(sender, datetime(2026, 10, 30, 2, 11, tzinfo=timezone.utc)),
                                 "HALTED_NO_NEW_ENTRIES")
                self.assertFalse(reader._closed_night_flat_no_get)

    def test_20261030_night_flat_snapshot_http_fault_is_retry_not_halt(self):
        # 3 real robots experienced 5xx storm followed by an unclassified
        # FinamError at 05:11/05:41 Moscow. Synthetic individual HTTP
        # classes: actual status is NOT available in the exported journal.
        for error in (
            FinamError("HTTP_409:/v1/accounts/isolated-test/orders"),
            FinamError("HTTP_422:/v1/accounts/isolated-test"),
            FinamNotFound("/v1/accounts/isolated-test/orders"),
        ):
            with self.subTest(error=type(error).__name__ + str(error)), TemporaryDirectory() as tmp:
                journal = self.fake_journal(Path(tmp))
                reader = SimpleNamespace(
                    account_id="isolated-test",
                    snapshot=lambda **kw: (_ for _ in ()).throw(error))
                sender = SimpleNamespace(
                    journal=journal, reader=reader,
                    auth_path=Path(tmp)/"none", source="0"*40)
                with patch("V20_TradingSystem_M15.v20_runtime.finam_live._safe_auth"), patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live._follow_existing"
                ) as follow:
                    with self.assertRaisesRegex(V20FinamSnapshotReadRetry, "FINAM_NIGHT_SNAPSHOT_HTTP_"):
                        run_cycle(sender, datetime(2026, 10, 30, 7, 11, 2, tzinfo=timezone.utc))
                    follow.assert_not_called()
                    self.assertEqual(journal.store.values, {})
                    self.assertEqual(journal.store.all_intents(), [])

    def test_night_snapshot_fault_does_not_relax_broker_ownership_or_auth(self):
        account = "isolated-test"
        for error in (
            FinamError("HTTP_401:/v1/accounts/" + account),
            FinamError("HTTP_403:/v1/accounts/" + account),
            FinamError("HTTP_422:/v1/assets/example/params"),
            FinamError("HTTP_409:/v1/accounts/foreign/orders"),
        ):
            with self.subTest(error=str(error)), TemporaryDirectory() as tmp:
                journal = self.fake_journal(Path(tmp))
                reader = SimpleNamespace(account_id=account, snapshot=lambda **kw: (_ for _ in ()).throw(error))
                sender = SimpleNamespace(journal=journal, reader=reader,
                                         auth_path=Path(tmp)/"none", source="0"*40)
                with patch("V20_TradingSystem_M15.v20_runtime.finam_live._safe_auth"):
                    with self.assertRaises(type(error)):
                        run_cycle(sender, datetime(2026, 10, 30, 7, 11, 2, tzinfo=timezone.utc))
                    self.assertEqual(journal.store.values, {})

        for state in ("unsettled", "in_session", "execution_halt"):
            with self.subTest(state=state), TemporaryDirectory() as tmp:
                journal = self.fake_journal(Path(tmp))
                if state == "unsettled":
                    journal.store.rows = [{"idempotency_key": "entry-key", "payload": {"kind": "ENTRY"}}]
                if state == "execution_halt":
                    journal.store.put("execution_halt", "MANUAL_OR_BROKER_FAULT")
                error = FinamError("HTTP_422:/v1/accounts/" + account + "/orders")
                reader = SimpleNamespace(account_id=account, snapshot=lambda **kw: (_ for _ in ()).throw(error))
                sender = SimpleNamespace(journal=journal, reader=reader,
                                         auth_path=Path(tmp)/"none", source="0"*40)
                now = datetime(2026, 10, 30, 8 if state == "in_session" else 2, 11, 2,
                               tzinfo=timezone.utc)
                with patch("V20_TradingSystem_M15.v20_runtime.finam_live._safe_auth"):
                    with self.assertRaisesRegex(FinamError, "HTTP_422"):
                        run_cycle(sender, now)

    def test_other_snapshot_errors_and_follow_get_remain_strict_halt(self):
        for error in (FinamError("HTTP_401:/v1/accounts/private"),
                      FinamError("HTTP_403:/v1/accounts/private"),
                      FinamError("HTTP_422:/v1/accounts/private"),
                      FinamUncertainSubmission("RECONCILIATION_REQUIRED")):
            with self.subTest(error=str(error)), TemporaryDirectory() as tmp:
                journal = self.fake_journal(Path(tmp))
                reader = SimpleNamespace(snapshot=lambda **k: (_ for _ in ()).throw(error))
                sender = SimpleNamespace(journal=journal, reader=reader,
                                         auth_path=Path(tmp)/"none", source="0"*40)
                with patch("V20_TradingSystem_M15.v20_runtime.finam_live._safe_auth"):
                    with self.assertRaises(type(error)):
                        run_cycle(sender, datetime(2026, 10, 29, 7, 11, 48, tzinfo=timezone.utc))
                    self.assertEqual(journal.store.values, {})
        with TemporaryDirectory() as tmp:
            journal = self.fake_journal(Path(tmp))
            sender = SimpleNamespace(journal=journal,
                                     reader=SimpleNamespace(snapshot=lambda **k: object()),
                                     auth_path=Path(tmp)/"none", source="0"*40)
            with patch("V20_TradingSystem_M15.v20_runtime.finam_live._safe_auth"), patch(
                "V20_TradingSystem_M15.v20_runtime.finam_live._follow_existing",
                side_effect=FinamError("HTTP_400:/v1/accounts/private/trades")):
                with self.assertRaisesRegex(FinamError, "HTTP_400"):
                    run_cycle(sender, datetime(2026, 10, 29, 7, 11, 48, tzinfo=timezone.utc))

    def test_transient_m15_signal_get_failure_skips_boundary_without_entry(self):
        with TemporaryDirectory() as tmp:
            journal = self.fake_journal(Path(tmp))
            reader = SimpleNamespace(snapshot=lambda **k: SimpleNamespace(positions={}, orders=[]))
            sender = SimpleNamespace(journal=journal, reader=reader,
                                     auth={"roundtrip_cost_rub": {x: "2.02" for x in SYMBOLS}},
                                     auth_path=Path(tmp)/"none", source="0"*40)
            now = datetime(2026, 10, 27, 7, 15, 10, tzinfo=timezone.utc)
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
                with self.assertRaises(FinamServerError):
                    run_cycle(sender, now)
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
                    run_cycle(sender, datetime(2026, 10, 27, 7, 0, 10, tzinfo=timezone.utc))

    def test_live_timestamp_skip_writes_market_only_evidence_to_existing_jsonl(self):
        class EndCycle(BaseException):
            pass

        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "V20Lab"
            instance = root / "robots" / "shallow"
            (instance / "logs").mkdir(parents=True)
            journal = self.fake_journal(instance)
            account = "v20-test-account"
            reader = SimpleNamespace(authenticate=lambda: None)
            details = {
                "symbol": "USDRUBF", "reason": "AFTER_NOW",
                "received_utc": "2026-10-29T11:30:00+00:00",
                "request_start_utc": "2026-10-09T11:15:00+00:00",
                "request_end_exclusive_utc": "2026-10-29T11:30:00+00:00",
                "observed_utc": "2026-10-29T11:15:00.264000+00:00",
            }
            def cycle(*_args):
                reader._m15_timestamp_diagnostic = details
                return "M15_TIMESTAMP_UNTRUSTED_NO_ENTRY"

            with ExitStack() as stack:
                stack.enter_context(patch.dict("os.environ", {
                    "V20_FINAM_ACCOUNT": account, "V20_FINAM_TOKEN": "synthetic",
                    "V20_FINAM_ACCOUNT_SHA256": hashlib.sha256(account.encode()).hexdigest(),
                }))
                stack.enter_context(patch("V20_TradingSystem_M15.v20_runtime.finam_live.V20LiveJournal",
                                          return_value=nullcontext(journal)))
                stack.enter_context(patch("V20_TradingSystem_M15.v20_runtime.finam_live.FinamAPI"))
                stack.enter_context(patch("V20_TradingSystem_M15.v20_runtime.finam_live.V20FinamReadAdapter",
                                          return_value=reader))
                stack.enter_context(patch("V20_TradingSystem_M15.v20_runtime.finam_live.V20LiveTransport"))
                stack.enter_context(patch("V20_TradingSystem_M15.v20_runtime.finam_live.run_cycle",
                                          side_effect=cycle))
                stack.enter_context(patch("V20_TradingSystem_M15.v20_runtime.finam_live.time.sleep",
                                          side_effect=EndCycle()))
                with self.assertRaises(EndCycle):
                    run(root=root, robot="v20-shallow", source="0" * 40)
            rows = [json.loads(line) for line in
                    (instance / "logs" / "live-m15.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["state"], "M15_TIMESTAMP_UNTRUSTED_NO_ENTRY")
            self.assertEqual(rows[0]["m15_rejected_bar"], details)
            self.assertNotIn(account, json.dumps(rows))
            self.assertNotIn("synthetic", json.dumps(rows))

    def test_h1_style_broker_fault_retry_keeps_process_and_existing_switch(self):
        class EndAfterRecoveredCycle(BaseException):
            pass

        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "V20Lab"
            robot = "v20-shallow"
            instance = root / "robots" / "shallow"
            (instance / "logs").mkdir(parents=True)
            journal = self.fake_journal(instance)
            account = "v20-test-account"
            env = {
                "V20_FINAM_ACCOUNT": account,
                "V20_FINAM_TOKEN": "synthetic-token",
                "V20_FINAM_ACCOUNT_SHA256": hashlib.sha256(account.encode()).hexdigest(),
            }
            reader = SimpleNamespace(authenticate=lambda: None)
            cycle = [FinamServerError("HTTP_503:GET"),
                     V20FinamSnapshotReadRetry("FINAM_SNAPSHOT_HTTP_400"),
                     "WAIT_NEXT_M15_OPEN"]
            with ExitStack() as stack:
                stack.enter_context(patch.dict("os.environ", env))
                stack.enter_context(patch("V20_TradingSystem_M15.v20_runtime.finam_live.V20LiveJournal",
                                          return_value=nullcontext(journal)))
                stack.enter_context(patch("V20_TradingSystem_M15.v20_runtime.finam_live.FinamAPI"))
                stack.enter_context(patch("V20_TradingSystem_M15.v20_runtime.finam_live.V20FinamReadAdapter",
                                          return_value=reader))
                stack.enter_context(patch("V20_TradingSystem_M15.v20_runtime.finam_live.V20LiveTransport"))
                run_mock = stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live.run_cycle",
                    side_effect=cycle))
                halt = stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live.emergency_halt"))
                sleep = stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live.time.sleep",
                    side_effect=[None, None, EndAfterRecoveredCycle()]))
                with self.assertRaises(EndAfterRecoveredCycle):
                    run(root=root, robot=robot, source="0" * 40)
                self.assertEqual(run_mock.call_count, 3)
                self.assertEqual([x.args[0] for x in sleep.call_args_list], [3, 3, 30])
                halt.assert_not_called()
            rows = [json.loads(x) for x in
                    (instance/"logs"/"live-m15.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual([row["state"] for row in rows],
                             ["FAULT_FinamServerError", "FAULT_FINAM_SNAPSHOT_HTTP_400",
                              "WAIT_NEXT_M15_OPEN"])

    def test_h1_style_unsafe_fault_halts_entries_but_does_not_terminate_process(self):
        class EndAfterSecondCycle(BaseException):
            pass

        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "V20Lab"
            instance = root / "robots" / "shallow"
            (instance / "logs").mkdir(parents=True)
            account = "v20-test-account"
            journal = self.fake_journal(instance)
            env = {
                "V20_FINAM_ACCOUNT": account, "V20_FINAM_TOKEN": "synthetic-token",
                "V20_FINAM_ACCOUNT_SHA256": hashlib.sha256(account.encode()).hexdigest(),
            }
            with ExitStack() as stack:
                stack.enter_context(patch.dict("os.environ", env))
                stack.enter_context(patch("V20_TradingSystem_M15.v20_runtime.finam_live.V20LiveJournal",
                                          return_value=nullcontext(journal)))
                stack.enter_context(patch("V20_TradingSystem_M15.v20_runtime.finam_live.FinamAPI"))
                stack.enter_context(patch("V20_TradingSystem_M15.v20_runtime.finam_live.V20FinamReadAdapter",
                                          return_value=SimpleNamespace(authenticate=lambda: None)))
                stack.enter_context(patch("V20_TradingSystem_M15.v20_runtime.finam_live.V20LiveTransport"))
                cycles = stack.enter_context(patch("V20_TradingSystem_M15.v20_runtime.finam_live.run_cycle",
                                                   side_effect=[V20FinamBlocked("V20_LIVE_UNOWNED_BROKER_POSITION"),
                                                                "HALTED_NO_NEW_ENTRIES"]))
                halted = stack.enter_context(patch("V20_TradingSystem_M15.v20_runtime.finam_live.emergency_halt"))
                stack.enter_context(patch("V20_TradingSystem_M15.v20_runtime.finam_live.time.sleep",
                                          side_effect=[None, EndAfterSecondCycle()]))
                with self.assertRaises(EndAfterSecondCycle):
                    run(root=root, robot="v20-shallow", source="0" * 40)
                self.assertEqual(cycles.call_count, 2)
                halted.assert_called_once_with(instance)
            lines=(instance/"logs"/"live-m15.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual([json.loads(row)["state"] for row in lines],
                             ["HALT_V20_LIVE_UNOWNED_BROKER_POSITION","HALTED_NO_NEW_ENTRIES"])

    def test_foreign_active_order_is_refused(self):
        with TemporaryDirectory() as tmp:
            journal = self.fake_journal(Path(tmp))
            order = SimpleNamespace(active=True, client_order_id="unknown",
                                    symbol="FUTCNYRUBF", kind="REGULAR")
            with self.assertRaisesRegex(V20FinamBlocked, "FOREIGN_OR_DUPLICATE_ACTIVE"):
                _ownership(journal, SimpleNamespace(positions={}, orders=[order]))


if __name__ == "__main__":
    unittest.main()
