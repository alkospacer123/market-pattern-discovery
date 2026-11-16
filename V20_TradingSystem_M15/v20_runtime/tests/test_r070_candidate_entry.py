"""R070 OFFLINE gate: frozen pre-entry draft never creates a trading intent."""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from unittest import TestCase, main

from V20_TradingSystem_M15.v20_runtime.offline_planner import FrozenSignal, ProposedEntry
from V20_TradingSystem_M15.v20_runtime.r070_candidate_entry import (
    evaluate_r070_candidate_ext2, stage_r070_after_frozen_proposal,
)
from V20_TradingSystem_M15.v20_runtime.tests.test_ext2_r060 import history


def fixtures(side=1, contra=False, robot="v20-shallow", symbol="GLDRUBF"):
    full = history(side, contra)
    recent = full.tail(150).reset_index(drop=True)
    label = full.Datetime.iloc[-1].to_pydatetime()
    strategy = {
        "v20-shallow": "SHALLOW_PULLBACK",
        "v20-obv": "OBV_PRESSURE",
        "v20-inside": "INSIDE_DAY_RELEASE",
    }[robot]
    signal = FrozenSignal(strategy, symbol, side, label, Decimal("1"))
    candidate = ProposedEntry(
        strategy, symbol, "LONG" if side == 1 else "SHORT",
        label + timedelta(minutes=15), Decimal("100"),
        Decimal("98") if side == 1 else Decimal("102"),
        Decimal("2"), 1, Decimal("1.5"), Decimal("10"), "STAGING_ONLY")
    draft = (signal, candidate, object(), object())
    return signal, full, recent, draft


class R070EntryCandidateTests(TestCase):
    def test_long_short_ext2_blocks_shallow_and_obv(self):
        for side in (1, -1):
            for robot in ("v20-shallow", "v20-obv"):
                signal, full, recent, _ = fixtures(side=side, robot=robot)
                result = evaluate_r070_candidate_ext2(
                    robot=robot, symbol="GLDRUBF", frozen_signal=signal,
                    finam_completed=recent, verified_full_history=full)
                self.assertFalse(result.permit)
                self.assertEqual(result.reason, "EXT2_LATE_NO_OPPOSING_M15")

    def test_contra_allows_but_recent_ohlcv_mismatch_blocks(self):
        signal, full, recent, _ = fixtures(contra=True)
        decision = evaluate_r070_candidate_ext2(
            robot="v20-shallow", symbol="GLDRUBF", frozen_signal=signal,
            finam_completed=recent, verified_full_history=full)
        self.assertTrue(decision.permit)
        altered = recent.copy()
        altered.loc[altered.index[-2], "Volume"] += 1
        decision = evaluate_r070_candidate_ext2(
            robot="v20-shallow", symbol="GLDRUBF", frozen_signal=signal,
            finam_completed=altered, verified_full_history=full)
        self.assertFalse(decision.permit)
        self.assertEqual(decision.reason, "EXT2_HISTORY_FINAM_OHLCV_MISMATCH")

    def test_missing_history_fails_closed_but_inside_imoex_unchanged(self):
        _, full, recent, _ = fixtures()
        for symbol, robot, expected in [
            ("GLDRUBF", "v20-shallow", False),
            ("GLDRUBF", "v20-inside", True),
            ("IMOEXF", "v20-shallow", True),
        ]:
            signal, _, _, _ = fixtures(robot=robot, symbol=symbol)
            decision = evaluate_r070_candidate_ext2(
                robot=robot, symbol=symbol, frozen_signal=signal,
                finam_completed=recent, verified_full_history=None)
            self.assertEqual(decision.permit, expected)

    def test_staged_veto_before_any_durable_intent(self):
        signal, full, recent, draft = fixtures(robot="v20-obv")
        audited = []
        def record(**kwargs):
            audited.append(kwargs["decision"].reason)
            return True
        result = stage_r070_after_frozen_proposal(
            robot="v20-obv", symbol="GLDRUBF", frozen_draft=draft,
            finam_completed=recent, verified_full_history=full,
            durable_audit=record)
        self.assertIsNone(result)
        self.assertEqual(audited, ["EXT2_LATE_NO_OPPOSING_M15"])

    def test_staged_permit_keeps_exact_original_draft(self):
        _, full, recent, draft = fixtures(contra=True)
        audited = []
        output = stage_r070_after_frozen_proposal(
            robot="v20-shallow", symbol="GLDRUBF", frozen_draft=draft,
            finam_completed=recent, verified_full_history=full,
            durable_audit=lambda **kwargs: (audited.append(kwargs["decision"].reason) or True))
        self.assertIs(output, draft)
        self.assertEqual(audited, ["EXT2_PASS"])

    def test_missing_history_and_failed_audit_cannot_authorize(self):
        _, full, recent, draft = fixtures(contra=True)
        audited = []
        with self.assertRaisesRegex(ValueError, "R070_EXT2_DURABLE_AUDIT_REQUIRED"):
            stage_r070_after_frozen_proposal(
                robot="v20-shallow", symbol="GLDRUBF", frozen_draft=draft,
                finam_completed=recent, verified_full_history=full,
                durable_audit=None)
        with self.assertRaisesRegex(ValueError, "R070_EXT2_AUDIT_NOT_PROVEN"):
            stage_r070_after_frozen_proposal(
                robot="v20-shallow", symbol="GLDRUBF", frozen_draft=draft,
                finam_completed=recent, verified_full_history=full,
                durable_audit=lambda **kwargs: False)
        self.assertIsNone(stage_r070_after_frozen_proposal(
            robot="v20-shallow", symbol="GLDRUBF", frozen_draft=draft,
            finam_completed=recent, verified_full_history=None,
            durable_audit=lambda **kwargs: (audited.append(kwargs["decision"].reason) or True)))
        self.assertEqual(audited, ["EXT2_CERTIFIED_HISTORY_MISSING"])

    def test_no_signal_preserves_frozen_null_and_no_audit(self):
        self.assertIsNone(stage_r070_after_frozen_proposal(
            robot="v20-shallow", symbol="GLDRUBF", frozen_draft=None,
            finam_completed=None, verified_full_history=None,
            durable_audit=None))


if __name__ == "__main__":
    main()
