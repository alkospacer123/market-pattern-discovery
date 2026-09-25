"""Build the v3 perpetual candidate registry from committed Phase 2 artifacts only."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

PHASE2_REFERENCE_MERGE = "272eabd5a4261a18a763356964b82b4b5b5673ea"
DOCS_REFERENCE_MERGE = "2a811672fe6619b8914fcc604769f2c2deeeb425"
PREDECLARED_CANDIDATES = (
    ("T2_M30_candidate_v3", "T2", "M30", "T2-M30-608dc87d09f1"),
    ("T2_H1_candidate_v3", "T2", "H1", "T2-H1-608dc87d09f1"),
    ("T3_M30_candidate_v3", "T3", "M30", "T3-M30-d6feb972db57"),
    ("T3_H1_candidate_v3", "T3", "H1", "T3-H1-4e73cdb77246"),
)
CANDIDATE_PARAMETERS = {
    "T2_M30_candidate_v3": {"ema_fast": 20, "ema_trend": 50, "ema_slow": 200, "adx_threshold": 20.0, "impulse_distance_atr": 0.5, "confirmation_window": 3, "max_initial_stop_atr": 2.5, "trailing_atr": 3.0},
    "T2_H1_candidate_v3": {"ema_fast": 20, "ema_trend": 50, "ema_slow": 200, "adx_threshold": 20.0, "impulse_distance_atr": 0.5, "confirmation_window": 3, "max_initial_stop_atr": 2.5, "trailing_atr": 3.0},
    "T3_M30_candidate_v3": {"ema_period": 100, "adx_threshold": 20.0, "breakout_period": 30, "atr_average_period": 20, "stop_atr": 2.0, "trail_atr": 3.0},
    "T3_H1_candidate_v3": {"ema_period": 100, "adx_threshold": 20.0, "breakout_period": 20, "atr_average_period": 20, "stop_atr": 2.5, "trail_atr": 3.0},
}
CANDIDATE_HASHES = {
    "T2_M30_candidate_v3": "608dc87d09f10aa0e03026ebb525f6b8ec865060c7890cee08fa0c7ed14cf86b",
    "T2_H1_candidate_v3": "608dc87d09f10aa0e03026ebb525f6b8ec865060c7890cee08fa0c7ed14cf86b",
    "T3_M30_candidate_v3": "d6feb972db575bf6e66ac901be95fe079dccc82d9e2c3e880d17faeae8d1adf9",
    "T3_H1_candidate_v3": "4e73cdb77246cb07b5953160b9fc0ab36bfd4bd6d9a7f7faaae7e6e392ee340a",
}
BASELINES = {
    "T2": {"ema_fast": 20, "ema_trend": 50, "ema_slow": 200, "adx_threshold": 20.0, "impulse_distance_atr": 0.5, "confirmation_window": 3, "max_initial_stop_atr": 3.0, "trailing_atr": 3.0},
    "T3": {"ema_period": 100, "adx_threshold": 20.0, "breakout_period": 20, "atr_average_period": 20, "stop_atr": 2.0, "trail_atr": 3.0},
}
BASELINE_HASHES = {"T2": "0f598fd08d5fee40575b8a23daaa12bdbe8ad40071f57fb8c9b8a566cda4eb4f", "T3": "782a150195d69651967ac8c5284b9140a050e35e9601cdc065ae11b196d30e47"}
STRATEGY_FILES = {"T2": "TradingSystemLab/strategies/trend/T2_Trend_Pullback.py", "T3": "TradingSystemLab/strategies/trend/T3_MTF_Trend.py"}
STRATEGY_HASHES = {"T2": "376df085cfda85eefccb31343aad40ed4fbb1078f1314496472a3a4ac9507774", "T3": "840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c"}
CHANGES = {"T2_M30_candidate_v3": ("max_initial_stop_atr", 3.0, 2.5), "T2_H1_candidate_v3": ("max_initial_stop_atr", 3.0, 2.5), "T3_M30_candidate_v3": ("breakout_period", 20, 30), "T3_H1_candidate_v3": ("stop_atr", 2.0, 2.5)}
EVIDENCE = {
    "T2-M30-608dc87d09f1": (324, 1.7118816595, .310463258155, 100.590095642, -16.3334012952, 6.15855165892),
    "T2-H1-608dc87d09f1": (156, 2.39295957746, .575052042961, 89.708118702, -6.88205022139, 13.0350863211),
    "T3-M30-d6feb972db57": (341, 1.93094457407, .376193476605, 128.281975522, -15.012134415, 8.54521895261),
    "T3-H1-4e73cdb77246": (181, 2.31342650378, .399304363394, 72.2740897743, -5.67342240555, 12.7390637622),
}
METRICS = ("trades", "PF_C1", "expectancy_C1", "net_R_C1", "max_DD_C1", "recovery_factor_C1")


def stable_hash(value: Any) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    return hashlib.sha256(data).hexdigest()


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _one(path: Path, config: str) -> dict[str, str]:
    found = [row for row in _rows(path) if row["configuration_id"] == config]
    if len(found) != 1:
        raise RuntimeError(f"EXPECTED_EXACTLY_ONE:{path}:{config}")
    return found[0]


def _persisted(row: dict[str, str]) -> dict[str, int | float]:
    answer = {}
    for key, text in row.items():
        if key not in {"configuration_id", "is_baseline"}:
            number = float(text)
            answer[key] = int(number) if number.is_integer() and "." not in text else number
    return answer


def build_registry(project_root: Path) -> tuple[dict[str, Any], dict[str, dict[str, str]]]:
    optimization = project_root / "TradingSystemLab/results/perpetual_v3/optimization"
    inventory = _rows(optimization / "robust_plateau_inventory.csv")
    if len(inventory) != 25:
        raise RuntimeError("PHASE2_INVENTORY_COUNT_MISMATCH")
    records, evidence_rows = [], {}
    for candidate_id, strategy, timeframe, config in PREDECLARED_CANDIDATES:
        study = optimization / strategy / timeframe
        parameter_row = _one(study / "parameters.csv", config)
        result_row = _one(study / "results.csv", config)
        plateau_row = _one(study / "plateau_report.csv", config)
        inventory_row = _one(optimization / "robust_plateau_inventory.csv", config)
        if plateau_row["classification"] != "ROBUST_PLATEAU" or (inventory_row["strategy"], inventory_row["timeframe"]) != (strategy, timeframe):
            raise RuntimeError(f"PHASE2_MEMBERSHIP_MISMATCH:{config}")
        parameters = CANDIDATE_PARAMETERS[candidate_id]
        if _persisted(parameter_row) != parameters or stable_hash(parameters) != CANDIDATE_HASHES[candidate_id]:
            raise RuntimeError(f"PARAMETER_IDENTITY_MISMATCH:{config}")
        if stable_hash(BASELINES[strategy]) != BASELINE_HASHES[strategy]:
            raise RuntimeError(f"BASELINE_IDENTITY_MISMATCH:{strategy}")
        differing = [key for key in parameters if parameters[key] != BASELINES[strategy][key]]
        if differing != [CHANGES[candidate_id][0]]:
            raise RuntimeError(f"NOT_SINGLE_PARAMETER_CHANGE:{config}")
        source_hash = hashlib.sha256((project_root / STRATEGY_FILES[strategy]).read_bytes()).hexdigest()
        if source_hash != STRATEGY_HASHES[strategy]:
            raise RuntimeError(f"STRATEGY_HASH_MISMATCH:{strategy}")
        observed = tuple(int(result_row[x]) if x == "trades" else float(result_row[x]) for x in METRICS)
        if observed != EVIDENCE[config]:
            raise RuntimeError(f"EVIDENCE_MISMATCH:{config}")
        records.append({"candidate_id": candidate_id, "strategy": strategy, "timeframe": timeframe, "phase2_configuration_id": config,
            "parameters": parameters, "parameter_hash": CANDIDATE_HASHES[candidate_id], "canonical_baseline_parameters": BASELINES[strategy],
            "canonical_baseline_parameter_hash": BASELINE_HASHES[strategy], "frozen_strategy_source_hash": source_hash,
            "phase2_classification": "ROBUST_PLATEAU", "selection_reason": "Predeclared ROBUST_PLATEAU member with positive instrument, Development-year, direction, and top-three-removed expectancy evidence. Maximum PF was not used as the selection method; declaration preceded Robustness and used no validation or future data.",
            "selection_method": "explicit_predeclared_identifier_without_metric_ranking", "validation_data_used_for_selection": False,
            "selection_locked_before_validation": True, "robustness_executed": False, "walk_forward_executed": False,
            "true_oos_executed": False, "true_oos_blocked": True, "phase2_reference_merge": PHASE2_REFERENCE_MERGE})
        evidence_rows[candidate_id] = result_row
    return {"schema_version": 1, "immutable": True, "candidates": records}, evidence_rows


def _report(registry: dict[str, Any], rows: dict[str, dict[str, str]]) -> str:
    out = ["# TradingSystemLab v3 Perpetual Phase 3 Candidate Freeze", "", "**Status:** `V3_PERPETUAL_PHASE_3_CANDIDATE_FREEZE_COMPLETE`", "", "This artifact-only freeze applies the original H1 predeclared-candidate contract to committed v3 Phase 2 Development evidence.", "", "No metric ranking, parameter search, raw market-data read, strategy execution, Robustness, Walk Forward, or TRUE OOS access occurred.", ""]
    for record in registry["candidates"]:
        cid, row = record["candidate_id"], rows[record["candidate_id"]]
        name, old, new = CHANGES[cid]
        out += [f"## {record['strategy']} / {record['timeframe']} — `{cid}`", "", f"- Phase 2 configuration ID: `{record['phase2_configuration_id']}`", f"- Single Baseline change: `{name}: {old} -> {new}`", "- Phase 2 classification: `ROBUST_PLATEAU`", f"- Trades: {row['trades']}; PF: {row['PF_C1']}; expectancy: {row['expectancy_C1']}; net R: {row['net_R_C1']}; max DD: {row['max_DD_C1']}; recovery: {row['recovery_factor_C1']}", f"- Instrument expectancies: USDRUBF {row['USDRUBF_expectancy_C1']}; CNYRUBF {row['CNYRUBF_expectancy_C1']}; GLDRUBF {row['GLDRUBF_expectancy_C1']}; IMOEXF {row['IMOEXF_expectancy_C1']}", f"- Year expectancies: 2023 {row['Y2023_expectancy_C1']}; 2024 {row['Y2024_expectancy_C1']}", f"- Direction expectancies: LONG {row['LONG_expectancy_C1']}; SHORT {row['SHORT_expectancy_C1']}", f"- Top-3 positive-R share: {row['top_3_positive_R_share']}; expectancy without top 3: {row['expectancy_C1_without_top3']}", f"- Full parameter hash: `{record['parameter_hash']}`", f"- Selection reason: {record['selection_reason']}", ""]
    out += ["## Lifecycle lock", "", "After merge, these candidate parameters are immutable for the next Robustness task. Robustness must consume the exact registry bytes from this directory. A weak, borderline, or rejected result does not permit replacement, return to the 25-member inventory, or a second selection. Any parameter change creates a new research identity and requires return to an earlier research stage.", "", "TRUE OOS >= 2025-01-01 remains `BLOCKED_NOT_READ_NOT_EXECUTED`. No validation or future data were used for declaration.", ""]
    return "\n".join(out)


def generate(project_root: Path, output_root: Path | None = None) -> Path:
    registry, rows = build_registry(project_root)
    output = output_root or project_root / "TradingSystemLab/results/perpetual_v3/phase3_candidate_freeze"
    output.mkdir(parents=True, exist_ok=True)
    registry_path, report_path = output / "candidate_registry.json", output / "Candidate_Freeze_Report.md"
    registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(_report(registry, rows), encoding="utf-8")
    manifest = {"generation": "v3_perpetual", "phase": "PHASE_3_CANDIDATE_FREEZE", "status": "V3_PERPETUAL_PHASE_3_CANDIDATE_FREEZE_COMPLETE", "methodological_source": "original H1 Phase 3.3 predeclared-candidate contract", "phase2_reference_merge": PHASE2_REFERENCE_MERGE, "docs_reference_merge": DOCS_REFERENCE_MERGE, "candidate_count": 4, "strategies": ["T2", "T3"], "timeframes": ["M30", "H1"], "instruments": ["USDRUBF", "CNYRUBF", "GLDRUBF", "IMOEXF"], "development_period": ["2023-01-01", "2024-12-31"], "true_oos_start": "2025-01-01", "selection_locked_before_validation": True, "raw_market_data_read": False, "optimization_executed": False, "parameter_search_executed": False, "ranking_executed": False, "robustness_executed": False, "walk_forward_executed": False, "true_oos_executed": False, "portfolio_executed": False, "mtf_executed": False, "true_oos_blocked": True, "next_action": "PHASE_3_ROBUSTNESS", "artifact_sha256": {"candidate_registry.json": hashlib.sha256(registry_path.read_bytes()).hexdigest(), "Candidate_Freeze_Report.md": hashlib.sha256(report_path.read_bytes()).hexdigest()}}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return output


if __name__ == "__main__":
    generate(Path(__file__).resolve().parents[1])
