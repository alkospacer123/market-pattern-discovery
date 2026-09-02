from dataclasses import replace

import pytest

from market_pattern_discovery.experiments.runner import ExperimentRunner, ExperimentSpec
from market_pattern_discovery.orchestration.unknown import (
    PatternBatch, PatternSearchCell, UnknownPatternScheduler,
    finalize_multiplicity_family,
)
from market_pattern_discovery.research.memory import (
    PatternEffectRecord, PatternRankingView, PatternStatus, RankingView, ResearchMemory,
)

SIGS = (("feature_set", "a"), ("targets", "b"))

def cell(**changes):
    values = dict(instrument="CNYRUBF", timeframe="M1", method="univariate_screen",
        feature_conditions=(("candle_range", "LE_P10"),), target="behavior_signed_displacement_atr_5",
        target_family="DIRECTIONAL", target_role="SHORT_SIGNED_DISPLACEMENT",
        contrast="median_difference", contract_signatures=SIGS)
    values.update(changes)
    return PatternSearchCell(**values)

def test_scientific_identity_is_deterministic_and_execution_independent(tmp_path):
    assert cell().pattern_cell_id == cell().pattern_cell_id
    a = UnknownPatternScheduler(ResearchMemory(tmp_path/"m"), "/data", tmp_path/"a", search_space=(cell(),)).plan(1, 1)
    b = UnknownPatternScheduler(ResearchMemory(tmp_path/"n"), "/data", tmp_path/"b", search_space=(cell(),)).plan(99, 1)
    assert a["pattern_batch"].cells[0].pattern_cell_id == b["pattern_batch"].cells[0].pattern_cell_id

def test_substantive_and_contract_changes_change_identity():
    base = cell().pattern_cell_id
    assert cell(feature_conditions=(("candle_range", "GE_P90"),)).pattern_cell_id != base
    assert cell(target="other").pattern_cell_id != base
    assert cell(contrast="probability_difference").pattern_cell_id != base
    assert cell(contract_signatures=(("feature_set", "drift"),)).pattern_cell_id != base

def test_batch_identity_is_ordered_and_separate():
    other = cell(instrument="USDRUBF")
    batch = PatternBatch((cell(), other))
    assert batch.pattern_batch_id != cell().pattern_cell_id
    assert batch.pattern_batch_id != PatternBatch((other, cell())).pattern_batch_id
    with pytest.raises(ValueError): PatternBatch((cell(), cell()))

def record(c, cycle=0):
    return PatternEffectRecord(c.pattern_cell_id, PatternBatch((c,)).pattern_batch_id,
        {"definition": "effect"}, {"primary_effect_absolute": .2, "coverage": .1,
        "primary_effect_signed": .2, "fold_results": [{"effect": .1}]},
        PatternStatus.INCOMPLETE_FAMILY, "experiment", cycle)

def test_memory_rejects_duplicate_and_patterns_never_enter_trading_views(tmp_path):
    memory = ResearchMemory(tmp_path)
    memory.add_pattern_effect(record(cell()))
    with pytest.raises(ValueError): memory.add_pattern_effect(record(cell(), 2))
    assert memory.pattern_view(PatternRankingView.TOP_EFFECT_MAGNITUDE)
    assert memory.view(RankingView.TOP_PF) == []

def test_scheduler_deterministic_resumable_balanced_and_exhausted(tmp_path):
    cells = tuple(cell(instrument=i, timeframe=t) for i in ("CNYRUBF", "USDRUBF") for t in ("M1", "M5"))
    memory = ResearchMemory(tmp_path/"m")
    scheduler = UnknownPatternScheduler(memory, "/data", tmp_path, search_space=cells)
    p1 = scheduler.plan(1, 2)
    assert [x.pattern_cell_id for x in p1["pattern_batch"].cells] == [x.pattern_cell_id for x in scheduler.plan(1,2)["pattern_batch"].cells]
    for c in p1["pattern_batch"].cells: memory.add_pattern_effect(record(c))
    p2 = scheduler.plan(2, 2)
    assert not ({x.pattern_cell_id for x in p1["pattern_batch"].cells} & {x.pattern_cell_id for x in p2["pattern_batch"].cells})
    for c in p2["pattern_batch"].cells: memory.add_pattern_effect(record(c))
    assert scheduler.plan(3, 1)["scheduler_status"] == "SEARCH_SPACE_EXHAUSTED"

def test_incomplete_family_has_no_q_and_complete_family_gets_bh():
    base = {"raw_p": .01, "multiplicity_family": "f", "coverage": .2, "unique_days": 20,
        "uncertainty": {"lower": .1, "upper": .2}, "primary_effect_signed": .1,
        "effect_metrics": {"primary_effect": .1}, "target_family": "DIRECTIONAL",
        "fold_results": [{"effect": .1}, {"effect": .1}]}
    incomplete = finalize_multiplicity_family([base], expected_family_size=2)[0]
    assert incomplete["fdr_status"] == "INCOMPLETE_FAMILY" and incomplete["q_value"] is None
    complete = finalize_multiplicity_family([base, {**base, "raw_p": .04}], expected_family_size=2)
    assert [x["q_value"] for x in complete] == pytest.approx([.02, .04])

def test_known_runner_calls_v3_once_and_rejects_unknown(tmp_path):
    calls=[]
    def pipeline(data, output): calls.append(1); return {}
    runner=ExperimentRunner(pipeline=pipeline)
    runner.run(ExperimentSpec("known", tmp_path, tmp_path/"out"))
    assert calls == [1]
    with pytest.raises(ValueError):
        runner.run(ExperimentSpec("unknown", tmp_path, tmp_path/"u", metadata={"research_track":"UNKNOWN_PATTERN"}))
    assert calls == [1]
