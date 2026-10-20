"""H1-style durable M15 outbound flow: NO-LIVE stage, only synthetic data."""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from dataclasses import replace
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
import tempfile
import unittest

from IntradayLab.m15_robot.live_execution import (
    M15AuthorizedExecutionTransport, M15ExecutionError, M15OutboundJournal,
    M15PrePostRefused, load_execution_authorization,
)
from IntradayLab.m15_robot.broker_fill_readonly import ExpectedEntry
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
