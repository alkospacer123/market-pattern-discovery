"""Evidence-gated conversion of scientific effects into trade hypotheses.

This module intentionally contains no strategy construction or performance
selection.  A candidate describes a directional behaviour worth investigating;
it does not prescribe how to trade it.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any, Mapping

from market_pattern_discovery.contracts import deterministic_hash

from .hypotheses import Hypothesis
from .intelligence import Evidence, Evaluation, PatternEffect


class TradingDirection(StrEnum):
    LONG = "LONG"
    SHORT = "SHORT"
    UNKNOWN = "UNKNOWN"


class CandidateFamily(StrEnum):
    KNOWN = "KNOWN"
    UNKNOWN_UNIVARIATE = "UNKNOWN_UNIVARIATE"
    UNKNOWN_INTERACTION = "UNKNOWN_INTERACTION"
    UNKNOWN_SUBGROUP = "UNKNOWN_SUBGROUP"


class TradingCandidateStatus(StrEnum):
    CREATED = "CREATED"
    READY_FOR_STRATEGY_SEARCH = "READY_FOR_STRATEGY_SEARCH"
    REJECTED = "REJECTED"


@dataclass(frozen=True, slots=True)
class TradingCandidate:
    """A versioned, scientific trade hypothesis downstream of PatternEffect."""

    candidate_id: str
    source_pattern_effect_id: str
    symbol: str
    horizon: str
    execution_timeframe: str
    context_timeframes: tuple[str, ...]
    direction: TradingDirection
    hypothesis_description: str
    market_state_definition: Mapping[str, Any]
    observed_behavior: str
    target_definition: str
    effect: float
    sample_size: int
    confidence_metadata: Mapping[str, Any]
    candidate_family: CandidateFamily
    status: TradingCandidateStatus
    schema_version: str = "trading-candidate-v1"

    def __post_init__(self) -> None:
        required = (self.candidate_id, self.source_pattern_effect_id, self.symbol,
                    self.horizon, self.execution_timeframe,
                    self.hypothesis_description, self.observed_behavior,
                    self.target_definition, self.schema_version)
        if not all(required) or not self.context_timeframes or self.sample_size <= 0:
            raise ValueError("trading candidate requires complete scientific and market scope")
        object.__setattr__(self, "context_timeframes", tuple(self.context_timeframes))
        object.__setattr__(self, "market_state_definition", dict(self.market_state_definition))
        object.__setattr__(self, "confidence_metadata", dict(self.confidence_metadata))
        object.__setattr__(self, "direction", TradingDirection(self.direction))
        object.__setattr__(self, "candidate_family", CandidateFamily(self.candidate_family))
        object.__setattr__(self, "status", TradingCandidateStatus(self.status))


_FAMILIES = {
    "known_event_evaluation": CandidateFamily.KNOWN,
    "univariate_screen": CandidateFamily.UNKNOWN_UNIVARIATE,
    "interaction_search": CandidateFamily.UNKNOWN_INTERACTION,
    "subgroup_discovery": CandidateFamily.UNKNOWN_SUBGROUP,
}


class TradingCandidateGenerator:
    """Apply quality and lineage gates to one complete scientific finding."""

    def generate(self, effect: PatternEffect, evaluation: Evaluation,
                 evidence: Evidence, hypothesis: Hypothesis) -> TradingCandidate:
        if not isinstance(effect, PatternEffect):
            raise TypeError("TradingCandidate source must be a PatternEffect")
        if evaluation.hypothesis_id != hypothesis.hypothesis_id:
            raise ValueError("evaluation does not reference hypothesis")
        if (effect.evaluation_id != evaluation.evaluation_id or
                evidence.evaluation_id != evaluation.evaluation_id):
            raise ValueError("invalid PatternEffect evaluation lineage")
        if not evidence.qualifies or not evidence.sufficient_sample:
            raise ValueError("PatternEffect lacks qualified, sufficient evidence")
        if (evaluation.effect is None or effect.effect != evaluation.effect or
                effect.sample_size != evaluation.sample_size or effect.sample_size <= 0):
            raise ValueError("PatternEffect conflicts with its evaluation")
        if not evaluation.target or not hypothesis.target_definition or evaluation.target != hypothesis.target_definition:
            raise ValueError("valid matching target definition is required")
        if (not evaluation.context or tuple(evaluation.context) != hypothesis.context_timeframes or
                not evaluation.state_definition or
                dict(evaluation.state_definition) != dict(hypothesis.state_definition)):
            raise ValueError("valid context and market state are required")
        try:
            family = _FAMILIES[hypothesis.method]
        except KeyError as exc:
            raise ValueError("unsupported scientific candidate family") from exc
        direction = (TradingDirection.LONG if effect.effect > 0 else
                     TradingDirection.SHORT if effect.effect < 0 else TradingDirection.UNKNOWN)
        identity_basis = {
            "schema_version": "trading-candidate-v1",
            "source_pattern_effect_id": effect.effect_id,
            "hypothesis_id": hypothesis.hypothesis_id,
            "symbol": hypothesis.symbol,
            "horizon": hypothesis.horizon,
            "execution_timeframe": hypothesis.primary_timeframe,
            "context_timeframes": hypothesis.context_timeframes,
            "direction": direction.value,
            "candidate_family": family.value,
        }
        description = (f"{hypothesis.method} hypothesis for {hypothesis.symbol} "
                       f"{hypothesis.primary_timeframe} under the defined causal state")
        behavior = (f"qualified {'positive' if effect.effect > 0 else 'negative' if effect.effect < 0 else 'zero'} "
                    f"conditional behavior in {hypothesis.target_definition}")
        confidence = {
            "evidence_rationale": evidence.rationale,
            "practical_effect": evidence.practical_effect,
            "statistically_reliable": evidence.statistically_reliable,
            "stable": evidence.stable,
            "uncertainty": evaluation.uncertainty,
            "stability": evaluation.stability,
            "null_comparison": evaluation.null_comparison,
            "multiplicity": evaluation.multiplicity,
        }
        return TradingCandidate(
            deterministic_hash(identity_basis), effect.effect_id, hypothesis.symbol,
            hypothesis.horizon, hypothesis.primary_timeframe,
            hypothesis.context_timeframes, direction, description,
            hypothesis.state_definition, behavior, hypothesis.target_definition,
            effect.effect, effect.sample_size, confidence, family,
            TradingCandidateStatus.READY_FOR_STRATEGY_SEARCH)


def trading_candidate_dict(candidate: TradingCandidate) -> dict[str, Any]:
    value = asdict(candidate)
    value["direction"] = candidate.direction.value
    value["candidate_family"] = candidate.candidate_family.value
    value["status"] = candidate.status.value
    return value
