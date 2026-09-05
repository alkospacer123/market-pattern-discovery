from dataclasses import asdict, replace
import json
import shutil

import numpy as np
import pandas as pd
import pytest

from market_pattern_discovery.experiments.runner import ExperimentRunner, ExperimentSpec
from market_pattern_discovery.discovery.unknown import DiscoveryMatrix, evaluate_hypothesis
from market_pattern_discovery.orchestration.unknown import (
    PatternBatch, PatternExperimentRunner, PatternSearchCell, PatternSearchSpace,
    UnknownPatternScheduler, UnknownUniverseIndex, build_unknown_universe_index,
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


def test_audit_serializer_is_exact_for_unicode_punctuation_and_state_types():
    import market_pattern_discovery.orchestration.unknown as unknown
    representatives = (
        cell(feature_conditions=(("цена/Δ", "≤ p10; \"quoted\""),)),
        cell(method="interaction_search", timeframe="M5",
             feature_conditions=(("binary", 1), ("flag", True)),
             contrast="P(+1) − P(−1)"),
        cell(method="subgroup_discovery", instrument="USDRUBF",
             feature_conditions=(("missing", None),)),
    )
    for item in representatives:
        assert unknown._audit_cell_id(item) == item.pattern_cell_id

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


def test_lazy_indexed_space_exactly_matches_legacy_enumerator(monkeypatch):
    import market_pattern_discovery.orchestration.unknown as unknown
    import market_pattern_discovery.discovery.unknown as discovery_unknown
    target = {"column_name": "target", "family": "DIRECTIONAL",
              "semantic_role": "ROLE", "hypothesis_contrasts": ["a", "b"]}
    matrix = DiscoveryMatrix("CNYRUBF", "M1", pd.DataFrame(), {},
        {"f": ["x", "y"], "g": [0, 1, 2]}, [target], [])
    monkeypatch.setattr(unknown, "feature_inventory", lambda *a, **k:
                        [{"feature": "f"}, {"feature": "g"}])
    monkeypatch.setattr(unknown, "enumerate_pairs", lambda *a, **k: [("f", "g")])
    monkeypatch.setattr(unknown, "subgroup_rules", lambda *a, **k:
                        [(('f', 'x'),), (('f', 'y'), ('g', 2))])
    monkeypatch.setattr(discovery_unknown, "feature_inventory", unknown.feature_inventory)
    monkeypatch.setattr(discovery_unknown, "enumerate_pairs", unknown.enumerate_pairs)
    monkeypatch.setattr(discovery_unknown, "subgroup_rules", unknown.subgroup_rules)
    methods = tuple(unknown.METHODS)
    eager = unknown.cells_for_matrix(matrix, methods=methods)
    lazy = PatternSearchSpace((matrix,), methods=methods)
    assert len(lazy) == len(eager)
    assert tuple(lazy) == eager
    assert lazy[0] == eager[0] and lazy[-1] == eager[-1]
    assert lazy[3:9] == eager[3:9]
    assert tuple(lazy) == tuple(lazy)  # restartable, not generator state


def test_bounded_planner_matches_legacy_and_stable_collision_order(tmp_path, monkeypatch):
    import market_pattern_discovery.orchestration.unknown as unknown
    cells = tuple(cell(instrument=i, timeframe=t,
        feature_conditions=(("candle_range", str(n)),))
        for i in ("CNYRUBF", "USDRUBF") for t in ("M1", "M5") for n in range(7))
    real_hash = unknown.deterministic_hash
    monkeypatch.setattr(unknown, "deterministic_hash", lambda value:
        "collision" if isinstance(value, dict) and set(value) == {"seed", "id"}
        else real_hash(value))
    scheduler = UnknownPatternScheduler(ResearchMemory(tmp_path / "memory"),
        "/data", tmp_path, search_space=cells)
    plan = scheduler.plan(1, 9)
    buckets = {(i, t): [] for i in ("CNYRUBF", "USDRUBF") for t in ("M1", "M5")}
    for item in cells: buckets[(item.instrument, item.timeframe)].append(item)
    expected = []
    while len(expected) < 9:
        for key in sorted(buckets):
            if buckets[key] and len(expected) < 9: expected.append(buckets[key].pop(0))
    assert plan["pattern_batch"].cells == tuple(expected)


def test_manifest_rank_index_validation_and_exact_planning(tmp_path, monkeypatch):
    import market_pattern_discovery.orchestration.unknown as unknown
    import market_pattern_discovery.discovery.unknown as discovery_unknown
    target = {"column_name": "target", "family": "DIRECTIONAL",
              "semantic_role": "ROLE", "hypothesis_contrasts": ["a", "b"]}
    matrices = [DiscoveryMatrix(i, t, pd.DataFrame(), {}, {"f": ["x", "y"]},
        [target], []) for i in ("CNYRUBF", "USDRUBF") for t in ("M1", "M5")]
    inventory = lambda *a, **k: [{"feature": "f"}]
    monkeypatch.setattr(unknown, "feature_inventory", inventory)
    monkeypatch.setattr(discovery_unknown, "feature_inventory", inventory)
    space = PatternSearchSpace(matrices, methods=("univariate_screen",))
    monkeypatch.setattr(UnknownUniverseIndex, "EXPECTED_TOTAL", len(space))
    root = tmp_path / "index"
    manifest = build_unknown_universe_index(space, root, seed=17)
    assert manifest["total_count"] == 16
    indexed_memory = ResearchMemory(tmp_path / "indexed")
    eager_memory = ResearchMemory(tmp_path / "eager")
    def compare(budget):
        indexed = UnknownPatternScheduler(indexed_memory, "/data", tmp_path,
            search_space=space, seed=17, index_root=root).plan(1, budget)
        eager = UnknownPatternScheduler(eager_memory, "/data", tmp_path,
            search_space=tuple(space), seed=17).plan(1, budget)
        assert indexed["scheduler_status"] == eager["scheduler_status"]
        assert indexed["search_space_remaining"] == eager["search_space_remaining"]
        left = indexed["pattern_batch"]; right = eager["pattern_batch"]
        assert ([c.pattern_cell_id for c in left.cells] if left else []) == [
            c.pattern_cell_id for c in right.cells] if right else []
        return left
    for budget in (1, 2, 3, 4, 5, 11):
        compare(budget)
    top = compare(1).cells[0]
    indexed_memory.add_pattern_effect(record(top))
    eager_memory.add_pattern_effect(record(top))
    compare(5)
    # Exhaust one complete scope, then reopen both memories and compare resume.
    for item in tuple(space)[:4]:
        if item.pattern_cell_id != top.pattern_cell_id:
            indexed_memory.add_pattern_effect(record(item))
            eager_memory.add_pattern_effect(record(item))
    indexed_memory = ResearchMemory(tmp_path / "indexed")
    eager_memory = ResearchMemory(tmp_path / "eager")
    compare(7)

    cases = ("missing", "corrupt", "truncated", "version", "schema",
             "binding", "seed", "rank")
    for case in cases:
        broken = tmp_path / case
        shutil.copytree(root, broken)
        path = broken / "manifest.json"
        value = json.loads(path.read_text())
        if case == "missing": path.unlink()
        elif case == "corrupt": path.write_text("not json")
        elif case == "truncated": path.write_text(path.read_text()[:20])
        elif case == "rank":
            rank_path = next(broken.glob("rank-*.u32"))
            rank_path.write_bytes(rank_path.read_bytes()[:-1])
        else:
            if case == "version": value["manifest_version"] += 1
            elif case == "schema": value["iterator_schema"] = "stale"
            elif case in {"binding", "seed"}: value["universe_binding_sha256"] = "0" * 64
            value["content_sha256"] = unknown.deterministic_hash(
                {k: v for k, v in value.items() if k != "content_sha256"})
            path.write_text(json.dumps(value))
        with pytest.raises(ValueError):
            UnknownUniverseIndex(broken, space, 18 if case == "seed" else 17)

def test_incomplete_family_has_no_q_and_complete_family_gets_bh():
    base = {"raw_p": .01, "multiplicity_family": "f", "coverage": .2, "unique_days": 20,
        "uncertainty": {"lower": .1, "upper": .2}, "primary_effect_signed": .1,
        "effect_metrics": {"primary_effect_signed": .1, "primary_effect_absolute": .1}, "target_family": "DIRECTIONAL",
        "fold_results": [{"effect": .1}, {"effect": .1}]}
    incomplete = finalize_multiplicity_family([base], expected_family_size=2)[0]
    assert incomplete["fdr_status"] == "INCOMPLETE_FAMILY" and incomplete["q_value"] is None
    complete = finalize_multiplicity_family([base, {**base, "raw_p": .04}], expected_family_size=2)
    assert [x["q_value"] for x in complete] == pytest.approx([.02, .04])


def test_real_evaluate_result_obeys_screening_effect_contract():
    dates = np.repeat(pd.date_range("2021-01-01", periods=12, tz="UTC"), 10)
    frame = pd.DataFrame({"timestamp": dates,
        "moscow_trading_date": pd.Series(dates).dt.date,
        "target": np.tile(np.arange(10, dtype=float), 12),
        "candle_range": np.tile(np.arange(10, dtype=float), 12)})
    states = pd.Series(np.tile(["LE_P10"] * 5 + ["other"] * 5, 12))
    target = {"column_name": "target", "family": "DIRECTIONAL",
              "semantic_role": "SHORT_SIGNED_DISPLACEMENT", "target_type": "continuous"}
    matrix = DiscoveryMatrix("CNYRUBF", "M1", frame, {"candle_range": states},
                             {"candle_range": ["LE_P10", "other"]}, [target], [])
    result = evaluate_hypothesis(matrix, {"hypothesis_id": "h", "effect_id": "e",
        "ordinal": 1, "method": "univariate_screen",
        "conditions": [("candle_range", "LE_P10")], "target": target,
        "contrast": "median_difference"}, infer=False)
    result.update({"raw_p": .02, "uncertainty": {"lower": -1., "upper": 1.}})
    finalized = finalize_multiplicity_family([result], expected_family_size=1)
    assert finalized[0]["family_complete"] is True
    assert "primary_effect" not in result["effect_metrics"]

def test_known_runner_calls_v3_once_and_rejects_unknown(tmp_path):
    calls=[]
    def pipeline(data, output): calls.append(1); return {}
    runner=ExperimentRunner(pipeline=pipeline)
    runner.run(ExperimentSpec("known", tmp_path, tmp_path/"out"))
    assert calls == [1]
    with pytest.raises(ValueError):
        runner.run(ExperimentSpec("unknown", tmp_path, tmp_path/"u", metadata={"research_track":"UNKNOWN_PATTERN"}))
    assert calls == [1]


def _evaluation(effect=.10, raw_p=None):
    value = {"status": "evaluated", "effect_id": "effect", "coverage": .2,
        "unique_days": 20, "primary_effect_signed": effect,
        "primary_effect_absolute": abs(effect),
        "effect_metrics": {"primary_effect_signed": effect,
                           "primary_effect_absolute": abs(effect)},
        "target_family": "DIRECTIONAL", "multiplicity_family": "family",
        "fold_results": [{"effect": effect}, {"effect": effect}],
        "uncertainty": {"lower": effect / 2, "upper": effect * 1.5},
        "family_complete": False, "q_value": None, "fdr_status": "INCOMPLETE_FAMILY"}
    if raw_p is not None:
        value["raw_p"] = raw_p
    return value


def test_append_only_inference_and_cross_restart_family_finalization(tmp_path):
    first = cell()
    second = cell(feature_conditions=(("candle_range", "GE_P90"),))
    batch = PatternBatch((first, second))
    memory = ResearchMemory(tmp_path / "memory")
    for item in (first, second):
        memory.add_pattern_effect(PatternEffectRecord(
            item.pattern_cell_id, batch.pattern_batch_id, asdict(item),
            {k: v for k, v in _evaluation().items() if k not in {"raw_p", "uncertainty"}},
            PatternStatus.INFERENCE_PENDING, "experiment", 1))
    assert len(memory.completed_pattern_cell_ids()) == 2
    assert all(x.screening_status is PatternStatus.INFERENCE_PENDING
               for x in memory.pattern_effects().values())

    # Reopen between batches: inference is evidence, never a second discovery.
    memory = ResearchMemory(tmp_path / "memory")
    memory.enrich_pattern(first.pattern_cell_id,
        {"raw_p": .01, "uncertainty": _evaluation()["uncertainty"]},
        PatternStatus.INCOMPLETE_FAMILY, event="INFERENCE_ADDED")
    runner = PatternExperimentRunner(memory)
    assert runner.finalize_ready_families((first, second)) == ()
    assert memory.pattern_effects()[first.pattern_cell_id].screening_status is PatternStatus.INCOMPLETE_FAMILY

    memory = ResearchMemory(tmp_path / "memory")
    memory.enrich_pattern(second.pattern_cell_id,
        {"raw_p": .04, "uncertainty": _evaluation()["uncertainty"]},
        PatternStatus.INCOMPLETE_FAMILY, event="INFERENCE_ADDED")
    history_before = len(memory.pattern_effect_history())
    assert set(runner.__class__(memory).finalize_ready_families((first, second))) == {
        first.pattern_cell_id, second.pattern_cell_id}
    effective = memory.pattern_effects()
    assert all(r.screening_status is PatternStatus.PATTERN_SURVIVOR for r in effective.values())
    assert len(memory.pattern_effect_history()) == history_before + 2
    assert runner.__class__(memory).finalize_ready_families((first, second)) == ()
    assert len(memory.pattern_effect_history()) == history_before + 2
    assert len(memory.pattern_view(PatternRankingView.PATTERN_SURVIVORS)) == 2
    assert memory.view(RankingView.TOP_PF) == []


def test_complete_family_can_screen_out_without_a_q_cutoff():
    failing = _evaluation(effect=.01, raw_p=.9)
    finalized = finalize_multiplicity_family([failing], expected_family_size=1)
    assert finalized[0]["q_value"] == pytest.approx(.9)
    assert finalized[0]["screening_status"] == PatternStatus.SCREENED_OUT
    assert "practical_effect" in finalized[0]["screening_failures"]


def test_pending_inference_selection_is_deterministic_and_resumable(tmp_path):
    cells = (cell(), cell(feature_conditions=(("candle_range", "GE_P90"),)))
    memory = ResearchMemory(tmp_path / "memory")
    for item in cells:
        memory.add_pattern_effect(PatternEffectRecord(item.pattern_cell_id,
            PatternBatch((item,)).pattern_batch_id, asdict(item), _evaluation(),
            PatternStatus.INFERENCE_PENDING, "experiment", 1))
    expected = UnknownPatternScheduler(memory, tmp_path / "data", tmp_path / "out",
                                       search_space=cells).pending_inference_cells(2)
    reopened = UnknownPatternScheduler(ResearchMemory(tmp_path / "memory"),
        tmp_path / "other-data", tmp_path / "other-out", search_space=cells)
    assert reopened.pending_inference_cells(2) == expected
    ResearchMemory(tmp_path / "memory").enrich_pattern(expected[0].pattern_cell_id,
        {"raw_p": .2}, PatternStatus.INCOMPLETE_FAMILY, event="INFERENCE_ADDED")
    assert reopened.pending_inference_cells(2) == (expected[1],)


def test_memory_driven_pending_selection_matches_eager_legacy_oracle(tmp_path):
    cells = tuple(cell(feature_conditions=(("candle_range", value),))
                  for value in ("LE_P10", "MID", "GE_P90", "OTHER"))
    memory = ResearchMemory(tmp_path / "memory")

    def add(item, status, *, evaluation=None):
        memory.add_pattern_effect(PatternEffectRecord(
            item.pattern_cell_id, PatternBatch((item,)).pattern_batch_id,
            asdict(item), evaluation if evaluation is not None else _evaluation(),
            status, "experiment", 1))

    # Deliberately append in a different order from the frozen universe.
    add(cells[2], PatternStatus.INFERENCE_PENDING,
        evaluation={**_evaluation(), "inference_enabled": False})
    add(cells[0], PatternStatus.INELIGIBLE)
    add(cells[3], PatternStatus.INFERENCE_PENDING,
        evaluation={**_evaluation(), "inference_enabled": True})
    add(cells[1], PatternStatus.INCOMPLETE_FAMILY,
        evaluation={**_evaluation(), "raw_p": .2, "family_complete": True})

    def legacy(limit):
        effective = memory.pattern_effects()
        pending = [item for item in cells
                   if item.pattern_cell_id in effective
                   and effective[item.pattern_cell_id].screening_status
                   is PatternStatus.INFERENCE_PENDING
                   and "raw_p" not in effective[item.pattern_cell_id].evaluation]
        from market_pattern_discovery.contracts import deterministic_hash
        pending.sort(key=lambda item: deterministic_hash(
            {"seed": 20260401, "id": item.pattern_cell_id}))
        return tuple(pending[:limit])

    scheduler = UnknownPatternScheduler(
        memory, tmp_path / "data", tmp_path / "out", search_space=cells)
    assert scheduler.pending_inference_cells(0) == legacy(0) == ()
    assert scheduler.pending_inference_cells(1) == legacy(1)
    assert scheduler.pending_inference_cells(99) == legacy(99)
    assert scheduler.pending_inference_count() == len(legacy(len(cells))) == 2

    reopened = UnknownPatternScheduler(
        ResearchMemory(tmp_path / "memory"), tmp_path / "data2", tmp_path / "out2",
        search_space=cells)
    assert reopened.pending_inference_cells(99) == legacy(99)
    assert reopened.pending_inference_count() == 2


def test_pending_reconstructs_existing_memory_definition_without_universe_scan(
        tmp_path, monkeypatch):
    import market_pattern_discovery.orchestration.unknown as unknown
    target = {"column_name": "target", "family": "DIRECTIONAL",
              "semantic_role": "ROLE", "hypothesis_contrasts": ["a"]}
    matrix = DiscoveryMatrix("CNYRUBF", "M1", pd.DataFrame(), {},
                             {"f": ["x", "y"]}, [target], [])
    monkeypatch.setattr(unknown, "feature_inventory", lambda *a, **k: [{"feature": "f"}])
    lazy = PatternSearchSpace((matrix,), methods=("univariate_screen",))
    item = lazy[1]
    memory = ResearchMemory(tmp_path / "memory")
    memory.add_pattern_effect(PatternEffectRecord(
        item.pattern_cell_id, PatternBatch((item,)).pattern_batch_id, asdict(item),
        _evaluation(), PatternStatus.INFERENCE_PENDING, "experiment", 1))

    # Exercise the production reconstruction branch without requiring a
    # 17-million-cell release manifest for this representative space.
    scheduler = UnknownPatternScheduler(
        memory, tmp_path / "data", tmp_path / "out", search_space=(item,))
    scheduler.search_space = lazy
    scheduler.rank_index = object()
    assert scheduler.pending_inference_cells(1) == (item,)
    assert scheduler.pending_inference_count() == 1


def test_pending_hash_ties_retain_frozen_universe_order(tmp_path, monkeypatch):
    items = (cell(feature_conditions=(("candle_range", "FIRST"),)),
             cell(feature_conditions=(("candle_range", "SECOND"),)))
    memory = ResearchMemory(tmp_path / "memory")
    for item in reversed(items):
        memory.add_pattern_effect(PatternEffectRecord(
            item.pattern_cell_id, PatternBatch((item,)).pattern_batch_id, asdict(item),
            _evaluation(), PatternStatus.INFERENCE_PENDING, "experiment", 1))
    scheduler = UnknownPatternScheduler(
        memory, tmp_path / "data", tmp_path / "out", search_space=items)
    monkeypatch.setattr(
        "market_pattern_discovery.orchestration.unknown.deterministic_hash",
        lambda value: "tied-rank")
    assert scheduler.pending_inference_cells(2) == items


def test_absolute_roots_do_not_change_identity_batch_or_ranking(tmp_path):
    item = cell()
    results = []
    for root in (tmp_path / "temp_A", tmp_path / "temp_B"):
        memory = ResearchMemory(root / "memory")
        plan = UnknownPatternScheduler(memory, root / "data", root / "output",
            search_space=(item,)).plan(1, 1)
        memory.add_pattern_effect(PatternEffectRecord(item.pattern_cell_id,
            plan["pattern_batch"].pattern_batch_id, asdict(item), _evaluation(),
            PatternStatus.INFERENCE_PENDING, "experiment", 1))
        results.append((item.pattern_cell_id, plan["pattern_batch"].pattern_batch_id,
                        memory.pattern_view(PatternRankingView.TOP_EFFECT_MAGNITUDE)))
    assert results[0] == results[1]
    assert str(tmp_path) not in repr(results[0])
