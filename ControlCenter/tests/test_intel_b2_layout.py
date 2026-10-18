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


def test_readiness_uses_only_current_cc_root_and_never_old_install(monkeypatch):
    import json
    from pathlib import PureWindowsPath
    from types import SimpleNamespace
    from observer import intel_preflight as observer

    seen = []
    def stub_run(*args, **kwargs):
        seen.append(json.loads(kwargs['input'])['roots'])
        return SimpleNamespace(returncode=0, stdout=json.dumps(dict(
            observer_standard=True, identities='CCPANEL_ENABLED',
            directories='EXISTING_ROOTS_OBSERVED')))

    monkeypatch.setattr(observer.subprocess, 'run', stub_run)
    monkeypatch.setattr(observer.subprocess, 'CREATE_NO_WINDOW', 0, raising=False)
    policy = {'cc_panel_sid': None}
    for root in ('C:/Control Center/data', 'C:/Temp/CC03-' + 'a' * 32 + '/data'):
        monkeypatch.setattr(observer, 'data_root', lambda r=root: PureWindowsPath(r))
        assert observer.readiness(policy)['directories'] == 'EXISTING_ROOTS_OBSERVED'
        data = PureWindowsPath(root)
        assert seen[-1] == [str(data.parent / 'app'), str(data.parent / 'venv'), str(data),
                            str(data / 'export'), str(data / 'logs'), str(data / 'private')]
        assert all('TSLControlCenter' not in item for item in seen[-1])

def test_single_ccpanel_installer_is_fail_closed():
    root = ROOT / 'deployment'
    common = (root / 'Common.ps1').read_text(encoding='utf-8')
    assert "Get-LocalUser -Name 'ccpanel'" in (root / 'PanelIdentity.ps1').read_text()
    assert "Get-CCPanelState $PanelSid" in common
    assert "CCPANEL_PRIVATE_ACCESS_FORBIDDEN" in common
    assert "CCPANEL_WRITE_FORBIDDEN" in common
    assert "Assert-CCPanelSid" in common
    assert "Assert-LayoutACL([string]$PanelSid)" in common
    assert 'ExporterSid' not in common
    for name in ('Preflight', 'Install', 'Start-Panel', 'Verify', 'Uninstall'):
        script = (root / (name + '.ps1')).read_text(encoding='utf-8')
        assert '[string]$PanelSid' in script
        assert 'ExporterSid' not in script
        assert 'TradingSystemLab' not in script
        assert 'IntradayLab' not in script
    exporter = (root / 'Start-Exporter.ps1').read_text(encoding='utf-8')
    assert "throw 'CC03_SINGLE_CCPANEL_EXPORTER_DISABLED'" in exporter
    assert 'source-policy.json' not in exporter and 'os-policy.json' not in exporter
    native = (ROOT / 'ci/Windows-Rehearsal.ps1').read_text(encoding='utf-8')
    assert "foreach ($role in @('panel','exporter'))" not in native
    assert '$exporterSid' not in native
    assert "DISPOSABLE_CCPANEL_SID=" in native
    assert 'DISABLED_EXPORTER_PUBLISHED_DATA' in native
