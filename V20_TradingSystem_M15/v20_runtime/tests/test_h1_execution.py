"""No sockets/tokens; actual H1 wire/readers/store against an explicit fake."""
from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from TradingSystemLab.stage8_robot.broker import compact_client_order_id
from TradingSystemLab.stage8_robot.production_broker_state import ProductionBrokerStateError
from V20_TradingSystem_M15.v20_runtime.h1_execution import (
    FakeBroker, OfflineH1Executor, ExecutionBlocked, LIVE_ENABLED,
)
from V20_TradingSystem_M15.v20_runtime.h1_state_journal import V20StateBoundaryError
from decimal import Decimal
from TradingSystemLab.stage8_robot.production_runtime import _load_registry
from V20_TradingSystem_M15.v20_runtime.offline_planner import FrozenSignal, OfflinePlanner

BINDINGS = _load_registry()


def plan(strategy, symbol="CNYRUBF", *, at, side=1):
    signal = FrozenSignal(strategy, symbol, side, at, Decimal("0.013"))
    entry = OfflinePlanner(strategy).reference_next_open(
        signal, at=at + timedelta(minutes=15),
        entry_open="10.00", realized_equity="500000",
        price_step=BINDINGS[symbol]["price_step"], tick_value=BINDINGS[symbol]["tick_value"],
        initial_margin="10000", available_cash="200000", trade_lot_size=1,
        cost_buffer_per_contract="50")
    return signal, entry


class H1ExecutionTests(TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)/"V20Lab"
        self.broker = FakeBroker("fake-shallow")
        self.signal, self.entry = plan("SHALLOW_PULLBACK", at=datetime(2024, 1, 9, 10))

    def executor(self, broker=None):
        return OfflineH1Executor(self.root, "v20-shallow", "fake-shallow", broker or self.broker)

    def submit(self, e):
        return e.submit_entry(self.signal, self.entry, price_step=BINDINGS[self.entry.symbol]["price_step"])

    def fill_entry(self, key, quantity=None, price="10.00"):
        oid = next(x["order_id"] for x in self.broker.orders
                   if x.get("order", {}).get("client_order_id") == compact_client_order_id(key))
        self.broker.fill(oid, key, self.entry.quantity if quantity is None else quantity,
                         price, "2024-01-09T10:15:00")

    def test_exact_fake_only_and_live_off(self):
        self.assertFalse(LIVE_ENABLED)
        for broker in (object(), FakeBroker("other")):
            with self.assertRaisesRegex(ExecutionBlocked, "EXACT_OFFLINE"):
                self.executor(broker)

    def test_entry_ack_is_not_fill_and_duplicate_is_not_resent(self):
        with self.executor() as e:
            key = self.submit(e)
            self.assertEqual(key, self.submit(e))
            self.assertEqual(self.broker.post_count, 1)
            self.assertEqual(e.store.get("remaining:"+key), 0)
            self.assertEqual(e.store.all_fills(), [])
            wire = self.broker.orders[0]["order"]
            self.assertEqual(wire["side"], "SIDE_BUY")
            self.assertEqual(wire["type"], "ORDER_TYPE_MARKET")
            self.assertEqual(wire["time_in_force"], "TIME_IN_FORCE_DAY")

    def test_partial_fill_installs_one_100_percent_stop_and_full_fill_reuses_it(self):
        with self.executor() as e:
            key = self.submit(e)
            self.fill_entry(key, 2)
            e.recover()
            stop = self.broker.orders[1]["sltp_order"]
            self.assertEqual(stop["quantity_sl"], {"value": "100"})
            self.assertEqual(stop["sl_qty_measure"], "SLTP_QTY_MEASURE_PERCENT")
            self.assertEqual(stop["sl_price"], {"value": "9.974"})
            self.assertEqual(stop["side"], "SIDE_SELL")
            self.assertNotIn("tp_price", stop)
            self.fill_entry(key, self.entry.quantity-2)
            e.recover()
            self.assertEqual(e.store.get("remaining:"+key), self.entry.quantity)
            self.assertEqual(self.broker.post_count, 2)

    def test_restart_restores_fills_position_stop_and_idempotency(self):
        with self.executor() as e:
            key = self.submit(e)
            self.fill_entry(key)
            e.recover()
        with self.executor() as e:
            self.assertEqual(e.recover()["positions"], {"CNYRUBF@RTSX": self.entry.quantity})
            self.assertEqual(self.submit(e), key)
            self.assertEqual(len(e.store.all_fills()), 1)
            self.assertEqual(self.broker.post_count, 2)

    def test_timeout_after_entry_accept_is_reconciled_without_retry(self):
        self.broker.next_fault = "timeout_after_accept"
        with self.executor() as e:
            key = self.submit(e)
            self.assertEqual(e.store.intent(key)["status"], "ACK")
        with self.executor() as e:
            self.submit(e)
            self.assertEqual(self.broker.post_count, 1)

    def test_uncertain_missing_entry_stays_blocked_after_restart(self):
        self.broker.next_fault = "timeout_before_accept"
        with self.executor() as e:
            with self.assertRaisesRegex(ExecutionBlocked, "UNCERTAIN_POST"):
                self.submit(e)
        with self.executor() as e:
            with self.assertRaisesRegex(ExecutionBlocked, "UNCERTAIN_POST"):
                self.submit(e)
        self.assertEqual(self.broker.post_count, 1)

    def test_stop_ack_lost_does_not_duplicate_protection(self):
        with self.executor() as e:
            key = self.submit(e); self.fill_entry(key, 1)
            self.broker.next_fault = "timeout_after_accept"
            e.recover(); e.recover()
            self.assertEqual(self.broker.post_count, 2)

    def test_stop_timeout_without_ack_blocks_no_blind_retry(self):
        with self.executor() as e:
            key = self.submit(e); self.fill_entry(key, 1)
            self.broker.next_fault = "timeout_before_accept"
            with self.assertRaisesRegex(ExecutionBlocked, "PROTECTION_UNCONFIRMED"):
                e.recover()
        with self.executor() as e:
            with self.assertRaisesRegex(ExecutionBlocked, "PROTECTION_UNCONFIRMED"):
                e.recover()
        self.assertEqual(self.broker.post_count, 2)

    def test_rejected_entry_is_terminal_without_retry(self):
        self.broker.next_fault = "rejected"
        with self.executor() as e:
            key = self.submit(e)
            self.assertEqual(e.store.intent(key)["status"], "REJECTED")
            self.submit(e)
            self.assertEqual(self.broker.post_count, 1)

    def test_unknown_order_and_duplicate_client_id_fail_closed(self):
        with self.executor() as e:
            self.submit(e)
            duplicate = deepcopy(self.broker.orders[0]); duplicate["order_id"] = "other"
            self.broker.orders.append(duplicate)
            with self.assertRaises(ProductionBrokerStateError):
                e.recover()
            duplicate["order"]["client_order_id"] = "unknown"
            with self.assertRaisesRegex(ExecutionBlocked, "UNKNOWN_BROKER_ORDER"):
                e.recover()

    def test_broker_wire_mismatch_cannot_be_adopted(self):
        with self.executor() as e:
            self.submit(e)
            self.broker.orders[0]["order"]["quantity"] = {"value": "999"}
            with self.assertRaisesRegex(ExecutionBlocked, "WIRE_MISMATCH"):
                e.recover()

    def test_unknown_broker_position_cannot_be_adopted(self):
        with self.executor() as e:
            snap = self.broker.snapshot()
            snap["positions"] = [dict(symbol="USDRUBF", quantity={"value": "1"})]
            with patch.object(self.broker, "snapshot", return_value=snap):
                with self.assertRaisesRegex(ExecutionBlocked, "UNKNOWN_BROKER_POSITION"):
                    e.recover()

    def test_incomplete_history_and_conflicting_fill_fail_closed(self):
        with self.executor() as e:
            key = self.submit(e); self.fill_entry(key); e.recover()
            self.broker.fills[0]["fee"] = "1"
            with self.assertRaisesRegex(RuntimeError, "CONFLICTING_DURABLE_FILL"):
                e.recover()
            self.broker.fills[0]["fee"] = "0"
            self.broker.fills.clear()
            with self.assertRaisesRegex(ExecutionBlocked, "FILL_HISTORY_INCOMPLETE"):
                e.recover()

    def test_slipped_fill_protected_but_further_entries_require_04_4(self):
        with self.executor() as e:
            key = self.submit(e); self.fill_entry(key, price="10.01")
            result = e.recover()
            self.assertEqual(result["halt"], "ACTUAL_FILL_RISK_REQUIRES_V20_04_4")
            self.assertEqual(self.broker.orders[1]["sltp_order"]["sl_price"], {"value": "9.984"})
            sig, entry = plan("SHALLOW_PULLBACK", "GLDRUBF", at=datetime(2024, 1, 9, 11))
            with self.assertRaisesRegex(ExecutionBlocked, "ACTUAL_FILL_RISK"):
                e.submit_entry(sig, entry, price_step=BINDINGS[entry.symbol]["price_step"])

    def test_frozen_exit_retains_stop_until_verified_flat_then_cancels(self):
        with self.executor() as e:
            key = self.submit(e); self.fill_entry(key); e.recover()
            e.request_frozen_exit(key)
            self.assertEqual(self.broker.orders[1]["status"], "NEW")
            exit_row = self.broker.orders[2]
            self.assertEqual(exit_row["order"]["side"], "SIDE_SELL")
            self.broker.fill(exit_row["order_id"], key, self.entry.quantity, "10.10", "2024-01-11T09:00:00")
            e.recover(); e.request_frozen_exit(key)
            self.assertEqual(self.broker.orders[1]["status"], "CANCELLED")
            self.assertEqual(e.store.intent(key)["status"], "CLOSED")
            self.assertEqual(self.broker.post_count, 3)

    def test_stop_execution_closes_position_without_reverse(self):
        with self.executor() as e:
            key = self.submit(e); self.fill_entry(key); e.recover()
            self.broker.fill(self.broker.orders[1]["order_id"], key, self.entry.quantity,
                             "9.974", "2024-01-09T10:30:00")
            self.assertEqual(e.recover()["positions"], {})
            self.assertEqual(e.store.intent(key)["status"], "CLOSED")

    def test_three_robots_use_independent_identity_state_and_side(self):
        ids = []
        for robot, strategy in (("shallow", "SHALLOW_PULLBACK"),
                                ("obv", "OBV_PRESSURE"), ("inside", "INSIDE_DAY_RELEASE")):
            broker = FakeBroker("fake-"+robot)
            signal, entry = plan(strategy, at=datetime(2024, 1, 9, 10), side=-1)
            with OfflineH1Executor(self.root, "v20-"+robot, broker.account_id, broker) as e:
                key = e.submit_entry(signal, entry, price_step=BINDINGS[entry.symbol]["price_step"])
                broker.fill(broker.orders[0]["order_id"], key, 1, "10", "2024-01-09T10:15:00")
                e.recover()
                self.assertEqual(broker.orders[1]["sltp_order"]["side"], "SIDE_BUY")
                self.assertEqual(broker.orders[1]["sltp_order"]["sl_price"], {"value": "10.026"})
                ids.append(key)
        self.assertEqual(len(set(ids)), 3)
        self.assertEqual(len(list(self.root.glob("*/state/v20-offline-execution.sqlite3"))), 3)

    def test_persistent_session_caps_and_wrong_account(self):
        with self.executor() as e:
            self.submit(e)
        with self.executor() as e:
            sig, entry = plan("SHALLOW_PULLBACK", "GLDRUBF", at=datetime(2024, 1, 9, 11))
            e.submit_entry(sig, entry, price_step=BINDINGS[entry.symbol]["price_step"])
            sig, entry = plan("SHALLOW_PULLBACK", "IMOEXF", at=datetime(2024, 1, 9, 12))
            with self.assertRaisesRegex(V20StateBoundaryError, "TWO_NEW_ENTRIES"):
                e.submit_entry(sig, entry, price_step=BINDINGS[entry.symbol]["price_step"])
        with self.assertRaisesRegex(V20StateBoundaryError, "ACCOUNT_OR_STRATEGY_MISMATCH"):
            OfflineH1Executor(self.root, "v20-shallow", "other", FakeBroker("other"))

    def test_pre_post_crash_restores_intent_without_resubmission(self):
        with self.executor() as e:
            with patch.object(self.broker, "submit", side_effect=KeyboardInterrupt):
                with self.assertRaises(KeyboardInterrupt):
                    self.submit(e)
        with self.executor() as e:
            with self.assertRaisesRegex(ExecutionBlocked, "UNCERTAIN_POST"):
                self.submit(e)
        self.assertEqual(self.broker.post_count, 0)

    def test_pending_unfilled_entry_blocks_same_symbol_next_session(self):
        with self.executor() as e:
            self.submit(e)
        with self.executor() as e:
            sig, entry = plan("SHALLOW_PULLBACK", at=datetime(2024, 1, 10, 10))
            with self.assertRaisesRegex(ExecutionBlocked, "ONE_OPEN_POSITION"):
                e.submit_entry(sig, entry, price_step="0.001")
            self.assertEqual(self.broker.post_count, 1)

    def test_ack_then_crash_is_reconciled_by_persisted_client_id(self):
        original = self.broker.submit
        def crash(*args, **kwargs):
            original(*args, **kwargs)
            raise KeyboardInterrupt()
        with self.executor() as e:
            with patch.object(self.broker, "submit", side_effect=crash):
                with self.assertRaises(KeyboardInterrupt):
                    self.submit(e)
        with self.executor() as e:
            self.submit(e)
            self.assertEqual(self.broker.post_count, 1)

    def test_filled_status_without_fill_authority_cannot_open_position(self):
        with self.executor() as e:
            self.submit(e)
            self.broker.orders[0]["status"] = "FILLED"
            with self.assertRaisesRegex(ExecutionBlocked, "FILL_HISTORY_INCONSISTENT"):
                e.recover()

    def test_reject_wrong_grid_or_changed_frozen_stop_before_post(self):
        with self.executor() as e:
            with self.assertRaisesRegex(ExecutionBlocked, "PRICE_STEP_MISMATCH"):
                e.submit_entry(self.signal, self.entry, price_step="0.01")
            changed = replace(self.entry, initial_stop=Decimal("9.90"))
            with self.assertRaisesRegex(ExecutionBlocked, "2_ATR_STOP_MISMATCH"):
                e.submit_entry(self.signal, changed, price_step="0.001")
            self.assertEqual(self.broker.post_count, 0)

    def test_rejected_protection_blocks_and_is_not_retransmitted(self):
        with self.executor() as e:
            key = self.submit(e); self.fill_entry(key, 1)
            self.broker.next_fault = "rejected"
            with self.assertRaisesRegex(ExecutionBlocked, "PROTECTION_OR_EXIT_REJECTED"):
                e.recover()
        with self.executor() as e:
            with self.assertRaisesRegex(ExecutionBlocked, "PROTECTION_UNCONFIRMED"):
                e.recover()
        self.assertEqual(self.broker.post_count, 2)
