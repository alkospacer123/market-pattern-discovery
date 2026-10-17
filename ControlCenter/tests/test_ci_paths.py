"""The rehearsal override must never select a production or neighboring root."""
from pathlib import PureWindowsPath
import pytest
from cc.deployment_paths import sandbox_root, data_root


def environment():
    return dict(GITHUB_ACTIONS='true', RUNNER_ENVIRONMENT='github-hosted',
                RUNNER_TEMP=r'D:\a\_temp',
                CC03_CI_DISPOSABLE_ROOT='D:\\a\\_temp\\CC03-' + 'a' * 32)


def test_only_hosted_disposable_root_can_be_selected():
    value = environment()
    assert sandbox_root(value, windows=True) == PureWindowsPath(value['CC03_CI_DISPOSABLE_ROOT'])
    assert sandbox_root({}, windows=False) is None
    with pytest.raises(ValueError):
        sandbox_root(value, windows=False)


@pytest.mark.parametrize('key,value', [
    ('GITHUB_ACTIONS', 'false'), ('RUNNER_ENVIRONMENT', 'self-hosted'), ('RUNNER_TEMP', ''),
    ('CC03_CI_DISPOSABLE_ROOT', r'C:\TSLControlCenterData'),
    ('CC03_CI_DISPOSABLE_ROOT', 'D:\\a\\_temporary\\CC03-' + 'a'*32),
    ('CC03_CI_DISPOSABLE_ROOT', 'D:\\a\\_temp\\..\\CC03-' + 'a'*32),
    ('CC03_CI_DISPOSABLE_ROOT', 'D:\\a\\_temp\\nested\\CC03-' + 'a'*32),
    ('CC03_CI_DISPOSABLE_ROOT', 'D:/a/_temp/CC03-' + 'a'*32),
    ('CC03_CI_DISPOSABLE_ROOT', r'\\server\share\CC03-' + 'a'*32),
    ('CC03_CI_DISPOSABLE_ROOT', 'D:\\a\\_temp\\CC03-' + 'a'*32 + ':stream'),
])
def test_invalid_rehearsal_root_fails_closed(key, value):
    env = environment(); env[key] = value
    with pytest.raises(ValueError):
        sandbox_root(env, windows=True)


def test_production_data_root_uses_operator_approved_project(monkeypatch):
    monkeypatch.delenv('CC03_CI_DISPOSABLE_ROOT', raising=False)
    assert str(data_root()).replace('\\', '/') == 'C:/Control Center/data'
