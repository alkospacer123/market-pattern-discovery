"""Research governance plus separate trading and market-effect memory APIs."""

from .memory import (CandidateRecord, CandidateStatus, KnowledgeRecord, PatternEffectRecord,
                     PatternRankingView, PatternStatus, RankingView,
                     ResearchMemory, rank_candidates)
from .historical_registry import build_historical_registry, write_historical_registry
from .protocol import AccessMode, DEFAULT_RESEARCH_SEED, load_protocol, protocol_signature
from .cells import (MultiHorizonScheduler, PROFILES, ResearchCell,
                    ResearchHorizon, ResearchTrack, research_space)
from .execution import ResearchAttempt, ScientificResult, UnifiedResearchExecutor
from .intelligence import (Conclusion, Evidence, Evaluation, KnowledgeConclusion,
                           PatternEffect, ResearchIntelligence, create_pattern_effect)

__all__ = [
    "AccessMode", "CandidateRecord", "CandidateStatus", "DEFAULT_RESEARCH_SEED", "RankingView",
    "PatternEffectRecord", "PatternRankingView", "PatternStatus", "ResearchMemory",
    "KnowledgeRecord",
    "build_historical_registry", "load_protocol", "protocol_signature", "rank_candidates",
    "write_historical_registry",
    "MultiHorizonScheduler", "PROFILES", "ResearchCell", "ResearchHorizon",
    "ResearchTrack", "research_space",
    "ResearchAttempt", "ScientificResult", "UnifiedResearchExecutor",
    "Conclusion", "Evidence", "Evaluation", "KnowledgeConclusion", "PatternEffect",
    "ResearchIntelligence", "create_pattern_effect",
]
