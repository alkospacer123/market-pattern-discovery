"""Keep hosted acceptance I/O inside a single disposable runner directory."""
import os
from pathlib import Path, PureWindowsPath
import re


def sandbox_root(environment, *, windows):
    raw = environment.get('CC03_CI_DISPOSABLE_ROOT')
    if not raw:
        return None
    if (not windows or environment.get('GITHUB_ACTIONS') != 'true'
            or environment.get('RUNNER_ENVIRONMENT') != 'github-hosted'
            or not environment.get('RUNNER_TEMP')):
        raise ValueError('HOSTED_DISPOSABLE_REHEARSAL_REQUIRED')
    root, temporary = PureWindowsPath(raw), PureWindowsPath(environment['RUNNER_TEMP'])
    if (not root.is_absolute() or len(root.drive) != 2 or root.parent != temporary
            or not re.fullmatch(r'CC03-[a-f0-9]{32}', root.name)
            or any(part in ('.', '..') for part in raw.split('\\'))
            or '/' in raw or ':' in raw[2:]):
        raise ValueError('DISPOSABLE_ROOT_OUTSIDE_RUNNER_TEMP')
    return root


def data_root():
    root = sandbox_root(os.environ, windows=os.name == 'nt')
    return Path(root / 'data') if root is not None else Path('C:/TSLControlCenterData')
