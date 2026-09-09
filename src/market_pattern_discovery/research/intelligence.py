"""Evidence-gated effects and non-trading research conclusions."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Mapping

from market_pattern_discovery.contracts import deterministic_hash


class Conclusion(StrEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True, slots=True)
class Evaluation:
    evaluation_id: str
    effect: float | None
    sample_size: int
    metadata: Mapping[str, Any]
    hypothesis_id: str = ""
    baseline_statistic: float | None = None
    conditional_statistic: float | None = None
    target: str = ""
    method: str = ""
    context: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Evidence:
    evaluation_id: str
    qualifies: bool
    rationale: str


@dataclass(frozen=True, slots=True)
class PatternEffect:
    effect_id: str
    evaluation_id: str
    effect: float
    sample_size: int


@dataclass(frozen=True, slots=True)
class KnowledgeConclusion:
    evidence_reference: str
    conclusion: Conclusion
    rationale: str


def create_pattern_effect(evaluation: Evaluation, evidence: Evidence) -> PatternEffect | None:
    if evidence.evaluation_id != evaluation.evaluation_id:
        raise ValueError("evidence does not reference evaluation")
    if not evidence.qualifies:
        return None
    if evaluation.effect is None or evaluation.sample_size <= 0:
        raise ValueError("qualified evidence requires an observed effect and sample")
    return PatternEffect(deterministic_hash({"evaluation": evaluation.evaluation_id,
        "effect": evaluation.effect, "sample_size": evaluation.sample_size}),
        evaluation.evaluation_id, evaluation.effect, evaluation.sample_size)


class ResearchIntelligence:
    """Interpret research evidence; never emits entries, exits, or positions."""
    def conclude(self, evaluation: Evaluation, evidence: Evidence,
                 effect: PatternEffect | None) -> KnowledgeConclusion:
        if evidence.evaluation_id != evaluation.evaluation_id:
            raise ValueError("mismatched evidence")
        if not evidence.qualifies or effect is None or evaluation.effect == 0:
            conclusion = Conclusion.UNRESOLVED
        elif effect.effect > 0:
            conclusion = Conclusion.POSITIVE
        else:
            conclusion = Conclusion.NEGATIVE
        return KnowledgeConclusion(evaluation.evaluation_id, conclusion, evidence.rationale)
