"""Append-only research memory and read-only candidate ranking views.

This module deliberately has no dependency on strategy, signal, simulator, or
metrics code.  Evaluations are accepted as already-computed facts; ranking only
projects those facts into deterministic views.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, replace
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterable, Mapping


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

    @staticmethod
    def _read(path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]

    @staticmethod
    def _append(path: Path, value: Mapping[str, Any]) -> None:
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
        fd = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o644)
        try:
            os.write(fd, (encoded + "\n").encode())
            os.fsync(fd)
        finally:
            os.close(fd)

    def record_experiment(self, experiment_id: str, metadata: Mapping[str, Any]) -> None:
        existing = self._read(self._experiments)
        if any(row["experiment_id"] == experiment_id for row in existing):
            raise ValueError(f"experiment already exists: {experiment_id}")
        search_cell_id = metadata.get("search_cell_id")
        if search_cell_id and any(row["metadata"].get("search_cell_id") == search_cell_id
                                  for row in existing):
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

    def candidate_history(self) -> list[dict[str, Any]]:
        return self._read(self._candidates)

    def evaluation_history(self) -> list[dict[str, Any]]:
        return self._read(self._evaluations)

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
