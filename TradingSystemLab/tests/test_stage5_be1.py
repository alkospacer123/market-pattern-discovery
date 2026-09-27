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
