"""Independent static/semantic auditor for the Stage 8 foundation."""
import argparse,ast,csv,hashlib,json,re,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; HERE=Path(__file__).resolve().parent
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from specification import PRODUCTION_SPECIFICATION_ID,load_frozen_specification
from TradingSystemLab.authority_hashing import canonical_authority_sha256
from TradingSystemLab.stage8_robot.readonly_supervisor import (SafetyFault,newest_expected_h1_close,
                                                               trading_h1_windows)
def canonical_text_sha256(raw: bytes) -> str:
    return hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
def csv_rows(path):
    with path.open(newline="") as stream:return list(csv.DictReader(stream))
def current_readme_status(document):
    match=re.search(r"^\*\*Status:\*\*\s+`([^`]+)`",document,re.M)
    return match.group(1) if match else None
def _current_handoff(document):
    marker="## Current handoff"
    start=document.find(marker)
    if start < 0: return ""
    body_start=document.find("\n",start)
    if body_start < 0: return ""
    next_section=document.find("\n## ",body_start+1)
    return document[body_start+1:] if next_section < 0 else document[body_start+1:next_section]

def _stage8_10_document_consistency(document):
    """Return independent semantic verdicts for current and historical prose."""
    historical_labels=("historical","at the time","in this historical snapshot",
                       "subsequently","later","current authority is recorded below")
    paragraphs=re.split(r"\n\s*\n",document)
    stale_next=False; inconsistent=False
    for paragraph in paragraphs:
        normalized=" ".join(paragraph.split()); lower=normalized.lower()
        historical=any(label in lower for label in historical_labels)
        if (re.search(r"stage 8\.10\.[1-8]\s+(?:(?:is\s+)?(?:\*\*)?complete(?:\*\*)?\s+(?:and\s+is\s+)?|is\s+(?:the\s+)?)next (?:separate )?(?:lifecycle )?gate",normalized,re.I)
                or (re.search(r"Stage 8\.10\.8 is (?:\*\*)?COMPLETE", normalized, re.I)
                    and "next separate lifecycle gate" in lower)
                or (re.search(r"Stage 8\.10\.8 is (?:\*\*)?COMPLETE", normalized, re.I)
                    and "not implemented or executed here" in lower)):
            stale_next=True
        earlier_not_started=re.search(r"Stage 8\.10\.[1-7].{0,40}(?:\*\*)?NOT STARTED",normalized,re.I)
        later_complete=bool(re.search(r"Stage 8\.10\.8 is (?:\*\*)?COMPLETE",normalized,re.I))
        active_8107=bool(re.search(r"Stage 8\.10\.7.{0,40}(?:\*\*)?NOT STARTED",normalized,re.I))
        stage11_invalid=bool(re.search(r"Stage 8\.11.{0,40}(?:is|=) (?:\*\*)?(?:STARTED|AUTHORIZED)",normalized,re.I))
        if not historical and (active_8107 or stage11_invalid or (earlier_not_started and later_complete)):
            inconsistent=True
    handoff=_current_handoff(document)
    normalized_handoff=" ".join(handoff.split())
    required=(
        "Stage 8.9 is **COMPLETE**", "Stage 8.10 is **COMPLETE**",
        "Stage 8.11 — Controlled Real Execution Acceptance — is now **COMPLETE / PASS**",
        "72a910e49b876cda99484a810e6f8a1b16ac0209", "stage8.11.attempt7",
        "704BFCC19B1A63F490192C0D8D0E4715BFECF77664296AFEF47E5B80FBF64B5F",
        "exactly two real order-endpoint calls", "final position quantity: `0`",
        "final active broker orders: `0`", "unresolved Stage 8.11 intents: `0`",
        "final production kill switch: `HALTED`", "Scheduled Task: `Disabled`",
        "The physical authorization used for attempt7 is consumed",
        "Current `execution_authorized = false`",
        "real-order transmission remains unauthorized",
        "Stage 8.12 — **STARTED / STAGES 8.12.1–8.12.3 COMPLETE / STAGE 8.12.4 IMPLEMENTATION IN PROGRESS / NOT AUTHORIZED**",
        "Stage 8.12.1 — Production runtime assembly — is **COMPLETE / PASS**",
        "Stage 8.12.2 — Production path conformance and failure audit — is **COMPLETE / PASS**",
        "2a15f4331afc1433dfbfd0464108e39e59d236f8",
        "4F58595E2F62F2A377E5525972B9E88A136B2F9BC51760268D012AF94A70AE9F",
        "19/19 PASS", "25/25 PASS", "144/144 PASS", "48/48 PASS", "113/113 PASS", "111/111 PASS",
        "test-only real-order count: `0`",
        "Stage 8.12.3 — Intel production preflight — is **COMPLETE / PASS**",
        "Stage 8.12.4 — Explicit FULL/R15 production authorization and activation — is now **STARTED / IMPLEMENTATION IN PROGRESS / NOT AUTHORIZED**")
    exact=bool(handoff and all(" ".join(token.split()) in normalized_handoff for token in required))
    if handoff and re.search(r"next (?:possible )?(?:lifecycle )?gate is Stage 8\.10\.[1-8]",handoff,re.I):
        stale_next=True
    return exact,not inconsistent,not stale_next
def _stage8_10_6_python_safe(source):
    try: tree=ast.parse(source)
    except SyntaxError: return False
    forbidden_modules=("finam_api","broker","runner","urllib.request","requests","httpx","socket","http.client","subprocess")
    imports=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.Import): imports.extend(alias.name.lower() for alias in node.names)
        elif isinstance(node,ast.ImportFrom):
            imports.append((node.module or "").lower())
            imports.extend(alias.name.lower() for alias in node.names)
    forbidden_calls={"urlopen","request","post","put","patch","delete","place_order","submit_order","cancel_order","modify_order"}
    calls={node.func.attr.lower() if isinstance(node.func,ast.Attribute) else node.func.id.lower()
           for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,(ast.Attribute,ast.Name))}
    return not any(module == term or module.startswith(term + ".") for module in imports for term in forbidden_modules) and not calls.intersection(forbidden_calls)

def _stage8_10_6_semantics(safety,validation,wrapper):
    safety_required=(
        'return None, "KILL_SWITCH_MISSING"', 'return None, "KILL_SWITCH_INVALID"',
        'if switch["state"] == "HALTED": reasons.append("KILL_SWITCH_HALTED")',
        'if execution_authorized is not True: reasons.append("EXECUTION_NOT_AUTHORIZED")',
        'heartbeat.get("health_status") == "HEALTHY"', 'heartbeat.get("reconciliation_status") == "PASS"',
        'heartbeat.get("entries_enabled") is False', 'heartbeat.get("unresolved_order_count") == 0',
        'heartbeat.get("failure_code") is None', 'heartbeat.get("consecutive_failures") == 0',
        'heartbeat.get("cycle_count") >= 1', 'elif age > MAX_HEARTBEAT_AGE_SECONDS: reasons.append("HEARTBEAT_STALE")',
        'elif age > MAX_HEARTBEAT_AGE_SECONDS: reasons.append("FINAM_CONTACT_STALE")',
        'last_successful_finam_api_contact', '_HASH.fullmatch', 'REPOSITORY_OUTPUT_FORBIDDEN')
    report_required=('"production_kill_switch_initialized": True','"production_kill_switch_final_state": "HALTED"',
                     '"production_kill_switch_valid": True','--production-runtime-root','load_kill_switch(root)')
    wrapper_forbidden=("credential-store.ps1","trading-credential-store.ps1","get-readonlycredential","get-tradingcredential",
        "initialize-readonly-credentials","initialize-trading-credentials","invoke-webrequest","invoke-restmethod","curl","wget",
        "run-readonly","install-task","runner","broker","enable-scheduledtask","start-scheduledtask","register-scheduledtask","allow_arm",
        "execution_authorized=true")
    lower=wrapper.lower()
    offline=_stage8_10_6_python_safe(safety) and _stage8_10_6_python_safe(validation) and all(x in safety for x in safety_required)
    halt_only=(not any(x in lower for x in wrapper_forbidden)
               and not re.search(r"execution[_-]?authorized\s*=\s*\$?true",lower))
    report_contract=all(x in validation for x in report_required) and "--production-runtime-root $runtime" in wrapper
    return offline,halt_only,report_contract

def _stage8_10_7_semantics(diagnostic,wrapper):
    try: tree=ast.parse(diagnostic)
    except SyntaxError: return (False,)*6
    calls={node.func.attr.lower() if isinstance(node.func,ast.Attribute) else node.func.id.lower()
           for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,(ast.Attribute,ast.Name))}
    imports=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.Import): imports.extend(alias.name.lower() for alias in node.names)
        elif isinstance(node,ast.ImportFrom): imports.append((node.module or "").lower()); imports.extend(alias.name.lower() for alias in node.names)
    forbidden_calls={"orders","order","place_order","cancel_order","submit_order","modify_order","account","assets","assets_all_active","asset","params","schedule","bars","urlopen"}
    forbidden_imports=("broker","runner","operations","reconciliation","requests","httpx","socket","http.client","urllib.request")
    required=('api.create_session()','api.session_details()',
              'local_account_binding_confirmed is not True',
              'type(details["readonly"]) is not bool','details["readonly"] is not False',
              'occurrences = [str(value) for value in account_ids].count(str(expected_account))',
              'occurrences == 0','occurrences != 1','REPOSITORY_OUTPUT_FORBIDDEN')
    session_only=(not calls.intersection(forbidden_calls)
                  and not any(module == term or module.startswith(term + ".") for module in imports for term in forbidden_imports)
                  and {"create_session","session_details","load_kill_switch"}.issubset(calls)
                  and all(term in diagnostic for term in required))
    pre=diagnostic.find('_halted_switch(runtime_root)')
    create=diagnostic.find('api = api_factory(secret)')
    details=diagnostic.find('details = api.session_details()')
    post=diagnostic.find('_halted_switch(runtime_root, post=True)')
    kill_switch=(diagnostic.count('load_kill_switch(runtime_root)') == 1
                 and diagnostic.count('_halted_switch(runtime_root)') == 1
                 and diagnostic.count('_halted_switch(runtime_root, post=True)') == 1
                 and 'switch.get("state") != "HALTED"' in diagnostic
                 and -1 < pre < create < details < post)
    report_required={
        "schema_id":"stage8_10_7_intel_trading_token_acceptance.v1",
        "mode":"INTEL_TRADING_TOKEN_SESSION_ACCEPTANCE_NO_ORDER",
        "local_readonly_trading_account_match":True,"trading_dpapi_current_user_validated":True,
        "trading_credential_production_id_validated":True,"production_kill_switch_pre_valid":True,
        "production_kill_switch_pre_state":"HALTED","trading_session_created":True,
        "expected_account_enumerated":True,"expected_account_occurrence_count":1,
        "trading_token_readonly":False,"trading_token_write_boundary_confirmed":True,
        "remote_call_scope":"SESSION_CREATE_AND_DETAILS_ONLY","production_kill_switch_post_valid":True,
        "production_kill_switch_post_state":"HALTED","trading_token_used":True,
        "readonly_token_used_for_remote_auth":False,"finam_authentication_performed":True,
        "order_endpoint_called":False,"order_count":0,"execution_authorized":False,
        "live_trading_authorized":False,"real_order_transmission_authorized":False,
        "scheduled_task_required":False,"stage8_10_8_status":"NOT_STARTED",
        "stage8_11_status":"NOT_STARTED_NOT_AUTHORIZED","stage8_12_status":"NOT_STARTED_NOT_AUTHORIZED"}
    constants={node.targets[0].id:node.value.value for node in tree.body
               if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name)
               and isinstance(node.value,ast.Constant)}
    report=None
    for node in ast.walk(tree):
        if isinstance(node,ast.Return) and isinstance(node.value,ast.Dict):
            candidate={k.value:(v.value if isinstance(v,ast.Constant) else constants.get(v.id) if isinstance(v,ast.Name) else None)
                       for k,v in zip(node.value.keys,node.value.values)
                       if isinstance(k,ast.Constant) and isinstance(k.value,str)}
            if "schema_id" in candidate: report=candidate
    sensitive=("account_id","account_ids","api_secret","secret","jwt","authorization","dpapi_material","raw_finam")
    report_contract=(report is not None and all(report.get(k)==v and type(report.get(k)) is type(v)
                     for k,v in report_required.items())
                     and not any(any(term in key.lower() for term in sensitive) for key in report))
    lower=wrapper.lower()
    wrapper_required=('assert-hostsafe','assert-killswitchhalted','credential-store.ps1','trading-credential-store.ps1',
        'get-readonlycredential','get-tradingcredential','finam_real_account_id -cne',
        '$env:finam_8107_trading_api_secret','$env:finam_8107_account_id',
        'tradingsystemlab.stage8_robot.trading_token_intel_acceptance','remove-item "env:$name"',
        '$readonlycredential = $null','$tradingcredential = $null','push-location $repo','pop-location')
    wrapper_forbidden=('set-processreadonlycredentials','enable-scheduledtask','start-scheduledtask','register-scheduledtask',
        'set-scheduledtask','write_kill_switch','emergency_halt','allow_arm','place_order','submit_order','cancel_order',
        'modify_order','run-readonly','install-task','readonly_supervisor','runner','broker','order_path_dry_validation',
        'validate-order-path-dry','invoke-webrequest','invoke-restmethod','curl','wget',
        '$env:finam_api_secret =','$env:finam_real_account_id =','$env:finam_trading_api_secret =',
        '$env:finam_trading_account_id =','$env:finam_permission_','execution_authorized=true')
    runtime_safe=not any(term in lower for term in wrapper_forbidden) and not re.search(r'(?<![\w-])orders?(?![\w-])',lower)
    generic_credentials=('$env:finam_api_secret =','$env:finam_real_account_id =',
        '$env:finam_trading_api_secret =','$env:finam_trading_account_id =','$env:finam_permission_')
    credential_safe=(all(term in lower for term in wrapper_required) and not any(term in lower for term in generic_credentials)
        and lower.count('$readonlycredential.finam_api_secret') == 1
        and '[string]::isnullorwhitespace([string]$readonlycredential.finam_api_secret)' in lower
        and '$env:finam_8107_trading_api_secret = [string]$tradingcredential.finam_trading_api_secret' in lower
        and not re.search(r'\$env:[^\r\n=]+\s*=\s*[^\r\n]*\$readonlycredential\.finam_api_secret',lower))
    cleanup=(lower.count('remove-item "env:$name"') == 1 and lower.count('$readonlycredential = $null') == 2
             and lower.count('$tradingcredential = $null') == 2 and lower.count('pop-location') == 1
             and lower.rfind('[environment]::getenvironmentvariable($name)') > lower.find('finally {'))
    try:
        conflict=lower.find('[environment]::getenvironmentvariable($name)')
        host_pre=lower.find('assert-hostsafe',lower.find('# host/task'))
        push=lower.find('push-location $repo'); halt_pre=lower.find('assert-killswitchhalted',lower.find('try {'))
        ro_store=lower.find('"credential-store.ps1")'); tr_store=lower.find('"trading-credential-store.ps1")')
        get_ro=lower.find('get-readonlycredential',ro_store); get_tr=lower.find('get-tradingcredential',tr_store)
        compare=lower.find('finam_real_account_id -cne'); assign=lower.find('$env:finam_8107_trading_api_secret')
        child=lower.find('tradingsystemlab.stage8_robot.trading_token_intel_acceptance',assign)
        halt_post=lower.find('assert-killswitchhalted',child); host_post=lower.find('assert-hostsafe',halt_post)
        finally_at=lower.find('finally {'); remove=lower.find('remove-item "env:$name"',finally_at)
        nulling=lower.find('$readonlycredential = $null',remove); pop=lower.find('pop-location',nulling)
        confirm=lower.find('[environment]::getenvironmentvariable($name)',pop)
        ordering=conflict < host_pre < push < halt_pre < ro_store < tr_store < get_ro < get_tr < compare < assign < child < halt_post < host_post < finally_at < remove < nulling < pop < confirm and conflict >= 0
    except ValueError: ordering=False
    return session_only,kill_switch,credential_safe,runtime_safe and ordering,report_contract,cleanup

def audit(write_result=True,readme_text=None,authority_text=None,tracked_files=None,source_overrides=None):
    errors=[]; checks=0
    def check(ok,name):
        nonlocal checks; checks+=1
        if not ok: errors.append(name)
    spec=load_frozen_specification()
    check(spec.production_id==PRODUCTION_SPECIFICATION_ID,"SPEC_ID"); check(spec.identity=="TRAIL1__N4_01__FULL__R15","IDENTITY")
    check(spec.strategy["name"]=="T3" and spec.strategy["timeframe"]=="H1","T3_H1"); check(spec.variant["name"]=="TRAIL1","TRAIL1")
    check(spec.instruments==("USDRUBF","CNYRUBF","GLDRUBF","IMOEXF"),"N4"); check(spec.risk_fraction==.015 and spec.maximum_nominal_risk==.06,"R15_MAX")
    core=(HERE/"strategy_core.py").read_text(); config=(HERE/"config.py").read_text(); broker=(HERE/"broker.py").read_text(); state=(HERE/"state.py").read_text(); runner=(HERE/"runner.py").read_text(); api=(HERE/"finam_api.py").read_text(); historical=(HERE/"historical_conformance.py").read_text(); production=(HERE/"production_replay.py").read_text(); resolver=(HERE/"instrument_resolver.py").read_text(); smoke=(HERE/"demo_smoke.py").read_text(); updater=(HERE/"update_demo_registry.py").read_text()
    margin=(HERE/"margin.py").read_text(); funding_diagnostic=(HERE/"funding_margin_diagnostic.py").read_text(); real_smoke=(HERE/"real_account_smoke.py").read_text(); real_updater=(HERE/"update_real_registry.py").read_text(); operations=(HERE/"operations.py").read_text(); preflight=(HERE/"server_preflight.py").read_text()
    backup=(HERE/"backup_state.py").read_text(); restore=(HERE/"restore_state.py").read_text()
    supervisor_path=HERE/"readonly_supervisor.py"; supervisor=supervisor_path.read_text() if supervisor_path.is_file() else ""
    timing_path=HERE/"h1_timing_diagnostic.py"; timing=timing_path.read_text() if timing_path.is_file() else ""
    launcher=(HERE/"deploy/windows/run-readonly.ps1").read_text()
    trading_store=(HERE/"deploy/windows/trading-credential-store.ps1").read_text(); trading_init=(HERE/"deploy/windows/initialize-trading-credentials.ps1").read_text(); trading_verify=(HERE/"deploy/windows/verify-trading-credentials.ps1").read_text()
    credential_store=(HERE/"deploy/windows/credential-store.ps1").read_text(); credential_init=(HERE/"deploy/windows/initialize-readonly-credentials.ps1").read_text(); credential_verify=(HERE/"deploy/windows/verify-readonly-credentials.ps1").read_text(); task_installer=(HERE/"deploy/windows/install-task.ps1").read_text()
    conformance=json.loads((HERE/"conformance_report.json").read_text()); provenance=json.loads(authority_text if authority_text is not None else (HERE/"authority_provenance.json").read_text()); registry=(HERE/"production_instrument_registry.csv").read_text(); registry_rows=csv_rows(HERE/"production_instrument_registry.csv")
    source_overrides=source_overrides or {}
    def document(relative,path):
        canonical = path.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
        return source_overrides.get(
            relative,
            source_overrides.get(str(path.relative_to(ROOT)), canonical),
        )
    acceptance=document("controlled_real_acceptance.py",HERE/"controlled_real_acceptance.py")
    position_reconcile = acceptance.split("def _reconcile_position",1)[1].split("def _reconcile(",1)[0]
    normal_lifecycle = acceptance.split("def run_controlled_lifecycle",1)[1].split("_PREFLIGHT_KEYS",1)[0]
    finam_api=document("finam_api.py",HERE/"finam_api.py")
    acceptance_integration=document("tests/test_controlled_real_acceptance_finam_integration.py",
                                    HERE/"tests/test_controlled_real_acceptance_finam_integration.py")
    evidence_schema=json.loads(document("stage8_11_physical_evidence.schema.json",HERE/"stage8_11_physical_evidence.schema.json"))
    current_state=document("CURRENT_STATE.md",ROOT/"TradingSystemLab/CURRENT_STATE.md")
    project_context=document("PROJECT_CONTEXT.md",ROOT/"TradingSystemLab/PROJECT_CONTEXT.md")
    readme=readme_text if readme_text is not None else document("README.md",HERE/"README.md")
    roadmap=document("ROADMAP.md",ROOT/"TradingSystemLab/ROADMAP.md")
    authoritative_docs=(current_state,project_context,readme,roadmap)
    closeout_docs="\n".join(authoritative_docs)
    document_verdicts=[_stage8_10_document_consistency(doc) for doc in authoritative_docs]
    check(all(verdict[0] for verdict in document_verdicts),"STAGE_8_10_CURRENT_HANDOFF_EXACT")
    check(all(verdict[1] for verdict in document_verdicts),"STAGE_8_10_HISTORICAL_SCOPE_CONSISTENT")
    check(all(verdict[2] for verdict in document_verdicts),"STAGE_8_10_NO_STALE_NEXT_GATE")
    # Stage 8.11 is audited as an isolated boundary, not merely a document status.
    check("request.quantity != MAX_ACCEPTANCE_QUANTITY" in acceptance and "MAX_ACCEPTANCE_QUANTITY = 1" in acceptance,
          "STAGE_8_11_EXACTLY_ONE_HARD_CAP")
    check("self.store.persist_intent" in acceptance and acceptance.find("self.store.persist_intent") < acceptance.find("self.api.place_order"),
          "STAGE_8_11_INTENT_BEFORE_POST")
    check("no retry: exactly one call" in acceptance and acceptance.count("self.api.place_order") == 1,
          "STAGE_8_11_NO_POST_RETRY")
    check(
          "POSITION_RECONCILIATION_MAX_OBSERVATIONS = 30" in acceptance
          and "POSITION_RECONCILIATION_SLEEP_SECONDS = 2.0" in acceptance
          and "def _reconcile_position" in acceptance
          and "broker.position_snapshot(finam_symbol)" in position_reconcile
          and "POSITION_RECONCILIATION_TIMEOUT" in position_reconcile
          and "POSITION_RECONCILIATION_UNEXPECTED_QUANTITY" in position_reconcile
          and "POSITION_RECONCILIATION_UNEXPECTED_OTHER_POSITION" in position_reconcile
          and "STAGE8_11_PRE_SUBMIT_ACCOUNT_NOT_CLEAN" in normal_lifecycle
          and "ENTRY_SUBMISSION_UNCERTAIN_POSITION_RECONCILE" in normal_lifecycle
          and "FLATTEN_SUBMISSION_UNCERTAIN_POSITION_RECONCILE" in normal_lifecycle
          and "expected_position=expected_position, pending_position=0" in normal_lifecycle
          and "expected_position=0, pending_position=expected_position" in normal_lifecycle
          and ".trades(" not in position_reconcile
          and ".order(" not in position_reconcile
          and ".orders(" not in position_reconcile
          and "cancel_order" not in position_reconcile
          and "broker.snapshot(" not in normal_lifecycle
          and "broker.cancel(" not in normal_lifecycle,
          "STAGE_8_11_POSITION_AUTHORITATIVE_RECONCILIATION")
    check("_digest(account_id) != accepted_account_hash.lower()" in acceptance
          and "heartbeat_account_hash" in acceptance, "STAGE_8_11_EXACT_ACCOUNT_BINDING")
    check("resolve_frozen_symbol(instrument)" in acceptance and "FINAM_SYMBOL_BINDING_INVALID" in acceptance,
          "STAGE_8_11_EXACT_N4_SYMBOL_BINDING")
    check(all(token in normal_lifecycle for token in (
          'classification="SYNTHETIC_PASS"',
          "entry_fill_proven=True",
          "one_contract_position_observed=True",
          "flatten_fill_proven=True",
          "_account_is_clean(final)",
          '"FINAL_RECONCILIATION_PASS"',
          '"HALTED"')),
          "STAGE_8_11_FILL_FLAT_HALTED_PASS")
    check("except FinamOrderRejected as exc:" in normal_lifecycle
          and "if not _account_is_clean(final):" in normal_lifecycle
          and 'classification="NOT_ACCEPTED_NO_EXECUTION"' in normal_lifecycle
          and 'failure_code="DEFINITIVE_REJECTION"' in normal_lifecycle,
          "STAGE_8_11_NO_FILL_REQUIRES_CLEAN_ACCOUNT_PROOF")
    check('final["unexpected_position_count"] == 0' in acceptance
          and 'if row_symbol != symbol and quantity != 0' in acceptance,
          "STAGE_8_11_FINAL_RECONCILIATION_ALL_POSITIONS")
    check('active = count_active_orders(order_rows)' in acceptance
          and "acceptance_ids" not in acceptance,
          "STAGE_8_11_FINAL_RECONCILIATION_ALL_ACTIVE_ORDERS")
    props=evidence_schema.get("properties",{}); gates=props.get("preflight_gate_outcomes",{})
    check(evidence_schema.get("additionalProperties") is False and gates.get("additionalProperties") is False
          and props.get("quantity",{}).get("const") == 1
          and {"attempt_id", "entry_fill_proven"}.issubset(evidence_schema.get("required",[])),
          "STAGE_8_11_EVIDENCE_PRIVACY_SCHEMA")
    check("controlled_real_acceptance" not in runner and "controlled_real_acceptance" not in supervisor
          and "controlled_real_acceptance" not in launcher and "controlled_real_acceptance" not in task_installer,
          "STAGE_8_11_NO_ROUTINE_OR_SCHEDULED_INTEGRATION")
    physical_entry=document("stage8_11_physical_acceptance.py",HERE/"stage8_11_physical_acceptance.py")
    physical_wrapper=document("deploy/windows/run-stage8-11-physical-acceptance.ps1",HERE/"deploy/windows/run-stage8-11-physical-acceptance.ps1")
    attempt3_entry=document("stage8_11_physical_acceptance_attempt3.py",HERE/"stage8_11_physical_acceptance_attempt3.py")
    attempt3_wrapper=document("deploy/windows/run-stage8-11-physical-acceptance-attempt3.ps1",HERE/"deploy/windows/run-stage8-11-physical-acceptance-attempt3.ps1")
    recovery=document("stage8_11_failed_attempt_recovery.py",HERE/"stage8_11_failed_attempt_recovery.py")
    attempt2_manual_recovery=document("stage8_11_attempt2_manual_recovery.py",HERE/"stage8_11_attempt2_manual_recovery.py")
    check(all(token in physical_entry for token in (
          'AUTHORIZATION_VALUE = "STAGE_8_11_ONE_CONTRACT_ACCEPTANCE_AUTHORIZED"',
          'INSTRUMENT = "CNYRUBF"', 'FINAM_SYMBOL = "CNYRUBF@RTSX"',
          'DIRECTION = "LONG"', 'QUANTITY = 1', 'run_controlled_lifecycle(',
          'initialize_stage8_11_acceptance_ledger(', 'create_stage8_11_acceptance_backup('))
          and "place_order(" not in physical_entry, "STAGE_8_11_PHYSICAL_CANONICAL_BOUNDARY")
    check("--accepted-commit" in physical_entry and "AcceptedCommit" in physical_wrapper
          and "readonly_supervisor --runtime-root $runtime --once" in physical_wrapper
          and "Get-ScheduledTask" in physical_wrapper and "W32Time" in physical_wrapper,
          "STAGE_8_11_PHYSICAL_MANUAL_OPERATOR_PREFLIGHT")
    check('PRECHECK_EVIDENCE_SHA256 = "7171B7CD0098FF51159DC05C46C0326BF7F412A2D9EA0CBB3F9BDAFBE7745455"' in physical_entry
          and "precheck_report.is_file()" in physical_entry
          and "hashlib.sha256(precheck_report.read_bytes())" in physical_entry,
          "STAGE_8_11_FROZEN_PRECHECK_PROVENANCE")
    check('final.get("position_quantity", 0)' not in physical_entry
          and 'final.get("active_order_count", 0)' not in physical_entry
          and 'authority.unresolved_intent_count' not in physical_entry.split("def _physical_evidence",1)[1].split("def execute_boundary",1)[0],
          "STAGE_8_11_UNKNOWN_FINAL_STATE_NOT_SAFE_ZERO")
    check("$timeStatusExitCode = $LASTEXITCODE" in physical_wrapper
          and "$timeSourceExitCode = $LASTEXITCODE" in physical_wrapper,
          "STAGE_8_11_WINDOWS_TIME_EXIT_CODES")
    check("emergency_halt(Path" in physical_wrapper, "STAGE_8_11_PARENT_WRAPPER_HALT_DEFENSE")
    check('ATTEMPT_ID = STAGE8_11_ATTEMPT2_ID' in physical_entry
          and 'REPORT_NAME = "stage8_11_physical_acceptance_attempt2.json"' in physical_entry
          and 'HISTORICAL_REPORT_NAME = "stage8_11_physical_acceptance.json"' in physical_entry
          and 'attempt_id=ATTEMPT_ID' in physical_entry
          and '--attempt-id' not in physical_entry and 'os.replace(' not in physical_entry
          and 'os.link(temporary, destination)' in physical_entry,
          "STAGE8_11_ATTEMPT2_FIXED_CREATE_ONLY_EVIDENCE")
    check('attempt_id=ATTEMPT_ID' in physical_entry
          and 'stage8.11.attempt2' in acceptance and 'stage8.11.attempt3' in acceptance
          and 'intent_prefix = attempt_id or "stage8.11"' in acceptance
          and 'stage8_11_physical_acceptance_attempt2.json' in physical_wrapper
          and 'stage8_11_physical_acceptance.json"' not in physical_wrapper
          and 'ATTEMPT_ID = STAGE8_11_ATTEMPT3_ID' in attempt3_entry
          and 'REPORT_NAME = "stage8_11_physical_acceptance_attempt3.json"' in attempt3_entry
          and 'PREVIOUS_EVIDENCE_SHA256 = "0954B5C3D62444BA9AE59519386B0FC454D85C987BE1BAC04B82CA6C671B15A0"' in attempt3_entry
          and 'PREVIOUS_ENTRY_KEY = "stage8.11.attempt2:CNYRUBF:entry"' in attempt3_entry
          and '_reconcile_previous_attempt' in attempt3_entry
          and 'stage8_11_physical_acceptance_attempt3.json' in attempt3_wrapper
          and 'stage8_11_physical_acceptance_attempt3' in attempt3_wrapper
          and 'os.replace(' not in attempt3_entry and 'os.link(temporary, destination)' in attempt3_entry
          and 'RECONCILIATION_MAX_OBSERVATIONS = 12' in acceptance
          and 'RECONCILIATION_ACTIVE_GRACE_OBSERVATIONS = 3' in acceptance
          and 'class ReconciliationPending' in acceptance
          and '"trade_propagation_pending": len(matching) < executed' in acceptance
          and 'ack_position_proven = (' in acceptance
          and 'observation + 1 >= RECONCILIATION_ACTIVE_GRACE_OBSERVATIONS' in acceptance,
          "STAGE8_11_ATTEMPT2_DISTINCT_FIXED_INTENT_AND_WRAPPER_BINDING")
    check(
          'ATTEMPT2_EVIDENCE_SHA256 = "0954B5C3D62444BA9AE59519386B0FC454D85C987BE1BAC04B82CA6C671B15A0"' in attempt2_manual_recovery
          and 'ATTEMPT2_INTENT_KEY = "stage8.11.attempt2:CNYRUBF:entry"' in attempt2_manual_recovery
          and 'ATTEMPT2_ACCEPTED_CODE_COMMIT = "8857f3a01a060360a33f5909a9020201d3ade502"' in attempt2_manual_recovery
          and 'ATTEMPT2_EXECUTED_STATUSES = frozenset({"FILLED", "EXECUTED"})' in attempt2_manual_recovery
          and "_validate_attempt2_physical_evidence(_load_json(previous), account_id=account_id)" in attempt2_manual_recovery
          and '"order_endpoint_call_count": 1' in attempt2_manual_recovery
          and '"broker_order_present": True' in attempt2_manual_recovery
          and '"one_contract_position_observed": False' in attempt2_manual_recovery
          and '"final_position_quantity": 1' in attempt2_manual_recovery
          and '"final_active_order_count": 0' in attempt2_manual_recovery
          and '"unresolved_intent_count": 1' in attempt2_manual_recovery
          and '"physical_result_classification": "OPERATOR_INTERVENTION_REQUIRED"' in attempt2_manual_recovery
          and "count_nonzero_positions(positions)" in attempt2_manual_recovery
          and "count_active_orders(orders)" in attempt2_manual_recovery
          and 'request.get("client_order_id") != payload.get("client_order_id")' in attempt2_manual_recovery
          and 'broker_status not in ATTEMPT2_EXECUTED_STATUSES' in attempt2_manual_recovery
          and "UPDATE intents SET status='CLOSED'" in attempt2_manual_recovery
          and '"attempt2_reclassified_as_pass": False' in attempt2_manual_recovery
          and '"manual_close_history_preserved": True' in attempt2_manual_recovery
          and ".place_order(" not in attempt2_manual_recovery
          and ".cancel_order(" not in attempt2_manual_recovery
          and ".trades(" not in attempt2_manual_recovery
          and "stage8_11_attempt2_manual_recovery" in attempt3_wrapper
          and attempt3_wrapper.index("stage8_11_attempt2_manual_recovery") < attempt3_wrapper.index("$env:STAGE8_11_TRADING_SECRET")
          and "STAGE8_11_RECOVERY_READONLY_SECRET" in attempt3_wrapper
          and "STAGE8_11_RECOVERY_ACCOUNT_ID" in attempt3_wrapper
          and "ATTEMPT2_RECOVERY_EVIDENCE_NAME" in attempt3_entry
          and 'ATTEMPT2_RECOVERY_CODE_COMMIT = "8f614a73ec885f45cd159d350cab910e2a3b585c"' in attempt3_entry
          and 'recovery.get("recovery_code_commit") != ATTEMPT2_RECOVERY_CODE_COMMIT' in attempt3_entry
          and '$attempt2RecoveryCommit = "8f614a73ec885f45cd159d350cab910e2a3b585c"' in attempt3_wrapper
          and "--accepted-recovery-commit $attempt2RecoveryCommit" in attempt3_wrapper
          and "_reconcile(broker, PREVIOUS_ENTRY_KEY" not in attempt3_entry,
          "STAGE8_11_ATTEMPT2_MANUAL_RECOVERY_BOUNDARY")
    attempt2_physical=provenance.get("stage8_11_attempt2_physical",{})
    check(attempt2_physical.get("attempt_id") == "stage8.11.attempt2"
          and attempt2_physical.get("accepted_code_commit") == "8857f3a01a060360a33f5909a9020201d3ade502"
          and attempt2_physical.get("physical_evidence_sha256") == "0954B5C3D62444BA9AE59519386B0FC454D85C987BE1BAC04B82CA6C671B15A0"
          and attempt2_physical.get("entry_intent_status_at_evidence") == "ACK"
          and attempt2_physical.get("order_endpoint_call_count") == 1
          and attempt2_physical.get("final_position_quantity_observed") == 1
          and attempt2_physical.get("canonical_unresolved_intent_count") == 1
          and attempt2_physical.get("physical_result") == "OPERATOR_INTERVENTION_REQUIRED"
          and attempt2_physical.get("defect_classification") == "FINAM_READ_SIDE_EVENTUAL_CONSISTENCY"
          and attempt2_physical.get("operator_reported_manual_close_after_evidence") is True
          and attempt2_physical.get("corrective_retry_identity") == "stage8.11.attempt3"
          and attempt2_physical.get("stage8_12_activity") is False
          and 'FAILED_PHYSICAL_EVIDENCE_SHA256 = "9FEFC5469F2C97F1EB36A5B5C99D323FA37BB948CF53C8A8745A27A06AB3B324"' in recovery
          and 'HISTORICAL_INTENT_KEY = "stage8.11:CNYRUBF:entry"' in recovery
          and all("0954B5C3D62444BA9AE59519386B0FC454D85C987BE1BAC04B82CA6C671B15A0" in doc
                  and "OPERATOR_INTERVENTION_REQUIRED" in doc
                  and "stage8.11.attempt3" in doc
                  and "has not been physically executed" in doc for doc in authoritative_docs),
          "STAGE8_11_ATTEMPT1_IMMUTABLE_ATTEMPT2_PREPARED_ONLY")
    physical_tree=ast.parse(physical_entry)
    lifecycle_calls=[node for node in ast.walk(physical_tree) if isinstance(node,ast.Call)
                     and getattr(node.func,"id",None)=="run_controlled_lifecycle"]
    check(len(lifecycle_calls)==1
          and any(keyword.arg=="clock" for keyword in lifecycle_calls[0].keywords)
          and not any(keyword.arg=="now" for keyword in lifecycle_calls[0].keywords),
          "STAGE8_11_PHYSICAL_ENTRYPOINT_FRESH_CLOCK_PROPAGATION")
    check(props.get("order_endpoint_call_count",{}).get("maximum") == 2
          and acceptance.count("submit_entry(") == 2 and acceptance.count("submit_flatten(") == 3,
          "STAGE_8_11_MAXIMUM_TWO_POST_CAPABILITY")
    normal_owners="\n".join((runner,supervisor,task_installer,launcher))
    check("run-stage8-11-physical-acceptance.ps1" not in normal_owners,
          "STAGE_8_11_PHYSICAL_MANUAL_ONLY_AIRGAP")
    intel_precheck=document("stage8_11_intel_acceptance.py",HERE/"stage8_11_intel_acceptance.py")
    intel_wrapper=document("deploy/windows/run-stage8-11-intel-precheck.ps1",
                           HERE/"deploy/windows/run-stage8-11-intel-precheck.ps1")
    intel_calls={node.func.attr for node in ast.walk(ast.parse(intel_precheck))
                 if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)}
    check(not intel_calls.intersection({"place_order","cancel_order","modify_order","submit_order"})
          and 'MODE = "STAGE8_11_PRECHECK_ONLY"' in intel_precheck
          and '"execution_authorization_observed":False' in intel_precheck
          and '"order_endpoint_call_count":0' in intel_precheck,
          "STAGE_8_11_INTEL_PRECHECK_ORDER_INCAPABLE")
    check("stage8_11_intel_acceptance" not in runner and "stage8_11_intel_acceptance" not in supervisor
          and "stage8_11_intel_acceptance" not in launcher and "stage8_11_intel_acceptance" not in task_installer,
          "STAGE_8_11_INTEL_PRECHECK_MANUAL_ONLY")
    check("Get-TradingCredential" in intel_wrapper and "Get-ReadonlyCredential" in intel_wrapper
          and "$AcceptedCommit" in intel_wrapper and "Get-ScheduledTask" in intel_wrapper
          and "readonly_supervisor|stage8_robot\\.runner" in intel_wrapper
          and "backup_state" in intel_wrapper and "--direction" in intel_wrapper
          and "--execute" not in intel_wrapper,
          "STAGE_8_11_INTEL_WINDOWS_OPERATOR_SAFEGUARDS")
    check("select_candidate" in intel_precheck and "for instrument in N4" in intel_precheck
          and "required_readonly=False" in intel_precheck
          and "collect_funding_authority" in intel_precheck,
          "STAGE_8_11_INTEL_REUSES_FROZEN_SIZING_AUTHORITY")
    check("evaluate_new_entry_gate" in intel_precheck and "execution_authorized=False" in intel_precheck
          and 'EXPECTED_GATE_REASONS = ["KILL_SWITCH_HALTED", "EXECUTION_NOT_AUTHORIZED"]' in intel_precheck,
          "STAGE_8_11_INTEL_EXISTING_SAFETY_GATE_EXACT_BLOCKERS")
    state_source=document("state.py",HERE/"state.py")
    precheck_tests=document("tests/test_stage8_11_intel_acceptance.py",HERE/"tests/test_stage8_11_intel_acceptance.py")
    schema_tokens=('"idempotency_key","TEXT",0,None,1', '"status","TEXT",1,None,0',
                   '"updated_at","TEXT",1,"CURRENT_TIMESTAMP",0', '"fill_id","TEXT",0,None,1',
                   'tuple(connection.execute(f"PRAGMA table_info({table})")) != expected')
    check(all(token in state_source for token in schema_tokens)
          and "_validate_acceptance_schema(connection)" in state_source
          and "COALESCE(status,'') NOT IN" in state_source,
          "STAGE_8_11_EXACT_ACCEPTANCE_SCHEMA_AND_NULL_SAFE_UNRESOLVED")
    check(all(token in precheck_tests for token in (
          "test_same_column_family_mutated_constraints_fail_closed",
          "test_nullable_null_status_cannot_disappear_from_readonly_count",
          "ACCEPTANCE_SCHEMA_INVALID")), "STAGE_8_11_SCHEMA_MUTATION_COVERAGE")
    check("stage8_11_acceptance_path" in intel_precheck and "readonly_unresolved_intent_count(acceptance_path)" in intel_precheck
          and 'STAGE8_11_ACCEPTANCE_DATABASE = "stage8-11-acceptance.sqlite3"' in state_source
          and 'SUPERVISOR_DATABASE = "readonly-supervisor.sqlite3"' in state_source,
          "STAGE_8_11_SEPARATE_PERSISTENCE_AUTHORITIES")
    check("canonical_controlled_acceptance_broker" in acceptance and "stage8_11_acceptance_path(runtime_root)" in acceptance,
          "STAGE_8_11_PRECHECK_AND_ACCEPTANCE_SHARED_LEDGER")
    stage811_provenance=provenance.get("stage8_11",{})
    physical=stage811_provenance.get("physical_precheck",{})
    independent=stage811_provenance.get("independent_evidence_audit",{})
    physical_acceptance=stage811_provenance.get("physical_acceptance",{})
    stage812_provenance=provenance.get("stage8_12",{})
    check(all((
          stage811_provenance.get("stage8_11_0_status") == "COMPLETE",
          stage811_provenance.get("stage8_11_1_status") == "COMPLETE_PASS",
          stage811_provenance.get("stage8_11_2_status") == "COMPLETE_PASS",
          stage811_provenance.get("stage8_11_3_status") == "PRIOR_AUTHORIZATION_CONSUMED",
          stage811_provenance.get("current_gate") == "STAGE_8_12_4_EXPLICIT_FULL_R15_PRODUCTION_AUTHORIZATION",
          stage811_provenance.get("latest_physical_precheck_result") == "STAGE8_11_PRECHECK_ONLY_PASS",
          physical.get("accepted_code_commit") == "9be31f1723877a9c542f89027052570425f7e976",
          physical.get("report_sha256") == "7171B7CD0098FF51159DC05C46C0326BF7F412A2D9EA0CBB3F9BDAFBE7745455",
          physical.get("acceptance_ledger_sha256_observed") == "A83C93733321C696225F606A5DBE584413915DA3C46C2B4A261091EC85B7C354",
          physical.get("real_order_count") == 0,
          physical.get("order_endpoint_call_count") == 0,
          physical.get("execution_authorized") is False,
          physical.get("kill_switch") == "HALTED",
          physical.get("safety_gate_reasons") == ["KILL_SWITCH_HALTED", "EXECUTION_NOT_AUTHORIZED"],
          independent.get("result") == "STAGE_8_11_2_INDEPENDENT_PRECHECK_EVIDENCE_AUDIT_PASS",
          independent.get("acceptance_ledger_binary_independently_rehashed_off_intel_host") is False,
          stage811_provenance.get("status") == "STAGE_8_11_CONTROLLED_REAL_EXECUTION_ACCEPTANCE_COMPLETE_PASS",
          stage811_provenance.get("latest_physical_acceptance_result") == "PASS",
          stage811_provenance.get("latest_authorization_status") == "CONSUMED_AFTER_ATTEMPT7_PASS",
          physical_acceptance.get("schema_id") == "stage8_11_physical_acceptance.v1",
          physical_acceptance.get("attempt_id") == "stage8.11.attempt7",
          physical_acceptance.get("accepted_code_commit") == "72a910e49b876cda99484a810e6f8a1b16ac0209",
          physical_acceptance.get("evidence_sha256") == "704BFCC19B1A63F490192C0D8D0E4715BFECF77664296AFEF47E5B80FBF64B5F",
          physical_acceptance.get("instrument") == "CNYRUBF",
          physical_acceptance.get("finam_symbol") == "CNYRUBF@RTSX",
          physical_acceptance.get("direction") == "LONG",
          physical_acceptance.get("quantity") == 1,
          physical_acceptance.get("broker_fill_count") == 2,
          physical_acceptance.get("broker_order_present") is True,
          physical_acceptance.get("entry_fill_proven") is True,
          physical_acceptance.get("one_contract_position_observed") is True,
          physical_acceptance.get("controlled_flatten_proven") is True,
          physical_acceptance.get("order_endpoint_call_count") == 2,
          physical_acceptance.get("final_position_quantity") == 0,
          physical_acceptance.get("final_active_order_count") == 0,
          physical_acceptance.get("unresolved_intent_count") == 0,
          physical_acceptance.get("reconciliation_result") == "PASS",
          physical_acceptance.get("physical_result_classification") == "PASS",
          physical_acceptance.get("kill_switch_pre_state") == "ARMED",
          physical_acceptance.get("kill_switch_final_state") == "HALTED",
          physical_acceptance.get("scheduled_task_final_state") == "Disabled",
          physical_acceptance.get("stage8_12_status") == "NOT_STARTED_NOT_AUTHORIZED",
          stage811_provenance.get("execution_authorized") is False,
          stage811_provenance.get("order_endpoint_call_count") == 2,
          stage811_provenance.get("real_order_count") == 2,
          stage811_provenance.get("production_kill_switch_final_state") == "HALTED",
          stage811_provenance.get("stage8_12_status") == "STAGE_8_12_4_STARTED_IMPLEMENTATION_NOT_AUTHORIZED",
          stage811_provenance.get("current_precheck_code_authority") == {
              "pull_request":357,"base":"ea090d99266d5dae808c03024f327c41fb8b9170",
              "head":"60e3f72dae3a08eeb3ba8c756861efbb4c4f28e7",
              "merge":"f29053e2c4b5f687115f0a5b12f582e822b60ea1"},
          stage811_provenance.get("exact_ledger_schema_hardening_authority",{}).get("pull_request") == 358,
          stage811_provenance.get("operator_boundary_predecessor_authority") == {
              "pull_request":360,"base":"cc1508e87c0cfc1994352761aa800da58751c132",
              "head":"a233ebd9c1d56d85e6878389b3e4fb86a0054683",
              "merge":"a54465d84b4eddabff38519011e8a26eafbfdd6d"},
          stage811_provenance.get("production_readiness_findings") == [
              "STAGE8_11_PHYSICAL_EVIDENCE_UNPROVEN_STATE_DEFAULTED_SAFE",
              "STAGE8_11_NO_FILL_FLAT_STATE_NOT_PROVEN"],
          stage811_provenance.get("physical_wrapper_run") is True,
          len(stage811_provenance.get("historical_failed_prechecks",[])) == 2,
    )), "STAGE_8_11_LIFECYCLE_EVIDENCE_CLOSEOUT")
    stage812_expected = {
        "status":"STAGE_8_12_STARTED_STAGE8_12_4_IMPLEMENTATION_NOT_AUTHORIZED",
        "stage8_12_1_status":"STAGE_8_12_1_PRODUCTION_RUNTIME_ASSEMBLY_COMPLETE_PASS",
        "accepted_code_commit":"3f2d68ca0c327271fb543a0b63c0e8f842c855bd",
        "external_test_only_evidence_sha256":"F11FD6620A21F48499600392F49D3FC8A2340765B2B7B1C3C190822D8316513C",
        "stage8_12_2_status":"STAGE_8_12_2_PRODUCTION_PATH_CONFORMANCE_AND_FAILURE_AUDIT_COMPLETE_PASS",
        "stage8_12_2_accepted_code_commit":"2a15f4331afc1433dfbfd0464108e39e59d236f8",
        "stage8_12_2_external_test_only_evidence_sha256":"4F58595E2F62F2A377E5525972B9E88A136B2F9BC51760268D012AF94A70AE9F",
        "stage8_12_3_status":"STAGE_8_12_3_INTEL_PRODUCTION_PREFLIGHT_COMPLETE_PASS",
        "stage8_12_3_accepted_code_commit":"0a40e3bf7a97f0c011d3a6f5216d9f61dd52ef30",
        "stage8_12_3_external_evidence_sha256":"9584F45186DE38ABAE9209E1F326255C783AF762CD736EA45718D19C93BC61B1",
        "stage8_12_3_physical_result":"STAGE_8_12_3_INTEL_PRODUCTION_PREFLIGHT_PASS",
        "stage8_12_3_focused_zero_order_regression":{"passed":205,"failed":0},
        "stage8_12_3_order_endpoint_call_count":0,
        "stage8_12_3_real_order_count":0,
        "stage8_12_3_execution_authorized":False,
        "stage8_12_3_production_kill_switch_final_state":"HALTED",
        "stage8_12_4_status":"STARTED_IMPLEMENTATION_NOT_AUTHORIZED",
        "next_gate":"STAGE_8_12_4_EXPLICIT_FULL_R15_PRODUCTION_AUTHORIZATION",
        "execution_authorized":False,
        "live_trading_authorized":False,
        "real_order_transmission_authorized":False,
        "production_kill_switch_final_state":"HALTED",
        "production_scheduled_task":"Disabled",
        "mode":"STAGE8_12_4_IMPLEMENTATION_CODE_ONLY_NOT_AUTHORIZED",
    }
    check(all(stage812_provenance.get(key) == value for key,value in stage812_expected.items())
          and stage812_provenance.get("stage8_12_4_authorization_foundation") == {
              "status":"CODE_READY_PENDING_ZERO_ORDER_VALIDATION",
              "durable_authorization_schema":"stage8_12_4_production_authorization.v1",
              "durable_authorization_repository_external":True,
              "explicit_operator_phrase_required":True,
              "exact_commit_binding_required":True,
              "exact_account_hash_binding_required":True,
              "stage8_12_2_evidence_binding":"4F58595E2F62F2A377E5525972B9E88A136B2F9BC51760268D012AF94A70AE9F",
              "stage8_12_3_evidence_binding":"9584F45186DE38ABAE9209E1F326255C783AF762CD736EA45718D19C93BC61B1",
              "production_heartbeat_schema":"stage8_12_4_production_heartbeat.v1",
              "finam_sltp_endpoint":"POST /v1/accounts/{account_id}/sltp-orders",
              "entry_requires_armed_production_gate":True,
              "protection_and_emergency_exit_remain_available_after_halt":True,
              "automatic_authorization_creation":False,
              "automatic_kill_switch_arm":False,
              "production_task_enabled":False,
              "production_task_started":False,
              "real_order_count":0,
              "production_service_prerequisites":{
                  "status":"CODE_READY_PENDING_ZERO_ORDER_VALIDATION",
                  "stage5_data_commit":"50f1fd2178c18b7ab3bd969be82ad01f47a34745",
                  "h1_seed_source_sha256":{
                      "USDRUBF":"f0ca366d816a6213742271242e87c53d1e23f5a5fc4655df0123217df418a226",
                      "CNYRUBF":"a3815b88a11aa5878b8bd104140f002859349c2c8d7f6ff0476a0d4c4d9a612e",
                      "GLDRUBF":"12a626ba6cc47fce2f392d4a6ce3bdb8a3c1aad074306a73ab480fcfbb83b87e",
                      "IMOEXF":"119878c12f602924296ab27b5b9f3cf51fa54f1a9370793892edbea58003e110",
                  },
                  "h1_seed_semantics":"STAGE5_FOREVER_OPEN_TIME_EUROPE_MOSCOW_PLUS_1H_CLOSE_INDEX",
                  "finam_h1_splice":"EXACT_TIMESTAMP_AND_OHLC_OVERLAP_REQUIRED",
                  "broker_state_parser":"STRICT_READ_SIDE_REGULAR_AND_SLTP",
                  "restart_intent_read_authority":True,
                  "order_transmission_added_by_this_layer":False,
                  "execution_authorized":False,
                  "real_order_count":0,
              },
          },
          "STAGE_8_12_CURRENT_MACHINE_AUTHORITY_EXACT")

    stage8124_authorization=(HERE/"production_authorization.py").read_text()
    stage8124_live=(HERE/"live_execution.py").read_text()
    stage8124_gate=(HERE/"production_safety_gate.py").read_text()
    stage8124_wrapper=(HERE/"deploy/windows/run-stage8-12-4-foundation-validation.ps1").read_text()
    check(all(token in stage8124_authorization for token in (
              'AUTHORIZATION_SCHEMA = "stage8_12_4_production_authorization.v1"',
              'OPERATOR_AUTHORIZATION_PHRASE = "AUTHORIZE_STAGE8_12_4_FULL_R15_PRODUCTION"',
              'STAGE8_12_4_REPOSITORY_AUTHORIZATION_FORBIDDEN',
              'STAGE8_12_4_EXPLICIT_OPERATOR_AUTHORIZATION_REQUIRED',
              'os.link(temporary, destination)',
              'STAGE8_12_4_AUTHORIZATION_BINDING_MISMATCH',
              '4F58595E2F62F2A377E5525972B9E88A136B2F9BC51760268D012AF94A70AE9F',
              '9584F45186DE38ABAE9209E1F326255C783AF762CD736EA45718D19C93BC61B1')),
          "STAGE_8_12_4_DURABLE_AUTHORIZATION_EXACT")
    authorization_calls={node.func.attr for node in ast.walk(ast.parse(stage8124_authorization))
                         if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)}
    check(not authorization_calls.intersection({"place_order","place_sltp_order","cancel_order","create_session"}),
          "STAGE_8_12_4_AUTHORIZATION_NO_BROKER_CAPABILITY")
    check(all(token in stage8124_live for token in (
              "load_authorization(", "evaluate_production_entry_gate(",
              "self.api.place_order(", "self.api.place_sltp_order(",
              "STAGE8_12_4_PROTECTIVE_STOP_CANCEL_REQUIRES_FLAT",
              "TIME_IN_FORCE_DAY")),
          "STAGE_8_12_4_AUTHORIZED_TRANSPORT_GATES")
    check("write_kill_switch" not in stage8124_live and "allow_arm" not in stage8124_live
          and "Enable-ScheduledTask" not in stage8124_live and "Start-ScheduledTask" not in stage8124_live,
          "STAGE_8_12_4_TRANSPORT_CANNOT_SELF_AUTHORIZE_OR_ACTIVATE")
    check(all(token in stage8124_gate for token in (
              'PRODUCTION_HEARTBEAT_SCHEMA = "stage8_12_4_production_heartbeat.v1"',
              '"KILL_SWITCH_NOT_ARMED"', '"EXECUTION_NOT_AUTHORIZED"',
              '"UNRESOLVED_PRODUCTION_INTENTS_PRESENT"',
              '"PRODUCTION_POSITION_PROTECTION_INVALID"',
              "position_protection", "expected_position_quantity", "covered_quantity",
              "active_stop_order_ids") ),
          "STAGE_8_12_4_PRODUCTION_AWARE_ENTRY_GATE")
    wrapper_lower=stage8124_wrapper.lower()
    check(all(token in stage8124_wrapper for token in (
              "STAGE8_12_4_AUTHORIZATION_MUST_BE_ABSENT",
              'if ($kill.state -cne "HALTED")',
              "STAGE8_12_4_FOUNDATION_VALIDATION_PASS=true",
              "STAGE8_12_4_REAL_ORDER_COUNT=0"))
          and not any(token in wrapper_lower for token in (
              "get-tradingcredential","trading-credential-store","enable-scheduledtask",
              "start-scheduledtask","allow_arm","finam_api_secret")),
          "STAGE_8_12_4_FOUNDATION_VALIDATOR_ZERO_ORDER_BOUNDARY")

    stage8124_history=(HERE/"production_history.py").read_text()
    stage8124_broker_state=(HERE/"production_broker_state.py").read_text()
    check(all(token in stage8124_history for token in (
              'STAGE5_DATA_COMMIT = "50f1fd2178c18b7ab3bd969be82ad01f47a34745"',
              '"USDRUBF": "f0ca366d816a6213742271242e87c53d1e23f5a5fc4655df0123217df418a226"',
              '"CNYRUBF": "a3815b88a11aa5878b8bd104140f002859349c2c8d7f6ff0476a0d4c4d9a612e"',
              '"GLDRUBF": "12a626ba6cc47fce2f392d4a6ce3bdb8a3c1aad074306a73ab480fcfbb83b87e"',
              '"IMOEXF": "119878c12f602924296ab27b5b9f3cf51fa54f1a9370793892edbea58003e110"',
              "completed_h1_bars(", "seed_overlap.index.equals(live_overlap.index)",
              "STAGE8_12_4_H1_SPLICE_OHLC_MISMATCH", 'pd.Timedelta("1h")')),
          "STAGE_8_12_4_FROZEN_H1_WARMUP_PROVENANCE")
    history_tree=ast.parse(stage8124_history)
    history_calls={node.func.attr for node in ast.walk(history_tree)
                   if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)}
    check(not history_calls.intersection({"place_order","place_sltp_order","cancel_order","submit_order"}),
          "STAGE_8_12_4_HISTORY_ORDER_INCAPABLE")
    check(all(token in stage8124_broker_state for token in (
              "position_quantities(", "normalize_order_status(",
              '"SLTP_QTY_MEASURE_PERCENT"', "unique_order_by_client_id(",
              "active_sltp_for_trade(")),
          "STAGE_8_12_4_STRICT_BROKER_STATE_PARSER")
    broker_state_tree=ast.parse(stage8124_broker_state)
    broker_state_calls={node.func.attr for node in ast.walk(broker_state_tree)
                        if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)}
    check(not broker_state_calls.intersection({"place_order","place_sltp_order","cancel_order","create_session"}),
          "STAGE_8_12_4_BROKER_STATE_READ_PARSER_ONLY")
    check("def all_intents(self)" in state_source and "def unresolved_intents(self)" in state_source
          and "COALESCE(status,'') NOT IN" in state_source,
          "STAGE_8_12_4_RESTART_INTENT_READ_AUTHORITY")

    stage8124_service=(HERE/"production_service.py").read_text()
    stage8124_production_launcher=(HERE/"deploy/windows/run-production.ps1").read_text()
    stage8124_production_installer=(HERE/"deploy/windows/install-production-task.ps1").read_text()
    ast.parse(stage8124_service)
    check(all(token in stage8124_service for token in (
              'STATE_DATABASE = "stage8-12-production.sqlite3"',
              "H1_LOOKBACK_DAYS = 30",
              "load_stage5_seed_open_h1", "splice_seed_and_finam_open_h1",
              "newest_expected_h1_close", "self.runtime.context_builder.build",
              "directional_initial_margin", "evaluate_production_entry_gate",
              "write_production_heartbeat", "InstanceLock",
              "equity - unrealized - explained")),
          "STAGE_8_12_4_PACKAGE2_CONTINUOUS_SERVICE_WIRING")
    service_tree=ast.parse(stage8124_service)
    service_calls={node.func.attr for node in ast.walk(service_tree)
                   if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)}
    check(not service_calls.intersection({"place_order","place_sltp_order","cancel_order","write_authorization","write_kill_switch"})
          and "if authorization_path(self.root).exists()" in stage8124_service
          and "self.transport = None" in stage8124_service,
          "STAGE_8_12_4_PACKAGE2_UNAUTHORIZED_ZERO_ORDER_CONSTRUCTION")
    check('"signal_timestamp": signal.timestamp.isoformat()' in production_runtime
          and 'watermark_key = f"last_managed_h1:{payload[\'instrument\']}"' in production_runtime
          and "ENTRY_SIGNAL_WATERMARK_MISMATCH" in production_runtime,
          "STAGE_8_12_4_PACKAGE2_ENTRY_CANDLE_CAUSALITY")
    installer_lower=stage8124_production_installer.lower()
    check(all(token in stage8124_production_installer for token in (
              "TradingSystemLab-Stage8-Production",
              "TradingSystemLab-Stage8-Readonly",
              "STAGE8_12_4_READONLY_TASK_MUST_REMAIN_DISABLED",
              "Disable-ScheduledTask",
              "STAGE8_12_4_PRODUCTION_TASK_INSTALLED_DISABLED"))
          and "enable-scheduledtask" not in installer_lower
          and "start-scheduledtask" not in installer_lower,
          "STAGE_8_12_4_PACKAGE2_PRODUCTION_TASK_INSTALLED_DISABLED")
    launcher_lower=stage8124_production_launcher.lower()
    check(all(token in stage8124_production_launcher for token in (
              "trading-credential-store.ps1",
              '$env:FINAM_MODE = "STAGE8_12_PRODUCTION"',
              "--accepted-commit", "--stage5-data-root", "--once",
              "50f1fd2178c18b7ab3bd969be82ad01f47a34745"))
          and "run-readonly.ps1" not in launcher_lower
          and "write_authorization" not in launcher_lower
          and "write_kill_switch" not in launcher_lower,
          "STAGE_8_12_4_PACKAGE2_EXACT_COMMIT_TRADING_DPAPI_LAUNCHER")
    check("OperationalState(root/\"state/readonly-supervisor.sqlite3\")" in precheck_tests
          and "StateStore(root/\"state/readonly-supervisor.sqlite3\")" not in precheck_tests
          and '== {"operational_state"}' in precheck_tests,
          "STAGE_8_11_PRODUCTION_REALISTIC_SUPERVISOR_FIXTURE")
    check('f"{instrument}@RTSX"' not in intel_precheck and "load_registry(registry_path)" in intel_precheck
          and "AUTHENTICATED_REAL_READONLY" in intel_precheck and 'trading_status != "TRADABLE"' in intel_precheck,
          "STAGE_8_11_INTEL_FROZEN_REGISTRY_SYMBOL")
    check("w32tm /query /status" in intel_wrapper and "w32tm /query /source" in intel_wrapper
          and "Get-Service -Name W32Time" in intel_wrapper and "$clock = (Get-Date)" not in intel_wrapper,
          "STAGE_8_11_INTEL_WINDOWS_TIME_SANITY")
    check("LIVE_TRADING_NOT_AUTHORIZED" in config and "REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED" in broker,
          "STAGE_8_11_EXISTING_AIRGAPS_INTACT")
    api_methods={node.name for node in ast.parse(finam_api).body
                 if isinstance(node,ast.ClassDef) and node.name=="FinamAPI"
                 for node in node.body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))}
    acceptance_api_calls={node.func.attr for node in ast.walk(ast.parse(acceptance))
                          if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)
                          and (isinstance(node.func.value,ast.Name) and node.func.value.id=="api"
                               or isinstance(node.func.value,ast.Attribute)
                               and isinstance(node.func.value.value,ast.Name)
                               and node.func.value.value.id=="self" and node.func.value.attr=="api")}
    check(acceptance_api_calls <= api_methods
          and "acceptance_snapshot" not in acceptance and "acceptance_account_snapshot" not in acceptance,
          "STAGE_8_11_PRODUCTION_FINAM_API_CONTRACT")
    check('return _rows(account, "positions")' in acceptance and '_rows(account, "trades")' not in acceptance,
          "STAGE_8_11_TRADES_NOT_FROM_ACCOUNT")
    check("def trades(self,account_id)" in finam_api
          and 'f"/v1/accounts/{account_id}/trades"' in finam_api,
          "STAGE_8_11_FINAM_TRADES_PRIMITIVE")
    check("filled_quantity" not in acceptance and 'order.get("executed_quantity")' in acceptance,
          "STAGE_8_11_DOCUMENTED_EXECUTED_QUANTITY")
    check(all(token in acceptance for token in (
              "_REST_TIMESTAMP.fullmatch(value)", "not isinstance(value, str)",
              "datetime.fromisoformat", ".astimezone(timezone.utc)",
              '_timestamp(order.get("accept_at"))', '_timestamp(trade.get("timestamp"))')),
          "STAGE_8_11_REST_TIMESTAMP_STRING_AUTHORITY")
    check('prefix + "/trades"' in acceptance_integration
          and '"order":{"account_id":ACCOUNT' in acceptance_integration
          and '"executed_quantity":self.decimal(executed)' in acceptance_integration
          and '"accept_at":"2026-10-04T09:00:02Z"' in acceptance_integration
          and '"timestamp":"2026-10-04T09:00:03Z"' in acceptance_integration
          and "test_rest_timestamp_parser_rejects_unsupported_or_invalid_values" in acceptance_integration
          and '{"seconds":1,"nanos":0}' in acceptance_integration,
          "STAGE_8_11_EXACT_REST_SYNTHETIC_TRANSPORT")
    completed_status="STAGE_8_8_6_SQLITE_RECOVERY_INTEL_ACCEPTANCE_COMPLETE"
    accepted_code_sha="dc2b79e74817e71435eee20103ae617e13067d8e"
    evidence_sha="1A9B62D4BFC0E7384898C9DF9659E54E50E0E202BD44CE19413864AC2ECA14D6"
    tracked=(tracked_files if tracked_files is not None else subprocess.run(["git","ls-files","-z"],cwd=ROOT,check=True,capture_output=True).stdout.decode().split("\0"))
    check(all(completed_status in document and "STAGE_8_8_6_SQLITE_RECOVERY_CODE_READY_PENDING_INTEL_ACCEPTANCE" not in document
              for document in (current_state,readme,roadmap)),"STAGE_8_8_6_COMPLETED_STATUS_SYNCHRONIZED")
    check(all(accepted_code_sha in document for document in (current_state,readme,roadmap)),"STAGE_8_8_6_ACCEPTED_CODE_SHA_RECORDED")
    check(all(evidence_sha in document for document in (current_state,readme,roadmap)),"STAGE_8_8_6_EXTERNAL_EVIDENCE_SHA_RECORDED")
    check(not any("stage8_8_6_sqlite_recovery_acceptance.json" in path.lower()
                  or (Path(path).name.lower() in {"stage8_10_3_identity_account_binding.json","stage8_10_4_permission_boundary.json"})
                  or (("stage8_9" in path.lower() or "funding_margin_validation" in path.lower())
                      and path.lower().endswith(".json"))
                  or path.lower().endswith((".sqlite3","-wal","-shm",".dpapi",".jwt"))
                  or (any(term in Path(path.lower()).name for term in
                          ("trading_token","trading-token","token_1","token1","account_id","account-identifier"))
                      and path.lower().endswith((".json",".txt",".bin",".blob",".env")))
                  for path in tracked),
          "STAGE_8_8_6_RAW_EXTERNAL_AND_RUNTIME_MATERIAL_NOT_TRACKED")
    final_status="STAGE_8_8_7_FINAL_OPERATIONAL_AUDIT_INTEL_ACCEPTANCE_COMPLETE"
    final_code_sha="bda46f57f0f977e05593c46b55851c40c4ad34fe"
    final_evidence_sha="181225F29A966179AB513121C3CBACD31401752956EFC9A22253A8EFBF94766E"
    check(all(final_status in document and final_code_sha in document and final_evidence_sha in document
              for document in (current_state,readme,roadmap)),"STAGE_8_8_7_COMPLETED_PROVENANCE_SYNCHRONIZED")
    stage8_9_status="STAGE_8_9_REAL_ACCOUNT_FUNDING_MARGIN_VALIDATION_COMPLETE"; stage8_9_reason="ALL_AUTHORITIES_VALID"
    stage8_9_code="1013a5a2324e015ab3bc047a7b9af9064552cd10"
    stage8_9_report="C87400F845B73A666B95C83DA2E3B6B710F36F3210AD4AD175BFDABB453864D5"
    stage8_9_summary="099F85A0DCCF94D404411CFFAC2F5D8C80D606C5C1B5AA2F5B650E8BF5FEB636"
    stage8_9_8_status="STAGE_8_9_8_COMPLETE"
    required=(stage8_9_status,stage8_9_reason,stage8_9_code,stage8_9_report,stage8_9_summary,
              "STAGE_8_9_10_POST_FUNDING_REVALIDATION_PASS=1",
              "sizing_case_count = 8",
              "positive_capacity_case_count = 4","zero_capacity_case_count = 4",
              "positive_batch_reservation_count = 1")
    check(all(all(value in document for value in required)
              for document in authoritative_docs),
          "STAGE_8_9_10_COMPLETED_PROVENANCE_SYNCHRONIZED")
    lifecycle=provenance.get("stage8_9_8",{}); closeout=provenance.get("stage8_9_10",{}); preconditions=provenance.get("stage8_10_1",{}); provisioning=provenance.get("stage8_10_2",{}); identity_binding=provenance.get("stage8_10_3",{}); permission_boundary=provenance.get("stage8_10_4",{}); dry_gate=provenance.get("stage8_10_5",{}); safety_gate=provenance.get("stage8_10_6",{}); token_acceptance=provenance.get("stage8_10_7",{}); lifecycle_closeout=provenance.get("stage8_10_8",{})
    check(lifecycle.get("status")==stage8_9_8_status
          and lifecycle.get("stage8_9_9")=="PHYSICAL_REVALIDATION_COMPLETE"
          and lifecycle.get("stage8_9_complete") is True,
          "STAGE_8_9_LIFECYCLE_COMPLETE")
    check(closeout.get("status")==stage8_9_status
          and closeout.get("accepted_code_commit")==stage8_9_code
          and closeout.get("diagnostic_report_sha256")==stage8_9_report
          and closeout.get("physical_summary_sha256")==stage8_9_summary
          and closeout.get("physical_result")=="STAGE_8_9_10_POST_FUNDING_REVALIDATION_PASS=1"
          and closeout.get("funding_classification")=="STAGE_8_9_FUNDING_MARGIN_VALIDATED"
          and closeout.get("reason")==stage8_9_reason
          and closeout.get("sizing_case_count")==8
          and closeout.get("positive_capacity_case_count")==4
          and closeout.get("zero_capacity_case_count")==4
          and closeout.get("positive_batch_reservation_count")==1
          and closeout.get("stage8_9_complete") is True,
          "STAGE_8_9_10_PROVENANCE_EXACT")
    historical_tokens=("BLOCKED_ACCOUNT_FINANCIALS_UNAVAILABLE","FORTS_PORTFOLIO_MISSING",
                       "BLOCKED_INSUFFICIENT_CONTRACT_CAPACITY","ZERO_CONTRACT_CAPACITY")
    historical_labels=("earlier","previous","historical","old implementation","pre-funding")
    stale_unlabelled=[]
    for name,document in (("CURRENT_STATE.md",current_state),("PROJECT_CONTEXT.md",project_context),
                          ("README.md",readme),("ROADMAP.md",roadmap)):
        for paragraph in re.split(r"\n\s*\n",document):
            if any(token in paragraph for token in historical_tokens) and not any(
                    label in paragraph.lower() for label in historical_labels):
                stale_unlabelled.append(name)
    check(not stale_unlabelled,"STAGE_8_9_HISTORICAL_BLOCKERS_NOT_CURRENT")
    lifecycle_contradiction=re.compile(
        r"Stage 8\.9.{0,120}(?:NOT\s+COMPLETE|CURRENT.{0,40}BLOCKED|must not be described.{0,40}complete)",
        re.I|re.S)
    active_contradictions=[]
    for name,document in (("CURRENT_STATE.md",current_state),("PROJECT_CONTEXT.md",project_context),
                          ("README.md",readme),("ROADMAP.md",roadmap)):
        for paragraph in re.split(r"\n\s*\n",document):
            if lifecycle_contradiction.search(paragraph) and not any(
                    label in paragraph.lower() for label in historical_labels):
                active_contradictions.append(name)
    check(not active_contradictions,"STAGE_8_9_NO_ACTIVE_LIFECYCLE_CONTRADICTION")
    check(all("Stage 8.9 is **COMPLETE**" in document
              for document in authoritative_docs),
          "STAGE_8_9_COMPLETE_SYNCHRONIZED")
    stage8_10_1_status="STAGE_8_10_1_TRADING_TOKEN_PRECONDITIONS_COMPLETE"
    check(all(stage8_10_1_status in document for document in authoritative_docs),
          "STAGE_8_10_1_COMPLETE_SYNCHRONIZED")
    check(preconditions.get("status")==stage8_10_1_status
          and preconditions.get("order_count")==0
          and preconditions.get("stage8_10_3_through_8_status")=="NOT_STARTED"
          and preconditions.get("trading_token_provisioned") is False
          and preconditions.get("trading_token_used") is False,
          "STAGE_8_10_1_MACHINE_AUTHORITY_EXACT")
    check(all("Stage 8.10 is **COMPLETE**" in document for document in authoritative_docs),
          "STAGE_8_10_COMPLETE_SYNCHRONIZED")
    stage8_10_2_status="STAGE_8_10_2_SECURE_PROVISIONING_COMPLETE"
    stage8_10_2_code="f0c271e428c05ee0ff67b7941e342c06b48a42a0"
    stage8_10_2_evidence="E5FEA93CE28006BC5ADA19F1AA1C1C365FF7CF4BE48A5A1B8BC8C5589DFD754D"
    stage8_10_2_result="STAGE_8_10_2_PHYSICAL_SECURE_PROVISIONING_LOCAL_PASS"
    stage8_10_3_status="STAGE_8_10_3_IDENTITY_ACCOUNT_BINDING_COMPLETE"
    stage8_10_4_status="STAGE_8_10_4_PERMISSION_BOUNDARY_COMPLETE"
    stage8_10_5_status="STAGE_8_10_5_ORDER_PATH_DRY_VALIDATION_COMPLETE"
    token_status="STAGE_8_10_7_INTEL_TRADING_TOKEN_ACCEPTANCE_COMPLETE"
    check(current_readme_status(readme)=="STAGE_8_10_TRADING_TOKEN_LIFECYCLE_COMPLETE",
          "STAGE_8_ROBOT_README_CURRENT_STATUS_EXACT")
    check(all("Stage 8.10.2 is **COMPLETE**" in document
              and stage8_10_2_status in document
              and stage8_10_2_code in document
              and stage8_10_2_evidence in document
              and stage8_10_2_result in document for document in authoritative_docs),
          "STAGE_8_10_2_COMPLETE_SYNCHRONIZED")
    check(provisioning.get("status")==stage8_10_2_status
          and provisioning.get("accepted_code_commit")==stage8_10_2_code
          and provisioning.get("external_evidence_sha256")==stage8_10_2_evidence
          and provisioning.get("physical_result")==stage8_10_2_result
          and provisioning.get("physical_provisioning_performed") is True
          and provisioning.get("trading_token_provisioned") is True
          and provisioning.get("trading_token_used") is False
          and provisioning.get("finam_authentication_performed") is False
          and provisioning.get("order_count")==0
          and provisioning.get("stage8_10_status")=="IN_PROGRESS"
          and provisioning.get("stage8_10_3_status")=="NOT_STARTED"
          and provisioning.get("stage8_10_3_through_8_status")=="NOT_STARTED"
          and provisioning.get("stage8_11_status")=="NOT_STARTED_NOT_AUTHORIZED"
          and provisioning.get("stage8_12_status")=="NOT_STARTED_NOT_AUTHORIZED",
          "STAGE_8_10_2_MACHINE_AUTHORITY_EXACT")
    check("DataProtectionScope]::CurrentUser" in trading_store
          and "TradingSystemLab.Stage8.TradingToken.v1" in trading_store
          and "TRADING_CAPABLE_NOT_AUTHORIZED" in trading_store
          and "finam_trading_api_secret" in trading_store
          and "REAL_READONLY" not in trading_store,
          "TRADING_DPAPI_STORE_SEPARATE_FAIL_CLOSED")
    check(not any("trading-credential" in item.lower() or "finam-trading-token" in item.lower()
                  for item in (launcher,task_installer)), "TRADING_STORE_NOT_RUNTIME_WIRED")
    check(all(stage8_10_3_status in document and "Stage 8.10.3 is **COMPLETE**" in document for document in authoritative_docs), "STAGE_8_10_3_CODE_READY_SYNCHRONIZED")
    check(identity_binding.get("status")==stage8_10_3_status
          and identity_binding.get("accepted_code_commit") == "428d285336380726a3ce00487e2c85eb755e2dd9"
          and identity_binding.get("external_evidence_sha256") == "0DA102E61AB06FFA6A508CC64203FEA3F56BBA3016891A887688A4E300E11BB6"
          and identity_binding.get("physical_result") == "STAGE_8_10_3_IDENTITY_ACCOUNT_BINDING_PASS"
          and identity_binding.get("physical_validation_performed") is True
          and identity_binding.get("local_readonly_trading_account_binding_validated") is True
          and identity_binding.get("trading_session_created") is True
          and identity_binding.get("trading_token_used") is True
          and identity_binding.get("finam_authentication_performed") is True
          and identity_binding.get("expected_account_enumerated") is True
          and identity_binding.get("expected_account_occurrence_count") == 1
          and identity_binding.get("enumerated_account_count") == 1
          and identity_binding.get("order_count")==0
          and identity_binding.get("order_endpoint_called") is False
          and identity_binding.get("live_trading_authorized") is False
          and identity_binding.get("real_order_transmission_authorized") is False
          and identity_binding.get("stage8_10_status")=="IN_PROGRESS"
          and identity_binding.get("stage8_10_4_status")=="NOT_STARTED"
          and identity_binding.get("stage8_10_5_through_8_status")=="NOT_STARTED"
          and identity_binding.get("stage8_11_status")=="NOT_STARTED_NOT_AUTHORIZED"
          and identity_binding.get("stage8_12_status")=="NOT_STARTED_NOT_AUTHORIZED", "STAGE_8_10_3_MACHINE_AUTHORITY_EXACT")
    identity_path=HERE/"trading_identity_binding.py"; identity_wrapper_path=HERE/"deploy/windows/validate-trading-identity-binding.ps1"
    identity_source=identity_path.read_text() if identity_path.is_file() else ""; identity_wrapper=identity_wrapper_path.read_text() if identity_wrapper_path.is_file() else ""
    check(identity_path.is_file() and identity_wrapper_path.is_file(), "STAGE_8_10_3_DIAGNOSTIC_FILES_EXIST")
    check(canonical_text_sha256(identity_path.read_bytes())=="1303459b636c99ae7fea4e2e62863888f56ad0e12ca8311a47782a354069167e" and canonical_text_sha256(identity_wrapper_path.read_bytes())=="0ccaa1c6b7e37bba226c25647a068739dfcc1db2ad7c99a695752235b4a7b399", "STAGE_8_10_3_IMPLEMENTATION_HASHES")
    identity_calls={node.func.attr for node in ast.walk(ast.parse(identity_source)) if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)}
    check(not identity_calls.intersection({"place_order","cancel_order","submit_order","orders","order","account","assets","asset","asset_params","schedule","bars"}) and {"create_session","session_details"}.issubset(identity_calls), "STAGE_8_10_3_SESSION_ONLY_NO_ORDER_CAPABILITY")
    check("trading_identity_binding" not in launcher+task_installer+runner+broker and all(term not in identity_wrapper.lower() for term in ("run-readonly","install-task","scheduledtask","runner","broker","/orders")), "STAGE_8_10_3_NOT_RUNTIME_OR_TASK_WIRED")
    permission_path=HERE/"trading_permission_boundary.py"; permission_wrapper_path=HERE/"deploy/windows/validate-trading-permission-boundary.ps1"
    permission_source=permission_path.read_text() if permission_path.is_file() else ""; permission_wrapper=permission_wrapper_path.read_text() if permission_wrapper_path.is_file() else ""
    check(all(stage8_10_4_status in document and "Stage 8.10.4 is **COMPLETE**" in document for document in authoritative_docs), "STAGE_8_10_4_COMPLETE_SYNCHRONIZED")
    check(permission_boundary.get("status")==stage8_10_4_status
          and permission_boundary.get("accepted_code_commit")=="44858bacc2902591e11adc85cfa5f79e2b62dd5b"
          and permission_boundary.get("external_evidence_sha256")=="E4AEDC153F89E000EC034E5F33A6EF7BECB5DA29BA253BC0B28B2AC3D0C26C5D"
          and permission_boundary.get("physical_result")=="STAGE_8_10_4_TOKEN_PERMISSION_BOUNDARY_PASS"
          and permission_boundary.get("physical_validation_performed") is True
          and permission_boundary.get("local_readonly_trading_account_binding_validated") is True
          and permission_boundary.get("readonly_session_created") is True
          and permission_boundary.get("trading_session_created") is True
          and permission_boundary.get("readonly_expected_account_enumerated") is True
          and permission_boundary.get("trading_expected_account_enumerated") is True
          and permission_boundary.get("readonly_expected_account_occurrence_count")==1
          and permission_boundary.get("trading_expected_account_occurrence_count")==1
          and permission_boundary.get("readonly_token_readonly_observed") is True
          and permission_boundary.get("trading_token_readonly_false_observed") is True
          and permission_boundary.get("token_permission_boundary_validated") is True
          and permission_boundary.get("readonly_token_used") is True
          and permission_boundary.get("trading_token_used") is True
          and permission_boundary.get("finam_authentication_performed") is True
          and permission_boundary.get("order_count")==0
          and permission_boundary.get("order_endpoint_called") is False
          and permission_boundary.get("order_path_validation_performed") is False
          and permission_boundary.get("live_trading_authorized") is False
          and permission_boundary.get("real_order_transmission_authorized") is False
          and permission_boundary.get("stage8_10_status")=="IN_PROGRESS"
          and permission_boundary.get("stage8_10_5_status")=="NOT_STARTED"
          and permission_boundary.get("stage8_10_6_through_8_status")=="NOT_STARTED"
          and permission_boundary.get("stage8_11_status")=="NOT_STARTED_NOT_AUTHORIZED"
          and permission_boundary.get("stage8_12_status")=="NOT_STARTED_NOT_AUTHORIZED", "STAGE_8_10_4_MACHINE_AUTHORITY_EXACT")
    check(permission_path.is_file() and permission_wrapper_path.is_file(), "STAGE_8_10_4_DIAGNOSTIC_FILES_EXIST")
    check(canonical_text_sha256(permission_path.read_bytes())=="609baa9dda8859486cfdef204c99748088425c70c65895074bbb993df17b6624" and canonical_text_sha256(permission_wrapper_path.read_bytes())=="c4a086e1a8ae955056bb12053d5df9f3b2de9e4106ea6ba640c6e3f2e78a4e33", "STAGE_8_10_4_IMPLEMENTATION_HASHES")
    permission_calls={node.func.attr for node in ast.walk(ast.parse(permission_source)) if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)}
    forbidden_permission_calls={"orders","order","place_order","cancel_order","submit_order","account","assets","assets_all_active","asset","asset_params","schedule","bars"}
    check(not permission_calls.intersection(forbidden_permission_calls) and {"create_session","session_details"}.issubset(permission_calls), "STAGE_8_10_4_SESSION_ONLY_NO_ORDER_CAPABILITY")
    check("trading_permission_boundary" not in launcher+task_installer+runner+broker and all(term not in permission_wrapper.lower() for term in ("run-readonly","install-task","scheduledtask","runner","broker","/orders","place_order","cancel_order","submit_order")), "STAGE_8_10_4_NOT_RUNTIME_OR_TASK_WIRED")
    dry_path=HERE/"order_path_dry_validation.py"; dry_wrapper_path=HERE/"deploy/windows/validate-order-path-dry.ps1"
    dry_source=dry_path.read_text() if dry_path.is_file() else ""; dry_wrapper=dry_wrapper_path.read_text() if dry_wrapper_path.is_file() else ""
    check(all(stage8_10_5_status in document and "Stage 8.10.5 is **COMPLETE**" in document for document in authoritative_docs),"STAGE_8_10_5_CODE_READY_SYNCHRONIZED")
    expected_dry_gate={
        "status":stage8_10_5_status,
        "accepted_code_commit":"ba284e95954c8473c0e77a95172117bc5cefaf65",
        "external_evidence_sha256":"D878309E22FA49BFFA9EE9B37200C3FE207BF77DB5C29D6DE97010F1FFCE904A",
        "physical_result":"STAGE_8_10_5_OFFLINE_ORDER_PATH_DRY_VALIDATION_PASS",
        "physical_validation_performed":True,"offline_dry_validation_performed":True,
        "order_path_dry_validation_validated":True,"mode":"OFFLINE_SYNTHETIC_NO_TRANSMISSION",
        "frozen_n4_symbol_count":4,"broker_payload_case_count":16,"broker_payload_validation":"PASS",
        "client_order_id_validation":"PASS","market_order_type":"ORDER_TYPE_MARKET",
        "transport_serialization_validation":"PASS","synthetic_order_post_constructed":True,
        "synthetic_order_post_count":1,"uncertain_submission_validation":"PASS",
        "uncertain_submission_order_post_count":1,"automatic_order_post_retry_count":0,
        "external_network_calls":0,"real_account_id_used":False,
        "readonly_token_used_for_stage8_10_5":False,"trading_token_used_for_stage8_10_5":False,
        "finam_authentication_performed_for_stage8_10_5":False,"real_order_endpoint_called":False,
        "real_order_count":0,"live_trading_authorized":False,"real_order_transmission_authorized":False,
        "stage8_10_status":"IN_PROGRESS","stage8_10_6_status":"NOT_STARTED",
        "stage8_10_7_through_8_status":"NOT_STARTED","stage8_11_status":"NOT_STARTED_NOT_AUTHORIZED",
        "stage8_12_status":"NOT_STARTED_NOT_AUTHORIZED"}
    check(dry_gate==expected_dry_gate,"STAGE_8_10_5_MACHINE_AUTHORITY_EXACT")
    check(dry_path.is_file() and dry_wrapper_path.is_file() and canonical_text_sha256(dry_path.read_bytes())=="4bf00af63304001a5f127435d764876c02e545af7cfed1672288d6e4b8bdd460" and canonical_text_sha256(dry_wrapper_path.read_bytes())=="a1058ee61f3a9586649bb57a46e72d9d1ef49d89d3954c66df8752df05a98288","STAGE_8_10_5_IMPLEMENTATION_HASHES")
    forbidden_dry=("urlopen(","requests.","httpx.","socket.","invoke-webrequest","invoke-restmethod","curl ","wget ","credential-store","get-readonlycredential","get-tradingcredential","run-readonly","install-task","readonly_supervisor","tradingsystemlab\\runtime","tradingsystemlab/runtime","robotrunner",".sqlite",".sqlite3","-wal","-shm")
    check("transport=transport" in dry_source and "REPOSITORY_OUTPUT_FORBIDDEN" in dry_source and not any(term in (dry_source+dry_wrapper).lower() for term in forbidden_dry) and "order_path_dry_validation" not in launcher+task_installer+runner,"STAGE_8_10_5_OFFLINE_NOT_RUNTIME_WIRED")
    check(not any(Path(path).name.lower()=="stage8_10_5_order_path_dry_validation.json" for path in tracked),"STAGE_8_10_5_PHYSICAL_EVIDENCE_NOT_TRACKED")
    safety_status="STAGE_8_10_6_KILL_SWITCH_SAFETY_GATES_COMPLETE"
    expected_safety={"status":safety_status,"accepted_code_commit":"35ec9007e6302d66e35e1a42a34fc2e77be8a467","external_evidence_sha256":"CF34E54212B3385F154804F440361FE5E213B0AFA63D8DD8AE56E1EBB49D6B30","physical_result":"STAGE_8_10_6_PHYSICAL_SAFETY_GATE_VALIDATION_PASS","physical_validation_performed":True,"production_kill_switch_initialized":True,"production_kill_switch_halted_observed":True,"production_kill_switch_final_state":"HALTED","production_kill_switch_valid":True,"synthetic_safety_matrix_validated":True,"synthetic_case_count":25,"synthetic_open_case_count":1,"synthetic_blocked_case_count":24,"synthetic_matrix_validation":"PASS","emergency_halt_validated":True,"missing_switch_fail_closed":True,"malformed_switch_fail_closed":True,"execution_authorization_required":True,"heartbeat_health_gate_validated":True,"reconciliation_gate_validated":True,"unresolved_order_gate_validated":True,"heartbeat_freshness_gate_validated":True,"api_contact_freshness_gate_validated":True,"account_hash_shape_gate_validated":True,"execution_authorized":False,"real_account_id_used":False,"readonly_token_used_for_stage8_10_6":False,"trading_token_used_for_stage8_10_6":False,"finam_authentication_performed_for_stage8_10_6":False,"external_network_calls":0,"real_order_endpoint_called":False,"real_order_count":0,"live_trading_authorized":False,"real_order_transmission_authorized":False,"stage8_10_status":"IN_PROGRESS","stage8_10_7_status":"NOT_STARTED","stage8_10_8_status":"NOT_STARTED","stage8_11_status":"NOT_STARTED_NOT_AUTHORIZED","stage8_12_status":"NOT_STARTED_NOT_AUTHORIZED"}
    check(safety_gate==expected_safety,"STAGE_8_10_6_MACHINE_AUTHORITY_EXACT")
    safety_path=HERE/"trading_safety_gate.py"; validation_path=HERE/"safety_gate_validation.py"; safety_wrapper=HERE/"deploy/windows/validate-trading-safety-gates.ps1"
    safety_source=source_overrides.get("trading_safety_gate.py",safety_path.read_text()); validation_source=source_overrides.get("safety_gate_validation.py",validation_path.read_text()); wrapper_source=source_overrides.get("deploy/windows/validate-trading-safety-gates.ps1",safety_wrapper.read_text())
    check(all(p.is_file() for p in (safety_path,validation_path,safety_wrapper)),"STAGE_8_10_6_IMPLEMENTATION_PRESENT")
    check(canonical_text_sha256(safety_path.read_bytes())=="64c781579e630836cfde7a0b772df1e2707caf35decafb9acdc75d7d2e3df6e4" and canonical_text_sha256(validation_path.read_bytes())=="baf9f85f8fa3c6c789db7ce40d9d23fb13d7854c11820986f33c1c5436716b9f" and canonical_text_sha256(safety_wrapper.read_bytes())=="7da9ff0a252008f41c771866d528cbaf4ce2fc97221b87a1b933d50acb75c4d5","STAGE_8_10_6_IMPLEMENTATION_HASHES")
    offline_safe,wrapper_halt_only,physical_report_contract=_stage8_10_6_semantics(safety_source,validation_source,wrapper_source)
    check(offline_safe,"STAGE_8_10_6_OFFLINE_FAIL_CLOSED")
    check(wrapper_halt_only,"STAGE_8_10_6_WRAPPER_HALT_ONLY")
    check(physical_report_contract,"STAGE_8_10_6_PHYSICAL_REPORT_CONTRACT")
    check(not any(Path(path).name.lower() in {"stage8-trading-kill-switch.json","stage8_10_6_safety_gate_validation.json"} for path in tracked),"STAGE_8_10_6_EXTERNAL_ARTIFACTS_NOT_TRACKED")
    check(all(safety_status in document and "Stage 8.10.6 is **COMPLETE**" in document for document in authoritative_docs),"STAGE_8_10_6_COMPLETE_SYNCHRONIZED")
    expected_token={"status":token_status,"accepted_code_commit":"df4bba6be4f98ba4659e13a01c90bec8e4162ff3","external_evidence_sha256":"A2A6B330A5DC1F15D67A84860223D80786022B634BB8B6CD73E01C815EE7D1B6","physical_result":"STAGE_8_10_7_PHYSICAL_INTEL_TRADING_TOKEN_ACCEPTANCE_PASS","physical_validation_performed":True,"trading_dpapi_current_user_validated":True,"local_readonly_trading_account_binding_validated":True,"production_kill_switch_pre_halted_observed":True,"trading_session_created":True,"expected_account_enumerated":True,"expected_account_occurrence_count":1,"trading_token_readonly_false_observed":True,"trading_token_write_boundary_confirmed":True,"remote_call_scope":"SESSION_CREATE_AND_DETAILS_ONLY","production_kill_switch_post_halted_observed":True,"trading_token_used":True,"readonly_token_used_for_remote_auth":False,"finam_authentication_performed":True,"order_endpoint_called":False,"order_count":0,"execution_authorized":False,"live_trading_authorized":False,"real_order_transmission_authorized":False,"stage8_10_status":"IN_PROGRESS","stage8_10_8_status":"NOT_STARTED","stage8_11_status":"NOT_STARTED_NOT_AUTHORIZED","stage8_12_status":"NOT_STARTED_NOT_AUTHORIZED"}
    check(token_acceptance==expected_token,"STAGE_8_10_7_MACHINE_AUTHORITY_EXACT")
    token_path=HERE/"trading_token_intel_acceptance.py"; token_wrapper_path=HERE/"deploy/windows/validate-trading-token-intel-acceptance.ps1"
    token_source=source_overrides.get("trading_token_intel_acceptance.py",token_path.read_text() if token_path.is_file() else "")
    token_wrapper_source=source_overrides.get("deploy/windows/validate-trading-token-intel-acceptance.ps1",token_wrapper_path.read_text() if token_wrapper_path.is_file() else "")
    check(token_path.is_file() and token_wrapper_path.is_file(),"STAGE_8_10_7_IMPLEMENTATION_PRESENT")
    check(canonical_text_sha256(token_path.read_bytes())=="84d1acd85af02adfef7781d1fa01cbe5f418a53e5f3ef582224a34490a07b27b" and canonical_text_sha256(token_wrapper_path.read_bytes())=="26e7dbe2ff4d262a76d13b97cca181b80a06fb662a029ba3436af1fea2930386","STAGE_8_10_7_IMPLEMENTATION_HASHES")
    session_only,kill_switch,wrapper_boundary,runtime_wiring,report_contract,cleanup=_stage8_10_7_semantics(token_source,token_wrapper_source)
    check(session_only,"STAGE_8_10_7_SESSION_ONLY_NO_ORDER_CAPABILITY")
    check(kill_switch,"STAGE_8_10_7_KILL_SWITCH_HALTED_REQUIRED")
    check(wrapper_boundary,"STAGE_8_10_7_WRAPPER_CREDENTIAL_BOUNDARY")
    check(runtime_wiring,"STAGE_8_10_7_WRAPPER_NOT_RUNTIME_WIRED")
    check(report_contract,"STAGE_8_10_7_REPORT_CONTRACT")
    check(cleanup,"STAGE_8_10_7_CLEANUP_CONTRACT")
    check(not any(Path(path).name.lower()=="stage8_10_7_intel_trading_token_acceptance.json" for path in tracked),"STAGE_8_10_7_EXTERNAL_ARTIFACT_NOT_TRACKED")
    check(all(token_status in document and "Stage 8.10.7 is **COMPLETE**" in document and "Stage 8.10.8 is **COMPLETE**" in document for document in authoritative_docs),"STAGE_8_10_7_COMPLETE_SYNCHRONIZED")
    expected_closeout={"status":"STAGE_8_10_TRADING_TOKEN_LIFECYCLE_COMPLETE","stage8_10_complete":True,"completed_gate_count":7,
        "stage8_10_1_status":stage8_10_1_status,"stage8_10_2_status":stage8_10_2_status,
        "stage8_10_3_status":stage8_10_3_status,"stage8_10_4_status":stage8_10_4_status,
        "stage8_10_5_status":stage8_10_5_status,"stage8_10_6_status":safety_status,
        "stage8_10_7_status":token_status,"production_kill_switch_final_state":"HALTED",
        "execution_authorized":False,"order_endpoint_called":False,"order_count":0,
        "live_trading_authorized":False,"real_order_transmission_authorized":False,
        "stage8_11_status":"NOT_STARTED_NOT_AUTHORIZED","stage8_12_status":"NOT_STARTED_NOT_AUTHORIZED"}
    check(lifecycle_closeout==expected_closeout,"STAGE_8_10_8_MACHINE_AUTHORITY_EXACT")
    check(all("STAGE_8_10_TRADING_TOKEN_LIFECYCLE_COMPLETE" in document for document in authoritative_docs),
          "STAGE_8_10_CLOSEOUT_STATUS_SYNCHRONIZED")
    check(not any(re.search(r"Stage 8\.10(?: is| —) \*\*IN PROGRESS\*\*|Stage 8\.10\.8 is \*\*NOT STARTED\*\*", document)
                  for document in authoritative_docs),"STAGE_8_10_NO_STALE_CURRENT_STATUS")
    current_handoffs=[_current_handoff(document) for document in authoritative_docs]
    check(all("Stage 8.11 — Controlled Real Execution Acceptance — is now **COMPLETE / PASS**" in handoff
              and "stage8.11.attempt7" in handoff
              and "704BFCC19B1A63F490192C0D8D0E4715BFECF77664296AFEF47E5B80FBF64B5F" in handoff
              and "exactly two real order-endpoint calls" in handoff
              and "final position quantity: `0`" in handoff
              and "final active broker orders: `0`" in handoff
              and "unresolved Stage 8.11 intents: `0`" in handoff
              and "The physical authorization used for attempt7 is consumed" in handoff
              and "Current `execution_authorized = false`" in handoff
              for handoff in current_handoffs),"STAGE_8_11_LIFECYCLE_CLOSEOUT_SYNCHRONIZED")
    check(all("Stage 8.12.3 — Intel production preflight — is **COMPLETE / PASS**" in handoff
              and "0a40e3bf7a97f0c011d3a6f5216d9f61dd52ef30" in handoff
              and "9584F45186DE38ABAE9209E1F326255C783AF762CD736EA45718D19C93BC61B1" in handoff
              and "205/205 PASS" in handoff
              and "Stage 8.12.4 — Explicit FULL/R15 production authorization and activation — is now **STARTED / IMPLEMENTATION IN PROGRESS / NOT AUTHORIZED**" in handoff
              and "no authorization record has been created" in handoff.lower()
              and "kill switch remains `HALTED`" in handoff
              and "production Scheduled Task remains disabled" in handoff
              for handoff in current_handoffs),
          "STAGE_8_12_4_CURRENT_HANDOFF")
    forbidden_claims=(r"(?:broker acceptance (?:is |was )?validated|order (?:was )?accepted|FINAM server accepted an order)",
                      r"(?<!not )real-order (?:transmission|capability) is authorized",)
    check(not any(re.search(pattern,closeout_docs,re.I) for pattern in forbidden_claims),
          "STAGE_8_10_FALSE_AUTHORIZATION_OR_TOKEN_CLAIM")
    false_full_claim=re.compile(r"(?:FULL/N4|FULL N4|FULL/R15).{0,40}(?:ready|sufficient|validated)",re.I)
    check(not false_full_claim.search(closeout_docs),"FULL_N4_FUNDING_READINESS_NOT_CLAIMED")
    check("LIVE_TRADING_NOT_AUTHORIZED" in readme and "no live trading was authorized" in closeout_docs.lower(),"CLOSEOUT_LIVE_TRADING_UNAUTHORIZED")
    check("REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED" in readme
          and re.search(r"no live order\s+was transmitted",closeout_docs,re.I),
          "CLOSEOUT_REAL_ORDER_TRANSMISSION_UNAUTHORIZED")
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
    check("portfolio_mc" in margin and "initial_margin" in margin and "maintenance_margin" in margin
          and 'account_type=="UNION"' in margin,"UNION_MC_ACCOUNT_AUTHORITY_PARSED")
    check("long_initial_margin" in margin and "short_initial_margin" in margin and "MARGIN_CURRENCY_MISMATCH" in margin,"DIRECTIONAL_MARGIN_PARSED")
    decimal_parser=margin.split("def parse_rest_decimal_value_object",1)[1].split("def forts_funds",1)[0]
    check('set(value)!={"value"}' in decimal_parser and "Decimal(scalar)" in decimal_parser and "parse_money" not in decimal_parser,"ACCOUNT_REST_DECIMAL_DISTINCT")
    check('parse_rest_decimal_value_object(forts.get("available_cash"))' in margin and 'parse_rest_decimal_value_object(forts.get("money_reserved"))' in margin,"ACCOUNT_FUNDS_NOT_MONEY")
    check('return parse_money(params.get(key),positive=True)' in margin,"DIRECTIONAL_MARGIN_REMAINS_MONEY")
    check('row.update(values)' in real_updater and all(x in real_updater for x in ('"finam_symbol"','"security_id"','PRODUCTION_SPECIFICATION_ID','exact_matches','os.replace(temp,registry_path)','list(csv.DictReader(check_file))')),"REAL_REGISTRY_FULL_ATOMIC_ACTIVATION")
    check("class MarginBatchBudget" in margin and "self.remaining-=reservation" in margin,"SAME_BATCH_MARGIN_RESERVATION")
    diagnostic_tree=ast.parse(funding_diagnostic)
    diagnostic_calls={node.func.attr for node in ast.walk(diagnostic_tree)
                      if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)}
    check(not diagnostic_calls.intersection({"place_order","submit_order","cancel_order","modify_order"}),
          "STAGE_8_9_NO_ORDER_CAPABLE_CALL")
    check('os.getenv("FINAM_MODE") != "REAL_READONLY"' in funding_diagnostic
          and 'os.getenv("NEW_ENTRIES_DISABLED", "").lower() != "true"' in funding_diagnostic,
          "STAGE_8_9_REAL_READONLY_ENTRIES_DISABLED")
    check('portfolio_authority(account)' in funding_diagnostic
          and 'parse_rest_decimal_value_object(account.get("equity"), positive=True)' in funding_diagnostic
          and "AVAILABLE_CASH_SEMANTICS" in funding_diagnostic,
          "STAGE_8_9_EXACT_FINANCIAL_AUTHORITIES_NO_FALLBACK")
    check('for direction in ("LONG", "SHORT")' in funding_diagnostic
          and "final_quantity <= result.r15_quantity" in funding_diagnostic
          and "MarginBatchBudget(available)" in funding_diagnostic
          and "positive_capacity_case_count < 1" in funding_diagnostic
          and "ZERO_CONTRACT_CAPACITY" in funding_diagnostic,
          "STAGE_8_9_DIRECTIONAL_CAP_AND_BATCH")
    check('account_identity_sha256' in funding_diagnostic and 'no_order_call_assertion' in funding_diagnostic
          and 'stage8-8-9-funding-margin-validation/v1' in funding_diagnostic,
          "STAGE_8_9_SANITIZED_EXTERNAL_REPORT")
    check('parse_rest_value_object(bars[-1]["close"])' in funding_diagnostic
          and not re.search(r'Decimal\s*\(\s*str\s*\([^\n]*\[\s*[\'\"]close[\'\"]\s*\]',
                            funding_diagnostic),
          "STAGE_8_9_REST_H1_CLOSE_VALUE_OBJECT_ONLY")
    check("STAGE8_9_REPORT_REPOSITORY_OUTPUT_FORBIDDEN" in funding_diagnostic
          and "REPOSITORY_ROOT in destination.parents" in funding_diagnostic,
          "STAGE_8_9_EXTERNAL_REPORT_CANNOT_ENTER_REPOSITORY")
    run_path_tests=subprocess.run(
        [sys.executable,"-m","pytest","-q",
         "TradingSystemLab/stage8_robot/tests/test_funding_margin_diagnostic.py","-k","run_"],
        cwd=ROOT,capture_output=True,text=True)
    check(run_path_tests.returncode==0,
          "STAGE_8_9_SYNTHETIC_RUN_PATH_FAIL_CLOSED_INTEGRATION")
    check("Stage 8.10 is **COMPLETE**" in closeout_docs and stage8_10_1_status in closeout_docs
          and "LIVE_TRADING_NOT_AUTHORIZED" in readme,
          "STAGE_8_10_AND_LIVE_UNAUTHORIZED")
    check("starting_realized_equity" in runner and "REAL_ACCOUNT_NOT_CLEAN_FOR_INITIALIZATION" in runner,"CLEAN_REAL_EQUITY_BOOTSTRAP")
    check("account_identity_sha256" in runner and 'environment="REAL"' in runner,"REAL_STATE_ACCOUNT_HASH_BOUND")
    check("class InstanceLock" in operations and "SECOND_ROBOT_INSTANCE_BLOCKED" in operations and "src.backup(dst)" in operations,"SERVER_LOCK_AND_SQLITE_BACKUP")
    check('mode=ro' in operations and "source.is_file()" in operations and "source.is_symlink()" in operations,
          "SQLITE_BACKUP_MISSING_SOURCE_FAIL_CLOSED")
    check(operations.count('PRAGMA integrity_check')>=2 and "src.backup(dst)" in operations,
          "SQLITE_ONLINE_BACKUP_SOURCE_AND_DESTINATION_INTEGRITY")
    operations_tree=ast.parse(operations)
    operations_parents={child:parent for parent in ast.walk(operations_tree)
                        for child in ast.iter_child_nodes(parent)}
    def deterministically_closed_connects(function_name):
        function=next(node for node in operations_tree.body
                      if isinstance(node,ast.FunctionDef) and node.name==function_name)
        connects=[node for node in ast.walk(function) if isinstance(node,ast.Call)
                  and isinstance(node.func,ast.Attribute)
                  and ast.unparse(node.func)=="sqlite3.connect"]
        closing_withs=[]
        for connect in connects:
            parent=operations_parents.get(connect)
            closed=parent if (isinstance(parent,ast.Call) and isinstance(parent.func,ast.Name)
                              and parent.func.id=="closing" and parent.args==[connect]) else None
            context=operations_parents.get(closed) if closed is not None else None
            if not isinstance(context,ast.withitem): return function,connects,[]
            statement=operations_parents.get(context)
            if not isinstance(statement,ast.With): return function,connects,[]
            closing_withs.append(statement)
        return function,connects,closing_withs
    backup_function,backup_connects,backup_closing_withs=deterministically_closed_connects("sqlite_backup")
    validation_function,validation_connects,validation_closing_withs=deterministically_closed_connects("validate_operational_database")
    publish=next((node for node in ast.walk(backup_function) if isinstance(node,ast.Call)
                  and ast.unparse(node)=="os.replace(temporary, destination)"),None)
    check(len(backup_connects)==4 and len(backup_closing_withs)==4 and publish is not None
          and all(context.end_lineno < publish.lineno for context in backup_closing_withs)
          and len(validation_connects)==len(validation_closing_withs)==1,
          "SQLITE_WINDOWS_HANDLES_DETERMINISTICALLY_CLOSED_BEFORE_PUBLICATION")
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
    check("CLEANUP_PENDING_BASENAME" in restore
          and "RestoreResult(target=target, cleanup_pending=cleanup_incomplete)" in restore
          and "except OSError:\n                cleanup_incomplete = True" in restore
          and restore.index("validate_operational_schema(target)")
              < restore.index("os.replace(quarantine, pending)")
              < restore.index("pending.unlink(missing_ok=True)", restore.index("os.replace(quarantine, pending)"))
          and "READONLY_STATE_RECOVERY_COMMITTED_CLEANUP_PENDING_RECONCILIATION_REQUIRED" in restore
          and "READONLY_STATE_RECOVERY_PREVIOUS_COMMIT_CLEANUP_PENDING" in restore,
          "RECOVERY_POST_COMMIT_CLEANUP_OUTCOME_UNAMBIGUOUS")
    recovery_tests=(HERE/"tests/test_sqlite_recovery.py").read_text()
    check("subprocess.run(" in recovery_tests and "os._exit(0)" in recovery_tests
          and 'state.close()\n    target = root / "state/readonly-supervisor.sqlite3"' in recovery_tests
          and 'skipif(os.name != "nt"' in recovery_tests
          and "test_windows_external_open_database_fails_restore_closed" in recovery_tests,
          "RECOVERY_REAL_CRASH_WAL_NO_LIVE_HANDLE_AND_WINDOWS_REFUSAL_TESTED")
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
    controlled=acceptance
    finam=finam_api
    recovery=source_overrides.get("stage8_11_failed_attempt_recovery.py",
        source_overrides.get("TradingSystemLab/stage8_robot/stage8_11_failed_attempt_recovery.py",
                             (HERE/"stage8_11_failed_attempt_recovery.py").read_text()))
    recovery_wrapper=source_overrides.get("deploy/windows/run-stage8-11-failed-intent-recovery.ps1",
        (HERE/"deploy/windows/run-stage8-11-failed-intent-recovery.ps1").read_text())
    check("stage8_11_exclusive_lock(runtime_root)" in physical_entry
          and "stage8_11_exclusive_lock(root)" in recovery,
          "STAGE8_11_SHARED_EXCLUSIVE_LOCK_AUTHORITY")
    check("stage8_11_failed_attempt_recovery" in physical_wrapper,
          "STAGE8_11_PHYSICAL_WRAPPER_RECOVERY_CONFLICT")
    check("class FinamOrderRejected" in finam and "FinamUncertainSubmission" in finam
          and "order_post and exc.code==400" in finam and "exc.code>=500 and order_post" in finam,
          "STAGE8_11_DETERMINISTIC_REJECT_UNCERTAIN_TAXONOMY")
    check('transition_intent(request.idempotency_key, "REJECTED")' in controlled
          and "ENTRY_DEFINITIVE_REJECTION" in controlled, "STAGE8_11_HTTP400_TERMINAL_REJECTED")
    check("require_active_trading_session" in controlled and "self.api.schedule(finam_symbol)" in controlled
          and "STAGE8_11_TRADING_SESSION_NOT_OPEN" in controlled, "STAGE8_11_EXACT_SCHEDULE_SESSION_GATE")
    check("entry_observed = time_source()" in controlled and "flatten_observed = time_source()" in controlled
          and "FLATTEN_TRADING_SESSION_NOT_OPEN" in controlled
          and "minimum_remaining=ENTRY_MINIMUM_REMAINING_SESSION" in controlled,
          "STAGE8_11_FRESH_PER_POST_CLOCK_AND_ENTRY_MARGIN")
    check("if not _account_is_clean(final):" in controlled and '"unresolved_intent_count"' in controlled,
          "STAGE8_11_ACCOUNT_WIDE_CLEAN_PROOF")
    recovery_calls={node.func.attr for node in ast.walk(ast.parse(recovery))
                    if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)}
    check(not recovery_calls.intersection({"place_order","cancel_order","submit_order","modify_order"})
          and "FAILED_PHYSICAL_EVIDENCE_SHA256" in recovery and "ACCEPTED_PHYSICAL_COMMIT" in recovery
          and "backup, manifest = create_stage8_11_acceptance_backup" in recovery, "STAGE8_11_BOUND_ORDER_INCAPABLE_RECOVERY")
    check("recovery_status\": \"PREPARED" in recovery and "BEGIN IMMEDIATE" in recovery
          and "during_evidence_finalization" in recovery,
          "STAGE8_11_RECOVERY_DURABLE_COMMIT_PROTOCOL")
    check("Get-ReadonlyCredential" in recovery_wrapper and "Get-TradingCredential" not in recovery_wrapper
          and "stage8_11_failed_attempt_recovery" in recovery_wrapper,
          "STAGE8_11_RUNNABLE_READONLY_RECOVERY_OPERATOR_BOUNDARY")
    check(all(token in recovery_wrapper for token in (
              "ValidatePattern('^[0-9a-f]{40}$')", "rev-parse HEAD", "status --porcelain",
              "Get-FileHash", "STAGE8_11_KILL_SWITCH_NOT_HALTED",
              "stage8_11_physical_acceptance|stage8_11_failed_attempt_recovery",
              "Global\\TradingSystemLab-Stage8-11-Failed-Intent-Recovery", "ReleaseMutex"))
          and recovery_wrapper.index("rev-parse HEAD") < recovery_wrapper.index("Get-ReadonlyCredential")
          and recovery_wrapper.index("Get-FileHash") < recovery_wrapper.index("Get-ReadonlyCredential"),
          "STAGE8_11_RECOVERY_PREAUTHORITY_EXCLUSIVITY_BOUNDARY")
    recovery_tree=ast.parse(recovery)
    recovery_keys=[node.value for node in ast.walk(recovery_tree)
                   if isinstance(node,ast.Constant) and isinstance(node.value,str)]
    check(recovery_keys.count("recovery_code_commit") >= 3
          and "load_kill_switch" in recovery and 'switch.get("state") != "HALTED"' in recovery,
          "STAGE8_11_RECOVERY_CODE_AND_HALTED_EVIDENCE_BINDING")
    check("finally:\n        emergency_halt(runtime_root" in controlled
          and controlled.count("submit_entry(") <= 2 and controlled.count("submit_flatten(") <= 3,
          "STAGE8_11_PARENT_CHILD_HALT_MAX_TWO_POST_CAPABILITY")
    record=provenance.get("stage8_11_failed_physical_attempt_correction",{})
    recovered=provenance.get("stage8_11_historical_failed_intent_recovery",{})
    check(recovered == {
        "schema":"stage8_11_failed_attempt_recovery.v1",
        "recovery_status":"COMMITTED",
        "failed_physical_attempt_authority":"069806355fc6931470d7f68d5ca6db20b06358fa",
        "accepted_physical_code_commit":"069806355fc6931470d7f68d5ca6db20b06358fa",
        "recovery_implementation_authority":"da3bf756fefc4ed8dbe8c33847c6bb183fcaff30",
        "recovery_code_commit":"da3bf756fefc4ed8dbe8c33847c6bb183fcaff30",
        "physical_evidence_sha256":"9FEFC5469F2C97F1EB36A5B5C99D323FA37BB948CF53C8A8745A27A06AB3B324",
        "recovery_evidence_sha256":"4B787AD9A4986D2E3AB88CAAB1B5F2FCD88CAB299A303FA431D38A74D1CD292D",
        "intent_key":"stage8.11:CNYRUBF:entry","terminal_status":"REJECTED","broker_order_id":None,
        "fresh_account_wide_reconciliation":"PASS","all_positions_zero":True,
        "active_broker_order_count":0,"canonical_unresolved_intent_count":0,"readonly_session":True,
        "real_order_submitted_by_recovery":False,"order_cancellation_performed":False,
        "physical_acceptance_retried":False,"production_identity":"TRAIL1__N4_01__FULL__R15",
        "production_specification":"PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8",
        "final_kill_switch":"HALTED","final_scheduled_task":"Disabled","stage8_12_activity":False},
        "STAGE8_11_HISTORICAL_RECOVERY_CLOSEOUT_IMMUTABLE")

    check(record.get("lifecycle",{}).get("8.11.7") == "COMPLETE / PASS / HISTORICAL INTENT RECOVERED"
          and record.get("lifecycle",{}).get("8.11.8") == "COMPLETE / STAGE 8.11 CLOSEOUT"
          and record.get("lifecycle",{}).get("8.12") == "NOT STARTED / NOT AUTHORIZED"
          and record.get("authorization") == "STAGE8_11_PRIOR_ONE_CONTRACT_AUTHORIZATION_CONSUMED"
          and record.get("finam_http_status") == 400
          and record.get("physical_result")=="OPERATOR_INTERVENTION_REQUIRED"
          and record.get("order_endpoint_call_count")==1 and record.get("retry_occurred") is False,
          "STAGE8_11_FAILED_ATTEMPT_PROVENANCE")
    result={"status":"PASS" if not errors else "FAIL","checks":checks,"errors":errors,"production_specification_id":spec.production_id,"live_trading_activated":False,"real_order_transmission_authorized":False,"stage8_status":completed_status,"margin_status":"STAGE_8_MARGIN_AWARE_FULL_R15_CODE_READY","deployment_status":"STAGE_8_INTEL_SERVER_DEPLOYMENT_PREPARED","stage8_11_0_status":"COMPLETE","stage8_11_1_status":"COMPLETE_PASS","stage8_11_2_status":"COMPLETE_PASS","stage8_11_3_status":"PRIOR_AUTHORIZATION_CONSUMED","stage8_11_current_gate":"STAGE_8_12_4_EXPLICIT_FULL_R15_PRODUCTION_AUTHORIZATION","stage8_11_latest_physical_precheck_result":"STAGE8_11_PRECHECK_ONLY_PASS","stage8_11_physical_precheck_real_order_count":0,"stage8_11_latest_physical_acceptance_result":"PASS","stage8_11_physical_acceptance_order_endpoint_call_count":2,"stage8_11_real_order_count":2,"stage8_9_status":stage8_9_status,"stage8_9_reason":stage8_9_reason,"stage8_9_accepted_code_commit":stage8_9_code,"stage8_9_diagnostic_report_sha256":stage8_9_report,"stage8_9_physical_summary_sha256":stage8_9_summary,"stage8_9_8_status":stage8_9_8_status,"stage8_9_9_status":"PHYSICAL_REVALIDATION_COMPLETE","stage8_9_10_status":"COMPLETE","stage8_9_sizing_case_count":8,"stage8_9_positive_capacity_case_count":4,"stage8_9_zero_capacity_case_count":4,"stage8_9_positive_batch_reservation_count":1,"stage8_10_status":"STAGE_8_10_TRADING_TOKEN_LIFECYCLE_COMPLETE","stage8_10_1_status":stage8_10_1_status,"stage8_10_2_status":stage8_10_2_status,"stage8_10_2_accepted_code_commit":stage8_10_2_code,"stage8_10_2_external_evidence_sha256":stage8_10_2_evidence,"stage8_10_2_physical_result":stage8_10_2_result,"physical_provisioning_performed":True,"trading_token_provisioned":True,"trading_token_used":True,"finam_authentication_performed":True,"order_count":0,"order_endpoint_called":False,"stage8_10_3_status":stage8_10_3_status,"stage8_10_3_accepted_code_commit":"428d285336380726a3ce00487e2c85eb755e2dd9","stage8_10_3_external_evidence_sha256":"0DA102E61AB06FFA6A508CC64203FEA3F56BBA3016891A887688A4E300E11BB6","stage8_10_3_physical_result":"STAGE_8_10_3_IDENTITY_ACCOUNT_BINDING_PASS","physical_validation_performed":True,"local_readonly_trading_account_binding_validated":True,"trading_session_created":True,"expected_account_enumerated":True,"expected_account_occurrence_count":1,"enumerated_account_count":1,"stage8_10_4_status":stage8_10_4_status,"stage8_10_4_accepted_code_commit":"44858bacc2902591e11adc85cfa5f79e2b62dd5b","stage8_10_4_external_evidence_sha256":"E4AEDC153F89E000EC034E5F33A6EF7BECB5DA29BA253BC0B28B2AC3D0C26C5D","stage8_10_4_physical_result":"STAGE_8_10_4_TOKEN_PERMISSION_BOUNDARY_PASS","stage8_10_4_physical_validation_performed":True,"readonly_token_readonly_observed":True,"trading_token_readonly_false_observed":True,"token_permission_boundary_validated":True,"order_path_validation_performed":False,"stage8_10_5_status":stage8_10_5_status,"stage8_10_5_accepted_code_commit":"ba284e95954c8473c0e77a95172117bc5cefaf65","stage8_10_5_external_evidence_sha256":"D878309E22FA49BFFA9EE9B37200C3FE207BF77DB5C29D6DE97010F1FFCE904A","stage8_10_5_physical_result":"STAGE_8_10_5_OFFLINE_ORDER_PATH_DRY_VALIDATION_PASS","stage8_10_5_physical_validation_performed":True,"offline_dry_validation_performed":True,"order_path_dry_validation_validated":True,"stage8_10_5_external_network_calls":0,"real_order_endpoint_called":False,"real_order_count":0,"stage8_10_6_status":safety_status,"stage8_10_6_accepted_code_commit":safety_gate["accepted_code_commit"],"stage8_10_6_external_evidence_sha256":safety_gate["external_evidence_sha256"],"stage8_10_6_physical_result":safety_gate["physical_result"],"stage8_10_6_physical_validation_performed":True,"production_kill_switch_initialized":True,"production_kill_switch_halted_observed":True,"production_kill_switch_final_state":"HALTED","production_kill_switch_valid":True,"synthetic_safety_matrix_validated":True,"synthetic_case_count":25,"synthetic_open_case_count":1,"synthetic_blocked_case_count":24,"emergency_halt_validated":True,"execution_authorized":False,"stage8_10_6_external_network_calls":0,"stage8_10_7_status":token_status,"stage8_10_7_accepted_code_commit":token_acceptance["accepted_code_commit"],"stage8_10_7_external_evidence_sha256":token_acceptance["external_evidence_sha256"],"stage8_10_7_physical_result":token_acceptance["physical_result"],"stage8_10_7_physical_validation_performed":True,"stage8_10_7_trading_dpapi_current_user_validated":True,"stage8_10_7_local_readonly_trading_account_binding_validated":True,"stage8_10_7_production_kill_switch_pre_halted_observed":True,"stage8_10_7_trading_session_created":True,"stage8_10_7_expected_account_enumerated":True,"stage8_10_7_expected_account_occurrence_count":1,"stage8_10_7_trading_token_readonly_false_observed":True,"stage8_10_7_trading_token_write_boundary_confirmed":True,"stage8_10_7_remote_call_scope":"SESSION_CREATE_AND_DETAILS_ONLY","stage8_10_7_production_kill_switch_post_halted_observed":True,"stage8_10_7_trading_token_used":True,"stage8_10_7_readonly_token_used_for_remote_auth":False,"stage8_10_7_finam_authentication_performed":True,"stage8_10_7_order_endpoint_called":False,"stage8_10_7_order_count":0,"stage8_10_8_status":lifecycle_closeout.get("status"),"stage8_10_complete":True,"stage8_10_completed_gate_count":7,"stage8_10_production_kill_switch_final_state":"HALTED","stage8_10_execution_authorized":False,"stage8_10_order_endpoint_called":False,"stage8_10_order_count":0,"stage8_10_live_trading_authorized":False,"stage8_10_real_order_transmission_authorized":False,"stage8_11_status":"STAGE_8_11_CONTROLLED_REAL_EXECUTION_ACCEPTANCE_COMPLETE_PASS","stage8_12_status":"STAGE_8_12_STARTED_STAGE8_12_4_IMPLEMENTATION_NOT_AUTHORIZED","stage8_12_1_status":"STAGE_8_12_1_PRODUCTION_RUNTIME_ASSEMBLY_COMPLETE_PASS","stage8_12_1_accepted_code_commit":"3f2d68ca0c327271fb543a0b63c0e8f842c855bd","stage8_12_1_external_evidence_sha256":"F11FD6620A21F48499600392F49D3FC8A2340765B2B7B1C3C190822D8316513C","stage8_12_2_status":"STAGE_8_12_2_PRODUCTION_PATH_CONFORMANCE_AND_FAILURE_AUDIT_COMPLETE_PASS","stage8_12_2_accepted_code_commit":"2a15f4331afc1433dfbfd0464108e39e59d236f8","stage8_12_2_external_evidence_sha256":"4F58595E2F62F2A377E5525972B9E88A136B2F9BC51760268D012AF94A70AE9F","stage8_12_next_gate":"STAGE_8_12_4_EXPLICIT_FULL_R15_PRODUCTION_AUTHORIZATION","stage8_9_complete":True,"stage8_9_physical_validation_performed":True}
    if write_result: (HERE/"independent_audit_result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    return result
if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--check-only",action="store_true"); args=parser.parse_args()
    result=audit(write_result=not args.check_only); print(json.dumps(result,sort_keys=True)); raise SystemExit(result["status"]!="PASS")
