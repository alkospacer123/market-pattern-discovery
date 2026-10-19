"""Offline tests for real failure modes of the blocked preflight and scalar audit."""
import csv
import math
import tempfile
import unittest
from pathlib import Path

import preflight
import scalar_audit


class SourcePreflightTests(unittest.TestCase):
    def source(self, root, body):
        path = Path(root)/"fixture.csv"
        path.write_text("Datetime;Open;High;Low;Close;Volume\n"+body)
        return path

    def test_duplicate_conflicts_are_detected_before_any_deduplication(self):
        with tempfile.TemporaryDirectory() as root:
            path = self.source(root, "2021-01-04 10:00:00;100;102;99;101;5\n2021-01-04 10:00:00;100;103;99;102;5\n")
            before = path.read_bytes()
            audit = preflight.inspect_csv(path)
            self.assertEqual(audit["duplicate_timestamps"], 1)
            self.assertEqual(audit["conflicting_duplicates"], 1)
            self.assertEqual(audit["non_increasing_transitions"], 1)
            self.assertEqual(path.read_bytes(), before)

    def test_gap_is_unobserved_slot_not_certified_missing_bar(self):
        with tempfile.TemporaryDirectory() as root:
            audit = preflight.inspect_csv(self.source(root, "2021-01-04 10:00:00;100;102;99;101;5\n2021-01-04 13:00:00;101;103;100;102;0\n"))
            self.assertEqual(audit["intraday_unobserved_hour_slots"], 2)
            self.assertIsNone(audit["missing_trading_bars"])
            self.assertEqual(audit["zero_volume_rows"], 1)
            self.assertEqual(audit["rows"], 2)
            self.assertIsNone(audit["roll_rule"])

    def test_invalid_ohlc_and_nonfinite_are_reported(self):
        with tempfile.TemporaryDirectory() as root:
            audit = preflight.inspect_csv(self.source(root, "2021-01-04 10:00:00;100;99;98;101;5\n2021-01-04 11:00:00;100;102;99;101;nan\n"))
            self.assertEqual(audit["invalid_ohlc_rows"], 1)
            self.assertEqual(audit["nonfinite_numeric_rows"], 1)

    def test_unexpected_schema_and_empty_series_are_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            path = self.source(root, "")
            with self.assertRaisesRegex(ValueError, "EMPTY_SOURCE"):
                preflight.inspect_csv(path)
            path.write_text("timestamp,close\n1,100\n")
            with self.assertRaisesRegex(ValueError, "UNEXPECTED_SOURCE_SCHEMA"):
                preflight.inspect_csv(path)

    def test_output_inside_data_root_is_rejected_before_writing(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(ValueError, "OUTPUT_MUST_NOT"):
                preflight.execute(Path(root), Path(root)/"bad-output")
            self.assertFalse((Path(root)/"bad-output").exists())

    def test_uncomputed_metrics_are_blank_never_zero(self):
        with tempfile.TemporaryDirectory() as root:
            preflight.placeholders(Path(root))
            rows = preflight.read_csv(Path(root)/"annual_by_instrument.csv")
            self.assertEqual(len(rows), 48)
            self.assertTrue(all(r["status"] == "DATA_BLOCKED" for r in rows))
            self.assertTrue(all(r[k] == "" for r in rows for k in preflight.METRICS))
            self.assertEqual(preflight.read_csv(Path(root)/"trades.csv"), [])
            comparison = preflight.read_csv(Path(root)/"quarterly_vs_perpetual_n4.csv")
            self.assertTrue(all(r["n4_status"] == "NO_DATA" for r in comparison if int(r["year"]) < 2023))
            self.assertTrue(all(r["perpetual_trades"] == "" for r in comparison))

    def test_frozen_source_and_parameter_payload_authenticate(self):
        audit, _ = preflight.authenticate()
        self.assertEqual(audit["status"], "PASS")
        self.assertEqual(audit["candidate_parameter_sha256"], preflight.PARAM_SHA)
        self.assertEqual(audit["effective_nine_parameters"]["stop_atr"], 2.5)
        self.assertGreater(audit["stage6_ledger"]["walk_forward_rows_excluded"], 0)


class IndependentScalarTests(unittest.TestCase):
    def test_scalar_ewm_manual_values_and_missing_observation_weight(self):
        actual = scalar_audit.ewm([1., 3., float("nan"), 5.], .5, 1)
        self.assertEqual(actual[:3], [1., 2., 2.])
        self.assertAlmostEqual(actual[3], 4.)

    def test_prior_donchian_excludes_current_bar(self):
        rows = [{"time": i, "Open": 10., "High": 11., "Low": 9., "Close": 10.} for i in range(21)]
        rows[-1].update(High=100., Low=1.)
        answer = scalar_audit.indicator_rows(rows)[-1]
        self.assertEqual(answer["PriorHigh"], 11.)
        self.assertEqual(answer["PriorLow"], 9.)

    def test_context_publishes_four_observations_and_never_crosses_day(self):
        rows = scalar_audit.fixture(20)
        result = scalar_audit.context(rows)
        self.assertTrue(all(any(r["time"] == c["time"] for r in rows) for c in result))
        for cut in range(1, 20):
            self.assertEqual(scalar_audit.context(rows[:cut]), [r for r in result if r["time"] <= rows[cut-1]["time"]])

    def test_scalar_reference_and_production_with_future_perturbations(self):
        result = scalar_audit.run_audit()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["adversarial_long_short_trigger_gap_checks"], 2)
        self.assertFalse(result["historical_quarterly_replay_executed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
