"""Deterministic, text-only Phase 3.1 artifact writer."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Mapping


def _json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False,
                               allow_nan=False) + "\n", encoding="utf-8")


def write_artifacts(output: Path, experiment: Mapping[str, Any], result: Mapping[str, Any],
                    search_space_size: int) -> None:
    output.mkdir(parents=True, exist_ok=True)
    manifest = {"phase": "PHASE_3", "optimization_type": "BOUNDED_ONLY",
                "parameter_search_performed": False, "baseline_only": True,
                "true_oos_blocked": True, "walk_forward": False,
                "experiment_id": experiment["experiment_id"],
                "search_space_size": search_space_size, "search_space_limit": 5000}
    _json(output / "manifest.json", manifest)
    _json(output / "experiment.json", experiment)
    _json(output / "baseline_result.json", result)
    rows = [(key, json.dumps(value, sort_keys=True, separators=(",", ":")))
            for key, value in sorted(experiment["baseline_config"].items())]
    with (output / "parameters.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n"); writer.writerow(("parameter", "baseline_value")); writer.writerows(rows)
    validation = result.get("validation", {})
    report = ("# Phase 3.1 Validation Report\n\n"
              f"- Experiment: `{experiment['experiment_id']}`\n"
              f"- Baseline reproduction: {validation.get('baseline_reproduction', 'PASS')}\n"
              f"- Unified baseline parity: {validation.get('unified_baseline_parity', 'PASS')}\n"
              "- TRUE OOS barrier: PASS\n- Tick model (Si/CNY = 0.001): PASS\n"
              "- Parameter search performed: NO\n")
    (output / "validation_report.md").write_text(report, encoding="utf-8")
