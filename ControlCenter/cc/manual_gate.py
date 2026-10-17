"""Nonblocking OS gate for manual CC export reads; no polling or source access."""
from contextlib import contextmanager
import os


def _windows_sid(kernel, ctypes, w):
    # Scope the object to the actual token SID, never an environment username.
    # An administrator/test identity must not create an inaccessible object for
    # the separately owned standard ccpanel. No cross-user grant is introduced.
    adv = ctypes.WinDLL('advapi32', use_last_error=True)
    kernel.GetCurrentProcess.restype = w.HANDLE
    kernel.LocalFree.argtypes = [w.LPVOID]
    adv.OpenProcessToken.argtypes = [w.HANDLE, w.DWORD, ctypes.POINTER(w.HANDLE)]
    adv.GetTokenInformation.argtypes = [w.HANDLE, w.DWORD, w.LPVOID, w.DWORD, ctypes.POINTER(w.DWORD)]
    adv.ConvertSidToStringSidW.argtypes = [w.LPVOID, ctypes.POINTER(w.LPWSTR)]
    token = w.HANDLE()
    if not adv.OpenProcessToken(kernel.GetCurrentProcess(), 8, ctypes.byref(token)):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        needed = w.DWORD()
        adv.GetTokenInformation(token, 1, None, 0, ctypes.byref(needed))
        if not 0 < needed.value <= 16384:
            raise ValueError('TOKEN_QUERY_UNAVAILABLE')
        data = ctypes.create_string_buffer(needed.value)
        if not adv.GetTokenInformation(token, 1, data, len(data), ctypes.byref(needed)):
            raise ctypes.WinError(ctypes.get_last_error())
        sid = w.LPWSTR()
        if not adv.ConvertSidToStringSidW(w.LPVOID.from_buffer(data), ctypes.byref(sid)):
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            return sid.value
        finally:
            kernel.LocalFree(ctypes.cast(sid, w.LPVOID))
    finally:
        kernel.CloseHandle(token)


@contextmanager
def export_gate():
    """All Windows sessions/processes of the same SID share one mutex during the read.

    An inaccessible/precreated object fails closed. The OS releases ownership on
    process exit. No file in H1, FINAM, or the protected CC package is touched.
    """
    if os.name == 'nt':
        import ctypes
        from ctypes import wintypes as w
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.CreateMutexExW.argtypes = [w.LPVOID, w.LPCWSTR, w.DWORD, w.DWORD]
        kernel.CreateMutexExW.restype = w.HANDLE
        kernel.WaitForSingleObject.argtypes = [w.HANDLE, w.DWORD]
        kernel.WaitForSingleObject.restype = w.DWORD
        kernel.ReleaseMutex.argtypes = [w.HANDLE]
        kernel.CloseHandle.argtypes = [w.HANDLE]
        sid = _windows_sid(kernel, ctypes, w)
        # Explicit own-SID rights work across logon sessions; never depend on a
        # default DACL's logon SID or request ALL_ACCESS to an existing mutex.
        class SecurityAttributes(ctypes.Structure):
            _fields_ = [('size', w.DWORD), ('descriptor', w.LPVOID), ('inherit', w.BOOL)]
        adv = ctypes.WinDLL('advapi32', use_last_error=True)
        adv.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes = [
            w.LPCWSTR, w.DWORD, ctypes.POINTER(w.LPVOID), ctypes.POINTER(w.DWORD)]
        descriptor = w.LPVOID()
        if not adv.ConvertStringSecurityDescriptorToSecurityDescriptorW(
                'D:P(A;;0x00100001;;;' + sid + ')(A;;GA;;;SY)', 1, ctypes.byref(descriptor), None):
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            attributes = SecurityAttributes(ctypes.sizeof(SecurityAttributes), descriptor, False)
            handle = kernel.CreateMutexExW(ctypes.byref(attributes),
                'Global\\ControlCenter.CC03.ManualExportRefresh.v2.' + sid, 0, 0x00100001)
        finally:
            kernel.LocalFree(descriptor)
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        owned = False
        try:
            result = kernel.WaitForSingleObject(handle, 0)
            if result == 0xFFFFFFFF:
                raise ctypes.WinError(ctypes.get_last_error())
            owned = result in (0, 0x80)
            yield owned
        finally:
            if owned:
                kernel.ReleaseMutex(handle)
            kernel.CloseHandle(handle)
    else:
        # Development on POSIX: lock the existing module inode read-only.
        # Windows uses the machine-wide mutex even across separate checkouts.
        import fcntl
        descriptor = os.open(__file__, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                yield False
                return
            try:
                yield True
            finally:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)
