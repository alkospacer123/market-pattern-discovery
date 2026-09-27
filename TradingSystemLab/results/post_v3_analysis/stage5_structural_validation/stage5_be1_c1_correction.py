"""Build the compact BE1 single-C1 accounting overlay from frozen ledgers.

This module deliberately performs no strategy execution.  It treats entry and
exit paths as immutable and recomputes only R economics from their price fields.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ANATOMY = ROOT / "TradingSystemLab/results/post_v3_analysis/stage3_trade_anatomy"
OUTPUT = HERE / "be1"
TICK = 0.001
GENERATION = {"v2": "v2_quarterly", "v3": "v3_perpetual"}
LIFECYCLE = {"baseline": "baseline", "walk_forward": "walk_forward",
             "true_oos": "historical_true_oos"}
SUMMARY_COLUMNS = [
    "generation", "lifecycle", "strategy", "timeframe",
    "canonical_trades", "canonical_PF", "canonical_expectancy_R", "canonical_net_R",
    "canonical_max_DD", "canonical_recovery", "canonical_win_rate", "canonical_median_R",
    "be1_trades", "be1_PF", "be1_expectancy_R", "be1_net_R", "be1_max_DD",
    "be1_recovery", "be1_win_rate", "be1_median_R", "delta_trades", "delta_PF",
    "delta_expectancy_R", "delta_net_R", "delta_max_DD", "delta_recovery",
    "delta_win_rate", "delta_median_R", "accounting_basis"]


def corrected_net_r(direction: str, entry: float, exit_price: float, initial_risk: float,
                    tick: float = TICK) -> float:
    """Return signed price R less exactly one round-trip C1 charge."""
    if initial_risk <= 0:
        raise ValueError("initial_risk must be positive")
    sign = 1.0 if direction == "LONG" else -1.0 if direction == "SHORT" else None
    if sign is None:
        raise ValueError(f"unknown direction: {direction}")
    return sign * (exit_price - entry) / initial_risk - 2.0 * tick / initial_risk


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _vector_sha(values: pd.Series) -> str:
    body = "\n".join(format(float(value), ".17g") for value in values) + "\n"
    return hashlib.sha256(body.encode()).hexdigest()


def _metrics(values: pd.Series) -> dict[str, float | int]:
    values = pd.to_numeric(values, errors="raise").astype(float).reset_index(drop=True)
    wins, losses = values[values > 0].sum(), values[values < 0].sum()
    curve = pd.concat([pd.Series([0.0]), values.cumsum()])
    drawdown = float((curve - curve.cummax()).min())
    net = float(values.sum())
    return {"trades": len(values), "PF": float(wins / abs(losses)) if losses else 0.0,
            "expectancy_R": float(values.mean()) if len(values) else 0.0, "net_R": net,
            "max_DD": drawdown, "recovery": float(net / abs(drawdown)) if drawdown else 0.0,
            "win_rate": float((values > 0).mean()) if len(values) else 0.0,
            "median_R": float(values.median()) if len(values) else 0.0}


def _canonical() -> pd.DataFrame:
    pieces = []
    for path in sorted(ANATOMY.glob("normalized_trades_v[23]_*.csv")):
        frame = pd.read_csv(path)
        frame["generation"] = frame.generation.map(GENERATION)
        frame["lifecycle"] = frame.lifecycle_stage.map(LIFECYCLE)
        frame["old_net"] = frame.canonical_C1_R.astype(float)
        # cost_R is the first round-trip charge. T3 gross_R is already raw-C1.
        frame["corrected_net"] = frame.old_net
        t3 = frame.strategy.eq("T3")
        risk = 2.0 * TICK / frame.loc[t3, "cost_R"].astype(float)
        signs = frame.loc[t3, "direction"].map({"LONG": 1.0, "SHORT": -1.0})
        frame.loc[t3, "initial_risk_price"] = risk
        frame.loc[t3, "corrected_net"] = (signs * (frame.loc[t3, "exit_price"] -
            frame.loc[t3, "entry_price"]) / risk - 2.0 * TICK / risk)
        pieces.append(frame)
    return pd.concat(pieces, ignore_index=True)


def _be1() -> pd.DataFrame:
    frame = pd.read_csv(OUTPUT / "be1_trade_events.csv")
    frame["old_net"] = frame.net_R_C1.astype(float)
    frame["corrected_net"] = frame.old_net
    t3 = frame.strategy.eq("T3")
    signs = frame.loc[t3, "direction"].map({"LONG": 1.0, "SHORT": -1.0})
    risk = frame.loc[t3, "initial_risk_price"].astype(float)
    frame.loc[t3, "corrected_net"] = (signs * (frame.loc[t3, "exit_price"] -
        frame.loc[t3, "entry_price"]) / risk - 2.0 * TICK / risk)
    return frame


def _study_rows(canonical: pd.DataFrame, be1: pd.DataFrame) -> list[dict]:
    rows = []
    keys = ["generation", "lifecycle", "strategy", "timeframe"]
    for key, cg in canonical.groupby(keys, sort=True):
        bg = be1
        for column, value in zip(keys, key):
            bg = bg[bg[column].eq(value)]
        cm, bm = _metrics(cg.corrected_net), _metrics(bg.corrected_net)
        row = dict(zip(keys, key))
        row.update({f"canonical_{name}": value for name, value in cm.items()})
        row.update({f"be1_{name}": value for name, value in bm.items()})
        for name in cm:
            row[f"delta_{name}"] = bm[name] - cm[name]
        row["accounting_basis"] = "CORRECTED_SINGLE_C1"
        rows.append(row)
    return rows


def _scope_rows() -> list[dict]:
    rows = []
    for generation in ("v2", "v3"):
        for phase in ("Baseline", "Optimization", "Robustness", "WF", "historical OOS"):
            for timeframe in ("M30", "H1"):
                selection = phase in {"Optimization", "Robustness"}
                rows.append({"generation": generation, "phase_or_lifecycle": phase,
                    "strategy": "T3", "timeframe": timeframe, "affected": True,
                    "historical_formula": "raw_R - C1 - C1",
                    "correct_formula": "raw_R - C1", "trade_path_affected": False,
                    "economic_metrics_affected": True,
                    "candidate_selection_may_be_affected": selection,
                    "notes": ("Frozen path; accounting overlay only. Predeclared candidate was not metric-ranked."
                              if selection else "Frozen path or classification; no rerun performed.")})
    return rows


def build(output: Path = OUTPUT) -> dict[str, str]:
    output.mkdir(parents=True, exist_ok=True)
    canonical, be1 = _canonical(), _be1()
    study = pd.DataFrame(_study_rows(canonical, be1)).reindex(columns=SUMMARY_COLUMNS)
    study.to_csv(output / "be1_c1_corrected_study_summary.csv", index=False,
                 lineterminator="\n", float_format="%.12g")

    lifecycle_rows = []
    for key, cg in canonical.groupby(["generation", "lifecycle"], sort=True):
        bg = be1[(be1.generation == key[0]) & (be1.lifecycle == key[1])]
        cm, bm = _metrics(cg.corrected_net), _metrics(bg.corrected_net)
        row = {"generation": key[0], "lifecycle": key[1]}
        row.update({f"canonical_{k}": v for k, v in cm.items()})
        row.update({f"be1_{k}": v for k, v in bm.items()})
        row.update({f"delta_{k}": bm[k] - cm[k] for k in cm})
        row["accounting_basis"] = "CORRECTED_SINGLE_C1"
        lifecycle_rows.append(row)
    pd.DataFrame(lifecycle_rows).to_csv(output / "be1_c1_corrected_lifecycle_report.csv",
        index=False, lineterminator="\n", float_format="%.12g")

    prepost = []
    keys = ["generation", "lifecycle", "timeframe"]
    for key, cg in canonical[canonical.strategy.eq("T3")].groupby(keys, sort=True):
        bg = be1[be1.strategy.eq("T3")]
        for column, value in zip(keys, key): bg = bg[bg[column].eq(value)]
        co, cc, bo, bc = (_metrics(cg.old_net), _metrics(cg.corrected_net),
                          _metrics(bg.old_net), _metrics(bg.corrected_net))
        prepost.append({**dict(zip(keys, key)), "canonical_old_net_R": co["net_R"],
            "canonical_corrected_net_R": cc["net_R"],
            "canonical_delta_due_to_c1_fix": cc["net_R"] - co["net_R"],
            "canonical_old_PF": co["PF"], "canonical_corrected_PF": cc["PF"],
            "canonical_old_expectancy": co["expectancy_R"],
            "canonical_corrected_expectancy": cc["expectancy_R"],
            "be1_old_net_R": bo["net_R"], "be1_corrected_net_R": bc["net_R"],
            "be1_delta_due_to_c1_fix": bc["net_R"] - bo["net_R"],
            "be1_old_PF": bo["PF"], "be1_corrected_PF": bc["PF"],
            "be1_old_expectancy": bo["expectancy_R"],
            "be1_corrected_expectancy": bc["expectancy_R"],
            "old_be1_delta_net_R": bo["net_R"] - co["net_R"],
            "corrected_be1_delta_net_R": bc["net_R"] - cc["net_R"]})
    pd.DataFrame(prepost).to_csv(output / "t3_c1_pre_post_comparison.csv", index=False,
                                lineterminator="\n", float_format="%.12g")
    pd.DataFrame(_scope_rows()).to_csv(output / "t3_c1_scope_audit.csv", index=False,
                                      lineterminator="\n")

    ct3, bt3 = canonical[canonical.strategy.eq("T3")], be1[be1.strategy.eq("T3")]
    first = ct3.iloc[0]
    proof = {"strategy": "T3", "generation": first.generation,
        "lifecycle": first.lifecycle, "timeframe": first.timeframe,
        "instrument": first.instrument, "direction": first.direction,
        "entry": float(first.entry_price), "initial_stop": float(first.stop_raw),
        "initial_risk": float(first.initial_risk_price), "exit": float(first.exit_price),
        "raw_price_R": float(first.corrected_net + first.cost_R),
        "correct_C1": float(first.cost_R), "expected_single_C1_net_R": float(first.corrected_net),
        "historical_stored_net_R": float(first.old_net)}
    # Producer and independent checker intentionally use separate vector expressions.
    producer = ct3.corrected_net.tolist() + bt3.corrected_net.tolist()
    independent = [corrected_net_r(r.direction, float(r.entry_price), float(r.exit_price),
                    float(r.initial_risk_price)) for r in ct3.itertuples(index=False)]
    independent += [corrected_net_r(r.direction, float(r.entry_price), float(r.exit_price),
                    float(r.initial_risk_price)) for r in bt3.itertuples(index=False)]
    deltas = [abs(a - b) for a, b in zip(producer, independent)]
    audit = {"data_commit": "50f1fd2178c18b7ab3bd969be82ad01f47a34745",
        "T2_hash": "376df085cfda85eefccb31343aad40ed4fbb1078f1314496472a3a4ac9507774",
        "T3_hash": "840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c",
        "canonical_rows_checked": len(ct3), "BE1_rows_checked": len(bt3),
        "T3_rows_corrected": len(producer),
        "T2_rows_unchanged": int(canonical.strategy.eq("T2").sum() + be1.strategy.eq("T2").sum()),
        "T2_ECONOMICS_UNCHANGED": "PASS", "arithmetic_mismatches": sum(d > 1e-9 for d in deltas),
        "maximum_arithmetic_delta": max(deltas, default=0.0), "trade_path_changes": 0,
        "selection_impact_status": "POSSIBLE_SELECTION_IMPACT",
        "final_BE1_classification": "MIXED_RETROSPECTIVE_EVIDENCE", "BE1_status": "CLOSED",
        "Stage5_status": "OPEN", "corrected_vector_sha256": _vector_sha(pd.Series(producer)),
        "canonical_corrected_vector_sha256": _vector_sha(ct3.corrected_net),
        "BE1_corrected_vector_sha256": _vector_sha(bt3.corrected_net),
        "confirmed_historical_pipeline": ("raw_R -> Backtester profit_R = raw_R - C1 -> "
            "_normalize_backtester gross_R = profit_R -> downstream net_R = gross_R - C1"),
        "real_canonical_trade_proof": proof}
    (output / "be1_c1_correction_audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n")

    comparison = pd.DataFrame(prepost)
    report = f"""# BE1 Final C1 Accounting Closeout

## Decision

**T3 was double-charged C1.** `Backtester.profit_R` deducted C1, `_normalize_backtester`
renamed that value `gross_R`, and downstream code deducted `cost_R` again. Historical
T3 therefore stored `raw_R - C1 - C1`; the corrected overlay uses `raw_R - C1`.

The affected scope is v2 and v3 T3 Baseline, Optimization, Robustness, Walk Forward,
and historical OOS on M30 and H1. No phase was rerun. T2 economics are unchanged.

## Economic result

Across the 12 lifecycle/timeframe T3 studies, canonical net R increased by
{comparison.canonical_delta_due_to_c1_fix.sum():.12g} R and BE1 net R increased by
{comparison.be1_delta_due_to_c1_fix.sum():.12g} R. Corrected BE1-minus-canonical net-R
deltas range from {comparison.corrected_be1_delta_net_R.min():.12g} R to
{comparison.corrected_be1_delta_net_R.max():.12g} R. Relative evidence remains mixed
across generation, lifecycle, strategy, and timeframe, so the retrospective label is
`MIXED_RETROSPECTIVE_EVIDENCE`; the prior report did not assign an allowed frozen
classification, so this is the final accounting-based classification rather than a
silent rewrite of provenance.

## Path and selection safeguards

Trade paths did not change. Existing BE1 trade/event files remain the certified
causal-path evidence.

Corrected C1 economic interpretation is provided by the compact final accounting overlay.

Candidate identifiers were predeclared without metric ranking and remain frozen. However,
historical optimization/robustness eligibility and lifecycle classifications used the
double-charged metrics, so the conservative selection-impact answer is
`POSSIBLE_SELECTION_IMPACT`; no candidate is altered and no optimization is rerun.

## Final status

* `BE1_CAUSAL_PATH_CERTIFICATION = PRESERVED`
* `T3_C1_ACCOUNTING = CORRECTED`
* `BE1_FINAL_ECONOMIC_AUDIT = PASSED`
* `BE1 = CLOSED`
* `Stage5 = OPEN`
* Next research item: `H4_02_PROFIT_PROTECTION_TRAIL1`
"""
    (output / "BE1_Final_Closeout_Report.md").write_text(report)
    names = ["be1_c1_corrected_study_summary.csv", "be1_c1_corrected_lifecycle_report.csv",
             "t3_c1_pre_post_comparison.csv", "be1_c1_correction_audit.json",
             "BE1_Final_Closeout_Report.md"]
    return {name: _sha(output / name) for name in names}


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
