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


class PatternBatch:
    pattern_batch_id = "unknown-batch"


class UnknownScheduler:
    def __init__(self, calls, *, fail=False):
        self.calls, self.fail = calls, fail

    def plan(self, cycle_number, budget):
        self.calls.append("unknown")
        if self.fail:
            raise RuntimeError("unknown failed")
        return {"pattern_batch": PatternBatch(), "cycle_number": cycle_number}


class UnknownRunner:
    def __init__(self, calls):
        self.calls = calls

    def run(self, plan, *, infer):
        self.calls.append("unknown-runner")
        assert infer is False
        return ()


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


@pytest.mark.parametrize("track, expected", [
    ("known", ["known"]),
    ("unknown", ["unknown", "unknown-runner"]),
    ("mixed", ["known", "unknown", "unknown-runner"]),
])
def test_worker_routes_tracks_in_deterministic_order(tmp_path, track, expected):
    calls = []

    class KnownScheduler(Scheduler):
        def plan(self, cycle_number, budget):
            calls.append("known")
            return super().plan(cycle_number, budget)

    options = {}
    if track != "known":
        options = {"unknown_scheduler": UnknownScheduler(calls),
                   "unknown_runner": UnknownRunner(calls)}
    worker = AutonomousResearchWorker(
        KnownScheduler(), ResearchMemory(tmp_path / "memory"), tmp_path / "state",
        runner=Runner(), track=track, **options)
    worker.run_once(cycle_number=1, budget=1)
    assert calls == expected


@pytest.mark.parametrize("failing_track", ["known", "unknown"])
def test_mixed_track_isolates_failures(tmp_path, failing_track):
    calls = []

    class KnownScheduler(Scheduler):
        def plan(self, cycle_number, budget):
            calls.append("known")
            if failing_track == "known":
                raise RuntimeError("known failed")
            return super().plan(cycle_number, budget)

    worker = AutonomousResearchWorker(
        KnownScheduler(), ResearchMemory(tmp_path / "memory"), tmp_path / "state",
        runner=Runner(), track="mixed",
        unknown_scheduler=UnknownScheduler(calls, fail=failing_track == "unknown"),
        unknown_runner=UnknownRunner(calls))
    result = worker.run_once(cycle_number=1, budget=1)
    assert calls[0] == "known"
    assert "unknown" in calls
    assert result.status == "COMPLETED_WITH_FAILURES"
    assert failing_track in result.failures
