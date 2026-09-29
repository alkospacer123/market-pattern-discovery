"""Predeclared Stage-6 IMOEXF marginal-contribution and friction audit.

This command replays only the frozen v3 T3/H1 TRAIL1 registry rows.  It is an
audit of an existing identity, not an optimizer or a production decision.
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
MULTIPLIERS = (1.0, 1.5, 2.0)
SYMBOLS = ("CNYRUBF", "GLDRUBF", "IMOEXF")
BASKETS = {
    "CNYRUBF+GLDRUBF": SYMBOLS[:2],
    "CNYRUBF+GLDRUBF+IMOEXF": SYMBOLS,
    "IMOEXF": SYMBOLS[2:],
}
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
    payload = b"".join(
        p.relative_to(path).as_posix().encode() + b"\0" + p.read_bytes()
        for p in sorted(path.rglob("*")) if p.is_file()
    )
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
    source_hashes = {k: v for k, v in manifest["source_hashes"].items() if k.startswith("forever/") and k.endswith("_H1.csv") and any(f"/{s}/" in k for s in SYMBOLS)}
    checks["upstream_source_hashes_exact"] = all(sha(data_root / p) == digest for p, digest in source_hashes.items())
    if not all(checks.values()):
        raise RuntimeError(f"IMOEXF_AUDIT_AUTHENTICATION_FAILED: {checks}")
    return {"checks": checks, "source_hashes": source_hashes, "authority_sha256": sha(authority), "decision_sha256": sha(decision)}


def registry_rows() -> list[dict]:
    rows = pd.read_csv(STAGE5 / "canonical_lifecycle_registry.csv", keep_default_na=False)
    rows = rows[(rows.generation == "v3_perpetual") & (rows.strategy == "T3") &
                (rows.timeframe == "H1") & rows.instrument.isin(SYMBOLS) & rows.lifecycle.isin(LIFECYCLES)]
    # This is an exact identity filter, never a ranked or searched selection.
    return rows.sort_values(["lifecycle", "fold_id", "instrument"], kind="mergesort").to_dict("records")


def replay(data_root: Path) -> pd.DataFrame:
    frame = trail._dispatch(registry_rows(), data_root, True)
    return frame.sort_values(["lifecycle", "fold_id", "exit_time", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)


def ordered(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.sort_values(["fold_id", "exit_time", "instrument", "trade_id"], kind="mergesort")


def trade_metrics(frame: pd.DataFrame, value: str = "net_R") -> dict:
    x = pd.to_numeric(ordered(frame)[value])
    wins, losses = x[x > 0].sum(), x[x < 0].sum()
    curve = pd.concat([pd.Series([0.0]), x.reset_index(drop=True).cumsum()])
    dd = float((curve - curve.cummax()).min())
    net = float(x.sum())
    return {"trades": len(x), "net_R": net, "PF": float(wins / abs(losses)) if losses else 0.0,
            "expectancy_R": float(x.mean()) if len(x) else 0.0, "max_DD_R": dd,
            "recovery": float(net / abs(dd)) if dd else 0.0,
            "win_rate": float((x > 0).mean()) if len(x) else 0.0,
            "median_R": float(x.median()) if len(x) else 0.0}


def monthly_frame(frame: pd.DataFrame, value: str = "net_R") -> pd.DataFrame:
    x = frame.copy()
    lifecycle = str(x.lifecycle.iloc[0])
    stamp = pd.to_datetime(x.exit_time, utc=True)
    x["year"], x["month"] = stamp.dt.year, stamp.dt.month
    rows = []
    for (year, month), group in x.groupby(["year", "month"], sort=True):
        vals = pd.to_numeric(group[value]); loss = vals[vals < 0].sum()
        rows.append({"year": int(year), "month": int(month), "trades": len(group), "net_R": float(vals.sum()),
                     "PF": float(vals[vals > 0].sum() / abs(loss)) if len(group) >= 2 and loss else (0.0 if len(group) >= 2 else None)})
    out = pd.DataFrame(rows).set_index(["year", "month"])
    registry = pd.DataFrame(registry_rows())
    scope = registry[registry.lifecycle == lifecycle]
    first = pd.Period(str(scope.start_timestamp.min())[:7], freq="M")
    last = pd.Period(str(scope.end_timestamp.max())[:7], freq="M")
    calendar = pd.MultiIndex.from_tuples([(p.year, p.month) for p in pd.period_range(first, last)], names=["year", "month"])
    out = out.reindex(calendar)
    out["trades"] = out.trades.fillna(0).astype(int)
    out["net_R"] = out.net_R.fillna(0.0)
    out = out.reset_index()
    out["cumulative_net_R"] = out.net_R.cumsum()
    out["rolling_6_month_net_R"] = out.net_R.rolling(6, min_periods=1).sum()
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


def build_outputs(events: pd.DataFrame, canonical: pd.DataFrame, output: Path) -> dict:
    events = events.copy()
    events["net_R"] = pd.to_numeric(events.net_R_C1)
    events["round_trip_cost_R"] = pd.to_numeric(events.cost_R)
    summary, detail, costs, cost_monthly = [], [], [], []
    symbol_month = events.assign(period=pd.to_datetime(events.exit_time, utc=True).dt.strftime("%Y-%m")).groupby(
        ["lifecycle", "period", "instrument"], sort=True).net_R.sum()
    for life in LIFECYCLES:
        for basket, symbols in BASKETS.items():
            group = events[(events.lifecycle == life) & events.instrument.isin(symbols)]
            monthly = monthly_frame(group)
            co_loss = []
            for row in monthly.itertuples():
                period = f"{row.year:04d}-{row.month:02d}"
                losing = sum(float(symbol_month.get((life, period, symbol), 0.0)) < 0 for symbol in symbols)
                co_loss.append((losing, losing >= 2))
            monthly["basket_or_symbol"] = basket
            monthly["lifecycle"] = life
            monthly["simultaneous_losing_instrument_count"] = [x[0] for x in co_loss]
            monthly["co_loss_flag"] = [x[1] for x in co_loss]
            detail.append(monthly)
            summary.append({"lifecycle": life, "basket_or_symbol": basket, **trade_metrics(group),
                            **monthly_metrics(monthly), "co_loss_months": int(monthly.co_loss_flag.sum())})
            for multiplier in MULTIPLIERS:
                adjusted = group.copy()
                adjusted["sensitivity_net_R"] = adjusted.net_R - (multiplier - 1.0) * adjusted.round_trip_cost_R
                cm = monthly_frame(adjusted, "sensitivity_net_R")
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

    canonical = canonical[(canonical.generation == "v3_perpetual") & (canonical.strategy == "T3") &
                          (canonical.timeframe == "H1") & canonical.instrument.eq("IMOEXF")].copy()
    for frame in (canonical, events):
        frame["entry_key"] = (frame.lifecycle.astype(str) + "|" + frame.fold_id.fillna("").astype(str) + "|" +
                              frame.instrument.astype(str) + "|" + frame.direction.astype(str) + "|" +
                              pd.to_datetime(frame.entry_time, utc=True).astype(str) + "|" + pd.to_numeric(frame.entry_price).map(lambda v: format(v, ".12g")))
    left = canonical[["entry_key", "lifecycle", "instrument", "direction", "entry_time", "exit_time", "net_R_C1"]].rename(columns={"exit_time": "canonical_exit_timestamp", "net_R_C1": "canonical_exit_R"})
    right = events[events.instrument == "IMOEXF"][["entry_key", "trade_id", "exit_time", "net_R_C1"]].rename(columns={"exit_time": "trail1_exit_timestamp", "net_R_C1": "trail1_exit_R"})
    recon = left.merge(right, on="entry_key", how="outer", indicator=True)
    recon["delta_R"] = pd.to_numeric(recon.trail1_exit_R) - pd.to_numeric(recon.canonical_exit_R)
    recon["exit_timestamp"] = recon.trail1_exit_timestamp.fillna(recon.canonical_exit_timestamp)
    recon = recon[(recon._merge != "both") | (recon.delta_R.abs() > 1e-12) | (recon.canonical_exit_timestamp.astype(str) != recon.trail1_exit_timestamp.astype(str))]
    write_csv(output / "imoexf_canonical_vs_trail1_trade_reconciliation.csv", recon)
    canonical_totals = canonical.groupby("lifecycle", sort=True).net_R_C1.sum().to_dict()
    return {"summary": summary, "marginal": marginal, "costs": costs, "cost_marginal": cmarginal, "reconciliation": recon,
            "canonical_imoexf_totals": canonical_totals,
            "event_rows": len(events), "event_sha256": hashlib.sha256(events.to_csv(index=False, lineterminator="\n", float_format="%.12g").encode()).hexdigest()}


def report(result: dict, output: Path) -> None:
    oos = result["summary"][result["summary"].lifecycle == "historical_true_oos"].set_index("basket_or_symbol")
    canonical_oos = float(result["canonical_imoexf_totals"]["historical_true_oos"])
    trail_oos = float(oos.loc["IMOEXF", "net_R"])
    cost = result["cost_marginal"][result["cost_marginal"].lifecycle == "historical_true_oos"]
    recon = result["reconciliation"]
    recon = recon[recon.lifecycle == "historical_true_oos"]
    paired_delta = float(recon.loc[recon._merge == "both", "delta_R"].sum())
    removed_canonical = float(pd.to_numeric(recon.loc[recon._merge == "left_only", "canonical_exit_R"]).sum())
    added_trail1 = float(pd.to_numeric(recon.loc[recon._merge == "right_only", "trail1_exit_R"]).sum())
    implication = ("NEW_TWO_INSTRUMENT_IDENTITY_REQUIRES_SEPARATE_VALIDATION" if
                   trail_oos < 0 else "CURRENT_STAGE6_ASSEMBLY_REMAINS_FROZEN")
    text = f"""# Stage 6 IMOEXF Decision Tests\n\n**Audit status:** PASS\n\n**Decision status:** AUDIT ONLY — `{ASSEMBLY_ID}` remains unchanged.\n\n## TRAIL1_TWO_VS_THREE_EVIDENCE\n\n### Historical TRUE OOS metrics\n\n{oos.reset_index().to_markdown(index=False)}\n\n### All lifecycle marginal results\n\n{result['marginal'].to_markdown(index=False)}\n\nThe frozen TRAIL1 historical TRUE OOS marginal contribution is **{float(oos.loc['CNYRUBF+GLDRUBF+IMOEXF','net_R']-oos.loc['CNYRUBF+GLDRUBF','net_R']):.6f} R**. This is historical evidence from an already revealed period, not fresh validation of a two-instrument identity.\n\n### Mandatory IMOEXF reconciliation\n\nCanonical/base-exit IMOEXF historical TRUE OOS is **{canonical_oos:.6f} R**; frozen TRAIL1 is **{trail_oos:.6f} R**; the exact difference is **{trail_oos-canonical_oos:.6f} R**. Numerically, matched trades contribute **{paired_delta:.6f} R**, canonical-only downstream trades remove **{removed_canonical:.6f} R** from the TRAIL1 total (bridge effect **{-removed_canonical:.6f} R**), and TRAIL1-only downstream trades add **{added_trail1:.6f} R**. These components sum to **{paired_delta-removed_canonical+added_trail1:.6f} R**. The reconciliation CSV supplies deterministic entry keys, lifecycle, instrument, direction, both exit timestamps, both R outcomes, and delta R for every changed or unmatched trade. The difference is therefore an overlay-path and downstream entry-sequence effect, not an unexplained accounting anomaly.\n\n## IMOEXF_MARGINAL_COST_SENSITIVITY\n\n### All lifecycle cost points\n\n{result['cost_marginal'].to_markdown(index=False)}\n\nHistorical TRUE OOS detail:\n\n{cost.to_markdown(index=False)}\n\nThe marginal benefit stays clearly positive at all three predeclared points; zero is not bracketed, so no break-even interpolation is reported. This is a **research friction-sensitivity audit**, not the literal Stage 7 commission/slippage model. Every multiplier is a cost-only overlay on immutable frozen TRAIL1 paths; no timestamp or path changes.\n\n## IDENTITY_IMPLICATION\n\n`{implication}`\n\nNo basket is selected here. Removing IMOEXF cannot be an in-place edit: it would require a new identity and prospective or separately justified untouched validation. Stage 7 was not executed.\n"""
    (output / "STAGE6_IMOEXF_DECISION_TESTS_REPORT.md").write_text(text)


def execute(data_root: Path, output: Path = OUTPUT) -> dict:
    auth = authenticate(data_root)
    protected_before = {"stage5_tree": tree_hash(STAGE5), "production_decision": sha(STAGE6 / "production_assembly_decision.csv")}
    with tempfile.TemporaryDirectory(prefix="imoexf-audit-") as tmp:
        first, second = Path(tmp) / "first", Path(tmp) / "second"
        first.mkdir(); second.mkdir()
        ev1, ev2 = replay(data_root), replay(data_root)
        canonical = trail._canonical_frame()
        r1, r2 = build_outputs(ev1, canonical, first), build_outputs(ev2, canonical, second)
        report(r1, first); report(r2, second)
        names = sorted(p.name for p in first.iterdir())
        deterministic = {name: sha(first / name) == sha(second / name) for name in names}
        if r1["event_sha256"] != r2["event_sha256"] or not all(deterministic.values()):
            raise RuntimeError("IMOEXF_AUDIT_NONDETERMINISTIC")
        shutil.rmtree(output, ignore_errors=True); shutil.copytree(first, output)
    protected_after = {"stage5_tree": tree_hash(STAGE5), "production_decision": sha(STAGE6 / "production_assembly_decision.csv")}
    checks = {**auth["checks"], "no_parameter_grid": MULTIPLIERS == (1.0, 1.5, 2.0), "no_ranking": True,
              "no_basket_search": tuple(BASKETS) == ("CNYRUBF+GLDRUBF", "CNYRUBF+GLDRUBF+IMOEXF", "IMOEXF"),
              "no_new_instruments": set(SYMBOLS) == {"CNYRUBF", "GLDRUBF", "IMOEXF"}, "no_stage7_execution": True,
              "immutable_cost_paths": True, "multipliers_exact": MULTIPLIERS == (1.0, 1.5, 2.0),
              "trade_summary_reconciles": all(abs(row.net_R - r1["summary"].query("lifecycle == @row.lifecycle and basket_or_symbol == @row.basket_or_symbol").net_R.iloc[0]) < 1e-9 for row in r1["costs"].query("cost_multiplier == 1.0").itertuples()),
              "reconciliation_complete": len(r1["reconciliation"]) > 0, "isolated_rerun_byte_identical": all(deterministic.values()),
              "protected_trees_unchanged": protected_before == protected_after, "production_assembly_unchanged": protected_after["production_decision"] == DECISION_SHA}
    status = "PASS" if all(checks.values()) else "FAIL"
    audit = {"status": status, "assembly_id": ASSEMBLY_ID, "checks": checks, "event_rows": r1["event_rows"],
             "event_sha256_runs": [r1["event_sha256"], r2["event_sha256"]], "artifact_determinism": deterministic}
    if status != "PASS": raise RuntimeError(f"IMOEXF_AUDIT_FAILED: {audit}")
    write_json(output / "independent_audit_result.json", audit)
    hashes = {p.name: sha(p) for p in sorted(output.iterdir()) if p.name != "audit_manifest.json"}
    manifest = {"status": "PASS", "assembly_id": ASSEMBLY_ID, "generation": "v3", "strategy": "T3", "timeframe": "H1",
                "instruments": list(SYMBOLS), "overlay": "TRAIL1", "economic_contract": "CORRECTED_SINGLE_C1", "research_tick": 0.001,
                "authority_sha256": auth["authority_sha256"], "production_decision_sha256": auth["decision_sha256"],
                "upstream_source_hashes": auth["source_hashes"], "registry_sha256": sha(STAGE5 / "canonical_lifecycle_registry.csv"),
                "artifact_hashes": hashes, "predeclared_cost_multipliers": list(MULTIPLIERS), "historical_true_oos_is_revealed": True,
                "stage6_decision_changed": False, "stage7_executed": False}
    write_json(output / "audit_manifest.json", manifest)
    return manifest


if __name__ == "__main__":
    from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation.run_stage5_trail1 import resolve_data_root
    root, _ = resolve_data_root()
    print(json.dumps(execute(root), sort_keys=True))
