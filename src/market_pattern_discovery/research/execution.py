"""Common execution boundary for KNOWN and unrestricted UNKNOWN research."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable, Mapping

from market_pattern_discovery.contracts import deterministic_hash
from .cells import ResearchCell, ResearchTrack
from .intelligence import Evidence, Evaluation


@dataclass(frozen=True, slots=True)
class ScientificResult:
    """The only valid output of a production research-track handler.

    Keeping evaluation and evidence together makes it impossible for an
    orchestrator to turn a label-only handler response into knowledge.
    """
    discovery_method: str
    hypothesis_id: str
    evaluation: Evaluation
    evidence: Evidence


@dataclass(frozen=True, slots=True)
class ResearchAttempt:
    symbol: str
    horizon: str
    timeframe: str
    discovery_method: str
    evidence_state: str
    research_track: ResearchTrack
    cell_id: str

    @property
    def identity(self) -> str:
        return deterministic_hash(asdict(self))


class UnifiedResearchExecutor:
    """Dispatch identical prepared data contracts to either research track.

    UNKNOWN receives no family catalogue and is constrained only by the
    callable explicitly supplied by the discovery implementation.
    """
    def __init__(self, known: Callable[..., Mapping[str, Any]],
                 unknown: Callable[..., Mapping[str, Any]]) -> None:
        self._handlers = {ResearchTrack.KNOWN: known, ResearchTrack.UNKNOWN: unknown}

    def execute(self, cell: ResearchCell, market_data: Any, context: Any,
                features: Any) -> tuple[ResearchAttempt, ScientificResult]:
        contract = {"cell": cell, "market_data": market_data, "context": context,
                    "features": features}
        result = self._handlers[cell.research_track](**contract)
        if not isinstance(result, ScientificResult):
            raise TypeError("research handler must return ScientificResult, not labels/metadata")
        if result.evidence.evaluation_id != result.evaluation.evaluation_id:
            raise ValueError("scientific evidence does not reference its evaluation")
        method = result.discovery_method
        state = "QUALIFIED" if result.evidence.qualifies else "UNRESOLVED"
        attempt = ResearchAttempt(cell.symbol, cell.research_horizon.value,
            cell.primary_timeframe, method, state, cell.research_track, cell.identity)
        return attempt, result
