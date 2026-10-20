"""Independent Git/manifest audit for #550; no production imports or source I/O.

Run in the disposable CI checkout, including sparse/shallow merge checkouts.
Source evidence is pinned metadata, not an instruction to open Intel files.
"""
import json
from pathlib import Path
import subprocess

from scope_audit import audit as scope_audit


def audit():
    from deployment.manifest import MANIFEST, entries
    root = Path(__file__).absolute().parents[1]
    evidence = json.loads((root / 'docs/CC03_H1_SOURCE_EVIDENCE.json').read_text())
    assert evidence['classification'] == 'NOT_AUTHORIZED / NO_SAFE_SOURCE'
    expected = evidence['unchanged_runtime_git_entries']
    output = subprocess.check_output(['git', '-C', str(root.parent), 'ls-tree',
                                      '--full-tree', 'HEAD', '--', *expected], text=True)
    actual = {}
    for line in output.splitlines():
        metadata, name = line.split('\t', 1)
        actual[name] = metadata
    assert actual == expected, 'SOURCE_FEASIBILITY_RUNTIME_OR_GUARD_CHANGED'
    sources = evidence['inspected_source_files']
    source_pins = {row['path']: row['git_blob'] for row in sources}
    assert len(source_pins) == len(sources), 'DUPLICATE_SOURCE_PIN'
    output = subprocess.check_output(['git', '-C', str(root.parent), 'ls-tree',
                                      '--full-tree', '-r', 'HEAD', '--', *source_pins], text=True)
    actual_sources = {}
    for line in output.splitlines():
        metadata, name = line.split('\t', 1)
        actual_sources[name] = metadata.split()[2]
    assert actual_sources == source_pins, 'INSPECTED_SOURCE_BLOB_CHANGED'
    protected = scope_audit()
    assert json.loads(MANIFEST.read_text())['files'] == entries(), 'MANIFEST_MISMATCH'
    report = dict(classification=evidence['classification'], base_sha=evidence['base_sha'],
                  runtime_and_entrypoints='UNCHANGED_FROM_ACTUAL_MAIN',
                  inspected_source_blob_pins='PASS',
                  outside_controlcenter=protected['outside_controlcenter'], manifest='PASS',
                  producer_activation='DISABLED', independent_audit='AUTOMATED_GIT_AND_MANIFEST',
                  external_reviewer_approval='NOT_CLAIMED')
    print(json.dumps(report, indent=2))
    return report


if __name__ == '__main__':
    # Match the ControlCenter pytest/CLI import root without installing modules.
    import sys
    sys.path.insert(0, str(Path(__file__).absolute().parents[1]))
    audit()
