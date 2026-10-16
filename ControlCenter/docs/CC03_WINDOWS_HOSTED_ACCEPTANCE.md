# CC-03: GitHub-hosted Windows native acceptance

**CC03_WINDOWS_HOSTED_NATIVE_NEEDS_FIX — промежуточное evidence, не Windows PASS.**
Draft PR [#534](https://github.com/alkospacer123/market-pattern-discovery/pull/534),
ветка `codex/controlcenter-cc03-windows-native`, от main
`1c8b0c702fa73bc99e0a6593dc7dc2fa072eb6cb` (merge #533 подтверждён).
Новой фазы roadmap нет. NO MERGE / NO AUTO-MERGE / NO INTEL / NO TRADING.

## Фактическое выполнение

Standard GitHub-hosted `windows-2022`, Windows Server 2022 Datacenter
10.0.20348, NTFS, CPython 3.12.10 x64, pytest 8.4.2.
Точные Windows/Python metadata, freeze, JUnit и логи команд сохранены в artifact каждого run.

| Run | Head SHA | Полный pytest | Manifest | PowerShell |
| --- | --- | --- | --- | --- |
| [38805454778](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/38805454778) | `f00eda14e64bc8afcf0264660909a2964d455387` | 306 PASS / 6 FAIL / 15 SKIP / 2 ERROR | FAIL | 8 syntax / 7 preview PASS |
| [38806311854](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/38806311854) | `936ef83ca8712e48c108b8193916cf3eb8f4ef1e` | 323 PASS / 2 FAIL / 15 SKIP | FAIL | 8 syntax / 7 preview PASS; rehearsal FAIL из-за наследованного PS7 module path |
| [38858099772](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/38858099772) | `fd572ab34157f3c31bf5aa39b2b37cad07586cda` | NOT_EXECUTED: CI wrapper KeyError перед первой командой | NOT_EXECUTED | NOT_EXECUTED |
| [38858276737](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/38858276737) | `a01764e7e6d3d9a576326b1d2b698c61e7dbd28a` | 323 PASS / 2 FAIL / 15 SKIP | PASS | 10 separate-SID probes PASS; Install FAIL |
| [38858709525](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/38858709525) | `dae9fded9d2f97a2ef8c086db97549b0c5aa657f` | 323 PASS / 2 FAIL / 15 SKIP | PASS | Install.ps1:19 — JSON array nested by PowerShell 5.1 |

Actions проверяет synthetic PR merge commit. Фактически tested SHA первых
двух runs: `c6b5918f9d3834d4483f2203514c5d1930356b54` и
`7264c6f40d8de48072c43b738db7093ff79366da` соответственно.
Третий checkout SHA — `ea15f27ea3bbf7efe995f86baef838a32b57db2e`, но тесты
не начались, поэтому он не считается native acceptance.
Tested merge SHA runs 38858276737 / 38858709525:
`f0c610ce2e01348fa5ca2814c054d53e7eadb5a3` /
`d3a76838887796b812ffa76fa5edb265aac120cf`.

Во время продолжения работы main продвинулся до
`0aae41d9c02f67e3cd6539a2cb610174fc270e01` через upstream #535/#536:
только пять operational Markdown / 72 добавленные строки TradingSystemLab.
Затем upstream #537/#538 добавили независимый diagnostics package и operational
Markdown. Ветка rebased на pinned base `cb7e1cc32694fb97fba3c7f9200f9a492d8eebea`;
собственных protected changes нет. Эти upstream scripts не исполняются CI.
Protected base/head: TradingSystemLab `d27ac7153a4d25455112c1a6673d2b37a1784f43`,
IntradayLab `c4f6e652ba442a575ad5711cb3f55841f860f484`.

Во втором run: reader suite 42 PASS / 2 FAIL / 0 SKIP; source suite
27 PASS / 0 FAIL / 0 SKIP; все 12 ранее skipped native сценариев реально
выполнены — 10 PASS / 2 FAIL. Обе ошибки — atomic producer replacement.
Pip check PASS в обоих runs. Windows-native SKIP отсутствуют.

Portable manifest, Windows PowerShell 5.1 module path и directory pin уже
проверены на Windows. Все 10 effective-access probes под двумя отдельными
непривилегированными SID прошли. Install выявил PowerShell 5.1 JSON array
enumeration bug; исправлен с сохранением wheel name/hash/count checks.
Следующий run проверяет полный installer rehearsal после этого исправления.

| Из 12 native cases | Результат |
| --- | --- |
| read + hardlink | PASS |
| file symlink | PASS |
| directory symlink | PASS |
| junction/reparse | PASS |
| inplace writer denial + atomic replacement | **FAIL: replacement** |
| missing safe API | PASS |
| missing/oversize/directory leaf | PASS |
| existing writer + pinned directory | PASS |
| insufficient read-data ACL | PASS |
| concurrent atomic producer while reader holds handles | **FAIL: replacement** |
| untrusted policy write ACE | PASS |
| positive admin-owned policy then weak ACE rejection | PASS |

## Открытый блокирующий дефект

`test_native_inplace_write_denied_atomic_replace_allowed` и
`test_native_atomic_producer_is_unblocked_and_receiver_rejects_change`
остаются FAIL. На Windows существующий `os.replace` не может заменить
целевой файл, пока observer держит его открытым. `FILE_SHARE_DELETE` этого
не устраняет. Второй run также проверил девять combinations: GENERIC_READ,
FILE_READ_DATA или metadata-only access × READ / READ+DELETE / READ+WRITE+DELETE
sharing — replacement отвергнут во всех девяти. WRITE-sharing дополнительно
допускает in-place writer и не является безопасным исправлением.

Microsoft документирует отдельный
[FILE_RENAME_POSIX_SEMANTICS](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/ns-ntifs-_file_rename_information)
для replacement при открытых handles. Reader не может изменить semantics
внешнего producer. Защищённый H1 producer в этой работе не менялся.
Обычный небезопасный read, ослабление share/ACL checks и FAIL→SKIP не применялись.
Без доказанного совместимого read protocol приёмка и rollout заблокированы.

## Исправления по Windows evidence

- Metadata-only directory handle заменён на read-only LIST_DIRECTORY handle:
  реальный directory rename теперь отвергается. WRITE-sharing относится к
  каталогу и разрешает child publication; DELETE-sharing по-прежнему запрещён.
- Deny ACL fixture запрещает FILE_READ_DATA и проверяет реальный access-denied;
  READ_CONTROL сохранён для снятия собственного тестового ACE.
- UTF-8 source audits используют явную кодировку; большой binary pytest case
  получил короткий ID, чтобы Windows PYTEST_CURRENT_TEST не превысил 32767 chars.
- Manifest сортирует package-relative POSIX spelling независимо от OS.
- PowerShell 5.1 materializes JSON wheel records до array wrapping; multi-wheel
  manifest больше не передаёт массив имён в Join-Path.
- Все Windows dependencies закреплены версиями и SHA256; bootstrap actions
  закреплены commit SHA, Python — точным patch release и x64.
- CI-only root override проверяет hosted context и confinement в одноразовый
  `RUNNER_TEMP/CC03-<guid>`; Python exporter/receiver и PowerShell согласованы.
  Без override используются прежние defaults; security validators сохранены.

## Skips и дальнейшие gates

Все 15 skips — `POSIX descriptor fault injection; native Windows equivalents in test_windows_reader.py`:

- `test_unsafe_files_and_ancestors_rejected`: file_symlink, directory_symlink,
  ancestor_symlink, hardlink, fifo, directory (6).
- `test_partial_write_and_path_races_fail_closed`: replace, truncate, grow,
  rewrite, symlink, root_replace, root_symlink (7).
- `test_no_secure_platform_primitive_fails_closed` (1).
- `test_read_uses_no_write_capability_or_external_systems` (1).

Administrative Actions settings и selected-actions GET дали 403, hosted-runner
management endpoint — 404. Они не интерпретируются как полные настройки.
Реальные jobs подтверждают доступность стандартного `windows-2022`; self-hosted
или larger runners, secrets, FINAM/production variables и remote sessions не используются.

Protected tree IDs pinned-base/head совпадают:
`TradingSystemLab=d27ac7153a4d25455112c1a6673d2b37a1784f43`;
`IntradayLab=c4f6e652ba442a575ad5711cb3f55841f860f484`.
Исходный TradingSystemLab tree `be882bd0aa9cf5e7c210c2bf2a4928615e298eab`
изменён только upstream #535–#538, не diff этой ветки.

Intel physical NOT_EXECUTED. Отдельно остаются реальные identities/ACL сервера,
H1 heartbeat/kill-switch source, account binding, утверждённые TTL,
физические before/after checks и разрешение оператора на установку.
Даже будущий hosted PASS не будет CC03_PHYSICAL_PASS.
