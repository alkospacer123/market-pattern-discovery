"""Run only on the disposable GitHub-hosted Windows VM; preserve exact evidence."""
import json
from hashlib import sha256
import os
from pathlib import Path
import platform
import struct
import subprocess
import sys
import uuid
import zipfile
import xml.etree.ElementTree as ET


def build_bundle(evidence):
    """Preserve manifest-verified bytes; Git archive applies Windows EOL filters."""
    root = Path(__file__).absolute().parents[1]
    manifest_raw = (root / 'deployment/manifest.json').read_bytes()
    manifest = json.loads(manifest_raw)
    bundle = evidence / 'CC03_INTEL_READONLY_PREFLIGHT_PACKAGE.zip'
    names = {'ControlCenter/deployment/manifest.json'}
    with zipfile.ZipFile(bundle, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('ControlCenter/deployment/manifest.json', manifest_raw)
        for entry in manifest['files']:
            relative = Path(entry['path'])
            assert not relative.is_absolute() and '..' not in relative.parts
            assert relative.name not in {'os-policy.json', 'source-policy.json',
                                         'receiver-policy.json', 'preflight-policy.json', 'manual-os-policy.json'}
            name = 'ControlCenter/' + relative.as_posix()
            assert name not in names
            names.add(name)
            raw = (root / relative).read_bytes()
            assert sha256(raw).hexdigest() == entry['sha256']
            archive.writestr(name, raw)
    with zipfile.ZipFile(bundle) as archive:
        assert set(archive.namelist()) == names
        assert archive.read('ControlCenter/deployment/manifest.json') == manifest_raw
        for entry in manifest['files']:
            assert sha256(archive.read('ControlCenter/' + entry['path'])).hexdigest() == entry['sha256']
    print('PREFLIGHT_BUNDLE_MANIFEST_VERIFIED=' + str(len(manifest['files'])), flush=True)
    return bundle, len(manifest['files'])


def main():
    assert os.name == 'nt' and os.environ.get('RUNNER_ENVIRONMENT') == 'github-hosted'
    assert sys.version_info[:3] == (3, 12, 10) and struct.calcsize('P') == 8
    # Even absence/UI tests must resolve default receiver/exporter I/O to a
    # disposable path, never the installed machine's conventional CC roots.
    sandbox = Path(os.environ['RUNNER_TEMP']) / ('CC03-' + uuid.uuid4().hex)
    sandbox.mkdir()
    os.environ['CC03_CI_DISPOSABLE_ROOT'] = str(sandbox)
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
    os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
    evidence = Path(os.environ['RUNNER_TEMP']) / 'cc03-evidence'
    evidence.mkdir(exist_ok=True)
    metadata = dict(windows=platform.platform(), windows_version=platform.win32_ver(),
                    python=sys.version, bits=struct.calcsize('P') * 8,
                    tested_sha=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
                    event_sha=os.environ['GITHUB_SHA'], run_id=os.environ['GITHUB_RUN_ID'])
    event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text(encoding='utf-8'))
    metadata.update(pr_head_sha=event['pull_request']['head']['sha'],
                    pr_base_sha=event['pull_request']['base']['sha'],
                    controlcenter_tree=subprocess.check_output(
                        ['git', 'rev-parse', 'HEAD:ControlCenter'], text=True).strip())
    print(json.dumps(metadata, indent=2), flush=True)
    (evidence / 'environment.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    (evidence / 'git-blobs.txt').write_text(subprocess.check_output(
        ['git', 'ls-tree', '--full-tree', '-r', 'HEAD', '--', 'ControlCenter'], text=True), encoding='utf-8')
    # Fail early on package-byte defects before repeating the full native suite.
    bundle, bundle_file_count = build_bundle(evidence)
    commands = [
        ('scope-audit', [sys.executable, 'ci/scope_audit.py']),
        ('host', ['powershell', '-NoProfile', '-Command',
                  "Get-CimInstance Win32_OperatingSystem | Select Caption,Version,BuildNumber | Format-List; "
                  "Get-Volume | Where DriveLetter -in @((Get-Item .).PSDrive.Name, (Get-Item $env:RUNNER_TEMP).PSDrive.Name) | Select DriveLetter,FileSystem | Format-Table; whoami /user; whoami /priv"]),
        ('windows-reader', [sys.executable, '-m', 'pytest', '-v', '-ra', 'tests/test_windows_reader.py',
                            f'--junitxml={evidence / "windows-reader.xml"}']),
        ('windows-transport', [sys.executable, '-m', 'pytest', '-v', '-ra', 'tests/test_windows_transport.py',
                                f'--junitxml={evidence / "windows-transport.xml"}']),
        ('cc03-source', [sys.executable, '-m', 'pytest', '-q', 'tests/test_cc03_source.py',
                         f'--junitxml={evidence / "cc03-source.xml"}']),
        ('os-observer', [sys.executable, '-m', 'pytest', '-v', '-ra', '-s',
                         'tests/test_os_observer.py', 'tests/test_os_windows_native.py',
                         f'--junitxml={evidence / "os-observer.xml"}']),
        ('intel-preflight', [sys.executable, '-m', 'pytest', '-v', '-ra',
                            'tests/test_intel_preflight.py', 'tests/test_intel_preflight_native.py',
                            f'--junitxml={evidence / "intel-preflight.xml"}']),
        ('manual-os', [sys.executable, '-m', 'pytest', '-v', '-ra', '-s',
                       'tests/test_manual_os.py','tests/test_manual_os_native.py',
                       f'--junitxml={evidence / "manual-os.xml"}']),
        ('full-suite', [sys.executable, '-m', 'pytest', '-q',
                        f'--junitxml={evidence / "full-suite.xml"}']),
        ('manifest', [sys.executable, 'deployment/manifest.py', '--check']),
        ('pip-check', [sys.executable, '-m', 'pip', 'check']),
        ('pip-freeze', [sys.executable, '-m', 'pip', 'freeze', '--all']),
        ('powershell-preview', ['powershell', '-NoProfile', '-Command',
            "$ErrorActionPreference='Stop'; Get-ChildItem deployment/*.ps1 | ForEach-Object { "
            "$tokens=$null; $errors=$null; [void][Management.Automation.Language.Parser]::ParseFile($_.FullName,[ref]$tokens,[ref]$errors); "
            "if ($errors.Count) { throw ($errors | Out-String) }; Write-Output ('SYNTAX_PASS '+$_.Name); "
            "if ($_.Name -ne 'Common.ps1') { & $_.FullName } }"]),
        ('powershell-rehearsal', ['powershell', '-NoProfile', '-File', 'ci/Windows-Rehearsal.ps1']),
    ]
    results = {}
    for name, command in commands:
        print(f'\n=== {name} ===', flush=True)
        environment = os.environ.copy()
        if command[0] == 'powershell':
            # pwsh's inherited PSModulePath includes incompatible PowerShell 7
            # copies of built-ins. Rehearse the actual Windows PowerShell 5.1.
            # os.environ is case-insensitive on Windows; its plain-dict copy is
            # not. Use canonical uppercase names and replace the existing key.
            environment['PSMODULEPATH'] = os.pathsep.join([
                str(Path(environment['SYSTEMROOT']) / 'System32/WindowsPowerShell/v1.0/Modules'),
                str(Path(environment['PROGRAMFILES']) / 'WindowsPowerShell/Modules')])
        try:
            completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       encoding='utf-8', errors='replace', timeout=600 if name == 'powershell-rehearsal' else 360, env=environment)
            output, exit_code = completed.stdout, completed.returncode
        except subprocess.TimeoutExpired as exc:
            output = (exc.stdout or b'').decode('utf-8', errors='replace') + '\nACCEPTANCE_COMMAND_TIMEOUT'
            exit_code = 124
        print(output, flush=True)
        (evidence / f'{name}.log').write_text(output, encoding='utf-8')
        results[name] = dict(exit_code=exit_code)
    for name in ('windows-reader', 'windows-transport', 'cc03-source', 'os-observer', 'intel-preflight', 'manual-os', 'full-suite'):
        path = evidence / f'{name}.xml'
        if not path.exists():
            results[name]['missing_junit'] = True
            continue
        cases = list(ET.parse(path).iter('testcase'))
        skipped = [dict(test=c.get('classname') + '.' + c.get('name'), reason=c.find('skipped').get('message'))
                   for c in cases if c.find('skipped') is not None]
        failed = sum(c.find('failure') is not None or c.find('error') is not None for c in cases)
        results[name].update(passed=len(cases)-len(skipped)-failed, failed=failed, skipped=skipped)
        if any(not s['reason'].startswith('POSIX descriptor fault injection;') for s in skipped):
            results[name]['native_incomplete'] = True
        native = [c for c in cases if c.get('name').startswith('test_native_')]
        if name == 'windows-reader' and (len(native) != 12 or any(len(c) > 0 for c in native)):
            results[name]['native_incomplete'] = True
    # Native provisioning cases are real PowerShell transactions, represented
    # in JUnit alongside pytest. Missing case or interrupted rehearsal fails.
    rehearsal_path = evidence / 'powershell-rehearsal.json'
    rehearsal = json.loads(rehearsal_path.read_text(encoding='utf-8-sig')) if rehearsal_path.exists() else {}
    suite = ET.Element('testsuite', name='pythoncore-provision', tests='4')
    failures = 0
    for name in ('pythoncore_standard_token', 'pythoncore_archive_negatives',
                 'pythoncore_provision_rollback', 'pythoncore_runtime'):
        case = ET.SubElement(suite, 'testcase', classname='native.pythoncore', name=name)
        result = rehearsal.get(name, 'MISSING_NATIVE_EVIDENCE')
        if not result.startswith('PASS:'):
            failures += 1
            ET.SubElement(case, 'failure', message=result)
        ET.SubElement(case, 'system-out').text = result
    suite.set('failures', str(failures))
    ET.ElementTree(suite).write(evidence / 'pythoncore-provision.xml', encoding='utf-8', xml_declaration=True)
    results['pythoncore-provision'] = dict(exit_code=int(bool(failures)), passed=4-failures, failed=failures)
    (evidence / 'results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(json.dumps(results, indent=2), flush=True)
    failed = any(r['exit_code'] or r.get('native_incomplete') or r.get('missing_junit') for r in results.values())
    acceptance = dict(classification='CC03_WINDOWS_NATIVE_NEEDS_FIX' if failed else 'CC03_OS_READONLY_OBSERVER_PARTIAL',
                      legacy_live_source='CC03_LIVE_SOURCE_COMPATIBILITY_BLOCKED',
                      original_legacy_replace_requirements='NOT_PASSED: conflicts reproduced, not fixed',
                      native_transport_and_deployment='NEEDS_FIX' if failed else 'PASS',
                      windows_os_observer='NEEDS_FIX' if failed else 'PASS: OS facts only; physical source binding not executed',
                      manual_os_source='NEEDS_FIX' if failed else 'PASS: manual one-shot; session-local; source/account UNVERIFIED',
                      metadata_source='CC03_METADATA_COMPATIBILITY_BLOCKED: expected-conflict regression is not noninterference acceptance',
                      runtime_retention='DISABLED: bounded stop, no deletion',
                      intel_readonly_preflight='NEEDS_FIX' if failed else 'PASS: disposable hosted sources only',
                      physical='NOT_EXECUTED')
    # Package the exact tested Git tree, excluding environments/caches/private
    # runtime policies by construction. Companion checksums are outside the ZIP,
    # so final PR head and ZIP/manifest hashes need no self-reference.
    if not failed:
        checksums = dict(schema_id='cc03.intel-preflight-package-checksums.v1',
            classification='CC03_INTEL_READONLY_PREFLIGHT_PACKAGE_READY',
            pr_base_sha=metadata['pr_base_sha'], pr_head_sha=metadata['pr_head_sha'],
            tested_checkout_sha=metadata['tested_sha'], controlcenter_tree=metadata['controlcenter_tree'],
            run_id=metadata['run_id'], intel_execution='NOT_EXECUTED', physical='NOT_VERIFIED',
            archive_manifest_files_verified=bundle_file_count,
            files=[dict(path=bundle.name, sha256=sha256(bundle.read_bytes()).hexdigest()),
                   dict(path='ControlCenter/deployment/manifest.json',
                        sha256=sha256(Path('deployment/manifest.json').read_bytes()).hexdigest())])
        (evidence / 'CC03_INTEL_PREFLIGHT_CHECKSUMS.json').write_text(
            json.dumps(checksums, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(checksums, indent=2), flush=True)
    (evidence / 'acceptance.json').write_text(json.dumps(acceptance, indent=2), encoding='utf-8')
    inventory = [dict(path=p.relative_to(evidence).as_posix(), sha256=sha256(p.read_bytes()).hexdigest(), size=p.stat().st_size)
                 for p in sorted(evidence.rglob('*')) if p.is_file() and p.name != 'ARTIFACT_SHA256.json']
    (evidence / 'ARTIFACT_SHA256.json').write_text(json.dumps(inventory, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(acceptance, indent=2), flush=True)
    with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as summary:
        summary.write('\n' + acceptance['classification'] + '\n\nLegacy H1 continuous monitoring remains disabled. '
                      'Expected-conflict regressions do not satisfy legacy live producer compatibility. '
                      'Hosted CI is not physical Intel acceptance.\n')
    return int(failed)


if __name__ == '__main__':
    raise SystemExit(main())
