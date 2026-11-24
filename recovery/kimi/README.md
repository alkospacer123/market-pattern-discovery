# Kimi Phase II — три логических проекта знаний

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

## Полная квалификация Kimi и проверка месячного Pro — 23.11.2026

[Детальная программа этапа II: обучение трём системам, экзамены Chat/Work/Code, самостоятельное чтение GitHub, изолированные тесты, GPT↔Kimi handoff, устойчивость между сессиями, лимиты и итоговая оценка](PHASE_II_QUALIFICATION_AND_PRO_LIMITS_20261123.md). Приоритет качество/безопасность, а не ускорение ARMED. Владелец сохраняет роботов HALTED до отдельного согласованного практического наблюдения; учебные материалы не являются разрешением на LIVE-команды. Исторические pins и статусы в документе ниже не переписываются задним числом.

**G1.1–G1.3, 23.11.2026:** [журнал source-аудитов Work и Chat, оценки и расход месячного Pro](G1_CHAT_WORK_READONLY_SCORECARD_20261123.md). Это принятая по отчётам READONLY-проверка GitHub, не полный экзамен Chat/Code, не offline test и не LIVE.

**G2.1 V20, 23.11.2026:** [проверенная карта знаний, 96/100 (обучающий этап), ограничения и обнаруженные устаревшие CC blob SHA](G2_V20_TRAINING_REVIEW_20261123.md). Не является экзаменом, offline test или допуском в LIVE.

**G2.2A Control Center, 23.11.2026:** [проверка инженерной карты, 28/28 source blob SHA, 96/100, технические нюансы и квота Pro](G2_CC_TRAINING_REVIEW_20261123.md). Только обучение, без Code-exam и LIVE.

**G2.3A TRL, 23.11.2026:** [глубокое обучение и независимая проверка 54/54 Git blob SHA, 97/100, ограничения воспроизводимости и квота Pro](G2_TRL_TRAINING_REVIEW_20261123.md) — не экзамен и не replay.

**Контроль качества этапа II:** [журнал подтверждённых ошибок, неподтверждённых возможностей и независимых повторных проверок Kimi](KIMI_DEFECTS_AND_REMEDIATION_REGISTER.md). [Усиленные условия G2–G9](PHASE_II_QUALIFICATION_AND_PRO_LIMITS_20261123.md#9-усиление-критериев-приёмки-и-журнал-недостатков--решение-владельца-23112026): без ускорения и снижения порогов, прямая обратная связь Kimi после G2.3C TRL, синтетический кодовый ретест повторяющегося Protect3-пробела и полный GPT-OUTAGE перед финальной документацией.

**Усиление 23.11.2026, V20 + TRL:** [программа особо строгих Code/replay, негативных и слепых испытаний](V20_TRL_ENHANCED_PRACTICAL_ACCEPTANCE_20261123.md); [TRL G2.3B 12 сценариев, 25/25 discovery SHA + 4/4 data SHA, формирующая оценка 98/100, временная зона требует уточнения](G2_TRL_TRAINING_REVIEW_20261123.md). До TRL G2.3C это только обучение, не Chat/Code квалификация; финальный GPT-OUTAGE и Recovery впереди.

**G2.3C TRL independent exam 23.11.2026:** [проверенный протокол 39/40 PASS, 30/30 Git SHA, сохранённый KDR-001 и отсутствие Code/replay](G2_TRL_INDEPENDENT_EXAM_REVIEW_20261123.md). Три Chat-экзамена сданы (V20 59/60, CC 58/60, TRL 39/40); перед практикой — прямой разговор Kimi по [журналу](KIMI_DEFECTS_AND_REMEDIATION_REGISTER.md). Ни одна теория не даёт LIVE-допуска.

**Postmortem Kimi и независимые улучшения**, 23.11.2026: KDR-001 признан Kimi и остаётся открыт до Code negative/positive/reachability теста и новых слепых проверок; KDR-003 не доказан, часовой пояс неизвестен. [Независимый обзор и 10 мер надёжности](KIMI_RELIABILITY_IMPROVEMENTS_20261123.md), [текущий журнал KDR](KIMI_DEFECTS_AND_REMEDIATION_REGISTER.md). Текущий Pro 23,22%, Code 0%, автономная квалификация впереди.

**G4.0 Kimi Code source-only, 24.11.2026:** [итоги согласования RLI (7 ACCEPT / 3 MODIFY) и безопасный source-only вход](G4_RELIABILITY_CONSENSUS_AND_CODE_ENTRY_GATE_20261124.md). Практические запуски требуют отдельной доказанной OS isolation; KDR-001 по-прежнему открыт, разрешения LIVE не изменены.

**Memory & Skills Qualification (24.11.2026):** [установка Memory Space, MyKimi Self-growth, десять M01–M10, подготовка пяти `SKILL.md` и независимые тесты памяти/переноса](MEMORY_AND_SKILLS_QUALIFICATION_20261124.md). Только утверждённый план; создание записей памяти и Skills в аккаунте пока NOT_VERIFIED, не открывает новые права Code/LIVE.
