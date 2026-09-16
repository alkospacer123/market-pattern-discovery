from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.multitimeframe.phase73 import hash_tree
from TradingSystemLab.optimization.phase82 import RANGES, run as run82
from TradingSystemLab.robustness.phase83 import run as run83
from TradingSystemLab.walk_forward.phase84 import (FOLDS, reject_forbidden_timestamps,
                                                    run, validate_fold_causality)


def _trades(key: str, config: dict, alias: str, frame: pd.DataFrame) -> pd.DataFrame:
    times = frame.index[::max(1, len(frame) // 8)][:8]
    gross = [1.0 if n % 3 else -.4 for n in range(len(times))]
    return pd.DataFrame({"trade_id": [f"temporary-{n}" for n in range(len(times))],
        "entry_time": times, "exit_time": times + pd.Timedelta("1min"), "gross_R": gross,
        "initial_risk_ticks": [100.] * len(times), "net_R": [x - .01 for x in gross],
        "MAE_R": [-.2] * len(times), "MFE_R": [.8] * len(times),
        "instrument": ["USDRUBF" if alias == "Si" else "CNYRUBF"] * len(times),
        "direction": ["LONG" if n % 2 else "SHORT" for n in range(len(times))]})


@pytest.fixture
def phase_inputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import TradingSystemLab.optimization.phase82 as phase82
    import TradingSystemLab.robustness.phase83 as phase83
    import TradingSystemLab.walk_forward.phase84 as phase84
    index = pd.date_range("2023-01-01", "2024-12-31 23:00", freq="12h", tz="UTC")
    frames = {alias: pd.DataFrame({"Close": range(len(index))}, index=index) for _, alias in phase84.INSTRUMENTS}
    loader = lambda root, alias: (frames[alias], [])
    monkeypatch.setattr(phase82, "load_m1_development", loader)
    monkeypatch.setattr(phase82, "_execute", _trades)
    root82 = tmp_path / "phase82"; run82(output=root82)
    monkeypatch.setattr(phase83, "load_m1_development", loader)
    monkeypatch.setattr(phase83, "_execute", _trades)
    root83 = tmp_path / "phase83"; run83(output=root83, phase82_root=root82)
    monkeypatch.setattr(phase84, "load_m1_development", loader)
    monkeypatch.setattr(phase84, "_execute", _trades)
    return root82, root83, tmp_path / "phase84"


def test_folds_are_causal_and_true_oos_is_rejected() -> None:
    validate_fold_causality()
    for _, train_start, train_end, test_start, test_end in FOLDS:
        assert train_start == "2023-01-01"
        assert pd.Timestamp(train_end) == pd.Timestamp(test_start)
        assert pd.Timestamp(test_start) < pd.Timestamp(test_end)
    with pytest.raises(ValueError, match="TRUE_OOS_BARRIER_VIOLATION"):
        reject_forbidden_timestamps(pd.DataFrame({"entry_time": ["2025-01-01T00:00:00Z"]}))


def test_determinism_flat_initialization_and_protection(phase_inputs) -> None:
    root82, root83, output = phase_inputs
    protected = (hash_tree(root82), hash_tree(root83))
    first = run(output=output, phase83_root=root83, phase82_root=root82)
    hashes = {str(p.relative_to(output)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in output.rglob("*") if p.is_file()}
    second = run(output=output, phase83_root=root83, phase82_root=root82)
    assert first == second
    assert hashes == {str(p.relative_to(output)): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in output.rglob("*") if p.is_file()}
    assert protected == (hash_tree(root82), hash_tree(root83))
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["flat_initialization_per_fold"] is True
    assert manifest["optimization"] is manifest["ranking"] is False
    assert manifest["true_oos_blocked"] is manifest["deterministic"] is True
    for key in ("T2", "T3"):
        report = pd.read_csv(output / key / "fold_report.csv")
        assert set(report.initial_state) == {"FLAT"}
        assert list(report.split) == ["train", "test"] * 4
        trades = pd.read_csv(output / key / "trades.csv")
        assert trades.trade_id.is_unique
        assert trades.trade_id.str.contains(r"-WF0[1-4]-test-").all()


def test_frozen_candidate_tampering_fails_closed(phase_inputs) -> None:
    root82, root83, output = phase_inputs
    registry_path = root82 / "T2" / "candidate_registry.json"
    registry = json.loads(registry_path.read_text())
    registry["parameters"][next(iter(RANGES["T2"]))] = "tampered"
    registry_path.write_text(json.dumps(registry))
    with pytest.raises(RuntimeError, match="CANDIDATE_HASH_MISMATCH"):
        run(output=output, phase83_root=root83, phase82_root=root82)


def test_no_optimization_interface() -> None:
    import TradingSystemLab.walk_forward.phase84 as phase84
    assert not hasattr(phase84, "optimize")
    source = Path(phase84.__file__).read_text(encoding="utf-8")
    assert "RANGES" not in source and "optimization_results" not in source
