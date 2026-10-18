"""Roadmap №18: combined offline fault/restart replay; NEVER a live broker.

Exercises existing M15 clocks, durable intents, FINAM GET-only adapter, and
broker evidence gates together. Every response/credential is synthetic.
No trade POST, H1 import, real token, existing runtime or Windows Task.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlparse

from IntradayLab.m15_robot.broker_fill_readonly import ExpectedEntry
from IntradayLab.m15_robot.broker_snapshot import ProductionBrokerStateError
from IntradayLab.m15_robot.broker_reconcile_gate import (
    M15ReconcileGateError, assess_entry_evidence,
)
from IntradayLab.m15_robot.finam_readonly import M15FinamReadOnlyAPI, M15FinamReadOnlyError
from IntradayLab.m15_robot.offline_intents import OfflineIntentLedger, M15OfflineLedgerError
from IntradayLab.m15_robot.service_clock import M15OfflineClock, M15ClockError
from IntradayLab.m15_robot.protective_gate import BrokerProtection, decide_protection


NOW = datetime(2026, 10, 18, 10, 30, tzinfo=timezone.utc)
ENTRY = "m15:offline-fault-01"
ACCOUNT = "M15-SYNTH"
SYMBOL = "USDRUBF@RTSX"


class JsonReply:
    status = 200

    def __init__(self, payload):
        self.payload = payload

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class SyntheticFinam:
    """Only two session-auth POSTs. All other injected events are GETs."""

    def __init__(self, failures=()):
        self.failures = tuple(failures)
        self.calls = []
        self.target_calls = 0

    def __call__(self, req, timeout):
        method, path = req.get_method(), urlparse(req.full_url).path
        self.calls.append((method, path))
        if path == "/v1/sessions":
            return JsonReply({"token": "synthetic-not-a-real-jwt"})
        if path == "/v1/sessions/details":
            return JsonReply({"readonly": True, "account_ids": [ACCOUNT]})
        self.target_calls += 1
        if self.target_calls <= len(self.failures):
            code = self.failures[self.target_calls - 1]
            if code == "TIMEOUT":
                raise TimeoutError("synthetic timeout")
            raise HTTPError(req.full_url, code, "synthetic", None, None)
        if path.endswith("/trades"):
            return JsonReply({"trades": []})
        if path.endswith("/orders"):
            return JsonReply({"orders": []})
        return JsonReply({"account_id": ACCOUNT, "status": "ACCOUNT_ACTIVE", "positions": []})


def broker_entry(status="ORDER_STATUS_NEW"):
    return {
        "order_id": "broker-synthetic-01", "status": status,
        "order": {"symbol": SYMBOL, "client_order_id": "m15synthetic01",
                  "side": "SIDE_BUY", "quantity": {"value": "2"}},
    }


def expected():
    return ExpectedEntry(ACCOUNT, "broker-synthetic-01", SYMBOL,
                         "SIDE_BUY", 2, Decimal("0.01"))


class FailureRecoveryReplay(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        base = Path(self.temp.name)
        self.opts = {
            "runtime_root": base / "m15",
            "h1_runtime_root": base / "h1",
            "repository_root": base / "code",
            "m15_account_id": ACCOUNT,
            "h1_account_sha256": hashlib.sha256(b"OTHER-H1-SYNTH").hexdigest(),
        }
        self.ledger = OfflineIntentLedger(**self.opts)
        self.base = base

    def tearDown(self):
        self.ledger.close()
        self.temp.cleanup()

    def prepare_uncertain(self):
        self.assertTrue(self.ledger.prepare(
            key=ENTRY, instrument="USDRUBF", direction="LONG", quantity=2,
        ))
        self.ledger.uncertain(ENTRY)

    def connect(self, transport):
        api = M15FinamReadOnlyAPI(
            secret="synthetic-no-real-token", account_id=ACCOUNT,
            transport=transport, sleeper=lambda _: None,
        )
        api.connect_readonly()
        self.assertTrue(api.readonly_bound)
        return api

    def test_post_timeout_uncertain_restart_does_not_resubmit(self):
        self.prepare_uncertain()
        self.ledger.close()
        self.ledger = OfflineIntentLedger(**self.opts)
        self.assertEqual(self.ledger.intent(ENTRY)["status"], "UNCERTAIN")
        self.assertFalse(self.ledger.prepare(
            key=ENTRY, instrument="USDRUBF", direction="LONG", quantity=2,
        ))
        with self.assertRaisesRegex(M15OfflineLedgerError, "OCCUPIED"):
            self.ledger.prepare(key="m15:second", instrument="USDRUBF",
                                direction="LONG", quantity=2)
        self.assertEqual(self.ledger.filled_quantity(ENTRY), 0)
        self.assertFalse(self.ledger.execution_authorized)

    def test_broker_history_400_halts_uncertain_with_no_fill(self):
        self.prepare_uncertain()
        fake = SyntheticFinam((400,))
        api = self.connect(fake)
        with self.assertRaisesRegex(M15FinamReadOnlyError, "TRADES_STATUS_400"):
            api.trades(ACCOUNT, start="2026-10-18T07:00:00Z",
                       end="2026-10-18T08:00:00Z")
        self.assertEqual(fake.target_calls, 1)
        self.assertEqual(self.ledger.intent(ENTRY)["status"], "UNCERTAIN")
        self.assertEqual(self.ledger.filled_quantity(ENTRY), 0)
        self.assertTrue(all(m == "GET" for m, _ in fake.calls[2:]))

    def test_broker_history_404_halts_without_fake_ack(self):
        self.prepare_uncertain()
        fake = SyntheticFinam((404,))
        api = self.connect(fake)
        with self.assertRaisesRegex(M15FinamReadOnlyError, "TRADES_STATUS_404"):
            api.trades(ACCOUNT, start="2026-10-18T07:00:00Z",
                       end="2026-10-18T08:00:00Z")
        self.assertEqual(fake.target_calls, 1)
        self.assertEqual(self.ledger.intent(ENTRY)["status"], "UNCERTAIN")
        self.assertEqual(self.ledger.filled_quantity(ENTRY), 0)

    def test_broker_history_429_twice_halts_after_bounded_retry(self):
        self.prepare_uncertain()
        fake = SyntheticFinam((429, 429))
        api = self.connect(fake)
        with self.assertRaisesRegex(M15FinamReadOnlyError, "TRADES_STATUS_429"):
            api.trades(ACCOUNT, start="2026-10-18T07:00:00Z",
                       end="2026-10-18T08:00:00Z")
        self.assertEqual(fake.target_calls, 2)
        self.assertEqual(self.ledger.filled_quantity(ENTRY), 0)
        self.assertEqual(self.ledger.intent(ENTRY)["status"], "UNCERTAIN")

    def test_timeout_broker_get_twice_never_changes_intent(self):
        self.prepare_uncertain()
        fake = SyntheticFinam(("TIMEOUT", "TIMEOUT"))
        api = self.connect(fake)
        with self.assertRaisesRegex(M15FinamReadOnlyError, "TRANSPORT_OR_JSON"):
            api.orders(ACCOUNT)
        self.assertEqual(fake.target_calls, 2)
        self.assertEqual(self.ledger.intent(ENTRY)["status"], "UNCERTAIN")
        self.assertEqual(self.ledger.filled_quantity(ENTRY), 0)

    def test_broker_no_matching_fills_but_position_denied(self):
        with self.assertRaisesRegex(M15ReconcileGateError, "POSITION_FILL_DIVERGENCE"):
            assess_entry_evidence(
                account={"account_id": ACCOUNT, "status": "ACCOUNT_ACTIVE",
                         "positions": [{"symbol": SYMBOL, "quantity": {"value": "2"}}]},
                orders_response={"orders": [broker_entry()]},
                trades_response={"trades": []}, expected=expected(),
                expected_client_order_id="m15synthetic01",
                stop_trade_tag="offline-fault", start="2026-10-18T07:00:00Z",
                end="2026-10-18T08:00:00Z",
            )
        self.assertEqual(self.ledger.db.execute("SELECT COUNT(*) FROM fills").fetchone()[0], 0)

    def test_broker_foreign_account_denied_before_order_adoption(self):
        with self.assertRaisesRegex(M15ReconcileGateError, "ACCOUNT_BINDING"):
            assess_entry_evidence(
                account={"account_id": "OTHER-H1-SYNTH", "status": "ACCOUNT_ACTIVE",
                         "positions": []},
                orders_response={"orders": [broker_entry()]},
                trades_response={"trades": []}, expected=expected(),
                expected_client_order_id="m15synthetic01",
                stop_trade_tag="offline-fault", start="2026-10-18T07:00:00Z",
                end="2026-10-18T08:00:00Z",
            )

    def test_malformed_broker_order_status_is_not_adopted(self):
        with self.assertRaisesRegex(ProductionBrokerStateError, "ORDER_STATUS"):
            assess_entry_evidence(
                account={"account_id": ACCOUNT, "status": "ACCOUNT_ACTIVE",
                         "positions": []},
                orders_response={"orders": [broker_entry("ORDER_STATUS_INVENTED")]},
                trades_response={"trades": []}, expected=expected(),
                expected_client_order_id="m15synthetic01",
                stop_trade_tag="offline-fault", start="2026-10-18T07:00:00Z",
                end="2026-10-18T08:00:00Z",
            )

    def test_sqlite_mid_fill_abort_rolls_back_then_restart(self):
        self.assertTrue(self.ledger.prepare(
            key=ENTRY, instrument="USDRUBF", direction="LONG", quantity=2))
        self.ledger.synthetic_ack(ENTRY, "sim-order-1")
        with self.ledger.db:
            self.ledger.db.execute(
                "CREATE TRIGGER simulated_crash BEFORE INSERT ON fills "
                "BEGIN SELECT RAISE(ABORT,'synthetic sqlite fault'); END"
            )
        with self.assertRaises(sqlite3.DatabaseError):
            self.ledger.synthetic_fill(
                key=ENTRY, fill_id="sim-fill-1",
                broker_order_id="sim-order-1", quantity=1, price="100")
        self.assertEqual(self.ledger.filled_quantity(ENTRY), 0)
        self.assertEqual(self.ledger.intent(ENTRY)["status"], "ACK")
        self.ledger.close()
        self.ledger = OfflineIntentLedger(**self.opts)
        self.assertEqual(self.ledger.filled_quantity(ENTRY), 0)
        with self.ledger.db:
            self.ledger.db.execute("DROP TRIGGER simulated_crash")
        self.assertTrue(self.ledger.synthetic_fill(
            key=ENTRY, fill_id="sim-fill-1",
            broker_order_id="sim-order-1", quantity=1, price="100"))
        self.assertEqual(self.ledger.filled_quantity(ENTRY), 1)

    def test_sqlite_restart_with_lost_identity_fails_closed(self):
        self.ledger.close()
        with sqlite3.connect(self.ledger.path) as db:
            db.execute("DELETE FROM metadata WHERE key='identity'")
        with self.assertRaisesRegex(M15OfflineLedgerError, "EXISTING_IDENTITY_MISSING"):
            OfflineIntentLedger(**self.opts)
        self.ledger.path.unlink()
        self.ledger = OfflineIntentLedger(**self.opts)
        self.assertFalse(self.ledger.execution_authorized)

    def test_future_or_stale_close_cannot_advance_valid_watermark(self):
        prior = NOW - timedelta(minutes=15)
        bars = {"USDRUBF": [prior], "CNYRUBF": [], "GLDRUBF": [], "IMOEXF": []}
        clock = M15OfflineClock(
            root=self.base / "m15-clock", completed=lambda symbol, _: bars[symbol],
            clock=lambda: NOW,
        )
        self.assertEqual(len(clock.once()["advanced"]), 1)
        saved = (self.base / "m15-clock" / "state" /
                 "m15-offline-service-clock.json").read_bytes()
        bars["USDRUBF"] = [NOW + timedelta(minutes=15)]
        with self.assertRaisesRegex(M15ClockError, "FUTURE_CLOSE"):
            clock.once()
        self.assertEqual(
            (self.base / "m15-clock" / "state" /
             "m15-offline-service-clock.json").read_bytes(), saved)
        bars["USDRUBF"] = [prior]
        self.assertEqual(len(clock.once()["advanced"]), 0)

    def test_missing_sltp_after_broker_fill_requires_install_no_entry(self):
        decision = decide_protection(
            direction="LONG", actual_entry=Decimal("100"),
            atr=Decimal("2"), price_step=Decimal("1"),
            broker_position_qty=2, broker_stop=None, broker_stop_count=0,
        )
        self.assertEqual(decision.action, "INSTALL_REQUIRED")
        self.assertFalse(decision.new_entries_authorized)
        self.assertFalse(decision.live_submission_authorized)

    def test_partial_fill_beyond_old_sltp_cover_requires_replacement(self):
        old = BrokerProtection(
            broker_order_id="sim-stop-1", stop_price=Decimal("96"),
            percent=100, covered_quantity_at_ack=1, active=True,
        )
        decision = decide_protection(
            direction="LONG", actual_entry=Decimal("100"),
            atr=Decimal("2"), price_step=Decimal("1"),
            broker_position_qty=2, broker_stop=old, broker_stop_count=1,
        )
        self.assertEqual(decision.action, "REPLACE_REQUIRED_COVERAGE")
        self.assertTrue(decision.old_stop_must_remain)
        self.assertFalse(decision.new_entries_authorized)

    def test_recovery_replay_does_not_expose_execution_api(self):
        self.assertFalse(hasattr(self.ledger, "place_order"))
        self.assertFalse(hasattr(self.ledger, "cancel_order"))
        self.assertTrue(self.ledger.unsafe_for_live())


if __name__ == "__main__":
    unittest.main()
