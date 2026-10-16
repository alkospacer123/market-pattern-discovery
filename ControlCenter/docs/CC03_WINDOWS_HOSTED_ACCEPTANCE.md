# CC-03: GitHub-hosted Windows native acceptance

**CC03_WINDOWS_HOSTED_NATIVE_NEEDS_FIX.** Windows инфраструктура доступна; приёмка заблокирована дефектом reader/atomic producer.

Один [Draft PR #534](https://github.com/alkospacer123/market-pattern-discovery/pull/534), ветка `codex/controlcenter-cc03-windows-native`. NO MERGE / NO AUTO-MERGE / NO INTEL / NO TRADING. Новая фаза roadmap не создавалась.

## Основное Windows evidence

- Run ID: [38862012808](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/38862012808); actual job log прочитан и сохранён.
- Проверенный synthetic merge SHA: `797b1d30c2692f5eca429689b74f588410d0d968`.
- PR head SHA: `0b7fd2b6a67345bed047036868b14af72d96dc48`; base SHA: `cb7e1cc32694fb97fba3c7f9200f9a492d8eebea`.
- Проверенный ControlCenter tree: `9dcc5752a7f994c2dfea6c585eedea62f0151803`.
- GitHub-hosted `windows-2022`, Windows Server 2022 Datacenter 10.0.20348 (build 20348), local fixed NTFS.
- Python: `3.12.10 (tags/v3.12.10:0cc8128, Apr  8 2025, 12:21:36) [MSC v.1943 64 bit (AMD64)]`; разрядность **64**. pytest 8.4.2.

| Проверка | PASS | FAIL | SKIP |
| --- | ---: | ---: | ---: |
| tests/test_windows_reader.py | 42 | 2 | 0 |
| tests/test_cc03_source.py | 27 | 0 | 0 |
| Полный python -m pytest -q | 323 | 2 | 15 |

`deployment/manifest.py --check`: **PASS**; `python -m pip check`: **PASS**. Все Windows-native skips отсутствуют; 15 skips — только документированные POSIX injections.

## Все 12 ранее пропущенных native scenarios

| Реальный Windows test | Результат |
| --- | --- |
| `test_native_read_and_hardlink` | PASSED |
| `test_native_symlink[False]` | PASSED |
| `test_native_symlink[True]` | PASSED |
| `test_native_junction_reparse` | PASSED |
| `test_native_inplace_write_denied_atomic_replace_allowed` | FAILED |
| `test_native_api_missing` | PASSED |
| `test_native_missing_oversize_and_directory` | PASSED |
| `test_native_existing_writer_and_pinned_directory` | PASSED |
| `test_native_insufficient_file_acl` | PASSED |
| `test_native_atomic_producer_is_unblocked_and_receiver_rejects_change` | FAILED |
| `test_native_policy_with_untrusted_write_acl_is_rejected` | PASSED |
| `test_native_admin_owned_policy_accepts_then_rejects_weak_ace` | PASSED |

**10 PASS / 2 FAIL / 0 native SKIP.** Win32 reader не принят: обе ошибки относятся к atomic replacement, а не к отсутствию Windows API.

Существующий `os.replace` producer получает WinError 5 при открытом leaf handle. Реальная диагностика девяти access/share combinations дала отказ во всех случаях; после закрытия observer handle replacement проходит. WRITE-sharing дополнительно допускает in-place write и не применялся как исправление. Изменять защищённый H1 producer или менять FAIL на SKIP нельзя. Нужен отдельно доказанный совместимый read protocol в рамках CC-03.

Microsoft документирует [FILE_RENAME_POSIX_SEMANTICS](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/ns-ntifs-_file_rename_information) для replacement при открытых handles; reader не может изменить семантику внешнего producer.

## PowerShell и реальные ACL

Windows PowerShell 5.1: восемь deployment files прошли синтаксический parser; все семь entrypoints прошли безопасный preview: Preflight, Install, Verify, Start-Panel, Start-Exporter, Uninstall, Probe-H1Task. Probe-H1Task -Execute не запускался.

| Runtime проверка | Фактический результат |
| --- | --- |
| Два SID / effective ACL | PASS: 10 actual access probes under two distinct non-admin logon tokens |
| Bad wheel hash regression | PASS: bad hash rejected before any target write |
| Offline Install | PASS: real offline install into disposable ACL-provisioned roots |
| Panel + Verify под отдельным SID | NOT_VERIFIED: dependent startup gate not completed |
| Exporter под отдельным SID / unapproved policy | NOT_VERIFIED: dependent startup gate not completed |
| Uninstall / data retention | PASS: own package/venv removed after failed launch; data retained |

Итог rehearsal: **FAIL**. Preflight реально выполнен до install. Установленный venv отдельно подтвердил Python 3.12.10 x64. ACL применялись только к собственному disposable `RUNNER_TEMP/CC03-<guid>`. Два новых standard users удаляются в finally; чужие и production ACL не изменялись.

Не завершённые пункты не засчитываются как PASS:

```json
{
  "panel_child_exit": "RUNNING_WITHOUT_LISTENER",
  "panel_log_present": false,
  "status": "FAIL",
  "error": "DISPOSABLE_PANEL_DID_NOT_BIND_LOOPBACK"
}
```

LogonUser и 10 actual file-access probes под двумя SID работают. SeImpersonatePrivilege у runner включена. Отсутствие конкретного Windows права не доказано; ошибки startup не объявляются ошибками permissions. Непроверенные Start-Panel / Verify / Start-Exporter под отдельными SID остаются NOT_VERIFIED. Execution policy, desktop ACL и системные privileges не ослаблялись.

Пароль temporary users остаётся в памяти: его нет в process command line, bootstrap или artifacts. Logon command ограничен 1024 chars; [это лимит Windows API](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-createprocesswithtokenw). Bootstrap хранит только CI paths/context и защищён ACL. Код панели/exporter продолжает проверять dedicated identity и прежнюю ACL-матрицу.

## Исправления, подтверждённые Windows execution

- Directory metadata-only handle не удерживал каталог от rename: добавлен read-only FILE_LIST_DIRECTORY с запретом DELETE-sharing. WRITE-sharing каталога разрешает child publication; write access reader не запрашивает. Leaf security checks сохранены.
- Deny fixture запрещает FILE_READ_DATA, проверяет настоящий access-denied и затем восстанавливает свой ACE, сохраняя READ_CONTROL для cleanup.
- UTF-8 source audits используют явную кодировку; oversized binary case получил короткий pytest ID вместо превышения Windows environment limit.
- Manifest использует одинаковую case-sensitive сортировку package-relative POSIX spelling на Windows и Linux; checkout сохраняет LF.
- PowerShell 5.1 materializes wheel JSON array перед wrapping: все filename/hash/count checks сохранены. Bad-hash regression подтверждает отказ до записи в targets.
- Windows PowerShell получает собственный module path; CI-only roots согласованы для Python receiver/exporter и PowerShell. Все default test I/O также ограничены disposable roots.

## Полный список 15 skips

Единственная причина: `POSIX descriptor fault injection; native Windows equivalents in test_windows_reader.py`.

- `tests.test_h1_fault_injection.test_unsafe_files_and_ancestors_rejected[file_symlink]`
- `tests.test_h1_fault_injection.test_unsafe_files_and_ancestors_rejected[directory_symlink]`
- `tests.test_h1_fault_injection.test_unsafe_files_and_ancestors_rejected[ancestor_symlink]`
- `tests.test_h1_fault_injection.test_unsafe_files_and_ancestors_rejected[hardlink]`
- `tests.test_h1_fault_injection.test_unsafe_files_and_ancestors_rejected[fifo]`
- `tests.test_h1_fault_injection.test_unsafe_files_and_ancestors_rejected[directory]`
- `tests.test_h1_fault_injection.test_partial_write_and_path_races_fail_closed[replace]`
- `tests.test_h1_fault_injection.test_partial_write_and_path_races_fail_closed[truncate]`
- `tests.test_h1_fault_injection.test_partial_write_and_path_races_fail_closed[grow]`
- `tests.test_h1_fault_injection.test_partial_write_and_path_races_fail_closed[rewrite]`
- `tests.test_h1_fault_injection.test_partial_write_and_path_races_fail_closed[symlink]`
- `tests.test_h1_fault_injection.test_partial_write_and_path_races_fail_closed[root_replace]`
- `tests.test_h1_fault_injection.test_partial_write_and_path_races_fail_closed[root_symlink]`
- `tests.test_h1_fault_injection.test_no_secure_platform_primitive_fails_closed`
- `tests.test_h1_fault_injection.test_read_uses_no_write_capability_or_external_systems`

## Actions / воспроизводимость / scope

Один workflow `.github/workflows/controlcenter-cc03-windows-native.yml`: pull_request с двумя path filters, runs-on windows-2022, contents: read, timeout 15 минут, sparse checkout только /ControlCenter/, persist-credentials: false. Нет pull_request_target, self-hosted/larger labels, privileged GitHub token permissions, repository secrets, FINAM tokens, production environment variables или remote sessions. Python 3.12.10 x64, все 44 Windows wheels закреплены versions/SHA256, actions — commit SHA. Freeze и JUnit сохраняются в artifacts на 30 дней.

Administrative Actions permissions / selected-actions GET вернули 403; hosted-runner management endpoint — 404. Чтение этих настроек полностью недоступно текущей integration. Registry перечислил пять legacy active workflows; файлов других workflows в pinned main нет. Реальное выделение windows-2022 VM и execution подтверждены job logs; settings не изменялись.

Начальный main `1c8b0c702fa73bc99e0a6593dc7dc2fa072eb6cb` и merge #533 проверены. Единственная ветка актуализирована на `cb7e1cc32694fb97fba3c7f9200f9a492d8eebea` после upstream #535–#538. Их operational Markdown / diagnostics package не принадлежат diff этого PR и не исполняются данным CI.

| Protected tree | Pinned base = PR head |
| --- | --- |
| TradingSystemLab | `d27ac7153a4d25455112c1a6673d2b37a1784f43` |
| IntradayLab | `c4f6e652ba442a575ad5711cb3f55841f860f484` |

Protected diff пуст. Единственное разрешённое изменение вне ControlCenter — новый workflow. TradingSystemLab / IntradayLab, стратегии, identity, production configurations, SQLite, Task, kill switch, authorization и FINAM logic этой веткой не менялись.

## История настоящих Windows runs

| Run | Raw full pytest summary | Manifest |
| --- | --- | --- |
| [38805454778](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/38805454778) | 6 failed, 306 passed, 15 skipped, 2 errors | FAIL |
| [38806311854](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/38806311854) | 2 failed, 323 passed, 15 skipped | FAIL |
| [38858099772](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/38858099772) | NOT_EXECUTED: wrapper failed before commands | NOT_EXECUTED |
| [38858276737](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/38858276737) | 2 failed, 323 passed, 15 skipped | PASS |
| [38858709525](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/38858709525) | 2 failed, 323 passed, 15 skipped | PASS |
| [38859180303](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/38859180303) | 2 failed, 323 passed, 15 skipped | PASS |
| [38859974112](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/38859974112) | 2 failed, 323 passed, 15 skipped | PASS |
| [38860731461](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/38860731461) | 2 failed, 323 passed, 15 skipped | PASS |
| [38861276003](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/38861276003) | 2 failed, 323 passed, 15 skipped | PASS |
| [38862012808](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/38862012808) | 2 failed, 323 passed, 15 skipped | PASS |

Каждый completed native run имеет actual environment metadata, command logs, JUnit и skip list. Wrapper-only run не засчитывается как Windows acceptance. Raw job logs сохранены отдельно; последняя проверка документального commit и её точные SHA/run URL указаны в Draft PR checks/body.

## Intel physical gate

**CC03_PHYSICAL_PASS не установлен; CC-03 Intel physical NOT_EXECUTED.** GitHub main не является измерением установленного робота. Отдельно остаются:

- реальные Windows identities и ACL сервера;
- реальный источник H1 heartbeat / kill switch;
- account binding;
- утверждённые TTL;
- физические before/after checks;
- отдельное разрешение оператора на установку.

Ни Control Center, ни exporter на Intel не устанавливались и не запускались. Merge / Auto-Merge не выполнялись. Оба native FAIL сохраняются открытыми; физический rollout заблокирован. STOP, без CC-04.
