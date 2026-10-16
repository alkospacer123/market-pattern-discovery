"""Native diagnostic only: never select an unsafe share mode for the reader."""
import json
import os
from pathlib import Path
import tempfile
from cc.providers.windows_file import WinAPI


def main():
    assert os.name == 'nt' and os.environ.get('RUNNER_ENVIRONMENT') == 'github-hosted'
    api = WinAPI()
    results = []
    with tempfile.TemporaryDirectory(prefix='cc03-share-', dir=os.environ['RUNNER_TEMP']) as root:
        for desired in (0x80000000, 0x1, 0x20080):
            for share in (1, 5, 7):
                path = Path(root) / 'target.json'; path.write_bytes(b'{}')
                replacement = Path(root) / 'new.json'; replacement.write_bytes(b'{ }')
                handle = api.k.CreateFileW(str(path), desired, share, None, 3, 0x02200000, None)
                assert handle not in (None, -1, 0xffffffffffffffff)
                record = dict(desired=hex(desired), share=share)
                try:
                    try:
                        os.replace(replacement, path)
                        record['replace'] = 'PASS'
                    except OSError as exc:
                        record['replace'] = f'WinError {exc.winerror}'
                    try:
                        with path.open('ab') as stream:
                            stream.write(b'X')
                        record['inplace_write'] = 'ALLOWED'
                    except OSError as exc:
                        record['inplace_write'] = f'WinError {exc.winerror}'
                finally:
                    api.close(handle)
                if replacement.exists():
                    os.replace(replacement, path)
                    record['replace_after_close'] = 'PASS'
                results.append(record)
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
