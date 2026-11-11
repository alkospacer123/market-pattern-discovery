"""Pure M15 initial-stop proposal from bounded synthetic FINAM AccountTrade GET."""
from __future__ import annotations

import hashlib
import tempfile
import unittest
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

from IntradayLab.m15_robot.broker_fill_readonly import ExpectedEntry
from IntradayLab.m15_robot.grid_risk import ContractAuthority, size_r15
from IntradayLab.m15_robot.initial_stop_from_fills import (
    M15InitialStopDraftError, initial_stop_draft_from_broker_get,
)
from IntradayLab.m15_robot.offline_intents import OfflineIntentLedger
from IntradayLab.m15_robot.offline_trade_handoff import prepare_offline_entry
from IntradayLab.m15_robot.trade_draft_contract import M15OfflineTradeDrafts, M15DraftError


ACCOUNT = "M15-ONLY-SYNTH"
START = "2026-10-18T07:00:00Z"
END = "2026-10-18T09:00:00Z"


def number(value):
    return {"value": str(value)}


class InitialStopFromBrokerFills(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        opts = {
            "m15_account_id": ACCOUNT,
            "h1_account_sha256": hashlib.sha256(b"DIFFERENT-H1-SYNTH").hexdigest(),
            "h1_runtime_root": root / "h1",
            "repository_root": root / "repo",
        }
        self.drafts = M15OfflineTradeDrafts(m15_runtime_root=root / "draft", **opts)
        self.ledger = OfflineIntentLedger(runtime_root=root / "ledger", **opts)
        self.contract = ContractAuthority(
            price_step=Decimal("0.001"), tick_value=Decimal("1"), trade_lot_size=1,
            long_initial_margin=Decimal("1000"), short_initial_margin=Decimal("1000"),
        )
        self.risk = size_r15(
            realized_equity=Decimal("100000"), entry=Decimal("12.500"),
            stop=Decimal("12.250"), contract=self.contract,
            direction="LONG", available_margin_cash=Decimal("20000"),
        )
        self.assertEqual(self.risk.final_quantity, 6)

    def tearDown(self):
        self.ledger.close()
        self.tmp.cleanup()

    def make(self, direction="LONG"):
        return prepare_offline_entry(
            drafts=self.drafts, ledger=self.ledger,
            instrument="CNYRUBF", direction=direction,
            idempotency_key="m15:prepared-entry",
            sized=self.risk, observed_occupied=False,
        )

    def build(self, prepared, *, prices=("12.500",), sizes=None, direction="LONG",
              account_override=None, orders_override=None, trades_override=None,
              atr=Decimal("0.1"), stop_key="m15:initial-stop", expected_qty=None,
              price_step=Decimal("0.001"), extra_history=None):
        sizes = (1,) * len(prices) if sizes is None else sizes
        qty = sum(sizes)
        side = "SIDE_BUY" if direction == "LONG" else "SIDE_SELL"
        expected = ExpectedEntry(
            account_id=ACCOUNT, order_id="broker-01", symbol="CNYRUBF@RTSX",
            side=side, quantity=prepared.quantity if expected_qty is None else expected_qty,
            price_step=price_step,
        )
        status = ("ORDER_STATUS_NEW" if qty == 0 else
                  "ORDER_STATUS_FILLED" if qty == expected.quantity else
                  "ORDER_STATUS_PARTIAL_FILL")
        entry = {"order_id": "broker-01", "status": status,
                 "order": {"symbol": "CNYRUBF@RTSX",
                           "side": side,
                           "quantity": number(expected.quantity),
                           "client_order_id": prepared.draft.payload["client_order_id"]}}
        trades = [
            {"trade_id": "get-fill-" + str(i), "account_id": ACCOUNT,
             "order_id": "broker-01", "symbol": "CNYRUBF@RTSX", "side": side,
             "currency": "XXX", "timestamp": "2026-10-18T07:15:00Z",
             "price": number(price), "size": number(size)}
            for i, (price, size) in enumerate(zip(prices, sizes), 1)
        ]
        account = {"account_id": ACCOUNT, "status": "ACCOUNT_ACTIVE",
                   "positions": ([{"symbol": "CNYRUBF@RTSX",
                                  "quantity": number(qty if direction == "LONG" else -qty)}]
                                 if qty else [])}
        return initial_stop_draft_from_broker_get(
            drafts=self.drafts, prepared=prepared, expected=expected,
            stop_idempotency_key=stop_key, atr_at_entry_signal=atr,
            account=account if account_override is None else account_override,
            orders_response={"orders": [entry]} if orders_override is None else orders_override,
            trades_response={"trades": trades, **(extra_history or {})}
                if trades_override is None else trades_override,
            stop_trade_tag="trade-1", start=START, end=END,
        )

    def test_one_broker_fill_generates_correct_2atr_100pct_draft(self):
        p = self.make()
        x = self.build(p)
        self.assertEqual(x.matched_quantity, 1)
        self.assertEqual(x.weighted_entry_exact, Fraction(25, 2))
        self.assertEqual(x.stop_price, Decimal("12.300"))
        self.assertEqual(x.draft.payload["quantity_sl"], {"value": "100"})
        self.assertEqual(x.draft.payload["side"], "SIDE_SELL")
        self.assertEqual(x.draft.payload["sl_price"], {"value": "12.300"})
        self.assertFalse(x.live_authorized or x.broker_stop_acknowledged
                         or x.broker_position_protected
                         or x.order_submission_authorized or x.draft.submitted)
        self.assertEqual(self.ledger.intent(p.key)["status"], "PREPARED")

    def test_two_realistic_fills_vwap_off_tick_still_projects_stop(self):
        p = self.make()
        x = self.build(p, prices=("12.500", "12.501"))
        self.assertEqual(x.weighted_entry_exact, Fraction(25001, 2000))
        self.assertEqual(x.matched_quantity, 2)
        self.assertEqual(x.stop_price, Decimal("12.300"))
        self.assertEqual(x.draft.payload["sl_qty_measure"], "SLTP_QTY_MEASURE_PERCENT")

    def test_short_vwap_off_tick_projects_stop_outward_up(self):
        p = self.make(direction="SHORT")
        x = self.build(p, direction="SHORT", prices=("12.500", "12.501"))
        self.assertEqual(x.stop_price, Decimal("12.701"))
        self.assertEqual(x.draft.payload["side"], "SIDE_BUY")

    def test_empty_history_cannot_create_stop(self):
        p = self.make()
        with self.assertRaisesRegex(M15InitialStopDraftError, "FILL_OR_STOP_UNPROVEN"):
            self.build(p, prices=(), sizes=())

    def test_missing_broker_fill_but_nonzero_position_is_denied(self):
        p = self.make()
        acc = {"account_id": ACCOUNT, "status": "ACCOUNT_ACTIVE",
               "positions": [{"symbol": "CNYRUBF@RTSX", "quantity": number(1)}]}
        with self.assertRaisesRegex(RuntimeError, "POSITION_FILL_DIVERGENCE"):
            self.build(p, prices=(), sizes=(), account_override=acc)

    def test_wrong_account_is_denied(self):
        p = self.make()
        bad = {"account_id": "FOREIGN-H1", "status": "ACCOUNT_ACTIVE", "positions": []}
        with self.assertRaisesRegex(RuntimeError, "ACCOUNT_BINDING"):
            self.build(p, account_override=bad)

    def test_missing_history_page_is_denied(self):
        p = self.make()
        with self.assertRaisesRegex(RuntimeError, "COMPLETENESS_UNPROVEN"):
            self.build(p, extra_history={"next_cursor": "another-page"})

    def test_bad_price_grid_in_broker_fill_denied(self):
        p = self.make()
        with self.assertRaisesRegex(RuntimeError, "FILL_PRICE_OFF_GRID"):
            self.build(p, prices=("12.5005",))

    def test_wrong_stop_key_denied_by_draft_contract(self):
        p = self.make()
        with self.assertRaisesRegex(M15DraftError, "IDEMPOTENCY_KEY_INVALID"):
            self.build(p, stop_key="h1:stop")

    def test_same_entry_stop_key_denied(self):
        p = self.make()
        with self.assertRaisesRegex(M15InitialStopDraftError, "OFFLINE_IDENTITY_INVALID"):
            self.build(p, stop_key=p.key)

    def test_zero_and_nonfinite_atr_refused_before_snapshot(self):
        p = self.make()
        for atr in (Decimal("0"), Decimal("-0.01"), Decimal("NaN")):
            with self.subTest(atr=atr), self.assertRaisesRegex(M15InitialStopDraftError, "SIGNAL_ATR_INVALID"):
                self.build(p, atr=atr)

    def test_stale_or_duplicate_broker_stop_fails_not_installed_again(self):
        p = self.make()
        stop = {"order_id": "broker-stop-01", "status": "ORDER_STATUS_NEW",
                "sltp_order": {"symbol": "CNYRUBF@RTSX", "side": "SIDE_SELL",
                               "comment": "m15:trade-1:stop:0",
                               "quantity_sl": number(100),
                               "sl_qty_measure": "SLTP_QTY_MEASURE_PERCENT",
                               "sl_price": number("12.300"),
                               "valid_before": "VALID_BEFORE_GOOD_TILL_CANCEL",
                               "client_order_id": "m15stop000001"}}
        entry = {"order_id": "broker-01", "status": "ORDER_STATUS_PARTIAL_FILL",
                 "order": {"symbol": "CNYRUBF@RTSX", "side": "SIDE_BUY",
                           "quantity": number(p.quantity),
                           "client_order_id": p.draft.payload["client_order_id"]}}
        with self.assertRaisesRegex(M15InitialStopDraftError, "FILL_OR_STOP_UNPROVEN"):
            self.build(p, orders_override={"orders": [entry, stop]})

    def test_competing_entry_order_denied(self):
        p = self.make()
        original = {"order_id": "broker-01", "status": "ORDER_STATUS_PARTIAL_FILL",
                    "order": {"symbol": "CNYRUBF@RTSX", "side": "SIDE_BUY",
                              "quantity": number(p.quantity),
                              "client_order_id": p.draft.payload["client_order_id"]}}
        foreign = {"order_id": "broker-02", "status": "ORDER_STATUS_NEW",
                   "order": {"symbol": "CNYRUBF@RTSX", "side": "SIDE_BUY",
                             "quantity": number(p.quantity),
                             "client_order_id": "foreign-id"}}
        with self.assertRaisesRegex(RuntimeError, "COMPETING_ENTRY_ORDER"):
            self.build(p, orders_override={"orders": [original, foreign]})

    def test_broker_account_quantity_disagreement_denied(self):
        p = self.make()
        bad = {"account_id": ACCOUNT, "status": "ACCOUNT_ACTIVE",
               "positions": [{"symbol": "CNYRUBF@RTSX", "quantity": number(2)}]}
        with self.assertRaisesRegex(RuntimeError, "POSITION_FILL_DIVERGENCE"):
            self.build(p, account_override=bad)

    def test_expected_broker_order_quantity_mismatch_denied(self):
        p = self.make()
        with self.assertRaisesRegex(M15InitialStopDraftError, "DRAFT_BROKER_IDENTITY_MISMATCH"):
            self.build(p, expected_qty=2)

    def test_no_actual_financial_or_order_state_mutation(self):
        p = self.make()
        x = self.build(p)
        self.assertFalse(hasattr(x, "submit"))
        self.assertFalse(hasattr(x.draft, "submit"))
        self.assertFalse(hasattr(self.drafts, "place_sltp_order"))
        self.assertEqual(self.ledger.filled_quantity(p.key), 0)
        self.assertEqual(x.draft.endpoint, "SLTP_ORDER_DRAFT")
        with self.assertRaisesRegex(M15DraftError, "NOT_AUTHORIZED"):
            self.drafts.submit(x.draft)


if __name__ == "__main__":
    unittest.main()
