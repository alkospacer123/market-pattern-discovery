"""Query own token only; never adjust privileges or impersonate another token."""
import ctypes
from ctypes import wintypes as w


def current_identity():
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    adv = ctypes.WinDLL('advapi32', use_last_error=True)
    kernel.GetCurrentProcess.restype = w.HANDLE
    kernel.CloseHandle.argtypes = [w.HANDLE]
    kernel.LocalFree.argtypes = [w.LPVOID]
    adv.OpenProcessToken.argtypes = [w.HANDLE, w.DWORD, ctypes.POINTER(w.HANDLE)]
    adv.GetTokenInformation.argtypes = [w.HANDLE, w.DWORD, w.LPVOID, w.DWORD, ctypes.POINTER(w.DWORD)]
    adv.ConvertSidToStringSidW.argtypes = [w.LPVOID, ctypes.POINTER(w.LPWSTR)]
    token = w.HANDLE()
    if not adv.OpenProcessToken(kernel.GetCurrentProcess(), 8, ctypes.byref(token)):
        raise ValueError('TOKEN_QUERY_DENIED')
    try:
        needed = w.DWORD()
        adv.GetTokenInformation(token, 1, None, 0, ctypes.byref(needed))
        buffer = ctypes.create_string_buffer(needed.value)
        if not adv.GetTokenInformation(token, 1, buffer, len(buffer), ctypes.byref(needed)):
            raise ValueError('TOKEN_QUERY_DENIED')
        sid = w.LPWSTR()
        if not adv.ConvertSidToStringSidW(w.LPVOID.from_buffer(buffer), ctypes.byref(sid)):
            raise ValueError('TOKEN_QUERY_DENIED')
        try:
            result = sid.value
        finally:
            kernel.LocalFree(ctypes.cast(sid, w.LPVOID))
        elevation = w.DWORD()
        if not adv.GetTokenInformation(token, 20, ctypes.byref(elevation), ctypes.sizeof(elevation), ctypes.byref(needed)):
            raise ValueError('TOKEN_QUERY_DENIED')
        return result, bool(elevation.value)
    finally:
        kernel.CloseHandle(token)
