# IntradayLab — Final Independent Trading Logic Audit

Дата: 2026-10-10, Europe/Moscow. Исходный Draft [#451](https://github.com/alkospacer123/market-pattern-discovery/pull/451), строго HEAD `2cfab348011c874e5d8e98787855f86b75fb5e43`. Фактический main до аудита: `f5dec0a73bf1273f9490502fbc0b9588f9315260`.

## Вердикт

**TRADING LOGIC PASS — для объявленной условной исследовательской модели.** Независимое восстановление всех возможностей и состояний совпало с опубликованными сигналами, исполнениями, защитой, выходами и P&L. Доказанного дефекта, меняющего сигналы или сделки, не найдено. Минимальная торговая коррекция и пересчёт экономических результатов не требуются.

Для **обеих испытанных стратегий подтверждаю `NO BASELINE PASS / REJECT`**. Это отказ в принятии исследованных фиксированных M5/derived-MTF архитектур как экономического Baseline, а не доказательство убыточности всех возможных VWAP/Momentum систем. Полные годовые Net/PF/DD остаются недоказанными и null; положительные GLD closed-only подвыборки не дают оснований для PASS.

За пределами этого вердикта остаются реальные биржевые fills, native FINAM delivery, очередь/ёмкость, фактическая постановка защиты, GO/капитал и ненаблюдаемый intrabar порядок. Эти свойства не объявлялись доказанными в модели #451. Их недоказанность не преобразована в ошибку кода или в экономический успех.

## Независимый метод и охват

Новый [final_independent_logic_audit.py](../tools/final_independent_logic_audit.py) использует только Python stdlib. Он **не импортирует торговые модули, не вызывает Replay, Features, Indicators, DerivedContext или существующие audit-функции как источник ожидаемого результата**. Сначала читает исходные свечи и восстанавливает все решения с нуля; только после этого сопоставляет полученные таблицы с журналами. Заданные правила взяты из замороженных деклараций, а не подобраны по доходностям.

Проверены ровно 128 ранее объявленных вариантов #451: обе стратегии, четыре инструмента, фиксированные parent-архитектуры, NONE/M30 и ранее испытанные M15/H1, T10/T15. Это повторная проверка уже проведённых исследований; новых вариантов, численных параметров, MTF-гипотез или стратегий не введено. Frozen M5 NONE-компараторы входят в этот полный охват; их исходные файлы также сохранены по SHA256.

| Независимая проверка | Результат |
| --- | --- |
| Исходные M5 строки 2023 / точные байты префикса | 104 795 / 5 833 704 |
| Решения по доставленным свечам до размножения на архитектуры | 255 148 |
| Все записи сигналов: принятые, busy, boundary, filtered, nonfill, missing-entry | 123 712; 0 отсутствующих/лишних/несовпадающих |
| Входы / известные исходы / неизвестные cohort-scenario исходы | 8 198 / 7 906 / 292; MATCH |
| Execution events: цена, время, ack, причина, flags и количества | 199 511; MATCH |
| Заявки BE/trailing, decided/effective Stop | 486; MATCH, включая неисполненные до исхода |
| YEAR/MONTH × ALL/LONG/SHORT экономические строки | 4 992; MATCH |
| M15 / M30 / H1 полные дочерние наборы | 20 433 / 8 986 / 3 567 |
| Все MTF decision clocks T10/T15 | 418 176; причинные инварианты PASS |
| Ручные трассировки | 34, с OHLCV, расчётами и строками журналов |
| Существующие проверки IntradayLab | 153 tests PASS, 0 skips |
| Неизменные исходные Lab-файлы / защищённые root IDs | 193 / 25; PASS |

Числа сделок разных cohort не складываются как независимые реальные сделки. 292 unknown — повторяющиеся случаи разных архитектур/задержек. Первоначальные 82 unknown FROZEN_V2 T10 остаются теми же. Проверяющий алгоритм сохраняет null после обнаружения ненаблюдаемого пути; не пытается восстановить Stop/Take в отсутствующей свече или рассчитать альтернативный P&L.

Сравнение цен, индикаторов, Gross/C1/Net/R использует **точное Decimal-равенство**, а времени, причин и статусов — точное равенство. Все возможности перечислены из входных свечей, включая отсутствие сигнала на остальных допустимых решениях. Поэтому совпадение не ограничено опубликованными удачными примерами или существующим ledger.

## Что именно реализовано как VWAP Mean Reversion

Это **условная разновидность возврата внутрь ATR-полосы с остаточным движением к VWAP**, объявленная до результатов. Для LONG:

```text
previous Close <= previous VWAP - shifted ATR12
current VWAP - shifted ATR12 < signal Close < current VWAP
Take = decision VWAP, далее не перемещается
```

Для SHORT условия симметричны. Один и тот же ATR, известный на текущем сигнале и рассчитанный строго по предыдущим свечам, используется для обеих проверок. Это не механическое правило входа при любом отклонении на один ATR: требуется уже наблюдаемый возврат внутрь полосы, без пересечения самой средней. Направление соответствует возврату к VWAP; это Mean Reversion по намерению и payoff, но только указанная разновидность.

VWAP = накопленная `(H+L+C)/3 × relative Volume` / накопленная relative Volume. Anchor — разрешённое непрерывное исследовательское окно; после пропуска аккумулятор сбрасывается. Это **OHLCV approximation по наблюдаемому фрагменту**, а не transaction VWAP или полный session VWAP с неизвестными весами. Формулы и gap-reset прямо заданы в baseline/v2 manifest. Различие с более широким бытовым названием стратегии является заранее объявленным модельным выбором, **не доказанным дефектом реализации**. Отказ относится к этой испытанной разновидности; общий класс VWAP MR этим не опровергнут.

## Сигналы, индикаторы, фильтры и входы

- ATR12 — среднее 12 прошлых True Range, каждый со своим previous Close; signal bar исключён. Warm-up — 13 последовательных предыдущих M5. Momentum range — High/Low прошлых 12, без signal bar; LONG строго выше High, SHORT строго ниже Low.
- Wilder ATR14/DM/DI: seed из 14 интервалов; ADX — среднее первых 14 DX, затем Wilder smoothing. Initial ADX требует 28 свечей. Индикаторы сбрасываются на границе окна/дня/физическом пропуске. EMA50 восстановлена и совпадает как резервная диагностика; торговым фильтром не является.
- В FULL Momentum требует ADX≥25 и DI по направлению; MR отвергает сильный adverse DI при ADX≥25. Ни M30 ADX, ни перенос прогрева через ночь/перерыв не подставлены.
- Signal OHLCV известно в T+10/T+15. Ready учитывает замороженные нулевые дополнительные задержки; scheduled Open **строго позже** ready: T+15/T+20. OHLCV этого Open не участвует в принятии сигнала, а используется только в условном исполнении заранее назначенного точного слота.
- Busy, известный boundary cutoff, невалидные округлённые уровни, ATR/ADX warm-up, risk≥4 tick, net reward≥net risk, сохранение breakout и ограничение extension/TR проверены как на cap, так и на фактическом Open, где это предусмотрено parent-архитектурой.
- Payable MR cap выводится из `(Take + Stop − direction×4tick)/2` и округляется в безопасную сторону. Take сохраняется. Это ограничение цены заявки; отсутствующий limit-touch не превращается в fill. Fill допускается только по exact scheduled Open, внутри Stop/Take и cap.
- One-bar TTL не переносит неисполненную заявку на удобную более позднюю свечу. 235 missing-entry сценариев во всём повторяющемся batch имеют `NO_BAR_NO_MODEL_FILL`, без модельной позиции, цены или C1. Это не утверждение о реальной биржевой отмене.

## Первоначальная защита и сопровождение

Baseline Stop = signal Close ±1.5 ATR12; Momentum Take = Close ±3 ATR12; MR Take = frozen VWAP. Округление LONG Stop/Take вверх, cap вниз; SHORT наоборот. Management Stop — более дальний из 1.5 ATR14 и frozen структуры: MR последние три swing-свечи плюс один tick; Momentum breakout edge плюс adverse 0.5 ATR14. Initial R рассчитывается от actual Open до **initial** Stop, не от впоследствии изменённой защиты.

Resident Stop разрешён при касании; неблагоприятный гэп исполняется по `min(Open,Stop)` LONG / `max(Open,Stop)` SHORT. Take требует penetration хотя бы на один датированный tick; touch даёт nonfill, благоприятный gap improvement не присваивается. Если обе границы достижимы в одной свече, принят Stop-first. На entry bar разрешён adverse Stop, но запрещён Take. Это явно выбранные intrabar допущения; OHLCV не доказывает фактическую последовательность.

**Своевременная постановка первоначальной защиты — допущение resident precommitted conditional Stop**, считающегося активным уже на entry candle до позднего acknowledgement. Модель проверена именно с этим допущением. Отдельных broker/exchange timestamps, доказывающих фактическое атомарное прикрепление защиты, нет; они не выдуманы.

Management Momentum снимает resident TP после входа и ведёт runner; прежний nominal target остаётся ruler для entry admissibility. Delivered Close внутри frozen edge вызывает FAILED_BREAKOUT. После 30 минут прогресс ниже 0.5 initial R вызывает no-progress exit. Close≥1 initial R ставит BE на entry±2 dated ticks; Close≥2R разрешает монотонный trail от best delivered High/Low минус/плюс 2 ATR14. Если кандидат уже marketable относительно доставленного Close, отправляется будущий Open exit.

MR premise exit использует delivered Close за frozen swing последних трёх signal-свечей; после 30 минут неположительный прогресс вызывает VWAP_NO_PROGRESS. Он не переопределяет historical VWAP, target или прошлый Stop. Каждая поправка Stop действует только на **следующем строго будущем M5 Open после решения**, не на свечах между наблюдаемым start и delivery. Проверены queued updates, применение и state BE/TRAIL; изменение защиты задним числом не обнаружено.

## Выходы, расходы и границы сессии

Цена и причина каждого выхода восстановлены из последовательности событий. Предназначенный market exit исполняется по будущему Open раньше внутрисвечной защиты; opening gap остаётся в цене. Timers имеют приоритет session flat перед max-hold, затем adaptive management. MAX_HOLD request сохраняет ранее объявленную семантику entry start +60/90 минут −5 минут; поздний ack не приравнивается к точной длительности подтверждённого удержания.

Gross = direction×(Exit−Entry); C1 — один датированный tick на сторону, отдельно от reference price. CNY tick меняется с 0.01 на 0.001 **27.09.2023 в 19:00 MSK**; в дневном-only исследовании новый tick впервые применим на следующем разрешённом дне. Entry и Exit датируются независимо. Net = Gross−C1; Net R = Net/initial risk. C2 проверен как замена C1 на 2×C1 тех же допущенных fills, без нового отбора сделок.

Session submission deadline выводится из future Open + availability ≤B−10: T10 требует B−25, T15 — B−30. При отсутствии entry acknowledgement к этому времени закрытие не гарантируется. Во всём batch T10 имеет **1 breach, unknown**, исходный GLD Baseline 06.10.2023; все T10 MTF-варианты — 0. T15 имеет **119 breaches: 112 с известным payoff и 7 unknown**. Они воспроизведены, сохранены и явно отличены от реального пересечения funding snapshot. Наличие известного P&L не доказывает выполнение B−10 резерва. Это уже отражённая задержочная/данная граница условной модели, не скрытый новый дефект.

Годовые и месячные coverage построены заново из разрешённого календаря, без заполнения missing slots. Closed-only PF/Net/DD не подменяют полные календарные результаты. UNKNOWN total C1/Net/R остаются null; известный entry C1 учитывается отдельно. Консервативный monthly cohort gate блокирует calendar PASS обеих сторон при unknown любой стороны — это ограничивает, а не завышает экономическую приёмку.

## MTF и причинность

MTF — ранее объявленная `DERIVED_EXACT_COMPLETED_M5_V1`, а не native feed. Каждый M15/M30/H1 имеет ровно 3/6/12 реально существующих детей одного непрерывного окна. OHLCV = first Open / max High / min Low / last Close / sum Volume. Clock alignment сохранён: PM M30 начинается в 14:30, H1 в 15:00; произвольного anchor 14:05 нет.

Минимум доступности: M15 T+20, M30 T+35, H1 T+65 при T10; T15 добавляет пять минут. Выбирается последняя **ожидаемая** пара к decision clock; отсутствие ребёнка в ней блокирует контекст, без stale fallback. В исходных свечах нет измеренных дополнительных delivery stamps; сценарий поздней доставки остаётся ограничением и покрыт существующими synthetic causality tests. Native FINAM timing по совпадению OHLCV не сертифицируется.

Независимый обратный clock scan подтвердил все signal contexts и admission/rejection решения, а полный перебор — 418 176 допустимых clocks. Полные aggregates дают те же 20 433/8 986/3 567. Из 2023 данных дополнительно выполнены metamorphic проверки: изменение будущих цен не меняет прошлые features/MTF; удаление каждого из шести детей latest M30 блокирует пару; повреждённый payoff отвергается сравнением.

Направление контекста задаётся двумя completed parent candles: обе Close>Open и второй Close>первого — +1, симметрично −1, иначе 0. Momentum требует совпадения направления; MR запрещает sustained adverse direction. Gate меняет только допуск входа; independent state machine учитывает освободившиеся после отказа возможности, а не ошибочно предполагает MTF-ledger простым подмножеством M5.

В 45 906 T15 signal records diagnostic `indicator_available_at` остаётся номинальным T+10. Это **заранее раскрыто** в [reporting_notes.json](../results/stage2_architecture_review/reporting_notes.json): actual clocks — `available_at`, `ready_at`, `decided_at`. Поле не читается торговыми решениями и не создаёт look-ahead; использовать его как фактическую T15-доставку нельзя. Замороженный diagnostic timestamp не исправлялся.

Ещё одна оговорка по названию diagnostic-колонки: `entries_retention_ratio` фактически равен **current entries / reference entries**, включая newly freed opportunities. Он не равен доле сохранённых signal IDs. Например, VWAP USD FROZEN M30: 350/548 = 0.638686 — размер cohort; сохранены 328/548 = 0.598540, освобождены 22 новых входа. Все три количества независимо совпали. Для выводов о сохранении используются `entries_retained_same_signal`, `reference_entries_omitted`, `newly_freed_opportunities`, а не неоднозначное имя ratio. Торговые решения/P&L от этой колонки не зависят.

## Экономическое решение

Независимые Gross/C1/Net/PF по всем вариантам и месяцам совпали; компактный [run_summary.csv](../results/stage2_final_independent_audit/run_summary.csv) содержит 128 cohort/scenario агрегатов. Дополнительно проверены все 64 основные summary, включая T15, C2, сохранённые/освобождённые входы, концентрацию и знаки closed месяцев: [economic_summary_check.json](../results/stage2_final_independent_audit/economic_summary_check.json). Полные годовые Net/PF/DD по-прежнему null из-за coverage/unknown, независимо от знака closed-only подвыборок.

| Основной full+M30, T10 | VWAP E/K/U; Net/PF | Momentum E/K/U; Net/PF |
| --- | --- | --- |
| USDRUBF | 24/24/0; −0.64 / 0.467 | 22/22/0; +0.46 / 1.442 |
| CNYRUBF | 7/7/0; −0.024 / 0.500 | 8/8/0; −0.003 / 0.959 |
| GLDRUBF | 12/12/0; +29.9 / 2.431 | 5/5/0; +68.9 / 9.833 |
| IMOEXF | 0/0/0; N/A | 0/0/0; N/A |

GLD VWAP full M30 имеет два положительных и два отрицательных closed месяца, только 12 известных сделок. GLD Momentum full M30 имеет пять сделок; главный победитель +74.8 даёт 97.52% positive P&L, без него Net −5.9. T15 Momentum GLD Net −5.7 / PF 0.462, USD −0.67 / PF 0.489. Эти факты не подтверждают совместно положительное ожидание, PF≥1.6, устойчивость месяцев, частоту и задержочный резерв. Локальные исключения сохранены, но общий экономический Baseline не принят. Никакого нового фильтра, подбора параметров или пересчёта ради улучшения PF аудит не предлагает.

## Трассировки и воспроизводимость

[34 ручных трассировки](../results/stage2_final_independent_audit/manual_traces.md) охватывают обе стратегии, LONG/SHORT и выигрыш/убыток, Stop/Take, BE/trailing, premise/failed breakout/no-progress, max-hold/session flat, M15/M30/H1, missing-entry/unknown path, Stop-first, entry-bar Stop/TP prohibition, gap, CNY tick switch, T15 breach и мартовскую границу. По каждой указаны signal/decision/entry/exit/ack timestamps, source row и OHLCV, 12 TR, VWAP accumulator, индикаторы, уровни/фильтры и расчёт P&L, строки CSV и сравнение с журналом.

Воспроизведение из audit-ветки при наличии frozen source checkout `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`:

```bash
python IntradayLab/tools/final_independent_logic_audit.py --data-root /workspace/market-pattern-data --output /workspace/work/independent-repeat-a
python IntradayLab/tools/final_independent_logic_audit.py --data-root /workspace/market-pattern-data --output /workspace/work/independent-repeat-b
cmp /workspace/work/independent-repeat-a/audit.json /workspace/work/independent-repeat-b/audit.json
cmp /workspace/work/independent-repeat-a/run_summary.csv /workspace/work/independent-repeat-b/run_summary.csv
python IntradayLab/tools/final_audit_traces.py --data-root /workspace/market-pattern-data --audit-folder /workspace/work/independent-repeat-a --output /workspace/work/independent-traces.md
cmp /workspace/work/independent-traces.md IntradayLab/results/stage2_final_independent_audit/manual_traces.md
```

Каждый output folder должен быть новым; перезапись результатов запрещена. `reconstructed.json` — большой промежуточный независимый журнал, остаётся в work/, не публикуется в репозиторий. Компактные [audit.json](../results/stage2_final_independent_audit/audit.json), summary и traces публикуются с SHA256. Два полных исполнения проверяющего алгоритма должны быть побайтово одинаковы; опубликованная фактическая сверка — [reproducibility.json](../results/stage2_final_independent_audit/reproducibility.json).

В reader используются точные attested byte budgets и unbuffered read; последующая строка/EOF не запрашиваются. Все годы проверяются до разбора OHLCV. **Числовые market rows 2024 WF и 2025+ TRUE OOS не читались**; M5 не восстанавливались. Source checkout остался clean/read-only. Все 193 исходных Lab-файла и 25 защищённых roots сравниваются с исходным HEAD/main, включая TradingSystemLab и BBW.

Отдельный Draft PR содержит только новые файлы IntradayLab. Фактическая post-publication проверка main, обоих PR, base/head, remote diff, frozen hashes и protected trees сохраняется в новом audit artifact. **Merge, LIVE, Stage 3 и третья стратегия не выполнялись. Следующая стратегия требует отдельного решения пользователя.**
