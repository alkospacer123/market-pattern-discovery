"""Run explicitly selected existing offline checks; forbid network connections."""
from pathlib import Path
import socket
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
def deny_network(*args, **kwargs):
    raise AssertionError("AUDIT_NETWORK_CONNECTION_FORBIDDEN")
socket.socket.connect = deny_network
socket.socket.connect_ex = deny_network
socket.create_connection = deny_network

import pytest
raise SystemExit(pytest.main([
    "-q", "-p", "no:cacheprovider", "--basetemp=/workspace/work/stop-tick-results/pytest-temp",
    "TradingSystemLab/stage8_robot/tests/test_stage8_12_production_runtime.py",
    "TradingSystemLab/stage8_robot/tests/test_stage8_12_production_conformance.py",
    "TradingSystemLab/stage8_robot/tests/test_stage8_12_4_production_service.py",
    "TradingSystemLab/stage8_robot/tests/test_stage8.py",
    "TradingSystemLab/stage8_robot/tests/test_real_readonly_margin.py",
    "TradingSystemLab/stage8_robot/tests/test_sqlite_recovery.py",
    "TradingSystemLab/results/post_v3_analysis/stage7_production_specification_freeze/test_production_specification.py",
    "tests/test_trail1_authoritative_ledger.py",
]))
