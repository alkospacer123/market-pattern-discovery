"""Run only on the disposable GitHub-hosted Windows VM; preserve exact evidence."""
import json
import os
from pathlib import Path
import platform
import struct
import subprocess
import sys
import xml.etree.ElementTree as ET


def main():
    assert os.name == 'nt' and os.environ.get('RUNNER_ENVIRONMENT') == 'github-hosted'
    assert sys.version_info[:3] == (3, 12, 10) and struct.calcsize('P') == 8
    evidence = Path(os.environ['RUNNER_TEMP']) / 'cc03-evidence'
    evidence.mkdir(exist_ok=True)
    metadata = dict(windows=platform.platform(), windows_version=platform.win32_ver(),
                    python=sys.version, bits=struct.calcsize('P') * 8,
                    tested_sha=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
                    event_sha=os.environ['GITHUB_SHA'], run_id=os.environ['GITHUB_RUN_ID'])
    print(json.dumps(metadata, indent=2), flush=True)
    (evidence / 'environment.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    commands = [
        ('host', ['powershell', '-NoProfile', '-Command',
                  "Get-CimInstance Win32_OperatingSystem | Select Caption,Version,BuildNumber | Format-List; "
                  "Get-Volume | Where DriveLetter -in @((Get-Item .).PSDrive.Name, (Get-Item $env:RUNNER_TEMP).PSDrive.Name) | Select DriveLetter,FileSystem | Format-Table; whoami /user; whoami /priv"]),
        ('windows-reader', [sys.executable, '-m', 'pytest', '-v', '-ra', 'tests/test_windows_reader.py',
                            f'--junitxml={evidence / "windows-reader.xml"}']),
        ('cc03-source', [sys.executable, '-m', 'pytest', '-q', 'tests/test_cc03_source.py',
                         f'--junitxml={evidence / "cc03-source.xml"}']),
        ('full-suite', [sys.executable, '-m', 'pytest', '-q',
                        f'--junitxml={evidence / "full-suite.xml"}']),
        ('manifest', [sys.executable, 'deployment/manifest.py', '--check']),
        ('pip-check', [sys.executable, '-m', 'pip', 'check']),
        ('pip-freeze', [sys.executable, '-m', 'pip', 'freeze', '--all']),
        ('native-share-diagnostic', [sys.executable, '-m', 'ci.windows_share_probe']),
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
        try:
            completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       encoding='utf-8', errors='replace', timeout=360)
            output, exit_code = completed.stdout, completed.returncode
        except subprocess.TimeoutExpired as exc:
            output = (exc.stdout or b'').decode('utf-8', errors='replace') + '\nACCEPTANCE_COMMAND_TIMEOUT'
            exit_code = 124
        print(output, flush=True)
        (evidence / f'{name}.log').write_text(output, encoding='utf-8')
        results[name] = dict(exit_code=exit_code)
    for name in ('windows-reader', 'cc03-source', 'full-suite'):
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
