"""Bounded deterministic planning over executable V3 Phase 6B cells."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from market_pattern_discovery.backtest.phase6b import STRATEGIES, default_configs
from market_pattern_discovery.contracts import deterministic_hash
from market_pattern_discovery.experiments import ExperimentSpec
from market_pattern_discovery.research.memory import RankingView, ResearchMemory


@dataclass(frozen=True, slots=True)
class SearchCell:
    instrument: str
    timeframe: str
    strategy: str
    exit_configuration: tuple[str, float | None, float | None, int]

    @property
    def parameters(self) -> Mapping[str, Any]:
        name, stop, target, hold = self.exit_configuration
        return {"exit_configuration": name, "stop_atr": stop,
                "target_r": target, "max_hold_bars": hold}

    @property
    def search_cell_id(self) -> str:
        return deterministic_hash(asdict(self))


def executable_search_space() -> tuple[SearchCell, ...]:
    """The finite product supported by the real execution boundary (396 cells)."""
    return tuple(SearchCell(instrument, timeframe, strategy, config)
                 for instrument in ("CNY", "Si") for timeframe in ("M1", "M5")
                 for strategy in STRATEGIES for config in default_configs())


class AutonomousSearchScheduler:
    """Select unseen scientific cells; never mutates candidate lifecycle state."""

    def __init__(self, memory: ResearchMemory, data_root: str | Path,
                 output_root: str | Path, *, seed: int = 35,
                 exploration_fraction: float = .60,
                 search_space: tuple[SearchCell, ...] | None = None) -> None:
        if not 0 <= exploration_fraction <= 1:
            raise ValueError("exploration_fraction must be in [0, 1]")
        self.memory, self.data_root = memory, Path(data_root)
        self.output_root, self.seed = Path(output_root), seed
        self.exploration_fraction = exploration_fraction
        self.search_space = search_space or executable_search_space()
        ids = [cell.search_cell_id for cell in self.search_space]
        if len(ids) != len(set(ids)):
            raise ValueError("search space contains duplicate semantic cells")

    def _completed(self) -> set[str]:
        return {str(row["metadata"].get("search_cell_id")) for row in self.memory.experiments()
                if row["metadata"].get("search_cell_id")}

    def _ordered(self, cells: list[SearchCell]) -> list[SearchCell]:
        return sorted(cells, key=lambda c: deterministic_hash(
            {"seed": self.seed, "search_cell_id": c.search_cell_id}))

    def _friction_metrics(self) -> dict[str, dict[str, dict[str, float]]]:
        """Return persisted friction evidence grouped by semantic search cell."""
        evaluations = {row["evaluation_id"]: row["metrics"]
                       for row in self.memory.evaluation_history()}
        result: dict[str, dict[str, dict[str, float]]] = {}
        for candidate in sorted(self.memory.candidates().values(),
                                key=lambda row: row.candidate_id):
            cell_id = candidate.parameters.get("search_cell_id")
            scenario = candidate.parameters.get("friction_scenario")
            metrics = evaluations.get(candidate.metrics_reference)
            if cell_id and scenario in {"GROSS", "BASE", "STRESS"} and metrics is not None:
                result.setdefault(str(cell_id), {})[str(scenario)] = dict(metrics)
        return result

    def _parents(self) -> tuple[list[str], dict[str, dict[str, dict[str, float]]]]:
        friction_metrics = self._friction_metrics()
        evaluations = {row["evaluation_id"]: row["metrics"]
                       for row in self.memory.evaluation_history()}
        result: list[str] = []
        for view in (RankingView.TOP_PF, RankingView.TOP_EXPECTANCY, RankingView.TOP_ROBUST):
            for candidate in self.memory.view(view):
                cell_id = candidate.parameters.get("search_cell_id")
                metrics = evaluations.get(candidate.metrics_reference, {})
                eligible = (candidate.parameters.get("friction_scenario") == "BASE"
                            and metrics.get("profit_factor", float("-inf")) > 1.0
                            and metrics.get("expectancy", float("-inf")) > 0.0)
                if eligible and cell_id not in result:
                    result.append(str(cell_id))
        return result, friction_metrics

    @staticmethod
    def _neighbor(parent: SearchCell, other: SearchCell) -> bool:
        if (parent.instrument, parent.timeframe, parent.strategy) != (
                other.instrument, other.timeframe, other.strategy):
            return False
        a, b = parent.exit_configuration, other.exit_configuration
        if a[1] is None or b[1] is None:
            holds = (15, 30, 60)
            return a[1] is b[1] is None and abs(holds.index(a[3]) - holds.index(b[3])) == 1
        stops, targets = (.5, 1.), (1., 1.5, 2.)
        distance = abs(stops.index(a[1]) - stops.index(b[1])) + abs(targets.index(a[2]) - targets.index(b[2]))
        return distance == 1

    def plan(self, cycle_number: int, budget: int):
        from .cycle import CycleManifest
        if budget <= 0:
            raise ValueError("budget must be positive")
        completed = self._completed()
        unseen = [cell for cell in self.search_space if cell.search_cell_id not in completed]
        target_explore = (budget * 60 + 50) // 100 if self.exploration_fraction == .60 else round(budget * self.exploration_fraction)
        target_explore = min(budget, int(target_explore))
        parent_ids, friction_metrics = self._parents()
        by_id = {cell.search_cell_id: cell for cell in self.search_space}
        refinement: list[tuple[SearchCell, str]] = []
        for parent_id in parent_ids:
            parent = by_id.get(parent_id)
            if parent:
                for cell in self._ordered([x for x in unseen if self._neighbor(parent, x)]):
                    if cell.search_cell_id not in {x.search_cell_id for x, _ in refinement}:
                        refinement.append((cell, parent_id))
        refinement = refinement[:budget - target_explore]
        selected = {cell.search_cell_id for cell, _ in refinement}
        exploration_count = min(budget - len(refinement), target_explore + (budget - target_explore - len(refinement)))
        exploration = self._ordered([x for x in unseen if x.search_cell_id not in selected])[:exploration_count]
        planned = [(cell, "EXPLORATION", None) for cell in exploration]
        planned += [(cell, "REFINEMENT", parent) for cell, parent in refinement]
        specs = []
        for index, (cell, mode, parent) in enumerate(planned):
            metadata = {"search_cell_id": cell.search_cell_id, "search_spec": asdict(cell),
                "parameters": dict(cell.parameters),
                "selection_mode": mode, "selection_provenance": mode if parent is None else f"NEIGHBOR_OF:{parent}",
                "parent_search_cell_id": parent, "instrument": cell.instrument,
                "parent_friction_metrics": friction_metrics.get(parent) if parent else None,
                "timeframe": cell.timeframe, "strategies": [cell.strategy],
                "exit_configurations": [list(cell.exit_configuration)]}
            specs.append(ExperimentSpec(f"cell-{cell.search_cell_id[:12]}", self.data_root,
                self.output_root / f"cycle-{cycle_number}" / f"{index:03d}-{cell.search_cell_id[:12]}",
                cycle_number, metadata))
        status = "SEARCH_SPACE_EXHAUSTED" if not specs else "PLANNED"
        metadata = {"scheduler_status": status, "seed": self.seed, "budget": budget,
            "exploration_count": len(exploration), "refinement_count": len(refinement),
            "new_search_cells": len(specs), "skipped_duplicate_cells": len(completed),
            "search_space_remaining": len(unseen) - len(specs)}
        return CycleManifest(cycle_number, tuple(specs), metadata)
