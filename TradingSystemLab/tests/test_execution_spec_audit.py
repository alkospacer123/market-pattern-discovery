import hashlib
from pathlib import Path

from TradingSystemLab.core.instrument_specs import get_instrument_spec
from TradingSystemLab.run_execution_spec_audit import FROZEN_TREE_HASHES, RESULTS, run, tree_hash


def test_instrument_execution_and_data_units_are_distinct():
    for symbol in ("USDRUBF", "CNYRUBF"):
        spec = get_instrument_spec(symbol)
        assert spec.tick_size == 0.01
        assert spec.price_precision == 0.001
        assert spec.lot_size == 1000


def test_frozen_r3_round_level_steps_are_unchanged():
    assert get_instrument_spec("Si").round_level_step == 0.10
    assert get_instrument_spec("CNY").round_level_step == 0.05


def test_frozen_phase_1_to_6_artifact_hashes_are_unchanged():
    assert {name: tree_hash(RESULTS / name) for name in FROZEN_TREE_HASHES} == FROZEN_TREE_HASHES


def test_audit_is_deterministic_and_does_not_mutate_phase_5_or_6(tmp_path):
    protected = {name: tree_hash(RESULTS / name)
                 for name in ("true_oos_validation", "portfolio_construction")}
    output = tmp_path / "audit"
    run(output)
    first = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir()}
    run(output)
    second = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir()}
    assert first == second
    assert protected == {name: tree_hash(RESULTS / name) for name in protected}
