import subprocess
from pathlib import Path

import pytest

from TradingSystemLab.stage8_robot.stage8_11_physical_acceptance import (
    AUTHORIZATION_VALUE, DIRECTION, FINAM_SYMBOL, INSTRUMENT, QUANTITY,
    PhysicalAcceptanceBlocked, verify_authorization, verify_repository_authority,
)


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
    assert "finally:\n        emergency_halt(runtime_root" in source
    assert "place_order(" not in source
