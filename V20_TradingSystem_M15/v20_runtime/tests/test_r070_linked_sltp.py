"""R070 linked SL+TP6 pure contract: one active 100%-percent broker order."""
from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
import unittest

from TradingSystemLab.stage8_robot.production_broker_state import BrokerOrderView
from TradingSystemLab.stage8_robot.production_runtime import RuntimeAction
from V20_TradingSystem_M15.v20_runtime.tp6_protect3 import (
    TP6Protect3Unsafe, levels_from_finam_fills,
)
from V20_TradingSystem_M15.v20_runtime.r070_linked_sltp import (
    prepare_r070_linked_sltp_draft, verify_r070_linked_sltp,
)


class R070LinkedSltpTests(unittest.TestCase):
    def fixture(self, direction="LONG"):
        stop = "98" if direction == "LONG" else "102"
        levels = levels_from_finam_fills(
            direction=direction, fills=[(1, "100"), (1, "100")],
            initial_stop=stop, tick="0.1")
        action = RuntimeAction(
            "PROTECTIVE_STOP_INSTALL", "v20:shallow:acct:entry:stop",
            "USDRUBF", "USDRUBF@FUT", direction, 2,
            "entry", None, Decimal("100"), Decimal(stop),
            2 if direction == "LONG" else -2,
        )
        wire = prepare_r070_linked_sltp_draft(action=action, levels=levels)
        order = BrokerOrderView(
            "order-123", "WATCHING", True, "SLTP",
            wire["symbol"], wire["client_order_id"], wire["comment"],
            wire["side"], wire.copy(),
        )
        return levels, action, wire, order

    def test_single_linked_sltp_has_two_100pct_parts_and_6r(self):
        for direction in ("LONG", "SHORT"):
            levels, action, wire, order = self.fixture(direction)
            self.assertEqual(wire["quantity_sl"], {"value": "100"})
            self.assertEqual(wire["quantity_tp"], {"value": "100"})
            self.assertEqual(wire["tp_qty_measure"], "SLTP_QTY_MEASURE_PERCENT")
            self.assertEqual(wire["sl_qty_measure"], "SLTP_QTY_MEASURE_PERCENT")
            self.assertEqual(wire["tp_price"]["value"], str(levels.take_profit))
            self.assertEqual(wire["sl_price"]["value"], str(levels.initial_stop))
            self.assertEqual(verify_r070_linked_sltp(
                observed_position=2 if direction == "LONG" else -2,
                orders=(order,), levels=levels, wire=wire,
                expected_broker_order_id="order-123"), order)

    def test_watch_stop_without_client_id_recovers_only_with_proved_broker_id(self):
        levels, _, wire, order = self.fixture()
        watch = replace(order, client_order_id="")
        self.assertEqual(verify_r070_linked_sltp(
            observed_position=2, orders=(watch,), levels=levels,
            wire=wire, expected_broker_order_id="order-123"), watch)
        with self.assertRaises(TP6Protect3Unsafe):
            verify_r070_linked_sltp(
                observed_position=2, orders=(watch,), levels=levels,
                wire=wire, expected_broker_order_id="different")

    def test_duplicate_or_missing_order_never_counts_as_protection(self):
        levels, _, wire, order = self.fixture()
        for orders in (tuple(), (replace(order, active=False),),
                       (order, replace(order, order_id="another", comment="different"))):
            with self.assertRaises(TP6Protect3Unsafe):
                verify_r070_linked_sltp(
                    observed_position=2, orders=orders, levels=levels,
                    wire=wire, expected_broker_order_id="order-123")

    def test_tp_missing_or_wrong_price_or_fraction_rejected(self):
        levels, _, wire, order = self.fixture()
        for change in (
            {"tp_price": {"value": "110"}},
            {"tp_price": None},
            {"quantity_tp": {"value": "50"}},
            {"tp_qty_measure": "SLTP_QTY_MEASURE_UNITS"},
            {"sl_price": {"value": "97"}},
        ):
            request = {**order.request, **change}
            with self.assertRaises(TP6Protect3Unsafe):
                verify_r070_linked_sltp(
                    observed_position=2, orders=(replace(order, request=request),),
                    levels=levels, wire=wire, expected_broker_order_id="order-123")

    def test_partial_fill_quantity_or_action_drift_is_rejected(self):
        levels, action, wire, order = self.fixture()
        with self.assertRaisesRegex(TP6Protect3Unsafe, "R070_SLTP_FILL_OR_STOP_SCOPE_INVALID"):
            prepare_r070_linked_sltp_draft(
                action=replace(action, quantity=1, expected_position_quantity=1),
                levels=levels)
        with self.assertRaisesRegex(TP6Protect3Unsafe, "R070_SLTP_BROKER_STATE_UNVERIFIED"):
            verify_r070_linked_sltp(
                observed_position=1, orders=(order,), levels=levels,
                wire=wire, expected_broker_order_id="order-123")


if __name__ == "__main__":
    unittest.main()
