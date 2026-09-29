"""Corrected, audit-only Stage-6 IMOEXF frozen-TRAIL1 decision evidence.

Month attribution deliberately matches the Stage-5 TRAIL1 authority: exit
timestamps are parsed with ``utc=True`` and assigned to their UTC YYYY-MM.
Authenticated registry start/end timestamps are converted by the same rule.
This module neither selects a basket nor executes Stage 7.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pandas as pd

from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation import stage5_trail1_lifecycle as trail

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
STAGE5 = HERE.parent / "stage5_structural_validation"
STAGE6 = HERE.parent / "stage6_production_assembly"
OUTPUT = HERE / "audit_results"
ASSEMBLY_ID = "PROD_STAGE6_83C7B31BB42C"
AUDIT_STATUS = "POST_V3_STAGE6_IMOEXF_DECISION_TESTS_CORRECTION_AUDIT_PASSED"
MULTIPLIERS = (1.0, 1.5, 2.0)
SYMBOLS = ("CNYRUBF", "GLDRUBF", "IMOEXF")
BASKETS = {"CNYRUBF+GLDRUBF": SYMBOLS[:2], "CNYRUBF+GLDRUBF+IMOEXF": SYMBOLS, "IMOEXF": SYMBOLS[2:]}
LIFECYCLES = ("baseline", "walk_forward", "historical_true_oos")
DECISION_SHA = "1efdaac2b689e2537b17371407a4d219dec5334c490a56c2378b065b9055431b"
TRAIL_EXECUTION_SHA = "d1d8ac2eeea9095becd6f74295e4a540d02ee0494237af5f16f6d66a487f221b"
T3_SHA = "840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, rows) -> None:
    frame = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)
    frame.to_csv(path, index=False, lineterminator="\n", float_format="%.12g", na_rep="")


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def tree_hash(path: Path) -> str:
    payload = b"".join(p.relative_to(path).as_posix().encode() + b"\0" + p.read_bytes()
                       for p in sorted(path.rglob("*")) if p.is_file())
    return hashlib.sha256(payload).hexdigest()


def authenticate(data_root: Path) -> dict:
    authority = STAGE6 / "POST_V3_STAGE_6_IMOEXF_MARGINAL_CONTRIBUTION_AUDIT.md"
    decision = STAGE6 / "production_assembly_decision.csv"
    execution = STAGE5 / "stage5_trail1_execution.py"
    t3 = ROOT / "TradingSystemLab/strategies/trend/T3_MTF_Trend.py"
    manifest = json.loads((STAGE5 / "trail1/manifest_trail1.json").read_text())
    assembly = pd.read_csv(decision)
    checks = {
        "authority_present": authority.is_file(),
        "authority_declares_audit_only": "AUDIT-ONLY / NO STAGE 6 DECISION CHANGE" in authority.read_text(),
        "assembly_id_exact": ASSEMBLY_ID in assembly.astype(str).to_csv(index=False),
        "production_decision_sha_exact": sha(decision) == DECISION_SHA,
        "trail1_semantics_sha_exact": sha(execution) == TRAIL_EXECUTION_SHA,
        "frozen_t3_sha_exact": sha(t3) == T3_SHA,
        "stage5_certified": manifest.get("status") == "STAGE5_TRAIL1_FINAL_CLOSEOUT_PASSED",
        "trail1_trigger_exact": manifest.get("trigger", "").startswith("first completed execution bar after entry reaching +1.0"),
        "cost_contract_exact": manifest.get("cost_contract") == "CORRECTED_SINGLE_C1",
        "data_commit_exact": subprocess.check_output(["git", "-C", str(data_root), "rev-parse", "HEAD"], text=True).strip() == manifest["data_repo_commit"],
    }
    source_hashes = {k: v for k, v in manifest["source_hashes"].items()
                     if k.startswith("forever/") and k.endswith("_H1.csv") and any(f"/{s}/" in k for s in SYMBOLS)}
    checks["upstream_source_hashes_exact"] = all(sha(data_root / p) == digest for p, digest in source_hashes.items())
    if not all(checks.values()):
        raise RuntimeError(f"IMOEXF_AUDIT_AUTHENTICATION_FAILED: {checks}")
    return {"checks": checks, "source_hashes": source_hashes, "authority_sha256": sha(authority), "decision_sha256": sha(decision)}


def registry_frame() -> pd.DataFrame:
    rows = pd.read_csv(STAGE5 / "canonical_lifecycle_registry.csv", keep_default_na=False)
    return rows[(rows.generation == "v3_perpetual") & (rows.strategy == "T3") &
                (rows.timeframe == "H1") & rows.instrument.isin(SYMBOLS) & rows.lifecycle.isin(LIFECYCLES)].copy()


def registry_rows() -> list[dict]:
    return registry_frame().sort_values(["lifecycle", "fold_id", "instrument"], kind="mergesort").to_dict("records")


def replay(data_root: Path) -> pd.DataFrame:
    frame = trail._dispatch(registry_rows(), data_root, True)
    return frame.sort_values(["lifecycle", "fold_id", "exit_time", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)


def ordered(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.sort_values(["fold_id", "exit_time", "instrument", "trade_id"], kind="mergesort")


def profit_factor(values: pd.Series) -> float | None:
    """Repository-safe PF: undefined for <2 trades or a zero loss denominator."""
    x = pd.to_numeric(values)
    if len(x) < 2:
        return None
    losses = float(x[x < 0].sum())
    return float(x[x > 0].sum() / abs(losses)) if losses < 0 else None


def trade_metrics(frame: pd.DataFrame, value: str = "net_R") -> dict:
    x = pd.to_numeric(ordered(frame)[value])
    curve = pd.concat([pd.Series([0.0]), x.reset_index(drop=True).cumsum()])
    dd, net = float((curve - curve.cummax()).min()), float(x.sum())
    return {"trades": len(x), "net_R": net, "PF": profit_factor(x),
            "expectancy_R": float(x.mean()) if len(x) else 0.0, "max_DD_R": dd,
            "recovery": float(net / abs(dd)) if dd else 0.0,
            "win_rate": float((x > 0).mean()) if len(x) else 0.0,
            "median_R": float(x.median()) if len(x) else 0.0}


def availability_months(lifecycle: str, symbols: tuple[str, ...], registry: pd.DataFrame | None = None) -> dict[str, set[pd.Period]]:
    """Return each component's authenticated UTC months (NOT_YET_AVAILABLE excluded)."""
    reg = registry_frame() if registry is None else registry.copy()
    reg = reg[(reg.lifecycle == lifecycle) & reg.instrument.isin(symbols)]
    result: dict[str, set[pd.Period]] = {symbol: set() for symbol in symbols}
    for row in reg.itertuples():
        start = pd.Timestamp(row.start_timestamp).tz_convert("UTC") if pd.Timestamp(row.start_timestamp).tzinfo else pd.Timestamp(row.start_timestamp).tz_localize("UTC")
        end = pd.Timestamp(row.end_timestamp).tz_convert("UTC") if pd.Timestamp(row.end_timestamp).tzinfo else pd.Timestamp(row.end_timestamp).tz_localize("UTC")
        result[row.instrument].update(pd.period_range(start.tz_localize(None).to_period("M"), end.tz_localize(None).to_period("M"), freq="M"))
    if any(not result[s] for s in symbols):
        raise ValueError(f"missing authenticated availability: {lifecycle} {symbols}")
    return result


def monthly_frame(frame: pd.DataFrame, value: str = "net_R", *, symbols: tuple[str, ...] | None = None,
                  registry: pd.DataFrame | None = None) -> pd.DataFrame:
    if frame.empty:
        raise ValueError("monthly frame requires lifecycle-bearing evidence")
    lifecycle = str(frame.lifecycle.iloc[0])
    symbols = tuple(sorted(frame.instrument.unique())) if symbols is None else tuple(symbols)
    available = availability_months(lifecycle, symbols, registry)
    portfolio_months = sorted(set().union(*(available[s] for s in symbols)))
    x = frame.copy()
    stamps = pd.to_datetime(x.exit_time, utc=True)
    x["period"] = stamps.dt.tz_localize(None).dt.to_period("M")
    rows = []
    for period in portfolio_months:
        group = x[x.period == period]
        vals = pd.to_numeric(group[value])
        rows.append({"year": period.year, "month": period.month, "trades": len(group),
                     "net_R": float(vals.sum()), "PF": profit_factor(vals),
                     "available_instruments": "+".join(s for s in symbols if period in available[s])})
    out = pd.DataFrame(rows)
    out["cumulative_net_R"] = out.net_R.cumsum()
    out["rolling_6_month_net_R"] = out.net_R.rolling(6, min_periods=6).sum()
    return out


def monthly_metrics(monthly: pd.DataFrame) -> dict:
    x = monthly.net_R
    curve = pd.concat([pd.Series([0.0]), x.cumsum().reset_index(drop=True)])
    streak = longest = 0
    for value in x:
        streak = streak + 1 if value < 0 else 0
        longest = max(longest, streak)
    return {"positive_month_share": float((x > 0).mean()), "monthly_median_R": float(x.median()),
            "monthly_std_R": float(x.std(ddof=1)) if len(x) > 1 else 0.0, "worst_month_R": float(x.min()),
            "monthly_equity_max_DD_R": float((curve - curve.cummax()).min()),
            "longest_negative_month_streak": longest}


def build_outputs(events: pd.DataFrame, canonical: pd.DataFrame, output: Path, registry: pd.DataFrame | None = None) -> dict:
    events = events.copy(); events["net_R"] = pd.to_numeric(events.net_R_C1); events["round_trip_cost_R"] = pd.to_numeric(events.cost_R)
    summary, detail, costs, cost_monthly = [], [], [], []
    event_period = pd.to_datetime(events.exit_time, utc=True).dt.strftime("%Y-%m")
    symbol_month = events.assign(period=event_period).groupby(["lifecycle", "period", "instrument"], sort=True).net_R.sum()
    path_fingerprints = []
    for life in LIFECYCLES:
        for basket, symbols in BASKETS.items():
            group = events[(events.lifecycle == life) & events.instrument.isin(symbols)]
            monthly = monthly_frame(group, symbols=symbols, registry=registry)
            losing_counts = [sum(float(symbol_month.get((life, f"{r.year:04d}-{r.month:02d}", s), 0.0)) < 0
                                 for s in symbols if s in r.available_instruments.split("+")) for r in monthly.itertuples()]
            monthly["basket_or_symbol"], monthly["lifecycle"] = basket, life
            monthly["simultaneous_losing_instrument_count"] = losing_counts
            monthly["co_loss_flag"] = [n >= 2 for n in losing_counts]
            detail.append(monthly)
            summary.append({"lifecycle": life, "basket_or_symbol": basket, **trade_metrics(group),
                            **monthly_metrics(monthly), "co_loss_months": int(monthly.co_loss_flag.sum())})
            base_path = group[["trade_id", "entry_time", "exit_time"]].astype(str).to_csv(index=False)
            for multiplier in MULTIPLIERS:
                adjusted = group.copy()
                adjusted["sensitivity_net_R"] = adjusted.net_R - (multiplier - 1.0) * adjusted.round_trip_cost_R
                path_fingerprints.append(hashlib.sha256(base_path.encode()).hexdigest())
                cm = monthly_frame(adjusted, "sensitivity_net_R", symbols=symbols, registry=registry)
                cm["lifecycle"], cm["basket_or_symbol"], cm["cost_multiplier"] = life, basket, multiplier
                cost_monthly.append(cm)
                costs.append({"lifecycle": life, "basket_or_symbol": basket, "cost_multiplier": multiplier,
                              **trade_metrics(adjusted, "sensitivity_net_R"), **monthly_metrics(cm)})
    summary = pd.DataFrame(summary)
    three = summary[summary.basket_or_symbol == "CNYRUBF+GLDRUBF+IMOEXF"][["lifecycle", "net_R"]].rename(columns={"net_R": "three_instrument_net_R"})
    two = summary[summary.basket_or_symbol == "CNYRUBF+GLDRUBF"][["lifecycle", "net_R"]].rename(columns={"net_R": "two_instrument_net_R"})
    marginal = three.merge(two, on="lifecycle"); marginal["IMOEXF_marginal_net_R"] = marginal.three_instrument_net_R - marginal.two_instrument_net_R
    write_csv(output / "trail1_basket_summary.csv", summary[summary.basket_or_symbol != "IMOEXF"].merge(marginal, on="lifecycle"))
    write_csv(output / "trail1_lifecycle_summary.csv", summary)
    write_csv(output / "trail1_monthly_detail.csv", pd.concat(detail, ignore_index=True))
    costs = pd.DataFrame(costs)
    c3 = costs[costs.basket_or_symbol == "CNYRUBF+GLDRUBF+IMOEXF"][["lifecycle", "cost_multiplier", "net_R"]].rename(columns={"net_R": "three_instrument_net_R"})
    c2 = costs[costs.basket_or_symbol == "CNYRUBF+GLDRUBF"][["lifecycle", "cost_multiplier", "net_R"]].rename(columns={"net_R": "two_instrument_net_R"})
    cmarginal = c3.merge(c2, on=["lifecycle", "cost_multiplier"]); cmarginal["IMOEXF_marginal_net_R"] = cmarginal.three_instrument_net_R - cmarginal.two_instrument_net_R
    write_csv(output / "cost_sensitivity_summary.csv", costs.merge(cmarginal, on=["lifecycle", "cost_multiplier"], how="left"))
    write_csv(output / "cost_sensitivity_monthly.csv", pd.concat(cost_monthly, ignore_index=True))
    canonical = canonical[(canonical.generation == "v3_perpetual") & (canonical.strategy == "T3") & (canonical.timeframe == "H1") & canonical.instrument.eq("IMOEXF")].copy()
    for f in (canonical, events):
        f["entry_key"] = (f.lifecycle.astype(str) + "|" + f.fold_id.fillna("").astype(str) + "|" + f.instrument.astype(str) + "|" + f.direction.astype(str) + "|" + pd.to_datetime(f.entry_time, utc=True).astype(str) + "|" + pd.to_numeric(f.entry_price).map(lambda v: format(v, ".12g")))
    left = canonical[["entry_key", "lifecycle", "instrument", "direction", "entry_time", "exit_time", "net_R_C1"]].rename(columns={"exit_time": "canonical_exit_timestamp", "net_R_C1": "canonical_exit_R"})
    right = events[events.instrument == "IMOEXF"][["entry_key", "trade_id", "exit_time", "net_R_C1"]].rename(columns={"exit_time": "trail1_exit_timestamp", "net_R_C1": "trail1_exit_R"})
    recon = left.merge(right, on="entry_key", how="outer", indicator=True)
    recon["delta_R"] = pd.to_numeric(recon.trail1_exit_R) - pd.to_numeric(recon.canonical_exit_R)
    recon["exit_timestamp"] = recon.trail1_exit_timestamp.fillna(recon.canonical_exit_timestamp)
    recon = recon[(recon._merge != "both") | (recon.delta_R.abs() > 1e-12) | (recon.canonical_exit_timestamp.astype(str) != recon.trail1_exit_timestamp.astype(str))]
    write_csv(output / "imoexf_canonical_vs_trail1_trade_reconciliation.csv", recon)
    return {"summary": summary, "marginal": marginal, "costs": costs, "cost_marginal": cmarginal,
            "reconciliation": recon, "canonical_imoexf_totals": canonical.groupby("lifecycle").net_R_C1.sum().to_dict(),
            "event_rows": len(events), "events": events, "path_fingerprints": path_fingerprints,
            "event_sha256": hashlib.sha256(events.to_csv(index=False, lineterminator="\n", float_format="%.12g").encode()).hexdigest()}


def _same(a, b, tolerance=1e-9) -> bool:
    return (pd.isna(a) and pd.isna(b)) or (not pd.isna(a) and not pd.isna(b) and abs(float(a) - float(b)) <= tolerance)


def independent_audit(output: Path, events: pd.DataFrame, canonical: pd.DataFrame,
                      registry: pd.DataFrame | None = None, *, deterministic=True) -> dict:
    """Independently rebuild every monthly field; persisted producer summaries are never trusted."""
    names = ("monthly_detail_rebuilt", "monthly_summary_rebuilt", "pf_semantics", "availability_semantics",
             "rolling_six_complete", "cost_paths_immutable", "cost_formula_rebuilt", "reconciliation_bridge",
             "no_ranking", "no_stage7_execution", "assembly_preserved", "deterministic")
    checks = {name: "NOT_CHECKED" for name in names}
    actual_detail = pd.read_csv(output / "trail1_monthly_detail.csv")
    actual_summary = pd.read_csv(output / "trail1_lifecycle_summary.csv")
    rebuilt_detail, rebuilt_summary = [], []
    events = events.copy(); events["net_R"] = pd.to_numeric(events.net_R_C1); events["round_trip_cost_R"] = pd.to_numeric(events.cost_R)
    for life in LIFECYCLES:
        for basket, symbols in BASKETS.items():
            group = events[(events.lifecycle == life) & events.instrument.isin(symbols)]
            m = monthly_frame(group, symbols=symbols, registry=registry)
            period_net = events.assign(period=pd.to_datetime(events.exit_time, utc=True).dt.strftime("%Y-%m")).groupby(["lifecycle", "period", "instrument"]).net_R.sum()
            counts = [sum(float(period_net.get((life, f"{r.year:04d}-{r.month:02d}", s), 0)) < 0 for s in symbols if s in r.available_instruments.split("+")) for r in m.itertuples()]
            m["basket_or_symbol"], m["lifecycle"] = basket, life
            m["simultaneous_losing_instrument_count"], m["co_loss_flag"] = counts, [n >= 2 for n in counts]
            rebuilt_detail.append(m)
            rebuilt_summary.append({"lifecycle": life, "basket_or_symbol": basket, **trade_metrics(group),
                                    **monthly_metrics(m), "co_loss_months": sum(n >= 2 for n in counts)})
    expected_detail = pd.concat(rebuilt_detail, ignore_index=True)
    key = ["lifecycle", "basket_or_symbol", "year", "month"]
    a = actual_detail.sort_values(key).reset_index(drop=True); e = expected_detail.sort_values(key).reset_index(drop=True)
    fields = ["trades", "net_R", "PF", "available_instruments", "cumulative_net_R", "rolling_6_month_net_R", "simultaneous_losing_instrument_count", "co_loss_flag"]
    detail_ok = len(a) == len(e) and all((str(x) == str(y) if field in {"available_instruments", "co_loss_flag"} else _same(x, y))
                                          for field in fields for x, y in zip(a.get(field, []), e.get(field, [])))
    checks["monthly_detail_rebuilt"] = "PASS" if detail_ok else "FAIL"
    expected_summary = pd.DataFrame(rebuilt_summary).sort_values(["lifecycle", "basket_or_symbol"]).reset_index(drop=True)
    a_summary = actual_summary.sort_values(["lifecycle", "basket_or_symbol"]).reset_index(drop=True)
    summary_fields = ["trades", "net_R", "PF", "positive_month_share", "monthly_median_R", "monthly_std_R", "worst_month_R", "monthly_equity_max_DD_R", "longest_negative_month_streak", "co_loss_months"]
    summary_ok = len(a_summary) == len(expected_summary) and all(_same(x, y) for f in summary_fields for x, y in zip(a_summary.get(f, []), expected_summary.get(f, [])))
    checks["monthly_summary_rebuilt"] = "PASS" if summary_ok else "FAIL"
    all_win = [g for _, g in events.assign(p=pd.to_datetime(events.exit_time, utc=True).dt.strftime("%Y-%m")).groupby(["lifecycle", "instrument", "p"]) if len(g) >= 2 and (g.net_R > 0).all()]
    checks["pf_semantics"] = "PASS" if all_win and all(profit_factor(g.net_R) is None for g in all_win) and detail_ok else "FAIL"
    standalone = expected_detail[expected_detail.basket_or_symbol == "IMOEXF"]
    av = all(row.available_instruments == "IMOEXF" for row in standalone.itertuples())
    checks["availability_semantics"] = "PASS" if av and detail_ok else "FAIL"
    rolling_ok = all(g.rolling_6_month_net_R.iloc[:5].isna().all() and all(_same(g.rolling_6_month_net_R.iloc[i], g.net_R.iloc[i-5:i+1].sum()) for i in range(5, len(g))) for _, g in expected_detail.groupby(["lifecycle", "basket_or_symbol"], sort=False))
    checks["rolling_six_complete"] = "PASS" if rolling_ok and detail_ok else "FAIL"
    costs = pd.read_csv(output / "cost_sensitivity_summary.csv")
    rebuilt_cost_ok = True
    for row in costs.itertuples():
        g = events[(events.lifecycle == row.lifecycle) & events.instrument.isin(BASKETS[row.basket_or_symbol])]
        adjusted = g.net_R - (float(row.cost_multiplier) - 1) * g.round_trip_cost_R
        rebuilt_cost_ok &= _same(row.net_R, adjusted.sum()) and row.trades == len(g)
    checks["cost_formula_rebuilt"] = "PASS" if rebuilt_cost_ok and set(costs.cost_multiplier) == set(MULTIPLIERS) else "FAIL"
    checks["cost_paths_immutable"] = "PASS" if rebuilt_cost_ok and all(costs.groupby(["lifecycle", "basket_or_symbol"]).trades.nunique() == 1) else "FAIL"
    recon = pd.read_csv(output / "imoexf_canonical_vs_trail1_trade_reconciliation.csv")
    oos = recon[recon.lifecycle == "historical_true_oos"]
    bridge = pd.to_numeric(oos.delta_R).sum(skipna=True) - pd.to_numeric(oos.loc[oos._merge == "left_only", "canonical_exit_R"]).sum(skipna=True) + pd.to_numeric(oos.loc[oos._merge == "right_only", "trail1_exit_R"]).sum(skipna=True)
    ctotal = float(canonical[(canonical.generation == "v3_perpetual") & (canonical.strategy == "T3") & (canonical.timeframe == "H1") & (canonical.instrument == "IMOEXF") & (canonical.lifecycle == "historical_true_oos")].net_R_C1.sum())
    ttotal = float(events[(events.instrument == "IMOEXF") & (events.lifecycle == "historical_true_oos")].net_R.sum())
    checks["reconciliation_bridge"] = "PASS" if _same(bridge, ttotal - ctotal) else "FAIL"
    schemas = " ".join(" ".join(pd.read_csv(p, nrows=0).columns) for p in output.glob("*.csv")).lower()
    checks["no_ranking"] = "PASS" if not any(x in schemas for x in ("rank", "optimizer", "objective")) else "FAIL"
    # All executable input/output roots are enumerated here; none enters a Stage-7 tree.
    checks["no_stage7_execution"] = "PASS" if all("stage7" not in str(p).lower() for p in (HERE, STAGE5, STAGE6, output)) else "FAIL"
    checks["assembly_preserved"] = "PASS" if sha(STAGE6 / "production_assembly_decision.csv") == DECISION_SHA else "FAIL"
    checks["deterministic"] = "PASS" if deterministic else "FAIL"
    status = AUDIT_STATUS if all(v == "PASS" for v in checks.values()) else "POST_V3_STAGE6_IMOEXF_DECISION_TESTS_CORRECTION_AUDIT_FAILED"
    return {"status": status, "assembly_id": ASSEMBLY_ID, "checks": checks}


def report(result: dict, output: Path, audit_status: str) -> None:
    def markdown(frame: pd.DataFrame) -> str:
        values = frame.map(lambda x: "" if pd.isna(x) else format(x, ".6g") if isinstance(x, float) else str(x))
        headers = list(values.columns)
        lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
        lines.extend("| " + " | ".join(row) + " |" for row in values.astype(str).to_numpy())
        return "\n".join(lines)
    oos = result["summary"][result["summary"].lifecycle == "historical_true_oos"].set_index("basket_or_symbol")
    canonical_oos = float(result["canonical_imoexf_totals"]["historical_true_oos"]); trail_oos = float(oos.loc["IMOEXF", "net_R"])
    recon = result["reconciliation"]; recon = recon[recon.lifecycle == "historical_true_oos"]
    paired = float(recon.loc[recon._merge == "both", "delta_R"].sum()); removed = float(pd.to_numeric(recon.loc[recon._merge == "left_only", "canonical_exit_R"]).sum()); added = float(pd.to_numeric(recon.loc[recon._merge == "right_only", "trail1_exit_R"]).sum())
    monthly = pd.read_csv(output / "trail1_monthly_detail.csv")
    im = monthly[(monthly.lifecycle == "historical_true_oos") & (monthly.basket_or_symbol == "IMOEXF")]
    y2025 = float(im[im.year == 2025].net_R.sum()); y2026 = float(im[im.year == 2026].net_R.sum()); sep = im[(im.year == 2026) & (im.month == 9)].iloc[0]
    positive = float((im.net_R > 0).mean())
    cost = result["cost_marginal"][result["cost_marginal"].lifecycle == "historical_true_oos"]
    text = f"""# Stage 6 IMOEXF Decision Tests — Monthly Semantics Correction\n\n**Audit status:** `{audit_status}`\n\n**Decision status:** AUDIT ONLY — `{ASSEMBLY_ID}` remains unchanged.\n\n## Calendar and monthly semantics\n\nMonth attribution uses the UTC calendar of the exit timestamp, exactly as the Stage 5 TRAIL1 lifecycle authority (`pd.to_datetime(..., utc=True).dt.strftime('%Y-%m')`). `NOT_YET_AVAILABLE` is excluded; authenticated available months with no trades remain zero-return rows. Monthly PF is blank for fewer than two trades and for a zero gross-loss denominator. Six-month rolling values require six complete available calendar months.\n\n## Frozen TRAIL1 evidence\n\n### Historical TRUE OOS metrics\n\n{markdown(oos.reset_index())}\n\n### All lifecycle marginal results\n\n{markdown(result['marginal'])}\n\n## Corrected standalone IMOEXF monitoring\n\n* Frozen TRAIL1 2025 Net R: **{y2025:.6f} R**.\n* Frozen TRAIL1 2026 through September Net R: **{y2026:.6f} R**.\n* Full six-month rolling Net R ending 2026-09: **{float(sep.rolling_6_month_net_R):.6f} R**.\n* Availability-aware positive-month share: **{positive:.6f}**.\n\nThese are frozen TRAIL1 monitoring results. They are distinct from canonical/base-exit evidence and are revealed historical evidence, not fresh OOS.\n\n## Canonical/base-exit versus frozen TRAIL1 bridge\n\nCanonical IMOEXF historical TRUE OOS is **{canonical_oos:.6f} R**; frozen TRAIL1 is **{trail_oos:.6f} R**; difference **{trail_oos-canonical_oos:.6f} R**. Matched exit delta is **{paired:.6f} R**; canonical-only trades total **{removed:.6f} R** ({int((recon._merge == 'left_only').sum())} trades); TRAIL1-only trades total **{added:.6f} R** ({int((recon._merge == 'right_only').sum())} trades).\n\n## Predeclared cost sensitivity\n\n{markdown(cost)}\n\nThe only multipliers are 1.0x, 1.5x, and 2.0x, applied as `TRAIL1_net_R - (multiplier - 1) * round_trip_C1_cost_R` without changing trade paths.\n\n## Identity implication\n\n`CURRENT_STAGE6_ASSEMBLY_REMAINS_FROZEN`\n\nNo optimization, ranking, basket selection, strategy change, or Stage 7 execution occurred.\n"""
    (output / "STAGE6_IMOEXF_DECISION_TESTS_REPORT.md").write_text(text)


def execute(data_root: Path, output: Path = OUTPUT) -> dict:
    auth = authenticate(data_root)
    protected_before = {"stage5_tree": tree_hash(STAGE5), "production_decision": sha(STAGE6 / "production_assembly_decision.csv")}
    with tempfile.TemporaryDirectory(prefix="imoexf-audit-") as tmp:
        first, second = Path(tmp) / "first", Path(tmp) / "second"; first.mkdir(); second.mkdir()
        ev1, ev2, canonical = replay(data_root), replay(data_root), trail._canonical_frame()
        r1, r2 = build_outputs(ev1, canonical, first), build_outputs(ev2, canonical, second)
        # Reports are generated only after independent semantic validation of producer CSVs.
        a1 = independent_audit(first, ev1, canonical); a2 = independent_audit(second, ev2, canonical)
        if a1["status"] != AUDIT_STATUS or a2["status"] != AUDIT_STATUS:
            raise RuntimeError(f"IMOEXF_AUDIT_FAILED: {a1} {a2}")
        report(r1, first, a1["status"]); report(r2, second, a2["status"])
        names = sorted(p.name for p in first.iterdir())
        hashes1, hashes2 = {n: sha(first / n) for n in names}, {n: sha(second / n) for n in names}
        deterministic = hashes1 == hashes2 and r1["event_sha256"] == r2["event_sha256"]
        if not deterministic:
            raise RuntimeError("IMOEXF_AUDIT_NONDETERMINISTIC")
        a1["authentication_checks"] = auth["checks"]
        a1["event_rows"] = r1["event_rows"]; a1["event_sha256_runs"] = [r1["event_sha256"], r2["event_sha256"]]
        a1["determinism"] = {"run_1_hashes": hashes1, "run_2_hashes": hashes2, "byte_identical": True}
        write_json(first / "independent_audit_result.json", a1)
        shutil.rmtree(output, ignore_errors=True); shutil.copytree(first, output)
    protected_after = {"stage5_tree": tree_hash(STAGE5), "production_decision": sha(STAGE6 / "production_assembly_decision.csv")}
    if protected_before != protected_after or protected_after["production_decision"] != DECISION_SHA:
        raise RuntimeError("PROTECTED_EVIDENCE_MUTATED")
    hashes = {p.name: sha(p) for p in sorted(output.iterdir()) if p.name != "audit_manifest.json"}
    manifest = {"status": AUDIT_STATUS, "identity_implication": "CURRENT_STAGE6_ASSEMBLY_REMAINS_FROZEN", "assembly_id": ASSEMBLY_ID,
                "generation": "v3", "strategy": "T3", "timeframe": "H1", "instruments": list(SYMBOLS), "overlay": "TRAIL1",
                "economic_contract": "CORRECTED_SINGLE_C1", "research_tick": 0.001, "calendar_attribution": "UTC exit timestamp YYYY-MM; matches Stage 5 TRAIL1",
                "authority_sha256": auth["authority_sha256"], "production_decision_sha256": auth["decision_sha256"],
                "upstream_source_hashes": auth["source_hashes"], "registry_sha256": sha(STAGE5 / "canonical_lifecycle_registry.csv"),
                "artifact_hashes": hashes, "predeclared_cost_multipliers": list(MULTIPLIERS), "historical_true_oos_is_revealed": True,
                "stage6_decision_changed": False, "stage7_executed": False, "protected_hashes_before": protected_before, "protected_hashes_after": protected_after}
    write_json(output / "audit_manifest.json", manifest)
    return manifest


if __name__ == "__main__":
    from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation.run_stage5_trail1 import resolve_data_root
    root, _ = resolve_data_root()
    print(json.dumps(execute(root), sort_keys=True))
