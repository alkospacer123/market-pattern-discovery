#!/usr/bin/env python3
"""STS-EXP-001 research-only replay. No broker, LIVE token, or production IO.

Prerequisites extracted from historical TRL-R-038 and R039 archives:
--r038-engine code/trl_fixed_engine.py
--r039-sources .../sources/ containing research_extended.py and ohlcv/ N4
"""
import argparse
import hashlib
import json
import math
import sys
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd

ENGINE_SHA = "ce7468ee72568fbae01be5784e22cd4028833fc804fe0b561ee104d9064fb855"
SOURCES_SHA = "c048f96ff9a008ffda874189be12c4176e0fe305b0c410ae74734bfd3f4f657c"
BASE_PARITY = (773, 505.4766203967774)
TP_PARITY = (808, 499.2860389864027)

def checked_bytes(path, expected):
    content = Path(path).read_bytes()
    sha = hashlib.sha256(content).hexdigest()
    if sha != expected:
        raise ValueError(f"Frozen dependency mismatch: {path}: {sha}")
    return content

def stats_cash(rows):
    d = pd.DataFrame(rows)
    pnl = d.cash_pnl.to_numpy(float)
    wins = pnl[pnl > 0].sum()
    losses = -pnl[pnl < 0].sum()
    line = np.r_[0.0, np.cumsum(pnl)]
    by_month = pd.to_datetime(d.exit_dt).dt.strftime("%Y-%m")
    months = d.groupby(by_month).cash_pnl.sum()
    return dict(trades=len(d), net_rub=round(float(pnl.sum()), 2),
                pf_rub=round(float(wins/losses), 6) if losses else None,
                closed_dd_rub=round(float((np.maximum.accumulate(line)-line).max()), 2),
                positive_months=int((months > 0).sum()))

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--r038-engine", required=True, type=Path)
    p.add_argument("--r039-sources", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    engine_source = checked_bytes(a.r038_engine, ENGINE_SHA).decode("utf-8")
    checked_bytes(a.r039_sources/"research_extended.py", SOURCES_SHA)
    with tempfile.TemporaryDirectory(prefix="sts-exp-001-") as tmpdir:
        tmp = Path(tmpdir)
        (tmp/"sources").symlink_to(a.r039_sources.resolve(), target_is_directory=True)
        for original, replaced in [
            ("risk_budget_equity*.015", 'risk_budget_equity*float(finance.get("risk_per_trade",0.015))'),
            ("risk_budget_equity*.06", 'risk_budget_equity*float(finance.get("max_total_risk",0.06))')
        ]:
            if engine_source.count(original) != 1:
                raise ValueError("Frozen sizing line changed: "+original)
            engine_source = engine_source.replace(original, replaced)
        (tmp/"trl_fixed_engine_sts.py").write_text(engine_source, encoding="utf-8")
        sys.path.insert(0, str(tmp))
        from trl_fixed_engine_sts import base, prepare, engine, SYMS, GO_OLD, GO_MOEX
        base.SRC = tmp/"sources"/"ohlcv"
        data = {sym: base.load_one(sym) for sym in SYMS}
        arr = prepare("SHALLOW_PULLBACK", data)
        results = []
        for label, tp, protect, parity in [
            ("BASE", None, None, BASE_PARITY),
            ("TP6_PROTECT3", 6, 3, TP_PARITY)
        ]:
            frozen, _ = engine(arr, 1, tp=tp, protection=protect)
            total_r = sum(row["net_R"] for row in frozen)
            if len(frozen) != parity[0] or not math.isclose(total_r, parity[1], abs_tol=1e-8):
                raise RuntimeError(f"Shallow parity failed {label}: {len(frozen)} {total_r}")
            for go_label, go in [("GO_OCT2026", GO_OLD), ("GO_NOV2026", GO_MOEX)]:
                for risk in (0.005, 0.015):
                    trades, meta = engine(arr, 1, tp=tp, protection=protect,
                        finance=dict(bank=135000.0, go=go, no_compound=True,
                                     risk_per_trade=risk, max_total_risk=0.06))
                    results.append(dict(exit=label, go_proxy=go_label, risk_per_trade=risk,
                        blocked_go=meta.get("blocked_margin", 0),
                        unclosed_positions=meta["unclosed"], **stats_cash(trades)))
        report = dict(experiment="STS-EXP-001", research_only=True,
            engine_sha256=ENGINE_SHA, signal_sha256=SOURCES_SHA, bank_rub=135000,
            no_compounding=True,
            caveat="Static GO proxies; C1 not real FINAM costs, no MTM, not true OOS",
            rows=results)
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        for row in results:
            print(row)
        print("STS_EXP_001_PARITY_PASS", len(results), "scenarios")

if __name__ == "__main__":
    main()
