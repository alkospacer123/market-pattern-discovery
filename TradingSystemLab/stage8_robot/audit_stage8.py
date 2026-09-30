"""Independent static/semantic auditor for the Stage 8 foundation."""
import hashlib,json,re
from pathlib import Path
from specification import PRODUCTION_SPECIFICATION_ID,load_frozen_specification
ROOT=Path(__file__).resolve().parents[2]; HERE=Path(__file__).resolve().parent
def audit():
    errors=[]; checks=0
    def check(ok,name):
        nonlocal checks; checks+=1
        if not ok: errors.append(name)
    spec=load_frozen_specification()
    check(spec.production_id==PRODUCTION_SPECIFICATION_ID,"SPEC_ID"); check(spec.identity=="TRAIL1__N4_01__FULL__R15","IDENTITY")
    check(spec.strategy["name"]=="T3" and spec.strategy["timeframe"]=="H1","T3_H1"); check(spec.variant["name"]=="TRAIL1","TRAIL1")
    check(spec.instruments==("USDRUBF","CNYRUBF","GLDRUBF","IMOEXF"),"N4"); check(spec.risk_fraction==.015 and spec.maximum_nominal_risk==.06,"R15_MAX")
    core=(HERE/"strategy_core.py").read_text(); config=(HERE/"config.py").read_text(); broker=(HERE/"broker.py").read_text(); state=(HERE/"state.py").read_text(); runner=(HERE/"runner.py").read_text()
    check("import .broker" not in core and "from .broker" not in core,"BROKER_CORE_ISOLATION"); check("LIVE_TRADING_ENABLED" in config and 'os.getenv(name,"")' in config,"LIVE_DEFAULT_OFF")
    check(not any(x in config for x in ("ema_period","adx_period","risk_fraction","basket")),"NO_MUTABLE_PARAMETERS")
    check("PRIMARY KEY" in state and "persist_intent" in state,"PERSISTENCE_IDEMPOTENCY"); check("reconcile" in runner and "entries_enabled" in runner,"RECONCILIATION_GATE")
    check("PARTIALLY_FILLED" in broker,"PARTIAL_FILL_STATE"); check("DryRunBroker" in runner,"DRY_RUN")
    prohibited=re.compile(r"(?i)(api[_-]?key|password|private[_-]?key)\s*[=:]\s*['\"][^'\"\r\n]{8,}")
    check(not any(prohibited.search(p.read_text(errors="ignore")) for p in HERE.rglob("*.py")),"NO_EMBEDDED_SECRETS")
    stage7=ROOT/"TradingSystemLab/results/post_v3_analysis/stage7_production_specification_freeze/source_provenance.json"
    for item in json.loads(stage7.read_text()).values():
        if "path" in item: check(hashlib.sha256((ROOT/item["path"]).read_bytes()).hexdigest()==item["sha256"],"RESEARCH_HASH:"+item["path"])
    check((HERE/"tests/golden_fixtures.json").is_file(),"CONFORMANCE_FIXTURES")
    result={"status":"PASS" if not errors else "FAIL","checks":checks,"errors":errors,"production_specification_id":spec.production_id,"live_trading_activated":False,"stage8_status":"STAGE_8_IMPLEMENTATION_IN_PROGRESS"}
    (HERE/"independent_audit_result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n"); return result
if __name__=="__main__":
    result=audit(); print(json.dumps(result,sort_keys=True)); raise SystemExit(result["status"]!="PASS")
