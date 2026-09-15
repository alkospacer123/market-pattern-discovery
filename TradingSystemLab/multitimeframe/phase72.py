"""Phase 7.2: deterministic analysis of the immutable Phase 7.1 artifacts.

This module intentionally has no market-data, strategy, ranking, or parameter
search interface.  Every statistic is derived from the saved Phase 7.1 trade
files and the repository's unified R-metric definitions.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
from typing import Any

import pandas as pd

from ..core.unified_metrics import concentration, finite, stats

INPUT = Path("TradingSystemLab/results/multitimeframe_research")
ANALYSIS_OUTPUT = Path("TradingSystemLab/results/multitimeframe_analysis")
REGISTRY_OUTPUT = Path("TradingSystemLab/results/candidate_registry_v2")
STRATEGIES = ("T2", "T3")
INSTRUMENTS = ("USDRUBF", "CNYRUBF")
TIMEFRAMES = ("M30", "H1", "H4", "D1")

# Pre-declared, non-tunable classification policy.  These are gates, never
# weights or sorting criteria; every combination remains in the registry.
QUALIFICATION_RULES = {
    "minimum_trades": 30,
    "minimum_expectancy_R": 0.0,
    "minimum_net_R": 0.0,
    "maximum_absolute_drawdown_R": 15.0,
    "maximum_top5_positive_R_share": 0.60,
    "require_both_years_positive": True,
    "require_both_directions_positive": True,
    "require_other_instrument_positive": True,
}


def _hashes(root: Path) -> dict[str, str]:
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    pd.DataFrame(rows).map(finite).to_csv(
        path, index=False, lineterminator="\n", float_format="%.12g", na_rep="")


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
                    encoding="utf-8")


def _returns(frame: pd.DataFrame) -> pd.Series:
    """Read Phase 7.1's saved C1 return, accommodating its two trade schemas."""
    if not len(frame):
        return pd.Series(dtype=float)
    if "net_R_C1" in frame:
        return frame["net_R_C1"].astype(float)
    # This is the exact Phase 7.1 summary expression, not a trade recalculation.
    return frame["gross_R"].astype(float) - 2.0 / frame["initial_risk_ticks"].astype(float)


def _metrics(frame: pd.DataFrame) -> dict[str, Any]:
    values = _returns(frame)
    result = stats(values)
    holding = ((pd.to_datetime(frame["exit_time"], utc=True) -
                pd.to_datetime(frame["entry_time"], utc=True)).dt.total_seconds() / 3600
               if len(frame) else pd.Series(dtype=float))
    return {"trades": result["trades"], "PF": result["PF_R"],
            "expectancy": result["expectancy"], "net_R": result["net_R"],
            "max_drawdown": result["max_DD_R"],
            "recovery_factor": result["recovery_factor"],
            "win_rate": result["winrate"],
            "average_holding_hours": finite(holding.mean())}


def _positive(metric: dict[str, Any]) -> bool:
    return metric["trades"] > 0 and metric["expectancy"] is not None and metric["expectancy"] > 0 and metric["net_R"] > 0


def classify(evidence: dict[str, Any]) -> tuple[str, str, str]:
    """Apply fixed independent gates and return status, reason, limitations."""
    failures = []
    if evidence["trades"] < QUALIFICATION_RULES["minimum_trades"]: failures.append("insufficient trade count")
    if evidence["expectancy"] is None or evidence["expectancy"] <= 0: failures.append("non-positive expectancy")
    if evidence["net_R"] <= 0: failures.append("non-positive net R")
    if abs(evidence["max_drawdown"]) > QUALIFICATION_RULES["maximum_absolute_drawdown_R"]: failures.append("drawdown exceeds policy")
    if evidence["top5_positive_R_share"] is None or evidence["top5_positive_R_share"] > QUALIFICATION_RULES["maximum_top5_positive_R_share"]: failures.append("high or unavailable top-5 concentration")
    if not evidence["yearly_consistency"]: failures.append("2023/2024 results are not both positive")
    if not evidence["direction_consistency"]: failures.append("LONG/SHORT results are not both positive")
    if not evidence["instrument_consistency"]: failures.append("paired instrument result is not positive")
    if failures:
        return "RESEARCH_ONLY", "; ".join(failures), "Retained for future research; failed gates require independent evidence."
    return ("ROBUST_TIMEFRAME_CANDIDATE",
            "All fixed trade-count, expectancy, net-R, drawdown, concentration, year, direction, and instrument gates passed.",
            "Descriptive development evidence only; no validation or selection inference.")


def run(input_root: Path = INPUT, analysis_output: Path = ANALYSIS_OUTPUT,
        registry_output: Path = REGISTRY_OUTPUT) -> dict[str, Any]:
    input_root = Path(input_root)
    before = _hashes(input_root)
    manifest = json.loads((input_root / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("phase") != "7.1" or not manifest.get("true_oos_blocked"):
        raise RuntimeError("INVALID_PHASE_7_1_INPUT_MANIFEST")

    frames, base = {}, {}
    for strategy in STRATEGIES:
        for timeframe in TIMEFRAMES:
            for instrument in INSTRUMENTS:
                key = (strategy, instrument, timeframe)
                path = input_root / strategy / timeframe / f"{instrument}_trades.csv"
                frame = pd.read_csv(path)
                frames[key], base[key] = frame, _metrics(frame)

    comparison, stability, concentrations, decisions = [], [], [], []
    for strategy in STRATEGIES:
        for timeframe in TIMEFRAMES:
            for instrument in INSTRUMENTS:
                key, frame = (strategy, instrument, timeframe), frames[(strategy, instrument, timeframe)]
                metric = base[key]
                years = {year: _metrics(frame.loc[pd.to_datetime(frame["exit_time"], utc=True).dt.year.eq(year)]) for year in (2023, 2024)}
                directions = {side: _metrics(frame.loc[frame["direction"].eq(side)]) for side in ("LONG", "SHORT")}
                other = next(x for x in INSTRUMENTS if x != instrument)
                conc = concentration(_returns(frame))
                evidence = {**metric,
                    "yearly_consistency": all(_positive(years[y]) for y in (2023, 2024)),
                    "direction_consistency": all(_positive(directions[d]) for d in ("LONG", "SHORT")),
                    "instrument_consistency": _positive(base[(strategy, other, timeframe)]),
                    "top5_positive_R_share": conc["top_5_positive_R_share"]}
                status, reason, limitations = classify(evidence)
                identity = {"strategy": strategy, "instrument": instrument, "timeframe": timeframe}
                comparison.append({**identity, **metric, "trades_per_year": metric["trades"] / 2,
                                   "trades_per_month": metric["trades"] / 24,
                                   "yearly_consistency": evidence["yearly_consistency"],
                                   "direction_consistency": evidence["direction_consistency"],
                                   "instrument_consistency": evidence["instrument_consistency"]})
                for dimension, parts in (("YEAR", years), ("DIRECTION", directions)):
                    for segment, values in parts.items():
                        stability.append({**identity, "dimension": dimension, "segment": segment, **values})
                concentrations.append({**identity, **conc})
                decisions.append({**identity, "status": status, "reason": reason,
                                  "evidence": (f"trades={metric['trades']}; expectancy={metric['expectancy']}; "
                                               f"net_R={metric['net_R']}; max_drawdown={metric['max_drawdown']}; "
                                               f"top5_share={evidence['top5_positive_R_share']}"),
                                  "limitations": limitations})

    if _hashes(input_root) != before:
        raise RuntimeError("PHASE_7_1_ARTIFACTS_CHANGED")
    for target in (analysis_output, registry_output):
        if target.exists(): shutil.rmtree(target)
        target.mkdir(parents=True)
    _write_csv(analysis_output / "comparison.csv", comparison)
    _write_csv(analysis_output / "stability_report.csv", stability)
    _write_csv(analysis_output / "concentration_report.csv", concentrations)
    _write_csv(analysis_output / "candidate_decision_log.csv", decisions)
    common_manifest = {"phase": "7.2", "status": "PHASE_7_2_MULTITIMEFRAME_ANALYSIS_COMPLETE",
        "input_root": str(input_root), "input_artifact_sha256": before,
        "qualification_rules": QUALIFICATION_RULES, "true_oos_blocked": True,
        "market_data_accessed": False, "strategy_execution_performed": False,
        "trade_recalculation_performed": False, "optimization_performed": False,
        "ranking_performed": False, "selection_performed": False,
        "all_combinations_retained": True}
    _write_json(analysis_output / "manifest.json", common_manifest)
    registry = [{k: row[k] for k in ("strategy", "instrument", "timeframe", "status", "reason")}
                for row in decisions]
    _write_csv(registry_output / "candidate_registry.csv", registry)
    _write_json(registry_output / "manifest.json", common_manifest)

    table = ["# Candidate Registry v2", "", "Classification only; entries are not ranked and none are discarded.", "",
             "| Strategy | Instrument | Timeframe | Status | Reason |", "|---|---|---|---|---|"]
    table += ["| " + " | ".join(str(row[k]) for k in ("strategy", "instrument", "timeframe", "status", "reason")) + " |" for row in registry]
    table += ["", "PHASE_7_2_MULTITIMEFRAME_ANALYSIS_COMPLETE", ""]
    (registry_output / "candidate_registry.md").write_text("\n".join(table), encoding="utf-8")
    report = ["# Phase 7.2 Multi-Timeframe Analysis", "",
              "Analytical classification of Phase 7.1 saved trades only. No market data, strategy execution, parameter search, ranking, validation, or TRUE OOS was used.", "",
              "## Decisions", ""] + table[4:-2] + ["", "## Limitations", "",
              "All results describe 2023–2024 development artifacts. A candidate status is permission for future research, not strategy selection.", "",
              "PHASE_7_2_MULTITIMEFRAME_ANALYSIS_COMPLETE", ""]
    (analysis_output / "summary_report.md").write_text("\n".join(report), encoding="utf-8")
    return {"status": common_manifest["status"], "combinations": len(decisions)}
