"""Regression contract for v2 frozen-candidate Phase 4."""
from pathlib import Path
import json

import pandas as pd

from TradingSystemLab.audit_phase4_walk_forward_v2 import audit
from TradingSystemLab.walk_forward.phase4_v2 import (
    EXPECTED_IDS, FROZEN_TICK_SIZE, INSTRUMENTS, OUTPUT_ROOT, REGISTRY_PATH,
    ROBUSTNESS, SCHEDULE, STUDIES, classify,
)


def test_exact_frozen_candidates_include_borderline_t2_h1():
    registry = json.loads(REGISTRY_PATH.read_text())
    assert len(registry["candidates"]) == 4
    assert [(x["strategy"], x["timeframe"]) for x in registry["candidates"]] == list(STUDIES)
    assert {(x["candidate_id"], x["parameter_hash"]) for x in registry["candidates"]} == set(EXPECTED_IDS.values())
    assert ROBUSTNESS[("T2", "H1")] == "BORDERLINE"


def test_exact_expanding_four_quarter_schedule():
    assert len(SCHEDULE) == 4
    assert all(x[1] == "2020-01-01" for x in SCHEDULE)
    assert [x[3][:7] for x in SCHEDULE] == ["2024-01", "2024-04", "2024-07", "2024-10"]
    assert all(pd.Timestamp(x[4]) < pd.Timestamp("2025-01-01") for x in SCHEDULE)
    assert all(pd.Timestamp(SCHEDULE[n][4]) < pd.Timestamp(SCHEDULE[n+1][3]) for n in range(3))
    assert [x[2] for x in SCHEDULE] == sorted(x[2] for x in SCHEDULE)


def test_cost_universe_and_context_contract_in_committed_artifacts():
    manifest = json.loads((OUTPUT_ROOT / "summary/manifest.json").read_text())
    assert FROZEN_TICK_SIZE == .001 and manifest["C1_only"] is True
    assert tuple(manifest["instruments"]) == INSTRUMENTS
    assert not manifest["optimization"] and not manifest["ranking"] and not manifest["candidate_replacement"]
    assert manifest["true_oos_blocked"] and not manifest["true_oos_read"]
    coverage = json.loads((OUTPUT_ROOT / "DATA_COVERAGE_REPORT.json").read_text())
    assert coverage["timeframes"]["M30"]["CNY"]["actual_history_limitation"]
    for strategy, timeframe in STUDIES:
        metrics = json.loads((OUTPUT_ROOT / strategy / timeframe / "metrics.json").read_text())
        expected = "none" if strategy == "T2" else f"four completed non-overlapping {timeframe} bars; local-day reset"
        assert metrics["execution_context"] == expected
        folds = pd.read_csv(OUTPUT_ROOT / strategy / timeframe / "folds.csv")
        trades = pd.read_csv(OUTPUT_ROOT / strategy / timeframe / "trades.csv")
        assert folds.status.eq("COMPLETE").all() and trades.fold_start_state.eq("FLAT").all()
        assert pd.to_datetime(trades.entry_time, utc=True).dt.year.eq(2024).all()


def _base(**changes):
    value = {"trades": 50, "expectancy": .1}
    value.update(changes); return value


def test_exact_verdict_gates_and_no_extra_gates():
    positive = [.1] * 6
    assert classify(_base(), .75, .7, positive, 4) == "WALK_FORWARD_PASS"
    assert classify(_base(trades=49), .75, .7, positive, 4) == "WALK_FORWARD_BORDERLINE"
    assert classify(_base(expectancy=0), .75, .7, positive, 4) == "WALK_FORWARD_BORDERLINE"
    assert classify(_base(), .5, .7, positive, 4) == "WALK_FORWARD_BORDERLINE"
    assert classify(_base(), .75, .70001, positive, 4) == "WALK_FORWARD_BORDERLINE"
    assert classify(_base(), .75, None, positive, 4) == "WALK_FORWARD_PASS"
    assert classify(_base(), .75, .7, [None, 0, .1, .1, .1, .1], 4) == "WALK_FORWARD_PASS"
    assert classify(_base(), .75, .7, [-.01] + positive[1:], 4) == "WALK_FORWARD_BORDERLINE"
    assert classify(_base(expectancy=-.001), .75, .7, positive, 4) == "WALK_FORWARD_FAIL"
    assert classify(_base(), .25, .7, positive, 4) == "WALK_FORWARD_FAIL"


def test_independent_audit_recomputes_committed_verdicts():
    assert audit()["status"] == "PHASE_4_WALK_FORWARD_AUDIT_PASSED"
