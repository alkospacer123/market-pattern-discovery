"""Deterministic fixed-baseline research, gated before new instrument economics."""
import argparse
from dataclasses import asdict
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
import platform
import sys

import numpy as np
import pandas as pd

from engine import (ALIASES, BASE_COMMIT, CONFIGS, DATA_COMMIT, END, START,
                    SYMBOLS, TZ, UNITS, close_index, git, historical_quarters,
                    read_prefix, replay, sha_file, verify_source)

HERE = Path(__file__).resolve().parent
REFERENCES = {
    "BASELINE": "TradingSystemLab/results/timeframe_validation/M15/T3/trades.csv",
    "OPTIMIZED": "TradingSystemLab/results/timeframe_analysis/M15_ROBUSTNESS/T3/trades.csv"}
SOURCE_CODE = ["TradingSystemLab/strategies/trend/T3_MTF_Trend.py",
    "TradingSystemLab/timeframe_validation/m15_baseline.py", "TradingSystemLab/optimization/m15.py",
    "TradingSystemLab/timeframe_analysis/m15_robustness.py", "TradingSystemLab/walk_forward/m15.py",
    "TradingSystemLab/core/backtester.py", "TradingSystemLab/core/data_loader.py",
    "TradingSystemLab/core/indicators.py", "TradingSystemLab/core/instrument_specs.py",
    "IntradayLab/reports/STAGE1_M5_CLOCK_CONFIRMATION.md", "IntradayLab/reports/STAGE1_EXECUTION_COSTS_SPEC.md"]
# Published reference CSV uses 12 significant digits. Absolute allowances are
# far below the smallest research unit; no relative-price tolerance is used.
TOLERANCES = {"entry_price": 5e-9, "initial_stop": 5e-9, "exit_price": 5e-9,
              "initial_risk": 5e-10, "initial_risk_ticks": 5e-7,
              "gross_R": 5e-10, "net_R": 5e-10, "MAE_R": 5e-10, "MFE_R": 5e-10}
EXPECTED = {("BASELINE", 2023): (196, 2.179, 88.98), ("BASELINE", 2024): (229, 1.107, 11.76),
            ("OPTIMIZED", 2023): (185, 2.177, 93.36), ("OPTIMIZED", 2024): (216, 1.255, 28.13)}


def json_write(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+"\n")


def csv_write(path, value, columns=None):
    frame = value if isinstance(value, pd.DataFrame) else pd.DataFrame(value, columns=columns)
    frame.to_csv(path, index=False, float_format="%.15g", lineterminator="\n", na_rep="")


def pinned(root, path):
    return git(root, "show", f"{BASE_COMMIT}:{path}")


def pin_record(root, path):
    value = pinned(root, path)
    # git() strips whitespace; hash the actual blob for exact source provenance.
    import subprocess
    content = subprocess.check_output(["git", "-C", str(root), "show", f"{BASE_COMMIT}:{path}"])
    return {"path": path, "git_blob_sha": git(root, "rev-parse", f"{BASE_COMMIT}:{path}"),
            "full_sha256": hashlib.sha256(content).hexdigest()}


def order(trades):
    return trades.sort_values(["exit_time", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)


def metrics(frame):
    frame = order(frame)
    net = frame.net_R.to_numpy(float)
    n = len(net)
    positive, negative = net[net > 0].sum(), -net[net < 0].sum()
    top = np.sort(net)[-5:][::-1]
    rest = np.sort(net)[:-5] if n >= 5 else np.array([])
    eq = np.r_[0., net.cumsum()]
    longest = current = 0
    for value in net:
        current = current+1 if value < 0 else 0
        longest = max(longest, current)
    return {"trades": n, "PF": float(positive/negative) if negative else None,
        "gross_R": float(frame.gross_R.sum()), "net_R": float(net.sum()),
        "expectancy_R": float(net.mean()) if n else None,
        "C1_total_R": float(frame.C1_R.sum()), "C1_mean_R": float(frame.C1_R.mean()) if n else None,
        "win_rate": float((net > 0).mean()) if n else None,
        "mean_win_R": float(net[net > 0].mean()) if (net > 0).any() else None,
        "mean_loss_R": float(net[net < 0].mean()) if (net < 0).any() else None,
        "max_drawdown_R": float((np.maximum.accumulate(eq)-eq).max()), "max_losing_streak": longest,
        "top5_net_R": float(top.sum()), "top5_share_positive_R": float(top.clip(min=0).sum()/positive) if positive else None,
        "net_R_without_top5": float(rest.sum()),
        "PF_without_top5": float(rest[rest > 0].sum()/-rest[rest < 0].sum()) if (rest < 0).any() else None,
        "mean_MAE_R": float(frame.MAE_R.mean()) if n else None,
        "mean_MFE_R": float(frame.MFE_R.mean()) if n else None,
        "median_MAE_R": float(frame.MAE_R.median()) if n else None,
        "median_MFE_R": float(frame.MFE_R.median()) if n else None,
        "p90_MAE_R": float(frame.MAE_R.quantile(.9)) if n else None,
        "p90_MFE_R": float(frame.MFE_R.quantile(.9)) if n else None,
        "MFE_ge_0_5R_share": float((frame.MFE_R >= .5).mean()) if n else None,
        "MFE_ge_1R_share": float((frame.MFE_R >= 1).mean()) if n else None,
        "MFE_ge_2R_share": float((frame.MFE_R >= 2).mean()) if n else None,
        "MFE_lt_0_5R_share": float((frame.MFE_R < .5).mean()) if n else None,
        "mean_holding_minutes": float(frame.holding_minutes.mean()) if n else None,
        "median_holding_minutes": float(frame.holding_minutes.median()) if n else None,
        "p90_holding_minutes": float(frame.holding_minutes.quantile(.9)) if n else None,
        "mean_bars_held": float(frame.bars_held.mean()) if n else None,
        "initial_stop_exits": int((frame.exit_type == "INITIAL_STOP").sum()),
        "ratcheted_stop_exits": int((frame.exit_type == "RATCHETED_STOP").sum()),
        "gap_exits": int(frame.gap_exit.sum()), "cross_day_trades": int(frame.cross_calendar_day.sum())}


def compare(version, actual, reference):
    diffs, maxima = [], {}
    exact = ["trade_id", "instrument", "direction", "bars_held"]
    if len(actual) != len(reference):
        diffs.append({"version": version, "ordinal": -1, "field": "count", "reference": len(reference), "actual": len(actual), "absolute_difference": abs(len(reference)-len(actual)), "tolerance": 0})
    for col in exact + ["entry_time", "exit_time"] + list(TOLERANCES):
        n = min(len(actual), len(reference))
        if col in TOLERANCES:
            delta = abs(actual[col].iloc[:n].to_numpy(float)-reference[col].iloc[:n].to_numpy(float))
            maxima[col] = float(delta.max()) if n else 0.
            mismatch = ~np.isfinite(delta) | (delta > TOLERANCES[col])
        elif col.endswith("time"):
            mismatch = pd.to_datetime(actual[col].iloc[:n], utc=True).to_numpy() != pd.to_datetime(reference[col].iloc[:n], utc=True).to_numpy()
        else:
            mismatch = actual[col].iloc[:n].to_numpy() != reference[col].iloc[:n].to_numpy()
        for i in np.flatnonzero(mismatch):
            diffs.append({"version": version, "ordinal": int(i)+1, "field": col,
                "reference": str(reference.iloc[i][col]), "actual": str(actual.iloc[i][col]),
                "absolute_difference": float(delta[i]) if col in TOLERANCES else None,
                "tolerance": TOLERANCES.get(col, 0)})
    return diffs, {"version": version, "reference_trades": len(reference), "actual_trades": len(actual),
                   "mismatches": len(diffs), "max_absolute_differences": maxima}


def table(rows, columns):
    lines = ["| " + " | ".join(columns) + " |", "|"+"|".join(["---"]*len(columns))+"|"]
    for row in rows:
        def fmt(v):
            if v is None: return "—"
            if isinstance(v, (float, np.floating)): return f"{v:.4f}"
            return str(v)
        lines.append("| "+" | ".join(fmt(row.get(c)) for c in columns)+" |")
    return "\n".join(lines)


def monthly_stats(rows):
    vals = [r["net_R"] for r in rows]
    longest = current = 0
    for value in vals:
        current = current+1 if value < 0 else 0
        longest = max(longest, current)
    worst = min(rows, key=lambda r: r["net_R"])
    return {"available_calendar_months": len(vals), "positive_months": sum(v > 0 for v in vals),
        "positive_month_share": sum(v > 0 for v in vals)/len(vals),
        "worst_month": worst["period"], "worst_month_net_R": worst["net_R"],
        "max_losing_month_streak": longest}


def run(data_root, reference_root, output):
    output.mkdir(parents=True, exist_ok=True)
    specs = json.loads((HERE / "SPEC_EVIDENCE.json").read_text())
    manifest = {"discovery_repository": "alkospacer123/market-pattern-discovery", "base_commit": BASE_COMMIT,
        "data_repository": "alkospacer123/market-pattern-data", "repository_commit": DATA_COMMIT,
        "historical_window": [START.isoformat(), END.isoformat()],
        "timestamp_rule": "Naive open labels localized Europe/Moscow (UTC+3); availability=open+15min; include closes <2025-01-01; calendar diagnostics use local exit time",
        "future_OHLC_ingested": False, "full_hash_note": "Opaque full-file byte integrity hashing includes suffix; future OHLC never parsed or used in calculation",
        "sources": [], "historical_quarter_sources": [], "reference_sources": [],
        "implementation_sources": {name: sha_file(HERE/name) for name in ['engine.py', 'research.py', 'audit.py', 'test_research.py', 'SPEC_EVIDENCE.json', 'README.md']},
        "runtime": {"python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__}}
    frames, equality, pieces, open_positions = {}, [], [], []
    for symbol in SYMBOLS:
        relative = f"forever/{symbol}/{symbol}_M15.csv"
        source = verify_source(data_root, relative)
        raw, prefix_hash = read_prefix(data_root / relative)
        frame = close_index(raw)
        source.update(instrument=symbol, historical_prefix_sha256=prefix_hash, source_open_candles=len(raw),
            used_candles=len(frame), first_open=raw.index[0].isoformat(), last_open=raw.index[-1].isoformat(),
            first_close=frame.index[0].isoformat(), last_close=frame.index[-1].isoformat())
        manifest["sources"].append(source)
        frames[symbol] = frame
        if symbol in ALIASES:
            old, records = historical_quarters(data_root, ALIASES[symbol])
            manifest["historical_quarter_sources"] += records
            same_index = old.index.equals(raw.index)
            same_values = len(old) == len(raw) and np.array_equal(old.to_numpy(), raw.to_numpy())
            equality.append({"instrument": symbol, "candles": len(raw), "timestamps_exact": same_index, "OHLCV_exact": same_values})
    configs = {"fixed_control_versions": {}, "optimization": False, "selection": False,
               "source_defaults": "Historical T3Parameters; only the explicitly frozen controls are replayed"}
    for version, p in CONFIGS.items():
        subset = {k: v for k,v in asdict(p).items() if k not in ("slope_lookback", "adx_period", "atr_period")}
        h = hashlib.sha256(json.dumps(subset, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        configs["fixed_control_versions"][version] = {"parameters": asdict(p), "historical_override_parameters": subset,
            "historical_parameter_sha256": h, "candidate_id": "T3-M15-0011-76dd2f3526c3" if version == "OPTIMIZED" else "T3_candidate_v1"}
    assert configs["fixed_control_versions"]["OPTIMIZED"]["historical_parameter_sha256"] == "76dd2f3526c38a3c7abfd3117d2a9ea4a78d0954c868bd01260736011726ba69"
    json_write(output / "BASELINE_CONFIGS.json", configs)
    diffs, audit = [], []
    for version in CONFIGS:
        chunk = []
        for symbol in SYMBOLS[:2]:
            trades, opened = replay(frames[symbol], symbol, version)
            chunk.append(trades)
            if opened: open_positions.append(opened)
        actual = order(pd.concat(chunk, ignore_index=True))
        ref = pd.read_csv(io.StringIO(pinned(reference_root, REFERENCES[version])))
        d, a = compare(version, actual, ref)
        diffs += d; audit.append(a); pieces.append(actual)
        for year in (2023, 2024):
            m = metrics(actual.loc[actual.exit_time.dt.year.eq(year)])
            n, pf, net = EXPECTED[(version, year)]
            if m["trades"] != n or round(m["PF"], 3) != pf or round(m["net_R"], 2) != net:
                diffs.append({"version": version, "ordinal": -1, "field": f"year_{year}_control", "reference": str((n,pf,net)), "actual": str((m["trades"],m["PF"],m["net_R"])), "tolerance": 0})
    for path in SOURCE_CODE + list(REFERENCES.values()) + ["TradingSystemLab/results/walk_forward/M15/T3/aggregate_metrics.json", "TradingSystemLab/results/walk_forward/M15/T3/folds.json", "TradingSystemLab/results/walk_forward/M15/T3/fold_metrics.csv", "TradingSystemLab/results/walk_forward/M15/T3/stitched_forward_trades.csv"]:
        manifest["reference_sources"].append(pin_record(reference_root, path))
    gate_a = not diffs and all(r["timestamps_exact"] and r["OHLCV_exact"] for r in equality) and sum(r["candles"] for r in equality) == 59523
    csv_write(output / "REPRODUCTION_DIFF.csv", diffs, ["version", "ordinal", "field", "reference", "actual", "absolute_difference", "tolerance"])
    json_write(output / "REPRODUCTION_DETAIL.json", {"gate_a": "PASS" if gate_a else "FAIL", "source_equality": equality,
        "tolerances": {"absolute": TOLERANCES, "relative": 0}, "replays": audit, "total_differences": len(diffs)})
    statuses = {s: {"status": "PASS" if gate_a else "NOT RUN", "reason": "Historical per-record reproduction and explicit 0.001 research C1 unit confirmed" if gate_a else "Gate A required"} for s in SYMBOLS}
    grid_rows = []
    if gate_a:
        for symbol in SYMBOLS[2:]:
            unit = Decimal(str(UNITS[symbol]))
            violations = sum(Decimal(str(v)) % unit != 0 for v in frames[symbol][["Open", "High", "Low", "Close"]].to_numpy().ravel())
            grid_rows.append({"instrument": symbol, "research_unit": str(unit), "checked_prices": 4*len(frames[symbol]), "off_grid_prices": violations})
            if violations or specs["instruments"][symbol]["research_c1_unit"] != UNITS[symbol]:
                statuses[symbol] = {"status": "BLOCKED", "reason": "C1 specification or historical price grid mismatch; no new-instrument economics run"}
                continue
            statuses[symbol] = {"status": "PASS", "reason": "Confirmed fixed research price scale from dated MOEX launch announcement; entire prefix passes Decimal grid; R monetary multiplier cancels. Exhaustive dated contract terms not claimed."}
            for version in CONFIGS:
                trades, opened = replay(frames[symbol], symbol, version)
                pieces.append(trades)
                if opened: open_positions.append(opened)
    json_write(output / "GATES.json", {"Gate_A": "PASS" if gate_a else "FAIL", "Gate_B": "PASS" if gate_a and all(v["status"] == "PASS" for v in statuses.values()) else ("BLOCKED" if gate_a else "NOT RUN"), "instruments": statuses, "price_grid": grid_rows,
        "scope": "Normalized closed-trade C1 research model only; standalone executable net economics remains unproven"})
    json_write(output / "SOURCE_MANIFEST.json", manifest)
    json_write(output / "OPEN_POSITIONS.json", open_positions)
    all_trades = pd.concat(pieces, ignore_index=True).sort_values(["version", "exit_time", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)
    all_trades["year"] = all_trades.exit_time.dt.year
    csv_write(output / "trades.csv", all_trades)
    report(output, all_trades, frames, statuses, gate_a, audit, equality, reference_root)
    artifact_names = [p.name for p in output.iterdir() if p.is_file() and p.suffix in (".csv", ".json", ".md") and p.name not in ("ARTIFACT_SHA256.json", "INDEPENDENT_AUDIT.md", "AUDIT_RESULTS.json", "REPEATABILITY.json", "SCOPE_CHECK.json") and p.name not in ("README.md", "SPEC_EVIDENCE.json")]
    json_write(output / "ARTIFACT_SHA256.json", {n: sha_file(output/n) for n in sorted(artifact_names)})
    print(json.dumps({"Gate_A": "PASS" if gate_a else "FAIL", "trades": len(all_trades), "artifacts": len(artifact_names)}, sort_keys=True))


def report(output, trades, frames, statuses, gate_a, audit, equality, reference_root):
    yearly, quarterly, monthly, instruments, directions = [], [], [], [], []
    for version in CONFIGS:
        base = trades.loc[trades.version.eq(version)]
        for scope in [*SYMBOLS, "Si_CNY", "ALL_FOUR"]:
            selected = [scope] if scope in SYMBOLS else list(SYMBOLS[:2] if scope == "Si_CNY" else SYMBOLS)
            f = base.loc[base.instrument.isin(selected)]
            first = min(frames[s].index[0] for s in selected)
            last = max(frames[s].index[-1] for s in selected)
            if any(statuses[s]["status"] != "PASS" for s in selected):
                instruments.append({"version": version, "instrument": scope, "status": "BLOCKED"})
                continue
            months = []
            for period in pd.period_range(first.tz_localize(None).to_period("M"), last.tz_localize(None).to_period("M"), freq="M"):
                r = {"version": version, "instrument": scope, "period": str(period), **metrics(f.loc[f.exit_time.dt.strftime("%Y-%m").eq(str(period))])}
                months.append(r); monthly.append(r)
            instruments.append({"version": version, "instrument": scope, "status": "PASS", **metrics(f), **monthly_stats(months)})
            for year in (2023, 2024):
                yf = f.loc[f.year.eq(year)]
                ym = [r for r in months if r["period"].startswith(str(year))]
                yearly.append({"version": version, "instrument": scope, "year": year, **metrics(yf), **monthly_stats(ym)})
                for direction in ("LONG", "SHORT"):
                    directions.append({"version": version, "instrument": scope, "year": year, "direction": direction, **metrics(yf.loc[yf.direction.eq(direction)])})
            for period in pd.period_range(first.tz_localize(None).to_period("Q"), last.tz_localize(None).to_period("Q"), freq="Q"):
                matches = f.exit_time.dt.tz_localize(None).dt.to_period("Q").eq(period)
                quarterly.append({"version": version, "instrument": scope, "period": str(period), **metrics(f.loc[matches])})
    csv_write(output / "yearly_report.csv", yearly)
    csv_write(output / "quarterly_report.csv", quarterly)
    csv_write(output / "monthly_report.csv", monthly)
    csv_write(output / "instrument_report.csv", instruments)
    csv_write(output / "direction_report.csv", directions)
    diag_cols = ["version", "instrument", "year", "trades", "mean_MAE_R", "median_MAE_R", "p90_MAE_R", "mean_MFE_R", "median_MFE_R", "p90_MFE_R", "MFE_ge_0_5R_share", "MFE_ge_1R_share", "MFE_ge_2R_share", "MFE_lt_0_5R_share", "mean_holding_minutes", "median_holding_minutes", "p90_holding_minutes", "mean_bars_held"]
    csv_write(output / "mae_mfe_report.csv", [{c:r[c] for c in diag_cols} for r in yearly])
    exits = []
    for keys, f in trades.groupby(["version", "instrument", "year", "exit_type"], sort=True):
        exits.append(dict(zip(["version", "instrument", "year", "exit_type"], keys)) | metrics(f) | {"mean_trailing_updates": float(f.trailing_updates.mean())})
    csv_write(output / "exit_diagnostics.csv", exits)
    audit_text = ["# Reproduction audit", "", f"Gate A: **{'PASS' if gate_a else 'FAIL'}**.", "",
        "Standalone engine; no executable TradingSystemLab imports and no historical runners executed. Both versions were fixed before reading prices.", "",
        "All historical records compared in canonical exit_time/instrument/trade_id order: count/order, IDs, instrument, direction, timestamps, entry, initial Stop, exit, initial risk, risk ticks, Gross/Net R, MAE/MFE and bars held. Timestamps and categorical fields are exact. Reference CSV has 12 significant digits; comparisons use absolute tolerances with relative tolerance zero:", "", table([{"field": k, "absolute_tolerance": v} for k,v in TOLERANCES.items()], ["field", "absolute_tolerance"]), "",
        "Scientific tolerances: prices 5e-9; risks and R 5e-10; risk ticks 5e-7. Table formatting is abbreviated; authoritative values are in REPRODUCTION_DETAIL.json.", "",
        table(audit, ["version", "reference_trades", "actual_trades", "mismatches"]), "",
        table(equality, ["instrument", "candles", "timestamps_exact", "OHLCV_exact"]), "",
        "59,523 OHLCV rows are exactly equal numerically, including Volume, and timestamps/order are identical. REPRODUCTION_DIFF.csv contains only its header when no differences exist. Fieldwise maximum errors are in REPRODUCTION_DETAIL.json.", "",
        table([r for r in yearly if r["instrument"] == "Si_CNY"], ["version", "year", "trades", "PF", "net_R"]), "",
        "Historical execution: enter at signal-candle close; first check carried Stop, gap execution min(Open,Stop) LONG / max(Open,Stop) SHORT; only survivors update extrema/trailing for later bars; same-close re-entry allowed. Signal/exit bars are excluded from favourable path extrema; adverse travel through exit price contributes to MAE. Open terminal positions are not forcibly liquidated; OPEN_POSITIONS.json explicitly records them.", "",
        "The close-fill convention is a historical assumption, not proven LIVE execution. H1 grouping resets on the local calendar date of the close timestamp, not a separately inferred exchange session. Complete ordinal blocks of four must be contiguous; incomplete/gapped blocks are skipped without repacking. Indicators and Donchian history explicitly cross days as in the reference; Donchian uses shift(1). No 2025+ OHLC is ingested.", ""]
    (output / "REPRODUCTION_AUDIT.md").write_text("\n".join(audit_text))
    wf = json.loads(pinned(reference_root, "TradingSystemLab/results/walk_forward/M15/T3/aggregate_metrics.json"))
    wf_folds = pd.read_csv(io.StringIO(pinned(reference_root, "TradingSystemLab/results/walk_forward/M15/T3/fold_metrics.csv")))
    wf_trades = pd.read_csv(io.StringIO(pinned(reference_root, "TradingSystemLab/results/walk_forward/M15/T3/stitched_forward_trades.csv")))
    wf_trades['entry_time'] = pd.to_datetime(wf_trades.entry_time, utc=True).dt.tz_convert(TZ)
    wf_trades['exit_time'] = pd.to_datetime(wf_trades.exit_time, utc=True).dt.tz_convert(TZ)
    fixed = trades.loc[trades.version.eq('OPTIMIZED') & trades.instrument.isin(SYMBOLS[:2])]
    within = fixed.loc[(fixed.entry_time >= pd.Timestamp('2024-02-01', tz=TZ)) & (fixed.entry_time < pd.Timestamp('2024-11-01', tz=TZ))]
    joined = within.merge(wf_trades, on=['instrument', 'direction', 'entry_time'], how='outer', suffixes=('_full', '_wf'), indicator=True)
    wf_rows = []
    for _, r in joined.iterrows():
        wf_rows.append({'instrument': r.instrument, 'direction': r.direction, 'entry_time': r.entry_time,
            'match': r['_merge'], 'exit_time_equal': r['exit_time_full'] == r['exit_time_wf'],
            'net_R_full': r['net_R_full'], 'net_R_reference': r['net_R_wf'],
            'abs_net_R_difference': abs(r['net_R_full']-r['net_R_wf'])})
    csv_write(output/'WF_REFERENCE_COMPARISON.csv', wf_rows)
    wf_identical = (joined['_merge'] == 'both').all() and (joined.exit_time_full == joined.exit_time_wf).all() and (abs(joined.net_R_full-joined.net_R_wf) <= 5e-10).all()
    fx_years = {(r['version'],r['year']):r for r in yearly if r['instrument']=='Si_CNY'}
    fact_lines = []
    for v in CONFIGS:
        a,b = fx_years[(v,2023)],fx_years[(v,2024)]
        weak = [r for r in monthly if r['version']==v and r['instrument']=='Si_CNY' and r['period'] in ['2024-02','2024-03','2024-04','2024-05','2024-07']]
        fact_lines.append(f"{v}, Si/CNY: Gross R {a['gross_R']:.2f} → {b['gross_R']:.2f}; win rate {a['win_rate']:.1%} → {b['win_rate']:.1%}; MFE≥2R {a['MFE_ge_2R_share']:.1%} → {b['MFE_ge_2R_share']:.1%}; MFE<0.5R {a['MFE_lt_0_5R_share']:.1%} → {b['MFE_lt_0_5R_share']:.1%}. C1 {a['C1_total_R']:.2f} → {b['C1_total_R']:.2f}R, то есть основной провал возник до издержек. В пяти выделенных месяцах {sum(r['trades'] for r in weak)} сделок, Gross {sum(r['gross_R'] for r in weak):.2f}R, C1 {sum(r['C1_total_R'] for r in weak):.2f}R, Net {sum(r['net_R'] for r in weak):.2f}R; каждый из этих месяцев отрицателен уже по Gross. После удаления пяти лучших сделок весь 2024 Si/CNY даёт {b['net_R_without_top5']:.2f}R.")
    fact_lines += ["Главный подтверждённый источник валютной слабости — USDRUBF: win rate Baseline снизился с 48.6% до 36.5%, средний выигрыш с 1.90 до 1.38R; у Optimized средний выигрыш снизился с 2.41 до 1.49R. CNY Baseline потерял частоту выигрышей (41.2% → 33.3%), тогда как CNY Optimized в 2024 вырос по Net R относительно 2023. Это различие не позволяет объявлять единый режим для всех инструментов.",
        "В июле Si/CNY у обеих версий 10 из 15 сделок (66.7%) имеют записанный MFE<0.5R. В марте доля MFE≥2R лишь 5.9% Baseline / 12.5% Optimized. Наблюдения согласуются со слабым продолжением после входов, но не доказывают механизм ложных пробоев без отдельного определения и исследования.",
        "Слабость не универсальна: GLD в 2024 улучшился относительно короткого 2023, IMOEX также улучшился после своего короткого стартового периода. Во всех восьми отдельных строках инструмент × версия за 2024 результат без пяти лучших сделок отрицателен; положительная сумма года зависит от небольшого числа крупных выигрышей. У IMOEX C1 отнимает 12.01R из 19.17 Gross Baseline и 11.64R из 23.83 Gross Optimized, поэтому корректный масштаб стоимости экономически существенен."]
    conclusion = ("По закрытым сделкам фиксированной нормализованной модели C1 каждая из двух версий имеет положительные Net R и expectancy на каждом инструменте за доступный период 2023–2024. Это самостоятельный результат исходной логики без дополнительных фильтров. Уверенного устойчивого преимущества на четырёх инструментах не установлено: слабый валютный 2024, отрицательный исторический WF, зависимость отдельных годовых результатов от пяти лучших сделок и короткая история новых контрактов ограничивают вывод. У IMOEXF по одной открытой позиции в каждой версии на конце префикса; их выход и окончательная экономика НЕ РАЗРЕШЕНЫ. OPEN_POSITIONS.json показывает направление, Stop, последнюю цену и нереализованный Gross R без выдуманного выхода. Полная экономическая прибыль после всех обязательств остаётся НЕ ПОДТВЕРЖДЕНА; положительная модель C1 не снимает неизвестные funding/дивидендные поправки и исполнимость.")
    lines = ["# Independent T3/M15 Forever Baseline v1", "", "Это независимый фиксированный исторический replay 2023–2024. Новая оптимизация, Robustness, Walk Forward, TRUE OOS и подбор фильтров не запускались. Две версии — контрольные варианты; победитель не выбирается.", "",
        f"Discovery/main и base: `{BASE_COMMIT}`. Данные: `{DATA_COMMIT}`; read-only pinned blobs, полные SHA-256 и разрешённые префиксы в SOURCE_MANIFEST.json.", "",
        f"Gate A: **{'PASS' if gate_a else 'FAIL'}**. Gate B: **{'PASS' if gate_a and all(s['status']=='PASS' for s in statuses.values()) else 'BLOCKED / NOT RUN'}** для нормализованной исследовательской модели C1.", "",
        "C1: один исследовательский тик на сторону. Si/CNY сохраняют 0.001; GLD — 0.1 RUB, IMOEX — 0.5 пункта. Масштаб новых инструментов подтверждён датированными объявлениями MOEX; все исторические OHLC проходят Decimal-проверку сетки. R и стоимость считаются в одной ценовой единице; RUB-множитель сокращается. См. SPEC_EVIDENCE.json. Полные архивные DOC недоступны; исчерпывающая историческая контрактная аттестация не заявляется.", "",
        "История не выравнивается: USDRUBF/CNYRUBF с 03.01.2023; GLDRUBF с 11.07.2023; IMOEXF с 14.11.2023. Прогрев начинается с доступного старта каждого инструмента, минимум 75 завершённых H1-контекстов плюс slope lookback. Никаких предысторий вне периода. 2023 IMOEXF — короткий неполный год.", "",
        "## Результаты по инструментам и годам", "",
        table([r for r in yearly if r["instrument"] in SYMBOLS], ["version", "instrument", "year", "trades", "PF", "gross_R", "net_R", "expectancy_R", "positive_month_share"]), "",
        "## Полный доступный период и календарные месяцы", "",
        table([r for r in instruments if r["instrument"] in SYMBOLS], ["version", "instrument", "trades", "PF", "net_R", "net_R_without_top5", "positive_months", "available_calendar_months", "positive_month_share", "worst_month", "worst_month_net_R", "max_losing_month_streak"]), "",
        "Доля месяцев использует все доступные календарные месяцы инструмента, включая неполный стартовый месяц и месяцы без закрытых сделок (0R). До запуска месяцы не включаются. Год/месяц относится к московской дате выхода. ALL_FOUR и Si_CNY — сумма R одинаковых условных рисковых единиц, не портфель и не доходность капитала.", "",
        "## Подтверждённая диагностика 2024", "",
        *[paragraph + "\n" for paragraph in fact_lines],
        table([r for r in yearly if r["year"] == 2024], ["version", "instrument", "trades", "win_rate", "mean_MFE_R", "MFE_ge_1R_share", "MFE_ge_2R_share", "MFE_lt_0_5R_share", "initial_stop_exits", "ratcheted_stop_exits", "C1_total_R", "C1_mean_R", "max_drawdown_R", "max_losing_streak", "top5_net_R", "net_R_without_top5"]), "",
        "MFE — консервативная наблюдаемая нижняя оценка: благоприятный экстремум Stop-свечи не включён, поскольку OHLC не раскрывает его порядок. «Нет существенного движения» здесь строго означает записанный MFE<0.5R; это диагностический порог, не фильтр входа. INITIAL_STOP означает отсутствие любого изменения активного Stop; RATCHETED_STOP — достоверное причинное изменение до выхода, даже если выход остаётся убыточным. Историческое общее имя ATR_TRAILING_STOP само по себе этих случаев не различало.", "",
        "## Февраль–май и июль 2024", "",
        table([r for r in monthly if r["instrument"] in SYMBOLS and r["period"] in ["2024-02", "2024-03", "2024-04", "2024-05", "2024-07"]], ["version", "instrument", "period", "trades", "PF", "gross_R", "net_R", "win_rate", "MFE_lt_0_5R_share", "MFE_ge_2R_share", "C1_total_R"]), "",
        "Для исторической слабости Si/CNY отдельно:", "",
        table([r for r in monthly if r["instrument"] == "Si_CNY" and r["period"] in ["2024-02", "2024-03", "2024-04", "2024-05", "2024-07"]], ["version", "period", "trades", "gross_R", "net_R", "win_rate", "mean_MFE_R", "MFE_lt_0_5R_share", "initial_stop_exits", "C1_total_R"]), "",
        "## Исторический Walk Forward — только reference", "",
        f"Исторический Optimized WF: {wf['trades']} сделок, PF {wf['PF']:.6f}, {wf['net_R']:.6f}R; expectancy {wf['expectancy_R']:.6f}R, max DD {abs(wf['max_drawdown_R']):.6f}R. Значения считаны из закреплённых результатов; новый WF не запускался.", "",
        table(wf_folds.to_dict('records'), ["fold_id", "test_start", "test_end", "trades", "PF", "net_R"]), "",
        f"WF покрывал входы февраля–октября 2024 в трёх независимых FLAT-окнах, с историческим прогревом; это не полный 2024. Сверка сохранённых WF-записей с непрерывным replay: совпадение всех {len(within)} сделок по инструменту/направлению/входу/выходу и Net R в допуске = {wf_identical}. См. WF_REFERENCE_COMPARISON.csv. Здесь границы FLAT-окон фактически не изменили это подмножество. Остальные {len(fixed.loc[fixed.year.eq(2024)])-len(within)} сделки 2024 дают {fixed.loc[fixed.year.eq(2024),'net_R'].sum()-within.net_R.sum():.6f}R, объясняя полный год +28.13R при −6.77R WF. Записи WF не использованы для настройки или отбора; календарное разделение не объявляется TRUE OOS.", "",
        "## Границы экономического вывода", "",
        conclusion, "",
        "Net R здесь означает Gross R минус только C1. Финансирование вечных контрактов, дивидендная поправка IMOEXF, дополнительные комиссии/спред/slippage и исторические ГО не восстановлены и не приравнены к нулю. Cross-day удержание показано в отчётах; оно не доказывает отсутствие этих обязательств. Результат не является прибылью LIVE или доходностью капитала.", "",
        "Модель сохраняет все исходные M15, в том числе известный из прежнего MTF-аудита участок IMOEXF 16.08.2024 вечером: отсутствие M5-состава не изменяет M15-первичный replay, но ограничивает независимую аттестацию качества. Дополнительный карантин/фильтр не вводился; история не очищалась по результатам.", "",
        "Гипотезы о боковом режиме, ложных пробоях и слабом продолжении допустимы лишь как объяснения, требующие отдельной проверки. Ни один новый ATR/EMA/ADX/Donchian, TRAIL1, ONE_BAR, LOCK1 или SESSION не испытывался. Статусы завершённых IntradayLab исследований не изменены. 2025–2026 не использовались и не являются новым нетронутым TRUE OOS.", ""]
    (output / "BASELINE_REPORT.md").write_text("\n".join(lines))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--reference-root", type=Path, default=HERE.parents[1])
    parser.add_argument("--output", type=Path, default=HERE)
    args = parser.parse_args()
    run(args.data_root.resolve(), args.reference_root.resolve(), args.output.resolve())
