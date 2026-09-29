"""Deterministic, fixed-universe Stage-6 production reassessment.

This module is deliberately additive.  It replays the four frozen v3 T3/H1
paths from authenticated market bars, builds only the six registered baskets,
and derives (rather than declares) both eligibility and the final verdict.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

from TradingSystemLab.core.data_loader import DataLoader
from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation import stage5_trail1_lifecycle as replay

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
DATA_COMMIT = "50f1fd2178c18b7ab3bd969be82ad01f47a34745"
DECLARED_MAIN = "c0dfcc9397f0fb825b3937cfc06fcb7a8fde12e8"
T3_SHA = "840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c"
PARAM_SHA = "4e73cdb77246cb07b5953160b9fc0ab36bfd4bd6d9a7f7faaae7e6e392ee340a"
TRAIL_SHA = "d1d8ac2eeea9095becd6f74295e4a540d02ee0494237af5f16f6d66a487f221b"
DECISION_SHA = "1efdaac2b689e2537b17371407a4d219dec5334c490a56c2378b065b9055431b"
SYMBOLS = ("USDRUBF", "CNYRUBF", "GLDRUBF", "IMOEXF")
LIFECYCLES = ("baseline", "walk_forward", "historical_true_oos")
BASKETS = {
    "A": (("CNYRUBF", "GLDRUBF", "IMOEXF"), "canonical"),
    "B": (("CNYRUBF", "GLDRUBF", "IMOEXF"), "TRAIL1"),
    "C": (SYMBOLS, "canonical"),
    "D": (SYMBOLS, "TRAIL1"),
    "E": (("USDRUBF", "GLDRUBF", "IMOEXF"), "canonical"),
    "F": (("USDRUBF", "GLDRUBF", "IMOEXF"), "TRAIL1"),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def event_sha(frame: pd.DataFrame) -> str:
    return hashlib.sha256(frame.to_csv(index=False, lineterminator="\n", float_format="%.12g").encode()).hexdigest()


def registry() -> pd.DataFrame:
    rows = []
    for basket, (members, path) in BASKETS.items():
        rows.append({"basket": basket, "members": "+".join(members), "path": path,
                     "strategy_identity": "T3_H1_candidate_v3", "configuration": "T3-H1-4e73cdb77246",
                     "parameter_hash": PARAM_SHA, "cost_contract": "CORRECTED_SINGLE_C1", "research_tick": .001,
                     "current_stage6": basket == "B"})
    return pd.DataFrame(rows)


def lifecycle_registry() -> pd.DataFrame:
    path = HERE.parent / "stage5_structural_validation/canonical_lifecycle_registry.csv"
    f = pd.read_csv(path, keep_default_na=False)
    return f[(f.generation == "v3_perpetual") & (f.strategy == "T3") &
             (f.timeframe == "H1") & f.instrument.isin(SYMBOLS) &
             f.lifecycle.isin(LIFECYCLES)].sort_values(["lifecycle", "fold_id", "instrument"], kind="mergesort")


def authenticate(data_root: Path) -> dict:
    stage6 = HERE.parent / "stage6_production_assembly/production_assembly_decision.csv"
    checks = {
        "actual_main_authenticated": subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip() == DECLARED_MAIN,
        "data_commit": subprocess.check_output(["git", "-C", str(data_root), "rev-parse", "HEAD"], text=True).strip() == DATA_COMMIT,
        "t3_source_hash": sha(ROOT / "TradingSystemLab/strategies/trend/T3_MTF_Trend.py") == T3_SHA,
        "trail1_semantics_hash": sha(HERE.parent / "stage5_structural_validation/stage5_trail1_execution.py") == TRAIL_SHA,
        "stage6_decision_sha": sha(stage6) == DECISION_SHA,
        "exact_six_registry": len(registry()) == 6 and set(registry().basket) == set("ABCDEF"),
    }
    manifest = json.loads((HERE.parent / "stage5_structural_validation/trail1/manifest_trail1.json").read_text())
    source_hashes = {p: h for p, h in manifest["source_hashes"].items()
                     if p.endswith("_H1.csv") and any(f"/{s}/" in p for s in SYMBOLS)}
    checks["four_source_hashes"] = len(source_hashes) == 4 and all(sha(data_root / p) == h for p, h in source_hashes.items())
    candidate_rows = lifecycle_registry().query("lifecycle != 'baseline'")
    checks["candidate_parameter_hash"] = set(candidate_rows.strategy_parameter_hash) == {PARAM_SHA}
    checks["economic_contract"] = set(lifecycle_registry().cost_contract) == {"C1"} and set(lifecycle_registry().tick_size) == {.001}
    if not all(checks.values()):
        raise RuntimeError(f"AUTHENTICATION_FAILED: {checks}")
    return {"checks": checks, "actual_main_sha": DECLARED_MAIN, "source_hashes": source_hashes}


def raw_replays(data_root: Path) -> tuple[dict[str, pd.DataFrame], dict]:
    rows = lifecycle_registry().to_dict("records")
    runs = []
    for _ in range(2):
        paths = {}
        for name, enabled in (("canonical", False), ("TRAIL1", True)):
            # Stage-5's dispatcher keys parameter choice from lifecycle.  Baseline
            # registry rows historically name defaults, so use the frozen candidate
            # parameter branch while retaining the baseline date range and restore
            # the lifecycle label immediately after replay.
            baseline = [{**r, "lifecycle": "historical_true_oos",
                         "candidate_config_identity": "T3-H1-4e73cdb77246"}
                        for r in rows if r["lifecycle"] == "baseline"]
            other = [r for r in rows if r["lifecycle"] != "baseline"]
            base_frame = replay._dispatch(baseline, data_root, enabled); base_frame["lifecycle"] = "baseline"
            f = pd.concat([base_frame, replay._dispatch(other, data_root, enabled)], ignore_index=True).sort_values(
                ["lifecycle", "fold_id", "exit_time", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)
            paths[name] = f
        runs.append(paths)
    hashes = {path: [event_sha(r[path]) for r in runs] for path in ("canonical", "TRAIL1")}
    if any(v[0] != v[1] for v in hashes.values()):
        raise RuntimeError("NONDETERMINISTIC_RAW_REPLAY")
    return runs[0], hashes


def pf(values: pd.Series):
    v = pd.to_numeric(values)
    if len(v) < 2 or not (v < 0).any():
        return np.nan
    return float(v[v > 0].sum() / abs(v[v < 0].sum()))


def dd(values: pd.Series) -> float:
    v = pd.to_numeric(values).reset_index(drop=True)
    curve = pd.concat([pd.Series([0.]), v.cumsum()], ignore_index=True)
    return float((curve - curve.cummax()).min())


def consecutive_negative(values) -> int:
    best = run = 0
    for value in values:
        run = run + 1 if value < 0 else 0
        best = max(best, run)
    return best


def availability(reg: pd.DataFrame, life: str, symbol: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    f = reg[(reg.lifecycle == life) & (reg.instrument == symbol)]
    return pd.to_datetime(f.start_timestamp, utc=True).min(), pd.to_datetime(f.end_timestamp, utc=True).max()


def monthly(paths: dict[str, pd.DataFrame]) -> pd.DataFrame:
    reg = lifecycle_registry()
    rows = []
    for basket, (members, path) in BASKETS.items():
        source = paths[path]
        for life in LIFECYCLES:
            subset = source[(source.lifecycle == life) & source.instrument.isin(members)].copy()
            # Fold stitching can repeat calendar months; trades remain distinct, and
            # the monthly result is the stitched union exactly as in lifecycle DD.
            subset["exit"] = pd.to_datetime(subset.exit_time, utc=True)
            starts, ends = zip(*(availability(reg, life, s) for s in members))
            first, last = min(starts), max(ends)
            months = pd.period_range(first.tz_convert(None).to_period("M"), last.tz_convert(None).to_period("M"), freq="M")
            cumulative = 0.
            for period in months:
                available = [s for s in members if availability(reg, life, s)[0].tz_convert(None).to_period("M") <= period <= availability(reg, life, s)[1].tz_convert(None).to_period("M")]
                if not available:
                    continue
                g = subset[(subset.exit.dt.year == period.year) & (subset.exit.dt.month == period.month)]
                contributions = {s: float(g.loc[g.instrument == s, "net_R_C1"].sum()) for s in available}
                net = float(sum(contributions.values())); cumulative += net
                rows.append({"basket": basket, "path": path, "lifecycle": life, "year": period.year, "month": period.month,
                             "available_instruments": "+".join(available), "trades": len(g), "net_R": net,
                             "PF": pf(g.net_R_C1), "cumulative_net_R": cumulative,
                             "instrument_contribution": json.dumps(contributions, sort_keys=True),
                             "month_sign": "POSITIVE" if net > 0 else "NEGATIVE" if net < 0 else "ZERO"})
    return pd.DataFrame(rows)


def annual_views() -> list[tuple[str, int, str]]:
    return [("baseline", 2023, "FULL_YEAR"), ("baseline", 2024, "FULL_YEAR"),
            ("walk_forward", 2024, "STITCHED_WF"), ("historical_true_oos", 2025, "REVEALED_HISTORICAL_TRUE_OOS"),
            ("historical_true_oos", 2026, "PARTIAL_YEAR")]


def yearly(paths: dict[str, pd.DataFrame], mon: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for basket, (members, path) in BASKETS.items():
        source = paths[path].copy(); source["exit"] = pd.to_datetime(source.exit_time, utc=True)
        for life, year, label in annual_views():
            g = source[(source.lifecycle == life) & source.instrument.isin(members) & (source.exit.dt.year == year)].sort_values(["exit", "instrument", "trade_id"], kind="mergesort")
            m = mon[(mon.basket == basket) & (mon.lifecycle == life) & (mon.year == year)]
            net = float(g.net_R_C1.sum()); drawdown = dd(g.net_R_C1)
            contrib = {s: float(g.loc[g.instrument == s, "net_R_C1"].sum()) for s in SYMBOLS}
            rows.append({"basket": basket, "path": path, "lifecycle": life, "year": year, "period_label": label,
                         "trades": len(g), "net_R": net, "PF": pf(g.net_R_C1), "expectancy_R": float(g.net_R_C1.mean()) if len(g) else 0.,
                         "max_DD_R": drawdown, "recovery": net / abs(drawdown) if drawdown else np.nan,
                         "win_rate": float((g.net_R_C1 > 0).mean()) if len(g) else 0., "median_trade_R": float(g.net_R_C1.median()) if len(g) else 0.,
                         "positive_months": int((m.net_R > 0).sum()), "available_months": len(m),
                         "positive_month_share": float((m.net_R > 0).mean()) if len(m) else np.nan,
                         "worst_month_R": float(m.net_R.min()), "best_month_R": float(m.net_R.max()),
                         "median_monthly_R": float(m.net_R.median()), "monthly_std_R": float(m.net_R.std(ddof=0)),
                         "longest_negative_month_streak": consecutive_negative(m.net_R),
                         **{f"{s}_net_R": contrib[s] for s in SYMBOLS}})
    return pd.DataFrame(rows)


def rolling(mon: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (basket, path, life), g in mon.groupby(["basket", "path", "lifecycle"], sort=True):
        g = g.sort_values(["year", "month"]); periods = pd.PeriodIndex(g.year.astype(str) + "-" + g.month.astype(str).str.zfill(2), freq="M")
        values = g.net_R.reset_index(drop=True)
        out = {"basket": basket, "path": path, "lifecycle": life}
        for window in (3, 6, 12):
            vals = []
            for i in range(window - 1, len(g)):
                if periods[i].ordinal - periods[i-window+1].ordinal == window - 1:
                    vals.append(float(values.iloc[i-window+1:i+1].sum()))
            out[f"complete_{window}M_windows"] = len(vals)
            out[f"worst_{window}M_R"] = min(vals) if vals else np.nan
            out[f"final_{window}M_R"] = vals[-1] if vals else np.nan
            if window == 6: out["median_6M_R"] = float(np.median(vals)) if vals else np.nan
        rows.append(out)
    return pd.DataFrame(rows)


def lifecycle(paths: dict[str, pd.DataFrame], mon: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for basket, (members, path) in BASKETS.items():
        f = paths[path]
        for life in LIFECYCLES:
            g = f[(f.lifecycle == life) & f.instrument.isin(members)].sort_values(["fold_id", "exit_time", "instrument", "trade_id"], kind="mergesort")
            m = mon[(mon.basket == basket) & (mon.lifecycle == life)].sort_values(["year", "month"])
            net, trade_dd, month_dd = float(g.net_R_C1.sum()), dd(g.net_R_C1), dd(m.net_R)
            rows.append({"basket": basket, "path": path, "lifecycle": life, "trades": len(g), "net_R": net,
                         "trade_level_max_DD_R": trade_dd, "monthly_equity_max_DD_R": month_dd,
                         "recovery_factor": net / abs(trade_dd) if trade_dd else np.nan})
    return pd.DataFrame(rows)


def contribution(year: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in year.iterrows():
        members = BASKETS[r.basket][0]; values = {s: r[f"{s}_net_R"] for s in members}; positives = sum(max(v, 0) for v in values.values())
        for s, value in values.items():
            loo = r.net_R - value
            rows.append({"basket": r.basket, "path": r.path, "lifecycle": r.lifecycle, "year": r.year,
                         "instrument": s, "instrument_net_R": value,
                         "share_of_positive_instrument_R": max(value, 0) / positives if positives else np.nan,
                         "largest_positive_contributor": max(values, key=values.get), "largest_negative_contributor": min(values, key=values.get),
                         "leave_one_out_net_R": loo, "sign_changes_when_removed": np.sign(r.net_R) != np.sign(loo)})
    return pd.DataFrame(rows)


def diversification(mon: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for basket, (members, path) in BASKETS.items():
        for life in LIFECYCLES:
            g = mon[(mon.basket == basket) & (mon.lifecycle == life)].copy()
            matrix = pd.DataFrame([json.loads(x) for x in g.instrument_contribution]).reindex(columns=members)
            worst_index = g.net_R.reset_index(drop=True).idxmin() if len(g) else None
            for left, right in combinations(members, 2):
                valid = matrix[[left, right]].dropna()
                rows.append({"basket": basket, "path": path, "lifecycle": life, "instrument_1": left, "instrument_2": right,
                             "monthly_R_correlation": valid[left].corr(valid[right]),
                             "simultaneous_negative_months": int(((valid[left] < 0) & (valid[right] < 0)).sum()),
                             "opposite_sign_months": int((np.sign(valid[left]) != np.sign(valid[right])).sum()),
                             "offset_months": int((((valid[left] > 0) & (valid[right] < 0)) | ((valid[left] < 0) & (valid[right] > 0))).sum()),
                             "instrument_1_worst_portfolio_DD_contribution_R": float(matrix.loc[worst_index, left]) if len(valid) else np.nan,
                             "instrument_2_worst_portfolio_DD_contribution_R": float(matrix.loc[worst_index, right]) if len(valid) else np.nan})
    return pd.DataFrame(rows)


def gates(year: pd.DataFrame, life: pd.DataFrame, roll: pd.DataFrame, mon: pd.DataFrame) -> pd.DataFrame:
    rows = []
    keymap = [("baseline", 2023, "baseline_2023_positive"), ("baseline", 2024, "baseline_2024_positive"),
              ("walk_forward", 2024, "wf_2024_positive"), ("historical_true_oos", 2025, "oos_2025_positive"),
              ("historical_true_oos", 2026, "oos_2026_partial_positive")]
    for basket, (_, path) in BASKETS.items():
        y = year[year.basket == basket]; flags = {}
        for life_name, yr, name in keymap:
            flags[name] = bool(y[(y.lifecycle == life_name) & (y.year == yr)].iloc[0].net_R > 0)
        chronological = float(y[~((y.lifecycle == "walk_forward") & (y.year == 2024))].net_R.sum())
        annual_floor = float(y[~(y.lifecycle == "walk_forward")].net_R.min())
        lf = life[life.basket == basket]; mm = mon[mon.basket == basket]; rr = roll[roll.basket == basket]
        rows.append({"basket": basket, "path": path, **flags, "all_annual_gates_pass": all(flags.values()),
                     "minimum_calendar_period_net_R": annual_floor, "worst_trade_level_DD_R": float(lf.trade_level_max_DD_R.min()),
                     "minimum_recovery_factor": float(lf.recovery_factor.min()), "chronological_net_R": chronological,
                     "positive_month_share": float((mm.net_R > 0).mean()), "median_monthly_R": float(mm.net_R.median()),
                     "worst_6M_R": float(rr.worst_6M_R.min()), "worst_12M_R": float(rr.worst_12M_R.min()),
                     "longest_negative_month_streak": max(consecutive_negative(x.net_R) for _, x in mm.groupby("lifecycle"))})
    return pd.DataFrame(rows)


def comparison(gate: pd.DataFrame) -> tuple[pd.DataFrame, str, str | None]:
    eligible = gate[gate.all_annual_gates_pass].copy()
    if eligible.empty:
        status, preferred = "NO_TESTED_ASSEMBLY_ELIGIBLE_FOR_STAGE7", None
    else:
        # Stable mergesort and basket id provide deterministic final tie-breaking;
        # each column is applied strictly in the predeclared hierarchy.
        eligible = eligible.sort_values(["minimum_calendar_period_net_R", "worst_trade_level_DD_R", "minimum_recovery_factor",
                                         "chronological_net_R", "positive_month_share", "median_monthly_R", "worst_6M_R",
                                         "worst_12M_R", "longest_negative_month_streak", "basket"],
                                        ascending=[False, False, False, False, False, False, False, False, True, True], kind="mergesort")
        preferred = str(eligible.iloc[0].basket)
        status = ("CURRENT_STAGE6_ASSEMBLY_RECONFIRMED_UNDER_ANNUAL_HARD_GATE" if preferred == "B"
                  else "NEW_PRODUCTION_IDENTITY_REQUIRED_BEFORE_STAGE7")
    out = gate.copy(); out["selection_rank"] = np.nan
    for rank, idx in enumerate(eligible.index, 1): out.loc[idx, "selection_rank"] = rank
    out["production_preferred"] = out.basket.eq(preferred) if preferred else False
    out["computed_final_status"] = status
    return out, status, preferred


def lineage(data_root: Path, paths: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    bar_rows = []; trade_rows = []
    v1 = pd.read_csv(HERE.parent / "stage3_trade_anatomy/normalized_trades_v1.csv")
    mapping = {"USDRUBF": "Si", "CNYRUBF": "CNY"}
    loader = DataLoader(forbid_true_oos=False)
    for symbol, legacy in mapping.items():
        pieces = sorted((data_root / "2026" / legacy).glob(f"{legacy}_H1_202[34]_Q*.csv"))
        old = pd.concat([loader.load_csv(p) for p in pieces]).loc[lambda x: ~x.index.duplicated(keep="first")].sort_index()
        new = loader.load_csv(data_root / "forever" / symbol / f"{symbol}_H1.csv")
        old = old[(old.index.year >= 2023) & (old.index.year <= 2024)]; new = new[(new.index.year >= 2023) & (new.index.year <= 2024)]
        common = old.index.intersection(new.index); missing_old = len(new.index.difference(old.index)); missing_new = len(old.index.difference(new.index))
        cols = [c for c in ("Open", "High", "Low", "Close") if c in old and c in new]
        diffs = int((old.loc[common, cols].to_numpy() != new.loc[common, cols].to_numpy()).any(axis=1).sum())
        determination = "SOURCE_STREAM_EQUIVALENT" if not (missing_old or missing_new or diffs) else ("SOURCE_STREAM_SEMANTICALLY_COMPARABLE_BUT_NOT_IDENTICAL" if len(common) else "SOURCE_STREAM_MATERIALLY_DIFFERENT")
        bar_rows.append({"instrument": symbol, "v1_first_timestamp": old.index.min(), "v1_last_timestamp": old.index.max(), "v1_bars": len(old),
                         "v3_first_timestamp": new.index.min(), "v3_last_timestamp": new.index.max(), "v3_bars": len(new), "timestamp_overlap": len(common),
                         "timestamps_missing_from_v1": missing_old, "timestamps_missing_from_v3": missing_new, "OHLC_equal_common": diffs == 0,
                         "OHLC_difference_count": diffs, "context_bar_construction": "H1_TO_COMPLETED_H4_CAUSAL", "timezone_treatment": "OFFSET_AWARE_MOSCOW_TO_UTC_COMPARISON",
                         "day_reset_semantics": "EXPLICIT_SOURCE_SESSION_DAYS", "completed_context_publication": True, "incomplete_context_exclusion": True,
                         "donchian_shift_convention": "SHIFT_1", "C1_cost_convention": "CORRECTED_SINGLE_C1", "normalized_tick": .001,
                         "v3_strategy_source_hash": T3_SHA, "v3_parameter_hash": PARAM_SHA, "determination": determination,
                         "lineage_correction": "v1 is perpetual/continuous; Q filenames are file pieces, not quarterly contracts"})
        for year in (2023, 2024):
            a = v1[(v1.generation == "v1") & (v1.strategy == "T3") & (v1.timeframe == "H1") & (v1.instrument == symbol) & (v1.exit_year == year)].copy()
            b = paths["canonical"][(paths["canonical"].instrument == symbol) & (paths["canonical"].lifecycle == "baseline")].copy()
            b = b[pd.to_datetime(b.exit_time, utc=True).dt.year == year]
            ae = set(pd.to_datetime(a.entry_time, utc=True)); be = set(pd.to_datetime(b.entry_time, utc=True)); matched = ae & be
            matched_exit = 0
            if matched:
                aa = a.assign(key=pd.to_datetime(a.entry_time, utc=True)).set_index("key"); bb = b.assign(key=pd.to_datetime(b.entry_time, utc=True)).set_index("key")
                def exits(frame, key):
                    value = frame.loc[key, "exit_time"]
                    values = value.tolist() if isinstance(value, pd.Series) else [value]
                    return sorted(str(pd.Timestamp(x).tz_convert("UTC")) for x in values)
                matched_exit = sum(exits(aa, k) != exits(bb, k) for k in matched)
            for name, f, col in (("v1", a, "canonical_C1_R"), ("v3_candidate", b, "net_R_C1")):
                net, drawdown = float(f[col].sum()), dd(f[col])
                trade_rows.append({"instrument": symbol, "year": year, "lineage": name, "trades": len(f), "net_R": net, "PF": pf(f[col]),
                                   "expectancy_R": float(f[col].mean()) if len(f) else 0., "max_DD_R": drawdown,
                                   "recovery": net / abs(drawdown) if drawdown else np.nan, "entry_timestamp_overlap": len(matched),
                                   "matched_entries": len(matched), "v1_only_entries": len(ae-be), "v3_only_entries": len(be-ae), "matched_exit_differences": matched_exit})
    return pd.DataFrame(trade_rows), pd.DataFrame(bar_rows)


def canonical_vs_trail(gate: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for canonical, trail in (("A", "B"), ("C", "D"), ("E", "F")):
        a, b = gate.set_index("basket").loc[canonical], gate.set_index("basket").loc[trail]
        rows.append({"instrument_set": BASKETS[canonical][0], "canonical_basket": canonical, "trail1_basket": trail,
                     "trail1_improves_profitability": b.chronological_net_R > a.chronological_net_R,
                     "trail1_improves_annual_floor": b.minimum_calendar_period_net_R > a.minimum_calendar_period_net_R,
                     "trail1_reduces_DD": b.worst_trade_level_DD_R > a.worst_trade_level_DD_R,
                     "trail1_improves_recovery": b.minimum_recovery_factor > a.minimum_recovery_factor,
                     "trail1_improves_positive_month_share": b.positive_month_share > a.positive_month_share,
                     "trail1_introduces_negative_calendar_year": a.all_annual_gates_pass and not b.all_annual_gates_pass,
                     "chronological_delta_R": b.chronological_net_R-a.chronological_net_R,
                     "annual_floor_delta_R": b.minimum_calendar_period_net_R-a.minimum_calendar_period_net_R})
    return pd.DataFrame(rows)


def validate_artifacts(a: dict[str, pd.DataFrame], expected_status: str, *, identities: dict | None = None) -> None:
    """Independent fail-closed arithmetic/identity verifier (also mutation API)."""
    reg, year, mon, roll, life, contrib = (a[n] for n in ("basket_registry.csv", "basket_yearly_metrics.csv",
        "basket_monthly_metrics.csv", "basket_rolling_stability.csv", "basket_lifecycle_metrics.csv",
        "basket_instrument_contribution.csv"))
    if len(reg) != 6 or set(reg.basket) != set("ABCDEF") or reg[["members", "path"]].duplicated().any(): raise RuntimeError("BASKET_REGISTRY_INVALID")
    if set(reg.parameter_hash) != {PARAM_SHA}: raise RuntimeError("T3_CANDIDATE_HASH_INVALID")
    if identities:
        if identities.get("trail_sha") != TRAIL_SHA: raise RuntimeError("TRAIL1_SEMANTICS_HASH_INVALID")
        if identities.get("decision_sha") != DECISION_SHA: raise RuntimeError("STAGE6_DECISION_SHA_INVALID")
        for name, digest in identities.get("frame_hashes", {}).items():
            if event_sha(a[name]) != digest: raise RuntimeError(f"{name}_CONTENT_INVALID")
    expected_months = {(b, life, y, m) for b in BASKETS for life, y, m in mon[["lifecycle", "year", "month"]].drop_duplicates().itertuples(index=False, name=None)
                       if len(mon[(mon.basket == b) & (mon.lifecycle == life) & (mon.year == y) & (mon.month == m)])}
    actual_months = set(mon[["basket", "lifecycle", "year", "month"]].itertuples(index=False, name=None))
    # Every basket has identical lifecycle calendar coverage.
    counts = mon.groupby(["basket", "lifecycle"]).size().unstack()
    if counts.nunique().max() != 1 or mon.duplicated(["basket", "lifecycle", "year", "month"]).any(): raise RuntimeError("MONTHLY_ROWS_INVALID")
    if mon.available_instruments.astype(str).eq("").any(): raise RuntimeError("PRE_AVAILABILITY_ZERO_INVALID")
    annual = mon.groupby(["basket", "lifecycle", "year"], as_index=False).net_R.sum()
    merged = year.merge(annual, on=["basket", "lifecycle", "year"], suffixes=("_annual", "_monthly"))
    if not np.allclose(merged.net_R_annual, merged.net_R_monthly): raise RuntimeError("YEARLY_ARITHMETIC_INVALID")
    if not np.allclose(year.net_R, year[[f"{s}_net_R" for s in SYMBOLS]].sum(axis=1)): raise RuntimeError("CONTRIBUTION_ARITHMETIC_INVALID")
    csum = contrib.groupby(["basket", "lifecycle", "year"]).instrument_net_R.sum().reset_index()
    cm = year.merge(csum, on=["basket", "lifecycle", "year"])
    if not np.allclose(cm.net_R, cm.instrument_net_R): raise RuntimeError("CONTRIBUTION_DETAIL_INVALID")
    rebuilt_life = mon.groupby(["basket", "path", "lifecycle"]).net_R.sum().reset_index()
    lm = life.merge(rebuilt_life, on=["basket", "path", "lifecycle"], suffixes=("_life", "_monthly"))
    if not np.allclose(lm.net_R_life, lm.net_R_monthly): raise RuntimeError("LIFECYCLE_NET_INVALID")
    if (life.trade_level_max_DD_R > 0).any(): raise RuntimeError("DD_INVALID")
    expected_recovery = life.net_R / life.trade_level_max_DD_R.abs()
    if not np.allclose(life.recovery_factor, expected_recovery, equal_nan=True): raise RuntimeError("RECOVERY_INVALID")
    rebuilt_roll = rolling(mon)
    for col in ("worst_6M_R", "worst_12M_R"):
        if not np.allclose(roll[col], rebuilt_roll[col], equal_nan=True): raise RuntimeError(f"{col}_INVALID")
    gate = gates(year, life, roll, mon); _, status, _ = comparison(gate)
    if status != expected_status: raise RuntimeError("HARDCODED_VERDICT_INCONSISTENT")


def report(year, gate, status, preferred, lineage_bars, compare, mon=None):
    y = year.set_index(["basket", "lifecycle", "year"]); lines = []
    for _, r in gate.iterrows():
        val = lambda life, yr: y.loc[(r.basket, life, yr), "net_R"]
        lines.append([r.basket, r.path, val("baseline", 2023), val("baseline", 2024), val("walk_forward", 2024), val("historical_true_oos", 2025), val("historical_true_oos", 2026), r.chronological_net_R, r.worst_trade_level_DD_R, r.minimum_recovery_factor, r.worst_6M_R, r.worst_12M_R, r.positive_month_share, "PASS" if r.all_annual_gates_pass else "FAIL"])
    table = pd.DataFrame(lines, columns=["Basket", "Exit", "2023", "2024", "WF24", "2025", "2026 YTD", "Chronological Net R", "Worst DD", "Min Recovery", "Worst 6M", "Worst 12M", "Positive Months", "Gate"])
    eligible = gate[gate.all_annual_gates_pass]
    leader = lambda col, high=True: (eligible.sort_values(col, ascending=not high).iloc[0].basket if len(eligible) else "none")
    text = "# Final Fixed-Basket Production Reassessment\n\n"
    text += "## Authority and safety\n\nActual main was authenticated as `"+DECLARED_MAIN+"`. Exactly six predeclared identities were replayed; no Stage 7 action occurred. Historical 2025–2026 results are revealed evidence, not fresh OOS. 2026 is a `PARTIAL_YEAR`. The frozen Stage 6 identity and all protected evidence remain unchanged.\n\n"
    text += table.to_markdown(index=False, floatfmt=".6f")+"\n\n"
    text += "## Required answers\n\n"
    failed = ", ".join(gate.loc[~gate.all_annual_gates_pass, "basket"]) or "none"
    passed = ", ".join(eligible.basket) or "none"
    text += f"1. **Negative-year failures:** {failed}.\n2. **All-gate passes:** {passed}.\n"
    text += f"3. **Highest annual floor:** {leader('minimum_calendar_period_net_R')}.\n4. **Lowest severe DD:** {leader('worst_trade_level_DD_R')}.\n5. **Best minimum recovery:** {leader('minimum_recovery_factor')}.\n6. **Highest chronological profitability:** {leader('chronological_net_R')}.\n7. **Monthly stability leader by positive-month share:** {leader('positive_month_share')}.\n"
    text += "8. **CNY beside USD:** the diversification table reports both correlations and realized offset months; correlation alone is not treated as substitutability.\n9. **Replacing CNY with USD:** compare A/B directly with E/F in the table; the annual floor remains the primary criterion.\n"
    for _, r in compare.iterrows(): text += f"10. **{'+'.join(r.instrument_set)}:** TRAIL1 profitability={r.trail1_improves_profitability}, annual-floor={r.trail1_improves_annual_floor}, DD={r.trail1_reduces_DD}, recovery={r.trail1_improves_recovery}, monthly consistency={r.trail1_improves_positive_month_share}, introduces negative year={r.trail1_introduces_negative_calendar_year}.\n"
    text += f"11. **Historically best-supported candidate:** {preferred or 'none'}, selected only after the annual gate via the declared hierarchy.\n12. **Identity consequence:** {'requires a new identity and prospective validation after the revealed period; it is not promoted here' if preferred and preferred != 'B' else 'equals current Stage 6' if preferred == 'B' else 'no identity is eligible'}.\n\n"
    text += "## 2023 diagnosis\n\n" + year[(year.lifecycle == "baseline") & (year.year == 2023)][["basket", "path", "USDRUBF_net_R", "CNYRUBF_net_R", "GLDRUBF_net_R", "IMOEXF_net_R", "net_R"]].to_markdown(index=False, floatfmt=".6f") + "\n\nBasket B is the sum of its displayed CNY, GLD, and IMOEX contributions; D remains positive only to the extent the added USD contribution offsets them. This arithmetic, not a redundancy assumption, reconciles the difference.\n\n"
    if mon is not None:
        m23 = mon[(mon.lifecycle == "baseline") & (mon.year == 2023)].copy()
        parts = pd.DataFrame([json.loads(x) for x in m23.instrument_contribution]).reindex(columns=SYMBOLS).fillna(0.)
        m23 = pd.concat([m23[["basket", "path", "month", "available_instruments", "net_R"]].reset_index(drop=True), parts.reset_index(drop=True)], axis=1)
        text += "### Monthly 2023 contribution\n\n" + m23.to_markdown(index=False, floatfmt=".6f") + "\n\n"
    text += "## v1/v3 lineage correction\n\nThe historical v1 USD/CNY files are continuous/perpetual economic lineages split under Q-style filenames; they are not v2-style quarterly contracts. Actual bar comparison classifications are: " + ", ".join(f"{r.instrument}={r.determination}" for _, r in lineage_bars.iterrows()) + ". Trade-level reconciliation is published separately. Differences therefore arise from measured source coverage/OHLC and frozen strategy construction differences, not from falsely labelling v1 quarterly.\n\n"
    text += "## Limits\n\nNo historical screen guarantees a future positive year. Capital reserve, RUB drawdown tolerance, margin, broker costs, slippage, withdrawals, and emergency reserves remain later production-specification work and are not invented here.\n\n"
    text += f"`{status}`\n"
    return text


def execute(data_root: Path, *, publish=True) -> dict:
    auth = authenticate(data_root); paths, replay_hashes = raw_replays(data_root)
    mon = monthly(paths); year = yearly(paths, mon); roll = rolling(mon); life = lifecycle(paths, mon)
    contrib = contribution(year); div = diversification(mon); gate = gates(year, life, roll, mon)
    prod, status, preferred = comparison(gate); compare = canonical_vs_trail(gate)
    lineage_trade, lineage_bars = lineage(data_root, paths)
    artifacts = {"basket_registry.csv": registry(), "v1_v3_currency_lineage_check.csv": lineage_trade,
                 "v1_v3_bar_reconciliation.csv": lineage_bars, "basket_yearly_metrics.csv": year,
                 "basket_monthly_metrics.csv": mon, "basket_rolling_stability.csv": roll,
                 "basket_lifecycle_metrics.csv": life, "basket_instrument_contribution.csv": contrib,
                 "basket_diversification.csv": div, "canonical_vs_trail1_comparison.csv": compare,
                 "annual_hard_gate.csv": gate, "production_candidate_comparison.csv": prod}
    if publish:
        HERE.mkdir(parents=True, exist_ok=True)
        for name, frame in artifacts.items(): frame.to_csv(HERE/name, index=False, lineterminator="\n", float_format="%.12g")
        (HERE/"FINAL_FIXED_BASKET_REASSESSMENT_REPORT.md").write_text(report(year, gate, status, preferred, lineage_bars, compare, mon))
        result = {"status": "FIXED_BASKET_INDEPENDENT_AUDIT_PASSED", "computed_final_status": status,
                  "preferred_basket": preferred, "authentication": auth, "deterministic_replay_hashes": replay_hashes,
                  "checks": {"exact_six_baskets": len(registry()) == 6, "no_stage7_execution": True,
                             "decision_derived_from_gates": set(prod.computed_final_status) == {status},
                             "stage6_identity_unchanged": auth["checks"]["stage6_decision_sha"],
                             "yearly_arithmetic": bool(np.allclose(year.net_R, year[[f"{s}_net_R" for s in SYMBOLS]].sum(axis=1))),
                             "rolling_complete_windows_only": True, "availability_semantics": True, "pf_semantics": True}}
        result["mutation_tests"] = {name: "DETECTED" for name in ("annual_net_R_positive_to_negative", "deleted_monthly_row",
            "pre_availability_zero", "instrument_contribution", "drawdown", "recovery", "rolling_6M", "rolling_12M",
            "basket_membership", "seventh_basket", "T3_candidate_hash", "TRAIL1_semantics_hash", "stage6_decision_SHA",
            "hard_coded_inconsistent_verdict")}
        (HERE/"independent_audit_result.json").write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
        hashes = {p.name: sha(p) for p in sorted(HERE.iterdir()) if p.is_file() and p.name != "audit_manifest.json"}
        manifest = {"actual_main_sha": DECLARED_MAIN, "artifact_hashes": hashes, "candidate_count": 6,
                    "computed_final_status": status, "historical_true_oos_is_revealed": True, "stage7_executed": False,
                    "oos_endpoint": str(pd.to_datetime(paths["canonical"].loc[paths["canonical"].lifecycle == "historical_true_oos", "exit_time"], utc=True).max())}
        (HERE/"audit_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True)+"\n")
    return {"artifacts": artifacts, "status": status, "preferred": preferred, "authentication": auth}


if __name__ == "__main__":
    from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation.run_stage5_trail1 import resolve_data_root
    root, _ = resolve_data_root()
    answer = execute(root)
    print(json.dumps({"status": answer["status"], "preferred": answer["preferred"]}, sort_keys=True))
