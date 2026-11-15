"""Focused no-order TP6 / Protect3 contract tests (TRL-R060/R070)."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import unittest

from V20_TradingSystem_M15.v20_runtime.tp6_protect3 import (
    TP6Protect3Unsafe, levels_from_finam_fills, sltp_tp6_fields,
    review_completed_m15, place_or_replace_protect3_live,
)


class TP6Protect3OfflineTests(unittest.TestCase):
    def levels(self, side="LONG"):
        return levels_from_finam_fills(
            direction=side, fills=[(2, "100")], initial_stop="98" if side == "LONG" else "102",
            tick="0.1")

    def test_long_short_exact_6r_and_3r_trigger_and_1r_lock(self):
        long = self.levels("LONG")
        self.assertEqual((long.fill_quantity, long.fill_vwap, long.risk),
                         (2, Decimal("100"), Decimal("2")))
        self.assertEqual(long.take_profit, Decimal("112"))
        self.assertEqual(long.trigger_3r, Decimal("106"))
        self.assertEqual(long.locked_stop_1r, Decimal("102"))
        short = self.levels("SHORT")
        self.assertEqual(short.take_profit, Decimal("88"))
        self.assertEqual(short.trigger_3r, Decimal("94"))
        self.assertEqual(short.locked_stop_1r, Decimal("98"))

    def test_partial_fill_vwap_and_tick_rounding_preserve_minimum_6r(self):
        x = levels_from_finam_fills(
            direction="LONG", fills=[(1, "100.0"), (1, "100.1")],
            initial_stop="99.8", tick="0.1")
        self.assertEqual(x.fill_quantity, 2)
        self.assertEqual(x.fill_vwap, Decimal("100.05"))
        self.assertEqual(x.risk, Decimal("0.25"))
        self.assertEqual(x.take_profit, Decimal("101.6"))
        self.assertEqual(x.locked_stop_1r, Decimal("100.3"))
        self.assertGreaterEqual(x.take_profit - x.fill_vwap, 6 * x.risk)
        self.assertGreaterEqual(x.locked_stop_1r - x.fill_vwap, x.risk)
        short = levels_from_finam_fills(
            direction="SHORT", fills=[(1, "100.0"), (1, "100.1")],
            initial_stop="100.3", tick="0.1")
        self.assertEqual(short.risk, Decimal("0.25"))
        self.assertEqual(short.take_profit, Decimal("98.5"))
        self.assertEqual(short.locked_stop_1r, Decimal("99.8"))

    def test_full_position_broker_linked_tp_fields(self):
        self.assertEqual(sltp_tp6_fields(self.levels()), {
            "tp_price": {"value": "112"},
            "tp_qty_measure": "SLTP_QTY_MEASURE_PERCENT",
            "quantity_tp": {"value": "100"},
        })

    def test_invalid_fill_stop_grid_or_side_fails_closed(self):
        for arguments in (
            dict(direction="LONG", fills=[], initial_stop="98", tick="0.1"),
            dict(direction="LONG", fills=[(0, "100")], initial_stop="98", tick="0.1"),
            dict(direction="LONG", fills=[(1, "100")], initial_stop="98.01", tick="0.1"),
            dict(direction="LONG", fills=[(1, "100")], initial_stop="102", tick="0.1"),
            dict(direction="SELL", fills=[(1, "100")], initial_stop="98", tick="0.1"),
        ):
            with self.assertRaises(TP6Protect3Unsafe):
                levels_from_finam_fills(**arguments)

    def test_only_confirmed_completed_bar_may_trigger_next_m15(self):
        levels = self.levels()
        bar = datetime(2026, 11, 16, 10, 0)
        args = dict(levels=levels, m15_open_msk=bar,
                    high="107", low="104", active_stop="98",
                    broker_stop_proved=True, completed_bar_proved=True)
        early = review_completed_m15(
            **args, observed_utc=datetime(2026, 11, 16, 7, 14, tzinfo=timezone.utc))
        self.assertEqual(early.status, "M15_UNCONFIRMED_NO_CHANGE")
        due = review_completed_m15(
            **args, observed_utc=datetime(2026, 11, 16, 7, 15, tzinfo=timezone.utc))
        self.assertEqual(due.status, "LOCK_1R_DUE_NEXT_M15_BROKER_REPLACE_BLOCKED")
        self.assertEqual(due.proposed_stop, Decimal("102"))
        self.assertEqual(due.eligible_m15_open_msk, datetime(2026, 11, 16, 10, 15))
        self.assertEqual(review_completed_m15(
            **{**args, "completed_bar_proved": False},
            observed_utc=datetime(2026, 11, 16, 7, 15, tzinfo=timezone.utc)).status,
            "M15_UNCONFIRMED_NO_CHANGE")
        self.assertEqual(review_completed_m15(
            **{**args, "broker_stop_proved": False},
            observed_utc=datetime(2026, 11, 16, 7, 15, tzinfo=timezone.utc)).status,
            "BROKER_STOP_UNVERIFIED_NO_CHANGE")

    def test_stop_first_tp_first_and_already_protected_never_move_back(self):
        levels = self.levels()
        at = dict(levels=levels, m15_open_msk=datetime(2026, 11, 16, 10, 0),
                  observed_utc=datetime(2026, 11, 16, 7, 15, tzinfo=timezone.utc),
                  broker_stop_proved=True, completed_bar_proved=True)
        both = review_completed_m15(
            **at, high="113", low="97", active_stop="98")
        self.assertEqual(both.status, "M15_COULD_HAVE_EXITED_RECONCILE_BROKER")
        tp = review_completed_m15(
            **at, high="112.5", low="104", active_stop="98")
        self.assertEqual(tp.status, "M15_COULD_HAVE_EXITED_RECONCILE_BROKER")
        locked = review_completed_m15(
            **at, high="108", low="104", active_stop="102")
        self.assertEqual(locked.status, "ALREADY_LOCKED_NO_REGRESSION")
        short = review_completed_m15(
            levels=self.levels("SHORT"), m15_open_msk=datetime(2026, 11, 16, 10, 0),
            observed_utc=datetime(2026, 11, 16, 7, 15, tzinfo=timezone.utc),
            high="96", low="93", active_stop="102",
            broker_stop_proved=True, completed_bar_proved=True)
        self.assertEqual(short.proposed_stop, Decimal("98"))

    def test_live_replacement_is_explicitly_disabled(self):
        with self.assertRaisesRegex(TP6Protect3Unsafe,
                                    "FINAM_SLTP_NO_GAP_REPLACEMENT_NOT_PROVEN"):
            place_or_replace_protect3_live()
        with self.assertRaisesRegex(TP6Protect3Unsafe,
                                    "FINAM_SLTP_NO_GAP_REPLACEMENT_NOT_PROVEN"):
            place_or_replace_protect3_live(None, "synthetic", proof=True)


if __name__ == "__main__":
    unittest.main()
