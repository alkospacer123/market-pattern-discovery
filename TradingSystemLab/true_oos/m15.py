"""One-shot TRUE OOS validation for the frozen M15 T2/T3 candidates.

This is an execution-only boundary.  It deliberately has no optimization,
ranking, selection, or parameter override API.  Market data is discovered by
explicit 2025+ file names and is rejected unless every candle close is on or
after the locked boundary.
"""
from __future__ import annotations

import ast
from dataclasses import replace
import hashlib
import html
import json
from pathlib import Path
import shutil
from typing import Any, Mapping

import pandas as pd
import numpy as np

from ..core.backtester import Backtester
from ..core.data_loader import DataLoader
from ..core.instrument_specs import get_instrument_spec
from ..core.portfolio import FixedRiskPortfolio
from ..core.unified_metrics import concentration, finite, stats
from ..multitimeframe.phase71 import (APPROVED_DATA_ROOT, COST_TICKS_PER_SIDE,
    STRATEGY_SHA256, TRUE_OOS_START, verify_frozen_strategies)
from ..multitimeframe.phase73 import hash_tree
from ..optimization.experiment import stable_hash
from ..optimization.phase32 import PARAMETERS, _normalize_backtester
from ..strategies.trend.T2_Trend_Pullback import T2TrendPullback
from ..strategies.trend.T3_MTF_Trend import T3MTFTrend
from ..timeframe_validation.m15_baseline import INSTRUMENTS, TRADE_COLUMNS, causal_h1_context

TIMEFRAME = "M15"
PHASE = "M15_TRUE_OOS"
STATUS = "PHASE_M15_TRUE_OOS_COMPLETE"
DEVELOPMENT_PERIOD = ["2023-01-01", "2024-12-31"]
TRUE_OOS_PERIOD = ["2025-01-01", None]
OUTPUT = Path("TradingSystemLab/results/true_oos_validation/M15")
FROZEN_REGISTRY = Path("TradingSystemLab/results/timeframe_optimization/M15")
WALK_FORWARD = Path("TradingSystemLab/results/walk_forward/M15")
BASELINE = Path("TradingSystemLab/results/timeframe_validation/M15")
ROBUSTNESS = Path("TradingSystemLab/results/timeframe_analysis/M15_ROBUSTNESS")
ALLOWED_CANDIDATES = {"T2": "T2_candidate_v1", "T3": "T3_candidate_v1"}
EVALUATED_CANDIDATES = {"T2": "T2_M15_candidate_v1", "T3": "T3_M15_candidate_v1"}
PRE_OOS_VERDICTS = {"T2": "WALK_FORWARD_BORDERLINE", "T3": "WALK_FORWARD_FAIL"}
BOOTSTRAP_ITERATIONS = 10_000
BOOTSTRAP_SEED = 5102025
EXPECTED_REGISTRY = {
    "T2": ("T2_M15_candidate_v1", "T2-M15-0014-26fb9b19bd4f", "26fb9b19bd4fca7805d88d08817831d516d5de51b118bfd428d8626e593da317"),
    "T3": ("T3_M15_candidate_v1", "T3-M15-0011-76dd2f3526c3", "76dd2f3526c38a3c7abfd3117d2a9ea4a78d0954c868bd01260736011726ba69"),
}


class FrozenParameters(dict):
    """JSON-compatible parameter mapping that cannot be changed in memory."""
    def _immutable(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("TRUE OOS parameters are frozen")

    __setitem__ = __delitem__ = clear = pop = popitem = setdefault = update = _immutable

    def __copy__(self) -> "FrozenParameters":
        return self

    def __deepcopy__(self, memo: dict) -> "FrozenParameters":
        return self


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _csv(path: Path, value: Any) -> None:
    frame = value if isinstance(value, pd.DataFrame) else pd.DataFrame(value)
    frame.map(finite).to_csv(path, index=False, lineterminator="\n", float_format="%.12g", na_rep="")


def reject_pre_oos(values: Any) -> None:
    """Reject an empty-timezone or pre-boundary TRUE OOS input."""
    stamps = pd.DatetimeIndex(pd.to_datetime(values, utc=True))
    if len(stamps) and (stamps < TRUE_OOS_START.tz_convert("UTC")).any():
        raise RuntimeError("M15_TRUE_OOS_PRE_BOUNDARY_ACCESS")


def _assert_execution_only() -> None:
    """Fail closed if a forbidden API call is ever added to this runner."""
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    forbidden = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = node.func.id if isinstance(node.func, ast.Name) else (
            node.func.attr if isinstance(node.func, ast.Attribute) else "")
        if name.lower().startswith(("optim", "rank")):
            forbidden.append(name)
    if forbidden:
        raise RuntimeError("M15_TRUE_OOS_FORBIDDEN_API_CALL")


def load_frozen_registry(registry_root: Path = FROZEN_REGISTRY,
                         walk_forward: Path = WALK_FORWARD) -> dict[str, dict]:
    """Load parameters solely from the frozen registries and verify identity."""
    wf_path = Path(walk_forward) / "manifest.json"
    wf = json.loads(wf_path.read_text(encoding="utf-8"))
    if wf.get("status") != "PHASE_M15_WALK_FORWARD_COMPLETE" or wf.get("development_period") != DEVELOPMENT_PERIOD:
        raise RuntimeError("M15_WALK_FORWARD_PROVENANCE_INVALID")
    result: dict[str, dict] = {}
    for key in ("T2", "T3"):
        path = Path(registry_root) / key / "candidate_registry.json"
        row = json.loads(path.read_text(encoding="utf-8"))
        expected_id, configuration, parameter_hash = EXPECTED_REGISTRY[key]
        identity = (row.get("candidate_id"), row.get("configuration_id"), row.get("parameter_hash"))
        if identity != (expected_id, configuration, parameter_hash):
            raise RuntimeError(f"{key}_FROZEN_CANDIDATE_IDENTITY_MISMATCH")
        if row.get("baseline_candidate_id") != ALLOWED_CANDIDATES[key]:
            raise RuntimeError(f"{key}_CANDIDATE_ID_MISMATCH")
        if stable_hash(row.get("parameters", {})) != parameter_hash:
            raise RuntimeError(f"{key}_FROZEN_PARAMETER_HASH_MISMATCH")
        if row.get("strategy_hash") != STRATEGY_SHA256[key]:
            raise RuntimeError(f"{key}_FROZEN_STRATEGY_HASH_MISMATCH")
        if (wf.get("candidate_ids", {}).get(key), wf.get("configuration_ids", {}).get(key),
                wf.get("parameter_hashes", {}).get(key), wf.get("candidate_registry_hashes", {}).get(key)) != (
                expected_id, configuration, parameter_hash, _sha(path)):
            raise RuntimeError(f"{key}_WALK_FORWARD_IDENTITY_MISMATCH")
        aggregate = json.loads((Path(walk_forward) / key / "aggregate_metrics.json").read_text(encoding="utf-8"))
        if aggregate.get("candidate_id") != expected_id or aggregate.get("verdict") != PRE_OOS_VERDICTS[key]:
            raise RuntimeError(f"{key}_WALK_FORWARD_VERDICT_MISMATCH")
        row["parameters"] = FrozenParameters(row["parameters"])
        result[key] = row
    return result


def discover_true_oos_files(data_root: Path, alias: str) -> list[Path]:
    root = Path(data_root).resolve()
    if root != APPROVED_DATA_ROOT.resolve():
        raise ValueError("UNAPPROVED_MARKET_DATA_ROOT")
    folder = root / "2026" / alias
    # Enumerate admitted years explicitly; never use an unbounded development glob.
    files = [path for year in range(2025, 2100)
             for path in folder.glob(f"{alias}_M15_{year}_Q*.csv")]
    return sorted(files, key=lambda path: path.name)


def validate_true_oos_candles(frame: pd.DataFrame) -> None:
    if frame.empty or frame.index.tz is None:
        raise ValueError("M15_TRUE_OOS_EMPTY_OR_NAIVE")
    if not frame.index.is_monotonic_increasing or frame.index.has_duplicates:
        raise ValueError("M15_TRUE_OOS_ORDERING_VIOLATION")
    reject_pre_oos(frame.index)
    index = pd.DatetimeIndex(frame.index)
    if not ((index.minute % 15 == 0) & (index.second == 0) & (index.microsecond == 0)).all():
        raise ValueError("M15_TRUE_OOS_TIMEFRAME_VIOLATION")


def load_true_oos(data_root: Path, alias: str) -> tuple[pd.DataFrame, list[Path]]:
    paths = discover_true_oos_files(data_root, alias)
    if not paths:
        raise FileNotFoundError(f"no TRUE OOS M15 data for {alias}")
    loader = DataLoader(forbid_true_oos=False)
    pieces = [loader._read(path) for path in paths]
    for piece in pieces:
        validate_true_oos_candles(piece)
    raw = pd.concat(pieces)
    validate_true_oos_candles(raw)
    frame = loader.close_index(raw, "15min")
    validate_true_oos_candles(frame)
    return frame, paths


class _OOST2(T2TrendPullback):
    """Admission-only adapter; signal and state-machine behavior is unchanged."""
    @staticmethod
    def _validate(frame: pd.DataFrame) -> None:
        validate_true_oos_candles(frame)
        if not {"Open", "High", "Low", "Close"}.issubset(frame.columns):
            raise ValueError("M15 OHLC columns are required")


def execute_candidate(key: str, registry: Mapping[str, Any], loaded: Mapping[str, pd.DataFrame]) -> pd.DataFrame:
    """Execute one uninterrupted OOS period from a new FLAT strategy state."""
    if registry.get("baseline_candidate_id") != ALLOWED_CANDIDATES.get(key):
        raise RuntimeError(f"{key}_CANDIDATE_ID_MISMATCH")
    parameter_hash = stable_hash(registry["parameters"])
    if parameter_hash != EXPECTED_REGISTRY[key][2]:
        raise RuntimeError(f"{key}_FROZEN_PARAMETER_HASH_MISMATCH")
    params = replace(PARAMETERS[key], **registry["parameters"])
    pieces = []
    for instrument, alias in INSTRUMENTS:
        candles = loaded[alias]
        spec = get_instrument_spec(alias)
        if key == "T2":
            raw = _OOST2(params).run(candles, alias, tick_size=spec.price_precision)
        else:
            context = causal_h1_context(candles)
            if len(context) and any(context.index > candles.index[-1]):
                raise RuntimeError("M15_TRUE_OOS_LOOK_AHEAD")
            raw = Backtester(FixedRiskPortfolio(), tick_size=spec.price_precision,
                             allow_true_oos=True).run(T3MTFTrend(params), alias, candles, context).trades
            raw = _normalize_backtester(raw, key)
        frame = raw.copy()
        if frame.empty:
            continue
        reject_pre_oos(frame.entry_time); reject_pre_oos(frame.exit_time)
        frame["instrument"], frame["strategy"], frame["timeframe"] = instrument, key, TIMEFRAME
        frame["net_R"] = frame.gross_R.astype(float) - 2 * COST_TICKS_PER_SIDE / frame.initial_risk_ticks.astype(float)
        frame["trade_id"] = [f"{key}-M15-TRUE-OOS-{alias}-{i:06d}" for i in range(1, len(frame) + 1)]
        pieces.append(frame)
    result = pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame(columns=TRADE_COLUMNS)
    if stable_hash(registry["parameters"]) != parameter_hash:
        raise RuntimeError(f"{key}_FROZEN_PARAMETERS_MODIFIED")
    return result.sort_values(["entry_time", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)


def _metric(frame: pd.DataFrame) -> dict[str, Any]:
    values = frame.net_R.astype(float) if len(frame) else pd.Series(dtype=float)
    item = stats(values)
    return {"trades": item["trades"], "PF": finite(item["PF_R"]),
        "expectancy_R": finite(item["expectancy"]), "net_R": item["net_R"],
        "max_drawdown_R": item["max_DD_R"], "recovery_factor": finite(item["recovery_factor"]),
        "win_rate": finite(item["winrate"]), "average_win": finite(item["average_win_R"]),
        "average_loss": finite(item["average_loss_R"]), "max_winning_streak": item["max_winning_streak"],
        "max_losing_streak": item["max_losing_streak"]}


def bootstrap(values: pd.Series) -> dict[str, Any]:
    """Canonical Phase 5 deterministic trade bootstrap."""
    x = np.asarray(values, dtype=np.float64)
    empty = {k: None for k in ("mean_R_2.5%", "mean_R_5%", "mean_R_50%", "mean_R_95%",
                                "mean_R_97.5%", "probability_mean_R_gt_0")}
    if not len(x):
        return {"iterations": BOOTSTRAP_ITERATIONS, "seed": BOOTSTRAP_SEED, "trades": 0, **empty}
    means = np.random.default_rng(BOOTSTRAP_SEED).choice(
        x, size=(BOOTSTRAP_ITERATIONS, len(x)), replace=True).mean(axis=1)
    q = np.quantile(means, [.025, .05, .5, .95, .975])
    return {"iterations": BOOTSTRAP_ITERATIONS, "seed": BOOTSTRAP_SEED, "trades": len(x),
            "mean_R_2.5%": q[0], "mean_R_5%": q[1], "mean_R_50%": q[2],
            "mean_R_95%": q[3], "mean_R_97.5%": q[4],
            "probability_mean_R_gt_0": float((means > 0).mean())}


def classify(metrics: Mapping[str, Any], quarters: list[dict], instruments: list[dict],
             directions: list[dict], boot: Mapping[str, Any], conc: Mapping[str, Any]) -> str:
    """Apply the frozen H1 Phase 5 PASS/FAIL/BORDERLINE thresholds."""
    observed = [row for row in quarters if row["trades"]]
    fraction = sum((row["expectancy_R"] or 0) > 0 for row in observed) / len(observed) if observed else 0
    expectancy = metrics["expectancy_R"] or 0
    probability = boot["probability_mean_R_gt_0"] or 0
    passing = (metrics["trades"] >= 50 and expectancy > 0
               and probability >= .95 and fraction >= .60
               and all(row["expectancy_R"] >= 0 for row in instruments + directions if row["trades"])
               and conc["net_R_without_top5"] > 0)
    failing = expectancy <= 0 or probability <= .50
    return "PASS" if passing else ("FAIL" if failing else "BORDERLINE")


def _svg(path: Path, values: list[float], title: str, *, cumulative: bool = False) -> None:
    series = pd.Series(values, dtype=float)
    if cumulative: series = series.cumsum()
    width, height, pad = 800, 360, 48
    if len(series):
        lo, hi = min(float(series.min()), 0.0), max(float(series.max()), 0.0)
        span = hi - lo or 1.0
        points = " ".join(f"{pad + i * (width - 2*pad) / max(1, len(series)-1):.2f},{height-pad-(v-lo)*(height-2*pad)/span:.2f}" for i, v in enumerate(series))
    else: points = ""
    body = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
            '<rect width="100%" height="100%" fill="white"/>'
            f'<text x="{pad}" y="28" font-family="sans-serif" font-size="18">{html.escape(title)}</text>'
            f'<polyline points="{points}" fill="none" stroke="#2458a6" stroke-width="2"/>'
            f'<text x="{pad}" y="{height-12}" font-family="sans-serif" font-size="12">deterministic trade order</text></svg>\n')
    path.write_text(body, encoding="utf-8")


def _reports(target: Path, key: str, registry: dict, trades: pd.DataFrame) -> dict:
    target.mkdir(parents=True)
    _csv(target / "trades.csv", trades)
    metrics = {"candidate_id": registry["candidate_id"], "baseline_candidate_id": registry["baseline_candidate_id"],
        "configuration_id": registry["configuration_id"],
        "parameter_hash": registry["parameter_hash"], "initial_state": "FLAT", "resets": 0,
        "continuous_period": True, "cost_ticks_per_side": COST_TICKS_PER_SIDE, **_metric(trades)}
    _csv(target / "period_summary.csv", [{"period_id": "TRUE_OOS", "start": "2025-01-01",
        "end": None, "initial_state": "FLAT", "resets": 0, **_metric(trades)}])
    group = lambda column, value: _metric(trades.loc[trades[column].eq(value)])
    instruments = [{"instrument": name, **group("instrument", name)} for name, _ in INSTRUMENTS]
    directions = [{"direction": value, **group("direction", value)} for value in ("LONG", "SHORT")]
    _csv(target / "instrument_report.csv", instruments); _csv(target / "direction_report.csv", directions)
    exits = pd.to_datetime(trades.exit_time, utc=True) if len(trades) else pd.Series(dtype="datetime64[ns, UTC]")
    years = exits.dt.year
    quarters_value = exits.dt.year.astype(str) + "Q" + (((exits.dt.month - 1) // 3) + 1).astype(str)
    yearly_frame, quarterly_frame = trades.assign(year=years), trades.assign(quarter=quarters_value)
    yearly = [{"year": int(year), **_metric(yearly_frame.loc[yearly_frame.year.eq(year)])} for year in sorted(years.unique())]
    quarterly = [{"quarter": quarter, **_metric(quarterly_frame.loc[quarterly_frame.quarter.eq(quarter)])} for quarter in sorted(quarters_value.unique())]
    _csv(target / "yearly_report.csv", yearly); _csv(target / "quarterly_report.csv", quarterly)
    conc = concentration(trades.net_R if len(trades) else pd.Series(dtype=float))
    _csv(target / "concentration_report.csv", [conc])
    excursions = []
    for label, sample in (("ALL", trades), ("WINNERS", trades.loc[trades.net_R > 0]), ("LOSERS", trades.loc[trades.net_R <= 0])):
        excursions.append({"group": label, "trades": len(sample), **{f"{name}_{stat}":
            (finite(getattr(sample[name].astype(float), stat)()) if len(sample) else None)
            for name in ("MAE_R", "MFE_R") for stat in ("mean", "median", "min", "max")}})
    _csv(target / "mae_mfe_report.csv", excursions)
    boot = bootstrap(trades.net_R if len(trades) else pd.Series(dtype=float))
    _csv(target / "bootstrap_report.csv", [boot])
    classification = classify(metrics, quarterly, instruments, directions, boot, conc)
    observed = [row for row in quarterly if row["trades"]]
    metrics.update({"bootstrap_probability_mean_R_gt_0": boot["probability_mean_R_gt_0"],
                    "positive_quarters": sum(row["expectancy_R"] > 0 for row in observed),
                    "observed_quarters": len(observed), "net_R_without_top5": conc["net_R_without_top5"],
                    "classification": classification})
    _json(target / "metrics.json", metrics)
    _svg(target / "equity_curve.svg", trades.net_R.tolist(), f"{registry['candidate_id']} TRUE OOS equity (R)", cumulative=True)
    ordered = sorted(trades.net_R.astype(float).tolist()) if len(trades) else []
    _svg(target / "r_distribution.svg", ordered, f"{registry['candidate_id']} R distribution")
    (target / "final_report.md").write_text(
        f"# {registry['candidate_id']} — M15 TRUE OOS\n\n**Classification: {classification}**\n\n"
        "One continuous 2025+ period, initialized FLAT with no internal reset. Parameters are loaded from the "
        "frozen registry; no retraining, optimization, ranking, selection, filters, or parameter changes occur.\n\n"
        f"Pre-OOS Walk Forward verdict: {PRE_OOS_VERDICTS[key]}.\n\nTrades: {metrics['trades']}; PF: {metrics['PF']}; expectancy: {metrics['expectancy_R']} R; net: {metrics['net_R']} R.\n",
        encoding="utf-8")
    return metrics


def artifact_sha256(root: Path, *, exclude_manifest: bool = True) -> dict[str, str]:
    return {path.relative_to(root).as_posix(): _sha(path) for path in sorted(Path(root).rglob("*"))
            if path.is_file() and not (exclude_manifest and path.relative_to(root).as_posix() == "manifest.json")}


def run(data_root: Path = APPROVED_DATA_ROOT, output: Path = OUTPUT,
        registry_root: Path = FROZEN_REGISTRY, walk_forward: Path = WALK_FORWARD) -> dict[str, Any]:
    """Run the locked validation. No strategy or parameter arguments exist."""
    _assert_execution_only(); verify_frozen_strategies()
    prerequisites = ((BASELINE, "PHASE_M15_BASELINE_COMPLETE"),
                     (Path(registry_root), "PHASE_M15_OPTIMIZATION_COMPLETE"),
                     (ROBUSTNESS, "PHASE_M15_ROBUSTNESS_COMPLETE"),
                     (Path(walk_forward), "PHASE_M15_WALK_FORWARD_COMPLETE"))
    for root, expected in prerequisites:
        if json.loads((root / "manifest.json").read_text(encoding="utf-8")).get("status") != expected:
            raise RuntimeError(f"M15_PREREQUISITE_INVALID:{root}")
    registries = load_frozen_registry(Path(registry_root), Path(walk_forward))
    protected = (BASELINE, Path(registry_root), ROBUSTNESS, Path(walk_forward))
    before = {str(path): hash_tree(path) for path in protected}
    loaded, coverage = {}, []
    for instrument, alias in INSTRUMENTS:
        frame, paths = load_true_oos(Path(data_root), alias)
        loaded[alias] = frame
        coverage.append({"instrument": instrument, "alias": alias, "bars": len(frame),
            "first_close": frame.index.min().isoformat(), "last_close": frame.index.max().isoformat(),
            "files": [{"name": path.name, "sha256": _sha(path)} for path in paths]})
    output = Path(output)
    if output.exists(): shutil.rmtree(output)
    output.mkdir(parents=True)
    summaries = {key: _reports(output / key, key, registries[key], execute_candidate(key, registries[key], loaded))
                 for key in ("T2", "T3")}
    if before != {str(path): hash_tree(path) for path in protected}:
        raise RuntimeError("M15_TRUE_OOS_FROZEN_ARTIFACT_MUTATION")
    comparison = []
    for key in ("T2", "T3"):
        development = json.loads((ROBUSTNESS / key / "metrics.json").read_text(encoding="utf-8"))
        forward = json.loads((Path(walk_forward) / key / "aggregate_metrics.json").read_text(encoding="utf-8"))
        oos = summaries[key]
        comparison.append({"candidate_id": registries[key]["candidate_id"],
            **{f"development_{name}": development[name] for name in ("trades", "PF", "expectancy_R", "net_R", "max_drawdown_R")},
            **{f"walk_forward_{name}": forward[name] for name in ("trades", "PF", "expectancy_R", "net_R", "max_drawdown_R")},
            **{f"true_oos_{name}": oos[name] for name in ("trades", "PF", "expectancy_R", "net_R", "max_drawdown_R")},
            "PF_decay_development_to_true_oos": None if development["PF"] is None or oos["PF"] is None else oos["PF"] - development["PF"],
            "expectancy_decay_development_to_true_oos": None if oos["expectancy_R"] is None else oos["expectancy_R"] - development["expectancy_R"],
            "drawdown_change_walk_forward_to_true_oos": abs(oos["max_drawdown_R"]) - abs(forward["max_drawdown_R"])})
    _csv(output / "comparison.csv", comparison)
    (output / "final_true_oos_report.md").write_text(
        "# M15 TRUE OOS Validation\n\n" + "\n".join(
            f"- **{registries[k]['candidate_id']}: {summaries[k]['classification']}** (pre-OOS: {PRE_OOS_VERDICTS[k]})"
            for k in ("T2", "T3")) +
        "\n\nCandidates were evaluated independently and are not ranked or reselected.\n\nPHASE_M15_TRUE_OOS_COMPLETE\n",
        encoding="utf-8")
    manifest = {"phase": PHASE, "status": STATUS, "timeframe": TIMEFRAME,
        "development_period": DEVELOPMENT_PERIOD, "true_oos_period": TRUE_OOS_PERIOD,
        "candidate_ids": EVALUATED_CANDIDATES, "baseline_candidate_ids": ALLOWED_CANDIDATES,
        "configuration_ids": {k: registries[k]["configuration_id"] for k in registries},
        "parameter_hashes": {k: registries[k]["parameter_hash"] for k in registries},
        "candidate_registry_hashes": {k: _sha(Path(registry_root) / k / "candidate_registry.json") for k in registries},
        "walk_forward_manifest_hash": _sha(Path(walk_forward) / "manifest.json"),
        "pre_true_oos_walk_forward_verdicts": PRE_OOS_VERDICTS, "strategy_hashes": STRATEGY_SHA256,
        "classifications": {k: summaries[k]["classification"] for k in summaries},
        "coverage": coverage, "summaries": summaries, "initial_state": "FLAT", "continuous_period": True,
        "internal_resets": 0, "retraining": False, "optimization": False, "ranking": False,
        "selection": False, "parameters_frozen": True, "parameter_change": False,
        "true_oos_isolated": True, "development_rows_read": 0, "deterministic": True,
        "cost_model": {"name": "H1_C1", "cost_ticks_per_side": COST_TICKS_PER_SIDE,
                       "round_trip_ticks": 2 * COST_TICKS_PER_SIDE, "slippage_ticks_per_side": 0.0},
        "bootstrap": {"iterations": BOOTSTRAP_ITERATIONS, "seed": BOOTSTRAP_SEED},
        "protected_artifact_hashes_before": before,
        "protected_artifacts_unchanged": True}
    _json(output / "manifest.json", manifest)
    manifest["artifact_sha256"] = artifact_sha256(output)
    _json(output / "manifest.json", manifest)
    return manifest
