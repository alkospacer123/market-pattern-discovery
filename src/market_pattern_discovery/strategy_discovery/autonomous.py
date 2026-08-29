"""Generic executable strategy synthesis for machine-discovered Phase 5B effects.

The module deliberately consumes only already-discovered directional patterns.
It does not alter Phase 5B enumeration or ranking.  It applies one frozen,
generic execution grid to every eligible pattern and gates discovery-period
strategy candidates at BASE PF>=2 plus robustness requirements.

No INTERNAL_CONFIRMATION or TRUE_OOS data is read here.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import hashlib
import itertools
import json

import numpy as np
import pandas as pd

from market_pattern_discovery.discovery.phase5b_runner import (
    SPECS, DiscoveryMatrix, load_discovery_matrix,
)

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "config" / "autonomous_strategy_synthesis_v1.json"


def _canonical_unsigned(value: dict) -> bytes:
    return json.dumps(
        {k: v for k, v in value.items() if k != "signature_sha256"},
        sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode()


def load_synthesis_config(path: Path = CONFIG_PATH) -> dict:
    value = json.loads(path.read_text())
    actual = hashlib.sha256(_canonical_unsigned(value)).hexdigest()
    if actual != value.get("signature_sha256"):
        raise ValueError("autonomous strategy synthesis config signature drift")
    if value["safety"]["internal_confirmation_accessed"]:
        raise PermissionError("synthesis config may not open internal confirmation")
    if value["safety"]["true_oos_2025_accessed"]:
        raise PermissionError("synthesis config may not open TRUE OOS")
    return value


def _read_effects(paths: list[str | Path]) -> list[dict[str, Any]]:
    rows = []
    for path in paths:
        with Path(path).open() as stream:
            for line in stream:
                if line.strip():
                    rows.append(json.loads(line))
    return rows


def _conditions(effect: dict) -> list[tuple[str, Any]]:
    return [(x["feature"], x["state"]) for x in effect["feature_conditions"]]


def _direction(effect: dict) -> int | None:
    signed = float(effect.get("primary_effect_signed", np.nan))
    if not np.isfinite(signed) or signed == 0:
        return None
    family = effect.get("target_family")
    if family not in {"DIRECTIONAL", "FIRST_PASSAGE"}:
        return None
    contrast = str(effect.get("contrast", ""))
    target = str(effect.get("target", ""))
    if "signed_displacement" in target:
        return 1 if signed > 0 else -1
    if "+1" in contrast or "upper-first" in contrast or "upper_first" in contrast:
        base = 1
    elif "-1" in contrast or "lower-first" in contrast or "lower_first" in contrast:
        base = -1
    else:
        return None
    return base if signed > 0 else -base


def _pattern_mask(matrix: DiscoveryMatrix, effect: dict) -> np.ndarray:
    mask = np.ones(len(matrix.frame), dtype=bool)
    for feature, state in _conditions(effect):
        if feature not in matrix.states:
            raise ValueError(f"pattern feature unavailable: {feature}")
        mask &= matrix.states[feature].eq(state).to_numpy()
    previous = np.r_[False, mask[:-1]]
    dates = matrix.frame["moscow_trading_date"].to_numpy()
    same_day = np.r_[False, dates[1:] == dates[:-1]]
    return mask & ~(previous & same_day)


def _round_tick(price: float, tick: float) -> float:
    return float(np.floor(price / tick + .5) * tick)


def _simulate_raw(
    frame: pd.DataFrame, signal_mask: np.ndarray, direction: int, tick: float,
    stop_atr: float, target_r: float, max_hold: int,
) -> pd.DataFrame:
    required = {"open_time", "close_time", "open", "high", "low", "close", "atr_20",
                "moscow_trading_date"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"execution frame missing {sorted(missing)}")
    n = len(frame)
    dates = frame["moscow_trading_date"].to_numpy()
    opens = frame.open.to_numpy(float); highs = frame.high.to_numpy(float)
    lows = frame.low.to_numpy(float); closes = frame.close.to_numpy(float)
    atr = pd.to_numeric(frame.atr_20, errors="coerce").to_numpy(float)
    day_end = np.empty(n, dtype=np.int64)
    for _, idx in frame.groupby("moscow_trading_date", sort=False).indices.items():
        idx = np.asarray(idx, dtype=np.int64); day_end[idx] = idx[-1]

    rows = []; busy_until = -1
    for signal_i in np.flatnonzero(signal_mask):
        if signal_i <= busy_until:
            continue
        entry_i = signal_i + 1
        if entry_i >= n or dates[entry_i] != dates[signal_i]:
            continue
        if pd.Timestamp(frame.open_time.iloc[entry_i]) != pd.Timestamp(frame.close_time.iloc[signal_i]):
            continue
        if not np.isfinite(atr[signal_i]) or atr[signal_i] <= 0:
            continue
        entry = opens[entry_i]
        stop = _round_tick(entry - direction * stop_atr * atr[signal_i], tick)
        risk = direction * (entry - stop)
        if risk <= 0:
            continue
        target = _round_tick(entry + direction * risk * target_r, tick)
        if direction * (target - entry) <= 0:
            continue
        last = min(entry_i + max_hold - 1, int(day_end[entry_i]))
        exit_i = last; exit_price = closes[last]
        reason = "TIME" if last == entry_i + max_hold - 1 else "DAY_END"
        for i in range(entry_i, last + 1):
            op, hi, lo = opens[i], highs[i], lows[i]
            stop_gap = op <= stop if direction == 1 else op >= stop
            target_gap = op >= target if direction == 1 else op <= target
            stop_hit = lo <= stop if direction == 1 else hi >= stop
            target_hit = hi >= target if direction == 1 else lo <= target
            if stop_gap:
                exit_i, exit_price, reason = i, op, "STOP_GAP"; break
            if target_gap:
                exit_i, exit_price, reason = i, target, "TARGET_GAP_CONSERVATIVE"; break
            if stop_hit:
                exit_i, exit_price = i, stop
                reason = "STOP_FIRST_TIE" if target_hit else "STOP"; break
            if target_hit:
                exit_i, exit_price, reason = i, target, "TARGET"; break
        rows.append({
            "signal_index": int(signal_i), "signal_time": frame.close_time.iloc[signal_i],
            "signal_month": pd.Timestamp(frame.close_time.iloc[signal_i]).strftime("%Y-%m"),
            "trading_date": dates[signal_i], "entry_time": frame.open_time.iloc[entry_i],
            "exit_time": frame.close_time.iloc[exit_i], "direction": direction,
            "raw_entry": entry, "raw_exit": exit_price, "stop": stop, "target": target,
            "risk_price": risk, "exit_reason": reason, "bars_held": exit_i - entry_i + 1,
        })
        busy_until = exit_i
    return pd.DataFrame(rows)


def _expand_friction(raw: pd.DataFrame, tick: float, scenarios: dict[str, int]) -> pd.DataFrame:
    if raw.empty:
        return pd.DataFrame()
    rows = []
    for r in raw.itertuples(index=False):
        for scenario, friction in scenarios.items():
            adjusted_entry = r.raw_entry + r.direction * friction * tick
            adjusted_exit = r.raw_exit - r.direction * friction * tick
            pnl_price = r.direction * (adjusted_exit - adjusted_entry)
            rows.append({
                **r._asdict(), "friction": scenario, "friction_ticks_per_side": friction,
                "entry_price": adjusted_entry, "exit_price": adjusted_exit,
                "pnl_price": pnl_price, "pnl_R": pnl_price / r.risk_price,
            })
    return pd.DataFrame(rows)


def _metrics(rows: pd.DataFrame) -> dict[str, float]:
    if rows.empty:
        return {"trades": 0, "profit_factor": np.nan, "expectancy_R": np.nan,
                "win_rate": np.nan, "max_drawdown_R": np.nan,
                "net_R": 0.0, "largest_winner_share": np.nan, "unique_days": 0}
    x = rows.pnl_R.to_numpy(float)
    wins = x[x > 0]; losses = x[x < 0]
    pf = wins.sum() / -losses.sum() if len(losses) else np.inf
    equity = np.cumsum(x)
    peak = np.maximum.accumulate(np.r_[0.0, equity])[:-1]
    dd = float(np.max(peak - equity)) if len(equity) else 0.0
    share = float(wins.max() / wins.sum()) if len(wins) and wins.sum() > 0 else np.nan
    return {
        "trades": int(len(x)), "profit_factor": float(pf),
        "expectancy_R": float(x.mean()), "win_rate": float(np.mean(x > 0)),
        "max_drawdown_R": dd, "net_R": float(x.sum()),
        "largest_winner_share": share,
        "unique_days": int(rows.trading_date.nunique()),
    }


def _month_summary(base: pd.DataFrame) -> dict[str, dict[str, float]]:
    result = {}
    for month, g in base.groupby("signal_month", sort=True):
        if len(g) >= 3:
            result[str(month)] = _metrics(g)
    return result


def _gate(base: dict, stress: dict, months: dict, cfg: dict) -> tuple[bool, list[str]]:
    g = cfg["discovery_gate"]; failures = []
    if base["trades"] < g["minimum_trades"]: failures.append("trades")
    if base["unique_days"] < g["minimum_unique_days"]: failures.append("unique_days")
    if not np.isfinite(base["profit_factor"]) or base["profit_factor"] < g["base_profit_factor"]:
        failures.append("base_pf")
    if not np.isfinite(base["expectancy_R"]) or base["expectancy_R"] <= g["base_expectancy_r"]:
        failures.append("base_expectancy")
    if not np.isfinite(stress["profit_factor"]) or stress["profit_factor"] < g["stress_profit_factor"]:
        failures.append("stress_pf")
    if not np.isfinite(stress["expectancy_R"]) or stress["expectancy_R"] <= g["stress_expectancy_r"]:
        failures.append("stress_expectancy")
    positive = sum(m["expectancy_R"] > 0 for m in months.values())
    if positive < g["minimum_positive_calendar_blocks"]: failures.append("calendar_stability")
    share = base["largest_winner_share"]
    if np.isfinite(share) and share > g["maximum_largest_winner_share"]:
        failures.append("winner_concentration")
    return not failures, failures


def _grid_neighbors(surface: pd.DataFrame, row: pd.Series, cfg: dict) -> int:
    stops = cfg["grid"]["stop_atr"]; targets = cfg["grid"]["target_r"]
    holds = cfg["grid"]["max_hold_minutes"]
    si = stops.index(row.stop_atr); ti = targets.index(row.target_r); hi = holds.index(row.max_hold_minutes)
    neighbors = []
    for axis, index, size in ((0, si, len(stops)), (1, ti, len(targets)), (2, hi, len(holds))):
        for delta in (-1, 1):
            j = index + delta
            if not 0 <= j < size: continue
            values = [row.stop_atr, row.target_r, row.max_hold_minutes]
            values[axis] = (stops, targets, holds)[axis][j]
            m = surface[
                (surface.effect_id == row.effect_id)
                & (surface.stop_atr == values[0])
                & (surface.target_r == values[1])
                & (surface.max_hold_minutes == values[2])
            ]
            if len(m): neighbors.append(m.iloc[0])
    floor = cfg["robustness"]["neighbor_base_pf_floor"]
    return sum(
        np.isfinite(n.base_pf) and n.base_pf >= floor and n.base_expectancy_R > 0
        for n in neighbors
    )


def synthesize(
    data_root: str | Path, effect_paths: list[str | Path], output: str | Path,
    instrument: str = "CNYRUBF", timeframe: str = "M1",
    *, allow_evaluated_smoke: bool = False,
) -> dict[str, Any]:
    cfg = load_synthesis_config()
    if timeframe != "M1":
        raise NotImplementedError("v1 synthesis is intentionally M1-primary")
    matrix = load_discovery_matrix(data_root, instrument, timeframe)
    effects = _read_effects(effect_paths)
    allowed_status = {"promoted"} | ({"evaluated", "screened"} if allow_evaluated_smoke else set())
    effects = [
        e for e in effects
        if e.get("status") in allowed_status
        and e.get("target_family") in cfg["scope"]["allowed_source_target_families"]
        and _direction(e) is not None
    ]
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    surface_rows = []; audit_samples = []
    tick = SPECS[instrument]["tick"]
    for effect in effects:
        signal_mask = _pattern_mask(matrix, effect)
        direction = _direction(effect)
        for stop_atr, target_r, hold in itertools.product(
            cfg["grid"]["stop_atr"], cfg["grid"]["target_r"], cfg["grid"]["max_hold_minutes"]
        ):
            raw = _simulate_raw(matrix.frame, signal_mask, direction, tick, stop_atr, target_r, hold)
            ledger = _expand_friction(raw, tick, cfg["friction_ticks_per_side"])
            metrics = {
                scenario: _metrics(ledger.loc[ledger.friction.eq(scenario)])
                if not ledger.empty else _metrics(pd.DataFrame())
                for scenario in ("GROSS", "BASE", "STRESS")
            }
            base_rows = ledger.loc[ledger.friction.eq("BASE")] if not ledger.empty else pd.DataFrame()
            months = _month_summary(base_rows) if not base_rows.empty else {}
            passed, failures = _gate(metrics["BASE"], metrics["STRESS"], months, cfg)
            surface_rows.append({
                "effect_id": effect["effect_id"], "hypothesis_id": effect["hypothesis_id"],
                "instrument": instrument, "timeframe": timeframe,
                "direction": direction, "stop_atr": stop_atr, "target_r": target_r,
                "max_hold_minutes": hold,
                "gross_pf": metrics["GROSS"]["profit_factor"],
                "base_pf": metrics["BASE"]["profit_factor"],
                "stress_pf": metrics["STRESS"]["profit_factor"],
                "base_expectancy_R": metrics["BASE"]["expectancy_R"],
                "stress_expectancy_R": metrics["STRESS"]["expectancy_R"],
                "base_trades": metrics["BASE"]["trades"],
                "base_unique_days": metrics["BASE"]["unique_days"],
                "base_dd_R": metrics["BASE"]["max_drawdown_R"],
                "base_net_R": metrics["BASE"]["net_R"],
                "base_win_rate": metrics["BASE"]["win_rate"],
                "largest_winner_share": metrics["BASE"]["largest_winner_share"],
                "positive_calendar_blocks": sum(m["expectancy_R"] > 0 for m in months.values()),
                "gate_before_neighbors": passed,
                "gate_failures": "|".join(failures),
                "month_metrics_json": json.dumps(months, sort_keys=True),
            })
            if len(audit_samples) < 100 and not ledger.empty:
                sample = ledger.head(1).copy()
                sample["effect_id"] = effect["effect_id"]
                sample["stop_atr"] = stop_atr; sample["target_r"] = target_r
                sample["max_hold_minutes"] = hold
                audit_samples.append(sample)
    surface = pd.DataFrame(surface_rows)
    if surface.empty:
        surface.to_csv(output / "strategy_surface.csv", index=False)
        summary = {"patterns_consumed": len(effects), "configurations": 0, "survivors": 0,
                   "internal_confirmation_accessed": False, "true_oos_accessed": False}
        (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        return summary

    surface["passing_neighbors"] = [
        _grid_neighbors(surface, row, cfg) for _, row in surface.iterrows()
    ]
    surface["discovery_gate_pass"] = (
        surface.gate_before_neighbors
        & (surface.passing_neighbors >= cfg["robustness"]["minimum_passing_neighbors"])
    )
    surface.to_csv(output / "strategy_surface.csv", index=False)
    if audit_samples:
        pd.concat(audit_samples, ignore_index=True).to_csv(output / "trade_audit_sample.csv", index=False)

    survivors = surface.loc[surface.discovery_gate_pass].sort_values(
        ["base_pf", "stress_pf", "base_expectancy_R"], ascending=False, kind="mergesort"
    )
    survivor_records = survivors.to_dict("records")
    (output / "survivors.json").write_text(
        json.dumps(survivor_records, indent=2, sort_keys=True, default=str) + "\n"
    )
    summary = {
        "patterns_consumed": len(effects), "configurations": int(len(surface)),
        "survivors": int(len(survivors)), "target_base_pf": cfg["discovery_gate"]["base_profit_factor"],
        "minimum_stress_pf": cfg["discovery_gate"]["stress_profit_factor"],
        "internal_confirmation_accessed": False, "true_oos_accessed": False,
        "data_2025_accessed": False,
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return summary


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Synthesize PF-gated strategies from Phase 5B effects")
    p.add_argument("--data-root", required=True)
    p.add_argument("--effects", nargs="+", required=True)
    p.add_argument("--output", default="results/autonomous_strategy_synthesis")
    p.add_argument("--instrument", choices=sorted(SPECS), default="CNYRUBF")
    p.add_argument("--timeframe", choices=["M1", "M5"], default="M1")
    p.add_argument("--allow-evaluated-smoke", action="store_true")
    a = p.parse_args(argv)
    print(json.dumps(synthesize(
        a.data_root, a.effects, a.output, a.instrument, a.timeframe,
        allow_evaluated_smoke=a.allow_evaluated_smoke,
    ), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
