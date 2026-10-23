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
from V20_TradingSystem_M15.v20_runtime.account_risk import AccountAuthority
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


    def money_authority(self, *, cash="200000", cost="50", step=None):
        binding = BINDINGS[self.entry.symbol]
        return AccountAuthority(
            self.broker.account_id, Decimal("500000"), Decimal(cash),
            Decimal(str(binding["price_step"] if step is None else step)),
            Decimal(str(binding["tick_value"])), Decimal("10000"), 1,
            Decimal(cost))

    def test_account_risk_reservation_is_durable_with_order_intent(self):
        with self.executor() as e:
            key = e.submit_entry(self.signal, self.entry,
                                 price_step=BINDINGS[self.entry.symbol]["price_step"],
                                 account_authority=self.money_authority())
            reservations = e.store.get("risk_reservations")
            self.assertIn(key, reservations)
            self.assertEqual(reservations[key]["account_id"], self.broker.account_id)
            self.assertEqual(int(reservations[key]["quantity"]),
                             e.store.get("execution_entries")[key]["quantity"])
            self.assertLessEqual(Decimal(reservations[key]["reserved_risk"]), Decimal("7500"))
            self.assertEqual(self.broker.post_count, 1)
        with self.executor() as e:
            self.assertIn(key, e.store.get("risk_reservations"))
            e.recover()
            self.assertEqual(self.broker.post_count, 1)

    def test_actual_slipped_fill_money_risk_and_protection(self):
        with self.executor() as e:
            key = e.submit_entry(self.signal, self.entry,
                                 price_step=BINDINGS[self.entry.symbol]["price_step"],
                                 account_authority=self.money_authority())
            qty = e.store.get("execution_entries")[key]["quantity"]
            self.fill_entry(key, quantity=qty, price="10.001")
            result = e.recover()
            self.assertEqual(result["reconciliation"], "RECONCILED")
            self.assertFalse(result["halt"])
            self.assertEqual(e.store.get("actual_fill_risk:" + key)["status"], "PASS")
            self.assertEqual(self.broker.orders[1]["sltp_order"]["quantity_sl"], {"value": "100"})
            self.assertEqual(self.broker.orders[1]["sltp_order"]["sl_price"], {"value": "9.975"})

    def test_missing_or_wrong_money_authority_blocks_before_post(self):
        with self.executor() as e:
            with self.assertRaisesRegex(ExecutionBlocked, "ACCOUNT_MONEY_PRICE_STEP_MISMATCH"):
                e.submit_entry(self.signal, self.entry,
                               price_step=BINDINGS[self.entry.symbol]["price_step"],
                               account_authority=self.money_authority(step="0.01"))
            self.assertEqual(self.broker.post_count, 0)

    def test_insufficient_money_capacity_blocks_before_post(self):
        with self.executor() as e:
            with self.assertRaisesRegex(ExecutionBlocked, "ACCOUNT_RISK_"):
                e.submit_entry(self.signal, self.entry,
                               price_step=BINDINGS[self.entry.symbol]["price_step"],
                               account_authority=self.money_authority(cash="0"))
            self.assertEqual(self.broker.post_count, 0)

    def test_legacy_unaccounted_position_cannot_share_money_budget(self):
        with self.executor() as e:
            key = self.submit(e)  # prior reference-only FakeBroker path
            sig, second = plan("SHALLOW_PULLBACK", "GLDRUBF",
                               at=datetime(2024, 1, 9, 11))
            binding = BINDINGS[second.symbol]
            authority = AccountAuthority(self.broker.account_id,
                Decimal("500000"), Decimal("200000"),
                Decimal(str(binding["price_step"])),
                Decimal(str(binding["tick_value"])), Decimal("10000"), 1, Decimal("50"))
            with self.assertRaisesRegex(ExecutionBlocked, "UNACCOUNTED_EXISTING_POSITION_RISK"):
                e.submit_entry(sig, second, price_step=binding["price_step"],
                               account_authority=authority)
            self.assertEqual(self.broker.post_count, 1)

    def strict_executor(self, cash="500000"):
        if self.broker.financials is None:
            self.broker.configure_funds(realized_equity="500000", available_cash=cash,
                margins={s: {"LONG": "10000", "SHORT": "15000"} for s in BINDINGS})
        return OfflineH1Executor(self.root, "v20-shallow", self.broker.account_id,
                                 self.broker, require_money_authority=True)

    def strict_submit(self, e, sig=None, entry=None):
        sig, entry = sig or self.signal, entry or self.entry
        return e.submit_entry(sig, entry, price_step=BINDINGS[entry.symbol]["price_step"],
                               account_authority=self.broker.authority(entry.symbol, entry.direction))

    def test_strict_money_required_and_sticky_across_legacy_constructor(self):
        with self.strict_executor() as e:
            with self.assertRaisesRegex(ExecutionBlocked, "MONEY_AUTHORITY_REQUIRED"):
                self.submit(e)
        with self.executor() as e:
            with self.assertRaisesRegex(ExecutionBlocked, "MONEY_AUTHORITY_REQUIRED"):
                self.submit(e)
        self.assertEqual(self.broker.post_count, 0)

    def test_fresh_broker_snapshot_does_not_double_subtract_go(self):
        with self.strict_executor() as e:
            first = self.strict_submit(e)
            sig, entry = plan("SHALLOW_PULLBACK", "GLDRUBF", at=datetime(2024, 1, 9, 11))
            evidence = self.broker.authority(entry.symbol, entry.direction)
            self.assertEqual(evidence.available_cash, Decimal("300000"))
            second = self.strict_submit(e, sig, entry)
            self.assertEqual(e.store.get("execution_entries")[second]["quantity"], 20)
            self.assertEqual(self.broker.financial_snapshot()["available_cash"], "100000")
            self.assertIn(compact_client_order_id(first), evidence.margin_reflected_client_ids)

    def test_stale_financial_snapshot_blocks_before_post(self):
        with self.strict_executor() as e:
            stale = self.broker.authority(self.entry.symbol, self.entry.direction)
            self.broker.configure_funds(realized_equity="500000", available_cash="0",
                                       margins=self.broker.financials["margins"])
            with self.assertRaisesRegex(ExecutionBlocked, "STALE_OR_UNVERIFIED"):
                e.submit_entry(self.signal, self.entry, price_step="0.001", account_authority=stale)
            self.assertEqual(self.broker.post_count, 0)

    def test_money_reserve_and_intent_rollback_together(self):
        with self.strict_executor() as e:
            with patch.object(e.store, "persist_intent", side_effect=RuntimeError("write failed")):
                with self.assertRaisesRegex(RuntimeError, "write failed"):
                    self.strict_submit(e)
            self.assertEqual(e.store.get("execution_entries", {}), {})
            self.assertEqual(e.store.get("risk_reservations", {}), {})
            self.assertEqual(e.store.get("risk_authorities", {}), {})
            self.assertEqual(e.journal.offline_snapshot(), [])
            self.assertEqual(self.broker.post_count, 0)

    def test_changed_partial_vwap_keeps_stop_blocks_entries_and_allows_exit(self):
        with self.strict_executor() as e:
            key = self.strict_submit(e); self.fill_entry(key, 2); e.recover()
            original = deepcopy(self.broker.orders[1])
            before = Decimal(e.store.get("risk_reservations")[key]["reserved_risk"])
            self.fill_entry(key, 2, "10.010")
            result = e.recover()
            self.assertEqual(result["halt"], "ACTUAL_FILL_STOP_UPDATE_UNCONFIRMED")
            self.assertEqual(original, self.broker.orders[1])
            self.assertEqual(self.broker.post_count, 2)
            self.assertGreater(Decimal(e.store.get("risk_reservations")[key]["reserved_risk"]), before)
            sig, entry = plan("SHALLOW_PULLBACK", "GLDRUBF", at=datetime(2024, 1, 9, 11))
            with self.assertRaisesRegex(ExecutionBlocked, "STOP_UPDATE_UNCONFIRMED"):
                self.strict_submit(e, sig, entry)
            e.request_frozen_exit(key)
            self.broker.fill(self.broker.orders[-1]["order_id"], key, 4, "10.000", "2024-01-11T09:00:00")
            e.recover()
            self.assertEqual(e.store.get("risk_reservations"), {})
            self.assertEqual(self.broker.orders[1]["status"], "CANCELLED")

    def test_reduced_money_quantity_is_idempotent_after_restart(self):
        with self.strict_executor(cash="50000") as e:
            key = self.strict_submit(e)
            self.assertEqual(e.store.get("execution_entries")[key]["quantity"], 4)
        with self.strict_executor() as e:
            self.assertEqual(self.strict_submit(e), key)
            self.assertEqual(self.broker.post_count, 1)

    def test_current_account_equity_r6_blocks_new_entries_keeps_stops(self):
        with self.strict_executor() as e:
            key = self.strict_submit(e); self.fill_entry(key, 20); e.recover()
            self.broker.configure_funds(realized_equity="5000", available_cash="500000",
                                       margins=self.broker.financials["margins"])
            result = e.recover()
            self.assertEqual(result["halt"], "ACCOUNT_INITIAL_RISK_EXCEEDS_R6")
            self.assertEqual(self.broker.orders[1]["status"], "NEW")
            sig, entry = plan("SHALLOW_PULLBACK", "GLDRUBF", at=datetime(2024, 1, 9, 11))
            with self.assertRaisesRegex(ExecutionBlocked, "ACCOUNT_INITIAL_RISK_EXCEEDS_R6"):
                self.strict_submit(e, sig, entry)
            e.request_frozen_exit(key)
            self.assertEqual(self.broker.orders[1]["status"], "NEW")

    def test_go_and_cost_reserve_fit_cash_and_paid_fee_is_not_reserved_twice(self):
        with self.strict_executor(cash="200000") as e:
            key = self.strict_submit(e)
            qty = e.store.get("execution_entries")[key]["quantity"]
            self.assertEqual(qty, 19)
            self.broker.fill(self.broker.orders[0]["order_id"], key, qty, "10",
                             "2024-01-09T10:15:00", fee=str(qty))
            e.recover()
            reserve = e.store.get("risk_reservations")[key]
            self.assertEqual(Decimal(reserve["reserved_cost"]), Decimal(qty))
            self.assertEqual(Decimal(self.broker.financial_snapshot()["available_cash"]), Decimal("9981"))
            self.assertEqual(Decimal(e.store.get("actual_fill_risk:"+key)["actual_risk"]), Decimal("532"))

    def test_unknown_fee_keeps_protection_and_does_not_disable_safe_exit(self):
        with self.strict_executor() as e:
            key = self.strict_submit(e)
            self.broker.fill(self.broker.orders[0]["order_id"], key, 1, "10",
                             "2024-01-09T10:15:00", fee="UNKNOWN")
            result = e.recover()
            self.assertIsNotNone(result["halt"])
            self.assertEqual(self.broker.orders[1]["status"], "NEW")
            e.request_frozen_exit(key)
            self.assertEqual(self.broker.orders[-1]["fake_kind"], "EXIT")
            self.assertEqual(self.broker.orders[1]["status"], "NEW")
