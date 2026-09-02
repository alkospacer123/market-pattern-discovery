from dataclasses import replace

import pandas as pd
import pytest

from market_pattern_discovery.research.memory import (
    CandidateRecord, CandidateStatus, PatternEffectRecord, PatternStatus,
    RankingView, ResearchMemory,
)
from market_pattern_discovery.strategy_synthesis import (
    ACTIVATION_RULE, PatternStrategySpec, assess_exit_surface, exit_neighbours,
    map_direction, synthesize_pattern,
    execution_cell_id, persisted_exit_evidence,
)


def survivor(status=PatternStatus.PATTERN_SURVIVOR, **changes):
    definition = {"instrument":"CNYRUBF", "timeframe":"M1", "feature_conditions":[["candle_direction","1"]],
                  "target_family":"DIRECTIONAL", "target_role":"SHORT_SIGNED_DISPLACEMENT",
                  "target_type":"continuous", "contrast":"median_difference", "contract_signatures":{"feature":"abc"}}
    definition.update(changes)
    return PatternEffectRecord("p1", "b1", definition, {"primary_effect_signed":1.0}, status, "e1", 1)


@pytest.mark.parametrize("status", [PatternStatus.INELIGIBLE, PatternStatus.INFERENCE_PENDING,
    PatternStatus.INCOMPLETE_FAMILY, PatternStatus.SCREENED_OUT])
def test_only_survivor_is_synthesized(status):
    with pytest.raises(ValueError, match="requires PATTERN_SURVIVOR"):
        synthesize_pattern(survivor(status))


@pytest.mark.parametrize("family,target_type,contrast,effect,expected", [
    ("DIRECTIONAL","continuous","median_difference",1,"LONG"),
    ("DIRECTIONAL","continuous","median_difference",-1,"SHORT"),
    ("DIRECTIONAL","multiclass","P(+1 | feature_state) - P(+1 | baseline)",-1,"SHORT"),
    ("DIRECTIONAL","multiclass","P(-1 | feature_state) - P(-1 | baseline)",1,"SHORT"),
    ("FIRST_PASSAGE","multiclass","P(+1 upper-first | feature_state) - P(+1 upper-first | baseline)",1,"LONG"),
    ("FIRST_PASSAGE","multiclass","P(-1 lower-first | feature_state) - P(-1 lower-first | baseline)",-1,"LONG"),
])
def test_exact_direction_whitelist(family,target_type,contrast,effect,expected):
    assert map_direction(family,target_type,contrast,effect).direction == expected


def test_nondirectional_and_zero_rejected():
    assert not map_direction("VOLATILITY","continuous","median_difference",1).actionable
    assert not map_direction("DIRECTIONAL","continuous","median_difference",0).actionable


def test_strategy_identity_is_semantic_not_runtime():
    spec, _ = synthesize_pattern(survivor())
    assert spec is not None
    assert spec.pattern_strategy_id == PatternStrategySpec.from_dict(spec.to_dict()).pattern_strategy_id
    changed = replace(spec, feature_conditions=(("candle_direction","-1"),))
    assert changed.pattern_strategy_id != spec.pattern_strategy_id
    assert "cycle" not in spec.to_dict() and "data_root" not in spec.to_dict()


def test_neighbours_and_plateau_gate_are_deterministic():
    assert exit_neighbours("TIME_30") == ("TIME_15", "TIME_60")
    assert set(exit_neighbours("STOP_0.5_TARGET_1.5")) == {"STOP_0.5_TARGET_1.0", "STOP_0.5_TARGET_2.0", "STOP_1.0_TARGET_1.5"}
    good = {"BASE":{"trades":30,"profit_factor":2.1,"expectancy":.1},
            "STRESS":{"profit_factor":1.6,"expectancy":.01}, "unique_trading_days":15,
            "positive_calendar_blocks":3,"largest_winner_share":.2}
    neighbour = {"BASE":{"trades":30,"profit_factor":1.3,"expectancy":.01}, "STRESS":{}}
    isolated = assess_exit_surface({"TIME_30":good})["TIME_30"]
    assert not isolated["trading_survivor"]
    plateau = assess_exit_surface({"TIME_30":good,"TIME_15":neighbour,"TIME_60":neighbour})["TIME_30"]
    assert plateau["trading_survivor"] and plateau["candidate_status"] == "GENERATED"


def test_signal_module_has_no_future_target_dependency():
    import inspect, market_pattern_discovery.strategy_synthesis as module
    source = inspect.getsource(module)
    assert "build_behaviors" not in source
    assert "load_discovery_matrix" not in source
    assert "targets.behavior" not in source


def test_persisted_v3_atr_evidence_and_assessment_view(tmp_path):
    root = tmp_path / "v3"; root.mkdir()
    pd.DataFrame([
        {"strategy_id":"s", "instrument":"CNYRUBF", "exit_configuration":"TIME_30",
         "friction_scenario":"BASE", "trades":30, "profit_factor_ATR":2.1,
         "expectancy_ATR":.1, "max_drawdown_ATR":.5, "recovery_factor_ATR":3.0},
        {"strategy_id":"s", "instrument":"CNYRUBF", "exit_configuration":"TIME_30",
         "friction_scenario":"STRESS", "trades":30, "profit_factor_ATR":1.6,
         "expectancy_ATR":.01, "max_drawdown_ATR":.8, "recovery_factor_ATR":1.0},
    ]).to_csv(root / "strategy_summary.csv", index=False)
    pd.DataFrame([{"exit_configuration":"TIME_30", "friction_scenario":"BASE",
                   "expectancy_ATR":x} for x in (.1,.2,.3)]).to_csv(root / "monthly_summary.csv", index=False)
    pd.DataFrame([{"exit_configuration":"TIME_30", "friction_scenario":"BASE",
                   "entry_time":f"2026-01-{i:02d}T08:00:00Z", "pnl_atr":1.0}
                  for i in range(1,16)]).to_csv(root / "trade_ledger.csv", index=False)
    evidence = persisted_exit_evidence(root, "TIME_30")
    assert evidence["BASE"] == {"trades":30, "profit_factor":2.1, "expectancy":.1,
                                 "max_drawdown":.5, "recovery":3.0}
    assert evidence["STRESS"] == {"profit_factor":1.6, "expectancy":.01}
    assert evidence["unique_trading_days"] == 15 and evidence["positive_calendar_blocks"] == 3

    memory = ResearchMemory(tmp_path / "memory")
    cell = "cell"
    siblings = []
    for friction in ("GROSS", "BASE", "STRESS"):
        candidate = CandidateRecord(f"c-{friction}", "s", "CNYRUBF", "M1",
            {"pattern_strategy_id":"ps", "execution_search_cell_id":cell,
             "friction_scenario":friction}, f"e-{friction}", 1)
        memory.add_candidate(candidate)
        memory.record_evaluation(f"e-{friction}", candidate.candidate_id,
            {"profit_factor":2.1, "expectancy":.1, "robustness":3.0})
        siblings.append(candidate)
    memory.record_synthesis_assessment({"pattern_strategy_id":"ps", "source_pattern_cell_id":"p",
        "execution_search_cell_id":cell, "exit_configuration":"TIME_30",
        "assessment_complete":True, "trading_survivor":True})
    assert [c.candidate_id for c in memory.view(RankingView.TRADING_SURVIVORS)] == ["c-BASE"]
    assert memory.view(RankingView.TRADING_SURVIVORS)[0].status is CandidateStatus.GENERATED
    assert [c.candidate_id for c in memory.view(RankingView.TOP_RECOVERY)] == ["c-BASE"]


def test_synthesis_rankings_exclude_known_candidates_and_legacy_views_do_not(tmp_path):
    memory = ResearchMemory(tmp_path)
    for identifier, pattern in (("known", None), ("synth", "ps")):
        candidate = CandidateRecord(identifier, identifier, "CNYRUBF", "M1",
            {"pattern_strategy_id":pattern, "friction_scenario":"BASE"}, identifier + "-eval", 1)
        memory.add_candidate(candidate)
        memory.record_evaluation(identifier + "-eval", identifier,
            {"profit_factor":9 if identifier == "known" else 2, "expectancy":1,
             "robustness":3})
    for view in (RankingView.TOP_BASE_PF, RankingView.TOP_BASE_EXPECTANCY, RankingView.TOP_RECOVERY):
        assert [c.candidate_id for c in memory.view(view)] == ["synth"]
    assert [c.candidate_id for c in memory.view(RankingView.TOP_PF)] == ["known", "synth"]
    assert {c.candidate_id for c in memory.view(RankingView.TOP_EXPECTANCY)} == {"known", "synth"}
    assert {c.candidate_id for c in memory.view(RankingView.TOP_ROBUST)} == {"known", "synth"}
