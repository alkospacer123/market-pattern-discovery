"""Offline tests for step14 broker-fills/order/position cross-source gate.

Entirely synthetic response objects. No API, task, token, H1 or live SQLite.
"""
from __future__ import annotations

import unittest
from copy import deepcopy
from decimal import Decimal

from IntradayLab.m15_robot.broker_fill_readonly import ExpectedEntry
from IntradayLab.m15_robot.broker_reconcile_gate import (
    M15ReconcileGateError, assess_entry_evidence,
)

START = "2026-10-18T07:00:00Z"
END = "2026-10-18T09:00:00Z"


def number(value):
    return {"value": str(value)}


def target(**changes):
    values = dict(account_id="M15-SYNTH-ACCOUNT", order_id="broker-entry-01",
                  symbol="CNYRUBF@RTSX", side="SIDE_BUY",
                  quantity=3, price_step=Decimal("0.001"))
    values.update(changes)
    return ExpectedEntry(**values)


def account(qty=0, **changes):
    value = dict(
        account_id="M15-SYNTH-ACCOUNT", status="ACCOUNT_ACTIVE",
        positions=[] if qty == 0 else [
            {"symbol": "CNYRUBF@RTSX", "quantity": number(qty)}
        ],
    )
    value.update(changes)
    return value


def entry_order(**changes):
    order = dict(
        order_id="broker-entry-01", status="ORDER_STATUS_FILLED",
        order={"symbol": "CNYRUBF@RTSX", "client_order_id": "m15entry0001",
               "side": "SIDE_BUY", "quantity": number(3)},
    )
    order.update(changes)
    return order


def stop_order(order_id="broker-sltp-01", **changes):
    value = dict(
        order_id=order_id, status="ORDER_STATUS_NEW",
        sltp_order={
            "symbol": "CNYRUBF@RTSX", "client_order_id": "m15stop00001",
            "side": "SIDE_SELL", "comment": "m15:trade-1:stop:0",
            "sl_qty_measure": "SLTP_QTY_MEASURE_PERCENT",
            "quantity_sl": number(100),
            "sl_price": number("12.230"),
            "valid_before": "VALID_BEFORE_GOOD_TILL_CANCEL",
        },
    )
    value.update(changes)
    return value


def trade(idx=1, **changes):
    row = dict(
        trade_id="fill-" + str(idx), account_id="M15-SYNTH-ACCOUNT",
        order_id="broker-entry-01", symbol="CNYRUBF@RTSX",
        side="SIDE_BUY", currency="XXX",
        timestamp="2026-10-18T07:15:00Z",
        price=number("12.533"), size=number(1),
    )
    row.update(changes)
    return row


def assess(*, qty=0, fills=(), orders=None, expected=None, acc=None):
    if orders is None:
        orders = [entry_order()]
    return assess_entry_evidence(
        account=account(qty) if acc is None else acc,
        orders_response={"orders": orders},
        trades_response={"trades": list(fills)},
        expected=target() if expected is None else expected,
        expected_client_order_id="m15entry0001",
        stop_trade_tag="trade-1", start=START, end=END,
    )


class ExactReadOnlyReconciliation(unittest.TestCase):
    def test_no_broker_fill_never_claims_fill_or_stop(self):
        result = assess()
        self.assertEqual(result.quantity_status, "NO_MATCH")
        self.assertEqual(result.protection_status, "NO_CONFIRMED_FILL")
        self.assertEqual(result.matched_fill_quantity, 0)
        self.assertFalse(result.sqlite_adoption_authorized)
        self.assertFalse(result.live_authorized)

    def test_partial_fill_without_stop_exposes_missing_protection(self):
        result = assess(qty=1, fills=[trade()])
        self.assertEqual(result.quantity_status, "PARTIAL")
        self.assertEqual(result.protection_status, "UNPROTECTED_BROKER_FILL")

    def test_full_fill_with_sltp_still_not_full_coverage_proof(self):
        result = assess(qty=3, fills=[trade(1), trade(2), trade(3)],
                        orders=[entry_order(), stop_order()])
        self.assertEqual(result.quantity_status, "FULL")
        self.assertEqual(result.matched_fill_quantity, 3)
        self.assertEqual(result.active_sltp_count, 1)
        self.assertEqual(result.protection_status, "ACTIVE_SLTP_COVERAGE_TIMESTAMP_UNPROVEN")
        self.assertFalse(result.live_authorized)
        self.assertFalse(result.sqlite_adoption_authorized)

    def test_partial_fill_with_active_stop_does_not_adopt_full_cover(self):
        result = assess(qty=1, fills=[trade()],
                        orders=[entry_order(), stop_order()])
        self.assertEqual(result.protection_status, "ACTIVE_SLTP_COVERAGE_TIMESTAMP_UNPROVEN")

    def test_wrong_account_denied_before_fills(self):
        with self.assertRaisesRegex(M15ReconcileGateError, "ACCOUNT_BINDING"):
            assess(acc=account(account_id="H1-SYNTH"))

    def test_broker_position_without_matched_fills_denied(self):
        with self.assertRaisesRegex(M15ReconcileGateError, "POSITION_FILL_DIVERGENCE"):
            assess(qty=2)

    def test_matched_fill_but_broker_flat_denied(self):
        with self.assertRaisesRegex(M15ReconcileGateError, "POSITION_FILL_DIVERGENCE"):
            assess(fills=[trade()])

    def test_partial_fill_quantity_disagreement_denied(self):
        with self.assertRaisesRegex(M15ReconcileGateError, "POSITION_FILL_DIVERGENCE"):
            assess(qty=2, fills=[trade()])

    def test_unknown_broker_entry_id_not_adopted(self):
        with self.assertRaisesRegex(M15ReconcileGateError, "EXACT_ORDER_UNPROVEN"):
            assess(orders=[entry_order(order_id="wrong-broker-id")])

    def test_broker_entry_client_order_id_wrong_denied(self):
        bad = entry_order()
        bad["order"]["client_order_id"] = "foreign-entry"
        with self.assertRaisesRegex(M15ReconcileGateError, "ORDER_IDENTITY_MISMATCH"):
            assess(orders=[bad])

    def test_second_same_symbol_live_entry_denied(self):
        foreign = entry_order(order_id="broker-other", status="ORDER_STATUS_NEW")
        with self.assertRaisesRegex(M15ReconcileGateError, "COMPETING_ENTRY_ORDER"):
            assess(orders=[entry_order(), foreign])

    def test_wrong_side_active_stop_denied(self):
        bad = stop_order()
        bad["sltp_order"]["side"] = "SIDE_BUY"
        with self.assertRaisesRegex(M15ReconcileGateError, "CLOSING_SIDE"):
            assess(qty=1, fills=[trade()], orders=[entry_order(), bad])

    def test_active_stop_off_grid_denied(self):
        bad = stop_order()
        bad["sltp_order"]["sl_price"] = number("12.2305")
        with self.assertRaisesRegex(M15ReconcileGateError, "SLTP_GRID"):
            assess(qty=1, fills=[trade()], orders=[entry_order(), bad])

    def test_duplicate_active_stops_denied(self):
        with self.assertRaisesRegex(M15ReconcileGateError, "DUPLICATE_ACTIVE_SLTP"):
            assess(qty=1, fills=[trade()], orders=[
                entry_order(), stop_order(), stop_order(
                    order_id="broker-sltp-02",
                    sltp_order={**stop_order()["sltp_order"], "client_order_id": "m15stop00002"}),
            ])

    def test_foreign_active_stop_denied(self):
        bad = stop_order()
        bad["sltp_order"]["comment"] = "m15:another-trade:stop:0"
        with self.assertRaisesRegex(M15ReconcileGateError, "FOREIGN_ACTIVE_SLTP"):
            assess(qty=1, fills=[trade()], orders=[entry_order(), bad])

    def test_stop_but_zero_confirmed_fill_denied(self):
        with self.assertRaisesRegex(M15ReconcileGateError, "ORPHAN_ACTIVE_SLTP"):
            assess(orders=[entry_order(), stop_order()])

    def test_unbounded_trade_history_cannot_be_adopted(self):
        with self.assertRaisesRegex(RuntimeError, "COMPLETENESS_UNPROVEN"):
            assess_entry_evidence(
                account=account(1), orders_response={"orders": [entry_order()]},
                trades_response={"trades": [trade()], "next_cursor": "more"},
                expected=target(), expected_client_order_id="m15entry0001",
                stop_trade_tag="trade-1", start=START, end=END,
            )

    def test_synthetic_gate_has_no_order_or_sqlite_transport(self):
        result = assess()
        self.assertFalse(hasattr(result, "place_order"))
        self.assertFalse(hasattr(result, "sqlite_commit"))
        self.assertFalse(result.live_authorized)


if __name__ == "__main__":
    unittest.main()
