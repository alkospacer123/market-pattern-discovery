"""Offline causal-prefix/restart checks and mathematical proposal edge cases."""
from dataclasses import replace
import argparse
from decimal import Decimal, ROUND_FLOOR, ROUND_CEILING
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit import ROOT, S5, HASHES, D, economics, authority, deny_network, aligned, write_json
from TradingSystemLab.core.data_loader import DataLoader
from TradingSystemLab.stage8_robot.production_runtime import ProductionRuntime, ProductionRuntimeError
from TradingSystemLab.stage8_robot.risk import size_position
from TradingSystemLab.stage8_robot.trail1_state import Trail1State
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument("--data-root", type=Path, required=True)
parser.add_argument("--results-dir", type=Path, default=Path(__file__).resolve().parent)
parser.add_argument("--scratch", type=Path, required=True)
args = parser.parse_args()
HERE = args.results_dir
SCRATCH = args.scratch
SCRATCH.mkdir(parents=True, exist_ok=True)
if any(SCRATCH.iterdir()):
    raise ValueError("DIAGNOSTIC_SCRATCH_MUST_BE_EMPTY_NEVER_USE_PRODUCTION_STATE")
reg = pd.read_csv(S5 / "canonical_lifecycle_registry.csv", keep_default_na=False)
reg = reg[(reg.generation == "v3_perpetual") & (reg.strategy == "T3") & (reg.timeframe == "H1") & reg.instrument.isin(HASHES)]
entries = pd.read_csv(HERE / "lifecycle_admitted_entries.csv", keep_default_na=False, dtype={"entry":str, "initial_stop":str, "initial_r":str})
evidence, ohlc_grid = [], []
for symbol in HASHES:
    path = args.data_root / "forever" / symbol / f"{symbol}_H1.csv"
    frame = DataLoader.close_index(DataLoader(forbid_true_oos=False).load_csv(path))
    c = economics(symbol)
    ohlc_grid.append({"instrument": symbol, "rows":len(frame), "off_grid_ohlc":{col:sum(not aligned(x,c.price_step) for x in frame[col]) for col in ("Open","High","Low","Close")}})
    for direction in ("LONG", "SHORT"):
        r = entries[(entries.instrument == symbol) & (entries.direction == direction)].iloc[0]
        window = reg[(reg.instrument == symbol) & (reg.lifecycle == r.lifecycle) & (reg.fold_id == r.fold_id)].iloc[0]
        # Cut the source before construction: no future OHLC or context admitted.
        prefix = frame.loc[window.start_timestamp:r.timestamp].copy()
        state = SCRATCH / f"{symbol}-{direction}.sqlite3"
        rt = ProductionRuntime(state)
        sig = rt.build_latest_signal(symbol, prefix, prefix.index[-1].to_pydatetime())
        assert sig is not None and sig.direction == direction
        assert D(sig.entry) == D(r.entry) and D(sig.initial_stop) == D(r.initial_stop)
        key = sig.signal_id
        budget = rt.begin_batch(realized_equity=D(100000), available_cash=D(1000000))
        action = rt.plan_entry(sig, authority(symbol), realized_equity=D(100000), budget=budget)
        assert action.kind == "SKIP_STOP_NOT_ON_TICK_GRID" and budget.remaining == D(1000000)
        assert rt.store.unresolved_intent_count() == 0 and rt.open_positions() == {}
        rt.close()
        rt = ProductionRuntime(state)
        assert rt.build_latest_signal(symbol, prefix, prefix.index[-1].to_pydatetime()) is None
        assert rt.store.unresolved_intent_count() == 0
        rt.close()
        evidence.append({"instrument":symbol,"direction":direction,"timestamp":r.timestamp,"entry":r.entry,"initial_stop":r.initial_stop,
                         "stop_ticks":str(abs(D(r.entry)-D(r.initial_stop))/c.price_step), "signal_id":key,
                         "runtime_action":action.payload(),"prefix_only":True,"same_bar_after_restart":"NO_SIGNAL","status":"PASS"})

projection = []
for symbol in HASHES:
    c = economics(symbol)
    for side in ("LONG", "SHORT"):
        for ticks in ("5", "5.1", "5.5", "5.999999999999"):
            e = D(100)
            s = e + (-1 if side == "LONG" else 1) * D(ticks) * c.price_step
            q = (s/c.price_step).to_integral_value(rounding=ROUND_FLOOR if side == "LONG" else ROUND_CEILING)*c.price_step
            assert abs(e-q) >= abs(e-s) and abs(e-q)-abs(e-s) < c.price_step
            sized = size_position(D(100000),e,q,c)
            assert sized.quantity*sized.loss_per_contract <= D(1500)
            if ticks == "5": assert q == s
            projection.append({"instrument":symbol,"side":side,"raw_ticks":ticks,"exec_ticks":str(abs(e-q)/c.price_step),"quantity":sized.quantity,"status":"PASS"})
    rt = ProductionRuntime(SCRATCH/f"{symbol}-invalid.sqlite3")
    try:
        for bad in (replace(authority(symbol),price_step=D(0)),replace(authority(symbol),tick_value=D(0)),
                    replace(authority(symbol),long_initial_margin=D(0)),replace(authority(symbol),trade_lot_size=0)):
            try: rt._validate_instrument_authority(bad)
            except ProductionRuntimeError: pass
            else: raise AssertionError("INVALID_AUTHORITY_ACCEPTED")
    finally: rt.close()

# Explain the scope of equivalence without producing adjusted PnL/OOS results.
trail_equivalence = []
for side in ("LONG","SHORT"):
    e = D(100); s = D("99.949") if side=="LONG" else D("100.051")
    q = D("99.94") if side=="LONG" else D("100.06")
    raw = Trail1State(side,float(e),float(s)); executed = Trail1State(side,float(e),float(q))
    for n in range(-20,21):
        extreme = e+D(n)*D("0.01")
        old_reached = float(extreme)>=raw.trigger_price if side=="LONG" else float(extreme)<=raw.trigger_price
        new_reached = float(extreme)>=executed.trigger_price if side=="LONG" else float(extreme)<=executed.trigger_price
        assert old_reached == new_reached
    offgrid_extreme = 100.055 if side=="LONG" else 99.945
    assert (offgrid_extreme>=raw.trigger_price if side=="LONG" else offgrid_extreme<=raw.trigger_price)
    assert not (offgrid_extreme>=executed.trigger_price if side=="LONG" else offgrid_extreme<=executed.trigger_price)
    trail_equivalence.append({"direction":side,"raw_1R":str(abs(e-s)),"exec_1R":str(abs(e-q)),
                              "grid_extreme_threshold_checks":41,"thresholds_equal_on_grid":True,
                              "off_grid_extreme_counterexample":offgrid_extreme,"raw_trigger":True,"exec_trigger":False,
                              "limitation":"Numeric thresholds differ. Same trigger bars require grid OHLC, same entry, same tick step; exits/fills and exact Stage7 conformance remain changed."})
write_json(HERE/"supplemental_results.json", {"causal_prefix_runtime_rejections_and_restart":evidence,"ohlc_grid":ohlc_grid,
                                           "outward_projection_edge_checks":projection,"invalid_authority_checks":16,
                                           "trail1_threshold_checks":trail_equivalence,"real_broker_operations":0,"PRODUCTION_CHANGES":"NONE"})
print("PASS: 8 real causal-prefix/restart checks, 32 outward projection edges, 16 invalid authorities, 82 grid threshold checks")
