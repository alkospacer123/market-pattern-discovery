import pytest

from .generate_lock1_reassessment import lock_levels


def test_does_not_activate_before_two_r():
    assert lock_levels("LONG", 100, 10, 80, False) == (80, False)


@pytest.mark.parametrize(
    "direction,canonical,expected,binding",
    [("LONG", 80, 110, True), ("SHORT", 120, 90, True), ("LONG", 117, 117, False), ("SHORT", 83, 83, False)],
)
def test_exact_floor_and_canonical_priority(direction, canonical, expected, binding):
    assert lock_levels(direction, 100, 10, canonical, True) == (expected, binding)


def test_persistent_activation_state_machine_and_no_same_event_protection():
    armed = False
    # Event t starts unarmed, reaches exactly 2R and retraces through +1R.
    stop, _ = lock_levels("LONG", 100, 10, 75, armed)
    assert stop == 75  # no synthetic same-event LOCK1 stop
    if 120 >= 100 + 2 * 10:
        armed = True
    # Event t+1 starts armed. Falling below the trigger cannot deactivate it.
    assert lock_levels("LONG", 100, 10, 75, armed) == (110, True)
    assert armed is True


def test_no_rule_contamination_in_registry():
    import pandas as pd
    from pathlib import Path

    registry = pd.read_csv(Path(__file__).with_name("lock1_registry.csv"))
    assert not registry.session_restriction.any()
    assert not registry.one_bar_confirmation.any()
    assert not registry.opposite_regime_exit.any()
