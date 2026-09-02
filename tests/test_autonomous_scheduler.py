from dataclasses import replace

import pandas as pd
import pytest

from market_pattern_discovery.backtest.phase6b import END, START, ExecutionContext, default_configs, generate_signals
from market_pattern_discovery.experiments import ExperimentRunner
from market_pattern_discovery.orchestration import AutonomousSearchScheduler, CycleRunner, SearchCell
from market_pattern_discovery.research import CandidateRecord, CandidateStatus, RankingView, ResearchMemory
from market_pattern_discovery.research.protocol import assert_discovery_period, assert_true_oos_not_accessed


def _space():
    configs = default_configs()
    return tuple(SearchCell(i, t, s, c) for i in ("CNY", "Si") for t in ("M1", "M5")
                 for s in ("RL-01", "MOM-01") for c in configs)


def _scheduler(tmp_path, memory=None, space=None):
    memory = memory or ResearchMemory(tmp_path / "memory")
    return AutonomousSearchScheduler(memory, tmp_path / "data", tmp_path / "out",
                                     seed=7, search_space=space or _space())


def _record_candidate(memory, cell, scenario="BASE", pf=1.5, expectancy=.1,
                      robustness=.8, suffix=""):
    candidate_id = f"candidate-{scenario}{suffix}"
    evaluation_id = f"evaluation-{scenario}{suffix}"
    candidate = CandidateRecord(candidate_id, cell.strategy, "CNYRUBF", cell.timeframe,
        {"search_cell_id": cell.search_cell_id, "friction_scenario": scenario}, evaluation_id, 0)
    memory.add_candidate(candidate)
    memory.record_evaluation(evaluation_id, candidate_id,
                             {"profit_factor": pf, "expectancy": expectancy,
                              "robustness": robustness})
    return candidate


def _record_parent(memory, cell):
    memory.record_experiment("prior", {"search_cell_id": cell.search_cell_id})
    return _record_candidate(memory, cell)


def test_same_seed_and_memory_is_deterministic_and_cycle_is_not_scientific_identity(tmp_path):
    scheduler = _scheduler(tmp_path)
    first, again = scheduler.plan(1, 5), scheduler.plan(1, 5)
    later = scheduler.plan(99, 5)
    assert [x.search_cell_id for x in first.experiments] == [x.search_cell_id for x in again.experiments]
    assert [x.search_cell_id for x in first.experiments] == [x.search_cell_id for x in later.experiments]
    assert [x.experiment_id for x in first.experiments] != [x.experiment_id for x in later.experiments]
    assert len({x.search_cell_id for x in first.experiments}) == 5


def test_completed_cells_are_not_reused_and_exhaustion_is_explicit(tmp_path):
    space = _space()[:2]
    memory = ResearchMemory(tmp_path / "memory")
    memory.record_experiment("done", {"search_cell_id": space[0].search_cell_id})
    plan = _scheduler(tmp_path, memory, space).plan(2, 5)
    assert [x.search_cell_id for x in plan.experiments] == [space[1].search_cell_id]
    memory.record_experiment("done2", {"search_cell_id": space[1].search_cell_id})
    exhausted = _scheduler(tmp_path, memory, space).plan(3, 5)
    assert not exhausted.experiments
    assert exhausted.metadata["scheduler_status"] == "SEARCH_SPACE_EXHAUSTED"


def test_sixty_forty_allocation_and_real_neighbor_refinement_without_lifecycle_mutation(tmp_path):
    memory = ResearchMemory(tmp_path / "memory")
    space = _space()
    parent = _record_parent(memory, space[0])
    before = memory.candidates()[parent.candidate_id]
    plan = _scheduler(tmp_path, memory, space).plan(1, 5)
    assert plan.metadata["exploration_count"] == 3
    assert plan.metadata["refinement_count"] == 2
    refined = [x for x in plan.experiments if x.metadata["selection_mode"] == "REFINEMENT"]
    assert refined and all(x.metadata["parent_search_cell_id"] == space[0].search_cell_id for x in refined)
    assert all(x.metadata["exit_configurations"] != [list(space[0].exit_configuration)] for x in refined)
    assert memory.candidates()[parent.candidate_id] == before
    assert before.status is CandidateStatus.GENERATED


@pytest.mark.parametrize(("scenario", "pf", "expectancy"), [
    ("GROSS", 9.0, 2.0), ("STRESS", 9.0, 2.0),
    ("BASE", 1.0, .1), ("BASE", 1.5, 0.0),
])
def test_ineligible_friction_or_losing_base_reassigns_all_budget_to_exploration(
        tmp_path, scenario, pf, expectancy):
    memory = ResearchMemory(tmp_path / "memory")
    space = _space()
    memory.record_experiment("prior", {"search_cell_id": space[0].search_cell_id})
    _record_candidate(memory, space[0], scenario, pf, expectancy)
    before = memory.candidate_history()
    plan = _scheduler(tmp_path, memory, space).plan(2, 5)
    assert plan.metadata["refinement_count"] == 0
    assert plan.metadata["exploration_count"] == 5
    assert all(row.metadata["selection_mode"] == "EXPLORATION" for row in plan.experiments)
    assert memory.candidate_history() == before


def test_gross_winner_cannot_override_losing_base(tmp_path):
    memory = ResearchMemory(tmp_path / "memory")
    space = _space()
    memory.record_experiment("prior", {"search_cell_id": space[0].search_cell_id})
    _record_candidate(memory, space[0], "GROSS", 20.0, 4.0)
    _record_candidate(memory, space[0], "BASE", .9, -.1)
    plan = _scheduler(tmp_path, memory, space).plan(2, 5)
    assert plan.metadata["refinement_count"] == 0
    assert plan.metadata["exploration_count"] == 5


def test_eligible_base_is_deduplicated_across_views_and_persists_sibling_evidence(tmp_path):
    memory = ResearchMemory(tmp_path / "memory")
    space = _space()
    memory.record_experiment("prior", {"search_cell_id": space[0].search_cell_id})
    _record_candidate(memory, space[0], "GROSS", 3.0, .3, .9)
    parent = _record_candidate(memory, space[0], "BASE", 1.5, .1, .8)
    _record_candidate(memory, space[0], "STRESS", .8, -.1, .4)
    scheduler = _scheduler(tmp_path, memory, space)
    assert all(parent in memory.view(view) for view in (
        RankingView.TOP_PF, RankingView.TOP_EXPECTANCY, RankingView.TOP_ROBUST))
    parent_ids, evidence = scheduler._parents()
    assert parent_ids == [space[0].search_cell_id]  # present in all three ranking views
    assert evidence[space[0].search_cell_id] == {
        "GROSS": {"profit_factor": 3.0, "expectancy": .3, "robustness": .9},
        "BASE": {"profit_factor": 1.5, "expectancy": .1, "robustness": .8},
        "STRESS": {"profit_factor": .8, "expectancy": -.1, "robustness": .4},
    }
    plan = scheduler.plan(2, 5)
    refined = [row for row in plan.experiments
               if row.metadata["selection_mode"] == "REFINEMENT"]
    assert len(refined) == 2
    assert all(row.metadata["selection_provenance"] ==
               f"NEIGHBOR_OF:{space[0].search_cell_id}" for row in refined)
    assert all(row.metadata["parent_friction_metrics"] == evidence[space[0].search_cell_id]
               for row in refined)
    assert memory.candidates()[parent.candidate_id].status is CandidateStatus.GENERATED

    def fake_v3(_, output, context):
        pd.DataFrame([{"strategy_id": context.strategies[0],
            "instrument": context.instruments[0],
            "exit_configuration": context.exit_configurations[0][0],
            "friction_scenario": "BASE", "profit_factor_ATR": 1.1,
            "expectancy_ATR": .01, "recovery_factor_ATR": .2}]).to_csv(
                output / "strategy_summary.csv", index=False)
        return {"status": "PASS", "timeframe": context.timeframe}

    ExperimentRunner(memory, fake_v3).run(refined[0])
    persisted = memory.experiments()[-1]["metadata"]
    assert persisted["selection_provenance"] == f"NEIGHBOR_OF:{space[0].search_cell_id}"
    assert persisted["parent_friction_metrics"] == evidence[space[0].search_cell_id]


def test_scope_and_data_fences_are_exact():
    assert {(x.instrument, x.timeframe) for x in _space()} == {
        ("CNY", "M1"), ("CNY", "M5"), ("Si", "M1"), ("Si", "M5")}
    assert str(START.date()) == "2026-01-05" and str(END.date()) == "2026-05-16"
    assert START.year != 2025 and END <= pd.Timestamp("2026-05-16", tz="Europe/Moscow")
    with pytest.raises(PermissionError):
        assert_true_oos_not_accessed(("2025-01-01T00:00:00+03:00", "2025-02-01T00:00:00+03:00"))
    with pytest.raises(PermissionError):
        assert_discovery_period(("2026-05-16T00:00:00+03:00", "2026-07-02T00:00:00+03:00"))


def test_execution_parameter_defaults_and_strategy_semantics_are_unchanged():
    assert ExecutionContext.from_metadata({}) == ExecutionContext()
    configured = ExecutionContext.from_metadata({"strategies": ["RL-01"],
        "exit_configurations": [["TIME_15", None, None, 15]]})
    assert configured.strategies == ("RL-01",)
    with pytest.raises(ValueError):
        ExecutionContext(strategies=("invented",))


def test_two_cycle_execution_uses_memory_and_different_cells(tmp_path):
    memory = ResearchMemory(tmp_path / "memory")
    scheduler = _scheduler(tmp_path, memory)

    def fake_v3(_, output, context):
        pd.DataFrame([{"strategy_id": context.strategies[0], "instrument": context.instruments[0],
            "exit_configuration": context.exit_configurations[0][0], "friction_scenario": "BASE",
            "profit_factor_ATR": 1.2, "expectancy_ATR": .1,
            "recovery_factor_ATR": .4}]).to_csv(output / "strategy_summary.csv", index=False)
        return {"status": "PASS", "timeframe": context.timeframe,
                "window": {"start": START.isoformat(), "end_exclusive": END.isoformat()}}

    runner = CycleRunner(ExperimentRunner(memory, fake_v3))
    first = scheduler.plan(10, 4); report1 = runner.run(first)
    second = scheduler.plan(11, 4); report2 = runner.run(second)
    ids1 = {x.search_cell_id for x in first.experiments}; ids2 = {x.search_cell_id for x in second.experiments}
    assert report1.succeeded and report2.succeeded and ids1.isdisjoint(ids2)
    assert second.metadata["refinement_count"] > 0
    assert len(memory.experiments()) == 8
