# Control Center — реестр документации и source authority

**MAIN audit 22.11.2026:** `0e569be6cb3c7cce1f7224e7f1fef6be38f6ba52`. Все **28 ранее существовавших** Markdown-файлов `ControlCenter/` классифицированы вместе с пятью новыми документами передачи знаний. Статус CURRENT — авторитет по GitHub-коду, а не гарантированная физическая LIVE-приёмка.

Метки: **CURRENT** — актуальный V20 8502; **HISTORICAL** — H1/M15 8501/ранняя стадия; **SOURCE_EVIDENCE** — датированный отчёт/аудит; **SUPERSEDED** — не использовать как нынешний guide V20; **RESEARCH** — предложение, не implementation; **UNKNOWN** — недостаточно подтверждений. У смешанных документов статус указывается по разделам.

| Документ (от `ControlCenter/`) | Статус |
|---|---|
| `README.md` | CURRENT верх / HISTORICAL раздел CC-03 ниже |
| `docs/ACCEPTANCE_REPORT.md` | SOURCE_EVIDENCE: frozen acceptance |
| `docs/ARCHITECTURE.md` | HISTORICAL: H1/M15 8501 |
| `docs/CC02_INTEL_REAL_SOURCE_PREVIEW_20261027.md` | SOURCE_EVIDENCE: датированный V20 preview |
| `docs/CC03_ACCEPTANCE_REPORT.md` | SOURCE_EVIDENCE: CC03 |
| `docs/CC03_EXPORT_MAINTENANCE.md` | HISTORICAL: CC03 maintenance |
| `docs/CC03_FUTURE_TELEMETRY_SPEC.md` | RESEARCH: future proposal |
| `docs/CC03_INDEPENDENT_AUDIT_551.md` | SOURCE_EVIDENCE: independent audit |
| `docs/CC03_INTEL_INSTALLATION_PLAN.md` | HISTORICAL: H1 install plan |
| `docs/CC03_INTEL_PREFLIGHT_POLICIES.md` | SOURCE_EVIDENCE: historical preflight |
| `docs/CC03_INTEL_READONLY_PREFLIGHT_PACKAGE.md` | SOURCE_EVIDENCE: package |
| `docs/CC03_MANUAL_OS_INSTALLATION_READINESS.md` | SOURCE_EVIDENCE: NOT_EXECUTED |
| `docs/CC03_MANUAL_OS_SOURCE.md` | HISTORICAL: H1 OS-only |
| `docs/CC03_OS_ACCEPTANCE.md` | SOURCE_EVIDENCE: partial acceptance |
| `docs/CC03_PHYSICAL_ACCEPTANCE_PLAN.md` | HISTORICAL: CC03 plan |
| `docs/CC03_PYTHON312_BASE.md` | SOURCE_EVIDENCE: historical Python |
| `docs/CC03_SINGLE_CCPANEL_AUDIT.md` | SOURCE_EVIDENCE: ACL audit |
| `docs/CC03_SOURCE_AUTHORITY.md` | SOURCE_EVIDENCE: H1 source limits |
| `docs/CC03_STREAMLIT_REFRESH_558.md` | SOURCE_EVIDENCE: historical UI |
| `docs/CC03_WINDOWS_HOSTED_ACCEPTANCE.md` | SOURCE_EVIDENCE: historical CI |
| `docs/CC03_WINDOWS_OS_OBSERVER.md` | HISTORICAL: H1 observer |
| `docs/CC03_WINDOWS_SECURITY.md` | HISTORICAL: H1 security |
| `docs/H1_READONLY_SNAPSHOT_CONTRACT.md` | HISTORICAL: H1 schema |
| `docs/ROADMAP_STATUS.md` | SUPERSEDED для V20 / HISTORICAL для H1 |
| `docs/SECURITY_BOUNDARY.md` | SUPERSEDED для V20 / HISTORICAL для H1 |
| `docs/SOURCE_INVENTORY.md` | SOURCE_EVIDENCE: H1/M15 inventory |
| `docs/V20_CC08_OPERATIONS.md` | CURRENT верх / SOURCE_EVIDENCE archival appendix |
| `docs/V20_CONTROL_CENTER_ROADMAP.md` | CURRENT верх / SOURCE_EVIDENCE timeline |
| `docs/V20_START_HERE_SOURCE_MAP.md` | CURRENT: источник навигации |
| `docs/V20_CC07_COMMAND_CONTRACT.md` | CURRENT: команды |
| `docs/V20_DATA_SECURITY_TESTS.md` | CURRENT: данные/security/CI |
| `docs/V20_HEALTH_EXPOSURE_FIX_20261126.md` | SOURCE_EVIDENCE / REVIEW_CANDIDATE: HEALTHY/exposure fix; не INSTALLED/LIVE |
| `docs/V20_KIMI_EXAM.md` | CURRENT: экзамен prepared |
| `docs/V20_DOCUMENT_REGISTER_20261122.md` | CURRENT: реестр |

## Не-Markdown и файлы сопровождения

- `docs/CC02_AUDIT_REPORT.json`, `docs/CC03_OS_NATIVE_RESULTS.json`, `docs/INTEGRITY_REPORT.json`, `docs/browser-check.json`, `docs/screenshots/` — **SOURCE_EVIDENCE**; не LIVE.
- `docs/CC03_READONLY_EXPORT_SCHEMA.json`, `docs/CC03_WINDOWS_OS_SCHEMA.json`, `docs/H1_READONLY_SNAPSHOT_SCHEMA.json` — **HISTORICAL** схемы H1/CC-03. `deployment/v20-readonly-policy.example.json` — только пример, не действующая permission.
- `app.py`, `observer/` и тесты H1/CC-03 — **HISTORICAL/SOURCE_EVIDENCE**. `v20_app.py`, `v20_admin_control.py`, `cc/v20_contract.py`, `controller/cc07-v20-operator.ps1`, `deployment/v20_live_export.py` — действующие **SOURCE** по MAIN; установленность на Intel сверяется отдельно.
- `.github/workflows/controlcenter-cc03-windows-native.yml` — **CURRENT frozen CI definition для HISTORICAL CC-03**. Никакой green CI не отменяет исторический `scope_audit` exit 1 или отсутствие FINAM LIVE acceptance. `requirements*.lock`, `pytest.ini`, `deployment/manifest.json` — параметры/manifest, не разрешения на запуск.

## Найденные конфликты
1. В действующих status blocks `README.md` и `docs/V20_CONTROL_CENTER_ROADMAP.md` #568 обозначался Draft после фактического [Merge #568](https://github.com/alkospacer123/market-pattern-discovery/pull/568) 20.11; исправить действующий текст, оставить оригинальные старые утверждения в исторических разделах.
2. `ARCHITECTURE.md` и `SECURITY_BOUNDARY.md` явно описывают старый H1/CC03/8501 с отключёнными кнопками. Для V20/8502 актуальный путь описан в [START HERE](V20_START_HERE_SOURCE_MAP.md), [CC-07](V20_CC07_COMMAND_CONTRACT.md) и [телеметрии](V20_DATA_SECURITY_TESTS.md).
3. `v20_command_channel.py` + `cc07_command_worker.py` — альтернативный staged gateway с другим PIN/контрактом, тогда как нынешний UI импортирует `v20_admin_control.py`. Не объединять их в одну установленную систему.
4. Для frozen CC03 ожидаемый native `scope_audit exit 1` — **исторический отказ**, отдельно распознанный workflow. Узкий CI SUCCESS ≠ исправленный исходный полный scope PASS.

## Статическая проверка относительных ссылок — 22.11.2026

В точном head `bd0817b19f2837e48b8c33bc298f4d2a92a06691` проверены **33/33 Markdown-документа**, **147** относительных ссылок по полным путям Git tree. **146 целей существуют, 1 историческая цель отсутствует в MAIN:** `docs/SOURCE_INVENTORY.md` → `../../IntradayLab/SELECTED_T3_M15_SESSION_T1_R20.md` (строка 121). Это историческая ссылка на план M15/R20, не рабочая V20-инструкция; **HISTORICAL LINK BROKEN**. Не перенаправлять на более позднюю R15-версию без независимой source-parity проверки и не изменять старый отчёт задним числом. Указанный SHA — проверенная версия до добавления этого абзаца; для PR HEAD повторно сверить файл, дифф и новые ссылки.

Проверены **пути**, но не Markdown anchors, внешние URL, содержимое ZIP/изображений или частные Windows пути: `NOT_VERIFIED`.

## Ограничения
Идентичности источников и 28 названий сверены с Git tree MAIN (не усечён). Отсутствуют новая физическая проверка Intel, новый Windows pytest/JUnit и независимая FINAM/SLTP сверка; их статусы **NOT RUN / NOT_VERIFIED**. Не заявлена ручная проверка **каждой** старой ссылки, внешнего URL, anchor и бинарных артефактов. Не редактировать старые отрицательные отчёты задним числом и не удалять их ради чистоты.

[Главная карта](V20_START_HERE_SOURCE_MAP.md) · [CC-08](V20_CC08_OPERATIONS.md) · [Экзамен Kimi](V20_KIMI_EXAM.md).
