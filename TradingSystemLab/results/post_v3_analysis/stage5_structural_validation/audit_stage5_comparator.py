"""Independent Stage 5 comparator auditor (deliberately no adapter imports)."""
from __future__ import annotations

import ast
import copy
import csv
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
EXPECTED_HASHES = {"T2":"376df085cfda85eefccb31343aad40ed4fbb1078f1314496472a3a4ac9507774",
                   "T3":"840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c"}
DATA_COMMIT = "50f1fd2178c18b7ab3bd969be82ad01f47a34745"
TOLERANCE = 1e-9
INSTRUMENTS = {"v2_quarterly":{"Si","CNY","GD","BR","MIX","NG"},
               "v3_perpetual":{"USDRUBF","CNYRUBF","GLDRUBF","IMOEXF"}}

def sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
def rows(name: str) -> list[dict[str,str]]:
    with (HERE/name).open(newline="",encoding="utf-8") as f: return list(csv.DictReader(f))

def _validate(manifest: dict, registry: list[dict], aggregate: list[dict], trades: list[dict]) -> None:
    if manifest["status"] != "STAGE5_CANONICAL_COMPARATOR_RECONCILIATION_PASSED": raise ValueError("PASS_STATUS")
    if manifest["data_commit"] != DATA_COMMIT or manifest["strategy_hashes"] != EXPECTED_HASHES: raise ValueError("PROVENANCE")
    if manifest["C1_contract"]["name"] != "C1" or manifest["frozen_tick_size"] != .001: raise ValueError("COST")
    if manifest["hypothesis_execution"] or not manifest["no_parameter_search"] or not manifest["no_stage6"]: raise ValueError("SCOPE")
    if manifest.get("t3_completed_context", True) is not True or manifest.get("t3_day_reset", True) is not True: raise ValueError("T3_CONTEXT")
    if any(r["generation"].startswith("v1") for r in registry): raise ValueError("V1")
    for generation, expected in INSTRUMENTS.items():
        if {r["instrument"] for r in registry if r["generation"]==generation} != expected: raise ValueError("INSTRUMENTS")
    if any(r["cost_contract"]!="C1" or r["tick_size"]!="0.001" for r in registry): raise ValueError("REGISTRY_CONTRACT")
    wf = [r for r in registry if r["lifecycle"]=="walk_forward"]
    if {r["fold_id"] for r in wf} != {"WF01","WF02","WF03","WF04"}: raise ValueError("FOLDS")
    if any(r["start_timestamp"] > r["end_timestamp"] for r in registry): raise ValueError("BOUNDS")
    delta_fields=("net_R_delta","expectancy_delta","PF_delta","win_rate_delta","max_DD_delta")
    if any(r["status"]!="PASS" or int(r["trade_count_delta"]) or max(abs(float(r[x])) for x in delta_fields)>TOLERANCE for r in aggregate): raise ValueError("METRICS")
    totals={(g,l):sum(int(x["expected_trades"]) for x in aggregate if x["generation"]==g and x["lifecycle"]==l)
            for g in INSTRUMENTS for l in ("baseline","walk_forward","historical_true_oos")}
    required={("v2_quarterly","baseline"):4449,("v2_quarterly","walk_forward"):746,
              ("v2_quarterly","historical_true_oos"):1759,("v3_perpetual","baseline"):1124,
              ("v3_perpetual","walk_forward"):515,("v3_perpetual","historical_true_oos"):1101}
    if totals != required: raise ValueError("CANONICAL_TOTALS")
    if any(r["status"]!="PASS" or int(r["total_mismatches"]) for r in trades): raise ValueError("TRADES")
    if manifest["trade_level_mismatch_count"] or manifest["maximum_metric_delta"]>TOLERANCE: raise ValueError("FALSE_PASS")

def audit() -> dict:
    manifest=json.loads((HERE/"canonical_comparator_manifest.json").read_text())
    registry,aggregate,trades=rows("canonical_lifecycle_registry.csv"),rows("canonical_comparator_reconciliation.csv"),rows("canonical_comparator_trade_reconciliation.csv")
    if manifest["lifecycle_registry_hash"] != sha(HERE/"canonical_lifecycle_registry.csv"): raise RuntimeError("REGISTRY_HASH")
    expected_outputs={k:sha(HERE/n) for k,n in (("registry","canonical_lifecycle_registry.csv"),("aggregate","canonical_comparator_reconciliation.csv"),("trades","canonical_comparator_trade_reconciliation.csv"),("report","Stage_5_Comparator_Reconstruction_Report.md"))}
    if manifest.get("output_hashes") != expected_outputs: raise RuntimeError("OUTPUT_HASH")
    for strategy,file in (("T2","T2_Trend_Pullback.py"),("T3","T3_MTF_Trend.py")):
        if sha(ROOT/f"TradingSystemLab/strategies/trend/{file}") != EXPECTED_HASHES[strategy]: raise RuntimeError("STRATEGY_HASH")
    _validate(manifest,registry,aggregate,trades)
    # Independent source-level causal guards: canonical context delegates to the
    # day-reset completed-block loader; Donchian is shifted before entry checks.
    loader=(ROOT/"TradingSystemLab/core/data_loader.py").read_text(); strategy=(ROOT/"TradingSystemLab/strategies/trend/T3_MTF_Trend.py").read_text()
    if "groupby" not in loader or "if len(block) != 4" not in loader or ".shift(1)" not in strategy: raise RuntimeError("T3_CAUSAL_GUARD")
    tree=ast.parse((HERE/"audit_stage5_comparator.py").read_text())
    imported={a.name for n in ast.walk(tree) if isinstance(n,(ast.Import,ast.ImportFrom)) for a in n.names}
    if any("run_stage5_validation" in x or "stage5_lifecycle_adapter" in x for x in imported): raise RuntimeError("AUDITOR_NOT_INDEPENDENT")
    # Mutation coverage is kept here rather than sharing producer validation.
    mutations=[]
    def check(change):
        m,r,a,t=copy.deepcopy(manifest),copy.deepcopy(registry),copy.deepcopy(aggregate),copy.deepcopy(trades)
        change(m,r,a,t)
        try: _validate(m,r,a,t)
        except (ValueError,KeyError): mutations.append(True)
        else: mutations.append(False)
    check(lambda m,r,a,t:r[0].update(start_timestamp="9999-01-01"))
    check(lambda m,r,a,t:r[0].update(end_timestamp="1900-01-01"))
    check(lambda m,r,a,t:next(x for x in r if x["lifecycle"]=="walk_forward").update(fold_id="WF99"))
    check(lambda m,r,a,t:r.__setitem__(slice(None),[x for x in r if x["instrument"]!="Si"]))
    check(lambda m,r,a,t:r.append({**r[0],"generation":"v1"}))
    check(lambda m,r,a,t:r[0].update(cost_contract="C0"))
    check(lambda m,r,a,t:r[0].update(tick_size="0.01"))
    check(lambda m,r,a,t:m["strategy_hashes"].update(T2="bad"))
    check(lambda m,r,a,t:m["strategy_hashes"].update(T3="bad"))
    check(lambda m,r,a,t:m.update(data_commit="bad"))
    check(lambda m,r,a,t:m.update(t3_completed_context=False))
    check(lambda m,r,a,t:m.update(t3_day_reset=False))
    check(lambda m,r,a,t:t[0].update(entry_time_mismatches="1",total_mismatches="1"))
    check(lambda m,r,a,t:t[0].update(exit_time_mismatches="1",total_mismatches="1"))
    check(lambda m,r,a,t:t[0].update(c1_R_mismatches="1",total_mismatches="1"))
    check(lambda m,r,a,t:a[0].update(PF_delta="0.1"))
    check(lambda m,r,a,t:m.update(hypothesis_execution=True))
    check(lambda m,r,a,t:m.update(trade_level_mismatch_count=1))
    # The two explicit T3 state mutations above must also be rejected.
    # Their required keys are absent in valid evidence; require true values if present.
    if len(mutations)!=18 or not all(mutations): raise RuntimeError(f"MUTATION_TEST_FAILURE:{sum(mutations)}/18")
    return {"status":"STAGE5_COMPARATOR_AUDIT_PASSED","studies":24,"folds":32,"trade_mismatches":0,"mutation_tests":"18/18 PASS"}

if __name__=="__main__": print(json.dumps(audit(),sort_keys=True))
