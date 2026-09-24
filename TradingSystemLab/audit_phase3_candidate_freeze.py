"""Independent, fail-closed audit of the artifact-only candidate freeze."""
from __future__ import annotations

import ast
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

PHASE2_REFERENCE_COMMIT = "9206e2f2ca9a6524ddf78ba473b9b882938aefc6"
PREDECLARED_CANDIDATES = (
    ("T2_M30_candidate_v2", "T2", "M30", "T2-M30-7c89b4a215cd"),
    ("T2_H1_candidate_v2", "T2", "H1", "T2-H1-a98459cab4f2"),
    ("T3_M30_candidate_v2", "T3", "M30", "T3-M30-0050d828c1a8"),
    ("T3_H1_candidate_v2", "T3", "H1", "T3-H1-aeeb96942cf3"),
)
BASELINES = {
    "T2": {"ema_fast": 20, "ema_trend": 50, "ema_slow": 200, "adx_threshold": 20.0,
           "impulse_distance_atr": 0.5, "confirmation_window": 3,
           "max_initial_stop_atr": 3.0, "trailing_atr": 3.0},
    "T3": {"ema_period": 100, "adx_threshold": 20.0, "breakout_period": 20,
           "atr_average_period": 20, "stop_atr": 2.0, "trail_atr": 3.0},
}
CHANGES = {"T2_M30_candidate_v2": ("adx_threshold", 25),
           "T2_H1_candidate_v2": ("ema_fast", 25),
           "T3_M30_candidate_v2": ("ema_period", 75),
           "T3_H1_candidate_v2": ("atr_average_period", 30)}
STRATEGY_FILES = {"T2": "TradingSystemLab/strategies/trend/T2_Trend_Pullback.py",
                  "T3": "TradingSystemLab/strategies/trend/T3_MTF_Trend.py"}
STRATEGY_HASHES = {"T2": "376df085cfda85eefccb31343aad40ed4fbb1078f1314496472a3a4ac9507774",
                   "T3": "840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c"}

EXPECTED_EVIDENCE = {
    "T2-M30-7c89b4a215cd": (982, 1.38439307062, 0.179005404674, 175.783307389, -33.5282069751, 5.24284843266),
    "T2-H1-a98459cab4f2": (649, 1.49070753729, 0.224423840621, 145.651072563, -14.9346837251, 9.75253813499),
    "T3-M30-0050d828c1a8": (1581, 1.36261268342, 0.162875006507, 257.505385288, -22.5343558886, 11.4272352208),
    "T3-H1-aeeb96942cf3": (714, 1.46328578667, 0.203160457152, 145.056566406, -16.2129477802, 8.9469582196),
}
METRIC_FIELDS = ("trades", "PF_C1", "expectancy_C1", "net_R_C1", "max_DD_C1", "recovery_factor_C1")


def stable_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _exact(rows: list[dict[str, str]], key: str, value: str, label: str) -> dict[str, str]:
    found = [row for row in rows if row[key] == value]
    if len(found) != 1:
        raise AssertionError(f"{label}: expected exactly one {value}, found {len(found)}")
    return found[0]


def _parameters(row: dict[str, str], strategy: str, candidate_id: str) -> dict[str, int | float]:
    resolved = dict(BASELINES[strategy])
    name, value = CHANGES[candidate_id]
    resolved[name] = value
    persisted = {key: float(item) for key, item in row.items()
                 if key not in {"configuration_id", "is_baseline"}}
    if set(persisted) != set(resolved) or any(persisted[key] != resolved[key] for key in resolved):
        raise AssertionError(f"{candidate_id}: Phase 2 parameter row mismatch")
    return resolved


def _prove_declaration_only(project_root: Path) -> None:
    """Reject any executable winner-selection primitive in the freeze module."""
    source = (project_root / "TradingSystemLab/phase3_candidate_freeze.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    declarations = None
    prohibited_calls = {"sorted", "sort", "nlargest", "idxmax", "argmax"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "PREDECLARED_CANDIDATES"
                                                for target in node.targets):
            declarations = ast.literal_eval(node.value)
        if isinstance(node, ast.Call):
            name = node.func.id if isinstance(node.func, ast.Name) else (
                node.func.attr if isinstance(node.func, ast.Attribute) else "")
            if name in prohibited_calls:
                raise AssertionError(f"candidate selection primitive forbidden: {name}")
    if declarations != PREDECLARED_CANDIDATES:
        raise AssertionError("candidate identities are not literal predeclarations")


def audit(project_root: Path | str = Path("."), registry_path: Path | None = None) -> dict[str, Any]:
    root = Path(project_root)
    registry_path = registry_path or root / "TradingSystemLab/results/phase3_candidate_freeze/candidate_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    manifest_path = root / "TradingSystemLab/results/phase3_candidate_freeze/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_contract = {
        "phase": "PHASE_3_CANDIDATE_FREEZE", "status": "PHASE_3_CANDIDATE_FREEZE_COMPLETE",
        "phase2_reference_commit": PHASE2_REFERENCE_COMMIT, "candidate_count": 4,
        "selection_locked_before_validation": True, "raw_market_data_read": False,
        "optimization_executed": False, "parameter_search_executed": False,
        "ranking_executed": False, "robustness_executed": False,
        "walk_forward_executed": False, "true_oos_executed": False,
        "phase7_mtf_research": False, "true_oos_blocked": True,
    }
    if any(manifest.get(key) != value for key, value in manifest_contract.items()):
        raise AssertionError("freeze manifest contract mismatch")
    # For normal audit operation, bind the immutable provenance bundle. A
    # caller-supplied registry is intentionally permitted for corruption tests.
    canonical_registry = root / "TradingSystemLab/results/phase3_candidate_freeze/candidate_registry.json"
    if registry_path == canonical_registry:
        artifacts = manifest.get("artifact_sha256", {})
        report = root / "TradingSystemLab/results/phase3_candidate_freeze/Candidate_Freeze_Report.md"
        if artifacts.get("candidate_registry.json") != hashlib.sha256(registry_path.read_bytes()).hexdigest():
            raise AssertionError("registry artifact hash mismatch")
        if artifacts.get("Candidate_Freeze_Report.md") != hashlib.sha256(report.read_bytes()).hexdigest():
            raise AssertionError("report artifact hash mismatch")
    records = registry.get("candidates")
    if not isinstance(records, list) or len(records) != 4:
        raise AssertionError("exactly four frozen candidates required")
    actual_order = [(r.get("candidate_id"), r.get("strategy"), r.get("timeframe"), r.get("phase2_configuration_id")) for r in records]
    if actual_order != list(PREDECLARED_CANDIDATES):
        raise AssertionError("candidate declaration/order mismatch")

    _prove_declaration_only(root)
    inventory = _rows(root / "TradingSystemLab/results/optimization_v2/robust_plateau_inventory.csv")
    if len(inventory) != 25:
        raise AssertionError("canonical plateau inventory must contain 25 rows")

    for record in records:
        strategy, timeframe = record["strategy"], record["timeframe"]
        config_id = record["phase2_configuration_id"]
        study = root / "TradingSystemLab/results/optimization_v2" / strategy / timeframe
        parameter_row = _exact(_rows(study / "parameters.csv"), "configuration_id", config_id, "parameters")
        result_row = _exact(_rows(study / "results.csv"), "configuration_id", config_id, "results")
        plateau_row = _exact(_rows(study / "plateau_report.csv"), "configuration_id", config_id, "plateau")
        inventory_row = _exact(inventory, "configuration_id", config_id, "inventory")
        if plateau_row["classification"] != "ROBUST_PLATEAU" or record.get("phase2_classification") != "ROBUST_PLATEAU":
            raise AssertionError(f"{config_id}: classification mismatch")
        if (inventory_row["strategy"], inventory_row["timeframe"]) != (strategy, timeframe):
            raise AssertionError(f"{config_id}: inventory scope mismatch")
        resolved = _parameters(parameter_row, strategy, record["candidate_id"])
        if record.get("parameters") != resolved or record.get("parameter_hash") != stable_hash(resolved):
            raise AssertionError(f"{config_id}: candidate parameter/hash mismatch")
        baseline = record.get("canonical_baseline_parameters")
        if baseline != BASELINES[strategy] or record.get("canonical_baseline_parameter_hash") != stable_hash(baseline):
            raise AssertionError(f"{config_id}: baseline parameter/hash mismatch")
        source_hash = hashlib.sha256((root / STRATEGY_FILES[strategy]).read_bytes()).hexdigest()
        if source_hash != STRATEGY_HASHES[strategy] or record.get("frozen_strategy_source_hash") != source_hash:
            raise AssertionError(f"{strategy}: frozen strategy hash mismatch")
        observed = tuple(int(result_row[field]) if field == "trades" else float(result_row[field]) for field in METRIC_FIELDS)
        if observed != EXPECTED_EVIDENCE[config_id]:
            raise AssertionError(f"{config_id}: expected evidence mismatch")
        required = {
            "selection_method": "explicit_predeclared_identifier_without_metric_ranking",
            "validation_data_used_for_selection": False,
            "selection_locked_before_validation": True,
            "robustness_executed": False, "walk_forward_executed": False,
            "true_oos_executed": False, "true_oos_blocked": True,
            "phase2_reference_commit": PHASE2_REFERENCE_COMMIT,
        }
        if any(record.get(key) != value for key, value in required.items()):
            raise AssertionError(f"{config_id}: lifecycle lock mismatch")
    return {"status": "PHASE_3_CANDIDATE_FREEZE_COMPLETE", "candidate_count": 4,
            "selection_locked_before_validation": True}


if __name__ == "__main__":
    result = audit(Path(__file__).resolve().parents[1])
    print(json.dumps(result, sort_keys=True))
