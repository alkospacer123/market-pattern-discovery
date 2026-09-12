"""Cost and path robustness for the frozen T1 trade rules."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import pandas as pd

from .core.backtester import Backtester
from .core.portfolio import FixedRiskPortfolio
from .run_robust import SCENARIOS, TICK_SIZE, IDENTITY, _stats, _summary
from .run_t1_baseline import load_h1
from .strategies.trend.T1_BBW_Donchian import T1BBWDonchian


def run(data_root: Path, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    scenarios = {}
    for name, ticks in SCENARIOS.items():
        pieces = []
        for symbol in ("Si", "CNY"):
            h1 = load_h1(data_root, symbol)
            pieces.append(Backtester(FixedRiskPortfolio(), cost_ticks_per_side=ticks,
                tick_size=TICK_SIZE[symbol]).run(T1BBWDonchian(), symbol, h1, h1).trades)
        scenarios[name] = pd.concat(pieces).sort_values(
            ["exit_time", "symbol", "trade_id"], kind="mergesort").reset_index(drop=True)
    if any(not scenarios["C0"][IDENTITY].equals(frame[IDENTITY]) for frame in scenarios.values()):
        raise AssertionError("cost scenarios changed frozen trades")
    rows = [{"scenario": name, "cost_ticks_per_side": ticks, **_stats(scenarios[name])}
            for name, ticks in SCENARIOS.items()]
    pd.DataFrame(rows).to_csv(output / "cost_sensitivity.csv", index=False)
    c0, c1 = scenarios["C0"], scenarios["C1"]
    per_tick = 2 * c0.symbol.map(TICK_SIZE) / c0.initial_risk
    break_even = float(2 * c0.gross_R.sum() / per_tick.sum())
    (output / "break_even_cost.json").write_text(json.dumps({
        "estimated_break_even_ticks": break_even,
        "method": "linear aggregate net-R solution; round-trip ticks"
    }, indent=2) + "\n")
    c0.to_csv(output / "mae_mfe.csv", index=False)
    instrument = pd.DataFrame([{"symbol": key, **_stats(group)} for key, group in c1.groupby("symbol", sort=True)])
    direction = pd.DataFrame([{"direction": key, **_stats(group)} for key, group in c1.groupby("direction", sort=True)])
    dated = c1.assign(year=pd.to_datetime(c1.exit_time, utc=True).dt.year)
    years = pd.DataFrame([{"year": key, **_stats(group)} for key, group in dated.groupby("year", sort=True)])
    instrument.to_csv(output / "instrument_report.csv", index=False)
    direction.to_csv(output / "direction_report.csv", index=False)
    years.to_csv(output / "year_report.csv", index=False)
    concentration = []
    for name in ("C0", "C1"):
        positive = scenarios[name].profit_R.clip(lower=0)
        concentration.append({"scenario": name, **{f"top{n}": positive.nlargest(n).sum() / positive.sum()
                              for n in (1, 3, 5, 10)}})
    pd.DataFrame(concentration).to_csv(output / "profit_concentration.csv", index=False)
    stats = _stats(c1)
    positive_groups = (instrument.net_R.gt(0).all() and years.net_R.gt(0).all())
    top5 = concentration[1]["top5"]
    robust = stats["profit_factor"] is not None and stats["profit_factor"] > 1.3 and stats["expectancy"] > 0 and positive_groups and top5 < .5
    verdict = "ROBUST_CANDIDATE" if robust else ("BORDERLINE" if stats["expectancy"] > 0 else "NO_EDGE")
    report = f"""# T1 robustness report

Frozen `T1_BBW_Donchian_v1.0`; no parameter search. Si/CNY 2023–2024 only.

## Cost stress
C0 PF {rows[0]['profit_factor']:.6f}; C1 PF {stats['profit_factor']:.6f}, expectancy {stats['expectancy']:.6f} R, net {stats['net_R']:.6f} R. Break-even cost: {break_even:.6f} round-trip ticks.

## MAE/MFE and breakdowns
Shared backtester path measurements are in `mae_mfe.csv`. Instrument, direction,
year, and profit concentration reports use C1 net R. C1 top-five positive-R share: {top5:.6f}.

## Final verdict
**{verdict}**
"""
    (output / "final_report.md").write_text(report)
    return {"costs": rows, "break_even": break_even, "verdict": verdict}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("TradingSystemLab/results/T1_robust"))
    args = parser.parse_args()
    run(args.data_root, args.output)
