"""Reproducible offline checks for the proposed amendment; connections forbidden."""
from pathlib import Path
import argparse
import socket
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'src'))
def deny(*args,**kwargs): raise AssertionError('STOP_TICK_GRID_OFFLINE_NETWORK_FORBIDDEN')
socket.socket.connect=deny;socket.socket.connect_ex=deny;socket.create_connection=deny
import pytest

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--basetemp',type=Path,required=True)
    parser.add_argument('--full-stage8',action='store_true')
    args=parser.parse_args()
    args.basetemp.parent.mkdir(parents=True,exist_ok=True)
    paths=[
        'TradingSystemLab/stage8_robot/tests/test_stop_tick_grid_amendment.py',
        'TradingSystemLab/stage8_robot/tests/test_finam_fill_price_readonly.py',
        'TradingSystemLab/stage8_robot/tests/test_finam_durable_fill_handoff.py',
        'TradingSystemLab/stage8_robot/tests/test_entry_pre_post_recovery.py',
        'TradingSystemLab/stage8_robot/tests/test_release_preparation.py',
        'TradingSystemLab/stage8_robot/tests/test_stage8_12_production_runtime.py',
        'TradingSystemLab/stage8_robot/tests/test_stage8_12_production_conformance.py',
        'TradingSystemLab/stage8_robot/tests/test_stage8_12_4_production_service.py',
        'TradingSystemLab/stage8_robot/tests/test_stage8_12_4_production_broker_state.py',
        'TradingSystemLab/stage8_robot/tests/test_stage8.py',
        'TradingSystemLab/stage8_robot/tests/test_real_readonly_margin.py',
        'TradingSystemLab/stage8_robot/tests/test_sqlite_recovery.py',
        'TradingSystemLab/results/post_v3_analysis/stage7_production_specification_freeze/test_production_specification.py',
        'tests/test_trail1_authoritative_ledger.py',
    ]
    if args.full_stage8:
        paths=sorted(set(paths)|{str(p.relative_to(ROOT)) for p in (ROOT/'TradingSystemLab/stage8_robot/tests').glob('test_*.py')})
    raise SystemExit(pytest.main(['-q','-p','no:cacheprovider','--basetemp='+str(args.basetemp),*paths]))
