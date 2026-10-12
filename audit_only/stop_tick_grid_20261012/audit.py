"""Read-only STOP/TICK GRID diagnostics. No strategy edits, transport, or backtest outputs.

All SQLite files are disposable diagnostic state in --scratch. The rounding
formula below is a mathematical proposal check, never installed in the runtime.
No profitability calculation is performed on adjusted prices.
"""
from __future__ import annotations
import argparse
from decimal import Decimal, ROUND_FLOOR, ROUND_CEILING
import hashlib
import json
from pathlib import Path
import socket
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
def deny_network(*args, **kwargs):
    raise AssertionError("AUDIT_NETWORK_CONNECTION_FORBIDDEN")
socket.socket.connect = deny_network
socket.socket.connect_ex = deny_network
socket.create_connection = deny_network

import pandas as pd
from TradingSystemLab.core.data_loader import DataLoader
from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation.stage5_trail1_lifecycle import run_t3
from TradingSystemLab.stage8_robot.authority_replay import frozen_parameters, replay_authority
from TradingSystemLab.stage8_robot.context_builder import T3ContextBuilder
from TradingSystemLab.stage8_robot.historical_conformance import authenticate, reconcile, HASHES, sha, DATA_COMMIT, T3_SHA, TRAIL_SHA, PARAM_SHA, LEDGER_SHA
from TradingSystemLab.stage8_robot.margin import MarginBatchBudget, cap_r15_by_margin
from TradingSystemLab.stage8_robot.production_replay import replay_production
from TradingSystemLab.stage8_robot.production_runtime import InstrumentAuthority, ProductionRuntime
from TradingSystemLab.stage8_robot.risk import ContractEconomics, size_position
from TradingSystemLab.stage8_robot.strategy_core import CompletedBar, DecisionCore, PositionState, T3Context, SignalIntent
from TradingSystemLab.stage8_robot.trail1_state import Trail1State

D = lambda x: Decimal(str(x))
PROD = "184e8c2b8fa092a606249ff293a4f507160bff29"
MAIN = "688560ec2e8a71c1085bec255a9660783b51e122"
S5 = ROOT / "TradingSystemLab/results/post_v3_analysis/stage5_structural_validation"
S6 = ROOT / "TradingSystemLab/results/post_v3_analysis/stage6_fixed_basket_reassessment"
REGISTRY = pd.read_csv(ROOT / "TradingSystemLab/stage8_robot/production_instrument_registry.csv", keep_default_na=False).set_index("research_symbol")

def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n")

def authenticate_exact_sources(data_root):
    # Existing authenticate() now normalizes CRLF, but the frozen market-data
    # hashes are RAW Git-blob hashes. Report that pre-existing mismatch and
    # independently require exact source bytes, never alter source line endings.
    try:
        authenticate(data_root)
        existing = "PASS"
    except RuntimeError as exc:
        existing = str(exc)
    m = json.loads((S6 / "trail1_authoritative_ledger_manifest.json").read_text())
    checks = {
        "row_count": m["row_count"] == 418,
        "committed_sha": m["committed_file_sha256"] == LEDGER_SHA == sha(S6 / "trail1_authoritative_trades.csv"),
        "event_hash": m["event_hash"] == LEDGER_SHA,
        "t3": m["t3_sha"] == T3_SHA == sha(ROOT / "TradingSystemLab/strategies/trend/T3_MTF_Trend.py"),
        "trail": m["trail1_implementation_sha"] == TRAIL_SHA == sha(S5 / "stage5_trail1_execution.py"),
        "parameter": m["parameter_sha"] == PARAM_SHA,
        "data_commit": m["data_commit"] == DATA_COMMIT == subprocess.check_output(["git", "-C", str(data_root), "rev-parse", "HEAD"], text=True).strip(),
        "lifecycle_registry": m["lifecycle_registry_sha"] == sha(S5 / "canonical_lifecycle_registry.csv"),
        "repeated": m["repeated_replay_hashes"] == [LEDGER_SHA, LEDGER_SHA],
        "instruments": set(m["instruments"]) == set(HASHES),
        "lifecycles": set(m["lifecycle_coverage"]) == {"baseline", "walk_forward", "historical_true_oos"},
    }
    for symbol, digest in HASHES.items():
        rel = f"forever/{symbol}/{symbol}_H1.csv"
        raw = (data_root / rel).read_bytes()
        blob = subprocess.check_output(["git", "-C", str(data_root), "show", f"{DATA_COMMIT}:{rel}"])
        checks["raw_h1_" + symbol] = raw == blob and hashlib.sha256(raw).hexdigest() == digest == m["raw_h1_source_hashes"][rel]
    assert all(checks.values()), checks
    frozen_parameters()
    return {"byte_exact_source_checks": checks, "existing_authenticate_function": existing,
            "data_hash_contract": "Frozen raw Git-blob hashes, including CRLF; sources unchanged"}

def economics(symbol):
    row = REGISTRY.loc[symbol]
    return ContractEconomics(D(row.price_step), D(row.tick_value), int(row.quantity_granularity), True)

def authority(symbol):
    # Synthetic margins, expressly not historical FINAM account authority.
    c = economics(symbol)
    return InstrumentAuthority(symbol, REGISTRY.loc[symbol].finam_symbol, c.price_step, c.tick_value, c.quantity_granularity, D(100), D(120))

def aligned(value, step):
    ticks = D(value) / step
    return ticks == ticks.to_integral_value()

def classify(signal, meta):
    c = economics(signal.instrument)
    entry, stop = D(signal.entry), D(signal.initial_stop)
    ticks = abs(entry - stop) / c.price_step
    try:
        sized = size_position(D(100000), entry, stop, c)
        status = "PASS_GRID" if sized.quantity else "ZERO_QUANTITY"
    except ValueError as exc:
        status = str(exc)
    nearest = abs(ticks - ticks.to_integral_value())
    return {**meta, "instrument": signal.instrument, "direction": signal.direction,
            "timestamp": signal.timestamp.isoformat(), "year": signal.timestamp.year,
            "entry": str(entry), "initial_stop": str(stop), "initial_r": str(D(signal.initial_r)),
            "price_step": str(c.price_step), "stop_ticks": str(ticks),
            "entry_on_grid": aligned(entry, c.price_step), "stop_on_grid": aligned(stop, c.price_step),
            "distance_on_grid": ticks == ticks.to_integral_value(),
            "near_grid_within_1e_10_ticks": nearest != 0 and nearest <= D("1e-10"),
            "sizing_status": status, "signal_id": signal.signal_id, "trade_id": signal.trade_id}

def scan(frame, symbol, meta):
    low, high = T3ContextBuilder().build(frame, frame.index[-1])
    cursor, sequence, position = -1, 0, None
    raw, admitted = [], []
    core = DecisionCore()
    for stamp, row in low.iterrows():
        while cursor + 1 < len(high) and high.index[cursor + 1] <= stamp:
            cursor += 1
        b = CompletedBar(stamp.to_pydatetime(), float(row.Open), float(row.High), float(row.Low), float(row.Close), float(row.ATR),
                         None if pd.isna(row.PriorHigh) else float(row.PriorHigh),
                         None if pd.isna(row.PriorLow) else float(row.PriorLow))
        if position is not None:
            outcome = core.manage(position, b)
            if outcome["event"] == "EXIT":
                admitted[-1]["completed"] = True
                admitted[-1]["exit_timestamp"] = stamp.isoformat()
                position = None
        if cursor < 0 or pd.isna(row.ATR):
            continue
        h = high.iloc[cursor]
        ctx = T3Context(float(h.Close), float(h.EMA100), float(h.EMA100Slope), float(h.ADX), float(h.ATR), float(h.ATRMean20), float(h.EMA50), float(h.EMA200))
        sig = core.signal(symbol, b, ctx, sequence + 1)
        if sig is None:
            continue
        record = classify(sig, meta)
        raw.append(record)
        if position is None:
            sequence += 1
            admitted.append({**record, "completed": False, "exit_timestamp": ""})
            position = PositionState(symbol, sig.direction, sig.entry, sig.initial_stop, sig.initial_stop, sig.entry,
                                     Trail1State(sig.direction, sig.entry, sig.initial_stop))
    return raw, admitted

def grouped(frame, keys):
    rows = []
    for key, f in frame.groupby(keys, dropna=False, sort=True):
        key = key if isinstance(key, tuple) else (key,)
        n = len(f)
        off = int(f.sizing_status.eq("STOP_NOT_ON_TICK_GRID").sum())
        rows.append({**dict(zip(keys, key)), "signals": n, "entry_on_grid": int(f.entry_on_grid.sum()),
                     "stop_on_grid": int(f.stop_on_grid.sum()), "distance_on_grid": int(f.distance_on_grid.sum()),
                     "stop_not_on_tick_grid": off, "off_grid_percent": off * 100 / n,
                     "near_grid_within_1e_10_ticks": int(f.near_grid_within_1e_10_ticks.sum())})
    return rows

def diagnose_runtime(records, scratch):
    runtime = ProductionRuntime(scratch / "historical-rejection.sqlite3")
    checked, on_grid = 0, []
    try:
        for r in records:
            if r["sizing_status"] != "STOP_NOT_ON_TICK_GRID":
                on_grid.append(r)
                continue
            sig = SignalIntent(r["signal_id"], r["trade_id"], r["instrument"], r["direction"], pd.Timestamp(r["timestamp"]).to_pydatetime(),
                               float(r["entry"]), float(r["initial_stop"]), float(r["initial_r"]), float(r["initial_stop"]))
            budget = MarginBatchBudget(D(1000000))
            action = runtime.plan_entry(sig, authority(sig.instrument), realized_equity=D(100000), budget=budget)
            assert action.kind == "SKIP_STOP_NOT_ON_TICK_GRID" and action.quantity == 0
            assert budget.remaining == D(1000000) and runtime.store.unresolved_intent_count() == 0 and runtime.open_positions() == {}
            checked += 1
    finally:
        runtime.close()
    return {"independent_funded_flat_plan_entry_off_grid_checks": checked, "on_grid_records_not_counted_as_rejected": len(on_grid),
            "equity": "100000 synthetic RUB", "available_cash": "1000000 synthetic RUB",
            "directional_margin": "LONG 100 / SHORT 120 synthetic RUB; no historical broker snapshots", "broker_orders": 0}

def matrix_checks(scratch):
    result = []
    for symbol in HASHES:
        c = economics(symbol)
        for side in ("LONG", "SHORT"):
            for case in ("integer_tick", "fractional_tick", "zero_r15_quantity", "margin_cap", "zero_margin"):
                entry = D(100)
                ticks = D("5.1") if case == "fractional_tick" else D(5)
                stop = entry + (-1 if side == "LONG" else 1) * ticks * c.price_step
                eq = c.tick_value if case == "zero_r15_quantity" else D(100000)
                im = D(100) if side == "LONG" else D(120)
                cash = D(0) if case == "zero_margin" else im * D("2.5") if case == "margin_cap" else D(1000000)
                sig = SignalIntent(f"{symbol}-{side}-{case}", f"trade-{symbol}-{side}-{case}", symbol, side,
                                   pd.Timestamp("2026-01-02T10:00:00+03:00").to_pydatetime(), float(entry), float(stop), float(abs(entry-stop)), float(stop))
                rt = ProductionRuntime(scratch / f"{symbol}-{side}-{case}.sqlite3")
                try:
                    b = rt.begin_batch(realized_equity=eq, available_cash=cash)
                    a = rt.plan_entry(sig, authority(symbol), realized_equity=eq, budget=b)
                    expected = "SKIP_STOP_NOT_ON_TICK_GRID" if case == "fractional_tick" else "SKIP_ZERO_CAPACITY" if case in ("zero_r15_quantity", "zero_margin") else "ENTRY"
                    assert a.kind == expected
                    loss = abs(entry-stop) / c.price_step * c.tick_value
                    assert a.quantity * loss <= eq * D("0.015")
                    assert a.quantity * im <= cash and a.quantity % c.quantity_granularity == 0
                    if case == "margin_cap": assert a.quantity == 2
                    result.append({"instrument": symbol, "direction": side, "case": case, "action": a.kind,
                                   "quantity": a.quantity, "actual_initial_loss_cash": str(a.quantity * loss),
                                   "risk_budget": str(eq * D("0.015")), "margin_reserved": str(a.quantity * im), "status": "PASS"})
                finally:
                    rt.close()
    return result

def proposal_checks(records):
    rows = []
    for r in records:
        c = economics(r["instrument"])
        entry, stop = D(r["entry"]), D(r["initial_stop"])
        rounding = ROUND_FLOOR if r["direction"] == "LONG" else ROUND_CEILING
        adjusted = (stop / c.price_step).to_integral_value(rounding=rounding) * c.price_step
        if not aligned(entry, c.price_step):
            rows.append({"instrument": r["instrument"], "timestamp": r["timestamp"], "status": "ENTRY_OFF_GRID_REQUIRES_SEPARATE_POLICY"})
            continue
        new_r = abs(entry-adjusted)
        assert abs(entry-stop) <= new_r < abs(entry-stop) + c.price_step
        assert aligned(adjusted, c.price_step)
        base = size_position(D(100000), entry, adjusted, c)
        cap = cap_r15_by_margin(realized_equity=D(100000), entry=entry, stop=adjusted, price_step=c.price_step, tick_value=c.tick_value,
                               r15_quantity=base.quantity, available_cash=D(1000000), direction=r["direction"], initial_margin=D(100), trade_lot_size=c.quantity_granularity)
        assert cap.final_quantity <= base.quantity and cap.final_quantity * base.loss_per_contract <= D(1500)
        rows.append({"instrument": r["instrument"], "direction": r["direction"], "timestamp": r["timestamp"], "raw_stop": str(stop),
                     "executable_stop": str(adjusted), "raw_r": str(abs(entry-stop)), "executable_r": str(new_r),
                     "r_widening_ticks": str((new_r-abs(entry-stop))/c.price_step), "r15_quantity": base.quantity,
                     "capped_quantity": cap.final_quantity, "actual_initial_loss_cash": str(cap.final_quantity*base.loss_per_contract), "status": "PASS_MATH_ONLY"})
    return rows

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data-root", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--scratch", type=Path, required=True)
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    a.scratch.mkdir(parents=True, exist_ok=True)
    if any(a.scratch.iterdir()):
        raise ValueError("DIAGNOSTIC_SCRATCH_MUST_BE_EMPTY_NEVER_USE_PRODUCTION_STATE")
    checks = authenticate_exact_sources(a.data_root)
    registry = pd.read_csv(S5 / "canonical_lifecycle_registry.csv", keep_default_na=False)
    registry = registry[(registry.generation == "v3_perpetual") & (registry.strategy == "T3") & (registry.timeframe == "H1") & registry.instrument.isin(HASHES)]
    frames, coverage = {}, []
    for symbol in HASHES:
        path = a.data_root / "forever" / symbol / f"{symbol}_H1.csv"
        frame = DataLoader.close_index(DataLoader(forbid_true_oos=False).load_csv(path))
        frames[symbol] = frame
        coverage.append({"instrument": symbol, "h1_rows": len(frame), "first_close": frame.index[0].isoformat(),
                         "last_close": frame.index[-1].isoformat(), "sha256": HASHES[symbol]})
    raw, admitted, prod, auth = [], [], [], []
    for r in registry.to_dict("records"):
        frame = frames[r["instrument"]].loc[r["start_timestamp"]:r["end_timestamp"]].copy()
        meta = {k: r[k] for k in ("lifecycle", "fold_id", "instrument")}
        rr, aa = scan(frame, r["instrument"], meta)
        raw.extend(rr); admitted.extend(aa)
        prod.extend(replay_production(frame, r["instrument"], meta))
        auth.extend(replay_authority(frame, r["instrument"], meta))
    expected = pd.read_csv(S6 / "trail1_authoritative_trades.csv", keep_default_na=False)
    conformance = {"production": reconcile(expected, pd.DataFrame(prod), a.out / "production_reconciliation.csv"),
                   "research_authority": reconcile(expected, pd.DataFrame(auth), a.out / "authority_reconciliation.csv")}
    assert all(x["status"] == "PASS" for x in conformance.values())
    full, full_admitted = [], []
    for symbol, frame in frames.items():
        rr, aa = scan(frame, symbol, {"lifecycle": "full_available_continuous", "fold_id": ""})
        full.extend(rr); full_admitted.extend(aa)
    tables = {"lifecycle_raw_signals": raw, "lifecycle_admitted_entries": admitted,
              "full_available_raw_signals": full, "full_available_admitted_entries": full_admitted}
    summaries = {}
    for name, rows in tables.items():
        f = pd.DataFrame(rows)
        f.to_csv(a.out / f"{name}.csv", index=False, lineterminator="\n")
        summaries[name] = {"total": grouped(f, ["lifecycle"]), "instrument": grouped(f, ["lifecycle", "instrument"]),
                           "year": grouped(f, ["lifecycle", "year"]), "instrument_year": grouped(f, ["lifecycle", "year", "instrument"]),
                           "unique_instrument_timestamp_direction": len(f.drop_duplicates(["instrument", "timestamp", "direction"]))}
        if "completed" in f:
            summaries[name]["completed_trades"] = int(f.completed.sum())
            summaries[name]["terminal_open_entries"] = int((~f.completed).sum())
    runtime = diagnose_runtime(raw + full, a.scratch)
    matrix = matrix_checks(a.scratch)
    pd.DataFrame(matrix).to_csv(a.out / "runtime_matrix.csv", index=False)
    proposal = proposal_checks(admitted)
    pd.DataFrame(proposal).to_csv(a.out / "outward_rounding_math_only.csv", index=False)
    original_oos = pd.read_csv(ROOT / "TradingSystemLab/results/perpetual_v3/true_oos/T3/H1/trades.csv", keep_default_na=False)
    canonical_oos = []
    for r in registry[registry.lifecycle.eq("historical_true_oos")].to_dict("records"):
        frame = frames[r["instrument"]].loc[r["start_timestamp"]:r["end_timestamp"]].copy()
        meta = {k: r[k] for k in ("lifecycle", "fold_id", "instrument")}
        canonical_oos.extend(run_t3(frame, r["instrument"], frozen_parameters(), {**meta, "strategy": "T3", "timeframe": "H1"}, False))
    old = original_oos.rename(columns={"symbol": "instrument"}).copy()
    regenerated = pd.DataFrame(canonical_oos)
    sort = ["instrument", "entry_time", "direction"]
    for f in (old, regenerated):
        for col in ("entry_time", "exit_time"):
            f[col] = pd.to_datetime(f[col], utc=True).astype(str)
    old = old.sort_values(sort).reset_index(drop=True)
    regenerated = regenerated.sort_values(sort).reset_index(drop=True)
    mismatches = abs(len(old)-len(regenerated))
    for col in ("instrument", "entry_time", "exit_time", "direction", "exit_reason"):
        mismatches += int(old[col].ne(regenerated[col]).sum())
    for col in ("entry_price", "exit_price", "cost_R"):
        mismatches += int(old[col].map(lambda x: format(float(x), ".12g")).ne(regenerated[col].map(lambda x: format(float(x), ".12g"))).sum())
    assert mismatches == 0, ("ORIGINAL_CANONICAL_OOS_PRICE_PATH_REPLAY_MISMATCH", mismatches)
    # Already documented legacy accounting: _normalize_backtester labels
    # profit_R (after one C1) as gross_R; original TRUE OOS subtracts C1 again.
    # Verify the archived equations without rewriting any frozen result.
    gross_delta = (old.gross_R - (regenerated.gross_R-regenerated.cost_R)).abs()
    net_delta = (old.net_R_C1 - (regenerated.gross_R-2*regenerated.cost_R)).abs()
    assert float(gross_delta.max()) <= 1e-9 and float(net_delta.max()) <= 1e-9
    original_off = sum(not aligned(D(r["entry_price"])-D(r["initial_stop_price"]), economics(r["instrument"]).price_step) for r in canonical_oos)
    original_entry_off = sum(not aligned(r["entry_price"], economics(r["instrument"]).price_step) for r in canonical_oos)
    result = {"main_at_start": MAIN, "production_code_sha": PROD, "data_sha": "50f1fd2178c18b7ab3bd969be82ad01f47a34745",
              "authentication": checks, "coverage": coverage, "frozen_parameters": vars(frozen_parameters()),
              "conformance": conformance, "signal_counts": summaries, "runtime_rejection_checks": runtime,
              "runtime_matrix_checks": len(matrix), "proposal_math_checks": len(proposal),
              "proposal_entry_grid_exceptions": sum(x["status"] != "PASS_MATH_ONLY" for x in proposal),
              "original_canonical_oos_artifact": {"completed_trades": len(original_oos), "reconstructed_causal_off_grid_distances": int(original_off), "off_grid_entries": int(original_entry_off),
                                                   "price_time_direction_cost_replay_mismatches": mismatches,
                                                   "legacy_gross_R_equation": "actual_gross_R - C1", "legacy_net_R_C1_equation": "actual_gross_R - 2*C1",
                                                   "legacy_equation_max_delta": max(float(gross_delta.max()),float(net_delta.max())),
                                                   "stage6_basis": "Already accepted CORRECTED_SINGLE_C1; original OOS left unchanged",
                                                   "initial_stop_source": "Original serialized artifact omits initial_stop; independently reconstructed in canonical replay, no stop inferred from rounded cost_R"},
              "trail1_grid_diagnostic": {"completed_trades":len(prod), "stored_trigger_candidates":sum(r["stored_trail_candidate"] is not None for r in prod),
                                         "off_grid_stored_trigger_candidates":sum(r["stored_trail_candidate"] is not None and not aligned(r["stored_trail_candidate"],economics(r["instrument"]).price_step) for r in prod)},
              "classifications": {"RESEARCH_SIGNAL_CONFORMANCE": "PASS", "LIVE_EXECUTION_CONFORMANCE": "FAIL", "OOS_EXECUTABILITY_VERIFIED": "NO"},
              "PRODUCTION_CHANGES": "NONE", "real_broker_operations": 0,
              "recent_12_signal_claim": "UNVERIFIED: frozen data ends 2026-09-15; 2026-09-16 through 2026-10-11 not replayed"}
    write_json(a.out / "results.json", result)
    print(json.dumps({"conformance": conformance, "counts": {k: v["total"] for k, v in summaries.items()}, "matrix": len(matrix)}, ensure_ascii=False))

if __name__ == "__main__":
    main()
