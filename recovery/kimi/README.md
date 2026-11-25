# Kimi Phase II — три логических проекта знаний

## Checkpoint G6.4 / G6.5 — 25.11.2026

**Проверенный SOURCE BASE:** `alkospacer123/market-pattern-discovery/main@e05bbd24db88f127a52f0ff1b7282d7c6919cd81`. Фактическая среда текущей проверки — **Kimi Work**; GitHub READONLY-доступ в ней **PASS**. Это отдельное свидетельство о GitHub source-only работе, не о Kimi Code на Windows, INSTALLED или LIVE.

- **G6.4 — COMPLETE в заявленном scope:** оператор принял проверку GitHub READONLY-доступа и иерархии документации.
- **Независимая сверка GPT — 19/19 Git blob SHA MATCH; иерархия документации Control Center признана корректной.** Результат передан оператором и для данного checkpoint имеет класс `REPORTED_ONLY`: Kimi Work не выдаёт его за собственную повторную сверку всех 19 blob.
- **G6.5 — DOCUMENTATION ONLY:** фиксирует этот результат через отдельную ветку и Draft PR. Draft PR не является принятым MAIN, независимой приёмкой или основанием для Merge.

| Последующий статус | Действующее заключение на 25.11.2026 |
| --- | --- |
| Полный `CODE_EXAM_PASS` | **NOT CONFIRMED** данным испытанием |
| Полный `HANDOFF_PASS` | **NOT CONFIRMED** до независимого review G6.5 и решения оператора |
| `OFFLINE_EXECUTOR` | **NOT READY / NOT CONFIRMED** |
| `LIVE` | **UNKNOWN** |
| `COLD_RESTORE` | **NOT TESTED** |

Новый блок не отменяет датированные статусы и SHA ниже и не закрывает другие пункты [Roadmap](../../ROADMAP.md). Следующий проверяемый шаг — независимое GPT-ревью именно G6.5 diff, затем решение оператора. Практические правила остаются в [экзамене и handoff](EXAM_AND_HANDOFF.md) и [Windows access gate](WINDOWS_WORKSPACE_AND_ACCESS.md). Никаких действий с FINAM, Intel, production, секретами или долговременной памятью этот checkpoint не разрешает и не подтверждает.


**OPERATING UPDATE 23.11.2026 (operator evidence):** два Kimi Chat проекта уже созданы до подписки; третий (Control Center) планируется после активации Pro. Kimi Code Desktop авторизован под тем же аккаунтом, `Always Ask` выбран; GitHub OAuth Kimi предоставлен, но фактический доступ инструментами Kimi ещё не проверялся. На Intel NTFS создана рабочая Git-копия `C:\KimiSandbox\market-pattern-discovery`: оператор сообщил `HEAD=1413273a1a312802a0ced7a06a4eb73f050d2ec3`, `REQUIRED_FILES=PASS`, `WORKTREE_CLEAN=PASS`, `KIMI_C_SOURCE_WORKSPACE_READY`. Это **не** OS sandbox, не тест Kimi и не LIVE. Исторический статус и SHA документа 22.11 ниже относятся только к своему срезу. [Действующий Windows gate](WINDOWS_WORKSPACE_AND_ACCESS.md).


> **SOURCE AUTHORITY CHECK 22.11.2026:** последние принятые GitHub-документы после [Merge #589](https://github.com/alkospacer123/market-pattern-discovery/pull/589) зафиксированы на контрольном `main=41d0b48c1d33db29bc1b19497d558748b3db8fb4`. Указанный ниже `bb8c46c1...` — **воспроизводимый исходный base до #589**, а не всегда актуальный HEAD. Перед чтением и практическим экзаменом перепроверять `main`, Git blobs и [иерархию документов](../DOCUMENTATION_AUTHORITY_2026-11-22.md). Никаких Kimi Chat/Code access, установленного LIVE, FINAM или cold restore не подтверждено.

PINNED_SOURCE: market-pattern-discovery main `bb8c46c1db89ca2b5311f22c755bb4e51ce8f7d6`, GitHub 22.11.2026. Это исходные материалы, а не настройка Kimi или проверка Intel.

**СТАТУС: SOURCE_PACKAGES_PREPARED / KIMI_CHAT_NOT_CONNECTED / KIMI_CODE_NOT_CONNECTED / EXAM_NOT_RUN.**

Один общий репозиторий, три независимых логических проекта Kimi: [V20 Trading System](V20.md), [Control Center V20](CONTROL_CENTER.md), [Trading Research Lab](TRL.md). Для каждого использовать [общий AGENTS](../../AGENTS.md), [README](../../README.md), [паспорт и источники](../README.md), затем только свой профиль. Исторические H1/M15 — общие библиотеки и исследовательские источники, не отдельные LIVE-проекты. Исторический `audit_only/stop_tick_grid_20261012` **не удалён**: [R7 финальный аудит](../R7_STAGE_I_FINAL_ACCEPTANCE_20261122.md) выявил два прямых H1 offline source/test dependency; Kimi не должен выдавать их за актуальную V20 LIVE логику.

Kimi Chat: понять письменные источники и независимо ответить на вопросы. Kimi Code: отдельный реальный доступ к GitHub, точные SHA, isolated checkout, запуск разрешённых offline tests. Kimi Chat не заменяет Kimi Code.

MAIN != INSTALLED != LIVE != RESEARCH != ARCHIVE. Никаких DPAPI, FINAM credentials, приватных SQLite, номеров счетов, персональных журналов, брокерских POST, удалённых команд на Intel, ребалансировки капитала, auto-Merge или deploy.

Обязательный практический [экзамен и GPT ↔ Kimi handoff](EXAM_AND_HANDOFF.md). После подлинной приёмки Kimi — последний этап: автономный backup и настоящий offline cold restore. Git history и CI не заменяют Recovery.

Внешние Kimi-проекты ещё не созданы через этот GitHub PR, доступ не подтверждён, экзамен не сдавался.

## Kimi Code on Intel Windows — practical preparation (23.11.2026)

[Windows workspace, GitHub access and staged permissions](WINDOWS_WORKSPACE_AND_ACCESS.md): the designated *source* checkout is `C:\KimiSandbox\market-pattern-discovery` on NTFS; the former temporary external `D:\KimiSandbox` was removed by the operator. Creating this folder and cloning Git does **not** establish a secure execution sandbox. Read-only source evaluation precedes isolated offline tests; successful examinations permit operator-approved graduated access to non-secret production evidence, not automatic LIVE control. Monthly Pro is the capacity pilot before annual Pro/Max; local Windows acceptance is still pending.
