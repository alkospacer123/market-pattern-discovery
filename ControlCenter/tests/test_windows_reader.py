"""Protocol fault tests run everywhere; native tests MUST run on real Windows."""
import ctypes
import os
from pathlib import Path
import subprocess
import pytest
from cc.providers import windows_file as win
from cc.providers.readonly_file import read_snapshot


class FakeAPI:
    def __init__(self, attack=None):
        self.attack, self.handles, self.closed, self.reading = attack, {}, [], False
        self.calls = 0

    def volume(self, anchor):
        if self.attack == 'network_volume':
            raise ValueError('denied')

    def open(self, path, directory):
        if self.attack in ('acl', 'locked', 'api_missing'):
            raise ValueError('denied')
        self.calls += 1
        self.handles[self.calls] = (path, directory)
        return self.calls

    def info(self, handle, path, directory):
        assert self.handles[handle] == (path, directory)
        if self.attack in ('symlink', 'junction', 'reparse', 'hardlink', 'type'):
            raise ValueError('invalid')
        size = 131073 if self.attack == 'oversize' else 2
        identity = hash(path)
        if self.reading and (self.attack == 'file_replace' and not directory or self.attack == 'directory_replace' and directory):
            identity += 1
        return (1, 2, identity, size, 1, 1)

    def read(self, handle, maximum):
        self.reading = True
        if self.attack == 'partial':
            return b'{'
        if self.attack == 'growing':
            return b' ' * (maximum + 1)
        return b'{}'

    def close(self, handle):
        self.closed.append(handle)


def test_protocol_read_and_root_pin():
    api = FakeAPI()
    assert win._read_native(r'C:\CC\export', 'h1.snapshot.json', 131072, api) == b'{}'
    assert set(api.closed) == set(api.handles)
    with pytest.raises(ValueError):
        win._read_native(r'C:\CC\export', 'h1.snapshot.json', 131072, FakeAPI(), [1, 2, 3])


@pytest.mark.parametrize('attack', ['network_volume','acl','locked','api_missing','symlink','junction','reparse',
                                   'hardlink','type','oversize','file_replace','directory_replace','partial','growing'])
def test_protocol_fail_closed_and_closes_handles(attack):
    api = FakeAPI(attack)
    with pytest.raises(ValueError):
        win._read_native(r'C:\CC\export', 'h1.snapshot.json', 131072, api)
    # Even a metadata failure after open must release the returned handle.
    assert set(api.closed) == set(api.handles)


@pytest.mark.parametrize('root,filename', [
    (r'C:\CC\..\export','h1.snapshot.json'), (r'C:\CC\.\export','h1.snapshot.json'),
    (r'\\host\share','h1.snapshot.json'), (r'\\?\C:\CC','h1.snapshot.json'),
    ('C:relative','h1.snapshot.json'), (r'C:\CC','../x'), (r'C:\CC','x:stream'),
    (r'C:\CC','CON.json'), (r'C:\CC','x.'), (r'C:\CC ','x'), ('C:/CC','x'),
])
def test_windows_path_rejected(root, filename):
    with pytest.raises(ValueError): win.components(root, filename)


@pytest.mark.parametrize('size', [0, -1, 131073, True])
def test_strict_limit(tmp_path, size):
    with pytest.raises(ValueError): read_snapshot(tmp_path, 'h1.snapshot.json', size)


def test_timeout_worker_is_terminated(monkeypatch):
    class Connection:
        def close(self): pass
        def poll(self, seconds):
            assert seconds == 2
            return False
    class Process:
        pid = 1
        terminated = False
        def start(self): pass
        def join(self, seconds): assert seconds <= .2
        def is_alive(self): return True
        def terminate(self): self.terminated = True
    process = Process()
    class Context:
        def Pipe(self, duplex): return Connection(), Connection()
        def Process(self, **kwargs): return process
    monkeypatch.setattr(win.multiprocessing, 'get_context', lambda method: Context())
    with pytest.raises(ValueError, match='TIMEOUT'):
        win.read_windows(r'C:\CC', 'h1.snapshot.json', 131072)
    assert process.terminated


native = pytest.mark.skipif(os.name != 'nt', reason='NOT_VERIFIED: requires real Windows local NTFS')


@native
def test_native_read_and_hardlink(tmp_path):
    path = tmp_path / 'h1.snapshot.json'
    path.write_bytes(b'{}')
    assert read_snapshot(tmp_path, path.name, 131072) == b'{}'
    os.link(path, tmp_path / 'another.json')
    with pytest.raises(ValueError): read_snapshot(tmp_path, path.name, 131072)


@native
@pytest.mark.parametrize('directory', [False, True])
def test_native_symlink(tmp_path, directory):
    target = tmp_path / 'target'
    if directory:
        target.mkdir(); (target / 'h1.snapshot.json').write_bytes(b'{}')
        link = tmp_path / 'link'
    else:
        target.write_bytes(b'{}'); link = tmp_path / 'h1.snapshot.json'
    try:
        link.symlink_to(target, target_is_directory=directory)
    except OSError:
        pytest.skip('NOT_VERIFIED: symlink creation privilege unavailable')
    with pytest.raises(ValueError):
        read_snapshot(link if directory else tmp_path, 'h1.snapshot.json', 131072)


@native
def test_native_junction_reparse(tmp_path):
    target = tmp_path / 'target'; target.mkdir()
    (target / 'h1.snapshot.json').write_bytes(b'{}')
    link = tmp_path / 'junction'
    subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(target)], check=True, capture_output=True)
    try:
        with pytest.raises(ValueError): read_snapshot(link, 'h1.snapshot.json', 131072)
    finally:
        link.rmdir()


@native
def test_native_legacy_replace_conflict_requires_live_block(tmp_path):
    path = tmp_path / 'h1.snapshot.json'; path.write_bytes(b'{}')
    api = win.WinAPI()
    handle = api.open(str(path), False)
    try:
        with pytest.raises(OSError): path.write_bytes(b'{')
        replacement = tmp_path / 'new.json'; replacement.write_bytes(b'{ }')
        with pytest.raises(PermissionError) as conflict:
            os.replace(replacement, path)
        assert conflict.value.winerror == 5
        assert api.read(handle, 131072) == b'{}'
    finally:
        api.close(handle)


@native
def test_native_api_missing(monkeypatch, tmp_path):
    monkeypatch.delattr(ctypes, 'WinDLL')
    with pytest.raises(AttributeError): win.WinAPI()


@native
def test_native_missing_oversize_and_directory(tmp_path):
    with pytest.raises(ValueError): read_snapshot(tmp_path, 'h1.snapshot.json', 131072)
    path = tmp_path / 'h1.snapshot.json'
    path.write_bytes(b' ' * 131073)
    with pytest.raises(ValueError): read_snapshot(tmp_path, path.name, 131072)
    path.unlink(); path.mkdir()
    with pytest.raises(ValueError): read_snapshot(tmp_path, path.name, 131072)


@native
def test_native_existing_writer_and_pinned_directory(tmp_path):
    path = tmp_path / 'h1.snapshot.json'; path.write_bytes(b'{}')
    with path.open('ab'):
        with pytest.raises(ValueError): read_snapshot(tmp_path, path.name, 131072)
    api = win.WinAPI()
    handle = api.open(str(tmp_path), True)
    try:
        with pytest.raises(OSError): tmp_path.rename(tmp_path.with_name(tmp_path.name+'-replaced'))
    finally:
        api.close(handle)


@native
def test_native_insufficient_file_acl(tmp_path):
    # Disposable test file only. Never use this test against production paths.
    path = tmp_path / 'h1.snapshot.json'; path.write_bytes(b'{}')
    output = subprocess.run(['whoami','/user','/fo','csv','/nh'],check=True,capture_output=True,text=True).stdout
    import csv
    sid = next(csv.reader([output.strip()]))[1]
    # Deny FILE_READ_DATA only. Denying READ_CONTROL too also prevents icacls
    # from reading the DACL to remove its own fixture ACE during cleanup.
    subprocess.run(['icacls',str(path),'/deny',f'*{sid}:(RD)'],check=True,capture_output=True)
    try:
        with pytest.raises(PermissionError): path.read_bytes()
        with pytest.raises(ValueError): read_snapshot(tmp_path, path.name, 131072)
    finally:
        subprocess.run(['icacls',str(path),'/remove:d',f'*{sid}'],check=True,capture_output=True)
    assert path.read_bytes() == b'{}'


@native
def test_native_legacy_concurrent_conflict_and_release(tmp_path):
    path = tmp_path / 'h1.snapshot.json'; path.write_bytes(b'{}')
    replacement = tmp_path / 'new.json'; replacement.write_bytes(b'{ }')
    class ReplacingAPI(win.WinAPI):
        def read(self, handle, maximum):
            data = super().read(handle, maximum)
            os.replace(replacement, path)  # Legacy conflict must remain visible.
            return data
    with pytest.raises(PermissionError) as conflict:
        win._read_native(str(tmp_path), path.name, 131072, ReplacingAPI())
    assert conflict.value.winerror == 5
    # Every reader handle closed even on conflict; producer resumes unchanged.
    os.replace(replacement, path)
    assert path.read_bytes() == b'{ }'



def test_policy_acl_is_checked_on_root_and_leaf_before_data():
    class PolicyAPI(FakeAPI):
        def __init__(self):
            super().__init__(); self.checked = []
        def admin_policy(self, handle):
            self.checked.append(self.handles[handle][0])
    api = PolicyAPI()
    assert win._read_native(r'C:\CC\private','source-policy.json',131072,api,admin_policy=True) == b'{}'
    assert api.checked == [r'C:\CC', r'C:\CC\private', r'C:\CC\private\source-policy.json']
    class WeakPolicyAPI(PolicyAPI):
        def admin_policy(self, handle):
            raise ValueError('POLICY_WRITABLE_BY_UNTRUSTED_SID')
    api = WeakPolicyAPI()
    with pytest.raises(ValueError):
        win._read_native(r'C:\CC\private','source-policy.json',131072,api,admin_policy=True)
    assert not api.reading and set(api.closed) == set(api.handles)


@native
def test_native_policy_with_untrusted_write_acl_is_rejected(tmp_path):
    path = tmp_path / 'policy.json'; path.write_bytes(b'{}')
    subprocess.run(['icacls',str(path),'/grant','*S-1-5-32-545:(W)'],check=True,capture_output=True)
    api = win.WinAPI(); handle = api.open(str(path), False)
    try:
        with pytest.raises(ValueError): api.admin_policy(handle)
    finally:
        api.close(handle)


@native
def test_native_admin_owned_policy_accepts_then_rejects_weak_ace(tmp_path):
    if not ctypes.windll.shell32.IsUserAnAdmin():
        pytest.skip('NOT_VERIFIED: positive policy ACL test requires elevated disposable sandbox')
    path = tmp_path / 'policy.json'; path.write_bytes(b'{}')
    subprocess.run(['icacls',str(path),'/inheritance:r','/grant:r','*S-1-5-18:(F)',
                    '*S-1-5-32-544:(F)'],check=True,capture_output=True)
    subprocess.run(['icacls',str(path),'/setowner','*S-1-5-32-544'],check=True,capture_output=True)
    api = win.WinAPI(); handle = api.open(str(path), False)
    try:
        api.admin_policy(handle)
    finally:
        api.close(handle)
    subprocess.run(['icacls',str(path),'/grant','*S-1-5-32-545:(W)'],check=True,capture_output=True)
    handle = api.open(str(path), False)
    try:
        with pytest.raises(ValueError): api.admin_policy(handle)
    finally:
        api.close(handle)
