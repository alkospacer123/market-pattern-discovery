"""Optional evidence-gated V20 market suitability labels, isolated from trading.

No baseline is embedded here. An externally verified, holdout-tested reference
must be supplied before issuing 3-state verdicts. Unreviewed profiles cannot label.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime
from math import isfinite
from typing import Any, Mapping
from .market_suitability import METRIC_SCHEMA

# Five diagnostic aspects are NOT five mandatory trading conditions. Only this
# compact, externally validated strategy profile can ever label the card.
STRATEGY_METRICS = {
    "SHALLOW_PULLBACK": frozenset(("directional_efficiency", "continuation_rate")),
    "OBV_PRESSURE": frozenset(("pressure_direction_alignment", "continuation_rate")),
    "INSIDE_DAY_RELEASE": frozenset(("range_compression_ratio", "inside_release_continuation_rate")),
}
VERDICTS = ("ДОПУСТИМО", "НЕЙТРАЛЬНО", "НЕДОПУСТИМО")


def _number(value: Any) -> bool:
    return isinstance(value, (float, int)) and not isinstance(value, bool) and isfinite(value)


def _validated(reference: Mapping[str, Any] | None, symbol: str, as_of: str) -> tuple[bool, str]:
    if not isinstance(reference, Mapping):
        return False, "REFERENCE_NOT_PROVIDED"
    if (reference.get("schema") != "v20.market_suitability.validated_reference.v2"
            or reference.get("metric_schema") != METRIC_SCHEMA):
        return False, "REFERENCE_SCHEMA_NOT_VALIDATED"
    evidence = reference.get("evidence")
    if not isinstance(evidence, Mapping) or evidence.get("validation_status") != "PASS":
        return False, "OUT_OF_PERIOD_VALIDATION_NOT_PASSED"
    if evidence.get("independent_holdout") is not True or evidence.get("causal_entry_precedes_outcome") is not True:
        return False, "CAUSAL_HOLDOUT_EVIDENCE_MISSING"
    identifier = evidence.get("artifact_sha256")
    if not isinstance(identifier, str) or len(identifier) != 64 or any(c not in "0123456789abcdef" for c in identifier):
        return False, "AUDITED_ARTIFACT_SHA256_MISSING"
    try:
        calibration_end = date.fromisoformat(evidence["calibration_end"])
        holdout_start = date.fromisoformat(evidence["holdout_start"])
        holdout_end = date.fromisoformat(evidence["holdout_end"])
        evaluation_date = datetime.fromisoformat(as_of).date()
    except (ValueError, TypeError, KeyError):
        return False, "HOLDOUT_DATES_INVALID"
    if not calibration_end < holdout_start <= holdout_end < evaluation_date:
        return False, "NON_CHRONOLOGICAL_REFERENCE"
    universe = reference.get("validated_symbols")
    if not isinstance(universe, (list, tuple)) or not all(isinstance(s, str) for s in universe):
        return False, "VALIDATED_SYMBOL_UNIVERSE_INVALID"
    if symbol not in universe:
        return False, "SYMBOL_NOT_VALIDATED"
    return True, "VERIFIED_REFERENCE"


def apply_market_reference(card: Mapping[str, Any], reference: Mapping[str, Any] | None) -> dict:
    """Annotate readonly diagnostic card with evidence-backed labels and explanations.

    Thresholds and validation evidence are NEVER inferred or optimized here.
    Return a new mapping; original frozen signal/risk/positions cannot be affected.
    """
    result = deepcopy(dict(card))
    result["affects_signals_or_risk"] = False
    result["trading_instrument_authority"] = "OPERATOR_ONLY"
    valid, evidence_reason = _validated(reference, result["symbol"], result["as_of_msk"])
    if result.get("metric_schema") != METRIC_SCHEMA:
        valid, evidence_reason = False, "CARD_METRIC_SCHEMA_MISMATCH"
    result["reference_evidence"] = {"ready": valid, "reason": evidence_reason,
                                    "external_audit_required": True,
                                    "artifact_sha256": (reference.get("evidence", {}).get("artifact_sha256")
                                                        if valid else None)}
    for strategy, fields in STRATEGY_METRICS.items():
        entry = result["strategies"][strategy]
        if entry["suitability"] == "НЕДОСТАТОЧНО ДАННЫХ":
            entry["explanation"] = ["INCOMPLETE_OR_UNVERIFIED_M15"]
            continue
        if not valid:
            entry["suitability"] = "НЕ ОЦЕНЕНО"
            entry["explanation"] = [evidence_reason]
            continue
        strategies = reference.get("strategies")
        rule = strategies.get(strategy) if isinstance(strategies, Mapping) else None
        if not isinstance(rule, Mapping) or set(rule) != fields:
            entry["suitability"] = "НЕ ОЦЕНЕНО"
            entry["explanation"] = ["STRATEGY_RULE_NOT_VALIDATED"]
            continue
        missing, bad_count, good, explanations = False, 0, True, []
        for metric in sorted(fields):
            value = entry["diagnostics"].get(metric)
            spec = rule[metric]
            if not _number(value):
                missing = True
                explanations.append(f"{metric}:NO_OBSERVATION")
                continue
            if (not isinstance(spec, Mapping) or
                    not all(_number(spec.get(k)) for k in ("reject_below", "allow_min", "allow_max", "reject_above")) or
                    not spec["reject_below"] <= spec["allow_min"] <= spec["allow_max"] <= spec["reject_above"]):
                missing = True
                explanations.append(f"{metric}:REFERENCE_RULE_INVALID")
                continue
            if value < spec["reject_below"] or value > spec["reject_above"]:
                bad_count += 1
                good = False
                explanations.append(f"{metric}={value:.6g}:OUTSIDE_EVIDENCED_RANGE[{spec['reject_below']},{spec['reject_above']}]")
            elif spec["allow_min"] <= value <= spec["allow_max"]:
                explanations.append(f"{metric}={value:.6g}:WITHIN_EVIDENCED_RANGE[{spec['allow_min']},{spec['allow_max']}]")
            else:
                good = False
                explanations.append(f"{metric}={value:.6g}:BORDERLINE")
        # Missing evidence is not a negative market assessment; never issue BAD on partial rule data.
        entry["suitability"] = ("НЕ ОЦЕНЕНО" if missing else
                                 "НЕДОПУСТИМО" if bad_count == len(fields) else
                                 "ДОПУСТИМО" if good else "НЕЙТРАЛЬНО")
        entry["explanation"] = explanations
    return result
