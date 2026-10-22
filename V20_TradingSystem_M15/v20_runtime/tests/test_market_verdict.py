"""V20 evidence-gated market verdict: synthetic offline tests, no FINAM/orders."""
import unittest
from copy import deepcopy

from V20_TradingSystem_M15.v20_runtime.market_verdict import apply_market_reference, STRATEGY_METRICS
from V20_TradingSystem_M15.v20_runtime.market_suitability import METRIC_SCHEMA


def card():
    result = {"symbol": "SILV", "as_of_msk": "2026-10-22T18:00:00",
              "metric_schema": METRIC_SCHEMA, "strategies": {
        name: {"suitability": "НЕ ОЦЕНЕНО", "diagnostics": {m: .4 for m in fields}}
        for name, fields in STRATEGY_METRICS.items()}, "affects_signals_or_risk": False}
    result["strategies"]["OBV_PRESSURE"]["diagnostics"]["pressure_direction_alignment"] = .8
    return result


def profile():
    bounds = {"reject_below": .1, "allow_min": .3, "allow_max": .7, "reject_above": .9}
    return {"schema": "v20.market_suitability.validated_reference.v2",
            "metric_schema": METRIC_SCHEMA,
            "validated_symbols": ["SILV"],
            "evidence": {
                "validation_status": "PASS",
                "independent_holdout": True,
                "causal_entry_precedes_outcome": True,
                "artifact_sha256": "a" * 64,
                "calibration_end": "2023-12-31",
                "holdout_start": "2024-01-01",
                "holdout_end": "2026-09-30"},
            "strategies": {
                strategy: {metric: bounds.copy() for metric in entry["diagnostics"]}
                for strategy, entry in card()["strategies"].items()}}


class VerdictTests(unittest.TestCase):
    def test_legacy_proxy_profile_is_rejected(self):
        reference = profile()
        reference['schema'] = 'v20.market_suitability.validated_reference.v1'
        self.assertEqual(apply_market_reference(card(),reference)['reference_evidence']['reason'],
                         'REFERENCE_SCHEMA_NOT_VALIDATED')

    def test_bidirectional_status_transitions_are_synthetic_only(self):
        original, reference = card(), profile()
        for value, label in ((.05,'НЕЙТРАЛЬНО'),(.4,'ДОПУСТИМО'),(.8,'НЕЙТРАЛЬНО'),
                             (.95,'НЕДОПУСТИМО'),(.4,'ДОПУСТИМО')):
            original['strategies']['SHALLOW_PULLBACK']['diagnostics']['directional_efficiency'] = value
            original['strategies']['SHALLOW_PULLBACK']['diagnostics']['continuation_rate'] = .95 if value == .95 else .4
            self.assertEqual(apply_market_reference(original,reference)['strategies']['SHALLOW_PULLBACK']['suitability'],label)

    def test_default_unknown_not_neutral(self):
        original = card()
        out = apply_market_reference(original, None)
        self.assertTrue(all(s["suitability"] == "НЕ ОЦЕНЕНО"
                            for s in out["strategies"].values()))
        self.assertEqual(original, card())

    def test_allow_neutral_reject_are_distinct(self):
        original, reference = card(), profile()
        out = apply_market_reference(original, reference)
        self.assertEqual(out["strategies"]["SHALLOW_PULLBACK"]["suitability"],
                         "ДОПУСТИМО")
        self.assertEqual(out["strategies"]["OBV_PRESSURE"]["suitability"],
                         "НЕЙТРАЛЬНО")
        original["strategies"]["INSIDE_DAY_RELEASE"]["diagnostics"]["range_compression_ratio"] = .05
        out = apply_market_reference(original, reference)
        self.assertEqual(out["strategies"]["INSIDE_DAY_RELEASE"]["suitability"],
                         "НЕЙТРАЛЬНО")
        original["strategies"]["INSIDE_DAY_RELEASE"]["diagnostics"]["inside_release_continuation_rate"] = .05
        out = apply_market_reference(original, reference)
        self.assertEqual(out["strategies"]["INSIDE_DAY_RELEASE"]["suitability"],
                         "НЕДОПУСТИМО")
        self.assertFalse(out["affects_signals_or_risk"])

    def test_unvalidated_market_never_labeled(self):
        reference = profile()
        reference["validated_symbols"] = ["CNYRUBF"]
        self.assertEqual(apply_market_reference(card(), reference)["reference_evidence"]["reason"],
                         "SYMBOL_NOT_VALIDATED")
        self.assertEqual(apply_market_reference(card(), reference)["strategies"]["SHALLOW_PULLBACK"]["suitability"],
                         "НЕ ОЦЕНЕНО")

    def test_no_holdout(self):
        reference = profile()
        reference["evidence"]["independent_holdout"] = False
        self.assertEqual(apply_market_reference(card(), reference)["strategies"]["SHALLOW_PULLBACK"]["suitability"],
                         "НЕ ОЦЕНЕНО")

    def test_future_leakage_evidence_rejected(self):
        reference = profile()
        reference["evidence"]["calibration_end"] = "2025-07-01"
        self.assertEqual(apply_market_reference(card(), reference)["reference_evidence"]["reason"],
                         "NON_CHRONOLOGICAL_REFERENCE")

    def test_holdout_not_finished_before_card_cannot_label(self):
        reference = profile()
        reference["evidence"]["holdout_end"] = "2027-01-01"
        self.assertEqual(apply_market_reference(card(), reference)["reference_evidence"]["reason"],
                         "NON_CHRONOLOGICAL_REFERENCE")

    def test_bad_rule_remains_not_evaluated(self):
        reference = profile()
        reference["strategies"]["SHALLOW_PULLBACK"]["continuation_rate"]["allow_min"] = 2
        self.assertEqual(apply_market_reference(card(), reference)["strategies"]["SHALLOW_PULLBACK"]["suitability"],
                         "НЕ ОЦЕНЕНО")

    def test_missing_and_bad_metric_never_false_negative(self):
        original, reference = card(), profile()
        original["strategies"]["SHALLOW_PULLBACK"]["diagnostics"].pop("continuation_rate")
        original["strategies"]["SHALLOW_PULLBACK"]["diagnostics"]["directional_efficiency"] = .01
        self.assertEqual(apply_market_reference(original, reference)["strategies"]["SHALLOW_PULLBACK"]["suitability"],
                         "НЕ ОЦЕНЕНО")

    def test_incomplete_card_stays_incomplete(self):
        original, reference = card(), profile()
        original["strategies"]["SHALLOW_PULLBACK"]["suitability"] = "НЕДОСТАТОЧНО ДАННЫХ"
        self.assertEqual(apply_market_reference(original, reference)["strategies"]["SHALLOW_PULLBACK"]["suitability"],
                         "НЕДОСТАТОЧНО ДАННЫХ")

    def test_mutation_no_effect_on_caller(self):
        original, reference = card(), profile()
        before = deepcopy(original)
        apply_market_reference(original, reference)
        self.assertEqual(original, before)


if __name__ == "__main__":
    unittest.main()
