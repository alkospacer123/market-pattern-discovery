"""Run only on the disposable GitHub-hosted Windows VM; preserve exact evidence."""
import json
import os
from pathlib import Path
import platform
import struct
import subprocess
import sys
import uuid
import xml.etree.ElementTree as ET


def main():
    assert os.name == 'nt' and os.environ.get('RUNNER_ENVIRONMENT') == 'github-hosted'
    assert sys.version_info[:3] == (3, 12, 10) and struct.calcsize('P') == 8
    # Even absence/UI tests must resolve default receiver/exporter I/O to a
    # disposable path, never the installed machine's conventional CC roots.
    sandbox = Path(os.environ['RUNNER_TEMP']) / ('CC03-' + uuid.uuid4().hex)
    sandbox.mkdir()
    os.environ['CC03_CI_DISPOSABLE_ROOT'] = str(sandbox)
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
    commands = [
        ('host', ['powershell', '-NoProfile', '-Command',
                  "Get-CimInstance Win32_OperatingSystem | Select Caption,Version,BuildNumber | Format-List; "
                  "Get-Volume | Where DriveLetter -in @((Get-Item .).PSDrive.Name, (Get-Item $env:RUNNER_TEMP).PSDrive.Name) | Select DriveLetter,FileSystem | Format-Table; whoami /user; whoami /priv"]),
        ('windows-reader', [sys.executable, '-m', 'pytest', '-v', '-ra', 'tests/test_windows_reader.py',
                            f'--junitxml={evidence / "windows-reader.xml"}']),
        ('windows-transport', [sys.executable, '-m', 'pytest', '-v', '-ra', 'tests/test_windows_transport.py',
                                f'--junitxml={evidence / "windows-transport.xml"}']),
        ('cc03-source', [sys.executable, '-m', 'pytest', '-q', 'tests/test_cc03_source.py',
                         f'--junitxml={evidence / "cc03-source.xml"}']),
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
                                       encoding='utf-8', errors='replace', timeout=360, env=environment)
            output, exit_code = completed.stdout, completed.returncode
        except subprocess.TimeoutExpired as exc:
            output = (exc.stdout or b'').decode('utf-8', errors='replace') + '\nACCEPTANCE_COMMAND_TIMEOUT'
            exit_code = 124
        print(output, flush=True)
        (evidence / f'{name}.log').write_text(output, encoding='utf-8')
        results[name] = dict(exit_code=exit_code)
    for name in ('windows-reader', 'windows-transport', 'cc03-source', 'full-suite'):
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
    (evidence / 'results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(json.dumps(results, indent=2), flush=True)
    return int(any(r['exit_code'] or r.get('native_incomplete') or r.get('missing_junit') for r in results.values()))


if __name__ == '__main__':
    raise SystemExit(main())
