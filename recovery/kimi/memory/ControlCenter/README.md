# Control Center — постоянная база знаний Kimi

ACTIVE SOURCE, операторская панель V20, не broker truth.

**DRAFT REVIEW CANDIDATE, 25.11.2026.** Исходный snapshot `ec20cfcfbf7eebdd17862091f00fb20af11ad154`, контрольный MAIN `e05bbd24db88f127a52f0ff1b7282d7c6919cd81`. Не допуск к операциям и не проверка LIVE. KMS приняты только для ручного аналитического применения.

## Порядок работы

1. В начале новой сессии или существенной задачи открывать этот README. Разрешить актуальный MAIN и разрешённый ref. До Merge использовать указанный владельцем pinned Draft как кандидат/контекст, не выдавать за MAIN. После Merge постоянный адрес — `main:recovery/kimi/memory/ControlCenter/README.md`.
2. Прочитать [общий AGENTS](https://github.com/alkospacer123/market-pattern-discovery/blob/main/AGENTS.md), [профильный контракт](https://github.com/alkospacer123/market-pattern-discovery/blob/main/ControlCenter/docs/V20_CC07_COMMAND_CONTRACT.md), архитектуру и паспорт; далее только нужные документы и навыки. [Windows access gate](https://github.com/alkospacer123/market-pattern-discovery/blob/main/recovery/kimi/WINDOWS_WORKSPACE_AND_ACCESS.md) обязателен. Не повторять полный аудит при каждой задаче.
3. Ниже точные снимки Git blobs, не второй канон. Относительные ссылки внутри копий рассчитаны на исходный каталог: переходить по первичному пути из таблицы. Перед использованием изменяемого контракта сверить актуальный авторитетный исходник, ref, blob и дату. При расхождении действует подтверждённый канон; сообщить владельцу о drift. Обновлять снимки только согласованным PR.
4. При потере вложений/памяти восстановить нужный контекст через GitHub. При недоступности GitHub запросить проверенную независимую копию у владельца; не выдумывать знания. UNKNOWN/BLOCKED для зависимой части. В память — назначение проекта, путь к этому README, правило актуальной сверки и принципы взаимодействия; не хранить меняющиеся SHA, релизы, локальные пути, параметры и допуски.
5. Chat выбирает Chat/Work/Code по задаче; HANDOFF KMS-05 не передаёт права. Навыки доступны для ручного чтения, не гарантируют автоматическую загрузку. Любые права, исполнение, запись, Merge, deploy и LIVE отдельно gated. Никаких секретов и приватных данных в GitHub.

## Состав и provenance

| Файл | Канонический путь / источник | Git blob SHA | Authority |
| --- | --- | --- | --- |
| [Trading_Systems_Architecture_and_AI_Collaboration.md](Trading_Systems_Architecture_and_AI_Collaboration.md) | [Общий оригинал](../../Trading_Systems_Architecture_and_AI_Collaboration.md) | `66325ca5e9264bf449cc73e9a6bfc2bd42a16db0` | DRAFT NEW |
| [PROJECT_PASSPORT_CONTROL_CENTER.md](PROJECT_PASSPORT_CONTROL_CENTER.md) | [Первичный путь](https://github.com/alkospacer123/market-pattern-discovery/blob/ec20cfcfbf7eebdd17862091f00fb20af11ad154/recovery/PROJECT_PASSPORT_CONTROL_CENTER.md) | `9e649ee4820e1849580b85574f58d6084e798018` | PINNED_SOURCE_CHECK_MAIN |
| [CONTROL_CENTER.md](CONTROL_CENTER.md) | [Первичный путь](https://github.com/alkospacer123/market-pattern-discovery/blob/ec20cfcfbf7eebdd17862091f00fb20af11ad154/recovery/kimi/CONTROL_CENTER.md) | `afdf81f3c61a45a3642a7f91692601aa4c1fcf79` | PINNED_SOURCE_CHECK_MAIN |
| [V20_START_HERE_SOURCE_MAP.md](V20_START_HERE_SOURCE_MAP.md) | [Первичный путь](https://github.com/alkospacer123/market-pattern-discovery/blob/ec20cfcfbf7eebdd17862091f00fb20af11ad154/ControlCenter/docs/V20_START_HERE_SOURCE_MAP.md) | `b8e18e49f2504852821b98f152ba348350720c12` | PINNED_SOURCE_CHECK_MAIN |
| [V20_CC08_OPERATIONS.md](V20_CC08_OPERATIONS.md) | [Первичный путь](https://github.com/alkospacer123/market-pattern-discovery/blob/ec20cfcfbf7eebdd17862091f00fb20af11ad154/ControlCenter/docs/V20_CC08_OPERATIONS.md) | `18be465651d3747abe99f669967e374cde616252` | PINNED_SOURCE_CHECK_MAIN |
| [V20_CC07_COMMAND_CONTRACT.md](V20_CC07_COMMAND_CONTRACT.md) | [Первичный путь](https://github.com/alkospacer123/market-pattern-discovery/blob/ec20cfcfbf7eebdd17862091f00fb20af11ad154/ControlCenter/docs/V20_CC07_COMMAND_CONTRACT.md) | `7f42a76888df8ec9ce5b0fa1a14cb19b52d851b2` | PINNED_SOURCE_CHECK_MAIN |
| [skills/cc-incident-audit/SKILL.md](skills/cc-incident-audit/SKILL.md) | [Первичный путь](https://github.com/alkospacer123/market-pattern-discovery/blob/ec20cfcfbf7eebdd17862091f00fb20af11ad154/recovery/kimi/skills/cc-incident-audit/SKILL.md) | `1f2ed856cddf30d00b611985c26d7c48f79cf428` | DRAFT_SKILL |
| [skills/github-source-audit/SKILL.md](skills/github-source-audit/SKILL.md) | [Первичный путь](https://github.com/alkospacer123/market-pattern-discovery/blob/ec20cfcfbf7eebdd17862091f00fb20af11ad154/recovery/kimi/skills/github-source-audit/SKILL.md) | `513faaf196c678c5fbec3db0a2b0b2a05545b953` | DRAFT_SKILL |
| [skills/ai-engineering-handoff/SKILL.md](skills/ai-engineering-handoff/SKILL.md) | [Первичный путь](https://github.com/alkospacer123/market-pattern-discovery/blob/ec20cfcfbf7eebdd17862091f00fb20af11ad154/recovery/kimi/skills/ai-engineering-handoff/SKILL.md) | `0d8e521de93d777f9da5405721a814a8f6520384` | DRAFT_SKILL |

[MANIFEST.json](MANIFEST.json) — реестр; Git blob SHA-1 не SHA256. PINNED_SOURCE_CHECK_MAIN означает, что статус актуального MAIN нужно установить отдельно. DRAFT_CHANGED/DRAFT_SKILL — не утверждённый MAIN на данном срезе. Изменения источника требуют проверки свежести пакета, не блокируют использование актуального канона. INSTALLED/LIVE, воспроизводимость и доступ к данным доказываются отдельно.
