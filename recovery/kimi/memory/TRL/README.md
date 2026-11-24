# Trading Research Lab — постоянная база знаний Kimi

RESEARCH ONLY: Research / Evolution / Journal, не LIVE.

**DRAFT REVIEW CANDIDATE, 25.11.2026.** Исходный snapshot `ec20cfcfbf7eebdd17862091f00fb20af11ad154`, контрольный MAIN `e05bbd24db88f127a52f0ff1b7282d7c6919cd81`. Не допуск к операциям и не проверка LIVE. KMS приняты только для ручного аналитического применения.

## Порядок работы

1. В начале новой сессии или существенной задачи открывать этот README. Разрешить актуальный MAIN и разрешённый ref. До Merge использовать указанный владельцем pinned Draft как кандидат/контекст, не выдавать за MAIN. После Merge постоянный адрес — `main:recovery/kimi/memory/TRL/README.md`.
2. Прочитать [общий AGENTS](https://github.com/alkospacer123/market-pattern-discovery/blob/main/AGENTS.md), [профильный контракт](https://github.com/alkospacer123/market-pattern-discovery/blob/main/TradingResearchLab/AGENTS.md), архитектуру и паспорт; далее только нужные документы и навыки. [Windows access gate](https://github.com/alkospacer123/market-pattern-discovery/blob/main/recovery/kimi/WINDOWS_WORKSPACE_AND_ACCESS.md) обязателен. Не повторять полный аудит при каждой задаче.
3. Ниже точные снимки Git blobs, не второй канон. Относительные ссылки внутри копий рассчитаны на исходный каталог: переходить по первичному пути из таблицы. Перед использованием изменяемого контракта сверить актуальный авторитетный исходник, ref, blob и дату. При расхождении действует подтверждённый канон; сообщить владельцу о drift. Обновлять снимки только согласованным PR.
4. При потере вложений/памяти восстановить нужный контекст через GitHub. При недоступности GitHub запросить проверенную независимую копию у владельца; не выдумывать знания. UNKNOWN/BLOCKED для зависимой части. В память — назначение проекта, путь к этому README, правило актуальной сверки и принципы взаимодействия; не хранить меняющиеся SHA, релизы, локальные пути, параметры и допуски.
5. Chat выбирает Chat/Work/Code по задаче; HANDOFF KMS-05 не передаёт права. Навыки доступны для ручного чтения, не гарантируют автоматическую загрузку. Любые права, исполнение, запись, Merge, deploy и LIVE отдельно gated. Никаких секретов и приватных данных в GitHub.

## Состав и provenance

| Файл | Канонический путь / источник | Git blob SHA | Authority |
| --- | --- | --- | --- |
| [Trading_Systems_Architecture_and_AI_Collaboration.md](Trading_Systems_Architecture_and_AI_Collaboration.md) | [Общий оригинал](../../Trading_Systems_Architecture_and_AI_Collaboration.md) | `66325ca5e9264bf449cc73e9a6bfc2bd42a16db0` | DRAFT NEW |
| [PROJECT_PASSPORT_TRL.md](PROJECT_PASSPORT_TRL.md) | [Первичный путь](https://github.com/alkospacer123/market-pattern-discovery/blob/ec20cfcfbf7eebdd17862091f00fb20af11ad154/recovery/PROJECT_PASSPORT_TRL.md) | `0420ec83a8328ce625c2d699062ef9ec75018e43` | PINNED_SOURCE_CHECK_MAIN |
| [TRL.md](TRL.md) | [Первичный путь](https://github.com/alkospacer123/market-pattern-discovery/blob/ec20cfcfbf7eebdd17862091f00fb20af11ad154/recovery/kimi/TRL.md) | `eac1180335ea89c52bcefcb40983a3a423e9d662` | PINNED_SOURCE_CHECK_MAIN |
| [TRL-NOV-2026-KIMI-START-HERE.md](TRL-NOV-2026-KIMI-START-HERE.md) | [Первичный путь](https://github.com/alkospacer123/market-pattern-discovery/blob/ec20cfcfbf7eebdd17862091f00fb20af11ad154/TradingResearchLab/reports/TRL-NOV-2026-KIMI-START-HERE.md) | `20de0d0f5e8ad56323321de931265e4e57e61278` | PINNED_SOURCE_CHECK_MAIN |
| [RESEARCH_METHODOLOGY.md](RESEARCH_METHODOLOGY.md) | [Первичный путь](https://github.com/alkospacer123/market-pattern-discovery/blob/ec20cfcfbf7eebdd17862091f00fb20af11ad154/TradingResearchLab/research/RESEARCH_METHODOLOGY.md) | `334129b6ca15210015e25df6f59c324afd033537` | DRAFT_CHANGED |
| [OPERATING_CYCLE.md](OPERATING_CYCLE.md) | [Первичный путь](https://github.com/alkospacer123/market-pattern-discovery/blob/ec20cfcfbf7eebdd17862091f00fb20af11ad154/TradingResearchLab/OPERATING_CYCLE.md) | `8e770c0b282d7f41ae611f608f98e4fe19bd9545` | DRAFT_CHANGED |
| [RESEARCH_CARD_TEMPLATE.md](RESEARCH_CARD_TEMPLATE.md) | [Первичный путь](https://github.com/alkospacer123/market-pattern-discovery/blob/ec20cfcfbf7eebdd17862091f00fb20af11ad154/TradingResearchLab/research/RESEARCH_CARD_TEMPLATE.md) | `a59264b5d6cee8f460f5bf1d0bf83953eae3e92e` | DRAFT_CHANGED |
| [TRL-NOV-2026-ARTIFACT-MANIFEST.md](TRL-NOV-2026-ARTIFACT-MANIFEST.md) | [Первичный путь](https://github.com/alkospacer123/market-pattern-discovery/blob/ec20cfcfbf7eebdd17862091f00fb20af11ad154/TradingResearchLab/reports/TRL-NOV-2026-ARTIFACT-MANIFEST.md) | `725da79a35484a7385a8f9b98c3d7c59bc4e19e3` | PINNED_SOURCE_CHECK_MAIN |
| [TRL-NOV-2026-FINAL-CLOSEOUT.md](TRL-NOV-2026-FINAL-CLOSEOUT.md) | [Первичный путь](https://github.com/alkospacer123/market-pattern-discovery/blob/ec20cfcfbf7eebdd17862091f00fb20af11ad154/TradingResearchLab/reports/TRL-NOV-2026-FINAL-CLOSEOUT.md) | `ec06839fd233f9909eead53e82b9b7d1d7868fb8` | PINNED_SOURCE_CHECK_MAIN |
| [skills/trl-repro-review/SKILL.md](skills/trl-repro-review/SKILL.md) | [Первичный путь](https://github.com/alkospacer123/market-pattern-discovery/blob/ec20cfcfbf7eebdd17862091f00fb20af11ad154/recovery/kimi/skills/trl-repro-review/SKILL.md) | `16ed2cb8ccc39578e0f8bee937c5495a3a25efdd` | DRAFT_SKILL |
| [skills/github-source-audit/SKILL.md](skills/github-source-audit/SKILL.md) | [Первичный путь](https://github.com/alkospacer123/market-pattern-discovery/blob/ec20cfcfbf7eebdd17862091f00fb20af11ad154/recovery/kimi/skills/github-source-audit/SKILL.md) | `513faaf196c678c5fbec3db0a2b0b2a05545b953` | DRAFT_SKILL |
| [skills/ai-engineering-handoff/SKILL.md](skills/ai-engineering-handoff/SKILL.md) | [Первичный путь](https://github.com/alkospacer123/market-pattern-discovery/blob/ec20cfcfbf7eebdd17862091f00fb20af11ad154/recovery/kimi/skills/ai-engineering-handoff/SKILL.md) | `0d8e521de93d777f9da5405721a814a8f6520384` | DRAFT_SKILL |

[MANIFEST.json](MANIFEST.json) — реестр; Git blob SHA-1 не SHA256. PINNED_SOURCE_CHECK_MAIN означает, что статус актуального MAIN нужно установить отдельно. DRAFT_CHANGED/DRAFT_SKILL — не утверждённый MAIN на данном срезе. Изменения источника требуют проверки свежести пакета, не блокируют использование актуального канона. INSTALLED/LIVE, воспроизводимость и доступ к данным доказываются отдельно.
