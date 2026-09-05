"""Deterministic, profit-independent UNKNOWN_PATTERN planning and execution."""
from __future__ import annotations

import argparse
import bisect
import heapq
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence, overload

from market_pattern_discovery.contracts import deterministic_hash
from market_pattern_discovery.discovery.execution_contract import load_execution_contract
from market_pattern_discovery.discovery.execution_contract import (
    enumerate_pairs, feature_inventory, subgroup_rules,
)
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


def _cell_factory(matrix, methods: Sequence[str]) -> Iterator[PatternSearchCell]:
    contract = load_execution_contract()
    signatures = tuple(sorted({**contract["upstream_signatures"],
                               "discovery_execution": contract["signature_sha256"]}.items()))
    for method in methods:
        for spec in _hypotheses(matrix, method, contract):
            target = spec["target"]
            yield PatternSearchCell(matrix.instrument, matrix.timeframe, method,
                tuple(tuple(x) for x in spec["conditions"]), target["column_name"],
                target["family"], target["semantic_role"], spec["contrast"], signatures)


def cells_for_matrix(matrix, *, methods: Sequence[str] = tuple(METHODS),
                     limit: int | None = None) -> tuple[PatternSearchCell, ...]:
    """Legacy eager enumerator, retained as the equivalence/audit oracle."""
    iterator = _cell_factory(matrix, methods)
    if limit is None:
        return tuple(iterator)
    from itertools import islice
    return tuple(islice(iterator, limit))


@dataclass(frozen=True, slots=True)
class _ConditionBlock:
    method: str
    features: tuple[str, ...]
    domains: tuple[tuple[Any, ...], ...]
    size: int


class PatternSearchSpace(Sequence[PatternSearchCell]):
    """Restartable, immutable indexed view of the frozen logical universe.

    Only compact condition blocks are resident.  Cells are reconstructed on
    demand, in precisely the nesting order used by :func:`_hypotheses`.
    """
    def __init__(self, scopes: Iterable[Any], *, methods: Sequence[str] = tuple(METHODS)):
        contract = load_execution_contract()
        self._scopes = []
        self._ends: list[int] = []
        total = 0
        for matrix in scopes:
            inventory = feature_inventory(matrix.timeframe, included_only=True,
                                          contract=contract)
            blocks: list[_ConditionBlock] = []
            for method in methods:
                if method == "univariate_screen":
                    definitions = [(entry["feature"],) for entry in inventory]
                elif method == "interaction_search":
                    definitions = [tuple(pair) for pair in enumerate_pairs(
                        inventory, cap=contract["pairwise_selection"]["cap"],
                        timeframe=matrix.timeframe, seed=contract["execution_seed"])]
                else:
                    feature_states = [(x["feature"], matrix.state_values[x["feature"]])
                                      for x in inventory]
                    rules = subgroup_rules(
                        feature_states, cap=contract["subgroup_selection"]["cap"],
                        seed=contract["execution_seed"], depth2_fraction=
                        contract["subgroup_selection"]["depth_allocation"]["2"])
                    outcomes = sum(len(t["hypothesis_contrasts"]) for t in matrix.targets)
                    for rule in rules:
                        features = tuple(name for name, _ in rule)
                        domains = tuple((state,) for _, state in rule)
                        blocks.append(_ConditionBlock(method, features, domains, outcomes))
                    continue
                outcomes = sum(len(t["hypothesis_contrasts"]) for t in matrix.targets)
                for features in definitions:
                    domains = tuple(tuple(matrix.state_values[name]) for name in features)
                    combinations = 1
                    for domain in domains:
                        combinations *= len(domain)
                    blocks.append(_ConditionBlock(method, features, domains,
                                                  combinations * outcomes))
            signatures = tuple(sorted({**contract["upstream_signatures"],
                "discovery_execution": contract["signature_sha256"]}.items()))
            block_ends = []
            scope_total = 0
            for block in blocks:
                scope_total += block.size
                block_ends.append(scope_total)
            targets = tuple((t["column_name"], t["family"], t["semantic_role"], contrast)
                for t in matrix.targets for contrast in t["hypothesis_contrasts"])
            self._scopes.append((matrix.instrument, matrix.timeframe, tuple(blocks),
                                 tuple(block_ends), targets, signatures, scope_total))
            total += scope_total
            self._ends.append(total)

    def __len__(self) -> int:
        return self._ends[-1] if self._ends else 0

    @property
    def scope_counts(self) -> Mapping[tuple[str, str], int]:
        return {(s[0], s[1]): s[6] for s in self._scopes}

    @overload
    def __getitem__(self, index: int) -> PatternSearchCell: ...
    @overload
    def __getitem__(self, index: slice) -> tuple[PatternSearchCell, ...]: ...
    def __getitem__(self, index):
        if isinstance(index, slice):
            return tuple(self[i] for i in range(*index.indices(len(self))))
        if index < 0:
            index += len(self)
        if index < 0 or index >= len(self):
            raise IndexError(index)
        scope_index = bisect.bisect_right(self._ends, index)
        scope_start = 0 if scope_index == 0 else self._ends[scope_index - 1]
        instrument, timeframe, blocks, block_ends, targets, signatures, _ = self._scopes[scope_index]
        local = index - scope_start
        block_index = bisect.bisect_right(block_ends, local)
        block_start = 0 if block_index == 0 else block_ends[block_index - 1]
        block = blocks[block_index]
        within = local - block_start
        outcome_count = len(targets)
        state_ordinal, outcome_ordinal = divmod(within, outcome_count)
        states = [None] * len(block.domains)
        for pos in range(len(block.domains) - 1, -1, -1):
            state_ordinal, digit = divmod(state_ordinal, len(block.domains[pos]))
            states[pos] = block.domains[pos][digit]
        target, family, role, contrast = targets[outcome_ordinal]
        return PatternSearchCell(instrument, timeframe, block.method,
            tuple(zip(block.features, states)), target, family, role, contrast, signatures)

    def __iter__(self) -> Iterator[PatternSearchCell]:
        for instrument, timeframe, blocks, _, targets, signatures, _ in self._scopes:
            for block in blocks:
                combinations = block.size // len(targets)
                for state_ordinal in range(combinations):
                    value = state_ordinal
                    states = [None] * len(block.domains)
                    for pos in range(len(block.domains) - 1, -1, -1):
                        value, digit = divmod(value, len(block.domains[pos]))
                        states[pos] = block.domains[pos][digit]
                    conditions = tuple(zip(block.features, states))
                    for target, family, role, contrast in targets:
                        yield PatternSearchCell(instrument, timeframe, block.method,
                            conditions, target, family, role, contrast, signatures)


class _ReverseKey:
    __slots__ = ("value",)
    def __init__(self, value): self.value = value
    def __lt__(self, other): return self.value > other.value


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


def family_key(cell: PatternSearchCell) -> tuple[str, str, str, str, str]:
    return (cell.instrument, cell.timeframe, cell.method,
            cell.target_family, cell.target_role)


class UnknownPatternScheduler:
    """Select unseen frozen cells without reading trading candidates or metrics."""

    def __init__(self, memory: ResearchMemory, data_root: str | Path,
                 output_root: str | Path, *, search_space: Sequence[PatternSearchCell],
                 seed: int = 20260401) -> None:
        self.memory, self.data_root = memory, Path(data_root)
        self.output_root, self.seed = Path(output_root), seed
        # Preserve lazy/indexed views.  Small caller-provided sequences retain
        # the legacy exact duplicate guard; production universes are validated
        # by their immutable construction contract rather than a 17M-string set.
        self.search_space = search_space
        if not isinstance(search_space, PatternSearchSpace):
            self.search_space = tuple(search_space)
            ids = [x.pattern_cell_id for x in self.search_space]
            if len(ids) != len(set(ids)):
                raise ValueError("duplicate cells in pattern search space")

    def plan(self, cycle_number: int, budget: int) -> Mapping[str, Any]:
        if budget <= 0:
            raise ValueError("budget must be positive")
        completed = self.memory.completed_pattern_cell_ids()
        # Each heap retains exactly the prefix which a full stable bucket sort
        # could consume.  The semantic ID is computed once in this pass and is
        # carried with the finalist into batch construction.
        buckets = {(i, t): [] for i in ("CNYRUBF", "USDRUBF") for t in ("M1", "M5")}
        scope_ordinals = {key: 0 for key in buckets}
        unseen_count = 0
        for cell in self.search_space:
            key = (cell.instrument, cell.timeframe)
            ordinal = scope_ordinals.setdefault(key, 0)
            scope_ordinals[key] = ordinal + 1
            cell_id = cell.pattern_cell_id
            if cell_id in completed:
                continue
            unseen_count += 1
            rank = deterministic_hash({"seed": self.seed, "id": cell_id})
            item = (_ReverseKey((rank, ordinal)), rank, ordinal, cell_id, cell)
            heap = buckets.setdefault(key, [])
            if len(heap) < budget:
                heapq.heappush(heap, item)
            elif (rank, ordinal) < heap[0][0].value:
                heapq.heapreplace(heap, item)
        for key, heap in buckets.items():
            buckets[key] = sorted(heap, key=lambda item: (item[1], item[2]))
        selected = []
        while len(selected) < budget and any(buckets.values()):
            for key in sorted(buckets):
                if buckets[key] and len(selected) < budget:
                    selected.append(buckets[key].pop(0)[4])
        batch = PatternBatch(tuple(selected)) if selected else None
        return {"cycle_number": cycle_number,
                "scheduler_status": "PLANNED" if batch else "SEARCH_SPACE_EXHAUSTED",
                "pattern_batch": batch, "data_root": self.data_root,
                "output_root": self.output_root, "research_track": "UNKNOWN_PATTERN",
                "search_space_total": len(self.search_space),
                "completed_cells": len(completed),
                "search_space_remaining": unseen_count - len(selected), "seed": self.seed}

    def pending_inference_cells(self, budget: int) -> tuple[PatternSearchCell, ...]:
        """Select existing, eligible cells lacking inference in stable seed order."""
        if budget < 0:
            raise ValueError("inference budget must be non-negative")
        effective = self.memory.pattern_effects()
        pending = [cell for cell in self.search_space
                   if cell.pattern_cell_id in effective
                   and effective[cell.pattern_cell_id].screening_status is PatternStatus.INFERENCE_PENDING
                   and "raw_p" not in effective[cell.pattern_cell_id].evaluation]
        pending.sort(key=lambda c: deterministic_hash({"seed": self.seed, "id": c.pattern_cell_id}))
        return tuple(pending[:budget])


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
            status = (PatternStatus.INELIGIBLE if evaluation["status"] == "ineligible"
                      else PatternStatus.INCOMPLETE_FAMILY if infer
                      else PatternStatus.INFERENCE_PENDING)
            record = PatternEffectRecord(cell.pattern_cell_id, batch.pattern_batch_id,
                asdict(cell), evaluation, status, experiment_id, int(plan["cycle_number"]))
            self.memory.add_pattern_effect(record); records.append(record)
        return tuple(records)

    def add_inference(self, cells: Sequence[PatternSearchCell], data_root: str | Path) -> tuple[str, ...]:
        """Compute and append inference for frozen, already-created cells."""
        matrices: dict[tuple[str, str], Any] = {}; completed = []
        for ordinal, cell in enumerate(cells, 1):
            current = self.memory.pattern_effects().get(cell.pattern_cell_id)
            if current is None or current.screening_status is not PatternStatus.INFERENCE_PENDING:
                continue
            key = (cell.instrument, cell.timeframe)
            if key not in matrices:
                matrices[key] = load_discovery_matrix(data_root, *key)
            matrix = matrices[key]
            target = next(x for x in matrix.targets if x["column_name"] == cell.target
                          and x["semantic_role"] == cell.target_role)
            spec = {"ordinal": ordinal, "hypothesis_id": cell.pattern_cell_id,
                    "effect_id": current.evaluation["effect_id"], "method": cell.method,
                    "conditions": list(cell.feature_conditions), "target": target,
                    "contrast": cell.contrast}
            inferred = evaluate_hypothesis(matrix, spec, infer=True)
            evidence = {key: inferred[key] for key in ("uncertainty", "raw_p")}
            evidence.update({"inference_enabled": True, "family_complete": False,
                             "fdr_status": "INCOMPLETE_FAMILY"})
            self.memory.enrich_pattern(cell.pattern_cell_id, evidence,
                                       PatternStatus.INCOMPLETE_FAMILY,
                                       event="INFERENCE_ADDED")
            completed.append(cell.pattern_cell_id)
        return tuple(completed)

    def finalize_ready_families(self, search_space: Sequence[PatternSearchCell]) -> tuple[str, ...]:
        """Finalize whole frozen families using persistent evidence across runs."""
        expected: dict[tuple[str, str, str, str, str], list[PatternSearchCell]] = {}
        for cell in search_space:
            expected.setdefault(family_key(cell), []).append(cell)
        finalized: list[str] = []
        for key in sorted(expected):
            cells = sorted(expected[key], key=lambda c: c.pattern_cell_id)
            effective = self.memory.pattern_effects()
            records = [effective.get(c.pattern_cell_id) for c in cells]
            if not all(records):
                continue
            eligible = [(cell, record) for cell, record in zip(cells, records)
                        if record.screening_status is not PatternStatus.INELIGIBLE]
            if (not eligible or any("raw_p" not in record.evaluation for _, record in eligible)
                    or all(record.evaluation.get("family_complete") for _, record in eligible)):
                continue
            evaluated = finalize_multiplicity_family(
                [dict(record.evaluation) for _, record in eligible],
                expected_family_size=len(eligible))
            for (cell, _), result in zip(eligible, evaluated):
                status = PatternStatus(result["screening_status"])
                self.memory.enrich_pattern(cell.pattern_cell_id, result, status,
                                           event="FAMILY_FINALIZED")
                finalized.append(cell.pattern_cell_id)
        return tuple(finalized)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Resumable UNKNOWN_PATTERN discovery")
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--memory-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--cycle", required=True, type=int)
    parser.add_argument("--mode", choices=("discovery", "inference", "both"), default="both")
    parser.add_argument("--budget", type=int, default=1)
    parser.add_argument("--inference-budget", type=int, default=0)
    parser.add_argument("--methods", nargs="+", choices=METHODS, default=["univariate_screen"])
    parser.add_argument("--instrument", default="CNYRUBF")
    parser.add_argument("--timeframe", choices=("M1", "M5"), default="M1")
    parser.add_argument("--seed", type=int, default=20260401)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    memory = ResearchMemory(args.memory_root)
    matrix = load_discovery_matrix(args.data_root, args.instrument, args.timeframe)
    search_space = cells_for_matrix(matrix, methods=args.methods)
    scheduler = UnknownPatternScheduler(memory, args.data_root, args.output_root,
                                        search_space=search_space, seed=args.seed)
    runner = PatternExperimentRunner(memory)
    if args.mode in {"discovery", "both"}:
        plan = scheduler.plan(args.cycle, args.budget)
        discovered = runner.run(plan, infer=False)
    else:
        plan = {"pattern_batch": None}
        discovered = ()
    inference_budget = args.inference_budget if args.mode in {"inference", "both"} else 0
    pending = scheduler.pending_inference_cells(inference_budget)
    inferred = runner.add_inference(pending, args.data_root)
    finalized = runner.finalize_ready_families(search_space)
    effective = memory.pattern_effects()
    resumed = scheduler.plan(args.cycle + 1, 1)
    args.output_root.mkdir(parents=True, exist_ok=True)
    batch = plan.get("pattern_batch")
    manifest = {"cycle": args.cycle,
        "batch_id": batch.pattern_batch_id if batch else None,
        "pattern_cell_ids": [c.pattern_cell_id for c in batch.cells] if batch else [],
        "execution_mode": args.mode.upper(),
        "inference_mode": "ENABLED" if inference_budget else "DISABLED",
        "completed": [r.pattern_cell_id for r in discovered],
        "patterns_created": len(discovered),
        "inference_pending": len(scheduler.pending_inference_cells(len(search_space))),
        "inference_completed": len(inferred),
        "survivors": sum(effective[cell_id].screening_status is PatternStatus.PATTERN_SURVIVOR
                         for cell_id in finalized),
        "screened_out": sum(effective[cell_id].screening_status is PatternStatus.SCREENED_OUT
                            for cell_id in finalized),
        "families_finalized": list(finalized), "failed": [],
        "remaining_discovery_cells": resumed["search_space_remaining"] + (1 if resumed["pattern_batch"] else 0),
        "remaining_inference_pending_cells": len(scheduler.pending_inference_cells(len(search_space))),
        "source_provenance_hashes": matrix.provenance,
        "contract_signatures": dict(search_space[0].contract_signatures) if search_space else {}}
    destination = args.output_root / f"cycle-{args.cycle:06d}.json"
    destination.write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
