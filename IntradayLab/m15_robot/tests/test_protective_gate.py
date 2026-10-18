"""Step16 offline STOP-first FINAM 100%-coverage gate, no networking/orders."""
import unittest
from dataclasses import replace
from decimal import Decimal

from IntradayLab.m15_robot.protective_gate import (
    BrokerProtection, M15ProtectionError, decide_protection,
)


def proof(**changes):
    data = dict(broker_order_id="sltp-1", stop_price=Decimal("98"),
                percent=100, covered_quantity_at_ack=2, active=True)
    data.update(changes)
    return BrokerProtection(**data)


def decision(*, stop=None, count=0, qty=2, direction="LONG", entry="100", atr="1"):
    return decide_protection(
        direction=direction, actual_entry=Decimal(entry),
        atr=Decimal(atr), price_step=Decimal("0.5"),
        broker_position_qty=qty, broker_stop=stop, broker_stop_count=count,
    )


class StopFirstNoLive(unittest.TestCase):
    def test_initial_long_exact_2atr_offline_install(self):
        d = decision()
        self.assertEqual(d.action, "INSTALL_REQUIRED")
        self.assertEqual(d.proposed_stop, Decimal("98"))
        self.assertFalse(d.old_stop_must_remain)
        self.assertFalse(d.new_entries_authorized)
        self.assertFalse(d.live_submission_authorized)

    def test_initial_short_exact_2atr_offline_install(self):
        d = decision(direction="SHORT")
        self.assertEqual(d.action, "INSTALL_REQUIRED")
        self.assertEqual(d.proposed_stop, Decimal("102"))

    def test_full_ack_cover_is_hold_and_never_new_entry(self):
        d = decision(stop=proof(), count=1)
        self.assertEqual(d.action, "HOLD_BROKER_CONFIRMED")
        self.assertTrue(d.old_stop_must_remain)
        self.assertFalse(d.new_entries_authorized)

    def test_later_partial_fill_exposes_extra_contract(self):
        d = decision(stop=proof(), count=1, qty=3)
        self.assertEqual(d.action, "REPLACE_REQUIRED_COVERAGE")
        self.assertTrue(d.old_stop_must_remain)
        self.assertFalse(d.live_submission_authorized)

    def test_partial_then_full_ack_cover(self):
        d = decision(stop=proof(covered_quantity_at_ack=1), count=1, qty=1)
        self.assertEqual(d.action, "HOLD_BROKER_CONFIRMED")

    def test_short_partial_increase_still_requires_new_broker_proof(self):
        d = decision(direction="SHORT", stop=proof(stop_price=Decimal("102"),
                     covered_quantity_at_ack=1), count=1, qty=2)
        self.assertEqual(d.action, "REPLACE_REQUIRED_COVERAGE")

    def test_more_cover_than_broker_exposure_is_unsafe(self):
        with self.assertRaisesRegex(M15ProtectionError, "EXCEEDS_POSITION"):
            decision(stop=proof(covered_quantity_at_ack=3), count=1, qty=2)

    def test_broker_stop_not_active_is_not_coverage(self):
        with self.assertRaisesRegex(M15ProtectionError, "BROKER_STOP_INVALID"):
            decision(stop=proof(active=False), count=1)

    def test_percent_must_be_exact_integer_100(self):
        for percent in (99, 100.0, True, None):
            with self.subTest(percent=percent):
                with self.assertRaisesRegex(M15ProtectionError, "BROKER_STOP_INVALID"):
                    decision(stop=proof(percent=percent), count=1)

    def test_duplicate_stop_fails_before_action(self):
        with self.assertRaisesRegex(M15ProtectionError, "DUPLICATE"):
            decision(stop=proof(), count=2)

    def test_unknown_stop_is_not_silent_install(self):
        with self.assertRaisesRegex(M15ProtectionError, "EVIDENCE_MISSING"):
            decision(stop=None, count=1)

    def test_missing_active_stop_is_not_allowed_when_count_zero(self):
        with self.assertRaisesRegex(M15ProtectionError, "COUNT_MISMATCH"):
            decision(stop=proof(), count=0)

    def test_missing_or_zero_broker_position_fails_closed(self):
        for qty in (0, -1, True, 1.0):
            with self.subTest(qty=qty):
                with self.assertRaisesRegex(M15ProtectionError, "POSITION_NOT_PROVEN"):
                    decision(qty=qty)

    def test_invalid_side_rejected(self):
        with self.assertRaisesRegex(M15ProtectionError, "DIRECTION_INVALID"):
            decision(direction="BUY")

    def test_broker_stop_off_tick_grid_denied(self):
        with self.assertRaisesRegex(ValueError, "TICK_GRID"):
            decision(stop=proof(stop_price=Decimal("98.25")), count=1)

    def test_existing_trailing_stop_above_entry_accepted(self):
        d = decision(stop=proof(stop_price=Decimal("102")), count=1)
        self.assertEqual(d.action, "HOLD_BROKER_CONFIRMED")
        self.assertEqual(d.proposed_stop, Decimal("102"))

    def test_existing_short_trailing_stop_below_entry_accepted(self):
        d = decision(direction="SHORT", stop=proof(stop_price=Decimal("98")),
                     count=1)
        self.assertEqual(d.action, "HOLD_BROKER_CONFIRMED")

    def test_missing_protective_order_id_denied(self):
        with self.assertRaisesRegex(M15ProtectionError, "BROKER_STOP_INVALID"):
            decision(stop=proof(broker_order_id=""), count=1)

    def test_contract_has_no_transport_or_cancel_interface(self):
        d = decision()
        self.assertFalse(hasattr(d, "submit_order"))
        self.assertFalse(hasattr(d, "cancel_stop"))


if __name__ == "__main__":
    unittest.main()
