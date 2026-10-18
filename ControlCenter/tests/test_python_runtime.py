"""Offline pre-write validation of the wheel lock and runtime packaging contract."""
import importlib.util
from pathlib import Path
from hashlib import sha256
import zipfile
import pytest

ROOT = Path(__file__).parents[1]


def checker():
    spec = importlib.util.spec_from_file_location('cc_wheels', ROOT/'deployment/check_wheels.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture(tmp_path, dependency='', *, bad_hash=False):
    wheel = tmp_path/'example-1.0-py3-none-any.whl'
    with zipfile.ZipFile(wheel, 'w') as archive:
        archive.writestr('example-1.0.dist-info/METADATA', 'Name: example\nVersion: 1.0\n'+dependency)
    lock = tmp_path/'lock.txt'
    lock.write_text('example==1.0 --hash=sha256:'+('0'*64 if bad_hash else sha256(wheel.read_bytes()).hexdigest())+'\n')
    req = tmp_path/'req.txt'; req.write_text('example==1.0\n')
    return wheel, lock, req


def test_wheel_closure_is_readonly_and_rejects_missing_and_bad_bytes(tmp_path):
    module = checker()
    wheel, lock, req = fixture(tmp_path)
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    module.check(tmp_path, lock, req)
    assert before == {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    wheel.write_bytes(wheel.read_bytes()+b'tamper')
    with pytest.raises(ValueError, match='HASH_OR_PLATFORM'): module.check(tmp_path, lock, req)
    wheel.unlink()
    with pytest.raises(ValueError, match='WHEELS_MISSING'): module.check(tmp_path, lock, req)


def test_incomplete_and_unpinned_dependencies_rejected(tmp_path):
    module = checker()
    _, lock, req = fixture(tmp_path, 'Requires-Dist: missing>=2\n')
    with pytest.raises(ValueError, match='CLOSURE_INVALID'): module.check(tmp_path, lock, req)


def test_marker_excluded_dependency_does_not_require_wheel(tmp_path):
    module = checker()
    _, lock, req = fixture(tmp_path, 'Requires-Dist: missing; python_version < "2"\n')
    module.check(tmp_path, lock, req)


def test_runtime_entrypoints_never_use_launcher_and_start_revalidates():
    for name in ('Preflight','Install','Start-Panel','Verify'):
        source = (ROOT/f'deployment/{name}.ps1').read_text()
        assert 'py -3.12' not in source and 'Get-Command python' not in source
    for name in ('Start-Panel','Verify'):
        assert 'Assert-PanelVenv $PanelSid' in (ROOT/f'deployment/{name}.ps1').read_text()
    assert "'runtime'" in (ROOT/'deployment/manifest.py').read_text()
