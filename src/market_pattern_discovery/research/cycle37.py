"""Frozen, causal Cycle37 structural-rejection family miner."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from hashlib import sha256
from itertools import product
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from market_pattern_discovery.data.loader import MarketDataLoader


@dataclass(frozen=True)
class Candidate:
    structure: str
    direction: str
    rejection_type: str
    session: str
    stop_ticks: int
    target_r: int

    @property
    def candidate_id(self) -> str:
        return "__".join(map(str, (self.structure, self.direction, self.rejection_type,
                                    self.session, self.stop_ticks, self.target_r)))


def _jsonable(value: Any) -> Any:
    if isinstance(value, (np.integer,)): return int(value)
    if isinstance(value, (np.floating,)): return float(value)
    if isinstance(value, pd.Timestamp): return value.isoformat()
    raise TypeError(type(value).__name__)


def load_protocol(path: str | Path) -> dict:
    with Path(path).open(encoding="utf-8") as stream:
        protocol = json.load(stream)
    if protocol["periods"]["true_oos_year"] != 2025:
        raise ValueError("Cycle37 must retain the 2025 TRUE OOS lock")
    return protocol


def enumerate_candidates(protocol: dict, instrument: str) -> list[Candidate]:
    stops = protocol["instruments"][instrument]["stop_ticks"]
    sessions = [item["id"] for item in protocol["session_windows"]]
    return [Candidate(*values) for values in product(
        protocol["structures"], protocol["directions"], protocol["rejection_types"],
        sessions, stops, protocol["targets_r"])]


def causal_levels(m5: pd.DataFrame, structure: str, direction: str,
                  round_step: float) -> pd.Series:
    """Return one causal level per setup row; rolling windows reset each day."""
    frame = m5.copy()
    day = frame.timestamp.dt.normalize()
    if structure == "ROUND":
        base = np.floor(frame.close / round_step) if direction == "LONG" else np.ceil(frame.close / round_step)
        return base * round_step
    if structure in {"ROLL30", "ROLL60"}:
        window = int(structure[4:])
        column = "low" if direction == "LONG" else "high"
        reducer = "min" if direction == "LONG" else "max"
        shifted = frame.groupby(day, sort=False)[column].shift(1)
        return shifted.groupby(day, sort=False).transform(
            lambda values: values.rolling(window, min_periods=window).agg(reducer))
    if structure == "PREVIOUS_DAY_HIGH_LOW":
        column = "low" if direction == "LONG" else "high"
        daily = frame.groupby(day, sort=True)[column].agg("min" if direction == "LONG" else "max")
        return day.map(daily.shift(1))
    raise ValueError(f"unknown structure: {structure}")


def rejection_mask(m5: pd.DataFrame, level: pd.Series, direction: str,
                   rejection_type: str) -> pd.Series:
    o, h, low, c, prior = (m5.open, m5.high, m5.low, m5.close, m5.close.shift(1))
    if direction == "LONG":
        predicates = {
            "wick_rejection": (low <= level) & (o >= level) & (c > o) & (c > level),
            "close_rejection": (o <= level) & (c > level),
            "sweep_reclaim": (low < level) & (c > level),
            "failed_breakout": (prior < level) & (low <= level) & (c > level),
        }
    else:
        predicates = {
            "wick_rejection": (h >= level) & (o <= level) & (c < o) & (c < level),
            "close_rejection": (o >= level) & (c < level),
            "sweep_reclaim": (h > level) & (c < level),
            "failed_breakout": (prior > level) & (h >= level) & (c < level),
        }
    try:
        return predicates[rejection_type].fillna(False)
    except KeyError as exc:
        raise ValueError(f"unknown rejection type: {rejection_type}") from exc


def _session(protocol: dict, session_id: str) -> tuple[Any, Any]:
    item = next(x for x in protocol["session_windows"] if x["id"] == session_id)
    return pd.Timestamp(item["start"]).time(), pd.Timestamp(item["end"]).time()


def signals_for(m5: pd.DataFrame, candidate: Candidate, protocol: dict,
                instrument: str) -> pd.DataFrame:
    level = causal_levels(m5, candidate.structure, candidate.direction,
                          protocol["instruments"][instrument]["round_step"])
    mask = rejection_mask(m5, level, candidate.direction, candidate.rejection_type)
    start, end = _session(protocol, candidate.session)
    completion = m5.timestamp + pd.Timedelta(minutes=5)
    mask &= (m5.timestamp.dt.time >= start) & (completion.dt.time <= end)
    return pd.DataFrame({"setup_open": m5.timestamp[mask], "signal_time": completion[mask],
                         "level": level[mask]}).reset_index(drop=True)


def simulate(m1: pd.DataFrame, signals: pd.DataFrame, candidate: Candidate, protocol: dict,
             instrument: str, *, stress: bool = False) -> list[dict]:
    """Execute after setup completion. A deterministic stop-first rule is used."""
    tick = protocol["instruments"][instrument]["tick_size"]
    costs = protocol["costs"][instrument]
    multiplier = protocol["stress"]["cost_multiplier"] if stress else 1.0
    slip_multiplier = protocol["stress"]["slippage_multiplier"] if stress else 1.0
    commission = 2 * costs["transaction_cost_ticks_per_side"] * tick * multiplier
    slip = costs["slippage_ticks_per_side"] * tick * slip_multiplier
    risk = candidate.stop_ticks * tick
    _, end = _session(protocol, candidate.session)
    records, available_at = [], None
    times = m1.timestamp
    opens = m1.open.to_numpy(dtype=float)
    highs = m1.high.to_numpy(dtype=float)
    lows = m1.low.to_numpy(dtype=float)
    closes = m1.close.to_numpy(dtype=float)
    for signal in signals.itertuples(index=False):
        if available_at is not None and signal.signal_time < available_at:
            continue
        day_end = pd.Timestamp.combine(signal.signal_time.date(), end).tz_localize(signal.signal_time.tz)
        entry_i = int(times.searchsorted(signal.signal_time, side="left"))
        if entry_i >= len(m1) or times.iloc[entry_i] >= day_end:
            continue
        sign = 1 if candidate.direction == "LONG" else -1
        entry = opens[entry_i] + sign * slip
        stop, target = entry - sign * risk, entry + sign * risk * candidate.target_r
        exit_price = exit_time = reason = None
        for i in range(entry_i, len(m1)):
            timestamp = times.iloc[i]
            if timestamp.date() != signal.signal_time.date() or timestamp >= day_end:
                break
            stop_hit = lows[i] <= stop if sign == 1 else highs[i] >= stop
            target_hit = highs[i] >= target if sign == 1 else lows[i] <= target
            if stop_hit:
                raw = min(opens[i], stop) if sign == 1 else max(opens[i], stop)
                exit_price, exit_time, reason = raw - sign * slip, timestamp + pd.Timedelta(minutes=1), "stop"
                break
            if target_hit:
                exit_price, exit_time, reason = target - sign * slip, timestamp + pd.Timedelta(minutes=1), "target"
                break
            exit_price, exit_time, reason = closes[i] - sign * slip, timestamp + pd.Timedelta(minutes=1), "session"
        if exit_price is None:
            continue
        net_r = (sign * (exit_price - entry) - commission) / risk
        records.append({"signal_time": signal.signal_time, "entry_time": times.iloc[entry_i],
                        "exit_time": exit_time, "exit_reason": reason, "net_r": net_r})
        available_at = exit_time
    return records


def metrics(trades: list[dict]) -> dict:
    values = np.asarray([x["net_r"] for x in trades], dtype=float)
    gains, losses = values[values > 0].sum(), -values[values < 0].sum()
    infinite = bool(len(values) and losses == 0 and gains > 0)
    return {"n": len(values), "net_r": float(values.sum()),
            "pf": None if losses == 0 else float(gains / losses), "pf_infinite": infinite}


def _pf_at_least(result: dict, minimum: float) -> bool:
    return result["pf_infinite"] or (result["pf"] is not None and result["pf"] >= minimum)


def bootstrap_lower(trades: list[dict], protocol: dict) -> float | None:
    values = np.asarray([x["net_r"] for x in trades])
    if not len(values): return None
    spec = protocol["bootstrap"]
    rng = np.random.default_rng(spec["seed"])
    samples = rng.choice(values, size=(spec["samples"], len(values)), replace=True).sum(axis=1)
    return float(np.quantile(samples, spec["lower_quantile"]))


def _period(frame: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    left, right = pd.Timestamp(start, tz="Europe/Moscow"), pd.Timestamp(end, tz="Europe/Moscow")
    return frame[(frame.timestamp >= left) & (frame.timestamp < right)].reset_index(drop=True)


def _source_record(path: Path) -> dict:
    digest = sha256(path.read_bytes()).hexdigest()
    return {"path": str(path.resolve()), "sha256": digest, "bytes": path.stat().st_size}


def run_instrument(data_root: str | Path, output_root: str | Path, protocol: dict,
                   instrument: str) -> dict:
    loader, out = MarketDataLoader(data_root), Path(output_root) / instrument
    out.mkdir(parents=True, exist_ok=True)
    paths = {tf: loader.discover(instrument, tf) for tf in ("M1", "M5")}
    if any("2025" in str(p) for values in paths.values() for p in values):
        raise ValueError("TRUE OOS path was selected")
    m1, m5 = loader.load(instrument, "M1", paths["M1"]), loader.load(instrument, "M5", paths["M5"])
    selection_m5, forward_m5 = _period(m5, "2026-01-01", "2026-03-01"), _period(m5, "2026-03-01", "2026-05-16")
    selection_m1, forward_m1 = _period(m1, "2026-01-01", "2026-03-01"), _period(m1, "2026-03-01", "2026-05-16")
    candidates, generated, shortlist = enumerate_candidates(protocol, instrument), [], []
    selection_signal_cache: dict[tuple[str, str, str, str], pd.DataFrame] = {}
    for candidate in candidates:
        signal_key = (candidate.structure, candidate.direction, candidate.rejection_type, candidate.session)
        if signal_key not in selection_signal_cache:
            selection_signal_cache[signal_key] = signals_for(selection_m5, candidate, protocol, instrument)
        sig = selection_signal_cache[signal_key]
        base = metrics(simulate(selection_m1, sig, candidate, protocol, instrument))
        row = {**candidate.__dict__, "candidate_id": candidate.candidate_id, "selection_base": base}
        generated.append(row)
        gate = protocol["gates"]["base"]
        if base["n"] >= gate["trades_min"] and _pf_at_least(base, gate["pf_min"]): shortlist.append(row)
    evaluated: list[dict] = []
    # Evaluate only frozen discovery shortlist; no forward result can alter the grid.
    forward_signal_cache: dict[tuple[str, str, str, str], pd.DataFrame] = {}
    for row in shortlist:
        candidate = Candidate(*(row[k] for k in Candidate.__dataclass_fields__))
        signal_key = (candidate.structure, candidate.direction, candidate.rejection_type, candidate.session)
        if signal_key not in forward_signal_cache:
            forward_signal_cache[signal_key] = signals_for(forward_m5, candidate, protocol, instrument)
        sig = forward_signal_cache[signal_key]
        trades = simulate(forward_m1, sig, candidate, protocol, instrument)
        stress_trades = simulate(forward_m1, sig, candidate, protocol, instrument, stress=True)
        base, stress, lower = metrics(trades), metrics(stress_trades), bootstrap_lower(trades, protocol)
        monthly = {}
        for name, start, end in (("2026-03", "2026-03-01", "2026-04-01"),
                                 ("2026-04", "2026-04-01", "2026-05-01"),
                                 ("2026-05-01_15", "2026-05-01", "2026-05-16")):
            monthly[name] = float(sum(t["net_r"] for t in trades if pd.Timestamp(start, tz="Europe/Moscow") <= t["entry_time"] < pd.Timestamp(end, tz="Europe/Moscow")))
        evaluated.append({**row, "forward_base": base, "forward_stress": stress,
                          "bootstrap_lower_net_r": lower, "monthly_net_r": monthly})
    by_id = {x["candidate_id"]: x for x in evaluated}
    session_ids = [x["id"] for x in protocol["session_windows"]]
    def neighbors(row: dict) -> list[str]:
        found = []
        for field, grid in (("stop_ticks", protocol["instruments"][instrument]["stop_ticks"]),
                            ("target_r", protocol["targets_r"]), ("session", session_ids)):
            at = grid.index(row[field])
            for adjacent in (at - 1, at + 1):
                if 0 <= adjacent < len(grid):
                    values = {k: row[k] for k in Candidate.__dataclass_fields__}; values[field] = grid[adjacent]
                    candidate_id = Candidate(**values).candidate_id
                    if candidate_id in by_id and by_id[candidate_id]["forward_base"]["net_r"] > 0: found.append(candidate_id)
        return found
    survivors = []
    for row in evaluated:
        adjacent = neighbors(row); base, stress = row["forward_base"], row["forward_stress"]
        bg, sg = protocol["gates"]["base"], protocol["gates"]["stress"]
        gates = {"base": base["n"] >= bg["trades_min"] and _pf_at_least(base, bg["pf_min"]),
                 "stress": stress["n"] >= sg["trades_min"] and _pf_at_least(stress, sg["pf_min"]),
                 "bootstrap": row["bootstrap_lower_net_r"] is not None and row["bootstrap_lower_net_r"] > 0,
                 "monthly": all(value > 0 for value in row["monthly_net_r"].values()), "neighbor": bool(adjacent)}
        if all(gates.values()): survivors.append({**row, "gates": gates, "positive_neighbors": adjacent})
    manifest = {"protocol_id": protocol["protocol_id"], "instrument": instrument,
                "source_files": {tf: [_source_record(p) for p in paths[tf]] for tf in paths},
                "rows": {"M1": len(m1), "M5": len(m5)}, "candidate_count": len(candidates),
                "family_isolation": True, "combined_or_strategy": False}
    for name, value in (("run_manifest.json", manifest), ("generated_candidates.json", generated),
                        ("shortlist.json", evaluated), ("survivors.json", survivors)):
        (out / name).write_text(json.dumps(value, indent=2, default=_jsonable) + "\n", encoding="utf-8")
    family_counts = {family: sum(x["structure"] == family for x in survivors) for family in protocol["structures"]}
    report = f"# Cycle37 — {instrument}\n\nGenerated: {len(generated)}  \nShortlisted: {len(shortlist)}  \nSurvivors: {len(survivors)}\n\n## Survivors by independent family\n" + "".join(f"\n- {k}: {v}" for k, v in family_counts.items()) + "\n"
    (out / "report.md").write_text(report, encoding="utf-8")
    return {"instrument": instrument, "generated": len(generated), "shortlisted": len(shortlist), "survivors": len(survivors), "survivors_by_family": family_counts}


def run(data_root: str | Path, output_root: str | Path, protocol_path: str | Path) -> dict:
    protocol, root = load_protocol(protocol_path), Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    summaries = [run_instrument(data_root, root, protocol, instrument) for instrument in protocol["instruments"]]
    summary = {"protocol_id": protocol["protocol_id"], "research_question": protocol["research_question"],
               "combined_or_strategy": False, "instruments": summaries}
    (root / "cycle37_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", default="/workspace/market-pattern-data")
    parser.add_argument("--output-root", default="results/cycle37_structural_rejection_family")
    parser.add_argument("--protocol", default="config/cycle37_structural_rejection_family.json")
    args = parser.parse_args(argv)
    print(json.dumps(run(args.data_root, args.output_root, args.protocol), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
