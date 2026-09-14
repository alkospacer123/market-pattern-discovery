"""One-shot, deterministic TRUE OOS evaluation of the frozen T2/T3 candidates.

This module intentionally exposes no parameter or selection interface.  It is
the only research path allowed to open 2025+ files, and rejects every bar whose
*close* predates the TRUE OOS boundary.  Indicators therefore start cold on
OOS data; development history and portfolio state can never leak across it.
"""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any, Mapping

import numpy as np
import pandas as pd

from ..core.data_loader import DataLoader
from ..core.backtester import Backtester
from ..core.portfolio import FixedRiskPortfolio
from ..core.unified_metrics import concentration, finite, stats
from ..optimization.experiment import stable_hash
from ..optimization.phase32 import PARAMETERS, SPACES, _normalize_backtester
from ..strategies.trend.T2_Trend_Pullback import T2TrendPullback
from ..strategies.trend.T3_MTF_Trend import T3MTFTrend
from ..walk_forward.phase4 import EXPECTED_IDS, KEYS, verify_provenance as verify_phase33

TRUE_OOS_START = pd.Timestamp("2025-01-01", tz="UTC")
BOOTSTRAP_ITERATIONS = 10_000
BOOTSTRAP_SEED = 5102025
COST_TICKS_PER_SIDE = 1.0
STRATEGY_SHA256 = {
    "T2": "376df085cfda85eefccb31343aad40ed4fbb1078f1314496472a3a4ac9507774",
    "T3": "840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c",
}


def _json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _csv(path: Path, rows: Any, columns: list[str] | None = None) -> None:
    frame = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows, columns=columns)
    frame.map(finite).to_csv(path, index=False, lineterminator="\n", float_format="%.12g", na_rep="")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_provenance(
    registry_root: Path = Path("TradingSystemLab/results/robustness_validation"),
    optimization_root: Path = Path("TradingSystemLab/results/optimization"),
    phase4_root: Path = Path("TradingSystemLab/results/walk_forward_validation"),
    phase41_root: Path = Path("TradingSystemLab/results/borderline_diagnostics"),
    project_root: Path = Path("."),
) -> list[dict]:
    """HARD FAIL unless every frozen provenance link is still byte-valid."""
    candidates = verify_phase33(registry_root, optimization_root)
    phase4 = json.loads((phase4_root / "summary/manifest.json").read_text())
    phase41 = json.loads((phase41_root / "manifest.json").read_text())
    if phase41.get("status") != "PHASE_4_1_BORDERLINE_DIAGNOSTICS_COMPLETE":
        raise RuntimeError("PHASE41_MANIFEST_INVALID")
    registry_path = registry_root / "candidate_registry.json"
    if _sha(registry_path) != phase41["phase_3_3_provenance"]["sha256"]:
        raise RuntimeError("PHASE33_REGISTRY_HASH_MISMATCH")
    for candidate in candidates:
        key, cid = candidate["strategy"], candidate["candidate_id"]
        if phase41["classifications"].get(key) != "SAMPLE_LIMITED":
            raise RuntimeError("PHASE41_CANDIDATE_STATUS_MISMATCH")
        if phase4["frozen_parameter_hashes"].get(cid) != stable_hash(candidate["parameters"]):
            raise RuntimeError("PHASE4_FROZEN_PARAMETER_HASH_MISMATCH")
        if phase41["frozen_parameter_hashes"].get(cid) != stable_hash(candidate["parameters"]):
            raise RuntimeError("PHASE41_FROZEN_PARAMETER_HASH_MISMATCH")
        if phase41["phase_3_3_provenance"]["configuration_ids"].get(cid) != candidate["phase32_configuration_id"]:
            raise RuntimeError("PHASE32_CONFIGURATION_ID_MISMATCH")
        strategy = project_root / f"TradingSystemLab/strategies/trend/{key}_{'Trend_Pullback' if key == 'T2' else 'MTF_Trend'}.py"
        if _sha(strategy) != STRATEGY_SHA256[key]:
            raise RuntimeError("STRATEGY_CODE_CHANGED_AFTER_PHASE41")
        # Recheck the baseline explicitly, in addition to Phase 3.3 validation.
        if stable_hash(asdict(PARAMETERS[key])) != candidate["baseline_parameters_hash"]:
            raise RuntimeError("BASELINE_HASH_MISMATCH")
    return candidates


def load_true_oos(data_root: Path) -> tuple[dict[tuple[str, str], pd.DataFrame], dict]:
    """Load only H1 files named 2025+, with an independent content barrier."""
    result, coverage = {}, {}
    for symbol in ("Si", "CNY"):
        paths = sorted((data_root / "2026" / symbol).glob(f"{symbol}_H1_20*.csv"))
        paths = [p for p in paths if int(p.name.split("_")[2]) >= 2025]
        if not paths:
            raise FileNotFoundError(f"no TRUE OOS H1 data for {symbol}")
        frame = DataLoader(forbid_true_oos=False).close_index(
            DataLoader(forbid_true_oos=False).load_csv(paths), "1h")
        boundary = TRUE_OOS_START.tz_convert(frame.index.tz)
        if (frame.index < boundary).any():
            raise RuntimeError("TRUE_OOS_BARRIER_VIOLATION")
        frame = frame.loc[frame.index >= boundary].copy()
        result[(symbol, "H1")] = frame
        coverage[symbol] = {"bars": len(frame), "first_close": frame.index.min().isoformat(),
                            "last_close": frame.index.max().isoformat(),
                            "source_files": [p.name for p in paths]}
    return result, coverage


def _net(frame: pd.DataFrame) -> pd.Series:
    return frame.gross_R.astype(float) - 2 * COST_TICKS_PER_SIDE / frame.initial_risk_ticks.astype(float)


def _execute_oos(key: str, parameters: Any, data: Mapping) -> pd.DataFrame:
    """Execute frozen code with the development-only T2 guard replaced here.

    T2's static validator was intentionally baked into its Phase 1 research
    implementation.  The local subclass changes only data admission, not any
    signal or execution rule; Phase 5's stronger close-time barrier runs first.
    """
    class OOST2(T2TrendPullback):
        @staticmethod
        def _validate(frame: pd.DataFrame) -> None:
            if frame.empty or frame.index.tz is None or not frame.index.is_monotonic_increasing:
                raise ValueError("closed H1 timestamps must be timezone-aware, nonempty, and sorted")
            if (frame.index < TRUE_OOS_START.tz_convert(frame.index.tz)).any():
                raise RuntimeError("TRUE_OOS_BARRIER_VIOLATION")
            if not {"Open", "High", "Low", "Close"}.issubset(frame.columns):
                raise ValueError("H1 OHLC columns are required")
    pieces = []
    for symbol in ("Si", "CNY"):
        h1 = data[(symbol, "H1")]
        if key == "T2":
            pieces.append(OOST2(parameters).run(h1, symbol, tick_size=.001))
        else:
            raw = Backtester(FixedRiskPortfolio(), commission_per_unit=0, slippage_points=0,
                             allow_true_oos=True).run(
                T3MTFTrend(parameters), symbol, h1, DataLoader.h4_from_h1(h1)).trades
            pieces.append(_normalize_backtester(raw, key))
    frame = pd.concat(pieces, ignore_index=True)
    return frame.sort_values(["exit_time", "symbol", "trade_id"], kind="mergesort").reset_index(drop=True)


def _summary(values: pd.Series) -> dict:
    s = stats(values)
    return {"total_trades": s["trades"], "PF": s["PF_R"], "expectancy": s["expectancy"],
            "net_R": s["net_R"], "max_drawdown": s["max_DD_R"], "win_rate": s["winrate"],
            "average_win": s["average_win_R"], "average_loss": s["average_loss_R"],
            "recovery_factor": s["recovery_factor"]}


def _group_report(frame: pd.DataFrame, column: str, groups: list[Any]) -> list[dict]:
    net = _net(frame)
    return [{column: group, **_summary(net[frame[column].eq(group)])} for group in groups]


def _bootstrap(values: pd.Series) -> dict:
    x = np.asarray(values, dtype=np.float64)
    if not len(x):
        return {"iterations": BOOTSTRAP_ITERATIONS, "seed": BOOTSTRAP_SEED, "trades": 0,
                **{k: None for k in ("mean_R_2.5%", "mean_R_5%", "mean_R_50%", "mean_R_95%", "mean_R_97.5%", "probability_mean_R_gt_0")}}
    means = np.random.default_rng(BOOTSTRAP_SEED).choice(x, size=(BOOTSTRAP_ITERATIONS, len(x)), replace=True).mean(axis=1)
    q = np.quantile(means, [.025, .05, .5, .95, .975])
    return {"iterations": BOOTSTRAP_ITERATIONS, "seed": BOOTSTRAP_SEED, "trades": len(x),
            "mean_R_2.5%": q[0], "mean_R_5%": q[1], "mean_R_50%": q[2],
            "mean_R_95%": q[3], "mean_R_97.5%": q[4],
            "probability_mean_R_gt_0": float((means > 0).mean())}


def _classify(frame: pd.DataFrame, quarterly: list[dict], instruments: list[dict], directions: list[dict], boot: dict) -> tuple[str, list[str]]:
    overall, c = _summary(_net(frame)), concentration(_net(frame))
    positive_quarters = sum((r["expectancy"] or 0) > 0 for r in quarterly if r["total_trades"])
    observed_quarters = sum(r["total_trades"] > 0 for r in quarterly)
    robust = (overall["total_trades"] >= 50 and (overall["expectancy"] or 0) > 0
              and boot["probability_mean_R_gt_0"] >= .95
              and observed_quarters and positive_quarters / observed_quarters >= .6
              and all((r["expectancy"] or 0) >= 0 for r in instruments + directions if r["total_trades"])
              and (c["net_R_without_top5"] or 0) > 0)
    vanished = (overall["expectancy"] or 0) <= 0 or boot["probability_mean_R_gt_0"] <= .5
    reasons = [f"trades={overall['total_trades']} (PASS minimum 50)",
               f"bootstrap P(mean R > 0)={boot['probability_mean_R_gt_0']}",
               f"positive quarters={positive_quarters}/{observed_quarters}",
               f"net R after top-5 removal={c['net_R_without_top5']}"]
    return ("PASS" if robust else ("FAIL" if vanished else "BORDERLINE")), reasons


def _reports(key: str, frame: pd.DataFrame, target: Path) -> tuple[dict, str]:
    frame = frame.copy(); frame["R_result"] = _net(frame)
    frame["holding_time"] = pd.to_datetime(frame.exit_time, utc=True) - pd.to_datetime(frame.entry_time, utc=True)
    wanted = ["trade_id", "entry_time", "exit_time", "direction", "symbol", "entry_price", "exit_price",
              "R_result", "MAE_R", "MFE_R", "exit_reason", "holding_time"]
    _csv(target / "trades.csv", frame[wanted])
    years = pd.to_datetime(frame.exit_time, utc=True).dt.year
    exits = pd.to_datetime(frame.exit_time, utc=True)
    quarters = exits.dt.year.astype(str) + "Q" + (((exits.dt.month - 1) // 3) + 1).astype(str)
    yearly = _group_report(frame.assign(year=years), "year", sorted(set(years) | {2025, 2026}))
    quarterly = _group_report(frame.assign(quarter=quarters), "quarter", sorted(set(quarters)))
    instruments = _group_report(frame, "symbol", ["Si", "CNY"])
    directions = _group_report(frame, "direction", ["LONG", "SHORT"])
    _csv(target / "yearly_report.csv", yearly); _csv(target / "quarterly_report.csv", quarterly)
    _csv(target / "instrument_report.csv", instruments); _csv(target / "direction_report.csv", directions)
    conc = concentration(frame.R_result); _csv(target / "concentration_report.csv", [conc])
    distributions = []
    for group, mask in (("ALL", pd.Series(True, index=frame.index)), ("WINNERS", frame.R_result.gt(0)), ("LOSERS", frame.R_result.lt(0))):
        for name in ("MAE_R", "MFE_R"):
            x = frame.loc[mask, name].astype(float)
            distributions.append({"group": group, "metric": name, "trades": len(x), "mean": x.mean(), "median": x.median(), "p05": x.quantile(.05), "p95": x.quantile(.95)})
    for reason, part in frame.groupby("exit_reason", sort=True):
        distributions.append({"group": f"EXIT:{reason}", "metric": "R_result", "trades": len(part), "mean": part.R_result.mean(), "median": part.R_result.median(), "p05": part.R_result.quantile(.05), "p95": part.R_result.quantile(.95)})
    holding_hours = frame.holding_time.dt.total_seconds() / 3600
    distributions.append({"group": "ALL", "metric": "holding_hours", "trades": len(frame), "mean": holding_hours.mean(), "median": holding_hours.median(), "p05": holding_hours.quantile(.05), "p95": holding_hours.quantile(.95)})
    _csv(target / "mae_mfe_report.csv", distributions)
    boot = _bootstrap(frame.R_result); _csv(target / "bootstrap_report.csv", [boot])
    classification, reasons = _classify(frame, quarterly, instruments, directions, boot)
    metrics = {"candidate_id": EXPECTED_IDS[key], "cost_ticks_per_side": COST_TICKS_PER_SIDE,
               "start_state": "FLAT", "aggregate": _summary(frame.R_result), "classification": classification}
    _json(target / "metrics.json", metrics)
    report = (f"# {EXPECTED_IDS[key]} — TRUE OOS\n\n**Classification: {classification}**\n\n"
              "Frozen one-shot evaluation; no optimization, ranking, filters, or development state. "
              "C1 costs (one tick per side) are included.\n\n## Predeclared classification criteria\n\n"
              "PASS requires >=50 trades, positive expectancy, bootstrap probability >=95%, >=60% positive observed quarters, "
              "non-negative observed instrument/direction slices, and positive net R after top-5 removal. "
              "FAIL means non-positive expectancy or bootstrap probability <=50%; otherwise BORDERLINE.\n\n"
              "## Evidence\n\n" + "\n".join(f"- {x}" for x in reasons) + "\n")
    (target / "final_report.md").write_text(report, encoding="utf-8")
    return metrics, classification


def run(data_root: Path = Path("/workspace/market-pattern-data"), output: Path = Path("TradingSystemLab/results/true_oos_validation")) -> dict:
    candidates = verify_provenance(); data, coverage = load_true_oos(Path(data_root)); output = Path(output)
    if output.exists(): shutil.rmtree(output)
    output.mkdir(parents=True); (output / "summary").mkdir()
    baseline = pd.read_csv("TradingSystemLab/results/unified_baseline/baseline_comparison.csv").set_index("strategy")
    wf = pd.read_csv("TradingSystemLab/results/walk_forward_validation/summary/comparison.csv").set_index("candidate_id")
    comparison, classifications = [], {}
    for candidate in candidates:
        key, cid = candidate["strategy"], candidate["candidate_id"]; target = output / key; target.mkdir()
        before = stable_hash(candidate["parameters"])
        from dataclasses import replace
        frame = _execute_oos(key, replace(PARAMETERS[key], **candidate["parameters"]), data)
        if stable_hash(candidate["parameters"]) != before:
            raise RuntimeError("FROZEN_PARAMETERS_MODIFIED")
        if len(frame) and (pd.to_datetime(frame.entry_time, utc=True) < TRUE_OOS_START).any():
            raise RuntimeError("TRUE_OOS_TRADE_BARRIER_VIOLATION")
        metrics, classifications[key] = _reports(key, frame, target)
        oos = metrics["aggregate"]; b, w = baseline.loc[key], wf.loc[cid]
        days = (pd.Timestamp(max(v["last_close"] for v in coverage.values())) - TRUE_OOS_START).days + 1
        annual_frequency = oos["total_trades"] / days * 365.2425
        comparison.append({"candidate_id": cid, "phase2_PF": b.PF_R_C1, "phase4_PF": w.PF, "true_oos_PF": oos["PF"],
                           "PF_decay_phase2_to_oos": (oos["PF"] - b.PF_R_C1) if oos["PF"] is not None else None,
                           "phase2_expectancy": b.expectancy_C1, "phase4_expectancy": w.expectancy, "true_oos_expectancy": oos["expectancy"],
                           "expectancy_decay_phase2_to_oos": oos["expectancy"] - b.expectancy_C1,
                           "phase2_max_drawdown": b.max_DD_R_C1, "phase4_max_drawdown": w.max_drawdown, "true_oos_max_drawdown": oos["max_drawdown"],
                           "drawdown_expansion_vs_phase4": abs(oos["max_drawdown"]) - abs(w.max_drawdown),
                           "phase2_trades_per_year": b.trades_per_year, "phase4_trades_per_year": w.trades,
                           "true_oos_trades_per_year": annual_frequency, "classification": classifications[key]})
    _csv(output / "summary/comparison.csv", comparison)
    manifest = {"phase": "5", "status": "PHASE_5_TRUE_OOS_VALIDATION_COMPLETE", "candidate_ids": [c["candidate_id"] for c in candidates],
                "classifications": classifications, "true_oos_barrier": {"enabled": True, "start": "2025-01-01", "development_rows_read": 0},
                "coverage": coverage, "start_state": "FLAT", "cost_ticks_per_side": COST_TICKS_PER_SIDE,
                "parameters_frozen": True, "optimization": False, "walk_forward": False, "ranking": False,
                "bootstrap": {"iterations": BOOTSTRAP_ITERATIONS, "seed": BOOTSTRAP_SEED, "diagnostic_only": True},
                "strategy_code_sha256": STRATEGY_SHA256, "deterministic": True}
    _json(output / "summary/manifest.json", manifest)
    decision = "ELIGIBLE: carry PASS candidates only" if "PASS" in classifications.values() else "DO NOT PROCEED: no candidate passed"
    (output / "summary/final_true_oos_report.md").write_text(
        "# Phase 5 TRUE OOS Validation\n\n" + "\n".join(f"- **{EXPECTED_IDS[k]}: {v}**" for k, v in classifications.items()) +
        "\n\nPhase 2 baseline, Phase 4 forward, and TRUE OOS decay are reported in `comparison.csv`; candidates are not ranked. "
        "Instrument, direction, year/quarter, concentration/removal, MAE/MFE, exit-reason, holding-time and bootstrap diagnostics are retained per candidate.\n\n"
        f"## Phase 6 Portfolio Construction\n\n**{decision}.** No winner is selected.\n\nPHASE_5_TRUE_OOS_VALIDATION_COMPLETE\n", encoding="utf-8")
    # Hashes exclude manifest to avoid a self-referential digest.
    manifest["artifact_sha256"] = artifact_sha256(output, exclude={"summary/manifest.json"})
    _json(output / "summary/manifest.json", manifest)
    return manifest


def artifact_sha256(root: Path, exclude: set[str] | None = None) -> dict[str, str]:
    excluded = exclude or set()
    return {p.relative_to(root).as_posix(): _sha(p) for p in sorted(root.rglob("*"))
            if p.is_file() and p.relative_to(root).as_posix() not in excluded}
