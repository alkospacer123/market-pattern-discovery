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
        # Limited UAC tokens and assigned powerful privileges are not standard.
        kind = w.DWORD()
        if not adv.GetTokenInformation(token, 18, ctypes.byref(kind), ctypes.sizeof(kind), ctypes.byref(needed)):
            raise ValueError('TOKEN_QUERY_DENIED')
        adv.GetTokenInformation(token, 3, None, 0, ctypes.byref(needed))
        privileges = ctypes.create_string_buffer(needed.value)
        if not adv.GetTokenInformation(token, 3, privileges, len(privileges), ctypes.byref(needed)):
            raise ValueError('TOKEN_QUERY_DENIED')
        count = w.DWORD.from_buffer(privileges).value
        if count > 128 or needed.value < 4 + count * 12:
            raise ValueError('TOKEN_PRIVILEGES_INVALID')
        adv.LookupPrivilegeNameW.argtypes = [w.LPCWSTR, w.LPVOID, w.LPWSTR, ctypes.POINTER(w.DWORD)]
        standard = {'SeChangeNotifyPrivilege', 'SeIncreaseWorkingSetPrivilege',
                    'SeTimeZonePrivilege', 'SeShutdownPrivilege', 'SeUndockPrivilege'}
        unsafe = bool(elevation.value) or kind.value != 1
        for index in range(count):
            name, size = ctypes.create_unicode_buffer(256), w.DWORD(256)
            if not adv.LookupPrivilegeNameW(None, ctypes.byref(privileges, 4 + index * 12), name, ctypes.byref(size)):
                raise ValueError('TOKEN_PRIVILEGE_UNKNOWN')
            unsafe = unsafe or name.value not in standard
        # Any thread impersonation is outside the approved primary-token model.
        kernel.GetCurrentThread.restype = w.HANDLE
        adv.OpenThreadToken.argtypes = [w.HANDLE, w.DWORD, w.BOOL, ctypes.POINTER(w.HANDLE)]
        thread_token = w.HANDLE()
        if adv.OpenThreadToken(kernel.GetCurrentThread(), 8, True, ctypes.byref(thread_token)):
            kernel.CloseHandle(thread_token)
            unsafe = True
        elif ctypes.get_last_error() != 1008:  # ERROR_NO_TOKEN is the only normal case.
            raise ValueError('THREAD_TOKEN_QUERY_DENIED')
        return result, unsafe
    finally:
        kernel.CloseHandle(token)
