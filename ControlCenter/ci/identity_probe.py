"""Separate-SID Python/spawn proof using synthetic bytes, disposable VM only."""
import ctypes
import json
import multiprocessing
import os
from pathlib import Path
import sys
from cc.providers.windows_file import read_windows, WinAPI


def main():
    assert os.name == 'nt' and os.environ.get('RUNNER_ENVIRONMENT') == 'github-hosted'
    # whoami is performed by the PS bootstrap; Python verifies access and spawn.
    root = Path(os.environ['TEMP'])
    path = root/'probe.json'; path.write_bytes(b'{}')
    api=WinAPI(); handle=api.open(str(root), True)
    try: pin=api.info(handle,str(root),True)[:3]
    finally: api.close(handle)
    assert read_windows(root,path.name,131072,pin) == b'{}'
    print(json.dumps(dict(identity_python='PASS',expected_sid=sys.argv[1],python=sys.version,
                          executable=sys.executable,cwd=os.getcwd(),spawn=multiprocessing.get_start_method(),
                          ntfs_read_spawn='PASS')),flush=True)


if __name__ == '__main__': main()
