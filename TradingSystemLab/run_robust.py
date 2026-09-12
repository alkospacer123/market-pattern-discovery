"""Frozen T3 robustness study: path diagnostics and post-signal cost stress."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .core.backtester import Backtester
from .core.data_loader import DataLoader
from .core.portfolio import FixedRiskPortfolio
from .strategies.trend.T3_MTF_Trend import T3MTFTrend

SCENARIOS = {"C0": 0.0, "C0.5": 0.5, "C1": 1.0, "C2": 2.0}
# Source prices are RUB per currency unit.  The Si exchange quote step of one
# RUB per USD 1,000 therefore converts to 0.001 in these source price units.
TICK_SIZE = {"Si": 0.001, "CNY": 0.001}
IDENTITY = ["trade_id", "symbol", "direction", "entry_time", "exit_time", "exit_reason"]


def _stats(frame: pd.DataFrame) -> dict:
    r = frame["profit_R"].astype(float)
    gains, losses = r[r > 0].sum(), -r[r < 0].sum()
    cumulative = r.cumsum()
    dd = cumulative - cumulative.cummax().clip(lower=0)
    pf = gains / losses if losses else None
    return {"trades": len(frame), "net_R": r.sum(),
            "profit_factor": pf, "profit_factor_R": pf,
            "expectancy": r.mean(), "expectancy_R": r.mean(), "average_R": r.mean(),
            "max_drawdown": dd.min() if len(dd) else 0.0,
            "max_DD_R": dd.min() if len(dd) else 0.0, "win_rate": (r > 0).mean()}


def _svg(path: Path, title: str, series: list[tuple[str, np.ndarray]]) -> None:
    values = np.concatenate([v for _, v in series]) if series else np.array([0.0])
    lo, hi = min(0.0, float(values.min())), max(0.0, float(values.max()))
    span = hi - lo or 1.0
    colours = ["#2563eb", "#dc2626", "#059669", "#7c3aed"]
    lines = []
    for n, (label, vals) in enumerate(series):
        xs = np.linspace(55, 865, max(len(vals), 1))
        ys = 365 - (vals - lo) / span * 300
        points = " ".join(f"{x:.2f},{y:.2f}" for x, y in zip(xs, ys))
        lines.append(f'<polyline points="{points}" fill="none" stroke="{colours[n % 4]}" stroke-width="2"/>')
        lines.append(f'<text x="{60+n*150}" y="405" font-family="sans-serif" font-size="12" fill="{colours[n % 4]}">{label}</text>')
    path.write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
                    '<svg xmlns="http://www.w3.org/2000/svg" width="920" height="430">\n'
                    '<rect width="100%" height="100%" fill="white"/>\n'
                    f'<text x="20" y="28" font-family="sans-serif" font-size="18">{title}</text>\n'
                    + "\n".join(lines) + '\n</svg>\n', encoding="utf-8")


def _summary(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    groups = [("All", frame), ("Winning", frame[frame.profit_R > 0]),
              ("Losing", frame[frame.profit_R <= 0])]
    for name, group in groups:
        row = {"group": name, "trades": len(group)}
        for metric in ("MAE_R", "MFE_R"):
            row.update({f"median_{metric}": group[metric].median(), f"mean_{metric}": group[metric].mean(),
                        f"p75_{metric}": group[metric].quantile(.75), f"p90_{metric}": group[metric].quantile(.90)})
        rows.append(row)
    return pd.DataFrame(rows)


def _markdown(frame: pd.DataFrame) -> str:
    """Small dependency-free Markdown serializer for committed reports."""
    values = [[str(value) for value in row] for row in frame.itertuples(index=False, name=None)]
    return "\n".join(["| " + " | ".join(map(str, frame.columns)) + " |",
                      "| " + " | ".join(["---"] * len(frame.columns)) + " |"] +
                     ["| " + " | ".join(row) + " |" for row in values])


def run(data_root: Path, output: Path) -> dict:
    output = Path(output)
    for child in ("reports", "costs", "mae_mfe", "trades"):
        (output / child).mkdir(parents=True, exist_ok=True)
    scenario_frames = {}
    for scenario, ticks in SCENARIOS.items():
        pieces = []
        for symbol in ("Si", "CNY"):
            paths = [p for year in (2023, 2024) for p in sorted(
                (Path(data_root) / "2026" / symbol).glob(f"{symbol}_H1_{year}_Q*.csv"))]
            h1 = DataLoader().close_index(DataLoader().load_csv(paths))
            h4 = DataLoader.h4_from_h1(h1)
            pieces.append(Backtester(FixedRiskPortfolio(), cost_ticks_per_side=ticks,
                                     tick_size=TICK_SIZE[symbol]).run(T3MTFTrend(), symbol, h1, h4).trades)
        frame = pd.concat(pieces).sort_values(["exit_time", "symbol", "trade_id"], kind="mergesort").reset_index(drop=True)
        scenario_frames[scenario] = frame
        frame.to_csv(output / "trades" / f"trades_{scenario.replace('.', '_')}.csv", index=False)
    baseline_identity = scenario_frames["C0"][IDENTITY]
    if any(not baseline_identity.equals(frame[IDENTITY]) for frame in scenario_frames.values()):
        raise AssertionError("cost scenarios changed the frozen trade list")

    cost_rows = [{"scenario": name, "cost_ticks_per_side": SCENARIOS[name], **_stats(frame)}
                 for name, frame in scenario_frames.items()]
    costs = pd.DataFrame(cost_rows)
    costs.to_csv(output / "costs" / "cost_sensitivity.csv", index=False)
    c0 = scenario_frames["C0"]
    per_tick = 2 * c0.symbol.map(TICK_SIZE) / c0.initial_risk
    break_even_per_side = float(c0.gross_R.sum() / per_tick.sum())
    break_even = 2 * break_even_per_side
    (output / "costs" / "break_even_cost.json").write_text(json.dumps({
        "estimated_break_even_ticks": break_even,
        "method": "linear aggregate-net-R solution, reported as round-trip ticks (twice the equal per-side cost)"
    }, indent=2) + "\n", encoding="utf-8")
    (output / "costs" / "cost_report.md").write_text(
        "# Cost stress\n\nSignals and trade identities are invariant. Costs are tick-size-adjusted, per side.\n\n" +
        _markdown(costs) + "\n", encoding="utf-8")

    c0.to_csv(output / "mae_mfe" / "mae_mfe.csv", index=False)
    mae = _summary(c0)
    mae.to_csv(output / "mae_mfe" / "mae_mfe_summary.csv", index=False)
    (output / "mae_mfe" / "mae_mfe_report.md").write_text(
        "# MAE/MFE\n\nEntry and stop-exit candles are excluded from extrema.\n\n" + _markdown(mae) + "\n", encoding="utf-8")
    winners = c0[c0.gross_R > 0].copy()
    winners["exit_efficiency"] = winners.gross_R / winners.MFE_R.replace(0, np.nan)
    winners[["trade_id", "symbol", "direction", "gross_R", "MFE_R", "exit_efficiency"]].to_csv(
        output / "mae_mfe" / "exit_efficiency.csv", index=False)

    reports = {}
    for name, keys in (("instrument", ["symbol"]), ("direction", ["direction"])):
        rows = [{keys[0]: value, **_stats(group)} for value, group in scenario_frames["C1"].groupby(keys[0], sort=True)]
        pd.DataFrame(rows).to_csv(output / "reports" / f"{name}_report.csv", index=False)
        reports[name] = rows
    years = scenario_frames["C1"].assign(year=pd.to_datetime(scenario_frames["C1"].exit_time).dt.year)
    year_rows = [{"year": year, **_stats(group)} for year, group in years.groupby("year", sort=True)]
    pd.DataFrame(year_rows).to_csv(output / "reports" / "year_report.csv", index=False)
    concentration = []
    for scenario in ("C0", "C1"):
        positive = scenario_frames[scenario].profit_R.clip(lower=0)
        concentration.append({"scenario": scenario, **{f"top{n}": positive.nlargest(n).sum() / positive.sum() for n in (1, 3, 5, 10)}})
    pd.DataFrame(concentration).to_csv(output / "reports" / "profit_concentration.csv", index=False)

    c1s = _stats(scenario_frames["C1"])
    positives = all(row["net_R"] > 0 for row in reports["instrument"] + year_rows)
    top5 = concentration[1]["top5"]
    verdict = "ROBUST_CANDIDATE" if c1s["profit_factor"] > 1.3 and c1s["expectancy"] > 0 and positives and top5 < .5 else ("BORDERLINE" if c1s["expectancy"] > 0 else "NO_EDGE")
    final = f"""# T3 Robust Baseline

## Frozen strategy
T3_MTF_Trend_v1.0: H4 EMA100/slope/ADX14/ATR expansion; H1 Donchian 20; SL 2 ATR; trailing 3 ATR. No parameter or signal changes.

## Dataset
Si and CNY, 2023–2024 only. Calendar 2025+ is rejected before indicator calculation.

## Cost stress
C0 PF {cost_rows[0]['profit_factor']:.4f}, net R {cost_rows[0]['net_R']:.4f}; C1 PF {c1s['profit_factor']:.4f}, expectancy {c1s['expectancy']:.4f} R, net R {c1s['net_R']:.4f}. Break-even {break_even:.4f} round-trip ticks.

## MAE/MFE
See `mae_mfe/mae_mfe_report.md`; path statistics are collected sequentially, excluding entry and stop candles.

## Exit efficiency
See `mae_mfe/exit_efficiency.csv`.

## Instrument robustness
See `reports/instrument_report.csv` (C1).

## Direction robustness
See `reports/direction_report.csv` (C1).

## Year robustness
See `reports/year_report.csv` (C1; 2023 and 2024 only).

## Profit concentration
C1 top-5 share of positive R: {top5:.4f}.

## Final verdict
**{verdict}**
"""
    (output / "reports" / "final_report.md").write_text(final, encoding="utf-8")
    (output / "final_report.md").write_text(final, encoding="utf-8")
    _svg(output / "reports" / "equity_C0.svg", "C0 cumulative net R", [("C0", c0.profit_R.cumsum().to_numpy())])
    _svg(output / "reports" / "equity_C1.svg", "C1 cumulative net R", [("C1", scenario_frames['C1'].profit_R.cumsum().to_numpy())])
    _svg(output / "reports" / "cost_sensitivity.svg", "Cost sensitivity", [("net R", costs.net_R.to_numpy())])
    _svg(output / "reports" / "mae_mfe_distribution.svg", "MAE and MFE by trade", [("MAE R", c0.MAE_R.to_numpy()), ("MFE R", c0.MFE_R.to_numpy())])
    return {"costs": cost_rows, "break_even": break_even, "mae_mfe": mae.to_dict("records"), "verdict": verdict}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("TradingSystemLab/results/T3_robust"))
    args = parser.parse_args()
    run(args.data_root, args.output)
