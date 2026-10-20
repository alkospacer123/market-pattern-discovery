"""H1-style durable M15 outbound flow: NO-LIVE stage, only synthetic data."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from dataclasses import replace
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from IntradayLab.m15_robot.live_execution import (
    M15AuthorizedExecutionTransport, M15ExecutionError, M15OutboundJournal,
    M15PrePostRefused, load_execution_authorization,
)
from IntradayLab.m15_robot.broker_fill_readonly import ExpectedEntry
from IntradayLab.m15_robot.spec import ROBOT_ID
from IntradayLab.m15_robot.cashflow_reconcile_gate import CashflowWindow
from IntradayLab.m15_robot.grid_risk import ContractAuthority, TrailingState, size_r15
from IntradayLab.m15_robot.protective_gate import BrokerProtection
from IntradayLab.m15_robot.trailing_gate import confirm_trail
from IntradayLab.m15_robot.trade_draft_contract import M15Draft, M15OfflineTradeDrafts


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


    def broker_get(self, *, filled=1, second_id="fill-2",
                   second_price="12.501", account="M15-SYNTH",
                   client_id=None, incomplete=False):
        rows = [
            {"trade_id": "fill-1", "order_id": "broker-entry-1",
             "account_id": account, "symbol": "CNYRUBF@RTSX",
             "side": "SIDE_BUY", "currency": "XXX",
             "timestamp": "2026-10-19T10:15:00Z",
             "price": {"value": "12.500"}, "size": {"value": "1"}},
        ] if filled else []
        if filled == 2:
            rows.append({
                "trade_id": second_id, "order_id": "broker-entry-1",
                "account_id": account, "symbol": "CNYRUBF@RTSX",
                "side": "SIDE_BUY", "currency": "XXX",
                "timestamp": "2026-10-19T10:16:00Z",
                "price": {"value": second_price}, "size": {"value": "1"},
            })
        trades = {"trades": rows}
        if incomplete:
            trades["next_cursor"] = "another-page"
        return {
            "key": self.key, "draft": self.draft,
            "expected": ExpectedEntry(
                account_id="M15-SYNTH", order_id="broker-entry-1",
                symbol="CNYRUBF@RTSX", side="SIDE_BUY",
                quantity=2, price_step=Decimal("0.001"),
            ),
            "expected_client_order_id": client_id or
                                        self.draft.payload["client_order_id"],
            "stop_trade_tag": "trade-1",
            "account": {
                "account_id": account, "status": "ACCOUNT_ACTIVE",
                "positions": ([{"symbol": "CNYRUBF@RTSX",
                                "quantity": {"value": str(filled)}}]
                              if filled else []),
            },
            "orders_response": {
                "orders": [{
                    "order_id": "broker-entry-1",
                    "status": ("ORDER_STATUS_FILLED" if filled == 2
                               else "ORDER_STATUS_PARTIAL_FILL" if filled
                               else "ORDER_STATUS_NEW"),
                    "order": {
                        "symbol": "CNYRUBF@RTSX", "side": "SIDE_BUY",
                        "quantity": {"value": "2"},
                        "client_order_id": self.draft.payload["client_order_id"],
                    },
                }],
            },
            "trades_response": trades,
            "start": "2026-10-19T10:00:00Z",
            "end": "2026-10-19T11:00:00Z",
        }

    def test_broker_get_recovers_uncertain_partial_full_without_new_post(self):
        self.j.prepare(key=self.key, draft=self.draft)
        self.j.begin_post_uncertain(key=self.key, draft=self.draft)
        partial = self.j.reconcile_entry_broker_get(**self.broker_get())
        self.assertEqual((partial["matched_quantity"], partial["new_durable_fills"]), (1, 1))
        self.assertEqual(self.j.inspect(self.key)["state"], "ACK")
        self.assertFalse(partial["live_authorized"] or partial["broker_stop_acknowledged"])
        full = self.j.reconcile_entry_broker_get(**self.broker_get(filled=2))
        self.assertEqual((full["matched_quantity"], full["new_durable_fills"]), (2, 1))
        v = full["weighted_vwap_exact"]
        self.assertEqual(Fraction(int(v["numerator"]), int(v["denominator"])),
                         Fraction(25001, 2000))
        self.j.close()
        self.j = M15OutboundJournal(**self.args)
        replay = self.j.reconcile_entry_broker_get(**self.broker_get(filled=2))
        self.assertEqual(replay["new_durable_fills"], 0)
        self.assertEqual(self.j.db.execute(
            "SELECT COUNT(*) FROM broker_fills").fetchone()[0], 2)

    def test_broker_get_rejects_lost_prior_fill_after_restart(self):
        self.j.prepare(key=self.key, draft=self.draft)
        self.j.begin_post_uncertain(key=self.key, draft=self.draft)
        self.j.reconcile_entry_broker_get(**self.broker_get(filled=2))
        with self.assertRaisesRegex(M15ExecutionError, "DURABLE_HISTORY_MISSING"):
            self.j.reconcile_entry_broker_get(**self.broker_get(filled=1))
        self.assertEqual(self.j.db.execute(
            "SELECT COUNT(*) FROM broker_fills").fetchone()[0], 2)

    def test_broker_get_rejects_fill_id_rewrite_same_quantity(self):
        self.j.prepare(key=self.key, draft=self.draft)
        self.j.begin_post_uncertain(key=self.key, draft=self.draft)
        self.j.reconcile_entry_broker_get(**self.broker_get(filled=2))
        with self.assertRaisesRegex(M15ExecutionError, "DURABLE_HISTORY_MISSING"):
            self.j.reconcile_entry_broker_get(**self.broker_get(
                filled=2, second_id="another-fill-id"))
        self.assertEqual(self.j.db.execute(
            "SELECT COUNT(*) FROM broker_fills").fetchone()[0], 2)

    def test_broker_get_requires_post_boundary_not_just_prepared(self):
        self.j.prepare(key=self.key, draft=self.draft)
        with self.assertRaisesRegex(M15ExecutionError, "UNCERTAIN_OR_ACK"):
            self.j.reconcile_entry_broker_get(**self.broker_get())
        self.assertEqual(self.j.db.execute(
            "SELECT COUNT(*) FROM broker_fills").fetchone()[0], 0)

    def test_broker_get_invalid_account_or_pagination_never_writes(self):
        self.j.prepare(key=self.key, draft=self.draft)
        self.j.begin_post_uncertain(key=self.key, draft=self.draft)
        with self.assertRaisesRegex(RuntimeError, "ACCOUNT_BINDING"):
            self.j.reconcile_entry_broker_get(**self.broker_get(account="OTHER"))
        with self.assertRaisesRegex(RuntimeError, "COMPLETENESS_UNPROVEN"):
            self.j.reconcile_entry_broker_get(**self.broker_get(incomplete=True))
        self.assertEqual(self.j.db.execute(
            "SELECT COUNT(*) FROM broker_fills").fetchone()[0], 0)
        self.assertEqual(self.j.inspect(self.key)["state"], "UNCERTAIN")


    def test_broker_full_fill_exact_vwap_to_100_percent_stop_durable(self):
        self.j.prepare(key=self.key, draft=self.draft)
        self.j.begin_post_uncertain(key=self.key, draft=self.draft)
        broker = self.j.reconcile_entry_broker_get(**self.broker_get(filled=2))
        drafts = M15OfflineTradeDrafts(
            m15_account_id=self.args["m15_account_id"],
            h1_account_sha256=self.args["h1_account_sha256"],
            m15_runtime_root=self.args["runtime_root"],
            h1_runtime_root=self.args["h1_runtime_root"],
            repository_root=self.args["repository_root"],
        )
        kwargs = dict(
            entry_key=self.key, entry_draft=self.draft,
            broker_report=broker, stop_key="m15:stop:fill:1",
            drafts=drafts, instrument="CNYRUBF", direction="LONG",
            atr_at_signal=Decimal("0.100"), price_step=Decimal("0.001"),
        )
        stop = self.j.prepare_initial_sltp_from_durable_fills(**kwargs)
        self.assertEqual(stop.payload["sl_price"], {"value": "12.300"})
        self.assertEqual(stop.payload["quantity_sl"], {"value": "100"})
        self.assertEqual(stop.kind, "PROTECTIVE_STOP_INSTALL")
        self.assertEqual(self.j.inspect("m15:stop:fill:1")["state"], "PREPARED")
        self.assertFalse(stop.submitted or stop.live_authorized)
        self.j.close()
        self.j = M15OutboundJournal(**self.args)
        same = self.j.prepare_initial_sltp_from_durable_fills(**kwargs)
        self.assertEqual(same.payload, stop.payload)
        with self.assertRaisesRegex(M15ExecutionError, "DUPLICATE_INITIAL_STOP"):
            self.j.prepare_initial_sltp_from_durable_fills(
                **dict(kwargs, stop_key="m15:stop:fill:2"))

    def test_initial_stop_rejects_unproven_vwap_or_partial_position(self):
        self.j.prepare(key=self.key, draft=self.draft)
        self.j.begin_post_uncertain(key=self.key, draft=self.draft)
        broker = self.j.reconcile_entry_broker_get(**self.broker_get(filled=1))
        drafts = M15OfflineTradeDrafts(
            m15_account_id=self.args["m15_account_id"],
            h1_account_sha256=self.args["h1_account_sha256"],
            m15_runtime_root=self.args["runtime_root"],
            h1_runtime_root=self.args["h1_runtime_root"],
            repository_root=self.args["repository_root"],
        )
        kwargs = dict(
            entry_key=self.key, entry_draft=self.draft, broker_report=broker,
            stop_key="m15:stop:fill:1", drafts=drafts, instrument="CNYRUBF",
            direction="LONG", atr_at_signal=Decimal("0.100"),
            price_step=Decimal("0.001"),
        )
        tampered = dict(broker, weighted_vwap_exact={
            "numerator": "999", "denominator": "1"})
        with self.assertRaisesRegex(M15ExecutionError, "VWAP_RECONCILIATION_FAILED"):
            self.j.prepare_initial_sltp_from_durable_fills(
                **dict(kwargs, broker_report=tampered))
        tampered_qty = dict(broker, broker_position_quantity=2)
        with self.assertRaisesRegex(M15ExecutionError, "QUANTITY_MISMATCH"):
            self.j.prepare_initial_sltp_from_durable_fills(
                **dict(kwargs, broker_report=tampered_qty))
        self.assertIsNone(self.j.inspect("m15:stop:fill:1"))
        partial = self.j.prepare_initial_sltp_from_durable_fills(**kwargs)
        self.assertEqual(partial.payload["sl_price"], {"value": "12.300"})
        self.assertEqual(partial.payload["quantity_sl"], {"value": "100"})
        self.assertFalse(partial.submitted)


    def test_broker_covered_trail_proposal_durable_but_old_stop_unchanged(self):
        drafts = M15OfflineTradeDrafts(
            m15_account_id=self.args["m15_account_id"],
            h1_account_sha256=self.args["h1_account_sha256"],
            m15_runtime_root=self.args["runtime_root"],
            h1_runtime_root=self.args["h1_runtime_root"],
            repository_root=self.args["repository_root"],
        )
        confirmed = TrailingState("USDRUBF", "LONG", Decimal("100"),
                                  Decimal("96"), Decimal("100"))
        stop = BrokerProtection("broker-old-stop", Decimal("96"), 100, 2, True)
        pending, proposal = self.j.prepare_trailing_sltp_from_broker(
            drafts=drafts, stop_key="m15:trail:synthetic:1",
            confirmed=confirmed, broker_stop=stop, broker_position_qty=2,
            completed_at=datetime(2026, 10, 19, 10, 30, tzinfo=timezone.utc),
            high=Decimal("115"), low=Decimal("100"), atr=Decimal("2"),
            price_step=Decimal("1"), survived_completed_bar=True,
        )
        self.assertEqual(confirmed.active_stop, Decimal("96"))
        self.assertEqual(pending.candidate.active_stop, Decimal("108"))
        self.assertEqual(proposal.payload["sl_price"], {"value": "108"})
        self.assertEqual(self.j.inspect("m15:trail:synthetic:1")["state"], "PREPARED")
        self.assertFalse(proposal.submitted or proposal.live_authorized)
        observed = BrokerProtection("broker-new-stop", Decimal("108"), 100, 2, True)
        after = confirm_trail(
            pending, observed_stop=observed, observed_stop_count=1,
            broker_position_qty=2, price_step=Decimal("1"),
        )
        self.assertEqual(after.active_stop, Decimal("108"))

    def test_undercovered_broker_stop_blocks_trail_without_sqlite_intent(self):
        drafts = M15OfflineTradeDrafts(
            m15_account_id=self.args["m15_account_id"],
            h1_account_sha256=self.args["h1_account_sha256"],
            m15_runtime_root=self.args["runtime_root"],
            h1_runtime_root=self.args["h1_runtime_root"],
            repository_root=self.args["repository_root"],
        )
        confirmed = TrailingState("USDRUBF", "LONG", Decimal("100"),
                                  Decimal("96"), Decimal("100"))
        old = BrokerProtection("broker-old-stop", Decimal("96"), 100, 1, True)
        with self.assertRaisesRegex(ValueError, "PROTECTION_NOT_CONFIRMED"):
            self.j.prepare_trailing_sltp_from_broker(
                drafts=drafts, stop_key="m15:trail:synthetic:1",
                confirmed=confirmed, broker_stop=old, broker_position_qty=2,
                completed_at=datetime(2026, 10, 19, 10, 30, tzinfo=timezone.utc),
                high=Decimal("115"), low=Decimal("100"), atr=Decimal("2"),
                price_step=Decimal("1"), survived_completed_bar=True,
            )
        self.assertIsNone(self.j.inspect("m15:trail:synthetic:1"))


    def protection_first_args(self):
        """A synthetic two-contract R15 pre-entry plan, no AccountTrade needed."""
        drafts = M15OfflineTradeDrafts(
            m15_account_id=self.args["m15_account_id"],
            h1_account_sha256=self.args["h1_account_sha256"],
            m15_runtime_root=self.args["runtime_root"],
            h1_runtime_root=self.args["h1_runtime_root"],
            repository_root=self.args["repository_root"],
        )
        contract = ContractAuthority(
            price_step=Decimal("0.001"), tick_value=Decimal("1"),
            trade_lot_size=1, long_initial_margin=Decimal("100"),
            short_initial_margin=Decimal("100"),
        )
        sized = size_r15(
            realized_equity=Decimal("30000"), entry=Decimal("12.500"),
            stop=Decimal("12.300"), contract=contract, direction="LONG",
            available_margin_cash=Decimal("1000"),
        )
        self.assertEqual(sized.final_quantity, 2)
        snapshot = self.broker_get(filled=1)
        return dict(
            entry_key=self.key, entry_draft=self.draft,
            stop_key="m15:stop:precommit:1", drafts=drafts,
            instrument="CNYRUBF", direction="LONG",
            reference_entry=Decimal("12.500"),
            precommitted_stop=Decimal("12.300"),
            atr_at_signal=Decimal("0.100"), contract=contract, sized=sized,
            account=snapshot["account"],
            orders_response=snapshot["orders_response"],
        )

    def test_h1_protection_first_partial_position_without_trade_history(self):
        self.j.prepare(key=self.key, draft=self.draft)
        self.j.begin_post_uncertain(key=self.key, draft=self.draft)
        args = self.protection_first_args()
        # The only broker facts are authenticated-looking account+orders GET,
        # not a trades response. Initial STOP must not wait for fill-price GET.
        proposal = self.j.prepare_initial_sltp_from_broker_position(**args)
        self.assertEqual(proposal.kind, "PROTECTIVE_STOP_INSTALL")
        self.assertEqual(proposal.payload["sl_price"], {"value": "12.300"})
        self.assertEqual(proposal.payload["quantity_sl"], {"value": "100"})
        self.assertEqual(self.j.inspect(self.key)["state"], "ACK")
        self.assertEqual(self.j.inspect(args["stop_key"])["state"], "PREPARED")
        self.assertEqual(
            self.j.db.execute("SELECT COUNT(*) FROM broker_fills").fetchone()[0], 0)
        self.assertFalse(proposal.submitted or proposal.live_authorized)

    def test_h1_protection_first_restarts_idempotently_without_second_stop(self):
        self.j.prepare(key=self.key, draft=self.draft)
        self.j.begin_post_uncertain(key=self.key, draft=self.draft)
        args = self.protection_first_args()
        proposal = self.j.prepare_initial_sltp_from_broker_position(**args)
        self.j.close()
        self.j = M15OutboundJournal(**self.args)
        replay = self.j.prepare_initial_sltp_from_broker_position(**args)
        self.assertEqual(replay.payload, proposal.payload)
        self.assertEqual(
            self.j.db.execute("SELECT COUNT(*) FROM outbound WHERE kind='PROTECTIVE_STOP_INSTALL'").fetchone()[0], 1)
        with self.assertRaisesRegex(M15ExecutionError, "DUPLICATE_INITIAL_STOP"):
            self.j.prepare_initial_sltp_from_broker_position(
                **dict(args, stop_key="m15:stop:precommit:2"))

    def test_h1_protection_first_blocks_wrong_r15_or_stop_or_broker_position(self):
        self.j.prepare(key=self.key, draft=self.draft)
        self.j.begin_post_uncertain(key=self.key, draft=self.draft)
        args = self.protection_first_args()
        with self.assertRaisesRegex(M15ExecutionError, "2ATR_MISMATCH"):
            self.j.prepare_initial_sltp_from_broker_position(
                **dict(args, precommitted_stop=Decimal("12.299")))
        with self.assertRaisesRegex(M15ExecutionError, "R15_GO_INVALID"):
            self.j.prepare_initial_sltp_from_broker_position(
                **dict(args, sized=__import__("dataclasses").replace(
                    args["sized"], final_quantity=3)))
        fake_account = dict(args["account"], account_id="DIFFERENT-ACCOUNT")
        with self.assertRaisesRegex(M15ExecutionError, "BROKER_ACCOUNT_NOT_BOUND"):
            self.j.prepare_initial_sltp_from_broker_position(
                **dict(args, account=fake_account))
        flat_account = dict(args["account"], positions=[])
        with self.assertRaisesRegex(M15ExecutionError, "BROKER_POSITION_NOT_MATCHED"):
            self.j.prepare_initial_sltp_from_broker_position(
                **dict(args, account=flat_account))
        self.assertIsNone(self.j.inspect(args["stop_key"]))
        self.assertEqual(self.j.inspect(self.key)["state"], "UNCERTAIN")

    def test_h1_protection_first_rejects_competing_order_before_stop_prep(self):
        self.j.prepare(key=self.key, draft=self.draft)
        self.j.begin_post_uncertain(key=self.key, draft=self.draft)
        args = self.protection_first_args()
        second = {
            "order_id": "competitor",
            "status": "ORDER_STATUS_NEW",
            "order": dict(args["orders_response"]["orders"][0]["order"]),
        }
        second["order"]["client_order_id"] = "m15other001"
        orders = {"orders": args["orders_response"]["orders"] + [second]}
        with self.assertRaisesRegex(M15ExecutionError, "COMPETING_BROKER_ORDER"):
            self.j.prepare_initial_sltp_from_broker_position(
                **dict(args, orders_response=orders))
        self.assertIsNone(self.j.inspect(args["stop_key"]))


    def protective_observation(self, draft, *, include_new=True, old_stop=None):
        data = self.broker_get(filled=1)
        rows = list(data["orders_response"]["orders"])
        if old_stop is not None:
            rows.append({
                "order_id": "broker-old-stop", "status": "ORDER_STATUS_NEW",
                "sltp_order": dict(old_stop.payload),
            })
        if include_new:
            rows.append({
                "order_id": "broker-new-stop", "status": "ORDER_STATUS_NEW",
                "sltp_order": dict(draft.payload),
            })
        return data["account"], {"orders": rows}

    def test_protective_raw_post_ack_never_proves_stop_coverage(self):
        key = "m15:stop:synthetic:1"
        draft = self.stop(key)
        self.j.prepare(key=key, draft=draft)
        account, before = self.protective_observation(draft, include_new=False)
        self.j.begin_protective_post_uncertain(
            key=key, draft=draft, account=account, orders_response=before)
        with self.assertRaisesRegex(M15ExecutionError, "REQUIRES_ACTIVE_BROKER_GET"):
            self.j.record_broker_ack(
                key=key, draft=draft, broker_order_id="claimed-ack")
        self.assertEqual(self.j.inspect(key)["state"], "UNCERTAIN")
        self.assertEqual(self.j.db.execute(
            "SELECT COUNT(*) FROM protective_coverage").fetchone()[0], 0)

    def test_protective_prepost_unknown_to_verified_active_get_no_retry(self):
        key = "m15:stop:synthetic:1"
        draft = self.stop(key)
        self.j.prepare(key=key, draft=draft)
        account, before = self.protective_observation(draft, include_new=False)
        with self.assertRaisesRegex(M15ExecutionError, "REQUIRES_BROKER_POSITION"):
            self.j.begin_post_uncertain(key=key, draft=draft)
        self.j.begin_protective_post_uncertain(
            key=key, draft=draft, account=account, orders_response=before)
        self.assertEqual(self.j.inspect(key)["state"], "UNCERTAIN")
        after_account, after = self.protective_observation(draft)
        # FINAM may serialize the SAME numeric price/percentage at a new scale.
        after["orders"][-1]["sltp_order"]["sl_price"] = {"value": "12.4"}
        after["orders"][-1]["sltp_order"]["quantity_sl"] = {"value": "100.0"}
        proof = self.j.reconcile_protective_broker_get(
            key=key, draft=draft, account=after_account, orders_response=after)
        self.assertEqual(proof.stop_price, Decimal("12.400"))
        self.assertEqual(proof.percent, 100)
        self.assertEqual(proof.covered_quantity_at_ack, 1)
        self.assertTrue(proof.active)
        self.assertEqual(self.j.inspect(key)["state"], "ACK")
        self.j.close()
        self.j = M15OutboundJournal(**self.args)
        again = self.j.reconcile_protective_broker_get(
            key=key, draft=draft, account=after_account, orders_response=after)
        self.assertEqual(again, proof)
        self.assertEqual(self.j.db.execute(
            "SELECT COUNT(*) FROM protective_coverage").fetchone()[0], 1)

    def test_protective_100_percent_ack_does_not_cover_later_fill(self):
        key = "m15:stop:synthetic:1"
        draft = self.stop(key)
        self.j.prepare(key=key, draft=draft)
        account, before = self.protective_observation(draft, include_new=False)
        self.j.begin_protective_post_uncertain(
            key=key, draft=draft, account=account, orders_response=before)
        account, after = self.protective_observation(draft)
        self.j.reconcile_protective_broker_get(
            key=key, draft=draft, account=account, orders_response=after)
        grown = dict(account, positions=[{
            "symbol": "CNYRUBF@RTSX", "quantity": {"value": "2"}}])
        with self.assertRaisesRegex(M15ExecutionError, "COVERAGE_UNPROVEN"):
            self.j.reconcile_protective_broker_get(
                key=key, draft=draft, account=grown, orders_response=after)
        self.assertEqual(self.j.db.execute(
            "SELECT covered_quantity_at_ack FROM protective_coverage"
        ).fetchone()[0], 1)

    def test_protective_missing_or_mismatched_sltp_never_ack(self):
        key = "m15:stop:synthetic:1"
        draft = self.stop(key)
        self.j.prepare(key=key, draft=draft)
        account, before = self.protective_observation(draft, include_new=False)
        self.j.begin_protective_post_uncertain(
            key=key, draft=draft, account=account, orders_response=before)
        with self.assertRaisesRegex(M15ExecutionError, "NOT_ACTIVE"):
            self.j.reconcile_protective_broker_get(
                key=key, draft=draft, account=account, orders_response=before)
        _, valid = self.protective_observation(draft)
        for field, value in (
            ("sl_price", {"value": "12.399"}),
            ("quantity_sl", {"value": "99"}),
            ("side", "SIDE_BUY"),
        ):
            rows = list(valid["orders"])
            bad = dict(rows[-1], sltp_order={
                **rows[-1]["sltp_order"], field: value})
            with self.subTest(field=field):
                with self.assertRaisesRegex(M15ExecutionError, "MISMATCH"):
                    self.j.reconcile_protective_broker_get(
                        key=key, draft=draft, account=account,
                        orders_response={"orders": rows[:-1] + [bad]})
        self.assertEqual(self.j.inspect(key)["state"], "UNCERTAIN")

    def test_protective_prepost_rejects_wrong_account_and_old_stop(self):
        key = "m15:stop:synthetic:1"
        draft = self.stop(key)
        self.j.prepare(key=key, draft=draft)
        account, before = self.protective_observation(draft, include_new=False)
        with self.assertRaisesRegex(M15ExecutionError, "ACCOUNT_INVALID"):
            self.j.begin_protective_post_uncertain(
                key=key, draft=draft,
                account=dict(account, account_id="H1-ACCOUNT"),
                orders_response=before)
        _, with_stop = self.protective_observation(draft)
        with self.assertRaisesRegex(M15ExecutionError, "EXISTING_STOP"):
            self.j.begin_protective_post_uncertain(
                key=key, draft=draft, account=account,
                orders_response=with_stop)
        self.assertEqual(self.j.inspect(key)["state"], "PREPARED")

    def test_protective_replacement_keeps_broker_backstop_until_new_ack(self):
        old_key = "m15:stop:synthetic:1"
        old = self.stop(old_key)
        new_key = "m15:trail:synthetic:1"
        updated = self.stop(new_key)
        new = M15Draft(
            "PROTECTIVE_STOP_REPLACE", updated.account_fingerprint,
            updated.endpoint, {**updated.payload, "sl_price": {"value": "12.500"}},
        )
        self.j.prepare(key=new_key, draft=new)
        account, prior = self.protective_observation(
            new, include_new=False, old_stop=old)
        with self.assertRaisesRegex(M15ExecutionError, "BACKSTOP_UNPROVEN"):
            self.j.begin_protective_post_uncertain(
                key=new_key, draft=new, account=account,
                orders_response=prior)
        self.j.begin_protective_post_uncertain(
            key=new_key, draft=new, account=account,
            orders_response=prior, prior_active_broker_stop_id="broker-old-stop")
        account, both = self.protective_observation(new, old_stop=old)
        proof = self.j.reconcile_protective_broker_get(
            key=new_key, draft=new, account=account,
            orders_response=both)
        self.assertEqual(proof.stop_price, Decimal("12.500"))
        self.assertEqual(proof.covered_quantity_at_ack, 1)
        self.assertEqual(self.j.inspect(new_key)["state"], "ACK")
        _, without_old = self.protective_observation(new)
        with self.assertRaisesRegex(M15ExecutionError, "OLD_BACKSTOP_MISSING"):
            self.j.reconcile_protective_broker_get(
                key=new_key, draft=new, account=account,
                orders_response=without_old)


    def r15_entry_inputs(self):
        """Synthetic separate M15 FINAM equity/GO/transaction & frozen T1 risk."""
        birth = datetime(2026, 10, 16, 12, tzinfo=timezone.utc)
        now = datetime(2026, 10, 18, 12, tzinfo=timezone.utc)
        account = {
            "account_id": "M15-SYNTH", "status": "ACCOUNT_ACTIVE",
            "type": "FORTS", "open_account_date": birth.isoformat(),
            "positions": [],
            "equity": {"value": "50000.00"},
            "unrealized_profit": {"value": "0.00"},
            "portfolio_forts": {
                "available_cash": {"value": "50000.00"},
                "money_reserved": {"value": "0"},
            },
        }
        windows = [CashflowWindow(
            birth - timedelta(seconds=1), now + timedelta(minutes=1),
            {"transactions": [{
                "id": "deposit-1", "timestamp": birth.isoformat(),
                "transaction_category": "DEPOSIT",
                "change": {"currency_code": "RUB", "units": "50000", "nanos": 0},
            }]},
        )]
        contract = ContractAuthority(
            price_step=Decimal("0.001"), tick_value=Decimal("1"),
            trade_lot_size=1, long_initial_margin=Decimal("100"),
            short_initial_margin=Decimal("100"),
        )
        rub100 = {"currency_code": "RUB", "units": "100", "nanos": 0}
        drafts = M15OfflineTradeDrafts(
            m15_account_id=self.args["m15_account_id"],
            h1_account_sha256=self.args["h1_account_sha256"],
            m15_runtime_root=self.args["runtime_root"],
            h1_runtime_root=self.args["h1_runtime_root"],
            repository_root=self.args["repository_root"],
        )
        return {
            "key": "m15:entry:r15:1", "drafts": drafts, "instrument": "CNYRUBF",
            "direction": "LONG", "reference_entry": Decimal("12.500"),
            "signal_atr": Decimal("0.100"), "contract": contract,
            "asset": {"ticker": "CNYRUBF", "mic": "RTSX", "decimals": 3,
                      "min_step": "1"},
            "asset_params": {"symbol": "CNYRUBF@RTSX",
                             "account_id": "M15-SYNTH", "trade_lot_size": "1",
                             "long_initial_margin": rub100,
                             "short_initial_margin": rub100},
            "account": account, "orders_response": {"orders": []},
            "cashflow_windows": windows,
            "observed_at": now - timedelta(seconds=5), "now": now,
        }

    def test_h1_entry_r15_go_clean_finam_account_to_durable_intent(self):
        args = self.r15_entry_inputs()
        proposal, sized = self.j.prepare_entry_from_broker_r15(**args)
        self.assertEqual(sized.final_quantity, 3)
        self.assertEqual(sized.initial_nominal_risk, Decimal("600"))
        self.assertEqual(proposal.payload["quantity"], {"value": "3"})
        self.assertEqual(proposal.payload["side"], "SIDE_BUY")
        self.assertEqual(self.j.inspect(args["key"])["state"], "PREPARED")
        record = self.j.db.execute(
            "SELECT realized_equity,available_cash,quantity,stop_price,"
            "nominal_initial_risk FROM entry_r15_basis").fetchone()
        self.assertEqual(record, ("50000", "50000.00", 3, "12.300", "600"))
        self.assertFalse(proposal.live_authorized or proposal.submitted)
        self.j.close()
        self.j = M15OutboundJournal(**self.args)
        self.assertEqual(self.j.inspect(args["key"])["state"], "PREPARED")
        self.assertEqual(self.j.db.execute(
            "SELECT COUNT(*) FROM entry_r15_basis").fetchone()[0], 1)

    def test_h1_entry_r15_rejects_stale_or_foreign_account(self):
        args = self.r15_entry_inputs()
        with self.assertRaisesRegex(M15ExecutionError, "STALE"):
            self.j.prepare_entry_from_broker_r15(
                **dict(args, observed_at=args["now"] - timedelta(minutes=5)))
        wrong = dict(args["account"], account_id="H1-SYNTH")
        with self.assertRaisesRegex(M15ExecutionError, "WRONG_FINAM_ACCOUNT"):
            self.j.prepare_entry_from_broker_r15(
                **dict(args, account=wrong))
        self.assertIsNone(self.j.inspect(args["key"]))

    def test_h1_entry_r15_missing_cashflow_or_bad_margin_refused(self):
        args = self.r15_entry_inputs()
        with self.assertRaisesRegex(RuntimeError, "LIFETIME_INCOMPLETE"):
            self.j.prepare_entry_from_broker_r15(
                **dict(args, cashflow_windows=[]))
        wrong = dict(args["asset_params"], long_initial_margin={
            "currency_code": "RUB", "units": "101", "nanos": 0})
        with self.assertRaisesRegex(M15ExecutionError, "CONTRACT_OR_GO_MISMATCH"):
            self.j.prepare_entry_from_broker_r15(
                **dict(args, asset_params=wrong))
        self.assertIsNone(self.j.inspect(args["key"]))

    def test_h1_entry_r15_no_bootstrap_on_existing_position_or_order(self):
        args = self.r15_entry_inputs()
        occupied = dict(args["account"], positions=[{
            "symbol": "USDRUBF@RTSX", "quantity": {"value": "1"}}])
        with self.assertRaisesRegex(M15ExecutionError, "M15_N4_UNOWNED_BROKER_POSITION_OR_ORDER"):
            self.j.prepare_entry_from_broker_r15(
                **dict(args, account=occupied))
        active = self.broker_get(filled=0)["orders_response"]
        with self.assertRaisesRegex(M15ExecutionError, "M15_N4_UNOWNED_BROKER_POSITION_OR_ORDER"):
            self.j.prepare_entry_from_broker_r15(
                **dict(args, orders_response=active))
        self.assertIsNone(self.j.inspect(args["key"]))

    def test_h1_entry_r15_no_second_prepare_without_risk_reconciliation(self):
        args = self.r15_entry_inputs()
        self.j.prepare_entry_from_broker_r15(**args)
        with self.assertRaisesRegex(M15ExecutionError, "UNRESOLVED_OR_DUPLICATE_ENTRY"):
            self.j.prepare_entry_from_broker_r15(**dict(
                args, key="m15:entry:r15:2", instrument="CNYRUBF"))
        self.assertEqual(self.j.db.execute(
            "SELECT COUNT(*) FROM outbound").fetchone()[0], 1)


    def synthetic_owned_n4(self):
        """A complete H1-style GET entry+fills+active stop on first CNY position."""
        data = self.r15_entry_inputs()
        entry, _ = self.j.prepare_entry_from_broker_r15(**data)
        self.j.begin_post_uncertain(key=data["key"], draft=entry)
        order_id = "broker-owned-cny"
        self.j.record_broker_ack(
            key=data["key"], draft=entry, broker_order_id=order_id)
        account = dict(data["account"], positions=[
            {"symbol": "CNYRUBF@RTSX", "quantity": {"value": "3"}},
        ])
        orders = [{
            "order_id": order_id, "status": "ORDER_STATUS_FILLED",
            "order": {**entry.payload},
        }]
        trades = [{
            "trade_id": "owned-fill-" + str(n),
            "account_id": "M15-SYNTH", "order_id": order_id,
            "symbol": "CNYRUBF@RTSX", "side": "SIDE_BUY",
            "currency": "XXX", "timestamp": "2026-10-18T08:15:00Z",
            "price": {"value": "12.500"}, "size": {"value": "1"},
        } for n in range(3)]
        self.j.reconcile_entry_broker_get(
            key=data["key"], draft=entry,
            expected=ExpectedEntry(
                account_id="M15-SYNTH", order_id=order_id,
                symbol="CNYRUBF@RTSX", side="SIDE_BUY",
                quantity=3, price_step=Decimal("0.001"),
            ),
            expected_client_order_id=entry.payload["client_order_id"],
            stop_trade_tag="trade-1", account=account,
            orders_response={"orders": orders}, trades_response={"trades": trades},
            start="2026-10-18T08:00:00Z", end="2026-10-18T09:00:00Z",
        )
        stop_key = "m15:trade-1:stop:0"
        stop = data["drafts"].protective_stop(
            instrument="CNYRUBF", direction="LONG",
            idempotency_key=stop_key, observed_position_quantity=3,
            stop_price=Decimal("12.300"), price_step=Decimal("0.001"),
        )
        self.j.prepare(key=stop_key, draft=stop)
        self.j.begin_protective_post_uncertain(
            key=stop_key, draft=stop, account=account,
            orders_response={"orders": orders},
        )
        all_orders = orders + [{
            "order_id": "broker-owned-cny-stop", "status": "ORDER_STATUS_NEW",
            "sltp_order": dict(stop.payload),
        }]
        self.j.reconcile_protective_broker_get(
            key=stop_key, draft=stop, account=account,
            orders_response={"orders": all_orders},
        )
        data["account"] = account
        data["orders_response"] = {"orders": all_orders}
        return data

    def usd_followup(self, existing):
        return dict(
            existing, key="m15:entry:r15:2", instrument="USDRUBF",
            reference_entry=Decimal("100.00"),
            signal_atr=Decimal("0.10"),
            contract=ContractAuthority(Decimal("0.01"), Decimal("10"), 1,
                                       Decimal("100"), Decimal("100")),
            asset={"ticker": "USDRUBF", "mic": "RTSX",
                   "decimals": 2, "min_step": "1"},
            asset_params={
                **existing["asset_params"],
                "symbol": "USDRUBF@RTSX",
            },
        )

    def test_h1_n4_second_symbol_reserves_existing_broker_risk(self):
        data = self.synthetic_owned_n4()
        self.assertEqual(
            self.j._owned_n4_risk_from_broker(
                positions={"CNYRUBF@RTSX": 3},
                orders=__import__("IntradayLab.m15_robot.broker_snapshot",
                                   fromlist=["order_views"]).order_views(
                                       data["orders_response"]))[0],
            Decimal("600"),
        )
        new, sized = self.j.prepare_entry_from_broker_r15(
            **self.usd_followup(data))
        self.assertEqual(sized.final_quantity, 3)
        self.assertEqual(sized.initial_nominal_risk, Decimal("600"))
        self.assertEqual(new.payload["symbol"], "USDRUBF@RTSX")
        self.assertEqual(self.j.db.execute(
            "SELECT COUNT(*) FROM entry_r15_basis").fetchone()[0], 2)
        self.assertFalse(new.submitted or new.live_authorized)

    def test_h1_n4_position_growth_after_stop_ack_blocks_new_entry(self):
        data = self.synthetic_owned_n4()
        changed = dict(data["account"], positions=[
            {"symbol": "CNYRUBF@RTSX", "quantity": {"value": "4"}},
        ])
        with self.assertRaisesRegex(M15ExecutionError, "POSITION_NOT_FULLY_FILLED"):
            self.j.prepare_entry_from_broker_r15(
                **self.usd_followup(dict(data, account=changed)))
        self.assertEqual(self.j.db.execute(
            "SELECT COUNT(*) FROM entry_r15_basis").fetchone()[0], 1)

    def test_h1_n4_lost_protective_order_blocks_followup(self):
        data = self.synthetic_owned_n4()
        orders = {"orders": data["orders_response"]["orders"][:1]}
        with self.assertRaisesRegex(M15ExecutionError, "ONE_ACTIVE_PROTECTIVE_STOP"):
            self.j.prepare_entry_from_broker_r15(
                **self.usd_followup(dict(data, orders_response=orders)))

    def test_h1_n4_tick_value_cannot_be_forged_by_caller(self):
        args = self.r15_entry_inputs()
        wrong = replace(args["contract"], tick_value=Decimal("0.1"))
        with self.assertRaisesRegex(M15ExecutionError, "CONTRACT_OR_GO_MISMATCH"):
            self.j.prepare_entry_from_broker_r15(
                **dict(args, contract=wrong))
        self.assertIsNone(self.j.inspect(args["key"]))

    def test_h1_n4_unresolved_stop_intent_blocks_new_entry(self):
        data = self.synthetic_owned_n4()
        pending = data["drafts"].protective_stop(
            instrument="CNYRUBF", direction="LONG",
            idempotency_key="m15:pending:replace:1",
            observed_position_quantity=3, stop_price=Decimal("12.300"),
            price_step=Decimal("0.001"), kind="PROTECTIVE_STOP_REPLACE",
            previous_active_stop=Decimal("12.300"),
        )
        self.j.prepare(key="m15:pending:replace:1", draft=pending)
        with self.assertRaisesRegex(M15ExecutionError, "UNRESOLVED_PROTECTIVE"):
            self.j.prepare_entry_from_broker_r15(**self.usd_followup(data))


    def test_h1_emergency_exit_prepost_restart_and_flat_stop_cleanup(self):
        owned = self.synthetic_owned_n4()
        exit_key = "m15:exit:trade-1:emergency"
        proposal = self.j.prepare_emergency_exit_from_broker(
            entry_key=owned["key"], stop_key="m15:trade-1:stop:0",
            exit_key=exit_key, drafts=owned["drafts"],
            account=owned["account"], orders_response=owned["orders_response"],
        )
        self.assertEqual(proposal.kind, "EMERGENCY_EXIT")
        self.assertEqual(proposal.payload["quantity"], {"value": "3"})
        self.assertEqual(proposal.payload["side"], "SIDE_SELL")
        self.assertEqual(self.j.inspect(exit_key)["state"], "PREPARED")
        self.j.begin_exit_post_uncertain(
            entry_key=owned["key"], stop_key="m15:trade-1:stop:0",
            exit_key=exit_key, draft=proposal,
            account=owned["account"], orders_response=owned["orders_response"],
        )
        self.assertEqual(self.j.inspect(exit_key)["state"], "UNCERTAIN")
        self.j.close()
        self.j = M15OutboundJournal(**self.args)
        with self.assertRaisesRegex(M15ExecutionError, "ALREADY_SENT"):
            self.j.begin_exit_post_uncertain(
                entry_key=owned["key"], stop_key="m15:trade-1:stop:0",
                exit_key=exit_key, draft=proposal,
                account=owned["account"], orders_response=owned["orders_response"],
            )
        flat_account = dict(owned["account"], positions=[])
        snapshot = dict(
            entry_key=owned["key"], stop_key="m15:trade-1:stop:0",
            exit_key=exit_key, account=flat_account,
            observed_at=datetime(2026, 10, 18, 12, tzinfo=timezone.utc),
        )
        # Even a broker-flat account cannot remove a still-ACTIVE stop.
        active_result = self.j.observe_flat_broker_get(
            **dict(snapshot, orders_response=owned["orders_response"]))
        self.assertTrue(active_result["active_sltp_cleanup_required"])
        self.assertFalse(active_result["durable_closed"])
        self.assertEqual(
            self.j.db.execute("SELECT COUNT(*) FROM broker_flat").fetchone()[0], 0)
        terminal = [dict(x) for x in owned["orders_response"]["orders"]]
        terminal[-1]["status"] = "ORDER_STATUS_CANCELLED"
        terminal.append({
            "order_id": "broker-exit-one", "status": "ORDER_STATUS_FILLED",
            "order": dict(proposal.payload),
        })
        proven = self.j.observe_flat_broker_get(
            **dict(snapshot, orders_response={"orders": terminal}))
        self.assertTrue(proven["durable_closed"])
        self.assertFalse(proven["active_sltp_cleanup_required"])
        self.assertEqual(proven["reason"], "EMERGENCY_EXIT")
        self.assertFalse(proven["live_authorized"] or proven["new_entries_authorized"])
        self.j.close()
        self.j = M15OutboundJournal(**self.args)
        replay = self.j.observe_flat_broker_get(
            **dict(snapshot, orders_response={"orders": terminal}))
        self.assertEqual(replay, proven)
        self.assertEqual(
            self.j.db.execute("SELECT COUNT(*) FROM broker_flat").fetchone()[0], 1)

    def test_h1_stop_filled_flat_without_exit_is_durably_observed(self):
        owned = self.synthetic_owned_n4()
        flat = dict(owned["account"], positions=[])
        orders = [dict(x) for x in owned["orders_response"]["orders"]]
        orders[-1]["status"] = "ORDER_STATUS_SL_EXECUTED"
        result = self.j.observe_flat_broker_get(
            entry_key=owned["key"], stop_key="m15:trade-1:stop:0",
            account=flat, orders_response={"orders": orders},
            observed_at=datetime(2026, 10, 18, 12, tzinfo=timezone.utc),
        )
        self.assertEqual(result["reason"], "PROTECTIVE_EXECUTED")
        self.assertTrue(result["durable_closed"])
        self.assertFalse(result["new_entries_authorized"])

    def test_h1_flat_cannot_be_claimed_from_broker_position_still_open(self):
        owned = self.synthetic_owned_n4()
        with self.assertRaisesRegex(M15ExecutionError, "BROKER_NOT_FLAT"):
            self.j.observe_flat_broker_get(
                entry_key=owned["key"], stop_key="m15:trade-1:stop:0",
                account=owned["account"],
                orders_response=owned["orders_response"],
                observed_at=datetime(2026, 10, 18, 12, tzinfo=timezone.utc),
            )
        self.assertEqual(
            self.j.db.execute("SELECT COUNT(*) FROM broker_flat").fetchone()[0], 0)

    def test_h1_exit_refuses_uncovered_growth_and_duplicate(self):
        owned = self.synthetic_owned_n4()
        kw = dict(
            entry_key=owned["key"], stop_key="m15:trade-1:stop:0",
            exit_key="m15:exit:trade-1:emergency", drafts=owned["drafts"],
            account=owned["account"], orders_response=owned["orders_response"],
        )
        grown = dict(owned["account"], positions=[
            {"symbol": "CNYRUBF@RTSX", "quantity": {"value": "4"}}])
        with self.assertRaisesRegex(M15ExecutionError, "OPEN_POSITION_CHANGED"):
            self.j.prepare_emergency_exit_from_broker(
                **dict(kw, account=grown))
        draft = self.j.prepare_emergency_exit_from_broker(**kw)
        self.assertEqual(draft.payload["quantity"], {"value": "3"})
        with self.assertRaisesRegex(M15ExecutionError, "DUPLICATE_OR_UNRESOLVED"):
            self.j.prepare_emergency_exit_from_broker(
                **dict(kw, exit_key="m15:exit:trade-1:again"))
        self.assertIsNone(self.j.inspect("m15:exit:trade-1:again"))

    def test_h1_exit_no_false_flat_on_missing_fill_order(self):
        owned = self.synthetic_owned_n4()
        exit_key = "m15:exit:trade-1:emergency"
        draft = self.j.prepare_emergency_exit_from_broker(
            entry_key=owned["key"], stop_key="m15:trade-1:stop:0",
            exit_key=exit_key, drafts=owned["drafts"],
            account=owned["account"], orders_response=owned["orders_response"],
        )
        self.j.begin_exit_post_uncertain(
            entry_key=owned["key"], stop_key="m15:trade-1:stop:0",
            exit_key=exit_key, draft=draft,
            account=owned["account"], orders_response=owned["orders_response"],
        )
        flat = dict(owned["account"], positions=[])
        orders = [dict(x) for x in owned["orders_response"]["orders"]]
        orders[-1]["status"] = "ORDER_STATUS_CANCELLED"
        with self.assertRaisesRegex(M15ExecutionError, "EXIT_FILL_ORDER_UNVERIFIED"):
            self.j.observe_flat_broker_get(
                entry_key=owned["key"], stop_key="m15:trade-1:stop:0",
                exit_key=exit_key, account=flat,
                orders_response={"orders": orders},
                observed_at=datetime(2026, 10, 18, 12, tzinfo=timezone.utc),
            )
        self.assertEqual(
            self.j.db.execute("SELECT COUNT(*) FROM broker_flat").fetchone()[0], 0)


    def test_h1_proven_flat_releases_r15_for_same_symbol_new_trade(self):
        owned = self.synthetic_owned_n4()
        flat = dict(owned["account"], positions=[])
        orders = [dict(x) for x in owned["orders_response"]["orders"]]
        orders[-1]["status"] = "ORDER_STATUS_SL_EXECUTED"
        self.j.observe_flat_broker_get(
            entry_key=owned["key"], stop_key="m15:trade-1:stop:0",
            account=flat, orders_response={"orders": orders},
            observed_at=datetime(2026, 10, 18, 12, tzinfo=timezone.utc),
        )
        risk, occupied = self.j._owned_n4_risk_from_broker(
            positions={}, orders=__import__(
                "IntradayLab.m15_robot.broker_snapshot",
                fromlist=["order_views"]).order_views({"orders": orders}))
        self.assertEqual(risk, Decimal("0"))
        self.assertEqual(occupied, set())
        proposal, size = self.j.prepare_entry_from_broker_r15(
            **dict(owned, key="m15:entry:r15:new-cycle",
                   account=flat, orders_response={"orders": orders}))
        self.assertEqual(proposal.payload["symbol"], "CNYRUBF@RTSX")
        self.assertEqual(size.final_quantity, 3)
        self.assertEqual(self.j.db.execute(
            "SELECT COUNT(*) FROM broker_flat").fetchone()[0], 1)
        self.assertEqual(self.j.db.execute(
            "SELECT COUNT(*) FROM entry_r15_basis").fetchone()[0], 2)
        self.assertFalse(proposal.live_authorized)

    def test_h1_flat_not_released_while_orphan_sltp_active(self):
        owned = self.synthetic_owned_n4()
        flat = dict(owned["account"], positions=[])
        observed = self.j.observe_flat_broker_get(
            entry_key=owned["key"], stop_key="m15:trade-1:stop:0",
            account=flat, orders_response=owned["orders_response"],
            observed_at=datetime(2026, 10, 18, 12, tzinfo=timezone.utc),
        )
        self.assertTrue(observed["active_sltp_cleanup_required"])
        with self.assertRaisesRegex(M15ExecutionError, "POSITION_OR_ORDER_UNOWNED"):
            self.j.prepare_entry_from_broker_r15(
                **dict(owned, key="m15:entry:r15:new-cycle",
                       account=flat))
        self.assertIsNone(self.j.inspect("m15:entry:r15:new-cycle"))


    def test_h1_emergency_exit_rejects_broker_stop_rewritten_same_id(self):
        owned = self.synthetic_owned_n4()
        args = dict(
            entry_key=owned["key"], stop_key="m15:trade-1:stop:0",
            exit_key="m15:exit:trade-1:emergency", drafts=owned["drafts"],
            account=owned["account"],
        )
        for value in ({"sl_price": {"value": "12.299"}},
                      {"quantity_sl": {"value": "95"}}):
            orders = [dict(x) for x in owned["orders_response"]["orders"]]
            orders[-1]["sltp_order"] = {**orders[-1]["sltp_order"], **value}
            with self.subTest(value=value):
                with self.assertRaisesRegex(M15ExecutionError, "STOP_OWNERSHIP_MISMATCH"):
                    self.j.prepare_emergency_exit_from_broker(
                        **dict(args, orders_response={"orders": orders}))
        self.assertIsNone(self.j.inspect(args["exit_key"]))


    def test_h1_flat_stop_cancel_unknown_restart_second_get_proves_cleanup(self):
        owned = self.synthetic_owned_n4()
        exit_key = "m15:exit:trade-1:cleanup"
        draft = self.j.prepare_emergency_exit_from_broker(
            entry_key=owned["key"], stop_key="m15:trade-1:stop:0",
            exit_key=exit_key, drafts=owned["drafts"],
            account=owned["account"], orders_response=owned["orders_response"],
        )
        self.j.begin_exit_post_uncertain(
            entry_key=owned["key"], stop_key="m15:trade-1:stop:0",
            exit_key=exit_key, draft=draft, account=owned["account"],
            orders_response=owned["orders_response"],
        )
        flat = dict(owned["account"], positions=[])
        observed = datetime(2026, 10, 18, 12, tzinfo=timezone.utc)
        kwargs = dict(
            entry_key=owned["key"], stop_key="m15:trade-1:stop:0",
            broker_order_id="broker-owned-cny-stop", account=flat,
            orders_response=owned["orders_response"], observed_at=observed,
        )
        self.j.begin_flat_stop_cancel_uncertain(**kwargs)
        self.assertEqual(self.j.db.execute(
            "SELECT state FROM flat_stop_cleanup").fetchone()[0], "UNCERTAIN")
        self.j.close()
        self.j = M15OutboundJournal(**self.args)
        with self.assertRaisesRegex(M15ExecutionError, "ALREADY_ATTEMPTED"):
            self.j.begin_flat_stop_cancel_uncertain(**kwargs)
        pending = self.j.observe_flat_broker_get(
            entry_key=owned["key"], stop_key="m15:trade-1:stop:0",
            exit_key=exit_key, account=flat, observed_at=observed,
            orders_response=owned["orders_response"],
        )
        self.assertTrue(pending["active_sltp_cleanup_required"])
        self.assertFalse(pending["durable_closed"])
        finished = [dict(x) for x in owned["orders_response"]["orders"]]
        finished[-1]["status"] = "ORDER_STATUS_CANCELLED"
        finished.append({
            "order_id": "broker-exit-for-cleanup",
            "status": "ORDER_STATUS_FILLED",
            "order": dict(draft.payload),
        })
        done = self.j.observe_flat_broker_get(
            entry_key=owned["key"], stop_key="m15:trade-1:stop:0",
            exit_key=exit_key, account=flat, observed_at=observed,
            orders_response={"orders": finished},
        )
        self.assertTrue(done["durable_closed"])
        self.assertEqual(self.j.db.execute(
            "SELECT state FROM flat_stop_cleanup").fetchone()[0], "RECONCILED")

    def test_h1_flat_stop_cancel_rejects_wrong_stop_or_nonflat_without_write(self):
        owned = self.synthetic_owned_n4()
        args = dict(
            entry_key=owned["key"], stop_key="m15:trade-1:stop:0",
            broker_order_id="not-own-stop",
            account=dict(owned["account"], positions=[]),
            orders_response=owned["orders_response"],
            observed_at=datetime(2026, 10, 18, 12, tzinfo=timezone.utc),
        )
        with self.assertRaisesRegex(M15ExecutionError, "OWNED_ACTIVE_STOP_REQUIRED"):
            self.j.begin_flat_stop_cancel_uncertain(**args)
        with self.assertRaisesRegex(M15ExecutionError, "BROKER_NOT_FLAT"):
            self.j.begin_flat_stop_cancel_uncertain(
                **dict(args, broker_order_id="broker-owned-cny-stop",
                       account=owned["account"]))
        self.assertEqual(self.j.db.execute(
            "SELECT COUNT(*) FROM flat_stop_cleanup").fetchone()[0], 0)

    def test_h1_cancel_http_receipt_alone_never_proves_flat_close(self):
        owned = self.synthetic_owned_n4()
        flat = dict(owned["account"], positions=[])
        observed = datetime(2026, 10, 18, 12, tzinfo=timezone.utc)
        self.j.begin_flat_stop_cancel_uncertain(
            entry_key=owned["key"], stop_key="m15:trade-1:stop:0",
            broker_order_id="broker-owned-cny-stop",
            account=flat, orders_response=owned["orders_response"],
            observed_at=observed,
        )
        after = [dict(x) for x in owned["orders_response"]["orders"]]
        after[-1]["status"] = "ORDER_STATUS_CANCELLED"
        with self.assertRaisesRegex(M15ExecutionError, "PROTECTIVE_EXECUTION_UNVERIFIED"):
            self.j.observe_flat_broker_get(
                entry_key=owned["key"], stop_key="m15:trade-1:stop:0",
                account=flat, orders_response={"orders": after},
                observed_at=observed,
            )
        self.assertEqual(self.j.db.execute(
            "SELECT state FROM flat_stop_cleanup").fetchone()[0], "UNCERTAIN")
        self.assertEqual(self.j.db.execute(
            "SELECT COUNT(*) FROM broker_flat").fetchone()[0], 0)


    def h1_entry_prepost_args(self):
        """Same synthetic FINAM account/GO/initial equity already audited for R15."""
        data = self.r15_entry_inputs()
        draft, _ = self.j.prepare_entry_from_broker_r15(**data)
        now = data["now"]
        schedule = {"sessions": [{
            "type": "CORE_TRADING",
            "interval": {
                "start_time": (now - timedelta(hours=1)).isoformat(),
                "end_time": (now + timedelta(hours=1)).isoformat(),
            },
        }]}
        kwargs = {
            "key": data["key"], "draft": draft,
            "account": data["account"],
            "orders_response": data["orders_response"],
            "asset": data["asset"],
            "asset_params": data["asset_params"],
            "schedule": schedule,
            "signal_atr": data["signal_atr"],
            "signal_closed_at": now,
            "now": now,
        }
        return data, kwargs

    def test_h1_entry_prepost_fresh_n4_r15_to_uncertain_once(self):
        data, kw = self.h1_entry_prepost_args()
        self.j.begin_entry_post_uncertain_checked(**kw)
        self.assertEqual(self.j.inspect(data["key"])["state"], "UNCERTAIN")
        self.assertEqual(
            self.j.db.execute("SELECT COUNT(*) FROM entry_r15_basis").fetchone()[0], 1)
        self.j.close()
        self.j = M15OutboundJournal(**self.args)
        with self.assertRaisesRegex(M15ExecutionError, "DURABLE_R15_MISSING"):
            self.j.begin_entry_post_uncertain_checked(**kw)
        self.assertEqual(self.j.inspect(data["key"])["state"], "UNCERTAIN")

    def test_h1_entry_prepost_stale_basis_and_offtime_never_send(self):
        data, kw = self.h1_entry_prepost_args()
        with self.assertRaisesRegex(M15ExecutionError, "R15_STALE"):
            self.j.begin_entry_post_uncertain_checked(**dict(
                kw, now=kw["now"] + timedelta(minutes=15),
                signal_closed_at=kw["now"] + timedelta(minutes=15)))
        with self.assertRaisesRegex(M15ExecutionError, "NOT_NEXT_OPEN"):
            self.j.begin_entry_post_uncertain_checked(**dict(
                kw, signal_closed_at=kw["now"] - timedelta(minutes=15)))
        with self.assertRaisesRegex(M15ExecutionError, "SESSION_NOT_OPEN"):
            closed = {"sessions": [{
                "type": "CORE_TRADING", "interval": {
                    "start_time": (kw["now"] - timedelta(hours=2)).isoformat(),
                    "end_time": (kw["now"] - timedelta(hours=1)).isoformat(),
                },
            }]}
            self.j.begin_entry_post_uncertain_checked(**dict(
                kw, schedule=closed))
        self.assertEqual(self.j.inspect(data["key"])["state"], "PREPARED")

    def test_h1_entry_prepost_capital_go_or_broker_account_changed(self):
        data, kw = self.h1_entry_prepost_args()
        mutated = dict(kw["account"], equity={"value": "49999"})
        with self.assertRaisesRegex(M15ExecutionError, "CAPITAL_OR_GO_CHANGED"):
            self.j.begin_entry_post_uncertain_checked(**dict(
                kw, account=mutated))
        bad_go = dict(kw["asset_params"], long_initial_margin={
            "currency_code": "RUB", "units": "20000", "nanos": 0})
        with self.assertRaisesRegex(M15ExecutionError, "R15_GO_RECALC_MISMATCH"):
            self.j.begin_entry_post_uncertain_checked(**dict(
                kw, asset_params=bad_go))
        with self.assertRaisesRegex(M15ExecutionError, "ACCOUNT_MISMATCH"):
            self.j.begin_entry_post_uncertain_checked(**dict(
                kw, account=dict(kw["account"], account_id="H1-ACCOUNT")))
        self.assertEqual(self.j.inspect(data["key"])["state"], "PREPARED")

    def test_h1_entry_prepost_rejects_foreign_active_order_or_position(self):
        data, kw = self.h1_entry_prepost_args()
        with self.assertRaisesRegex(M15ExecutionError, "UNOWNED_BROKER"):
            self.j.begin_entry_post_uncertain_checked(**dict(
                kw, account=dict(kw["account"], positions=[{
                    "symbol": "USDRUBF@RTSX", "quantity": {"value": "1"},
                }])))
        with self.assertRaisesRegex(M15ExecutionError, "UNOWNED_BROKER"):
            self.j.begin_entry_post_uncertain_checked(**dict(
                kw, orders_response=self.broker_get(filled=0)["orders_response"]))
        self.assertEqual(self.j.inspect(data["key"])["state"], "PREPARED")

    def test_h1_n4_second_prepared_entry_not_double_counted_prepost(self):
        owned = self.synthetic_owned_n4()
        candidate = self.usd_followup(owned)
        draft, size = self.j.prepare_entry_from_broker_r15(**candidate)
        self.assertEqual(size.final_quantity, 3)
        now = candidate["now"]
        session = {"sessions": [{
            "type": "CORE_TRADING",
            "interval": {
                "start_time": (now - timedelta(hours=1)).isoformat(),
                "end_time": (now + timedelta(hours=1)).isoformat(),
            },
        }]}
        self.j.begin_entry_post_uncertain_checked(
            key=candidate["key"], draft=draft, account=candidate["account"],
            orders_response=candidate["orders_response"],
            asset=candidate["asset"], asset_params=candidate["asset_params"],
            schedule=session, signal_atr=candidate["signal_atr"],
            signal_closed_at=now, now=now,
        )
        self.assertEqual(self.j.inspect(candidate["key"])["state"], "UNCERTAIN")
        self.assertEqual(self.j.inspect(owned["key"])["state"], "ACK")
        self.assertEqual(self.j.db.execute(
            "SELECT COUNT(*) FROM entry_r15_basis").fetchone()[0], 2)

    def test_h1_entry_prepost_rejects_repriced_atr_or_bad_session_format(self):
        data, kw = self.h1_entry_prepost_args()
        with self.assertRaisesRegex(M15ExecutionError, "2ATR_GRID_CHANGED"):
            self.j.begin_entry_post_uncertain_checked(**dict(
                kw, signal_atr=Decimal("0.150")))
        with self.assertRaisesRegex(RuntimeError, "NO_TRADING_SESSIONS"):
            self.j.begin_entry_post_uncertain_checked(**dict(
                kw, schedule={"sessions": []}))
        self.assertEqual(self.j.inspect(data["key"])["state"], "PREPARED")

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



    def test_m15_entry_requires_armed_fresh_reconciled_production_evidence(self):
        from IntradayLab.m15_robot.live_execution import require_m15_production_entry_gate
        now = datetime.now(timezone.utc)
        args = dict(runtime_root=self.args["runtime_root"], accepted_commit="a"*40,
                    account_hash=self.j.account_hash, now=now)
        with self.assertRaisesRegex(M15PrePostRefused, "EVIDENCE_MISSING"):
            require_m15_production_entry_gate(**args)
        root = args["runtime_root"]
        (root / "safety").mkdir(exist_ok=True)
        (root / "diagnostics").mkdir(exist_ok=True)
        sw_path = root / "safety" / "m15-trading-kill-switch.json"
        hb_path = root / "diagnostics" / "m15-production-heartbeat.json"
        sw = {"schema_id":"m15_trading_kill_switch.v1", "robot_id":ROBOT_ID,
              "state":"HALTED", "generation":1,
              "updated_utc":(now-timedelta(days=1)).isoformat()}
        hb = {"schema_id":"m15_production_heartbeat.v1", "robot_id":ROBOT_ID,
              "accepted_code_commit":args["accepted_commit"],
              "account_hash":args["account_hash"], "reconciliation_status":"PASS",
              "health_status":"HEALTHY", "cycle_count":1, "unresolved_intent_count":0,
              "kill_switch_generation":1, "position_protection_verified":True,
              "timestamp":now.isoformat(),
              "last_successful_finam_api_contact":now.isoformat()}
        sw_path.write_text(json.dumps(sw),encoding="utf-8")
        hb_path.write_text(json.dumps(hb),encoding="utf-8")
        with self.assertRaisesRegex(M15PrePostRefused, "NOT_ARMED"):
            require_m15_production_entry_gate(**args)
        sw["state"]="ARMED"
        sw_path.write_text(json.dumps(sw),encoding="utf-8")
        require_m15_production_entry_gate(**args)
        hb["unresolved_intent_count"]=1
        hb_path.write_text(json.dumps(hb),encoding="utf-8")
        with self.assertRaisesRegex(M15PrePostRefused, "NOT_RECONCILED"):
            require_m15_production_entry_gate(**args)
        hb["unresolved_intent_count"]=0
        hb["last_successful_finam_api_contact"]=(now-timedelta(minutes=2)).isoformat()
        hb_path.write_text(json.dumps(hb),encoding="utf-8")
        with self.assertRaisesRegex(M15PrePostRefused, "EVIDENCE_STALE"):
            require_m15_production_entry_gate(**args)
        hb["last_successful_finam_api_contact"]=now.isoformat()
        hb["accepted_code_commit"]="b"*40
        hb_path.write_text(json.dumps(hb),encoding="utf-8")
        with self.assertRaisesRegex(M15PrePostRefused, "NOT_RECONCILED"):
            require_m15_production_entry_gate(**args)


    def test_same_trading_jwt_entry_fill_recovery_uses_only_three_gets(self):
        from IntradayLab.m15_robot.finam_trading import M15FinamTradingAPI
        controller = object.__new__(M15AuthorizedExecutionTransport)
        controller.api = object.__new__(M15FinamTradingAPI)
        controller.account_id = self.args["m15_account_id"]
        controller.account_hash = self.j.account_hash
        controller.runtime_root = self.args["runtime_root"]
        controller._require_connected = lambda: None  # synthetic, no FINAM
        expected = ExpectedEntry(
            "M15-SYNTH", "broker-order-1", "CNYRUBF@RTSX",
            "SIDE_BUY", 2, Decimal("0.001"),
        )
        first = {"account_id": "M15-SYNTH", "positions": []}
        orders = {"orders": []}
        trades = {"trades": []}
        start, end = "2026-10-20T08:00:00+00:00", "2026-10-20T09:00:00+00:00"
        with (patch.object(M15FinamTradingAPI, "account", return_value=first) as a,
              patch.object(M15FinamTradingAPI, "orders", return_value=orders) as o,
              patch.object(M15FinamTradingAPI, "trades", return_value=trades) as t,
              patch.object(self.j, "reconcile_entry_broker_get",
                           return_value={"matched_quantity": 0,
                                         "live_authorized": False}) as adopted):
            result = controller.reconcile_entry_from_finam(
                journal=self.j, key=self.key, draft=self.draft,
                expected=expected, stop_trade_tag="test-order",
                start=start, end=end,
            )
            self.assertEqual(result["matched_quantity"], 0)
            self.assertFalse(result["live_authorized"])
            a.assert_called_once_with("M15-SYNTH")
            o.assert_called_once_with("M15-SYNTH")
            t.assert_called_once_with(
                "M15-SYNTH", start=start, end=end, limit=1000)
            kwargs = adopted.call_args.kwargs
            self.assertIs(kwargs["account"], first)
            self.assertIs(kwargs["orders_response"], orders)
            self.assertIs(kwargs["trades_response"], trades)
            self.assertEqual(
                kwargs["expected_client_order_id"],
                self.draft.payload["client_order_id"],
            )
        foreign = ExpectedEntry(
            "OTHER", "broker-order-1", "CNYRUBF@RTSX",
            "SIDE_BUY", 2, Decimal("0.001"),
        )
        with self.assertRaisesRegex(M15ExecutionError, "SESSION_OR_ACCOUNT_INVALID"):
            controller.reconcile_entry_from_finam(
                journal=self.j, key=self.key, draft=self.draft,
                expected=foreign, stop_trade_tag="test-order",
                start=start, end=end,
            )


    def test_uncertain_entry_without_post_ack_recovers_exact_broker_client_id(self):
        from IntradayLab.m15_robot.finam_trading import M15FinamTradingAPI
        self.j.prepare(key=self.key, draft=self.draft)
        self.j.begin_post_uncertain(key=self.key, draft=self.draft)
        broker = self.broker_get(filled=1)
        source = self.r15_entry_inputs()
        controller = object.__new__(M15AuthorizedExecutionTransport)
        controller.api = object.__new__(M15FinamTradingAPI)
        controller.account_id = "M15-SYNTH"
        controller.account_hash = self.j.account_hash
        controller.runtime_root = self.args["runtime_root"]
        controller._require_connected = lambda: None
        payload = dict(journal=self.j, key=self.key, draft=self.draft,
                       expected=None, stop_trade_tag="trade-1",
                       start=broker["start"], end=broker["end"])
        with (patch.object(M15FinamTradingAPI, "account",
                           return_value=broker["account"]) as a,
              patch.object(M15FinamTradingAPI, "orders",
                           return_value=broker["orders_response"]) as o,
              patch.object(M15FinamTradingAPI, "asset_details",
                           return_value=source["asset"]) as asset,
              patch.object(M15FinamTradingAPI, "asset_params",
                           return_value=source["asset_params"]) as params,
              patch.object(M15FinamTradingAPI, "trades",
                           return_value=broker["trades_response"]) as trades):
            first = controller.reconcile_entry_from_finam(**payload)
            self.assertEqual(first["matched_quantity"], 1)
            self.assertEqual(first["new_durable_fills"], 1)
            self.assertFalse(first["broker_stop_acknowledged"])
            self.assertEqual(self.j.inspect(self.key)["state"], "ACK")
            self.assertEqual(
                self.j.inspect(self.key)["broker_order_sha256"],
                hashlib.sha256(b"broker-entry-1").hexdigest())
            second = controller.reconcile_entry_from_finam(**payload)
            self.assertEqual(second["new_durable_fills"], 0)
            a.assert_called()
            o.assert_called()
            asset.assert_called()
            params.assert_called()
            trades.assert_called()
        self.assertEqual(
            self.j.db.execute("SELECT COUNT(*) FROM broker_fills").fetchone()[0], 1)

    def test_uncertain_entry_missing_or_duplicate_client_order_never_reposts(self):
        from IntradayLab.m15_robot.finam_trading import M15FinamTradingAPI
        self.j.prepare(key=self.key, draft=self.draft)
        self.j.begin_post_uncertain(key=self.key, draft=self.draft)
        source = self.broker_get(filled=1)
        controller = object.__new__(M15AuthorizedExecutionTransport)
        controller.api = object.__new__(M15FinamTradingAPI)
        controller.account_id = "M15-SYNTH"
        controller.account_hash = self.j.account_hash
        controller.runtime_root = self.args["runtime_root"]
        controller._require_connected = lambda: None
        payload = dict(journal=self.j, key=self.key, draft=self.draft,
                       expected=None, stop_trade_tag="trade-1",
                       start=source["start"], end=source["end"])
        with (patch.object(M15FinamTradingAPI, "account",
                           return_value=source["account"]),
              patch.object(M15FinamTradingAPI, "orders",
                           return_value={"orders": []})):
            with self.assertRaisesRegex(
                    M15ExecutionError, "CLIENT_ORDER_NOT_FOUND_NO_REPOST"):
                controller.reconcile_entry_from_finam(**payload)
        duplicate = dict(source["orders_response"]["orders"][0])
        duplicate["order_id"] = "broker-other-entry"
        with (patch.object(M15FinamTradingAPI, "account",
                           return_value=source["account"]),
              patch.object(M15FinamTradingAPI, "orders",
                           return_value={"orders": source["orders_response"]["orders"]
                                                 + [duplicate]})):
            with self.assertRaisesRegex(
                    RuntimeError, "DUPLICATE_CLIENT_ORDER_ID"):
                controller.reconcile_entry_from_finam(**payload)
        self.assertEqual(self.j.inspect(self.key)["state"], "UNCERTAIN")
        self.assertEqual(
            self.j.db.execute("SELECT COUNT(*) FROM broker_fills").fetchone()[0], 0)


    def test_stop_first_same_session_get_requires_durable_r15_then_100pct_ack(self):
        from IntradayLab.m15_robot.finam_trading import M15FinamTradingAPI
        seed = self.r15_entry_inputs()
        entry, sized = self.j.prepare_entry_from_broker_r15(**seed)
        self.j.begin_post_uncertain(key=seed["key"], draft=entry)
        broker = self.broker_get(filled=1)
        broker["orders_response"]["orders"][0]["order"]["client_order_id"] = (
            entry.payload["client_order_id"])
        broker["orders_response"]["orders"][0]["order"]["quantity"] = {"value": "3"}
        controller = object.__new__(M15AuthorizedExecutionTransport)
        controller.api = object.__new__(M15FinamTradingAPI)
        controller.account_id = "M15-SYNTH"
        controller.account_hash = self.j.account_hash
        controller.runtime_root = self.args["runtime_root"]
        controller._require_connected = lambda: None
        stop_key = "m15:stop:same-jwt:1"
        args = dict(journal=self.j, entry_key=seed["key"],
                    entry_draft=entry, stop_key=stop_key,
                    drafts=seed["drafts"], instrument="CNYRUBF",
                    direction="LONG", reference_entry=seed["reference_entry"],
                    precommitted_stop=Decimal("12.300"),
                    atr_at_signal=seed["signal_atr"],
                    contract=seed["contract"], sized=sized)
        with (patch.object(M15FinamTradingAPI, "asset_details",
                           return_value=seed["asset"]) as a,
              patch.object(M15FinamTradingAPI, "asset_params",
                           return_value=seed["asset_params"]) as p,
              patch.object(M15FinamTradingAPI, "account",
                           return_value=broker["account"]) as acct,
              patch.object(M15FinamTradingAPI, "orders",
                           return_value=broker["orders_response"]) as orders):
            with self.assertRaisesRegex(M15ExecutionError, "DURABLE_R15_BASIS_MISMATCH"):
                controller.prepare_initial_stop_from_finam(
                    **dict(args, precommitted_stop=Decimal("12.299")))
            self.assertEqual(orders.call_count, 0)
            stop = controller.prepare_initial_stop_from_finam(**args)
            self.assertEqual(stop.kind, "PROTECTIVE_STOP_INSTALL")
            self.assertEqual(stop.payload["sl_price"], {"value": "12.300"})
            self.assertEqual(stop.payload["quantity_sl"], {"value": "100"})
            self.assertEqual(self.j.inspect(stop_key)["state"], "PREPARED")
            self.assertEqual(self.j.inspect(seed["key"])["state"], "ACK")
            self.assertEqual(orders.call_count, 1)
            self.j.begin_protective_post_uncertain(
                key=stop_key, draft=stop,
                account=broker["account"],
                orders_response=broker["orders_response"])
            after = {"orders": broker["orders_response"]["orders"] + [{
                "order_id": "broker-M15-stop", "status": "ORDER_STATUS_NEW",
                "sltp_order": dict(stop.payload),
            }]}
            orders.return_value = after
            proof = controller.reconcile_protective_from_finam(
                journal=self.j, key=stop_key, draft=stop)
            self.assertEqual(proof.covered_quantity_at_ack, 1)
            self.assertEqual(proof.stop_price, Decimal("12.300"))
            self.assertTrue(proof.active)
            self.assertEqual(self.j.inspect(stop_key)["state"], "ACK")
            self.assertEqual(self.j.db.execute(
                "SELECT COUNT(*) FROM protective_coverage").fetchone()[0], 1)
            a.assert_called_once_with("CNYRUBF@RTSX")
            p.assert_called_once_with("CNYRUBF@RTSX")
            self.assertEqual(acct.call_count, 2)
            self.assertEqual(orders.call_count, 2)

    def test_protective_same_session_without_active_stop_cannot_ack(self):
        from IntradayLab.m15_robot.finam_trading import M15FinamTradingAPI
        key = "m15:stop:synthetic:1"
        stop = self.stop(key)
        self.j.prepare(key=key, draft=stop)
        account, before = self.protective_observation(stop, include_new=False)
        self.j.begin_protective_post_uncertain(
            key=key, draft=stop, account=account, orders_response=before)
        controller = object.__new__(M15AuthorizedExecutionTransport)
        controller.api = object.__new__(M15FinamTradingAPI)
        controller.account_id = "M15-SYNTH"
        controller.account_hash = self.j.account_hash
        controller.runtime_root = self.args["runtime_root"]
        controller._require_connected = lambda: None
        with (patch.object(M15FinamTradingAPI, "account", return_value=account),
              patch.object(M15FinamTradingAPI, "orders", return_value=before)):
            with self.assertRaisesRegex(M15ExecutionError, "EXACT_STOP_NOT_ACTIVE"):
                controller.reconcile_protective_from_finam(
                    journal=self.j, key=key, draft=stop)
        self.assertEqual(self.j.inspect(key)["state"], "UNCERTAIN")
        self.assertEqual(self.j.db.execute(
            "SELECT COUNT(*) FROM protective_coverage").fetchone()[0], 0)



    def test_readonly_cycle_prepared_intent_never_reposts(self):
        from IntradayLab.m15_robot.execution_cycle import reconcile_m15_readonly_once
        from IntradayLab.m15_robot.finam_readonly import M15FinamReadOnlyAPI
        self.j.prepare(key=self.key, draft=self.draft)
        api = object.__new__(M15FinamReadOnlyAPI)
        account = {"account_id": "M15-SYNTH", "status": "ACCOUNT_ACTIVE",
                   "positions": []}
        with (patch.object(M15FinamReadOnlyAPI, "readonly_bound", True),
              patch.object(M15FinamReadOnlyAPI, "account_id", "M15-SYNTH"),
              patch.object(M15FinamReadOnlyAPI, "account", return_value=account) as a,
              patch.object(M15FinamReadOnlyAPI, "orders",
                           return_value={"orders": []}) as o):
            first = reconcile_m15_readonly_once(
                journal=self.j, api=api, m15_account_id="M15-SYNTH")
            self.assertEqual(first["events"][0]["state"], "ENTRY_PREPARED_NOT_SENT")
            self.assertFalse(first["new_entries_authorized"])
            self.assertEqual(self.j.inspect(self.key)["state"], "PREPARED")
            self.j.close()
            self.j = M15OutboundJournal(**self.args)
            second = reconcile_m15_readonly_once(
                journal=self.j, api=api, m15_account_id="M15-SYNTH")
            self.assertEqual(first, second)
            self.assertEqual(a.call_count, 2)
            self.assertEqual(o.call_count, 2)

    def test_readonly_cycle_uncertain_missing_order_never_resends(self):
        from IntradayLab.m15_robot.execution_cycle import reconcile_m15_readonly_once
        from IntradayLab.m15_robot.finam_readonly import M15FinamReadOnlyAPI
        self.j.prepare(key=self.key, draft=self.draft)
        self.j.begin_post_uncertain(key=self.key, draft=self.draft)
        api = object.__new__(M15FinamReadOnlyAPI)
        account = {"account_id": "M15-SYNTH", "status": "ACCOUNT_ACTIVE",
                   "positions": []}
        with (patch.object(M15FinamReadOnlyAPI, "readonly_bound", True),
              patch.object(M15FinamReadOnlyAPI, "account_id", "M15-SYNTH"),
              patch.object(M15FinamReadOnlyAPI, "account", return_value=account),
              patch.object(M15FinamReadOnlyAPI, "orders",
                           return_value={"orders": []})):
            result = reconcile_m15_readonly_once(
                journal=self.j, api=api, m15_account_id="M15-SYNTH")
        self.assertEqual(result["events"][0]["state"],
                         "ENTRY_UNCERTAIN_NO_REPOST")
        self.assertEqual(self.j.inspect(self.key)["state"], "UNCERTAIN")
        self.assertEqual(self.j.db.execute(
            "SELECT COUNT(*) FROM broker_fills").fetchone()[0], 0)

    def test_readonly_cycle_active_protective_get_ack_and_restart(self):
        from IntradayLab.m15_robot.execution_cycle import reconcile_m15_readonly_once
        from IntradayLab.m15_robot.finam_readonly import M15FinamReadOnlyAPI
        self.j.prepare(key=self.key, draft=self.draft)
        self.j.begin_post_uncertain(key=self.key, draft=self.draft)
        key = "m15:stop:synthetic:1"
        stop = self.stop(key)
        self.j.prepare(key=key, draft=stop)
        account, before = self.protective_observation(stop, include_new=False)
        self.j.begin_protective_post_uncertain(
            key=key, draft=stop, account=account, orders_response=before)
        account, after = self.protective_observation(stop, include_new=True)
        api = object.__new__(M15FinamReadOnlyAPI)
        with (patch.object(M15FinamReadOnlyAPI, "readonly_bound", True),
              patch.object(M15FinamReadOnlyAPI, "account_id", "M15-SYNTH"),
              patch.object(M15FinamReadOnlyAPI, "account", return_value=account),
              patch.object(M15FinamReadOnlyAPI, "orders", return_value=after)):
            first = reconcile_m15_readonly_once(
                journal=self.j, api=api, m15_account_id="M15-SYNTH")
            self.assertEqual(first["events"][1]["state"],
                             "STOP_BROKER_ACTIVE_100_PERCENT_RECONCILED")
            self.assertEqual(self.j.inspect(key)["state"], "ACK")
            self.j.close()
            self.j = M15OutboundJournal(**self.args)
            second = reconcile_m15_readonly_once(
                journal=self.j, api=api, m15_account_id="M15-SYNTH")
            self.assertEqual(first, second)
        self.assertEqual(self.j.db.execute(
            "SELECT COUNT(*) FROM protective_coverage").fetchone()[0], 1)

    def test_readonly_cycle_foreign_position_fails_closed(self):
        from IntradayLab.m15_robot.execution_cycle import (
            reconcile_m15_readonly_once, M15ReadOnlyCycleError,
        )
        from IntradayLab.m15_robot.finam_readonly import M15FinamReadOnlyAPI
        api = object.__new__(M15FinamReadOnlyAPI)
        account = {"account_id": "M15-SYNTH", "status": "ACCOUNT_ACTIVE",
                   "positions": [{"symbol": "CNYRUBF@RTSX",
                                  "quantity": {"value": "1"}}]}
        with (patch.object(M15FinamReadOnlyAPI, "readonly_bound", True),
              patch.object(M15FinamReadOnlyAPI, "account_id", "M15-SYNTH"),
              patch.object(M15FinamReadOnlyAPI, "account", return_value=account),
              patch.object(M15FinamReadOnlyAPI, "orders",
                           return_value={"orders": []})):
            with self.assertRaisesRegex(M15ReadOnlyCycleError,
                                        "FOREIGN_POSITION_HALTED"):
                reconcile_m15_readonly_once(
                    journal=self.j, api=api, m15_account_id="M15-SYNTH")
        self.assertEqual(self.j.db.execute(
            "SELECT COUNT(*) FROM outbound").fetchone()[0], 0)


    def test_readonly_cycle_adopts_only_proven_finam_fills_once(self):
        from IntradayLab.m15_robot.execution_cycle import reconcile_m15_readonly_once
        from IntradayLab.m15_robot.finam_readonly import M15FinamReadOnlyAPI
        self.j.prepare(key=self.key, draft=self.draft)
        self.j.begin_post_uncertain(key=self.key, draft=self.draft)
        broker = self.broker_get(filled=1)
        source = self.r15_entry_inputs()
        api = object.__new__(M15FinamReadOnlyAPI)
        kwargs = dict(
            journal=self.j, api=api, m15_account_id="M15-SYNTH",
            trade_start=broker["start"], trade_end=broker["end"],
            stop_trade_tag="trade-1",
        )
        with (patch.object(M15FinamReadOnlyAPI, "readonly_bound", True),
              patch.object(M15FinamReadOnlyAPI, "account_id", "M15-SYNTH"),
              patch.object(M15FinamReadOnlyAPI, "account",
                           return_value=broker["account"]),
              patch.object(M15FinamReadOnlyAPI, "orders",
                           return_value=broker["orders_response"]),
              patch.object(M15FinamReadOnlyAPI, "asset_details",
                           return_value=source["asset"]) as asset,
              patch.object(M15FinamReadOnlyAPI, "asset_params",
                           return_value=source["asset_params"]) as params,
              patch.object(M15FinamReadOnlyAPI, "trades",
                           return_value=broker["trades_response"]) as trades):
            first = reconcile_m15_readonly_once(**kwargs)
            self.assertEqual(first["events"][0]["state"],
                             "ENTRY_BROKER_FILL_RECONCILED_STOP_UNPROVEN")
            self.assertEqual(self.j.inspect(self.key)["state"], "ACK")
            self.assertEqual(self.j.db.execute(
                "SELECT COUNT(*) FROM broker_fills").fetchone()[0], 1)
            self.j.close()
            self.j = M15OutboundJournal(**self.args)
            kwargs["journal"] = self.j
            second = reconcile_m15_readonly_once(**kwargs)
            self.assertEqual(first, second)
            self.assertEqual(self.j.db.execute(
                "SELECT COUNT(*) FROM broker_fills").fetchone()[0], 1)
            asset.assert_called()
            params.assert_called()
            self.assertEqual(trades.call_count, 2)

    def test_readonly_cycle_wrong_m15_account_never_queries_broker(self):
        from IntradayLab.m15_robot.execution_cycle import (
            reconcile_m15_readonly_once, M15ReadOnlyCycleError,
        )
        from IntradayLab.m15_robot.finam_readonly import M15FinamReadOnlyAPI
        api = object.__new__(M15FinamReadOnlyAPI)
        with (patch.object(M15FinamReadOnlyAPI, "readonly_bound", True),
              patch.object(M15FinamReadOnlyAPI, "account_id", "M15-OTHER"),
              patch.object(M15FinamReadOnlyAPI, "account") as account,
              patch.object(M15FinamReadOnlyAPI, "orders") as orders):
            with self.assertRaisesRegex(M15ReadOnlyCycleError,
                                        "EXACT_READONLY_ACCOUNT_REQUIRED"):
                reconcile_m15_readonly_once(
                    journal=self.j, api=api, m15_account_id="M15-SYNTH")
            account.assert_not_called()
            orders.assert_not_called()


    def test_readonly_recovery_operator_one_cycle_heartbeat_and_restart(self):
        from IntradayLab.m15_robot.execution_cycle import run_m15_readonly_recovery_once
        from IntradayLab.m15_robot.finam_readonly import M15FinamReadOnlyAPI
        self.j.prepare(key=self.key, draft=self.draft)
        account = {"account_id": "M15-SYNTH", "status": "ACCOUNT_ACTIVE",
                   "positions": []}
        api = object.__new__(M15FinamReadOnlyAPI)
        kw = dict(
            runtime_root=self.args["runtime_root"], journal=self.j,
            api=api, m15_account_id="M15-SYNTH",
            observed_at=datetime(2026,10,20,12,tzinfo=timezone.utc))
        with (patch.object(M15FinamReadOnlyAPI, "readonly_bound", True),
              patch.object(M15FinamReadOnlyAPI, "account_id", "M15-SYNTH"),
              patch.object(M15FinamReadOnlyAPI, "account", return_value=account),
              patch.object(M15FinamReadOnlyAPI, "orders",
                           return_value={"orders": []})):
            result = run_m15_readonly_recovery_once(**kw)
            self.assertEqual(result["status"], "HALTED_READONLY_RECOVERY")
            heartbeat = self.args["runtime_root"] / "diagnostics" / "m15-readonly-execution-recovery.json"
            recorded = json.loads(heartbeat.read_text(encoding="utf-8"))
            self.assertFalse(recorded["order_post_permitted"])
            self.assertFalse(recorded["live_authorized"])
            self.assertEqual(recorded["intent_count"], 1)
            self.j.close()
            self.j = M15OutboundJournal(**self.args)
            kw["journal"] = self.j
            again = run_m15_readonly_recovery_once(**kw)
            self.assertEqual(result, again)

    def test_readonly_recovery_duplicate_instance_refused_without_network(self):
        from IntradayLab.m15_robot.execution_cycle import run_m15_readonly_recovery_once
        from IntradayLab.m15_robot.finam_readonly import M15FinamReadOnlyAPI
        from IntradayLab.m15_robot.service_clock import M15SingleInstance, M15ClockError
        api = object.__new__(M15FinamReadOnlyAPI)
        state = self.args["runtime_root"] / "state"
        with M15SingleInstance(state / "m15-outbound-recovery.lock"):
            with patch.object(M15FinamReadOnlyAPI, "account") as account:
                with self.assertRaisesRegex(M15ClockError, "SECOND_PROCESS"):
                    run_m15_readonly_recovery_once(
                        runtime_root=self.args["runtime_root"], journal=self.j,
                        api=api, m15_account_id="M15-SYNTH",
                        observed_at=datetime(2026,10,20,12,tzinfo=timezone.utc))
                account.assert_not_called()

    def test_readonly_recovery_fault_overwrites_stale_heartbeat(self):
        from IntradayLab.m15_robot.execution_cycle import (
            run_m15_readonly_recovery_once, M15ReadOnlyCycleError,
        )
        from IntradayLab.m15_robot.finam_readonly import M15FinamReadOnlyAPI
        api = object.__new__(M15FinamReadOnlyAPI)
        heartbeat = self.args["runtime_root"] / "diagnostics" / "m15-readonly-execution-recovery.json"
        with (patch.object(M15FinamReadOnlyAPI, "readonly_bound", True),
              patch.object(M15FinamReadOnlyAPI, "account_id", "M15-OTHER")):
            with self.assertRaisesRegex(M15ReadOnlyCycleError,
                                        "EXACT_READONLY_ACCOUNT_REQUIRED"):
                run_m15_readonly_recovery_once(
                    runtime_root=self.args["runtime_root"], journal=self.j,
                    api=api, m15_account_id="M15-SYNTH",
                    observed_at=datetime(2026,10,20,12,tzinfo=timezone.utc))
        recorded = json.loads(heartbeat.read_text(encoding="utf-8"))
        self.assertEqual(recorded["status"], "FAULT_HALTED_NO_TRADING")
        self.assertFalse(recorded["live_authorized"])


    def test_readonly_cycle_proven_stop_flat_releases_once_after_restart(self):
        from IntradayLab.m15_robot.execution_cycle import reconcile_m15_readonly_once
        from IntradayLab.m15_robot.finam_readonly import M15FinamReadOnlyAPI
        owned = self.synthetic_owned_n4()
        flat = dict(owned["account"], positions=[])
        finished = [dict(row) for row in owned["orders_response"]["orders"]]
        finished[-1]["status"] = "ORDER_STATUS_SL_EXECUTED"
        api = object.__new__(M15FinamReadOnlyAPI)
        kw = dict(journal=self.j, api=api, m15_account_id="M15-SYNTH",
                  observed_at=datetime(2026, 10, 20, 12, tzinfo=timezone.utc))
        with (patch.object(M15FinamReadOnlyAPI, "readonly_bound", True),
              patch.object(M15FinamReadOnlyAPI, "account_id", "M15-SYNTH"),
              patch.object(M15FinamReadOnlyAPI, "account", return_value=flat),
              patch.object(M15FinamReadOnlyAPI, "orders",
                           return_value={"orders": finished})):
            first = reconcile_m15_readonly_once(**kw)
            self.assertEqual(first["events"][-1]["state"],
                             "FLAT_DURABLY_RECONCILED")
            self.assertEqual(self.j.db.execute(
                "SELECT COUNT(*) FROM broker_flat").fetchone()[0], 1)
            self.j.close()
            self.j = M15OutboundJournal(**self.args)
            kw["journal"] = self.j
            second = reconcile_m15_readonly_once(**kw)
            self.assertEqual(first, second)
            self.assertEqual(self.j.db.execute(
                "SELECT COUNT(*) FROM broker_flat").fetchone()[0], 1)
            self.assertFalse(second["new_entries_authorized"])

    def test_readonly_cycle_broker_flat_with_active_stop_needs_cleanup(self):
        from IntradayLab.m15_robot.execution_cycle import reconcile_m15_readonly_once
        from IntradayLab.m15_robot.finam_readonly import M15FinamReadOnlyAPI
        owned = self.synthetic_owned_n4()
        flat = dict(owned["account"], positions=[])
        api = object.__new__(M15FinamReadOnlyAPI)
        with (patch.object(M15FinamReadOnlyAPI, "readonly_bound", True),
              patch.object(M15FinamReadOnlyAPI, "account_id", "M15-SYNTH"),
              patch.object(M15FinamReadOnlyAPI, "account", return_value=flat),
              patch.object(M15FinamReadOnlyAPI, "orders",
                           return_value=owned["orders_response"])):
            result = reconcile_m15_readonly_once(
                journal=self.j, api=api, m15_account_id="M15-SYNTH",
                observed_at=datetime(2026, 10, 20, 12, tzinfo=timezone.utc))
        self.assertEqual(result["events"][-1]["state"],
                         "FLAT_ACTIVE_SLTP_CLEANUP_REQUIRED")
        self.assertEqual(self.j.db.execute(
            "SELECT COUNT(*) FROM broker_flat").fetchone()[0], 0)

    def test_readonly_cycle_canceled_stop_without_exit_is_not_flat_proof(self):
        from IntradayLab.m15_robot.execution_cycle import reconcile_m15_readonly_once
        from IntradayLab.m15_robot.finam_readonly import M15FinamReadOnlyAPI
        owned = self.synthetic_owned_n4()
        flat = dict(owned["account"], positions=[])
        terminal = [dict(row) for row in owned["orders_response"]["orders"]]
        terminal[-1]["status"] = "ORDER_STATUS_CANCELLED"
        api = object.__new__(M15FinamReadOnlyAPI)
        with (patch.object(M15FinamReadOnlyAPI, "readonly_bound", True),
              patch.object(M15FinamReadOnlyAPI, "account_id", "M15-SYNTH"),
              patch.object(M15FinamReadOnlyAPI, "account", return_value=flat),
              patch.object(M15FinamReadOnlyAPI, "orders",
                           return_value={"orders": terminal})):
            with self.assertRaisesRegex(M15ExecutionError,
                                        "FLAT_PROTECTIVE_EXECUTION_UNVERIFIED"):
                reconcile_m15_readonly_once(
                    journal=self.j, api=api, m15_account_id="M15-SYNTH",
                    observed_at=datetime(2026, 10, 20, 12, tzinfo=timezone.utc))
        self.assertEqual(self.j.db.execute(
            "SELECT COUNT(*) FROM broker_flat").fetchone()[0], 0)


    def test_readonly_cycle_finam_emergency_exit_flat_reconciled(self):
        from IntradayLab.m15_robot.execution_cycle import reconcile_m15_readonly_once
        from IntradayLab.m15_robot.finam_readonly import M15FinamReadOnlyAPI
        owned = self.synthetic_owned_n4()
        entry_key = owned["key"]
        stop_key = "m15:trade-1:stop:0"
        exit_key = "m15:exit:trade-1:readonly"
        exit_draft = self.j.prepare_emergency_exit_from_broker(
            entry_key=entry_key, stop_key=stop_key, exit_key=exit_key,
            drafts=owned["drafts"], account=owned["account"],
            orders_response=owned["orders_response"])
        self.j.begin_exit_post_uncertain(
            entry_key=entry_key, stop_key=stop_key, exit_key=exit_key,
            draft=exit_draft, account=owned["account"],
            orders_response=owned["orders_response"])
        flat = dict(owned["account"], positions=[])
        terminal = [dict(row) for row in owned["orders_response"]["orders"]]
        terminal[-1]["status"] = "ORDER_STATUS_CANCELLED"
        terminal.append({
            "order_id": "broker-exit-readonly", "status": "ORDER_STATUS_FILLED",
            "order": dict(exit_draft.payload),
        })
        api = object.__new__(M15FinamReadOnlyAPI)
        with (patch.object(M15FinamReadOnlyAPI, "readonly_bound", True),
              patch.object(M15FinamReadOnlyAPI, "account_id", "M15-SYNTH"),
              patch.object(M15FinamReadOnlyAPI, "account", return_value=flat),
              patch.object(M15FinamReadOnlyAPI, "orders",
                           return_value={"orders": terminal})):
            result = reconcile_m15_readonly_once(
                journal=self.j, api=api, m15_account_id="M15-SYNTH",
                observed_at=datetime(2026, 10, 20, 12, tzinfo=timezone.utc))
            self.assertEqual(result["events"][-1]["state"],
                             "FLAT_DURABLY_RECONCILED")
            self.assertEqual(self.j.db.execute(
                "SELECT reason FROM broker_flat").fetchone()[0], "EMERGENCY_EXIT")
            self.assertFalse(result["live_authorized"])

    def test_readonly_cycle_missing_exit_fill_never_claims_flat(self):
        from IntradayLab.m15_robot.execution_cycle import reconcile_m15_readonly_once
        from IntradayLab.m15_robot.finam_readonly import M15FinamReadOnlyAPI
        owned = self.synthetic_owned_n4()
        exit_key = "m15:exit:trade-1:unproven"
        proposal = self.j.prepare_emergency_exit_from_broker(
            entry_key=owned["key"], stop_key="m15:trade-1:stop:0",
            exit_key=exit_key, drafts=owned["drafts"],
            account=owned["account"],
            orders_response=owned["orders_response"])
        self.j.begin_exit_post_uncertain(
            entry_key=owned["key"], stop_key="m15:trade-1:stop:0",
            exit_key=exit_key, draft=proposal,
            account=owned["account"],
            orders_response=owned["orders_response"])
        flat = dict(owned["account"], positions=[])
        terminal = [dict(row) for row in owned["orders_response"]["orders"]]
        terminal[-1]["status"] = "ORDER_STATUS_CANCELLED"
        api = object.__new__(M15FinamReadOnlyAPI)
        with (patch.object(M15FinamReadOnlyAPI, "readonly_bound", True),
              patch.object(M15FinamReadOnlyAPI, "account_id", "M15-SYNTH"),
              patch.object(M15FinamReadOnlyAPI, "account", return_value=flat),
              patch.object(M15FinamReadOnlyAPI, "orders",
                           return_value={"orders": terminal})):
            with self.assertRaisesRegex(M15ExecutionError,
                                        "FLAT_EXIT_FILL_ORDER_UNVERIFIED"):
                reconcile_m15_readonly_once(
                    journal=self.j, api=api, m15_account_id="M15-SYNTH",
                    observed_at=datetime(2026, 10, 20, 12, tzinfo=timezone.utc))
        self.assertEqual(self.j.db.execute(
            "SELECT COUNT(*) FROM broker_flat").fetchone()[0], 0)

    def test_restart_recovers_exact_entry_draft_without_reposting(self):
        self.j.prepare(key=self.key, draft=self.draft)
        self.j.begin_post_uncertain(key=self.key, draft=self.draft)
        self.j.close()
        self.j = M15OutboundJournal(**self.args)
        recovered = self.j.recover_draft(self.key)
        self.assertEqual(recovered, self.draft)
        self.assertEqual(self.j.inspect(self.key)["state"], "UNCERTAIN")
        self.assertFalse(recovered.submitted or recovered.live_authorized)
        self.assertFalse(self.j.prepare(key=self.key, draft=recovered))
        self.assertEqual(self.j.db.execute(
            "SELECT COUNT(*) FROM outbound").fetchone()[0], 1)

    def test_restart_recovers_protective_draft_while_unknown(self):
        key = "m15:stop:synthetic:1"
        protective = self.stop(key)
        self.j.prepare(key=key, draft=protective)
        account, orders = self.protective_observation(
            protective, include_new=False)
        self.j.begin_protective_post_uncertain(
            key=key, draft=protective, account=account,
            orders_response=orders)
        self.j.close()
        self.j = M15OutboundJournal(**self.args)
        recovered = self.j.recover_draft(key)
        self.assertEqual(recovered, protective)
        self.assertEqual(self.j.inspect(key)["state"], "UNCERTAIN")
        self.assertFalse(self.j.prepare(key=key, draft=recovered))

    def test_modified_or_missing_durable_draft_refused_after_restart(self):
        self.j.prepare(key=self.key, draft=self.draft)
        self.j.db.execute(
            "UPDATE outbound_drafts SET payload_json=? WHERE intent_key=?",
            ('{"symbol":"CNYRUBF@RTSX"}', self.key))
        with self.assertRaises(M15ExecutionError):
            self.j.recover_draft(self.key)
        self.j.db.execute(
            "DELETE FROM outbound_drafts WHERE intent_key=?", (self.key,))
        with self.assertRaisesRegex(M15ExecutionError, "DRAFT_MISSING"):
            self.j.recover_draft(self.key)
        with self.assertRaisesRegex(M15ExecutionError, "DRAFT_MISSING"):
            self.j.prepare(key=self.key, draft=self.draft)
        self.assertEqual(self.j.inspect(self.key)["state"], "PREPARED")

    def test_r15_atomic_prepare_also_persists_exact_entry_payload(self):
        args = self.r15_entry_inputs()
        proposal, _ = self.j.prepare_entry_from_broker_r15(**args)
        self.j.close()
        self.j = M15OutboundJournal(**self.args)
        self.assertEqual(self.j.recover_draft(args["key"]), proposal)
        self.assertEqual(self.j.db.execute(
            "SELECT COUNT(*) FROM entry_r15_basis").fetchone()[0], 1)

    def test_verified_next_open_same_m15_account_prepares_atomic_r15(self):
        from IntradayLab.m15_robot.finam_readonly import M15FinamReadOnlyAPI
        import pandas as pd
        from zoneinfo import ZoneInfo
        data = self.r15_entry_inputs()
        now = data["now"]
        seed_close = now - timedelta(minutes=15)
        times = [now - timedelta(minutes=30), seed_close, now]
        seed = pd.DataFrame(
            {"Open": [12.5], "High": [12.6], "Low": [12.4],
             "Close": [12.5], "Volume": [200]},
            index=pd.DatetimeIndex([seed_close]).tz_convert(ZoneInfo("Europe/Moscow")),
        )
        def bar(at, op):
            return {
                "timestamp": at.isoformat(),
                "open": {"value": op}, "high": {"value": "12.600"},
                "low": {"value": "12.400"}, "close": {"value": "12.500"},
                "volume": {"value": "200"},
            }
        raw = {"symbol": "CNYRUBF@RTSX", "bars": [
            bar(times[0], "12.500"), bar(times[1], "12.500"),
            bar(times[2], "12.505"),
        ]}
        session = {"sessions": [{"type": "CORE_TRADING", "interval": {
            "start_time": (now - timedelta(hours=2)).isoformat(),
            "end_time": (now + timedelta(hours=1)).isoformat(),
        }}]}
        signal = {"at": now.astimezone(ZoneInfo("Europe/Moscow")),
                  "Signal": 1, "ATR": 0.1, "Close": 12.5,
                  "H1AvailableAt": (now - timedelta(minutes=15)).astimezone(
                      ZoneInfo("Europe/Moscow")),
                  "PriorHigh": 12.4, "PriorLow": 12.6}
        api = object.__new__(M15FinamReadOnlyAPI)
        with (patch.object(M15FinamReadOnlyAPI, "readonly_bound", True),
              patch.object(M15FinamReadOnlyAPI, "account_id", "M15-SYNTH"),
              patch.object(M15FinamReadOnlyAPI, "account", return_value=data["account"]),
              patch.object(M15FinamReadOnlyAPI, "orders", return_value=data["orders_response"]),
              patch.object(M15FinamReadOnlyAPI, "asset_details", return_value=data["asset"]),
              patch.object(M15FinamReadOnlyAPI, "asset_params", return_value=data["asset_params"]),
              patch.object(M15FinamReadOnlyAPI, "schedule", return_value=session),
              patch.object(M15FinamReadOnlyAPI, "bars_m15", return_value=raw),
              patch.object(M15FinamReadOnlyAPI, "transactions",
                           return_value=data["cashflow_windows"][0].response) as tx,
              patch("IntradayLab.t3_m15_t1_entry_retest_v1.primary.features",
                    return_value=[signal])):
            outcome = self.j.prepare_verified_next_open_r15(
                api=api, m15_account_id="M15-SYNTH", drafts=data["drafts"], instrument="CNYRUBF",
                authenticated_seed=seed,
                interval_start=times[0].isoformat(),
                interval_end=(now + timedelta(minutes=15)).isoformat(),
                observed_at=now, now=now, verified_open_labels=True,
            )
            self.assertIsNotNone(outcome)
            evidence, entry, sized = outcome
            self.assertEqual(evidence.reference_open, Decimal("12.505"))
            self.assertEqual(entry.payload["quantity"]["value"], "3")
            self.assertEqual(sized.final_quantity, 3)
            self.assertEqual(self.j.inspect(entry.payload["client_order_id"]), None)
            values = self.j.db.execute(
                "SELECT reference_entry,stop_price,quantity "
                "FROM entry_r15_basis WHERE intent_key=?",
                (evidence.signal.signal_id,),
            ).fetchone()
            self.assertEqual(values, ("12.505", "12.305", 3))
            self.assertEqual(self.j.inspect(evidence.signal.signal_id)["state"], "PREPARED")
            self.assertFalse(entry.submitted or entry.live_authorized)
            tx.assert_called_once()
        self.assertEqual(self.j.db.execute(
            "SELECT COUNT(*) FROM outbound").fetchone()[0], 1)

    def test_verified_next_open_missing_proof_fails_without_sqlite_intent(self):
        from IntradayLab.m15_robot.finam_readonly import M15FinamReadOnlyAPI
        data = self.r15_entry_inputs()
        api = object.__new__(M15FinamReadOnlyAPI)
        with (patch.object(M15FinamReadOnlyAPI, "readonly_bound", True),
              patch.object(M15FinamReadOnlyAPI, "account_id", "M15-SYNTH")):
            with self.assertRaisesRegex(ValueError, "OPEN_LABEL_PROOF_REQUIRED"):
                self.j.prepare_verified_next_open_r15(
                    api=api, m15_account_id="M15-SYNTH", drafts=data["drafts"], instrument="CNYRUBF",
                    authenticated_seed=None, interval_start="invalid",
                    interval_end="invalid", observed_at=data["now"],
                    now=data["now"], verified_open_labels=False,
                )
        self.assertEqual(self.j.db.execute(
            "SELECT COUNT(*) FROM outbound").fetchone()[0], 0)

if __name__ == "__main__":
    unittest.main()
