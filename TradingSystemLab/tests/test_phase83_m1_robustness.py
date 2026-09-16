from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.multitimeframe.phase73 import hash_tree
from TradingSystemLab.optimization.phase82 import RANGES, run as run82
from TradingSystemLab.robustness.phase83 import ITERATIONS, bootstrap, reject_forbidden_timestamps, run


def _trades(key: str, config: dict, alias: str, frame: pd.DataFrame) -> pd.DataFrame:
    offset = sum(RANGES[key][name].index(config[name]) for name in RANGES[key]) * .001
    times = pd.date_range("2023-01-02 10:00", periods=40, freq="15D", tz="UTC")
    gross = ([1.0 + offset, -.3, .5, -.2] * 10)
    risk = [100.0] * 40
    return pd.DataFrame({"trade_id": [f"{key}-{alias}-{n}" for n in range(40)],
        "entry_time": times, "exit_time": times + pd.Timedelta("5min"), "gross_R": gross,
        "initial_risk_ticks": risk, "net_R": [value - .01 for value in gross],
        "MAE_R": [-.2] * 40, "MFE_R": [.8] * 40,
        "instrument": ["USDRUBF" if alias == "Si" else "CNYRUBF"] * 40,
        "direction": (["LONG", "SHORT"] * 20)})


@pytest.fixture
def phase_inputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import TradingSystemLab.optimization.phase82 as phase82
    import TradingSystemLab.robustness.phase83 as phase83
    loader = lambda *args: (pd.DataFrame({"Close": [1]}), [])
    monkeypatch.setattr(phase82, "load_m1_development", loader)
    monkeypatch.setattr(phase82, "_execute", _trades)
    root = tmp_path / "phase82"; run82(output=root)
    monkeypatch.setattr(phase83, "load_m1_development", loader)
    monkeypatch.setattr(phase83, "_execute", _trades)
    return root, tmp_path / "robustness"


def test_bootstrap_determinism_and_true_oos_barrier() -> None:
    values = pd.Series([-.5, .25, 1.0])
    assert bootstrap(values) == bootstrap(values)
    assert bootstrap(values)["iterations"] == ITERATIONS == 10_000
    with pytest.raises(ValueError, match="TRUE_OOS_BARRIER_VIOLATION"):
        reject_forbidden_timestamps(pd.DataFrame({"entry_time": ["2025-01-01T00:00Z"]}))


def test_artifact_determinism_provenance_and_protection(phase_inputs) -> None:
    root, output = phase_inputs
    before = hash_tree(root)
    first = run(output=output, phase82_root=root)
    hashes = {str(path.relative_to(output)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in output.rglob("*") if path.is_file()}
    second = run(output=output, phase82_root=root)
    assert first == second
    assert hashes == {str(path.relative_to(output)): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in output.rglob("*") if path.is_file()}
    assert before == hash_tree(root)
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["optimization"] is manifest["ranking"] is manifest["walk_forward"] is False
    assert manifest["true_oos_blocked"] is True
    assert set(manifest["parameter_hashes"]) == {"T2", "T3"}


def test_candidate_tampering_fails_closed(phase_inputs) -> None:
    root, output = phase_inputs
    path = root / "T2" / "candidate_registry.json"
    registry = json.loads(path.read_text()); registry["parameters"]["ema_fast"] = 999
    path.write_text(json.dumps(registry))
    with pytest.raises(RuntimeError, match="CANDIDATE_HASH_MISMATCH"):
        run(output=output, phase82_root=root)


def test_no_optimizer_interface_exposed() -> None:
    import TradingSystemLab.robustness.phase83 as phase83
    assert not hasattr(phase83, "optimize")
    source = Path(phase83.__file__).read_text(encoding="utf-8")
    assert "walk_forward import" not in source and "true_oos import" not in source
