import json

import pytest

from market_pattern_discovery.experiments import ExperimentSpec
from market_pattern_discovery.orchestration.cycle import CycleManifest, CycleReport
from market_pattern_discovery.orchestration.worker import AutonomousResearchWorker
from market_pattern_discovery.research.memory import ResearchMemory


class Scheduler:
    def plan(self, cycle_number, budget):
        specs = () if budget == 99 else (ExperimentSpec("one", "/dev/null", "/tmp/out", cycle_number),)
        return CycleManifest(cycle_number, specs)


class Runner:
    def run(self, manifest):
        return CycleReport(manifest.cycle_id, (), {}, ())


def test_worker_runs_and_persists_one_bounded_cycle(tmp_path):
    worker = AutonomousResearchWorker(Scheduler(), ResearchMemory(tmp_path / "memory"),
                                      tmp_path / "state", runner=Runner())
    result = worker.run_once(cycle_number=7, budget=1)
    persisted = json.loads((tmp_path / "state/cycle-000007.json").read_text())

    assert result.status == "COMPLETED"
    assert persisted["cycle_id"] == result.cycle_id
    with pytest.raises(ValueError, match="already finalized"):
        worker.run_once(cycle_number=7, budget=1)


def test_worker_records_exhausted_search_space(tmp_path):
    worker = AutonomousResearchWorker(Scheduler(), ResearchMemory(tmp_path / "memory"),
                                      tmp_path / "state", runner=Runner())
    assert worker.run_once(cycle_number=8, budget=99).status == "SEARCH_SPACE_EXHAUSTED"
