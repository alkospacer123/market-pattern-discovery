# Схемы и ограничения таблиц

- `ENTRY_FEATURES_H1/M15.csv`: одна строка на исходный signal Close, включая
  занятость/вне T1. `signal_id` = system|lifecycle|fold|instrument|Close ISO|side.
  Только причинные признаки; `feature_available_at=signal_time`,
  `context_available_at<=signal_time`. `breakout_atr` — положительное
  превышение предыдущего Donchian по стороне сделки. Все distance/slope/
  prior-move признаки знаковые по направлению LONG/SHORT. `context_ema`
  на H1 — опубликованная H4 EMA100, на M15 — опубликованная H1 EMA75.
  H1 EMA100 отдельно в `price_h1_ema100_atr`. `_cross_day` явно переносит
  предшествующие бары между днями; ATR и EMA также CROSS_DAY по протоколу.
- `SIGNAL_DISPOSITION_H1/M15.csv`: одна строка на тот же signal_id; accepted,
  frozen причина исполнения/пропуска. Никакого P&L неисполненным сигналам.
- `EXECUTION_DIAGNOSTICS.csv`: исполненные входы; signed NEXT_OPEN gap / ATR
  сигнальной свечи известен после signal decision, в execution-open event.
  Совпадение wall timestamp не делает его доступным на более ранней фазе.
  Он не входит в ENTRY_FEATURES и не используется в hypothesis ranking.
- `OUTCOME_GROUPS_H1/M15.csv`: фактический CONTROL вход. Взаимоисключающие
  outcome_group: INITIAL_STOP, TRAILING_NEGATIVE, TRAILING_POSITIVE,
  TRAILING_ZERO, OPEN. >=2R — дополнительный пересекающийся флаг по
  фактическому итоговому Gross R, не по touched MFE. OPEN не имеет Gross R.
- `MFE_pre_stop_R0`, `MAE_executable_R0`: консервативные stop-first bounds
  PR560; exit-bar HL не включены в гарантированный путь до стопа. Observed
  upper extrema включают весь exit bar и не доказывают порядок до выхода.
  Gross R нормирован на неизменный initial CONTROL risk. High/Low пути,
  latency и early adverse — признаки исхода, не признаки входа.
- `first_favorable_*`: первое строго >0 движение. Open точен; intrabar
  time_lower / time_bound задают интервал, bar Close — верхняя граница.
  `_minutes_bound` — wall minutes от signal Close (включает ночные gaps);
  `_bar` — номер наблюдаемой execution-свечи. Аналогично `first_half_R_*`
  для >=0.5R. Медианы времени считаются только среди наблюдённых; missing
  не становится нулём. NOT_OBSERVED / AMBIGUOUS_EXIT_BAR / CENSORED отдельно.
- `FEATURE_DISTRIBUTIONS.csv`: p25/median/p75/N/missing каждого признака по
  исходам, winners=R>0, losers=R<0. ZERO и OPEN не входят в winners/losers.
- `FEATURE_THRESHOLDS.csv`: development-квантили 1/3 и 2/3 **исполненных**
  входов, включая OPEN, без outcome при вычислении. `LOW <=q1`,
  `MID q1<x<=q2`, `HIGH >q2`, `MISSING` отдельно. Ties не разделяются.
- `FEATURE_BUCKETS.csv`, `OUTCOME_SUMMARY.csv`, `INSTRUMENT_DIRECTION.csv`:
  N включает OPEN, CLOSED отдельный denominator для initial_stop_share,
  mean/median Gross R и large_winner_share. MAE/MFE/time median охватывает
  входы группы, включая доступный путь OPEN. `share_of_all_large_winners`
  — доля всех CLOSED >=2R данной системы, находящихся в группе.
  Инструмент/сторона/год атрибутируются signal Close МСК, не exit-year.
- `STABILITY.csv`: HIGH–LOW терциль по общим development-порогам; разрезы
  не переопределяют пороги. Leave-one-instrument-out не переобучает пороги.
  `BREAKOUT_05_STRATA.csv`: аналогичная разница >=0.5 против <0.5; контекстный
  volatility tercile задаётся общими development-квантилями ATRRatio.
- `BREAKOUT_05_STANDARDIZED.csv`: только общие страты с обеими группами;
  вес n_high*n_low/(n_high+n_low), покрытие раскрыто. Не causal adjustment.
- `*_ci95_*`: paired percentile month-cluster bootstrap по 24 signal months
  всех инструментов, 2000, seed560518. Quarter sensitivity — 8 кварталов.
  Без поправки на multiple comparisons; широкие CI/SMALL не скрыты.
- `POST_STOP.csv`: CONTROL INITIAL_STOP, остаток дня и 1/2 следующих
  observed trading dates; стоповая свеча исключена, intrabar unknown.
  Полнота окна требует ещё следующую наблюдаемую дату; иначе CENSORED.
  COMPLETE не аттестует наличие каждого ожидаемого биржевого бара.
  `recovery_vs_adverse_1p5R_order`: сравнение порядков интервалов; один
  intrabar интервал для обеих границ → AMBIGUOUS_SAME_BAR.
- `POST_STOP_SUMMARY.csv`: проценты и cluster CI только по COMPLETE окнам.
  `recovery_first`/`only`/`adverse_first`/`ambiguous` не исчерпывают окна:
  adverse-only и neither доступны в per-trade POST_STOP.
- `MONTHLY_BASELINE.csv`: исходный реализованный Gross R по frozen exit-label
  МСК, включая 00:00 следующего дня. Это не actual intrabar exit calendar,
  не MTM/cash, не гипотетическое исключение сделок. Нулевой месяц —
  наблюдаемое отсутствие закрытий, не заявление о полном N4 покрытии.
- `CONFLICT_EXAMPLES.csv`: для каждого bucket с INITIAL_STOP и >=2R —
  первый по signal time экземпляр каждого исхода. Детерминированные примеры
  пересечения признаков, не подбор убедительных иллюстраций.

Gross R — исследовательская нормировка. Frozen H1 C1 не менялся; M15 gross
only. Executable net, денежные улучшения, исторические ГО/комиссии/скольжение
и сохранность победителей при изменениях не валидированы. Это диагностика,
не новый backtest и не торговая рекомендация.
