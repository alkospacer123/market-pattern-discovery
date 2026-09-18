"""One-shot TRUE-OOS replay of the frozen M5 session hypothesis.

All provenance is verified before the first 2025+ source is opened.  This
module deliberately has no search, threshold, ranking, or selection API.
"""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any, Mapping

import pandas as pd

from ..core.backtester import Backtester
from ..core.data_loader import DataLoader
from ..core.instrument_specs import get_instrument_spec
from ..core.portfolio import FixedRiskPortfolio
from ..core.unified_metrics import concentration, finite, stats
from ..multitimeframe.phase71 import APPROVED_DATA_ROOT, COST_TICKS_PER_SIDE, STRATEGY_FILES, STRATEGY_SHA256
from ..multitimeframe.phase73 import hash_tree
from ..optimization.experiment import stable_hash
from ..optimization.phase32 import PARAMETERS, _normalize_backtester
from ..strategies.trend.T2_Trend_Pullback import T2TrendPullback
from ..strategies.trend.T3_MTF_Trend import T3MTFTrend
from ..timeframe_validation.m5_baseline import INSTRUMENTS, TRADE_COLUMNS, causal_four_bar_context

OUTPUT = Path("TradingSystemLab/results/true_oos_validation/M5")
BASELINE = Path("TradingSystemLab/results/timeframe_validation/M5")
OPTIMIZATION = Path("TradingSystemLab/results/timeframe_optimization/M5")
ROBUSTNESS = Path("TradingSystemLab/results/timeframe_analysis/M5_ROBUSTNESS")
WALK_FORWARD = Path("TradingSystemLab/results/walk_forward/M5")
SESSION_RESEARCH = Path("TradingSystemLab/results/timeframe_analysis/M5_SESSION_CANDIDATE")
STATUS = "PHASE_M5_TRUE_OOS_COMPLETE"
OOS_START = pd.Timestamp("2025-01-01", tz="Europe/Moscow")
CANDIDATES = {"T2": "T2_M5_candidate_v1", "T3": "T3_M5_candidate_v1"}
SESSION = {"weekdays": "Monday-Friday", "entry_start_inclusive": "10:00",
           "entry_end_exclusive": "17:00", "timezone": "Europe/Moscow"}
VARIANTS = {"baseline": "M5_BASELINE", "session_candidate": "M5_SESSION_CANDIDATE"}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _csv(path: Path, value: Any) -> None:
    frame = value if isinstance(value, pd.DataFrame) else pd.DataFrame(value)
    frame.map(finite).to_csv(path, index=False, lineterminator="\n", float_format="%.12g", na_rep="")


def artifact_sha256(root: Path, exclude: set[str] | None = None) -> dict[str, str]:
    excluded = exclude or set()
    return {p.relative_to(root).as_posix(): _sha(p) for p in sorted(root.rglob("*"))
            if p.is_file() and p.relative_to(root).as_posix() not in excluded}


def verify_provenance(baseline: Path = BASELINE, optimization: Path = OPTIMIZATION,
                      robustness: Path = ROBUSTNESS, walk_forward: Path = WALK_FORWARD,
                      session_research: Path = SESSION_RESEARCH) -> dict[str, Any]:
    """Freeze every candidate input, or fail before market-data discovery."""
    paths = [baseline / "manifest.json", optimization / "manifest.json",
             robustness / "manifest.json", walk_forward / "manifest.json",
             session_research / "manifest.json"]
    if not all(path.is_file() for path in paths):
        raise RuntimeError("M5_FROZEN_PROVENANCE_MISSING")
    manifests = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    base, opt, robust, wf, session = manifests
    if base.get("status") != "PHASE_M5_BASELINE_COMPLETE":
        raise RuntimeError("M5_BASELINE_PROVENANCE_INVALID")
    if opt.get("status") != "PHASE_M5_OPTIMIZATION_COMPLETE":
        raise RuntimeError("M5_OPTIMIZATION_PROVENANCE_INVALID")
    if robust.get("status") != "PHASE_M5_ROBUSTNESS_COMPLETE":
        raise RuntimeError("M5_ROBUSTNESS_PROVENANCE_INVALID")
    if wf.get("status") != "PHASE_M5_WALK_FORWARD_COMPLETE":
        raise RuntimeError("M5_WALK_FORWARD_PROVENANCE_INVALID")
    if session.get("status") != "PHASE_M5_SESSION_CANDIDATE_COMPLETE":
        raise RuntimeError("M5_SESSION_PROVENANCE_INVALID")
    for name, manifest in (("robustness", robust), ("walk_forward", wf)):
        for flag in ("optimization", "ranking", "parameter_change", "strategy_change", "true_oos_access"):
            if manifest.get(flag, False) is not False:
                raise RuntimeError(f"{name.upper()}_{flag.upper()}_INVALID")
    expected_session = session.get("session_definition", {})
    if (expected_session.get("start_inclusive") != "10:00" or
            expected_session.get("end_exclusive") != "17:00" or
            expected_session.get("weekdays") != ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]):
        raise RuntimeError("M5_SESSION_DEFINITION_CHANGED")
    registries, registry_hashes, parameter_hashes = {}, {}, {}
    for key, identity in CANDIDATES.items():
        path = optimization / key / "candidate_registry.json"
        registry = json.loads(path.read_text(encoding="utf-8"))
        if registry.get("candidate_id") != identity:
            raise RuntimeError(f"{key}_FROZEN_CANDIDATE_IDENTITY_MISMATCH")
        if stable_hash(registry.get("parameters", {})) != registry.get("parameter_hash"):
            raise RuntimeError(f"{key}_FROZEN_PARAMETER_HASH_MISMATCH")
        strategy_path = Path("TradingSystemLab/strategies/trend") / STRATEGY_FILES[key]
        if registry.get("strategy_hash") != STRATEGY_SHA256[key] or _sha(strategy_path) != STRATEGY_SHA256[key]:
            raise RuntimeError(f"{key}_FROZEN_STRATEGY_HASH_MISMATCH")
        if robust.get("candidate_identities", {}).get(key) != identity:
            raise RuntimeError(f"{key}_ROBUSTNESS_IDENTITY_MISMATCH")
        registries[key], registry_hashes[key] = registry, _sha(path)
        parameter_hashes[key] = registry["parameter_hash"]
    definition = {"candidate_id": "M5_SESSION_CANDIDATE", "underlying_candidate_ids": CANDIDATES, **SESSION}
    return {"registries": registries, "registry_hashes": registry_hashes,
            "parameter_hashes": parameter_hashes, "candidate_hash": _canonical(definition),
            "manifest_hashes": {path.name if path.parent == baseline else str(path): _sha(path) for path in paths},
            "walk_forward_hash": hash_tree(walk_forward), "robustness_hash": hash_tree(robustness),
            "strategy_hashes": dict(STRATEGY_SHA256), "definition": definition}


def discover_true_oos_files(data_root: Path, alias: str) -> list[Path]:
    root = Path(data_root).resolve()
    if root != APPROVED_DATA_ROOT.resolve():
        raise ValueError("UNAPPROVED_MARKET_DATA_ROOT")
    paths = sorted((root / "2026" / alias).glob(f"{alias}_M5_20*.csv"), key=lambda p: p.name)
    return [p for p in paths if len(p.stem.split("_")) >= 4 and
            p.stem.split("_")[2].isdigit() and int(p.stem.split("_")[2]) >= 2025]


def validate_true_oos_candles(frame: pd.DataFrame) -> None:
    index = frame.index
    if not isinstance(index, pd.DatetimeIndex) or index.tz is None:
        raise ValueError("TRUE_OOS_TIMESTAMP_REQUIRED")
    if not index.is_monotonic_increasing or index.has_duplicates:
        raise ValueError("M5_CANDLE_ORDER_OR_DUPLICATE_VIOLATION")
    local = index.tz_convert("Europe/Moscow")
    if len(local) and local.min() < OOS_START:
        raise ValueError("DEVELOPMENT_DATA_IN_TRUE_OOS")
    if not ((local.minute % 5 == 0) & local.second.eq(0) if hasattr(local.second, "eq") else
            ((local.minute % 5 == 0) & (local.second == 0))).all():
        raise ValueError("M5_TIMEFRAME_VIOLATION")


def load_true_oos(data_root: Path, alias: str) -> tuple[pd.DataFrame, list[Path]]:
    paths = discover_true_oos_files(data_root, alias)
    if not paths:
        raise FileNotFoundError(f"no TRUE OOS M5 data for {alias}")
    loader = DataLoader(forbid_true_oos=False)
    pieces = [loader._read(path) for path in paths]
    opened = pd.concat(pieces)
    if not opened.index.is_monotonic_increasing or opened.index.has_duplicates:
        raise ValueError("M5_CANDLE_ORDER_OR_DUPLICATE_VIOLATION")
    frame = loader.close_index(opened, "5min")
    validate_true_oos_candles(frame)
    return frame, paths


def _eligible(timestamp: pd.Timestamp) -> bool:
    stamp = timestamp.tz_convert("Europe/Moscow")
    return stamp.weekday() < 5 and 10 <= stamp.hour < 17


class _OOST2(T2TrendPullback):
    @staticmethod
    def _validate(frame: pd.DataFrame) -> None:
        validate_true_oos_candles(frame)


class _SessionT2(_OOST2):
    def is_confirmation(self, bar: pd.Series, previous: pd.Series, direction: str) -> bool:
        return _eligible(bar.name) and super().is_confirmation(bar, previous, direction)


class _SessionT3(T3MTFTrend):
    def generate_signal(self, bar: pd.Series, regime: str | None) -> str | None:
        return super().generate_signal(bar, regime) if _eligible(bar.name) else None


def _execute(key: str, registry: dict, alias: str, bars: pd.DataFrame, session: bool) -> pd.DataFrame:
    params = replace(PARAMETERS[key], **registry["parameters"])
    tick = get_instrument_spec(alias).price_precision
    if key == "T2":
        raw = (_SessionT2 if session else _OOST2)(params).run(bars, alias, tick_size=tick)
    else:
        strategy = _SessionT3(params) if session else T3MTFTrend(params)
        raw = Backtester(FixedRiskPortfolio(), cost_ticks_per_side=0, tick_size=tick,
                         allow_true_oos=True).run(strategy, alias, bars, causal_four_bar_context(bars)).trades
        raw = _normalize_backtester(raw, key)
    if raw.empty:
        return pd.DataFrame(columns=TRADE_COLUMNS)
    frame = raw.copy()
    frame["instrument"] = "USDRUBF" if alias == "Si" else "CNYRUBF"
    frame["strategy"], frame["timeframe"] = key, "M5"
    frame["net_R"] = frame.gross_R.astype(float) - 2 * COST_TICKS_PER_SIDE / frame.initial_risk_ticks.astype(float)
    marker = "SESSION" if session else "BASELINE"
    frame["trade_id"] = [f"{key}-M5-OOS-{marker}-{alias}-{n:06d}" for n in range(1, len(frame) + 1)]
    if (pd.to_datetime(frame.entry_time, utc=True) < OOS_START.tz_convert("UTC")).any():
        raise RuntimeError("DEVELOPMENT_TRADE_IN_TRUE_OOS")
    if session and not pd.to_datetime(frame.entry_time).map(_eligible).all():
        raise RuntimeError("SESSION_ENTRY_VIOLATION")
    return frame.sort_values(["exit_time", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)


def _metrics(frame: pd.DataFrame) -> dict[str, Any]:
    values = frame.net_R.astype(float) if len(frame) else pd.Series(dtype=float)
    metric, conc = stats(values), concentration(values)
    holding = ((pd.to_datetime(frame.exit_time, utc=True) - pd.to_datetime(frame.entry_time, utc=True))
               .dt.total_seconds() / 60) if len(frame) else pd.Series(dtype=float)
    return {"trades": metric["trades"], "PF": finite(metric["PF_R"]),
            "expectancy_R": finite(metric["expectancy"]), "net_R": metric["net_R"],
            "max_drawdown_R": metric["max_DD_R"], "recovery_factor": finite(metric["recovery_factor"]),
            "win_rate": finite(metric["winrate"]), "average_holding_minutes": finite(holding.mean()),
            "losing_streak": metric["max_losing_streak"],
            "average_MAE_R": finite(frame.MAE_R.astype(float).mean()) if len(frame) else None,
            "average_MFE_R": finite(frame.MFE_R.astype(float).mean()) if len(frame) else None,
            "top_1_positive_R_concentration": conc["top_1_positive_R_share"],
            "top_5_positive_R_concentration": conc["top_5_positive_R_share"],
            "net_R_without_top5": conc["net_R_without_top5"],
            "PF_without_top5": conc["PF_R_C1_without_top5"]}


def _groups(frame: pd.DataFrame, column: str, values: list[Any]) -> list[dict]:
    return [{column: value, **_metrics(frame.loc[frame[column].eq(value)])} for value in values]


def _wf_metrics(walk_forward: Path, key: str) -> dict[str, Any]:
    pieces = []
    for fold in ("WF01", "WF02", "WF03"):
        frame = pd.read_csv(walk_forward / "session_candidate" / fold / "test_trades.csv")
        pieces.append(frame.loc[frame.strategy.eq(key)])
    combined = pd.concat(pieces, ignore_index=True)
    return _metrics(combined)


def _write_reports(target: Path, frame: pd.DataFrame, key: str, variant: str,
                   walk_forward: Path | None = None, days: float = 1) -> dict[str, Any]:
    target.mkdir(parents=True)
    frame = frame.sort_values(["exit_time", "strategy", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)
    _csv(target / "trades.csv", frame)
    metric = _metrics(frame); _json(target / "metrics.json", metric)
    exits = pd.to_datetime(frame.exit_time, utc=True)
    dated = frame.assign(year=exits.dt.year, month=exits.dt.strftime("%Y-%m"))
    _csv(target / "instrument_report.csv", _groups(frame, "instrument", ["USDRUBF", "CNYRUBF"]))
    _csv(target / "direction_report.csv", _groups(frame, "direction", ["LONG", "SHORT"]))
    _csv(target / "yearly_report.csv", _groups(dated, "year", sorted(dated.year.unique().tolist())))
    _csv(target / "monthly_report.csv", _groups(dated, "month", sorted(dated.month.unique().tolist())))
    _csv(target / "concentration_report.csv", [{k: metric[k] for k in
        ("top_1_positive_R_concentration", "top_5_positive_R_concentration", "net_R_without_top5", "PF_without_top5")}])
    excursion = [{"statistic": label,
        "MAE_R": finite(frame.MAE_R.astype(float).quantile(q)) if len(frame) else None,
        "MFE_R": finite(frame.MFE_R.astype(float).quantile(q)) if len(frame) else None}
        for label, q in (("minimum", 0), ("p25", .25), ("median", .5), ("p75", .75), ("maximum", 1))]
    _csv(target / "mae_mfe_report.csv", excursion)
    if walk_forward is not None:
        if key == "COMBINED":
            wf_parts = [_wf_metrics(walk_forward, item) for item in ("T2", "T3")]
            ledgers = [pd.read_csv(walk_forward / "session_candidate" / fold / "test_trades.csv")
                       for fold in ("WF01", "WF02", "WF03")]
            wf = _metrics(pd.concat(ledgers, ignore_index=True))
        else:
            wf = _wf_metrics(walk_forward, key)
        oos_frequency = metric["trades"] / days * 365.2425
        wf_frequency = wf["trades"] / (365.25 * 1.5) * 365.2425
        decay = {"walk_forward_expectancy_R": wf["expectancy_R"], "true_oos_expectancy_R": metric["expectancy_R"],
                 "expectancy_decay_R": None if metric["expectancy_R"] is None or wf["expectancy_R"] is None else metric["expectancy_R"] - wf["expectancy_R"],
                 "walk_forward_PF": wf["PF"], "true_oos_PF": metric["PF"],
                 "PF_decay": None if metric["PF"] is None or wf["PF"] is None else metric["PF"] - wf["PF"],
                 "walk_forward_max_drawdown_R": wf["max_drawdown_R"], "true_oos_max_drawdown_R": metric["max_drawdown_R"],
                 "drawdown_expansion_R": abs(metric["max_drawdown_R"]) - abs(wf["max_drawdown_R"]),
                 "walk_forward_trades_per_year": wf_frequency, "true_oos_trades_per_year": oos_frequency,
                 "trade_frequency_decay_per_year": oos_frequency - wf_frequency}
        _csv(target / "decay_report.csv", [decay])
    (target / "final_report.md").write_text(
        f"# {variant} — {key}\n\nFrozen TRUE OOS replay: {metric['trades']} trades, "
        f"PF {metric['PF']}, expectancy {metric['expectancy_R']} R, net {metric['net_R']} R.\n\n"
        "Evaluation only; no optimization, ranking, parameter change, or candidate selection.\n", encoding="utf-8")
    return metric


def run(data_root: Path = APPROVED_DATA_ROOT, output: Path = OUTPUT, *,
        baseline: Path = BASELINE, optimization: Path = OPTIMIZATION,
        robustness: Path = ROBUSTNESS, walk_forward: Path = WALK_FORWARD,
        session_research: Path = SESSION_RESEARCH,
        market_data: Mapping[str, pd.DataFrame] | None = None) -> dict[str, Any]:
    # This entire block precedes source discovery/loading by design.
    frozen = verify_provenance(Path(baseline), Path(optimization), Path(robustness),
                               Path(walk_forward), Path(session_research))
    protected = [Path(x) for x in (baseline, optimization, robustness, walk_forward, session_research)]
    before = {str(path): hash_tree(path) for path in protected}
    loaded, source_hashes = {}, []
    for instrument, alias in INSTRUMENTS:
        if market_data is None:
            bars, paths = load_true_oos(Path(data_root), alias)
            files = [{"name": path.name, "sha256": _sha(path)} for path in paths]
        else:
            bars, files = market_data[alias].copy(), []
            validate_true_oos_candles(bars)
        loaded[alias] = bars
        source_hashes.append({"instrument": instrument, "alias": alias, "files": files,
                              "bars": len(bars), "first_close": bars.index.min().isoformat(),
                              "last_close": bars.index.max().isoformat()})
    first, last = min(x.index.min() for x in loaded.values()), max(x.index.max() for x in loaded.values())
    days = max(1.0, (last - first).total_seconds() / 86400 + 1)
    frames: dict[str, dict[str, pd.DataFrame]] = {name: {} for name in VARIANTS}
    for variant in VARIANTS:
        for key in CANDIDATES:
            pieces = [_execute(key, frozen["registries"][key], alias, loaded[alias], variant == "session_candidate")
                      for _, alias in INSTRUMENTS]
            frames[variant][key] = pd.concat(pieces, ignore_index=True).sort_values(
                ["exit_time", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)
        frames[variant]["COMBINED"] = pd.concat([frames[variant][k] for k in CANDIDATES], ignore_index=True).sort_values(
            ["exit_time", "strategy", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)
    output = Path(output)
    if output.exists(): shutil.rmtree(output)
    output.mkdir(parents=True)
    comparison, summaries = [], {}
    for variant, identity in VARIANTS.items():
        summaries[variant] = {}
        for key in ("T2", "T3", "COMBINED"):
            metric = _write_reports(output / variant / key, frames[variant][key], key, identity,
                                    Path(walk_forward) if variant == "session_candidate" else None, days)
            summaries[variant][key] = metric
            comparison.append({"candidate": identity, "scope": key, **metric})
    _csv(output / "comparison.csv", comparison)
    after = {str(path): hash_tree(path) for path in protected}
    if before != after:
        raise RuntimeError("FROZEN_PROVENANCE_MUTATED")
    primary = summaries["session_candidate"]["COMBINED"]
    baseline_metric = summaries["baseline"]["COMBINED"]
    manifest = {"phase": "M5_TRUE_OOS_VALIDATION", "status": STATUS, "timeframe": "M5",
        "primary_candidate": "M5_SESSION_CANDIDATE", "candidate_definition": SESSION,
        "underlying_candidate_ids": CANDIDATES, "frozen_candidate_hashes": {
            **frozen["registry_hashes"], "M5_SESSION_CANDIDATE": frozen["candidate_hash"]},
        "frozen_parameter_hashes": frozen["parameter_hashes"], "walk_forward_artifact_hash": frozen["walk_forward_hash"],
        "robustness_artifact_hash": frozen["robustness_hash"], "strategy_hashes": frozen["strategy_hashes"],
        "true_oos_source_hashes": source_hashes,
        "true_oos_coverage": {"start": first.isoformat(), "end": last.isoformat()},
        "transaction_cost_model": {"cost_ticks_per_side": COST_TICKS_PER_SIDE,
            "round_trip_ticks": 2 * COST_TICKS_PER_SIDE, "slippage_ticks_per_side": 0.0},
        "candidate_frozen_before_oos_read": True, "deterministic": True,
        "optimization_performed": False, "ranking_performed": False, "parameter_change": False,
        "strategy_change": False, "session_change_after_freeze": False,
        "candidate_selection_after_oos": False, "true_oos_access": True,
        "true_oos_used_for_training": False, "true_oos_used_for_optimization": False,
        "true_oos_used_for_selection": False, "protected_artifact_hashes": after}
    report = ["# M5 TRUE OOS Validation", "", "The frozen session candidate is the primary hypothesis; the baseline is descriptive control only.", "",
        f"- Coverage: {first.isoformat()} through {last.isoformat()}",
        f"- M5_BASELINE: {baseline_metric['trades']} trades, PF {baseline_metric['PF']}, expectancy {baseline_metric['expectancy_R']} R, net {baseline_metric['net_R']} R.",
        f"- M5_SESSION_CANDIDATE: {primary['trades']} trades, PF {primary['PF']}, expectancy {primary['expectancy_R']} R, net {primary['net_R']} R.", "",
        "The instrument, direction, yearly, monthly, concentration, MAE/MFE, and frozen walk-forward decay tables answer the preregistered questions without changing the hypothesis.", "",
        "No optimization, ranking, threshold tuning, or candidate reselection was performed. Costs and slippage are unchanged.", "", STATUS, ""]
    (output / "m5_true_oos_report.md").write_text("\n".join(report), encoding="utf-8")
    manifest["artifact_tree_sha256"] = artifact_sha256(output, {"manifest.json"})
    _json(output / "manifest.json", manifest)
    return {"status": STATUS, "coverage": manifest["true_oos_coverage"], "summaries": summaries,
            "artifact_tree_sha256": manifest["artifact_tree_sha256"]}
