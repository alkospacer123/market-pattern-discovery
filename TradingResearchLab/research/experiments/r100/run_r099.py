#!/usr/bin/env python3
"""TRL-R-2026-099 frozen offline replay. No network, no production access."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

COMMIT = "f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8"
SYMBOL = "USDRUBF"
M5_SHA256 = "3758ed99e4ec0c712af09575ddc74f0437f2fcddda05df2c5d27268296037786"
M5_BLOB_SHA1 = "2b621e1c0aa9a84838d95d4c139257889b6f825e"
TICK = 0.01
LOT = 1000
COSTS = (1, 2, 4)
FIRST_TIMES = [f"10:{m:02d}" for m in range(0, 30, 5)]
LAST_TIMES = [f"18:{m:02d}" for m in range(20, 50, 5)]
REQUIRED_TIMES = FIRST_TIMES + LAST_TIMES


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def json_dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def finite(value: float | int | None):
    if value is None:
        return None
    if isinstance(value, (int, np.integer)):
        return int(value)
    value = float(value)
    return value if math.isfinite(value) else None


def load_bars(path: Path) -> pd.DataFrame:
    d = pd.read_csv(path, sep=";", parse_dates=["Datetime"])
    d["date"] = d["Datetime"].dt.date
    d["time"] = d["Datetime"].dt.strftime("%H:%M")
    return d


def valid_ohlcv(d: pd.DataFrame) -> pd.Series:
    return (
        (d[["Open", "High", "Low", "Close"]] > 0).all(axis=1)
        & (d["Volume"] > 0)
        & (d["High"] >= d[["Open", "Close", "Low"]].max(axis=1))
        & (d["Low"] <= d[["Open", "Close", "High"]].min(axis=1))
    )


def signal_direction(current_day: pd.DataFrame, p0: float) -> int:
    """Extract the frozen signal from supplied bars only; fail on ambiguous input."""
    close = current_day.loc[current_day.time == "10:25", "Close"]
    if len(close) != 1:
        raise RuntimeError("Signal witness requires exactly one 10:25 bar")
    p1 = float(close.iloc[0])
    return 1 if p1 > p0 else (-1 if p1 < p0 else 0)


def pf(values: pd.Series) -> float | None:
    pos = float(values[values > 0].sum())
    neg = float(-values[values < 0].sum())
    if neg > 0:
        return pos / neg
    if pos > 0:
        return math.inf
    return None


def metrics(values: pd.Series) -> dict:
    a = values.astype(float)
    if len(a) == 0:
        return {"n": 0, "net_rub": 0.0, "gross_rub": 0.0, "mean_rub": None,
                "mean_bps": None, "pf": None, "win_rate": None, "sharpe_252": None,
                "trade_close_max_dd_rub": None}
    eq = a.cumsum()
    dd = eq - eq.cummax()
    std = float(a.std(ddof=1))
    return {
        "n": int(len(a)),
        "net_rub": float(a.sum()),
        "mean_rub": float(a.mean()),
        "pf": finite(pf(a)),
        "win_rate": float((a > 0).mean()),
        "sharpe_252": finite(float(a.mean()) / std * math.sqrt(252)) if std > 0 else None,
        "trade_close_max_dd_rub": float(-dd.min()),
    }


def hac_regression(rf: np.ndarray, rl: np.ndarray, lag: int = 5) -> dict:
    n = len(rf)
    x = np.column_stack([np.ones(n), rf])
    xtx_inv = np.linalg.inv(x.T @ x)
    coef = xtx_inv @ x.T @ rl
    resid = rl - x @ coef
    xu = x * resid[:, None]
    meat = xu.T @ xu
    for ell in range(1, lag + 1):
        w = 1.0 - ell / (lag + 1.0)
        cross = xu[ell:].T @ xu[:-ell]
        meat += w * (cross + cross.T)
    cov = xtx_inv @ meat @ xtx_inv * n / (n - x.shape[1])
    se = np.sqrt(np.diag(cov))
    t_stat = coef / se
    # Normal asymptotic two-sided p-value, computed without scipy.
    p_values = [math.erfc(abs(float(t)) / math.sqrt(2.0)) for t in t_stat]
    fitted = x @ coef
    r2 = 1.0 - float(resid @ resid) / float(((rl - rl.mean()) ** 2).sum())
    return {
        "n": n, "hac_lag": lag, "alpha": float(coef[0]), "beta": float(coef[1]),
        "alpha_se": float(se[0]), "beta_se": float(se[1]),
        "beta_t": float(t_stat[1]), "beta_p_two_sided": float(p_values[1]), "r2": r2,
        "covariance": "Newey-West HAC, normal asymptotic two-sided p-value",
        "fitted_mean_check": float(np.mean(fitted - (coef[0] + coef[1] * rf))),
    }


def circular_block_bootstrap(values: np.ndarray, block: int = 20,
                             resamples: int = 20000, seed: int = 20261126) -> dict:
    rng = np.random.default_rng(seed)
    n = len(values)
    blocks_needed = math.ceil(n / block)
    offsets = np.arange(block)
    means = np.empty(resamples, dtype=float)
    batch = 250
    for start in range(0, resamples, batch):
        count = min(batch, resamples - start)
        origins = rng.integers(0, n, size=(count, blocks_needed))
        idx = (origins[:, :, None] + offsets[None, None, :]) % n
        idx = idx.reshape(count, blocks_needed * block)[:, :n]
        means[start:start + count] = values[idx].mean(axis=1)
    return {
        "observed_mean_rub": float(values.mean()),
        "ci95_low_rub": float(np.quantile(means, 0.025)),
        "ci95_high_rub": float(np.quantile(means, 0.975)),
        "block_sessions": block, "resamples": resamples, "seed": seed,
        "method": "circular moving-block bootstrap of daily P&L, including zero-signal days",
        "bootstrap_mean_rub": float(means.mean()),
    }


def aggregation_witnesses(m5: pd.DataFrame, other: dict[str, pd.DataFrame], dates: list) -> dict:
    result = {"m30_first30": {"checked": 0, "mismatch": 0},
              "m15_close": {"checked": 0, "mismatch": 0},
              "m30_close": {"checked": 0, "mismatch": 0},
              "diagnostic_m15_18:45_close": {"checked": 0, "mismatch": 0}}
    m5map = {(r.date, r.time): r for r in m5.itertuples()}
    maps = {name: {(r.date, r.time): r for r in d.itertuples()} for name, d in other.items()}
    for date in dates:
        first = [m5map[(date, t)] for t in FIRST_TIMES]
        expected = (first[0].Open, max(r.High for r in first), min(r.Low for r in first),
                    first[-1].Close, sum(r.Volume for r in first))
        actual = maps["M30"].get((date, "10:00"))
        if actual is not None:
            result["m30_first30"]["checked"] += 1
            got = (actual.Open, actual.High, actual.Low, actual.Close, actual.Volume)
            if not np.allclose(np.array(expected[:4], dtype=float), np.array(got[:4], dtype=float), atol=1e-9, rtol=0) or expected[4] != got[4]:
                result["m30_first30"]["mismatch"] += 1
        close = m5map[(date, "18:45")].Close
        for tf, key in (("M15", "m15_close"), ("M30", "m30_close")):
            actual = maps[tf].get((date, "18:30"))
            if actual is not None:
                result[key]["checked"] += 1
                if not math.isclose(float(close), float(actual.Close), abs_tol=1e-9, rel_tol=0):
                    result[key]["mismatch"] += 1
        # Post-freeze data-quality diagnostic only: same nominal last-bar timestamp.
        actual = maps["M15"].get((date, "18:45"))
        if actual is not None:
            result["diagnostic_m15_18:45_close"]["checked"] += 1
            if not math.isclose(float(close), float(actual.Close), abs_tol=1e-9, rel_tol=0):
                result["diagnostic_m15_18:45_close"]["mismatch"] += 1
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True, help="Pinned forever/ directory")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    log_lines = [f"UTC start {datetime.now(timezone.utc).isoformat()}",
                 f"commit {COMMIT}", f"symbol {SYMBOL}", "network not used"]

    m5_path = args.data_root / SYMBOL / f"{SYMBOL}_M5.csv"
    actual_sha = sha256(m5_path)
    if actual_sha != M5_SHA256:
        raise RuntimeError(f"SOURCE_DRIFT: expected {M5_SHA256}, got {actual_sha}")
    m5 = load_bars(m5_path)
    other = {tf: load_bars(args.data_root / SYMBOL / f"{SYMBOL}_{tf}.csv") for tf in ("M15", "M30")}

    raw_quality = {
        "rows": len(m5), "first_timestamp": str(m5.Datetime.min()), "last_timestamp": str(m5.Datetime.max()),
        "na_cells": int(m5[["Ticker", "Datetime", "Open", "High", "Low", "Close", "Volume"]].isna().sum().sum()),
        "duplicate_timestamps": int(m5.Datetime.duplicated().sum()),
        "non_monotonic_timestamps": int((m5.Datetime.diff().dropna() <= pd.Timedelta(0)).sum()),
        "invalid_ohlcv_rows": int((~valid_ohlcv(m5)).sum()),
        "ticker_values": sorted(m5.Ticker.unique().tolist()),
    }
    if raw_quality["na_cells"] or raw_quality["duplicate_timestamps"] or raw_quality["non_monotonic_timestamps"] or raw_quality["invalid_ohlcv_rows"]:
        raise RuntimeError(f"HOLD_DATA: raw quality failure {raw_quality}")

    observed_dates = sorted(m5.date.unique())
    previous_date = {d: observed_dates[i - 1] if i else None for i, d in enumerate(observed_dates)}
    m5map = {(r.date, r.time): r for r in m5.itertuples()}
    by_date = {d: g for d, g in m5.groupby("date", sort=False)}
    valid_flags = valid_ohlcv(m5).to_numpy()
    eligible_dates, ledger_rows, exclusions = [], [], []
    zero_signal_days = 0
    weekday_candidates = 0

    for date in observed_dates:
        weekday = pd.Timestamp(date).dayofweek < 5
        day_rows = by_date[date].itertuples()
        has_main = any("10:00" <= r.time <= "18:45" for r in day_rows)
        if not weekday or not has_main:
            continue
        weekday_candidates += 1
        prev = previous_date[date]
        missing = [t for t in REQUIRED_TIMES if (date, t) not in m5map]
        if prev is None or (prev, "18:45") not in m5map:
            missing.append("previous_session_18:45")
        if missing:
            exclusions.append({"date": str(date), "reason": "MISSING_REQUIRED_BARS", "detail": ";".join(missing)})
            continue
        req = [m5map[(date, t)] for t in REQUIRED_TIMES]
        prev_bar = m5map[(prev, "18:45")]
        if not all(valid_flags[r.Index] for r in req + [prev_bar]):
            exclusions.append({"date": str(date), "reason": "INVALID_REQUIRED_OHLCV", "detail": ""})
            continue
        p0, p1 = float(prev_bar.Close), float(m5map[(date, "10:25")].Close)
        e, x = float(m5map[(date, "18:20")].Open), float(m5map[(date, "18:45")].Close)
        direction = 1 if p1 > p0 else (-1 if p1 < p0 else 0)
        eligible_dates.append(date)
        if direction == 0:
            zero_signal_days += 1
            continue
        row = {
            "date": str(date), "previous_session_date": str(prev),
            "p0_available": f"{prev} 18:50:00", "p1_available": f"{date} 10:30:00",
            "order_timestamp": f"{date} 18:20:00", "exit_timestamp": f"{date} 18:50:00",
            "p0": p0, "p1": p1, "entry_open": e, "exit_close": x,
            "rf_log": math.log(p1 / p0), "rl_log": math.log(x / e), "direction": direction,
            "gross_rub": direction * (x - e) * LOT,
            "gross_bps": direction * (x - e) / e * 10000.0,
        }
        for c in COSTS:
            entry_fill = e + direction * c * TICK
            exit_fill = x - direction * c * TICK
            row[f"entry_fill_c{c}"] = entry_fill
            row[f"exit_fill_c{c}"] = exit_fill
            row[f"net_rub_c{c}"] = direction * (exit_fill - entry_fill) * LOT
            row[f"net_bps_c{c}"] = direction * (exit_fill - entry_fill) / e * 10000.0
        ledger_rows.append(row)

    ledger = pd.DataFrame(ledger_rows)
    if ledger.empty:
        raise RuntimeError("HOLD_DATA: no eligible nonzero signals")
    ledger.to_csv(out / "daily_ledger.csv", index=False, float_format="%.12g")
    pd.DataFrame(exclusions).to_csv(out / "excluded_days.csv", index=False)

    eligible_frame = pd.DataFrame({"date": [str(d) for d in eligible_dates]})
    eligible_frame["year"] = pd.to_datetime(eligible_frame.date).dt.year
    ledger["year"] = pd.to_datetime(ledger.date).dt.year
    ledger["month"] = ledger.date.str[:7]
    ledger["side"] = np.where(ledger.direction == 1, "LONG", "SHORT")
    benchmark_frame = pd.DataFrame({
        "date": [str(d) for d in eligible_dates],
        "entry_open": [float(m5map[(d, "18:20")].Open) for d in eligible_dates],
        "exit_close": [float(m5map[(d, "18:45")].Close) for d in eligible_dates],
    })

    # All eligible days are retained for bootstrap; no-trade days have zero P&L.
    daily_c2 = eligible_frame[["date"]].merge(ledger[["date", "net_rub_c2"]], on="date", how="left").fillna({"net_rub_c2": 0.0})
    rf = np.array([math.log(float(m5map[(d, "10:25")].Close) / float(m5map[(previous_date[d], "18:45")].Close)) for d in eligible_dates])
    rl = np.array([math.log(float(m5map[(d, "18:45")].Close) / float(m5map[(d, "18:20")].Open)) for d in eligible_dates])
    regression = hac_regression(rf, rl)
    bootstrap = circular_block_bootstrap(daily_c2.net_rub_c2.to_numpy())

    metric_rows = []
    for c in COSTS:
        for scope, segment, group in [("FULL", "ALL", ledger)] + [("YEAR", str(y), g) for y, g in ledger.groupby("year")]:
            m = metrics(group[f"net_rub_c{c}"])
            m["gross_rub"] = float(group.gross_rub.sum())
            m["mean_bps"] = float(group[f"net_bps_c{c}"].mean())
            metric_rows.append({"strategy": "SIGN_RF", "scope": scope, "segment": segment, "cost": f"C{c}", **m})
        for benchmark, signs in (("ALWAYS_LONG", 1), ("ALWAYS_SHORT", -1)):
            gross = signs * (benchmark_frame.exit_close - benchmark_frame.entry_open) * LOT
            vals = gross - 2 * c * TICK * LOT
            m = metrics(vals)
            m["gross_rub"] = float(gross.sum())
            m["mean_bps"] = float((vals / LOT / benchmark_frame.entry_open * 10000.0).mean())
            metric_rows.append({"strategy": benchmark, "scope": "FULL", "segment": "ALL", "cost": f"C{c}", **m})
        for side, group in ledger.groupby("side"):
            m = metrics(group[f"net_rub_c{c}"])
            m["gross_rub"] = float(group.gross_rub.sum())
            m["mean_bps"] = float(group[f"net_bps_c{c}"].mean())
            metric_rows.append({"strategy": "SIGN_RF", "scope": "SIDE", "segment": side, "cost": f"C{c}", **m})
        for month, group in ledger.groupby("month"):
            m = metrics(group[f"net_rub_c{c}"])
            m["gross_rub"] = float(group.gross_rub.sum())
            m["mean_bps"] = float(group[f"net_bps_c{c}"].mean())
            metric_rows.append({"strategy": "SIGN_RF", "scope": "MONTH", "segment": month, "cost": f"C{c}", **m})
    metrics_df = pd.DataFrame(metric_rows)
    metrics_df.to_csv(out / "metrics.csv", index=False, float_format="%.12g")

    yearly_net = ledger.groupby("year").net_rub_c2.sum()
    positive_yearly = yearly_net[yearly_net > 0]
    top10 = ledger.nlargest(10, "net_rub_c2")[["date", "net_rub_c2"]]
    concentration = {
        "net_c2_rub": float(ledger.net_rub_c2.sum()),
        "net_c2_without_top10_rub": float(ledger.net_rub_c2.sum() - top10.net_rub_c2.sum()),
        "top10_profit_rub": float(top10.net_rub_c2.sum()),
        "top10_dates": top10.to_dict(orient="records"),
        "yearly_net_c2_rub": {str(k): float(v) for k, v in yearly_net.items()},
        "max_year_share_of_positive_yearly_net": float(positive_yearly.max() / positive_yearly.sum()) if len(positive_yearly) else None,
    }

    prefix_mismatch, future_mismatch = 0, 0
    for date in eligible_dates:
        p0 = float(m5map[(previous_date[date], "18:45")].Close)
        full_direction = signal_direction(by_date[date], p0)
        # Independent truncated-input calculation; no current-day row after 10:25 is supplied.
        prefix = m5[(m5.date == date) & (m5.time <= "10:25")]
        prefix_direction = signal_direction(prefix, p0)
        prefix_mismatch += int(prefix_direction != full_direction)
        # Deterministically perturb every current-day OHLC after 10:25; direction must not change.
        future = m5[(m5.date == date) & (m5.time > "10:25")].copy()
        future[["Open", "High", "Low", "Close"]] *= 1.01
        perturbed_day = pd.concat([prefix, future], ignore_index=True)
        future_direction = signal_direction(perturbed_day, p0)
        future_mismatch += int(future_direction != full_direction)

    controls = {
        "prefix_invariance": {"checked": len(eligible_dates), "mismatch": int(prefix_mismatch)},
        "future_perturbation": {"checked": len(eligible_dates), "multiplier_after_10:25": 1.01, "mismatch": int(future_mismatch)},
        "aggregation": aggregation_witnesses(m5, other, eligible_dates),
        "ledger_invariants": {
            "rows": len(ledger), "unique_dates": int(ledger.date.nunique()),
            "one_row_per_date": bool(ledger.date.nunique() == len(ledger)),
            "nonzero_directions_only": bool((ledger.direction != 0).all()),
            "net_recalculation_mismatch": int(sum(
                not math.isclose(float(r.net_rub_c2), float(r.direction * (r.exit_fill_c2 - r.entry_fill_c2) * LOT), abs_tol=1e-7)
                for r in ledger.itertuples())),
        },
    }

    exclusions_rate = len(exclusions) / weekday_candidates if weekday_candidates else 1.0
    quality = {
        "source": {"repository": "alkospacer123/market-pattern-data", "commit": COMMIT,
                   "path": f"forever/{SYMBOL}/{SYMBOL}_M5.csv", "sha256": actual_sha,
                   "git_blob_sha1": M5_BLOB_SHA1},
        "raw": raw_quality, "observed_dates": len(observed_dates), "weekday_main_session_candidates": weekday_candidates,
        "eligible_days_including_zero_signals": len(eligible_dates), "trades_nonzero_signals": len(ledger),
        "zero_signal_days": zero_signal_days, "excluded_weekday_days": len(exclusions),
        "exclusion_rate": exclusions_rate, "exclusions": exclusions,
        "timezone_timestamp_assumption": "naive CSV timestamps interpreted as bar start in MSK; original export metadata absent",
    }

    pf_c2, pf_c4 = pf(ledger.net_rub_c2), pf(ledger.net_rub_c4)
    gates = {
        "data": bool(exclusions_rate <= 0.02 and len(eligible_dates) >= 850 and zero_signal_days / len(eligible_dates) <= 0.01),
        "predictive": bool(regression["beta"] > 0 and regression["beta_p_two_sided"] < 0.05),
        "bootstrap_economic": bool(bootstrap["observed_mean_rub"] > 0 and bootstrap["ci95_low_rub"] > 0),
        "pf": bool(pf_c2 is not None and pf_c2 >= 1.10 and pf_c4 is not None and pf_c4 > 1.0),
        "years": bool(int((yearly_net > 0).sum()) >= 3 and yearly_net.get(2025, -1) > 0 and yearly_net.get(2026, -1) > 0),
        "concentration": bool(concentration["net_c2_without_top10_rub"] > 0 and concentration["max_year_share_of_positive_yearly_net"] <= 0.60),
        "controls": bool(prefix_mismatch == 0 and future_mismatch == 0),
    }
    decision = "CONTINUE_RESEARCH" if all(gates.values()) else "REJECT_CURRENT_BASELINE"
    statistical = {"regression": regression, "bootstrap_c2": bootstrap,
                   "concentration": concentration, "gates": gates, "decision": decision,
                   "sample_class": "RETROSPECTIVE_DEVELOPMENT_NOT_TRUE_OOS"}

    json_dump(out / "data_quality.json", quality)
    json_dump(out / "statistical_tests.json", statistical)
    json_dump(out / "controls.json", controls)
    log_lines.extend([f"eligible {len(eligible_dates)}", f"trades {len(ledger)}", f"decision {decision}",
                      f"UTC end {datetime.now(timezone.utc).isoformat()}"])
    (out / "run.log").write_text("\n".join(log_lines) + "\n", encoding="utf-8")

    code_path = Path(__file__).resolve()
    protocol_path = code_path.parent / "FROZEN_PROTOCOL.md"
    manifest = {
        "research_id": "TRL-R-2026-099", "commit": COMMIT,
        "code": {"path": code_path.name, "sha256": sha256(code_path)},
        "protocol": {"path": protocol_path.name, "sha256": sha256(protocol_path)},
        "inputs": [{"path": str(p.relative_to(args.data_root)), "sha256": sha256(p)}
                   for p in [m5_path] + [args.data_root / SYMBOL / f"{SYMBOL}_{tf}.csv" for tf in ("M15", "M30")]],
        "environment": {"python": sys.version, "platform": platform.platform(), "pandas": pd.__version__, "numpy": np.__version__},
        "decision": decision, "sample_class": "RETROSPECTIVE_DEVELOPMENT_NOT_TRUE_OOS",
    }
    manifest["outputs"] = [{"path": p.name, "sha256": sha256(p), "bytes": p.stat().st_size}
                           for p in sorted(out.iterdir()) if p.is_file() and p.name != "run_manifest.json"]
    json_dump(out / "run_manifest.json", manifest)
    print(json.dumps({"decision": decision, "eligible": len(eligible_dates), "trades": len(ledger), "gates": gates}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
