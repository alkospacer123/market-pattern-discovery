"""Independent static/semantic auditor for the Stage 8 foundation."""
import argparse,ast,csv,json,re,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; HERE=Path(__file__).resolve().parent
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from specification import PRODUCTION_SPECIFICATION_ID,load_frozen_specification
from TradingSystemLab.authority_hashing import canonical_authority_sha256
from TradingSystemLab.stage8_robot.readonly_supervisor import (SafetyFault,newest_expected_h1_close,
                                                               trading_h1_windows)
def csv_rows(path):
    with path.open(newline="") as stream:return list(csv.DictReader(stream))
def audit(write_result=True):
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
    backup=(HERE/"backup_state.py").read_text(); restore=(HERE/"restore_state.py").read_text()
    supervisor_path=HERE/"readonly_supervisor.py"; supervisor=supervisor_path.read_text() if supervisor_path.is_file() else ""
    timing_path=HERE/"h1_timing_diagnostic.py"; timing=timing_path.read_text() if timing_path.is_file() else ""
    launcher=(HERE/"deploy/windows/run-readonly.ps1").read_text()
    credential_store=(HERE/"deploy/windows/credential-store.ps1").read_text(); credential_init=(HERE/"deploy/windows/initialize-readonly-credentials.ps1").read_text(); credential_verify=(HERE/"deploy/windows/verify-readonly-credentials.ps1").read_text(); task_installer=(HERE/"deploy/windows/install-task.ps1").read_text()
    conformance=json.loads((HERE/"conformance_report.json").read_text()); provenance=json.loads((HERE/"authority_provenance.json").read_text()); registry=(HERE/"production_instrument_registry.csv").read_text(); registry_rows=csv_rows(HERE/"production_instrument_registry.csv")
    check("import .broker" not in core and "from .broker" not in core,"BROKER_CORE_ISOLATION"); check('FINAM_MODE","DRY_RUN' in config and 'LIVE_TRADING_NOT_AUTHORIZED' in config,"LIVE_DEFAULT_OFF_AND_IMPOSSIBLE")
    check(not any(x in config for x in ("ema_period","adx_period","risk_fraction","basket")),"NO_MUTABLE_PARAMETERS")
    check("PRIMARY KEY" in state and "persist_intent" in state,"PERSISTENCE_IDEMPOTENCY"); check("reconcile" in runner and "entries_enabled" in runner,"RECONCILIATION_GATE")
    check("PARTIALLY_FILLED" in broker,"PARTIAL_FILL_STATE"); check("DryRunBroker" in runner,"DRY_RUN")
    prohibited=re.compile(r"(?i)(api[_-]?key|password|private[_-]?key)\s*[=:]\s*['\"][^'\"\r\n]{8,}")
    check(not any(prohibited.search(p.read_text(errors="ignore")) for p in HERE.rglob("*.py")),"NO_EMBEDDED_SECRETS")
    stage7=ROOT/"TradingSystemLab/results/post_v3_analysis/stage7_production_specification_freeze/source_provenance.json"
    for item in json.loads(stage7.read_text()).values():
        if "path" in item: check(canonical_authority_sha256(ROOT/item["path"])==item["sha256"],"RESEARCH_HASH:"+item["path"])
    check((HERE/"tests/golden_fixtures.json").is_file(),"CONFORMANCE_FIXTURES")
    check(registry.count("PERPETUAL_FUTURE")==4 and ",expiry," not in registry.splitlines()[0],"DIRECT_PERPETUAL_NO_EXPIRY")
    check(all(x in registry for x in ("USDRUBF","CNYRUBF","GLDRUBF","IMOEXF")),"FOUR_EXACT_INSTRUMENTS")
    expected_real_identities={"USDRUBF":("USDRUBF@RTSX","3447194"),"CNYRUBF":("CNYRUBF@RTSX","3447192"),"GLDRUBF":("GLDRUBF@RTSX","4454911"),"IMOEXF":("IMOEXF@RTSX","4631091")}
    check(len(registry_rows)==4
          and sum(row.get("binding_status")=="AUTHENTICATED_REAL_READONLY" for row in registry_rows)==4
          and not any(row.get("binding_status")=="BLOCKED_UNAUTHENTICATED" for row in registry_rows)
          and {row.get("research_symbol"):(row.get("finam_symbol"),row.get("security_id")) for row in registry_rows}==expected_real_identities
          and all(row.get("mic")=="RTSX" and row.get("trading_status")=="TRADABLE" for row in registry_rows),
          "REAL_REGISTRY_4_OF_4_ACTIVATED")
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
    check('f"{ticker}@{mic}"' in resolver and 'security_id' in resolver and 'currency!="RUB"' in resolver and '"FUTURES"' in resolver,"STRICT_IDENTITY_CURRENCY_TYPE")
    check('tuple(sorted(bindings))' in updater and 'os.replace(temp,registry_path)' in updater and 'evidence_sha256(bindings)' in updater,"ATOMIC_FOUR_BINDING_ACTIVATION")
    check('api.asset(symbol,account)' in smoke and 'api.asset_params(symbol,account)' in smoke and 'api.schedule(symbol)' in smoke,"READ_ONLY_BINDING_EVIDENCE")
    check('"quantity":{"value":str(r.quantity)}' in broker and '"client_order_id":client_id' in broker and "broker_side(r.direction" in broker,"ORDER_SCHEMA")
    check("CLIENT_ORDER_ID_MAX_LENGTH=20" in api and '"s8"+hashlib.sha256' in broker,"SHORT_CLIENT_ID")
    expected_hashes={"USDRUBF":"f0ca366d816a6213742271242e87c53d1e23f5a5fc4655df0123217df418a226","CNYRUBF":"a3815b88a11aa5878b8bd104140f002859349c2c8d7f6ff0476a0d4c4d9a612e","GLDRUBF":"12a626ba6cc47fce2f392d4a6ce3bdb8a3c1aad074306a73ab480fcfbb83b87e","IMOEXF":"119878c12f602924296ab27b5b9f3cf51fa54f1a9370793892edbea58003e110"}
    check(conformance.get("frozen_data_commit")=="50f1fd2178c18b7ab3bd969be82ad01f47a34745" and conformance.get("h1_sha256")==expected_hashes,"FROZEN_H1_AUTHORITY")
    check(canonical_authority_sha256(ROOT/"TradingSystemLab/results/post_v3_analysis/stage6_fixed_basket_reassessment/trail1_authoritative_trades.csv")=="0f9034edf228a687da67e9f3e35fad01f2339be162c558e6d802c3cd77eea8ad","AUTHORITY_LEDGER_SHA")
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
    check('mode=ro' in operations and "source.is_file()" in operations and "source.is_symlink()" in operations,
          "SQLITE_BACKUP_MISSING_SOURCE_FAIL_CLOSED")
    check(operations.count('PRAGMA integrity_check')>=2 and "src.backup(dst)" in operations,
          "SQLITE_ONLINE_BACKUP_SOURCE_AND_DESTINATION_INTEGRITY")
    check('state_directory = root / "state"' in backup and 'source = state_directory / SUPERVISOR_DATABASE' in backup
          and 'backup_directory = root / "backups"' in backup
          and 'SUPERVISOR_DATABASE = "readonly-supervisor.sqlite3"' in backup,
          "BACKUP_EXACT_SUPERVISOR_DATABASE_AUTHORITY")
    check("BACKUP_MANIFEST_SCHEMA" in backup and "PRODUCTION_SPECIFICATION_ID" in backup
          and '"sha256": sha256_file(backup)' in backup and "os.replace(manifest_temp, manifest)" in backup,
          "BACKUP_ATOMIC_PRODUCTION_CHECKSUM_MANIFEST")
    check("frozenset(payload) != MANIFEST_KEYS" in restore
          and "payload[\"production_specification_id\"] != PRODUCTION_SPECIFICATION_ID" in restore
          and "sha256_file(backup) != payload[\"sha256\"]" in restore,
          "RECOVERY_STRICT_MANIFEST_PRODUCTION_CHECKSUM")
    check("validate_operational_database(path)" in restore
          and "PRAGMA table_info(operational_state)" in operations
          and "PRAGMA integrity_check" in operations,
          "RECOVERY_INTEGRITY_AND_EXACT_OPERATIONAL_SCHEMA")
    check("InstanceLock" in restore and "stage8-readonly.lock" in restore
          and "SQLITE_RECOVERY_SUPERVISOR_RUNNING" in restore,
          "RECOVERY_LIFETIME_LOCK_EXCLUSION")
    restore_tree=ast.parse(restore)
    restore_function=next(node for node in restore_tree.body
                          if isinstance(node,ast.FunctionDef) and node.name=="restore_production_state")
    rollback_try=next((node for node in ast.walk(restore_function)
                       if isinstance(node,ast.Try)
                       and any(isinstance(call,ast.Call) and isinstance(call.func,ast.Attribute)
                               and call.func.attr=="replace" for call in ast.walk(node))),None)
    rollback_source=ast.unparse(rollback_try) if rollback_try is not None else ""
    quarantine_line=next((call.lineno for call in ast.walk(restore_function)
                          if isinstance(call,ast.Call) and ast.unparse(call)=="os.replace(original, quarantine)"),0)
    early_target_unlink=any(call.lineno<quarantine_line and isinstance(call.func,ast.Attribute)
                            and call.func.attr=="unlink" and "target" in ast.unparse(call.func.value)
                            for call in ast.walk(restore_function) if isinstance(call,ast.Call))
    check(rollback_try is not None
          and "for original, quarantine in zip(originals, quarantines)" in rollback_source
          and "os.replace(original, quarantine)" in rollback_source
          and "os.replace(temporary, target)" in rollback_source
          and "validate_operational_schema(target)" in rollback_source
          and "for original, quarantine in reversed(moved)" in rollback_source
          and rollback_source.index("os.replace(original, quarantine)")
              < rollback_source.index("os.replace(temporary, target)")
              < rollback_source.index("validate_operational_schema(target)")
          and quarantine_line and not early_target_unlink
          and "ROLLBACK_BASENAME" in restore and "ROLLBACK_MATERIAL_PRESENT" in restore,
          "RECOVERY_QUARANTINE_COMMIT_VALIDATION_ROLLBACK_INVARIANT")
    recovery_calls=set()
    for recovery_source in (operations,backup,restore):
        recovery_calls.update(node.func.attr for node in ast.walk(ast.parse(recovery_source))
                              if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute))
    check(not recovery_calls.intersection({"place_order","submit_order","cancel_order","modify_order"}),
          "BACKUP_RECOVERY_NO_ORDER_CALLS")
    check("--offline" in preflight and "live_trading_authorized\":False" in preflight,"ORDER_FREE_SERVER_PREFLIGHT")
    production_source="\n".join(p.read_text(errors="ignore") for p in HERE.glob("*.py") if p.name not in {"audit_stage8.py"})
    check(not re.search(r"(?:MICRO_LIVE_MAX_QTY|MAX_CONTRACTS_PER_ORDER)\s*=",production_source),"NO_FIXED_CONTRACT_CAP")
    check("api.place_order" not in real_smoke and "submit_order" not in real_smoke,"REAL_SMOKE_ZERO_ORDERS")
    check(supervisor_path.is_file(),"READONLY_SUPERVISOR_EXISTS")
    check('MODE = "REAL_READONLY"' in supervisor and "FINAM_REAL_READONLY_MODE_REQUIRED" in supervisor,"SUPERVISOR_REAL_READONLY_MANDATORY")
    check("NEW_ENTRIES_DISABLED_REQUIRED" in supervisor and 'entries_enabled=False' in supervisor,"SUPERVISOR_ENTRIES_DISABLED_MANDATORY")
    check("InstanceLock" in supervisor and "stage8-readonly.lock" in supervisor,"SUPERVISOR_LIFETIME_LOCK")
    check("write_heartbeat" in supervisor and "configure_operational_log" in supervisor,"SUPERVISOR_HEARTBEAT_ROTATING_LOG")
    check("self.api.schedule(symbol)" in supervisor and "STALE_COMPLETED_H1_DATA" in supervisor,
          "SUPERVISOR_SCHEDULE_AWARE_H1_FRESHNESS")
    audit_now=datetime(2026,1,5,12,30,tzinfo=timezone.utc)
    active={"sessions":[
      {"type":"EARLY_TRADING","interval":{"start_time":"2026-01-05T04:00:00Z","end_time":"2026-01-05T06:00:00Z"}},
      {"type":"CORE_TRADING","interval":{"start_time":"2026-01-05T06:00:00Z","end_time":"2026-01-05T16:00:00Z"}},
      {"type":"LATE_TRADING","interval":{"start_time":"2026-01-05T16:00:00Z","end_time":"2026-01-05T20:50:00Z"}}]}
    windows=trading_h1_windows(active)
    check(windows==[(datetime(2026,1,5,4,tzinfo=timezone.utc),datetime(2026,1,5,20,50,tzinfo=timezone.utc))],"H1_CONTIGUOUS_TRADING_WINDOWS")
    check(newest_expected_h1_close(active,datetime(2026,1,5,19,30,tzinfo=timezone.utc)).hour==18,"H1_WHOLE_UTC_HOUR_OPEN_GRID")
    check(newest_expected_h1_close(active,datetime(2026,1,5,20,49,tzinfo=timezone.utc)).hour==19
          and newest_expected_h1_close(active,datetime(2026,1,5,20,50,tzinfo=timezone.utc)).hour==20,"H1_FINAL_PARTIAL_BAR_COMPLETION")
    nontrading={"sessions":[
      {"type":"OPENING_AUCTION","interval":{"start_time":"2026-01-05T03:30:00Z","end_time":"2026-01-05T04:00:00Z"}},
      {"type":"CLEARING","interval":{"start_time":"2026-01-05T14:00:00Z","end_time":"2026-01-05T14:05:00Z"}},
      {"type":"CLOSED","interval":{"start_time":"2026-01-05T21:00:00Z","end_time":"2026-01-06T04:00:00Z"}}]}
    check(newest_expected_h1_close(nontrading,audit_now) is None,"H1_NONTRADING_SESSIONS_NO_EXPECTATION")
    check('TRADING_SESSION_TYPES = frozenset({"EARLY_TRADING", "CORE_TRADING", "LATE_TRADING"})' in supervisor,"H1_ALLOWED_SESSION_TYPES_EXPLICIT")
    check("candidate = start +" not in supervisor and "available_until - start" not in supervisor,"H1_NO_LEGACY_SESSION_START_FLOOR")
    check("min(opened+timedelta(hours=1),end)" in api,"H1_WINDOW_END_COMPLETION_BOUNDARY")
    check("expected not in raw_opens" in supervisor
          and "if str(exc) == OFF_GRID_H1_OPEN_CODE" in supervisor
          and "test_off_grid_h1_open_surfaces_distinct_sanitized_safety_fault" in (HERE/"tests/test_readonly_supervisor.py").read_text(),
          "H1_EXACT_EXPECTED_RAW_OPEN_MEMBERSHIP")
    check('f"expected_h1:{name}"' in supervisor and "self.state.put_many(updates)" in supervisor,"H1_EXPECTED_WATERMARK_TRANSACTIONAL_SQLITE")
    check("derived or prior_expected" in supervisor,"H1_CLOSED_PERSISTED_CONTINUITY")
    check("H1_EXPECTED_COMPLETED_WATERMARK_UNAVAILABLE" in supervisor,"H1_COLD_START_CLOSED_FAILS_CLOSED")
    check("time_model_validated" not in supervisor and "H1_FINAM_TIME_MODEL_NOT_VALIDATED" not in supervisor,"H1_NO_TIME_MODEL_OR_ENVIRONMENT_BYPASS")
    tests=(HERE/"tests/test_readonly_supervisor.py").read_text()
    check("newer_pending_bar_cannot_hide_exact_missing_expected" in tests,"H1_PENDING_BAR_MISSING_COMPLETED_REGRESSION")
    check("cycle_count\"] == 0" in tests and "expected_h1:{name}" in tests,"H1_STALE_STATE_IMMUTABILITY_TESTED")
    check("fresh_cycle_after_stale_fault_clears_failure" in tests,"H1_STALE_RECOVERY_TESTED")
    check(not any(p.suffix.lower() in {".csv",".json",".png",".jpg"} and "evidence" in p.name.lower()
                  for p in (HERE/"tests").iterdir() if p.name not in {"finam_binding_fixtures.json"}),"H1_NO_REAL_TIMING_EVIDENCE_FIXTURE")
    supervisor_tree=ast.parse(supervisor); calls={node.func.attr for node in ast.walk(supervisor_tree) if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)}
    check(not calls.intersection({"place_order","submit_order","cancel_order","modify_order"}),"SUPERVISOR_NO_ORDER_CALLS")
    check(timing_path.is_file() and 'api.schedule(symbol)' in timing and 'api.bars(symbol' in timing,
          "H1_REAL_TIMING_EVIDENCE_COLLECTOR")
    timing_calls={node.func.attr for node in ast.walk(ast.parse(timing))
                  if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)}
    check(not timing_calls.intersection({"account","orders","order","asset","asset_params",
                                         "place_order","submit_order","cancel_order","modify_order"}),
          "H1_DIAGNOSTIC_PUBLIC_TIME_ONLY_NO_ORDER_OR_ACCOUNT_CALLS")
    check('"h1_timestamps"' in timing and '"contains_account_data": False' in timing
          and '"contains_credentials": False' in timing,
          "H1_DIAGNOSTIC_SANITIZED_PROJECTION")
    check("H1_TIMING_EVIDENCE_REPOSITORY_OUTPUT_FORBIDDEN" in timing
          and "REPOSITORY_ROOT" in timing and ".resolve()" in timing,
          "H1_DIAGNOSTIC_REPOSITORY_OUTPUT_FAIL_CLOSED")
    readme=(HERE/"README.md").read_text()
    check("external operational evidence" in readme and "must not be committed to Git" in readme
          and "synthetic fixtures" in readme,
          "H1_REAL_CAPTURE_EXTERNAL_SYNTHETIC_TESTS_ONLY")
    check("TradingSystemLab.stage8_robot.readonly_supervisor" in launcher,"WINDOWS_LAUNCHES_READONLY_SUPERVISOR")
    check("TradingSystemLab.stage8_robot.real_account_smoke" not in launcher,"REAL_SMOKE_NOT_SERVICE_TARGET")
    windows_deployment="\n".join((credential_store,credential_init,credential_verify,launcher,task_installer))
    check("ProtectedData]::Protect" in credential_store and "ProtectedData]::Unprotect" in credential_store and "DataProtectionScope]::CurrentUser" in credential_store,"WINDOWS_DPAPI_CURRENT_USER_STORE")
    check("LocalMachine" not in windows_deployment,"WINDOWS_DPAPI_NEVER_LOCAL_MACHINE")
    check(not re.search(r"\bsetx(?:\.exe)?\b",windows_deployment,re.I),"WINDOWS_NO_SETX")
    check(not re.search(r"SetEnvironmentVariable\s*\([^\n]+(?:User|Machine)",windows_deployment,re.I),"WINDOWS_NO_PERSISTENT_ENV_WRITE")
    task_action=task_installer.split("New-ScheduledTaskAction",1)[1].splitlines()[0]
    check("FINAM_API_SECRET" not in task_action and "FINAM_REAL_ACCOUNT_ID" not in task_action,"WINDOWS_TASK_ARGUMENTS_SECRET_FREE")
    check("New-ScheduledTaskPrincipal" in task_installer and "-UserId $principal.Name" in task_installer and "Get-ReadonlyCredential" in task_installer,"WINDOWS_EXPLICIT_MATCHED_PRINCIPAL")
    check(not re.search(r"-UserId\s+(?:['\"])?(?:NT AUTHORITY\\)?SYSTEM\b",task_installer,re.I) and "-LogonType Password" in task_installer,"WINDOWS_UNATTENDED_NON_SYSTEM_LOGON")
    check('$env:FINAM_MODE = "REAL_READONLY"' in launcher,"WINDOWS_REAL_READONLY_FORCED")
    check('$env:NEW_ENTRIES_DISABLED = "true"' in launcher,"WINDOWS_ENTRIES_DISABLED_FORCED")
    check("ROBOT_STATE_PATH" not in launcher and "stage8.sqlite3" not in launcher,
          "WINDOWS_NO_OBSOLETE_SUPERVISOR_STATE_AUTHORITY")
    check("TradingSystemLab.stage8_robot.readonly_supervisor" in launcher and not any(x in windows_deployment for x in ("place_order","submit_order","cancel_order")),"WINDOWS_SERVICE_READONLY_NO_ORDER_PATH")
    check("-ExecutionPolicy RemoteSigned" in task_installer and "-MultipleInstances IgnoreNew" in task_installer,"WINDOWS_TASK_POLICY_CONSERVATIVE")
    result={"status":"PASS" if not errors else "FAIL","checks":checks,"errors":errors,"production_specification_id":spec.production_id,"live_trading_activated":False,"stage8_status":"STAGE_8_8_6_SQLITE_RECOVERY_CODE_READY_PENDING_INTEL_ACCEPTANCE","margin_status":"STAGE_8_MARGIN_AWARE_FULL_R15_CODE_READY","deployment_status":"STAGE_8_INTEL_SERVER_DEPLOYMENT_PREPARED"}
    if write_result: (HERE/"independent_audit_result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    return result
if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--check-only",action="store_true"); args=parser.parse_args()
    result=audit(write_result=not args.check_only); print(json.dumps(result,sort_keys=True)); raise SystemExit(result["status"]!="PASS")
