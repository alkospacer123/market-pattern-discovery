"""Strict H4 center-plus-OAT optimization using the audited H4 baseline path.

Only 2023--2024 development data and the normalized H1 C1 cost convention are
available here.  This module deliberately has no ranking, candidate selection,
robustness, walk-forward, or TRUE-OOS interface.
"""

# H4 and M30 share the original H1 bounded-OAT reporting implementation.  Keep
# one implementation and bind its execution/provenance constants to the audited
# H4 baseline, rather than duplicating strategy logic.
from .m30 import *  # noqa: F401,F403
from . import m30 as _common
from ..timeframe_validation import h4_baseline as baseline

_sha = _common._sha
_json = _common._json
_ORIGINAL_METRICS = _common._metrics
def _metrics(configuration_id: str, trades):
    """C1 aggregate plus complete instrument/year/direction diagnostics."""
    row = _ORIGINAL_METRICS(configuration_id, trades)
    scopes = {
        "Si": trades.symbol.eq("Si"), "CNY": trades.symbol.eq("CNY"),
        "2023": pd.to_datetime(trades.exit_time, utc=True).dt.year.eq(2023),
        "2024": pd.to_datetime(trades.exit_time, utc=True).dt.year.eq(2024),
        "LONG": trades.direction.eq("LONG"), "SHORT": trades.direction.eq("SHORT"),
    }
    for label, mask in scopes.items():
        metric = stats(trades.loc[mask, "net_R"].astype(float))
        row.update({f"{label}_PF_C1": metric["PF_R"],
                    f"{label}_expectancy_C1": metric["expectancy"],
                    f"{label}_net_R_C1": metric["net_R"],
                    f"{label}_max_DD_C1": metric["max_DD_R"],
                    f"{label}_recovery_factor_C1": metric["recovery_factor"],
                    f"{label}_win_rate_C1": metric["winrate"]})
    return {name: finite(value) for name, value in row.items()}

PHASE = "H4_OPTIMIZATION"
STATUS = "PHASE_H4_OPTIMIZATION_COMPLETE"
OUTPUT = Path("TradingSystemLab/results/timeframe_optimization/H4")
BASELINE_MANIFEST = Path("TradingSystemLab/results/timeframe_validation/H4/manifest.json")
EXPECTED_METRICS = {
    "T2": {"trades": 19, "PF": 1.7422955759186958, "expectancy_R": .42029394192661923,
           "net_R": 7.985584896605766, "max_drawdown_R": -7.357579556504138},
    "T3": {"trades": 27, "PF": 1.9626820421169813, "expectancy_R": .47692349446242016,
           "net_R": 12.876934350485344, "max_drawdown_R": -4.813504170618327},
}
PHASE_GUARDS = {"winner_selection": False, "robustness": False,
                "walk_forward": False, "true_oos_blocked": True}

# Exclude only this phase's output.  Frozen source files are protected with a
# direct digest because hash_tree intentionally represents directories only.
PROTECTED = _common.PROTECTED + (
    Path("TradingSystemLab/results/timeframe_optimization/M1"),
    Path("TradingSystemLab/results/timeframe_optimization/M5"),
    Path("TradingSystemLab/results/timeframe_optimization/M15"),
    Path("TradingSystemLab/results/timeframe_optimization/M30"),
)
FROZEN_STRATEGY_FILES = tuple(Path(p) for p in (
    "TradingSystemLab/strategies/trend/T2_Trend_Pullback.py",
    "TradingSystemLab/strategies/trend/T3_MTF_Trend.py"))
_ORIGINAL_VALIDATE = _common._validate_prerequisites


def protected_snapshot() -> dict[str, object]:
    snapshot = {str(path): hash_tree(path) for path in PROTECTED}
    snapshot.update({str(path): _sha(path) for path in FROZEN_STRATEGY_FILES})
    return snapshot


def configuration_rows(key: str) -> list[dict[str, Any]]:
    center = baseline.EXPECTED[key]["parameters"]
    return [{"configuration_id": f"{key}-H4-{i:04d}-{stable_hash(cfg)[:12]}",
             "parameter_hash": stable_hash(cfg), "baseline_configuration": cfg == center, **cfg}
            for i, cfg in enumerate(bounded_design(key))]


def _bind() -> None:
    """Bind globals read by inherited functions to this H4 phase."""
    for name in ("baseline", "PHASE", "STATUS", "OUTPUT", "BASELINE_MANIFEST",
                 "EXPECTED_METRICS", "PROTECTED"):
        setattr(_common, name, globals()[name])
    _common.configuration_rows = configuration_rows
    _common._metrics = _metrics


def _validate_h4_prerequisites(data_root: Path):
    manifest = json.loads(BASELINE_MANIFEST.read_text(encoding="utf-8"))
    required = {
        "status": baseline.STATUS, "timeframe": "H4",
        "development_period": DEVELOPMENT_PERIOD, "true_oos_cutoff": TRUE_OOS_CUTOFF,
        "true_oos_blocked": True, "optimization": False, "ranking": False,
        "selection": False, "parameter_change": False, "strategy_change": False,
    }
    if any(manifest.get(name) != value for name, value in required.items()):
        raise RuntimeError("H4_BASELINE_PROVENANCE_MISMATCH")
    # The audited baseline tree must still equal the canonical merged commit.
    import subprocess
    changed = subprocess.run(
        ["git", "diff", "--quiet", "9133c0f9ad8eddff82ea5b3af0e9532594dec20a", "--", str(baseline.OUTPUT)],
        check=False).returncode
    if changed:
        raise RuntimeError("H4_BASELINE_COMMIT_PARITY_MISMATCH")
    verify_frozen_strategies()
    candidates = baseline.frozen_candidates()
    for key in ("T2", "T3"):
        recorded, expected = manifest["candidates"][key], baseline.EXPECTED[key]
        if (recorded["phase32_configuration_id"] != expected["phase32_configuration_id"] or
                recorded["parameter_hash"] != expected["parameter_hash"] or
                recorded["strategy_hash"] != STRATEGY_SHA256[key]):
            raise RuntimeError(f"{key}_BASELINE_IDENTITY_MISMATCH")
    loaded = {alias: baseline.load_h1_development(data_root, alias) for _, alias in baseline.INSTRUMENTS}
    if any(frame is None for frame, _ in loaded.values()):
        raise RuntimeError("DATA_UNAVAILABLE")
    actual_sources = []
    for instrument, alias in baseline.INSTRUMENTS:
        actual_sources.extend({"instrument": instrument, "alias": alias, "name": p.name, "sha256": _sha(p)}
                              for p in loaded[alias][1])
    if actual_sources != manifest["source_files"]:
        raise RuntimeError("H4_SOURCE_HASH_MISMATCH")
    return manifest, {alias: item[0] for alias, item in loaded.items()}


def run(data_root: Path = APPROVED_DATA_ROOT, output: Path = OUTPUT) -> dict[str, Any]:
    _bind()
    _common._validate_prerequisites = _validate_h4_prerequisites
    before = protected_snapshot()
    result = _common.run(data_root, output)
    after = protected_snapshot()
    if before != after:
        raise RuntimeError("PROTECTED_RESEARCH_ARTIFACT_MUTATION")

    target = Path(output)
    manifest_path = target / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    # Complete the H4-specific provenance vocabulary required by the phase.
    manifest.update({
        "methodological_source": "original H1 bounded OAT methodology",
        "parameter_spaces": SPACES,
        "cost_model": "H1_C1", "cost_scenarios": ["C1"],
        "ticks_per_side": 1, "round_trip_ticks": 2, "additional_slippage_ticks": 0,
        "optimization": True, "selection": False,
        "protected_artifact_hashes": after,
    })
    # Rename inherited M30 provenance keys without retaining misleading aliases.
    manifest["h4_baseline_manifest_sha256"] = manifest.pop("m30_baseline_manifest_hash")
    manifest["h4_baseline_trade_ledger_sha256"] = manifest.pop("m30_baseline_trade_ledger_hashes")
    _json(manifest_path, manifest)
    report = target / "m30_optimization_report.md"
    report.rename(target / "h4_optimization_report.md")
    text = (target / "h4_optimization_report.md").read_text(encoding="utf-8")
    (target / "h4_optimization_report.md").write_text(
        text.replace("M30", "H4").replace("actual H4 data", "causal H4 execution data"), encoding="utf-8")
    for key in ("T2", "T3"):
        for name in ("experiment.json", "final_report.md", "best_regions.md"):
            path = target / key / name
            path.write_text(path.read_text(encoding="utf-8").replace("M30", "H4"), encoding="utf-8")
    return result
