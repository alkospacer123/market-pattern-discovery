"""R070 candidate entry OFFLINE tests: exact EXT2 before account/risk/order access."""
from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest import TestCase, main
from unittest.mock import patch
from zoneinfo import ZoneInfo

from V20_TradingSystem_M15.v20_runtime.offline_planner import FrozenSignal
from V20_TradingSystem_M15.v20_runtime.finam_execution import (
    V20FinamReadAdapter, V20FinamBlocked, propose_finam_m15_next_open,
)
from V20_TradingSystem_M15.v20_runtime.r070_candidate_entry import (
    evaluate_r070_candidate_ext2,
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
    return signal, full, recent


class R070EntryCandidateTests(TestCase):
    def test_long_short_block_only_scoped_shallow_obv(self):
        for side in (1, -1):
            for robot in ("v20-shallow", "v20-obv"):
                signal, full, recent = fixtures(side=side, robot=robot)
                result = evaluate_r070_candidate_ext2(
                    robot=robot, symbol="GLDRUBF", frozen_signal=signal,
                    finam_completed=recent, verified_full_history=full)
                self.assertFalse(result.permit)
                self.assertEqual(result.reason, "EXT2_LATE_NO_OPPOSING_M15")

    def test_contra_candle_allows_and_mismatch_failclosed(self):
        signal, full, recent = fixtures(side=1, contra=True)
        result = evaluate_r070_candidate_ext2(
            robot="v20-shallow", symbol="GLDRUBF", frozen_signal=signal,
            finam_completed=recent, verified_full_history=full)
        self.assertTrue(result.permit)
        changed = recent.copy()
        changed.loc[changed.index[-2], "Volume"] += 1
        mismatch = evaluate_r070_candidate_ext2(
            robot="v20-shallow", symbol="GLDRUBF", frozen_signal=signal,
            finam_completed=changed, verified_full_history=full)
        self.assertEqual(mismatch.reason, "EXT2_HISTORY_FINAM_OHLCV_MISMATCH")
        self.assertFalse(mismatch.permit)

    def test_missing_history_blocks_only_ext2_symbols(self):
        signal, full, recent = fixtures()
        for symbol, robot, expected in [
            ("GLDRUBF", "v20-shallow", False),
            ("GLDRUBF", "v20-inside", True),
            ("IMOEXF", "v20-shallow", True),
        ]:
            sg, _, _ = fixtures(robot=robot, symbol=symbol)
            decision = evaluate_r070_candidate_ext2(
                robot=robot, symbol=symbol, frozen_signal=sg,
                finam_completed=recent, verified_full_history=None)
            self.assertEqual(decision.permit, expected)

    def _mock_frozen_proposal(self, side=1, robot="v20-obv"):
        signal, full, recent = fixtures(side=side, robot=robot)
        next_open = signal.signal_bar_open + timedelta(minutes=15)
        next_utc = next_open.replace(tzinfo=ZoneInfo("Europe/Moscow")).astimezone(ZoneInfo("UTC"))
        boundary = SimpleNamespace(
            at_msk=next_open, completed=recent, witnessed_open=Decimal("100"))
        reader = V20FinamReadAdapter.__new__(V20FinamReadAdapter)
        reader.robot_id = robot
        return signal, full, reader, boundary, next_utc

    def test_staging_gate_blocks_before_snapshot_risk_and_order(self):
        signal, full, reader, boundary, now = self._mock_frozen_proposal()
        decisions = []
        def audit(**kwargs):
            decisions.append(kwargs["decision"].reason)
            return True
        with patch("V20_TradingSystem_M15.v20_runtime.finam_execution.read_finam_m15_boundary",
                   return_value=boundary), patch(
                   "V20_TradingSystem_M15.v20_runtime.finam_execution.completed_signal",
                   return_value=signal), patch.object(
                   reader, "snapshot", side_effect=AssertionError("BROKER_SNAPSHOT_UNEXPECTED")):
            result = propose_finam_m15_next_open(
                reader, symbol="GLDRUBF", from_utc=now-timedelta(days=2),
                now=now, cost_per_contract=Decimal("0"),
                r070_ext2_candidate=True, r070_ext2_verified_history=full,
                r070_ext2_audit=audit)
        self.assertIsNone(result)
        self.assertEqual(decisions, ["EXT2_LATE_NO_OPPOSING_M15"])

    def test_missing_audit_or_missing_history_never_authorizes(self):
        signal, full, reader, boundary, now = self._mock_frozen_proposal()
        with patch("V20_TradingSystem_M15.v20_runtime.finam_execution.read_finam_m15_boundary",
                   return_value=boundary), patch(
                   "V20_TradingSystem_M15.v20_runtime.finam_execution.completed_signal",
                   return_value=signal), patch.object(
                   reader, "snapshot", side_effect=AssertionError("BROKER_SNAPSHOT_UNEXPECTED")):
            with self.assertRaisesRegex(V20FinamBlocked, "R070_EXT2_STAGING_AUDIT_REQUIRED"):
                propose_finam_m15_next_open(
                    reader, symbol="GLDRUBF", from_utc=now-timedelta(days=2),
                    now=now, cost_per_contract=Decimal("0"),
                    r070_ext2_candidate=True, r070_ext2_verified_history=full)
            audits = []
            self.assertIsNone(propose_finam_m15_next_open(
                reader, symbol="GLDRUBF", from_utc=now-timedelta(days=2),
                now=now, cost_per_contract=Decimal("0"),
                r070_ext2_candidate=True, r070_ext2_verified_history=None,
                r070_ext2_audit=lambda **kwargs: (audits.append(
                    kwargs["decision"].reason) or True)))
            self.assertEqual(audits, ["EXT2_CERTIFIED_HISTORY_MISSING"])

    def test_staging_disabled_keeps_existing_pretrade_behavior(self):
        signal, full, reader, boundary, now = self._mock_frozen_proposal()
        with patch("V20_TradingSystem_M15.v20_runtime.finam_execution.read_finam_m15_boundary",
                   return_value=boundary), patch(
                   "V20_TradingSystem_M15.v20_runtime.finam_execution.completed_signal",
                   return_value=signal), patch.object(
                   reader, "snapshot", side_effect=RuntimeError("OLD_SNAPSHOT_PATH")):
            with self.assertRaisesRegex(RuntimeError, "OLD_SNAPSHOT_PATH"):
                propose_finam_m15_next_open(
                    reader, symbol="GLDRUBF", from_utc=now-timedelta(days=2),
                    now=now, cost_per_contract=Decimal("0"))


if __name__ == "__main__":
    main()
