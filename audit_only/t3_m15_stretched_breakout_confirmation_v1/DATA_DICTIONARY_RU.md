# Схемы и смысл результатов

Все timestamp — ISO 8601 Europe/Moscow (+03:00). Числа float сериализованы
round-trip, NaN/None — пустые поля. Gzip mtime=0. Сортировка детерминирована.
Отсутствие source history не равно нулевому результату; COVERAGE явно NO_DATA.

- `CONTROL/CONFIRM_trades.csv`: CLOSED сделки. `signal_time` и сохранённое
  frozen `entry_time` означают исходный signal Close. Физическое время входа —
  **actual_entry_time**, execution-bar Close — `execution_bar_close`.
  `entry_price` — его Open. `confirmed` — факт задержанного исполнения.
  `initial_risk` = abs(entry_price-initial_stop); `gross_R` = signed exit-entry/R0.
  `bars_held` и `holding_minutes` сохраняют frozen отсчёт от исходного сигнала;
  у задержанного входа включают ожидание. Они не равны времени фактической позиции.
  MAE/MFE frozen stop-first: exit-bar High/Low не добавляются до исполнения стопа.
- `*_OPEN.csv`, `*_snapshots.csv`: цензурированные OPEN и переносы месяца.
  unrealized_gross_R — mark исходной позиции, не фиктивная закрытая сделка.
  Snapshots не суммируют как дополнительные сделки.
- `*_signals.csv.gz`: все исходные пробои с frozen H1 gate, включая вне T1,
  занятость и резерв. `trade_id` может переиспользоваться после отмены; устойчивый
  `signal_id` = instrument|signal_time|direction. `stretched_delay` — признак
  >=0.5 в альтернативе, даже у неразрешённых сигналов; фактическая попытка имеет
  непустой trade_id. `confirmation_*` — информация только после следующего Close.
  `ready_time` — Close, после которого допускается непосредственно следующий Open.
  `entry_accepted` — действительно исполнен, а не предварительное разрешение.
- `*_stops.csv.gz`: прежний активный stop, stop_hit, gap и proposal/next_stop после
  выжившей свечи. На exit строке будущий trail отсутствует.
- `*_marks.csv.gz`: каждый наблюдённый Close, накопленные realized/unrealized/MTM R,
  фактический position_trade_id и отдельный waiting_signal_id/stage. Сигнальное
  ожидание не считается фактической позицией. `*_occupancy.csv`: число свечей
  с фактическим stop test; denominator=len(bars)-1 — frozen соглашение PR518.
- `features/*.csv.gz`: производные ATR, prior Donchian, доступный H1 контекст,
  исходный Signal и timestamp. Полные исходные OHLC/Volume не сохраняются.
- `MONTHLY.csv`: CLOSED по frozen exit-bar Close; MTM — изменение суммарной
  month-end MTM от предыдущего месяца с forward-fill последней отметки каждого
  инструмента. PARTIAL_N4 в 2023 раскрыт. `SUMMARY.csv`: весь development и
  отдельно exit-year 2023/2024. OPEN_at_period_end — позиции на последней
  наблюдаемой отметке года. >=2R — фактические CLOSED R. DD включает начальный 0.
- `PORTFOLIO_CURVES.csv.gz`: нормированные R, не cash equity и не R15-compounding.
  MTM учитывает High/Low только через frozen stop logic; внутрисвечная equity
  неизвестна. Это Close-mark DD, не максимальная intrabar денежная просадка.
- `MONTH_SIGN_TRANSITIONS.csv`: все пары месяц × CLOSED/MTM; знак при tolerance
  1e-8; `sign_changed` включает переход через ноль.
- `TRADE_COMPARISON.csv`, `NEW_AND_MISSED_ENTRIES.csv`: сопоставление исходных
  сигналов независимо от меняющихся counters; общие CLOSED имеют отдельную
  декомпозицию в CONTROL R0: exit delta − entry penalty = delta PNL.
- `LOST_AND_REDUCED_WINNERS.csv`: исходные положительные CLOSED, пропущенные,
  ставшие <=0, OPEN либо уменьшившие положительный R. Пропуск включает прямой
  отказ подтверждения и последующие изменения занятости; CONFIRM_reason раскрыт.
- `ORIGINAL_GE_2R_WINNERS.csv`, `ORIGINAL_GE_2R_BY_YEAR.csv`: фиксированная исходная
  когорта, год по signal Close. Её альтернативный CLOSED вклад включает <2R/убытки;
  пропуски и OPEN не маскируются новыми победителями. Общая новая когорта >=2R
  показана отдельно в SUMMARY (год там по exit Close).
- `MECHANISM_SUMMARY.csv`: попытки со свободным слотом по signal year, вынос,
  результат единственной свечи, обе смежности, T1 и прежние малые NEXT_OPEN.
- `NORMALIZED_COST_SENSITIVITY.csv`: из Gross каждого CLOSED вычитаются заданные
  round-trip cost_R+slippage_R. Это чувствительность, не historical executable Net.
- `CAPITAL_FEASIBILITY.json`: R15/nominal cap и отсутствующие денежные данные;
  integer qty/денежная доходность/ГО/рублёвая DD не валидированы.
- `control/*`: свежий полный CONTROL и authentication receipt; единственная
  ретроспективная обработка 2025–2026, не альтернативный OOS.
- `DEVELOPMENT_CONTROL.json`, `INDEPENDENT_VERIFICATION.json`, `SYNTHETIC_TESTS.json`,
  `AUDIT.json`, `CODE_FREEZE.json`, `REPEATABILITY.json`: границы и результаты
  проверки. Внешней человеческой/отдельной агентской экспертизы нет.
