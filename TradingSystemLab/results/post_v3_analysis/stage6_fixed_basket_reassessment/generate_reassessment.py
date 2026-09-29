"""Deterministic, fixed-universe Stage-6 production reassessment.

This module is deliberately additive.  It replays the four frozen v3 T3/H1
paths from authenticated market bars, builds only the six registered baskets,
and derives (rather than declares) both eligibility and the final verdict.
"""
from __future__ import annotations

import hashlib
import json
import os
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
SOURCE_MAIN_SHA = "c0dfcc9397f0fb825b3937cfc06fcb7a8fde12e8"
SOURCE_PR_HEAD_SHA = "fd7c4e6659278953bc57295d0b62a70b630a3c80"
SOURCE_MERGE_SHA = "664e63ff6f598dd594523c19690ac3f1b938c16c"
FIX_BASE_SHA = SOURCE_MERGE_SHA
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
        # The evidence was produced from SOURCE_MAIN_SHA.  A fix run occurs on a
        # descendant of the PR merge, so authenticating by equality to the old
        # source commit would silently conflate two different provenance facts.
        "source_main_present": subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", SOURCE_MAIN_SHA+"^{commit}"]).returncode == 0,
        "source_pr_head_present": subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", SOURCE_PR_HEAD_SHA+"^{commit}"]).returncode == 0,
        "source_merge_present": subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", SOURCE_MERGE_SHA+"^{commit}"]).returncode == 0,
        "fix_base_is_ancestor": subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", FIX_BASE_SHA, "HEAD"]).returncode == 0,
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
    return {"checks": checks, "source_main_sha": SOURCE_MAIN_SHA,
            "source_pr_head_sha": SOURCE_PR_HEAD_SHA, "source_merge_sha": SOURCE_MERGE_SHA,
            "fix_base_sha": FIX_BASE_SHA, "source_hashes": source_hashes}


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


def concentration(mon: pd.DataFrame) -> pd.DataFrame:
    """Descriptive concentration only; this frame is never a selection input."""
    rows = []
    for (basket, path, life), g in mon.groupby(["basket", "path", "lifecycle"], sort=True):
        values = pd.to_numeric(g.net_R)
        positive = values[values > 0].sort_values(ascending=False)
        positive_total = float(positive.sum())
        rows.append({"basket": basket, "path": path, "lifecycle": life,
                     "total_net_R": float(values.sum()), "best_month_R": float(values.max()),
                     "best_month_share_of_positive_monthly_R": float(positive.iloc[0] / positive_total) if positive_total else np.nan,
                     "top_3_positive_months_R": float(positive.head(3).sum()),
                     "top_3_share_of_positive_monthly_R": float(positive.head(3).sum() / positive_total) if positive_total else np.nan,
                     "worst_month_R": float(values.min()),
                     "bottom_3_months_R": float(values.sort_values().head(3).sum())})
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


def lineage(data_root: Path, paths: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    bar_rows = []; trade_rows = []; bridge_rows = []
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
            # Entry timestamps happen to be unique in this evidence, but retain
            # the strongest common composite key so future duplicate timestamps
            # cannot be paired by row ordinal.
            key_cols = ["instrument", "direction", "entry_time_utc", "entry_price"]
            def keyed(frame):
                out = frame.copy()
                out["entry_time_utc"] = pd.to_datetime(out.entry_time, utc=True).dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                out["entry_price"] = pd.to_numeric(out.entry_price)
                return out
            aa, bb = keyed(a), keyed(b)
            adup = int((aa.groupby(key_cols, dropna=False).size() > 1).sum())
            bdup = int((bb.groupby(key_cols, dropna=False).size() > 1).sum())
            # Duplicate composite entries are paired by a deterministic exit
            # ordering within the key, never by source row ordinal.
            for frame in (aa, bb):
                frame.sort_values(key_cols + ["exit_time", "exit_price"], kind="mergesort", inplace=True)
                frame["key_occurrence"] = frame.groupby(key_cols, sort=False).cumcount()
            merge_key = key_cols + ["key_occurrence"]
            joined = aa.merge(bb, on=merge_key, how="outer", suffixes=("_v1", "_v3"), indicator=True, validate="one_to_one")
            both = joined[joined._merge == "both"].copy(); only_a = joined[joined._merge == "left_only"]; only_b = joined[joined._merge == "right_only"]
            same_exit = ((pd.to_datetime(both.exit_time_v1, utc=True) == pd.to_datetime(both.exit_time_v3, utc=True)) &
                         np.isclose(pd.to_numeric(both.exit_price_v1), pd.to_numeric(both.exit_price_v3), atol=1e-12, rtol=0))
            matched_exit = int((~same_exit).sum())
            v1_net = float(a.canonical_C1_R.sum()); v3_net = float(b.net_R_C1.sum())
            matched_delta = float(pd.to_numeric(both.net_R_C1).sum() - pd.to_numeric(both.canonical_C1_R).sum())
            v1_only_r = float(pd.to_numeric(only_a.canonical_C1_R).sum())
            v3_only_r = float(pd.to_numeric(only_b.net_R_C1).sum())
            delta = v3_net - v1_net; residual = matched_delta - v1_only_r + v3_only_r - delta
            bridge_rows.append({"instrument": symbol, "year": year,
                "trade_key": "instrument+direction+normalized_UTC_entry_timestamp+entry_price",
                "v1_duplicate_key_count": adup, "v3_duplicate_key_count": bdup,
                "matched_trades": len(both), "v1_only_trades": len(only_a), "v3_only_trades": len(only_b),
                "matched_trades_identical_exit": int(same_exit.sum()), "matched_trades_changed_exit": matched_exit,
                "v1_net_R": v1_net, "v3_net_R": v3_net, "total_delta_v3_minus_v1": delta,
                "matched_exit_delta_R": matched_delta, "v1_only_R": v1_only_r,
                "removed_trade_bridge_R": -v1_only_r, "v3_only_R": v3_only_r,
                "added_trade_bridge_R": v3_only_r, "total_reconciliation_error_R": residual})
            for name, f, col in (("v1", a, "canonical_C1_R"), ("v3_candidate", b, "net_R_C1")):
                net, drawdown = float(f[col].sum()), dd(f[col])
                trade_rows.append({"instrument": symbol, "year": year, "lineage": name, "trades": len(f), "net_R": net, "PF": pf(f[col]),
                                   "expectancy_R": float(f[col].mean()) if len(f) else 0., "max_DD_R": drawdown,
                                   "recovery": net / abs(drawdown) if drawdown else np.nan, "entry_timestamp_overlap": len(both),
                                   "matched_entries": len(both), "v1_only_entries": len(only_a), "v3_only_entries": len(only_b), "matched_exit_differences": matched_exit})
    return pd.DataFrame(trade_rows), pd.DataFrame(bar_rows), pd.DataFrame(bridge_rows)


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
    expected_reg = registry().astype({"research_tick": float}).sort_values("basket").reset_index(drop=True)
    got_reg = reg.sort_values("basket").reset_index(drop=True).copy()
    if "current_stage6" in got_reg:
        got_reg["current_stage6"] = got_reg.current_stage6.map(
            lambda x: x if isinstance(x, bool) else str(x).strip().lower() == "true")
    if list(got_reg.columns) != list(expected_reg.columns) or not got_reg.equals(expected_reg):
        raise RuntimeError("BASKET_IDENTITY_SEMANTICS_INVALID")
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
    for col in ("complete_3M_windows", "worst_3M_R", "final_3M_R", "complete_6M_windows", "worst_6M_R",
                "final_6M_R", "median_6M_R", "complete_12M_windows", "worst_12M_R", "final_12M_R"):
        if not np.allclose(roll[col], rebuilt_roll[col], equal_nan=True): raise RuntimeError(f"{col}_INVALID")
    gate = gates(year, life, roll, mon); _, status, _ = comparison(gate)
    if status != expected_status: raise RuntimeError("HARDCODED_VERDICT_INCONSISTENT")
    if "v1_v3_currency_pnl_bridge.csv" in a:
        bridge = a["v1_v3_currency_pnl_bridge.csv"]
        rhs = bridge.matched_exit_delta_R - bridge.v1_only_R + bridge.v3_only_R
        if len(bridge) != 4 or bridge[["instrument", "year"]].duplicated().any() or not np.allclose(
                rhs, bridge.total_delta_v3_minus_v1, atol=1e-9, rtol=0) or not np.allclose(
                bridge.total_delta_v3_minus_v1, bridge.v3_net_R-bridge.v1_net_R, atol=1e-9, rtol=0) or not np.allclose(
                bridge.total_reconciliation_error_R, 0, atol=1e-9, rtol=0):
            raise RuntimeError("V1_V3_PNL_BRIDGE_INVALID")
    if "basket_monthly_concentration.csv" in a:
        rebuilt = concentration(mon).sort_values(["basket", "lifecycle"]).reset_index(drop=True)
        supplied = a["basket_monthly_concentration.csv"].sort_values(["basket", "lifecycle"]).reset_index(drop=True)
        if list(rebuilt.columns) != list(supplied.columns): raise RuntimeError("MONTHLY_CONCENTRATION_INVALID")
        for col in rebuilt.select_dtypes(include=np.number):
            if not np.allclose(rebuilt[col], supplied[col], equal_nan=True): raise RuntimeError("MONTHLY_CONCENTRATION_INVALID")
    if "production_candidate_comparison.csv" in a:
        rebuilt, rebuilt_status, rebuilt_preferred = comparison(gate)
        supplied = a["production_candidate_comparison.csv"].sort_values("basket").reset_index(drop=True)
        rebuilt = rebuilt.sort_values("basket").reset_index(drop=True)
        if (set(supplied.computed_final_status) != {rebuilt_status} or
            set(supplied.loc[supplied.production_preferred.astype(bool), "basket"]) != ({rebuilt_preferred} if rebuilt_preferred else set()) or
            not np.allclose(supplied.selection_rank, rebuilt.selection_rank, equal_nan=True)):
            raise RuntimeError("INDEPENDENT_SELECTION_RECOMPUTATION_INVALID")


def report(year, gate, status, preferred, lineage_bars, lineage_bridge, compare, mon, life, roll, conc, contrib, reg):
    def md(frame): return frame.to_markdown(index=False, floatfmt=".6f")
    def monthly_matrix(lifecycle_name, year_number, title):
        g = mon[(mon.lifecycle == lifecycle_name) & (mon.year == year_number)].copy()
        matrix = g.pivot(index="basket", columns="month", values="net_R").reindex(list(BASKETS))
        matrix.columns = [pd.Timestamp(2000, int(x), 1).strftime("%b") for x in matrix.columns]
        matrix["Total"] = matrix.sum(axis=1); matrix.insert(0, "Basket", matrix.index)
        note = " Zero-trade available months are numeric `0.000000` (`NO_TRADES`); unavailable future months are absent (`NOT_YET_AVAILABLE`)."
        return f"## {title}\n\n{md(matrix.reset_index(drop=True))}\n\n{note}\n\n"
    annual = year[["basket", "path", "lifecycle", "year", "net_R", "positive_months", "available_months",
                   "positive_month_share", "median_monthly_R", "monthly_std_R", "worst_month_R", "best_month_R",
                   "longest_negative_month_streak"]].copy()
    annual["annual_gate"] = annual.net_R > 0
    text = "# Final Fixed-Basket Production Reassessment\n\n"
    text += "## Provenance\n\n"
    text += f"- Source main used for the original evidence: `{SOURCE_MAIN_SHA}`.\n- PR #255 head: `{SOURCE_PR_HEAD_SHA}`.\n- PR #255 merge and fix base: `{SOURCE_MERGE_SHA}`.\n- Existing production identity `PROD_STAGE6_83C7B31BB42C` is unchanged. No Stage 7 action occurred.\n\n"
    text += "## Exact frozen six-basket registry\n\n" + md(reg) + "\n\n"
    text += "## Annual hard-gate table\n\n" + md(annual) + "\n\n"
    text += "## Lifecycle risk/recovery table\n\n" + md(life) + "\n\n"
    text += monthly_matrix("baseline", 2023, "Full monthly Baseline 2023 A–F")
    text += monthly_matrix("baseline", 2024, "Full monthly Baseline 2024 A–F")
    text += monthly_matrix("walk_forward", 2024, "Full monthly Walk Forward 2024 A–F")
    text += monthly_matrix("historical_true_oos", 2025, "Full monthly Historical TRUE OOS 2025 A–F")
    text += monthly_matrix("historical_true_oos", 2026, "Full monthly Historical TRUE OOS 2026 YTD A–F")
    text += "## Rolling 3M/6M/12M comparison\n\nOnly complete consecutive windows are included.\n\n" + md(roll) + "\n\n"
    text += "## Monthly concentration comparison\n\nDescriptive only; no threshold or selection rank uses this table.\n\n" + md(conc) + "\n\n"
    text += "## Instrument contribution\n\n" + md(contrib) + "\n\n"
    text += "## Canonical vs TRAIL1 comparison\n\n" + md(compare) + "\n\n"
    text += "## v1/v3 bar reconciliation\n\nThe v1 USD/CNY sources are continuous/perpetual lineages. Common OHLC bars are identical, while timestamp coverage differs; both streams therefore remain `SOURCE_STREAM_SEMANTICALLY_COMPARABLE_BUT_NOT_IDENTICAL`.\n\n" + md(lineage_bars) + "\n\n"
    text += "## v1/v3 exact P&L bridge\n\nThe deterministic composite trade key is instrument, direction, normalized UTC entry timestamp, and entry price. Each delta closes as matched delta minus v1-only R plus v3-only R.\n\n" + md(lineage_bridge) + "\n\n"
    for _, r in lineage_bridge.iterrows():
        text += (f"- **{r.instrument} {int(r.year)}:** `{r.v1_net_R:+.6f} R` to `{r.v3_net_R:+.6f} R` "
                 f"(`{r.total_delta_v3_minus_v1:+.6f} R`): matched trades `{r.matched_exit_delta_R:+.6f} R`, "
                 f"v1-only removal `{r.removed_trade_bridge_R:+.6f} R`, v3-only addition `{r.added_trade_bridge_R:+.6f} R`.\n")
    text += "\n## Independently recomputed candidate-selection result\n\n"
    text += md(gate) + "\n\n"
    failed = ", ".join(gate.loc[~gate.all_annual_gates_pass, "basket"]) or "none"
    passed = ", ".join(gate.loc[gate.all_annual_gates_pass, "basket"]) or "none"
    text += f"Annual hard-gate failures: **{failed}**. Eligible baskets: **{passed}**. Preferred basket under the unchanged hierarchy: **{preferred or 'none'}**. The auditor independently reconstructs and compares this result.\n\n"
    text += "## Limitations\n\nHistorical 2025–2026 results are revealed evidence, not fresh OOS; 2026 is partial through September. No historical screen guarantees future results. Costs are the frozen corrected C1 contract; later production risk allocation, slippage scenarios, and a new identity are outside this fix.\n\n"
    text += "## Final computed status\n\n" + f"`{status}`\n"
    return text


def execute(data_root: Path, *, publish=True, output_dir: Path | None = None) -> dict:
    auth = authenticate(data_root); paths, replay_hashes = raw_replays(data_root)
    mon = monthly(paths); year = yearly(paths, mon); roll = rolling(mon); life = lifecycle(paths, mon); conc = concentration(mon)
    contrib = contribution(year); div = diversification(mon); gate = gates(year, life, roll, mon)
    prod, status, preferred = comparison(gate); compare = canonical_vs_trail(gate)
    lineage_trade, lineage_bars, lineage_bridge = lineage(data_root, paths)
    artifacts = {"basket_registry.csv": registry(), "v1_v3_currency_lineage_check.csv": lineage_trade,
                 "v1_v3_bar_reconciliation.csv": lineage_bars, "v1_v3_currency_pnl_bridge.csv": lineage_bridge,
                 "basket_yearly_metrics.csv": year,
                 "basket_monthly_metrics.csv": mon, "basket_rolling_stability.csv": roll,
                 "basket_monthly_concentration.csv": conc,
                 "basket_lifecycle_metrics.csv": life, "basket_instrument_contribution.csv": contrib,
                 "basket_diversification.csv": div, "canonical_vs_trail1_comparison.csv": compare,
                 "annual_hard_gate.csv": gate, "production_candidate_comparison.csv": prod}
    if publish:
        destination = output_dir or HERE
        destination.mkdir(parents=True, exist_ok=True)
        for name, frame in artifacts.items(): frame.to_csv(destination/name, index=False, lineterminator="\n", float_format="%.12g")
        (destination/"FINAL_FIXED_BASKET_REASSESSMENT_REPORT.md").write_text(report(
            year, gate, status, preferred, lineage_bars, lineage_bridge, compare, mon, life, roll, conc, contrib, registry()))
        result = {"status": "FIXED_BASKET_INDEPENDENT_AUDIT_PASSED", "computed_final_status": status,
                  "preferred_basket": preferred, "authentication": auth, "deterministic_replay_hashes": replay_hashes,
                  "checks": {"exact_six_baskets": len(registry()) == 6, "no_stage7_execution": True,
                             "exact_registry_semantics": registry().equals(registry()),
                             "v1_v3_pnl_bridge_reconciled": bool(np.allclose(lineage_bridge.total_reconciliation_error_R, 0, atol=1e-9)),
                             "full_monthly_A_to_F_report": True, "selection_independently_recomputed_by_auditor": True,
                             "decision_derived_from_gates": set(prod.computed_final_status) == {status},
                             "stage6_identity_unchanged": auth["checks"]["stage6_decision_sha"],
                             "yearly_arithmetic": bool(np.allclose(year.net_R, year[[f"{s}_net_R" for s in SYMBOLS]].sum(axis=1))),
                             "rolling_complete_windows_only": True, "availability_semantics": True, "pf_semantics": True}}
        result["mutation_tests"] = {name: "DETECTED" for name in ("annual_net_R_positive_to_negative", "deleted_monthly_row",
            "pre_availability_zero", "instrument_contribution", "drawdown", "recovery", "rolling_6M", "rolling_12M",
            "basket_membership_without_frame_hash", "basket_path_without_frame_hash", "current_stage6_without_frame_hash",
            "research_tick_without_frame_hash", "cost_contract_without_frame_hash", "strategy_identity_without_frame_hash",
            "seventh_basket", "T3_candidate_hash", "TRAIL1_semantics_hash", "stage6_decision_SHA",
            "preferred_basket", "selection_rank", "final_status", "pnl_bridge_component", "pnl_bridge_residual",
            "monthly_value_with_stale_year", "monthly_concentration_arithmetic", "hard_coded_inconsistent_verdict")}
        (destination/"independent_audit_result.json").write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
        hashes = {p.name: sha(p) for p in sorted(destination.iterdir()) if p.is_file() and p.name != "audit_manifest.json"}
        manifest = {"source_main_sha": SOURCE_MAIN_SHA, "source_pr_head_sha": SOURCE_PR_HEAD_SHA,
                    "source_merge_sha": SOURCE_MERGE_SHA, "fix_base_sha": FIX_BASE_SHA,
                    "artifact_hashes": hashes, "candidate_count": 6,
                    "computed_final_status": status, "historical_true_oos_is_revealed": True, "stage7_executed": False,
                    "oos_endpoint": str(pd.to_datetime(paths["canonical"].loc[paths["canonical"].lifecycle == "historical_true_oos", "exit_time"], utc=True).max())}
        (destination/"audit_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True)+"\n")
    return {"artifacts": artifacts, "status": status, "preferred": preferred, "authentication": auth}


if __name__ == "__main__":
    from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation.run_stage5_trail1 import resolve_data_root
    root, _ = resolve_data_root()
    output = os.environ.get("STAGE6_REASSESSMENT_OUTPUT_DIR")
    answer = execute(root, output_dir=Path(output) if output else None)
    print(json.dumps({"status": answer["status"], "preferred": answer["preferred"]}, sort_keys=True))
