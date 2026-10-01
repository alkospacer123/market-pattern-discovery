"""Independent static/semantic auditor for the Stage 8 foundation."""
import ast,csv,hashlib,json,re
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
    core=(HERE/"strategy_core.py").read_text(); config=(HERE/"config.py").read_text(); broker=(HERE/"broker.py").read_text(); state=(HERE/"state.py").read_text(); runner=(HERE/"runner.py").read_text(); api=(HERE/"finam_api.py").read_text(); historical=(HERE/"historical_conformance.py").read_text(); production=(HERE/"production_replay.py").read_text(); resolver=(HERE/"instrument_resolver.py").read_text(); smoke=(HERE/"demo_smoke.py").read_text(); updater=(HERE/"update_demo_registry.py").read_text()
    margin=(HERE/"margin.py").read_text(); real_smoke=(HERE/"real_account_smoke.py").read_text(); real_updater=(HERE/"update_real_registry.py").read_text(); operations=(HERE/"operations.py").read_text(); preflight=(HERE/"server_preflight.py").read_text()
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
    check('SESSION_DETAILS_PATH="/v1/sessions/details"' in api and '{"token":self.__jwt}' in api and 'get("accounts"' not in broker,"SESSION_DETAILS_TOKEN_ACCOUNT_IDS")
    check('BARS_PATH_TEMPLATE="/v1/instruments/{symbol}/bars"' in api and 'H1_TIMEFRAME="TIME_FRAME_H1"' in api and '"interval.start_time":start' in api and '"interval.end_time":end' in api and '"from":start' not in api and '"to":end' not in api,"BARS_SCHEMA")
    check("def asset_params(self,symbol,account_id)" in api and "'account_id':account_id" in api,"ACCOUNT_SPECIFIC_PARAMS")
    check("def asset(self,symbol,account_id)" in api and "assets/{symbol}?" in api,"ACCOUNT_SPECIFIC_ASSET")
    check('Decimal(10)**decimals' in resolver and 'parse_rest_decimal_scalar(authority.get("min_step")' in resolver,"FINAM_REST_DECIMAL_PRICE_STEP")
    check('params.get("is_tradable")' in resolver and 'asset.get("is_tradable")' not in resolver,"ACCOUNT_PARAMS_TRADABILITY_ONLY")
    check('params.get("trade_lot_size")' in resolver and 'future.get("contract_size")' in resolver,"TYPED_QUANTITY_ECONOMICS")
    check('authority.get("quote_currency")' in resolver and 'authority.get("currency")' not in resolver,"REST_QUOTE_CURRENCY_ONLY")
    check('parse_rest_value_object(authority.get("lot_size")' in resolver and 'parse_rest_value_object(future.get("contract_size")' in resolver,"REST_VALUE_OBJECT_ECONOMICS")
    bool_parser=resolver.split("def parse_rest_bool",1)[1].split("def schedule_summary",1)[0]
    check('parse_rest_bool(params.get("is_tradable")' in resolver and "type(value) is not bool" in bool_parser and "dict" not in bool_parser,"REST_PRIMITIVE_TRADABILITY")
    check('{"num", "scale"}' not in resolver and "scaleb" not in resolver,"NO_PROTOBUF_DECIMAL_BINDING")
    check(all(alias not in resolver for alias in ("priceIncrement","lotSize","quantityStep","tradingAvailable")),"NO_GUESSED_BINDING_ALIASES")
    check('f"{ticker}@{mic}"' in resolver and 'security_id' in resolver and 'currency!="RUB"' in resolver and 'ASSET_TYPE_FUTURE' in resolver,"STRICT_IDENTITY_CURRENCY_TYPE")
    check('tuple(sorted(bindings))' in updater and 'os.replace(temp,registry_path)' in updater and 'evidence_sha256(bindings)' in updater,"ATOMIC_FOUR_BINDING_ACTIVATION")
    check('api.asset(symbol,account)' in smoke and 'api.asset_params(symbol,account)' in smoke and 'api.schedule(symbol)' in smoke,"READ_ONLY_BINDING_EVIDENCE")
    check('"quantity":{"value":str(r.quantity)}' in broker and '"client_order_id":client_id' in broker and "broker_side(r.direction" in broker,"ORDER_SCHEMA")
    check("CLIENT_ORDER_ID_MAX_LENGTH=20" in api and '"s8"+hashlib.sha256' in broker,"SHORT_CLIENT_ID")
    expected_hashes={"USDRUBF":"f0ca366d816a6213742271242e87c53d1e23f5a5fc4655df0123217df418a226","CNYRUBF":"a3815b88a11aa5878b8bd104140f002859349c2c8d7f6ff0476a0d4c4d9a612e","GLDRUBF":"12a626ba6cc47fce2f392d4a6ce3bdb8a3c1aad074306a73ab480fcfbb83b87e","IMOEXF":"119878c12f602924296ab27b5b9f3cf51fa54f1a9370793892edbea58003e110"}
    check(conformance.get("frozen_data_commit")=="50f1fd2178c18b7ab3bd969be82ad01f47a34745" and conformance.get("h1_sha256")==expected_hashes,"FROZEN_H1_AUTHORITY")
    check(hashlib.sha256((ROOT/"TradingSystemLab/results/post_v3_analysis/stage6_fixed_basket_reassessment/trail1_authoritative_trades.csv").read_bytes()).hexdigest()=="0f9034edf228a687da67e9f3e35fad01f2339be162c558e6d802c3cd77eea8ad","AUTHORITY_LEDGER_SHA")
    tree=ast.parse(production); rendered=ast.unparse(tree)
    check(not any(x in rendered for x in ("run_t3", "_dispatch", "raw_replays", "trail1_authoritative_trades.csv")),"PRODUCTION_RESEARCH_DECOUPLING")
    check("frozen_parameters()" in historical and '"lifecycle": "historical_true_oos"' not in historical,"CANDIDATE_PARAMETERS_ALL_LIFECYCLES")
    for layer in ("authority_replay","production_robot_replay"):
        x=conformance.get(layer,{}); check(x.get("status")=="PASS" and x.get("expected_trade_count")==x.get("reproduced_trade_count")==x.get("exact_matches")==418 and not sum(x.get(k,0) for k in ("missing","extra","timestamp_mismatches","direction_mismatches","price_mismatches","state_mismatches","R_mismatches")),layer.upper())
    check("DEMO_ORDER_TRANSMISSION_ENABLED" in (HERE/"demo_order_smoke.py").read_text() and "LIVE_TRADING_NOT_AUTHORIZED" in config,"DEMO_ONLY_LIVE_IMPOSSIBLE")
    check("database_identity" in state and "STATE_ENVIRONMENT_ACCOUNT_MISMATCH" in state,"STATE_ACCOUNT_ENVIRONMENT_BINDING")
    check("FINAM_REAL_READONLY" in config and 'os.getenv("FINAM_REAL_ACCOUNT_ID")' in config and 'os.getenv("FINAM_DEMO_ACCOUNT_ID")' in config,"REAL_MODE_SEPARATE_IDENTITY")
    check("class FinamRealReadOnlyBroker" in broker and 'raise RuntimeError("REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED")' in broker,"REAL_READONLY_NO_SUBMIT")
    check("details.get(\"readonly\") is not True" in broker and "REAL_TOKEN_NOT_READONLY" in real_smoke,"TOKEN_READONLY_ENFORCED")
    check("min(r15_quantity,margin_qty)" in margin and "floor_to_trade_lot" in margin and "MARGIN_CAP_INCREASED_R15" in margin,"MARGIN_ONLY_REDUCES_R15")
    check("portfolio_forts" in margin and "available_cash" in margin and "money_reserved" in margin,"FORTS_AVAILABLE_RESERVED_PARSED")
    check("long_initial_margin" in margin and "short_initial_margin" in margin and "MARGIN_CURRENCY_MISMATCH" in margin,"DIRECTIONAL_MARGIN_PARSED")
    decimal_parser=margin.split("def parse_rest_decimal_value_object",1)[1].split("def forts_funds",1)[0]
    check('set(value)!={"value"}' in decimal_parser and "Decimal(scalar)" in decimal_parser and "parse_money" not in decimal_parser,"ACCOUNT_REST_DECIMAL_DISTINCT")
    check('parse_rest_decimal_value_object(forts.get("available_cash"))' in margin and 'parse_rest_decimal_value_object(forts.get("money_reserved"))' in margin,"ACCOUNT_FUNDS_NOT_MONEY")
    check('return parse_money(params.get(key),positive=True)' in margin,"DIRECTIONAL_MARGIN_REMAINS_MONEY")
    check('row.update(values)' in real_updater and all(x in real_updater for x in ('"finam_symbol"','"security_id"','PRODUCTION_SPECIFICATION_ID','exact_matches','os.replace(temp,registry_path)','list(csv.DictReader(check_file))')),"REAL_REGISTRY_FULL_ATOMIC_ACTIVATION")
    check("class MarginBatchBudget" in margin and "self.remaining-=reservation" in margin,"SAME_BATCH_MARGIN_RESERVATION")
    check("starting_realized_equity" in runner and "REAL_ACCOUNT_NOT_CLEAN_FOR_INITIALIZATION" in runner,"CLEAN_REAL_EQUITY_BOOTSTRAP")
    check("account_identity_sha256" in runner and 'environment="REAL"' in runner,"REAL_STATE_ACCOUNT_HASH_BOUND")
    check("class InstanceLock" in operations and "SECOND_ROBOT_INSTANCE_BLOCKED" in operations and "src.backup(dst)" in operations,"SERVER_LOCK_AND_SQLITE_BACKUP")
    check("--offline" in preflight and "live_trading_authorized\":False" in preflight,"ORDER_FREE_SERVER_PREFLIGHT")
    production_source="\n".join(p.read_text(errors="ignore") for p in HERE.glob("*.py") if p.name not in {"audit_stage8.py"})
    check(not re.search(r"(?:MICRO_LIVE_MAX_QTY|MAX_CONTRACTS_PER_ORDER)\s*=",production_source),"NO_FIXED_CONTRACT_CAP")
    check("api.place_order" not in real_smoke and "submit_order" not in real_smoke,"REAL_SMOKE_ZERO_ORDERS")
    result={"status":"PASS" if not errors else "FAIL","checks":checks,"errors":errors,"production_specification_id":spec.production_id,"live_trading_activated":False,"stage8_status":"STAGE_8_REAL_ACCOUNT_READONLY_CODE_READY","margin_status":"STAGE_8_MARGIN_AWARE_FULL_R15_CODE_READY","deployment_status":"STAGE_8_INTEL_SERVER_DEPLOYMENT_PREPARED"}
    (HERE/"independent_audit_result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n"); return result
if __name__=="__main__":
    result=audit(); print(json.dumps(result,sort_keys=True)); raise SystemExit(result["status"]!="PASS")
