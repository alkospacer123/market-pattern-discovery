"""Produce the reproducible T1/T3 execution-unit audit (development data only)."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd

from .run_robust import SCENARIOS, TICK_SIZE, _stats

AUDIT = Path("TradingSystemLab/results/execution_units_audit")


def _observed_increment(data_root: Path, symbol: str) -> float:
    values: list[np.ndarray] = []
    for year in (2023, 2024):
        for path in sorted((data_root / "2026" / symbol).glob(f"{symbol}_H1_{year}_Q*.csv")):
            raw = pd.read_csv(path, sep=";")
            for column in ("<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>"):
                values.append(raw[column].dropna().astype(float).unique())
    unique = np.unique(np.concatenate(values))
    positive = np.diff(unique)
    return float(positive[positive > 1e-12].min())


def _read(strategy: str, scenario: str) -> pd.DataFrame:
    if strategy == "T3":
        name = scenario.replace(".", "_")
        return pd.read_csv(Path("TradingSystemLab/results/T3_robust/trades") / f"trades_{name}.csv")
    # T1 only persisted C0 historically; costs are post-signal and derived exactly.
    base = pd.read_csv("TradingSystemLab/results/T1_robust/mae_mfe.csv")
    ticks = SCENARIOS[scenario]
    base["cost_R"] = 2 * ticks * base.symbol.map(TICK_SIZE) / base.initial_risk
    base["profit_R"] = base.gross_R - base.cost_R
    return base


def generate(data_root: Path) -> None:
    AUDIT.mkdir(parents=True, exist_ok=True)
    units = {}
    for symbol in ("Si", "CNY"):
        observed = _observed_increment(Path(data_root), symbol)
        units[symbol] = {
            "configured_tick_size": TICK_SIZE[symbol],
            "observed_min_positive_price_increment": observed,
            "source": ("TradingSystemLab/configs/Si.yaml; exchange quote point converted "
                       "to repository RUB/USD price units" if symbol == "Si" else
                       "TradingSystemLab/configs/CNY.yaml; instrument configuration"),
            "status": "OK" if observed + 1e-12 >= TICK_SIZE[symbol] else "MISMATCH",
        }
    (AUDIT / "instrument_units.json").write_text(json.dumps(units, indent=2) + "\n")

    diagnostics, summaries, comparison = [], [], []
    for strategy in ("T1", "T3"):
        c0 = _read(strategy, "C0")
        risk_ticks = c0.initial_risk / c0.symbol.map(TICK_SIZE)
        for row, rt in zip(c0.itertuples(index=False), risk_ticks):
            diagnostics.append({"trade_id": row.trade_id, "strategy": strategy,
                "symbol": row.symbol, "entry_price": row.entry_price,
                "initial_stop": row.initial_stop, "initial_risk_points": row.initial_risk,
                "tick_size": TICK_SIZE[row.symbol], "initial_risk_ticks": rt,
                "gross_R": row.gross_R, "cost_R_C05": 1 / rt,
                "cost_R_C1": 2 / rt, "cost_R_C2": 4 / rt})
        summaries.append({"strategy": strategy, "mean": risk_ticks.mean(),
            "p10": risk_ticks.quantile(.1), "p25": risk_ticks.quantile(.25),
            "p50": risk_ticks.quantile(.5), "p75": risk_ticks.quantile(.75),
            "p90": risk_ticks.quantile(.9), "minimum": risk_ticks.min(),
            "maximum": risk_ticks.max(),
            "status": "CRITICAL_UNIT_ERROR" if risk_ticks.median() <= 2 else "OK"})
        for scenario in SCENARIOS:
            frame = _read(strategy, scenario)
            stats = _stats(frame)
            comparison.append({"strategy": strategy, "scenario": scenario,
                "trades": stats["trades"], "PF_R": stats["profit_factor_R"],
                "expectancy_R": stats["expectancy_R"], "net_R": stats["net_R"],
                "average_cost_R_per_trade": frame.cost_R.mean(),
                "median_cost_R_per_trade": frame.cost_R.median(), "max_DD_R": stats["max_DD_R"]})
    pd.DataFrame(diagnostics).to_csv(AUDIT / "trade_unit_diagnostics.csv", index=False)
    pd.DataFrame(summaries).to_csv(AUDIT / "risk_in_ticks_summary.csv", index=False)
    pd.DataFrame(comparison).to_csv(AUDIT / "corrected_cost_comparison.csv", index=False)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    generate(parser.parse_args().data_root)
