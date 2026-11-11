# Схемы и определения

- `CONTROL/BE1_trades.csv`: фактически CLOSED; `OPEN.csv` и `snapshots.csv`
  содержат незакрытые позиции без выдуманного исхода. `initial_risk` —
  неизменный R0 в единицах цены; `gross_R=side*(exit-entry)/R0`.
  `entry_time=signal_time` — frozen timestamp следующего смежного Open,
  `execution_bar_close` — Close свечи исполнения. `exit_time` — Close свечи
  стопа, `exit_bar_open_time` — её Open; точное intrabar время неизвестно.
- `stops.csv.gz`: stop-first на каждой наблюдаемой свече в позиции;
  `active_stop` действует до её проверки; `proposal` — обычный trailing;
  `next_stop` действует только со следующей наблюдаемой свечи. Exit-bar
  не имеет proposal/next_stop/extreme_after. `BE1_reached_now` — впервые
  наблюдён +1R на полностью пережитой свече (также диагностика CONTROL),
  `BE1_raised_now` — именно BE1 усилил stop после обычного trailing;
  `BE1_eligible_next_observed` — порог достигнут, floor доступен BE1.
  `BE1_activation_time` в trade — первое достижение, не обещание fill без убытка.
- `stop_source` INITIAL/TRAIL/BE1 описывает последнее фактическое усиление.
  Frozen `exit_type` INITIAL_STOP/RATCHETED_STOP сохраняется: BE1 тоже
  ratchet; его источник виден отдельно. `trailing_updates` считает только
  фактические усиления обычным trailing, BE1 raise сюда не включается.
- `signals.csv.gz`: все исходные ненулевые signal Close, решения SESSION,
  занятость, pending и фактический NEXT_OPEN. ID последовательно меняются
  с занятостью; matching всегда instrument + signal_time + direction.
- `marks.csv.gz`: наблюдаемые Close marks и накопленный realized R.
  `PORTFOLIO_CURVES.csv.gz` — объединённая шкала, перенос последнего mark
  без синтетических свечей; до старта инструмента вклад в сумму отсутствует.
- `MONTHLY.csv`: все 24 наблюдаемых портфельных месяца МСК. CLOSED — сумма
  exit R, MTM — разность month-end совокупного realized+unrealized.
  `COVERAGE.csv` явно отмечает NO_DATA/PARTIAL_N4, scheduled и прочие gaps
  не различаются без биржевого календаря. Численный sign tolerance 1e-8
  относится только к отчётной арифметике, не к торговому правилу +1R.
- `SUMMARY.csv`: общие и годовые trade-метрики по exit-year; DD от нулевого
  начала периода, MTM с переносом исходного mark до года. CLOSED DD
  сортирует одновременные события по instrument/trade_id как frozen.
- `TRADE_COMPARISON.csv`: общие, новые, пропущенные входы, реальные исходы
  и сроки. Missing/OPEN R пуст, не ноль. `negative_trailing_prevented` —
  исходный отрицательный RATCHETED_STOP сопоставлен с BE1 CLOSED R >=0;
  пропущенные и OPEN выделены отдельно. `EARLY_PROFITABLE_EXITS.csv` —
  исходные R>0, сопоставленный BE1 фактически закрыт раньше.
- `ORIGINAL_GE_2R_WINNERS.csv` / `BY_YEAR.csv`: фиксированная исходная
  когорта, год по signal time. Полный набор >=2R каждого replay отдельно
  в SUMMARY; skipped/OPEN не объявляются CLOSED-нолём.
- `MECHANISM_SUMMARY.csv`: количество/вклад фактических отрицательных
  trailing, все отрицательные/нулевые сделки, активации и adverse BE gaps.
  Год по exit/event time; счёт активаций включает терминальные OPEN.
- `NORMALIZED_COST_SENSITIVITY.csv`: заданное единое вычитание R на CLOSED
  round trip; не влияет на входы и не является денежной исполнимостью.
- `AUDIT.json`, `DEVELOPMENT_CONTROL.json`, `control/*`,
  `INDEPENDENT_VERIFICATION.json`, `SYNTHETIC_TESTS.json`: gates и scope.
  `features/*` содержит только derived features, OHLC исключены.
- `CODE_FREEZE.json`, `REPEATABILITY.json`, `SHA256SUMS`: freeze, квитанция
  сравнения всех generated artifacts и полный deliverable inventory.
