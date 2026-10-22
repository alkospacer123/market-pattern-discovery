"""V20 evidence-gated market verdict: synthetic offline tests, no FINAM/orders."""
import unittest
from copy import deepcopy

from V20_TradingSystem_M15.v20_runtime.market_verdict import apply_market_reference


def card():
    return {"symbol": "SILV", "strategies": {
        "SHALLOW_PULLBACK": {"suitability": "НЕ ОЦЕНЕНО", "diagnostics": {
            "directional_efficiency": .4, "continuation_rate": .6}},
        "OBV_PRESSURE": {"suitability": "НЕ ОЦЕНЕНО", "diagnostics": {
            "signed_volume_pressure_abs": .8, "continuation_rate": .6}},
        "INSIDE_DAY_RELEASE": {"suitability": "НЕ ОЦЕНЕНО", "diagnostics": {
            "inside_session_share": .2, "continuation_rate": .6}}
    }, "affects_signals_or_risk": False}


def profile():
    bounds = {"reject_below": .1, "allow_min": .3, "allow_max": .7, "reject_above": .9}
    return {"schema": "v20.market_suitability.validated_reference.v1",
            "validated_symbols": ["SILV"],
            "evidence": {
                "validation_status": "PASS",
                "independent_holdout": True,
                "causal_entry_precedes_outcome": True,
                "artifact_sha256": "a" * 64,
                "calibration_end": "2024-12-31",
                "holdout_start": "2025-01-01"},
            "strategies": {
                strategy: {metric: bounds.copy() for metric in entry["diagnostics"]}
                for strategy, entry in card()["strategies"].items()}}


class VerdictTests(unittest.TestCase):
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
        original["strategies"]["INSIDE_DAY_RELEASE"]["diagnostics"]["inside_session_share"] = .05
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
