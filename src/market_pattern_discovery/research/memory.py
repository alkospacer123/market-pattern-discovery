"""Append-only research memory and read-only candidate ranking views.

This module deliberately has no dependency on strategy, signal, simulator, or
metrics code.  Evaluations are accepted as already-computed facts; ranking only
projects those facts into deterministic views.
"""
from __future__ import annotations

import json
import math
import os
import errno
from dataclasses import asdict, dataclass, replace
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterable, Mapping

from market_pattern_discovery.contracts import deterministic_hash


class CandidateStatus(StrEnum):
    GENERATED = "GENERATED"
    VALIDATED = "VALIDATED"
    PROMOTED = "PROMOTED"
    REJECTED = "REJECTED"
    RETIRED = "RETIRED"


class RankingView(StrEnum):
    TOP_PF = "TOP_PF"
    TOP_EXPECTANCY = "TOP_EXPECTANCY"
    TOP_ROBUST = "TOP_ROBUST"
    CHAMPIONS = "CHAMPIONS"
    TOP_BASE_PF = "TOP_BASE_PF"
    TOP_BASE_EXPECTANCY = "TOP_BASE_EXPECTANCY"
    TOP_STRESS_PF = "TOP_STRESS_PF"
    TOP_RECOVERY = "TOP_RECOVERY"
    TRADING_SURVIVORS = "TRADING_SURVIVORS"


class PatternStatus(StrEnum):
    INELIGIBLE = "INELIGIBLE"
    INFERENCE_PENDING = "INFERENCE_PENDING"
    INCOMPLETE_FAMILY = "INCOMPLETE_FAMILY"
    SCREENED_OUT = "SCREENED_OUT"
    PATTERN_SURVIVOR = "PATTERN_SURVIVOR"


class PatternRankingView(StrEnum):
    TOP_EFFECT_MAGNITUDE = "TOP_EFFECT_MAGNITUDE"
    TOP_TEMPORAL_STABILITY = "TOP_TEMPORAL_STABILITY"
    TOP_COVERAGE = "TOP_COVERAGE"
    PATTERN_SURVIVORS = "PATTERN_SURVIVORS"


@dataclass(frozen=True, slots=True)
class KnowledgeRecord:
    symbol: str
    horizon: str
    primary_timeframe: str
    context_timeframe: str
    research_track: str
    evidence_reference: str
    conclusion: str
    status: str
    metadata: Mapping[str, Any]
    schema_version: str = "1"

    def __post_init__(self) -> None:
        required = (self.symbol, self.horizon, self.primary_timeframe,
            self.context_timeframe, self.research_track, self.evidence_reference,
            self.conclusion, self.status, self.schema_version)
        if not all(required):
            raise ValueError("knowledge record fields are required")
        if self.conclusion not in {"positive", "negative", "unresolved"}:
            raise ValueError("invalid knowledge conclusion")
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def identity(self) -> str:
        return deterministic_hash(asdict(self))


@dataclass(frozen=True, slots=True)
class PatternEffectRecord:
    pattern_cell_id: str
    pattern_batch_id: str
    scientific_definition: Mapping[str, Any]
    evaluation: Mapping[str, Any]
    screening_status: PatternStatus
    originating_experiment_id: str
    creation_cycle: int

    def __post_init__(self) -> None:
        if not all((self.pattern_cell_id, self.pattern_batch_id,
                    self.originating_experiment_id)):
            raise ValueError("pattern identities are required")
        object.__setattr__(self, "scientific_definition", dict(self.scientific_definition))
        object.__setattr__(self, "evaluation", dict(self.evaluation))
        object.__setattr__(self, "screening_status", PatternStatus(self.screening_status))


@dataclass(frozen=True, slots=True)
class CandidateRecord:
    candidate_id: str
    strategy_id: str
    instrument: str
    timeframe: str
    parameters: Mapping[str, Any]
    metrics_reference: str
    creation_cycle: int
    status: CandidateStatus = CandidateStatus.GENERATED

    def __post_init__(self) -> None:
        if not all((self.candidate_id, self.strategy_id, self.instrument, self.timeframe,
                    self.metrics_reference)):
            raise ValueError("candidate identifiers, market scope, and metrics reference are required")
        if self.creation_cycle < 0:
            raise ValueError("creation_cycle must be non-negative")
        object.__setattr__(self, "parameters", dict(self.parameters))
        object.__setattr__(self, "status", CandidateStatus(self.status))


_TRANSITIONS = {
    CandidateStatus.GENERATED: {CandidateStatus.VALIDATED, CandidateStatus.REJECTED},
    CandidateStatus.VALIDATED: {CandidateStatus.PROMOTED, CandidateStatus.REJECTED},
    CandidateStatus.PROMOTED: {CandidateStatus.RETIRED},
    CandidateStatus.REJECTED: {CandidateStatus.RETIRED},
    CandidateStatus.RETIRED: set(),
}


class ResearchMemory:
    """Filesystem-backed append-only registry.

    Each operation appends one canonical JSON object to its own history file.
    No source data or computed result is produced or changed here.
    """

    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self._experiments = self.directory / "experiments.jsonl"
        self._candidates = self.directory / "candidate_history.jsonl"
        self._evaluations = self.directory / "evaluation_history.jsonl"
        self._patterns = self.directory / "pattern_effect_history.jsonl"
        self._synthesis_assessments = self.directory / "synthesis_assessment_history.jsonl"
        self._attempts = self.directory / "research_attempts.jsonl"
        self._knowledge = self.directory / "knowledge_records.jsonl"
        self._scientific = self.directory / "scientific_findings.jsonl"
        self._trading_candidates = self.directory / "trading_candidates.jsonl"
        self._strategy_candidates = self.directory / "strategy_candidates.jsonl"
        self._backtest_results = self.directory / "backtest_results.jsonl"
        self._validation_reports = self.directory / "validation_reports.jsonl"
        self._strategy_rankings = self.directory / "strategy_rankings.jsonl"

    @staticmethod
    def _read(path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]

    @staticmethod
    def _append(path: Path, value: Mapping[str, Any]) -> None:
        def portable(item: Any) -> Any:
            if isinstance(item, float) and not math.isfinite(item):
                return None
            if isinstance(item, Mapping):
                return {key: portable(child) for key, child in item.items()}
            if isinstance(item, (list, tuple)):
                return [portable(child) for child in item]
            return item
        encoded = json.dumps(portable(value), sort_keys=True, separators=(",", ":"), allow_nan=False)
        fd = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o644)
        try:
            os.write(fd, (encoded + "\n").encode())
            try:
                os.fsync(fd)
            except OSError as exc:
                # Some overlay/remote filesystems cannot provide fsync.  The
                # append and close still preserve process-restart semantics.
                if exc.errno not in {errno.EINVAL, errno.EIO, errno.ENOTSUP}:
                    raise
        finally:
            os.close(fd)

    def record_experiment(self, experiment_id: str, metadata: Mapping[str, Any]) -> None:
        existing = self._read(self._experiments)
        if any(row["experiment_id"] == experiment_id for row in existing):
            raise ValueError(f"experiment already exists: {experiment_id}")
        search_cell_id = metadata.get("search_cell_id")
        if (search_cell_id and metadata.get("research_track") != "SYNTHESIZED_STRATEGY"
                and any(row["metadata"].get("search_cell_id") == search_cell_id
                        for row in existing)):
            raise ValueError(f"search cell already completed: {search_cell_id}")
        self._append(self._experiments, {"experiment_id": experiment_id, "metadata": dict(metadata)})

    def add_candidate(self, candidate: CandidateRecord) -> None:
        if candidate.candidate_id in self.candidates():
            raise ValueError(f"candidate already exists: {candidate.candidate_id}")
        self._append(self._candidates, {"event": "CREATED", "record": self._serialize(candidate)})

    def transition(self, candidate_id: str, status: CandidateStatus) -> CandidateRecord:
        current = self.candidates()[candidate_id]
        target = CandidateStatus(status)
        if target not in _TRANSITIONS[current.status]:
            raise ValueError(f"invalid candidate transition {current.status} -> {target}")
        updated = replace(current, status=target)
        self._append(self._candidates, {"event": "STATUS_CHANGED", "candidate_id": candidate_id,
                                      "from": current.status, "to": target})
        return updated

    def record_evaluation(self, evaluation_id: str, candidate_id: str,
                          metrics: Mapping[str, float], metadata: Mapping[str, Any] | None = None) -> None:
        if candidate_id not in self.candidates():
            raise KeyError(candidate_id)
        if any(row["evaluation_id"] == evaluation_id for row in self._read(self._evaluations)):
            raise ValueError(f"evaluation already exists: {evaluation_id}")
        self._append(self._evaluations, {"evaluation_id": evaluation_id, "candidate_id": candidate_id,
            "metrics": dict(metrics), "metadata": dict(metadata or {})})

    def experiments(self) -> list[dict[str, Any]]:
        return self._read(self._experiments)

    def research_attempts(self) -> list[dict[str, Any]]:
        return self._read(self._attempts)

    def completed_hypothesis_ids(self) -> set[str]:
        """Level-2 memory used by the restart-safe hypothesis scheduler."""
        return {row["hypothesis_id"] for row in self.research_attempts()
                if row.get("hypothesis_id")}

    def record_research_attempt(self, attempt: Any) -> bool:
        """Idempotently append one semantic attempt; return whether it was new."""
        value = asdict(attempt)
        value["research_track"] = str(attempt.research_track.value)
        value["attempt_id"] = attempt.identity
        if any(row["attempt_id"] == attempt.identity for row in self.research_attempts()):
            return False
        self._append(self._attempts, value)
        return True

    def knowledge_records(self) -> list[dict[str, Any]]:
        return self._read(self._knowledge)

    def add_knowledge_record(self, record: KnowledgeRecord) -> bool:
        """Append once across restarts while leaving legacy histories untouched."""
        if any(row["knowledge_id"] == record.identity for row in self.knowledge_records()):
            return False
        value = asdict(record)
        value["knowledge_id"] = record.identity
        self._append(self._knowledge, value)
        return True

    def scientific_findings(self) -> list[dict[str, Any]]:
        return self._read(self._scientific)

    def record_scientific_finding(self, evaluation: Any, evidence: Any,
                                  effect: Any | None) -> bool:
        """Persist compact Hypothesis→Evaluation→Evidence→PatternEffect lineage once."""
        if not evaluation.hypothesis_id:
            raise ValueError("scientific evaluation must reference a hypothesis")
        if evidence.evaluation_id != evaluation.evaluation_id:
            raise ValueError("evidence does not reference evaluation")
        if effect is not None and effect.evaluation_id != evaluation.evaluation_id:
            raise ValueError("pattern effect does not reference evaluation")
        if any(row["evaluation"]["evaluation_id"] == evaluation.evaluation_id
               for row in self.scientific_findings()):
            return False
        self._append(self._scientific, {
            "evaluation": asdict(evaluation), "evidence": asdict(evidence),
            "pattern_effect": asdict(effect) if effect is not None else None,
        })
        return True

    def trading_candidates(self) -> dict[str, Any]:
        """Reload the deterministic, append-only trade-hypothesis registry."""
        from .trading_candidates import TradingCandidate
        return {row["candidate_id"]: TradingCandidate(**row)
                for row in self._read(self._trading_candidates)}

    def add_trading_candidate(self, candidate: Any) -> bool:
        """Persist a candidate once; identical regeneration is a restart-safe skip."""
        from .trading_candidates import TradingCandidate, trading_candidate_dict
        if not isinstance(candidate, TradingCandidate):
            raise TypeError("only TradingCandidate objects can be persisted")
        if candidate.candidate_id in self.trading_candidates():
            return False
        self._append(self._trading_candidates, trading_candidate_dict(candidate))
        return True

    def strategy_candidates(self) -> dict[str, Any]:
        """Reload the deterministic, append-only strategy registry."""
        from .strategy_candidates import StrategyCandidate
        return {row["strategy_id"]: StrategyCandidate(**row)
                for row in self._read(self._strategy_candidates)}

    def add_strategy_candidate(self, candidate: Any) -> bool:
        """Append a strategy once; regenerated identities are harmless skips."""
        from .strategy_candidates import StrategyCandidate, strategy_candidate_dict
        if not isinstance(candidate, StrategyCandidate):
            raise TypeError("only StrategyCandidate objects can be persisted")
        sources = self.trading_candidates()
        if candidate.source_trading_candidate_id not in sources:
            raise ValueError("strategy source TradingCandidate is not in memory")
        if candidate.strategy_id in self.strategy_candidates():
            return False
        self._append(self._strategy_candidates, strategy_candidate_dict(candidate))
        return True

    def backtest_results(self) -> dict[str, Any]:
        """Reload immutable StrategyCandidate evaluation facts."""
        from market_pattern_discovery.backtest import BacktestResult
        return {row["backtest_id"]: BacktestResult.from_dict(row)
                for row in self._read(self._backtest_results)}

    def add_backtest_result(self, result: Any) -> bool:
        """Append a result once, requiring its strategy lineage to be present."""
        from market_pattern_discovery.backtest import BacktestResult
        if not isinstance(result, BacktestResult):
            raise TypeError("only BacktestResult objects can be persisted")
        if result.strategy_id not in self.strategy_candidates():
            raise ValueError("backtest StrategyCandidate is not in memory")
        existing = self.backtest_results()
        if result.backtest_id in existing:
            if existing[result.backtest_id] != result:
                raise ValueError("backtest identity collision")
            return False
        self._append(self._backtest_results, result.to_dict())
        return True

    def validation_reports(self) -> dict[str, Any]:
        """Reload immutable BacktestResult validation facts."""
        from market_pattern_discovery.validation import ValidationReport
        return {row["validation_id"]: ValidationReport.from_dict(row)
                for row in self._read(self._validation_reports)}

    def add_validation_report(self, report: Any) -> bool:
        """Append once and enforce complete StrategyCandidate→BacktestResult lineage."""
        from market_pattern_discovery.validation import ValidationReport
        if not isinstance(report, ValidationReport):
            raise TypeError("only ValidationReport objects can be persisted")
        backtests = self.backtest_results()
        if report.backtest_id not in backtests:
            raise ValueError("validation BacktestResult is not in memory")
        if backtests[report.backtest_id].strategy_id != report.strategy_id:
            raise ValueError("validation strategy lineage is inconsistent")
        existing = self.validation_reports()
        if report.validation_id in existing:
            if existing[report.validation_id] != report:
                raise ValueError("validation identity collision")
            return False
        self._append(self._validation_reports, report.to_dict())
        return True

    def strategy_rankings(self) -> dict[str, Any]:
        """Reload immutable, versioned validation ranking facts."""
        from market_pattern_discovery.ranking import StrategyRanking
        return {row["ranking_id"]: StrategyRanking.from_dict(row)
                for row in self._read(self._strategy_rankings)}

    def add_strategy_ranking(self, ranking: Any) -> bool:
        """Append once, enforcing the complete persisted validation lineage."""
        from market_pattern_discovery.ranking import StrategyRanking
        if not isinstance(ranking, StrategyRanking):
            raise TypeError("only StrategyRanking objects can be persisted")
        reports = self.validation_reports()
        if ranking.validation_id not in reports:
            raise ValueError("ranking ValidationReport is not in memory")
        report = reports[ranking.validation_id]
        if report.strategy_id != ranking.strategy_id:
            raise ValueError("ranking strategy lineage is inconsistent")
        strategies, sources = self.strategy_candidates(), self.trading_candidates()
        strategy = strategies.get(ranking.strategy_id)
        if strategy is None or strategy.source_trading_candidate_id != ranking.trading_candidate_id:
            raise ValueError("ranking TradingCandidate lineage is inconsistent")
        source = sources.get(ranking.trading_candidate_id)
        if source is None or source.source_pattern_effect_id != ranking.pattern_effect_id:
            raise ValueError("ranking PatternEffect lineage is inconsistent")
        expected = deterministic_hash({"validation_id": ranking.validation_id,
                                       "ranking_version": ranking.ranking_version})
        if ranking.ranking_id != expected:
            raise ValueError("ranking identity is not deterministic")
        existing = self.strategy_rankings()
        if ranking.ranking_id in existing:
            if existing[ranking.ranking_id] != ranking:
                raise ValueError("ranking identity collision")
            return False
        self._append(self._strategy_rankings, ranking.to_dict())
        return True

    def candidate_history(self) -> list[dict[str, Any]]:
        return self._read(self._candidates)

    def evaluation_history(self) -> list[dict[str, Any]]:
        return self._read(self._evaluations)

    def pattern_effect_history(self) -> list[dict[str, Any]]:
        return self._read(self._patterns)

    def synthesis_assessment_history(self) -> list[dict[str, Any]]:
        """Return immutable Phase 4C assessment events in append order."""
        return self._read(self._synthesis_assessments)

    def record_synthesis_assessment(self, assessment: Mapping[str, Any]) -> None:
        """Append an assessment fact; candidate lifecycle records are never edited."""
        required = {"pattern_strategy_id", "source_pattern_cell_id",
                    "execution_search_cell_id", "exit_configuration",
                    "assessment_complete", "trading_survivor"}
        missing = required - assessment.keys()
        if missing:
            raise ValueError(f"missing synthesis assessment fields: {sorted(missing)}")
        self._append(self._synthesis_assessments, dict(assessment))

    def latest_synthesis_assessments(self) -> dict[str, dict[str, Any]]:
        """Latest append-only assessment keyed by semantic execution cell."""
        return {row["execution_search_cell_id"]: row
                for row in self.synthesis_assessment_history()}

    def completed_pattern_cell_ids(self) -> set[str]:
        return {row["pattern_cell_id"] for row in self.pattern_effect_history()
                if row.get("event", "CREATED") == "CREATED"}

    def add_pattern_effect(self, record: PatternEffectRecord) -> None:
        if record.pattern_cell_id in self.completed_pattern_cell_ids():
            raise ValueError(f"pattern cell already completed: {record.pattern_cell_id}")
        value = asdict(record)
        value["screening_status"] = record.screening_status.value
        value["event"] = "CREATED"
        self._append(self._patterns, value)

    def enrich_pattern(self, pattern_cell_id: str, evaluation: Mapping[str, Any],
                       status: PatternStatus, *, event: str) -> None:
        """Append evidence for an existing hypothesis without rediscovering it."""
        if pattern_cell_id not in self.completed_pattern_cell_ids():
            raise KeyError(pattern_cell_id)
        if event not in {"INFERENCE_ADDED", "FAMILY_FINALIZED"}:
            raise ValueError("invalid pattern evidence event")
        current = self.pattern_effects()[pattern_cell_id]
        if event == "INFERENCE_ADDED" and "raw_p" in current.evaluation:
            raise ValueError(f"inference already exists: {pattern_cell_id}")
        if event == "FAMILY_FINALIZED" and current.evaluation.get("family_complete"):
            raise ValueError(f"family already finalized: {pattern_cell_id}")
        self._append(self._patterns, {"event": event, "pattern_cell_id": pattern_cell_id,
            "evaluation": dict(evaluation), "screening_status": PatternStatus(status).value})

    def pattern_effects(self) -> dict[str, PatternEffectRecord]:
        """Reconstruct the effective latest state from append-only evidence."""
        result: dict[str, PatternEffectRecord] = {}
        for row in self.pattern_effect_history():
            if row.get("event", "CREATED") == "CREATED":
                value = dict(row); value.pop("event", None)
                result[value["pattern_cell_id"]] = PatternEffectRecord(**value)
            else:
                current = result[row["pattern_cell_id"]]
                result[current.pattern_cell_id] = replace(
                    current, evaluation={**current.evaluation, **row["evaluation"]},
                    screening_status=PatternStatus(row["screening_status"]))
        return result

    def pattern_view(self, view: PatternRankingView, *, limit: int | None = None) -> list[dict[str, Any]]:
        rows = [self._pattern_dict(record) for record in self.pattern_effects().values()]
        view = PatternRankingView(view)
        if view is PatternRankingView.PATTERN_SURVIVORS:
            rows = [r for r in rows if r["screening_status"] == PatternStatus.PATTERN_SURVIVOR]
            rows.sort(key=lambda r: r["pattern_cell_id"])
        elif view is PatternRankingView.TOP_EFFECT_MAGNITUDE:
            rows.sort(key=lambda r: (-r["evaluation"].get("primary_effect_absolute", float("-inf")), r["pattern_cell_id"]))
        elif view is PatternRankingView.TOP_COVERAGE:
            rows.sort(key=lambda r: (-r["evaluation"].get("coverage", float("-inf")), r["pattern_cell_id"]))
        else:
            def stability(row):
                effects = [x.get("effect") for x in row["evaluation"].get("fold_results", [])]
                effects = [x for x in effects if isinstance(x, (int, float))]
                signed = row["evaluation"].get("primary_effect_signed", 0)
                return sum((x > 0) == (signed > 0) for x in effects if x != 0)
            rows.sort(key=lambda r: (-stability(r), r["pattern_cell_id"]))
        return rows[:limit] if limit is not None else rows

    @staticmethod
    def _pattern_dict(record: PatternEffectRecord) -> dict[str, Any]:
        value = asdict(record)
        value["screening_status"] = record.screening_status.value
        return value

    def candidates(self) -> dict[str, CandidateRecord]:
        result: dict[str, CandidateRecord] = {}
        for event in self.candidate_history():
            if event["event"] == "CREATED":
                record = event["record"]
                result[record["candidate_id"]] = CandidateRecord(**record)
            else:
                current = result[event["candidate_id"]]
                result[current.candidate_id] = replace(current, status=CandidateStatus(event["to"]))
        return result

    def view(self, view: RankingView, *, limit: int | None = None) -> list[CandidateRecord]:
        """Return a deterministic projection without updating candidates or evaluations."""
        selected = list(self.candidates().values())
        view = RankingView(view)
        if view is RankingView.CHAMPIONS:
            selected = [candidate for candidate in selected if candidate.status is CandidateStatus.PROMOTED]
            selected.sort(key=lambda candidate: candidate.candidate_id)
        elif view is RankingView.TRADING_SURVIVORS:
            passing = {cell for cell, row in self.latest_synthesis_assessments().items()
                       if row.get("assessment_complete") is True
                       and row.get("trading_survivor") is True}
            selected = [c for c in selected
                        if c.parameters.get("pattern_strategy_id") is not None
                        and c.parameters.get("friction_scenario") == "BASE"
                        and c.parameters.get("execution_search_cell_id") in passing]
            selected.sort(key=lambda c: c.candidate_id)
        elif view in {RankingView.TOP_BASE_PF, RankingView.TOP_BASE_EXPECTANCY,
                      RankingView.TOP_STRESS_PF, RankingView.TOP_RECOVERY}:
            referenced = {row["evaluation_id"]: row["metrics"] for row in self.evaluation_history()}
            scenario = "STRESS" if view is RankingView.TOP_STRESS_PF else "BASE"
            key = {RankingView.TOP_BASE_PF:"profit_factor", RankingView.TOP_BASE_EXPECTANCY:"expectancy",
                   RankingView.TOP_STRESS_PF:"profit_factor", RankingView.TOP_RECOVERY:"robustness"}[view]
            selected = [c for c in selected if c.parameters.get("pattern_strategy_id") is not None
                        and c.parameters.get("friction_scenario") == scenario
                        and key in referenced.get(c.metrics_reference,{})]
            selected.sort(key=lambda c: (-referenced[c.metrics_reference][key], c.candidate_id))
        else:
            key = {RankingView.TOP_PF: "profit_factor", RankingView.TOP_EXPECTANCY: "expectancy",
                   RankingView.TOP_ROBUST: "robustness"}[view]
            referenced = {row["evaluation_id"]: row["metrics"] for row in self.evaluation_history()}
            selected = [candidate for candidate in selected if key in referenced.get(candidate.metrics_reference, {})]
            selected.sort(key=lambda candidate: (-referenced[candidate.metrics_reference][key], candidate.candidate_id))
        return selected[:limit] if limit is not None else selected

    @staticmethod
    def _serialize(candidate: CandidateRecord) -> dict[str, Any]:
        value = asdict(candidate)
        value["status"] = candidate.status.value
        return value


def rank_candidates(candidates: Iterable[CandidateRecord], metrics: Mapping[str, Mapping[str, float]],
                    view: RankingView) -> list[CandidateRecord]:
    """Pure convenience view for callers that do not need persistence."""
    records = list(candidates)
    view = RankingView(view)
    if view is RankingView.CHAMPIONS:
        return sorted((row for row in records if row.status is CandidateStatus.PROMOTED),
                      key=lambda row: row.candidate_id)
    metric = {RankingView.TOP_PF: "profit_factor", RankingView.TOP_EXPECTANCY: "expectancy",
              RankingView.TOP_ROBUST: "robustness"}[view]
    return sorted((row for row in records if metric in metrics.get(row.metrics_reference, {})),
                  key=lambda row: (-metrics[row.metrics_reference][metric], row.candidate_id))
