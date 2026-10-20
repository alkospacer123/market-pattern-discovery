# Как читать диагностические CSV

Основные новые наблюдения — `H1_TRADE_FORENSICS.csv`, `M15_TRADE_FORENSICS.csv`,
`POST_STOP_1D_2D.csv`, `STOP_VARIANT_*`. Протокол и REPORT_RU определяют единицы
и population. Все CSV с WF имеют lifecycle/fold: его нельзя прибавлять к основному
неперекрывающемуся Baseline + historical OOS. OPEN не принудительно закрывались.

## Frozen и новые поля

`H1_TRADES.csv` / `M15_TRADES.csv` сохраняют схему повторно использованного
движка PR #557 для точной сверки, включая технические поля прежней работы.
В этой работе **ни один разрешённый вариант не выполняет partial TP**:
`partial_executed=False`. `part1` и `part2` — две бухгалтерские половины условной
единицы, закрывающиеся одновременно по одному стопу; это не реальное дробное
количество контрактов и не новая торговая альтернатива. `target_price` не участвует
в исполнении разрешённых вариантов. `initial_quantity=1` — нормированная единица,
не проверенное целочисленное количество production.

Legacy `reached_2R` в этих журналах означает наблюдаемый диапазон свечи и может
включать свечу выхода. Его нельзя читать как доказательство достижения +2R **до**
стопа. Аналогично унаследованные M15 `MFE_R`/`MAE_R` сохранены ради reconciliation.
Для новой причинно ограниченной диагностики нужны:

- `MFE_pre_stop_R0`: favorable Open плюс диапазоны пережитых execution bars;
  exit-bar favorable High/Low не предполагается достигнутым до стопа.
- `MAE_executable_R0`: adverse наблюдения пережитых баров и фактический exit fill;
  не включает возможное дальнейшее adverse движение после исполнения в exit bar.
- `MFE_observed_upper_R0` / `MAE_observed_upper_R0`: полный наблюдаемый диапазон
  удержанных свечей, включая exit bar; это ретроспективная верхняя граница.
- `MFE_before_stop_ge_*`: HIT_BEFORE_STOP / AMBIGUOUS_EXIT_BAR / NOT_OBSERVED.
- `giveback_R0`: max(0,MFE−exitR), включая уход ниже entry.
  `positive_MFE_surrendered_R0` показывает только возвращённую положительную MFE;
  `loss_below_entry_R0` — остальной убыток ниже entry.

У каждой альтернативной сделки свой исходный Risk0. LOW_FOLLOW_THROUGH имеет
сферу CONTROL_ONLY и порог +0.5 CONTROL R0. Post-stop всегда использует CONTROL
R0. В comparison `variant_own_R` и `variant_exit_in_CONTROL_R0` различны по смыслу.

## Метки времени и наблюдаемое время

Все новые calendar tables — MSK. Frozen timestamps H1/M15 относятся к Close
свечи исполнения, включая выход на её Open. Они сохраняются для reconciliation.
`actual_exit_time_lower/upper` показывают физический интервал исполнения: Open
точен при exit_at_open, intrabar touch ограничен Open/Close. Timestamp первой
intrabar excursion — верхняя граница её интервала, не точная секунда события.
H1 trigger/activation в сравнении — исходные frozen event/bar labels; candidate
только из завершённого прошлого бара, действует перед более поздним допустимым
баром. Физическую секунду активации из Close label не следует домысливать.

`wall_clock_minutes` и `observed_trading_minutes` используют frozen Close labels
и число допустимых баров. Это не подтверждённый биржевой календарь. Дополнительные
`observed_exposure_minutes_lower/upper` отделяют выход на Open и неизвестную
долю exit bar. Неприсутствующие свечи не синтезировались.

## После стопа и исполнение

Post-stop начинается со следующего наблюдаемого бара, а не с остатка High/Low
свечи стопа. Окно включает остаток stop-date и следующие 1/2 полные наблюдаемые
даты Open MSK. COMPLETE_OBSERVED_DATE_WINDOW не доказывает наличие всех ожидаемых
биржевых свечей; CENSORED не равен no-hit. Entry-touch bars и completed-close
crossings — два разных наблюдаемых счёта. Точное количество внутрисвечных
пересечений UNKNOWN. Одновременные first hits получают AMBIGUOUS_SAME_BAR,
кроме порядка, установленного Open.

CAPITAL_FEASIBILITY использует статический registry только для grid/one-lot
чувствительности. Эти рублёвые расстояния не являются историческим денежным
backtest. H1 C1 — нормированные расходы, M15 GROSS_ONLY; executable qty, Net,
рублёвая просадка и cash-return остаются NOT_VALIDATED.
