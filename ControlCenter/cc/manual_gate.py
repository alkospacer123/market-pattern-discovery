"""Nonblocking OS gate for manual CC export reads; no polling or source access."""
from contextlib import contextmanager
import os


def _windows_sid(kernel, ctypes, w):
    # The shared object name uses the actual token SID, never an environment username.
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
    """One local first-instance named pipe per SID, across Windows sessions.

    No connection, read, write, polling thread, or remote client is permitted.
    Holding the sole server handle is the lock; closing it (also on process exit)
    removes the instance. A competing/precreated object fails closed. This avoids
    the Global object namespace which denied the real standard hosted token.
    """
    if os.name == 'nt':
        import ctypes
        from ctypes import wintypes as w
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.CreateNamedPipeW.argtypes = [w.LPCWSTR, w.DWORD, w.DWORD, w.DWORD,
                                            w.DWORD, w.DWORD, w.DWORD, w.LPVOID]
        kernel.CreateNamedPipeW.restype = w.HANDLE
        kernel.CloseHandle.argtypes = [w.HANDLE]
        sid = _windows_sid(kernel, ctypes, w)
        # PIPE_ACCESS_INBOUND | FILE_FLAG_FIRST_PIPE_INSTANCE; maximum one
        # instance; PIPE_REJECT_REMOTE_CLIENTS. Never call ConnectNamedPipe.
        handle = kernel.CreateNamedPipeW('\\\\.\\pipe\\ControlCenter.CC03.ManualRefresh.v1.' + sid,
                                         0x00000001 | 0x00080000, 0x00000008, 1, 0, 0, 0, None)
        if handle == ctypes.c_void_p(-1).value or handle is None:
            error = ctypes.get_last_error()
            if error not in (5, 231):  # access denied / busy: including an existing first instance
                raise ctypes.WinError(error)
            yield False
            return
        try:
            yield True
        finally:
            kernel.CloseHandle(handle)
    else:
        # Development on POSIX: lock the existing module inode read-only.
        # Windows uses the same pipe name across sessions and separate checkouts.
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
