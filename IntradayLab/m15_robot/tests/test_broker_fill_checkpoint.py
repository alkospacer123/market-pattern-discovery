"""M15 #14 synthetic-only FINAM GET -> independent SQLite fill recovery tests."""
from __future__ import annotations

import hashlib
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from fractions import Fraction
from pathlib import Path
from decimal import Decimal

from IntradayLab.m15_robot.broker_fill_readonly import ExpectedEntry
from IntradayLab.m15_robot.broker_fill_checkpoint import (
    M15BrokerFillCheckpointStore, M15FillCheckpointError,
)


def n(value):
    return {"value": str(value)}


class BrokerFillCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.args = dict(
            runtime_root=root / "m15", h1_runtime_root=root / "separate-h1",
            repository_root=root / "repo", m15_account_id="M15-SYNTH-ACCOUNT",
            h1_account_sha256=hashlib.sha256(b"OTHER-SYNTH-H1").hexdigest(),
        )
        self.store = M15BrokerFillCheckpointStore(**self.args)
        self.entry = ExpectedEntry(
            account_id="M15-SYNTH-ACCOUNT", order_id="broker-entry-1",
            symbol="CNYRUBF@RTSX", side="SIDE_BUY", quantity=2,
            price_step=Decimal("0.001"),
        )
        self.t0 = datetime(2026, 10, 19, 10, 30, tzinfo=timezone.utc)

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def evidence(self, *, filled=1, now=None, price2="12.501", account_id=None,
                 trade_id2="fill-2", missing_history=False):
        current_id = account_id or self.entry.account_id
        trades = [{"trade_id": "fill-1", "order_id": self.entry.order_id,
                   "account_id": current_id, "symbol": self.entry.symbol,
                   "side": self.entry.side, "currency": "XXX",
                   "timestamp": "2026-10-19T10:15:00Z", "price": n("12.500"),
                   "size": n(1)}]
        if filled == 2:
            trades.append({"trade_id": trade_id2, "order_id": self.entry.order_id,
                           "account_id": current_id, "symbol": self.entry.symbol,
                           "side": self.entry.side, "currency": "XXX",
                           "timestamp": "2026-10-19T10:16:00Z", "price": n(price2),
                           "size": n(1)})
        if filled == 0:
            trades = []
        account = {"account_id": current_id, "status": "ACCOUNT_ACTIVE",
                   "positions": [{"symbol": self.entry.symbol, "quantity": n(filled)}] if filled else []}
        orders = {"orders": [{"order_id": self.entry.order_id,
                             "status": "ORDER_STATUS_FILLED" if filled == 2 else
                                       "ORDER_STATUS_PARTIAL_FILL" if filled else "ORDER_STATUS_NEW",
                             "order": {"symbol": self.entry.symbol, "side": self.entry.side,
                                       "quantity": n(self.entry.quantity),
                                       "client_order_id": "m15check123456789"}}]}
        history = {"trades": trades}
        if missing_history:
            history["next_cursor"] = "pending"
        return dict(
            observed_at=now or self.t0, expected=self.entry,
            expected_client_order_id="m15check123456789",
            stop_trade_tag="trade-1", account=account, orders_response=orders,
            trades_response=history, start="2026-10-19T10:00:00Z",
            end="2026-10-19T11:00:00Z", limit=1000,
        )

    def test_partial_then_full_exact_offgrid_vwap_persists_after_restart(self):
        partial = self.store.observe(**self.evidence())
        self.assertEqual((partial.sequence, partial.filled_quantity), (1, 1))
        self.assertEqual(partial.exact_vwap, Fraction(25, 2))
        full = self.store.observe(**self.evidence(filled=2, now=self.t0 + timedelta(seconds=1)))
        self.assertEqual((full.sequence, full.filled_quantity), (2, 2))
        self.assertEqual(full.exact_vwap, Fraction(25001, 2000))
        self.assertFalse(full.live_authorized or full.broker_stop_acknowledged or
                         full.sqlite_trading_adoption_authorized)
        self.store.close()
        self.store = M15BrokerFillCheckpointStore(**self.args)
        same = self.store.observe(**self.evidence(filled=2, now=self.t0 + timedelta(seconds=2)))
        self.assertEqual(same.sequence, 2)
        self.assertFalse(same.newly_appended)

    def test_identical_history_is_idempotent(self):
        self.store.observe(**self.evidence())
        repeated = self.store.observe(**self.evidence(now=self.t0 + timedelta(seconds=1)))
        self.assertEqual(repeated.sequence, 1)
        self.assertFalse(repeated.newly_appended)

    def test_stale_or_shrunk_history_refused(self):
        self.store.observe(**self.evidence())
        with self.assertRaisesRegex(M15FillCheckpointError, "STALE_OR_SHRUNK"):
            self.store.observe(**self.evidence(now=self.t0 - timedelta(seconds=1)))
        self.store.observe(**self.evidence(filled=2, now=self.t0 + timedelta(seconds=2)))
        with self.assertRaisesRegex(M15FillCheckpointError, "STALE_OR_SHRUNK"):
            self.store.observe(**self.evidence(now=self.t0 + timedelta(seconds=3)))

    def test_same_fill_quantity_changed_ids_refused(self):
        self.store.observe(**self.evidence(filled=2))
        with self.assertRaisesRegex(M15FillCheckpointError, "EQUAL_QTY_CONFLICT"):
            self.store.observe(**self.evidence(filled=2, trade_id2="replacement-2",
                                               now=self.t0 + timedelta(seconds=1)))

    def test_wrong_account_never_writes(self):
        with self.assertRaisesRegex(RuntimeError, "ACCOUNT_BINDING"):
            self.store.observe(**self.evidence(account_id="FOREIGN-ACCOUNT"))
        count = self.store.db.execute("SELECT COUNT(*) FROM checkpoints").fetchone()[0]
        self.assertEqual(count, 0)

    def test_incomplete_broker_trade_history_never_writes(self):
        with self.assertRaisesRegex(RuntimeError, "COMPLETENESS_UNPROVEN"):
            self.store.observe(**self.evidence(missing_history=True))
        count = self.store.db.execute("SELECT COUNT(*) FROM checkpoints").fetchone()[0]
        self.assertEqual(count, 0)

    def test_restart_with_wrong_m15_account_denied(self):
        self.store.close()
        wrong = dict(self.args, m15_account_id="ANOTHER-M15-SYNTH")
        with self.assertRaisesRegex(M15FillCheckpointError, "ACCOUNT_BINDING_MISMATCH"):
            M15BrokerFillCheckpointStore(**wrong)
        self.store = M15BrokerFillCheckpointStore(**self.args)

    def test_no_fill_cannot_be_adopted(self):
        with self.assertRaisesRegex(M15FillCheckpointError, "BROKER_FILL_UNPROVEN"):
            self.store.observe(**self.evidence(filled=0))

    def test_no_live_transport_or_protective_ack_from_checkpoint(self):
        obj = self.store.observe(**self.evidence())
        self.assertFalse(self.store.execution_authorized)
        self.assertFalse(obj.broker_snapshot_freshness_proven)
        for name in ("submit", "send", "place_order", "cancel", "enable_task"):
            self.assertFalse(hasattr(self.store, name))


if __name__ == "__main__":
    unittest.main()
