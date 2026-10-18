"""Offline confirmation contract for unchanged T3/M15 TRAIL_3.5.
No broker calls, Task, tokens or live-state write.
"""
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from IntradayLab.m15_robot.grid_risk import TrailingState
from IntradayLab.m15_robot.protective_gate import BrokerProtection
from IntradayLab.m15_robot.trailing_gate import (
    M15TrailingGateError, propose_trail, confirm_trail,
)

AT = datetime(2026, 10, 18, 10, 30, tzinfo=timezone.utc)


def state(direction="LONG"):
    if direction == "LONG":
        return TrailingState("USDRUBF", "LONG", Decimal("100"),
                             Decimal("96"), Decimal("100"))
    return TrailingState("USDRUBF", "SHORT", Decimal("100"),
                         Decimal("104"), Decimal("100"))


def stop(price="96", qty=2, **kwargs):
    values = dict(broker_order_id="stop-1", stop_price=Decimal(price),
                  percent=100, covered_quantity_at_ack=qty, active=True)
    values.update(kwargs)
    return BrokerProtection(**values)


def propose(*, current=None, observed=None, qty=2, at=AT,
            high="115", low="100", atr="2", survived=True):
    return propose_trail(
        confirmed=current or state(), observed_stop=observed or stop(),
        broker_position_qty=qty, completed_at=at,
        high=Decimal(high), low=Decimal(low), atr=Decimal(atr),
        price_step=Decimal("1"), survived_completed_bar=survived,
    )


class BrokerConfirmedTrailingOnly(unittest.TestCase):
    def test_long_proposal_is_not_live_state(self):
        s = state()
        p = propose(current=s)
        self.assertEqual(s.active_stop, Decimal("96"))
        self.assertEqual(p.before.active_stop, Decimal("96"))
        self.assertEqual(p.candidate.active_stop, Decimal("108"))
        self.assertTrue(p.replace_required)
        self.assertFalse(p.live_submission_authorized)

    def test_ack_after_replace_commits_new_state(self):
        p = propose()
        committed = confirm_trail(p, observed_stop=stop("108"), observed_stop_count=1,
                                  broker_position_qty=2, price_step=Decimal("1"))
        self.assertEqual(committed.active_stop, Decimal("108"))
        self.assertEqual(committed.last_survived_m15_close, AT.isoformat())

    def test_old_active_stop_does_not_confirm_new_level(self):
        p = propose()
        with self.assertRaisesRegex(M15TrailingGateError, "PRICE_OR_ID_MISMATCH"):
            confirm_trail(p, observed_stop=stop("96"), observed_stop_count=1,
                          broker_position_qty=2, price_step=Decimal("1"))
        self.assertEqual(p.before.active_stop, Decimal("96"))

    def test_unconfirmed_replace_has_no_broker_proof(self):
        p = propose()
        with self.assertRaisesRegex(M15TrailingGateError, "CONFIRMATION_UNPROVEN"):
            confirm_trail(p, observed_stop=None, observed_stop_count=0,
                          broker_position_qty=2, price_step=Decimal("1"))

    def test_new_partial_fill_requires_new_coverage(self):
        p = propose()
        with self.assertRaisesRegex(M15TrailingGateError, "CONFIRMATION_UNPROVEN"):
            confirm_trail(p, observed_stop=stop("108", 2), observed_stop_count=1,
                          broker_position_qty=3, price_step=Decimal("1"))

    def test_nonactive_broker_ack_denied(self):
        p = propose()
        with self.assertRaises(ValueError):
            confirm_trail(p, observed_stop=stop("108", active=False),
                          observed_stop_count=1, broker_position_qty=2,
                          price_step=Decimal("1"))

    def test_missing_survival_proof_denied(self):
        with self.assertRaisesRegex(M15TrailingGateError, "SURVIVAL"):
            propose(survived=False)

    def test_broker_stop_does_not_match_local_stop(self):
        with self.assertRaisesRegex(M15TrailingGateError, "DIVERGENCE"):
            propose(observed=stop("95"))

    def test_stop_ack_coverage_shortfall_blocks_proposal(self):
        with self.assertRaisesRegex(M15TrailingGateError, "PROTECTION_NOT_CONFIRMED"):
            propose(observed=stop("96", 1))

    def test_out_of_order_bar_denied(self):
        s = replace(state(), last_survived_m15_close=AT.isoformat())
        with self.assertRaisesRegex(M15TrailingGateError, "BAR_OR_GRID"):
            propose(current=s)

    def test_short_trailing_tighten_and_commit(self):
        s = state("SHORT")
        p = propose(current=s, observed=stop("104"), high="100", low="85")
        self.assertEqual(p.candidate.active_stop, Decimal("92"))
        c = confirm_trail(p, observed_stop=stop("92"), observed_stop_count=1,
                          broker_position_qty=2, price_step=Decimal("1"))
        self.assertEqual(c.active_stop, Decimal("92"))

    def test_no_tightening_can_advance_only_on_same_broker_stop(self):
        p = propose(high="102", low="101", atr="5")
        self.assertFalse(p.replace_required)
        self.assertEqual(p.candidate.active_stop, Decimal("96"))
        c = confirm_trail(p, observed_stop=stop(), observed_stop_count=1,
                          broker_position_qty=2, price_step=Decimal("1"))
        self.assertEqual(c.last_survived_m15_close, AT.isoformat())

    def test_no_tightening_other_order_id_denied(self):
        p = propose(high="102", low="101", atr="5")
        with self.assertRaisesRegex(M15TrailingGateError, "PRICE_OR_ID_MISMATCH"):
            confirm_trail(p, observed_stop=stop(broker_order_id="other"),
                          observed_stop_count=1, broker_position_qty=2,
                          price_step=Decimal("1"))

    def test_proposed_candidate_never_mutates_frozen_state(self):
        s = state()
        a = propose(current=s)
        b = propose(current=s, at=AT+timedelta(minutes=15), high="120")
        self.assertEqual(s.active_stop, Decimal("96"))
        self.assertEqual(a.candidate.active_stop, Decimal("108"))
        self.assertEqual(b.candidate.active_stop, Decimal("113"))


if __name__ == "__main__":
    unittest.main()
