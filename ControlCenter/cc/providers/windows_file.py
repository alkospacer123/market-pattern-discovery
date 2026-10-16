"""Local NTFS read boundary. No shell, trading imports, write handles or fallback.

Directories deny DELETE sharing; leaves allow DELETE sharing. Hosted Windows
acceptance still exposes a blocking legacy os.replace conflict; do not deploy.
A spawned worker bounds native I/O; ACL/source trust remains an acceptance gate.
"""
import ctypes
from ctypes import wintypes as w
import multiprocessing
from pathlib import PureWindowsPath
import hashlib
import os
import re

MAX_BYTES = 128 * 1024
TIMEOUT_SECONDS = 2.0
SNAPSHOT_NAME = re.compile(r"h1-[0-9]{20}-[a-f0-9]{32}-([a-f0-9]{64})\.json")
MAX_ENTRIES = 2048


def components(root, filename):
    raw = str(root)
    path = PureWindowsPath(raw)
    if (not path.is_absolute() or len(path.drive) != 2 or path.drive[1] != ':'
            or '/' in raw or raw.startswith('\\\\') or '..' in raw.split('\\')
            or '.' in raw.split('\\')):
        raise ValueError('PATH_INVALID')
    parts = (*path.parts[1:], filename)
    reserved = {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(10)), *(f'LPT{i}' for i in range(10))}
    for part in parts:
        if (not part or part[-1] in '. ' or any(c in part for c in ':\\/\x00*?"<>|')
                or any(ord(c) < 32 for c in part) or part.split('.')[0].upper() in reserved):
            raise ValueError('PATH_INVALID')
    paths = [path.anchor]
    for part in path.parts[1:]:
        paths.append(str(PureWindowsPath(paths[-1]) / part))
    return paths, str(path / filename)


class FileInfo(ctypes.Structure):
    _fields_ = [('attributes', w.DWORD), ('creation', w.FILETIME), ('access', w.FILETIME),
                ('modified', w.FILETIME), ('volume', w.DWORD), ('size_high', w.DWORD),
                ('size_low', w.DWORD), ('links', w.DWORD), ('index_high', w.DWORD), ('index_low', w.DWORD)]


class WinAPI:
    def __init__(self):
        # Missing DLL/export => fail closed. No dynamically selected DLL or dependency.
        self.k = ctypes.WinDLL('kernel32', use_last_error=True)
        self.security = ctypes.WinDLL('advapi32', use_last_error=True)
        signatures = {
            'CreateFileW': ([w.LPCWSTR, w.DWORD, w.DWORD, w.LPVOID, w.DWORD, w.DWORD, w.HANDLE], w.HANDLE),
            'CloseHandle': ([w.HANDLE], w.BOOL),
            'LocalFree': ([w.LPVOID], w.LPVOID),
            'GetFileInformationByHandle': ([w.HANDLE, ctypes.POINTER(FileInfo)], w.BOOL),
            'GetFinalPathNameByHandleW': ([w.HANDLE, w.LPWSTR, w.DWORD, w.DWORD], w.DWORD),
            'GetFileType': ([w.HANDLE], w.DWORD),
            'ReadFile': ([w.HANDLE, w.LPVOID, w.DWORD, ctypes.POINTER(w.DWORD), w.LPVOID], w.BOOL),
            'GetDriveTypeW': ([w.LPCWSTR], w.UINT),
            'GetVolumeInformationW': ([w.LPCWSTR, w.LPWSTR, w.DWORD, ctypes.POINTER(w.DWORD),
                                       ctypes.POINTER(w.DWORD), ctypes.POINTER(w.DWORD), w.LPWSTR, w.DWORD], w.BOOL),
        }
        for name, (args, result) in signatures.items():
            fn = getattr(self.k, name)
            fn.argtypes, fn.restype = args, result

    def admin_policy(self, handle):
        # Policy authenticity is anchored in OS ACL, never in its own booleans.
        # Source/export files use separately accepted producer ACLs instead.
        security = self.security
        security.GetSecurityInfo.argtypes = [w.HANDLE, w.DWORD, w.DWORD, ctypes.POINTER(w.LPVOID),
            ctypes.POINTER(w.LPVOID), ctypes.POINTER(w.LPVOID), ctypes.POINTER(w.LPVOID), ctypes.POINTER(w.LPVOID)]
        security.GetSecurityInfo.restype = w.DWORD
        security.GetAce.argtypes = [w.LPVOID, w.DWORD, ctypes.POINTER(w.LPVOID)]
        security.GetAce.restype = w.BOOL
        security.ConvertSidToStringSidW.argtypes = [w.LPVOID, ctypes.POINTER(w.LPWSTR)]
        security.ConvertSidToStringSidW.restype = w.BOOL
        owner, dacl, descriptor = w.LPVOID(), w.LPVOID(), w.LPVOID()
        if security.GetSecurityInfo(handle, 1, 1 | 4, ctypes.byref(owner), None,
                                    ctypes.byref(dacl), None, ctypes.byref(descriptor)) != 0:
            raise ValueError('POLICY_ACL_UNAVAILABLE')
        def sid_string(pointer):
            output = w.LPWSTR()
            if not security.ConvertSidToStringSidW(pointer, ctypes.byref(output)):
                raise ValueError('POLICY_SID_INVALID')
            try:
                return output.value
            finally:
                self.k.LocalFree(ctypes.cast(output, w.LPVOID))
        try:
            trusted = {'S-1-5-18', 'S-1-5-32-544'}
            if not dacl.value or not owner.value or sid_string(owner) not in trusted:
                raise ValueError('POLICY_OWNER_OR_DACL_INVALID')
            # ACL header: revision, reserved, size WORD, count WORD, reserved WORD.
            count = ctypes.c_ushort.from_address(dacl.value + 4).value
            for index in range(count):
                ace = w.LPVOID()
                if not security.GetAce(dacl, index, ctypes.byref(ace)):
                    raise ValueError('POLICY_ACE_INVALID')
                kind = ctypes.c_ubyte.from_address(ace.value).value
                flags = ctypes.c_ubyte.from_address(ace.value + 1).value
                if flags & 0x08:  # INHERIT_ONLY_ACE does not apply to this object.
                    continue
                if kind == 1:  # ACCESS_DENIED_ACE cannot grant write authority.
                    continue
                if kind != 0:
                    raise ValueError('POLICY_ACE_UNSUPPORTED')
                mask = ctypes.c_uint32.from_address(ace.value + 4).value
                if mask & (0x40000000 | 0x10000000 | 0x000D0156):
                    if sid_string(ace.value + 8) not in trusted:
                        raise ValueError('POLICY_WRITABLE_BY_UNTRUSTED_SID')
        finally:
            self.k.LocalFree(descriptor)

    def volume(self, anchor):
        fs = ctypes.create_unicode_buffer(32)
        if (self.k.GetDriveTypeW(anchor) != 3 or not self.k.GetVolumeInformationW(
                anchor, None, 0, None, None, None, fs, len(fs)) or fs.value != 'NTFS'):
            raise ValueError('LOCAL_NTFS_REQUIRED')

    def open(self, path, directory):
        # FILE_LIST_DIRECTORY + READ_ATTRIBUTES + READ_CONTROL for directories;
        # metadata-only access does not participate in Windows share checking.
        # GENERIC_READ for leaf. OPEN_EXISTING.
        # Directory WRITE sharing permits child publication while DELETE denial
        # pins the directory itself. Leaf DELETE sharing is necessary but the
        # hosted test still exposes legacy os.replace blocking on an open leaf.
        # OPEN_REPARSE_POINT applies even to directories; never traverse an unchecked one.
        handle = self.k.CreateFileW(path, (0x1 | 0x80 | 0x20000) if directory else 0x80000000,
                                    1 | 2 if directory else 1 | 4, None, 3, 0x00200000 | 0x02000000, None)
        if handle == ctypes.c_void_p(-1).value or handle is None:
            raise ValueError('OPEN_DENIED')
        return handle

    def info(self, handle, path, directory):
        info = FileInfo()
        buf = ctypes.create_unicode_buffer(32768)
        n = self.k.GetFinalPathNameByHandleW(handle, buf, len(buf), 0)
        if (self.k.GetFileType(handle) != 1 or not self.k.GetFileInformationByHandle(handle, ctypes.byref(info))
                or not 0 < n < len(buf) or buf.value.casefold() != ('\\\\?\\' + path).casefold()
                or info.attributes & 0x400 or bool(info.attributes & 0x10) != directory):
            raise ValueError('FILE_TYPE_OR_PATH_INVALID')
        size = (info.size_high << 32) | info.size_low
        if not directory and info.links != 1:
            raise ValueError('HARDLINK_FORBIDDEN')
        # Access time is intentionally excluded: a read can update it.
        return (info.volume, info.index_high, info.index_low, size,
                info.modified.dwHighDateTime, info.modified.dwLowDateTime,
                info.creation.dwHighDateTime, info.creation.dwLowDateTime, info.links, info.attributes)

    def read(self, handle, maximum):
        data = ctypes.create_string_buffer(maximum + 1)
        count = w.DWORD()
        if not self.k.ReadFile(handle, data, maximum + 1, ctypes.byref(count), None):
            raise ValueError('READ_DENIED')
        return data.raw[:count.value]

    def close(self, handle):
        self.k.CloseHandle(handle)


def _read_native(root, filename, maximum, api, expected_root=None, admin_policy=False):
    directories, leaf = components(root, filename)
    api.volume(directories[0])
    held = []
    try:
        for path in directories:
            handle = api.open(path, True)
            held.append((handle, path, True, None))
            held[-1] = (handle, path, True, api.info(handle, path, True))
        if admin_policy:
            for handle, path, *_ in held[1:]:
                api.admin_policy(handle)
        if expected_root is not None and tuple(held[-1][3][:3]) != tuple(expected_root):
            raise ValueError("ROOT_IDENTITY_MISMATCH")
        # Discovery occurs while every ancestor and the accepted root are held.
        # Ignore unpublished temp files. Bound total entries, not just matches.
        if filename == 'LATEST-COMPLETED':
            names = []
            with os.scandir(root) as entries:
                for index, entry in enumerate(entries):
                    if index >= MAX_ENTRIES:
                        raise ValueError('EXPORT_DIRECTORY_FULL')
                    if SNAPSHOT_NAME.fullmatch(entry.name):
                        names.append(entry.name)
            if not names:
                raise ValueError('NO_COMPLETED_EXPORT')
            filename = max(names)
            _, leaf = components(root, filename)
        handle = api.open(leaf, False)
        held.append((handle, leaf, False, None))
        held[-1] = (handle, leaf, False, api.info(handle, leaf, False))
        if admin_policy:
            api.admin_policy(handle)
        size = held[-1][3][3]
        if not 0 < size <= maximum:
            raise ValueError('SIZE_INVALID')
        data = api.read(handle, maximum)
        if len(data) != size:
            raise ValueError('PARTIAL_READ')
        def stable(info, directory):
            # Publishing a child changes directory timestamps. Only directory
            # identity and attributes define the pinned no-reparse boundary.
            return info[:3] + info[-1:] if directory else info
        for handle, path, directory, before in held:
            if stable(api.info(handle, path, directory), directory) != stable(before, directory):
                raise ValueError('FILE_CHANGED')
            check = api.open(path, directory)
            try:
                if stable(api.info(check, path, directory), directory) != stable(before, directory):
                    raise ValueError('PATH_CHANGED')
            finally:
                api.close(check)
        match = SNAPSHOT_NAME.fullmatch(filename)
        if match and hashlib.sha256(data).hexdigest() != match[1]:
            raise ValueError('SNAPSHOT_NAME_DIGEST_MISMATCH')
        return data
    finally:
        for handle, *_ in reversed(held):
            api.close(handle)


def _worker(connection, root, filename, maximum, expected_root, admin_policy):
    try:
        connection.send_bytes(b'Y' + _read_native(root, filename, maximum, WinAPI(), expected_root, admin_policy))
    except Exception:
        connection.send_bytes(b'N')  # Never disclose native paths/errors.
    finally:
        connection.close()


def read_windows(root, filename, maximum, expected_root=None, admin_policy=False):
    if type(maximum) is not int or not 0 < maximum <= MAX_BYTES:
        raise ValueError('SIZE_LIMIT_INVALID')
    components(root, filename)
    context = multiprocessing.get_context('spawn')
    receive, send = context.Pipe(duplex=False)
    process = context.Process(target=_worker, args=(send, str(root), filename, maximum, expected_root, admin_policy), daemon=True)
    try:
        process.start()
        send.close()
        if not receive.poll(TIMEOUT_SECONDS):
            raise ValueError('READ_TIMEOUT')
        data = receive.recv_bytes(maxlength=maximum + 1)
        if not data.startswith(b'Y') or not 1 < len(data) <= maximum + 1:
            raise ValueError('SECURE_READ_UNAVAILABLE')
        return data[1:]
    finally:
        if process.pid is not None:
            process.join(0.1)
            if process.is_alive():
                process.terminate()
                process.join(0.2)
        receive.close()
        send.close()


def read_latest_windows(root, maximum, expected_root):
    if expected_root is None or len(expected_root) != 3 or any(type(x) is not int or x < 0 for x in expected_root):
        raise ValueError('EXPORT_ROOT_PIN_REQUIRED')
    return read_windows(root, 'LATEST-COMPLETED', maximum, expected_root)
