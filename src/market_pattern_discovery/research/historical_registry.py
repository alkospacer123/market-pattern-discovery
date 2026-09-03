"""Historical Strategy Registry v1 read-only enrichment projection."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from market_pattern_discovery.contracts import deterministic_hash
from market_pattern_discovery.research.memory import ResearchMemory


REGISTRY_VERSION = "historical-strategy-registry-v1"


def build_historical_registry(memory: ResearchMemory) -> dict[str, Any]:
    """Build a deterministic audit view without changing append-only history."""
    candidates = memory.candidates()
    evaluations = {row["evaluation_id"]: row for row in memory.evaluation_history()}
    lifecycle: dict[str, list[dict[str, Any]]] = {candidate_id: [] for candidate_id in candidates}
    for sequence, event in enumerate(memory.candidate_history()):
        candidate_id = (event.get("record") or {}).get("candidate_id", event.get("candidate_id"))
        lifecycle.setdefault(candidate_id, []).append({"sequence": sequence, **event})

    records = []
    for candidate_id, candidate in sorted(candidates.items()):
        evaluation = evaluations.get(candidate.metrics_reference)
        parameters = dict(candidate.parameters)
        records.append({
            "candidate_id": candidate_id,
            "strategy_id": candidate.strategy_id,
            "market_scope": {"instrument": candidate.instrument, "timeframe": candidate.timeframe},
            "creation_cycle": candidate.creation_cycle,
            "current_status": candidate.status.value,
            "research_track": parameters.get("research_track", "KNOWN_STRATEGY"),
            "lineage": {
                "originating_experiment_id": parameters.get("originating_experiment_id"),
                "search_cell_id": parameters.get("search_cell_id"),
                "source_pattern_cell_id": parameters.get("source_pattern_cell_id"),
                "pattern_strategy_id": parameters.get("pattern_strategy_id"),
            },
            "parameters": parameters,
            "metrics_reference": candidate.metrics_reference,
            "metrics": dict(evaluation["metrics"]) if evaluation else None,
            "evaluation_metadata": dict(evaluation.get("metadata") or {}) if evaluation else None,
            "lifecycle": lifecycle.get(candidate_id, []),
        })
    payload = {"registry_version": REGISTRY_VERSION, "record_count": len(records), "records": records}
    payload["content_signature"] = deterministic_hash(payload)
    return payload


def write_historical_registry(memory: ResearchMemory, destination: str | Path) -> dict[str, Any]:
    """Write the reproducible projection; source registry files remain untouched."""
    payload = build_historical_registry(memory)
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload
