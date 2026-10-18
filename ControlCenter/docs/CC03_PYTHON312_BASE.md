# CC-03 B — official PythonCore ZIP, full isolated base

Authority: [roadmap #524 task](https://github.com/alkospacer123/market-pattern-discovery/issues/524#issuecomment-6253566301),
main `86279fe366b188dc8d2c1d63b832b429f0c0775e`. Code-only Draft PR.
Intel A = NOT_VERIFIED; B installation = NOT_EXECUTED; C = NOT_ACTIVATED.
Hosted CI cannot grant physical B approval. No merge or Intel execution here.

## One accepted distribution

[PSF index](https://www.python.org/ftp/python/3.12.10/windows-3.12.10.json)
identifies `pythoncore-3.12-64`, version `3.12.10`, separately from PythonEmbed.
The [official directory](https://www.python.org/ftp/python/3.12.10/) lists the
32,399,361-byte complete archive:
`https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.zip`.
SHA-256: `8649692de846c56a7189d6dae5c322ab20deb1b5908b6f39426b62a36f39415d`.
These exact bytes, with 3845 regular files, are the only B distribution.
Embeddable, other versions/architectures, `py.exe`, registry/PATH discovery,
profile Python and copied setup-python trees cannot satisfy provenance v2.

Fixed active paths under `C:\Control Center\runtime`:

- `python312\python.exe`: full CPython 3.12.10 amd64.
- `python-3.12.10-amd64.zip`: retained actual source bytes.
- `python-3.12.10-amd64.exe`: retained signed **supporting media** only.
- `python312.provenance.json`: protected, independently approved B handoff.

The extracted base is **not installed from EXE**. The EXE signature does not
authenticate ZIP bytes. No EXE/MSI, system Python, launcher, registration or
installer `/layout` command is executed by this implementation.

## Protected provenance v2

The v1 EXE-source schema is rejected. The generated v2 record contains:

```json
{
  "schema_id": "cc03.python-base.v2",
  "b_only_approved": true,
  "release": "CPython-3.12.10-amd64-full",
  "distribution_id": "pythoncore-3.12-64",
  "control_center_root": "C:\\Control Center",
  "panel_sid": "<existing independently checked ccpanel SID>",
  "source_uri": "https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.zip",
  "archive_sha256": "8649692de846c56a7189d6dae5c322ab20deb1b5908b6f39426b62a36f39415d",
  "archive_size": 32399361,
  "review_reference": "<independent B review reference>",
  "supporting_media": {
    "source_uri": "https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe",
    "sha256": "<independently reviewed supporting EXE hash>"
  },
  "files": [{"path": "python.exe", "sha256": "<actual ZIP entry hash>", "size": 0}]
}
```

This is a schema illustration, not an active approval. `files` must contain all
3845 actual entries with real sizes and hashes. Reader independently reopens the
retained ZIP, checks the compiled-in SHA/size, validates every entry, compares its
inventory with provenance and then hashes the entire runtime tree before Python
execution. Supporting EXE hash and valid PSF organizational Authenticode signature
are checked separately. `-I -B` verifies exact executable, `_base_executable`,
`base_prefix`, `prefix`, version/x64 and encodings/ssl/venv/ensurepip/pip origins.
Start and Verify revalidate these boundaries and exact venv binding.
Provenance is bound to the exact CC root and panel SID. Hosted CI records name
their disposable root/SID and cannot serve as physical Intel approval. Within one
script invocation only ZIP entry inventory may be reused after rechecking full
archive size/SHA on every call; callers receive copies. Runtime tree/ACL checks
are never cached.
Each bounded validation operation checks live ccpanel account/group state once
before its path-only ACL checks; standalone `Assert-ACL` also checks it. Account
state is never cached between operations. Every path/owner/ACE is still checked.

Existing standard, enabled `ccpanel` SID is required. Control Center/runtime/base/
provenance and intermediate ancestors retain protected admin/SYSTEM ownership
and DACLs. Only SYSTEM/Administrators and ccpanel RX/Synchronize are accepted;
ccpanel cannot write/delete/change permissions. Every child owner/ACE and reparse
state is checked. Drive-root mutation rights fail closed. Data/private remains
admin-only. No account creation/enabling, old staging ACL repair or system/H1 ACL
repair is part of provisioning.

## Offline B provisioning contract

`deployment/Provision-PythonCore.ps1` defaults to PREVIEW with no reads of media,
approval or targets and no writes. Execution is separate from Install/Start/Verify.
It requires elevated B administrator, explicit `-Execute -SealFreshCCFiles`, existing
CC roots and ACL contract, empty runtime/app/venv, validated package manifest and
an independently installed admin-only approval at
`data\private\pythoncore-b-approval.json`. No approval is shipped active.

Approval schema `cc03.pythoncore-b-approval.v1` requires `b_execution_approved=true`,
`seal_fresh_cc_files_approved=true`, exact `panel_sid`, `archive_sha256` (the pinned
ZIP), `supporting_media_sha256`, `package_manifest_sha256` and nonempty
`review_reference`. An authorized reviewer must authenticate those values before
placing the private file. Do not create it merely by measuring unreviewed inputs.

Both input media must already exist within CC, under protected plain ancestors,
with trusted ownership and no ccpanel write. Source handles deny write/delete for
the transaction. All source verification precedes target writes. Archive entries
reject traversal/absolute/drive/UNC/backslash/ADS/wildcards, duplicate or case
collisions including ancestors, file/directory conflicts, reserved NTFS names,
trailing dot/space, symlink/reparse/special files and oversized entries. Extraction
uses CreateNew only; every output is rehashed against the authenticated offline
ZIP inventory. There is no network or Python execution in provisioning.

The distinct `Protect-FreshCCFiles` sealing step requires both the switch and
private approval. It sets trusted owner and seals only transaction-created CC
paths; it never changes existing roots/ancestors/input media. Failed preconditions
make zero target writes. Transaction failure prevalidates all tracked paths for
reparse state and removes only those exact fresh files and empty directories,
without recursive deletion. Unexpected objects cause STOP. Existing CC roots,
review input, private approval, prior 98/103 packages and other staging survive.
Runtime is retained by the panel's Install rollback and Uninstall.

Panel Install remains separate: exact full 40-wheel `requirements-windows.lock`,
offline hash/metadata/platform/dependency closure, isolated pip with no network
fallback. It scrubs PIP/PYTHON/launcher environment and fixes TEMP/TMP/TMPDIR and
CWD inside its own initially empty roots, restoring the caller afterward.

## Native evidence and operator handoff

Existing unchanged Windows Server 2022 workflow runs `ci/PythonCore-Tests.ps1`
through the production provisioner, downloads the official index/ZIP/supporting
EXE only on disposable hosted Windows, and exercises real full ZIP runtime and
standard ccpanel access. CI-only users/ACL/Task fixtures are never Intel users or
Tasks. Previous suites, ETW/PID/counters and 500 os.replace regressions remain.
Negatives cover ZIP corruption/names/links, approval/signature/provenance,
missing/injected files, privileges/ACL and two provisioning rollback faults.
JUnit, provenance inventory, index, Git blobs and artifact hashes accompany results.

Only after native tests PASS and independent audit may exact reviewed package
hashes and staging commands be issued in the final handoff. No Intel execution
command is authorized here. Safe default preview (lowercase single-line):

```powershell
powershell.exe -noprofile -file 'c:\control center\deployment\provision-pythoncore.ps1'
```

Physical B still requires a separate operator decision, standard ccpanel effective
access (including private denial), full offline runtime and wheel closure,
and CC-only ACL acceptance. Physical A binding and C source activation remain
separate. HALTED/fill/trading gates are unchanged.
