"""№16 synthetic read-only protective coverage across two FINAM GET observations."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import unittest

from IntradayLab.m15_robot.sltp_observation import (
    M15SLTPObservationError, inspect_sltp_between_gets,
)
from IntradayLab.m15_robot.tests.test_broker_reconcile_gate import (
    account, stop_order, target, number,
)

AT = datetime(2026, 10, 18, 10, 45, tzinfo=timezone.utc)


def stop(**change):
    v = stop_order()
    v["sltp_order"].update(change)
    return v


def check(*, initial=1, current=1, first_stop=None, current_stop=None,
          first_account=None, current_account=None, expected=None,
          first_at=AT, current_at=AT + timedelta(seconds=30),
          stop_id="broker-sltp-01", tag="trade-1"):
    a = account(initial) if first_account is None else first_account
    b = account(current) if current_account is None else current_account
    return inspect_sltp_between_gets(
        expected=target() if expected is None else expected,
        trade_tag=tag, stop_order_id=stop_id,
        first_at=first_at, current_at=current_at,
        first_account=a, current_account=b,
        first_orders={"orders": [stop()] if first_stop is None else first_stop},
        current_orders={"orders": [stop()] if current_stop is None else current_stop},
    )


class ReadOnlyStopWitness(unittest.TestCase):
    def test_same_position_stop_is_observation_only(self):
        got = check()
        self.assertEqual(got.protection_action, "HOLD_CURRENT_OBSERVATION_ONLY")
        self.assertEqual(got.initially_observed_quantity, 1)
        self.assertEqual(got.current_broker_quantity, 1)
        self.assertEqual(got.stop_price, Decimal("12.230"))
        self.assertFalse(got.live_authorized)
        self.assertFalse(got.broker_submission_authorized)
        self.assertNotIn("broker-sltp-01", str(got))

    def test_later_partial_fill_must_refresh_coverage(self):
        got = check(initial=1, current=2)
        self.assertEqual(got.protection_action, "REPLACE_REQUIRED_COVERAGE")
        self.assertEqual(got.initially_observed_quantity, 1)
        self.assertEqual(got.current_broker_quantity, 2)
        self.assertFalse(got.live_authorized)

    def test_full_new_position_does_not_inherit_old_100_percent(self):
        self.assertEqual(check(initial=1, current=3).protection_action,
                         "REPLACE_REQUIRED_COVERAGE")

    def test_wrong_account_denied_on_first_get(self):
        with self.assertRaisesRegex(M15SLTPObservationError, "EXACT_ACCOUNT"):
            check(first_account=account(1, account_id="FOREIGN"))

    def test_wrong_account_denied_on_second_get(self):
        with self.assertRaisesRegex(M15SLTPObservationError, "EXACT_ACCOUNT"):
            check(current_account=account(1, account_id="H1-FOREIGN"))

    def test_missing_current_sltp_is_not_broker_confirmed(self):
        with self.assertRaisesRegex(M15SLTPObservationError, "INACTIVE"):
            check(current_stop=[])

    def test_wrong_symbol_stop_is_not_coverage(self):
        with self.assertRaisesRegex(M15SLTPObservationError, "INACTIVE"):
            check(current_stop=[stop(symbol="IMOEXF@RTSX")])

    def test_duplicate_current_stop_fails_closed(self):
        duplicate = stop_order(order_id="broker-sltp-02", sltp_order={
            **stop()["sltp_order"], "client_order_id": "m15stop00002",
        })
        with self.assertRaisesRegex(M15SLTPObservationError, "NOT_UNIQUE"):
            check(current_stop=[stop(), duplicate])

    def test_stop_price_changed_without_new_ack_refused(self):
        with self.assertRaisesRegex(M15SLTPObservationError, "STOP_CHANGED"):
            check(current_stop=[stop(sl_price=number("12.231"))])

    def test_wrong_closing_side_denied(self):
        with self.assertRaisesRegex(M15SLTPObservationError, "CLOSING_SIDE"):
            check(current_stop=[stop(side="SIDE_BUY")])

    def test_wrong_percent_denied(self):
        with self.assertRaisesRegex(Exception, "SLTP_CLOSE_ONLY"):
            check(current_stop=[stop(quantity_sl=number("99"))])

    def test_price_off_exchange_grid_denied(self):
        with self.assertRaisesRegex(M15SLTPObservationError, "PRICE_GRID"):
            check(current_stop=[stop(sl_price=number("12.2305"))])

    def test_more_than_expected_entry_quantity_denied(self):
        with self.assertRaisesRegex(M15SLTPObservationError, "POSITION_UNPROVEN"):
            check(initial=1, current=4)

    def test_current_position_reduction_needs_exit_reconciliation(self):
        with self.assertRaisesRegex(M15SLTPObservationError, "POSITION_REDUCTION"):
            check(initial=2, current=1)

    def test_same_instant_replayed_get_denied(self):
        with self.assertRaisesRegex(M15SLTPObservationError, "REPLAYED"):
            check(current_at=AT)

    def test_naive_time_denied(self):
        with self.assertRaisesRegex(M15SLTPObservationError, "CLOCK_UNPROVEN"):
            check(first_at=datetime(2026, 10, 18, 10, 45))

    def test_utc_offset_representation_does_not_break_time_order(self):
        earlier = datetime(2026, 10, 18, 13, 45, tzinfo=timezone(timedelta(hours=3)))
        self.assertEqual(check(first_at=earlier).initially_observed_quantity, 1)

    def test_stale_stop_id_denied(self):
        with self.assertRaisesRegex(M15SLTPObservationError, "ORDER_OR_CLOSING_SIDE"):
            check(stop_id="some-other-stop")

    def test_orphan_different_trade_tag_denied(self):
        with self.assertRaisesRegex(M15SLTPObservationError, "INACTIVE"):
            check(tag="foreign-trade")

    def test_short_position_must_have_buy_sltp(self):
        expected = target(side="SIDE_SELL")
        first = account(-1)
        current = account(-2)
        x = stop(side="SIDE_BUY")
        got = check(
            expected=expected, first_account=first, current_account=current,
            first_stop=[x], current_stop=[deepcopy(x)],
        )
        self.assertEqual(got.protection_action, "REPLACE_REQUIRED_COVERAGE")
        self.assertFalse(got.broker_submission_authorized)

    def test_short_wrong_stop_side_denied(self):
        with self.assertRaisesRegex(M15SLTPObservationError, "CLOSING_SIDE"):
            check(expected=target(side="SIDE_SELL"), initial=-1, current=-1)

    def test_no_api_or_sqlite_access(self):
        got = check()
        self.assertFalse(hasattr(got, "place_order"))
        self.assertFalse(hasattr(got, "cancel_order"))
        self.assertFalse(hasattr(got, "db"))


if __name__ == "__main__":
    unittest.main()
