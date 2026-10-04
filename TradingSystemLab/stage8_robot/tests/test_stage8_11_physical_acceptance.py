import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

from TradingSystemLab.stage8_robot.stage8_11_physical_acceptance import (
    AUTHORIZATION_VALUE, DIRECTION, FINAM_SYMBOL, INSTRUMENT, QUANTITY,
    PRECHECK_EVIDENCE_SHA256, PhysicalAcceptanceBlocked, _physical_evidence,
    execute_boundary, verify_authorization, verify_repository_authority,
)
from TradingSystemLab.stage8_robot.trading_safety_gate import write_kill_switch
from TradingSystemLab.stage8_robot.trading_safety_gate import heartbeat_path, load_kill_switch
from TradingSystemLab.stage8_robot.specification import ACTIVE_IDENTITY, PRODUCTION_SPECIFICATION_ID
import TradingSystemLab.stage8_robot.stage8_11_physical_acceptance as physical
from TradingSystemLab.stage8_robot.tests.test_controlled_real_acceptance import HASH, NOW, authority


@pytest.mark.parametrize("value", ["", "LIVE_TRADING_ENABLED", AUTHORIZATION_VALUE.lower(), "wrong"])
def test_missing_or_wrong_explicit_authorization_blocks_before_post(value):
    with pytest.raises(PhysicalAcceptanceBlocked, match="EXPLICIT_AUTHORIZATION_REQUIRED"):
        verify_authorization(value)


def test_exact_authorization_is_the_only_accepted_value():
    verify_authorization(AUTHORIZATION_VALUE)


def _completed(returncode=0, stdout=""):
    return subprocess.CompletedProcess([], returncode, stdout=stdout, stderr="")


def test_wrong_accepted_commit_blocks_before_post(tmp_path):
    calls = iter([_completed(stdout="b" * 40 + "\n"), _completed(), _completed()])
    with pytest.raises(PhysicalAcceptanceBlocked, match="ACCEPTED_COMMIT_MISMATCH"):
        verify_repository_authority("a" * 40, repository=tmp_path, run=lambda *a, **k: next(calls))


@pytest.mark.parametrize("unstaged,staged", [(1, 0), (0, 1), (1, 1)])
def test_dirty_or_staged_repository_blocks_before_post(tmp_path, unstaged, staged):
    calls = iter([_completed(stdout="a" * 40 + "\n"), _completed(unstaged), _completed(staged)])
    with pytest.raises(PhysicalAcceptanceBlocked, match="WORKTREE_NOT_CLEAN"):
        verify_repository_authority("a" * 40, repository=tmp_path, run=lambda *a, **k: next(calls))


def test_fixed_acceptance_identity_has_no_operator_choice():
    assert (INSTRUMENT, FINAM_SYMBOL, DIRECTION, QUANTITY) == ("CNYRUBF", "CNYRUBF@RTSX", "LONG", 1)


def test_wrapper_is_manual_only_and_runtime_airgapped():
    root = Path(__file__).resolve().parents[1]
    wrapper_name = "run-stage8-11-physical-acceptance.ps1"
    wrapper = (root / "deploy/windows" / wrapper_name).read_text(encoding="utf-8")
    assert AUTHORIZATION_VALUE in wrapper
    assert "readonly_supervisor --runtime-root $runtime --once" in wrapper
    assert wrapper.index("FINAM_API_SECRET") < wrapper.index("STAGE8_11_TRADING_SECRET")
    assert "CNYRUBF" in wrapper and "LONG" in wrapper and "quantity" in wrapper.lower()
    for relative in ("runner.py", "readonly_supervisor.py", "deploy/windows/install-task.ps1",
                     "deploy/windows/run-readonly.ps1"):
        assert wrapper_name not in (root / relative).read_text(encoding="utf-8")


def test_module_uses_canonical_lifecycle_ledger_backup_and_bounded_arm():
    source = Path(__file__).resolve().parents[1].joinpath("stage8_11_physical_acceptance.py").read_text()
    assert "run_controlled_lifecycle(" in source
    assert "initialize_stage8_11_acceptance_ledger(" in source
    assert "create_stage8_11_acceptance_backup(" in source
    # One executable occurrence plus the explanatory safety comment.
    assert source.count('execution_authorized=True') == 2
    assert source.count('write_kill_switch(runtime_root, "ARMED"') == 1
    assert "try: emergency_halt(root)" in source
    assert "place_order(" not in source


def test_operator_intervention_physical_evidence_keeps_unknown_facts_null():
    result={"classification":"OPERATOR_INTERVENTION_REQUIRED","phases":["HALTED"],
            "order_endpoint_call_count":1}
    got=_physical_evidence(accepted_commit="a"*40,account_hash=HASH,result=result,
        authority=authority(),external_sha256=PRECHECK_EVIDENCE_SHA256)
    assert got["final_position_quantity"] is None
    assert got["final_active_order_count"] is None
    assert got["unresolved_intent_count"] is None


class NoPostAPI:
    def __init__(self): self.posts=0
    def place_order(self,*args,**kwargs): self.posts += 1


def test_wrong_precheck_sha_blocks_with_zero_posts(tmp_path):
    runtime=tmp_path/"runtime"; write_kill_switch(runtime,"HALTED",now=NOW)
    api=NoPostAPI()
    with pytest.raises(PhysicalAcceptanceBlocked,match="EXTERNAL_EVIDENCE"):
        execute_boundary(accepted_commit="a"*40,authorization=AUTHORIZATION_VALUE,
            account_id="synthetic-account",api=api,runtime_root=runtime,
            external_evidence_sha256="0"*64,now=NOW)
    assert api.posts == 0


def test_missing_precheck_report_blocks_with_zero_posts(tmp_path):
    runtime=tmp_path/"runtime"; write_kill_switch(runtime,"HALTED",now=NOW)
    api=NoPostAPI()
    with pytest.raises(PhysicalAcceptanceBlocked,match="PRECHECK_EVIDENCE_MISSING"):
        execute_boundary(accepted_commit="a"*40,authorization=AUTHORIZATION_VALUE,
            account_id="synthetic-account",api=api,runtime_root=runtime,
            external_evidence_sha256=PRECHECK_EVIDENCE_SHA256,now=NOW)
    assert api.posts == 0


def test_wrapper_checks_each_w32tm_exit_code_and_has_parent_halt_defense():
    wrapper=Path(__file__).resolve().parents[1].joinpath(
        "deploy/windows/run-stage8-11-physical-acceptance.ps1").read_text()
    status=wrapper.index("w32tm /query /status")
    source=wrapper.index("w32tm /query /source")
    assert status < wrapper.index("$timeStatusExitCode = $LASTEXITCODE") < source
    assert source < wrapper.index("$timeSourceExitCode = $LASTEXITCODE")
    assert "emergency_halt(Path" in wrapper


class EntrypointAPI:
    def __init__(self):
        self.posts = 0; self.client_id = None
    def schedule(self, symbol):
        return {"sessions":[{"type":"CORE_TRADING","interval":{
            "start_time":"2026-10-04T11:00:00Z","end_time":"2026-10-04T12:10:00Z"}}]}
    def place_order(self, account, payload):
        self.posts += 1; self.client_id = payload["client_order_id"]
        return {"order_id":"entry-1"}
    def orders(self, account):
        return {"orders":[{"order_id":"entry-1","status":"FILLED",
            "order":{"client_order_id":self.client_id}}]}
    def order(self, account, order_id):
        return {"order_id":"entry-1","status":"FILLED","order":{"account_id":account,
            "client_order_id":self.client_id,"symbol":FINAM_SYMBOL,"side":"SIDE_BUY",
            "quantity":{"value":"1"}},"accept_at":"2026-10-04T12:00:00Z",
            "initial_quantity":{"value":"1"},"executed_quantity":{"value":"1"},
            "remaining_quantity":{"value":"0"}}
    def account(self, account):
        return {"account_id":account,"positions":[{"symbol":FINAM_SYMBOL,"quantity":{"value":"1"}}]}
    def trades(self, account):
        return {"trades":[{"trade_id":"trade-1","order_id":"entry-1","account_id":account,
            "symbol":FINAM_SYMBOL,"side":"SIDE_BUY","size":{"value":"1"},
            "price":{"value":"1"},"timestamp":"2026-10-04T12:00:01Z"}]}


def test_execute_boundary_propagates_fresh_clock_and_refuses_closed_flatten(tmp_path, monkeypatch):
    runtime=tmp_path/"runtime"; write_kill_switch(runtime,"HALTED",now=NOW)
    heartbeat=heartbeat_path(runtime); heartbeat.parent.mkdir(parents=True,exist_ok=True)
    heartbeat.write_text(json.dumps({"production_id":PRODUCTION_SPECIFICATION_ID,"mode":"REAL_READONLY",
        "health_status":"HEALTHY","reconciliation_status":"PASS","entries_enabled":False,
        "unresolved_order_count":0,"failure_code":None,"consecutive_failures":0,"cycle_count":1,
        "account_hash":HASH,"timestamp":NOW.isoformat(),"last_successful_finam_api_contact":NOW.isoformat()}))
    report=runtime/"diagnostics"/physical.PRECHECK_REPORT_NAME; report.parent.mkdir(parents=True,exist_ok=True)
    report.write_bytes(b"synthetic precheck")
    digest=hashlib.sha256(report.read_bytes()).hexdigest().upper()
    monkeypatch.setattr(physical,"PRECHECK_EVIDENCE_SHA256",digest)
    monkeypatch.setattr(physical,"stage8_10_authority_complete",lambda:True)
    funding=lambda *args,**kwargs:{"funding_classification":physical.READY,"account_clean":True,
        "account_identity_sha256":HASH,"n4_binding_valid":True,
        "per_instrument":{"CNYRUBF:LONG":{"r15_quantity":2,"margin_quantity":2}}}
    supplied=[datetime(2026,10,4,11,59,tzinfo=timezone.utc),
              datetime(2026,10,4,11,59,30,tzinfo=timezone.utc),
              datetime(2026,10,4,12,0,tzinfo=timezone.utc),
              datetime(2026,10,4,12,10,tzinfo=timezone.utc)]
    seen=[]
    def clock():
        value=supplied[len(seen)]; seen.append(value); return value
    api=EntrypointAPI()
    result=execute_boundary(accepted_commit="a"*40,authorization=AUTHORIZATION_VALUE,
        account_id="synthetic-account",api=api,runtime_root=runtime,
        external_evidence_sha256=digest,funding_collector=funding,clock=clock)
    assert seen == supplied
    assert result["classification"] == "OPERATOR_INTERVENTION_REQUIRED", result
    assert result["failure_code"] == "FLATTEN_TRADING_SESSION_NOT_OPEN"
    assert result["entry_fill_proven"] and result["one_contract_position_observed"]
    assert result["flatten_fill_proven"] is False
    assert result["final_state"]["position_quantity"] == 1
    assert api.posts == 1
    assert load_kill_switch(runtime)[0]["state"] == "HALTED"
