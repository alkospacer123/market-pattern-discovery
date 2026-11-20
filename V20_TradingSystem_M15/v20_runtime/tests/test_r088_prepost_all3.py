"""R088 pre-POST recovery: minimal mock of durable never-sent intent on N4."""
from __future__ import annotations
import unittest
from contextlib import contextmanager
from types import SimpleNamespace
from V20_TradingSystem_M15.v20_runtime.finam_live import _resolve_never_posted_entry


class Store:
    def __init__(self, key):
        self.key = key
        self.row = {"status": "INTENT_PERSISTED", "broker_order_id": None}
        self.states = {"risk_reservations": {key: {"quantity": 1}}}

    def intent(self, key):
        return dict(self.row) if key == self.key else None

    def get(self, key, default=None):
        return self.states.get(key, default)

    @contextmanager
    def transaction(self):
        yield

    def transition_intent(self, key, status):
        assert key == self.key
        self.row["status"] = status

    def put(self, key, value):
        self.states[key] = value


class Journal:
    account_hash = "a" * 64

    def __init__(self, key):
        self.store = Store(key)
        self.checked = 0

    def reconcile_order(self, *, key, snapshot):
        self.checked += 1
        assert key == self.store.key and not snapshot.positions and not snapshot.orders
        return "PREPARED_ONLY_NO_POST"


class PrePostAll3Tests(unittest.TestCase):
    def test_all_three_can_resolve_never_sent_entry(self):
        for robot in ("v20-shallow", "v20-obv", "v20-inside"):
            with self.subTest(robot=robot):
                key = f"v20:{robot}:aaaa:entry"
                journal = Journal(key)
                snapshot = SimpleNamespace(positions={}, orders=())
                payload = {"finam_symbol": "USDRUBF@RTSX"}
                self.assertTrue(_resolve_never_posted_entry(journal, snapshot, key, payload))
                self.assertEqual(journal.checked, 1)
                self.assertEqual(journal.store.row["status"], "CANCELLED")
                self.assertEqual(journal.store.get("flat_cleanup:" + key)["status"],
                                 "PREPOST_ABORT_NO_FINAM_ORDER")
                self.assertNotIn(key, journal.store.get("risk_reservations"))

    def test_unknown_post_or_active_broker_exposure_never_cleared(self):
        for flag in ("live_post", "entry_submission", "broker_id", "position", "order"):
            with self.subTest(flag=flag):
                key = "v20:v20-inside:aaaa:entry"
                journal = Journal(key)
                snapshot = SimpleNamespace(positions={}, orders=())
                if flag == "live_post":
                    journal.store.put("live_post:" + key, "CONSUMED")
                elif flag == "entry_submission":
                    journal.store.put("entry_submission:" + key, {"submitted_at": "x"})
                elif flag == "broker_id":
                    journal.store.row["broker_order_id"] = "FINAM-ACK"
                elif flag == "position":
                    snapshot.positions["USDRUBF@RTSX"] = 1
                else:
                    snapshot.orders = (SimpleNamespace(active=True, symbol="USDRUBF@RTSX"),)
                self.assertFalse(_resolve_never_posted_entry(
                    journal, snapshot, key, {"finam_symbol": "USDRUBF@RTSX"}))
                self.assertEqual(journal.checked, 0)
                self.assertEqual(journal.store.row["status"], "INTENT_PERSISTED")


if __name__ == "__main__":
    unittest.main()
