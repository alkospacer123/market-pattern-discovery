"""M15-only offline durable draft + sanitized broker GET bridge tests.

ALL broker JSON is synthetic. No FINAM network, credentials, H1, Task or LIVE.
"""
from __future__ import annotations

import hashlib
import tempfile
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from IntradayLab.m15_robot.broker_fill_readonly import ExpectedEntry
from IntradayLab.m15_robot.broker_receipt_store import M15ReadOnlyBrokerReceiptStore
from IntradayLab.m15_robot.grid_risk import ContractAuthority, size_r15
from IntradayLab.m15_robot.offline_intents import OfflineIntentLedger, M15OfflineLedgerError
from IntradayLab.m15_robot.offline_trade_handoff import (
    M15OfflineHandoffError, prepare_offline_entry, inspect_broker_evidence_offline,
)
from IntradayLab.m15_robot.trade_draft_contract import M15OfflineTradeDrafts, M15DraftError


START = "2026-10-18T07:00:00Z"
END = "2026-10-18T09:00:00Z"
OBSERVED = datetime(2026, 10, 18, 8, 30, tzinfo=timezone.utc)
ACCOUNT = "M15-SYNTH-DRAFT-ONLY"


def number(value):
    return {"value": str(value)}


class OfflineHandoffTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.opts = dict(
            m15_account_id=ACCOUNT,
            h1_account_sha256=hashlib.sha256(b"SEPARATE-H1-SYNTH").hexdigest(),
            h1_runtime_root=root / "h1",
            repository_root=root / "code",
        )
        self.drafts = M15OfflineTradeDrafts(m15_runtime_root=root / "drafts", **self.opts)
        self.ledger = OfflineIntentLedger(runtime_root=root / "ledger", **self.opts)
        self.receipts = M15ReadOnlyBrokerReceiptStore(runtime_root=root / "receipts", **self.opts)
        contract = ContractAuthority(
            price_step=Decimal("0.001"), tick_value=Decimal("1"), trade_lot_size=1,
            long_initial_margin=Decimal("1000"), short_initial_margin=Decimal("1000"),
        )
        self.sized = size_r15(
            realized_equity=Decimal("100000"), entry=Decimal("12.500"),
            stop=Decimal("12.250"), contract=contract,
            direction="LONG", available_margin_cash=Decimal("20000"),
        )

    def tearDown(self):
        self.receipts.close()
        self.ledger.close()
        self.tmp.cleanup()

    def prep(self, key="m15:handoff-001", **changes):
        kw = dict(drafts=self.drafts, ledger=self.ledger,
                  instrument="CNYRUBF", direction="LONG",
                  idempotency_key=key, sized=self.sized,
                  observed_occupied=False)
        return prepare_offline_entry(**(kw | changes))

    def evidence(self, p, *, qty=0, order=None, trades=None, acc=None,
                 when=OBSERVED, trade_rows_extra=None):
        expected = ExpectedEntry(
            account_id=ACCOUNT, order_id="broker-synthetic-entry",
            symbol="CNYRUBF@RTSX", side="SIDE_BUY",
            quantity=p.quantity, price_step=Decimal("0.001"),
        )
        entry_order = {
            "order_id": expected.order_id,
            "status": "ORDER_STATUS_PARTIAL_FILL" if qty else "ORDER_STATUS_NEW",
            "order": {
                "symbol": expected.symbol,
                "client_order_id": p.draft.payload["client_order_id"],
                "side": expected.side,
                "quantity": number(expected.quantity),
            },
        }
        positions = [] if qty == 0 else [{
            "symbol": expected.symbol, "quantity": number(qty),
        }]
        trade = {
            "trade_id": "synthetic-fill-01", "account_id": ACCOUNT,
            "order_id": expected.order_id, "symbol": expected.symbol,
            "side": expected.side, "currency": "XXX",
            "timestamp": "2026-10-18T07:15:00Z",
            "price": number("12.533"), "size": number(1),
        }
        return inspect_broker_evidence_offline(
            prepared=p, ledger=self.ledger, receipts=self.receipts,
            expected=expected, observed_at=when,
            account={"account_id": ACCOUNT, "status": "ACCOUNT_ACTIVE",
                     "positions": positions} if acc is None else acc,
            orders_response={"orders": [entry_order if order is None else order]},
            trades_response={"trades": ([] if not qty else [trade])
                             if trades is None else trades, **(trade_rows_extra or {})},
            start=START, end=END, stop_trade_tag="handoff-1",
        )

    def test_prepared_draft_persists_before_any_broker_snapshot(self):
        p = self.prep()
        self.assertTrue(p.new_intent)
        self.assertFalse(p.live_authorized or p.post_authorized)
        self.assertEqual(self.ledger.intent(p.key)["status"], "PREPARED")
        self.assertEqual(self.ledger.intent(p.key)["planned_quantity"], self.sized.final_quantity)
        self.assertEqual(self.ledger.filled_quantity(p.key), 0)
        self.assertIsNone(self.receipts.latest())

    def test_identical_key_never_prepares_second_intent(self):
        a, b = self.prep(), self.prep()
        self.assertTrue(a.new_intent)
        self.assertFalse(b.new_intent)
        self.assertEqual(self.ledger.db.execute("SELECT count(*) FROM intents").fetchone()[0], 1)

    def test_uncertain_intent_is_never_retried(self):
        p = self.prep()
        self.ledger.uncertain(p.key)
        other = self.prep()
        self.assertFalse(other.new_intent)
        self.assertEqual(self.ledger.intent(p.key)["status"], "UNCERTAIN")

    def test_second_same_instrument_intent_refused(self):
        self.prep()
        with self.assertRaisesRegex(M15OfflineLedgerError, "OCCUPIED"):
            self.prep("m15:second-instrument-key")
        self.assertEqual(self.ledger.db.execute("SELECT count(*) FROM intents").fetchone()[0], 1)

    def test_refuse_mismatched_draft_vs_ledger_account(self):
        root = Path(self.tmp.name)
        foreign = M15OfflineTradeDrafts(
            m15_runtime_root=root / "other-drafts",
            m15_account_id="OTHER-M15-SYNTH",
            h1_account_sha256=self.opts["h1_account_sha256"],
            h1_runtime_root=self.opts["h1_runtime_root"],
            repository_root=self.opts["repository_root"],
        )
        with self.assertRaisesRegex(M15OfflineHandoffError, "ACCOUNT_OR_AUTHORITY"):
            self.prep(drafts=foreign)
        self.assertEqual(self.ledger.db.execute("SELECT count(*) FROM intents").fetchone()[0], 0)

    def test_zero_margin_is_denied_before_any_ledger_write(self):
        zero = self.sized.__class__(
            risk_budget=Decimal("1000"), per_contract_loss=Decimal("250"),
            by_risk=4, by_margin=0, final_quantity=0,
            initial_nominal_risk=Decimal("0"), reason="ZERO_RISK_OR_MARGIN_CAPACITY",
        )
        with self.assertRaisesRegex(M15DraftError, "R15_GO_AUTHORITY"):
            self.prep(sized=zero)
        self.assertEqual(self.ledger.db.execute("SELECT count(*) FROM intents").fetchone()[0], 0)

    def test_empty_broker_history_receipt_is_not_an_execution(self):
        p = self.prep()
        result = self.evidence(p)
        self.assertTrue(result["appended"])
        self.assertTrue(result["synthetic_intent_unchanged"])
        self.assertFalse(result["sqlite_fill_adoption_authorized"])
        self.assertFalse(result["order_submission_authorized"])
        self.assertEqual(self.receipts.latest()["quantity_status"], "NO_MATCH")
        self.assertEqual(self.ledger.filled_quantity(p.key), 0)

    def test_partial_broker_fill_is_observed_never_adopted(self):
        p = self.prep()
        self.ledger.uncertain(p.key)
        result = self.evidence(p, qty=1)
        self.assertTrue(result["synthetic_intent_unchanged"])
        row = self.receipts.latest()
        self.assertEqual(row["matched_quantity"], 1)
        self.assertEqual(row["broker_position_quantity"], 1)
        self.assertEqual(row["protection_status"], "UNPROTECTED_BROKER_FILL")
        self.assertEqual(self.ledger.intent(p.key)["status"], "UNCERTAIN")
        self.assertEqual(self.ledger.filled_quantity(p.key), 0)

    def test_bad_broker_account_fails_before_receipt_append(self):
        p = self.prep()
        with self.assertRaisesRegex(RuntimeError, "ACCOUNT_BINDING"):
            self.evidence(p, acc={"account_id": "FOREIGN-H1", "status": "ACCOUNT_ACTIVE",
                                   "positions": []})
        self.assertIsNone(self.receipts.latest())

    def test_wrong_broker_client_id_fails_before_receipt_append(self):
        p = self.prep()
        order = {"order_id": "broker-synthetic-entry", "status": "ORDER_STATUS_NEW",
                 "order": {"symbol": "CNYRUBF@RTSX", "side": "SIDE_BUY",
                           "quantity": number(p.quantity), "client_order_id": "foreign-id"}}
        with self.assertRaisesRegex(RuntimeError, "ORDER_IDENTITY_MISMATCH"):
            self.evidence(p, order=order)
        self.assertIsNone(self.receipts.latest())

    def test_incomplete_trade_history_fails_without_receipt(self):
        p = self.prep()
        with self.assertRaisesRegex(RuntimeError, "COMPLETENESS_UNPROVEN"):
            self.evidence(p, trade_rows_extra={"next_cursor": "more"})
        self.assertIsNone(self.receipts.latest())

    def test_replayed_identical_broker_snapshot_is_idempotent(self):
        p = self.prep()
        a, b = self.evidence(p), self.evidence(p)
        self.assertTrue(a["appended"])
        self.assertFalse(b["appended"])
        self.assertEqual(self.receipts.latest()["cycle"], 1)

    def test_stale_or_conflicting_broker_snapshot_refused(self):
        p = self.prep()
        self.evidence(p)
        with self.assertRaisesRegex(RuntimeError, "STALE_OR_CONFLICTING_CYCLE"):
            self.evidence(p, qty=1, when=OBSERVED)
        self.assertEqual(self.receipts.latest()["matched_quantity"], 0)

    def test_synthetic_ack_never_mistaken_for_real_broker_proof(self):
        p = self.prep()
        self.ledger.synthetic_ack(p.key, "sim-order-1")
        with self.assertRaisesRegex(M15OfflineHandoffError, "DURABLE_INTENT_MISMATCH"):
            self.evidence(p)
        self.assertIsNone(self.receipts.latest())

    def test_no_submit_cancel_or_broker_transport_in_handoff(self):
        p = self.prep()
        for obj in (self.receipts, self.ledger):
            self.assertFalse(obj.execution_authorized)
        self.assertFalse(hasattr(p, "submit"))
        self.assertFalse(hasattr(self.receipts, "place_order"))
        self.assertFalse(hasattr(self.receipts, "place_sltp_order"))
        self.assertFalse(hasattr(self.ledger, "place_order"))
        with self.assertRaisesRegex(M15DraftError, "NOT_AUTHORIZED"):
            self.drafts.submit(p)

    def test_distinct_drafts_and_intents_are_readonly_rehearsal(self):
        p = self.prep()
        self.assertEqual(p.draft.endpoint, "REGULAR_ORDER_DRAFT")
        self.assertEqual(self.ledger.identity["broker"], "SYNTHETIC_ONLY")
        self.assertEqual(self.receipts.identity["environment"], "BROKER_GET_READONLY_RECEIPTS")


if __name__ == "__main__":
    unittest.main()
