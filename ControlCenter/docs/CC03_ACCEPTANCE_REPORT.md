# CC-03 source preparation acceptance

> Исторический отчёт подготовки #533. Реальная hosted Windows проверка #534
> обнаружила блокирующий atomic producer conflict; прежнее утверждение о
> достаточности DELETE-sharing опровергнуто исполнением.
> Актуальный статус: [CC03_WINDOWS_HOSTED_NATIVE_NEEDS_FIX](CC03_WINDOWS_HOSTED_ACCEPTANCE.md).

Результат: **CC03_SOURCE_PREPARATION_PASS** для кодовой подготовки. **CC03_PHYSICAL_PASS НЕ установлен.** Windows native/PowerShell/effective ACL и Intel установка/приёмка — **NOT_VERIFIED / NOT_EXECUTED**. После одного Draft PR — STOP для независимого внешнего аудита, без merge/auto-merge/CC-04.

## GitHub / protected identity

- Исходный main/HEAD: `305587ccc10ce6b4fa456a72d74fec4dad70eb11`. Во время работы merged docs-only #532; итоговая база актуализирована до `52e167d7b36170f1f639827eb875a57d52175491`, без собственных изменений trading projects. Ветка `codex/controlcenter-cc03-windows-readonly` создана от него. Final head SHA и полный список изменённых файлов — в Draft PR body (без self-referential hash документа).
- PR #531 GitHub REST: merged=true, merge `305587ccc10ce6b4fa456a72d74fec4dad70eb11`, former head `450477b80e18b4a77a330e649b6a93ec59c794ba`.
- Прочитаны Issue #524 и roadmap v1.0, CC-02 contract/schema/audit/architecture/security/source docs, actual ControlCenter, CURRENT_STATE и код heartbeat/kill switch producers. Research/OOS/market data не использовались.
- Последний документированный Intel installed `3a18c8c24301c866a60f5d725de227288d48f7ec`, Task Disabled, HALTED. Новый merged #532 документирует созданный durable exact-commit/account-bound authorization; NOT ARMED / NOT RUNNING, отдельного разрешения start/rearm нет. Исходное отсутствие authorization теперь исторический checkpoint. Это исторический операторский checkpoint, не новый server read. Source fill flag #528 True отличается от старых roadmap comments; он не менялся и не считается authorization.
- Intel→base protected-project diff: пять operational Markdown TradingSystemLab, 100 added lines; IntradayLab без отличий. GitHub main не переносился на Intel.

| Protected tree | Base / итоговый Git tree |
| --- | --- |
| TradingSystemLab | `be882bd0aa9cf5e7c210c2bf2a4928615e298eab` |
| IntradayLab | `c4f6e652ba442a575ad5711cb3f55841f860f484` |

Исходный protected H1 tree до upstream #532 был `ecc5f08f331a55d76f46be48a02febec1877b87f`; новый H1 tree принят исключительно из upstream docs-only base. Собственных изменений вне ControlCenter нет. Сравнение tree IDs и diff выполняется перед commit/PR; manifest содержит package file SHA-256, не broker signatures.

## Выполненная реализация

Windows Kernel32 read-only backend: local NTFS, lexical/no-reparse ancestor validation, held handles, type/final path/link count, identity before/after/path reopen, strict 128KiB, worker timeout. Leaf DELETE sharing сохраняет production atomic publication; root pin для existing sources. Администраторские policies дополнительно проверяются через GetSecurityInfo owner/DACL, а не собственными approval booleans.

Независимый one-shot exporter читает два утверждаемых JSON без engine/DB/API/token, очищает и атомарно пишет только собственный export. Реальная настройка отсутствует. Receiver source/account/spec/active/installed commit/time checks, per-group TTL без production defaults, UNKNOWN/STALE/HALTED/UNHEALTHY/UNRESOLVED и отсутствие account-derived numbers. HEALTHY от нынешнего partial exporter недостижим без approved Task source. DEMO/OFFLINE_FIXTURE работают, M15 независим, 10 disabled controls сохранены.

Windows package: preview-first preflight/install/panel+exporter launch/readonly verify/manual Task probe/uninstall, manifest, independent venv/offline-wheelhouse, ACL matrix/log/network/rollback instructions. ACL и Tasks физически не изменялись.

## Фактическая проверка

Среда: Linux, Python 3.12.14, Streamlit 1.50.0, Plotly 6.3.1, pytest 8.4.2. Standalone import check: TradingSystemLab=False, IntradayLab=False, finam=False. Windows отсутствует.

| Проверка | Результат |
| --- | --- |
| Исходный CC-02 suite из git archive base | **254 PASS** |
| Итоговый полный ControlCenter suite | **316 PASS, 12 SKIP** (все native Windows → NOT_VERIFIED) |
| Standalone copy только ControlCenter, без trading dirs | **316 PASS, 12 SKIP** |
| Старые tests сохранены | PASS; selector assertion расширен только новым fixed READONLY_EXPORT; import allowlist узко добавлен для новых receiving modules |
| Native Windows API/security, junction/symlink/hardlink, race и ACL actual execution | **NOT_VERIFIED** (12 native cases) |
| PowerShell runtime/install/rollback/effective ACL | **NOT_VERIFIED**; static preview/path/forbidden mutation checks PASS |
| package manifest / schema parity / pip check / git diff --check | PASS |
| Independent code audit отдельным агентом | PASS по исходникам/отдельному suite; три findings исправлены, открытых blocking нет; внешний Draft PR audit ожидается |

Команды воспроизведения из standalone ControlCenter:

```powershell
python -m pytest -q
python deployment\manifest.py --check
python -m pip check
```

Полный fault coverage: malformed/duplicate/nonfinite/oversize/partial JSON; source/spec/commit/account/binding mismatch; HALTED с историческим heartbeat и свежим KS; unapproved TTL/calendar UNKNOWN; STALE без last-good resurrection; missing exporter, M15 и disabled UI; no account authority/finance/fill/protection. Windows protocol mocks: symlink/junction/reparse/hardlink/type/ACL/API failures, substitution file/root, partial/growing read, deadline/cleanup. Native cases отдельно помечены, они **не выполнены**. На будущем Windows run 15 POSIX-specific injections будут явно skipped и заменены native suite; Linux здесь выполнил их все.

Independent audit нашёл и закрыл: (1) leaf sharing, блокирующий producer atomic replace; (2) policy trust без ACL leaf/ancestor enforcement; (3) unconditional current HALTED caption и fixture captions для export. Добавлены regression checks. Linux audit не сертифицирует Win32 safety.

## Нулевые торговые действия и оставшиеся блокеры

В этой сессии: ноль trading/broker API calls, ноль H1/IntradayLab file changes, ноль production SQLite opens/writes, ноль robot Task mutations, authorization/rearm/FINAM_FILL_AUTHORITY_VERIFIED changes, trading-engine imports, Trading Token access, Intel контактов. Evidence: protected Git trees/diff, narrow runtime import/call AST guards, tests с запрещёнными network/DB/process/write hooks, independent code review. Это не новый broker-account audit и не доказательство фактического текущего состояния Intel.

Будущие потенциальные источники: existing production heartbeat и kill-switch JSON; heartbeat reconciliation только диагностическое. Реальное наличие/ACL/commit/account binding/cadence на Intel **не подтверждены**. Task manual probe подготовлен, ingestion/process source NEEDS_SOURCE_APPROVAL. H1 bars/calendar, decision trace, execution/position/fill/active SLTP и finances/cashflows — NEEDS_SOURCE_APPROVAL; production SQLite не используется для обхода.

Остаются: native Windows full run и PowerShell rehearsal; exact source root IDs/ACL/effective rights; реальная private account mapping и independent receiver policy; production TTL/calendar; разрешённые безопасные источники недостающих полей; отдельное операторское разрешение physical install и before/after evidence. Если old heartbeat другого commit не позволяет binding, оставить UNKNOWN без H1 restart.

Точные будущие команды/ожидания/STOP/rollback: [installation](CC03_INTEL_INSTALLATION_PLAN.md), [Windows security](CC03_WINDOWS_SECURITY.md), [physical acceptance plan](CC03_PHYSICAL_ACCEPTANCE_PLAN.md), [source authority](CC03_SOURCE_AUTHORITY.md). Ни один физический шаг не выполнен. Merge, auto-merge и переход CC-04 запрещены в этой поставке.
