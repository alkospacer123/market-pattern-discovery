"""FAILED CI EXPERIMENT ONLY: metadata handles still interfere with os.replace.

Native run 38873837179 disproved noninterference with zero desired access and
ALL sharing. Never import from the observer/UI or use on production files.
The retained experiment reproduces the blocker on disposable NTFS only.
"""
import ctypes
from ctypes import wintypes as w
from datetime import datetime, timedelta, timezone
import hashlib
import multiprocessing
from cc.providers.windows_file import WinAPI, components


class MetadataAPI(WinAPI):
    def open(self, path, directory):
        handle = self.k.CreateFileW(path, 0, 1 | 2 | 4, None, 3, 0x00200000 | 0x02000000, None)
        if handle == ctypes.c_void_p(-1).value or handle is None:
            code = ctypes.get_last_error()
            if code in (2, 3):
                raise FileNotFoundError()
            raise PermissionError()
        return handle

    def read(self, *args):
        raise AssertionError('CONTENT_READ_FORBIDDEN')


def metadata_native(root, filename, expected_root):
    api = MetadataAPI()
    paths, leaf = components(root, filename)
    api.volume(paths[0])
    held = []
    try:
        for path in paths:
            handle = api.open(path, True)
            held.append((handle, path, True, None))
            held[-1] = (handle, path, True, api.info(handle, path, True))
        if tuple(held[-1][3][:3]) != tuple(expected_root):
            raise ValueError('IDENTITY_MISMATCH')
        absent = False
        try:
            handle = api.open(leaf, False)
        except FileNotFoundError:
            absent = True
        if not absent:
            held.append((handle, leaf, False, None))
            held[-1] = (handle, leaf, False, api.info(handle, leaf, False))
        # Directory dates can change during publication; compare only identity/type.
        for handle, path, directory, before in held:
            check = api.open(path, directory)
            try:
                after = api.info(check, path, directory)
                stable = lambda info: info[:3] + info[-1:] if directory else info
                if stable(before) != stable(after):
                    raise ValueError('CHANGED')
            finally:
                api.close(check)
        if absent:
            return 'FILE_ABSENT', None
        info = held[-1][3]
        ticks = (info[4] << 32) | info[5]
        modified = datetime(1601, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=ticks // 10)
        return 'FILE_PRESENT', dict(identity=hashlib.sha256(repr(info[:3] + info[6:8]).encode('ascii')).hexdigest(),
                                    modified_at=modified.isoformat(), size=info[3])
    finally:
        for handle, *_ in reversed(held):
            api.close(handle)


def _worker(connection, root, filename, expected_root):
    try:
        state, value = metadata_native(root, filename, expected_root)
        connection.send((state, 'OK' if state == 'FILE_PRESENT' else 'NOT_FOUND', value))
    except PermissionError:
        connection.send(('UNKNOWN', 'ACCESS_DENIED', None))
    except Exception as exc:
        reason = str(exc) if str(exc) in ('IDENTITY_MISMATCH', 'CHANGED') else 'UNAVAILABLE'
        connection.send(('UNKNOWN', reason, None))
    finally:
        connection.close()


def probe(root, filename, expected_root, timeout=2.0):
    context = multiprocessing.get_context('spawn')
    receive, send = context.Pipe(duplex=False)
    worker = context.Process(target=_worker, args=(send, root, filename, expected_root), daemon=True)
    try:
        worker.start()
        send.close()
        if not receive.poll(timeout):
            return 'UNKNOWN', 'TIMEOUT', None
        return receive.recv()
    except Exception:
        return 'UNKNOWN', 'UNAVAILABLE', None
    finally:
        if worker.pid is not None:
            worker.join(0.1)
            if worker.is_alive():
                worker.terminate()
                worker.join(0.2)
        receive.close()
        send.close()
