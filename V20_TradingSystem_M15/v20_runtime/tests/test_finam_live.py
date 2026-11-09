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
    V20FinamSnapshotReadRetry, _night_protected_sleep_seconds, _verify_sealed_protection,
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


class LiveWatchingStopMissingClientIdTests(unittest.TestCase):
    """2026-11-03: FINAM returns WATCHING SLTP with empty client_order_id."""

    def example(self):
        from decimal import Decimal
        from V20_TradingSystem_M15.v20_runtime.finam_execution import (
            _v20_order_views, V20FinamReadAdapter, LiveAccountSnapshot,
        )
        account_hash = "a" * 64
        key = "v20:v20-inside:" + account_hash[:16] + ":20261102-entry"
        raw = {
            "order_id": "exact-stop-broker-id", "status": "ORDER_STATUS_WATCHING",
            "sltp_order": {
                "symbol": "USDRUBF@RTSX", "side": "SIDE_SELL",
                "client_order_id": "", "comment": key + ":stop",
                "quantity_sl": {"value": "100"},
                "sl_qty_measure": "SLTP_QTY_MEASURE_PERCENT",
                "sl_price": {"value": "100"},
                "valid_before": "VALID_BEFORE_GOOD_TILL_CANCEL",
            },
        }
        order, omitted = _v20_order_views({"orders": [raw]})
        self.assertEqual(omitted, 0)
        self.assertEqual(order[0].client_order_id, "")
        self.assertEqual(order[0].request["client_order_id"], "")
        payload = {"kind": "ENTRY", "mode": "PRETRADE_NOT_AUTHORIZED",
                   "robot_id": "v20-inside", "account_sha256": account_hash,
                   "symbol": "USDRUBF", "finam_symbol": "USDRUBF@RTSX",
                   "direction": "LONG", "quantity": 2}
        entry = {"idempotency_key": key, "status": "RECONCILED",
                 "broker_order_id": "entry-broker-id", "payload": payload}
        journal = SimpleNamespace(robot_id="v20-inside", account_hash=account_hash,
                                  store=StubStore(rows=[entry]))
        journal.store.intents[key + ":stop"] = {
            "status": "RECONCILED", "broker_order_id": "exact-stop-broker-id"}
        journal.store.values["protected_fill:" + key] = {
            "account_sha256": account_hash,
            "broker_order_id": "entry-broker-id",
            "broker_stop_id": "exact-stop-broker-id",
            "installed_stop": "100", "broker_stop_percent": "100",
            "filled_quantity": 2,
            "risk_assessment": {"status": "PASS", "stop_conforms": True}}
        snap = LiveAccountSnapshot("v20-inside", account_hash,
                                   datetime.now(timezone.utc),
                                   Decimal("45000"), Decimal("10000"),
                                   {"USDRUBF@RTSX": 2}, tuple(order))
        reader = object.__new__(V20FinamReadAdapter)
        reader.robot_id = "v20-inside"
        reader.account_hash = account_hash
        reader._bound = True
        return raw, journal, snap, reader, entry

    def test_confirmed_broker_stop_no_synthetic_client_id(self):
        from V20_TradingSystem_M15.v20_runtime.finam_execution import _v20_order_views
        raw, journal, snap, reader, entry = self.example()
        self.assertEqual(len(_ownership(journal, snap)), 1)
        now = snap.observed_at
        _verify_sealed_protection(journal, reader, snap, now, entry)
        self.assertEqual(snap.orders[0].client_order_id, "")
        self.assertEqual(raw["sltp_order"]["client_order_id"], "")
        # Broker-flat may precede FINAM stop deactivation. Its exact
        # known stop must remain visible for safe stop cleanup, not vanish.
        from dataclasses import replace as dc_replace
        self.assertEqual(len(_ownership(journal, dc_replace(snap, positions={}))), 1)

    def test_20261108_flat_cleanup_watching_stop_uses_exact_broker_id(self):
        # FINAM WATCHING may omit client_order_id even after an exact
        # protected-fill observation; cancellation must stay owner-scoped.
        from dataclasses import replace as dc_replace
        from V20_TradingSystem_M15.v20_runtime.finam_execution import V20SingleTradeTransport
        raw, journal, snap, reader, entry = self.example()
        key = entry["idempotency_key"]
        class CancelStore(StubStore):
            def transaction(self):
                return nullcontext()
            def persist_intent(self, name, payload):
                self.intents[name] = {"status": "INTENT_PERSISTED", "payload": payload}
            def transition_intent(self, name, status, broker_id=None):
                self.intents[name]["status"] = status
        store = CancelStore(rows=[entry])
        store.intents.update(journal.store.intents)
        store.intents[key + ":frozen-exit"] = {
            "status": "ACK", "payload": {"kind": "FROZEN_EXIT"}}
        store.values.update(journal.store.values)
        journal.store = store
        flat = dc_replace(snap, positions={})
        current = [flat]
        canceled = []
        api = SimpleNamespace(cancel_order=lambda account, oid: canceled.append((account, oid)))
        transport = SimpleNamespace(journal=journal,
            reader=SimpleNamespace(_fresh=lambda *args: None,
                snapshot=lambda **kw: current[0], api=api, account_id="test-account"),
            _permit=lambda **kw: {"instrument": "USDRUBF"})
        # Reject a different broker order or a non-WATCHING empty client ID.
        for altered in (dc_replace(flat.orders[0], order_id="wrong-id"),
                        dc_replace(flat.orders[0], status="NEW")):
            current[0] = dc_replace(flat, orders=(altered,))
            with self.assertRaisesRegex(V20FinamBlocked, "FLAT_CLEANUP_STOP_ID_MISMATCH"):
                V20SingleTradeTransport.cancel_stop_after_flat_once(
                    transport, key=key, snapshot=current[0], now=flat.observed_at)
        self.assertEqual(canceled, [])
        current[0] = flat
        self.assertEqual(V20SingleTradeTransport.cancel_stop_after_flat_once(
            transport, key=key, snapshot=flat, now=flat.observed_at),
            "CANCEL_ACK_REQUIRE_BROKER_NO_STOP_CONFIRMATION")
        self.assertEqual(canceled, [("test-account", "exact-stop-broker-id")])

    def test_missing_broker_identity_and_foreign_active_fail_closed(self):
        from V20_TradingSystem_M15.v20_runtime.finam_execution import _v20_order_views
        raw, journal, snap, reader, entry = self.example()
        journal.store.intents[entry["idempotency_key"] + ":stop"]["broker_order_id"] = "wrong-id"
        with self.assertRaisesRegex(V20FinamBlocked, "STOP_BROKER_IDENTITY_MISMATCH"):
            _ownership(journal, snap)
        journal.store.intents[entry["idempotency_key"] + ":stop"]["broker_order_id"] = "exact-stop-broker-id"
        damaged = dict(raw, sltp_order=dict(raw["sltp_order"], quantity_sl={"value": "50"}))
        from TradingSystemLab.stage8_robot.production_broker_state import ProductionBrokerStateError
        with self.assertRaisesRegex(ProductionBrokerStateError, "SLTP_CLOSE_ONLY_CONTRACT_INVALID"):
            _v20_order_views({"orders": [damaged]})
        damaged = dict(raw, sltp_order=dict(raw["sltp_order"], comment="foreign:stop"))
        with self.assertRaisesRegex(ProductionBrokerStateError, "STAGE8_12_4_ORDER_REQUEST_INVALID"):
            _v20_order_views({"orders": [damaged]})
        damaged = dict(raw, order={"symbol": "USDRUBF@RTSX", "side": "SIDE_BUY",
                                   "client_order_id": ""}, sltp_order={})
        with self.assertRaisesRegex(ProductionBrokerStateError, "STAGE8_12_4_ORDER_REQUEST_INVALID"):
            _v20_order_views({"orders": [damaged]})

class PostWeekendSafetyFixTests(unittest.TestCase):
    def test_sealed_entry_uses_current_broker_stop_without_historical_replay(self):
        journal = SimpleNamespace(account_hash="a" * 64, store=StubStore())
        key = "v20:v20-shallow:" + "a" * 16 + ":entry"
        row = {"idempotency_key": key, "broker_order_id": "entry-broker",
               "status": "RECONCILED", "payload": {
                   "symbol": "GLDRUBF", "direction": "LONG",
                   "finam_symbol": "FUTGLDRUBF"}}
        journal.store.values["protected_fill:" + key] = {
            "account_sha256": journal.account_hash,
            "broker_order_id": "entry-broker", "broker_stop_id": "broker-stop",
            "broker_stop_percent": "100", "filled_quantity": 2,
            "installed_stop": "101.5",
            "risk_assessment": {"status": "PASS", "stop_conforms": True}}
        journal.store.intents[key + ":stop"] = {
            "status": "ACK", "broker_order_id": "broker-stop"}
        calls = []
        reader = SimpleNamespace(inspect_protective_stop=lambda *a, **kw:
                                  (calls.append(kw) or SimpleNamespace(order_id="broker-stop")))
        snapshot = SimpleNamespace(positions={"FUTGLDRUBF": 2})
        now = datetime.now(timezone.utc)
        _verify_sealed_protection(journal, reader, snapshot, now, row)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["stop_price"], __import__("decimal").Decimal("101.5"))
        snapshot.positions["FUTGLDRUBF"] = 3
        with self.assertRaisesRegex(V20FinamBlocked, "SEALED_ENTRY_DURABLE_PROTECTION_INVALID"):
            _verify_sealed_protection(journal, reader, snapshot, now, row)
        snapshot.positions["FUTGLDRUBF"] = 2
        reader.inspect_protective_stop = lambda *a, **kw: SimpleNamespace(order_id="changed-stop")
        with self.assertRaisesRegex(V20FinamBlocked, "SEALED_ENTRY_BROKER_STOP_ID_CHANGED"):
            _verify_sealed_protection(journal, reader, snapshot, now, row)

    def test_terminal_metadata_tolerance_never_masks_active_stop_or_duplicate_id(self):
        from TradingSystemLab.stage8_robot.production_broker_state import ProductionBrokerStateError
        from V20_TradingSystem_M15.v20_runtime.finam_execution import _v20_order_views
        terminal = {"order_id": "old-entry", "status": "ORDER_STATUS_FILLED",
                    "order": {"symbol": "GLDRUBF", "side": "SIDE_UNSPECIFIED",
                              "client_order_id": ""}}
        active = {"order_id": "active-stop", "status": "ORDER_STATUS_NEW",
                  "sltp_order": {"symbol": "GLDRUBF", "side": "SIDE_SELL",
                                 "client_order_id": "stop-key", "comment": "owned"}}
        views, omitted = _v20_order_views({"orders": [terminal, active]})
        self.assertEqual(omitted, 1)
        self.assertEqual(len(views), 1)
        self.assertTrue(views[0].active)
        invalid_active = dict(active, sltp_order=dict(active["sltp_order"], side="SIDE_UNSPECIFIED"))
        with self.assertRaisesRegex(ProductionBrokerStateError, "STAGE8_12_4_ORDER_REQUEST_INVALID"):
            _v20_order_views({"orders": [terminal, invalid_active]})
        with self.assertRaisesRegex(ProductionBrokerStateError, "STAGE8_12_4_ORDER_ID_INVALID"):
            _v20_order_views({"orders": [terminal, dict(active, order_id="old-entry")]})

class LiveAdmissionTests(unittest.TestCase):
    def fake_journal(self, root: Path):
        return SimpleNamespace(
            instance_root=root, robot_id="v20-shallow",
            account_hash=hashlib.sha256(b"v20-test-account").hexdigest(),
            store=StubStore(),
        )

    def test_20261106_second_position_gets_stop_before_prior_protected_entry_halt(self):
        # CNY is already protected; GLD ACK has no stop and a durable
        # pre-POST checkpoint. Prioritise GLD's protection without clearing
        # the halt, bypassing risk checks or creating a duplicate entry.
        from decimal import Decimal
        from unittest.mock import Mock
        from V20_TradingSystem_M15.v20_runtime.finam_live import _follow_existing
        with TemporaryDirectory() as tmp:
            journal = self.fake_journal(Path(tmp))
            cny = {"idempotency_key": "cny-key", "status": "RECONCILED",
                   "broker_order_id": "cny-entry", "payload": {
                       "symbol": "CNYRUBF", "finam_symbol": "FUTCNYRUBF",
                       "direction": "LONG", "entry_at": "2026-11-06T10:45:00",
                       "atr14": "0.01", "quantity": 20}}
            gld = {"idempotency_key": "gld-key", "status": "ACK",
                   "broker_order_id": "gld-entry", "payload": {
                       "symbol": "GLDRUBF", "finam_symbol": "FUTGLDRUBF",
                       "direction": "LONG", "entry_at": "2026-11-06T12:00:00",
                       "atr14": "29", "quantity": 11}}
            journal.store.rows = [cny, gld]
            journal.store.intents["cny-key:stop"] = {"status": "ACK"}
            journal.store.values["execution_halt"] = "UNKNOWN_POST_REQUIRE_BROKER_RECONCILIATION"
            journal.store.values["entry_submission:gld-key"] = {
                "submitted_at": "2026-11-06T09:00:14+00:00"}
            journal.reconcile_order = Mock()
            snap = SimpleNamespace(positions={"FUTCNYRUBF": 20, "FUTGLDRUBF": 11}, orders=[])
            reader = SimpleNamespace(inspect_entry_fills=Mock(return_value={
                "matched_quantity": 11,
                "matched_unique_fills": [{"quantity": 11, "price": "10788.6"}]}))
            sender = SimpleNamespace(journal=journal, reader=reader,
                                     submit_protection_once=Mock())
            with patch("V20_TradingSystem_M15.v20_runtime.finam_live._ownership",
                       return_value=[cny, gld]), patch(
                "V20_TradingSystem_M15.v20_runtime.finam_live._verify_sealed_protection"
            ) as sealed, patch(
                "V20_TradingSystem_M15.v20_runtime.finam_live._load_registry",
                return_value={"GLDRUBF": {"price_step": "0.1"}}
            ), patch(
                "V20_TradingSystem_M15.v20_runtime.finam_live.project_stop",
                return_value=Decimal("10729.9")
            ):
                state = _follow_existing(sender, datetime(
                    2026, 11, 6, 9, 0, 22, tzinfo=timezone.utc), snap)
            self.assertEqual(state, "STOP_ACK_NEEDS_BROKER_PROOF")
            sender.submit_protection_once.assert_called_once()
            self.assertEqual(sender.submit_protection_once.call_args.kwargs["key"], "gld-key")
            sealed.assert_not_called()
            self.assertEqual(journal.store.get("execution_halt"),
                             "UNKNOWN_POST_REQUIRE_BROKER_RECONCILIATION")

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

    def test_20261103_insufficient_go_skips_entry_without_halt_or_post(self):
        # Incident: OBV already had a fully protected IMOEX position;
        # a later candidate with insufficient free GO must NOT HALT.
        from unittest.mock import Mock
        from V20_TradingSystem_M15.v20_runtime.account_risk import RiskBlocked
        with TemporaryDirectory() as tmp:
            journal = self.fake_journal(Path(tmp))
            journal.prepare_entry = Mock(side_effect=RiskBlocked(
                "NO_ACCOUNT_RISK_OR_MARGIN_CAPACITY"))
            snapshot = SimpleNamespace(positions={}, orders=[])
            reader = SimpleNamespace(snapshot=lambda now: snapshot)
            sender = SimpleNamespace(
                journal=journal, reader=reader, source="0" * 40,
                auth_path=Path(tmp)/"safety"/"v20-live-authorization.json",
                auth=self.valid_auth(journal, "0" * 40),
                submit_entry_once=Mock(side_effect=AssertionError("NO_ORDER_POST")),
            )
            candidate = (object(), object(), object(), snapshot)
            calls = []
            def propose(*args, **kwargs):
                calls.append(kwargs["symbol"])
                return candidate if len(calls) == 1 else None
            with ExitStack() as stack:
                stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live._safe_auth",
                    return_value=sender.auth))
                stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live._follow_existing",
                    return_value="BROKER_RECONCILED_PROTECTION_PASS"))
                stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live.load_kill_switch",
                    return_value=({"state": "ARMED"}, None)))
                stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live._entries",
                    return_value=[]))
                stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live._ownership"))
                stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live.propose_finam_m15_next_open",
                    side_effect=propose))
                result = run_cycle(sender, datetime(2026, 11, 3, 13, 15, tzinfo=timezone.utc))
            self.assertEqual(result, "NO_FROZEN_SIGNAL")
            self.assertEqual(calls, list(SYMBOLS))
            journal.prepare_entry.assert_called_once()
            sender.submit_entry_once.assert_not_called()

    def test_20261103_unsafe_risk_block_still_fails_closed(self):
        from unittest.mock import Mock
        from V20_TradingSystem_M15.v20_runtime.account_risk import RiskBlocked
        with TemporaryDirectory() as tmp:
            journal = self.fake_journal(Path(tmp))
            journal.prepare_entry = Mock(side_effect=RiskBlocked(
                "CROSS_ACCOUNT_RESERVATION"))
            reader = SimpleNamespace(snapshot=lambda now: SimpleNamespace(positions={}, orders=[]))
            sender = SimpleNamespace(
                journal=journal, reader=reader, source="0" * 40,
                auth_path=Path(tmp)/"auth.json",
                auth=self.valid_auth(journal, "0" * 40),
                submit_entry_once=Mock())
            with ExitStack() as stack:
                stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live._safe_auth",
                    return_value=sender.auth))
                stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live._follow_existing",
                    return_value="BROKER_RECONCILED_PROTECTION_PASS"))
                stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live.load_kill_switch",
                    return_value=({"state": "ARMED"}, None)))
                stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live._entries",
                    return_value=[]))
                stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live._ownership"))
                stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live.propose_finam_m15_next_open",
                    return_value=(object(), object(), object(), object())))
                with self.assertRaisesRegex(RiskBlocked, "CROSS_ACCOUNT_RESERVATION"):
                    run_cycle(sender, datetime(2026, 11, 3, 13, 15, tzinfo=timezone.utc))
            sender.submit_entry_once.assert_not_called()

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

    def test_weekend_entry_block_but_existing_exits_and_protection_continue(self):
        with TemporaryDirectory() as tmp:
            journal = self.fake_journal(Path(tmp))
            calls = []
            reader = SimpleNamespace(snapshot=lambda **kw: calls.append(kw) or
                                     SimpleNamespace(positions={}, orders=[]))
            sender = SimpleNamespace(journal=journal, reader=reader,
                                     auth_path=Path(tmp)/"none", source="0"*40)
            with ExitStack() as stack:
                stack.enter_context(patch("V20_TradingSystem_M15.v20_runtime.finam_live._safe_auth"))
                follow = stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live._follow_existing",
                    return_value="BROKER_RECONCILED_PROTECTION_PASS"))
                stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live.load_kill_switch",
                    return_value=({"state": "ARMED"}, None)))
                propose = stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live.propose_finam_m15_next_open"))
                # Saturday 31 Oct and Sunday 1 Nov, both inside normal entry window.
                for day, utc_hour in ((31, 8), (1, 11)):
                    month = 10 if day == 31 else 11
                    now = datetime(2026, month, day, utc_hour, 15, 10,
                                   tzinfo=timezone.utc)
                    self.assertEqual(run_cycle(sender, now), "WEEKEND_NO_NEW_ENTRIES")
                self.assertEqual(len(calls), 2)  # broker reconciliation remains
                self.assertEqual(follow.call_count, 2)
                propose.assert_not_called()
                # A weekday-open position due for its frozen third observed
                # session exit MUST still reach existing followup/exit logic.
                follow.return_value = "FROZEN_EXIT_ACK_KEEP_STOP_UNTIL_FLAT"
                self.assertEqual(run_cycle(sender, datetime(
                    2026, 10, 31, 8, 15, 10, tzinfo=timezone.utc)),
                    "FROZEN_EXIT_ACK_KEEP_STOP_UNTIL_FLAT")
                self.assertEqual(follow.call_count, 3)
                propose.assert_not_called()

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

    def test_protected_open_position_late_m15_witness_retries_without_halt(self):
        # 30 Oct 2026 Shallow/GLDRUBF: FINAM 14:15 MSK Open was late.
        # This occurs AFTER a verified broker position and protective stop;
        # it must not permanently HALT or create any new order.
        with TemporaryDirectory() as tmp:
            journal = self.fake_journal(Path(tmp))
            symbol, key = "GLDRUBF", "friday-gld-entry"
            entry = {"idempotency_key": key, "status": "RECONCILED",
                     "payload": {"kind": "ENTRY", "mode": "PRETRADE_NOT_AUTHORIZED",
                                 "robot_id": journal.robot_id,
                                 "account_sha256": journal.account_hash,
                                 "symbol": symbol, "finam_symbol": "FUTGLDRUBF",
                                 "entry_at": "2026-10-30T12:45:00", "direction": "LONG"},
                     "broker_order_id": "entry-broker"}
            journal.store.rows = [entry]
            journal.store.intents[key+":stop"] = {"status": "RECONCILED",
                                                  "broker_order_id": "stop-broker"}
            journal.store.values["protected_fill:" + key] = {
                "account_sha256": journal.account_hash,
                "broker_order_id": "entry-broker", "broker_stop_id": "stop-broker",
                "filled_quantity": 1, "installed_stop": "101.5",
                "broker_stop_percent": "100",
                "risk_assessment": {"status": "PASS", "stop_conforms": True}}
            journal.reconcile_order = lambda **kw: None
            proof_calls = []
            snapshot = SimpleNamespace(positions={"FUTGLDRUBF": 1}, orders=[])
            reader = SimpleNamespace(
                snapshot=lambda **kw: snapshot,
                inspect_protective_stop=lambda *a, **kw: (proof_calls.append(kw)
                    or SimpleNamespace(order_id="stop-broker")))
            sender = SimpleNamespace(journal=journal, reader=reader,
                                     auth_path=Path(tmp)/"none", source="0"*40)
            with ExitStack() as stack:
                stack.enter_context(patch("V20_TradingSystem_M15.v20_runtime.finam_live._safe_auth"))
                stack.enter_context(patch("V20_TradingSystem_M15.v20_runtime.finam_live._ownership",
                                          return_value=[entry]))
                read = stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live.read_finam_m15_boundary",
                    side_effect=V20FinamBlocked("M15_NEXT_OPEN_WITNESS_MISSING")))
                submit = stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live.V20LiveTransport.submit_frozen_exit_once"))
                enter = stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live.propose_finam_m15_next_open"))
                stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live.load_kill_switch",
                    return_value=({"state": "HALTED"}, None)))
                now = datetime(2026, 10, 30, 11, 15, 3, tzinfo=timezone.utc)
                self.assertEqual(run_cycle(sender, now), "M15_EXIT_WITNESS_PENDING_RETRY")
                self.assertEqual(len(proof_calls), 1)
                read.assert_called_once()
                submit.assert_not_called()
                enter.assert_not_called()
                # Other malformed M15 evidence still fails closed.
                read.side_effect = V20FinamBlocked("M15_FINAM_TIMESTAMP_OUT_OF_RANGE")
                with self.assertRaisesRegex(V20FinamBlocked, "M15_FINAM_TIMESTAMP_OUT_OF_RANGE"):
                    run_cycle(sender, now)
                # Without confirmed broker protection even the delayed-witness
                # exception cannot authorize a healthy/pending state.
                journal.store.values["protected_fill:" + key]["broker_stop_percent"] = "0"
                read.side_effect = V20FinamBlocked("M15_NEXT_OPEN_WITNESS_MISSING")
                with self.assertRaisesRegex(V20FinamBlocked,
                                            "SEALED_ENTRY_DURABLE_PROTECTION_INVALID"):
                    run_cycle(sender, now)

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

    def test_closed_night_protected_throttle_requires_broker_stop_and_settled_entry(self):
        with TemporaryDirectory() as tmp:
            journal = self.fake_journal(Path(tmp))
            key, symbol = "protected-entry", "FUTCNYRUBF"
            entry = {"idempotency_key": key, "status": "RECONCILED",
                     "payload": {"kind": "ENTRY", "mode": "PRETRADE_NOT_AUTHORIZED",
                                 "robot_id": journal.robot_id,
                                 "account_sha256": journal.account_hash,
                                 "symbol": "CNYRUBF", "finam_symbol": symbol}}
            journal.store.rows = [entry]
            journal.store.intents[key + ":stop"] = {"status": "RECONCILED"}
            journal.store.values["protected_fill:" + key] = {
                "broker_stop_id": "stop-1", "filled_quantity": 1,
                "broker_stop_percent": "100"}
            stop = SimpleNamespace(active=True, kind="SLTP", symbol=symbol, order_id="stop-1")
            snap = SimpleNamespace(positions={symbol: 1}, orders=[stop])
            reader = SimpleNamespace(snapshot=lambda **kwargs: snap)
            sender = SimpleNamespace(journal=journal, reader=reader,
                                     auth_path=Path(tmp)/"none", source="0"*40)
            with ExitStack() as stack:
                stack.enter_context(patch("V20_TradingSystem_M15.v20_runtime.finam_live._safe_auth"))
                follow = stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live._follow_existing",
                    return_value="BROKER_RECONCILED_PROTECTION_PASS"))
                stack.enter_context(patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live.load_kill_switch",
                    return_value=({"state": "ARMED"}, None)))
                night = datetime(2026, 10, 30, 2, 11, tzinfo=timezone.utc)
                self.assertEqual(run_cycle(sender, night), "MOEX_CLOSED_PROTECTED_MONITOR")
                self.assertEqual(_night_protected_sleep_seconds(night), 120)
                self.assertEqual(_night_protected_sleep_seconds(
                    datetime(2026, 10, 30, 3, 49, 59, tzinfo=timezone.utc)), 1)
                self.assertEqual(_night_protected_sleep_seconds(
                    datetime(2026, 10, 30, 3, 50, tzinfo=timezone.utc)), 0)
                self.assertEqual(run_cycle(sender, datetime(
                    2026, 10, 30, 3, 50, tzinfo=timezone.utc)), "WAIT_NEXT_M15_OPEN")
                entry["status"] = "PARTIAL_FILL"
                self.assertEqual(run_cycle(sender, night), "WAIT_NEXT_M15_OPEN")
                entry["status"] = "RECONCILED"
                snap.orders = []
                self.assertEqual(run_cycle(sender, night), "WAIT_NEXT_M15_OPEN")
                snap.orders = [stop, SimpleNamespace(active=True, kind="REGULAR")]
                self.assertEqual(run_cycle(sender, night), "WAIT_NEXT_M15_OPEN")
                snap.orders = [stop]
                journal.store.intents[key + ":cancel-after-flat"] = {"status": "ACK"}
                self.assertEqual(run_cycle(sender, night), "WAIT_NEXT_M15_OPEN")
                self.assertEqual(follow.call_count, 6)

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
                             ["FAULT_FINAM_HTTP_503", "FAULT_FINAM_SNAPSHOT_HTTP_400",
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
