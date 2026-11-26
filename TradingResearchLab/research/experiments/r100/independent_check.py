#!/usr/bin/env python3
"""Independent vectorized R099 ledger and HAC witness; no trading decisions."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

EXPECTED_M5 = "3758ed99e4ec0c712af09575ddc74f0437f2fcddda05df2c5d27268296037786"
FIRST = [f"10:{m:02d}" for m in range(0, 30, 5)]
LAST = [f"18:{m:02d}" for m in range(20, 50, 5)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--m5", type=Path, required=True)
    ap.add_argument("--canonical-dir", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    digest = hashlib.sha256(args.m5.read_bytes()).hexdigest()
    if digest != EXPECTED_M5:
        raise RuntimeError("SOURCE_DRIFT")
    raw = pd.read_csv(args.m5, sep=";", parse_dates=["Datetime"])
    raw["date"] = raw.Datetime.dt.strftime("%Y-%m-%d")
    raw["time"] = raw.Datetime.dt.strftime("%H:%M")
    close = raw.pivot(index="date", columns="time", values="Close").sort_index()
    open_ = raw.pivot(index="date", columns="time", values="Open").sort_index()
    high = raw.pivot(index="date", columns="time", values="High").sort_index()
    low = raw.pivot(index="date", columns="time", values="Low").sort_index()
    volume = raw.pivot(index="date", columns="time", values="Volume").sort_index()

    previous_close = close["18:45"].shift(1)
    weekday = pd.to_datetime(close.index).dayofweek < 5
    has_main = close.loc[:, "10:00":"18:45"].notna().any(axis=1).to_numpy()
    complete = close[FIRST + LAST].notna().all(axis=1) & previous_close.notna()
    required_valid = pd.Series(True, index=close.index)
    for t in FIRST + LAST:
        required_valid &= (close[t] > 0) & (open_[t] > 0) & (high[t] > 0) & (low[t] > 0) & (volume[t] > 0)
        required_valid &= (high[t] >= pd.concat([open_[t], close[t], low[t]], axis=1).max(axis=1))
        required_valid &= (low[t] <= pd.concat([open_[t], close[t], high[t]], axis=1).min(axis=1))
    # Previous 18:45 validity is checked explicitly through its source row.
    previous_rows = raw[raw.time == "18:45"].set_index("date")
    prev_date = pd.Series(close.index, index=close.index).shift(1)
    prev_ok = []
    for d in prev_date:
        if d is None or pd.isna(d) or d not in previous_rows.index:
            prev_ok.append(False)
        else:
            r = previous_rows.loc[d]
            prev_ok.append(bool(min(r.Open, r.High, r.Low, r.Close, r.Volume) > 0 and r.High >= max(r.Open, r.Close, r.Low) and r.Low <= min(r.Open, r.Close, r.High)))
    prev_ok = pd.Series(prev_ok, index=close.index)
    eligible = close.index[weekday & has_main & complete & required_valid & prev_ok]

    p0 = previous_close.loc[eligible].to_numpy(float)
    p1 = close.loc[eligible, "10:25"].to_numpy(float)
    e = open_.loc[eligible, "18:20"].to_numpy(float)
    x = close.loc[eligible, "18:45"].to_numpy(float)
    direction = np.sign(p1 - p0).astype(int)
    nonzero = direction != 0
    dates = eligible.to_numpy()[nonzero]
    d = direction[nonzero]
    gross = d * (x[nonzero] - e[nonzero]) * 1000.0
    net = {c: gross - 20.0 * c for c in (1, 2, 4)}

    canonical = pd.read_csv(args.canonical_dir / "daily_ledger.csv")
    canonical = canonical.sort_values("date").reset_index(drop=True)
    compare = pd.DataFrame({
        "date": dates, "p0": p0[nonzero], "p1": p1[nonzero],
        "entry_open": e[nonzero], "exit_close": x[nonzero],
        "direction": d, "gross_rub": gross,
        "net_rub_c1": net[1], "net_rub_c2": net[2], "net_rub_c4": net[4],
    }).sort_values("date").reset_index(drop=True)
    columns = list(compare.columns)
    if list(canonical.date) != list(compare.date):
        raise RuntimeError("INDEPENDENT_LEDGER_DATE_MISMATCH")
    numeric_diffs = {}
    for col in columns[1:]:
        numeric_diffs[col] = float(np.max(np.abs(canonical[col].to_numpy(float) - compare[col].to_numpy(float))))
    if any(v > 1e-7 for v in numeric_diffs.values()):
        raise RuntimeError(f"INDEPENDENT_LEDGER_VALUE_MISMATCH {numeric_diffs}")

    rf = np.log(p1 / p0)
    rl = np.log(x / e)
    fit = sm.OLS(rl, sm.add_constant(rf)).fit(cov_type="HAC", cov_kwds={"maxlags": 5, "use_correction": True}, use_t=False)
    expected = json.loads((args.canonical_dir / "statistical_tests.json").read_text(encoding="utf-8"))
    regression = expected["regression"]
    regression_diff = {
        "alpha": abs(float(fit.params[0]) - regression["alpha"]),
        "beta": abs(float(fit.params[1]) - regression["beta"]),
        "beta_se": abs(float(fit.bse[1]) - regression["beta_se"]),
        "beta_p": abs(float(fit.pvalues[1]) - regression["beta_p_two_sided"]),
    }
    if regression_diff["beta"] > 1e-12 or regression_diff["beta_se"] > 1e-12 or regression_diff["beta_p"] > 1e-12:
        raise RuntimeError(f"INDEPENDENT_HAC_MISMATCH {regression_diff}")

    result = {
        "status": "PASS",
        "method": "Independent vectorized pivot/shift extraction plus statsmodels OLS HAC; no import or execution of run_r099.py",
        "m5_sha256": digest,
        "eligible_days": len(eligible),
        "trades": len(compare),
        "ledger_columns_compared": columns,
        "max_absolute_differences": numeric_diffs,
        "statsmodels_version": sm.__version__,
        "independent_hac": {
            "alpha": float(fit.params[0]), "beta": float(fit.params[1]),
            "beta_se": float(fit.bse[1]), "beta_p_two_sided": float(fit.pvalues[1]),
        },
        "absolute_differences_vs_canonical": regression_diff,
        "net_rub": {f"C{c}": float(net[c].sum()) for c in (1, 2, 4)},
        "decision_crosscheck": expected["decision"],
        "scope": "Independent calculation witness, not TRUE OOS or a profitability claim",
    }
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "eligible": len(eligible), "trades": len(compare), "net_c2": result["net_rub"]["C2"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
