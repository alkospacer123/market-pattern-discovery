"""M15-only offline entry, SLTP, emergency draft tests. NO network."""
from __future__ import annotations

import hashlib
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from IntradayLab.m15_robot.grid_risk import ContractAuthority, size_r15
from IntradayLab.m15_robot.trade_draft_contract import M15DraftError, M15OfflineTradeDrafts


class DraftContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.contract = M15OfflineTradeDrafts(
            m15_account_id="TEST-M15-NO-REAL-ACCOUNT",
            h1_account_sha256=hashlib.sha256(b"OTHER-FAKE-H1").hexdigest(),
            m15_runtime_root=root / "m15", h1_runtime_root=root / "h1",
            repository_root=root / "code",
        )
        self.authority = ContractAuthority(
            price_step=Decimal("0.001"), tick_value=Decimal("1"),
            trade_lot_size=1, long_initial_margin=Decimal("1000"),
            short_initial_margin=Decimal("1000"),
        )
        self.sized = size_r15(
            realized_equity=Decimal("100000"), entry=Decimal("12.500"),
            stop=Decimal("12.250"), contract=self.authority,
            direction="LONG", available_margin_cash=Decimal("20000"),
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_identity_and_hard_disabled(self):
        self.assertEqual(self.contract.identity, "T3_M15_T1_TRAIL35_N4_R15")
        self.assertFalse(self.contract.execution_authorized)
        for name in ("submit", "cancel"):
            with self.assertRaisesRegex(M15DraftError, "NOT_AUTHORIZED"):
                getattr(self.contract, name)(object(), api=object(), live_authorized=True)

    def test_live_account_collision_denied(self):
        root = Path(self.tmp.name)
        with self.assertRaisesRegex(ValueError, "H1_ACCOUNT_REUSE_PROHIBITED"):
            M15OfflineTradeDrafts(
                m15_account_id="M15-SAME",
                h1_account_sha256=hashlib.sha256(b"M15-SAME").hexdigest(),
                m15_runtime_root=root / "m15", h1_runtime_root=root / "h1",
                repository_root=root / "code",
            )

    def test_market_entry_payload_long_matches_h1_shape(self):
        draft = self.contract.entry(instrument="CNYRUBF", direction="LONG",
                                    idempotency_key="m15:entry-001", sized=self.sized,
                                    observed_occupied=False)
        self.assertEqual(self.sized.final_quantity, 6)
        self.assertEqual(draft.endpoint, "REGULAR_ORDER_DRAFT")
        self.assertEqual(draft.payload["symbol"], "CNYRUBF@RTSX")
        self.assertEqual(draft.payload["quantity"], {"value": "6"})
        self.assertEqual(draft.payload["type"], "ORDER_TYPE_MARKET")
        self.assertEqual(draft.payload["side"], "SIDE_BUY")
        self.assertEqual(draft.payload["time_in_force"], "TIME_IN_FORCE_DAY")
        self.assertEqual(len(draft.payload["client_order_id"]), 20)
        self.assertFalse(draft.live_authorized or draft.submitted)
        self.assertEqual(draft.account_fingerprint,
                         hashlib.sha256(b"TEST-M15-NO-REAL-ACCOUNT").hexdigest())

    def test_short_entry_sells(self):
        draft = self.contract.entry(instrument="USDRUBF", direction="SHORT",
                                    idempotency_key="m15:short", sized=self.sized,
                                    observed_occupied=False)
        self.assertEqual(draft.payload["side"], "SIDE_SELL")

    def test_duplicate_client_identity_stable_distinct(self):
        kwargs = dict(instrument="CNYRUBF", direction="LONG", sized=self.sized,
                      observed_occupied=False)
        a = self.contract.entry(idempotency_key="m15:one", **kwargs).payload["client_order_id"]
        b = self.contract.entry(idempotency_key="m15:one", **kwargs).payload["client_order_id"]
        c = self.contract.entry(idempotency_key="m15:two", **kwargs).payload["client_order_id"]
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)

    def test_reject_invalid_symbol_key_and_occupied(self):
        kw = dict(instrument="CNYRUBF", direction="LONG", idempotency_key="m15:k",
                  sized=self.sized, observed_occupied=False)
        for field, bad in (("instrument", "MIX"), ("idempotency_key", "h1:key"),
                           ("idempotency_key", "m15:secret/injection"),
                           ("observed_occupied", True), ("observed_occupied", 0),
                           ("direction", "FLAT")):
            with self.subTest(field=field, bad=bad), self.assertRaises(M15DraftError):
                self.contract.entry(**(kw | {field: bad}))

    def test_zero_risk_rejected(self):
        zero = size_r15(
            realized_equity=Decimal("100000"), entry=Decimal("12.500"),
            stop=Decimal("12.250"), contract=self.authority,
            direction="LONG", available_margin_cash=Decimal("0"),
        )
        self.assertEqual(zero.final_quantity, 0)
        with self.assertRaisesRegex(M15DraftError, "R15_GO_AUTHORITY_MISSING"):
            self.contract.entry(instrument="CNYRUBF", direction="LONG",
                                idempotency_key="m15:zero", sized=zero,
                                observed_occupied=False)

    def test_initial_protective_stop_100_percent(self):
        draft = self.contract.protective_stop(
            instrument="CNYRUBF", direction="LONG", idempotency_key="m15:sl1",
            observed_position_quantity=2, stop_price=Decimal("12.250"),
            price_step=Decimal("0.001"),
        )
        self.assertEqual(draft.payload["quantity_sl"], {"value": "100"})
        self.assertEqual(draft.payload["sl_qty_measure"], "SLTP_QTY_MEASURE_PERCENT")
        self.assertEqual(draft.payload["valid_before"], "VALID_BEFORE_GOOD_TILL_CANCEL")
        self.assertEqual(draft.payload["side"], "SIDE_SELL")
        self.assertEqual(draft.payload["sl_price"], {"value": "12.250"})
        self.assertFalse(draft.submitted)

    def test_initial_protective_short_buys(self):
        draft = self.contract.protective_stop(
            instrument="CNYRUBF", direction="SHORT", idempotency_key="m15:slshort",
            observed_position_quantity=-2, stop_price=Decimal("12.750"),
            price_step=Decimal("0.001"),
        )
        self.assertEqual(draft.payload["side"], "SIDE_BUY")

    def test_stop_reject_offgrid_and_zero_or_wrong_position(self):
        kw = dict(instrument="CNYRUBF", direction="LONG", idempotency_key="m15:sl",
                  observed_position_quantity=2, stop_price=Decimal("12.250"),
                  price_step=Decimal("0.001"))
        for field, bad in (("stop_price", Decimal("12.2505")),
                           ("observed_position_quantity", 0),
                           ("observed_position_quantity", -2),
                           ("observed_position_quantity", True),
                           ("price_step", Decimal("0"))):
            with self.subTest(field=field, bad=bad), self.assertRaises(M15DraftError):
                self.contract.protective_stop(**(kw | {field: bad}))

    def test_replacement_requires_old_backstop_and_no_widening(self):
        kw = dict(instrument="CNYRUBF", direction="LONG", idempotency_key="m15:trail",
                  observed_position_quantity=2, stop_price=Decimal("12.300"),
                  price_step=Decimal("0.001"), kind="PROTECTIVE_STOP_REPLACE")
        with self.assertRaisesRegex(M15DraftError, "REQUIRES_BACKSTOP"):
            self.contract.protective_stop(**kw)
        with self.assertRaisesRegex(M15DraftError, "STOP_WIDENING"):
            self.contract.protective_stop(**(kw | {"stop_price": Decimal("12.200"),
                                                  "previous_active_stop": Decimal("12.250")}))
        x = self.contract.protective_stop(**(kw | {"previous_active_stop": Decimal("12.250")}))
        self.assertEqual(x.kind, "PROTECTIVE_STOP_REPLACE")
        self.assertEqual(x.payload["sl_price"], {"value": "12.300"})

    def test_short_replacement_widening_denied(self):
        kw = dict(instrument="CNYRUBF", direction="SHORT", idempotency_key="m15:trailshort",
                  observed_position_quantity=-2, stop_price=Decimal("12.900"),
                  previous_active_stop=Decimal("12.750"),
                  price_step=Decimal("0.001"), kind="PROTECTIVE_STOP_REPLACE")
        with self.assertRaisesRegex(M15DraftError, "STOP_WIDENING"):
            self.contract.protective_stop(**kw)

    def test_initial_with_existing_stop_denied(self):
        with self.assertRaisesRegex(M15DraftError, "INITIAL_STOP_ALREADY_EXISTS"):
            self.contract.protective_stop(instrument="CNYRUBF", direction="LONG",
                idempotency_key="m15:sl", observed_position_quantity=2,
                stop_price=Decimal("12.250"), previous_active_stop=Decimal("12.200"),
                price_step=Decimal("0.001"))

    def test_emergency_exit_requires_exact_broker_position(self):
        x = self.contract.emergency_exit(
            instrument="GLDRUBF", direction="SHORT", idempotency_key="m15:emergency",
            observed_position_quantity=-3)
        self.assertEqual(x.payload["side"], "SIDE_BUY")
        self.assertEqual(x.payload["quantity"], {"value": "3"})
        self.assertFalse(x.submitted)
        with self.assertRaisesRegex(M15DraftError, "BROKER_POSITION_NOT_EXACT"):
            self.contract.emergency_exit(instrument="GLDRUBF", direction="LONG",
                idempotency_key="m15:bad", observed_position_quantity=-3)

    def test_transport_structurally_absent(self):
        self.assertFalse(hasattr(self.contract, "connect"))
        self.assertFalse(hasattr(self.contract, "place_order"))
        self.assertFalse(hasattr(self.contract, "place_sltp_order"))
        self.assertFalse(hasattr(self.contract, "cancel_order"))


if __name__ == "__main__":
    unittest.main()
