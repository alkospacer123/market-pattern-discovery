# Независимый аудит Draft PR #551 — первый проход

Дата: 18.10.2026 MSK. Аудитор: отдельный агент по явному поручению пользователя.
Проверенный репозиторий: `alkospacer123/market-pattern-discovery`.
Вердикт: **NEEDS_FIX** для head `c155d37592719ac940eff112de9d40c0e3d9c7eb`.
Это инженерный code/evidence review; Intel physical acceptance **NOT_EXECUTED**.

## Дефект, требующий исправления

**A551-01 / P2 — истёкшие Task/process positives возвращаются при откате часов.**

`ControlCenter/app.py:49` сохраняет исходный positive snapshot. На `app.py:53`
`age_export_snapshot()` возвращает очищенную копию только для отображения; она
не записывается обратно в session state. В `cc/providers/h1_export.py:61` исходный
снимок снова принимается, если wall clock вернулся между received_at и expiry.

Самостоятельное воспроизведение на проверенном head без файлового/source I/O:

```
age(original, received_at + 31s):
  task=None, state=STALE, authority=UNKNOWN, value=None
age(original, received_at + 5s):
  task=TASK_RUNNING, state=UNKNOWN, authority=WINDOWS_OS_ONLY, value=XML hash
```

Так работает текущая последовательность UI reruns. Системный rollback после
истечения TTL возвращает старые OS facts без нового явного click. Health и
trading authority остаются UNKNOWN, поэтому это дефект свежести наблюдений,
а не разрешение торговли.

Требуемое поведение: наблюдённые expiry/clock failure должны очищать cached
positives до следующего явного получения. Узкое решение — сохранить aged copy
в session state, сохранив timestamps и zero I/O. Нужен UI regression
expiry → clock rollback → всё ещё UNKNOWN → новый ручной click восстанавливает
только заново полученные facts. Существующий `test_ttl_and_clock_rollback_without_new_io`
проверяет отдельные отображения, но не эту последовательность session state.

## Самостоятельно полученные GitHub и package evidence

- `git ls-remote origin refs/heads/main refs/pull/551/head`: main
  `9506d5c8790d4d3b3eabb629d38532a581051e54`, head `c155d37592719ac940eff112de9d40c0e3d9c7eb`.
- GitHub PR API: OPEN, draft=true, merged=false; base SHA тот же. Полное ТЗ
  прочитано из issue #524 comment 6247468651, весь diff и runtime зависимости проверены.
- Diff: 32 файла, +1001/-68; каждый changed path начинается с `ControlCenter/`.
  Все top-level Git entries вне ControlCenter побайтно совпадают как Git tree/blob metadata.
- Неизменные Git trees: TradingSystemLab `d27ac7153a4d25455112c1a6673d2b37a1784f43`,
  IntradayLab `9b71aeff75c49d3fc7b2fff7116b21d03fee5783`.
- GitHub exact-head workflow API: [run 39112796843](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/39112796843),
  job 117632284882, completed/success. Workflow неизменён, windows-2022,
  CPython 3.12.10 x64, pinned action SHAs, hashed dependency lock, contents:read.
- Checkout в артефакте `acbf1044b244f5053686896af9a4392c91113fbc` — merge ref;
  ControlCenter tree `d65c26662deceff385570d68a1f85381579bdd65` совпал с head.
- Артефакт 12130887953 скачан аудитором заново через GitHub tool. Outer SHA256
  `c99de1d36dfca568790117ec9a4980af499002e19efbd6824e4604e1bce2206d`
  совпал с GitHub digest. Inner ZIP SHA256
  `6c57a72bd9ec799e80ff93671f0b7d40f124a58c291bd9f54bb7670d91be3b9c`.
- Manifest SHA256 `5485621ec5e44e7ea3b87b58996c50a3b191ddf89b004c9cfebfe3812b04aa29`.
  112 entries: каждый packaged file независимо сопоставлен с digest И Git blob
  exact head. ZIP entries уникальны и ровно manifest + сам manifest. Active policies отсутствуют.
- JUnit пересчитан независимо: full 479 PASS / 0 FAIL / 15 POSIX-only SKIP;
  manual OS 48/0/0; observer 39/0/0; reader 44/0/0; transport 12/0/0;
  source 27/0/0; preflight 41/0/0. Summary не был единственным основанием.
- Локально аудитор повторил manual/os-observer suite: **67 PASS** (Linux;
  это дополнительная проверка, не Windows evidence).

## Проверенные границы

1. **Ручной путь.** `app.py:43-55`, `h1_windows_os.py:92`, `h1_export.py:41-55`:
   shared thread lock и существующий per-SID OS manual gate берутся до policy,
   identity и Task/process I/O. Busy/error возвращает новый UNKNOWN. Source switch
   очищает cache. Timer, background polling, retry и live calls на navigation/startup
   в исходнике отсутствуют; AppTest проверяет zero-call сценарии и один вызов по click.
2. **Один стандартный ccpanel.** `h1_windows_os.py:63-74`, `observer/identity.py`,
   `Read-OsFacts.ps1:24-34`: собственный primary token/SID, full token groups,
   privileges, elevation/limited-token/impersonation rejection; helper проверяет
   existing enabled local ccpanel до Task. No compiler child в manual path.
   Реальный hosted low-SID rehearsal читает protected policy через spawned reader,
   выполняет fixed helper с require_ccpanel, подтверждает Ready/real ACCESS_DENIED,
   private denial, TTL и zero export writes (`ci/identity_probe.py:65-97`).
3. **Policy/source binding.** `h1_windows_os.py:23-60`: отдельная C schema,
   exact keys, duplicate/NaN rejection, explicit TTL, fixed Task, SID separation,
   optional полный PID/epoch/image/command/owner binding. Existing native reader
   проверяет admin owner/DACL, NTFS, held ancestors/leaf, reparse/hardlinks/path drift.
   Native valid/junction/writable-parent/missing/duplicate случаи действительно PASS.
   A policy не принимается как C approval; example unapproved, active policy не поставляется.
4. **Task/process identity.** `Read-OsFacts.ps1:36-106`: only readonly scheduler COM,
   targeted CIM PID, XML/principal/state bracket; optional pinned process без discovery,
   wrong epoch/image/command/owner → UNKNOWN; unknown Task блокирует process.
   Hash image означает hash строки path, а не проверку executable bytes — docs это раскрывают.
5. **Bounded acquisition.** `observer/windows_os.py:60-87`: один fixed
   PowerShell child, scrubbed env, total timeout 6s, no shell string/retry; отдельный
   policy read worker имеет 2s timeout/cleanup. Native helper timeout test проверяет
   завершение child, ошибки не превращаются в absence.
6. **Legacy noninterference.** `read_source()` и default exporter collect остаются
   BLOCKED; Start-Exporter execute disabled. Runtime OS path не принимает legacy path.
   Native negative WinError5/последующее recovery сохранены.
   В positive native competition producer — отдельный process: 500 успешных
   os.replace, 0 errors. Обе filtered kernel File Create traces самостоятельно
   пересчитаны: 2 parent / 1 PowerShell positive opens, 0 heartbeat creates,
   1000 next.tmp creates только producer; все EventsLost/LogBuffersLost/
   RealTimeBuffersLost=0. Producer завершается внутри trace coverage.
   Elevated fixture competition адаптирует Task и identity; отдельный unmodified
   standard-ccpanel helper проверяется в rehearsal. Это CI fixtures, не Intel H1.
7. **Metadata не включена.** Отдельный path-attributes experiment реально записал
   PermissionError/WinError5 после 1 replace; runtime DISABLED/NOT_ACCEPTED.
   Он не выдаётся за successful noninterference и не используется manual source.
8. **Доверие и UNKNOWN.** os_contract + os_snapshot проверяют schema/reasons,
   confidence/digest/timestamps/pins; source/account UNVERIFIED. Heartbeat, health,
   reconciliation, kill-switch, FINAM, positions, SLTP и финансы UNKNOWN.
   Нулевых fabricated positions/finance нет. M15 NOT_DEPLOYED, десять controls disabled.
9. **Запрещённые компоненты.** В diff нет TradingSystemLab/IntradayLab или workflow
   edits; runtime не импортирует broker/production/SQLite и не читает private policy.
   Нет H1 Task/kill-switch/ARMED/trading authorization mutation. CI accounts/ACL/Tasks
   создаются только в guarded disposable hosted fixtures; это не Intel changes.
10. **Heartbeat script.** Tracked `tsl-h1-01-check.ps1` отсутствует; source не
    предоставлен, скрипт не запускался. Отдельные будущие способы получения
    sanitised readonly telemetry описаны с независимым audit gate.

## Остаточные физические условия

Intel не подключался. Реальные Task/CIM read rights, root-volume ACL, source pins,
ccpanel profile и cross-terminal Windows sessions требуют отдельного физического
evidence. Read access может законно дать ACCESS_DENIED/UNKNOWN без ACL repair.
`CC03_MANUAL_OS_INSTALLATION_READINESS.md` правильно сохраняет A отдельным,
B/C NOT_AUTHORIZED/NOT_APPROVED и physical NOT_EXECUTED. Hosted CI не Intel PASS.

Merge, auto-merge, deployment, публикация GitHub review/comment и изменения серверных
прав аудитором не выполнялись. После исправления A551-01 требуется повторный audit
изменённых участков и exact-head Windows CI; текущий PASS pipeline дефект не покрывает.
