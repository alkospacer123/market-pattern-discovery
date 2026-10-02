"""Stage 8.8.7 deterministic repository-only final operational audit.

This module deliberately reads only Git/repository material.  It never creates a
FINAM client, reads credentials, or opens the operational database.  Physical
Intel acceptance is a separate, subsequent gate.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SPEC_ID = "PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8"
IDENTITY = "TRAIL1__N4_01__FULL__R15"
INTERIM_STATUS = "STAGE_8_8_7_FINAL_OPERATIONAL_AUDIT_CODE_READY_PENDING_INTEL_ACCEPTANCE"
STAGE_8_8_5_STATUS = "STAGE_8_8_5_STALE_DATA_PROTECTION_COMPLETE"
STAGE_8_8_6_STATUS = "STAGE_8_8_6_SQLITE_RECOVERY_INTEL_ACCEPTANCE_COMPLETE"
STAGE_8_8_5_SOURCE = "1c1c2bb5458827f200bc753e7e64db0272b33a8f"
STAGE_8_8_5_EVIDENCE = "C57554AE3AE54018EC1E558108520088C1883718F0406E7B6C6669B4696A9CBC"
STAGE_8_8_6_CODE = "dc2b79e74817e71435eee20103ae617e13067d8e"
STAGE_8_8_6_EVIDENCE = "1A9B62D4BFC0E7384898C9DF9659E54E50E0E202BD44CE19413864AC2ECA14D6"
BACKUP_SHA = "00b5e4ca2b389d55389b6b57ac73b5e557c11b72daab8d6e118311613e0aa3b0"
MANIFEST_SHA = "3d0ef1d7cb11ee592be32550625e8badefc596108f4d0c34eff6c5e12ceba822"
BASELINE_SHA = "13f01f1009768ddce65dce079f70486f2cbc2508cd1ea8ec4787414a78e0d3be"

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
    "TradingSystemLab/stage8_robot/margin.py": "2081aa6154a5ebb44d75a00fdeac2bc12e6baa8f593ae9354ff8b1c0e07aeddc",
    "TradingSystemLab/stage8_robot/deploy/windows/run-readonly.ps1": "c91937716e84d8e746475ad27b89d32b0424cc928aeedc239c7628477d5055e3",
    "TradingSystemLab/stage8_robot/deploy/windows/credential-store.ps1": "ba7e4e14d0638d989674bb9907c070f43c03672a3b767d5eb522ecb2f5ccfa8a",
    "TradingSystemLab/stage8_robot/deploy/windows/initialize-readonly-credentials.ps1": "e8dde65ca96ffbfb6ca6171a5eb71298040fc4d500a31f0b3e65722ac35fd118",
    "TradingSystemLab/stage8_robot/deploy/windows/verify-readonly-credentials.ps1": "ff84620a5bf5c705730428420a053e682715cfc22e9fa1cdc1d476bc2859e0ae",
    "TradingSystemLab/stage8_robot/deploy/windows/install-task.ps1": "18f3b65b401f9ced6c55b49e8a7b6f7b7711c53671c7b445835101bd77cba478",
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

    docs_paths = ["TradingSystemLab/CURRENT_STATE.md", "TradingSystemLab/ROADMAP.md", "TradingSystemLab/stage8_robot/README.md"]
    docs = [text(path) for path in docs_paths]
    joined_docs = "\n".join(docs)
    spec = json.loads(text("TradingSystemLab/results/post_v3_analysis/stage7_production_specification_freeze/production_specification.json"))
    conformance = json.loads(text("TradingSystemLab/stage8_robot/conformance_report.json"))

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

    check(all(STAGE_8_8_5_STATUS in doc for doc in docs), "STAGE_8_8_5_COMPLETE_SYNCHRONIZED")
    check(all(STAGE_8_8_5_SOURCE in doc and STAGE_8_8_5_EVIDENCE in doc for doc in docs), "STAGE_8_8_5_PROVENANCE_SYNCHRONIZED")
    check(all(STAGE_8_8_6_STATUS in doc for doc in docs), "STAGE_8_8_6_COMPLETE_SYNCHRONIZED")
    check(all(STAGE_8_8_6_CODE in doc and STAGE_8_8_6_EVIDENCE in doc for doc in docs), "STAGE_8_8_6_PROVENANCE_SYNCHRONIZED")
    check(all(value in joined_docs for value in (BACKUP_SHA, MANIFEST_SHA, BASELINE_SHA)), "STAGE_8_8_6_RECOVERY_HASHES_RECORDED")

    bad_hashes = [path for path, expected in PROTECTED_SHA256.items() if hashlib.sha256(content(path)).hexdigest() != expected]
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
        raw_capture = any(term in name for term in ("raw_finam", "account_response", "real_market_capture", "stale_h1_evidence"))
        credential = any(term in name for term in ("credential", "secret")) and not lower.endswith((".py", ".ps1", ".md", ".example"))
        return runtime_suffix or external_acceptance or raw_capture or credential

    runtime_artifacts = sorted(path for path in tracked_files if forbidden_artifact(path))
    check(not runtime_artifacts, "RUNTIME_OR_SECRET_ARTIFACT_TRACKED")

    check(all(INTERIM_STATUS in doc for doc in docs), "STAGE_8_8_7_INTERIM_STATUS_SYNCHRONIZED")
    check(all("Stage 8.9 has not started" in doc for doc in docs), "STAGE_8_9_NOT_STARTED")
    check("Stage 8.10" in joined_docs and "Stage 8.11/8.12" in joined_docs and "NOT AUTHORIZED" in joined_docs, "LATER_STAGES_PENDING_NOT_AUTHORIZED")
    check("STAGE_8_8_7_FINAL_OPERATIONAL_AUDIT_COMPLETE" not in joined_docs, "STAGE_8_8_7_NOT_FALSELY_COMPLETE")

    result = {
        "status": "PASS" if not errors else "FAIL", "checks": checks, "errors": errors,
        "production_specification_id": spec.get("production_specification_id"), "production_identity": spec.get("identity"),
        "stage7_audit_status": stage7_result.get("status"), "stage7_audit_checks": stage7_result.get("checks"),
        "stage8_audit_status": stage8_result.get("status"), "stage8_audit_checks": stage8_result.get("checks"),
        "stage8_8_5_status": STAGE_8_8_5_STATUS, "stage8_8_5_external_evidence_sha256": STAGE_8_8_5_EVIDENCE,
        "stage8_8_6_status": STAGE_8_8_6_STATUS, "stage8_8_6_external_evidence_sha256": STAGE_8_8_6_EVIDENCE,
        "protected_implementation_status": "PASS" if not bad_hashes else "FAIL",
        "runtime_artifacts_tracked": runtime_artifacts, "live_trading_authorized": False,
        "real_order_transmission_authorized": False, "stage8_8_7_status": INTERIM_STATUS,
        "intel_final_acceptance_performed": False, "stage8_9_started": False,
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
