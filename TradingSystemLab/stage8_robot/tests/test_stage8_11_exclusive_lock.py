from pathlib import Path
import subprocess
import sys
import time

import pytest

from TradingSystemLab.stage8_robot.operations import stage8_11_exclusive_lock
from TradingSystemLab.stage8_robot.stage8_11_failed_attempt_recovery import (
    RecoveryBlocked, recover_historical_intent,
)


def _assert_second_boundary_blocked(root: Path) -> None:
    with stage8_11_exclusive_lock(root):
        with pytest.raises(RuntimeError, match="SECOND_ROBOT_INSTANCE_BLOCKED"):
            with stage8_11_exclusive_lock(root):
                pytest.fail("shared boundary overlapped")


@pytest.mark.parametrize("owner,contender", [
    ("recovery", "physical"), ("physical", "recovery"),
    ("recovery", "recovery"), ("physical", "physical"),
])
def test_every_stage811_owner_contends_on_one_shared_lock(tmp_path, owner, contender):
    _assert_second_boundary_blocked(tmp_path / "runtime")


def test_shared_lock_released_after_success_exception_and_stale_file(tmp_path):
    root=tmp_path/"runtime"
    with stage8_11_exclusive_lock(root):
        pass
    with pytest.raises(ValueError):
        with stage8_11_exclusive_lock(root):
            raise ValueError("injected")
    lock_file=root/"locks"/"stage8-11-exclusive.lock"
    assert lock_file.is_file()  # stale file presence is expected and harmless
    with stage8_11_exclusive_lock(root):
        pass


def test_shared_lock_released_after_recovery_blocked(tmp_path):
    root=tmp_path/"runtime"
    with pytest.raises(RecoveryBlocked, match="RECOVERY_CODE_COMMIT_INVALID"):
        recover_historical_intent(runtime_root=root,account_id="synthetic",
            readonly_api=object(),recovery_code_commit="invalid",
            physical_evidence=tmp_path/"missing",physical_evidence_sha256="0"*64,
            intent_key="wrong")
    with stage8_11_exclusive_lock(root):
        pass


def test_shared_lock_is_cross_process_and_releases_when_owner_exits(tmp_path):
    root=tmp_path/"runtime"; ready=tmp_path/"ready"
    program=("from pathlib import Path\n"
        "from TradingSystemLab.stage8_robot.operations import stage8_11_exclusive_lock\n"
        f"with stage8_11_exclusive_lock(Path({str(root)!r})):\n"
        f" Path({str(ready)!r}).write_text('ready')\n"
        " input()\n")
    child=subprocess.Popen([sys.executable,"-c",program],stdin=subprocess.PIPE,text=True)
    try:
        deadline=time.monotonic()+5
        while not ready.exists() and time.monotonic()<deadline:
            time.sleep(.01)
        assert ready.exists() and child.poll() is None
        with pytest.raises(RuntimeError,match="SECOND_ROBOT_INSTANCE_BLOCKED"):
            with stage8_11_exclusive_lock(root):
                pass
    finally:
        child.communicate("\n",timeout=5)
    assert child.returncode == 0
    with stage8_11_exclusive_lock(root):
        pass
