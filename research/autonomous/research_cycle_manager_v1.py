"""
Autonomous Research Cycle Manager v1

Purpose:
- close the loop after daemon job queue exhaustion
- consume Research Brain observations
- create next-generation research queue

This module does NOT modify execution rules or validation contracts.
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone


DEFAULT_OUT = Path("results/research_brain/generated_jobs.json")


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def classify_observations(observations):
    """Prepare conservative hypotheses.

    v1 intentionally creates only follow-up tasks from existing evidence.
    It does not invent unrestricted parameter searches.
    """
    jobs = []
    for item in observations:
        instrument = item.get("instrument")
        timeframe = item.get("timeframe")
        family = item.get("family")
        if not instrument or not timeframe or not family:
            continue
        jobs.append({
            "family": family,
            "instrument": instrument,
            "timeframe": timeframe,
            "source": "research_brain_v1",
            "priority": 50,
        })
    return jobs


def generate(results_root="results", output=DEFAULT_OUT):
    observations_file = Path(results_root) / "research_brain_observations.json"
    observations = load_json(observations_file, [])
    jobs = classify_observations(observations)

    payload = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "count": len(jobs),
        "jobs": jobs,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


if __name__ == "__main__":
    result = generate()
    print(f"RESEARCH CYCLE MANAGER COMPLETE jobs={result['count']}")
