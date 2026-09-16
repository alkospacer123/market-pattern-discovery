"""Artifact-producing, TRAIN-only adapter for the BBW CORE v1 engine."""
from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .engine import CoreExecutionError, replay_core_v1
from .models import CoreExecutionConfig

TRAIN_START = pd.Timestamp("2023-01-03")
TRAIN_END_EXCLUSIVE = pd.Timestamp("2025-01-01")
EXPECTED_EXITS = ("INITIAL_STOP", "BREAKEVEN_STOP", "TRAILING_STOP", "TAKE_PROFIT", "END_OF_DATA")
MAX_REASONABLE_DURATION_MINUTES = 24 * 60


def _resolve(root: Path, symbol: str, names: tuple[str, ...]) -> Path:
    for directory in (root, root / symbol, root / "v1", root / symbol / "v1"):
        for name in names:
            path = directory / name
            if path.is_file():
                return path
    raise CoreExecutionError(f"none of {list(names)} found under {root}")


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _load_train_csv(path: Path, label: str) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if "timestamp" not in frame:
        raise CoreExecutionError(f"{label} has no timestamp column")
    timestamps = pd.to_datetime(frame["timestamp"], errors="raise")
    if timestamps.empty or timestamps.min() < TRAIN_START or timestamps.max() >= TRAIN_END_EXCLUSIVE:
        raise CoreExecutionError(
            f"{label} must be wholly inside TRAIN 2023-01-03 through 2024-12-31; "
            "TRUE OOS and pre-TRAIN rows are forbidden"
        )
    return frame


def _metrics(trades: pd.DataFrame) -> dict[str, Any]:
    values = pd.to_numeric(trades.get("result_R", pd.Series(dtype=float)), errors="raise")
    count = len(values)
    wins = float(values[values > 0].sum())
    losses = float(-values[values < 0].sum())
    equity = values.cumsum()
    drawdown = equity.cummax().clip(lower=0) - equity
    maximum_drawdown = float(drawdown.max()) if count else 0.0
    total = float(values.sum()) if count else 0.0
    if count and {"entry_time", "exit_time"}.issubset(trades):
        duration = (pd.to_datetime(trades.exit_time) - pd.to_datetime(trades.entry_time)).dt.total_seconds() / 60
        average_duration = float(duration.mean())
    else:
        average_duration = 0.0
    return {
        "trades": count,
        "winrate": float((values > 0).mean()) if count else 0.0,
        "mean_R": float(values.mean()) if count else 0.0,
        "PF": None if losses == 0 else wins / losses,
        "total_R": total,
        "max_drawdown": maximum_drawdown,
        "recovery_factor": None if maximum_drawdown == 0 else total / maximum_drawdown,
        "average_duration": average_duration,
        "END_OF_DATA_count": int((trades.get("exit_reason", pd.Series(dtype=str)) == "END_OF_DATA").sum()),
    }


def _load_comparison_trades(path: Path, label: str) -> pd.DataFrame:
    trades = pd.read_csv(path)
    required = {"entry_time", "exit_time", "result_R", "exit_reason"}
    if missing := required - set(trades):
        raise CoreExecutionError(f"{label} trades missing columns: {sorted(missing)}")
    for column in ("entry_time", "exit_time"):
        timestamps = pd.to_datetime(trades[column], errors="raise")
        if ((timestamps < TRAIN_START) | (timestamps >= TRAIN_END_EXCLUSIVE)).any():
            raise CoreExecutionError(f"{label} comparison contains non-TRAIN or TRUE OOS trades")
    return trades


def _exit_reason(trade: pd.Series, trade_fills: pd.DataFrame) -> str:
    if trade.exit_reason in {"TP1", "TP2", "TP3"}:
        return "TAKE_PROFIT"
    if trade.exit_reason == "DATA_BOUNDARY":
        return "END_OF_DATA"
    if trade.exit_reason == "TIME_EXIT":
        return "TIME_EXIT"
    if trade.exit_reason != "STOP":
        return str(trade.exit_reason)
    stop_fill = trade_fills.loc[trade_fills.kind.eq("STOP")]
    stop_price = float(stop_fill.iloc[-1].price) if not stop_fill.empty else float(trade.final_stop)
    tolerance = max(1e-12, abs(float(trade.entry_price)) * 1e-12)
    if abs(stop_price - float(trade.initial_stop)) <= tolerance:
        return "INITIAL_STOP"
    if abs(stop_price - float(trade.entry_price)) <= tolerance:
        return "BREAKEVEN_STOP"
    return "TRAILING_STOP"


def _trade_ledger(result: Any, m15: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "trade_id", "direction", "range_high", "range_low", "range_width", "range_bars",
        "breakout_time", "breakout_price", "retest_time", "retest_quality", "confirmation_time",
        "entry_time", "entry_price", "initial_stop", "initial_risk", "TP1_reached", "TP2_reached",
        "breakeven_activated", "trailing_activated", "exit_time", "exit_price", "exit_reason",
        "result_R", "duration_minutes",
    ]
    rows: list[dict[str, Any]] = []
    if result.trades.empty:
        return pd.DataFrame(columns=columns)
    setup_by_id = result.setups.set_index("setup_id")
    prices = m15.assign(timestamp=pd.to_datetime(m15.timestamp)).set_index("timestamp")
    for trade_id, trade in result.trades.reset_index(drop=True).iterrows():
        setup = setup_by_id.loc[trade.setup_id]
        fills = result.fills.loc[result.fills.setup_id.eq(trade.setup_id)].copy()
        confirmation_start = pd.Timestamp(setup.confirmation_time) - pd.Timedelta(minutes=15)
        confirmation = prices.loc[confirmation_start]
        boundary = float(setup.range_high if setup.direction == "LONG" else setup.range_low)
        penetration = max(0.0, boundary - float(confirmation.low)) if setup.direction == "LONG" else max(0.0, float(confirmation.high) - boundary)
        exit_fills = fills.loc[~fills.kind.eq("ENTRY")]
        rows.append({
            "trade_id": f"CORE-{trade_id + 1:06d}", "direction": trade.direction,
            "range_high": setup.range_high, "range_low": setup.range_low, "range_width": setup.range_width,
            "range_bars": setup.range_bars, "breakout_time": setup.breakout_time,
            "breakout_price": boundary + (setup.breakout_extension if setup.direction == "LONG" else -setup.breakout_extension),
            "retest_time": setup.confirmation_time, "retest_quality": 1.0 - penetration / float(setup.range_width),
            "confirmation_time": setup.confirmation_time, "entry_time": trade.entry_time,
            "entry_price": trade.entry_price, "initial_stop": trade.initial_stop, "initial_risk": trade.initial_risk,
            "TP1_reached": bool(fills.kind.eq("TP1").any()), "TP2_reached": bool(fills.kind.eq("TP2").any()),
            "breakeven_activated": bool(fills.kind.isin(("TP1", "TP2", "TP3")).any()),
            "trailing_activated": bool((fills.stop_after != trade.initial_stop).any() and not fills.kind.isin(("TP1", "TP2", "TP3")).any()),
            "exit_time": trade.exit_time,
            "exit_price": float(exit_fills.iloc[-1].price) if not exit_fills.empty else float(trade.entry_price),
            "exit_reason": _exit_reason(trade, fills), "result_R": trade.result_R,
            "duration_minutes": (pd.Timestamp(trade.exit_time) - pd.Timestamp(trade.entry_time)).total_seconds() / 60,
        })
    return pd.DataFrame(rows, columns=columns)


def _comparison_row(label: str, trades: pd.DataFrame) -> dict[str, Any]:
    return {"execution": label, **{key: value for key, value in _metrics(trades).items() if key != "recovery_factor"}}


def _distribution(values: pd.Series) -> pd.DataFrame:
    edges = np.array([-np.inf, -1, -0.5, 0, 0.5, 1, 2, 3, np.inf], dtype=float)
    counts, _ = np.histogram(pd.to_numeric(values, errors="raise"), bins=edges)
    labels = [f"[{edges[i]:g}, {edges[i + 1]:g}{']' if i == len(counts) - 1 else ')'}" for i in range(len(counts))]
    return pd.DataFrame({"bins": labels, "count": counts})


def run_execution_replay(*, symbol: str, feature_root: Path, normalized_root: Path,
                         candidate_root: Path, baseline_root: Path, output_root: Path,
                         config: CoreExecutionConfig | None = None) -> dict[str, Any]:
    """Run CORE v1 and emit an auditable comparison without altering inputs."""
    symbol = symbol.upper()
    feature_path = _resolve(feature_root, symbol, ("BBW_FEATURES.csv",))
    normalized_path = _resolve(normalized_root, symbol, ("M15.csv",))
    candidate_config = _resolve(candidate_root, symbol, ("CANDIDATE_CONFIG.json", "bbw_candidate_v1.json"))
    candidate_trades_path = _resolve(candidate_root, symbol, ("CANDIDATE_TRADES.csv", "BASELINE_TRADES.csv"))
    baseline_config = _resolve(baseline_root, symbol, ("BASELINE_CONFIG.json", "bbw_baseline.json"))
    baseline_trades_path = _resolve(baseline_root, symbol, ("BASELINE_TRADES.csv",))
    inputs = (feature_path, normalized_path, candidate_config, baseline_config, candidate_trades_path, baseline_trades_path)
    before = {str(path.resolve()): _digest(path) for path in inputs}
    h1 = _load_train_csv(feature_path, "BBW features")
    m15 = _load_train_csv(normalized_path, "normalized M15")
    candidate = json.loads(candidate_config.read_text(encoding="utf-8"))
    baseline_parameters = json.loads(baseline_config.read_text(encoding="utf-8"))
    execution_config = config or CoreExecutionConfig()
    result = replay_core_v1(h1, m15, candidate, execution_config)
    core_trades = _trade_ledger(result, m15)
    baseline_trades = _load_comparison_trades(baseline_trades_path, "Baseline")
    candidate_trades = _load_comparison_trades(candidate_trades_path, "Candidate")
    comparison = pd.DataFrame([
        _comparison_row("Baseline", baseline_trades), _comparison_row("Candidate", candidate_trades),
        _comparison_row("CORE v1", core_trades),
    ])
    summary = _metrics(core_trades)
    exit_distribution = {reason: int(core_trades.exit_reason.eq(reason).sum()) for reason in EXPECTED_EXITS}
    exit_distribution["TIME_EXIT"] = int(core_trades.exit_reason.eq("TIME_EXIT").sum())
    confirmation_prices, adverse_gaps, old_risks = [], [], []
    indexed_m15 = m15.assign(timestamp=pd.to_datetime(m15.timestamp)).set_index("timestamp")
    setups = result.setups.set_index("setup_id") if not result.setups.empty else pd.DataFrame()
    for trade in result.trades.itertuples(index=False):
        setup = setups.loc[trade.setup_id]
        old_entry = float(indexed_m15.loc[pd.Timestamp(setup.confirmation_time) - pd.Timedelta(minutes=15), "close"])
        sign = 1 if trade.direction == "LONG" else -1
        old_stop = float(setup.range_low) - float(baseline_parameters.get("stop_offset", 0)) if sign == 1 else float(setup.range_high) + float(baseline_parameters.get("stop_offset", 0))
        confirmation_prices.append(old_entry)
        adverse_gaps.append(sign * (float(trade.entry_price) - old_entry))
        old_risks.append(sign * (old_entry - old_stop))
    entry_impact = {
        "old_entry": "confirmation close", "new_entry": "next M15 open",
        "mean_signed_adverse_price_change": float(np.mean(adverse_gaps)) if adverse_gaps else 0.0,
    }
    stop_impact = {
        "old_stop": "opposite range boundary with Baseline stop_offset",
        "new_stop": "opposite range boundary with CORE stop_offset",
        "mean_old_initial_risk": float(np.mean(old_risks)) if old_risks else 0.0,
        "mean_structural_initial_risk": float(core_trades.initial_risk.mean()) if len(core_trades) else 0.0,
    }
    management_impact = {
        "breakeven_activations": int(core_trades.breakeven_activated.sum()) if len(core_trades) else 0,
        "partial_exit_fills": int(result.fills.kind.isin(("TP1", "TP2", "TP3")).sum()),
        "trailing_activations": int(core_trades.trailing_activated.sum()) if len(core_trades) else 0,
        "note": "Event counts describe mechanisms; they are not counterfactual causal P&L attribution.",
    }
    warnings = []
    if summary["average_duration"] > MAX_REASONABLE_DURATION_MINUTES:
        warnings.append(f"average duration exceeds {MAX_REASONABLE_DURATION_MINUTES} minutes")
    if summary["trades"] and summary["END_OF_DATA_count"] / summary["trades"] > 0.05:
        warnings.append("END_OF_DATA exceeds 5% of trades")
    payload = {
        "status": "CORE_EXECUTION_ANALYSIS_COMPLETE", "symbol": symbol,
        "period": {"start": "2023-01-03", "end": "2024-12-31"}, "input_sha256": before,
        "execution_config": asdict(execution_config), "metrics": summary,
        "exit_distribution": exit_distribution, "entry_impact": entry_impact,
        "stop_impact": stop_impact, "management_impact": management_impact, "warnings": warnings,
    }
    output_root.mkdir(parents=True, exist_ok=True)
    core_trades.to_csv(output_root / "CORE_TRADES.csv", index=False, lineterminator="\n", date_format="%Y-%m-%d %H:%M:%S", float_format="%.15g")
    comparison.to_csv(output_root / "CORE_EXECUTION_COMPARISON.csv", index=False, lineterminator="\n", float_format="%.15g")
    _distribution(core_trades.result_R).to_csv(output_root / "R_DISTRIBUTION.csv", index=False, lineterminator="\n")
    (output_root / "CORE_EXECUTION_SUMMARY.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = _report(payload)
    (output_root / "CORE_EXECUTION_REPORT.md").write_text(report, encoding="utf-8")
    outputs = ("CORE_TRADES.csv", "CORE_EXECUTION_REPORT.md", "CORE_EXECUTION_SUMMARY.json", "CORE_EXECUTION_COMPARISON.csv", "R_DISTRIBUTION.csv")
    manifest = {"status": payload["status"], "input_sha256": before,
                "output_sha256": {name: _digest(output_root / name) for name in outputs}}
    (output_root / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if any(_digest(Path(path)) != digest for path, digest in before.items()):
        raise CoreExecutionError("an input changed during execution replay")
    return payload


def _format(value: Any) -> str:
    return "N/A" if value is None else f"{value:.6f}" if isinstance(value, float) else str(value)


def _report(payload: dict[str, Any]) -> str:
    metrics, exits = payload["metrics"], payload["exit_distribution"]
    hashes = "\n".join(f"- `{path}`: `{digest}`" for path, digest in payload["input_sha256"].items())
    warnings = "\n".join(f"- WARNING: {item}" for item in payload["warnings"]) or "- None."
    return f"""# BBW CORE v1 Execution Report

## Scope
- Period: 2023-01-03 through 2024-12-31 (TRAIN only; 2025 TRUE OOS is rejected).
- Instrument: {payload['symbol']}.
- Input SHA256:\n{hashes}

## CORE v1 execution model
- Entry: causal next-M15 open after a closed confirmation candle.
- Structural Stop: opposite range boundary plus the configured outward offset.
- Position Management: partial targets, breakeven, locked-R, and optional causal ATR trailing.
- Exit State Machine: deterministic stop-first processing, final target, same-day/time exit, or incomplete-window rejection.

## Trade statistics
- Trades: {metrics['trades']}
- Win rate: {_format(metrics['winrate'])}
- PF: {_format(metrics['PF'])}
- Mean R: {_format(metrics['mean_R'])}
- Total R: {_format(metrics['total_R'])}
- Max drawdown: {_format(metrics['max_drawdown'])}
- Recovery factor: {_format(metrics['recovery_factor'])}
- Average duration: {_format(metrics['average_duration'])} minutes

## Exit distribution
""" + "\n".join(f"- {name}: {count}" for name, count in exits.items()) + f"""

## Entry impact
- Old entry: confirmation close.
- New entry: next M15 open.
- Mean signed adverse price change: {_format(payload['entry_impact']['mean_signed_adverse_price_change'])}.

## Stop impact
- Old stop: {payload['stop_impact']['old_stop']}.
- New stop: {payload['stop_impact']['new_stop']}.
- Mean old initial risk: {_format(payload['stop_impact']['mean_old_initial_risk'])}.
- Mean structural initial risk: {_format(payload['stop_impact']['mean_structural_initial_risk'])}.

## Management impact
- Breakeven activations: {payload['management_impact']['breakeven_activations']}.
- Partial-exit fills: {payload['management_impact']['partial_exit_fills']}.
- Trailing activations: {payload['management_impact']['trailing_activations']}.
- {payload['management_impact']['note']}

## Duration sanity
{warnings}

## Final classification
`{payload['status']}`
"""
