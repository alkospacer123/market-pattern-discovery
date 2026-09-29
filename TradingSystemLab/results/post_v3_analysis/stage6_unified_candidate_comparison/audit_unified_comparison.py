"""Independent, fail-closed auditor for Stage 6.6 evidence.

The audit deliberately rebuilds every portfolio and hierarchy input from the
five authenticated ledgers.  Producer gate, hierarchy, and rank columns are
comparison targets only; they are never calculation inputs.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
STARTING_MAIN_SHA = "1bf22b559c12f6244dd4087de176d5f684a1025e"
T3_SHA = "840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c"
PARAMETER_SHA = "4e73cdb77246cb07b5953160b9fc0ab36bfd4bd6d9a7f7faaae7e6e392ee340a"
CANDIDATE = "T3_H1_candidate_v3"
CONFIG_IDENTITY = "T3-H1-4e73cdb77246"
EXPECTED_SOURCES = {
    "CANONICAL": ("0b4e9165b0de5b2206c723240b960119531540ec60e84435c4289ef6718288e7", 446),
    "TRAIL1": ("0f9034edf228a687da67e9f3e35fad01f2339be162c558e6d802c3cd77eea8ad", 418),
    "SESSION_10_21": ("bb55cc21cd20e8610995821aa451705eecef974bbd8beb5fe1685e87b74c8191", 428),
    "LOCK1_AFTER_2R": ("aa85e51bacf63517c4a37b7ae22dca3f02870526ea73fd13d6f7bb3f7db9607f", 447),
    "STRUCTURAL_STACK_V1": ("84869f4a4392be204272234d3e6c881b8ce6b1bcdae16506e959e042444fcbdd", 429),
}
EXPECTED_VARIANTS = list(EXPECTED_SOURCES)
PERIODS = (("baseline", 2023, "BASELINE_2023"), ("baseline", 2024, "BASELINE_2024"),
           ("walk_forward", 2024, "WF24"), ("historical_true_oos", 2025, "OOS2025"),
           ("historical_true_oos", 2026, "OOS2026_YTD"))
LIFECYCLES = ("baseline", "walk_forward", "historical_true_oos")
ORDER = ["annual_floor_R", "worst_complete_12M_R", "worst_complete_6M_R", "worst_trade_level_DD_R",
         "minimum_lifecycle_recovery", "positive_month_share", "median_monthly_R", "longest_negative_month_streak",
         "top_3_concentration", "chronological_net_R"]
ASCENDING = [False] * 7 + [True, True, False, True]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_matches(path: Path, expected_sha: str, expected_count: int) -> bool:
    return path.is_file() and sha(path) == expected_sha and len(pd.read_csv(path)) == expected_count


def validate_starting_sha(repo: Path, starting_sha: str, head: str = "HEAD") -> tuple[bool, bool]:
    exists = subprocess.run(["git", "cat-file", "-e", f"{starting_sha}^{{commit}}"], cwd=repo,
                            capture_output=True, check=False).returncode == 0
    ancestor = exists and subprocess.run(["git", "merge-base", "--is-ancestor", starting_sha, head], cwd=repo,
                                         capture_output=True, check=False).returncode == 0
    return exists, ancestor


def max_dd(values) -> float:
    curve = pd.concat([pd.Series([0.0]), pd.Series(values, dtype=float).reset_index(drop=True).cumsum()], ignore_index=True)
    return float((curve - curve.cummax()).min())


def recovery(net: float, dd: float) -> float:
    return float(net / abs(dd)) if dd else np.nan


def negative_streak(values) -> int:
    longest = current = 0
    for value in values:
        current = current + 1 if value < 0 else 0
        longest = max(longest, current)
    return longest


def rolling_windows(months: pd.DataFrame, window: int) -> list[float]:
    periods = pd.PeriodIndex(months.year.astype(str) + "-" + months.month.astype(str).str.zfill(2), freq="M")
    return [float(months.net_R.iloc[i-window+1:i+1].sum()) for i in range(window - 1, len(months))
            if periods[i].ordinal - periods[i-window+1].ordinal == window - 1]


def concentration(values) -> tuple[float, float, float]:
    positive = pd.Series(values, dtype=float)[lambda x: x > 0].sort_values(ascending=False)
    total = float(positive.sum())
    if not total:
        return np.nan, np.nan, 0.0
    return float(positive.iloc[0] / total), float(positive.head(3).sum() / total), float(positive.head(3).sum())


def rank_candidates(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[frame.all_annual_gates_pass].sort_values(ORDER + ["configuration_id"], ascending=ASCENDING, kind="mergesort")


def first_differentiating_criterion(left: pd.Series, right: pd.Series) -> str:
    return next((field for field in ORDER if not np.isclose(float(left[field]), float(right[field]), equal_nan=True)), "FULL_TIE")


def pf(values) -> float:
    values = pd.Series(values, dtype=float)
    losses = -values[values < 0].sum()
    return float(values[values > 0].sum() / losses) if losses else np.nan


def close(left, right) -> bool:
    return bool(np.allclose(pd.to_numeric(left), pd.to_numeric(right), equal_nan=True, rtol=1e-9, atol=1e-9))


def compare(actual: pd.DataFrame, expected: pd.DataFrame, keys: list[str], fields: list[str]) -> bool:
    joined = actual.merge(expected[keys + fields], on=keys, suffixes=("_audit", "_artifact"), how="outer", indicator=True)
    if len(joined) != len(actual) or set(joined._merge) != {"both"}:
        return False
    return all(close(joined[f"{field}_audit"], joined[f"{field}_artifact"]) for field in fields)


def availability() -> dict[tuple[str, str], tuple[pd.Period, pd.Period]]:
    source = pd.read_csv(HERE.parent / "stage5_structural_validation/canonical_lifecycle_registry.csv", keep_default_na=False)
    source = source[(source.generation == "v3_perpetual") & (source.strategy == "T3") &
                    (source.timeframe == "H1") & source.instrument.isin(("USDRUBF", "CNYRUBF", "GLDRUBF", "IMOEXF"))]
    return {key: (pd.to_datetime(group.start_timestamp, utc=True).min().tz_localize(None).to_period("M"),
                  pd.to_datetime(group.end_timestamp, utc=True).max().tz_localize(None).to_period("M"))
            for key, group in source.groupby(["lifecycle", "instrument"])}


def protected_evidence_ok() -> bool:
    manifest_path = HERE.parent / "stage6_fixed_basket_reassessment/trail1_authoritative_ledger_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    hashes = manifest.get("protected_stage5_and_stage6_1_to_6_5_hashes", {})
    protected_root = HERE.parent
    return bool(hashes) and all((protected_root / rel).is_file() and sha(protected_root / rel) == digest for rel, digest in hashes.items())


def main(directory: Path = HERE) -> None:
    checks: dict[str, bool] = {}
    exists, ancestor = validate_starting_sha(ROOT, STARTING_MAIN_SHA)
    checks["provenance_starting_sha_valid"] = exists
    checks["starting_sha_is_ancestor"] = ancestor

    src = pd.read_csv(directory / "variant_source_registry.csv", keep_default_na=False)
    checks["T3_sha_exact"] = len(src) == 5 and set(src.strategy_sha256) == {T3_SHA} and set(src.strategy_identity) == {CANDIDATE}
    checks["parameter_sha_exact"] = set(src.parameter_identity) == {PARAMETER_SHA} and set(src.configuration_identity) == {CONFIG_IDENTITY}
    checks["five_source_sha_exact"] = list(src.variant) == EXPECTED_VARIANTS and all(
        sha(ROOT / row.authoritative_source_path) == EXPECTED_SOURCES[row.variant][0] == row.source_sha256 for row in src.itertuples())
    checks["five_source_trade_counts_exact"] = all(int(row.trade_count) == EXPECTED_SOURCES[row.variant][1] for row in src.itertuples())

    baskets = pd.read_csv(directory / "basket_registry.csv")
    configs = pd.read_csv(directory / "configuration_registry.csv")
    members = pd.read_csv(directory / "configuration_trade_membership.csv")
    checks["exact_11_baskets"] = len(baskets) == 11 and baskets.basket_size.value_counts().to_dict() == {2: 6, 3: 4, 4: 1}
    checks["exact_55_configurations"] = len(configs) == configs.configuration_id.nunique() == 55 and configs.variant.nunique() == 5
    checks["membership_recomputed"] = all(set(members.loc[members.configuration_id == c.configuration_id, "instrument"]) == set(c.instruments.split("+")) for c in configs.itertuples())
    checks["equal_sleeve_scaling_recomputed"] = bool(np.allclose(members.sleeve_weight * members.groupby("configuration_id").instrument.transform("count"), 1.0))

    ledgers = {}
    for row in src.itertuples():
        frame = pd.read_csv(ROOT / row.authoritative_source_path, keep_default_na=False)
        rcol = "net_R_C1" if "net_R_C1" in frame else "strategy_R"
        frame = frame.rename(columns={"trade_id": "source_trade_id", rcol: "strategy_R"})
        ledgers[row.variant] = frame

    avail = availability()
    annual_rows, monthly_rows, iy_rows, im_rows, dd_rows, roll_rows, stable_rows, conc_rows, hierarchy_rows = ([] for _ in range(9))
    for c in configs.itertuples():
        instruments = c.instruments.split("+")
        trades = ledgers[c.variant][ledgers[c.variant].instrument.isin(instruments)].copy()
        trades["portfolio_R"] = trades.strategy_R.astype(float) / c.basket_size
        trades["exit"] = pd.to_datetime(trades.exit_time, utc=True)
        trades = trades.sort_values(["exit", "instrument", "source_trade_id"], kind="mergesort")
        config_months = []
        for life in LIFECYCLES:
            lt = trades[trades.lifecycle == life]
            start = min(avail[(life, instrument)][0] for instrument in instruments)
            end = max(avail[(life, instrument)][1] for instrument in instruments)
            running = 0.0
            for period in pd.period_range(start, end, freq="M"):
                group = lt[(lt.exit.dt.year == period.year) & (lt.exit.dt.month == period.month)]
                net = float(group.portfolio_R.sum()); running += net
                base = {"configuration_id": c.configuration_id, "lifecycle": life, "year": period.year, "month": period.month}
                monthly_rows.append({**base, "trades": len(group), "net_R": net, "PF": pf(group.portfolio_R), "cumulative_R": running})
                config_months.append({**base, "net_R": net})
                for instrument in instruments:
                    ig = group[group.instrument == instrument]
                    im_rows.append({**base, "instrument": instrument, "trades": len(ig), "net_R": float(ig.portfolio_R.sum()), "PF": pf(ig.portfolio_R)})
            lm = pd.DataFrame(config_months); lm = lm[lm.lifecycle == life].sort_values(["year", "month"])
            trade_dd = max_dd(lt.portfolio_R); life_net = float(lt.portfolio_R.sum())
            dd_rows.append({"configuration_id": c.configuration_id, "lifecycle": life, "trade_level_max_DD_R": trade_dd,
                            "monthly_equity_max_DD_R": max_dd(lm.net_R), "net_R": life_net, "recovery_factor": recovery(life_net, trade_dd)})
            for window in (3, 6, 12):
                values = rolling_windows(lm, window)
                roll_rows.append({"configuration_id": c.configuration_id, "lifecycle": life, "window_months": window,
                                  "complete_windows": len(values), "worst_window_R": min(values) if values else np.nan,
                                  "median_window_R": np.median(values) if values else np.nan, "final_window_R": values[-1] if values else np.nan})
            best_share, top3_share, top3_r = concentration(lm.net_R)
            conc_rows.append({"configuration_id": c.configuration_id, "lifecycle": life, "top_3_positive_months_R": top3_r,
                              "best_month_share_of_positive_monthly_R": best_share, "top_3_share_of_positive_monthly_R": top3_share})
            stable_rows.append({"configuration_id": c.configuration_id, "lifecycle": life,
                                "positive_month_share": float((lm.net_R > 0).mean()), "median_monthly_R": float(lm.net_R.median()),
                                "worst_month_R": float(lm.net_R.min()), "best_month_R": float(lm.net_R.max()),
                                "longest_negative_month_streak": negative_streak(lm.net_R)})
        cm = pd.DataFrame(config_months)
        for life, year, label in PERIODS:
            group = trades[(trades.lifecycle == life) & (trades.exit.dt.year == year)]
            months = cm[(cm.lifecycle == life) & (cm.year == year)]
            net, dd = float(group.portfolio_R.sum()), max_dd(group.portfolio_R)
            annual_rows.append({"configuration_id": c.configuration_id, "lifecycle": life, "year": year, "period_label": label,
                                "trades": len(group), "net_R": net, "PF": pf(group.portfolio_R), "expectancy_R": group.portfolio_R.mean(),
                                "max_DD_R": dd, "recovery_factor": recovery(net, dd), "win_rate": (group.portfolio_R > 0).mean(),
                                "median_trade_R": group.portfolio_R.median(), "positive_month_share": (months.net_R > 0).mean(),
                                "median_monthly_R": months.net_R.median()})
            for instrument in instruments:
                ig = group[group.instrument == instrument]
                iy_rows.append({"configuration_id": c.configuration_id, "lifecycle": life, "year": year, "instrument": instrument,
                                "trades": len(ig), "net_R": float(ig.portfolio_R.sum()), "PF": pf(ig.portfolio_R)})

        cy = pd.DataFrame(annual_rows); cy = cy[cy.configuration_id == c.configuration_id]
        cd = pd.DataFrame(dd_rows); cd = cd[cd.configuration_id == c.configuration_id]
        cr = pd.DataFrame(roll_rows); cr = cr[cr.configuration_id == c.configuration_id]
        cs = pd.DataFrame(stable_rows); cs = cs[cs.configuration_id == c.configuration_id]
        cc = pd.DataFrame(conc_rows); cc = cc[cc.configuration_id == c.configuration_id]
        all_months = cm.net_R
        nets = {row.period_label: float(row.net_R) for row in cy.itertuples()}
        flags = {label: nets[label] > 0 for _, _, label in PERIODS}
        hierarchy_rows.append({"configuration_id": c.configuration_id, "basket_id": c.basket_id, "variant": c.variant,
            **{f"{label}_positive": flags[label] for _, _, label in PERIODS}, "all_annual_gates_pass": all(flags.values()),
            "annual_floor_R": min(nets[x] for x in ("BASELINE_2023", "BASELINE_2024", "OOS2025", "OOS2026_YTD")),
            "worst_complete_12M_R": cr[cr.window_months == 12].worst_window_R.min(),
            "worst_complete_6M_R": cr[cr.window_months == 6].worst_window_R.min(),
            "worst_trade_level_DD_R": cd.trade_level_max_DD_R.min(), "minimum_lifecycle_recovery": cd.recovery_factor.min(),
            "positive_month_share": float((all_months > 0).mean()), "median_monthly_R": float(all_months.median()),
            "longest_negative_month_streak": int(cs.longest_negative_month_streak.max()),
            "top_3_concentration": cc.top_3_share_of_positive_monthly_R.max(),
            "chronological_net_R": sum(nets[x] for x in ("BASELINE_2023", "BASELINE_2024", "OOS2025", "OOS2026_YTD"))})

    annual, monthly = pd.DataFrame(annual_rows), pd.DataFrame(monthly_rows)
    iyear, imonth = pd.DataFrame(iy_rows), pd.DataFrame(im_rows)
    dd, rolling = pd.DataFrame(dd_rows), pd.DataFrame(roll_rows)
    stable, conc, hierarchy = pd.DataFrame(stable_rows), pd.DataFrame(conc_rows), pd.DataFrame(hierarchy_rows)
    yearly_art = pd.read_csv(directory / "yearly_metrics.csv")
    monthly_art = pd.read_csv(directory / "monthly_metrics.csv")
    checks["yearly_metrics_recomputed"] = compare(annual, yearly_art, ["configuration_id", "lifecycle", "year"],
        ["trades", "net_R", "PF", "expectancy_R", "max_DD_R", "recovery_factor", "win_rate", "median_trade_R", "positive_month_share", "median_monthly_R"])
    checks["monthly_metrics_recomputed"] = compare(monthly, monthly_art, ["configuration_id", "lifecycle", "year", "month"], ["trades", "net_R", "PF", "cumulative_R"])
    checks["instrument_yearly_recomputed"] = compare(iyear, pd.read_csv(directory / "instrument_yearly_metrics.csv"), ["configuration_id", "lifecycle", "year", "instrument"], ["trades", "net_R", "PF"])
    checks["instrument_monthly_recomputed"] = compare(imonth, pd.read_csv(directory / "instrument_monthly_metrics.csv"), ["configuration_id", "lifecycle", "year", "month", "instrument"], ["trades", "net_R", "PF"])
    dd_ok = compare(dd, pd.read_csv(directory / "drawdown_recovery.csv"), ["configuration_id", "lifecycle"], ["trade_level_max_DD_R", "monthly_equity_max_DD_R", "net_R", "recovery_factor"])
    checks["DD_recomputed"] = dd_ok; checks["recovery_recomputed"] = dd_ok
    roll_art = pd.read_csv(directory / "rolling_stability.csv")
    for window in (3, 6, 12):
        checks[f"rolling_{window}M_recomputed"] = compare(rolling[rolling.window_months == window], roll_art[roll_art.window_months == window],
            ["configuration_id", "lifecycle", "window_months"], ["complete_windows", "worst_window_R", "median_window_R", "final_window_R"])
    stable_ok = compare(stable, pd.read_csv(directory / "monthly_stability.csv"), ["configuration_id", "lifecycle"],
                        ["positive_month_share", "median_monthly_R", "worst_month_R", "best_month_R", "longest_negative_month_streak"])
    checks["positive_month_share_recomputed"] = stable_ok
    checks["median_month_recomputed"] = stable_ok
    checks["negative_streak_recomputed"] = stable_ok
    checks["concentration_recomputed"] = compare(conc, pd.read_csv(directory / "monthly_concentration.csv"), ["configuration_id", "lifecycle"],
        ["top_3_positive_months_R", "best_month_share_of_positive_monthly_R", "top_3_share_of_positive_monthly_R"])

    gate = pd.read_csv(directory / "annual_hard_gates.csv")
    master = pd.read_csv(directory / "master_55_configuration_comparison.csv")
    gate_fields = [f"{label}_positive" for _, _, label in PERIODS] + ["all_annual_gates_pass", *ORDER]
    hierarchy_gate_ok = compare(hierarchy, gate, ["configuration_id"], gate_fields)
    hierarchy_master_ok = compare(hierarchy, master, ["configuration_id"], ORDER)
    checks["all_10_hierarchy_fields_recomputed"] = hierarchy_gate_ok and hierarchy_master_ok
    checks["hard_gates_recomputed"] = hierarchy_gate_ok

    eligible = rank_candidates(hierarchy)
    actual_ranks = master.dropna(subset=["eligible_rank"]).sort_values("eligible_rank")
    checks["all_55_ranks_recomputed"] = list(actual_ranks.configuration_id) == list(eligible.configuration_id)
    leaders = pd.read_csv(directory / "unified_leaders.csv")
    role_map = {row.leader_role: row.configuration_id for row in leaders.itertuples()}
    expected_roles = {}
    for variant, role in (("CANONICAL", "BEST_CANONICAL"), ("TRAIL1", "BEST_TRAIL1"), ("SESSION_10_21", "BEST_SESSION"),
                          ("LOCK1_AFTER_2R", "BEST_LOCK1"), ("STRUCTURAL_STACK_V1", "BEST_STACK")):
        expected_roles[role] = eligible[eligible.variant == variant].iloc[0].configuration_id
    for size in (2, 3, 4):
        expected_roles[f"BEST_N{size}_GLOBAL"] = eligible[eligible.basket_id.str.startswith(f"N{size}_")].iloc[0].configuration_id
    expected_roles["UNIFIED_EQUAL_SLEEVE_REFERENCE_LEADER"] = eligible.iloc[0].configuration_id
    expected_roles["RUNNER_UP"] = eligible.iloc[1].configuration_id
    checks["variant_leaders_recomputed"] = all(role_map.get(k) == v for k, v in expected_roles.items() if k.startswith("BEST_") and "_GLOBAL" not in k)
    checks["size_leaders_recomputed"] = all(role_map.get(k) == v for k, v in expected_roles.items() if "_GLOBAL" in k)
    checks["unified_leader_recomputed"] = role_map.get("UNIFIED_EQUAL_SLEEVE_REFERENCE_LEADER") == expected_roles["UNIFIED_EQUAL_SLEEVE_REFERENCE_LEADER"]
    checks["runner_up_recomputed"] = role_map.get("RUNNER_UP") == expected_roles["RUNNER_UP"]
    criterion = first_differentiating_criterion(eligible.iloc[0], eligible.iloc[1])
    checks["first_differentiating_criterion_recomputed"] = set(leaders.first_differentiating_criterion) == {criterion}

    legacy = pd.read_csv(directory / "legacy_A_F_unified_bridge.csv")
    checks["legacy_A_F_reconciled"] = legacy.reconciliation_status.eq("MATCH").all() and set(legacy.frozen_monthly_source_sha256) == {"e724851fc17ce3f6f71778129ea5cfa4e810d47a0992f00c1974761dde982cb4"}
    checks["protected_evidence_unchanged"] = protected_evidence_ok()
    manifest = json.loads((directory / "audit_manifest.json").read_text())
    checks["deterministic_outputs"] = all(sha(directory / name) == digest for name, digest in manifest["core_artifact_sha256"].items())
    checks["stage7_not_executed"] = manifest.get("stage7_executed") is False and not (ROOT / "TradingSystemLab/results/post_v3_analysis/stage7").exists()

    checks = {key: bool(value) for key, value in checks.items()}
    status = "PASS" if all(checks.values()) else "FAIL"
    result = {"status": status, "checks": checks, "failed_checks": [key for key, value in checks.items() if not value],
              "configuration_count": len(configs), "basket_count": len(baskets), "eligible_count": int(hierarchy.all_annual_gates_pass.sum()),
              "ineligible_count": int((~hierarchy.all_annual_gates_pass).sum()), "hierarchy_fields": ORDER,
              "leader": eligible.iloc[0].configuration_id, "runner_up": eligible.iloc[1].configuration_id,
              "first_differentiating_criterion": criterion, "leaders": expected_roles,
              "strategy_replay_executed": False, "stage7_executed": False}
    (directory / "independent_audit_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    manifest["audit_status"] = status
    (directory / "audit_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    if status != "PASS":
        raise RuntimeError("INDEPENDENT_AUDIT_FAILED: " + ", ".join(result["failed_checks"]))


if __name__ == "__main__":
    main()
