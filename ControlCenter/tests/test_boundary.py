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
        'windows_file.py': {'ctypes', 'pathlib', 'hashlib', 'os', 're', 'json', 'subprocess', 'sys'},
        'h1_export.py': {'json', 'pathlib', 'threading'},
        'h1_windows_os.py': {'json', 'pathlib', 're', 'observer'},
        'deployment_paths.py': {'os', 'pathlib', 're'},
        'manual_gate.py': {'contextlib', 'os', 'ctypes', 'fcntl'},
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
                assert not any(k.arg in ('on_click','args','kwargs') for k in node.keywords)
                if path.name == 'app.py':
                    # Exactly one non-trading UI control; no Task/shell/network capability.
                    assert len(node.args)==1 and isinstance(node.args[0],ast.Constant)
                    assert node.args[0].value=='Обновить данные'
                    assert any(k.arg=='key' and isinstance(k.value,ast.Constant)
                               and k.value.value=='cc03-manual-refresh' for k in node.keywords)
                    assert any(k.arg=='disabled' for k in node.keywords)
                else:
                    assert any(k.arg=='disabled' and isinstance(k.value,ast.Constant)
                               and k.value.value is True for k in node.keywords)


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


def test_manual_refresh_only_no_timer_or_background_poll():
    tree=ast.parse((ROOT/'app.py').read_text(encoding='utf-8'))
    calls=[node for node in ast.walk(tree) if isinstance(node,ast.Call)
           and isinstance(node.func,ast.Attribute)]
    assert not any(c.func.attr in {'fragment','autorefresh','experimental_rerun','rerun'}
                   for c in calls)
    buttons=[c for c in calls if c.func.attr=='button']
    assert len(buttons)==1 and buttons[0].args[0].value=='Обновить данные'
    assert not any(isinstance(node,(ast.While,ast.AsyncFor,ast.For)) for node in ast.walk(tree))


def test_native_reader_has_only_one_fixed_isolated_child_and_no_shell():
    tree = ast.parse((ROOT / 'cc/providers/windows_file.py').read_text(encoding='utf-8'))
    children = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name) and node.func.value.id == 'subprocess'
                and node.func.attr in {'run', 'Popen', 'call', 'check_call', 'check_output'}]
    assert len(children) == 1 and children[0].func.attr == 'run'
    child = children[0]
    assert ast.unparse(child.args[0]) == "[sys.executable, '-I', '-B', str(Path(__file__).absolute())]"
    options = {k.arg: ast.unparse(k.value) for k in child.keywords}
    assert options == dict(input='request', stdout='subprocess.PIPE', stderr='subprocess.DEVNULL',
                           timeout='TIMEOUT_SECONDS', env='environment',
                           creationflags='subprocess.CREATE_NO_WINDOW')
    writes = [ast.unparse(node) for node in ast.walk(tree) if isinstance(node, ast.Call)
              and isinstance(node.func, ast.Attribute) and node.func.attr == 'write']
    assert sorted(writes) == ["sys.stdout.buffer.write(b'N')", "sys.stdout.buffer.write(b'Y' + data)"]
