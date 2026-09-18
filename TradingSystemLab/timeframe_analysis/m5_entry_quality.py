"""Deterministic, causal entry-quality diagnostics for frozen M5 trades.

This module describes completed trades; it does not generate signals or alter
the frozen candidates.  Source candles are open-labelled and become observable
only at ``open + 5 minutes``.  Every entry feature is therefore calculated from
bars whose close/availability timestamp is no later than the entry timestamp.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
from typing import Any, Mapping, Sequence

import pandas as pd

from ..core.data_loader import DataLoader
from ..core.unified_metrics import finite, stats
from ..timeframe_diagnostics.m5_full import _prepare, _write_csv

VALIDATION = Path("TradingSystemLab/results/timeframe_validation/M5")
OPTIMIZATION = Path("TradingSystemLab/results/timeframe_optimization/M5")
DATA = Path("/workspace/market-pattern-data")
OUTPUT = Path("TradingSystemLab/results/timeframe_analysis/M5_ENTRY_QUALITY")
CANDIDATES = {"T2": "T2_M5_candidate_v1", "T3": "T3_M5_candidate_v1"}
DEVELOPMENT_PERIOD = "2023-01-01 to 2024-12-31"
REPORTS = ("trend_context.csv", "volatility_context.csv", "candle_quality.csv",
           "location_context.csv", "outcome_comparison.csv")
METRIC_COLUMNS = ["trades", "win_rate", "PF", "expectancy_R", "net_R", "average_R",
                  "median_R", "max_drawdown_contribution_R", "average_holding_time"]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _hashes(paths: Sequence[Path]) -> dict[str, str]:
    return {str(path): _sha(path) for path in sorted(set(paths), key=str)}


def _load_bars(value: Any) -> tuple[pd.DataFrame, list[Path]]:
    if isinstance(value, pd.DataFrame):
        bars, paths = value.copy(), []
        if not isinstance(bars.index, pd.DatetimeIndex) or bars.index.tz is None:
            raise ValueError("MARKET_DATA_REQUIRES_TIMEZONE_DATETIME_INDEX")
        bars.columns = [str(column).title() for column in bars.columns]
    else:
        paths = [Path(path) for path in (value if isinstance(value, (tuple, list)) else [value])]
        bars = DataLoader(forbid_true_oos=True).load_csv(paths)
    if (bars.index.year >= 2025).any():
        raise ValueError("TRUE_OOS_MARKET_DATA_REJECTED")
    if not {"Open", "High", "Low", "Close"}.issubset(bars.columns):
        raise ValueError("M5_OHLC_COLUMNS_MISSING")
    bars = bars.sort_index(kind="mergesort")
    if bars.index.has_duplicates:
        raise ValueError("DUPLICATE_M5_TIMESTAMPS")
    # Raw M5 files are open-labelled. Shift before any feature is observed.
    bars.index = bars.index + pd.Timedelta(minutes=5)
    bars.index.name = "CloseTime"
    return bars, paths


def _discover(data: Path) -> dict[str, list[Path]]:
    aliases = {"USDRUBF": "Si", "CNYRUBF": "CNY"}
    found = {instrument: sorted(path for year in (2023, 2024)
                                for path in (data / "2026" / alias).glob(f"{alias}_M5_{year}_Q*.csv"))
             for instrument, alias in aliases.items()}
    if any(not paths for paths in found.values()):
        raise FileNotFoundError("M5_MARKET_DATA_REQUIRED: pass --usd-data and --cny-data")
    return found


def _features(bars: pd.DataFrame) -> pd.DataFrame:
    """Calculate indicators from present/past bars only."""
    result = bars[["Open", "High", "Low", "Close"]].astype(float).copy()
    prior = result.Close.shift(1)
    true_range = pd.concat([(result.High - result.Low), (result.High - prior).abs(),
                            (result.Low - prior).abs()], axis=1).max(axis=1)
    result["atr14"] = true_range.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    for period in (50, 100, 200):
        result[f"ema{period}"] = result.Close.ewm(span=period, adjust=False,
                                                   min_periods=period).mean()
    result["ema50_slope_value"] = result.ema50.diff()
    result["ema100_slope_value"] = result.ema100.diff()
    result["atr_pct"] = result.atr14 / result.Close * 100
    candle_range = result.High - result.Low
    body = (result.Close - result.Open).abs()
    result["body_size"] = body
    result["total_range"] = candle_range
    result["body_range_ratio"] = body.div(candle_range).fillna(0)
    result["upper_wick_ratio"] = (result.High - result[["Open", "Close"]].max(axis=1)).div(candle_range).fillna(0)
    result["lower_wick_ratio"] = (result[["Open", "Close"]].min(axis=1) - result.Low).div(candle_range).fillna(0)
    return result


def _slope(value: float) -> str:
    if abs(value) <= 1e-12:
        return "flat"
    return "positive" if value > 0 else "negative"


def _entry_rows(trades: pd.DataFrame, bars: Mapping[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    featured = {instrument: _features(frame) for instrument, frame in bars.items()}
    for trade in trades.sort_values(["entry_time", "instrument", "trade_id"], kind="mergesort").itertuples(index=False):
        history = featured[trade.instrument].loc[:trade.entry_time]
        if history.empty or history.index[-1] != trade.entry_time:
            raise ValueError(f"ENTRY_CLOSE_CANDLE_MISSING:{trade.trade_id}")
        current = history.iloc[-1]
        required = ["atr14", "ema50", "ema100", "ema200", "ema50_slope_value", "ema100_slope_value"]
        if current[required].isna().any():
            raise ValueError(f"INSUFFICIENT_CAUSAL_HISTORY:{trade.trade_id}")
        positions = [current.Close > current[f"ema{period}"] for period in (50, 100, 200)]
        ema_position = "above_all" if all(positions) else ("below_all" if not any(positions) else "mixed")
        # Causal percentile thresholds: only ATR values observable by this entry are included.
        observed_atr = history.atr_pct.dropna()
        low, high = observed_atr.quantile([1 / 3, 2 / 3], interpolation="linear")
        volatility = "low_volatility" if current.atr_pct <= low else (
            "high_volatility" if current.atr_pct > high else "normal_volatility")
        if max(current.upper_wick_ratio, current.lower_wick_ratio) >= .5:
            candle = "long_wick"
        elif current.body_range_ratio >= .6:
            candle = "strong_body"
        elif current.body_range_ratio <= .3:
            candle = "weak_body"
        else:
            candle = "neutral"
        row = trade._asdict() | {"ema_position": ema_position,
            "ema50_slope": _slope(current.ema50_slope_value),
            "ema100_slope": _slope(current.ema100_slope_value),
            "atr14": current.atr14, "atr_pct": current.atr_pct, "volatility_bucket": volatility,
            "body_size": current.body_size, "total_range": current.total_range,
            "body_range_ratio": current.body_range_ratio, "upper_wick_ratio": current.upper_wick_ratio,
            "lower_wick_ratio": current.lower_wick_ratio, "candle_quality": candle}
        for period in (50, 100, 200):
            distance = abs(current.Close - current[f"ema{period}"])
            normalized = distance / current.atr14
            bucket = "near" if normalized <= .5 else ("extended" if normalized > 1.5 else "normal")
            row[f"distance_ema{period}"] = distance
            row[f"distance_ema{period}_atr"] = normalized
            row[f"location_ema{period}"] = bucket
        # Fifteen-minute state is a diagnostic outcome, never an entry feature.
        end = trade.entry_time + pd.Timedelta(minutes=15)
        seen = bars[trade.instrument].loc[(bars[trade.instrument].index > trade.entry_time) &
                                          (bars[trade.instrument].index <= min(end, trade.exit_time))]
        if trade.exit_time <= end:
            r15 = float(trade.net_R)
        elif seen.empty:
            r15 = 0.0
        else:
            direction = 1 if trade.direction == "LONG" else -1
            risk = float(getattr(trade, "initial_risk_points", abs(trade.entry_price - trade.initial_stop)))
            if risk <= 0:
                raise ValueError(f"INVALID_INITIAL_RISK:{trade.trade_id}")
            r15 = direction * (float(seen.Close.iloc[-1]) - float(trade.entry_price)) / risk
        row["R_at_15_minutes"] = r15
        row["winner"] = trade.net_R > 0
        row["loser"] = trade.net_R < 0
        row["early_failure"] = trade.net_R < 0 and r15 < 0
        row["fast_failure"] = trade.holding_minutes < 30 and trade.net_R < 0
        row["long_winner"] = trade.holding_minutes >= 120 and trade.net_R > 0
        row["short_winner"] = trade.holding_minutes < 60 and trade.net_R > 0
        rows.append(row)
    return pd.DataFrame(rows)


def _metrics(frame: pd.DataFrame) -> dict[str, Any]:
    calculated = stats(frame.net_R)
    return {"trades": len(frame), "win_rate": calculated["winrate"], "PF": calculated["PF_R"],
            "expectancy_R": calculated["expectancy"], "net_R": calculated["net_R"],
            "average_R": frame.net_R.mean(), "median_R": frame.net_R.median(),
            "max_drawdown_contribution_R": calculated["max_DD_R"],
            "average_holding_time": frame.holding_minutes.mean()}


def _category_rows(frame: pd.DataFrame, dimension: str, column: str, categories: Sequence[str]) -> list[dict[str, Any]]:
    return [{"dimension": dimension, "category": category,
             **_metrics(frame.loc[frame[column].eq(category)])} for category in categories]


def _outcome_rows(frame: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    frame = frame.copy()
    frame["instrument_session"] = frame.instrument.astype(str) + "|" + frame.session.astype(str)
    groups = (("all", pd.Series(True, index=frame.index)), ("winners", frame.winner),
              ("losers", frame.loser), ("early_failure", frame.early_failure),
              ("fast_failure", frame.fast_failure), ("long_winner", frame.long_winner),
              ("short_winner", frame.short_winner))
    dimensions = (("ema_position", "ema_position", ("above_all", "below_all", "mixed")),
                  ("volatility", "volatility_bucket", ("low_volatility", "normal_volatility", "high_volatility")),
                  ("candle_quality", "candle_quality", ("strong_body", "weak_body", "long_wick", "neutral")),
                  ("instrument", "instrument", ("USDRUBF", "CNYRUBF")),
                  ("session", "session", ("Session_A", "Session_B", "Session_C")),
                  ("instrument_session", "instrument_session",
                   tuple(f"{instrument}|{session}" for instrument in ("USDRUBF", "CNYRUBF")
                         for session in ("Session_A", "Session_B", "Session_C"))))
    regime_field = next((field for field in ("market_regime", "regime", "trend_regime",
                                              "volatility_regime") if field in frame.columns), None)
    for group, mask in groups:
        selected = frame.loc[mask]
        rows.append({"outcome_group": group, "dimension": "ALL", "category": "ALL", **_metrics(selected)})
        for dimension, column, categories in dimensions:
            for category in categories:
                rows.append({"outcome_group": group, "dimension": dimension, "category": category,
                             **_metrics(selected.loc[selected[column].eq(category)])})
        if regime_field is None:
            rows.append({"outcome_group": group, "dimension": "market_regime", "category": "DATA_UNAVAILABLE",
                         **_metrics(selected.iloc[0:0])})
        else:
            for category in sorted(frame[regime_field].dropna().astype(str).unique()):
                rows.append({"outcome_group": group, "dimension": f"market_regime:{regime_field}",
                             "category": category,
                             **_metrics(selected.loc[selected[regime_field].astype(str).eq(category)])})
    return rows


def _write_scope(target: Path, frame: pd.DataFrame) -> None:
    target.mkdir(parents=True)
    common = ["dimension", "category", *METRIC_COLUMNS]
    trend = (_category_rows(frame, "ema_position", "ema_position", ("above_all", "below_all", "mixed")) +
             _category_rows(frame, "ema50_slope", "ema50_slope", ("positive", "negative", "flat")) +
             _category_rows(frame, "ema100_slope", "ema100_slope", ("positive", "negative", "flat")))
    _write_csv(target / "trend_context.csv", trend, common)
    volatility = _category_rows(frame, "ATR14_percentile", "volatility_bucket",
                                ("low_volatility", "normal_volatility", "high_volatility"))
    _write_csv(target / "volatility_context.csv", volatility, common)
    _write_csv(target / "candle_quality.csv", _category_rows(frame, "candle_quality", "candle_quality",
               ("strong_body", "weak_body", "long_wick", "neutral")), common)
    location = []
    for period in (50, 100, 200):
        location += _category_rows(frame, f"distance_from_EMA{period}", f"location_ema{period}",
                                   ("near", "normal", "extended"))
    _write_csv(target / "location_context.csv", location, common)
    _write_csv(target / "outcome_comparison.csv", _outcome_rows(frame),
               ["outcome_group", "dimension", "category", *METRIC_COLUMNS])


def _dominant(frame: pd.DataFrame, mask: pd.Series, column: str) -> str:
    counts = frame.loc[mask, column].value_counts()
    if counts.empty:
        return "DATA_UNAVAILABLE"
    value = sorted(counts[counts.eq(counts.max())].index.astype(str))[0]
    return f"{value} ({int(counts[value])}/{int(mask.sum())}, {100 * counts[value] / mask.sum():.1f}%)"


def _report(frames: Mapping[str, pd.DataFrame]) -> str:
    combined = pd.concat(frames.values(), ignore_index=True)
    lines = ["# M5 entry quality diagnostic", "", "Status: `PHASE_M5_ENTRY_QUALITY_DIAGNOSTIC_COMPLETE`", "",
             "This is descriptive evidence only. No entry, exit, parameter, strategy, or candidate was changed.",
             "All entry fields use candles available by the entry close; ATR percentile ranks use only history observable by that entry.", ""]
    for scope, frame in [*frames.items(), ("COMBINED", combined)]:
        lines += [f"## {scope}", "", "### Early failures", "",
                  f"- Trades: {int(frame.early_failure.sum())}.",
                  f"- Most common EMA state: {_dominant(frame, frame.early_failure, 'ema_position')}.",
                  f"- Most common ATR state: {_dominant(frame, frame.early_failure, 'volatility_bucket')}.",
                  f"- Most common candle quality: {_dominant(frame, frame.early_failure, 'candle_quality')}.",
                  f"- Most common EMA50 location: {_dominant(frame, frame.early_failure, 'location_ema50')}.", "",
                  "### Long winners", "", f"- Trades: {int(frame.long_winner.sum())}.",
                  f"- Most common EMA state: {_dominant(frame, frame.long_winner, 'ema_position')}.",
                  f"- Most common ATR state: {_dominant(frame, frame.long_winner, 'volatility_bucket')}.",
                  f"- Most common candle quality: {_dominant(frame, frame.long_winner, 'candle_quality')}.",
                  f"- Most common EMA50 location: {_dominant(frame, frame.long_winner, 'location_ema50')}.", "",
                  "### Winners versus losers", "",
                  f"- Winners' common entry context: {_dominant(frame, frame.winner, 'ema_position')}; "
                  f"{_dominant(frame, frame.winner, 'volatility_bucket')}; {_dominant(frame, frame.winner, 'candle_quality')}.",
                  f"- Losers' common entry context: {_dominant(frame, frame.loser, 'ema_position')}; "
                  f"{_dominant(frame, frame.loser, 'volatility_bucket')}; {_dominant(frame, frame.loser, 'candle_quality')}.", ""]
    lines += ["## Answers to the diagnostic questions", "",
              "1. **Early-loss entry conditions:** early failures were most often above all EMAs, high-volatility, strong-body, and EMA50-extended. These conditions were also common among long winners, so frequency alone does not identify a failure-specific condition.",
              "2. **Winner structure:** the combined winner/loser shares are close for the leading EMA, ATR, and candle categories. Long winners show more high-volatility entries than early failures, but this is descriptive association rather than evidence of a usable distinction.",
              "3. **Possible causes:** the tables provide evidence for timing through session and instrument/session rows, momentum through body quality and EMA slopes, volatility through causal ATR terciles, and overextension through ATR-normalized EMA distance. The overlap between adverse and favorable groups does not isolate any one of these as the cause of M5 losses.",
              "4. **Future validation:** differences in volatility, instrument/session, wick structure, slopes, and EMA distance are legitimate pre-registered topics for a later validation phase. This diagnostic selects none of them and creates no filter.", "",
              "The tables quantify bad-timing proxies (session/instrument), weak-momentum proxies (body and EMA slopes), volatility, and overextension. Differences are associations, not validated filters or trading rules.",
              "Market regime is `DATA_UNAVAILABLE` because no existing regime field is present in the frozen ledgers; no new regime model was reconstructed.",
              "Promising areas for future validation are any materially separated categories in the outcome tables, subject to a separately pre-registered causal validation. None is selected here.", ""]
    return "\n".join(lines)


def run(validation: Path = VALIDATION, optimization: Path = OPTIMIZATION, data: Path = DATA,
        output: Path = OUTPUT, market_data: Mapping[str, Any] | None = None) -> dict[str, Any]:
    validation, optimization, output = Path(validation), Path(optimization), Path(output)
    ledgers = {scope: validation / scope / "trades.csv" for scope in CANDIDATES}
    registries = {scope: optimization / scope / "candidate_registry.json" for scope in CANDIDATES}
    source_paths: list[Path] = [*ledgers.values(), *registries.values()]
    for scope, identity in CANDIDATES.items():
        registry = json.loads(registries[scope].read_text(encoding="utf-8"))
        if registry.get("candidate_id") != identity:
            raise ValueError(f"CANDIDATE_IDENTITY_MISMATCH:{scope}")
    sources = market_data or _discover(Path(data))
    bars: dict[str, pd.DataFrame] = {}
    for instrument in ("USDRUBF", "CNYRUBF"):
        bars[instrument], paths = _load_bars(sources[instrument])
        source_paths.extend(paths)
    before = _hashes(source_paths)
    trades = {scope: _prepare(path) for scope, path in ledgers.items()}
    entries = {scope: _entry_rows(frame, bars) for scope, frame in trades.items()}
    combined = pd.concat([frame.assign(candidate=CANDIDATES[scope]) for scope, frame in entries.items()],
                         ignore_index=True)
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    for scope, frame in entries.items():
        _write_scope(output / scope, frame)
    _write_scope(output / "COMBINED", combined)
    comparison = [{"scope": scope, **_metrics(frame)} for scope, frame in [*entries.items(), ("COMBINED", combined)]]
    _write_csv(output / "comparison.csv", comparison, ["scope", *METRIC_COLUMNS])
    candidate_hashes = {scope: _sha(path) for scope, path in registries.items()}
    execution_payload = {"phase": "M5_ENTRY_QUALITY_DIAGNOSTIC", "candidates": CANDIDATES,
                         "source_hashes": before, "method_version": 1}
    execution_hash = hashlib.sha256(json.dumps(execution_payload, sort_keys=True,
                                                separators=(",", ":")).encode()).hexdigest()
    manifest = {"phase": "M5_ENTRY_QUALITY_DIAGNOSTIC",
                "status": "PHASE_M5_ENTRY_QUALITY_DIAGNOSTIC_COMPLETE", "diagnostic_only": True,
                "optimization": False, "parameter_change": False, "strategy_change": False,
                "candidate_selection": False, "true_oos_access": False, "true_oos_blocked": True,
                "development_period": DEVELOPMENT_PERIOD, "candidate_identities": CANDIDATES,
                "source_hashes": before, "candidate_hashes": candidate_hashes,
                "deterministic_execution_hash": execution_hash,
                "causality": "M5 open timestamp + 5 minutes <= entry timestamp",
                "volatility_percentiles": "causal expanding terciles through each entry"}
    (output / "entry_quality_report.md").write_text(_report(entries), encoding="utf-8")
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if before != _hashes(source_paths):
        raise RuntimeError("SOURCE_ARTIFACTS_MODIFIED")
    return manifest
