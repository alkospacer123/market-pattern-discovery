"""Static, offline B2 layout checks; not physical Intel acceptance."""
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_windows_install_targets_are_only_under_control_center():
    script = (ROOT / 'deployment' / 'Common.ps1').read_text(encoding='utf-8')
    assert "$script:ControlCenterRoot = 'C:\\Control Center'" in script
    assert "Join-Path $script:ControlCenterRoot 'app'" in script
    assert "Join-Path $script:ControlCenterRoot 'venv'" in script
    assert "Join-Path $script:ControlCenterRoot 'data'" in script
    assert 'TSLControlCenterApp' not in script
    assert 'TSLControlCenterVenv' not in script
    assert 'TSLControlCenterData' not in script
    # CI sandbox override remains limited to disposable GitHub-hosted Windows.
    assert "$env:GITHUB_ACTIONS -cne 'true'" in script
    assert "$env:RUNNER_ENVIRONMENT -cne 'github-hosted'" in script


def test_staged_manifest_excludes_own_runtime_roots(tmp_path):
    spec = importlib.util.spec_from_file_location('b2_manifest', ROOT / 'deployment' / 'manifest.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ROOT = tmp_path
    module.MANIFEST = tmp_path / 'deployment' / 'manifest.json'
    (tmp_path / 'deployment').mkdir()
    module.MANIFEST.write_text('{}', encoding='utf-8')
    (tmp_path / 'app').mkdir()
    (tmp_path / 'app' / 'deployed.exe').write_bytes(b'not-source')
    (tmp_path / 'data').mkdir()
    (tmp_path / 'data' / 'private').mkdir()
    (tmp_path / 'data' / 'private' / 'os-policy.json').write_text('private')
    (tmp_path / 'venv').mkdir()
    (tmp_path / 'venv' / 'python.exe').write_bytes(b'not-source')
    (tmp_path / 'cc').mkdir()
    (tmp_path / 'cc' / 'app.py').write_text('source')
    assert [row['path'] for row in module.entries()] == ['cc/app.py']
