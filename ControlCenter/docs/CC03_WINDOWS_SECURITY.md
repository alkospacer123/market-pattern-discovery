# CC-03 Windows security: hosted native NEEDS_FIX

GitHub-hosted Windows execution выявил блокирующий конфликт с существующим
`os.replace` producer. См. [актуальное hosted acceptance evidence](CC03_WINDOWS_HOSTED_ACCEPTANCE.md).
Все native cases исполняются; безопасность и совместимость ещё не приняты.

Backend: `cc/providers/windows_file.py`, стандартная библиотека `ctypes` + штатный Kernel32. Только local fixed NTFS, drive-letter absolute paths. UNC/remote/device namespace, ADS, traversal, reserved DOS names, trailing dot/space, reparse/junction/symlink и hardlink leaf запрещены. Неподдерживаемый API/FS/право/тип → безопасный UNKNOWN; обычного read_text fallback нет.

Каждый ancestor, включая drive root и разрешённый root, открывается `CreateFileW(FILE_LIST_DIRECTORY|FILE_READ_ATTRIBUTES|READ_CONTROL, FILE_SHARE_READ|FILE_SHARE_WRITE, OPEN_EXISTING, FILE_FLAG_OPEN_REPARSE_POINT|FILE_FLAG_BACKUP_SEMANTICS)`. Metadata-only handle ранее не участвовал в Windows share checks и не блокировал rename каталога; добавленный LIST_DIRECTORY делает запрет DELETE-sharing действенным. WRITE-sharing каталога позволяет child publication; write access reader не запрашивает. Все handles удерживаются до конца чтения. Для leaf — `GENERIC_READ`, `FILE_SHARE_READ|FILE_SHARE_DELETE`, тот же OPEN_EXISTING/no-follow. Ни WRITE/CREATE/TRUNCATE доступа, ни открытие SQLite. DELETE-sharing **недостаточно** для замены открытого leaf через существующий `os.replace`: реальные Windows tests остаются FAIL. Проверяются disk type, directory bit, reparse attribute, GetFinalPathNameByHandleW, volume+file index, размер, modification/creation times и число ссылок. После чтения повторяются handle metadata и pathname-open identity всех компонентов. Source roots дополнительно привязаны к заранее независимо принятому NTFS file ID. В любой сомнительной ситуации весь снимок UNKNOWN.

Размер вызывающего запроса строго 1..131072 bytes; stat leaf строго 1..limit, чтение максимум limit+1, длина равна исходному size. Частичное/изменённое чтение и подмена отвергаются. In-place writer с уже открытым write-handle не совместим с sharing policy — reader откажет. Совместимость с существующим атомарным heartbeat producer не подтверждена и фактически блокирует приёмку.

Native I/O исполняется в отдельном spawned процессе. Parent ждёт сообщение до 2s после process.start; затем terminate + ограниченный join. Metadata/File open без async cancellation не блокируют Streamlit навсегда в worker. Это **не абсолютная real-time гарантия**: OS process creation/termination/scheduling могут задерживаться; при зависшем ядре нельзя обещать точную верхнюю границу. Native API из worker не вызывается из веб-процесса. Процесс не запускает shell, сервис или Windows Task.

## Ограничения

Это не защита от администратора, kernel driver, compromised filesystem, writable memory mapping, смены mount/volume вне обычных NTFS semantics, преднамеренного изменения timestamps привилегированным субъектом или скомпрометированного approved producer. Проверки before/after уменьшают TOCTOU; изменение сразу после последней проверки неизбежно возможно. Снимок представляет наблюдение с timestamp, не непрерывную истину. Close/reopen не доказывает брокерскую подлинность. Directory handles могут кратко мешать переименованию runtime directory; открытый leaf блокирует существующую atomic replacement. Подключение к реальному producer запрещено до исправления.

ACL не угадываются из JSON и не изменяются reader-ом. `GetFinalPathNameByHandleW` intentionally fail-closed при short-name/case/volume alias несоответствии (case сравнивается без регистра); использовать канонические длинные local paths. Parent процесс/очищенная policy и export roots доверяются по ACL. Exporter удерживает no-reparse directory handles во время atomic publication в фиксированный собственный каталог. Панель не импортирует exporter и не получает запись в его каталог.

## Проверяемая ACL-матрица (план, не применена)

| Ресурс | SYSTEM / Administrators | CCPanel | CCExporter | H1 robot identity |
| --- | --- | --- | --- | --- |
| `C:\TSLControlCenterApp` + code/deployment policy | Full | Read/Execute | Read/Execute | Нет новых grant |
| `C:\TSLControlCenterVenv` | Full | Read/Execute | Read/Execute | Нет новых grant |
| `C:\TSLControlCenterData` parent | Full | Read/Execute | Read/Execute | Нет новых grant |
| `…\export` | Full | Read/Execute | Modify | Нет новых grant |
| `…\logs` | Full | Modify | Нет (допустим Read/Execute) | Нет новых grant |
| `…\private` | Full | Нет | Read/Execute | Нет новых grant |
| Два принятых H1 source JSON + traversal parents | Без изменения действующих grants | Нет | Только явно утверждённое read/traverse | Прежние права без изменений |
| H1/M15 checkout, SQLite/WAL, tokens, auth, другие runtime files | Прежние права | Нет | Нет (кроме двух утверждённых JSON) | Прежние права |
| H1 Task/service/process control | Прежние права | Нет | Нет; manual probe отдельный read-only identity | Прежние права |

Два разных standard local users, не robot/admin identity; без Administrator/Backup/Debug/операторских групп/привилегий. Родительские каталоги защищены от перенаправления и изменения DACL этими SID; owner SYSTEM или Administrators. Отключить inheritance на шести CC roots; только SYSTEM/Admin и два явных SID по матрице, без Everyone/Users/Authenticated Users/Creator Owner grants. Никакой автоматической модификации H1 ACL: если невозможно предоставить узкий read без ослабления production boundary — NEEDS_SOURCE_APPROVAL, exporter не подключать.

Проверка в будущей sandbox Windows после отдельного согласования (SID только локально, не публиковать):

```powershell
$panelSid = (Get-LocalUser 'CCPanel').SID.Value
$exporterSid = (Get-LocalUser 'CCExporter').SID.Value
Get-LocalGroupMember Administrators  # вручную исключить оба SID и связанные привилегированные группы
Get-Acl C:\TSLControlCenterApp | Format-List Owner,AreAccessRulesProtected,Access
icacls C:\TSLControlCenterApp
.\deployment\Preflight.ps1                       # PREVIEW, без writes
.\deployment\Preflight.ps1 -Execute -PanelSid $panelSid -ExporterSid $exporterSid
```

Ожидается `CC03_PREFLIGHT_PASS_NO_H1_ACCESS`; ошибка наследования, owner, broad grant, excessive rights, совпавшие SID или не-NTFS → STOP. Скрипт проверяет declared DACL, **не полную effective token/group privilege модель**. Дополнительно под каждым настоящим SID выполнить `whoami /all` приватно и negative-access checks из физического плана. Root DACL checker не доказывает ACL каждого старого source ancestor: их проверяют отдельно.

## Тесты и стоп-условия

```powershell
# Только disposable Windows sandbox, НЕ Intel production runtime.
.\.venv\Scripts\python.exe -m pytest tests/test_windows_reader.py tests/test_cc03_source.py -q
.\.venv\Scripts\python.exe -m pytest -q
```

На Windows 15 POSIX descriptor-specific fault cases явно skipped, вместо них запускается native backend suite; они не объявляются Windows PASS. Native tests: обычный read, symlink file/directory, junction/reparse, hardlink, oversize/directory/missing, existing writer, pinned-directory substitution, atomic producer replace while handle открыт, insufficient file ACL, missing Kernel32 primitive. ACL tests меняют **только временный тестовый файл**, finally восстанавливает deny. Symlink privilege absent → skip, остаётся NOT_VERIFIED. Protocol mocks проверяют partial/size/file+directory substitution/handle cleanup/deadline; они не заменяют Windows. Native JSON parsing проверяется общим receiving suite на Windows.

Hosted Windows доступен; точные native/PowerShell/ACL результаты и SHA перечислены в отдельном hosted отчёте. Intel не использовался. Запрет физического rollout сохраняется: есть producer sharing conflict. Любой native failure, permission excess или source identity mismatch → STOP приёмки; H1 не трогать.
