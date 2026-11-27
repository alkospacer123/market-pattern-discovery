# Kimi Phase II — три логических проекта знаний

## C3 — переход к единой базе знаний (27.11.2026, candidate)

- Рабочая очередь и статус: [Roadmap](../../ROADMAP.md), [Recovery STATUS](../STATUS.md). Актуальный MAIN устанавливается при каждой содержательной задаче; dated checkpoints ниже — история.
- Общая проверка источников — [AGENTS](../../AGENTS.md#проверка-источников--общий-порядок-c3-candidate); совместная работа — [HANDOFF](EXAM_AND_HANDOFF.md#действующий-рабочий-маршрут--c3-candidate-27112026); критические инварианты — [COC](../CRITICAL_OPERATIONS_CONTRACT.md). Профильные паспорта и source maps остаются предметными источниками. Читай только необходимое.
- Цель: устранить повторные копии и оставить только действительно необходимые установленные Skills после проверки полного покрытия требований, CI, ссылок и проверяемого fallback. [Текущие snapshots и план перехода](memory/README.md). В этом commit никаких удалений и изменения установленных Skills/настроек.
- C1/C2 приняты в указанном Roadmap объёме, B принят ограниченно, C3 не завершён. Не повторять прежние экзамены; обязательные evidence gaps и KDR остаются. Ранее датированные NOT_CONNECTED/NOT_EXAMINED не являются текущим состоянием.

**Решение владельца 26.11.2026 — рабочие роли Kimi.** Kimi Chat — основное общение, знания, обсуждение, аналитика и планирование; Kimi Code — основной технический исполнитель (Intel, V20, Control Center, TRL, GitHub, Python, PowerShell, тестирование, удалённая работа и Recovery); Kimi Work — резерв по необходимости, без параллельной адаптации и дублирования заданий. Владелец лично отмечает более стабильную удалённую работу Code с телефона; это не независимый тест и не полный допуск. B1/B2 выполняются через Code. Действующие полномочия и LIVE safety неизменны. [Действующий Roadmap](../../ROADMAP.md). Датированные исторические сведения ниже сохраняются; резервный Work проверяется только при фактической необходимости.

## Current checkpoint — 26.11.2026

[Block A engineering acceptance](BLOCK_A_ACCEPTANCE_20261126.md) · [current Roadmap](../../ROADMAP.md) · [three knowledge profiles](memory/README.md) · [KDR register](KIMI_DEFECTS_AND_REMEDIATION_REGISTER.md). Three Chat projects and five Skills accepted in reported/tested scope; GitHub #601–#604 source results merged. Full autonomy, actual installed/LIVE and cold restore not established. Earlier dated statuses below remain historical. COC and five canonical Skills remain authoritative; KDR-001 later owner acceptance recorded in checkpoint. Use accepted MAIN, not old #597 as current source. No new access authorized.


## Checkpoint G6.4 / G6.5 — 25.11.2026; исправление G6.5.1

**Проверенный SOURCE BASE:** `alkospacer123/market-pattern-discovery/main@e05bbd24db88f127a52f0ff1b7282d7c6919cd81`.

**Каноническая среда G6.5:** `CLIENT_ENVIRONMENT=KIMI_CHAT`; `EXECUTION_CONTEXT=AGENT_TOOL_ENABLED_CHAT`; `ENVIRONMENT_EVIDENCE=OPERATOR_CONFIRMED`; `KIMI_WORK=NOT_USED`; `KIMI_CODE=NOT_USED`; `GITHUB_PLUGIN_ACCESS=READ_WRITE_PASS`; `LOCAL_WINDOWS_ACCESS=NOT_PERFORMED`; `OFFLINE_EXECUTOR=NOT_CONFIRMED`; `LIVE=UNKNOWN`. Это свидетельство о GitHub source/documentation работе в Kimi Chat, не о Kimi Work, Kimi Code на Windows, INSTALLED или LIVE.

- **G6.4 — COMPLETE в заявленном scope:** оператор принял проверку GitHub READONLY и иерархии документации. `G6.4_CLIENT_ENVIRONMENT=UNKNOWN`: отдельная принадлежность G6.4 к клиенту не подтверждена, и атрибуция G6.5 на него не переносится.
- **Независимая сверка GPT — 19/19 Git blob SHA MATCH; иерархия Control Center признана корректной.** Результат передан оператором и имеет класс `REPORTED_ONLY`: Kimi не выдаёт его за собственную повторную сверку всех 19 blob.
- По переданному оператором решению GPT, **G6.5=PARTIALLY_ACCEPTED, MERGE_HOLD** до исправления атрибуции. G6.5.1 сохраняет исходный commit и добавляет один корректирующий commit в существующий Draft PR #598.

| Последующий статус | Действующее заключение |
| --- | --- |
| Полный `CODE_EXAM_PASS` | **NOT CONFIRMED** |
| Полный `HANDOFF_PASS` | **NOT CONFIRMED** до повторного независимого review и решения оператора |
| `OFFLINE_EXECUTOR` | **NOT_CONFIRMED** |
| `LIVE` | **UNKNOWN** |
| `COLD_RESTORE` | **NOT TESTED** |

**ENVIRONMENT_ATTRIBUTION_ERROR:** Kimi ошибочно отождествил наличие Agent-инструментов с использованием Kimi Work; ошибку обнаружили оператор и GPT. Исправление разделяет клиента, execution context, фактические инструменты и полномочия. Запрещено выводить среду только из Skills, plugins или sandbox. Статус: `CORRECTION_PENDING_GPT_REVIEW`.

Новый блок не отменяет датированные статусы и SHA ниже и не закрывает другие пункты [Roadmap](../../ROADMAP.md). Корректные исторические упоминания Work/Code сохранены. Следующий шаг — повторное GPT-ревью именно G6.5.1, затем решение оператора. Правила остаются в [экзамене и handoff](EXAM_AND_HANDOFF.md) и [Windows access gate](WINDOWS_WORKSPACE_AND_ACCESS.md). Никаких действий с FINAM, Intel, production, секретами или долговременной памятью checkpoint не разрешает и не подтверждает.


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

## Critical Operations Contract и Skills

- Общий вход: [Critical Operations Contract](../CRITICAL_OPERATIONS_CONTRACT.md). Перед критической задачей требуются контракт и **релевантные** Skills, не обязательно все пять.
- Канонические редакции: `recovery/kimi/skills/<name>/SKILL.md`. Резервные копии в `recovery/kimi/memory/{V20,ControlCenter,TRL}/skills/` должны быть побайтово идентичны соответствующему canonical файлу; одинаковые bytes имеют одинаковый Git blob SHA.
- Не редактируй backup самостоятельно. Старый `trl-reproducibility-review` не заменяет канонический `trl-repro-review`.
- Фактическая загрузка Skill, чтение canonical `SKILL.md` как `SOURCE_FALLBACK` и наличие backup — разные проверки. Manifest не доказывает установку или qualification.
