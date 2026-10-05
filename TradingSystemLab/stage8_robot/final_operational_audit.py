"""Stage 8.8.7 deterministic repository-only final operational audit.

This module deliberately reads only Git/repository material.  It never creates a
FINAM client, reads credentials, or opens the operational database.  Physical
Intel acceptance was performed externally; this audit validates only its
sanitized repository provenance and SHA-256 reference, not the evidence itself.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SPEC_ID = "PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8"
IDENTITY = "TRAIL1__N4_01__FULL__R15"
COMPLETE_STATUS = "STAGE_8_8_7_FINAL_OPERATIONAL_AUDIT_INTEL_ACCEPTANCE_COMPLETE"
HARDENING_COMPLETE = "Stage 8.8 operational hardening is COMPLETE."
INDIVIDUAL_STAGES_COMPLETE = (
    "Stages 8.8.1, 8.8.2, 8.8.3, 8.8.4, 8.8.5, 8.8.6, and 8.8.7 are COMPLETE."
)
STAGE_8_8_5_STATUS = "STAGE_8_8_5_STALE_DATA_PROTECTION_COMPLETE"
STAGE_8_8_6_STATUS = "STAGE_8_8_6_SQLITE_RECOVERY_INTEL_ACCEPTANCE_COMPLETE"
STAGE_8_8_5_SOURCE = "1c1c2bb5458827f200bc753e7e64db0272b33a8f"
STAGE_8_8_5_EVIDENCE = "C57554AE3AE54018EC1E558108520088C1883718F0406E7B6C6669B4696A9CBC"
STAGE_8_8_6_CODE = "dc2b79e74817e71435eee20103ae617e13067d8e"
STAGE_8_8_6_EVIDENCE = "1A9B62D4BFC0E7384898C9DF9659E54E50E0E202BD44CE19413864AC2ECA14D6"
STAGE_8_8_7_CODE = "bda46f57f0f977e05593c46b55851c40c4ad34fe"
STAGE_8_8_7_EVIDENCE = "181225F29A966179AB513121C3CBACD31401752956EFC9A22253A8EFBF94766E"
STAGE_8_9_STATUS = "STAGE_8_9_REAL_ACCOUNT_FUNDING_MARGIN_VALIDATION_COMPLETE"
STAGE_8_9_REASON = "ALL_AUTHORITIES_VALID"
STAGE_8_9_CODE = "1013a5a2324e015ab3bc047a7b9af9064552cd10"
STAGE_8_9_REPORT = "C87400F845B73A666B95C83DA2E3B6B710F36F3210AD4AD175BFDABB453864D5"
STAGE_8_9_SUMMARY = "099F85A0DCCF94D404411CFFAC2F5D8C80D606C5C1B5AA2F5B650E8BF5FEB636"
STAGE_8_10_1_STATUS = "STAGE_8_10_1_TRADING_TOKEN_PRECONDITIONS_COMPLETE"
STAGE_8_10_2_STATUS = "STAGE_8_10_2_SECURE_PROVISIONING_COMPLETE"
STAGE_8_10_2_CODE = "f0c271e428c05ee0ff67b7941e342c06b48a42a0"
STAGE_8_10_2_EVIDENCE = "E5FEA93CE28006BC5ADA19F1AA1C1C365FF7CF4BE48A5A1B8BC8C5589DFD754D"
STAGE_8_10_2_RESULT = "STAGE_8_10_2_PHYSICAL_SECURE_PROVISIONING_LOCAL_PASS"
STAGE_8_10_3_STATUS = "STAGE_8_10_3_IDENTITY_ACCOUNT_BINDING_COMPLETE"
STAGE_8_10_4_STATUS = "STAGE_8_10_4_PERMISSION_BOUNDARY_COMPLETE"
STAGE_8_10_5_STATUS = "STAGE_8_10_5_ORDER_PATH_DRY_VALIDATION_COMPLETE"
STAGE_8_10_6_STATUS = "STAGE_8_10_6_KILL_SWITCH_SAFETY_GATES_COMPLETE"
STAGE_8_10_7_STATUS = "STAGE_8_10_7_INTEL_TRADING_TOKEN_ACCEPTANCE_COMPLETE"
STAGE_8_10_COMPLETE_STATUS = "STAGE_8_10_TRADING_TOKEN_LIFECYCLE_COMPLETE"
STAGE_8_9_8_STATUS = "STAGE_8_9_8_COMPLETE"
STAGE_8_9_8_VARIANT = "60A529DB021B39E1C6117D01CCF3AB5B8B331073D407782E90383E4D124BADC5"
STAGE_8_9_8_SHAPE = "EED27193E35F46FFCF13CFB4A2F2EAA4AB87A35F967D78139E97BFA885009371"
BACKUP_SHA = "00b5e4ca2b389d55389b6b57ac73b5e557c11b72daab8d6e118311613e0aa3b0"
MANIFEST_SHA = "3d0ef1d7cb11ee592be32550625e8badefc596108f4d0c34eff6c5e12ceba822"
BASELINE_SHA = "13f01f1009768ddce65dce079f70486f2cbc2508cd1ea8ec4787414a78e0d3be"


def current_readme_status(document: str) -> str | None:
    """Return the single top-level backtick-delimited repository status."""
    match = re.search(r"^\*\*Status:\*\*\s+`([^`]+)`", document, re.M)
    return match.group(1) if match else None

# Byte hashes captured from the independently audited Stage 8.8.6 closeout at
# f9eec7e986d93471bcd3a43abf3c0144866b7556.  Moving result JSON and project
# status documents are intentionally excluded: they are outputs/metadata for
# this gate, not executable or frozen Stage 7 authorities.
PROTECTED_SHA256 = {
    "TradingSystemLab/stage8_robot/trading_token_intel_acceptance.py": "84d1acd85af02adfef7781d1fa01cbe5f418a53e5f3ef582224a34490a07b27b",
    "TradingSystemLab/stage8_robot/deploy/windows/validate-trading-token-intel-acceptance.ps1": "26e7dbe2ff4d262a76d13b97cca181b80a06fb662a029ba3436af1fea2930386",
    "TradingSystemLab/stage8_robot/trading_safety_gate.py": "64c781579e630836cfde7a0b772df1e2707caf35decafb9acdc75d7d2e3df6e4",
    "TradingSystemLab/stage8_robot/safety_gate_validation.py": "baf9f85f8fa3c6c789db7ce40d9d23fb13d7854c11820986f33c1c5436716b9f",
    "TradingSystemLab/stage8_robot/deploy/windows/validate-trading-safety-gates.ps1": "7da9ff0a252008f41c771866d528cbaf4ce2fc97221b87a1b933d50acb75c4d5",
    "TradingSystemLab/stage8_robot/order_path_dry_validation.py": "4bf00af63304001a5f127435d764876c02e545af7cfed1672288d6e4b8bdd460",
    "TradingSystemLab/stage8_robot/deploy/windows/validate-order-path-dry.ps1": "a1058ee61f3a9586649bb57a46e72d9d1ef49d89d3954c66df8752df05a98288",
    "TradingSystemLab/stage8_robot/trading_permission_boundary.py": "609baa9dda8859486cfdef204c99748088425c70c65895074bbb993df17b6624",
    "TradingSystemLab/stage8_robot/deploy/windows/validate-trading-permission-boundary.ps1": "c4a086e1a8ae955056bb12053d5df9f3b2de9e4106ea6ba640c6e3f2e78a4e33",
    "TradingSystemLab/stage8_robot/trading_identity_binding.py": "1303459b636c99ae7fea4e2e62863888f56ad0e12ca8311a47782a354069167e",
    "TradingSystemLab/stage8_robot/deploy/windows/validate-trading-identity-binding.ps1": "0ccaa1c6b7e37bba226c25647a068739dfcc1db2ad7c99a695752235b4a7b399",
    "TradingSystemLab/stage8_robot/readonly_supervisor.py": "1455fee5fe207c617676a0463ce3034247c5534578555cac293807da22bcaab8",
    "TradingSystemLab/stage8_robot/finam_api.py": "15c97d5557021ec50702bd9e2abf1bde4e76faf90063b973fd61f9cf9d096cb0",
    "TradingSystemLab/stage8_robot/operations.py": "1ae2e848aa3301cbd924f7165bd61a8888a586e86a792fac807b7fd6ff5cd734",
    "TradingSystemLab/stage8_robot/backup_state.py": "a841ca6d8090a893157bb87bf0ee47101c79c398b7b36e06259a7d33cf0977cd",
    "TradingSystemLab/stage8_robot/restore_state.py": "ff6adb1503e0edd53c6c3c749e4bcc3afa56b8f56042703c3000a246cd94b2cd",
    "TradingSystemLab/stage8_robot/production_instrument_registry.csv": "90d64e16dfeb292b4b339ac3eb196074e133bf52a962cc6715c488a32d16e013",
    "TradingSystemLab/stage8_robot/margin.py": "05c1c44eb199dccb126d533bdd1f4389ff78ce53d920f2b6bec967155964339e",
    "TradingSystemLab/stage8_robot/deploy/windows/run-readonly.ps1": "c91937716e84d8e746475ad27b89d32b0424cc928aeedc239c7628477d5055e3",
    "TradingSystemLab/stage8_robot/deploy/windows/credential-store.ps1": "ba7e4e14d0638d989674bb9907c070f43c03672a3b767d5eb522ecb2f5ccfa8a",
    "TradingSystemLab/stage8_robot/deploy/windows/initialize-readonly-credentials.ps1": "e8dde65ca96ffbfb6ca6171a5eb71298040fc4d500a31f0b3e65722ac35fd118",
    "TradingSystemLab/stage8_robot/deploy/windows/verify-readonly-credentials.ps1": "ff84620a5bf5c705730428420a053e682715cfc22e9fa1cdc1d476bc2859e0ae",
    "TradingSystemLab/stage8_robot/deploy/windows/install-task.ps1": "18f3b65b401f9ced6c55b49e8a7b6f7b7711c53671c7b445835101bd77cba478",
    "TradingSystemLab/stage8_robot/deploy/windows/trading-credential-store.ps1": "c9fd0d7abb38776bc854e5975bce909af98cc683fdf4a34325a0e34100ef8014",
    "TradingSystemLab/stage8_robot/deploy/windows/initialize-trading-credentials.ps1": "d3265a7dd468607560e2e720638dbd41f7519a798b04eb7ad846e6511ce721a9",
    "TradingSystemLab/stage8_robot/deploy/windows/verify-trading-credentials.ps1": "eee8d08d9abbecefb94fe2cb4397761e0292194f557c9124e5d01ed4ab2a40d1",
    "TradingSystemLab/results/post_v3_analysis/stage7_production_specification_freeze/production_specification.json": "c719bb3e7b9a7e707077fc499867613010068d623d6879c247f480f7658aff7c",
    "TradingSystemLab/results/post_v3_analysis/stage7_production_specification_freeze/production_identity_registry.csv": "5418fb19d4aaa32b4292fce0425a644c4bf70a5451e78fd2a801b5dc8dd003aa",
    "TradingSystemLab/results/post_v3_analysis/stage7_production_specification_freeze/source_provenance.json": "4d6e3d7d221e019ea00faa3d523affd39d0b45df3f6898c41e2e8c7ed4c3d494",
    "TradingSystemLab/results/post_v3_analysis/stage7_production_specification_freeze/audit_production_specification.py": "5731466205611bb3b1b0e89370afef639594c776883d31fa59f7362f82d174df",
}


def _run_json(command: list[str], root: Path) -> dict:
    completed = subprocess.run(command, cwd=root, check=False, text=True, capture_output=True)
    if completed.returncode:
        return {"status": "FAIL", "checks": 0, "errors": ["SUBAUDIT_EXECUTION_FAILED"]}
    try:
        return json.loads(completed.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        return {"status": "FAIL", "checks": 0, "errors": ["SUBAUDIT_RESULT_UNREADABLE"]}


def _protected_sha256(raw: bytes) -> str:
    """Hash protected text using the canonical Git/GitHub LF representation."""
    canonical = raw.replace(b"\r\n", b"\n")
    return hashlib.sha256(canonical).hexdigest()


def _stage8_10_document_consistency(document: str) -> tuple[bool, bool, bool]:
    """Independently validate active handoff and chronological prose semantics."""
    historical_labels = ("historical", "at the time", "in this historical snapshot",
                         "subsequently", "later", "current authority is recorded below")
    stale_next = False
    inconsistent = False
    for paragraph in re.split(r"\n\s*\n", document):
        normalized = " ".join(paragraph.split())
        lower = normalized.lower()
        historical = any(label in lower for label in historical_labels)
        if (re.search(r"stage 8\.10\.[1-8]\s+(?:(?:is\s+)?(?:\*\*)?complete(?:\*\*)?\s+(?:and\s+is\s+)?|is\s+(?:the\s+)?)next (?:separate )?(?:lifecycle )?gate",
                      normalized, re.I)
                or (re.search(r"Stage 8\.10\.8 is (?:\*\*)?COMPLETE", normalized, re.I)
                    and "next separate lifecycle gate" in lower)
                or (re.search(r"Stage 8\.10\.8 is (?:\*\*)?COMPLETE", normalized, re.I)
                    and "not implemented or executed here" in lower)):
            stale_next = True
        earlier_not_started = re.search(
            r"Stage 8\.10\.[1-7].{0,40}(?:\*\*)?NOT STARTED", normalized, re.I)
        later_complete = re.search(r"Stage 8\.10\.8 is (?:\*\*)?COMPLETE", normalized, re.I)
        active_8107 = re.search(r"Stage 8\.10\.7.{0,40}(?:\*\*)?NOT STARTED", normalized, re.I)
        stage11_invalid = re.search(r"Stage 8\.11.{0,40}(?:is|=) (?:\*\*)?(?:STARTED|AUTHORIZED)", normalized, re.I)
        if not historical and (active_8107 or stage11_invalid or (earlier_not_started and later_complete)):
            inconsistent = True
    match = re.search(r"^## Current handoff\s*$\n(.*?)(?=^## |\Z)", document, re.M | re.S)
    handoff = match.group(1) if match else ""
    exact = bool(match and all(token in handoff for token in (
        "Stage 8.9 is **COMPLETE**", "Stage 8.10 is **COMPLETE**", "`HALTED`",
        "Stage 8.11.0 — **COMPLETE**", "Stage 8.11.1 — **COMPLETE / PASS**",
        "Stage 8.11.2 — **COMPLETE / PASS**", "prior explicit authorization **CONSUMED**",
        "Stage 8.11.4 — **ATTEMPTED / FAILED HTTP 400 / NO ACCEPTED ENTRY**",
        "Stage 8.11.7 — **COMPLETE / PASS / HISTORICAL INTENT RECOVERED**",
        "Stage 8.11.8 — **COMPLETE / STAGE 8.11 CLOSEOUT**", "Stage 8.12 — **NOT STARTED / NOT AUTHORIZED**",
        "Scheduled Task is `Disabled`", "new explicit operator authorization")))
    if match and re.search(r"next (?:possible )?(?:lifecycle )?gate is Stage 8\.10\.[1-8]", handoff, re.I):
        stale_next = True
    return exact, not inconsistent, not stale_next


def _stage8_10_6_python_safe(source: str) -> bool:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    forbidden_modules = ("finam_api", "broker", "runner", "urllib.request", "requests", "httpx",
                         "socket", "http.client", "subprocess")
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name.lower() for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append((node.module or "").lower())
            imports.extend(alias.name.lower() for alias in node.names)
    forbidden_calls = {"urlopen", "request", "post", "put", "patch", "delete", "place_order",
                       "submit_order", "cancel_order", "modify_order"}
    calls = {node.func.attr.lower() if isinstance(node.func, ast.Attribute) else node.func.id.lower()
             for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, (ast.Attribute, ast.Name))}
    return (not any(module == term or module.startswith(term + ".")
                    for module in imports for term in forbidden_modules)
            and not calls.intersection(forbidden_calls))


def _stage8_10_6_semantics(safety: str, validation: str, wrapper: str) -> tuple[bool, bool, bool]:
    safety_required = (
        'return None, "KILL_SWITCH_MISSING"', 'return None, "KILL_SWITCH_INVALID"',
        'if switch["state"] == "HALTED": reasons.append("KILL_SWITCH_HALTED")',
        'if execution_authorized is not True: reasons.append("EXECUTION_NOT_AUTHORIZED")',
        'heartbeat.get("health_status") == "HEALTHY"', 'heartbeat.get("reconciliation_status") == "PASS"',
        'heartbeat.get("entries_enabled") is False', 'heartbeat.get("unresolved_order_count") == 0',
        'heartbeat.get("failure_code") is None', 'heartbeat.get("consecutive_failures") == 0',
        'heartbeat.get("cycle_count") >= 1',
        'elif age > MAX_HEARTBEAT_AGE_SECONDS: reasons.append("HEARTBEAT_STALE")',
        'elif age > MAX_HEARTBEAT_AGE_SECONDS: reasons.append("FINAM_CONTACT_STALE")',
        'last_successful_finam_api_contact', '_HASH.fullmatch', 'REPOSITORY_OUTPUT_FORBIDDEN',
    )
    report_required = ('"production_kill_switch_initialized": True',
                       '"production_kill_switch_final_state": "HALTED"',
                       '"production_kill_switch_valid": True', '--production-runtime-root',
                       'load_kill_switch(root)')
    wrapper_forbidden = ("credential-store.ps1", "trading-credential-store.ps1", "get-readonlycredential",
        "get-tradingcredential", "initialize-readonly-credentials", "initialize-trading-credentials",
        "invoke-webrequest", "invoke-restmethod", "curl", "wget", "run-readonly", "install-task", "runner", "broker",
        "enable-scheduledtask", "start-scheduledtask", "register-scheduledtask", "allow_arm",
        "execution_authorized=true")
    lower = wrapper.lower()
    offline = (_stage8_10_6_python_safe(safety) and _stage8_10_6_python_safe(validation)
               and all(item in safety for item in safety_required))
    halt_only = (not any(item in lower for item in wrapper_forbidden)
                 and not re.search(r"execution[_-]?authorized\s*=\s*\$?true", lower))
    report_contract = all(item in validation for item in report_required) and "--production-runtime-root $runtime" in wrapper
    return offline, halt_only, report_contract


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


def audit(
    root: Path = ROOT,
    *,
    write_result: bool = True,
    text_overrides: dict[str, str] | None = None,
    tracked_files: list[str] | None = None,
    stage7_result: dict | None = None,
    stage8_result: dict | None = None,
) -> dict:
    """Audit repository authorities; injectable inputs support mutation tests."""
    root = root.resolve()
    overrides = text_overrides or {}

    def content(relative: str) -> bytes:
        if relative in overrides:
            return overrides[relative].encode()
        return (root / relative).read_bytes()

    def text(relative: str) -> str:
        return content(relative).decode()

    if tracked_files is None:
        raw = subprocess.run(["git", "ls-files", "-z"], cwd=root, check=True, capture_output=True).stdout
        tracked_files = [name for name in raw.decode().split("\0") if name]
    if stage7_result is None:
        stage7_result = _run_json([
            sys.executable,
            "TradingSystemLab/results/post_v3_analysis/stage7_production_specification_freeze/audit_production_specification.py",
            "--check-only",
        ], root)
    if stage8_result is None:
        stage8_result = _run_json([
            sys.executable, "TradingSystemLab/stage8_robot/audit_stage8.py", "--check-only"
        ], root)

    errors: list[str] = []
    checks = 0

    def check(condition: bool, name: str) -> None:
        nonlocal checks
        checks += 1
        if not condition:
            errors.append(name)

    docs_paths = ["TradingSystemLab/CURRENT_STATE.md", "TradingSystemLab/ROADMAP.md",
                  "TradingSystemLab/stage8_robot/README.md"]
    docs = [text(path) for path in docs_paths]
    normalized_docs = [" ".join(doc.split()) for doc in docs]
    joined_docs = "\n".join(docs)
    stage8_9_docs_paths = [*docs_paths, "TradingSystemLab/PROJECT_CONTEXT.md"]
    stage8_9_docs = [text(path) for path in stage8_9_docs_paths]
    stage8_9_joined_docs = "\n".join(stage8_9_docs)
    document_verdicts = [_stage8_10_document_consistency(doc) for doc in stage8_9_docs]
    check(all(verdict[0] for verdict in document_verdicts), "STAGE_8_10_CURRENT_HANDOFF_EXACT")
    check(all(verdict[1] for verdict in document_verdicts), "STAGE_8_10_HISTORICAL_SCOPE_CONSISTENT")
    check(all(verdict[2] for verdict in document_verdicts), "STAGE_8_10_NO_STALE_NEXT_GATE")
    spec = json.loads(text("TradingSystemLab/results/post_v3_analysis/stage7_production_specification_freeze/production_specification.json"))
    conformance = json.loads(text("TradingSystemLab/stage8_robot/conformance_report.json"))
    provenance = json.loads(text("TradingSystemLab/stage8_robot/authority_provenance.json"))

    check(spec.get("production_specification_id") == SPEC_ID, "PRODUCTION_SPECIFICATION_ID_EXACT")
    check(spec.get("identity") == IDENTITY, "PRODUCTION_IDENTITY_EXACT")
    check(spec.get("strategy", {}).get("name") == "T3" and spec.get("strategy", {}).get("timeframe") == "H1", "T3_H1_FROZEN")
    check(spec.get("basket", {}).get("instruments") == ["USDRUBF", "CNYRUBF", "GLDRUBF", "IMOEXF"], "N4_EXACT")
    risk = spec.get("risk", {})
    check(spec.get("variant", {}).get("name") == "TRAIL1" and risk.get("load") == "FULL" and risk.get("mode") == "R15", "TRAIL1_FULL_R15")
    check(risk.get("risk_fraction_per_new_instrument_position") == .015 and risk.get("maximum_nominal_simultaneous_initial_risk") == .06, "REALIZED_EQUITY_RISK_LIMITS")
    check("fallback" not in json.dumps(spec).lower(), "NO_CANONICAL_PRODUCTION_FALLBACK")

    check(stage7_result.get("status") == "PASS" and not stage7_result.get("errors"), "STAGE7_AUDIT_PASS")
    check(stage7_result.get("checks") == 22 and stage7_result.get("mutation_test_count") == 19, "STAGE7_AUDIT_AND_MUTATION_COUNTS")
    check(stage7_result.get("production_specification_id") == SPEC_ID, "STAGE7_AUDIT_PRODUCTION_ID")
    for layer in ("authority_replay", "production_robot_replay"):
        replay = conformance.get(layer, {})
        check(replay.get("status") == "PASS" and replay.get("expected_trade_count") == replay.get("reproduced_trade_count") == replay.get("exact_matches") == 418, f"STAGE7_{layer.upper()}_418")
        check(not sum(replay.get(key, 0) for key in ("missing", "extra", "timestamp_mismatches", "direction_mismatches", "price_mismatches", "state_mismatches", "R_mismatches")), f"STAGE7_{layer.upper()}_ZERO_MISMATCHES")

    check(stage8_result.get("status") == "PASS" and not stage8_result.get("errors") and isinstance(stage8_result.get("checks"), int), "STAGE8_DYNAMIC_AUDIT_PASS")
    check(stage8_result.get("production_specification_id") == SPEC_ID, "STAGE8_AUDIT_PRODUCTION_ID")
    check(stage8_result.get("live_trading_activated") is False, "STAGE8_LIVE_FALSE")

    check(all(HARDENING_COMPLETE in doc for doc in docs), "STAGE_8_8_OPERATIONAL_HARDENING_COMPLETE")
    check(
        all(INDIVIDUAL_STAGES_COMPLETE in doc for doc in normalized_docs),
        "STAGE_8_8_1_THROUGH_8_8_7_COMPLETE",
    )
    check(all(STAGE_8_8_5_STATUS in doc for doc in docs), "STAGE_8_8_5_COMPLETE_SYNCHRONIZED")
    check(all(STAGE_8_8_5_SOURCE in doc and STAGE_8_8_5_EVIDENCE in doc for doc in docs), "STAGE_8_8_5_PROVENANCE_SYNCHRONIZED")
    check(all(STAGE_8_8_6_STATUS in doc for doc in docs), "STAGE_8_8_6_COMPLETE_SYNCHRONIZED")
    check(all(STAGE_8_8_6_CODE in doc and STAGE_8_8_6_EVIDENCE in doc for doc in docs), "STAGE_8_8_6_PROVENANCE_SYNCHRONIZED")
    check(all(value in joined_docs for value in (BACKUP_SHA, MANIFEST_SHA, BASELINE_SHA)), "STAGE_8_8_6_RECOVERY_HASHES_RECORDED")

    bad_hashes = [path for path, expected in PROTECTED_SHA256.items() if _protected_sha256(content(path)) != expected]
    check(not bad_hashes, "PROTECTED_IMPLEMENTATION_HASHES:" + ",".join(bad_hashes))

    supervisor = text("TradingSystemLab/stage8_robot/readonly_supervisor.py")
    api = text("TradingSystemLab/stage8_robot/finam_api.py")
    operations = text("TradingSystemLab/stage8_robot/operations.py")
    backup = text("TradingSystemLab/stage8_robot/backup_state.py")
    restore = text("TradingSystemLab/stage8_robot/restore_state.py")
    tests = text("TradingSystemLab/stage8_robot/tests/test_readonly_supervisor.py")
    check(all(token in supervisor for token in ("EARLY_TRADING", "CORE_TRADING", "LATE_TRADING", "STALE_COMPLETED_H1_DATA", 'f"expected_h1:{name}"', "expected not in raw_opens", "derived or prior_expected", "H1_EXPECTED_COMPLETED_WATERMARK_UNAVAILABLE")), "H1_FRESHNESS_MODEL")
    check("min(opened+timedelta(hours=1),end)" in api and "cycle_count\"] == 0" in tests, "H1_PARTIAL_COMPLETION_AND_STALE_IMMUTABILITY")
    check(all(token in operations + backup + restore for token in ("readonly-supervisor.sqlite3", "src.backup(dst)", "PRAGMA integrity_check", "PRODUCTION_SPECIFICATION_ID", "sha256", "InstanceLock", "quarantine", "CLEANUP_PENDING_BASENAME")), "SQLITE_RECOVERY_DESIGN")
    recovery_tests = text("TradingSystemLab/stage8_robot/tests/test_sqlite_recovery.py")
    check("os._exit(0)" in recovery_tests and "test_windows_external_open_database_fails_restore_closed" in recovery_tests, "SQLITE_WAL_AND_WINDOWS_REGRESSIONS")

    win_paths = [path for path in PROTECTED_SHA256 if "/deploy/windows/" in path]
    windows = "\n".join(text(path) for path in win_paths)
    launcher = text("TradingSystemLab/stage8_robot/deploy/windows/run-readonly.ps1")
    installer = text("TradingSystemLab/stage8_robot/deploy/windows/install-task.ps1")
    check("DataProtectionScope]::CurrentUser" in windows and "LocalMachine" not in windows, "WINDOWS_CURRENT_USER_DPAPI_ONLY")
    check("setx" not in windows.lower() and "SetEnvironmentVariable" not in windows, "WINDOWS_NO_PERSISTENT_SECRET_ENVIRONMENT")
    check("FINAM_API_SECRET" not in installer.split("New-ScheduledTaskAction", 1)[1].splitlines()[0] and "FINAM_REAL_ACCOUNT_ID" not in installer.split("New-ScheduledTaskAction", 1)[1].splitlines()[0], "WINDOWS_TASK_ARGUMENTS_SECRET_FREE")
    check("-UserId $principal.Name" in installer and "SYSTEM" not in installer, "WINDOWS_MATCHED_NON_SYSTEM_PRINCIPAL")
    check("PRODUCTION_SPECIFICATION_ID" in windows and "SetAccessRuleProtection" in windows and "Set-Acl" in windows, "WINDOWS_PRODUCTION_BINDING_PRIVATE_ACL")
    check('$env:FINAM_MODE = "REAL_READONLY"' in launcher and '$env:NEW_ENTRIES_DISABLED = "true"' in launcher, "WINDOWS_READONLY_ENTRIES_DISABLED_FORCED")
    launcher_commands = "\n".join(line for line in launcher.splitlines() if not line.lstrip().startswith("#"))
    check("TradingSystemLab.stage8_robot.readonly_supervisor" in launcher_commands and "TradingSystemLab.stage8_robot.real_account_smoke" not in launcher_commands, "WINDOWS_READONLY_SERVICE_TARGET")

    operational = [
        "TradingSystemLab/stage8_robot/readonly_supervisor.py", "TradingSystemLab/stage8_robot/backup_state.py",
        "TradingSystemLab/stage8_robot/restore_state.py", "TradingSystemLab/stage8_robot/operations.py",
        *win_paths,
    ]
    forbidden_calls = {"place_order", "submit_order", "cancel_order", "modify_order"}
    calls: set[str] = set()
    for path in operational:
        if path.endswith(".py"):
            calls.update(node.func.attr for node in ast.walk(ast.parse(text(path))) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute))
        else:
            calls.update(name for name in forbidden_calls if name in text(path))
    check(not calls.intersection(forbidden_calls), "OPERATIONAL_MODULES_NO_ORDER_CALLS")
    broker = text("TradingSystemLab/stage8_robot/broker.py")
    config = text("TradingSystemLab/stage8_robot/config.py")
    check('raise RuntimeError("REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED")' in broker, "REAL_ORDER_TRANSMISSION_BLOCKED")
    check("LIVE_TRADING_NOT_AUTHORIZED" in config and 'FINAM_MODE","DRY_RUN' in config, "LIVE_TRADING_BLOCKED")

    def forbidden_artifact(path: str) -> bool:
        lower = path.lower()
        name = Path(lower).name
        runtime_suffix = lower.endswith((".sqlite3", "-wal", "-shm", ".dpapi", ".jwt"))
        external_acceptance = "acceptance" in name and name.endswith(".json") and "tests/" not in lower
        external_stage8_9 = ("stage8_9" in name or "funding_margin_validation" in name) and name.endswith(".json")
        external_stage8_10_3 = name in {"stage8_10_3_identity_account_binding.json", "stage8_10_4_permission_boundary.json", "stage8_10_5_order_path_dry_validation.json"}
        raw_capture = any(term in name for term in ("raw_finam", "account_response", "real_market_capture", "stale_h1_evidence"))
        credential = any(term in name for term in ("credential", "secret")) and not lower.endswith((".py", ".ps1", ".md", ".example"))
        trading_token = any(term in name for term in ("trading_token", "trading-token", "token_1", "token1")) and lower.endswith((".json", ".txt", ".bin", ".blob", ".dpapi", ".env"))
        account_material = any(term in name for term in ("account_id", "account-identifier")) and lower.endswith((".json", ".txt", ".bin", ".blob", ".env"))
        return runtime_suffix or external_acceptance or external_stage8_9 or external_stage8_10_3 or raw_capture or credential or trading_token or account_material

    runtime_artifacts = sorted(path for path in tracked_files if forbidden_artifact(path))
    check(not runtime_artifacts, "RUNTIME_OR_SECRET_ARTIFACT_TRACKED")

    check(all(COMPLETE_STATUS in doc for doc in docs), "STAGE_8_8_7_COMPLETE_STATUS_SYNCHRONIZED")
    check(all(STAGE_8_8_7_CODE in doc and STAGE_8_8_7_EVIDENCE in doc for doc in docs), "STAGE_8_8_7_EXTERNAL_PROVENANCE_SYNCHRONIZED")
    stage8_9_status = STAGE_8_9_STATUS
    required = (STAGE_8_9_STATUS, STAGE_8_9_REASON, STAGE_8_9_CODE,
                STAGE_8_9_REPORT, STAGE_8_9_SUMMARY,
                "STAGE_8_9_10_POST_FUNDING_REVALIDATION_PASS=1",
                "sizing_case_count = 8",
                "positive_capacity_case_count = 4", "zero_capacity_case_count = 4",
                "positive_batch_reservation_count = 1")
    check(all(all(value in doc for value in required) for doc in stage8_9_docs),
          "STAGE_8_9_10_COMPLETED_PROVENANCE_SYNCHRONIZED")
    lifecycle = provenance.get("stage8_9_8", {})
    closeout = provenance.get("stage8_9_10", {})
    preconditions = provenance.get("stage8_10_1", {})
    provisioning = provenance.get("stage8_10_2", {})
    identity_binding = provenance.get("stage8_10_3", {})
    permission_boundary = provenance.get("stage8_10_4", {})
    dry_gate = provenance.get("stage8_10_5", {})
    safety_gate = provenance.get("stage8_10_6", {})
    token_acceptance = provenance.get("stage8_10_7", {})
    lifecycle_closeout = provenance.get("stage8_10_8", {})
    acceptance = text("TradingSystemLab/stage8_robot/controlled_real_acceptance.py")
    finam_api_source = text("TradingSystemLab/stage8_robot/finam_api.py")
    acceptance_integration = text("TradingSystemLab/stage8_robot/tests/test_controlled_real_acceptance_finam_integration.py")
    evidence_schema = json.loads(text("TradingSystemLab/stage8_robot/stage8_11_physical_evidence.schema.json"))
    normal_config = text("TradingSystemLab/stage8_robot/config.py")
    normal_broker = text("TradingSystemLab/stage8_robot/broker.py")
    normal_runner = text("TradingSystemLab/stage8_robot/runner.py")
    normal_supervisor = text("TradingSystemLab/stage8_robot/readonly_supervisor.py")
    task_installer = text("TradingSystemLab/stage8_robot/deploy/windows/install-task.ps1")
    launcher = text("TradingSystemLab/stage8_robot/deploy/windows/run-readonly.ps1")
    check("request.quantity != MAX_ACCEPTANCE_QUANTITY" in acceptance and "MAX_ACCEPTANCE_QUANTITY = 1" in acceptance,
          "STAGE_8_11_EXACTLY_ONE_HARD_CAP")
    check("self.store.persist_intent" in acceptance and acceptance.find("self.store.persist_intent") < acceptance.find("self.api.place_order"),
          "STAGE_8_11_INTENT_BEFORE_POST")
    check("no retry: exactly one call" in acceptance and acceptance.count("self.api.place_order") == 1,
          "STAGE_8_11_NO_POST_RETRY")
    check(all(token in acceptance for token in ("ENTRY_UNCERTAIN_RECONCILE", "FLATTEN_UNCERTAIN_RECONCILE",
          "OPERATOR_INTERVENTION_REQUIRED", "class ReconciliationPending",
          "RECONCILIATION_MAX_OBSERVATIONS = 12", "ORDER_COLLECTION_PROPAGATION_PENDING",
          "TRADE_PROPAGATION_PENDING")), "STAGE_8_11_UNCERTAIN_RECONCILIATION")
    check("_digest(account_id) != accepted_account_hash.lower()" in acceptance and "heartbeat_account_hash" in acceptance,
          "STAGE_8_11_EXACT_ACCOUNT_BINDING")
    check("resolve_frozen_symbol(instrument)" in acceptance and "FINAM_SYMBOL_BINDING_INVALID" in acceptance,
          "STAGE_8_11_EXACT_N4_SYMBOL_BINDING")
    check(all(token in acceptance for token in ('result.update(classification="SYNTHETIC_PASS", entry_fill_proven=True', "one_contract_position_observed=True",
          "flatten_fill_proven=True", "_account_is_clean(final)", '"HALTED"')),
          "STAGE_8_11_FILL_FLAT_HALTED_PASS")
    check('int(entry.get("executed_quantity", -1)) != 0 or not _account_is_clean(final)' in acceptance,
          "STAGE_8_11_NO_FILL_REQUIRES_CLEAN_ACCOUNT_PROOF")
    check('final["unexpected_position_count"] == 0' in acceptance
          and 'if row_symbol != symbol and quantity != 0' in acceptance,
          "STAGE_8_11_FINAL_RECONCILIATION_ALL_POSITIONS")
    check('if _status(row.get("status")) in ACTIVE' in acceptance and "acceptance_ids" not in acceptance,
          "STAGE_8_11_FINAL_RECONCILIATION_ALL_ACTIVE_ORDERS")
    props=evidence_schema.get("properties",{}); gates=props.get("preflight_gate_outcomes",{})
    check(evidence_schema.get("additionalProperties") is False and gates.get("additionalProperties") is False
          and props.get("quantity",{}).get("const") == 1
          and {"attempt_id", "entry_fill_proven"}.issubset(evidence_schema.get("required",[])),
          "STAGE_8_11_EVIDENCE_PRIVACY_SCHEMA")
    check(all("controlled_real_acceptance" not in source for source in
              (normal_runner,normal_supervisor,task_installer,launcher)),
          "STAGE_8_11_NO_ROUTINE_OR_SCHEDULED_INTEGRATION")
    check("LIVE_TRADING_NOT_AUTHORIZED" in normal_config and "REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED" in normal_broker,
          "STAGE_8_11_EXISTING_AIRGAPS_INTACT")
    api_methods = {node.name for node in ast.parse(finam_api_source).body
                   if isinstance(node, ast.ClassDef) and node.name == "FinamAPI"
                   for node in node.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    acceptance_api_calls = {node.func.attr for node in ast.walk(ast.parse(acceptance))
                            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                            and (isinstance(node.func.value, ast.Name) and node.func.value.id == "api"
                                 or isinstance(node.func.value, ast.Attribute)
                                 and isinstance(node.func.value.value, ast.Name)
                                 and node.func.value.value.id == "self" and node.func.value.attr == "api")}
    check(acceptance_api_calls <= api_methods
          and "acceptance_snapshot" not in acceptance and "acceptance_account_snapshot" not in acceptance,
          "STAGE_8_11_PRODUCTION_FINAM_API_CONTRACT")
    check('return _rows(account, "positions")' in acceptance and '_rows(account, "trades")' not in acceptance,
          "STAGE_8_11_TRADES_NOT_FROM_ACCOUNT")
    check("def trades(self,account_id)" in finam_api_source
          and 'f"/v1/accounts/{account_id}/trades"' in finam_api_source,
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
    check(current_readme_status(text("TradingSystemLab/stage8_robot/README.md")) == STAGE_8_10_COMPLETE_STATUS,
          "STAGE_8_ROBOT_README_CURRENT_STATUS_EXACT")
    check(lifecycle.get("status") == STAGE_8_9_8_STATUS
          and lifecycle.get("stage8_9_9") == "PHYSICAL_REVALIDATION_COMPLETE"
          and lifecycle.get("stage8_9_complete") is True,
          "STAGE_8_9_LIFECYCLE_COMPLETE")
    check(closeout.get("status") == STAGE_8_9_STATUS
          and closeout.get("accepted_code_commit") == STAGE_8_9_CODE
          and closeout.get("diagnostic_report_sha256") == STAGE_8_9_REPORT
          and closeout.get("physical_summary_sha256") == STAGE_8_9_SUMMARY
          and closeout.get("sizing_case_count") == 8
          and closeout.get("positive_capacity_case_count") == 4
          and closeout.get("zero_capacity_case_count") == 4
          and closeout.get("positive_batch_reservation_count") == 1
          and closeout.get("stage8_9_complete") is True
          and closeout.get("stage8_10_status") == "IN_PROGRESS",
          "STAGE_8_9_10_PROVENANCE_EXACT")
    check(closeout.get("physical_result") == "STAGE_8_9_10_POST_FUNDING_REVALIDATION_PASS=1"
          and closeout.get("funding_classification") == "STAGE_8_9_FUNDING_MARGIN_VALIDATED"
          and closeout.get("reason") == "ALL_AUTHORITIES_VALID",
          "STAGE_8_9_10_PHYSICAL_PASS_RECORDED")
    historical_tokens = ("BLOCKED_ACCOUNT_FINANCIALS_UNAVAILABLE", "FORTS_PORTFOLIO_MISSING",
                         "BLOCKED_INSUFFICIENT_CONTRACT_CAPACITY", "ZERO_CONTRACT_CAPACITY")
    historical_labels = ("earlier", "previous", "historical", "old implementation", "pre-funding")
    stale_unlabelled = []
    for path, doc in zip(stage8_9_docs_paths, stage8_9_docs):
        for paragraph in re.split(r"\n\s*\n", doc):
            if any(token in paragraph for token in historical_tokens) and not any(
                label in paragraph.lower() for label in historical_labels
            ):
                stale_unlabelled.append(path)
    check(not stale_unlabelled, "STAGE_8_9_HISTORICAL_BLOCKERS_NOT_CURRENT")
    lifecycle_contradiction = re.compile(
        r"Stage 8\.9.{0,120}(?:NOT\s+COMPLETE|CURRENT.{0,40}BLOCKED|must not be described.{0,40}complete)",
        re.I | re.S,
    )
    active_contradictions = []
    for path, doc in zip(stage8_9_docs_paths, stage8_9_docs):
        for paragraph in re.split(r"\n\s*\n", doc):
            if lifecycle_contradiction.search(paragraph) and not any(
                label in paragraph.lower() for label in historical_labels
            ):
                active_contradictions.append(path)
    check(not active_contradictions, "STAGE_8_9_NO_ACTIVE_LIFECYCLE_CONTRADICTION")
    check(all("Stage 8.9 is **COMPLETE**" in doc for doc in stage8_9_docs),
          "STAGE_8_9_COMPLETE_SYNCHRONIZED")
    check(all(STAGE_8_10_1_STATUS in doc for doc in stage8_9_docs),
          "STAGE_8_10_1_COMPLETE_SYNCHRONIZED")
    check(preconditions.get("status") == STAGE_8_10_1_STATUS
          and preconditions.get("order_count") == 0
          and preconditions.get("stage8_10_3_through_8_status") == "NOT_STARTED"
          and preconditions.get("trading_token_provisioned") is False
          and preconditions.get("trading_token_used") is False,
          "STAGE_8_10_1_MACHINE_AUTHORITY_EXACT")
    check(all("Stage 8.10 is **COMPLETE**" in doc for doc in stage8_9_docs),
          "STAGE_8_10_COMPLETE_SYNCHRONIZED")
    check(all("Stage 8.10.2 is **COMPLETE**" in doc
              and STAGE_8_10_2_STATUS in doc
              and STAGE_8_10_2_CODE in doc
              and STAGE_8_10_2_EVIDENCE in doc
              and STAGE_8_10_2_RESULT in doc for doc in stage8_9_docs),
          "STAGE_8_10_2_COMPLETE_SYNCHRONIZED")
    check(provisioning.get("status") == STAGE_8_10_2_STATUS
          and provisioning.get("accepted_code_commit") == STAGE_8_10_2_CODE
          and provisioning.get("external_evidence_sha256") == STAGE_8_10_2_EVIDENCE
          and provisioning.get("physical_result") == STAGE_8_10_2_RESULT
          and provisioning.get("physical_provisioning_performed") is True
          and provisioning.get("trading_token_provisioned") is True
          and provisioning.get("trading_token_used") is False
          and provisioning.get("finam_authentication_performed") is False
          and provisioning.get("order_count") == 0
          and provisioning.get("stage8_10_status") == "IN_PROGRESS"
          and provisioning.get("stage8_10_3_status") == "NOT_STARTED"
          and provisioning.get("stage8_10_3_through_8_status") == "NOT_STARTED"
          and provisioning.get("stage8_11_status") == "NOT_STARTED_NOT_AUTHORIZED"
          and provisioning.get("stage8_12_status") == "NOT_STARTED_NOT_AUTHORIZED",
          "STAGE_8_10_2_MACHINE_AUTHORITY_EXACT")
    trading_store = text("TradingSystemLab/stage8_robot/deploy/windows/trading-credential-store.ps1")
    launcher = text("TradingSystemLab/stage8_robot/deploy/windows/run-readonly.ps1")
    installer = text("TradingSystemLab/stage8_robot/deploy/windows/install-task.ps1")
    check("DataProtectionScope]::CurrentUser" in trading_store
          and "TradingSystemLab.Stage8.TradingToken.v1" in trading_store
          and "TRADING_CAPABLE_NOT_AUTHORIZED" in trading_store
          and "REAL_READONLY" not in trading_store,
          "TRADING_DPAPI_STORE_SEPARATE_FAIL_CLOSED")
    check("trading-credential" not in launcher.lower() and "trading-credential" not in installer.lower()
          and "finam-trading-token" not in launcher.lower() and "finam-trading-token" not in installer.lower(),
          "TRADING_STORE_NOT_RUNTIME_WIRED")
    check(all(STAGE_8_10_3_STATUS in doc and "Stage 8.10.3 is **COMPLETE**" in doc for doc in stage8_9_docs), "STAGE_8_10_3_CODE_READY_SYNCHRONIZED")
    check(identity_binding.get("status") == STAGE_8_10_3_STATUS
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
          and identity_binding.get("order_count") == 0
          and identity_binding.get("order_endpoint_called") is False
          and identity_binding.get("live_trading_authorized") is False
          and identity_binding.get("real_order_transmission_authorized") is False
          and identity_binding.get("stage8_10_status") == "IN_PROGRESS"
          and identity_binding.get("stage8_10_4_status") == "NOT_STARTED"
          and identity_binding.get("stage8_10_5_through_8_status") == "NOT_STARTED"
          and identity_binding.get("stage8_11_status") == "NOT_STARTED_NOT_AUTHORIZED"
          and identity_binding.get("stage8_12_status") == "NOT_STARTED_NOT_AUTHORIZED", "STAGE_8_10_3_MACHINE_AUTHORITY_EXACT")
    identity_source = text("TradingSystemLab/stage8_robot/trading_identity_binding.py")
    identity_wrapper = text("TradingSystemLab/stage8_robot/deploy/windows/validate-trading-identity-binding.ps1")
    identity_calls = {node.func.attr for node in ast.walk(ast.parse(identity_source)) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
    check(not identity_calls.intersection({"place_order","cancel_order","submit_order","orders","order","account","assets","asset","asset_params","schedule","bars"}) and {"create_session","session_details"}.issubset(identity_calls), "STAGE_8_10_3_SESSION_ONLY_NO_ORDER_CAPABILITY")
    check("trading_identity_binding" not in launcher + installer and all(term not in identity_wrapper.lower() for term in ("run-readonly","install-task","scheduledtask","runner","broker","/orders")), "STAGE_8_10_3_NOT_RUNTIME_OR_TASK_WIRED")
    permission_source = text("TradingSystemLab/stage8_robot/trading_permission_boundary.py")
    permission_wrapper = text("TradingSystemLab/stage8_robot/deploy/windows/validate-trading-permission-boundary.ps1")
    check(all(STAGE_8_10_4_STATUS in doc and "Stage 8.10.4 is **COMPLETE**" in doc for doc in stage8_9_docs), "STAGE_8_10_4_COMPLETE_SYNCHRONIZED")
    check(permission_boundary.get("status") == STAGE_8_10_4_STATUS
          and permission_boundary.get("accepted_code_commit") == "44858bacc2902591e11adc85cfa5f79e2b62dd5b"
          and permission_boundary.get("external_evidence_sha256") == "E4AEDC153F89E000EC034E5F33A6EF7BECB5DA29BA253BC0B28B2AC3D0C26C5D"
          and permission_boundary.get("physical_result") == "STAGE_8_10_4_TOKEN_PERMISSION_BOUNDARY_PASS"
          and permission_boundary.get("physical_validation_performed") is True
          and permission_boundary.get("local_readonly_trading_account_binding_validated") is True
          and permission_boundary.get("readonly_session_created") is True
          and permission_boundary.get("trading_session_created") is True
          and permission_boundary.get("readonly_expected_account_enumerated") is True
          and permission_boundary.get("trading_expected_account_enumerated") is True
          and permission_boundary.get("readonly_expected_account_occurrence_count") == 1
          and permission_boundary.get("trading_expected_account_occurrence_count") == 1
          and permission_boundary.get("readonly_token_readonly_observed") is True
          and permission_boundary.get("trading_token_readonly_false_observed") is True
          and permission_boundary.get("token_permission_boundary_validated") is True
          and permission_boundary.get("readonly_token_used") is True
          and permission_boundary.get("trading_token_used") is True
          and permission_boundary.get("finam_authentication_performed") is True
          and permission_boundary.get("order_count") == 0
          and permission_boundary.get("order_endpoint_called") is False
          and permission_boundary.get("order_path_validation_performed") is False
          and permission_boundary.get("live_trading_authorized") is False
          and permission_boundary.get("real_order_transmission_authorized") is False
          and permission_boundary.get("stage8_10_status") == "IN_PROGRESS"
          and permission_boundary.get("stage8_10_5_status") == "NOT_STARTED"
          and permission_boundary.get("stage8_10_6_through_8_status") == "NOT_STARTED"
          and permission_boundary.get("stage8_11_status") == "NOT_STARTED_NOT_AUTHORIZED"
          and permission_boundary.get("stage8_12_status") == "NOT_STARTED_NOT_AUTHORIZED", "STAGE_8_10_4_MACHINE_AUTHORITY_EXACT")
    permission_calls = {node.func.attr for node in ast.walk(ast.parse(permission_source)) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
    forbidden_permission_calls = {"orders","order","place_order","cancel_order","submit_order","account","assets","assets_all_active","asset","asset_params","schedule","bars"}
    check(not permission_calls.intersection(forbidden_permission_calls) and {"create_session","session_details"}.issubset(permission_calls), "STAGE_8_10_4_SESSION_ONLY_NO_ORDER_CAPABILITY")
    check("trading_permission_boundary" not in launcher + installer and all(term not in permission_wrapper.lower() for term in ("run-readonly","install-task","scheduledtask","runner","broker","/orders","place_order","cancel_order","submit_order")), "STAGE_8_10_4_NOT_RUNTIME_OR_TASK_WIRED")
    check(all(STAGE_8_10_5_STATUS in doc and "Stage 8.10.5 is **COMPLETE**" in doc for doc in stage8_9_docs), "STAGE_8_10_5_CODE_READY_SYNCHRONIZED")
    expected_dry_gate = {
        "status": STAGE_8_10_5_STATUS,
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
    check(dry_gate == expected_dry_gate, "STAGE_8_10_5_MACHINE_AUTHORITY_EXACT")
    dry_source=text("TradingSystemLab/stage8_robot/order_path_dry_validation.py").lower(); dry_wrapper=text("TradingSystemLab/stage8_robot/deploy/windows/validate-order-path-dry.ps1").lower()
    forbidden_dry = ("urlopen(","requests.","httpx.","socket.","invoke-webrequest",
                     "invoke-restmethod","curl ","wget ","credential-store",
                     "get-readonlycredential","get-tradingcredential","run-readonly",
                     "install-task","readonly_supervisor","tradingsystemlab\\runtime",
                     "tradingsystemlab/runtime","robotrunner",".sqlite",".sqlite3","-wal","-shm")
    check("transport=transport" in dry_source and "repository_output_forbidden" in dry_source
          and not any(term in dry_source+dry_wrapper for term in forbidden_dry)
          and "order_path_dry_validation" not in launcher+installer,
          "STAGE_8_10_5_OFFLINE_NOT_RUNTIME_WIRED")
    expected_safety={"status":STAGE_8_10_6_STATUS,"accepted_code_commit":"35ec9007e6302d66e35e1a42a34fc2e77be8a467","external_evidence_sha256":"CF34E54212B3385F154804F440361FE5E213B0AFA63D8DD8AE56E1EBB49D6B30","physical_result":"STAGE_8_10_6_PHYSICAL_SAFETY_GATE_VALIDATION_PASS","physical_validation_performed":True,"production_kill_switch_initialized":True,"production_kill_switch_halted_observed":True,"production_kill_switch_final_state":"HALTED","production_kill_switch_valid":True,"synthetic_safety_matrix_validated":True,"synthetic_case_count":25,"synthetic_open_case_count":1,"synthetic_blocked_case_count":24,"synthetic_matrix_validation":"PASS","emergency_halt_validated":True,"missing_switch_fail_closed":True,"malformed_switch_fail_closed":True,"execution_authorization_required":True,"heartbeat_health_gate_validated":True,"reconciliation_gate_validated":True,"unresolved_order_gate_validated":True,"heartbeat_freshness_gate_validated":True,"api_contact_freshness_gate_validated":True,"account_hash_shape_gate_validated":True,"execution_authorized":False,"real_account_id_used":False,"readonly_token_used_for_stage8_10_6":False,"trading_token_used_for_stage8_10_6":False,"finam_authentication_performed_for_stage8_10_6":False,"external_network_calls":0,"real_order_endpoint_called":False,"real_order_count":0,"live_trading_authorized":False,"real_order_transmission_authorized":False,"stage8_10_status":"IN_PROGRESS","stage8_10_7_status":"NOT_STARTED","stage8_10_8_status":"NOT_STARTED","stage8_11_status":"NOT_STARTED_NOT_AUTHORIZED","stage8_12_status":"NOT_STARTED_NOT_AUTHORIZED"}
    check(safety_gate == expected_safety, "STAGE_8_10_6_MACHINE_AUTHORITY_EXACT")
    safety=text("TradingSystemLab/stage8_robot/trading_safety_gate.py"); validation=text("TradingSystemLab/stage8_robot/safety_gate_validation.py"); safety_wrapper=text("TradingSystemLab/stage8_robot/deploy/windows/validate-trading-safety-gates.ps1")
    offline_safe,wrapper_halt_only,physical_report_contract=_stage8_10_6_semantics(safety,validation,safety_wrapper)
    check(offline_safe, "STAGE_8_10_6_OFFLINE_FAIL_CLOSED")
    check(wrapper_halt_only, "STAGE_8_10_6_WRAPPER_HALT_ONLY")
    check(physical_report_contract, "STAGE_8_10_6_PHYSICAL_REPORT_CONTRACT")
    check(all(STAGE_8_10_6_STATUS in doc and "Stage 8.10.6 is **COMPLETE**" in doc for doc in stage8_9_docs), "STAGE_8_10_6_COMPLETE_SYNCHRONIZED")
    expected_token={"status":STAGE_8_10_7_STATUS,"accepted_code_commit":"df4bba6be4f98ba4659e13a01c90bec8e4162ff3","external_evidence_sha256":"A2A6B330A5DC1F15D67A84860223D80786022B634BB8B6CD73E01C815EE7D1B6","physical_result":"STAGE_8_10_7_PHYSICAL_INTEL_TRADING_TOKEN_ACCEPTANCE_PASS","physical_validation_performed":True,"trading_dpapi_current_user_validated":True,"local_readonly_trading_account_binding_validated":True,"production_kill_switch_pre_halted_observed":True,"trading_session_created":True,"expected_account_enumerated":True,"expected_account_occurrence_count":1,"trading_token_readonly_false_observed":True,"trading_token_write_boundary_confirmed":True,"remote_call_scope":"SESSION_CREATE_AND_DETAILS_ONLY","production_kill_switch_post_halted_observed":True,"trading_token_used":True,"readonly_token_used_for_remote_auth":False,"finam_authentication_performed":True,"order_endpoint_called":False,"order_count":0,"execution_authorized":False,"live_trading_authorized":False,"real_order_transmission_authorized":False,"stage8_10_status":"IN_PROGRESS","stage8_10_8_status":"NOT_STARTED","stage8_11_status":"NOT_STARTED_NOT_AUTHORIZED","stage8_12_status":"NOT_STARTED_NOT_AUTHORIZED"}
    check(token_acceptance == expected_token, "STAGE_8_10_7_MACHINE_AUTHORITY_EXACT")
    diagnostic=text("TradingSystemLab/stage8_robot/trading_token_intel_acceptance.py")
    token_wrapper=text("TradingSystemLab/stage8_robot/deploy/windows/validate-trading-token-intel-acceptance.ps1")
    session_only,kill_switch,wrapper_boundary,runtime_wiring,report_contract,cleanup=_stage8_10_7_semantics(diagnostic,token_wrapper)
    check(session_only,"STAGE_8_10_7_SESSION_ONLY_NO_ORDER_CAPABILITY")
    check(kill_switch,"STAGE_8_10_7_KILL_SWITCH_HALTED_REQUIRED")
    check(wrapper_boundary,"STAGE_8_10_7_WRAPPER_CREDENTIAL_BOUNDARY")
    check(runtime_wiring,"STAGE_8_10_7_WRAPPER_NOT_RUNTIME_WIRED")
    check(report_contract,"STAGE_8_10_7_REPORT_CONTRACT")
    check(cleanup,"STAGE_8_10_7_CLEANUP_CONTRACT")
    check(all(STAGE_8_10_7_STATUS in doc and "Stage 8.10.7 is **COMPLETE**" in doc and "Stage 8.10.8 is **COMPLETE**" in doc for doc in stage8_9_docs),"STAGE_8_10_7_COMPLETE_SYNCHRONIZED")
    expected_closeout={"status":STAGE_8_10_COMPLETE_STATUS,"stage8_10_complete":True,"completed_gate_count":7,
        "stage8_10_1_status":STAGE_8_10_1_STATUS,"stage8_10_2_status":STAGE_8_10_2_STATUS,
        "stage8_10_3_status":STAGE_8_10_3_STATUS,"stage8_10_4_status":STAGE_8_10_4_STATUS,
        "stage8_10_5_status":STAGE_8_10_5_STATUS,"stage8_10_6_status":STAGE_8_10_6_STATUS,
        "stage8_10_7_status":STAGE_8_10_7_STATUS,"production_kill_switch_final_state":"HALTED",
        "execution_authorized":False,"order_endpoint_called":False,"order_count":0,
        "live_trading_authorized":False,"real_order_transmission_authorized":False,
        "stage8_11_status":"NOT_STARTED_NOT_AUTHORIZED","stage8_12_status":"NOT_STARTED_NOT_AUTHORIZED"}
    check(lifecycle_closeout == expected_closeout, "STAGE_8_10_8_MACHINE_AUTHORITY_EXACT")
    check(all(STAGE_8_10_COMPLETE_STATUS in doc for doc in stage8_9_docs),
          "STAGE_8_10_CLOSEOUT_STATUS_SYNCHRONIZED")
    check(all("Stage 8.11.1 — **COMPLETE / PASS**" in doc
              and "Stage 8.11.2 — **COMPLETE / PASS**" in doc
              and "prior explicit authorization **CONSUMED**" in doc for doc in stage8_9_docs),
          "STAGE_8_11_LIFECYCLE_CLOSEOUT_SYNCHRONIZED")
    physical_entry=text("TradingSystemLab/stage8_robot/stage8_11_physical_acceptance.py")
    physical_wrapper=text("TradingSystemLab/stage8_robot/deploy/windows/run-stage8-11-physical-acceptance.ps1")
    attempt3_entry=text("TradingSystemLab/stage8_robot/stage8_11_physical_acceptance_attempt3.py")
    attempt3_wrapper=text("TradingSystemLab/stage8_robot/deploy/windows/run-stage8-11-physical-acceptance-attempt3.ps1")
    recovery=text("TradingSystemLab/stage8_robot/stage8_11_failed_attempt_recovery.py")
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
          and 'os.replace(' not in attempt3_entry and 'os.link(temporary, destination)' in attempt3_entry,
          "STAGE8_11_ATTEMPT2_DISTINCT_FIXED_INTENT_AND_WRAPPER_BINDING")
    check('FAILED_PHYSICAL_EVIDENCE_SHA256 = "9FEFC5469F2C97F1EB36A5B5C99D323FA37BB948CF53C8A8745A27A06AB3B324"' in recovery
          and 'HISTORICAL_INTENT_KEY = "stage8.11:CNYRUBF:entry"' in recovery
          and all("0954B5C3D62444BA9AE59519386B0FC454D85C987BE1BAC04B82CA6C671B15A0" in doc
                  and "OPERATOR_INTERVENTION_REQUIRED" in doc
                  and "stage8.11.attempt3" in doc
                  and "has not been physically executed" in doc for doc in stage8_9_docs),
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
    normal_owners="\n".join(text(path) for path in (
          "TradingSystemLab/stage8_robot/runner.py",
          "TradingSystemLab/stage8_robot/readonly_supervisor.py",
          "TradingSystemLab/stage8_robot/deploy/windows/install-task.ps1",
          "TradingSystemLab/stage8_robot/deploy/windows/run-readonly.ps1"))
    check("run-stage8-11-physical-acceptance.ps1" not in normal_owners,
          "STAGE_8_11_PHYSICAL_MANUAL_ONLY_AIRGAP")
    intel_precheck=text("TradingSystemLab/stage8_robot/stage8_11_intel_acceptance.py")
    intel_wrapper=text("TradingSystemLab/stage8_robot/deploy/windows/run-stage8-11-intel-precheck.ps1")
    intel_ast=ast.parse(intel_precheck)
    intel_order_calls={node.func.attr for node in ast.walk(intel_ast)
                       if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)}
    check('MODE = "STAGE8_11_PRECHECK_ONLY"' in intel_precheck
          and not intel_order_calls.intersection({"place_order","cancel_order","modify_order","submit_order"})
          and '"execution_authorization_observed":False' in intel_precheck
          and '"real_order_count":0' in intel_precheck,
          "STAGE_8_11_INTEL_PRECHECK_ONLY_ZERO_ORDER")
    check("Get-TradingCredential" in intel_wrapper and "$AcceptedCommit" in intel_wrapper
          and "Get-ScheduledTask" in intel_wrapper and "backup_state" in intel_wrapper
          and "--execute" not in intel_wrapper,
          "STAGE_8_11_INTEL_OPERATOR_WRAPPER_ISOLATED")
    check("evaluate_new_entry_gate" in intel_precheck and "execution_authorized=False" in intel_precheck
          and 'EXPECTED_GATE_REASONS = ["KILL_SWITCH_HALTED", "EXECUTION_NOT_AUTHORIZED"]' in intel_precheck,
          "STAGE_8_11_INTEL_EXISTING_SAFETY_GATE_EXACT_BLOCKERS")
    state_source=text("TradingSystemLab/stage8_robot/state.py")
    acceptance_source=text("TradingSystemLab/stage8_robot/controlled_real_acceptance.py")
    precheck_tests=text("TradingSystemLab/stage8_robot/tests/test_stage8_11_intel_acceptance.py")
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
    check("canonical_controlled_acceptance_broker" in acceptance_source
          and "stage8_11_acceptance_path(runtime_root)" in acceptance_source,
          "STAGE_8_11_PRECHECK_AND_ACCEPTANCE_SHARED_LEDGER")
    stage811_provenance=provenance.get("stage8_11",{})
    physical=stage811_provenance.get("physical_precheck",{})
    independent=stage811_provenance.get("independent_evidence_audit",{})
    check(all((
          stage811_provenance.get("stage8_11_0_status") == "COMPLETE",
          stage811_provenance.get("stage8_11_1_status") == "COMPLETE_PASS",
          stage811_provenance.get("stage8_11_2_status") == "COMPLETE_PASS",
          stage811_provenance.get("stage8_11_3_status") == "PRIOR_AUTHORIZATION_CONSUMED",
          stage811_provenance.get("current_gate") == "STAGE_8_11_CLOSEOUT_COMPLETE_NEW_EXPLICIT_AUTHORIZATION_REQUIRED_FOR_RETRY",
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
          stage811_provenance.get("execution_authorized") is False,
          stage811_provenance.get("real_order_count") == 0,
          stage811_provenance.get("production_kill_switch_final_state") == "HALTED",
          stage811_provenance.get("stage8_12_status") == "NOT_STARTED_NOT_AUTHORIZED",
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
    check(all("Stage 8.12 — **NOT STARTED / NOT AUTHORIZED**" in doc for doc in stage8_9_docs),
          "STAGE_8_12_NOT_STARTED_NOT_AUTHORIZED")
    forbidden_claims = (
        r"(?:broker acceptance (?:is |was )?validated|order (?:was )?accepted|FINAM server accepted an order)",
        r"(?<!not )real-order (?:transmission|capability) is authorized",
    )
    check(not any(re.search(pattern, stage8_9_joined_docs, re.I) for pattern in forbidden_claims),
          "STAGE_8_10_FALSE_AUTHORIZATION_OR_TOKEN_CLAIM")
    check("LIVE_TRADING_NOT_AUTHORIZED" in stage8_9_joined_docs
          and "REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED" in stage8_9_joined_docs,
          "LIVE_AND_REAL_ORDER_TRANSMISSION_UNAUTHORIZED")
    false_full_claim = re.compile(r"(?:FULL/N4|FULL N4|FULL/R15).{0,40}(?:ready|sufficient|validated)", re.I)
    check(not false_full_claim.search(stage8_9_joined_docs), "FULL_N4_FUNDING_READINESS_NOT_CLAIMED")

    controlled = text("TradingSystemLab/stage8_robot/controlled_real_acceptance.py")
    finam = text("TradingSystemLab/stage8_robot/finam_api.py")
    recovery = text("TradingSystemLab/stage8_robot/stage8_11_failed_attempt_recovery.py")
    recovery_wrapper = text("TradingSystemLab/stage8_robot/deploy/windows/run-stage8-11-failed-intent-recovery.ps1")
    check("stage8_11_exclusive_lock(runtime_root)" in physical_entry
          and "stage8_11_exclusive_lock(root)" in recovery,
          "STAGE8_11_SHARED_EXCLUSIVE_LOCK_AUTHORITY")
    check("stage8_11_failed_attempt_recovery" in physical_wrapper,
          "STAGE8_11_PHYSICAL_WRAPPER_RECOVERY_CONFLICT")
    provenance = json.loads(text("TradingSystemLab/stage8_robot/authority_provenance.json"))
    check("class FinamOrderRejected" in finam and "order_post and exc.code==400" in finam
          and "exc.code>=500 and order_post" in finam, "STAGE8_11_REJECTION_TAXONOMY")
    check('transition_intent(request.idempotency_key, "REJECTED")' in controlled
          and "FinamUncertainSubmission" in controlled, "STAGE8_11_REJECTED_VS_UNCERTAIN")
    check("self.api.schedule(finam_symbol)" in controlled and "STAGE8_11_TRADING_SESSION_NOT_OPEN" in controlled,
          "STAGE8_11_LIVE_EXACT_SYMBOL_SESSION_GATE")
    check("entry_observed = time_source()" in controlled and "flatten_observed = time_source()" in controlled
          and "FLATTEN_TRADING_SESSION_NOT_OPEN" in controlled
          and "minimum_remaining=ENTRY_MINIMUM_REMAINING_SESSION" in controlled,
          "STAGE8_11_FRESH_PER_POST_CLOCK_AND_ENTRY_MARGIN")
    recovery_calls = {node.func.attr for node in ast.walk(ast.parse(recovery))
                      if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
    check(not recovery_calls.intersection({"place_order","cancel_order","submit_order","modify_order"})
          and "backup, manifest = create_stage8_11_acceptance_backup" in recovery, "STAGE8_11_RECOVERY_NO_ORDER_CAPABILITY")
    check("recovery_status\": \"PREPARED" in recovery and "BEGIN IMMEDIATE" in recovery
          and "during_evidence_finalization" in recovery,
          "STAGE8_11_RECOVERY_DURABLE_COMMIT_PROTOCOL")
    check("Get-ReadonlyCredential" in recovery_wrapper and "Get-TradingCredential" not in recovery_wrapper
          and "stage8_11_failed_attempt_recovery" in recovery_wrapper,
          "STAGE8_11_RUNNABLE_READONLY_RECOVERY_OPERATOR_BOUNDARY")
    recovery_keys=[node.value for node in ast.walk(ast.parse(recovery))
                   if isinstance(node,ast.Constant) and isinstance(node.value,str)]
    check(recovery_keys.count("recovery_code_commit") >= 3
          and "load_kill_switch" in recovery and 'switch.get("state") != "HALTED"' in recovery,
          "STAGE8_11_RECOVERY_CODE_AND_HALTED_EVIDENCE_BINDING")
    check(all(token in recovery_wrapper for token in (
              "ValidatePattern('^[0-9a-f]{40}$')", "rev-parse HEAD", "status --porcelain",
              "Get-FileHash", "STAGE8_11_KILL_SWITCH_NOT_HALTED",
              "stage8_11_physical_acceptance|stage8_11_failed_attempt_recovery",
              "Global\\TradingSystemLab-Stage8-11-Failed-Intent-Recovery", "ReleaseMutex"))
          and recovery_wrapper.index("rev-parse HEAD") < recovery_wrapper.index("Get-ReadonlyCredential")
          and recovery_wrapper.index("Get-FileHash") < recovery_wrapper.index("Get-ReadonlyCredential"),
          "STAGE8_11_RECOVERY_PREAUTHORITY_EXCLUSIVITY_BOUNDARY")
    check("if not _account_is_clean(final):" in controlled and "finally:\n        emergency_halt(runtime_root" in controlled,
          "STAGE8_11_CLEAN_PROOF_AND_HALT")
    record = provenance.get("stage8_11_failed_physical_attempt_correction", {})
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
          and record.get("physical_evidence_sha256") == "9FEFC5469F2C97F1EB36A5B5C99D323FA37BB948CF53C8A8745A27A06AB3B324"
          and record.get("retry_occurred") is False, "STAGE8_11_HISTORICAL_EVIDENCE_BINDING")
    result = {
        "status": "PASS" if not errors else "FAIL", "checks": checks, "errors": errors,
        "production_specification_id": spec.get("production_specification_id"), "production_identity": spec.get("identity"),
        "stage7_audit_status": stage7_result.get("status"), "stage7_audit_checks": stage7_result.get("checks"),
        "stage8_audit_status": stage8_result.get("status"), "stage8_audit_checks": stage8_result.get("checks"),
        "stage8_8_5_status": STAGE_8_8_5_STATUS, "stage8_8_5_external_evidence_sha256": STAGE_8_8_5_EVIDENCE,
        "stage8_8_6_status": STAGE_8_8_6_STATUS, "stage8_8_6_external_evidence_sha256": STAGE_8_8_6_EVIDENCE,
        "stage8_8_7_accepted_code_commit": STAGE_8_8_7_CODE,
        "stage8_8_7_external_evidence_sha256": STAGE_8_8_7_EVIDENCE,
        "protected_implementation_status": "PASS" if not bad_hashes else "FAIL",
        "stage8_11_0_status": "COMPLETE",
        "stage8_11_1_status": "COMPLETE_PASS",
        "stage8_11_2_status": "COMPLETE_PASS",
        "stage8_11_3_status": "PRIOR_AUTHORIZATION_CONSUMED",
        "stage8_11_current_gate": "STAGE_8_11_CLOSEOUT_COMPLETE_NEW_EXPLICIT_AUTHORIZATION_REQUIRED_FOR_RETRY",
        "stage8_11_latest_physical_precheck_result": "STAGE8_11_PRECHECK_ONLY_PASS",
        "stage8_11_physical_precheck_real_order_count": 0,
        "runtime_artifacts_tracked": runtime_artifacts, "live_trading_authorized": False,
        "real_order_transmission_authorized": False, "stage8_8_7_status": COMPLETE_STATUS,
        "intel_final_acceptance_performed": True, "stage8_9_started": True,
        "stage8_9_status": stage8_9_status, "stage8_9_reason": STAGE_8_9_REASON,
        "stage8_9_accepted_code_commit": STAGE_8_9_CODE,
        "stage8_9_diagnostic_report_sha256": STAGE_8_9_REPORT,
        "stage8_9_physical_summary_sha256": STAGE_8_9_SUMMARY,
        "stage8_9_8_status": STAGE_8_9_8_STATUS,
        "stage8_9_8_portfolio_variant_evidence_sha256": STAGE_8_9_8_VARIANT,
        "stage8_9_8_financial_shape_evidence_sha256": STAGE_8_9_8_SHAPE,
        "stage8_9_9_status": "PHYSICAL_REVALIDATION_COMPLETE",
        "stage8_9_10_status": "COMPLETE",
        "stage8_9_sizing_case_count": 8,
        "stage8_9_positive_capacity_case_count": 4,
        "stage8_9_zero_capacity_case_count": 4,
        "stage8_9_positive_batch_reservation_count": 1,
        "stage8_10_status": STAGE_8_10_COMPLETE_STATUS, "stage8_10_1_status": STAGE_8_10_1_STATUS,
        "stage8_10_2_status": STAGE_8_10_2_STATUS,
        "stage8_10_2_accepted_code_commit": STAGE_8_10_2_CODE,
        "stage8_10_2_external_evidence_sha256": STAGE_8_10_2_EVIDENCE,
        "stage8_10_2_physical_result": STAGE_8_10_2_RESULT,
        "physical_provisioning_performed": True, "trading_token_provisioned": True,
        "trading_token_used": True, "finam_authentication_performed": True, "order_count": 0,
        "order_endpoint_called": False,
        "stage8_10_3_status": STAGE_8_10_3_STATUS,
        "stage8_10_3_accepted_code_commit": "428d285336380726a3ce00487e2c85eb755e2dd9",
        "stage8_10_3_external_evidence_sha256": "0DA102E61AB06FFA6A508CC64203FEA3F56BBA3016891A887688A4E300E11BB6",
        "stage8_10_3_physical_result": "STAGE_8_10_3_IDENTITY_ACCOUNT_BINDING_PASS",
        "physical_validation_performed": True,
        "local_readonly_trading_account_binding_validated": True,
        "trading_session_created": True,
        "expected_account_enumerated": True,
        "expected_account_occurrence_count": 1,
        "enumerated_account_count": 1,
        "stage8_10_4_status": STAGE_8_10_4_STATUS,
        "stage8_10_4_accepted_code_commit": "44858bacc2902591e11adc85cfa5f79e2b62dd5b",
        "stage8_10_4_external_evidence_sha256": "E4AEDC153F89E000EC034E5F33A6EF7BECB5DA29BA253BC0B28B2AC3D0C26C5D",
        "stage8_10_4_physical_result": "STAGE_8_10_4_TOKEN_PERMISSION_BOUNDARY_PASS",
        "stage8_10_4_physical_validation_performed": True,
        "readonly_token_readonly_observed": True,
        "trading_token_readonly_false_observed": True,
        "token_permission_boundary_validated": True,
        "order_path_validation_performed": False,
        "stage8_10_5_status": STAGE_8_10_5_STATUS,
        "stage8_10_5_accepted_code_commit": "ba284e95954c8473c0e77a95172117bc5cefaf65",
        "stage8_10_5_external_evidence_sha256": "D878309E22FA49BFFA9EE9B37200C3FE207BF77DB5C29D6DE97010F1FFCE904A",
        "stage8_10_5_physical_result": "STAGE_8_10_5_OFFLINE_ORDER_PATH_DRY_VALIDATION_PASS",
        "stage8_10_5_physical_validation_performed": True,
        "offline_dry_validation_performed": True,
        "order_path_dry_validation_validated": True,
        "stage8_10_5_external_network_calls": 0,
        "real_order_endpoint_called": False, "real_order_count": 0,
        "stage8_10_6_status": STAGE_8_10_6_STATUS,
        "stage8_10_6_accepted_code_commit": safety_gate["accepted_code_commit"],
        "stage8_10_6_external_evidence_sha256": safety_gate["external_evidence_sha256"],
        "stage8_10_6_physical_result": safety_gate["physical_result"],
        "stage8_10_6_physical_validation_performed": True,
        "production_kill_switch_initialized": True,
        "production_kill_switch_halted_observed": True,
        "production_kill_switch_final_state": "HALTED",
        "production_kill_switch_valid": True,
        "synthetic_safety_matrix_validated": True,
        "synthetic_case_count": 25,
        "synthetic_open_case_count": 1,
        "synthetic_blocked_case_count": 24,
        "emergency_halt_validated": True,
        "execution_authorized": False,
        "stage8_10_6_external_network_calls": 0,
        "stage8_10_7_status": STAGE_8_10_7_STATUS,
        "stage8_10_7_accepted_code_commit": token_acceptance["accepted_code_commit"],
        "stage8_10_7_external_evidence_sha256": token_acceptance["external_evidence_sha256"],
        "stage8_10_7_physical_result": token_acceptance["physical_result"],
        "stage8_10_7_physical_validation_performed": True,
        "stage8_10_7_trading_dpapi_current_user_validated": True,
        "stage8_10_7_local_readonly_trading_account_binding_validated": True,
        "stage8_10_7_production_kill_switch_pre_halted_observed": True,
        "stage8_10_7_trading_session_created": True,
        "stage8_10_7_expected_account_enumerated": True,
        "stage8_10_7_expected_account_occurrence_count": 1,
        "stage8_10_7_trading_token_readonly_false_observed": True,
        "stage8_10_7_trading_token_write_boundary_confirmed": True,
        "stage8_10_7_remote_call_scope": "SESSION_CREATE_AND_DETAILS_ONLY",
        "stage8_10_7_production_kill_switch_post_halted_observed": True,
        "stage8_10_7_trading_token_used": True,
        "stage8_10_7_readonly_token_used_for_remote_auth": False,
        "stage8_10_7_finam_authentication_performed": True,
        "stage8_10_7_order_endpoint_called": False,
        "stage8_10_7_order_count": 0,
        "stage8_10_8_status": lifecycle_closeout.get("status"),
        "stage8_10_complete": True,
        "stage8_10_completed_gate_count": 7,
        "stage8_10_production_kill_switch_final_state": "HALTED",
        "stage8_10_execution_authorized": False,
        "stage8_10_order_endpoint_called": False,
        "stage8_10_order_count": 0,
        "stage8_10_live_trading_authorized": False,
        "stage8_10_real_order_transmission_authorized": False,
        "stage8_11_status": "STAGE_8_11_CONTROLLED_REAL_EXECUTION_ACCEPTANCE_NOT_YET_PASSED",
        "stage8_12_status": "NOT_STARTED_NOT_AUTHORIZED",
        "stage8_9_complete": True, "stage8_9_physical_validation_performed": True,
    }
    if write_result:
        (root / "TradingSystemLab/stage8_robot/final_operational_audit_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    output = audit(write_result=not args.check_only)
    print(json.dumps(output, sort_keys=True))
    raise SystemExit(output["status"] != "PASS")
