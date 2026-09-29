"""Independent fail-closed auditor for normalized Stage 6.6 evidence."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
EXPECTED_VARIANTS = ["CANONICAL", "TRAIL1", "SESSION_10_21", "LOCK1_AFTER_2R", "STRUCTURAL_STACK_V1"]
ORDER = ["annual_floor_R", "worst_complete_12M_R", "worst_complete_6M_R", "worst_trade_level_DD_R",
         "minimum_lifecycle_recovery", "positive_month_share", "median_monthly_R", "longest_negative_month_streak",
         "top_3_concentration", "chronological_net_R"]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def close(left, right) -> bool:
    return bool(np.allclose(pd.to_numeric(left), pd.to_numeric(right), equal_nan=True, rtol=1e-9, atol=1e-9))


def main(directory: Path = HERE) -> None:
    checks = {}
    src = pd.read_csv(directory / "variant_source_registry.csv", keep_default_na=False)
    checks["exact_authenticated_five_sources"] = list(src.variant) == EXPECTED_VARIANTS and set(src.source_status) == {"AUTHENTICATED"}
    checks["source_ledgers_unchanged"] = all(sha(ROOT / r.authoritative_source_path) == r.source_sha256 for r in src.itertuples())
    trail = src[src.variant == "TRAIL1"].iloc[0]
    checks["trail1_authoritative_418"] = int(trail.trade_count) == 418 and trail.source_sha256 == "0f9034edf228a687da67e9f3e35fad01f2339be162c558e6d802c3cd77eea8ad"
    baskets = pd.read_csv(directory / "basket_registry.csv")
    configs = pd.read_csv(directory / "configuration_registry.csv")
    members = pd.read_csv(directory / "configuration_trade_membership.csv")
    registry = pd.read_csv(directory / "portfolio_trade_scaling_registry.csv", keep_default_na=False)
    checks["exact_11_baskets"] = len(baskets) == 11 and baskets.basket_size.value_counts().to_dict() == {2: 6, 3: 4, 4: 1}
    checks["exact_55_configurations"] = len(configs) == 55 and configs.configuration_id.nunique() == 55
    checks["normalized_trade_registry"] = len(registry) == sum(src.trade_count.astype(int)) and not registry.duplicated(["variant", "source_trade_id", "lifecycle", "fold_id"]).any()
    checks["membership_cardinality"] = len(members) == int(configs.basket_size.sum())
    # Independently load each source ledger and authenticate every normalized row.
    authoritative = []
    for r in src.itertuples():
        f = pd.read_csv(ROOT / r.authoritative_source_path, keep_default_na=False)
        col = "net_R_C1" if "net_R_C1" in f else "strategy_R"
        authoritative.append(pd.DataFrame({"variant": r.variant, "source_trade_id": f.trade_id,
                                           "lifecycle": f.lifecycle, "fold_id": f.fold_id,
                                           "instrument": f.instrument, "direction": f.direction,
                                           "entry_time": f.entry_time, "exit_time": f.exit_time,
                                           "strategy_R": f[col].astype(float)}))
    auth = pd.concat(authoritative, ignore_index=True)
    keys = ["variant", "source_trade_id", "lifecycle", "fold_id", "instrument", "direction", "entry_time", "exit_time"]
    merged = auth.merge(registry, on=keys, suffixes=("_source", "_registry"), how="outer", indicator=True)
    checks["normalized_rows_authentic"] = set(merged._merge) == {"both"} and close(merged.strategy_R_source, merged.strategy_R_registry)
    yearly = pd.read_csv(directory / "yearly_metrics.csv")
    monthly = pd.read_csv(directory / "monthly_metrics.csv")
    iyear = pd.read_csv(directory / "instrument_yearly_metrics.csv")
    imonth = pd.read_csv(directory / "instrument_monthly_metrics.csv")
    year_rows, month_rows, iy_rows, im_rows = [], [], [], []
    for c in configs.itertuples():
        cm = members[members.configuration_id == c.configuration_id]
        t = auth[(auth.variant == c.variant) & auth.instrument.isin(cm.instrument)].copy()
        weight = dict(zip(cm.instrument, cm.sleeve_weight)); t["portfolio_R"] = t.apply(lambda x: x.strategy_R * weight[x.instrument], axis=1)
        t["exit"] = pd.to_datetime(t.exit_time, utc=True)
        t = t.sort_values(["exit", "instrument", "source_trade_id"], kind="mergesort")
        expected_months = monthly[monthly.configuration_id == c.configuration_id]
        for m in expected_months.itertuples():
            g = t[(t.lifecycle == m.lifecycle) & (t.exit.dt.year == m.year) & (t.exit.dt.month == m.month)]
            month_rows.append((m.configuration_id, m.lifecycle, m.year, m.month, float(g.portfolio_R.sum()), len(g)))
            for s in cm.instrument:
                sg = g[g.instrument == s]; im_rows.append((m.configuration_id, m.lifecycle, m.year, m.month, s, float(sg.portfolio_R.sum()), len(sg)))
        for y in yearly[yearly.configuration_id == c.configuration_id].itertuples():
            g = t[(t.lifecycle == y.lifecycle) & (t.exit.dt.year == y.year)]
            year_rows.append((y.configuration_id, y.lifecycle, y.year, float(g.portfolio_R.sum()), len(g)))
            for s in cm.instrument:
                sg = g[g.instrument == s]; iy_rows.append((y.configuration_id, y.lifecycle, y.year, s, float(sg.portfolio_R.sum()), len(sg)))
    ay = pd.DataFrame(year_rows, columns=["configuration_id","lifecycle","year","net_R","trades"])
    am = pd.DataFrame(month_rows, columns=["configuration_id","lifecycle","year","month","net_R","trades"])
    aiy = pd.DataFrame(iy_rows, columns=["configuration_id","lifecycle","year","instrument","net_R","trades"])
    aim = pd.DataFrame(im_rows, columns=["configuration_id","lifecycle","year","month","instrument","net_R","trades"])
    def verify(actual, expected, keys):
        x = actual.merge(expected[keys+["net_R","trades"]], on=keys, suffixes=("_audit","_artifact"), how="outer", indicator=True)
        return set(x._merge) == {"both"} and close(x.net_R_audit, x.net_R_artifact) and (x.trades_audit == x.trades_artifact).all()
    checks["yearly_reconstructed"] = verify(ay, yearly, ["configuration_id","lifecycle","year"])
    checks["monthly_reconstructed"] = verify(am, monthly, ["configuration_id","lifecycle","year","month"])
    checks["instrument_yearly_reconstructed"] = verify(aiy, iyear, ["configuration_id","lifecycle","year","instrument"])
    checks["instrument_monthly_reconstructed"] = verify(aim, imonth, ["configuration_id","lifecycle","year","month","instrument"])
    checks["all_months_present"] = len(monthly) > 55 * 12 and len(imonth) == sum(len(members[members.configuration_id == c]) * len(monthly[monthly.configuration_id == c]) for c in configs.configuration_id)
    gate = pd.read_csv(directory / "annual_hard_gates.csv")
    master = pd.read_csv(directory / "master_55_configuration_comparison.csv")
    leaders = pd.read_csv(directory / "unified_leaders.csv")
    eligible = gate[gate.all_annual_gates_pass].sort_values(ORDER+["configuration_id"], ascending=[False]*7+[True,True,False,True], kind="mergesort")
    checks["hard_gates_recomputed"] = all(bool((yearly[(yearly.configuration_id == r.configuration_id) & yearly.period_label.isin(["BASELINE_2023","BASELINE_2024","WF24","OOS2025","OOS2026_YTD"])].net_R > 0).all()) == r.all_annual_gates_pass for r in gate.itertuples())
    checks["hierarchy_and_leaders_recomputed"] = len(eligible) >= 2 and leaders[leaders.leader_role == "UNIFIED_EQUAL_SLEEVE_REFERENCE_LEADER"].iloc[0].configuration_id == eligible.iloc[0].configuration_id and leaders[leaders.leader_role == "RUNNER_UP"].iloc[0].configuration_id == eligible.iloc[1].configuration_id
    legacy = pd.read_csv(directory / "legacy_A_F_unified_bridge.csv")
    checks["legacy_source_unchanged"] = legacy.reconciliation_status.eq("MATCH").all() and all(legacy.frozen_monthly_source_sha256 == sha(ROOT / legacy.iloc[0].frozen_monthly_source_path))
    manifest = json.loads((directory / "audit_manifest.json").read_text())
    checks["deterministic_manifest_hashes"] = all(sha(directory / p) == h for p, h in manifest["core_artifact_sha256"].items())
    checks["no_denormalized_ledger"] = not (directory / "portfolio_scaled_trades.csv").exists()
    checks = {key: bool(value) for key, value in checks.items()}
    status = "PASS" if all(checks.values()) else "FAIL"
    result = {"status": status, "checks": checks, "failed_checks": [k for k,v in checks.items() if not v],
              "strategy_replay_executed": False, "stage7_executed": False,
              "configuration_count": len(configs), "basket_count": len(baskets), "eligible_count": int(gate.all_annual_gates_pass.sum())}
    (directory / "independent_audit_result.json").write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    manifest["audit_status"] = status
    (directory / "audit_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True)+"\n")
    if status != "PASS": raise RuntimeError("INDEPENDENT_AUDIT_FAILED: " + ", ".join(result["failed_checks"]))


if __name__ == "__main__":
    main()
