"""Independent static/semantic auditor for the Stage 8 foundation."""
import csv,hashlib,json,re
from pathlib import Path
from specification import PRODUCTION_SPECIFICATION_ID,load_frozen_specification
ROOT=Path(__file__).resolve().parents[2]; HERE=Path(__file__).resolve().parent
def csv_rows(path):
    with path.open(newline="") as stream:return list(csv.DictReader(stream))
def audit():
    errors=[]; checks=0
    def check(ok,name):
        nonlocal checks; checks+=1
        if not ok: errors.append(name)
    spec=load_frozen_specification()
    check(spec.production_id==PRODUCTION_SPECIFICATION_ID,"SPEC_ID"); check(spec.identity=="TRAIL1__N4_01__FULL__R15","IDENTITY")
    check(spec.strategy["name"]=="T3" and spec.strategy["timeframe"]=="H1","T3_H1"); check(spec.variant["name"]=="TRAIL1","TRAIL1")
    check(spec.instruments==("USDRUBF","CNYRUBF","GLDRUBF","IMOEXF"),"N4"); check(spec.risk_fraction==.015 and spec.maximum_nominal_risk==.06,"R15_MAX")
    core=(HERE/"strategy_core.py").read_text(); config=(HERE/"config.py").read_text(); broker=(HERE/"broker.py").read_text(); state=(HERE/"state.py").read_text(); runner=(HERE/"runner.py").read_text(); api=(HERE/"finam_api.py").read_text(); historical=(HERE/"historical_conformance.py").read_text()
    conformance=json.loads((HERE/"conformance_report.json").read_text()); provenance=json.loads((HERE/"authority_provenance.json").read_text()); registry=(HERE/"production_instrument_registry.csv").read_text()
    check("import .broker" not in core and "from .broker" not in core,"BROKER_CORE_ISOLATION"); check('FINAM_MODE","DRY_RUN' in config and 'LIVE_TRADING_NOT_AUTHORIZED' in config,"LIVE_DEFAULT_OFF_AND_IMPOSSIBLE")
    check(not any(x in config for x in ("ema_period","adx_period","risk_fraction","basket")),"NO_MUTABLE_PARAMETERS")
    check("PRIMARY KEY" in state and "persist_intent" in state,"PERSISTENCE_IDEMPOTENCY"); check("reconcile" in runner and "entries_enabled" in runner,"RECONCILIATION_GATE")
    check("PARTIALLY_FILLED" in broker,"PARTIAL_FILL_STATE"); check("DryRunBroker" in runner,"DRY_RUN")
    prohibited=re.compile(r"(?i)(api[_-]?key|password|private[_-]?key)\s*[=:]\s*['\"][^'\"\r\n]{8,}")
    check(not any(prohibited.search(p.read_text(errors="ignore")) for p in HERE.rglob("*.py")),"NO_EMBEDDED_SECRETS")
    stage7=ROOT/"TradingSystemLab/results/post_v3_analysis/stage7_production_specification_freeze/source_provenance.json"
    for item in json.loads(stage7.read_text()).values():
        if "path" in item: check(hashlib.sha256((ROOT/item["path"]).read_bytes()).hexdigest()==item["sha256"],"RESEARCH_HASH:"+item["path"])
    check((HERE/"tests/golden_fixtures.json").is_file(),"CONFORMANCE_FIXTURES")
    check(registry.count("PERPETUAL_FUTURE")==4 and ",expiry," not in registry.splitlines()[0],"DIRECT_PERPETUAL_NO_EXPIRY")
    check(all(x in registry for x in ("USDRUBF","CNYRUBF","GLDRUBF","IMOEXF")),"FOUR_EXACT_INSTRUMENTS")
    check(provenance["finam"]["base_url"]=="https://api.finam.ru" and provenance["finam"]["api_version"]=="v1","FINAM_AUTHORITY_PROVENANCE")
    check((HERE/"context_builder.py").is_file(),"CONTEXT_BUILDER")
    check('SESSION_DETAILS_PATH="/v1/sessions/details"' in api and 'def session_details(self): return self._request("POST"' in api,"SESSION_DETAILS_POST_SCHEMA")
    check('BARS_PATH_TEMPLATE="/v1/instruments/{symbol}/bars"' in api and 'H1_TIMEFRAME="TIME_FRAME_H1"' in api,"BARS_SCHEMA")
    check("def asset_params(self,symbol,account_id)" in api and "'account_id':account_id" in api,"ACCOUNT_SPECIFIC_PARAMS")
    check('"quantity":{"value":str(r.quantity)}' in broker and '"client_order_id":client_id' in broker and "broker_side(r.direction" in broker,"ORDER_SCHEMA")
    check("CLIENT_ORDER_ID_MAX_LENGTH=20" in api and '"s8"+hashlib.sha256' in broker,"SHORT_CLIENT_ID")
    expected_hashes={"USDRUBF":"f0ca366d816a6213742271242e87c53d1e23f5a5fc4655df0123217df418a226","CNYRUBF":"a3815b88a11aa5878b8bd104140f002859349c2c8d7f6ff0476a0d4c4d9a612e","GLDRUBF":"12a626ba6cc47fce2f392d4a6ce3bdb8a3c1aad074306a73ab480fcfbb83b87e","IMOEXF":"119878c12f602924296ab27b5b9f3cf51fa54f1a9370793892edbea58003e110"}
    check(conformance.get("frozen_data_commit")=="50f1fd2178c18b7ab3bd969be82ad01f47a34745" and conformance.get("h1_sha256")==expected_hashes,"FROZEN_H1_AUTHORITY")
    mismatch_sum=conformance.get("missing",0)+conformance.get("extra",0)+sum(1 for row in csv_rows(HERE/"trade_reconciliation.csv") if row["status"]=="MISMATCH")
    check(conformance.get("unexplained_mismatches")==mismatch_sum and conformance.get("production_conformance_pass")== (mismatch_sum==0),"REAL_CONFORMANCE_NOT_FORCED")
    check("DEMO_ORDER_TRANSMISSION_ENABLED" in (HERE/"demo_order_smoke.py").read_text() and "LIVE_TRADING_NOT_AUTHORIZED" in config,"DEMO_ONLY_LIVE_IMPOSSIBLE")
    check("database_identity" in state and "STATE_ENVIRONMENT_ACCOUNT_MISMATCH" in state,"STATE_ACCOUNT_ENVIRONMENT_BINDING")
    result={"status":"PASS" if not errors else "FAIL","checks":checks,"errors":errors,"production_specification_id":spec.production_id,"live_trading_activated":False,"stage8_status":"STAGE_8_RESEARCH_ROBOT_CONFORMANCE_FAIL" if not conformance.get("production_conformance_pass") else "STAGE_8_FINAM_DEMO_BINDING_READY_AWAITING_OPERATOR_CREDENTIALS"}
    (HERE/"independent_audit_result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n"); return result
if __name__=="__main__":
    result=audit(); print(json.dumps(result,sort_keys=True)); raise SystemExit(result["status"]!="PASS")
