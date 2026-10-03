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
STAGE_8_10_2_STATUS = "STAGE_8_10_2_SECURE_PROVISIONING_CODE_READY_PENDING_PHYSICAL_PROVISIONING"
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
    "TradingSystemLab/stage8_robot/readonly_supervisor.py": "1455fee5fe207c617676a0463ce3034247c5534578555cac293807da22bcaab8",
    "TradingSystemLab/stage8_robot/finam_api.py": "3972bdd7d9c016bec79b1cfcf6ff1120d77bab745cd2e102d827dcb830878588",
    "TradingSystemLab/stage8_robot/operations.py": "1a9c24b9eae666112cc215946cd41166e8f1d425c471393832a9d45b9bb0f783",
    "TradingSystemLab/stage8_robot/backup_state.py": "ce055584fba17a3ce7160e7ccf312bc6ac8d69589ca14e8841078999c3757ba4",
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
        runtime_suffix = lower.endswith((".sqlite3", "-wal", "-shm", ".dpapi"))
        external_acceptance = "acceptance" in name and name.endswith(".json") and "tests/" not in lower
        external_stage8_9 = ("stage8_9" in name or "funding_margin_validation" in name) and name.endswith(".json")
        raw_capture = any(term in name for term in ("raw_finam", "account_response", "real_market_capture", "stale_h1_evidence"))
        credential = any(term in name for term in ("credential", "secret")) and not lower.endswith((".py", ".ps1", ".md", ".example"))
        trading_token = any(term in name for term in ("trading_token", "trading-token", "token_1", "token1")) and lower.endswith((".json", ".txt", ".bin", ".blob", ".dpapi", ".env"))
        account_material = any(term in name for term in ("account_id", "account-identifier")) and lower.endswith((".json", ".txt", ".bin", ".blob", ".env"))
        return runtime_suffix or external_acceptance or external_stage8_9 or raw_capture or credential or trading_token or account_material

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
    check(current_readme_status(text("TradingSystemLab/stage8_robot/README.md")) == STAGE_8_10_2_STATUS,
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
          and closeout.get("stage8_9_complete") is True,
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
    check(all("Stage 8.10 is **IN PROGRESS**" in doc for doc in stage8_9_docs)
          and closeout.get("stage8_10_status") == "IN_PROGRESS"
          and not re.search(r"Stage 8\.10 is \*\*COMPLETE\*\*", stage8_9_joined_docs, re.I),
          "STAGE_8_10_IN_PROGRESS_NOT_COMPLETE")
    check(all("Stage 8.10.2 is **CODE READY / PENDING PHYSICAL PROVISIONING**" in doc
              and STAGE_8_10_2_STATUS in doc for doc in stage8_9_docs),
          "STAGE_8_10_2_CODE_READY_SYNCHRONIZED")
    check(provisioning.get("status") == STAGE_8_10_2_STATUS
          and provisioning.get("physical_provisioning_performed") is False
          and provisioning.get("trading_token_provisioned") is False
          and provisioning.get("trading_token_used") is False
          and provisioning.get("finam_authentication_performed") is False
          and provisioning.get("order_count") == 0
          and provisioning.get("stage8_10_3_status") == "NOT_STARTED"
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
    check(all(all(f"Stage 8.10.{number} is **NOT STARTED**" in doc for number in range(3, 9))
              for doc in stage8_9_docs), "STAGE_8_10_3_THROUGH_8_NOT_STARTED")
    check(all("Stage 8.11 is **NOT STARTED / NOT AUTHORIZED**" in doc for doc in stage8_9_docs),
          "STAGE_8_11_NOT_STARTED_NOT_AUTHORIZED")
    check(all("Stage 8.12 is **NOT STARTED / NOT AUTHORIZED**" in doc for doc in stage8_9_docs),
          "STAGE_8_12_NOT_STARTED_NOT_AUTHORIZED")
    forbidden_claims = (
        r"(?<!no )trading(?:-capable)? token (?:has been|was|is) (?:provisioned|stored|authenticated|inspected|used)",
        r"(?<!no )trading-token physical acceptance (?:has occurred|is complete|passed)",
        r"(?<!not )real-order (?:transmission|capability) is authorized",
    )
    check(not any(re.search(pattern, stage8_9_joined_docs, re.I) for pattern in forbidden_claims),
          "STAGE_8_10_FALSE_AUTHORIZATION_OR_TOKEN_CLAIM")
    check("LIVE_TRADING_NOT_AUTHORIZED" in stage8_9_joined_docs
          and "REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED" in stage8_9_joined_docs,
          "LIVE_AND_REAL_ORDER_TRANSMISSION_UNAUTHORIZED")
    false_full_claim = re.compile(r"(?:FULL/N4|FULL N4|FULL/R15).{0,40}(?:ready|sufficient|validated)", re.I)
    check(not false_full_claim.search(stage8_9_joined_docs), "FULL_N4_FUNDING_READINESS_NOT_CLAIMED")

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
        "stage8_10_status": "IN_PROGRESS", "stage8_10_1_status": STAGE_8_10_1_STATUS,
        "stage8_10_2_status": STAGE_8_10_2_STATUS,
        "physical_provisioning_performed": False, "trading_token_provisioned": False,
        "trading_token_used": False, "finam_authentication_performed": False, "order_count": 0,
        "stage8_10_3_through_8_status": "NOT_STARTED",
        "stage8_11_status": "NOT_STARTED_NOT_AUTHORIZED",
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
