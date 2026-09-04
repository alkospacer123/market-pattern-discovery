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
        self.data_root = "/data"
        self.search_space = (object(),)

    def plan(self, cycle_number, budget):
        self.calls.append("unknown")
        if self.fail:
            raise RuntimeError("unknown failed")
        return {"pattern_batch": PatternBatch(), "cycle_number": cycle_number}

    def pending_inference_cells(self, budget):
        self.calls.append(("pending", budget))
        return ()


class UnknownRunner:
    def __init__(self, calls):
        self.calls = calls

    def run(self, plan, *, infer):
        self.calls.append("unknown-runner")
        assert infer is False
        return ()

    def add_inference(self, cells, data_root):
        self.calls.append("inference")
        return ()

    def finalize_ready_families(self, search_space):
        self.calls.append("finalize")
        return ()


def test_worker_runs_and_persists_one_bounded_cycle(tmp_path):
    worker = AutonomousResearchWorker(Scheduler(), ResearchMemory(tmp_path / "memory"),
                                      tmp_path / "state", runner=Runner())
    result = worker.run_once(cycle_number=7, budget=1)
    persisted = json.loads((tmp_path / "state/cycle-000007.json").read_text())

    assert result.status == "COMPLETED"
    assert persisted["cycle_id"] == result.cycle_id
    assert {key: persisted[key] for key in (
        "patterns_created", "inference_pending", "inference_completed",
        "survivors", "screened_out")} == {
            "patterns_created": 0, "inference_pending": 0,
            "inference_completed": 0, "survivors": 0, "screened_out": 0}
    with pytest.raises(ValueError, match="already finalized"):
        worker.run_once(cycle_number=7, budget=1)


def test_worker_records_exhausted_search_space(tmp_path):
    worker = AutonomousResearchWorker(Scheduler(), ResearchMemory(tmp_path / "memory"),
                                      tmp_path / "state", runner=Runner())
    assert worker.run_once(cycle_number=8, budget=99).status == "SEARCH_SPACE_EXHAUSTED"


@pytest.mark.parametrize("track, expected", [
    ("known", ["known"]),
    ("unknown", ["unknown", "unknown-runner", ("pending", 2), "inference",
                 "finalize", ("pending", 1)]),
    ("mixed", ["known"]),
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
    worker.run_once(cycle_number=1, budget=1, inference_budget=2)
    assert calls == expected


def test_mixed_budget_is_one_total_budget(tmp_path):
    allocations = []

    class KnownScheduler(Scheduler):
        def plan(self, cycle_number, budget):
            allocations.append(("known", budget))
            return super().plan(cycle_number, budget)

    class AllocatingUnknownScheduler(UnknownScheduler):
        def plan(self, cycle_number, budget):
            allocations.append(("unknown", budget))
            return super().plan(cycle_number, budget)

    calls = []
    worker = AutonomousResearchWorker(
        KnownScheduler(), ResearchMemory(tmp_path / "memory"), tmp_path / "state",
        runner=Runner(), track="mixed",
        unknown_scheduler=AllocatingUnknownScheduler(calls),
        unknown_runner=UnknownRunner(calls))
    worker.run_once(cycle_number=1, budget=5)
    assert allocations == [("known", 3), ("unknown", 2)]
    assert sum(value for _, value in allocations) == 5


def test_mixed_initializes_unknown_only_after_known_execution(tmp_path):
    calls = []

    class KnownScheduler(Scheduler):
        def plan(self, cycle_number, budget):
            calls.append("known")
            return super().plan(cycle_number, budget)

    def build_unknown_components():
        calls.append("initialize-unknown")
        return UnknownScheduler(calls), UnknownRunner(calls)

    worker = AutonomousResearchWorker(
        KnownScheduler(), ResearchMemory(tmp_path / "memory"), tmp_path / "state",
        runner=Runner(), track="mixed",
        unknown_components_factory=build_unknown_components)

    assert calls == []
    worker.run_once(cycle_number=1, budget=2)
    assert calls[:3] == ["known", "initialize-unknown", "unknown"]


@pytest.mark.parametrize("inference_budget, inferred, expected_status", [
    (1, ("pending-cell",), "COMPLETED"),
    (0, (), "INFERENCE_PENDING"),
])
def test_unknown_exhaustion_preserves_and_services_pending_inference(
        tmp_path, inference_budget, inferred, expected_status):
    calls = []

    class ExhaustedUnknownScheduler(UnknownScheduler):
        def plan(self, cycle_number, budget):
            calls.append("unknown-exhausted")
            return {"pattern_batch": None, "cycle_number": cycle_number}

        def pending_inference_cells(self, budget):
            calls.append(("pending", budget))
            return ("pending-cell",) if budget else ()

    class InferenceRunner(UnknownRunner):
        def add_inference(self, cells, data_root):
            calls.append(("inference", cells, data_root))
            return inferred

    worker = AutonomousResearchWorker(
        Scheduler(), ResearchMemory(tmp_path / "memory"), tmp_path / "state",
        runner=Runner(), track="unknown",
        unknown_scheduler=ExhaustedUnknownScheduler(calls),
        unknown_runner=InferenceRunner(calls))
    result = worker.run_once(
        cycle_number=1, budget=1, inference_budget=inference_budget)

    assert result.status == expected_status
    assert calls[0] == "unknown-exhausted"
    assert calls[1:3] == [
        ("pending", inference_budget),
        ("inference", ("pending-cell",) if inference_budget else (), "/data"),
    ]


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
    result = worker.run_once(cycle_number=1, budget=2)
    assert calls[0] == "known"
    assert "unknown" in calls
    assert result.status == "COMPLETED_WITH_FAILURES"
    assert failing_track in result.failures
