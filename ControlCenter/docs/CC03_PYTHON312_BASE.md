# CC-03 B — независимая полная база Python 3.12

Основание: [ТЗ #524](https://github.com/alkospacer123/market-pattern-discovery/issues/524#issuecomment-6251496487).
Только code-only Draft PR. Intel A = NOT_VERIFIED; B/C = NOT_AUTHORIZED / NOT_EXECUTED.
Ни merge, ни физические изменения этим документом не разрешаются.

## Фиксированный layout и доверие

Единственная панельная identity — уже существующий **standard ccpanel** с отдельно
проверенным effective token. ccobserver/ccexporter не используются. Disabled ccpanel
блокирует B; код не создаёт/включает учётные записи и не исправляет ACL.

- `C:\Control Center\runtime\python312\python.exe` — единственный разрешённый
  полный CPython **3.12.10 amd64**; никакого `py.exe`, registry discovery, PATH или
  базы под Users, TradingSystemLab, IntradayLab. Embeddable ZIP запрещён: это не
  штатная база для venv/ensurepip/pip.
- `C:\Control Center\runtime\python-3.12.10-amd64.exe` — сохранённое OFFLINE media.
- `C:\Control Center\runtime\python312.provenance.json` — отдельная утверждённая
  B provenance, **не поставляется активной в release**.
- app/venv/data сохраняют прежние отдельные roots. `runtime` не входит в исходный
  manifest пакета и не удаляется rollback/uninstall панели.

Root Control Center, runtime, python312 и provenance должны быть admin/SYSTEM-owned,
с protected DACL: SYSTEM `S-1-5-18` и Administrators `S-1-5-32-544` FullControl;
только независимо проверенный ccpanel SID — ReadAndExecute/Synchronize. Дочерние
файлы могут наследовать эти grants, но каждый owner/ACE проверяется. Панель не
владеет кодом, базой, venv, не имеет write/delete/change-permissions. Data/private
остаётся admin-only. Drive root не должен позволять непривилегированной identity
удалять защищённые children или менять DACL/owner. Системные/H1 ACL не исправлять.

## Отдельная B-only подготовка OFFLINE media

Это описание будущей операции B, **не команда к выполнению сейчас**. На отдельной
доверенной provisioning-машине получить официальный полный Windows installer:
`https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe`.
Проверить валидную Authenticode подпись Python Software Foundation и независимо
зафиксировать SHA256 именно полученных bytes в review B. Подготовить полный offline
layout installer, включая все MSI/CAB для выбранных компонентов; зафиксировать их
SHA256 и provenance в B handoff. В чистом staging установить из этого media полный
CPython 3.12.10 x64 без launcher, PATH, associations, shortcuts и system-wide
installation; требуются Lib, DLLs, ssl, encodings, venv, ensurepip с bundled pip wheel,
а также рабочий pip. Переносимый **полный** runtime tree проверить в конечном exact
layout; отсутствие исходной provisioning-машины не должно менять imports/prefixes.
Не копировать чужую пользовательскую установку Intel и не читать профиль alkos.

После отдельного B approval администратор размещает media и runtime tree только в
указанных CC roots, проверяет каждый ancestor/reparse/owner/ACL и frozen file list.
Сам installer панели не загружает и не устанавливает базу. Не доверять одному
самовычисленному digest: reviewer B должен сопоставить release/media SHA256 и полный
runtime tree с полученным offline handoff. Из CI нельзя переносить approval на Intel.

Protected provenance JSON имеет обязательные поля:

```json
{
  "schema_id": "cc03.python-base.v1",
  "b_only_approved": true,
  "release": "CPython-3.12.10-amd64-full",
  "source_uri": "https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe",
  "media_sha256": "<64 lowercase hex: independently reviewed actual offline installer SHA256>",
  "files": [{"path": "python.exe", "sha256": "<actual SHA256>"}]
}
```

Это схема, не рабочая policy. `files` содержит **все** файлы базы, portable `/` paths,
без дублей и посторонних файлов; venv или `._pth` запрещены. Обязательны python.exe,
python312.dll, encodings, venv и ensurepip. Media SHA256 сверяется с сохранённым
installer, подпись проверяется до запуска Python. Все bytes базы сверяются до
первого запуска exact executable; затем `-I -B` проверяет версию/x64, executable,
base_executable/base_prefix/prefix и origins модулей. Изменение runtime требует
нового B review и нового provenance, не автоматической регенерации на Intel.

Wheelhouse готовится отдельно на доверенной машине под Windows CPython 3.12 x64
по `requirements-windows.lock` (`--require-hashes --only-binary=:all: --no-deps`).
`wheels.sha256.json` содержит уникальные `{name, sha256}` для всех `.whl`.
До install writes проверяются индекс, SHA256 из reviewed lock, platform tags и
полная dependency closure по METADATA без imports/extraction/network/temp writes.
Установка использует только offline wheelhouse, полный hash lock и isolated pip;
PIP_* и configs не могут перенаправить установку. На время venv/ensurepip/pip также
очищаются PYTHON* и __PYVENV_LAUNCHER__, запрещён user site/bytecode, а рабочий каталог
фиксируется на проверенном app: дочерний ensurepip не наследует родительский -I.
Scratch ограничен собственным venv. Окружение и CWD вызывающего восстанавливаются.
Нет сетевого fallback.

## Команды оператора — только PREVIEW

Однострочные lowercase PowerShell команды; ни одна не имеет `-execute`:

```powershell
powershell.exe -noprofile -file 'c:\control center\deployment\preflight.ps1'
powershell.exe -noprofile -file 'c:\control center\deployment\install.ps1'
powershell.exe -noprofile -file 'c:\control center\app\deployment\verify.ps1'
powershell.exe -noprofile -file 'c:\control center\app\deployment\start-panel.ps1'
```

Реальный B Preflight дополнительно потребует PanelSid и локальный Wheelhouse;
Install допускается только elevated администратору после отдельного B approval.
До записи требуются пустые app/venv, полный package manifest, enabled standard
ccpanel, trusted base/media и полный offline wheelhouse. Ошибка после начала
copy/venv/pip удаляет только содержимое первоначально пустых app/venv, сохраняя их
ACL, runtime и data. Обнаруженный reparse при rollback означает STOP без обхода
ссылки. Не удалять/ремонтировать чужие каталоги.

Start-Panel под реальным ccpanel и Verify заново проверяют provenance/base/tree ACL,
`venv\pyvenv.cfg` home/executable/version/system-site-packages и реальный runtime
со Streamlit/Plotly/pip. Следует отдельно подтвердить effective denial H1/private,
невозможность менять app/venv/base и loopback-only listener. Hosted rehearsal
доказывает это только на disposable fixtures, не на Intel.

## STOP

Любой missing/hash/version/architecture/signature/stdlib/venv/ensurepip/wheel failure,
профильная или другая неразрешённая база, junction/reparse, неизвестный owner/ACE,
ненадёжные ancestors, Disabled/привилегированный/непроверенный ccpanel, непустые
app/venv, mismatch pyvenv/runtime, ACCESS_DENIED либо неутверждённый B handoff:
**STOP; ничего не исправлять автоматически**. Не менять аккаунты/ACL/Windows Task,
H1 ARM/HALTED/SQLite/WAL, FINAM/пароли/DPAPI. C source/task остаётся disabled до
отдельного C approval. A policy v2 для ccobserver не переносится на ccpanel;
необходим отдельный A policy rebind и физическая A приёмка. H1/M15 не объединяются.
