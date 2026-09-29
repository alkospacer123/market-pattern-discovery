"""Independent, fail-closed audit of the committed Stage 6.4 evidence."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import generate_lock1_reassessment as gen


HERE = Path(__file__).resolve().parent


def audit(directory: Path = HERE) -> dict:
    manifest = json.loads((directory / "audit_manifest.json").read_text())
    checks: dict[str, bool] = {}
    checks["strategy_hash"] = gen.sha(gen.ROOT / "TradingSystemLab/strategies/trend/T3_MTF_Trend.py") == gen.T3_SHA
    checks["parameter_hash"] = manifest["parameter_sha"] == gen.PARAM_SHA
    checks["c1_tick"] = bool((pd.read_csv(directory / "lock1_registry.csv")["tick"] == 0.001).all())
    checks["artifacts_unchanged"] = all(gen.sha(directory / name) == digest for name, digest in manifest["artifact_hashes"].items())
    checks["replays_deterministic"] = all(len(set(pair)) == 1 for pair in manifest["deterministic_replay_hashes"].values())
    events = pd.read_csv(directory / "lock1_activation_events.csv")
    checks["next_event_activation"] = bool((pd.to_datetime(events.first_lock1_active_event, utc=True) > pd.to_datetime(events.trigger_event_time, utc=True)).all())
    checks["exact_original_r_levels"] = bool(np.allclose(abs(events.entry_price - events.initial_stop_price), events.initial_risk_price) and np.allclose(abs(events.plus2r_trigger_price - events.entry_price), 2 * events.initial_risk_price) and np.allclose(abs(events.lock1_price - events.entry_price), events.initial_risk_price))
    checks["monotonic_floor"] = bool(((events.direction.eq("LONG") & (events.effective_stop_at_activation >= events.canonical_stop_at_activation)) | (events.direction.eq("SHORT") & (events.effective_stop_at_activation <= events.canonical_stop_at_activation))).all())
    trades = pd.read_csv(directory / "lock1_after_2r_trades.csv")
    checks["exit_attribution"] = set(trades.exit_reason) <= {"INITIAL_STOP", "ATR_TRAILING_STOP", "LOCK1_STOP"}
    decision = pd.read_csv(directory / "lock1_decision_comparison.csv").computed_decision.iloc[0]
    checks["decision_recomputed"] = decision == manifest["decision"]
    checks["annual_gates"] = bool(pd.read_csv(directory / "yearly_metrics.csv").query("path == 'LOCK1_AFTER_2R'").net_R.gt(0).all())
    checks["protected_scope"] = not manifest["stage7_executed"] and all(k in manifest for k in ("stage6_1_hashes", "stage6_2_hashes", "stage6_3_hashes", "old_stage6_sha"))
    result = {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks, "independently_recomputed_decision": decision}
    (directory / "independent_audit_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    if result["status"] != "PASS":
        raise RuntimeError(result)
    return result


if __name__ == "__main__":
    print(json.dumps(audit(), sort_keys=True))
