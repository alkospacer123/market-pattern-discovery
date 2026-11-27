# Control Center — инженерный журнал

[Текущий статус](STATUS.md) · [Общие правила](../AGENTS.md)

Журнал GPT/Kimi: добавляй записи в конец после значимого результата, принятого решения, незавершённого checkpoint или передачи задачи. Не записывай каждый запрос, действие или полный отчёт; ссылки на PR, commit и доказательства достаточны. Старые записи не переписывай; исправления — новой записью со ссылкой на исходную.

Формат одной записи:

- Дата/TZ, исполнитель и среда; задача.
- Результат и статус; что изменено или не выполнено.
- Проверки и доказательства: точные SHA/PR/артефакты, PASS/FAIL/SKIP/UNKNOWN по факту.
- Решения владельца, остаточные риски/блокеры.
- Следующий шаг и нужное разрешение.

Не включай секреты, идентификаторы счетов, приватные журналы и необезличенные брокерские данные. Запись не разрешает Merge, установку или LIVE. Записывай в рамках разрешённой ветки/PR; Draft не равен принятому MAIN. Если исход записи неизвестен, сначала проверь HEAD/содержимое, не повторяй вслепую.

## Записи

Первые содержательные записи добавит профильный чат после сверки источников. Исторические записи обозначать датой события и датой внесения; не реконструировать неизвестные факты.

### 27.11.2026 — профильная сводка C3.2 (GPT, GitHub READONLY)

- 20.11 (событие): историческое CC-07 install PASS/`already_current`, operator `10de325be0335733a248c412943f39d45bd93c62`, adapter `ef2fa2cd6b0ddfefc920548995274f123c5884bf`. START/PAUSE и отдельные STOP/RESTART в ограниченном объёме; RECOVER при естественном HALT, all-three и независимый FINAM/SLTP NOT_VERIFIED. [CC-08](docs/V20_CC08_OPERATIONS.md).
- 22–23.11: актуальная V20 SOURCE-навигация, CC-03/H1/8501 как история. Frozen CC-03 historical scope_audit exit 1 не LIVE PASS. [SOURCE map](docs/V20_START_HERE_SOURCE_MAP.md), [CC-07](docs/V20_CC07_COMMAND_CONTRACT.md).
- 25–26.11: CC-G53-01, synthetic false HEALTHY с positions_local=1/stops_local=0. [#602](https://github.com/alkospacer123/market-pattern-discovery/pull/602) MERGED `e70cfed5db274530ba9687f5a9b13f2290fde1e7`; локальный FAULT/LOCAL_POSITION_WITHOUT_STOPS и UNKNOWN при неполной экспозиции; исторические 14 BASE fails → 14 DERIVED passes, Linux 729 PASS/57 SKIP/0 FAIL, не Windows/LIVE. [Отчёт](docs/V20_HEALTH_EXPOSURE_FIX_20261126.md). INSTALLED/FINAM UNKNOWN.
- 26–27.11: [#603](https://github.com/alkospacer123/market-pattern-discovery/pull/603), [#609](https://github.com/alkospacer123/market-pattern-discovery/pull/609) MERGED: разделены frozen CC-03/active V20 и допущен точный C3 docs scope. Исходный #608 HEAD `f6c28ad4027fdc1fdfc8c279671f5c3001f3bd1e`, CC docs/Main Admission PASS. Skill blob `4ba0b325dd6ba7ee6129a3316b8313ea9fd7835d`, 9/9 mirror pairs MATCH по профильному HANDOFF. Original patch отсутствует; STATUS/JOURNAL адаптированы из переданных файлов с сохранением шаблона/истории. Actual fallback, отключение Skill и новые diagnostics ещё требуют проверки/интеграции. Intel/FINAM/LIVE не проверялись.
