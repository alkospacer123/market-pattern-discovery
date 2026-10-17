"""Nonblocking OS gate for manual CC export reads; no polling or source access."""
from contextlib import contextmanager
import os


@contextmanager
def export_gate():
    """All Windows sessions/processes share one mutex, held through the read.

    An inaccessible/precreated object fails closed. The OS releases ownership on
    process exit. No file in H1, FINAM, or the protected CC package is touched.
    """
    if os.name == 'nt':
        import ctypes
        from ctypes import wintypes as w
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.CreateMutexW.argtypes = [w.LPVOID, w.BOOL, w.LPCWSTR]
        kernel.CreateMutexW.restype = w.HANDLE
        kernel.WaitForSingleObject.argtypes = [w.HANDLE, w.DWORD]
        kernel.WaitForSingleObject.restype = w.DWORD
        kernel.ReleaseMutex.argtypes = [w.HANDLE]
        kernel.CloseHandle.argtypes = [w.HANDLE]
        handle = kernel.CreateMutexW(None, False, r'Global\ControlCenter.CC03.ManualExportRefresh.v1')
        if not handle:
            yield False
            return
        owned = False
        try:
            owned = kernel.WaitForSingleObject(handle, 0) in (0, 0x80)
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
