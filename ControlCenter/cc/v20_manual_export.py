"""CC-02: bounded manual READONLY refresh, never a trading/control adapter.

Only called after the operator presses Refresh. This invokes the pinned
ControlCenter V20 check-only exporter; Streamlit never has arbitrary commands.
"""
from hashlib import sha1
import os
from pathlib import Path
import subprocess
import sys

PUBLISHER = Path(r"C:\Control Center\v20-preview-d80f2446\deployment\v20_live_export.py")
BLOB = "28857795dc79edea16832a617f9b70ea97ab5907"
PYTHON = Path(r"C:\Control Center\runtime\python312\python.exe")
EXPECTED = ("cc02_export=PUBLISHED_CC_OWNED",
            "cc02_no_finam_no_task_mutation_no_arm=YES")

def refresh_once():
    """Return a literal result; never return secrets, arbitrary stdout or paths."""
    if os.name != "nt":
        return "PUBLISHER_UNAVAILABLE"
    try:
        if not (PUBLISHER.is_file() and PYTHON.is_file()
                and not PUBLISHER.is_symlink() and not PYTHON.is_symlink()
                and not PUBLISHER.parent.is_symlink()):
            return "PUBLISHER_UNAVAILABLE"
        body = PUBLISHER.read_bytes()
        if not 0 < len(body) <= 32768:
            return "PUBLISHER_UNVERIFIED"
        actual = sha1(b"blob " + str(len(body)).encode("ascii") + b"\0" + body).hexdigest()
        if actual != BLOB:
            return "PUBLISHER_UNVERIFIED"
        result = subprocess.run(
            [str(PYTHON), "-I", "-B", str(PUBLISHER), "--publish"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=90, check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        output = result.stdout.decode("utf-8", errors="replace")
        if result.returncode != 0 or len(output) > 4096 or any(
            marker not in output for marker in EXPECTED
        ):
            return "READONLY_EXPORT_FAILED"
        for robot in ("v20-shallow", "v20-obv", "v20-inside"):
            if "cc02_" + robot + "=" not in output:
                return "READONLY_EXPORT_INCOMPLETE"
        return "READONLY_EXPORT_PASS"
    except (OSError, ValueError, subprocess.SubprocessError):
        return "READONLY_EXPORT_UNAVAILABLE"
