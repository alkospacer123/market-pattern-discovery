"""H1-style durable M15 outbound flow: NO-LIVE stage, only synthetic data."""
from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest

from IntradayLab.m15_robot.live_execution import (
    M15AuthorizedExecutionTransport, M15ExecutionError, M15OutboundJournal,
    M15PrePostRefused, load_execution_authorization,
)
from IntradayLab.m15_robot.trade_draft_contract import M15Draft


class FakeOrderAPI:
    def __init__(self):
        self.calls = []

    def create_session(self):
        self.calls.append("create_session")

    def session_details(self):
        self.calls.append("session_details")
        return {"readonly": False, "account_ids": ["M15-SYNTH"]}

    def account(self, account_id):
        self.calls.append("account")
        return {"account_id": account_id}

    def place_order(self, account_id, payload):
        self.calls.append("place_order")
        return {"order_id": "test-no-real-order"}

    def place_sltp_order(self, account_id, payload):
        self.calls.append("place_sltp_order")
        return {"order_id": "test-no-real-sltp"}

    def cancel_order(self, account_id, order_id):
        self.calls.append("cancel_order")
        return {}


class M15ExecutionStageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.args = dict(
            runtime_root=root / "m15", h1_runtime_root=root / "h1",
            repository_root=root / "repo", m15_account_id="M15-SYNTH",
            h1_account_sha256=hashlib.sha256(b"H1-DIFFERENT").hexdigest(),
        )
        self.j = M15OutboundJournal(**self.args)
        self.key = "m15:entry:synthetic:1"
        self.draft = self.entry(self.key)

    def tearDown(self):
        self.j.close()
        self.tmp.cleanup()

    @staticmethod
    def entry(key, symbol="CNYRUBF@RTSX", quantity="2", fingerprint=None):
        return M15Draft(
            "ENTRY", fingerprint or hashlib.sha256(b"M15-SYNTH").hexdigest(),
            "REGULAR_ORDER_DRAFT",
            {
                "symbol": symbol, "side": "SIDE_BUY",
                "quantity": {"value": quantity},
                "type": "ORDER_TYPE_MARKET", "time_in_force": "TIME_IN_FORCE_DAY",
                "client_order_id": "m15" + hashlib.sha256(key.encode()).hexdigest()[:17],
            },
        )

    def stop(self, key):
        return M15Draft(
            "PROTECTIVE_STOP_INSTALL", self.j.account_hash, "SLTP_ORDER_DRAFT",
            {"symbol": "CNYRUBF@RTSX", "side": "SIDE_SELL",
             "quantity_sl": {"value": "100"},
             "sl_qty_measure": "SLTP_QTY_MEASURE_PERCENT",
             "sl_price": {"value": "12.400"},
             "valid_before": "VALID_BEFORE_GOOD_TILL_CANCEL",
             "client_order_id": "m15" + hashlib.sha256(key.encode()).hexdigest()[:17],
             "comment": key},
        )

    def test_pre_post_atomic_and_restart_never_retries(self):
        self.assertTrue(self.j.prepare(key=self.key, draft=self.draft))
        self.assertEqual(self.j.inspect(self.key)["state"], "PREPARED")
        self.j.begin_post_uncertain(key=self.key, draft=self.draft)
        self.assertEqual(self.j.inspect(self.key)["state"], "UNCERTAIN")
        self.j.close()
        self.j = M15OutboundJournal(**self.args)
        self.assertFalse(self.j.prepare(key=self.key, draft=self.draft))
        with self.assertRaisesRegex(M15ExecutionError, "ALREADY_SENT"):
            self.j.begin_post_uncertain(key=self.key, draft=self.draft)
        self.assertEqual(self.j.inspect(self.key)["state"], "UNCERTAIN")

    def test_broker_ack_is_only_order_ack_not_fill(self):
        self.j.prepare(key=self.key, draft=self.draft)
        self.j.begin_post_uncertain(key=self.key, draft=self.draft)
        self.j.record_broker_ack(
            key=self.key, draft=self.draft, broker_order_id="synthetic-order-1")
        state = self.j.inspect(self.key)
        self.assertEqual(state["state"], "ACK")
        self.assertEqual(state["broker_order_sha256"],
                         hashlib.sha256(b"synthetic-order-1").hexdigest())
        self.assertFalse(self.j.execution_authorized)
        with self.assertRaisesRegex(M15ExecutionError, "ALREADY_SENT"):
            self.j.begin_post_uncertain(key=self.key, draft=self.draft)

    def test_duplicate_entry_for_instrument_denied(self):
        self.j.prepare(key=self.key, draft=self.draft)
        key2 = "m15:entry:synthetic:2"
        with self.assertRaisesRegex(M15ExecutionError, "INSTRUMENT_OCCUPIED"):
            self.j.prepare(key=key2, draft=self.entry(key2))

    def test_two_instruments_independent(self):
        self.j.prepare(key=self.key, draft=self.draft)
        key2 = "m15:entry:synthetic:2"
        self.assertTrue(self.j.prepare(
            key=key2, draft=self.entry(key2, symbol="USDRUBF@RTSX")))

    def test_reused_key_conflicting_payload_denied(self):
        self.j.prepare(key=self.key, draft=self.draft)
        with self.assertRaisesRegex(M15ExecutionError, "IDEMPOTENCY_CONFLICT"):
            self.j.prepare(key=self.key, draft=self.entry(self.key, quantity="3"))

    def test_wrong_account_draft_denied(self):
        foreign = self.entry(self.key, fingerprint=hashlib.sha256(b"OTHER").hexdigest())
        with self.assertRaisesRegex(M15ExecutionError, "DRAFT_IDENTITY_INVALID"):
            self.j.prepare(key=self.key, draft=foreign)
        self.assertIsNone(self.j.inspect(self.key))

    def test_zero_and_noninteger_quantity_denied(self):
        for bad in ("0", "1.5", "-3", "02"):
            with self.subTest(bad=bad):
                with self.assertRaises(M15ExecutionError):
                    self.j.prepare(key=self.key, draft=self.entry(self.key, quantity=bad))

    def test_bad_market_client_id_denied(self):
        draft = self.entry(self.key)
        draft.payload["client_order_id"] = "other"
        with self.assertRaisesRegex(M15ExecutionError, "CLIENT_ID_MISMATCH"):
            self.j.prepare(key=self.key, draft=draft)

    def test_100_percent_stop_intent_is_separate_no_post(self):
        key = "m15:stop:synthetic:1"
        d = self.stop(key)
        self.assertTrue(self.j.prepare(key=key, draft=d))
        self.assertEqual(self.j.inspect(key)["state"], "PREPARED")
        self.assertFalse(self.j.execution_authorized)

    def test_below_100_percent_stop_denied(self):
        key = "m15:stop:synthetic:1"
        d = self.stop(key)
        d.payload["quantity_sl"] = {"value": "99"}
        with self.assertRaisesRegex(M15ExecutionError, "STOP_PARAMS_INVALID"):
            self.j.prepare(key=key, draft=d)

    def test_foreign_account_binding_refused_on_reopen(self):
        self.j.close()
        with self.assertRaisesRegex(M15ExecutionError, "ACCOUNT_MISMATCH"):
            M15OutboundJournal(**dict(self.args, m15_account_id="M15-OTHER"))
        self.j = M15OutboundJournal(**self.args)

    def test_h1_account_reuse_refused(self):
        with self.assertRaisesRegex(ValueError, "H1_ACCOUNT_REUSE_PROHIBITED"):
            M15OutboundJournal(**dict(
                self.args, h1_account_sha256=self.j.account_hash))

    def test_live_adapter_denies_before_any_broker_session(self):
        api = FakeOrderAPI()
        with self.assertRaisesRegex(M15PrePostRefused, "STATIC_FREEZE"):
            M15AuthorizedExecutionTransport(
                api=api, accepted_commit="a" * 40, **self.args)
        self.assertEqual(api.calls, [])

    def test_authorization_file_cannot_override_frozen_status(self):
        root = self.args["runtime_root"]
        (root / "safety").mkdir(parents=True, exist_ok=True)
        (root / "safety" / "m15-execution-authorization.json").write_text(
            '{"execution_authorized":true}', encoding="utf-8")
        with self.assertRaisesRegex(M15PrePostRefused, "STATIC_FREEZE"):
            load_execution_authorization(
                runtime_root=root, expected_commit="a"*40,
                account_hash=self.j.account_hash,
            )


if __name__ == "__main__":
    unittest.main()
