"""Focused boundaries; reuse the locked synthetic engine, never full replay."""
import importlib.util
import sys
from datetime import datetime, timedelta
from pathlib import Path
from decimal import Decimal
from zoneinfo import ZoneInfo
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

import pandas as pd

from V20_TradingSystem_M15.v20_runtime import frozen_adapter as adapter
from V20_TradingSystem_M15.v20_runtime.offline_planner import OfflinePlanner
from V20_TradingSystem_M15.v20_runtime.prepare_n4_quotes import prepare, PROJECT_ROOT
from IntradayLab.core.m15_bars import aggregate_m15
from IntradayLab.core.models import Bar


def locked_module(name):
    path = PROJECT_ROOT / "V20-03" / "offline" / (name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class M15BoundaryTests(TestCase):
    def frame(self):
        return pd.DataFrame([dict(Datetime=datetime(2024, 1, 9, 10),
                                 Open=10., High=11., Low=9., Close=10., Volume=1.)])

    def evaluate(self, frame, at=datetime(2024, 1, 9, 10, 15)):
        return adapter.completed_signal("CNYRUBF", "OBV_PRESSURE", frame,
                                        observed_at=at)

    def test_unfinished_stale_and_future_m15_rejected_before_features(self):
        with patch.object(adapter, "_frozen_immutable_features") as features:
            for minute in (14, 16, 30):
                with self.subTest(minute=minute), self.assertRaisesRegex(ValueError, "ONLY_COMPLETED"):
                    self.evaluate(self.frame(), datetime(2024, 1, 9, 10, minute))
            features.assert_not_called()

    def test_duplicates_reordering_timezone_and_subsecond_rejected(self):
        original = self.frame()
        variants = [pd.concat([original, original], ignore_index=True)]
        later = original.copy(); later.Datetime += timedelta(minutes=15)
        variants.append(pd.concat([later, original], ignore_index=True))
        for offset in (timedelta(microseconds=1), pd.Timedelta(nanoseconds=1)):
            f = original.copy(); f.Datetime += offset; variants.append(f)
        zoned = original.copy(); zoned.Datetime = zoned.Datetime.dt.tz_localize("Europe/Moscow")
        variants.append(zoned)
        with patch.object(adapter, "_frozen_immutable_features") as features:
            for f in variants:
                with self.subTest(frame=str(f.Datetime.tolist())), self.assertRaises(ValueError):
                    self.evaluate(f)
            features.assert_not_called()

    def test_no_cross_contract_or_corrupt_ohlcv(self):
        bad = []
        for field, value in (("Ticker", "Si-3.24"), ("High", 8.),
                             ("Close", float("nan")), ("Volume", -1.)):
            f = self.frame(); f[field] = value; bad.append(f)
        with patch.object(adapter, "_frozen_immutable_features") as features:
            for f in bad:
                with self.subTest(fields=f.to_dict()), self.assertRaises(ValueError):
                    self.evaluate(f)
            features.assert_not_called()

    def test_frozen_session_is_09_msk_not_midnight(self):
        key = OfflinePlanner._session_key
        self.assertEqual(key(datetime(2024, 1, 10, 0)), key(datetime(2024, 1, 9, 23, 45)))
        self.assertNotEqual(key(datetime(2024, 1, 10, 8, 45)), key(datetime(2024, 1, 10, 9)))

    def test_existing_engine_gaps_third_session_roll_stop_and_c1(self):
        locked = locked_module("stress_v20_03")
        with patch.dict(sys.modules, {"stress_v20_03": locked}):
            tests = locked_module("test_causality")
            tests.engine_tests()  # Existing synthetic checks ONLY, no read_inputs/main.

    def test_roll_uses_only_finished_previous_sessions(self):
        locked = locked_module("stress_v20_03")
        rows = []
        for day in ("2022-08-29", "2022-08-30", "2022-08-31"):
            for contract in ("Si-9.22", "Si-12.22"):
                rows.append(dict(family="Si", contract=contract, day=pd.Timestamp(day),
                                 known_after=pd.Timestamp(day)+pd.Timedelta(hours=19),
                                 prior_day_eligible=True))
        history = pd.DataFrame(rows)
        before = locked.roll_plan(history)
        # A future summary cannot alter previously chosen contracts.
        after = locked.roll_plan(pd.concat([history, pd.DataFrame([
            dict(family="Si", contract="Si-3.23", day=pd.Timestamp("2022-09-01"),
                 known_after=pd.Timestamp("2022-09-01 19:00"), prior_day_eligible=True)
        ])], ignore_index=True))
        pd.testing.assert_frame_equal(before, after.iloc[:len(before)].reset_index(drop=True))
        chosen = before[before.chosen_contract.ne("")]
        self.assertTrue((chosen.proof_known_after <= chosen.decision_time).all())
        delayed = history.copy(); delayed.known_after = pd.Timestamp("2022-09-10")
        self.assertTrue(locked.roll_plan(delayed).chosen_contract.eq("").all())

    def test_sources_cannot_be_written_anywhere_in_checkout(self):
        for path in (PROJECT_ROOT / "data", PROJECT_ROOT.parent / "other-data"):
            with self.assertRaisesRegex(ValueError, "OUTSIDE_V20_CHECKOUT"):
                prepare(path)

    def test_prepare_fails_closed_on_existing_wrong_hash(self):
        with TemporaryDirectory() as tmp:
            p = Path(tmp)/"USDRUBF"; p.mkdir(); (p/"USDRUBF_M15.csv").write_text("bad")
            with self.assertRaisesRegex(RuntimeError, "HASH_MISMATCH"):
                prepare(Path(tmp))

    def test_reused_m15_aggregation_never_invents_missing_child_path(self):
        zone = ZoneInfo("Europe/Moscow")
        start = datetime(2024, 1, 9, 9, tzinfo=zone)
        class Rules:
            def windows(self, day):
                return [(start, start+timedelta(minutes=30))]
        rules = Rules(); rules.zone = zone
        rows = {start+i*timedelta(minutes=5): Bar(
            start+i*timedelta(minutes=5), timedelta(minutes=5),
            Decimal(10), Decimal(11), Decimal(9), Decimal(10), Decimal(1))
                for i in (0, 1, 2, 3, 5)}  # second parent has a missing 09:20 child
        parents, diagnostics = aggregate_m15(rows, rules, start.date(),
                                            start.date()+timedelta(days=1))
        self.assertTrue(parents[start].valid)
        self.assertEqual(parents[start].available_at, start+timedelta(minutes=15))
        incomplete = parents[start+timedelta(minutes=15)]
        self.assertFalse(incomplete.valid)
        self.assertTrue(incomplete.high.is_nan())
        self.assertTrue(diagnostics[1]["open_observed"])
        self.assertFalse(diagnostics[1]["valid"])
