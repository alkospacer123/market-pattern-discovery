"""Read-only offline wheel closure verification; run by the trusted base with -I -B.

No wheel imports, subprocesses, network, extraction or temp-file writes.
"""
from email.parser import BytesParser
from hashlib import file_digest
from pathlib import Path
import re
import sys
import zipfile
from pip._vendor.packaging.requirements import Requirement
from pip._vendor.packaging.tags import sys_tags
from pip._vendor.packaging.utils import canonicalize_name, parse_wheel_filename


def check(root, lock, requirements):
    pins = {}
    for line in lock.read_text().splitlines():
        if not line or line.startswith('#'):
            continue
        match = re.fullmatch(r'([\w-]+)==([^ ]+) --hash=sha256:([a-f0-9]{64})', line)
        if not match:
            raise ValueError('LOCK_FORMAT_INVALID')
        name, version, digest = match.groups()
        name = canonicalize_name(name)
        if name in pins:
            raise ValueError('LOCK_DUPLICATE')
        pins[name] = (version, digest)
    found = {}
    tags = set(sys_tags())
    for path in root.glob('*.whl'):
        name, version, _, supported = parse_wheel_filename(path.name)
        if name not in pins:  # CI may stage extra reviewed test-tool wheels.
            continue
        with path.open('rb') as stream:
            digest = file_digest(stream, 'sha256').hexdigest()
        if str(version) != pins[name][0] or digest != pins[name][1] or not supported & tags or name in found:
            raise ValueError('WHEEL_LOCK_HASH_OR_PLATFORM_MISMATCH')
        with zipfile.ZipFile(path) as archive:
            metadata = [n for n in archive.namelist() if n.endswith('.dist-info/METADATA')]
            if len(metadata) != 1:
                raise ValueError('WHEEL_METADATA_INVALID')
            info = BytesParser().parsebytes(archive.read(metadata[0]))
            if canonicalize_name(info['Name']) != name or info['Version'] != str(version):
                raise ValueError('WHEEL_IDENTITY_MISMATCH')
            found[name] = info.get_all('Requires-Dist', [])
    if set(found) != set(pins):
        raise ValueError('OFFLINE_PINNED_WHEELS_MISSING')
    dependencies = [line for line in requirements.read_text().splitlines() if line and not line.startswith('#')]
    dependencies += [entry for entries in found.values() for entry in entries]
    for entry in dependencies:
        req = Requirement(entry)
        if req.marker is not None and not req.marker.evaluate({'extra': ''}):
            continue
        key = canonicalize_name(req.name)
        if req.url or req.extras or key not in pins or not req.specifier.contains(pins[key][0]):
            raise ValueError('OFFLINE_DEPENDENCY_CLOSURE_INVALID: ' + str(req))
    print('OFFLINE_WHEEL_CLOSURE_PASS=' + str(len(pins)))


if __name__ == '__main__':
    check(*(Path(arg) for arg in sys.argv[1:]))
