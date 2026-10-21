"""Offline-only checks of three independent V20 profiles (no FINAM calls)."""
import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from robot_profiles import N4, SOURCES, profiles, RobotProfile


class V20ProfilesTest(unittest.TestCase):
    def setUp(self):
        self.p = profiles()

    def test_exactly_three_frozen_strategies(self):
        self.assertEqual(set(self.p), {
            "SHALLOW_PULLBACK", "OBV_PRESSURE", "INSIDE_DAY_RELEASE"
        })
        self.assertEqual({p.slot for p in self.p.values()}, {"shallow", "obv", "inside"})
        self.assertEqual({p.frozen_signal_source for p in self.p.values()}, set(SOURCES.values()))

    def test_no_execution_or_broker_binding(self):
        for p in self.p.values():
            self.assertFalse(p.live_enabled)
            self.assertEqual(p.execution_mode, "OFFLINE_ONLY")
            self.assertEqual(p.risk_fraction_provisional, Decimal("0.015"))
            self.assertNotIn("TOKEN", str(p))
            self.assertNotIn("ACCOUNT_ID=", str(p))

    def test_isolation(self):
        for field in ("root", "task_name", "state_path", "audit_path",
                      "account_env", "token_ref_env"):
            values = [getattr(p, field) for p in self.p.values()]
            self.assertEqual(len(set(values)), 3, field)
        for p in self.p.values():
            self.assertEqual(p.root, p.state_path.parent)
            self.assertEqual(p.root, p.audit_path.parent)

    def test_frozen_limits(self):
        for p in self.p.values():
            self.assertEqual(p.symbols, N4)
            self.assertEqual(p.timeframe, "M15")
            self.assertEqual(p.max_new_entries_session, 2)
            self.assertEqual(p.max_new_entries_instrument_session, 1)
            self.assertEqual(p.max_open_positions_instrument, 1)
            self.assertEqual(p.initial_stop_atr, 2)
            self.assertEqual(p.exit_before_observed_session, 3)

    def test_illegal_profile_fails_closed(self):
        from dataclasses import replace
        p = self.p["SHALLOW_PULLBACK"]
        with self.assertRaisesRegex(ValueError, "LIVE_NOT_AUTHORIZED"):
            replace(p, live_enabled=True)
        with self.assertRaisesRegex(ValueError, "STATE_AUDIT_NOT_ISOLATED"):
            replace(p, audit_path=p.state_path)
        with self.assertRaisesRegex(ValueError, "PROVISIONAL_RISK_MISMATCH"):
            replace(p, risk_fraction_provisional=Decimal("0.02"))
        with self.assertRaisesRegex(ValueError, "FROZEN_EXECUTION_LIMITS"):
            replace(p, max_new_entries_session=3)
        with self.assertRaisesRegex(ValueError, "FROZEN_UNIVERSE"):
            replace(p, symbols=("USDRUBF",))
        with self.assertRaisesRegex(ValueError, "PROFILE_STRATEGY_MISMATCH"):
            replace(p, strategy="UNREGISTERED")

    def test_invalid_root_fails(self):
        with self.assertRaisesRegex(ValueError, "ABSOLUTE"):
            profiles("relative_v20")


if __name__ == "__main__":
    unittest.main()
