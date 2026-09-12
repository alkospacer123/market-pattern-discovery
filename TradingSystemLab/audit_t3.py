"""Reproducible, descriptive audit of the frozen T3 baseline artifacts.

This module does not run or alter the strategy.  It reads only the committed
baseline outputs and refuses the locked TRUE OOS period (2025 onward).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


BASELINE_DIR = Path(__file__).parent / "results" / "T3_baseline"
AUDIT_DIR = BASELINE_DIR / "audit"
OOS_START = pd.Timestamp("2025-01-01", tz="UTC")
RECONCILE_FIELDS = (
    "trades", "long_trades", "short_trades", "net_profit", "profit_factor",
    "expectancy", "average_R", "win_rate", "max_drawdown",
)


def _load_inputs(source: Path) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    with (source / "metrics.json").open(encoding="utf-8") as handle:
        frozen = json.load(handle)
    trades = pd.read_csv(source / "trades.csv")
    equity = pd.read_csv(source / "equity_curve.csv")
    required = {"symbol", "direction", "entry_time", "exit_time", "profit_R", "net_profit"}
    missing = required.difference(trades.columns)
    if missing:
        raise ValueError(f"trades.csv is missing required columns: {sorted(missing)}")
    for frame, columns in ((trades, ("entry_time", "exit_time")), (equity, ("time",))):
        for column in columns:
            if column not in frame:
                raise ValueError(f"input is missing date column: {column}")
            frame[column] = pd.to_datetime(frame[column], utc=True, errors="raise", format="mixed")
            if (frame[column] >= OOS_START).any():
                raise ValueError(f"TRUE OOS data (2025+) found in {column}")
    # Stable explicit tie breakers make the same trade order reproducible.
    trades = trades.sort_values(
        ["exit_time", "entry_time", "symbol", "direction"], kind="mergesort"
    ).reset_index(drop=True)
    equity = equity.sort_values(["time", "symbol"], kind="mergesort").reset_index(drop=True)
    return frozen, trades, equity


def _streak(values: pd.Series, winning: bool) -> int:
    best = current = 0
    for value in values:
        if (value > 0) == winning:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def _stats(trades: pd.DataFrame) -> dict:
    pnl = trades["net_profit"].astype(float)
    r = trades["profit_R"].astype(float)
    gains, losses = pnl[pnl > 0].sum(), -pnl[pnl < 0].sum()
    cumulative = pnl.cumsum()
    drawdown = cumulative - cumulative.cummax().clip(lower=0)
    max_dd = float(drawdown.min()) if len(drawdown) else 0.0
    net = float(pnl.sum())
    return {
        "trades": int(len(trades)),
        "long_trades": int((trades["direction"] == "LONG").sum()),
        "short_trades": int((trades["direction"] == "SHORT").sum()),
        "net_profit": net,
        "profit_factor": float(gains / losses) if losses else None,
        "expectancy": float(pnl.mean()) if len(pnl) else None,
        "average_R": float(r.mean()) if len(r) else None,
        "median_R": float(r.median()) if len(r) else None,
        "win_rate": float((pnl > 0).mean()) if len(pnl) else None,
        "max_drawdown": max_dd,
        "max_losing_streak": _streak(pnl, False),
        "max_winning_streak": _streak(pnl, True),
        "recovery_factor": float(net / abs(max_dd)) if max_dd else None,
    }


def _concentration(r: pd.Series) -> dict:
    positive = r[r > 0].sort_values(ascending=False)
    total = positive.sum()
    return {
        f"top_{n}_share_of_positive_R": float(positive.head(n).sum() / total) if total else None
        for n in (1, 3, 5, 10)
    }


def _svg(path: Path, title: str, elements: str, width: int = 900, height: int = 420) -> None:
    path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n'
        '<rect width="100%" height="100%" fill="white"/>\n'
        f'<text x="20" y="28" font-family="sans-serif" font-size="18">{title}</text>\n'
        f'{elements}\n</svg>\n', encoding="utf-8"
    )


def _line_svg(path: Path, trades: pd.DataFrame) -> None:
    r = trades["profit_R"].astype(float)
    cumulative = np.r_[0.0, r.cumsum().to_numpy()]
    peak = np.maximum.accumulate(cumulative)
    dd = cumulative < peak
    x = np.linspace(50, 870, len(cumulative))
    low, high = float(cumulative.min()), float(cumulative.max())
    span = high - low or 1.0
    y = 370 - (cumulative - low) / span * 310
    shaded = "".join(
        f'<rect x="{x[i]:.2f}" y="50" width="{max(1, x[i]-x[i-1]):.2f}" height="320" fill="#fee2e2"/>'
        for i in range(1, len(x)) if dd[i]
    )
    points = " ".join(f"{a:.2f},{b:.2f}" for a, b in zip(x, y))
    _svg(path, "T3 cumulative R (red = drawdown)", shaded +
         f'<polyline points="{points}" fill="none" stroke="#2563eb" stroke-width="2"/>')


def _histogram_svg(path: Path, trades: pd.DataFrame) -> None:
    counts, edges = np.histogram(trades["profit_R"].astype(float), bins=20)
    maximum = max(int(counts.max()), 1)
    bars = []
    for i, count in enumerate(counts):
        x, width = 50 + i * 41, 36
        height = 300 * int(count) / maximum
        bars.append(f'<rect x="{x}" y="{370-height:.2f}" width="{width}" height="{height:.2f}" fill="#2563eb"/>')
    labels = (f'<text x="50" y="400" font-family="sans-serif" font-size="12">{edges[0]:.2f} R</text>'
              f'<text x="820" y="400" font-family="sans-serif" font-size="12">{edges[-1]:.2f} R</text>')
    _svg(path, "T3 trade R distribution", "".join(bars) + labels)


def _maximum_drawdown_duration(trades: pd.DataFrame) -> int:
    cumulative = trades["profit_R"].astype(float).cumsum()
    peak = cumulative.cummax()
    start = None
    longest = 0
    for timestamp, underwater in zip(trades["exit_time"], cumulative < peak):
        if underwater and start is None:
            start = timestamp
        elif not underwater and start is not None:
            longest = max(longest, (timestamp - start).days)
            start = None
    if start is not None:
        longest = max(longest, (trades["exit_time"].iloc[-1] - start).days)
    return int(longest)


def _fmt(value: object) -> str:
    if value is None:
        return "NA"
    return f"{value:.6f}" if isinstance(value, float) else str(value)


def run_audit(source: Path = BASELINE_DIR, output: Path | None = None) -> dict:
    """Build the audit and return its statistics. Raises on OOS or mismatch."""
    source, output = Path(source), Path(output or source / "audit")
    frozen, trades, _equity = _load_inputs(source)
    overall = _stats(trades)
    for field in RECONCILE_FIELDS:
        if field not in frozen:
            raise ValueError(f"frozen metrics.json is missing {field}")
        expected, actual = frozen[field], overall[field]
        if not math.isclose(float(expected), float(actual), rel_tol=1e-10, abs_tol=1e-8):
            raise ValueError(f"frozen metric mismatch for {field}: {expected} != {actual}")

    r = trades["profit_R"].astype(float)
    distribution = {
        "mean_R": float(r.mean()), "median_R": float(r.median()),
        "standard_deviation_R": float(r.std(ddof=1)),
        "percentile_25_R": float(r.quantile(.25)), "percentile_75_R": float(r.quantile(.75)),
        "best_trade_R": float(r.max()), "worst_trade_R": float(r.min()), **_concentration(r),
    }
    instruments = {name: _stats(group) for name, group in trades.groupby("symbol", sort=True)}
    directions = {name: _stats(group) for name, group in trades.groupby("direction", sort=True)}

    yearly_rows = []
    for year, group in trades.groupby(trades["exit_time"].dt.year, sort=True):
        stats = _stats(group)
        yearly_rows.append({"year": year, "trades": stats["trades"], "net_profit": stats["net_profit"],
                            "PF": stats["profit_factor"], "winrate": stats["win_rate"],
                            "average_R": stats["average_R"], "max_DD": stats["max_drawdown"]})
    monthly_rows = []
    for month, group in trades.groupby(trades["exit_time"].dt.strftime("%Y-%m"), sort=True):
        rr = group["profit_R"].astype(float)
        dd = rr.cumsum() - rr.cumsum().cummax().clip(lower=0)
        monthly_rows.append({"month": month, "return_R": float(rr.sum()), "trades": len(group),
                             "drawdown": float(dd.min())})
    yearly = pd.DataFrame(yearly_rows)
    monthly = pd.DataFrame(monthly_rows)
    best_month = str(monthly.loc[monthly["return_R"].idxmax(), "month"])
    worst_month = str(monthly.loc[monthly["return_R"].idxmin(), "month"])

    output.mkdir(parents=True, exist_ok=True)
    yearly.to_csv(output / "yearly_report.csv", index=False, lineterminator="\n")
    monthly.to_csv(output / "monthly_returns.csv", index=False, lineterminator="\n")
    # The frozen trade log has no bar-by-bar path; blank values are intentional.
    pd.DataFrame({"trade_number": range(1, len(trades) + 1), "MAE": [pd.NA] * len(trades),
                  "MFE": [pd.NA] * len(trades)}).to_csv(output / "mae_mfe_analysis.csv", index=False,
                                                        lineterminator="\n")
    statistics = {"strategy": "T3_MTF_Trend_v1.0", "sample": {"start": str(trades.entry_time.min()),
                  "end": str(trades.exit_time.max())}, "frozen_metrics_reconciled": True,
                  "overall": overall, "R_distribution": distribution, "instruments": instruments,
                  "directions": directions, "best_month": best_month, "worst_month": worst_month,
                  "maximum_drawdown_duration_days": _maximum_drawdown_duration(trades)}
    (output / "statistics.json").write_text(json.dumps(statistics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _line_svg(output / "equity_curve.svg", trades)
    _histogram_svg(output / "r_distribution.svg", trades)

    top1 = distribution["top_1_share_of_positive_R"]
    # Pre-declared audit interpretation: visible cross-instrument/cross-year edge,
    # but only 109 trades, zero recorded costs, and no intratrade path.
    verdict = "NEEDS_RESEARCH"
    summary = f"""# T3 Baseline Audit

## Strategy
`T3_MTF_Trend_v1.0`; descriptive audit only. Strategy and parameters were not rerun or changed.

## Sample
{statistics['sample']['start']} through {statistics['sample']['end']}; {overall['trades']} closed trades. Calendar year 2025 and later is rejected.

## Overall results
Net profit {_fmt(overall['net_profit'])}; PF {_fmt(overall['profit_factor'])}; expectancy {_fmt(overall['expectancy'])}; average/median R {_fmt(overall['average_R'])}/{_fmt(overall['median_R'])}; win rate {_fmt(overall['win_rate'])}; max DD {_fmt(overall['max_drawdown'])}; losing/winning streak {overall['max_losing_streak']}/{overall['max_winning_streak']}; recovery factor {_fmt(overall['recovery_factor'])}.

## Instrument robustness
Si: {instruments.get('Si', {}).get('trades', 0)} trades, PF {_fmt(instruments.get('Si', {}).get('profit_factor'))}, expectancy {_fmt(instruments.get('Si', {}).get('expectancy'))}, average R {_fmt(instruments.get('Si', {}).get('average_R'))}, max DD {_fmt(instruments.get('Si', {}).get('max_drawdown'))}, win rate {_fmt(instruments.get('Si', {}).get('win_rate'))}.
CNY: {instruments.get('CNY', {}).get('trades', 0)} trades, PF {_fmt(instruments.get('CNY', {}).get('profit_factor'))}, expectancy {_fmt(instruments.get('CNY', {}).get('expectancy'))}, average R {_fmt(instruments.get('CNY', {}).get('average_R'))}, max DD {_fmt(instruments.get('CNY', {}).get('max_drawdown'))}, win rate {_fmt(instruments.get('CNY', {}).get('win_rate'))}.

## LONG/SHORT robustness
LONG: {directions.get('LONG', {}).get('trades', 0)} trades, PF {_fmt(directions.get('LONG', {}).get('profit_factor'))}, expectancy {_fmt(directions.get('LONG', {}).get('expectancy'))}, average R {_fmt(directions.get('LONG', {}).get('average_R'))}, win rate {_fmt(directions.get('LONG', {}).get('win_rate'))}.
SHORT: {directions.get('SHORT', {}).get('trades', 0)} trades, PF {_fmt(directions.get('SHORT', {}).get('profit_factor'))}, expectancy {_fmt(directions.get('SHORT', {}).get('expectancy'))}, average R {_fmt(directions.get('SHORT', {}).get('average_R'))}, win rate {_fmt(directions.get('SHORT', {}).get('win_rate'))}.

## Year robustness
Years present: {', '.join(map(str, yearly['year']))}. See `yearly_report.csv`. Best/worst month: {best_month}/{worst_month}; maximum drawdown duration: {statistics['maximum_drawdown_duration_days']} days.

## Profit concentration
Top-1 share of positive R: {_fmt(top1)}; top-3/top-5/top-10: {_fmt(distribution['top_3_share_of_positive_R'])}/{_fmt(distribution['top_5_share_of_positive_R'])}/{_fmt(distribution['top_10_share_of_positive_R'])}.

## Limitations
MAE/MFE unavailable from frozen baseline artifacts.
Intratrade OHLC path is required.
Frozen trades record zero transaction costs; execution robustness therefore remains unverified. This audit does not access source market data or TRUE OOS.

## Verdict
**{verdict}** — positive expectancy appears across both instruments and both years, but the modest sample, absent intratrade path, and zero recorded costs are material limitations.
"""
    (output / "summary.md").write_text(summary, encoding="utf-8")
    return statistics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=BASELINE_DIR)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    run_audit(args.source, args.output)


if __name__ == "__main__":
    main()
