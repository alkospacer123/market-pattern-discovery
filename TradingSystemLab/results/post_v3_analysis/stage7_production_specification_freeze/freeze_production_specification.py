"""Generate the Stage 7 declaration from authenticated, already accepted evidence only."""
from __future__ import annotations

import argparse, csv, hashlib, json, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
BASE_SHA = "afeb33421483d6b47cde78c85ca4266eea616600"
ACTIVE = "TRAIL1__N4_01__FULL__R15"
REFERENCE = "CANONICAL__N4_01__FULL__R15"
INSTRUMENTS = ["USDRUBF", "CNYRUBF", "GLDRUBF", "IMOEXF"]
SOURCES = {
 "stage6_registry": ("TradingSystemLab/results/post_v3_analysis/stage6_unified_candidate_comparison/portfolio_trade_scaling_registry.csv", "8f0493f5dd4edf087881622005efde0531c6146903a38c362e72dbc508071b1e"),
 "stage5_lifecycle": ("TradingSystemLab/results/post_v3_analysis/stage5_structural_validation/canonical_lifecycle_registry.csv", "f2d66ba2a9a16170adc39cb0ef1cdd94b7b13ee46f9c172a5730727b1c5379f6"),
 "trail1_source": ("TradingSystemLab/results/post_v3_analysis/stage5_structural_validation/stage5_trail1_execution.py", "d1d8ac2eeea9095becd6f74295e4a540d02ee0494237af5f16f6d66a487f221b"),
 "trail1_manifest": ("TradingSystemLab/results/post_v3_analysis/stage5_structural_validation/trail1/manifest_trail1.json", "ae29ceba3c52509336ea3c097863aa92ca3e404c15415e3192b49646d29862dd"),
 "t3_source": ("TradingSystemLab/strategies/trend/T3_MTF_Trend.py", "840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c"),
 "t3_manifest": ("TradingSystemLab/results/perpetual_v3/robustness/T3/H1/manifest.json", ""),
 "four_case_registry": ("TradingSystemLab/results/post_v3_analysis/stage6_7_n4_full_four_case_test/four_case_registry.csv", "e1f5edbff005ce17fcaa73c71837db1b3906bdd3d92d1f249788e80c725c34a2"),
 "four_case_audit": ("TradingSystemLab/results/post_v3_analysis/stage6_7_n4_full_four_case_test/independent_audit_result.json", ""),
}
CORE_FILES = ["production_specification.json", "production_identity_registry.csv", "instrument_registry.csv", "strategy_identity.json", "risk_and_sizing_contract.md", "execution_semantics.md", "state_persistence_contract.md", "data_contract.md", "research_to_robot_conformance.md", "source_provenance.json", "PRODUCTION_SPECIFICATION.md"]

def sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
def dump(path: Path, obj: object) -> None: path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False)+"\n", encoding="utf-8")
def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=fields, lineterminator="\n"); w.writeheader(); w.writerows(rows)

def authenticate() -> dict:
    out={}
    for key,(rel,expected) in SOURCES.items():
        p=ROOT/rel
        if not p.is_file(): raise RuntimeError(f"MISSING_SOURCE:{rel}")
        actual=sha(p)
        if expected and actual != expected: raise RuntimeError(f"SOURCE_HASH_MISMATCH:{rel}:{actual}")
        out[key]={"path":rel,"sha256":actual}
    manifest=json.loads((ROOT/SOURCES["t3_manifest"][0]).read_text())
    expected={"candidate_id":"T3_H1_candidate_v3","phase2_configuration_id":"T3-H1-4e73cdb77246","candidate_parameter_hash":"4e73cdb77246cb07b5953160b9fc0ab36bfd4bd6d9a7f7faaae7e6e392ee340a","frozen_strategy_source_hash":SOURCES["t3_source"][1],"strategy":"T3","timeframe":"H1"}
    for k,v in expected.items():
        if manifest.get(k)!=v: raise RuntimeError(f"T3_IDENTITY_MISMATCH:{k}:{manifest.get(k)}")
    audit=json.loads((ROOT/SOURCES["four_case_audit"][0]).read_text())
    if audit.get("status")!="PASS": raise RuntimeError("STAGE6_7_AUDIT_NOT_PASS")
    with (ROOT/SOURCES["four_case_registry"][0]).open(newline="") as f: cases={r["case_id"] for r in csv.DictReader(f)}
    if not {ACTIVE,REFERENCE} <= cases: raise RuntimeError("REQUIRED_CASE_MISSING")
    out["repository_authority"]={"branch":"main merged state at task start","sha":BASE_SHA}
    return out

def active_spec() -> dict:
    return {
      "schema_version":1,"decision_authority":"explicit human selection after accepted Stage 6 final four-case comparison",
      "identity":ACTIVE,"status":"ACTIVE_PRODUCTION_SPECIFICATION","research_generation":"v3_perpetual",
      "strategy":{"name":"T3","candidate":"T3_H1_candidate_v3","configuration_id":"T3-H1-4e73cdb77246","parameter_sha256":"4e73cdb77246cb07b5953160b9fc0ab36bfd4bd6d9a7f7faaae7e6e392ee340a","source_sha256":"840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c","timeframe":"H1","parameters":{"ema_period":100,"slope_lookback":5,"adx_period":14,"adx_threshold":20.0,"atr_period":14,"atr_average_period":20,"breakout_period":20,"stop_atr":2.5,"trail_atr":3.0}},
      "variant":{"name":"TRAIL1","source_sha256":"d1d8ac2eeea9095becd6f74295e4a540d02ee0494237af5f16f6d66a487f221b","authoritative_ledger_sha256":"b773811cb39df3c2585bf3aa278195ccb6e1777dcc664b714b2c74a2bc3badde","trigger_r":1.0,"activation":"first later event; never trigger event/bar","initial_risk_frozen":True,"tighten_only":True,"forbidden_overlays":["BE1","LOCK1_AFTER_2R","SESSION_10_21","ONE_BAR","EXIT_ON_OPPOSITE_REGIME","STRUCTURAL_STACK"]},
      "basket":{"id":"N4_01","instruments":INSTRUMENTS,"dynamic_selection":False,"maximum_simultaneous_instruments":4},
      "risk":{"mode":"R15","load":"FULL","risk_fraction_per_new_instrument_position":0.015,"equal_split":False,"maximum_nominal_simultaneous_initial_risk":0.06,"risk_cash":"current_equity * 0.015","risk_cash_frozen_at_entry":True},
      "equity":{"starting_equity":"required runtime input","basis":"realized equity only; open/unrealized PnL excluded","realized_pnl":"applied on EXIT before later same-timestamp ENTRY sizing"},
      "event_order":["timestamp_ascending","EXIT_before_ENTRY","deterministic_trade_instrument_order_identity_ascending"],
      "position_model":{"one_active_position_per_instrument":True,"pyramiding":False,"repeated_entry_while_open":False,"reversal":"no atomic reversal; exit only by active stop, then independently evaluate a new signal"},
      "cost_evidence_contract":{"name":"C1","ticks_per_side":1,"round_trip_ticks":2,"normalized_research_tick":0.001,"live_fees":"BROKER_ADAPTER_BINDING_REQUIRED_STAGE8"},
      "schedule":{"entry_time_filter":None,"session_10_21":False},
      "contract_mapping":"BROKER_ADAPTER_BINDING_REQUIRED_STAGE8",
      "accepted_evidence":{"window":"2024-01-01 through 2026-09-15 authenticated endpoint","TRAIL1_R15":{"return_2024_pct":165.280419816,"return_2025_pct":74.3831505316,"return_2026_ytd_pct":88.3106185615,"cagr_2024_plus_pct":122.444495514,"max_drawdown_pct":-19.9598387654,"positive_complete_quarters":"10/10","positive_months":"23/33","time_weighted_average_open_risk_pct":1.02405093074},"CANONICAL_R15_REFERENCE":{"cagr_2024_plus_pct":109.127844528,"max_drawdown_pct":-16.3447661141,"positive_complete_quarters":"9/10","positive_months":"21/33"}},
      "stage8_started":False
    }

def generate(out: Path) -> str:
    provenance=authenticate(); spec=active_spec()
    canonical=json.dumps(spec, sort_keys=True, separators=(",",":"), ensure_ascii=False).encode()
    digest=hashlib.sha256(canonical).hexdigest(); spec_id="PROD_STAGE7_"+digest.upper()
    spec["production_specification_id"]=spec_id; spec["canonical_active_payload_sha256"]=digest
    if out.resolve() == HERE.resolve():
        out.mkdir(parents=True, exist_ok=True)
        for name in CORE_FILES + ["audit_manifest.json", "independent_audit_result.json"]:
            (out/name).unlink(missing_ok=True)
    else:
        if out.exists(): shutil.rmtree(out)
        out.mkdir(parents=True)
    dump(out/"production_specification.json",spec)
    dump(out/"strategy_identity.json",{"strategy":spec["strategy"],"variant":spec["variant"]})
    dump(out/"source_provenance.json",provenance)
    write_csv(out/"production_identity_registry.csv",["identity","status","production_specification_id","evidence_path","evidence_sha256"],[
      {"identity":ACTIVE,"status":"ACTIVE_PRODUCTION_SPECIFICATION","production_specification_id":spec_id,"evidence_path":SOURCES["four_case_registry"][0],"evidence_sha256":SOURCES["four_case_registry"][1]},
      {"identity":REFERENCE,"status":"STABLE_REFERENCE_NOT_ACTIVE_PRODUCTION","production_specification_id":"","evidence_path":SOURCES["four_case_registry"][0],"evidence_sha256":SOURCES["four_case_registry"][1]}])
    write_csv(out/"instrument_registry.csv",["instrument","research_symbol","production_symbol","exchange_code","price_step","tick_value","contract_multiplier","currency","quantity_granularity","binding_status"],[{ "instrument":i,"research_symbol":i,"production_symbol":"","exchange_code":"","price_step":"","tick_value":"","contract_multiplier":"","currency":"","quantity_granularity":"","binding_status":"BROKER_ADAPTER_BINDING_REQUIRED_STAGE8"} for i in INSTRUMENTS])
    (out/"risk_and_sizing_contract.md").write_text("""# Risk and sizing contract\n\n`current_equity` is the required starting equity plus realized PnL booked by completed exits; unrealized PnL is excluded. At one timestamp all exits are booked before entries. Each entry freezes `risk_cash = current_equity * 0.015` and its initial stop/1R. FULL never divides this budget by four; four positions imply 6% nominal initial risk.\n\nFor authenticated contract values: `stop_ticks = abs(entry - initial_stop) / price_step`; `loss_per_contract = stop_ticks * tick_value` (equivalently use an authenticated multiplier mapping); `quantity = floor_to_quantity_granularity(risk_cash / loss_per_contract)`. Non-integral ticks, nonpositive values, zero quantity, or unavailable specifications block entry. Exact FINAM/MOEX fields remain `BROKER_ADAPTER_BINDING_REQUIRED_STAGE8`; research R is not represented as live RUB PnL.\n""",encoding="utf-8")
    (out/"execution_semantics.md").write_text("""# Execution semantics\n\nH1 close-labelled completed bars drive T3. Four completed, non-overlapping H1 bars within one Europe/Moscow local day form context; incomplete blocks are unpublished. T3 uses the latest published context close at or before the execution timestamp. It applies EMA100 and five-bar slope, ADX14 > 20, ATR14 > its 20-context-bar mean, and a 20-H1-bar prior Donchian breakout (shifted one bar). Entry is signal-bar close. Initial stop is 2.5 × H1 ATR.\n\nOne position per instrument; no pyramiding or repeated entry while open. Before incorporating a bar's extreme, test the stop entering that bar. Gap fill is `min(open, stop)` LONG / `max(open, stop)` SHORT. A non-exit bar updates the favorable extreme and canonical 3 × ATR trailing candidate; stops only tighten, symmetrically. TRAIL1 triggers when a completed bar first reaches frozen +1R, stores that bar's canonical candidate, and may activate only before a later event; it cannot retroactively stop on the trigger bar. After activation canonical candidates continue tighten-only. Initial R never changes.\n\nGlobal ordering is timestamp ascending, EXIT before ENTRY, then deterministic trade/instrument/order identity ascending. No time-of-day filter or unauthorized overlay exists. Perpetual-to-live contract selection, roll/expiry detection, prohibition on entries to invalid contracts, near-expiry open-position handling, and persistent contract identity are `BROKER_ADAPTER_BINDING_REQUIRED_STAGE8`; unresolved mapping blocks entries.\n\nSignal identity is SHA-256 of canonical UTF-8 JSON containing production specification ID, strategy/configuration, variant, instrument, H1 signal close timestamp, direction, and deterministic signal sequence. The resulting trade ID plus broker idempotency key is persisted before submission; reuse is mandatory after restart.\n""",encoding="utf-8")
    (out/"state_persistence_contract.md").write_text("""# State persistence contract\n\nAtomically persist specification ID, open position and contract identity, direction, entry and initial stop, frozen initial risk and risk_cash, favorable extreme, current/canonical stop, TRAIL1 triggered/activated flags and times and stored candidate, last processed completed H1/context bars, last accepted signal/trade ID, pending order/idempotency state, fills, realized equity, and broker reconciliation marker. Restart must reconcile persisted state and broker positions/orders before processing later bars. Any mismatch blocks new entries.\n""",encoding="utf-8")
    (out/"data_contract.md").write_text("""# Data contract\n\nInput is strictly increasing, unique, timezone-aware Europe/Moscow H1 close timestamps with finite positive Open, High, Low, Close and valid OHLC geometry. A bar is usable only after close. Duplicate, conflicting, missing/stale, or non-monotonic data blocks new entries; accepted historical behavior does not synthesize missing bars. Context consists of complete same-local-day groups of four H1 bars and never crosses a day.\n\nWarm-up is validity-based: ATR14, shifted Donchian20, context EMA100 (plus source-computed EMA50/EMA200), EMA100 slope lookback 5, ADX14, context ATR14 and ATRMean20 must all be non-null. Because pandas EWM indicators seed causally, no invented fixed bar count replaces this rule. No signal is permitted until every field used by `regime` and `generate_signal` is available.\n""",encoding="utf-8")
    (out/"research_to_robot_conformance.md").write_text("""# Research-to-robot conformance\n\nStage 8 must replay authenticated frozen bar/event fixtures through the production decision core and match signal identity, direction, entry abstraction, initial stop/R, all stop and TRAIL1 transitions, exit reason/time/price abstraction, and ordering exactly. Separately test broker rounding, fees, contract mapping, gaps, restart idempotency, and reconciliation. Differences fail closed; they may not be rationalized by changing this freeze or Stage 6 economics. This is a conformance requirement, not authorization for optimization or a new backtest.\n""",encoding="utf-8")
    (out/"PRODUCTION_SPECIFICATION.md").write_text(f"""# Stage 7 Production Specification Freeze\n\n**Status:** `STAGE_7_PRODUCTION_SPECIFICATION_FREEZE_COMPLETE`\n\n**Production specification ID:** `{spec_id}`\n\n**Stage 8:** `STAGE_8_NOT_STARTED`\n\nThe user explicitly selected `{ACTIVE}` after the accepted final four-case comparison; no new score or ranking was calculated. It freezes v3 perpetual T3/H1, N4_01 (`{' + '.join(INSTRUMENTS)}`), TRAIL1, FULL, and 1.5% of current realized equity independently per position (6% maximum nominal initial risk).\n\n`{REFERENCE}` is retained only as `STABLE_REFERENCE_NOT_ACTIVE_PRODUCTION`: it is neither runtime fallback nor a second production specification. R20 is historical comparative evidence only. C1 is the research evidence contract; live costs and contract specifications require authenticated Stage 8 adapter binding.\n\nSee the focused contracts in this directory. No Stage 8 implementation is included.\n""",encoding="utf-8")
    manifest={"status":"PASS","production_specification_id":spec_id,"core_artifacts":{n:sha(out/n) for n in CORE_FILES}}
    dump(out/"audit_manifest.json",manifest)
    return spec_id

def main():
    p=argparse.ArgumentParser(); p.add_argument("--output",type=Path,default=HERE); a=p.parse_args(); print(generate(a.output))
if __name__=="__main__": main()
