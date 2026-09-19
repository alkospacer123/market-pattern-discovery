"""Contract tests for standalone H4 Phase 4 walk-forward validation."""
from __future__ import annotations

import ast
import json
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.walk_forward import h4

ROOT = Path("TradingSystemLab/results/walk_forward/H4")


def test_standalone_methodology_and_frozen_candidates():
    imports=" ".join(ast.unparse(node) for node in ast.walk(ast.parse(Path(h4.__file__).read_text()))
                     if isinstance(node,(ast.Import,ast.ImportFrom))).lower()
    assert h4.METHODOLOGICAL_SOURCE == "H1_PHASE_4"
    assert "timeframe_validation import h4_baseline" in imports
    assert not any(f"walk_forward.{name}" in imports for name in ("m30","m15","m5","phase84"))
    assert h4.FROZEN["T2"]["candidate_id"] == "T2_H4_candidate_v1"
    assert h4.FROZEN["T3"]["candidate_id"] == "T3_H4_candidate_v1"
    assert h4.FROZEN["T2"]["configuration_id"] == "T2-H4-0008-2b0494cdd24b"
    assert h4.FROZEN["T3"]["configuration_id"] == "T3-H4-0003-9b1e60957d91"
    assert not any(hasattr(h4,name) for name in ("optimize","search","rank_candidates","fallback_candidate"))


def test_exact_schedule_is_expanding_sequential_and_pre_oos():
    assert len(h4.SCHEDULE) == 4
    assert [row[0] for row in h4.SCHEDULE] == ["WF01","WF02","WF03","WF04"]
    assert {row[1] for row in h4.SCHEDULE} == {"2023-01-01"}
    for previous,current in zip(h4.SCHEDULE,h4.SCHEDULE[1:]):
        assert pd.Timestamp(previous[4])+pd.Timedelta(seconds=1) == pd.Timestamp(current[3])
        assert pd.Timestamp(previous[2]) < pd.Timestamp(current[2])
    assert all(pd.Timestamp(row[4]) < pd.Timestamp("2025-01-01") for row in h4.SCHEDULE)


def test_provenance_and_actual_sources_are_exact():
    provenance,candidates=h4.verify_provenance()
    _,sources=h4.load_verified_development(h4.APPROVED_DATA_ROOT,provenance)
    assert sources == provenance["baseline"]["source_files"]
    assert sources == provenance["optimization"]["source_files"]
    assert sources == provenance["robustness"]["verified_source_files"]
    assert provenance["robustness"]["classifications"] == {"T2":"BORDERLINE","T3":"BORDERLINE"}
    assert all(candidates[k]["selection_locked_before_validation"] for k in candidates)


@pytest.mark.parametrize("failure",["changed","missing"])
def test_changed_or_missing_source_fails_closed(monkeypatch,tmp_path,failure):
    source=tmp_path/"Si_H1_2023_Q1.csv"; source.write_text("bytes")
    paths=[] if failure=="missing" else [source]
    expected=[{"instrument":"USDRUBF","alias":"Si","name":source.name,"sha256":"0"*64}]
    monkeypatch.setattr(h4.baseline,"INSTRUMENTS",(("USDRUBF","Si"),))
    monkeypatch.setattr(h4.baseline,"load_h1_development",lambda *_:(pd.DataFrame({"close":[1]}),paths))
    provenance={"baseline":{"source_files":expected},"optimization":{"source_files":expected},
                "robustness":{"verified_source_files":expected}}
    with pytest.raises(RuntimeError,match="H4_WALK_FORWARD_SOURCE_HASH_MISMATCH"):
        h4.load_verified_development(tmp_path,provenance)


def test_exact_verdict_boundaries():
    metric={"trades":50,"expectancy_C1":.1}
    assert h4.classify(metric,.75,4,.70,[0,.1]) == "WALK_FORWARD_PASS"
    assert h4.classify({**metric,"expectancy_C1":-.01},1,4,.1,[1,1]) == "WALK_FORWARD_FAIL"
    assert h4.classify(metric,.25,4,.1,[1,1]) == "WALK_FORWARD_FAIL"
    assert h4.classify({**metric,"trades":49},.75,4,.1,[1,1]) == "WALK_FORWARD_BORDERLINE"


def test_artifact_contract_c1_containment_state_and_determinism():
    manifest=json.loads((ROOT/"manifest.json").read_text())
    assert manifest["phase"] == "H4_WALK_FORWARD"
    assert manifest["status"] == "PHASE_H4_WALK_FORWARD_BORDERLINE"
    assert manifest["cost_scenarios"] == ["C1"] and manifest["true_oos_read"] is False
    assert not manifest["optimization"] and not manifest["ranking"] and not manifest["candidate_selection"]
    for key in ("T2","T3"):
        target=ROOT/key
        required=("folds.csv","trades.csv","train_test_decay.csv","instrument_report.csv","direction_report.csv",
                  "year_report.csv","concentration.csv","leave_one_fold_out.csv","mae_mfe.csv","metrics.json","final_report.md")
        assert all((target/name).is_file() for name in required)
        folds=pd.read_csv(target/"folds.csv"); trades=pd.read_csv(target/"trades.csv")
        assert (folds.fold_start_state == "FLAT").all() and len(folds)==4
        assert trades.trade_id.is_unique and trades.trade_id.tolist()==trades.sort_values(
            ["exit_time","instrument","fold","trade_id"],kind="mergesort").trade_id.tolist()
        for row in h4.SCHEDULE:
            selected=trades.loc[trades.fold.eq(row[0])]
            assert (pd.to_datetime(selected.entry_time,utc=True)>=pd.Timestamp(row[3],tz="UTC")).all()
            assert (pd.to_datetime(selected.exit_time,utc=True)<=pd.Timestamp(row[4],tz="UTC")).all()
        text=" ".join(path.read_text() for path in target.iterdir() if path.suffix in (".csv",".json",".md"))
        assert not any(token in text for token in ("C0","C0.5","C2"))


def test_strategy_hashes_and_protected_artifacts_remain_frozen():
    manifest=json.loads((ROOT/"manifest.json").read_text())
    assert manifest["strategy_hashes"] == h4.STRATEGY_SHA256
    assert manifest["protected_artifact_hashes"] == h4.protected_snapshot()
