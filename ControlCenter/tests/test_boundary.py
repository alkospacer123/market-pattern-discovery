"""Source audit plus runtime guards. Framework server networking is out of scope."""
import ast
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import urllib.request
import pytest
from cc.models import RobotId
from cc.providers.synthetic import SCENARIOS, SyntheticProvider, read_safely

ROOT=Path(__file__).resolve().parents[1]
RUNTIME=[ROOT/'app.py',*sorted((ROOT/'cc').rglob('*.py'))]
ALLOWED={'dataclasses','datetime','enum','math','types','typing','collections','streamlit','plotly','cc'}


@pytest.mark.parametrize('path',RUNTIME,ids=lambda p:p.name)
def test_no_trade_or_system_capabilities_in_runtime(path):
    # CC-02 grants only receiving modules their narrowly scoped stdlib imports.
    receiving = {
        'h1_contract.py': {'re'},
        'h1_readonly.py': {'hashlib', 'json', 'pathlib'},
        'readonly_file.py': {'os', 'pathlib', 'stat'},
        'windows_file.py': {'ctypes', 'multiprocessing', 'pathlib'},
        'h1_export.py': {'json', 'pathlib'},
    }
    allowed = ALLOWED | receiving.get(path.name, set())
    tree=ast.parse(path.read_text(encoding='utf-8'))
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):
            assert all(name.name.split('.')[0] in allowed for name in node.names)
        if isinstance(node,ast.ImportFrom) and node.level==0:
            assert node.module.split('.')[0] in allowed
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):
            assert node.func.id not in {'open','exec','eval','compile','__import__','input'}
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute):
            assert node.func.attr not in {'system','popen','Popen','connect','write_text','write_bytes','unlink','mkdir','run_command'}
            if node.func.attr=='button':
                assert any(k.arg=='disabled' and isinstance(k.value,ast.Constant) and k.value.value is True for k in node.keywords)
                assert not any(k.arg in ('on_click','args','kwargs') for k in node.keywords)


def test_scenarios_have_no_network_database_shell_side_effects(monkeypatch,now):
    def forbidden(*args,**kwargs):
        pytest.fail('external side effect attempted')
    for module,name in ((os,'system'),(subprocess,'Popen'),(socket,'create_connection'),
                        (sqlite3,'connect'),(urllib.request,'urlopen')):
        monkeypatch.setattr(module,name,forbidden)
    before=set(sys.modules)
    for robot in RobotId:
        for scenario in SCENARIOS:
            read_safely(SyntheticProvider(),robot,scenario,now)
    added=set(sys.modules)-before
    assert not any('finam' in name.lower() or name.startswith(('TradingSystemLab','IntradayLab')) for name in added)


def test_refresh_is_bounded_streamlit_fragment():
    tree=ast.parse((ROOT/'app.py').read_text())
    calls=[node for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='fragment']
    assert len(calls)==1
    keyword=calls[0].keywords[0]
    assert keyword.arg=='run_every' and isinstance(keyword.value,ast.IfExp) and keyword.value.body.value==2
    assert not any(isinstance(node,(ast.While,ast.AsyncFor)) for node in ast.walk(tree))
