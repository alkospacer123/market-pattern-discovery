"""Synthetic GET-only H1-derived FINAM broker/SQLite guard regression suite.

No account secrets, network access, orders, live file paths or Windows tasks.
"""
import hashlib
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from IntradayLab.m15_robot.broker_status import normalize_order_status
from IntradayLab.m15_robot.broker_snapshot import (
    ProductionBrokerStateError, order_views, position_quantities,
)
from IntradayLab.m15_robot.shadow_state import ShadowLedger, ShadowStateError
from IntradayLab.m15_robot.shadow_service import (
    ShadowObservationError, observe_broker_once,
)


def qty(value):
    return {"value": str(value)}


def account(account_id="M15-ACCOUNT", positions=None):
    return {
        "account_id": account_id, "status": "ACCOUNT_ACTIVE",
        "positions": [] if positions is None else positions,
    }


def order(status="ORDER_STATUS_NEW", kind="REGULAR", symbol="USDRUBF@RTSX"):
    payload = {
        "symbol": symbol, "client_order_id": "m15shadow0001",
        "side": "SIDE_SELL",
    }
    if kind == "REGULAR":
        payload["quantity"] = qty(1)
        return {"order_id": "test-order-1", "status": status, "order": payload}
    payload.update({
        "comment": "m15:trade-1:stop:0",
        "sl_qty_measure": "SLTP_QTY_MEASURE_PERCENT",
        "quantity_sl": qty(100),
        "sl_price": qty("100"),
        "valid_before": "VALID_BEFORE_GOOD_TILL_CANCEL",
    })
    return {"order_id": "test-order-1", "status": status, "sltp_order": payload}


class FakeReadPort:
    def __init__(self, snapshot=None, orders=None):
        self.snapshot = snapshot or account()
        self.order_rows = [] if orders is None else orders
        self.read_calls = 0
        self.order_calls = 0

    def account(self, identifier):
        self.read_calls += 1
        return self.snapshot

    def orders(self, identifier):
        self.read_calls += 1
        return {"orders": self.order_rows}

    def place_order(self, *args, **kwargs):
        self.order_calls += 1
        raise AssertionError("REAL_ORDER_WAS_CALLED")

    def cancel_order(self, *args, **kwargs):
        self.order_calls += 1
        raise AssertionError("CANCEL_WAS_CALLED")


class BrokerParsing(unittest.TestCase):
    def test_zero_quantity_position_means_flat(self):
        self.assertEqual(position_quantities(account(positions=[
            {"symbol": "USDRUBF@RTSX", "quantity": qty(0)},
        ])), {})

    def test_nonzero_position_is_exposure(self):
        self.assertEqual(position_quantities(account(positions=[
            {"symbol": "USDRUBF@RTSX", "quantity": qty(-2)},
        ])), {"USDRUBF@RTSX": -2})

    def test_duplicate_position_symbol_rejected(self):
        with self.assertRaisesRegex(ProductionBrokerStateError, "POSITIONS_SCHEMA"):
            position_quantities(account(positions=[
                {"symbol": "USDRUBF@RTSX", "quantity": qty(1)},
                {"symbol": "USDRUBF@RTSX", "quantity": qty(1)},
            ]))

    def test_malformed_fractional_position_rejected(self):
        with self.assertRaisesRegex(ProductionBrokerStateError, "POSITION_QUANTITY"):
            position_quantities(account(positions=[
                {"symbol": "USDRUBF@RTSX", "quantity": qty("1.5")},
            ]))

    def test_regular_and_sltp_status_parse(self):
        self.assertTrue(order_views({"orders": [order()]})[0].active)
        self.assertEqual(order_views({"orders": [order(kind="SLTP")]})[0].kind, "SLTP")
        self.assertFalse(order_views({"orders": [order(status="ORDER_STATUS_FILLED")]})[0].active)

    def test_unknown_order_status_fails_closed(self):
        with self.assertRaises(ProductionBrokerStateError):
            order_views({"orders": [order(status="INVENTED_LIVE_STATUS")]})

    def test_unspecified_status_fails_closed(self):
        with self.assertRaises(ValueError):
            normalize_order_status("ORDER_STATUS_UNSPECIFIED")

    def test_duplicate_broker_order_id_fails(self):
        with self.assertRaises(ProductionBrokerStateError):
            order_views({"orders": [order(), order()]})


class ShadowIntegration(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        self.opts = {
            "runtime_root": d / "m15", "h1_runtime_root": d / "h1",
            "repository_root": d / "repo",
            "m15_account_id": "M15-ACCOUNT",
            "h1_account_sha256": hashlib.sha256(b"H1-ACCOUNT").hexdigest(),
        }
        self.store = ShadowLedger(**self.opts)
        self.at = datetime(2026, 10, 16, 8, 0, tzinfo=timezone.utc)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_clean_broker_records_readonly_halted_receipt(self):
        # The staged SQLite file must be closed and unlinked on Windows.
        # A leaked sqlite3.Connection holds .pending open (WinError 32).
        self.assertEqual(
            list(self.store.path.parent.glob(".m15-shadow-readonly.sqlite3*.pending")), []
        )
        broker = FakeReadPort()
        report = observe_broker_once(
            ledger=self.store, read_api=broker,
            m15_account_id="M15-ACCOUNT", observed_at=self.at,
        )
        self.assertEqual(report["status"], "HEALTHY_READONLY")
        self.assertEqual(report["cycle"], 1)
        self.assertTrue(report["halted"])
        self.assertFalse(report["execution_authorized"])
        self.assertFalse(report["entries_enabled"])
        self.assertEqual(broker.read_calls, 2)
        self.assertEqual(broker.order_calls, 0)
        self.assertEqual(self.store.latest()["status"], "HEALTHY_READONLY")

    def test_restart_keeps_identity_and_cycle_sequence(self):
        broker = FakeReadPort()
        observe_broker_once(ledger=self.store, read_api=broker,
                            m15_account_id="M15-ACCOUNT", observed_at=self.at)
        self.store.close()
        self.store = ShadowLedger(**self.opts)
        nxt = observe_broker_once(
            ledger=self.store, read_api=broker,
            m15_account_id="M15-ACCOUNT", observed_at=self.at + timedelta(seconds=30),
        )
        self.assertEqual(nxt["cycle"], 2)
        self.assertEqual(broker.order_calls, 0)

    def test_unknown_live_position_fault_halts(self):
        broker = FakeReadPort(snapshot=account(positions=[
            {"symbol": "USDRUBF@RTSX", "quantity": qty(1)},
        ]))
        with self.assertRaisesRegex(ShadowObservationError, "FOREIGN_EXPOSURE"):
            observe_broker_once(ledger=self.store, read_api=broker,
                                m15_account_id="M15-ACCOUNT", observed_at=self.at)
        self.assertEqual(self.store.latest()["status"], "FAULT_HALTED")
        self.assertEqual(broker.order_calls, 0)

    def test_active_sltp_without_owned_position_faults(self):
        broker = FakeReadPort(orders=[order(kind="SLTP")])
        with self.assertRaisesRegex(ShadowObservationError, "FOREIGN_EXPOSURE"):
            observe_broker_once(ledger=self.store, read_api=broker,
                                m15_account_id="M15-ACCOUNT", observed_at=self.at)
        self.assertEqual(self.store.latest()["status"], "FAULT_HALTED")
        self.assertEqual(broker.order_calls, 0)

    def test_missing_orders_view_blocks(self):
        broker = FakeReadPort()
        broker.orders = lambda account_id: {"orders": None}
        with self.assertRaises(ShadowObservationError):
            observe_broker_once(ledger=self.store, read_api=broker,
                                m15_account_id="M15-ACCOUNT", observed_at=self.at)
        self.assertEqual(self.store.latest()["status"], "FAULT_HALTED")

    def test_account_reply_wrong_binding_blocks(self):
        broker = FakeReadPort(snapshot=account(account_id="H1-ACCOUNT"))
        with self.assertRaisesRegex(ShadowObservationError, "ACCOUNT_OR_STATUS_INVALID"):
            observe_broker_once(ledger=self.store, read_api=broker,
                                m15_account_id="M15-ACCOUNT", observed_at=self.at)

    def test_m15_id_swapped_blocks_before_broker(self):
        broker = FakeReadPort()
        with self.assertRaisesRegex(ShadowObservationError, "ACCOUNT_MISMATCH"):
            observe_broker_once(ledger=self.store, read_api=broker,
                                m15_account_id="H1-ACCOUNT", observed_at=self.at)
        self.assertEqual(broker.read_calls, 0)

    def test_replayed_timestamp_never_appends_again(self):
        broker = FakeReadPort()
        for _ in range(1):
            observe_broker_once(ledger=self.store, read_api=broker,
                                m15_account_id="M15-ACCOUNT", observed_at=self.at)
        with self.assertRaisesRegex(ShadowStateError, "STALE_OR_REPEATED"):
            observe_broker_once(ledger=self.store, read_api=broker,
                                m15_account_id="M15-ACCOUNT", observed_at=self.at)
        self.assertEqual(self.store.latest()["cycle"], 1)

    def test_sqlite_forged_identity_refused_on_restart(self):
        self.store.close()
        with sqlite3.connect(self.store.path) as con:
            con.execute("UPDATE authority SET value='{}' WHERE key='identity'")
        with self.assertRaisesRegex(ShadowStateError, "IDENTITY_MISMATCH"):
            ShadowLedger(**self.opts)
        # Restore our test store handle for tearDown.
        with sqlite3.connect(self.store.path) as con:
            import json
            con.execute("UPDATE authority SET value=? WHERE key='identity'",
                        (json.dumps(self.store.identity, sort_keys=True),))
        self.store = ShadowLedger(**self.opts)

    def test_sqlite_contains_no_raw_account_id(self):
        broker = FakeReadPort()
        observe_broker_once(ledger=self.store, read_api=broker,
                            m15_account_id="M15-ACCOUNT", observed_at=self.at)
        raw = self.store.path.read_bytes()
        self.assertNotIn(b"M15-ACCOUNT", raw)
        self.assertNotIn(b"H1-ACCOUNT", raw)


if __name__ == "__main__":
    unittest.main()
