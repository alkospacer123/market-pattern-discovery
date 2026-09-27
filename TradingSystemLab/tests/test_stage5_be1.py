from pathlib import Path
import importlib.util
import sys
import pytest

BASE = Path(__file__).parents[1] / "results/post_v3_analysis/stage5_structural_validation"


def load(name):
    spec = importlib.util.spec_from_file_location(name, BASE / f"{name}.py")
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


be = load("stage5_be1_execution")
audit = load("audit_stage5_be1")
lifecycle = load("stage5_be1_lifecycle")


@pytest.mark.parametrize("direction,entry,stop,high,low", [
    ("LONG", 100, 98, 102, 99), ("SHORT", 100, 102, 101, 98),
])
def test_exact_one_r_and_next_event(direction, entry, stop, high, low):
    state = be.BE1State(direction, entry, stop)
    assert state.observe_completed_bar("t1", high, low)
    assert state.activate_before_event("t1", stop) == stop  # never same-bar
    assert state.activate_before_event("t2", stop) == entry


def test_below_threshold_and_frozen_initial_r():
    state = be.BE1State("LONG", 100, 98)
    assert not state.observe_completed_bar("t1", 101.999999, 99)
    # A moved canonical stop does not redefine the frozen trigger.
    assert state.trigger_price == 102


def test_same_bar_retracement_is_not_retroactive():
    state = be.BE1State("LONG", 100, 98)
    state.observe_completed_bar("t1", 103, 99)
    assert not state.activated
    assert state.activate_before_event("t1", 98) == 98


@pytest.mark.parametrize("direction,stop", [("LONG", 101), ("SHORT", 99)])
def test_existing_tighter_stop_never_loosened(direction, stop):
    state = be.BE1State(direction, 100, 98 if direction == "LONG" else 102)
    state.observe_completed_bar("t1", 102 if direction == "LONG" else 101,
                                99 if direction == "LONG" else 98)
    assert state.activate_before_event("t2", stop) == stop
    assert state.canonical_stop_already_tighter


def test_gap_through_uses_canonical_fill():
    state = be.BE1State("LONG", 100, 98)
    state.observe_completed_bar("t1", 102, 100)
    stop = state.activate_before_event("t2", 98)
    assert state.stop_fill(97, stop) == 97
    assert state.gap_through_be_level


def test_tighter_trail_touch_is_not_automatically_be_level_touch():
    state = be.BE1State("LONG", 100, 98)
    state.observe_completed_bar("t1", 102, 100)
    state.activate_before_event("t2", 98)
    # The canonical trail has tightened beyond entry.  A bar can touch that
    # stop without ever trading at the distinct BE level.
    assert state.stop_fill(102, 101, bar_low=100.5, bar_high=103) == 101
    fields = state.event_fields()
    assert fields["protective_stop_touched_after_be"]
    assert not fields["be_level_touched"]
    assert fields["exit_protection_source"] == "CANONICAL_TRAIL_AFTER_BE"


def test_independent_diagnostic_classification_agrees():
    state = audit.IndependentBE1("SHORT", 100, 102)
    state.observe("t1", 100, 98)
    assert state.activate("t2", 102) == 100
    assert state.fill(98, 99, low=97, high=99.5) == 99
    assert state.protective_stop_touched_after_be
    assert not state.be_level_touched
    assert state.exit_protection_source == "CANONICAL_TRAIL_AFTER_BE"


def test_exit_on_trigger_bar_cannot_fabricate_activation():
    state = be.BE1State("LONG", 100, 98)
    # Canonical exit processing happens before observe_completed_bar, so an
    # exited position has no call to observe and cannot acquire BE state.
    assert not state.triggered and not state.activated


def test_fold_boundary_constructs_fresh_flat_state():
    old = be.BE1State("LONG", 100, 98); old.observe_completed_bar("t1", 102, 99)
    new = be.BE1State("LONG", 110, 108)
    assert old.triggered and not new.triggered and not new.activated


def test_independent_implementation_reconciles_contract():
    producer = be.BE1State("SHORT", 100, 102)
    independent = audit.IndependentBE1("SHORT", 100, 102)
    producer.observe_completed_bar("a", 101, 98); independent.observe("a", 101, 98)
    assert producer.activate_before_event("b", 102) == independent.activate("b", 102) == 100
    assert producer.stop_fill(103, 100) == independent.fill(103, 100) == 103


def test_invalid_initial_risk_rejected():
    with pytest.raises(ValueError, match="BE1_INITIAL_RISK_NOT_POSITIVE"):
        be.BE1State("LONG", 100, 100)


def test_be_disabled_state_is_inert_for_both_execution_loops():
    for direction, stop, high, low in (("LONG", 98, 110, 90), ("SHORT", 102, 110, 90)):
        state = be.BE1State(direction, 100, stop, enabled=False)
        assert not state.observe_completed_bar("bar", high, low)
        assert state.activate_before_event("next", stop) == stop


def test_independent_auditor_has_no_producer_imports():
    source = (BASE / "audit_stage5_be1.py").read_text()
    for forbidden in ("run_stage5_be1", "stage5_be1_lifecycle", "stage5_be1_execution"):
        assert forbidden not in source


def test_executable_mutations_really_reject_and_match_guards():
    rows = audit.executable_mutations()
    assert len(rows) == 30
    assert all(row["rejected"] and row["pass"] for row in rows)
    bad = dict(audit.CLEAN); bad["trigger_r"] = .5
    with pytest.raises(ValueError, match="TRIGGER_NOT_1R_LOW"):
        audit.validate_contract(bad)


def test_independent_source_and_registry_authentication():
    root = Path("/workspace/market-pattern-data")
    if not root.is_dir():
        pytest.skip("frozen read-only data checkout unavailable")
    authenticated = audit.authenticate_prerequisites(root)
    assert len(authenticated["source_hashes"]) == 20
    assert len(authenticated["lifecycle_registry_sha256"]) == 64


def test_real_event_corruption_hits_reconciliation():
    row = _trade("2024-01-01", "2024-01-02")
    row.update(initial_stop_price=98., initial_risk_price=2., trigger_price=102.,
               be_triggered=True, trigger_bar_time="2024-01-01T01:00:00Z",
               trigger_bar_high=103., trigger_bar_low=99.,
               be_activation_time="2024-01-01T02:00:00Z",
               protective_stop_before_activation=98.,
               protective_stop_after_activation=100.,
               canonical_stop_already_tighter=False,
               exit_protection_source="BE_LEVEL", gap_through_be_level=False)
    import pandas as pd
    clean = pd.DataFrame([row])
    rows = audit.executable_mutations(clean, clean)
    assert all(r["pass"] for r in rows)
    assert all(r["validation_surface"] == "producer_auditor_reconciliation"
               for r in rows[-4:])


def _trade(entry, exit_, exit_price=101):
    return {"generation":"v2_quarterly","lifecycle":"baseline","fold_id":"",
            "strategy":"T2","timeframe":"H1","instrument":"X","direction":"LONG",
            "entry_time":entry,"entry_price":100.,"exit_time":exit_,
            "exit_price":exit_price,"exit_reason":"ATR_TRAILING_STOP","net_R_C1":.4}


def test_path_divergence_detects_changed_exit():
    import pandas as pd
    canonical = pd.DataFrame([_trade("2024-01-01", "2024-01-02")])
    changed = pd.DataFrame([_trade("2024-01-01", "2024-01-03")])
    row = lifecycle.path_divergences(canonical, changed)[0]
    assert row["divergence_reason"] == "EXIT_CHANGED_BY_BE1"
    assert row["exact_paired_prefix_trades"] == 0


def test_path_divergence_detects_inserted_trade_without_forced_pairing():
    import pandas as pd
    canonical = pd.DataFrame([_trade("2024-01-01", "2024-01-02")])
    inserted = pd.DataFrame([_trade("2024-01-01", "2024-01-02"),
                             _trade("2024-02-01", "2024-02-02")])
    row = lifecycle.path_divergences(canonical, inserted)[0]
    assert row["divergence_reason"] == "EXTRA_OR_MISSING_TRADE"
    assert row["exact_paired_prefix_trades"] == 1


def test_deterministic_json_serialization(tmp_path):
    left, right = tmp_path / "a.json", tmp_path / "b.json"
    lifecycle._json(left, {"z": 1, "a": [2, 3]})
    lifecycle._json(right, {"a": [2, 3], "z": 1})
    assert left.read_bytes() == right.read_bytes()
