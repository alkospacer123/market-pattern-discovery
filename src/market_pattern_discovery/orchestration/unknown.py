"""Deterministic, profit-independent UNKNOWN_PATTERN planning and execution."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from market_pattern_discovery.contracts import deterministic_hash
from market_pattern_discovery.discovery.execution_contract import load_execution_contract
from market_pattern_discovery.discovery.protocol import (
    benjamini_hochberg, load_discovery_protocol, screen_effect,
)
from market_pattern_discovery.discovery.unknown import (
    METHODS, _hypotheses, evaluate_hypothesis, load_discovery_matrix,
)
from market_pattern_discovery.research.memory import (
    PatternEffectRecord, PatternStatus, ResearchMemory,
)


@dataclass(frozen=True, slots=True)
class PatternSearchCell:
    instrument: str
    timeframe: str
    method: str
    feature_conditions: tuple[tuple[str, Any], ...]
    target: str
    target_family: str
    target_role: str
    contrast: str
    contract_signatures: tuple[tuple[str, str], ...]
    research_track: str = "UNKNOWN_PATTERN"

    def __post_init__(self) -> None:
        if self.method not in METHODS:
            raise ValueError(f"method is not executable: {self.method}")
        if self.timeframe not in {"M1", "M5"}:
            raise ValueError("timeframe must be M1 or M5")
        if self.research_track != "UNKNOWN_PATTERN":
            raise ValueError("invalid research track")

    @property
    def pattern_cell_id(self) -> str:
        return deterministic_hash(asdict(self))


@dataclass(frozen=True, slots=True)
class PatternBatch:
    cells: tuple[PatternSearchCell, ...]

    def __post_init__(self) -> None:
        ids = [cell.pattern_cell_id for cell in self.cells]
        if not ids or len(ids) != len(set(ids)):
            raise ValueError("batch must contain unique cells")

    @property
    def pattern_batch_id(self) -> str:
        return deterministic_hash({"ordered_pattern_cell_ids": [c.pattern_cell_id for c in self.cells]})


def cells_for_matrix(matrix, *, methods: Sequence[str] = tuple(METHODS),
                     limit: int | None = None) -> tuple[PatternSearchCell, ...]:
    contract = load_execution_contract()
    signatures = tuple(sorted({**contract["upstream_signatures"],
                               "discovery_execution": contract["signature_sha256"]}.items()))
    cells = []
    for method in methods:
        for spec in _hypotheses(matrix, method, contract):
            target = spec["target"]
            cells.append(PatternSearchCell(matrix.instrument, matrix.timeframe, method,
                tuple(tuple(x) for x in spec["conditions"]), target["column_name"],
                target["family"], target["semantic_role"], spec["contrast"], signatures))
            if limit is not None and len(cells) >= limit:
                return tuple(cells)
    return tuple(cells)


def finalize_multiplicity_family(rows: Sequence[dict[str, Any]], *,
                                 expected_family_size: int) -> list[dict[str, Any]]:
    """Attach BH evidence only when the entire preregistered family is present."""
    result = [dict(row) for row in rows]
    if len(result) != expected_family_size or any("raw_p" not in row for row in result):
        for row in result:
            row.update({"family_complete": False, "family_size": expected_family_size,
                        "adjusted_p": None, "q_value": None,
                        "fdr_status": "INCOMPLETE_FAMILY"})
        return result
    adjusted = benjamini_hochberg([row["raw_p"] for row in result])
    policy = load_discovery_protocol()["candidate_screening_policy"]
    for row, q_value in zip(result, adjusted):
        row.update({"family_complete": True, "family_size": expected_family_size,
                    "adjusted_p": float(q_value), "q_value": float(q_value),
                    "fdr_status": "COMPLETE_FAMILY"})
        screening_input = dict(row)
        screening_input["multiplicity_family"] = row.get("multiplicity_family")
        passed, failures = screen_effect(screening_input, policy)
        row["screening_status"] = "PATTERN_SURVIVOR" if passed else "SCREENED_OUT"
        row["screening_failures"] = failures
    return result


class UnknownPatternScheduler:
    """Select unseen frozen cells without reading trading candidates or metrics."""

    def __init__(self, memory: ResearchMemory, data_root: str | Path,
                 output_root: str | Path, *, search_space: Sequence[PatternSearchCell],
                 seed: int = 20260401) -> None:
        self.memory, self.data_root = memory, Path(data_root)
        self.output_root, self.seed = Path(output_root), seed
        self.search_space = tuple(search_space)
        ids = [x.pattern_cell_id for x in self.search_space]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate cells in pattern search space")

    def plan(self, cycle_number: int, budget: int) -> Mapping[str, Any]:
        if budget <= 0:
            raise ValueError("budget must be positive")
        completed = self.memory.completed_pattern_cell_ids()
        unseen = [x for x in self.search_space if x.pattern_cell_id not in completed]
        # Hash ordering is deterministic; scope prefix round-robin keeps markets balanced.
        buckets = {(i, t): [] for i in ("CNYRUBF", "USDRUBF") for t in ("M1", "M5")}
        for cell in unseen:
            buckets.setdefault((cell.instrument, cell.timeframe), []).append(cell)
        for key in buckets:
            buckets[key].sort(key=lambda c: deterministic_hash({"seed": self.seed, "id": c.pattern_cell_id}))
        selected = []
        while len(selected) < budget and any(buckets.values()):
            for key in sorted(buckets):
                if buckets[key] and len(selected) < budget:
                    selected.append(buckets[key].pop(0))
        batch = PatternBatch(tuple(selected)) if selected else None
        return {"cycle_number": cycle_number,
                "scheduler_status": "PLANNED" if batch else "SEARCH_SPACE_EXHAUSTED",
                "pattern_batch": batch, "data_root": self.data_root,
                "output_root": self.output_root, "research_track": "UNKNOWN_PATTERN",
                "search_space_total": len(self.search_space),
                "completed_cells": len(completed),
                "search_space_remaining": len(unseen) - len(selected), "seed": self.seed}


class PatternExperimentRunner:
    """Evaluate feature/behaviour effects; it has no V3/backtest dependency."""

    def __init__(self, memory: ResearchMemory) -> None:
        self.memory = memory

    def run(self, plan: Mapping[str, Any], *, infer: bool = False) -> tuple[PatternEffectRecord, ...]:
        batch = plan.get("pattern_batch")
        if batch is None:
            return ()
        overlap = self.memory.completed_pattern_cell_ids() & {c.pattern_cell_id for c in batch.cells}
        if overlap:
            raise ValueError(f"batch overlaps completed pattern cells: {sorted(overlap)}")
        matrices = {}
        records = []
        experiment_id = deterministic_hash({"batch": batch.pattern_batch_id,
                                            "cycle": plan["cycle_number"]})
        for ordinal, cell in enumerate(batch.cells, 1):
            key = (cell.instrument, cell.timeframe)
            if key not in matrices:
                matrices[key] = load_discovery_matrix(plan["data_root"], *key)
            matrix = matrices[key]
            target = next(x for x in matrix.targets if x["column_name"] == cell.target and x["semantic_role"] == cell.target_role)
            spec = {"ordinal": ordinal, "hypothesis_id": cell.pattern_cell_id,
                    "effect_id": deterministic_hash({"effect": cell.pattern_cell_id}),
                    "method": cell.method, "conditions": list(cell.feature_conditions),
                    "target": target, "contrast": cell.contrast}
            evaluation = evaluate_hypothesis(matrix, spec, infer=infer)
            evaluation.update({"pattern_cell_id": cell.pattern_cell_id,
                "family_complete": False, "family_size": None, "adjusted_p": None,
                "q_value": None, "fdr_status": "INCOMPLETE_FAMILY",
                "inference_enabled": infer, "source_provenance": matrix.provenance,
                "contract_signatures": dict(cell.contract_signatures)})
            status = PatternStatus.INELIGIBLE if evaluation["status"] == "ineligible" else PatternStatus.INCOMPLETE_FAMILY
            record = PatternEffectRecord(cell.pattern_cell_id, batch.pattern_batch_id,
                asdict(cell), evaluation, status, experiment_id, int(plan["cycle_number"]))
            self.memory.add_pattern_effect(record); records.append(record)
        return tuple(records)
