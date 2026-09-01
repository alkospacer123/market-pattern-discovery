"""
Research Brain v1

Purpose:
- keep daemon from becoming a finite job executor only
- scan completed research outputs
- collect near-misses and generate next research hypotheses

This is an analysis layer. It does not change backtest rules,
causal execution, data fence or validation gates.
"""

from __future__ import annotations

import json
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class CandidateObservation:
    source: str
    instrument: str | None = None
    timeframe: str | None = None
    family: str | None = None
    pf: float | None = None
    expectancy: float | None = None
    trades: int | None = None
    status: str = "unknown"


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def scan_results(root: Path) -> list[CandidateObservation]:
    observations = []
    for manifest in root.rglob("run_manifest.json"):
        data = read_json(manifest)
        if not isinstance(data, dict):
            continue
        observations.append(
            CandidateObservation(
                source=str(manifest),
                instrument=data.get("instrument"),
                timeframe=data.get("timeframe"),
                family=data.get("job_type") or data.get("family"),
                status=data.get("status", "completed"),
            )
        )
    return observations


def build_report(results_root: str, output: str):
    observations = scan_results(Path(results_root))
    Path(output).write_text(
        json.dumps([asdict(x) for x in observations], indent=2),
        encoding="utf-8",
    )
    print(f"RESEARCH BRAIN SCAN COMPLETE observations={len(observations)}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results")
    parser.add_argument("--output", default="results/research_brain_observations.json")
    args = parser.parse_args()
    build_report(args.results, args.output)
