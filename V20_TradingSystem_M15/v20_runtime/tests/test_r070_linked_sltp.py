"""R070 linked SL+TP6 pure contract: one active 100%-percent broker order."""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
from fractions import Fraction
from decimal import Decimal
import unittest

from TradingSystemLab.stage8_robot.production_broker_state import BrokerOrderView
from TradingSystemLab.stage8_robot.production_runtime import RuntimeAction
from TradingSystemLab.stage8_robot.broker import compact_client_order_id
from V20_TradingSystem_M15.v20_runtime.tp6_protect3 import (
    TP6Protect3Unsafe, levels_from_finam_fills,
)
from V20_TradingSystem_M15.v20_runtime.r070_linked_sltp import (
    plan_r070_protect3_cancel_first, verify_r070_protect3_cancelled_before_post,
    verify_r070_protect3_new_sltp,
    prepare_r070_linked_sltp_draft, verify_r070_linked_sltp,
    prepare_r070_tp6_from_h1_full_fills,
    choose_r070_initial_protection,
)


class R070LinkedSltpTests(unittest.TestCase):
    def fixture(self, direction="LONG"):
        stop = "98" if direction == "LONG" else "102"
        levels = levels_from_finam_fills(
            direction=direction, fills=[(1, "100"), (1, "100")],
            initial_stop=stop, tick="0.1")
        action = RuntimeAction(
            "PROTECTIVE_STOP_INSTALL", "v20:shallow:acct:entry:stop",
            "USDRUBF", "USDRUBF@FUT", direction, 2,
            "entry", None, Decimal("100"), Decimal(stop),
            2 if direction == "LONG" else -2,
        )
        wire = prepare_r070_linked_sltp_draft(action=action, levels=levels)
        order = BrokerOrderView(
            "order-123", "WATCHING", True, "SLTP",
            wire["symbol"], wire["client_order_id"], wire["comment"],
            wire["side"], wire.copy(),
        )
        return levels, action, wire, order

    def test_protect3_current_finam_quote_only_bid_ask_and_stale_fail_closed(self):
        from datetime import datetime, timezone
        from V20_TradingSystem_M15.v20_runtime.r070_linked_sltp import (
            prove_r070_protect3_fresh_quote,
        )
        now = datetime(2026, 11, 17, 7, 30, 4, tzinfo=timezone.utc)
        quote = {"symbol": "USDRUBF@FUT", "quote": {
            "symbol": "USDRUBF@FUT", "timestamp": "2026-11-17T07:30:02Z",
            "bid": {"value": "106.0"}, "ask": {"value": "106.1"},
        }}
        args = dict(
            response=quote, symbol="USDRUBF@FUT",
            direction="LONG", observed_utc=now, tick="0.1",
        )
        self.assertEqual(prove_r070_protect3_fresh_quote(**args),
                         Decimal("106.0"))
        self.assertEqual(prove_r070_protect3_fresh_quote(
            **{**args, "direction": "SHORT"}), Decimal("106.1"))
        for mutated in (
            {**quote, "symbol": "CNYRUBF@FUT"},
            {**quote, "quote": {**quote["quote"],
                 "timestamp": "2026-11-17T07:29:50Z"}},
            {**quote, "quote": {**quote["quote"],
                 "timestamp": "2026-11-17T07:30:09Z"}},
            {**quote, "quote": {**quote["quote"],
                 "ask": {"value": "105.9"}}},
            {**quote, "quote": {**quote["quote"],
                 "bid": {"value": "106.05"}}},
            {**quote, "quote": {**quote["quote"],
                 "bid": None}},
        ):
            with self.subTest(mutated=mutated), self.assertRaises(TP6Protect3Unsafe):
                prove_r070_protect3_fresh_quote(
                    **{**args, "response": mutated})
        with self.assertRaises(TP6Protect3Unsafe):
            prove_r070_protect3_fresh_quote(
                **{**args, "observed_utc": now.replace(tzinfo=None)})

    def test_protect3_finamboundary_closed_m15_trigger_no_forming_bar(self):
        from datetime import datetime, timezone
        from decimal import Decimal
        import pandas as pd
        from V20_TradingSystem_M15.v20_runtime.finam_execution import V20M15Boundary
        from V20_TradingSystem_M15.v20_runtime.r070_linked_sltp import (
            review_r070_protect3_m15_boundary,
        )
        for direction in ("LONG", "SHORT"):
            with self.subTest(direction=direction):
                levels, _, _, _ = self.fixture(direction)
                open_msk = datetime(2026, 11, 17, 10, 15)
                at = datetime(2026, 11, 17, 10, 30)
                high, low = ((Decimal("106.5"), Decimal("103"))
                             if direction == "LONG" else
                             (Decimal("97"), Decimal("93.5")))
                completed = pd.DataFrame([{
                    "Datetime": open_msk, "Open": Decimal("104"),
                    "High": high, "Low": low, "Close": Decimal("105"),
                    "Volume": 25,
                }])
                boundary = V20M15Boundary(
                    "USDRUBF", at, completed, Decimal("105"),
                    datetime(2026, 11, 17, 7, 30, tzinfo=timezone.utc))
                k = dict(
                    levels=levels, boundary=boundary,
                    entry_open_msk=open_msk, broker_stop_proved=True,
                    currently_proved_stop=levels.initial_stop,
                )
                review = review_r070_protect3_m15_boundary(**k)
                self.assertEqual(
                    review.status,
                    "LOCK_1R_DUE_NEXT_M15_BROKER_REPLACE_BLOCKED")
                self.assertEqual(review.proposed_stop, levels.locked_stop_1r)
                self.assertEqual(review.eligible_m15_open_msk, at)
                self.assertEqual(
                    review_r070_protect3_m15_boundary(
                        **{**k, "broker_stop_proved": False}).status,
                    "BROKER_STOP_UNVERIFIED_NO_CHANGE")
                self.assertEqual(
                    review_r070_protect3_m15_boundary(
                        **{**k, "entry_open_msk": at}).status,
                    "BEFORE_ENTRY_NO_CHANGE")
                # Last observed row is a forming candle, not closed: fail.
                forming = completed.copy()
                forming.loc[0, "Datetime"] = at
                with self.assertRaisesRegex(
                        TP6Protect3Unsafe, "COMPLETED_M15_NOT_ADJACENT"):
                    review_r070_protect3_m15_boundary(
                        **{**k, "boundary": V20M15Boundary(
                            "USDRUBF", at, forming, Decimal("105"),
                            boundary.observed_at_utc)})
                # Could have exited via old SL or TP: broker reconcile first.
                exited = completed.copy()
                exited.loc[0, "High" if direction == "LONG" else "Low"] = (
                    Decimal("113") if direction == "LONG" else Decimal("87"))
                status = review_r070_protect3_m15_boundary(
                    **{**k, "boundary": V20M15Boundary(
                        "USDRUBF", at, exited, Decimal("105"),
                        boundary.observed_at_utc)}).status
                self.assertEqual(status, "M15_COULD_HAVE_EXITED_RECONCILE_BROKER")

    def test_protect3_cancel_first_candidate_long_and_short_no_post(self):
        from datetime import datetime
        from V20_TradingSystem_M15.v20_runtime.tp6_protect3 import ProtectionReview
        for side in ("LONG", "SHORT"):
            with self.subTest(side=side):
                levels, _, wire, old = self.fixture(side)
                qty = 2 if side == "LONG" else -2
                review = ProtectionReview(
                    "LOCK_1R_DUE_NEXT_M15_BROKER_REPLACE_BLOCKED",
                    datetime(2026, 11, 17, 10, 15), levels.locked_stop_1r)
                plan = plan_r070_protect3_cancel_first(
                    levels=levels, review=review, observed_position=qty,
                    orders=(old,), old_wire=wire, old_order_id=old.order_id,
                    m15_boundary_msk=datetime(2026, 11, 17, 10, 15),
                    broker_last_price="106" if side == "LONG" else "94")
                self.assertEqual(wire["sl_price"]["value"], str(levels.initial_stop))
                self.assertEqual(plan.new_wire["sl_price"]["value"], str(levels.locked_stop_1r))
                self.assertEqual(plan.new_wire["tp_price"], wire["tp_price"])
                self.assertEqual(plan.new_wire["quantity_sl"], {"value": "100"})
                self.assertEqual(plan.new_wire["quantity_tp"], {"value": "100"})
                self.assertNotEqual(plan.new_wire["client_order_id"], wire["client_order_id"])
                with self.assertRaisesRegex(
                        TP6Protect3Unsafe, "CANCEL_NOT_BROKER_PROVEN"):
                    verify_r070_protect3_cancelled_before_post(
                        plan=plan, observed_position=qty, orders=(old,))
                gone = replace(old, active=False, status="CANCELLED")
                verify_r070_protect3_cancelled_before_post(
                    plan=plan, observed_position=qty, orders=(gone,))
                new = BrokerOrderView(
                    "new-order-456", "WATCHING", True, "SLTP", plan.symbol,
                    plan.new_wire["client_order_id"], plan.new_wire["comment"],
                    plan.new_wire["side"], plan.new_wire.copy())
                self.assertEqual(verify_r070_protect3_new_sltp(
                    plan=plan, observed_position=qty,
                    orders=(gone, new), new_order_id="new-order-456"), new)
                for bad_orders in (
                    (old, new),
                    (gone,),
                    (gone, replace(new, request={**new.request, "tp_price": {"value": "200"}})),
                ):
                    with self.assertRaises(TP6Protect3Unsafe):
                        verify_r070_protect3_new_sltp(
                            plan=plan, observed_position=qty,
                            orders=bad_orders, new_order_id="new-order-456")

    def test_protect3_preflight_rejects_stale_price_or_ambiguous_stop(self):
        from datetime import datetime
        from V20_TradingSystem_M15.v20_runtime.tp6_protect3 import ProtectionReview
        levels, _, wire, old = self.fixture()
        review = ProtectionReview(
            "LOCK_1R_DUE_NEXT_M15_BROKER_REPLACE_BLOCKED",
            datetime(2026, 11, 17, 10, 15), levels.locked_stop_1r)
        base = dict(
            levels=levels, review=review, observed_position=2,
            orders=(old,), old_wire=wire, old_order_id=old.order_id,
            m15_boundary_msk=datetime(2026, 11, 17, 10, 15),
            broker_last_price="106")
        for change in (
            {"broker_last_price": "102"},
            {"observed_position": 1},
            {"old_order_id": "unknown"},
            {"orders": (old, replace(old, order_id="duplicate"))},
            {"m15_boundary_msk": datetime(2026, 11, 17, 10, 30)},
        ):
            with self.subTest(change=change), self.assertRaises(TP6Protect3Unsafe):
                plan_r070_protect3_cancel_first(**{**base, **change})

    def test_protect3_one_shot_candidate_durable_and_restart_mock_only(self):
        from contextlib import nullcontext
        from datetime import datetime, timezone
        from types import SimpleNamespace
        from unittest.mock import Mock
        from V20_TradingSystem_M15.v20_runtime.finam_execution import (
            V20TradeJournal, V20FinamReadAdapter)
        from V20_TradingSystem_M15.v20_runtime.tp6_protect3 import ProtectionReview
        from V20_TradingSystem_M15.v20_runtime.r070_linked_sltp import (
            stage_r070_protect3_cancel_first_once,
            examine_r070_protect3_after_restart)
        levels, _, wire, old = self.fixture()
        mark = datetime(2026, 11, 17, 10, 15)
        plan = plan_r070_protect3_cancel_first(
            levels=levels,
            review=ProtectionReview(
                "LOCK_1R_DUE_NEXT_M15_BROKER_REPLACE_BLOCKED", mark,
                levels.locked_stop_1r),
            observed_position=2, orders=(old,), old_wire=wire,
            old_order_id="order-123", m15_boundary_msk=mark,
            broker_last_price="106")
        new_order = BrokerOrderView(
            "new-order-456", "WATCHING", True, "SLTP",
            wire["symbol"], plan.new_wire["client_order_id"],
            plan.new_wire["comment"], plan.new_wire["side"], plan.new_wire.copy())
        before = SimpleNamespace(positions={wire["symbol"]: 2}, orders=(old,))
        cancelled = SimpleNamespace(
            positions={wire["symbol"]: 2},
            orders=(replace(old, active=False, status="CANCELLED"),))
        after = SimpleNamespace(
            positions={wire["symbol"]: 2}, orders=(*cancelled.orders, new_order))
        k = "v20:shallow:acct:entry"
        now = datetime(2026, 11, 17, 7, 15, tzinfo=timezone.utc)

        def environment(snapshots):
            rows = {}
            store = Mock()
            store.get.side_effect = lambda key: rows.get(key)
            store.put.side_effect = lambda key, val: rows.__setitem__(key, val)
            store.transaction.side_effect = lambda: nullcontext()
            store.intent.side_effect = lambda key: ({
                k: {"status": "RECONCILED",
                    "payload": {"finam_symbol": wire["symbol"]}},
                k + ":stop": {"status": "RECONCILED",
                              "broker_order_id": "order-123"},
            }).get(key)
            rows["protected_fill:" + k] = {
                "broker_stop_id": "order-123", "account_sha256": "a"*64,
                "broker_stop_percent": "100"}
            journal = Mock(spec=V20TradeJournal)
            journal.store = store
            journal.robot_id = "v20-shallow"
            journal.account_hash = "a"*64
            reader = Mock(spec=V20FinamReadAdapter)
            reader.robot_id = "v20-shallow"
            reader.account_hash = "a"*64
            reader.account_id = "offline-test-account"
            reader.api = object()
            reader.snapshot.side_effect = snapshots
            api = Mock()
            api.place_sltp_order.return_value = {"order_id": "new-order-456"}
            return rows, journal, reader, api

        rows, journal, reader, api = environment((before, cancelled, after, after))
        self.assertEqual(stage_r070_protect3_cancel_first_once(
            journal=journal, reader=reader, entry_key=k, plan=plan,
            broker_api=api, observed_at=now), "new-order-456")
        self.assertEqual(api.cancel_order.call_count, 1)
        self.assertEqual(api.place_sltp_order.call_count, 1)
        self.assertEqual(rows["r070_protect3:" + k]["state"], "PROTECTED")
        self.assertEqual(rows["r070_protect3:" + k]["new_broker_id"], "new-order-456")
        self.assertEqual(examine_r070_protect3_after_restart(
            journal=journal, reader=reader, entry_key=k, observed_at=now),
            "CANDIDATE_PROTECTED_BROKER_SNAPSHOT_ONLY")

        # Missing cancel proof must NEVER permit a replacement POST.
        rows, journal, reader, api = environment((before, before))
        with self.assertRaisesRegex(TP6Protect3Unsafe,
                                    "R070_PROTECT3_CANCEL_NOT_BROKER_PROVEN"):
            stage_r070_protect3_cancel_first_once(
                journal=journal, reader=reader, entry_key=k, plan=plan,
                broker_api=api, observed_at=now)
        self.assertEqual(api.cancel_order.call_count, 1)
        self.assertEqual(api.place_sltp_order.call_count, 0)
        self.assertEqual(rows["execution_halt"], "PROTECT3_UNPROTECTED_OR_UNKNOWN")
        self.assertEqual(rows["r070_protect3:" + k]["state"],
                         "CANCEL_ACK_UNVERIFIED")

        # A POST timeout is UNKNOWN, not authority to create another SLTP.
        rows, journal, reader, api = environment((before, cancelled))
        api.place_sltp_order.side_effect = TimeoutError("offline timeout")
        with self.assertRaises(TimeoutError):
            stage_r070_protect3_cancel_first_once(
                journal=journal, reader=reader, entry_key=k, plan=plan,
                broker_api=api, observed_at=now)
        self.assertEqual(api.place_sltp_order.call_count, 1)
        self.assertEqual(rows["execution_halt"], "PROTECT3_UNPROTECTED_OR_UNKNOWN")
        self.assertEqual(rows["r070_protect3:" + k]["state"],
                         "NEW_POST_OUTCOME_UNKNOWN")
        with self.assertRaisesRegex(TP6Protect3Unsafe,
                                    "R070_PROTECT3_ALREADY_ATTEMPTED_NO_REPLAY"):
            stage_r070_protect3_cancel_first_once(
                journal=journal, reader=reader, entry_key=k, plan=plan,
                broker_api=api, observed_at=now)
        self.assertEqual(api.place_sltp_order.call_count, 1)

    def test_single_linked_sltp_has_two_100pct_parts_and_6r(self):
        for direction in ("LONG", "SHORT"):
            levels, action, wire, order = self.fixture(direction)
            self.assertEqual(wire["quantity_sl"], {"value": "100"})
            self.assertEqual(wire["quantity_tp"], {"value": "100"})
            self.assertEqual(wire["tp_qty_measure"], "SLTP_QTY_MEASURE_PERCENT")
            self.assertEqual(wire["sl_qty_measure"], "SLTP_QTY_MEASURE_PERCENT")
            self.assertEqual(wire["tp_price"]["value"], str(levels.take_profit))
            self.assertEqual(wire["sl_price"]["value"], str(levels.initial_stop))
            self.assertEqual(verify_r070_linked_sltp(
                observed_position=2 if direction == "LONG" else -2,
                orders=(order,), levels=levels, wire=wire,
                expected_broker_order_id="order-123"), order)

    def test_watch_stop_without_client_id_recovers_only_with_proved_broker_id(self):
        levels, _, wire, order = self.fixture()
        watch = replace(order, client_order_id="")
        self.assertEqual(verify_r070_linked_sltp(
            observed_position=2, orders=(watch,), levels=levels,
            wire=wire, expected_broker_order_id="order-123"), watch)
        with self.assertRaises(TP6Protect3Unsafe):
            verify_r070_linked_sltp(
                observed_position=2, orders=(watch,), levels=levels,
                wire=wire, expected_broker_order_id="different")

    def test_duplicate_or_missing_order_never_counts_as_protection(self):
        levels, _, wire, order = self.fixture()
        for orders in (tuple(), (replace(order, active=False),),
                       (order, replace(order, order_id="another", comment="different"))):
            with self.assertRaises(TP6Protect3Unsafe):
                verify_r070_linked_sltp(
                    observed_position=2, orders=orders, levels=levels,
                    wire=wire, expected_broker_order_id="order-123")


    def test_active_regular_child_blocks_linked_stop_proof(self):
        levels, _, wire, order = self.fixture()
        child = BrokerOrderView(
            "trigger-child", "NEW", True, "REGULAR",
            wire["symbol"], "child-id", "triggered",
            wire["side"], {"quantity": {"value": "2"}})
        with self.assertRaisesRegex(
                TP6Protect3Unsafe,
                "R070_SLTP_ACTIVE_CHILD_OR_OTHER_ORDER_UNVERIFIED"):
            verify_r070_linked_sltp(
                observed_position=2, orders=(order, child),
                levels=levels, wire=wire, expected_broker_order_id="order-123")

    def test_tp_missing_or_wrong_price_or_fraction_rejected(self):
        levels, _, wire, order = self.fixture()
        for change in (
            {"tp_price": {"value": "110"}},
            {"tp_price": None},
            {"quantity_tp": {"value": "50"}},
            {"tp_qty_measure": "SLTP_QTY_MEASURE_UNITS"},
            {"sl_price": {"value": "97"}},
        ):
            request = {**order.request, **change}
            with self.assertRaises(TP6Protect3Unsafe):
                verify_r070_linked_sltp(
                    observed_position=2, orders=(replace(order, request=request),),
                    levels=levels, wire=wire, expected_broker_order_id="order-123")


    def h1_full_fill_fixture(self, direction="LONG"):
        levels, action, wire, _ = self.fixture(direction)
        facts = [
            {"trade_id_sha256": sha256(f"trade-{i}".encode()).hexdigest(),
             "quantity": 1, "price": "100",
             "utc_seconds": 10000 + i, "nanoseconds": 0,
             "account_trade_currency": "RUB"}
            for i in (1, 2)
        ]
        facts.sort(key=lambda x: x["trade_id_sha256"])
        digest = sha256(json.dumps(facts, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        history = {
            "authority_scope": "READONLY_DIAGNOSTIC_ONLY_NO_RUNTIME_HANDOFF",
            "quantity_observation": "FULL_REQUEST_MATCHED",
            "matched_quantity": 2,
            "matched_unique_fills": facts,
            "fill_set_sha256": digest,
            "weighted_price_exact": {"numerator": "100", "denominator": "1"},
        }
        entry = BrokerOrderView(
            "entry-123", "FILLED", False, "REGULAR",
            action.finam_symbol, compact_client_order_id(action.trade_id),
            None, "SIDE_BUY" if direction == "LONG" else "SIDE_SELL",
            {"quantity": {"value": "2"}},
        )
        args = {
            "action": action, "history": history,
            "entry_orders": (entry,), "entry_broker_order_id": entry.order_id,
            "observed_position": 2 if direction == "LONG" else -2,
            "tick": Decimal("0.1"),
        }
        return levels, wire, args

    def test_h1_real_fill_shape_to_tp6_linked_draft_both_sides(self):
        for side in ("LONG", "SHORT"):
            levels, wire, args = self.h1_full_fill_fixture(side)
            new_levels, new_wire = prepare_r070_tp6_from_h1_full_fills(**args)
            self.assertEqual(new_levels, levels)
            self.assertEqual(new_wire, wire)

    def test_partial_fill_or_different_position_never_prepares_tp(self):
        levels, wire, args = self.h1_full_fill_fixture()
        for change in (
            {"history": {**args["history"], "matched_quantity": 1,
                         "quantity_observation": "PARTIAL_REQUEST_MATCHED"}},
            {"observed_position": 1},
        ):
            with self.assertRaises(TP6Protect3Unsafe):
                prepare_r070_tp6_from_h1_full_fills(**{**args, **change})

    def test_changed_trade_set_or_vwap_and_order_id_fails(self):
        levels, wire, args = self.h1_full_fill_fixture()
        mutated = {**args["history"]}
        mutated["matched_unique_fills"] = [
            *mutated["matched_unique_fills"][:-1],
            {**mutated["matched_unique_fills"][-1], "price": "101"}]
        for change in (
            {"history": mutated},
            {"entry_broker_order_id": "another-entry"},
            {"entry_orders": (replace(args["entry_orders"][0], active=True),)},
            {"history": {**args["history"],
                         "weighted_price_exact": {"numerator": "101", "denominator": "1"}}},
            {"history": {**args["history"], "fill_set_sha256": "0"*64}},
        ):
            with self.assertRaises(TP6Protect3Unsafe):
                prepare_r070_tp6_from_h1_full_fills(**{**args, **change})

    def test_preexisting_active_sltp_blocks_second_sltp_draft(self):
        _, _, args = self.h1_full_fill_fixture()
        other = BrokerOrderView(
            "old-stop", "WATCHING", True, "SLTP",
            args["action"].finam_symbol, "", "old", "SIDE_SELL",
            {"sl_price": {"value": "98"}})
        with self.assertRaisesRegex(
                TP6Protect3Unsafe,
                "R070_ENTRY_BROKER_IDENTITY_OR_ACTIVE_ORDER_INVALID"):
            prepare_r070_tp6_from_h1_full_fills(
                **{**args, "entry_orders": (*args["entry_orders"], other)})


    def candidate_choice_fixture(self, *, partial=False, protected=False):
        _, wire, args = self.h1_full_fill_fixture()
        if partial:
            original = args["history"]["matched_unique_fills"][0]
            facts = [original]
            digest = sha256(json.dumps(facts, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            hist = {
                **args["history"], "matched_unique_fills": facts,
                "matched_quantity": 1,
                "quantity_observation": "PARTIAL_REQUEST_MATCHED",
                "fill_set_sha256": digest,
            }
            order = replace(args["entry_orders"][0], status="PARTIALLY_FILLED", active=True)
            action = replace(args["action"], quantity=1, expected_position_quantity=1)
            args = {**args, "action": action, "history": hist,
                    "observed_position": 1, "entry_orders": (order,)}
        if protected:
            _, _, old_wire, stop = self.fixture()
            args = {**args, "entry_orders": (*args["entry_orders"], stop),
                    "existing_broker_stop_id": stop.order_id,
                    "existing_proved_stop_price": Decimal(old_wire["sl_price"]["value"])}
        return args

    def test_full_fill_before_stop_prepares_exactly_one_linked_sl_tp6(self):
        args = self.candidate_choice_fixture()
        choice = choose_r070_initial_protection(**args)
        self.assertEqual(choice.status, "SINGLE_LINKED_SL_TP6_DRAFT_ONLY")
        self.assertIsNotNone(choice.levels)
        self.assertEqual(choice.wire["quantity_sl"], {"value": "100"})
        self.assertEqual(choice.wire["quantity_tp"], {"value": "100"})
        self.assertEqual(choice.wire["tp_price"]["value"], str(choice.levels.take_profit))

    def test_partial_fill_never_waits_for_tp_and_requests_original_stop(self):
        args = self.candidate_choice_fixture(partial=True)
        choice = choose_r070_initial_protection(**args)
        self.assertEqual(choice.status, "ORIGINAL_V20_SL_REQUIRED_PARTIAL_FILL")
        self.assertIsNone(choice.wire)
        self.assertIsNone(choice.levels)

    def test_partial_growth_or_full_after_old_stop_keeps_verified_stop(self):
        for partial in (True, False):
            args = self.candidate_choice_fixture(partial=partial, protected=True)
            choice = choose_r070_initial_protection(**args)
            self.assertEqual(choice.status,
                             "KEEP_VERIFIED_ORIGINAL_STOP_NO_TP6_REPLACEMENT")
            self.assertIsNone(choice.wire)
            self.assertIsNone(choice.levels)

    def test_unverified_active_stop_must_not_make_second_sltp(self):
        args = self.candidate_choice_fixture(protected=True)
        with self.assertRaisesRegex(
                TP6Protect3Unsafe, "R070_UNKNOWN_ACTIVE_STOP_NO_SECOND_SLTP"):
            choose_r070_initial_protection(**{
                **args, "existing_broker_stop_id": None,
                "existing_proved_stop_price": None})
        with self.assertRaisesRegex(
                TP6Protect3Unsafe, "R070_EXISTING_STOP_ID_UNVERIFIED"):
            choose_r070_initial_protection(**{
                **args, "existing_broker_stop_id": "different-stop"})
        with self.assertRaisesRegex(
                TP6Protect3Unsafe, "R070_EXISTING_STOP_PRICE_OR_SIDE_UNVERIFIED"):
            choose_r070_initial_protection(**{
                **args, "existing_proved_stop_price": Decimal("97")})
        extra = BrokerOrderView("second-stop", "WATCHING", True, "SLTP",
                                args["action"].finam_symbol, "", "new",
                                "SIDE_SELL", args["entry_orders"][1].request)
        with self.assertRaises(TP6Protect3Unsafe):
            choose_r070_initial_protection(**{
                **args, "entry_orders": (*args["entry_orders"], extra)})

    def test_no_partial_stop_decision_when_fill_set_or_quantity_uncertain(self):
        args = self.candidate_choice_fixture(partial=True)
        cases = [
            {"history": {**args["history"], "matched_quantity": 0}},
            {"history": {**args["history"], "fill_set_sha256": "0"*64}},
            {"history": {**args["history"], "weighted_price_exact":
                         {"numerator": "101", "denominator": "1"}}},
            {"observed_position": 2},
        ]
        for change in cases:
            with self.subTest(change=change), self.assertRaises(TP6Protect3Unsafe):
                choose_r070_initial_protection(**{**args, **change})

    def test_partial_fill_quantity_or_action_drift_is_rejected(self):
        levels, action, wire, order = self.fixture()
        with self.assertRaisesRegex(TP6Protect3Unsafe, "R070_SLTP_FILL_OR_STOP_SCOPE_INVALID"):
            prepare_r070_linked_sltp_draft(
                action=replace(action, quantity=1, expected_position_quantity=1),
                levels=levels)
        with self.assertRaisesRegex(TP6Protect3Unsafe, "R070_SLTP_BROKER_STATE_UNVERIFIED"):
            verify_r070_linked_sltp(
                observed_position=1, orders=(order,), levels=levels,
                wire=wire, expected_broker_order_id="order-123")


if __name__ == "__main__":
    unittest.main()
